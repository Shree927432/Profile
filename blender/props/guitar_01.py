"""guitar_01: B.B. King's "Lucille", an exact replica in shape, hardware and finish (decisions
2026-10-23), built from blender/lib/guitar_specs.py GUITAR_01 (measured on the ES-355 cut-out and
the Lucille photos, video-local/footage/2026-11-12-guitars/measure/). No logos, wordmark, crown,
"Lucille" or signature anywhere; plain knobs, a plain truss-rod cover.

Frame. Every part is built in the spec's millimetres (u across, + to the viewer's right; v along,
0 at the body's tail edge; z out of the top, 0 on the rims' top edge) and mapped by SPEC into the
frame MESHES.md wants: +X right, +Z up, -Y out of the front, metres, origin at the hook contact on
the headstock (the pivot of `guitar_01`). A Gibson-type guitar is not flat like the Strat: the neck
is set 3 degrees back about the junction (NECK_M) and the headstock 17 degrees further about the
nut (HEAD_M); neck and head parts are built flat in their own frame and turned by those matrices.

Names (MESHES.md, obj_guitars):
    guitar_01           empty at the hook contact, the whole guitar
    guitar_01_strings   one mesh, one material, origin at the strings' midpoint (nut to saddles)
    guitar_01_part_*    every other part in the .blend; the exports join them into `guitar_01_body`

    build_steps(parent=None, collection=None, lite=False), build(...), BUILD_ORDER, check(root)
    export_rich(root), export_lite(root)   as guitar_02's (the lite bake runs on the CPU: this
                                           script never touches Cycles' device preferences)
    W(root, u, v, z)                       a spec point in world space (for cameras)

Geometry helpers (ring, bridge, cap, lathe, cyl, tube, resample, fill_cdt, ...) are guitar_02's;
guitar_02.py itself is imported, never changed.
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from lib import constants as C, geo, materials as M, names
from lib.guitar_specs import GUITAR_01 as G, fret_positions, spline
from props import guitar_02 as H

MM = C.MM
SC, VN, VJ = G["scale"], G["v_nut"], G["v_junction"]
T, ZC = G["body_t"], G["board_above_body"]
R_BOARD, BT, BB = G["radius"], G["board_t"], G["board_binding"]
FRETS = fret_positions(SC, G["frets"])
FH = G["fret_wire"][1]
NL = G["nut_l"]
HZ0 = ZC - G["head_drop"]                              # head face at the nut, neck frame
HT = G["head_t"]
TAN_H = math.tan(math.radians(G["head_angle_deg"]))


def _tr(x, y, z):
    return Matrix.Translation((x, y, z))


NECK_M = _tr(0, VJ, ZC) @ Matrix.Rotation(math.radians(-G["neck_angle_deg"]), 4, "X") @ _tr(0, -VJ, -ZC)
HEAD_M = NECK_M @ _tr(0, VN + NL, HZ0) @ Matrix.Rotation(math.radians(-G["head_angle_deg"]), 4, "X") \
    @ _tr(0, -(VN + NL), -HZ0)

BODY = H.ccw(spline(G["body"], n=3))
HEAD = [(a, VN + b) for a, b in spline(G["headstock"], closed=False, n=6)]
GUARD = H.ccw(spline(G["pickguard"], n=4))

RICH = dict(body_step=2.5, grid=8.0, neck_dv=4.0, arc=16, cseg=20, cyl=24, small=14, tube=8,
            head_step=2.0, fret_arc=14, fret_prof=7, guard_step=2.0, plies=True, knurl=48)
LITE = dict(body_step=12.0, grid=45.0, neck_dv=28.0, arc=5, cseg=7, cyl=10, small=6, tube=3,
            head_step=8.0, fret_arc=3, fret_prof=2, guard_step=10.0, plies=False, knurl=12)

BUILD_ORDER = []
MATS = {}
_st = dict(coll=None, root=None, lite=False, prefix="guitar_01_part_", Q=RICH, groups={})


def Q(k):
    return _st["Q"][k]


# ---------------------------------------------------------------------------
# the body's top and back: distance in from the edge, the arch
# ---------------------------------------------------------------------------
_BA = np.array(BODY)
_BB = np.roll(_BA, -1, axis=0)


def edge_dist(u, v):
    """Distance (mm) from (u, v) to the body outline; arrays or scalars."""
    P = np.stack([np.atleast_1d(u), np.atleast_1d(v)], 1).astype(float)
    AB = _BB - _BA
    L2 = (AB ** 2).sum(1) + 1e-12
    out = np.empty(len(P))
    for i in range(0, len(P), 256):
        q = P[i:i + 256, None, :]
        t = np.clip(((q - _BA[None]) * AB[None]).sum(2) / L2[None], 0, 1)
        proj = _BA[None] + t[..., None] * AB[None]
        out[i:i + 256] = np.sqrt(((q - proj) ** 2).sum(2)).min(1)
    return out if np.ndim(u) else float(out[0])


def arch(d, rise):
    x = np.clip(np.asarray(d, float) / G["arch_run"], 0.0, 1.0)
    return rise * (1.0 - (1.0 - x) ** 2)


def top_z(u, v):
    return float(arch(edge_dist(u, v), G["arch_top"]))


# ---------------------------------------------------------------------------
# strings: the line from the saddles to the nut, the saddle line from the scale
# ---------------------------------------------------------------------------
def neck_pt(u, v, z):
    return NECK_M @ Vector((u, v, z))


def head_pt(a, b, z):
    """A point on the head: a across, b above the nut, z in the head frame (HZ0 = the face)."""
    return HEAD_M @ Vector((a, VN + b, z))


def _string_line():
    nut = neck_pt(0, VN, ZC + FH + 0.45)
    end = neck_pt(0, G["v_board_end"], ZC + FH + G["string_over_board"])
    d = (end - nut).normalized()
    s = SC
    p = nut + d * s
    return nut, p


NUT_P, SAD_P = _string_line()
VS = SAD_P.y                                  # the scale line on the body (saddle crowns before compensation)
ZS = SAD_P.z                                  # string height over the rim plane at the saddles


def string_z(v):
    t = (v - SAD_P.y) / (NUT_P.y - SAD_P.y)
    return SAD_P.z + (NUT_P.z - SAD_P.z) * t


def strings_u(v):
    """u of the six strings at body position v (linear from the saddles to the nut)."""
    n = len(G["strings"])
    t = (v - VS) / (NUT_P.y - VS)
    spread = G["bridge_spread"] + (G["nut_spread"] - G["bridge_spread"]) * t
    return [-spread / 2 + spread * i / (n - 1) for i in range(n)]


def neck_w(v):
    """Board width (with binding) at neck-frame v."""
    return G["nut_w"] + (G["w12"] - G["nut_w"]) * (VN - v) / (SC / 2)


def board_top(u):
    return ZC - (R_BOARD - math.sqrt(R_BOARD ** 2 - u * u))


# ---------------------------------------------------------------------------
# objects
# ---------------------------------------------------------------------------
PIV = (0.0, 0.0, 0.0)
SPEC = Matrix.Identity(4)


def _set_pivot():
    """The hook contact: where the head is as wide as the hanger's gap, mid-thickness."""
    global PIV, SPEC
    gap = G["hook"]["gap"]
    b = next(k * 0.1 for k in range(0, 1200) if head_half_w(k * 0.1) * 2 >= gap)
    p = head_pt(0.0, b, HZ0 - HT / 2)
    PIV = (p.x, p.y, p.z)
    SPEC = Matrix(((MM, 0, 0, -PIV[0] * MM),
                   (0, 0, -MM, PIV[2] * MM),
                   (0, MM, 0, -PIV[1] * MM),
                   (0, 0, 0, 1)))
    return b


