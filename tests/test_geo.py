"""Tests for the geo module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from geopy.exc import GeocoderTimedOut
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, Timeout

from maptoposter.geo import (
    GeocodingError,
    OSMFetchError,
    fetch_features,
    fetch_graph,
    get_coordinates,
    get_crop_limits,
)


if TYPE_CHECKING:
    from pathlib import Path


class TestGetCoordinates:
    """Tests for get_coordinates function."""

    def test_successful_geocoding(self, tmp_path: Path) -> None:
        """Test successful geocoding returns coordinates."""
        mock_location = MagicMock()
        mock_location.latitude = 51.5074
        mock_location.longitude = -0.1278
        mock_location.address = "London, Greater London, England, UK"

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.Nominatim") as mock_nominatim,
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.cache_set", return_value=True),
            patch("maptoposter.geo.time.sleep"),
        ):
            mock_geolocator = MagicMock()
            mock_geolocator.geocode.return_value = mock_location
            mock_nominatim.return_value = mock_geolocator

            result = get_coordinates("London", "UK")

            assert result == (51.5074, -0.1278)
            mock_geolocator.geocode.assert_called_once_with("London, UK")

    def test_uses_cached_coordinates(self, tmp_path: Path) -> None:
        """Test that cached coordinates are returned without API call."""
        cached_coords = (40.7128, -74.0060)

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=cached_coords),
            patch("maptoposter.geo.Nominatim") as mock_nominatim,
        ):
            result = get_coordinates("New York", "USA")

            assert result == cached_coords
            mock_nominatim.assert_not_called()

    def test_raises_on_location_not_found(self, tmp_path: Path) -> None:
        """Test that GeocodingError is raised when location not found."""
        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.Nominatim") as mock_nominatim,
            patch("maptoposter.geo.cache_get", return_value=None),
        ):
            mock_geolocator = MagicMock()
            mock_geolocator.geocode.return_value = None
            mock_nominatim.return_value = mock_geolocator

            with pytest.raises(GeocodingError, match="Could not find coordinates"):
                get_coordinates("NonexistentCity", "FakeCountry")

    def test_raises_on_network_timeout(self, tmp_path: Path) -> None:
        """Test that GeocodingError is raised on network timeout."""
        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.Nominatim") as mock_nominatim,
            patch("maptoposter.geo.cache_get", return_value=None),
        ):
            mock_geolocator = MagicMock()
            mock_geolocator.geocode.side_effect = Timeout("Connection timed out")
            mock_nominatim.return_value = mock_geolocator

            with pytest.raises(GeocodingError, match="Network error"):
                get_coordinates("Tokyo", "Japan")

    def test_raises_on_connection_error(self, tmp_path: Path) -> None:
        """Test that GeocodingError is raised on connection error."""
        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.Nominatim") as mock_nominatim,
            patch("maptoposter.geo.cache_get", return_value=None),
        ):
            mock_geolocator = MagicMock()
            mock_geolocator.geocode.side_effect = RequestsConnectionError("No connection")
            mock_nominatim.return_value = mock_geolocator

            with pytest.raises(GeocodingError, match="Network error"):
                get_coordinates("Paris", "France")

    def test_raises_on_unexpected_error(self, tmp_path: Path) -> None:
        """Test that GeocodingError is raised on unexpected geocoding errors."""
        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.Nominatim") as mock_nominatim,
            patch("maptoposter.geo.cache_get", return_value=None),
        ):
            mock_geolocator = MagicMock()
            mock_geolocator.geocode.side_effect = GeocoderTimedOut("Service unavailable")
            mock_nominatim.return_value = mock_geolocator

            with pytest.raises(GeocodingError, match="Geocoding failed"):
                get_coordinates("Berlin", "Germany")

    def test_caches_result_after_successful_lookup(self, tmp_path: Path) -> None:
        """Test that successful geocoding results are cached."""
        mock_location = MagicMock()
        mock_location.latitude = 48.8566
        mock_location.longitude = 2.3522
        mock_location.address = "Paris, France"

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.Nominatim") as mock_nominatim,
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.cache_set") as mock_cache_set,
            patch("maptoposter.geo.time.sleep"),
        ):
            mock_geolocator = MagicMock()
            mock_geolocator.geocode.return_value = mock_location
            mock_nominatim.return_value = mock_geolocator

            get_coordinates("Paris", "France")

            mock_cache_set.assert_called_once()
            call_args = mock_cache_set.call_args
            assert call_args[0][0] == "coords_paris_france"
            assert call_args[0][1] == (48.8566, 2.3522)


class TestFetchGraph:
    """Tests for fetch_graph function."""

    def test_returns_cached_graph(self, tmp_path: Path) -> None:
        """Test that cached graph is returned without API call."""
        mock_graph = MagicMock()

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=mock_graph),
            patch("maptoposter.geo.ox") as mock_ox,
        ):
            result = fetch_graph((51.5074, -0.1278), 5000.0)

            assert result is mock_graph
            mock_ox.graph_from_point.assert_not_called()

    def test_fetches_graph_on_cache_miss(self, tmp_path: Path) -> None:
        """Test that graph is fetched from OSM on cache miss."""
        mock_graph = MagicMock()

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.cache_set", return_value=True),
            patch("maptoposter.geo.ox") as mock_ox,
            patch("maptoposter.geo.time.sleep"),
        ):
            mock_ox.graph_from_point.return_value = mock_graph

            result = fetch_graph((51.5074, -0.1278), 5000.0)

            assert result is mock_graph
            mock_ox.graph_from_point.assert_called_once_with(
                (51.5074, -0.1278),
                dist=5000.0,
                dist_type="bbox",
                network_type="all",
                truncate_by_edge=True,
            )

    def test_raises_on_network_timeout(self, tmp_path: Path) -> None:
        """Test that OSMFetchError is raised on network timeout."""
        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.ox") as mock_ox,
        ):
            mock_ox.graph_from_point.side_effect = Timeout("Request timed out")

            with pytest.raises(OSMFetchError, match="Network error"):
                fetch_graph((51.5074, -0.1278), 5000.0)

    def test_raises_on_connection_error(self, tmp_path: Path) -> None:
        """Test that OSMFetchError is raised on connection error."""
        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.ox") as mock_ox,
        ):
            mock_ox.graph_from_point.side_effect = RequestsConnectionError("No connection")

            with pytest.raises(OSMFetchError, match="Network error"):
                fetch_graph((51.5074, -0.1278), 5000.0)

    def test_raises_on_rate_limit(self, tmp_path: Path) -> None:
        """Test that OSMFetchError is raised on HTTP 429 rate limit."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        http_error = HTTPError()
        http_error.response = mock_response

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.ox") as mock_ox,
        ):
            mock_ox.graph_from_point.side_effect = http_error

            with pytest.raises(OSMFetchError, match="Rate limited"):
                fetch_graph((51.5074, -0.1278), 5000.0)

    def test_raises_on_empty_response(self, tmp_path: Path) -> None:
        """Test that OSMFetchError is raised when no street data available."""

        class InsufficientResponseError(Exception):
            pass

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.ox") as mock_ox,
        ):
            mock_ox.graph_from_point.side_effect = InsufficientResponseError("No data")

            with pytest.raises(OSMFetchError, match="No street data"):
                fetch_graph((0.0, 0.0), 5000.0)


