# Phase 03: Bug Fixes & Config Hardening

## Header

| Field | Value |
|-------|-------|
| **Phase ID** | 03 |
| **Phase Name** | Bug Fixes & Config Hardening |
| **Status** | ✅ Complete |
| **Start Date** | 2025-01-25 |
| **Completion Date** | 2025-01-25 |
| **Dependencies** | Phase 02 (error handling must be stable) |
| **Owner/Assignee** | AI Assistant |

---

## Tracking Data

| Metric | Value |
|--------|-------|
| **Total Issues** | 6 |
| **Resolved Issues** | 6 |
| **Remaining Issues** | 0 |
| **Progress** | 100% |
| **Blockers** | None |

---

## Issue Registry

| Issue ID | Description | Priority | Status | Completion Date | Notes |
|----------|-------------|----------|--------|-----------------|-------|
| CR-0003 | `name_label` parameter accepted but never used | Medium | ✅ Complete | 2025-01-25 | Typography uses name_label or city fallback |
| CR-0006 | Missing theme key validation | Medium | ✅ Complete | 2025-01-25 | ThemeValidationError with REQUIRED_THEME_KEYS |
| CR-0012 | `get_available_themes` silently creates directory | Low | ✅ Complete | 2025-01-25 | Returns empty list, no side effects |
| CR-0021 | `cli([])` ignores provided args and reads sys.argv | Medium | ✅ Complete | 2025-01-25 | Fixed condition to handle empty args list |
| CR-0022 | Output filename sanitization incomplete for Windows | Medium | ✅ Complete | 2025-01-25 | Added _sanitize_filename() for Windows compat |
| CR-0023 | `create_poster()` does not ensure output directory exists | Low | ✅ Complete | 2025-01-25 | Creates parent dirs with mkdir(parents=True) |

---

## Execution Plan

### Task 1: Wire `name_label` Parameter to Typography (CR-0003)

**Objective:** Enable users to override the displayed city name on posters.

**Current State:**
- `PosterConfig.name_label` exists but is never read
- `_add_typography()` always uses `self.config.city`

**Target State:**
- Typography uses `name_label` if provided, falls back to `city`

**Changes in render.py (~line 235):**
```python
def _add_typography(self, ax: Axes) -> None:
    """Add city name, country, and coordinates text."""
    # Use name_label override if provided, otherwise use city
    display_name = self.config.name_label or self.config.city
    spaced_city = "  ".join(list(display_name.upper()))

    # Rest of method unchanged...
```

**Files Affected:**
- `src/maptoposter/render.py`

**Validation:**
- [ ] `create_poster(..., name_label="NYC")` displays "N  Y  C" on poster
- [ ] Without `name_label`, displays city name as before
- [ ] Existing tests pass

---

### Task 2: Add Theme Schema Validation (CR-0006)

**Objective:** Validate theme files have all required keys before rendering.

**Define Required Keys:**
```python
REQUIRED_THEME_KEYS = frozenset({
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
})
```

**Changes in config.py:**
```python
class ThemeValidationError(ValueError):
    """Raised when theme file is missing required keys."""
    pass

REQUIRED_THEME_KEYS = frozenset({
    "name", "bg", "text", "gradient_color", "water", "parks",
    "road_motorway", "road_primary", "road_secondary",
    "road_tertiary", "road_residential", "road_default",
})

def load_theme(theme_name: str = "feature_based") -> dict[str, str]:
    """Load theme configuration from JSON file.

    Raises:
        ThemeValidationError: If theme is missing required keys.
        ValueError: If theme file is not a valid JSON object.
        FileNotFoundError: If theme file does not exist.
    """
    theme_file = get_themes_dir() / f"{theme_name}.json"
    if not theme_file.exists():
        raise FileNotFoundError(f"Theme '{theme_name}' not found at {theme_file}")

    with theme_file.open("r", encoding="utf-8") as f:
        theme = json.load(f)

    if not isinstance(theme, dict):
        raise ValueError(f"Theme '{theme_name}' must be a JSON object")

    # Validate required keys
    missing_keys = REQUIRED_THEME_KEYS - theme.keys()
    if missing_keys:
        raise ThemeValidationError(
            f"Theme '{theme_name}' is missing required keys: {', '.join(sorted(missing_keys))}"
        )

    return theme
```

**Files Affected:**
- `src/maptoposter/config.py`
- `tests/test_config.py` (add validation tests)

**Validation:**
- [ ] Theme with missing key raises `ThemeValidationError`
- [ ] Error message lists all missing keys
- [ ] All 17 existing themes pass validation
- [ ] Unit test for missing key scenario

---

### Task 3: Remove Side Effect from `get_available_themes()` (CR-0012)

**Objective:** Getter function should not create directories.

**Current State (config.py ~line 67-68):**
```python
def get_available_themes() -> list[str]:
    themes_dir = get_themes_dir()
    if not themes_dir.exists():
        themes_dir.mkdir(parents=True, exist_ok=True)  # SIDE EFFECT!
        return []
    # ...
```

**Target State:**
```python
def get_available_themes() -> list[str]:
    """Get list of available theme names.

    Returns:
        List of theme names (without .json extension).
        Empty list if themes directory doesn't exist.
    """
    themes_dir = get_themes_dir()
    if not themes_dir.exists():
        return []  # No side effect - just return empty

    return sorted([
        f.stem for f in themes_dir.glob("*.json")
        if f.is_file()
    ])
```

