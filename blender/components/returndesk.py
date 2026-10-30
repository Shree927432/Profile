"""The return-desk group (component, 2026-10-31): the last AI-lab and music-side props.

    RETURNDESK_PART=laptop|dj|lightstick|all (default all)
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/components/returndesk.py -- [stages] [--nobake]

stages: outline | build,stills,compare,closeups,export (default) | any comma list.
Cycles: RETURNDESK_CYCLES=1 (never a bare `--cycles` after `--`: Blender 5.2's own parser takes it and stops the run).
RETURNDESK_OUT=<dir> renders somewhere else; RETURNDESK_CU=key,key limits the close-ups; RETURNDESK_STILLS=key,key the
stills. Plain Python (Pillow): python3 returndesk.py --pairs <pairs.json> <dir> | --legends <size> <png>
Room: build_room(collection, lite) places every part at plan v3's numbers (blender/design/room_v3_component_test.py).

Parts (plan v3 names, blender/lib/plan_v3.py):
  laptop      Apple MacBook Pro 16 silver, open 110 degrees (laptop_*), on a Rain Design mStand silver (mstand_*).
              laptop_screen is the display's face: a clean 0..1 UV, top-left at (0, 1), a dark desktop for now.
              laptop_hinge is the lid's pivot empty (rotate about its local X to open or close the lid).
  dj          the two-deck controller in the Pioneer DDJ-FLX4 shape (dj_*) on the slim black steel stand (dj_stand).
              Interactive meshes each have their origin on their own axis: dj_jog_l/_r (spin about local Z),
              dj_pad_l_01..08 / dj_pad_r_01..08 (press along -Z; 01..04 the back row left to right, 05..08 the front),
              dj_play_l/_r, dj_cue_l/_r, dj_tempo_l/_r (slide along local Y), dj_fader_l/_r (local Y),
              dj_xfader (local X), dj_knob_* (turn about local Z).
  lightstick  our own K-pop lightstick (no real group's design): a faceted clear shell (lightstick_shell) over a glowing
              core (lightstick_head, its own material for the site to recolour) on a white handle, in a white cradle.

Frames: every part has the viewer at -Y, Z up, origin on the surface it stands on:
  mstand_root     the stand's footprint centre on the desk; laptop_root sits on its plate (MSTAND_PLATE_POSE)
  dj_stand_root   the stand's footprint centre on the floor; dj_root on its top (the controller's bottom centre),
                  lightstick_root on its top at local x +0.27 (plan v3)
Brand names (content/room-brands.json via lib/brands.py): "laptop" a round mark on the lid's back (polished), "dj"
KORVA where the real unit prints its maker's name (top front centre, and the rear panel). The mStand carries none:
no logo shows in any reference photo. No model numbers or other printed text anywhere.
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
sys.path.insert(0, HERE)

try:
    import bpy
    import bmesh
    from mathutils import Matrix, Vector
except ImportError:
    bpy = None

import wall as WA        # shared mesh helpers only (obj_from_bm, lathe, boolean_cut, look_cam, _export, pairs_sheet ...)

NAME = "returndesk"
MM = 0.001
PART = os.environ.get("RETURNDESK_PART", "all")
PARTS = ["laptop", "dj", "lightstick"] if PART == "all" else PART.split(",")
REF = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab")
FOOT = os.path.join(REPO, "video-local", "footage", "2026-10-31-components", "returndesk")
FONTS = os.path.join(BLENDER_DIR, "assets", "fonts")
LAP_REF = os.path.join(REF, "06-laptop")
MS_REF = os.path.join(REF, "07-laptop-stand")
DJ_REF = os.path.join(REF, "14-dj-controller")

# ---------------------------------------------------------------------------
# 1. numbers (mm unless said), tagged OFFICIAL / MEASURED / EST
# ---------------------------------------------------------------------------
# MacBook Pro 16 (06-laptop/SOURCES.md)
LP_W, LP_D, LP_H = 355.7, 248.1, 16.8                 # OFFICIAL
LP_BASE_H = 11.2                                       # EST: the base half of the 16.8 (side profile)
LP_LID_T = LP_H - LP_BASE_H                            # 5.6
LP_LID_D = 241.0                                       # MEASURED front-open photo: the lid 0.671 of its width tall
LP_R = 9.5                                             # EST: plan-view corner radius (top-lid photo)
LP_OPEN = 110.0                                        # the lid's opening from closed (brief)
LP_HINGE = (119.5, 10.6)                               # EST: the hinge axis y, z in the base frame (rear top)
LP_WELL = (-139.5, 139.5, -15.3, 99.2)                 # MEASURED top-keyboard-deck (2.943 px/mm): x0, x1, y0, y1
LP_PAD = (-80.0, 80.0, -118.3, -18.4)                  # MEASURED: the trackpad 160 x 100
LP_GRILLE = (139.8, 176.0, -11.0, 96.0)                # MEASURED: |x| range and y of the speaker grilles
LP_NOTCH_FRONT = 54.0                                  # MEASURED: the thumb notch's width at the front edge
LP_SCREEN = (345.6, 223.4)                             # OFFICIAL 3456 x 2234 at 254 ppi
LP_BEZEL_TOP = 3.6                                     # EST: the black edge to the active area's top
LP_NOTCH = (36.6, 11.7)                                # MEASURED front-open photo: notch width, height from the edge
LP_GLASS_INSET = 1.4                                   # EST: the silver lid rim around the black glass
LP_MARK = 46.0                                         # EST: the lid logo's size on the 16-inch
# the keys from the top-keyboard-deck photo, in px: rows (y0, y1) and columns (id, x0, x1, legend)
_PX = 2.943
_R0, _R1, _R2, _R3, _R4, _R5 = (98, 150), (157, 205), (212, 260), (266, 314), (321, 369), (376, 424)
_NUM = [("grave", ("~", "`")), ("n1", ("!", "1")), ("n2", ("@", "2")), ("n3", ("#", "3")), ("n4", ("$", "4")),
        ("n5", ("%", "5")), ("n6", ("^", "6")), ("n7", ("&", "7")), ("n8", ("*", "8")), ("n9", ("(", "9")),
        ("n0", (")", "0")), ("minus", ("_", "-")), ("equal", ("+", "="))]
_FICON = ["sun_s", "sun", "mission", "search", "mic", "moon", "rewind", "playpause", "forward", "mute", "vol_down",
          "vol_up"]


def laptop_keys():
    """[(id, x0, x1, y0, y1 (mm, base frame), legend)] for the 16-inch's 78 keys (MEASURED top-keyboard-deck)."""
    out = []

    def k(kid, x0, x1, row, leg, half=None):
        y0p, y1p = row
        if half == "top":
            y1p = (y0p + y1p) / 2 - 1.5
        elif half == "bot":
            y0p = (y0p + y1p) / 2 + 1.5
        out.append((kid, (x0 - 626.5) / _PX, (x1 - 626.5) / _PX, 124.05 - (y1p - 22) / _PX, 124.05 - (y0p - 22) / _PX, leg))
    p = 55.7
    k("esc", 226, 302, _R0, "esc")
    for i in range(12):
        k(f"f{i + 1}", 309 + i * p, 357 + i * p, _R0, (f"[{_FICON[i]}]", f"F{i + 1}"))
    k("touchid", 980, 1030, _R0, "")
    k(_NUM[0][0], 226, 274, _R1, _NUM[0][1])
    for i, (kid, leg) in enumerate(_NUM[1:]):
        k(kid, 281 + i * p, 329 + i * p, _R1, leg)
    k("delete", 952, 1028, _R1, "[larrow_s]")
    k("tab", 226, 302, _R2, "[tab]")
    for i, (kid, leg) in enumerate(list(zip("qwertyuiop", "QWERTYUIOP")) +
                                   [("lbracket", ("{", "[")), ("rbracket", ("}", "]")), ("backslash", ("|", "\\"))]):
        k(kid, 309 + i * p, 357 + i * p, _R2, leg)
    k("caps", 226, 316, _R3, "[caps]")
    for i, (kid, leg) in enumerate(list(zip("asdfghjkl", "ASDFGHJKL")) + [("semicolon", (":", ";")), ("quote", ('"', "'"))]):
        k(kid, 323 + i * p, 371 + i * p, _R3, leg)
    k("return", 938, 1028, _R3, "[enter]")
    k("lshift", 226, 344, _R4, "[shift]")
    for i, (kid, leg) in enumerate(list(zip("zxcvbnm", "ZXCVBNM")) +
                                   [("comma", ("<", ",")), ("period", (">", ".")), ("slash", ("?", "/"))]):
        k(kid, 351 + i * p, 399 + i * p, _R4, leg)
    k("rshift", 910, 1028, _R4, "[shift]")
    for kid, x0, x1, leg in (("fn", 226, 275, "[globe] fn"), ("lctrl", 281, 330, ("^", "control")),
                             ("lopt", 337, 386, ("[opt]", "option")), ("lcmd", 392, 456, ("[cmd]", "command")),
                             ("space", 463, 736, ""), ("rcmd", 742, 806, ("[cmd]", "command")),
                             ("ropt", 812, 861, ("[opt]", "option"))):
        k(kid, x0, x1, _R5, leg)
    k("left", 869, 918, _R5, "[tri_left]", "bot")
    k("up", 924, 973, _R5, "[tri_up]", "top")
    k("down", 924, 973, _R5, "[tri_down]", "bot")
    k("right", 979, 1028, _R5, "[tri_right]", "bot")
    return out


LP_KEY_TOP = LP_BASE_H - 0.25                          # EST: the caps' tops just under the deck
LP_KEY_FLOOR = LP_BASE_H - 1.6                         # EST: the black well floor
LP_LEGEND_INK = "#f1f1f1"
LP_KEY_RGB = "#0a0a0b"

# Rain Design mStand (07-laptop-stand/SOURCES.md): 253 x 262 x 150 OFFICIAL; the rest MEASURED on the drawings
MS_W, MS_D, MS_H = 253.0, 262.0, 150.0                 # OFFICIAL
MS_T = 10.0                                            # MEASURED dims-side: the plate's thickness
MS_SLOPE = 17.0                                        # MEASURED dims-side: the plate's slope (deg)
MS_FRONT_Z = 74.0                                      # MEASURED dims-side: the plate's centreline at the front end
MS_FRONT_Y = -130.0                                    # the plate's front end (centreline)
MS_BEND = (100.0, 124.0)                               # MEASURED dims-side: the upright's centreline y at top, bottom (it leans back toward the floor)
MS_BASE_FRONT = -69.0                                  # MEASURED dims-side (outline check): the base plate's front end (y)
MS_WAIST = 0.92                                        # MEASURED dims-front: the upright's narrowest width / 253
MS_HOLE = 62.0                                         # MEASURED detail-side-hole: the upright's round hole
MS_DROP = 17.0                                         # EST: the teardrop hole in the plate
MS_LIP = (48.0, 14.0, 7.0, 4.0)                        # EST from top-surface-pads-lip: each tab's width, the gap, height, thickness
MS_PAD = (6.0, 1.0)                                    # EST: the 8 clear silicone pads, radius, thickness

# Pioneer DJ DDJ-FLX4 (14-dj-controller/SOURCES.md): 482 x 272.8 x 59.2 OFFICIAL; layout MEASURED on the top view
DJ_W, DJ_D, DJ_H = 482.0, 272.8, 59.2                  # OFFICIAL
DJ_FEET = 2.5                                          # MEASURED front-edge photo: the feet under the body
DJ_TOP = 39.0                                          # MEASURED front-edge photo (3.07 px/mm): the top surface's height
DJ_R = 9.0                                             # MEASURED top view: plan corner radius
DJ_MIX_X = 76.9                                        # MEASURED: the mixer panel's half-width
DJ_JOG = (157.5, 22.1, 70.0, 57.0)                     # MEASURED: |x|, y, outer ring radius, platter radius
DJ_JOG_H = (11.0, 14.0)                                # MEASURED front edge: ring top, platter top above the surface
DJ_PAD_X = (-191.0, -168.6, -146.4, -124.2)            # MEASURED: the left deck's pad columns
DJ_PAD_Y = (-87.7, -110.4)                             # MEASURED: the two pad rows
DJ_PAD = 17.6                                          # MEASURED: pad size
DJ_DECK_DX = 314.9                                     # MEASURED: the right deck is the left one moved this far
DJ_CUE = (-218.5, -76.8, 12.4)                         # MEASURED: cue x, y, radius; play below it
DJ_PLAY_Y = -105.5
DJ_TEMPO = (-96.7, -46.6, -113.0, -79.8)               # MEASURED: x, slot y0, y1, the cap's centre position
DJ_CH = (20.0, -46.6, -91.9, -69.2)                    # MEASURED: |x|, slot y0, y1, the cap
DJ_XF = (19.5, -117.6)                                 # MEASURED: half travel, y
DJ_KNOBS = {   # name: (x, y, radius) MEASURED top view
    "trim_l": (-20.1, 98.0, 7.0), "trim_r": (19.8, 98.0, 7.0), "hi_l": (-20.1, 72.9, 7.5), "hi_r": (19.8, 72.9, 7.5),
    "mid_l": (-20.1, 47.8, 7.5), "mid_r": (19.8, 47.8, 7.5), "low_l": (-20.1, 23.0, 7.5), "low_r": (19.8, 23.0, 7.5),
    "cfx_l": (-20.1, -1.8, 7.5), "cfx_r": (19.8, -1.8, 7.5), "master": (56.8, 98.0, 7.5), "mic": (-57.1, 47.8, 6.5),
    "hp_mix": (-57.1, -31.4, 6.5), "hp_level": (-57.1, -57.8, 6.5), "fx_depth": (56.8, -58.7, 7.5),
    "browse": (0.0, 122.2, 8.5)}
