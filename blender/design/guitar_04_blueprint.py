"""2D blueprint for guitar_04, Stevie Ray Vaughan's "Number One", to scale from
blender/lib/guitar_specs.py GUITAR_04. Dimensions in mm.

The Strat geometry (small headstock r3, neck, posts) is guitar_02's; the body, pickups, bridge, guard, controls
and jack are Number One's own, measured (GUITAR_04):
this module runs blender/design/guitar_02_blueprint.py's geometry and drawing helpers with
GUITAR_04 (lib/variant.py) and re-exports them, so props/guitar_04.py reads the same derived
geometry under `import guitar_04_blueprint as BP`. The finish and wear pictures come from
lib/guitar_wear.py, the same fields the 3D material samples.

Plain Python with numpy (no Blender). Run from the repo root:

    python3 blender/design/guitar_04_blueprint.py

Output: video-local/footage/2026-10-23-guitar-04/guitar-04-blueprint.{html,png}
"""
import base64
import io
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from lib import variant  # noqa: E402

_B = variant.load(os.path.join(HERE, "guitar_02_blueprint.py"),
                  [("GUITAR_02", "GUITAR_04"), ("2026-10-23-guitar-02", "2026-10-23-guitar-04")],
                  "_guitar_04_blueprint_base")
globals().update({k: v for k, v in vars(_B).items() if not k.startswith("__") and k not in ("build", "main")})

from lib import constants as C, guitar_wear as GW  # noqa: E402

W_PX, H_PX = 2600, 3480
GOLD, GOLD_D, PEARL, CREAM, BLACK, ROSE, CLAY = "#c9a450", "#8e7235", "#ece6da", "#e6d9b0", "#151413", "#3a2419", "#d4a46c"
HEADC, CHROMEC = "#d2a35a", "#cfd2d6"


# ---------------------------------------------------------------------------
# the rack pivot: the body's lowest point when it leans in the rack (MESHES.md, obj_guitars)
# ---------------------------------------------------------------------------
def rack_pivot(lean_deg=None):
    """(u, v) of the body outline's lowest point with the guitar leaned lean_deg in its own plane,
    headstock towards +u (the rack's local +X)."""
    th = math.radians(C.LAYOUT["rack"]["lean"] if lean_deg is None else lean_deg)
    return min(BODY, key=lambda p: -p[0] * math.sin(th) + p[1] * math.cos(th))


FIELDS = None


def fields():
    global FIELDS
    if FIELDS is None:
        FIELDS = GW.fields(G, HEAD)
    return FIELDS


def _png_uri(rgba):
    from PIL import Image
    buf = io.BytesIO()
    Image.fromarray(rgba).save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def finish_image(V, side="front"):
    """The body finish (sunburst, wood, wear) as a raster under the vector drawing."""
    import numpy as np
    f = fields()
    rgb = GW.preview(G, f, side)
    a = ((f["dist"] > 0)[::-1] * 255).astype(np.uint8)
    img = np.dstack([rgb, a])
    if V.m < 0:
        img = img[:, ::-1]
    x0, y0 = V.p(GW.U0 if V.m > 0 else GW.U1, GW.V1)
    add(f'<image href="{_png_uri(img)}" x="{x0:.1f}" y="{y0:.1f}" width="{GW.W * GW.STEP * V.s:.1f}" '
        f'height="{GW.H * GW.STEP * V.s:.1f}" preserveAspectRatio="none"/>')


def wear_map_image(V):
    """Classes, front: sunburst kept, wood (grimy), wood (pale); the guard area hatched."""
    import numpy as np
    f = fields()
    inb = f["dist"] > 0
    img = np.zeros(f["dist"].shape + (4,), np.uint8)
    img[inb] = (123, 84, 53, 255)
    img[inb & (f["pale"] > 0.5)] = (227, 195, 152, 255)
    img[inb & (f["finish"] > 0.5)] = (201, 116, 32, 255)
    img = img[::-1]
    x0, y0 = V.p(GW.U0, GW.V1)
    add(f'<image href="{_png_uri(img)}" x="{x0:.1f}" y="{y0:.1f}" width="{GW.W * V.s:.1f}" '
        f'height="{GW.H * V.s:.1f}" preserveAspectRatio="none"/>')


