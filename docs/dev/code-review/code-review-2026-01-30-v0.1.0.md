# Code Review Report
**Date**: 2026-01-30
**Version**: 0.1.0
**Reviewer**: GitHub Copilot (Claude Opus 4.5)
**Project**: maptoposter
**Status**: ✅ COMPLETED

## Executive Summary
- Total issues found: 17
- Critical: 0
- High: 3 (✅ 3 completed)
- Medium: 6 (✅ 3 completed, ⏭️ 3 deferred)
- Low: 8 (✅ 3 completed, ⏭️ 5 deferred)

### Remediation Summary
- **Completed**: CR-002, CR-003, CR-004, CR-006, CR-007, CR-008, CR-011, CR-013, CR-016
- **Deferred**: CR-001, CR-005, CR-009, CR-010, CR-012, CR-014, CR-015, CR-017

## Review Scope
- Files analyzed: 12 (source) + 7 (tests)
- Lines of code: ~3,500 (source)
- Test coverage: 169 tests passing (100%)

---

## Issues

### CR-001: ⏭️ [Code Quality] High cyclomatic complexity in `build_layers` method
**File**: `src/maptoposter/render.py:710`
**Severity**: Medium
**Category**: Technical Debt

**Description**:
The `build_layers` method has a `noqa: PLR0912` suppression indicating it exceeds the maximum number of branches. This method handles water, waterways, parks, railways, and roads with multiple projection and caching paths.

**Current Code**:
```python
def build_layers(  # noqa: PLR0912
    self,
    graph: MultiDiGraph,
    water: Any,
    parks: Any,
    railways: Any,
    point: tuple[float, float],
    fig: Figure,
    compensated_dist: float,
) -> tuple[list[RenderLayer], tuple[float, float], tuple[float, float]]:
```

**Recommended Fix**:
Extract layer-specific logic into private helper methods:
```python
def build_layers(self, ...) -> tuple[list[RenderLayer], ...]:
    """Prepare layers without rendering."""
    layers: list[RenderLayer] = []
    # ... cache check logic ...

    layers.extend(self._build_water_layers(water_polys, waterways))
    layers.extend(self._build_park_layers(parks_polys))
    layers.extend(self._build_road_layers(edges_gdf))
    layers.extend(self._build_railway_layers(railways_lines))

    return layers, crop_xlim, crop_ylim

def _build_water_layers(self, water_polys, waterways) -> list[RenderLayer]:
    """Build water body and waterway layers."""
    ...
```

**Impact if Unaddressed**:
Difficult to maintain and test individual layer building logic.

**Effort**: Medium

---

### CR-002: ✅ [Code Quality] Unused parameters in `MatplotlibBackend.render_roads`
**File**: `src/maptoposter/render.py:157-161`
**Severity**: Low
**Category**: Code Quality & Best Practices

**Description**:
The `MatplotlibBackend.render_roads` method has 5 parameters all marked with `# noqa: ARG002` because they're unused. The method always returns `False` to defer to standard rendering.

**Current Code**:
```python
def render_roads(
    self,
    ax: Axes,  # noqa: ARG002
    layers: list[RenderLayer],  # noqa: ARG002
    crop_xlim: tuple[float, float],  # noqa: ARG002
    crop_ylim: tuple[float, float],  # noqa: ARG002
    theme: dict[str, str],  # noqa: ARG002
) -> bool:
    """..."""
    return False
```

**Recommended Fix**:
Consider using `*args, **kwargs` or document why this stub implementation is intentional:
```python
def render_roads(
    self,
    ax: Axes,
    layers: list[RenderLayer],
    crop_xlim: tuple[float, float],
    crop_ylim: tuple[float, float],
    theme: dict[str, str],
) -> bool:
    """Matplotlib backend defers to standard rendering path.

    This method intentionally returns False to indicate that the
    PosterRenderer should use its built-in matplotlib rendering
    instead of this backend. Parameters are required by the
    RenderBackend protocol but unused here.
    """
    del ax, layers, crop_xlim, crop_ylim, theme  # Satisfy linter
    return False
```