def head_half_w(b):
    v = VN + b
    xs = []
    for (a0, v0), (a1, v1) in zip(HEAD, HEAD[1:]):
        if (v0 - v) * (v1 - v) <= 0 and v0 != v1:
            xs.append(a0 + (a1 - a0) * (v - v0) / (v1 - v0))
    return (max(xs) - min(xs)) / 2 if xs else 0.0


HOOK_B = _set_pivot()


def S(u, v, z):
    return SPEC @ Vector((u, v, z))


def finish(key, bm, mats, group, frame=None, bev=None, seg=2, angle=35, smooth=True, recalc=True):
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if frame is not None:
        bmesh.ops.transform(bm, matrix=frame, verts=bm.verts)
    bmesh.ops.transform(bm, matrix=SPEC, verts=bm.verts)
    name = _st["prefix"] + key
    o = geo.from_bmesh(name, bm, collection=_st["coll"], parent=_st["root"], material=MATS[mats[0]], smooth=smooth)
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
def materials():
    MATS.clear()
    _mix = H._mix
    # gloss black lacquer, deep, a faint orange-peel in the clear coat
    m, nt, b = M._new("mat_guitar_01_lacquer")
    M._set(b, base="#060606", rough=0.32, spec=0.5, coat=1.0, coat_rough=0.025, coat_ior=1.52)
    sc = M._noise(nt, M._coords(nt), 900, detail=2)
    M._bump(nt, b, sc, 0.02, 0.0001, socket="Coat Normal")
    m.diffuse_color = M.rgba("#0b0b0b")
    MATS["lacquer"] = m

    def plain(key, name, colour, rough, **v):
        MATS[key] = M.principled(name, base=colour, rough=rough, **v)

    plain("white", "mat_guitar_01_binding", "#ece6d6", 0.3, coat=0.8, coat_rough=0.04, spec=0.5)
    plain("bblack", "mat_guitar_01_binding_black", "#0c0c0c", 0.3, coat=0.8, coat_rough=0.04, spec=0.5)
    plain("plastic", "mat_guitar_01_plastic", "#0f0f0f", 0.38, spec=0.5)
    plain("cream", "mat_guitar_01_cream", "#e9dfc6", 0.4, spec=0.5)
    plain("nut", "mat_guitar_01_nut", "#efe9da", 0.45, sss=0.1, sss_scale=0.002)
    plain("dark", "mat_guitar_01_dark", "#080808", 0.7)
    plain("felt", "mat_guitar_01_foam", "#1c1b1a", 0.85)

    # ebony board: near-black with a brown streak, dry
    m, nt, b = M._new("mat_guitar_01_ebony")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.05)
    nt.links.new(M._coords(nt), mp.inputs["Vector"])
    g = M._noise(nt, mp.outputs[0], 300, detail=6, rough=0.6, distortion=0.5)
    nt.links.new(M._ramp(nt, g, [(0.35, "#0d0a08"), (0.75, "#241912")]), b.inputs["Base Color"])
    M._set(b, rough=0.5, spec=0.45)
    M._bump(nt, b, g, 0.05, 0.0002)
    m.diffuse_color = M.rgba("#140f0c")
    MATS["ebony"] = m

    # mother of pearl blocks
    m, nt, b = M._new("mat_guitar_01_pearl")
    n1 = M._noise(nt, M._coords(nt), 650, detail=5, rough=0.7, distortion=1.5)
    nt.links.new(M._ramp(nt, n1, [(0.3, "#f4f1ea"), (0.45, "#dfe9ec"), (0.6, "#f1e6ec"), (0.75, "#fbfaf4"),
                                  (0.9, "#d8ded6")]), b.inputs["Base Color"])
    M._set(b, rough=0.18, coat=0.9, coat_rough=0.03, spec=0.6)
    M._bump(nt, b, n1, 0.08, 0.00015)
    m.diffuse_color = M.rgba("#ece9e2")
    MATS["pearl"] = m

    # tortoise guard: dark red-brown mottling under a gloss
    m, nt, b = M._new("mat_guitar_01_tortoise")
    co = M._coords(nt, scale=(1.0, 1.0, 1.6))
    n1 = M._noise(nt, co, 110, detail=6, rough=0.62, distortion=1.2)
    n2 = M._noise(nt, co, 170, detail=3, rough=0.5)
    c1 = M._ramp(nt, n1, [(0.4, "#0c0302"), (0.52, "#1e0603"), (0.62, "#3a1005"), (0.72, "#55200a")])
    nt.links.new(_mix(nt, H._maprange(nt, n2, 0.55, 0.7), c1, "#150503"), b.inputs["Base Color"])
    M._set(b, rough=0.3, coat=0.9, coat_rough=0.03, spec=0.5)
    m.diffuse_color = M.rgba("#3a0e06")
    MATS["tortoise"] = m

    for key, name, c0, c1, r0, r1 in (("gold", "mat_guitar_01_gold", "#e7c374", "#c9a35a", 0.14, 0.24),
                                      ("gold_dark", "mat_guitar_01_gold_dark", "#bf9c5c", "#93783f", 0.28, 0.4)):
        m, nt, b = M._new(name)
        tn = M._noise(nt, M._coords(nt), 380, detail=4)
        nt.links.new(M._ramp(nt, tn, [(0.45, c0), (0.85, c1)]), b.inputs["Base Color"])
        M._set(b, metal=1.0)
        H._rough_noise(nt, b, r0, r1)
        m.diffuse_color = M.rgba(c0)
        MATS[key] = m
    m, nt, b = M._new("mat_guitar_01_frets")
    M._set(b, base="#cfccc3", metal=1.0)
    H._rough_noise(nt, b, 0.18, 0.28)
    m.diffuse_color = M.rgba("#cfccc3")
    MATS["frets"] = m

    # strings: plain bright steel, wound nickel with the winding as a bump
    m, nt, b = M._new("mat_guitar_01_strings")
    w = H._attr(nt, "wound")
    nt.links.new(_mix(nt, w, "#bcbfc2", "#aaa596"), b.inputs["Base Color"])
    nt.links.new(_mix(nt, w, 0.22, 0.34, "FLOAT"), b.inputs["Roughness"])
    M._set(b, metal=1.0)
    uvn = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uvn.outputs[0], sep.inputs[0])
    wave = M._math(nt, "SINE", M._math(nt, "MULTIPLY", sep.outputs["X"], 2 * math.pi / 0.32), 1.0)
    hh = nt.nodes.new("ShaderNodeMath")
    hh.operation = "MULTIPLY"
    nt.links.new(wave, hh.inputs[0])
    nt.links.new(w, hh.inputs[1])
    M._bump(nt, b, hh.outputs[0], 0.6, 0.00006)
    m.diffuse_color = M.rgba("#b4b5b3")
    MATS["strings"] = m
    return MATS


MI = {}          # material key -> slot index, per object being built


def strip_uv(bm, rings, segments=4):
    """Lite only: UVs for the bands between the rings (binding, rims) as straight strips, in mm (arc
    length along, ring spacing across), cut into `segments` islands, faces flagged `strip`; the export
    smart-projects everything else and packs both. A smart projection turns these thin bands at all
    angles, and the 1024 atlas then draws the binding's edge as a staircase."""
    if not _st["lite"]:
        return
    uv = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")
    fl = bm.faces.layers.int.get("strip") or bm.faces.layers.int.new("strip")
    n = len(rings[0])
    where = {}
    for k, rr in enumerate(rings):
        for i, v in enumerate(rr):
            where[id(v)] = (k, i)
    ref = rings[0]
    s = [0.0]
    for i in range(1, n + 1):
        s.append(s[-1] + (ref[i % n].co - ref[i - 1].co).length)
    h = [0.0]
    for k in range(1, len(rings)):
        h.append(h[-1] + (rings[k][0].co - rings[k - 1][0].co).length)
    seg_of = lambda i: min(segments - 1, int(s[i] / s[n] * segments))   # noqa: E731
    seg_start = {}
    for i in range(n):
        seg_start.setdefault(seg_of(i), s[i])
    for f in bm.faces:
        ks = [where.get(id(v)) for v in f.verts]
        if len(ks) != 4 or any(x is None for x in ks):
            continue
        idx = [x[1] for x in ks]
        lo = min(idx)
        if max(idx) - lo > 1:                      # the closing quad: index n-1 and 0
            lo = n - 1
        sg = seg_of(lo)
        s0 = seg_start[sg]
        f[fl] = 1
        for lp, (k, i) in zip(f.loops, ks):
            si = s[n] if (i == 0 and lo == n - 1) else s[i]
            lp[uv].uv = (si - s0, h[k])