def back_map_image(V):
    import numpy as np
    f = fields()
    inb = f["dist"] > 0
    img = np.zeros(f["dist"].shape + (4,), np.uint8)
    img[inb] = (201, 116, 32, 255)
    img[inb & (f["back"] > 0.5)] = (123, 84, 53, 255)
    img[inb & (f["dist"] < G["edge_wear_mm"])] = (123, 84, 53, 255)
    img = img[::-1][:, ::-1]
    x0, y0 = V.p(GW.U1, GW.V1)
    add(f'<image href="{_png_uri(img)}" x="{x0:.1f}" y="{y0:.1f}" width="{GW.W * V.s:.1f}" '
        f'height="{GW.H * V.s:.1f}" preserveAspectRatio="none"/>')


# ---------------------------------------------------------------------------
# front and back
# ---------------------------------------------------------------------------
def oval(l, w, n, e=2.6):
    out_ = []
    for k in range(n):
        t = 2 * math.pi * k / n
        c, s_ = math.cos(t), math.sin(t)
        out_.append((l / 2 * math.copysign(abs(c) ** (2 / e), c), w / 2 * math.copysign(abs(s_) ** (2 / e), s_)))
    return out_


def _gold_screw(V, u, v, d):
    V.circle(u, v, d / 2, GOLD, INK, 0.6)


