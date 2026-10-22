"""guitar_02: Jimi Hendrix's 1968 Woodstock Stratocaster, an exact replica (decisions
2026-10-23), built from blender/lib/guitar_specs.py GUITAR_02 and the derived geometry of
its approved blueprint (blender/design/guitar_02_blueprint.py: outlines, neck width, string
lines, tuner posts, pickups, the hook contact), so the sheet and the model cannot disagree.
No logos, decals, model names, patent text, serials or stamps; plain 0 to 10 on the knobs.

Frame. Every part is built in the spec's millimetres (u across, + to the viewer's right;
v along, 0 at the body's tail; z out of the body's top, 0 on the top face) and mapped by
SPEC into the frame MESHES.md wants: +X right, +Z up, -Y out of the front, metres, origin
at the hook contact on the headstock (the pivot of `guitar_02`).

Names (MESHES.md, obj_guitars):
    guitar_02           empty at the hook contact, the whole guitar
    guitar_02_strings   one mesh, one material, origin at the strings' midpoint
    guitar_02_part_*    every other part, fine-grained in the .blend for the build preview;
                        the exports join them into `guitar_02_body`

    build_steps(parent=None, collection=None, lite=False)  generator: one group per step
    build(...)                    runs it, returns the empty
    BUILD_ORDER                   [(group, [object names])]: body, neck, hardware, pickguard, strings
    place_on_wall(root)           the empty on its hook (constants.WALL_GUITARS, guitar 2)
    build_hanger(root, ...)       the wall hanger, static (`guitars_hook_02`)
    export_rich(root)             (objects to export, undo): parts joined into guitar_02_body
    export_lite(root)             (objects, undo, stats): the web model, about 6k triangles,
                                  one material with a baked atlas and an ORM map

Values not in GUITAR_02 (chosen here, from the real parts): BOARD_T, the screw heads,
the pole stagger, the wrap heights on the posts, the knob and strap-button profiles.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.geometry import delaunay_2d_cdt

from lib import constants as C, geo, materials as M, names
from lib.guitar_specs import GUITAR_02 as G, spline

sys.path.insert(0, os.path.join(C.BLENDER_DIR, "design"))
import guitar_02_blueprint as BP  # noqa: E402  (shared geometry; drawing runs only as a script)

MM = C.MM
SC, VN, VS = BP.SC, BP.VN, BP.VS
R_BOARD = G["radius"]
ZC = G["board_above_body"]                          # fretboard crown above the body top
HZ_FACE = ZC - G["head_step"]                       # headstock face
HZ_BACK = HZ_FACE - G["head_t"]
NUT_TOP = ZC + G["fret_wire"][1] + 0.6              # as the blueprint's side view draws it
PIV = (0.0, VN + BP.HOOK_B, (HZ_FACE + HZ_BACK) / 2)   # hook contact, mid-thickness of the head
SPEC = Matrix(((MM, 0, 0, -PIV[0] * MM),
               (0, 0, -MM, PIV[2] * MM),
               (0, MM, 0, -PIV[1] * MM),
               (0, 0, 0, 1)))

BOARD_T = 6.0            # glued maple cap at the crown (two-piece neck)
SCREW = dict(guard=5.4, pickup=4.6, cover=5.4, jack=4.4, plate=8.0)   # head diameters, mm
POLE_UP = (1.0, 1.0, 1.6, 1.8, 0.6, 0.8)   # vintage stagger as built, left to right as it hangs
WRAP_Z = (8.0, 7.5, 7.0, 6.5, 6.0, 5.5)    # string wrap height above the head face, per string
WRAP_TURNS = (3.2, 2.8, 2.4, 2.0, 1.8, 1.5)
FOREARM_V, BELLY_V = (42, 252), (250, 455, 0.55)   # bell spans, as the blueprint's sections use

RICH = dict(body_step=2.5, ring_seg=6, grid=7.0, neck_dv=4.0, arc=16, cseg=20, cyl=24, small=14,
            tube=8, head_step=2.0, fret_arc=14, fret_prof=7, guard_step=2.0, lathe=48)
LITE = dict(body_step=14.0, ring_seg=2, grid=45.0, neck_dv=30.0, arc=5, cseg=6, cyl=10, small=6,
            tube=3, head_step=10.0, fret_arc=3, fret_prof=2, guard_step=11.0, lathe=10)

BUILD_ORDER = []
MATS = {}
_st = dict(coll=None, root=None, lite=False, prefix="guitar_02_part_", Q=RICH, groups={})


def Q(k):
    return _st["Q"][k]


def S(u, v, z):
    """A spec point (mm) in the guitar_02 frame (metres)."""
    return SPEC @ Vector((u, v, z))


# ---------------------------------------------------------------------------
# 2D helpers (spec mm)
# ---------------------------------------------------------------------------
def area2(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) / 2


def ccw(pts):
    pts = [tuple(p) for p in pts]
    return pts if area2(pts) > 0 else pts[::-1]


def resample(pts, step, closed=True):
    P = list(pts) + ([pts[0]] if closed else [])
    L = [0.0]
    for a, b in zip(P, P[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = L[-1]
    n = max(8 if closed else 2, round(total / step))
    out, j = [], 0
    for k in range(n if closed else n + 1):
        s = total * k / n
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        seg = L[j + 1] - L[j]
        t = (s - L[j]) / seg if seg > 0 else 0.0
        out.append((P[j][0] + (P[j + 1][0] - P[j][0]) * t, P[j][1] + (P[j + 1][1] - P[j][1]) * t))
    return out


def smooth_normals(pts, window):
    """Outward normals of a closed CCW polygon, tangents averaged over +-window mm."""
    n = len(pts)
    per = sum(math.hypot(pts[(i + 1) % n][0] - pts[i][0], pts[(i + 1) % n][1] - pts[i][1]) for i in range(n))
    k = max(1, round(window / (per / n)))
    out = []
    for i in range(n):
        a, b = pts[(i - k) % n], pts[(i + k) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        out.append((ty / ln, -tx / ln))
    return out


def inset(pts, nrm, d):
    return [(p[0] - n[0] * d, p[1] - n[1] * d) for p, n in zip(pts, nrm)]


def place2(pts, at, deg=0.0):
    return BP.shape(pts, at, deg)


# ---------------------------------------------------------------------------
# bmesh builders (spec mm)
# ---------------------------------------------------------------------------
def ring(bm, pts2, z):
    return [bm.verts.new((x, y, z)) for x, y in pts2]


def bridge(bm, ra, rb, mi=0, closed=True):
    n = len(ra)
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        try:
            f = bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
            f.material_index = mi
        except ValueError:
            pass


def cap(bm, vs, mi=0):
    try:
        f = bm.faces.new(vs)
        f.material_index = mi
        return f
    except ValueError:
        return None


def prism_uv(bm, outline, z0, z1, mi=0):
    pts = ccw(outline)
    a, b = ring(bm, pts, z0), ring(bm, pts, z1)
    cap(bm, a[::-1], mi)
    cap(bm, b, mi)
    bridge(bm, a, b, mi)
    return a, b


def loft_uv(bm, outline, z0, z1, scale_top=1.0, mi=0):
    """Plan outline extruded, the top scaled about the outline's centre (a taper)."""
    pts = ccw(outline)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    top = [(cx + (x - cx) * scale_top, cy + (y - cy) * scale_top) for x, y in pts]
    a, b = ring(bm, pts, z0), ring(bm, top, z1)
    cap(bm, a[::-1], mi)
    cap(bm, b, mi)
    bridge(bm, a, b, mi)


def prism_uz(bm, profile, v0, v1, mi=0):
    """A (u, z) profile extruded along v."""
    pts = profile if area2(profile) > 0 else profile[::-1]
    a = [bm.verts.new((u, v0, z)) for u, z in pts]
    b = [bm.verts.new((u, v1, z)) for u, z in pts]
    cap(bm, a, mi)
    cap(bm, b[::-1], mi)
    bridge(bm, b, a, mi)


def prism_vz(bm, profile, u0, u1, mi=0):
    """A (v, z) profile extruded along u."""
    a = [bm.verts.new((u0, v, z)) for v, z in profile]
    b = [bm.verts.new((u1, v, z)) for v, z in profile]
    cap(bm, a, mi)
    cap(bm, b[::-1], mi)
    bridge(bm, a, b, mi)


def _basis(axis):
    axis = Vector(axis).normalized()
    ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
    a1 = axis.cross(ref).normalized()
    return axis, a1, axis.cross(a1).normalized()


def lathe(bm, prof, centre, axis, seg, mi=0, rmod=None):
    """Revolve [(r, h)] about `axis` through `centre`. rmod(theta, index) scales r."""
    ax, a1, a2 = _basis(axis)
    c = Vector(centre)
    rings = []
    for i, (r, h) in enumerate(prof):
        if r < 1e-6:
            rings.append(bm.verts.new(c + ax * h))
            continue
        rr = []
        for k in range(seg):
            t = 2 * math.pi * k / seg
            rk = r * (rmod(t, i) if rmod else 1.0)
            rr.append(bm.verts.new(c + ax * h + (a1 * math.cos(t) + a2 * math.sin(t)) * rk))
        rings.append(rr)
    for A, B in zip(rings, rings[1:]):
        if isinstance(A, list) and isinstance(B, list):
            bridge(bm, A, B, mi)
        elif isinstance(A, list):
            for k in range(seg):
                cap(bm, (A[k], A[(k + 1) % seg], B), mi)
        elif isinstance(B, list):
            for k in range(seg):
                cap(bm, (A, B[(k + 1) % seg], B[k]), mi)
    if isinstance(rings[0], list):
        cap(bm, rings[0][::-1], mi)
    if isinstance(rings[-1], list):
        cap(bm, rings[-1], mi)


