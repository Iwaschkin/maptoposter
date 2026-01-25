"""Caching utilities for map data.

This module provides safe caching using JSON, GraphML, and GeoParquet formats.
No pickle serialization is used to prevent arbitrary code execution vulnerabilities.
"""

from __future__ import annotations

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    pass  # Types imported only for type checking


__all__ = ["CacheType", "cache_get", "cache_set", "get_cache_dir"]


logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Types of data that can be cached, each with its own format."""

    COORDS = "coords"  # JSON format
    GRAPH = "graph"  # GraphML format
    GEODATA = "geodata"  # GeoParquet format


def get_cache_dir() -> Path:
    """Get the cache directory path, creating it if necessary."""
    cache_path = Path(os.environ.get("MAPTOPOSTER_CACHE_DIR", ".cache"))
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


def _get_extension(cache_type: CacheType) -> str:
    """Get the file extension for a cache type."""
    extensions = {
        CacheType.COORDS: ".json",
        CacheType.GRAPH: ".graphml",
        CacheType.GEODATA: ".parquet",
    }
    return extensions[cache_type]


def _cache_path(key: str, cache_type: CacheType) -> Path:
    """Generate a safe cache file path for a given key and type."""
    safe = key.replace(os.sep, "_").replace("/", "_").replace("\\", "_")
    ext = _get_extension(cache_type)
    return get_cache_dir() / f"{safe}{ext}"


def cache_get(key: str, cache_type: CacheType) -> Any | None:
    """Retrieve a cached value by key.

    Uses safe deserialization formats (JSON, GraphML, GeoParquet) to prevent
    arbitrary code execution vulnerabilities.

    Args:
        key: The cache key to look up.
        cache_type: The type of data being cached.

    Returns:
        The cached value if found, None on cache miss or error.
    """
    try:
        path = _cache_path(key, cache_type)
        if not path.exists():
            return None

        if cache_type == CacheType.COORDS:
            data = json.loads(path.read_text(encoding="utf-8"))
            # Convert list back to tuple for coordinates
            if isinstance(data, list) and len(data) == 2:
                return tuple(data)
            return data

        elif cache_type == CacheType.GRAPH:
            import osmnx as ox

            return ox.load_graphml(path)

        elif cache_type == CacheType.GEODATA:
            import geopandas as gpd

            return gpd.read_parquet(path)

        return None  # Unknown type

    except Exception as e:
        logger.warning("Cache read error for %s: %s", key, e)
        return None


def cache_set(key: str, value: Any, cache_type: CacheType) -> bool:
    """Store a value in the cache.

    Uses safe serialization formats (JSON, GraphML, GeoParquet) to prevent
    arbitrary code execution vulnerabilities on load.

    Args:
        key: The cache key.
        value: The value to cache.
        cache_type: The type of data being cached.

    Returns:
        True if successful, False on error.
    """
    try:
        path = _cache_path(key, cache_type)

        if cache_type == CacheType.COORDS:
            # Ensure coords are serializable (convert tuple to list)
            if isinstance(value, tuple):
                value = list(value)
            path.write_text(json.dumps(value), encoding="utf-8")

        elif cache_type == CacheType.GRAPH:
            import osmnx as ox

            ox.save_graphml(value, path)

        elif cache_type == CacheType.GEODATA:
            value.to_parquet(path)

        else:
            logger.warning("Unknown cache type: %s", cache_type)
            return False

        return True

    except Exception as e:
        logger.warning("Cache write error for %s: %s", key, e)
        return False
