"""Plants (2026-11-01): three downloaded models replace the room's plant stand-ins (owner: "Plants first").

    B="/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python"
    $B blender/components/plants.py            rich (plants.blend, plants-rich.glb), lite (plants-lite.glb), close-ups
    STAGE=rich,lite,closeups (default all three; each runs in a fresh scene)

Sources (blender/assets/plants/README.md; the originals stay there untouched, git-ignored):
  - the sill plant (obj_plant): "Monstera Deliciosa Potted Mid-Century Plant" by ChubbyPanda, CC BY 4.0,
    https://sketchfab.com/3d-models/1ab9bf841df04c07b1819be596327629
  - the snake plant: "Snake plant In Pot" by FranklySketch, CC BY 4.0,
    https://sketchfab.com/3d-models/68b8acaeb29e402ea4dc7c981cb5b497
  - the small desk plant: "Potted Plant 04" (a zebra haworthia) by Poly Haven, CC0, https://polyhaven.com/a/potted_plant_04

Rich (owner: "keep the heavy models for the Blender file. Don't cut down on that"): the downloaded geometry and
textures as they are, only normalised: scale, origin at the pot's bottom centre, our names, the monstera's
mid-century stand removed and its pot recoloured terracotta (plan v3: "young monstera, terracotta pot"), the snake
plant's unlit scan material turned into a lit one. -> out/components/plants.blend, plants-rich.glb.
Lite (the web, plants-lite.glb): decimated (LITE_TRIS), textures 256-1024 px, no roughness/occlusion maps; the
monstera's leaves and their petioles share one atlas material (one draw call per leaf), alpha-tested (MASK).

Frame: each plant's root empty at its pot's bottom centre, Z up, metres, its best side to -Y. Names
(scene/objects/MESHES.md):
  plant > plant_pot, plant_soil, plant_leaf_01..NN (leaf blade + its petiole, largest first, the youngest last;
          origin where the petiole meets the stem or the crown: grow = scale from 0 there, sway = a small rotation
          there), plant_static (the stem parts that carry no leaf)
  snake_plant > snake_plant_body;  desk_plant > desk_plant_pot, desk_plant_soil, desk_plant_pebbles, desk_plant_leaves
The room (build_v3.py, design/room_v3_component_test.py) places the roots at plan v3's numbers with place().
"""
import json
import math
import os
import subprocess
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, BL)
from lib import constants as C  # noqa: E402
from lib import names as NM  # noqa: E402
from lib.blendfile import pack_and_save  # noqa: E402

ASSETS = os.path.join(BL, "assets", "plants")
SRC = {"plant": os.path.join(ASSETS, "monstera", "monstera_deliciosa_potted_mid-century_plant.glb"),
       "snake_plant": os.path.join(ASSETS, "snake_plant", "snake_plant_in_pot.glb"),
       "desk_plant": os.path.join(ASSETS, "potted_plant_04", "potted_plant_04_8k.gltf")}
OUT = os.path.join(BL, "out", "components")
BLEND = os.path.join(OUT, "plants.blend")
RICH_GLB = os.path.join(OUT, "plants-rich.glb")
LITE_GLB = os.path.join(OUT, "plants-lite.glb")
FOOT = os.path.join(C.FOOTAGE, "2026-11-01-plants")
PY = "/opt/anaconda3/bin/python3"
CREDITS = {
    "plant": '"Monstera Deliciosa Potted Mid-Century Plant" by ChubbyPanda, CC BY 4.0',
    "snake_plant": '"Snake plant In Pot" by FranklySketch, CC BY 4.0',
    "desk_plant": '"Potted Plant 04" by Poly Haven, CC0',
}

# heights, pot bottom to the top of the plant (plan v3: monstera about 40, snake plant about 45, desk plant about 20)
HEIGHT = {"plant": 0.42, "snake_plant": 0.45, "desk_plant": 0.22}
LAYOUT = {"plant": (0.0, 0.0), "snake_plant": (0.45, 0.0), "desk_plant": (-0.35, 0.0)}   # side by side in the .blend
TERRACOTTA = (0.70, 0.40, 0.29)     # sRGB, a dusty terracotta (the stand-in was #b4553a)
# lite: triangle ratios per part (judged on the close-ups and the room stills)
LITE = {"leaf": 0.5, "pot": 0.5, "snake": 0.12, "desk_pot": 0.2, "desk_leaves": 0.5, "desk_pebbles": 0.5,
        "desk_soil": 0.12}
