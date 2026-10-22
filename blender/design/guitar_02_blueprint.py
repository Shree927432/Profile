"""2D blueprint for guitar_02 (the Woodstock white Strat replica), to scale from
blender/lib/guitar_specs.py. Dimensions in mm.

Plain Python (no Blender): writes an HTML page with one SVG, then renders it to a PNG
with the cached headless Chromium. Run from the repo root:

    python3 blender/design/guitar_02_blueprint.py

Output: video-local/footage/2026-10-23-guitar-02/guitar-02-blueprint.{html,png}
"""
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from lib.guitar_specs import GUITAR_02 as G, spline, fret_positions  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "video-local", "footage", "2026-10-23-guitar-02")
W_PX, H_PX = 2400, 4900
CHROME = os.path.expanduser("~/Library/Caches/ms-playwright/chromium_headless_shell-1223/"
                            "chrome-headless-shell-mac-arm64/chrome-headless-shell")

INK, ACC, MUTED, PAPER, LINE = "#1d1c1a", "#b5532a", "#6b675f", "#f6f3ec", "#d6d0c4"
COL = dict(  # drawing colours; the material table below has the render values
    body="#efe9d8", body_b="#e8dfc4", body_c="#ddd0ac", guard="#f6f3ec", ply="#1f1e1c",
    maple="#e2bb76", head="#e6c385", neck_back="#e3bf80", dot="#1d1b18", fret="#b9b7b0",
    nut="#efe8d6", chrome="#cfd2d6", chrome_d="#9da2a8", plastic="#ede6d2", string="#7d8085",
    contour="#c9bfa4", hidden="#8d8678", primer="#c8bfa8", wood="#b99a6e")

out = []
_clip = [0]


def add(s):
    out.append(s)


def mm(x, nd=1):
    return f"{x:.{nd}f}".rstrip("0").rstrip(".")


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def shape(pts, at, deg=0.0):
    return [(at[0] + q[0], at[1] + q[1]) for q in (rot(p, deg) for p in pts)]


def rrect(w, h, r, n=5):
    """Rounded rectangle centred on 0, w along x, h along y."""
    r = min(r, w / 2, h / 2)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def ellipse(w, h, n=28):
    return [(w / 2 * math.cos(2 * math.pi * k / n), h / 2 * math.sin(2 * math.pi * k / n)) for k in range(n)]


def lens(l, w, n=14):
    """Football: two circular arcs meeting at points, l long (x), w wide."""
    R = (l * l / 4 + w * w / 4) / w
    a = math.asin((l / 2) / R)
    top = [(R * math.sin(t), R * math.cos(t) - (R - w / 2)) for t in
           (-a + 2 * a * k / n for k in range(n + 1))]
    return top + [(-x, -y) for x, y in top[1:-1]]


class View:
    """Guitar (u, v) in mm to page px. mirror=True draws the back view (u flips)."""
    def __init__(self, ox, oy, s, mirror=False):
        self.ox, self.oy, self.s, self.m = ox, oy, s, -1 if mirror else 1

    def p(self, u, v):
        return self.ox + self.m * u * self.s, self.oy - v * self.s

    @classmethod
    def at(cls, x, y, w, h, uc, vc, s):
        """A view of scale s with guitar point (uc, vc) at the centre of the page box."""
        return cls(x + w / 2 - uc * s, y + h / 2 + vc * s, s)

    def d(self, pts, closed=True):
        q = [self.p(*pt) for pt in pts]
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in q) + (" Z" if closed else "")

    def path(self, pts, fill="none", stroke=INK, sw=1.1, closed=True, extra=""):
        add(f'<path d="{self.d(pts, closed)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round" {extra}/>')

    def line(self, a, b, stroke=INK, sw=1.1, extra=""):
        (x0, y0), (x1, y1) = self.p(*a), self.p(*b)
        add(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linecap="round" {extra}/>')

    def circle(self, u, v, r, fill, stroke=INK, sw=1.0, extra=""):
        x, y = self.p(u, v)
        add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * self.s:.2f}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" {extra}/>')


def text(x, y, s, size=14, fill=INK, anchor="start", weight=400, rot_=None, italic=False, family=None):
    tr = f' transform="rotate({rot_} {x:.1f} {y:.1f})"' if rot_ is not None else ""
    st = ' font-style="italic"' if italic else ""
    fm = f' font-family="{family}"' if family else ""
    add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
        f'font-weight="{weight}"{st}{fm}{tr}>{s}</text>')


def para(x, y, s, width_ch, size=13, fill=MUTED, lh=None, weight=400):
    lh = lh or size * 1.35
    line_ = ""
    for wd in s.split():
        if len(line_) + len(wd) + 1 > width_ch:
            text(x, y, line_, size, fill, weight=weight)
            line_, y = "", y + lh
        line_ = (line_ + " " + wd).strip()
    if line_:
        text(x, y, line_, size, fill, weight=weight)
        y += lh
    return y


def balloon(x, y, n):
    add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="#fffdf8" stroke="{ACC}" stroke-width="1.3"/>')
    text(x, y + 4.5, str(n), 12, ACC, "middle", weight=700)


def note_box(x, y, w, h):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPER}" fill-opacity="0.92"/>')


def dim_h(x0, x1, y, label, above=True, ext=None):
    add(f'<g stroke="{ACC}" stroke-width="1"><line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}"/>'
        f'<line x1="{x0:.1f}" y1="{y - 6:.1f}" x2="{x0:.1f}" y2="{y + 6:.1f}"/>'
        f'<line x1="{x1:.1f}" y1="{y - 6:.1f}" x2="{x1:.1f}" y2="{y + 6:.1f}"/></g>')
    if ext:
        for x, y_ in ext:
            add(f'<line x1="{x:.1f}" y1="{y_:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="{ACC}" '
                f'stroke-width="0.6" stroke-dasharray="3 3"/>')
    text((x0 + x1) / 2, y - 6 if above else y + 17, label, 13, ACC, "middle")


def dim_v(x, y0, y1, label, left=True, ext=None):
    add(f'<g stroke="{ACC}" stroke-width="1"><line x1="{x:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y1:.1f}"/>'
        f'<line x1="{x - 6:.1f}" y1="{y0:.1f}" x2="{x + 6:.1f}" y2="{y0:.1f}"/>'
        f'<line x1="{x - 6:.1f}" y1="{y1:.1f}" x2="{x + 6:.1f}" y2="{y1:.1f}"/></g>')
    if ext:
        for x_, y in ext:
            add(f'<line x1="{x_:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="{ACC}" '
                f'stroke-width="0.6" stroke-dasharray="3 3"/>')
    text(x - 7 if left else x + 16, (y0 + y1) / 2, label, 13, ACC, "middle", rot_=-90)


def leader(x0, y0, x1, y1, label, anchor="start", sub=None):
    """Leader from the part (x0, y0) to a label at (x1, y1); the line stops at the label's near end."""
    wt = max(len(label) * 6.7, len(sub or "") * 6.0)
    xe = x1
    if anchor == "start" and x0 > x1:
        xe = x1 + wt + 8
    elif anchor == "end" and x0 < x1:
        xe = x1 - wt - 8
    add(f'<polyline points="{x0:.1f},{y0:.1f} {xe:.1f},{y1:.1f}" fill="none" stroke="{MUTED}" '
        f'stroke-width="0.9"/><circle cx="{x0:.1f}" cy="{y0:.1f}" r="2.4" fill="{MUTED}"/>')
    dx = 4 if anchor == "start" else -4
    text(x1 + dx, y1 + 4, label, 13, INK, anchor)
    if sub:
        text(x1 + dx, y1 + 20, sub, 12, MUTED, anchor)


def panel(x, y, w, h, title, sub=None):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{LINE}" stroke-width="1"/>')
    text(x + 16, y + 30, title, 19, INK, weight=600)
    if sub:
        text(x + 16, y + 52, sub, 13, MUTED)


def clip_path_begin(V, pts):
    _clip[0] += 1
    cid = f"p{_clip[0]}"
    add(f'<clipPath id="{cid}"><path d="{V.d(pts)}"/></clipPath><g clip-path="url(#{cid})">')


def spread(items, gap):
    """items: [y_wanted, ...payload]; nudges y so labels sit at least gap apart, in order."""
    items.sort(key=lambda it: it[0])
    for i in range(1, len(items)):
        if items[i][0] < items[i - 1][0] + gap:
            items[i][0] = items[i - 1][0] + gap
    return items


def clip_begin(x, y, w, h):
    _clip[0] += 1
    cid = f"c{_clip[0]}"
    add(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>'
        f'<g clip-path="url(#{cid})">')


def clip_end():
    add("</g>")


# ---------------------------------------------------------------------------
# geometry shared by every view
# ---------------------------------------------------------------------------
SC, VN = G["scale"], G["v_nut"]
VS = G["v_saddle"]
FRETS = fret_positions(SC, G["frets"])
BODY = spline(G["body"])
GUARD = spline(G["pickguard"])
HEAD = [(a, VN + b) for a, b in spline(G["headstock"], closed=False)]
FOREARM = spline(G["forearm"]["region"])
BELLY = spline(G["belly"]["region"])
BODY_W = max(p[0] for p in BODY) - min(p[0] for p in BODY)
BODY_L = max(p[1] for p in BODY)


def neck_w(v):
    return G["nut_w"] + (G["w12"] - G["nut_w"]) * (VN - v) / (SC / 2)


def neck_outline():
    hw = neck_w(G["butt_side_v"]) / 2
    dv = G["butt_side_v"] - G["v_butt"]
    end = [(hw * math.cos(t), G["butt_side_v"] + dv * math.sin(t))
           for t in (math.pi + math.pi * k / 16 for k in range(17))]
    return [(-G["nut_w"] / 2, VN)] + end + [(G["nut_w"] / 2, VN)]


NECK = neck_outline()


def strings_nut():
    n = len(G["strings"])
    return [-G["nut_spread"] / 2 + G["nut_spread"] * i / (n - 1) for i in range(n)]


def strings_bridge():
    n = len(G["strings"])
    return [-G["bridge_spread"] / 2 + G["bridge_spread"] * i / (n - 1) for i in range(n)]


