"""The desk-top group (component, 2026-10-26): Universal Audio Apollo x4 Gen 2 silver, Keychron Q1 Max white,
Logitech MX Master 3S pale grey, Elgato Stream Deck MK.2 white on its stand. Exact replicas in shape and finish
from the reference photos and official sizes in docs/moodboard/local/ai-lab/{10-audio-interface,22-keyboard,
23-mouse,24-control-pad}/ (SOURCES.md). Started from tools/component_template.py, arms.py as the pattern.

Always headless:

    DESKTOP_PART=interface|keyboard|mouse|streamdeck|all \\
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/components/desktop.py -- [stages] [--cycles]

stages: outline | build,stills,compare,closeups,export (default) | any comma list.
Plain Python (Pillow): python3 desktop.py --cutouts | --pairs <pairs.json> <dir>

Each part is built in its own frame: origin on the desk under the part's centre, front (the user's side) -Y.
The room turns them by plan v3's yaw (90: front to +X). Brand names from content/room-brands.json via
lib/brands.py (decision 2026-10-26), at the real logo's spot, size, colour and finish.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(BLENDER_DIR, ".."))
sys.path.insert(0, BLENDER_DIR)
sys.path.insert(0, os.path.join(BLENDER_DIR, "tools"))

try:
    import bpy
    from mathutils import Matrix, Vector
except ImportError:
    bpy = None

PART = os.environ.get("DESKTOP_PART", "all")
PARTS = ("interface", "keyboard", "mouse", "streamdeck")
NAME = "desktop" if PART == "all" else f"desktop_{PART}"
MM = 0.001
AI = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab")
R_IF = os.path.join(AI, "10-audio-interface")
R_KB = os.path.join(AI, "22-keyboard")
R_MS = os.path.join(AI, "23-mouse")
R_SD = os.path.join(AI, "24-control-pad")
FOOT = os.path.join(REPO, "video-local", "footage", "2026-10-26-components", "desktop")
CUT = os.path.join(FOOT, "cutouts")

# ---------------------------------------------------------------------------
# 1. numbers (mm unless said), each tagged OFFICIAL / MEASURED / EST
# ---------------------------------------------------------------------------
# Apollo x4 Gen 2 (10-audio-interface/SOURCES.md)
IF_W, IF_D, IF_H = 232.98, 149.13, 65.81      # OFFICIAL (retailer spec, Adorama/Thomann)
IF_FEET = 3.0                                 # EST: four rubber feet
IF_ZF = 28.0                                  # MEASURED gen2-silver-three-quarter-front: the front lip top
IF_STRIP = (4.0, 25.0)                        # MEASURED 3q front: the black front strip, bottom and top
IF_R_BACK = 16.0                              # MEASURED gen2-silver-back: the rounded back-top edge with the vents
IF_KNOB = (39.5, 2.0, 22.4, 14.0)            # MEASURED gen2-silver-top (0.345 mm/px): x, y, radius, height (EST)
IF_WIN = (-76.1, 10.0, -16.3, 18.2)           # MEASURED top: the meter window x0, x1, y0, y1
IF_RING_R = 35.0                              # MEASURED top: the black ring round the knob
IF_BTN_Y = -33.9                              # MEASURED top: the six small buttons and PREAMP / MONITOR
IF_BTN_X = (-67.8, -55.7, -43.6, -31.5, -19.4, -7.1)
IF_BTN2_X = (22.6, 56.1)
IF_BTN = (10.4, 4.8)
IF_JACKS = (-94.8, -69.2, 68.2, 93.7)        # MEASURED 3q front: instrument 1, 2 and headphones 1, 2
IF_JACK_Z = 15.5
IF_PROTRUDE = 6.47                            # OFFICIAL: 155.60 deep with knob and jacks, less 149.13

# Keychron Q1 Max (22-keyboard/SOURCES.md, Keychron "Precision Specs")
KB_W, KB_D = 327.5, 145.0                     # OFFICIAL
KB_HF, KB_HB = 20.7, 31.8                     # OFFICIAL front and back height without keycaps
KB_FEET = 2.4                                 # OFFICIAL
KB_ANGLE = 5.2                                # OFFICIAL typing angle (the plate and keys)
KB_U = 19.05                                  # the key unit
KB_TOP_BEZEL = 13.1                           # MEASURED variant-assembled-white-brown (0.682 mm/px)
KB_SIDE_BEZEL = (KB_W - 16.25 * KB_U) / 2     # 8.9 MEASURED the same photo (16.25 u wide: a 0.25 u gap before the nav column)
KB_SPLIT = 14.5                               # MEASURED review-tr-rear: the top case meets the bottom case
KB_WELL = 6.0                                 # EST: the plate below the frame's top
KB_CAP_H = 11.5                               # EST: KSA spherical caps, uniform rows
KB_SWITCH = 6.5                               # EST: cap bottom above the plate (switch housing and stem)
KB_ARROW_DROP = 0.2                           # MEASURED top photo: the arrow cluster sits a little lower
WHITE, GREY, GREEN = "w", "g", "e"
KB_ROWS = [     # (row y in u, [(id, x in u, width in u, colour)]) MEASURED from the white-variant photos
    (0.0, [("esc", 0, 1, GREEN)] + [(f"f{i}", 1.25 + (i - 1) + 0.25 * ((i - 1) // 4), 1, GREY if 5 <= i <= 8 else WHITE)
                                    for i in range(1, 13)] + [("del", 14.0, 1, GREY)]),
    (1.25, [("grave", 0, 1, GREY)] + [(f"n{d}", 1 + i, 1, WHITE) for i, d in enumerate("1234567890")]
     + [("minus", 11, 1, WHITE), ("equal", 12, 1, WHITE), ("backspace", 13, 2, GREY), ("pgup", 15.25, 1, GREY)]),
    (2.25, [("tab", 0, 1.5, GREY)] + [(c, 1.5 + i, 1, WHITE) for i, c in enumerate("qwertyuiop")]
     + [("lbracket", 11.5, 1, WHITE), ("rbracket", 12.5, 1, WHITE), ("backslash", 13.5, 1.5, GREY), ("pgdn", 15.25, 1, GREY)]),
    (3.25, [("caps", 0, 1.75, GREY)] + [(c, 1.75 + i, 1, WHITE) for i, c in enumerate("asdfghjkl")]
     + [("semicolon", 10.75, 1, WHITE), ("quote", 11.75, 1, WHITE), ("enter", 12.75, 2.25, GREEN), ("home", 15.25, 1, GREY)]),
    (4.25, [("lshift", 0, 2.25, GREY)] + [(c, 2.25 + i, 1, WHITE) for i, c in enumerate("zxcvbnm")]
     + [("comma", 9.25, 1, WHITE), ("period", 10.25, 1, WHITE), ("slash", 11.25, 1, WHITE), ("rshift", 12.25, 1.75, GREY),
        ("up", 14.25, 1, WHITE)]),
    (5.25, [("lctrl", 0, 1.25, GREY), ("lopt", 1.25, 1.25, GREY), ("lcmd", 2.5, 1.25, GREY), ("space", 3.75, 6.25, WHITE),
            ("rcmd", 10, 1, GREY), ("fn", 11, 1, GREY), ("rctrl", 12, 1, GREY),
            ("left", 13.25, 1, WHITE), ("down", 14.25, 1, WHITE), ("right", 15.25, 1, WHITE)]),
]
KB_DROPPED = {"up", "left", "down", "right"}
KB_KNOB = (15.25, 0.0, 8.5, 9.0)              # MEASURED top photo: the knob in the nav column, row 0 (u, u, r mm, h above the frame EST)

# MX Master 3S (23-mouse/SOURCES.md): 124.9 long, 84.3 wide, 51 high OFFICIAL
MS_L, MS_W, MS_H = 124.9, 84.3, 51.0
# MEASURED top.png alpha (0.0502 mm/px, the 124.9 length): the outline seen from above, (x, y), nose at -y
MS_OUTLINE = [
    (40.1, 2.5), (40.3, 5.7), (40.6, 8.9), (40.9, 12.3), (41.1, 15.9), (41.2, 19.6), (41.1, 23.7), (41.0, 28.1),
    (40.4, 32.6), (39.3, 37.3), (37.7, 42.1), (35.5, 46.8), (32.5, 51.1), (28.9, 54.8), (24.7, 57.9), (20.0, 60.4),
    (15.0, 61.9), (9.8, 62.5), (4.5, 62.0), (-0.6, 60.8), (-5.4, 58.7), (-9.9, 56.3), (-14.1, 53.7), (-18.1, 51.1),
    (-21.9, 48.4), (-25.8, 45.8), (-29.6, 43.2), (-33.3, 40.4), (-36.7, 37.1), (-39.4, 33.3), (-40.9, 28.8),
    (-41.2, 23.8), (-40.8, 19.0), (-40.2, 14.5), (-39.5, 10.3), (-38.9, 6.3), (-38.2, 2.5), (-37.6, -1.1),
    (-36.7, -4.7), (-35.4, -8.1), (-32.9, -11.1), (-29.2, -13.2), (-25.4, -14.7), (-22.7, -16.5), (-20.9, -18.8),
    (-20.3, -22.2), (-18.0, -24.3), (-16.6, -27.7), (-16.5, -33.8), (-16.2, -41.9), (-15.6, -52.9), (-12.2, -59.8),
    (-6.9, -62.2), (-1.1, -62.0), (4.5, -61.1), (10.0, -60.1), (15.3, -58.9), (20.6, -57.5), (25.7, -55.8),
    (30.8, -53.8), (35.2, -50.6), (37.9, -45.1), (39.0, -38.5), (39.6, -32.5), (40.1, -27.3), (40.3, -22.5),
    (40.4, -18.2), (40.6, -14.3), (40.6, -10.6), (40.5, -7.1), (40.4, -3.8), (40.1, -0.6)]
MS_WHEEL = (11.4, -37.0, 11.0, 7.0)           # MEASURED top.png: centre x, y; radius EST from the 17.6 visible chord; width
MS_SLOT = (8.4, 19.2)                         # MEASURED top.png: the wheel's dark slot
MS_MID = (11.6, -13.3, 5.9, 9.0)              # MEASURED top.png: the mode-shift button
MS_LOGO = (-9.1, -20.0, 12.0)                 # MEASURED top.png: "logi" centre x, y, turn (deg)
MS_THUMB = (-15.5, -1.6, 9.0, 10.0)           # MEASURED top.png: the thumb wheel centre x, y; radius, width EST
MS_PEAK = 0.62                                # EST from side-thumb-profile: the hump's top along the length

# Stream Deck MK.2 (24-control-pad/SOURCES.md)
SD_W, SD_D, SD_T = 118.0, 84.0, 18.0          # W x D OFFICIAL; T MEASURED gallery-01 / desk-white-lowangle (the official 25 does not match the photos)
SD_TILT = 46.0                                # EST: makes the 76 mm height with the stand (retailer, UNSURE)
SD_KEY = 17.5                                 # MEASURED hero-white-with-faceplates (0.50 mm/px)
SD_PITCH = 21.5                               # MEASURED the same photo
SD_ROW0 = 15.5                               # MEASURED: the bottom row's centre above the face's bottom edge
SD_LIFT = (2.5, -30.0)                        # EST: the deck's front-bottom edge above the desk and its y
SD_ICONS = ["#7b4dff", "#9d5cff", "#25b7e8", "#ff8a2a", "#ff4d6d",
            "#2f6bff", "#1d2a7a", "#ffd23f", "#1fb5a5", "#5b2bd1",
            "#202024", "#202024", "#2ed3b7", "#2f6bff", "#3a6dff"]
SD_SHAPES = ["circle", "square", "triangle", "ring", "bars", "triangle", "circle", "ring", "square", "bars",
             "circle", "bars", "ring", "triangle", "square"]

DEMO = {"interface": (-0.40, 0.04, 0.0), "streamdeck": (-0.17, 0.06, 0.0), "keyboard": (0.12, -0.02, 0.0),
        "mouse": (0.38, -0.02, 0.0)}


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def mats():
    from lib import materials as M
    from lib import parts as P
    p = dict(P.palette())

    def get(n, **v):
        return bpy.data.materials.get(n) or M.principled(n, **v)
    p["if_silver"] = get("mat_desktop_apollo_silver", base="#cfd1d4", rough=0.38, metal=0.9)
    p["if_strip"] = get("mat_desktop_apollo_strip", base="#121214", rough=0.5)
    p["if_glass"] = get("mat_desktop_apollo_glass", base="#050506", rough=0.06, spec=0.6, coat=1.0, coat_rough=0.03)
    p["if_knob"] = get("mat_desktop_apollo_knob", base="#d9dbde", rough=0.18, metal=1.0)
    p["if_btn"] = get("mat_desktop_apollo_button", base="#f1f1ef", rough=0.45)
    p["led_green"] = get("mat_desktop_led_green", base="#3bd16a", rough=0.4, emit="#21ff4e", emit_strength=1.3)
    p["led_dim"] = get("mat_desktop_led_off", base="#1c2a20", rough=0.4)
    p["led_orange"] = get("mat_desktop_led_orange", base="#ff9a2a", rough=0.4, emit="#ff8a10", emit_strength=1.3)
    p["led_red"] = get("mat_desktop_led_red", base="#ff3a2a", rough=0.4, emit="#ff2010", emit_strength=1.3)
    p["kb_case"] = get("mat_desktop_kb_case", base="#e9e8e3", rough=0.55, metal=0.0, spec=0.35)
    p["kb_pocket"] = get("mat_desktop_kb_pocket", base="#cfcec9", rough=0.6)
    p["kb_plate"] = get("mat_desktop_kb_plate", base="#232426", rough=0.6)
    p["cap_w"] = get("mat_desktop_kb_cap_white", base="#efede6", rough=0.62, spec=0.3)
    p["cap_g"] = get("mat_desktop_kb_cap_grey", base="#868b85", rough=0.62, spec=0.3)
    p["cap_e"] = get("mat_desktop_kb_cap_green", base="#62a58f", rough=0.62, spec=0.3)
    p["kb_knob"] = get("mat_desktop_kb_knob", base="#ecebe7", rough=0.35, metal=0.3)
    p["ms_top"] = get("mat_desktop_mouse_top", base="#e2e3e4", rough=0.62, spec=0.3)
    p["ms_side"] = get("mat_desktop_mouse_side", base="#c4c6c9", rough=0.3, metal=0.55)
    p["ms_line"] = get("mat_desktop_mouse_seam", base="#8c8e91", rough=0.6)
    p["ms_thumb"] = bpy.data.materials.get("mat_desktop_mouse_thumbrest") or thumbrest_material()
    p["ms_wheel"] = get("mat_desktop_mouse_wheel", base="#b8bbbf", rough=0.22, metal=1.0)
    p["ms_slot"] = get("mat_desktop_mouse_slot", base="#1a1b1d", rough=0.55)
    p["sd_white"] = get("mat_desktop_deck_white", base="#efefec", rough=0.5, spec=0.35)
    p["sd_key"] = get("mat_desktop_deck_key", base="#0b0b0d", rough=0.08, spec=0.6, coat=1.0, coat_rough=0.04)
    return p


def thumbrest_material():
    """Pale grey soft-touch with fine diagonal ridges (a bump map; ridge pitch about 1.5 mm)."""
    from lib import materials as M
    m = M.principled("mat_desktop_mouse_thumbrest", base="#e2e3e4", rough=0.62, spec=0.3)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type, wv.bands_direction = "BANDS", "DIAGONAL"
    wv.inputs["Scale"].default_value = 420.0
    wv.inputs["Distortion"].default_value = 0.0
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.5
    bp.inputs["Distance"].default_value = 0.0003
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def icon_mat(i, colour, strength=1.2):
    from lib import materials as M
    n = f"mat_desktop_deck_icon_{i:02d}"
    return bpy.data.materials.get(n) or M.principled(n, base="#050506", rough=0.2, emit=colour, emit_strength=strength)  # light only: a lit base went pastel


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(deg, axis):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def mm(*v):
    return tuple(x * MM for x in v)


def empty(name, parent=None, loc=(0, 0, 0), coll=None):
    from lib import names
    e = bpy.data.objects.new(name, None)
    (coll or bpy.context.scene.collection).objects.link(e)
    names.set_name(e, name, data=False)
    e.parent = parent
    e.location = loc
    e.empty_display_size = 0.03
    return e


def fin(A, name, mp, coll, parent, bevel=None, smooth=30):
    return A.finish(name, mp, "+Z", (0, 0, 0), coll, parent, bevel=bevel, smooth=smooth)


def box(A, x0, x1, y0, y1, z0, z1, key, m=None, r=0.0, n=0):
    from lib.parts import rrect
    o = rrect(x1 - x0, y1 - y0, r, n, (x0 + x1) / 2, (y0 + y1) / 2)
    A.prism(o, z0, z1, key, m=m)


def rloops(A, loops, key, cap_bottom=True, cap_top=True, m=None):
    """loops: [(z, outline)], same point counts; strips between, caps at the ends."""
    vs = [A.verts([(x, y, z) for x, y in o], m) for z, o in loops]
    for a, b in zip(vs, vs[1:]):
        A.strip(a, b, key)
    if cap_bottom:
        A.face(list(reversed(vs[0])), key)
    if cap_top:
        A.face(vs[-1], key)
    return vs


def flat_port(name, at, facing, coll, parent, mp, w=8.34, h=2.56):
    """The web model's USB-C: one dark stadium face on the surface."""
    from lib import parts as P
    A = P.Mesh()
    A.face(A.verts([(x, y, 0.15 * MM) for x, y in P.ccw(P.stadium(w * MM, h * MM, 3))]), "port")
    return A.finish(name, mp, facing, at, coll, parent, smooth=0)


