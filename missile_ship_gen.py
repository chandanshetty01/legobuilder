#!/usr/bin/env python3
"""Generate a validated wide missile / aviation ship for BrickBuilder.

User asks: a MISSILE ship, with RADAR, with a RUNWAY, wide enough to PARK JETS.
So this is a carrier-style hull:
  - MISSILES: forward vertical-launch battery (round-brick bodies + cone noses)
              plus a bow naval gun.
  - RADAR:    a starboard ISLAND superstructure (dark sensor block) with a tall
              mast + rotating radar boom — offset to keep the deck clear.
  - RUNWAY:   a wide flat flight deck, tiled smooth, with white centreline
              dashes and an aft helipad "H".
  - JETS:     three parked delta jets on the deck.

Grid conventions (matching index.html), worked in PLATE levels (8 LDU):
  - 1 stud = 20 LDU on X/Z; origin at footprint centre. +Y DOWN (up = -Y).
  - brick = 3 levels; plate/tile = 1 level; bottom pb, height hp -> origin (TOP)
    Y = -8*(pb+hp).  Parked plates sit on STUDDED deck patches (those cells are
    left un-tiled) so they clutch; tiles elsewhere keep the runway smooth.

Every part is overlap- and support-checked. Cantilevers (gun barrel, radar
boom) are rooted on the structure beneath them.
"""

BRICK_X = {8: '3008.dat', 6: '3009.dat', 4: '3010.dat', 3: '3622.dat', 2: '3004.dat', 1: '3005.dat'}
HULL_TABLE = {6: '3009.dat', 4: '3010.dat', 3: '3622.dat', 2: '3004.dat', 1: '3005.dat'}
TILE_X  = {4: '2431.dat', 2: '3069b.dat', 1: '3070b.dat'}
PLATE_X = {6: '3666.dat', 4: '3710.dat', 3: '3623.dat', 2: '3023.dat', 1: '3024.dat'}
ROUND2_BRICK = '3941.dat'
ROUND1_BRICK = '3062b.dat'
ROUND1_PLATE = '4073.dat'
CONE1        = '4589.dat'
TILE_2x2     = '3068b.dat'

# Colours: 7 light grey, 72 dark bluish grey, 0 black, 4 red, 15 white, 14 yellow.
HULL, WATER, DECK, SUPER, RADAR, GUN = 7, 72, 72, 7, 0, 72
FUNNEL, CAP, MAST, RAIL = 72, 0, 72, 7
M_BODY, M_TIP, MARK_C = 15, 4, 15
JET, JET_TRIM = 7, 0

occ = {}
lines = []
hull_cells = set()
used9 = set()


# ---------------------------------------------------------------------------
def emit(color, cx, cz, pb, hp, part):
    lines.append(f"1 {color} {20*cx:g} {-8*(pb+hp)} {20*cz:g} 1 0 0 0 1 0 0 0 1 {part}")


def occupy(cells, pb, hp, cantilever_root=None):
    for (x, z) in cells:
        for k in range(hp):
            assert (x, z, pb + k) not in occ, f"overlap at {(x, z, pb + k)}"
    if pb > 0:
        if cantilever_root is not None:
            assert cantilever_root + (pb - 1,) in occ, f"cantilever root unsupported {cantilever_root}"
        else:
            for (x, z) in cells:
                assert (x, z, pb - 1) in occ, f"unsupported at {(x, z, pb)}"
    for (x, z) in cells:
        for k in range(hp):
            occ[(x, z, pb + k)] = True


def place_x(color, x0, z, pb, length, table, hp):
    occupy([(x0 + i, z) for i in range(length)], pb, hp)
    emit(color, x0 + (length - 1) / 2, z, pb, hp, table[length])


def place_block(color, x0, z0, w, d, pb, hp, part):
    occupy([(x0 + i, z0 + j) for i in range(w) for j in range(d)], pb, hp)
    emit(color, x0 + (w - 1) / 2, z0 + (d - 1) / 2, pb, hp, part)


def place_barrel(color, x0, z, pb, length, root, table=PLATE_X):
    rx = x0 if root == 'lo' else x0 + length - 1
    occupy([(x0 + i, z) for i in range(length)], pb, 1, cantilever_root=(rx, z))
    emit(color, x0 + (length - 1) / 2, z, pb, 1, table[length])


SLOPE = '3039.dat'   # Slope 2x2 (45 deg) — the smooth raked hull-end surface
# Rotation about Y so the slope's high edge faces -X (bow, rakes down toward +X
# tip) or +X (stern, rakes down toward -X tip). Matrices proven in TREE_LDR.
M_BOW   = "0 0 -1 0 1 0 1 0 0"
M_STERN = "0 0 1 0 1 0 -1 0 0"


def place_slope(color, x0, z0, pb, matrix):
    """2x2 slope occupying a brick cell at x0..x0+1, z0..z0+1 (closes the deck
    edge with a continuous angled surface — no open step for water to sit in)."""
    occupy([(x0 + i, z0 + j) for i in range(2) for j in range(2)], pb, 3)
    lines.append(f"1 {color} {20*(x0+0.5):g} {-8*(pb+3)} {20*(z0+0.5):g} {matrix} {SLOPE}")


