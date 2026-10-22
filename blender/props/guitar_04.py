"""guitar_04: Stevie Ray Vaughan's "Number One", an exact replica in shape, hardware and finish
(decisions 2026-10-23), standing in the floor rack beside the desk (rack slot 1). No logos,
decals, initials, sticker, serials or stamps; plain 0 to 10 on the knobs.

Built on guitar_02's Strat: this module runs props/guitar_02.py's builders under guitar_04's
names and spec (lib/variant.py: "guitar_02" -> "guitar_04" throughout, so GUITAR_04, the
guitar_04 blueprint geometry, `guitar_04_part_*`, `mat_guitar_04_*`, `guitar_04_atlas`), then
replaces only what differs on Number One. guitar_02.py is not changed, so guitar_02's model
and export stay byte for byte as they were.

What is replaced here:
    materials()        the worn three-tone sunburst (wear fields from lib/guitar_wear.py, the
                       same maps the blueprint draws), rosewood board, clay dots, aged maple
                       worn on the back, the amber headstock worn at its edge, a 1-ply black
                       guard, aged cream plastics, gold plating, pearl tuner buttons
    finish()           wraps guitar_02's: per part, chrome or nickel becomes gold (bridge,
                       saddles, tuners, tree, screws, strap buttons, neck plate)
    build_jack()       the large oval gold plate with its deep cup (rich: the cup is cut into
                       the body); guitar_02's dished football is not used
    build_tuners()     the same tuners, the buttons split off in pearl plastic
    arm_uv(), _arm_path()   the left-handed tremolo: the arm on the bass side, across the bout
    PIV, SPEC          the pivot of `guitar_04` is the rack contact (MESHES.md, obj_guitars):
                       the body's lowest point at the rack's lean, on the body's centre plane

Names (MESHES.md, obj_guitars):
    guitar_04           empty at the rack contact, the whole guitar
    guitar_04_strings   one mesh, one material, origin at the strings' midpoint
    guitar_04_part_*    every other part in the .blend; the exports join them into `guitar_04_body`

    build_steps(parent=None, collection=None, lite=False), build(...), BUILD_ORDER, check(root)
    place_in_rack(root, slot=0)   on the rack's cradle, leaning onto the top bar
    export_rich(root), export_lite(root)   as guitar_02's
"""
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

from lib import constants as C, guitar_wear as GW, materials as M, variant

S = variant.load(os.path.join(C.BLENDER_DIR, "props", "guitar_02.py"),
                 [("guitar_02", "guitar_04"), ("GUITAR_02", "GUITAR_04")], "_guitar_04_strat")
G, BP, MM = S.G, S.BP, C.MM
VN, VS = S.VN, S.VS

# ---------------------------------------------------------------------------
# frame: the pivot at the rack contact
# ---------------------------------------------------------------------------
LEAN = C.LAYOUT["rack"]["lean"]
_pu, _pv = BP.rack_pivot(LEAN)
S.PIV = PIV = (_pu, _pv, -G["body_t"] / 2)
S.SPEC = SPEC = Matrix(((MM, 0, 0, -PIV[0] * MM),
                        (0, 0, -MM, PIV[2] * MM),
                        (0, MM, 0, -PIV[1] * MM),
                        (0, 0, 0, 1)))
S.WEAR_SPOTS = []                    # the wear is in the material (traced map + noise), not on vertices

# part key -> {material key: replacement} (his gold hardware)
REMAP = {
    "bridge": {"chrome": "gold"}, "saddles": {"nickel": "gold"}, "tuners": {"nickel": "gold"},
    "string_tree": {"nickel": "gold"}, "strap_buttons": {"chrome": "gold"}, "back_metal": {"chrome": "gold"},
    "guard_screws": {"chrome": "gold"},
}
_finish = S.finish


def finish(key, bm, mats, group, **kw):
    mats = [REMAP.get(key, {}).get(m, m) for m in mats]
    return _finish(key, bm, mats, group, **kw)


S.finish = finish


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
_materials_02 = S.materials
WEAR_IMAGES = ("guitar_04_wear_a", "guitar_04_wear_b")


