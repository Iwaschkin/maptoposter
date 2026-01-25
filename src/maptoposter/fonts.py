"""Font management utilities."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from matplotlib.font_manager import FontProperties

from .config import get_fonts_dir


__all__ = ["FontSet", "load_fonts"]

logger = logging.getLogger(__name__)


@dataclass
class FontSet:
    """Container for font paths and properties."""

    bold: Path | None = None
    regular: Path | None = None
    light: Path | None = None

    @property
    def is_loaded(self) -> bool:
        """Check if all fonts are loaded."""
        return all([self.bold, self.regular, self.light])

    def get_properties(
        self,
        weight: str = "regular",
        size: float = 12.0,
    ) -> FontProperties:
        """Get FontProperties for a specific weight and size.

        Args:
            weight: Font weight ('bold', 'regular', or 'light').
            size: Font size in points.

        Returns:
            FontProperties configured for the requested style.
        """
        # Try to get the requested weight, fall back to regular, then None
        font_path = getattr(self, weight, None) or self.regular

        if font_path is not None and font_path.exists():
            return FontProperties(fname=str(font_path), size=size)

        # Fallback to system fonts
        weight_map = {
            "bold": "bold",
            "regular": "normal",
            "light": "light",
        }
        return FontProperties(
            family="sans-serif",
            weight=weight_map.get(weight, "normal"),
            size=size,
        )


def load_fonts() -> FontSet:
    """Load Roboto fonts from the fonts directory.

    Returns:
        A FontSet with paths to the font files.
    """
    fonts_dir = get_fonts_dir()

    font_set = FontSet(
        bold=fonts_dir / "Roboto-Bold.ttf",
        regular=fonts_dir / "Roboto-Regular.ttf",
        light=fonts_dir / "Roboto-Light.ttf",
    )

    # Verify fonts exist
    for weight in ["bold", "regular", "light"]:
        path = getattr(font_set, weight)
        if path and not path.exists():
            logger.warning("Font not found: %s", path)
            setattr(font_set, weight, None)

    return font_set
