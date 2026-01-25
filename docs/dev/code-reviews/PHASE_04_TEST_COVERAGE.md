# Phase 04: Test Coverage Expansion

## Header

| Field | Value |
|-------|-------|
| **Phase ID** | 04 |
| **Phase Name** | Test Coverage Expansion |
| **Status** | Not Started |
| **Start Date** | - |
| **Completion Date** | - |
| **Dependencies** | Phases 01-03 (test stable, fixed code) |
| **Owner/Assignee** | TBD |

---

## Tracking Data

| Metric | Value |
|--------|-------|
| **Total Issues** | 2 |
| **Resolved Issues** | 0 |
| **Remaining Issues** | 2 |
| **Progress** | 0% |
| **Blockers** | Waiting for Phases 01-03 completion |

---

## Issue Registry

| Issue ID | Description | Priority | Status | Completion Date | Notes |
|----------|-------------|----------|--------|-----------------|-------|
| CR-0008 | No test coverage for rendering module | High | Not Started | - | Target >80% coverage |
| CR-0009 | No test coverage for geographic module | High | Not Started | - | Requires HTTP mocking |

---

## Execution Plan

### Task 1: Create Test Suite for Geo Module (CR-0009)

**Objective:** Achieve >80% line coverage on `geo.py` with mocked external dependencies.

**Test Strategy:**
- Mock `geopy.Nominatim` for geocoding tests
- Mock `osmnx` functions for graph/feature fetching
- Test cache interactions with Phase 01's new cache format
- Test error handling from Phase 02

**Create `tests/test_geo.py`:**

