"""2D ornament sheet for the upright piano: tribal tattoo-style artwork in silver on the
black lacquer, two levels (Medium, Full) and three centre emblems to choose from.

Plain Python (no Blender). It reuses the front elevation from piano_design_sheet.py and
the sheet clip from piano_ornament_sheet.py, so proportions match the approved sheet,
and draws every stroke in the piano's own metres on top. Writes an HTML page with one
SVG and renders it to a PNG with the cached headless Chromium. Run from the repo root:

    python3 blender/design/piano_tribal_sheet.py

Output: video-local/footage/2026-10-22-piano-quality-test/piano-tribal-sheet.{html,png}

The strokes are ours, built from four parts: a tapering blade, a hook, a flame point
and a teardrop cut-out, mirrored about the piano's centreline. The owner's two tattoo
references (docs/moodboard/local/, local only) set the style; nothing is traced.
No text, no logos.
"""
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import piano_design_sheet as D  # noqa: E402  (front elevation, View, text helpers)
import piano_ornament_sheet as O  # noqa: E402  (sheet clip, wrap, fields, bench)
from lib import constants as C  # noqa: E402

P, KT = C.PIANO, C.KT
OUT = D.OUT
W_PX, H_PX = 2400, 2900
add, text, wrap = D.add, D.text, O.wrap
INK, MUTED, ACC, PAPER = D.INK, D.MUTED, D.ACC, D.PAPER

# The strokes, the emblems, the metals and the placements live in lib/piano_ornament.py
# (one source: the 3D build rasterises the same geometry into its silver masks).
from lib.piano_ornament import (  # noqa: E402
    SILVER, SILVER_HI, SILVER_LO, CHROME, NICKEL, FIELD_LO, CHEEK_IN, FB_MID, UP_MID, LID_Z, BENCH_MID,
    arc, turn, wave, plus, thorn, spindle, blade, Piece, place, arm, wing, EMBLEMS, layout, emit)

LACQ = C.COL["lacquer_black"]
DARK = dict(O.DARK, brass="url(#chrome)")
MASK_N = [0]


class Layer:
    """Collects page polygons; flush() writes them as silver, with the cut-outs masked."""

    def __init__(self):
        self.solid, self.holes = [], []

    def flush(self, fill="url(#silver)"):
        # one page-wide sheen (no per-stroke gradients), so overlapping strokes show no seams
        if not self.solid:
            return
        MASK_N[0] += 1
        mid = f"tm{MASK_N[0]}"

        def pts(poly):
            return " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)
        add(f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W_PX}" height="{H_PX}">'
            f'<rect width="{W_PX}" height="{H_PX}" fill="#fff"/>'
            + "".join(f'<polygon points="{pts(p)}" fill="#000"/>' for p in self.holes) + "</mask>")
        add(f'<g mask="url(#{mid})" fill="{fill}">'
            + "".join(f'<polygon points="{pts(p)}"/>' for p in self.solid) + "</g>")
        self.solid, self.holes = [], []


# ---------------------------------------------------------------------------
# hardware in chrome
# ---------------------------------------------------------------------------
def lock_plate(v, x, z, w=0.020, h=0.040):
    """Lock plate: a pointed lozenge (two blades base to base) with the keyhole."""
    pts = []
    for i in range(48):
        t = 2 * math.pi * i / 48
        yy = math.sin(t)
        hw = w / 2 * (1 - abs(yy) ** 1.6) ** 1.1
        pts.append((x + math.copysign(hw, math.cos(t)), z + yy * h / 2))
    v.poly(pts, "url(#chrome)", "#5d626b", 0.6)
    v.circle(x, z + 0.004, 0.0026, "#050505", "none", 0)
    v.poly([(x - 0.0011, z + 0.003), (x + 0.0011, z + 0.003), (x + 0.0019, z - 0.007), (x - 0.0019, z - 0.007)],
           "#050505", "none", 0)


