"""The piano's tribal ornament: one source for the 2D sheet and the 3D model.

Decided 2026-10-22 (docs/05-decisions.md): tribal tattoo-style strokes of our own in
brushed silver on the black lacquer, the tuning-fork emblem, Full level, chrome
hardware. The strokes are built from four parts (a tapering blade, a hook, a flame
point, a teardrop cut-out) and mirrored about the piano's centreline. Everything is
in the piano's own metres, in the front elevation (x across, z up), the fallboard
drawn open as on the sheet.

Plain Python plus numpy (both ship with Blender); bpy is imported only inside
`build_images()`. Three users:

    blender/design/piano_tribal_sheet.py   draws the strokes as SVG (the approved sheet)
    blender/props/obj_piano.py             rasterises them into the silver masks, maps
                                           the case's UVs onto them, colours the key fronts
    blender/tests/piano_quality.py         reports the texture sizes

Layout of the textures (`ATLAS`, `LID`): every ornamented face is a rectangle of the
front elevation, placed in the atlas at its own pixels per metre, with a blank margin
round it. Faces that carry no ornament are mapped onto that margin, so bevels and
back faces never cross a stroke (see `uv_map`). Images are written with row 0 at
V = 0, the bottom, as Blender stores them; the glTF exporter flips V and the picture
arrives upright in three.js (no screen-helper flip here: that rule is only for the
canvases the site paints).
"""
import math

from . import constants as C
from .piano_layout import fallboard_profile

P, KT = C.PIANO, C.KT

# Colours (sRGB). Inlay: brushed sterling silver under the clear coat. Hardware:
# polished chrome. Nickel is the warmer alternative, shown on the sheet only.
SILVER = "#b7bbc2"
SILVER_HI, SILVER_LO = "#dfe2e7", "#8d929b"
CHROME = "#d4d7dc"
NICKEL = "#cbc4b6"
SILVER_ROUGH, CHROME_ROUGH = 0.35, 0.06

FIELD_UP = (-P["inset_half_w"], P["inset_half_w"], P["inset_bottom"], P["inset_top"])
FIELD_LO = (-P["lower_inset_half_w"], P["lower_inset_half_w"], P["lower_inset_bottom"], P["lower_inset_top"])
CHEEK_IN = P["fall_half_w"] + 0.002                # inside face of the key cheeks (obj_piano ARM_IN)
_fz = [z for _, z in fallboard_profile(P["fall_open_deg"])]
FB_TOP = max(_fz)                                  # top of the open fallboard's face
FB_MID = (KT + 0.024 + FB_TOP) / 2                 # middle of the part seen above the felt
UP_MID = (FIELD_UP[2] + FIELD_UP[3]) / 2
LID_Z = P["case_top"] + P["lid_t"] / 2             # middle of the lid's front edge
B = C.BENCH
BENCH_MID = B["h"] - B["t"] - B["apron"] / 2       # middle of the bench's front apron


# ---------------------------------------------------------------------------
# stroke engine: centrelines, blades, flame points, teardrop cut-outs (metres)
# ---------------------------------------------------------------------------
def arc(x, y, h_deg, L, dh=None, n=120):
    """Centreline from (x, y) along h_deg for length L. dh(t) is the heading rate in
    radians per unit t, so its integral over 0..1 is the total turn. [(x, y, heading)]"""
    pts, h = [], math.radians(h_deg)
    for i in range(n + 1):
        t = i / n
        pts.append((x, y, h))
        h += (dh(t) if dh else 0.0) / n
        x += math.cos(h) * L / n
        y += math.sin(h) * L / n
    return pts


def turn(deg, curl=0.0):
    """Total turn of deg, concentrated toward the tip as curl grows (0 = an even arc)."""
    k = math.radians(deg) * (curl + 1)
    return lambda t: k * t ** curl


def wave(deg):
    """Heading rises by deg at the middle and comes back: a gentle S."""
    return lambda t: math.radians(deg) * math.pi * math.sin(2 * math.pi * t)


def plus(*fs):
    return lambda t: sum(f(t) for f in fs)


