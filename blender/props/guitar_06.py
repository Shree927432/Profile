"""guitar_06: Tim Henson's TOD10 in Metallic Mauve, in the floor rack, slot 3. Exact in shape, hardware and
finish (decisions 2026-10-23), with two departures the decisions ask for: no logo on the head, and the board's
inlay is ours (the piano's tribal strokes, the tuning fork at the 12th: props/guitar_06_inlay.py), not the
Tree of Death.

Built from blender/lib/guitar_specs.py GUITAR_06 on Lucille's builder (props/guitar_01.py through
lib/variant.py, "guitar_01" -> "guitar_06") for the board, frets, neck, nut and strings; props/guitar_03.py
lends the unbound headstock. Replaced here: the body (rounded edges, mauve metallic), the materials (roasted
maple neck, ebony with the silver inlay, chrome), side dots, the six-in-line tuners, the truss-rod slot, the
pickups (cream open bobbins on black rings), the two-point tremolo and its arm, the controls (two dome knobs,
the five-way switch, the jack on the rim), the strap buttons, and the frame: the pivot is the rack contact,
as guitar_04's and guitar_05's.

Names: `guitar_06` (empty), `guitar_06_strings` (one mesh, one material, origin at the strings' midpoint),
`guitar_06_part_*` (joined into `guitar_06_body` by the exports).
"""
import math
import os
import subprocess

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from lib import constants as C, geo, materials as M, names, variant
from lib.guitar_specs import GUITAR_06 as G
from props import guitar_02 as H
from props import guitar_03 as G3

MM = C.MM
SRC = os.path.join(C.BLENDER_DIR, "props", "guitar_01.py")
M6 = variant.load(SRC, [("GUITAR_01", "GUITAR_06"), ("guitar_01", "guitar_06")], "_guitar_06")
T = G["body_t"]
BODY = M6.BODY
LEAN = C.LAYOUT["rack"]["lean"]
INLAY = os.path.join(C.OUT, "guitar_06_inlay.png")
INLAY_BOX = (-30.0, 30.0, 500.0)              # x0, x1 across, y1 from the nut (guitar_06_inlay.py)

_th = math.radians(LEAN)
_pu, _pv = min(BODY, key=lambda p: -p[0] * math.sin(_th) + p[1] * math.cos(_th))
PIV = (_pu, _pv, -T / 2)
SPEC = Matrix(((MM, 0, 0, -PIV[0] * MM),
               (0, 0, -MM, PIV[2] * MM),
               (0, MM, 0, -PIV[1] * MM),
               (0, 0, 0, 1)))
M6.PIV, M6.SPEC = PIV, SPEC
M6.top_z = lambda u, v: 0.0
M6._post_for = lambda i: sorted(G["tuner_posts"], key=lambda p: p[1])[i]      # low E nearest the nut
M6.G = dict(M6.G)
# the strings end in the bridge's saddle blocks, not at a tailpiece: guitar_01's string path starts at
# G["tailpiece"]; put that just behind the saddles at the saddle blocks' top
M6.G["tailpiece"] = dict(v=G["bridge2pt"]["saddle_v"] - 13.0, l=60.0, w=4.0, h=M6.ZS - 3.2, gap=0.0)


def S(u, v, z):
    return SPEC @ Vector((u, v, z))


MATS = M6.MATS