DJ_ORANGE_BTNS = [(-218.2, 109.2, 7.0), (-192.8, 109.2, 7.0), (-96.7, 109.2, 6.5)]     # IN, OUT, BEAT SYNC (left deck)
DJ_BLACK_BTNS = [(-167.7, 109.2, 5.0), (-141.9, 109.2, 4.2), (-120.9, 109.2, 4.2)]     # 4 BEAT, CALL < >
DJ_MIX_ORANGE = [(-57.1, -2.7, 6.0), (-57.1, -88.9, 6.0), (56.8, -88.9, 7.5)]           # SMART CFX, SMART FADER, ON/OFF
DJ_RECT_ORANGE = [(-20.1, -27.8, 13.0, 6.0), (19.8, -27.8, 13.0, 6.0), (56.8, 72.9, 13.0, 6.0)]   # channel and master CUE
DJ_RECT_BLACK = [(-32.5, 119.1, 15.0, 7.0), (32.2, 119.1, 15.0, 7.0), (49.4, -27.8, 9.0, 6.0), (64.2, -27.8, 9.0, 6.0),
                 (56.8, 23.0, 16.0, 7.0)]                                              # LOAD x2, BEAT < >, FX switch
DJ_MODE_Y = -64.7                                      # MEASURED: the four mode buttons over the pads
DJ_SHIFT = (-218.5, -49.0, 8.0)
DJ_METER = ((-4.7, 4.4), (65.9, 29.6))                 # MEASURED: the two LED columns' x and the y range (5 LEDs)
DJ_BRAND_TOP = (0.0, -99.5, 40.5, 4.6)                 # MEASURED: where the maker's name sits: x, y, width, cap height
DJ_BRAND_REAR = (157.0, 15.5, 79.0, 7.0)               # MEASURED rear-panel: x (unit frame), z, width, cap height
DJ_BRAND = "#bfbfc1"
DJ_PAD_GLOW = dict(rich=0.03, lite=0.03)                 # the pads' faint orange tint
DJ_LED_GLOW = dict(rich=0.9, lite=0.9)
STAND = dict(w=700.0, d=400.0, top=900.0, t=25.0, leg=25.0)   # plan v3 DJ_STAND (70 x 40, top at 90)
DJ_ON_STAND = (-50.0, 0.0)                             # plan v3: the controller's centre on the stand (stand frame)
LS_ON_STAND = (270.0, 0.0)                             # plan v3: the lightstick's cradle

# The lightstick: our own design (decision 2026-10-21: generic, never a real group's), 70 x 70 x 270 (plan v3)
LS_TINT = "#d9a0ff"                                    # plan v3 glow
LS_GLOW = dict(rich=3.0, lite=2.0)


# ---------------------------------------------------------------------------
# 2. materials
# ---------------------------------------------------------------------------
def mats(lite=False):
    from lib import materials as M
    sfx = "_lite" if lite else ""
    g = bpy.data.materials.get
    out = {}

    def P(name, **kw):
        n = f"mat_rd_{name}{sfx}"
        out[name] = g(n) or M.principled(n, **kw)
    P("silver", base="#d3d5d8", rough=0.32, metal=1.0)         # MacBook anodised aluminium
    P("stand", base="#cfd1d4", rough=0.38, metal=1.0)          # mStand, a touch more brushed
    P("hinge", base="#3b3c40", rough=0.35, metal=0.8)
    P("well", base="#060607", rough=0.7)
    P("trackpad", base="#bdbfc2", rough=0.38, metal=0.7)
    P("grille", base="#8d8f93", rough=0.55, metal=0.8)
    P("port", base="#08080a", rough=0.6)
    P("feet", base="#2a2a2c", rough=0.85)
    P("bezel", base="#050506", rough=0.06, spec=0.6)           # black glass
    P("silicone", base="#e4e6e8", rough=0.5)
    P("dj_body", base="#111113", rough=0.74)
    P("dj_mixer", base="#0c0c0e", rough=0.68)
    P("dj_rubber", base="#141415", rough=0.9)
    P("dj_jog", base="#121214", rough=0.5)
    P("dj_ring", base="#a3a4a7", rough=0.3, metal=0.9)
    P("dj_knob", base="#121213", rough=0.45)
    P("dj_line", base="#ececec", rough=0.5)
    P("dj_slot", base="#060607", rough=0.8)
    P("dj_cap", base="#1b1b1c", rough=0.4)
    P("dj_capline", base="#cfd0d2", rough=0.3, metal=0.8)
    P("stand_black", base="#1d1d1f", rough=0.48, metal=0.5)
    P("ls_white", base="#f3f1ed", rough=0.38)
    P("ls_grip", base="#e2dde8", rough=0.8)
    P("ls_pearl", base="#ece6f6", rough=0.28, metal=0.35)
    gl = (lambda d: d["lite" if lite else "rich"])
    for k, col, s in (("emit_orange", "#ff5c00", gl(DJ_LED_GLOW)), ("emit_green", "#55ff70", gl(DJ_LED_GLOW)),
                      ("emit_red", "#ff3a2a", gl(DJ_LED_GLOW)), ("emit_amber", "#ffb21a", gl(DJ_LED_GLOW))):
        n = f"mat_rd_{k}{sfx}"
        out[k] = g(n) or M.principled(n, base=col, rough=0.5, emit=col, emit_strength=s)
    n = f"mat_rd_dj_pad{sfx}"                                   # the pads: dark rubber, a faint orange tint
    out["dj_pad"] = g(n) or M.principled(n, base="#0b0b0b", rough=0.75, emit="#ff7a1a", emit_strength=gl(DJ_PAD_GLOW))
    n = f"mat_rd_dj_pad_glow{sfx}"                              # the lit frame around each pad
    out["dj_pad_glow"] = g(n) or M.principled(n, base="#ff5c00", rough=0.5, emit="#ff5c00", emit_strength=gl(DJ_LED_GLOW))
    n = f"mat_rd_lightstick_head{sfx}"                          # the glowing core: the site recolours this material
    out["ls_head"] = g(n) or M.principled(n, base=LS_TINT, rough=0.4, emit=LS_TINT, emit_strength=gl(LS_GLOW))
    n = f"mat_rd_lightstick_shell{sfx}"
    if g(n) is None:
        m = M.principled(n, base="#f6f0ff", rough=0.08)
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Alpha"].default_value = 0.22
        b.inputs["Transmission Weight"].default_value = 0.0 if lite else 0.6
        m.blend_method = "BLEND"
        m.show_transparent_back = False
        out["ls_shell"] = m
    else:
        out["ls_shell"] = g(n)
    out["screen"] = g(f"mat_rd_laptop_screen{sfx}") or screen_material(f"mat_rd_laptop_screen{sfx}", 256 if lite else 1024)
    out["grille"] = g(f"mat_rd_grille{sfx}") if lite else (grille_material(f"mat_rd_grille_dots") or out["grille"])
    return out


def screen_material(name, size):
    """A dark desktop for now: a deep blue-grey wallpaper with two soft light bands, a thin menu bar and a dock."""
    import numpy as np
    from lib import materials as M
    ar = LP_SCREEN[0] / LP_SCREEN[1]

    def fn(u, v):
        x, y = u * ar, v                                     # v = 1 at the top
        base = 0.035 + 0.03 * (1 - y)
        b1 = np.exp(-((y - 0.45 - 0.18 * np.sin(x * 2.2)) / 0.06) ** 2) * 0.10
        b2 = np.exp(-((y - 0.28 - 0.12 * np.cos(x * 1.7 + 1.0)) / 0.04) ** 2) * 0.06
        val = base + b1 + b2
        menu = (y > 0.975) * 0.05
        dock = ((y < 0.045) & (y > 0.012) & (np.abs(u - 0.5) < 0.2)) * 0.05
        r = val * 0.75 + menu + dock
        gch = val * 0.85 + menu + dock
        bl = val * 1.25 + menu + dock * 1.1
        return r, gch, bl, np.ones_like(u)
    im = WA._image_from(name + "_img", size, fn)
    m, nt, b = M._new(name)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.05
    return m