def brand(key, parent, name, lite, at, normal, up, **kw):
    from lib import brands
    bpy.context.view_layer.update()
    d = brands.decal(key, at=at, normal=normal, up=up, parent=parent, lite=lite, name=name, **kw)
    if d is not None and lite:          # the web lettering: about half the triangles (planar decimate keeps the shapes)
        mod = d.modifiers.new("lite_letters", "DECIMATE")
        mod.decimate_type = "DISSOLVE"
        mod.angle_limit = math.radians(5)
    return d


# ---------------------------------------------------------------------------
# 2a. Apollo x4 Gen 2. Origin: desk under the chassis centre; front (jacks) -Y.
# ---------------------------------------------------------------------------
IF_SLOPE = None


def if_profile(n_arc=10):
    """The side profile (y, z) in mm: front strip, sloped top, the rounded back-top edge, the back."""
    yf, yb = -IF_D / 2, IF_D / 2
    r = IF_R_BACK
    yc = yb - r
    a1 = 90.0 + math.degrees(math.atan(if_slope()))
    zc = IF_ZF + (yc + r * math.cos(math.radians(a1)) - yf) * if_slope() - r * math.sin(math.radians(a1))
    pts = [(yf, IF_FEET), (yb, IF_FEET), (yb, zc)]
    for i in range(1, n_arc + 1):
        a = math.radians(a1 * i / n_arc)
        pts.append((yc + r * math.cos(a), zc + r * math.sin(a)))
    pts += [(yf + 1.5, IF_ZF - 0.2), (yf, IF_ZF - 1.6)]
    return pts, (yc, zc, r, a1)


def if_slope():
    """Rise of the top plate per mm toward the back, so the back-top edge reaches IF_H (OFFICIAL)."""
    r = IF_R_BACK
    s = 0.28
    for _ in range(40):       # solve: zc + r = IF_H with the arc tangent to the top line
        a1 = math.pi / 2 + math.atan(s)
        yc = IF_D / 2 - r
        zc = IF_ZF + (yc + r * math.cos(a1) + IF_D / 2) * s - r * math.sin(a1)
        s += (IF_H - (zc + r)) / 140.0
    return s


def if_top(x, y):
    """Matrix onto the sloped top plate at (x, y) mm (top-view position), local +Z its normal."""
    s = if_slope()
    z = IF_ZF + (y + IF_D / 2) * s
    return T(x * MM, y * MM, z * MM) @ R(math.degrees(math.atan(s)), "X")