def posts():
    return [(a, VN + b) for a, b in G["tuner_posts"]]


def keys():
    """Key centres: each shaft square to the neck axis, the button `gap` past the bass-side edge."""
    k = G["tuner_key"]
    return [(head_width_at(pv - VN)[0] - k["gap"] - k["w"] / 2, pv) for _, pv in posts()]


def pickups():
    """(centre, angle) for neck, middle, bridge."""
    res = []
    for i, d in enumerate(G["pickups_from_scale"]):
        res.append(((0.0, VS + d), -G["bridge_slant_deg"] if i == 2 else 0.0))
    return res


def head_width_at(b):
    """Headstock width at b above the nut, from the sampled outline."""
    v = VN + b
    xs = []
    pts = HEAD
    for (a0, v0), (a1, v1) in zip(pts, pts[1:]):
        if (v0 - v) * (v1 - v) <= 0 and v0 != v1:
            xs.append(a0 + (a1 - a0) * (v - v0) / (v1 - v0))
    return (min(xs), max(xs)) if xs else (0, 0)


def hook_contact():
    gap = G["hook"]["gap"]
    for k in range(0, 600):
        b = k * 0.1
        a0, a1 = head_width_at(b)
        if a1 - a0 >= gap:
            return b, a0, a1
    return 0, 0, 0


HOOK_B, HOOK_A0, HOOK_A1 = hook_contact()


def body_span(v):
    xs = []
    for (u0, v0), (u1, v1) in zip(BODY, BODY[1:] + BODY[:1]):
        if (v0 - v) * (v1 - v) <= 0 and v0 != v1:
            xs.append(u0 + (u1 - u0) * (v - v0) / (v1 - v0))
    return min(xs), max(xs)


# ---------------------------------------------------------------------------
# front view: as it hangs on the wall, facing the room
# ---------------------------------------------------------------------------
def draw_front(V, body_fill=COL["body"], wear=0, fine=True, strings=True, hook=True, decals=False):
    s = V.s
    sw = 1.1 if s < 3 else 1.4
    # strap buttons first (behind the edge)
    sb = G["strap_button"]
    for u, v, ang, _ in G["strap_buttons"]:
        V.path(shape(rrect(sb["h"] * 2, sb["d"], 3), (u, v), ang), COL["chrome"], INK, sw * 0.9)
        cu, cv = u + sb["h"] * math.cos(math.radians(ang)), v + sb["h"] * math.sin(math.radians(ang))
        V.path(shape(rrect(3.2, sb["d"] + 2.5, 1.5), (cu, cv), ang), COL["chrome"], INK, sw * 0.9)
    # tuner keys and shafts (behind the headstock face)
    k = G["tuner_key"]
    for (pa, pv), (ka, _) in zip(posts(), keys()):
        V.line((pa, pv), (ka, pv), COL["chrome_d"], max(1.2, 3.0 * s * 0.5))
        V.path(shape(ellipse(k["w"], k["h"]), (ka, pv)), COL["chrome"], INK, sw * 0.9)
    # body
    V.path(BODY, body_fill, INK, sw * 1.2)
    if wear:
        _wear_front(V, wear)
    # forearm contour
    clip_path_begin(V, BODY)
    V.path(FOREARM, COL["contour"], "none", 0, extra='fill-opacity="0.35"')
    V.path(FOREARM, "none", COL["hidden"], 0.9, extra='stroke-dasharray="5 4"')
    clip_end()
    V.path(BODY, "none", INK, sw * 1.2)
    # jack: recess, plate, screws, socket
    j = G["jack"]
    V.path(shape(lens(j["l"] + 7, j["w"] + 8), (j["u"], j["v"]), j["angle_deg"]), "#d4ccb4", INK, sw * 0.8)
    V.path(shape(lens(j["l"], j["w"]), (j["u"], j["v"]), j["angle_deg"]), COL["chrome"], INK, sw)
    for sgn in (-1, 1):
        q = rot((sgn * (j["l"] / 2 - 7), 0), j["angle_deg"])
        V.circle(j["u"] + q[0], j["v"] + q[1], 1.9, COL["chrome_d"], INK, 0.8)
    V.circle(j["u"], j["v"], j["socket_d"] / 2, COL["chrome_d"], INK, sw * 0.9)
    V.circle(j["u"], j["v"], 3.2, "#2a2826", "none", 0)
    # pickguard with its 3-ply bevel (white edge, black line, white top)
    _clip[0] += 1
    cid = f"g{_clip[0]}"
    add(f'<clipPath id="{cid}"><path d="{V.d(GUARD)}"/></clipPath>')
    V.path(GUARD, COL["guard"], "none", 0)
    add(f'<g clip-path="url(#{cid})">')
    V.path(GUARD, "none", COL["ply"], max(2.0, 1.6 * s))
    V.path(GUARD, "none", "#e4ded0", max(1.0, 0.8 * s))
    add("</g>")
    V.path(GUARD, "none", INK, sw * 0.8)
    for u, v in G["guard_screws"]:
        _screw(V, u, v, 2.9)
    # neck and fretboard (maple cap), frets, dots, nut
    V.path(NECK, COL["maple"], INK, sw)
    for i, x in enumerate(FRETS):
        v = VN - x
        hw = neck_w(v) / 2 - 0.6
        V.line((-hw, v), (hw, v), COL["fret"], max(1.0, G["fret_wire"][0] * s * 0.9))
    if fine and s >= 3:
        for x in FRETS:
            v = VN - x
            hw = neck_w(v) / 2 - 0.6
            V.line((-hw, v + 0.9), (hw, v + 0.9), "#f4f1ea", 0.6)
    prev = 0.0
    for n, x in enumerate(FRETS, 1):
        if n in G["dots"]:
            vm = VN - (prev + x) / 2
            if n == 12:
                for sgn in (-1, 1):
                    V.circle(sgn * G["dot12_offset"], vm, G["dot_d"] / 2, COL["dot"], "none", 0)
            else:
                V.circle(0, vm, G["dot_d"] / 2, COL["dot"], "none", 0)
        prev = x
    # headstock
    V.path(HEAD, COL["head"], INK, sw)
    V.path([(-G["nut_w"] / 2, VN), (-G["nut_w"] / 2, VN + G["nut_l"]), (G["nut_w"] / 2, VN + G["nut_l"]),
            (G["nut_w"] / 2, VN)], COL["nut"], INK, sw * 0.9)
    if decals:
        _decal_boxes(V)
    for pa, pv in posts():
        V.circle(pa, pv, G["bushing_d"] / 2, COL["chrome"], INK, sw * 0.8)
        V.circle(pa, pv, G["post_d"] / 2, COL["chrome_d"], INK, sw * 0.8)
        if s >= 3:
            V.line((pa - G["post_d"] / 2, pv), (pa + G["post_d"] / 2, pv), "#4a4844", 1.0)
    # pickups
    pk = G["pickup"]
    for (c, ang) in pickups():
        V.path(shape(rrect(pk["l"], pk["w"], 7), c, ang), COL["plastic"], INK, sw)
        for i in range(6):
            q = rot((-pk["pole_spread"] / 2 + pk["pole_spread"] * i / 5, 0), ang)
            V.circle(c[0] + q[0], c[1] + q[1], pk["pole_d"] / 2, "#a8a9a6", INK, 0.7)
        for sgn in (-1, 1):
            q = rot((sgn * pk["screw_off"], 0), ang)
            _screw(V, c[0] + q[0], c[1] + q[1], 2.6)
    # tremolo bridge
    br = G["bridge"]
    front = VS + br["front_off"]
    V.path(shape(rrect(br["w"], br["l"], 2.5), (0, front - br["l"] / 2)), COL["chrome"], INK, sw)
    V.path(shape(rrect(br["w"] - 1.5, 4.0, 1.0), (0, front - br["l"] + 2.0)), COL["chrome_d"], INK, sw * 0.7)
    sb_u = strings_bridge()
    for u in sb_u:
        V.circle(u, front - 4.6, br["screw_d"] / 2, COL["chrome_d"], INK, 0.7)
    for u, back in zip(sb_u, G["saddle_back"]):
        crown = VS - back
        V.path(shape(rrect(br["saddle_w"] - 0.6, br["saddle_l"], 1.6), (u, crown - br["saddle_l"] / 2 + 3.5)),
               "#dadde0", INK, sw * 0.8)
        if s >= 3:
            for sgn in (-1, 1):
                V.circle(u + sgn * 2.9, crown - 6.5, 1.3, "#55524d", "none", 0)
            V.line((u, crown - br["saddle_l"] + 3.5), (u, front - br["l"] + 4), "#55524d", 1.0)
    # knobs
    kn = G["knob"]
    for _, u, v in G["knobs"]:
        V.circle(u, v, kn["d"] / 2, COL["plastic"], INK, sw)
        V.circle(u, v, kn["top_d"] / 2, "#f3eee0", INK, sw * 0.6)
        if s >= 3:
            for t in range(11):
                a = math.radians(90 - 30 * t)
                r0 = kn["d"] / 2 - 0.4
                V.line((u + r0 * math.cos(a) * 0.93, v + r0 * math.sin(a) * 0.93),
                       (u + r0 * math.cos(a), v + r0 * math.sin(a)), "#8d8678", 0.8)
    # switch: slot and tip (in the neck position)
    sw_ = G["switch"]
    V.path(shape(rrect(sw_["slot_l"], sw_["slot_w"], 1.5), (sw_["u"], sw_["v"]), sw_["angle_deg"]),
           "#2a2826", INK, 0.8)
    tip_c = rot((-(sw_["slot_l"] / 2 - 3.5), 0), sw_["angle_deg"])
    V.path(shape(rrect(sw_["tip_w"], sw_["tip_l"], 3.2), (sw_["u"] + tip_c[0], sw_["v"] + tip_c[1]),
                 sw_["angle_deg"]), COL["plastic"], INK, sw)
    # strings
    if strings:
        _strings_front(V)
    # tremolo arm, resting across the strings as displayed
    a = G["arm"]
    end = (a["u"] + a["length"] * math.cos(math.radians(a["angle_deg"])),
           a["v"] + a["length"] * math.sin(math.radians(a["angle_deg"])))
    V.circle(a["u"], a["v"], 4.2, COL["chrome_d"], INK, 0.8)
    V.line((a["u"], a["v"]), end, INK, max(2.2, 5.2 * s * 0.5 + 1.0))
    V.line((a["u"], a["v"]), end, COL["chrome"], max(1.2, 5.2 * s * 0.5 - 0.4))
    tip0 = (end[0] - 24 * math.cos(math.radians(a["angle_deg"])), end[1] - 24 * math.sin(math.radians(a["angle_deg"])))
    V.line(tip0, end, INK, max(2.8, 7 * s * 0.5 + 1))
    V.line(tip0, end, COL["plastic"], max(1.8, 7 * s * 0.5 - 0.4))
    # wall hook (guitars_static) and the pivot of guitar_02
    if hook:
        for a_ in (HOOK_A0, HOOK_A1):
            sg = -1 if a_ < 0 else 1
            V.path([(a_ + sg * 1.5, VN + HOOK_B - 14), (a_ + sg * 1.5, VN + HOOK_B + 2),
                    (a_ + sg * 9, VN + HOOK_B + 2), (a_ + sg * 9, VN + HOOK_B - 14)],
                   "#8d8678", INK, 0.8, extra='fill-opacity="0.35" stroke-dasharray="3 2"')
        x, y = V.p(0, VN + HOOK_B)
        r = 7
        add(f'<g stroke="{ACC}" stroke-width="1.6"><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none"/>'
            f'<line x1="{x - r - 4:.1f}" y1="{y:.1f}" x2="{x + r + 4:.1f}" y2="{y:.1f}"/>'
            f'<line x1="{x:.1f}" y1="{y - r - 4:.1f}" x2="{x:.1f}" y2="{y + r + 4:.1f}"/></g>')


