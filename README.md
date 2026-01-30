# City Map Poster Generator

Generate beautiful, minimalist map posters for any city in the world.

## Installation

### Using UV (Recommended)

```bash
# Clone the repository
git clone https://github.com/Iwaschkin/maptoposter.git
cd maptoposter

# Install dependencies and run
uv sync
uv run maptoposter --help

# Optional: enable datashader backend for better performance on large datasets
uv sync --extra render
```

### Using pip

```bash
pip install maptoposter
```

### Development Setup

```bash
# Clone and install with dev dependencies
git clone https://github.com/Iwaschkin/maptoposter.git
cd maptoposter
uv sync --all-extras

# Run tests (212 tests)
uv run pytest

# Run pre-commit hooks (includes ruff, mypy, etc.)
uv run pre-commit run --all-files

# Install pre-commit hooks for automatic checks
uv run pre-commit install
```

## Usage

```bash
# Using UV (recommended)
uv run maptoposter --city <city> --country <country> [options]

# Or if installed globally
maptoposter --city <city> --country <country> [options]

# Or using Python module syntax
python -m maptoposter --city <city> --country <country> [options]
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--city` | `-c` | City name | required |
| `--country` | `-C` | Country name | required |
| **OPTIONAL:** `--name` | | Override display name (city display on poster) | |
| **OPTIONAL:** `--country-label` | | Override display country (country display on poster) | |
| **OPTIONAL:** `--theme` | `-t` | Theme name | feature_based |
| **OPTIONAL:** `--preset` | | Style preset (overrides theme) | |
| **OPTIONAL:** `--style-pack` | | JSON style pack file (overrides theme) | |
| **OPTIONAL:** `--distance` | `-d` | Map radius in meters | 12000 |
| **OPTIONAL:** `--list-themes` | | List all available themes | |
| **OPTIONAL:** `--list-presets` | | List all available presets | |
| **OPTIONAL:** `--all-themes` | | Generate posters for all available themes | |
| **OPTIONAL:** `--width` | `-W` | Image width in inches | 12 |
| **OPTIONAL:** `--height` | `-H` | Image height in inches | 16 |
| **OPTIONAL:** `--render-backend` | | Rendering backend (`matplotlib`, `datashader`) | matplotlib |
| **OPTIONAL:** `--batch` | | Text file with city,country pairs for batch processing | |
| **OPTIONAL:** `--workers` | | Number of parallel workers for batch mode | 4 |
| **OPTIONAL:** `--cache-stats` | | Show cache statistics | |
| **OPTIONAL:** `--clear-cache` | | Clear all cached data | |

### Resolution Guide (300 DPI)

Use these values for `-W` and `-H` to target specific resolutions:

| Target | Resolution (px) | Inches (-W / -H) |
|--------|-----------------|------------------|
| **Instagram Post** | 1080 x 1080 | 3.6 x 3.6 |
| **Mobile Wallpaper** | 1080 x 1920 | 3.6 x 6.4 |
| **HD Wallpaper** | 1920 x 1080 | 6.4 x 3.6 |
| **4K Wallpaper** | 3840 x 2160 | 12.8 x 7.2 |
| **A4 Print** | 2480 x 3508 | 8.3 x 11.7 |

### Examples

```bash
# Iconic grid patterns
uv run maptoposter -c "New York" -C "USA" -t noir -d 12000           # Manhattan grid
uv run maptoposter -c "Barcelona" -C "Spain" -t warm_beige -d 8000   # Eixample district

# Waterfront & canals
uv run maptoposter -c "Venice" -C "Italy" -t blueprint -d 4000       # Canal network
uv run maptoposter -c "Amsterdam" -C "Netherlands" -t ocean -d 6000  # Concentric canals
uv run maptoposter -c "Dubai" -C "UAE" -t midnight_blue -d 15000     # Palm & coastline

# Radial patterns
uv run maptoposter -c "Paris" -C "France" -t pastel_dream -d 10000   # Haussmann boulevards
uv run maptoposter -c "Moscow" -C "Russia" -t noir -d 12000          # Ring roads

# Organic old cities
uv run maptoposter -c "Tokyo" -C "Japan" -t japanese_ink -d 15000    # Dense organic streets
uv run maptoposter -c "Marrakech" -C "Morocco" -t terracotta -d 5000 # Medina maze
uv run maptoposter -c "Rome" -C "Italy" -t warm_beige -d 8000        # Ancient layout

# Coastal cities
uv run maptoposter -c "San Francisco" -C "USA" -t sunset -d 10000    # Peninsula grid
uv run maptoposter -c "Sydney" -C "Australia" -t ocean -d 12000      # Harbor city
uv run maptoposter -c "Mumbai" -C "India" -t contrast_zones -d 18000 # Coastal peninsula

# River cities
uv run maptoposter -c "London" -C "UK" -t noir -d 15000              # Thames curves
uv run maptoposter -c "Budapest" -C "Hungary" -t copper_patina -d 8000  # Danube split

# List available themes
uv run maptoposter --list-themes

# Generate posters for every theme
uv run maptoposter -c "Tokyo" -C "Japan" --all-themes

# List available presets
uv run maptoposter --list-presets

# Use a preset (theme + styling bundle)
uv run maptoposter -c "Paris" -C "France" --preset noir -d 12000

# Use a custom style pack
uv run maptoposter -c "Berlin" -C "Germany" --style-pack styles/industrial.json

# Enable datashader backend (optional dependency)
uv run maptoposter -c "Tokyo" -C "Japan" --render-backend datashader -d 18000

# Batch processing: simple format (legacy)
echo "Paris, France" > cities.txt
echo "Tokyo, Japan" >> cities.txt
echo "New York, USA" >> cities.txt
uv run maptoposter --batch cities.txt -t noir -d 10000

# Batch processing: CSV with headers for custom labels
echo "city,country,display_name,country_label" > cities.csv
echo "Paris,France,Paname,République Française" >> cities.csv
echo "NYC,USA,New York City,United States" >> cities.csv
uv run maptoposter --batch cities.csv -t noir

# Batch with multiple workers (parallel processing)
uv run maptoposter --batch cities.txt --workers 8 -t noir

# Cache management
uv run maptoposter --cache-stats          # View cache statistics
uv run maptoposter --clear-cache          # Clear all cached data
```

