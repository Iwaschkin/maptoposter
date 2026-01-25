# Phase 02: Error Handling Consistency

## Header

| Field | Value |
|-------|-------|
| **Phase ID** | 02 |
| **Phase Name** | Error Handling Consistency |
| **Status** | ✅ Complete |
| **Start Date** | 2025-01-25 |
| **Completion Date** | 2025-01-25 |
| **Dependencies** | Phase 01 (cache contract must be stable) |
| **Owner/Assignee** | AI Assistant |

---

## Tracking Data

| Metric | Value |
|--------|-------|
| **Total Issues** | 5 |
| **Resolved Issues** | 5 |
| **Remaining Issues** | 0 |
| **Progress** | 100% |
| **Blockers** | None |

---

## Issue Registry

| Issue ID | Description | Priority | Status | Completion Date | Notes |
|----------|-------------|----------|--------|-----------------|-------|
| CR-0002 | Cache errors swallowed, converted to warnings | High | ✅ Complete | 2025-01-25 | Uses logging.warning() instead of print() |
| CR-0005 | Silent failures with generic error messages | Medium | ✅ Complete | 2025-01-25 | Specific exception handling (ConnectionError, Timeout, HTTPError) |
| CR-0007 | Fragile async/sync event loop detection | Medium | ✅ Complete | 2025-01-25 | Removed fragile asyncio detection code |
| CR-0013 | Font fallback logic incomplete | Low | ✅ Complete | 2025-01-25 | Fixed None handling in get_properties() |
| CR-0016 | Projection fallback exceptions silently caught | Medium | ✅ Complete | 2025-01-25 | Catches specific (ValueError, CRSError) with logging |

---

## Execution Plan

### Task 1: Improve Cache Error Handling in Geo Module (CR-0002)

**Objective:** Use proper logging instead of print statements for cache warnings.

**Context:** After Phase 01, `cache_set()` returns `bool` instead of raising. Update callers to handle this.

**Current State (geo.py):**
```python
try:
    cache_set(cache_key, coords)
except CacheError as e:
    print(f"Warning: {e}")
```

**Target State:**
```python
import logging
logger = logging.getLogger(__name__)

# In get_coordinates():
if not cache_set(cache_key, coords, CacheType.COORDS):
    logger.warning("Failed to cache coordinates for %s", cache_key)

# In fetch_graph():
if not cache_set(cache_key, graph, CacheType.GRAPH):
    logger.warning("Failed to cache graph for %s", cache_key)

# In fetch_features():
if not cache_set(cache_key, features, CacheType.GEODATA):
    logger.warning("Failed to cache features for %s", cache_key)
```

**Files Affected:**
- `src/maptoposter/geo.py`

**Validation:**
- [ ] No `print()` statements for cache errors
- [ ] Warnings go to stderr via logging
- [ ] Cache failures don't interrupt poster generation

---

### Task 2: Add Specific Exception Handling for OSM Fetching (CR-0005)

**Objective:** Replace bare `except Exception` with specific exception types and meaningful messages.

**Current State (geo.py ~line 122-126):**
```python
except Exception as e:
    print(f"OSMnx error while fetching graph: {e}")
    return None
```

**Target State:**
```python
import logging
from requests.exceptions import ConnectionError, Timeout, HTTPError
from osmnx._errors import InsufficientResponseError

logger = logging.getLogger(__name__)

def fetch_graph(point: tuple[float, float], dist: int) -> nx.MultiDiGraph | None:
    """Fetch street network graph from OSM."""
    # ... cache check ...
    try:
        graph = ox.graph_from_point(point, dist=dist, network_type="all")
        # ... cache and return ...
    except (ConnectionError, Timeout) as e:
        logger.error("Network error fetching OSM data: %s", e)
        logger.info("Check your internet connection and try again.")
        return None
    except HTTPError as e:
        if e.response.status_code == 429:
            logger.error("Rate limited by OSM API. Wait and try again.")
        else:
            logger.error("HTTP error from OSM API: %s", e)
        return None
    except InsufficientResponseError:
        logger.warning("No street data available for this location.")
        return None
    except Exception as e:
        logger.error("Unexpected error fetching OSM graph: %s", e, exc_info=True)
        return None
```

**Apply similar pattern to:**
- `fetch_features()` (~line 157-165)
- `get_coordinates()` (~line 48)

**Files Affected:**
- `src/maptoposter/geo.py`

**Validation:**
- [ ] Different error types produce different log messages
- [ ] Network errors suggest checking connection
- [ ] Rate limiting is detected and reported
- [ ] Stack traces logged for unexpected errors (with `exc_info=True`)

---

### Task 3: Fix Deprecated Asyncio Event Loop Detection (CR-0007)

**Objective:** Remove fragile async/sync detection code or fix deprecation warnings.

**Current State (geo.py ~line 63-73):**
```python
if asyncio.iscoroutine(location):
    try:
        location = asyncio.run(location)
    except RuntimeError as err:
        loop = asyncio.get_event_loop()  # DEPRECATED in 3.10+
        if loop.is_running():
            raise RuntimeError("...") from err
        location = loop.run_until_complete(location)
```

**Analysis:**
- `geopy.Nominatim` with default adapter does NOT return coroutines
- This code appears to be defensive but unnecessary
- The deprecated `get_event_loop()` will cause warnings in Python 3.12+