def build_interface(coll, mp, rough=False, lite=False):
    from lib import parts as P
    sfx = "_lite" if lite else ""
    names = {}
    root = empty("apollo" + sfx, coll=coll)
    prof, (yc, zc, r, a1) = if_profile(4 if lite else 12)
    m = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))) @ T(0, 0, -IF_W / 2 * MM)
    A = P.Mesh()
    A.prism([(y * MM, z * MM) for y, z in prof], 0.0, IF_W * MM, "if_silver", m=m)
    body = fin(A, "apollo_body" + sfx, mp, coll, root, bevel=None if (lite or rough) else 0.0016)
    names["body"] = [body.name]
    if rough:
        A = P.Mesh()
        box(A, -IF_W / 2 * MM, IF_W / 2 * MM, (-IF_D / 2 - IF_PROTRUDE) * MM, -IF_D / 2 * MM, IF_STRIP[0] * MM,
            IF_STRIP[1] * MM, "if_strip")
        names["strip"] = [fin(A, "apollo_strip", mp, coll, root).name]
        return root, names
    seg = 12 if lite else 40
    # the black front strip, 1 mm proud, with its vent slots and four jacks
    A = P.Mesh()
    yf = -IF_D / 2
    box(A, -113.8 * MM, 113.8 * MM, (yf - 1.0) * MM, (yf + 2.0) * MM, IF_STRIP[0] * MM, IF_STRIP[1] * MM, "if_strip",
        r=0.0)
    if not lite:
        for i in range(26):
            x = -68 + i * 126 / 25                     # MEASURED 3q front: between instrument 2 and headphones 1
            box(A, (x - 0.9) * MM, (x + 0.9) * MM, (yf - 1.08) * MM, (yf - 0.9) * MM, 6.0 * MM, 10.5 * MM, "port",
                r=0.85 * MM, n=3)
    strip = fin(A, "apollo_strip" + sfx, mp, coll, root)
    names["strip"] = [strip.name]
    gold = {"steel": mp["gold"], "chrome": mp["gold"], "port": mp["port"]}
    L = P.Mesh()                                       # lite: every socket a flat ring and a dark well

    def disc(facing, at, r_out, r_in, ko, ki="port"):
        m = T(*at) @ P.orient(facing)                  # flat discs: no walls in the web model
        L.face(L.verts([(x, y, 0.3 * MM) for x, y in P.ccw(P.circle(r_out * MM, 10))], m), ko)
        L.face(L.verts([(x, y, 0.35 * MM) for x, y in P.ccw(P.circle(r_in * MM, 8))], m), ki)
    for i, x in enumerate(IF_JACKS if lite else ()):
        disc("-Y", mm(x, yf - 1.0, IF_JACK_Z), 6.4, 3.3, "gold")
    for i, x in enumerate(() if lite else IF_JACKS):
        j = P.port(f"apollo_jack_{i + 1}{sfx}", "jack_635", lite=lite, mats=gold, facing="-Y",
                   at=mm(x, yf - 1.0, IF_JACK_Z), collection=coll, parent=root)
        names.setdefault("jacks", []).append(j.name)
    # the top: meter window (black glass), the ring round the knob, LEDs, knob, buttons, talkback hole
    x0, x1, y0, y1 = IF_WIN
    kx, ky, kr, kh = IF_KNOB
    A = P.Mesh()
    s = if_slope()
    ang = math.atan(s)

    def on_top(pts, h, key):
        """A flat piece on the sloped plate: outline in top-view mm, `h` mm proud."""
        lo = [((x * MM), (y * MM) / math.cos(ang)) for x, y in pts]
        A.prism(lo, -0.3 * MM, h * MM, key, bottom=False, m=T(0, 0, IF_ZF * MM) @ T(0, -IF_D / 2 * MM, 0) @ R(math.degrees(ang), "X")
                @ T(0, IF_D / 2 * MM / math.cos(ang), 0))
    Rr = IF_RING_R
    xb = kx - math.sqrt(Rr ** 2 - (y0 - ky) ** 2)          # where the window's bottom and top edges meet the circle
    xt = kx - math.sqrt(Rr ** 2 - (y1 - ky) ** 2)
    a0 = math.atan2(y0 - ky, xb - kx) % (2 * math.pi)
    a1 = math.atan2(y1 - ky, xt - kx) % (2 * math.pi) + 2 * math.pi
    na = 20 if lite else 72
    cr = 2.0
    shape = [(xb, y0)] + [(kx + Rr * math.cos(a0 + (a1 - a0) * i / na), ky + Rr * math.sin(a0 + (a1 - a0) * i / na))
                          for i in range(1, na)] + [(xt, y1)]
    for cx_, cy_, a_s in ((x0 + cr, y1 - cr, 90), (x0 + cr, y0 + cr, 180)):     # the window's two left corners
        shape += [(cx_ + cr * math.cos(math.radians(a_s + 90 * k / 3)), cy_ + cr * math.sin(math.radians(a_s + 90 * k / 3)))
                  for k in range(4)]
    on_top(shape, 0.15, "if_glass")                    # MEASURED gen2-silver-top: one black window round the knob
    nr = 24 if lite else 72
    A.ring_face(P.circle(26.0 * MM, nr, kx * MM, ky * MM / math.cos(ang)), P.circle(kr * MM + 0.2 * MM, nr, kx * MM, ky * MM / math.cos(ang)),
                0.17 * MM, "if_silver", m=T(0, 0, IF_ZF * MM) @ T(0, -IF_D / 2 * MM, 0) @ R(math.degrees(ang), "X")
                @ T(0, IF_D / 2 * MM / math.cos(ang), 0))
    on_top(P.circle(1.0, 12, 38.2, -27.3), 0.05, "port")            # the talkback mic hole (MEASURED top)
    win = fin(A, "apollo_meter_window" + sfx, mp, coll, root)
    names["window"] = [win.name]
    A = P.Mesh()
    lit = 26
    n_ring = 31
    for i in range(n_ring):               # the LED ring: lit from 200 deg over the top to -25, dark below
        a = math.radians(200 - i * 275 / (n_ring - 1))
        cxp, cyp = kx + 30.5 * math.cos(a), ky + 30.5 * math.sin(a)
        rr = Matrix.Rotation(a, 4, "Z")
        o = [(cxp + (rr @ Vector((px, py, 0))).x, cyp + (rr @ Vector((px, py, 0))).y)
             for px, py in P.rrect(3.6, 1.3, 0.3, 0 if lite else 2)]
        on_top(o, 0.22, "led_green" if i < lit else "led_dim")
    cols = [-72.5, -65.5, -58.5, -51.5, -34.0, -24.5, -15.0]          # CH1-4, HP1, HP2, MONITOR (MEASURED top)
    for ci, cx in enumerate(cols if lite else ()):
        for b in (0, 1):
            on_top(P.rrect(2.6, 17.4, 0.0, 0, cx + b * 3.2, 1.5), 0.22, "led_green")
            on_top(P.rrect(2.6, 1.4, 0.0, 0, cx + b * 3.2, 5.5 + 4.0), 0.24, "led_orange")
    for ci, cx in enumerate(() if lite else cols):
        for b in (0, 1):
            for rw in range(5):
                yy = 9.5 - rw * 4.0
                key = "led_red" if (rw == 0 and ci in (1, 2)) else "led_orange" if rw == 1 else (
                    "led_green" if rw >= 2 else "led_dim")
                on_top(P.rrect(2.6, 1.4, 0.0, 0, cx + b * 3.2, yy), 0.22, key)
    leds = fin(A, "apollo_leds" + sfx, mp, coll, root, smooth=0)
    names["leds"] = [leds.name]
    kn = P.knob("apollo_knob" + sfx, kr * MM, kh * MM, chamfer=0.7 * MM, seg=24 if lite else 96, lite=lite,
                mats={"knob": mp["if_knob"], "skirt": mp["if_knob"]}, facing="+Z", collection=coll, parent=root)
    kn.matrix_basis = if_top(kx, ky) @ T(0, 0, 0.15 * MM)
    names["knob"] = [kn.name]
    for i, x in enumerate(IF_BTN_X + IF_BTN2_X):
        if lite:                                        # the web model: a plain cap
            B_ = P.Mesh()
            box(B_, -IF_BTN[0] / 2 * MM, IF_BTN[0] / 2 * MM, -IF_BTN[1] / 2 * MM, IF_BTN[1] / 2 * MM, 0.0, 1.4 * MM, "if_btn")
            b = B_.finish(f"apollo_button_{i + 1}{sfx}", mp, "+Z", (0, 0, 0), coll, root, smooth=0)
            b.matrix_basis = if_top(x, IF_BTN_Y)
            names.setdefault("buttons", []).append(b.name)
            continue
        b = P.push_button(f"apollo_button_{i + 1}{sfx}", size=mm(*IF_BTN), height=1.4 * MM, bezel=0.5 * MM,
                          r_corner=2.2 * MM, lite=lite, mats={"cap": mp["if_btn"], "bezel": mp["if_silver"],
                                                               "port": mp["port"]}, facing="+Z", collection=coll,
                          parent=root)
        b.matrix_basis = if_top(x, IF_BTN_Y)
        names.setdefault("buttons", []).append(b.name)
    # the back: vents over the rounded edge, ports, screws, feet
    A = P.Mesh()
    if not lite:
        for i in range(34):
            x = -105 + i * 210 / 33
            ring_a, ring_b = [], []
            for k in range(9):
                a = math.radians(14 + (a1 - 34) * k / 8)
                yy, zz = yc + (r + 0.05) * math.cos(a), zc + (r + 0.05) * math.sin(a)
                ring_a.append((x - 1.4, yy, zz))
                ring_b.append((x + 1.4, yy, zz))
            va = A.verts([mm(*p) for p in ring_a])
            vb = A.verts([mm(*p) for p in ring_b])
            for k in range(8):
                A.face([va[k], va[k + 1], vb[k + 1], vb[k]], "port")
    else:
        for i in range(34):
            x = -105 + i * 210 / 33
            a = math.radians(14 + (a1 - 34) / 2)
            ring = []
            for k in (0, 1):
                ak = math.radians(14 + (a1 - 34) * k)
                ring.append((yc + (r + 0.05) * math.cos(ak), zc + (r + 0.05) * math.sin(ak)))
            va = A.verts([mm(x - 1.4, *ring[0]), mm(x - 1.4, *ring[1])])
            vb = A.verts([mm(x + 1.4, *ring[0]), mm(x + 1.4, *ring[1])])
            A.face([va[0], va[1], vb[1], vb[0]], "port")
    yb = IF_D / 2
    for x, z in ((99.6, 34.6), (87.1, 34.6)):                # optical out, in (MEASURED back)
        box(A, (x - 4.5) * MM, (x + 4.5) * MM, (yb - 0.2) * MM, (yb + 0.9) * MM, (z - 4.5) * MM, (z + 4.5) * MM,
            "black", r=0.8 * MM, n=2)
        box(A, (x - 2.2) * MM, (x + 2.2) * MM, (yb + 0.9) * MM, (yb + 0.95) * MM, (z - 2.2) * MM, (z + 2.2) * MM, "port")
    box(A, 86.5 * MM, 100.5 * MM, (yb - 0.2) * MM, (yb + 1.6) * MM, 14.0 * MM, 21.5 * MM, "black", r=0.6 * MM, n=2)
    box(A, 93.6 * MM, 99.5 * MM, (yb + 1.6) * MM, (yb + 2.6) * MM, 14.8 * MM, 20.7 * MM, "rubber")
    vents = fin(A, "apollo_back" + sfx, mp, coll, root, smooth=0)
    names["back"] = [vents.name]
    ports = [("usb_c", 72.7, 31.7), ("dc_barrel", 72.0, 19.0)]
    ports += [("jack_635", x, z) for x in (52.6, 35.7, 18.5) for z in (36.4, 19.2)]
    ports += [("xlr_combo", x, 28.1) for x in (-8.1, -35.7, -63.0, -90.6)]
    for i, (kind, x, z) in enumerate(ports if lite else ()):
        disc("+Y", mm(x, yb, z), {"usb_c": 4.4, "dc_barrel": 4.3, "jack_635": 6.4, "xlr_combo": 12.0}[kind],
             {"usb_c": 3.4, "dc_barrel": 3.1, "jack_635": 3.3, "xlr_combo": 10.0}[kind], "black")
    if lite:
        names["ports"] = [L.finish("apollo_ports_lite", mp, "+Z", (0, 0, 0), coll, root, smooth=0).name]
    for i, (kind, x, z) in enumerate(() if lite else ports):
        p = P.port(f"apollo_port_{i + 1}{sfx}", kind, lite=lite, facing="+Y", at=mm(x, yb, z), collection=coll,
                   parent=root, mats={"steel": mp["black"]} if kind == "jack_635" else None)
        names.setdefault("ports", []).append(p.name)
    if not lite:
        for i, (x, z) in enumerate(((109.3, 41.4), (-109.7, 41.4), (109.3, 12.0), (-109.7, 12.0))):
            s_ = P.screw(f"apollo_screw_{i + 1}", "phillips", d=5.0 * MM, facing="+Y", at=mm(x, yb, z),
                         collection=coll, parent=root, mats={"steel": mp["steel"]})
            names.setdefault("ports", []).append(s_.name)
    feet = P.rubber_feet("apollo_feet" + sfx, [mm(x, y) for x in (-100, 100) for y in (-60, 60)], d=12 * MM, square=lite,
                         h=IF_FEET * MM, z=IF_FEET * MM, lite=lite, collection=coll, parent=root)
    names["feet"] = [feet.name]
    # the invented name where the real maker's wordmark sits: front strip, centre, light grey print
    # (MEASURED 3q front: 48 wide, letters 3.2 tall; the "apollo | x4" model name on the top is left off)
    d = brand("interface", root, "apollo_brand" + sfx, lite, at=mm(2.6, yf - 1.0, IF_JACK_Z),
              normal=(0, -1, 0), up=(0, 0, 1), height=3.2 * MM, max_width=40 * MM, finish="printed", colour="#9a9ca0")
    if d:
        names["brand"] = [d.name]
    return root, names


# ---------------------------------------------------------------------------
# 2b. Keychron Q1 Max. Origin: desk under the case centre; front (spacebar) -Y.
# ---------------------------------------------------------------------------
def kb_ztop(y):
    """Case top (mm) at y (mm)."""
    return KB_HF + (y + KB_D / 2) / KB_D * (KB_HB - KB_HF)