def draw_front04(V, strings=True, pivot=True, left_out=False):
    s = V.s
    sw = 1.1 if s < 3 else 1.4
    sb = G["strap_button"]
    for u, v, ang, _ in G["strap_buttons"]:
        V.path(shape(rrect(sb["h"] * 2, sb["d"], 3), (u, v), ang), GOLD, INK, sw * 0.9)
    k = G["tuner_key"]
    for (pa, pv), (ka, _) in zip(posts(), keys()):
        V.line((pa, pv), (ka, pv), GOLD_D, max(1.2, 3.0 * s * 0.5))
        V.path(shape(ellipse(k["w"], k["h"]), (ka, pv)), PEARL, INK, sw * 0.9)
    finish_image(V, "front")
    V.path(BODY, "none", INK, sw * 1.2)
    # jack: the long oval plate, the deep cup towards its lower end, a screw at each end
    j = G["jack"]
    along = lambda d: (j["u"] + rot((d, 0), j["angle_deg"])[0], j["v"] + rot((d, 0), j["angle_deg"])[1])  # noqa: E731
    V.path(shape(oval(j["l"], j["w"], 48), (j["u"], j["v"]), j["angle_deg"]), GOLD, INK, sw)
    V.path(shape(oval(j["cup_l"], j["cup_w"], 40, 2.2), along(j["cup_off"]), j["angle_deg"]), "#e3c77a", INK, sw * 0.8)
    for d in j["screw_offs"]:
        _gold_screw(V, *along(d), 3.8)
    V.circle(*along(j["cup_off"] - j["cup_l"] * 0.18), 3.2, "#2a2826", "none", 0)
    # pickguard, 1-ply black
    V.path(GUARD, BLACK, INK, sw)
    V.path(GUARD, "none", "#4a4744", max(1.0, 0.9 * s), extra='stroke-opacity="0.7"')
    for u, v in G["guard_screws"]:
        _gold_screw(V, u, v, 5.4)
    # neck: rosewood board, frets, clay dots, nut
    V.path(NECK, ROSE, INK, sw)
    for x in FRETS:
        v = VN - x
        hw = neck_w(v) / 2 - 0.6
        V.line((-hw, v), (hw, v), "#b9b7b0", max(1.0, G["fret_wire"][0] * s * 0.9))
    prev = 0.0
    for n, x in enumerate(FRETS, 1):
        if n in G["dots"]:
            vm = VN - (prev + x) / 2
            for u in ((-G["dot12_offset"], G["dot12_offset"]) if n == 12 else (0.0,)):
                V.circle(u, vm, G["dot_d"] / 2, CLAY, "none", 0)
        prev = x
    # headstock, worn edge
    V.path(HEAD, HEADC, INK, sw)
    V.path(HEAD, "none", "#8a5a2a", max(1.5, G["head_edge_wear_mm"] * s * 0.6), closed=False,
           extra='stroke-opacity="0.55"')
    V.path(HEAD, "none", INK, sw * 0.8, closed=False)
    V.path([(-G["nut_w"] / 2, VN), (-G["nut_w"] / 2, VN + G["nut_l"]), (G["nut_w"] / 2, VN + G["nut_l"]),
            (G["nut_w"] / 2, VN)], "#efe8d6", INK, sw * 0.9)
    for pa, pv in posts():
        V.circle(pa, pv, G["bushing_d"] / 2, GOLD, INK, sw * 0.8)
        V.circle(pa, pv, G["post_d"] / 2, GOLD_D, INK, sw * 0.8)
    t = G["string_tree"]
    V.path(shape(rrect(t["w"], t["h"], 2.0), (t["a"], VN + t["b"])), GOLD, INK, 0.9)
    # pickups, aged cream
    pk = G["pickup"]
    for (c, ang) in pickups():
        V.path(shape(rrect(pk["l"], pk["w"], 7), c, ang), CREAM, INK, sw)
        for i in range(6):
            q = rot((-pk["pole_spread"] / 2 + pk["pole_spread"] * i / 5, 0), ang)
            V.circle(c[0] + q[0], c[1] + q[1], pk["pole_d"] / 2, "#8f8f8a", INK, 0.6)
        for sgn in (-1, 1):
            q = rot((sgn * pk["screw_off"], 0), ang)
            _gold_screw(V, c[0] + q[0], c[1] + q[1], 4.6)
    # gold bridge and saddles; the arm socket on the bass end
    br = G["bridge"]
    front = VS + br["front_off"]
    V.path(shape(rrect(br["w"], br["l"], 2.5), (0, front - br["l"] / 2)), GOLD, INK, sw)
    for u in strings_bridge():
        _gold_screw(V, u, front - br["screw_off_front"], br["screw_d"])
    b0 = sum(G["saddle_back"]) / 6
    for u, back in zip(strings_bridge(), G["saddle_back"]):
        d = b0 - back                                  # each saddle moves with its string's intonation
        v0, v1 = br["saddle_rear"] + d, br["saddle_front"] + d
        V.path(shape(rrect(br["saddle_w"] - 0.6, v1 - v0, 1.6), (u, (v0 + v1) / 2)), "#dcc27e", INK, sw * 0.8)
        for sg in (-1, 1):
            V.circle(u + sg * 2.9, br["height_screw_v"] + d, 1.3, GOLD_D, "none", 0)
    V.circle(G["arm"]["u"], G["arm"]["v"], G["arm"]["socket_r"], "#1c1b1a", INK, 0.8)
    kn = G["knob"]
    for _, u, v in G["knobs"]:
        V.circle(u, v, kn["d"] / 2, CREAM, INK, sw)
        V.circle(u, v, kn["top_d"] / 2, "#efe6c8", INK, sw * 0.6)
    sw_ = G["switch"]
    V.path(shape(rrect(sw_["slot_l"], sw_["slot_w"], 1.5), (sw_["u"], sw_["v"]), sw_["angle_deg"]), "#2a2826",
           "#55524d", 0.8)
    tip_c = rot((-(sw_["slot_l"] / 2 - 3.5), 0), sw_["angle_deg"])
    V.path(shape(rrect(sw_["tip_w"], sw_["tip_l"], 3.2), (sw_["u"] + tip_c[0], sw_["v"] + tip_c[1]),
                 sw_["angle_deg"]), CREAM, INK, sw)
    if strings:
        nut, brs = strings_nut(), strings_bridge()
        for i, (a, u, back, g) in enumerate(zip(nut, brs, G["saddle_back"], G["gauges"])):
            w = max(0.7, g * 25.4 * s * 0.9)
            V.line((a, VN), (u, VS - back), "#7d8085", w)
            pa, pv = posts()[i]
            V.line((a, VN + G["nut_l"]), (pa + G["post_d"] / 2, pv), "#7d8085", w)
    a = G["arm"]
    end = (a["u"] + a["length"] * math.cos(math.radians(a["angle_deg"])),
           a["v"] + a["length"] * math.sin(math.radians(a["angle_deg"])))
    V.line((a["u"], a["v"]), end, INK, max(2.2, 5.2 * s * 0.5 + 1.0))
    V.line((a["u"], a["v"]), end, CHROMEC, max(1.2, 5.2 * s * 0.5 - 0.4))
    tip0 = (end[0] - 24 * math.cos(math.radians(a["angle_deg"])), end[1] - 24 * math.sin(math.radians(a["angle_deg"])))
    V.line(tip0, end, INK, max(2.8, 7 * s * 0.5 + 1))
    V.line(tip0, end, CREAM, max(1.8, 7 * s * 0.5 - 0.4))
    if left_out:
        for (u, v, w, h, ang, lab) in LEFT_OUT:
            V.path(shape(rrect(w, h, 2), (u, v), ang), "url(#hatch)", ACC, 1.2, extra='stroke-dasharray="4 3"')
    if pivot:
        pu, pv = rack_pivot()
        x, y = V.p(pu, pv)
        r = 7
        add(f'<g stroke="{ACC}" stroke-width="1.6"><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none"/>'
            f'<line x1="{x - r - 4:.1f}" y1="{y:.1f}" x2="{x + r + 4:.1f}" y2="{y:.1f}"/>'
            f'<line x1="{x:.1f}" y1="{y - r - 4:.1f}" x2="{x:.1f}" y2="{y + r + 4:.1f}"/></g>')


