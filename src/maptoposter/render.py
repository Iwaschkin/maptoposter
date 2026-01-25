"""Map rendering and poster generation."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
from matplotlib.axes import Axes
from pyproj.exceptions import CRSError
from tqdm import tqdm

from .config import PosterConfig
from .fonts import load_fonts
from .geo import fetch_features, fetch_graph, get_crop_limits

if TYPE_CHECKING:
    from pathlib import Path

    from networkx import MultiDiGraph

__all__ = ["PosterRenderer", "create_poster"]

logger = logging.getLogger(__name__)


# =============================================================================
# Constants (CR-0011, CR-0019)
# =============================================================================


class ZOrder:
    """Z-order constants for layer stacking."""

    WATER = 1
    PARKS = 2
    ROADS = 3
    GRADIENT = 10
    TEXT = 11


# Typography positioning constants
TEXT_CENTER_X = 0.5
CITY_NAME_Y_POS = 0.14
COUNTRY_LABEL_Y_POS = 0.10
COORDS_Y_POS = 0.07
DIVIDER_Y_POS = 0.125
ATTRIBUTION_X_POS = 0.98
ATTRIBUTION_Y_POS = 0.02

# Gradient constants
GRADIENT_HEIGHT_FRACTION = 0.25

# Road width constants by highway type
ROAD_WIDTH_MOTORWAY = 1.2
ROAD_WIDTH_PRIMARY = 1.0
ROAD_WIDTH_SECONDARY = 0.8
ROAD_WIDTH_TERTIARY = 0.6
ROAD_WIDTH_DEFAULT = 0.4

# Base font sizes (at 12 inches width reference)
BASE_FONT_MAIN = 60
BASE_FONT_SUB = 22
BASE_FONT_COORDS = 14
BASE_FONT_ATTR = 8


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

    def create_gradient_fade(
        self,
        ax: Axes,
        color: str,
        location: str = "bottom",
        zorder: int = ZOrder.GRADIENT,
    ) -> None:
        """Create a fade effect at the top or bottom of the map.

        Args:
            ax: The matplotlib axes.
            color: The gradient color.
            location: Either 'top' or 'bottom'.
            zorder: The z-order for layering.
        """
        vals = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((vals, vals))

        rgb = mcolors.to_rgb(color)
        my_colors = np.zeros((256, 4))
        my_colors[:, 0] = rgb[0]
        my_colors[:, 1] = rgb[1]
        my_colors[:, 2] = rgb[2]

        if location == "bottom":
            my_colors[:, 3] = np.linspace(1, 0, 256)
            extent_y_start = 0.0
            extent_y_end = GRADIENT_HEIGHT_FRACTION
        else:
            my_colors[:, 3] = np.linspace(0, 1, 256)
            extent_y_start = 1.0 - GRADIENT_HEIGHT_FRACTION
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
            highway = data.get("highway", "unclassified")

            if isinstance(highway, list):
                highway = highway[0] if highway else "unclassified"

            if highway in ["motorway", "motorway_link"]:
                color = self.theme["road_motorway"]
            elif highway in ["trunk", "trunk_link", "primary", "primary_link"]:
                color = self.theme["road_primary"]
            elif highway in ["secondary", "secondary_link"]:
                color = self.theme["road_secondary"]
            elif highway in ["tertiary", "tertiary_link"]:
                color = self.theme["road_tertiary"]
            elif highway in ["residential", "living_street", "unclassified"]:
                color = self.theme["road_residential"]
            else:
                color = self.theme["road_default"]

            edge_colors.append(color)

        return edge_colors

    def get_edge_widths_by_type(self, graph: MultiDiGraph) -> list[float]:
        """Assign line widths to edges based on road type.

        Args:
            graph: The street network graph.

        Returns:
            A list of widths corresponding to each edge.
        """
        edge_widths = []

        for _, _, data in graph.edges(data=True):
            highway = data.get("highway", "unclassified")

            if isinstance(highway, list):
                highway = highway[0] if highway else "unclassified"

            if highway in ["motorway", "motorway_link"]:
                width = ROAD_WIDTH_MOTORWAY
            elif highway in ["trunk", "trunk_link", "primary", "primary_link"]:
                width = ROAD_WIDTH_PRIMARY
            elif highway in ["secondary", "secondary_link"]:
                width = ROAD_WIDTH_SECONDARY
            elif highway in ["tertiary", "tertiary_link"]:
                width = ROAD_WIDTH_TERTIARY
            else:
                width = ROAD_WIDTH_DEFAULT

            edge_widths.append(width)

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
        spaced_city = "  ".join(list(display_name.upper()))

        # Dynamically adjust font size based on city name length
        base_adjusted_main = BASE_FONT_MAIN * scale_factor
        city_char_count = len(display_name)

        if city_char_count > 10:
            length_factor = 10 / city_char_count
            adjusted_font_size = max(
                base_adjusted_main * length_factor, 10 * scale_factor
            )
        else:
            adjusted_font_size = base_adjusted_main

        font_main = self.fonts.get_properties("bold", adjusted_font_size)
        font_sub = self.fonts.get_properties("light", BASE_FONT_SUB * scale_factor)
        font_coords = self.fonts.get_properties(
            "regular", BASE_FONT_COORDS * scale_factor
        )
        font_attr = self.fonts.get_properties("light", BASE_FONT_ATTR)

        # City name
        ax.text(
            TEXT_CENTER_X,
            CITY_NAME_Y_POS,
            spaced_city,
            transform=ax.transAxes,
            color=self.theme["text"],
            ha="center",
            fontproperties=font_main,
            zorder=ZOrder.TEXT,
        )

        # Country label
        country_text = self.config.country_label or self.config.country
        ax.text(
            TEXT_CENTER_X,
            COUNTRY_LABEL_Y_POS,
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
            TEXT_CENTER_X,
            COORDS_Y_POS,
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
            [DIVIDER_Y_POS, DIVIDER_Y_POS],
            transform=ax.transAxes,
            color=self.theme["text"],
            linewidth=1 * scale_factor,
            zorder=ZOrder.TEXT,
        )

        # Attribution
        ax.text(
            ATTRIBUTION_X_POS,
            ATTRIBUTION_Y_POS,
            "© OpenStreetMap contributors",
            transform=ax.transAxes,
            color=self.theme["text"],
            alpha=0.5,
            ha="right",
            va="bottom",
            fontproperties=font_attr,
            zorder=ZOrder.TEXT,
        )

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

        logger.info("Generating map for %s, %s...", city, country)

        # Calculate compensated distance for viewport crop
        compensated_dist = dist * (max(height, width) / min(height, width)) / 4

        # Fetch data with progress bar
        show_progress = show_progress and sys.stderr.isatty()
        with tqdm(
            total=3,
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
                tags={"natural": "water", "waterway": "riverbank"},
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

        logger.info("All data retrieved successfully.")
        logger.info("Rendering map...")

        # Setup plot
        fig, ax = plt.subplots(figsize=(width, height), facecolor=self.theme["bg"])
        ax.set_facecolor(self.theme["bg"])
        ax.set_position((0.0, 0.0, 1.0, 1.0))

        # Project graph
        g_proj = ox.project_graph(graph)

        # Plot water features
        if water is not None and not water.empty:
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
                water_polys.plot(
                    ax=ax,
                    facecolor=self.theme["water"],
                    edgecolor="none",
                    zorder=ZOrder.WATER,
                )

        # Plot parks
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
                parks_polys.plot(
                    ax=ax,
                    facecolor=self.theme["parks"],
                    edgecolor="none",
                    zorder=ZOrder.PARKS,
                )

        # Plot roads
        logger.info("Applying road hierarchy colors...")
        edge_colors = self.get_edge_colors_by_type(g_proj)
        edge_widths = self.get_edge_widths_by_type(g_proj)

        crop_xlim, crop_ylim = get_crop_limits(g_proj, point, fig, compensated_dist)

        ox.plot_graph(
            g_proj,
            ax=ax,
            bgcolor=self.theme["bg"],
            node_size=0,
            edge_color=edge_colors,
            edge_linewidth=edge_widths,
            show=False,
            close=False,
        )

        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(crop_xlim)
        ax.set_ylim(crop_ylim)

        # Add gradients
        self.create_gradient_fade(
            ax, self.theme["gradient_color"], location="bottom", zorder=ZOrder.GRADIENT
        )
        self.create_gradient_fade(
            ax, self.theme["gradient_color"], location="top", zorder=ZOrder.GRADIENT
        )

        # Add typography
        scale_factor = width / 12.0
        self._add_typography(ax, point, scale_factor)

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
    theme: dict[str, str] | None = None,
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
        theme: Theme dictionary (loaded if not provided).
        show_progress: Whether to display a progress bar (TTY only).
    """
    # Ensure output directory exists (CR-0023 fix)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    config = PosterConfig(
        city=city,
        country=country,
        distance=dist,
        width=width,
        height=height,
        output_format=output_format,
        country_label=country_label,
        name_label=name_label,
        theme=theme or {},
    )

    renderer = PosterRenderer(config)
    renderer.render(point, output_file, show_progress=show_progress)
