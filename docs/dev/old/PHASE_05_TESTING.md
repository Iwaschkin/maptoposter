# Phase 05: Testing Improvements

## Header

| Field | Value |
|-------|-------|
| **Phase ID** | 05 |
| **Phase Name** | Testing Improvements |
| **Status** | ✅ Complete |
| **Start Date** | 2025-01-25 |
| **Completion Date** | 2025-01-25 |
| **Dependencies** | Phase 04 (code quality must be stable) |
| **Owner/Assignee** | AI Assistant |

---

## Tracking Data

| Metric | Value |
|--------|-------|
| **Total Issues** | 3 |
| **Resolved Issues** | 3 |
| **Remaining Issues** | 0 |
| **Progress** | 100% |
| **Blockers** | None |

---

## Issue Registry

| Issue ID | Description | Priority | Status | Completion Date | Notes |
|----------|-------------|----------|--------|-----------------|-------|
| CR-0014 | Missing font exception test | Low | ✅ Complete | 2025-01-25 | Added test_fonts.py with 14 tests |
| CR-0017 | Test coverage for gradient | Low | ✅ Complete | 2025-01-25 | Added test_render.py with 17 tests |
| CR-0018 | Parametric tests for themes | Low | ✅ Complete | 2025-01-25 | Added parametric tests in test_config.py |

---

## Execution Plan

### Task 1: Add Font Exception Tests (CR-0014)

**Objective:** Test that missing fonts fall back gracefully to system fonts.

**Tests to Add:**
```python
# tests/test_fonts.py
def test_missing_font_fallback():
    """Test that missing fonts fall back to system fonts."""
    fonts = FontConfig()
    fonts.regular = None  # Simulate missing font
    props = fonts.get_properties("regular", 12.0)
    assert props.get_family() == ["sans-serif"]

def test_missing_weight_fallback():
    """Test that missing weight falls back to regular."""
    fonts = FontConfig()
    props = fonts.get_properties("nonexistent", 12.0)
    # Should not raise, should fall back
    assert props is not None
```

**Files Affected:**
- `tests/test_fonts.py` (new file)
- `src/maptoposter/fonts.py` (may need minor fixes)

---

### Task 2: Add Render Module Tests (CR-0017)

**Objective:** Add test coverage for gradient generation and rendering utilities.

**Tests to Add:**
```python
# tests/test_render.py
def test_get_edge_colors_by_type():
    """Test road color assignment by highway type."""
    theme = load_theme("noir")
    colors = get_edge_colors_by_type(mock_graph, theme)
    # Verify motorway gets motorway color
    # Verify unknown types get default color

def test_get_edge_widths_by_type():
    """Test road width assignment by highway type."""
    widths = get_edge_widths_by_type(mock_graph)
    # Verify motorway is widest
    # Verify residential is thinnest

def test_gradient_generation():
    """Test gradient overlay is created correctly."""
    # Test _add_gradient_fade creates expected gradient
```

**Files Affected:**
- `tests/test_render.py` (new file)

---

### Task 3: Add Parametric Theme Tests (CR-0018)

**Objective:** Test that all theme files load correctly and have required keys.

**Tests to Add:**
```python
# tests/test_config.py
import pytest
from maptoposter.config import get_available_themes, load_theme, REQUIRED_THEME_KEYS

@pytest.mark.parametrize("theme_name", get_available_themes())
def test_theme_loads_successfully(theme_name: str):
    """Test that each theme file loads without error."""
    theme = load_theme(theme_name)
    assert isinstance(theme, dict)

@pytest.mark.parametrize("theme_name", get_available_themes())
def test_theme_has_required_keys(theme_name: str):
    """Test that each theme has all required keys."""
    theme = load_theme(theme_name)
    missing = REQUIRED_THEME_KEYS - theme.keys()
    assert not missing, f"Theme {theme_name} missing: {missing}"
```

**Files Affected:**
- `tests/test_config.py` (add parametric tests)

---

## Validation Criteria

Phase 05 is complete when:

1. ✅ **CR-0014:** Font fallback tests exist and pass
2. ✅ **CR-0017:** Render module has basic test coverage
3. ✅ **CR-0018:** All themes are tested parametrically
4. ✅ All tests pass with `uv run pytest`
5. ✅ Test coverage improved (target: >60% overall)

---

*Phase Document Created: 2025-01-25*