# what the real guitar carries and the model leaves out: (u, v, w, h, angle, label)
LEFT_OUT = [(62, 245, 70, 150, 0, "the stick-on initials on the guard"),
            (0, 105, 88, 18, 0, "the \"Custom\" sticker behind the bridge"),
            (22, VN + 118, 48, 20, 62, "headstock logo decal"), (30, VN + 84, 30, 7, 62, "model name"),
            (12, VN + 28, 26, 5, 80, "patent text, serials")]


def draw_back04(V):
    sw = 1.1
    sb = G["strap_button"]
    for u, v, ang, _ in G["strap_buttons"]:
        V.path(shape(rrect(sb["h"] * 2, sb["d"], 3), (u, v), ang), GOLD, INK, sw * 0.9)
    k = G["tuner_key"]
    for (pa, pv), (ka, _) in zip(posts(), keys()):
        V.line((pa, pv), (ka, pv), GOLD_D, 1.6)
        V.path(shape(ellipse(k["w"], k["h"]), (ka, pv)), PEARL, INK, sw * 0.9)
    V.path(NECK, "#d9b273", INK, sw)
    lo, hi = G["neck_wear"]
    V.path([(-neck_w(VN - lo) / 2, VN - lo), (neck_w(VN - lo) / 2, VN - lo), (neck_w(VN - hi) / 2, VN - hi),
            (-neck_w(VN - hi) / 2, VN - hi)], "#c9b28c", "none", 0, extra='fill-opacity="0.8"')
    V.path(HEAD, "#d9b273", INK, sw)
    finish_image(V, "back")
    V.path(BODY, "none", INK, sw * 1.2)
    tc = G["trem_cover"]
    cv = tc["v0"] + tc["l"] / 2
    V.path(shape(rrect(tc["w"], tc["l"], tc["r"]), (0, cv)), BLACK, INK, sw)
    for u in strings_bridge():
        V.path(shape(ellipse(5.0, 7.5, 16), (u, VS - 12)), "#3b3936", "#55524d", 0.6)
    npl = G["neck_plate"]
    V.path(shape(rrect(npl["w"], npl["l"], npl["r"]), (0, npl["v"])), GOLD, INK, sw)
    for su in (-1, 1):
        for sv in (-1, 1):
            V.circle(su * npl["screw_du"], npl["v"] + sv * npl["screw_dv"], 4.0, GOLD_D, INK, 0.8)
    th = G["tuner_housing"]
    for pa, pv in posts():
        V.path(shape(rrect(th["w"], th["h"], 2.5), (pa, pv)), GOLD, INK, sw * 0.8)


# ---------------------------------------------------------------------------
# the sheet
# ---------------------------------------------------------------------------
def swatch(x, y, col, label, sub=""):
    add(f'<rect x="{x}" y="{y}" width="46" height="34" rx="4" fill="{col}" stroke="{LINE}"/>')
    text(x + 58, y + 15, label, 13, INK)
    if sub:
        text(x + 58, y + 31, sub, 11.5, MUTED)


