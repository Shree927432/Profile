"""Tracing backdrops: a (lens-corrected, rectified) reference photo placed in the scene at true scale
and position, behind the model, for one orthographic view; and an orthographic camera that frames it
pixel for pixel, so a render from it lines up with the photo (compare.py uses that for exact tests).

Views (the room frame: front at -Y, right at +X, Z up; MESHES.md):

    view    seen from   image right   image up   backdrop sits at
    front   -Y          +X            +Z         y = +depth (behind the model)
    back    +Y          -X            +Z         y = -depth
    right   +X          +Y            +Z         x = -depth   (Blender's Right view, numpad 3)
    left    -X          -Y            +Z         x = +depth
    top     +Z          +X            +Y         z = -depth   (front at the bottom of the image)

Placement: a refs.ref_record() (image, mm_per_px, anchor_px, anchor_mm). anchor_px is a pixel in the
photo (x right, y down) and anchor_mm the same point on the model in the view's own right/up axes, in
mm; e.g. for the front of a screen standing on the desk: the photo's bottom-centre of the panel and
(0, panel bottom height). refs.anchor_of() and refs.mm_per_px_extent() give both from a silhouette.

    from lib import backdrops, refs
    rec = refs.ref_record(photo, s, refs.anchor_of(mask, "bottom-centre"), (0, 115), view="front")
    bd = backdrops.add(rec, opacity=0.6)                # a textured plane (renders; for sheets)
    bd = backdrops.add(rec, kind="empty")               # a Blender image empty (viewport only, no render cost)
    cam = backdrops.ortho_camera(rec)                   # renders line up with the photo, pixel for pixel
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

VIEWS = {
    #        right                up                   toward the viewer
    "front": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "back": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "right": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    "left": ((0, -1, 0), (0, 0, 1), (-1, 0, 0)),
    "top": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
}


def axes(view):
    r, u, n = VIEWS[view]
    return Vector(r), Vector(u), Vector(n)


def image_size(path):
    im = bpy.data.images.load(path, check_existing=True)
    return im, im.size[0], im.size[1]


def frame(rec):
    """World corners of the photo for a ref record: (top_left, right_step, down_step, w, h, image), where a
    pixel corner (x, y) sits at top_left + x * right_step + y * down_step, in the view's plane through
    the model origin."""
    im, w, h = image_size(rec["image"])
    R, U, N = axes(rec["view"])
    s = rec["mm_per_px"] / 1000.0
    ax, ay = rec["anchor_px"]
    am = Vector(rec["anchor_mm"]) / 1000.0
    anchor_world = R * am[0] + U * am[1]
    top_left = anchor_world - R * (ax * s) + U * (ay * s)
    return top_left, R * s, -U * s, w, h, im


def _material(name, im, opacity):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = im
    tex.interpolation = "Linear"
    em = nt.nodes.new("ShaderNodeEmission")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = opacity
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mul.inputs[0])
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except AttributeError:
        pass
    m.diffuse_color = (1, 1, 1, opacity)
    return m


def add(rec, depth=1.0, opacity=1.0, kind="plane", name=None, collection=None):
    """Put the photo behind the model for rec['view'] at true scale. kind 'plane' (a textured, emissive
    plane: shows in renders and in Material/Texture viewport shading) or 'empty' (Blender's image empty,
    shown only in orthographic viewports, never rendered). depth: metres behind the model origin."""
    view = rec["view"]
    R, U, N = axes(view)
    tl, rs, ds, w, h, im = frame(rec)
    name = name or f"ref_{view}_{os.path.splitext(os.path.basename(rec['image']))[0]}"[:60]
    coll = collection or bpy.context.scene.collection
    back = -N * depth

    def flat(p):           # move a point into the backdrop's plane
        return p - N * p.dot(N) + back
    if kind == "empty":
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "IMAGE"
        e.data = im
        size = max(w, h) * rs.length
        e.empty_display_size = size
        e.empty_image_offset = (-0.5, -0.5)
        e.empty_image_depth = "BACK"
        e.empty_image_side = "FRONT"
        e.show_empty_image_perspective = False
        e.show_empty_image_orthographic = True
        e.use_empty_image_alpha = opacity < 1.0
        e.color[3] = opacity
        centre = tl + rs * (w / 2) + ds * (h / 2)
        e.matrix_world = Matrix.Translation(flat(centre)) @ _basis(R, U, N).to_4x4()
        coll.objects.link(e)
        return e
    corners = [tl + ds * h, tl + rs * w + ds * h, tl + rs * w, tl]       # bottom-left, bottom-right, top-right, top-left
    me = bpy.data.meshes.new(name + "_mesh")
    me.from_pydata([tuple(flat(c)) for c in corners], [], [[0, 1, 2, 3]])
    uv = me.uv_layers.new(name="UVMap")
    for li, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[li].uv = c
    me.materials.append(_material("mat_" + name, im, opacity))
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.hide_select = True
    o["backdrop"] = rec["image"]
    return o


def _basis(R, U, N):
    m = Matrix((R, U, N)).transposed()          # columns: local X, Y, Z
    return m


def ortho_camera(rec, distance=5.0, name=None, set_scene=True, scale_res=1.0):
    """An orthographic camera looking at the backdrop's view that frames the photo exactly: the render's
    pixel (x, y) is the photo's pixel (x, y) (at scale_res=1). Sets the scene resolution."""
    R, U, N = axes(rec["view"])
    tl, rs, ds, w, h, im = frame(rec)
    centre = tl + rs * (w / 2) + ds * (h / 2)
    name = name or f"cam_ref_{rec['view']}"
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.type = "ORTHO"
    cd.sensor_fit = "AUTO"
    cd.ortho_scale = max(w, h) * rs.length
    cd.shift_x = cd.shift_y = 0.0
    cd.clip_start = 0.01
    cd.clip_end = distance * 4
    cam = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if cam.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(cam)
    cam.matrix_world = Matrix.Translation(centre - N * centre.dot(N) + N * distance) @ _basis(R, U, N).to_4x4()
    scene = bpy.context.scene
    if set_scene:
        scene.camera = cam
        scene.render.resolution_x = max(1, int(round(w * scale_res)))
        scene.render.resolution_y = max(1, int(round(h * scale_res)))
        scene.render.resolution_percentage = 100
        scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1.0
    return cam


