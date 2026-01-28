# Python Code Review Plan — MapToPoster

## Top 5 highest value changes
- [x] High (CLI-01, Status: Completed) - Add guardrails for CLI inputs and theme/preset resolution in [src/maptoposter/cli.py](src/maptoposter/cli.py) to avoid mixed states (preset + all-themes or style-pack + all-themes).
- [x] High (TEST-02, Status: Completed) - Add unit tests for new rendering pipeline stages (layers, casing/core, glow, datashader fallback) in [tests/test_render.py](tests/test_render.py).
- [ ] Medium (A-02, Status: Completed) - Introduce a render backend registry and configuration validation in [src/maptoposter/render.py](src/maptoposter/render.py) and [src/maptoposter/config.py](src/maptoposter/config.py) to prevent invalid backend strings.
- [ ] Medium (LOG-01, Status: Not Started) - Add structured error handling and logging around cache IO and geocoding in [src/maptoposter/cache.py](src/maptoposter/cache.py) and [src/maptoposter/geo.py](src/maptoposter/geo.py) with consistent error messages.
- [x] Medium (CR-01, Status: Completed) - Add style-pack schema validation with clear user errors in [src/maptoposter/render.py](src/maptoposter/render.py) and CLI integration in [src/maptoposter/cli.py](src/maptoposter/cli.py).

## Architecture and design
- [x] High (A-01, Status: Completed) - Split rendering concerns: move post-processing helpers from [src/maptoposter/render.py](src/maptoposter/render.py) into a dedicated module (e.g., postprocess.py) to reduce the god-module shape.
- [x] Medium (A-02, Status: Completed) - Introduce a small render backend registry mapping names to backend instances in [src/maptoposter/render.py](src/maptoposter/render.py) to avoid switch logic in `PosterRenderer`.
- [x] Low (A-03, Status: Completed) - Consolidate preset/style-pack loading into a single module (e.g., styles.py) to reduce coupling between CLI and renderer.

## Code quality and readability
- [x] High (CQ-01, Status: Completed) - Replace repeated highway classification logic with a single normalized mapping table in [src/maptoposter/render.py](src/maptoposter/render.py).
- [x] Medium (CQ-02, Status: Completed) - Clean up CLI help text alignment in [src/maptoposter/cli.py](src/maptoposter/cli.py) to avoid inconsistent indenting.
- [x] Low (CQ-03, Status: Completed) - Add docstrings for new helper methods in `PosterRenderer` to keep documentation coverage consistent.

## Correctness, robustness, and edge cases
- [x] High (CLI-01, Status: Completed) - Add guardrails for CLI inputs and theme/preset resolution in [src/maptoposter/cli.py](src/maptoposter/cli.py) to avoid mixed states (preset + all-themes or style-pack + all-themes).
- [x] High (CR-01, Status: Completed) - Validate style-pack JSON keys in `load_style_pack` in [src/maptoposter/render.py](src/maptoposter/render.py) to prevent silent misconfigurations.
- [x] High (CR-02, Status: Completed) - Add safe handling for missing/empty GeoDataFrames in layer building in [src/maptoposter/render.py](src/maptoposter/render.py).
- [x] Medium (CR-03, Status: Completed) - Ensure cache key normalization handles floating point rounding consistently in [src/maptoposter/render.py](src/maptoposter/render.py).
- [x] Medium (CR-04, Status: Completed) - Add explicit handling for invalid `--render-backend` in [src/maptoposter/cli.py](src/maptoposter/cli.py) beyond argparse choices (config validation).

## Security
- [x] Medium (SEC-01, Status: Completed) - Avoid printing raw exception strings for network errors in [src/maptoposter/geo.py](src/maptoposter/geo.py); log details, return sanitized CLI messages.
- [x] Low (SEC-02, Status: Completed) - Validate style-pack paths to prevent directory traversal in [src/maptoposter/cli.py](src/maptoposter/cli.py).

## Performance and scalability
- [x] High (PERF-01, Status: Completed) - Avoid repeatedly calling `ox.graph_to_gdfs` on each run when layer cache is enabled; add cache invalidation and size limits in [src/maptoposter/render.py](src/maptoposter/render.py).
- [x] Medium (PERF-02, Status: Completed) - Use vectorized classification for road classes instead of per-row mapping in [src/maptoposter/render.py](src/maptoposter/render.py).
- [x] Low (PERF-03, Status: Completed) - Limit in-memory cache growth in [src/maptoposter/render.py](src/maptoposter/render.py) with LRU behavior and stats.