def build():
    out.clear()
    add(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W_PX}" '
        f'height="{H_PX}" viewBox="0 0 {W_PX} {H_PX}" font-family="-apple-system, Helvetica Neue, Arial, sans-serif">')
    add('<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<line x1="0" y1="0" x2="0" y2="6" stroke="{ACC}" stroke-width="1.2" stroke-opacity=".55"/></pattern></defs>')
    add(f'<rect width="{W_PX}" height="{H_PX}" fill="{PAPER}"/>')
    text(48, 58, "guitar_04 · \"Number One\" · blueprint", 32, INK, weight=650)
    text(48, 88, f"After Stevie Ray Vaughan's Number One: a 1963 body, a 1962 neck, 1959 pickups, his left-handed "
         f"gold tremolo · its own body, traced; guitar_02's small headstock r3 · {mm(G['overall'])} long, "
         f"{mm(BODY_W)} wide, {mm(G['body_t'])} body · 21 jumbo frets, {mm(SC)} scale · no logos, initials, "
         f"sticker or serials", 16, MUTED)
    text(W_PX - 48, 58, "2026-10-23 · overnight, not yet approved: drawn and modelled for the morning review",
         15, ACC, "end")

    s = 2.0
    top_y, row_h = 116, 2160
    base_y = top_y + row_h - 90
    # ---- 1 front ------------------------------------------------------------------------
    fx, fw = 40, 1040
    panel(fx, top_y, fw, row_h, "1 · Front, as it stands in the rack (shown upright)",
          "Finish and wear from the fields the 3D material samples. Pivot ⊕: the body's lowest point at the 15° lean.")
    VF = View(fx + 380, base_y, s)
    draw_front04(VF)
    xl, _ = VF.p(-BODY_W / 2 - 0.2, 0)
    xr, _ = VF.p(BODY_W / 2 + 0.2, 0)
    dim_h(xl, xr, base_y + 46, f"{mm(BODY_W)} lower bout", above=False)
    _, yt = VF.p(0, G["v_tip"])
    _, yb = VF.p(0, 0)
    dim_v(fx + 40, yt, yb, f"{mm(G['overall'])} tail to tip (the small headstock r3)", ext=[(xl, yb), (VF.p(0, 0)[0], yt)])
    labels = [
        (VF.p(-60, 390), "wear map traced from the owner's photo (ref 11)", "bare alder, grimy; pale where rubbed clean"),
        (VF.p(-40, 60), "the sunburst survives on the lower bout", "dark edge, faded red, amber centre"),
        (VF.p(G["arm"]["u"], G["arm"]["v"]), "left-handed gold tremolo: arm on the bass side",
         "dark socket half over the plate's bass end; rests across the bout"),
        (VF.p(G["jack"]["u"], G["jack"]["v"]), "cup-style jack: a long oval gold plate",
         f"{mm(G['jack']['l'])} x {mm(G['jack']['w'])}, {mm(90 + G['jack']['angle_deg'], 0)} deg from the strings, the cup low"),
        (VF.p(60, 250), "1-ply black guard, 9 gold screws", "traced; the initials left out"),
        (VF.p(0, VN - 300), "rosewood board, clay dots, jumbo bass frets", "10 in radius as refretted; 41.9 bone nut"),
        (VF.p(-24, VN + 60), "gold tuners, plastic buttons", "headstock edge worn dark"),
    ]
    lx = fx + 760
    ys = spread([[p[1], p, a, b] for p, a, b in labels], 46)
    for y, p, a, b in ys:
        leader(p[0], p[1], lx, y, a, "start", b)

    # ---- 2 back -------------------------------------------------------------------------
    bx, bw = 1100, 700
    panel(bx, top_y, bw, row_h, "2 · Back (seen from behind: bass side on the right)",
          "Designed wear: the real back is not in our photos. Belly cut, buckle rash, edges.")
    VB = View(bx + bw / 2, base_y, s, mirror=True)
    draw_back04(VB)
    lo, hi = G["neck_wear"]
    leader(*VB.p(0, VN - (lo + hi) / 2), bx + bw - 14, VB.p(0, VN - (lo + hi) / 2)[1], "neck back rubbed to bare maple",
           "end", f"{mm(lo)} to {mm(hi)} mm from the nut")
    leader(*VB.p(-100, 380), bx + 14, VB.p(-100, 380)[1] - 160, "belly cut worn through", "start", "and the bass upper bout")
    leader(*VB.p(0, 228), bx + 14, base_y + 40, "buckle rash, under the cover too", "start")
    leader(*VB.p(0, G["trem_cover"]["v0"] + 30), bx + bw - 14, base_y + 40, "black back cover, gold neck plate",
           "end", "approximate: plain, no stamp or serial")

    # ---- 3 right column: differences, swatches -----------------------------------------
    rx, rw = 1820, 740
    panel(rx, top_y, rw, 1180, "3 · What differs from guitar_02", "Shared with guitar_02: contours, headstock r3, "
          "posts, neck heel")
    pk_ = G["pickups_from_scale"]
    rows = [("body outline", "r2, photo-measured", f"its own, traced from ref 11 ({mm(BODY_W, 0)} wide)"),
            ("pickups", "162 / 102 / 48 from the scale", f"measured: {pk_[0]} / {pk_[1]} / {pk_[2]}, {G['bridge_slant_deg']} deg"),
            ("strings", "Hendrix's reversed (thin E left)", "right-handed, low E left; .013 to .058"),
            ("string tree", "on A and low E", "on B and high E (same place)"),
            ("fingerboard", "maple cap, black dots", "rosewood, clay dots"),
            ("radius, frets", "7.25 in, vintage wire", "10 in, jumbo 2.79 x 1.40"),
            ("nut, neck", "41.3, 20.8 to 23.6", "41.9, 20.3 to 23.6 (big oval C)"),
            ("pickguard", "3-ply white, 11 screws", "1-ply black, 9 screws, traced"),
            ("pickups, knobs", "white", "aged cream"),
            ("knob layout", "the 1968 sheet's", "measured: 55/174, 94/154, 126/126"),
            ("switch", "3-way", "5-way, tip at the neck end"),
            ("bridge, saddles", "chrome, nickel; 74 x 42 plate", f"gold, left-handed; {mm(G['bridge']['w'])} x {mm(G['bridge']['l'])} plate, 5 mm nearer the tail"),
            ("tremolo arm", "treble side, across", "bass side, across the lower bout"),
            ("jack", "football in a dish", "long oval gold plate, 55 deg, the cup low"),
            ("strap buttons", "3, chrome", "2, gold"),
            ("tuners", "nickel, metal keys", "gold, pearl plastic buttons"),
            ("neck plate, cover", "chrome, white", "gold, black (approximate)"),
            ("finish", "Olympic White, aged a year", "3-tone sunburst worn to bare wood"),
            ("where it lives", "wall hook, guitar_02 pivot", "rack slot 1, pivot at the cradle")]
    y = top_y + 96
    text(rx + 16, y, "part", 13, MUTED, weight=600)
    text(rx + 190, y, "guitar_02", 13, MUTED, weight=600)
    text(rx + 440, y, "guitar_04", 13, MUTED, weight=600)
    for a, b, c in rows:
        y += 58
        text(rx + 16, y, a, 14, INK, weight=600)
        para(rx + 190, y, b, 30, 13, MUTED)
        para(rx + 440, y, c, 40, 13, INK)
    # swatches
    sy = top_y + 1210
    panel(rx, sy, rw, 950, "4 · Finishes (sRGB, as the materials use them)")
    y = sy + 80
    for i, (d, col) in enumerate(G["sunburst"]):
        swatch(rx + 16 + (i % 3) * 245, y + (i // 3) * 52, col, f"sunburst at {mm(d)} mm", "in from the edge")
    y += 3 * 52 + 20
    wd = G["wood"]
    items = [(wd["grime"], "bare alder, grimy", "most of the top"), (wd["grime_dark"], "grime, dark", "edges, horns"),
             (wd["pale"], "bare alder, pale", "rubbed clean (waist)"), (wd["stain"], "stained rim", "round each patch"),
             (ROSE, "rosewood board", "round-laminated"), (CLAY, "clay dots", ""),
             (BLACK, "pickguard", "1-ply black"), (CREAM, "pickups, knobs, tip", "aged cream"),
             (GOLD, "gold plating", "worn to brass on the saddles"), (PEARL, "tuner buttons", "pearl plastic"),
             (HEADC, "headstock face", "aged amber lacquer"), (CHROMEC, "arm", "chrome, cream tip")]
    for i, (col, a, b) in enumerate(items):
        swatch(rx + 16 + (i % 3) * 245, y + (i // 3) * 52, col, a, b)
    y += 4 * 52 + 30
    para(rx + 16, y, "Ageing heavy, as the real guitar: nitro checked and dulled where it survives, the bare wood "
         "darkened by grime and sweat, scratches and chips through to wood everywhere the finish is left. The "
         "chips, scratches and edge rash are noise in the material on top of the traced map, so they never repeat.",
         96, 13, MUTED)

    # ---- row 2: wear maps, left out, budget ----------------------------------------------
    r2 = top_y + row_h + 40
    s2 = 1.45
    h2 = 820
    panel(40, r2, 640, h2, "5 · Wear map, front (traced)", "orange: sunburst kept · brown: bare wood · pale: rubbed clean")
    VW = View(40 + 320, r2 + h2 - 60, s2)
    wear_map_image(VW)
    VW.path(BODY, "none", INK, 1.0)
    VW.path(GUARD, "none", "#55524d", 0.9, extra='stroke-dasharray="5 4"')
    panel(700, r2, 640, h2, "6 · Wear map, back (designed)", "orange: sunburst kept · brown: bare wood")
    VK = View(700 + 320, r2 + h2 - 60, s2, mirror=True)
    back_map_image(VK)
    VK.path(BODY, "none", INK, 1.0)
    panel(1360, r2, 520, h2, "7 · Left out", "hatched: on the real guitar, never on ours")
    VL = View(1360 + 260, r2 + h2 - 24, 0.68)
    draw_front04(VL, strings=False, pivot=False, left_out=True)
    y = r2 + 90
    for i, (_, _, _, _, _, lab) in enumerate(LEFT_OUT):
        text(1376, y + i * 22, f"· {lab}", 13, INK)
    panel(1900, r2, 660, h2, "8 · Web budget (lite, the site)")
    rows = [("", "rich, renders", "lite, site"), ("triangles", "about 125k", "about 7k"),
            ("strings", "own mesh, wound bump", "own mesh, 312"),
            ("textures", "procedural + 2 wear maps", "one 1024 atlas"), ("", "(1 mm, from the spec)", "+ 512 ORM"),
            ("materials", "about 20", "1 + strings"), ("meshes the code uses", "guitar_04, _body,", "same three"),
            ("", "_strings", ""), ("GLB", "about 3.5 MB", "about 600 KB")]
    y = r2 + 70
    for a, b, c in rows:
        y += 34
        wt = 600 if b == "rich, renders" else 400
        text(1916, y, a, 13, INK, weight=600 if a else 400)
        text(2110, y, b, 13, INK, weight=wt)
        text(2350, y, c, 13, INK, weight=wt)
    para(1916, y + 44, "Lite: the wear, sunburst and grime bake into the atlas from the same material; the "
         "contours and bevels stay geometry; tuners become simple caps; screws drop. Strings stay a separate mesh "
         "for the strum shimmer.", 72, 13, MUTED)

    # ---- row 3: notes -------------------------------------------------------------------
    r3 = r2 + h2 + 30
    panel(40, r3, 2520, H_PX - r3 - 30, "9 · For the morning review")
    notes = [
        "Not approved before 3D (decision 2026-10-23, overnight): this sheet and the model were made together.",
        "Measured on owner-ref-11 (a Custom Shop copy made from the real guitar), rectified by fit 8 (a homography and "
        "one radial lens term, 1.27 px rms, on the neck, bridge screws, poles and the r3 posts; nothing on the body "
        "assumed; the photo is barrel-distorted about 3% at its edges): the body outline, pickups, "
        "bridge, guard, its 9 screws, knobs, switch, jack, arm socket and the wear map. The headstock is guitar_02's "
        "r3 (approved). Checked on the real guitar (n1-4): see guitar-04-compare.png and NOTE.md.",
        "The arm: his left-handed tremolo puts the socket on the bass end of the plate. Displayed, the real guitar's "
        "arm hangs below the tail; in the rack that would hit the cradle, so it rests across the lower bout as in "
        "its case photo (ref 13). Approved by the owner overnight (\"you can change position of tremolo arm\").",
        "Found while measuring: guitar_02's pickguard is about 25 mm too wide on the bass side and its knob line "
        "is steeper than the photos (both photos agree). Fixed after this guitar (guitar_02 r4), with its pickups.",
    ]
    y = r3 + 70
    for n_ in notes:
        y = para(56, y, "· " + n_, 230, 14, INK) + 8
    add("</svg>")


def main():
    os.makedirs(OUT, exist_ok=True)
    build()
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>guitar_04 blueprint</title>"
            f"<style>html,body{{margin:0;background:{PAPER}}}svg{{display:block}}</style></head><body>"
            + "\n".join(out) + "</body></html>")
    hp = os.path.join(OUT, "guitar-04-blueprint.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    png = os.path.join(OUT, "guitar-04-blueprint.png")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={W_PX},{H_PX}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", hp, png)


if __name__ == "__main__":
    main()