def spline(ctrl, n=120):
    """Catmull-Rom through ctrl points, resampled evenly by length. [(x, y, heading)]"""
    Q = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    raw = []
    for i in range(len(Q) - 3):
        p0, p1, p2, p3 = Q[i:i + 4]
        for j in range(30):
            u = j / 30
            raw.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u * u
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u ** 3) for k in (0, 1)))
    raw.append(tuple(ctrl[-1]))
    acc = [0.0]
    for a, b in zip(raw, raw[1:]):
        acc.append(acc[-1] + math.dist(a, b))
    out, j = [], 0
    for i in range(n + 1):
        s = acc[-1] * i / n
        while j < len(acc) - 2 and acc[j + 1] < s:
            j += 1
        u = (s - acc[j]) / max(acc[j + 1] - acc[j], 1e-12)
        out.append((raw[j][0] + (raw[j + 1][0] - raw[j][0]) * u, raw[j][1] + (raw[j + 1][1] - raw[j][1]) * u))
    res = []
    for k, (x, y) in enumerate(out):
        a, b = out[max(0, k - 1)], out[min(len(out) - 1, k + 1)]
        res.append((x, y, math.atan2(b[1] - a[1], b[0] - a[0])))
    return res


def at(cl, t):
    n = len(cl) - 1
    f = min(max(t, 0.0), 1.0) * n
    i = min(int(f), n - 1)
    u = f - i
    (x0, y0, h0), (x1, y1, h1) = cl[i], cl[i + 1]
    return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, h0 + (h1 - h0) * u


# width profiles: t runs 0 (root) to 1 (tip)
def thorn(w0, p=1.3):
    """Wide root, concave sides, needle tip."""
    return lambda t: w0 * (1 - t) ** p


def spindle(wmax, tm=0.35, a=0.85):
    """Pointed at both ends, widest at tm."""
    e = math.log(0.5) / math.log(tm)
    return lambda t: wmax * math.sin(math.pi * t ** e) ** a


def tear(wmax, p=1.5):
    """Round head at t = 0, a tail that runs out to a point."""
    tm = 1 / (1 + 2 * p)
    fmax = math.sqrt(tm) * (1 - tm) ** p
    return lambda t: wmax * math.sqrt(max(t, 0)) * (1 - t) ** p / fmax


def tine(wmax):
    """Even width, then a short sharp point (the fork's tines)."""
    return lambda t: wmax * max(0.0, 1 - t ** 6) ** 0.7


def blade(cl, wfn, bias=0.0):
    """Polygon of a stroke: offsets the centreline by the width, bias > 0 fattens the left."""
    n = len(cl) - 1
    left, right = [], []
    for i, (x, y, h) in enumerate(cl):
        w = wfn(i / n)
        nx, ny = -math.sin(h), math.cos(h)
        wl, wr = w * (1 + bias) / 2, w * (1 - bias) / 2
        left.append((x + nx * wl, y + ny * wl))
        right.append((x - nx * wr, y - ny * wr))
    return left + right[::-1]


class Piece:
    """One stroke group in local metres: silver polygons and teardrop cut-outs."""

    def __init__(self):
        self.solid, self.holes = [], []

    def stroke(self, cl, wfn, bias=0.0):
        self.solid.append(blade(cl, wfn, bias))
        return cl

    def flame(self, spine, wfn, t, side, ang, L, bend, wfrac=0.78, curl=1.2, p=1.1, inset=0.0):
        """A flame point out of the spine's side (+1 left of its direction, -1 right),
        leaving at ang degrees and bending back toward the flow by bend degrees."""
        x, y, h = at(spine, t)
        w = wfn(t)
        nx, ny = -math.sin(h), math.cos(h)
        cl = arc(x + nx * side * w * inset, y + ny * side * w * inset, math.degrees(h) + side * ang, L,
                 turn(-side * bend, curl), n=48)
        self.solid.append(blade(cl, thorn(w * wfrac, p)))
        return cl

    def cut(self, spine, wfn, t0, t1, size=0.46, off=0.0):
        """A teardrop cut-out inside the spine from t0 (round head) to t1 (tail)."""
        cl = []
        for i in range(31):
            t = t0 + (t1 - t0) * i / 30
            x, y, h = at(spine, t)
            w = wfn(t)
            cl.append((x - math.sin(h) * off * w, y + math.cos(h) * off * w, h))
        wm = size * min(wfn(t0 + (t1 - t0) * 0.25), wfn((t0 + t1) / 2) * 1.3)
        self.holes.append(blade(cl, tear(wm)))

    def cut_free(self, cl, wmax):
        self.holes.append(blade(cl, tear(wmax)))

    def emit(self, layer, v, T):
        """Append page/pixel polygons to layer.solid and layer.holes; v.p maps metres."""
        for poly in self.solid:
            layer.solid.append([v.p(*T(x, y)) for x, y in poly])
        for poly in self.holes:
            layer.holes.append([v.p(*T(x, y)) for x, y in poly])

    def both(self, layer, v, T):
        """Emit, and emit again mirrored about the piano's centreline (world x = 0)."""
        self.emit(layer, v, T)
        self.emit(layer, v, lambda x, y: (-T(x, y)[0], T(x, y)[1]))


