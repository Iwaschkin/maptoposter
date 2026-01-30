"""Tests for style presets and style packs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from maptoposter.styles import (
    StyleConfig,
    get_available_presets,
    get_preset_description,
    get_style_preset,
    load_style_pack,
)


if TYPE_CHECKING:
    from pathlib import Path


def test_get_available_presets_contains_noir() -> None:
    """Test that noir preset is available."""
    presets = get_available_presets()
    assert "noir" in presets


def test_get_available_presets_contains_all_expected() -> None:
    """Test that all expected presets are available."""
    presets = get_available_presets()
    expected = {
        "noir",
        "blueprint",
        "neon_cyberpunk",
        "japanese_ink",
        "warm_beige",
        "vintage",
        "film_noir",
    }
    assert expected.issubset(set(presets))


def test_get_style_preset_returns_style_config() -> None:
    """Test that get_style_preset returns a StyleConfig."""
    style = get_style_preset("noir")
    assert isinstance(style, StyleConfig)
    assert style.theme_name == "noir"


def test_get_preset_description_returns_string() -> None:
    """Test that get_preset_description returns a description."""
    desc = get_preset_description("noir")
    assert isinstance(desc, str)
    assert len(desc) > 0


def test_get_preset_description_raises_for_unknown() -> None:
    """Test that get_preset_description raises for unknown preset."""
    with pytest.raises(KeyError, match="Unknown preset"):
        get_preset_description("nonexistent_preset")


def test_presets_have_meaningful_values() -> None:
    """Test that presets have non-default post-processing values."""
    # vintage and film_noir should have grain
    vintage = get_style_preset("vintage")
    assert vintage.grain_strength > 0
    assert vintage.vignette_strength > 0

    film_noir = get_style_preset("film_noir")
    assert film_noir.grain_strength > 0
    assert film_noir.vignette_strength > 0

    # neon_cyberpunk should have glow
    neon = get_style_preset("neon_cyberpunk")
    assert neon.road_glow_strength > 0


def test_load_style_pack_valid(tmp_path: Path) -> None:
    """Test loading a valid style pack from JSON."""
    style_pack = {
        "theme_name": "noir",
        "road_glow_strength": 0.3,
    }
    path = tmp_path / "pack.json"
    path.write_text(json.dumps(style_pack), encoding="utf-8")

    style = load_style_pack(str(path))
    assert style.theme_name == "noir"
    assert style.road_glow_strength == 0.3


def test_load_style_pack_rejects_unknown_keys(tmp_path: Path) -> None:
    """Test that unknown keys in style pack raise ValueError."""
    style_pack = {
        "theme_name": "noir",
        "unknown_key": 123,
    }
    path = tmp_path / "bad_pack.json"
    path.write_text(json.dumps(style_pack), encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown style pack keys"):
        load_style_pack(str(path))
    path.write_text(json.dumps(style_pack), encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown style pack keys"):
        load_style_pack(str(path))