def kb_plate_frame():
    """Matrix of the key plate: origin at the top-left key corner (u-space origin) on the plate, tilted KB_ANGLE."""
    ylr = KB_D / 2 - KB_TOP_BEZEL          # row 0's back edge
    z = kb_ztop(ylr) - KB_WELL
    return T(-KB_W / 2 * MM + KB_SIDE_BEZEL * MM, ylr * MM, z * MM) @ R(KB_ANGLE, "X")


def keycap_mesh(w, d, lite, mp, colour):
    """One KSA keycap (w x d mm footprint), as a reusable mesh."""
    from lib import parts as P
    A = P.Mesh()
    h = KB_CAP_H
    if lite:
        loops = [(0.0, 0.45, 0.0), (h, 3.0, 0.0)]
        n = 0
    else:
        loops = [(0.0, 0.45, 1.0), (h * 0.55, 1.6, 2.0), (h - 1.4, 2.6, 3.0), (h - 0.35, 3.05, 3.3), (h, 3.6, 3.2),
                 (h - 0.45, 5.0, 3.0)]
        n = 4
    ls = []
    for z, ins, rr in loops:
        ls.append((z * MM, P.rrect((w - 2 * ins) * MM, (d - 2 * ins) * MM, rr * MM, n)))
    if not lite:
        ls.append(((h - 0.75) * MM, P.rrect(max(w - 14.0, 0.6) * MM, max(d - 14.0, 0.6) * MM, 0.25 * MM, n)))
    rloops(A, ls, "cap_" + colour, cap_bottom=False)
    me_name = f"kb_cap_{'lite_' if lite else ''}{int(round(w * 10))}_{colour}"
    o = A.finish("tmp_" + me_name, mp, "+Z", (0, 0, 0), None, None, smooth=35)
    me = o.data
    bpy.data.objects.remove(o)
    me.name = me_name
    return me


def build_keyboard(coll, mp, rough=False, lite=False):
    from lib import parts as P
    from lib import names as NM
    sfx = "_lite" if lite else ""
    names = {}
    root = empty("keyboard" + sfx, coll=coll)
    n = 1 if lite else 6
    rc = 4.0                                  # MEASURED top photo: the case's corner radius
    A = P.Mesh()

    def sheared(o, dz=0.0, base=None):
        return [(x, y, (kb_ztop(y / MM) + dz) * MM if base is None else base) for x, y in o]
    out0 = P.rrect(KB_W * MM, KB_D * MM, rc * MM, n)
    out1 = P.rrect((KB_W - 1.6) * MM, (KB_D - 1.6) * MM, (rc - 0.8) * MM, n)
    ow, od = 16.25 * KB_U + 1.6, 6.45 * KB_U + 1.6
    ocy = KB_D / 2 - KB_TOP_BEZEL + 0.8 - od / 2
    inner = P.rrect(ow * MM, od * MM, 1.5 * MM, n, 0, ocy * MM)
    if rough:
        inner = None
    # bottom case (2.4 to the split, set in 0.5, its bottom edge rounded) and top case (split to the sloped top)
    bot0 = P.rrect((KB_W - 8.0) * MM, (KB_D - 12.0) * MM, (rc - 2.0) * MM, n, 0, -4.0 * MM)   # MEASURED rear: sloped in
    bot1 = P.rrect((KB_W - 1.6) * MM, (KB_D - 1.6) * MM, (rc - 0.8) * MM, n)
    va = A.verts([(x, y, KB_FEET * MM) for x, y in bot0])
    vb = A.verts([(x, y, (KB_SPLIT - 6.0) * MM) for x, y in bot1])
    vc = A.verts([(x, y, KB_SPLIT * MM) for x, y in bot1])
    A.face(list(reversed(va)), "kb_case")
    A.strip(va, vb, "kb_case")
    A.strip(vb, vc, "kb_case")
    A.face(vc, "kb_case")
    t0 = A.verts([(x, y, KB_SPLIT * MM) for x, y in out0])
    t1 = A.verts(sheared(out0, -0.8))
    t2 = A.verts(sheared(out1))
    A.face(list(reversed(t0)), "kb_case")
    A.strip(t0, t1, "kb_case")
    A.strip(t1, t2, "kb_case")
    if inner is None:
        A.face(t2, "kb_case")
    else:
        i0 = A.verts(sheared(inner))
        A.strip(t2, i0, "kb_case")
        # the well: walls down to the plate (the plate follows the case slope here; the keys take KB_ANGLE)
        i1 = A.verts(sheared(inner, -KB_WELL))
        A.strip(i0, i1, "kb_case")
        A.face(i1, "kb_plate")
    case = fin(A, "kb_case" + sfx, mp, coll, root, smooth=35)
    names["case"] = [case.name]
    if rough:
        A = P.Mesh()     # one slab for the keycaps' volume
        z0 = kb_ztop(0) - KB_WELL + KB_SWITCH
        box(A, -16.25 * KB_U / 2 * MM, 16.25 * KB_U / 2 * MM, (ocy - 6.45 * KB_U / 2) * MM, (ocy + 6.45 * KB_U / 2) * MM,
            z0 * MM, (z0 + KB_CAP_H) * MM, "cap_w")
        names["keys"] = [fin(A, "kb_keys", mp, coll, root).name]
        return root, names
    plate = empty("kb_plate" + sfx, root, coll=coll)
    plate.matrix_basis = kb_plate_frame()
    names["plate"] = [plate.name]
    meshes = {}
    U = KB_U
    for ry, row in KB_ROWS:
        for kid, ux, wu, col in row:
            k = (wu, col)
            if k not in meshes:
                meshes[k] = keycap_mesh(wu * U - 0.0, U, lite, mp, col)
            o = bpy.data.objects.new(f"kb_key_{kid}{sfx}", meshes[k])
            coll.objects.link(o)
            NM.set_name(o, f"kb_key_{kid}{sfx}", data=False)
            o.parent = plate
            dy = KB_ARROW_DROP if kid in KB_DROPPED else 0.0
            o.location = ((ux + wu / 2) * U * MM, -(ry + dy + 0.5) * U * MM, KB_SWITCH * MM)
            names.setdefault("keys", []).append(o.name)
    # stems under the space bar and the switch housings are hidden by the caps; the knob in the nav column
    kux, kuy, kr, kh = KB_KNOB
    kn = P.knob("kb_knob" + sfx, kr * MM, (KB_WELL + kh) * MM, knurl=not lite, flutes=40, depth=0.35 * MM,
                chamfer=0.8 * MM, lite=lite, mats={"knob": mp["kb_knob"]}, facing="+Z", collection=coll, parent=plate,
                at=((kux + 0.5) * U * MM, -(kuy + 0.5) * U * MM, 0.0))
    names["knob"] = [kn.name]
    # rear: USB-C, the two slide switches and the LED, in the pocket at the back left (MEASURED review-tr-rear)
    yb = KB_D / 2
    zp = (KB_SPLIT + 4.5)
    u = flat_port("kb_usb_lite", mm(-95.7, yb, zp), "+Y", coll, root, mp) if lite else \
        P.port("kb_usb", "usb_c", facing="+Y", at=mm(-95.7, yb, zp), collection=coll, parent=root)
    A = P.Mesh()
    for x, w in ((-111.0, 10.0), (-130.0, 12.0)):
        box(A, (x - w / 2) * MM, (x + w / 2) * MM, (yb - 0.1) * MM, (yb + 0.7) * MM, (zp - 2.0) * MM, (zp + 2.0) * MM,
            "black", r=0.6 * MM, n=2)
    if not lite:
        box(A, -86.2 * MM, -85.2 * MM, (yb - 0.1) * MM, (yb + 0.08) * MM, (zp - 0.5) * MM, (zp + 0.5) * MM, "port")
    box(A, -141.0 * MM, -81.5 * MM, (yb - 0.1) * MM, (yb + 0.04) * MM, KB_SPLIT * MM, (KB_SPLIT + 10.5) * MM, "kb_pocket",
        r=1.5 * MM, n=2 if lite else 4)                 # the pocket's shaded back wall (not cut: a flat inlay)
    pocket = fin(A, "kb_switches" + sfx, mp, coll, root)
    names["rear"] = [u.name, pocket.name]
    feet = P.rubber_feet("kb_feet" + sfx, [mm(x, y) for x in (-145, 145) for y in (-58, 58)], d=14 * MM, h=KB_FEET * MM,
                         square=True, z=KB_FEET * MM, lite=lite, collection=coll, parent=root)
    names["feet"] = [feet.name]
    # the real maker's logo is on the underside (no logo on the top or the back in any reference): ours there
    d = brand("keyboard", root, "kb_brand" + sfx, lite, at=mm(0, -10, KB_FEET), normal=(0, 0, -1), up=(0, -1, 0),
              height=6.0 * MM, finish="engraved", colour="#cfcec9")
    if d:
        names["brand"] = [d.name]
    return root, names


# ---------------------------------------------------------------------------
# 2c. MX Master 3S. Origin: desk under the top-view centre; nose -Y; thumb side -X.
# ---------------------------------------------------------------------------
def ms_height(x, y):
    """The shell's height (mm) at (x, y): a hump peaking MS_PEAK back from the nose, the thumb shelf lower."""
    u = min(max((-y + MS_L / 2) / MS_L, 0.0), 1.0)     # 0 at the nose (+Y)
    if u < MS_PEAK:
        t = u / MS_PEAK
        h = 21.0 + (MS_H - 21.0) * (1 - (1 - t) ** 2)
    else:
        t = (u - MS_PEAK) / (1 - MS_PEAK)
        h = MS_H - 19.0 * t ** 2
    h *= 1.0 - 0.28 * ((x - 6.0) / 44.0) ** 2
    # the thumb rest: a wide, flat, slightly cupped shelf, blended into the body in one sweep (coordinator 2026-10-26)
    w = ms_thumb_w(x, y)
    shelf = 20.5 + 2.0 * min(1.0, ((x + 29.0) / 12.0) ** 2) + 2.0 * _sstep(20.0, 55.0, -y)
    return h * (1 - w) + shelf * w


