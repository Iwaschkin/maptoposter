# Code Review Report
**Date**: 2026-01-30
**Version**: 0.1.0
**Reviewer**: GitHub Copilot (Claude Opus 4.5)
**Project**: maptoposter

## Executive Summary
- Total issues found: 15
- Critical: 1
- High: 3
- Medium: 7
- Low: 4

## Review Scope
- Files analyzed: 12 (8 source files, 4 test files in detail)
- Lines of code: ~3,500
- Test coverage: 169 tests passing

---

## Issues

### [MISSING FUNCTIONALITY] name_label CLI argument not passed to PosterConfig
**File**: [cli.py](../../../src/maptoposter/cli.py#L625-L638)
**Severity**: Critical
**Category**: Missing Functionality

**Description**:
The `--name` / `-n` CLI argument is defined in the parser (line 166) to allow users to override the city name displayed on the poster, but it is never passed to the `PosterConfig` when creating posters. This means the feature is documented but completely non-functional.

**Current Code**:
```python
config = PosterConfig(
    city=parsed.city,
    country=parsed.country,
    theme_name=current_theme,
    distance=parsed.distance,
    width=parsed.width,
    height=parsed.height,
    output_format=parsed.format,
    country_label=parsed.country_label,
    theme=theme,
    style_config=preset_style,
    render_backend=parsed.render_backend,
)
```

**Recommended Fix**:
```python
config = PosterConfig(
    city=parsed.city,
    country=parsed.country,
    theme_name=current_theme,
    distance=parsed.distance,
    width=parsed.width,
    height=parsed.height,
    output_format=parsed.format,
    country_label=parsed.country_label,
    name_label=parsed.name_label,  # Add this line
    theme=theme,
    style_config=preset_style,
    render_backend=parsed.render_backend,
)
```

**Impact if Unaddressed**:
Users cannot override the city display name despite the CLI advertising this feature. This is a user-facing bug that breaks documented functionality.

**Effort**: Low

---

### [TESTING COVERAGE] Missing test_geo.py for geo module
**File**: [tests/](../../../tests/)
**Severity**: High
**Category**: Testing Coverage

**Description**:
The `geo.py` module handles critical functionality including geocoding, OSM data fetching, and coordinate projection, but there is no dedicated test file for it. This module contains:
- `get_coordinates()` - geocoding with rate limiting
- `fetch_graph()` - street network fetching
- `fetch_features()` - water, parks, railway fetching
- `get_crop_limits()` - viewport calculation

These functions interact with external APIs and have complex error handling that should be tested.

**Current Code**:
```
tests/
    test_cache.py
    test_cli.py
    test_config.py
    test_fonts.py
    test_postprocess.py
    test_render.py
    test_styles.py
    # No test_geo.py
```

**Recommended Fix**:
Create `tests/test_geo.py` with tests covering:
1. Successful geocoding with mock responses
2. Network error handling (Timeout, ConnectionError)
3. Rate limiting behavior
4. Cache integration for coordinates
5. Graph fetching success/failure scenarios
6. Features fetching with various OSM tags
7. `get_crop_limits()` aspect ratio calculations

**Impact if Unaddressed**:
Critical API interaction code is untested, risking undetected regressions in geocoding or OSM data fetching.

**Effort**: Medium

---

### [BUG DETECTION] Bare except clause in _list_themes
**File**: [cli.py](../../../src/maptoposter/cli.py#L119)
**Severity**: High
**Category**: Bug Detection

**Description**:
The `_list_themes()` function uses a bare `except Exception:` clause that catches all exceptions including `KeyboardInterrupt` and `SystemExit`. This could mask real errors and make debugging difficult.

**Current Code**:
```python
try:
    with theme_path.open("r", encoding="utf-8") as f:
        theme_data = json.load(f)
        display_name = theme_data.get("name", theme_name)
        description = theme_data.get("description", "")
except Exception:
    display_name = theme_name
    description = ""
```

**Recommended Fix**:
```python
try:
    with theme_path.open("r", encoding="utf-8") as f:
        theme_data = json.load(f)
        display_name = theme_data.get("name", theme_name)
        description = theme_data.get("description", "")
except (OSError, json.JSONDecodeError, KeyError) as e:
    logger.debug("Could not load theme metadata for %s: %s", theme_name, e)
    display_name = theme_name
    description = ""
```

**Impact if Unaddressed**:
Could silently swallow unexpected errors and make debugging theme loading issues difficult.

**Effort**: Low

---

### [BUG DETECTION] Bare except in render.py cache estimation
**File**: [render.py](../../../src/maptoposter/render.py#L105)
**Severity**: Medium
**Category**: Bug Detection

**Description**:
The `_estimate_cache_entry_size()` function uses a bare `except Exception:` that assumes 10MB for any error case. This could mask real issues.

**Current Code**:
```python
def _estimate_cache_entry_size(payload: dict[str, Any]) -> int:
    total = 0
    for value in payload.values():
        if hasattr(value, "memory_usage"):
            try:
                total += int(value.memory_usage(deep=True).sum())
            except Exception:
                total += 10 * 1024 * 1024  # Assume 10MB if can't measure
```

**Recommended Fix**:
```python
def _estimate_cache_entry_size(payload: dict[str, Any]) -> int:
    total = 0
    for value in payload.values():
        if hasattr(value, "memory_usage"):
            try:
                total += int(value.memory_usage(deep=True).sum())
            except (TypeError, ValueError, AttributeError) as e:
                logger.debug("Could not measure memory usage: %s", e)
                total += 10 * 1024 * 1024  # Assume 10MB if can't measure
```

**Impact if Unaddressed**:
Could mask unexpected errors in memory estimation code.

**Effort**: Low

---

### [BUG DETECTION] Bare except in DatashaderBackend.render_roads
**File**: [render.py](../../../src/maptoposter/render.py#L286)
**Severity**: Medium
**Category**: Bug Detection

**Description**:
The datashader import uses a bare `except Exception:` which would catch all import errors but also any other unexpected exceptions.

**Current Code**:
```python
def render_roads(self, ax, layers, crop_xlim, crop_ylim, theme) -> bool:
    try:
        import datashader as ds
        import datashader.transfer_functions as tf
    except Exception:
        return False
```

**Recommended Fix**:
```python
def render_roads(self, ax, layers, crop_xlim, crop_ylim, theme) -> bool:
    try:
        import datashader as ds
        import datashader.transfer_functions as tf
    except ImportError:
        return False
```

**Impact if Unaddressed**:
Could silently fail for reasons other than missing datashader package.

**Effort**: Low

---

### [TECHNICAL DEBT] Inconsistent default distance value documentation
**File**: Multiple files
**Severity**: Medium
**Category**: Documentation Gaps

**Description**:
The default distance value is inconsistent across documentation:
- [cli.py](../../../src/maptoposter/cli.py#L207): `default=12000`
- [README.md](../../../README.md#L82): Documentation says `default: 29000`
- [config.py](../../../src/maptoposter/config.py#L247): `distance: int = 12000`

**Current Code**:
README.md:
```markdown
| `--distance` | `-d` | Map radius in meters | 29000 |
```

cli.py:
```python
parser.add_argument(
    "--distance",
    "-d",
    type=int,
    default=12000,
```

**Recommended Fix**:
Update README.md to reflect the actual default:
```markdown
| `--distance` | `-d` | Map radius in meters | 12000 |
```

**Impact if Unaddressed**:
Users may be confused when their posters look different than expected based on documentation.

**Effort**: Low

---

### [CODE QUALITY] Duplicated logic in _generate_single_city
**File**: [cli.py](../../../src/maptoposter/cli.py#L302-L338)
**Severity**: Medium
**Category**: Technical Debt

**Description**:
The `_generate_single_city()` function duplicates much of the logic from the main `cli()` function for poster generation. Both functions create a `PosterConfig`, instantiate `PosterRenderer`, and call `render()`.

**Current Code**:
```python
def _generate_single_city(...) -> tuple[str, bool, str]:
    try:
        coords = get_coordinates(city, country)
        theme = load_theme(theme_name)
        output_file = generate_output_filename(city, theme_name, output_format)

        config = PosterConfig(...)
        renderer = PosterRenderer(config)
        renderer.render(coords, output_file)
        return (city, True, "")
    except Exception as e:
        return (city, False, str(e))
```

**Recommended Fix**:
Extract shared logic into a helper function that both `_generate_single_city()` and the main `cli()` function can use:

```python
def _render_poster(
    city: str,
    country: str,
    theme_name: str,
    output_format: str,
    distance: int,
    width: float,
    height: float,
    render_backend: str,
    style_config: StyleConfig | None,
    country_label: str | None = None,
    name_label: str | None = None,
) -> Path:
    """Render a single poster and return the output path."""
    coords = get_coordinates(city, country)
    theme = load_theme(theme_name)
    output_file = generate_output_filename(city, theme_name, output_format)

    config = PosterConfig(
        city=city,
        country=country,
        theme_name=theme_name,
        distance=distance,
        width=width,
        height=height,
        output_format=output_format,
        country_label=country_label,
        name_label=name_label,
        theme=theme,
        style_config=style_config,
        render_backend=render_backend,
    )

    renderer = PosterRenderer(config)
    renderer.render(coords, output_file)
    return output_file
```

**Impact if Unaddressed**:
Bug fixes (like the missing `name_label`) need to be applied in multiple places, increasing maintenance burden and risk of inconsistencies.

**Effort**: Medium

---

### [MISSING FUNCTIONALITY] Batch processing doesn't pass name_label or use all CLI options
**File**: [cli.py](../../../src/maptoposter/cli.py#L302-L338)
**Severity**: Medium
**Category**: Missing Functionality

**Description**:
The `_generate_single_city()` function used for batch processing doesn't accept or pass through `name_label` or `country_label` options. While batch processing typically wouldn't use name overrides, there's no way to specify custom display names when using batch mode.

**Current Code**:
```python
def _generate_single_city(
    city: str,
    country: str,
    theme_name: str,
    output_format: str,
    distance: int,
    width: float,
    height: float,
    render_backend: str,
    style_config: StyleConfig | None,
) -> tuple[str, bool, str]:
```

**Recommended Fix**:
Switch to CSV format with headers for self-documenting, extensible batch files:
```csv
city,country,display_name,country_label
Paris,France,,
Tokyo,Japan,東京,JAPAN
New York,USA,NYC,United States
```

**Impact if Unaddressed**:
Users cannot use name overrides in batch mode, limiting the flexibility of the batch feature.

**Effort**: Medium

**Decision**: ✅ Implement CSV with headers format (breaking change for existing batch files)

---

### [DOCUMENTATION GAPS] Missing docstrings for some internal functions
**File**: [render.py](../../../src/maptoposter/render.py)
**Severity**: Low
**Category**: Documentation Gaps

**Description**:
Several private methods in `PosterRenderer` lack docstrings or have minimal documentation:
- `_get_tracking()` - has brief one-liner but could explain the algorithm
- `_split_city_name()` - has brief one-liner but could explain balancing logic
- `_apply_tracking()` - has brief one-liner

While these are private methods, better documentation would help maintainers understand the typography logic.

**Impact if Unaddressed**:
Makes the codebase harder to maintain and understand for new contributors.

**Effort**: Low

---

### [CODE QUALITY] Module-level mutable state in render.py
**File**: [render.py](../../../src/maptoposter/render.py#L74-L88)
**Severity**: Medium
**Category**: Code Quality

**Description**:
The layer cache uses module-level mutable state with global variables:

```python
LAYER_CACHE: dict[str, dict[str, Any]] = {}
LAYER_CACHE_ORDER: list[str] = []
LAYER_CACHE_LOCK = threading.Lock()
LAYER_CACHE_STATS = {
    "hits": 0,
    "misses": 0,
    "evictions": 0,
    "expired": 0,
    "memory_evictions": 0,
}
```

While thread-safe due to the lock, this global state makes testing harder and could cause issues in long-running processes.

**Recommended Fix**:
Implement as a singleton class with explicit `reset()` method for testing:

```python
class LayerCache:
    """Thread-safe LRU cache for rendered layers (singleton)."""

    _instance: LayerCache | None = None

    def __new__(cls) -> LayerCache:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_cache()
        return cls._instance

    def _init_cache(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0, "memory_evictions": 0}

    def get(self, key: str) -> dict[str, Any] | None: ...
    def set(self, key: str, value: dict[str, Any]) -> None: ...
    def clear(self) -> int: ...

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (for testing)."""
        if cls._instance is not None:
            cls._instance._init_cache()
```

**Impact if Unaddressed**:
Testing becomes harder, and cache state can persist across test runs or in long-running applications.

**Effort**: Medium

**Decision**: ✅ Implement singleton pattern with `reset()` method for testability

---

### [TESTING COVERAGE] No tests for datashader backend
**File**: [test_render.py](../../../tests/test_render.py)
**Severity**: Low
**Category**: Testing Coverage

**Description**:
The `DatashaderBackend` class has rendering logic but no dedicated tests. Only a simple fallback test exists:

```python
def test_get_backend_falls_back_to_matplotlib() -> None:
    """Test that get_backend falls back to matplotlib for unknown backends."""
    backend = get_backend("unknown")
    assert backend.name == "matplotlib"
```

**Recommended Fix**:
Add tests that mock datashader to verify:
1. `render_roads()` returns `True` when datashader is available
2. Glow effects are applied correctly
3. Line width calculations are correct
4. Layer sorting (casing before core) works as expected

**Impact if Unaddressed**:
Datashader backend code changes could introduce bugs without detection.

**Effort**: Medium

---

### [CODE QUALITY] Unused PostProcessResult class
**File**: [postprocess.py](../../../src/maptoposter/postprocess.py#L40-L44)
**Severity**: Low
**Category**: Technical Debt

**Description**:
The `PostProcessResult` dataclass is defined but never used anywhere in the codebase. The `apply_raster_effects()` function returns `Image.Image` directly, not wrapped in `PostProcessResult`.

**Current Code**:
```python
@dataclass(frozen=True)
class PostProcessResult:
    """Result container for post-processing operations."""

    image: Image.Image
```

**Recommended Fix**:
Use `PostProcessResult` to wrap the result with metadata about which effects were applied:

```python
@dataclass(frozen=True)
class PostProcessResult:
    """Result container for post-processing operations."""

    image: Image.Image
    effects_applied: tuple[str, ...] = ()
    grain_seed: int | None = None

def apply_raster_effects(image: Image.Image, style: RasterStyle) -> PostProcessResult:
    """Apply raster effects and return result with metadata."""
    effects: list[str] = []
    result = image.convert("RGBA")

    if style.grain_strength > 0:
        result = _apply_grain(result, style.grain_strength, style.seed)
        effects.append("grain")
    # ... etc

    return PostProcessResult(image=result, effects_applied=tuple(effects), grain_seed=style.seed)
```

**Impact if Unaddressed**:
Dead code adds confusion and maintenance overhead.

**Effort**: Low

**Decision**: ✅ Implement with metadata (effects_applied, grain_seed) for debugging/logging

---

### [CODE QUALITY] Inconsistent error handling in geo.py
**File**: [geo.py](../../../src/maptoposter/geo.py)
**Severity**: Low
**Category**: Code Quality

**Description**:
Error handling differs between `get_coordinates()` which raises `ValueError`, and `fetch_graph()`/`fetch_features()` which return `None`. This inconsistency makes the API harder to use predictably.

**Current Code**:
```python
# get_coordinates raises on failure
def get_coordinates(...) -> tuple[float, float]:
    ...
    raise ValueError(f"Could not find coordinates for {city}, {country}")

# fetch_graph returns None on failure
def fetch_graph(...) -> MultiDiGraph | None:
    ...
    return None  # On error
```

**Recommended Fix**:
Make all functions raise exceptions for explicit error handling. Create custom exception types:

```python
class GeoError(Exception):
    """Base exception for geo module errors."""

class GeocodingError(GeoError):
    """Raised when geocoding fails."""

class OSMFetchError(GeoError):
    """Raised when OSM data fetching fails."""

def fetch_graph(point: tuple[float, float], dist: float) -> MultiDiGraph:
    """Fetch the street network graph for a location.

    Raises:
        OSMFetchError: If the street network cannot be fetched.
    """
    # ... implementation
    raise OSMFetchError(f"Failed to fetch street network: {reason}")
```

**Impact if Unaddressed**:
Makes the API harder to use correctly and could lead to uncaught exceptions.

**Effort**: Medium (breaking change)

**Decision**: ✅ Implement consistent exception-based error handling with custom exception types

---

### [PROJECT-SPECIFIC] Entry point redundancy
**File**: [__main__.py](../../../src/maptoposter/__main__.py) and [cli.py](../../../src/maptoposter/cli.py#L660)
**Severity**: Low
**Category**: Project-Specific

**Description**:
Both `__main__.py` and `cli.py` have `if __name__ == "__main__":` blocks. While this is technically fine, the `cli.py` block is redundant since:
1. The package entry point is defined in `pyproject.toml` as `maptoposter.cli:main`
2. `python -m maptoposter` uses `__main__.py`

**Current Code**:
cli.py:
```python
if __name__ == "__main__":
    main()
```

**Recommended Fix**:
Keep both entry points - the redundancy is harmless and provides flexibility for developers who may want to run `python cli.py` directly during development.

**Impact if Unaddressed**:
Minor confusion about which file is the "real" entry point.

**Effort**: Low

**Decision**: ✅ Keep both entry points (no action required)

---

## Summary by Category
- Functional Integrity: 0 issues
- Missing Functionality: 2 issues (1 Critical, 1 Medium)
- Bug Detection: 3 issues (1 High, 2 Medium)
- Technical Debt: 2 issues (1 Medium, 1 Low)
- Documentation Gaps: 2 issues (1 Medium, 1 Low)
- Code Quality: 3 issues (2 Medium, 1 Low)
- Testing Coverage: 2 issues (1 High, 1 Low)
- Project-Specific: 1 issue (Low)

## Recommendations

### Immediate (Before Next Release)
1. **Fix Critical Bug**: Add `name_label=parsed.name_label` to PosterConfig creation in cli.py
2. **Fix Documentation**: Update README.md default distance from 29000 to 12000

### Short-term (Next Sprint)
3. **Create test_geo.py**: Add comprehensive tests for the geo module
4. **Fix bare except clauses**: Replace with specific exception types in cli.py and render.py
5. **Refactor duplicate code**: Extract shared poster generation logic into helper function

### Medium-term (v0.2.0 with Breaking Changes)
6. **Encapsulate layer cache**: Implement singleton `LayerCache` class with `reset()` method ✅
7. **Batch file CSV format**: Switch to CSV with headers for extensibility ✅
8. **Consistent error handling**: Implement custom exceptions (`GeoError`, `OSMFetchError`) in geo.py ✅
9. **Add datashader tests**: Improve test coverage for the alternative rendering backend

### Low Priority
10. **Use PostProcessResult**: Implement with metadata (effects_applied, grain_seed) ✅
11. **Improve internal documentation**: Add more detailed docstrings to typography methods
12. **Entry points**: Keep both (no action required) ✅

## Notes

### Strengths Observed
- **Well-structured codebase**: Clear separation of concerns between modules (CLI, config, geo, render, etc.)
- **Comprehensive type hints**: All functions have proper type annotations
- **Good test coverage**: 169 passing tests covering most functionality
- **Thoughtful configuration**: ruff and mypy are well-configured with sensible rules
- **Documentation**: README is comprehensive with usage examples
- **Error handling**: Most error cases are handled gracefully with meaningful messages
- **Thread safety**: Layer cache properly uses locks for concurrent access

### Architecture Highlights
- The layer-based rendering system is well-designed and extensible
- The theme system with JSON files is maintainable and user-friendly
- The cache system with multiple formats (JSON, GraphML, GeoParquet) is appropriate for different data types
- The backend abstraction (matplotlib/datashader) allows for future rendering engine additions