## Concurrency and async
- [x] Low (CONC-01, Status: Completed) - Document that global layer cache is not thread-safe and add a lock if multi-threaded use is planned in [src/maptoposter/render.py](src/maptoposter/render.py).

## Logging, monitoring, and observability
- [x] Medium (LOG-01, Status: Completed) - Add consistent log context for city/country/theme in [src/maptoposter/cli.py](src/maptoposter/cli.py) and [src/maptoposter/render.py](src/maptoposter/render.py).
- [x] Low (LOG-02, Status: Completed) - Use structured log messages for cache hits/misses in [src/maptoposter/cache.py](src/maptoposter/cache.py).

## Testing and CI
- [x] High (TEST-01, Status: Completed) - Add tests for `StyleConfig`, presets, and style-pack parsing in [tests/test_render.py](tests/test_render.py) and [tests/test_cli.py](tests/test_cli.py).
- [x] Medium (TEST-03, Status: Completed) - Add snapshot/visual regression testing strategy for render output (PNG-only) documented in [tests/](tests/).
- [x] Low (CI-01, Status: Completed) - Add CI checks to run ruff format and mypy if not already present in repo workflows.

## Dependencies and build
- [x] Medium (DEP-01, Status: Completed) - Document optional render extra in [README.md](README.md) and verify datashader/numba version compatibility with Python 3.11 in [pyproject.toml](pyproject.toml).
- [x] Low (DEP-02, Status: Completed) - Audit dependency minimum versions to avoid overly broad constraints in [pyproject.toml](pyproject.toml).

## Execution Notes
### Phase 1 — Architecture Foundation
- What changed: extracted raster post-processing helpers into [src/maptoposter/postprocess.py](src/maptoposter/postprocess.py), moved style presets/config to [src/maptoposter/styles.py](src/maptoposter/styles.py), introduced backend registry in [src/maptoposter/render.py](src/maptoposter/render.py).
- Why: reduce render module size, centralize style loading, and simplify backend selection.
- Issues resolved: A-01, A-02, A-03.

### Phase 2 — Correctness + Security Hardening
- What changed: validated style-pack keys in [src/maptoposter/styles.py](src/maptoposter/styles.py), added style-pack path checks in [src/maptoposter/cli.py](src/maptoposter/cli.py), added road data guards and cache-key normalization in [src/maptoposter/render.py](src/maptoposter/render.py), sanitized geo error output in [src/maptoposter/geo.py](src/maptoposter/geo.py).
- Why: prevent silent misconfiguration, improve stability for empty data, and avoid leaking raw error details.
- Issues resolved: CR-01, CR-02, CR-03, CR-04, SEC-01, SEC-02.

### Phase 3 — Performance + Concurrency
- What changed: added cache TTL, eviction stats, and a lock around layer cache operations in [src/maptoposter/render.py](src/maptoposter/render.py).
- Why: stabilize cache behavior, prevent unbounded growth, and reduce race risk in multi-threaded scenarios.
- Issues resolved: PERF-01, PERF-03, CONC-01.

### Phase 4 — Logging + Code Quality
- What changed: centralized highway classification mapping and vectorized road class assignment in [src/maptoposter/render.py](src/maptoposter/render.py), aligned CLI help text in [src/maptoposter/cli.py](src/maptoposter/cli.py), added helper docstrings, and added log context plus cache hit/miss logs.
- Why: reduce duplication, improve readability, and provide clearer operational context.
- Issues resolved: CQ-01, CQ-02, CQ-03, PERF-02, LOG-01, LOG-02.

### Phase 5 — Testing + CI
- What changed: added tests for styles and layer building, documented visual regression strategy in [tests/README.md](tests/README.md), and introduced CI workflow in [.github/workflows/ci.yml](.github/workflows/ci.yml).
- Why: ensure new rendering pipeline behavior is verified and automated checks run on PRs.
- Issues resolved: TEST-01, TEST-02, TEST-03, CI-01.

### Phase 6 — Dependencies + Build
- What changed: documented render extra installation in [README.md](README.md) and added a minimum version for `pyarrow` in [pyproject.toml](pyproject.toml).
- Why: clarify optional datashader setup and prevent overly broad dependency ranges.
- Issues resolved: DEP-01, DEP-02.