def cheek_caps(v):
    n = P["cheek_nose"]
    for sx in (-1, 1):
        v.rect(sx * (CHEEK_IN + 0.010), sx * (P["width"] / 2 - 0.010), n - 0.006, n + 0.006, "url(#chrome)",
               "#5d626b", 0.5, rx=3)


# ---------------------------------------------------------------------------
# the ornament on the piano, by level (2 Medium, 3 Full) and emblem
# ---------------------------------------------------------------------------
def orn_behind(v, lvl):
    """Everything the music sheet covers: the upper sweep and the lid edge."""
    L = Layer()
    lay = layout(lvl, REC_EMB)
    emit(lay["upper"] + lay["lid"], L, v)
    L.flush()


def orn_front(v, lvl, emb):
    # music rest lip, in front of the sheet's bottom edge
    hw, lz0, lz1 = P["ledge_half_w"], P["ledge_z"], P["ledge_lip_top"]
    v.rect(-hw, hw, lz0, lz1, DARK["case"], DARK["stroke"], DARK["sw"], rx=2)
    L = Layer()
    lay = layout(lvl, emb)
    emit(lay["fall"] + lay["lower"] + lay["cheek"] + lay["console"], L, v)
    L.flush()
    lock_plate(v, 0, KT - 0.045)
    cheek_caps(v)
    if lvl >= 3:
        for m, kind, xl, xr, _, _ in D.KEYS:
            if kind == "w":
                v.rect(xl, xr, KT - P["white_h"], KT - 0.002, "url(#silverv)", "#6e737c", 0.4, rx=0.6)


def gloss(v, op=0.5):
    xa, ya = v.p(-P["width"] / 2 - 0.01, P["case_top"] + P["lid_t"])
    xb, yb = v.p(P["width"] / 2 + 0.01, P["floor_gap"])
    add(f'<rect x="{xa:.1f}" y="{ya:.1f}" width="{xb - xa:.1f}" height="{yb - ya:.1f}" fill="url(#gloss)" '
        f'opacity="{op}" pointer-events="none"/>')


CLIP_N = [0]


def piano(v, lvl, emb, box):
    """The front elevation with the ornament; box (page px) bounds the sheet clip."""
    CLIP_N[0] += 1
    D.front(v, DARK)
    O.clip_not_sheet(f"ns{CLIP_N[0]}", v, box)
    add(f'<g clip-path="url(#ns{CLIP_N[0]})">')
    orn_behind(v, lvl)
    add("</g>")
    orn_front(v, lvl, emb)
    gloss(v)


