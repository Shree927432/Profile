"""2D room plan sheet, drawn to scale from blender/lib/constants.py (ROOM, LAYOUT, HERO).

Plain Python (no Blender): writes an HTML page with one SVG, then renders it to a PNG
with the cached headless Chromium. Run from the repo root:

    python3 blender/design/room_plan_sheet.py

Output: video-local/footage/2026-10-22-room-plan/room-plan-sheet.{html,png}

What it draws: the floor plan with every root's footprint, the four walls unfolded,
a lid-versus-guitar section at the piano, the hero camera on the plan and a flat-shaded
perspective sketch of what it sees (desktop 16:9 and a phone), and the two places the
guitar rack could stand. It also checks clearances and prints any clash.
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib import constants as C  # noqa: E402
from lib.piano_layout import lid_profile, cheek_profile, console_profile  # noqa: E402

import piano_design_sheet as PDS  # noqa: E402  (reuses its piano front elevation)

R, L, P, B = C.ROOM, C.LAYOUT, C.PIANO, C.BENCH
RX, RY, H = C.RX, C.RY, C.ROOM["height"]
WG, HERO, WIN, DOOR = C.WALL_GUITARS, C.HERO, C.WINDOW, C.DOOR
OUT = os.path.join(C.FOOTAGE, "2026-10-22-room-plan")
W_PX, H_PX = 2400, 3190
CHROME = PDS.CHROME

INK, ACC, MUTED, PAPER, RULE = "#1d1c1a", "#b5532a", "#6b675f", "#f6f3ec", "#d6d0c4"
OBJ_FILL, OBJ_LINE = "#dfe8f3", "#36557a"        # the nine interactive objects
SET_FILL = "#e6e1d7"                             # scenery
WALL_POCHE = "#4a4741"

out = []
PDS.out = out          # PDS.front() draws into this sheet


def add(s):
    out.append(s)


def cm(m, nd=1):
    t = f"{m * 100:.{nd}f}"
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t + " cm"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=14, fill=INK, anchor="start", weight=400, rot=None, italic=False):
    tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot is not None else ""
    st = ' font-style="italic"' if italic else ""
    add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
        f'font-weight="{weight}"{st}{tr}>{esc(s)}</text>')


def para(x, y, lines, size=15, fill=INK, lh=None, weight=400):
    lh = lh or size * 1.45
    for i, ln in enumerate(lines):
        if isinstance(ln, tuple):
            text(x, y + i * lh, ln[0], size, ln[1], weight=ln[2] if len(ln) > 2 else weight)
        else:
            text(x, y + i * lh, ln, size, fill, weight=weight)
    return y + len(lines) * lh


def panel(x, y, w, h, title, sub=None):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{RULE}" stroke-width="1"/>')
    text(x + 18, y + 34, title, 21, INK, weight=650)
    if sub:
        text(x + 18, y + 58, sub, 14, MUTED)


def dim(x0, y0, x1, y1, label, off=0, side=1, size=13):
    """Horizontal or vertical dimension between page points; off moves it (px, +down / +right)."""
    g = f'<g stroke="{ACC}" stroke-width="1">'
    if abs(y1 - y0) <= abs(x1 - x0):
        y = y0 + off
        add(g + f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}"/>'
            f'<line x1="{x0:.1f}" y1="{y - 6:.1f}" x2="{x0:.1f}" y2="{y + 6:.1f}"/>'
            f'<line x1="{x1:.1f}" y1="{y - 6:.1f}" x2="{x1:.1f}" y2="{y + 6:.1f}"/></g>')
        if off:
            add(f'<g stroke="{ACC}" stroke-width=".6" stroke-opacity=".55"><line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x0:.1f}" y2="{y:.1f}"/>'
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x1:.1f}" y2="{y:.1f}"/></g>')
        if label:
            text((x0 + x1) / 2, y - 5 if side > 0 else y + 16, label, size, ACC, "middle")
    else:
        x = x0 + off
        add(g + f'<line x1="{x:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y1:.1f}"/>'
            f'<line x1="{x - 6:.1f}" y1="{y0:.1f}" x2="{x + 6:.1f}" y2="{y0:.1f}"/>'
            f'<line x1="{x - 6:.1f}" y1="{y1:.1f}" x2="{x + 6:.1f}" y2="{y1:.1f}"/></g>')
        if off:
            add(f'<g stroke="{ACC}" stroke-width=".6" stroke-opacity=".55"><line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y0:.1f}"/>'
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y1:.1f}"/></g>')
        if label:
            cx, cy = (x - 6 if side > 0 else x + 15), (y0 + y1) / 2
            text(cx, cy, label, size, ACC, "middle", rot=-90)


def leader(x0, y0, x1, y1, label, anchor="start", size=13, fill=MUTED, weight=400):
    add(f'<polyline points="{x0:.1f},{y0:.1f} {x1:.1f},{y1:.1f}" fill="none" stroke="{MUTED}" '
        f'stroke-width="0.9"/><circle cx="{x0:.1f}" cy="{y0:.1f}" r="2.2" fill="{MUTED}"/>')
    text(x1 + (4 if anchor == "start" else -4), y1 + 4, label, size, fill, anchor, weight=weight)


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------
def rot(lx, ly, yaw):
    a = math.radians(yaw)
    return lx * math.cos(a) - ly * math.sin(a), lx * math.sin(a) + ly * math.cos(a)


def to_world(o, lx, ly):
    dx, dy = rot(lx, ly, o.get("yaw", 0))
    return o["x"] + dx, o["y"] + dy


def rect_local(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def foot(o, x0=None, x1=None, y0=None, y1=None):
    """World footprint polygon of an object from its local rectangle (default: centred w x d)."""
    x0 = -o["w"] / 2 if x0 is None else x0
    x1 = o["w"] / 2 if x1 is None else x1
    y0 = -o["d"] / 2 if y0 is None else y0
    y1 = o["d"] / 2 if y1 is None else y1
    return [to_world(o, x, y) for x, y in rect_local(x0, x1, y0, y1)]


PIANO_O = dict(L["piano"])
PIANO_FOOT = foot(PIANO_O, -P["width"] / 2, P["width"] / 2, P["toe_front_y"], P["lid_over_back"])
BENCH_O = dict(x=0, y=0, yaw=PIANO_O["yaw"])
BENCH_CY = B["cy"] + L["piano"]["bench_in"]      # at rest, pushed in under the keys
BENCH_FOOT = [to_world(PIANO_O, x, y) for x, y in
              rect_local(-B["w"] / 2, B["w"] / 2, BENCH_CY - B["d"] / 2, BENCH_CY + B["d"] / 2)]
BENCH_PLAY = [to_world(PIANO_O, x, y) for x, y in
              rect_local(-B["w"] / 2, B["w"] / 2, B["cy"] - B["d"] / 2, B["cy"] + B["d"] / 2)]
DESK_FOOT = foot(L["desk"])
BED_FOOT = foot(L["bed"])
SHELF_FOOT = foot(L["bookshelf"])
CHAIR_FOOT = foot(L["chair"])
RUG_FOOT = foot(L["rug"])
MON = L["monitor"]
SPK = L["speakers"]
LISTEN = (MON["x"], L["desk"]["y"] - L["desk"]["d"] / 2 - 0.45)   # head of someone seated at the desk


def speaker_objs():
    """Both studio monitors, toed in toward the listening point."""
    res = []
    for i, s in enumerate((-1, 1)):
        x = MON["x"] + s * SPK["dx"]
        y = SPK["y"]
        toe = math.degrees(math.atan2(LISTEN[0] - x, -(LISTEN[1] - y)))   # yaw that points -Y at the listener
        res.append(dict(x=x, y=y, yaw=toe, w=SPK["w"], d=SPK["d"], toe=abs(toe)))
    return res


SPEAKERS = speaker_objs()


RACK = dict(L["rack"])          # option A, as in constants; build_scene() can be given option B


def rack_slots(rk=None):
    """Rack guitars: guitar_04 to _06 by slot. Each stands in the rack's local X-Z plane at its
    slot's local y, bottom on the cradle, leaning lean degrees toward local +X."""
    rk = rk or RACK
    gs = [dict(name="guitar_04", length=0.99, width=0.34, look="single-cut, amber flame top"),
          dict(name="guitar_05", length=1.00, width=0.47, look="Explorer-style, off-white"),
          dict(name="guitar_06", length=0.98, width=0.32, look="modern double-cut, mauve")]
    slots = [(i - (rk["slots"] - 1) / 2) * rk["pitch"] for i in range(rk["slots"])]
    return rk, gs, slots


def guitar_outline(length, width, archtop=False, n=40):
    """Flat guitar silhouette in its own plane: (u across, v up from the bottom): body, neck, head."""
    bh = length * (0.47 if archtop else 0.42)
    # half-width along the body, bottom to top: lower bout, waist, upper bout
    prof = [(0.0, 0.0), (0.04, 0.62), (0.12, 0.88), (0.28, 1.0), (0.44, 0.93), (0.58, 0.74), (0.66, 0.70),
            (0.78, 0.78), (0.88, 0.74), (0.96, 0.52), (1.0, 0.2)]
    if archtop:
        prof = [(t, f if t < 0.55 else f * 1.08) for t, f in prof]

    def f(t):
        for (t0, f0), (t1, f1) in zip(prof, prof[1:]):
            if t <= t1:
                k = (t - t0) / (t1 - t0)
                k = 0.5 - 0.5 * math.cos(math.pi * k)
                return f0 + (f1 - f0) * k
        return prof[-1][1]
    ts = [i / n for i in range(n + 1)]
    right = [(f(t) * width / 2, t * bh) for t in ts]
    body = right + [(-x, v) for x, v in reversed(right[1:-1])]
    nw = 0.046
    neck = [(-nw / 2, bh * 0.9), (nw / 2, bh * 0.9), (nw / 2 * 0.85, length - 0.19), (-nw / 2 * 0.85, length - 0.19)]
    hw = 0.085
    head = [(-nw / 2 * 0.85, length - 0.19), (hw / 2, length - 0.15), (hw / 2 * 0.9, length), (-hw / 2 * 0.5, length)]
    return body, neck, head


# ---------------------------------------------------------------------------
# clash check (convex polygons: separating axis; distance by edges)
# ---------------------------------------------------------------------------
def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _overlap(A, Bp):
    for poly in (A, Bp):
        for i in range(len(poly)):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % len(poly)]
            nx, ny = y0 - y1, x1 - x0
            pa = [nx * x + ny * y for x, y in A]
            pb = [nx * x + ny * y for x, y in Bp]
            if max(pa) <= min(pb) or max(pb) <= min(pa):
                return False
    return True


def gap(A, Bp):
    if _overlap(A, Bp):
        return -1.0
    d = 1e9
    for P1, P2 in ((A, Bp), (Bp, A)):
        for p in P1:
            for i in range(len(P2)):
                d = min(d, _seg_dist(p, P2[i], P2[(i + 1) % len(P2)]))
    return d


def rack_foot():
    rk = L["rack"]
    return foot(rk)


CHECKS = []


def run_checks():
    lid90 = max(z for _, z in lid_profile(90)[0])
    lid55 = max(z for _, z in lid_profile(P["lid_open_deg"])[0])
    items = [
        ("bed to desk", BED_FOOT, DESK_FOOT, 0.03),
        ("desk to rack", DESK_FOOT, rack_foot(), 0.02),
        ("rack to piano", rack_foot(), PIANO_FOOT, 0.01),
        ("rack to bench", rack_foot(), BENCH_FOOT, 0.04),
        ("rack to bench, played", rack_foot(), BENCH_PLAY, 0.04),
        ("chair to bench", CHAIR_FOOT, BENCH_FOOT, 0.25),
        ("bed to bench", BED_FOOT, BENCH_FOOT, 1.0),
        ("bookshelf to bed", SHELF_FOOT, BED_FOOT, 0.04),
    ]
    for name, A, Bp, need in items:
        g = gap(A, Bp)
        CHECKS.append((name, g, need, g >= need))
    clear = WG["bottom"] - lid90
    CHECKS.append(("lid at 90 deg to lowest guitar", clear, 0.05, clear >= 0.05))
    top = WG["bottom"] + max(WG["length"])
    CHECKS.append(("tallest guitar to ceiling", H - top, 0.15, H - top >= 0.15))
    door_r = DOOR["y1"] - DOOR["y0"] - 0.05
    CHECKS.append(("door swing to bookshelf", L["bookshelf"]["y"] - L["bookshelf"]["w"] / 2 - (DOOR["y0"] + door_r), 0.0,
                   L["bookshelf"]["y"] - L["bookshelf"]["w"] / 2 >= DOOR["y0"] + 0.0))
    CHECKS.append(("window sill over headboard", WIN["sill"] - L["bed"]["head_h"], 0.03,
                   WIN["sill"] - L["bed"]["head_h"] >= 0.03))
    return lid90, lid55