def _sstep(a, b, v):
    t = min(max((v - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ms_thumb_w(x, y):
    """0 on the main body, 1 on the thumb rest (world x, y; the tail is -y)."""
    return _sstep(-11.0, -27.0, x) * _sstep(-22.0, 6.0, -y)


def ms_outline(n=None):
    pts = MS_OUTLINE
    if n and n < len(pts):
        step = len(pts) / n
        pts = [pts[int(i * step)] for i in range(n)]
    return [(x, -y) for x, y in reversed(pts)]      # the nose to +Y (away from the user); still CCW


def build_mouse(coll, mp, rough=False, lite=False):
    from lib import parts as P
    from mathutils.bvhtree import BVHTree
    sfx = "_lite" if lite else ""
    names = {}
    root = empty("mouse" + sfx, coll=coll)
    out = ms_outline(36 if lite else None)
    cx, cy = 3.0, -4.0                       # the rings shrink toward the hump
    rings = [1.0, 0.97, 0.92, 0.85, 0.75, 0.62, 0.48, 0.33, 0.18] if not lite else [1.0, 0.9, 0.65, 0.3]
    A = P.Mesh()
    loops = []
    # the side wall: the bottom tucked in 2.5 mm, then up the outline to the shoulder
    def ring(s, zf):
        pts = []
        for x, y in out:
            px, py = cx + (x - cx) * s, cy + (y - cy) * s
            pts.append((px * MM, py * MM, zf(px, py, x, y) * MM))
        return pts
    def ins(x):
        t = min(max((x + 18.0) / -20.0, 0.0), 1.0)
        return 5.0 + 9.0 * t * t * (3 - 2 * t)      # MEASURED front.png: the base sits 5 in, 14 under the thumb wing
    tuck = [((cx + (x - cx) * (1 - ins(x) / max(math.hypot(x - cx, y - cy), 1))), (cy + (y - cy) * (1 - ins(x) / max(
        math.hypot(x - cx, y - cy), 1)))) for x, y in out]
    loops.append(A.verts([(x * MM, y * MM, 1.2 * MM) for x, y in tuck]))
    loops.append(A.verts([(x * MM, y * MM, (0.3 * ms_height(x, y) + 0.25 * ins(x)) * MM) for x, y in out]))
    for s in rings:
        loops.append(A.verts(ring(s, lambda px, py, x, y, s=s: ms_height(px, py) * (1 - 0.42 * s ** 6))))
    A.face(list(reversed(loops[0])), "ms_side")
    for i, (a, b) in enumerate(zip(loops, loops[1:])):
        A.strip(a, b, "ms_side" if i < 2 else "ms_top")
    A.face(loops[-1], "ms_top")
    body = fin(A, "mouse_body" + sfx, mp, coll, root, smooth=89)
    if not (lite or rough):
        sub = body.modifiers.new("subsurf", "SUBSURF")
        sub.levels = sub.render_levels = 2
    names["body"] = [body.name]
    if not (lite or rough):            # the thumb rest's fine diagonal ridges: its own bump-mapped material
        body.data.materials.append(mp["ms_thumb"])
        ti = len(body.data.materials) - 1
        for f in body.data.polygons:
            c = f.center
            if c.z > 8 * MM and ms_thumb_w(c.x / MM, c.y / MM) > 0.55 and f.normal.z > 0.3:
                f.material_index = ti
    if rough:
        return root, names
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(body, dg)

    def hit(x, y):
        loc, nrm, _, _ = bvh.ray_cast(Vector((x * MM, -y * MM, 0.2)), Vector((0, 0, -1)))   # top.png frame
        return loc, nrm

    def surf_strip(A, pts, w, key, lift=0.2):
        """A thin line on the shell's top along a top-view polyline (mm)."""
        prev = None
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dx, dy = x1 - x0, y1 - y0
            L = math.hypot(dx, dy)
            k = max(1, int(L / 2.0))
            nx, ny = -dy / L * w / 2, dx / L * w / 2
            for j in range(k):
                ta, tb = j / k, (j + 1) / k
                q = []
                for (px, py) in ((x0 + dx * ta + nx, y0 + dy * ta + ny), (x0 + dx * tb + nx, y0 + dy * tb + ny),
                                 (x0 + dx * tb - nx, y0 + dy * tb - ny), (x0 + dx * ta - nx, y0 + dy * ta - ny)):
                    loc, nrm = hit(px, py)
                    if loc is None:
                        q = None
                        break
                    q.append(loc + nrm * lift * MM)
                if q:
                    A.face(A.verts(q), key)
    # seams: the two button splits, the button rear edges, the wheel housing, the mode button (MEASURED top.png)
    A = P.Mesh()
    w = 0.45
    surf_strip(A, [(1.0, -62.0), (1.2, -40.0)], w, "ms_line")                       # between the buttons, nose
    surf_strip(A, [(5.0, -46.8), (5.0, -22.0), (6.0, -16.0)], w, "ms_line")           # wheel housing, left
    surf_strip(A, [(18.0, -46.8), (18.0, -22.0), (17.0, -16.0)], w, "ms_line")        # right
    surf_strip(A, [(5.0, -46.8), (18.0, -46.8)], w, "ms_line")
    surf_strip(A, [(-17.5, -25.0), (6.0, -16.5)], w, "ms_line")                       # left button's rear edge
    surf_strip(A, [(17.5, -16.5), (36.0, -9.0), (39.5, -12.0)], w, "ms_line")         # right button's rear edge
    surf_strip(A, [(36.0, -9.0), (39.6, -45.0)], w, "ms_line")                       # right button's outer edge
    mx, my, mw, mh = MS_MID
    surf_strip(A, [(mx - mw / 2, my - mh / 2), (mx + mw / 2, my - mh / 2), (mx + mw / 2, my + mh / 2),
                   (mx - mw / 2, my + mh / 2), (mx - mw / 2, my - mh / 2)], w * 0.9, "ms_line")
    seams = fin(A, "mouse_seams" + sfx, mp, coll, root, smooth=0) if A.bm.faces else None
    if seams:
        names["seams"] = [seams.name]
    # the MagSpeed wheel in its dark slot
    wx, wy, wr, ww = MS_WHEEL
    loc, nrm = hit(wx, wy)
    sw, sl = MS_SLOT
    A = P.Mesh()
    zs = loc.z / MM
    wy = -wy
    box(A, (wx - sw / 2) * MM, (wx + sw / 2) * MM, (wy - sl / 2) * MM, (wy + sl / 2) * MM, (zs - 6.0) * MM,
        (zs + 0.25) * MM, "ms_slot", r=1.2 * MM, n=2 if lite else 4)
    slot = fin(A, "mouse_wheel_slot" + sfx, mp, coll, root)
    slot.matrix_basis = T(wx * MM, wy * MM, zs * MM) @ nrm.to_track_quat("Z", "Y").to_matrix().to_4x4() @ \
        T(-wx * MM, -wy * MM, -zs * MM)
    A = P.Mesh()
    seg = 16 if lite else 240
    ridge = (lambda a: 1.0 - 0.02 * (0.5 + 0.5 * math.cos(a * 60))) if not lite else None
    prof = [(0, -ww / 2), (wr - 0.6, -ww / 2), (wr, -ww / 2 + 0.6), (wr, -0.9), (wr - 0.5, -0.5), (wr - 0.5, 0.5),
            (wr, 0.9), (wr, ww / 2 - 0.6), (wr - 0.6, ww / 2), (0, ww / 2)]
    prof = [(r_ * MM, z * MM, ridge) if (ridge and abs(r_ - wr) < 1e-6) else (r_ * MM, z * MM) for r_, z in prof]
    A.lathe(prof, seg, "ms_wheel", m=T(wx * MM, wy * MM, (zs + 3.5 - wr) * MM) @ R(90, "Y"))
    wheel = fin(A, "mouse_wheel" + sfx, mp, coll, root, smooth=40)
    names["wheels"] = [slot.name, wheel.name]
    # the thumb wheel (coordinator 2026-10-26): a horizontal knurled drum, 22 long and 13 across, its axis along the
    # mouse's length, its outer half showing out of a silver pocket in the thumb wall; two pill buttons under it,
    # the green battery LED on the pocket behind it (Logitech three-quarter.png, side-thumb-profile.png)
    TW_L, TW_R = 22.0, 6.5
    ty = -MS_THUMB[1]
    tz = 31.0

    def wall_frame(y, z):
        h_ = bvh.ray_cast(Vector((-0.08, y * MM, z * MM)), Vector((1, 0, 0)))
        p_, n_ = (h_[0], h_[1].normalized()) if h_[0] is not None else (Vector(mm(-18.0, y, z)), Vector((-1, 0, 0)))
        zl = Vector((n_.x, 0.0, n_.z)).normalized()          # out of the wall, the axis kept along Y
        yl = Vector((0, 1, 0))
        xl = yl.cross(zl)
        m_ = Matrix((xl, yl, zl)).transposed().to_4x4()
        m_.translation = p_
        return m_
    Mw = wall_frame(ty, tz)
    A = P.Mesh()
    P._rbox(A, 16.0 * MM, 34.0 * MM, 9.0 * MM, 4.0 * MM, 1.2 * MM, 0.0, 1 if lite else 4, "ms_side", z0=-8.2 * MM)
    pocket = A.finish("mouse_thumb_pocket" + sfx, mp, "+Z", (0, 0, 0), coll, root, smooth=40)
    pocket.matrix_basis = Mw @ T(0, -3.0 * MM, 0)
    A = P.Mesh()
    knurl = (lambda a: 1.0 - 0.03 * (0.5 + 0.5 * math.cos(a * 40))) if not lite else None
    L2, Rd = TW_L / 2, TW_R
    prof = [(0, -L2), (Rd - 0.6, -L2), (Rd, -L2 + 0.6, knurl), (Rd, -1.0, knurl), (Rd - 0.8, -0.6), (Rd - 0.8, 0.6),
            (Rd, 1.0, knurl), (Rd, L2 - 0.6, knurl), (Rd - 0.6, L2), (0, L2)]
    prof = [(p[0] * MM, p[1] * MM, p[2]) if len(p) > 2 and p[2] else (p[0] * MM, p[1] * MM) for p in prof]
    A.lathe(prof, 12 if lite else 240, "ms_wheel", m=R(-90, "X"))
    thumb = fin(A, "mouse_thumbwheel" + sfx, mp, coll, root, smooth=40)
    thumb.matrix_basis = Mw @ T(0, 0, 0.8 * MM)          # the axis at the pocket's face: its outer half shows
    import bmesh as _bm
    A = P.Mesh()
    for yy in (ty + 6.0, ty - 6.0):                        # back / forward: two pills side by side under the wheel
        n0 = len(A.bm.verts)
        P._rbox(A, 4.4 * MM, 10.0 * MM, 2.0 * MM, 2.2 * MM, 1.0 * MM, 0.0, 1 if lite else 4, "ms_top", z0=-0.6 * MM)
        A.bm.verts.ensure_lookup_table()
        _bm.ops.transform(A.bm, matrix=wall_frame(yy, 24.0), verts=A.bm.verts[n0:])
    btns = A.finish("mouse_side_buttons" + sfx, mp, "+Z", (0, 0, 0), coll, root, smooth=40)
    A = P.Mesh()
    P._rbox(A, 1.2 * MM, 3.6 * MM, 0.5 * MM, 0.55 * MM, 0.2 * MM, 0.0, 2, "led_green", z0=0.0)
    led = A.finish("mouse_led" + sfx, mp, "+Z", (0, 0, 0), coll, root, smooth=0)
    led.matrix_basis = Mw @ T(2.5 * MM, -16.5 * MM, 0.75 * MM)
    names["thumb"] = [pocket.name, thumb.name, btns.name, led.name]
    # the nose: USB-C under the buttons (MEASURED front.png)
    h_ = bvh.ray_cast(Vector((1.0 * MM, 0.12, 7.5 * MM)), Vector((0, -1, 0)))
    at_ = h_[0] if h_[0] is not None else Vector(mm(1.0, 61.0, 7.5))
    u = flat_port("mouse_usb_lite", tuple(at_), "+Y", coll, root, mp) if lite else \
        P.port("mouse_usb", "usb_c", facing="+Y", at=tuple(at_), collection=coll, parent=root)
    names["front"] = [u.name]
    feet = P.rubber_feet("mouse_feet" + sfx, [mm(-27, -10), mm(27, -10), mm(0, 45)], d=6 * MM, h=1.2 * MM, square=lite,
                         z=1.2 * MM, lite=lite, collection=coll, parent=root)
    names["feet"] = [feet.name]
    # the invented name where "logi" sits: the left button's rear, turned 12 deg, mid grey print, on the shell
    lx, ly, la = MS_LOGO
    loc, nrm = hit(lx, ly)
    a = math.radians(la)
    up = Vector((-math.sin(a), math.cos(a), 0.0))      # the text's up toward the nose, turned la
    up = (up - nrm * up.dot(nrm)).normalized()
    d = brand("mouse", root, "mouse_brand" + sfx, lite, at=tuple(loc), normal=tuple(nrm), up=tuple(up),
              height=4.6 * MM, max_width=11.5 * MM, finish="printed", colour="#8e9094", conform=None if lite else body)
    if d:
        names["brand"] = [d.name]
    return root, names


# ---------------------------------------------------------------------------
# 2d. Stream Deck MK.2 on its stand. Origin: desk under the deck; the keys face the user (-Y), tilted back.
# ---------------------------------------------------------------------------
def build_streamdeck(coll, mp, rough=False, lite=False):
    from lib import parts as P
    sfx = "_lite" if lite else ""
    names = {}
    root = empty("deck" + sfx, coll=coll)
    th = math.radians(SD_TILT)
    z0, y0 = SD_LIFT
    # the deck: a slab, face toward -Y tilted back by SD_TILT about its front-bottom edge
    deck = empty("deck_body_frame" + sfx, root, coll=coll)
    deck.matrix_basis = T(0, y0 * MM, z0 * MM) @ Matrix((
        (1, 0, 0, 0),
        (0, math.cos(th), -math.sin(th), 0),
        (0, math.sin(th), math.cos(th), 0),
        (0, 0, 0, 1)))
    # local +Y -> (0, cos t, sin t): up the face toward the back; local +Z -> (0, -sin t, cos t): the face normal
    # the slab lies from local z = -SD_T (its back) to 0 (its face); shift so its back rests on the stand at z = 0
    A = P.Mesh()
    P._rbox(A, SD_W * MM, SD_D * MM, SD_T * MM, 6.0 * MM, (0.0 if rough else 2.4) * MM, (0.0 if rough else 1.6) * MM,
            1 if (lite or rough) else 4, "sd_white", z0=0.0)
    body = fin(A, "deck_body" + sfx, mp, coll, deck, smooth=35)
    body.location = (0, SD_D / 2 * MM, 0)
    names["body"] = [body.name]
    # the stand: base frame on the desk, two side cheeks, a sloped back plate with a window, the front lip
    A = P.Mesh()
    t = 3.0
    yb = y0 + (SD_D - 6.0) * math.cos(th)              # where the slope plate's top meets the back leg
    zt = z0 + (SD_D - 6.0) * math.sin(th)
    wi = SD_W - 8.0
    if rough:
        A.prism([(y * MM, z * MM) for y, z in ((y0 - 4, 0), (yb + 3, 0), (yb + 3, zt), (y0 - 4, z0 + 6))],
                0, wi * MM, "sd_white", m=Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))) @
                T(0, 0, -wi / 2 * MM))
    else:
        mside = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        for sx in (-1, 1):                              # side cheeks: a triangle frame, 3 mm thick
            xo = sx * (wi / 2 - t / 2)
            tri = [(y0 - 4.0, 0.0), (yb + 3.0, 0.0), (yb + 3.0, zt + 1.0)]
            A.prism([(y * MM, z * MM) for y, z in tri], 0.0, t * MM, "sd_white",
                    m=mside @ T(0, 0, (xo - t / 2) * MM))
        # base bars on the desk (front lip and back) and the back leg
        box(A, -wi / 2 * MM, wi / 2 * MM, (y0 - 3.0) * MM, (y0 + 4.0) * MM, 0.0, z0 * MM, "sd_white", r=1.0 * MM,
            n=1 if lite else 3)
        box(A, -wi / 2 * MM, wi / 2 * MM, (yb - 1.0) * MM, (yb + 3.0) * MM, 0.0, (zt + 1.0) * MM, "sd_white", r=1.0 * MM,
            n=1 if lite else 3)
    stand = fin(A, "deck_stand" + sfx, mp, coll, root, smooth=35)
    names["stand"] = [stand.name]
    if rough:
        return root, names
    # keys: 15 LCD keys, 3 x 5, glossy black with an emissive plain-shape icon each (no text, no logos)
    keys = []
    for r_ in range(3):
        for c in range(5):
            i = (2 - r_) * 5 + c                       # 0 = top-left as seen by the user
            x = (c - 2) * SD_PITCH
            y = SD_ROW0 + r_ * SD_PITCH
            A = P.Mesh()
            P._rbox(A, SD_KEY * MM, SD_KEY * MM, 1.2 * MM, 2.6 * MM, 0.6 * MM, 0.0, 1 if lite else 3, "sd_key", z0=-0.6 * MM)
            k = fin(A, f"deck_key_{i + 1:02d}{sfx}", mp, coll, deck, smooth=35)
            k.location = (x * MM, y * MM, SD_T * MM)
            # the icon: a dim colour field and a bright plain shape, just under the glass top
            col = SD_ICONS[i]
            im = icon_mat(i + 1, col, 0.9)
            wm = icon_mat(100, "#ffffff", 1.0)
            B = P.Mesh()
            def lay(o_, z0_, z1_, key_):
                if lite:
                    B.face(B.verts([(x_, y_, z1_) for x_, y_ in P.ccw(o_)]), key_)
                else:
                    B.prism(o_, z0_, z1_, key_, bottom=False)
            lay(P.rrect(14.6 * MM, 14.6 * MM, 1.8 * MM, 1 if lite else 3), 0.62 * MM, 0.64 * MM, "field")
            shp = SD_SHAPES[i]
            n = 12 if lite else 32
            if shp == "circle":
                o = [P.circle(3.2 * MM, n)]
            elif shp == "square":
                o = [P.rrect(6.0 * MM, 6.0 * MM, 0.8 * MM, 2)]
            elif shp == "triangle":
                o = [[(0, 3.6 * MM), (-3.4 * MM, -2.6 * MM), (3.4 * MM, -2.6 * MM)]]
            elif shp == "ring":
                o = [P.circle(3.4 * MM, n)]
            else:
                o = [P.rrect(1.4 * MM, hh * MM, 0.5 * MM, 1, xx * MM, (hh / 2 - 3.0) * MM)
                     for xx, hh in ((-2.6, 4.0), (0.0, 6.4), (2.6, 3.0))]
            for oo in o:
                lay(oo, 0.64 * MM, 0.66 * MM, "icon")
            if shp == "ring":
                lay(P.circle(2.0 * MM, n), 0.66 * MM, 0.68 * MM, "field")
            ic = B.finish(f"deck_icon_{i + 1:02d}{sfx}", {"field": im, "icon": wm}, "+Z", (0, 0, 0), coll, k, smooth=0)
            keys.append(k.name)
            names.setdefault("icons", []).append(ic.name)
    names["keys"] = keys
    # the invented name where "STREAM DECK" and the round mark sit: top of the face, centred, dark grey print
    # (MEASURED gallery-02: 45 wide with the mark, letters 3.5 tall, 9 below the top edge)
    d = brand("streamdeck", deck, "deck_brand" + sfx, lite, at=mm(0, SD_D - 9.5, SD_T), normal=(0, 0, 1), up=(0, 1, 0),
              height=3.5 * MM, max_width=37 * MM, finish="printed", colour="#2a2b2e")
    if d:
        names["brand"] = [d.name]
    names["frame"] = [deck.name]
    return root, names


