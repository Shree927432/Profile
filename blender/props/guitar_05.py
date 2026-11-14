"""guitar_05: James Hetfield's "Eet Fuk" Explorer (an ESP copy of the Explorer), in the floor rack, slot 2.
Exact in shape, hardware and finish (decisions 2026-10-23; built from photos and specs, the owner's choice
of 2026-11-13). No logos, no "ESP", no lettering on the tape.

Built from blender/lib/guitar_specs.py GUITAR_05 on Lucille's builder (props/guitar_01.py through
lib/variant.py, "guitar_01" -> "guitar_05"); props/guitar_03.py lends its unbound headstock and stop bar.
Replaced here: the body (flat, edges rounded over, off-white aged), the materials (black hardware, ebony,
black pickups without poles), the dot markers, the six-in-line tuners square to the post line, the
controls (black knobs, the toggle on the treble wing, the jack on the rim), the strap buttons, the tape,
and the frame: `guitar_05`'s pivot is the rack contact (MESHES.md, obj_guitars): the body's lowest point
at the rack's lean, on the body's centre plane, as guitar_04's.

Names: `guitar_05` (empty), `guitar_05_strings` (one mesh, one material, origin at the strings'
midpoint), `guitar_05_part_*` (joined into `guitar_05_body` by the exports).
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from lib import constants as C, geo, materials as M, names, variant
from lib.guitar_specs import GUITAR_05 as G, spline
from props import guitar_02 as H
from props import guitar_03 as G3

MM = C.MM
SRC = os.path.join(C.BLENDER_DIR, "props", "guitar_01.py")
M5 = variant.load(SRC, [("GUITAR_01", "GUITAR_05"), ("guitar_01", "guitar_05")], "_guitar_05")
T = G["body_t"]
BODY = M5.BODY
LEAN = C.LAYOUT["rack"]["lean"]

# ---------------------------------------------------------------------------
# frame: the rack contact
# ---------------------------------------------------------------------------
_th = math.radians(LEAN)
_pu, _pv = min(BODY, key=lambda p: -p[0] * math.sin(_th) + p[1] * math.cos(_th))
PIV = (_pu, _pv, -T / 2)
SPEC = Matrix(((MM, 0, 0, -PIV[0] * MM),
               (0, 0, -MM, PIV[2] * MM),
               (0, MM, 0, -PIV[1] * MM),
               (0, 0, 0, 1)))
M5.PIV, M5.SPEC = PIV, SPEC
M5.top_z = lambda u, v: 0.0
M5._post_for = lambda i: sorted(G["tuner_posts"], key=lambda p: p[1])[i]     # six in line: low E nearest the nut
M5.G = dict(M5.G)


def S(u, v, z):
    return SPEC @ Vector((u, v, z))


# ---------------------------------------------------------------------------
# materials: off-white aged, black hardware, ebony, black pickups
# ---------------------------------------------------------------------------
MATS = M5.MATS


def materials():
    M5.materials()
    m, nt, b = M._new("mat_guitar_05_offwhite")
    co = M._coords(nt)
    n1 = M._noise(nt, co, 4.0, detail=3)
    base = M._ramp(nt, n1, [(0.35, "#e8e1c9"), (0.7, "#ddd3b4")])
    dirt = M._noise(nt, co, 30.0, detail=6, rough=0.65)
    base = H._mix(nt, H._maprange(nt, dirt, 0.58, 0.75), base, "#b8a982")          # grime in patches
    nt.links.new(base, b.inputs["Base Color"])
    sc = nt.nodes.new("ShaderNodeMapping")
    sc.inputs["Scale"].default_value = (3.0, 0.4, 3.0)
    sc.inputs["Rotation"].default_value = (0.2, 0.8, 0.4)
    nt.links.new(co, sc.inputs["Vector"])
    scr = M._noise(nt, sc.outputs[0], 280, detail=3)
    M._set(b, rough=0.3, spec=0.5, coat=0.8, coat_ior=1.5)
    nt.links.new(H._mix(nt, H._maprange(nt, scr, 0.6, 0.67), 0.05, 0.3, "FLOAT"), b.inputs["Coat Roughness"])
    m.diffuse_color = M.rgba("#e3dbc2")
    MATS["lacquer"] = m
    MATS["headface"] = m
    for key, name, c0, c1, r0, r1 in (("gold", "mat_guitar_05_black_metal", "#1a1a1b", "#232324", 0.28, 0.38),
                                      ("gold_dark", "mat_guitar_05_black_metal_dark", "#111112", "#18181a", 0.35, 0.45)):
        m, nt, b = M._new(name)
        tn = M._noise(nt, M._coords(nt), 380, detail=4)
        nt.links.new(M._ramp(nt, tn, [(0.45, c0), (0.85, c1)]), b.inputs["Base Color"])
        M._set(b, metal=0.85)
        H._rough_noise(nt, b, r0, r1)
        m.diffuse_color = M.rgba(c0)
        MATS[key] = m
    MATS["white"] = MATS["ebony"]                     # the board is unbound
    MATS["pearl"] = M.principled("mat_guitar_05_dots", base="#ece7da", rough=0.3, coat=0.5, spec=0.5)
    MATS["pickup"] = M.principled("mat_guitar_05_pickup", base="#141414", rough=0.55, spec=0.4)
    MATS["tape"] = M.principled("mat_guitar_05_tape", base="#7b7d7c", rough=0.75, spec=0.3, sheen=0.3)
    return MATS


# ---------------------------------------------------------------------------
# body: flat, the edge rounded over front and back
# ---------------------------------------------------------------------------
def build_body():
    lite = M5._st["lite"]
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
    M5.strip_uv(bm, rings, segments=6)
    H.fill_cdt(bm, rings[0], 9.0 if not lite else 45.0, 0.0, True, 0)
    H.fill_cdt(bm, rings[-1], 9.0 if not lite else 45.0, -T, False, 0)
    return M5.finish("body", bm, ["lacquer"], "body")


def build_tape():
    """Plain grey cloth tape along the lower bass wing, its ends torn (no lettering)."""
    tp = G["tape"]
    # the wing's lower edge: the outline's run from its lowest point towards the tail strap button
    lo = min(BODY, key=lambda p: p[1])
    tail = min(BODY, key=lambda p: abs(p[0] - G["strap_buttons"][1][0]) + (p[1] > 150) * 1e3)
    ang = math.atan2(tail[1] - lo[1], tail[0] - lo[0])
    lite = M5._st["lite"]
    nl, nw = (24, 4) if not lite else (4, 1)
    rng = np.random.default_rng(5)
    cx, cy = tp["centre"]
    ca, sa = math.cos(ang), math.sin(ang)
    bm = bmesh.new()
    grid = []
    for i in range(nl + 1):
        row = []
        for j in range(nw + 1):
            x = -tp["l"] / 2 + tp["l"] * i / nl
            y = -tp["w"] / 2 + tp["w"] * j / nw
            if i in (0, nl) and not lite:
                x += (rng.random() - 0.5) * 3.0 * (1 if i else -1)
            row.append(bm.verts.new((cx + x * ca - y * sa, cy + x * sa + y * ca, 0.25)))
        grid.append(row)
    for i in range(nl):
        for j in range(nw):
            H.cap(bm, (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    return M5.finish("tape", bm, ["tape"], "body", smooth=False)


def build_controls():
    lite = M5._st["lite"]
    kn = G["knob"]
    r, h = kn["d"] / 2, kn["h"]
    bm = bmesh.new()
    prof = [(0, 0), (r, 0), (r, 4.0), (r - 1.0, 5.0), (r - 2.6, 6.0), (r - 3.0, h - 1.2), (r - 3.8, h), (0, h)]
    if lite:
        prof = [prof[0], prof[1], prof[2], prof[4], prof[6], prof[7]]

    def rm(t_, i):
        return 1.0 + (0.035 * math.cos(t_ * 30) if i in (1, 2) else 0.0)
    for u, v in G["knobs"]:
        H.lathe(bm, prof, (u, v, -0.3), (0, 0, 1), 48 if not lite else 12, rmod=rm if not lite else None)
    o = M5.finish("knobs", bm, ["plastic"], "pickguard", bev=0.4)
    met = bmesh.new()
    tip = bmesh.new()
    tu, tv = G["toggle"]
    H.lathe(met, [(0, 0), (9.5, 0), (9.5, 0.7), (7.0, 1.4), (0, 1.4)], (tu, tv, -0.2), (0, 0, 1), 32)
    H.lathe(met, [(0, 0), (5.5, 0), (5.5, 3.0), (4.6, 3.8), (0, 3.8)], (tu, tv, 1.0), (0, 0, 1), 6)
    lever = [Vector((tu, tv, 3.0)), Vector((tu, tv + 6.0, 21.0))]
    H.tube(met, lever, 1.5, 12 if not lite else 4)
    H.lathe(tip, [(0, -1), (2.6, 0), (3.8, 3.0), (3.8, 7.0), (2.8, 10.0), (0, 10.8)], lever[1] - Vector((0, 1.3, 4.0)),
            (lever[1] - lever[0]).normalized(), 14 if not lite else 6)
    # the jack on the treble rim, the strap buttons on the rim
    ju, n = M5._rim_point(G["jack_v"])
    c = Vector((ju, G["jack_v"], -T / 2))
    nn = Vector((n.x, n.y, 0))
    H.lathe(met, [(0, -0.2), (11.0, -0.2), (11.0, 0.8), (10.0, 1.4), (6.2, 1.4), (5.5, 4.0), (4.6, 4.0), (0, 1.0)], c,
            nn, 32 if not lite else 8)
    holes = bmesh.new()
    H.cyl(holes, 3.2, c + nn * 3.6, c + nn * 4.1, 14)
    sb = [(0, -2.5), (5.2, -2.5), (5.5, 0.3), (5.2, 1.2), (2.9, 2.2), (2.6, 5.5), (3.4, 7.0), (5.5, 8.0),
          (5.6, 9.0), (4.6, 10.4), (2.5, 11.0), (0, 11.1)]
    for u, v, ang in G["strap_buttons"]:
        p = min(BODY, key=lambda q: (q[0] - u) ** 2 + (q[1] - v) ** 2)
        d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0.0)
        H.lathe(met, sb, (p[0], p[1], -T / 2), d, 18 if not lite else 6)
    M5.finish("controls_metal", met, ["gold"], "pickguard", bev=0.3)
    M5.finish("toggle_tip", tip, ["plastic"], "pickguard")
    M5.finish("jack_hole", holes, ["dark"], "pickguard")
    return o


def build_dots_frets_nut():
    m = M5
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
    m.finish("frets", bm, ["frets"], "neck", frame=m.NECK_M)
    bm = bmesh.new()
    prev = 0.0
    rd = G["dot_d"] / 2
    for k, x in enumerate(m.FRETS, 1):
        if k in G["dots"]:
            vm = m.VN - (prev + x) / 2
            for u in ((-G["dot12_offset"], G["dot12_offset"]) if k == 12 else (0.0,)):
                nrm = Vector((u, 0, math.sqrt(m.R_BOARD ** 2 - u * u))).normalized()
                p = Vector((u, vm, m.board_top(u)))
                H.cyl(bm, rd, p - nrm * 0.3, p + nrm * 0.025, 24 if not m._st["lite"] else 7)
        prev = x
    m.finish("dots", bm, ["pearl"], "neck", frame=m.NECK_M)
    bm = bmesh.new()
    hw = G["nut_w"] / 2
    n = m.Q("arc")
    ntop = m.ZC + fh + 0.45
    top = [(-hw + 2 * hw * k / n, ntop - (-hw + 2 * hw * k / n) ** 2 / (2 * m.R_BOARD)) for k in range(n + 1)]
    H.prism_uz(bm, [(hw, m.HZ0 - 0.2)] + top[::-1] + [(-hw, m.HZ0 - 0.2)], m.VN, m.VN + m.NL)
    m.finish("nut", bm, ["nut"], "neck", frame=m.NECK_M, bev=0.5)


def _bass_edge_hit(p, d):
    """Where the ray from post p along d leaves the head outline (head frame, (a, VN + b))."""
    best = None
    P = Vector(p)
    D_ = Vector(d)
    for (a0, b0), (a1, b1) in zip(M5.HEAD, M5.HEAD[1:] + M5.HEAD[:1]):
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
    """Six in line along the bass edge: hex bushings and posts on the face, sealed housings on the back,
    the shafts square to the post line out past the edge, rounded black buttons. Plain, no stamp."""
    m = M5
    lite = m._st["lite"]
    HZ0, HT, VN = m.HZ0, m.HT, m.VN
    d = Vector(G["tuner_dir"]).normalized()
    ang = math.degrees(math.atan2(d.y, d.x))
    bm = bmesh.new()
    zb = HZ0 - HT
    zs = zb - 6.0
    for pa, pb in G["tuner_posts"]:
        pv = VN + pb
        if not lite:
            H.lathe(bm, [(0, 0), (5.2, 0), (5.2, 1.6), (4.2, 2.4), (0, 2.4)], (pa, pv, HZ0 - 0.1), (0, 0, 1), 6)
        H.cyl(bm, G["post_d"] / 2, (pa, pv, HZ0 - 0.2), (pa, pv, HZ0 + G["post_h"]), 16 if not lite else 6, dome=0.7)
        cx, cy = pa + d.x * 3.0, pv + d.y * 3.0
        H.rbox(bm, 17.0, 14.0, zb - 12.0, zb + 0.3, (cx, cy), ang, r=4.0, n=3 if not lite else 1)
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
        ca, sa = d.x, d.y
        for vtx in bm.verts[n0:]:
            x, y, z = vtx.co
            y *= 0.72
            vtx.co = Vector((kc.x + x * ca - y * sa, kc.y + x * sa + y * ca, zs + z))
    return m.finish("tuners", bm, ["gold"], "hardware", frame=m.HEAD_M, bev=0.5, angle=40)


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
    root = bpy.data.objects.new("guitar_05_lite_root" if lite else "guitar_05", None)
    if not lite:
        root.empty_display_type = "SPHERE"
        root.empty_display_size = 0.02
    coll.objects.link(root)
    names.set_name(root, root.name, data=False)
    root.parent = parent
    M5._st.update(coll=coll, root=root, lite=lite, Q=M5.LITE if lite else M5.RICH, groups=groups,
                  prefix=f"guitar_05_{'lite' if lite else 'part'}_")
    if "pickup" not in MATS or MATS["lacquer"].name not in bpy.data.materials:
        materials()
    if not lite:
        yield "materials"
    build_body()
    build_tape()
    yield "body"
    M5.build_board()
    build_dots_frets_nut()
    M5.build_neck_shaft()
    G3.build_headstock(M5)
    yield "neck"
    build_tuners()
    M5.build_bridge()
    G3.build_tailpiece(M5)
    yield "hardware"
    M5.build_pickups()
    build_controls()
    yield "pickguard"
    for o in list(root.children):                   # no heel button, no pole pieces (active pickups)
        if o.name.endswith(("heel_button", "_poles")):
            for lst in groups.values():
                if o in lst:
                    lst.remove(o)
            me = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
    for o in root.children:                         # the pickup covers in black plastic
        if o.name.endswith("_pickups"):
            o.data.materials[0] = MATS["pickup"]
    M5.build_strings()
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
    return M5.export_rich(root)


def export_lite(root, size=1024, orm_size=512):
    M5.build = build
    return M5.export_lite(root, size, orm_size, key="guitar_05")


def check(root):
    probs = []
    for o in [root] + names.descendants(root):
        if not names.NAME_RE.match(o.name):
            probs.append(f"bad name {o.name}")
    s = bpy.data.objects.get("guitar_05_strings")
    if s is None or s.parent is not root:
        probs.append("guitar_05_strings missing")
    if probs:
        raise AssertionError("guitar_05: " + "; ".join(probs))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in names.descendants(root) if o.type == "MESH")
    return {"parts": len(names.descendants(root)), "triangles_before_bevels": tris,
            "pivot_spec_mm": [round(x, 1) for x in PIV], "rack_lean_deg": LEAN, "scale_line_v": round(M5.VS, 1),
            "string_z_at_saddle": round(M5.ZS, 1)}