def grille_material(name):
    """The speaker grilles: fine dark perforations on the silver deck (rich only; the lite bake takes the average)."""
    from lib import materials as M
    m, nt, b = M._new(name)
    b.inputs["Metallic"].default_value = 0.8
    b.inputs["Roughness"].default_value = 0.45
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (700.0, 700.0, 700.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "F1"
    vo.inputs["Randomness"].default_value = 0.0
    nt.links.new(mp.outputs["Vector"], vo.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.44
    ramp.color_ramp.elements[0].color = M.rgba("#1a1a1c")
    ramp.color_ramp.elements[1].position = 0.48
    ramp.color_ramp.elements[1].color = M.rgba("#a4a6aa")
    nt.links.new(vo.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


# ---------------------------------------------------------------------------
# 3. mesh helpers (mm in, metres out)
# ---------------------------------------------------------------------------
V = WA.V


def rslab(bm, w, d, z0, z1, r, ft=0.0, fb=0.0, cx=0.0, cy=0.0, n=4, fn=3, mat=0):
    """A rounded-rectangle slab w x d (plan corner radius r) from z0 to z1 with a top fillet ft and a bottom fillet fb
    (mm). Returns the faces it made."""
    prof = []
    if fb > 0:
        for k in range(fn + 1):
            a = math.radians(90 * k / fn)
            prof.append((fb * (1 - math.sin(a)), z0 + fb * (1 - math.cos(a))))
    else:
        prof.append((0.0, z0))
    if ft > 0:
        for k in range(fn + 1):
            a = math.radians(90 * k / fn)
            prof.append((ft * (1 - math.cos(a)), z1 - ft + ft * math.sin(a)))
    else:
        prof.append((0.0, z1))
    rings = []
    for ins, z in prof:
        ol = WA.rrect2(w - 2 * ins, d - 2 * ins, max(r - ins, 0.3), n)
        rings.append([bm.verts.new(V(cx + x, cy + y, z)) for x, y in ol])
    faces = []
    m = len(rings[0])
    for i in range(len(rings) - 1):
        for j in range(m):
            faces.append(bm.faces.new((rings[i][j], rings[i][(j + 1) % m], rings[i + 1][(j + 1) % m], rings[i + 1][j])))
    faces.append(bm.faces.new(list(reversed(rings[0]))))
    faces.append(bm.faces.new(rings[-1]))
    for f in faces:
        f.material_index = mat
    return faces


def disc(bm, r, z0, z1, cx=0.0, cy=0.0, seg=24, ft=0.0, mat=0):
    """A round slab (a cylinder with an optional top fillet)."""
    prof = [(r, z0)]
    if ft > 0:
        for k in range(4):
            a = math.radians(90 * k / 3)
            prof.append((r - ft * (1 - math.cos(a)), z1 - ft + ft * math.sin(a)))
    else:
        prof.append((r, z1))
    rings = []
    for rr, z in prof:
        rings.append([bm.verts.new(V(cx + rr * math.cos(2 * math.pi * i / seg), cy + rr * math.sin(2 * math.pi * i / seg), z))
                      for i in range(seg)])
    fs = []
    for i in range(len(rings) - 1):
        for j in range(seg):
            fs.append(bm.faces.new((rings[i][j], rings[i][(j + 1) % seg], rings[i + 1][(j + 1) % seg], rings[i + 1][j])))
    fs.append(bm.faces.new(list(reversed(rings[0]))))
    fs.append(bm.faces.new(rings[-1]))
    for f in fs:
        f.material_index = mat
    return fs


def flat_rect(bm, x0, x1, y0, y1, z, mat=0, up=True):
    vs = [bm.verts.new(V(x, y, z)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    f = bm.faces.new(vs if up else list(reversed(vs)))
    f.material_index = mat
    return f


def mk(name, coll, parent, mats_list, build_fn, loc=(0, 0, 0), smooth=False, auto=None):
    """One object from a bmesh builder (mm, local to `loc` in mm); several material slots."""
    bm = bmesh.new()
    build_fn(bm)
    ob = WA.obj_from_bm(name, bm, None, coll, parent=parent, smooth=smooth, auto=auto)
    for m in mats_list:
        ob.data.materials.append(m)
    ob.location = (loc[0] * MM, loc[1] * MM, loc[2] * MM)
    return ob


def tri_count(obs):
    return WA.tri_count(obs)


# ---------------------------------------------------------------------------
# 4. keyboard legends (plain Python, Pillow)
# ---------------------------------------------------------------------------
def legend_cells(size):
    """Shelf-pack one cell per key at the largest whole px-per-mm that fits; {id: (x0, y0, x1, y1)}, ppm."""
    keys = laptop_keys()
    for ppm10 in range(int(size / 12 * 10), 5, -1):
        ppm = ppm10 / 10.0
        cells, x, y, rowh = {}, 0, 0, 0
        ok = True
        for kid, x0, x1, y0, y1, _ in keys:
            w, h = int(math.ceil((x1 - x0) * ppm)), int(math.ceil((y1 - y0) * ppm))
            if x + w > size:
                x, y, rowh = 0, y + rowh, 0
            if y + h > size:
                ok = False
                break
            cells[kid] = (x, y, x + w, y + h)
            x += w
            rowh = max(rowh, h)
        if ok:
            return cells, ppm
    raise ValueError("legend atlas too small")


def _icon(d, name, cx, cy, h, ink):
    """Small Mac key symbols as Pillow shapes (desktop.py's set plus the laptop's own)."""
    import desktop as DT
    lw = max(1, int(round(h * 0.11)))
    L = lambda pts: d.line(pts, fill=ink, width=lw, joint="curve")
    if name == "search":
        r = h * 0.28
        d.ellipse((cx - r - h * 0.08, cy - r - h * 0.08, cx + r - h * 0.08, cy + r - h * 0.08), outline=ink, width=lw)
        L([(cx + r * 0.55, cy + r * 0.55), (cx + h * 0.45, cy + h * 0.45)])
    elif name == "mic":
        d.rounded_rectangle((cx - h * 0.14, cy - h * 0.45, cx + h * 0.14, cy + h * 0.12), radius=h * 0.14, outline=ink, width=lw)
        d.arc((cx - h * 0.28, cy - h * 0.25, cx + h * 0.28, cy + h * 0.25), 0, 180, fill=ink, width=lw)
        L([(cx, cy + h * 0.25), (cx, cy + h * 0.45)])
    elif name == "moon":
        r = h * 0.4
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ink)
        d.ellipse((cx - r + h * 0.25, cy - r - h * 0.12, cx + r + h * 0.25, cy + r - h * 0.12), fill=LP_KEY_RGB)
    elif name == "globe":
        r = h * 0.42
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ink, width=lw)
        d.ellipse((cx - r * 0.45, cy - r, cx + r * 0.45, cy + r), outline=ink, width=lw)
        L([(cx - r, cy), (cx + r, cy)])
    elif name == "opt":
        w = h * 0.9
        L([(cx - w / 2, cy - h * 0.3), (cx - w * 0.15, cy - h * 0.3), (cx + w * 0.2, cy + h * 0.3), (cx + w / 2, cy + h * 0.3)])
        L([(cx + w * 0.1, cy - h * 0.3), (cx + w / 2, cy - h * 0.3)])
    elif name == "caps":
        DT._legend_icon(d, "shift", cx, cy - h * 0.12, h * 0.75, ink)
        d.rectangle((cx - h * 0.18, cy + h * 0.38, cx + h * 0.18, cy + h * 0.48), fill=ink)
    elif name == "larrow_s":
        w = h * 0.9
        pts = [(cx - w / 2, cy), (cx - w * 0.2, cy - h * 0.32), (cx + w / 2, cy - h * 0.32), (cx + w / 2, cy + h * 0.32),
               (cx - w * 0.2, cy + h * 0.32)]
        L(pts + [pts[0]])
        L([(cx - w * 0.02, cy - h * 0.13), (cx + w * 0.28, cy + h * 0.13)])
        L([(cx - w * 0.02, cy + h * 0.13), (cx + w * 0.28, cy - h * 0.13)])
    elif name.startswith("tri_"):
        a = h * 0.75
        pts = {"tri_up": [(cx - a, cy + a * 0.6), (cx + a, cy + a * 0.6), (cx, cy - a * 0.8)],
               "tri_down": [(cx - a, cy - a * 0.6), (cx + a, cy - a * 0.6), (cx, cy + a * 0.8)],
               "tri_left": [(cx + a * 0.6, cy - a), (cx + a * 0.6, cy + a), (cx - a * 0.8, cy)],
               "tri_right": [(cx - a * 0.6, cy - a), (cx - a * 0.6, cy + a), (cx + a * 0.8, cy)]}[name]
        d.polygon(pts, fill=ink)
    else:
        DT._legend_icon(d, name, cx, cy, h, ink)


def make_legends(size, path):
    """Plain Python: the laptop's legend atlas (white legends on the black caps); a key's footprint maps onto its cell."""
    import re
    from PIL import Image, ImageDraw, ImageFont
    cells, ppm = legend_cells(size)
    fpath = os.path.join(FONTS, "Montserrat-SemiBold.ttf")
    CAPH = 0.70
    im = Image.new("RGB", (size, size), LP_KEY_RGB)
    d = ImageDraw.Draw(im)
    fonts = {}

    def font(ch):
        px = max(4, int(round(ch / CAPH)))
        if px not in fonts:
            fonts[px] = ImageFont.truetype(fpath, px)
        return fonts[px]

    def line(text, cx, cy, ch, maxw):
        f = font(ch)
        segs, w = [], 0.0
        for tok in re.split(r"(\[\w+\])", text):
            if not tok:
                continue
            if tok.startswith("["):
                segs.append(("icon", tok[1:-1], ch * 1.5))
                w += ch * 1.5
            else:
                b = d.textbbox((0, 0), tok, font=f)
                segs.append(("text", tok, b))
                w += b[2] - b[0] + (ch * 0.3 if len(segs) > 1 else 0)
        if w > maxw:
            return line(text, cx, cy, ch * maxw / w, maxw)
        x = cx - w / 2
        for kind, val, b in segs:
            if kind == "icon":
                _icon(d, val, x + b / 2, cy, ch * 1.25, LP_LEGEND_INK)
                x += b
            else:
                if x > cx - w / 2 + 0.1:
                    x += ch * 0.3
                d.text((x - b[0], cy - (b[1] + b[3]) / 2), val, font=f, fill=LP_LEGEND_INK)
                x += b[2] - b[0]
    leg = {k[0]: k[5] for k in laptop_keys()}
    for kid, (x0, y0, x1, y1) in cells.items():
        spec = leg.get(kid, "")
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        w, h = x1 - x0, y1 - y0
        if kid == "touchid":                       # the Touch ID ring
            r = h * 0.36
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline="#3a3a3e", width=max(1, int(h * 0.05)))
        elif isinstance(spec, tuple):
            top, bot = spec
            small = kid.startswith("f") and kid[1:].isdigit()
            ch = h * (0.12 if small else 0.17)
            line(top, cx, cy - h * 0.17, ch, w * 0.8)
            line(bot, cx, cy + h * (0.25 if small else 0.15), ch * (1.0 if small else 1.0), w * 0.8)
        elif spec:
            single = len(spec) == 1
            ch = h * (0.21 if single else 0.15)
            line(spec, cx, cy if single else cy + h * 0.2, ch, w * 0.8)
    im.save(path, optimize=True)
    print("LEGENDS", path, size, ppm)


def apply_legends(ob, lite):
    """Blender: the legend atlas on the keys mesh; each key's footprint UV-mapped onto its cell (5% inset)."""
    import subprocess
    from lib import materials as M
    size = 512 if lite else 2048
    path = os.path.join(BLENDER_DIR, "out", "components", f"returndesk_legends-{'lite' if lite else 'rich'}.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(["/opt/anaconda3/bin/python3", os.path.abspath(__file__), "--legends", str(size), path], check=True)
    cells, ppm = legend_cells(size)
    name = "mat_rd_laptop_legend" + ("_lite" if lite else "")
    m, nt, b = M._new(name)
    for im in [i for i in bpy.data.images if i.filepath == path]:
        bpy.data.images.remove(im)
    im = bpy.data.images.load(path)
    im.name = os.path.basename(path)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.72
    b.inputs["Specular IOR Level"].default_value = 0.25
    ob.data.materials.clear()
    ob.data.materials.append(m)
    me = ob.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    keys = {k[0]: k for k in laptop_keys()}
    # each key's faces carry its index in an int attribute written by build_laptop
    att = me.attributes.get("key_index")
    ids = list(keys.keys())
    for poly in me.polygons:
        kid = ids[att.data[poly.index].value]
        _, kx0, kx1, ky0, ky1, _ = keys[kid]
        x0, y0, x1, y1 = cells[kid]
        cx, cy, cw, chh = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * 0.95, (y1 - y0) * 0.95
        mx, my = (kx0 + kx1) / 2, (ky0 + ky1) / 2
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            u = (cx + (co.x / MM - mx) / (kx1 - kx0) * cw) / size
            v = 1.0 - (cy - (co.y / MM - my) / (ky1 - ky0) * chh) / size
            uv.data[li].uv = (u, v)
    return m


# ---------------------------------------------------------------------------
# 5. the parts
# ---------------------------------------------------------------------------
def mstand_path():
    """The mStand's centreline in (y, z) mm, front plate end to base front end, with the two bends filleted, and the
    width factor per point (the upright's waist)."""
    s = math.radians(MS_SLOPE)
    A = (MS_FRONT_Y, MS_FRONT_Z)
    C1 = (MS_BEND[0], MS_FRONT_Z + (MS_BEND[0] - MS_FRONT_Y) * math.tan(s))
    C2 = (MS_BEND[1], MS_T / 2)
    E = (MS_BASE_FRONT, MS_T / 2)

    def lerp(p, q, t):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

    def dist(p, q):
        return math.hypot(q[0] - p[0], q[1] - p[1])
    pts = []
    d1, d2 = 30.0, 24.0
    a1, b1 = lerp(C1, A, d1 / dist(A, C1)), lerp(C1, C2, d1 / dist(C1, C2))
    a2, b2 = lerp(C2, C1, d2 / dist(C1, C2)), lerp(C2, E, d2 / dist(C2, E))
    for t in range(0, 9):
        pts.append((lerp(A, a1, t / 8), "plate"))
    for t in range(1, 10):
        u = t / 10
        p = lerp(lerp(a1, C1, u), lerp(C1, b1, u), u)
        pts.append((p, "bend1"))
    for t in range(0, 7):
        pts.append((lerp(b1, a2, t / 6), "upright"))
    for t in range(1, 9):
        u = t / 9
        pts.append((lerp(lerp(a2, C2, u), lerp(C2, b2, u), u), "bend2"))
    for t in range(0, 7):
        pts.append((lerp(b2, E, t / 6), "base"))
    # the waist: 1 on the plates, MS_WAIST at the upright's middle (smooth)
    up = [i for i, (_, k) in enumerate(pts) if k in ("bend1", "upright", "bend2")]
    i0, i1 = up[0] - 2, up[-1] + 2
    out = []
    for i, (p, k) in enumerate(pts):
        f = 1.0
        if i0 <= i <= i1:
            t = (i - i0) / (i1 - i0)
            f = 1.0 - (1.0 - MS_WAIST) * math.sin(math.pi * t) ** 1.5
        out.append((p, f))
    return out, C1


def plate_frame():
    """The top plate's top surface: a point at the front end and its along-slope direction and normal (y, z)."""
    s = math.radians(MS_SLOPE)
    t = (math.cos(s), math.sin(s))
    n = (-math.sin(s), math.cos(s))
    p = (MS_FRONT_Y + n[0] * MS_T / 2, MS_FRONT_Z + n[1] * MS_T / 2)
    return p, t, n


def mstand_plate_pose():
    """The laptop root's pose on the plate (in the mStand frame): the base's front edge 5 mm behind the lip, resting on
    the pads."""
    p, t, n = plate_frame()
    s = 6.0 + MS_LIP[3] + LP_D / 2
    off = MS_PAD[1] + 1.0                                   # the laptop's feet (1.0 below its base) on the pads
    y = p[0] + t[0] * s + n[0] * off
    z = p[1] + t[1] * s + n[1] * off
    return Matrix.Translation((0, y * MM, z * MM)) @ Matrix.Rotation(math.radians(MS_SLOPE), 4, "X")


def build_mstand(coll, mp, root, lite, rough):
    sfx = "_lite" if lite else ""
    names = []
    path, C1 = mstand_path()
    if rough:
        path = path[::2] + [path[-1]]
    ch = 1.6 if not lite else 0.0
    T = MS_T
    if ch > 0:
        sec = [(-1, -T / 2 + ch, 0), (-1, T / 2 - ch, 0), (-1, T / 2, ch), (1, T / 2, ch), (1, T / 2 - ch, 0), (1, -T / 2 + ch, 0),
               (1, -T / 2, ch), (-1, -T / 2, ch)]
    else:
        sec = [(-1, -T / 2, 0), (-1, T / 2, 0), (1, T / 2, 0), (1, -T / 2, 0)]

    def body(bm):
        rings = []
        n = len(path)
        for i, ((y, z), f) in enumerate(path):
            pa = path[max(i - 1, 0)][0]
            pb = path[min(i + 1, n - 1)][0]
            ty, tz = pb[0] - pa[0], pb[1] - pa[1]
            L = math.hypot(ty, tz)
            ny, nz = -tz / L, ty / L            # the section's "up" (outer side of the C at the plate's top)
            hw = MS_W / 2 * f
            ring = []
            for sx, sn, inset in sec:
                x = sx * (hw - inset)
                ring.append(bm.verts.new(V(x, y + ny * sn, z + nz * sn)))
            rings.append(ring)
        m = len(sec)
        for i in range(n - 1):
            for j in range(m):
                bm.faces.new((rings[i][j], rings[i][(j + 1) % m], rings[i + 1][(j + 1) % m], rings[i + 1][j]))
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
        WA.fix_normals(bm)
    ob = mk("mstand" + sfx, coll, root, [mp["stand"]], body, smooth=not lite, auto=40)
    names.append(ob.name)
    if rough:
        return names
    # the round hole in the upright (a cylinder along Y through the upright's middle)
    up_y = (MS_BEND[0] + MS_BEND[1]) / 2
    up_z = (C1[1] + MS_T) / 2 + 4
    seg = 24 if lite else 64

    def cutter_hole(bm):
        rings = []
        for yy in (up_y - 30, up_y + 30):
            rings.append([bm.verts.new(V(MS_HOLE / 2 * math.cos(2 * math.pi * i / seg), yy, up_z + MS_HOLE / 2 * math.sin(2 * math.pi * i / seg)))
                          for i in range(seg)])
        for j in range(seg):
            bm.faces.new((rings[0][j], rings[0][(j + 1) % seg], rings[1][(j + 1) % seg], rings[1][j]))
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[1])
        WA.fix_normals(bm)
    cut = mk("mstand_cut_hole" + sfx, coll, root, [], cutter_hole)
    WA.boolean_cut(ob, cut)
    # the teardrop through the plate, 30 mm in front of the rear bend, its point toward the front
    p, t, n = plate_frame()
    s_drop = (MS_BEND[0] - MS_FRONT_Y) / math.cos(math.radians(MS_SLOPE)) - 52.0
    cy, cz = p[0] + t[0] * s_drop, p[1] + t[1] * s_drop
    r = MS_DROP / 2
    outline = [(r * math.cos(a), r * math.sin(a)) for a in [math.radians(-60 + 300 * k / 20) for k in range(21)]]
    outline.append((0.0, -r * 1.9))

    def cutter_drop(bm):
        bot, top = [], []
        for x, a in outline:
            yy, zz = cy + t[0] * a, cz + t[1] * a
            bot.append(bm.verts.new(V(x, yy - n[0] * 20, zz - n[1] * 20)))
            top.append(bm.verts.new(V(x, yy + n[0] * 6, zz + n[1] * 6)))
        k = len(outline)
        for j in range(k):
            bm.faces.new((bot[j], bot[(j + 1) % k], top[(j + 1) % k], top[j]))
        bm.faces.new(list(reversed(bot)))
        bm.faces.new(top)
        WA.fix_normals(bm)
    cut = mk("mstand_cut_drop" + sfx, coll, root, [], cutter_drop)
    WA.boolean_cut(ob, cut)

    # the front lip: two tabs across the plate's front end, standing up from the plate
    def lip(bm):
        w, gap, h, th = MS_LIP
        for sx in (-1, 1):
            x0 = sx * gap / 2
            x1 = sx * (gap / 2 + w)
            xa, xb = min(x0, x1), max(x0, x1)
            base = (p[0] + t[0] * 1.0, p[1] + t[1] * 1.0)
            corners = []
            for a, b2 in ((0, -1.5), (th, -1.5), (th, h), (0, h)):
                corners.append((base[0] + t[0] * a + n[0] * b2, base[1] + t[1] * a + n[1] * b2))
            vs = [[bm.verts.new(V(xx, yy, zz)) for yy, zz in corners] for xx in (xa, xb)]
            for j in range(4):
                bm.faces.new((vs[0][j], vs[0][(j + 1) % 4], vs[1][(j + 1) % 4], vs[1][j]))
            bm.faces.new(vs[0])
            bm.faces.new(list(reversed(vs[1])))
        WA.fix_normals(bm)
    names.append(mk("mstand_lip" + sfx, coll, root, [mp["stand"]], lip).name)

    # the 8 clear silicone pads: two columns of four along the slope
    def pads(bm):
        L = (MS_BEND[0] - MS_FRONT_Y) / math.cos(math.radians(MS_SLOPE))
        for x in (-100.0, 100.0):
            for s_ in (22.0, 0.36 * L, 0.62 * L, L - 40.0):
                py, pz = p[0] + t[0] * s_, p[1] + t[1] * s_
                fs = disc(bm, MS_PAD[0], 0.0, MS_PAD[1], seg=6 if lite else 20, ft=0.0)
                vs = {v for f in fs for v in f.verts}
                for v in vs:
                    lx, ly, lz = v.co.x / MM, v.co.y / MM, v.co.z / MM
                    v.co = V(x + lx, py + t[0] * ly + n[0] * lz, pz + t[1] * ly + n[1] * lz)
        WA.fix_normals(bm)
    names.append(mk("mstand_pads" + sfx, coll, root, [mp["silicone"]], pads).name)

    def feet(bm):
        for x in (-95.0, 95.0):
            for y in (MS_BASE_FRONT + 14, MS_BEND[1] - 10):
                disc(bm, 7.0, 0.0, 0.3, cx=x, cy=y, seg=6 if lite else 16)     # flush: the stand rests on z 0
        WA.fix_normals(bm)
    names.append(mk("mstand_feet" + sfx, coll, root, [mp["feet"]], feet).name)
    return names


def build_laptop_only(coll, mp, root, lite, rough):
    """The MacBook Pro 16 in its base frame (origin at the base's bottom centre, front at -Y)."""
    sfx = "_lite" if lite else ""
    names = []
    hy, hz = LP_HINGE
    n_corner = 3 if lite else 6

    def base(bm):
        rslab(bm, LP_W, LP_D, 0.0, LP_BASE_H, LP_R, ft=0.0 if rough else 1.0, fb=0.0 if rough else 2.6, n=n_corner,
              fn=1 if lite else 3)
    ob = mk("laptop_base" + sfx, coll, root, [mp["silver"]], base, smooth=not lite, auto=35)
    names.append(ob.name)
    hinge = WA.empty("laptop_hinge" + sfx, coll, parent=root, loc=(0, hy * MM, hz * MM))
    hinge.rotation_euler = (math.radians(-LP_OPEN), 0, 0)
    lid_y = -(hy + LP_D / 2) + (LP_D - LP_LID_D) / 2 + 0.5   # the lid's centre (hinge frame, closed pose)
    lid_cy = -LP_LID_D / 2 - (hy - (LP_D / 2 - LP_LID_D)) + 0.0
    lid_cy = (LP_D / 2 - 2.0) - hy - LP_LID_D / 2                # rear edge 2 mm in front of the base's rear

    def lid(bm):
        rslab(bm, LP_W, LP_LID_D, LP_BASE_H - hz + 0.15, LP_H - hz, LP_R, ft=0.0 if rough else 1.2,
              fb=0.0 if rough else 0.5, cy=lid_cy, n=n_corner, fn=1 if lite else 3)
    names.append(mk("laptop_lid" + sfx, coll, hinge, [mp["silver"]], lid, smooth=not lite, auto=35).name)
    if rough:
        return names
    zf = LP_BASE_H - hz + 0.15 - 0.05                       # the lid's inner face (hinge frame), facing -Z when closed
    g0 = LP_GLASS_INSET
    top_edge = lid_cy - LP_LID_D / 2 + g0                   # the glass's far edge (the screen's top when open)

    def glass(bm):
        ol = WA.rrect2(LP_W - 2 * g0, LP_LID_D - 2 * g0, LP_R - g0, n_corner)
        vs = [bm.verts.new(V(x, lid_cy + y, zf)) for x, y in ol]
        bm.faces.new(list(reversed(vs)))                     # normal -Z
    names.append(mk("laptop_bezel" + sfx, coll, hinge, [mp["bezel"]], glass).name)
    sw, sh = LP_SCREEN
    s_top = top_edge + LP_BEZEL_TOP
    s_bot = s_top + sh

    def screen(bm):
        flat_rect(bm, -sw / 2, sw / 2, s_top, s_bot, zf - 0.05, up=False)
    so = mk("laptop_screen" + sfx, coll, hinge, [mp["screen"]], screen)
    me = so.data
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.x / MM + sw / 2) / sw, (s_bot - co.y / MM) / sh)
    names.append(so.name)

    def notch(bm):
        nw, nh = LP_NOTCH
        ol = WA.rrect2(nw, nh, 2.0, 2)
        vs = [bm.verts.new(V(x, top_edge + nh / 2 + y, zf - 0.1)) for x, y in ol]
        bm.faces.new(list(reversed(vs)))
    names.append(mk("laptop_notch" + sfx, coll, hinge, [mp["bezel"]], notch).name)
    mark = None
    try:
        from lib import brands
        lid_ob = bpy.data.objects["laptop_lid" + sfx]
        bpy.context.view_layer.update()
        mark = brands.decal("laptop", at=(0.0, lid_cy * MM, (LP_H - hz) * MM), normal=(0, 0, 1), up=(0, 1, 0),
                            height=LP_MARK * MM, finish="polished", colour="#eceef0", parent=lid_ob, lite=lite,
                            name="laptop_brand")
    except Exception as e:
        print("laptop mark:", e)
    if mark is not None:
        names.append(mark.name)

    # the deck: the black well, the keys, the trackpad, the grilles, the hinge cover, the thumb notch, ports, feet
    x0, x1, y0, y1 = LP_WELL

    def well_cut(bm):
        rslab(bm, x1 - x0, y1 - y0, LP_KEY_FLOOR, LP_BASE_H + 2.0, 2.5, cx=(x0 + x1) / 2, cy=(y0 + y1) / 2, n=2, fn=1)
    WA.boolean_cut(ob, mk("laptop_cut_well" + sfx, coll, root, [], well_cut))

    def well(bm):
        rslab(bm, x1 - x0, y1 - y0, LP_KEY_FLOOR - 0.3, LP_KEY_FLOOR + 0.02, 2.5, cx=(x0 + x1) / 2, cy=(y0 + y1) / 2, n=2, fn=1)
    names.append(mk("laptop_well" + sfx, coll, root, [mp["well"]], well).name)
    keys = laptop_keys()

    def keyfaces(bm):
        lay = bm.faces.layers.int.new("key_index")
        for i, (kid, kx0, kx1, ky0, ky1, _) in enumerate(keys):
            if lite:                     # a plain box: 12 triangles a key
                before = set(bm.faces)
                WA.box_bm(bm, kx1 - kx0, ky1 - ky0, LP_KEY_TOP - LP_KEY_FLOOR, at=((kx0 + kx1) / 2, (ky0 + ky1) / 2, 0),
                          z0=LP_KEY_FLOOR)
                fs = [f for f in bm.faces if f not in before]
            else:
                fs = rslab(bm, kx1 - kx0, ky1 - ky0, LP_KEY_FLOOR, LP_KEY_TOP, 1.6, ft=0.5,
                           cx=(kx0 + kx1) / 2, cy=(ky0 + ky1) / 2, n=2, fn=1)
            for f in fs:
                f[lay] = i
    ko = mk("laptop_keys" + sfx, coll, root, [mp["well"]], keyfaces)
    apply_legends(ko, lite)
    names.append(ko.name)
    px0, px1, py0, py1 = LP_PAD

    def pad(bm):
        rslab(bm, px1 - px0, py1 - py0, LP_BASE_H - 0.3, LP_BASE_H + 0.06, 4.5, cx=(px0 + px1) / 2, cy=(py0 + py1) / 2,
              n=2 if lite else 4, fn=1)
    names.append(mk("laptop_trackpad" + sfx, coll, root, [mp["trackpad"]], pad).name)
    gx0, gx1, gy0, gy1 = LP_GRILLE

    def grilles(bm):
        for sx in (-1, 1):
            flat_rect(bm, min(sx * gx0, sx * gx1), max(sx * gx0, sx * gx1), gy0, gy1, LP_BASE_H + 0.04)
    names.append(mk("laptop_grilles" + sfx, coll, root, [mp["grille"]], grilles).name)

    def hinge_cover(bm):           # the dark hinge barrel between the base's rear and the lid
        seg = 8 if lite else 20
        r = 4.6
        rings = []
        for x in (-LP_W / 2 + 42, LP_W / 2 - 42):
            rings.append([bm.verts.new(V(x, hy + r * math.cos(2 * math.pi * i / seg), hz + r * math.sin(2 * math.pi * i / seg)))
                          for i in range(seg)])
        for j in range(seg):
            bm.faces.new((rings[0][j], rings[0][(j + 1) % seg], rings[1][(j + 1) % seg], rings[1][j]))
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[1])))
        WA.fix_normals(bm)
    names.append(mk("laptop_hinge_cover" + sfx, coll, root, [mp["hinge"]], hinge_cover, smooth=not lite).name)

    def notch_cut(bm):            # the thumb notch at the base's front edge (a shallow scoop)
        rslab(bm, LP_NOTCH_FRONT, 14.0, LP_BASE_H - 1.6, LP_BASE_H + 2.0, 5.0, cy=-LP_D / 2, n=3, fn=1)
    cut = mk("laptop_cut_notch" + sfx, coll, root, [], notch_cut)
    WA.boolean_cut(ob, cut)

    def ports(bm):                 # flat dark port faces on both sides (MagSafe, 2 TB, jack | HDMI, TB, SDXC)
        L = [(-1, -60, 16, 3.0), (-1, -30, 9, 3.0), (-1, -15, 9, 3.0), (-1, 60, 4.5, 4.5),
             (1, -62, 14, 4.0), (1, -40, 9, 3.0), (1, 50, 25, 2.0)]
        for sx, y, w, h in L:
            x = sx * (LP_W / 2 + 0.05)
            vs = [bm.verts.new(V(x, y + a, 5.6 + b)) for a, b in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
            bm.faces.new(vs if sx > 0 else list(reversed(vs)))
        WA.fix_normals(bm)
    names.append(mk("laptop_ports" + sfx, coll, root, [mp["port"]], ports).name)

    def feet(bm):
        for sx in (-1, 1):
            for y in (-LP_D / 2 + 24, LP_D / 2 - 24):
                disc(bm, 7.5, -1.0, 0.3, cx=sx * (LP_W / 2 - 26), cy=y, seg=6 if lite else 20)
        WA.fix_normals(bm)
    names.append(mk("laptop_feet" + sfx, coll, root, [mp["feet"]], feet).name)
    return names


def build_laptop(coll, mp, lite=False, rough=False, sfx=""):
    """The mStand with the MacBook on its plate."""
    sroot = WA.empty("mstand_root" + sfx, coll)
    ms = build_mstand(coll, mp, sroot, lite, rough)
    lroot = WA.empty("laptop_root" + sfx, coll, parent=sroot)
    lroot.matrix_parent_inverse = Matrix.Identity(4)
    lroot.matrix_basis = mstand_plate_pose()
    lp = build_laptop_only(coll, mp, lroot, lite, rough)
    return {"all": ms + lp, "roots": [sroot.name, lroot.name, "laptop_hinge" + sfx], "mstand": ms, "laptop": lp}


def build_stand(coll, mp, root, lite, rough):
    S = STAND
    sfx = "_lite" if lite else ""

    def stand(bm):
        rslab(bm, S["w"], S["d"], S["top"] - S["t"], S["top"], 4.0, ft=0 if lite else 1.5, n=2, fn=1)
        lg = S["leg"]
        for sx in (-1, 1):
            for sy in (-1, 1):
                rslab(bm, lg, lg, 0.0, S["top"] - S["t"], 3.0, cx=sx * (S["w"] / 2 - 20 - lg / 2),
                      cy=sy * (S["d"] / 2 - 20 - lg / 2), n=1, fn=1)
            WA.box_bm(bm, 20.0, S["d"] - 40 - 2 * lg, 20.0, at=(sx * (S["w"] / 2 - 20 - lg / 2), 0, 150.0))
        WA.box_bm(bm, S["w"] - 40 - 2 * lg, 20.0, 20.0, at=(0, S["d"] / 2 - 20 - lg / 2, 150.0))
        WA.fix_normals(bm)
    return [mk("dj_stand" + sfx, coll, root, [mp["stand_black"]], stand).name]


def build_dj(coll, mp, lite=False, rough=False, sfx=""):
    """The controller on its stand; dj_root at the controller's bottom centre on the stand's top."""
    sroot = WA.empty("dj_stand_root" + sfx, coll)
    stand = build_stand(coll, mp, sroot, lite, rough)
    root = WA.empty("dj_root" + sfx, coll, parent=sroot, loc=(DJ_ON_STAND[0] * MM, DJ_ON_STAND[1] * MM, STAND["top"] * MM))
    names = []
    T = DJ_TOP
    seg_jog = 32 if lite else 160

    def body(bm):
        rslab(bm, DJ_W, DJ_D, DJ_FEET, T, DJ_R, ft=0.0 if rough else 3.5, fb=0.0 if rough else 6.0, n=2 if lite else 5,
              fn=1 if lite else 3)
    names.append(mk("dj_body" + sfx, coll, root, [mp["dj_body"]], body, smooth=not lite, auto=40).name)

    def jog_shape(bm, rough_=False):
        R, Rp = DJ_JOG[2], DJ_JOG[3]
        h1, h2 = DJ_JOG_H
        bumps = 22
        prof = [(R - 1.0, 0.0, 0), (R, 1.2, 0), (R - 0.4, h1 * 0.55, 0), (R - 3.5, h1, 0), (Rp + 1.0, h1, 0),
                (Rp, h1 + 0.5, 0), (Rp, h2 - 0.8, 0), (Rp - 0.8, h2, 0), (24.0, h2, 0), (24.0, h2 + 0.15, 1),
                (17.0, h2 + 0.15, 1), (17.0, h2, 0), (0.0, h2 - 0.3, 0)]
        if rough_:
            prof = [(R, 0, 0), (R, h1, 0), (Rp, h1, 0), (Rp, h2, 0), (0.0, h2, 0)]
        elif lite:
            prof = [(R, 0.0, 0), (R - 0.4, h1 * 0.55, 0), (R - 3.5, h1, 0), (Rp, h1 + 0.5, 0), (Rp - 0.8, h2, 0),
                    (24.0, h2 + 0.15, 1), (17.0, h2 + 0.15, 1), (0.0, h2 - 0.3, 0)]
        rings = []
        for k, (r, z, _) in enumerate(prof):
            ring = []
            for i in range(seg_jog):
                a = 2 * math.pi * i / seg_jog
                rr = r
                if 1 <= k <= 3 and not rough_:     # the finger dimples around the ring's outer face
                    rr = r - (1.8 if k == 2 else 0.9) * max(0.0, math.cos(bumps * a)) ** 2
                ring.append(bm.verts.new(V(rr * math.cos(a), rr * math.sin(a), z)))
            rings.append(ring)
        for k in range(len(rings) - 1):
            for i in range(seg_jog):
                f = bm.faces.new((rings[k][i], rings[k][(i + 1) % seg_jog], rings[k + 1][(i + 1) % seg_jog], rings[k + 1][i]))
                f.material_index = prof[k][2] if prof[k][2] == prof[k + 1][2] else 0
        c = bm.verts.new(V(0, 0, prof[-1][1]))
        for i in range(seg_jog):
            bm.faces.new((rings[-1][i], rings[-1][(i + 1) % seg_jog], c))
        bm.faces.new(list(reversed(rings[0])))
        WA.fix_normals(bm)
    for side, sx in (("l", -1), ("r", 1)):
        names.append(mk(f"dj_jog_{side}{sfx}", coll, root, [mp["dj_jog"], mp["dj_ring"]], lambda bm: jog_shape(bm, rough),
                        loc=(sx * DJ_JOG[0], DJ_JOG[1], T), smooth=not lite, auto=50).name)
    if rough:
        return {"all": names, "roots": [sroot.name, root.name], "dj": names, "dj_stand": stand}

    def mixer(bm):
        rslab(bm, 2 * DJ_MIX_X - 1.0, DJ_D - 2.5, T - 0.5, T + 0.35, 1.0, n=1, fn=1)
    names.append(mk("dj_mixer" + sfx, coll, root, [mp["dj_mixer"]], mixer).name)

    def feet(bm):
        for sx in (-1, 1):
            for sy in (-1, 1):
                disc(bm, 5.0, 0.0, DJ_FEET + 0.2, cx=sx * (DJ_W / 2 - 14), cy=sy * (DJ_D / 2 - 14), seg=8 if lite else 16)
        WA.fix_normals(bm)
    names.append(mk("dj_feet" + sfx, coll, root, [mp["dj_rubber"]], feet).name)

    # pads: 01..04 the back row left to right, 05..08 the front row
    frames = []
    for side, dx in (("l", 0.0), ("r", DJ_DECK_DX)):
        i = 0
        for y in DJ_PAD_Y:
            for x in DJ_PAD_X:
                i += 1
                nm = f"dj_pad_{side}_{i:02d}{sfx}"
                names.append(mk(nm, coll, root, [mp["dj_pad"]],
                                lambda bm: rslab(bm, DJ_PAD - 1.6, DJ_PAD - 1.6, -1.0, 3.2, 1.6, ft=0.0 if lite else 0.8,
                                                 n=1 if lite else 2, fn=1),
                                loc=(x + dx, y, T)).name)
                frames.append((x + dx, y))

    def pad_frames(bm):
        for x, y in frames:
            o, i_ = DJ_PAD + 1.2, DJ_PAD - 1.4
            for (a0, a1, b0, b1) in ((-o / 2, o / 2, i_ / 2, o / 2), (-o / 2, o / 2, -o / 2, -i_ / 2),
                                     (-o / 2, -i_ / 2, -i_ / 2, i_ / 2), (i_ / 2, o / 2, -i_ / 2, i_ / 2)):
                flat_rect(bm, x + a0, x + a1, y + b0, y + b1, T + 0.4)
    names.append(mk("dj_pad_frames" + sfx, coll, root, [mp["dj_pad_glow"]], pad_frames).name)

    seg_b = 8 if lite else 32
    for side, dx in (("l", 0.0), ("r", DJ_DECK_DX)):
        for kind, y, emit in (("cue", DJ_CUE[1], "emit_orange"), ("play", DJ_PLAY_Y, "emit_green")):
            def btn(bm):
                disc(bm, DJ_CUE[2] + 0.6, -0.5, 0.8, seg=seg_b, mat=1)
                disc(bm, DJ_CUE[2] - 0.8, 0.6, 4.2, seg=seg_b, ft=0.0 if lite else 1.0, mat=0)
                WA.fix_normals(bm)
            names.append(mk(f"dj_{kind}_{side}{sfx}", coll, root, [mp["dj_knob"], mp[emit]], btn,
                            loc=(DJ_CUE[0] + dx, y, T), smooth=not lite, auto=40).name)

    def cap(w, d, h, line_axis="x"):
        def f(bm):
            rslab(bm, w, d, 0.0, h, 1.5, ft=0.0 if lite else 1.0, n=1 if lite else 2, fn=1, mat=0)
            if line_axis == "x":
                flat_rect(bm, -w / 2 + 0.6, w / 2 - 0.6, -0.5, 0.5, h + 0.05, mat=1)
            else:
                flat_rect(bm, -0.5, 0.5, -d / 2 + 0.6, d / 2 - 0.6, h + 0.05, mat=1)
            WA.fix_normals(bm)
        return f
    slots = []
    for side, dx in (("l", 0.0), ("r", DJ_DECK_DX)):
        x = DJ_TEMPO[0] + dx
        names.append(mk(f"dj_tempo_{side}{sfx}", coll, root, [mp["dj_cap"], mp["dj_capline"]], cap(17.0, 12.0, 14.0),
                        loc=(x, DJ_TEMPO[3], T)).name)
        slots.append((x - 1.4, x + 1.4, DJ_TEMPO[2], DJ_TEMPO[1]))
    for side, sx in (("l", -1), ("r", 1)):
        x = sx * DJ_CH[0]
        names.append(mk(f"dj_fader_{side}{sfx}", coll, root, [mp["dj_cap"], mp["dj_capline"]], cap(20.0, 12.0, 18.0),
                        loc=(x, DJ_CH[3], T)).name)
        slots.append((x - 1.4, x + 1.4, DJ_CH[2], DJ_CH[1]))
    names.append(mk(f"dj_xfader{sfx}", coll, root, [mp["dj_cap"], mp["dj_capline"]], cap(10.0, 15.0, 13.0, "y"),
                    loc=(0.0, DJ_XF[1], T)).name)
    slots.append((-DJ_XF[0] - 6, DJ_XF[0] + 6, DJ_XF[1] - 1.4, DJ_XF[1] + 1.4))

    def slot_faces(bm):
        for a, b, c, d in slots:
            flat_rect(bm, a, b, c, d, T + 0.4)
        # the fader scales: short tick lines beside each slot
        for a, b, c, d in slots[:4]:
            n_ = 9
            for k in range(n_):
                y = c + (d - c) * k / (n_ - 1)
                for s_ in (-1, 1):
                    xm = (a + b) / 2 + s_ * 8.5
                    flat_rect(bm, xm - 3.0, xm + 3.0, y - 0.25, y + 0.25, T + 0.41, mat=1)
    names.append(mk("dj_slots" + sfx, coll, root, [mp["dj_slot"], mp["dj_line"]], slot_faces).name)

    seg_k = 10 if lite else 28
    for kn, (x, y, r) in DJ_KNOBS.items():
        def knob(bm, r=r):
            prof = [(r + 1.6, 0.0), (r + 1.6, 1.4), (r, 1.8), (r, 12.0), (r - 0.6, 19.5), (r - 1.6, 20.0), (0.0, 20.0)]
            if lite:
                prof = [(r + 1.4, 0.0), (r + 1.4, 1.4), (r, 1.8), (r - 0.6, 19.5), (0.0, 20.0)]
            rings = []
            for rr, z in prof:
                rings.append([bm.verts.new(V(rr * math.cos(2 * math.pi * i / seg_k), rr * math.sin(2 * math.pi * i / seg_k), z))
                              for i in range(seg_k)])
            for k in range(len(rings) - 1):
                for i in range(seg_k):
                    bm.faces.new((rings[k][i], rings[k][(i + 1) % seg_k], rings[k + 1][(i + 1) % seg_k], rings[k + 1][i]))
            bm.faces.new(list(reversed(rings[0])))
            for f in list(bm.faces):
                pass
            c = rings[-1][0]
            # the white indicator line on top, pointing to 12 o'clock (+Y)
            f = flat_rect(bm, -0.6, 0.6, 0.8, r - 1.0, 20.06, mat=1)
            WA.fix_normals(bm)
        names.append(mk(f"dj_knob_{kn}{sfx}", coll, root, [mp["dj_knob"], mp["dj_line"]], knob, loc=(x, y, T),
                        smooth=not lite, auto=40).name)

    def buttons_orange(bm):
        for dx in (0.0, DJ_DECK_DX):
            for x, y, r in DJ_ORANGE_BTNS:
                disc(bm, r, T, T + 2.2, cx=x + dx, cy=y, seg=seg_b, ft=0 if lite else 0.6)
            for x in DJ_PAD_X:
                rslab(bm, 16.0, 5.0, T, T + 1.8, 1.0, cx=x + dx, cy=DJ_MODE_Y, n=1, fn=1)
        for x, y, r in DJ_MIX_ORANGE:
            disc(bm, r, T, T + 2.2, cx=x, cy=y, seg=seg_b, ft=0 if lite else 0.6)
        for x, y, w, h in DJ_RECT_ORANGE:
            rslab(bm, w, h, T, T + 1.8, 1.0, cx=x, cy=y, n=1, fn=1)
        WA.fix_normals(bm)
    names.append(mk("dj_buttons_lit" + sfx, coll, root, [mp["emit_orange"]], buttons_orange).name)

    def buttons_dark(bm):
        for dx in (0.0, DJ_DECK_DX):
            for x, y, r in DJ_BLACK_BTNS:
                disc(bm, r, T, T + 2.4, cx=x + dx, cy=y, seg=seg_b, ft=0 if lite else 0.6)
            rslab(bm, DJ_SHIFT[2], DJ_SHIFT[2], T, T + 2.0, 1.0, cx=DJ_SHIFT[0] + dx, cy=DJ_SHIFT[1], n=1, fn=1)
        for x, y, w, h in DJ_RECT_BLACK:
            rslab(bm, w, h, T, T + 2.0, 1.0, cx=x, cy=y, n=1, fn=1)
        WA.fix_normals(bm)
    names.append(mk("dj_buttons" + sfx, coll, root, [mp["dj_knob"]], buttons_dark).name)

    def meters(bm):
        (xa, xb), (ya, yb) = DJ_METER
        for x in (xa, xb):
            for k in range(5):
                y = ya + (yb - ya) * k / 4
                m = 2 if k == 0 else (3 if k < 3 else 1)
                f = flat_rect(bm, x - 1.1, x + 1.1, y - 2.4, y + 2.4, T + 0.45, mat={1: 0, 2: 1, 3: 2}[m])
    names.append(mk("dj_meters" + sfx, coll, root, [mp["emit_green"], mp["emit_red"], mp["emit_amber"]], meters).name)

    def ports(bm):        # the headphone jack on the front; on the rear two USB-C, the switch, RCA x2, mic, att, lock
        def face(x, z, w, h, front, round_=False):
            y = -DJ_D / 2 - 0.05 if front else DJ_D / 2 + 0.05
            if round_:
                n_ = 10 if lite else 20
                pts = [(x + w / 2 * math.cos(2 * math.pi * i / n_), z + w / 2 * math.sin(2 * math.pi * i / n_)) for i in range(n_)]
            else:
                pts = [(x - w / 2, z - h / 2), (x + w / 2, z - h / 2), (x + w / 2, z + h / 2), (x - w / 2, z + h / 2)]
            vs = [bm.verts.new(V(a, y, b)) for a, b in pts]
            bm.faces.new(list(reversed(vs)) if front else vs)
        face(-57.0, 18.0, 6.5, 6.5, True, True)
        for x, w, h, rnd in ((77.2, 9.0, 3.2, False), (57.4, 9.0, 3.2, False), (32.8, 4.0, 7.0, False),
                             (-60.3, 10.0, 10.0, True), (-74.5, 10.0, 10.0, True), (-108.2, 11.0, 11.0, True),
                             (-123.0, 8.0, 8.0, True), (-146.7, 3.0, 6.0, False)):
            face(x, 16.0, w, h, False, rnd)
        WA.fix_normals(bm)
    names.append(mk("dj_ports" + sfx, coll, root, [mp["port"]], ports).name)
    try:
        from lib import brands
        body_ob = bpy.data.objects["dj_body" + sfx]
        bx, by, bw, bh = DJ_BRAND_TOP
        b1 = brands.decal("dj", at=(bx * MM, by * MM, (T + 0.36) * MM), normal=(0, 0, 1), up=(0, 1, 0), height=bh * MM,
                          max_width=bw * MM, finish="printed", colour=DJ_BRAND, parent=root, collection=coll, lite=lite,
                          name="dj_brand_top")
        rx, rz, rw, rh = DJ_BRAND_REAR
        b2 = brands.decal("dj", at=(rx * MM, (DJ_D / 2) * MM, rz * MM), normal=(0, 1, 0), up=(0, 0, 1), height=rh * MM,
                          max_width=rw * MM, finish="printed", colour="#a9a9ab", parent=root, collection=coll, lite=lite,
                          name="dj_brand_rear")
        names += [b.name for b in (b1, b2) if b is not None]
    except Exception as e:
        print("dj brand:", e)
    return {"all": names, "roots": [sroot.name, root.name], "dj": names, "dj_stand": stand}


def build_lightstick(coll, mp, lite=False, rough=False, sfx=""):
    """Our own lightstick standing in its cradle; root at the cradle's base centre."""
    root = WA.empty("lightstick_root" + sfx, coll)
    names = []
    seg = 16 if lite else 48

    def lathe_obj(prof, seg_=seg, close_top=True, close_bot=True):
        def f(bm):
            rings = []
            for r, z in prof:
                rings.append([bm.verts.new(V(r * math.cos(2 * math.pi * i / seg_), r * math.sin(2 * math.pi * i / seg_), z))
                              for i in range(seg_)])
            for k in range(len(rings) - 1):
                for i in range(seg_):
                    bm.faces.new((rings[k][i], rings[k][(i + 1) % seg_], rings[k + 1][(i + 1) % seg_], rings[k + 1][i]))
            if close_bot:
                bm.faces.new(list(reversed(rings[0])))
            if close_top:
                bm.faces.new(rings[-1])
            WA.fix_normals(bm)
        return f
    # the cradle: a low round base with a cup that holds the handle's foot
    cradle = [(33.0, 0.0), (35.0, 1.5), (35.0, 6.0), (33.5, 8.0), (20.0, 9.5), (18.5, 12.0), (18.0, 30.0), (16.8, 31.0),
              (15.6, 30.0), (15.6, 12.0)]
    if rough:
        cradle = [(35.0, 0.0), (35.0, 8.0), (18.0, 30.0), (15.6, 30.0)]
    names.append(mk("lightstick_cradle" + sfx, coll, root, [mp["ls_white"]], lathe_obj(cradle, close_top=True),
                    smooth=not lite, auto=40).name)
    handle = [(10.0, 12.0), (13.2, 12.5), (13.6, 40.0), (14.2, 100.0), (15.0, 150.0), (15.4, 158.0)]
    names.append(mk("lightstick_handle" + sfx, coll, root, [mp["ls_white"]], lathe_obj(handle), smooth=not lite, auto=40).name)
    if not rough:
        grip = [(13.9, 52.0), (14.35, 54.0), (14.55, 92.0), (14.2, 94.0)]
        names.append(mk("lightstick_grip" + sfx, coll, root, [mp["ls_grip"]], lathe_obj(grip), smooth=not lite).name)

        def button(bm):
            rslab(bm, 9.0, 14.0, 0.0, 1.6, 4.0, ft=0.0 if lite else 0.6, n=2, fn=1)
        b = mk("lightstick_button" + sfx, coll, root, [mp["ls_pearl"]], button)
        b.location = (0, -14.75 * MM, 118 * MM)
        b.rotation_euler = (math.radians(90), 0, 0)
        names.append(b.name)
        # the crown: a pearl collar with six rounded petals that hold the orb
        collar = [(15.4, 156.0), (19.0, 158.0), (21.0, 163.0), (20.5, 167.0), (16.0, 168.0)]
        names.append(mk("lightstick_collar" + sfx, coll, root, [mp["ls_pearl"]], lathe_obj(collar), smooth=not lite).name)

        def petals(bm):
            for k in range(6):
                a = 2 * math.pi * k / 6
                fs = rslab(bm, 9.0, 3.0, 0.0, 26.0, 1.4, ft=0.0 if lite else 1.2, n=1, fn=1)
                vs = {v for f in fs for v in f.verts}
                for v in vs:
                    x, y, z = v.co.x / MM, v.co.y / MM, v.co.z / MM
                    rr = 20.0 + 6.0 * (z / 26.0) ** 1.4 + y            # flares outward with the orb
                    v.co = V(rr * math.cos(a) - x * math.sin(a), rr * math.sin(a) + x * math.cos(a), 164.0 + z)
            WA.fix_normals(bm)
        names.append(mk("lightstick_petals" + sfx, coll, root, [mp["ls_pearl"]], petals, smooth=not lite, auto=40).name)
    # the head: a glowing egg-shaped core inside a faceted clear shell, a pearl cap on top
    zc, H, Rh = 170.0, 92.0, 33.5
    core = []
    shell = []
    for k in range(0, 13):
        t = k / 12
        z = zc + 4 + (H - 10) * t
        r = (Rh - 5) * math.sin(math.pi * (0.04 + 0.92 * t)) ** 0.8 * (1.0 - 0.18 * t)
        core.append((max(r, 0.1), z))
    for k in range(0, 9):
        t = k / 8
        z = zc + H * t
        r = Rh * math.sin(math.pi * (0.06 + 0.88 * t)) ** 0.75 * (1.0 - 0.16 * t)
        shell.append((max(r, 0.5), z))
    names.append(mk("lightstick_head" + sfx, coll, root, [mp["ls_head"]], lathe_obj(core, seg_=12 if lite else 40),
                    smooth=True).name)
    if not rough:
        names.append(mk("lightstick_shell" + sfx, coll, root, [mp["ls_shell"]], lathe_obj(shell, seg_=12)).name)
        topcap = [(7.0, zc + H - 2.0), (7.5, zc + H + 1.0), (5.5, zc + H + 4.5), (0.0, zc + H + 5.5)]
        names.append(mk("lightstick_cap" + sfx, coll, root, [mp["ls_pearl"]], lathe_obj(topcap, close_top=False),
                        smooth=not lite).name)
    return {"all": names, "roots": [root.name], "lightstick": names}


BUILDERS = {"laptop": build_laptop, "dj": build_dj, "lightstick": build_lightstick}
STUDIO_AT = {"laptop": (0.0, 0.0, 0.0), "dj": (0.95, 0.0, -0.9), "lightstick": (0.45, 0.0, 0.0)}   # dj: the stand's floor


def build(parts=None, rough=False, lite=False, collection=None, studio=True):
    parts = parts or PARTS
    sfx = "_lite" if lite else ""
    coll = collection
    if coll is None:
        coll = bpy.data.collections.get(NAME) or bpy.data.collections.new(NAME)
        if coll.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(coll)
    mp = mats(lite)
    names = {"all": [], "roots": [], "parts": {}}
    for p in parts:
        n = BUILDERS[p](coll, mp, lite=lite, rough=rough, sfx=sfx)
        names["parts"][p] = n
        for k, v in n.items():
            if k in ("all", "roots"):
                names[k] += v
            else:
                names[k] = v
        if studio:
            r = bpy.data.objects[n["roots"][0]]
            r.location = STUDIO_AT[p]
    bpy.context.view_layer.update()
    return names


def build_room(collection=None, lite=False):
    """The group at plan v3's numbers (blender/lib/plan_v3.py) for the room test. plan v3's `at` z is a part's bottom.
      mstand_root     at plan "mstand" (centre, the desk top), yaw LAPTOP_YAW; the laptop rides on its plate
      dj_stand_root   at plan "dj_stand" (centre, the floor), yaw -90; the controller on it at plan's offset
      lightstick_root at plan "lightstick" (the stand's top), yaw -90 (its button faces the room)"""
    from lib import plan_v3 as P
    names = build(parts=["laptop", "dj", "lightstick"], lite=lite, collection=collection, studio=False)
    sfx = "_lite" if lite else ""
    CP = P.CP

    def put(root, x, y, z, yaw):
        o = bpy.data.objects[root + sfx]
        o.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
    a = CP["mstand"]["at"]
    put("mstand_root", a[0], a[1], a[2], CP["mstand"]["yaw"])
    a = CP["dj_stand"]["at"]
    put("dj_stand_root", a[0], a[1], a[2], CP["dj_stand"]["yaw"])
    a = CP["lightstick"]["at"]
    put("lightstick_root", a[0], a[1], a[2], CP["dj_stand"]["yaw"])
    bpy.context.view_layer.update()
    return names


# ---------------------------------------------------------------------------
# 6. photo views (compare)
# ---------------------------------------------------------------------------
LAP_EXPLAIN = ("Apple's front shot is a perspective render from slightly above with the lid at about 100 degrees; the "
               "silver base edge and feet are thin and the screen glass meets the light background")
MS_EXPLAIN = ("Rain Design's drawings are perspective renders, not true orthographic views: the far end of the sloped "
              "plate is drawn smaller, so its outline is a trapezoid; and the 10 mm sheet is a thin shape, so a pixel "
              "or two of edge costs a lot of IoU")
DJ_EXPLAIN = ("the knob, fader-cap and jog-dimple silhouettes are a few pixels each; the body, its height and the jog "
              "rings match")
PHOTOS = {
    "laptop-front": dict(photo=os.path.join(LAP_REF, "front-open-silver-apple-store.jpg"), part="laptop",
                         title="MacBook Pro 16: front, open (Apple) vs our model",
                         camera={"mode": "fit", "view": "front", "tilts": [0.0, 3.0, 6.0]}, mask=0.93,
                         crop=(15, 930, 150, 720), fill=True, explain=LAP_EXPLAIN),
    "laptop-lid-top": dict(photo=os.path.join(FOOT, "cutouts", "top-lid-closed-silver-cut.png"), part="laptop_closed",
                           title="MacBook Pro 16: closed, from above (Apple) vs our model (lid closed for the test)",
                           camera={"mode": "ortho", "view": "top"}, mask="alpha", crop=(0, 926, 0, 646), fill=True),
    "mstand-front": dict(photo=os.path.join(MS_REF, "dims-front-253x150.png"), part="mstand",
                         title="mStand: front (Rain Design drawing) vs our model",
                         camera={"mode": "ortho", "view": "front"}, mask="alpha", crop=(70, 318, 40, 205), fill=False,
                         explain=MS_EXPLAIN),
    "mstand-side": dict(photo=os.path.join(MS_REF, "dims-side-262x150.png"), part="mstand",
                        title="mStand: side (Rain Design drawing) vs our model",
                        camera={"mode": "ortho", "view": "right"}, mask="alpha", crop=(30, 262, 40, 200), fill=False,
                        explain=MS_EXPLAIN),
    "mstand-three-quarter": dict(photo=os.path.join(MS_REF, "three-quarter-stand-only.png"), part="mstand",
                                 title="mStand: three-quarter (Rain Design) vs our model",
                                 camera={"mode": "free", "view": "front", "yaws": [-65, -50, 50, 65], "tilts": [12.0, 20.0]},
                                 mask="alpha", fill=False,
                                 explain="a 280 px packshot with a soft shadow in its alpha"),
    "dj-top": dict(photo=os.path.join(DJ_REF, "top-straight-down-1792.png"), part="dj",
                   title="DDJ-FLX4 shape: straight down (Pioneer DJ) vs our model",
                   camera={"mode": "ortho", "view": "top"}, mask="alpha", fill=True,
                   explain="the photo is a near-top perspective render: the rear sockets and knob tops peek past the edge"),
    "dj-front": dict(photo=os.path.join(DJ_REF, "front-edge-1792.png"), part="dj",
                     title="DDJ-FLX4 shape: the front edge (Pioneer DJ) vs our model",
                     camera={"mode": "ortho", "view": "front"}, mask="alpha", fill=False, explain=DJ_EXPLAIN),
    "dj-rear": dict(photo=os.path.join(DJ_REF, "rear-panel-1792.png"), part="dj",
                    title="DDJ-FLX4 shape: the rear panel (Pioneer DJ) vs our model",
                    camera={"mode": "ortho", "view": "back"}, mask="alpha", fill=False, explain=DJ_EXPLAIN),
    "dj-three-quarter": dict(photo=os.path.join(DJ_REF, "three-quarter-1792.png"), part="dj",
                             title="DDJ-FLX4 shape: three-quarter (Pioneer DJ) vs our model",
                             camera={"mode": "free", "view": "front", "yaws": [22, 30, 38], "tilts": [30.0, 38.0, 46.0]},
                             mask="alpha", fill=True,
                             explain="a perspective product render from high front-left; the knob and fader tops add "
                                     "small spikes that move with the lens"),
}


def photo_objects(names, part):
    if part in ("laptop", "laptop_closed"):
        return [n for n in names.get("laptop", []) if "brand" not in n]
    if part == "mstand":
        return names.get("mstand", [])
    if part == "dj":
        return [n for n in names.get("dj", []) if "brand" not in n]
    return names["all"]


def _close_lid(sfx=""):
    h = bpy.data.objects.get("laptop_hinge" + sfx)
    root = bpy.data.objects.get("laptop_root" + sfx)
    old_h, old_r = h.rotation_euler.x, root.matrix_basis.copy()
    h.rotation_euler.x = 0.0
    root.matrix_basis = Matrix.Translation(root.matrix_basis.translation)    # flat, for the top view
    bpy.context.view_layer.update()

    def undo():
        h.rotation_euler.x = old_h
        root.matrix_basis = old_r
        bpy.context.view_layer.update()
    return undo


def _flat_laptop(sfx=""):
    root = bpy.data.objects.get("laptop_root" + sfx)
    old = root.matrix_basis.copy()
    root.matrix_basis = Matrix.Translation(root.matrix_basis.translation)
    bpy.context.view_layer.update()

    def undo():
        root.matrix_basis = old
        bpy.context.view_layer.update()
    return undo


def outline_views(names):
    out = []
    have = set(names.get("parts", names).keys())
    for view, p in PHOTOS.items():
        need = {"laptop_closed": "laptop", "mstand": "laptop"}.get(p["part"], p["part"])
        if need not in have:
            continue
        mask = p.get("mask", 0.93)
        v = dict(name=f"{NAME}-{view}", title=p["title"], photo=p["photo"], mask=mask, crop=p.get("crop"),
                 fill=p.get("fill", False), objects=photo_objects(names, p["part"]), camera=dict(p["camera"]),
                 explain=p.get("explain"))
        if p["part"] == "laptop_closed":
            v["prepare"] = _close_lid
        elif p["part"] == "laptop":
            v["prepare"] = _flat_laptop
        out.append(v)
    return out


# ---------------------------------------------------------------------------
# 7. stages (wall.py's structure)
# ---------------------------------------------------------------------------
def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {NAME}: {msg}", flush=True)


def progress(msg):
    os.makedirs(FOOT, exist_ok=True)
    with open(os.path.join(FOOT, "PROGRESS.md"), "a") as f:
        f.write(f"{time.strftime('%H:%M')} [{PART}] {msg}\n")


def clear():
    WA.clear()


def stage_outline(out):
    import outline_check
    clear()
    def b(rough=True):
        n = build(rough=True)
        return {k: v for k, v in n.items() if k not in ("parts", "roots")}
    r = outline_check.run(NAME, b, outline_views, os.path.join(out, "outline"), log=log)
    progress(f"outline: {'PASS' if r['test']['passed'] else 'FAIL'} " + ", ".join(
        f"{e['name']} {e['iou']:.3f}" for e in r["views"]) + f" sheet {r.get('sheet')}")
    return r


def stage_build(out):
    clear()
    t = time.time()
    names = build()
    blend = os.path.join(BLENDER_DIR, "out", "components", f"{NAME}.blend")
    os.makedirs(os.path.dirname(blend), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    with open(os.path.join(out, f"{NAME}-names.json"), "w") as f:
        json.dump(names, f, indent=1)
    per = {p: tri_count([bpy.data.objects[n] for n in v["all"]]) for p, v in names["parts"].items()}
    log(f"built in {time.time() - t:.1f} s, {sum(per.values())} triangles {per}, saved {blend}")
    progress(f"build: {sum(per.values())} triangles {per} in {time.time() - t:.1f} s")
    return names


def _studio(sc, cycles, strength=1.0):
    from lib import compare
    compare.ensure_studio(strength)
    sc.render.film_transparent = False
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGB"
    sc.view_settings.view_transform = "AgX"
    if cycles:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 64
        sc.cycles.use_denoising = True
        try:                      # never set the Metal device in preferences (Blender 5.2 crash under --factory-startup)
            sc.cycles.device = "GPU"
        except Exception:
            pass
    else:
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = 32
        sc.eevee.use_raytracing = True


def _shoot(sc, cam, path, cycles, label):
    from lib import renderqueue
    sc.camera = cam
    sc.render.filepath = path
    if cycles:
        with renderqueue.slot(f"{NAME} {label}"):
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(write_still=True)


def floor_plane():
    from lib import materials as M
    if bpy.data.objects.get("studio_floor"):
        return
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(p)) for p in ((-3, -3, -0.9005), (4, -3, -0.9005), (4, 3, -0.9005), (-3, 3, -0.9005))]
    bm.faces.new(vs)
    WA.obj_from_bm("studio_floor", bm, M.principled("mat_studio_floor", base="#d9d7d2", rough=0.9), bpy.context.scene.collection)
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(p)) for p in ((-0.5, -0.5, -0.0005), (0.6, -0.5, -0.0005), (0.6, 0.5, -0.0005), (-0.5, 0.5, -0.0005))]
    bm.faces.new(vs)
    WA.obj_from_bm("studio_desk", bm, M.principled("mat_studio_desk", base="#f2f1ee", rough=0.6), bpy.context.scene.collection)


