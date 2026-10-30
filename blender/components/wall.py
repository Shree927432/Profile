"""The wall group (component, 2026-10-29): the parts on the AI-lab walls above and beside the desk.

    WALL_PART=shelf|plants|pegboard|neon|nanoleaf|all (default all)
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/components/wall.py -- [stages] [--cycles] [--nobake]

stages: outline | build,stills,compare,closeups,export (default) | any comma list.
Cycles: WALL_CYCLES=1 (the `--cycles` flag after `--` is taken by Blender's own parser in 5.2 and stops the run).
WALL_OUT=<dir> renders somewhere else; WALL_CU=key,key limits the close-ups; WALL_STILLS=key,key the stills.
Plain Python (Pillow): python3 wall.py --pairs <pairs.json> <dir>
Room: build_room(collection, lite) places every part at plan v3's numbers (blender/design/room_v3_component_test.py).

Round 2 (2026-10-30, coordinator review): ARVELL embossed in the centre of each cup's disc; the Nanoleaf an
edge-to-edge cluster in plan v3's 0.58 x 0.52 (NANO_CELLS); the neon as single-stroke 8 mm tubes swept along the
words' skeleton (neon_strokes.json) with round ends and a soft halo card; the pegboard's halo a rounded-rectangle
falloff in saturated blue-white; the frames' easel legs cut; pot 1's vines over the shelf's end (clear of key light 1).

Parts (plan v3 names, blender/lib/plan_v3.py):
  shelf     the white floating shelf 180 x 25 x 4 with three black 30 x 40 portrait frames (frame_1..3) standing on
            it; each frame's light grey mount is `frame_N_picture`, a clean 0..1 UV, top-left at (0, 1)
  plants    two trailing pothos in white pots (vine_pot_1..2) with vines hanging VINE_LEN (vine_1..2)
  pegboard  IKEA SKADIS 76 x 56 white, 4 cm off the wall on spacers, a soft glow behind it (pegboard_glow), with the
            Audio-Technica ATH-M50x white (headphones: _cup_l/_r, _band, _brand) hanging on a SKADIS hook
  neon      white LED neon on clear acrylic 0.70 x 0.26 (neon, neon_glow); the words come from
            content/room-brands.json "neon" -> "text" at build time
  nanoleaf  Nanoleaf Shapes Triangles, 7 panels (nanoleaf_panel_01..07), the owner's photo's arrangement

Frames: every part has its own local frame with the wall behind it at +Y and the viewer at -Y, Z up, so the room
test places each part's root empty at plan v3's `at` with its yaw (0 on the back wall, 90 on the left wall):
  shelf      origin at the shelf's centre x/y, z = the shelf's underside (plan: SHELF z - t); the wall at y +0.125
  frame_N    origin at the frame's bottom back edge, standing on the shelf top (z 0); it leans back FRAME_LEAN so
             its top touches a wall FRAME_WALL behind the origin
  vine_pot_N origin at the pot's base centre on the shelf top; the shelf's front edge at y -0.14 (plan: pot 0.11
             from the wall, shelf 0.25 deep); `end_side` = -1 or +1 says which x side is the shelf's end (7 cm away)
  pegboard   origin at the board's centre; the wall at y +0.04 (plan: board centre at RY - off + 0.01)
  headphones origin at the hook point (the band's inside top); the band's plane parallel to the wall
  neon       origin at the acrylic plate's centre; the wall at y +0.01
  nanoleaf   origin at the layout's centre; the wall at y +0.005
Brand names: ARVELL on the headphones from content/room-brands.json via lib/brands.py. The Nanoleaf's LUMARA is not
placed: no front logo shows on the real panels. The shelf, frames, plants, pegboard and neon carry no brand.
"""
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(BLENDER_DIR, ".."))
sys.path.insert(0, BLENDER_DIR)
sys.path.insert(0, os.path.join(BLENDER_DIR, "tools"))

try:
    import bpy
    import bmesh
    from mathutils import Matrix, Vector
except ImportError:
    bpy = None

NAME = "wall"
MM = 0.001
PART = os.environ.get("WALL_PART", "all")
PARTS = ["shelf", "plants", "pegboard", "neon", "nanoleaf"] if PART == "all" else PART.split(",")
REF = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab")
FOOT = os.path.join(REPO, "video-local", "footage", "2026-10-30-components", "wall")
FOOT_BEFORE = os.path.join(REPO, "video-local", "footage", "2026-10-29-components", "wall")   # round 1, kept
FONTS = os.path.join(BLENDER_DIR, "assets", "fonts")
CONTENT = os.path.join(REPO, "content", "room-brands.json")

# ---------------------------------------------------------------------------
# 1. numbers (mm unless said), tagged OFFICIAL / MEASURED / EST
# ---------------------------------------------------------------------------
SHELF_L, SHELF_D, SHELF_T = 1800.0, 250.0, 40.0        # plan v3 SHELF (OFFICIAL for the plan)
FRAME_W, FRAME_H, FRAME_T = 300.0, 400.0, 30.0         # plan v3: black 30 x 40 portrait frames
FRAME_MOULD = 20.0                                     # EST: the moulding's face width
FRAME_LIP = 8.0                                        # EST: the glass rebate behind the face
FRAME_WALL = 45.0                                      # EST: the wall behind the frame's bottom back edge (the lean)
FRAME_LEAN = math.degrees(math.atan(FRAME_WALL / FRAME_H))   # the top back edge touches the wall
FRAME_DX = (-380.0, 0.0, 380.0)                        # plan v3: frame spacing along the shelf
PICTURE = (FRAME_W - 2 * FRAME_MOULD, FRAME_H - 2 * FRAME_MOULD)   # the mount's visible face, 260 x 360
POT_D, POT_H = 120.0, 110.0                            # plan v3: pothos in a white pot 12 x 11
VINE_LEN = 570.0                                       # plan v3 VINE_LEN
SHELF_FRONT_Y = -140.0                                 # the shelf's front edge from the pot's centre
POT_END_X = 70.0                                       # the shelf's end from the pot's centre
PEG_W, PEG_H, PEG_T = 760.0, 560.0, 5.0                # OFFICIAL 760 x 560; 5 thick (third party, UNSURE)
PEG_R = 10.0                                           # corner radius (third party, UNSURE)
PEG_SLOT = (5.0, 15.0)                                 # slot 5 x 15, long axis vertical (third party)
PEG_PITCH = 40.0                                       # MEASURED from the packshot: 39.8 x 40
PEG_COLS, PEG_ROWS = 19, 14                            # MEASURED from the packshot
PEG_FIRST_X = 22.0                                     # MEASURED: first slot centre from the left edge (UNSURE)
PEG_OFF = 40.0                                         # plan v3: 4 cm off the wall, backlit
PEG_SCREW = (28.0, 28.0)                               # EST: the four mounting screws in from the corners
HOOK_WIRE = 5.0                                        # EST: SKADIS hook wire
HOOK_REACH = 45.0                                      # EST: the hook's reach from the board face
# ATH-M50x (no official drawing; MEASURED from the Thomann photos against the 45 mm driver and the 285 g class)
HP_BAND_HW = 92.0                                      # EST: the band's inside half-width at the yoke pivots
HP_BAND_DROP = 118.0                                   # EST: the yoke pivots below the band's top
HP_BAND_W, HP_BAND_T = 30.0, 11.0                      # EST: the band's width (across the head) and thickness
HP_PAD_W, HP_PAD_T = 36.0, 17.0                        # EST: the padded top third
HP_SLIDER_W, HP_SLIDER_T = 17.0, 6.0                   # EST: the slider arms
HP_CUP = (98.0, 88.0, 42.0)                            # EST: cup height, width, depth (an oval, the M50x shell)
HP_PAD_RING = (26.0, 24.0)                             # EST: pad thickness, pad ring width
HP_DISC = 56.0                                         # EST: the logo disc 40 across with a thin silver ring
HP_YOKE = (13.0, 9.0)                                  # EST: the yoke's section (width, depth)
HP_CUP_Z = -205.0                                      # EST: the cup centre below the band's top (hanging)
HP_LOGO = (30.0, 7.0)                                  # EST: the wordmark in the disc's centre, inside the silver ring,
#                                                        about the real audio-technica mark's size (30 wide in a 56 disc)
CUP_CX = HP_BAND_HW - 18.0                             # EST: the cup centres, 148 apart (the pads about 90 apart when hanging)
NEON_W, NEON_H = 700.0, 260.0                          # plan v3: 0.70 x 0.26
NEON_PLATE_T = 4.0                                     # EST: clear acrylic 3 to 5
NEON_TUBE = 8.0                                        # EST: LED neon flex 6 to 8 wide
NEON_STANDOFF = (12.0, 10.0)                           # EST: standoff cap diameter, length off the wall
NEON_TINT = "#ffffff"
NANO_SIDE, NANO_H = 230.0, 200.0                       # OFFICIAL 23 x 20
NANO_T, NANO_MOUNT = 6.0, 10.0                         # OFFICIAL: 6 mm edge, 10 mm mounted
NANO_CORNER = 14.0                                     # EST from the close-up: softly rounded corners
NANO_FRAME = 4.0                                       # EST: the thin white frame around the diffuser
NANO_GAP = 3.0                                         # EST: the seam between joined panels
NANO_TINT = "#86a8ff"
NANO_GLOW = dict(rich=4.0, lite=1.5)
NEON_GLOW = dict(rich=6.0, lite=1.5)                   # the tubes; GLB 1.5 like the PC glow (no bloom on the site)
PEG_GLOW = dict(rich=3.0, lite=1.5)                    # the halo on the wall around the pegboard
PEG_HALO = 170.0                                       # EST: the halo reaches about 17 cm past the board's edge
PEG_GLOW_TINT = "#9fc8ff"                              # the slots in the lite tile
PEG_HALO_TINT = "#4f8fff"                              # the halo: a saturated blue-white so it reads on a white wall
# The owner's photo (docs/moodboard/local/ai-desk-reference-1.jpg): seven triangles in an irregular cluster, edge to
# edge, pointing sideways (vertical bases), a zigzag spine with panels branching off it. Round 2 (coordinator): the
# round-1 straight column (920 tall) broke plan v3's footprint (0.58 x 0.52). The cells sit on a sideways triangle
# lattice: column c (0..2, each one triangle height h = 200 wide), row k (0..2, half-sides of 115 up); a cell points
# right when c + k is even. Seven of the nine cells: about 582 x 430 outside, inside the footprint.
NANO_CELLS = [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)]
NEON_PX_PER_MM = 2048 / 700.0                          # the neon raster: 2048 px across the plate's width
HOOK_COL, HOOK_ROW = 14, 1                             # the hook's slot (column from the left, row from the top): the
#                                                        board's upper right: x +0.202 for plan v3's headphones at +0.20

CUT = os.path.join(FOOT, "cutouts")
HP_REF = os.path.join(REF, "13-headphones")
HP_EXPLAIN = ("pose, not shape: the Thomann shots show the band slid out and the cups swivelled flat for display; ours "
              "hangs on the SKADIS hook with the sliders in and the cups facing each other, so the arch is shorter and the "
              "cups sit higher and closer; white on white also leaves a ragged photo mask")