def place(dx=0.0, dz=0.0, s=1.0, rot=0.0, mx=1, my=1):
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return lambda x, y: (dx + s * (c * x * mx - sn * y * my), dz + s * (sn * x * mx + c * y * my))


# ---------------------------------------------------------------------------
# the motifs (local metres; every composition is drawn as its right half)
# ---------------------------------------------------------------------------
def arm(L=0.46, wmax=0.017, rise=-3.0, sway=8.0, flames=None, cuts=None, tm=0.33):
    """The long sweep: a spine that swells and runs out to a needle, flame points
    leaving both sides and bending outward, a chain of teardrops in its belly.
    Root at (0, 0) toward +x."""
    m = Piece()
    spine = arc(0, 0, rise, L, plus(wave(sway), turn(-4, 2)), n=220)
    wfn = spindle(wmax, tm)
    m.stroke(spine, wfn)
    for t, side, ang, l, bend in flames or ():
        m.flame(spine, wfn, t, side, ang, L * l, bend)
    for t0, t1, size, off in cuts or ():
        m.cut(spine, wfn, t0, t1, size, off)
    return m, spine, wfn


def upper_arm():
    """Upper panel, right of the music: root hidden behind the sheet."""
    fl = [(0.17, 1, 62, 0.14, 70), (0.30, 1, 56, 0.17, 72), (0.45, 1, 50, 0.14, 64), (0.61, 1, 42, 0.10, 52),
          (0.76, 1, 34, 0.06, 40),
          (0.23, -1, 60, 0.12, 66), (0.37, -1, 54, 0.14, 68), (0.53, -1, 46, 0.11, 58), (0.69, -1, 38, 0.07, 44)]
    ct = [(0.10, 0.19, 0.52, 0.04), (0.20, 0.29, 0.56, -0.07), (0.30, 0.39, 0.56, 0.06), (0.40, 0.48, 0.52, -0.05),
          (0.49, 0.56, 0.48, 0.05), (0.57, 0.63, 0.42, -0.03), (0.645, 0.70, 0.36, 0.02)]
    m, spine, wfn = arm(0.46, 0.031, rise=-4, sway=8, flames=fl, cuts=ct)
    # a hook off the first upper flame, curling back toward the centre
    x, y, h = at(spine, 0.10)
    m.stroke(arc(x, y, 118, 0.050, turn(70, 1.6), n=48), thorn(0.016, 1.1))
    return m


def wing():
    """The emblem's wings on the fallboard: a short arm plus two framing hooks."""
    fl = [(0.28, 1, 56, 0.26, 66), (0.50, 1, 46, 0.20, 54), (0.70, 1, 36, 0.12, 40),
          (0.36, -1, 54, 0.22, 62), (0.60, -1, 42, 0.15, 48)]
    ct = [(0.10, 0.24, 0.52, 0.0), (0.27, 0.40, 0.54, 0.05), (0.43, 0.54, 0.48, -0.04), (0.57, 0.66, 0.40, 0.02)]
    m, spine, wfn = arm(0.175, 0.021, rise=-6, sway=10, flames=fl, cuts=ct, tm=0.30)
    m.stroke(arc(0.002, 0.012, 72, 0.062, turn(-66, 1.0), n=60), thorn(0.012, 1.15))
    m.stroke(arc(0.002, -0.012, -74, 0.052, turn(62, 1.0), n=60), thorn(0.011, 1.15))
    return m


