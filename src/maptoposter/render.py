"""Map rendering and poster generation."""

from __future__ import annotations

import io
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, cast

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
from matplotlib import patheffects
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from PIL import Image
from pyproj.exceptions import CRSError
from tqdm import tqdm

from .config import PosterConfig
from .fonts import load_fonts
from .geo import fetch_features, fetch_graph, get_crop_limits
from .postprocess import apply_raster_effects, needs_raster_postprocessing
from .render_constants import (
    BASE_FONT_ATTR,
    BASE_FONT_COORDS,
    BASE_FONT_MAIN,
    BASE_FONT_SUB,
    ROAD_WIDTH_DEFAULT,
)
from .styles import StyleConfig


# Increase PIL's decompression bomb limit for large posters
# Default is ~89 million pixels; we need more for large print sizes (e.g., 40"x40" @ 300 DPI)
Image.MAX_IMAGE_PIXELS = 300_000_000  # ~300 megapixels


if TYPE_CHECKING:
    from pathlib import Path

    from networkx import MultiDiGraph

__all__ = [
    "DatashaderBackend",
    "MatplotlibBackend",
    "PosterRenderer",
    "RenderBackend",
    "RenderLayer",
    "RoadStyle",
    "StyleConfig",
    "create_poster",
]

logger = logging.getLogger(__name__)

LAYER_CACHE_MAX = 4
LAYER_CACHE_TTL_SECONDS = 3600
LAYER_CACHE: dict[str, dict[str, Any]] = {}
LAYER_CACHE_ORDER: list[str] = []
LAYER_CACHE_LOCK = threading.Lock()
LAYER_CACHE_STATS = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0}


# =============================================================================
# Constants (CR-0011, CR-0019)
# =============================================================================


class ZOrder:
    """Z-order constants for layer stacking."""

    WATER = 1
    WATERWAYS = 2  # Rivers/streams rendered as lines above water polygons
    PARKS = 3
    ROADS = 4
    RAILWAYS = 8  # Railways rendered above roads
    GRADIENT = 10
    TEXT = 100  # Text always topmost


HIGHWAY_CLASS_MAP: dict[str, str] = {
    "motorway": "motorway",
    "motorway_link": "motorway",
    "trunk": "primary",
    "trunk_link": "primary",
    "primary": "primary",
    "primary_link": "primary",
    "secondary": "secondary",
    "secondary_link": "secondary",
    "tertiary": "tertiary",
    "tertiary_link": "tertiary",
    "residential": "residential",
    "living_street": "residential",
    "unclassified": "residential",
}


@dataclass(frozen=True)
class RenderLayer:
    """Prepared render layer without drawing."""

    name: str
    zorder: int
    gdf: Any | None = None
    graph: MultiDiGraph | None = None
    style: dict[str, Any] = field(default_factory=dict)


class RenderBackend(Protocol):
    """Render backend interface."""

    name: str

    def render_roads(
        self,
        ax: Axes,
        layers: list[RenderLayer],
        crop_xlim: tuple[float, float],
        crop_ylim: tuple[float, float],
        theme: dict[str, str],
    ) -> bool:
        """Render road layers using this backend.

        Args:
            ax: The matplotlib axes to render on.
            layers: List of RenderLayer objects to render.
            crop_xlim: X-axis limits (min, max) for cropping.
            crop_ylim: Y-axis limits (min, max) for cropping.
            theme: Theme dictionary with color definitions.

        Returns:
            True if rendering was handled by this backend, False otherwise.
        """
        ...


class MatplotlibBackend:
    """Matplotlib-based rendering backend."""

    name = "matplotlib"

    def render_roads(
        self,
        ax: Axes,  # noqa: ARG002
        layers: list[RenderLayer],  # noqa: ARG002
        crop_xlim: tuple[float, float],  # noqa: ARG002
        crop_ylim: tuple[float, float],  # noqa: ARG002
        theme: dict[str, str],  # noqa: ARG002
    ) -> bool:
        """Render roads using matplotlib (currently defers to standard rendering).

        This backend returns False to indicate that the standard matplotlib
        rendering path should be used instead.

        Args:
            ax: The matplotlib axes (unused, defers to standard rendering).
            layers: List of RenderLayer objects (unused).
            crop_xlim: X-axis limits (unused).
            crop_ylim: Y-axis limits (unused).
            theme: Theme dictionary (unused).

        Returns:
            False, indicating standard rendering should be used.
        """
        return False


