"""The chair (component; first built 2026-10-28, rebuilt 2026-11-12): Herman Miller Aeron Remastered, Size B,
Mineral, polished aluminium base, hard-floor casters, fully adjustable arms, PostureFit SL. Shape and finish from
the official photos and sizes in docs/moodboard/local/ai-lab/25-chair/ (SOURCES.md). Built from scratch: the only
real Aeron on Sketchfab is non-commercial (checked again 2026-11-12).

Always headless:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/components/chair.py -- [stages]        (CHAIR_CYCLES=1 for Cycles stills: Blender 5.2
                                                                 rejects a --cycles flag even after the --)

stages: outline | build,stills,compare,closeups,export (default) | any comma list.
Plain Python (Pillow): python3 chair.py --pairs <pairs.json> <dir>

Frame: origin on the floor under the cylinder's axis, front (the sitter's knees) -Y, up Z. The side photo looks
from +X (Blender's "right" view), which is the sitter's left: the polished tilt lever with the ball is on +X, the
tilt-tension knob on -X.

2026-11-12 rebuild. Every free-form part is a lofted surface traced from the photos on a millimetre grid:
  seat   one saddle surface S(x, y) (side rails arched, centre sagging, the front falling 110 mm: the waterfall);
         the frame is a ring lofted on S with a rolled outer edge and deep side skirts, the mesh hangs inside it
  back   a wedge-section frame (slim bezel in front, a broad flange behind, deeper up top) lofted round the loop,
         leaning along the traced S-curve, the top bar hooked back; the mesh cupped inside; the PostureFit Y
  arms   a sculpted pad on a carrier plate, a thin cast blade, a yoke sliding on a polished post behind the back
  link   the polished yoke from the posts forward under the seat to the tilt housing, the brackets up to the
         seat's side pivots
  base   five legs with a crowned shield section tapering to a turned-down boss, twin-wheel casters
Sub-assemblies under the empty `chair_swivel` at the cylinder's axis so the site can turn the chair. The brand
name comes from content/room-brands.json via lib/brands.py, where the real round mark sits (the top bar's rear
face, centre).
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
FOOT = os.path.join(REPO, "video-local", "footage", "2026-11-12-chair")
CUT = os.path.join(FOOT, "cutouts")

# ---------------------------------------------------------------------------
# 1. numbers (mm). Traced 2026-11-12 on a millimetre grid over side.jpg, front.jpg and back.jpg (0.4528 mm/px,
#    the column's axis at x 1216 / 1258 / 1255). "Upper" numbers are relative to the old seat datum (grid z 600).
#    The 2026-10-28 build took the photos' last non-white row as the floor; that row is the casters' reflection.
#    The casters touch the floor 90 mm higher (their bottoms sit at grid z 51, 78 and 121 by depth), so the datum
#    is 510 above the floor in the photos, not 600, and the base is 90 mm lower than it was built.
# ---------------------------------------------------------------------------
PHOTO_SEAT_H = 510.0       # MEASURED side: the seat datum above the floor in the photos
ROOM_SEAT_H = 480.0        # the datum in the room; the mesh's middle sits about 8 under it (a 470 seat)

# Seat. The outline of the frame's outer edge from above, right half, front centre to rear centre (x, y).
SEAT_OUT = [(0, -286), (80, -283), (160, -266), (215, -235), (244, -185), (252, -120), (250, -50), (244, 20),
            (235, 85), (222, 125), (196, 148), (130, 157), (0, 158)]
# The saddle: height of the side rails' top, of the centre line, and of the frame's underside, by y (MEASURED side)
SEAT_SIDE = [(-286, -64), (-261, -37), (-230, -17), (-202, 0), (-148, 22), (-103, 36), (-57, 45), (-12, 49),
             (33, 45), (78, 34), (115, 20), (140, 9), (158, 3)]
SEAT_MID = [(-286, -64), (-262, -46), (-230, -30), (-190, -18), (-120, -9), (-40, -8), (40, -9), (110, -6), (158, 3)]
SEAT_BOT = [(-286, -73), (-261, -68), (-216, -55), (-148, -46), (-103, -43), (-35, -43), (56, -40), (124, -42),
            (158, -30)]
SEAT_PIVOT = (6.0, 0.0, 27.0)   # MEASURED side: the polished side pivot's centre (y, z) and radius

# Back. The frame's outer edge from the front, right half, bottom centre to the crown (x, z): the mean of the
# front and back photos (the front photo alone reads 4-5 % narrow: the back is behind the axis there).
BACK_OUT = [(0, -138), (70, -138), (125, -134), (162, -118), (181, -92), (188, -55), (190, -10), (191, 50),
            (193, 100), (197, 150), (209, 200), (223, 240), (239, 280), (255, 320), (266, 360), (270, 385),
            (268, 405), (260, 428), (245, 447), (222, 461), (180, 473), (127, 481), (60, 486), (0, 488)]
# The frame's front edge behind the axis, by height (MEASURED side): the lumbar bows forward at 100 to 150, the
# upper back leans about 20 degrees, the top bar hooks back
BACK_YF = [(-138, 178), (-100, 174), (-40, 168), (0, 162), (50, 150), (100, 143), (150, 144), (200, 149),
           (220, 157), (240, 165), (260, 173), (280, 182), (300, 188), (320, 195), (340, 200), (360, 204),
           (380, 209), (400, 216), (420, 225), (440, 238), (460, 251), (475, 266), (488, 283)]
BACK_CUP = [(-138, 6), (-60, 14), (50, 24), (150, 26), (300, 32), (420, 22), (488, 8)]   # the mesh behind the rails
TOP_SKEW = 0.55            # MEASURED side: the top bar's front edge sits 15 lower than its crown
POST_X, POST_Y = 181.0, 191.0     # MEASURED back/side: the polished posts the arms slide on
POST_Z = (-105.0, 142.0)
ARM_X = 287.0              # MEASURED front/back: the pad's centre (outer edge 340: 680 over both)
# The pad: stations along y (y, width, top, thickness): a thick drooping nose, a slim tail (MEASURED side)
PAD = [(-139, 46, 166, 24), (-129, 80, 181, 40), (-108, 100, 189, 50), (-70, 108, 191, 50), (-10, 110, 191, 49),
       (70, 110, 186, 45), (120, 104, 178, 38), (142, 84, 172, 30), (150, 50, 168, 22)]
# The tilt housing: stations along y (y, width, top, bottom) (MEASURED front/side)
MECH = [(-192, 150, -152, -190), (-180, 200, -146, -197), (-130, 212, -132, -198), (-85, 212, -119, -198),
        (-40, 212, -124, -200), (40, 212, -130, -200), (90, 190, -140, -182), (128, 150, -148, -156)]
MECH_BOTTOM = -200.0
STALK = (-152.0, -172.0)   # MEASURED side/front: the two side stalks' axis (y, z)
# Base (above the floor)
HUB_TOP = 209.0            # MEASURED side
COLUMN_R = 12.5            # MEASURED: the black column 24 to 27 across
LEG_R = (30.0, 322.0)      # the leg from the hub to where it turns down
LEG_TOP = (163.0, 121.0)   # MEASURED side: the leg's top edge at the hub and at the tip
LEG_SEC = ((44.0, 54.0), (27.0, 34.0))   # (width, height) at the root and the tip: a crowned shield
BOSS = (335.0, 17.0, 68.0, 124.0)        # the turned-down end: radius of its centre, its radius, bottom, top
WHEEL = (62.0, 17.0, 12.0)               # twin wheels: diameter, each one's width, the gap
TRAIL = 26.0               # the wheels trail the stem (all toward +Y, as if the chair was rolled to the desk)
SCREWS = [(248, 427), (-248, 427), (252, 337), (-252, 337), (192, 190), (-192, 190), (0, 478), (0, -113)]   # MEASURED back
LOGO = (30.0, 5.0)         # MEASURED back: the round mark is 20 across at z 438; our word 30 wide, cap 5
LOGO_Z = 440.0

PHOTOS = {
    "front": dict(photo=os.path.join(CUT, "front-cut.png"), title="Aeron: front (Herman Miller photo) vs our model",
                  camera={"mode": "fit", "view": "front", "tilts": [0.0, 4.0, 8.0]}, mask="alpha",
                  explain="a perspective product shot: the camera is searched; the fit is by silhouette only"),
    "side": dict(photo=os.path.join(CUT, "side-cut.png"), title="Aeron: side (Herman Miller photo) vs our model",
                 camera={"mode": "fit", "view": "right", "tilts": [0.0], "distances": [4.5, 6.0],
                         "heights": [-0.08, 0.0, 0.08]}, mask="alpha",
                 base_turn=18.0,
                 explain="a perspective shot with the base turned 18 degrees (a leg points at the camera); ours is turned 18 for this view"),
    "back": dict(photo=os.path.join(CUT, "back-cut.png"), title="Aeron: back (Herman Miller photo) vs our model",
                 camera={"mode": "fit", "view": "back", "tilts": [0.0, 4.0, 8.0]}, mask="alpha",
                 explain="a perspective product shot: the camera is searched"),
    "three-quarter-front": dict(photo=os.path.join(CUT, "three-quarter-front-cut.png"), mask="alpha",
                                title="Aeron: three-quarter front (Herman Miller photo) vs our model",
                                camera={"mode": "fit", "view": "front", "yaws": [-50.0, -42.0, -34.0],
                                        "tilts": [0.0, 6.0], "distances": [3.5, 5.0]},
                                explain="a turned perspective shot: the camera's distance, height, turn and tilt are searched"),
}


# ---------------------------------------------------------------------------
# 2. helpers
# ---------------------------------------------------------------------------
def hermite(table, x):
    """A smooth curve through a table of (x, value) pairs (cubic, Catmull-Rom tangents), clamped at the ends."""
    n = len(table)
    if x <= table[0][0]:
        return table[0][1]
    if x >= table[-1][0]:
        return table[-1][1]
    for i in range(n - 1):
        x0, v0 = table[i]
        x1, v1 = table[i + 1]
        if x <= x1:
            h = x1 - x0
            t = (x - x0) / h
            m0 = (v1 - table[i - 1][1]) / (x1 - table[i - 1][0]) if i > 0 else (v1 - v0) / h
            m1 = (table[i + 2][1] - v0) / (table[i + 2][0] - x0) if i + 2 < n else (v1 - v0) / h
            t2, t3 = t * t, t * t * t
            return (2 * t3 - 3 * t2 + 1) * v0 + (t3 - 2 * t2 + t) * h * m0 + (-2 * t3 + 3 * t2) * v1 + (t3 - t2) * h * m1
    return table[-1][1]


def lerp_table(table, x):
    if x <= table[0][0]:
        return table[0][1]
    for (x0, v0), (x1, v1) in zip(table, table[1:]):
        if x <= x1:
            return v0 + (v1 - v0) * (x - x0) / max(x1 - x0, 1e-9)
    return table[-1][1]


interp = lerp_table


def spline(pts, n, closed=False):
    """Catmull-Rom through pts (tuples of any length): n samples when closed, n + 1 when open."""
    P = [tuple(float(c) for c in p) for p in pts]
    m = len(P)

    def at(i):
        return P[i % m] if closed else P[min(max(i, 0), m - 1)]
    segs = m if closed else m - 1
    out = []
    for k in range(n if closed else n + 1):
        t = k / n * segs
        i = min(int(t), segs - 1)
        u = t - i
        out.append(tuple(0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u
                                + (-a + 3 * b - 3 * c + d) * u * u * u)
                         for a, b, c, d in zip(at(i - 1), at(i), at(i + 1), at(i + 2))))
    return out


def mirror_loop(half):
    """A closed loop from its right half (first and last points on the centre line)."""
    return list(half) + [(-p[0],) + tuple(p[1:]) for p in reversed(half[1:-1])]


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def sup(w, h, e, n, cu=0.0, cv=0.0):
    """A superellipse section (u, v), n points, CCW: e = 2 an ellipse, 4 a soft rounded rectangle."""
    out = []
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        c, s = math.cos(a), math.sin(a)
        out.append((cu + w / 2 * math.copysign(abs(c) ** (2 / e), c), cv + h / 2 * math.copysign(abs(s) ** (2 / e), s)))
    return out


def mats():
    from lib import materials as M
    d = {}

    def get(n, **v):
        d[n] = bpy.data.materials.get("mat_chair_" + n) or M.principled("mat_chair_" + n, **v)
        return d[n]
    get("mineral", base="#c9cccb", rough=0.6, spec=0.4)             # soft-touch pale grey plastic
    get("pad", base="#c2c5c5", rough=0.85, spec=0.3)                 # the arm pads and lumbar pads, a foam skin
    get("polished", base="#eef0f3", rough=0.06, metal=1.0)           # polished aluminium
    get("black", base="#1a1a1b", rough=0.55)                         # casters, the column, the posts' slots
    get("dark", base="#55585c", rough=0.5)                           # the PostureFit dial
    get("cast", base="#c3c6ca", rough=0.28, metal=1.0)               # the tilt housing: bright cast aluminium
    return d


def mesh_material(lite):
    """8Z Pellicle: pale grey, see-through, fine vertical threads crossed by sparser wefts whose density changes
    in bands (the eight zones). Rich: procedural threads (alpha, colour and a bump). Lite: a small tiling
    alpha-tested weave texture (alphaMode MASK)."""
    name = "mat_chair_weave" + ("_lite" if lite else "")
    m = bpy.data.materials.get(name)
    if m:
        return m
    from lib import materials as M
    m, nt, b = M._new(name)
    M._set(b, base="#b4b3ad", rough=0.45, spec=0.5, sheen=0.6, sheen_tint="#fff4e4")
    m.use_backface_culling = False
    N = nt.nodes

    def math_(op, a, bv=None, c=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, bv, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]
    if lite:
        im = weave_image()
        tex = N.new("ShaderNodeTexImage")
        tex.image = im
        tex.interpolation = "Linear"        # Closest exported a nearest-mip sampler that moires in three.js
        uv = N.new("ShaderNodeUVMap")
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (15.6, 15.6, 1.0)     # the 8-rib tile every 35 mm (4.4 mm ribs)
        nt.links.new(uv.outputs[0], mp.inputs[0])
        nt.links.new(mp.outputs[0], tex.inputs[0])
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(math_("GREATER_THAN", tex.outputs["Alpha"], 0.5), b.inputs["Alpha"])
        for attr, val in (("blend_method", "CLIP"), ("alpha_threshold", 0.5), ("surface_render_method", "DITHERED")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    else:
        # UV is metres / 0.55. Warps (the vertical ribs the photos show, about 22 in 100 mm) every 4.4 mm, 64 % of
        # the pitch; wefts every 2.2 mm, 36 to 60 % by zone: about a fifth open (at a quarter open the seat read
        # as a glass bowl with the tilt housing showing through), denser where the bands are
        uv = N.new("ShaderNodeUVMap")
        sep = N.new("ShaderNodeSeparateXYZ")
        nt.links.new(uv.outputs[0], sep.inputs[0])
        fu = math_("FRACT", math_("MULTIPLY", sep.outputs[0], 0.55 / 0.0044))
        fv = math_("FRACT", math_("MULTIPLY", sep.outputs[1], 0.55 / 0.0022))
        zone = math_("MULTIPLY_ADD", math_("SINE", math_("MULTIPLY", sep.outputs[1], 2 * math.pi * 0.55 / 0.14)), 0.12, 0.48)
        warp = math_("LESS_THAN", fu, 0.64)
        weft = math_("LESS_THAN", fv, zone)
        thread = math_("MAXIMUM", warp, weft)
        nt.links.new(thread, b.inputs["Alpha"])
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["A"].default_value = M.rgba("#84837f")           # wefts, darker: the ribs must read
        mix.inputs["B"].default_value = M.rgba("#c6c5bf")           # warps (the ribs)
        nt.links.new(warp, mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
        bump = N.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.4
        bump.inputs["Distance"].default_value = 0.0004
        nt.links.new(math_("ADD", warp, math_("MULTIPLY", weft, 0.5)), bump.inputs["Height"])
        nt.links.new(bump.outputs[0], b.inputs["Normal"])
        for attr, val in (("surface_render_method", "DITHERED"), ("blend_method", "HASHED")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    return m


def weave_image(px=32):
    """A tiling weave tile, 8 ribs across: 4 px pitch (2 thread, 2 gap), a weft every 8 px; holes transparent.
    (A denser band in half the tile read as horizontal stripes from across the room: removed 2026-11-12.)"""
    name = "chair_weave"
    im = bpy.data.images.get(name)
    if im:
        return im
    im = bpy.data.images.new(name, px, px, alpha=True)
    data = []
    for y in range(px):
        for x in range(px):
            warp = (x % 4) < 2
            weft = (y % 8) == 0
            shade = 0.72 if warp else 0.60
            data += [shade, shade - 0.005, shade - 0.03, 1.0 if (warp or weft) else 0.0]
    im.pixels = data
    im.pack()
    return im


class A:
    """One sub-assembly's bmesh (lib/parts.Mesh plus lofts and sweeps). Points are Vectors or tuples in mm."""

    def __init__(self):
        from lib import parts as P
        self.m = P.Mesh()
        self.P = P

    def ring(self, pts):
        return self.m.verts([Vector(p) * MM for p in pts])

    def loft(self, rings, key, closed=False, caps=True):
        """Join rings of points (mm, the same count each) into a skin."""
        vs = [self.ring(r) for r in rings]
        n = len(vs)
        for i in range(n if closed else n - 1):
            self.m.strip(vs[i], vs[(i + 1) % n], key)
        if caps and not closed:
            self.m.face(list(reversed(vs[0])), key)
            self.m.face(vs[-1], key)
        return vs

    def sweep(self, path, profs, key, across, closed=False, caps=True, dome=0.0):
        """Sweep sections along a path (mm). profs: one profile [(u, v)] or one per station; u lies along
        `across` (made perpendicular to the path), v along tangent x across. dome > 0 rounds both ends."""
        path = [Vector(p) for p in path]
        n = len(path)
        across = Vector(across)
        one = isinstance(profs[0][0], (int, float))
        rings = []
        for i, p in enumerate(path):
            if closed:
                t = (path[(i + 1) % n] - path[i - 1]).normalized()
            else:
                t = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
            a = (across - across.dot(t) * t).normalized()
            b = t.cross(a)
            pr = profs if one else profs[i]
            rings.append([p + u * a + v * b for u, v in pr])
        if dome and not closed:
            for end, sgn in ((0, -1), (-1, 1)):
                r0 = rings[end]
                c = sum(r0, Vector()) / len(r0)
                i0 = 0 if end == 0 else n - 1
                t = (path[min(i0 + 1, n - 1)] - path[max(i0 - 1, 0)]).normalized() * sgn
                extra = [[c + (q - c) * s + t * dome * d for q in r0] for s, d in ((0.82, 0.5), (0.45, 0.9))]
                if end == 0:
                    rings = list(reversed(extra)) + rings
                else:
                    rings = rings + extra
        return self.loft(rings, key, closed=closed, caps=caps)

    def lathe(self, prof, seg, key, m=None):
        return self.m.lathe([(r * MM, z * MM) for r, z in prof], seg, key, m)

    def disc(self, at, axis, prof, seg, key):
        """A lathe about `axis` through `at` (mm): prof [(r, h)] along the axis."""
        q = Vector(axis).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        return self.lathe(prof, seg, key, Matrix.Translation(Vector(at) * MM) @ q)

    def rbox(self, c, size, r, seg, key):
        """A rounded box centred at c (mm), size (x, y, z), corner radius r."""
        n0 = len(self.m.bm.verts)
        w, d, h = size
        self.P._rbox(self.m, w * MM, d * MM, h * MM, min(r, w / 2 - 0.5, d / 2 - 0.5) * MM,
                     min(r, h / 2 - 0.5) * MM, min(r, h / 2 - 0.5) * MM, seg, key, z0=-h / 2 * MM)
        self.m.bm.verts.ensure_lookup_table()
        bmesh.ops.translate(self.m.bm, verts=self.m.bm.verts[n0:], vec=Vector(c) * MM)

    def finish(self, name, mp, coll, parent=None, smooth=40, subsurf=0):
        bmesh.ops.recalc_face_normals(self.m.bm, faces=self.m.bm.faces)
        o = self.m.finish(name, mp, "+Z", (0, 0, 0), coll, parent, smooth=smooth)
        if subsurf:
            md = o.modifiers.new("subsurf", "SUBSURF")
            md.levels = md.render_levels = subsurf
        return o


