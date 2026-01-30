# Revised Step-by-Step Plan: Artistic Rendering Upgrade

This is a detailed, executable roadmap aligned to the audit findings. It is designed to be worked through in order, with clear checkpoints and minimal rework.

---

## Phase 0 — Pipeline Groundwork (1–2 days)

**Goal:** Make the rendering pipeline modular before adding any effects.

### Step 0.1 — Introduce StyleConfig
- Create a new `StyleConfig` dataclass (or pydantic model if needed).
- Include fields for:
  - Road widths (core, casing)
  - Road glow strength (optional)
  - Gradient strength
  - Typography positions and tracking
  - Texture/grain/vignette settings
  - Output reproducibility seed

**Deliverable:** A central style object used by renderer.

### Step 0.2 — Introduce Layer Model
- Define a `RenderLayer` structure with:
  - `name`, `zorder`, `gdf` (or edge list), `style`
- Create `build_layers()` that prepares layers without rendering.

**Deliverable:** Renderer can enumerate layers without drawing.

### Step 0.3 — Split render() into pipeline stages
- `build_layers()` → `render_layers()` → `post_process()`
- Keep output identical to current behavior

**Deliverable:** Same output, but pipeline is staged.

---

## Phase 1 — Road Styling Refactor (1–2 days)

**Goal:** One source of truth for road styling.

### Step 1.1 — Add RoadStyle classification
- Add `RoadStyle` struct:
  - `road_class`, `core_color`, `core_width`, `casing_color`, `casing_width`, `glow`
- Create `classify_edge()` function

**Deliverable:** Consistent road styling in one place.

### Step 1.2 — Convert graph to GeoDataFrame
- Use `ox.graph_to_gdfs()` once
- Create per-class subsets

**Deliverable:** Road layers grouped by class.

### Step 1.3 — Render roads by class in order
- Replace `ox.plot_graph()` with explicit per-layer plotting
- Ensure z-order is respected

**Deliverable:** Same visual output, full layer control.

---

## Phase 2 — Casing and Optional Glow (2–4 days)

**Goal:** Make roads look designed, not plotted.

### Step 2.1 — Two-pass casing
- For each road class:
  - Pass A: casing (thicker, lower zorder)
  - Pass B: core (thin, higher zorder)

**Deliverable:** Clear visual hierarchy.

### Step 2.2 — Optional glow for major roads
- Add glow via `matplotlib.patheffects` for motorways/primaries
- Ensure glow can be disabled in config

**Deliverable:** Premium feel without heavy overhead.

---

## Phase 3 — Typography System (1–2 days)

**Goal:** Robust typography for long names and varied layouts.

### Step 3.1 — Adaptive tracking
- Replace static spacing with adaptive tracking
- Tighten tracking for long names

### Step 3.2 — Two-line splitting
- Add logic for balanced 2-line city names

### Step 3.3 — Text styling
- Add stroke/path effects for city name
- Keep country/coords simpler

**Deliverable:** Typography holds up across cases.

---

## Phase 4 — Post-Processing Pipeline (2–4 days)

**Goal:** Add texture and grading as separate pass.

### Step 4.1 — Grain
- Generate noise in NumPy
- Composite lightly with Pillow

### Step 4.2 — Vignette
- Add radial alpha mask
- Blend with low opacity

### Step 4.3 — Paper texture
- Add tileable texture overlay

### Step 4.4 — Color grading
- Add subtle curve adjustments

**Deliverable:** Output feels print-like.

---

## Phase 5 — Presets (1–2 days)

**Goal:** Allow users to switch styles quickly.

### Step 5.1 — Define 3–5 presets (based on existing themes)
Use the current theme set as the source of truth. Start with these:

- Noir (maps to `noir.json`)
- Blueprint (maps to `blueprint.json`)
- Neon Cyberpunk (maps to `neon_cyberpunk.json`)
- Japanese Ink (maps to `japanese_ink.json`)
- Warm Beige (maps to `warm_beige.json`)

### Step 5.2 — Preset mapping
- Presets map to a `StyleConfig`
- Theme name is an explicit field in `StyleConfig` (no hidden fallback)

**Deliverable:** One switch changes full aesthetic.

---

## Optional Phase 6 — Datashader Backend (3–7 days)

**Goal:** Dense city scalability.

### Step 6.1 — Backend abstraction
- Create `RenderBackend` interface

### Step 6.2 — Datashader implementation
- Render roads to RGBA
- Composite with Matplotlib output
- Add a CLI flag to enable it (e.g., `--render-backend datashader`)

**Deliverable:** Fast, dense rendering path.

---

# Optional Enhancements

These are not required but valuable if time allows:

1. **Layer cache** — cache projected GDFs for repeated renders.
2. **Deterministic seeds** — ensure grain/noise reproducibility.
3. **Style packs** — JSON files defining StyleConfig presets.
4. **SVG/PDF-aware mode** — skip raster-only effects on vector output.
5. **Batch generation optimization** — parallelize city rendering with cache reuse.

---

# Minimal Viable Artistic Upgrade Path (If time-limited)

If time is tight, do only:

1. Phase 0 (pipeline separation)
2. Phase 1 (road classification refactor)
3. Phase 2 (casing, no glow)

That yields the largest visual improvement for minimal engineering effort.
