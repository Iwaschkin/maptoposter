# Phase 01: Security & Cache Foundation

## Header

| Field | Value |
|-------|-------|
| **Phase ID** | 01 |
| **Phase Name** | Security & Cache Foundation |
| **Status** | ✅ Complete |
| **Start Date** | 2025-01-25 |
| **Completion Date** | 2025-01-25 |
| **Dependencies** | None (foundational phase) |
| **Owner/Assignee** | AI Assistant |

---

## Tracking Data

| Metric | Value |
|--------|-------|
| **Total Issues** | 4 |
| **Resolved Issues** | 4 |
| **Remaining Issues** | 0 |
| **Progress** | 100% |
| **Blockers** | None |

---

## Issue Registry

| Issue ID | Description | Priority | Status | Completion Date | Notes |
|----------|-------------|----------|--------|-----------------|-------|
| CR-0001 | Pickle deserialization allows arbitrary code execution | Blocker | ✅ Complete | 2025-01-25 | Migrated to JSON/GraphML/GeoParquet |
| CR-0004 | Exception handling inconsistency in `cache_get` | Medium | ✅ Complete | 2025-01-25 | cache_get returns None, cache_set returns bool |
| CR-0010 | Duplicate cache directories in project | Low | ✅ Complete | 2025-01-25 | Removed stale cache/ directory |
| CR-0015 | Blocking `time.sleep()` calls impact UX | Low | ✅ Complete | 2025-01-25 | Sleep moved after API calls, skipped for cache hits |

---

## Execution Plan

### Task 1: Investigate and Remove Duplicate Cache Directory (CR-0010)

**Objective:** Determine purpose of `cache/` directory and clean up.

**Steps:**
1. Examine contents of `cache/*.json` files to understand their purpose
2. Check if any code references the `cache/` directory
3. If obsolete: remove `cache/` directory from repo
4. If needed: document its purpose or consolidate with `.cache/`

**Files Affected:**
- `cache/` directory (removal candidate)
- `.gitignore` (verify entries)

**Validation:**
- [ ] No code references `cache/` directory
- [ ] Only `.cache/` is used for caching

---

### Task 2: Replace Pickle with Safe Serialization (CR-0001)

**Objective:** Eliminate arbitrary code execution vulnerability by replacing pickle.

**Steps:**

1. **Define new cache format strategy:**
   - Coordinates (lat/lon): JSON (simple, safe)
   - Street graphs (NetworkX): Use `osmnx.save_graphml()` / `osmnx.load_graphml()` (XML-based)
   - GeoDataFrames (water, parks): Use GeoParquet via `geopandas.to_parquet()` / `read_parquet()`

2. **Update `cache.py`:**
   ```python
   # New imports
   import json
   import geopandas as gpd
   import osmnx as ox
   from pathlib import Path

   # Define cache type enum
   class CacheType(Enum):
       COORDS = "coords"      # JSON
       GRAPH = "graph"        # GraphML
       GEODATA = "geodata"    # GeoParquet

   def cache_set(key: str, data: Any, cache_type: CacheType) -> None:
       """Write to cache using appropriate format based on type."""
       path = _cache_path(key, cache_type)
       if cache_type == CacheType.COORDS:
           path.write_text(json.dumps(data))
       elif cache_type == CacheType.GRAPH:
           ox.save_graphml(data, path)
       elif cache_type == CacheType.GEODATA:
           data.to_parquet(path)

   def cache_get(key: str, cache_type: CacheType) -> Any | None:
       """Read from cache using appropriate format based on type."""
       path = _cache_path(key, cache_type)
       if not path.exists():
           return None
       if cache_type == CacheType.COORDS:
           return json.loads(path.read_text())
       elif cache_type == CacheType.GRAPH:
           return ox.load_graphml(path)
       elif cache_type == CacheType.GEODATA:
           return gpd.read_parquet(path)
   ```

3. **Update file extensions:**
   - `.pkl` → `.json` (coords)
   - `.pkl` → `.graphml` (graphs)
   - `.pkl` → `.parquet` (geodata)

4. **Update `geo.py` callers:**
   - Update all `cache_get()` and `cache_set()` calls to include `cache_type` parameter
   - Coordinates: `CacheType.COORDS`
   - Graph: `CacheType.GRAPH`
   - Water/Parks: `CacheType.GEODATA`

5. **Add migration note:**
   - Document that existing `.pkl` cache files should be deleted
   - Old cache will not be read (safe fail-open to re-fetch)

**Files Affected:**
- `src/maptoposter/cache.py` (major rewrite)
- `src/maptoposter/geo.py` (update cache calls)
- `pyproject.toml` (add `pyarrow` dependency if not present)

