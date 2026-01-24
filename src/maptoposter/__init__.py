"""MapToPoster - Generate beautiful, minimalist map posters for any city.

This package provides tools to create customizable map posters from
OpenStreetMap data with various themes and styling options.
"""

from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("maptoposter")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = ["__version__"]