```python
"""Tests for geo module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, Polygon

from maptoposter.geo import get_coordinates, fetch_graph, fetch_features, get_crop_limits


class TestGetCoordinates:
    """Tests for get_coordinates function."""

    @patch("maptoposter.geo.cache_get")
    @patch("maptoposter.geo.Nominatim")
    def test_returns_cached_coordinates(self, mock_nominatim, mock_cache_get):
        """Should return cached coordinates without API call."""
        mock_cache_get.return_value = (48.8566, 2.3522)

        result = get_coordinates("Paris", "France")

        assert result == (48.8566, 2.3522)
        mock_nominatim.assert_not_called()

    @patch("maptoposter.geo.cache_set")
    @patch("maptoposter.geo.cache_get")
    @patch("maptoposter.geo.Nominatim")
    def test_fetches_and_caches_new_coordinates(self, mock_nominatim_class, mock_cache_get, mock_cache_set):
        """Should fetch from Nominatim and cache result."""
        mock_cache_get.return_value = None
        mock_location = Mock()
        mock_location.latitude = 48.8566
        mock_location.longitude = 2.3522
        mock_nominatim_class.return_value.geocode.return_value = mock_location

        result = get_coordinates("Paris", "France")

        assert result == (48.8566, 2.3522)
        mock_cache_set.assert_called_once()

    @patch("maptoposter.geo.cache_get")
    @patch("maptoposter.geo.Nominatim")
    def test_returns_none_when_location_not_found(self, mock_nominatim_class, mock_cache_get):
        """Should return None when geocoding fails."""
        mock_cache_get.return_value = None
        mock_nominatim_class.return_value.geocode.return_value = None

        result = get_coordinates("NonexistentCity", "Nowhere")

        assert result is None

    @patch("maptoposter.geo.cache_get")
    @patch("maptoposter.geo.Nominatim")
    def test_handles_network_error(self, mock_nominatim_class, mock_cache_get):
        """Should return None on network error."""
        from requests.exceptions import ConnectionError
        mock_cache_get.return_value = None
        mock_nominatim_class.return_value.geocode.side_effect = ConnectionError("Network error")

        result = get_coordinates("Paris", "France")

        assert result is None


class TestFetchGraph:
    """Tests for fetch_graph function."""

    @patch("maptoposter.geo.cache_get")
    def test_returns_cached_graph(self, mock_cache_get):
        """Should return cached graph without API call."""
        mock_graph = nx.MultiDiGraph()
        mock_cache_get.return_value = mock_graph

        result = fetch_graph((48.8566, 2.3522), 5000)

        assert result is mock_graph

    @patch("maptoposter.geo.cache_set")
    @patch("maptoposter.geo.cache_get")
    @patch("maptoposter.geo.ox")
    def test_fetches_and_caches_graph(self, mock_ox, mock_cache_get, mock_cache_set):
        """Should fetch from OSMnx and cache result."""
        mock_cache_get.return_value = None
        mock_graph = nx.MultiDiGraph()
        mock_ox.graph_from_point.return_value = mock_graph

        result = fetch_graph((48.8566, 2.3522), 5000)

        assert result is mock_graph
        mock_ox.graph_from_point.assert_called_once()
        mock_cache_set.assert_called_once()

    @patch("maptoposter.geo.cache_get")
    @patch("maptoposter.geo.ox")
    def test_handles_insufficient_data(self, mock_ox, mock_cache_get):
        """Should return None when no street data available."""
        from osmnx._errors import InsufficientResponseError
        mock_cache_get.return_value = None
        mock_ox.graph_from_point.side_effect = InsufficientResponseError("No data")

        result = fetch_graph((0.0, 0.0), 5000)  # Middle of ocean

        assert result is None


class TestFetchFeatures:
    """Tests for fetch_features function."""

    @patch("maptoposter.geo.cache_get")
    def test_returns_cached_features(self, mock_cache_get):
        """Should return cached features without API call."""
        mock_gdf = gpd.GeoDataFrame(geometry=[Point(0, 0)])
        mock_cache_get.return_value = mock_gdf

        result = fetch_features((48.8566, 2.3522), 5000, {"natural": "water"}, "water")

        assert result is mock_gdf

    @patch("maptoposter.geo.cache_set")
    @patch("maptoposter.geo.cache_get")
    @patch("maptoposter.geo.ox")
    def test_fetches_and_caches_features(self, mock_ox, mock_cache_get, mock_cache_set):
        """Should fetch from OSMnx and cache result."""
        mock_cache_get.return_value = None
        mock_gdf = gpd.GeoDataFrame(geometry=[Point(0, 0)])
        mock_ox.features_from_point.return_value = mock_gdf

        result = fetch_features((48.8566, 2.3522), 5000, {"natural": "water"}, "water")

        assert result is mock_gdf
        mock_cache_set.assert_called_once()


class TestGetCropLimits:
    """Tests for get_crop_limits function."""

    def test_calculates_correct_limits_square(self):
        """Should calculate correct limits for 1:1 aspect ratio."""
        result = get_crop_limits((0, 0), dist=1000, width=10, height=10)

        # Should have equal x and y ranges for square
        x_range = result[1] - result[0]
        y_range = result[3] - result[2]
        assert abs(x_range - y_range) < 0.01

    def test_calculates_correct_limits_portrait(self):
        """Should calculate correct limits for portrait aspect ratio."""
        result = get_crop_limits((0, 0), dist=1000, width=10, height=15)

        # Portrait should have larger y range
        x_range = result[1] - result[0]
        y_range = result[3] - result[2]
        assert y_range > x_range

    def test_calculates_correct_limits_landscape(self):
        """Should calculate correct limits for landscape aspect ratio."""
        result = get_crop_limits((0, 0), dist=1000, width=15, height=10)

        # Landscape should have larger x range
        x_range = result[1] - result[0]
        y_range = result[3] - result[2]
        assert x_range > y_range
```

**Dependencies to Add (if not present):**
- `pytest-mock` for cleaner mocking
- `responses` or `vcrpy` for HTTP mocking (optional, for integration tests)

**Files Affected:**
- `tests/test_geo.py` (new file)
- `pyproject.toml` (add test dependencies)

**Validation:**
- [ ] `uv run pytest tests/test_geo.py -v` passes
- [ ] Coverage report shows >80% on geo.py
- [ ] All mock scenarios work correctly

---

### Task 2: Create Test Suite for Render Module (CR-0008)

**Objective:** Achieve >80% line coverage on `render.py` with mocked matplotlib.

**Test Strategy:**
- Unit test pure functions: `get_edge_colors_by_type()`, `get_edge_widths_by_type()`
- Mock matplotlib for rendering tests
- Test gradient generation logic
- Integration test that verifies file output

**Create `tests/test_render.py`:**