def corner():
    """Lower panel corner: two blades along the field edges and a hook on the
    diagonal. Corner at (0, 0), the field toward +x, +y."""
    m = Piece()
    r = (0.014, 0.014)
    wa, wb = thorn(0.024, 1.15), thorn(0.020, 1.15)
    a = m.stroke(arc(*r, 4, 0.150, turn(10, 1.5), n=80), wa)
    b = m.stroke(arc(*r, 86, 0.105, turn(-10, 1.5), n=80), wb)
    m.stroke(arc(r[0] + 0.006, r[1] + 0.006, 45, 0.068, turn(-160, 1.7), n=80), thorn(0.017, 1.05))
    m.flame(a, wa, 0.34, 1, 50, 0.042, 46)
    m.flame(b, wb, 0.36, -1, 50, 0.032, 46)
    m.cut(a, wa, 0.12, 0.36, 0.50, 0.0)
    m.cut(b, wb, 0.14, 0.38, 0.48, 0.0)
    return m


def lid_band():
    """Lid front edge: a thin running sweep, needle at the outer end, small points
    alternating up and down (fits 1.4 cm of the 2.2 cm edge)."""
    fl = [(0.08 + 0.10 * k, 1 if k % 2 == 0 else -1, 30, 0.036 - 0.002 * k, 30) for k in range(8)]
    ct = [(0.05 + 0.10 * k, 0.12 + 0.10 * k, 0.40, 0.0) for k in range(6)]
    m, spine, wfn = arm(0.52, 0.0095, rise=0, sway=0, flames=fl, cuts=ct, tm=0.18)
    return m


def console():
    """Console face: the references' own vertical sweep, root under the cheek.
    The face is 4.8 cm wide, so the flames are short and steep enough that their tips
    stay inside it (owner, 2026-10-22: they were 5.5 cm at 40 degrees and got clipped)."""
    fl = [(0.12 + 0.11 * k, 1 if k % 2 == 0 else -1, 28, 0.026 - 0.002 * k, 34) for k in range(7)]
    ct = [(0.05 + 0.11 * k, 0.13 + 0.11 * k, 0.46, 0.0) for k in range(6)]
    m, spine, wfn = arm(0.50, 0.018, rise=-90, sway=0, flames=fl, cuts=ct, tm=0.22)
    return m


def cheek_hook():
    """Key cheek front, below the nose: a short sweep outward and a hook curling under.
    The sweep stops 10 mm short of the groove between the cheek block and the side
    panel (owner, 2026-10-22, after the first lit renders; it was 12.5 cm)."""
    m = Piece()
    w = thorn(0.020, 1.1)
    s = m.stroke(arc(0.0, 0.0, 4, 0.100, turn(-10, 1.5), n=90), w)
    m.stroke(arc(0.004, -0.004, -60, 0.050, turn(170, 1.6), n=90), thorn(0.013, 1.1))
    m.flame(s, w, 0.30, 1, 48, 0.034, 46)
    m.flame(s, w, 0.46, -1, 44, 0.026, 40)
    m.cut(s, w, 0.08, 0.34, 0.48, 0.0)
    return m


# --- the three centre emblems (centred on (0, 0), about 10 cm tall) ----------
def mirror_pts(right):
    """Right-half outline from top centre to bottom centre, closed with its mirror."""
    return right + [(-x, y) for x, y in reversed(right[1:-1])]


def skull():
    m = Piece()
    half = [(0, 0.050), (0.019, 0.047), (0.032, 0.036), (0.037, 0.019), (0.036, 0.004), (0.033, -0.007),
            (0.025, -0.015), (0.023, -0.029), (0.015, -0.041), (0, -0.045)]
    outline = [(x, y) for x, y, _ in spline(mirror_pts(half) + [half[0]], 200)]
    m.solid.append(outline)
    for sx in (1, -1):
        f = (lambda x, y, sx=sx: (sx * x, y))
        # cheekbone hooks sweeping out and down
        cb = arc(0.024, -0.002, -14, 0.042, turn(-80, 1.4), n=50)
        m.solid.append([f(x, y) for x, y in blade(cb, thorn(0.012, 1.3))])
        # eye: round at the outer corner, pointed in and up toward the brow
        eye = arc(0.0225, -0.001, 150, 0.022, turn(18, 1), n=40)
        m.holes.append([f(x, y) for x, y in blade(eye, tear(0.0140, 1.3))])
        # nose: two small teardrops, an inverted heart
        nose = arc(0.0032, -0.0215, 98, 0.011, turn(-25, 1), n=30)
        m.holes.append([f(x, y) for x, y in blade(nose, tear(0.0046))])
    # forehead flame and the teeth (gaps left between the cut-outs are the teeth)
    m.holes.append(blade(arc(0, 0.043, -90, 0.017, n=30), tear(0.0062)))
    for k in range(-2, 3):
        x0 = k * 0.0058
        y0 = -0.0325 + 0.0007 * k * k
        m.holes.append(blade(arc(x0, y0 - 0.0045, 90, 0.009, n=24), spindle(0.0034, 0.5, 0.8)))
    return m