**Impact if Unaddressed**:
Minor code smell; may confuse future maintainers.

**Effort**: Low

---

### CR-003: ✅ [Bug Detection] Potential memory leak in layer cache
**File**: `src/maptoposter/render.py:56-61`
**Severity**: High
**Category**: Bug Detection

**Description**:
The module-level `LAYER_CACHE` dictionary grows without bound if `enable_layer_cache` is used repeatedly with different coordinates. While there's a `LAYER_CACHE_MAX` limit and TTL, cached graph projections and GeoDataFrames can be very large (hundreds of MB each for large cities).

**Current Code**:
```python
LAYER_CACHE_MAX = 4
LAYER_CACHE_TTL_SECONDS = 3600
LAYER_CACHE: dict[str, dict[str, Any]] = {}
LAYER_CACHE_ORDER: list[str] = []
LAYER_CACHE_LOCK = threading.Lock()
```

**Recommended Fix**:
1. Add memory-based limits (not just count-based)
2. Consider using `weakref` for large objects
3. Add explicit cache clearing after batch operations

```python
import sys

LAYER_CACHE_MAX_BYTES = 500 * 1024 * 1024  # 500MB limit

def _estimate_cache_size() -> int:
    """Estimate current cache memory usage."""
    total = 0
    for payload in LAYER_CACHE.values():
        for key, value in payload.items():
            if hasattr(value, '__sizeof__'):
                total += sys.getsizeof(value)
    return total

def _set_cached_layers(self, cache_key: str, payload: dict[str, Any]) -> None:
    with LAYER_CACHE_LOCK:
        # Check memory limit
        if _estimate_cache_size() > LAYER_CACHE_MAX_BYTES:
            # Evict oldest entries
            while LAYER_CACHE_ORDER and _estimate_cache_size() > LAYER_CACHE_MAX_BYTES * 0.8:
                oldest = LAYER_CACHE_ORDER.pop(0)
                LAYER_CACHE.pop(oldest, None)
        # ... rest of method
```

**Impact if Unaddressed**:
Memory exhaustion during batch processing of many cities.

**Effort**: Medium

---

### CR-004: ✅ [Documentation Gaps] Missing docstrings for private helper methods
**File**: `src/maptoposter/render.py` (multiple locations)
**Severity**: Low
**Category**: Documentation Gaps

**Description**:
Several private methods lack docstrings:
- `_normalize_highway` (line ~458)
- `_format_cache_key` (line ~1021)
- `_get_cached_layers` (line ~1125)
- `_set_cached_layers` (line ~1140)
- `_get_backend` (line ~1105)

**Current Code**:
```python
def _normalize_highway(self, highway: Any) -> str:
    if isinstance(highway, list):
        return highway[0] if highway else "unclassified"
    if highway is None:
        return "unclassified"
    return str(highway)
```

**Recommended Fix**:
```python
def _normalize_highway(self, highway: Any) -> str:
    """Normalize highway value to a string.

    OSM highway tags can be strings, lists of strings, or None.
    This method normalizes them to a single string value.

    Args:
        highway: Raw highway value from OSM edge data.

    Returns:
        Normalized highway type string.
    """
    if isinstance(highway, list):
        return highway[0] if highway else "unclassified"
    if highway is None:
        return "unclassified"
    return str(highway)
```

**Impact if Unaddressed**:
Reduced maintainability; harder for new contributors to understand code.

**Effort**: Low

---

### CR-005: ⏭️ [Functional Integrity] Legacy cache directory note may confuse users
**File**: `src/maptoposter/cache.py` (docstring) and workspace root
**Severity**: Low
**Category**: Documentation Gaps

**Description**:
The copilot-instructions.md mentions "Only `.cache/` is the active cache. Any `cache/` directory at project root is legacy and can be deleted." However, there's still a `cache/` directory in the repo root with 12 `.json` files, which appears to be legacy data.

**Recommended Fix**:
1. Delete the `cache/` directory from the repo root
2. Add `cache/` to `.gitignore` if not already present
3. Update documentation to remove the legacy note once cleaned