def _slots(keys):
    MI.clear()
    for i, k in enumerate(keys):
        MI[k] = i
    return keys


# ---------------------------------------------------------------------------
# body: rims, the arched top and back, multi-ply binding (real rings, one material per ply)
# ---------------------------------------------------------------------------
def build_body():
    mats = _slots(["lacquer", "white", "bblack"])
    O = H.ccw(H.resample(BODY, Q("body_step")))
    N = H.smooth_normals(O, 6.0)
    bm = bmesh.new()
    at, ab = G["arch_top"], G["arch_back"]
    # rings from the top's inner ply edge, out over the edge, down the rim, in over the back
    seq = []                                 # (inset, z, material of the band from the previous ring)
    if Q("plies"):
        d = sum(w for _, w in G["binding_top"])
        seq.append((d, float(arch(d, at)), None))
        for col, w in reversed(G["binding_top"]):
            d -= w
            dd = max(d, 0.5)
            seq.append((dd, float(arch(dd, at)), "white" if col == "white" else "bblack"))
    else:
        seq.append((3.6, float(arch(3.6, at)), None))
        seq.append((0.5, float(arch(0.5, at)), "white"))
    seq.append((0.0, -0.6, "white"))
    seq.append((0.0, -G["binding_side_h"], "white"))
    seq.append((0.0, -T + G["binding_back_h"], "lacquer"))
    seq.append((0.0, -T + 0.6, "white"))
    seq.append((0.5, -T - float(arch(0.5, ab)), "white"))
    if Q("plies"):
        d = 0.0
        for col, w in G["binding_back"]:
            d += w
            seq.append((d, -T - float(arch(d, ab)), "white" if col == "white" else "bblack"))
    else:
        seq.append((2.4, -T - float(arch(2.4, ab)), "white"))
    rings = [H.ring(bm, H.inset(O, N, d), z) for d, z, _ in seq]
    for k in range(1, len(rings)):
        H.bridge(bm, rings[k - 1], rings[k], MI[seq[k][2]])
    strip_uv(bm, rings, segments=6)
    top = H.fill_cdt(bm, rings[0], Q("grid"), seq[0][1], True, MI["lacquer"])
    back = H.fill_cdt(bm, rings[-1], Q("grid"), seq[-1][1], False, MI["lacquer"])
    for vs, rise, sg in ((top, at, 1.0), (back, ab, -1.0)):
        if not vs:
            continue
        uu = np.array([v.co.x for v in vs])
        vv = np.array([v.co.y for v in vs])
        dz = arch(edge_dist(uu, vv), rise)
        for v, z in zip(vs, dz):
            v.co.z = (0.0 if sg > 0 else -T) + sg * z
    return finish("body", bm, mats, "body")


def _rim_point(v, side=1):
    """(u, v, outward normal) on the rim at body position v on one side."""
    best = None
    for (u0, v0), (u1, v1) in zip(BODY, BODY[1:] + BODY[:1]):
        if (v0 - v) * (v1 - v) <= 0 and v0 != v1:
            u = u0 + (u1 - u0) * (v - v0) / (v1 - v0)
            if u * side > 0 and (best is None or abs(u) > abs(best[0])):
                n = Vector((v1 - v0, -(u1 - u0))).normalized()
                best = (u, n)
    u, n = best
    if n.x * side < 0:
        n = -n
    return u, n


def build_rim_hardware():
    """Two output jacks on the treble rim, the guard's bracket, the tail strap button."""
    lite = _st["lite"]
    seg = Q("small") + 6
    bm = bmesh.new()
    holes = bmesh.new()
    for v in G["jacks_v"]:
        u, n = _rim_point(v)
        c = Vector((u, v, -T / 2))
        nn = Vector((n.x, n.y, 0))
        H.lathe(bm, [(0, -0.2), (G["jack_d"] / 2, -0.2), (G["jack_d"] / 2, 0.6), (G["jack_d"] / 2 - 1.0, 1.4),
                     (6.2, 1.4), (5.5, 4.0), (4.6, 4.0), (0, 1.0)], c, nn, seg)
        H.cyl(holes, 3.2, c + nn * 3.6, c + nn * 4.1, Q("small"))
    # the strap button at the tail
    sb = [(0, -2.5), (5.2, -2.5), (5.5, 0.3), (5.2, 1.2), (2.9, 2.2), (2.6, 5.5), (3.4, 7.0), (5.5, 8.0),
          (5.6, 9.0), (4.6, 10.4), (2.5, 11.0), (0, 11.1)]
    if lite:
        sb = [sb[0], sb[1], sb[4], sb[5], sb[8], sb[11]]
    for v in G["strap_buttons_v"]:
        H.lathe(bm, sb, (0.0, v, -T / 2), (0, -1, 0), seg)
    # the guard bracket: a gold foot on the rim, an arm in over the top to the guard's underside
    vb = G["guard_bracket_v"]
    u, n = _rim_point(vb)
    gz = G["guard_z"]
    tip = min(GUARD, key=lambda p: (p[0] - u) ** 2 * 0.3 + (p[1] - vb) ** 2)
    nn = Vector((n.x, n.y, 0.0))
    H.lathe(bm, [(0, -0.3), (5.5, -0.3), (5.5, 1.2), (4.0, 2.0), (0, 2.0)], Vector((u, vb, -6.0)), nn, Q("small"))
    path = [Vector((u + n.x * 1.5, vb + n.y * 1.5, -6.0)), Vector((u + n.x * 1.5, vb + n.y * 1.5, 2.0)),
            Vector((u - n.x * 4.0, vb - n.y * 4.0, gz - 2.5)), Vector((tip[0] + 6.0 * n.x, tip[1] + 6.0 * n.y, gz - 0.2))]
    H.tube(bm, path, 1.6, Q("small") if not lite else 4)
    o = finish("rim_hardware", bm, ["gold"], "body", bev=0.3)
    finish("rim_holes", holes, ["dark"], "body")
    return o


# ---------------------------------------------------------------------------
# neck: board (bound ebony), frets, blocks, nut, the shaft with its heel and the head transition
# ---------------------------------------------------------------------------
def _loft(bm, sections, seg_mats, cap0=None, cap1=None):
    """sections: [(v, [(u, z)])], same length; seg_mats[i]: material index of segment i (closed ring)."""
    rings = [[bm.verts.new((u, v, z)) for u, z in prof] for v, prof in sections]
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            try:
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
                f.material_index = seg_mats[i]
            except ValueError:
                pass
    if cap0 is not None:
        H.cap(bm, rings[0], cap0)
    if cap1 is not None:
        H.cap(bm, rings[-1][::-1], cap1)
    return rings


def _board_profile(w):
    n = Q("arc")
    wi = w - BB
    us = [-wi + 2 * wi * k / n for k in range(n + 1)]
    pts = [(-w, board_top(-w) - 0.4), (-w + 0.4, board_top(-w + 0.4))] + [(u, board_top(u)) for u in us] + \
          [(w - 0.4, board_top(w - 0.4)), (w, board_top(w) - 0.4), (w, ZC - BT), (-w, ZC - BT)]
    mats = [MI["white"], MI["white"]] + [MI["ebony"]] * n + [MI["white"], MI["white"], MI["white"], MI["ebony"],
                                                                 MI["white"]]
    return pts, mats