def tile_run(color, xa, xb, z, pb, table, hp, phase):
    lens = sorted(table.keys(), reverse=True)
    x = xa
    if phase and (xb - xa + 1) > 2 and 2 in table:
        place_x(color, x, z, pb, 2, table, hp); x += 2
    while x <= xb:
        run = xb - x + 1
        for L in lens:
            if L <= run:
                place_x(color, x, z, pb, L, table, hp); x += L; break


def fill_row(color, xs, z, pb, table, hp, phase=0):
    if not xs:
        return
    xs = sorted(xs)
    start = prev = xs[0]
    for x in xs[1:] + [None]:
        if x is None or x != prev + 1:
            tile_run(color, start, prev, z, pb, table, hp, phase)
            start = x
        prev = x if x is not None else prev


def mark9(x0, z0, w, d):
    for i in range(w):
        for j in range(d):
            used9.add((x0 + i, z0 + j))


def step():
    lines.append("0 STEP")


# ---------------------------------------------------------------------------
# Hull — bow at +X, beam 8 (z0..7), 3 courses, deck at level 9.
# ---------------------------------------------------------------------------
LEN = 44
DKY = 9


def hull_zs(x):
    # Plan view: full beam amidships, tapering to a 2-wide bow and a rounded
    # fantail at the stern (so neither end is a flat full-width wall).
    if x < 0 or x > LEN - 1:
        return []
    if x == 0:    return list(range(2, 6))   # rounded fantail tip (w4)
    if x == 1:    return list(range(1, 7))   # w6
    if x <= 33:   return list(range(0, 8))   # full beam z0..7
    if x <= 37:   return list(range(1, 7))   # w6
    if x <= 39:   return list(range(2, 6))   # w4
    if x <= 41:   return list(range(2, 6))   # bow cap (w4)
    return list(range(3, 5))                  # bow tip (w2)


BODY = range(2, 40)   # full-height, flat-deck region (deck level 9)

for x in range(LEN):
    for z in hull_zs(x):
        hull_cells.add((x, z))

# 1. BODY hull — three FULL courses (no open steps -> watertight), flat deck.
for course, pb in enumerate((0, 3, 6)):
    col = WATER if course == 0 else HULL
    for z in range(8):
        xs = [x for x in BODY if z in hull_zs(x)]
        fill_row(col, xs, z, pb, HULL_TABLE, 3, phase=course % 2)
    step()

# 2. BOW CAP (x40..43) — a smooth raked wedge: solid hull below, slope on top,
#    stepping the slope base down so the surface is CONTINUOUS (9 -> 6 -> 3).
for z in range(2, 6):                                  # x40-41 lower courses
    place_x(WATER, 40, z, 0, 2, HULL_TABLE, 3)
    place_x(HULL, 40, z, 3, 2, HULL_TABLE, 3)
for z in (2, 4):
    place_slope(HULL, 40, z, 6, M_BOW)                 # rakes 9 -> 6
for z in (3, 4):                                       # x42-43 lower course
    place_x(WATER, 42, z, 0, 2, HULL_TABLE, 3)
place_slope(HULL, 42, 3, 3, M_BOW)                     # rakes 6 -> 3 (fine stem)
step()

# 3. STERN CAP (x0..1) — rounded fantail raked down to a short transom (9 -> 6).
for z in range(2, 6):                                  # x0-1 lower courses (z2..5)
    place_x(WATER, 0, z, 0, 2, HULL_TABLE, 3)
    place_x(HULL, 0, z, 3, 2, HULL_TABLE, 3)
for z in (2, 4):
    place_slope(HULL, 0, z, 6, M_STERN)                # rakes 9 (x1) -> 6 (x0)
for z in (1, 6):                                       # fantail wing edges (x1 only)
    place_x(WATER, 1, z, 0, 1, HULL_TABLE, 3)
    place_x(HULL, 1, z, 3, 1, HULL_TABLE, 3)
    place_x(HULL, 1, z, 6, 1, HULL_TABLE, 3)
step()


# ---------------------------------------------------------------------------
# RADAR ISLAND — offset to starboard (z5..7) so the deck stays clear.
# ---------------------------------------------------------------------------
for z in range(5, 8):                                  # base x16..24
    fill_row(SUPER, list(range(16, 25)), z, DKY, BRICK_X, 3)
mark9(16, 5, 9, 3)
for z in range(5, 8):                                  # mid x17..22
    fill_row(SUPER, list(range(17, 23)), z, DKY + 3, BRICK_X, 3)
for z in range(6, 8):                                  # dark sensor top x18..20
    fill_row(RADAR, list(range(18, 21)), z, DKY + 6, BRICK_X, 3)
place_block(FUNNEL, 23, 5, 2, 2, DKY + 3, 3, ROUND2_BRICK)   # funnel on base top
place_block(CAP, 23, 5, 2, 2, DKY + 6, 1, TILE_2x2)
step()