**Impact if Unaddressed**:
User confusion about which cache is active; wasted disk space.

**Effort**: Low

---

### CR-006: ✅ [Technical Debt] Type annotation uses `Any` extensively
**File**: `src/maptoposter/render.py` (multiple locations)
**Severity**: Medium
**Category**: Code Quality & Best Practices

**Description**:
The code uses `Any` type annotations in several places where more specific types could be used:
- `water: Any` parameter in `build_layers`
- `parks: Any` parameter in `build_layers`
- `railways: Any` parameter in `build_layers`
- `gdf: Any | None` in `RenderLayer`

**Current Code**:
```python
def build_layers(
    self,
    graph: MultiDiGraph,
    water: Any,
    parks: Any,
    railways: Any,
    ...
```

**Recommended Fix**:
```python
from geopandas import GeoDataFrame

def build_layers(
    self,
    graph: MultiDiGraph,
    water: GeoDataFrame | None,
    parks: GeoDataFrame | None,
    railways: GeoDataFrame | None,
    ...
```

**Impact if Unaddressed**:
Reduced type safety; mypy cannot catch type errors in these paths.

**Effort**: Low

---

### CR-007: ✅ [Missing Functionality] No validation for distance parameter bounds
**File**: `src/maptoposter/cli.py:200-206`
**Severity**: Medium
**Category**: Missing Functionality

**Description**:
The `--distance` CLI argument accepts any integer value, but the copilot-instructions.md warns "Large `dist` values (>20km) cause slow downloads; use 4000-20000m range." There's no validation or warning for values outside this range.

**Current Code**:
```python
parser.add_argument(
    "--distance",
    "-d",
    type=int,
    default=29000,
    help="Map radius in meters (default: 29000)",
)
```

**Recommended Fix**:
```python
parser.add_argument(
    "--distance",
    "-d",
    type=int,
    default=15000,  # More sensible default within recommended range
    help="Map radius in meters (default: 15000, recommended: 4000-20000)",
)

# In cli() function, after parsing:
if parsed.distance > 25000:
    logger.warning(
        "Distance %d meters is very large and may cause slow downloads. "
        "Recommended range: 4000-20000 meters.",
        parsed.distance
    )
if parsed.distance < 1000:
    print("Error: Distance must be at least 1000 meters.")
    return 1
```

**Impact if Unaddressed**:
Users may experience very slow downloads or memory issues with large distances.

**Effort**: Low

---

### CR-008: ✅ [Bug Detection] Default distance (29000m) exceeds recommended range
**File**: `src/maptoposter/config.py:240` and `src/maptoposter/cli.py:205`
**Severity**: High
**Category**: Bug Detection

**Description**:
The default distance is 29000 meters, but the copilot-instructions.md states the recommended range is 4000-20000m. This default could cause slow performance for new users.

**Current Code**:
```python
# In PosterConfig
distance: int = 29000

# In CLI parser
default=29000,
```

**Recommended Fix**:
```python
# In PosterConfig
distance: int = 12000  # Center of recommended range

# In CLI parser
default=12000,
help="Map radius in meters (default: 12000)",
```

**Impact if Unaddressed**:
Poor first-user experience with slow downloads.

**Effort**: Low

---

### CR-009: ⏭️ [Testing Coverage] No integration tests for actual poster generation
**File**: `tests/`
**Severity**: Medium
**Category**: Testing Coverage

**Description**:
All 169 tests are unit tests that mock external dependencies. There are no integration tests that verify end-to-end poster generation (even with minimal parameters like a tiny distance).

**Recommended Fix**:
Add a minimal integration test that generates a very small poster:

```python
# tests/test_integration.py
import pytest
from pathlib import Path
from maptoposter.render import create_poster
from maptoposter.geo import get_coordinates

@pytest.mark.integration
@pytest.mark.slow
def test_generate_minimal_poster(tmp_path: Path):
    """Integration test: generate a tiny poster."""
    # Use a small, well-known location
    point = (48.8566, 2.3522)  # Paris
    output_file = tmp_path / "test_poster.png"

    create_poster(
        city="Paris",
        country="France",
        point=point,
        dist=1000,  # Very small radius
        output_file=output_file,
        output_format="png",
        width=3,  # Tiny size
        height=4,
        show_progress=False,
    )

    assert output_file.exists()
    assert output_file.stat().st_size > 0
```