def V(x, y, z):
    return Vector((x * MM, y * MM, z * MM))


def empty(name, coll, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type, e.empty_display_size = "ARROWS", 0.05
    coll.objects.link(e)
    e.parent = parent
    e.location = loc
    return e


def planar_uv(obj, ax, ay):
    """UVs in metres / 0.55 from two local axes (the weave's threads run along the second)."""
    me = obj.data
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (v[ax] / 0.55 + 0.5, v[ay] / 0.55 + 0.5)


# ---------------------------------------------------------------------------
# 3. sub-assemblies (the chair frame, mm; the upper parts relative to the seat datum)
# ---------------------------------------------------------------------------
_CACHE = {}


def _half_width(key, half, axis):
    """Half-width of a mirrored outline by its other coordinate (a table from a fine sampling of the loop)."""
    if key not in _CACHE:
        loop = spline(mirror_loop(half), 720, closed=True)
        tab = sorted((p[axis], p[0]) for p in loop if p[0] >= 0)
        out = []
        for v, x in tab:                      # keep the widest x where the loop doubles back on one value
            if out and abs(out[-1][0] - v) < 0.25:
                out[-1] = (out[-1][0], max(out[-1][1], x))
            else:
                out.append((v, x))
        _CACHE[key] = out
    return _CACHE[key]


def seat_hw(y):
    return lerp_table(_half_width("seat", SEAT_OUT, 1), y)


def seat_S(x, y):
    """The seat's saddle surface: the centre line sags, the side rails arch, the front falls away."""
    u = min(abs(x) / max(seat_hw(y), 1.0), 1.0)
    mid, side = hermite(SEAT_MID, y), hermite(SEAT_SIDE, y)
    return mid + (side - mid) * u ** 2.4


def seat_stations(n):
    """Stations round the frame: (point, outward normal, frame width)."""
    loop = spline(mirror_loop(SEAT_OUT), n, closed=True)
    out = []
    for i, p in enumerate(loop):
        a, b = loop[i - 1], loop[(i + 1) % n]
        t = Vector((b[0] - a[0], b[1] - a[1])).normalized()
        nrm = (t.y, -t.x)                       # the loop runs counter-clockwise from above
        w = 28 - 6 * max(-nrm[1], 0) ** 2 - 2 * max(nrm[1], 0) ** 2      # slimmest across the front: a thin lip
        out.append((p, nrm, w))
    return out


def build_seat(coll, mp, parent, rough=False, lite=False, sfx=""):
    names = []
    S = A()
    st = seat_stations(44 if lite else 96)
    rings = []
    for (x, y), n, w in st:
        sig = abs(n[0]) ** 1.5
        Sp = seat_S(x, y)

        def top(d):
            return seat_S(x - d * n[0], y - d * n[1])

        def under(d):                            # hollow under the side rails, a solid wedge under the lip
            return min(top(d) - 8, sig * (top(d) - 13) + (1 - sig) * hermite(SEAT_BOT, y - d * n[1]))
        zb = min(hermite(SEAT_BOT, y), Sp - 9)
        prof = [(w, top(w) - 1.0), (w * 0.55, top(w * 0.55) + 1.0), (9, top(9) + 0.6), (3.5, top(3.5) - 2.0),
                (0.8, Sp - 5), (0, Sp - 10), (0, zb + 5), (2.5, zb), (9, zb), (12, min(zb + 6, under(13))),
                (13.5, under(13.5)), (w - 5, under(w - 5)), (w, top(w) - 9)]
        if lite:
            prof = [prof[i] for i in (0, 2, 5, 7, 8, 10, 12)]
        rings.append([(x - d * n[0], y - d * n[1], z) for d, z in prof])
    S.loft(rings, "mineral", closed=True)
    obj = S.finish("chair_seat" + sfx, mp, coll, parent, smooth=38)      # no subdivision: it made the rim puffy
    names.append(obj.name)
    # the mesh: the same surface inside the frame, rings from the frame's inner edge to a centre point
    Mh = A()
    inner = [(x - (w - 4) * n[0], y - (w - 4) * n[1]) for (x, y), n, w in st]
    cx, cy = 0.0, -60.0
    nr = 4 if lite else 14
    vr = []
    for j in range(nr):
        rho = 1 - j / nr
        vr.append(Mh.ring([(cx + (x - cx) * rho, cy + (y - cy) * rho,
                            seat_S(cx + (x - cx) * rho, cy + (y - cy) * rho) - 1.5) for x, y in inner]))
    for a, b in zip(vr, vr[1:]):
        Mh.m.strip(a, b, "weave")
    c = Mh.ring([(cx, cy, seat_S(cx, cy) - 1.5)])[0]
    last = vr[-1]
    for i in range(len(last)):
        Mh.m.face([last[i], last[(i + 1) % len(last)], c], "weave")
    mesh = Mh.finish("chair_seat_mesh" + sfx, mp, coll, parent, smooth=80)
    mesh.data.materials.clear()
    mesh.data.materials.append(mesh_material(lite))
    planar_uv(mesh, 0, 1)
    names.append(mesh.name)
    return names


def back_hw(z):
    return lerp_table(_half_width("back", BACK_OUT, 1), z)


def back_stations(n):
    """Stations round the back frame: (x, z), the inward normal in the frame's plane, and the section's sizes:
    front bezel width, rear flange width, depth."""
    loop = spline(mirror_loop(BACK_OUT), n, closed=True)
    out = []
    for i, p in enumerate(loop):
        a, b = loop[i - 1], loop[(i + 1) % n]
        t = Vector((b[0] - a[0], b[1] - a[1])).normalized()
        m = (-t.y, t.x)                         # the loop runs counter-clockwise from the front
        bar = m[1] ** 2                         # 1 on the top and bottom bars, 0 on the side rails
        top = m[1] < 0
        up = smooth((p[1] - 150) / 90)
        wf = 15 + 4 * bar
        wr = (34 + 12 * up) * (1 - bar) + bar * (76 if top else 58)
        dep = (32 + 8 * up) * (1 - bar) + bar * (28 if top else 30)
        out.append((p, m, wf, wr, dep, bar if top else 0.0))
    return out


def back_y(x, z):
    """The mesh surface: just behind the bezel at the rails, cupped back in the middle."""
    u = min(abs(x) / max(back_hw(z) - 13, 1.0), 1.0)
    return hermite(BACK_YF, z) + 5 + hermite(BACK_CUP, z) * (1 - u * u)


def build_back(coll, mp, parent, rough=False, lite=False, sfx=""):
    names = []
    B = A()
    st = back_stations(48 if lite else 112)
    rings = []
    for (x, z), m, wf, wr, D, hook in st:
        y0 = hermite(BACK_YF, z)
        # the inner face: a slant on the side rails (a wedge); on the top bar it steps back behind the bezel,
        # leaving the rear flange as a lip that hangs down (the hook the side photo shows)
        lip = 9.5 + 4.5 * hook                  # the hanging lip is a thick rounded edge
        h5 = ((wf + 4 + wr - 2) / 2 * (1 - hook) + (wf + 9) * hook, (9 + D - lip) / 2 * (1 - hook) + (D - lip) * hook)
        if lite:
            prof = [(0, 0), (wf, 0), (wf + 3, 7), h5, (wr, D - 9), (wr, D), (0, D)]
        else:                                   # with the groove the mesh is splined into, a dark line in front
            prof = [(1.5, 0), (wf * 0.5, -1.0), (wf - 5.2, -0.3), (wf - 4.4, 3.0), (wf - 2.6, 3.0), (wf - 1.8, 0.3),
                    (wf + 1.5, 4), (wf + 4, 9), h5, (wr - 2, D - lip), (wr, D - 6), (wr - 1.5, D - 1.5), (wr - 5, D),
                    (4, D), (1, D - 2.5), (0, D - 6), (0, 5), (0.5, 1.5)]
        # the top bar's upper face is not level: it carries on up the back's lean to a crown at the rear
        rings.append([(x + (a + TOP_SKEW * hook * (D - b)) * m[0], y0 + b, z + (a + TOP_SKEW * hook * (D - b)) * m[1])
                      for a, b in prof])
    B.loft(rings, "mineral", closed=True)
    obj = B.finish("chair_back" + sfx, mp, coll, parent, smooth=28)      # creased corners: the real frame is crisp
    names.append(obj.name)
    # the mesh, from the bezel's inner edge to a centre point
    Mh = A()
    inner = [(x + (wf - 5 + TOP_SKEW * hook * (D - 5)) * m[0], z + (wf - 5 + TOP_SKEW * hook * (D - 5)) * m[1])
             for (x, z), m, wf, wr, D, hook in st]
    cx, cz = 0.0, 190.0
    nr = 4 if lite else 14
    vr = []
    for j in range(nr):
        rho = 1 - j / nr
        row = []
        for x, z in inner:
            px, pz = cx + (x - cx) * rho, cz + (z - cz) * rho
            # at the boundary the mesh meets the bezel; inside it follows the cupped surface
            row.append((px, back_y(px, pz) if j else hermite(BACK_YF, z) + 5, pz))
        vr.append(Mh.ring(row))
    for a, b in zip(vr, vr[1:]):
        Mh.m.strip(a, b, "weave")
    c = Mh.ring([(cx, back_y(cx, cz), cz)])[0]
    last = vr[-1]
    for i in range(len(last)):
        Mh.m.face([last[i], last[(i + 1) % len(last)], c], "weave")
    mesh = Mh.finish("chair_back_mesh" + sfx, mp, coll, parent, smooth=80)
    mesh.data.materials.clear()
    mesh.data.materials.append(mesh_material(lite))
    planar_uv(mesh, 0, 2)
    names.append(mesh.name)
    if rough:
        return names
    # PostureFit SL: the Y behind the mesh. Two arms from the rails' rear flanges to a stem that stands 90 mm
    # behind the lumbar; two pads press on the mesh; two small dials on the stem's rear, a larger one on its side
    Yp = A()
    k = 6 if lite else 12
    stem_y = [(-78, 243), (-50, 250), (0, 257), (60, 258), (130, 255)]
    for s in (-1, 1):
        root_z = 222
        ry = hermite(BACK_YF, root_z) + 36
        ctrl = [(s * 156, ry, root_z + 4, 64), (s * 138, ry + 8, root_z - 8, 34), (s * 105, ry + 22, 192, 30),
                (s * 55, 244, 158, 30), (0, 255, 128, 34)]
        pts = spline(ctrl, 4 if lite else 16)
        Yp.sweep([p[:3] for p in pts], [sup(16, p[3], 3.0, k) for p in pts], "mineral", across=(0, 1, 0))
    stem = [(-80, 26), (-60, 36), (-30, 50), (10, 72), (50, 82), (90, 60), (120, 40), (138, 34)]
    pts = spline(stem, 7 if lite else 24)
    Yp.sweep([(0, hermite(stem_y, z), z) for z, w in pts], [sup(14, w, 3.0, k) for z, w in pts], "mineral",
             across=(0, 1, 0), dome=6)
    for zc, w, h in ((180, 112, 104), (36, 86, 150)):       # the upper (lumbar) and lower (sacral) pads
        yc = back_y(0, zc) + 11
        for i, (sc, dy) in enumerate(((0.6, -5), (1.0, 0), (0.6, 7)) if lite else
                                     ((0.55, -6), (0.9, -3), (1.0, 2), (0.9, 6), (0.5, 8))):
            ring = [(u * sc, yc + dy, zc + v * sc) for u, v in sup(w, h, 3.0, k + 2 if lite else k + 4)]
            if i == 0:
                prev = Yp.ring(ring)
                Yp.m.face(list(reversed(prev)), "pad")
            else:
                cur = Yp.ring(ring)
                Yp.m.strip(prev, cur, "pad")
                prev = cur
        Yp.m.face(prev, "pad")
        y1 = hermite(stem_y, zc if zc < 130 else 128)
        Yp.sweep([(0, yc + 6, zc if zc < 130 else 150), (0, y1, zc if zc < 130 else 128)], sup(30, 22, 3.0, k),
                 "mineral", across=(1, 0, 0))                # the strut from the stem to the pad
    for s in (-1, 1):
        Yp.disc((s * 33, hermite(stem_y, -10) + 5, -10), (0, 1, 0), [(0, 0), (14, 0), (14, 9), (11, 12), (0, 12)],
                8 if lite else 24, "mineral")
    Yp.disc((34, 257, 0), (1, 0, 0), [(0, 0), (22, 0), (22, 10), (19, 13), (0, 13)], 10 if lite else 32, "dark")
    if not lite:
        # the frame's screws, where the back photo shows them: laid on the built rear face
        bpy.context.view_layer.update()
        oe = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        for sx, sz in SCREWS:
            ok, loc, nrm, _ = oe.ray_cast(V(sx, 600, sz), Vector((0, -1, 0)))
            if ok:
                at = loc / MM
                Yp.disc(at, (0, 1, 0), [(0, 0), (7, 0), (6.4, 0.7), (4.4, 0.7), (4.4, 0.2), (0, 0.2)], 20, "mineral")
                Yp.disc(at + Vector((0, 0.2, 0)), (0, 1, 0), [(0, 0), (4.2, 0), (3.6, 0.9), (0, 0.9)], 16, "dark")
    y = Yp.finish("chair_back_posturefit" + sfx, mp, coll, parent, smooth=50)
    names.append(y.name)
    return names


def build_arm(side, coll, mp, parent, rough=False, lite=False, sfx=""):
    s = 1 if side == "r" else -1
    R = A()
    k = 8 if lite else 16
    # the polished post on the back frame's rear, with two dark slots on its outer face
    path = [(s * POST_X, POST_Y + 6, POST_Z[0]), (s * POST_X, POST_Y + 2, POST_Z[0] + 40), (s * POST_X, POST_Y, 0),
            (s * POST_X, POST_Y + 2, 80), (s * POST_X, POST_Y + 8, POST_Z[1])]
    R.sweep(path, sup(34, 30, 4.0, k), "polished", across=(1, 0, 0), dome=8)
    if not lite:
        for z0, z1 in ((-80, -20), (20, 115)):
            x = s * (POST_X + 17.4)
            R.loft([[(x, POST_Y - 6, z0), (x, POST_Y + 6, z0), (x, POST_Y + 6, z1), (x, POST_Y - 6, z1)]], "black", caps=True)
    # the yoke that slides on the post, with the pale latch on its rear
    R.rbox((s * 226, POST_Y - 2, 22), (82, 52, 62), 16, 1 if lite else 4, "polished")
    R.rbox((s * 232, POST_Y + 26, 20), (22, 10, 40), 4, 1 if lite else 2, "mineral")
    # the cast horn (MEASURED side, zoomed): about 42 wide all the way, steep under the plate, flattening
    # into the yoke, flaring to 72 where it meets the plate; thin across
    ctrl = [(s * 258, 196, 18, 54), (s * 262, 180, 24, 52), (s * 266, 163, 30, 48), (s * 270, 138, 47, 44),
            (s * 274, 121, 66, 42), (s * 277, 110, 86, 40), (s * 279, 100, 108, 46), (s * 280, 88, 130, 72)]
    pts = spline(ctrl, 5 if lite else 24)
    R.sweep([p[:3] for p in pts], [sup(20, p[3], 2.6, k) for p in pts], "polished", across=(1, 0, 0))
    R.rbox((s * 281, 74, 136), (56, 110, 10), 4, 1 if lite else 3, "polished")           # the carrier plate
    # the pad: a soft slab, thick and drooping at the nose
    pst = PAD if lite else spline(PAD, 28)
    rings = []
    for y, w, zt, th in pst:
        rings.append([(s * ARM_X + u, y, zt - th / 2 + v) for u, v in sup(w, th, 3.4, k + 2)])
    R.loft(rings, "pad", caps=True)
    obj = R.finish(f"chair_arm_{side}" + sfx, mp, coll, parent, smooth=60, subsurf=0 if lite else 1)
    return [obj.name]


def build_mech(coll, mp, parent, rough=False, lite=False, sfx=""):
    Mc = A()
    k = 6 if lite else 16
    seg = 8 if lite else 32
    # the tilt housing: a cast bowl, and the pale cover over its front half
    pst = MECH if lite else spline(MECH, 24)
    Mc.loft([[(u, y, (zt + zb) / 2 + v) for u, v in sup(w, zt - zb, 4.0, k + 4)] for y, w, zt, zb in pst], "cast")
    cov = [(y, w + 5, zt + 3, zb + 8) for y, w, zt, zb in pst if y < -62]     # a wedge, taller toward the rear
    Mc.loft([[(u, y - 3, (zt + zb) / 2 + v) for u, v in sup(w, zt - zb, 4.0, k + 4)] for y, w, zt, zb in cov], "mineral")
    Mc.lathe([(0, MECH_BOTTOM - 24), (24, MECH_BOTTOM - 24), (36, MECH_BOTTOM + 4), (0, MECH_BOTTOM + 4)], seg, "cast")
    for sg in (-1, 1):
        # the polished link (MEASURED side, zoomed): a round 34 mm tube from the post's foot forward under the
        # seat at -116, then in, round a tight bend and down beside the housing; on +X it ends in the ball
        ctrl = [(sg * 181, 190, -70, 30), (sg * 184, 202, -98, 32), (sg * 192, 190, -112, 34), (sg * 205, 140, -114, 34),
                (sg * 214, 70, -116, 34), (sg * 216, 10, -117, 34), (sg * 206, -35, -118, 34), (sg * 182, -60, -122, 32),
                (sg * 160, -74, -140, 28), (sg * 151, -68, -166, 22), (sg * 150, -59, -186, 18)]
        pts = spline(ctrl, 8 if lite else 44)
        Mc.sweep([q[:3] for q in pts], [sup(q[3], q[3], 2.0, k) for q in pts], "polished", across=(0, 0, 1),
                 dome=0 if lite else 4)
        # the bracket up to the seat's side pivot, and the pivot's polished boss with its pale cap
        px = seat_hw(SEAT_PIVOT[0]) + 4
        bst = [(sg * 216, -106, 84), (sg * 232, -64, 66), (sg * 248, -30, 50), (sg * (px - 1), -4, 42)]
        Mc.sweep([(x, SEAT_PIVOT[0] + 2, z) for x, z, w in bst], [sup(14, w, 3.0, k) for x, z, w in bst], "polished",
                 across=(1, 0, 0))
        R = SEAT_PIVOT[2]
        Mc.disc((sg * (px - 6), SEAT_PIVOT[0], SEAT_PIVOT[1]), (sg, 0, 0),
                [(0, 0), (R, 0), (R, 13), (0, 16)] if lite else
                [(0, 0), (R, 0), (R, 12), (R - 5, 16), (15, 16), (13, 13), (0, 13)], seg, "polished")
        if not lite:
            Mc.disc((sg * (px + 7), SEAT_PIVOT[0], SEAT_PIVOT[1]), (sg, 0, 0), [(0, 0), (11, 0), (10, 2.5), (0, 2.5)],
                    seg, "mineral")
        # the lug the link ends in at the housing's side
        Mc.disc((sg * 100, -78, -160), (sg, 0, 0),
                [(0, 0), (16, 0), (16, 44), (0, 46)] if lite else [(0, 0), (16, 0), (16, 42), (13, 46), (0, 46)],
                seg, "polished")
    if not rough:
        y, z = STALK
        # -X: the tilt-tension stalk and its fat knob. +X: the slimmer tilt-limiter stalk with a collar
        Mc.disc((-98, y, z), (-1, 0, 0), [(0, 0), (10, 0), (10, 92), (20, 96), (21, 152), (0, 156)] if lite else
                [(0, 0), (14, 0), (14, 22), (10, 24), (10, 92), (20, 96), (21, 150), (17, 156), (0, 156)], seg, "mineral")
        Mc.disc((98, y, z), (1, 0, 0), [(0, 0), (8, 0), (8, 74), (13, 76), (13, 92), (8, 94), (9, 146), (0, 147)] if lite else
                [(0, 0), (12, 0), (12, 18), (8, 20), (8, 74), (13, 76), (13, 92), (8, 94), (8, 122), (12, 126), (12, 144),
                 (9, 147), (0, 147)], seg, "mineral")
        # +X: the ball the link's lever ends in
        n = 3 if lite else 10
        Mc.disc((150, -55, -193 - 23), (0, 0, 1), [(0, 0)] + [(23 * math.sin(math.pi * i / n), 23 - 23 * math.cos(math.pi * i / n))
                                                              for i in range(1, n)] + [(0, 46)], seg, "polished")
    obj = Mc.finish("chair_mech" + sfx, mp, coll, parent, smooth=50)
    return [obj.name]


def build_base(coll, mp, parent, rough=False, lite=False, sfx=""):
    """The hub, the five legs, the cylinder and the casters. Floor at z = 0, the cylinder's axis at the origin."""
    names = []
    seg = 12 if lite else 48
    Bs = A()
    Bs.lathe([(0, 98), (30, 98), (36, 104), (38, 118), (38, 150), (34, 166), (30, 172), (30, HUB_TOP - 4),
              (27, HUB_TOP), (0, HUB_TOP)], seg, "polished")
    Bs.lathe([(0, HUB_TOP), (21, HUB_TOP), (21, HUB_TOP + 4), (0, HUB_TOP + 4)], seg, "black")
    br, rr, bz0, bz1 = BOSS
    for i in range(5):
        a = -math.pi / 2 + 2 * math.pi * i / 5        # one leg straight forward (-Y)
        dirv = Vector((math.cos(a), math.sin(a), 0))
        n = 4 if lite else 14
        path, profs = [], []
        for j in range(n + 1):
            t = j / n
            r = LEG_R[0] + (LEG_R[1] - LEG_R[0]) * t
            w = LEG_SEC[0][0] + (LEG_SEC[1][0] - LEG_SEC[0][0]) * t
            h = LEG_SEC[0][1] + (LEG_SEC[1][1] - LEG_SEC[0][1]) * t
            path.append(dirv * r + Vector((0, 0, LEG_TOP[0] + (LEG_TOP[1] - LEG_TOP[0]) * t)))
            if lite:
                profs.append([(-0.15 * h, 0.5 * w), (0, 0.2 * w), (0, -0.2 * w), (-0.15 * h, -0.5 * w),
                              (-0.92 * h, -0.2 * w), (-0.92 * h, 0.2 * w)])
            else:                                     # a crowned top, shoulders, sides tucking under to a keel
                profs.append([(-0.18 * h, 0.5 * w), (-0.04 * h, 0.38 * w), (0, 0.15 * w), (0, -0.15 * w),
                              (-0.04 * h, -0.38 * w), (-0.18 * h, -0.5 * w), (-0.6 * h, -0.36 * w),
                              (-0.95 * h, -0.16 * w), (-h, 0), (-0.95 * h, 0.16 * w), (-0.6 * h, 0.36 * w)])
        # the leg runs on into the boss it turns down into
        path.append(dirv * (br - 2) + Vector((0, 0, LEG_TOP[1] - 4)))
        profs.append([(u * 0.9, v * 0.9) for u, v in profs[-1]])
        Bs.sweep(path, profs, "polished", across=(0, 0, 1))
        Bs.lathe([(0, bz0), (rr - 2, bz0), (rr, bz0 + 3), (rr, bz1 - 12), (rr - 3, bz1 - 4), (rr - 9, bz1), (0, bz1)],
                 8 if lite else 32, "polished", Matrix.Translation(dirv * br * MM))
    base = Bs.finish("chair_base" + sfx, mp, coll, parent, smooth=45)
    names.append(base.name)
    # the cylinder: the black column from the hub up into the tilt housing (trimmed in build())
    Cy = A()
    Cy.lathe([(0, HUB_TOP + 4), (COLUMN_R, HUB_TOP + 4), (COLUMN_R, 2000), (0, 2000)], 8 if lite else 24, "black")
    cyl = Cy.finish("chair_cylinder" + sfx, mp, coll, parent)
    names.append(cyl.name)
    # casters: twin wheels under a black hood, on a stem in the boss; all trail toward +Y
    wd, ww, gap = WHEEL
    for i in range(5):
        a = -math.pi / 2 + 2 * math.pi * i / 5
        stem = Vector((math.cos(a), math.sin(a), 0)) * br
        Cs = A()
        ws = 6 if lite else 32
        Cs.lathe([(0, 44), (13, 44), (13, bz0 - 5), (15, bz0 - 3), (15, bz0), (0, bz0)], ws, "black",
                 Matrix.Translation(stem * MM))                                  # the neck and its cap
        hood = Vector((stem.x, stem.y + TRAIL * 0.5, 0))
        Cs.lathe([(0, 30), (15, 33), (21, 42), (19, 52), (10, 58), (0, 59)], ws, "black", Matrix.Translation(hood * MM))
        axle = Vector((stem.x, stem.y + TRAIL, wd / 2))
        Cs.disc(axle - Vector((gap / 2 + 1, 0, 0)), (1, 0, 0), [(0, 0), (24, 0), (24, gap + 2), (0, gap + 2)], ws, "black")
        r = wd / 2
        for sg in (-1, 1):
            prof = [(0, 0), (r - 4, 0), (r - 1, 2), (r, 5), (r, ww - 5), (r - 1.5, ww - 2), (r - 5, ww),
                    (r - 9, ww - 1.5), (0, ww - 1.5)]
            if lite:            # no inner face (it is against the hub disc): rounder wheels for fewer triangles
                prof = [(r - 2, 0), (r, 3), (r, ww - 3), (0, ww - 1)]
            Cs.disc(axle + Vector((sg * gap / 2, 0, 0)), (sg, 0, 0), prof, 14 if lite else 40, "black")
        c = Cs.finish(f"chair_caster_{i + 1:02d}" + sfx, mp, coll, parent)
        names.append(c.name)
    return names


# ---------------------------------------------------------------------------
# 4. build
# ---------------------------------------------------------------------------
def build(rough=False, lite=False, collection=None, seat_h=None, parent=None):
    """Returns object names by role plus "all". The upper assembly (seat, back, arms, mechanism) is lifted to
    seat_h (mm, the seat datum above the floor; default the photos' 510)."""
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
    # the column's top is hidden in the tilt housing: trim it there
    cyl = bpy.data.objects["chair_cylinder" + sfx]
    top = (seat_h + MECH_BOTTOM + 15) * MM
    for v in cyl.data.vertices:
        if v.co.z > 1.0:
            v.co.z = top
    bpy.context.view_layer.update()
    if not rough:
        from lib import brands
        back = bpy.data.objects["chair_back" + sfx]
        # where the real round mark sits: the top bar's rear face, centre. The decal is laid on the built surface
        yr = hermite(BACK_YF, BACK_OUT[-1][1]) + 28
        d = brands.decal("chair", at=(0, (yr + 2) * MM, LOGO_Z * MM), normal=(0, 1, 0), up=(0, 0, 1),
                         height=LOGO[1] * MM, max_width=LOGO[0] * MM, finish="embossed", colour="#a2a6a6",
                         parent=back, collection=coll, conform=back, lite=lite, name="chair_brand" + sfx)
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
    """Plain Python (Pillow, numpy): the four photos as alpha cutouts in CUT; the photos are never touched.
    2026-11-12: the casters' floor reflections are cut away (below the far casters' feet only the black wheels are
    kept: the reflections are grey), and the weave's speckle is closed (a 7 px closing) so the mesh counts as
    solid, as it does in our silhouette."""
    import numpy as np
    from PIL import Image, ImageFilter
    os.makedirs(CUT, exist_ok=True)
    for n, zone in (("front", 2117), ("side", 2135), ("back", 2141), ("three-quarter-front", 2180)):
        im = Image.open(os.path.join(REF, n + ".jpg")).convert("RGB")
        a = np.asarray(im) / 255.0
        lum = a.mean(-1)
        k = lum < 0.93
        ys = np.arange(a.shape[0])[:, None]
        k &= ~((ys > zone) & (lum > 0.36))
        m = Image.fromarray((k * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))
        m = np.asarray(m) > 127
        m &= ~((ys > zone) & (lum > 0.5))
        Image.fromarray(np.dstack([a * 255, m * 255]).astype(np.uint8), "RGBA").save(os.path.join(CUT, n + "-cut.png"))
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
    from lib.blendfile import pack_and_save
    pack_and_save(blend, compress=True)
    with open(os.path.join(out, f"{NAME}-names.json"), "w") as f:
        json.dump(names, f, indent=1)
    tris = sum(sum(len(p.vertices) - 2 for p in bpy.data.objects[n].data.polygons) for n in names["all"]
               if bpy.data.objects[n].type == "MESH")
    log(f"built in {time.time() - t:.1f} s, {tris} triangles, saved {blend}")
    progress(f"build: {tris} triangles in {time.time() - t:.1f} s")
    return names


def white_studio(strength=1.0):
    """The photos' white studio: a bright, even world with a darker band at the horizon (what gives the polished
    parts their dark streaks), a soft key from the front-left, a rim and a top light. The camera sees a plain pale
    backdrop. Built once; lib/compare.ensure_studio() then leaves the scene's lights alone."""
    sc = bpy.context.scene
    if bpy.data.objects.get("chair_key"):
        return
    w = sc.world or bpy.data.worlds.new("World")
    sc.world = w
    try:
        w.use_nodes = True
    except AttributeError:
        pass
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    mp = nt.nodes.new("ShaderNodeMapRange")
    mp.inputs["From Min"].default_value, mp.inputs["From Max"].default_value = -1.0, 1.0
    nt.links.new(geo.outputs["Incoming"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mp.inputs["Value"])
    nt.links.new(mp.outputs[0], ramp.inputs["Fac"])
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, (0.55, 0.55, 0.57, 1)
    el[1].position, el[1].color = 1.0, (1.0, 1.0, 1.0, 1)
    for pos, c in ((0.44, 0.50), (0.5, 0.10), (0.56, 0.80)):
        e = el.new(pos)
        e.color = (c, c, c * 1.02, 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    cam = nt.nodes.new("ShaderNodeBackground")
    cam.inputs["Color"].default_value = (0.86, 0.87, 0.90, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.42 * strength
    nt.links.new(bg.outputs[0], mix.inputs[1])
    nt.links.new(cam.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    coll = bpy.data.collections.get("cmp_studio") or bpy.data.collections.new("cmp_studio")
    if coll.name not in sc.collection.children:
        sc.collection.children.link(coll)
    for nm, loc, e in (("chair_key", (-2.2, -2.8, 2.6), 300), ("chair_rim", (2.0, 2.6, 2.2), 180),
                       ("chair_top", (0.0, 0.0, 3.4), 60)):
        d = bpy.data.lights.new(nm, "AREA")
        d.size, d.energy = 2.5, e * strength
        o = bpy.data.objects.new(nm, d)
        coll.objects.link(o)
        o.location = loc
        o.rotation_euler = (-Vector(loc) + Vector((0, 0, 0.6))).to_track_quat("-Z", "Y").to_euler()


def _studio(sc, cycles, strength=1.0):
    white_studio(strength)
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
    _studio(sc, cycles, 1.0)
    lo, hi = compare.world_bbox(names["all"])
    c, size = (lo + hi) / 2, hi - lo
    cams = {"hero": backdrops.three_quarter_camera(c, max(size) * 1.25, az=-35, el=14, name="still_hero"),
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
    yb = hermite(BACK_YF, 200) * MM
    yr = (hermite(BACK_YF, BACK_OUT[-1][1]) + 28) * MM
    return [
        ("seat-side", "Aeron: the seat from the side (the waterfall, the arched rail)", os.path.join(REF, "side.jpg"),
         (2.2, -0.06, s + 0.02), (0.0, -0.06, s - 0.03), 110),
        ("back-frame", "Aeron: the back frame and the weave", os.path.join(REF, "three-quarter-back.jpg"),
         (0.55, 0.95, s + 0.45), (0.12, yb, s + 0.30), 50),
        ("posturefit", "Aeron: the PostureFit SL Y", os.path.join(REF, "back.jpg"),
         (0.05, 1.10, s + 0.22), (0.0, yb, s + 0.10), 50),
        ("arm", "Aeron: an arm: pad, blade, yoke and post", os.path.join(REF, "detail-arms-1.jpg"),
         (0.85, -0.30, s + 0.30), (0.27, 0.05, s + 0.10), 50),
        ("seat-front", "Aeron: the seat's waterfall front edge", os.path.join(REF, "three-quarter-front.jpg"),
         (-0.65, -0.65, s + 0.18), (-0.05, -0.18, s - 0.03), 50),
        ("mech", "Aeron: the tilt mechanism, link and levers", os.path.join(REF, "three-quarter-front.jpg"),
         (0.62, -0.45, s - 0.05), (0.06, -0.02, s - 0.14), 50),
        ("base", "Aeron: the polished base and a caster", os.path.join(REF, "three-quarter-front.jpg"),
         (0.50, -0.80, 0.32), (0.08, -0.14, 0.10), 50),
        ("logo", "Aeron: the mark on the top bar (ours: the name from content)", os.path.join(REF, "back.jpg"),
         (0.0, yr + 0.42, s + LOGO_Z * MM + 0.02), (0.0, yr, s + LOGO_Z * MM), 85),
    ]


def stage_closeups(out, names, cycles=False, only=None):
    sc = bpy.context.scene
    _studio(sc, cycles, 1.0)
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


def before_after(out=None):
    """Plain Python (Pillow): the 2026-10-28 chair's stills beside the rebuild's, same cameras, one sheet."""
    from PIL import Image, ImageDraw, ImageFont
    out = out or FOOT
    old = os.path.join(REPO, "video-local", "footage", "2026-10-28-components", "chair")
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except OSError:
        font = ImageFont.load_default()
    W, H, pad, head = 960, 540, 12, 44
    views = [("side", "side"), ("hero", "three-quarter"), ("front", "front"), ("back", "back")]
    sheet = Image.new("RGB", (2 * W + 3 * pad, head + len(views) * (H + pad)), (245, 244, 240))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 8), "before: the chair of 2026-10-28", fill=(30, 30, 34), font=font)
    d.text((W + 2 * pad, 8), "after: the rebuild of 2026-11-12 (same cameras)", fill=(30, 30, 34), font=font)
    for r, (k, label) in enumerate(views):
        for c, folder in enumerate((old, out)):
            f = os.path.join(folder, f"{NAME}-{k}.png")
            if not os.path.exists(f):
                continue
            im = Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS)
            sheet.paste(im, (pad + c * (W + pad), head + r * (H + pad)))
        d.text((pad + 10, head + r * (H + pad) + 8), label, fill=(60, 60, 70), font=font)
    path = os.path.join(out, "chair-before-after.jpg")
    sheet.save(path, quality=88)
    print("BEFORE-AFTER", path)
    return path


def stage_compare(out, names):
    from lib import compare
    white_studio(1.0)
    rep = compare.run(outline_views(names), os.path.join(out, "compare"), NAME, look_samples=48, log=log)
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


def bake_lite(objs, out, size=768, orm_size=512):     # 768: the chair is flat colours; 1024 put the lite over its byte ceiling
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
    scene.cycles.device = "CPU"      # a small bake; the Metal device prefs crash under --factory-startup
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
    for im, fn, q in ((base, "chair_atlas.jpg", 80), (orm, "chair_orm.jpg", 85)):
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
    elif "--beforeafter" in sys.argv:
        before_after()