def _screw(V, u, v, d):
    V.circle(u, v, d / 2, COL["chrome"], INK, 0.7)
    if V.s >= 3:
        V.line((u - d * 0.35, v - d * 0.2), (u + d * 0.35, v + d * 0.2), "#55524d", 0.8)


def _strings_front(V):
    nut = strings_nut()
    br = strings_bridge()
    gauges = G["gauges"]
    pts_ = posts()
    for i, (a, u, back, g) in enumerate(zip(nut, br, G["saddle_back"], gauges)):
        w = max(0.7, g * 25.4 * V.s * 0.9)
        V.line((a, VN), (u, VS - back), COL["string"], w)
        V.line((u, VS - back), (u, VS + G["bridge"]["front_off"] - G["bridge"]["l"] + 8), COL["string"], w)
        pa, pv = pts_[i]
        V.line((a, VN + G["nut_l"]), (pa + G["post_d"] / 2, pv), COL["string"], w)
    t = G["string_tree"]
    V.path(shape(rrect(t["w"], t["h"], 2.0), (t["a"], VN + t["b"])), COL["chrome"], INK, 0.9)
    V.circle(t["a"], VN + t["b"], 1.4, COL["chrome_d"], INK, 0.6)


def _wear_front(V, level):
    """Light edge wear for the finish options (texture, not geometry)."""
    spots = [(-150, 120, 10, 26, 20), (-157, 95, 6, 18, 10), (-106, 452, 9, 6, -20), (106, 380, 8, 5, 10),
             (150, 160, 5, 16, 80), (0, 1.5, 22, 3, 0)]
    if level >= 2:
        spots += [(-140, 190, 8, 22, 25), (124, 362, 4, 14, 85), (60, 7, 16, 3, 5), (-125, 442, 4, 12, 60)]
    fill = COL["primer"] if level < 3 else COL["wood"]
    for u, v, w, h, ang in spots[: 4 if level == 1 else None]:
        V.path(shape(ellipse(w, h, 16), (u, v), ang), fill, "none", 0, extra='fill-opacity="0.85"')


def _decal_boxes(V):
    """Where the real headstock carries printing; drawn as hatched boxes, never reproduced."""
    for (a, b, w, h, ang, lab) in ((22, 118, 48, 20, 62, "logo decal"), (30, 84, 30, 7, 62, "model name"),
                                   (12, 28, 26, 5, 80, "patent text")):
        V.path(shape(rrect(w, h, 2), (a, VN + b), ang), "url(#hatch)", ACC, 1.0, extra='stroke-dasharray="4 3"')


# ---------------------------------------------------------------------------
# back view (seen from behind: the bass side is on the viewer's right)
# ---------------------------------------------------------------------------
def draw_back(V):
    sw = 1.1
    sb = G["strap_button"]
    for u, v, ang, _ in G["strap_buttons"]:
        V.path(shape(rrect(sb["h"] * 2, sb["d"], 3), (u, v), ang), COL["chrome"], INK, sw * 0.9)
    k = G["tuner_key"]
    for (pa, pv), (ka, _) in zip(posts(), keys()):
        V.line((pa, pv), (ka, pv), COL["chrome_d"], 1.6)
        V.path(shape(ellipse(k["w"], k["h"]), (ka, pv)), COL["chrome"], INK, sw * 0.9)
    # neck back (one maple colour, no skunk stripe) drawn before the body so the body hides the heel
    V.path(NECK, COL["neck_back"], INK, sw)
    V.path(HEAD, COL["neck_back"], INK, sw)
    V.path(BODY, COL["body"], INK, sw * 1.2)
    clip_path_begin(V, BODY)
    V.path(BELLY, COL["contour"], "none", 0, extra='fill-opacity="0.35"')
    V.path(BELLY, "none", COL["hidden"], 0.9, extra='stroke-dasharray="5 4"')
    clip_end()
    V.path(BODY, "none", INK, sw * 1.2)
    # tremolo cavity cover with string holes and screws
    tc = G["trem_cover"]
    cv = tc["v0"] + tc["l"] / 2
    V.path(shape(rrect(tc["w"], tc["l"], tc["r"]), (0, cv)), COL["guard"], INK, sw)
    for u in strings_bridge():
        V.path(shape(ellipse(5.0, 7.5, 16), (u, VS - 12)), "#3b3936", INK, 0.6)
    for sgn in (-1, 1):
        for vv in (tc["v0"] + 8, cv, tc["v0"] + tc["l"] - 8):
            _screw(V, sgn * (tc["w"] / 2 - 6), vv, 2.9)
    # neck plate, plain: 4 screws, no stamp, no serial
    npl = G["neck_plate"]
    V.path(shape(rrect(npl["w"], npl["l"], npl["r"]), (0, npl["v"])), COL["chrome"], INK, sw)
    for su in (-1, 1):
        for sv in (-1, 1):
            V.circle(su * npl["screw_du"], npl["v"] + sv * npl["screw_dv"], 4.0, COL["chrome_d"], INK, 0.8)
            V.circle(su * npl["screw_du"], npl["v"] + sv * npl["screw_dv"], 1.2, "#55524d", "none", 0)
    # tuner housings on the headstock back (plain, no stamp)
    th = G["tuner_housing"]
    for pa, pv in posts():
        V.path(shape(rrect(th["w"], th["h"], 2.5), (pa, pv)), COL["chrome"], INK, sw * 0.8)
        V.circle(pa, pv + 5, 1.2, COL["chrome_d"], INK, 0.5)


# ---------------------------------------------------------------------------
# side view from the bass side: z across the page (front of the guitar to the right)
# ---------------------------------------------------------------------------
class SideView:
    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def p(self, z, v):
        return self.ox + z * self.s, self.oy - v * self.s

    def path(self, pts, fill="none", stroke=INK, sw=1.1, closed=True, extra=""):
        q = [self.p(*pt) for pt in pts]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in q) + (" Z" if closed else "")
        add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>')

    def rect(self, z0, z1, v0, v1, fill, stroke=INK, sw=1.0, extra=""):
        self.path([(z0, v0), (z1, v0), (z1, v1), (z0, v1)], fill, stroke, sw, extra=extra)

    def line(self, a, b, stroke=INK, sw=1.0, extra=""):
        self.path([a, b], "none", stroke, sw, closed=False, extra=extra)


def bell(v, v0, v1, peak=0.45):
    if v <= v0 or v >= v1:
        return 0.0
    t = (v - v0) / (v1 - v0)
    t = t / peak * 0.5 if t < peak else 0.5 + (t - peak) / (1 - peak) * 0.5
    return math.sin(math.pi * t) ** 1.4


def neck_back_z(v):
    x = VN - v
    return G["board_above_body"] - (G["neck_t1"] + (G["neck_t12"] - G["neck_t1"]) * x / (SC / 2))