def heart():
    m = Piece()
    pts = [(0.0, -0.050), (0.017, -0.030), (0.034, -0.007), (0.040, 0.014), (0.033, 0.033), (0.019, 0.039),
           (0.008, 0.032), (0.004, 0.021), (0.006, 0.013)]
    for sx in (1, -1):
        f = (lambda x, y, sx=sx: (sx * x, y))
        cl = spline(pts, 160)
        wfn = spindle(0.0125, 0.40, 0.8)
        m.solid.append([f(x, y) for x, y in blade(cl, wfn, bias=-0.15)])
        tmp = Piece()
        tmp.flame(cl, wfn, 0.66, -1, 46, 0.030, 58)
        tmp.flame(cl, wfn, 0.47, -1, 52, 0.024, 50)
        tmp.flame(cl, wfn, 0.25, -1, 50, 0.018, 44)
        tmp.cut(cl, wfn, 0.28, 0.48, 0.50, 0.02)
        tmp.cut(cl, wfn, 0.53, 0.66, 0.42, 0.0)
        m.solid += [[f(x, y) for x, y in p] for p in tmp.solid]
        m.holes += [[f(x, y) for x, y in p] for p in tmp.holes]
    m.solid.append(blade(arc(0, -0.044, -90, 0.020, n=30), thorn(0.0065, 1.2)))
    return m


def fork():
    m = Piece()
    tine_pts = [(0.0, -0.013), (0.008, -0.0105), (0.0122, -0.003), (0.0128, 0.012), (0.0128, 0.034),
                (0.0118, 0.050), (0.0090, 0.060)]
    for sx in (1, -1):
        f = (lambda x, y, sx=sx: (sx * x, y))
        cl = spline(tine_pts, 160)
        wfn = tine(0.0068)
        tmp = Piece()
        tmp.stroke(cl, wfn)
        tmp.flame(cl, wfn, 0.50, -1, 50, 0.020, 58, wfrac=0.8)
        tmp.flame(cl, wfn, 0.30, -1, 52, 0.014, 50, wfrac=0.8)
        tmp.cut(cl, wfn, 0.48, 0.80, 0.42, 0.0)
        # shoulder hook, curling down beside the stem
        tmp.stroke(arc(0.002, -0.017, -8, 0.030, turn(-150, 1.5), n=60), thorn(0.0072, 1.2))
        m.solid += [[f(x, y) for x, y in p] for p in tmp.solid]
        m.holes += [[f(x, y) for x, y in p] for p in tmp.holes]
    stem = arc(0, -0.009, -90, 0.054, n=80)
    m.stroke(stem, thorn(0.0082, 0.9))
    m.cut(stem, thorn(0.0082, 0.9), 0.22, 0.52, 0.44, 0.0)
    return m


EMBLEMS = [
    dict(key="skull", name="Skull", fn=skull, root=0.034,
         note="The owner's first reference, done cleanly: no spider. The cheekbones run out into hooks; "
              "the teeth are what is left between five cuts."),
    dict(key="heart", name="Heart", fn=heart, root=0.040,
         note="The second reference: two mirrored blades that meet at the point and roll into hooks at the "
              "cleft. The middle stays open lacquer."),
    dict(key="fork", name="Tuning fork", fn=fork, root=0.017,
         note="Ours, and musical: a fork's two tines and stem, with flame points and shoulder hooks. "
              "A treble clef cannot be mirrored, so the fork keeps the symmetry rule."),
]
CHOSEN_EMBLEM = 2        # the tuning fork (owner: "fork ,full")
CHOSEN_LEVEL = 3         # Full