def wear_images():
    """The wear fields of lib/guitar_wear.py as two packed float images (1 mm a pixel)."""
    have = [bpy.data.images.get(n) for n in WEAR_IMAGES]
    if all(im is not None and im.size[0] == GW.W for im in have):
        return have
    A, B = GW.pack(GW.fields(G, BP.HEAD))
    out = []
    import numpy as np
    for name, arr in zip(WEAR_IMAGES, (A, B)):
        im = bpy.data.images.get(name)
        if im is not None:
            bpy.data.images.remove(im)
        im = bpy.data.images.new(name, GW.W, GW.H, alpha=False, float_buffer=True)
        im.colorspace_settings.name = "Non-Color"
        px = np.ones((GW.H, GW.W, 4), np.float32)
        px[..., :3] = arr
        im.pixels.foreach_set(px.ravel())
        im.pack()
        out.append(im)
    return out


def _sep(nt, vec):
    s = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(vec, s.inputs[0])
    return s.outputs


def _ma(nt, a, mul, add):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = "MULTIPLY_ADD"
    nt.links.new(a, m.inputs[0])
    m.inputs[1].default_value = mul
    m.inputs[2].default_value = add
    return m.outputs[0]


def _op(nt, op, a, b):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for i, x in enumerate((a, b)):
        if isinstance(x, (int, float)):
            m.inputs[i].default_value = x
        else:
            nt.links.new(x, m.inputs[i])
    return m.outputs[0]


def _mr(nt, val, a, b, lo=0.0, hi=1.0, smooth=False):
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.clamp = True
    if smooth:
        mr.interpolation_type = "SMOOTHSTEP"
    nt.links.new(val, mr.inputs["Value"])
    mr.inputs["From Min"].default_value = a
    mr.inputs["From Max"].default_value = b
    mr.inputs["To Min"].default_value = lo
    mr.inputs["To Max"].default_value = hi
    return mr.outputs["Result"]