def view_camera(view, centre, width_m, aspect=16 / 9, distance=5.0, name=None, ortho=True, lens=50):
    """A plain camera for a view (front/back/right/left/top) centred on `centre`, framing width_m across;
    orthographic by default. For quick stills of a model with no photo."""
    R, U, N = axes(view)
    name = name or f"cam_{view}"
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.sensor_fit = "HORIZONTAL" if aspect >= 1 else "VERTICAL"
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = width_m if aspect >= 1 else width_m / aspect
    else:
        cd.type = "PERSP"
        cd.sensor_width = 36
        cd.lens = lens
        distance = width_m / 36 * lens
    cd.clip_start = 0.01
    cd.clip_end = distance * 4
    cam = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if cam.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(cam)
    c = Vector(centre)
    cam.matrix_world = Matrix.Translation(c + N * distance) @ _basis(R, U, N).to_4x4()
    return cam


def three_quarter_camera(centre, size_m, az=-35.0, el=22.0, lens=50, aspect=16 / 9, name="cam_three_quarter"):
    """A perspective camera from the front-left (az from -Y toward -X, degrees) and above (el), far enough
    to fit a bounding size of size_m."""
    c = Vector(centre)
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    dist = size_m * 1.7 / (36 / lens) * max(1.0, 16 / 9 / aspect)
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.type = "PERSP"
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36
    cd.lens = lens
    cd.clip_start = 0.01
    cd.clip_end = dist * 4
    cam = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if cam.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(cam)
    loc = c + d * dist
    fwd = (c - loc).normalized()
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd)
    cam.matrix_world = Matrix.Translation(loc) @ _basis(right, up, -fwd).to_4x4()
    return cam