### Distance Guide

| Distance | Best for |
|----------|----------|
| 4000-6000m | Small/dense cities (Venice, Amsterdam center) |
| 8000-12000m | Medium cities, focused downtown (Paris, Barcelona) |
| 15000-20000m | Large metros, full city view (Tokyo, Mumbai) |

## Themes

20 built-in themes available in `src/maptoposter/data/themes/`:

| Theme | Style |
|-------|-------|
| `feature_based` | Classic black & white with road hierarchy |
| `gradient_roads` | Smooth gradient shading |
| `contrast_zones` | High contrast urban density |
| `noir` | Pure black background, white roads |
| `midnight_blue` | Navy background with gold roads |
| `blueprint` | Architectural blueprint aesthetic |
| `neon_cyberpunk` | Dark with electric pink/cyan |
| `warm_beige` | Vintage sepia tones |
| `pastel_dream` | Soft muted pastels |
| `japanese_ink` | Minimalist ink wash style |
| `forest` | Deep greens and sage |
| `ocean` | Blues and teals for coastal cities |
| `terracotta` | Mediterranean warmth |
| `sunset` | Warm oranges and pinks |
| `autumn` | Seasonal burnt oranges and reds |
| `copper_patina` | Oxidized copper aesthetic |
| `monochrome_blue` | Single blue color family |
| `british_rail` | British Rail corporate identity inspired |
| `british_rail_refined` | Refined British Rail aesthetic |
| `lcars` | Star Trek LCARS interface style |

## Presets

Presets bundle a theme with style defaults (road casing, glow, typography, post-processing effects).

| Preset | Theme | Description |
|--------|-------|-------------|
| `noir` | `noir` | Classic film noir aesthetic with subtle grain and vignette |
| `blueprint` | `blueprint` | Technical drawing style with no casing or effects |
| `neon_cyberpunk` | `neon_cyberpunk` | Vibrant neon glow with enhanced color saturation |
| `japanese_ink` | `japanese_ink` | Calligraphic style with wide tracking and soft vignette |
| `warm_beige` | `warm_beige` | Vintage warmth with film grain and subtle color grading |
| `vintage` | `warm_beige` | Classic vintage film look with grain and vignette |
| `film_noir` | `noir` | High contrast noir with stronger effects |

## Output

Posters are saved to `posters/` directory with format:
```
{city}_{theme}_{YYYYMMDD_HHMMSS}.png
```

Raster post-processing effects (grain, vignette, paper texture, color grading)
are only applied to PNG output. SVG/PDF output remains vector-clean.

## Adding Custom Themes

Create a JSON file in `src/maptoposter/data/themes/` directory:

```json
{
  "name": "My Theme",
  "description": "Description of the theme",
  "bg": "#FFFFFF",
  "text": "#000000",
  "gradient_color": "#FFFFFF",
  "water": "#C0C0C0",
  "parks": "#F0F0F0",
  "railway": "#505050",
  "road_motorway": "#0A0A0A",
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_path": "#808080",
  "road_default": "#3A3A3A"
}
```

All color values must be hex codes. The `railway` and `road_path` keys are required in addition to the standard road types.

## Style Packs

Style packs are JSON files that map directly to renderer styling fields.
They can optionally include a `theme_name` to select the theme.

```json
{
  "theme_name": "noir",
  "road_glow_strength": 0.4,
  "typography_tracking": 1,
  "grain_strength": 0.15,
  "vignette_strength": 0.2,
  "color_grading_strength": 0.1
}
```

