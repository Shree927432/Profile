"""Invented brand names on the AI-lab gear (decision 2026-10-26).

The names come only from content/room-brands.json. Each decal sits where the real maker's logo
sits, at its size, colour and finish, in Blender's built-in font (plain lettering, never the real
logo's typeface or graphic).

    from lib import brands
    brands.decal("speakers", parent=front_obj, at=(x, y, z), normal=(0, -1, 0), up=(0, 0, 1),
                 height=4 * MM, finish="printed", colour="#d8d8d8", name="a7v_1_brand", lite=lite)

`at`, `normal` and `up` are in the parent's local space (world space when there is no parent).
The text reads left to right for someone looking at the face from outside (along -normal).

Rich: real thin geometry. "printed" is raised 0.12 mm, "embossed" 0.3 mm, "engraved" a flat inlay
0.03 mm proud in a darker, glossier finish (a true recess would mean cutting the approved part),
"lit" is emissive and 0.05 mm proud, "polished" is a mirror inlay. With `conform=<object>` every
vertex is projected onto that object's surface (curved bodies).
Lite: the same letters as one flat layer (curve resolution 3) 0.25 mm off the surface, own small
material, no texture.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

MM = 0.001
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON = os.path.join(REPO, "content", "room-brands.json")

FINISH = {   # raised height (rich), roughness, metallic
    "printed": (0.12 * MM, 0.45, 0.0),
    "embossed": (0.30 * MM, 0.35, 0.0),
    "engraved": (0.03 * MM, 0.22, 0.0),
    "polished": (0.05 * MM, 0.08, 1.0),
    "lit": (0.05 * MM, 0.5, 0.0),
}
LITE_OFFSET = 0.25 * MM
SINK = 0.05 * MM          # the rich decal's floor sits this far inside the surface


def load():
    with open(JSON) as f:
        return json.load(f)["brands"]


def entry(key):
    return load()[key]


def _font():
    f = bpy.data.fonts.get("Bfont Regular")
    return f or bpy.data.fonts.load("<builtin>")


def _hex(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def material(finish, colour, emit=0.0, lite=False):
    nm = f"mat_brand_{finish}_{colour.lstrip('#').lower()}" + ("_lite" if lite else "")
    m = bpy.data.materials.get(nm)
    if m:
        return m
    m = bpy.data.materials.new(nm)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    _, rough, metal = FINISH[finish]
    col = _hex(colour)
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if finish == "lit":
        b.inputs["Emission Color"].default_value = col
        b.inputs["Emission Strength"].default_value = emit or 2.0
    m.diffuse_color = col
    return m


def _letters(text, lite, weight):
    """Flat 2D letters as (verts xy, faces) centred on the origin, 1 unit cap height."""
    cu = bpy.data.curves.new("brand_tmp_text", "FONT")
    cu.body = text
    cu.font = _font()
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.resolution_u = 3 if lite else 6
    cu.offset = weight          # outline growth: bold feel without a different typeface
    cu.fill_mode = "BOTH"
    ob = bpy.data.objects.new("brand_tmp_text", cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    return bm


def _ring(outer, inner, seg):
    bm = bmesh.new()
    vo = [bm.verts.new((outer * math.cos(2 * math.pi * i / seg), outer * math.sin(2 * math.pi * i / seg), 0))
          for i in range(seg)]
    vi = [bm.verts.new((inner * math.cos(2 * math.pi * i / seg), inner * math.sin(2 * math.pi * i / seg), 0))
          for i in range(seg)]
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    return bm


def frame(at, normal, up):
    n = Vector(normal).normalized()
    u = (Vector(up) - Vector(up).dot(n) * n).normalized()
    r = u.cross(n)
    m = Matrix((r, u, n)).transposed().to_4x4()
    m.translation = Vector(at)
    return m


def decal(key, at, normal, up, height=None, width=None, finish="printed", colour="#ffffff", parent=None,
          collection=None, conform=None, lite=False, name=None, spacing=1.0, weight=0.0, emit=0.0,
          mark=None, tilt_italic=0.0):
    """Make one brand decal; returns the object (None if the brand has no name and no mark)."""
    e = entry(key)
    text = e.get("name", "")
    mark = mark or e.get("mark")
    if not text and not mark:
        return None
    if text:
        bm = _letters(text, lite, weight)
    else:          # our own plain round mark: a ring, `height` is its outer diameter
        bm = _ring(0.5, 0.36, 24 if lite else 64)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    w0, h0 = max(xs) - min(xs), max(ys) - min(ys)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    if width:
        s = width / w0
    else:
        s = height / h0
    for v in bm.verts:
        v.co.x = (v.co.x - cx) * s
        v.co.y = (v.co.y - cy) * s
        v.co.z = 0.0
    if text and spacing != 1.0:
        _spread(bm, spacing, s * h0)
    lift, _, _ = FINISH[finish]
    M = frame(at, normal, up)
    pw = parent.matrix_world.copy() if parent is not None else Matrix.Identity(4)
    Wm = pw @ M                                    # decal frame in world space
    Wn = (Wm.to_3x3() @ Vector((0, 0, 1))).normalized()
    bvh = None
    if conform is not None:
        dg = bpy.context.evaluated_depsgraph_get()
        ce = conform.evaluated_get(dg)
        cme = ce.to_mesh()
        cbm = bmesh.new()
        cbm.from_mesh(cme)
        cbm.transform(ce.matrix_world)
        bvh = BVHTree.FromBMesh(cbm)
        ce.to_mesh_clear()

    def place(p2, off):
        w = Wm @ Vector((p2.x, p2.y, 0.0))
        nrm = Wn
        if bvh is not None:
            hit = bvh.ray_cast(w + Wn * 0.01, -Wn, 0.03)
            if hit[0] is None:
                hit = bvh.find_nearest(w)
            if hit[0] is not None:
                w = hit[0]
                nrm = hit[1].normalized()
                if nrm.dot(Wn) < 0:
                    nrm = -nrm
        return w + nrm * off
    bm.verts.index_update()
    flat = [v.co.copy() for v in bm.verts]
    out = bmesh.new()
    if lite:
        top = [out.verts.new(place(p, LITE_OFFSET)) for p in flat]
        for f in bm.faces:
            out.faces.new([top[v.index] for v in f.verts])
    else:
        top = [out.verts.new(place(p, lift)) for p in flat]
        bot = [out.verts.new(place(p, -SINK)) for p in flat]
        for f in bm.faces:
            out.faces.new([top[v.index] for v in f.verts])
            out.faces.new([bot[v.index] for v in reversed(f.verts)])
        for ed in bm.edges:
            if len(ed.link_faces) == 1:
                lp = next(l for l in ed.link_loops)
                a, b = lp.vert.index, lp.link_loop_next.vert.index
                out.faces.new((top[b], top[a], bot[a], bot[b]))
    bm.free()
    out.normal_update()
    # world -> parent-local
    inv = pw.inverted()
    out.transform(inv)
    nm = name + ("_lite" if lite and not name.endswith("_lite") else "") if name else f"{key}_brand"
    me = bpy.data.meshes.new(nm + "_mesh")
    out.to_mesh(me)
    out.free()
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(material(finish, colour, emit, lite))
    ob = bpy.data.objects.new(nm, me)
    coll = collection or (parent.users_collection[0] if parent is not None else bpy.context.scene.collection)
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    ob["brand_key"] = key
    ob["brand_finish"] = finish
    return ob


def _spread(bm, spacing, cap):
    """Open up the letter-spacing: shift each letter (connected island) by its index from the centre."""
    bm.verts.index_update()
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for ed in bm.edges:
        a, b = ed.verts
        parent[find(a.index)] = find(b.index)
    groups = {}
    for v in bm.verts:
        groups.setdefault(find(v.index), []).append(v)
    spans = []
    for vs in groups.values():
        xs = [v.co.x for v in vs]
        spans.append([min(xs), max(xs), vs])
    spans.sort(key=lambda s: s[0])
    letters = []
    for s in spans:           # merge islands that overlap in x (O and its hole, A and its counter)
        if letters and s[0] < letters[-1][1] - 1e-6:
            letters[-1][1] = max(letters[-1][1], s[1])
            letters[-1][2] += s[2]
        else:
            letters.append(s)
    k = len(letters)
    gap = (spacing - 1.0) * cap * 0.25
    for i, (_, _, vs) in enumerate(letters):
        d = (i - (k - 1) / 2) * gap
        for v in vs:
            v.co.x += d


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)