def _spec_coords(nt):
    """u, v, z in the spec's mm, from the object coordinates (every part is in the guitar frame)."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    x, y, z = _sep(nt, tc.outputs["Object"])
    return _ma(nt, x, 1000.0, PIV[0]), _ma(nt, z, 1000.0, PIV[1]), _ma(nt, y, -1000.0, PIV[2]), tc.outputs["Object"]


def _wear_tex(nt, u, v, image):
    cx = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(_ma(nt, u, 1.0 / (GW.W * GW.STEP), -GW.U0 / (GW.W * GW.STEP)), cx.inputs[0])
    nt.links.new(_ma(nt, v, 1.0 / (GW.H * GW.STEP), -GW.V0 / (GW.H * GW.STEP)), cx.inputs[1])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = image
    t.interpolation = "Cubic"
    t.extension = "EXTEND"
    nt.links.new(cx.outputs[0], t.inputs["Vector"])
    s = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(t.outputs["Color"], s.inputs[0])
    return s.outputs


def _grain_v(nt, co, c0, c1, scale=260.0, stretch=0.06):
    """Wood grain running along the guitar (object Z)."""
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, stretch)
    nt.links.new(co, mp.inputs["Vector"])
    g = M._noise(nt, mp.outputs[0], scale, detail=6, rough=0.6, distortion=0.8)
    return M._ramp(nt, g, [(0.3, c0), (0.72, c1)]), g


def _ramp_stops(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    for i, (pos, col) in enumerate(stops):
        e = el[i] if i < len(el) else el.new(pos)
        e.position = pos
        e.color = M.rgba(col)
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def _lacquer(imA, imB):
    """The body: three-tone sunburst where the traced map keeps it, bare alder elsewhere (grimy,
    pale where rubbed clean, stained at each patch's rim), the edge rubbed through all round,
    chips and scratches from noise. Front or back by the depth in the body."""
    T = G["body_t"]
    m, nt, b = M._new("mat_guitar_04_lacquer")
    u, v, z, co = _spec_coords(nt)
    A = _wear_tex(nt, u, v, imA)
    Bm = _wear_tex(nt, u, v, imB)
    lo, hi = GW.ENC["dist"]
    dist = _ma(nt, A[0], hi - lo, lo)                                  # mm in from the edge
    front = _mr(nt, z, -T * 0.62, -T * 0.38, smooth=True)              # 1 on the top, 0 on the back
    keep_b = _op(nt, "SUBTRACT", 1.0, Bm[0])
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "FLOAT"
    mx.clamp_factor = True
    nt.links.new(front, mx.inputs["Factor"])
    nt.links.new(keep_b, mx.inputs[2])
    nt.links.new(A[1], mx.inputs[3])
    keep = mx.outputs[0]
    n1 = M._noise(nt, co, 70.0, detail=8, rough=0.62)                  # patch edges, ~1 cm features
    n2 = M._noise(nt, co, 520.0, detail=4, rough=0.5)                  # chips, ~2 mm
    n3m = nt.nodes.new("ShaderNodeMapping")                            # scratches: stretched noise
    n3m.inputs["Scale"].default_value = (2.5, 2.5, 0.35)
    n3m.inputs["Rotation"].default_value = (0.0, math.radians(28), 0.0)
    nt.links.new(co, n3m.inputs["Vector"])
    n3 = M._noise(nt, n3m.outputs[0], 240.0, detail=3, rough=0.5)
    ew = G["edge_wear_mm"]
    edge = _mr(nt, _op(nt, "ADD", dist, _ma(nt, n1, 9.0, -4.5)), ew * 0.35, ew * 1.1)
    k = _op(nt, "MULTIPLY", keep, edge)
    k = _op(nt, "MULTIPLY", k, _mr(nt, n2, 0.665, 0.70, 1.0, 0.0))
    k = _op(nt, "MULTIPLY", k, _mr(nt, n3, 0.665, 0.685, 1.0, 0.1))
    kk = _op(nt, "ADD", k, _ma(nt, n1, 0.5, -0.25))
    kk = _op(nt, "ADD", kk, _ma(nt, n2, 0.45, -0.225))                # ragged, chipped patch edges
    surv = _mr(nt, kk, 0.44, 0.56)                                     # 1: finish left
    rim = _op(nt, "SUBTRACT", _mr(nt, kk, 0.30, 0.44), surv)           # the stained rim round a patch
    rim = _op(nt, "MAXIMUM", rim, 0.0)
    # colours
    st = G["sunburst"]
    dmax = st[-1][0]
    burst = _ramp_stops(nt, _op(nt, "DIVIDE", _op(nt, "MAXIMUM", dist, 0.0), dmax),
                        [(d / dmax, c) for d, c in st])
    checking = M._noise(nt, co, 900.0, detail=2)
    burst = S._mix(nt, _mr(nt, checking, 0.62, 0.7, 0.0, 0.35), burst, "#2a1a10")
    wd = G["wood"]
    wood, grain = _grain_v(nt, co, wd["grime_dark"], wd["grime"], scale=200.0, stretch=0.14)
    dirt = M._noise(nt, co, 25.0, detail=5, rough=0.6)                 # sweat and grime, in patches
    wood = S._mix(nt, _mr(nt, dirt, 0.45, 0.7, 0.0, 0.6), wood, "#4a2e18")
    pale = _op(nt, "MULTIPLY", A[2], front)
    pale_c, _ = _grain_v(nt, co, "#c49a64", wd["pale"])
    wood = S._mix(nt, pale, wood, pale_c)
    wood = S._mix(nt, _mr(nt, dist, 6.0, 0.0, 0.0, 0.55), wood, "#3e2817")    # grime darkest at the edge
    wood = S._mix(nt, _op(nt, "MULTIPLY", rim, 0.8), wood, wd["stain"])
    base = S._mix(nt, surv, wood, burst)
    nt.links.new(base, b.inputs["Base Color"])
    rough = S._mix(nt, surv, 0.8, _ma(nt, checking, 0.25, 0.24), "FLOAT")
    nt.links.new(rough, b.inputs["Roughness"])
    nt.links.new(S._mix(nt, surv, 0.3, 0.5, "FLOAT"), b.inputs["Specular IOR Level"])
    nt.links.new(S._mix(nt, surv, 0.0, 0.55, "FLOAT"), b.inputs["Coat Weight"])
    M._set(b, coat_rough=0.14, coat_ior=1.5)
    b.inputs["Coat Tint"].default_value = M.rgba("#f3e3c0")
    h = _op(nt, "ADD", _op(nt, "MULTIPLY", surv, 0.6), _op(nt, "MULTIPLY", grain, 0.1))
    M._bump(nt, b, h, 0.35, 0.0004)
    m.diffuse_color = M.rgba("#8a5a30")
    return m


def materials():
    """guitar_02's set under guitar_04's names, then Number One's own looks over it."""
    MATS = _materials_02()
    imA, imB = wear_images()
    MATS["lacquer"] = _lacquer(imA, imB)

    # rosewood board, worn dry and paler between frets 1 and 7 (guitar_02's `wear` on the board)
    m, nt, b = M._new("mat_guitar_04_board")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    col, g = _grain_v(nt, tc.outputs["Object"], "#2a190f", "#4a2c1b", scale=320.0, stretch=0.05)
    wm = S._wear_mask(nt, 160.0, 0.45, 0.7)
    nt.links.new(S._mix(nt, wm, col, "#5c3b27"), b.inputs["Base Color"])
    nt.links.new(S._mix(nt, wm, 0.42, 0.62, "FLOAT"), b.inputs["Roughness"])
    M._set(b, spec=0.45)
    M._bump(nt, b, g, 0.08, 0.0002)
    m.diffuse_color = M.rgba("#3a2419")
    MATS["board"] = m

    # neck back: maple, aged amber lacquer, rubbed to bare grey maple where the hand runs
    m, nt, b = M._new("mat_guitar_04_neck")
    u, v, z, co = _spec_coords(nt)
    col, g = _grain_v(nt, co, "#c38e47", "#d3a35b", scale=300.0, stretch=0.05)
    lo, hi = G["neck_wear"]
    x = _op(nt, "SUBTRACT", VN, v)                                     # mm from the nut
    band = _op(nt, "MULTIPLY", _mr(nt, x, lo - 15, lo + 15, smooth=True), _mr(nt, x, hi + 20, hi - 20, smooth=True))
    backside = _mr(nt, z, S.ZC - 6.0, S.ZC - 9.0)
    nz = M._noise(nt, co, 60.0, detail=6)
    wear = _mr(nt, _op(nt, "ADD", _op(nt, "MULTIPLY", band, backside), _ma(nt, nz, 0.5, -0.25)), 0.4, 0.6)
    bare, _ = _grain_v(nt, co, "#94703f", "#ab8656", scale=300.0, stretch=0.05)
    nt.links.new(S._mix(nt, wear, col, bare), b.inputs["Base Color"])
    nt.links.new(S._mix(nt, wear, 0.3, 0.5, "FLOAT"), b.inputs["Roughness"])
    nt.links.new(S._mix(nt, wear, 0.35, 0.0, "FLOAT"), b.inputs["Coat Weight"])
    M._set(b, coat_rough=0.2, spec=0.5)
    M._bump(nt, b, g, 0.03, 0.0002)
    m.diffuse_color = M.rgba("#c9974f")
    MATS["neck"] = m

    # headstock: aged amber lacquer, the edge worn to dark wood (no decal, no text)
    m, nt, b = M._new("mat_guitar_04_head")
    u, v, z, co = _spec_coords(nt)
    col, g = _grain_v(nt, co, "#c99549", "#d8a95e", scale=300.0, stretch=0.05)
    Bm = _wear_tex(nt, u, v, imB)
    hlo, hhi = GW.ENC["head"]
    hd = _ma(nt, Bm[1], hhi - hlo, hlo)
    nz = M._noise(nt, co, 40.0, detail=8, rough=0.65)                 # patches along the edge, ~2.5 cm
    hw = G["head_edge_wear_mm"]
    worn = _mr(nt, _op(nt, "ADD", hd, _ma(nt, nz, 16.0, -8.0)), hw, hw * 0.3)
    nt.links.new(S._mix(nt, worn, col, "#7a4e22"), b.inputs["Base Color"])
    nt.links.new(S._mix(nt, worn, 0.3, 0.6, "FLOAT"), b.inputs["Roughness"])
    nt.links.new(S._mix(nt, worn, 0.6, 0.0, "FLOAT"), b.inputs["Coat Weight"])
    M._set(b, coat_rough=0.1, spec=0.5)
    b.inputs["Coat Tint"].default_value = M.rgba("#f3dcae")
    M._bump(nt, b, _op(nt, "ADD", g, _op(nt, "MULTIPLY", worn, -0.5)), 0.05, 0.0003)
    m.diffuse_color = M.rgba("#d2a35a")
    MATS["head"] = m

    # gold plating, worn towards brass where hands and picks rub
    for key, name, c0, c1, r0, r1 in (("gold", "mat_guitar_04_gold", "#e2bd6e", "#b79552", 0.2, 0.32),
                                      ("gold_dark", "mat_guitar_04_gold_dark", "#b9975a", "#8a7444", 0.3, 0.42)):
        m, nt, b = M._new(name)
        tn = M._noise(nt, M._coords(nt), 380, detail=4)
        nt.links.new(M._ramp(nt, tn, [(0.45, c0), (0.8, c1)]), b.inputs["Base Color"])
        M._set(b, metal=1.0)
        S._rough_noise(nt, b, r0, r1)
        m.diffuse_color = M.rgba(c0)
        MATS[key] = m

    def plain(key, name, colour, rough, **v):
        MATS[key] = M.principled(name, base=colour, rough=rough, **v)

    plain("guard", "mat_guitar_04_guard", "#121110", 0.34, coat=0.25, coat_rough=0.2, spec=0.5)
    plain("ply", "mat_guitar_04_ply", "#1e1d1b", 0.5, spec=0.5)                 # the 1-ply bevel, duller
    plain("plastic", "mat_guitar_04_plastic", "#d8c084", 0.45, spec=0.5)       # aged cream
    plain("dots", "mat_guitar_04_dots", "#d4a46c", 0.55, spec=0.4)             # clay
    plain("pearl", "mat_guitar_04_pearl", "#e4d9c2", 0.3, coat=0.6, coat_rough=0.1, sss=0.08,
          sss_scale=0.002)
    S.MATS.update(MATS)
    return S.MATS


S.materials = materials


# ---------------------------------------------------------------------------
# jack: the long oval plate and its deep cup at the lower end (measured)
# ---------------------------------------------------------------------------
def oval(l, w, n, e=2.6):
    """A superellipse l along x, w along y: the plate's long rounded oval."""
    out = []
    for k in range(n):
        t = 2 * math.pi * k / n
        c, s_ = math.cos(t), math.sin(t)
        out.append((l / 2 * math.copysign(abs(c) ** (2 / e), c), w / 2 * math.copysign(abs(s_) ** (2 / e), s_)))
    return out


def _along(d):
    j = G["jack"]
    q = BP.rot((d, 0), j["angle_deg"])
    return (j["u"] + q[0], j["v"] + q[1])


def _jack_cut(body):
    """Rich only: the cup's opening cut into the top, so the cup shows as a hole."""
    j = G["jack"]
    bm = bmesh.new()
    S.prism_uv(bm, S.place2(oval(j["cup_l"] + 0.6, j["cup_w"] + 0.6, 32, 2.2), _along(j["cup_off"]), j["angle_deg"]),
               -j["cup_depth"] - 2.0, 3.0)
    bmesh.ops.transform(bm, matrix=SPEC, verts=bm.verts)
    me = bpy.data.meshes.new("guitar_04_tmp_cut_mesh")
    bm.to_mesh(me)
    bm.free()
    cut = bpy.data.objects.new("guitar_04_tmp_cut", me)
    S._st["coll"].objects.link(cut)
    cut.parent = S._st["root"]
    mod = body.modifiers.new("cup", "BOOLEAN")
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


S._jack_dish = _jack_cut


def build_jack():
    j = G["jack"]
    ang = j["angle_deg"]
    lite = S._st["lite"]
    n = 40 if not lite else 12
    t = 1.2
    cup_c = _along(j["cup_off"])
    outer = S.place2(oval(j["l"], j["w"], n), (j["u"], j["v"]), ang)
    inner = S.place2(oval(j["cup_l"], j["cup_w"], n, 2.2), cup_c, ang)
    bm = bmesh.new()
    if lite:
        S.prism_uv(bm, outer, 0.0, t)
    else:                                          # the plate: a ring round the cup's opening
        o0, o1 = S.ring(bm, S.ccw(outer), 0.0), S.ring(bm, S.ccw(outer), t)
        i0, i1 = S.ring(bm, S.ccw(inner), 0.0), S.ring(bm, S.ccw(inner), t)
        S.bridge(bm, o0, o1)
        S.bridge(bm, i1, i0)
        S.bridge(bm, o1, i1)
        S.bridge(bm, i0, o0)
    for d in j["screw_offs"]:
        p = _along(d)
        S.cyl(bm, S.SCREW["jack"] / 2, (p[0], p[1], t - 0.3), (p[0], p[1], t + 1.0), S.Q("small"), dome=0.8)
    o = finish("jack", bm, ["gold"], "body", bev=0.4, seg=2)
    # the cup: a deep oval bowl, deepest towards its upper end where the socket is
    bm = bmesh.new()
    d = j["cup_depth"] if not lite else 2.5
    steps = [(1.0, 0.0), (0.97, 0.2), (0.9, 0.45), (0.78, 0.7), (0.6, 0.9), (0.42, 1.0)]
    if lite:
        steps = [(1.0, 0.0), (0.8, 0.6), (0.45, 1.0)]
    rings = []
    for k, f in steps:
        c = _along(j["cup_off"] - j["cup_l"] * 0.18 * f)        # the bowl leans towards the socket
        rings.append(S.ring(bm, S.ccw(S.place2(oval(j["cup_l"] * k, j["cup_w"] * k, n, 2.2), c, ang)), t - 0.05 - d * f))
    for a_, b_ in zip(rings, rings[1:]):
        S.bridge(bm, b_, a_)
    S.cap(bm, rings[-1])
    bm.normal_update()
    if sum(f.normal.z for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    finish("jack_cup", bm, ["gold"], "body", recalc=False)
    c = _along(j["cup_off"] - j["cup_l"] * 0.18)
    zb = t - 0.05 - d
    bm = bmesh.new()
    S.cyl(bm, j["socket_d"] / 2, (c[0], c[1], zb - 0.1), (c[0], c[1], zb + 1.6), S.Q("small") + 4)
    finish("jack_socket", bm, ["gold_dark"], "body")
    bm = bmesh.new()
    S.cyl(bm, 3.2, (c[0], c[1], zb + 1.0), (c[0], c[1], zb + 1.7), S.Q("small"))
    finish("jack_hole", bm, ["dark"], "body")
    return o


S.build_jack = build_jack


# ---------------------------------------------------------------------------
# bridge: the left-handed vintage unit (measured): a plate that barely shows behind the saddles, six
# chunky bent-steel saddles with two height screws each, intonation screws and springs, all gold
# ---------------------------------------------------------------------------
BR = G["bridge"]
_BACK0 = sum(G["saddle_back"]) / len(G["saddle_back"])
SADDLE_FRONT = BR["saddle_front"] - (VS - _BACK0)          # saddle front, from its crown
SADDLE_REAR = (VS - _BACK0) - BR["saddle_rear"]            # saddle rear, behind its crown
HEIGHT_SCREW = BR["height_screw_v"] - (VS - _BACK0)        # height screws, from the crown
S.SADDLE_SHEET = BR["sheet"]


def plate_front():
    return VS + BR["front_off"]


def saddle_rear(back):
    lip = plate_front() - BR["l"] + 1.5
    return max(VS - back - SADDLE_REAR, lip + 3.0)


def _saddle_b(u, back):
    """Underside of the strip, (v, z): rear tab, base on the plate, the rise, the crown, the front leg."""
    z1 = BR["float_gap"] + 1.2
    crown, top, dz, t = VS - back, BR["saddle_top_z"], S.saddle_drop(u), BR["sheet"]
    vr, vf = saddle_rear(back), VS - back + SADDLE_FRONT
    ctrl = [(vr, z1 + 5.0), (vr, z1 + 0.6), (vr + 0.6, z1), (vr + 2.5, z1), (crown - 4.0, top - dz - t - 1.4),
            (crown - 1.0, top - dz - t - 0.05), (crown + 1.2, top - dz - t - 0.1), (crown + 4.5, top - dz - t - 0.9),
            (vf - 2.0, top - dz - t - 3.6), (vf - 0.5, z1 + 1.2), (vf, z1)]
    return S.spline(ctrl, closed=False, n=4 if not S._st["lite"] else 1)


S.saddle_rear = saddle_rear
S._saddle_b = _saddle_b


def build_bridge():
    br = BR
    front = plate_front()
    rear = front - br["l"]
    z0, z1 = br["float_gap"], br["float_gap"] + 1.2
    lite = S._st["lite"]
    Qs = S.Q("small")
    bm = bmesh.new()
    S.rbox(bm, br["w"], br["l"], z0, z1, (0, front - br["l"] / 2), r=2.5, n=3 if not lite else 1)
    S.rbox(bm, br["w"] - 1.5, 1.5, z0, z0 + br["lip_h"], (0, rear + 0.75), r=0.6, n=2 if not lite else 1)
    for u in BP.strings_bridge() if not lite else ():
        vs = front - br["screw_off_front"]
        S.cyl(bm, br["screw_d"] / 2, (u, vs, z1 - 0.2), (u, vs, z1 + 1.3), Qs, dome=1.0)
    o = finish("bridge", bm, ["gold"], "hardware", bev=0.4, seg=2)
    # the arm socket: a dark round collar half over the plate's bass end
    au, av = arm_uv()
    bm = bmesh.new()
    sr = G["arm"]["socket_r"]
    S.lathe(bm, [(0, 0), (sr, 0), (sr, 1.8), (sr - 1.2, 2.6), (S.ARM_R + 0.4, 2.6), (S.ARM_R + 0.4, 1.0), (0, 1.0)],
            (au, av, z1 - 0.1), (0, 0, 1), Qs + 6)
    finish("arm_socket", bm, ["dark"], "hardware", bev=0.3, seg=2)
    # saddles
    bm = bmesh.new()
    sw = br["saddle_w"] - 0.6
    for u, back in zip(BP.strings_bridge(), G["saddle_back"]):
        sec = S.saddle_section(u, back)
        if lite:
            crown, dz, top = VS - back, S.saddle_drop(u), br["saddle_top_z"]
            vr, vf = saddle_rear(back), VS - back + SADDLE_FRONT
            sec = [(vr, z1), (vr, z1 + 4.5), (crown, top - dz), (crown + 4.5, top - dz - 0.8), (vf, z1)]
        S.prism_vz(bm, sec, u - sw / 2, u + sw / 2)
    finish("saddles", bm, ["gold"], "hardware", bev=0.35, seg=2, angle=30)
    if lite:
        build_arm()
        return o
    bm = bmesh.new()
    for u, back in zip(BP.strings_bridge(), G["saddle_back"]):
        vh = VS - back + HEIGHT_SCREW
        for sg in (-1, 1):                            # height screws, up through the strip, their heads just proud
            top = S.saddle_top_at(u, back, vh)
            S.cyl(bm, 1.3, (u + sg * 2.9, vh, z1), (u + sg * 2.9, vh, top + 0.6), 12)
        vr = saddle_rear(back)
        S.cyl(bm, 1.4, (u, vr + 1.0, z1 + 3.0), (u, rear - 2.4, z1 + 3.0), 12)
        S.lathe(bm, [(0, 0), (2.6, 0), (2.6, 1.4), (1.6, 2.2), (0, 2.2)], (u, rear - 0.6, z1 + 3.0), (0, -1, 0), 14)
    finish("saddle_screws", bm, ["gold_dark"], "hardware")
    bm = bmesh.new()                                  # intonation springs, lip to saddle
    for u, back in zip(BP.strings_bridge(), G["saddle_back"]):
        v0, v1 = rear + 1.5, saddle_rear(back)
        turns = max(2.0, (v1 - v0) / 0.9)
        path = []
        for k in range(int(turns * 12) + 1):
            tt = k / 12
            a = 2 * math.pi * tt
            path.append(Vector((u + 2.1 * math.cos(a), v0 + (v1 - v0) * tt / turns, z1 + 3.0 + 2.1 * math.sin(a))))
        S.tube(bm, path, 0.32, 6)
    finish("saddle_springs", bm, ["gold_dark"], "hardware")
    build_arm()
    return o


def build_arm():
    S.build_arm()


S.build_bridge = build_bridge


# ---------------------------------------------------------------------------
# tuners: pearl plastic buttons in their own mesh
# ---------------------------------------------------------------------------
_key02, _tuners02 = S._key, S.build_tuners
_keys = {"bm": None}


def _key(bm, ka, pv, k, seg):
    _key02(_keys["bm"], ka, pv, k, seg)


def build_tuners():
    _keys["bm"] = bmesh.new()
    o = _tuners02()
    finish("tuner_keys", _keys["bm"], ["pearl"], "hardware", bev=0.3, seg=2, angle=40)
    _keys["bm"] = None
    return o


S._key = _key
S.build_tuners = build_tuners


# ---------------------------------------------------------------------------
# the arm: left-handed tremolo, the socket at the bass end of the plate
# ---------------------------------------------------------------------------
def arm_uv():
    a = G["arm"]
    sw = G["bridge"]["saddle_w"] - 0.6
    return min(a["u"], BP.strings_bridge()[0] - sw / 2 - S.ARM_R - 0.05), a["v"]


def _arm_path(n):
    """As guitar_02's (the blueprint's side profile), along the arm's own direction."""
    a = G["arm"]
    au, av = arm_uv()
    ang = math.radians(a["angle_deg"])
    z1 = G["bridge"]["float_gap"] + 1.2
    side = [(z1, 0.0), (12.0, 2.0), (19.0, 9.0), (22.0, 22.0), (22.5, 60.0)]   # (z, mm along the arm)
    sm = S.spline([(0.0, -3.0)] + [(s, z) for z, s in side], closed=False, n=n)
    d = (math.cos(ang), math.sin(ang))
    return [Vector((au + s * d[0], av + s * d[1], z)) for s, z in sm], d


S.arm_uv = arm_uv
S._arm_path = _arm_path


# ---------------------------------------------------------------------------
# the rack
# ---------------------------------------------------------------------------
def rack_transform(slot=0):
    """matrix_world for `guitar_04` in rack slot `slot` (0 = slot 1): the body's lowest point on the
    cradle, leaning LEAN degrees in its own plane, the neck's treble edge on the top bar's corner.
    Returns (matrix, info)."""
    import sys
    sys.path.insert(0, os.path.join(C.BLENDER_DIR, "design"))
    import room_plan_sheet as PLAN
    rk, _, slots = PLAN.rack_slots()
    th = math.radians(rk["lean"])
    bar_x = -0.08 + 0.70 * math.sin(th)                 # the top bar's corner, as props/footprints.py builds it
    bar_z = rk["cradle"] + 0.70 * math.cos(th)

    def rel(u, v):                                      # guitar (u, v) mm -> rack (x, z) m from the pivot
        du, dv = (u - PIV[0]) * MM, (v - PIV[1]) * MM
        return du * math.cos(th) + dv * math.sin(th), -du * math.sin(th) + dv * math.cos(th)
    best = None
    for k in range(4000, 9600):
        v = k * 0.1
        x, z = rel(BP.neck_w(v) / 2, v)
        if best is None or abs(z - (bar_z - rk["cradle"])) < abs(best[1] - (bar_z - rk["cradle"])):
            best = (x, z, v)
    x_c = bar_x - best[0] - 0.0005                      # half a millimetre clear of the bar
    m = (Matrix.Translation((rk["x"], rk["y"], 0)) @ Matrix.Rotation(math.radians(rk["yaw"]), 4, "Z")
         @ Matrix.Translation((x_c, slots[slot], rk["cradle"])) @ Matrix.Rotation(th, 4, "Y"))
    fret = min(range(len(BP.FRETS)), key=lambda i: abs(VN - BP.FRETS[i] - best[2])) + 1
    return m, {"bar_contact_v": round(best[2], 1), "nut_to_contact": round(VN - best[2], 1),
               "nearest_fret": fret, "pivot_uv": (round(PIV[0], 1), round(PIV[1], 1)), "x_in_rack": round(x_c, 4)}


def place_in_rack(root, slot=0):
    m, info = rack_transform(slot)
    parent = root.parent
    root.matrix_world = m if parent is None else m
    if parent is not None:
        root.matrix_parent_inverse = Matrix.Identity(4)
        root.matrix_basis = parent.matrix_world.inverted() @ m
    bpy.context.view_layer.update()
    return info


# re-export guitar_02's driver and exports, now running with everything above
BUILD_ORDER, MATS = S.BUILD_ORDER, S.MATS
build_steps, build, check = S.build_steps, S.build, S.check
export_rich, export_lite, parts, Q = S.export_rich, S.export_lite, S.parts, S.Q
GROUPS = S.GROUPS
