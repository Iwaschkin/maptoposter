"""Tests for the render module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from maptoposter.config import load_theme
from maptoposter.render import (
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
    PosterRenderer,
    ZOrder,
)


class TestZOrderConstants:
    """Tests for ZOrder constant class."""

    def test_zorder_layering(self) -> None:
        """Test z-order values are in correct order."""
        assert ZOrder.WATER < ZOrder.PARKS
        assert ZOrder.PARKS < ZOrder.ROADS
        assert ZOrder.ROADS < ZOrder.GRADIENT
        assert ZOrder.GRADIENT < ZOrder.TEXT

    def test_zorder_values(self) -> None:
        """Test specific z-order values."""
        assert ZOrder.WATER == 1
        assert ZOrder.PARKS == 2
        assert ZOrder.ROADS == 3
        assert ZOrder.GRADIENT == 10
        assert ZOrder.TEXT == 11


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
