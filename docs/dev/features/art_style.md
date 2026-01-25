## Plan to add “artistic flare” to your poster renderer

### Goal

Move from “clean plotted map” to “designed poster” by adding:

* Multi-pass road rendering (casings, glow)
* Texture and grading (paper, grain, vignette)
* Better typography treatment (stroke, tracking, optional 2-line layout)
* Optional alternative render pipeline for dense networks (Datashader)

---

## Phase 0 - Baseline and safety rails (1-2 hours)

* Add a `style_version` or `preset` field in `PosterConfig` so outputs are reproducible.
* Standardise output logging:

  * Replace `print()` with `logger.info()` and keep tqdm optional.
* Add a “golden sample” output:

  * Pick 2-3 cities (one coastal, one river-heavy, one dense).
  * Save outputs in a `samples/` folder for before/after comparison.

Deliverable: same output as today, but reproducible and easier to iterate.

---

## Phase 1 - Refactor for styling control (2-4 hours)

### 1) Consolidate road classification

Create one function that returns a small struct for each edge:

* `road_class` (motorway, primary, secondary, tertiary, minor, path)
* `base_color`
* `base_width`
* `casing_color`
* `casing_width`

This removes duplication and makes artistic changes easy.

### 2) Plot roads by class in layers

Instead of one `ox.plot_graph()` call with per-edge arrays, do:

* Extract edges to GeoDataFrame with `ox.graph_to_gdfs()`
* Split by class
* Plot each class in a defined order

This gives you:

* Proper stacking
* Different effects per class
* Cleaner outcomes in dense places

Deliverable: visually similar output, but with full control.

---

## Phase 2 - “Poster-grade” roads (biggest visual win) (3-6 hours)

### 1) Two-pass “casing” roads

For each road class:

* Pass A (casing): thicker, lower z-order, slightly darker or lighter
* Pass B (core): thinner, top z-order, your theme colour

This instantly makes the network readable and premium.

### 2) Optional glow

Use Matplotlib path effects for selected classes:

* Motorways and primaries: subtle glow or stroke
* Minor roads: no glow, keep quiet

Implementation choices:

* Quick: `matplotlib.patheffects` for stroke
* More control: render road layers to RGBA image then blur with Pillow and composite

Deliverable: roads look designed, not plotted.

---

## Phase 3 - Typography that holds up (2-4 hours)

### 1) Add text strokes

Use `matplotlib.patheffects`:

* City name: stroke to separate from background
* Country: lighter stroke or none

### 2) Tracking and line-break rules

Replace fixed `"  ".join(...)` with adaptive tracking:

* Short names: wide tracking
* Long names: tighter tracking
* Very long: split into 2 lines (balanced)

### 3) Layout robustness

Make text positions configurable in `PosterConfig`:

* `typography_block_y`
* `divider_width_fraction`
* `coords_alpha`

Deliverable: typography stays clean for “Rio”, “San Francisco”, “Llanfairpwllgwyngyll”, etc.

---

## Phase 4 - Texture and grading pipeline (the “art” part) (3-8 hours)

Add a post-processing step after Matplotlib saves, using Pillow.

### 1) Paper texture overlay

* Add an optional texture image (tileable).
* Composite with low opacity.

### 2) Grain

* Generate grain with NumPy, blend lightly.

### 3) Vignette

* Radial alpha mask, subtle darken at edges.

### 4) Colour grading

* Gentle curves:

  * Lift blacks slightly for matte look
  * Push highlights warm or cool per preset

Deliverable: output feels like a print, not a screenshot.

---

## Phase 5 - Presets (so users can pick a look) (2-4 hours)

Define 3-5 named presets, each is just a theme + effect settings:

* Minimal Mono (no texture, strong casings, high contrast)
* Ink Wash (soft roads, paper, vignette)
* Blueprint (dark bg, cyan lines, grid optional)
* Neon Night (dark bg, glow roads)
* Vintage Atlas (warm paper, muted palette)

Each preset controls:

* Colours
* Casing widths
* Glow on/off
* Texture on/off
* Grain strength
* Gradient strength

Deliverable: one config switch changes the whole vibe.

---

## Optional Phase 6 - Datashader mode (only if you need it) (6-12 hours)

If you render large distances or dense cities and want a silky “ink density” look:

* Convert edges to lines
* Render roads with Datashader into an RGBA image
* Composite water/parks + typography in Matplotlib

Pros:

* Beautiful density rendering
* Fast for huge networks
  Cons:
* More complexity
* Less true vector output

Deliverable: a second render backend for “art mode”.

---

## Implementation checklist (what to build, in order)

1. Replace prints with logging, add sample outputs
2. Convert roads to GeoDataFrame and plot by class order
3. Add casing pass and optional glow
4. Add path effects to typography
5. Add typography tracking + 2-line break
6. Add Pillow post-process: grain, vignette, texture, grading
7. Add presets and document them
8. Optional Datashader backend

---

## Recommended libraries (pragmatic set)

* Matplotlib path effects: built-in (`matplotlib.patheffects`)
* Pillow: texture, grain, vignette, grading
* Shapely/GeoPandas: buffering, simplifying, dissolving for stylised layers
* Optional:

  * blend-modes (or do blending in Pillow)
  * datashader + colorcet for density rendering

---
