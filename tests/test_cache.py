"""Tests for the cache module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from maptoposter.cache import cache_get, cache_set, get_cache_dir


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

    def test_cache_roundtrip(self, tmp_path: Path) -> None:
        """Test that values can be cached and retrieved."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            test_data = {"key": "value", "number": 42}
            cache_set("test_key", test_data)

            result = cache_get("test_key")
            assert result == test_data

    def test_cache_miss(self, tmp_path: Path) -> None:
        """Test that cache miss returns None."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            result = cache_get("nonexistent_key")
            assert result is None

    def test_cache_complex_objects(self, tmp_path: Path) -> None:
        """Test caching of complex nested objects."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            test_data = {
                "coords": (40.7128, -74.0060),
                "nested": {"a": [1, 2, 3], "b": {"c": "d"}},
            }
            cache_set("complex_key", test_data)

            result = cache_get("complex_key")
            assert result == test_data
