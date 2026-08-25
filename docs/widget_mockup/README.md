# Weather widget mockup — Prototype A (chosen)

iOS medium widget (364x170pt), 9 readings: temp, sunrise, sunset, humidity,
wind speed, wind direction, pressure, light (lux), rain.

Style: deep blue card (#17558F), amber (#F5A623) temp accent only, white
text/icons, SF Pro Rounded. Wind speed/direction sit as plain cells (no
pill/divider) — this was the last change, chosen as final.

- `Main.dc.html` — chosen version (with vertical divider between temp block and grid)
- `NoDivider.dc.html` — alt: same, grouping by spacing instead of divider line
- `canvas.json` — layout manifest for both, used to re-seed the design canvas

Live editable canvas (Claude Design artifact):
https://claude.ai/code/artifact/45d60242-410d-41d7-bbae-9a7dceada0b1

To resume in a new session: point `/design` at this folder, or re-seed
`weather-widget-layouts.html` via `seed-canvas.mjs` using these files.
Visual prototype only — no Scriptable/code implementation yet.
