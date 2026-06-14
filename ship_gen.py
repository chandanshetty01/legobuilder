#!/usr/bin/env python3
"""Generate a validated military ship (gray destroyer) LDraw model for BrickBuilder.

Features: a boat-shaped hull that tapers to a bow, a dark waterline course, a
tiled deck, a stepped bridge superstructure, two funnels, a mast, fore + aft
main gun turrets with cantilevered barrels, deck-edge railings and AA guns.

Grid conventions (matching index.html), worked in PLATE levels (8 LDU):
  - 1 stud = 20 LDU on X/Z; origin at footprint centre. +Y is DOWN (up = -Y).
  - brick = 3 plate-levels (24 LDU); plate/tile = 1 level (8 LDU).
  - A part with bottom at plate-level pb and height hp has origin (TOP) at
    Y = -8*(pb+hp).  Cell below pb is pb-1.  pb==0 rests on the baseplate.

Built bottom-up; every part is overlap-checked and support-checked. The only
cantilevers are the gun barrels, whose rooted (inner) stud rests on the turret.
"""

BRICK_X = {8: '3008.dat', 6: '3009.dat', 4: '3010.dat', 3: '3622.dat', 2: '3004.dat', 1: '3005.dat'}
# Hull uses shorter bricks: more parts, and the staggered short courses read as
# riveted hull plating rather than one smooth slab.
HULL_TABLE = {4: '3010.dat', 3: '3622.dat', 2: '3004.dat', 1: '3005.dat'}
TILE_X  = {4: '2431.dat', 2: '3069b.dat', 1: '3070b.dat'}
PLATE_X = {4: '3710.dat', 3: '3623.dat', 2: '3023.dat', 1: '3024.dat'}
ROUND2_BRICK = '3941.dat'   # 2x2 round brick (funnel)
ROUND1_BRICK = '3062b.dat'  # 1x1 round brick (mast / AA gun)
ROUND1_PLATE = '4073.dat'   # 1x1 round plate (railing stanchion / cap)
TILE_2x2     = '3068b.dat'
PLATE_2x2    = '3022.dat'

# LDraw colours (all standard): 7 light grey, 72 dark bluish grey, 0 black, 4 red.
HULL, WATER, DECK, SUPER, TURRET, BARREL, FUNNEL, CAP, RAIL = 7, 72, 72, 7, 72, 0, 72, 0, 7

occ = {}            # (x, z, level) -> True
lines = []
hull_cells = set()  # (x,z) columns that form the hull (deck top available)
used9 = set()        # (x,z) deck cells already occupied at the deck level


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------
def emit(color, cx, cz, pb, hp, part):
    X = 20 * cx
    Z = 20 * cz
    Y = -8 * (pb + hp)
    lines.append(f"1 {color} {X:g} {Y} {Z:g} 1 0 0 0 1 0 0 0 1 {part}")


def occupy(cells, pb, hp, cantilever_root=None):
    for (x, z) in cells:
        for k in range(hp):
            assert (x, z, pb + k) not in occ, f"overlap at {(x, z, pb + k)}"
    if pb > 0:
        if cantilever_root is not None:
            rx, rz = cantilever_root
            assert (rx, rz, pb - 1) in occ, f"cantilever root unsupported {cantilever_root}"
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


def place_barrel(color, x0, z, pb, length, root):
    """1xlength plate cantilevered along X; `root` is the supported inner stud."""
    cells = [(x0 + i, z) for i in range(length)]
    rx = x0 if root == 'lo' else x0 + length - 1
    occupy(cells, pb, 1, cantilever_root=(rx, z))
    emit(color, x0 + (length - 1) / 2, z, pb, 1, PLATE_X[length])


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


def step():
    lines.append("0 STEP")


# ---------------------------------------------------------------------------
# Hull plan — length along X (bow at +X), width tapering toward the bow.
# ---------------------------------------------------------------------------
LEN = 36


def hull_zs(x):
    if x < 0 or x > LEN - 1:
        return []
    if x <= 25:   return list(range(0, 6))   # w6  (z0..5)  full beam
    if x <= 29:   return list(range(1, 5))   # w4  (z1..4)
    return list(range(2, 4))                  # w2  (z2..3)  bow


for x in range(LEN):
    for z in hull_zs(x):
        hull_cells.add((x, z))

DKY = 12   # deck surface plate-level (hull = 4 brick courses: levels 0..11)

# 1. Hull courses (waterline course dark), staggered bond.  pb = 0, 3, 6.
for course, pb in enumerate((0, 3, 6, 9)):
    col = WATER if course == 0 else HULL
    for z in range(6):
        xs = [x for x in range(LEN) if z in hull_zs(x)]
        fill_row(col, xs, z, pb, HULL_TABLE, 3, phase=course % 2)
    step()


def mark9(x0, z0, w, d):
    for i in range(w):
        for j in range(d):
            used9.add((x0 + i, z0 + j))