def stage_stills(out, names, cycles=False):
    from lib import backdrops, compare
    sc = bpy.context.scene
    _studio(sc, cycles, 0.6)
    floor_plane()
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    paths = {}
    shots = []
    groups = {"laptop": names.get("laptop", []) + names.get("mstand", []), "dj": names.get("dj", []),
              "dj_stand": names.get("dj", []) + names.get("dj_stand", []), "lightstick": names.get("lightstick", [])}
    for p, objs in groups.items():
        if not objs or (p == "dj_stand" and "dj" not in names["parts"]):
            continue
        lo, hi = compare.world_bbox(objs)
        c, size = (lo + hi) / 2, hi - lo
        if p != "dj_stand":
            shots.append((f"{p}-front", backdrops.view_camera("front", c, max(size.x, size.z * 16 / 9) * 1.15, name=f"still_{p}_front")))
        shots.append((f"{p}-hero", backdrops.three_quarter_camera(c, max(size) * 1.05, az=-32, el=22, name=f"still_{p}_hero")))
    keep = os.environ.get("RETURNDESK_STILLS")
    if keep:
        shots = [(k, c) for k, c in shots if k in keep.split(",")]
    for k, cam in shots:
        p = os.path.join(out, f"{NAME}-{k}.png")
        _shoot(sc, cam, p, cycles, k)
        paths[k] = p
    log(f"stills: {', '.join(paths)}")
    progress(f"stills ({'Cycles' if cycles else 'EEVEE'}): {', '.join(os.path.basename(p) for p in paths.values())}")
    return paths