class DatashaderBackend:
    """Datashader-based rendering backend.

    Renders roads using datashader for efficient handling of dense networks.
    Uses native line_width parameter for proper antialiased lines.
    Supports road width hierarchy, casing, and glow effects.
    """

    name = "datashader"

    def render_roads(
        self,
        ax: Axes,
        layers: list[RenderLayer],
        crop_xlim: tuple[float, float],
        crop_ylim: tuple[float, float],
        theme: dict[str, str],
    ) -> bool:
        """Render roads using datashader with antialiased lines.

        Args:
            ax: Matplotlib axes to render on.
            layers: List of road layers to render.
            crop_xlim: X-axis limits.
            crop_ylim: Y-axis limits.
            theme: Theme colors dictionary.

        Returns:
            True if rendering succeeded, False if datashader unavailable.
        """
        try:
            import datashader as ds
            import datashader.transfer_functions as tf
        except Exception:
            return False

        road_layers = [layer for layer in layers if layer.name.startswith("roads_")]
        if not road_layers:
            return True

        fig = cast(Figure, ax.figure)
        width_px = int(fig.get_figwidth() * fig.dpi)
        height_px = int(fig.get_figheight() * fig.dpi)
        canvas = ds.Canvas(
            plot_width=width_px,
            plot_height=height_px,
            x_range=crop_xlim,
            y_range=crop_ylim,
        )

        # Calculate pixel scale factor for line widths
        # At 300 DPI, 12" width = 3600px. Road widths are in "points" (1/72 inch)
        # Scale factor converts point-based widths to appropriate pixel widths
        dpi = fig.dpi
        px_per_point = dpi / 72.0  # Points to pixels
        # Additional scale for visual quality at high resolution
        quality_scale = min(width_px, height_px) / 1000.0

        # Sort layers by zorder - casing first, then core
        sorted_layers = sorted(road_layers, key=lambda item: item.zorder)

        # Group casing and core layers
        casing_layers = [layer for layer in sorted_layers if "_casing" in layer.name]
        core_layers = [layer for layer in sorted_layers if "_core" in layer.name]

        # Render casing layers first (behind core)
        for layer in casing_layers:
            if layer.gdf is None or layer.gdf.empty:
                continue
            self._render_layer(ax, canvas, layer, tf, theme, px_per_point, quality_scale)

        # Render core layers with optional glow
        for layer in core_layers:
            if layer.gdf is None or layer.gdf.empty:
                continue
            glow_strength = layer.style.get("glow", 0.0)
            if glow_strength > 0:
                self._render_glow(ax, canvas, layer, tf, glow_strength, px_per_point, quality_scale)
            self._render_layer(ax, canvas, layer, tf, theme, px_per_point, quality_scale)

        return True

    def _render_layer(
        self,
        ax: Axes,
        canvas: Any,
        layer: RenderLayer,
        tf: Any,
        theme: dict[str, str],
        px_per_point: float,
        quality_scale: float,
    ) -> None:
        """Render a single layer with proper antialiased line width.

        Args:
            ax: Matplotlib axes.
            canvas: Datashader canvas.
            layer: RenderLayer to render.
            tf: Datashader transfer_functions module.
            theme: Theme colors dictionary.
            px_per_point: Pixels per typographic point.
            quality_scale: Additional scaling for visual quality.
        """
        if layer.gdf is None:
            return

        color = layer.style.get("color", theme["road_default"])
        base_linewidth = layer.style.get("linewidth", 0.5)

        # Convert linewidth to pixels with quality scaling
        # Base widths are small (0.4-1.2), scale up for visibility
        line_width_px = max(0.5, base_linewidth * px_per_point * quality_scale * 0.8)

        # Use native line_width for proper antialiasing
        agg = canvas.line(layer.gdf, geometry="geometry", line_width=line_width_px)

        img = tf.shade(agg, cmap=[color])
        ax.imshow(
            img.to_pil(),
            extent=(*canvas.x_range, *canvas.y_range),
            zorder=layer.zorder,
            alpha=layer.style.get("alpha", 1.0),
        )

    def _render_glow(
        self,
        ax: Axes,
        canvas: Any,
        layer: RenderLayer,
        tf: Any,
        glow_strength: float,
        px_per_point: float,
        quality_scale: float,
    ) -> None:
        """Render a soft glow effect for a layer using wider antialiased lines.

        Args:
            ax: Matplotlib axes.
            canvas: Datashader canvas.
            layer: RenderLayer to render glow for.
            tf: Datashader transfer_functions module.
            glow_strength: Glow intensity (0.0-1.0).
            px_per_point: Pixels per typographic point.
            quality_scale: Additional scaling for visual quality.
        """
        if layer.gdf is None:
            return

        color = layer.style.get("color", "#FFFFFF")
        base_linewidth = layer.style.get("linewidth", 0.5)

        # Glow is rendered as a wider, semi-transparent version of the line
        # Use larger line_width for the glow effect
        core_width_px = max(0.5, base_linewidth * px_per_point * quality_scale * 0.8)
        glow_width_px = core_width_px * (2.0 + glow_strength * 3.0)  # 2x to 5x core width

        # Render glow with native antialiased line_width
        agg = canvas.line(layer.gdf, geometry="geometry", line_width=glow_width_px)

        # Soft alpha for glow effect
        glow_alpha = min(0.25, glow_strength * 0.3)
        img = tf.shade(agg, cmap=[color])
        ax.imshow(
            img.to_pil(),
            extent=(*canvas.x_range, *canvas.y_range),
            zorder=layer.zorder - 0.1,  # Slightly behind the core layer
            alpha=glow_alpha,
        )


