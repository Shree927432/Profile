"""2D ornament sheet for the upright piano: three levels of Polyphia-style ornament
(black and gold, filigree, a branch motif of our own) on the approved piano.

Plain Python (no Blender). It reuses the front elevation from piano_design_sheet.py,
so proportions match the approved sheet, and draws every ornament in the piano's own
metres on top of it. Writes an HTML page with one SVG and renders it to a PNG with
the cached headless Chromium. Run from the repo root:

    python3 blender/design/piano_ornament_sheet.py

Output: video-local/footage/2026-10-22-piano-quality-test/piano-ornament-sheet.{html,png}

The motif is ours: a Baroque scroll-vine (rinceau) that branches like a family tree,
the room's evolution of music. No copied artwork, no text, no logos.
"""
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import piano_design_sheet as D  # noqa: E402  (front elevation, View, text helpers)
from lib import constants as C  # noqa: E402
from lib.piano_layout import sheet_line  # noqa: E402

P, KT = C.PIANO, C.KT
OUT = D.OUT
W_PX, H_PX = 2400, 1950
add, text = D.add, D.text
INK, MUTED, ACC, PAPER = D.INK, D.MUTED, D.ACC, D.PAPER

# Ornament colours (sRGB). Hardware gold is the old brass pushed a little yellower;
# inlay gold sits under the clear coat, so it is a touch deeper.
GOLD_HW = "#cda24c"
GOLD_IN = "#b8913f"
PEARL = "#e6e3ea"
SILK = "#3b2738"
LACQ = C.COL["lacquer_black"]
RELIEF, RELIEF_HI = "#18191e", "#6b7387"
KIND = dict(gold=GOLD_IN, hw=GOLD_HW, pearl=PEARL, relief=RELIEF, lacq="#0c0c0f")

# Rendered style for the black piano (the front() drawing reads these keys).
DARK = dict(D.TECH, case="#0c0c0e", recess="#070709", inset="#121217", stroke="#2e323d", sw=0.9,
            white="#efe8d8", black="#141312", paper="#fbf9f3", cup="#1c1c1e", brass=GOLD_HW)

# Bench, as built in blender/props/obj_piano.py build_bench() (not yet in constants.py).
BENCH = dict(w=0.80, h=0.49, t=0.045, apron=0.075, leg_x=0.35, leg_top=0.048, leg_bot=0.032)

FIELD_UP = (-P["inset_half_w"], P["inset_half_w"], P["inset_bottom"], P["inset_top"])
FIELD_LO = (-P["lower_inset_half_w"], P["lower_inset_half_w"], P["lower_inset_bottom"], P["lower_inset_top"])
CHEEK_IN = 0.6125
(_, SHEET_Z0), (_, SHEET_Z1) = sheet_line()


# ---------------------------------------------------------------------------
# motif engine: tapering scroll-vines, leaves, dots, all in metres (x right, z up)
# ---------------------------------------------------------------------------
def centreline(x, y, h_deg, L, w0, bend=0.0, curl=1, cfrac=0.42, turns=0.9, taper=0.8, n=64):
    """A stem that bends gently, then rolls into a tightening curl.
    bend: total turn (radians, + is counter-clockwise) over the straight part.
    curl: +1 rolls counter-clockwise, -1 clockwise. Returns [(x, y, width, heading)]."""
    pts, h = [], math.radians(h_deg)
    Ls, Lc = L * (1 - cfrac), L * cfrac
    r0 = Lc * 1.848 / (turns * 2 * math.pi) if turns > 0 else 1e9
    ds = L / n
    for i in range(n + 1):
        s = i * ds
        pts.append((x, y, w0 * (1 - taper * s / L), h))
        if s < Ls or turns <= 0:
            k = bend / max(Ls, 1e-9)
        else:
            k = curl / (r0 * (1 - 0.75 * (s - Ls) / Lc))
        h += k * ds
        x += math.cos(h) * ds
        y += math.sin(h) * ds
    return pts


def ribbon(pts, ball=True):
    left = [(x - math.sin(h) * w / 2, y + math.cos(h) * w / 2) for x, y, w, h in pts]
    right = [(x + math.sin(h) * w / 2, y - math.cos(h) * w / 2) for x, y, w, h in pts]
    polys = [left + right[::-1]]
    if ball:
        x, y, w, _ = pts[-1]
        polys.append(circle(x, y, w * 0.95))
    return polys