# ---------------------------------------------------------------------------
# camera
# ---------------------------------------------------------------------------
class Cam:
    def __init__(self, pos, target, vfov, aspect):
        self.c = pos
        dx, dy, dz = (target[i] - pos[i] for i in range(3))
        self.yaw = math.atan2(dx, dy)
        self.pitch = math.atan2(dz, math.hypot(dx, dy))
        cy, sy, cp, sp = math.cos(self.yaw), math.sin(self.yaw), math.cos(self.pitch), math.sin(self.pitch)
        self.f = (sy * cp, cy * cp, sp)
        self.r = (cy, -sy, 0.0)
        f, r = self.f, self.r
        self.u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
        self.tv = math.tan(math.radians(vfov) / 2)
        self.th = self.tv * aspect
        self.vfov, self.aspect = vfov, aspect
        self.hfov = 2 * math.degrees(math.atan(self.th))

    def cam(self, p):
        d = [p[i] - self.c[i] for i in range(3)]
        return (sum(d[i] * self.r[i] for i in range(3)), sum(d[i] * self.u[i] for i in range(3)),
                sum(d[i] * self.f[i] for i in range(3)))

    def ndc(self, q):
        x, y, z = q
        return x / z / self.th, y / z / self.tv

    def visible(self, p):
        x, y, z = self.cam(p)
        if z <= 0.05:
            return False
        a, b = self.ndc((x, y, z))
        return abs(a) <= 1 and abs(b) <= 1


def clip_near(poly, zn=0.06):
    outp = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = a[2] > zn, b[2] > zn
        if ina:
            outp.append(a)
        if ina != inb:
            t = (zn - a[2]) / (b[2] - a[2])
            outp.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
    return outp


def hull(pts):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def shade(hexcol, k):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda c: max(0, min(255, int(c * k)))  # noqa: E731
    return f"#{f(r):02x}{f(g):02x}{f(b):02x}"


LIGHT_DIR = (-0.35, 0.80, 0.45)       # toward the window: faces turned to it are lighter
_ln = math.sqrt(sum(c * c for c in LIGHT_DIR))
LIGHT_DIR = tuple(c / _ln for c in LIGHT_DIR)


class Scene:
    """Flat-shaded painter's sketch: room shell first, wall items next, then all faces by depth."""
    def __init__(self):
        self.shell, self.wall, self.wall2, self.faces, self.lines, self.marks = [], [], [], [], [], {}
        self.wall_lines = []

    def quad(self, pts, col, layer="faces", stroke=None, alpha=1.0, shade_it=True, tile=None):
        if tile:
            # split a big rectangle into tiles so the depth sort stays local
            (a, b, c, d) = pts
            n, m = tile
            for i in range(n):
                for j in range(m):
                    def lerp(p, q, t):
                        return tuple(p[k] + (q[k] - p[k]) * t for k in range(3))
                    u0, u1, v0, v1 = i / n, (i + 1) / n, j / m, (j + 1) / m
                    p00 = lerp(lerp(a, b, u0), lerp(d, c, u0), v0)
                    p10 = lerp(lerp(a, b, u1), lerp(d, c, u1), v0)
                    p11 = lerp(lerp(a, b, u1), lerp(d, c, u1), v1)
                    p01 = lerp(lerp(a, b, u0), lerp(d, c, u0), v1)
                    self.quad([p00, p10, p11, p01], col, layer, "same", alpha, shade_it)
            return
        getattr(self, layer).append((pts, col, stroke, alpha, shade_it))

    def box(self, x0, x1, y0, y1, z0, z1, col, yaw=0, origin=(0, 0), stroke=None, tile_top=None, layer="faces"):
        ox, oy = origin
        c = []
        for (x, y) in rect_local(x0, x1, y0, y1):
            dx, dy = rot(x, y, yaw)
            c.append((ox + dx, oy + dy))
        b = [(x, y, z0) for x, y in c]
        t = [(x, y, z1) for x, y in c]
        self.quad([t[0], t[1], t[2], t[3]], col, layer, stroke, tile=tile_top)       # top
        self.quad([b[3], b[2], b[1], b[0]], col, layer, stroke)                       # bottom
        for i in range(4):
            j = (i + 1) % 4
            self.quad([b[i], b[j], t[j], t[i]], col, layer, stroke)

    def prism(self, cx, cy, r, z0, z1, col, n=12, layer="faces", r_top=None):
        r_top = r if r_top is None else r_top
        bot = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z0) for i in range(n)]
        top = [(cx + r_top * math.cos(2 * math.pi * i / n), cy + r_top * math.sin(2 * math.pi * i / n), z1) for i in range(n)]
        self.quad(top, col, layer)
        self.quad(bot[::-1], col, layer)
        for i in range(n):
            j = (i + 1) % n
            self.quad([bot[i], bot[j], top[j], top[i]], col, layer)

    def flat(self, pts3, col, layer="wall", stroke=None, alpha=1.0):
        self.quad(pts3, col, layer, stroke, alpha, shade_it=False)

    def render(self, cam, x0, y0, w, h, label_marks=True):
        def page(q):
            a, b = cam.ndc(q)
            return x0 + (a + 1) / 2 * w, y0 + (1 - b) / 2 * h

        def draw(pts, col, stroke, alpha, shade_it, cull=True):
            qs = clip_near([cam.cam(p) for p in pts])
            if len(qs) < 3:
                return
            if cull:
                # back-face cull in camera space (normal from the first three points)
                ax, ay, az = qs[0]
                bx, by, bz = qs[1]
                cx, cy, cz = qs[2]
                n = ((by - ay) * (cz - az) - (bz - az) * (cy - ay), (bz - az) * (cx - ax) - (bx - ax) * (cz - az),
                     (bx - ax) * (cy - ay) - (by - ay) * (cx - ax))
                if n[0] * ax + n[1] * ay + n[2] * az <= 0:
                    return
            k = 1.0
            if shade_it:
                p0, p1, p2 = pts[0], pts[1], pts[2]
                u = [p1[i] - p0[i] for i in range(3)]
                v = [p2[i] - p0[i] for i in range(3)]
                nn = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                ln = math.sqrt(sum(c * c for c in nn)) or 1
                d = sum(nn[i] / ln * LIGHT_DIR[i] for i in range(3))
                k = 0.78 + 0.30 * d
            pp = " ".join(f"{a:.1f},{b:.1f}" for a, b in (page(q) for q in qs))
            if stroke == "same":
                st = f'stroke="{shade(col, k)}" stroke-width="0.6"'
            elif stroke:
                st = f'stroke="{stroke}" stroke-width="0.7"'
            else:
                st = None
            st = st if st else f'stroke="{shade(col, k * 0.8)}" stroke-width="0.5"'
            add(f'<polygon points="{pp}" fill="{shade(col, k)}" fill-opacity="{alpha}" {st} stroke-linejoin="round"/>')

        def polyline(pts, col, sw):
            qs = [cam.cam(p) for p in pts]
            if any(q[2] <= 0.06 for q in qs):
                return
            pp = " ".join(f"{a:.1f},{b:.1f}" for a, b in (page(q) for q in qs))
            add(f'<polyline points="{pp}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')

        add(f'<svg x="{x0}" y="{y0}" width="{w}" height="{h}" viewBox="{x0} {y0} {w} {h}" overflow="hidden">')
        for f in self.shell:
            draw(*f, cull=False)
        wall = sorted(self.wall, key=lambda f: -sum(cam.cam(p)[2] for p in f[0]) / len(f[0]))
        for f in wall:
            draw(*f, cull=False)
        for f in sorted(self.wall2, key=lambda f: -sum(cam.cam(p)[2] for p in f[0]) / len(f[0])):
            draw(*f, cull=False)
        for pts, col, sw in self.wall_lines:
            polyline(pts, col, sw)
        faces = sorted(self.faces, key=lambda f: -sum(cam.cam(p)[2] for p in f[0]) / len(f[0]))
        for f in faces:
            draw(*f, cull=f[3] >= 1.0)
        for pts, col, sw in self.lines:
            polyline(pts, col, sw)
        add("</svg>")
        # markers for the nine objects (drawn outside the clip so labels can sit on the edge)
        placed = []
        if label_marks:
            for key, (p, num) in self.marks.items():
                q = cam.cam(p)
                if q[2] <= 0.06:
                    continue
                a, b = cam.ndc(q)
                if abs(a) > 1 or abs(b) > 1:
                    continue
                px, py = page(q)
                add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="13" fill="{OBJ_LINE}" stroke="#fff" stroke-width="2"/>')
                text(px, py + 5, str(num), 14, "#fff", "middle", weight=700)
                placed.append(key)
        return placed