def _spec_uv(nt):
    """u and mm-from-the-nut (y) from the object coordinates (all parts are in the guitar's frame)."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    u = M._math(nt, "ADD", M._math(nt, "MULTIPLY", sep.outputs["X"], 1000.0), PIV[0])
    v = M._math(nt, "ADD", M._math(nt, "MULTIPLY", sep.outputs["Z"], 1000.0), PIV[1])
    y = M._math(nt, "SUBTRACT", M._math(nt, "MULTIPLY", v, -1.0), -M6.VN)            # VN - v
    return u, y


def materials():
    M6.materials()
    # Metallic Mauve: a dusty pink-violet with fine metallic flake, a soft gloss
    m, nt, b = M._new("mat_guitar_06_mauve")
    co = M._coords(nt)
    fl = M._noise(nt, co, 2400, detail=2)
    nt.links.new(M._ramp(nt, fl, [(0.35, "#9d6c72"), (0.65, "#ae7d82")]), b.inputs["Base Color"])
    M._set(b, metal=0.6, rough=0.3, spec=0.5, coat=0.6, coat_rough=0.12)
    M._bump(nt, b, fl, 0.05, 0.00005)
    m.diffuse_color = M.rgba("#c29294")
    MATS["lacquer"] = m
    MATS["headface"] = m
    # roasted maple, satin
    m, nt, b = M._new("mat_guitar_06_maple")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.05)
    nt.links.new(M._coords(nt), mp.inputs["Vector"])
    g = M._noise(nt, mp.outputs[0], 300, detail=5, rough=0.55, distortion=0.5)
    nt.links.new(M._ramp(nt, g, [(0.3, "#9a6a3c"), (0.7, "#b07d4a")]), b.inputs["Base Color"])
    M._set(b, rough=0.45, spec=0.5)
    M._bump(nt, b, g, 0.03, 0.0002)
    m.diffuse_color = M.rgba("#a57445")
    MATS["maple"] = m
    # ebony with the silver inlay (the mask from guitar_06_inlay.py)
    if not os.path.exists(INLAY):
        subprocess.run(["python3", "-I", os.path.join(C.BLENDER_DIR, "props", "guitar_06_inlay.py"), INLAY], check=True)
    img = bpy.data.images.load(INLAY, check_existing=True)
    img.colorspace_settings.name = "Non-Color"
    m, nt, b = M._new("mat_guitar_06_board")
    u, y = _spec_uv(nt)
    x0, x1, y1 = INLAY_BOX
    cx = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(M._math(nt, "MULTIPLY", M._math(nt, "SUBTRACT", u, x0), 1.0 / (x1 - x0)), cx.inputs[0])
    nt.links.new(M._math(nt, "SUBTRACT", M._math(nt, "MULTIPLY", y, -1.0 / y1), -1.0), cx.inputs[1])  # 1 - y/y1
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    tx.interpolation = "Cubic"
    tx.extension = "CLIP"
    nt.links.new(cx.outputs[0], tx.inputs["Vector"])
    mask = tx.outputs["Color"]
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.05)
    nt.links.new(M._coords(nt), mp.inputs["Vector"])
    g = M._noise(nt, mp.outputs[0], 300, detail=6, rough=0.6, distortion=0.5)
    ebony = M._ramp(nt, g, [(0.35, "#0d0a08"), (0.75, "#1f1611")])
    sil = M._noise(nt, M._coords(nt), 1500, detail=2)
    silver = M._ramp(nt, sil, [(0.4, "#d3d6db"), (0.7, "#e6e8ec")])          # brushed sterling, kept bright
    mk = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(mask, mk.inputs[0])
    k = H._maprange(nt, mk.outputs[0], 0.35, 0.65)
    nt.links.new(H._mix(nt, k, ebony, silver), b.inputs["Base Color"])
    nt.links.new(H._mix(nt, k, 0.5, 0.38, "FLOAT"), b.inputs["Roughness"])
    nt.links.new(H._mix(nt, k, 0.0, 0.55, "FLOAT"), b.inputs["Metallic"])
    M._set(b, spec=0.45)
    m.diffuse_color = M.rgba("#151010")
    MATS["ebony"] = m
    MATS["white"] = m                                   # unbound
    for key, name, c0, c1, r0, r1 in (("gold", "mat_guitar_06_chrome", "#d6d9dd", "#c4c7cb", 0.06, 0.14),
                                      ("gold_dark", "mat_guitar_06_chrome_dark", "#a9acb0", "#96999d", 0.18, 0.28)):
        m, nt, b = M._new(name)
        tn = M._noise(nt, M._coords(nt), 380, detail=4)
        nt.links.new(M._ramp(nt, tn, [(0.45, c0), (0.85, c1)]), b.inputs["Base Color"])
        M._set(b, metal=1.0)
        H._rough_noise(nt, b, r0, r1)
        m.diffuse_color = M.rgba(c0)
        MATS[key] = m
    MATS["bobbin"] = M.principled("mat_guitar_06_bobbin", base="#ece6d4", rough=0.35, spec=0.5, coat=0.3)
    MATS["dots_side"] = M.principled("mat_guitar_06_side_dots", base="#e9edf0", rough=0.3, spec=0.5)
    return MATS


def fin(key, bm, mats, group, **kw):
    return M6.finish(key, bm, mats, group, **kw)


# ---------------------------------------------------------------------------
def build_body():
    lite = M6._st["lite"]
    r = G["edge_r"]
    O = H.ccw(H.resample(BODY, 2.5 if not lite else 12.0))
    N = H.smooth_normals(O, 5.0)
    seg = 6 if not lite else 2
    seq = []
    for k in range(seg + 1):
        phi = math.pi / 2 * (1 - k / seg)
        seq.append((r * (1 - math.cos(phi)), -r + r * math.sin(phi)))
    for k in range(seg + 1):
        phi = -math.pi / 2 * k / seg
        seq.append((r * (1 - math.cos(phi)), -T + r + r * math.sin(phi)))
    bm = bmesh.new()
    rings = [H.ring(bm, H.inset(O, N, d), z) for d, z in seq]
    for k in range(1, len(rings)):
        H.bridge(bm, rings[k - 1], rings[k], 0)
    M6.strip_uv(bm, rings, segments=6)
    H.fill_cdt(bm, rings[0], 9.0 if not lite else 22.0, 0.0, True, 0)
    H.fill_cdt(bm, rings[-1], 9.0 if not lite else 45.0, -T, False, 0)
    forearm(bm, r)
    return fin("body", bm, ["lacquer"], "body")


def _bass_edge(v):
    """u of the body's bass (left) edge at v."""
    xs = []
    for (u0, v0), (u1, v1) in zip(BODY, BODY[1:] + BODY[:1]):
        if (v0 - v) * (v1 - v) <= 0 and v0 != v1:
            xs.append(u0 + (u1 - u0) * (v - v0) / (v1 - v0))
    return min(xs) if xs else 0.0