**Impact if Unaddressed**:
Breaking changes in render pipeline may not be caught by tests.

**Effort**: Medium

---

### CR-010: ⏭️ [Code Quality] Inconsistent error handling in `fetch_graph` and `fetch_features`
**File**: `src/maptoposter/geo.py:83-130` and `133-190`
**Severity**: Medium
**Category**: Code Quality & Best Practices

**Description**:
Both functions return `None` on failure and print error messages, but don't distinguish between network errors, rate limiting, and missing data. Callers must check for `None` but can't determine the failure reason.

**Current Code**:
```python
except (ConnectionError, Timeout) as e:
    logger.error("Network error fetching street network: %s", e)
    print("Network error fetching street network. Check your connection and try again.")
    return None
except HTTPError as e:
    if hasattr(e, "response") and e.response is not None and e.response.status_code == 429:
        logger.error("Rate limited by OSM API")
        print("Rate limited by OSM API. Please wait and try again.")
    # ...
    return None
```

**Recommended Fix**:
Create a custom exception hierarchy:

```python
class GeoError(Exception):
    """Base exception for geo module errors."""
    pass

class NetworkError(GeoError):
    """Network-related error."""
    pass

class RateLimitError(GeoError):
    """Rate limited by API."""
    pass

class NoDataError(GeoError):
    """No data available for location."""
    pass

def fetch_graph(point: tuple[float, float], dist: float) -> MultiDiGraph:
    """Fetch the street network graph for a location.

    Raises:
        NetworkError: On connection issues.
        RateLimitError: When rate limited by OSM API.
        NoDataError: When no street data is available.
    """
```

**Impact if Unaddressed**:
Difficulty implementing retry logic or user-friendly error messages.

**Effort**: Medium

---

### CR-011: ✅ [Project-Specific] pyproject.toml has placeholder URLs
**File**: `pyproject.toml:71-75`
**Severity**: Low
**Category**: Project-Specific Checks

**Description**:
The project URLs still contain placeholder values with `your-username`:

**Current Code**:
```toml
[project.urls]
Homepage = "https://github.com/your-username/maptoposter"
Documentation = "https://github.com/your-username/maptoposter#readme"
Repository = "https://github.com/your-username/maptoposter"
Issues = "https://github.com/your-username/maptoposter/issues"
```

**Recommended Fix**:
Update to actual repository URLs:
```toml
[project.urls]
Homepage = "https://github.com/originalankur/maptoposter"
Documentation = "https://github.com/originalankur/maptoposter#readme"
Repository = "https://github.com/originalankur/maptoposter"
Issues = "https://github.com/originalankur/maptoposter/issues"
```

**Impact if Unaddressed**:
Broken links when package is published to PyPI.

**Effort**: Low

---

### CR-012: ⏭️ [Documentation Gaps] README references images that may not exist
**File**: `README.md`
**Severity**: Low
**Category**: Documentation Gaps

**Description**:
The README references multiple poster images in the `posters/` directory. These files may or may not exist in the repo, and the `posters/` directory appears to be for output, not for committed assets.

**Recommended Fix**:
Either:
1. Add a `docs/images/` directory for committed example images
2. Or host images externally and update URLs
3. Or document that images are generated examples that users must create

**Impact if Unaddressed**:
Broken images in README for users cloning fresh repo.

**Effort**: Low

---

### CR-013: ✅ [Technical Debt] Magic numbers in typography positioning
**File**: `src/maptoposter/render.py:560-575`
**Severity**: Medium
**Category**: Technical Debt

**Description**:
The typography positioning code uses magic numbers for clamping and compensation:

**Current Code**:
```python
y_compensation = max(1.0, aspect_ratio**0.5)  # Square root for gentler scaling

# Clamp to valid range (0.0 - 0.5) to prevent text going too high
city_y = min(city_y, 0.35)
divider_y = min(divider_y, 0.30)
country_y = min(country_y, 0.25)
coords_y = min(coords_y, 0.20)
```