See [docs/style-pack.schema.json](docs/style-pack.schema.json) for the full schema reference.

Example style packs are available in [examples/style-packs/](examples/style-packs/).

## Project Structure

```
maptoposter/
├── src/
│   └── maptoposter/
│       ├── __init__.py       # Package version
│       ├── __main__.py       # python -m entry point
│       ├── cache.py          # Caching utilities
│       ├── cli.py            # Command-line interface
│       ├── config.py         # Configuration & themes
│       ├── fonts.py          # Font management
│       ├── geo.py            # Geographic data fetching
│       ├── render.py         # Map rendering
│       └── data/
│           ├── themes/       # Theme JSON files
│           └── fonts/        # Roboto font files
├── tests/                    # Unit tests
├── posters/                  # Generated posters
├── pyproject.toml            # Project configuration
└── README.md
```

## Hacker's Guide

Quick reference for contributors who want to extend or modify the package.

### Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   CLI (cli.py)  │────▶│  Geocoding   │────▶│  Data Fetching  │
│   (argparse)    │     │  (geo.py)    │     │    (geo.py)     │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                     │
                        ┌──────────────┐             ▼
                        │    Output    │◀────┌─────────────────┐
                        │  (matplotlib)│     │ PosterRenderer  │
                        └──────────────┘     │  (render.py)    │
                                             └─────────────────┘
```

### Module Reference

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `cli.py` | Command-line interface | `main()`, `cli()`, `create_parser()`, `_parse_batch_file()` |
| `config.py` | Configuration & themes | `PosterConfig`, `load_theme()`, `get_available_themes()` |
| `geo.py` | Geographic data | `get_coordinates()`, `fetch_graph()`, `fetch_features()`, custom exceptions |
| `render.py` | Map rendering | `PosterRenderer`, `LayerCache`, `create_poster()` |
| `styles.py` | Style presets and packs | `StyleConfig`, `get_style_preset()`, `load_style_pack()` |
| `postprocess.py` | Raster effects | `apply_raster_effects()`, `PostProcessResult` |
| `cache.py` | Data caching | `cache_get()`, `cache_set()`, `cache_clear()` |
| `fonts.py` | Font management | `FontSet`, `load_fonts()` |
| `render_constants.py` | Typography & sizing | Road widths, z-order, text positioning constants |

### Rendering Layers (z-order)

```
z=100 Text labels (city, country, coords)
z=10  Gradient fades (top & bottom)
z=8   Railways (rail lines)
z=4   Roads - core layers (by type)
z=3.5 Paths (footpaths, cycleways - dotted lines)
z=3   Roads - casing layers (below core)
z=2.5 Parks (green polygons)
z=2   Waterways (rivers, streams)
z=1   Water bodies (lakes, oceans - blue polygons)
z=0   Background color
```

### Error Handling

The package uses custom exceptions for better error handling:

- `GeoError`: Base exception for geographic operations
- `GeocodingError`: Raised when city/country geocoding fails
- `OSMFetchError`: Raised when OpenStreetMap data fetching fails

All exceptions include descriptive error messages to help diagnose issues.

### Adding New Features

**New map layer (e.g., buildings):**

In `render.py`, modify `PosterRenderer._build_layers()`:

```python
# After parks fetch:
try:
    buildings = fetch_features(
        point, compensated_dist,
        tags={'building': True},
        name='buildings',
    )
except OSMFetchError as e:
    logger.warning(f"Failed to fetch buildings: {e}")
    buildings = None

# Add with appropriate z-order:
if buildings is not None and not buildings.empty:
    building_polys = buildings[buildings.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    if not building_polys.empty:
        layers.append(RenderLayer(
            name="buildings",
            zorder=5,  # Above roads, below text
            gdf=building_polys,
            style={"facecolor": self.theme.get("building", "#CCCCCC"),
                   "edgecolor": "none", "alpha": 0.3},
        ))
```

**New theme property:**
1. Add to all theme JSON files: `"building": "#CCCCCC"`
2. Add to `REQUIRED_THEME_KEYS` in `config.py` if mandatory
3. Add fallback in `config.py` `_get_default_theme()`
4. Use in code: `self.theme["building"]` or `self.theme.get("building", "#default")`

### Development Commands

```bash
# Run all pre-commit hooks (recommended)
uv run pre-commit run --all-files

# Run tests (212 tests)
uv run pytest

# Run tests with coverage
uv run pytest --cov=maptoposter --cov-report=html

# Format code (done automatically by pre-commit)
uv run ruff format src/

# Lint and fix
uv run ruff check src/ --fix

# Type check (strict mode)
uv run mypy src/

# Build package
uv build

# Install pre-commit hooks for automatic checking
uv run pre-commit install
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MAPTOPOSTER_CACHE_DIR` | Directory for cached OSM data | `.cache` |

## License

MIT
