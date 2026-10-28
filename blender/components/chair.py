"""The chair (component, 2026-10-28): Herman Miller Aeron Remastered, Size B, Mineral, polished aluminium base,
hard-floor casters, fully adjustable arms, PostureFit SL. An exact replica in shape and finish from the official
photos and sizes in docs/moodboard/local/ai-lab/25-chair/ (SOURCES.md). Built from scratch (MODELS.md: no usable
free Aeron). Pattern: tools/component_template.py, components/desktop.py and arms.py.

Always headless:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/components/chair.py -- [stages] [--cycles]

stages: outline | build,stills,compare,closeups,export (default) | any comma list.
Plain Python (Pillow): python3 chair.py --pairs <pairs.json> <dir>

Frame: origin on the floor under the cylinder's axis, front (the sitter's knees) -Y, up Z, the sitter's right +X.
Sub-assemblies, each its own function and mesh set: back (frame, mesh, PostureFit Y), seat (frame, mesh, waterfall
edge), arms (post, support, pad, knob), mechanism (box, levers, tension knob), base (hub, five legs, cylinder,
casters). All assembled under the empty `chair_swivel` at the cylinder's axis so the site can turn the chair.
The brand name "kalder" comes from content/room-brands.json via lib/brands.py at the real round mark's spot (the top
crossbar's rear face, centre).
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
    import bmesh
    from mathutils import Matrix, Vector
except ImportError:
    bpy = None

NAME = "chair"
MM = 0.001
REF = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab", "25-chair")
FOOT = os.path.join(REPO, "video-local", "footage", "2026-10-28-components", "chair")

# ---------------------------------------------------------------------------
# 1. numbers (mm), each tagged OFFICIAL / MEASURED / EST. The photos (front, side, back, 2500 px) were measured at
#    0.4528 mm/px (front: the base with casters spans 1515 px = 686 OFFICIAL overall width). In the photos the
#    seat sits at its highest (top 600 above the floor, overall 1079); SEAT_H sets the seat height when built.
# ---------------------------------------------------------------------------
OVERALL_W = 686.0          # OFFICIAL (27 in), arms and base
SEAT_D = 432.0             # OFFICIAL (17 in) seat depth
PHOTO_SEAT_H = 600.0       # MEASURED front/side: seat top in the photos (the cylinder at its highest)
ROOM_SEAT_H = 480.0        # EST: a mid setting in the room (OFFICIAL range 406 to 521 with the standard cylinder)
SEAT_FRONT = -277.0        # MEASURED side: front lip (y, mm behind the cylinder axis negative = forward)
SEAT_BACK = SEAT_FRONT + SEAT_D   # 155
SEAT_HW_FRONT, SEAT_HW_BACK = 250.0, 222.0   # MEASURED front: 500 across the front corners, 444 at the back
SEAT_RAIL = (26.0, 20.0)   # EST: the seat frame rail (wide, tall); the front lip swells to about 1.9 x
WATERFALL = (-215.0, 42.0)  # MEASURED side: the front edge starts curving at y -215 and drops about 40 (the thick lip)
SEAT_BOLSTER = 28.0        # EST side/3q: the frame sides rise at the rear corners (hip bolsters)
SEAT_TILT = 2.5            # EST: the seat pan tilts back 2 to 3 degrees
SEAT_DISH = 20.0           # EST: the mesh dishes into the frame
# Back: half-width and centre line (y behind the axis) per height above the seat, MEASURED front and side
BACK_HW = [(0, 206), (25, 200), (50, 195), (75, 194), (100, 193), (130, 194), (160, 197), (190, 204), (215, 212),
           (240, 223), (265, 234), (290, 245), (320, 253), (345, 257), (370, 258), (400, 255), (425, 249), (452, 218)]
BACK_YC = [(0, 202), (60, 190), (130, 181), (200, 186), (260, 199), (320, 218), (380, 240), (425, 258), (452, 271), (479, 294)]   # an S: lumbar bowed forward, about 11 degrees overall, the top rail curling back
BACK_TOP = 479.0           # MEASURED: the top arc's crown above the seat (1079 overall in the photo)
BACK_CORNER_Z = 440.0      # MEASURED: where the side rails turn into the top arc
BACK_RAIL = (36.0, 28.0)   # MEASURED front: the frame rail about 36 across its face; 28 deep EST
BACK_CUP = 22.0            # EST: the mesh is cupped (the centre 22 behind the rails)
BACK_BOTTOM = -40.0        # EST: the frame's lower crossbar centre below the seat top (behind the seat)
SPINE_X = 215.0            # MEASURED back: the two polished spine bars, 430 apart
Y_STEM = (48.0, 18.0)      # MEASURED back: the PostureFit stem 48 wide, 18 thick EST
Y_SPLIT_Z = 150.0          # MEASURED back: the Y forks 150 above the seat
Y_ARM_END = (200.0, 265.0)  # MEASURED front: the Y's arms end at x 200, z 265
Y_PAD = (160.0, 20.0)      # MEASURED back: the lumbar bar 160 wide, 20 tall, at the stem's foot
ARM_X = 250.0              # MEASURED front: the arm posts' centres, 500 apart
ARM_POST = (40.0, 24.0)    # MEASURED front: the post 40 across, 24 deep EST
ARM_POST_Y = 165.0         # MEASURED side: the post rises from the back link, 165 behind the axis
ARM_H = 182.0              # MEASURED side: pad top above the seat in the photos (the OFFICIAL range 173 to 274)
PAD = (250.0, 80.0, 26.0)  # MEASURED side/front: the pad 250 long, 80 wide, 26 thick
PAD_Y = (-137.0, 113.0)    # MEASURED side: the pad from 137 in front of the axis to 113 behind
PAD_X = 295.0              # MEASURED front: the pad's centre (outer edge at 335)
MECH = (250.0, 200.0, 90.0)    # MEASURED front/side, coordinator 2026-10-28: the cast tilt housing 250 wide, 200 long, 90 tall
MECH_Y = 95.0              # MEASURED side: housing centre 95 behind the axis
MECH_Z = -160.0            # MEASURED side: housing bottom 160 below the seat top
LEVER = (110.0, 22.0)      # EST: paddle length, width
COLUMN_R = 13.5            # MEASURED front: the black column 27 across
COLLAR = (24.0, 40.0)      # MEASURED front: the polished collar 48 across, 40 tall above the hub
HUB = (41.0, 280.0)        # MEASURED front: the hub 82 across at the top; its top 280 above the floor
LEG_R = 330.0              # MEASURED front: the leg tips (caster stems at 310)
LEG_ROOT = (36.0, 62.0)    # EST: leg section at the hub (wide, tall): a slim blade
LEG_TIP = (20.0, 24.0)     # EST: leg section at the tip
LEG_Z = (250.0, 108.0)     # MEASURED front: leg top at the hub 250, the tip 108 (the caster cap meets it)
CASTER = (60.0, 14.0, 12.0)  # MEASURED front: twin wheels 60 across, each 14 wide, 12 apart
CASTER_R = 310.0           # MEASURED front: the caster stems at r 310; the wheels trail 18 outward (centres 328)
LOGO = (22.0, 5.0)         # MEASURED back: the round mark 20 across on the top crossbar's rear face; our word 22 wide, cap 5

CUT = os.path.join(FOOT, "cutouts")
PHOTOS = {
    "front": dict(photo=os.path.join(CUT, "front-cut.png"), title="Aeron: front (Herman Miller photo) vs our model",
                  camera={"mode": "fit", "view": "front", "tilts": [0.0, 4.0, 8.0]}, mask="alpha",
                  explain="a perspective product shot (all five casters show): the camera is searched; the weave reads solid in the photo's silhouette but open in ours"),
    "side": dict(photo=os.path.join(CUT, "side-cut.png"), title="Aeron: side (Herman Miller photo) vs our model",
                 camera={"mode": "fit", "view": "right", "tilts": [0.0, 4.0, 8.0]}, mask="alpha", base_turn=18.0,
                 explain="a perspective shot with the base turned about 18 degrees (a leg points at the camera; the five casters sit at -293, -164, 14, 186, 335 mm, not a pure side); ours is turned 18 for this view"),
    "back": dict(photo=os.path.join(CUT, "back-cut.png"), title="Aeron: back (Herman Miller photo) vs our model",
                 camera={"mode": "fit", "view": "back", "tilts": [0.0, 4.0, 8.0]}, mask="alpha",
                 explain="a perspective product shot: the camera is searched; the weave reads solid in the photo, open in ours"),
    "three-quarter-front": dict(photo=os.path.join(REF, "three-quarter-front.jpg"),
                                title="Aeron: three-quarter front (Herman Miller photo) vs our model",
                                camera={"mode": "fit", "view": "front", "yaws": [28.0, 36.0], "tilts": [0.0],
                                        "distances": [3.0, 4.5]}, crop=(0, 2500, 0, 2400),
                                explain="a turned perspective shot: the camera's distance, height, turn and tilt are searched"),
}


# ---------------------------------------------------------------------------
# 2. helpers
# ---------------------------------------------------------------------------
def interp(table, z):
    if z <= table[0][0]:
        return table[0][1]
    for (z0, v0), (z1, v1) in zip(table, table[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0)
            return v0 + (v1 - v0) * t
    return table[-1][1]


def smooth(t):
    return t * t * (3 - 2 * t)


def mats():
    from lib import materials as M
    d = {}

    def get(n, **v):
        d[n] = bpy.data.materials.get("mat_chair_" + n) or M.principled("mat_chair_" + n, **v)
        return d[n]
    get("mineral", base="#c9cccb", rough=0.6, spec=0.4)             # soft-touch pale grey plastic
    get("pad", base="#cfd2d1", rough=0.8, spec=0.3)                  # the arm pads and lumbar pads
    get("polished", base="#eef0f3", rough=0.05, metal=1.0)           # polished aluminium
    get("black", base="#1a1a1b", rough=0.55)                         # casters, the column
    get("dark", base="#3e4043", rough=0.5)                           # the tension knob's grip
    get("cast", base="#6d7075", rough=0.42, metal=0.85)              # the cast tilt housing, dark grey metal
    get("mesh", base="#d2d5d5", rough=0.5, sheen=0.6, sheen_tint="#ffffff")
    return d


def mesh_material(lite):
    """8Z Pellicle: pale grey, see-through. Rich: a procedural weave (two wave textures) drives alpha and a bump
    for the sheen. Lite: a small tiling alpha-tested weave texture (alphaMode MASK)."""
    name = "mat_chair_weave" + ("_lite" if lite else "")
    m = bpy.data.materials.get(name)
    if m:
        return m
    from lib import materials as M
    m, nt, b = M._new(name)
    M._set(b, base="#a9a59c", rough=0.42, spec=0.5, sheen=0.6, sheen_tint="#fff4e4")   # a touch warmer than the frame
    try:
        b.inputs["Anisotropic"].default_value = 0.6
        b.inputs["Anisotropic Rotation"].default_value = 0.25
    except KeyError:
        pass
    m.use_backface_culling = False
    if lite:
        im = weave_image()
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = im
        tex.interpolation = "Linear"        # Closest exported a nearest-mip sampler that moires in three.js
        uv = nt.nodes.new("ShaderNodeUVMap")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (170.0, 170.0, 1.0)
        nt.links.new(uv.outputs[0], mp.inputs[0])
        nt.links.new(mp.outputs[0], tex.inputs[0])
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.5
        nt.links.new(tex.outputs["Alpha"], gt.inputs[0])
        nt.links.new(gt.outputs[0], b.inputs["Alpha"])
        for attr, val in (("blend_method", "CLIP"), ("alpha_threshold", 0.5), ("surface_render_method", "DITHERED")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    else:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
        nt.links.new(tc.outputs["UV"], mp.inputs[0])
        w1 = nt.nodes.new("ShaderNodeTexWave")
        w1.bands_direction, w1.wave_profile = "X", "SAW"
        w1.inputs["Scale"].default_value = 400.0
        w2 = nt.nodes.new("ShaderNodeTexWave")
        w2.bands_direction, w2.wave_profile = "Y", "SAW"
        w2.inputs["Scale"].default_value = 300.0
        nt.links.new(mp.outputs[0], w1.inputs[0])
        nt.links.new(mp.outputs[0], w2.inputs[0])
        mx = nt.nodes.new("ShaderNodeMath")
        mx.operation = "MINIMUM"           # a hole where both saws are high: about a quarter open
        nt.links.new(w1.outputs["Fac"], mx.inputs[0])
        nt.links.new(w2.outputs["Fac"], mx.inputs[1])
        ramp = nt.nodes.new("ShaderNodeMapRange")
        ramp.inputs["From Min"].default_value, ramp.inputs["From Max"].default_value = 0.30, 0.36   # about 45 % open
        ramp.inputs["To Min"].default_value, ramp.inputs["To Max"].default_value = 0.98, 0.06
        nt.links.new(mx.outputs[0], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], b.inputs["Alpha"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.3
        bump.inputs["Distance"].default_value = 0.0004
        nt.links.new(mx.outputs[0], bump.inputs["Height"])
        nt.links.new(bump.outputs[0], b.inputs["Normal"])
        for attr, val in (("surface_render_method", "DITHERED"), ("blend_method", "HASHED")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    return m


def weave_image(px=32):
    """A tiling weave tile: threads on a 2 px pitch (one cell = one thread crossing), holes transparent."""
    name = "chair_weave"
    im = bpy.data.images.get(name)
    if im:
        return im
    im = bpy.data.images.new(name, px, px, alpha=True)
    data = []
    for y in range(px):
        for x in range(px):
            on = (x % 4) < 2 or (y % 8) < 2          # dense warps, sparser wefts: fine vertical stripes
            shade = 0.66 if (x % 4) < 2 else 0.58
            data += [shade, shade - 0.015, shade - 0.05, 1.0 if on else 0.0]
    im.pixels = data
    im.pack()
    return im


class A:
    """One sub-assembly's bmesh (lib/parts.Mesh with a sweep and a grid added)."""

    def __init__(self):
        from lib import parts as P
        self.m = P.Mesh()
        self.P = P

    def sweep(self, path, profile, key, ref=None, closed=False, caps=True, refs=None):
        """Sweep a closed 2D profile [(u, v)] along a 3D path (mm). u lies in the plane normal to `ref`, v along
        it; `refs` gives a reference direction per station."""
        n = len(path)
        ref = ref or Vector((0, -1, 0))
        rings = []
        for i, p in enumerate(path):
            if closed:
                t = (path[(i + 1) % n] - path[i - 1]).normalized()
            else:
                t = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
            r = (refs[i] if refs else ref)
            n1 = t.cross(r).normalized()
            n2 = n1.cross(t).normalized()
            rings.append(self.m.verts([p + u * n1 + v * n2 for u, v in profile]))
        for i in range(n if closed else n - 1):
            self.m.strip(rings[i], rings[(i + 1) % n], key)
        if caps and not closed:
            self.m.face(list(reversed(rings[0])), key)
            self.m.face(rings[-1], key)
        return rings

    def grid(self, rows, key, double=False):
        """A surface from rows of points (each row the same length); quads wound so normals face -Y/+Z-ish."""
        vs = [self.m.verts(r) for r in rows]
        for a, b in zip(vs, vs[1:]):
            for i in range(len(a) - 1):
                self.m.face([a[i], a[i + 1], b[i + 1], b[i]], key)
        return vs

    def lathe(self, prof, seg, key, m=None):
        return self.m.lathe([(r * MM, z * MM) for r, z in prof], seg, key, m)

    def prism(self, outline, z0, z1, key, m=None):
        return self.m.prism([(x * MM, y * MM) for x, y in outline], z0 * MM, z1 * MM, key, m=m)

    def finish(self, name, mp, coll, parent=None, at=(0, 0, 0), smooth=30, bevel=None):
        return self.m.finish(name, mp, "+Z", at, coll, parent, smooth=smooth, bevel=bevel)