PHOTOS = {
    "headphones-front": dict(photo=os.path.join(HP_REF, "front-1.jpg"), part="headphones",
                             title="ATH-M50x: front (Thomann photo) vs our model",
                             camera={"mode": "fit", "view": "front", "tilts": [0.0, 6.0, 12.0],
                                     "distances": [0.45, 0.65, 0.9, 1.3]}, mask=0.97, fill=False,
                             explain=HP_EXPLAIN),
    "headphones-three-quarter": dict(photo=os.path.join(HP_REF, "three-quarter-1.jpg"), part="headphones",
                                     title="ATH-M50x: three-quarter (Thomann photo) vs our model",
                                     camera={"mode": "fit", "view": "front", "yaws": [20.0, 32.0, 44.0], "tilts": [0.0, 8.0],
                                             "distances": [0.45, 0.65, 0.9, 1.3]},
                                     mask=0.97, fill=True, explain=HP_EXPLAIN),
    "pegboard-front": dict(photo=os.path.join(REF, "05-pegboard", "pegboard-76x56-front.jpg"), part="pegboard",
                           title="SKADIS 76 x 56: front (IKEA packshot) vs our model",
                           camera={"mode": "ortho", "view": "front"}, mask=0.985, fill=True,
                           explain="a white board on a white packshot: the mask is the faint shadow edge"),
}


# ---------------------------------------------------------------------------
# 2. materials
# ---------------------------------------------------------------------------
def mats(lite=False):
    from lib import materials as M
    sfx = "_lite" if lite else ""
    g = bpy.data.materials.get
    out = {}

    def P(name, **kw):
        n = f"mat_wall_{name}{sfx}"
        out[name] = g(n) or M.principled(n, **kw)
    P("white", base="#f4f4f2", rough=0.55)                       # painted shelf, pots, SKADIS, Nanoleaf frames
    P("black", base="#1a1a1c", rough=0.45)                       # the frames
    P("mount", base="#d9d9d6", rough=0.9)                        # the light grey mounts
    P("soil", base="#2a1f17", rough=1.0)
    P("leaf", base="#3f7a37", rough=0.45, sss=0.0)
    P("stem", base="#5e7f3f", rough=0.6)
    P("hp_white", base="#ececea", rough=0.5)                     # the M50x matte shell
    P("hp_pad", base="#e9e6e1", rough=0.75)                      # protein leather
    P("hp_silver", base="#d2d4d8", rough=0.25, metal=1.0)
    P("steel", base="#e8e8e6", rough=0.35, metal=0.6)            # the hook, white powder coat
    P("chrome", base="#d8dadd", rough=0.15, metal=1.0)           # standoff caps
    P("diffuser", base="#e6e2dc", rough=0.9)                     # the Nanoleaf diffuser when off (not used lit)
    glow = NANO_GLOW["lite" if lite else "rich"]
    n = f"mat_wall_nano_glow{sfx}"
    out["nano_glow"] = g(n) or M.principled(n, base="#dfe8ff", rough=0.8, emit=NANO_TINT, emit_strength=glow)
    n = f"mat_wall_neon_glow{sfx}"
    out["neon_glow"] = g(n) or M.principled(n, base="#ffffff", rough=0.35, emit=NEON_TINT,
                                            emit_strength=NEON_GLOW["lite" if lite else "rich"])
    n = f"mat_wall_peg_glow{sfx}"
    out["peg_glow"] = g(n) or _glow_card_material(n, PEG_HALO_TINT, PEG_GLOW["lite" if lite else "rich"])
    n = f"mat_wall_acrylic{sfx}"
    if g(n) is None:
        m = M.principled(n, base="#ffffff", rough=0.05)
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Transmission Weight"].default_value = 0.0 if lite else 1.0
        b.inputs["Alpha"].default_value = 0.12
        m.blend_method = "BLEND"
        m.show_transparent_back = False
        out["acrylic"] = m
    else:
        out["acrylic"] = g(n)
    n = f"mat_wall_glass{sfx}"
    if g(n) is None:
        m = M.principled(n, base="#ffffff", rough=0.02)
        m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.08
        m.blend_method = "BLEND"
        out["glass"] = m
    else:
        out["glass"] = g(n)
    out["leaf_card"] = g(f"mat_wall_leaf_card{sfx}") or _leaf_card_material(f"mat_wall_leaf_card{sfx}")
    out["peg_tile"] = g(f"mat_wall_peg_tile{sfx}") or _peg_tile_material(f"mat_wall_peg_tile{sfx}")
    return out


def _image_from(name, size, fn, data=False):
    """A packed size x size image whose RGBA comes from fn(u, v) -> (r, g, b, a), vectorised with numpy."""
    import numpy as np
    im = bpy.data.images.get(name)
    if im is not None:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, size, size, alpha=True)
    if data:
        im.colorspace_settings.name = "Non-Color"
    v, u = np.mgrid[0:size, 0:size].astype(np.float32)
    u, v = (u + 0.5) / size, (v + 0.5) / size
    px = np.stack(fn(u, v), axis=-1).astype(np.float32)
    im.pixels.foreach_set(px.ravel())
    im.pack()
    return im


def _glow_card_material(name, tint, strength):
    """An emissive card that fades to nothing at its edges (a radial alpha); for the pegboard's backlight."""
    import numpy as np
    from lib import materials as M
    gw, gh = PEG_W + 2 * PEG_HALO, PEG_H + 2 * PEG_HALO

    def fn(u, v):
        # distance (mm) outside the board's rounded rectangle, inset 30 mm (the LED strip runs behind the edge)
        x, z = np.abs(u - 0.5) * gw, np.abs(v - 0.5) * gh
        qx, qz = x - (PEG_W / 2 - 30 - 40), z - (PEG_H / 2 - 30 - 40)
        d = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qz, 0) ** 2) - 40
        a = np.exp(-np.maximum(d, 0) / (PEG_HALO * 0.45)) * np.clip((gw / 2 - x) / 25, 0, 1) * np.clip((gh / 2 - z) / 25, 0, 1)
        return np.ones_like(u), np.ones_like(u), np.ones_like(u), np.clip(a, 0, 1)
    im = _image_from(name + "_img", 256, fn)
    m, nt, b = M._new(name)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    b.inputs["Base Color"].default_value = M.rgba(tint)
    b.inputs["Emission Color"].default_value = M.rgba(tint)
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Roughness"].default_value = 1.0
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    m.blend_method = "BLEND"
    m.show_transparent_back = False
    return m


def leaf_shape(t, s=1.0):
    """A pothos leaf outline (a heart with a drawn-out tip), t in 0..1 around; returns (x, y) in leaf lengths,
    the stalk at (0, 0), the tip at (0, 1)."""
    a = t * 2 * math.pi
    # a heart-like polar form, tip down in the usual formula: rotate so the tip points +y
    x = 0.42 * math.sin(a) ** 3 * s
    y = (0.33 * math.cos(a) - 0.13 * math.cos(2 * a) - 0.05 * math.cos(3 * a) - 0.02 * math.cos(4 * a))
    return x, 0.5 - y * 1.25