def _w(name):
    o = bpy.data.objects.get(name)
    return o.matrix_world if o else Matrix.Identity(4)


def closeup_specs(names):
    """(key, title, photo, cam pos, target, lens) in world coordinates, from the parts' own frames."""
    specs = []
    if "laptop" in names["parts"]:
        L = _w("laptop_root")
        S = _w("mstand_root")
        P_ = lambda m, x, y, z: m @ Vector((x * MM, y * MM, z * MM))
        specs += [
            ("lp-keyboard", "MacBook Pro 16: the keyboard and the trackpad from above",
             os.path.join(LAP_REF, "top-keyboard-deck-open.jpg"), P_(L, 0, -60, 520), P_(L, 0, -10, 0), 50),
            ("lp-hinge", "MacBook Pro 16 on the mStand: the hinge, the stand's side and its round hole",
             os.path.join(MS_REF, "detail-side-hole-with-laptop.jpg"), P_(S, 420, 260, 60), P_(S, 0, 80, 70), 45),
            ("lp-mark", "MacBook Pro 16: the lid's back and the round mark (ours, in place of the maker's logo)",
             os.path.join(LAP_REF, "lid-silver-wide.jpg"), P_(S, 60, 700, 260), P_(S, 0, 60, 230), 50),
            ("ms-top", "mStand: the plate's pads, the teardrop and the front lip",
             os.path.join(MS_REF, "top-surface-pads-lip.png"), P_(S, 160, -330, 70), P_(S, 0, -110, 85), 50),
        ]
    if "dj" in names["parts"]:
        D = _w("dj_root")
        P_ = lambda x, y, z: D @ Vector((x * MM, y * MM, z * MM))
        top = os.path.join(DJ_REF, "top-straight-down-1792.png")
        specs += [
            ("dj-deck", "DDJ-FLX4 shape: the left deck, jog, pads, cue and play", os.path.join(DJ_REF, "three-quarter-1792.png"),
             P_(-260, -330, 300), P_(-160, -30, 40), 45),
            ("dj-mixer", "DDJ-FLX4 shape: the mixer section (knobs, meters, faders, crossfader)",
             os.path.join(DJ_REF, "detail-left-deck-and-mixer-top-1000.png"), P_(0, -170, 420), P_(0, 10, 40), 45),
            ("dj-brand", "DDJ-FLX4 shape: the maker's-name spot (ours: KORVA, proposed) and the crossfader", top,
             P_(0, -260, 160), P_(0, -105, 40), 60),
            ("dj-rear", "DDJ-FLX4 shape: the rear panel and the rear name", os.path.join(DJ_REF, "rear-panel-1792.png"),
             P_(60, 520, 90), P_(0, 136, 20), 45),
        ]
    if "lightstick" in names["parts"]:
        R = _w("lightstick_root")
        P_ = lambda x, y, z: R @ Vector((x * MM, y * MM, z * MM))
        specs.append(("ls-head", "The lightstick (our own design): the head, crown and cradle",
                      os.path.join(FOOT, "ref-lightstick-none.png"), P_(-160, -330, 230), P_(0, 0, 150), 50))
    return specs


