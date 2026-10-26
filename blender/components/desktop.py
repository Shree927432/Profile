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

# MX Master 3S (23-mouse/SOURCES.md): 124.9 long, 84.3 wide, 51 high OFFICIAL. Rebuilt on a 3D scan (decision
# 2026-10-26): "Logitech MX Master 3S - Revopoint Mini 3D Scan" by Sircher, CC BY. Our own quad shell is wrapped
# onto the scan by components/mouse_scan.py and saved to assets/mouse/mx-master-3s-shell.json; the scan itself
# never ships. Feature positions MEASURED on the scan's depth maps (mm, nose +Y, thumb side -X, desk z = 0).
MS_L, MS_W, MS_H = 124.9, 84.3, 51.0
MS_SHELL = os.path.join(BLENDER_DIR, "assets", "mouse", "mx-master-3s-shell.json")
MS_WHEEL = (10.7, 33.5, 25.0, 10.0, 6.0)     # MEASURED scan: centre x, y, z; radius (the crown at z 35.0); width
MS_SLOT = (7.0, 14.6, 27.7, 46.3)            # MEASURED scan: the slot opening x0, x1, y0, y1
MS_HOUSING = (5.4, 17.0, 16.3, 49.7)         # MEASURED scan: the wheel housing's seams x0, x1, rear y, front y
MS_SPLIT_X = 10.7                             # MEASURED scan: the left/right split, the slot to the nose
MS_MID = (10.7, 13.7, 5.4, 8.0)              # MEASURED scan: the mode button x, y, w, l
MS_LOGO = (-9.3, 20.0, 12.0)                 # MEASURED top.png (frame matched to the scan): "logi" x, y, turn (deg)
MS_THUMB = (2.7, 40.0, 9.0, 7.0, 4.0)        # MEASURED scan: thumb wheel y, z; radius, width (EST); 4.0 out of the pocket floor (1.0 past the wall)
MS_POCKET = (-3.5, 41.8, 30.0, 7.5)          # MEASURED scan: the silver pocket y, z, length, height
MS_SIDE_BTNS = [(-7.7, 32.9), (6.1, 28.7)]   # MEASURED scan: back, forward button centres y, z (11.5 x 4.4 each)
MS_LED = (-13.0, 43.5)                       # MEASURED scan / side-thumb.jpg: behind the wheel on the pocket
MS_USB = (10.6, 8.0)                         # MEASURED scan: USB-C on the nose x, z
MS_REST_EDGE = [(21.7, 7.9), (23.0, 11.2), (22.3, 17.9), (19.0, 23.2), (9.7, 23.9), (-1.0, 25.2), (-14.3, 29.0),
                (-25.0, 28.6), (-40.0, 26.0)]   # MEASURED scan (thumb side): the thumb rest's top edge y, z
MS_RIGHT_SEAM = [(35.0, 9.7, 60.0), (42.6, 10.4, 37.0), (44.3, 21.4, 30.0), (45.4, 36.4, 23.0), (44.0, 44.4, 19.7),
                 (40.4, 51.4, 14.0)]       # MEASURED scan (right side): the right button's outer edge (x, y, z approx)

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
    p["ms_side"] = get("mat_desktop_mouse_side", base="#a9acb1", rough=0.34, metal=0.6)
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
# 2c. MX Master 3S. Origin: desk under the top-view centre; nose +Y; thumb side -X.
# ---------------------------------------------------------------------------
_MS_SHELL = {}


def ms_shell(res):
    if not _MS_SHELL:
        _MS_SHELL.update(json.load(open(MS_SHELL)))
    return _MS_SHELL[res]


def _shell_obj(name, data, key, mp, coll, parent, smooth=60):
    from lib import parts as P
    A = P.Mesh()
    vs = A.verts([tuple(c * MM for c in v) for v in data["v"]])
    for f in data["f"]:
        A.face([vs[i] for i in f], key)
    return A.finish(name, mp, "+Z", (0, 0, 0), coll, parent, smooth=smooth)


