"""Geographic data fetching and processing."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

import osmnx as ox
from geopy.geocoders import Nominatim
from shapely.geometry import Point

from .cache import CacheError, cache_get, cache_set


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
    cached = cache_get(cache_key)
    if cached is not None:
        print(f"✓ Using cached coordinates for {city}, {country}")
        return cast("tuple[float, float]", cached)

    print("Looking up coordinates...")
    geolocator = Nominatim(user_agent="maptoposter")
    geolocator.timeout = 10

    # Add a small delay to respect Nominatim's usage policy
    time.sleep(1)

    try:
        location = geolocator.geocode(f"{city}, {country}")
    except Exception as e:
        raise ValueError(f"Geocoding failed for {city}, {country}: {e}") from e

    # Handle coroutine if returned in async environments
    if asyncio.iscoroutine(location):
        try:
            location = asyncio.run(location)
        except RuntimeError as err:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise RuntimeError(
                    "Geocoder returned a coroutine while an event loop is "
                    "already running. Run this script in a synchronous environment."
                ) from err
            location = loop.run_until_complete(location)

    if location:
        addr = getattr(location, "address", None)
        if addr:
            print(f"✓ Found: {addr}")
        else:
            print("✓ Found location (address not available)")
        print(f"✓ Coordinates: {location.latitude}, {location.longitude}")

        coords = (float(location.latitude), float(location.longitude))
        try:
            cache_set(cache_key, coords)
        except CacheError as e:
            print(f"Warning: {e}")
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
    cached = cache_get(cache_key)
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
        # Rate limit between requests
        time.sleep(0.5)
        try:
            cache_set(cache_key, graph)
        except CacheError as e:
            print(f"Warning: {e}")
        return graph
    except Exception as e:
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
    cached = cache_get(cache_key)
    if cached is not None:
        print(f"✓ Using cached {name}")
        return cast("GeoDataFrame", cached)

    try:
        data = ox.features_from_point(point, tags=dict(tags), dist=dist)
        # Rate limit between requests
        time.sleep(0.3)
        try:
            cache_set(cache_key, data)
        except CacheError as e:
            print(f"Warning: {e}")
        return data
    except Exception as e:
        print(f"OSMnx error while fetching features: {e}")
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
