"""Tests for the render module."""

from __future__ import annotations

from typing import ClassVar
from unittest.mock import MagicMock

import geopandas as gpd
import pytest
from shapely.geometry import LineString

from maptoposter.config import load_theme
from maptoposter.render import PosterRenderer, ZOrder, get_backend
from maptoposter.render_constants import (
    BASE_FONT_ATTR,
    BASE_FONT_COORDS,
    BASE_FONT_MAIN,
    BASE_FONT_SUB,
    GRADIENT_HEIGHT_FRACTION,
    ROAD_WIDTH_DEFAULT,
    ROAD_WIDTH_MOTORWAY,
    ROAD_WIDTH_PRIMARY,
    ROAD_WIDTH_SECONDARY,
    ROAD_WIDTH_TERTIARY,
)
from maptoposter.styles import StyleConfig


class TestZOrderConstants:
    """Tests for ZOrder constant class."""

    def test_zorder_layering(self) -> None:
        """Test z-order values are in correct order."""
        assert ZOrder.WATER < ZOrder.WATERWAYS
        assert ZOrder.WATERWAYS < ZOrder.PARKS
        assert ZOrder.PARKS < ZOrder.ROADS
        assert ZOrder.ROADS < ZOrder.RAILWAYS
        assert ZOrder.RAILWAYS < ZOrder.GRADIENT
        assert ZOrder.GRADIENT < ZOrder.TEXT

    def test_zorder_values(self) -> None:
        """Test specific z-order values."""
        assert ZOrder.WATER == 1
        assert ZOrder.WATERWAYS == 2
        assert ZOrder.PARKS == 3
        assert ZOrder.ROADS == 4
        assert ZOrder.RAILWAYS == 8
        assert ZOrder.GRADIENT == 10
        assert ZOrder.TEXT == 100  # Text always topmost


class TestRoadWidthConstants:
    """Tests for road width constants."""

    def test_road_width_hierarchy(self) -> None:
        """Test road widths follow expected hierarchy."""
        assert ROAD_WIDTH_MOTORWAY > ROAD_WIDTH_PRIMARY
        assert ROAD_WIDTH_PRIMARY > ROAD_WIDTH_SECONDARY
        assert ROAD_WIDTH_SECONDARY > ROAD_WIDTH_TERTIARY
        assert ROAD_WIDTH_TERTIARY > ROAD_WIDTH_DEFAULT

    def test_road_width_values(self) -> None:
        """Test specific road width values."""
        assert ROAD_WIDTH_MOTORWAY == 1.2
        assert ROAD_WIDTH_PRIMARY == 1.0
        assert ROAD_WIDTH_SECONDARY == 0.8
        assert ROAD_WIDTH_TERTIARY == 0.6
        assert ROAD_WIDTH_DEFAULT == 0.4


class TestFontSizeConstants:
    """Tests for font size constants."""

    def test_font_size_hierarchy(self) -> None:
        """Test font sizes follow expected hierarchy."""
        assert BASE_FONT_MAIN > BASE_FONT_SUB
        assert BASE_FONT_SUB > BASE_FONT_COORDS
        assert BASE_FONT_COORDS > BASE_FONT_ATTR

    def test_font_size_values(self) -> None:
        """Test specific font size values."""
        assert BASE_FONT_MAIN == 60
        assert BASE_FONT_SUB == 22
        assert BASE_FONT_COORDS == 14
        assert BASE_FONT_ATTR == 8


class TestGradientConstants:
    """Tests for gradient constants."""

    def test_gradient_height_fraction(self) -> None:
        """Test gradient height fraction is reasonable."""
        assert 0 < GRADIENT_HEIGHT_FRACTION < 0.5
        assert GRADIENT_HEIGHT_FRACTION == 0.25


