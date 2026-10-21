"""2D design sheet for the upright piano, drawn to scale from blender/lib/constants.py.

Plain Python (no Blender): writes an HTML page with one SVG, then renders it to a
PNG with the cached headless Chromium. Run from the repo root:

    python3 blender/design/piano_design_sheet.py

Output: video-local/footage/2026-10-22-piano-quality-test/piano-design-sheet.{html,png}
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib import constants as C  # noqa: E402
from lib.piano_layout import (keyboard, fallboard_profile, lid_profile, cheek_profile,  # noqa: E402
                              console_profile, sheet_line)

P, KT = C.PIANO, C.KT
OUT = os.path.join(C.FOOTAGE, "2026-10-22-piano-quality-test")
W_PX, H_PX = 2400, 1800
CHROME = os.path.expanduser("~/Library/Caches/ms-playwright/chromium_headless_shell-1223/"
                            "chrome-headless-shell-mac-arm64/chrome-headless-shell")

INK, ACC, MUTED, PAPER = "#1d1c1a", "#b5532a", "#6b675f", "#f6f3ec"
TECH = dict(case="#d9d4ca", recess="#c9c3b8", inset="#e4e0d7", white="#fbfaf6", black="#2a2826",
            felt=C.COL["felt_red"], brass=C.COL["brass"], cup="#55524d", paper="#ffffff",
            stroke=INK, sw=1.1)

out = []


def add(s):
    out.append(s)


def cm(m, nd=1):
    return f"{m * 100:.{nd}f}".rstrip("0").rstrip(".") + " cm"


class View:
    """World metres (u, v) to page pixels. v is up."""
    def __init__(self, ox, oy, s, u0=0.0):
        self.ox, self.oy, self.s, self.u0 = ox, oy, s, u0

    def p(self, u, v):
        return self.ox + (u - self.u0) * self.s * 1000, self.oy - v * self.s * 1000

    def poly(self, pts, fill, stroke=INK, sw=1.1, extra=""):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in (self.p(u, v) for u, v in pts))
        add(f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round" {extra}/>')

    def rect(self, u0, u1, v0, v1, fill, stroke=INK, sw=1.1, rx=0, extra=""):
        x0, y0 = self.p(min(u0, u1), max(v0, v1))
        x1, y1 = self.p(max(u0, u1), min(v0, v1))
        add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" '
            f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def line(self, a, b, stroke=INK, sw=1.1, extra=""):
        (x0, y0), (x1, y1) = self.p(*a), self.p(*b)
        add(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{stroke}" '
            f'stroke-width="{sw}" {extra}/>')

    def circle(self, u, v, r, fill, stroke=INK, sw=1.1):
        x, y = self.p(u, v)
        add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * self.s * 1000:.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')


def text(x, y, s, size=14, fill=INK, anchor="start", weight=400, rot=None, italic=False):
    tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot is not None else ""
    st = ' font-style="italic"' if italic else ""
    add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
        f'font-weight="{weight}"{st}{tr}>{s}</text>')


def dim_h(v, x0, x1, y, label, above=True):
    """Horizontal dimension between page x0 and x1 at page y."""
    add(f'<g stroke="{ACC}" stroke-width="1"><line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}"/>'
        f'<line x1="{x0:.1f}" y1="{y - 6:.1f}" x2="{x0:.1f}" y2="{y + 6:.1f}"/>'
        f'<line x1="{x1:.1f}" y1="{y - 6:.1f}" x2="{x1:.1f}" y2="{y + 6:.1f}"/></g>')
    text((x0 + x1) / 2, y - 6 if above else y + 17, label, 13, ACC, "middle")


def dim_v(x, y0, y1, label, left=True):
    add(f'<g stroke="{ACC}" stroke-width="1"><line x1="{x:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y1:.1f}"/>'
        f'<line x1="{x - 6:.1f}" y1="{y0:.1f}" x2="{x + 6:.1f}" y2="{y0:.1f}"/>'
        f'<line x1="{x - 6:.1f}" y1="{y1:.1f}" x2="{x + 6:.1f}" y2="{y1:.1f}"/></g>')
    cx, cy = (x - 7 if left else x + 16), (y0 + y1) / 2
    text(cx, cy, label, 13, ACC, "middle", rot=-90)


def leader(x0, y0, x1, y1, label, anchor="start"):
    add(f'<polyline points="{x0:.1f},{y0:.1f} {x1:.1f},{y1:.1f}" fill="none" stroke="{MUTED}" '
        f'stroke-width="0.9"/><circle cx="{x0:.1f}" cy="{y0:.1f}" r="2.2" fill="{MUTED}"/>')
    text(x1 + (4 if anchor == "start" else -4), y1 + 4, label, 13, MUTED, anchor)


def panel(x, y, w, h, title):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#d6d0c4" stroke-width="1"/>')
    text(x + 16, y + 30, title, 19, INK, weight=600)


# ---------------------------------------------------------------------------
# keys: positions shared by the views
# ---------------------------------------------------------------------------
KEYS = keyboard()


# ---------------------------------------------------------------------------
# 1. front elevation
# ---------------------------------------------------------------------------
def front(v, st, detail=True):
    hw, sd = P["width"] / 2, P["side_t"]
    case, sw = st["case"], st["sw"]
    stroke = st["stroke"]
    fg = P["floor_gap"]
    # floor cups and castors (behind the case bottom edge)
    for x, y in P["cups"]:
        if y > -0.3 and not detail:
            continue
        v.rect(x - 0.006, x + 0.006, P["cup_h"] - 0.002, fg + 0.006, st["brass"], stroke, sw * 0.8)
        v.rect(x - P["cup_r"], x + P["cup_r"], 0, P["cup_h"], st["cup"], stroke, sw, rx=2)
    # side panels, upper and lower panels
    for sx in (-1, 1):
        v.rect(sx * hw, sx * (hw - sd), fg, P["case_top"], case, stroke, sw)
    v.rect(-(hw - sd), hw - sd, P["panel_bottom"], P["case_top"] - P["crown_h"], st["recess"], stroke, sw)
    v.rect(-P["inset_half_w"], P["inset_half_w"], P["inset_bottom"], P["inset_top"], st["inset"], stroke, sw, rx=3)
    v.rect(-(hw - sd), hw - sd, P["toe_rail_top"], P["cheek_bottom"], st["recess"], stroke, sw)
    v.rect(-P["lower_inset_half_w"], P["lower_inset_half_w"], P["lower_inset_bottom"],
           P["lower_inset_top"], st["inset"], stroke, sw, rx=3)
    # crown moulding and lid
    cp = P["crown_proud"]
    v.rect(-(hw + cp), hw + cp, P["case_top"] - P["crown_h"], P["case_top"], case, stroke, sw, rx=3)
    lo = P["lid_over_side"]
    v.rect(-(hw + lo), hw + lo, P["case_top"], P["case_top"] + P["lid_t"], case, stroke, sw, rx=3)
    # music ledge
    v.rect(-P["ledge_half_w"], P["ledge_half_w"], P["ledge_z"], P["ledge_lip_top"], case, stroke, sw, rx=2)
    # fallboard, open: its inner face toward the player
    fz = [z for _, z in fallboard_profile(P["fall_open_deg"])]
    v.rect(-P["fall_half_w"], P["fall_half_w"], min(fz), max(fz), case, stroke, sw, rx=2)
    # felt strip behind the keys
    v.rect(-0.611, 0.611, KT - 0.004, KT + 0.024, st["felt"], stroke, sw * 0.6)
    # keys: black above the white key line, then the white key fronts
    for m, kind, xl, xr, _, _ in KEYS:
        if kind == "b":
            v.rect(xl, xr, KT, KT + P["black_up"], st["black"], stroke, sw * 0.6, rx=1)
    for m, kind, xl, xr, _, _ in KEYS:
        if kind == "w":
            v.rect(xl, xr, KT - P["white_h"], KT, st["white"], stroke, sw * 0.6, rx=0.6)
    # music sheet, leaning on the ledge and the lid edge
    (y0, z0), (y1, z1) = sheet_line()
    v.rect(-P["sheet_w"] / 2, P["sheet_w"] / 2, z0, z1, st["paper"], stroke, sw)
    if detail:
        sx0, sx1 = -P["sheet_w"] / 2, P["sheet_w"] / 2
        v.line((0, z0), (0, z1), "#cfc9bd", 1)
        for page in (-1, 1):
            for sys_i in range(5):
                top = z1 - 0.045 - sys_i * 0.048
                for li in range(5):
                    zz = top - li * 0.0035
                    a, b = (sx0 + 0.018, -0.012) if page < 0 else (0.012, sx1 - 0.018)
                    v.line((a, zz), (b, zz), "#b9b3a7", 0.6)
    # cheeks, key slip and lock
    for sx in (-1, 1):
        v.rect(sx * hw, sx * 0.6125, P["cheek_bottom"], P["cheek_top"], case, stroke, sw, rx=3)
    v.rect(-0.6125, 0.6125, P["cheek_bottom"], P["slip_top"], case, stroke, sw, rx=2)
    v.circle(0, KT - 0.045, 0.009, st["brass"], stroke, sw * 0.7)
    # consoles, toe rail, toe blocks
    for sx in (-1, 1):
        cx = sx * P["toe_x"]
        v.rect(cx - P["console_w"] / 2, cx + P["console_w"] / 2, P["toe_rail_top"], P["cheek_bottom"], case, stroke, sw)
    v.rect(-(hw - sd), hw - sd, fg, P["toe_rail_top"], case, stroke, sw)
    v.rect(-0.13, 0.13, 0.046, 0.066, st["black"], stroke, sw * 0.6, rx=2)
    for sx in (-1, 1):
        cx = sx * P["toe_x"]
        v.rect(cx - P["toe_w"] / 2, cx + P["toe_w"] / 2, fg, P["toe_rail_top"], case, stroke, sw, rx=4)
    # pedals (seen end-on)
    for x in P["pedal_x"]:
        v.rect(x - P["pedal_w_front"] / 2, x + P["pedal_w_front"] / 2, P["pedal_z"],
               P["pedal_z"] + P["pedal_t"], st["brass"], stroke, sw, rx=3)


# ---------------------------------------------------------------------------
# 2. side section at middle C (front to the left)
# ---------------------------------------------------------------------------
def side(v, st):
    sw, stroke = st["sw"], st["stroke"]
    faint = "#ebe7df"
    fg = P["floor_gap"]
    # beyond the cut: side panel, cheek, console, toe block, cups (faint)
    v.rect(-P["side_depth"], 0, fg, P["case_top"], faint, "#bfb9ad", 1)
    v.poly(cheek_profile(), faint, "#bfb9ad", 1)
    v.poly(console_profile(), faint, "#bfb9ad", 1)
    v.rect(P["toe_front_y"], P["toe_back_y"], fg, P["toe_rail_top"], faint, "#bfb9ad", 1, rx=4)
    for x, y in P["cups"][:1] + P["cups"][2:3]:
        v.rect(y - P["cup_r"], y + P["cup_r"], 0, P["cup_h"], st["cup"], stroke, sw, rx=2)
        v.circle(y, fg - 0.006, P["castor_r"], st["brass"], stroke, sw * 0.8)
    # inside, for the lid-open view
    v.line((-0.075, 0.26), (-0.072, 1.11), "#9a8f7a", 1.4, 'stroke-dasharray="5 4"')
    v.rect(-0.115, -0.080, 0.965, 0.995, "#efe7d4", "#9a8f7a", 1, rx=4, extra='stroke-dasharray="3 3"')
    # cut parts
    case = st["case"]
    v.rect(-P["back_t"], 0, fg, P["case_top"], case, stroke, sw)
    v.rect(P["panel_face_y"], P["panel_back_y"], P["panel_bottom"], P["case_top"] - P["crown_h"], case, stroke, sw)
    v.rect(P["panel_face_y"] - P["inset_proud"], P["panel_face_y"], P["inset_bottom"], P["inset_top"], case, stroke, sw)
    v.rect(-(P["side_depth"] + P["crown_proud"]), P["panel_face_y"], P["case_top"] - P["crown_h"], P["case_top"],
           case, stroke, sw, rx=3)
    lz, lt = P["ledge_z"], P["ledge_t"]
    v.poly([(P["panel_face_y"], lz), (P["ledge_front_y"], lz), (P["ledge_front_y"], P["ledge_lip_top"]),
            (P["ledge_front_y"] + 0.012, P["ledge_lip_top"]), (P["ledge_front_y"] + 0.012, lz + lt),
            (P["panel_face_y"], lz + lt)], case, stroke, sw)
    (y0, z0), (y1, z1) = sheet_line()
    v.line((y0, z0), (y1, z1), INK, 2.4)
    # keys at middle C: white key and the C# behind it
    v.poly([(P["key_back_y"], KT - 0.010), (P["key_back_y"] - P["black_len"], KT - 0.010),
            (P["key_back_y"] - P["black_len"] + P["black_taper"], KT + P["black_up"]),
            (P["key_back_y"], KT + P["black_up"])], st["black"], stroke, sw * 0.8)
    v.rect(P["key_back_y"] - P["white_len"], P["key_back_y"], KT - P["white_h"], KT, st["white"], stroke, sw, rx=1)
    v.rect(-0.560, -0.395, KT - 0.028, KT - P["white_h"], "#4a4440", stroke, sw * 0.6)
    v.rect(-0.560, -0.360, P["cheek_bottom"], KT - 0.035, case, stroke, sw)
    v.rect(P["slip_front_y"], P["slip_back_y"], P["cheek_bottom"], P["slip_top"], case, stroke, sw, rx=2)
    v.rect(P["slip_back_y"], P["slip_back_y"] + 0.005, KT - 0.021, KT - 0.0135, st["felt"], stroke, sw * 0.5)
    v.rect(-0.405, -0.399, KT - P["white_h"], KT + 0.024, st["felt"], stroke, sw * 0.5)
    # fallboard: open (solid) and closed (dashed)
    v.poly(fallboard_profile(0), "none", MUTED, 1.1, 'stroke-dasharray="5 4"')
    v.poly(fallboard_profile(P["fall_open_deg"]), case, stroke, sw)
    v.circle(P["fall_pivot_y"], P["fall_pivot_z"], 0.004, ACC, ACC, 1)
    # lower case
    v.rect(P["lower_face_y"], P["lower_back_y"], P["toe_rail_top"], P["cheek_bottom"], case, stroke, sw)
    v.rect(P["lower_face_y"] - 0.006, P["lower_face_y"], P["lower_inset_bottom"], P["lower_inset_top"], case, stroke, sw)
    v.rect(P["toe_rail_front_y"], -0.300, fg, P["toe_rail_top"], case, stroke, sw)
    v.poly([(P["pedal_back_y"], P["pedal_z"]), (P["pedal_front_y"] + 0.01, P["pedal_z"] - 0.004),
            (P["pedal_front_y"], P["pedal_z"] + 0.002), (P["pedal_front_y"] + 0.006, P["pedal_z"] + P["pedal_t"] - 0.002),
            (P["pedal_back_y"], P["pedal_z"] + P["pedal_t"])], st["brass"], stroke, sw)
    # lid: closed (solid), open (dashed), hinge
    closed, (hy, hz) = lid_profile(0)
    v.poly(closed, case, stroke, sw)
    opened, _ = lid_profile(P["lid_open_deg"])
    v.poly(opened, "none", MUTED, 1.1, 'stroke-dasharray="5 4"')
    v.circle(hy, hz, P["hinge_r"] * 1.6, st["brass"], stroke, 1)
    # opening arcs
    for (py, pz), r, a0, a1 in (((hy, hz), P["side_depth"] + P["lid_over_front"] + P["lid_over_back"], 180, 180 - P["lid_open_deg"]),
                                ((P["fall_pivot_y"], P["fall_pivot_z"]), P["fall_len"], 180, 180 - P["fall_open_deg"])):
        x0, y0p = v.p(py + r * math.cos(math.radians(a0)), pz + r * math.sin(math.radians(a0)))
        x1, y1p = v.p(py + r * math.cos(math.radians(a1)), pz + r * math.sin(math.radians(a1)))
        rp = r * v.s * 1000
        add(f'<path d="M{x0:.1f},{y0p:.1f} A{rp:.1f},{rp:.1f} 0 0 1 {x1:.1f},{y1p:.1f}" fill="none" '
            f'stroke="{ACC}" stroke-width="1" stroke-dasharray="2 4" marker-end="url(#arr)"/>')


# ---------------------------------------------------------------------------
# 3. keyboard
# ---------------------------------------------------------------------------
def plan_keys(ox, oy, s, lo, hi, labels=False, sw=1.0):
    """Keys lo..hi (MIDI) in plan view: back of the keys at page y = oy, front below."""
    sel = [k for k in KEYS if lo <= k[0] <= hi]
    xmin = min(k[2] for k in sel if k[1] == "w") - P["white_gap"] / 2
    X = lambda x: ox + (x - xmin) * s * 1000
    Y = lambda d: oy + d * s * 1000                       # d: distance from the back, metres
    nb = P["black_len"] + P["white_gap"]
    for m, kind, xl, xr, bl, br in sel:
        if kind != "w":
            continue
        pts = [(bl, 0), (br, 0), (br, nb), (xr, nb), (xr, P["white_len"]), (xl, P["white_len"]), (xl, nb), (bl, nb)]
        d = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in pts)
        add(f'<polygon points="{d}" fill="{TECH["white"]}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
        if labels:
            text((X(xl) + X(xr)) / 2, Y(P["white_len"]) - 12, C.NOTE_NAMES[m % 12].upper(), 15, MUTED, "middle")
    for m, kind, xl, xr, _, _ in sel:
        if kind != "b":
            continue
        add(f'<rect x="{X(xl):.1f}" y="{Y(0):.1f}" width="{(xr - xl) * s * 1000:.1f}" '
            f'height="{P["black_len"] * s * 1000:.1f}" fill="{TECH["black"]}" stroke="{INK}" stroke-width="{sw}" rx="{s * 1.2:.1f}"/>')
        if labels:
            inset = (P["black_w"] - P["black_top_w"]) / 2
            add(f'<rect x="{X(xl + inset):.1f}" y="{Y(0):.1f}" width="{P["black_top_w"] * s * 1000:.1f}" '
                f'height="{(P["black_len"] - P["black_taper"]) * s * 1000:.1f}" fill="#3d3a37" stroke="#77716a" '
                f'stroke-width="0.8" rx="{s:.1f}"/>')
            text((X(xl) + X(xr)) / 2, Y(P["black_len"]) - 14, C.NOTE_NAMES[m % 12].upper().replace("S", "♯"),
                 12, "#e9e4da", "middle")
    return X, Y


# ---------------------------------------------------------------------------
# page
# ---------------------------------------------------------------------------
def build():
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_PX}" height="{H_PX}" viewBox="0 0 {W_PX} {H_PX}" '
        f'font-family="-apple-system, Helvetica Neue, Arial, sans-serif">')
    add('<defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{ACC}"/></marker>'
        '<linearGradient id="gloss" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".16"/>'
        '<stop offset=".35" stop-color="#fff" stop-opacity="0"/><stop offset=".62" stop-color="#9fb8e8" stop-opacity=".10"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="walnut" x1="0" y1="0" x2="1" y2="0.15">'
        f'<stop offset="0" stop-color="{C.COL["walnut_dark"]}"/><stop offset=".18" stop-color="{C.COL["walnut_mid"]}"/>'
        f'<stop offset=".33" stop-color="#3a2214"/><stop offset=".52" stop-color="{C.COL["walnut_light"]}"/>'
        f'<stop offset=".7" stop-color="{C.COL["walnut_mid"]}"/><stop offset=".86" stop-color="#341e12"/>'
        f'<stop offset="1" stop-color="{C.COL["walnut_mid"]}"/></linearGradient>'
        '<pattern id="grain" width="9" height="140" patternUnits="userSpaceOnUse">'
        '<path d="M2,0 C3,40 1,90 2.5,140 M6,0 C7,50 5,100 6.5,140" stroke="#1e1008" stroke-opacity=".28" stroke-width=".7" fill="none"/></pattern>'
        '</defs>')
    add(f'<rect width="{W_PX}" height="{H_PX}" fill="{PAPER}"/>')
    text(48, 58, "Upright piano · design sheet", 32, INK, weight=650)
    text(48, 86, f"obj_piano · drawn to scale from blender/lib/constants.py · dimensions in cm · "
         f"{cm(P['width'])} wide, {cm(P['case_top'] + P['lid_t'])} high, {cm(-P['toe_front_y'])} deep · 88 keys, A0 to C8",
         16, MUTED)
    text(W_PX - 48, 58, "2026-10-22 · for the owner's review, before 3D modelling", 15, MUTED, "end")

    # 1. front ---------------------------------------------------------------
    panel(40, 110, 900, 860, "1 · Front elevation (fallboard open, lid closed)")
    s = 0.48
    vf = View(490, 905, s)
    vf.line((-0.9, 0), (0.9, 0), "#8d8678", 1.2)
    front(vf, TECH)
    hw = P["width"] / 2
    x0, _ = vf.p(-hw, 0)
    x1, _ = vf.p(hw, 0)
    dim_h(0, x0, x1, 932, f"{cm(P['width'])} case", above=False)
    lx0, _ = vf.p(-(hw + P["lid_over_side"]), 0)
    lx1, _ = vf.p(hw + P["lid_over_side"], 0)
    _, ly = vf.p(0, P["case_top"] + P["lid_t"])
    dim_h(0, lx0, lx1, ly - 70, f"{cm(P['width'] + 2 * P['lid_over_side'])} lid", above=True)
    kx0, _ = vf.p(KEYS[0][2], 0)
    kx1, _ = vf.p(KEYS[-1][3], 0)
    _, ky = vf.p(0, KT)
    dim_h(0, kx0, kx1, ky - 52, f"{cm(52 * P['white_pitch'])} keyboard, 88 keys", above=True)
    _, y0 = vf.p(0, 0)
    _, y1 = vf.p(0, P["case_top"] + P["lid_t"])
    dim_v(95, y0, y1, f"{cm(P['case_top'] + P['lid_t'])} to lid top")
    dim_v(128, y0, ky, f"{cm(KT)} key top")
    _, yl = vf.p(0, P["ledge_z"] + P["ledge_t"])
    cx1, _ = vf.p(hw, 0)
    dim_v(cx1 + 22, y0, yl, f"{cm(P['ledge_z'] + P['ledge_t'])} music rest", left=False)
    ccx, ccy = vf.p(hw - 0.08, P["cheek_top"] - 0.03)
    leader(ccx, ccy, cx1 + 4, ccy - 120, "")
    text(cx1 - 160, ccy - 126, "key cheek, curved (see 4a)", 13, MUTED)
    px, py = vf.p(P["pedal_x"][2], P["pedal_z"] + 0.006)
    leader(px, py, px + 120, py - 90, f"3 brass pedals, {cm(P['pedal_x'][2])} apart")
    tx, ty = vf.p(P["toe_x"], P["toe_rail_top"] - 0.03)
    leader(tx, ty, tx - 40, ty - 130, "")
    text(tx - 230, ty - 134, "console (leg) on a toe block", 13, MUTED)
    sx_, sy_ = vf.p(0.16, 1.17)
    leader(sx_, sy_, sx_ + 70, sy_ - 64, "music on the rest (About, on the site)")
    fx, fy = vf.p(-0.45, KT + 0.12)
    tx_, ty_ = vf.p(-0.60, P["inset_bottom"] + 0.03)
    leader(fx, fy, tx_, ty_, "fallboard, open (its inner face)")
    mx, my = vf.p(-0.55, P["case_top"] - 0.015)
    leader(mx, my, mx - 40, my - 34, "top moulding (4b)")

    # 2. side section ------------------------------------------------------------
    panel(960, 110, 500, 860, "2 · Side section at middle C")
    vs = View(1040, 905, s, u0=-0.625)
    vs.line((-0.7, 0), (0.06, 0), "#8d8678", 1.2)
    side(vs, TECH)
    xa, _ = vs.p(P["toe_front_y"], 0)
    xb, _ = vs.p(0, 0)
    dim_h(0, xa, xb, 932, f"{cm(-P['toe_front_y'])} deep", above=False)
    xs, _ = vs.p(-P["side_depth"], 0)
    _, ytop = vs.p(0, P["case_top"])
    dim_h(0, xs, xb, ytop + 64, f"{cm(P['side_depth'])} case", above=True)
    kx_a, _ = vs.p(P["key_back_y"] - P["white_len"], 0)
    kx_b, _ = vs.p(P["key_back_y"], 0)
    _, kyy = vs.p(0, KT)
    dim_h(0, kx_a, kx_b, kyy + 82, f"{cm(P['white_len'])} key", above=False)
    hx, hy = vs.p(P["lid_over_back"], P["case_top"] + P["lid_t"])
    leader(hx, hy, hx + 40, hy - 60, "", "end")
    text(hx + 44, hy - 76, "lid hinge", 13, MUTED, "end")
    text(hx + 44, hy - 60, "(3 brass, 4c)", 13, MUTED, "end")
    op, _ = lid_profile(P["lid_open_deg"])
    ox_, oy_ = vs.p(*op[0])
    text(ox_ - 110, oy_ + 70, f"lid opens about {P['lid_open_deg']}°", 13, ACC, "end")
    text(ox_ - 110, oy_ + 86, "(angle set in code)", 13, ACC, "end")
    fpx, fpy = vs.p(P["fall_pivot_y"], P["fall_pivot_z"])
    text(fpx + 80, fpy + 40, f"fallboard opens {P['fall_open_deg']}°", 13, ACC)
    text(fpx + 80, fpy + 56, "about its back edge", 13, ACC)
    leader(fpx + 2, fpy + 2, fpx + 76, fpy + 78, "fallboard hinge")
    ix, iy = vs.p(-0.075, 0.55)
    leader(ix, iy, ix + 50, iy + 40, "strings", "start")
    hx2, hy2 = vs.p(-0.10, 0.98)
    leader(hx2, hy2, hx2 + 60, hy2 + 40, "hammers")
    text(1450, 162, "faint = beyond the cut", 12, MUTED, "end")
    text(1450, 178, "dashed = fallboard closed,", 12, MUTED, "end")
    text(1450, 194, "lid open", 12, MUTED, "end")

    # 3. keyboard -----------------------------------------------------------------
    panel(1480, 110, 880, 860, "3 · Keyboard: one octave, then all 88")
    so = 2.8
    X, Y = plan_keys(1560, 190, so, 60, 71, labels=True, sw=1.1)
    c4 = [k for k in KEYS if k[0] == 60][0]
    d4 = [k for k in KEYS if k[0] == 62][0]
    cs4 = [k for k in KEYS if k[0] == 61][0]
    dim_h(0, X(c4[2] - P["white_gap"] / 2), X(c4[3] + P["white_gap"] / 2), 176,
          f"{cm(P['white_pitch'], 2)} pitch")
    b4 = [k for k in KEYS if k[0] == 71][0]
    xr = X(b4[3]) + 30
    dim_v(xr, Y(0), Y(P["white_len"]), f"{cm(P['white_len'])} white", left=False)
    dim_v(xr + 46, Y(0), Y(P["black_len"]), f"{cm(P['black_len'])} black", left=False)
    dim_h(0, X(cs4[2]), X(cs4[3]), Y(P["black_len"]) + 22, f"{cm(P['black_w'], 2)}", above=False)
    gx = X(d4[3]) + 1
    leader(gx, Y(0.13), gx + 44, Y(0.13) - 30, f"{P['white_gap'] * 1000:.1f} mm gap")
    text(1590, Y(P["white_len"]) + 60,
         f"White keys notched around the black keys, {P['white_gap'] * 1000:.1f} mm gap. "
         f"Black keys taper from {cm(P['black_w'], 2)} to {cm(P['black_top_w'], 2)} on top,", 14, INK)
    text(1590, Y(P["white_len"]) + 80,
         f"stand {cm(P['black_up'], 2)} above the white keys, and their fronts slope back {cm(P['black_taper'], 1)}. "
         f"Black keys sit on the real offsets", 14, INK)
    text(1590, Y(P["white_len"]) + 100, "(C♯ and D♯ split C to E in five; F♯, G♯, A♯ split F to B in seven).", 14, INK)
    text(1590, Y(P["white_len"]) + 120, "Each key pivots at its back end, centred on its width: "
         "piano_key_c4 rotates about local +X to dip.", 14, MUTED)
    sf = 0.70
    X2, Y2 = plan_keys(1497, 766, sf, C.MIDI_A0, C.MIDI_C8, sw=0.5)
    dim_h(0, X2(KEYS[0][2] - P["white_gap"] / 2), X2(KEYS[-1][3] + P["white_gap"] / 2), 750,
          f"{cm(52 * P['white_pitch'])}: 52 white, 36 black")
    for m, lab in ((21, "A0"), (60, "C4, middle C"), (108, "C8")):
        k = [k for k in KEYS if k[0] == m][0]
        xm = X2((k[2] + k[3]) / 2)
        add(f'<line x1="{xm:.1f}" y1="{Y2(P["white_len"]) + 2:.1f}" x2="{xm:.1f}" y2="{Y2(P["white_len"]) + 16:.1f}" stroke="{ACC}"/>')
        text(xm, Y2(P["white_len"]) + 32, lab, 14, ACC, "middle" if m == 60 else ("start" if m == 21 else "end"))
    text(1497, 940, "Names: piano_key_a0 … piano_key_c8, sharps written s (piano_key_cs4). All 88 separate.", 13, MUTED)

    # 4. details --------------------------------------------------------------------
    by, bh, bw = 990, 770, 302
    titles = ["4a · Key cheek curve", "4b · Top moulding", "4c · Lid hinge", "4d · Castor in floor cup", "4e · Pedal"]
    for i, t in enumerate(titles):
        panel(40 + i * (bw + 10), by, bw, bh, t)
    # 4a cheek: side profile
    va = View(80, by + 330, 1.25, u0=-0.60)
    va.line((-0.60, P["cheek_bottom"] - 0.01), (-0.38, P["cheek_bottom"] - 0.01), "none", 0)
    vz = View(80, by + 330 + (P["cheek_bottom"]) * 1250, 1.25, u0=-0.60)
    vz.poly(cheek_profile(), TECH["case"], INK, 1.2)
    vz.rect(-0.405, -0.405 + 0.0, KT, KT, "none")
    vz.rect(P["key_back_y"] - P["white_len"], P["key_back_y"], KT - P["white_h"], KT, TECH["white"], "#8d8678", 0.8,
            extra='stroke-dasharray="3 3" fill-opacity=".6"')
    a_ = P["cheek_curve_y"] - P["cheek_front_y"]
    b_ = P["cheek_top"] - P["cheek_nose"]
    xq0, yq0 = vz.p(P["cheek_front_y"], P["cheek_bottom"])
    xq1, yq1 = vz.p(P["cheek_back_y"], P["cheek_bottom"])
    dim_h(0, xq0, xq1, yq0 + 26, cm(P["cheek_back_y"] - P["cheek_front_y"]) + " long", above=False)
    xt, yt = vz.p(P["cheek_back_y"], P["cheek_top"])
    dim_v(xt + 18, yq0, yt, cm(P["cheek_top"] - P["cheek_bottom"]), left=False)
    text(56, by + 440, f"Quarter ellipse, {cm(a_)} by {cm(b_)},", 14)
    text(56, by + 460, "from the top of the arm down to a", 14)
    text(56, by + 480, f"rounded nose {cm(P['cheek_nose'] - KT)} above the keys.", 14)
    text(56, by + 510, f"Arm width {cm(P['width'] / 2 - 0.6125)} each side,", 14)
    text(56, by + 530, "flush with the side panel.", 14)
    text(56, by + 560, "Every edge light can catch gets a", 14, MUTED)
    text(56, by + 580, "3 to 8 mm rounded bevel, never a", 14, MUTED)
    text(56, by + 600, "sharp box edge.", 14, MUTED)
    text(56, by + 640, "Dashed: the white key it guards.", 13, MUTED)
    # 4b moulding: section through the front top corner
    x0b = 40 + bw + 10
    zt = P["case_top"]
    add(f'<clipPath id="c4b"><rect x="{x0b + 1}" y="{by + 40}" width="{bw - 2}" height="380"/></clipPath><g clip-path="url(#c4b)">')
    vb2 = View(x0b + 70, by + 330 + (zt - 0.04) * 3000, 3.0, u0=-0.425)
    front_y = -(P["side_depth"] + P["lid_over_front"])
    vb2.rect(P["panel_face_y"], P["panel_face_y"] + 0.2, zt - 0.08, zt - P["crown_h"], TECH["case"], INK, 1.2)
    vb2.rect(-(P["side_depth"] + P["crown_proud"]), P["panel_face_y"] + 0.2, zt - P["crown_h"], zt, TECH["case"], INK, 1.2, rx=24)
    vb2.rect(front_y, P["panel_face_y"] + 0.2, zt, zt + P["lid_t"], TECH["case"], INK, 1.2, rx=18)
    xl0, yl0 = vb2.p(front_y, zt + P["lid_t"])
    xl1, yl1 = vb2.p(front_y, zt)
    dim_v(xl0 - 18, yl1, yl0, cm(P["lid_t"]))
    xc0, yc0 = vb2.p(-(P["side_depth"] + P["crown_proud"]), zt - P["crown_h"])
    xc1, yc1 = vb2.p(0, zt)
    dim_v(xc0 - 18, yc0, yc1, cm(P["crown_h"]))
    add("</g>")
    text(x0b + 200, by + 400, "upper front panel", 12, MUTED, "middle")
    text(x0b + 20, by + 470, "Lid: 2.2 cm board, front and side", 14)
    text(x0b + 20, by + 490, "edges rounded on an 8 mm radius,", 14)
    text(x0b + 20, by + 510, f"overhangs {cm(P['lid_over_front'])} at the front.", 14)
    text(x0b + 20, by + 540, f"Under it a {cm(P['crown_h'])} moulding, proud", 14)
    text(x0b + 20, by + 560, f"by {cm(P['crown_proud'])}, rounded below: two", 14)
    text(x0b + 20, by + 580, "highlights instead of one hard edge.", 14)
    text(x0b + 20, by + 620, "Upper and lower front panels carry a", 14, MUTED)
    text(x0b + 20, by + 640, f"raised field, {cm(P['inset_proud'])} proud, rounded,", 14, MUTED)
    text(x0b + 20, by + 660, "so the lacquer has edges to light.", 14, MUTED)
    # 4c hinge: seen from behind
    x0c = 40 + 2 * (bw + 10)
    cxh, cyh = x0c + bw / 2, by + 200
    k = 4.0
    L = P["hinge_len"] * 1000 * k
    r = P["hinge_r"] * 1000 * k
    add(f'<rect x="{cxh - 130}" y="{cyh - 70}" width="260" height="60" fill="{TECH["case"]}" stroke="{INK}" stroke-width="1.2"/>')
    add(f'<rect x="{cxh - 130}" y="{cyh - 10}" width="260" height="120" fill="{TECH["recess"]}" stroke="{INK}" stroke-width="1.2"/>')
    add(f'<rect x="{cxh - L / 2}" y="{cyh + 4}" width="{L}" height="{30 * k / 1.5}" fill="{TECH["brass"]}" stroke="{INK}" stroke-width="1"/>')
    for i in range(5):
        seg = L / 5
        add(f'<rect x="{cxh - L / 2 + i * seg + 1}" y="{cyh - r}" width="{seg - 2}" height="{2 * r}" rx="{r}" '
            f'fill="{TECH["brass"]}" stroke="{INK}" stroke-width="1"/>')
    for sx in (-0.35, 0, 0.35):
        for sy in (22, 58):
            add(f'<circle cx="{cxh + sx * L}" cy="{cyh + sy}" r="3.4" fill="#e9d6a6" stroke="{INK}" stroke-width=".8"/>')
    text(cxh, cyh - 80, "lid", 13, MUTED, "middle")
    text(cxh, cyh + 128, "back of the case", 13, MUTED, "middle")
    dim_h(0, cxh - L / 2, cxh + L / 2, cyh + 150, cm(P["hinge_len"]), above=False)
    text(x0c + 20, by + 440, "Three brass butt hinges along the", 14)
    text(x0c + 20, by + 460, "back top edge, at −55, 0 and +55 cm.", 14)
    text(x0c + 20, by + 480, f"Knuckle {cm(2 * P['hinge_r'], 2)} across, 5 segments,", 14)
    text(x0c + 20, by + 500, "slotted screws in the leaf.", 14)
    text(x0c + 20, by + 530, "The hinge line is piano_lid's pivot.", 14, MUTED)
    text(x0c + 20, by + 550, "Brass stays on the case, not the lid,", 14, MUTED)
    text(x0c + 20, by + 570, "so the lid keeps one material.", 14, MUTED)
    # 4d castor and cup, front view
    x0d = 40 + 3 * (bw + 10)
    vd = View(x0d + bw / 2, by + 330, 3.2)
    vd.line((-0.05, 0), (0.05, 0), "#8d8678", 1.2)
    vd.rect(-P["toe_w"] / 2, P["toe_w"] / 2, P["floor_gap"], P["floor_gap"] + 0.05, TECH["case"], INK, 1.2, rx=10)
    vd.rect(-0.007, 0.007, P["cup_h"] - 0.004, P["floor_gap"] + 0.008, TECH["brass"], INK, 1)
    vd.rect(-0.012, 0.012, P["floor_gap"] - 0.003, P["floor_gap"] + 0.002, "#9c8a62", INK, 1, rx=2)
    vd.rect(-P["cup_r"], P["cup_r"], 0, P["cup_h"], TECH["cup"], INK, 1.2, rx=6)
    vd.rect(-P["cup_r"] + 0.008, P["cup_r"] - 0.008, P["cup_h"] - 0.004, P["cup_h"], "#3b3935", INK, 0.8)
    xa0, ya0 = vd.p(-P["cup_r"], 0)
    xa1, _ = vd.p(P["cup_r"], 0)
    dim_h(0, xa0, xa1, ya0 + 26, f"Ø {cm(2 * P['cup_r'])}", above=False)
    _, yg = vd.p(0, P["floor_gap"])
    dim_v(xa1 + 22, ya0, yg, cm(P["floor_gap"]), left=False)
    text(x0d + 20, by + 440, "The case stands on four brass", 14)
    text(x0d + 20, by + 460, "castors in dark rubber floor cups,", 14)
    text(x0d + 20, by + 480, "two under the toe blocks, two", 14)
    text(x0d + 20, by + 500, "under the back corners.", 14)
    text(x0d + 20, by + 530, f"Case bottom {cm(P['floor_gap'])} off the floor:", 14, MUTED)
    text(x0d + 20, by + 550, "a thin dark gap with a glint of", 14, MUTED)
    text(x0d + 20, by + 570, "brass reads as a real, heavy", 14, MUTED)
    text(x0d + 20, by + 590, "instrument standing on wood.", 14, MUTED)
    # 4e pedal, plan
    x0e = 40 + 4 * (bw + 10)
    ke = 2.2
    cx_e, y_back = x0e + bw / 2, by + 90
    L = (P["pedal_back_y"] - P["pedal_front_y"]) * 1000 * ke
    wb, wf = P["pedal_w_back"] * 1000 * ke / 2, P["pedal_w_front"] * 1000 * ke / 2
    yf = y_back + L - wf
    add(f'<rect x="{x0e + 30}" y="{y_back - 40}" width="{bw - 60}" height="40" fill="{TECH["case"]}" stroke="{INK}" stroke-width="1.2"/>')
    add(f'<path d="M{cx_e - wb},{y_back} L{cx_e - wf},{yf} A{wf},{wf} 0 0 0 {cx_e + wf},{yf} L{cx_e + wb},{y_back} Z" '
        f'fill="{TECH["brass"]}" stroke="{INK}" stroke-width="1.2"/>')
    add(f'<path d="M{cx_e - wb + 4},{y_back + 6} L{cx_e - wf + 6},{yf}" stroke="#f3e2b4" stroke-width="2" fill="none" opacity=".8"/>')
    text(cx_e, y_back - 14, "toe rail", 13, MUTED, "middle")
    dim_v(cx_e + wf + 28, y_back, y_back + L, cm(P["pedal_back_y"] - P["pedal_front_y"]), left=False)
    dim_h(0, cx_e - wf, cx_e + wf, y_back + L + 24, cm(P["pedal_w_front"]), above=False)
    text(x0e + 20, by + 440, "Three cast-brass pedals, soft,", 14)
    text(x0e + 20, by + 460, "practice and sustain, flared from", 14)
    text(x0e + 20, by + 480, f"{cm(P['pedal_w_back'])} to {cm(P['pedal_w_front'])} with a round nose,", 14)
    text(x0e + 20, by + 500, f"{cm(P['pedal_t'])} thick, all edges rounded.", 14)
    text(x0e + 20, by + 530, "They come out of a dark felt slot", 14, MUTED)
    text(x0e + 20, by + 550, "in the toe rail.", 14, MUTED)

    # 5. finishes -------------------------------------------------------------------
    x5 = 40 + 5 * (bw + 10)
    w5 = W_PX - 40 - x5
    panel(x5, by, w5, bh, "5 · Finish options and materials")
    col_w = (w5 - 48) / 2
    for i, key in enumerate(("black", "walnut")):
        f = C.FINISHES[key]
        cx0 = x5 + 16 + i * (col_w + 16)
        ytop = by + 52
        # room context: wall and floor, the piano small in front of it
        add(f'<rect x="{cx0}" y="{ytop}" width="{col_w}" height="250" fill="{C.COL["wall"]}"/>')
        add(f'<rect x="{cx0}" y="{ytop + 206}" width="{col_w}" height="44" fill="{C.COL["oak_light"]}"/>')
        for j in range(1, 9):
            xx = cx0 + j * col_w / 9
            add(f'<line x1="{xx}" y1="{ytop + 206}" x2="{xx - 10}" y2="{ytop + 250}" stroke="#5a3a22" stroke-opacity=".5"/>')
        fill = "#0a0a0a" if key == "black" else "url(#walnut)"
        stf = dict(TECH, case=fill, recess=fill, inset=fill, stroke="#000" if key == "black" else "#1c0f08",
                   sw=0.5, white="#efe8d8", black="#121110", paper="#fbf9f3")
        vm = View(cx0 + col_w / 2, ytop + 232, 0.135)
        front(vm, stf, detail=False)
        # gloss overlay on the case silhouette
        x_a, y_a = vm.p(-P["width"] / 2 - 0.01, P["case_top"] + P["lid_t"])
        x_b, y_b = vm.p(P["width"] / 2 + 0.01, 0.035)
        add(f'<rect x="{x_a:.1f}" y="{y_a:.1f}" width="{x_b - x_a:.1f}" height="{y_b - y_a:.1f}" fill="url(#gloss)" '
            f'opacity="{1 if key == "black" else 0.6}"/>')
        if key == "walnut":
            add(f'<rect x="{x_a:.1f}" y="{y_a:.1f}" width="{x_b - x_a:.1f}" height="{y_b - y_a:.1f}" fill="url(#grain)" opacity=".7" '
                f'style="mix-blend-mode:multiply"/>')
        # big swatch
        sy0 = ytop + 268
        add(f'<rect x="{cx0}" y="{sy0}" width="{col_w}" height="110" fill="{fill}" rx="4"/>')
        add(f'<rect x="{cx0}" y="{sy0}" width="{col_w}" height="110" fill="url(#gloss)" rx="4"/>')
        if key == "walnut":
            add(f'<rect x="{cx0}" y="{sy0}" width="{col_w}" height="110" fill="url(#grain)" rx="4" opacity=".8"/>')
        text(cx0, sy0 + 136, f"{'A' if i == 0 else 'B'} · {f['label']}", 18, INK, weight=600)
        text(cx0, sy0 + 158, f"{f['material']}: {f['note']}", 13, MUTED)
        text(cx0, sy0 + 176, "base " + f["base"] + ("" if key == "black" else f", grain {f['dark']} to {f['light']}"),
             13, MUTED)
    # trim materials
    ty0 = by + 520
    trims = [("Ivory keys", C.COL["ivory"], "mat_piano_key_white", "warm, not pure white"),
             ("Ebony sharps", C.COL["ebony"], "mat_piano_key_black", "satin black"),
             ("Brass", C.COL["brass"], "mat_piano_brass", "pedals, hinges, castors, lock"),
             ("Red felt", C.COL["felt_red"], "mat_piano_felt", "strip behind the keys"),
             ("Hammer felt", C.COL["felt_cream"], "mat_piano_hammers", "inside, with the lid open")]
    tw = (w5 - 32 - 4 * 12) / 5
    for j, (lab, colr, mat, note) in enumerate(trims):
        tx0 = x5 + 16 + j * (tw + 12)
        add(f'<rect x="{tx0}" y="{ty0}" width="{tw}" height="70" fill="{colr}" stroke="#cfc8bb" rx="4"/>')
        if lab == "Brass":
            add(f'<rect x="{tx0}" y="{ty0}" width="{tw}" height="70" fill="url(#gloss)" rx="4"/>')
        text(tx0, ty0 + 92, lab, 14, INK, weight=600)
        text(tx0, ty0 + 110, colr, 12, MUTED)
        words, line, ly = note.split(), "", ty0 + 127
        for wd in words:
            if len(line) + len(wd) > 18:
                text(tx0, ly, line, 12, MUTED)
                line, ly = "", ly + 15
            line = (line + " " + wd).strip()
        text(tx0, ly, line, 12, MUTED)
    text(x5 + 16, by + 712, "Recommended: A, polished black. The 5:40 blue window shows up as a reflection", 14, INK, weight=600)
    text(x5 + 16, by + 731, "in it, and it stands apart from the oak floor and the sunburst guitars above it.", 14, INK)
    text(x5 + 16, by + 750, "B suits a warmer room, but brown on brown under the wood guitars reads as one mass.", 14, MUTED)
    add("</svg>")


def main():
    os.makedirs(OUT, exist_ok=True)
    build()
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>Piano design sheet</title>"
            f"<style>html,body{{margin:0;background:{PAPER}}}svg{{display:block}}</style></head><body>"
            + "\n".join(out) + "</body></html>")
    hp = os.path.join(OUT, "piano-design-sheet.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    png = os.path.join(OUT, "piano-design-sheet.png")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={W_PX},{H_PX}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", hp, png)


if __name__ == "__main__":
    main()