def _bell(v, v0, v1, peak):
    if v <= v0 or v >= v1:
        return 0.0
    t = (v - v0) / (v1 - v0)
    t = t / peak * 0.5 if t < peak else 0.5 + (t - peak) / (1 - peak) * 0.5
    return math.sin(math.pi * t) ** 1.4


def forearm(bm, r):
    """The forearm contour: the top and its roundover lowered along the lower bass edge, deepest at the
    edge, running out over `width` (the side below keeps its line, so the rim gets thinner there)."""
    fa = G["forearm"]
    for vtx in bm.verts:
        u, v, z = vtx.co
        if z < -r - 0.5:
            continue
        k = (_bass_edge(v) + fa["width"] - u) / fa["width"]
        k = max(0.0, min(1.0, k))
        vtx.co.z = z - fa["depth"] * _bell(v, fa["v0"], fa["v1"], fa["peak"]) * k ** 1.6


def build_frets_nut_side_dots():
    m = M6
    fw, fh = G["fret_wire"]
    na, npf = m.Q("fret_arc"), m.Q("fret_prof")
    bm = bmesh.new()
    for x in m.FRETS:
        v = m.VN - x
        w = m.neck_w(v) / 2 - 0.4
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
    m.finish("frets", bm, ["gold"], "neck", frame=m.NECK_M)
    # side dots on the bass edge of the board (the player's view)
    bm = bmesh.new()
    prev = 0.0
    for k, x in enumerate(m.FRETS, 1):
        if k in G["dots_side"]:
            vm = m.VN - (prev + x) / 2
            w = m.neck_w(vm) / 2
            zc = m.ZC - m.BT * 0.45
            for dy in ((-1.6, 1.6) if k in (12, 24) else (0.0,)):
                H.cyl(bm, 1.1, (-w + 0.3, vm + dy, zc), (-w - 0.05, vm + dy, zc), 10 if not m._st["lite"] else 5)
        prev = x
    m.finish("side_dots", bm, ["dots_side"], "neck", frame=m.NECK_M)
    bm = bmesh.new()
    hw = G["nut_w"] / 2
    n = m.Q("arc")
    ntop = m.ZC + fh + 0.45
    top = [(-hw + 2 * hw * k / n, ntop - (-hw + 2 * hw * k / n) ** 2 / (2 * m.R_BOARD)) for k in range(n + 1)]
    H.prism_uz(bm, [(hw, m.HZ0 - 0.2)] + top[::-1] + [(-hw, m.HZ0 - 0.2)], m.VN, m.VN + m.NL)
    m.finish("nut", bm, ["plastic"], "neck", frame=m.NECK_M, bev=0.5)