BUILDERS = {"interface": build_interface, "keyboard": build_keyboard, "mouse": build_mouse,
            "streamdeck": build_streamdeck}


def build(rough=False, lite=False, collection=None, layout=None):
    coll = collection or bpy.context.scene.collection
    mp = mats()
    lay = layout or DEMO
    names = {}
    parts = PARTS if PART == "all" else (PART,)
    for p in parts:
        root, d = BUILDERS[p](coll, mp, rough, lite)
        x, y, z = lay[p][:3]
        yaw = lay[p][3] if len(lay[p]) > 3 else 0.0
        root.location = (x, y, z) if (PART == "all" or layout) else (0, 0, 0)
        root.rotation_euler = (0, 0, math.radians(yaw)) if (PART == "all" or layout) else (0, 0, 0)
        names[p] = sorted({n for v in d.values() for n in v})
        for k, v in d.items():
            names[f"{p}:{k}"] = v
        names[f"{p}:root"] = [root.name]
    bpy.context.view_layer.update()
    names["all"] = sorted({n for k, v in names.items() if ":" not in k for n in v
                           if n in bpy.data.objects and bpy.data.objects[n].type == "MESH"})
    return names


def room_layout():
    """Room placement from plan v3 (parts interface, streamdeck, keyboard, mouse): at = centre on the desk, yaw."""
    from lib import plan_v3 as PL
    out = {}
    for c in PL.COMPONENTS:
        if c["key"] in PARTS:
            x, y, z = c["at"]
            out[c["key"]] = (x, y, z, c["yaw"])
    return out


def build_set(layout=None, collection=None, lite=False):
    global PART
    PART = "all"
    return build(False, lite, collection, layout or room_layout())