def build_board():
    _slots(["ebony", "white"])
    v0 = G["v_board_end"]
    vs = [v0]
    while vs[-1] < VN - 1e-6:
        vs.append(min(VN, vs[-1] + Q("neck_dv")))
    secs, mats = [], None
    for v in vs:
        pts, mats = _board_profile(neck_w(v) / 2)
        secs.append((v, pts))
    bm = bmesh.new()
    _loft(bm, secs, mats, cap0=MI["white"], cap1=MI["ebony"])
    return finish("board", bm, ["ebony", "white"], "neck", frame=NECK_M)


def build_frets_blocks_nut():
    fw, fh = G["fret_wire"]
    na, npf = Q("fret_arc"), Q("fret_prof")
    bm = bmesh.new()
    for x in FRETS:
        v = VN - x
        w = neck_w(v) / 2 - BB - 0.1
        loops = []
        for i in range(na + 1):
            u = -w + 2 * w * i / na
            hs = 1.0 if abs(u) < w - 1.0 else 0.4 + 0.6 * (w - abs(u)) / 1.0
            base = board_top(u) - 0.2
            crown = board_top(u) + fh * hs
            prof = [(v + fw / 2 * math.cos(math.pi * k / npf), base + (crown - base) * math.sin(math.pi * k / npf))
                    for k in range(npf + 1)]
            loops.append([bm.verts.new((u, vv, z)) for vv, z in prof])
        for a, b in zip(loops, loops[1:]):
            H.bridge(bm, b, a, closed=True)
        H.cap(bm, loops[0])
        H.cap(bm, loops[-1][::-1])
    finish("frets", bm, ["frets"], "neck", frame=NECK_M)
    # pearl blocks between the frets, following the radius
    bm = bmesh.new()
    prev = 0.0
    nseg = 6 if not _st["lite"] else 2
    for k, x in enumerate(FRETS, 1):
        if k in G["blocks"]:
            gap = x - prev
            vc = VN - (prev + x) / 2
            ln = gap * G["block_len_frac"]
            w = neck_w(vc) / 2 - G["block_margin"]
            secs = []
            for vv in (vc - ln / 2, vc + ln / 2):
                top = [(-w + 2 * w * i / nseg, board_top(-w + 2 * w * i / nseg) + 0.03) for i in range(nseg + 1)]
                bot = [(u, z - 0.6) for u, z in top[::-1]]
                secs.append((vv, top + bot))
            _slots(["pearl"])
            _loft(bm, secs, [0] * len(secs[0][1]), cap0=0, cap1=0)
        prev = x
    finish("blocks", bm, ["pearl"], "neck", frame=NECK_M)
    # the nut: white, its top on the radius, slotted by the strings (rich)
    bm = bmesh.new()
    hw = G["nut_w"] / 2
    n = Q("arc")
    ntop = ZC + FH + 0.45
    top = [(-hw + 2 * hw * k / n, ntop - (-hw + 2 * hw * k / n) ** 2 / (2 * R_BOARD)) for k in range(n + 1)]
    H.prism_uz(bm, [(hw, HZ0 - 0.2)] + top[::-1] + [(-hw, HZ0 - 0.2)], VN, VN + NL)
    finish("nut", bm, ["nut"], "neck", frame=NECK_M, bev=0.5)


def _shaft_profile(w, zt, zb, p):
    n = Q("cseg")
    pts = [(-w + 0.15, zt), (w - 0.15, zt), (w, zt - 0.3)]
    for k in range(n + 1):
        a = math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        u = w * math.copysign(abs(c) ** (2 / p), c)
        z = (zt - 0.6) - ((zt - 0.6) - zb) * abs(s) ** (2 / p)
        pts.append((u, z))
    pts.append((-w, zt - 0.3))
    return pts


def build_neck_shaft():
    """Mahogany, black: the tenon under the board over the body, the heel down the upper rim to the
    back, the neck's rounded C, and the turn into the angled head (the back's line runs on)."""
    _slots(["lacquer"])
    t1, t12 = G["neck_t1"], G["neck_t12"]
    zt = ZC - BT
    v0 = G["v_board_end"] + 0.5
    secs = []
    vs = [v0, VJ - 6, VJ - 2]
    v = VJ
    while v < VN:
        vs.append(v)
        v += Q("neck_dv") if v > VJ + 50 else Q("neck_dv") / 2
    vs.append(VN)
    for v in vs:
        w = neck_w(v) / 2 - 0.05
        back = ZC - (t1 + (t12 - t1) * (VN - v) / (SC / 2))
        if v <= VJ:
            zb, p = -3.0, 9.0                                         # the tenon, inside the body
        else:
            k = min(1.0, (v - VJ) / 42.0)
            sm = k * k * (3 - 2 * k)
            zb = (-T + 3.0) * (1 - sm) + back * sm                   # the heel, down the rim to the back
            p = 4.5 * (1 - sm) + 2.4 * sm
        secs.append((v, _shaft_profile(w, zt, zb, p)))
    # into the head: the top drops to the face line, the back to the head's back line
    hb = lambda vv: HZ0 - max(0.0, vv - (VN + NL)) * TAN_H          # face, neck frame
    for k in range(1, 9 if not _st["lite"] else 3):
        vv = VN + 32.0 * k / (8 if not _st["lite"] else 2)
        f = k / (8 if not _st["lite"] else 2)
        back0 = ZC - t1
        zb = back0 + ((hb(vv) - HT / math.cos(math.atan(TAN_H))) - back0) * f ** 0.8
        w = G["nut_w"] / 2 + (min(head_half_w(vv - VN), 30.0) - G["nut_w"] / 2) * f
        secs.append((vv, _shaft_profile(w - 0.3, hb(vv) - 0.3, zb, 2.4 + 3.0 * f)))
    bm = bmesh.new()
    _loft(bm, secs, [0] * len(secs[0][1]), cap0=0, cap1=0)
    o = finish("neck", bm, ["lacquer"], "neck", frame=NECK_M)
    # the strap button on the heel's back
    bm = bmesh.new()
    sb = [(0, -2.5), (5.2, -2.5), (5.5, 0.3), (5.2, 1.2), (2.9, 2.2), (2.6, 5.5), (3.4, 7.0), (5.5, 8.0),
          (5.6, 9.0), (4.6, 10.4), (2.5, 11.0), (0, 11.1)]
    if _st["lite"]:
        sb = [sb[0], sb[1], sb[4], sb[5], sb[8], sb[11]]
    vh = VJ + 14.0
    H.lathe(bm, sb, (0.0, vh, -T + 6.0), (0, 0.35, -1), Q("small") + 6)
    finish("heel_button", bm, ["gold"], "body", frame=NECK_M)
    return o