class TestFetchFeatures:
    """Tests for fetch_features function."""

    def test_returns_cached_features(self, tmp_path: Path) -> None:
        """Test that cached features are returned without API call."""
        mock_gdf = MagicMock()

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=mock_gdf),
            patch("maptoposter.geo.ox") as mock_ox,
        ):
            result = fetch_features((51.5074, -0.1278), 5000.0, {"natural": "water"}, "water")

            assert result is mock_gdf
            mock_ox.features_from_point.assert_not_called()

    def test_fetches_features_on_cache_miss(self, tmp_path: Path) -> None:
        """Test that features are fetched from OSM on cache miss."""
        mock_gdf = MagicMock()

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.cache_set", return_value=True),
            patch("maptoposter.geo.ox") as mock_ox,
            patch("maptoposter.geo.time.sleep"),
        ):
            mock_ox.features_from_point.return_value = mock_gdf

            result = fetch_features((51.5074, -0.1278), 5000.0, {"natural": "water"}, "water")

            assert result is mock_gdf
            mock_ox.features_from_point.assert_called_once()

    def test_raises_on_network_timeout(self, tmp_path: Path) -> None:
        """Test that OSMFetchError is raised on network timeout."""
        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.ox") as mock_ox,
        ):
            mock_ox.features_from_point.side_effect = Timeout("Request timed out")

            with pytest.raises(OSMFetchError, match="Network error"):
                fetch_features((51.5074, -0.1278), 5000.0, {"natural": "water"}, "water")

    def test_raises_on_connection_error(self, tmp_path: Path) -> None:
        """Test that OSMFetchError is raised on connection error."""
        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=None),
            patch("maptoposter.geo.ox") as mock_ox,
        ):
            mock_ox.features_from_point.side_effect = RequestsConnectionError("No connection")

            with pytest.raises(OSMFetchError, match="Network error"):
                fetch_features((51.5074, -0.1278), 5000.0, {"leisure": "park"}, "parks")

    def test_cache_key_includes_tags_hash(self, tmp_path: Path) -> None:
        """Test that cache key changes when tags change."""
        mock_gdf = MagicMock()

        with (
            patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}),
            patch("maptoposter.geo.cache_get", return_value=None) as mock_cache_get,
            patch("maptoposter.geo.cache_set", return_value=True),
            patch("maptoposter.geo.ox") as mock_ox,
            patch("maptoposter.geo.time.sleep"),
        ):
            mock_ox.features_from_point.return_value = mock_gdf

            # Fetch with water tags
            fetch_features((51.5, -0.1), 5000.0, {"natural": "water"}, "features")

            # Fetch with park tags (different tags)
            fetch_features((51.5, -0.1), 5000.0, {"leisure": "park"}, "features")

            # Should have been called with different cache keys
            calls = mock_cache_get.call_args_list
            assert len(calls) == 2
            # Cache keys should be different due to tags hash
            assert calls[0][0][0] != calls[1][0][0]