def stage_closeups(out, names, cycles=False, only=None):
    sc = bpy.context.scene
    _studio(sc, cycles, 0.5)
    floor_plane()
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 720, 100
    d = os.path.join(out, "closeups")
    os.makedirs(d, exist_ok=True)
    pairs = []
    for key, title, photo, pos, tgt, lens in closeup_specs(names):
        if only and key not in only:
            continue
        cam = WA.look_cam(f"still_cu_{key.replace('-', '_')}", tuple(pos), tuple(tgt), lens)
        p = os.path.join(d, f"{key}.png")
        _shoot(sc, cam, p, cycles, key)
        pairs.append(dict(key=key, title=title, photo=photo, render=p))
    jp = os.path.join(d, "pairs.json")
    with open(jp, "w") as f:
        json.dump(pairs, f, indent=1)
    import subprocess
    subprocess.run(["/opt/anaconda3/bin/python3", os.path.abspath(__file__), "--pairs", jp, d], check=False)
    log(f"close-ups: {len(pairs)} in {d}")
    progress(f"closeups ({'Cycles' if cycles else 'EEVEE'}): {len(pairs)} pairs in {d}")
    return pairs


def stage_compare(out, names):
    from lib import compare
    views = outline_views(names)
    rep = compare.run(views, os.path.join(out, "compare"), NAME, log=log)
    log(f"compare test {'PASSED' if rep['test']['passed'] else 'FAILED'}: {rep['paths']['md']}")
    progress(f"compare: {'PASS' if rep['test']['passed'] else 'FAIL'} " + ", ".join(
        f"{e['name']} {e['iou']:.3f}" for e in rep["views"]))
    return rep["test"]