**Note:** The themes directory is packaged with the module, so it should always exist. If it's missing, that indicates a broken installation.

**Files Affected:**
- `src/maptoposter/config.py`

**Validation:**
- [ ] Missing themes directory returns empty list without creating it
- [ ] Existing tests pass
- [ ] `--list-themes` works correctly

---

### Task 4: Fix CLI Empty Args Behavior (CR-0021)

**Objective:** Make `cli([])` behave consistently with `cli(None)`.

**Current State (cli.py ~line 213-218):**
```python
def cli(args: list[str] | None = None) -> int:
    # If no arguments provided, show examples
    if len(sys.argv) == 1 and args is None:
        _print_examples()
        return 0
    # ...
```

**Issue:** `cli([])` passes an empty list, so `args is None` is `False`, and examples aren't shown.

**Target State:**
```python
def cli(args: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        args: Command line arguments. If None, uses sys.argv[1:].
              If empty list, shows examples.
    """
    # Determine effective arguments
    if args is None:
        effective_args = sys.argv[1:]
    else:
        effective_args = args

    # If no arguments, show examples
    if not effective_args:
        _print_examples()
        return 0

    # Parse arguments
    parser = _create_parser()
    parsed = parser.parse_args(effective_args)
    # ...
```

**Files Affected:**
- `src/maptoposter/cli.py`
- `tests/test_cli.py` (add test for `cli([])`)

**Validation:**
- [ ] `cli(None)` with no sys.argv shows examples
- [ ] `cli([])` shows examples
- [ ] `cli(["-c", "Paris", "-C", "France"])` works correctly
- [ ] Unit test for empty args behavior

---

### Task 5: Add Comprehensive Filename Sanitization (CR-0022)

**Objective:** Sanitize output filenames for Windows compatibility.

**Windows Reserved Characters:** `< > : " / \ | ? *`
**Windows Reserved Names:** `CON, PRN, AUX, NUL, COM1-9, LPT1-9`

**Add Sanitization Function in config.py:**
```python
import re

def _sanitize_filename(name: str) -> str:
    """Sanitize string for use in filenames across platforms.

    Replaces invalid characters and handles Windows reserved names.
    """
    # Replace invalid characters with underscore
    # Windows: < > : " / \ | ? *
    # Also replace spaces and commas for consistency
    sanitized = re.sub(r'[<>:"/\\|?*\s,]', '_', name)

    # Remove leading/trailing dots and spaces (Windows issue)
    sanitized = sanitized.strip('. ')

    # Handle Windows reserved names
    reserved = {'CON', 'PRN', 'AUX', 'NUL'}
    reserved.update(f'COM{i}' for i in range(1, 10))
    reserved.update(f'LPT{i}' for i in range(1, 10))

    if sanitized.upper() in reserved:
        sanitized = f"_{sanitized}"

    # Ensure non-empty
    return sanitized or "unnamed"

def get_output_filename(city: str, theme_name: str, ext: str = "png") -> str:
    """Generate sanitized output filename."""
    from datetime import datetime

    city_slug = _sanitize_filename(city.lower())
    theme_slug = _sanitize_filename(theme_name.lower())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{city_slug}_{theme_slug}_{timestamp}.{ext}"
```

**Files Affected:**
- `src/maptoposter/config.py`
- `tests/test_config.py` (add sanitization tests)

**Validation:**
- [ ] `St. John's/Port` → `st__john_s_port`
- [ ] `Mexico:City` → `mexico_city`
- [ ] `CON` → `_con`
- [ ] Unit tests for edge cases

---

### Task 6: Ensure Output Directory Exists (CR-0023)

**Objective:** `create_poster()` should create parent directories if needed.

**Changes in render.py (~line 405-440):**
```python
def create_poster(
    config: PosterConfig,
    output_file: Path,
    # ...
) -> Path | None:
    """Create a map poster for the configured city.

    Creates parent directories for output_file if they don't exist.
    """
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # ... rest of function ...
```

**Files Affected:**
- `src/maptoposter/render.py`

**Validation:**
- [ ] `create_poster(..., output_file=Path("deep/nested/dir/poster.png"))` succeeds
- [ ] Existing behavior unchanged for `posters/` directory
- [ ] Unit test with temporary nested directory

---

## Validation Criteria

Phase 03 is complete when:

1. ✅ **CR-0003:** `name_label` overrides displayed city name
2. ✅ **CR-0006:** Invalid themes raise `ThemeValidationError` with missing keys
3. ✅ **CR-0012:** `get_available_themes()` has no side effects
4. ✅ **CR-0021:** `cli([])` shows examples
5. ✅ **CR-0022:** Filenames are Windows-safe
6. ✅ **CR-0023:** Output directories are created automatically
7. ✅ All existing tests pass
8. ✅ Manual test: Generate poster for city with special characters

---

## Rollback Plan

If Phase 03 fails:

1. Each task is independent; revert individual files as needed
2. Theme validation is additive; removal won't break existing behavior
3. Filename sanitization is backwards-compatible

**Safe Rollback Command:**
```bash
git checkout HEAD~1 -- src/maptoposter/config.py src/maptoposter/cli.py src/maptoposter/render.py
```

---

*Phase Document Created: 2026-01-24*