def V(x, y, z):
    return Vector((x * MM, y * MM, z * MM))


def rprof(w, h, r, n):
    """Rounded rectangle profile (u, v) in metres, CCW, centred."""
    from lib import parts as P
    return [(u * MM, v * MM) for u, v in P.rrect(w, h, r, n)]


def empty(name, coll, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type, e.empty_display_size = "ARROWS", 0.05
    coll.objects.link(e)
    e.parent = parent
    e.location = loc
    return e


# ---------------------------------------------------------------------------
# 3. sub-assemblies (all in the chair frame, mm, seat top at z = 0 until the whole upper part is lifted)
# ---------------------------------------------------------------------------
def back_loop(n_side=18, n_top=16):
    """The back frame's centre line: a closed loop (bottom crossbar, left rail, top arc, right rail)."""
    pts = []
    zs = [BACK_BOTTOM + (BACK_CORNER_Z - BACK_BOTTOM) * i / n_side for i in range(n_side + 1)]
    for s in (-1, 1):
        rail = []
        for z in zs:
            hw = interp(BACK_HW, max(z, 0)) - BACK_RAIL[0] / 2 - (0 if z >= 0 else -4 * (z / BACK_BOTTOM))
            rail.append(V(s * hw, interp(BACK_YC, max(z, 0)) - (0 if z >= 0 else 0.3 * z), z))
        pts.append(rail)
    left, right = pts
    top = []
    hw_c = interp(BACK_HW, BACK_CORNER_Z) - BACK_RAIL[0] / 2
    for i in range(1, n_top):
        t = i / n_top
        x = -hw_c * math.cos(math.pi * t)
        rise = math.sin(math.pi * t)
        z = BACK_CORNER_Z + (BACK_TOP - BACK_RAIL[0] / 2 - BACK_CORNER_Z) * rise
        top.append(V(x, interp(BACK_YC, z), z))
    loop = left + top + list(reversed(right))
    return loop


def build_back(coll, mp, parent, rough=False, lite=False, sfx=""):
    names = []
    seg = 4 if lite else 8
    # the frame: a rounded rail swept round the loop
    B = A()
    loop = back_loop(10 if lite else 18, 10 if lite else 16)
    B.sweep(loop, rprof(BACK_RAIL[0], BACK_RAIL[1], 9.0, 2 if lite else 4), "mineral", closed=True,
            refs=[Vector((0, -0.94, 0.34)) for _ in loop])
    # the lower crossbar behind the seat, joining the rails
    hw0 = interp(BACK_HW, 0)
    B.sweep([V(-hw0, 186, BACK_BOTTOM), V(hw0, 186, BACK_BOTTOM)], rprof(34, 40, 10, 2 if lite else 4), "mineral",
            ref=Vector((0, 0, 1)))
    # the polished spine bars, from the mechanism up the rails' lower half
    for s in (-1, 1):
        path = [V(s * SPINE_X, 150, -150), V(s * SPINE_X, 175, -60), V(s * (SPINE_X - 4), 188, 40),
                V(s * (SPINE_X - 10), 196, 140), V(s * (SPINE_X - 20), 204, 210)]
        B.sweep(path, rprof(18, 26, 6, 2 if lite else 4), "polished", ref=Vector((0, -1, 0)))
    obj = B.finish("chair_back" + sfx, mp, coll, parent)
    names.append(obj.name)
    # the mesh: a cupped grid inside the rails (kept in rough too: the photos' silhouettes are filled)
    Mh = A()
    nz, nx = (14, 10) if lite else (30, 22)
    rows = []
    for i in range(nz + 1):
        z = 8 + (BACK_TOP - 30 - 8) * i / nz
        hw = interp(BACK_HW, min(z, BACK_CORNER_Z)) - BACK_RAIL[0] * 0.45
        if z > BACK_CORNER_Z:   # under the top arc
            t = (z - BACK_CORNER_Z) / (BACK_TOP - BACK_CORNER_Z)
            hw = hw * math.sqrt(max(1 - t * t, 0.02))
        yc = interp(BACK_YC, z)
        row = []
        for j in range(nx + 1):
            u = -1 + 2 * j / nx
            row.append(V(u * hw, yc + BACK_CUP * (1 - u * u) * (1 - 0.5 * (z / BACK_TOP)), z))
        rows.append(row)
    Mh.grid(rows, "weave")
    mesh = Mh.finish("chair_back_mesh" + sfx, mp, coll, parent, smooth=80)
    mesh.data.materials.clear()
    mesh.data.materials.append(mesh_material(lite))
    uv = mesh.data.uv_layers.new(name="UVMap")
    for poly in mesh.data.polygons:
        for li in poly.loop_indices:
            v = mesh.data.vertices[mesh.data.loops[li].vertex_index].co
            uv.data[li].uv = (v.x / 0.55 + 0.5, v.z / 0.55)
    names.append(mesh.name)
    if rough:
        return names
    # PostureFit SL: the Y on the back of the mesh (stem, two arms, the lumbar bar with two pads, the dial)
    Yp = A()
    yb = lambda z: interp(BACK_YC, z) + BACK_CUP * (1 - 0.5 * z / BACK_TOP) + 6   # just behind the mesh centre
    stem = [V(0, yb(z), z) for z in (-10, 40, 90, Y_SPLIT_Z)]
    Yp.sweep(stem, rprof(Y_STEM[0], Y_STEM[1], 7, 2 if lite else 4), "mineral", ref=Vector((0, 0, 1)))
    for s in (-1, 1):
        arm = []
        for i in range(5):
            t = i / 4
            x = s * (8 + (Y_ARM_END[0] - 8) * t)
            z = Y_SPLIT_Z - 10 + (Y_ARM_END[1] - Y_SPLIT_Z + 10) * t
            u = x / (interp(BACK_HW, z) - BACK_RAIL[0] * 0.45)
            arm.append(V(x, interp(BACK_YC, z) + BACK_CUP * (1 - u * u) * (1 - 0.5 * z / BACK_TOP) + 5, z))
        Yp.sweep(arm, rprof(26, 14, 5, 2 if lite else 4), "mineral", ref=Vector((0, 1, 0)))
    # the lumbar bar and its two pads
    Yp.sweep([V(-Y_PAD[0] / 2, yb(28) + 3, 28), V(Y_PAD[0] / 2, yb(28) + 3, 28)], rprof(Y_PAD[1], 16, 6, 2 if lite else 4),
             "mineral", ref=Vector((0, 1, 0)))
    for s in (-1, 1):
        Yp.sweep([V(s * 62, yb(28) + 2, 12), V(s * 62, yb(28) + 2, 52)], rprof(52, 20, 8, 2 if lite else 4), "pad",
                 ref=Vector((0, 1, 0)))
    # the dial on the stem (the lumbar depth adjuster)
    Yp.lathe([(0, 0), (11, 0), (11, 6), (0, 6)], 8 if lite else 24, "mineral",
             Matrix.Translation(V(0, yb(70) + Y_STEM[1] / 2, 70)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    y = Yp.finish("chair_back_posturefit" + sfx, mp, coll, parent)
    names.append(y.name)
    return names


def seat_outline(n=40):
    """The seat frame's centre line in the top view, CCW, (x, y) in mm: a sculpted rounded outline, widest just
    behind the front corners, narrowing to the back (side.jpg and three-quarter-front.jpg)."""
    pts = []
    yf = SEAT_FRONT + SEAT_RAIL[0] / 2 + 2
    yb = SEAT_BACK - SEAT_RAIL[0] / 2
    L = yb - yf
    for i in range(n):
        t = i / n                              # 0 at the front centre, round the right side, back, left side
        a = 2 * math.pi * t
        # a superellipse-ish outline: y from a cosine, x from a sine shaped by the local half-width
        y = yf + L * (1 - math.cos(a)) / 2
        v = (y - yf) / L
        hw = SEAT_HW_FRONT - 10 + 24 * math.sin(math.pi * min(v / 0.55, 1.0)) * (v < 0.55) \
            - (SEAT_HW_FRONT - SEAT_HW_BACK + 2) * max(v - 0.35, 0) / 0.65
        hw -= SEAT_RAIL[0] / 2
        x = hw * math.sin(a) / max(abs(math.sin(a)), 1e-6) * abs(math.sin(a)) ** 0.55
        pts.append((x, y))
    return pts


def waterfall_z(y):
    y0, drop = WATERFALL
    if y >= y0:
        return 0.0
    t = min((y0 - y) / (y0 - SEAT_FRONT), 1.0)
    return -drop * (1 - math.sqrt(max(1 - t * t, 0.0)))


def bolster_z(x, y, hw):
    """The frame's sides rise at the back into the hip bolsters (28 mm at the rear corners)."""
    v = max((y - 20) / (SEAT_BACK - 20), 0.0)
    return SEAT_BOLSTER * (v ** 1.5) * min(abs(x) / max(hw, 1), 1.0) ** 2


def build_seat(coll, mp, parent, rough=False, lite=False, sfx=""):
    names = []
    S = A()
    ol = seat_outline(24 if lite else 48)
    path, refs = [], []
    for x, y in ol:
        hw = SEAT_HW_FRONT - 16 if y < 0 else SEAT_HW_BACK
        path.append(V(x, y, waterfall_z(y) - SEAT_RAIL[1] / 2 + bolster_z(x, y, hw)))
        refs.append(Vector((0, 0, 1)))
    # the rail: a rounded section, taller and rounder across the front (the thick waterfall lip)
    prof = rprof(SEAT_RAIL[0], SEAT_RAIL[1], 7, 2 if lite else 4)
    rings = S.sweep(path, prof, "mineral", closed=True, ref=Vector((0, 0, 1)))
    for ring, (x, y) in zip(rings, ol):
        if y < WATERFALL[0] + 40:
            f = min((WATERFALL[0] + 40 - y) / 60, 1.0)
            c = sum((v.co for v in ring), Vector()) / len(ring)
            for v in ring:
                v.co = c + (v.co - c) * (1 + 0.9 * f)      # the front lip swells to about 1.9 x the rail
    # the seat pan under the frame: a shallow rounded box the mechanism bolts to
    n0 = len(S.m.bm.verts)
    S.P._rbox(S.m, 330 * MM, 300 * MM, 24 * MM, 40 * MM, 6 * MM, 6 * MM, 1 if lite else 3, "mineral",
              z0=-(SEAT_RAIL[1] + 26) * MM)
    S.m.bm.verts.ensure_lookup_table()
    bmesh.ops.translate(S.m.bm, verts=S.m.bm.verts[n0:], vec=(0, 40 * MM, 0))
    obj = S.finish("chair_seat" + sfx, mp, coll, parent)
    obj.rotation_euler.x = math.radians(-SEAT_TILT)
    names.append(obj.name)
    # the seat mesh: dished into the frame, following the waterfall and the bolsters (kept in rough: filled silhouettes)
    Mh = A()
    ny, nx = (12, 10) if lite else (28, 20)
    rows = []
    yf, yb = SEAT_FRONT + 4, SEAT_BACK - SEAT_RAIL[0] / 2 - 2
    L = yb - yf
    for i in range(ny + 1):
        t = i / ny
        y = yf + L * t
        hw = SEAT_HW_FRONT - 10 + 24 * math.sin(math.pi * min(t / 0.55, 1.0)) * (t < 0.55) \
            - (SEAT_HW_FRONT - SEAT_HW_BACK + 2) * max(t - 0.35, 0) / 0.65 - SEAT_RAIL[0] * 0.75
        if y < yf + 70:
            hw -= 70 * (1 - math.sqrt(max(1 - ((yf + 70 - y) / 70) ** 2, 0)))
        row = []
        for j in range(nx + 1):
            u = -1 + 2 * j / nx
            dish = SEAT_DISH * (1 - u * u) * math.sin(math.pi * min(max((y - yf - 30) / (L - 30), 0), 1))
            row.append(V(u * hw, y, waterfall_z(y) - 5 - dish + bolster_z(u * hw, y, hw) * 0.8))
        rows.append(row)
    Mh.grid(rows, "weave")
    mesh = Mh.finish("chair_seat_mesh" + sfx, mp, coll, parent, smooth=80)
    mesh.rotation_euler.x = math.radians(-SEAT_TILT)
    mesh.data.materials.clear()
    mesh.data.materials.append(mesh_material(lite))
    uv = mesh.data.uv_layers.new(name="UVMap")
    for poly in mesh.data.polygons:
        for li in poly.loop_indices:
            v = mesh.data.vertices[mesh.data.loops[li].vertex_index].co
            uv.data[li].uv = (v.x / 0.55 + 0.5, v.y / 0.55 + 0.5)
    names.append(mesh.name)
    return names


def build_arm(side, coll, mp, parent, rough=False, lite=False, sfx=""):
    s = 1 if side == "r" else -1
    R = A()
    seg = 2 if lite else 5
    zt = ARM_H - PAD[2]
    # the polished support: from the pivot on the back frame's side, down a little, then sweeping up and forward
    # in one curve to under the pad's front half (side.jpg, detail-arms-1.jpg)
    path = [V(s * (ARM_X - 15), ARM_POST_Y + 8, -30), V(s * (ARM_X - 2), ARM_POST_Y + 2, 20),
            V(s * (ARM_X + 12), ARM_POST_Y - 18, 70), V(s * (ARM_X + 32), ARM_POST_Y - 60, zt - 42),
            V(s * (PAD_X - 4), ARM_POST_Y - 130, zt - 16), V(s * (PAD_X - 2), ARM_POST_Y - 200, zt - 8),
            V(s * (PAD_X - 2), PAD_Y[0] + 70, zt - 8)]
    refs = [Vector((s, 0, 0)) for _ in path]
    R.sweep(path, rprof(ARM_POST[0], ARM_POST[1], 9, seg), "polished", refs=refs)
    # the pad: a rounded slab, slightly pivoted inward at the front
    pad = [V(s * (PAD_X + 6), PAD_Y[1], ARM_H - PAD[2] / 2), V(s * (PAD_X - 6), PAD_Y[0], ARM_H - PAD[2] / 2)]
    R.sweep(pad, rprof(PAD[1], PAD[2], 11, 3 if lite else 6), "pad", ref=Vector((0, 0, 1)))
    if not rough:
        # the height-adjustment knob on the pivot's outer face, and the pivot boss on the back frame's side
        R.lathe([(0, 0), (16, 0), (16, 8), (13, 11), (0, 11)], 8 if lite else 24, "polished",
                Matrix.Translation(V(s * (ARM_X - 15 + ARM_POST[0] / 2), ARM_POST_Y + 8, -30)) @ Matrix.Rotation(s * math.pi / 2, 4, "Y"))
        R.lathe([(0, 0), (14, 0), (14, 14), (0, 14)], 8 if lite else 20, "mineral",
                Matrix.Translation(V(s * (ARM_X - 15 - ARM_POST[0] / 2 - 14), ARM_POST_Y + 8, -30)) @ Matrix.Rotation(s * math.pi / 2, 4, "Y"))
    obj = R.finish(f"chair_arm_{side}" + sfx, mp, coll, parent)
    return [obj.name]


def build_mech(coll, mp, parent, rough=False, lite=False, sfx=""):
    Mc = A()
    seg = 1 if lite else 3
    w, d, h = MECH
    # the cast tilt housing: dark metal, rounded, with a polished cross link under the back's spine bars
    Mc.P._rbox(Mc.m, w * MM, d * MM, h * MM, 45 * MM, 20 * MM, 30 * MM, seg, "cast", z0=MECH_Z * MM)
    bmesh.ops.translate(Mc.m.bm, verts=Mc.m.bm.verts, vec=(0, MECH_Y * MM, 0))
    Mc.sweep([V(-SPINE_X - 8, 150, MECH_Z + 36), V(SPINE_X + 8, 150, MECH_Z + 36)], rprof(28, 28, 8, 2 if lite else 4),
             "polished", ref=Vector((0, 0, 1)))
    # the two pivot ears the back's spine bars hinge on, and a polished front yoke
    for sg in (-1, 1):
        Mc.lathe([(0, -14), (22, -14), (22, 14), (0, 14)], 8 if lite else 20, "cast",
                 Matrix.Translation(V(sg * (SPINE_X - 20), 150, MECH_Z + 36)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    Mc.sweep([V(-w / 2 + 10, MECH_Y - d / 2 + 12, MECH_Z + h - 10), V(w / 2 - 10, MECH_Y - d / 2 + 12, MECH_Z + h - 10)],
             rprof(20, 20, 6, 2 if lite else 4), "polished", ref=Vector((0, 0, 1)))
    if not rough:
        # the two paddle levers on the sitter's right (seat height, tilt limiter), polished arms with pale paddles
        zl = MECH_Z + 28
        for y, length in ((-10, LEVER[0]), (50, LEVER[0] * 0.8)):
            Mc.sweep([V(w / 2 - 20, y, zl), V(w / 2 + 40, y, zl), V(w / 2 + 40, y - length, zl + 4)],
                     rprof(16, 12, 5, 2 if lite else 4), "polished", ref=Vector((0, 0, 1)))
            Mc.sweep([V(w / 2 + 40, y - length + 10, zl + 4), V(w / 2 + 40, y - length - 40, zl + 8)],
                     rprof(LEVER[1], 14, 6, 2 if lite else 4), "mineral", ref=Vector((0, 0, 1)))
        # the tilt tension knob on the sitter's left, a ribbed dark drum on a polished axle
        Mc.lathe([(0, 0), (8, 0), (8, 36), (19, 36), (21, 40), (21, 68), (18, 72), (0, 72)], 12 if lite else 36, "dark",
                 Matrix.Translation(V(-(w / 2 - 10), MECH_Y + 50, MECH_Z + 50)) @ Matrix.Rotation(-math.pi / 2, 4, "Y"))
    obj = Mc.finish("chair_mech" + sfx, mp, coll, parent)
    return [obj.name]


def build_base(coll, mp, parent, rough=False, lite=False, sfx=""):
    """The hub, the five legs, the cylinder and the casters. Floor at z = 0, the cylinder's axis at the origin."""
    names = []
    seg = 16 if lite else 48
    Bs = A()
    # hub: a polished dome with a collar
    Bs.lathe([(0, 230), (70, 230), (62, 262), (48, HUB[1] - 4), (COLLAR[0], HUB[1]), (COLLAR[0], HUB[1] + COLLAR[1]),
              (COLUMN_R + 3, HUB[1] + COLLAR[1] + 6), (0, HUB[1] + COLLAR[1] + 6)], seg, "polished")
    for i in range(5):
        a = -math.pi / 2 + 2 * math.pi * i / 5        # one leg straight forward (-Y)
        dirv = Vector((math.cos(a), math.sin(a), 0))
        path, refs = [], []
        n = 4 if lite else 8
        for k in range(n + 1):
            t = k / n
            r = 40 + (LEG_R - 40) * t
            z = LEG_Z[0] + (LEG_Z[1] - LEG_Z[0]) * (1 - (1 - t) ** 1.6)
            path.append(dirv * r * MM + Vector((0, 0, z * MM)))
        # tapered section: sweep with per-station scaling (build rings by hand)
        rings = []
        for k, p in enumerate(path):
            t = k / n
            w = LEG_ROOT[0] + (LEG_TIP[0] - LEG_ROOT[0]) * t
            h = LEG_ROOT[1] + (LEG_TIP[1] - LEG_ROOT[1]) * t
            tng = (path[min(k + 1, n)] - path[max(k - 1, 0)]).normalized()
            n1 = tng.cross(Vector((0, 0, 1))).normalized()
            n2 = n1.cross(tng).normalized()
            prof = rprof(w, h, min(w, h) * 0.35, 2 if lite else 4)
            rings.append(Bs.m.verts([p + u * n1 + v * n2 for u, v in prof]))
        for a_, b_ in zip(rings, rings[1:]):
            Bs.m.strip(a_, b_, "polished")
        Bs.m.face(list(reversed(rings[0])), "polished")
        Bs.m.face(rings[-1], "polished")
    base = Bs.finish("chair_base" + sfx, mp, coll, parent)
    names.append(base.name)
    # the cylinder: the black column from the collar up into the mechanism
    Cy = A()
    Cy.lathe([(0, HUB[1] + COLLAR[1]), (COLUMN_R, HUB[1] + COLLAR[1]), (COLUMN_R, 2000), (0, 2000)], 8 if lite else 24, "black")
    cyl = Cy.finish("chair_cylinder" + sfx, mp, coll, parent)
    names.append(cyl.name)
    # casters: twin black wheels on a polished stem under each leg tip, trailing outward
    for i in range(5):
        a = -math.pi / 2 + 2 * math.pi * i / 5
        dirv = Vector((math.cos(a), math.sin(a), 0))
        Cs = A()
        rot = Matrix.Rotation(a, 4, "Z")
        stem_at = dirv * CASTER_R * MM
        wd, ww, gap = CASTER
        if True:
            # the swivel stem and cap
            Cs.lathe([(0, 24), (5.5, 24), (5.5, LEG_Z[1] + 10), (0, LEG_Z[1] + 10)], 8 if lite else 16, "polished",
                     Matrix.Translation(stem_at))
            Cs.lathe([(0, 26), (21, 26), (23, 30), (23, 66), (17, LEG_Z[1] - 12), (0, LEG_Z[1] - 12)], 8 if lite else 24, "black",
                     Matrix.Translation(stem_at))
            # the fork body (a block between the wheels) and the two wheels on an axle trailing 18 mm outward
            axle = stem_at + dirv * 18 * MM + Vector((0, 0, wd / 2 * MM))
            tr = Matrix.Translation(axle) @ rot @ Matrix.Rotation(math.pi / 2, 4, "X")
            Cs.lathe([(0, -gap / 2 - 1), (14, -gap / 2 - 1), (14, gap / 2 + 1), (0, gap / 2 + 1)], 8 if lite else 16, "black", tr)
            for sgn in (-1, 1):
                z0 = sgn * gap / 2
                z1 = sgn * (gap / 2 + ww)
                pr = [(0, z0), (wd / 2 - 3, z0), (wd / 2, z0 + sgn * 2), (wd / 2, z1 - sgn * 2), (wd / 2 - 3, z1), (0, z1)]
                if sgn < 0:
                    pr = list(reversed(pr))
                Cs.lathe(pr, 12 if lite else 32, "black", tr)
        c = Cs.finish(f"chair_caster_{i + 1:02d}" + sfx, mp, coll, parent)
        names.append(c.name)
    return names


# ---------------------------------------------------------------------------
# 4. build
# ---------------------------------------------------------------------------
def build(rough=False, lite=False, collection=None, seat_h=None, parent=None):
    """Returns object names by role plus "all". The upper assembly (seat, back, arms, mechanism) is lifted to
    seat_h (mm, seat top above the floor; default the photos' 600)."""
    sfx = "_lite" if lite else ""
    coll = collection or bpy.context.scene.collection
    mp = mats()
    seat_h = PHOTO_SEAT_H if seat_h is None else seat_h
    swivel = empty("chair_swivel" + sfx, coll, parent, (0, 0, 0))
    upper = empty("chair_upper" + sfx, coll, swivel, (0, 0, seat_h * MM))
    names = {"swivel": [swivel.name], "upper": [upper.name]}
    names["back"] = build_back(coll, mp, upper, rough, lite, sfx)
    names["seat"] = build_seat(coll, mp, upper, rough, lite, sfx)
    names["arms"] = build_arm("l", coll, mp, upper, rough, lite, sfx) + build_arm("r", coll, mp, upper, rough, lite, sfx)
    names["mech"] = build_mech(coll, mp, upper, rough, lite, sfx)
    names["base"] = build_base(coll, mp, swivel, rough, lite, sfx)
    # the column's top is hidden in the mechanism: trim it to the housing
    cyl = bpy.data.objects["chair_cylinder" + sfx]
    top = (seat_h + MECH_Z + 20) * MM
    for v in cyl.data.vertices:
        if v.co.z > 1.0:
            v.co.z = top
    if not rough:
        from lib import brands
        back = bpy.data.objects["chair_back" + sfx]
        # the top crossbar's rear face: the rail's section is tilted with the lean (normal (0, -0.94, 0.34) in
        # back_loop), so the rear face sits 13.2 behind and 4.8 below the crown's centre line and faces back and
        # a little down; the mark sits 1 mm proud of it, 7 mm under the crown
        zcrown = BACK_TOP - BACK_RAIL[0] / 2
        at = (0, (interp(BACK_YC, zcrown) + 13.2 + 1.0) * MM, (zcrown - 4.8 - 7.0) * MM)
        d = brands.decal("chair", at=at, normal=(0, 0.94, -0.34), up=(0, 0.34, 0.94), height=LOGO[1] * MM,
                         max_width=LOGO[0] * MM, finish="embossed", colour="#a2a6a6", parent=back, collection=coll,
                         lite=lite, name="chair_brand" + sfx)
        names["brand"] = [d.name] if d else []
    names["all"] = [n for k, v in names.items() if k not in ("swivel", "upper") for n in v]
    bpy.context.view_layer.update()
    return names


def outline_views(names):
    out = []
    for view, p in PHOTOS.items():
        out.append(dict(name=f"{NAME}-{view}", title=p["title"], photo=p["photo"], mask=p.get("mask", 0.93),
                        crop=p.get("crop"), fill=False, objects=[n for n in names["all"] if "brand" not in n],
                        camera=dict(p["camera"]), explain=p.get("explain"),
                        prepare=turn_base(p["base_turn"]) if p.get("base_turn") else None))
    return out


def turn_base(deg):
    def prep():
        objs = [o for o in bpy.data.objects if o.name.startswith(("chair_base", "chair_caster"))]
        for o in objs:
            o.rotation_euler.z += math.radians(deg)
        bpy.context.view_layer.update()

        def undo():
            for o in objs:
                o.rotation_euler.z -= math.radians(deg)
            bpy.context.view_layer.update()
        return undo
    return prep


def make_cutouts():
    """Plain Python (Pillow, numpy): the three straight photos as alpha cutouts, the floor shadow under the base
    removed (grey, lighter than 0.6, in the bottom 130 px where only the black casters stand). Written to CUT; the
    photos are never touched."""
    import numpy as np
    from PIL import Image
    os.makedirs(CUT, exist_ok=True)
    for n, floor in (("front", 2384), ("side", 2402), ("back", 2408)):
        im = Image.open(os.path.join(REF, n + ".jpg")).convert("RGB")
        a = np.asarray(im) / 255.0
        lum = a.mean(-1)
        k = lum < 0.93
        ys = np.arange(a.shape[0])[:, None]
        k &= ~((ys > floor - 130) & (lum > 0.6))
        k[floor + 2:] = False
        Image.fromarray(np.dstack([a * 255, k * 255]).astype(np.uint8), "RGBA").save(os.path.join(CUT, n + "-cut.png"))
    print("CUTOUTS", CUT)


# ---------------------------------------------------------------------------
# 5. stages
# ---------------------------------------------------------------------------
def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {NAME}: {msg}", flush=True)


def progress(msg):
    os.makedirs(FOOT, exist_ok=True)
    with open(os.path.join(FOOT, "PROGRESS.md"), "a") as f:
        f.write(f"{time.strftime('%H:%M')} {msg}\n")


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
    holder = {}

    def b(rough=True):
        holder["n"] = build(rough=True)
        return {k: v for k, v in holder["n"].items() if k not in ("swivel", "upper")}
    r = outline_check.run(NAME, b, outline_views, os.path.join(out, "outline"), log=log)
    progress(f"outline: {'PASS' if r['test']['passed'] else 'FAIL'} " + ", ".join(
        f"{e['name']} {e['iou']:.3f}" for e in r["views"]) + f" sheet {r.get('sheet')}")
    return r


def stage_build(out):
    clear()
    t = time.time()
    col = bpy.data.collections.new("chair")
    bpy.context.scene.collection.children.link(col)
    names = build(collection=col)
    blend = os.path.join(BLENDER_DIR, "out", "components", f"{NAME}.blend")
    os.makedirs(os.path.dirname(blend), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    with open(os.path.join(out, f"{NAME}-names.json"), "w") as f:
        json.dump(names, f, indent=1)
    tris = sum(sum(len(p.vertices) - 2 for p in bpy.data.objects[n].data.polygons) for n in names["all"]
               if bpy.data.objects[n].type == "MESH")
    log(f"built in {time.time() - t:.1f} s, {tris} triangles, saved {blend}")
    progress(f"build: {tris} triangles in {time.time() - t:.1f} s")
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
        try:                      # 2026-10-28: setting the Metal device prefs here crashed Blender 5.2 (NSURL nil); arms' way
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


def stage_stills(out, names, cycles=False):
    from lib import backdrops, compare
    sc = bpy.context.scene
    _studio(sc, cycles, 0.55)          # the pale chair blows out at full studio strength
    lo, hi = compare.world_bbox(names["all"])
    c, size = (lo + hi) / 2, hi - lo
    cams = {"hero": backdrops.three_quarter_camera(c, max(size) * 1.05, az=-35, el=14, name="still_hero"),
            "front": backdrops.view_camera("front", c, max(size.x, size.z * 16 / 9) * 1.1, name="still_front"),
            "side": backdrops.view_camera("right", c, max(size.y, size.z * 16 / 9) * 1.1, name="still_side"),
            "back": backdrops.view_camera("back", c, max(size.x, size.z * 16 / 9) * 1.1, name="still_back"),
            "top": backdrops.view_camera("top", c, max(size.x, size.y * 16 / 9) * 1.1, name="still_top")}
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    paths = {}
    for k, cam in list(cams.items()) + [("clay", cams["hero"])]:
        if k == "clay":
            from lib import looks
            looks.clay_on()
        p = os.path.join(out, f"{NAME}-{k}.png")
        _shoot(sc, cam, p, cycles, k)
        if k == "clay":
            from lib import looks
            looks.clay_off()
        paths[k] = p
    log(f"stills: {', '.join(paths)}")
    progress(f"stills ({'Cycles' if cycles else 'EEVEE'}): {', '.join(os.path.basename(p) for p in paths.values())}")
    return paths


def closeup_specs():
    s = PHOTO_SEAT_H * MM
    yb = interp(BACK_YC, 200) * MM
    return [
        ("back-frame", "Aeron: the back frame and the weave", os.path.join(REF, "three-quarter-back.jpg"),
         (0.55, 0.85, s + 0.45), (0.12, yb, s + 0.30), 50),
        ("posturefit", "Aeron: the PostureFit SL Y", os.path.join(REF, "back.jpg"),
         (0.05, 1.05, s + 0.25), (0.0, yb, s + 0.15), 50),
        ("arm", "Aeron: an arm, pad, post and knob", os.path.join(REF, "detail-arms-1.jpg"),
         (0.70, -0.30, s + 0.33), (0.27, 0.0, s + 0.12), 50),
        ("seat-front", "Aeron: the seat's waterfall front edge", os.path.join(REF, "side.jpg"),
         (-0.65, -0.55, s + 0.12), (-0.05, -0.20, s - 0.02), 50),
        ("mech", "Aeron: the tilt mechanism and levers", os.path.join(REF, "three-quarter-back.jpg"),
         (0.62, -0.25, s - 0.05), (0.08, 0.08, s - 0.14), 50),
        ("base", "Aeron: the polished base and a caster", os.path.join(REF, "three-quarter-front.jpg"),
         (0.45, -0.70, 0.30), (0.05, -0.12, 0.12), 50),
        ("logo", "Aeron: the mark on the top crossbar (ours: kalder)", os.path.join(REF, "back.jpg"),
         (0.0, 0.66, s + 0.40), (0.0, (interp(BACK_YC, BACK_TOP - 18) + 14) * MM, s + (BACK_TOP - 30) * MM), 85),
    ]


def stage_closeups(out, names, cycles=False, only=None):
    sc = bpy.context.scene
    _studio(sc, cycles, 0.45)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 720, 100
    d = os.path.join(out, "closeups")
    os.makedirs(d, exist_ok=True)
    pairs = []
    for key, title, photo, pos, tgt, lens in closeup_specs():
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
            im = Image.open(f).convert("RGB")
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
    rep = compare.run(outline_views(names), os.path.join(out, "compare"), NAME, log=log)
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


def bake_lite(objs, out, size=1024, orm_size=512):
    """One base-colour atlas and an ORM map for the opaque lite meshes (desktop.bake_lite's pattern). The weave
    keeps its own small alpha-tested material; the brand its own."""
    import numpy as np
    from lib import materials as M
    from lib import renderqueue
    sys.path.insert(0, HERE)
    import desktop as DT          # its _bake and _gltf_group helpers (the module only; nothing runs)
    scene = bpy.context.scene
    baked = [o for o in objs if o.type == "MESH" and "mesh" not in o.name.replace("_mesh", "") and "brand" not in o.name
             and not any(m and "weave" in m.name for m in o.data.materials)]
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
    base = DT._image("chair_atlas", size)
    rough = DT._image("chair_rough_tmp", orm_size, True)
    metal = DT._image("chair_metal_tmp", orm_size, True)
    ao = DT._image("chair_ao_tmp", orm_size, True)
    with renderqueue.slot("chair lite bake"):
        DT._bake(baked, base, "base", 4)
        DT._bake(baked, rough, "rough", 4)
        DT._bake(baked, metal, "metal", 4)
        DT._bake(baked, ao, "ao", 32)
    for o in hidden:
        o.hide_render = False
    orm = DT._image("chair_orm", orm_size, True)
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
    for im, fn, q in ((base, "chair_atlas.jpg", 90), (orm, "chair_orm.jpg", 92)):
        p = os.path.join(out, fn)
        im.filepath_raw = p
        im.file_format = "JPEG"
        scene.render.image_settings.quality = q
        im.save()
        kb[fn] = round(os.path.getsize(p) / 1024)
    m, nt, b = M._new("mat_chair_lite")
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
    rich = _export(_with_empties(names["all"]), os.path.join(d, f"{NAME}-rich.glb"))
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    lite_names = build(lite=True)
    objs = [bpy.data.objects[n] for n in lite_names["all"]]
    kb = bake_lite(objs, out) if bake else {}
    lite = _export(_with_empties(lite_names["all"]), os.path.join(d, f"{NAME}-lite.glb"))
    per = {k: sum(sum(len(f.vertices) - 2 for f in bpy.data.objects[n].data.polygons) for n in v
                  if bpy.data.objects[n].type == "MESH") for k, v in lite_names.items() if k not in ("all", "swivel", "upper")}
    log(f"GLB rich {rich['kb']} KB {rich['triangles']} tris; lite {lite['kb']} KB {lite['triangles']} tris {per} {kb}")
    progress(f"export: rich {rich['kb']} KB {rich['triangles']} tris; lite {lite['kb']} KB {lite['triangles']} tris {per}")
    return {"rich": rich, "lite": lite, "lite_per_part": per, "images_kb": kb}


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    st = next((x for x in a if not x.startswith("--") and os.path.sep not in x), "default")
    stages = ["build", "stills", "compare", "closeups", "export"] if st == "default" else st.split(",")
    out = os.environ.get("CHAIR_OUT") or FOOT
    os.makedirs(out, exist_ok=True)
    rep = {"stages": stages}
    t0 = time.time()
    names = None
    cycles = "--cycles" in a or os.environ.get("CHAIR_CYCLES") == "1"
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
        only = os.environ.get("CHAIR_CU")
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
    elif "--cutouts" in sys.argv:
        make_cutouts()
