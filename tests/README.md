# Visual Regression Strategy

This project uses lightweight visual checks for PNG output:

1. Generate a small, deterministic poster (fixed city, distance, preset, seed).
2. Store baseline PNGs under tests/fixtures/.
3. In tests, render a new PNG and compare using a pixel-diff threshold.
4. Fail if the diff exceeds tolerance; update baselines only with approval.

Suggested defaults:
- City: Congleton, UK
- Preset: noir
- Distance: 8000
- Width/Height: 6x6
- Seed: fixed in style pack

Use this strategy to cover:
- Road casing/core layer changes
- Typography adjustments
- Post-processing effects (PNG only)