def build_mouse(coll, mp, rough=False, lite=False):
    """MX Master 3S. Origin: desk under the top-view centre; nose +Y; thumb side -X. The body is our quad shell
    wrapped onto the scan (assets/mouse/); every detail is built here, placed by the scan's features."""
    from lib import parts as P
    from mathutils.bvhtree import BVHTree
    import bmesh as _bm
    sfx = "_lite" if lite else ""
    names = {}
    root = empty("mouse" + sfx, coll=coll)
    sh = ms_shell("lite" if (lite or rough) else "rich")
    body = _shell_obj("mouse_body" + sfx, sh["body"], "ms_top", mp, coll, root, smooth=70)
    band = _shell_obj("mouse_band" + sfx, sh["band"], "ms_side", mp, coll, root, smooth=70)
    if not (lite or rough):
        for o in (body, band):
            sub = o.modifiers.new("subsurf", "SUBSURF")
            sub.levels = sub.render_levels = 1
            sub.boundary_smooth = "PRESERVE_CORNERS"
    names["body"] = [body.name, band.name]
    if not (lite or rough):            # the thumb rest's fine diagonal ridges: its own bump-mapped material
        body.data.materials.append(mp["ms_thumb"])
        ti = len(body.data.materials) - 1
        for f in body.data.polygons:
            c = f.center / MM
            if c.z > 8 and c.x < -21.0 and c.y < 16.0 and f.normal.z > 0.3:
                f.material_index = ti
    if rough:
        return root, names
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(body, dg), BVHTree.FromObject(band, dg)]

    def ray(o, d):
        best = None
        for t in trees:
            h = t.ray_cast(Vector(o), Vector(d))
            if h[0] is not None and (best is None or h[3] < best[3]):
                best = h
        return (best[0], best[1].normalized()) if best else (None, None)

    def near(p):
        best = None
        for t in trees:
            h = t.find_nearest(Vector(p))
            if h[0] is not None and (best is None or h[3] < best[3]):
                best = h
        return best[0], best[1].normalized()

    def top(x, y):
        return ray(mm(x, y, 100.0), (0, 0, -1))

    def side(y, z, sgn=-1):            # the thumb wall (sgn -1) or the right wall, seen from outside
        return ray(mm(sgn * 100.0, y, z), (-sgn, 0, 0))

    def ribbon(A, pts, w, key, lift=0.2, closed=False):
        """A thin line on the shell along surface points [(loc, nrm)]; w and lift in mm."""
        n = len(pts)
        L, R_ = [], []
        for i, (p, nr) in enumerate(pts):
            a = pts[(i - 1) % n][0] if (closed or i > 0) else p
            b = pts[(i + 1) % n][0] if (closed or i < n - 1) else p
            t = (b - a).normalized()
            s = t.cross(nr).normalized() * (w / 2 * MM)
            q = p + nr * lift * MM
            L.append(q + s)
            R_.append(q - s)
        lv, rv = A.verts(L), A.verts(R_)
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            A.face([lv[i], rv[i], rv[j], lv[j]], key)

    def dense(poly, step=1.5):
        out = []
        for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
            k = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
            out += [(x0 + (x1 - x0) * j / k, y0 + (y1 - y0) * j / k) for j in range(k)]
        return out + [poly[-1]]

    def top_line(poly, step=1.5):
        return [h for h in (top(x, y) for x, y in dense(poly, step)) if h[0] is not None]

    # seams (MEASURED scan): the split from the slot to the nose, the wheel housing, the buttons' rear edges,
    # the right button's outer edge, the mode button; the band's top edge all round
    A = P.Mesh()
    w = 0.5 if not lite else 0.7
    st = 1.5 if not lite else 4.0
    hx0, hx1, hy0, hy1 = MS_HOUSING
    ribbon(A, top_line([(MS_SPLIT_X, hy1), (MS_SPLIT_X, 66.0)], st), w, "ms_line")
    ribbon(A, top_line([(hx0, hy0), (hx0, hy1), (hx1, hy1), (hx1, hy0)], st), w, "ms_line")
    ribbon(A, top_line([(hx0, hy0), (-14.1, 13.7)], st), w, "ms_line")
    rs = [near(mm(x + 6.0, y, z)) if z < 50 else top(x, y) for x, y, z in MS_RIGHT_SEAM]
    rs = [top((hx1 + 35.0) / 2, (hy0 + 9.7) / 2)] + rs
    rs = [top(hx1, hy0)] + rs
    dn = []
    for (pa, _), (pb, _) in zip(rs, rs[1:]):
        k = max(1, int((pb - pa).length / MM / st))
        dn += [near(pa.lerp(pb, j / k)) for j in range(k)]
    ribbon(A, dn + [near(rs[-1][0])], w, "ms_line")
    mx, my, mw, ml = MS_MID
    ribbon(A, top_line([(mx - mw / 2 - 0.4, my - ml / 2 - 0.4), (mx + mw / 2 + 0.4, my - ml / 2 - 0.4),
                        (mx + mw / 2 + 0.4, my + ml / 2 + 0.4), (mx - mw / 2 - 0.4, my + ml / 2 + 0.4),
                        (mx - mw / 2 - 0.4, my - ml / 2 - 0.4)], 1.0), 0.4, "ms_line")
    d0 = Vector((38.0, 0.0, -45.0)).normalized()        # the thumb rest's top edge, seen from outside and above
    re_ = []
    for (ya, za), (yb, zb) in zip(MS_REST_EDGE, MS_REST_EDGE[1:]):
        k = max(1, int(math.hypot(yb - ya, zb - za) / st))
        for j in range(k):
            y_, z_ = ya + (yb - ya) * j / k, za + (zb - za) * j / k
            h_ = ray(mm(-60.0, y_, z_ + 45.0), d0)
            if h_[0] is not None:
                re_.append(h_)
    if len(re_) > 2:
        ribbon(A, re_, w, "ms_line")
    nb = len(sh["body"]["v"]) - 1                       # the band edge: the body's first ring
    nu = len(sh["body"]["f"]) - len([f for f in sh["body"]["f"] if len(f) == 4])
    nk1 = nb // nu
    if not lite:                                       # the web model shows the band edge by its material alone
        edge = [near(mm(*sh["body"]["v"][i * nk1])) for i in range(nu)]
        ribbon(A, edge, 0.45, "ms_line", lift=0.15, closed=True)
    seams = fin(A, "mouse_seams" + sfx, mp, coll, root, smooth=0)
    names["seams"] = [seams.name]
    # the wheel slot: a dark patch on the shell, the MagSpeed wheel through it
    x0, x1, y0, y1 = MS_SLOT
    A = P.Mesh()
    nx_, ny_ = (3, 6) if lite else (6, 16)
    grid = [[top(x0 + (x1 - x0) * i / nx_, y0 + (y1 - y0) * j / ny_) for i in range(nx_ + 1)] for j in range(ny_ + 1)]
    gv = [[A.verts([p + n * 0.25 * MM])[0] for p, n in row] for row in grid]
    for j in range(ny_):
        for i in range(nx_):
            A.face([gv[j][i], gv[j][i + 1], gv[j + 1][i + 1], gv[j + 1][i]], "ms_slot")
    slot = fin(A, "mouse_wheel_slot" + sfx, mp, coll, root, smooth=0)
    wx, wy, wz, wr, ww = MS_WHEEL
    A = P.Mesh()
    seg = 16 if lite else 240
    ridge = (lambda a: 1.0 - 0.02 * (0.5 + 0.5 * math.cos(a * 60))) if not lite else None
    if lite:
        prof = [(0, -ww / 2), (wr - 0.6, -ww / 2), (wr, -ww / 2 + 0.6), (wr, ww / 2 - 0.6), (wr - 0.6, ww / 2), (0, ww / 2)]
    else:
        prof = [(0, -ww / 2), (wr - 0.6, -ww / 2), (wr, -ww / 2 + 0.6), (wr, -0.9), (wr - 0.5, -0.5), (wr - 0.5, 0.5),
                (wr, 0.9), (wr, ww / 2 - 0.6), (wr - 0.6, ww / 2), (0, ww / 2)]
    prof = [(r_ * MM, z * MM, ridge) if (ridge and abs(r_ - wr) < 1e-6) else (r_ * MM, z * MM) for r_, z in prof]
    A.lathe(prof, seg, "ms_wheel", m=T(wx * MM, wy * MM, wz * MM) @ R(90, "Y"))
    wheel = fin(A, "mouse_wheel" + sfx, mp, coll, root, smooth=40)
    # the mode button behind the housing: a low rounded key on the shell
    loc, nrm = top(mx, my)
    A = P.Mesh()
    P._rbox(A, mw * MM, ml * MM, 1.4 * MM, 1.2 * MM, 0.5 * MM, 0.0, 1 if lite else 3, "ms_top", z0=-0.8 * MM)
    mode = fin(A, "mouse_mode_button" + sfx, mp, coll, root, smooth=40)
    yl = (Vector((0, 1, 0)) - nrm * nrm.y).normalized()
    mf = Matrix((yl.cross(nrm), yl, nrm)).transposed().to_4x4()
    mf.translation = loc
    mode.matrix_basis = mf
    names["wheels"] = [slot.name, wheel.name, mode.name]

    # the thumb side: the silver pocket, the slim thumb wheel set into it (axis up the wall, only an arc out),
    # the back / forward buttons and the green LED (scan, side-thumb.jpg, closeup-thumb-area.jpg)
    def wall_frame(y, z):
        p_, n_ = side(y, z)
        if p_ is None:
            p_, n_ = Vector(mm(-30.0, y, z)), Vector((-1, 0, 0))
        zl = Vector((n_.x, 0.0, n_.z)).normalized()
        yl = Vector((0, 1, 0))
        xl = yl.cross(zl)
        m_ = Matrix((xl, yl, zl)).transposed().to_4x4()
        m_.translation = p_
        return m_
    py_, pz_, pl_, ph_ = MS_POCKET                       # a rounded silver panel laid onto the wall (projected)
    Mp = wall_frame(py_, pz_)
    zl = Mp.to_3x3() @ Vector((0, 0, 1))
    A = P.Mesh()
    out_ = P.ccw(P.stadium(ph_, pl_, 2 if lite else 6))   # (up the wall, along y) in mm
    rv = []
    for s_ in ((1.0,) if lite else (1.0, 0.66, 0.33)):
        pts = []
        for v_, u_ in out_:
            q = Mp @ Vector(mm(v_ * s_, u_ * s_, 6.0))
            h_ = ray(q, -zl)
            pts.append(h_[0] + h_[1] * 0.25 * MM if h_[0] is not None else Mp @ Vector(mm(v_ * s_, u_ * s_, 0.25)))
        rv.append(A.verts(pts))
    for a_, b_ in zip(rv, rv[1:]):
        A.strip(a_, b_, "ms_side")
    A.face(rv[-1], "ms_side")
    pocket = fin(A, "mouse_thumb_pocket" + sfx, mp, coll, root, smooth=40)
    ty, tz, tr, tw, tshow = MS_THUMB
    A = P.Mesh()
    knurl = (lambda a: 1.0 - 0.04 * (0.5 + 0.5 * math.cos(a * 48))) if not lite else None
    h2 = tw / 2
    if lite:
        prof = [(0, -h2), (tr - 0.5, -h2), (tr, -h2 + 0.5), (tr, h2 - 0.5), (tr - 0.5, h2), (0, h2)]
    else:
        prof = [(0, -h2), (tr - 0.5, -h2), (tr, -h2 + 0.5, knurl), (tr, h2 - 0.5, knurl), (tr - 0.5, h2), (0, h2)]
    prof = [(p[0] * MM, p[1] * MM, p[2]) if len(p) > 2 and p[2] else (p[0] * MM, p[1] * MM) for p in prof]
    A.lathe(prof, 12 if lite else 200, "ms_wheel", m=R(90, "Y"))
    thumb = fin(A, "mouse_thumbwheel" + sfx, mp, coll, root, smooth=40)
    thumb.matrix_basis = wall_frame(ty, tz) @ T(0, 0, -(tr - tshow) * MM)
    A = P.Mesh()
    a_ = math.degrees(math.atan2(-(MS_SIDE_BTNS[1][1] - MS_SIDE_BTNS[0][1]), MS_SIDE_BTNS[1][0] - MS_SIDE_BTNS[0][0]))
    for yy, zz in MS_SIDE_BTNS:
        n0 = len(A.bm.verts)
        P._rbox(A, 4.4 * MM, 11.5 * MM, 2.0 * MM, 2.0 * MM, 0.8 * MM, 0.0, 1 if lite else 4, "ms_top", z0=-1.0 * MM)
        A.bm.verts.ensure_lookup_table()
        _bm.ops.transform(A.bm, matrix=wall_frame(yy, zz) @ R(a_, "Z"), verts=A.bm.verts[n0:])
    btns = fin(A, "mouse_side_buttons" + sfx, mp, coll, root, smooth=40)
    A = P.Mesh()
    A.face(A.verts([(x * MM, y * MM, 0.0) for x, y in P.ccw(P.stadium(1.1, 3.4, 2 if lite else 4))]), "led_green")
    led = fin(A, "mouse_led" + sfx, mp, coll, root, smooth=0)
    led.matrix_basis = wall_frame(*MS_LED) @ T(0, 0, 0.4 * MM)
    names["thumb"] = [pocket.name, thumb.name, btns.name, led.name]
    # the nose: USB-C centred low, in the silver band
    ux, uz = MS_USB
    at_, _ = ray(mm(ux, 100.0, uz), (0, -1, 0))
    at_ = at_ if at_ is not None else Vector(mm(ux, 62.0, uz))
    hu = ray(mm(ux, 100.0, uz), (0, -1, 0))
    nu_ = hu[1] if hu[0] is not None else Vector((0, 1, 0))
    zu = Vector((0, 0, 1))
    zu = (zu - nu_ * zu.dot(nu_)).normalized()
    Mu = Matrix((zu.cross(nu_), zu, nu_)).transposed().to_4x4()
    Mu.translation = at_
    A = P.Mesh()
    sg = 3 if lite else 8
    A.face(A.verts([(x * MM, y * MM, 0.12 * MM) for x, y in P.ccw(P.stadium(11.0, 4.6, sg))], Mu), "ms_wheel")
    A.face(A.verts([(x * MM, y * MM, 0.22 * MM) for x, y in P.ccw(P.stadium(8.6, 2.8, sg))], Mu), "port")
    u = fin(A, "mouse_usb" + sfx, mp, coll, root, smooth=0)
    names["front"] = [u.name]
    # the feet (bottom.png): two long PTFE strips at the back, a round one at the nose
    A = P.Mesh()
    for fx, fy0, fy1 in ((-16.0, -40.0, -8.0), (30.0, -40.0, -8.0)):
        box(A, (fx - 3.2) * MM, (fx + 3.2) * MM, fy0 * MM, fy1 * MM, 0.0, 1.25 * MM, "rubber", r=0.0 if lite else 2.5 * MM,
            n=0 if lite else 4)
    A.lathe([(0, 0), (3.5 * MM, 0), (3.5 * MM, 1.25 * MM), (0, 1.25 * MM)], 8 if lite else 32, "rubber",
            m=T(MS_SPLIT_X * MM, 40.0 * MM, 0))
    feet = fin(A, "mouse_feet" + sfx, mp, coll, root, smooth=30)
    names["feet"] = [feet.name]
    # the invented name where "logi" sits: the left button, turned 12 deg, mid grey print, on the shell
    lx, ly, la = MS_LOGO
    loc, nrm = top(lx, ly)
    a = math.radians(la)
    up = Vector((-math.sin(a), math.cos(a), 0.0))
    up = (up - nrm * up.dot(nrm)).normalized()
    d = brand("mouse", root, "mouse_brand" + sfx, lite, at=tuple(loc), normal=tuple(nrm), up=tuple(up),
              height=4.6 * MM, max_width=10.0 * MM, finish="printed", colour="#7c7e82", conform=None if lite else body)
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
        SC = os.path.join(FOOT, "mouse-scan", "cutouts")       # silhouettes of the sketchfab-ref views (Krystian, view-only)
        v.append(dict(name="mouse-top", title="MX Master 3S: top (Logitech image) vs our model",
                      photo=os.path.join(R_MS, "top.png"), mask="alpha", objects=o, camera={"mode": "ortho", "view": "top"}))
        v.append(dict(name="mouse-front", title="MX Master 3S: nose-on (Logitech image) vs our model",
                      photo=os.path.join(R_MS, "front.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "back", "yaws": [-8.0, -4.0, 0.0, 4.0, 8.0],
                              "tilts": [-24.0, -18.0, -12.0, -6.0]},
                      explain="Logitech's nose-on shot is a perspective render from above; searched"))
        v.append(dict(name="mouse-side", title="MX Master 3S: thumb side (Logitech image) vs our model",
                      photo=os.path.join(R_MS, "side-thumb-profile.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "left", "yaws": [-60.0, -50.0, -40.0, -30.0],
                              "tilts": [-50.0, -40.0, -30.0]},
                      explain="a low three-quarter from the thumb side, not a profile; searched"))
        v.append(dict(name="mouse-thumb-profile", title="MX Master 3S: thumb side profile (sketchfab-ref) vs our model",
                      photo=os.path.join(SC, "side-thumb-cut.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "left", "yaws": [-6.0, -3.0, 0.0, 3.0, 6.0], "tilts": [-8.0, -4.0, 0.0]},
                      explain="a screenshot of another author's model: an edge cutout, the floor line filled flat"))
        v.append(dict(name="mouse-right", title="MX Master 3S: right side profile (sketchfab-ref) vs our model",
                      photo=os.path.join(SC, "side-right-profile-cut.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "right", "yaws": [-6.0, -3.0, 0.0, 3.0, 6.0], "tilts": [-8.0, -4.0, 0.0]},
                      explain="a screenshot of another author's model: an edge cutout, the floor line filled flat"))
        for k, vw, t in (("nose", "back", "nose-on"), ("thumb", "left", "thumb side"), ("right", "right", "right side")):
            v.append(dict(name=f"mouse-scan-{k}", title=f"MX Master 3S: {t}, orthographic (the 3D scan of the real mouse) vs our model",
                          photo=os.path.join(SC, f"scan-{k}-alpha.png"), mask="alpha", objects=o,
                          camera={"mode": "ortho", "view": vw}))
        v.append(dict(name="mouse-3q", title="MX Master 3S: top, thumb side (Logitech image) vs our model",
                      photo=os.path.join(R_MS, "three-quarter.png"), mask="alpha", objects=o,
                      camera={"mode": "free", "view": "top", "yaws": [-30.0, -20.0, -10.0, 0.0, 10.0],
                              "tilts": [-40.0, -30.0, -15.0]},
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
        SR = os.path.join(R_MS, "sketchfab-ref")
        lx, ly = MS_LOGO[:2]
        out += [
            ("mouse-wheels", "MX Master 3S: the scroll wheel, the button split and the mode button (sketchfab-ref)",
             os.path.join(SR, "closeup-top-wheel-and-button-split.jpg"),
             W("mouse", (-75, -45, 170)), W("mouse", (6, 30, 36)), 50),
            ("mouse-thumb", "MX Master 3S: the thumb wheel, the side buttons and the LED", (os.path.join(R_MS, "side-thumb-profile.png"),
                                                                                         (1900, 3000, 500, 1400)),
             W("mouse", (-120, 120, 95)), W("mouse", (-26, -2, 36)), 50),
            ("mouse-front", "MX Master 3S: the nose and USB-C", os.path.join(R_MS, "front.png"),
             W("mouse", (5, 260, 85)), W("mouse", (2, 30, 20)), 50),
            ("mouse-rest", "MX Master 3S: the thumb rest (sketchfab-ref)", os.path.join(SR, "closeup-thumb-area.jpg"),
             W("mouse", (-170, 60, 110)), W("mouse", (-22, -8, 22)), 50),
            ("mouse-band", "MX Master 3S: the back and the silver band (sketchfab-ref)", os.path.join(SR, "closeup-back-silver-band.jpg"),
             W("mouse", (-15, -230, 70)), W("mouse", (0, -20, 22)), 50),
            ("mouse-brand", "MX Master 3S: the name on the left button", (os.path.join(R_MS, "top.png"), (1000, 1800, 600, 1300)),
             W("mouse", (lx, ly, 150)), W("mouse", (lx, ly, 40)), 50),
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
    out = os.environ.get("DESKTOP_OUT") or (FOOT if PART == "all" else os.path.join(FOOT, PART))
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