def build_head_extras():
    """The truss-rod slot at the head's foot (a dark rounded recess)."""
    m = M6
    ts = G["truss_slot"]
    bm = bmesh.new()
    H.rbox(bm, ts["w"], ts["b1"] - ts["b0"], m.HZ0 - 0.2, m.HZ0 + 0.05, (0, m.VN + (ts["b0"] + ts["b1"]) / 2),
           r=ts["w"] / 2 - 0.2, n=4 if not m._st["lite"] else 1)
    m.finish("truss_slot", bm, ["dark"], "neck", frame=m.HEAD_M)


def _bass_edge_hit(p, d):
    best = None
    P, D_ = Vector(p), Vector(d)
    for (a0, b0), (a1, b1) in zip(M6.HEAD, M6.HEAD[1:] + M6.HEAD[:1]):
        A, B = Vector((a0, b0)), Vector((a1, b1))
        e = B - A
        den = D_.x * e.y - D_.y * e.x
        if abs(den) < 1e-9:
            continue
        w = A - P
        t = (w.x * e.y - w.y * e.x) / den
        s = (w.x * D_.y - w.y * D_.x) / den
        if t > 0 and 0 <= s <= 1 and (best is None or t < best):
            best = t
    return best or 20.0


def build_tuners():
    """Six in line, locking, chrome: a round bushing and post on the face (the locking thumbwheel on the
    back), the housing on the back, the shaft straight out to the bass side, a rounded chrome button."""
    m = M6
    lite = m._st["lite"]
    HZ0, HT, VN = m.HZ0, m.HT, m.VN
    d = Vector(G["tuner_dir"]).normalized()
    ang = math.degrees(math.atan2(d.y, d.x))
    bm = bmesh.new()
    zb = HZ0 - HT
    zs = zb - 6.0
    for pa, pb in G["tuner_posts"]:
        pv = VN + pb
        H.lathe(bm, [(0, 0), (5.6, 0), (5.6, 1.2), (4.6, 2.0), (0, 2.0)], (pa, pv, HZ0 - 0.1), (0, 0, 1),
                24 if not lite else 6)
        H.cyl(bm, G["post_d"] / 2, (pa, pv, HZ0 - 0.2), (pa, pv, HZ0 + G["post_h"]), 16 if not lite else 6, dome=0.7)
        H.rbox(bm, 16.0, 13.0, zb - 11.0, zb + 0.3, (pa + d.x * 2.5, pv + d.y * 2.5), ang, r=4.0, n=3 if not lite else 1)
        if not lite:
            H.cyl(bm, 6.5, (pa, pv, zb - 11.0), (pa, pv, zb - 14.0), 32)          # the locking wheel
        t = _bass_edge_hit((pa, pv), d)
        a0 = Vector((pa, pv)) + d * 9.0
        a1 = Vector((pa, pv)) + d * (t + 4.0)
        H.cyl(bm, 1.8, (a0.x, a0.y, zs), (a1.x, a1.y, zs), 10 if not lite else 4)
        kc = Vector((pa, pv)) + d * (t + 13.0)
        n0 = len(bm.verts)
        prof = [(0.0, -9.0), (2.4, -8.6), (5.0, -7.0), (6.8, -4.5), (7.6, -1.5), (7.4, 1.5), (6.2, 5.0), (4.0, 7.6),
                (2.0, 8.7), (0.0, 9.0)]
        if lite:
            prof = prof[::3] + [prof[-1]]
        H.lathe(bm, prof, (0, 0, 0), (1, 0, 0), 20 if not lite else 6)
        bm.verts.ensure_lookup_table()
        for vtx in bm.verts[n0:]:
            x, y, z = vtx.co
            y *= 0.62
            vtx.co = Vector((kc.x + x * d.x - y * d.y, kc.y + x * d.y + y * d.x, zs + z))
    return m.finish("tuners", bm, ["gold"], "hardware", frame=m.HEAD_M, bev=0.5, angle=40)


