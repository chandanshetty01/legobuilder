# BrickBuilder — a 3D LEGO-style builder

A browser-based 3D builder. People place bricks on a baseplate and build objects
from a palette of **real LDraw parts** (38 curated pieces, plus any LDraw part
number on demand). Built with [Three.js](https://threejs.org/).

## Run it

Just open `index.html` in a browser (double-click it). Three.js loads from a CDN,
so an internet connection is needed on first load.

Prefer a local server? From this folder:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## The pieces

All pieces use the real LEGO unit system (1 stud spacing, a brick = 3 plates tall).
The curated palette has 38 parts: bricks (1×1 … 2×6), plates, tiles, slopes
(incl. 2×4 slope and 2×1 ridge), round parts, cones, an arch, a classic
1×4×3 window, and a wheel assembly. Geometry comes from the open-source
[LDraw](https://www.ldraw.org/) parts library, so any other part can be added
by typing its part number into the sidebar.

## Controls

- **Click** the grid to place a piece — it snaps to studs and stacks automatically.
- **R** — rotate 90° · **1–9** — pick a piece · **Del** — toggle delete mode.
- **Drag** to orbit · **scroll** to zoom · **right-drag** to pan.

## Blueprints

The **Blueprints** panel has preset builds with real step-by-step instructions:

- **Cozy House** — a custom model authored in LDraw format and embedded in
  `index.html` (`HOUSE_LDR`): 39 parts, 8 steps, white walls, green classic
  windows, red 45° gable roof.
- **Tree** — a custom model (`TREE_LDR`): 12 parts, 7 steps — round-brick
  trunk, slope-tapered canopy, cone top. Uses palette parts only.
- **Castle Gate** — a custom model (`CASTLE_LDR`): 79 parts, 17 steps — twin
  towers with battlements and blue cone spires, arched gateway, walkway.
  Palette parts only.
- **Missile Ship** — a custom model (`MISSILESHIP_LDR`): 363 parts, 12 steps — a
  wide guided-missile aviation ship: forward vertical-launch missiles (round-brick
  bodies + cone noses) and a bow gun, a starboard **radar island** (dark sensor
  block, mast, rotating radar booms), and a wide flat **flight deck / runway**
  with white centreline dashes, an aft helipad "H", and **three parked delta
  jets**. The hull is full-height/watertight (no open steps); the **bow** rakes
  down to a fine pointed stem and the **stern** to a rounded transom, both via
  45° slope bricks (`3039`) for a smooth, water-shedding shell. Generated and
  geometry-validated by `missile_ship_gen.py` (no collisions, every part
  supported; jets sit on left-studded deck patches so they clutch, while the
  rest of the deck is tiled smooth).
- **Military Ship** — a custom model (`SHIP_LDR`): 313 parts, 11 steps — a gray
  naval destroyer: a hull tapering to a bow with a dark waterline, tiled deck,
  stepped bridge superstructure, two funnels and a mast, fore + aft gun turrets
  (incl. superfiring) with barrels, deck railings and AA guns. Generated and
  geometry-validated by `ship_gen.py` (no collisions, every part supported; the
  only cantilevers are the gun barrels, rooted on their turrets).
- **Great Wall** — a custom model (`GREATWALL_LDR`): 310 parts, 15 steps —
  modelled on reference photos: a warm-tan stone wall that *undulates* over
  several ridge humps (not one peak), crenellated on both faces, with four
  blocky watchtowers on the hump tops and an arched `3659` gateway through a
  low saddle. Generated and geometry-validated by `greatwall_gen.py`
  (running-bond courses, no collisions, every brick supported; the arch legs
  rest on the gate pillars).

While a blueprint is active, the HUD shows an instruction-booklet style
callout of the pieces the next step needs (e.g. `4× Brick 2×4 · 2× Arch 1×4`) —
handy for following along with real bricks. A **next-pieces panel** in the
top-right shows those upcoming parts as 3D thumbnails with counts, so a second
person can pre-find the pieces while you place the current step.
- Official LEGO sets (Car, Radar Truck, X-Wing, AT-AT, …) loaded as packed
  `.mpd` models from the LDraw official model library.

Use *Place next* to build step-by-step, or *Auto* to watch it assemble.

## Where things live

Everything is in `index.html`:
- `REAL_PARTS` — the piece palette (real LDraw parts, loaded from a CDN).
- `COLORS` — the palette.
- `HOUSE_LDR` — the custom house blueprint (plain LDraw text with `0 STEP` markers).
- `MODEL_BLUEPRINTS` — the blueprint list (add a `file:` for a packed official
  set, or a `text:` for your own inline LDraw model).