def build_scene(rack=None):
    S = Scene()
    oak, wallc, ceil = "#6b4a32", "#a9adbb", "#8d91a0"
    # shell
    S.flat([(-RX, -RY, 0), (RX, -RY, 0), (RX, RY, 0), (-RX, RY, 0)], oak, "shell")
    S.flat([(-RX, RY, 0), (RX, RY, 0), (RX, RY, H), (-RX, RY, H)], "#b3b6c3", "shell")           # back
    S.flat([(-RX, -RY, 0), (-RX, RY, 0), (-RX, RY, H), (-RX, -RY, H)], "#a3a7b6", "shell")       # left
    S.flat([(RX, RY, 0), (RX, -RY, 0), (RX, -RY, H), (RX, RY, H)], "#999dac", "shell")           # right
    S.flat([(-RX, RY, H), (RX, RY, H), (RX, -RY, H), (-RX, -RY, H)], ceil, "shell")
    sk = R["skirting_h"]
    for pts in ([(-RX, RY - 0.001, 0), (RX, RY - 0.001, 0), (RX, RY - 0.001, sk), (-RX, RY - 0.001, sk)],
                [(-RX + 0.001, -RY, 0), (-RX + 0.001, RY, 0), (-RX + 0.001, RY, sk), (-RX + 0.001, -RY, sk)],
                [(RX - 0.001, RY, 0), (RX - 0.001, -RY, 0), (RX - 0.001, -RY, sk), (RX - 0.001, RY, sk)]):
        S.flat(pts, "#d9d6cf", "shell")
    # rug
    S.flat([(*p, 0.004) for p in RUG_FOOT], "#7c7f8c", "shell")
    # window: sky, frame, ledge
    wy = RY - 0.002
    S.flat([(WIN["x0"], wy, WIN["sill"]), (WIN["x1"], wy, WIN["sill"]), (WIN["x1"], wy, WIN["head"]),
            (WIN["x0"], wy, WIN["head"])], "#6f8fcf", "wall", stroke="#e8e6e0")
    xm = (WIN["x0"] + WIN["x1"]) / 2
    S.wall_lines.append(([(xm, wy - 0.01, WIN["sill"]), (xm, wy - 0.01, WIN["head"])], "#e8e6e0", 2.4))
    for k in range(1, 9):
        z = WIN["sill"] + (WIN["head"] - WIN["sill"]) * k / 9
        S.wall_lines.append(([(WIN["x0"], wy - 0.02, z), (WIN["x1"], wy - 0.02, z)], "#3b3f4a", 0.8))
    S.box(WIN["x0"] - 0.04, WIN["x1"] + 0.04, RY - WIN["ledge_d"], RY, WIN["sill"] - WIN["ledge_t"], WIN["sill"], "#8a8478", layer="wall")
    # panels
    pg = L["panels_guitar"]
    S.box(RX - pg["t"], RX, pg["y0"], pg["y1"], pg["z0"], pg["z1"], "#34353b", layer="wall")
    pdk = L["panels_desk"]
    for x in pdk["x"]:
        S.box(x - pdk["w"] / 2, x + pdk["w"] / 2, RY - pdk["t"], RY, pdk["z0"], pdk["z1"], "#5b6170", layer="wall")
    # frames
    fr = L["frames"]
    for i, y in enumerate(fr["y"]):
        S.box(-RX, -RX + fr["t"], y - fr["w"] / 2, y + fr["w"] / 2, fr["z"] - fr["h"] / 2, fr["z"] + fr["h"] / 2,
              "#1f1d1b", layer="wall")
        S.flat([(-RX + fr["t"] + 0.002, y - fr["w"] / 2 + 0.035, fr["z"] - fr["h"] / 2 + 0.04),
                (-RX + fr["t"] + 0.002, y + fr["w"] / 2 - 0.035, fr["z"] - fr["h"] / 2 + 0.04),
                (-RX + fr["t"] + 0.002, y + fr["w"] / 2 - 0.035, fr["z"] + fr["h"] / 2 - 0.04),
                (-RX + fr["t"] + 0.002, y - fr["w"] / 2 + 0.035, fr["z"] + fr["h"] / 2 - 0.04)],
               ["#c98a4a", "#5d7f9e", "#9aa27a"][i], "faces")
    # switch
    sw = C.SWITCH
    S.flat([(-RX + 0.002, sw["y"] - sw["w"] / 2, sw["z"] - sw["h"] / 2), (-RX + 0.002, sw["y"] + sw["w"] / 2, sw["z"] - sw["h"] / 2),
            (-RX + 0.002, sw["y"] + sw["w"] / 2, sw["z"] + sw["h"] / 2), (-RX + 0.002, sw["y"] - sw["w"] / 2, sw["z"] + sw["h"] / 2)],
           "#eeeeea", "wall")
    # wall guitars
    gx = RX - WG["off_wall"]
    cols = ["#b5651d", "#f1efe8", "#8a4b1f"]
    for i, y in enumerate(WG["y"]):
        body, neck, head = guitar_outline(WG["length"][i], WG["width"][i], archtop=(i == 0))
        for part, col in ((neck, "#5b3a22"), (head, "#2a1d14"), (body, cols[i])):
            S.flat([(gx, y - u, WG["bottom"] + v) for u, v in part], col, "wall2")
        hook_z = WG["bottom"] + WG["length"][i] - WG["hook_from_top"][i]
        S.wall_lines.append(([(RX - 0.05, y, hook_z - 0.03), (gx, y, hook_z)], "#c8c8c8", 2.5))
    # bed
    bd = L["bed"]
    bx0, bx1 = bd["x"] - bd["w"] / 2, bd["x"] + bd["w"] / 2
    by0, by1 = bd["y"] - bd["d"] / 2, bd["y"] + bd["d"] / 2
    S.box(bx0, bx1, by0, by1 - 0.05, 0.0, 0.32, "#4b3426")
    S.box(bx0 + 0.02, bx1 - 0.02, by0 + 0.02, by1 - 0.07, 0.32, bd["h"], "#c9cdd8", tile_top=(4, 6))
    S.box(bx0, bx1, by1 - 0.05, by1, 0.0, bd["head_h"], "#4b3426")
    for k in range(2):
        px0 = bx0 + 0.08 + k * 0.66
        S.box(px0, px0 + 0.58, by1 - 0.45, by1 - 0.12, bd["h"], bd["h"] + 0.12, "#e4e4ea")
    # bookshelf
    bs = L["bookshelf"]
    S.box(-RX, -RX + bs["d"], bs["y"] - bs["w"] / 2, bs["y"] + bs["w"] / 2, 0, bs["h"], "#3e2c20")
    # desk
    dk = L["desk"]
    dx0, dx1 = dk["x"] - dk["w"] / 2, dk["x"] + dk["w"] / 2
    dy0, dy1 = dk["y"] - dk["d"] / 2, dk["y"] + dk["d"] / 2
    S.box(dx0, dx1, dy0, dy1, dk["h"] - dk["top_t"], dk["h"], "#2a2420", tile_top=(8, 4))
    for (x, y) in ((dx0 + 0.04, dy0 + 0.04), (dx1 - 0.04, dy0 + 0.04), (dx0 + 0.04, dy1 - 0.04), (dx1 - 0.04, dy1 - 0.04)):
        S.box(x - 0.025, x + 0.025, y - 0.025, y + 0.025, 0, dk["h"] - dk["top_t"], "#1c1916")
    top = dk["h"]
    # monitor
    mz0, mz1 = MON["z"] - MON["h"] / 2, MON["z"] + MON["h"] / 2
    S.box(MON["x"] - 0.11, MON["x"] + 0.11, MON["y"] - 0.02, MON["y"] + 0.14, top, top + 0.012, "#16181d")
    S.box(MON["x"] - 0.025, MON["x"] + 0.025, MON["y"] + 0.05, MON["y"] + 0.08, top, mz0 + 0.1, "#16181d")
    S.box(MON["x"] - MON["w"] / 2, MON["x"] + MON["w"] / 2, MON["y"], MON["y"] + MON["t"], mz0, mz1, "#16181d")
    S.flat([(MON["x"] - 0.28, MON["y"] - 0.002, MON["z"] - 0.175), (MON["x"] + 0.28, MON["y"] - 0.002, MON["z"] - 0.175),
            (MON["x"] + 0.28, MON["y"] - 0.002, MON["z"] + 0.175), (MON["x"] - 0.28, MON["y"] - 0.002, MON["z"] + 0.175)],
           "#5aa0e6", "faces")
    # speakers on pads
    for s in SPEAKERS:
        S.box(-0.10, 0.10, -0.135, 0.135, top, top + SPK["pad_h"], "#3a3b40", yaw=s["yaw"], origin=(s["x"], s["y"]))
        S.box(-SPK["w"] / 2, SPK["w"] / 2, -SPK["d"] / 2, SPK["d"] / 2, top + SPK["pad_h"], top + SPK["pad_h"] + SPK["h"],
              "#1e1f23", yaw=s["yaw"], origin=(s["x"], s["y"]))
        cx, cy = to_world(s, 0, -SPK["d"] / 2 - 0.002)
        S.lines.append(([(cx, cy, top + SPK["pad_h"] + 0.09), (cx, cy, top + SPK["pad_h"] + 0.095)], "#d9d3c4", 9))
    # desk items
    for key, col in (("dj", "#2f3035"), ("interface", "#45474e"), ("keyboard", "#d8d6d0")):
        o = L[key]
        hh = o.get("h", 0.02)
        S.box(o["x"] - o["w"] / 2, o["x"] + o["w"] / 2, o["y"] - o["d"] / 2, o["y"] + o["d"] / 2, top, top + hh, col)
    dj = L["dj"]
    for s in (-1, 1):
        S.flat([(dj["x"] + s * 0.12 + 0.065 * math.cos(2 * math.pi * i / 16), dj["y"] + 0.03 + 0.065 * math.sin(2 * math.pi * i / 16),
                 top + dj["h"] + 0.002) for i in range(16)], "#5a5c63", "faces")
    ls = L["lightstick"]
    S.box(ls["x"] - ls["w"] / 2, ls["x"] + 0.03, ls["y"] - 0.018, ls["y"] + 0.018, top, top + 0.036, "#f2f2f2")
    S.box(ls["x"] + 0.03, ls["x"] + ls["w"] / 2, ls["y"] - ls["d"] / 2, ls["y"] + ls["d"] / 2, top, top + ls["h"], "#e9c6f2")
    # mic arm
    mc = L["mic"]
    cl = (*mc["clamp"], top)
    S.lines.append(([cl, (cl[0], cl[1], top + 0.08), mc["elbow"], mc["capsule"]], "#26272b", 3.2))
    S.prism(mc["capsule"][0], mc["capsule"][1], 0.028, mc["capsule"][2] - 0.07, mc["capsule"][2] + 0.06, "#2b2c30")
    # chair
    ch = L["chair"]
    S.box(-0.25, 0.25, -0.25, 0.25, ch["seat"] - 0.07, ch["seat"], "#2c2d33", yaw=ch["yaw"], origin=(ch["x"], ch["y"]))
    S.box(-0.23, 0.23, 0.21, 0.26, ch["seat"] + 0.05, ch["h"], "#2c2d33", yaw=ch["yaw"], origin=(ch["x"], ch["y"]))
    S.prism(ch["x"], ch["y"], 0.025, 0.08, ch["seat"] - 0.07, "#1b1b1f", n=6)
    for k in range(5):
        a = 2 * math.pi * k / 5
        S.lines.append(([(ch["x"], ch["y"], 0.08), (ch["x"] + 0.31 * math.cos(a), ch["y"] + 0.31 * math.sin(a), 0.04)],
                        "#1b1b1f", 3))
    # rack and its guitars
    rk, gs, slots = rack_slots(rack)
    o = dict(x=rk["x"], y=rk["y"], yaw=rk["yaw"])
    S.box(-rk["w"] / 2, rk["w"] / 2 - 0.20, -rk["d"] / 2, rk["d"] / 2, rk["cradle"] - 0.03, rk["cradle"], "#232326",
          yaw=rk["yaw"], origin=(rk["x"], rk["y"]))
    bar_x = -0.08 + 0.70 * math.sin(math.radians(rk["lean"]))
    bar_z = rk["cradle"] + 0.70 * math.cos(math.radians(rk["lean"]))
    S.box(bar_x, bar_x + 0.03, -rk["d"] / 2, rk["d"] / 2, bar_z - 0.03, bar_z, "#232326", yaw=rk["yaw"], origin=(rk["x"], rk["y"]))
    for s in (-1, 1):
        S.box(-0.12, bar_x + 0.03, s * rk["d"] / 2 - 0.012, s * rk["d"] / 2 + 0.012, 0, 0.03, "#232326",
              yaw=rk["yaw"], origin=(rk["x"], rk["y"]))
        S.box(bar_x, bar_x + 0.025, s * rk["d"] / 2 - 0.012, s * rk["d"] / 2 + 0.012, 0, bar_z, "#232326",
              yaw=rk["yaw"], origin=(rk["x"], rk["y"]))
    rcols = ["#c0762a", "#ece8dc", "#a98aa9"]
    lean = math.radians(rk["lean"])
    for i, (g, sl) in enumerate(zip(gs, slots)):
        body, neck, head = guitar_outline(g["length"], g["width"])
        for part, col in ((neck, "#5b3a22"), (head, "#2a1d14"), (body, rcols[i])):
            pts = []
            for u, v in part:
                lu = -0.08 + u * math.cos(lean) + v * math.sin(lean)
                lv = rk["cradle"] - u * math.sin(lean) + v * math.cos(lean)
                wx, wy2 = to_world(o, lu, sl)
                pts.append((wx, wy2, lv))
            S.quad(pts, col, "faces", alpha=0.999, shade_it=False)
    # piano: case, keybed, consoles, bench (boxes in the piano's frame)
    po = PIANO_O
    pyaw = po["yaw"]
    org = (po["x"], po["y"])
    hw = P["width"] / 2
    lac = "#141416"
    S.box(-hw, hw, P["panel_face_y"], P["lid_over_back"], P["panel_bottom"], P["case_top"] + P["lid_t"], lac, yaw=pyaw, origin=org)
    S.box(-hw + 0.03, hw - 0.03, P["slip_front_y"], P["panel_face_y"], P["slip_top"] - 0.05, P["slip_top"], lac, yaw=pyaw, origin=org)
    S.box(-hw + 0.06, hw - 0.06, P["key_back_y"] - P["white_len"], P["panel_face_y"], P["slip_top"], C.KT, "#ece6d6",
          yaw=pyaw, origin=org)
    S.box(-hw, hw, P["lower_face_y"], 0.0, P["floor_gap"], P["panel_bottom"], lac, yaw=pyaw, origin=org)
    for s in (-1, 1):
        S.box(s * P["toe_x"] - P["toe_w"] / 2, s * P["toe_x"] + P["toe_w"] / 2, P["toe_front_y"], P["toe_back_y"], 0,
              P["cheek_top"], lac, yaw=pyaw, origin=org)
    S.box(-B["w"] / 2, B["w"] / 2, BENCH_CY - B["d"] / 2, BENCH_CY + B["d"] / 2, B["h"] - B["t"], B["h"], lac, yaw=pyaw, origin=org)
    for sx in (-1, 1):
        for sy in (-1, 1):
            S.box(sx * B["leg_x"] - 0.025, sx * B["leg_x"] + 0.025, BENCH_CY + sy * (B["d"] / 2 - 0.05) - 0.025,
                  BENCH_CY + sy * (B["d"] / 2 - 0.05) + 0.025, 0, B["h"] - B["t"], lac, yaw=pyaw, origin=org)
    # sheet music on the rest (About)
    sx0, sy_ = to_world(po, -P["sheet_w"] / 2, P["ledge_front_y"] + 0.03)
    sx1, sy1 = to_world(po, P["sheet_w"] / 2, P["ledge_front_y"] + 0.03)
    z0s = P["ledge_lip_top"]
    S.quad([(sx0, sy_, z0s), (sx1, sy1, z0s), (sx1 + 0.03, sy1, z0s + P["sheet_h"]), (sx0 + 0.03, sy_, z0s + P["sheet_h"])],
           "#f4f1e8", "faces", shade_it=False, alpha=0.999)
    # plant on the sill
    pl = L["plant"]
    S.prism(pl["x"], pl["y"], pl["pot_d"] / 2, WIN["sill"], WIN["sill"] + 0.13, "#b4553a", r_top=pl["pot_d"] / 2 * 1.1)
    for k, (dx, dz, r) in enumerate(((0.0, 0.25, 0.09), (-0.07, 0.20, 0.06), (0.07, 0.22, 0.065))):
        S.prism(pl["x"] + dx, pl["y"], r, WIN["sill"] + dz - r * 0.6, WIN["sill"] + dz + r * 0.6, "#4f7a46", n=10)
    # ceiling light
    lt = C.LIGHT
    S.lines.append(([(lt["x"], lt["y"], H), (lt["x"], lt["y"], H - lt["drop"])], "#3a3a3a", 1.6))
    S.prism(lt["x"], lt["y"], lt["canopy_d"] / 2, H - 0.03, H, "#dcdcdc")
    zb = H - lt["drop"] - lt["shade_h"]
    S.prism(lt["x"], lt["y"], lt["shade_d"] / 2, zb, zb + lt["shade_h"] * 0.5, "#ecebe6", n=16, r_top=lt["shade_d"] / 2 * 0.9)
    S.prism(lt["x"], lt["y"], lt["shade_d"] / 2 * 0.9, zb + lt["shade_h"] * 0.5, zb + lt["shade_h"], "#ecebe6", n=16,
            r_top=lt["shade_d"] / 2 * 0.35)

    # markers: the nine objects (number, anchor point)
    S.marks = {
        "piano": ((po["x"] - 0.32, po["y"], 1.05), 1),
        "guitars": ((RX - 0.12, WG["y"][1], WG["bottom"] + 0.30), 2),
        "rack": ((rk["x"], rk["y"], 0.55), 2),
        "monitor": ((MON["x"], MON["y"] - 0.01, MON["z"] + 0.10), 3),
        "mic": (mc["capsule"], 4),
        "frames": ((-RX + 0.03, fr["y"][1], fr["z"] + 0.30), 5),
        "studio": ((dj["x"], dj["y"], top + 0.08), 6),
        "light": ((lt["x"], lt["y"], zb - 0.08), 7),
        "window": ((WIN["x0"] + 0.25, RY, WIN["head"] - 0.25), 8),
        "plant": ((pl["x"], pl["y"], WIN["sill"] + 0.45), 9),
    }
    return S


