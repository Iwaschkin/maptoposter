"""Caching utilities for map data."""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any


__all__ = ["CacheError", "cache_get", "cache_set", "get_cache_dir"]


class CacheError(Exception):
    """Raised when a cache operation fails."""

    pass


def get_cache_dir() -> Path:
    """Get the cache directory path, creating it if necessary."""
    cache_path = Path(os.environ.get("MAPTOPOSTER_CACHE_DIR", ".cache"))
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


def _cache_path(key: str) -> Path:
    """Generate a safe cache file path for a given key."""
    safe = key.replace(os.sep, "_").replace("/", "_").replace("\\", "_")
    return get_cache_dir() / f"{safe}.pkl"


def cache_get(key: str) -> Any | None:
    """Retrieve a cached value by key.

    Args:
        key: The cache key to look up.

    Returns:
        The cached value if found, None otherwise.

    Raises:
        CacheError: If reading the cache fails.
    """
    try:
        path = _cache_path(key)
        if not path.exists():
            return None
        with path.open("rb") as f:
            return pickle.load(f)
    except Exception as e:
        raise CacheError(f"Cache read failed: {e}") from e


def cache_set(key: str, value: Any) -> None:
    """Store a value in the cache.

    Args:
        key: The cache key.
        value: The value to cache.

    Raises:
        CacheError: If writing to the cache fails.
    """
    try:
        path = _cache_path(key)
        with path.open("wb") as f:
            pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise CacheError(f"Cache write failed: {e}") from e
