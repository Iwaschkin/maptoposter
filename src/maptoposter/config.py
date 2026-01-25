"""Configuration and path management."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import cast


__all__ = [
    "PosterConfig",
    "ThemeValidationError",
    "generate_output_filename",
    "get_available_themes",
    "get_fonts_dir",
    "get_package_dir",
    "get_posters_dir",
    "get_themes_dir",
    "load_theme",
]


class ThemeValidationError(ValueError):
    """Raised when theme file is missing required keys."""

    pass


# Required keys that every theme must have
REQUIRED_THEME_KEYS = frozenset(
    {
        "name",
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
    }
)


def get_package_dir() -> Path:
    """Get the package installation directory."""
    return Path(__file__).parent


def get_themes_dir() -> Path:
    """Get the themes directory path."""
    # Check for themes in package data first, then fall back to cwd
    package_themes = get_package_dir() / "data" / "themes"
    if package_themes.exists():
        return package_themes

    cwd_themes = Path.cwd() / "themes"
    if cwd_themes.exists():
        return cwd_themes

    # Default to package data location
    return package_themes


def get_fonts_dir() -> Path:
    """Get the fonts directory path."""
    # Check for fonts in package data first, then fall back to cwd
    package_fonts = get_package_dir() / "data" / "fonts"
    if package_fonts.exists():
        return package_fonts

    cwd_fonts = Path.cwd() / "fonts"
    if cwd_fonts.exists():
        return cwd_fonts

    return package_fonts


def get_posters_dir() -> Path:
    """Get the posters output directory, creating it if necessary."""
    posters_dir = Path.cwd() / "posters"
    posters_dir.mkdir(parents=True, exist_ok=True)
    return posters_dir


def get_available_themes() -> list[str]:
    """Scan the themes directory and return a list of available theme names.

    Returns:
        A sorted list of theme names (without .json extension).
        Empty list if themes directory doesn't exist.
    """
    themes_dir = get_themes_dir()
    if not themes_dir.exists():
        # Don't create directory - just return empty list (CR-0012 fix)
        return []

    return sorted(f.stem for f in themes_dir.glob("*.json"))


def load_theme(theme_name: str = "feature_based") -> dict[str, str]:
    """Load a theme from a JSON file in the themes directory.

    Args:
        theme_name: The name of the theme (without .json extension).

    Returns:
        A dictionary containing theme colors and settings.

    Raises:
        ThemeValidationError: If theme is missing required keys.
        ValueError: If theme file is not a valid JSON object.
        FileNotFoundError: If theme file does not exist.
    """
    themes_dir = get_themes_dir()
    theme_file = themes_dir / f"{theme_name}.json"

    if not theme_file.exists():
        print(f"⚠ Theme file '{theme_file}' not found. Using default feature_based theme.")
        return _get_default_theme()

    with theme_file.open("r", encoding="utf-8") as f:
        theme = json.load(f)
        if not isinstance(theme, dict):
            raise ValueError(f"Theme file '{theme_file}' is not a JSON object.")
        theme_dict = cast(dict[str, str], theme)

        # Validate required keys (CR-0006 fix)
        missing_keys = REQUIRED_THEME_KEYS - theme_dict.keys()
        if missing_keys:
            raise ThemeValidationError(
                f"Theme '{theme_name}' is missing required keys: {', '.join(sorted(missing_keys))}"
            )

        print(f"✓ Loaded theme: {theme_dict.get('name', theme_name)}")
        if description := theme_dict.get("description"):
            print(f"  {description}")
        return theme_dict


def _get_default_theme() -> dict[str, str]:
    """Return the default feature_based theme."""
    return {
        "name": "Feature-Based Shading",
        "bg": "#FFFFFF",
        "text": "#000000",
        "gradient_color": "#FFFFFF",
        "water": "#C0C0C0",
        "parks": "#F0F0F0",
        "road_motorway": "#0A0A0A",
        "road_primary": "#1A1A1A",
        "road_secondary": "#2A2A2A",
        "road_tertiary": "#3A3A3A",
        "road_residential": "#4A4A4A",
        "road_default": "#3A3A3A",
    }


def _sanitize_filename(name: str) -> str:
    """Sanitize string for use in filenames across platforms.

    Replaces invalid characters and handles Windows reserved names.

    Args:
        name: The string to sanitize.

    Returns:
        A safe filename string.
    """
    # Replace invalid characters with underscore
    # Windows: < > : " / \ | ? *
    # Also replace spaces and commas for consistency
    sanitized = re.sub(r'[<>:"/\\|?*\s,\']', "_", name)

    # Remove leading/trailing dots and spaces (Windows issue)
    sanitized = sanitized.strip(". ")

    # Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Handle Windows reserved names
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update(f"COM{i}" for i in range(1, 10))
    reserved.update(f"LPT{i}" for i in range(1, 10))

    if sanitized.upper() in reserved:
        sanitized = f"_{sanitized}"

    # Ensure non-empty
    return sanitized or "unnamed"


def generate_output_filename(
    city: str,
    theme_name: str,
    output_format: str = "png",
) -> Path:
    """Generate a unique output filename with city, theme, and datetime.

    Args:
        city: The city name.
        theme_name: The theme name.
        output_format: The file format (png, svg, pdf).

    Returns:
        The full path to the output file.
    """
    posters_dir = get_posters_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use sanitize function for Windows compatibility (CR-0022 fix)
    city_slug = _sanitize_filename(city.lower())
    theme_slug = _sanitize_filename(theme_name.lower())
    ext = output_format.lower()
    filename = f"{city_slug}_{theme_slug}_{timestamp}.{ext}"
    return posters_dir / filename


@dataclass
class PosterConfig:
    """Configuration for poster generation."""

    city: str
    country: str
    theme_name: str = "feature_based"
    distance: int = 29000
    width: float = 12.0
    height: float = 16.0
    output_format: str = "png"
    country_label: str | None = None
    name_label: str | None = None
    theme: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Load theme data after initialization."""
        if not self.theme:
            self.theme = load_theme(self.theme_name)

    def get_output_path(self) -> Path:
        """Generate the output file path."""
        return generate_output_filename(self.city, self.theme_name, self.output_format)
