"""guitar_03: Jimmy Page's 1971 double-neck (the EDS-1275 type), an exact replica in shape, hardware and
finish (decisions 2026-10-23; built from photos and specs, the owner's choice of 2026-11-13). No logos on
the heads, no wordmark, plain knobs.

Built from blender/lib/guitar_specs.py GUITAR_03 (the body, guard, controls; u from the body's centre line)
and GUITAR_03_N12 / GUITAR_03_N6 (each neck as Lucille's builder reads a guitar, u local to that neck).
props/guitar_01.py is loaded twice through lib/variant.py ("guitar_01" -> "guitar_03"), once per neck, and
each copy builds its neck, head, tuners, bridge, tailpiece, pickups and strings; its SPEC carries the neck's
offset across the body. guitar_01.py is not changed. What differs from Lucille is replaced here:
    the body          solid, flat, the SG bevels all round (front and back), cherry
    materials         cherry (aged), rosewood, nickel instead of gold, black guard, black head face,
                      aged keystone buttons
    markers           double parallelograms (pearl)
    tuners            Kluson-type: single housings on the back, keystone buttons
    tailpieces        a stop bar (6) and a fixed through-bar (12)
    the 12-string     six courses of pairs: strings, posts, saddles and poles by course
    controls          four black witch-hat knobs, the neck selector, the pickup selector, the jack on the top

Names (MESHES.md, obj_guitars): `guitar_03` (empty, midway between the two heads' hook contacts: the plan
hangs it on two hooks), `guitar_03_strings` (both necks' strings, one mesh, one material, origin midway
between the two string midpoints), `guitar_03_part_*` (joined into `guitar_03_body` by the exports).
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from lib import constants as C, geo, materials as M, names, variant
from lib.guitar_specs import GUITAR_03 as GB, spline
from props import guitar_02 as H

MM = C.MM
SRC = os.path.join(C.BLENDER_DIR, "props", "guitar_01.py")
N12 = variant.load(SRC, [("GUITAR_01", "GUITAR_03_N12"), ("guitar_01", "guitar_03")], "_guitar_03_n12")
N6 = variant.load(SRC, [("GUITAR_01", "GUITAR_03_N6"), ("guitar_01", "guitar_03")], "_guitar_03_n6")
NECKS = (("n12", N12, GB["necks"][0]), ("n6", N6, GB["necks"][1]))
T = GB["body_t"]
G = dict(GB, v_nut=N6.VN, body_t=T)

# ---------------------------------------------------------------------------
# frame: the pivot midway between the two heads' hook contacts
# ---------------------------------------------------------------------------
_pp = [Vector((off + m.PIV[0], m.PIV[1], m.PIV[2])) for _, m, off in NECKS]
_p = (_pp[0] + _pp[1]) / 2
PIV = (_p.x, _p.y, _p.z)
SPEC = Matrix(((MM, 0, 0, -PIV[0] * MM),
               (0, 0, -MM, PIV[2] * MM),
               (0, MM, 0, -PIV[1] * MM),
               (0, 0, 0, 1)))
for _, m, off in NECKS:
    m.OFF = Matrix.Translation((off, 0.0, 0.0))
    m.SPEC = SPEC @ m.OFF
BODY_FRAME = N6.OFF.inverted()          # N6.finish(frame=BODY_FRAME) builds in the body's frame


def S(u, v, z):
    return SPEC @ Vector((u, v, z))


# ---------------------------------------------------------------------------
# the body's top: flat, the bevel by distance in from the edge
# ---------------------------------------------------------------------------
BODY = H.ccw(spline(GB["body"], n=3))
_BA = np.array(BODY)
_BB = np.roll(_BA, -1, axis=0)


def edge_dist(u, v):
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


_BEV = sorted(GB["bevel"])


def bevel_z(d):
    ds, zs = zip(*_BEV)
    return np.interp(d, ds, zs)


def top_z(u, v):
    return float(bevel_z(edge_dist(u, v)))


for _, m, off in NECKS:                 # the necks' hardware sits on this top (u local -> body)
    m.top_z = (lambda o: (lambda u, v: top_z(u + o, v)))(off)

# ---------------------------------------------------------------------------
# the 12-string: courses of pairs
# ---------------------------------------------------------------------------
G12 = N12.G


def _courses12(v):
    t = (v - N12.VS) / (N12.NUT_P.y - N12.VS)
    spread = G12["bridge_spread"] + (G12["nut_spread"] - G12["bridge_spread"]) * t
    return [-spread / 2 + spread * i / 5 for i in range(6)], t


def strings_u12(v):
    cs, t = _courses12(v)
    gap = G12["pair_gap"][1] + (G12["pair_gap"][0] - G12["pair_gap"][1]) * t
    out = []
    for c in cs:
        out += [c - gap / 2, c + gap / 2]
    return out


N12.strings_u = strings_u12
N12.WRAP_Z = tuple(z for z in N12.WRAP_Z for _ in (0, 1))
N12.WRAP_TURNS = tuple(z for z in N12.WRAP_TURNS for _ in (0, 1))


def _post12(i):
    left = sorted([p for p in G12["tuner_posts"] if p[0] < 0], key=lambda p: -p[1])     # far from the nut first
    right = sorted([p for p in G12["tuner_posts"] if p[0] > 0], key=lambda p: p[1])     # near first
    return (left + right)[i]


N12._post_for = _post12
_G12_6 = dict(G12, strings=G12["strings"][::2], gauges=G12["gauges"][::2])


def _by_course(fn):
    """Run one of guitar_01's builders on the 12-string with six courses (saddles, poles)."""
    def run():
        N12.G = _G12_6
        N12.strings_u = lambda v: _courses12(v)[0]
        N12.saddle_v = lambda i: N12.VS - G12["saddle_back"][i]
        try:
            return fn()
        finally:
            N12.G = G12
            N12.strings_u = strings_u12
            N12.saddle_v = lambda i: N12.VS - G12["saddle_back"][min(i // 2, 5)]
    return run


N12.saddle_v = lambda i: N12.VS - G12["saddle_back"][min(i // 2, 5)]
_bridge12, _pickups12 = _by_course(N12.build_bridge), _by_course(N12.build_pickups)

# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
MATS = {}


def materials():
    N6.materials()
    mats = N6.MATS
    # cherry: a deep translucent red over mahogany, a little faded and scratched (Page played it hard)
    m, nt, b = M._new("mat_guitar_03_cherry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.08)
    nt.links.new(M._coords(nt), mp.inputs["Vector"])
    g = M._noise(nt, mp.outputs[0], 160, detail=6, rough=0.6, distortion=0.6)
    base = M._ramp(nt, g, [(0.3, "#4c080b"), (0.55, "#5a0c0f"), (0.8, "#661312")])
    fade = M._noise(nt, M._coords(nt), 6.0, detail=2)
    base = H._mix(nt, H._maprange(nt, fade, 0.45, 0.75), base, "#6b1a18")
    nt.links.new(base, b.inputs["Base Color"])
    sc = nt.nodes.new("ShaderNodeMapping")
    sc.inputs["Scale"].default_value = (3.0, 0.4, 3.0)
    sc.inputs["Rotation"].default_value = (0.3, 0.9, 0.2)
    nt.links.new(M._coords(nt), sc.inputs["Vector"])
    scr = M._noise(nt, sc.outputs[0], 300, detail=3)
    M._set(b, rough=0.3, spec=0.5, coat=0.85, coat_ior=1.5)
    nt.links.new(H._mix(nt, H._maprange(nt, scr, 0.62, 0.68), 0.04, 0.22, "FLOAT"), b.inputs["Coat Roughness"])
    M._bump(nt, b, g, 0.03, 0.0002)
    m.diffuse_color = M.rgba("#5a0b0e")
    mats["lacquer"] = m
    # rosewood board
    m, nt, b = M._new("mat_guitar_03_rosewood")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.05)
    nt.links.new(M._coords(nt), mp.inputs["Vector"])
    g = M._noise(nt, mp.outputs[0], 300, detail=6, rough=0.6, distortion=0.6)
    nt.links.new(M._ramp(nt, g, [(0.3, "#2a160d"), (0.7, "#4f2b19")]), b.inputs["Base Color"])
    M._set(b, rough=0.55, spec=0.4)
    M._bump(nt, b, g, 0.06, 0.0002)
    m.diffuse_color = M.rgba("#3a2014")
    mats["ebony"] = m
    for key, name, c0, c1, r0, r1 in (("gold", "mat_guitar_03_nickel", "#d3d1c9", "#b9b6aa", 0.14, 0.26),
                                      ("gold_dark", "mat_guitar_03_nickel_dark", "#a9a69c", "#8d8a80", 0.3, 0.42)):
        m, nt, b = M._new(name)
        tn = M._noise(nt, M._coords(nt), 380, detail=4)
        nt.links.new(M._ramp(nt, tn, [(0.45, c0), (0.85, c1)]), b.inputs["Base Color"])
        M._set(b, metal=1.0)
        H._rough_noise(nt, b, r0, r1)
        m.diffuse_color = M.rgba(c0)
        mats[key] = m
    mats["guard"] = M.principled("mat_guitar_03_guard", base="#0b0b0b", rough=0.25, coat=0.6, coat_rough=0.08,
                                 spec=0.5)
    mats["headface"] = M.principled("mat_guitar_03_headface", base="#070707", rough=0.3, coat=0.9,
                                    coat_rough=0.05, spec=0.5)
    mats["keystone"] = M.principled("mat_guitar_03_keystone", base="#c9cfae", rough=0.35, coat=0.4,
                                    coat_rough=0.15, spec=0.5, sss=0.05, sss_scale=0.002)
    MATS.clear()
    MATS.update(mats)
    N12.MATS.clear()
    N12.MATS.update(mats)
    return MATS


# ---------------------------------------------------------------------------
# body-level parts (built through N6.finish with the body's frame)
# ---------------------------------------------------------------------------
def fin(key, bm, mats, group, **kw):
    return N6.finish(key, bm, mats, group, frame=BODY_FRAME, **kw)


def build_body():
    lite = N6._st["lite"]
    O = H.ccw(H.resample(BODY, 2.5 if not lite else 12.0))
    N = H.smooth_normals(O, 5.0)
    top = sorted(GB["bevel"], reverse=True)              # inner first
    back = list(GB["bevel_back"])
    if lite:
        top = [top[0], top[2], top[4], top[-1]]
        back = [back[0], back[2], back[-1]]
    seq = [(d, z) for d, z in top] + [(d, z) for d, z in back]
    bm = bmesh.new()
    rings = [H.ring(bm, H.inset(O, N, d), z) for d, z in seq]
    for k in range(1, len(rings)):
        H.bridge(bm, rings[k - 1], rings[k], 0)
    N6.strip_uv(bm, rings, segments=6)
    H.fill_cdt(bm, rings[0], 9.0 if not lite else 45.0, seq[0][1], True, 0)
    H.fill_cdt(bm, rings[-1], 9.0 if not lite else 45.0, seq[-1][1], False, 0)
    return fin("body", bm, ["lacquer"], "body")


def build_guard():
    """Black, 3-ply (black, white, black: the white shows as a line on the bevelled edge), on the top."""
    lite = N6._st["lite"]
    O = H.ccw(H.resample(H.ccw(spline(GB["pickguard"], n=4)), 2.0 if not lite else 9.0))
    N = H.smooth_normals(O, 3.0)
    t = GB["guard_t"]
    seq = [(1.6, t, None), (1.0, t - 0.6, 0), (0.65, t - 1.0, 1), (0.0, 0.6, 0), (0.0, 0.0, 0)]
    if lite:
        seq = [(1.6, t, None), (0.8, t - 0.8, 1), (0.0, 0.0, 0)]
    bm = bmesh.new()
    rings = [H.ring(bm, H.inset(O, N, d), z) for d, z, _ in seq]
    for k in range(1, len(rings)):
        H.bridge(bm, rings[k - 1], rings[k], seq[k][2])
    N6.strip_uv(bm, rings, segments=2)
    H.fill_cdt(bm, rings[0], 6.0 if not lite else 25.0, t, True, 0)
    H.fill_cdt(bm, rings[-1], 6.0 if not lite else 25.0, 0.0, False, 0)
    vs = list(bm.verts)
    dz = bevel_z(edge_dist(np.array([v.co.x for v in vs]), np.array([v.co.y for v in vs])))
    for v, z in zip(vs, dz):
        v.co.z += max(float(z), -3.0) + 0.15          # it bends a little over the bevel near the waist
    o = fin("pickguard", bm, ["guard", "white"], "pickguard")
    if not lite:
        bm = bmesh.new()
        for k in range(0, len(O), max(1, len(O) // 12)):
            u, v = H.inset([O[k]], [N[k]], 4.0)[0]
            z = top_z(u, v) + t + 0.15
            H.cyl(bm, 1.7, (u, v, z - 0.3), (u, v, z + 0.8), 12, dome=0.6)
        fin("guard_screws", bm, ["gold"], "pickguard")
    return o


def build_controls():
    lite = N6._st["lite"]
    kn = GB["knob"]
    r, h = kn["d"] / 2, kn["h"]
    bm = bmesh.new()
    # witch hats: a flared skirt, a cone, a rounded top
    prof = [(0, 0), (r, 0), (r, 2.2), (r - 0.8, 3.4), (r - 3.6, 4.6), (r - 5.4, 9.0), (r - 6.4, h - 1.5),
            (r - 7.2, h - 0.3), (0, h)]
    if lite:
        prof = [prof[0], prof[1], prof[2], prof[4], prof[6], prof[8]]

    def rm(t_, i):
        return 1.0 + (0.03 * math.cos(t_ * 24) if i in (4, 5, 6) else 0.0)
    for u, v in GB["knobs"]:
        H.lathe(bm, prof, (u, v, top_z(u, v) - 0.3), (0, 0, 1), 48 if not lite else 12,
                rmod=rm if not lite else None)
    o = fin("knobs", bm, ["plastic"], "pickguard", bev=0.4)
    nickel = bmesh.new()
    tips = bmesh.new()
    for u, v in (GB["neck_selector"], GB["pickup_toggle"]):
        z0 = top_z(u, v) + (GB["guard_t"] + 0.15 if (u, v) == tuple(GB["neck_selector"]) else 0.0)
        H.lathe(nickel, [(0, 0), (9.5, 0), (9.5, 0.7), (7.0, 1.4), (0, 1.4)], (u, v, z0 - 0.2), (0, 0, 1), 32)
        H.lathe(nickel, [(0, 0), (5.5, 0), (5.5, 3.0), (4.6, 3.8), (0, 3.8)], (u, v, z0 + 1.0), (0, 0, 1), 6)
        lever = [Vector((u, v, z0 + 3.0)), Vector((u, v + 6.0, z0 + 21.0))]
        H.tube(nickel, lever, 1.5, 12 if not lite else 4)
        H.lathe(tips, [(0, -1), (2.6, 0), (3.8, 3.0), (3.8, 7.0), (2.8, 10.0), (0, 10.8)],
                lever[1] - Vector((0, 1.3, 4.0)), (lever[1] - lever[0]).normalized(), 14 if not lite else 6)
    ju, jv = GB["jack"]
    z0 = top_z(ju, jv)
    H.lathe(nickel, [(0, 0), (10.0, 0), (10.0, 0.6), (8.0, 1.2), (0, 1.2)], (ju, jv, z0 - 0.2), (0, 0, 1), 32)
    H.lathe(nickel, [(0, 0), (6.5, 0), (6.5, 2.6), (5.6, 3.4), (0, 3.4)], (ju, jv, z0 + 0.9), (0, 0, 1), 6)
    hole = bmesh.new()
    H.cyl(hole, 3.3, (ju, jv, z0 + 3.4), (ju, jv, z0 + 4.4), 16)
    fin("toggles", nickel, ["gold"], "pickguard", bev=0.3)
    fin("toggle_tips", tips, ["cream"], "pickguard")
    fin("jack_hole", hole, ["dark"], "pickguard")
    # strap buttons on the rim
    sb = [(0, -2.5), (5.2, -2.5), (5.5, 0.3), (5.2, 1.2), (2.9, 2.2), (2.6, 5.5), (3.4, 7.0), (5.5, 8.0),
          (5.6, 9.0), (4.6, 10.4), (2.5, 11.0), (0, 11.1)]
    bm = bmesh.new()
    for u, v, ang in GB["strap_buttons"]:
        d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0.0)
        H.lathe(bm, sb, (u, v, -T / 2), d, 18 if not lite else 6)
    fin("strap_buttons", bm, ["gold"], "body", bev=0.3)
    return o


# ---------------------------------------------------------------------------
# per neck: board markers, tuners, head, tailpiece (replacing Lucille's)
# ---------------------------------------------------------------------------
def build_frets_markers_nut(m):
    G_ = m.G
    fw, fh = G_["fret_wire"]
    lite = m._st["lite"]
    na, npf = m.Q("fret_arc"), m.Q("fret_prof")
    bm = bmesh.new()
    for x in m.FRETS:
        v = m.VN - x
        w = m.neck_w(v) / 2 - m.BB - 0.1
        loops = []
        for i in range(na + 1):
            u = -w + 2 * w * i / na
            hs = 1.0 if abs(u) < w - 1.0 else 0.4 + 0.6 * (w - abs(u))
            base = m.board_top(u) - 0.2
            crown = m.board_top(u) + fh * hs
            prof = [(v + fw / 2 * math.cos(math.pi * k / npf), base + (crown - base) * math.sin(math.pi * k / npf))
                    for k in range(npf + 1)]
            loops.append([bm.verts.new((u, vv, z)) for vv, z in prof])
        for a, b in zip(loops, loops[1:]):
            H.bridge(bm, b, a, closed=True)
        H.cap(bm, loops[0])
        H.cap(bm, loops[-1][::-1])
    m.finish("frets", bm, ["frets"], "neck", frame=m.NECK_M)
    # double parallelograms: two slanted pearl quads across the board, each fret space listed
    bm = bmesh.new()
    prev = 0.0
    ns = 4 if not lite else 1
    for k, x in enumerate(m.FRETS, 1):
        if k in G_["blocks"]:
            gap = x - prev
            vc = m.VN - (prev + x) / 2
            ln = gap * G_["block_len_frac"]
            w = m.neck_w(vc) / 2 - G_["block_margin"]
            s = 0.3 * ln
            for (x0, x1) in ((-w, -1.4 - s), (1.4, w - s)):
                # corners: nut side at x0..x1, body side shifted by s (towards the treble side)
                quad = [(x0, vc + ln / 2), (x1, vc + ln / 2), (x1 + s, vc - ln / 2), (x0 + s, vc - ln / 2)]
                grid = []
                for i in range(ns + 1):
                    a_ = i / ns
                    pa = (quad[0][0] + (quad[1][0] - quad[0][0]) * a_, quad[0][1])
                    pb = (quad[3][0] + (quad[2][0] - quad[3][0]) * a_, quad[3][1])
                    grid.append((pa, pb))
                tv = [(bm.verts.new((pa[0], pa[1], m.board_top(pa[0]) + 0.03)),
                       bm.verts.new((pb[0], pb[1], m.board_top(pb[0]) + 0.03))) for pa, pb in grid]
                bv = [(bm.verts.new((pa[0], pa[1], m.board_top(pa[0]) - 0.6)),
                       bm.verts.new((pb[0], pb[1], m.board_top(pb[0]) - 0.6))) for pa, pb in grid]
                for i in range(ns):
                    H.cap(bm, (tv[i][0], tv[i + 1][0], tv[i + 1][1], tv[i][1])[::-1])
                    H.cap(bm, (bv[i][0], bv[i][1], bv[i + 1][1], bv[i + 1][0])[::-1])
                    H.cap(bm, (tv[i][0], bv[i][0], bv[i + 1][0], tv[i + 1][0]))
                    H.cap(bm, (tv[i][1], tv[i + 1][1], bv[i + 1][1], bv[i][1]))
                H.cap(bm, (tv[0][0], tv[0][1], bv[0][1], bv[0][0]))
                H.cap(bm, (tv[ns][0], bv[ns][0], bv[ns][1], tv[ns][1]))
        prev = x
    m.finish("markers", bm, ["pearl"], "neck", frame=m.NECK_M)
    bm = bmesh.new()
    hw = G_["nut_w"] / 2
    n = m.Q("arc")
    ntop = m.ZC + fh + 0.45
    top = [(-hw + 2 * hw * k / n, ntop - (-hw + 2 * hw * k / n) ** 2 / (2 * m.R_BOARD)) for k in range(n + 1)]
    H.prism_uz(bm, [(hw, m.HZ0 - 0.2)] + top[::-1] + [(-hw, m.HZ0 - 0.2)], m.VN, m.VN + m.NL)
    m.finish("nut", bm, ["nut"], "neck", frame=m.NECK_M, bev=0.5)


def build_headstock(m):
    """Unbound: a black face (the veneer), cherry sides and back, a plain bell truss-rod cover."""
    lite = m._st["lite"]
    G_ = m.G
    O = H.ccw(H.resample(m.HEAD + [m.HEAD[0]], m.Q("head_step")))
    N = H.smooth_normals(O, 3.0)
    HZ0, HT = m.HZ0, m.HT
    seq = [(0.6, HZ0, None), (0.0, HZ0 - 0.6, 1), (0.0, HZ0 - 1.4, 1), (0.0, HZ0 - HT + 0.6, 0), (0.6, HZ0 - HT, 0)]
    if lite:
        seq = [(0.0, HZ0, None), (0.0, HZ0 - 1.4, 1), (0.0, HZ0 - HT, 0)]
    bm = bmesh.new()
    rings = [H.ring(bm, H.inset(O, N, d), z) for d, z, _ in seq]
    for k in range(1, len(rings)):
        H.bridge(bm, rings[k - 1], rings[k], seq[k][2])
    m.strip_uv(bm, rings, segments=2)
    H.fill_cdt(bm, rings[0], 12.0 if not lite else 0, HZ0, True, 1)
    H.fill_cdt(bm, rings[-1], 12.0 if not lite else 0, seq[-1][1], False, 0)
    o = m.finish("headstock", bm, ["lacquer", "headface"], "neck", frame=m.HEAD_M)
    tc = G_["truss_cover"]
    b0, b1, wb, wm = tc["bottom_b"], tc["top_b"], tc["w_bottom"] / 2, tc["w_mid"] / 2
    half = [(wb, b0), (wb - 0.6, b0 + 4), (wm + 3.5, b0 + 13), (wm + 0.5, b0 + 21), (wm, b0 + 28), (wm + 0.6, b0 + 37),
            (wm - 0.5, b0 + 44), (wm - 3.0, b1 - 4), (0.0, b1)]
    bell = spline(half + [(-a, b) for a, b in half[-2::-1]], closed=True, n=4 if not lite else 1)
    bm = bmesh.new()
    H.prism_uv(bm, [(a, m.VN + b) for a, b in bell], HZ0 - 0.05, HZ0 + 0.8)
    inner = H.inset(H.ccw(bell), H.smooth_normals(H.ccw(bell), 2.0), 0.9)
    bk = bmesh.new()
    H.prism_uv(bk, [(a, m.VN + b) for a, b in inner], HZ0 + 0.7, HZ0 + tc["t"])
    m.finish("truss_edge", bm, ["white"], "neck", frame=m.HEAD_M)
    m.finish("truss_cover", bk, ["plastic"], "neck", frame=m.HEAD_M, bev=0.3)
    if not lite:
        bm = bmesh.new()
        for b in (b0 + 5.0, b1 - 5.5):
            H.cyl(bm, 1.6, (0, m.VN + b, HZ0 + tc["t"] - 0.2), (0, m.VN + b, HZ0 + tc["t"] + 0.9), 12, dome=0.6)
        m.finish("truss_screws", bm, ["gold"], "neck", frame=m.HEAD_M)
    return o


def build_tuners(m):
    """Kluson-type: a bushing and post on the face, a single housing with a domed cover on the back, the
    shaft out past the edge, an aged keystone button. Plain, no stamp."""
    lite = m._st["lite"]
    G_ = m.G
    HZ0, HT, VN = m.HZ0, m.HT, m.VN
    met = bmesh.new()
    keys = bmesh.new()
    zb = HZ0 - HT
    zs = zb - 5.5
    for pa, pb in G_["tuner_posts"]:
        sg = 1 if pa > 0 else -1
        pv = VN + pb
        H.lathe(met, [(0, 0), (4.6, 0), (4.6, 1.4), (3.8, 2.0), (0, 2.0)], (pa, pv, HZ0 - 0.1), (0, 0, 1),
                16 if not lite else 6)
        H.cyl(met, G_["post_d"] / 2, (pa, pv, HZ0), (pa, pv, HZ0 + G_["post_h"]), 16 if not lite else 6, dome=0.7)
        # the housing: 13 along the neck, 19 across, 10 deep, a domed cover
        H.rbox(met, 19.0, 13.0, zb - 9.0, zb + 0.2, (pa + sg * 2.0, pv), r=2.0, n=2 if not lite else 1)
        if not lite:
            H.rbox(met, 16.0, 10.5, zb - 10.2, zb - 8.8, (pa + sg * 2.0, pv), r=3.0, n=3)
        edge = m.head_half_w(pb)
        H.cyl(met, 1.6, (pa + sg * 9.0, pv, zs), (sg * (edge + 5.0), pv, zs), 10 if not lite else 4)
        # keystone: a flat trapezoid, wider at the outer end, its edges rounded
        x0, x1 = sg * (edge + 4.0), sg * (edge + 22.0)
        n0 = len(keys.verts)
        prof = [(-6.0, -2.8), (6.0, -2.8), (7.6, 2.8), (-7.6, 2.8)]       # (along v, along z) at the outer end
        inner = [(-4.4, -2.4), (4.4, -2.4), (4.4, 2.4), (-4.4, 2.4)]
        ring0 = [keys.verts.new((x0, pv + a, zs + z * 0.0 + z)) for a, z in [(p[0], p[1]) for p in inner]]
        ring1 = [keys.verts.new((x0 + (x1 - x0) * 0.25, pv + a * 1.0, zs + z)) for a, z in
                 [(-6.4, -3.0), (6.4, -3.0), (6.4, 3.0), (-6.4, 3.0)]]
        ring2 = [keys.verts.new((x1, pv + a, zs + z)) for a, z in [(-8.0, -2.6), (8.0, -2.6), (8.0, 2.6), (-8.0, 2.6)]]
        H.bridge(keys, ring0, ring1)
        H.bridge(keys, ring1, ring2)
        H.cap(keys, ring0[::-1] if sg > 0 else ring0)
        H.cap(keys, ring2 if sg > 0 else ring2[::-1])
        if not lite:
            H.cyl(met, 2.6, (x0 - sg * 1.5, pv, zs), (x0 + sg * 0.8, pv, zs), 12)       # the ferrule
    o = m.finish("tuners", met, ["gold"], "hardware", frame=m.HEAD_M, bev=0.3, angle=40)
    m.finish("tuner_keys", keys, ["keystone"], "hardware", frame=m.HEAD_M, bev=1.2, seg=3, angle=30)
    return o


def build_tailpiece(m):
    """6: the stop bar on two studs. 12: a fixed bar, the twelve strings through holes in its front."""
    tp = m.G["tailpiece"]
    lite = m._st["lite"]
    v = tp["v"]
    z0 = m.top_z(0, v) + tp["gap"]
    w = tp["w"] / 2
    n = 10 if not lite else 3
    prof = [(v - w, z0)]
    for k in range(n + 1):
        a = math.pi * k / n
        prof.append((v - w * math.cos(a), z0 + 2.0 + (tp["h"] - 2.0) * math.sin(a)))
    prof += [(v + w, z0)]
    bm = bmesh.new()
    if m.G["tail_kind"] == "fixed12":
        H.rbox(bm, tp["l"], tp["w"] + 2.0, m.top_z(0, v) - 0.3, m.top_z(0, v) + 1.4, (0, v), r=3.0,
               n=3 if not lite else 1)                     # a base plate screwed to the top
        prof = [(v - w, z0 - tp["gap"] + 1.2)] + prof[1:-1] + [(v + w, z0 - tp["gap"] + 1.2)]
    H.prism_vz(bm, prof, -tp["l"] / 2, tp["l"] / 2)
    o = m.finish("tailpiece", bm, ["gold"], "hardware", bev=1.0, seg=3)
    bm = bmesh.new()
    holes = bmesh.new()
    if m.G["tail_kind"] == "stopbar":
        for sg in (-1, 1):
            u = sg * tp["stud_span"] / 2
            H.cyl(bm, 5.5, (u, v, z0 + tp["h"] - 1.0), (u, v, z0 + tp["h"] + 1.6), 18 if not lite else 6, dome=1.0)
            H.cyl(bm, 2.8, (u, v, m.top_z(u, v) - 1.0), (u, v, z0 + 0.5), 12 if not lite else 4)
            H.lathe(bm, [(0, 0), (5.2, 0), (5.2, 1.0), (0, 1.0)], (u, v, m.top_z(u, v) - 0.3), (0, 0, 1), 18)
    else:
        for u in (-tp["l"] / 2 + 6.0, 0.0, tp["l"] / 2 - 6.0):           # three screws through the bar
            H.cyl(bm, 2.4, (u, v - 2.0, z0 + tp["h"] - 4.0), (u, v - 2.0, z0 + tp["h"] - 0.2), 14, dome=0.8)
    for u in m.strings_u(v):
        H.cyl(holes, 1.0, (u, v + w - 1.0, z0 + 5.0), (u, v + w + 0.15, z0 + 5.0), 8 if not lite else 4)
    finish_kw = dict(bev=0.2) if bm.verts else {}
    if bm.verts:
        m.finish("tail_studs", bm, ["gold_dark"], "hardware", **finish_kw)
    m.finish("tail_holes", holes, ["dark"], "hardware")
    return o


# the strings: each neck builds its own, renamed at once; joined after both
def _strings(m, tag):
    o = m.build_strings()
    names.set_name(o, f"guitar_03_{'lite_' if m._st['lite'] else ''}strings_{tag}")
    return o


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
GROUPS = ("body", "neck", "hardware", "pickguard", "strings")
BUILD_ORDER = []


def build_steps(parent=None, collection=None, lite=False):
    if not lite:
        BUILD_ORDER.clear()
    groups = {}
    scene = bpy.context.scene
    coll = collection or bpy.data.collections.get("obj_guitars") or bpy.data.collections.new("obj_guitars")
    if coll.users == 0:
        scene.collection.children.link(coll)
    root = bpy.data.objects.new("guitar_03_lite_root" if lite else "guitar_03", None)
    if not lite:
        root.empty_display_type = "SPHERE"
        root.empty_display_size = 0.02
    coll.objects.link(root)
    names.set_name(root, root.name, data=False)
    root.parent = parent
    for tag, m, _ in NECKS:
        m._st.update(coll=coll, root=root, lite=lite, Q=m.LITE if lite else m.RICH, groups=groups,
                     prefix=f"guitar_03_{'lite' if lite else 'part'}_{tag}_")
    N6._st["prefix"] = f"guitar_03_{'lite' if lite else 'part'}_"
    if "lacquer" not in MATS or MATS["lacquer"].name not in bpy.data.materials:
        materials()
    if not lite:
        yield "materials"
    build_body()
    yield "body"
    for tag, m, _ in NECKS:
        m._st["prefix"] = f"guitar_03_{'lite' if lite else 'part'}_{tag}_"
        m.build_board()
        build_frets_markers_nut(m)
        m.build_neck_shaft()
        build_headstock(m)
    yield "neck"
    for tag, m, _ in NECKS:
        m._st["prefix"] = f"guitar_03_{'lite' if lite else 'part'}_{tag}_"
        build_tuners(m)
        (_bridge12 if m is N12 else m.build_bridge)()
        build_tailpiece(m)
    yield "hardware"
    N6._st["prefix"] = f"guitar_03_{'lite' if lite else 'part'}_"
    build_guard()
    build_controls()
    for tag, m, _ in NECKS:
        m._st["prefix"] = f"guitar_03_{'lite' if lite else 'part'}_{tag}_"
        (_pickups12 if m is N12 else m.build_pickups)()
    yield "pickguard"
    for o in list(root.children):                   # Lucille's heel strap button: not on this guitar
        if o.name.endswith("heel_button"):
            for lst in groups.values():
                if o in lst:
                    lst.remove(o)
            me = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
    ss = [_strings(m, tag) for tag, m, _ in NECKS]
    mids = [Vector(o.location) for o in ss]
    st = geo.join(ss, f"guitar_03_{'lite_' if lite else ''}strings")
    geo.set_origin(st, (mids[0] + mids[1]) / 2)
    groups["strings"] = [st]
    yield "strings"
    for g in GROUPS if not lite else ():
        BUILD_ORDER.append((g, [o.name for o in groups.get(g, [])]))
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


def export_rich(root):
    return N6.export_rich(root)


def export_lite(root, size=1024, orm_size=512):
    N6.build = build
    return N6.export_lite(root, size, orm_size, key="guitar_03")


def check(root):
    probs = []
    for o in [root] + names.descendants(root):
        if not names.NAME_RE.match(o.name):
            probs.append(f"bad name {o.name}")
    s = bpy.data.objects.get("guitar_03_strings")
    if s is None or s.parent is not root:
        probs.append("guitar_03_strings missing")
    elif len(s.data.materials) != 1:
        probs.append("guitar_03_strings needs one material")
    if probs:
        raise AssertionError("guitar_03: " + "; ".join(probs))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in names.descendants(root) if o.type == "MESH")
    return {"parts": len(names.descendants(root)), "triangles_before_bevels": tris,
            "pivot_spec_mm": [round(x, 1) for x in PIV], "scale_line_v": round(N6.VS, 1),
            "string_z_at_saddle": round(N6.ZS, 1)}