# ---------------------------------------------------------------------------
# 3. the photo views
# ---------------------------------------------------------------------------
def outline_views(names):
    v = []
    if "interface" in names:
        o = names["interface"]
        v.append(dict(name="apollo-top", title="Apollo x4 Gen 2: top (UA image) vs our model",
                      photo=os.path.join(R_IF, "gen2-silver-top.png"), mask="alpha", objects=o,
                      camera={"mode": "ortho", "view": "top"},
                      explain="UA's top render has a little perspective: the tall back edge reads deeper than the front lip"))
        v.append(dict(name="apollo-back", title="Apollo x4 Gen 2: back (UA image) vs our model",
                      photo=os.path.join(R_IF, "gen2-silver-back.png"), mask="alpha", objects=o,
                      camera={"mode": "fit", "view": "back", "tilts": [-6.0, -3.0, 0.0]},
                      explain="the corner radius of the back-top edge and the feet; perspective render"))
        v.append(dict(name="apollo-3q", title="Apollo x4 Gen 2: three-quarter front (UA image) vs our model",
                      photo=os.path.join(R_IF, "gen2-silver-three-quarter-front.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "front", "yaws": [-3.0, 0.0, 3.0], "tilts": [-40.0, -34.0, -28.0]},
                      explain="UA's perspective render; the lens and the turn are searched"))
    if "keyboard" in names:
        o = names["keyboard"]
        v.append(dict(name="kb-top", title="Q1 Max white: top (Keychron image) vs our model",
                      photo=os.path.join(R_KB, "variant-assembled-white-brown.jpg"), mask=0.95, crop=(0, 2000, 630, 1380),
                      objects=o, camera={"mode": "ortho", "view": "top"}))
        v.append(dict(name="kb-3q", title="Q1 Max white: three-quarter (Keychron render) vs our model",
                      photo=os.path.join(R_KB, "variant-white-osa-sideprinted.jpg"), mask=0.86, crop=(0, 2000, 500, 1000),
                      objects=o, camera={"mode": "free", "view": "front", "yaws": [-4.0, 0.0, 4.0],
                                          "tilts": [-50.0, -42.0, -34.0]},
                      explain="Keychron's render of the side-printed OSA set (taller caps); perspective searched"))
    if "mouse" in names:
        o = names["mouse"]
        v.append(dict(name="mouse-top", title="MX Master 3S: top (Logitech image) vs our model",
                      photo=os.path.join(R_MS, "top.png"), mask="alpha", objects=o, camera={"mode": "ortho", "view": "top"}))
        v.append(dict(name="mouse-front", title="MX Master 3S: front (Logitech image) vs our model",
                      photo=os.path.join(R_MS, "front.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "back", "yaws": [-10.0, 0.0, 10.0], "tilts": [-20.0, -10.0, 0.0]},
                      explain="Logitech's nose-on shot is tilted and turned; searched"))
        v.append(dict(name="mouse-side", title="MX Master 3S: thumb side (Logitech image) vs our model",
                      photo=os.path.join(R_MS, "side-thumb-profile.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "left", "yaws": [-30.0, -15.0, 0.0, 15.0],
                              "tilts": [-35.0, -20.0, -5.0]},
                      explain="a low three-quarter from the thumb side, not a profile; searched"))
        v.append(dict(name="mouse-3q", title="MX Master 3S: top, thumb side (Logitech image) vs our model",
                      photo=os.path.join(R_MS, "three-quarter.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "top", "yaws": [-20.0, -10.0, 0.0, 10.0],
                              "tilts": [-30.0, -15.0, 0.0]},
                      explain="Logitech's tilted top shot; searched"))
    if "streamdeck" in names:
        o = names["streamdeck"]
        v.append(dict(name="deck-3q", title="Stream Deck MK.2 white: three-quarter on the stand (Elgato image) vs our model",
                      photo=os.path.join(CUT, "deck-gallery-01-cut.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "front", "yaws": [30.0, 45.0, 60.0], "tilts": [-75.0, -65.0, -55.0]},
                      explain="Elgato's render from high on the left; brightness cutout (cutouts/)"))
        v.append(dict(name="deck-low", title="Stream Deck MK.2 white: low front on the stand (Elgato image) vs our model",
                      photo=os.path.join(CUT, "deck-lowangle-cut.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "front", "yaws": [-25.0, -15.0, -5.0], "tilts": [-15.0, -8.0, 0.0]},
                      explain="a desk photo; the cutout keeps the deck and stand only (cable cropped)"))
    only = os.environ.get("DESKTOP_VIEWS")
    if only:
        v = [x for x in v if x["name"] in only.split(",")]
    return v


# ---------------------------------------------------------------------------
# 4. stages
# ---------------------------------------------------------------------------
def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {NAME}: {msg}", flush=True)


def progress(line):
    os.makedirs(FOOT, exist_ok=True)
    with open(os.path.join(FOOT, "PROGRESS.md"), "a") as f:
        f.write(f"- {time.strftime('%H:%M')} {line}\n")


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")


def stage_outline(out):
    import outline_check
    clear()

    def b(rough=True):
        n = build(rough=True)
        return {k: v for k, v in n.items() if ":" not in k}
    return outline_check.run(NAME, b, outline_views, os.path.join(out, "outline"), log=log)


def stage_build(out):
    clear()
    t = time.time()
    names = build()
    blend = os.path.join(BLENDER_DIR, "out", "components", f"{NAME}.blend")
    os.makedirs(os.path.dirname(blend), exist_ok=True)
    with open(os.path.join(out, f"{NAME}-names.json"), "w") as f:
        json.dump(names, f, indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    log(f"built in {time.time() - t:.1f} s, saved {blend}")
    return names


def _studio(sc, cycles, strength=1.0):
    from lib import compare
    compare.ensure_studio(strength)
    sc.render.film_transparent = False
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGB"
    sc.view_settings.view_transform = "AgX"
    if cycles:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 96
        sc.cycles.use_denoising = True
        try:
            sc.cycles.device = "GPU"
        except Exception:
            pass
    else:
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = 32


def _shoot(sc, cam, path, cycles, label):
    from lib import renderqueue
    sc.camera = cam
    sc.render.filepath = path
    if cycles:
        with renderqueue.slot(f"{NAME} {label}"):
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(write_still=True)


def look_cam(name, pos, target, lens=50, ortho=None):
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.002
    cd.clip_end = 50
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    cam = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if cam.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(cam)
    d = Vector(target) - Vector(pos)
    cam.location = pos
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return cam


def stage_stills(out, names, cycles=False):
    sc = bpy.context.scene
    _studio(sc, cycles, 0.8)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    from lib import compare
    lo, hi = compare.world_bbox(names["all"])
    c = (lo + hi) / 2
    k = max(hi - lo) * 2.2
    shots = {"hero": look_cam("still_hero", (c.x - 0.35 * k, c.y - 0.9 * k, c.z + 0.55 * k), c, 50),
             "front": look_cam("still_front", (c.x, c.y - 6, c.z), c, ortho=max((hi - lo).x, (hi - lo).z * 16 / 9) * 1.1),
             "top": look_cam("still_top", (c.x, c.y, c.z + 6), c, ortho=max((hi - lo).x, (hi - lo).y * 16 / 9) * 1.1)}
    paths = {}
    for kk, cam in shots.items():
        p = os.path.join(out, f"{NAME}-{kk}{'-cycles' if cycles else ''}.png")
        _shoot(sc, cam, p, cycles, kk)
        paths[kk] = p
    log(f"stills: {paths}")
    return paths


def closeup_specs():
    """(key, title, photo or (photo, crop box), camera pos, target, lens): positions in each part's frame."""
    o = bpy.data.objects
    out = []

    def W(root, p):
        if root == "mouse":
            p = (p[0], -p[1], p[2])      # mouse close-ups are given in top.png's frame (y toward the tail)
        return o[root].matrix_world @ Vector(mm(*p))
    if "apollo" in o:
        kx, ky = IF_KNOB[:2]
        out += [
            ("apollo-knob", "Apollo: the knob and its LED ring", (os.path.join(R_IF, "gen2-silver-three-quarter-front.png"),
                                                                    (1250, 1950, 550, 1100)),
             W("apollo", (kx - 30, ky - 170, 150)), W("apollo", (kx, ky, 52)), 50),
            ("apollo-meters", "Apollo: the meter window and buttons", (os.path.join(R_IF, "gen2-silver-top.png"),
                                                                        (300, 1700, 500, 1300)),
             W("apollo", (-25, -20, 320)), W("apollo", (-25, -5, 45)), 50),
            ("apollo-rear", "Apollo: the back", os.path.join(R_IF, "gen2-silver-back.png"),
             W("apollo", (0, 420, 60)), W("apollo", (0, 70, 28)), 50),
            ("apollo-brand", "Apollo: the front strip and the maker's name", (os.path.join(R_IF, "gen2-silver-three-quarter-front.png"),
                                                                              (300, 2300, 1000, 1500)),
             W("apollo", (0, -260, 90)), W("apollo", (0, -75, 16)), 50),
        ]
    if "keyboard" in o:
        out += [
            ("kb-caps", "Q1 Max: keycap profile and the back edge", (os.path.join(R_KB, "review-tr-rear.jpg"), (0, 1920, 200, 1000)),
             W("keyboard", (-110, 250, 40)), W("keyboard", (-110, 60, 28)), 50),
            ("kb-knob", "Q1 Max: the knob", (os.path.join(R_KB, "review-tr-full.jpg"), (1250, 1700, 250, 600)),
             W("keyboard", (110, -60, 200)), W("keyboard", (150, 60, 35)), 50),
            ("kb-wedge", "Q1 Max: the side and its wedge", (os.path.join(R_KB, "variant-white-osa-sideprinted.jpg"),
                                                            (1300, 1950, 500, 1000)),
             W("keyboard", (420, -140, 90)), W("keyboard", (150, 0, 22)), 50),
            ("kb-brand", "Q1 Max: the underside name (no reference photo of the real underside)",
             (os.path.join(R_KB, "variant-barebone-white.jpg"), (0, 2000, 400, 1600)),
             W("keyboard", (0, -40, -260)), W("keyboard", (0, -10, 2)), 50),
        ]
    if "mouse" in o:
        out += [
            ("mouse-wheels", "MX Master 3S: the MagSpeed wheel and the mode button", (os.path.join(R_MS, "top.png"),
                                                                                       (1500, 2200, 300, 1300)),
             W("mouse", (11, -30, 190)), W("mouse", (11, -28, 40)), 50),
            ("mouse-thumb", "MX Master 3S: the thumb wheel and thumb rest", os.path.join(R_MS, "side-thumb-profile.png"),
             W("mouse", (-210, -60, 110)), W("mouse", (-15, 5, 22)), 50),
            ("mouse-brand", "MX Master 3S: the name on the left button", (os.path.join(R_MS, "top.png"), (1100, 1700, 700, 1250)),
             W("mouse", (-9, -20, 140)), W("mouse", (-9, -20, 40)), 50),
            ("mouse-front", "MX Master 3S: the nose and USB-C", os.path.join(R_MS, "front.png"),
             W("mouse", (10, -260, 60)), W("mouse", (0, -40, 22)), 50),   # the nose (top.png -y)
        ]
    if "deck" in o:
        out += [
            ("deck-keys", "Stream Deck: the keys and icons", (os.path.join(R_SD, "gallery-01.jpg"), (650, 1900, 200, 1350)),
             W("deck", (-120, -220, 180)), W("deck", (0, -5, 40)), 50),
            ("deck-stand", "Stream Deck: the stand", (os.path.join(R_SD, "desk-white-lowangle.jpg"), (850, 2150, 450, 1500)),
             W("deck", (-170, -200, 50)), W("deck", (0, 5, 35)), 50),
            ("deck-brand", "Stream Deck: the name on the face", (os.path.join(R_SD, "gallery-02.jpg"), (1050, 1750, 650, 950)),
             W("deck", (0, -150, 150)), W("deck", (0, 20, 62)), 50),
        ]
    only = os.environ.get("DESKTOP_CU")
    if only:
        out = [x for x in out if x[0] in only.split(",")]
    return out


def stage_closeups(out, names, cycles=False):
    sc = bpy.context.scene
    _studio(sc, cycles, 0.8)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 720, 100
    d = os.path.join(out, "closeups")
    os.makedirs(d, exist_ok=True)
    pairs = []
    for key, title, photo, pos, tgt, lens in closeup_specs():
        cam = look_cam(f"still_cu_{key.replace('-', '_')}", pos, tgt, lens)
        p = os.path.join(d, f"{key}.png")
        _shoot(sc, cam, p, cycles, key)
        ph, crop = (photo if isinstance(photo, tuple) else (photo, None))
        pairs.append(dict(key=key, title=title, photo=ph, crop=crop, render=p))
    jp = os.path.join(d, "pairs.json")
    old = json.load(open(jp)) if os.path.exists(jp) and os.environ.get("DESKTOP_CU") else []
    keep = {p["key"] for p in pairs}
    pairs = [p for p in old if p["key"] not in keep] + pairs
    with open(jp, "w") as f:
        json.dump(pairs, f, indent=1)
    import subprocess
    subprocess.run(["/opt/anaconda3/bin/python3", os.path.abspath(__file__), "--pairs", jp, d], check=False)
    log(f"close-ups: {len(pairs)} in {d}")
    return pairs


def pairs_sheet(jp, d):
    from PIL import Image, ImageDraw
    pairs = json.load(open(jp))
    W, H = 1600, 600
    rows = []
    for p in pairs:
        row = Image.new("RGB", (W, H + 40), (24, 24, 26))
        dr = ImageDraw.Draw(row)
        dr.text((12, 10), p["title"] + "   (left: reference photo, right: our model)", fill=(235, 235, 235))
        for i, f in enumerate((p["photo"], p["render"])):
            im = Image.open(f)
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
                bg = Image.new("RGB", im.size, (200, 200, 204))
                bg.paste(im, mask=im.split()[3])
                im = bg
            im = im.convert("RGB")
            if i == 0 and p.get("crop"):
                x0, x1, y0, y1 = p["crop"]
                im = im.crop((x0, y0, min(x1, im.width), min(y1, im.height)))
            im.thumbnail((W // 2 - 20, H))
            row.paste(im, (i * W // 2 + 10, 40))
        row.save(os.path.join(d, f"{p['key']}-pair.jpg"), quality=88)
        rows.append(row)
    for k in range(0, len(rows), 4):
        part = rows[k:k + 4]
        s = Image.new("RGB", (W, sum(r.height for r in part)))
        y = 0
        for r in part:
            s.paste(r, (0, y))
            y += r.height
        s.save(os.path.join(d, f"closeups-sheet-{k // 4 + 1}.jpg"), quality=85)
    print("SHEETS", d)


def stage_compare(out, names):
    from lib import compare
    subs = [m for o in bpy.data.objects if o.type == "MESH" for m in o.modifiers if m.type == "SUBSURF"]
    for m in subs:            # the silhouette search renders hundreds of times: the mouse shell unsubdivided
        m.show_render = False
    rep = compare.run(outline_views(names), os.path.join(out, "compare"), NAME, log=log)
    for m in subs:
        m.show_render = True
    log(f"compare test {'PASSED' if rep['test']['passed'] else 'FAILED'}: {rep['paths']['md']}")
    return rep["test"]


def _export(objs, path):
    from lib import run
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select_set(o.name in objs)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_cameras=False, export_lights=False, export_extras=False)
    return run.glb_stats(path)


def _with_empties(names):
    keep = set(names)
    for o in bpy.data.objects:
        if o.name in keep:
            p = o.parent
            while p is not None:
                keep.add(p.name)
                p = p.parent
    return keep


# the lite bake helpers, copied from speakers_render.py (importing that module runs its whole job)
def _ctx(obj, objs=None):
    wm = bpy.data.window_managers[0]
    objs = objs or [obj]
    kw = dict(active_object=obj, object=obj, selected_objects=objs, selected_editable_objects=objs)
    if wm.windows and not bpy.app.background:
        kw.update(window=wm.windows[0], screen=wm.windows[0].screen)
    return bpy.context.temp_override(**kw)


def _image(name, size, data=False):
    im = bpy.data.images.get(name)
    if im is not None:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    if data:
        im.colorspace_settings.name = "Non-Color"
    return im


def _bake(objs, target, kind, samples=4):
    """Bake one channel of all `objs` into `target`: 'base', 'rough', 'metal' (an emission rewire) or 'ao'."""
    scene = bpy.context.scene
    restore = []
    seen = set()
    for o in objs:
        for mat in o.data.materials:
            if mat.name in seen:
                continue
            seen.add(mat.name)
            nt = mat.node_tree
            tn = nt.nodes.new("ShaderNodeTexImage")
            tn.image = target
            nt.nodes.active = tn
            restore.append((mat, tn, None))
            if kind == "ao":
                continue
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
            em = next((n for n in nt.nodes if n.type == "EMISSION"), None)
            e = nt.nodes.new("ShaderNodeEmission")
            if b is not None:
                sock = b.inputs[{"base": "Base Color", "rough": "Roughness", "metal": "Metallic"}[kind]]
                if sock.is_linked:
                    nt.links.new(sock.links[0].from_socket, e.inputs["Color"])
                else:
                    dv = sock.default_value
                    e.inputs["Color"].default_value = tuple(dv) if kind == "base" else (dv, dv, dv, 1.0)
            else:
                c = tuple(em.inputs["Color"].default_value) if em else (1, 1, 1, 1)
                e.inputs["Color"].default_value = c if kind == "base" else ((0.5,) * 3 + (1,) if kind == "rough" else (0, 0, 0, 1))
            old = out.inputs["Surface"].links[0].from_socket
            nt.links.new(e.outputs[0], out.inputs["Surface"])
            restore[-1] = (mat, tn, (e, old, out))
    scene.cycles.samples = samples
    scene.render.bake.margin = 4
    scene.render.bake.use_clear = True
    scene.render.bake.target = "IMAGE_TEXTURES"
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    with _ctx(objs[0], objs):
        bpy.ops.object.bake(type="AO" if kind == "ao" else "EMIT")
    for mat, tn, rw in restore:
        nt = mat.node_tree
        if rw:
            e, old, out = rw
            nt.links.new(old, out.inputs["Surface"])
            nt.nodes.remove(e)
        nt.nodes.remove(tn)


def _gltf_group():
    g = bpy.data.node_groups.get("glTF Material Output")
    if g is None:
        g = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
        g.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    return g


EMISSIVE_PREFIX = ("mat_desktop_led", "mat_desktop_deck_icon", "mat_brand")


def bake_lite(objs, out, size=1024, orm_size=512):
    """One base-colour atlas and an ORM map (AO, roughness, metal) for every lite mesh that is not emissive or
    a brand decal, as the speakers and screens did (speakers_render._bake). Emissive parts keep their own small
    materials. Shared key meshes are made single-user first (one UV island each)."""
    import numpy as np
    from lib import materials as M
    from lib import renderqueue
    scene = bpy.context.scene

    def emissive(o):
        return any(m and (m.name.startswith(EMISSIVE_PREFIX) or "brand" in m.name) for m in o.data.materials)
    baked = [o for o in objs if o.type == "MESH" and not emissive(o) and "brand" not in o.name]
    for o in baked:
        if o.data.users > 1:
            o.data = o.data.copy()
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in baked:
        lay = o.data.uv_layers.new(name="UVMap")
        o.data.uv_layers.active = lay
        o.select_set(True)
    bpy.context.view_layer.objects.active = baked[0]
    with _ctx(baked[0], baked):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.002, correct_aspect=True,
                                 scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    prev = scene.render.engine
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "METAL"
    scene.cycles.device = "GPU"
    scene.cycles.use_denoising = False
    hidden = []
    for o in scene.objects:
        if o not in baked and o.type == "MESH" and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.light_settings.distance = 0.01
    base = _image("desktop_atlas", size)
    rough = _image("desktop_rough_tmp", orm_size, True)
    metal = _image("desktop_metal_tmp", orm_size, True)
    ao = _image("desktop_ao_tmp", orm_size, True)
    with renderqueue.slot("desktop lite bake"):
        _bake(baked, base, "base", 4)
        _bake(baked, rough, "rough", 4)
        _bake(baked, metal, "metal", 4)
        _bake(baked, ao, "ao", 32)
    for o in hidden:
        o.hide_render = False
    orm = _image("desktop_orm", orm_size, True)
    px = np.empty(orm_size * orm_size * 4, np.float32)
    ch = []
    for im in (ao, rough, metal):
        im.pixels.foreach_get(px)
        ch.append(px.reshape(-1, 4)[:, 0].copy())
    o4 = np.ones((orm_size * orm_size, 4), np.float32)
    o4[:, 0] = 0.4 + 0.6 * ch[0]
    o4[:, 1], o4[:, 2] = ch[1], ch[2]
    orm.pixels.foreach_set(o4.ravel())
    for im in (rough, metal, ao):
        bpy.data.images.remove(im)
    kb = {}
    for im, fn, q in ((base, "desktop_atlas.jpg", 90), (orm, "desktop_orm.jpg", 92)):
        p = os.path.join(out, fn)
        im.filepath_raw = p
        im.file_format = "JPEG"
        scene.render.image_settings.quality = q
        im.save()
        kb[fn] = round(os.path.getsize(p) / 1024)
    m, nt, b = M._new("mat_desktop_lite")
    tb = nt.nodes.new("ShaderNodeTexImage")
    tb.image = base
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = orm
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sep.inputs[0])
    nt.links.new(tb.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(sep.outputs[1], b.inputs["Roughness"])
    nt.links.new(sep.outputs[2], b.inputs["Metallic"])
    gg = nt.nodes.new("ShaderNodeGroup")
    gg.node_tree = _gltf_group()
    nt.links.new(sep.outputs[0], gg.inputs["Occlusion"])
    for o in baked:
        o.data.materials.clear()
        o.data.materials.append(m)
    scene.render.engine = prev
    return kb


def stage_export(out, names, bake=True):
    d = os.path.join(BLENDER_DIR, "out", "components")
    os.makedirs(d, exist_ok=True)
    rich = _export(_with_empties(names["all"]), os.path.join(d, f"{NAME}-rich.glb"))
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    lite_names = build(lite=True)
    objs = [bpy.data.objects[n] for n in lite_names["all"]]
    kb = bake_lite(objs, out) if bake else {}
    lite = _export(_with_empties(lite_names["all"]), os.path.join(d, f"{NAME}-lite.glb"))
    per = {}
    for p in PARTS:
        if p in lite_names:
            per[p] = sum(sum(len(f.vertices) - 2 for f in bpy.data.objects[n].data.polygons)
                         for n in lite_names[p] if bpy.data.objects[n].type == "MESH")
    log(f"GLB rich {rich['kb']} KB {rich['triangles']} tris; lite {lite['kb']} KB {lite['triangles']} tris {per} {kb}")
    return {"rich": rich, "lite": lite, "lite_per_part": per, "images_kb": kb}


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    st = next((x for x in a if not x.startswith("--") and os.path.sep not in x), "default")
    stages = ["build", "stills", "compare", "closeups", "export"] if st == "default" else st.split(",")
    out = FOOT if PART == "all" else os.path.join(FOOT, PART)
    os.makedirs(out, exist_ok=True)
    rep = {"stages": stages}
    t0 = time.time()
    names = None
    cycles = "--cycles" in a or os.environ.get("DESKTOP_CYCLES") == "1"     # Blender 5.2 eats a bare --cycles
    if "outline" in stages:
        r = stage_outline(out)
        rep["outline"] = {"passed": r["test"]["passed"], "sheet": r.get("sheet")}
    if "build" in stages:
        names = stage_build(out)
    elif any(s in stages for s in ("stills", "compare", "export", "closeups")):
        bpy.ops.wm.open_mainfile(filepath=os.path.join(BLENDER_DIR, "out", "components", f"{NAME}.blend"))
        names = json.load(open(os.path.join(out, f"{NAME}-names.json")))
    if "stills" in stages:
        rep["stills"] = stage_stills(out, names, cycles)
    if "compare" in stages:
        rep["compare"] = stage_compare(out, names)
    if "closeups" in stages:
        rep["closeups"] = stage_closeups(out, names, cycles)
    if "export" in stages:
        rep["export"] = stage_export(out, names, bake="--nobake" not in a)
    rep["total_s"] = round(time.time() - t0, 1)
    with open(os.path.join(out, f"{NAME}-report{'-' + st if st != 'default' else ''}.json"), "w") as f:
        json.dump(rep, f, indent=1, default=str)
    log(f"done in {rep['total_s']} s: {out}")


def make_cutouts():
    """Plain Python: the Stream Deck silhouettes from Elgato's dark-backdrop images (bright white deck and stand,
    holes filled), written to CUT; the photos are never touched."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage as nd
    os.makedirs(CUT, exist_ok=True)
    for src, dst, crop, thr in (("gallery-01.jpg", "deck-gallery-01-cut.png", None, 0.42),
                                ("desk-white-lowangle.jpg", "deck-lowangle-cut.png", (760, 1650, 930, 1490), 0.40)):
        im = Image.open(os.path.join(R_SD, src)).convert("RGB")
        a = np.asarray(im) / 255.0
        k = (a.mean(-1) > thr) & ((a.max(-1) - a.min(-1)) < 0.18)
        if crop:
            x0, x1, y0, y1 = crop
            box_ = np.zeros_like(k)
            box_[y0:y1, x0:x1] = True
            k &= box_
        k = nd.binary_closing(k, iterations=4)
        lab, n = nd.label(k)
        k = lab == (np.argmax(nd.sum(k, lab, range(1, n + 1))) + 1)
        k = nd.binary_fill_holes(nd.binary_closing(k, iterations=8))
        k = nd.binary_opening(k, iterations=2)
        Image.fromarray(np.dstack([a * 255, k * 255]).astype(np.uint8), "RGBA").save(os.path.join(CUT, dst))
    print("CUTOUTS", CUT)


if __name__ == "__main__":
    if bpy is not None:
        main()
        bpy.ops.wm.quit_blender()
    elif "--cutouts" in sys.argv:
        make_cutouts()
    elif "--pairs" in sys.argv:
        i = sys.argv.index("--pairs")
        pairs_sheet(sys.argv[i + 1], sys.argv[i + 2])