# ---------------------------------------------------------------------------
# where every piece goes, by level (2 Medium, 3 Full) and emblem: (piece, T, mirrored)
# ---------------------------------------------------------------------------
def layout(lvl=CHOSEN_LEVEL, emb=CHOSEN_EMBLEM):
    E = EMBLEMS[emb]
    x0, x1, z0, z1 = FIELD_LO
    L = {
        "upper": [(upper_arm(), place(0.165, UP_MID - 0.004), True)],
        "lid": [(lid_band(), place(0.215, LID_Z), True)] if lvl >= 3 else [],
        "fall": [(E["fn"](), place(0, FB_MID), False), (wing(), place(E["root"], FB_MID - 0.004), True)],
        "lower": [(corner(), place(x0 if sx < 0 else x1, z0 if sz < 0 else z1, mx=-sx, my=-sz), False)
                  for sx in (-1, 1) for sz in (-1, 1)],
        "cheek": [], "console": [], "bench": [],
    }
    if lvl >= 3:
        L["cheek"] = [(cheek_hook(), place(CHEEK_IN + 0.012, (P["cheek_bottom"] + P["cheek_nose"]) / 2 - 0.006), True)]
        L["console"] = [(console(), place(P["toe_x"], P["cheek_bottom"] - 0.012), True)]
        s = 0.52
        L["bench"] = [(E["fn"](), place(0, BENCH_MID, s), False),
                      (wing(), place(E["root"] * s, BENCH_MID - 0.002, s), True)]
    return L


def emit(items, layer, v):
    for piece, T, both in items:
        (piece.both if both else piece.emit)(layer, v, T)


# ---------------------------------------------------------------------------
# the textures: regions of the front elevation packed into two images
# ---------------------------------------------------------------------------
class Region:
    """A rectangle of the front elevation (x0..x1, z0..z1 metres) at (u0, v0) pixels in
    an image, su/sv pixels per metre. `swap` turns it 90 degrees (u runs along z)."""

    def __init__(self, name, group, x0, x1, z0, z1, su, sv, u0, v0, swap=False):
        self.name, self.group = name, group
        self.x0, self.x1, self.z0, self.z1 = x0, x1, z0, z1
        self.su, self.sv, self.u0, self.v0, self.swap = su, sv, u0, v0, swap
        a, b = (x1 - x0) * su, (z1 - z0) * sv
        self.w, self.h = (int(round(b)), int(round(a))) if swap else (int(round(a)), int(round(b)))

    def px(self, x, z):
        """Front-elevation metres to image pixels (u right, v up)."""
        if self.swap:
            return self.u0 + (z - self.z0) * self.su, self.v0 + (x - self.x0) * self.sv
        return self.u0 + (x - self.x0) * self.su, self.v0 + (z - self.z0) * self.sv

    def p(self, x, z):
        """Metres to this region's own raster pixels (for Piece.emit)."""
        u, v = self.px(x, z)
        return u - self.u0, v - self.v0


MARGIN = 8     # blank pixels kept round every region; non-ornament faces map onto this ring

hw = P["width"] / 2
ATLAS = dict(name="piano_tribal_front", size=(4096, 1024), regions=[
    Region("upper", "upper", *FIELD_UP, 1600, 1600, 16, 16),
    Region("fall", "fall", -P["fall_half_w"], P["fall_half_w"], P["fall_pivot_z"], FB_TOP, 1600, 1600, 2104, 16),
    Region("lower", "lower", *FIELD_LO, 1400, 1400, 16, 340),
    Region("cheek_l", "cheek", -hw, -CHEEK_IN, P["cheek_bottom"], P["cheek_nose"], 2400, 2400, 1680, 340),
    Region("cheek_r", "cheek", CHEEK_IN, hw, P["cheek_bottom"], P["cheek_nose"], 2400, 2400, 1680, 590),
    Region("console_l", "console", -P["toe_x"] - P["console_w"] / 2, -P["toe_x"] + P["console_w"] / 2,
           P["toe_rail_top"], P["cheek_bottom"], 2000, 2000, 2104, 340, swap=True),
    Region("console_r", "console", P["toe_x"] - P["console_w"] / 2, P["toe_x"] + P["console_w"] / 2,
           P["toe_rail_top"], P["cheek_bottom"], 2000, 2000, 2104, 476, swap=True),
    Region("bench", "bench", -B["leg_x"], B["leg_x"], B["h"] - B["t"] - B["apron"], B["h"] - B["t"],
           2000, 2000, 2104, 612),
])
LID = dict(name="piano_tribal_lid", size=(2048, 96), regions=[
    Region("lid", "lid", -hw - P["lid_over_side"], hw + P["lid_over_side"], P["case_top"], P["case_top"] + P["lid_t"],
           1984 / (P["width"] + 2 * P["lid_over_side"]), 64 / P["lid_t"], 32, 16),
])

