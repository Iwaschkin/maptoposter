"""Unit tests for post-processing effects."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest
from PIL import Image

from maptoposter.postprocess import (
    PostProcessResult,
    apply_raster_effects,
    needs_raster_postprocessing,
)


@dataclass
class MockStyle:
    """Mock style object for testing RasterStyle protocol."""

    grain_strength: float = 0.0
    vignette_strength: float = 0.0
    texture_strength: float = 0.0
    color_grading_strength: float = 0.0
    paper_texture_path: str | None = None
    seed: int | None = None


def create_test_image(width: int = 100, height: int = 100) -> Image.Image:
    """Create a solid color test image."""
    return Image.new("RGBA", (width, height), (128, 128, 128, 255))


class TestNeedsRasterPostprocessing:
    """Tests for needs_raster_postprocessing function."""

    def test_returns_false_for_non_png_format(self) -> None:
        """Non-PNG formats should never need postprocessing."""
        style = MockStyle(grain_strength=1.0)
        assert needs_raster_postprocessing("svg", style) is False
        assert needs_raster_postprocessing("pdf", style) is False
        assert needs_raster_postprocessing("jpg", style) is False

    def test_returns_false_when_all_strengths_zero(self) -> None:
        """PNG with no effects should not need postprocessing."""
        style = MockStyle()
        assert needs_raster_postprocessing("png", style) is False

    def test_returns_true_when_grain_strength_positive(self) -> None:
        """PNG with grain should need postprocessing."""
        style = MockStyle(grain_strength=0.1)
        assert needs_raster_postprocessing("png", style) is True

    def test_returns_true_when_vignette_strength_positive(self) -> None:
        """PNG with vignette should need postprocessing."""
        style = MockStyle(vignette_strength=0.1)
        assert needs_raster_postprocessing("png", style) is True

    def test_returns_true_when_texture_strength_positive(self) -> None:
        """PNG with texture should need postprocessing."""
        style = MockStyle(texture_strength=0.1)
        assert needs_raster_postprocessing("png", style) is True

    def test_returns_true_when_color_grading_strength_positive(self) -> None:
        """PNG with color grading should need postprocessing."""
        style = MockStyle(color_grading_strength=0.1)
        assert needs_raster_postprocessing("png", style) is True


class TestApplyRasterEffects:
    """Tests for apply_raster_effects function."""

    def test_returns_post_process_result(self) -> None:
        """Result should be a PostProcessResult instance."""
        image = create_test_image()
        style = MockStyle()
        result = apply_raster_effects(image, style)
        assert isinstance(result, PostProcessResult)

    def test_returns_rgba_image(self) -> None:
        """Result image should always be RGBA mode."""
        image = Image.new("RGB", (50, 50), (100, 100, 100))
        style = MockStyle()
        result = apply_raster_effects(image, style)
        assert result.image.mode == "RGBA"

    def test_preserves_image_size(self) -> None:
        """Effect should not change image dimensions."""
        image = create_test_image(120, 80)
        style = MockStyle(grain_strength=0.1, vignette_strength=0.1)
        result = apply_raster_effects(image, style)
        assert result.image.size == (120, 80)

    def test_grain_modifies_image(self) -> None:
        """Grain effect should modify pixel values."""
        image = create_test_image()
        style = MockStyle(grain_strength=0.5, seed=42)
        result = apply_raster_effects(image, style)

        original_arr = np.array(image)
        result_arr = np.array(result.image)
        # Images should differ due to grain noise
        assert not np.array_equal(original_arr, result_arr)

    def test_grain_is_reproducible_with_seed(self) -> None:
        """Same seed should produce identical grain results."""
        image = create_test_image()
        style = MockStyle(grain_strength=0.3, seed=12345)

        result1 = apply_raster_effects(image.copy(), style)
        result2 = apply_raster_effects(image.copy(), style)

        assert np.array_equal(np.array(result1.image), np.array(result2.image))

    def test_vignette_darkens_edges(self) -> None:
        """Vignette should make edges darker than center."""
        image = create_test_image(100, 100)
        style = MockStyle(vignette_strength=0.5)
        result = apply_raster_effects(image, style)

        result_arr = np.array(result.image)
        # Check that corners are darker than center
        center_brightness = np.mean(result_arr[45:55, 45:55, :3])
        corner_brightness = np.mean(result_arr[0:10, 0:10, :3])
        assert corner_brightness < center_brightness

    def test_color_grading_enhances_image(self) -> None:
        """Color grading should change color/contrast."""
        # Use an image with some color variation
        image = Image.new("RGBA", (50, 50), (100, 150, 200, 255))
        style = MockStyle(color_grading_strength=0.5)
        result = apply_raster_effects(image, style)

        original_arr = np.array(image)
        result_arr = np.array(result.image)
        assert not np.array_equal(original_arr, result_arr)

    def test_no_effects_returns_unchanged_pixels(self) -> None:
        """With all effects at zero, pixels should be unchanged."""
        image = create_test_image()
        style = MockStyle()  # All zeros
        result = apply_raster_effects(image, style)

        original_arr = np.array(image)
        result_arr = np.array(result.image)
        assert np.array_equal(original_arr, result_arr)

    def test_multiple_effects_can_combine(self) -> None:
        """Multiple effects should all apply when enabled."""
        image = create_test_image()
        style = MockStyle(
            grain_strength=0.2,
            vignette_strength=0.3,
            color_grading_strength=0.1,
            seed=99,
        )
        result = apply_raster_effects(image, style)

        original_arr = np.array(image)
        result_arr = np.array(result.image)
        assert not np.array_equal(original_arr, result_arr)

    def test_effects_applied_tracks_grain(self) -> None:
        """effects_applied should include 'grain' when grain is applied."""
        image = create_test_image()
        style = MockStyle(grain_strength=0.5, seed=42)
        result = apply_raster_effects(image, style)
        assert "grain" in result.effects_applied

    def test_effects_applied_tracks_vignette(self) -> None:
        """effects_applied should include 'vignette' when vignette is applied."""
        image = create_test_image()
        style = MockStyle(vignette_strength=0.5)
        result = apply_raster_effects(image, style)
        assert "vignette" in result.effects_applied

    def test_effects_applied_tracks_color_grading(self) -> None:
        """effects_applied should include 'color_grading' when color grading is applied."""
        image = create_test_image()
        style = MockStyle(color_grading_strength=0.5)
        result = apply_raster_effects(image, style)
        assert "color_grading" in result.effects_applied

    def test_effects_applied_empty_when_no_effects(self) -> None:
        """effects_applied should be empty when no effects are applied."""
        image = create_test_image()
        style = MockStyle()
        result = apply_raster_effects(image, style)
        assert result.effects_applied == ()

    def test_grain_seed_is_captured(self) -> None:
        """grain_seed should be captured when grain is applied."""
        image = create_test_image()
        style = MockStyle(grain_strength=0.5, seed=12345)
        result = apply_raster_effects(image, style)
        assert result.grain_seed == 12345

    def test_grain_seed_none_when_no_grain(self) -> None:
        """grain_seed should be None when grain is not applied."""
        image = create_test_image()
        style = MockStyle(vignette_strength=0.5)
        result = apply_raster_effects(image, style)
        assert result.grain_seed is None


class TestPostProcessResult:
    """Tests for PostProcessResult dataclass."""

    def test_holds_image(self) -> None:
        """PostProcessResult should store the image."""
        image = create_test_image()
        result = PostProcessResult(image=image)
        assert result.image is image

    def test_holds_effects_applied(self) -> None:
        """PostProcessResult should store effects_applied."""
        image = create_test_image()
        result = PostProcessResult(image=image, effects_applied=("grain", "vignette"))
        assert result.effects_applied == ("grain", "vignette")

    def test_holds_grain_seed(self) -> None:
        """PostProcessResult should store grain_seed."""
        image = create_test_image()
        result = PostProcessResult(image=image, grain_seed=12345)
        assert result.grain_seed == 12345

    def test_defaults(self) -> None:
        """PostProcessResult should have sensible defaults."""
        image = create_test_image()
        result = PostProcessResult(image=image)
        assert result.effects_applied == ()
        assert result.grain_seed is None

    def test_is_frozen(self) -> None:
        """PostProcessResult should be immutable."""
        image = create_test_image()
        result = PostProcessResult(image=image)
        with pytest.raises(AttributeError):
            result.image = create_test_image()  # type: ignore[misc]
