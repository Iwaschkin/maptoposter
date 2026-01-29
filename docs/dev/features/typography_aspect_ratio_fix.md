# Typography Aspect Ratio Investigation

## Issue Description
Text elements (city name, separator line, country name, coordinates) shift their visual positions when the poster aspect ratio (W:H) changes. On wide posters, elements appeared crowded together.

## Investigation Process

### 1. Understanding the Current System
The typography system uses `ax.transAxes` for positioning, which provides **normalized coordinates (0-1)**:
- x=0.5 is horizontal center
- y=0.14 means "14% from the bottom of the axes"

Key constants (from `render_constants.py`):
```python
CITY_NAME_Y_POS = 0.14
DIVIDER_Y_POS = 0.12
COUNTRY_LABEL_Y_POS = 0.09
COORDS_Y_POS = 0.06
```

### 2. Root Cause Identified
The problem occurs because:

1. **Y positions are percentages of HEIGHT** - A Y position of 0.14 represents 14% of the poster height
2. **Font sizes scale based on WIDTH** - `scale_factor = width / 12.0`
3. **These scaling approaches conflict on non-square posters**

#### Example: Physical Spacing by Aspect Ratio

| Poster Size | Height | Y=0.14 Physical | Y=0.12 Physical | Gap |
|-------------|--------|-----------------|-----------------|-----|
| 40" × 40"   | 40"    | 5.6"            | 4.8"            | 0.8" |
| 90" × 60"   | 60"    | 8.4"            | 7.2"            | 1.2" |
| 60" × 40"   | 40"    | 5.6"            | 4.8"            | 0.8" |

#### The Core Problem
On a **wide poster** (W > H):
- Font sizes are LARGE (scaled to wide width)
- Vertical spacing is SMALL (percentage of short height)
- **Result: Text elements overlap or crowd together**

On a **tall poster** (H > W):
- Font sizes are SMALL (scaled to narrow width)
- Vertical spacing is LARGE (percentage of tall height)
- **Result: Excessive gaps between text elements**

## Solution Design

### Approach: Aspect Ratio Compensation
Apply a compensation factor to Y positions based on the aspect ratio:

```python
aspect_ratio = width / height
y_compensation = max(1.0, aspect_ratio ** 0.5)  # Square root for gentler scaling

city_y = base_y_pos * y_compensation
```

### Why Square Root?
- Linear compensation (`aspect_ratio`) would be too aggressive
- Square root provides gentler, more visually pleasing adjustment
- A 2:1 aspect ratio gets ~1.41x Y position multiplier
- A 1.5:1 aspect ratio gets ~1.22x Y position multiplier

### Safety Clamping
Y positions are clamped to prevent text going too high on extremely wide posters:
```python
city_y = min(city_y, 0.35)
divider_y = min(divider_y, 0.30)
country_y = min(country_y, 0.25)
coords_y = min(coords_y, 0.20)
```

## Implementation

### Files Modified
1. **render.py** - `_add_typography()` method:
   - Added `aspect_ratio` parameter
   - Calculates Y compensation factor
   - Applies compensation to all text Y positions

2. **render.py** - `post_process()` method:
   - Added `aspect_ratio` parameter
   - Passes through to `_add_typography()`

3. **render.py** - `render()` method:
   - Calculates `aspect_ratio = width / height`
   - Passes to `post_process()`

### Code Flow
```
render() 
  → calculates aspect_ratio = width / height
  → post_process(ax, point, scale_factor, aspect_ratio)
    → _add_typography(ax, point, scale_factor, aspect_ratio)
      → y_compensation = max(1.0, aspect_ratio ** 0.5)
      → applies compensation to city_y, divider_y, country_y, coords_y
```

## Verification

### Test Cases
| Dimensions | Aspect Ratio | Y Compensation | City Y (base 0.14) |
|------------|--------------|----------------|-------------------|
| 40 × 40    | 1.0          | 1.00           | 0.140             |
| 50 × 40    | 1.25         | 1.12           | 0.157             |
| 60 × 40    | 1.5          | 1.22           | 0.171             |
| 80 × 40    | 2.0          | 1.41           | 0.198             |
| 90 × 60    | 1.5          | 1.22           | 0.171             |
| 40 × 60    | 0.67         | 1.00 (clamped) | 0.140             |

### Additional Changes
- Increased PIL `MAX_IMAGE_PIXELS` from 300M to 500M to support larger poster sizes (e.g., 90" × 60" @ 300 DPI)

## Future Considerations
- Style packs could potentially override the compensation behavior
- Ultra-wide aspect ratios (>3:1) may need special handling
- Consider allowing users to manually adjust compensation factor