**Validation:**
- [ ] No pickle imports remain in codebase
- [ ] Cache files are in safe formats (JSON, GraphML, Parquet)
- [ ] Malicious file injection cannot execute code
- [ ] Existing functionality preserved

---

### Task 3: Standardize Cache Exception Handling (CR-0004)

**Objective:** Establish consistent contract for cache failures.

**Current State:**
- `cache_get` docstring says it raises `CacheError`
- Callers expect `None` on cache miss
- Corrupted files cause unhandled exceptions

**Target State:**
- `cache_get` returns `None` on any failure (miss or error)
- Errors are logged for debugging
- Callers handle `None` uniformly

**Steps:**

1. **Update `cache_get` in `cache.py`:**
   ```python
   def cache_get(key: str, cache_type: CacheType) -> Any | None:
       """Retrieve value from cache.

       Returns:
           Cached value if found, None if cache miss or error.
       """
       try:
           path = _cache_path(key, cache_type)
           if not path.exists():
               return None
           # Read based on type...
           return data
       except Exception as e:
           # Log error but return None to allow graceful fallback
           import logging
           logging.getLogger(__name__).warning(f"Cache read error for {key}: {e}")
           return None
   ```

2. **Update `cache_set` to not raise on failure:**
   ```python
   def cache_set(key: str, data: Any, cache_type: CacheType) -> bool:
       """Write value to cache.

       Returns:
           True if successful, False on error.
       """
       try:
           # Write based on type...
           return True
       except Exception as e:
           import logging
           logging.getLogger(__name__).warning(f"Cache write error for {key}: {e}")
           return False
   ```

3. **Remove `CacheError` exception class** (no longer raised)

4. **Update tests in `test_cache.py`** to reflect new contract

**Files Affected:**
- `src/maptoposter/cache.py`
- `tests/test_cache.py`

**Validation:**
- [ ] `cache_get` never raises exceptions
- [ ] Cache errors are logged, not printed
- [ ] Tests pass with new contract

---

### Task 4: Optimize Rate Limiting Delays (CR-0015)

**Objective:** Move `time.sleep()` calls after API calls and skip when cached.

**Current State:**
```python
# geo.py
time.sleep(1)  # Always sleeps before geocoding
cached = cache_get(key)
if cached is not None:
    return cached  # Wasted 1 second!
# Make API call...
```

**Target State:**
```python
# geo.py
cached = cache_get(key, CacheType.COORDS)
if cached is not None:
    return cached  # No delay for cached data!
# Make API call...
result = api_call()
time.sleep(1)  # Delay after API call, before next potential call
cache_set(key, result, CacheType.COORDS)
return result
```

**Steps:**

1. **In `get_coordinates()` (geo.py ~line 48):**
   - Move `time.sleep(1)` to after the Nominatim API call
   - Check cache before any delay

2. **In `fetch_graph()` (geo.py ~line 119):**
   - Move `time.sleep(0.5)` to after `ox.graph_from_point()` call
   - Check cache before any delay

3. **In `fetch_features()` (geo.py ~line 157):**
   - Move `time.sleep(0.3)` to after `ox.features_from_point()` call
   - Check cache before any delay

**Files Affected:**
- `src/maptoposter/geo.py`

**Validation:**
- [ ] Cached requests have no artificial delay
- [ ] Rate limiting still occurs between actual API calls
- [ ] Performance improvement measurable on cached runs

---

## Validation Criteria

Phase 01 is complete when:

1. ✅ **CR-0001 (Blocker):** No pickle serialization in codebase
2. ✅ **CR-0004:** Cache operations return `None`/`bool` instead of raising
3. ✅ **CR-0010:** Only `.cache/` directory exists (or `cache/` documented)
4. ✅ **CR-0015:** Cached requests execute without delay
5. ✅ All existing tests pass
6. ✅ Manual test: Generate poster for "Paris, France" successfully

---

## Rollback Plan

If Phase 01 fails:

1. **Checkpoint 1 (after CR-0010):** Git revert to pre-cleanup state
2. **Checkpoint 2 (after CR-0001):** Cache format change is backwards-incompatible; users must delete `.cache/` directory
3. **Checkpoint 3 (after CR-0004):** Revert cache.py to re-add CacheError if callers need it
4. **Checkpoint 4 (after CR-0015):** Sleep timing is low-risk, simple revert

**Safe Rollback Command:**
```bash
git stash  # Save any uncommitted work
git checkout main -- src/maptoposter/cache.py src/maptoposter/geo.py
```

---

*Phase Document Created: 2026-01-24*