def build_headstock():
    """The head: black face and back, its edge bound (a white line on the face, a white band on the
    side); a plain bell truss-rod cover, black with a white edge, two screws. No inlay, no text."""
    _slots(["lacquer", "white"])
    O = H.ccw(H.resample(HEAD + [HEAD[0]], Q("head_step")))
    N = H.smooth_normals(O, 3.0)
    bm = bmesh.new()
    lite = _st["lite"]
    seq = [(1.4, HZ0, None), (0.3, HZ0, "white"), (0.0, HZ0 - 0.4, "white"), (0.0, HZ0 - 3.0, "white"),
           (0.0, HZ0 - HT + 0.4, "lacquer"), (0.4, HZ0 - HT, "lacquer")]
    if lite:
        seq = [(1.4, HZ0, None), (0.0, HZ0, "white"), (0.0, HZ0 - 3.0, "white"), (0.0, HZ0 - HT, "lacquer")]
    rings = [H.ring(bm, H.inset(O, N, d), z) for d, z, _ in seq]
    for k in range(1, len(rings)):
        H.bridge(bm, rings[k - 1], rings[k], MI[seq[k][2]])
    strip_uv(bm, rings, segments=2)
    H.fill_cdt(bm, rings[0], 12.0 if not lite else 0, HZ0, True, MI["lacquer"])
    H.fill_cdt(bm, rings[-1], 12.0 if not lite else 0, seq[-1][1], False, MI["lacquer"])
    o = finish("headstock", bm, ["lacquer", "white"], "neck", frame=HEAD_M)
    # truss-rod cover (the bell), 2-ply: white under black
    tc = G["truss_cover"]
    b0, b1, wb, wm = tc["bottom_b"], tc["top_b"], tc["w_bottom"] / 2, tc["w_mid"] / 2
    half = [(wb, b0), (wb - 0.6, b0 + 4), (wm + 3.5, b0 + 13), (wm + 0.5, b0 + 21), (wm, b0 + 28), (wm + 0.6, b0 + 37),
            (wm - 0.5, b0 + 44), (wm - 3.0, b1 - 4), (0.0, b1)]
    bell = spline(half + [(-a, b) for a, b in half[-2::-1]], closed=True, n=4 if not lite else 1)
    bm = bmesh.new()
    H.prism_uv(bm, [(a, VN + b) for a, b in bell], HZ0 - 0.05, HZ0 + 0.8)
    w_n = H.smooth_normals(H.ccw(bell), 2.0)
    inner = H.inset(H.ccw(bell), w_n, 0.9)
    bk = bmesh.new()
    H.prism_uv(bk, [(a, VN + b) for a, b in inner], HZ0 + 0.7, HZ0 + tc["t"])
    finish("truss_edge", bm, ["white"], "neck", frame=HEAD_M)
    finish("truss_cover", bk, ["bblack" if "bblack" in MATS else "plastic"], "neck", frame=HEAD_M, bev=0.3)
    if not lite:
        bm = bmesh.new()
        for b in (b0 + 5.0, b1 - 5.5):
            H.cyl(bm, 1.6, (0, VN + b, HZ0 + tc["t"] - 0.2), (0, VN + b, HZ0 + tc["t"] + 0.9), 12, dome=0.6)
        finish("truss_screws", bm, ["gold"], "neck", frame=HEAD_M)
    return o


def build_tuners():
    """3 + 3 gold sealed tuners (Grover-type): hex bushings on the face, posts, housings on the back,
    shafts out past the edge and stepped oval buttons. Plain, no stamp."""
    lite = _st["lite"]
    bm = bmesh.new()
    zb = HZ0 - HT                           # the back
    zs = zb - 6.0                           # the shafts
    for pa, pb in G["tuner_posts"]:
        sg = 1 if pa > 0 else -1
        pv = VN + pb
        if not lite:
            H.lathe(bm, [(0, 0), (G["bushing_d"] / 2, 0), (G["bushing_d"] / 2, 1.6), (4.2, 2.4), (0, 2.4)],
                    (pa, pv, HZ0 - 0.1), (0, 0, 1), 6)                    # hex nut
            H.cyl(bm, G["post_d"] / 2, (pa, pv, HZ0), (pa, pv, HZ0 + G["post_h"]), Q("cyl"), dome=0.8)
        else:
            H.cyl(bm, G["post_d"] / 2, (pa, pv, HZ0 - 0.5), (pa, pv, HZ0 + G["post_h"]), 6)
        # housing: a rounded box on the back, its long side across
        edge = head_half_w(pb)
        H.rbox(bm, 17.0, 14.0, zb - 12.0, zb + 0.3, (pa + sg * 3.0, pv), r=4.0, n=3 if not lite else 1)
        # shaft and button
        x0, x1 = pa + sg * 10.0, sg * (edge + 4.0)
        H.cyl(bm, 1.8, (x0, pv, zs), (x1, pv, zs), Q("small") if not lite else 4)
        kc = sg * (edge + 4.0 + 9.0)
        prof = [(0.0, -9.0), (2.4, -8.6), (5.0, -7.0), (6.8, -4.5), (7.6, -1.5), (7.4, 1.5), (6.2, 5.0), (4.0, 7.6),
                (2.0, 8.7), (0.0, 9.0)]
        if lite:
            prof = prof[::3] + [prof[-1]]
        n0 = len(bm.verts)
        H.lathe(bm, prof, (0, 0, 0), (1, 0, 0), 20 if not lite else 6)
        bm.verts.ensure_lookup_table()
        for vtx in bm.verts[n0:]:
            x, y, z = vtx.co
            vtx.co = Vector((kc + x, pv + y * 0.72, zs + z * 1.0))    # a chunky kidney, flatter along the neck
    o = finish("tuners", bm, ["gold"], "hardware", frame=HEAD_M, bev=0.5, angle=40)
    if not lite:
        bm = bmesh.new()
        for pa, pb in G["tuner_posts"]:
            top = HZ0 + G["post_h"]
            H.rbox(bm, G["post_d"] + 0.1, 1.0, top - 5.0, top + 0.02, (pa, VN + pb), 90, r=0.2, n=1)
            H.cyl(bm, 1.1, (pa, VN + pb, top - 1.0), (pa, VN + pb, top + 0.03), 10)
        finish("tuner_slots", bm, ["dark"], "hardware", frame=HEAD_M)
    return o


# ---------------------------------------------------------------------------
# hardware on the top: pickups, bridge, tailpiece, guard, controls
# ---------------------------------------------------------------------------
def build_pickups():
    pk = G["pickups"]
    cw, cl = pk["cover"]
    rw, rl = pk["ring"]
    lite = _st["lite"]
    rings = bmesh.new()
    covers = bmesh.new()
    poles = bmesh.new()
    screws = bmesh.new()
    for key in ("neck", "bridge"):
        v = pk[key]
        zs = string_z(v)
        ctop = zs - pk["under_string"]
        cbase = ctop - pk["cover_h"]
        zt = top_z(0, v)
        # the ring: wedge to the arch (lower at the outer bouts), top flat at the cover's base
        H.rbox(rings, rw, rl, zt - 2.5, cbase + 0.8, (0, v), r=5.0, n=4 if not lite else 1)
        # the cover: rounded box, its top edge rounded
        H.rbox(covers, cw, cl, cbase - 4.0, ctop, (0, v), r=2.5, n=4 if not lite else 1)
        if not lite:
            for u in strings_u(v):
                H.cyl(poles, 2.6, (u, v + 9.6, ctop - 0.3), (u, v + 9.6, ctop + 0.6), 14, dome=0.5)
            for su in (-1, 1):
                for sv in (-1, 1):
                    H.cyl(screws, 1.4, (su * (rw / 2 - 4.0), v + sv * (rl / 2 - 4.0), cbase + 0.5),
                          (su * (rw / 2 - 4.0), v + sv * (rl / 2 - 4.0), cbase + 1.6), 10, dome=0.6)
                H.cyl(screws, 1.6, (su * (cw / 2 + 4.5), v, cbase + 0.6), (su * (cw / 2 + 4.5), v, cbase + 1.8), 10,
                      dome=0.7)
    finish("pickup_rings", rings, ["plastic"], "pickguard", bev=0.6)
    o = finish("pickups", covers, ["gold"], "pickguard", bev=0.9, seg=3)
    if not lite:
        finish("poles", poles, ["gold_dark"], "pickguard")
        finish("pickup_screws", screws, ["gold"], "pickguard")
    return o


def saddle_v(i):
    return VS - G["saddle_back"][i]


