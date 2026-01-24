# Repository Code Review (GPT-5.2-Codex)

## Executive Summary

**Most Severe Issues:**

1. **Security: Pickle cache deserialization (CR-0001)** - Arbitrary code execution vulnerability when loading cached data from disk
2. **Reliability: Swallowed exceptions in cache operations (CR-0002)** - Cache errors are caught and converted to warnings, potentially hiding disk corruption or permission issues
3. **Test Gap: No tests for render module (CR-0008)** - Core rendering logic has zero test coverage
4. **Test Gap: No tests for geo module (CR-0009)** - Geographic data fetching has zero test coverage
5. **Bug: Cache exception handling inconsistency (CR-0004)** - `cache_get` raises `CacheError` but callers expect `None` on failure
6. **Reliability: Silent failures in OSM data fetch (CR-0005)** - Returns `None` without logging specifics, making debugging difficult
7. **API/Contract: Missing theme key validation (CR-0006)** - Theme files lacking required keys cause runtime `KeyError`
8. **Bug: Unused `name_label` configuration parameter (CR-0003)** - Parameter is accepted but never used in rendering
9. **Bug: CLI behavior depends on `sys.argv` even when args are provided (CR-0021)** - Programmatic usage is inconsistent
10. **Bug: Output filenames are not sanitized for Windows-reserved characters (CR-0022)** - Can crash on save

**Risk Posture:**
The codebase demonstrates good architectural separation and follows modern Python packaging conventions. However, critical security and reliability issues exist. The pickle-based cache poses a significant security risk in shared environments. Exception handling patterns are inconsistent—some modules swallow exceptions, others re-raise them with context, creating unpredictable failure modes. Test coverage is concentrated on configuration and CLI parsing, leaving the core rendering and geographic data modules untested. For a demo pitch, the most critical issues are the untested rendering logic and silent failures that could cause crashes during live demonstration.

---

## Review Methodology

### Scanned Areas
- **Source code:** `src/maptoposter/` (7 Python modules + `__init__.py`)
- **Tests:** `tests/` (3 test files: `test_cache.py`, `test_cli.py`, `test_config.py`)
- **Configuration:** `pyproject.toml`, `.pre-commit-config.yaml`, `.gitignore`
- **CI/CD:** `.github/workflows/conflicts.yml`
- **Data files:** `src/maptoposter/data/themes/*.json` (17 theme files)
- **Documentation:** `README.md`, `.github/copilot-instructions.md`
- **Lock file:** `uv.lock`

### Assumptions and Limitations
- No access to actual runtime execution or test run results (only static analysis)
- Font files (`.ttf`) in `data/fonts/` were not inspected for validity
- Cache files (`.pkl`) in `.cache/` were not deserializable for inspection
- Repository history and branch structure not reviewed
- Third-party dependency security (e.g., osmnx, geopandas) not audited

---

## Issue Index (Tracking System)

| ID | Severity | Category | Component | File:Line | Title | Confidence |
|----|----------|----------|-----------|-----------|-------|------------|
| CR-0001 | Blocker | Security | cache | cache.py:50 | Pickle deserialization allows arbitrary code execution | High |
| CR-0002 | High | Reliability | geo | geo.py:78-88 | Cache errors swallowed, converted to warnings | High |
| CR-0003 | Medium | Bug | config/render | config.py:160, render.py:438 | `name_label` parameter accepted but never used | High |
| CR-0004 | Medium | Bug | cache | cache.py:38-52 | Exception handling inconsistency in `cache_get` | High |
| CR-0005 | Medium | Reliability | geo | geo.py:122-126 | Silent failures with generic error messages | High |
| CR-0006 | Medium | Bug | config | config.py:83-104 | Missing theme key validation | High |
| CR-0007 | Medium | Reliability | geo | geo.py:63-73 | Fragile async/sync event loop detection | Medium |
| CR-0008 | High | Test gap | render | render.py | No test coverage for rendering module | High |
| CR-0009 | High | Test gap | geo | geo.py | No test coverage for geographic module | High |
| CR-0010 | Low | Config/Build | root | .cache/, cache/ | Duplicate cache directories in project | High |
| CR-0011 | Medium | Docs mismatch | README | README.md:77 | `--name` CLI option documented but not implemented | High |
| CR-0012 | Low | Bug | config | config.py:67-68 | `get_available_themes` silently creates missing directory | Medium |
| CR-0013 | Low | Reliability | fonts | fonts.py:52-56 | Font fallback logic incomplete | Medium |
| CR-0014 | Medium | API/Contract | render | render.py:235-249 | Typography positioning hardcoded, not configurable | Medium |
| CR-0015 | Low | Performance | geo | geo.py:48, geo.py:119, geo.py:157 | Blocking `time.sleep()` calls impact UX | High |
| CR-0016 | Medium | Reliability | render | render.py:321-340 | Projection fallback exceptions silently caught | Medium |
| CR-0017 | Low | Config/Build | pyproject.toml | pyproject.toml:65-67 | Placeholder URLs in project metadata | High |
| CR-0018 | Low | Dead code | cli | cli.py:202-207 | Version flag handling duplicates argparse behavior | Medium |
| CR-0019 | Medium | Docs mismatch | README | README.md:69-94 | CLI options table omits `--format` and `--version` | High |
| CR-0020 | Medium | Config/Build | .github | .github/workflows/conflicts.yml | No CI workflow to run tests/lint | High |
| CR-0021 | Medium | Bug | cli | cli.py:213-219 | `cli([])` ignores provided args and reads `sys.argv` | High |
| CR-0022 | Medium | Bug | config | config.py:131-143 | Output filename sanitization is incomplete for Windows | High |
| CR-0023 | Low | Reliability | render | render.py:405-440 | `create_poster()` does not ensure output directory exists | Medium |