**Recommended Fix**:
Add these as named constants in `render_constants.py`:
```python
# Typography position clamp limits
CITY_NAME_Y_MAX = 0.35
DIVIDER_Y_MAX = 0.30
COUNTRY_LABEL_Y_MAX = 0.25
COORDS_Y_MAX = 0.20
```

**Impact if Unaddressed**:
Difficult to adjust typography behavior without understanding magic values.

**Effort**: Low

---

### CR-014: ⏭️ [Testing Coverage] No tests for `DatashaderBackend`
**File**: `tests/test_render.py`
**Severity**: Medium
**Category**: Testing Coverage

**Description**:
The `DatashaderBackend` class has complex rendering logic including glow effects and line width calculations, but there are no dedicated tests for it. Only the fallback behavior is tested.

**Current Code**:
```python
def test_get_backend_falls_back_to_matplotlib() -> None:
    """Test that get_backend falls back to matplotlib for unknown backends."""
    backend = get_backend("unknown")
    assert backend.name == "matplotlib"
```

**Recommended Fix**:
Add tests for `DatashaderBackend`:
```python
class TestDatashaderBackend:
    """Tests for DatashaderBackend rendering."""

    @pytest.fixture
    def backend(self) -> DatashaderBackend:
        return DatashaderBackend()

    def test_backend_name(self, backend: DatashaderBackend) -> None:
        assert backend.name == "datashader"

    @pytest.mark.skipif(not HAS_DATASHADER, reason="datashader not installed")
    def test_render_roads_with_datashader(self, backend: DatashaderBackend) -> None:
        # Test actual rendering with mocked canvas
        ...

    def test_render_roads_returns_false_without_datashader(self, backend: DatashaderBackend, monkeypatch) -> None:
        # Mock import failure
        monkeypatch.setattr("builtins.__import__", lambda name, *args: (_ for _ in ()).throw(ImportError()) if name == "datashader" else __import__(name, *args))
        ...
```

**Impact if Unaddressed**:
Datashader rendering bugs may go undetected.

**Effort**: Medium

---

### CR-015: ⏭️ [Code Quality] `FontSet` dataclass is mutable but should be immutable
**File**: `src/maptoposter/fonts.py:20-35`
**Severity**: Low
**Category**: Code Quality & Best Practices

**Description**:
`FontSet` is a dataclass used for font paths, but it can be mutated after creation. This conflicts with the intent in `load_fonts()` where missing fonts are set to `None` after creation.

**Current Code**:
```python
@dataclass
class FontSet:
    """Container for font paths and properties."""

    bold: Path | None = None
    regular: Path | None = None
    light: Path | None = None
```

**Recommended Fix**:
Either make it frozen (and adjust `load_fonts`):
```python
@dataclass(frozen=True)
class FontSet:
    """Container for font paths and properties (immutable)."""
    bold: Path | None = None
    regular: Path | None = None
    light: Path | None = None
```

Or document the mutation is intentional and move validation to `__post_init__`:
```python
@dataclass
class FontSet:
    """Container for font paths and properties.

    Note: Font paths are validated on creation and set to None if not found.
    """
    bold: Path | None = None
    regular: Path | None = None
    light: Path | None = None

    def __post_init__(self) -> None:
        """Validate font paths exist."""
        for weight in ["bold", "regular", "light"]:
            path = getattr(self, weight)
            if path and not path.exists():
                logger.warning("Font not found: %s", path)
                object.__setattr__(self, weight, None)
```

**Impact if Unaddressed**:
Minor; unexpected mutation could cause subtle bugs.

**Effort**: Low

---

### CR-016: ✅ [Technical Debt] Duplicate path sanitization logic
**File**: `src/maptoposter/config.py:178-199`
**Severity**: Low
**Category**: Technical Debt

**Description**:
The `_sanitize_filename` function handles Windows reserved names with repeated code for COM and LPT ports.

