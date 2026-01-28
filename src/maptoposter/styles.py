"""Style presets and style pack loading."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from dataclasses import fields as dataclass_fields

from .render_constants import (
    ATTRIBUTION_X_POS,
    ATTRIBUTION_Y_POS,
    CITY_NAME_Y_POS,
    COORDS_Y_POS,
    COUNTRY_LABEL_Y_POS,
    DIVIDER_Y_POS,
    GRADIENT_HEIGHT_FRACTION,
    ROAD_WIDTH_DEFAULT,
    ROAD_WIDTH_MOTORWAY,
    ROAD_WIDTH_PRIMARY,
    ROAD_WIDTH_SECONDARY,
    ROAD_WIDTH_TERTIARY,
    TEXT_CENTER_X,
)


__all__ = [
    "StyleConfig",
    "get_available_presets",
    "get_preset_description",
    "get_style_preset",
    "load_style_pack",
]


@dataclass(frozen=True)
class StyleConfig:
    """Styling configuration for rendering."""

    theme_name: str | None = None
    road_core_widths: dict[str, float] = field(
        default_factory=lambda: {
            "motorway": ROAD_WIDTH_MOTORWAY,
            "primary": ROAD_WIDTH_PRIMARY,
            "secondary": ROAD_WIDTH_SECONDARY,
            "tertiary": ROAD_WIDTH_TERTIARY,
            "default": ROAD_WIDTH_DEFAULT,
        }
    )
    road_casing_widths: dict[str, float] = field(
        default_factory=lambda: {
            "motorway": 1.8,
            "primary": 1.5,
            "secondary": 1.2,
            "tertiary": 0.9,
            "default": 0.6,
        }
    )
    road_glow_strength: float = 0.0
    gradient_strength: float = GRADIENT_HEIGHT_FRACTION
    typography_tracking: int = 2
    text_center_x: float = TEXT_CENTER_X
    city_name_y_pos: float = CITY_NAME_Y_POS
    country_label_y_pos: float = COUNTRY_LABEL_Y_POS
    coords_y_pos: float = COORDS_Y_POS
    divider_y_pos: float = DIVIDER_Y_POS
    attribution_x_pos: float = ATTRIBUTION_X_POS
    attribution_y_pos: float = ATTRIBUTION_Y_POS
    texture_strength: float = 0.0
    grain_strength: float = 0.0
    vignette_strength: float = 0.0
    color_grading_strength: float = 0.0
    paper_texture_path: str | None = None
    seed: int | None = None
    enable_layer_cache: bool = False


PRESET_STYLES: dict[str, tuple[StyleConfig, str]] = {
    "noir": (
        StyleConfig(
            theme_name="noir",
            road_glow_strength=0.2,
            typography_tracking=3,
            grain_strength=0.08,
            vignette_strength=0.15,
        ),
        "Classic film noir aesthetic with subtle grain and vignette",
    ),
    "blueprint": (
        StyleConfig(
            theme_name="blueprint",
            road_glow_strength=0.0,
            typography_tracking=1,
            road_casing_widths={
                "motorway": 0.0,
                "primary": 0.0,
                "secondary": 0.0,
                "tertiary": 0.0,
                "default": 0.0,
            },
        ),
        "Technical drawing style with no casing or effects",
    ),
    "neon_cyberpunk": (
        StyleConfig(
            theme_name="neon_cyberpunk",
            road_glow_strength=0.6,
            typography_tracking=2,
            color_grading_strength=0.2,
        ),
        "Vibrant neon glow with enhanced color saturation",
    ),
    "japanese_ink": (
        StyleConfig(
            theme_name="japanese_ink",
            road_glow_strength=0.0,
            typography_tracking=4,
            vignette_strength=0.25,
            gradient_strength=0.3,
        ),
        "Calligraphic style with wide tracking and soft vignette",
    ),
    "warm_beige": (
        StyleConfig(
            theme_name="warm_beige",
            road_glow_strength=0.1,
            typography_tracking=2,
            grain_strength=0.12,
            vignette_strength=0.1,
            color_grading_strength=0.15,
        ),
        "Vintage warmth with film grain and subtle color grading",
    ),
    "vintage": (
        StyleConfig(
            theme_name="warm_beige",
            grain_strength=0.15,
            vignette_strength=0.2,
            color_grading_strength=0.1,
        ),
        "Classic vintage film look with grain and vignette",
    ),
    "film_noir": (
        StyleConfig(
            theme_name="noir",
            grain_strength=0.2,
            vignette_strength=0.3,
            color_grading_strength=0.05,
        ),
        "Heavy film noir with pronounced grain and dark vignette",
    ),
}


def get_available_presets() -> list[str]:
    """Return available style preset names."""
    return sorted(PRESET_STYLES.keys())


def get_preset_description(preset_name: str) -> str:
    """Return the description for a preset name."""
    if preset_name not in PRESET_STYLES:
        raise KeyError(f"Unknown preset '{preset_name}'.")
    return PRESET_STYLES[preset_name][1]


def get_style_preset(preset_name: str) -> StyleConfig:
    """Return the style configuration for a preset name."""
    if preset_name not in PRESET_STYLES:
        raise KeyError(f"Unknown preset '{preset_name}'.")
    return PRESET_STYLES[preset_name][0]


def load_style_pack(path: str) -> StyleConfig:
    """Load a StyleConfig from a JSON style pack file."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Style pack must be a JSON object.")
    allowed_keys = {field.name for field in dataclass_fields(StyleConfig)}
    unknown_keys = set(data) - allowed_keys
    if unknown_keys:
        raise ValueError(f"Unknown style pack keys: {sorted(unknown_keys)}")
    return StyleConfig(**data)