NINE = [(1, "Upright piano", "obj_piano"), (2, "Guitars: wall 01 to 03, rack 04 to 06", "obj_guitars"),
        (3, "Desk monitor, the posts screen", "obj_monitor"), (4, "Mic on its arm", "obj_mic"),
        (5, "Three picture frames", "obj_frames"), (6, "Studio desk: DJ controller, interface, speakers, lightstick", "obj_studio"),
        (7, "Ceiling light", "obj_light"), (8, "Window", "obj_window"), (9, "Plant on the sill", "obj_plant")]


def visibility(cam):
    """Share of sample points of each object inside the frame (no occlusion)."""
    def share(pts):
        return sum(cam.visible(p) for p in pts) / len(pts)

    def boxpts(x0, x1, y0, y1, z0, z1, n=5):
        return [(x0 + (x1 - x0) * i / (n - 1), y0 + (y1 - y0) * j / (n - 1), z0 + (z1 - z0) * k / (n - 1))
                for i in range(n) for j in range(n) for k in range(n)]
    xs = [p[0] for p in PIANO_FOOT]
    ys = [p[1] for p in PIANO_FOOT]
    res = {"piano": share(boxpts(min(xs), max(xs), min(ys), max(ys), 0, P["case_top"]))}
    gpts = []
    for i, y in enumerate(WG["y"]):
        gpts += boxpts(RX - 0.15, RX - 0.08, y - WG["width"][i] / 2, y + WG["width"][i] / 2, WG["bottom"],
                       WG["bottom"] + WG["length"][i], 4)
    rf = rack_foot()
    gpts += boxpts(min(p[0] for p in rf), max(p[0] for p in rf), min(p[1] for p in rf), max(p[1] for p in rf), 0.1, 1.07, 4)
    res["guitars"] = share(gpts)
    res["monitor"] = share(boxpts(MON["x"] - MON["w"] / 2, MON["x"] + MON["w"] / 2, MON["y"], MON["y"] + 0.03,
                                  MON["z"] - MON["h"] / 2, MON["z"] + MON["h"] / 2))
    mc = L["mic"]["capsule"]
    res["mic"] = share(boxpts(mc[0] - 0.03, mc[0] + 0.03, mc[1] - 0.03, mc[1] + 0.03, mc[2] - 0.07, mc[2] + 0.06, 3))
    fr = L["frames"]
    res["frames"] = share(boxpts(-RX, -RX + 0.03, min(fr["y"]) - fr["w"] / 2, max(fr["y"]) + fr["w"] / 2,
                                 fr["z"] - fr["h"] / 2, fr["z"] + fr["h"] / 2))
    dk = L["desk"]
    res["studio"] = share(boxpts(dk["x"] - dk["w"] / 2, dk["x"] + dk["w"] / 2, dk["y"] - dk["d"] / 2, dk["y"] + dk["d"] / 2,
                                 dk["h"], dk["h"] + 0.40))
    lt = C.LIGHT
    zb = H - lt["drop"] - lt["shade_h"]
    res["light"] = share(boxpts(lt["x"] - lt["shade_d"] / 2, lt["x"] + lt["shade_d"] / 2, lt["y"] - lt["shade_d"] / 2,
                                lt["y"] + lt["shade_d"] / 2, zb, zb + lt["shade_h"]))
    res["window"] = share(boxpts(WIN["x0"], WIN["x1"], RY - 0.02, RY, WIN["sill"], WIN["head"]))
    pl = L["plant"]
    res["plant"] = share(boxpts(pl["x"] - 0.08, pl["x"] + 0.08, pl["y"] - 0.07, pl["y"] + 0.07, WIN["sill"], WIN["sill"] + pl["h"], 3))
    return res


