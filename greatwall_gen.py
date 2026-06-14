#!/usr/bin/env python3
"""Generate a validated Great Wall of China LDraw model for BrickBuilder.

Tuned to reference photos: an UNDULATING wall that climbs and dips over several
ridge humps (not a single peak), warm tan stone, blocky crenellated watchtowers
on the hump tops, and an arched gateway at a low saddle. No flag/cone.

Grid conventions (matching index.html):
  - 1 stud = 20 LDU on X/Z; origin at footprint centre.
  - brick = 24 LDU tall; +Y is DOWN, so 'up' is negative Y; origin at TOP of body.
  - Layer n (0-based) -> origin Y = -(n+1)*24.  Cell below n is n-1.

Built bottom-up as solid, staggered courses so every brick rests on the brick
(or baseplate) directly beneath it. The only bridging part is the arch, whose
legs rest on the gate pillars (real LEGO clutch, like the Castle Gate model).
"""

# 1xN bricks along X (footprint N wide, 1 deep). LDraw part numbers.
BRICK = {8: '3008.dat', 6: '3009.dat', 4: '3010.dat', 3: '3622.dat', 2: '3004.dat', 1: '3005.dat'}
LENS = sorted(BRICK.keys(), reverse=True)
ARCH = '3659.dat'   # Arch 1x4 — spans the gateway opening

# Warm-stone colours: 19 tan (body), 28 dark tan (foundation/banding/trim).
C_BODY, C_BAND, C_FOUND, C_MERLON = 19, 28, 28, 19

lines = []          # output LDraw lines, with '0 STEP' separators
occ = {}            # (x, z, n) -> True   placed cell-layers (overlap guard)
colH = {}           # (x, z) -> target fill height in layers (the height map)


def setH(x, z, h):
    colH[(x, z)] = max(colH.get((x, z), 0), h)


def emit(color, x0, z, n, part, width):
    """Low-level part write at stud x0, row z, layer n (centred on its width)."""
    X = 20 * (x0 + (width - 1) / 2)
    Z = 20 * z
    Y = -(n + 1) * 24
    lines.append(f"1 {color} {X:g} {Y} {Z:g} 1 0 0 0 1 0 0 0 1 {part}")


def place_brick(color, x0, z, n, length):
    for i in range(length):
        cell = (x0 + i, z, n)
        assert cell not in occ, f"overlap at {cell}"
        occ[cell] = True
        if n > 0:
            assert (x0 + i, z, n - 1) in occ, f"unsupported at {cell}"
    emit(color, x0, z, n, BRICK[length], length)


def place_arch(color, x0, z, n):
    """Arch 1x4 spanning x0..x0+3. Legs (ends) must rest on filled pillars; the
    2-stud span underneath is the gateway opening."""
    assert (x0, z, n - 1) in occ and (x0 + 3, z, n - 1) in occ, "arch legs unsupported"
    for i in range(4):
        cell = (x0 + i, z, n)
        assert cell not in occ, f"overlap at {cell}"
        occ[cell] = True
    emit(color, x0, z, n, ARCH, 4)


def tile_run(color, x_start, x_end, z, n, phase):
    """Greedy-fill studs [x_start, x_end] in row z at layer n; `phase` staggers."""
    x = x_start
    if phase and (x_end - x_start + 1) > 2:
        place_brick(color, x, z, n, 2)
        x += 2
    while x <= x_end:
        run = x_end - x + 1
        for L in LENS:
            if L <= run:
                place_brick(color, x, z, n, L)
                x += L
                break


def fill_layer(n, color, skip):
    """Place every column whose target height exceeds n, except `skip` (x,z)."""
    rows = {}
    for (x, z), h in colH.items():
        if h > n and (x, z) not in skip:
            rows.setdefault(z, []).append(x)
    for z in sorted(rows):
        xs = sorted(rows[z])
        run_start = prev = xs[0]
        for x in xs[1:] + [None]:
            if x is None or x != prev + 1:
                tile_run(color, run_start, prev, z, n, n % 2)
                run_start = x
            prev = x if x is not None else prev


def step():
    lines.append("0 STEP")


# ---------------------------------------------------------------------------
# 1. Undulating height profile (brick layers) via linear ramps between control
#    points — the wall snakes over ridge humps and dips into saddles.
# ---------------------------------------------------------------------------
CTRL = [(0, 3), (8, 6), (17, 3), (26, 7), (35, 3), (44, 6), (52, 3), (60, 5), (63, 4)]
WALL_LEN = 64
WALL_DEPTH = 2                      # studs deep (z = 0,1); z=0 is the outer face


