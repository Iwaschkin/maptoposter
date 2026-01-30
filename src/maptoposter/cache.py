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
from typing import TYPE_CHECKING, Any, TypeAlias


if TYPE_CHECKING:
    from geopandas import GeoDataFrame
    from networkx import MultiDiGraph

# Type alias for cached values - defined at module level for runtime access
# The actual types are only available at type-checking time
CacheValue: TypeAlias = "tuple[float, float] | MultiDiGraph | GeoDataFrame"

__all__ = [
    "CacheType",
    "cache_get",
    "cache_set",
    "clear_cache",
    "get_cache_dir",
    "get_cache_stats",
]


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


def cache_get(key: str, cache_type: CacheType) -> CacheValue | None:
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
            logger.debug("Cache miss", extra={"key": key, "type": cache_type.value})
            return None

        if cache_type == CacheType.COORDS:
            data = json.loads(path.read_text(encoding="utf-8"))
            # Convert list back to tuple for coordinates
            if isinstance(data, list) and len(data) == 2:
                logger.debug("Cache hit", extra={"key": key, "type": cache_type.value})
                return tuple(data)
            logger.debug("Cache hit", extra={"key": key, "type": cache_type.value})
            return data

        if cache_type == CacheType.GRAPH:
            import osmnx as ox

            result = ox.load_graphml(path)
            logger.debug("Cache hit", extra={"key": key, "type": cache_type.value})
            return result

        if cache_type == CacheType.GEODATA:
            import geopandas as gpd

            result = gpd.read_parquet(path)
            logger.debug("Cache hit", extra={"key": key, "type": cache_type.value})
            return result

        return None  # Unknown type

    except Exception as e:
        logger.warning("Cache read error for %s: %s", key, e)
        return None


def cache_set(key: str, value: CacheValue, cache_type: CacheType) -> bool:
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
            # GeoDataFrame has to_parquet method
            value.to_parquet(path)  # type: ignore[union-attr]

        else:
            logger.warning("Unknown cache type: %s", cache_type)
            return False

        logger.debug("Cache write", extra={"key": key, "type": cache_type.value})
        return True

    except Exception as e:
        logger.warning("Cache write error for %s: %s", key, e)
        return False


def get_cache_stats() -> dict[str, Any]:
    """Get statistics about the cache.

    Returns:
        Dict with cache statistics including:
        - total_files: Number of cached files
        - total_size_mb: Total size in megabytes
        - by_type: Breakdown by cache type (coords, graph, geodata)
    """
    cache_dir = get_cache_dir()
    stats: dict[str, Any] = {
        "total_files": 0,
        "total_size_bytes": 0,
        "total_size_mb": 0.0,
        "by_type": {
            "coords": {"files": 0, "size_bytes": 0},
            "graph": {"files": 0, "size_bytes": 0},
            "geodata": {"files": 0, "size_bytes": 0},
        },
    }

    if not cache_dir.exists():
        return stats

    for cache_type in CacheType:
        ext = _get_extension(cache_type)
        for path in cache_dir.glob(f"*{ext}"):
            size = path.stat().st_size
            stats["total_files"] += 1
            stats["total_size_bytes"] += size
            stats["by_type"][cache_type.value]["files"] += 1
            stats["by_type"][cache_type.value]["size_bytes"] += size

    stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
    for cache_type in CacheType:
        bytes_val = stats["by_type"][cache_type.value]["size_bytes"]
        stats["by_type"][cache_type.value]["size_mb"] = round(bytes_val / (1024 * 1024), 2)

    return stats


def clear_cache(cache_type: CacheType | None = None) -> int:
    """Clear the cache.

    Args:
        cache_type: Optional type to clear. If None, clears all cache files.

    Returns:
        Number of files deleted.
    """
    cache_dir = get_cache_dir()
    deleted = 0

    if not cache_dir.exists():
        return 0

    if cache_type is not None:
        # Clear specific type
        ext = _get_extension(cache_type)
        for path in cache_dir.glob(f"*{ext}"):
            try:
                path.unlink()
                deleted += 1
                logger.debug("Deleted cache file: %s", path)
            except Exception as e:
                logger.warning("Failed to delete %s: %s", path, e)
    else:
        # Clear all types
        for ct in CacheType:
            ext = _get_extension(ct)
            for path in cache_dir.glob(f"*{ext}"):
                try:
                    path.unlink()
                    deleted += 1
                    logger.debug("Deleted cache file: %s", path)
                except Exception as e:
                    logger.warning("Failed to delete %s: %s", path, e)

    logger.info("Cleared %d cache files", deleted)
    return deleted