# ---------------------------------------------------------------------------
# 1. floor plan
# ---------------------------------------------------------------------------
class View:
    """World metres (u, v) to page pixels, v up."""
    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def p(self, u, v):
        return self.ox + u * self.s, self.oy - v * self.s

    def poly(self, pts, fill, stroke=INK, sw=1.1, extra=""):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in (self.p(u, v) for u, v in pts))
        add(f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>')

    def rect(self, u0, u1, v0, v1, fill, stroke=INK, sw=1.1, rx=0, extra=""):
        x0, y0 = self.p(min(u0, u1), max(v0, v1))
        x1, y1 = self.p(max(u0, u1), min(v0, v1))
        add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def line(self, a, b, stroke=INK, sw=1.1, extra=""):
        (x0, y0), (x1, y1) = self.p(*a), self.p(*b)
        add(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def circle(self, u, v, r, fill, stroke=INK, sw=1.1, extra=""):
        x, y = self.p(u, v)
        add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * self.s:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def path(self, pts, stroke=INK, sw=1.1, fill="none", extra=""):
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (self.p(u, v) for u, v in pts))
        add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')


DASH = 'stroke-dasharray="6 4"'
DOT = 'stroke-dasharray="2 3"'


def draw_walls_plan(v):
    tb, ts = R["wall_back_t"], R["wall_side_t"]
    # poché: back, left, right, front
    v.rect(-RX - ts, RX + ts, RY, RY + tb, WALL_POCHE, WALL_POCHE, 0.5)
    v.rect(-RX - ts, -RX, -RY - ts, RY, WALL_POCHE, WALL_POCHE, 0.5)
    v.rect(RX, RX + ts, -RY - ts, RY, WALL_POCHE, WALL_POCHE, 0.5)
    v.rect(-RX - ts, RX + ts, -RY - ts, -RY, "#8d8880", "#8d8880", 0.5)      # front: bake only, lighter
    # window opening with glass and the ledge
    v.rect(WIN["x0"], WIN["x1"], RY, RY + tb, PAPER, PAPER, 0)
    v.line((WIN["x0"], RY + tb * 0.45), (WIN["x1"], RY + tb * 0.45), INK, 1.0)
    v.line((WIN["x0"], RY + tb * 0.58), (WIN["x1"], RY + tb * 0.58), INK, 1.0)
    v.rect(WIN["x0"] - 0.04, WIN["x1"] + 0.04, RY - (WIN["ledge_d"] - tb * 0.45), RY, "#d2ccc0", INK, 0.8)
    # door: opening, leaf open along the front wall, swing arc
    dy0, dy1 = DOOR["y0"], DOOR["y1"]
    v.rect(-RX - ts, -RX, dy0, dy1, PAPER, PAPER, 0)
    leaf = dy1 - dy0 - 0.05
    hx, hy = -RX, dy0
    v.rect(hx, hx + leaf, hy, hy + DOOR["leaf_t"], "#fff", INK, 1.0)
    arc = [(hx + leaf * math.sin(math.radians(a)), hy + leaf * math.cos(math.radians(a))) for a in range(0, 91, 3)]
    v.path(arc, MUTED, 0.9, extra=DASH)


def plan(px, py, pw, ph):
    panel(px, py, pw, ph, "1 · Floor plan", "top view, back wall at the top · dimensions in cm · blue: the nine objects, grey: scenery")
    s = 215
    v = View(px + 150 + RX * s, py + 205 + RY * s + R["wall_back_t"] * s, s)
    draw_walls_plan(v)
    # rug
    v.poly(RUG_FOOT, "#ece8e0", MUTED, 0.9, extra=DASH)
    rg = L["rug"]
    v.p(0, 0)
    # ceiling light (dashed, above)
    lt = C.LIGHT
    v.circle(lt["x"], lt["y"], lt["shade_d"] / 2, "none", OBJ_LINE, 1.1, extra=DASH)
    v.circle(lt["x"], lt["y"], 0.02, OBJ_LINE, OBJ_LINE, 1)
    # bed
    bd = L["bed"]
    v.poly(BED_FOOT, SET_FILL, INK, 1.1)
    bx0, bx1, by0, by1 = bd["x"] - bd["w"] / 2, bd["x"] + bd["w"] / 2, bd["y"] - bd["d"] / 2, bd["y"] + bd["d"] / 2
    v.rect(bx0, bx1, by1 - 0.05, by1, "#cfc8bb", INK, 0.9)
    for k in range(2):
        v.rect(bx0 + 0.08 + k * 0.66, bx0 + 0.66 + k * 0.66, by1 - 0.45, by1 - 0.12, "#f3f0ea", MUTED, 0.8, rx=6)
    v.line((bx0, by1 - 0.62), (bx1, by1 - 0.62), MUTED, 0.8)
    # bookshelf
    v.poly(SHELF_FOOT, SET_FILL, INK, 1.1)
    bs = L["bookshelf"]
    for k in range(1, 4):
        yy = bs["y"] - bs["w"] / 2 + bs["w"] * k / 4
        v.line((-RX, yy), (-RX + bs["d"], yy), MUTED, 0.6)
    # frames (left wall), switch, panels
    fr = L["frames"]
    for i, y in enumerate(fr["y"]):
        v.rect(-RX, -RX + fr["t"] + 0.02, y - fr["w"] / 2, y + fr["w"] / 2, OBJ_FILL, OBJ_LINE, 1.4)
    sw = C.SWITCH
    v.rect(-RX, -RX + 0.04, sw["y"] - sw["w"] / 2, sw["y"] + sw["w"] / 2, OBJ_FILL, OBJ_LINE, 1.4)
    pg = L["panels_guitar"]
    v.rect(RX - pg["t"], RX, pg["y0"], pg["y1"], "#2b2c31", "#2b2c31", 0.5)
    pdk = L["panels_desk"]
    for x in pdk["x"]:
        v.rect(x - pdk["w"] / 2, x + pdk["w"] / 2, RY - pdk["t"], RY, "#2b2c31", "#2b2c31", 0.5)
    # desk and what stands on it
    v.poly(DESK_FOOT, SET_FILL, INK, 1.1)
    dk = L["desk"]
    for key in ("dj", "interface", "keyboard", "lightstick"):
        o = L[key]
        v.rect(o["x"] - o["w"] / 2, o["x"] + o["w"] / 2, o["y"] - o["d"] / 2, o["y"] + o["d"] / 2, OBJ_FILL,
               OBJ_LINE if key != "keyboard" else MUTED, 1.0)
    dj = L["dj"]
    for s_ in (-1, 1):
        v.circle(dj["x"] + s_ * 0.12, dj["y"] + 0.03, 0.065, "none", OBJ_LINE, 0.8)
    v.rect(MON["x"] - MON["w"] / 2, MON["x"] + MON["w"] / 2, MON["y"], MON["y"] + MON["t"], "#2a2c33", OBJ_LINE, 1.4)
    v.rect(MON["x"] - 0.11, MON["x"] + 0.11, MON["y"] - 0.02, MON["y"] + 0.14, "none", OBJ_LINE, 0.8, extra=DOT)
    for s_ in SPEAKERS:
        v.poly(foot(s_), OBJ_FILL, OBJ_LINE, 1.3)
    mc = L["mic"]
    v.path([mc["clamp"], mc["elbow"][:2], mc["capsule"][:2]], OBJ_LINE, 2.2)
    v.rect(mc["clamp"][0] - 0.03, mc["clamp"][0] + 0.03, mc["clamp"][1] - 0.03, mc["clamp"][1] + 0.02, OBJ_LINE, OBJ_LINE, 1)
    v.circle(*mc["capsule"][:2], 0.03, OBJ_FILL, OBJ_LINE, 1.4)
    # chair
    ch = L["chair"]
    v.circle(ch["x"], ch["y"], 0.33, "none", MUTED, 0.8, extra=DOT)
    v.poly([to_world(ch, x, y) for x, y in rect_local(-0.25, 0.25, -0.25, 0.22)], SET_FILL, INK, 1.0)
    v.poly([to_world(ch, x, y) for x, y in rect_local(-0.23, 0.23, 0.21, 0.27)], "#cfc8bb", INK, 1.0)
    # rack + guitars 04 to 06
    rk, gs, slots = rack_slots()
    v.poly(rack_foot(), "none", OBJ_LINE, 1.0, extra=DASH)
    bar_x = -0.08 + 0.70 * math.sin(math.radians(rk["lean"]))
    v.path([to_world(rk, bar_x, -rk["d"] / 2), to_world(rk, bar_x, rk["d"] / 2)], OBJ_LINE, 3)
    v.path([to_world(rk, -0.08, -rk["d"] / 2), to_world(rk, -0.08, rk["d"] / 2)], OBJ_LINE, 3)
    for g, sl in zip(gs, slots):
        lean = math.radians(rk["lean"])
        u0, u1 = -0.08 - g["width"] / 2, -0.08 + g["length"] * math.sin(lean) + 0.04
        v.poly([to_world(rk, x, y) for x, y in rect_local(u0, u1, sl - 0.025, sl + 0.025)], OBJ_FILL, OBJ_LINE, 1.2)
    # piano + bench + lid zone + player
    v.poly(PIANO_FOOT, "#2a2a2d", OBJ_LINE, 1.4)
    keys = [to_world(PIANO_O, x, y) for x, y in rect_local(-P["width"] / 2 + 0.06, P["width"] / 2 - 0.06,
                                                           P["key_back_y"] - P["white_len"], P["panel_face_y"])]
    v.poly(keys, "#f4efe2", OBJ_LINE, 0.9)
    lidz = [to_world(PIANO_O, x, y) for x, y in rect_local(-P["width"] / 2 - P["lid_over_side"], P["width"] / 2 + P["lid_over_side"],
                                                           -(P["side_depth"] + P["lid_over_front"]), P["lid_over_back"])]
    v.poly(lidz, "none", "#9fb5d6", 1.2, extra=DASH)
    v.poly(BENCH_PLAY, "none", OBJ_LINE, 0.9, extra=DASH)
    v.poly(BENCH_FOOT, OBJ_FILL, OBJ_LINE, 1.2)
    play = [to_world(PIANO_O, x, y) for x, y in rect_local(-B["w"] / 2, B["w"] / 2, B["cy"] - B["d"] / 2 - 0.40, B["cy"] - B["d"] / 2)]
    v.poly(play, "none", MUTED, 0.8, extra=DOT)
    # wall guitars (above, dashed)
    for i, y in enumerate(WG["y"]):
        v.rect(RX - WG["off_wall"] - 0.04, RX - WG["off_wall"] + 0.03, y - WG["width"][i] / 2, y + WG["width"][i] / 2, "none",
               OBJ_LINE, 1.2, extra=DASH)
    # plant on the sill
    pl = L["plant"]
    v.circle(pl["x"], pl["y"], pl["pot_d"] / 2, "#cfe0c8", OBJ_LINE, 1.3)
    # hero camera: fov wedge (16:9) and the phone wedge
    cam = Cam(HERO["pos"], HERO["target"], HERO["vfov"], 16 / 9)
    cx, cy = HERO["pos"][:2]
    def wall_hit(a):
        sx, sy = math.sin(a), math.cos(a)
        ts = []
        if sy > 1e-6:
            ts.append((RY - cy) / sy)
        if sx > 1e-6:
            ts.append((RX - cx) / sx)
        if sx < -1e-6:
            ts.append((-RX - cx) / sx)
        return min(ts)
    for sgn in (-1, 1):
        a = cam.yaw + sgn * math.radians(cam.hfov / 2)
        t = wall_hit(a)
        v.line((cx, cy), (cx + t * math.sin(a), cy + t * math.cos(a)), ACC, 1.3, extra='stroke-dasharray="10 5"')
    phone = Cam(HERO["pos"], (MON["x"], MON["y"], MON["z"]), HERO["phone_vfov"], 390 / 844)
    for sgn in (-1, 1):
        a = phone.yaw + sgn * math.radians(phone.hfov / 2)
        t = (MON["y"] - cy) / math.cos(a)
        v.line((cx, cy), (cx + t * math.sin(a), cy + t * math.cos(a)), "#7a8fb0", 1.0, extra=DOT)
    tx, ty = HERO["target"][:2]
    v.line((cx, cy), (tx, ty), ACC, 0.9, extra='stroke-dasharray="2 4"')
    v.circle(tx, ty, 0.025, ACC, ACC, 1)
    # camera glyph
    gx, gy = v.p(cx, cy)
    ang = -math.degrees(cam.yaw)
    add(f'<g transform="translate({gx:.1f} {gy:.1f}) rotate({ang:.1f})"><rect x="-13" y="-6" width="26" height="20" rx="3" '
        f'fill="{ACC}"/><polygon points="-8,-6 8,-6 13,-16 -13,-16" fill="{ACC}"/></g>')

    # labels -----------------------------------------------------------
    def lab(u, vv, s1, s2=None, anchor="middle", col=INK, size=14):
        x, y = v.p(u, vv)
        text(x, y, s1, size, col, anchor, weight=600)
        if s2:
            text(x, y + 16, s2, 12, MUTED, anchor)

    def lead(a, b, c, d, s1, an="start", size=13):
        leader(*v.p(a, b), *v.p(c, d), s1, an, size)
    lab(bd["x"], 0.80, "Bed", "set_bed · 145 × 200 · head on the back wall")
    lab(-RX + 0.15, bs["y"] + 0.02, "books", None, "middle", INK, 12)
    lab(0.10, -1.05, "Rug", "set_rug · 150 × 230", col=MUTED)
    lab(dk["x"] + 0.36, dk["y"] - 0.28, "Desk 145 × 75", None, "middle", INK, 13)
    lab(PIANO_O["x"] - 0.30, PIANO_O["y"] + 0.10, "Piano", None, "middle", "#fff", 14)
    text(*v.p(PIANO_O["x"] - 0.30, PIANO_O["y"] - 0.06), "153 × 61", 11, "#cfd6e2", "middle")
    xb, yb = v.p(min(p[0] for p in BENCH_FOOT) - 0.03, PIANO_O["y"] - 0.02)
    text(xb, yb, "bench at rest", 12, OBJ_LINE, "end")
    text(xb, yb + 15, "(dashed: played)", 11, MUTED, "end")
    xc_, yc_ = v.p(ch["x"], ch["y"] - 0.02)
    text(xc_, yc_ + 4, "chair", 12, INK, "middle")
    # top band
    top1, top2 = RY + R["wall_back_t"] + 0.50, RY + R["wall_back_t"] + 0.30
    lead((WIN["x0"] + WIN["x1"]) / 2 - 0.30, RY + 0.12, -1.05, top1, "window 120 wide, sill 105, head 210 (obj_window)", "end")
    lead(pl["x"], pl["y"], -0.80, top2, "plant on the stone sill (obj_plant)", "end")
    lead(MON["x"], MON["y"] + 0.02, 0.10, top1, "monitor 62 wide, faces straight out (obj_monitor)", "middle")
    lead(SPEAKERS[1]["x"], SPEAKERS[1]["y"] + 0.05, 0.62, top2, f"studio monitors on pads, toed in {SPEAKERS[0]['toe']:.0f}°", "start")
    lead(rk["x"] + 0.05, rk["y"] + 0.20, 1.20, top1, "rack, guitars 04 to 06 (option A)", "start")
    # left wall
    lead(-RX + 0.03, fr["y"][1], -1.90, 1.38, "frames 01 to 03 on the wall (obj_frames)", "start", 12)
    lead(-RX + 0.03, sw["y"], -1.80, -1.05, "switch board, 120 high (obj_light)", "start", 12)
    lead(-RX + 0.45, DOOR["y0"] + 0.30, -1.10, -1.55, "door 90 × 210", "start", 12)
    # right wall
    lead(RX - WG["off_wall"], WG["y"][2] - 0.05, 1.35, -0.30, "wall guitars 01 to 03, above the piano", "end", 12)
    lead(RX - 0.02, pg["y0"] + 0.04, 1.35, -0.50, "acoustic panel behind them", "end", 12)
    lead(lt["x"] + 0.15, lt["y"] - 0.12, 0.55, 0.22, "ceiling light, a pendant (obj_light)", "start", 12)
    xk, yk = v.p(lidz[2][0], lidz[2][1])
    leader(xk, yk, xk + 26, yk - 24, "lid", "start", 12, "#6d84a8")
    # key for the desk
    kx0, kx1, ky0, ky1 = 1.02, RX - 0.08, -1.68, -0.72
    v.rect(kx0, kx1, ky0, ky1, "#fffdf8", RULE, 1)
    keys_ = [("a", dj["x"], dj["y"], "DJ controller 44 × 28"), ("b", L["interface"]["x"], L["interface"]["y"], "audio interface 18 × 12"),
             ("c", L["lightstick"]["x"] - 0.06, L["lightstick"]["y"], "lightstick, lying down"),
             ("d", mc["capsule"][0], mc["capsule"][1], "mic on its arm (obj_mic)"),
             ("e", L["keyboard"]["x"], L["keyboard"]["y"], "keyboard")]
    xk0, yk0 = v.p(kx0, ky1)
    text(xk0 + 14, yk0 + 26, "On the desk (obj_studio)", 13, INK, weight=650)
    for i, (k, x_, y_, lbl) in enumerate(keys_):
        px_, py_ = v.p(x_, y_)
        add(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="8" fill="#fff" stroke="{OBJ_LINE}" stroke-width="1.2"/>')
        text(px_, py_ + 4, k, 11, OBJ_LINE, "middle", weight=700)
        yy_ = yk0 + 50 + i * 23
        add(f'<circle cx="{xk0 + 24:.1f}" cy="{yy_ - 4:.1f}" r="8" fill="#fff" stroke="{OBJ_LINE}" stroke-width="1.2"/>')
        text(xk0 + 24, yy_, k, 11, OBJ_LINE, "middle", weight=700)
        text(xk0 + 40, yy_, lbl, 13, INK)
    # camera
    xc, yc = v.p(cx, cy)
    text(xc + 22, yc - 18, f"hero camera, eye at {cm(HERO['pos'][2], 0)}, {cm(cx + RX, 0)} from the left wall, {cm(cy + RY, 0)} off the front", 13, ACC, weight=600)
    text(xc + 22, yc - 2, f"{cam.vfov:.0f}° vertical, {cam.hfov:.0f}° across on 16:9 · dotted: phone", 12, ACC)
    # east arrow
    ex, ey = v.p(RX + 0.52, RY + 0.58)
    add(f'<g stroke="{MUTED}" fill="{MUTED}"><line x1="{ex:.1f}" y1="{ey + 22:.1f}" x2="{ex:.1f}" y2="{ey - 10:.1f}" stroke-width="1.4"/>'
        f'<polygon points="{ex - 6:.1f},{ey - 6:.1f} {ex + 6:.1f},{ey - 6:.1f} {ex:.1f},{ey - 18:.1f}"/></g>')
    text(ex, ey - 24, "east", 12, MUTED, "middle")

    # dimensions ---------------------------------------------------------
    x0, y0 = v.p(-RX, -RY)
    x1, y1 = v.p(RX, RY)
    dim(x0, y0, v.p(RX, -RY)[0], y0, cm(R["width"], 0) + " inside", off=62, side=-1)
    dim(v.p(RX, -RY)[0], y0, v.p(RX, RY)[0], y1, cm(R["depth"], 0) + " inside", off=96, side=-1)
    ya = v.p(0, RY + R["wall_back_t"])[1]
    chain = [-RX, WIN["x0"], WIN["x1"], dk["x"] - dk["w"] / 2, dk["x"] + dk["w"] / 2, RX - 0.05 + P["toe_front_y"], RX]
    for a_, b_ in zip(chain, chain[1:]):
        dim(v.p(a_, 0)[0], ya, v.p(b_, 0)[0], ya, cm(b_ - a_, 0) if b_ - a_ > 0.12 else "", off=-16, size=12)
    xr = v.p(RX, 0)[0]
    py0 = min(p[1] for p in PIANO_FOOT)
    py1 = max(p[1] for p in PIANO_FOOT)
    dim(xr, v.p(0, RY)[1], xr, v.p(0, py1)[1], cm(RY - py1, 0), off=56, side=-1, size=12)
    dim(xr, v.p(0, py1)[1], xr, v.p(0, py0)[1], cm(py1 - py0, 0) + " piano", off=56, side=-1, size=12)
    dim(xr, v.p(0, py0)[1], xr, v.p(0, -RY)[1], cm(py0 + RY, 0), off=56, side=-1, size=12)
    yy = v.p(0, 0.12)[1]
    dim(v.p(bx1, 0)[0], yy, v.p(min(p[0] for p in PIANO_FOOT), 0)[0], yy,
        cm(min(p[0] for p in PIANO_FOOT) - bx1, 0) + " free floor, bed to piano", off=0, size=12)
    bench_x0 = min(p[0] for p in BENCH_FOOT)
    yb2 = v.p(0, min(p[1] for p in BENCH_FOOT) - 0.06)[1]
    dim(v.p(bench_x0, 0)[0], yb2, xr, yb2, cm(RX - bench_x0, 0), off=0, size=12)
    return v, cam


# ---------------------------------------------------------------------------
# 2. walls unfolded
# ---------------------------------------------------------------------------
def wall_frame(v, length, title, sub):
    v.rect(0, length, 0, H, "#fbfaf6", INK, 1.2)
    v.rect(0, length, 0, R["skirting_h"], "#efebe4", MUTED, 0.6)
    x, y = v.p(0, H)
    text(x, y - 12, title, 16, INK, weight=650)
    text(x + 8 + len(title) * 8.6, y - 12, sub, 13, MUTED)


def elevations(px, py, pw, ph, lid90, lid55):
    panel(px, py, pw, ph, "2 · The walls, unfolded",
          "seen from inside the room · left, back, right, then the front · solid: on or against the wall · dashed: standing out in the room")
    s = 146
    gap_m = 0.22
    base_y = py + 118 + H * s
    x = px + 40
    # ----- left wall: u = y + RY (front corner at the left) -----
    vl = View(x, base_y, s)
    wall_frame(vl, R["depth"], "Left wall", "bed, books, frames, door, switch")
    U = lambda y: y + RY  # noqa: E731
    vl.rect(U(DOOR["y0"]), U(DOOR["y1"]), 0, DOOR["head"], "#f1ede5", INK, 1.1)
    vl.line((U(DOOR["y0"]) + 0.02, 0), (U(DOOR["y0"]) + 0.02, DOOR["head"]), MUTED, 0.8)
    vl.path([(U(DOOR["y1"]), 0), (U(DOOR["y0"]) + 0.02, DOOR["head"] / 2), (U(DOOR["y1"]), DOOR["head"])], MUTED, 0.7, extra=DASH)
    sw = C.SWITCH
    vl.rect(U(sw["y"]) - sw["w"] / 2, U(sw["y"]) + sw["w"] / 2, sw["z"] - sw["h"] / 2, sw["z"] + sw["h"] / 2, OBJ_FILL, OBJ_LINE, 1.3)
    bs = L["bookshelf"]
    y0b, y1b = bs["y"] - bs["w"] / 2, bs["y"] + bs["w"] / 2
    vl.rect(U(y0b), U(y1b), 0, bs["h"], SET_FILL, INK, 1.1)
    for k in range(1, 5):
        vl.line((U(y0b), bs["h"] * k / 5), (U(y1b), bs["h"] * k / 5), MUTED, 0.7)
    bd = L["bed"]
    by0, by1 = bd["y"] - bd["d"] / 2, bd["y"] + bd["d"] / 2
    vl.rect(U(by0), U(by1), 0.05, 0.32, "#cfc8bb", INK, 1)
    vl.rect(U(by0) + 0.02, U(by1) - 0.05, 0.32, bd["h"], SET_FILL, INK, 1)
    vl.rect(U(by1) - 0.05, U(by1), 0, bd["head_h"], "#cfc8bb", INK, 1)
    fr = L["frames"]
    for i, y in enumerate(fr["y"]):
        vl.rect(U(y) - fr["w"] / 2, U(y) + fr["w"] / 2, fr["z"] - fr["h"] / 2, fr["z"] + fr["h"] / 2, OBJ_FILL, OBJ_LINE, 1.4)
        vl.rect(U(y) - fr["w"] / 2 + 0.035, U(y) + fr["w"] / 2 - 0.035, fr["z"] - fr["h"] / 2 + 0.04, fr["z"] + fr["h"] / 2 - 0.04,
                "#fff", OBJ_LINE, 0.7)
        xf, yf = vl.p(U(y), fr["z"])
        text(xf, yf + 4, f"0{i + 1}", 12, OBJ_LINE, "middle", weight=600)
    lt = C.LIGHT
    zb = H - lt["drop"] - lt["shade_h"]
    vl.line((U(lt["y"]), H), (U(lt["y"]), zb + lt["shade_h"]), MUTED, 0.8, extra=DASH)
    vl.rect(U(lt["y"]) - lt["shade_d"] / 2, U(lt["y"]) + lt["shade_d"] / 2, zb, zb + lt["shade_h"], "none", OBJ_LINE, 1, extra=DASH)
    # dims (left wall)
    xa = vl.p(U(fr["y"][0]) - fr["w"] / 2 - 0.10, 0)[0]
    dim(xa, vl.p(0, 0)[1], xa, vl.p(0, fr["z"] - fr["h"] / 2)[1], cm(fr["z"] - fr["h"] / 2, 0), off=0, size=12)
    xa2 = vl.p(U(fr["y"][2]) + fr["w"] / 2 + 0.10, 0)[0]
    dim(xa2, vl.p(0, 0)[1], xa2, vl.p(0, fr["z"] + fr["h"] / 2)[1], cm(fr["z"] + fr["h"] / 2, 0), off=0, side=-1, size=12)
    xd = vl.p(U(DOOR["y0"]) - 0.06, 0)[0]
    dim(xd, vl.p(0, 0)[1], xd, vl.p(0, DOOR["head"])[1], cm(DOOR["head"], 0), off=0, size=12)
    xs = vl.p(U(sw["y"]) + 0.16, 0)[0]
    dim(xs, vl.p(0, 0)[1], xs, vl.p(0, sw["z"])[1], cm(sw["z"], 0), off=0, side=-1, size=12)
    xb = vl.p(U(y1b) + 0.06, 0)[0]
    dim(xb, vl.p(0, 0)[1], xb, vl.p(0, bs["h"])[1], cm(bs["h"], 0), off=0, side=-1, size=12)
    xh = vl.p(U(by1) - 0.12, 0)[0]
    dim(xh, vl.p(0, 0)[1], xh, vl.p(0, bd["head_h"])[1], cm(bd["head_h"], 0), off=0, size=12)
    xcl = vl.p(R["depth"] - 0.08, 0)[0]
    dim(xcl, vl.p(0, 0)[1], xcl, vl.p(0, H)[1], cm(H, 0), off=0, side=-1, size=12)
    # ----- back wall: u = x + RX -----
    x2 = x + (R["depth"] + gap_m) * s
    vb = View(x2, base_y, s)
    wall_frame(vb, R["width"], "Back wall", "window over the bed, the desk, the rack")
    U = lambda xx: xx + RX  # noqa: E731
    vb.rect(U(-RX), U(L["bed"]["x"] + L["bed"]["w"] / 2), 0.05, 0.32, "#cfc8bb", INK, 1)
    vb.rect(U(-RX), U(L["bed"]["x"] + L["bed"]["w"] / 2), 0, L["bed"]["head_h"], "#cfc8bb", INK, 1)
    vb.rect(U(WIN["x0"]), U(WIN["x1"]), WIN["sill"], WIN["head"], "#cdd9ef", INK, 1.3)
    xm = (WIN["x0"] + WIN["x1"]) / 2
    vb.line((U(xm), WIN["sill"]), (U(xm), WIN["head"]), INK, 1.0)
    for k in range(1, 9):
        z = WIN["sill"] + (WIN["head"] - WIN["sill"]) * k / 9
        vb.line((U(WIN["x0"]), z), (U(WIN["x1"]), z), "#9aa6bb", 0.6)
    vb.rect(U(WIN["x0"] - 0.04), U(WIN["x1"] + 0.04), WIN["sill"] - WIN["ledge_t"], WIN["sill"], "#d2ccc0", INK, 0.9)
    pl = L["plant"]
    vb.rect(U(pl["x"]) - pl["pot_d"] / 2, U(pl["x"]) + pl["pot_d"] / 2, WIN["sill"], WIN["sill"] + 0.13, "#e9c7b8", OBJ_LINE, 1.2)
    vb.circle(U(pl["x"]), WIN["sill"] + 0.25, 0.10, "#cfe0c8", OBJ_LINE, 1.2)
    pdk = L["panels_desk"]
    for xx in pdk["x"]:
        vb.rect(U(xx - pdk["w"] / 2), U(xx + pdk["w"] / 2), pdk["z0"], pdk["z1"], "#3a3b41", "#2b2c31", 0.8)
    dk = L["desk"]
    dx0, dx1 = dk["x"] - dk["w"] / 2, dk["x"] + dk["w"] / 2
    vb.rect(U(dx0), U(dx1), dk["h"] - dk["top_t"], dk["h"], SET_FILL, INK, 1.1)
    for xx in (dx0 + 0.04, dx1 - 0.04):
        vb.rect(U(xx) - 0.025, U(xx) + 0.025, 0, dk["h"] - dk["top_t"], SET_FILL, INK, 0.9)
    for s_ in SPEAKERS:
        vb.rect(U(s_["x"]) - 0.10, U(s_["x"]) + 0.10, dk["h"], dk["h"] + SPK["pad_h"], "#bdb8ae", INK, 0.8)
        vb.rect(U(s_["x"]) - SPK["w"] / 2, U(s_["x"]) + SPK["w"] / 2, dk["h"] + SPK["pad_h"], dk["h"] + SPK["pad_h"] + SPK["h"],
                OBJ_FILL, OBJ_LINE, 1.3)
        vb.circle(U(s_["x"]), dk["h"] + SPK["pad_h"] + 0.09, 0.05, "none", OBJ_LINE, 0.9)
    mz0, mz1 = MON["z"] - MON["h"] / 2, MON["z"] + MON["h"] / 2
    vb.rect(U(MON["x"]) - 0.025, U(MON["x"]) + 0.025, dk["h"], mz0, "#2a2c33", INK, 0.8)
    vb.rect(U(MON["x"]) - 0.11, U(MON["x"]) + 0.11, dk["h"], dk["h"] + 0.012, "#2a2c33", INK, 0.8)
    vb.rect(U(MON["x"] - MON["w"] / 2), U(MON["x"] + MON["w"] / 2), mz0, mz1, "#2a2c33", OBJ_LINE, 1.4)
    vb.rect(U(MON["x"]) - 0.28, U(MON["x"]) + 0.28, MON["z"] - 0.175, MON["z"] + 0.175, "#3f7fc4", "none", 0)
    for key in ("dj", "interface"):
        o = L[key]
        vb.rect(U(o["x"] - o["w"] / 2), U(o["x"] + o["w"] / 2), dk["h"], dk["h"] + o["h"], OBJ_FILL, OBJ_LINE, 1.0)
    mc = L["mic"]
    vb.path([(U(mc["clamp"][0]), dk["h"]), (U(mc["clamp"][0]), dk["h"] + 0.08), (U(mc["elbow"][0]), mc["elbow"][2]),
             (U(mc["capsule"][0]), mc["capsule"][2])], OBJ_LINE, 2.2)
    vb.rect(U(mc["capsule"][0]) - 0.03, U(mc["capsule"][0]) + 0.03, mc["capsule"][2] - 0.07, mc["capsule"][2] + 0.06, OBJ_FILL, OBJ_LINE, 1.2)
    # rack silhouettes, projected on the back wall plane
    rk, gs, slots = rack_slots()
    lean = math.radians(rk["lean"])
    for g, sl in zip(gs, slots):
        body, neck, head = guitar_outline(g["length"], g["width"])
        for part in (neck, head, body):
            pts = []
            for u, vv in part:
                lu = -0.08 + u * math.cos(lean) + vv * math.sin(lean)
                lv = rk["cradle"] - u * math.sin(lean) + vv * math.cos(lean)
                wx, _ = to_world(rk, lu, sl)
                pts.append((U(wx), lv))
            vb.poly(pts, OBJ_FILL, OBJ_LINE, 0.9, extra='fill-opacity=".85"')
    # piano treble side, standing out in the room (dashed), and the ceiling light
    pxs = [p[0] for p in PIANO_FOOT]
    vb.rect(U(min(pxs)), U(max(pxs)), 0, P["case_top"] + P["lid_t"], "none", MUTED, 0.9, extra=DASH)
    xpt, ypt = vb.p(U((min(pxs) + max(pxs)) / 2), 0.55)
    text(xpt, ypt, "piano side", 11, MUTED, "middle")
    vb.line((U(lt["x"]), H), (U(lt["x"]), zb + lt["shade_h"]), MUTED, 0.8, extra=DASH)
    vb.rect(U(lt["x"]) - lt["shade_d"] / 2, U(lt["x"]) + lt["shade_d"] / 2, zb, zb + lt["shade_h"], "none", OBJ_LINE, 1, extra=DASH)
    # dims (back wall)
    xw = vb.p(U(WIN["x0"]) - 0.07, 0)[0]
    dim(xw, vb.p(0, 0)[1], xw, vb.p(0, WIN["sill"])[1], cm(WIN["sill"], 0), off=0, size=12)
    dim(xw, vb.p(0, WIN["sill"])[1], xw, vb.p(0, WIN["head"])[1], cm(WIN["head"] - WIN["sill"], 0), off=0, size=12)
    xdk = vb.p(U(dx0) + 0.10, 0)[0]
    dim(xdk, vb.p(0, 0)[1], xdk, vb.p(0, dk["h"])[1], cm(dk["h"], 0), off=0, side=-1, size=12)
    xmn = vb.p(U(MON["x"] + MON["w"] / 2) + 0.05, 0)[0]
    dim(xmn, vb.p(0, 0)[1], xmn, vb.p(0, MON["z"])[1], f"screen centre {cm(MON['z'], 1)}", off=0, side=-1, size=11)
    xpn = vb.p(U(pdk["x"][0] - pdk["w"] / 2) - 0.05, 0)[0]
    dim(xpn, vb.p(0, pdk["z0"])[1], xpn, vb.p(0, pdk["z1"])[1], f"{cm(pdk['z0'], 0)} to {cm(pdk['z1'], 0)}", off=0, size=11)
    # ----- right wall: u = RY - y (back corner at the left) -----
    x3 = x2 + (R["width"] + gap_m) * s
    vr = View(x3, base_y, s)
    wall_frame(vr, R["depth"], "Right wall", "piano, guitar wall, panel")
    U = lambda y: RY - y  # noqa: E731
    pg = L["panels_guitar"]
    vr.rect(U(pg["y1"]), U(pg["y0"]), pg["z0"], pg["z1"], "#3a3b41", "#2b2c31", 0.8)
    for k in range(1, 18):
        uu = U(pg["y1"]) + (pg["y1"] - pg["y0"]) * k / 18
        vr.line((uu, pg["z0"]), (uu, pg["z1"]), "#55565d", 0.7)
    # the piano's front, from the piano design sheet (reused, same numbers)
    pv = PDS.View(vr.ox + U(PIANO_O["y"]) * s, base_y, s / 1000)
    PDS.front(pv, dict(PDS.TECH, sw=0.7), detail=False)
    # lid envelope
    hw = P["width"] / 2 + P["lid_over_side"]
    vr.rect(U(PIANO_O["y"]) - hw, U(PIANO_O["y"]) + hw, P["case_top"] + P["lid_t"], lid90, "#dfe8f3", "#7f9cc4", 1.0,
            extra=DASH + ' fill-opacity=".6"')
    xl, yl = vr.p(U(PIANO_O["y"]), (P["case_top"] + lid90) / 2 + 0.07)
    text(xl, yl + 10, "the top lid swings up in here (seen from the front)", 11, "#46628a", "middle")
    # wall guitars on hooks
    cols = ["#e9c49a", "#f8f6f0", "#d9b08a"]
    for i, y in enumerate(WG["y"]):
        body, neck, head = guitar_outline(WG["length"][i], WG["width"][i], archtop=(i == 0))
        for part, col in ((neck, "#c9b59c"), (head, "#8c7a66"), (body, cols[i])):
            vr.poly([(U(y) + u, WG["bottom"] + vv) for u, vv in part], col, OBJ_LINE, 1.0)
        hz = WG["bottom"] + WG["length"][i] - WG["hook_from_top"][i]
        vr.rect(U(y) - 0.03, U(y) + 0.03, hz - 0.05, hz, "#9a9a9a", INK, 0.8)
        xg, yg = vr.p(U(y), WG["bottom"] + 0.20)
        text(xg, yg, f"0{i + 1}", 13, OBJ_LINE, "middle", weight=700)
    # bench, rack, desk end standing out in the room (dashed)
    bys = [p[1] for p in BENCH_FOOT]
    vr.rect(U(max(bys)), U(min(bys)), 0, B["h"], "none", MUTED, 0.9, extra=DASH)
    rfy = [p[1] for p in rack_foot()]
    vr.rect(U(max(rfy)), U(min(rfy)), 0, 1.07, "none", MUTED, 0.9, extra=DASH)
    xrk, yrk = vr.p(U((max(rfy) + min(rfy)) / 2), 1.12)
    text(xrk, yrk, "rack", 11, MUTED, "middle")
    vr.line((U(lt["y"]), H), (U(lt["y"]), zb + lt["shade_h"]), MUTED, 0.8, extra=DASH)
    vr.rect(U(lt["y"]) - lt["shade_d"] / 2, U(lt["y"]) + lt["shade_d"] / 2, zb, zb + lt["shade_h"], "none", OBJ_LINE, 1, extra=DASH)
    # dims (right wall)
    xg0 = vr.p(U(WG["y"][2]) + WG["width"][2] / 2 + 0.08, 0)[0]
    dim(xg0, vr.p(0, 0)[1], xg0, vr.p(0, lid90)[1], cm(lid90, 1), off=0, side=-1, size=12)
    dim(xg0, vr.p(0, lid90)[1], xg0, vr.p(0, WG["bottom"])[1], cm(WG["bottom"] - lid90, 1), off=0, side=-1, size=12)
    xg1 = vr.p(0.14, 0)[0]
    dim(xg1, vr.p(0, 0)[1], xg1, vr.p(0, WG["bottom"])[1], cm(WG["bottom"], 0), off=0, size=12)
    top0 = WG["bottom"] + WG["length"][0]
    dim(xg1, vr.p(0, WG["bottom"])[1], xg1, vr.p(0, top0)[1], cm(WG["length"][0], 0), off=0, size=12)
    dim(xg1, vr.p(0, top0)[1], xg1, vr.p(0, H)[1], cm(H - top0, 0), off=0, size=12)
    xpp = vr.p(U(PIANO_O["y"]) + P["width"] / 2 + 0.06, 0)[0]
    dim(xpp, vr.p(0, 0)[1], xpp, vr.p(0, P["case_top"] + P["lid_t"])[1], cm(P["case_top"] + P["lid_t"], 1), off=0, side=-1, size=12)
    xpg = vr.p(U(pg["y0"]) + 0.05, 0)[0]
    dim(xpg, vr.p(0, pg["z0"])[1], xpg, vr.p(0, pg["z1"])[1], f"{cm(pg['z0'], 0)} to {cm(pg['z1'], 0)}", off=0, side=-1, size=11)
    # ----- section at the piano: lid vs guitar -----
    x4 = x3 + (R["depth"] + gap_m + 0.20) * s
    s4 = s
    vs = View(x4 + 1.20 * s4, base_y, s4)      # u = distance into the room, wall on the right
    xa, ya = vs.p(-1.20, H)
    text(xa, ya - 12, "Section at the piano", 16, INK, weight=650)
    text(xa, ya + 18, "lid fully open vs the lowest guitar", 12, MUTED)
    vs.rect(0, R["wall_side_t"], 0, H, WALL_POCHE, WALL_POCHE, 0.5)
    vs.line((-1.20, 0), (R["wall_side_t"], 0), INK, 1.4)
    vs.line((-1.20, H), (R["wall_side_t"], H), INK, 1.4)
    pb = -0.05                                   # piano back, 5 cm off the wall
    # piano side: case outline from the shared layout (y local -> u = pb + y)
    sd = P["side_depth"]
    vs.poly([(pb - sd, P["floor_gap"]), (pb, P["floor_gap"]), (pb, P["case_top"]), (pb - sd, P["case_top"])], "#2a2a2d", INK, 0.9)
    vs.poly([(pb + y, z) for y, z in cheek_profile()], "#2a2a2d", INK, 0.9)
    vs.poly([(pb + y, z) for y, z in console_profile()], "#2a2a2d", INK, 0.9)
    vs.poly([(pb + y, z) for y, z in lid_profile(0)[0]], "#2a2a2d", INK, 0.9)
    vs.poly([(pb + y, z) for y, z in lid_profile(P["lid_open_deg"])[0]], "none", "#7f9cc4", 1.1)
    vs.poly([(pb + y, z) for y, z in lid_profile(90)[0]], "#dfe8f3", "#7f9cc4", 1.1, extra=DASH)
    # guitar in side view: body depth, hanging from the hook arm
    gb = WG["bottom"]
    g_front = -WG["off_wall"] - 0.04
    vs.rect(g_front, g_front + 0.08, gb, gb + 0.46, OBJ_FILL, OBJ_LINE, 1.2)
    vs.rect(g_front + 0.02, g_front + 0.05, gb + 0.46, gb + WG["length"][0], OBJ_FILL, OBJ_LINE, 1.0)
    hz = gb + WG["length"][0] - WG["hook_from_top"][0]
    vs.path([(0, hz - 0.04), (-WG["off_wall"] + 0.01, hz - 0.01), (-WG["off_wall"] + 0.01, hz + 0.02)], INK, 2)
    xq = vs.p(-0.70, 0)[0]
    dim(xq, vs.p(0, 0)[1], xq, vs.p(0, lid90)[1], cm(lid90, 1), off=0, size=12)
    dim(xq, vs.p(0, lid90)[1], xq, vs.p(0, gb)[1], cm(gb - lid90, 1), off=0, size=12)
    xx1, yy1 = vs.p(-0.62, lid90 - 0.30)
    text(xx1 - 18, yy1, "", 11, MUTED, "end")
    xl1, yl1 = vs.p(pb - 0.27, P["case_top"] + 0.30)
    text(xl1 - 4, yl1, f"lid at {P['lid_open_deg']}° (stills)", 11, "#46628a", "end")
    xl2, yl2 = vs.p(pb - 0.05, lid90 + 0.06)
    text(xl2 - 6, yl2, "at 90°", 11, "#46628a", "end")
    xl3, yl3 = vs.p(g_front, gb + 0.60)
    text(xl3 - 6, yl3, "guitar 01", 11, OBJ_LINE, "end")
    text(xl3 - 6, yl3 + 14, "(the longest)", 11, OBJ_LINE, "end")
    return base_y


# ---------------------------------------------------------------------------
# 3. front wall, rack options, the shell build
# ---------------------------------------------------------------------------
def front_wall(px, py, pw, ph):
    panel(px, py, pw, ph, "Front wall", "bake only (bake_wall_front): not in the GLB")
    s = 118
    base_y = py + ph - 46
    v = View(px + 36, base_y, s)
    v.rect(0, R["width"], 0, H, "#fbfaf6", INK, 1.2)
    v.rect(0, R["width"], 0, R["skirting_h"], "#efebe4", MUTED, 0.6)
    U = lambda xx: RX - xx  # noqa: E731
    cx, cy, cz = HERO["pos"]
    v.circle(U(cx), cz, 0.06, ACC, ACC, 1)
    xc, yc = v.p(U(cx), cz)
    text(xc, yc - 14, f"hero camera, {cm(cy + RY, 0)} in front", 12, ACC, "middle")
    v.rect(U(-RX), U(-RX + 0.15), 0, DOOR["head"], "none", MUTED, 0.8, extra=DASH)
    xd, yd = v.p(U(-RX + 0.10), DOOR["head"] + 0.08)
    text(xd, yd, "door leaf rests here", 11, MUTED, "end")
    para(px + 36, py + 90, [("Plain wall. The camera's side of the room.", MUTED)], 13)


RACK_B = dict(L["rack"], x=-0.40, y=0.36, yaw=-20)   # the only free spot left of the desk: out in the room


def rack_options(px, py, pw, ph, cam):
    panel(px, py, pw, ph, "3 · Where the guitar rack stands", "the open question, seen from the hero camera")
    w = (pw - 60) / 2
    h = w * 9 / 16
    for k, (rk, title, col) in enumerate(((None, "A · by the right studio monitor (recommended)", INK),
                                          (RACK_B, "B · by the left studio monitor", MUTED))):
        x0 = px + 20 + k * (w + 20)
        y0 = py + 100
        text(x0, y0 - 12, title, 15, col, weight=650)
        build_scene(rack=rk).render(cam, x0, y0, w, h, label_marks=False)
        add(f'<rect x="{x0}" y="{y0}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="{INK}" stroke-width="1"/>')
    para(px + 20, py + 100 + h + 34, [
        ("A: all six guitars in one corner, the eye runs from the wall down into the rack. It fills the 75 cm between", INK),
        (f"the desk and the piano's toe blocks ({gap(DESK_FOOT, rack_foot()) * 100:.0f} and {gap(rack_foot(), PIANO_FOOT) * 100:.0f} cm clear) "
         "and keeps the window, the plant and the DJ controller clear.", INK),
        ("B: left of the desk is the bed's head, so no wall is free. The rack would stand out on the rug in front of the", MUTED),
        ("bed, cut off from the desk, in the way to the window, and the timeline would split across the room.", MUTED),
    ], 14)


def owner_panel(px, py, pw, ph):
    panel(px, py, pw, ph, "For the owner", "what this sheet asks you to decide")
    para(px + 22, py + 94, [
        ("1. The room: 440 × 420 cm, 300 cm ceiling, window over the bed's head, door on the left wall by the front corner.", INK),
        ("2. The rack: A, between the desk and the piano (recommended), or B.", INK),
        ("3. The hero camera: just inside the front wall by the door, eye at 160 cm, 50° vertical (about 22 mm). The site would", INK),
        ("    open on this view instead of today's straight-on monitor close-up; the monitor stays in the middle and a click still glides in.", INK),
        ("4. Changes to the object list's details, all small: the nightstand is cut (no wall for it); the ceiling light becomes a", INK),
        (f"    pendant over the free floor, {C.LIGHT['y'] * 100:.0f} cm behind the room's centre, bottom at "
         f"{(H - C.LIGHT['drop'] - C.LIGHT['shade_h']) * 100:.0f} cm, so it shows in the hero; the light switch sits on the", INK),
        ("    left wall by the door (out of the hero frame, the shade is the click target); the bench rests pushed in 22 cm.", INK),
        ("5. Wall guitars: bottoms in one line at 172 cm, 8.3 cm above the lid opened fully; the code may open the lid up to 90°.", INK),
    ], 14.5, lh=23)


def shell_list(px, py, pw, ph):
    panel(px, py, pw, ph, "4 · What the shell build makes next", "Step 1 of the Phase 4 brief, from these numbers")
    y = para(px + 22, py + 92, [
        ("Built in full:", INK, 650),
        "· set_room: floor (oak), three walls, ceiling, skirting 10 cm,",
        "  the window opening 120 × 105 in the back wall with its",
        "  stone ledge, the door opening in the left wall",
        "· bake_wall_front and bake_door (bake only, never exported)",
        "· set_desk: top, legs, keyboard, mouse",
        "· obj_monitor: monitor_body, monitor_screen 16:10 with the",
        "  TOP test texture, monitor_static",
        "· room_view and room_view_target at the hero camera",
        "",
        ("As footprint boxes only, named, to scale:", INK, 650),
        "bed, bookshelf, rug, chair, rack, piano and bench, the three",
        "wall guitars, frames, panels, speakers, DJ controller,",
        "interface, lightstick, mic, plant, ceiling light, switch.",
        "",
        ("Then:", INK, 650),
        "the GLB behind /?room&glb, TOP upright, stills from the",
        "hero camera (clay, wireframe, blue hour).",
    ], 14, lh=21)


def hero_panel(px, py, pw, ph, cam):
    panel(px, py, pw, ph, "5 · The hero camera: what the site opens on",
          "flat-shaded sketch from the plan's numbers, for composition only · numbers mark the nine objects")
    S = build_scene()
    sw_ = pw - 40
    sh_ = sw_ * 9 / 16
    x0, y0 = px + 20, py + 78
    placed = S.render(cam, x0, y0, sw_, sh_)
    add(f'<rect x="{x0}" y="{y0}" width="{sw_}" height="{sh_:.1f}" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    text(x0 + 10, y0 + sh_ - 12, "desktop, 16:9", 13, "#ffffff", weight=600)
    # phone
    ph_w = 236
    ph_h = ph_w * 844 / 390
    phx, phy = px + 20, y0 + sh_ + 26
    phone = Cam(HERO["pos"], (MON["x"], MON["y"], MON["z"]), HERO["phone_vfov"], 390 / 844)
    S.render(phone, phx, phy, ph_w, ph_h, label_marks=False)
    add(f'<rect x="{phx}" y="{phy}" width="{ph_w}" height="{ph_h:.1f}" rx="18" fill="none" stroke="{INK}" stroke-width="3"/>')
    text(phx + ph_w / 2, phy + ph_h + 20, "phone, 390 × 844", 13, MUTED, "middle")
    # numbers and the list
    vis = visibility(cam)
    tx = phx + ph_w + 34
    ty = phy + 8
    cx, cy, cz = HERO["pos"]
    tgt = HERO["target"]
    ty = para(tx, ty + 14, [
        ("room_view (also still_cam_home)", INK, 650),
        f"position x {cm(cx, 0)}, y {cm(cy, 0)}, eye height {cm(cz, 0)}:",
        f"just inside the front wall, left of the monitor, as in the photo",
        f"looks at room_view_target x {cm(tgt[0], 0)}, y {cm(tgt[1], 0)}, z {cm(tgt[2], 0)}",
        f"turned {math.degrees(cam.yaw):.0f}° right of straight, {abs(math.degrees(cam.pitch)):.0f}° down",
        f"field of view {cam.vfov:.0f}° vertical, {cam.hfov:.0f}° across on 16:9",
        f"(about a 22 mm lens on full frame)",
        "",
        ("still_cam_phone", INK, 650),
        f"same place, aimed at the monitor, {HERO['phone_vfov']}° vertical",
        "",
        ("In the 16:9 frame (share of each object)", INK, 650),
    ], 14, lh=20.5)
    keys = ["piano", "guitars", "monitor", "mic", "frames", "studio", "light", "window", "plant"]
    for (num, name, root), k in zip(NINE, keys):
        v_ = vis[k]
        col = INK if v_ >= 0.9 else (ACC if v_ >= 0.5 else "#a33")
        add(f'<circle cx="{tx + 9}" cy="{ty - 5}" r="9" fill="{OBJ_LINE}"/>')
        text(tx + 9, ty - 1, str(num), 11, "#fff", "middle", weight=700)
        text(tx + 26, ty, f"{name}", 13.5, INK)
        text(tx + pw - 300, ty, f"{v_ * 100:.0f} %", 13.5, col, "end", weight=600)
        ty += 20.5
    ty += 6
    mw = 2 * math.degrees(math.atan((MON["w"] / 2) / math.dist(HERO["pos"][:2], (MON["x"], MON["y"]))))
    mx_, my_ = cam.ndc(cam.cam((MON["x"], MON["y"], MON["z"])))
    where = "in the middle" if abs(mx_) < 0.06 else ("left of centre" if mx_ < 0 else "right of centre")
    where += ", a little low" if my_ < -0.06 else ""
    para(tx, ty, [
        (f"The monitor sits {where}, {mw / cam.hfov * 100:.0f} % of the frame's width, the brightest thing", INK),
        ("in the blue room; a click glides in to the posts (the existing glide). The orbit keeps", INK),
        ("its ±25° around room_view_target. The code today starts straight on at the monitor:", INK),
        ("Phase 4 points it at room_view instead (one change in desktop.js, no new names).", INK),
    ], 13.5)
    return vis


def notes_panel(px, py, pw, ph, lid90):
    panel(px, py, pw, ph, "Room numbers and why", "ROOM, WINDOW, DOOR, LAYOUT, WALL_GUITARS, HERO in blender/lib/constants.py")
    y = para(px + 22, py + 92, [
        (f"{cm(R['width'], 0)} × {cm(R['depth'], 0)}, ceiling {cm(H, 0)} clear", INK, 650),
        "14 ft 5 in × 13 ft 9 in: a large master bedroom in an older",
        "Pune flat. Smaller, and bed, desk chair and piano bench collide.",
        f"The 3 m ceiling lets the wall guitars hang {cm(WG['bottom'] - lid90, 1)} above",
        f"the piano's lid fully open ({cm(lid90, 1)}), with {cm(H - WG['bottom'] - max(WG['length']), 0)} under the ceiling.",
        "Walls: back 23 cm brick (outside wall), sides 15 cm.",
        "",
        ("Window: back wall, east", INK, 650),
        "120 × 105, sill 105, head 210: aluminium sliding with a grill,",
        "over the bed's head; the stone ledge holds the plant beside",
        "the desk. East, so the live window can show a real sunrise.",
        "",
        ("Door: left wall by the front corner, as in the photo", INK, 650),
        "90 × 210, swings onto the front wall; switch board at 120.",
        "",
        ("Clearances (checked by the script)", INK, 650),
    ], 14, lh=20.5)
    for name, g, need, ok in CHECKS:
        col = INK if ok else "#a33"
        val = "overlap" if g < 0 else cm(g, 1)
        text(px + 34, y, f"{'ok' if ok else 'CLASH'}  {name}: {val}", 13, col)
        y += 19


def main():
    os.makedirs(OUT, exist_ok=True)
    lid90, lid55 = run_checks()
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_PX}" height="{H_PX}" viewBox="0 0 {W_PX} {H_PX}" '
        f'font-family="-apple-system, Helvetica Neue, Arial, sans-serif">')
    add(f'<rect width="{W_PX}" height="{H_PX}" fill="{PAPER}"/>')
    text(48, 58, "The room · plan sheet", 32, INK, weight=650)
    text(48, 88, f"set_room and where every root stands · to scale from blender/lib/constants.py · dimensions in cm · "
         f"Blender axes: back wall +Y, viewer −Y, origin on the floor at the room's centre", 16, MUTED)
    text(W_PX - 48, 58, "2026-10-22 · for the owner's review, before the shell is built", 15, MUTED, "end")
    v, cam = plan(40, 116, 1290, 1300)
    hero_panel(1350, 116, 1010, 1300, cam)
    elevations(40, 1440, 2320, 610, lid90, lid55)
    y3 = 2074
    rack_options(40, y3, 1000, 620, cam)
    notes_panel(1060, y3, 650, 620, lid90)
    shell_list(1730, y3, 630, 620)
    front_wall(40, 2718, 640, 440)
    owner_panel(700, 2718, 1660, 440)
    add("</svg>")
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>Room plan sheet</title>"
            f"<style>html,body{{margin:0;background:{PAPER}}}svg{{display:block}}</style></head><body>"
            + "\n".join(out) + "</body></html>")
    hp = os.path.join(OUT, "room-plan-sheet.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    png = os.path.join(OUT, "room-plan-sheet.png")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={W_PX},{H_PX}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for name, g, need, ok in CHECKS:
        print(("ok    " if ok else "CLASH ") + f"{name}: {g * 100:.1f} cm (need {need * 100:.0f})")
    print("visibility:", {k: round(x, 2) for k, x in visibility(cam).items()})
    print("wrote", hp, png)


if __name__ == "__main__":
    main()