OWN_MATERIAL = ("emit", "pad", "screen", "legend", "brand", "shell", "head", "bezel")


def bake_lite(objs, out, size=1024, orm_size=512):
    """wall.bake_lite's pattern with this group's name: one base atlas and an ORM for the opaque lite meshes; the
    emissives, the screen, the legends, the brand, the glass and the shell keep their own small materials."""
    import numpy as np
    from lib import materials as M
    from lib import renderqueue
    import desktop as DT
    scene = bpy.context.scene
    baked = [o for o in objs if o.type == "MESH" and "brand" not in o.name and o.data.materials
             and not any(m is None or any(k in m.name for k in OWN_MATERIAL) for m in o.data.materials)]
    for o in baked:
        if o.data.users > 1:
            o.data = o.data.copy()
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in baked:
        lay = o.data.uv_layers.get("UVMap") or o.data.uv_layers.new(name="UVMap")
        o.data.uv_layers.active = lay
        o.select_set(True)
    bpy.context.view_layer.objects.active = baked[0]
    with WA._ctx(baked[0], baked):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.002, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    prev = scene.render.engine
    scene.render.engine = "CYCLES"
    try:                      # never set the Metal device in preferences under --factory-startup (chair.py's fix)
        scene.cycles.device = "GPU"
    except Exception as e:
        log(f"bake on CPU ({e})")
    scene.cycles.use_denoising = False
    hidden = []
    for o in scene.objects:
        if o not in baked and o.type == "MESH" and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.light_settings.distance = 0.01
    base = DT._image(f"{NAME}_atlas", size)
    rough = DT._image(f"{NAME}_rough_tmp", orm_size, True)
    metal = DT._image(f"{NAME}_metal_tmp", orm_size, True)
    ao = DT._image(f"{NAME}_ao_tmp", orm_size, True)
    with renderqueue.slot(f"{NAME} lite bake"):
        DT._bake(baked, base, "base", 4)
        DT._bake(baked, rough, "rough", 4)
        DT._bake(baked, metal, "metal", 4)
        DT._bake(baked, ao, "ao", 32)
    for o in hidden:
        o.hide_render = False
    orm = DT._image(f"{NAME}_orm", orm_size, True)
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
    for im, fn, q in ((base, f"{NAME}_atlas.jpg", 90), (orm, f"{NAME}_orm.jpg", 92)):
        p = os.path.join(out, fn)
        im.filepath_raw = p
        im.file_format = "JPEG"
        scene.render.image_settings.quality = q
        im.save()
        kb[fn] = round(os.path.getsize(p) / 1024)
    m, nt, b = M._new(f"mat_{NAME}_lite")
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
    gg.node_tree = DT._gltf_group()
    nt.links.new(sep.outputs[0], gg.inputs["Occlusion"])
    for o in baked:
        o.data.materials.clear()
        o.data.materials.append(m)
    scene.render.engine = prev
    return kb