def draw_side(S):
    T = G["body_t"]
    hz_face = G["board_above_body"] - G["head_step"]
    hz_back = hz_face - G["head_t"]
    # strap buttons
    sb = G["strap_button"]
    S.rect(-T / 2 - sb["d"] / 2, -T / 2 + sb["d"] / 2, -sb["h"], 0.0, COL["chrome"], INK, 0.9)
    S.rect(-T / 2 - sb["d"] / 2, -T / 2 + sb["d"] / 2, BODY_L - 1, BODY_L - 1 + sb["h"], COL["chrome"], INK, 0.9)
    # body slab with the contours seen as edge lines on the near (bass) side
    r = G["edge_r"]
    x0, y0 = S.p(-T, BODY_L)
    x1, y1 = S.p(0, 0)
    add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" rx="{r * S.s:.1f}" '
        f'fill="{COL["body"]}" stroke="{INK}" stroke-width="1.3"/>')
    fa, be = G["forearm"], G["belly"]
    vs_ = [k * 2.0 for k in range(0, int(BODY_L / 2) + 1)]
    top = [(-fa["depth"] * bell(v, 42, 252), v) for v in vs_ if 42 <= v <= 252]
    S.path(top + [(0, 252), (0, 42)], COL["contour"], "none", 0, extra='fill-opacity="0.55"')
    S.path(top, "none", INK, 1.0, closed=False)
    bot = [(-T + be["depth"] * bell(v, 250, 455, 0.55), v) for v in vs_ if 250 <= v <= 455]
    S.path(bot + [(-T, 455), (-T, 250)], COL["contour"], "none", 0, extra='fill-opacity="0.55"')
    S.path(bot, "none", INK, 1.0, closed=False)
    for zz in (-r, -T + r):
        S.line((zz, 8), (zz, BODY_L - 8), "#b8b0a0", 0.7, extra='stroke-dasharray="2 3"')
    # tremolo block and spring cavity, hidden
    br = G["bridge"]
    front = VS + br["front_off"]
    S.rect(-T + 4, 0, front - br["l"] + 2, front - br["l"] + 21, "none", COL["hidden"], 0.9, extra='stroke-dasharray="4 3"')
    S.rect(-T + 4, -T + 16, front - br["l"] + 21, 240, "none", COL["hidden"], 0.8, extra='stroke-dasharray="4 3"')
    # pickguard
    S.rect(0, G["guard_t"], min(p[1] for p in GUARD), max(p[1] for p in GUARD), COL["guard"], INK, 0.8)
    # neck: visible above the body and beyond it; the heel in the pocket is hidden
    PE = G["v_pocket_end"]
    nb = [(neck_back_z(v), v) for v in (PE + k * (VN - PE) / 30 for k in range(31))]
    S.path([(0, G["v_butt"]), (G["board_above_body"], G["v_butt"]), (G["board_above_body"], VN)] +
           nb[::-1] + [(0, PE)], COL["maple"], INK, 1.1)
    S.rect(-G["pocket_depth"], 0, G["v_butt"], PE, "none", COL["hidden"], 0.9, extra='stroke-dasharray="4 3"')
    for x in FRETS:
        v = VN - x
        S.rect(G["board_above_body"], G["board_above_body"] + G["fret_wire"][1], v - 1.05, v + 1.05, COL["fret"], INK, 0.5)
    # nut and headstock
    S.rect(hz_face, G["board_above_body"] + G["fret_wire"][1] + 0.6, VN, VN + G["nut_l"], COL["nut"], INK, 0.9)
    S.path([(hz_face, VN + G["nut_l"]), (hz_face, G["v_tip"] - 2), (hz_face - 2, G["v_tip"]),
            (hz_back + 2, G["v_tip"]), (hz_back, G["v_tip"] - 2), (hz_back, VN),
            (neck_back_z(VN), VN)], COL["head"], INK, 1.1)
    th, k = G["tuner_housing"], G["tuner_key"]
    for _, pv in posts():
        S.rect(hz_back - th["depth"], hz_back, pv - th["h"] / 2, pv + th["h"] / 2, COL["chrome"], INK, 0.8)
        S.rect(hz_face, hz_face + G["post_h"], pv - G["post_d"] / 2, pv + G["post_d"] / 2, COL["chrome_d"], INK, 0.8)
        S.rect(hz_face, hz_face + 1.5, pv - G["bushing_d"] / 2, pv + G["bushing_d"] / 2, COL["chrome"], INK, 0.6)
        S.rect(k["z"] - k["t"] / 2, k["z"] + k["t"] / 2, pv - k["h"] / 2, pv + k["h"] / 2, COL["chrome"], INK, 0.8)
    t = G["string_tree"]
    S.rect(hz_face, hz_face + t["height"], VN + t["b"] - 2.5, VN + t["b"] + 2.5, COL["chrome"], INK, 0.8)
    # pickups, bridge, knobs, switch above the guard
    pk = G["pickup"]
    for (c, ang), top_z in zip(pickups(), G["pickup_top_z"]):
        half = abs(pk["w"] / 2 * math.cos(math.radians(ang))) + abs(pk["l"] / 2 * math.sin(math.radians(ang)))
        S.rect(G["guard_t"], top_z, c[1] - half, c[1] + half, COL["plastic"], INK, 0.8)
    S.rect(br["float_gap"], br["float_gap"] + 1.2, front - br["l"], front, COL["chrome"], INK, 0.8)
    S.rect(br["float_gap"], br["float_gap"] + br["lip_h"], front - br["l"], front - br["l"] + 1.5, COL["chrome"], INK, 0.8)
    crown = VS - 3.0
    S.path([(br["float_gap"] + 1.2, crown - br["saddle_l"] + 3.5), (br["saddle_top_z"] - 3, crown - br["saddle_l"] + 3.5),
            (br["saddle_top_z"], crown), (br["saddle_top_z"] - 1, crown + 3.5), (br["float_gap"] + 1.2, crown + 3.5)],
           "#dadde0", INK, 0.8)
    kn = G["knob"]
    for _, u, v in G["knobs"]:
        z0 = G["guard_t"] + kn["above_guard"]
        S.path([(z0, v - kn["d"] / 2), (z0 + 4, v - kn["d"] / 2), (z0 + kn["h"], v - kn["top_d"] / 2),
                (z0 + kn["h"], v + kn["top_d"] / 2), (z0 + 4, v + kn["d"] / 2), (z0, v + kn["d"] / 2)],
               COL["plastic"], INK, 0.8)
    sw_ = G["switch"]
    S.rect(G["guard_t"], G["guard_t"] + 11, sw_["v"] + 6 - 4, sw_["v"] + 6 + 4, COL["plastic"], INK, 0.8)
    # tremolo arm, rising from its socket then across
    av = G["arm"]["v"]
    arm_ = [(br["float_gap"] + 1.2, av), (12, av + 1), (19, av + 6), (22, av + 16), (22.5, av + 52)]
    S.path(arm_, "none", INK, 2.6, closed=False)
    S.path(arm_, "none", COL["chrome"], 1.4, closed=False)
    # one string, saddle to nut to the nearest post
    nz = G["board_above_body"] + G["fret_wire"][1] + 0.6
    S.line((br["saddle_top_z"], crown), (nz, VN), COL["string"], 1.0)
    S.line((nz, VN + G["nut_l"]), (hz_face + 9, posts()[0][1]), COL["string"], 1.0)


# ---------------------------------------------------------------------------
# cross sections through the body contours
# ---------------------------------------------------------------------------
def section_pts(v, kind):
    T, r = G["body_t"], G["edge_r"]
    umin, umax = body_span(v)
    fa, be = G["forearm"], G["belly"]
    df = fa["depth"] * bell(v, 42, 252) if kind == "A" else 0.0
    db = be["depth"] * bell(v, 250, 455, 0.55) if kind == "B" else 0.0

    def ztop(u):
        if df and u < umin + fa["width"]:
            return -df * ((umin + fa["width"] - u) / fa["width"]) ** 1.6
        return 0.0

    def zbot(u):
        if db and u < umin + be["width"]:
            return -T + db * ((umin + be["width"] - u) / be["width"]) ** 1.6
        return -T

    n = 80
    top = [(umin + r + (umax - umin - 2 * r) * k / n, 0) for k in range(n + 1)]
    top = [(u, ztop(u)) for u, _ in top]
    pts = []
    zt0 = ztop(umin + r)
    for k in range(7):     # bass top corner
        a = math.pi - math.pi / 2 * k / 6
        pts.append((umin + r + r * math.cos(a), zt0 - r + r * math.sin(a)))
    pts += top
    for k in range(1, 13):  # treble edge: top roundover, side, bottom roundover
        a = math.pi / 2 - math.pi * k / 12
        if k <= 6:
            pts.append((umax - r + r * math.cos(a), -r + r * math.sin(a)))
        else:
            pts.append((umax - r + r * math.cos(a), -T + r + r * math.sin(a)))
    bot = [(umax - r - (umax - umin - 2 * r) * k / n, 0) for k in range(n + 1)]
    pts += [(u, zbot(u)) for u, _ in bot]
    zb0 = zbot(umin + r)
    for k in range(7):     # bass bottom corner
        a = -math.pi / 2 - math.pi / 2 * k / 6
        pts.append((umin + r + r * math.cos(a), zb0 + r + r * math.sin(a)))
    return pts, umin, umax, df, db


# ---------------------------------------------------------------------------
# small silhouettes for the option strips
# ---------------------------------------------------------------------------
def mini(V, mirror_geo=False, thick_right=True, label_strings=False):
    """Front silhouette at small scale. mirror_geo draws a true mirrored guitar."""
    m = -1 if mirror_geo else 1
    f = lambda pts: [(m * u, v) for u, v in pts]  # noqa: E731
    k = G["tuner_key"]
    for ka, pv in keys():
        V.path(shape(ellipse(k["w"], k["h"]), (m * ka, pv)), COL["chrome"], INK, 0.7)
    V.path(f(BODY), COL["body"], INK, 1.0)
    V.path(f(GUARD), COL["guard"], INK, 0.8)
    V.path(f(NECK), COL["maple"], INK, 0.8)
    V.path(f(HEAD), COL["head"], INK, 0.8)
    for (c, ang) in pickups():
        V.path(f(shape(rrect(G["pickup"]["l"], G["pickup"]["w"], 7), c, ang)), COL["plastic"], INK, 0.7)
    for _, u, v in G["knobs"]:
        V.circle(m * u, v, G["knob"]["d"] / 2, COL["plastic"], INK, 0.7)
    j = G["jack"]
    V.path(f(shape(lens(j["l"], j["w"]), (j["u"], j["v"]), j["angle_deg"])), COL["chrome"], INK, 0.7)
    br = G["bridge"]
    V.path(f(shape(rrect(br["w"], br["l"], 2), (0, VS + br["front_off"] - br["l"] / 2))), COL["chrome"], INK, 0.7)
    nut, bri = strings_nut(), strings_bridge()
    gauges = list(G["gauges"]) if thick_right else list(G["gauges"])[::-1]
    for a, u, g in zip(nut, bri, gauges):
        V.line((m * a, VN), (m * u, VS), "#55585c", 0.5 + g * 40)


