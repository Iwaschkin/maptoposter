"""Geographic data fetching and processing."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

import osmnx as ox
from geopy.geocoders import Nominatim
from requests.exceptions import ConnectionError, HTTPError, Timeout
from shapely.geometry import Point

from .cache import CacheType, cache_get, cache_set


if TYPE_CHECKING:
    from geopandas import GeoDataFrame
    from matplotlib.figure import Figure
    from networkx import MultiDiGraph

__all__ = [
    "fetch_features",
    "fetch_graph",
    "get_coordinates",
    "get_crop_limits",
]

logger = logging.getLogger(__name__)


def get_coordinates(city: str, country: str) -> tuple[float, float]:
    """Fetch coordinates for a given city and country using geopy.

    Includes rate limiting to be respectful to the geocoding service.
    Results are cached to avoid repeated API calls.

    Args:
        city: The city name.
        country: The country name.

    Returns:
        A tuple of (latitude, longitude).

    Raises:
        ValueError: If the location cannot be found.
    """
    cache_key = f"coords_{city.lower()}_{country.lower()}"
    cached = cache_get(cache_key, CacheType.COORDS)
    if cached is not None:
        print(f"✓ Using cached coordinates for {city}, {country}")
        return cast("tuple[float, float]", cached)

    print("Looking up coordinates...")
    geolocator = Nominatim(user_agent="maptoposter")
    geolocator.timeout = 10

    try:
        location = geolocator.geocode(f"{city}, {country}")
    except (ConnectionError, Timeout) as e:
        logger.error("Network error during geocoding: %s", e)
        raise ValueError(f"Network error during geocoding for {city}, {country}: {e}") from e
    except Exception as e:
        logger.error("Geocoding failed: %s", e)
        raise ValueError(f"Geocoding failed for {city}, {country}: {e}") from e

    if location:
        addr = getattr(location, "address", None)
        if addr:
            print(f"✓ Found: {addr}")
        else:
            print("✓ Found location (address not available)")
        print(f"✓ Coordinates: {location.latitude}, {location.longitude}")

        coords = (float(location.latitude), float(location.longitude))

        # Rate limit AFTER successful API call
        time.sleep(1)

        if not cache_set(cache_key, coords, CacheType.COORDS):
            logger.warning("Failed to cache coordinates for %s", cache_key)
        return coords

    raise ValueError(f"Could not find coordinates for {city}, {country}")


def fetch_graph(point: tuple[float, float], dist: float) -> MultiDiGraph | None:
    """Fetch the street network graph for a location.

    Args:
        point: A tuple of (latitude, longitude).
        dist: The distance in meters from the point.

    Returns:
        A NetworkX MultiDiGraph of the street network, or None on failure.
    """
    lat, lon = point
    cache_key = f"graph_{lat}_{lon}_{dist}"
    cached = cache_get(cache_key, CacheType.GRAPH)
    if cached is not None:
        print("✓ Using cached street network")
        return cast("MultiDiGraph", cached)

    try:
        graph = ox.graph_from_point(
            point,
            dist=dist,
            dist_type="bbox",
            network_type="all",
            truncate_by_edge=True,
        )
        # Rate limit AFTER successful API call
        time.sleep(0.5)

        if not cache_set(cache_key, graph, CacheType.GRAPH):
            logger.warning("Failed to cache graph for %s", cache_key)
        return graph
    except (ConnectionError, Timeout) as e:
        logger.error("Network error fetching street network: %s", e)
        print(f"Network error fetching street network: {e}")
        print("Check your internet connection and try again.")
        return None
    except HTTPError as e:
        if hasattr(e, "response") and e.response is not None and e.response.status_code == 429:
            logger.error("Rate limited by OSM API")
            print("Rate limited by OSM API. Please wait and try again.")
        else:
            logger.error("HTTP error from OSM API: %s", e)
            print(f"HTTP error from OSM API: {e}")
        return None
    except Exception as e:
        # Check for osmnx InsufficientResponseError
        if "InsufficientResponseError" in type(e).__name__ or "EmptyOverpassResponse" in str(e):
            logger.warning("No street data available for this location")
            print("No street data available for this location.")
        else:
            logger.error("Unexpected error fetching OSM graph: %s", e, exc_info=True)
            print(f"OSMnx error while fetching graph: {e}")
        return None


def fetch_features(
    point: tuple[float, float],
    dist: float,
    tags: Mapping[str, bool | str | list[str]],
    name: str,
) -> GeoDataFrame | None:
    """Fetch geographic features (water, parks, etc.) for a location.

    Args:
        point: A tuple of (latitude, longitude).
        dist: The distance in meters from the point.
        tags: OpenStreetMap tags to query.
        name: A descriptive name for caching.

    Returns:
        A GeoDataFrame of features, or None on failure.
    """
    lat, lon = point
    tag_str = "_".join(tags.keys())
    cache_key = f"{name}_{lat}_{lon}_{dist}_{tag_str}"
    cached = cache_get(cache_key, CacheType.GEODATA)
    if cached is not None:
        print(f"✓ Using cached {name}")
        return cast("GeoDataFrame", cached)

    try:
        data = ox.features_from_point(point, tags=dict(tags), dist=dist)
        # Rate limit AFTER successful API call
        time.sleep(0.3)

        if not cache_set(cache_key, data, CacheType.GEODATA):
            logger.warning("Failed to cache %s for %s", name, cache_key)
        return data
    except (ConnectionError, Timeout) as e:
        logger.error("Network error fetching %s: %s", name, e)
        print(f"Network error fetching {name}: {e}")
        return None
    except HTTPError as e:
        if hasattr(e, "response") and e.response is not None and e.response.status_code == 429:
            logger.error("Rate limited by OSM API while fetching %s", name)
            print(f"Rate limited by OSM API while fetching {name}.")
        else:
            logger.error("HTTP error fetching %s: %s", name, e)
            print(f"HTTP error fetching {name}: {e}")
        return None
    except Exception as e:
        # Check for osmnx InsufficientResponseError
        if "InsufficientResponseError" in type(e).__name__ or "EmptyOverpassResponse" in str(e):
            logger.info("No %s data available for this location", name)
            print(f"No {name} data available for this location.")
        else:
            logger.error("Unexpected error fetching %s: %s", name, e, exc_info=True)
            print(f"OSMnx error while fetching {name}: {e}")
        return None


def get_crop_limits(
    g_proj: MultiDiGraph,
    center_lat_lon: tuple[float, float],
    fig: Figure,
    dist: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Calculate cropping limits to preserve aspect ratio while covering the requested radius.

    Args:
        g_proj: The projected street network graph.
        center_lat_lon: The center point (latitude, longitude).
        fig: The matplotlib figure.
        dist: The requested radius in meters.

    Returns:
        A tuple of ((x_min, x_max), (y_min, y_max)) limits.
    """
    lat, lon = center_lat_lon

    # Project center point into graph CRS
    center = ox.projection.project_geometry(
        Point(lon, lat),
        crs="EPSG:4326",
        to_crs=g_proj.graph["crs"],
    )[0]
    center_point = cast("Point", center)
    center_x, center_y = center_point.x, center_point.y

    fig_width, fig_height = fig.get_size_inches()
    aspect = fig_width / fig_height

    # Start from the requested radius
    half_x = dist
    half_y = dist

    # Adjust to match aspect ratio
    if aspect > 1:  # landscape → reduce height
        half_y = half_x / aspect
    else:  # portrait → reduce width
        half_x = half_y * aspect

    return (
        (center_x - half_x, center_x + half_x),
        (center_y - half_y, center_y + half_y),
    )
