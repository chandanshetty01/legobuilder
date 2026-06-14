---
name: legobuilder-blueprint
description: >-
  Create or edit a BrickBuilder (legobuilder) blueprint — a real-LDraw LEGO model
  embedded in index.html and built step-by-step. USE THIS whenever the user asks to
  build / design / add a model in this project: "build a <thing> with N parts",
  "make a LEGO <X>", "add a blueprint", "design a ship/castle/wall/car", or to fix
  the shape of an existing custom model. Encodes the validated Python-generator
  workflow (coordinate conventions, overlap/support checks, slopes, cantilevers,
  sheer, embedding, and ASCII verification) learned building the Ship / Missile
  Ship / Great Wall.
---

# Building a BrickBuilder blueprint

Blueprints are plain **LDraw text** with `0 STEP` markers, embedded in `index.html`
as a `const <NAME>_LDR = \`...\`` and registered in `MODEL_BLUEPRINTS`. For anything
past ~30 parts, **do not hand-place** — write a Python generator that emits the
`.ldr` and *asserts* validity, then embed it. Templates already in the repo:
`ship_gen.py`, `missile_ship_gen.py`, `greatwall_gen.py` — copy the helper block and
write a new layout.

## Golden rule (project memory)
Real-LEGO behavior: **every part rests on the part/baseplate below it**, no floating,
no overlaps, hulls/walls are watertight (no open horizontal steps), and behavior is
derived from geometry — never per-part hacks. Must also work for runtime-added parts.

## Coordinate conventions (match index.html exactly)
- 1 stud = **20 LDU** on X/Z; part origin is the **footprint centre**.
- **+Y is DOWN** (up = negative Y); a part's origin is the **TOP** of its body.
- brick = 24 LDU = **3 plate-levels**; plate/tile = 8 LDU = **1 level**.
- Work in **plate-levels**: a part with bottom at level `pb`, height `hp` plates →
  LDraw origin `Y = -8*(pb+hp)`. Cell directly below `pb` is `pb-1`; `pb==0` rests on
  the baseplate.
- Footprint centre for a `w`-wide part starting at stud `x0`: `X = 20*(x0 + (w-1)/2)`.
- A line is: `1 <colorCode> <X> <Y> <Z> <a b c d e f g h i> <part.dat>`; identity
  matrix = `1 0 0 0 1 0 0 0 1`. Steps are separated by `0 STEP`.

## Generator skeleton (reuse from ship_gen.py)
`occ[(x,z,level)]` set + helpers:
- `occupy(cells, pb, hp, cantilever_root=None)` — assert **no overlap**; assert
  **support** (every footprint cell has `pb-1` filled) UNLESS `pb==0` or a
  `cantilever_root` is given (then only the root cell must be supported). Fail fast.
- `place_x(color,x0,z,pb,length,table,hp)` — 1×N along X.
- `place_block(color,x0,z0,w,d,pb,hp,part)` — w×d footprint (2×2 round/brick/cone…).
- `place_barrel(...root='lo'/'hi')` — **cantilever**: only the rooted inner stud is
  supported; real LEGO clutch lets the rest overhang (gun barrels, radar booms, antennas).
- `place_slope(color,x0,z0,pb,matrix)` — 2×2 slope `3039` for smooth angled surfaces.
- `tile_run` / `fill_row` — greedy-pack a row from a length→part table; pass a `phase`
  to stagger seams (running bond) so courses interlock and read as masonry/plating.

## Shaping techniques that worked
- **Tapered / pointed footprint**: per-station width function (e.g. `hull_zs(x)`).
- **Sheer / varying height**: per-column `height(x)`; fill course `c` only where
  `height(x) > c` (same trick as the Great Wall's ridge profile).
- **Watertight ends (no "water gets in")**: keep the body **full-height & solid** —
  open stepped sheer leaves horizontal ledges and looks unfinished. Shape the ends
  with **slopes**, not steps. Stack slope bases one level apart for a *continuous*
  rake (e.g. deck 9 → 6 → 3 to a fine bow stem).
- **Slope rotation matrices** (proven in TREE_LDR): rises toward **+X** =
  `0 0 1 0 1 0 -1 0 0`; rises toward **−X** = `0 0 -1 0 1 0 1 0 0`. So a bow whose tip
  is at +X uses the −X-rising matrix (high edge aft); a stern tip at −X uses +X-rising.
- **Attaching flat plates/decals on a deck**: tiles are SMOOTH (no stud) so plates
  won't clutch on them. Leave those cells **studded** (don't tile them; mark them
  used) and place the plate there; tile everything else smooth. (How the parked jets
  sit on the flight deck.)
- **Cones** (missile noses, spires): 1×1 cone `4589` (hp 3), 2×2×2 cone `3942c`
  (hp 6). Origin is at the TOP like bricks → `Y = -8*(pb+hp)`; seat the base on the
  course below.
- **Markings / stripes / waterline**: 1×1 tiles in a contrast colour on studded cells;
  a dark bottom course reads as a waterline.

## Colour codes that render here (stick to these)
`0` black · `1` blue · `2` green · `4` red · `6` brown · `7` light grey ·
`14` yellow · `15` white · `19` tan · `28` dark tan · `72` dark bluish grey.

## Embedding into index.html
1. Add `const <NAME>_LDR = \`<ldr text>\`;` **immediately before** the line
   `// Only sets with real multi-step instructions` (i.e. before `MODEL_BLUEPRINTS`).
2. Register an entry in `MODEL_BLUEPRINTS`:
   `{ id:'m_xxx', name:'…', icon:'🛳️', steps:N, text:<NAME>_LDR, tag:'custom · real parts' }`.
3. **steps N must equal `(number of "0 STEP" lines) + 1`** — keep them in sync.
4. The `.ldr` text must contain **no backtick** (it would close the template literal).

## Verify before declaring done (no GUI browser is available)
- Run the generator — the **asserts** prove no overlaps and full support. A crash is
  a real geometry bug; fix it, don't suppress it.
- Render an **ASCII top view** (topmost part per `(x,z)`) and **side elevation**
  (max level per `x`) straight from the `.ldr` to confirm the silhouette/features.
- Validate the embed: extract the `<script type="module">` block and run
  `node --check`; confirm the embedded part count.
- Always tell the user you verified **geometry**, but **not the shaded 3D render**
  (no browser here), and offer to tune colours/shape from their feedback.

## Part-number cheatsheet (1×N along X unless noted)
bricks: `3005`1×1 `3004`1×2 `3622`1×3 `3010`1×4 `3009`1×6 `3008`1×8 · plates:
`3024`1×1 `3023`1×2 `3623`1×3 `3710`1×4 `3666`1×6 · tiles: `3070b`1×1 `3069b`1×2
`2431`1×4 `3068b`2×2 · round: `3062b` 1×1 brick, `4073` 1×1 plate, `3941` 2×2 brick ·
slope: `3039` 2×2 · cones: `4589` 1×1, `3942c` 2×2×2 · 2×2 brick `3003` · arch `3659`.