# which parts of obj_piano carry which region (the rest of each image is blank)
PART_REGIONS = {
    "piano_field_upper": ("front", "upper"), "piano_fallboard": ("front", "fall"),
    "piano_field_lower": ("front", "lower"),
    "piano_cheek_l": ("front", "cheek_l"), "piano_side_l": ("front", "cheek_l"),
    "piano_cheek_r": ("front", "cheek_r"), "piano_side_r": ("front", "cheek_r"),
    "piano_console_l": ("front", "console_l"), "piano_console_r": ("front", "console_r"),
    "piano_bench_apron_01": ("front", "bench"),
    "piano_lid": ("lid", "lid"),
}


def _check_layout():
    for img in (ATLAS, LID):
        W, H = img["size"]
        boxes = []
        for r in img["regions"]:
            b = (r.u0 - MARGIN, r.v0 - MARGIN, r.u0 + r.w + MARGIN, r.v0 + r.h + MARGIN)
            assert 0 <= b[0] and 0 <= b[1] and b[2] <= W and b[3] <= H, f"{r.name} outside {img['name']}"
            for o, ob in boxes:
                assert b[2] <= ob[0] or ob[2] <= b[0] or b[3] <= ob[1] or ob[3] <= b[1], f"{r.name} overlaps {o}"
            boxes.append((r.name, b))


_check_layout()


class _Layer:
    def __init__(self):
        self.solid, self.holes = [], []


def rasterise(polys, w, h, ss=4):
    """Coverage (h, w) float32 in 0..1 of the union of polygons (pixel coords, v up,
    row 0 at the bottom). Non-zero winding on a ss x ss sub-grid, box-filtered."""
    import numpy as np
    W, H = w * ss, h * ss
    diff = np.zeros((H, W + 1), dtype=np.int32)
    ys = np.arange(H, dtype=np.float64) + 0.5
    for poly in polys:
        pts = np.asarray(poly, dtype=np.float64) * ss
        if len(pts) < 3:
            continue
        x0, y0 = pts[:, 0], pts[:, 1]
        x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
        # orient every polygon the same way, so overlaps add instead of cancelling
        if np.sum(x0 * y1 - x1 * y0) < 0:
            x0, y0, x1, y1 = x1, y1, x0, y0
        lo, hi = np.minimum(y0, y1), np.maximum(y0, y1)
        r0 = max(int(np.floor(lo.min())), 0)
        r1 = min(int(np.ceil(hi.max())) + 1, H)
        if r1 <= r0:
            continue
        yy = ys[r0:r1][:, None]                                  # rows x 1
        up = y1 > y0
        hit = (yy >= lo[None, :]) & (yy < hi[None, :])          # rows x edges
        if not hit.any():
            continue
        dy = np.where(y1 == y0, 1.0, y1 - y0)
        xs = x0[None, :] + (yy - y0[None, :]) * ((x1 - x0) / dy)[None, :]
        rows, cols = np.nonzero(hit)
        xc = np.clip(np.rint(xs[rows, cols]), 0, W).astype(np.int64)
        sign = np.where(up[cols], 1, -1)
        np.add.at(diff, (rows + r0, xc), sign)
    wind = np.cumsum(diff, axis=1)[:, :W]
    cov = (wind != 0).astype(np.float32)
    return cov.reshape(h, ss, w, ss).mean(axis=(1, 3))