```python
"""Tests for render module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, LineString

from maptoposter.render import (
    get_edge_colors_by_type,
    get_edge_widths_by_type,
    PosterRenderer,
    create_poster,
)
from maptoposter.config import PosterConfig


class TestGetEdgeColorsByType:
    """Tests for road color assignment."""

    def test_motorway_color(self):
        """Should assign motorway color for motorway highways."""
        theme = {"road_motorway": "#FF0000", "road_default": "#000000"}
        edges = [(0, 1, {"highway": "motorway"})]
        graph = nx.MultiDiGraph()
        graph.add_edges_from(edges)

        colors = get_edge_colors_by_type(graph, theme)

        assert colors[0] == "#FF0000"

    def test_motorway_link_color(self):
        """Should assign motorway color for motorway_link."""
        theme = {"road_motorway": "#FF0000", "road_default": "#000000"}
        edges = [(0, 1, {"highway": "motorway_link"})]
        graph = nx.MultiDiGraph()
        graph.add_edges_from(edges)

        colors = get_edge_colors_by_type(graph, theme)

        assert colors[0] == "#FF0000"

    def test_primary_color(self):
        """Should assign primary color for primary/trunk roads."""
        theme = {"road_primary": "#00FF00", "road_default": "#000000"}
        edges = [(0, 1, {"highway": "primary"})]
        graph = nx.MultiDiGraph()
        graph.add_edges_from(edges)

        colors = get_edge_colors_by_type(graph, theme)

        assert colors[0] == "#00FF00"

    def test_default_color_for_unknown(self):
        """Should use default color for unknown highway types."""
        theme = {"road_default": "#CCCCCC"}
        edges = [(0, 1, {"highway": "unknown_type"})]
        graph = nx.MultiDiGraph()
        graph.add_edges_from(edges)

        colors = get_edge_colors_by_type(graph, theme)

        assert colors[0] == "#CCCCCC"

    def test_missing_highway_attribute(self):
        """Should use default color when highway attribute missing."""
        theme = {"road_default": "#CCCCCC"}
        edges = [(0, 1, {})]  # No highway attribute
        graph = nx.MultiDiGraph()
        graph.add_edges_from(edges)

        colors = get_edge_colors_by_type(graph, theme)

        assert colors[0] == "#CCCCCC"


class TestGetEdgeWidthsByType:
    """Tests for road width assignment."""

    def test_motorway_width(self):
        """Should assign widest width for motorways."""
        edges = [(0, 1, {"highway": "motorway"})]
        graph = nx.MultiDiGraph()
        graph.add_edges_from(edges)

        widths = get_edge_widths_by_type(graph)

        assert widths[0] == 1.2  # Motorway is thickest

    def test_residential_width(self):
        """Should assign thinnest width for residential."""
        edges = [(0, 1, {"highway": "residential"})]
        graph = nx.MultiDiGraph()
        graph.add_edges_from(edges)

        widths = get_edge_widths_by_type(graph)

        assert widths[0] == 0.4  # Residential is thinnest

    def test_width_hierarchy(self):
        """Should maintain correct width hierarchy."""
        edges = [
            (0, 1, {"highway": "motorway"}),
            (1, 2, {"highway": "primary"}),
            (2, 3, {"highway": "secondary"}),
            (3, 4, {"highway": "tertiary"}),
            (4, 5, {"highway": "residential"}),
        ]
        graph = nx.MultiDiGraph()
        graph.add_edges_from(edges)

        widths = get_edge_widths_by_type(graph)

        # Verify hierarchy: motorway > primary > secondary > tertiary > residential
        assert widths[0] > widths[1] > widths[2] > widths[3] > widths[4]


class TestPosterRenderer:
    """Tests for PosterRenderer class."""

    def test_initialization(self):
        """Should initialize with valid config."""
        config = PosterConfig(
            city="Paris",
            country="France",
            theme={"bg": "#FFFFFF", "text": "#000000"},
        )

        renderer = PosterRenderer(config)

        assert renderer.config == config

    @patch("maptoposter.render.plt")
    def test_creates_figure_with_correct_size(self, mock_plt):
        """Should create figure with configured dimensions."""
        config = PosterConfig(
            city="Paris",
            country="France",
            theme={"bg": "#FFFFFF"},
            width=10,
            height=15,
        )
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        renderer = PosterRenderer(config)
        # Trigger figure creation (implementation dependent)

        # Verify subplots called with correct figsize
        # (Actual assertion depends on implementation)


class TestCreatePoster:
    """Integration tests for create_poster function."""

    @patch("maptoposter.render.fetch_graph")
    @patch("maptoposter.render.fetch_features")
    @patch("maptoposter.render.get_coordinates")
    def test_creates_output_file(self, mock_coords, mock_features, mock_graph):
        """Should create output file at specified path."""
        # Setup mocks
        mock_coords.return_value = (48.8566, 2.3522)
        mock_graph.return_value = _create_mock_graph()
        mock_features.return_value = None  # No water/parks

        config = PosterConfig(
            city="Paris",
            country="France",
            theme_name="noir",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_poster.png"

            result = create_poster(config, output_path)

            assert result is not None
            assert output_path.exists()

    @patch("maptoposter.render.get_coordinates")
    def test_returns_none_when_coordinates_fail(self, mock_coords):
        """Should return None when geocoding fails."""
        mock_coords.return_value = None

        config = PosterConfig(
            city="NonexistentCity",
            country="Nowhere",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_poster.png"

            result = create_poster(config, output_path)

            assert result is None

    def test_creates_parent_directories(self):
        """Should create parent directories if they don't exist."""
        # This tests CR-0023 fix
        config = PosterConfig(
            city="Paris",
            country="France",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "deep" / "nested" / "dir" / "poster.png"

            # Should not raise FileNotFoundError
            # (May still fail if mocks not set up, but directory should be created)


class TestNameLabelOverride:
    """Tests for name_label functionality (CR-0003)."""

    @patch("maptoposter.render.PosterRenderer._add_typography")
    def test_name_label_overrides_city(self, mock_typography):
        """Should use name_label when provided."""
        config = PosterConfig(
            city="New York",
            country="USA",
            name_label="NYC",
            theme={"text": "#000000"},
        )

        renderer = PosterRenderer(config)
        # Verify name_label is used in typography
        # (Actual implementation will be tested in Phase 03)


def _create_mock_graph():
    """Create a minimal mock graph for testing."""
    graph = nx.MultiDiGraph()
    graph.add_edge(0, 1, highway="residential", geometry=LineString([(0, 0), (1, 1)]))
    graph.graph["crs"] = "EPSG:4326"
    return graph
```

