# MapToPoster - AI Coding Instructions

## Project Overview
A Python CLI tool that generates minimalist map posters for any city using OpenStreetMap data. Package-first layout under `src/maptoposter/` with JSON-based theming and a CLI entry point.

## Architecture

```
CLI (argparse) → Geocoding (Nominatim) → Data Fetch (OSMnx) → Render (matplotlib) → PNG/SVG/PDF
```

**Key data flow:**
1. City/country → `get_coordinates()` → lat/lon (cached)
2. lat/lon → `fetch_graph()` / `fetch_features()` → street network + water/parks (cached)
3. Graph → `ox.project_graph()` → projected coordinates for accurate rendering
4. Layers rendered in z-order: WATER(1) → WATERWAYS(2) → PARKS(3) → PATHS(3.5) → ROADS(4) → RAILWAYS(8) → GRADIENT(10) → TEXT(100)

## Repo Map

- `src/maptoposter/cli.py`: CLI parsing and orchestration (entry point `maptoposter`).
- `src/maptoposter/geo.py`: Geocoding and OSM feature/graph fetch (rate-limited + cached).
- `src/maptoposter/render.py`: PosterRenderer class, layer system, matplotlib plotting.
- `src/maptoposter/config.py`: Paths, theme loading/validation, and output filename convention.
- `src/maptoposter/styles.py`: StyleConfig, presets, and style pack loading.
- `src/maptoposter/postprocess.py`: Raster effects (grain, vignette, color grading).
- `src/maptoposter/cache.py`: Safe cache in `.cache/` using JSON/GraphML/GeoParquet.
- `src/maptoposter/render_constants.py`: Typography and road width constants.
- `src/maptoposter/fonts.py`: Font loading utilities.
- `src/maptoposter/data/themes/` + `src/maptoposter/data/fonts/`: Packaged assets (source of truth).

## Critical Patterns

### Caching System
All OSM data is cached to `.cache/` (customizable via `MAPTOPOSTER_CACHE_DIR` env var). Cache uses MD5 hash of tag JSON for keys:
```python
cached = cache_get(f"graph_{lat}_{lon}_{dist}")
if cached is None:
    data = ox.graph_from_point(...)
    cache_set(key, data)
```
**Note:** Only `.cache/` is the active cache. Any `cache/` directory at project root is legacy and can be deleted.

### Theme Structure
Themes are JSON files in `src/maptoposter/data/themes/` with required keys:
```json
{
  "name": "Display Name",
  "bg": "#FFFFFF",           // background
  "text": "#000000",         // typography
  "gradient_color": "#FFFFFF", // fade overlays
  "water": "#C0C0C0",
  "parks": "#F0F0F0",
  "railway": "#505050",       // railway lines
  "road_motorway": "#0A0A0A",  // thickest roads
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_path": "#808080",      // footpaths, bridleways, cycleways
  "road_default": "#3A3A3A"
}
```
Access via `PosterConfig.theme` after `load_theme()`.

### Road Hierarchy
OSM highway types map to visual weight (constants in `render_constants.py`):
- `motorway*` → ROAD_WIDTH_MOTORWAY (1.2, thickest)
- `trunk/primary*` → ROAD_WIDTH_PRIMARY (1.0)
- `secondary*` → ROAD_WIDTH_SECONDARY (0.8)
- `tertiary*` → ROAD_WIDTH_TERTIARY (0.6)
- `residential/living_street` → ROAD_WIDTH_RESIDENTIAL (0.4)
- `footway/path/bridleway/cycleway` → ROAD_WIDTH_PATH (0.2, thinnest, dotted lines, rendered below roads)

## Adding Features

### New Map Layer (e.g., railways)
1. Fetch in `_build_layers()` (in `render.py`):
   ```python
   railways = fetch_features(point, dist, tags={'railway': 'rail'}, name='railways')
   ```
2. Add as RenderLayer with appropriate z-order:
   ```python
   layers.append(RenderLayer(name="railways", zorder=ZOrder.RAILWAYS, gdf=railways, style={...}))
   ```
3. Add `"railway": "#COLOR"` to all theme JSON files in `src/maptoposter/data/themes/`
4. Add key to `_get_default_theme()` fallback in `config.py`

### New Theme Property
1. Add key to theme JSON files
2. Add fallback in `_get_default_theme()`
3. Add to `REQUIRED_THEME_KEYS` if mandatory
4. Use as `config.theme['property_name']`

## Development Commands (uv only)

```bash
# Install dependencies (uv only)
uv sync --all-extras

# Generate single poster
uv run maptoposter -c "Tokyo" -C "Japan" -t noir -d 15000

# Override display name
uv run maptoposter -c "NYC" -C "USA" --name "New York City"

# Generate all themes for a city
uv run maptoposter -c "Paris" -C "France" --all-themes

# Use style preset
uv run maptoposter -c "London" -C "UK" --preset neon_cyberpunk

# Batch processing
uv run maptoposter --batch cities.txt --workers 4

# Cache management
uv run maptoposter --cache-stats
uv run maptoposter --clear-cache

# List available themes/presets
uv run maptoposter --list-themes
uv run maptoposter --list-presets

# Quick preview (lower DPI)
uv run maptoposter -c "Venice" -C "Italy" -d 4000 -W 6 -H 8

# Run tests
uv run pytest
```

## Important Constraints

- **Rate limiting**: Nominatim requires 1s delay between requests (already implemented)
- **Memory**: Large `dist` values (>20km) cause slow downloads; use 4000-20000m range
- **Projection**: Always use `ox.project_graph()` before rendering for accurate aspect ratios
- **Geometry filtering**: Filter GeoDataFrames to `Polygon/MultiPolygon` before plotting to avoid point artifacts:
  ```python
  water_polys = water[water.geometry.type.isin(['Polygon', 'MultiPolygon'])]
  ```
- **Park-water overlap**: Water polygons are subtracted from parks to preserve water features

## Package Management

- **Use uv exclusively** for installs, running scripts, and dependency updates in this repo.
- Do not use `pip`, `pipenv`, `poetry`, or `conda` commands for this project.

## File Conventions

- **Output naming**: `{city}_{theme}_{YYYYMMDD_HHMMSS}.{format}` in `posters/`
- **Fonts**: Roboto family in `src/maptoposter/data/fonts/` (Bold, Regular, Light)
- **Typography positioning**: Uses normalized axes coordinates (0-1) via `transform=ax.transAxes`