def masks(lvl=CHOSEN_LEVEL, emb=CHOSEN_EMBLEM):
    """{image name: coverage array (H, W), row 0 at the bottom} for both images."""
    import numpy as np
    L = layout(lvl, emb)
    out = {}
    for img in (ATLAS, LID):
        W, H = img["size"]
        cov = np.zeros((H, W), dtype=np.float32)
        for r in img["regions"]:
            lay = _Layer()
            emit(L[r.group], lay, r)
            if not lay.solid:
                continue
            solid = rasterise(lay.solid, r.w, r.h)
            if lay.holes:
                solid = np.clip(solid - rasterise(lay.holes, r.w, r.h), 0, 1)
            cov[r.v0:r.v0 + r.h, r.u0:r.u0 + r.w] = solid
        out[img["name"]] = cov
    return out


def srgb8(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def build_images(out_dir=None, lvl=CHOSEN_LEVEL, emb=CHOSEN_EMBLEM):
    """Blender images: RGB is the lacquer or the silver (sRGB), alpha the silver mask.
    Returns {"front": image, "lid": image, "files": {name: path}}. Each image is also
    saved as a PNG in out_dir (default blender/out/) for the size report, then packed."""
    import os
    import bpy
    import numpy as np
    out_dir = out_dir or C.OUT
    os.makedirs(out_dir, exist_ok=True)
    lacq, silv = np.array(srgb8(C.COL["lacquer_black"]), np.float32), np.array(srgb8(SILVER), np.float32)
    result = {"files": {}}
    for key, spec, cov in (("front", ATLAS, None), ("lid", LID, None)):
        cov = masks(lvl, emb)[spec["name"]] if cov is None else cov
        H, W = cov.shape
        px = np.empty((H, W, 4), dtype=np.float32)
        px[..., :3] = lacq[None, None, :] * (1 - cov[..., None]) + silv[None, None, :] * cov[..., None]
        px[..., 3] = cov
        name = spec["name"]
        old = bpy.data.images.get(name)
        if old is not None:
            bpy.data.images.remove(old)
        img = bpy.data.images.new(name, W, H, alpha=True)
        img.alpha_mode = "CHANNEL_PACKED"      # alpha is a mask, not transparency
        img.pixels.foreach_set(np.ascontiguousarray(px).ravel())
        path = os.path.join(out_dir, f"{name}.png")
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        img.pack()
        result[key] = img
        result["files"][name] = path
    return result


# ---------------------------------------------------------------------------
# UVs: project each part's faces onto its region; the rest onto the blank margin
# ---------------------------------------------------------------------------
def _region(part):
    if part not in PART_REGIONS:
        return None
    which, rname = PART_REGIONS[part]
    spec = ATLAS if which == "front" else LID
    return spec, next(r for r in spec["regions"] if r.name == rname)


def uv_map(obj, part=None):
    """Write the UV layer of a part. Front faces (normal toward -Y in the piano frame,
    the fallboard open as built) project onto the region; side, top, bottom and back
    faces are snapped to the margin ring just outside it, so bevel strips between a
    front face and its neighbours only ever cross blank texels. Returns the region."""
    from mathutils import Vector
    found = _region(part or obj.name)
    if found is None:
        return None
    spec, r = found
    W, H = spec["size"]
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    M = obj.matrix_local
    R = M.to_3x3()
    uL, uR = r.u0 - MARGIN / 2, r.u0 + r.w + MARGIN / 2
    vB, vT = r.v0 - MARGIN / 2, r.v0 + r.h + MARGIN / 2
    um, vm = (uL + uR) / 2, (vB + vT) / 2
    for poly in me.polygons:
        n = (R @ poly.normal).normalized()
        front = n.y < -0.4
        snap_u = (not front) and (abs(n.x) > 0.5 or n.y > 0.4)
        snap_v = (not front) and (abs(n.z) > 0.5 or n.y > 0.4)
        for li in poly.loop_indices:
            co = M @ me.vertices[me.loops[li].vertex_index].co
            u, v = r.px(co.x, co.z)
            if snap_u:
                u = uL if u < um else uR
            if snap_v:
                v = vB if v < vm else vT
            u = min(max(u, uL), uR)
            v = min(max(v, vB), vT)
            uv.data[li].uv = (u / W, v / H)
    return r
