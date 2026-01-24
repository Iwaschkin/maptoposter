# City Map Poster Generator

Generate beautiful, minimalist map posters for any city in the world.

<img src="posters/singapore_neon_cyberpunk_20260118_153328.png" width="250">
<img src="posters/dubai_midnight_blue_20260118_140807.png" width="250">

## Examples


| Country      | City           | Theme           | Poster |
|:------------:|:--------------:|:---------------:|:------:|
| USA          | San Francisco  | sunset          | <img src="posters/san_francisco_sunset_20260118_144726.png" width="250"> |
| Spain        | Barcelona      | warm_beige      | <img src="posters/barcelona_warm_beige_20260118_140048.png" width="250"> |
| Italy        | Venice         | blueprint       | <img src="posters/venice_blueprint_20260118_140505.png" width="250"> |
| Japan        | Tokyo          | japanese_ink    | <img src="posters/tokyo_japanese_ink_20260118_142446.png" width="250"> |
| India        | Mumbai         | contrast_zones  | <img src="posters/mumbai_contrast_zones_20260118_145843.png" width="250"> |
| Morocco      | Marrakech      | terracotta      | <img src="posters/marrakech_terracotta_20260118_143253.png" width="250"> |
| Singapore    | Singapore      | neon_cyberpunk  | <img src="posters/singapore_neon_cyberpunk_20260118_153328.png" width="250"> |
| Australia    | Melbourne      | forest          | <img src="posters/melbourne_forest_20260118_153446.png" width="250"> |
| UAE          | Dubai          | midnight_blue   | <img src="posters/dubai_midnight_blue_20260118_140807.png" width="250"> |

## Installation

### Using UV (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/maptoposter.git
cd maptoposter

# Install dependencies and run
uv sync
uv run maptoposter --help
```

### Using pip

```bash
pip install maptoposter
```

### Development Setup

```bash
# Clone and install with dev dependencies
git clone https://github.com/your-username/maptoposter.git
cd maptoposter
uv sync --all-extras

# Run tests
uv run pytest

# Run linter
uv run ruff check src/

# Run type checker
uv run mypy src/
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
| **OPTIONAL:** `--distance` | `-d` | Map radius in meters | 29000 |
| **OPTIONAL:** `--list-themes` | | List all available themes | |
| **OPTIONAL:** `--all-themes` | | Generate posters for all available themes | |
| **OPTIONAL:** `--width` | `-W` | Image width in inches | 12 |
| **OPTIONAL:** `--height` | `-H` | Image height in inches | 16 |

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
```

### Distance Guide

| Distance | Best for |
|----------|----------|
| 4000-6000m | Small/dense cities (Venice, Amsterdam center) |
| 8000-12000m | Medium cities, focused downtown (Paris, Barcelona) |
| 15000-20000m | Large metros, full city view (Tokyo, Mumbai) |

## Themes

17 themes available in `themes/` directory:

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

## Output

Posters are saved to `posters/` directory with format:
```
{city}_{theme}_{YYYYMMDD_HHMMSS}.png
```

## Adding Custom Themes

Create a JSON file in `themes/` directory:

```json
{
  "name": "My Theme",
  "description": "Description of the theme",
  "bg": "#FFFFFF",
  "text": "#000000",
  "gradient_color": "#FFFFFF",
  "water": "#C0C0C0",
  "parks": "#F0F0F0",
  "road_motorway": "#0A0A0A",
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_default": "#3A3A3A"
}
```

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
| `cli.py` | Command-line interface | `main()`, `cli()`, `create_parser()` |
| `config.py` | Configuration & themes | `PosterConfig`, `load_theme()`, `get_available_themes()` |
| `geo.py` | Geographic data | `get_coordinates()`, `fetch_graph()`, `fetch_features()` |
| `render.py` | Map rendering | `PosterRenderer`, `create_poster()` |
| `cache.py` | Data caching | `cache_get()`, `cache_set()` |
| `fonts.py` | Font management | `FontSet`, `load_fonts()` |

### Rendering Layers (z-order)

```
z=11  Text labels (city, country, coords)
z=10  Gradient fades (top & bottom)
z=3   Roads (via ox.plot_graph)
z=2   Parks (green polygons)
z=1   Water (blue polygons)
z=0   Background color
```

### Adding New Features

**New map layer (e.g., railways):**

In `render.py`, modify the `PosterRenderer.render()` method:

```python
# After parks fetch:
railways = fetch_features(
    point, compensated_dist,
    tags={'railway': 'rail'},
    name='railways',
)

# Plot before roads:
if railways is not None and not railways.empty:
    railways_lines = railways[railways.geometry.type.isin(['LineString', 'MultiLineString'])]
    if not railways_lines.empty:
        railways_lines.plot(ax=ax, color=self.theme['railway'], linewidth=0.5, zorder=2.5)
```

**New theme property:**
1. Add to theme JSON: `"railway": "#FF0000"`
2. Use in code: `self.theme['railway']`
3. Add fallback in `config.py` `_get_default_theme()`

### Development Commands

```bash
# Run tests with coverage
uv run pytest --cov=maptoposter

# Format code
uv run ruff format src/

# Lint and fix
uv run ruff check src/ --fix

# Type check
uv run mypy src/

# Build package
uv build
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MAPTOPOSTER_CACHE_DIR` | Directory for cached OSM data | `.cache` |

## License

MIT