def _leaf_card_material(name):
    import numpy as np
    from lib import materials as M

    def fn(u, v):
        # inside test: sample the outline polygon
        pts = [leaf_shape(i / 96) for i in range(96)]
        px = np.array([p[0] for p in pts])
        py = np.array([p[1] for p in pts])
        x = (u - 0.5) * 1.0
        y = v
        inside = np.zeros_like(u, dtype=bool)
        j = len(pts) - 1
        for i in range(len(pts)):
            cond = ((py[i] > y) != (py[j] > y)) & (x < (px[j] - px[i]) * (y - py[i]) / (py[j] - py[i] + 1e-9) + px[i])
            inside ^= cond
            j = i
        rib = np.exp(-(x / 0.03) ** 2) * 0.25
        shade = 0.85 + 0.15 * v
        r = (0.17 + rib * 0.3) * shade
        g = (0.44 + rib * 0.3) * shade
        b = (0.16 + rib * 0.2) * shade
        a = inside.astype(np.float32)
        return r, g, b, a
    im = _image_from(name + "_img", 128, fn)
    m, nt, b = M._new(name)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    gt = nt.nodes.new("ShaderNodeMath")          # alpha > 0.5: the glTF exporter writes alphaMode MASK (not BLEND)
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    nt.links.new(t.outputs["Alpha"], gt.inputs[0])
    nt.links.new(gt.outputs[0], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.5
    m.blend_method = "CLIP"
    m.alpha_threshold = 0.5
    m.use_backface_culling = False
    return m


def _peg_tile_material(name):
    """One 40 x 40 mm SKADIS cell as a repeating tile: white with the slot (5 x 15) in the glow's colour, for the
    lite board (its UVs repeat 19 x 14)."""
    import numpy as np
    from lib import materials as M
    tint = M.srgb(PEG_GLOW_TINT)

    def fn(u, v):
        sx, sy = PEG_SLOT[0] / PEG_PITCH / 2, PEG_SLOT[1] / PEG_PITCH / 2
        dx, dy = np.abs(u - 0.5), np.abs(v - 0.5)
        r = sx
        core = (dx < r) & (dy < sy - r)
        cap = np.sqrt(dx ** 2 + (dy - (sy - r)) ** 2) < r
        slot = (core | cap).astype(np.float32)
        base = np.array([0.957, 0.957, 0.949])
        out = []
        for c in range(3):
            out.append(base[c] * (1 - slot) + tint[c] * 0.85 * slot)
        out.append(np.ones_like(u))
        return out
    im = _image_from(name + "_img", 96, fn)
    m, nt, b = M._new(name)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    t.extension = "REPEAT"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    return m


# ---------------------------------------------------------------------------
# 3. mesh helpers (bmesh, metres)
# ---------------------------------------------------------------------------
def V(x, y, z):
    return Vector((x * MM, y * MM, z * MM))


def obj_from_bm(name, bm, mat, coll, parent=None, smooth=False, auto=None):
    bm.normal_update()
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    if mat is not None:
        me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    if smooth and auto:
        try:
            mod = ob.modifiers.new("smooth", "SMOOTH_BY_ANGLE")
            mod["Input_1"] = math.radians(auto)
        except Exception:
            pass
    return ob


def empty(name, coll, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.location = loc
    coll.objects.link(e)
    if parent is not None:
        e.parent = parent
    return e


def box_bm(bm, w, d, h, at=(0, 0, 0), z0=0.0):
    """A w x d x h box centred in x and y at `at`, z from z0 (mm)."""
    x, y, z = at
    vs = [bm.verts.new(V(x + sx * w / 2, y + sy * d / 2, z + z0 + zz)) for zz in (0, h) for sy in (-1, 1) for sx in (-1, 1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (1, 5, 7, 3), (3, 7, 6, 2), (2, 6, 4, 0)]
    for a in f:
        bm.faces.new([vs[i] for i in a])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def sweep(bm, path, section, up=None, closed_path=False, cap=True, loop=True):
    """Sweep a closed 2D section (list of (u, v) in mm) along a 3D path (list of Vector, metres). The section's
    u axis follows the path's normal (perpendicular to the tangent and `up`), v follows `up` projected.
    Returns the rings of verts."""
    n = len(path)
    rings = []
    upv = Vector(up) if up is not None else Vector((0, 0, 1))
    for i, p in enumerate(path):
        if closed_path:
            t = (path[(i + 1) % n] - path[i - 1]).normalized()
        elif i == 0:
            t = (path[1] - path[0]).normalized()
        elif i == n - 1:
            t = (path[-1] - path[-2]).normalized()
        else:
            t = (path[i + 1] - path[i - 1]).normalized()
        u_ax = t.cross(upv)
        if u_ax.length < 1e-6:
            u_ax = t.cross(Vector((1, 0, 0)))
        u_ax.normalize()
        v_ax = u_ax.cross(t).normalized()
        rings.append([bm.verts.new(p + u_ax * (a * MM) + v_ax * (b * MM)) for a, b in section])
    m = len(section)
    for i in range(n if closed_path else n - 1):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for j in range(m if loop else m - 1):
            bm.faces.new((r0[j], r1[j], r1[(j + 1) % m], r0[(j + 1) % m]))
    if cap and not closed_path and loop:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return rings


def circle(r, n, phase=0.0):
    return [(r * math.cos(2 * math.pi * i / n + phase), r * math.sin(2 * math.pi * i / n + phase)) for i in range(n)]


def rrect2(w, h, r, n=3):
    """A rounded rectangle outline (mm), centred, counter-clockwise."""
    out = []
    r = min(r, w / 2, h / 2)
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def extrude_outline(bm, outline, y0, y1, holes=None):
    """A flat outline in the XZ plane (mm (x, z)), extruded from y0 to y1 (mm): a slab with its front at the
    smaller y. Holes (list of outlines) are cut with a boolean later, not here."""
    front = [bm.verts.new(V(x, y0, z)) for x, z in outline]
    back = [bm.verts.new(V(x, y1, z)) for x, z in outline]
    n = len(outline)
    bm.faces.new(front)            # outline counter-clockwise seen from -Y (x right, z up): normal points -Y
    bm.faces.new(list(reversed(back)))
    for i in range(n):
        bm.faces.new((front[(i + 1) % n], front[i], back[i], back[(i + 1) % n]))
    return front, back


def fix_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def lathe(bm, profile, axis="X", seg=32, scale_v=1.0):
    """Revolve a profile [(r, a)] (radius, position along the axis, mm) around the given axis through the origin.
    scale_v squashes the revolve in the second cross axis (an oval cup)."""
    rings = []
    for r, a in profile:
        ring = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            c, s = r * math.cos(t), r * math.sin(t) * scale_v
            if axis == "X":
                p = (a, c, s)
            elif axis == "Z":
                p = (c, s, a)
            else:
                p = (c, a, s)
            ring.append(bm.verts.new(V(*p)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for j in range(seg):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % seg], rings[i + 1][(j + 1) % seg], rings[i + 1][j]))
    return rings


def cap_ring(bm, ring, flip=False):
    bm.faces.new(list(reversed(ring)) if flip else ring)


def boolean_cut(target, cutter, apply=True):
    mod = target.modifiers.new("cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    mod.solver = "EXACT"
    if apply:
        with bpy.context.temp_override(object=target, active_object=target, selected_objects=[target]):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
        me = target.data                  # the cutter's empty material slot comes along: fold its faces into slot 0
        if any(m is None for m in me.materials) and len(me.materials) > 1:
            for p in me.polygons:
                p.material_index = 0
            for i in reversed(range(len(me.materials))):
                if me.materials[i] is None:
                    me.materials.pop(index=i)


def set_uv_rect(ob, u0=0.0, v0=0.0, u1=1.0, v1=1.0, axes=("x", "z")):
    """A clean planar UV on a flat face set: the face's bbox maps to (u0,v0)..(u1,v1); x right, z up."""
    me = ob.data
    lay = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    ax = {"x": 0, "y": 1, "z": 2}
    i0, i1 = ax[axes[0]], ax[axes[1]]
    xs = [v.co[i0] for v in me.vertices]
    zs = [v.co[i1] for v in me.vertices]
    a0, a1, b0, b1 = min(xs), max(xs), min(zs), max(zs)
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            lay.data[li].uv = (u0 + (u1 - u0) * (co[i0] - a0) / max(a1 - a0, 1e-9),
                               v0 + (v1 - v0) * (co[i1] - b0) / max(b1 - b0, 1e-9))


def tri_count(obs):
    obs = {o.name: o for o in obs}.values()          # a part's name lists repeat some objects (headphones)
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs if o.type == "MESH")


# ---------------------------------------------------------------------------
# 4. the parts
# ---------------------------------------------------------------------------
def build_shelf(coll, mp, lite=False, rough=False, sfx=""):
    """The floating shelf and the three frames. Returns {shelf: [...], frame_1: [...], ...}."""
    names = {}
    root = empty("shelf_root" + sfx, coll)
    bm = bmesh.new()
    box_bm(bm, SHELF_L, SHELF_D, SHELF_T, (0, 0, 0))
    ob = obj_from_bm("shelf" + sfx, bm, mp["white"], coll, root)
    if not lite and not rough:
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments = 0.0025, 3
    names["shelf"] = [ob.name]
    for i, dx in enumerate(FRAME_DX):
        fr = empty(f"frame_{i + 1}_root{sfx}", coll, root, (dx * MM, (SHELF_D / 2 - FRAME_WALL) * MM, SHELF_T * MM))
        names[f"frame_{i + 1}"] = build_frame(coll, mp, fr, i + 1, lite, rough, sfx)
    names["all"] = [n for k, v in names.items() for n in v]
    names["roots"] = [root.name]
    return names


def build_frame(coll, mp, parent, k, lite, rough, sfx):
    """One black 30 x 40 frame: origin at its bottom back edge, leaning back FRAME_LEAN; the mount is the picture
    face with a clean 0..1 UV (top-left at (0, 1))."""
    out = []
    lean = Matrix.Rotation(math.radians(-FRAME_LEAN), 4, "X")   # top goes toward +Y (the wall)
    bm = bmesh.new()
    outer = rrect2(FRAME_W, FRAME_H, 1.5 if not lite else 0.1, 2)
    outer = [(x, z + FRAME_H / 2) for x, z in outer]
    extrude_outline(bm, outer, -FRAME_T, 0.0)
    fix_normals(bm)
    frame = obj_from_bm(f"frame_{k}{sfx}", bm, mp["black"], coll, parent)
    # the window through the face: cut the picture opening into the front FRAME_LIP, then the mount closes it
    bm = bmesh.new()
    box_bm(bm, PICTURE[0], FRAME_LIP + 2, PICTURE[1], (0, -FRAME_T - 1 + (FRAME_LIP + 2) / 2, 0), FRAME_MOULD)
    fix_normals(bm)
    cutter = obj_from_bm(f"frame_{k}_cut{sfx}", bm, None, coll, parent)
    boolean_cut(frame, cutter)
    frame.matrix_basis = lean
    out.append(frame.name)
    # the mount: a plane just behind the lip, the picture face
    bm = bmesh.new()
    y = -FRAME_T + FRAME_LIP
    pw, ph = PICTURE
    vs = [bm.verts.new(V(x, y, z)) for x, z in ((-pw / 2, FRAME_MOULD), (pw / 2, FRAME_MOULD),
                                               (pw / 2, FRAME_MOULD + ph), (-pw / 2, FRAME_MOULD + ph))]
    bm.faces.new(vs)
    pic = obj_from_bm(f"frame_{k}_picture{sfx}", bm, mp["mount"], coll, parent)
    set_uv_rect(pic)
    pic.matrix_basis = lean
    out.append(pic.name)
    if not lite and not rough:
        bm = bmesh.new()
        vs = [bm.verts.new(V(x, -FRAME_T + 1.0, z)) for x, z in ((-pw / 2, FRAME_MOULD), (pw / 2, FRAME_MOULD),
                                                                (pw / 2, FRAME_MOULD + ph), (-pw / 2, FRAME_MOULD + ph))]
        bm.faces.new(vs)
        gl = obj_from_bm(f"frame_{k}_glass{sfx}", bm, mp["glass"], coll, parent)
        gl.matrix_basis = lean
        out.append(gl.name)
        # round 2: the easel leg is cut; the frame leans on the wall, and the leg went 4 cm into it in the room test
    return out


VINE_END_ONLY = {1}          # round 2: pot 1 (the corner end, beside key light 1 in plan v3) sends every vine over the
#                              shelf's end, close to the wall, so none hangs through the key light's panel


def vine_path(rng, end_side, i, n, lite, end_only=False):
    """One vine's centre line (metres): from the pot rim, over the shelf's front edge or end, then hanging."""
    # which way: most over the front (-Y), a few over the end (all of them for an `end_only` pot)
    over_end = end_only or i % 3 == 2
    ang = rng.uniform(-0.6, 0.6) + (math.pi / 2 * end_side if over_end else -math.pi / 2)
    r0 = POT_D / 2 - 8
    p0 = Vector((r0 * math.cos(ang), r0 * math.sin(ang), POT_H - 6))
    if over_end:
        edge = Vector((end_side * (POT_END_X + rng.uniform(5, 25)),
                       rng.uniform(-10, 35) if end_only else rng.uniform(-40, 40), -2))
    else:
        edge = Vector((rng.uniform(-70, 70), SHELF_FRONT_Y - rng.uniform(5, 25), -2))
    length = VINE_LEN * rng.uniform(0.55, 1.0)
    pts = []
    steps = 6 if lite else 12
    # rise a little over the rim then out to the edge
    for k in range(steps + 1):
        t = k / steps
        p = p0.lerp(edge, t)
        p.z = p0.z + 25 * math.sin(math.pi * t) * (1 - t) - (p0.z - edge.z) * t ** 1.6
        pts.append(p)
    drop = 8 if lite else 16
    sway = rng.uniform(10, 30)
    ph = rng.uniform(0, 6)
    for k in range(1, drop + 1):
        t = k / drop
        p = edge.copy()
        p.z = edge.z - length * t
        d = Vector((math.cos(ang), math.sin(ang), 0)) if over_end else Vector((0, -1, 0))
        p += d * (18 * t ** 0.5)
        p.x += sway * math.sin(ph + t * 4.5) * t
        p.y += sway * 0.5 * math.cos(ph + t * 3.2) * t
        pts.append(p)
    return [V(p.x, p.y, p.z) for p in pts]


def leaf_mesh(bm, at, dirv, size, lite, droop=0.6, twist=0.0):
    """A pothos leaf (mm size) at `at` pointing `dirv`, hanging down with droop. Rich: a small heart-shaped mesh
    with a midrib fold; lite: a quad card (the alpha texture draws the shape)."""
    d = Vector(dirv).normalized()
    up = Vector((0, 0, 1))
    side = d.cross(up)
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize()
    rot = Matrix.Rotation(twist, 4, d)
    side = rot @ side
    nrm = side.cross(d).normalized()
    if lite:
        pts2 = [(-0.5, 0), (0.5, 0), (0.5, 1), (-0.5, 1)]
        vs = []
        for u, v in pts2:
            p = Vector(at) + d * (v * size * MM) + side * (u * size * MM) + up * (-droop * v * v * size * MM)
            vs.append(bm.verts.new(p))
        f = bm.faces.new(vs)
        return [f], pts2
    n = 14
    outline = [leaf_shape(i / n) for i in range(n)]
    centre = bm.verts.new(Vector(at) + d * (0.5 * size * MM) - up * (droop * 0.25 * size * MM) + nrm * (2 * MM))
    ring = []
    for u, v in outline:
        p = Vector(at) + d * (v * size * MM) + side * (u * size * MM) - up * (droop * v * v * size * MM) + nrm * (abs(u) * 0.12 * size * MM)
        ring.append(bm.verts.new(p))
    faces = []
    for i in range(n):
        faces.append(bm.faces.new((centre, ring[i], ring[(i + 1) % n])))
    return faces, None


def build_plants(coll, mp, lite=False, rough=False, sfx=""):
    names = {"all": [], "roots": []}
    for k, end_side in ((1, -1), (2, 1)):
        root = empty(f"vine_pot_{k}_root{sfx}", coll)
        names["roots"].append(root.name)
        # the pot: a tapered white cylinder with a rim and a soil disc
        bm = bmesh.new()
        seg = 16 if lite else 48
        r = POT_D / 2
        prof = [(0, 0), (r * 0.78, 0), (r * 0.80, 2), (r * 0.98, POT_H - 8), (r, POT_H - 4), (r, POT_H),
                (r - 4, POT_H), (r - 4, POT_H - 10)]
        if lite:
            prof = [(0, 0), (r * 0.78, 0), (r, POT_H - 4), (r, POT_H), (r - 4, POT_H - 10)]
        rings = lathe(bm, prof, "Z", seg)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        pot = obj_from_bm(f"vine_pot_{k}{sfx}", bm, mp["white"], coll, root, smooth=True, auto=40)
        # soil
        bm = bmesh.new()
        ring = [bm.verts.new(V((r - 4) * math.cos(2 * math.pi * i / seg), (r - 4) * math.sin(2 * math.pi * i / seg), POT_H - 10))
                for i in range(seg)]
        bm.faces.new(ring)
        soil = obj_from_bm(f"vine_pot_{k}_soil{sfx}", bm, mp["soil"], coll, root)
        names[f"vine_pot_{k}"] = [pot.name, soil.name]
        if rough:
            names["all"] += names[f"vine_pot_{k}"]
            continue
        # the vines: stems swept along the paths, leaves along them
        rng = random.Random(100 + k)
        n_v = 4 if lite else 7
        bm_s = bmesh.new()
        bm_l = bmesh.new()
        for i in range(n_v):
            path = vine_path(rng, end_side, i, n_v, lite, end_only=k in VINE_END_ONLY)
            sweep(bm_s, path, circle(2.2 if not lite else 2.5, 4 if lite else 7), up=(0, 0, 1), cap=True)
            # leaves every few points after the rim, alternating sides, bigger near the top
            start = 3 if lite else 5
            step = 2 if lite else 2
            for j in range(start, len(path) - 1, step):
                p = path[j]
                t = (path[j + 1] - path[j - 1]).normalized()
                sgn = 1 if (j // step) % 2 == 0 else -1
                side = t.cross(Vector((0, 0, 1)))
                if side.length < 1e-4:
                    side = Vector((1, 0, 0))
                side.normalize()
                d = (side * sgn * 0.8 + t * 0.35 + Vector((0, 0, -0.45))).normalized()
                size = rng.uniform(55, 85) if not lite else rng.uniform(60, 90)
                leaf_mesh(bm_l, p, d, size, lite, droop=rng.uniform(0.3, 0.7), twist=rng.uniform(-0.5, 0.5))
        stems = obj_from_bm(f"vine_{k}_stems{sfx}", bm_s, mp["stem"], coll, root, smooth=True)
        leaves = obj_from_bm(f"vine_{k}{sfx}", bm_l, mp["leaf_card"] if lite else mp["leaf"], coll, root, smooth=not lite)
        if lite:
            lay = leaves.data.uv_layers.new(name="UVMap")
            for poly in leaves.data.polygons:
                for n_i, li in enumerate(poly.loop_indices):
                    lay.data[li].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][n_i]
        names[f"vine_{k}"] = [leaves.name, stems.name]
        names["all"] += names[f"vine_pot_{k}"] + names[f"vine_{k}"]
    return names


def slot_outline(cx, cz, lite=False):
    w, h = PEG_SLOT
    return [(cx + x, cz + z) for x, z in rrect2(w, h, w / 2, 1 if lite else 3)]


def build_pegboard(coll, mp, lite=False, rough=False, sfx=""):
    names = {}
    root = empty("pegboard_root" + sfx, coll)
    names["roots"] = [root.name]
    bm = bmesh.new()
    outer = rrect2(PEG_W, PEG_H, PEG_R, 1 if lite else 4)
    extrude_outline(bm, outer, -PEG_T / 2, PEG_T / 2)
    fix_normals(bm)
    board = obj_from_bm("pegboard" + sfx, bm, mp["peg_tile"] if lite else mp["white"], coll, root)
    x0 = -PEG_W / 2 + PEG_FIRST_X
    z_top = PEG_H / 2 - 10                    # the top row sits open at the edge (half slots); EST
    if lite:
        # UVs: the front and back faces repeat the tile 19 x 14, the edges map to the white corner of a cell
        me = board.data
        lay = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            flat = abs(poly.normal.y) > 0.9
            for li in poly.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                if flat:
                    lay.data[li].uv = ((co.x / MM - x0) / PEG_PITCH + 0.5, (co.z / MM - (z_top - (PEG_ROWS - 1) * PEG_PITCH)) / PEG_PITCH + 0.5)
                else:
                    lay.data[li].uv = (0.02, 0.02)
    elif not rough:
        cb = bmesh.new()
        for c in range(PEG_COLS):
            for r in range(PEG_ROWS):
                cx = x0 + c * PEG_PITCH
                cz = z_top - r * PEG_PITCH
                sl = slot_outline(cx, cz + (6 if r == 0 else 0))
                extrude_outline(cb, sl, -PEG_T, PEG_T)
        fix_normals(cb)
        cutter = obj_from_bm("pegboard_cut" + sfx, cb, None, coll, root)
        boolean_cut(board, cutter)
    names["pegboard"] = [board.name]
    # spacers and screws at the four corners: a white tube to the wall, a screw cap in front
    extra = []
    if not rough:
        for sx in (-1, 1):
            for sz in (-1, 1):
                x = sx * (PEG_W / 2 - PEG_SCREW[0])
                z = sz * (PEG_H / 2 - PEG_SCREW[1])
                bm = bmesh.new()
                seg = 8 if lite else 20
                path = [V(x, PEG_T / 2, z), V(x, PEG_OFF, z)]
                sweep(bm, path, circle(7, seg), up=(0, 0, 1))
                extra.append(obj_from_bm(f"pegboard_spacer_{sx}{sz}{sfx}".replace("-", "m"), bm, mp["white"], coll, root, smooth=True).name)
                bm = bmesh.new()
                path = [V(x, -PEG_T / 2 - 2.5, z), V(x, -PEG_T / 2, z)]
                sweep(bm, path, circle(5.5, seg), up=(0, 0, 1))
                extra.append(obj_from_bm(f"pegboard_cap_{sx}{sz}{sfx}".replace("-", "m"), bm, mp["white"], coll, root, smooth=True).name)
    # the glow card on the wall behind the board
    bm = bmesh.new()
    gw, gh = PEG_W + 2 * PEG_HALO, PEG_H + 2 * PEG_HALO
    vs = [bm.verts.new(V(x, PEG_OFF - 1.5, z)) for x, z in ((-gw / 2, -gh / 2), (gw / 2, -gh / 2), (gw / 2, gh / 2), (-gw / 2, gh / 2))]
    bm.faces.new(vs)
    glow = obj_from_bm("pegboard_glow" + sfx, bm, mp["peg_glow"], coll, root)
    set_uv_rect(glow)
    names["pegboard_glow"] = [glow.name]
    # the hook, at the slot the headphones hang from: column 5 from the left, row 1 (EST from the owner's photo)
    hook_x = x0 + HOOK_COL * PEG_PITCH
    hook_z = z_top - HOOK_ROW * PEG_PITCH
    hook = build_hook(coll, mp, root, hook_x, hook_z, lite, rough, sfx)
    names["pegboard_hook"] = hook
    names["pegboard"] += extra
    hp_root = empty("headphones_root" + sfx, coll, root, (hook_x * MM, -(PEG_T / 2 + HOOK_REACH - 12) * MM, (hook_z + 2) * MM))
    names["roots"].append(hp_root.name)
    if not rough:
        names.update(build_headphones(coll, mp, hp_root, lite, sfx))
    else:
        names["headphones"] = []
    names["all"] = [n for k, v in names.items() if k != "roots" for n in v]
    return names


def build_hook(coll, mp, parent, x, z, lite, rough, sfx):
    """A SKADIS single hook: a 5 mm wire that goes into the slot, comes out and up in a shallow J."""
    if rough:
        return []
    bm = bmesh.new()
    r = HOOK_WIRE / 2
    pts = [V(x, PEG_T / 2 + 6, z - 10), V(x, PEG_T / 2 + 6, z + 4), V(x, -PEG_T / 2 - 2, z + 4)]
    # out from the board, a slight droop then the up-turned tip
    n = 4 if lite else 10
    for k in range(1, n + 1):
        t = k / n
        y = -PEG_T / 2 - 2 - (HOOK_REACH - 2) * t
        zz = z + 4 - 6 * t + (12 * (t - 0.75) / 0.25 ** 1 if t > 0.75 else 0) * 0.0
        pts.append(V(x, y, zz))
    tip = pts[-1].copy()
    for k in range(1, (3 if lite else 6) + 1):
        a = math.pi / 2 * k / (3 if lite else 6)
        pts.append(tip + Vector((0, (1 - math.cos(a)) * 6 * MM + 0.0, math.sin(a) * 10 * MM)))
    sweep(bm, pts, circle(r, 6 if lite else 12), up=(1, 0, 0))
    ob = obj_from_bm("pegboard_hook" + sfx, bm, mp["steel"], coll, parent, smooth=True, auto=50)
    return [ob.name]


def band_path(n):
    """The headband's centre line (mm) from the left pivot over the top to the right pivot: a flattened arch."""
    pts = []
    for k in range(n + 1):
        t = -1 + 2 * k / n
        x = HP_BAND_HW * math.sin(t * math.pi / 2)
        z = -HP_BAND_DROP * (1 - math.cos(t * math.pi / 2) ** 0.85)
        pts.append(V(x, 0, z))
    return pts


def build_headphones(coll, mp, root, lite, sfx):
    """ATH-M50x white, hanging: the band's inside top at the origin, the band in the XZ plane, cups facing in."""
    names = {"headphones": [], "headphones_band": [], "headphones_cup_l": [], "headphones_cup_r": [],
             "headphones_brand": []}
    n = 12 if lite else 36
    path = band_path(n)
    # the outer band shell: a rounded rectangle section, wider and thicker at the padded top
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(path):
        t = abs(-1 + 2 * i / n)
        pad = max(0.0, 1 - (t / 0.42) ** 2)          # 1 at the crown, 0 beyond 42% of the way down
        w = HP_BAND_W + (HP_PAD_W - HP_BAND_W) * pad
        th = HP_BAND_T + (HP_PAD_T - HP_BAND_T) * pad
        sec = rrect2(w, th, 4.0 if not lite else 1.0, 2 if not lite else 1)
        rings.append((p, sec, th))
    # sweep by hand: the section lies in the plane perpendicular to the path, u along Y, v along the outward normal
    vr = []
    for i, (p, sec, th) in enumerate(rings):
        if i == 0:
            tg = (path[1] - path[0]).normalized()
        elif i == n:
            tg = (path[-1] - path[-2]).normalized()
        else:
            tg = (path[i + 1] - path[i - 1]).normalized()
        out_n = Vector((0, 1, 0)).cross(tg).normalized()     # outward from the head
        if out_n.z < 0 and abs(p.x) < 0.01:
            out_n = -out_n
        vr.append([bm.verts.new(p + Vector((0, 1, 0)) * (a * MM) + out_n * ((b + th / 2 + 2) * MM)) for a, b in sec])
    m = len(vr[0])
    for i in range(n):
        for j in range(m):
            bm.faces.new((vr[i][j], vr[i + 1][j], vr[i + 1][(j + 1) % m], vr[i][(j + 1) % m]))
    bm.faces.new(list(reversed(vr[0])))
    bm.faces.new(vr[-1])
    fix_normals(bm)
    band = obj_from_bm("headphones_band" + sfx, bm, mp["hp_white"], coll, root, smooth=True, auto=45)
    names["headphones_band"].append(band.name)
    # the underside pad (the padded top third, protein leather), a slimmer sweep under the shell
    if not lite:
        bm = bmesh.new()
        sub = [p for i, p in enumerate(path) if abs(-1 + 2 * i / n) < 0.45]
        sweep(bm, sub, rrect2(HP_BAND_W - 2, 7, 3, 2), up=(0, 1, 0))
        pad = obj_from_bm("headphones_pad" + sfx, bm, mp["hp_pad"], coll, root, smooth=True, auto=45)
        names["headphones_band"].append(pad.name)
    for side, key in ((-1, "l"), (1, "r")):
        names[f"headphones_cup_{key}"] += build_cup(coll, mp, root, side, key, lite, sfx)
    # the slider arms: flat bars from the band's ends down to the yokes
    for side in (-1, 1):
        bm = bmesh.new()
        x = side * HP_BAND_HW
        p0 = V(x, 0, -HP_BAND_DROP)
        p1 = V(side * (CUP_CX + HP_CUP[2] * 0.62), 0, HP_CUP_Z + HP_CUP[0] / 2 + 5 + 14)
        sweep(bm, [p0, p1], rrect2(HP_SLIDER_T, HP_SLIDER_W, 1.5, 1), up=(0, 1, 0))
        sl = obj_from_bm(f"headphones_slider_{'l' if side < 0 else 'r'}{sfx}", bm, mp["hp_silver"], coll, root, smooth=True, auto=45)
        names["headphones"].append(sl.name)
    # the brand: the small wordmark on each cup's disc (where the real text sits, white-on-white print)
    if not lite or True:
        from lib import brands
        for side, key in ((-1, "l"), (1, "r")):
            # round 2: in the centre of the cup's outer disc, inside the silver ring, embossed tone-on-tone (the real
            # audio-technica mark sits there, a slightly glossier white on the matte white disc)
            at = (side * (CUP_CX + HP_CUP[2] + 1.2) * MM, 0.0, HP_CUP_Z * MM)
            d = brands.decal("headphones", at, (side, 0, 0), (0, 0, 1), height=HP_LOGO[1] * MM, finish="embossed",
                             colour="#d0d0ce", parent=root, collection=coll, lite=lite,
                             name=f"headphones_brand_{key}{sfx}", max_width=HP_LOGO[0] * MM)
            if d is not None:
                names["headphones_brand"].append(d.name)
    names["headphones"] = names["headphones"] + names["headphones_band"] + names["headphones_cup_l"] + names["headphones_cup_r"] + names["headphones_brand"]
    return names


def build_cup(coll, mp, root, side, key, lite, sfx):
    """One ear cup facing inward (+X for the left cup at -X): the oval shell with a domed back and logo disc, the
    silver ring, the thick pad ring, and the yoke over its top half."""
    out = []
    h, w, d = HP_CUP
    cx = side * CUP_CX
    cz = HP_CUP_Z
    seg = 16 if lite else 48
    sv = w / h
    # shell: a lathe along X (the cup axis) from the pad face (inner, x toward the centre) to the domed back
    rr = h / 2
    # a shallow shell: straight sides, a soft shoulder, then the wide flat back with the raised disc
    prof = [(rr - 1, 0), (rr, 3), (rr, d - 16), (rr - 3, d - 9), (rr - 9, d - 3.5), (rr - 16, d - 1), (HP_DISC / 2 + 5, d - 0.5),
            (HP_DISC / 2 + 3, d + 0.6), (HP_DISC / 2, d + 1.2), (0, d + 1.2)]
    if lite:
        prof = [(rr - 1, 0), (rr, 3), (rr, d - 14), (rr - 8, d - 3), (HP_DISC / 2 + 3, d + 0.6), (0, d + 1.2)]
    bm = bmesh.new()
    rings = lathe(bm, [(r, -a) for r, a in prof], "X", seg, sv)       # the back at -X, the pad face at 0: the left cup
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    cap_ring(bm, rings[0], flip=True)
    fix_normals(bm)
    bm.transform(Matrix.Translation((cx * MM, 0, cz * MM)) @ Matrix.Scale(-side, 4, (1, 0, 0)))   # mirrored for the right
    if side > 0:
        for f in bm.faces:
            f.normal_flip()
    shell = obj_from_bm(f"headphones_cup_{key}{sfx}", bm, mp["hp_white"], coll, root, smooth=True, auto=40)
    out.append(shell.name)
    # the pad ring: an oval torus on the inner face
    bm = bmesh.new()
    pt, pw_ = HP_PAD_RING
    ring_prof = []
    nseg = 6 if lite else 14
    for k in range(nseg + 1):
        a = math.pi * k / nseg
        ring_prof.append((rr - pw_ / 2 + (pw_ / 2) * math.cos(a), pt * math.sin(a) ** 0.8 if k > 0 else 0))
    ring_prof.append((rr - pw_, 0))
    rings = lathe(bm, [(r, a) for r, a in ring_prof], "X", seg, sv)
    bm.transform(Matrix.Translation((cx * MM, 0, cz * MM)) @ Matrix.Scale(-side, 4, (1, 0, 0)))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    fix_normals(bm)
    pad = obj_from_bm(f"headphones_pad_{key}{sfx}", bm, mp["hp_pad"], coll, root, smooth=True, auto=40)
    out.append(pad.name)
    # the silver ring around the disc, on the back
    if not lite:
        bm = bmesh.new()
        prof = [(HP_DISC / 2 + 0.5, -(d + 2.2)), (HP_DISC / 2 + 2.5, -(d + 1.0)), (HP_DISC / 2 + 2.5, -(d - 1))]
        lathe(bm, prof, "X", seg)
        bm.transform(Matrix.Translation((cx * MM, 0, cz * MM)) @ Matrix.Scale(-side, 4, (1, 0, 0)))
        fix_normals(bm)
        out.append(obj_from_bm(f"headphones_ring_{key}{sfx}", bm, mp["hp_silver"], coll, root, smooth=True).name)
    # the yoke: a rounded bar over the cup's top half in the cup's plane, 10 mm off the shell's rim, ending at the
    # pivots at 9 and 3 o'clock; plus the two pivot bosses
    bm = bmesh.new()
    yr = rr + 5
    yx = cx + side * (d * 0.62)                       # the yoke sits over the back half of the rim
    pts = []
    ny = 8 if lite else 20
    for k in range(ny + 1):
        a = math.pi * k / ny                           # from +Y (front pivot) over the top to -Y (back pivot)
        pts.append(V(yx, yr * sv * math.cos(a), cz + yr * math.sin(a)))
    sweep(bm, pts, rrect2(HP_YOKE[1], HP_YOKE[0], 2.5 if not lite else 0.5, 2 if not lite else 1), up=(side, 0, 0))
    fix_normals(bm)
    out.append(obj_from_bm(f"headphones_yoke_{key}{sfx}", bm, mp["hp_white"], coll, root, smooth=True, auto=40).name)
    for sy in (-1, 1):
        bm = bmesh.new()
        p0 = V(yx, sy * (rr * sv - 2), cz)
        p1 = V(yx, sy * (rr * sv + 8), cz)
        sweep(bm, [p0, p1], circle(8, 8 if lite else 16), up=(0, 0, 1))
        out.append(obj_from_bm(f"headphones_pivot_{key}{'f' if sy < 0 else 'b'}{sfx}", bm, mp["hp_white"], coll, root, smooth=True, auto=40).name)
    # the hinge block joining the yoke's crown to the slider
    bm = bmesh.new()
    box_bm(bm, 16, 20, 18, (yx, 0, cz + yr + 2), -4)
    out.append(obj_from_bm(f"headphones_hinge_{key}{sfx}", bm, mp["hp_white"], coll, root).name)
    return out


def neon_text():
    with open(CONTENT) as f:
        return json.load(f)["neon"]["text"]


def _trace_skeleton(sk):
    """Plain Python: a one-pixel skeleton (bool array) to polylines of (row, col): the runs between end points and
    junctions, then the pure loops. Returns [(points, closed)]."""
    import numpy as np
    pts = set(zip(*[a.tolist() for a in np.nonzero(sk)]))
    off = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def nb(p):
        return [(p[0] + dr, p[1] + dc) for dr, dc in off if (p[0] + dr, p[1] + dc) in pts]
    deg = {p: len(nb(p)) for p in pts}
    nodes = {p for p in pts if deg[p] != 2}
    used = set()
    out = []
    for n in nodes:
        for q in nb(n):
            if (n, q) in used:
                continue
            path = [n, q]
            used.update({(n, q), (q, n)})
            prev, cur = n, q
            while cur not in nodes:
                nx = [x for x in nb(cur) if x != prev and (cur, x) not in used]
                if not nx:
                    break
                nxt = nx[0]
                used.update({(cur, nxt), (nxt, cur)})
                path.append(nxt)
                prev, cur = cur, nxt
            out.append((path, False))
    for p in pts:                                  # a lone pixel (a small dot's skeleton): a 2-pixel stroke
        if deg[p] == 0:
            out.append(([(p[0] + 1, p[1]), (p[0] - 1, p[1])], False))
    seen = {p for e in used for p in e}
    for p0 in pts:
        if p0 in seen or deg[p0] != 2:
            continue
        path = [p0]
        seen.add(p0)
        cur = p0
        while True:
            nx = [x for x in nb(cur) if x not in seen]
            if not nx:
                break
            cur = nx[0]
            seen.add(cur)
            path.append(cur)
        if len(path) > 8:
            out.append((path, True))
    return out


def neon_raster(spec_path, out_dir):
    """Plain Python (PIL, numpy, scipy, skimage). Round 2: real LED neon is ONE round tube per stroke, so the words
    (from content, in the rounded font) are drawn, skeletonised to their centre lines (the medial axis), traced into
    single-stroke polylines (short spurs pruned, smoothed, resampled) and written as neon_strokes.json in mm about
    the plate's centre (x right, z up); the rich and lite tubes are swept along them in Blender. neon_halo.png is
    the soft glow around the tubes (white, alpha) for a card on the plate; neon_glyphs.png a preview of the tubes.
    Any words work: nothing here knows the letters."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from scipy import ndimage
    from skimage.morphology import skeletonize
    spec = json.load(open(spec_path))
    text, w_mm, h_mm, tube_mm, ppm = spec["text"], spec["w_mm"], spec["h_mm"], spec["tube_mm"], spec["ppm"]
    W, H = int(round(w_mm * ppm)), int(round(h_mm * ppm))
    target_w = 0.80 * W
    size = 200
    font = ImageFont.truetype(spec["font"], size)
    bb = font.getbbox(text)
    size = int(size * target_w / max(bb[2] - bb[0], 1))
    font = ImageFont.truetype(spec["font"], size)
    bb = font.getbbox(text)
    if (bb[3] - bb[1]) > 0.66 * H:
        size = int(size * 0.66 * H / (bb[3] - bb[1]))
        font = ImageFont.truetype(spec["font"], size)
        bb = font.getbbox(text)
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).text(((W - (bb[2] - bb[0])) / 2 - bb[0], (H - (bb[3] - bb[1])) / 2 - bb[1]), text, font=font, fill=255)
    ink = ndimage.gaussian_filter(np.array(im).astype(np.float32), 1.5) > 127
    edt = ndimage.distance_transform_edt(ink)
    half = float(np.percentile(edt[ink], 96))                  # the stroke's half-width in px (a monoline font)
    sk = skeletonize(ink)
    polys = _trace_skeleton(sk)
    # prune spurs: a run from a free end shorter than 1.6 half-widths is a corner whisker, not a stroke
    deg_end = {}
    for pts, closed in polys:
        if not closed:
            for e in (pts[0], pts[-1]):
                deg_end[e] = deg_end.get(e, 0) + 1
    keep = []
    for pts, closed in polys:
        free = (deg_end[pts[0]] == 1) + (deg_end[pts[-1]] == 1) if not closed else 0
        if free == 1 and len(pts) < 1.6 * half:     # a whisker off a stroke (an isolated short run is a dot: kept)
            continue
        if len(pts) < 2:
            continue
        keep.append((pts, closed))
    strokes = []
    for pts, closed in keep:
        a = np.array(pts, np.float32)
        k = 7                                                  # smooth the pixel staircase (ends held)
        if len(a) > k:
            ker = np.ones(k) / k
            if closed:
                pad = np.concatenate([a[-k:], a, a[:k]])
                sm = np.stack([np.convolve(pad[:, i], ker, "same") for i in range(2)], 1)[k:-k]
            else:
                pad = np.concatenate([np.repeat(a[:1], k, 0), a, np.repeat(a[-1:], k, 0)])
                sm = np.stack([np.convolve(pad[:, i], ker, "same") for i in range(2)], 1)[k:-k]
                sm[0], sm[-1] = a[0], a[-1]
            a = sm
        xy = [(float((c - W / 2) / ppm), float((H / 2 - r) / ppm)) for r, c in a]
        strokes.append(dict(pts=xy, closed=bool(closed)))
    with open(os.path.join(out_dir, "neon_strokes.json"), "w") as f:
        json.dump({"stroke_mm": half * 2 / ppm, "ppm": ppm, "tube_mm": tube_mm, "text": text, "strokes": strokes}, f)
    # the tubes as a mask (preview) and the halo around them
    r = tube_mm / 2 * ppm
    line = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(line)
    for st in strokes:
        q = [(x * ppm + W / 2, H / 2 - z * ppm) for x, z in st["pts"]]
        if st["closed"]:
            q.append(q[0])
        dr.line(q, fill=255, width=1)
    dist = ndimage.distance_transform_edt(np.array(line) < 128)
    tube = dist <= r
    shade = np.sqrt(np.clip(1 - (dist / r) ** 2, 0, 1)) * 0.45 + 0.55
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = (255 * shade)[..., None].astype(np.uint8)
    rgba[..., 3] = (tube * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").resize((1024, int(1024 * H / W)), Image.LANCZOS).save(os.path.join(out_dir, "neon_glyphs.png"))
    halo = np.exp(-np.maximum(dist - r, 0) / (7.0 * ppm)) * 0.55
    hr = np.zeros((H, W, 4), np.uint8)
    hr[..., :3] = 255
    hr[..., 3] = (np.clip(halo, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(hr, "RGBA").resize((512, int(512 * H / W)), Image.LANCZOS).save(os.path.join(out_dir, "neon_halo.png"))
    print("NEON", len(strokes), "strokes; stroke", round(half * 2 / ppm, 1), "mm; font px", size, flush=True)


def tube(bm, path, r, seg, closed=False, caps=True, up=(0, 1, 0)):
    """A round tube (radius r mm, seg sides) along `path` (Vectors, metres) that lies in a plane with normal `up`,
    with rounded (half-sphere) ends when open."""
    upv = Vector(up)
    n = len(path)
    pts = [(p, r) for p in path]
    if caps and not closed and n >= 2:
        t0 = (path[0] - path[1]).normalized()
        t1 = (path[-1] - path[-2]).normalized()
        nc = 2 if seg <= 6 else 4
        pre = [(path[0] + t0 * (r * MM * math.sin(math.radians(80) * k / nc)), r * math.cos(math.radians(80) * k / nc))
               for k in range(nc, 0, -1)]
        post = [(path[-1] + t1 * (r * MM * math.sin(math.radians(80) * k / nc)), r * math.cos(math.radians(80) * k / nc))
                for k in range(1, nc + 1)]
        pts = pre + pts + post
    n = len(pts)
    rings = []
    for i, (p, rr) in enumerate(pts):
        if closed:
            t = pts[(i + 1) % n][0] - pts[i - 1][0]
        else:
            t = pts[min(i + 1, n - 1)][0] - pts[max(i - 1, 0)][0]
        if t.length < 1e-9:
            t = Vector((1, 0, 0))
        t.normalize()
        u = t.cross(upv)
        if u.length < 1e-6:
            u = t.cross(Vector((0, 0, 1)))
        u.normalize()
        v = u.cross(t).normalized()
        rings.append([bm.verts.new(p + (u * math.cos(2 * math.pi * j / seg) + v * math.sin(2 * math.pi * j / seg)) * (rr * MM))
                      for j in range(seg)])
    for i in range(n if closed else n - 1):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for j in range(seg):
            bm.faces.new((r0[j], r1[j], r1[(j + 1) % seg], r0[(j + 1) % seg]))
    if not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])


def resample(pts, step, closed=False):
    """A polyline (list of (x, z) mm) resampled every `step` mm (the ends kept)."""
    if closed:
        pts = pts + [pts[0]]
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        acc += d
        if acc >= step:
            out.append(b)
            acc = 0.0
    if closed:
        if math.hypot(out[-1][0] - out[0][0], out[-1][1] - out[0][1]) < step * 0.5:
            out.pop()
    elif out[-1] != pts[-1]:
        if len(out) > 1 and math.hypot(out[-1][0] - pts[-1][0], out[-1][1] - pts[-1][1]) < step * 0.5:
            out[-1] = pts[-1]
        else:
            out.append(pts[-1])
    return out


def _halo_material(name, image_path, strength):
    from lib import materials as M
    im = bpy.data.images.load(image_path, check_existing=False)
    im.name = name + "_img"
    im.pack()
    m, nt, b = M._new(name)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    b.inputs["Base Color"].default_value = M.rgba(NEON_TINT)
    b.inputs["Emission Color"].default_value = M.rgba(NEON_TINT)
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Roughness"].default_value = 1.0
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    m.blend_method = "BLEND"
    m.show_transparent_back = False
    return m


def _neon_card_material(name, image_path, strength):
    from lib import materials as M
    im = bpy.data.images.get(os.path.basename(image_path)) or bpy.data.images.load(image_path)
    im.pack()
    m, nt, b = M._new(name)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Roughness"].default_value = 0.6
    m.blend_method = "CLIP"
    m.alpha_threshold = 0.5
    return m


def build_neon(coll, mp, lite=False, rough=False, sfx=""):
    """White LED neon lettering on a clear acrylic plate: the words from content in Comfortaa Bold, thinned to the
    tube's width on a raster (neon_raster); rich: round tubes swept along the thinned outlines; lite: one emissive
    alpha-tested card of the tubes."""
    import subprocess
    names = {}
    root = empty("neon_root" + sfx, coll)
    names["roots"] = [root.name]
    os.makedirs(FOOT, exist_ok=True)
    spec = os.path.join(FOOT, "neon_spec.json")
    with open(spec, "w") as f:
        json.dump(dict(text=neon_text(), w_mm=NEON_W, h_mm=NEON_H, tube_mm=NEON_TUBE, ppm=NEON_PX_PER_MM,
                       font=os.path.join(FONTS, "Comfortaa-Bold.ttf")), f)
    cj = os.path.join(FOOT, "neon_strokes.json")
    if os.path.exists(cj):
        os.remove(cj)
    pr = subprocess.run(["/opt/anaconda3/bin/python3", os.path.abspath(__file__), "--neon-raster", spec, FOOT],
                        capture_output=True, text=True)
    if not os.path.exists(cj):
        raise RuntimeError("neon raster failed: " + pr.stdout + pr.stderr)
    data = json.load(open(cj))
    y_front = -NEON_PLATE_T / 2 * MM
    r = NEON_TUBE / 2
    bm = bmesh.new()
    step, seg = (9.0, 6) if (lite or rough) else (2.5, 12)
    for st in data["strokes"]:
        pts = resample(st["pts"], step, st["closed"])
        if len(pts) < 2:
            continue
        tube(bm, [V(x, -NEON_PLATE_T / 2 - r - 0.3, z) for x, z in pts], r, seg, closed=st["closed"] and len(pts) > 2)
    glow = obj_from_bm("neon_glow" + sfx, bm, mp["neon_glow"], coll, root, smooth=True)
    # the soft glow on the acrylic around the tubes (an emissive alpha card just in front of the plate)
    bm = bmesh.new()
    vs = [bm.verts.new(V(x, -NEON_PLATE_T / 2 - 0.4, z)) for x, z in ((-NEON_W / 2, -NEON_H / 2), (NEON_W / 2, -NEON_H / 2),
                                                                    (NEON_W / 2, NEON_H / 2), (-NEON_W / 2, NEON_H / 2))]
    bm.faces.new(vs)
    hm = bpy.data.materials.get("mat_wall_neon_halo" + sfx) or _halo_material(
        "mat_wall_neon_halo" + sfx, os.path.join(FOOT, "neon_halo.png"), 1.0 if lite else 2.0)
    halo = obj_from_bm("neon_halo" + sfx, bm, hm, coll, root)
    set_uv_rect(halo)
    names["neon_halo"] = [halo.name]
    names["neon_glow"] = [glow.name]
    # the acrylic plate and four standoffs
    bm = bmesh.new()
    outer = rrect2(NEON_W, NEON_H, 12, 1 if lite else 4)
    extrude_outline(bm, outer, -NEON_PLATE_T / 2, NEON_PLATE_T / 2)
    fix_normals(bm)
    plate = obj_from_bm("neon" + sfx, bm, mp["acrylic"], coll, root)
    names["neon"] = [plate.name]
    if not rough:
        for sx in (-1, 1):
            for sz in (-1, 1):
                x, z = sx * (NEON_W / 2 - 16), sz * (NEON_H / 2 - 16)
                bm = bmesh.new()
                seg = 8 if lite else 20
                sweep(bm, [V(x, NEON_PLATE_T / 2, z), V(x, 10.0, z)], circle(4, seg), up=(0, 0, 1))
                sweep(bm, [V(x, -NEON_PLATE_T / 2 - 3, z), V(x, NEON_PLATE_T / 2 + 0.5, z)], circle(NEON_STANDOFF[0] / 2, seg), up=(0, 0, 1))
                names["neon"].append(obj_from_bm(f"neon_standoff_{sx}{sz}{sfx}".replace("-", "m"), bm, mp["chrome"], coll, root, smooth=True, auto=40).name)
    names["all"] = names["neon"] + names["neon_glow"] + names["neon_halo"]
    return names


ORIENT = {"up": 0.0, "left": 90.0, "down": 180.0, "right": -90.0}


def tri_outline(orient, side=NANO_SIDE, r=NANO_CORNER, n=4):
    """An equilateral triangle outline (mm) with rounded corners, centred on its centroid, its apex pointing
    `orient` (up, down, left or right; True/False mean up/down)."""
    h = side * math.sqrt(3) / 2
    if orient is True:
        orient = "up"
    elif orient is False:
        orient = "down"
    a0 = math.radians(ORIENT[orient])
    ca, sa = math.cos(a0), math.sin(a0)
    corners = [(-y * sa + x * ca, x * sa + y * ca) for x, y in ((0, 2 * h / 3), (-side / 2, -h / 3), (side / 2, -h / 3))]
    # inset the corners by the radius along the bisectors, then arc
    out = []
    inset = r / math.sin(math.radians(30))
    for i, (x, y) in enumerate(corners):
        cxm, cym = sum(c[0] for c in corners) / 3, sum(c[1] for c in corners) / 3
        dx, dy = cxm - x, cym - y
        L = math.hypot(dx, dy)
        cx, cy = x + dx / L * inset, y + dy / L * inset
        a_mid = math.atan2(y - cy, x - cx)
        for k in range(n + 1):
            a = a_mid + math.radians(-60 + 120 * k / n)
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    # make counter-clockwise (x right, z up)
    area = sum(out[i][0] * out[(i + 1) % len(out)][1] - out[(i + 1) % len(out)][0] * out[i][1] for i in range(len(out)))
    if area < 0:
        out.reverse()
    return out


def build_nanoleaf(coll, mp, lite=False, rough=False, sfx=""):
    names = {"nanoleaf": [], "roots": []}
    root = empty("nanoleaf_root" + sfx, coll)
    names["roots"] = [root.name]
    h = NANO_H
    s = NANO_SIDE
    # the sideways lattice (NANO_CELLS): a right-pointing cell in column c has its vertical base at x = c h and its
    # centroid at c h + h/3; a left-pointer's centroid at c h + 2h/3; row k's centroid at z = k s/2 + s/2
    cells = []
    for c, k in NANO_CELLS:
        orient = "right" if (c + k) % 2 == 0 else "left"
        cells.append((c * h + (h / 3 if orient == "right" else 2 * h / 3), k * s / 2 + s / 2, orient))
    xs = [c * h for c, k in NANO_CELLS] + [(c + 1) * h for c, k in NANO_CELLS]
    zs = [k * s / 2 for c, k in NANO_CELLS] + [k * s / 2 + s for c, k in NANO_CELLS]
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    for i, (x, z, up) in enumerate(cells):
        sub = empty(f"nanoleaf_{i + 1:02d}_root{sfx}", coll, root, ((x - cx) * MM, 0, (z - cz) * MM))
        inset = NANO_GAP / 2
        bm = bmesh.new()
        body = tri_outline(up, NANO_SIDE - 2 * inset * math.sqrt(3), NANO_CORNER, 1 if lite else 4)
        extrude_outline(bm, body, -NANO_T, 0.0)
        fix_normals(bm)
        frame = obj_from_bm(f"nanoleaf_frame_{i + 1:02d}{sfx}", bm, mp["white"], coll, sub)
        bm = bmesh.new()
        face = tri_outline(up, NANO_SIDE - 2 * (inset + NANO_FRAME) * math.sqrt(3), max(NANO_CORNER - NANO_FRAME, 3), 1 if lite else 4)
        if lite:
            vs = [bm.verts.new(V(px, -NANO_T - 0.4, pz)) for px, pz in face]
            bm.faces.new(vs)
        else:
            extrude_outline(bm, face, -NANO_T - 0.8, -NANO_T + 1.5)
            fix_normals(bm)
        panel = obj_from_bm(f"nanoleaf_panel_{i + 1:02d}{sfx}", bm, mp["nano_glow"], coll, sub)
        if not lite and not rough:
            # the mounting plate behind: a smaller triangle to the wall
            bm = bmesh.new()
            back = tri_outline(up, NANO_SIDE * 0.5, 6, 2)
            extrude_outline(bm, back, 0.0, NANO_MOUNT - NANO_T)
            fix_normals(bm)
            names["nanoleaf"].append(obj_from_bm(f"nanoleaf_mount_{i + 1:02d}{sfx}", bm, mp["white"], coll, sub).name)
        names["nanoleaf"] += [frame.name, panel.name]
        names[f"nanoleaf_panel_{i + 1:02d}"] = [panel.name]
    names["all"] = list(names["nanoleaf"])
    return names


BUILDERS = {"shelf": build_shelf, "plants": build_plants, "pegboard": build_pegboard, "neon": build_neon,
            "nanoleaf": build_nanoleaf}
# where the parts sit when built together in the studio (metres): spread out on one plane, for the stills
STUDIO_WALL_Y = 0.125                 # the studio wall: the shelf's wall; the other parts move up to it
STUDIO_AT = {"shelf": (0.0, 0.0, 1.95 - 0.04), "plants": (0.0, 0.0, 1.95), "pegboard": (1.35, STUDIO_WALL_Y - 0.04, 1.28),
             "neon": (1.35, STUDIO_WALL_Y - 0.01, 1.28 + 0.28 + 0.11 + 0.13), "nanoleaf": (2.12, STUDIO_WALL_Y - 0.005, 1.50)}
PLANT_STUDIO = [(-0.9 + 0.07, 0.0), (0.9 - 0.07, 0.0)]


def build(parts=None, rough=False, lite=False, collection=None, studio=True):
    """Build the chosen parts into `collection` (default: a new 'wall'). Each part's root empty is at the origin,
    or spread out at STUDIO_AT when `studio`. Returns {part key: [object names], ..., 'all': [...], 'roots': [...]}."""
    parts = parts or PARTS
    sfx = "_lite" if lite else ""
    coll = collection
    if coll is None:
        coll = bpy.data.collections.get("wall") or bpy.data.collections.new("wall")
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
            at = STUDIO_AT[p]
            roots = [bpy.data.objects[r] for r in n["roots"] if bpy.data.objects[r].parent is None]
            for j, r in enumerate(roots):
                if p == "plants":
                    r.location = (at[0] + PLANT_STUDIO[j][0], STUDIO_WALL_Y - 0.11, at[2])
                else:
                    r.location = at
    bpy.context.view_layer.update()
    return names


ROOM_ROOTS = {"shelf": ["shelf_root"], "plants": ["vine_pot_1_root", "vine_pot_2_root"], "pegboard": ["pegboard_root"],
              "neon": ["neon_root"], "nanoleaf": ["nanoleaf_root"]}


def build_room(collection=None, lite=False):
    """The wall group at plan v3's numbers (blender/lib/plan_v3.py) for the room test. plan v3's `at` z is a part's
    bottom; x and y its centre. The shelf and pots turn 90 (the left wall); the rest sit on the back wall at yaw 0.
      shelf      root at plan "shelf" (centre, underside), yaw 90; frame_N moved along the shelf to plan's y
      vine_pot_N root at plan "vine_pot_N" (base centre on the shelf top), yaw 90
      pegboard   board centre at plan x, z bottom + h/2; y so the spacers touch the wall (RY - 0.04)
      neon       plate centre at plan x, y (RY - 0.01), z bottom + 0.13
      nanoleaf   cluster centre at plan x, y (RY - 0.005), z bottom + 0.26 (the footprint's middle)"""
    from lib import plan_v3 as P
    names = build(lite=lite, collection=collection, studio=False)
    sfx = "_lite" if lite else ""
    CP = P.CP

    def put(root, x, y, z, yaw):
        o = bpy.data.objects[root + sfx]
        o.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
    sh = CP["shelf"]["at"]
    put("shelf_root", sh[0], sh[1], sh[2], 90)
    for i in range(3):
        fr = bpy.data.objects[f"frame_{i + 1}_root{sfx}"]
        fr.location.x = CP[f"frame_{i + 1}"]["at"][1] - sh[1]           # local x is world +y after the 90 turn
    for i in range(2):
        a = CP[f"vine_pot_{i + 1}"]["at"]
        put(f"vine_pot_{i + 1}_root", a[0], a[1], a[2], 90)
    put("pegboard_root", P.PEG["x"], P.RY - PEG_OFF * MM, P.PEG["z"] + P.PEG["h"] / 2, 0)
    a = CP["neon"]["at"]
    put("neon_root", a[0], a[1], a[2] + CP["neon"]["size"][2] / 2, 0)
    a = CP["nanoleaf"]["at"]
    put("nanoleaf_root", a[0], a[1], a[2] + CP["nanoleaf"]["size"][2] / 2, 0)
    bpy.context.view_layer.update()
    return names


# ---------------------------------------------------------------------------
# 5. stages
# ---------------------------------------------------------------------------
def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {NAME}: {msg}", flush=True)


def progress(msg):
    os.makedirs(FOOT, exist_ok=True)
    with open(os.path.join(FOOT, "PROGRESS.md"), "a") as f:
        f.write(f"{time.strftime('%H:%M')} [{PART}] {msg}\n")


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for c in list(bpy.data.curves):
        if c.users == 0:
            bpy.data.curves.remove(c)
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")


def photo_objects(names, part):
    """The objects a photo view compares: the headphones alone, the pegboard alone, etc."""
    if part == "headphones":
        return [n for n in names.get("headphones", []) if "brand" not in n]
    if part == "pegboard":
        return names.get("pegboard", [])[:1]
    return names["all"]


def outline_views(names):
    out = []
    have = set(names.get("parts", {}).keys())
    for view, p in PHOTOS.items():
        need = "pegboard" if p["part"] in ("pegboard", "headphones") else p["part"]
        if need not in have:
            continue
        out.append(dict(name=f"{NAME}-{view}", title=p["title"], photo=p["photo"], mask=p.get("mask", 0.93),
                        crop=p.get("crop"), fill=p.get("fill", False), objects=photo_objects(names, p["part"]),
                        camera=dict(p["camera"]), explain=p.get("explain")))
    return out


def stage_outline(out):
    import outline_check
    clear()

    def b(rough=True):
        return build(rough=True)
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
    tris = sum(per.values())
    log(f"built in {time.time() - t:.1f} s, {tris} triangles {per}, saved {blend}")
    progress(f"build: {tris} triangles {per} in {time.time() - t:.1f} s")
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
        try:                      # never set the Metal device in preferences here (Blender 5.2 crash under --factory-startup)
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


def look_cam(name, pos, target, lens=50, ortho=None):
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.005
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


def wall_plane(coll=None):
    """A white wall behind the parts for the stills (the parts sit at y 0 with the wall at +0.04 at most)."""
    from lib import materials as M
    if bpy.data.objects.get("studio_wall"):
        return bpy.data.objects["studio_wall"]
    bm = bmesh.new()
    y = STUDIO_WALL_Y + 0.001
    vs = [bm.verts.new(Vector(p)) for p in ((-1.6, y, 0.4), (3.2, y, 0.4), (3.2, y, 2.8), (-1.6, y, 2.8))]
    bm.faces.new(vs)
    ob = obj_from_bm("studio_wall", bm, M.principled("mat_studio_wall", base="#ececea", rough=0.9), coll or bpy.context.scene.collection)
    return ob


def stage_stills(out, names, cycles=False):
    from lib import backdrops, compare
    sc = bpy.context.scene
    _studio(sc, cycles, 0.6)
    wall_plane()
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    paths = {}
    shots = []
    for p, n in names["parts"].items():
        objs = n["all"]
        lo, hi = compare.world_bbox(objs)
        c, size = (lo + hi) / 2, hi - lo
        shots.append((f"{p}-front", backdrops.view_camera("front", c, max(size.x, size.z * 16 / 9) * 1.15, name=f"still_{p}_front")))
        shots.append((f"{p}-hero", backdrops.three_quarter_camera(c, max(size) * 1.05, az=-30, el=10, name=f"still_{p}_hero")))
    if len(names["parts"]) > 1:
        lo, hi = compare.world_bbox(names["all"])
        c, size = (lo + hi) / 2, hi - lo
        shots.append(("all-front", backdrops.view_camera("front", c, max(size.x, size.z * 16 / 9) * 1.1, name="still_all_front")))
        shots.append(("all-hero", backdrops.three_quarter_camera(c, max(size) * 0.9, az=-28, el=8, name="still_all_hero")))
    keep = os.environ.get("WALL_STILLS")          # e.g. all-front,all-hero (the Cycles finals on battery)
    if keep:
        shots = [(k, c) for k, c in shots if k in keep.split(",")]
    for k, cam in shots:
        p = os.path.join(out, f"{NAME}-{k}.png")
        _shoot(sc, cam, p, cycles, k)
        paths[k] = p
    log(f"stills: {', '.join(paths)}")
    progress(f"stills ({'Cycles' if cycles else 'EEVEE'}): {', '.join(os.path.basename(p) for p in paths.values())}")
    return paths


def closeup_specs(names):
    """(key, title, photo, cam pos, target, lens), in studio coordinates (STUDIO_AT)."""
    S = STUDIO_AT
    specs = []
    if "pegboard" in names["parts"]:
        hp = bpy.data.objects.get("headphones_root")
        hpw = hp.matrix_world.translation if hp else Vector(S["pegboard"])
        cl = hpw + Vector((-CUP_CX * MM, 0, HP_CUP_Z * MM))
        specs += [
            ("hp-cup", "ATH-M50x: an ear cup and the yoke (ours: left cup)", os.path.join(HP_REF, "side-cup-profile.jpg"),
             cl + Vector((-0.26, -0.22, 0.10)), cl + Vector((0, 0, 0.01)), 60),
            ("hp-band", "ATH-M50x: the padded band and the slider", os.path.join(HP_REF, "detail-cup-hinge-top.jpg"),
             hpw + Vector((-0.20, -0.26, 0.08)), hpw + Vector((-0.06, 0, -0.06)), 60),
            ("peg-holes", "SKADIS: the slots and the hook", os.path.join(REF, "05-pegboard", "detail-edge-hole-screw.jpg"),
             hpw + Vector((-0.10, -0.20, 0.12)), hpw + Vector((0.0, 0, 0.0)), 70),
        ]
        c = Vector(S["pegboard"])
        specs.append(("peg-glow", "SKADIS: the backlight's halo on the wall around the board (owner's photo)",
                      os.path.join(FOOT, "ref-owner-photo-wall.png"),
                      c + Vector((-0.75, -1.05, -0.05)), c + Vector((-0.22, 0, -0.08)), 50))
    if "neon" in names["parts"]:
        c = Vector(S["neon"])
        specs.append(("neon-front", "Neon: the single-stroke tubes from the front (owner's photo: Spudd Gaming sign)",
                      os.path.join(FOOT, "ref-owner-photo-wall.png"), c + Vector((0, -1.25, 0)), c, 50))
        specs.append(("neon-tube", "Neon: the tubing and a standoff (ours: the words from content)",
                      os.path.join(REF, "27-neon-and-ledge", "neon-1-feeling-good-led-neon-on-acrylic.jpg"),
                      c + Vector((0.22, -0.26, 0.08)), c + Vector((0.14, 0, 0.02)), 60))
    if "nanoleaf" in names["parts"]:
        c = Vector(S["nanoleaf"])
        specs.append(("nano-cluster", "Nanoleaf: the seven-panel cluster from the front (owner's photo)",
                      os.path.join(FOOT, "ref-owner-photo-wall.png"), c + Vector((0, -1.6, 0)), c, 50))
        specs.append(("nano-edge", "Nanoleaf: a panel's edge and the glow",
                      os.path.join(REF, "20-light-panels", "detail-panel-white-unlit-closeup-crop.jpg"),
                      c + Vector((-0.30, -0.30, 0.12)), c + Vector((-0.08, 0, 0.0)), 60))
    if "shelf" in names["parts"]:
        c = Vector(S["shelf"])
        specs.append(("frame-edge", "A frame's edge and mount on the shelf",
                      os.path.join(REF, "27-neon-and-ledge", "ledge-1-small-wall-ledges-with-framed-photos.jpg"),
                      c + Vector((-0.55, -0.40, 0.30)), c + Vector((-0.38, 0.0, 0.22)), 60))
    if "plants" in names["parts"]:
        c = Vector(S["plants"])
        specs.append(("vine-leaves", "Pothos: a vine's leaves",
                      os.path.join(REF, "26-plants", "monstera-3-white-pot-under-print.jpg"),
                      c + Vector((-0.55, -0.45, -0.10)), c + Vector((-0.83, -0.12, -0.22)), 60))
    return specs


def stage_closeups(out, names, cycles=False, only=None):
    sc = bpy.context.scene
    _studio(sc, cycles, 0.5)
    wall_plane()
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 720, 100
    d = os.path.join(out, "closeups")
    os.makedirs(d, exist_ok=True)
    pairs = []
    for key, title, photo, pos, tgt, lens in closeup_specs(names):
        if only and key not in only:
            continue
        cam = look_cam(f"still_cu_{key.replace('-', '_')}", pos, tgt, lens)
        p = os.path.join(d, f"{key}.png")
        _shoot(sc, cam, p, cycles, key)
        pairs.append(dict(key=key, title=title, photo=photo, render=p))
    jp = os.path.join(d, "pairs.json")
    with open(jp, "w") as f:
        json.dump(pairs, f, indent=1)
    import subprocess
    subprocess.run(["/opt/anaconda3/bin/python3", os.path.abspath(__file__), "--pairs", jp, d], check=False)
    log(f"close-ups: {len(pairs)} in {d}")
    progress(f"closeups: {len(pairs)} pairs in {d}")
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
            try:
                im = Image.open(f).convert("RGB")
            except Exception:
                continue
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
    views = outline_views(names)
    if not views:
        log("compare: no photo views for these parts")
        return {"passed": True, "views": []}
    rep = compare.run(views, os.path.join(out, "compare"), NAME, log=log)
    log(f"compare test {'PASSED' if rep['test']['passed'] else 'FAILED'}: {rep['paths']['md']}")
    progress(f"compare: {'PASS' if rep['test']['passed'] else 'FAIL'} " + ", ".join(
        f"{e['name']} {e['iou']:.3f}" for e in rep["views"]))
    return rep["test"]


def _export(objs, path):
    from lib import run
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select_set(o.name in objs)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_cameras=False, export_lights=False, export_extras=False,
                              export_image_format="AUTO")
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


def _ctx(obj, objs=None):
    import contextlib

    @contextlib.contextmanager
    def ctx():
        with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=objs or [obj],
                                       selected_editable_objects=objs or [obj]):
            yield
    return ctx()


OWN_MATERIAL = ("glow", "halo", "leaf_card", "peg_tile", "acrylic", "glass", "brand")


def bake_lite(objs, out, size=1024, orm_size=512):
    """One base-colour atlas and an ORM map for the opaque lite meshes (chair.bake_lite's pattern). The emissives,
    the leaf cards, the pegboard tile, the acrylic and the brand keep their own small materials."""
    import numpy as np
    from lib import materials as M
    from lib import renderqueue
    sys.path.insert(0, HERE)
    import desktop as DT          # its _bake and _gltf_group helpers (the module only; nothing runs)
    scene = bpy.context.scene
    baked = [o for o in objs if o.type == "MESH" and "brand" not in o.name
             and not any(m and any(k in m.name for k in OWN_MATERIAL) for m in o.data.materials)]
    odd = [o.name for o in baked if not o.data.materials or any(m is None for m in o.data.materials)]
    if odd:
        log(f"bake: no material on {odd}; skipped")
    baked = [o for o in baked if o.name not in odd]
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
    with _ctx(baked[0], baked):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.002, correct_aspect=True,
                                 scale_to_bounds=False)
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
    rich = _export(_with_empties(names["all"]), os.path.join(d, f"{NAME}{sfx}-rich.glb"))
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    lite_names = build(lite=True, studio=False)
    objs = [bpy.data.objects[n] for n in lite_names["all"]]
    kb = bake_lite(objs, out) if bake else {}
    lite = _export(_with_empties(lite_names["all"]), os.path.join(d, f"{NAME}{sfx}-lite.glb"))
    per = {p: tri_count([bpy.data.objects[n] for n in v["all"]]) for p, v in lite_names["parts"].items()}
    log(f"GLB rich {rich['kb']} KB {rich['triangles']} tris; lite {lite['kb']} KB {lite['triangles']} tris {per} {kb}")
    progress(f"export: rich {rich['kb']} KB {rich['triangles']} tris; lite {lite['kb']} KB {lite['triangles']} tris {per}")
    return {"rich": rich, "lite": lite, "lite_per_part": per, "images_kb": kb}


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    st = next((x for x in a if not x.startswith("--") and os.path.sep not in x), "default")
    stages = ["build", "stills", "compare", "closeups", "export"] if st == "default" else st.split(",")
    out = os.environ.get("WALL_OUT") or FOOT
    os.makedirs(out, exist_ok=True)
    rep = {"stages": stages, "part": PART}
    t0 = time.time()
    names = None
    cycles = "--cycles" in a or os.environ.get("WALL_CYCLES") == "1"
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
        only = os.environ.get("WALL_CU")
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
        pairs_sheet(sys.argv[i + 1], sys.argv[i + 2])
    elif "--neon-raster" in sys.argv:
        i = sys.argv.index("--neon-raster")
        neon_raster(sys.argv[i + 1], sys.argv[i + 2])