LITE_TEX = {"leaf_atlas": 1024, "pot": 512, "soil": 256, "snake": 512, "desk": 512}

T0 = time.time()
REPORT = {}


def log(m):
    print(f"MILESTONE {time.time() - T0:6.1f}s plants: {m}", flush=True)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def _import(path, coll):
    """Import a glTF; bake every mesh's world transform into its data; drop the empties."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy()
        if o.data.users > 1:
            o.data = o.data.copy()
        o.parent = None
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    return meshes


def _verts(o):
    v = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", v)
    return v.reshape(-1, 3)


def _tris(objs):
    return sum(len(p.vertices) - 2 for o in objs if o.type == "MESH" for p in o.data.polygons)


def _area(o):
    return sum(p.area for p in o.data.polygons)


def _select(objs, active=None):
    for x in bpy.context.scene.objects:
        x.select_set(False)
    for x in objs:
        x.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def _separate(o):
    """Loose parts of o as separate objects (o is one of them)."""
    _select([o])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    return list(bpy.context.selected_objects)


def _join(objs, name):
    objs = list(objs)
    if len(objs) > 1:
        with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs):
            bpy.ops.object.join()
    return NM.set_name(objs[0], name)


def _transform(objs, M):
    for o in objs:
        o.data.transform(M)
        o.data.update()


def _set_origin(o, p):
    p = Vector(p)
    o.data.transform(Matrix.Translation(-p))
    o.location = p


def _parent(o, root):
    o.parent = root
    o.matrix_parent_inverse = root.matrix_world.inverted()


def _empty(name, coll):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type, e.empty_display_size = "PLAIN_AXES", 0.1
    coll.objects.link(e)
    return NM.set_name(e, name, data=False)


def _decimate(o, ratio):
    if ratio >= 1.0:
        return
    m = o.modifiers.new("dec", "DECIMATE")
    m.ratio = ratio
    m.use_collapse_triangulate = True
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier=m.name)


def _bvh(o):
    return BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices], [p.vertices[:] for p in o.data.polygons])


def _pixels(im, w=None, h=None):
    """An image's pixels (h, w, 4) float32, resized first on a copy if w, h are given."""
    src = im
    if w and (w, h) != tuple(im.size):
        src = im.copy()
        src.scale(w, h)
    W, H = src.size
    px = np.empty(W * H * 4, np.float32)
    src.pixels.foreach_get(px)
    if src is not im:
        bpy.data.images.remove(src)
    return px.reshape(H, W, 4)


def _image(name, px, colorspace="sRGB", alpha=False):
    h, w = px.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=alpha)
    im.colorspace_settings.name = colorspace
    im.pixels.foreach_set(np.ascontiguousarray(px, np.float32).ravel())
    im.pack()
    return im


def _lowfreq(size, cells, seed):
    """Smooth noise (std 1) on a size x size grid: a random (cells+1)^2 lattice, bilinear."""
    g = np.random.default_rng(seed).standard_normal((cells + 1, cells + 1))
    x = np.linspace(0, cells, size)
    k = np.arange(cells + 1)
    rows = np.stack([np.interp(x, k, g[i]) for i in range(cells + 1)])           # (cells+1, size)
    out = np.stack([np.interp(x, k, rows[:, j]) for j in range(size)], 1)        # (size, size)
    return (out - out.mean()) / out.std()