**Files Affected:**
- `tests/test_render.py` (new file)

**Validation:**
- [ ] `uv run pytest tests/test_render.py -v` passes
- [ ] Coverage report shows >80% on render.py
- [ ] Edge color/width logic thoroughly tested

---

### Task 3: Add Coverage Reporting

**Objective:** Enable coverage reporting in test suite.

**Update `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src/maptoposter --cov-report=term-missing --cov-report=html"

[tool.coverage.run]
source = ["src/maptoposter"]
omit = ["*/__pycache__/*", "*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

**Add Dev Dependencies:**
```toml
[project.optional-dependencies]
dev = [
    # ... existing ...
    "pytest-cov>=4.0.0",
]
```

**Files Affected:**
- `pyproject.toml`

**Validation:**
- [ ] `uv run pytest --cov` produces coverage report
- [ ] HTML report generated in `htmlcov/`

---

## Validation Criteria

Phase 04 is complete when:

1. ✅ **CR-0008:** render.py has >80% line coverage
2. ✅ **CR-0009:** geo.py has >80% line coverage
3. ✅ All tests pass: `uv run pytest` succeeds
4. ✅ Coverage report confirms thresholds met
5. ✅ No mocked tests leak to external APIs

---

## Coverage Targets

| Module | Current Coverage | Target Coverage | Status |
|--------|------------------|-----------------|--------|
| geo.py | 0% | >80% | Not Started |
| render.py | 0% | >80% | Not Started |
| fonts.py | 0% | >50% | Optional |

---

## Rollback Plan

If Phase 04 fails:

1. Tests are additive; removal has no production impact
2. Coverage configuration can be reverted easily
3. Failing tests should be fixed, not removed

**Safe Rollback Command:**
```bash
rm tests/test_geo.py tests/test_render.py
git checkout HEAD~1 -- pyproject.toml
```

---

*Phase Document Created: 2026-01-24*