**Current Code**:
```python
reserved = {"CON", "PRN", "AUX", "NUL"}
reserved.update(f"COM{i}" for i in range(1, 10))
reserved.update(f"LPT{i}" for i in range(1, 10))
```

**Recommended Fix**:
Extract to a module-level constant:
```python
WINDOWS_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)

def _sanitize_filename(name: str) -> str:
    # ...
    if sanitized.upper() in WINDOWS_RESERVED_NAMES:
        sanitized = f"_{sanitized}"
```

**Impact if Unaddressed**:
Minor; set is recreated on every function call.

**Effort**: Low

---

### CR-017: ⏭️ [Missing Functionality] No progress indicator for layer building
**File**: `src/maptoposter/render.py:1172-1230`
**Severity**: Low
**Category**: Missing Functionality

**Description**:
The `render` method shows progress for data fetching (4 steps), but layer building and rendering can take significant time for large datasets with no progress feedback.

**Current Code**:
```python
with tqdm(
    total=4,
    desc="Fetching map data",
    unit="step",
    ...
) as pbar:
    pbar.set_description("Downloading street network")
    graph = fetch_graph(point, compensated_dist)
    # ...

logger.info("All data retrieved successfully.")
logger.info("Rendering map...")  # No progress after this
```

**Recommended Fix**:
Add a second progress bar for rendering:
```python
logger.info("Rendering map...")
with tqdm(
    total=3,
    desc="Rendering poster",
    unit="step",
    disable=not show_progress,
) as pbar:
    pbar.set_description("Building layers")
    layers, crop_xlim, crop_ylim = self.build_layers(...)
    pbar.update(1)

    pbar.set_description("Rendering layers")
    self.render_layers(ax, layers, crop_xlim, crop_ylim)
    pbar.update(1)

    pbar.set_description("Post-processing")
    self.post_process(ax, point, scale_factor, aspect_ratio)
    pbar.update(1)
```

**Impact if Unaddressed**:
Users may think the program is stuck during rendering of large maps.

**Effort**: Low

---

## Summary by Category
- Functional Integrity: 0 issues
- Missing Functionality: 2 issues
- Bug Detection: 2 issues (1 High)
- Technical Debt: 4 issues
- Documentation Gaps: 3 issues
- Code Quality: 5 issues
- Testing Coverage: 2 issues
- Project-Specific: 1 issue

## Recommendations

### Immediate Priority (High Severity)
1. **Fix default distance value** - Change from 29000m to 12000m to align with documentation
2. **Add memory limits to layer cache** - Prevent memory exhaustion during batch processing
3. **Update pyproject.toml URLs** - Fix placeholder repository URLs before publishing

### Short-term (Medium Severity)
4. Refactor `build_layers` method to reduce complexity
5. Add integration tests for end-to-end poster generation
6. Improve type annotations (replace `Any` with specific types)
7. Add distance validation with warnings
8. Create custom exception hierarchy for geo module

### Long-term (Low Severity)
9. Add docstrings to private helper methods
10. Remove legacy `cache/` directory from repo root
11. Move magic numbers to named constants
12. Add tests for `DatashaderBackend`
13. Add rendering progress indicator

## Notes

### Positive Observations
1. **Excellent test coverage** - 169 tests passing with good organization
2. **Type hints throughout** - `py.typed` marker present, most code is typed
3. **Clean separation of concerns** - Modules are well-organized (cli, geo, render, config, etc.)
4. **Good documentation** - Comprehensive copilot-instructions.md and README
5. **Security-conscious caching** - Uses safe serialization (JSON, GraphML, GeoParquet) instead of pickle
6. **Pre-commit hooks configured** - Code quality is maintained

### Architecture Strengths
- Clean dataclass-based configuration (`PosterConfig`, `StyleConfig`, `RenderLayer`)
- Plugin-like render backend system (`RenderBackend` protocol)
- Layered rendering with clear z-order system
- Theme system with validation

### Minor Style Observations
- Code follows PEP 8 and passes ruff checks
- Consistent use of `from __future__ import annotations`
- Good use of context managers and pathlib