def _image_node(m, kind):
    """The image feeding the Principled input `kind` (through any Separate/Normal Map/Math node), or None."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    stack = [l.from_node for l in b.inputs[kind].links]
    while stack:
        n = stack.pop()
        if n.type == "TEX_IMAGE":
            return n.image
        stack += [l.from_node for i in n.inputs for l in i.links]
    return None


def _material(name, base, rough, normal=None, clip=False, metal=0.0):
    """A plain glTF-friendly material: base colour (and alpha clip) from one image, a normal map, constants."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image, t.location = base, (-500, 250)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if clip:                       # glTF alphaMode MASK, cutoff 0.5 (as pc_export's tiles)
        r = nt.nodes.new("ShaderNodeMath")
        r.operation, r.location = "ROUND", (-200, 0)
        nt.links.new(t.outputs["Alpha"], r.inputs[0])
        nt.links.new(r.outputs[0], b.inputs["Alpha"])
        m.surface_render_method = "DITHERED"
    if normal is not None:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image, tn.location = normal, (-700, -250)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.location = (-300, -250)
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.use_backface_culling = False
    return m


def _one_material(objs, m):
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(m)


# ---------------------------------------------------------------------------
# the monstera (obj_plant)
# ---------------------------------------------------------------------------
def terracotta_pixels(src_px):
    """Terracotta from the original white pot's albedo: its grey veining becomes a faint tonal variation, plus two
    scales of smooth noise. Matte, slightly varied, not painted stripes."""
    size = src_px.shape[0]
    L = src_px[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    m = float(np.median(L[L > 0.45])) if np.any(L > 0.45) else float(np.median(L))
    vein = np.clip((L - m) * 0.45, -0.10, 0.05)
    n1, n2 = _lowfreq(size, 10, 7), _lowfreq(size, 40, 3)
    f = 1.0 + vein + 0.05 * n1 + 0.025 * n2
    rgb = np.array(TERRACOTTA, np.float32)[None, None, :] * f[..., None]
    rgb[..., 1] *= 1.0 + 0.03 * n2                 # a little hue drift (orange to brown)
    rgb[..., 2] *= 1.0 - 0.04 * n1
    out = np.ones_like(src_px)
    out[..., :3] = np.clip(rgb, 0.0, 1.0)
    return out


def monstera(coll, lite):
    rep = {}
    ms = _import(SRC["plant"], coll)
    get = lambda p: next(o for o in ms if o.name.startswith(p))
    leaves_o, stems_o, pot_o, stand_o = get("Leaves"), get("root_HP"), get("Pot_LP"), get("Stand")
    rep["tris_downloaded"] = _tris(ms)
    bpy.data.objects.remove(stand_o, do_unlink=True)           # the mid-century stand: the plant sits on the sill
    # scale and origin: the pot's bottom centre at 0, pot bottom to the top leaf = HEIGHT
    pv, lv = _verts(pot_o), _verts(leaves_o)
    lo, hi = pv.min(0), pv.max(0)
    s = HEIGHT["plant"] / (max(lv[:, 2].max(), _verts(stems_o)[:, 2].max()) - lo[2])
    M = Matrix.Scale(s, 4) @ Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))
    _transform([leaves_o, stems_o, pot_o], M)
    rep["scale"] = round(s, 4)
    # materials (shared by all leaves: the leaf blade's and the stem's)
    m_leaf, m_stem, m_pot = leaves_o.data.materials[0], stems_o.data.materials[0], pot_o.data.materials[0]
    m_leaf.name, m_stem.name, m_pot.name = "mat_plant_leaf", "mat_plant_stem", "mat_plant_soil"
    # pot and soil: the soil is the largest flat disc above the pot's middle
    parts = _separate(pot_o)
    flat = [p for p in parts if np.ptp(_verts(p)[:, 2]) < 1e-4 and _verts(p)[:, 2].mean() > 0.03]
    soil = max(flat, key=_area)
    pot = _join([p for p in parts if p is not soil], "plant_pot")
    NM.set_name(soil, "plant_soil")
    # leaves and petioles
    leaves = sorted(_separate(leaves_o), key=_area, reverse=True)
    stems = _separate(stems_o)
    area = {l.name: _area(l) for l in leaves}
    trees = [_bvh(l) for l in leaves]
    info = {}
    for st in stems:
        v = _verts(st)
        zmin = v[:, 2].min()
        base = v[v[:, 2] < zmin + 0.002].mean(0)
        d = np.linalg.norm(v - base, axis=1)
        top = v[d > 0.95 * d.max()].mean(0) if d.max() > 0 else base
        dists = [t.find_nearest(Vector(top))[3] for t in trees]
        k = int(np.argmin(dists))
        info[st.name] = dict(base=base, top=top, length=float(d.max()), leaf=k if dists[k] < 0.012 and d.max() > 0.02 else None,
                             dist=float(dists[k]))
    # chains: a stem part whose top meets an assigned part's base belongs to the same leaf
    for _ in range(3):
        for st in stems:
            i = info[st.name]
            if i["leaf"] is not None or i["length"] < 0.02:
                continue
            for o2 in stems:
                j = info[o2.name]
                if j["leaf"] is not None and np.linalg.norm(i["top"] - j["base"]) < 0.006:
                    i["leaf"] = j["leaf"]
                    break
    stem_trees = [_bvh(st) for st in stems]
    mine = {k: [st for st in stems if info[st.name]["leaf"] == k] for k in range(len(leaves))}
    rest = [st for st in stems if info[st.name]["leaf"] is None]
    table, origins = [], []
    for k, leaf in enumerate(leaves):
        if mine[k]:
            low = min(mine[k], key=lambda st: info[st.name]["base"][2])
            origin = info[low.name]["base"]
        else:                                  # no petiole of its own: the blade's point nearest any stem
            best = None
            for vv in _verts(leaf):
                for t in stem_trees:
                    h = t.find_nearest(Vector(vv))
                    if h[0] is not None and (best is None or h[3] < best[1]):
                        best = (np.array(h[0][:]), h[3])
            origin = best[0]
        origins.append(origin)
        table.append(dict(leaf=f"plant_leaf_{k + 1:02d}", blade_area_cm2=round(area[leaf.name] * 1e4, 1),
                          petiole_parts=len(mine[k]), origin=[round(float(x), 4) for x in origin],
                          petiole_len=round(max((info[st.name]["length"] for st in mine[k]), default=0.0), 3),
                          dist=[round(info[st.name]["dist"], 4) for st in mine[k]]))
    for k, leaf in enumerate(leaves):
        obj = _join([leaf] + mine[k], f"plant_leaf_{k + 1:02d}")
        _set_origin(obj, origins[k])
    static = _join(rest, "plant_static") if rest else None
    rep["leaves"] = table
    rep["stems_without_leaf"] = len(rest)
    log(f"monstera: {len(leaves)} leaves, {sum(t['petiole_parts'] for t in table)} petiole parts joined, "
        f"{len(rest)} stem parts left in plant_static, scale {s:.3f}")
    leaf_objs = [bpy.data.objects[t["leaf"]] for t in table]
    # the terracotta pot
    src = _image_node(m_pot, "Base Color")
    nrm = _image_node(m_pot, "Normal")
    if lite:
        for mm in (m_leaf, m_stem, m_pot):     # the downloaded materials stay in the file unused; free their names
            mm.name = "src_" + mm.name
        _decimate(pot, LITE["pot"])
        for o in leaf_objs:
            _decimate(o, LITE["leaf"])
        n = LITE_TEX["pot"]
        tc = _image("tex_plant_terracotta", terracotta_pixels(_pixels(src, n, n)))
        nn = _image("tex_plant_pot_normal", _pixels(nrm, n, n), "Non-Color")
        _one_material([pot], _material("mat_plant_terracotta", tc, 0.88, normal=nn))
        lite_soil(soil, src)
        lite_leaves(leaf_objs + ([static] if static else []), m_leaf, m_stem)
    else:
        w = src.size[0]
        tc = _image("tex_plant_terracotta", terracotta_pixels(_pixels(src)))
        mt = m_pot.copy()
        mt.name = "mat_plant_terracotta"
        nt = mt.node_tree
        b = next(x for x in nt.nodes if x.type == "BSDF_PRINCIPLED")
        tex = next(l.from_node for l in b.inputs["Base Color"].links)
        tex.image = tc
        for inp in ("Roughness", "Metallic"):
            for l in list(b.inputs[inp].links):
                nt.links.remove(l)
        b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value = 0.88, 0.0
        _one_material([pot], mt)
        rep["terracotta_px"] = w
    root = _empty("plant", coll)
    for o in [pot, soil] + leaf_objs + ([static] if static else []):
        _parent(o, root)
    rep["tris"] = {o.name: _tris([o]) for o in [pot, soil] + leaf_objs + ([static] if static else [])}
    rep["tris_total"] = sum(rep["tris"].values())
    return root, rep