# ---------------------------------------------------------------------------
# 2. Superstructure — stepped bridge amidships.
# ---------------------------------------------------------------------------
# Deckhouse (level 9): x12..21, z1..4
for z in range(1, 5):
    fill_row(SUPER, list(range(12, 22)), z, DKY, BRICK_X, 3)
mark9(12, 1, 10, 4)
# Bridge (level 12): x14..19, z1..4
for z in range(1, 5):
    fill_row(SUPER, list(range(14, 20)), z, DKY + 3, BRICK_X, 3)
# Bridge windows band (black tile strip on the bridge front, level 12)
# Bridge top (level 15): x15..17, z2..3
for z in range(2, 4):
    fill_row(SUPER, list(range(15, 18)), z, DKY + 6, BRICK_X, 3)
step()

# Funnels — 2x2 round bricks on the deckhouse top (level 12), capped black.
for fx in (12, 20):
    place_block(FUNNEL, fx, 2, 2, 2, DKY + 3, 3, ROUND2_BRICK)   # on deckhouse top
    place_block(CAP, fx, 2, 2, 2, DKY + 6, 1, TILE_2x2)
# Mast — stacked round bricks on the bridge top, capped.
place_block(SUPER, 16, 2, 1, 1, DKY + 9, 3, ROUND1_BRICK)
place_block(SUPER, 16, 2, 1, 1, DKY + 12, 3, ROUND1_BRICK)
place_block(RAIL, 16, 2, 1, 1, DKY + 15, 1, ROUND1_PLATE)
step()


# ---------------------------------------------------------------------------
# 3. Gun turrets with cantilevered barrels.
# ---------------------------------------------------------------------------
def turret(x0, z0, pb, facing):
    """2x2 turret block at pb; two barrels (length 4) cantilevered toward bow
    (facing='bow', +X) or stern (facing='stern', -X)."""
    place_block(TURRET, x0, z0, 2, 2, pb, 3, '3003.dat')           # 2x2 brick body
    top = pb + 3
    for z in (z0, z0 + 1):
        if facing == 'bow':
            place_barrel(BARREL, x0 + 1, z, top, 4, root='lo')     # inner stud over turret
        else:
            place_barrel(BARREL, x0 - 3, z, top, 4, root='hi')


# Aft main turret (fires astern) and a superfiring turret behind it.
turret(8, 2, DKY, 'stern')
mark9(8, 2, 2, 2)
# Fore main turret (fires forward) + superfiring turret.
turret(26, 2, DKY, 'bow')
mark9(26, 2, 2, 2)
step()

# Superfiring turrets, raised one brick on a 2x2 pedestal (between the main
# turret and the superstructure, clear of the deckhouse at x12..21).
for (px, facing) in ((10, 'stern'), (23, 'bow')):
    place_block(TURRET, px, 2, 2, 2, DKY, 3, '3003.dat')         # pedestal
    mark9(px, 2, 2, 2)
    turret(px, 2, DKY + 3, facing)
step()


# ---------------------------------------------------------------------------
# 4. Deck details — AA guns near the bridge, depth-charge racks at the stern.
# ---------------------------------------------------------------------------
# AA guns on the deckhouse-top corners (level 12), clear of bridge + funnels.
for (ax, az) in ((12, 1), (12, 4), (21, 1), (21, 4)):
    place_block(BARREL, ax, az, 1, 1, DKY + 3, 3, ROUND1_BRICK)
for (dx, dz) in ((2, 1), (2, 4), (3, 1), (3, 4)):
    if (dx, dz) not in used9:
        place_block(TURRET, dx, dz, 1, 1, DKY, 1, ROUND1_PLATE)
        used9.add((dx, dz))
step()


# ---------------------------------------------------------------------------
# 5. Railings — round-plate stanchions along both deck edges (z0, z5).
# ---------------------------------------------------------------------------
for z in (0, 5):
    for x in range(LEN):
        if (x, z) in hull_cells and (x, z) not in used9:
            place_block(RAIL, x, z, 1, 1, DKY, 1, ROUND1_PLATE)
            used9.add((x, z))
step()

# ---------------------------------------------------------------------------
# 6. Deck plating — tiles over every remaining hull-top cell.
# ---------------------------------------------------------------------------
for z in range(6):
    xs = [x for x in range(LEN) if (x, z) in hull_cells and (x, z) not in used9]
    fill_row(DECK, xs, z, DKY, TILE_X, 1)
step()


# ---------------------------------------------------------------------------
# Assemble + report.
# ---------------------------------------------------------------------------
header = ["0 Military Ship", "0 Name: ship.ldr", "0 Author: BrickBuilder", "0 !LDRAW_ORG Model"]
out_lines = header + lines
while out_lines and out_lines[-1].strip() == "0 STEP":
    out_lines.pop()
out = "\n".join(out_lines) + "\n"

parts = sum(1 for l in out_lines if l.startswith("1 "))
steps = sum(1 for l in out_lines if l.strip() == "0 STEP") + 1
with open("ship.ldr", "w") as f:
    f.write(out)
print(f"parts={parts} steps={steps}")