def circle(x, y, r, n=18):
    return [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def leaf_poly(x, y, h_deg, l, w, n=10):
    """A teardrop leaf from (x, y) pointing along h_deg, slightly bent."""
    h = math.radians(h_deg)
    ux, uy, nx, ny = math.cos(h), math.sin(h), -math.sin(h), math.cos(h)
    side = []
    for sgn in (1, -1):
        for i in range(n + 1):
            t = i / n if sgn > 0 else 1 - i / n
            a = t * l
            b = sgn * w / 2 * math.sin(math.pi * t ** 0.8) * (1 - 0.25 * t) + 0.12 * w * math.sin(math.pi * t)
            side.append((x + ux * a + nx * b, y + uy * a + ny * b))
    return side


class Motif:
    def __init__(self):
        self.items = []                         # (polygon, kind)

    def vine(self, x, y, h, L, w0, kind="gold", ball=True, **kw):
        pts = centreline(x, y, h, L, w0, **kw)
        self.items += [(p, kind) for p in ribbon(pts, ball)]
        return pts

    def child(self, parent, f, dh, L, w0, kind="gold", **kw):
        x, y, _, h = parent[min(len(parent) - 1, int(f * (len(parent) - 1)))]
        return self.vine(x, y, math.degrees(h) + dh, L, w0, kind, **kw)

    def leaf(self, parent, f, dh, l, w, kind="pearl"):
        x, y, _, h = parent[min(len(parent) - 1, int(f * (len(parent) - 1)))]
        self.items.append((leaf_poly(x, y, math.degrees(h) + dh, l, w), kind))

    def leaf_at(self, x, y, h, l, w, kind="pearl"):
        self.items.append((leaf_poly(x, y, h, l, w), kind))

    def dot(self, x, y, r, kind="gold"):
        self.items.append((circle(x, y, r), kind))

    def emit(self, v, T=lambda x, y: (x, y), kinds=None, stroke="none", sw=0):
        kinds = kinds or {}
        for poly, kind in self.items:
            fill = kinds.get(kind, KIND[kind])
            st = stroke if kind in ("relief", "lacq") else "none"
            v.poly([T(x, y) for x, y in poly], fill, st, sw if st != "none" else 0)


def mirror2(m, v, dx=0.0, dz=0.0, s=1.0, **kw):
    """Emit a right-half motif and its mirror, about x = dx, shifted up by dz, scaled s."""
    m.emit(v, lambda x, y: (dx + x * s, dz + y * s), **kw)
    m.emit(v, lambda x, y: (dx - x * s, dz + y * s), **kw)


# --- the motifs ---------------------------------------------------------------
def emblem_half(pearl=True):
    """The seed: right half of the fallboard emblem, centred on (0, 0). About 17 x 6 cm whole."""
    m = Motif()
    main = m.vine(0.009, 0.002, 12, 0.085, 0.0036, bend=-0.55, curl=-1, cfrac=0.45, turns=0.95)
    m.child(main, 0.30, 58, 0.038, 0.0024, bend=0.25, curl=1, cfrac=0.55, turns=0.9)
    m.leaf(main, 0.56, -62, 0.015, 0.0062, "gold")
    m.leaf(main, 0.12, 70, 0.012, 0.005, "gold")
    m.leaf_at(0.004, -0.009, -35, 0.012, 0.0045, "gold")
    return m


def emblem_centre(pearl=True):
    m = Motif()
    m.leaf_at(0, -0.010, 90, 0.032, 0.0125, "pearl" if pearl else "gold")
    m.dot(0, -0.013, 0.0034, "gold")
    return m


def corner(ax, ay, w=0.0026):
    """Corner flourish with the corner at (0, 0) and the field toward +x, +y."""
    m = Motif()
    a = m.vine(0.004, 0.004, 0, ax, w, bend=0.30, curl=1, cfrac=0.34, turns=0.8)
    b = m.vine(0.004, 0.004, 90, ay, w, bend=-0.30, curl=-1, cfrac=0.34, turns=0.8)
    m.child(a, 0.42, 62, ax * 0.32, w * 0.7, bend=0.1, curl=-1, cfrac=0.6, turns=0.85)
    m.child(b, 0.42, -62, ay * 0.32, w * 0.7, bend=-0.1, curl=1, cfrac=0.6, turns=0.85)
    d = min(ax, ay)
    m.leaf_at(0.006, 0.006, 45, d * 0.30, d * 0.11, "gold")
    m.dot(0.0035, 0.0035, w * 0.9, "gold")
    return m


def band(x0, x1, h, kind="gold"):
    """Running scroll band centred on y = 0, h tall: a waving stem with curls
    alternating above and below (the lip fretwork and the lid edge)."""
    m = Motif()
    Pd = h * 1.75
    n = max(8, int((x1 - x0) / Pd * 40))
    amp, w = 0.10 * h, 0.095 * h
    stem = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        ph = 2 * math.pi * (x - x0) / Pd
        stem.append((x, amp * math.sin(ph), w, math.atan2(amp * 2 * math.pi / Pd * math.cos(ph), 1)))
    m.items += [(p, kind) for p in ribbon(stem, ball=False)]
    k = 0
    while True:
        xc = x0 + Pd / 4 + k * Pd / 2
        if xc > x1 - Pd * 0.6:
            break
        side = 1 if k % 2 == 0 else -1
        y = amp * math.sin(2 * math.pi * (xc - x0) / Pd)
        m.vine(xc, y, side * 40, 0.80 * h, w * 0.9, kind, curl=side, cfrac=0.72, turns=1.15, taper=0.55)
        m.leaf_at(xc - Pd * 0.20, y * 0.6, 180 - side * 130, 0.24 * h, 0.10 * h, kind)
        k += 1
    return m


def panel_branch_half():
    """Full: the big branch, right half, in field coordinates (x from centre, y from the
    field's middle line). It grows out from behind the music."""
    m = Motif()
    main = m.vine(0.175, 0.004, 3, 0.335, 0.0060, bend=-0.10, curl=-1, cfrac=0.20, turns=0.95, taper=0.75)
    c1 = m.child(main, 0.16, 46, 0.085, 0.0038, bend=-0.35, curl=-1, cfrac=0.42, turns=0.9)
    m.child(c1, 0.40, 52, 0.030, 0.0022, curl=1, cfrac=0.6, turns=0.8)
    c2 = m.child(main, 0.33, -48, 0.075, 0.0034, bend=0.35, curl=1, cfrac=0.42, turns=0.9)
    m.child(c2, 0.45, -50, 0.026, 0.002, curl=-1, cfrac=0.6, turns=0.8)
    m.child(main, 0.52, 44, 0.060, 0.0030, bend=-0.3, curl=-1, cfrac=0.45, turns=0.9)
    m.child(main, 0.68, -44, 0.048, 0.0026, bend=0.3, curl=1, cfrac=0.48, turns=0.9)
    for f, dh, l in ((0.06, 68, 0.017), (0.25, -70, 0.016), (0.43, 66, 0.015), (0.60, -64, 0.013), (0.76, 60, 0.011)):
        m.leaf(main, f, dh, l, l * 0.42, "pearl")
    m.leaf(c1, 0.22, -60, 0.012, 0.005, "pearl")
    m.leaf(c2, 0.22, 60, 0.011, 0.0046, "pearl")
    return m


def console_vine(L):
    """Full: a carved vine down a console face, from a scroll at the top (local x = 0 is
    the face centre, y = 0 the top of the console)."""
    m = Motif()
    top = m.vine(-0.012, -0.004, -20, 0.050, 0.0070, "relief", bend=0.4, curl=1, cfrac=0.55, turns=1.0)
    stem = m.vine(0.0, -0.030, -90, L, 0.0075, "relief", bend=0.0, curl=1, cfrac=0.10, turns=0.7, taper=0.6)
    for i, f in enumerate((0.14, 0.30, 0.46, 0.62, 0.78)):
        side = 1 if i % 2 == 0 else -1
        m.child(stem, f, side * 38, 0.034, 0.0042, "relief", curl=side, cfrac=0.6, turns=0.95)
    del top
    return m


def cheek_scroll():
    """Full: a C-scroll in relief on the right cheek's front (local origin at the cheek's
    inner bottom corner)."""
    m = Motif()
    s = m.vine(0.020, 0.010, 72, 0.175, 0.011, "relief", bend=-0.55, curl=-1, cfrac=0.42, turns=1.05, taper=0.7)
    m.child(s, 0.35, -58, 0.050, 0.006, "relief", curl=1, cfrac=0.6, turns=0.95)
    m.leaf(s, 0.18, 62, 0.030, 0.012, "relief")
    return m


# ---------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------
def notched_rect(v, x0, x1, z0, z1, r, stroke, sw_m, clip=None):
    """A pinstripe rectangle with concave (notched) corners, line width sw_m metres."""
    def P_(u, w):
        return v.p(u, w)
    pts = [P_(x0 + r, z0), P_(x1 - r, z0), P_(x1, z0 + r), P_(x1, z1 - r), P_(x1 - r, z1), P_(x0 + r, z1),
           P_(x0, z1 - r), P_(x0, z0 + r)]
    rp = r * v.s * 1000
    d = (f"M{pts[0][0]:.1f},{pts[0][1]:.1f} L{pts[1][0]:.1f},{pts[1][1]:.1f} "
         f"A{rp:.1f},{rp:.1f} 0 0 1 {pts[2][0]:.1f},{pts[2][1]:.1f} L{pts[3][0]:.1f},{pts[3][1]:.1f} "
         f"A{rp:.1f},{rp:.1f} 0 0 1 {pts[4][0]:.1f},{pts[4][1]:.1f} L{pts[5][0]:.1f},{pts[5][1]:.1f} "
         f"A{rp:.1f},{rp:.1f} 0 0 1 {pts[6][0]:.1f},{pts[6][1]:.1f} L{pts[7][0]:.1f},{pts[7][1]:.1f} "
         f"A{rp:.1f},{rp:.1f} 0 0 1 {pts[0][0]:.1f},{pts[0][1]:.1f} Z")
    add(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{max(0.6, sw_m * v.s * 1000):.2f}"/>')


def hline(v, x0, x1, z, colour, sw_m):
    v.line((x0, z), (x1, z), colour, max(0.6, sw_m * v.s * 1000))


def escutcheon(v, x, z, w=0.022, h=0.038):
    pts = []
    for i in range(40):
        t = 2 * math.pi * i / 40
        yy = math.sin(t)
        hw = w / 2 * (1 - abs(yy) ** 2.2) ** 0.75
        pts.append((x + math.copysign(hw, math.cos(t)), z + yy * h / 2))
    v.poly(pts, GOLD_HW, "#6d5420", 0.6)
    v.circle(x, z + 0.004, 0.0028, "#050505", "none", 0)
    v.poly([(x - 0.0012, z + 0.003), (x + 0.0012, z + 0.003), (x + 0.002, z - 0.008), (x - 0.002, z - 0.008)],
           "#050505", "none", 0)


def wrap(x, y, s, chars, size=14, fill=INK, lh=None, weight=400):
    lh = lh or size + 5
    line = ""
    for wd in s.split():
        if len(line) + len(wd) + 1 > chars and line:
            text(x, y, line, size, fill, weight=weight)
            y += lh
            line = ""
        line = (line + " " + wd).strip()
    if line:
        text(x, y, line, size, fill, weight=weight)
        y += lh
    return y


def clip_not_sheet(cid, v, box):
    """clipPath: the box (page px) minus the music sheet, so ornament stays behind it."""
    sx0, sy0 = v.p(-P["sheet_w"] / 2, SHEET_Z1)
    sx1, sy1 = v.p(P["sheet_w"] / 2, SHEET_Z0)
    x0, y0, x1, y1 = box
    add(f'<clipPath id="{cid}"><path clip-rule="evenodd" d="M{x0},{y0} H{x1} V{y1} H{x0} Z '
        f'M{sx0:.1f},{sy0:.1f} H{sx1:.1f} V{sy1:.1f} H{sx0:.1f} Z"/></clipPath>')


# ---------------------------------------------------------------------------
# the ornament, by level, in the piano's metres
# ---------------------------------------------------------------------------
def ornament_behind_sheet(v, lvl):
    """Everything above the music rest that the sheet must cover."""
    sw = 0.0025
    # crown moulding pinstripe
    hline(v, -P["width"] / 2 - P["crown_proud"] + 0.012, P["width"] / 2 + P["crown_proud"] - 0.012,
          P["case_top"] - P["crown_h"] / 2, GOLD_IN, sw)
    # upper field pinstripe
    x0, x1, z0, z1 = FIELD_UP
    ins = 0.010
    notched_rect(v, x0 + ins, x1 - ins, z0 + ins, z1 - ins, 0.012, GOLD_IN, sw)
    if lvl >= 2:
        for sx in (-1, 1):
            for sz in (-1, 1):
                cx = (x0 if sx < 0 else x1) - sx * 0.020
                cz = (z0 if sz < 0 else z1) - sz * 0.020
                corner(0.085, 0.040).emit(v, lambda x, y, cx=cx, cz=cz, sx=sx, sz=sz: (cx - sx * x, cz - sz * y))
        # lid front edge: running scroll
        lz = P["case_top"] + P["lid_t"] / 2
        lw = P["width"] / 2 + P["lid_over_side"] - 0.020
        band(-lw, lw, P["lid_t"] * 0.62).emit(v, lambda x, y: (x, lz + y))
    if lvl >= 3:
        mid = (z0 + z1) / 2
        mirror2(panel_branch_half(), v, dz=mid)


def ornament_front(v, lvl):
    """Everything else, drawn over the front elevation."""
    sw = 0.0025
    # music rest lip, redrawn in front of the sheet's bottom edge
    hw, lz0, lz1 = P["ledge_half_w"], P["ledge_z"], P["ledge_lip_top"]
    v.rect(-hw, hw, lz0, lz1, DARK["case"], DARK["stroke"], DARK["sw"], rx=2)
    if lvl >= 2:
        rail = 0.0045
        v.rect(-hw + 0.012, hw - 0.012, lz0 + rail, lz1 - rail, SILK, "none", 0)
        b = band(-hw + 0.016, hw - 0.016, (lz1 - lz0) - 2 * rail - 0.002, "lacq")
        b.emit(v, lambda x, y: (x, (lz0 + lz1) / 2 + y), stroke="#666d80", sw=0.6)
        hline(v, -hw + 0.008, hw - 0.008, lz0 + rail * 0.55, GOLD_IN, 0.0018)
        hline(v, -hw + 0.008, hw - 0.008, lz1 - rail * 0.55, GOLD_IN, 0.0018)
    # fallboard emblem, centred on the face seen when open
    fz = (KT + 0.022 + 0.934) / 2
    mirror2(emblem_half(), v, dz=fz)
    emblem_centre().emit(v, lambda x, y: (x, fz + y))
    # lower field pinstripe
    x0, x1, z0, z1 = FIELD_LO
    notched_rect(v, x0 + 0.012, x1 - 0.012, z0 + 0.012, z1 - 0.012, 0.018, GOLD_IN, sw)
    # lock escutcheon on the key slip
    escutcheon(v, 0, KT - 0.045)
    if lvl >= 2:
        for sx in (-1, 1):
            for sz in (-1, 1):
                cx = (x0 if sx < 0 else x1) - sx * 0.026
                cz = (z0 if sz < 0 else z1) - sz * 0.026
                corner(0.13, 0.11, 0.0032).emit(v, lambda x, y, cx=cx, cz=cz, sx=sx, sz=sz: (cx - sx * x, cz - sz * y))
        # gold key-cheek caps over the rounded noses
        n = P["cheek_nose"]
        for sx in (-1, 1):
            v.rect(sx * (CHEEK_IN + 0.010), sx * (P["width"] / 2 - 0.010), n - 0.007, n + 0.007, GOLD_HW,
                   "#6d5420", 0.5, rx=3)
            for k in range(3):
                xx = sx * (CHEEK_IN + 0.045 + k * 0.03)
                v.line((xx, n - 0.004), (xx + sx * 0.006, n + 0.004), "#8a6a2c", 0.5)
    if lvl >= 3:
        # pearl fronts on the white keys
        for m, kind, xl, xr, _, _ in D.KEYS:
            if kind == "w":
                v.rect(xl, xr, KT - P["white_h"], KT - 0.002, PEARL, "#9d97a6", 0.4, rx=0.6)
        # relief: cheek scrolls (mirrored) and console vines
        rk = dict(stroke=RELIEF_HI, sw=0.6)
        cs = cheek_scroll()
        cb = P["cheek_bottom"]
        cs.emit(v, lambda x, y: (CHEEK_IN + x, cb + y), **rk)
        cs.emit(v, lambda x, y: (-CHEEK_IN - x, cb + y), **rk)
        cv = console_vine(P["cheek_bottom"] - P["toe_rail_top"] - 0.10)
        for sx in (-1, 1):
            cx = sx * P["toe_x"]
            cv.emit(v, lambda x, y, cx=cx, sx=sx: (cx + sx * x, cb - 0.004 + y), **rk)
        # engraved pedals
        for x in P["pedal_x"]:
            v.line((x - 0.011, P["pedal_z"] + 0.006), (x + 0.011, P["pedal_z"] + 0.006), "#7a5c22", 0.7)


def draw_bench(v, lvl):
    B = BENCH
    hw = B["w"] / 2
    st, sw = DARK["stroke"], DARK["sw"]
    for sx in (-1, 1):
        lx = sx * B["leg_x"]
        v.poly([(lx - B["leg_bot"] / 2, 0), (lx + B["leg_bot"] / 2, 0), (lx + B["leg_top"] / 2, B["h"] - B["t"]),
                (lx - B["leg_top"] / 2, B["h"] - B["t"])], DARK["case"], st, sw)
    v.rect(-B["leg_x"], B["leg_x"], B["h"] - B["t"] - B["apron"], B["h"] - B["t"], DARK["recess"], st, sw)
    v.rect(-hw, hw, B["h"] - B["t"], B["h"], DARK["case"], st, sw, rx=3)
    if lvl >= 3:
        az0, az1 = B["h"] - B["t"] - B["apron"], B["h"] - B["t"]
        notched_rect(v, -B["leg_x"] + 0.04, B["leg_x"] - 0.04, az0 + 0.010, az1 - 0.010, 0.010, GOLD_IN, 0.0025)
        mid = (az0 + az1) / 2 + 0.004
        mirror2(emblem_half(), v, dz=mid, s=0.62)
        emblem_centre().emit(v, lambda x, y: (x * 0.62, mid + y * 0.62))


# ---------------------------------------------------------------------------
# page
# ---------------------------------------------------------------------------
LEVELS = [
    dict(n=1, name="Light", sub="gold hardware, a pinstripe, one motif",
         items=[("Hardware in polished gold: pedals, castors, the three lid hinges (on top, seen in three-quarter)", "M"),
                ("Lock escutcheon: a small pointed oval plate with a keyhole, on the key slip", "G"),
                ("Gold pinstripe, 2.5 mm, notched corners, on both raised fields and the top moulding", "G"),
                ("The seed motif centred on the fallboard: two scrolls and a pearl bud, on the face you see "
                 "when it is open, where a maker's name would sit", "T")],
         cost="About +0.4k triangles (escutcheon; pinstripes as thin decal strips so they stay sharp at any "
              "bake size). No new texture file: the motif goes in the fallboard's existing bake.",
         fit="Shares only the gold. The branch is small and shows only in the keys close-up, so from the "
             "room the piano and guitar_06 read as unrelated."),
    dict(n=2, name="Medium", sub="Light, plus filigree, a pierced rest, cheek caps, the lid edge",
         items=[("Gold filigree in the 8 corners of the upper and lower fields, inside the pinstripe", "T"),
                ("Music rest lip in pierced fretwork of the running scroll, backed with dark silk, "
                 "gold rail lines. The silk shows through, so no transparency is needed", "T"),
                ("Key-cheek caps in polished gold over the rounded noses, three engraved lines", "M"),
                ("Lid front edge: a fine running scroll in gold (the sheet hides its middle)", "T")],
         cost="About +0.5k triangles in all. One new 2048 x 1024 front-of-case texture at about 1 mm per "
              "texel (fields, lip), roughly 0.5 MB as KTX2; the lid edge goes in the lid's own bake.",
         fit="Same stroke, curl and leaf as the tree inlay planned for guitar_06's fretboard: across the "
             "room the gold corners and the guitar's pearl tree read as one hand."),
    dict(n=3, name="Full", sub="Medium, plus the big branch, relief, pearl keys, the bench",
         items=[("Branch inlay across the upper field, gold stems and pearl leaves, growing out from "
                 "behind the music", "T"),
                ("Scrollwork relief on the cheeks (fronts and outer arms) and a carved vine down each "
                 "console", "G"),
                ("Engraved pedals (see the hardware swatch)", "T"),
                ("Pearl fronts on the 52 white keys (gold is the louder option)", "M"),
                ("Bench: pinstripe and a smaller seed motif on the front apron", "T")],
         cost="About +8k triangles of sculpted relief (the piano from 51.5k to about 60k); the front texture "
              "doubles to 4096 x 1024 and the relief wants a normal map: about +2 MB on the 3 s 4G budget.",
         fit="The strongest echo of the guitar's tree, but the piano becomes the louder of the two and "
             "the branch competes with the About page on the music rest."),
]


def column(i, lv):
    cw, gap, top, ch = 764, 14, 112, 1306
    x0 = 40 + i * (cw + gap)
    D.panel(x0, top, cw, ch, f"{lv['n']} · {lv['name']}")
    text(x0 + 16 + 14 * len(lv["name"]) + 40, top + 30, lv["sub"], 15, MUTED)
    if lv["n"] == 2:
        add(f'<rect x="{x0 + cw - 150}" y="{top + 12}" width="134" height="26" rx="13" fill="{ACC}"/>')
        text(x0 + cw - 83, top + 30, "recommended", 14, "#fff", "middle", 600)

    # elevation card: dawn wall and oak floor
    ex0, ey0, ew, eh = x0 + 14, top + 48, cw - 28, 600
    floor_y = ey0 + eh - 34
    add(f'<rect x="{ex0}" y="{ey0}" width="{ew}" height="{eh}" fill="url(#wall)"/>')
    add(f'<rect x="{ex0}" y="{floor_y}" width="{ew}" height="34" fill="#3e281a"/>')
    s = 0.44
    v = D.View(x0 + cw / 2, floor_y, s)
    D.front(v, DARK)
    xa, ya = v.p(-P["width"] / 2 - 0.01, P["case_top"] + P["lid_t"])
    xb, yb = v.p(P["width"] / 2 + 0.01, P["floor_gap"])
    add(f'<rect x="{xa:.1f}" y="{ya:.1f}" width="{xb - xa:.1f}" height="{yb - ya:.1f}" fill="url(#gloss)" opacity=".55"/>')
    clip_not_sheet(f"nse{i}", v, (ex0, ey0, ex0 + ew, ey0 + eh))
    add(f'<g clip-path="url(#nse{i})">')
    ornament_behind_sheet(v, lv["n"])
    add("</g>")
    ornament_front(v, lv["n"])
    text(ex0 + 10, floor_y + 22, "Front elevation, fallboard open, lid closed. Same scale in all three.", 13, "#d8cfc2")

    # close-up: centre of the fallboard and the music rest
    cy0, chh = ey0 + eh + 14, 330
    sc = 1.05
    vc = D.View(x0 + cw / 2, cy0 + 1.03 * sc * 1000, sc)
    add(f'<clipPath id="cw{i}"><rect x="{ex0}" y="{cy0}" width="{ew}" height="{chh}"/></clipPath>')
    add(f'<g clip-path="url(#cw{i})"><rect x="{ex0}" y="{cy0}" width="{ew}" height="{chh}" fill="{DARK["recess"]}"/>')
    D.front(vc, DARK)
    clip_not_sheet(f"nsc{i}", vc, (ex0, cy0, ex0 + ew, cy0 + chh))
    add(f'<g clip-path="url(#nsc{i})">')
    ornament_behind_sheet(vc, lv["n"])
    add("</g>")
    ornament_front(vc, lv["n"])
    add("</g>")
    add(f'<rect x="{ex0 + 8}" y="{cy0 + 8}" width="330" height="24" rx="3" fill="#000" opacity=".55"/>')
    text(ex0 + 16, cy0 + 25, "Close-up, 2.4x: fallboard (open) and music rest", 13, "#e8e4dc")
    # leaders in the close-up
    lx, ly = vc.p(0.075, (KT + 0.022 + 0.934) / 2 + 0.02)
    D.leader(lx, ly, ex0 + ew - 150, cy0 + 120, "")
    add(f'<rect x="{ex0 + ew - 150}" y="{cy0 + 108}" width="124" height="20" rx="3" fill="#000" opacity=".7"/>')
    text(ex0 + ew - 146, cy0 + 123, "seed motif  T", 13, "#e8e4dc")
    if lv["n"] >= 2:
        lx, ly = vc.p(0.30, (P["ledge_z"] + P["ledge_lip_top"]) / 2)
        D.leader(lx, ly, ex0 + ew - 150, cy0 + 90, "")
        add(f'<rect x="{ex0 + ew - 150}" y="{cy0 + 78}" width="132" height="20" rx="3" fill="#000" opacity=".7"/>')
        text(ex0 + ew - 146, cy0 + 93, "pierced rest  T", 13, "#e8e4dc")
    if lv["n"] >= 3:
        lx, ly = vc.p(-0.2, KT - 0.01)
        D.leader(lx, ly, ex0 + 150, cy0 + chh - 70, "")
        add(f'<rect x="{ex0 + 12}" y="{cy0 + chh - 82}" width="152" height="20" rx="3" fill="#000" opacity=".7"/>')
        text(ex0 + 16, cy0 + chh - 67, "pearl key fronts  M", 13, "#e8e4dc")

    # element list
    ly = cy0 + chh + 34
    chars = 66 if lv["n"] == 3 else 92
    if lv["n"] > 1:
        text(x0 + 16, ly, f"Everything in {LEVELS[lv['n'] - 2]['name']}, plus:", 14, MUTED, weight=600)
        ly += 22
    for s_, tag in lv["items"]:
        add(f'<rect x="{x0 + 16}" y="{ly - 13}" width="22" height="18" rx="3" fill="{ {"G": "#3d5a80", "T": "#8a6a2c", "M": "#5c5c5c"}[tag] }"/>')
        text(x0 + 27, ly + 1, tag, 12, "#fff", "middle", 700)
        ly = wrap(x0 + 46, ly, s_, chars, 14, INK, 18) + 4
    ly += 6
    ly = wrap(x0 + 16, ly, "Cost: " + lv["cost"], chars + 6, 13.5, INK, 18) + 4
    wrap(x0 + 16, ly, "Henson guitar: " + lv["fit"], chars + 6, 13.5, MUTED, 18)
    if lv["n"] == 3:
        bx0, by0 = x0 + cw - 226, cy0 + chh + 14
        add(f'<rect x="{bx0}" y="{by0}" width="212" height="180" fill="url(#wall)"/>')
        add(f'<rect x="{bx0}" y="{by0 + 158}" width="212" height="22" fill="#3e281a"/>')
        vb = D.View(bx0 + 106, by0 + 158, 0.25)
        draw_bench(vb, 3)
        text(bx0 + 8, by0 + 18, "Bench, front, 0.6x", 12, "#3a4152")


def motif_strip():
    y0, h = 1432, 486
    x0, w = 40, 1530
    D.panel(x0, y0, w, h, "4 · The motif language (our own: a Baroque scroll-vine that branches like a family tree)")
    cells = 6
    cw = (w - 32 - (cells - 1) * 12) / cells
    cy = y0 + 52
    titles = ["Branch: the seed", "Corner flourish", "Running scroll", "Pinstripe", "Hardware", "Colours"]
    notes = [
        ["Two scrolls and a pearl bud, 17 cm.", "It sits on the fallboard at every", "level and grows into the panel",
         "branch in Full. Curl, leaf and taper", "are the same everywhere."],
        ["Two vines along the field edges,", "each curling into the field, a leaf", "on the diagonal. 13 x 11 cm low,",
         "8.5 x 4 cm up. Inlaid gold, flush."],
        ["A waving stem with curls above", "and below. Top: pierced in the lip,", "silk behind. Bottom: gold on the",
         "lid edge, 1.4 cm tall."],
        ["2.5 mm gold line, 10 to 12 mm in", "from the field edge, notched", "corners (r 12 to 18 mm). The one",
         "element every level shares."],
        ["Polished gold: hinges, castors,", "escutcheon, cheek caps. Pedals", "engraved only in Full (left)."],
        ["Inlays sit under the clear coat,", "so in the browser they are colour", "in the bake and reflect like",
         "the lacquer. Hardware is metal."],
    ]
    for c in range(cells):
        cx0 = x0 + 16 + c * (cw + 12)
        add(f'<clipPath id="mc{c}"><rect x="{cx0:.1f}" y="{cy}" width="{cw:.1f}" height="270" rx="3"/></clipPath>')
        add(f'<rect x="{cx0:.1f}" y="{cy}" width="{cw:.1f}" height="270" fill="#0a0a0c" rx="3"/><g clip-path="url(#mc{c})">')
        mid_x = cx0 + cw / 2
        if c == 0:
            v = D.View(mid_x, cy + 135, 1.30)
            mirror2(emblem_half(), v)
            emblem_centre().emit(v)
        elif c == 1:
            v = D.View(cx0 + 30, cy + 240, 1.55)
            notched_rect(v, -0.004, 0.30, -0.004, 0.30, 0.018, GOLD_IN, 0.0025)
            corner(0.13, 0.11, 0.0032).emit(v, lambda x, y: (x + 0.012, y + 0.012))
        elif c == 2:
            v = D.View(cx0 + 10, cy + 90, 1.30)
            hh = 0.029
            v.rect(0, 0.172, -hh / 2 - 0.0045, hh / 2 + 0.0045, "#0c0c0e", "#2e323d", 0.8)
            v.rect(0.004, 0.168, -hh / 2, hh / 2, SILK, "none", 0)
            band(0.006, 0.166, hh - 0.002, "lacq").emit(v, stroke="#666d80", sw=0.7)
            hline(v, 0.002, 0.170, -hh / 2 - 0.002, GOLD_IN, 0.0018)
            hline(v, 0.002, 0.170, hh / 2 + 0.002, GOLD_IN, 0.0018)
            v2 = D.View(cx0 + 10, cy + 200, 1.30)
            band(0.004, 0.168, 0.0136).emit(v2)
            text(cx0 + 10, cy + 140, "lip, pierced, silk behind", 12, "#bdb6a8")
            text(cx0 + 10, cy + 236, "lid edge, inlaid gold", 12, "#bdb6a8")
        elif c == 3:
            v = D.View(cx0 + 30, cy + 240, 4.0)
            v.rect(-0.010, 0.2, -0.010, 0.2, "#121217", "#2e323d", 0.8)
            notched_rect(v, 0.0, 0.2, 0.0, 0.2, 0.012, GOLD_IN, 0.0025)
            text(cx0 + 52, cy + 24, "corner at 4x", 12, "#bdb6a8")
        elif c == 4:
            # engraved pedal (plan), escutcheon, hinge
            k = 1.7
            px, py = cx0 + 40, cy + 30
            L = (P["pedal_back_y"] - P["pedal_front_y"]) * 1000 * k
            wb, wf = P["pedal_w_back"] * 1000 * k / 2, P["pedal_w_front"] * 1000 * k / 2
            yf = py + L - wf
            add(f'<path d="M{px - wb},{py} L{px - wf},{yf} A{wf},{wf} 0 0 0 {px + wf},{yf} L{px + wb},{py} Z" '
                f'fill="{GOLD_HW}" stroke="#6d5420" stroke-width="1"/>')
            pv = D.View(px, py, k)
            m = Motif()
            st = m.vine(0, -0.012, -90, 0.085, 0.0018, curl=1, cfrac=0.25, turns=0.8)
            for f, sd in ((0.25, 1), (0.5, -1), (0.72, 1)):
                m.child(st, f, sd * 40, 0.016, 0.0011, curl=sd, cfrac=0.6, turns=0.85)
            m.emit(pv, kinds={"gold": "#8a6a2c"})
            ev = D.View(cx0 + 130, cy + 70, 2.6)
            escutcheon(ev, 0, 0)
            text(cx0 + 130, cy + 130, "escutcheon", 12, "#bdb6a8", "middle")
            hx, hy, kk = cx0 + 100, cy + 190, 2.0
            Lh, r = P["hinge_len"] * 1000 * kk, P["hinge_r"] * 1000 * kk
            add(f'<rect x="{hx}" y="{hy + 2}" width="{Lh}" height="22" fill="{GOLD_HW}" stroke="#6d5420"/>')
            for j in range(5):
                seg = Lh / 5
                add(f'<rect x="{hx + j * seg + 1}" y="{hy - r}" width="{seg - 2}" height="{2 * r}" rx="{r}" '
                    f'fill="{GOLD_HW}" stroke="#6d5420"/>')
            text(hx + Lh / 2, hy + 44, "lid hinge", 12, "#bdb6a8", "middle")
            text(px, py + L + 18, "pedal", 12, "#bdb6a8", "middle")
        elif c == 5:
            sw_ = [("Lacquer", LACQ), ("Hardware gold", GOLD_HW), ("Inlay gold", GOLD_IN), ("Pearl", PEARL),
                   ("Silk (rest)", SILK), ("Ivory keys", C.COL["ivory"])]
            for j, (lab, col) in enumerate(sw_):
                yy = cy + 14 + j * 42
                add(f'<rect x="{cx0 + 12}" y="{yy}" width="54" height="32" rx="3" fill="{col}" stroke="#3a3a40"/>')
                text(cx0 + 76, yy + 14, lab, 13, "#e8e4dc", weight=600)
                text(cx0 + 76, yy + 29, col, 12, "#bdb6a8")
        add("</g>")
        text(cx0, cy + 296, titles[c], 15, INK, weight=600)
        for k, ln in enumerate(notes[c]):
            text(cx0, cy + 318 + k * 18, ln, 13, MUTED)


def recommendation():
    x0, y0, w, h = 1584, 1432, 776, 486
    D.panel(x0, y0, w, h, "5 · Recommendation: 2 · Medium")
    y = y0 + 62
    pts = [
        "It reads from the room. The gold corners and the top line catch the warm lamp at 5:40, and the "
        "gold pedals and castors glint at floor level. Light disappears at room distance.",
        "The branch is where the camera looks: on the fallboard, in frame in the keys close-up "
        "(piano_view). The pierced rest frames the About page without covering it.",
        "It stays a serious instrument. The ornament keeps to borders and hardware, the black fields stay "
        "open, the silhouette does not change. Full turns the case into a canvas and makes the music "
        "the second thing you look at.",
        "Cheap: one new texture and under 1k triangles. No new meshes and no new names in MESHES.md: "
        "everything sits on piano_static, piano_fallboard and piano_lid.",
    ]
    for s_ in pts:
        add(f'<circle cx="{x0 + 22}" cy="{y - 5}" r="3" fill="{ACC}"/>')
        y = wrap(x0 + 34, y, s_, 96, 14, INK, 19) + 8
    y += 4
    y = wrap(x0 + 16, y, "First to cut if it looks busy once lit: the lid-edge scroll (the top pinstripe "
             "already draws that line).", 100, 14, INK, 19, weight=600) + 10
    text(x0 + 16, y, "Tags", 14, INK, weight=600)
    y += 20
    for tag, col, s_ in (("G", "#3d5a80", "geometry: modelled (escutcheon, decal pinstripes, Full's relief)"),
                         ("T", "#8a6a2c", "texture: painted into the bake (inlays, filigree, fretwork, lid edge)"),
                         ("M", "#5c5c5c", "material: existing faces made gold metal or pearl, no new shape")):
        add(f'<rect x="{x0 + 16}" y="{y - 13}" width="22" height="18" rx="3" fill="{col}"/>')
        text(x0 + 27, y + 1, tag, 12, "#fff", "middle", 700)
        text(x0 + 46, y, s_, 13.5, MUTED)
        y += 22
    y += 6
    wrap(x0 + 16, y, "For the owner: the silk behind the fretwork, dark mauve (a nod to guitar_06, shown) or "
         "black (quieter). And guitar_06's fretboard tree should be drawn in this same hand when the "
         "guitars get their sheet.", 100, 13.5, MUTED, 18)


def build():
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_PX}" height="{H_PX}" viewBox="0 0 {W_PX} {H_PX}" '
        f'font-family="-apple-system, Helvetica Neue, Arial, sans-serif">')
    add('<defs><linearGradient id="gloss" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".14"/>'
        '<stop offset=".35" stop-color="#fff" stop-opacity="0"/><stop offset=".62" stop-color="#9fb8e8" stop-opacity=".08"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c3c9d8"/>'
        '<stop offset="1" stop-color="#a7afc2"/></linearGradient>'
        f'<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{ACC}"/></marker></defs>')
    add(f'<rect width="{W_PX}" height="{H_PX}" fill="{PAPER}"/>')
    text(48, 58, "Upright piano · ornament sheet", 32, INK, weight=650)
    text(48, 86, "obj_piano, style A (polished black) with Polyphia-style ornament: black and gold, filigree, "
         "a branch of our own. Three levels on the approved piano, dimensions unchanged. "
         "G geometry · T texture · M material", 16, MUTED)
    text(W_PX - 48, 58, "2026-10-22 · for the owner's choice, before the 3D rebuild", 15, MUTED, "end")
    for i, lv in enumerate(LEVELS):
        column(i, lv)
    motif_strip()
    recommendation()
    add("</svg>")


def main():
    os.makedirs(OUT, exist_ok=True)
    D.out.clear()
    build()
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>Piano ornament sheet</title>"
            f"<style>html,body{{margin:0;background:{PAPER}}}svg{{display:block}}</style></head><body>"
            + "\n".join(D.out) + "</body></html>")
    hp = os.path.join(OUT, "piano-ornament-sheet.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    png = os.path.join(OUT, "piano-ornament-sheet.png")
    subprocess.run([D.CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={W_PX},{H_PX}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", hp, png)


if __name__ == "__main__":
    main()
