"""Tests for the cache module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from maptoposter.cache import (
    CacheType,
    cache_get,
    cache_set,
    clear_cache,
    get_cache_dir,
    get_cache_stats,
)


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


class TestCacheStats:
    """Tests for get_cache_stats function."""

    def test_empty_cache_stats(self, tmp_path: Path) -> None:
        """Test stats for an empty cache."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            stats = get_cache_stats()
            assert stats["total_files"] == 0
            assert stats["total_size_mb"] == 0.0
            assert stats["by_type"]["coords"]["files"] == 0

    def test_stats_with_cached_data(self, tmp_path: Path) -> None:
        """Test stats after caching some data."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            # Add some test data
            cache_set("test1", (40.0, -74.0), CacheType.COORDS)
            cache_set("test2", (35.0, 139.0), CacheType.COORDS)

            stats = get_cache_stats()
            assert stats["total_files"] == 2
            assert stats["total_size_bytes"] > 0
            assert stats["by_type"]["coords"]["files"] == 2

    def test_stats_keys_present(self, tmp_path: Path) -> None:
        """Test that all expected keys are present in stats."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            stats = get_cache_stats()
            assert "total_files" in stats
            assert "total_size_bytes" in stats
            assert "total_size_mb" in stats
            assert "by_type" in stats
            assert "coords" in stats["by_type"]
            assert "graph" in stats["by_type"]
            assert "geodata" in stats["by_type"]


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clear_empty_cache(self, tmp_path: Path) -> None:
        """Test clearing an empty cache returns 0."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            deleted = clear_cache()
            assert deleted == 0

    def test_clear_all_cache(self, tmp_path: Path) -> None:
        """Test clearing all cached data."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            # Add some test data
            cache_set("test1", (40.0, -74.0), CacheType.COORDS)
            cache_set("test2", (35.0, 139.0), CacheType.COORDS)

            # Verify data exists
            assert get_cache_stats()["total_files"] == 2

            # Clear and verify
            deleted = clear_cache()
            assert deleted == 2
            assert get_cache_stats()["total_files"] == 0

    def test_clear_specific_type(self, tmp_path: Path) -> None:
        """Test clearing only a specific cache type."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            # Add coord data
            cache_set("test1", (40.0, -74.0), CacheType.COORDS)
            cache_set("test2", (35.0, 139.0), CacheType.COORDS)

            # Clear only coords
            deleted = clear_cache(CacheType.COORDS)
            assert deleted == 2
            assert get_cache_stats()["by_type"]["coords"]["files"] == 0