def wall_h(x):
    for (x0, h0), (x1, h1) in zip(CTRL, CTRL[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return max(3, round(h0 + t * (h1 - h0)))
    return 3


for x in range(WALL_LEN):
    for z in range(WALL_DEPTH):
        setH(x, z, wall_h(x))

# ---------------------------------------------------------------------------
# 2. Watchtowers on the hump tops — solid blocks projecting outward (+Z) and
#    rising above the wall.  (x0, x1, depth, top_layer)
# ---------------------------------------------------------------------------
TOWERS = [
    (6, 9, 4, 8),       # west hump
    (23, 30, 4, 9),     # great central tower (highest hump)
    (42, 45, 4, 8),     # east hump
    (58, 61, 4, 7),     # far-east hump
]
for (x0, x1, depth, top) in TOWERS:
    for x in range(x0, x1 + 1):
        for z in range(depth):
            setH(x, z, top)

# ---------------------------------------------------------------------------
# 3. Gateway — a 2-stud arched passage straight through the wall on the west
#    flank, away from the towers.  Pillars at g0 and g0+3, opening between.
# ---------------------------------------------------------------------------
GATE0 = 12
GATE_COLS = {(GATE0 + i, z) for i in range(4) for z in range(WALL_DEPTH)}
gate_top = max(wall_h(GATE0 + i) for i in range(4))

MAXH = max(colH.values())

# ---------------------------------------------------------------------------
# 4. Emit the solid body course-by-course (skipping the gate columns), with a
#    foundation course and banded courses for stone texture.
# ---------------------------------------------------------------------------
for n in range(MAXH):
    col = C_FOUND if n == 0 else (C_BAND if n % 3 == 2 else C_BODY)
    fill_layer(n, col, GATE_COLS)
    step()

# ---------------------------------------------------------------------------
# 5. Build the gateway: pillars, arch, and the wall carried above it.
# ---------------------------------------------------------------------------
for z in range(WALL_DEPTH):
    place_brick(C_FOUND, GATE0, z, 0, 1)            # pillar feet
    place_brick(C_FOUND, GATE0 + 3, z, 0, 1)
    place_brick(C_BODY, GATE0, z, 1, 1)             # pillar shafts (opening is 2 tall)
    place_brick(C_BODY, GATE0 + 3, z, 1, 1)
    place_arch(C_BODY, GATE0, z, 2)                 # arch bridges the opening
    for n in range(3, gate_top):                    # wall carried above the arch
        for i in range(4):
            x = GATE0 + i
            if wall_h(x) > n:
                place_brick(C_BAND if n % 3 == 2 else C_BODY, x, z, n, 1)
step()

# ---------------------------------------------------------------------------
# 6. Wall battlements — outer-face merlons (z=0, every other stud) and an offset
#    inner parapet (z=1), skipping the tower footprints.
# ---------------------------------------------------------------------------
tower_x = set()
for (x0, x1, depth, top) in TOWERS:
    tower_x.update(range(x0, x1 + 1))

for x in range(WALL_LEN):
    if x in tower_x:
        continue
    n = wall_h(x)
    if x % 2 == 0:
        place_brick(C_MERLON, x, 0, n, 1)
    else:
        place_brick(C_BAND, x, WALL_DEPTH - 1, n, 1)
step()

# ---------------------------------------------------------------------------
# 7. Tower-top battlements — a ring of merlons around each tower's top edge.
# ---------------------------------------------------------------------------
for (x0, x1, depth, top) in TOWERS:
    for x in range(x0, x1 + 1):
        for z in range(depth):
            edge = (x == x0 or x == x1 or z == 0 or z == depth - 1)
            if edge and ((x + z) % 2 == 0):
                place_brick(C_MERLON, x, z, top, 1)
    step()

# ---------------------------------------------------------------------------
# Assemble + report.
# ---------------------------------------------------------------------------
header = ["0 Great Wall of China", "0 Name: greatwall.ldr",
          "0 Author: BrickBuilder", "0 !LDRAW_ORG Model"]
out_lines = header + lines
while out_lines[-1].strip() == "0 STEP":
    out_lines.pop()
out = "\n".join(out_lines) + "\n"

part_count = sum(1 for l in out_lines if l.startswith("1 "))
step_count = sum(1 for l in out_lines if l.strip() == "0 STEP") + 1

with open("greatwall.ldr", "w") as f:
    f.write(out)

print(f"parts={part_count} steps={step_count}")