def build_bridge():
    """The tune-o-matic on its two posts and thumbwheels; six notched saddles with their screws."""
    tm = G["tom"]
    lite = _st["lite"]
    v = tm["v"]
    ztop = ZS - 2.6                                         # the bridge's top, saddles crown above
    zbot = ztop - tm["h"]
    bm = bmesh.new()
    # the body: a channel, its ends rounded over the posts
    prof = [(-tm["w"] / 2, zbot), (tm["w"] / 2, zbot), (tm["w"] / 2, ztop - 1.0), (tm["w"] / 2 - 1.0, ztop),
            (-tm["w"] / 2 + 1.0, ztop), (-tm["w"] / 2, ztop - 1.0)]
    H.prism_vz(bm, [(v + a, z) for a, z in prof], -tm["l"] / 2 + 5.0, tm["l"] / 2 - 5.0)
    for sg in (-1, 1):
        H.cyl(bm, 5.0, (sg * tm["post_span"] / 2, v, zbot), (sg * tm["post_span"] / 2, v, ztop - 0.5), Q("small") + 4)
    o = finish("bridge", bm, ["gold"], "hardware", bev=0.5)
    # posts and thumbwheels down to the top
    bm = bmesh.new()
    for sg in (-1, 1):
        u = sg * tm["post_span"] / 2
        z0 = top_z(u, v)
        H.cyl(bm, 2.1, (u, v, z0 - 1.0), (u, v, ztop + 0.4), Q("small"), dome=1.2)
        rm = (lambda t, i: 1.0 + 0.04 * math.cos(t * 24)) if not lite else None
        H.lathe(bm, [(0, 0), (tm["wheel_d"] / 2, 0), (tm["wheel_d"] / 2, 2.6), (0, 2.6)], (u, v, zbot - 3.2),
                (0, 0, 1), Q("knurl"), rmod=rm)
        H.lathe(bm, [(0, 0), (4.0, 0), (4.0, 1.2), (0, 1.2)], (u, v, z0 - 0.4), (0, 0, 1), Q("small"))
    finish("bridge_posts", bm, ["gold_dark"], "hardware")
    # saddles and their intonation screws (heads towards the pickups)
    bm = bmesh.new()
    scr = bmesh.new()
    for i in range(len(G["strings"])):
        sv = saddle_v(i)
        u = strings_u(sv)[i]
        crown = ZS - u * u / (2 * R_BOARD) - G["gauges"][i] * 25.4 / 2
        prof = [(v - 3.6, ztop - 3.0), (v + 3.6, ztop - 3.0), (v + 3.6, crown - 1.6), (sv + 0.4, crown),
                (sv - 0.4, crown), (v - 3.6, crown - 2.0)]
        H.prism_vz(bm, prof, u - 3.8, u + 3.8)
        if not lite:
            H.cyl(scr, 1.3, (u, v + 3.0, ztop - 4.2), (u, v + 6.6, ztop - 4.2), 10)
            H.lathe(scr, [(0, 0), (2.4, 0), (2.4, 1.3), (1.5, 2.0), (0, 2.0)], (u, v + 5.6, ztop - 4.2), (0, 1, 0), 14)
    finish("saddles", bm, ["gold"], "hardware", bev=0.3, angle=30)
    if not lite:
        finish("saddle_screws", scr, ["gold_dark"], "hardware")
        # the retaining wire over the saddles
        bm = bmesh.new()
        path = [Vector((-tm["l"] / 2 + 6.0, v - 3.0, ztop - 1.0)), Vector((-tm["l"] / 2 + 8, v - 3.4, ztop + 1.2)),
                Vector((tm["l"] / 2 - 8, v - 3.4, ztop + 1.2)), Vector((tm["l"] / 2 - 6.0, v - 3.0, ztop - 1.0))]
        H.tube(bm, path, 0.45, 8)
        finish("bridge_wire", bm, ["gold_dark"], "hardware")
    return o


def tail_top():
    tp = G["tailpiece"]
    return top_z(0, tp["v"]) + tp["gap"] + tp["h"]


def build_tailpiece():
    """The fine-tuner tailpiece: a rounded gold bar on two studs, the six string anchors in black on
    its front face, six knurled fine-tuner screws behind."""
    tp = G["tailpiece"]
    lite = _st["lite"]
    v = tp["v"]
    z0 = top_z(0, v) + tp["gap"]
    z1 = z0 + tp["h"]
    w = tp["w"] / 2
    n = 10 if not lite else 3
    prof = [(v - w, z0)]
    for k in range(n + 1):
        a = math.pi * k / n
        prof.append((v - w * math.cos(a), z0 + 2.0 + (tp["h"] - 2.0) * math.sin(a)))
    prof += [(v + w, z0)]
    bm = bmesh.new()
    H.prism_vz(bm, prof, -tp["l"] / 2, tp["l"] / 2)
    o = finish("tailpiece", bm, ["gold"], "hardware", bev=1.2, seg=3)
    bm = bmesh.new()
    for sg in (-1, 1):
        u = sg * tp["stud_span"] / 2
        H.cyl(bm, 5.5, (u, v, z1 - 1.0), (u, v, z1 + 1.6), Q("small") + 4, dome=1.0)
        H.cyl(bm, 2.8, (u, v, top_z(u, v) - 1.0), (u, v, z0 + 0.5), Q("small"))
        H.lathe(bm, [(0, 0), (5.2, 0), (5.2, 1.0), (0, 1.0)], (u, v, top_z(u, v) - 0.3), (0, 0, 1), Q("small"))
    finish("tail_studs", bm, ["gold_dark"], "hardware")
    blk = bmesh.new()
    knob = bmesh.new()
    for i, u in enumerate(strings_u(v)):
        H.cyl(blk, 2.6, (u, v + w - 1.6, z0 + 5.0), (u, v + w + 0.15, z0 + 5.0), Q("small"))
        if not lite:
            rm = (lambda t, j: 1.0 + 0.06 * math.cos(t * 16))
            H.lathe(knob, [(0, 0), (3.4, 0), (3.4, 5.0), (2.4, 5.8), (0, 5.8)], (u, v - w + 0.5, z0 + 5.5), (0, -1, 0),
                    32, rmod=rm)
    finish("tail_anchors", blk, ["dark"], "hardware")
    if not lite:
        finish("fine_tuners", knob, ["gold"], "hardware", bev=0.2)
    return o


def build_pickguard():
    """Floating over the treble bout: tortoise, bound white, at guard_z over the rims' top edge."""
    _slots(["tortoise", "white"])
    O = H.ccw(H.resample(GUARD, Q("guard_step")))
    N = H.smooth_normals(O, 3.0)
    gz, t, gb = G["guard_z"], G["guard_t"], G["guard_binding"]
    seq = [(gb, gz + t, None), (0.3, gz + t, "white"), (0.0, gz + t - 0.3, "white"), (0.0, gz + 0.3, "white"),
           (0.3, gz, "white"), (gb, gz, "white")]
    bm = bmesh.new()
    rings = [H.ring(bm, H.inset(O, N, d), z) for d, z, _ in seq]
    for k in range(1, len(rings)):
        H.bridge(bm, rings[k - 1], rings[k], MI[seq[k][2]])
    strip_uv(bm, rings, segments=2)
    H.fill_cdt(bm, rings[0], 0, gz + t, True, MI["tortoise"])
    H.fill_cdt(bm, rings[-1], 0, gz, False, MI["tortoise"])
    o = finish("pickguard", bm, ["tortoise", "white"], "pickguard")
    if not _st["lite"]:
        bm = bmesh.new()                           # the screw into the neck pickup's ring
        p = max(GUARD, key=lambda q: q[1] - abs(q[0] - 35) * 2)
        H.cyl(bm, 1.6, (p[0] - 3.0, p[1] - 6.0, gz + t - 0.2), (p[0] - 3.0, p[1] - 6.0, gz + t + 0.9), 12, dome=0.6)
        finish("guard_screw", bm, ["gold"], "pickguard")
    return o


