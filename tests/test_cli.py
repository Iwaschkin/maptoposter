"""Tests for the CLI module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from maptoposter.cli import _parse_batch_file, cli, create_parser


class TestCLI:
    """Tests for CLI functionality."""

    def test_cli_no_args_returns_zero(self) -> None:
        """Test that CLI with no args shows help and returns 0."""
        # When called with explicit empty args, should return 0
        result = cli(["--version"])
        assert result == 0

    def test_cli_list_themes(self) -> None:
        """Test --list-themes flag."""
        result = cli(["--list-themes"])
        assert result == 0

    def test_cli_list_presets(self) -> None:
        """Test --list-presets flag."""
        result = cli(["--list-presets"])
        assert result == 0

    def test_cli_cache_stats(self, tmp_path: Path) -> None:
        """Test --cache-stats flag."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            result = cli(["--cache-stats"])
            assert result == 0

    def test_cli_clear_cache(self, tmp_path: Path) -> None:
        """Test --clear-cache flag."""
        with patch.dict("os.environ", {"MAPTOPOSTER_CACHE_DIR": str(tmp_path)}):
            result = cli(["--clear-cache"])
            assert result == 0

    def test_cli_missing_city_country(self) -> None:
        """Test that missing city/country returns error."""
        result = cli(["--city", "Paris"])
        assert result == 1

    def test_cli_invalid_theme(self) -> None:
        """Test that invalid theme returns error."""
        result = cli(
            [
                "--city",
                "Paris",
                "--country",
                "France",
                "--theme",
                "nonexistent_theme_xyz",
            ]
        )
        assert result == 1


class TestParser:
    """Tests for argument parser."""

    def test_parser_defaults(self) -> None:
        """Test parser default values."""
        parser = create_parser()
        args = parser.parse_args(["--city", "Paris", "--country", "France"])
        assert args.theme == "feature_based"
        assert args.preset is None
        assert args.style_pack is None
        assert args.render_backend == "matplotlib"
        assert args.distance == 29000
        assert args.width == 12.0
        assert args.height == 16.0
        assert args.format == "png"

    def test_parser_custom_values(self) -> None:
        """Test parser with custom values."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "-c",
                "Tokyo",
                "-C",
                "Japan",
                "-t",
                "noir",
                "-d",
                "15000",
                "-W",
                "18",
                "-H",
                "24",
                "-f",
                "svg",
            ]
        )
        assert args.city == "Tokyo"
        assert args.country == "Japan"
        assert args.theme == "noir"
        assert args.distance == 15000
        assert args.width == 18.0
        assert args.height == 24.0
        assert args.format == "svg"

    def test_parser_preset_value(self) -> None:
        """Test parser with preset value."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "--city",
                "Paris",
                "--country",
                "France",
                "--preset",
                "noir",
            ]
        )
        assert args.preset == "noir"

    def test_parser_all_themes_flag(self) -> None:
        """Test --all-themes flag."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "--city",
                "Paris",
                "--country",
                "France",
                "--all-themes",
            ]
        )
        assert args.all_themes is True

    def test_parser_batch_flag(self) -> None:
        """Test --batch flag."""
        parser = create_parser()
        args = parser.parse_args(["--batch", "cities.txt"])
        assert args.batch == "cities.txt"

    def test_parser_workers_flag(self) -> None:
        """Test --workers flag."""
        parser = create_parser()
        args = parser.parse_args(["--batch", "cities.txt", "--workers", "8"])
        assert args.workers == 8


class TestBatchProcessing:
    """Tests for batch processing functionality."""

    def test_parse_batch_file(self, tmp_path: Path) -> None:
        """Test parsing a valid batch file."""
        batch_file = tmp_path / "cities.txt"
        batch_file.write_text("Paris, France\nTokyo, Japan\n")

        cities = _parse_batch_file(str(batch_file))
        assert len(cities) == 2
        assert cities[0] == ("Paris", "France")
        assert cities[1] == ("Tokyo", "Japan")

    def test_parse_batch_file_with_comments(self, tmp_path: Path) -> None:
        """Test parsing a batch file with comments and blank lines."""
        batch_file = tmp_path / "cities.txt"
        batch_file.write_text("# Comment\nParis, France\n\nTokyo, Japan\n")

        cities = _parse_batch_file(str(batch_file))
        assert len(cities) == 2

    def test_parse_batch_file_invalid_lines(self, tmp_path: Path) -> None:
        """Test parsing skips invalid lines."""
        batch_file = tmp_path / "cities.txt"
        batch_file.write_text("Paris, France\nInvalidLine\nTokyo, Japan\n")

        cities = _parse_batch_file(str(batch_file))
        assert len(cities) == 2

    def test_cli_batch_file_not_found(self, tmp_path: Path) -> None:
        """Test --batch with nonexistent file returns error."""
        result = cli(["--batch", str(tmp_path / "nonexistent.txt")])
        assert result == 1