def crop(box, world, lvl, emb, bg=None, label=None):
    """Fit a world window (u0, u1, v0, v1) into a page box (x, y, w, h), clipped."""
    x, y, w, h = box
    u0, u1, v0, v1 = world
    s = min(w / (u1 - u0), h / (v1 - v0)) / 1000
    ox = x + (w - (u1 - u0) * s * 1000) / 2 - u0 * s * 1000
    oy = y + (h - (v1 - v0) * s * 1000) / 2 + v1 * s * 1000
    v = D.View(ox, oy, s)
    CLIP_N[0] += 1
    cid = f"cr{CLIP_N[0]}"
    add(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>')
    add(f'<g clip-path="url(#{cid})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{bg or DARK["recess"]}"/>')
    piano(v, lvl, emb, (x, y, x + w, y + h))
    add("</g>")
    if label:
        tag(x + 8, y + 8, label)
    return v


def tag(x, y, s, size=13):
    add(f'<rect x="{x}" y="{y}" width="{len(s) * size * 0.55 + 16:.0f}" height="{size + 11}" rx="3" fill="#000" opacity=".62"/>')
    text(x + 8, y + size + 4, s, size, "#e8e4dc")


def draw_bench(v, lvl, emb):
    B = O.BENCH
    hw = B["w"] / 2
    st, sw = DARK["stroke"], DARK["sw"]
    for sx in (-1, 1):
        lx = sx * B["leg_x"]
        v.poly([(lx - B["leg_bot"] / 2, 0), (lx + B["leg_bot"] / 2, 0), (lx + B["leg_top"] / 2, B["h"] - B["t"]),
                (lx - B["leg_top"] / 2, B["h"] - B["t"])], DARK["case"], st, sw)
    v.rect(-B["leg_x"], B["leg_x"], B["h"] - B["t"] - B["apron"], B["h"] - B["t"], DARK["recess"], st, sw)
    v.rect(-hw, hw, B["h"] - B["t"], B["h"], DARK["case"], st, sw, rx=3)
    if lvl >= 3:
        L = Layer()
        emit(layout(lvl, emb)["bench"], L, v)
        L.flush()


# ---------------------------------------------------------------------------
# page
# ---------------------------------------------------------------------------
REC_EMB = 2          # the emblem shown on both levels (the recommendation)

LEVELS = [
    dict(n=2, name="Medium", sub="the sweep, the emblem, chrome hardware, the lower corners",
         items=[("The long sweep across the upper panel: two arms that come out from behind the music and "
                 "run to needle points 1.5 cm short of the field's ends", "T"),
                ("The centre emblem on the fallboard's face (seen when open, where a maker's name sits), "
                 "with short wings and two framing hooks", "T"),
                ("Corner points in the four corners of the lower panel: two blades and a hook each", "T"),
                ("Hardware in polished chrome: pedals, castors, hinges, cheek caps over the noses, a pointed "
                 "lock plate on the key slip", "M"),
                ],
         cost="Triangles: about +0.4k (lock plate and two cheek caps; the rest is a material swap). "
              "Textures: one new 2048 x 1024 front-of-case texture (upper field, fallboard face and lower field at "
              "0.6 to 2 mm per texel, enough for sharp needle points in the close-up), its alpha the silver mask. "
              "About +0.5 MB as KTX2, +0 draw calls.",
         ),
    dict(n=3, name="Full", sub="Medium, plus cheeks, consoles, lid edge, bench, silver key fronts",
         items=[("Blades down both consoles: the references' own vertical sweep, root under the cheek", "T"),
                ("A short sweep and a hook on each key cheek's flat front, below the nose", "T"),
                ("The lid's front edge: a thin running sweep with small points (the sheet hides the middle)", "T"),
                ("Bench: the emblem and wings at half size on the front apron", "T"),
                ("Silver fronts on the 52 white keys (vertex colour on the key material, so +0 draw calls; "
                 "a material slot would add 52)", "M")],
         cost="Triangles: the same +0.4k. Textures: the front texture doubles to 4096 x 1024 (cheeks, consoles, "
              "bench apron), plus a 4096 x 64 strip in the lid's bake for the edge. About +1.1 MB in all, "
              "+0 draw calls.",
         ),
]


def column(i, lv):
    cw, top = 1152, 112
    x0 = 40 + i * (cw + 16)
    D.panel(x0, top, cw, 1540, f"{lv['n'] - 1} · {lv['name']}")
    text(x0 + 16 + 14 * len(lv["name"]) + 46, top + 30, lv["sub"], 15, MUTED)
    if lv["n"] == 2:
        add(f'<rect x="{x0 + cw - 150}" y="{top + 12}" width="134" height="26" rx="13" fill="{ACC}"/>')
        text(x0 + cw - 83, top + 30, "recommended", 14, "#fff", "middle", 600)
    # elevation on the dawn wall and oak floor
    ex0, ey0, ew, eh = x0 + 14, top + 48, cw - 28, 790
    floor_y = ey0 + eh - 34
    add(f'<rect x="{ex0}" y="{ey0}" width="{ew}" height="{eh}" fill="url(#wall)"/>')
    add(f'<rect x="{ex0}" y="{floor_y}" width="{ew}" height="34" fill="#3e281a"/>')
    v = D.View(x0 + cw / 2, floor_y, 0.58)
    piano(v, lv["n"], REC_EMB, (ex0, ey0, ex0 + ew, ey0 + eh))
    text(ex0 + 10, floor_y + 22, "Front elevation, fallboard open, lid closed, 0.58 px per mm. Same scale in both. "
         "Emblem shown: 3, the tuning fork (see 3 for all three).", 13, "#d8cfc2")
    # close-ups
    cy0, chh = ey0 + eh + 14, 440
    if lv["n"] == 2:
        crop((ex0, cy0, ew, chh), (-0.27, 0.79, 0.745, 1.150), 2, REC_EMB,
             label="Close-up: the fallboard emblem and the right arm, behind and beside the music")
    else:
        hw2 = (ew - 12) / 2
        crop((ex0, cy0, hw2, chh), (0.36, 0.785, 0.985, 1.230), 3, REC_EMB,
             label="Lid edge and the arm's needle")
        crop((ex0 + hw2 + 12, cy0, hw2, chh), (0.40, 0.785, 0.40, 0.835), 3, REC_EMB,
             label="Cheek, console, silver key fronts")
    # list
    ly = cy0 + chh + 34
    chars = 112 if lv["n"] == 2 else 92
    if lv["n"] == 3:
        text(x0 + 16, ly, "Everything in Medium, plus:", 14, MUTED, weight=600)
        ly += 22
    for s_, tg in lv["items"]:
        add(f'<rect x="{x0 + 16}" y="{ly - 13}" width="22" height="18" rx="3" fill="{ {"G": "#3d5a80", "T": "#6e737c", "M": "#3c3c3c"}[tg] }"/>')
        text(x0 + 27, ly + 1, tg, 12, "#fff", "middle", 700)
        ly = wrap(x0 + 46, ly, s_, chars, 14, INK, 18) + 4
    ly += 6
    wrap(x0 + 16, ly, "Cost: " + lv["cost"], chars + 4, 14, INK, 19)
    if lv["n"] == 3:
        bx0, by0 = x0 + cw - 280, cy0 + chh + 14
        add(f'<rect x="{bx0}" y="{by0}" width="266" height="200" fill="url(#wall)"/>')
        add(f'<rect x="{bx0}" y="{by0 + 176}" width="266" height="24" fill="#3e281a"/>')
        draw_bench(D.View(bx0 + 133, by0 + 176, 0.32), 3, REC_EMB)
        text(bx0 + 8, by0 + 18, "Bench, front, 0.32", 12, "#3a4152")


def emblems_row():
    y0, h = 1668, 640
    D.panel(40, y0, 2320, h, "3 · The centre emblem: three to choose from, same strokes, same size (about 10 cm tall)")
    tw = (2320 - 32 - 2 * 16) / 3
    for k, E in enumerate(EMBLEMS):
        x0 = 56 + k * (tw + 16)
        cy = y0 + 50
        add(f'<rect x="{x0:.1f}" y="{cy}" width="{tw:.1f}" height="560" fill="#0a0a0c" rx="3"/>')
        # large, alone
        v = D.View(x0 + 190, cy + 205, 2.45)
        L = Layer()
        E["fn"]().emit(L, v, lambda x, y: (x, y))
        L.flush()
        text(x0 + 16, cy + 30, f"{k + 1} · {E['name']}", 18, "#eeeae2", weight=600)
        if k == REC_EMB:
            add(f'<rect x="{x0 + tw - 150:.1f}" y="{cy + 12}" width="134" height="26" rx="13" fill="{ACC}"/>')
            text(x0 + tw - 83, cy + 30, "recommended", 14, "#fff", "middle", 600)
        wrap(x0 + 380, cy + 80, E["note"], 44, 14, "#d9d4cb", 20)
        text(x0 + 380, cy + 320, "2.45x, on lacquer", 12, "#8f8a80")
        # in place: the fallboard face with wings, 1x
        crop((x0 + 12, cy + 352, tw - 24, 196), (-0.37, 0.37, 0.745, 0.985), 2, k,
             label="On the fallboard with its wings, 1.0x", bg="#070709")


def motif_strip():
    y0, h = 2324, 548
    x0, w = 40, 1530
    D.panel(x0, y0, w, h, "4 · The motif language: four parts, one rule, two metals")
    cells = 6
    cw = (w - 32 - (cells - 1) * 12) / cells
    cy = y0 + 50
    titles = ["Blade", "Hook", "Teardrop cut-out", "Symmetry rule", "Turned horizontal", "Silver and chrome"]
    notes = [
        ["A centreline that swells and", "runs out to a needle. Concave", "sides; flame points leave the",
         "spine at 40 to 60° and bend", "back toward the flow."],
        ["A blade whose turn gathers at", "the tip: 150 to 170° in the last", "third. Used where a stroke",
         "should end looking back at the", "centre (cheeks, corners)."],
        ["Round head toward the centre,", "tail toward the tip. A chain of", "them in every wide part, about",
         "half its width, alternating a", "little either side."],
        ["Draw one half, mirror it about", "the piano's centreline. Every", "stroke runs outward from the",
         "emblem: the needle is always", "the end farthest from it."],
        ["The references stand tall. The", "piano is wide, so the axis turns", "90°: the emblem drops to the",
         "fallboard, the two arms open", "sideways behind the music."],
        ["Inlay: brushed silver under the", "clear coat, flat in the bake.", "Hardware: polished chrome.",
         "Nickel is the warmer option.", "No gold anywhere."],
    ]
    for c in range(cells):
        cx0 = x0 + 16 + c * (cw + 12)
        add(f'<clipPath id="mc{c}"><rect x="{cx0:.1f}" y="{cy}" width="{cw:.1f}" height="300" rx="3"/></clipPath>')
        add(f'<rect x="{cx0:.1f}" y="{cy}" width="{cw:.1f}" height="300" fill="#0a0a0c" rx="3"/><g clip-path="url(#mc{c})">')
        L = Layer()
        if c == 0:
            v = D.View(cx0 + 22, cy + 175, 1.9)
            m = Piece()
            sp = arc(0, 0, 8, 0.105, plus(wave(12), turn(-6, 2)), n=120)
            wf = spindle(0.020, 0.32)
            m.stroke(sp, wf)
            m.flame(sp, wf, 0.30, 1, 55, 0.045, 60)
            m.flame(sp, wf, 0.42, -1, 50, 0.035, 55)
            m.emit(L, v, lambda x, y: (x, y))
            L.flush()
            text(cx0 + 18, cy + 104, "flame point", 12, "#9da2ab")
            text(cx0 + cw - 16, cy + 214, "needle", 12, "#9da2ab", "end")
            text(cx0 + 18, cy + 222, "root", 12, "#9da2ab")
        elif c == 1:
            v = D.View(cx0 + 40, cy + 230, 2.2)
            m = Piece()
            m.stroke(arc(0, 0, 55, 0.085, turn(-165, 1.6), n=120), spindle(0.020, 0.22))
            m.emit(L, v, lambda x, y: (x, y))
            L.flush()
        elif c == 2:
            v = D.View(cx0 + 14, cy + 150, 1.8)
            m = Piece()
            sp = arc(0, 0, 0, 0.115, wave(10), n=120)
            wf = spindle(0.034, 0.34)
            m.stroke(sp, wf)
            m.cut(sp, wf, 0.10, 0.34, 0.50, 0.04)
            m.cut(sp, wf, 0.36, 0.56, 0.48, -0.05)
            m.cut(sp, wf, 0.58, 0.74, 0.40, 0.03)
            m.emit(L, v, lambda x, y: (x, y))
            L.flush()
            text(cx0 + 18, cy + 262, "head inward, tail outward", 12, "#9da2ab")
        elif c == 3:
            mx = cx0 + cw / 2
            v = D.View(mx, cy + 150, 0.56)
            m = wing()
            m.emit(L, v, lambda x, y: (x + 0.017, y))
            L.flush()
            m.emit(L, v, lambda x, y: (-x - 0.017, y))
            L.flush(fill="#3a3d44")
            add(f'<line x1="{mx}" y1="{cy + 30}" x2="{mx}" y2="{cy + 280}" stroke="{ACC}" stroke-width="1.2" '
                f'stroke-dasharray="6 5"/>')
            text(mx + 8, cy + 44, "drawn", 12, "#9da2ab")
            text(mx - 8, cy + 44, "mirrored", 12, "#9da2ab", "end")
        elif c == 4:
            # tall: our arm stood up (top, bottom mirrored about an emblem); wide: turned
            v = D.View(cx0 + 36, cy + 150, 0.27)
            m, _, _ = arm(0.46, 0.034, rise=-4, sway=9,
                          flames=[(0.3, 1, 52, 0.2, 60), (0.45, -1, 50, 0.17, 60), (0.6, 1, 44, 0.12, 50)])
            m.emit(L, v, place(0, 0.02, rot=90))
            m.emit(L, v, place(0, -0.02, rot=-90))
            L.flush()
            v.circle(0, 0, 0.012, "#cfd2d8", "none", 0)
            add(f'<path d="M{cx0 + 66},{cy + 150} h30" stroke="{ACC}" stroke-width="2" marker-end="url(#arr)"/>')
            v2 = D.View(cx0 + 172, cy + 150, 0.145)
            m.emit(L, v2, place(0.03, 0.0))
            m.emit(L, v2, place(-0.03, 0.0, mx=-1))
            L.flush()
            v2.circle(0, 0, 0.014, "#cfd2d8", "none", 0)
            text(cx0 + 16, cy + 288, "reference format", 12, "#9da2ab")
            text(cx0 + cw - 12, cy + 288, "on the piano", 12, "#9da2ab", "end")
        elif c == 5:
            sw_ = [("Lacquer", LACQ, LACQ), ("Inlay silver, brushed", SILVER, "url(#silver)"),
                   ("Chrome, polished", CHROME, "url(#chrome)"), ("Nickel (alternative)", NICKEL, "url(#nickel)"),
                   ("Ivory keys", C.COL["ivory"], C.COL["ivory"]), ("Red felt", C.COL["felt_red"], C.COL["felt_red"])]
            for j, (lab, col, fill) in enumerate(sw_):
                yy = cy + 14 + j * 47
                add(f'<rect x="{cx0 + 12}" y="{yy}" width="54" height="34" rx="3" fill="{fill}" stroke="#3a3a40"/>')
                text(cx0 + 76, yy + 15, lab, 13, "#e8e4dc", weight=600)
                text(cx0 + 76, yy + 31, col, 12, "#bdb6a8")
        add("</g>")
        text(cx0, cy + 326, titles[c], 15, INK, weight=600)
        for k, ln in enumerate(notes[c]):
            text(cx0, cy + 348 + k * 18, ln, 13, MUTED)
    yy = cy + 460
    wrap(x0 + 16, yy, "Texture, not relief: the inlays lie flush under the clear coat, so the lacquer's reflection runs "
         "unbroken across them, which is what makes an inlay read as an inlay. Relief would need a normal map "
         "(about +1 MB), about +8k triangles, and would break that reflection line. Hardware is material only.",
         200, 14, INK, 19)


def recommendation():
    x0, y0, w, h = 1584, 2324, 776, 548
    D.panel(x0, y0, w, h, "5 · Recommendation: Medium, with the tuning fork")
    y = y0 + 62
    pts = [
        "Medium keeps it an instrument. The sweep, the emblem and four corners sit on three panels; every "
        "black field stays mostly open and the silhouette does not change. Full puts silver on almost every "
        "face and the piano starts to read as a tattoo flash sheet.",
        "Full's silver key fronts fight the ivory, and its console blades sit at floor level where the "
        "camera seldom goes. Its best part, the lid edge, is mostly behind the music.",
        "The tuning fork is ours and says piano before it says tattoo; it also suits the room's evolution of "
        "music. The skull is the strong alternative if the owner wants the references' attitude, and it "
        "carries the most character at room distance. The heart is the quietest.",
        "Silver from 5:40 light: brushed, not polished. A polished inlay under the clear coat goes mirror-dark "
        "in a dim room and only flashes; brushed scatters the blue window, so the strokes read light grey "
        "from every angle. Chrome on the hardware gives the flashes instead.",
    ]
    for s_ in pts:
        add(f'<circle cx="{x0 + 22}" cy="{y - 5}" r="3" fill="{ACC}"/>')
        y = wrap(x0 + 34, y, s_, 98, 14, INK, 19) + 8
    y += 2
    text(x0 + 16, y, "Spec", 14, INK, weight=600)
    y += 20
    for s_ in ("Inlay: brushed sterling silver #b7bbc2, metallic 1, roughness 0.35 (Blender), under the case's clear coat.",
               "In the browser: the silver is colour in the bake; the texture's alpha lets the lacquer's small reflection map",
               "add a faint sheen to it. Hardware: polished chrome #d4d7dc, metallic 1, roughness 0.06, same reflection map.",
               "No new meshes and no new names in MESHES.md: piano_static, piano_fallboard, piano_lid only."):
        text(x0 + 16, y, s_, 13, MUTED)
        y += 18
    y += 10
    wrap(x0 + 16, y, "Henson guitar: on a fretboard the composition stands up again, its native format: the emblem at "
         "the 12th fret, one arm toward the nut and one toward the body, teardrops as the negative space, silver "
         "in the dark board at about 0.4x these strokes.", 100, 13.5, INK, 18)


def defs():
    add('<defs><linearGradient id="gloss" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".12"/>'
        '<stop offset=".35" stop-color="#fff" stop-opacity="0"/><stop offset=".62" stop-color="#9fb8e8" stop-opacity=".07"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c3c9d8"/>'
        '<stop offset="1" stop-color="#a7afc2"/></linearGradient>'
        f'<linearGradient id="silver" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="180" y2="120" spreadMethod="reflect">'
        f'<stop offset="0" stop-color="{SILVER_HI}"/>'
        f'<stop offset=".5" stop-color="{SILVER}"/><stop offset="1" stop-color="{SILVER_LO}"/></linearGradient>'
        f'<linearGradient id="silverv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{SILVER_HI}"/>'
        f'<stop offset="1" stop-color="{SILVER_LO}"/></linearGradient>'
        '<linearGradient id="chrome" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="#f6f8fa"/>'
        '<stop offset=".38" stop-color="#9ba0a8"/><stop offset=".55" stop-color="#e9ecef"/>'
        '<stop offset="1" stop-color="#5d626b"/></linearGradient>'
        '<linearGradient id="nickel" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="#f3eee4"/>'
        '<stop offset=".38" stop-color="#a49c8d"/><stop offset=".55" stop-color="#e4ddcf"/>'
        '<stop offset="1" stop-color="#655e52"/></linearGradient>'
        f'<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{ACC}"/></marker></defs>')


def build():
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_PX}" height="{H_PX}" viewBox="0 0 {W_PX} {H_PX}" '
        f'font-family="-apple-system, Helvetica Neue, Arial, sans-serif">')
    defs()
    add(f'<rect width="{W_PX}" height="{H_PX}" fill="{PAPER}"/>')
    text(48, 58, "Upright piano · tribal ornament in silver", 32, INK, weight=650)
    text(48, 86, "obj_piano, style A (polished black) with tattoo-style tribal strokes of our own in brushed silver, "
         "chrome hardware, no gold. Two levels, three centre emblems, on the approved piano, dimensions unchanged. "
         "T texture · M material", 16, MUTED)
    text(W_PX - 48, 58, "2026-10-22 · for the owner's choice, before the 3D rebuild", 15, MUTED, "end")
    for i, lv in enumerate(LEVELS):
        column(i, lv)
    emblems_row()
    motif_strip()
    recommendation()
    add("</svg>")


def main():
    os.makedirs(OUT, exist_ok=True)
    D.out.clear()
    build()
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>Piano tribal sheet</title>"
            f"<style>html,body{{margin:0;background:{PAPER}}}svg{{display:block}}</style></head><body>"
            + "\n".join(D.out) + "</body></html>")
    hp = os.path.join(OUT, "piano-tribal-sheet.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    png = os.path.join(OUT, "piano-tribal-sheet.png")
    subprocess.run([D.CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={W_PX},{H_PX}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", hp, png)


if __name__ == "__main__":
    main()