class TestGetEdgeColorsByType:
    """Tests for get_edge_colors_by_type method."""

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """Create a mock PosterConfig."""
        config = MagicMock()
        config.theme = load_theme("noir")
        config.city = "Test City"
        config.country = "Test Country"
        config.name_label = None
        config.country_label = None
        return config

    def test_motorway_gets_motorway_color(self, mock_config: MagicMock) -> None:
        """Test motorway highway type gets correct color."""
        renderer = PosterRenderer(mock_config)

        # Create mock graph with motorway edge
        mock_graph = MagicMock()
        mock_graph.edges.return_value = [
            (1, 2, {"highway": "motorway"}),
        ]

        colors = renderer.get_edge_colors_by_type(mock_graph)

        assert len(colors) == 1
        assert colors[0] == mock_config.theme["road_motorway"]

    def test_primary_gets_primary_color(self, mock_config: MagicMock) -> None:
        """Test primary highway type gets correct color."""
        renderer = PosterRenderer(mock_config)

        mock_graph = MagicMock()
        mock_graph.edges.return_value = [
            (1, 2, {"highway": "primary"}),
        ]

        colors = renderer.get_edge_colors_by_type(mock_graph)

        assert colors[0] == mock_config.theme["road_primary"]

    def test_residential_gets_residential_color(self, mock_config: MagicMock) -> None:
        """Test residential highway type gets correct color."""
        renderer = PosterRenderer(mock_config)

        mock_graph = MagicMock()
        mock_graph.edges.return_value = [
            (1, 2, {"highway": "residential"}),
        ]

        colors = renderer.get_edge_colors_by_type(mock_graph)

        assert colors[0] == mock_config.theme["road_residential"]

    def test_unknown_type_gets_default_color(self, mock_config: MagicMock) -> None:
        """Test unknown highway type gets default color."""
        renderer = PosterRenderer(mock_config)

        mock_graph = MagicMock()
        mock_graph.edges.return_value = [
            (1, 2, {"highway": "unknown_type"}),
        ]

        colors = renderer.get_edge_colors_by_type(mock_graph)

        assert colors[0] == mock_config.theme["road_default"]

    def test_list_highway_uses_first_element(self, mock_config: MagicMock) -> None:
        """Test that list of highway types uses first element."""
        renderer = PosterRenderer(mock_config)

        mock_graph = MagicMock()
        mock_graph.edges.return_value = [
            (1, 2, {"highway": ["motorway", "primary"]}),
        ]

        colors = renderer.get_edge_colors_by_type(mock_graph)

        assert colors[0] == mock_config.theme["road_motorway"]


class TestGetEdgeWidthsByType:
    """Tests for get_edge_widths_by_type method."""

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """Create a mock PosterConfig."""
        config = MagicMock()
        config.theme = load_theme("noir")
        config.city = "Test City"
        config.country = "Test Country"
        config.name_label = None
        config.country_label = None
        return config

    def test_motorway_gets_widest_width(self, mock_config: MagicMock) -> None:
        """Test motorway gets widest line width."""
        renderer = PosterRenderer(mock_config)

        mock_graph = MagicMock()
        mock_graph.edges.return_value = [
            (1, 2, {"highway": "motorway"}),
        ]

        widths = renderer.get_edge_widths_by_type(mock_graph)

        assert widths[0] == ROAD_WIDTH_MOTORWAY

    def test_residential_gets_narrow_width(self, mock_config: MagicMock) -> None:
        """Test residential gets narrow line width."""
        renderer = PosterRenderer(mock_config)

        mock_graph = MagicMock()
        mock_graph.edges.return_value = [
            (1, 2, {"highway": "residential"}),
        ]

        widths = renderer.get_edge_widths_by_type(mock_graph)

        assert widths[0] == ROAD_WIDTH_DEFAULT

    def test_width_hierarchy_in_mixed_graph(self, mock_config: MagicMock) -> None:
        """Test that width hierarchy is maintained in mixed graphs."""
        renderer = PosterRenderer(mock_config)

        mock_graph = MagicMock()
        mock_graph.edges.return_value = [
            (1, 2, {"highway": "motorway"}),
            (2, 3, {"highway": "primary"}),
            (3, 4, {"highway": "secondary"}),
            (4, 5, {"highway": "tertiary"}),
            (5, 6, {"highway": "residential"}),
        ]

        widths = renderer.get_edge_widths_by_type(mock_graph)

        assert widths[0] == ROAD_WIDTH_MOTORWAY
        assert widths[1] == ROAD_WIDTH_PRIMARY
        assert widths[2] == ROAD_WIDTH_SECONDARY
        assert widths[3] == ROAD_WIDTH_TERTIARY
        assert widths[4] == ROAD_WIDTH_DEFAULT


class TestPosterRendererInit:
    """Tests for PosterRenderer initialization."""

    def test_renderer_stores_config(self) -> None:
        """Test renderer stores config correctly."""
        config = MagicMock()
        config.theme = {"bg": "#000"}
        config.city = "Test"
        config.country = "Country"
        config.name_label = None
        config.country_label = None

        renderer = PosterRenderer(config)

        assert renderer.config is config
        assert renderer.theme == config.theme

    def test_renderer_loads_fonts(self) -> None:
        """Test renderer loads fonts on init."""
        config = MagicMock()
        config.theme = {"bg": "#000"}
        config.city = "Test"
        config.country = "Country"
        config.name_label = None
        config.country_label = None

        renderer = PosterRenderer(config)

        assert renderer.fonts is not None


