"""Command-line interface for MapToPoster."""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from .config import (
    PosterConfig,
    generate_output_filename,
    get_available_themes,
    load_theme,
)
from .geo import get_coordinates
from .render import PosterRenderer


__all__ = ["cli", "main"]


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
  --all-themes      Generate posters for all themes
  --distance, -d    Map radius in meters (default: 29000)
  --list-themes     List all available themes

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


def cli(args: list[str] | None = None) -> int:
    """Run the CLI with the given arguments.

    Args:
        args: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = create_parser()
    parsed = parser.parse_args(args)

    # Show version
    if parsed.version:
        from . import __version__

        print(f"maptoposter {__version__}")
        return 0

    # If no arguments provided, show examples
    if len(sys.argv) == 1 and args is None:
        _print_examples()
        return 0

    # List themes if requested
    if parsed.list_themes:
        _list_themes()
        return 0

    # Validate required arguments
    if not parsed.city or not parsed.country:
        print("Error: --city and --country are required.\n")
        _print_examples()
        return 1

    available_themes = get_available_themes()
    if not available_themes:
        print("No themes found in 'themes/' directory.")
        return 1

    if parsed.all_themes:
        themes_to_generate = available_themes
    else:
        if parsed.theme not in available_themes:
            print(f"Error: Theme '{parsed.theme}' not found.")
            print(f"Available themes: {', '.join(available_themes)}")
            return 1
        themes_to_generate = [parsed.theme]

    print("=" * 50)
    print("City Map Poster Generator")
    print("=" * 50)

    try:
        coords = get_coordinates(parsed.city, parsed.country)

        for theme_name in themes_to_generate:
            theme = load_theme(theme_name)
            output_file = generate_output_filename(
                parsed.city,
                theme_name,
                parsed.format,
            )

            config = PosterConfig(
                city=parsed.city,
                country=parsed.country,
                theme_name=theme_name,
                distance=parsed.distance,
                width=parsed.width,
                height=parsed.height,
                output_format=parsed.format,
                country_label=parsed.country_label,
                theme=theme,
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
