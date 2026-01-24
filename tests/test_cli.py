"""Tests for the CLI module."""

from __future__ import annotations

from maptoposter.cli import cli, create_parser


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