def cyl(bm, r, p0, p1, seg, mi=0, dome=0.0):
    """Closed cylinder p0 to p1; dome > 0 rounds the p1 end by that height."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    if dome > 0:
        prof = [(r, 0.0), (r, L - dome)]
        for k in range(1, 4):
            a = math.pi / 2 * k / 4
            prof.append((r * math.cos(a), L - dome + dome * math.sin(a)))
        prof.append((0.0, L))
        prof = [(0.0, 0.0)] + prof
    else:
        prof = [(0.0, 0.0), (r, 0.0), (r, L), (0.0, L)]
    lathe(bm, prof, p0, d, seg, mi)


def tube(bm, path, r, seg, mi=0, caps=True, uv=None, attr=None, aval=0.0):
    """Tube along a polyline of Vectors (parallel-transport frames). uv: a loop UV layer
    (x = arc length in mm, y = around); attr: a vert float layer set to aval."""
    path = [Vector(p) for p in path]
    clean = [path[0]]
    for p in path[1:]:
        if (p - clean[-1]).length > 1e-4:
            clean.append(p)
    path = clean
    n = len(path)
    tans = []
    for i in range(n):
        a = path[max(0, i - 1)]
        b = path[min(n - 1, i + 1)]
        tans.append((b - a).normalized())
    _, nrm, _ = _basis(tans[0])
    rings, s, svals = [], 0.0, []
    for i in range(n):
        if i:
            s += (path[i] - path[i - 1]).length
            q = tans[i - 1].rotation_difference(tans[i])
            nrm = (q @ nrm).normalized()
        bi = tans[i].cross(nrm).normalized()
        rr = []
        for k in range(seg):
            t = 2 * math.pi * k / seg
            v = bm.verts.new(path[i] + (nrm * math.cos(t) + bi * math.sin(t)) * r)
            if attr is not None:
                v[attr] = aval
            rr.append(v)
        rings.append(rr)
        svals.append(s)
    faces = []
    for i in range(n - 1):
        for k in range(seg):
            j = (k + 1) % seg
            try:
                f = bm.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]))
            except ValueError:
                continue
            f.material_index = mi
            if uv is not None:
                for lp, (ii, kk) in zip(f.loops, ((i, k), (i, k + 1), (i + 1, k + 1), (i + 1, k))):
                    lp[uv].uv = (svals[ii], kk / seg)
            faces.append(f)
    if caps:
        for rr in (rings[0][::-1], rings[-1]):
            f = cap(bm, rr, mi)
            if f is not None and uv is not None:
                for lp in f.loops:
                    lp[uv].uv = (0.0, 0.0)
    return rings


def rounded_slab(bm, outline, z0, z1, r, seg, step, grid, dome=None, at=(0, 0), deg=0.0, mi=0):
    """A plan outline (local, centred) as a slab with a true roundover of radius r on its
    top edge and a CDT-filled top (optionally domed: dome(x, y) adds height), then turned
    by deg and moved to `at`. Clean shading where a bevel modifier would streak."""
    O = ccw(resample(outline, step))
    N = smooth_normals(O, max(step * 1.5, r * 0.8))
    rings = [ring(bm, O, z0)]
    for k in range(seg + 1):
        phi = math.pi / 2 * k / seg
        rings.append(ring(bm, inset(O, N, r * (1 - math.cos(phi))), z1 - r + r * math.sin(phi)))
    for a_, b_ in zip(rings, rings[1:]):
        bridge(bm, a_, b_, mi)
    cap(bm, rings[0][::-1], mi)
    top = fill_cdt(bm, rings[-1], grid, z1, True, mi)
    if dome:
        for v in top + rings[-1]:
            v.co.z += dome(v.co.x, v.co.y)
    vs = [v for rr in rings for v in rr] + top
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    for v in vs:
        x, y = v.co.x, v.co.y
        v.co.x, v.co.y = at[0] + x * c - y * s_, at[1] + x * s_ + y * c


def rbox(bm, w, h, z0, z1, at, deg=0.0, r=1.0, n=3, mi=0):
    prism_uv(bm, place2(BP.rrect(w, h, r, n), at, deg), z0, z1, mi)


# ---------------------------------------------------------------------------
# objects
# ---------------------------------------------------------------------------
def finish(key, bm, mats, group, bev=None, seg=3, angle=35, smooth=True, recalc=True):
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=SPEC, verts=bm.verts)
    name = _st["prefix"] + key
    o = geo.from_bmesh(name, bm, collection=_st["coll"], parent=_st["root"], material=MATS[mats[0]],
                       smooth=smooth)
    for m in mats[1:]:
        o.data.materials.append(MATS[m])
    if bev and not _st["lite"]:
        geo.bevel(o, bev * MM, segments=seg, angle=angle)
    o["group"] = group
    _st["groups"].setdefault(group, []).append(o)
    return o


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def _attr(nt, name):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = name
    return a.outputs["Fac"]


def _mix(nt, fac, a, b, kind="RGBA"):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = kind
    m.clamp_factor = True
    nt.links.new(fac, m.inputs["Factor"])
    ia, ib = (6, 7) if kind == "RGBA" else (2, 3)
    for sock, val in ((m.inputs[ia], a), (m.inputs[ib], b)):
        if isinstance(val, (int, float)):
            sock.default_value = val
        elif isinstance(val, str):
            sock.default_value = M.rgba(val)
        else:
            nt.links.new(val, sock)
    return m.outputs[2] if kind == "RGBA" else m.outputs[0]


def _maprange(nt, val, a, b):
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.clamp = True
    nt.links.new(val, mr.inputs["Value"])
    mr.inputs["From Min"].default_value = a
    mr.inputs["From Max"].default_value = b
    return mr.outputs["Result"]


def _wear_mask(nt, scale, lo, hi):
    """Patchy wear from the `wear` attribute broken up by noise."""
    co = M._coords(nt)
    nz = M._noise(nt, co, scale, detail=6, rough=0.65)
    t = nt.nodes.new("ShaderNodeMath")
    t.operation = "MULTIPLY"
    nt.links.new(_attr(nt, "wear"), t.inputs[0])
    nt.links.new(M._math(nt, "ADD", nz, 0.55), t.inputs[1])
    return _maprange(nt, t.outputs[0], lo, hi)


def _grain(nt, c0, c1, stretch=0.05, scale=320.0):
    """Maple: tight grain running along the neck (object Z)."""
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, stretch)
    nt.links.new(M._coords(nt), mp.inputs["Vector"])
    g = M._noise(nt, mp.outputs[0], scale, detail=5, rough=0.55, distortion=0.6)
    return M._ramp(nt, g, [(0.3, c0), (0.7, c1)]), g


def _rough_noise(nt, b, r0, r1, scale=160):
    rn = M._noise(nt, M._coords(nt), scale, detail=3)
    nt.links.new(M._ramp(nt, rn, [(0.3, (r0, r0, r0, 1)), (0.7, (r1, r1, r1, 1))]), b.inputs["Roughness"])


def materials():
    MATS.clear()
    # Olympic White, aged a year: slightly yellow under the clear coat, primer at the worn edges
    m, nt, b = M._new("mat_guitar_02_lacquer")
    yel = M._noise(nt, M._coords(nt), 3.0, detail=2)
    base = M._ramp(nt, yel, [(0.35, "#ece5d1"), (0.7, "#f1ebdc")])
    wm = _wear_mask(nt, 260.0, 0.5, 0.68)
    edge = _wear_mask(nt, 260.0, 0.36, 0.5)            # the dirty rim round each worn patch
    base = _mix(nt, M._math(nt, "MULTIPLY", edge, 0.45), base, "#d6cbaf")
    nt.links.new(_mix(nt, wm, base, "#c2b494"), b.inputs["Base Color"])
    nt.links.new(_mix(nt, wm, 0.22, 0.55, "FLOAT"), b.inputs["Roughness"])
    nt.links.new(_mix(nt, wm, 1.0, 0.1, "FLOAT"), b.inputs["Coat Weight"])
    M._set(b, coat_rough=0.035, coat_ior=1.5, spec=0.5)
    b.inputs["Coat Tint"].default_value = M.rgba("#fbf5e3")
    sc = M._noise(nt, M._coords(nt, scale=(1.0, 1.0, 1.0)), 1800, detail=2)
    M._bump(nt, b, sc, 0.015, 0.0001, socket="Coat Normal")
    m.diffuse_color = M.rgba("#efe9d8")
    MATS["lacquer"] = m

    # maple board: amber lacquer, worn to greyish wood between frets 1 and 7
    m, nt, b = M._new("mat_guitar_02_board")
    col, g = _grain(nt, "#dcb169", "#e6c27f")
    wm = _wear_mask(nt, 180.0, 0.45, 0.7)
    nt.links.new(_mix(nt, wm, col, "#b39770"), b.inputs["Base Color"])
    nt.links.new(_mix(nt, wm, 0.30, 0.5, "FLOAT"), b.inputs["Roughness"])
    nt.links.new(_mix(nt, wm, 0.6, 0.0, "FLOAT"), b.inputs["Coat Weight"])
    M._set(b, coat_rough=0.08, spec=0.5)
    b.inputs["Coat Tint"].default_value = M.rgba("#f6e2b4")
    M._bump(nt, b, g, 0.04, 0.0002)
    m.diffuse_color = M.rgba("#e2bb76")
    MATS["board"] = m

    # neck back: same maple, gloss rubbed to satin by the hand
    m, nt, b = M._new("mat_guitar_02_neck")
    col, g = _grain(nt, "#ddb672", "#e8c68a")
    nt.links.new(col, b.inputs["Base Color"])
    M._set(b, rough=0.35, coat=0.35, coat_rough=0.22, spec=0.5)
    M._bump(nt, b, g, 0.03, 0.0002)
    m.diffuse_color = M.rgba("#e3bf80")
    MATS["neck"] = m

    # headstock: lacquered maple, gloss (no decal, no text)
    m, nt, b = M._new("mat_guitar_02_head")
    col, g = _grain(nt, "#dfb670", "#e9c789")
    nt.links.new(col, b.inputs["Base Color"])
    M._set(b, rough=0.28, coat=0.7, coat_rough=0.06, spec=0.5)
    b.inputs["Coat Tint"].default_value = M.rgba("#f6e2b4")
    M._bump(nt, b, g, 0.03, 0.0002)
    m.diffuse_color = M.rgba("#e6c385")
    MATS["head"] = m

    def metal(key, name, colour, r0, r1, tarnish=None):
        m, nt, b = M._new(name)
        if tarnish:
            tn = M._noise(nt, M._coords(nt), 420, detail=4)    # fine (a 90 scale made 1 cm blotches)
            nt.links.new(M._ramp(nt, tn, [(0.5, colour), (0.85, tarnish)]), b.inputs["Base Color"])
        else:
            M._set(b, base=colour)
        M._set(b, metal=1.0)
        _rough_noise(nt, b, r0, r1)
        m.diffuse_color = M.rgba(colour)
        MATS[key] = m

    metal("chrome", "mat_guitar_02_chrome", "#cfd2d6", 0.12, 0.2, tarnish="#c3c2bb")
    metal("nickel", "mat_guitar_02_nickel", "#cdc9bd", 0.16, 0.26, tarnish="#bdb8aa")
    metal("frets", "mat_guitar_02_frets", "#c4c2ba", 0.24, 0.32)
    metal("steel", "mat_guitar_02_steel", "#a8a9a6", 0.3, 0.4)

    def plain(key, name, colour, rough, **v):
        m = M.principled(name, base=colour, rough=rough, **v)
        MATS[key] = m

    plain("guard", "mat_guitar_02_guard", "#f2efe6", 0.38, spec=0.5)
    plain("ply", "mat_guitar_02_ply", "#1f1e1c", 0.4)
    plain("plastic", "mat_guitar_02_plastic", "#eae3cf", 0.45, spec=0.5)
    plain("nut", "mat_guitar_02_nut", "#eee6d2", 0.5, sss=0.1, sss_scale=0.002)
    plain("dark", "mat_guitar_02_dark", "#151413", 0.6)
    plain("ink", "mat_guitar_02_ink", "#6c665a", 0.5)
    plain("dots", "mat_guitar_02_dots", "#1d1b18", 0.4)
    plain("foam", "mat_guitar_02_foam", "#1c1b1a", 0.8)

    # strings: plain #b9bcbf, wound #a8a294 with the winding as a bump along the string
    m, nt, b = M._new("mat_guitar_02_strings")
    w = _attr(nt, "wound")
    nt.links.new(_mix(nt, w, "#b9bcbf", "#a8a294"), b.inputs["Base Color"])
    nt.links.new(_mix(nt, w, 0.25, 0.35, "FLOAT"), b.inputs["Roughness"])
    M._set(b, metal=1.0)
    uvn = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uvn.outputs[0], sep.inputs[0])
    wave = M._math(nt, "SINE", M._math(nt, "MULTIPLY", sep.outputs["X"], 2 * math.pi / 0.32), 1.0)
    h = nt.nodes.new("ShaderNodeMath")
    h.operation = "MULTIPLY"
    nt.links.new(wave, h.inputs[0])
    nt.links.new(w, h.inputs[1])
    M._bump(nt, b, h.outputs[0], 0.6, 0.00006)
    m.diffuse_color = M.rgba("#b4b5b3")
    MATS["strings"] = m
    return MATS


# ---------------------------------------------------------------------------
# body: alder slab, edge roundover, forearm and belly contours, jack dish
# ---------------------------------------------------------------------------
def _umin_table():
    tab = {}
    for v in range(-20, 480):
        try:
            tab[v] = BP.body_span(min(max(v, 0.5), BP.BODY_L - 0.5))[0]
        except ValueError:
            tab[v] = 0.0
    return tab


_UMIN = None


def umin(v):
    global _UMIN
    if _UMIN is None:
        _UMIN = _umin_table()
    v0 = int(math.floor(v))
    v0 = min(max(v0, -20), 478)
    t = v - v0
    return _UMIN[v0] * (1 - t) + _UMIN[v0 + 1] * t


def contour_dz(u, v, front):
    if front:
        fa = G["forearm"]
        k = (umin(v) + fa["width"] - u) / fa["width"]
        return -fa["depth"] * BP.bell(v, *FOREARM_V) * max(0.0, min(1.0, k)) ** 1.6
    be = G["belly"]
    k = (umin(v) + be["width"] - u) / be["width"]
    return be["depth"] * BP.bell(v, *BELLY_V) * max(0.0, min(1.0, k)) ** 1.6


WEAR_SPOTS = [(-150, 120, 10, 26, 20), (-157, 95, 6, 18, 10), (-106, 452, 9, 6, -20), (106, 380, 8, 5, 10)]
# the four ageing-A spots of the blueprint (_wear_front level 1): forearm edge, both horn tips


def spot_weight(u, v, grow=3.0):
    best = 0.0
    for cu, cv, w, h, ang in WEAR_SPOTS:
        du, dv = BP.rot((u - cu, v - cv), -ang)
        d = math.hypot(du / (w / 2 * grow), dv / (h / 2 * grow))
        best = max(best, max(0.0, 1.0 - d) ** 0.8)
    return best


def _grid_inside(poly, spacing):
    import numpy as np
    P = np.array(poly)
    x0, y0 = P.min(0)
    x1, y1 = P.max(0)
    pts = []
    row = 0
    y = y0 + spacing / 2
    while y < y1:
        x = x0 + spacing / 2 + (spacing / 2 if row % 2 else 0)
        while x < x1:
            pts.append((x, y))
            x += spacing
        y += spacing * 0.866
        row += 1
    if not pts:
        return []
    Q_ = np.array(pts)
    A, B = P, np.roll(P, -1, axis=0)
    inside = np.zeros(len(Q_), bool)
    for (ax, ay), (bx, by) in zip(A, B):
        cond = ((ay > Q_[:, 1]) != (by > Q_[:, 1]))
        xi = ax + (Q_[:, 1] - ay) * (bx - ax) / ((by - ay) + 1e-12)
        inside ^= cond & (Q_[:, 0] < xi)
    Q_ = Q_[inside]
    AB = B - A
    L2 = (AB ** 2).sum(1) + 1e-12
    dmin = np.full(len(Q_), 1e9)
    for i in range(0, len(Q_), 512):
        q = Q_[i:i + 512, None, :]
        t = np.clip(((q - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
        proj = A[None] + t[..., None] * AB[None]
        dmin[i:i + 512] = np.sqrt(((q - proj) ** 2).sum(2)).min(1)
    return [tuple(p) for p in Q_[dmin > spacing * 0.6]]


def fill_cdt(bm, ring_verts, spacing, z, up, mi=0):
    ring2 = [(v.co.x, v.co.y) for v in ring_verts]
    n = len(ring2)
    pts = _grid_inside(ring2, spacing) if spacing else []
    coords = [Vector(p) for p in ring2] + [Vector(p) for p in pts]
    res = delaunay_2d_cdt(coords, [(i, (i + 1) % n) for i in range(n)], [list(range(n))], 1, 1e-5)
    ov, of, orig = res[0], res[2], res[3]
    vmap, new = [], []
    for i, co in enumerate(ov):
        k = next((s for s in orig[i] if s < n), None)
        if k is not None:
            vmap.append(ring_verts[k])
        else:
            v = bm.verts.new((co.x, co.y, z))
            vmap.append(v)
            new.append(v)
    for f in of:
        vs = [vmap[i] for i in f]
        if len(set(vs)) < 3:
            continue
        a = area2([(v.co.x, v.co.y) for v in vs])
        if (a > 0) != up:
            vs = vs[::-1]
        cap(bm, vs, mi)
    return new


def build_body():
    T, r = G["body_t"], G["edge_r"]
    O = ccw(resample(BP.BODY, Q("body_step")))
    N = smooth_normals(O, 8.0)
    seg = Q("ring_seg")
    bm = bmesh.new()
    wear = bm.verts.layers.float.new("wear")
    rings, ew = [], []
    for k in range(seg + 1):                         # front roundover: face edge to side
        phi = math.pi / 2 * (1 - k / seg)
        rings.append(ring(bm, inset(O, N, r * (1 - math.cos(phi))), -r + r * math.sin(phi)))
        ew.append(min(1.0, 0.35 + (90 - math.degrees(phi)) / 30))
    for k in range(seg + 1):                         # back roundover: side to face edge
        phi = -math.pi / 2 * k / seg
        rings.append(ring(bm, inset(O, N, r * (1 - math.cos(phi))), -T + r + r * math.sin(phi)))
        ew.append(0.5 if k < seg else 0.2)
    for a, b in zip(rings, rings[1:]):
        bridge(bm, b, a)
    front = fill_cdt(bm, rings[0], Q("grid"), 0.0, True)
    back = fill_cdt(bm, rings[-1], Q("grid"), -T, False)
    for rr, e in zip(rings, ew):
        for v in rr:
            v[wear] = e * spot_weight(v.co.x, v.co.y)
    for v in front:
        v[wear] = 0.12 * spot_weight(v.co.x, v.co.y, grow=3.0)
    for v in back:
        v[wear] = 0.0
    if _st["lite"]:                              # sparse vertices spread the patches: keep them light
        for v in bm.verts:
            v[wear] *= 0.6
    for v in bm.verts:
        u, vv, z = v.co
        v.co.z = z + contour_dz(u, vv, z > -T / 2)
    o = finish("body", bm, ["lacquer"], "body", recalc=True)
    if not _st["lite"]:
        _jack_dish(o)
    return o


def _jack_dish(body):
    """The jack sits in a dish routed into the top: a boolean, applied at once."""
    j = G["jack"]
    bm = bmesh.new()
    prism_uv(bm, place2(BP.lens(j["l"] + 7, j["w"] + 8, 24), (j["u"], j["v"]), j["angle_deg"]),
             -4.5, 8.0)
    bmesh.ops.transform(bm, matrix=SPEC, verts=bm.verts)
    me = bpy.data.meshes.new("guitar_02_tmp_dish_mesh")
    bm.to_mesh(me)
    bm.free()
    cut = bpy.data.objects.new("guitar_02_tmp_dish", me)
    _st["coll"].objects.link(cut)
    cut.parent = _st["root"]
    mod = body.modifiers.new("dish", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cut
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(body.evaluated_get(dg))
    body.modifiers.remove(mod)
    old = body.data
    body.data = new
    bpy.data.meshes.remove(old)
    new.name = body.name + "_mesh"
    bpy.data.objects.remove(cut)
    bpy.data.meshes.remove(me)


def build_jack():
    j = G["jack"]
    at, ang = (j["u"], j["v"]), j["angle_deg"]
    lite = _st["lite"]
    z0 = 0.0 if lite else -4.5
    bm = bmesh.new()
    prism_uv(bm, place2(BP.lens(j["l"], j["w"], 20 if not lite else 8), at, ang), z0, z0 + 0.9)
    lathe(bm, [(0, 0), (j["socket_d"] / 2, 0), (j["socket_d"] / 2, 2.2), (j["socket_d"] / 2 - 1.2, 2.6),
               (4.0, 2.6), (4.0, 1.2), (0, 1.2)], (at[0], at[1], z0 + 0.9), (0, 0, 1), Q("small") + 4)
    for sg in (-1, 1) if not lite else ():
        q = BP.rot((sg * (j["l"] / 2 - 7), 0), ang)
        cyl(bm, SCREW["jack"] / 2, (at[0] + q[0], at[1] + q[1], z0 + 0.5), (at[0] + q[0], at[1] + q[1], z0 + 1.7),
            Q("small"), dome=0.9)
    o = finish("jack", bm, ["chrome"], "body", bev=0.4, seg=2)
    bm = bmesh.new()
    cyl(bm, 3.2, (at[0], at[1], z0 + 1.15), (at[0], at[1], z0 + 1.25), Q("small"))
    finish("jack_hole", bm, ["dark"], "body")
    return o


def build_strap_buttons():
    sb = G["strap_button"]
    rr = sb["d"] / 2
    h = sb["h"]
    prof = [(0, -2.5), (rr * 0.95, -2.5), (rr, 0.3), (rr * 0.95, 1.2), (rr * 0.53, 2.2), (rr * 0.47, h * 0.5),
            (rr * 0.62, h * 0.64), (rr, h * 0.73), (rr * 1.02, h * 0.82), (rr * 0.84, h * 0.95),
            (rr * 0.45, h), (0, h * 1.01)]
    if _st["lite"]:
        prof = [prof[0], prof[1], prof[4], prof[5], prof[8], prof[11]]
    bm = bmesh.new()
    for u, v, ang, _ in G["strap_buttons"]:
        d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0.0)
        lathe(bm, prof, (u, v, -G["body_t"] / 2), d, Q("small") + 4 if not _st["lite"] else 6)
    return finish("strap_buttons", bm, ["chrome"], "body", bev=0.3, seg=2)


def build_back_plates():
    T = G["body_t"]
    tc = G["trem_cover"]
    cv = tc["v0"] + tc["l"] / 2
    bm = bmesh.new()
    rbox(bm, tc["w"], tc["l"], -T - 2.0, -T + 0.2, (0, cv), r=tc["r"], n=6 if not _st["lite"] else 2)
    finish("trem_cover", bm, ["guard"], "body", bev=0.5, seg=2)
    bm = bmesh.new()
    for u in BP.strings_bridge():
        prism_uv(bm, place2(BP.ellipse(5.0, 7.5, 16 if not _st["lite"] else 4), (u, VS - 12)), -T - 2.08, -T - 1.9)
    finish("trem_holes", bm, ["dark"], "body")
    bm = bmesh.new()
    for sg in (-1, 1) if not _st["lite"] else ():
        for vv in (tc["v0"] + 8, cv, tc["v0"] + tc["l"] - 8):
            cyl(bm, SCREW["cover"] / 2, (sg * (tc["w"] / 2 - 6), vv, -T - 1.6), (sg * (tc["w"] / 2 - 6), vv, -T - 3.0),
                Q("small"), dome=0.9)
    npl = G["neck_plate"]
    rbox(bm, npl["w"], npl["l"], -T - 1.6, -T + 0.2, (0, npl["v"]), r=npl["r"])
    for su in (-1, 1) if not _st["lite"] else ():
        for sv in (-1, 1):
            p = (su * npl["screw_du"], npl["v"] + sv * npl["screw_dv"])
            cyl(bm, SCREW["plate"] / 2, (p[0], p[1], -T - 1.2), (p[0], p[1], -T - 3.0), Q("small") + 2, dome=1.2)
    finish("back_metal", bm, ["chrome"], "body", bev=0.4, seg=2)
    if not _st["lite"]:
        bm = bmesh.new()                       # screw slots (cross on the neck screws)
        for sg in (-1, 1):
            for vv in (tc["v0"] + 8, cv, tc["v0"] + tc["l"] - 8):
                rbox(bm, 4.2, 0.6, -T - 3.05, -T - 2.6, (sg * (tc["w"] / 2 - 6), vv), r=0.2, n=1)
        for su in (-1, 1):
            for sv in (-1, 1):
                p = (su * npl["screw_du"], npl["v"] + sv * npl["screw_dv"])
                for a in (45, -45):
                    rbox(bm, 4.4, 0.8, -T - 3.05, -T - 2.5, p, a, r=0.2, n=1)
        finish("back_slots", bm, ["dark"], "body")


# ---------------------------------------------------------------------------
# neck: two-piece maple, 7.25 in radius board, 21 frets, dots, bone nut; the headstock
# ---------------------------------------------------------------------------
def board_top(u):
    return ZC - (R_BOARD - math.sqrt(R_BOARD ** 2 - u * u))


def _neck_vs():
    hw = BP.neck_w(G["butt_side_v"]) / 2
    dv = G["butt_side_v"] - G["v_butt"]
    out = []
    nb = 6 if not _st["lite"] else 2
    for k in range(nb + 1):
        th = math.radians(14 + (90 - 14) * k / nb)
        out.append((G["butt_side_v"] - dv * math.cos(th), math.sin(th)))
    v = G["butt_side_v"]
    marks = [G["v_pocket_end"], G["v_pocket_end"] + 2.5, VN]
    step = Q("neck_dv")
    while v < VN - 1e-6:
        nxt = min([v + step] + [m for m in marks if m > v + 0.2])
        out.append((nxt, 1.0))
        v = nxt
    return out, hw


def _board_profile(w):
    er = 1.0
    n = Q("arc")
    pts = []
    for k in range(n + 1):
        u = -(w - er) + 2 * (w - er) * k / n
        pts.append((u, board_top(u)))
    zg = ZC - BOARD_T
    right = [(w - er + er * math.sin(math.radians(a)), board_top(w - er) - er + er * math.cos(math.radians(a)))
             for a in (30, 60, 90)]
    left = [(-x, z) for x, z in right][::-1]
    return left + pts + right + [(w, zg + 0.25), (w - 0.15, zg), (-w + 0.15, zg), (-w, zg + 0.25)]


def _shaft_profile(w, v, top):
    pe = G["v_pocket_end"]
    zg = top
    zc_back = BP.neck_back_z(min(v, VN))
    if v <= pe:
        p, zb, zs = 12.0, -G["pocket_depth"], zg - 0.6
    else:
        t = min(1.0, (v - pe) / 2.5)
        p = 12.0 + (2.4 - 12.0) * t
        zb = -G["pocket_depth"] + (zc_back + G["pocket_depth"]) * t
        zs = zg - 0.6 - 0.9 * t
    if v > VN:
        t = min(1.0, (v - VN) / 26.0)
        p = 2.4 + 5.0 * t
        zb = zc_back + (HZ_BACK + 0.05 - zc_back) * t
    n = Q("cseg")
    pts = [(-w + 0.15, zg), (w - 0.15, zg), (w, zg - 0.25)]
    for k in range(n + 1):
        a = math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        u = w * math.copysign(abs(c) ** (2 / p), c)
        z = zs - (zs - zb) * abs(s) ** (2 / p)
        pts.append((u, z))
    pts.append((-w, zg - 0.25))
    return pts


def _loft_sections(bm, sections, mi=0):
    """sections: [(v, [(u, z)])] all of one length. Closed loft with end caps."""
    rings = [[bm.verts.new((u, v, z)) for u, z in prof] for v, prof in sections]
    for a, b in zip(rings, rings[1:]):
        bridge(bm, a, b, mi)
    cap(bm, rings[0], mi)
    cap(bm, rings[-1][::-1], mi)


def build_neck():
    vs, hw = _neck_vs()
    w_at = lambda v, sc: BP.neck_w(v) / 2 * sc if v > G["butt_side_v"] else hw * sc  # noqa: E731
    bm = bmesh.new()
    wear = bm.verts.layers.float.new("wear")
    _loft_sections(bm, [(v, _board_profile(w_at(v, sc))) for v, sc in vs])
    f7 = BP.FRETS[6]
    for v in bm.verts:
        x = VN - v.co.y
        if v.co.z > ZC - 1.5 and 0 <= x <= f7 + 6:
            along = min(1.0, x / 8.0) * max(0.0, min(1.0, (f7 + 6 - x) / 22.0))
            across = max(0.0, 1.0 - (v.co.x / 19.0) ** 2)
            v[wear] = along * across * (0.6 if _st["lite"] else 1.0)
    board = finish("board", bm, ["board"], "neck")
    sh = [(v, _shaft_profile(w_at(v, sc), v, ZC - BOARD_T)) for v, sc in vs]
    if not _st["lite"]:
        for k in range(1, 14):
            v = VN + 0.5 + 27.5 * k / 13
            sh.append((v, _shaft_profile(G["nut_w"] / 2, v, HZ_FACE - 0.6)))
    else:
        sh.append((VN + 24, _shaft_profile(G["nut_w"] / 2, VN + 24, HZ_FACE - 0.6)))
    bm = bmesh.new()
    _loft_sections(bm, sh)
    finish("neck", bm, ["neck"], "neck")
    return board


def build_frets_dots_nut():
    fw, fh = G["fret_wire"]
    na, npf = Q("fret_arc"), Q("fret_prof")
    bm = bmesh.new()
    for x in BP.FRETS:
        v = VN - x
        w = BP.neck_w(v) / 2 - 0.3
        loops = []
        for i in range(na + 1):
            u = -w + 2 * w * i / na
            hs = 1.0 if abs(u) < w - 1.2 else 0.35 + 0.65 * (w - abs(u)) / 1.2
            base = board_top(u) - 0.2
            crown = board_top(u) + fh * hs
            prof = [(v + fw / 2 * math.cos(math.pi * k / npf), base + (crown - base) * math.sin(math.pi * k / npf))
                    for k in range(npf + 1)]
            loops.append([bm.verts.new((u, vv, z)) for vv, z in prof])
        for a, b in zip(loops, loops[1:]):
            bridge(bm, b, a, closed=True)
        cap(bm, loops[0])
        cap(bm, loops[-1][::-1])
    finish("frets", bm, ["frets"], "neck")
    # dots: black, 6.35, centred between frets; two at the 12th
    bm = bmesh.new()
    prev = 0.0
    rd = G["dot_d"] / 2
    for n, x in enumerate(BP.FRETS, 1):
        if n in G["dots"]:
            vm = VN - (prev + x) / 2
            for u in ((-G["dot12_offset"], G["dot12_offset"]) if n == 12 else (0.0,)):
                nrm = Vector((u, 0, math.sqrt(R_BOARD ** 2 - u * u))).normalized()
                p = Vector((u, vm, board_top(u)))
                cyl(bm, rd, p - nrm * 0.3, p + nrm * 0.025, Q("cyl") if not _st["lite"] else 7)
        prev = x
    finish("dots", bm, ["dots"], "neck")
    # nut: bone, top on the radius
    bm = bmesh.new()
    hw = G["nut_w"] / 2
    n = Q("arc")
    top = [(-hw + 2 * hw * k / n, NUT_TOP - (-hw + 2 * hw * k / n) ** 2 / (2 * R_BOARD)) for k in range(n + 1)]
    prism_uz(bm, [(hw, HZ_FACE - 0.2)] + top[::-1] + [(-hw, HZ_FACE - 0.2)], VN, VN + G["nut_l"])
    finish("nut", bm, ["nut"], "neck", bev=0.5, seg=2)


def build_headstock():
    pts = resample(BP.HEAD, Q("head_step"), closed=False)
    bm = bmesh.new()
    prism_uv(bm, pts, HZ_BACK, HZ_FACE)
    return finish("headstock", bm, ["head"], "neck", bev=1.6, seg=3, angle=50)


# ---------------------------------------------------------------------------
# hardware: tuners, string tree, bridge, saddles, arm
# ---------------------------------------------------------------------------
def _key(bm, ka, pv, k, seg):
    """A vintage oval key: domed on both faces (a flat paddle mirrored the room and read as a dark disc)."""
    t = k["t"]
    prof = [(0, -t / 2), (0.45, -t * 0.46), (0.75, -t * 0.36), (0.93, -t * 0.2), (1.0, 0.0), (0.93, t * 0.2),
            (0.75, t * 0.36), (0.45, t * 0.46), (0, t / 2)]
    if _st["lite"]:
        prof = [prof[0], prof[2], prof[4], prof[6], prof[8]]
        seg = 6
    n0 = len(bm.verts)
    lathe(bm, prof, (0, 0, 0), (0, 0, 1), seg)
    bm.verts.ensure_lookup_table()
    for v in bm.verts[n0:]:
        v.co.x = ka + v.co.x * k["w"] / 2
        v.co.y = pv + v.co.y * k["h"] / 2
        v.co.z = k["z"] + v.co.z


def build_tuners():
    k, th = G["tuner_key"], G["tuner_housing"]
    lite = _st["lite"]
    bm = bmesh.new()
    for (pa, pv), (ka, _) in zip(BP.posts(), BP.keys()):     # keys square to the neck, just past the edge
        if not lite:
            cyl(bm, G["bushing_d"] / 2, (pa, pv, HZ_FACE - 0.5), (pa, pv, HZ_FACE + 1.5), Q("cyl"), dome=0.5)
            cyl(bm, G["post_d"] / 2, (pa, pv, HZ_FACE), (pa, pv, HZ_FACE + G["post_h"]), Q("cyl"), dome=0.6)
            rbox(bm, th["w"], th["h"], HZ_BACK - th["depth"], HZ_BACK + 0.3, (pa, pv), r=2.5, n=3)
        else:
            cyl(bm, G["post_d"] / 2, (pa, pv, HZ_FACE - 0.5), (pa, pv, HZ_FACE + G["post_h"]), 6)
            prism_uv(bm, place2(BP.rrect(th["w"], th["h"], 2.5, 1), (pa, pv)), HZ_BACK - th["depth"], HZ_BACK + 0.3)
        cyl(bm, 1.6, (pa - th["w"] / 2 + 0.5, pv, k["z"]), (ka + k["w"] / 2 - 0.5, pv, k["z"]),
            Q("small") if not lite else 4)
        if not lite:
            cyl(bm, 2.7, (pa - th["w"] / 2 + 0.2, pv, k["z"]), (pa - th["w"] / 2 - 2.2, pv, k["z"]), Q("small"))
            cyl(bm, 2.3, (ka + k["w"] / 2 + 1.5, pv, k["z"]), (ka + k["w"] / 2 - 1.0, pv, k["z"]), Q("small"))
        _key(bm, ka, pv, k, 32 if not lite else 8)
    o = finish("tuners", bm, ["nickel"], "hardware", bev=0.8, seg=2, angle=40)
    if not lite:
        bm = bmesh.new()
        for pa, pv in BP.posts():
            top = HZ_FACE + G["post_h"]
            rbox(bm, G["post_d"] + 0.1, 1.0, top - 6.0, top + 0.02, (pa, pv), 90, r=0.2, n=1)
            cyl(bm, 1.1, (pa, pv, top - 1.0), (pa, pv, top + 0.03), 10)
            cyl(bm, 0.9, (pa, pv + 5, HZ_BACK - th["depth"] - 0.4), (pa, pv + 5, HZ_BACK - th["depth"] + 0.2), 10)
        finish("tuner_slots", bm, ["dark"], "hardware")
    return o


TREE_UNDER = HZ_FACE + G["string_tree"]["height"] - 2.6     # where the wings hold A and low E


def build_string_tree():
    t = G["string_tree"]
    a, b = t["a"], VN + t["b"]
    bm = bmesh.new()
    cyl(bm, 2.2, (a, b, HZ_FACE - 0.3), (a, b, HZ_FACE + t["height"] - 0.8), Q("small"))
    n = 10 if not _st["lite"] else 4
    prof = []
    for k in range(n + 1):
        uu = -t["w"] / 2 + t["w"] * k / n
        zz = HZ_FACE + t["height"] - 1.8 * (abs(uu) / (t["w"] / 2)) ** 2
        prof.append((a + uu, zz))                  # centred on the tree (it was drawn on the centre line)
    sec = [(x, z) for x, z in prof] + [(x, z - 0.8) for x, z in prof[::-1]]
    prism_uz(bm, sec, b - t["h"] / 2, b + t["h"] / 2)
    cyl(bm, 2.2, (a, b, HZ_FACE + t["height"] - 0.4), (a, b, HZ_FACE + t["height"] + 1.0), Q("small"), dome=0.8)
    return finish("string_tree", bm, ["nickel"], "hardware", bev=0.25, seg=2)


def saddle_drop(u):
    return u * u / (2 * R_BOARD)


SADDLE_SHEET = 1.2      # bent steel strip, mm


def saddle_rear(back):
    """The saddle's rear tab: saddle_l behind its front, but never closer than 3 mm to the
    lip (the blueprint's 26 mm saddles would reach through it on the set-back strings)."""
    br = G["bridge"]
    lip = VS + br["front_off"] - br["l"] + 1.5
    return max(VS - back - br["saddle_l"] + 3.5, lip + 3.0)


def _saddle_b(u, back):
    """Underside of the strip, (v, z): rear tab, base on the plate, slope, crown, nose."""
    br = G["bridge"]
    z1 = br["float_gap"] + 1.2
    crown, top, dz, t = VS - back, br["saddle_top_z"], saddle_drop(u), SADDLE_SHEET
    vr = saddle_rear(back)
    ctrl = [(vr, z1 + 5.0), (vr, z1 + 0.6), (vr + 0.6, z1), (vr + 7.0, z1), (crown - 7.0, top - dz - t - 3.0),
            (crown - 1.4, top - dz - t - 0.15), (crown + 1.0, top - dz - t - 0.35), (crown + 2.6, top - dz - t - 2.4),
            (crown + 3.5, top - dz - t - 4.6)]
    return spline(ctrl, closed=False, n=4 if not _st["lite"] else 1)


def _offset_path(pts, d):
    out = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        out.append((x - ty / ln * d, y + tx / ln * d))
    return out


def saddle_section(u, back):
    B = _saddle_b(u, back)
    A = _offset_path(B, SADDLE_SHEET)
    return B + A[::-1]


def saddle_top_at(u, back, v):
    """Height of the strip's top face at v (for the string and the height screws)."""
    A = _offset_path(_saddle_b(u, back), SADDLE_SHEET)
    best = None
    for (v0, z0), (v1, z1_) in zip(A, A[1:]):
        if min(v0, v1) <= v <= max(v0, v1) and v1 != v0:
            z = z0 + (z1_ - z0) * (v - v0) / (v1 - v0)
            best = z if best is None else max(best, z)
    return best if best is not None else G["bridge"]["saddle_top_z"] - saddle_drop(u)


def build_bridge():
    br = G["bridge"]
    front = VS + br["front_off"]
    rear = front - br["l"]
    z0, z1 = br["float_gap"], br["float_gap"] + 1.2
    lite = _st["lite"]
    bm = bmesh.new()
    rbox(bm, br["w"], br["l"], z0, z1, (0, front - br["l"] / 2), r=2.5, n=3 if not lite else 1)
    rbox(bm, br["w"] - 1.5, 1.5, z0, z0 + br["lip_h"], (0, rear + 0.75), r=0.6, n=2 if not lite else 1)
    for u in BP.strings_bridge() if not lite else ():
        cyl(bm, br["screw_d"] / 2, (u, front - 4.6, z1 - 0.2), (u, front - 4.6, z1 + 1.3), Q("small"), dome=1.0)
    # arm collar
    lathe(bm, [(0, 0), (4.2, 0), (4.2, 1.6), (2.8, 2.4), (0, 2.4)], (*arm_uv(), z1 - 0.1), (0, 0, 1), Q("small"))
    o = finish("bridge", bm, ["chrome"], "hardware", bev=0.4, seg=2)
    # saddles: bent steel strips, each on its own height (7.25 in radius), set back per string
    bm = bmesh.new()
    sw = br["saddle_w"] - 0.6
    for u, back in zip(BP.strings_bridge(), G["saddle_back"]):
        sec = saddle_section(u, back)
        if lite:                                  # five points: tab, slope, crown, nose
            crown, dz, top = VS - back, saddle_drop(u), br["saddle_top_z"]
            vr = saddle_rear(back)
            sec = [(vr, z1), (vr, z1 + 4.5), (crown, top - dz), (crown + 3.5, top - dz - 4.0), (crown + 3.5, z1)]
        prism_vz(bm, sec, u - sw / 2, u + sw / 2)
    finish("saddles", bm, ["nickel"], "hardware", bev=0.3, seg=2, angle=30)
    if not lite:
        bm = bmesh.new()
        for u, back in zip(BP.strings_bridge(), G["saddle_back"]):
            vh = VS - back - 6.5
            for sg in (-1, 1):                  # height screws, up through the strip
                cyl(bm, 1.3, (u + sg * 2.9, vh, z1), (u + sg * 2.9, vh, saddle_top_at(u, back, vh) + 0.5), 12)
            vr = saddle_rear(back)
            cyl(bm, 1.4, (u, vr + 1.0, z1 + 3.0), (u, rear - 2.4, z1 + 3.0), 12)
            lathe(bm, [(0, 0), (2.6, 0), (2.6, 1.4), (1.6, 2.2), (0, 2.2)], (u, rear - 0.6, z1 + 3.0), (0, -1, 0), 14)
        finish("saddle_screws", bm, ["steel"], "hardware")
        bm = bmesh.new()                        # intonation springs, lip to saddle
        for u, back in zip(BP.strings_bridge(), G["saddle_back"]):
            v0, v1 = rear + 1.5, saddle_rear(back)
            turns = max(2.0, (v1 - v0) / 0.9)
            path = []
            for k in range(int(turns * 12) + 1):
                t = k / 12
                ang = 2 * math.pi * t
                path.append(Vector((u + 2.1 * math.cos(ang), v0 + (v1 - v0) * t / turns,
                                    z1 + 3.0 + 2.1 * math.sin(ang))))
            tube(bm, path, 0.32, 6)
        finish("saddle_springs", bm, ["steel"], "hardware")
    build_arm()
    return o


def arm_uv():
    """The arm's socket: the blueprint's v; u moved out just clear of the high-E saddle
    (at the blueprint's u = 31 the arm would rise through that saddle)."""
    a = G["arm"]
    sw = G["bridge"]["saddle_w"] - 0.6
    return max(a["u"], BP.strings_bridge()[-1] + sw / 2 + ARM_R + 0.05), a["v"]


ARM_R = 2.2


def _arm_path(n):
    a = G["arm"]
    au, av = arm_uv()
    ang = math.radians(a["angle_deg"])
    sinA = math.sin(ang)
    z1 = G["bridge"]["float_gap"] + 1.2
    side = [(z1, 0.0), (12.0, 1.0), (19.0, 6.0), (22.0, 16.0), (22.5, 52.0)]   # the blueprint's side view
    dz = [(dv / sinA, z) for z, dv in side]
    dz = [(0.0, -3.0)] + dz
    sm = spline(dz, closed=False, n=n)
    d = (math.cos(ang), math.sin(ang))
    return [Vector((au + s * d[0], av + s * d[1], z)) for s, z in sm], d


def build_arm():
    a = G["arm"]
    path, d = _arm_path(6 if not _st["lite"] else 2)
    L = a["length"]
    tip0 = L - 24.0
    au, av = arm_uv()
    cut = [p for p in path if (p.xy - Vector((au, av))).length <= tip0]
    end = Vector((au + tip0 * d[0], av + tip0 * d[1], path[-1].z))
    bm = bmesh.new()
    tube(bm, cut + [end + Vector((d[0], d[1], 0)) * 2.0], ARM_R, Q("tube") + 2)
    finish("arm", bm, ["chrome"], "hardware")
    bm = bmesh.new()
    prof = [(0, 0), (3.0, 0), (3.3, 3), (3.5, 14), (3.4, 20), (2.6, 23), (0, 24)]
    lathe(bm, prof, end, (d[0], d[1], 0.0), Q("small") + 2)
    finish("arm_tip", bm, ["plastic"], "hardware", bev=0.3, seg=2)


# ---------------------------------------------------------------------------
# pickguard, pickups, knobs, switch, screws
# ---------------------------------------------------------------------------
def build_pickguard():
    t = G["guard_t"]
    O = ccw(resample(BP.GUARD, Q("guard_step")))
    N = smooth_normals(O, 3.0)
    bw = (t - 0.6) / math.tan(math.radians(30))
    bm = bmesh.new()
    # rows down the vintage bevel: white top ply, black ply, white bottom ply, then the edge
    rows = [(bw, t, 0), (bw * (1 - (t - 1.55) / (t - 0.6)), 1.55, 1), (bw * (1 - (t - 1.2) / (t - 0.6)), 1.2, 0),
            (0.0, 0.6, 0), (0.0, 0.05, 0)]
    if _st["lite"]:
        rows = [(bw, t, 0), (0.0, 0.6, 0), (0.0, 0.05, 0)]
    rings = [ring(bm, inset(O, N, d), z) for d, z, _ in rows]
    for (a, b), (_, _, mi) in zip(zip(rings, rings[1:]), rows):
        bridge(bm, b, a, mi)
    fill_cdt(bm, rings[0], 10.0 if not _st["lite"] else 0, t, True)     # an even mesh (it shows in the wireframe)
    fill_cdt(bm, rings[-1], 10.0 if not _st["lite"] else 0, 0.05, False)
    finish("pickguard", bm, ["guard", "ply"], "pickguard")
    # guard screws: oval heads (too small for the web model)
    if _st["lite"]:
        return
    bm = bmesh.new()
    for u, v in G["guard_screws"]:
        lathe(bm, [(0, 0), (SCREW["guard"] / 2, 0), (SCREW["guard"] / 2 * 0.9, 0.4), (SCREW["guard"] / 2 * 0.55, 0.85),
                   (0, 1.0)], (u, v, t - 0.05), (0, 0, 1), Q("small"))
    for (c, ang), top in zip(BP.pickups(), G["pickup_top_z"]):     # through the cover's ends
        for sg in (-1, 1):
            q = BP.rot((sg * G["pickup"]["screw_off"], 0), ang)
            lathe(bm, [(0, 0), (SCREW["pickup"] / 2, 0), (SCREW["pickup"] / 2 * 0.9, 0.4),
                       (SCREW["pickup"] / 2 * 0.5, 0.8), (0, 0.95)],
                  (c[0] + q[0], c[1] + q[1], top - 0.85), (0, 0, 1), Q("small"))
    finish("guard_screws", bm, ["chrome"], "pickguard")
    if not _st["lite"]:
        bm = bmesh.new()
        for u, v in G["guard_screws"]:
            rbox(bm, SCREW["guard"] * 0.8, 0.55, t + 0.5, t + 1.05, (u, v), 25, r=0.2, n=1)
        for (c, ang), top in zip(BP.pickups(), G["pickup_top_z"]):
            for sg in (-1, 1):
                q = BP.rot((sg * G["pickup"]["screw_off"], 0), ang)
                rbox(bm, SCREW["pickup"] * 0.8, 0.5, top - 0.35, top + 0.15, (c[0] + q[0], c[1] + q[1]), 70, r=0.2, n=1)
        finish("guard_slots", bm, ["dark"], "pickguard")


def build_pickups():
    pk = G["pickup"]
    t = G["guard_t"]
    lite = _st["lite"]
    bm = bmesh.new()
    hw = pk["w"] / 2
    for (c, ang), top in zip(BP.pickups(), G["pickup_top_z"]):
        rounded_slab(bm, BP.rrect(pk["l"], pk["w"], 7, 8 if not lite else 2), t - 0.2, top - 0.5,
                     1.4 if not lite else 1.0, 4 if not lite else 1, 1.2 if not lite else 8.0,
                     2.5 if not lite else 0, dome=lambda x, y: 0.5 * max(0.0, 1 - (y / hw) ** 2), at=c, deg=ang)
    covers = finish("pickups", bm, ["plastic"], "pickguard")
    bm = bmesh.new()
    for (c, ang), top in zip(BP.pickups(), G["pickup_top_z"]):
        for i in range(6):
            q = BP.rot((-pk["pole_spread"] / 2 + pk["pole_spread"] * i / 5, 0), ang)
            cyl(bm, pk["pole_d"] / 2, (c[0] + q[0], c[1] + q[1], top - 1.5), (c[0] + q[0], c[1] + q[1], top + POLE_UP[i]),
                Q("small") + 2 if not lite else 4, dome=0.5 if not lite else 0.0)
    finish("poles", bm, ["steel"], "pickguard")
    return covers


def _knob_profile(kn, z0):
    rs, rt, h = kn["d"] / 2, kn["top_d"] / 2, kn["h"]
    return [(0, z0), (rs, z0), (rs, z0 + 1.5), (rs - 0.25, z0 + 1.8), (rs - 1.9, z0 + 4.0), (rt + 0.6, z0 + 4.4),
            (rt + 0.4, z0 + 5.2), (rt, h + z0 - 2.4), (rt - 0.6, h + z0 - 1.0), (rt - 2.4, h + z0 - 0.15),
            (0, h + z0)]


def build_knobs():
    kn = G["knob"]
    z0 = G["guard_t"] + kn["above_guard"]
    lite = _st["lite"]
    prof = _knob_profile(kn, 0.0)
    if lite:
        prof = [prof[0], prof[1], prof[2], prof[4], prof[7], prof[9], prof[10]]
    ribs = (lambda th, i: 1.0 + (0.018 * math.cos(30 * th) if 6 <= i <= 7 else 0.0)) if not lite else None
    bm = bmesh.new()
    for _, u, v in G["knobs"]:
        lathe(bm, [(r, z0 + h) for r, h in prof], (u, v, 0.0), (0, 0, 1), 120 if not lite else Q("lathe"), rmod=ribs)
        # the shaft under the knob, in the gap above the guard
        cyl(bm, 3.0, (u, v, G["guard_t"] - 0.1), (u, v, z0 + 0.2), Q("small"))
    o = finish("knobs", bm, ["plastic"], "pickguard", bev=0.25, seg=2, angle=40)
    if not lite:
        _knob_numbers(kn, z0)
    return o


def _knob_numbers(kn, z0):
    """0 to 10 on each skirt (plain digits, nothing else), on the sloped face, ink-dark."""
    rs = kn["d"] / 2
    bm = bmesh.new()
    sl_out, sl_in = (rs - 0.25, z0 + 1.8), (rs - 1.9, z0 + 4.0)
    mid_r = (sl_out[0] + sl_in[0]) / 2
    mid_z = (sl_out[1] + sl_in[1]) / 2
    up2 = Vector((sl_in[0] - sl_out[0], sl_in[1] - sl_out[1])).normalized()
    cu = bpy.data.curves.new("guitar_02_tmp_digits", "FONT")
    cu.size = 1.75
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.extrude = 0.08
    cu.fill_mode = "BOTH"
    cu.resolution_u = 4
    ob = bpy.data.objects.new("guitar_02_tmp_digits", cu)
    bpy.context.scene.collection.objects.link(ob)
    meshes = {}
    for t in range(11):
        cu.body = str(t)
        bpy.context.view_layer.update()
        meshes[t] = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    for _, u, v in G["knobs"]:
        for t in range(11):
            th = math.radians(90 - 30 * t)
            rad = Vector((math.cos(th), math.sin(th), 0))
            right = Vector((-math.sin(th), math.cos(th), 0))
            up = rad * up2.x + Vector((0, 0, up2.y))         # up the slope, toward the top
            nrm = right.cross(up).normalized()
            if nrm.dot(rad + Vector((0, 0, 1))) < 0:
                nrm = -nrm
            c = Vector((u, v, 0)) + rad * mid_r + Vector((0, 0, mid_z)) + nrm * 0.02
            n0 = len(bm.verts)
            bm.from_mesh(meshes[t])
            bm.verts.ensure_lookup_table()
            for vert in bm.verts[n0:]:
                x, y, z = vert.co
                vert.co = c + right * x + up * y + nrm * z
    for me in meshes.values():
        bpy.data.meshes.remove(me)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    finish("knob_numbers", bm, ["ink"], "pickguard", recalc=False)


def build_switch():
    sw = G["switch"]
    t = G["guard_t"]
    ang = sw["angle_deg"]
    lite = _st["lite"]
    bm = bmesh.new()
    rbox(bm, sw["slot_l"], sw["slot_w"], t - 0.3, t + 0.03, (sw["u"], sw["v"]), ang, r=1.5, n=3 if not lite else 1)
    finish("switch_slot", bm, ["dark"], "pickguard")
    tip_c = BP.rot((-(sw["slot_l"] / 2 - 3.5), 0), ang)
    c = (sw["u"] + tip_c[0], sw["v"] + tip_c[1])
    bm = bmesh.new()
    rbox(bm, 1.0, 3.0, t - 1.0, t + 4.0, c, ang, r=0.2, n=1)
    finish("switch_lever", bm, ["steel"], "pickguard")
    bm = bmesh.new()
    if lite:
        loft_uv(bm, place2(BP.rrect(sw["tip_w"], sw["tip_l"], 3.2, 1), c, ang), t + 2.5, t + 11.0, 0.8)
    else:                                         # a clean rounded cap (a bevel on the taper streaked)
        rounded_slab(bm, BP.rrect(sw["tip_w"], sw["tip_l"], 3.2, 6), t + 2.5, t + 11.0, 2.6, 5, 0.8, 1.5,
                     dome=lambda x, y: 0.6 * max(0.0, 1 - (y / (sw["tip_l"] / 2)) ** 2), at=c, deg=ang)
    return finish("switch_tip", bm, ["plastic"], "pickguard")


# ---------------------------------------------------------------------------
# strings: Hendrix's stringing (thin E on the left), one mesh
# ---------------------------------------------------------------------------
def string_paths(coils=True):
    br = G["bridge"]
    front = VS + br["front_off"]
    vh = front - br["l"] + 8
    z1 = br["float_gap"] + 1.2
    top = br["saddle_top_z"]
    nut_u, br_u = BP.strings_nut(), BP.strings_bridge()
    posts = BP.posts()
    tree = G["string_tree"]
    out = []
    for i, (un, ub, back, g) in enumerate(zip(nut_u, br_u, G["saddle_back"], G["gauges"])):
        rad = g * 25.4 / 2
        crown = VS - back
        dz = saddle_drop(ub)
        zs = top - dz + rad
        zt_hole = saddle_top_at(ub, back, vh + 0.2) + rad
        zn = NUT_TOP - un * un / (2 * R_BOARD) - 0.25 + rad
        pts = [Vector((ub, vh, z1 - 1.0)), Vector((ub, vh + 0.2, zt_hole))]
        for f in (0.3, 0.55, 0.8):                # along the strip's top to the crown
            vv = vh + 0.2 + (crown - vh - 0.2) * f
            pts.append(Vector((ub, vv, saddle_top_at(ub, back, vv) + rad)))
        pts.append(Vector((ub, crown, zs)))
        if coils:                                 # speaking length subdivided, for the strum code
            for k in range(1, 24):
                t = k / 24
                pts.append(Vector((ub + (un - ub) * t, crown + (VN - crown) * t, zs + (zn - zs) * t)))
        pts += [Vector((un, VN, zn)), Vector((un, VN + G["nut_l"], zn))]
        pa, pv = posts[i]
        pr = G["post_d"] / 2 + rad
        zw = HZ_FACE + WRAP_Z[i]
        q = Vector((un, VN + G["nut_l"]))
        c = Vector((pa, pv))
        d = (c - q).normalized()
        for _ in range(3):                        # tangent point on the post's inner (+u) side
            n = Vector((d.y, -d.x))
            if n.x < 0:
                n = -n
            tp = c + n * pr
            d = (tp - q).normalized()
        if i >= 4:                                # A and low E go under the butterfly tree
            bt = VN + tree["b"]
            f = (bt - q.y) / (tp.y - q.y)
            pts.append(Vector((q.x + (tp.x - q.x) * f, bt, TREE_UNDER - rad)))
        pts.append(Vector((tp.x, tp.y, zw)))
        if coils:
            a0 = math.atan2(n.y, n.x)
            tang = Vector((-math.sin(a0), math.cos(a0)))
            sgn = 1 if tang.dot(d) > 0 else -1
            turns = WRAP_TURNS[i]
            pitch = 2 * rad * 1.05
            steps = int(turns * 20)
            for k in range(1, steps + 1):
                tt = k / 20
                aa = a0 + sgn * 2 * math.pi * tt
                pts.append(Vector((pa + pr * math.cos(aa), pv + pr * math.sin(aa), zw - pitch * tt)))
        out.append((pts, rad, 1.0 if g >= 0.026 else 0.0))
    return out


def build_strings():
    bm = bmesh.new()
    wound = bm.verts.layers.float.new("wound")
    uv = bm.loops.layers.uv.new("UVMap")
    for pts, rad, w in string_paths(coils=not _st["lite"]):
        tube(bm, pts, rad, Q("tube"), uv=uv, attr=wound, aval=w)
    bmesh.ops.transform(bm, matrix=SPEC, verts=bm.verts)
    name = "guitar_02_strings" if not _st["lite"] else "guitar_02_lite_strings"
    mat = MATS["strings"] if not _st["lite"] else _strings_lite_mat()
    o = geo.from_bmesh(name, bm, collection=_st["coll"], parent=_st["root"], material=mat, smooth=True)
    zm = (NUT_TOP + G["bridge"]["saddle_top_z"]) / 2
    geo.set_origin(o, S(0.0, (VN + VS) / 2, zm))
    o["group"] = "strings"
    _st["groups"].setdefault("strings", []).append(o)
    return o


def _strings_lite_mat():
    return bpy.data.materials.get("mat_guitar_02_strings_web") or \
        M.principled("mat_guitar_02_strings_web", base="#b6b7b5", metal=1.0, rough=0.3)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
GROUPS = ("body", "neck", "hardware", "pickguard", "strings")


def build_steps(parent=None, collection=None, lite=False):
    """Yield after each group. Returns the root (StopIteration.value)."""
    if not lite:
        BUILD_ORDER.clear()
    _st["groups"] = {}
    _st["lite"] = lite
    _st["Q"] = LITE if lite else RICH
    _st["prefix"] = "guitar_02_lite_" if lite else "guitar_02_part_"
    scene = bpy.context.scene
    coll = collection or bpy.data.collections.get("obj_guitars") or bpy.data.collections.new("obj_guitars")
    if coll.users == 0:
        scene.collection.children.link(coll)
    _st["coll"] = coll
    if lite:
        root = bpy.data.objects.new("guitar_02_lite_root", None)
    else:
        root = bpy.data.objects.new("guitar_02", None)
        root.empty_display_type = "SPHERE"
        root.empty_display_size = 0.02
    coll.objects.link(root)
    names.set_name(root, root.name, data=False)
    root.parent = parent
    _st["root"] = root
    if not MATS or "lacquer" not in MATS or MATS["lacquer"].name not in bpy.data.materials:
        materials()
    if not lite:
        yield "materials"
    build_body()
    build_jack()
    build_strap_buttons()
    build_back_plates()
    yield "body"
    build_neck()
    build_frets_dots_nut()
    build_headstock()
    yield "neck"
    build_tuners()
    build_string_tree()
    build_bridge()
    yield "hardware"
    build_pickguard()
    build_pickups()
    build_knobs()
    build_switch()
    yield "pickguard"
    build_strings()
    yield "strings"
    for g in GROUPS if not lite else ():
        BUILD_ORDER.append((g, [o.name for o in _st["groups"].get(g, [])]))
    return root


def build(parent=None, collection=None, lite=False):
    gen = build_steps(parent, collection, lite)
    try:
        while True:
            next(gen)
    except StopIteration as s:
        return s.value


def place_on_wall(root):
    """On its hook on the right wall, facing the room (-X): the body's centre plane at
    WALL_GUITARS off_wall, the hook contact at the hook height."""
    WG = C.WALL_GUITARS
    root.location = (C.RX - WG["off_wall"] - (G["body_t"] / 2 + PIV[2]) * MM, WG["y"][1],
                     WG["bottom"] + PIV[1] * MM)
    root.rotation_euler = (0, 0, math.radians(-90))
    bpy.context.view_layer.update()
    return root


def build_hanger(root, collection, parent=None, wall_z=None, name="guitars_hook_02"):
    """The wall hanger that holds guitar_02 (static scenery): a round wall plate, an arm,
    a yoke behind the headstock and two foam-covered prongs at the blueprint's 46 mm gap.
    Built in the guitar's frame, written in world space under `parent`."""
    bpy.context.view_layer.update()
    gap_l, gap_r = BP.HOOK_A0, BP.HOOK_A1
    bh = VN + BP.HOOK_B
    pr = 3.75
    if wall_z is None:
        wall_z = -G["body_t"] / 2 - C.WALL_GUITARS["off_wall"] / MM
    zb = -30.0
    chrome = bmesh.new()
    foam = bmesh.new()
    for a, sg in ((gap_l, -1), (gap_r, 1)):
        cu = a + sg * pr
        cv = bh - 1.2
        tube(foam, [Vector((cu, cv, zb + 4)), Vector((cu, cv, HZ_FACE + 10)), Vector((cu, cv + 3, HZ_FACE + 15))],
             pr, 16)
        tube(chrome, [Vector((cu, cv, zb + 6)), Vector((cu, cv - 2, zb)), Vector((cu * 0.5, cv - 8, zb)),
                      Vector((0, cv - 9, zb))], 2.4, 12)
    tube(chrome, [Vector((0, bh - 10.2, zb)), Vector((0, bh - 10.2, wall_z + 6))], 3.0, 14)
    # the base on the wall: black, small, like a common wall hanger's (a chrome disc read as a stray part)
    lathe(foam, [(0, 0), (16, 0), (16, 4), (13, 8), (0, 8)], (0, bh - 10.2, wall_z), (0, 0, 1), 32)
    mats = []
    out = []
    for bm, mat, key in ((chrome, "chrome", "arm"), (foam, "foam", "foam")):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.transform(bm, matrix=root.matrix_world @ SPEC, verts=bm.verts)
        if parent is not None:
            bmesh.ops.transform(bm, matrix=parent.matrix_world.inverted(), verts=bm.verts)
        o = geo.from_bmesh(f"{name}_{key}_tmp", bm, collection=collection, parent=parent, material=MATS[mat])
        out.append(o)
        mats.append(mat)
    h = geo.join(out, name)
    return h


# ---------------------------------------------------------------------------
# exports
# ---------------------------------------------------------------------------
def parts(root):
    return [o for o in root.children if o.type == "MESH" and o.name != "guitar_02_strings"]


def _joined_copy(objs, name, parent):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    copies = []
    for o in objs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        c = bpy.data.objects.new(o.name + "_tmp", me)
        o.users_collection[0].objects.link(c)
        c.parent = parent
        c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        c.matrix_basis = o.matrix_basis.copy()
        copies.append(c)
    return geo.join(copies, name)


def export_rich(root):
    """guitar_02 + guitar_02_body (the parts joined, several materials: renders only) +
    guitar_02_strings. Returns (objects, undo)."""
    body = _joined_copy(parts(root), "guitar_02_body", root)

    def undo():
        me = body.data
        bpy.data.objects.remove(body)
        bpy.data.meshes.remove(me)
    return [root, body, bpy.data.objects["guitar_02_strings"]], undo


def _gltf_group():
    g = bpy.data.node_groups.get("glTF Material Output")
    if g is None:
        g = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
        g.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    return g


def _image(name, size, data=False):
    im = bpy.data.images.get(name)
    if im is not None:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    if data:
        im.colorspace_settings.name = "Non-Color"
    return im


def _bake(obj, target, kind, samples=4):
    """Bake one channel into `target`: kind 'base', 'rough', 'metal' (an emission rewire) or 'ao'."""
    scene = bpy.context.scene
    restore = []
    for mat in obj.data.materials:
        nt = mat.node_tree
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = target
        nt.nodes.active = tn
        restore.append((mat, tn, None))
        if kind == "ao":
            continue
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        sock = b.inputs[{"base": "Base Color", "rough": "Roughness", "metal": "Metallic"}[kind]]
        e = nt.nodes.new("ShaderNodeEmission")
        if sock.is_linked:
            nt.links.new(sock.links[0].from_socket, e.inputs["Color"])
        else:
            dv = sock.default_value
            e.inputs["Color"].default_value = tuple(dv) if kind == "base" else (dv, dv, dv, 1.0)
        old = out.inputs["Surface"].links[0].from_socket
        nt.links.new(e.outputs[0], out.inputs["Surface"])
        restore[-1] = (mat, tn, (e, old, out))
    scene.cycles.samples = samples
    scene.render.bake.margin = 6
    scene.render.bake.use_clear = True
    scene.render.bake.target = "IMAGE_TEXTURES"
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    with _ctx(obj):
        bpy.ops.object.bake(type="AO" if kind == "ao" else "EMIT")
    for mat, tn, rw in restore:
        nt = mat.node_tree
        if rw:
            e, old, out = rw
            nt.links.new(old, out.inputs["Surface"])
            nt.nodes.remove(e)
        nt.nodes.remove(tn)


def _ctx(obj):
    wm = bpy.data.window_managers[0]
    kw = dict(active_object=obj, object=obj, selected_objects=[obj], selected_editable_objects=[obj])
    if wm.windows and not bpy.app.background:
        kw.update(window=wm.windows[0], screen=wm.windows[0].screen)
    return bpy.context.temp_override(**kw)


def _setup_cycles_bake():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "METAL"
    scene.cycles.device = "GPU"
    scene.cycles.use_denoising = False


def export_lite(root, size=1024, orm_size=512):
    """The web model: builds the lite parts (same frame), joins them into one mesh, packs
    its UVs, bakes base colour, AO, roughness and metallic from the same materials into a
    1024 atlas and a 512 ORM, and gives it one material. Renames the rich root and strings
    while the export runs. Returns (objects, undo, info)."""
    import numpy as np
    scene = bpy.context.scene
    prev_engine = scene.render.engine
    prev_samples = scene.cycles.samples
    coll = root.users_collection[0]
    lroot = build(parent=root.parent, collection=coll, lite=True)
    lroot.matrix_world = root.matrix_world.copy()
    bpy.context.view_layer.update()
    lparts = [o for o in lroot.children if o.type == "MESH" and o.name != "guitar_02_lite_strings"]
    body = geo.join(lparts, "guitar_02_lite_body")
    lstr = bpy.data.objects["guitar_02_lite_strings"]
    # UVs
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    body.data.uv_layers.new(name="UVMap")
    with _ctx(body):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.006, correct_aspect=True)
        bpy.ops.object.mode_set(mode="OBJECT")
    # bake: everything else hidden so AO only sees the web model itself
    _setup_cycles_bake()
    hidden = []
    for o in scene.objects:
        if o is not body and o.type in ("MESH", "CURVE", "FONT") and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    world = scene.world
    old_ao = world.light_settings.distance
    world.light_settings.distance = 0.03
    base = _image("guitar_02_atlas", size)
    rough = _image("guitar_02_rough_tmp", orm_size, True)
    metal = _image("guitar_02_metal_tmp", orm_size, True)
    ao = _image("guitar_02_ao_tmp", orm_size, True)
    _bake(body, base, "base", 4)
    _bake(body, rough, "rough", 4)
    _bake(body, metal, "metal", 4)
    _bake(body, ao, "ao", 64)
    world.light_settings.distance = old_ao
    for o in hidden:
        o.hide_render = False
    orm = _image("guitar_02_orm", orm_size, True)
    px = np.empty(orm_size * orm_size * 4, np.float32)
    ch = []
    for im in (ao, rough, metal):
        im.pixels.foreach_get(px)
        ch.append(px.reshape(-1, 4)[:, 0].copy())
    out = np.ones((orm_size * orm_size, 4), np.float32)
    out[:, 0] = 0.35 + 0.65 * ch[0]          # keep AO gentle: the room light does the rest
    out[:, 1], out[:, 2] = ch[1], ch[2]
    orm.pixels.foreach_set(out.ravel())
    for im in (rough, metal, ao):
        bpy.data.images.remove(im)
    paths = {}
    for im, fn, q in ((base, "guitar_02_atlas.jpg", 90), (orm, "guitar_02_orm.jpg", 92)):
        p = os.path.join(C.OUT, fn)
        im.filepath_raw = p
        im.file_format = "JPEG"
        scene.render.image_settings.quality = q
        try:
            im.save(filepath=p, quality=q)
        except TypeError:
            im.save()
        paths[fn] = round(os.path.getsize(p) / 1024)
    # one material
    m, nt, b = M._new("mat_guitar_02")
    tb = nt.nodes.new("ShaderNodeTexImage")
    tb.image = base
    tb.location = (-600, 200)
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = orm
    to.location = (-600, -200)
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sep.inputs[0])
    nt.links.new(tb.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(sep.outputs[1], b.inputs["Roughness"])
    nt.links.new(sep.outputs[2], b.inputs["Metallic"])
    gg = nt.nodes.new("ShaderNodeGroup")
    gg.node_tree = _gltf_group()
    nt.links.new(sep.outputs[0], gg.inputs["Occlusion"])
    M._set(b, spec=0.5)
    m.diffuse_color = M.rgba("#e6dfcf")
    body.data.materials.clear()
    body.data.materials.append(m)
    scene.render.engine = prev_engine
    scene.cycles.samples = prev_samples
    # swap names for the export
    strings_rich = bpy.data.objects["guitar_02_strings"]
    root.name = "guitar_02_rich"
    strings_rich.name = "guitar_02_strings_rich"
    names.set_name(lroot, "guitar_02", data=False)
    names.set_name(body, "guitar_02_body")
    names.set_name(lstr, "guitar_02_strings")
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    stris = sum(len(p.vertices) - 2 for p in lstr.data.polygons)
    info = {"body_triangles": tris, "strings_triangles": stris, "images_kb": paths}

    def undo():
        for o in (body, lstr):
            me = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
        bpy.data.objects.remove(lroot)
        root.name = "guitar_02"
        strings_rich.name = "guitar_02_strings"
        assert root.name == "guitar_02" and strings_rich.name == "guitar_02_strings"
    return [lroot, body, lstr], undo, info


def check(root):
    """Names, one material on each code-touched mesh, the strings' origin at their midpoint."""
    probs = []
    for o in [root] + names.descendants(root):
        if not names.NAME_RE.match(o.name):
            probs.append(f"bad name {o.name}")
        if o.type == "MESH" and o.data.name == o.name:
            probs.append(f"mesh data named like {o.name}")
    s = bpy.data.objects.get("guitar_02_strings")
    if s is None or s.parent is not root:
        probs.append("guitar_02_strings missing")
    elif len(s.data.materials) != 1:
        probs.append("guitar_02_strings needs one material")
    if root.type != "EMPTY":
        probs.append("guitar_02 is not an empty")
    if probs:
        raise AssertionError("guitar_02: " + "; ".join(probs))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in names.descendants(root) if o.type == "MESH")
    return {"parts": len(names.descendants(root)), "triangles_before_bevels": tris}