# Mast + rotating radar on the island top.
place_block(MAST, 19, 6, 1, 1, DKY + 9, 3, ROUND1_BRICK)
place_block(MAST, 19, 6, 1, 1, DKY + 12, 3, ROUND1_BRICK)
place_barrel(RADAR, 19, 6, DKY + 15, 4, root='lo')           # air-search radar boom
place_barrel(RADAR, 18, 7, DKY + 9, 3, root='lo')            # surface-search radar (on the dark top)
step()


# ---------------------------------------------------------------------------
# MISSILES — forward vertical-launch battery + bow gun.
# ---------------------------------------------------------------------------
for z in range(2, 6):                                  # VLS deck block x33..36
    fill_row(SUPER, list(range(33, 37)), z, DKY, BRICK_X, 3)
mark9(33, 2, 4, 4)
for x in range(33, 37):                                # 4 x 2 missiles
    for z in (3, 4):
        place_block(M_BODY, x, z, 1, 1, DKY + 3, 3, ROUND1_BRICK)
        place_block(M_TIP, x, z, 1, 1, DKY + 6, 3, CONE1)
place_block(GUN, 38, 3, 2, 2, DKY, 3, ROUND2_BRICK)    # bow gun (full-height deck)
for z in (3, 4):
    place_barrel(GUN, 39, z, DKY + 3, 3, root='lo')    # rooted on the gun, rakes over the prow
mark9(38, 3, 2, 2)
step()


# ---------------------------------------------------------------------------
# JETS — three parked delta jets on the flight deck (flat, on studded patches).
# ---------------------------------------------------------------------------
def jet(x0, zc):
    """Flat delta jet, nose toward +X, on a studded deck patch (cells -> used9)."""
    place_x(JET, x0, zc, DKY, 4, PLATE_X, 1)               # fuselage (1x4)
    for dz in (-1, 1):                                     # mid wing
        place_block(JET, x0 + 1, zc + dz, 1, 1, DKY, 1, ROUND1_PLATE)
    for dz in (-2, -1, 1, 2):                              # rear wing (wider delta)
        place_block(JET, x0, zc + dz, 1, 1, DKY, 1, ROUND1_PLATE)
    place_block(JET_TRIM, x0 + 2, zc, 1, 1, DKY + 1, 1, ROUND1_PLATE)   # cockpit
    place_block(JET_TRIM, x0, zc, 1, 1, DKY + 1, 1, ROUND1_PLATE)       # tail fin
    for dz in (-2, -1, 0, 1, 2):
        mark9(x0, zc + dz, 1, 1)
    mark9(x0 + 1, zc - 1, 1, 1); mark9(x0 + 1, zc + 1, 1, 1)
    for i in range(4):
        mark9(x0 + i, zc, 1, 1)


jet(5, 2)
jet(11, 2)
jet(26, 2)
step()


# ---------------------------------------------------------------------------
# RUNWAY markings — white centreline dashes + an aft helipad "H".
# ---------------------------------------------------------------------------
MARK = {}
for x in (3, 4, 9, 16, 20, 24, 30, 32):       # centreline dashes (z2), clear of jets
    MARK[(x, 2)] = MARK_C
for c in [(2, 4), (3, 4), (4, 4), (2, 6), (3, 6), (4, 6), (3, 5)]:   # aft helipad "H"
    MARK[c] = MARK_C
for (x, z), col in MARK.items():
    if x in BODY and (x, z) in hull_cells and (x, z) not in used9:
        place_block(col, x, z, 1, 1, DKY, 1, TILE_X[1])
        used9.add((x, z))
step()

# Deck-edge railings (skip the open flight deck so the runway reads clear).
for z in (0, 7):
    for x in range(LEN):
        if (x, z) in hull_cells and (x, z) not in used9 and x % 2 == 0 and x > 13:
            place_block(RAIL, x, z, 1, 1, DKY, 1, ROUND1_PLATE)
            used9.add((x, z))
step()

# Flight-deck plating — smooth tiles over the flat body deck (level 9). The bow
# and stern caps are sloped surfaces, so they get no tiles.
for z in range(8):
    xs = [x for x in BODY if (x, z) in hull_cells and (x, z) not in used9]
    fill_row(DECK, xs, z, DKY, TILE_X, 1)
step()


# ---------------------------------------------------------------------------
# Assemble + report.
# ---------------------------------------------------------------------------
header = ["0 Missile Ship", "0 Name: missileship.ldr", "0 Author: BrickBuilder", "0 !LDRAW_ORG Model"]
out_lines = header + lines
while out_lines and out_lines[-1].strip() == "0 STEP":
    out_lines.pop()
out = "\n".join(out_lines) + "\n"
parts = sum(1 for l in out_lines if l.startswith("1 "))
steps = sum(1 for l in out_lines if l.strip() == "0 STEP") + 1
with open("missileship.ldr", "w") as f:
    f.write(out)
print(f"parts={parts} steps={steps}")