BACKEND_REGISTRY: dict[str, RenderBackend] = {
    "matplotlib": MatplotlibBackend(),
    "datashader": DatashaderBackend(),
}


def get_backend(name: str) -> RenderBackend:
    """Resolve a render backend by name, falling back to matplotlib."""
    return BACKEND_REGISTRY.get(name, BACKEND_REGISTRY["matplotlib"])


@dataclass(frozen=True)
class RoadStyle:
    """Road rendering style for a classified edge."""

    road_class: str
    core_color: str
    core_width: float
    casing_color: str
    casing_width: float
    glow_strength: float = 0.0


class PosterRenderer:
    """Renders map posters with customizable styling."""

    def __init__(self, config: PosterConfig) -> None:
        """Initialize the renderer with configuration.

        Args:
            config: The poster configuration.
        """
        self.config = config
        self.theme = config.theme
        self.fonts = load_fonts()
        style_config = getattr(config, "style_config", None)
        self.style = style_config if isinstance(style_config, StyleConfig) else StyleConfig()

    def create_gradient_fade(
        self,
        ax: Axes,
        color: str,
        location: str = "bottom",
        zorder: int = ZOrder.GRADIENT,
        height_fraction: float | None = None,
    ) -> None:
        """Create a fade effect at the top or bottom of the map.

        Args:
            ax: The matplotlib axes.
            color: The gradient color.
            location: Either 'top' or 'bottom'.
            zorder: The z-order for layering.
            height_fraction: Optional fraction of the axes height for gradient.
        """
        vals = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((vals, vals))

        rgb = mcolors.to_rgb(color)
        my_colors = np.zeros((256, 4))
        my_colors[:, 0] = rgb[0]
        my_colors[:, 1] = rgb[1]
        my_colors[:, 2] = rgb[2]

        if height_fraction is None:
            height_fraction = self.style.gradient_strength

        if location == "bottom":
            my_colors[:, 3] = np.linspace(1, 0, 256)
            extent_y_start = 0.0
            extent_y_end = height_fraction
        else:
            my_colors[:, 3] = np.linspace(0, 1, 256)
            extent_y_start = 1.0 - height_fraction
            extent_y_end = 1.0

        custom_cmap = mcolors.ListedColormap(my_colors)

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        y_range = ylim[1] - ylim[0]

        y_bottom = ylim[0] + y_range * extent_y_start
        y_top = ylim[0] + y_range * extent_y_end

        ax.imshow(
            gradient,
            extent=(xlim[0], xlim[1], y_bottom, y_top),
            aspect="auto",
            cmap=custom_cmap,
            zorder=zorder,
            origin="lower",
        )

    def get_edge_colors_by_type(self, graph: MultiDiGraph) -> list[str]:
        """Assign colors to edges based on road type hierarchy.

        Args:
            graph: The street network graph.

        Returns:
            A list of colors corresponding to each edge.
        """
        edge_colors = []

        for _, _, data in graph.edges(data=True):
            style = self.classify_edge(data.get("highway", "unclassified"))
            edge_colors.append(style.core_color)

        return edge_colors

    def _normalize_highway(self, highway: Any) -> str:
        if isinstance(highway, list):
            return highway[0] if highway else "unclassified"
        if highway is None:
            return "unclassified"
        return str(highway)

    def classify_edge(self, highway: Any) -> RoadStyle:
        """Classify an edge by highway value into a RoadStyle."""
        highway_value = self._normalize_highway(highway)
        road_class = HIGHWAY_CLASS_MAP.get(highway_value, "default")
        if road_class == "motorway":
            color = self.theme["road_motorway"]
        elif road_class == "primary":
            color = self.theme["road_primary"]
        elif road_class == "secondary":
            color = self.theme["road_secondary"]
        elif road_class == "tertiary":
            color = self.theme["road_tertiary"]
        elif road_class == "residential":
            color = self.theme["road_residential"]
        else:
            color = self.theme["road_default"]

        core_width = self.style.road_core_widths.get(road_class, ROAD_WIDTH_DEFAULT)
        casing_width = self.style.road_casing_widths.get(road_class, core_width)
        glow = self.style.road_glow_strength if road_class in {"motorway", "primary"} else 0.0

        return RoadStyle(
            road_class=road_class,
            core_color=color,
            core_width=core_width,
            casing_color=self.theme["bg"],
            casing_width=casing_width,
            glow_strength=glow,
        )

    def get_edge_widths_by_type(self, graph: MultiDiGraph) -> list[float]:
        """Assign line widths to edges based on road type.

        Args:
            graph: The street network graph.

        Returns:
            A list of widths corresponding to each edge.
        """
        edge_widths = []

        for _, _, data in graph.edges(data=True):
            style = self.classify_edge(data.get("highway", "unclassified"))
            edge_widths.append(style.core_width)

        return edge_widths

    def _add_typography(
        self,
        ax: Axes,
        point: tuple[float, float],
        scale_factor: float,
    ) -> None:
        """Add text elements to the poster."""
        # Use name_label if provided, otherwise use city (CR-0003 fix)
        display_name = self.config.name_label or self.config.city
        tracking_value = self._get_tracking(display_name)
        city_lines = self._split_city_name(display_name)
        spaced_city = self._apply_tracking(city_lines, tracking_value)

        # Dynamically adjust font size based on city name length
        base_adjusted_main = BASE_FONT_MAIN * scale_factor
        city_char_count = len(display_name)

        if city_char_count > 10:
            length_factor = 10 / city_char_count
            adjusted_font_size = max(base_adjusted_main * length_factor, 10 * scale_factor)
        else:
            adjusted_font_size = base_adjusted_main

        font_main = self.fonts.get_properties("bold", adjusted_font_size)
        font_sub = self.fonts.get_properties("light", BASE_FONT_SUB * scale_factor)
        font_coords = self.fonts.get_properties("regular", BASE_FONT_COORDS * scale_factor)
        font_attr = self.fonts.get_properties("light", BASE_FONT_ATTR)

        # City name
        city_artist = ax.text(
            self.style.text_center_x,
            self.style.city_name_y_pos,
            spaced_city,
            transform=ax.transAxes,
            color=self.theme["text"],
            ha="center",
            fontproperties=font_main,
            zorder=ZOrder.TEXT,
            linespacing=1.05,
        )
        city_artist.set_path_effects(
            [
                patheffects.Stroke(
                    linewidth=1.5 * scale_factor,
                    foreground=self.theme["bg"],
                    alpha=0.8,
                ),
                patheffects.Normal(),
            ]
        )

        # Country label
        country_text = self.config.country_label or self.config.country
        ax.text(
            self.style.text_center_x,
            self.style.country_label_y_pos,
            country_text.upper(),
            transform=ax.transAxes,
            color=self.theme["text"],
            ha="center",
            fontproperties=font_sub,
            zorder=ZOrder.TEXT,
        )

        # Coordinates
        lat, lon = point
        if lat >= 0:
            coords = f"{lat:.4f}° N / {abs(lon):.4f}° {'E' if lon >= 0 else 'W'}"
        else:
            coords = f"{abs(lat):.4f}° S / {abs(lon):.4f}° {'E' if lon >= 0 else 'W'}"

        ax.text(
            self.style.text_center_x,
            self.style.coords_y_pos,
            coords,
            transform=ax.transAxes,
            color=self.theme["text"],
            alpha=0.7,
            ha="center",
            fontproperties=font_coords,
            zorder=ZOrder.TEXT,
        )

        # Divider line
        ax.plot(
            [0.4, 0.6],
            [self.style.divider_y_pos, self.style.divider_y_pos],
            transform=ax.transAxes,
            color=self.theme["text"],
            linewidth=1 * scale_factor,
            zorder=ZOrder.TEXT,
        )

        # Attribution
        ax.text(
            self.style.attribution_x_pos,
            self.style.attribution_y_pos,
            "© OpenStreetMap contributors",
            transform=ax.transAxes,
            color=self.theme["text"],
            alpha=0.5,
            ha="right",
            va="bottom",
            fontproperties=font_attr,
            zorder=ZOrder.TEXT,
        )

    def _get_tracking(self, display_name: str) -> int:
        """Determine character tracking based on display name length."""
        length = len(display_name)
        if length >= 18:
            return 0
        if length >= 14:
            return 1
        if length >= 11:
            return 1
        return self.style.typography_tracking

    def _split_city_name(self, display_name: str) -> str:
        """Split long city names into two balanced lines."""
        words = display_name.split()
        if len(words) < 2:
            return display_name.upper()
        total_len = sum(len(word) for word in words)
        if total_len <= 14:
            return display_name.upper()

        left_words: list[str] = []
        right_words = words.copy()
        left_len = 0
        while right_words and left_len < total_len / 2:
            word = right_words.pop(0)
            left_words.append(word)
            left_len += len(word)

        left = " ".join(left_words).strip()
        right = " ".join(right_words).strip()
        if not right:
            return display_name.upper()
        return f"{left.upper()}\n{right.upper()}"

    def _apply_tracking(self, text: str, tracking: int) -> str:
        """Apply character tracking to single or multi-line text."""
        spacer = " " * tracking
        if "\n" not in text:
            return spacer.join(list(text))
        lines = text.split("\n")
        spaced_lines = [spacer.join(list(line)) for line in lines]
        return "\n".join(spaced_lines)

    def build_layers(  # noqa: PLR0912
        self,
        graph: MultiDiGraph,
        water: Any,
        parks: Any,
        railways: Any,
        point: tuple[float, float],
        fig: Figure,
        compensated_dist: float,
    ) -> tuple[list[RenderLayer], tuple[float, float], tuple[float, float]]:
        """Prepare layers without rendering."""
        layers: list[RenderLayer] = []
        cache_key = self._format_cache_key(point, compensated_dist)
        cached = self._get_cached_layers(cache_key) if self.style.enable_layer_cache else None

        if cached:
            g_proj = cached["graph"]
            water_polys = cached["water"]
            waterways = cached.get("waterways")  # Linear water features
            parks_polys = cached["parks"]
            railways_lines = cached.get("railways")  # Railway lines
            edges_gdf = cached["edges"]
            crop_xlim = cached["crop_xlim"]
            crop_ylim = cached["crop_ylim"]
        else:
            g_proj = ox.project_graph(graph)
            water_polys = None
            waterways = None
            parks_polys = None
            railways_lines = None

            if water is not None and not water.empty:
                # Extract polygon water bodies (lakes, ponds, wide rivers)
                water_polys = water[water.geometry.type.isin(["Polygon", "MultiPolygon"])]
                if not water_polys.empty:
                    try:
                        water_polys = ox.projection.project_gdf(water_polys)
                    except (ValueError, CRSError) as e:
                        logger.debug(
                            "OSMnx projection failed for water, using direct CRS transform: %s",
                            e,
                        )
                        try:
                            water_polys = water_polys.to_crs(g_proj.graph["crs"])
                        except Exception as e2:
                            logger.warning("Could not project water data: %s", e2)

                # Extract linear waterways (rivers, streams, canals)
                waterways = water[water.geometry.type.isin(["LineString", "MultiLineString"])]
                if not waterways.empty:
                    try:
                        waterways = ox.projection.project_gdf(waterways)
                    except (ValueError, CRSError) as e:
                        logger.debug(
                            "OSMnx projection failed for waterways, using direct CRS transform: %s",
                            e,
                        )
                        try:
                            waterways = waterways.to_crs(g_proj.graph["crs"])
                        except Exception as e2:
                            logger.warning("Could not project waterways data: %s", e2)

            if parks is not None and not parks.empty:
                parks_polys = parks[parks.geometry.type.isin(["Polygon", "MultiPolygon"])]
                if not parks_polys.empty:
                    try:
                        parks_polys = ox.projection.project_gdf(parks_polys)
                    except (ValueError, CRSError) as e:
                        logger.debug(
                            "OSMnx projection failed for parks, using direct CRS transform: %s",
                            e,
                        )
                        try:
                            parks_polys = parks_polys.to_crs(g_proj.graph["crs"])
                        except Exception as e2:
                            logger.warning("Could not project parks data: %s", e2)

                    # Subtract water bodies from parks to prevent covering lakes/meres
                    if water_polys is not None and not water_polys.empty:
                        try:
                            water_union = water_polys.union_all()
                            parks_polys = parks_polys.copy()
                            parks_polys["geometry"] = parks_polys.geometry.difference(water_union)
                            # Remove any empty geometries after subtraction
                            parks_polys = parks_polys[~parks_polys.geometry.is_empty]
                        except Exception as e:
                            logger.debug("Could not subtract water from parks: %s", e)

            # Extract railway lines
            if railways is not None and not railways.empty:
                railways_lines = railways[
                    railways.geometry.type.isin(["LineString", "MultiLineString"])
                ]
                if not railways_lines.empty:
                    try:
                        railways_lines = ox.projection.project_gdf(railways_lines)
                    except (ValueError, CRSError) as e:
                        logger.debug(
                            "OSMnx projection failed for railways, using direct CRS transform: %s",
                            e,
                        )
                        try:
                            railways_lines = railways_lines.to_crs(g_proj.graph["crs"])
                        except Exception as e2:
                            logger.warning("Could not project railways data: %s", e2)

            edges_gdf = ox.graph_to_gdfs(g_proj, nodes=False, fill_edge_geometry=True)
            crop_xlim, crop_ylim = get_crop_limits(g_proj, point, fig, compensated_dist)

            if self.style.enable_layer_cache:
                self._set_cached_layers(
                    cache_key,
                    {
                        "graph": g_proj,
                        "water": water_polys,
                        "waterways": waterways,
                        "parks": parks_polys,
                        "railways": railways_lines,
                        "edges": edges_gdf,
                        "crop_xlim": crop_xlim,
                        "crop_ylim": crop_ylim,
                    },
                )

        if water_polys is not None and not water_polys.empty:
            layers.append(
                RenderLayer(
                    name="water",
                    zorder=ZOrder.WATER,
                    gdf=water_polys,
                    style={"facecolor": self.theme["water"], "edgecolor": "none"},
                )
            )

        # Render linear waterways (rivers, streams, canals)
        if waterways is not None and not waterways.empty:
            # Determine line width based on waterway type
            waterway_widths = {
                "river": 1.5,
                "canal": 1.2,
                "stream": 0.8,
            }
            default_width = 0.8

            # Group by waterway type for varying widths
            if "waterway" in waterways.columns:
                for waterway_type, width in waterway_widths.items():
                    type_waterways = waterways[waterways["waterway"] == waterway_type]
                    if not type_waterways.empty:
                        layers.append(
                            RenderLayer(
                                name=f"waterways_{waterway_type}",
                                zorder=ZOrder.WATERWAYS,
                                gdf=type_waterways,
                                style={
                                    "color": self.theme["water"],
                                    "linewidth": width,
                                },
                            )
                        )
                # Handle any other waterway types
                known_types = set(waterway_widths.keys())
                other_waterways = waterways[~waterways["waterway"].isin(known_types)]
                if not other_waterways.empty:
                    layers.append(
                        RenderLayer(
                            name="waterways_other",
                            zorder=ZOrder.WATERWAYS,
                            gdf=other_waterways,
                            style={
                                "color": self.theme["water"],
                                "linewidth": default_width,
                            },
                        )
                    )
            else:
                # No waterway column, render all with default width
                layers.append(
                    RenderLayer(
                        name="waterways",
                        zorder=ZOrder.WATERWAYS,
                        gdf=waterways,
                        style={
                            "color": self.theme["water"],
                            "linewidth": default_width,
                        },
                    )
                )

        if parks_polys is not None and not parks_polys.empty:
            layers.append(
                RenderLayer(
                    name="parks",
                    zorder=ZOrder.PARKS,
                    gdf=parks_polys,
                    style={"facecolor": self.theme["parks"], "edgecolor": "none"},
                )
            )

        logger.info("Applying road hierarchy colors...")
        if edges_gdf.empty or "highway" not in edges_gdf.columns:
            logger.warning("No road data available for rendering.")
            return layers, crop_xlim, crop_ylim
        edges_gdf = edges_gdf.copy()
        edges_gdf["road_class"] = (
            edges_gdf["highway"]
            .map(self._normalize_highway)
            .map(HIGHWAY_CLASS_MAP)
            .fillna("default")
        )

        class_order = [
            "default",
            "residential",
            "tertiary",
            "secondary",
            "primary",
            "motorway",
        ]
        for index, road_class in enumerate(class_order):
            class_edges = edges_gdf[edges_gdf["road_class"] == road_class]
            if class_edges.empty:
                continue

            style = self.classify_edge(class_edges.iloc[0].get("highway"))
            casing_zorder = ZOrder.ROADS + index * 2
            core_zorder = ZOrder.ROADS + index * 2 + 1

            layers.append(
                RenderLayer(
                    name=f"roads_{road_class}_casing",
                    zorder=casing_zorder,
                    gdf=class_edges,
                    style={
                        "color": style.casing_color,
                        "linewidth": style.casing_width,
                        "glow": 0.0,
                    },
                )
            )
            layers.append(
                RenderLayer(
                    name=f"roads_{road_class}_core",
                    zorder=core_zorder,
                    gdf=class_edges,
                    style={
                        "color": style.core_color,
                        "linewidth": style.core_width,
                        "glow": style.glow_strength,
                    },
                )
            )

        # Render railway lines
        if railways_lines is not None and not railways_lines.empty:
            # Get railway color from theme with fallback
            railway_color = self.theme.get("railway", self.theme.get("road_secondary", "#555555"))
            layers.append(
                RenderLayer(
                    name="railways",
                    zorder=ZOrder.RAILWAYS,
                    gdf=railways_lines,
                    style={
                        "color": railway_color,
                        "linewidth": 0.8,
                        "linestyle": (0, (5, 3)),  # Dashed pattern for railway
                    },
                )
            )

        return layers, crop_xlim, crop_ylim

    def _format_cache_key(self, point: tuple[float, float], compensated_dist: float) -> str:
        lat = round(point[0], 5)
        lon = round(point[1], 5)
        dist = round(compensated_dist, 1)
        return f"{lat:.5f}_{lon:.5f}_{dist:.1f}"

    def render_layers(
        self,
        ax: Axes,
        layers: list[RenderLayer],
        crop_xlim: tuple[float, float],
        crop_ylim: tuple[float, float],
    ) -> None:
        """Render prepared layers to an axes."""
        backend = self._get_backend()
        if backend.render_roads(ax, layers, crop_xlim, crop_ylim, self.theme):
            layers = [layer for layer in layers if "roads_" not in layer.name]
        elif backend.name != "matplotlib":
            logger.warning(
                "Datashader backend unavailable. Falling back to matplotlib. "
                "To enable datashader, install it with: uv add datashader "
                "or pip install datashader"
            )

        for layer in sorted(layers, key=lambda item: item.zorder):
            if layer.gdf is not None:
                if "linewidth" in layer.style:
                    artist = layer.gdf.plot(
                        ax=ax,
                        color=layer.style.get("color", self.theme["road_default"]),
                        linewidth=layer.style.get("linewidth", ROAD_WIDTH_DEFAULT),
                        zorder=layer.zorder,
                    )
                    glow = layer.style.get("glow", 0.0)
                    if glow > 0 and artist.collections:
                        collection = artist.collections[-1]
                        base_width = layer.style.get("linewidth", ROAD_WIDTH_DEFAULT)
                        collection.set_path_effects(
                            [
                                patheffects.Stroke(
                                    linewidth=base_width + glow,
                                    foreground=layer.style.get("color", self.theme["road_default"]),
                                    alpha=0.4,
                                ),
                                patheffects.Normal(),
                            ]
                        )
                else:
                    layer.gdf.plot(
                        ax=ax,
                        facecolor=layer.style.get("facecolor", self.theme["bg"]),
                        edgecolor=layer.style.get("edgecolor", "none"),
                        zorder=layer.zorder,
                    )
            elif layer.graph is not None:
                ox.plot_graph(
                    layer.graph,
                    ax=ax,
                    bgcolor=self.theme["bg"],
                    node_size=0,
                    edge_color=layer.style.get("edge_colors", []),
                    edge_linewidth=layer.style.get("edge_widths", []),
                    show=False,
                    close=False,
                )

        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(crop_xlim)
        ax.set_ylim(crop_ylim)

    def _get_backend(self) -> RenderBackend:
        backend = get_backend(self.config.render_backend)
        if backend.name != self.config.render_backend:
            logger.warning(
                "Unknown render backend '%s'. Falling back to matplotlib.",
                self.config.render_backend,
            )
        return backend

    def post_process(
        self,
        ax: Axes,
        point: tuple[float, float],
        scale_factor: float,
    ) -> None:
        """Apply post-processing effects after rendering layers."""
        self.create_gradient_fade(
            ax, self.theme["gradient_color"], location="bottom", zorder=ZOrder.GRADIENT
        )
        self.create_gradient_fade(
            ax, self.theme["gradient_color"], location="top", zorder=ZOrder.GRADIENT
        )
        self._add_typography(ax, point, scale_factor)

    def _get_cached_layers(self, cache_key: str) -> dict[str, Any] | None:
        with LAYER_CACHE_LOCK:
            cached = LAYER_CACHE.get(cache_key)
            if cached is None:
                LAYER_CACHE_STATS["misses"] += 1
                return None
            cached_at = cached.get("cached_at")
            if cached_at and time.time() - cached_at > LAYER_CACHE_TTL_SECONDS:
                LAYER_CACHE_STATS["expired"] += 1
                LAYER_CACHE.pop(cache_key, None)
                if cache_key in LAYER_CACHE_ORDER:
                    LAYER_CACHE_ORDER.remove(cache_key)
                return None
            LAYER_CACHE_STATS["hits"] += 1
            return cached

    def _set_cached_layers(self, cache_key: str, payload: dict[str, Any]) -> None:
        with LAYER_CACHE_LOCK:
            if cache_key in LAYER_CACHE:
                return
            if len(LAYER_CACHE_ORDER) >= LAYER_CACHE_MAX:
                oldest = LAYER_CACHE_ORDER.pop(0)
                LAYER_CACHE.pop(oldest, None)
                LAYER_CACHE_STATS["evictions"] += 1
            payload["cached_at"] = time.time()
            LAYER_CACHE[cache_key] = payload
            LAYER_CACHE_ORDER.append(cache_key)

    def render(
        self,
        point: tuple[float, float],
        output_file: Path,
        show_progress: bool = True,
    ) -> None:
        """Render the poster and save to file.

        Args:
            point: The center coordinates (latitude, longitude).
            output_file: The output file path.
            show_progress: Whether to display a progress bar (TTY only).
        """
        config = self.config
        city, country = config.city, config.country
        dist = config.distance
        width, height = config.width, config.height

        logger.info(
            "Generating map for %s, %s (theme: %s, format: %s)...",
            city,
            country,
            config.theme_name,
            config.output_format,
        )

        # Calculate compensated distance for viewport crop
        compensated_dist = dist * (max(height, width) / min(height, width)) / 4

        # Fetch data with progress bar
        show_progress = show_progress and sys.stderr.isatty()
        with tqdm(
            total=4,
            desc="Fetching map data",
            unit="step",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
            disable=not show_progress,
        ) as pbar:
            pbar.set_description("Downloading street network")
            graph = fetch_graph(point, compensated_dist)
            if graph is None:
                raise RuntimeError("Failed to retrieve street network data.")
            pbar.update(1)

            pbar.set_description("Downloading water features")
            water = fetch_features(
                point,
                compensated_dist,
                tags={
                    # Water bodies (polygons) - natural=water covers lakes, ponds, etc.
                    "natural": ["water", "bay", "strait", "wetland", "coastline"],
                    # Specific water body types (water=* tag)
                    "water": [
                        "lake",
                        "pond",
                        "reservoir",
                        "basin",
                        "lagoon",
                        "oxbow",
                        "canal",
                        "river",
                        "stream",
                        "moat",
                        "wastewater",
                    ],
                    # Waterways (lines and polygons)
                    "waterway": [
                        "river",
                        "stream",
                        "canal",
                        "riverbank",
                        "dock",
                        "boatyard",
                    ],
                    # Landuse water features
                    "landuse": ["basin", "reservoir"],
                    # Place=sea for named seas/oceans
                    "place": "sea",
                },
                name="water",
            )
            pbar.update(1)

            pbar.set_description("Downloading parks/green spaces")
            parks = fetch_features(
                point,
                compensated_dist,
                tags={"leisure": "park", "landuse": "grass"},
                name="parks",
            )
            pbar.update(1)

            pbar.set_description("Downloading railway lines")
            railways = fetch_features(
                point,
                compensated_dist,
                tags={"railway": ["rail", "light_rail", "subway", "tram"]},
                name="railways",
            )
            pbar.update(1)

        logger.info("All data retrieved successfully.")
        logger.info("Rendering map...")

        # Setup plot
        fig, ax = plt.subplots(figsize=(width, height), facecolor=self.theme["bg"])
        if config.output_format.lower() == "png":
            fig.set_dpi(300)
        ax.set_facecolor(self.theme["bg"])
        ax.set_position((0.0, 0.0, 1.0, 1.0))

        layers, crop_xlim, crop_ylim = self.build_layers(
            graph=graph,
            water=water,
            parks=parks,
            railways=railways,
            point=point,
            fig=fig,
            compensated_dist=compensated_dist,
        )
        self.render_layers(ax, layers, crop_xlim, crop_ylim)

        scale_factor = width / 12.0
        self.post_process(ax, point, scale_factor)

        # Save
        logger.info("Saving to %s...", output_file)

        fmt = config.output_format.lower()
        save_kwargs: dict[str, Any] = {
            "facecolor": self.theme["bg"],
            "bbox_inches": "tight",
            "pad_inches": 0.05,
        }

        if fmt == "png":
            save_kwargs["dpi"] = 300

        try:
            if needs_raster_postprocessing(fmt, self.style):
                buffer = io.BytesIO()
                plt.savefig(buffer, format="png", **save_kwargs)
                buffer.seek(0)
                image = Image.open(buffer)
                image = apply_raster_effects(image, self.style)
                image.save(output_file, format="PNG")
            else:
                plt.savefig(output_file, format=fmt, **save_kwargs)
        finally:
            plt.close()

        logger.info("Done! Poster saved as %s", output_file)