def build_pickups():
    """Black rings with ears (two screws), two cream bobbins each, six chrome poles in each bobbin."""
    m = M6
    lite = m._st["lite"]
    pk = G["pickups"]
    bw, bl = pk["bobbin"]
    rw, rl = pk["ring"]
    rings, bob, poles = bmesh.new(), bmesh.new(), bmesh.new()
    for key in ("neck", "bridge"):
        v = pk[key]
        zs = m.string_z(v)
        top = zs - pk["under_string"]
        base = top - pk["cover_h"]
        H.rbox(rings, rw, rl, -1.0, base + 1.2, (0, v), r=4.0, n=4 if not lite else 1)
        for sg in (-1, 1):                                    # the ears
            H.rbox(rings, 14.0, 12.0, -1.0, base + 0.6, (sg * (rw / 2 + 4.0), v), r=5.5, n=4 if not lite else 1)
        for sv in (-1, 1):
            H.rbox(bob, bw, bl, base - 3.0, top, (0, v + sv * bl / 2), r=2.0, n=3 if not lite else 1)
            if not lite:
                for u in m.strings_u(v):
                    H.cyl(poles, 1.9, (u, v + sv * bl / 2, top - 0.3), (u, v + sv * bl / 2, top + 0.4), 12, dome=0.4)
    fin("pickup_rings", rings, ["plastic"], "pickguard", bev=0.5)
    o = fin("pickups", bob, ["bobbin"], "pickguard", bev=0.7, seg=3)
    if not lite:
        fin("poles", poles, ["gold"], "pickguard")
    return o


