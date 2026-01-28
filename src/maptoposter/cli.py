"""Command-line interface for MapToPoster."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, NoReturn

from .config import (
    PosterConfig,
    generate_output_filename,
    get_available_themes,
    load_theme,
)
from .geo import get_coordinates
from .render import PosterRenderer
from .styles import (
    StyleConfig,
    get_available_presets,
    get_style_preset,
    load_style_pack,
)


__all__ = ["cli", "main"]

logger = logging.getLogger(__name__)


def _print_examples() -> None:
    """Print usage examples."""
    print(
        """
City Map Poster Generator
=========================

Usage:
  maptoposter --city <city> --country <country> [options]

Examples:
  # Iconic grid patterns
  maptoposter -c "New York" -C "USA" -t noir -d 12000           # Manhattan grid
  maptoposter -c "Barcelona" -C "Spain" -t warm_beige -d 8000   # Eixample district grid

  # Waterfront & canals
  maptoposter -c "Venice" -C "Italy" -t blueprint -d 4000       # Canal network
  maptoposter -c "Amsterdam" -C "Netherlands" -t ocean -d 6000  # Concentric canals
  maptoposter -c "Dubai" -C "UAE" -t midnight_blue -d 15000     # Palm & coastline

  # Radial patterns
  maptoposter -c "Paris" -C "France" -t pastel_dream -d 10000   # Haussmann boulevards
  maptoposter -c "Moscow" -C "Russia" -t noir -d 12000          # Ring roads

  # Organic old cities
  maptoposter -c "Tokyo" -C "Japan" -t japanese_ink -d 15000    # Dense organic streets
  maptoposter -c "Marrakech" -C "Morocco" -t terracotta -d 5000 # Medina maze
  maptoposter -c "Rome" -C "Italy" -t warm_beige -d 8000        # Ancient street layout

  # Coastal cities
  maptoposter -c "San Francisco" -C "USA" -t sunset -d 10000    # Peninsula grid
  maptoposter -c "Sydney" -C "Australia" -t ocean -d 12000      # Harbor city
  maptoposter -c "Mumbai" -C "India" -t contrast_zones -d 18000 # Coastal peninsula

  # River cities
  maptoposter -c "London" -C "UK" -t noir -d 15000              # Thames curves
  maptoposter -c "Budapest" -C "Hungary" -t copper_patina -d 8000  # Danube split

  # List themes
  maptoposter --list-themes

Options:
  --city, -c        City name (required)
  --country, -C     Country name (required)
  --country-label   Override country text displayed on poster
  --theme, -t       Theme name (default: feature_based)
    --preset          Style preset (overrides theme)
    --style-pack      JSON style pack file (overrides theme)
    --render-backend  Rendering backend (matplotlib, datashader)
  --all-themes      Generate posters for all themes
  --distance, -d    Map radius in meters (default: 29000)
  --list-themes     List all available themes
    --list-presets    List all available presets

Distance guide:
  4000-6000m   Small/dense cities (Venice, Amsterdam old center)
  8000-12000m  Medium cities, focused downtown (Paris, Barcelona)
  15000-20000m Large metros, full city view (Tokyo, Mumbai)

Available themes can be found in the 'themes/' directory.
Generated posters are saved to 'posters/' directory.
"""
    )


def _list_themes() -> None:
    """List all available themes with descriptions."""
    import json

    from .config import get_themes_dir

    available_themes = get_available_themes()
    if not available_themes:
        print("No themes found in 'themes/' directory.")
        return

    themes_dir = get_themes_dir()

    print("\nAvailable Themes:")
    print("-" * 60)
    for theme_name in available_themes:
        theme_path = themes_dir / f"{theme_name}.json"
        try:
            with theme_path.open("r", encoding="utf-8") as f:
                theme_data = json.load(f)
                display_name = theme_data.get("name", theme_name)
                description = theme_data.get("description", "")
        except Exception:
            display_name = theme_name
            description = ""

        print(f"  {theme_name}")
        print(f"    {display_name}")
        if description:
            print(f"    {description}")
        print()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="maptoposter",
        description="Generate beautiful map posters for any city",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  maptoposter --city "New York" --country "USA"
  maptoposter --city Tokyo --country Japan --theme midnight_blue
  maptoposter --city Paris --country France --theme noir --distance 15000
  maptoposter --list-themes
        """,
    )

    parser.add_argument(
        "--city",
        "-c",
        type=str,
        help="City name",
    )
    parser.add_argument(
        "--country",
        "-C",
        type=str,
        help="Country name",
    )
    parser.add_argument(
        "--country-label",
        dest="country_label",
        type=str,
        help="Override country text displayed on poster",
    )
    parser.add_argument(
        "--theme",
        "-t",
        type=str,
        default="feature_based",
        help="Theme name (default: feature_based)",
    )
    parser.add_argument(
        "--preset",
        type=str,
        help="Style preset (overrides theme)",
    )
    parser.add_argument(
        "--style-pack",
        type=str,
        help="JSON style pack file (overrides theme)",
    )
    parser.add_argument(
        "--render-backend",
        type=str,
        default="matplotlib",
        choices=["matplotlib", "datashader"],
        help="Rendering backend (default: matplotlib)",
    )
    parser.add_argument(
        "--all-themes",
        dest="all_themes",
        action="store_true",
        help="Generate posters for all themes",
    )
    parser.add_argument(
        "--distance",
        "-d",
        type=int,
        default=29000,
        help="Map radius in meters (default: 29000)",
    )
    parser.add_argument(
        "--width",
        "-W",
        type=float,
        default=12.0,
        help="Image width in inches (default: 12)",
    )
    parser.add_argument(
        "--height",
        "-H",
        type=float,
        default=16.0,
        help="Image height in inches (default: 16)",
    )
    parser.add_argument(
        "--list-themes",
        action="store_true",
        help="List all available themes",
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List all available presets",
    )
    parser.add_argument(
        "--cache-stats",
        action="store_true",
        help="Show cache statistics and exit",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear all cached data and exit",
    )
    parser.add_argument(
        "--batch",
        type=str,
        metavar="FILE",
        help="Generate posters for multiple cities from a text file (one city,country per line)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers for batch processing (default: 4)",
    )
    parser.add_argument(
        "--format",
        "-f",
        default="png",
        choices=["png", "svg", "pdf"],
        help="Output format for the poster (default: png)",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show version and exit",
    )

    return parser


