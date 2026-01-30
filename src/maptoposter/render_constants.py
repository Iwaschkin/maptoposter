"""Shared render constants."""

from __future__ import annotations


__all__ = [
    "ATTRIBUTION_X_POS",
    "ATTRIBUTION_Y_POS",
    "BASE_FONT_ATTR",
    "BASE_FONT_COORDS",
    "BASE_FONT_MAIN",
    "BASE_FONT_SUB",
    "CITY_NAME_Y_MAX",
    "CITY_NAME_Y_POS",
    "COORDS_Y_MAX",
    "COORDS_Y_POS",
    "COUNTRY_LABEL_Y_MAX",
    "COUNTRY_LABEL_Y_POS",
    "DIVIDER_Y_MAX",
    "DIVIDER_Y_POS",
    "GRADIENT_HEIGHT_FRACTION",
    "ROAD_WIDTH_DEFAULT",
    "ROAD_WIDTH_MOTORWAY",
    "ROAD_WIDTH_PATH",
    "ROAD_WIDTH_PRIMARY",
    "ROAD_WIDTH_RESIDENTIAL",
    "ROAD_WIDTH_SECONDARY",
    "ROAD_WIDTH_TERTIARY",
    "TEXT_CENTER_X",
]

# Typography positioning constants
TEXT_CENTER_X = 0.5
CITY_NAME_Y_POS = 0.14
COUNTRY_LABEL_Y_POS = 0.09
COORDS_Y_POS = 0.06
DIVIDER_Y_POS = 0.12
ATTRIBUTION_X_POS = 0.98
ATTRIBUTION_Y_POS = 0.02

# Typography position clamp limits (CR-013)
# Prevent text going too high on wide aspect ratio posters
CITY_NAME_Y_MAX = 0.35
DIVIDER_Y_MAX = 0.30
COUNTRY_LABEL_Y_MAX = 0.25
COORDS_Y_MAX = 0.20

# Gradient constants
GRADIENT_HEIGHT_FRACTION = 0.25

# Road width constants by highway type
ROAD_WIDTH_MOTORWAY = 1.2
ROAD_WIDTH_PRIMARY = 1.0
ROAD_WIDTH_SECONDARY = 0.8
ROAD_WIDTH_TERTIARY = 0.6
ROAD_WIDTH_RESIDENTIAL = 0.4
ROAD_WIDTH_PATH = 0.2  # Footpaths, bridleways, cycleways - thinnest
ROAD_WIDTH_DEFAULT = 0.4

# Base font sizes (at 12 inches width reference)
BASE_FONT_MAIN = 60
BASE_FONT_SUB = 22
BASE_FONT_COORDS = 14
BASE_FONT_ATTR = 8