def build_controls():
    """Four black knurled knobs with gold caps, the toggle (gold nut, cream tip), the Varitone: a gold
    plate and a black pointer knob. Plain: no numbers, no words."""
    lite = _st["lite"]
    kn = G["knob"]
    r, h = kn["d"] / 2, kn["h"]
    knobs = bmesh.new()
    caps = bmesh.new()
    gold = bmesh.new()
    prof = [(0, 0), (r, 0), (r, 3.8), (r - 0.4, 4.6), (r - 1.6, 5.4), (r - 2.2, 9.0), (r - 2.6, h - 0.8), (r - 3.4, h),
            (0, h)]
    if lite:
        prof = [prof[0], prof[1], prof[2], prof[5], prof[7], prof[8]]

    def rm(t, i):
        return 1.0 + (0.035 * math.cos(t * 30) if i in (1, 2) else 0.0)
    for u, v in G["knobs"]:
        z0 = top_z(u, v)
        H.lathe(knobs, prof, (u, v, z0 - 0.4), (0, 0, 1), Q("knurl"), rmod=rm if not lite else None)
        H.cyl(caps, r - 4.0, (u, v, z0 + h - 0.6), (u, v, z0 + h + 0.25), Q("cyl"))
    # the toggle
    tu, tv = G["toggle"]
    z0 = top_z(tu, tv)
    H.lathe(gold, [(0, 0), (8.0, 0), (8.0, 0.6), (6.0, 1.2), (0, 1.2)], (tu, tv, z0 - 0.2), (0, 0, 1), Q("cyl"))
    H.lathe(gold, [(0, 0), (5.5, 0), (5.5, 3.2), (4.6, 4.0), (0, 4.0)], (tu, tv, z0 + 0.8), (0, 0, 1), 6 if not lite else 6)
    lever = [Vector((tu, tv, z0 + 3.0)), Vector((tu, tv + 6.0, z0 + 21.0))]
    H.tube(gold, lever, 1.5, Q("small"))
    tip = bmesh.new()
    H.lathe(tip, [(0, -1), (2.6, 0), (3.8, 3.0), (3.8, 7.0), (2.8, 10.0), (0, 10.8)], lever[1] - Vector((0, 1.3, 4.0)),
            (lever[1] - lever[0]).normalized(), Q("small"))
    # the Varitone: gold plate with 6 position ticks, a black pointer knob
    vt = G["varitone"]
    z0 = top_z(vt["u"], vt["v"])
    H.lathe(gold, [(0, 0), (vt["plate_d"] / 2, 0), (vt["plate_d"] / 2, 0.8), (vt["plate_d"] / 2 - 0.8, 1.2), (0, 1.2)],
            (vt["u"], vt["v"], z0 - 0.2), (0, 0, 1), Q("cyl") + 16)
    ticks = bmesh.new()
    if not lite:
        for k in range(6):
            a = math.radians(210 - k * 48)
            c = (vt["u"] + 15.5 * math.cos(a), vt["v"] + 15.5 * math.sin(a))
            H.rbox(ticks, 1.0, 3.0, z0 + 0.95, z0 + 1.08, c, math.degrees(a) - 90, r=0.3, n=1)
    H.lathe(knobs, [(0, 0), (7.0, 0), (7.0, 6.0), (6.0, 7.0), (0, 7.0)], (vt["u"], vt["v"], z0 + 0.9), (0, 0, 1),
            Q("cyl"))
    ptr = [(-5.5, -4.0), (5.5, -4.0), (3.2, 18.0), (0.0, 19.5), (-3.2, 18.0)]
    a = math.radians(-35)
    ptr = [(vt["u"] + x * math.cos(a) - y * math.sin(a), vt["v"] + x * math.sin(a) + y * math.cos(a)) for x, y in ptr]
    H.prism_uv(knobs, ptr, z0 + 4.0, z0 + 13.5)
    o = finish("knobs", knobs, ["plastic"], "pickguard", bev=0.5)
    finish("knob_caps", caps, ["gold"], "pickguard")
    finish("toggle", gold, ["gold"], "pickguard", bev=0.3)
    finish("toggle_tip", tip, ["cream"], "pickguard")
    if not lite:
        finish("varitone_ticks", ticks, ["white"], "pickguard")
    return o


# ---------------------------------------------------------------------------
# strings
# ---------------------------------------------------------------------------
WRAP_Z = (5.0, 5.5, 6.0, 6.5, 7.0, 7.5)
WRAP_TURNS = (1.8, 2.0, 2.4, 2.8, 3.2, 3.5)


def string_paths(coils=True):
    tp = G["tailpiece"]
    out = []
    zt = tail_top()
    nut_u = strings_u(NUT_P.y)
    for i, g in enumerate(G["gauges"]):
        rad = g * 25.4 / 2
        sv = saddle_v(i)
        ub = strings_u(sv)[i]
        ua = strings_u(tp["v"])[i]
        crown = ZS - ub * ub / (2 * R_BOARD)
        pts = [Vector((ua, tp["v"] + tp["w"] / 2 - 1.0, zt - 4.0 + rad)), Vector((ua, tp["v"] + tp["w"] / 2 + 1.2, zt - 1.5 + rad)),
               Vector((ub, sv, crown + rad))]
        un = nut_u[i]
        n_ = NUT_P + Vector((un, 0, -un * un / (2 * R_BOARD) - 0.3 + rad))
        if coils:
            for k in range(1, 24):
                t = k / 24
                pts.append(Vector((ub, sv, crown + rad)).lerp(n_, t))
        pts.append(n_)
        pts.append(NECK_M @ Vector((un, VN + NL, (NECK_M.inverted() @ n_).z)))   # over the nut's back edge
        pa, pb = _post_for(i)                       # the bass strings to the left posts, trebles right
        pr = G["post_d"] / 2 + rad
        side = 1 if pa < 0 else -1                         # wrap on the post's inner side
        q = Vector((pa + side * pr, VN + pb, HZ0 + WRAP_Z[i]))
        pts.append(HEAD_M @ q)
        if coils:
            a0 = 0.0 if side > 0 else math.pi
            sg = -1 if pa < 0 else 1
            steps = int(WRAP_TURNS[i] * 20)
            for k in range(1, steps + 1):
                tt = k / 20
                aa = a0 + sg * 2 * math.pi * tt
                pts.append(HEAD_M @ Vector((pa + pr * math.cos(aa), VN + pb + pr * math.sin(aa),
                                             HZ0 + WRAP_Z[i] - 2 * rad * 1.05 * tt)))
        out.append((pts, rad, 1.0 if g >= 0.024 else 0.0))
    return out


def _post_for(i):
    """Gibson 3 + 3: low E, A, D on the bass side (D nearest the nut), G, B, high E on the treble side
    (G nearest the nut)."""
    left = sorted([p for p in G["tuner_posts"] if p[0] < 0], key=lambda p: p[1])     # near the nut first
    right = sorted([p for p in G["tuner_posts"] if p[0] > 0], key=lambda p: p[1])
    return [left[2], left[1], left[0], right[0], right[1], right[2]][i]


def build_strings():
    bm = bmesh.new()
    wound = bm.verts.layers.float.new("wound")
    uv = bm.loops.layers.uv.new("UVMap")
    for pts, rad, w in string_paths(coils=not _st["lite"]):
        H.tube(bm, pts, rad, Q("tube"), uv=uv, attr=wound, aval=w)
    bmesh.ops.transform(bm, matrix=SPEC, verts=bm.verts)
    lite = _st["lite"]
    name = "guitar_01_strings" if not lite else "guitar_01_lite_strings"
    mat = MATS["strings"] if not lite else (bpy.data.materials.get("mat_guitar_01_strings_web") or
                                            M.principled("mat_guitar_01_strings_web", base="#b8b9b7", metal=1.0,
                                                         rough=0.3))
    o = geo.from_bmesh(name, bm, collection=_st["coll"], parent=_st["root"], material=mat, smooth=True)
    mid = (NUT_P + SAD_P) / 2
    geo.set_origin(o, S(0.0, mid.y, mid.z))
    o["group"] = "strings"
    _st["groups"].setdefault("strings", []).append(o)
    return o


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
GROUPS = ("body", "neck", "hardware", "pickguard", "strings")


