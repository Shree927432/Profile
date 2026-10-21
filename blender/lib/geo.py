"""Geometry helpers: boxes, extruded profiles, lofts, cylinders, bevels, origins.

Everything is built in the object's own frame (facing -Y, right at +X, Z up) and in
metres. Bevels are modifiers, so the clay and wireframe looks show them and the GLB
export applies them.
"""
import math
import bmesh
import bpy
from mathutils import Vector

from . import names


def _link(obj, collection=None, parent=None):
    (collection or bpy.context.scene.collection).objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def mesh_obj(name, verts, faces, collection=None, parent=None, material=None, smooth=True):
    me = bpy.data.meshes.new(name + "_mesh")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    me.update()
    obj = bpy.data.objects.new(name, me)
    _link(obj, collection, parent)
    names.set_name(obj, name)
    if material is not None:
        me.materials.append(material)
    if smooth:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(35))
    return obj


def from_bmesh(name, bm, **kw):
    me = bpy.data.meshes.new(name + "_mesh")
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    _link(obj, kw.get("collection"), kw.get("parent"))
    names.set_name(obj, name)
    if kw.get("material") is not None:
        me.materials.append(kw["material"])
    if kw.get("smooth", True):
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(35))
    return obj


def _ccw(pts):
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
            for i in range(len(pts)))
    return pts if a > 0 else list(reversed(pts))


def prism(name, pts, axis, a0, a1, **kw):
    """Extrude a 2D polygon along an axis from a0 to a1.

    axis "X": pts are (y, z); axis "Y": pts are (x, z); axis "Z": pts are (x, y).
    """
    pts = _ccw([tuple(p) for p in pts])
    n = len(pts)

    def v3(p, a):
        if axis == "X":
            return (a, p[0], p[1])
        if axis == "Y":
            return (p[0], a, p[1])
        return (p[0], p[1], a)

    verts = [v3(p, a0) for p in pts] + [v3(p, a1) for p in pts]
    # For X and Z, CCW in (u,v) faces +axis; for Y, (x,z) CCW faces -Y. Fix winding after.
    faces = [list(reversed(range(n))), list(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in verts]
    for f in faces:
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return from_bmesh(name, bm, **kw)


def box(name, x0, x1, y0, y1, z0, z1, **kw):
    return prism(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "Z", z0, z1, **kw)


def loft(name, bottom, top, **kw):
    """Hull of two 4-point rings (bottom and top), e.g. a tapered black key."""
    bm = bmesh.new()
    b = [bm.verts.new(v) for v in bottom]
    t = [bm.verts.new(v) for v in top]
    bm.faces.new(list(reversed(b)))
    bm.faces.new(t)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([b[i], b[j], t[j], t[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return from_bmesh(name, bm, **kw)


def cylinder(name, r, p0, p1, segments=16, **kw):
    """Closed cylinder from point p0 to point p1."""
    bm = bmesh.new()
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r, radius2=r,
                                depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    bmesh.ops.translate(bm, vec=(p0 + p1) / 2, verts=bm.verts)
    return from_bmesh(name, bm, **kw)


def bevel(obj, width, segments=3, angle=35, profile=0.5):
    m = obj.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.profile = profile
    m.use_clamp_overlap = True
    m.harden_normals = True
    return obj


def set_origin(obj, point):
    """Move the object's origin to `point` (in its parent's frame) without moving the mesh."""
    p = Vector(point)
    off = p - obj.location
    obj.data.transform(__import__("mathutils").Matrix.Translation(-off))
    obj.location = p
    return obj


def origin_to_center(obj):
    vs = [v.co for v in obj.data.vertices]
    c = sum(vs, Vector()) / len(vs)
    return set_origin(obj, obj.location + c)


def screen_plane(name, width, height, center, **kw):
    """A screen per MESHES.md: spans local X and Z, faces local -Y, UVs written
    upside down (V = 0 on the top edge) because the glTF exporter flips V."""
    w, h = width / 2, height / 2
    obj = mesh_obj(name, [(-w, 0, -h), (w, 0, -h), (w, 0, h), (-w, 0, h)], [[0, 1, 2, 3]],
                   smooth=False, **kw)
    uv = obj.data.uv_layers.new(name="UVMap")
    for li, (u, v) in zip(range(4), [(0, 1), (1, 1), (1, 0), (0, 0)]):
        uv.data[li].uv = (u, v)
    obj.location = center
    return obj