def create_poster(
    city: str,
    country: str,
    point: tuple[float, float],
    dist: int,
    output_file: Path,
    output_format: str,
    width: float = 12,
    height: float = 16,
    country_label: str | None = None,
    name_label: str | None = None,
    theme_name: str | None = None,
    theme: dict[str, str] | None = None,
    style_config: StyleConfig | None = None,
    render_backend: str = "matplotlib",
    show_progress: bool = True,
) -> None:
    """Create a map poster for a city.

    This is a convenience function that wraps PosterRenderer.

    Args:
        city: The city name.
        country: The country name.
        point: The center coordinates (latitude, longitude).
        dist: Map radius in meters.
        output_file: Path to save the poster.
        output_format: Output format (png, svg, pdf).
        width: Image width in inches.
        height: Image height in inches.
        country_label: Override country text on poster.
        name_label: Override city name on poster.
        theme_name: Name of the theme to use.
        theme: Theme dictionary (loaded if not provided).
        style_config: StyleConfig for post-processing effects.
        render_backend: Rendering backend name ('matplotlib' or 'datashader').
        show_progress: Whether to display a progress bar (TTY only).
    """
    # Ensure output directory exists (CR-0023 fix)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    config = PosterConfig(
        city=city,
        country=country,
        theme_name=theme_name or "feature_based",
        distance=dist,
        width=width,
        height=height,
        output_format=output_format,
        country_label=country_label,
        name_label=name_label,
        theme=theme or {},
        style_config=style_config,
        render_backend=render_backend,
    )

    renderer = PosterRenderer(config)
    renderer.render(point, output_file, show_progress=show_progress)