def build_bridge():
    """The two-point tremolo: a chrome plate in its rout, two pivot posts, six block saddles with their
    intonation screws and height screws, the arm socket at the treble rear corner, the arm."""
    m = M6
    lite = m._st["lite"]
    br = G["bridge2pt"]
    v = br["v"]
    bm = bmesh.new()
    H.rbox(bm, br["w"], br["l"], 0.2, 2.4, (0, v), r=3.0, n=3 if not lite else 1)
    o = fin("bridge", bm, ["gold"], "hardware", bev=0.4)
    rout = bmesh.new()
    H.rbox(rout, br["w"] + 4.0, br["l"] + 4.0, 0.02, 0.12, (0, v), r=4.5, n=4 if not lite else 1)
    fin("bridge_rout", rout, ["dark"], "hardware")
    bm = bmesh.new()
    for sg in (-1, 1):
        u = sg * br["post_u"]
        H.cyl(bm, 4.6, (u, br["post_v"], 0.0), (u, br["post_v"], 4.2), 20 if not lite else 6, dome=1.4)
    sad = bmesh.new()
    scr = bmesh.new()
    for i in range(6):
        sv = m.saddle_v(i)
        u = m.strings_u(sv)[i]
        crown = m.ZS - u * u / (2 * m.R_BOARD) - G["gauges"][i] * 25.4 / 2
        prof = [(sv - 13.0, 2.4), (sv + 4.0, 2.4), (sv + 4.0, crown - 3.0), (sv + 0.8, crown), (sv - 1.0, crown),
                (sv - 13.0, crown - 2.5)]
        H.prism_vz(sad, prof, u - 4.7, u + 4.7)
        if not lite:
            H.cyl(scr, 1.3, (u, sv - 13.0, 5.5), (u, v - br["l"] / 2 - 1.0, 5.5), 10)
            H.lathe(scr, [(0, 0), (2.4, 0), (2.4, 1.3), (1.5, 2.0), (0, 2.0)], (u, v - br["l"] / 2 + 0.5, 5.5),
                    (0, -1, 0), 14)
    fin("bridge_posts", bm, ["gold"], "hardware")
    fin("saddles", sad, ["gold"], "hardware", bev=0.4, angle=30)
    if not lite:
        fin("saddle_screws", scr, ["gold_dark"], "hardware")
    # the arm: a socket, a short rise, a gentle bend, resting towards the neck pickup
    a = G["arm"]
    bm = bmesh.new()
    H.cyl(bm, 3.0, (a["u"], a["v"], 1.5), (a["u"], a["v"], 6.5), 16 if not lite else 6)
    tu, tv = a["tip"]
    path = [Vector((a["u"], a["v"], 4.0)), Vector((a["u"], a["v"], 12.0)), Vector((a["u"] + 2.0, a["v"] + 10.0, 16.0)),
            Vector((a["u"] + 7.0, a["v"] + 40.0, 17.0)), Vector((tu, tv, 17.5))]
    H.tube(bm, path, 2.4, 12 if not lite else 4)
    H.cyl(bm, 2.6, (tu, tv, 17.5), (tu + (tu - a["u"]) * 0.02, tv + 2.0, 17.5), 12, dome=1.0)
    fin("arm", bm, ["gold"], "hardware", bev=0.3)
    return o


