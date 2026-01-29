"""Raster post-processing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from PIL import Image, ImageEnhance


class RasterStyle(Protocol):
    """Protocol for raster post-processing style values."""

    @property
    def grain_strength(self) -> float:
        """Film grain effect strength (0-1)."""
        ...

    @property
    def vignette_strength(self) -> float:
        """Vignette darkening effect strength (0-1)."""
        ...

    @property
    def texture_strength(self) -> float:
        """Paper texture overlay strength (0-1)."""
        ...

    @property
    def color_grading_strength(self) -> float:
        """Color grading/toning effect strength (0-1)."""
        ...

    @property
    def paper_texture_path(self) -> str | None:
        """Path to custom paper texture image, or None."""
        ...

    @property
    def seed(self) -> int | None:
        """Random seed for reproducible grain effects, or None."""
        ...


@dataclass(frozen=True)
class PostProcessResult:
    """Result container for post-processing operations."""

    image: Image.Image


def needs_raster_postprocessing(fmt: str, style: RasterStyle) -> bool:
    """Determine whether raster post-processing should run for this format."""
    if fmt != "png":
        return False
    return any(
        value > 0
        for value in (
            style.grain_strength,
            style.vignette_strength,
            style.texture_strength,
            style.color_grading_strength,
        )
    )


def apply_raster_effects(image: Image.Image, style: RasterStyle) -> Image.Image:
    """Apply raster effects to a PIL image based on style settings."""
    result = image.convert("RGBA")
    if style.grain_strength > 0:
        result = _apply_grain(result, style.grain_strength, style.seed)
    if style.vignette_strength > 0:
        result = _apply_vignette(result, style.vignette_strength)
    if style.texture_strength > 0 and style.paper_texture_path:
        result = _apply_texture(
            result,
            style.paper_texture_path,
            style.texture_strength,
        )
    if style.color_grading_strength > 0:
        result = _apply_color_grading(result, style.color_grading_strength)
    return result


def _apply_grain(image: Image.Image, strength: float, seed: int | None) -> Image.Image:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 255 * strength, (image.height, image.width, 1))
    noise = np.clip(noise + 128, 0, 255).astype(np.uint8)
    noise_rgb = np.repeat(noise, 3, axis=2)
    alpha = int(255 * min(strength, 1.0) * 0.35)
    alpha_channel = np.full((image.height, image.width, 1), alpha, dtype=np.uint8)
    noise_rgba = np.concatenate([noise_rgb, alpha_channel], axis=2)
    noise_image = Image.fromarray(noise_rgba, mode="RGBA")
    return Image.alpha_composite(image, noise_image)


def _apply_vignette(image: Image.Image, strength: float) -> Image.Image:
    width, height = image.size
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    xv, yv = np.meshgrid(x, y)
    mask = np.clip(1 - (xv**2 + yv**2), 0, 1)
    # Apply gentler vignette (1/10 of original intensity)
    effective_strength = strength * 0.1
    mask = (mask**1.5) * (1 - effective_strength) + effective_strength * mask
    alpha = (mask * 255).astype(np.uint8)
    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    vignette.putalpha(Image.fromarray(255 - alpha))
    return Image.alpha_composite(image, vignette)


def _apply_texture(image: Image.Image, texture_path: str, strength: float) -> Image.Image:
    texture = Image.open(texture_path).convert("RGBA").resize(image.size)
    red, green, blue, alpha = texture.split()
    alpha = alpha.point(lambda value: int(value * strength))
    texture = Image.merge("RGBA", (red, green, blue, alpha))
    return Image.alpha_composite(image, texture)


def _apply_color_grading(image: Image.Image, strength: float) -> Image.Image:
    factor = 1 + min(strength, 1.0) * 0.1
    result = ImageEnhance.Color(image).enhance(factor)
    result = ImageEnhance.Contrast(result).enhance(factor)
    return result