def lite_soil(soil, src):
    """Lite soil: its own small crop of the pot atlas, the soil's UVs stretched over it."""
    uv = soil.data.uv_layers.active.data
    a = np.empty(len(uv) * 2)
    uv.foreach_get("uv", a)
    a = a.reshape(-1, 2)
    u0, v0 = a.min(0)
    u1, v1 = a.max(0)
    W = 1024
    px = _pixels(src, W, W)
    crop = px[int(v0 * W):int(math.ceil(v1 * W)), int(u0 * W):int(math.ceil(u1 * W))]
    n = LITE_TEX["soil"]
    tmp = _image("tmp_soil", crop)
    im = _image("tex_plant_soil", _pixels(tmp, n, n))
    bpy.data.images.remove(tmp)
    a = (a - [u0, v0]) / [max(u1 - u0, 1e-6), max(v1 - v0, 1e-6)]
    uv.foreach_set("uv", a.ravel())
    _one_material([soil], _material("mat_plant_soil", im, 0.95))


def lite_leaves(objs, m_leaf, m_stem):
    """One atlas for the leaf blades and the petioles (colour + alpha, normal): leaf texture on top (1024 x 1024),
    a 32 px clear gutter, the stem texture squeezed into the bottom 224 rows. One material, alpha-tested."""
    W = LITE_TEX["leaf_atlas"]
    S, G = 224 * W // 1024, 32 * W // 1024
    H = W + G + S
    col = np.zeros((H, W, 4), np.float32)
    nrm = np.zeros((H, W, 4), np.float32)
    nrm[...] = (0.5, 0.5, 1.0, 1.0)
    col[S + G:] = _pixels(_image_node(m_leaf, "Base Color"), W, W)
    col[:S] = _pixels(_image_node(m_stem, "Base Color"), W, S)
    col[:S, :, 3] = 1.0
    nl, ns = _image_node(m_leaf, "Normal"), _image_node(m_stem, "Normal")
    nrm[S + G:] = _pixels(nl, W, W)
    nrm[:S] = _pixels(ns, W, S)
    nrm[..., 3] = 1.0
    tc = _image("tex_plant_leaf_atlas", col, alpha=True)
    tn = _image("tex_plant_leaf_atlas_normal", nrm, "Non-Color")
    m = _material("mat_plant_leaf", tc, 0.45, normal=tn, clip=True)
    for o in objs:
        me = o.data
        slot = {i: mm.name for i, mm in enumerate(me.materials)}
        mi = np.empty(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", mi)
        lt = np.empty(len(me.polygons), np.int32)
        me.polygons.foreach_get("loop_total", lt)
        is_leaf = np.repeat(np.array([slot[i] == m_leaf.name for i in mi], bool), lt)
        uv = me.uv_layers.active.data
        a = np.empty(len(uv) * 2)
        uv.foreach_get("uv", a)
        a = a.reshape(-1, 2)
        a[:, 1] = np.where(is_leaf, (S + G + a[:, 1] * W) / H, a[:, 1] * S / H)
        uv.foreach_set("uv", a.ravel())
        me.materials.clear()
        me.materials.append(m)
        me.polygons.foreach_set("material_index", np.zeros(len(me.polygons), np.int32))
        me.update()


# ---------------------------------------------------------------------------
# the snake plant and the desk plant (set_plants)
# ---------------------------------------------------------------------------
def _normalise(objs, height):
    """Pot bottom centre to the origin (the pot: the vertices in the lowest 3 cm), top at `height`."""
    v = np.concatenate([_verts(o) for o in objs])
    z0 = v[:, 2].min()
    low = v[v[:, 2] < z0 + 0.03]
    cx, cy = (low[:, 0].min() + low[:, 0].max()) / 2, (low[:, 1].min() + low[:, 1].max()) / 2
    s = height / (v[:, 2].max() - z0)
    _transform(objs, Matrix.Scale(s, 4) @ Matrix.Translation((-cx, -cy, -z0)))
    return s


def snake_plant(coll, lite):
    ms = _import(SRC["snake_plant"], coll)
    body = _join(ms, "snake_plant_body")
    rep = {"tris_downloaded": _tris([body])}
    rep["scale"] = round(_normalise([body], HEIGHT["snake_plant"]), 4)
    # the scan's material is unlit (an Emission shader, the light baked into the photo texture): lit, matte-ish
    img = next(n.image for n in body.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE")
    rep["texture_px"] = list(img.size)
    if lite:
        _decimate(body, LITE["snake"])
        n = LITE_TEX["snake"]
        img = _image("tex_snake_plant", _pixels(img, n, n))
    _one_material([body], _material("mat_snake_plant", img, 0.6))
    root = _empty("snake_plant", coll)
    _parent(body, root)
    rep["tris"] = _tris([body])
    return root, rep


def desk_plant(coll, lite):
    ms = _import(SRC["desk_plant"], coll)
    rep = {"tris_downloaded": _tris(ms)}
    named = {"dirt": "desk_plant_pebbles", "ground": "desk_plant_soil", "plant": "desk_plant_leaves", "pot": "desk_plant_pot"}
    objs = []
    for o in ms:
        key = o.name.replace("potted_plant_04_", "").split(".")[0]
        NM.set_name(o, named[key])
        objs.append(o)
    rep["scale"] = round(_normalise(objs, HEIGHT["desk_plant"]), 4)
    m = ms[0].data.materials[0]
    rep["texture_px"] = list(_image_node(m, "Base Color").size)
    if lite:
        ratio = {"desk_plant_pot": "desk_pot", "desk_plant_leaves": "desk_leaves", "desk_plant_pebbles": "desk_pebbles",
                 "desk_plant_soil": "desk_soil"}
        for o in objs:
            _decimate(o, LITE[ratio[o.name]])
        n = LITE_TEX["desk"]
        img = _image("tex_desk_plant", _pixels(_image_node(m, "Base Color"), n, n))
        _one_material(objs, _material("mat_desk_plant", img, 0.6))
    else:
        m.name = "mat_desk_plant"
    root = _empty("desk_plant", coll)
    for o in objs:
        _parent(o, root)
    rep["tris"] = {o.name: _tris([o]) for o in objs}
    rep["tris_total"] = _tris(objs)
    return root, rep


# ---------------------------------------------------------------------------
# build, place
# ---------------------------------------------------------------------------
def build(lite=False, collection=None):
    """The three plants, side by side (LAYOUT), in `collection` (default: a collection 'plants')."""
    coll = collection or _coll("plants")
    out = {}
    for key, fn in (("plant", monstera), ("snake_plant", snake_plant), ("desk_plant", desk_plant)):
        root, rep = fn(coll, lite)
        root.location = (*LAYOUT[key], 0.0)
        rep["credit"] = CREDITS[key]
        out[key] = rep
    bpy.context.view_layer.update()
    return out


def place(get, P):
    """Put the three roots at plan v3's numbers: obj_plant on the window sill, its best side to the INTRO camera;
    the snake plant and the desk plant with their best side to the HERO_V3 camera."""
    for key, cam in (("plant", P.INTRO), ("snake_plant", P.HERO_V3), ("desk_plant", P.HERO_V3)):
        x, y, z = P.CP[key]["at"]
        d = Vector(cam["pos"]) - Vector((x, y, z))
        yaw = math.atan2(d.x, -d.y)            # local -Y (the model's front) towards the camera
        get(key).matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(yaw, 4, "Z")
    bpy.context.view_layer.update()


def export(path, objs):
    _select(objs)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                              export_cameras=False, export_lights=False, export_extras=False)
    log(f"exported {path}: {os.path.getsize(path) / 1e6:.2f} MB")
    return os.path.getsize(path)


# ---------------------------------------------------------------------------
# close-ups: each plant alone, the same camera for rich and lite (EEVEE)
# ---------------------------------------------------------------------------
def closeups(tag):
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 900, 1000
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("plants_world")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value, bg.inputs[1].default_value = (0.55, 0.56, 0.6, 1.0), 0.8
    sun = bpy.data.objects.new("still_sun", bpy.data.lights.new("still_sun", "SUN"))
    sc.collection.objects.link(sun)
    sun.data.energy, sun.data.angle = 3.0, math.radians(8)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    floor = bpy.data.objects.new("still_floor", bpy.data.meshes.new("still_floor"))
    floor.data.from_pydata([(-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0)], [], [(0, 1, 2, 3)])
    sc.collection.objects.link(floor)
    cd = bpy.data.cameras.new("still_cam")
    cam = bpy.data.objects.new("still_cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.lens = 60
    os.makedirs(os.path.join(FOOT, "closeup-parts"), exist_ok=True)
    for key in ("plant", "snake_plant", "desk_plant"):
        x, y = LAYOUT[key]
        h = HEIGHT[key]
        for k2, (x2, y2) in LAYOUT.items():
            for o in bpy.data.objects[k2].children_recursive:
                o.hide_render = k2 != key
        target = Vector((x, y, h * 0.5))
        cam.location = target + Vector((0.35, -1.0, 0.55)).normalized() * h * 3.3
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(FOOT, "closeup-parts", f"{key}-{tag}.png")
        bpy.ops.render.render(write_still=True)
        log(f"close-up {key} {tag}")


def sheets():
    code = ("import sys,os\nfrom PIL import Image, ImageDraw\nd0=sys.argv[1]\n"
            "for k in ('plant','snake_plant','desk_plant'):\n"
            " a=Image.open(os.path.join(d0,'closeup-parts',k+'-rich.png')).convert('RGB')\n"
            " b=Image.open(os.path.join(d0,'closeup-parts',k+'-lite.png')).convert('RGB')\n"
            " s=Image.new('RGB',(a.width+b.width+60,a.height+80),(24,24,26));s.paste(a,(20,60));s.paste(b,(a.width+40,60))\n"
            " d=ImageDraw.Draw(s);d.text((20,20),k+': rich (Blender) '+sys.argv[2+('plant','snake_plant','desk_plant').index(k)*2],fill=(230,230,230))\n"
            " d.text((a.width+40,20),'lite (web) '+sys.argv[3+('plant','snake_plant','desk_plant').index(k)*2],fill=(230,230,230))\n"
            " s.save(os.path.join(d0,'closeup-'+k.replace('_','-')+'.png'))\n")
    rep = json.load(open(os.path.join(FOOT, "plants-report.json")))
    lab = []
    for k in ("plant", "snake_plant", "desk_plant"):
        for v in ("rich", "lite"):
            r = rep.get(v, {}).get(k, {})
            t = r.get("tris_total", r.get("tris", "?"))
            lab.append(f"{t} tris")
    subprocess.run([PY, "-c", code, FOOT] + lab, check=False)


def _save_report(part, data):
    os.makedirs(FOOT, exist_ok=True)
    p = os.path.join(FOOT, "plants-report.json")
    rep = json.load(open(p)) if os.path.exists(p) else {}
    rep[part] = data
    json.dump(rep, open(p, "w"), indent=1, default=lambda x: x.tolist() if hasattr(x, "tolist") else str(x))


def main():
    stages = os.environ.get("STAGE", "rich,lite,closeups").split(",")
    os.makedirs(OUT, exist_ok=True)
    for lite in (False, True):
        tag = "lite" if lite else "rich"
        if tag not in stages:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        rep = build(lite=lite)
        objs = list(bpy.data.collections["plants"].all_objects)
        if not lite:
            pack_and_save(BLEND)
            log(f"saved {BLEND}")
        rep["glb_bytes"] = export(LITE_GLB if lite else RICH_GLB, objs)
        rep["images"] = {im.name: list(im.size) for im in bpy.data.images if im.users}
        _save_report(tag, rep)
        if "closeups" in stages:
            closeups(tag)
    if "closeups" in stages:
        sheets()
    log("done")


if __name__ == "__main__":
    main()
