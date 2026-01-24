"""Tests for the config module."""

from __future__ import annotations

from pathlib import Path

from maptoposter.config import (
    PosterConfig,
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