def build_controls():
    m = M6
    lite = m._st["lite"]
    kn = G["knob"]
    r, h = kn["d"] / 2, kn["h"]
    bm = bmesh.new()
    prof = [(0, 0), (r, 0), (r, 4.0)]
    n = 8 if not lite else 3
    for k in range(1, n + 1):
        a = math.pi / 2 * k / n
        prof.append((r * math.cos(a), 4.0 + (h - 4.0) * math.sin(a)))
    for u, v in G["knobs"]:
        H.lathe(bm, prof, (u, v, -0.3), (0, 0, 1), 40 if not lite else 10)
    o = fin("knobs", bm, ["gold"], "pickguard", bev=0.3)
    # the five-way switch: a slot, the lever, a white tip, two screws
    sw = G["switch"]
    ca, sa = math.cos(math.radians(sw["angle_deg"])), math.sin(math.radians(sw["angle_deg"]))
    dark, met, tip = bmesh.new(), bmesh.new(), bmesh.new()
    H.rbox(dark, sw["slot_l"], 3.2, -0.2, 0.05, (sw["u"], sw["v"]), sw["angle_deg"], r=1.4, n=3 if not lite else 1)
    for s_ in (-1, 1):
        p = (sw["u"] + s_ * 17.0 * ca, sw["v"] + s_ * 17.0 * sa)
        H.cyl(met, 1.6, (p[0], p[1], -0.2), (p[0], p[1], 0.7), 12, dome=0.6)
    H.rbox(met, 2.2, 2.0, -0.5, 9.0, (sw["u"], sw["v"]), sw["angle_deg"], r=0.4, n=1)
    H.lathe(tip, [(0, 0), (3.2, 0), (3.6, 3.0), (3.4, 7.0), (2.0, 9.0), (0, 9.5)], (sw["u"], sw["v"], 6.5), (0, 0, 1), 16)
    # the jack: a recessed plate on the treble rim
    ju, nrm = m._rim_point(G["jack_v"])
    c = Vector((ju, G["jack_v"], -T / 2))
    nn = Vector((nrm.x, nrm.y, 0))
    H.lathe(met, [(0, -0.2), (10.0, -0.2), (10.0, 0.8), (9.0, 1.2), (6.0, 1.2), (5.5, 3.2), (4.6, 3.2), (0, 1.0)], c, nn,
            32 if not lite else 8)
    H.cyl(dark, 3.2, c + nn * 2.9, c + nn * 3.4, 14)
    sb = [(0, -2.5), (5.0, -2.5), (5.3, 0.3), (5.0, 1.2), (2.8, 2.2), (2.5, 5.5), (3.3, 7.0), (5.3, 8.0),
          (5.4, 9.0), (4.4, 10.4), (2.4, 11.0), (0, 11.1)]
    for u, v, ang in G["strap_buttons"]:
        p = min(BODY, key=lambda q: (q[0] - u) ** 2 + (q[1] - v) ** 2)
        d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0.0)
        H.lathe(met, sb, (p[0], p[1], -T / 2), d, 18 if not lite else 6)
    fin("switch_slot", dark, ["dark"], "pickguard")
    fin("controls_metal", met, ["gold"], "pickguard", bev=0.3)
    fin("switch_tip", tip, ["cream"], "pickguard")
    return o


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
    root = bpy.data.objects.new("guitar_06_lite_root" if lite else "guitar_06", None)
    if not lite:
        root.empty_display_type = "SPHERE"
        root.empty_display_size = 0.02
    coll.objects.link(root)
    names.set_name(root, root.name, data=False)
    root.parent = parent
    M6._st.update(coll=coll, root=root, lite=lite, Q=M6.LITE if lite else M6.RICH, groups=groups,
                  prefix=f"guitar_06_{'lite' if lite else 'part'}_")
    if "bobbin" not in MATS or MATS["lacquer"].name not in bpy.data.materials:
        materials()
    if not lite:
        yield "materials"
    build_body()
    yield "body"
    M6.build_board()
    build_frets_nut_side_dots()
    M6.build_neck_shaft()
    G3.build_headstock(M6)
    build_head_extras()
    yield "neck"
    build_tuners()
    build_bridge()
    yield "hardware"
    build_pickups()
    build_controls()
    yield "pickguard"
    for o in list(root.children):            # no heel button, no truss-rod cover (a slot instead)
        if o.name.endswith(("heel_button", "truss_cover", "truss_edge", "truss_screws")):
            for lst in groups.values():
                if o in lst:
                    lst.remove(o)
            me = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
    for o in root.children:                  # the neck and the head's back and sides are roasted maple
        if o.name.endswith("_neck"):
            o.data.materials[0] = MATS["maple"]
        if o.name.endswith("_headstock"):
            o.data.materials[0] = MATS["maple"]
    M6.build_strings()
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


def export_rich(root):
    return M6.export_rich(root)


def export_lite(root, size=1024, orm_size=512):
    M6.build = build
    return M6.export_lite(root, size, orm_size, key="guitar_06")


def check(root):
    probs = []
    for o in [root] + names.descendants(root):
        if not names.NAME_RE.match(o.name):
            probs.append(f"bad name {o.name}")
    s = bpy.data.objects.get("guitar_06_strings")
    if s is None or s.parent is not root:
        probs.append("guitar_06_strings missing")
    if probs:
        raise AssertionError("guitar_06: " + "; ".join(probs))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in names.descendants(root) if o.type == "MESH")
    return {"parts": len(names.descendants(root)), "triangles_before_bevels": tris,
            "pivot_spec_mm": [round(x, 1) for x in PIV], "rack_lean_deg": LEAN, "scale_line_v": round(M6.VS, 1),
            "string_z_at_saddle": round(M6.ZS, 1)}
