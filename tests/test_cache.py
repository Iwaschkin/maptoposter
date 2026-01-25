"""Tests for the cache module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from maptoposter.cache import CacheType, cache_get, cache_set, get_cache_dir


class TestCacheDir:
    """Tests for get_cache_dir function."""

    def test_default_cache_dir(self) -> None:
        """Test that default cache directory is .cache."""
        with patch.dict("os.environ", {}, clear=True):
            cache_dir = get_cache_dir()
            assert cache_dir.name == ".cache"

    def test_custom_cache_dir(self, tmp_path: Path) -> None:
        """Test that custom cache directory is respected."""
        custom_dir = tmp_path / "custom_cache"
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(custom_dir)}):
            cache_dir = get_cache_dir()
            assert cache_dir == custom_dir
            assert cache_dir.exists()


class TestCacheOperations:
    """Tests for cache_get and cache_set functions."""

    def test_cache_coords_roundtrip(self, tmp_path: Path) -> None:
        """Test that coordinate tuples can be cached and retrieved."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            test_coords = (40.7128, -74.0060)
            result = cache_set("test_coords", test_coords, CacheType.COORDS)
            assert result is True

            retrieved = cache_get("test_coords", CacheType.COORDS)
            assert retrieved == test_coords

    def test_cache_miss(self, tmp_path: Path) -> None:
        """Test that cache miss returns None."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            result = cache_get("nonexistent_key", CacheType.COORDS)
            assert result is None

    def test_cache_set_returns_bool(self, tmp_path: Path) -> None:
        """Test that cache_set returns success indicator."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            test_data = {"key": "value", "number": 42}
            result = cache_set("bool_test", test_data, CacheType.COORDS)
            assert isinstance(result, bool)
            assert result is True

    def test_cache_get_returns_none_on_missing(self, tmp_path: Path) -> None:
        """Test that cache_get returns None for missing keys, not raises."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            result = cache_get("definitely_missing", CacheType.COORDS)
            assert result is None