def _parse_batch_file(batch_file: str) -> list[tuple[str, str]]:
    """Parse a batch file containing city,country pairs.

    Args:
        batch_file: Path to the batch file.

    Returns:
        List of (city, country) tuples.
    """
    cities: list[tuple[str, str]] = []
    path = Path(batch_file).expanduser()

    with path.open("r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, 1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split(",")
            if len(parts) != 2:
                logger.warning("Skipping invalid line %d: %s", line_num, stripped)
                continue
            city = parts[0].strip()
            country = parts[1].strip()
            if city and country:
                cities.append((city, country))

    return cities


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
    """Generate a poster for a single city.

    Args:
        city: City name.
        country: Country name.
        theme_name: Theme to use.
        output_format: Output format (png, svg, pdf).
        distance: Map radius in meters.
        width: Image width in inches.
        height: Image height in inches.
        render_backend: Rendering backend.
        style_config: Optional style configuration.

    Returns:
        Tuple of (city_name, success, error_message).
    """
    try:
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
            theme=theme,
            style_config=style_config,
            render_backend=render_backend,
        )

        renderer = PosterRenderer(config)
        renderer.render(coords, output_file)
        return (city, True, "")
    except Exception as e:
        return (city, False, str(e))


def _process_batch(parsed: argparse.Namespace) -> int:
    """Process batch generation of multiple cities.

    Args:
        parsed: Parsed command line arguments.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    batch_file = parsed.batch
    path = Path(batch_file).expanduser()

    if not path.is_file():
        print(f"Error: Batch file '{batch_file}' not found.")
        return 1

    cities = _parse_batch_file(batch_file)
    if not cities:
        print("Error: No valid cities found in batch file.")
        return 1

    available_themes = get_available_themes()
    theme_name = parsed.theme
    if theme_name not in available_themes:
        print(f"Error: Theme '{theme_name}' not found.")
        return 1

    # Create style config with caching enabled for batch efficiency
    style_config = StyleConfig(enable_layer_cache=True)

    print("=" * 50)
    print("Batch City Map Poster Generator")
    print("=" * 50)
    print(f"Cities: {len(cities)}")
    print(f"Theme: {theme_name}")
    print(f"Workers: {parsed.workers}")
    print("=" * 50)

    success_count = 0
    failure_count = 0
    futures_to_city: dict[Any, str] = {}

    with ThreadPoolExecutor(max_workers=parsed.workers) as executor:
        for city, country in cities:
            future = executor.submit(
                _generate_single_city,
                city,
                country,
                theme_name,
                parsed.format,
                parsed.distance,
                parsed.width,
                parsed.height,
                parsed.render_backend,
                style_config,
            )
            futures_to_city[future] = city

        for future in as_completed(futures_to_city):
            city_name, success, error = future.result()
            if success:
                print(f"  ✓ {city_name}")
                success_count += 1
            else:
                print(f"  ✗ {city_name}: {error}")
                failure_count += 1

    print("\n" + "=" * 50)
    print(f"Batch complete: {success_count} succeeded, {failure_count} failed")
    print("=" * 50)

    return 0 if failure_count == 0 else 1


def _handle_info_commands(parsed: argparse.Namespace) -> int | None:
    """Handle informational commands that exit early.

    Returns:
        Exit code if handled, None if not handled.
    """
    if parsed.version:
        from . import __version__

        print(f"maptoposter {__version__}")
        return 0

    if parsed.list_themes:
        _list_themes()
        return 0

    if parsed.list_presets:
        from .styles import get_preset_description

        presets = get_available_presets()
        print("\nAvailable Presets:")
        print("-" * 60)
        for preset in presets:
            description = get_preset_description(preset)
            print(f"  {preset}")
            if description:
                print(f"    {description}")
        return 0

    if parsed.cache_stats:
        from .cache import get_cache_stats

        stats = get_cache_stats()
        print("\nCache Statistics:")
        print("-" * 60)
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total size: {stats['total_size_mb']} MB")
        print("\n  By type:")
        for type_name, type_stats in stats["by_type"].items():
            print(f"    {type_name}: {type_stats['files']} files, {type_stats['size_mb']} MB")
        return 0

    if parsed.clear_cache:
        from .cache import clear_cache

        deleted = clear_cache()
        print(f"Cleared {deleted} cache files.")
        return 0

    return None


def _validate_style_options(
    parsed: argparse.Namespace,
) -> tuple[StyleConfig | None, str] | int:
    """Validate and resolve style options.

    Returns:
        Tuple of (style_config, theme_name) on success, or int exit code on error.
    """
    if parsed.preset and parsed.all_themes:
        print("Error: --preset cannot be combined with --all-themes.")
        return 1
    if parsed.style_pack and parsed.all_themes:
        print("Error: --style-pack cannot be combined with --all-themes.")
        return 1
    if parsed.preset and parsed.style_pack:
        print("Error: --preset cannot be combined with --style-pack.")
        return 1

    preset_style: StyleConfig | None = None
    theme_name = parsed.theme

    if parsed.preset:
        available_presets = get_available_presets()
        if parsed.preset not in available_presets:
            print(f"Error: Preset '{parsed.preset}' not found.")
            print(f"Available presets: {', '.join(available_presets)}")
            return 1
        preset_style = get_style_preset(parsed.preset)
        if preset_style.theme_name:
            theme_name = preset_style.theme_name

    if parsed.style_pack:
        style_pack_path = Path(parsed.style_pack).expanduser()
        if style_pack_path.suffix.lower() != ".json":
            print("Error: Style pack must be a JSON file.")
            return 1
        if not style_pack_path.is_file():
            print("Error: Style pack file not found.")
            return 1
        try:
            preset_style = load_style_pack(str(style_pack_path))
        except (OSError, ValueError) as exc:
            print(f"Error: Failed to load style pack: {exc}")
            return 1
        if preset_style.theme_name:
            theme_name = preset_style.theme_name

    return (preset_style, theme_name)


def cli(args: list[str] | None = None) -> int:
    """Run the CLI with the given arguments.

    Args:
        args: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    # Configure logging for CLI usage
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    parser = create_parser()
    parsed = parser.parse_args(args)

    # If no arguments provided, show examples
    # Check both sys.argv (command line) and explicit empty args list (tests)
    if (len(sys.argv) == 1 and args is None) or args == []:
        _print_examples()
        return 0

    # Handle informational commands
    info_result = _handle_info_commands(parsed)
    if info_result is not None:
        return info_result

    # Batch processing
    if parsed.batch:
        return _process_batch(parsed)

    # Validate required arguments
    if not parsed.city or not parsed.country:
        print("Error: --city and --country are required.\n")
        _print_examples()
        return 1

    available_themes = get_available_themes()
    if not available_themes:
        print("No themes found in 'themes/' directory.")
        return 1

    # Validate style options
    style_result = _validate_style_options(parsed)
    if isinstance(style_result, int):
        return style_result
    preset_style, theme_name = style_result

    if parsed.all_themes:
        themes_to_generate = available_themes
    else:
        if theme_name not in available_themes:
            print(f"Error: Theme '{theme_name}' not found.")
            print(f"Available themes: {', '.join(available_themes)}")
            return 1
        themes_to_generate = [theme_name]

    print("=" * 50)
    print("City Map Poster Generator")
    print("=" * 50)

    if parsed.all_themes and preset_style is None:
        preset_style = StyleConfig(enable_layer_cache=True)

    try:
        coords = get_coordinates(parsed.city, parsed.country)
        logger.info(
            "Starting render for %s, %s with format %s and backend %s",
            parsed.city,
            parsed.country,
            parsed.format,
            parsed.render_backend,
        )

        for current_theme in themes_to_generate:
            logger.info("Rendering theme %s", current_theme)
            theme = load_theme(current_theme)
            output_file = generate_output_filename(
                parsed.city,
                current_theme,
                parsed.format,
            )

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

            renderer = PosterRenderer(config)
            renderer.render(coords, output_file)

        print("\n" + "=" * 50)
        print("✓ Poster generation complete!")
        print("=" * 50)
        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main() -> NoReturn:
    """Main entry point."""
    sys.exit(cli())


if __name__ == "__main__":
    main()