# ---------------------------------------------------------------------------
# the sheet
# ---------------------------------------------------------------------------
def build():
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_PX}" height="{H_PX}" viewBox="0 0 {W_PX} {H_PX}" '
        f'font-family="-apple-system, Helvetica Neue, Arial, sans-serif">')
    add('<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<line x1="0" y1="0" x2="0" y2="6" stroke="{ACC}" stroke-width="1.2" stroke-opacity=".55"/></pattern></defs>')
    add(f'<rect width="{W_PX}" height="{H_PX}" fill="{PAPER}"/>')
    text(48, 58, "guitar_02 · the Woodstock white Strat · blueprint", 32, INK, weight=650)
    text(48, 88, f"After Jimi Hendrix's 1968 Olympic White guitar, a right-handed guitar flipped and strung "
         f"left-handed · drawn to scale from blender/lib/guitar_specs.py · mm · {mm(G['overall'])} long, "
         f"{mm(BODY_W)} wide, {mm(G['body_t'])} body · 21 frets, {mm(SC)} scale · no logos, names or serial",
         16, MUTED)
    text(W_PX - 48, 58, "2026-10-23 · for the owner's review, before 3D modelling", 15, MUTED, "end")

    # ===== row 1: side, front, back at 1:1 = 2 px/mm =====================================
    s = 2.0
    top_y, row_h = 116, 2200
    base_y = top_y + row_h - 90          # page y of v = 0
    # --- front --------------------------------------------------------------------------
    fx, fw = 520, 940
    panel(fx, top_y, fw, row_h, "1 · Front, as it hangs on the wall facing the room",
          "Option A (recommended): exactly as the real guitar hangs. Flipped means turned 180° in its own plane, "
          "so on a wall the body reads right-handed.")
    VF = View(fx + fw / 2 + 10, base_y, s)
    draw_front(VF)
    # overall dims
    xl, _ = VF.p(-BODY_W / 2 - 0.2, 0)
    xr, _ = VF.p(BODY_W / 2 + 0.2, 0)
    dim_h(xl, xr, base_y + 46, f"{mm(BODY_W)} lower bout (measured 12⅝ and 12¾ in)", above=False)
    _, yt = VF.p(0, G["v_tip"])
    _, yb = VF.p(0, 0)
    dim_v(fx + 40, yt, yb, f"{mm(G['overall'])} overall, {mm(G['overall'] + G['strap_button']['h'])} with the end button",
          ext=[(VF.p(-16, G['v_tip'])[0] - 30, yt), (VF.p(0, 0)[0] - 60, yb)])
    _, yh = VF.p(0, BODY_L)
    dim_v(fx + 80, yh, yb, f"{mm(BODY_L)} body", ext=[(VF.p(-90, BODY_L)[0] - 10, yh)])
    _, yn = VF.p(0, VN)
    _, ys = VF.p(0, VS)
    dim_v(fx + fw - 40, yn, ys, f"{mm(SC)} scale, nut to saddle line (25.5 in)", left=False,
          ext=[(VF.p(G['nut_w'] / 2, VN)[0] + 4, yn), (VF.p(40, VS)[0] + 4, ys)])
    _, y12 = VF.p(0, VN - FRETS[11])
    dim_v(fx + fw - 80, yn, y12, f"{mm(FRETS[11], 2)} to 12th fret", left=False,
          ext=[(VF.p(neck_w(VN - FRETS[11]) / 2, 0)[0] + 4, y12)])
    _, yhd = VF.p(0, G["v_tip"])
    dim_v(fx + fw - 120, yhd, yn, f"{mm(G['v_tip'] - VN)} headstock", left=False)
    # neck widths
    x0, y = VF.p(-G["nut_w"] / 2, VN)
    x1, _ = VF.p(G["nut_w"] / 2, VN)
    dim_h(x0, x1, y + 34, f"{mm(G['nut_w'])} nut", above=False)
    v12 = VN - FRETS[11]
    x0, y = VF.p(-neck_w(v12) / 2, v12)
    x1, _ = VF.p(neck_w(v12) / 2, v12)
    dim_h(x0 - 0, x1, y - 16, f"{mm(G['w12'])} at 12th", above=True)
    a0, a1 = min(p[0] for p in HEAD), max(p[0] for p in HEAD)
    x0, _ = VF.p(a0, 0)
    x1, _ = VF.p(a1, 0)
    dim_h(x0, x1, yt - 22, f"{mm(a1 - a0)} headstock", above=True)
    # labels, front
    lx = fx + 120
    LL, RR = [], []
    L = lambda u, v, y, lab, sub=None: LL.append([y, VF.p(u, v), lab, sub])  # noqa: E731
    R = lambda u, v, y, lab, sub=None: RR.append([y, VF.p(u, v), lab, sub])  # noqa: E731
    L(keys()[3][0], posts()[3][1], VF.p(0, posts()[3][1])[1] + 40, "6 vintage tuners in line, metal oval keys",
      f"posts on a line {G['tuner_line_deg']:.0f} deg to the neck, backs plain")
    L(head_width_at(120)[0], VN + 120, VF.p(0, VN + 120)[1] + 150, "small headstock (owner's choice, r3)",
      "traced from the owner's photo; flat, no decal")
    R(G["string_tree"]["a"] + 5, VN + G["string_tree"]["b"], VF.p(0, VN + 62)[1] + 30,
      "one butterfly string tree", "as on the photo; holds A and low E")
    R(17.5, VN + 2, VF.p(0, VN)[1] + 74, f"bone nut {mm(G['nut_w'])}, re-slotted for", "left-handed order: e B G D A E")
    L(0, VN + HOOK_B, VF.p(0, VN + HOOK_B)[1] + 84, f"pivot: hook contact, {mm(HOOK_B)} above the nut",
      f"{mm(G['v_tip'] - VN - HOOK_B)} below the tip; hanger gap {mm(G['hook']['gap'])}")
    L(-neck_w(VN - 300) / 2, VN - 300, VF.p(0, VN - 300)[1], "maple neck with glued maple board",
      "lacquered, 7.25 in radius, 21 vintage frets")
    prev = 0
    for n, x in enumerate(FRETS, 1):
        if n == 9:
            vm = VN - (prev + x) / 2
            L(0, vm, VF.p(0, vm)[1] - 10, "black dots: 3 5 7 9 12 (pair) 15 17 19 21", "6.35 dia")
        prev = x
    pk = pickups()
    j_, sw0, br_ = G["jack"], G["switch"], strings_bridge()
    arm_pt = (G["arm"]["u"] + 80 * math.cos(math.radians(G["arm"]["angle_deg"])),
              G["arm"]["v"] + 80 * math.sin(math.radians(G["arm"]["angle_deg"])))
    items = [  # (anchor u, v), (balloon u, v), label, sub
        ((-84, 300), (-84, 300), "pickguard, 3-ply white/black/white", "11 screws, 30° bevel, 2.3 thick"),
        ((-140, 150), (-140, 150), "forearm contour (front)", "late-60s: 12 deep, 60 wide"),
        ((-37, 128), (-58, 118), "vintage synchronised tremolo", "6 screws, bent-steel saddles, 56.4 E to E"),
        (arm_pt, (arm_pt[0] - 12, arm_pt[1] + 16), "arm, resting across as displayed", "white tip"),
        ((-41, pk[2][0][1] + 7), (-60, pk[2][0][1] + 14), f"bridge pickup, slanted {mm(G['bridge_slant_deg'])}°",
         f"as built, right end to the bridge; {mm(G['pickups_from_scale'][2])} from saddle line"),
        ((0, 0), (26, -13), "tail strap button", None),
        ((-105, 456), (-130, 466), "original strap button, long horn", None),
        ((108, 383.5), (130, 394), "strap button Hendrix added", "on the short horn, for left-handed playing"),
        ((42, pk[0][0][1]), (60, pk[0][0][1] + 4), "neck pickup",
         f"{mm(G['pickups_from_scale'][0])} from saddle line (the 24th-fret node)"),
        ((42, pk[1][0][1]), (60, pk[1][0][1] + 4), "middle pickup", f"{mm(G['pickups_from_scale'][1])} from saddle line"),
        ((sw0["u"], sw0["v"]), (sw0["u"] + 20, sw0["v"] + 8), "3-way blade switch (1968)", "white tip"),
        ((64, 170), (86, 178), "volume", "white knob, 24.5 skirt"),
        ((83.5, 136), (106, 144), "tone, neck pickup", None),
        ((103, 102), (126, 109), "tone, middle pickup", None),
        ((br_[5], VS - 4.8), (40, 106), "low E saddle, now on the right", "set furthest back for intonation"),
        ((j_["u"], j_["v"]), (128, 40), "football jack in a dish", f"{mm(j_['l'])} x {mm(j_['w'])}, at {mm(j_['angle_deg'])}°"),
    ]
    for n, (a_, b_, lab, sub) in enumerate(items, 1):
        x0, y0 = VF.p(*a_)
        x1, y1 = VF.p(*b_)
        if (x0, y0) != (x1, y1):
            add(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{ACC}" stroke-width="1"/>'
                f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="2.2" fill="{ACC}"/>')
        balloon(x1, y1, n)
    for n, (a_, b_, lab, sub) in enumerate(items, 1):
        left = n <= 8
        x = fx + 24 if left else fx + 566
        y = VF.p(0, 740)[1] + ((n - 1) % 8) * 44 if left else VF.p(0, 712)[1] + ((n - 9) % 8) * 44
        balloon(x + 10, y - 4, n)
        text(x + 28, y, lab, 13, INK)
        if sub:
            text(x + 28, y + 16, sub, 12, MUTED)
    for y, (x0, y0), lab, sub in spread(LL, 44):
        leader(x0, y0, lx, y, lab, "start", sub)
    for y, (x0, y0), lab, sub in spread(RR, 44):
        leader(x0, y0, fx + fw - 160, y, lab, "end", sub)

    # --- side ---------------------------------------------------------------------------
    sx, sw_ = 40, 470
    panel(sx, top_y, sw_, row_h, "2 · Side, from the bass side", "front of the guitar to the right")
    SV = SideView(sx + 300, base_y, s)
    draw_side(SV)
    T = G["body_t"]
    xa, _ = SV.p(-T, 0)
    xb, _ = SV.p(0, 0)
    dim_h(xa, xb, base_y + 46, f"{mm(T)} body (1¾ in)", above=False)
    hz_face = G["board_above_body"] - G["head_step"]
    hz_back = hz_face - G["head_t"]
    _, yv = SV.p(0, G["v_tip"] + 14)
    xa, _ = SV.p(hz_back, 0)
    xb, _ = SV.p(hz_face, 0)
    dim_h(xa, xb, yv, f"{mm(G['head_t'])} head", above=True)
    xa, _ = SV.p(0, 0)
    xb, _ = SV.p(G["board_above_body"], 0)
    _, yv = SV.p(0, 450)
    dim_h(xa, xb, yv, "", above=True)
    text(xb + 6, yv + 4, f"{mm(G['board_above_body'])} board above body", 13, ACC)
    nb1 = neck_back_z(VN - FRETS[0])
    xa, _ = SV.p(nb1, 0)
    xb, _ = SV.p(G["board_above_body"], 0)
    _, yv = SV.p(0, VN - FRETS[0] - 6)
    dim_h(xa, xb, yv, "", above=True)
    text(xa - 6, yv + 4, f"{mm(G['neck_t1'])} at 1st", 13, ACC, "end")
    nb12 = neck_back_z(VN - FRETS[11])
    xa, _ = SV.p(nb12, 0)
    _, yv = SV.p(0, VN - FRETS[11])
    dim_h(xa, xb, yv, "", above=True)
    text(xa - 6, yv + 4, f"{mm(G['neck_t12'])} at 12th", 13, ACC, "end")
    ty = SV.p(0, 640)[1]
    for ln in ("Neck angle 0°: the neck sits",
               "flat in a 15.9 deep pocket.",
               "Headstock angle 0°: a Strat",
               "head is flat, its face 6.4",
               "below the fretboard; the",
               "string tree gives the break",
               "angle at the nut.",
               "Fretboard radius 7.25 in",
               "(184), vintage wire about",
               "2.1 wide, 1.1 high.",
               "Neck '60s C: 20.8 at the 1st",
               "fret, 23.6 at the 12th.",
               "Tuner posts 16 above the",
               "face; keys 17 behind it."):
        text(sx + 16, ty, ln, 13, MUTED)
        ty += 18
    leader(*SV.p(-G["forearm"]["depth"] * 0.9, 150), sx + 30, SV.p(0, 150)[1] + 60, "forearm bevel", "front edge")
    leader(*SV.p(-T + G["belly"]["depth"] * 0.9, 340), sx + 30, SV.p(0, 340)[1] + 10, "belly cut", "back edge, 14 deep")
    leader(*SV.p(-8, 180), sx + 30, SV.p(0, 200)[1] - 40, "tremolo block, springs", "in their cavity (hidden)")
    leader(*SV.p(-15.9, 360), sx + 30, SV.p(0, 370)[1] - 20, "heel in the pocket (hidden)")
    leader(*SV.p(14, 150), sx + sw_ - 20, SV.p(0, 150)[1] - 60, "knobs 16 tall", None)
    leader(*SV.p(G["bridge"]["saddle_top_z"], VS), sx + sw_ - 20, SV.p(0, VS)[1] + 26, "saddle top 12.5", None)
    # neck section at 12th fret, 3x
    nsx, nsy = sx + 140, SV.p(0, 900)[1]
    k3 = 4.0
    text(sx + 16, nsy - 50, "Neck at the 12th fret, 2x", 14, INK, weight=600)
    w = G["w12"]
    R_ = G["radius"]
    th = G["neck_t12"]
    crown = [(u, math.sqrt(R_ * R_ - u * u) - R_) for u in (-w / 2 + w * k / 30 for k in range(31))]
    back = [(w / 2 * math.cos(t), -th + 3 + (th - 3 - 4.5) * 0 + -0 * t) for t in ()]
    edge = crown[0][1]
    back = []
    for k in range(31):
        t = math.pi * k / 30
        back.append((w / 2 * math.cos(t), edge - 4.5 - (th - 4.5 + edge) * math.sin(t)))
    pts = [(nsx + u * k3, nsy + 70 - z * k3) for u, z in crown + back]
    add('<path d="M' + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f' Z" fill="{COL["maple"]}" '
        f'stroke="{INK}" stroke-width="1.1"/>')
    gy = nsy + 70 - (edge - 4.5) * k3
    add(f'<line x1="{nsx - w / 2 * k3 + 2:.1f}" y1="{gy:.1f}" x2="{nsx + w / 2 * k3 - 2:.1f}" y2="{gy:.1f}" '
        f'stroke="{COL["hidden"]}" stroke-width="0.9" stroke-dasharray="4 3"/>')
    text(sx + 16, nsy + 70 + th * k3 + 28, "crown R 184 (7.25 in); dashed: the", 12, ACC)
    text(sx + 16, nsy + 70 + th * k3 + 44, "glue line of the maple board", 12, MUTED)
    dim_h(nsx - w / 2 * k3, nsx + w / 2 * k3, nsy + 70 - 14, f"{mm(w)}", above=True)
    dim_v(nsx - w / 2 * k3 - 18, nsy + 70, nsy + 70 + th * k3, f"{mm(th)}")

    # --- back ---------------------------------------------------------------------------
    bx, bw = 1480, 880
    panel(bx, top_y, bw, row_h, "3 · Back, seen from behind", "bass side on the right")
    VB = View(bx + 400, base_y, s, mirror=True)
    draw_back(VB)
    BL = lambda u, v, y, lab, sub=None: leader(*VB.p(u, v), bx + 30, y, lab, "start", sub)  # noqa: E731
    BR = lambda u, v, y, lab, sub=None: leader(*VB.p(u, v), bx + bw - 30, y, lab, "end", sub)  # noqa: E731
    BR(0, 540, VB.p(0, 540)[1], "one-colour maple back", "no skunk stripe (glued board)")
    BL(-20, posts()[2][1], VB.p(0, posts()[2][1])[1] + 60, "tuner housings, plain backs", "13 x 21, 12 deep")
    npl, tc = G["neck_plate"], G["trem_cover"]
    bitems = [((-95, 360), (-95, 360), "belly contour (back)", "late-60s: 14 deep, 95 wide"),
              ((0, npl["v"] - npl["l"] / 2 + 4), (0, npl["v"] - npl["l"] / 2 - 18), "4-bolt neck plate, 51 x 64",
               "plain chrome: no stamp, no serial"),
              ((0, tc["v0"] + 110), (0, tc["v0"] + 110), f"tremolo cavity cover {mm(tc['w'])} x {mm(tc['l'])}",
               "white plastic, 6 screws, 6 string holes"),
              ((-105, 456), (-128, 466), "original strap button, long horn", None),
              ((108, 383.5), (130, 394), "strap button Hendrix added, short horn", None)]
    for n, (a_, b_, lab, sub) in enumerate(bitems, 17):
        x0, y0 = VB.p(*a_)
        x1, y1 = VB.p(*b_)
        if (x0, y0) != (x1, y1):
            add(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{ACC}" stroke-width="1"/>')
        balloon(x1, y1, n)
        x, y = bx + 560, VB.p(0, 700)[1] + (n - 17) * 44
        balloon(x + 10, y - 4, n)
        text(x + 28, y, lab, 13, INK)
        if sub:
            text(x + 28, y + 16, sub, 12, MUTED)
    ty = top_y + 100
    for ln in ("How the Woodstock guitar differs from a stock",
               "right-handed one hung the same way:",
               "· strings reversed: thin e on the left, low E on the",
               "  right, the low E going to the tip tuner",
               "· saddle intonation reversed (low E saddle furthest",
               "  back, now on the right)",
               "· nut re-slotted for the reversed order",
               "· the string tree holds A and low E",
               "· an extra strap button on the short horn",
               "· pickups, contours, controls, jack, tremolo arm and",
               "  headstock stay where Fender put them. The bridge",
               "  pickup's slant now puts the low E closest to the",
               "  bridge (his brighter bass), the pole stagger reads",
               "  backwards, and the contours face the wrong way",
               "  for a left-handed player."):
        text(bx + 560, ty, ln, 13, INK if ty == top_y + 100 else MUTED, weight=600 if ty == top_y + 100 else 400)
        ty += 19

    # ===== row 2: detail callouts =========================================================
    ry, rh = top_y + row_h + 24, 980
    # headstock 2x
    px_, pw = 40, 600
    panel(px_, ry, pw, rh, "4a · Headstock, 1.8x", "tuners, string tree, nut, hook contact")
    clip_begin(px_ + 1, ry + 60, pw - 2, rh - 62)
    VH = View.at(px_ + 80, ry + 70, pw - 80, rh - 150, -6, VN + 102, 3.6)
    draw_front(VH)
    clip_end()
    pp = posts()
    x0, y0 = VH.p(pp[0][0], pp[0][1])
    x1, y1 = VH.p(pp[1][0], pp[1][1])
    dim_v(px_ + 70, y1, y0, f"{mm(pp[1][1] - pp[0][1])} along the neck ({mm(G['tuner_pitch'])} on the post line)",
          ext=[(x0 - 30, y0), (x0 - 30, y1)])
    _, yn = VH.p(0, VN)
    dim_v(px_ + 40, y0, yn, f"{mm(G['tuner_b0'])} nut to 1st post", ext=[(VH.p(-21, 0)[0], yn)])
    for i, nm in enumerate(("e", "B", "G", "D", "A", "E")):
        xq, yq = VH.p(pp[i][0], pp[i][1])
        text(xq + 22, yq - 12, nm, 13, ACC, weight=600)
    xq, yq = VH.p(G["string_tree"]["a"], VN + G["string_tree"]["b"])
    leader(xq + 20, yq, px_ + pw - 20, yq + 40, "butterfly tree", "end", "on a 5 spacer")
    note_box(px_ + 1, ry + rh - 92, pw - 2, 91)
    para(px_ + 16, ry + rh - 70, f"r3: the small headstock, traced from the owner's photo. Posts on one line at "
         f"{G['tuner_line_deg']:.0f} deg to the neck, 25.4 apart, 6.3 posts in 9 bushings; vintage keys 2.5 past the edge.", 66)

    # pickups 1.5x
    px_, pw = 660, 480
    panel(px_, ry, pw, rh, "4b · Pickups, 1.5x", "three single coils, bridge slanted")
    clip_begin(px_ + 1, ry + 60, pw - 2, rh - 62)
    sP = 3.0
    VP = View.at(px_, ry + 60, pw, rh - 120, 0, VS + 105, sP)
    draw_front(VP)
    clip_end()
    for (c, ang), lab in zip(pickups(), ("neck", "middle", "bridge")):
        x, y = VP.p(*c)
        q = rot((G["pickup"]["l"] / 2 + 14, 0), ang)
        leader(*VP.p(c[0] + q[0], c[1] + q[1]), px_ + pw - 20, y - 4, lab, "end")
    yS = VP.p(0, VS)[1]
    for (c, ang), d in zip(pickups(), G["pickups_from_scale"]):
        y = VP.p(*c)[1]
        dim_v(px_ + 30 + 34 * pickups().index((c, ang)), y, yS, f"{mm(d)}",
              ext=[(VP.p(-G['pickup']['l'] / 2, c[1])[0], y)])
    x0, y0 = VP.p(-G["pickup"]["l"] / 2, pickups()[1][0][1])
    x1, _ = VP.p(G["pickup"]["l"] / 2, pickups()[1][0][1])
    dim_h(x0, x1, y0 - 22, f"{mm(G['pickup']['l'])} x {mm(G['pickup']['w'])} cover", above=True)
    note_box(px_ + 1, ry + rh - 74, pw - 2, 73)
    para(px_ + 16, ry + rh - 52, f"Poles 4.9 dia over {mm(G['pickup']['pole_spread'])}. Distances from the scale "
         "line. Covers white, aged; no text.", 64)

    # controls 2.5x
    px_, pw = 1160, 520
    panel(px_, ry, pw, rh, "4c · Controls, 2.5x", "volume, two tones, 3-way switch")
    clip_begin(px_ + 1, ry + 60, pw - 2, rh - 62)
    sC = 5.0
    VC = View.at(px_ - 60, ry + 60, pw, rh - 120, 84, 156, sC)
    draw_front(VC)
    clip_end()
    for name, u, v in G["knobs"]:
        x, y = VC.p(u, v)
        leader(x + 64, y, px_ + pw - 20, y - 46, name, "end", f"24.5 skirt, 20 top")
    x, y = VC.p(G["switch"]["u"], G["switch"]["v"])
    leader(x + 10, y - 20, px_ + pw - 20, y - 70, "3-way blade switch", "end")
    text(px_ + pw - 24, y - 50, "slot 22 x 3.5, at -60°", 12, MUTED, "end")
    k1, k2 = G["knobs"][0], G["knobs"][1]
    d12 = math.hypot(k2[1] - k1[1], k2[2] - k1[2])
    note_box(px_ + 1, ry + rh - 72, pw - 2, 71)
    text(px_ + 16, ry + rh - 50, f"Knob centres {mm(d12)} apart on a line at -60°; numbers 0 to 10 on the", 13, MUTED)
    text(px_ + 16, ry + rh - 32, "skirts are kept (plain digits), nothing else printed.", 13, MUTED)

    # bridge 4x and jack 4x
    px_, pw = 1700, 660
    panel(px_, ry, pw, rh, "4d · Tremolo bridge 4x, jack plate 4x")
    clip_begin(px_ + 1, ry + 60, pw - 2, 480)
    sB = 8.0
    VBr = View.at(px_, ry + 60, pw, 480, 0, VS + 2, sB)
    draw_front(VBr)
    clip_end()
    br = G["bridge"]
    front = VS + br["front_off"]
    x0, y0 = VBr.p(-br["w"] / 2, front)
    x1, _ = VBr.p(br["w"] / 2, front)
    dim_h(x0, x1, y0 - 64, f"{mm(br['w'])} plate", above=True)
    _, yr = VBr.p(0, front - br["l"])
    dim_v(x1 + 26, y0, yr, f"{mm(br['l'])}", left=False)
    xs0, _ = VBr.p(strings_bridge()[0], 0)
    xs1, _ = VBr.p(strings_bridge()[-1], 0)
    dim_h(xs0, xs1, yr + 30, "56.4 E to E (2 7/32 in)", above=False)
    clip_begin(px_ + 1, ry + 560, pw - 2, rh - 562)
    j = G["jack"]
    VJ = View.at(px_ + 120, ry + 560, pw - 120, rh - 640, j["u"], j["v"], sB)
    draw_front(VJ)
    clip_end()
    add(f'<line x1="{px_ + 10}" y1="{ry + 552}" x2="{px_ + pw - 10}" y2="{ry + 552}" stroke="{LINE}"/>')
    text(px_ + 16, ry + 586, "Jack plate", 15, INK, weight=600)
    text(px_ + 16, ry + 606, f"football, {mm(j['l'])} x {mm(j['w'])}, at {mm(j['angle_deg'])}°", 13, MUTED)
    text(px_ + 16, ry + 624, "in a 4.5 deep dish, 2 screws", 13, MUTED)
    para(px_ + 16, ry + rh - 70, "Saddles 11.1 wide, each with two height screws and an intonation screw "
         "to the rear lip. Arm socket on the right, white tip.", 80)

    # ===== row 3: sections, finish, options ==============================================
    ry3, rh3 = ry + rh + 24, 800
    px_, pw = 40, 760
    panel(px_, ry3, pw, rh3, "5 · Sections through the contours, 1x")
    for i, (v, kind, lab) in enumerate(((140.0, "A", "A-A at 140 from the tail: forearm contour"),
                                         (340.0, "B", "B-B at 340: belly contour"))):
        pts, umin, umax, df, db = section_pts(v, kind)
        ox, oy = px_ + 70 + (-umin) * 2, ry3 + 150 + i * 300
        q = [(ox + u * 2, oy - z * 2) for u, z in pts]
        add('<path d="M' + " L".join(f"{x:.1f},{y:.1f}" for x, y in q) + f' Z" fill="{COL["body"]}" '
            f'stroke="{INK}" stroke-width="1.2"/>')
        text(px_ + 16, oy - 40, lab, 14, INK, weight=600)
        text(px_ + 16, oy + 130, f"bass side left · width {mm(umax - umin)} · "
             f"{'forearm ' + mm(df) + ' deep' if kind == 'A' else 'belly ' + mm(db) + ' deep'} · edges R {mm(G['edge_r'])}",
             13, MUTED)
        dim_v(ox + umax * 2 + 22, oy, oy + G["body_t"] * 2, f"{mm(G['body_t'])}", left=False)
        if kind == "A":
            w_ = G["forearm"]["width"]
            add(f'<line x1="{ox + umin * 2:.1f}" y1="{oy:.1f}" x2="{ox + (umin + w_) * 2:.1f}" y2="{oy:.1f}" '
                f'stroke="{COL["hidden"]}" stroke-width="1" stroke-dasharray="4 3"/>')
            dim_v(ox + umin * 2 - 14, oy, oy + df * 2, f"{mm(df)}")
            dim_h(ox + umin * 2, ox + (umin + w_) * 2, oy - 14, f"{mm(w_)} bevel", above=True)
        else:
            w_ = G["belly"]["width"]
            yb_ = oy + G["body_t"] * 2
            add(f'<line x1="{ox + umin * 2:.1f}" y1="{yb_:.1f}" x2="{ox + (umin + w_) * 2:.1f}" y2="{yb_:.1f}" '
                f'stroke="{COL["hidden"]}" stroke-width="1" stroke-dasharray="4 3"/>')
            dim_v(ox + umin * 2 - 14, yb_ - db * 2, yb_, f"{mm(db)}")
            dim_h(ox + umin * 2, ox + (umin + w_) * 2, yb_ + 14, f"{mm(w_)} belly cut", above=False)
    # finish and materials
    px_, pw = 820, 900
    panel(px_, ry3, pw, rh3, "6 · Finish and materials", "render values; the lite model bakes them into one atlas")
    mats = [
        ("Olympic White, aged A", "#efe9d8", "0.22, clear coat", "body: lacquer, a year old in 1969"),
        ("edge wear", COL["primer"], "0.55", "primer through on horn tips and forearm edge"),
        ("maple board, lacquer", "#e2bb76", "0.30", "amber; play wear 0.45 at frets 1 to 7"),
        ("maple neck back", "#e3bf80", "0.35", "gloss rubbed to satin by the hand"),
        ("dot inlays", "#1d1b18", "0.40", "black, 6.35"),
        ("frets, nickel silver", "#c4c2ba", "0.28, metal", "vintage wire"),
        ("hardware, chrome/nickel", "#cfd2d6", "0.15 to 0.25, metal", "bridge, saddles, tuners, plates, screws"),
        ("guard, top ply", "#f2efe6", "0.38", "3-ply W/B/W, black ply #1f1e1c"),
        ("covers, knobs, switch tip", "#eae3cf", "0.45", "aged white plastic"),
        ("nut", "#eee6d2", "0.50", "bone"),
        ("strings plain / wound", "#b9bcbf", "0.25 / 0.35, metal", "wound #a8a294"),
    ]
    for i, (lab, hx, rough, note) in enumerate(mats):
        y = ry3 + 76 + i * 35
        add(f'<rect x="{px_ + 16}" y="{y}" width="46" height="30" rx="3" fill="{hx}" stroke="{INK}" stroke-width="0.8"/>')
        text(px_ + 74, y + 13, lab, 14, INK, weight=600)
        text(px_ + 74, y + 29, f"{hx} · roughness {rough}", 12, MUTED, family="Menlo, monospace")
        text(px_ + 420, y + 21, note, 12, MUTED)
    # aging options
    oy = ry3 + 488
    text(px_ + 16, oy, "Ageing, choose one (owner)", 15, INK, weight=600)
    for i, (lab, fill, lvl, sub) in enumerate((("A · a year old, Woodstock 1969", COL["body"], 1, "recommended: 'aged a little'"),
                                               ("B · well played, early 1970s", COL["body_b"], 2, "more yellow, more edge wear"),
                                               ("C · as in the museum today", COL["body_c"], 3, "cream, worn to primer and wood"))):
        Vm = View(px_ + 130 + i * 290, oy + 250, 0.5)
        clip_begin(px_ + 10 + i * 290, oy + 12, 280, 250)
        Vm.path(BODY, fill, INK, 1.0)
        _wear_front(Vm, lvl)
        Vm.path(GUARD, COL["guard"] if lvl < 3 else "#ece3cc", INK, 0.8)
        Vm.path(NECK, COL["maple"] if lvl < 3 else "#d4a45c", INK, 0.8)
        clip_end()
        text(px_ + 30 + i * 290, oy + 280, lab, 13, INK, weight=600 if i == 0 else 400)
        text(px_ + 30 + i * 290, oy + 296, sub, 12, MUTED)
    # mirroring options and left-out strip
    px_, pw = 1740, 620
    panel(px_, ry3, pw, rh3, "7 · Left-handed: how it hangs", "choose one (owner)")
    sm = 0.42
    for i, (lab, sub, mg) in enumerate((("A · exact", "as it really hangs", False),
                                        ("B · mirrored", "what MESHES.md says", True))):
        cxm = px_ + 100 + i * 170
        Vm = View(cxm, ry3 + 600, sm)
        mini(Vm, mirror_geo=mg, thick_right=not mg)
        text(cxm - 64, ry3 + 626, lab, 14, INK, weight=600)
        text(cxm - 64, ry3 + 644, sub, 12, MUTED)
    cxm, cym, sm = px_ + 470, ry3 + 300, 0.27
    add(f'<g transform="rotate(-90 {cxm:.1f} {cym:.1f})">')
    mini(View(cxm, cym + 500 * sm, sm))
    add("</g>")
    text(cxm - 120, ry3 + 400, "C · lifted", 14, INK, weight=600)
    text(cxm - 120, ry3 + 418, "a quarter turn to his playing view:", 12, MUTED)
    text(cxm - 120, ry3 + 434, "controls on top, tuners below", 12, MUTED)
    para(px_ + 16, ry3 + 690, "A is the real guitar on a wall: right-handed body, strings reversed (thick strings on "
         "the right). B is a true left-handed build, which this guitar never was. C costs nothing: the same model "
         "turned a quarter turn when lifted, controls on top, as he held it.", 84, 12)
    text(px_ + 16, ry3 + 770, "Recommended: A on the wall, C when lifted.", 14, INK, weight=600)

    # ===== row 4: left out, key dimensions, web budget ==================================
    ry4, rh4 = ry3 + rh3 + 24, 700
    px_, pw = 40, 560
    panel(px_, ry4, pw, rh4, "8 · Left out", "printing on the real guitar, shown as hatched areas only")
    for i, (lab, dec) in enumerate((("a real face, printed", True), ("ours", False))):
        Vh = View(px_ + 160 + i * 250, ry4 + 430 + VN * 1.6, 1.6)
        k = G["tuner_key"]
        for (pa, pv), (ka, _) in zip(posts(), keys()):
            Vh.line((pa, pv), (ka, pv), COL["chrome_d"], 2)
            Vh.path(shape(ellipse(k["w"], k["h"]), (ka, pv)), COL["chrome"], INK, 0.8)
        Vh.path(HEAD, COL["head"], INK, 1.1)
        Vh.path([(-21, VN), (-21, VN + 4.7), (21, VN + 4.7), (21, VN)], COL["nut"], INK, 0.8)
        for pa, pv in posts():
            Vh.circle(pa, pv, 4.5, COL["chrome"], INK, 0.7)
            Vh.circle(pa, pv, 3.15, COL["chrome_d"], INK, 0.7)
        if dec:
            _decal_boxes(Vh)
        text(px_ + 80 + i * 250, ry4 + 462, lab, 14, INK, weight=600)
    y = ry4 + 500
    for ln in ("Left out: the black headstock logo and model name,",
               "patent text, the neck-plate stamp and serial,",
               "tuner and saddle stamps, any brand on the pickups.",
               "Kept: the shapes, hardware, colours and wear.",
               "Ours shows bare lacquered maple, posts and the",
               "string tree, nothing printed.",
               "Owner: the cigarette burns near the tip are part",
               "of the real wear; off by default, add them?"):
        text(px_ + 16, y, ln, 13, MUTED)
        y += 19
    # key dimensions
    px_, pw = 620, 1080
    panel(px_, ry4, pw, rh4, "9 · Key dimensions and where they come from",
          "spec = published figure · measured = a real vintage guitar · reconstructed = our drawing from photos")
    rows = [
        ("Scale", "647.7 (25.5 in)", "spec", "Fender / retailer spec sheets; RetroFret 1966"),
        ("Frets, radius", "21 vintage, 184 (7.25 in)", "spec", "Custom Shop Woodstock tribute spec"),
        ("Nut width", "41.3 (1 5/8 in)", "measured", "RetroFret 1969; Custom Shop tribute 1.650 in"),
        ("Width at 12th", "52.0", "reconstructed", "typical vintage Fender, no source on this guitar"),
        ("Body, lower bout", f"{mm(BODY_W)}", "measured", "RetroFret 1966 12 5/8 in, 1969 12 3/4 in"),
        ("Body thickness", "44.5 (1.75 in)", "measured", "RetroFret 1966; same in spec sheets"),
        ("Body length", f"{mm(BODY_L)}", "spec", "sources give 18.1 to 18.75 in; 18.0 fits the photo"),
        ("Overall length", "994, 1005 with button", "measured", "RetroFret 1966: 39 1/4 in, 1969: 39 3/4 in"),
        ("Saddle line from tail", "138", "reconstructed", "MoPOP photo, scaled by the body; neck end checks"),
        ("Headstock", f"{mm(G['v_tip'] - VN)} x {mm(max(a for a, _ in HEAD) - min(a for a, _ in HEAD))}", "measured", "r3, small: owner's photo, rectified"),
        ("String spacing, bridge", "56.4 (2 7/32 in)", "spec", "Fender vintage bridge plate spec"),
        ("Pickguard", "3-ply W/B/W, 11 screws", "spec", "Fuzzfaced; vendor guard 279 x 228; ours 286 x 228"),
        ("Pickups from saddle line", "162 / 102 / 48, 10°", "reconstructed", "MoPOP photo; neck = 24th-fret node"),
        ("Controls", "vol, tone, tone, 3-way", "spec", "1968; the 5-way came in 1977"),
        ("Neck build", "2-piece maple, heel rod", "spec", "gearnews on the original: no skunk stripe"),
        ("Contours", "forearm 12, belly 14", "reconstructed", "late-60s are shallower than 1950s"),
        ("Strap button, short horn", "added by Hendrix", "spec", "Equipboard; MoPOP display"),
        ("String tree", "one butterfly", "spec", "Equipboard"),
        ("Body, guard, head outlines", "drawn", "reconstructed", "MoPOP photo silhouette fitted to the sizes, ±3"),
    ]
    cols = (px_ + 16, px_ + 230, px_ + 440, px_ + 570)
    y = ry4 + 92
    for c, h in zip(cols, ("part", "value, mm", "how sure", "source")):
        text(c, y, h, 13, MUTED, weight=600)
    y += 10
    colr = {"spec": "#3f6b3a", "measured": "#3f6b3a", "reconstructed": ACC}
    for r_ in rows:
        y += 26
        add(f'<line x1="{px_ + 12}" y1="{y - 18}" x2="{px_ + pw - 12}" y2="{y - 18}" stroke="{LINE}" stroke-width="0.7"/>')
        text(cols[0], y, r_[0], 13, INK)
        text(cols[1], y, r_[1], 13, INK, family="Menlo, monospace")
        text(cols[2], y, r_[2], 13, colr[r_[2]], weight=600)
        text(cols[3], y, r_[3], 12, MUTED)
    para(px_ + 16, y + 40, "The outlines (body, guard, headstock) are reconstructed to the published numbers, about "
         "±3 mm. To call them exact we need a measured 1:1 template of a late-60s body and large headstock, or a "
         "square-on photo of the real guitar with a known scale. Sources: NOTE.md beside this sheet.", 150, 13, INK)
    # web budget
    px_, pw = 1720, 640
    panel(px_, ry4, pw, rh4, "10 · Web budget (estimate)")
    rows = [("", "rich, renders", "lite, site"),
            ("body + contours", "18k", "2.2k"),
            ("neck, board, frets", "14k", "1.2k"),
            ("headstock, 6 tuners", "10k", "0.9k"),
            ("bridge, saddles, arm", "14k", "0.8k"),
            ("pickups, knobs, switch", "8k", "0.6k"),
            ("guard, plates, screws", "8k", "0.4k"),
            ("strings (own mesh)", "2.4k", "72"),
            ("triangles, total", "about 75k", "about 6k"),
            ("textures", "4K body colour,", "one 1024 atlas"),
            ("", "roughness, normal;", "+ 512 ORM,"),
            ("", "2K neck; 1K metal", "about 240 KB"),
            ("materials / draw calls", "8 / 10", "2 / 3"),
            ("meshes the code uses", "guitar_02, _body,", "same three"),
            ("", "_strings", "")]
    y = ry4 + 80
    for a, b, c in rows:
        y += 30
        w8 = 600 if a in ("", ) and b == "rich, renders" else 400
        text(px_ + 16, y, a, 13, INK, weight=600 if b == "rich, renders" else 400)
        text(px_ + 270, y, b, 13, INK, weight=w8, family=None)
        text(px_ + 460, y, c, 13, INK, weight=w8)
    para(px_ + 16, y + 40, "Lite: the contours, guard bevel and wear go into the normal and colour maps; tuners "
         "become simple caps; fret wire is a texture line on a flat board. Strings stay a separate mesh "
         "for the strum shimmer.", 82, 13, MUTED)

    add("</svg>")


def main():
    os.makedirs(OUT, exist_ok=True)
    build()
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>guitar_02 blueprint</title>"
            f"<style>html,body{{margin:0;background:{PAPER}}}svg{{display:block}}</style></head><body>"
            + "\n".join(out) + "</body></html>")
    hp = os.path.join(OUT, "guitar-02-blueprint.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    png = os.path.join(OUT, "guitar-02-blueprint.png")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={W_PX},{H_PX}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", hp, png)


if __name__ == "__main__":
    main()