---

## Findings (Detailed)

### CR-0001: Pickle deserialization allows arbitrary code execution

- **Severity:** Blocker
- **Category:** Security
- **Component:** cache
- **Location:** [cache.py](src/maptoposter/cache.py#L50)
- **Evidence:**
  ```python
  def cache_get(key: str) -> Any | None:
      ...
      with path.open("rb") as f:
          return pickle.load(f)
  ```
  The cache system uses Python's `pickle` module to serialize and deserialize OSM data. Pickle is inherently unsafe for untrusted data—a malicious `.pkl` file can execute arbitrary code upon loading.

- **Impact:**
  - If an attacker gains write access to the `.cache/` directory (e.g., via directory traversal, shared filesystem, or compromised CI), they can inject malicious pickled objects
  - Arbitrary code execution as the user running `maptoposter`
  - Worst-case: complete system compromise in shared or cloud environments

- **Reproduction/Trigger:**
  1. Create a malicious pickle file: `pickle.dumps(__import__('os').system('id'))`
  2. Place in `.cache/` with a predictable key name (e.g., `coords_new york_usa.pkl`)
  3. Run `maptoposter --city "New York" --country "USA"`

- **Recommended fix:**
  - Replace pickle with a safer serialization format (JSON for coordinates, parquet/geoparquet for GeoDataFrames)
  - If pickle is required, implement HMAC-based integrity verification
  - Document the security implications in README
  - Consider using `cloudpickle` with a restricted `Unpickler` subclass

- **Tests/Verification:**
  - Add test that verifies cache files cannot execute arbitrary code
  - Security audit of cache deserialization paths

---

### CR-0002: Cache errors swallowed, converted to warnings

- **Severity:** High
- **Category:** Reliability
- **Component:** geo
- **Location:** [geo.py](src/maptoposter/geo.py#L78-L88)
- **Evidence:**
  ```python
  try:
      cache_set(cache_key, coords)
  except CacheError as e:
      print(f"Warning: {e}")
  return coords
  ```
  Similar pattern at lines 119-122 and 157-160. Cache write failures are logged as warnings but execution continues, potentially leading to:
  - Repeated expensive API calls without caching
  - Silent disk space exhaustion or permission issues going unnoticed

- **Impact:**
  - Users may not notice cache is non-functional
  - Performance degradation from repeated Nominatim/OSM API calls
  - Rate limiting from upstream services

- **Reproduction/Trigger:**
  - Set `MAPTOPOSTER_CACHE_DIR` to a read-only directory
  - Run multiple poster generations

- **Recommended fix:**
  - Log at `WARNING` level to stderr (not stdout mixed with progress output)
  - Track cache failures and emit a summary at end of run
  - Consider failing fast on persistent cache errors

- **Tests/Verification:**
  - Add tests for cache failure scenarios
  - Verify graceful degradation behavior

---

### CR-0003: `name_label` parameter accepted but never used

- **Severity:** Medium
- **Category:** Bug
- **Component:** config, render
- **Location:** [config.py](src/maptoposter/config.py#L160), [render.py](src/maptoposter/render.py#L410-L438)
- **Evidence:**
  ```python
  # config.py line 160
  name_label: str | None = None

  # render.py line 410
  name_label: str | None = None,

  # render.py _add_typography method uses self.config.city directly:
  city = self.config.city
  spaced_city = "  ".join(list(city.upper()))
  ```
  The `name_label` parameter is defined in `PosterConfig` and accepted in `create_poster()`, but `_add_typography()` always uses `self.config.city` instead of checking `name_label`.

- **Impact:**
  - Users cannot override the displayed city name on posters
  - Documentation suggests this feature exists but it doesn't work
  - API contract violation

- **Reproduction/Trigger:**
  - Call `create_poster()` with `name_label="NYC"` for New York
  - Poster still shows "NEW YORK" instead of "NYC"

- **Recommended fix:**
  ```python
  # In _add_typography:
  city = self.config.name_label or self.config.city
  ```

- **Tests/Verification:**
  - Add test verifying `name_label` overrides displayed city name
  - Integration test with visual output verification

---

### CR-0004: Exception handling inconsistency in `cache_get`

- **Severity:** Medium
- **Category:** Bug
- **Component:** cache
- **Location:** [cache.py](src/maptoposter/cache.py#L38-L52)
- **Evidence:**
  ```python
  def cache_get(key: str) -> Any | None:
      """...
      Raises:
          CacheError: If reading the cache fails.
      """
      try:
          path = _cache_path(key)
          if not path.exists():
              return None
          with path.open("rb") as f:
              return pickle.load(f)
      except Exception as e:
          raise CacheError(f"Cache read failed: {e}") from e
  ```
  The docstring states this raises `CacheError`, but callers like `geo.py` check for `None` as the cache miss indicator:
  ```python
  cached = cache_get(cache_key)
  if cached is not None:
      ...
  ```
  If `cache_get` raises on corrupted files, callers will crash instead of gracefully handling the miss.

- **Impact:**
  - Corrupted cache file causes unhandled exception
  - Application crashes instead of falling back to API fetch

- **Reproduction/Trigger:**
  - Create an invalid/corrupted `.pkl` file in cache directory
  - Run maptoposter command that would load that cache key

- **Recommended fix:**
  - Either catch `CacheError` in callers, or
  - Change `cache_get` to return `None` on errors (with logging) to match expected contract

- **Tests/Verification:**
  - Add test with corrupted cache file
  - Verify graceful fallback to fresh fetch

---

### CR-0005: Silent failures with generic error messages

- **Severity:** Medium
- **Category:** Reliability
- **Component:** geo
- **Location:** [geo.py](src/maptoposter/geo.py#L122-L126), [geo.py](src/maptoposter/geo.py#L161-L165)
- **Evidence:**
  ```python
  except Exception as e:
      print(f"OSMnx error while fetching graph: {e}")
      return None
  ```
  Network errors, authentication issues, rate limiting, and data parsing failures all collapse into the same generic error message and `None` return.

- **Impact:**
  - Users cannot distinguish between transient network errors and permanent failures
  - No retry logic for transient failures
  - Debugging production issues is difficult

- **Reproduction/Trigger:**
  - Run with no network connection
  - Run against a location with no OSM data

- **Recommended fix:**
  - Catch specific exception types (network, timeout, parsing)
  - Log at appropriate levels (WARNING for transient, ERROR for permanent)
  - Consider retry with exponential backoff for network errors

- **Tests/Verification:**
  - Mock OSMnx to raise various exception types
  - Verify appropriate error messages and logging

---

### CR-0006: Missing theme key validation

- **Severity:** Medium
- **Category:** Bug
- **Component:** config
- **Location:** [config.py](src/maptoposter/config.py#L83-L104)
- **Evidence:**
  ```python
  def load_theme(theme_name: str = "feature_based") -> dict[str, str]:
      ...
      with theme_file.open("r", encoding="utf-8") as f:
          theme = json.load(f)
          if not isinstance(theme, dict):
              raise ValueError(...)
          # No validation of required keys!
          return theme_dict
  ```
  Theme files can be missing required keys like `road_motorway`, `water`, `parks`, etc. The renderer will fail with `KeyError` at render time.

- **Impact:**
  - Malformed theme files cause cryptic `KeyError` deep in rendering
  - User-created themes may have subtle typos causing runtime failures

- **Reproduction/Trigger:**
  - Create theme file with missing `road_motorway` key
  - Run maptoposter with that theme
  - Get `KeyError: 'road_motorway'` during render

- **Recommended fix:**
  - Add schema validation in `load_theme()`
  - Define required keys as constant: `REQUIRED_THEME_KEYS = ["bg", "text", "gradient_color", ...]`
  - Validate all required keys present before returning
  - Provide helpful error message listing missing keys

- **Tests/Verification:**
  - Add test loading theme with missing keys
  - Verify validation error message is clear

---

### CR-0007: Fragile async/sync event loop detection

- **Severity:** Medium
- **Category:** Reliability
- **Component:** geo
- **Location:** [geo.py](src/maptoposter/geo.py#L63-L73)
- **Evidence:**
  ```python
  if asyncio.iscoroutine(location):
      try:
          location = asyncio.run(location)
      except RuntimeError as err:
          loop = asyncio.get_event_loop()
          if loop.is_running():
              raise RuntimeError(
                  "Geocoder returned a coroutine while an event loop is "
                  "already running..."
              ) from err
          location = loop.run_until_complete(location)
  ```
  This code attempts to handle both sync and async contexts, but:
  - `asyncio.get_event_loop()` is deprecated in Python 3.10+
  - Race conditions possible between `is_running()` check and `run_until_complete`
  - The `Nominatim` geocoder from `geopy` shouldn't return coroutines in normal usage

- **Impact:**
  - Unpredictable behavior in Jupyter notebooks or async frameworks
  - Deprecation warnings in Python 3.12+
  - Potential deadlocks

- **Reproduction/Trigger:**
  - Run maptoposter from within an async event loop
  - Use in Jupyter environment

- **Recommended fix:**
  - Use `geopy.adapters.AioHTTPAdapter` explicitly for async contexts
  - Remove async detection code if sync-only operation is intended
  - Use `asyncio.get_running_loop()` (Python 3.7+) instead of deprecated API

- **Tests/Verification:**
  - Test in async context (pytest-asyncio)
  - Verify no deprecation warnings

---

### CR-0008: No test coverage for rendering module

- **Severity:** High
- **Category:** Test gap
- **Component:** render
- **Location:** [render.py](src/maptoposter/render.py) (entire file)
- **Evidence:**
  The `tests/` directory contains no `test_render.py`. The rendering module (444 lines) includes:
  - Gradient fade generation
  - Road color/width assignment
  - Typography layout
  - GeoDataFrame projection
  - File output

  None of these are tested.

- **Impact:**
  - Rendering bugs won't be caught before release
  - Refactoring is risky without test coverage
  - Demo could fail due to untested edge cases

- **Reproduction/Trigger:**
  - Any rendering regression goes undetected until visual inspection

- **Recommended fix:**
  - Add unit tests for `get_edge_colors_by_type()`, `get_edge_widths_by_type()`
  - Add tests for gradient generation
  - Add integration tests that verify output files are created
  - Consider visual regression testing with image comparison

- **Tests/Verification:**
  - Achieve >80% line coverage on render.py

---

### CR-0009: No test coverage for geographic module

- **Severity:** High
- **Category:** Test gap
- **Component:** geo
- **Location:** [geo.py](src/maptoposter/geo.py) (entire file)
- **Evidence:**
  The `tests/` directory contains no `test_geo.py`. The geo module includes:
  - Geocoding with Nominatim
  - OSM graph fetching
  - Feature fetching (water, parks)
  - Crop limit calculation

  None of these have test coverage.

- **Impact:**
  - Geocoding failures won't be caught
  - API contract changes from osmnx could break silently
  - Coordinate calculation bugs could produce wrong output

- **Reproduction/Trigger:**
  - Any geo module regression goes undetected

- **Recommended fix:**
  - Add tests with mocked Nominatim responses
  - Add tests with mocked osmnx graph/feature data
  - Test `get_crop_limits()` with various aspect ratios

- **Tests/Verification:**
  - Achieve >80% line coverage on geo.py

---

### CR-0010: Duplicate cache directories in project

- **Severity:** Low
- **Category:** Config/Build
- **Component:** root
- **Location:** Project root: `.cache/`, `cache/`
- **Evidence:**
  Two cache-like directories exist:
  - `.cache/` - contains `.pkl` files (actual cache, per code)
  - `cache/` - contains `.json` files (unknown purpose, possibly old cache format)

  The `.gitignore` ignores both `.cache/` and `cache/`, but only `.cache/` is documented.

- **Impact:**
  - Confusion about which cache is active
  - Potential for stale data in wrong directory
  - Disk space waste

- **Reproduction/Trigger:**
  - Inspect project root

- **Recommended fix:**
  - Investigate purpose of `cache/` directory with `.json` files
  - Remove obsolete cache directory
  - Update documentation if `cache/` serves a different purpose

- **Tests/Verification:**
  - Verify only one cache mechanism is in use

---

### CR-0011: `--name` CLI option documented but not implemented

- **Severity:** Medium
- **Category:** Docs mismatch
- **Component:** README
- **Location:** [README.md](README.md#L77)
- **Evidence:**
  ```markdown
  | **OPTIONAL:** `--name` | | Override display name (city display on poster) | |
  ```
  But in `cli.py`, there is no `--name` argument defined. Only `--country-label` exists for override purposes.

- **Impact:**
  - Users following documentation will get "unrecognized argument" error
  - Confusing UX

- **Reproduction/Trigger:**
  - Run `maptoposter --name "NYC" -c "New York" -C "USA"`
  - Get error: `unrecognized arguments: --name NYC`

- **Recommended fix:**
  - Either implement `--name` argument (linking to `name_label` config), or
  - Remove from documentation

- **Tests/Verification:**
  - CLI test for `--name` argument if implemented

---

### CR-0012: `get_available_themes` silently creates missing directory

- **Severity:** Low
- **Category:** Bug
- **Component:** config
- **Location:** [config.py](src/maptoposter/config.py#L67-L68)
- **Evidence:**
  ```python
  if not themes_dir.exists():
      themes_dir.mkdir(parents=True, exist_ok=True)
      return []
  ```
  A function called `get_available_themes` (read operation) silently creates directories (write operation). This violates principle of least surprise.

- **Impact:**
  - Unexpected directory creation as side effect
  - Could mask configuration errors where themes_dir is misconfigured

- **Reproduction/Trigger:**
  - Delete themes directory
  - Call `get_available_themes()`
  - Directory is recreated empty

- **Recommended fix:**
  - Remove directory creation from getter function
  - Let caller handle missing directory explicitly
  - Or rename function to indicate side effects

- **Tests/Verification:**
  - Test that missing themes dir returns empty list without side effects

---

### CR-0013: Font fallback logic incomplete

- **Severity:** Low
- **Category:** Reliability
- **Component:** fonts
- **Location:** [fonts.py](src/maptoposter/fonts.py#L52-L56)
- **Evidence:**
  ```python
  def get_properties(self, weight: str = "regular", size: float = 12.0) -> FontProperties:
      font_path = getattr(self, weight, self.regular)
      if font_path and font_path.exists():
          return FontProperties(fname=str(font_path), size=size)
      # Fallback to system fonts
      return FontProperties(family="sans-serif", weight=weight_map.get(weight, "normal"), size=size)
  ```
  If `self.regular` is `None` (all fonts missing), `getattr(self, weight, self.regular)` returns `None`, and `font_path.exists()` will raise `AttributeError`.

- **Impact:**
  - Complete font directory missing causes crash
  - Error message is cryptic (`'NoneType' has no attribute 'exists'`)

- **Reproduction/Trigger:**
  - Delete all font files from `data/fonts/`
  - Generate a poster

- **Recommended fix:**
  ```python
  font_path = getattr(self, weight, None) or self.regular
  if font_path is not None and font_path.exists():
  ```

- **Tests/Verification:**
  - Test with missing fonts directory

---

### CR-0014: Typography positioning hardcoded, not configurable

- **Severity:** Medium
- **Category:** API/Contract
- **Component:** render
- **Location:** [render.py](src/maptoposter/render.py#L235-L249)
- **Evidence:**
  ```python
  # City name
  ax.text(0.5, 0.14, spaced_city, ...)
  # Country label
  ax.text(0.5, 0.10, country_text.upper(), ...)
  # Coordinates
  ax.text(0.5, 0.07, coords, ...)
  ```
  All text positions are hardcoded. The gradient extends 25% from edges, but text at 0.14 may overlap with different poster sizes.

- **Impact:**
  - Custom poster sizes may have overlapping or misplaced text
  - Very long city names may extend beyond margins
  - No way to customize layout without code changes

- **Reproduction/Trigger:**
  - Generate poster with very long city name like "Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch"
  - Text may overflow or be truncated poorly

- **Recommended fix:**
  - Add layout configuration to theme or config
  - Calculate positions relative to text bounding boxes
  - Add text wrapping for long names

- **Tests/Verification:**
  - Visual tests with extreme city name lengths

---

### CR-0015: Blocking `time.sleep()` calls impact UX

- **Severity:** Low
- **Category:** Performance
- **Component:** geo
- **Location:** [geo.py](src/maptoposter/geo.py#L48), [geo.py](src/maptoposter/geo.py#L119), [geo.py](src/maptoposter/geo.py#L157)
- **Evidence:**
  ```python
  time.sleep(1)   # Before geocoding
  time.sleep(0.5) # After graph fetch
  time.sleep(0.3) # After feature fetch
  ```
  These blocking delays are hardcoded and occur even when data is cached.

- **Impact:**
  - 1.8+ seconds of mandatory delay per run
  - Poor UX during demo if multiple posters generated

- **Reproduction/Trigger:**
  - Run maptoposter with fully cached data
  - Still experiences delays

- **Recommended fix:**
  - Move sleep after successful API call, not before
  - Skip sleep when loading from cache
  - Make sleep duration configurable

- **Tests/Verification:**
  - Verify no sleep when cache hit

- **Notes:** Related to CR-0002 (cache reliability)

---

### CR-0016: Projection fallback exceptions silently caught

- **Severity:** Medium
- **Category:** Reliability
- **Component:** render
- **Location:** [render.py](src/maptoposter/render.py#L321-L340)
- **Evidence:**
  ```python
  try:
      water_polys = ox.projection.project_gdf(water_polys)
  except Exception:
      water_polys = water_polys.to_crs(g_proj.graph["crs"])
  ```
  Similar pattern for parks. The bare `except Exception` hides:
  - What caused the projection failure
  - Whether the fallback is appropriate
  - Memory errors or keyboard interrupts

- **Impact:**
  - CRS mismatches could produce visually incorrect output
  - Debugging projection issues is difficult
  - Could catch `KeyboardInterrupt` inappropriately

- **Reproduction/Trigger:**
  - Location with unusual CRS in OSM data

- **Recommended fix:**
  - Catch specific exceptions (`ValueError`, `CRSError`)
  - Log when fallback is used
  - Don't catch `BaseException` derivatives

- **Tests/Verification:**
  - Test with mocked projection failures

---

### CR-0017: Placeholder URLs in project metadata

- **Severity:** Low
- **Category:** Config/Build
- **Component:** pyproject.toml
- **Location:** [pyproject.toml](pyproject.toml#L65-L67)
- **Evidence:**
  ```toml
  Homepage = "https://github.com/your-username/maptoposter"
  Documentation = "https://github.com/your-username/maptoposter#readme"
  Repository = "https://github.com/your-username/maptoposter"
  ```
  Placeholder URLs with `your-username` are present.

- **Impact:**
  - Published package metadata will have broken links
  - Unprofessional appearance on PyPI

- **Reproduction/Trigger:**
  - Build and inspect package metadata

- **Recommended fix:**
  - Replace with actual repository URLs before publishing

- **Tests/Verification:**
  - Add pre-release check for placeholder strings

---

### CR-0018: Version flag handling duplicates argparse behavior

- **Severity:** Low
- **Category:** Dead code
- **Component:** cli
- **Location:** [cli.py](cli.py#L202-L207)
- **Evidence:**
  ```python
  parser.add_argument("--version", "-v", action="store_true", help="Show version and exit")
  ...
  if parsed.version:
      from . import __version__
      print(f"maptoposter {__version__}")
      return 0
  ```
  This manually implements version printing, but argparse has built-in `action="version"`:
  ```python
  parser.add_argument("--version", "-v", action="version", version=f"maptoposter {__version__}")
  ```

- **Impact:**
  - Extra code to maintain
  - Inconsistent with standard CLI conventions (version flag typically exits after printing)

- **Reproduction/Trigger:**
  - Compare with standard argparse version behavior

- **Recommended fix:**
  - Use argparse's built-in version action

- **Tests/Verification:**
  - Existing tests cover version flag

---

### CR-0019: CLI options table omits `--format` and `--version`

- **Severity:** Medium
- **Category:** Docs mismatch
- **Component:** README
- **Location:** [README.md](README.md#L74-L87)
- **Evidence:**
  ```markdown
  | **OPTIONAL:** `--width` | `-W` | Image width in inches | 12 |
  | **OPTIONAL:** `--height` | `-H` | Image height in inches | 16 |
  ```
  The CLI defines `--format` and `--version`, but they are not documented in the options table.

- **Impact:**
  - Users may not discover output format or version flags
  - Documentation is incomplete compared to CLI capabilities

- **Reproduction/Trigger:**
  - Search options table for `--format` or `--version`

- **Recommended fix:**
  - Add `--format` and `--version` rows to the options table
  - Ensure the table stays in sync with CLI arguments

- **Tests/Verification:**
  - Add a doc check that validates documented options against argparse definitions

---

### CR-0020: No CI workflow to run tests or linting

- **Severity:** Medium
- **Category:** Config/Build
- **Component:** .github
- **Location:** [.github/workflows/conflicts.yml](.github/workflows/conflicts.yml#L1-L18)
- **Evidence:**
  The only workflow handles merge-conflict labeling. There is no workflow that runs tests, linters, or type checks.

- **Impact:**
  - Regressions can merge undetected
  - No automated signal before releases or demo builds

- **Reproduction/Trigger:**
  - Observe GitHub Actions workflows; only merge-conflict labeling exists

- **Recommended fix:**
  - Add CI workflow to run `uv run pytest`, `uv run ruff check`, and `uv run mypy`
  - Gate merges on CI success

- **Tests/Verification:**
  - Verify CI runs on PRs and fails on introduced regressions

---

### CR-0021: `cli([])` ignores provided args and reads `sys.argv`

- **Severity:** Medium
- **Category:** Bug
- **Component:** cli
- **Location:** [cli.py](src/maptoposter/cli.py#L213-L218)
- **Evidence:**
  ```python
  # If no arguments provided, show examples
  if len(sys.argv) == 1 and args is None:
      _print_examples()
      return 0
  ```
  When `cli([])` is called programmatically, `args` is not `None`, so the condition fails and the CLI falls through to argument validation even though no args were provided.

- **Impact:**
  - Programmatic usage (`cli([])`) returns error instead of showing examples
  - Inconsistent behavior between CLI entrypoint and direct function call

- **Reproduction/Trigger:**
  - Call `cli([])` from a Python REPL

- **Recommended fix:**
  - Use `if args is None and len(sys.argv) == 1` for CLI execution
  - Or change condition to `if not (args or sys.argv[1:])`

- **Tests/Verification:**
  - Add test for `cli([])` returning 0 and printing examples

---

### CR-0022: Output filename sanitization is incomplete for Windows

- **Severity:** Medium
- **Category:** Bug
- **Component:** config
- **Location:** [config.py](src/maptoposter/config.py#L136-L141)
- **Evidence:**
  ```python
  city_slug = city.lower().replace(" ", "_").replace(",", "")
  filename = f"{city_slug}_{theme_name}_{timestamp}.{ext}"
  ```
  Only spaces and commas are sanitized. City names can include characters invalid on Windows (e.g., `:`, `?`, `*`, `/`, `\\`), causing `OSError` at save time.

- **Impact:**
  - Poster generation fails for cities containing reserved characters
  - Cross-platform incompatibility in generated filenames

- **Reproduction/Trigger:**
  - Use a city name like `St. John's/Port` or `Mexico:City`
  - Saving fails on Windows

- **Recommended fix:**
  - Normalize and sanitize filenames (e.g., replace invalid characters with `_`)
  - Consider using a slugify helper

- **Tests/Verification:**
  - Unit tests for filename generation with reserved characters

---

### CR-0023: `create_poster()` does not ensure output directory exists

- **Severity:** Low
- **Category:** Reliability
- **Component:** render
- **Location:** [render.py](src/maptoposter/render.py#L405-L440)
- **Evidence:**
  ```python
  def create_poster(..., output_file: Path, ...):
      ...
      renderer.render(point, output_file)
  ```
  `create_poster()` accepts an `output_file` path but does not ensure the parent directory exists before saving.

- **Impact:**
  - Programmatic use of `create_poster()` can fail with `FileNotFoundError`
  - Inconsistent behavior compared to CLI, which uses `get_posters_dir()`

- **Reproduction/Trigger:**
  - Call `create_poster()` with `output_file` pointing to a non-existent directory

- **Recommended fix:**
  - Create the parent directory before saving (`output_file.parent.mkdir(parents=True, exist_ok=True)`)

- **Tests/Verification:**
  - Add test that uses a nested temporary directory path

---

## Cross-Cutting Concerns

### Architectural/Systemic Risks

**Error Handling Strategy:**
The codebase lacks a consistent error handling philosophy. Some modules (cache) raise custom exceptions, others (geo) return `None` on failure, and callers sometimes catch exceptions (cli) but sometimes don't (render). This creates unpredictable failure modes.

**Recommendation:** Establish a consistent strategy—either fail-fast with typed exceptions, or use result types with explicit error handling.

**Dependency Management:**
The `uv.lock` file pins exact dependency versions (good), but the `pyproject.toml` uses minimum version constraints like `>=1.0.0` (normal for libraries but potentially risky for applications). Major version bumps in osmnx or geopandas could break functionality.

**Recommendation:** Consider tighter version constraints for critical dependencies.

### API Consistency and Contracts

**PosterConfig vs Function Parameters:**
The `create_poster()` function accepts many parameters that duplicate `PosterConfig` fields. This creates confusion about which is the source of truth and makes it easy to pass inconsistent values.

**Recommendation:** Either use only `PosterConfig`, or clearly document that function parameters override config values.

### Config and Deployment Posture

**Secrets/Environment:**
The only environment variable is `MAPTOPOSTER_CACHE_DIR`, which is reasonable. No secrets management issues detected.

**12-Factor Compliance:**
- Codebase: Single repo ✓
- Dependencies: Declared in pyproject.toml ✓
- Config: Only cache dir is configurable via env ✓
- Backing services: OSM APIs used appropriately ✓
- Build/Release/Run: No explicit separation (manual `uv run`)
- Processes: Stateless except cache ✓
- Port binding: N/A (CLI tool)
- Concurrency: Not designed for concurrent use
- Disposability: Fast startup ✓
- Dev/Prod parity: Good with uv
- Logs: Uses print() to stdout (basic, but functional)
- Admin processes: None defined

### Testing Strategy Gaps

| Module | Lines | Test Coverage |
|--------|-------|---------------|
| cli.py | 304 | Partial (parser, flags) |
| config.py | 165 | Good (themes, config) |
| cache.py | 70 | Good (roundtrip, dirs) |
| geo.py | 206 | None |
| render.py | 444 | None |
| fonts.py | 74 | None |

**Critical Gap:** The two largest and most complex modules (render.py, geo.py) have zero test coverage.

---

## Appendix

### Feature requests

- **FR-0001: Add Typer-based CLI**
  - Rationale: Improves CLI ergonomics (rich help, type-driven validation, shell completion) and supports future subcommands without large argparse refactors.
  - Impact: Requires new dependency and migration plan for existing argparse flags.
  - Suggested approach: Introduce Typer entrypoint alongside existing CLI, then deprecate argparse after parity.

### Questionable Areas Needing Human Confirmation

1. **Cache Directory Contents:**
   - The `cache/` directory (not `.cache/`) contains JSON files with SHA-1-like names
   - Hypothesis: These may be from an older cache implementation or a different tool
   - Evidence needed: Check git history for origin of these files

2. **Font Licensing:**
   - Roboto fonts included in `data/fonts/`
   - Hypothesis: Fonts are Apache 2.0 licensed and distribution is legal
   - Evidence needed: Verify license compatibility with MIT project license

3. **Rate Limiting Adequacy:**
   - 1-second delay before Nominatim calls
   - Hypothesis: Compliant with Nominatim usage policy
   - Evidence needed: Verify against current Nominatim ToS (nominatim.org)

4. **GeoDataFrame Memory Usage:**
   - Large `dist` values fetch significant OSM data
   - Hypothesis: Memory usage could exceed typical machine RAM for very large areas
   - Evidence needed: Profiling with various dist values

5. **Thread Safety:**
   - Global matplotlib state used without explicit backend configuration
   - Hypothesis: Concurrent calls to `PosterRenderer.render()` may interfere
   - Evidence needed: Test concurrent execution

### No Issues Found

The following areas were reviewed and no significant issues were identified:

- **Pre-commit Configuration:** Comprehensive hooks for code quality
- **Type Hints:** Consistent use of modern Python typing throughout
- **Docstrings:** All public functions have Google-style docstrings
- **Theme JSON Files:** All 17 theme files have consistent structure
- **License:** MIT license properly declared

---

## Severity Rubric Applied

| Severity | Count | Description |
|----------|-------|-------------|
| Blocker | 1 | CR-0001 (pickle security) |
| High | 4 | CR-0002, CR-0008, CR-0009, CR-0005 |
| Medium | 12 | CR-0003, CR-0004, CR-0006, CR-0007, CR-0011, CR-0014, CR-0016, CR-0018, CR-0019, CR-0020, CR-0021, CR-0022 |
| Low | 6 | CR-0010, CR-0012, CR-0013, CR-0015, CR-0017, CR-0023 |

---

*Review generated: 2026-01-24*
*Reviewer: GPT-5.2-Codex (automated static analysis)*