def stage_export(out, names, bake=True):
    d = os.path.join(BLENDER_DIR, "out", "components")
    os.makedirs(d, exist_ok=True)
    sfx = "" if PART == "all" else f"-{PART.replace(',', '+')}"
    rich = WA._export(WA._with_empties(names["all"]), os.path.join(d, f"{NAME}{sfx}-rich.glb"))
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    lite_names = build(lite=True, studio=False)
    objs = [bpy.data.objects[n] for n in lite_names["all"]]
    kb = bake_lite(objs, out) if bake else {}
    lite = WA._export(WA._with_empties(lite_names["all"]), os.path.join(d, f"{NAME}{sfx}-lite.glb"))
    per = {p: tri_count([bpy.data.objects[n] for n in v["all"]]) for p, v in lite_names["parts"].items()}
    log(f"GLB rich {rich['kb']} KB {rich['triangles']} tris; lite {lite['kb']} KB {lite['triangles']} tris {per} {kb}")
    progress(f"export: rich {rich['kb']} KB {rich['triangles']} tris; lite {lite['kb']} KB {lite['triangles']} tris {per}")
    return {"rich": rich, "lite": lite, "lite_per_part": per, "images_kb": kb}


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    st = next((x for x in a if not x.startswith("--") and os.path.sep not in x), "default")
    stages = ["build", "stills", "compare", "closeups", "export"] if st == "default" else st.split(",")
    out = os.environ.get("RETURNDESK_OUT") or FOOT
    os.makedirs(out, exist_ok=True)
    rep = {"stages": stages, "part": PART}
    t0 = time.time()
    names = None
    cycles = os.environ.get("RETURNDESK_CYCLES") == "1"
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
        only = os.environ.get("RETURNDESK_CU")
        rep["closeups"] = stage_closeups(out, names, cycles, only.split(",") if only else None)
    if "export" in stages:
        rep["export"] = stage_export(out, names, bake="--nobake" not in a)
    rep["total_s"] = round(time.time() - t0, 1)
    with open(os.path.join(out, f"{NAME}-report{'-' + st if st != 'default' else ''}.json"), "w") as f:
        json.dump(rep, f, indent=1, default=str)
    log(f"done in {rep['total_s']} s: {out}")


if __name__ == "__main__":
    if bpy is not None:
        main()
        bpy.ops.wm.quit_blender()
    elif "--pairs" in sys.argv:
        i = sys.argv.index("--pairs")
        WA.pairs_sheet(sys.argv[i + 1], sys.argv[i + 2])
    elif "--legends" in sys.argv:
        i = sys.argv.index("--legends")
        make_legends(int(sys.argv[i + 1]), sys.argv[i + 2])