def build_steps(parent=None, collection=None, lite=False):
    if not lite:
        BUILD_ORDER.clear()
    _st["groups"] = {}
    _st["lite"] = lite
    _st["Q"] = LITE if lite else RICH
    _st["prefix"] = "guitar_01_lite_" if lite else "guitar_01_part_"
    scene = bpy.context.scene
    coll = collection or bpy.data.collections.get("obj_guitars") or bpy.data.collections.new("obj_guitars")
    if coll.users == 0:
        scene.collection.children.link(coll)
    _st["coll"] = coll
    root = bpy.data.objects.new("guitar_01_lite_root" if lite else "guitar_01", None)
    if not lite:
        root.empty_display_type = "SPHERE"
        root.empty_display_size = 0.02
    coll.objects.link(root)
    names.set_name(root, root.name, data=False)
    root.parent = parent
    _st["root"] = root
    if "lacquer" not in MATS or MATS["lacquer"].name not in bpy.data.materials:
        materials()
    if not lite:
        yield "materials"
    build_body()
    build_rim_hardware()
    yield "body"
    build_board()
    build_frets_blocks_nut()
    build_neck_shaft()
    build_headstock()
    yield "neck"
    build_tuners()
    build_bridge()
    build_tailpiece()
    yield "hardware"
    build_pickguard()
    build_pickups()
    build_controls()
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


def W(root, u, v, z):
    return root.matrix_world @ S(u, v, z)


# ---------------------------------------------------------------------------
# exports
# ---------------------------------------------------------------------------
def parts(root):
    return [o for o in root.children if o.type == "MESH" and o.name != "guitar_01_strings"]


def export_rich(root):
    """guitar_01 + guitar_01_body (the parts joined, several materials: renders) + guitar_01_strings."""
    body = H._joined_copy(parts(root), "guitar_01_body", root)

    def undo():
        me = body.data
        bpy.data.objects.remove(body)
        bpy.data.meshes.remove(me)
    return [root, body, bpy.data.objects["guitar_01_strings"]], undo


def _cpu_cycles():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:                   # never set the Metal device in preferences under --factory-startup
        sc.cycles.device = "CPU"
    except Exception:
        pass
    sc.cycles.use_denoising = False


def export_lite(root, size=1024, orm_size=512, key="guitar_01"):
    """The web model: the lite parts joined into one mesh, smart-UV packed, base colour, roughness,
    metallic and AO baked from the same materials into a 1024 atlas and a 512 ORM, one material.
    Renames the rich root and strings while the export runs. Returns (objects, undo, info)."""
    scene = bpy.context.scene
    prev_engine = scene.render.engine
    prev_samples = scene.cycles.samples
    coll = root.users_collection[0]
    lroot = build(parent=root.parent, collection=coll, lite=True)
    lroot.matrix_world = root.matrix_world.copy()
    bpy.context.view_layer.update()
    lparts = [o for o in lroot.children if o.type == "MESH" and o.name != f"{key}_lite_strings"]
    body = geo.join(lparts, f"{key}_lite_body")
    lstr = bpy.data.objects[f"{key}_lite_strings"]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    if "UVMap" not in body.data.uv_layers:
        body.data.uv_layers.new(name="UVMap")
    flag = [0] * len(body.data.polygons)
    if "strip" in body.data.attributes:
        body.data.attributes["strip"].data.foreach_get("value", flag)
    for p, f in zip(body.data.polygons, flag):
        p.select = not f
    with H._ctx(body):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.006, correct_aspect=True)
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
        bpy.ops.object.mode_set(mode="OBJECT")
    if "strip" in body.data.attributes:
        body.data.attributes.remove(body.data.attributes["strip"])
    _cpu_cycles()
    hidden = []
    for o in scene.objects:
        if o is not body and o.type in ("MESH", "CURVE", "FONT") and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    world = scene.world
    old_ao = world.light_settings.distance
    world.light_settings.distance = 0.03
    base = H._image(f"{key}_atlas", size)
    rough = H._image(f"{key}_rough_tmp", orm_size, True)
    metal = H._image(f"{key}_metal_tmp", orm_size, True)
    ao = H._image(f"{key}_ao_tmp", orm_size, True)
    H._bake(body, base, "base", 2)
    H._bake(body, rough, "rough", 2)
    H._bake(body, metal, "metal", 2)
    H._bake(body, ao, "ao", 32)
    world.light_settings.distance = old_ao
    for o in hidden:
        o.hide_render = False
    orm = H._image(f"{key}_orm", orm_size, True)
    px = np.empty(orm_size * orm_size * 4, np.float32)
    ch = []
    for im in (ao, rough, metal):
        im.pixels.foreach_get(px)
        ch.append(px.reshape(-1, 4)[:, 0].copy())
    out = np.ones((orm_size * orm_size, 4), np.float32)
    out[:, 0] = 0.35 + 0.65 * ch[0]
    out[:, 1], out[:, 2] = ch[1], ch[2]
    orm.pixels.foreach_set(out.ravel())
    for im in (rough, metal, ao):
        bpy.data.images.remove(im)
    paths = {}
    for im, fn, q in ((base, f"{key}_atlas.jpg", 90), (orm, f"{key}_orm.jpg", 92)):
        p = os.path.join(C.OUT, fn)
        im.filepath_raw = p
        im.file_format = "JPEG"
        scene.render.image_settings.quality = q
        try:
            im.save(filepath=p, quality=q)
        except TypeError:
            im.save()
        paths[fn] = round(os.path.getsize(p) / 1024)
    m, nt, b = M._new(f"mat_{key}")
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
    gg.node_tree = H._gltf_group()
    nt.links.new(sep.outputs[0], gg.inputs["Occlusion"])
    M._set(b, spec=0.5)
    m.diffuse_color = M.rgba("#202020")
    body.data.materials.clear()
    body.data.materials.append(m)
    scene.render.engine = prev_engine
    scene.cycles.samples = prev_samples
    strings_rich = bpy.data.objects[f"{key}_strings"]
    root.name = f"{key}_rich"
    strings_rich.name = f"{key}_strings_rich"
    names.set_name(lroot, key, data=False)
    names.set_name(body, f"{key}_body")
    names.set_name(lstr, f"{key}_strings")
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    stris = sum(len(p.vertices) - 2 for p in lstr.data.polygons)
    info = {"body_triangles": tris, "strings_triangles": stris, "images_kb": paths}

    def undo():
        for o in (body, lstr):
            me = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
        bpy.data.objects.remove(lroot)
        root.name = key
        strings_rich.name = f"{key}_strings"
    return [lroot, body, lstr], undo, info


def check(root):
    probs = []
    for o in [root] + names.descendants(root):
        if not names.NAME_RE.match(o.name):
            probs.append(f"bad name {o.name}")
    s = bpy.data.objects.get("guitar_01_strings")
    if s is None or s.parent is not root:
        probs.append("guitar_01_strings missing")
    elif len(s.data.materials) != 1:
        probs.append("guitar_01_strings needs one material")
    if root.type != "EMPTY":
        probs.append("guitar_01 is not an empty")
    if probs:
        raise AssertionError("guitar_01: " + "; ".join(probs))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in names.descendants(root) if o.type == "MESH")
    return {"parts": len(names.descendants(root)), "triangles_before_bevels": tris,
            "pivot_spec_mm": [round(x, 1) for x in PIV], "hook_b": round(HOOK_B, 1), "scale_line_v": round(VS, 1),
            "string_z_at_saddle": round(ZS, 1)}
