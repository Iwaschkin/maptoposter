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
4. Layers rendered in z-order: background → water(1) → parks(2) → roads(3) → gradients(10) → text(11)

## Repo Map

- `src/maptoposter/cli.py`: CLI parsing and orchestration (entry point `maptoposter`).
- `src/maptoposter/geo.py`: Geocoding and OSM feature/graph fetch (rate-limited + cached).
- `src/maptoposter/render.py`: Plotting and layout (matplotlib), typography, gradients.
- `src/maptoposter/config.py`: Paths, theme loading, and output filename convention.
- `src/maptoposter/cache.py`: Pickle cache in `.cache/`.
- `src/maptoposter/data/themes/` + `src/maptoposter/data/fonts/`: Packaged assets (source of truth).

## Critical Patterns

### Caching System
All OSM data is cached to `.cache/` using pickle. Cache keys follow pattern `{type}_{lat}_{lon}_{dist}`:
```python
cached = cache_get(f"graph_{lat}_{lon}_{dist}")
if cached is None:
    data = ox.graph_from_point(...)
    cache_set(key, data)
```

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
  "road_motorway": "#0A0A0A",  // thickest roads
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_default": "#3A3A3A"
}
```
Access via `PosterConfig.theme` after `load_theme()`.

### Road Hierarchy
OSM highway types map to visual weight in `get_edge_colors_by_type()` and `get_edge_widths_by_type()`:
- `motorway*` → width 1.2 (thickest)
- `trunk/primary*` → width 1.0
- `secondary*` → width 0.8
- `tertiary*` → width 0.6
- `residential/living_street` → width 0.4 (thinnest)

## Adding Features

### New Map Layer (e.g., railways)
1. Fetch in `create_poster()` (in `render.py`) after parks:
   ```python
   railways = fetch_features(point, dist, tags={'railway': 'rail'}, name='railways')
   ```
2. Plot before roads (z-order 2.5):
   ```python
   if railways is not None and not railways.empty:
       railways_polys = railways[railways.geometry.type.isin(['LineString', 'MultiLineString'])]
      railways_polys.plot(ax=ax, color=config.theme['railway'], linewidth=0.5, zorder=2.5)
   ```
3. Add `"railway": "#COLOR"` to all theme JSON files in `src/maptoposter/data/themes/`

### New Theme Property
1. Add key to theme JSON
2. Add fallback in `load_theme()` default dict
3. Use as `config.theme['property_name']`

## Development Commands (uv only)

```bash
# Install dependencies (uv only)
uv sync --all-extras

# Generate single poster
uv run maptoposter -c "Tokyo" -C "Japan" -t noir -d 15000

# Generate all themes for a city
uv run maptoposter -c "Paris" -C "France" --all-themes

# List available themes
uv run maptoposter --list-themes

# Quick preview (lower DPI)
uv run maptoposter -c "Venice" -C "Italy" -d 4000 -W 6 -H 8
```

## Important Constraints

- **Rate limiting**: Nominatim requires 1s delay between requests (already implemented)
- **Memory**: Large `dist` values (>20km) cause slow downloads; use 4000-20000m range
- **Projection**: Always use `ox.project_graph()` before rendering for accurate aspect ratios
- **Geometry filtering**: Filter GeoDataFrames to `Polygon/MultiPolygon` before plotting to avoid point artifacts:
  ```python
  water_polys = water[water.geometry.type.isin(['Polygon', 'MultiPolygon'])]
  ```

## Package Management

- **Use uv exclusively** for installs, running scripts, and dependency updates in this repo.
- Do not use `pip`, `pipenv`, `poetry`, or `conda` commands for this project.

## File Conventions

- **Output naming**: `{city}_{theme}_{YYYYMMDD_HHMMSS}.{format}` in `posters/`
- **Fonts**: Roboto family in `src/maptoposter/data/fonts/` (Bold, Regular, Light)
- **Typography positioning**: Uses normalized axes coordinates (0-1) via `transform=ax.transAxes`