def test_build_layers_creates_casing_and_core(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that build_layers creates both casing and core layers for roads."""
    config = MagicMock()
    config.theme = load_theme("noir")
    config.city = "Test City"
    config.country = "Test Country"
    config.name_label = None
    config.country_label = None
    config.style_config = StyleConfig(road_glow_strength=0.4)
    config.render_backend = "matplotlib"
    config.output_format = "png"
    config.theme_name = "noir"

    renderer = PosterRenderer(config)

    class DummyGraph:
        graph: ClassVar[dict[str, str]] = {"crs": "EPSG:4326"}

    edges_gdf = gpd.GeoDataFrame(
        {
            "highway": ["motorway", "residential"],
            "geometry": [LineString([(0, 0), (1, 1)]), LineString([(1, 0), (2, 1)])],
        },
        crs="EPSG:4326",
    )

    monkeypatch.setattr("maptoposter.render.ox.project_graph", lambda _graph: DummyGraph())
    monkeypatch.setattr(
        "maptoposter.render.ox.graph_to_gdfs",
        lambda *_args, **_kwargs: edges_gdf,
    )
    monkeypatch.setattr(
        "maptoposter.render.get_crop_limits",
        lambda *_args, **_kwargs: ((0.0, 1.0), (0.0, 1.0)),
    )

    layers, _, _ = renderer.build_layers(
        graph=MagicMock(),
        water=None,
        parks=None,
        railways=None,
        point=(0.0, 0.0),
        fig=MagicMock(),
        compensated_dist=1000.0,
    )

    layer_names = {layer.name for layer in layers}
    assert "roads_motorway_casing" in layer_names
    assert "roads_motorway_core" in layer_names
    assert "roads_residential_casing" in layer_names
    assert "roads_residential_core" in layer_names

    motorway_core = next(layer for layer in layers if layer.name == "roads_motorway_core")
    assert motorway_core.style["glow"] > 0


def test_get_backend_falls_back_to_matplotlib() -> None:
    """Test that get_backend falls back to matplotlib for unknown backends."""
    backend = get_backend("unknown")
    assert backend.name == "matplotlib"


class TestTypography:
    """Tests for typography-related methods."""

    @pytest.fixture
    def renderer(self) -> PosterRenderer:
        """Create a PosterRenderer with default style."""
        config = MagicMock()
        config.theme = load_theme("noir")
        config.city = "Test City"
        config.country = "Test Country"
        config.name_label = None
        config.country_label = None
        return PosterRenderer(config)

    def test_get_tracking_returns_default_for_short_names(self, renderer: PosterRenderer) -> None:
        """Short city names should use the style default tracking."""
        # Default typography_tracking is 2
        assert renderer._get_tracking("Paris") == renderer.style.typography_tracking
        assert renderer._get_tracking("Tokyo") == renderer.style.typography_tracking

    def test_get_tracking_reduces_for_medium_names(self, renderer: PosterRenderer) -> None:
        """Medium-length names (11-17 chars) should reduce tracking."""
        assert renderer._get_tracking("Philadelphia") == 1  # 12 chars
        assert renderer._get_tracking("San Francisco") == 1  # 13 chars

    def test_get_tracking_zero_for_very_long_names(self, renderer: PosterRenderer) -> None:
        """Very long names (18+ chars) should have zero tracking."""
        assert renderer._get_tracking("Rio de Janeiro Brazil") == 0  # 21 chars
        assert renderer._get_tracking("Llanfairpwllgwyngyll") == 0  # 20 chars

    def test_split_city_name_single_word_unchanged(self, renderer: PosterRenderer) -> None:
        """Single-word names should not be split."""
        result = renderer._split_city_name("Tokyo")
        assert result == "TOKYO"
        assert "\n" not in result

    def test_split_city_name_short_two_words_unchanged(self, renderer: PosterRenderer) -> None:
        """Short two-word names (<=14 chars) stay on one line."""
        result = renderer._split_city_name("New York")
        assert result == "NEW YORK"
        assert "\n" not in result

    def test_split_city_name_long_splits_balanced(self, renderer: PosterRenderer) -> None:
        """Long multi-word names should split into balanced lines."""
        result = renderer._split_city_name("San Francisco California")
        assert "\n" in result
        lines = result.split("\n")
        assert len(lines) == 2
        # Should be uppercase
        assert result == result.upper()

    def test_split_city_name_returns_uppercase(self, renderer: PosterRenderer) -> None:
        """All split results should be uppercase."""
        assert renderer._split_city_name("paris").isupper()
        assert renderer._split_city_name("los angeles").isupper()

    def test_apply_tracking_single_line(self, renderer: PosterRenderer) -> None:
        """Tracking adds spaces between characters on single line."""
        result = renderer._apply_tracking("ABC", 2)
        assert result == "A  B  C"

    def test_apply_tracking_multi_line(self, renderer: PosterRenderer) -> None:
        """Tracking applies to each line independently."""
        result = renderer._apply_tracking("AB\nCD", 1)
        assert result == "A B\nC D"

    def test_apply_tracking_zero_no_spaces(self, renderer: PosterRenderer) -> None:
        """Zero tracking should not add any spaces."""
        result = renderer._apply_tracking("ABC", 0)
        assert result == "ABC"

    def test_apply_tracking_preserves_existing_spaces(self, renderer: PosterRenderer) -> None:
        """Tracking treats spaces as characters too."""
        result = renderer._apply_tracking("A B", 1)
        # Each character including space gets tracking applied
        assert result == "A   B"
