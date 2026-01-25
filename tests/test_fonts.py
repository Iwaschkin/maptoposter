"""Tests for the fonts module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from matplotlib.font_manager import FontProperties

from maptoposter.fonts import FontSet, load_fonts


class TestFontSet:
    """Tests for FontSet class."""

    def test_font_set_is_loaded_all_present(self, tmp_path: Path) -> None:
        """Test is_loaded returns True when all fonts exist."""
        # Create mock font files
        for name in ["bold.ttf", "regular.ttf", "light.ttf"]:
            (tmp_path / name).touch()

        font_set = FontSet(
            bold=tmp_path / "bold.ttf",
            regular=tmp_path / "regular.ttf",
            light=tmp_path / "light.ttf",
        )
        assert font_set.is_loaded is True

    def test_font_set_is_loaded_missing_font(self, tmp_path: Path) -> None:
        """Test is_loaded returns False when a font is missing."""
        (tmp_path / "bold.ttf").touch()
        (tmp_path / "regular.ttf").touch()
        # light.ttf not created

        font_set = FontSet(
            bold=tmp_path / "bold.ttf",
            regular=tmp_path / "regular.ttf",
            light=None,  # Missing font
        )
        assert font_set.is_loaded is False

    def test_font_set_is_loaded_all_none(self) -> None:
        """Test is_loaded returns False when all fonts are None."""
        font_set = FontSet(bold=None, regular=None, light=None)
        assert font_set.is_loaded is False


class TestGetProperties:
    """Tests for FontSet.get_properties method."""

    def test_get_properties_with_existing_font(self, tmp_path: Path) -> None:
        """Test get_properties returns FontProperties with correct font."""
        # Create a mock font file
        font_file = tmp_path / "regular.ttf"
        font_file.write_bytes(b"fake font data")

        font_set = FontSet(regular=font_file)
        props = font_set.get_properties("regular", 14.0)

        assert isinstance(props, FontProperties)
        assert props.get_size() == 14.0

    def test_get_properties_fallback_to_regular(self, tmp_path: Path) -> None:
        """Test get_properties falls back to regular when weight not found."""
        font_file = tmp_path / "regular.ttf"
        font_file.write_bytes(b"fake font data")

        font_set = FontSet(regular=font_file, bold=None, light=None)
        # Request bold, but it's None, should fall back to regular
        props = font_set.get_properties("bold", 12.0)

        assert isinstance(props, FontProperties)
        assert props.get_size() == 12.0

    def test_get_properties_fallback_to_system_fonts(self) -> None:
        """Test get_properties falls back to system fonts when no fonts available."""
        font_set = FontSet(bold=None, regular=None, light=None)
        props = font_set.get_properties("regular", 16.0)

        assert isinstance(props, FontProperties)
        assert props.get_size() == 16.0
        # Should be system sans-serif
        assert "sans-serif" in props.get_family()

    def test_get_properties_missing_weight_uses_system(self) -> None:
        """Test that missing weight with no regular falls back to system."""
        font_set = FontSet(bold=None, regular=None, light=None)
        props = font_set.get_properties("nonexistent", 10.0)

        assert isinstance(props, FontProperties)
        assert "sans-serif" in props.get_family()

    def test_get_properties_weight_map_bold(self) -> None:
        """Test bold weight maps correctly for system fonts."""
        font_set = FontSet(bold=None, regular=None, light=None)
        props = font_set.get_properties("bold", 12.0)

        assert props.get_weight() == "bold"

    def test_get_properties_weight_map_light(self) -> None:
        """Test light weight maps correctly for system fonts."""
        font_set = FontSet(bold=None, regular=None, light=None)
        props = font_set.get_properties("light", 12.0)

        assert props.get_weight() == "light"


class TestLoadFonts:
    """Tests for load_fonts function."""

    def test_load_fonts_returns_font_set(self) -> None:
        """Test load_fonts returns a FontSet instance."""
        fonts = load_fonts()
        assert isinstance(fonts, FontSet)

    def test_load_fonts_has_expected_paths(self) -> None:
        """Test load_fonts sets paths for Roboto fonts."""
        fonts = load_fonts()

        # Check that paths are set (may be None if fonts don't exist)
        # The important thing is they're Path objects or None
        if fonts.bold is not None:
            assert fonts.bold.name == "Roboto-Bold.ttf"
        if fonts.regular is not None:
            assert fonts.regular.name == "Roboto-Regular.ttf"
        if fonts.light is not None:
            assert fonts.light.name == "Roboto-Light.ttf"

    def test_load_fonts_with_missing_directory(self, tmp_path: Path) -> None:
        """Test load_fonts handles missing fonts directory gracefully."""
        with patch("maptoposter.fonts.get_fonts_dir", return_value=tmp_path / "nonexistent"):
            fonts = load_fonts()
            # Should return FontSet with None paths for missing fonts
            assert fonts.bold is None or not fonts.bold.exists()


class TestFontFallbackIntegration:
    """Integration tests for font fallback behavior (CR-0014)."""

    def test_missing_all_fonts_does_not_raise(self) -> None:
        """Test that missing all fonts doesn't raise AttributeError."""
        font_set = FontSet(bold=None, regular=None, light=None)

        # This should not raise AttributeError: 'NoneType' has no attribute 'exists'
        props = font_set.get_properties("regular", 12.0)
        assert props is not None

    def test_missing_requested_weight_falls_back(self) -> None:
        """Test missing weight falls back gracefully."""
        font_set = FontSet(bold=None, regular=None, light=None)

        # Request nonexistent weight
        props = font_set.get_properties("extralight", 12.0)
        assert props is not None
        assert isinstance(props, FontProperties)