class TestGetCropLimits:
    """Tests for get_crop_limits function."""

    def test_portrait_aspect_ratio(self) -> None:
        """Test crop limits calculation for portrait aspect ratio."""
        mock_graph = MagicMock()
        mock_graph.graph = {"crs": "EPSG:32632"}

        mock_fig = MagicMock()
        mock_fig.get_size_inches.return_value = (8.0, 12.0)

        mock_point = MagicMock()
        mock_point.x = 500000.0
        mock_point.y = 5500000.0

        with patch("maptoposter.geo.ox.projection.project_geometry") as mock_project:
            mock_project.return_value = (mock_point, None)

            xlim, ylim = get_crop_limits(mock_graph, (51.5074, -0.1278), mock_fig, 10000.0)

            # For portrait (8/12 = 0.67 < 1), width should be reduced
            # half_y = 10000, half_x = 10000 * 0.67 = 6666.67
            expected_half_x = 10000.0 * (8.0 / 12.0)
            assert xlim[0] == pytest.approx(500000.0 - expected_half_x)
            assert xlim[1] == pytest.approx(500000.0 + expected_half_x)
            assert ylim[0] == pytest.approx(5500000.0 - 10000.0)
            assert ylim[1] == pytest.approx(5500000.0 + 10000.0)

    def test_landscape_aspect_ratio(self) -> None:
        """Test crop limits calculation for landscape aspect ratio."""
        mock_graph = MagicMock()
        mock_graph.graph = {"crs": "EPSG:32632"}

        mock_fig = MagicMock()
        mock_fig.get_size_inches.return_value = (12.0, 8.0)

        mock_point = MagicMock()
        mock_point.x = 500000.0
        mock_point.y = 5500000.0

        with patch("maptoposter.geo.ox.projection.project_geometry") as mock_project:
            mock_project.return_value = (mock_point, None)

            xlim, ylim = get_crop_limits(mock_graph, (51.5074, -0.1278), mock_fig, 10000.0)

            # For landscape (12/8 = 1.5 > 1), height should be reduced
            # half_x = 10000, half_y = 10000 / 1.5 = 6666.67
            expected_half_y = 10000.0 / (12.0 / 8.0)
            assert xlim[0] == pytest.approx(500000.0 - 10000.0)
            assert xlim[1] == pytest.approx(500000.0 + 10000.0)
            assert ylim[0] == pytest.approx(5500000.0 - expected_half_y)
            assert ylim[1] == pytest.approx(5500000.0 + expected_half_y)

    def test_square_aspect_ratio(self) -> None:
        """Test crop limits calculation for square aspect ratio."""
        mock_graph = MagicMock()
        mock_graph.graph = {"crs": "EPSG:32632"}

        mock_fig = MagicMock()
        mock_fig.get_size_inches.return_value = (10.0, 10.0)

        mock_point = MagicMock()
        mock_point.x = 500000.0
        mock_point.y = 5500000.0

        with patch("maptoposter.geo.ox.projection.project_geometry") as mock_project:
            mock_project.return_value = (mock_point, None)

            xlim, ylim = get_crop_limits(mock_graph, (51.5074, -0.1278), mock_fig, 10000.0)

            # For square (1:1), both dimensions should use full dist
            assert xlim[0] == pytest.approx(500000.0 - 10000.0)
            assert xlim[1] == pytest.approx(500000.0 + 10000.0)
            assert ylim[0] == pytest.approx(5500000.0 - 10000.0)
            assert ylim[1] == pytest.approx(5500000.0 + 10000.0)