**Target State - Option A (Remove defensive code):**
```python
geolocator = Nominatim(user_agent="maptoposter")
location = geolocator.geocode(f"{city}, {country}")
# No asyncio handling - Nominatim sync adapter returns Location directly
if location is None:
    raise ValueError(f"Could not find coordinates for {city}, {country}")
```

**Target State - Option B (Fix for async compatibility):**
```python
import asyncio

def _run_sync(coro):
    """Run coroutine synchronously, handling existing event loops."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # Already in async context - create new event loop in thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()

# Usage:
location = geolocator.geocode(f"{city}, {country}")
if asyncio.iscoroutine(location):
    location = _run_sync(location)
```

**Recommended:** Option A - Remove defensive code since geopy sync adapter is used.

**Files Affected:**
- `src/maptoposter/geo.py`

**Validation:**
- [ ] No deprecation warnings in Python 3.12+
- [ ] Geocoding works in standard CLI context
- [ ] (If needed) Works in Jupyter notebook context

---

### Task 4: Fix Font Fallback Logic (CR-0013)

**Objective:** Handle `None` font paths gracefully to avoid `AttributeError`.

**Current State (fonts.py ~line 52-56):**
```python
def get_properties(self, weight: str = "regular", size: float = 12.0) -> FontProperties:
    font_path = getattr(self, weight, self.regular)
    if font_path and font_path.exists():  # Crashes if font_path is None
        return FontProperties(fname=str(font_path), size=size)
    return FontProperties(family="sans-serif", weight=..., size=size)
```

**Issue:** If `self.regular` is `None` and requested weight doesn't exist, `font_path` is `None` and `.exists()` raises `AttributeError: 'NoneType' object has no attribute 'exists'`.

**Target State:**
```python
def get_properties(self, weight: str = "regular", size: float = 12.0) -> FontProperties:
    """Get font properties for the specified weight.

    Falls back to system sans-serif if custom fonts are unavailable.
    """
    font_path = getattr(self, weight, None) or self.regular
    if font_path is not None and font_path.exists():
        return FontProperties(fname=str(font_path), size=size)
    # Fallback to system fonts
    weight_map = {"light": "light", "regular": "normal", "bold": "bold"}
    return FontProperties(
        family="sans-serif",
        weight=weight_map.get(weight, "normal"),
        size=size
    )
```

**Files Affected:**
- `src/maptoposter/fonts.py`

**Validation:**
- [ ] Missing font files fall back to system fonts
- [ ] No `AttributeError` when fonts directory is empty
- [ ] Poster generates (with system fonts) when custom fonts missing

---

### Task 5: Improve Projection Error Handling (CR-0016)

**Objective:** Catch specific projection exceptions and log when fallback is used.

**Current State (render.py ~line 321-340):**
```python
try:
    water_polys = ox.projection.project_gdf(water_polys)
except Exception:  # Catches everything including KeyboardInterrupt
    water_polys = water_polys.to_crs(g_proj.graph["crs"])
```

**Target State:**
```python
import logging
from pyproj.exceptions import CRSError

logger = logging.getLogger(__name__)

def _project_geodataframe(gdf, target_crs, name: str):
    """Project GeoDataFrame with fallback and logging."""
    try:
        return ox.projection.project_gdf(gdf)
    except (ValueError, CRSError) as e:
        logger.debug("OSMnx projection failed for %s, using direct CRS transform: %s", name, e)
        try:
            return gdf.to_crs(target_crs)
        except Exception as e:
            logger.warning("Could not project %s data: %s", name, e)
            return gdf  # Return unprojected as last resort

# Usage in render():
if water_polys is not None and not water_polys.empty:
    water_polys = _project_geodataframe(water_polys, g_proj.graph["crs"], "water")

if parks_polys is not None and not parks_polys.empty:
    parks_polys = _project_geodataframe(parks_polys, g_proj.graph["crs"], "parks")
```

**Files Affected:**
- `src/maptoposter/render.py`

**Validation:**
- [ ] Projection failures are logged at DEBUG level
- [ ] CRS transform failures are logged at WARNING level
- [ ] `KeyboardInterrupt` is not caught
- [ ] Poster still generates with fallback projection

---

## Validation Criteria

Phase 02 is complete when:

1. ✅ **CR-0002:** Cache errors use logging, not print statements
2. ✅ **CR-0005:** OSM fetch errors are categorized and logged appropriately
3. ✅ **CR-0007:** No asyncio deprecation warnings in Python 3.12+
4. ✅ **CR-0013:** Missing fonts fall back gracefully to system fonts
5. ✅ **CR-0016:** Projection errors catch specific exceptions with logging
6. ✅ All existing tests pass
7. ✅ Manual test: Generate poster with network disconnected (verify error messages)

---

## Rollback Plan

If Phase 02 fails:

1. **Checkpoint 1 (after CR-0002):** Revert geo.py cache handling
2. **Checkpoint 2 (after CR-0005):** Revert exception handling changes
3. **Checkpoint 3 (after CR-0007):** Revert asyncio changes
4. **Checkpoint 4 (after CR-0013):** Revert fonts.py changes
5. **Checkpoint 5 (after CR-0016):** Revert render.py projection changes

**Safe Rollback Command:**
```bash
git checkout HEAD~1 -- src/maptoposter/geo.py src/maptoposter/fonts.py src/maptoposter/render.py
```

---

*Phase Document Created: 2026-01-24*
