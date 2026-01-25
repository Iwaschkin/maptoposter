"""Tests for the config module."""

from __future__ import annotations

from pathlib import Path

import pytest

from maptoposter.config import (
    REQUIRED_THEME_KEYS,
    PosterConfig,
    ThemeValidationError,
    generate_output_filename,
    get_available_themes,
    load_theme,
)


class TestThemes:
    """Tests for theme loading functions."""

    def test_get_available_themes_returns_list(self) -> None:
        """Test that get_available_themes returns a list."""
        themes = get_available_themes()
        assert isinstance(themes, list)

    def test_load_default_theme(self) -> None:
        """Test loading the default theme."""
        theme = load_theme("feature_based")
        assert isinstance(theme, dict)
        assert "bg" in theme
        assert "text" in theme
        assert "road_motorway" in theme

    def test_load_nonexistent_theme_falls_back(self) -> None:
        """Test that loading nonexistent theme returns default."""
        theme = load_theme("nonexistent_theme_xyz")
        assert isinstance(theme, dict)
        assert theme["bg"] == "#FFFFFF"


class TestOutputFilename:
    """Tests for filename generation."""

    def test_generate_output_filename_format(self) -> None:
        """Test output filename format."""
        filename = generate_output_filename("New York", "noir", "png")
        assert isinstance(filename, Path)
        assert "new_york" in filename.stem
        assert "noir" in filename.stem
        assert filename.suffix == ".png"

    def test_generate_output_filename_svg(self) -> None:
        """Test SVG output format."""
        filename = generate_output_filename("Tokyo", "japanese_ink", "svg")
        assert filename.suffix == ".svg"


class TestPosterConfig:
    """Tests for PosterConfig dataclass."""

    def test_config_creation(self) -> None:
        """Test creating a basic config."""
        config = PosterConfig(city="Paris", country="France")
        assert config.city == "Paris"
        assert config.country == "France"
        assert config.theme_name == "feature_based"
        assert config.distance == 29000

    def test_config_with_options(self) -> None:
        """Test config with custom options."""
        config = PosterConfig(
            city="Tokyo",
            country="Japan",
            theme_name="noir",
            distance=15000,
            width=18.0,
            height=24.0,
        )
        assert config.distance == 15000
        assert config.width == 18.0
        assert config.height == 24.0

    def test_config_loads_theme(self) -> None:
        """Test that config loads theme on init."""
        config = PosterConfig(city="Berlin", country="Germany")
        assert isinstance(config.theme, dict)


# =============================================================================
# Parametric Theme Tests (CR-0018)
# =============================================================================


class TestAllThemesParametric:
    """Parametric tests that run against all available themes."""

    @pytest.mark.parametrize("theme_name", get_available_themes())
    def test_theme_loads_successfully(self, theme_name: str) -> None:
        """Test that each theme file loads without error."""
        theme = load_theme(theme_name)
        assert isinstance(theme, dict)
        assert "name" in theme

    @pytest.mark.parametrize("theme_name", get_available_themes())
    def test_theme_has_required_keys(self, theme_name: str) -> None:
        """Test that each theme has all required keys."""
        theme = load_theme(theme_name)
        missing = REQUIRED_THEME_KEYS - theme.keys()
        assert not missing, f"Theme {theme_name} missing keys: {missing}"

    @pytest.mark.parametrize("theme_name", get_available_themes())
    def test_theme_colors_are_valid(self, theme_name: str) -> None:
        """Test that theme color values look like valid hex colors."""
        theme = load_theme(theme_name)

        color_keys = [
            "bg",
            "text",
            "gradient_color",
            "water",
            "parks",
            "road_motorway",
            "road_primary",
            "road_secondary",
            "road_tertiary",
            "road_residential",
            "road_default",
        ]

        for key in color_keys:
            if key in theme:
                color = theme[key]
                # Should be a hex color string starting with #
                assert isinstance(color, str), f"{key} should be string"
                assert color.startswith("#"), f"{key} should start with #"
                # Should be either #RGB, #RRGGBB, or #RRGGBBAA
                assert len(color) in [4, 7, 9], f"{key} has invalid length"


class TestThemeValidation:
    """Tests for theme validation logic."""

    def test_required_theme_keys_is_frozen(self) -> None:
        """Test that REQUIRED_THEME_KEYS is a frozenset."""
        assert isinstance(REQUIRED_THEME_KEYS, frozenset)

    def test_required_keys_includes_essential_keys(self) -> None:
        """Test that required keys includes essential elements."""
        assert "bg" in REQUIRED_THEME_KEYS
        assert "text" in REQUIRED_THEME_KEYS
        assert "road_motorway" in REQUIRED_THEME_KEYS
        assert "water" in REQUIRED_THEME_KEYS
        assert "parks" in REQUIRED_THEME_KEYS

    def test_theme_validation_error_exists(self) -> None:
        """Test ThemeValidationError can be raised."""
        with pytest.raises(ThemeValidationError):
            raise ThemeValidationError("Test error")

    def test_theme_validation_error_is_value_error(self) -> None:
        """Test ThemeValidationError is a ValueError subclass."""
        assert issubclass(ThemeValidationError, ValueError)
