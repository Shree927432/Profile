"""Three ceiling-light ideas for obj_light (2026-11-15), lit and seen from below in a plain white room corner at
dusk, for the owner to choose from. Design only: nothing here goes into the room.

    blender -b --factory-startup --python blender/design/pendant_options.py -- <outdir>

A  paper lantern: a 45 cm white paper globe, thin ribs, on a white cord
B  opal globe: a 30 cm opal glass sphere under a short brass rod and a small canopy
C  halo ring: a 60 cm thin white ring of light hung on three fine wires
Each is rendered off (as the room is at dusk) and on (warm, 2700 K), and from the desk view's height.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp"
CEIL = 2.8
BOTTOM = 2.40                                                       # the shade's bottom, as plan v3


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0, trans=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def obj(name, bm, material):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(material)
    return o


def cyl(r, z0, z1, x=0.0, y=0.0, seg=24):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=z1 - z0,
                          matrix=__import__("mathutils").Matrix.Translation((x, y, (z0 + z1) / 2)))
    return bm


def sphere(r, c, seg=48, ring=24, squash=1.0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=r)
    for v in bm.verts:
        v.co.z *= squash
        v.co += Vector(c)
    return bm


def room():
    wall = mat("wall", (0.86, 0.86, 0.88), 0.9)
    bm = bmesh.new()
    for (a, b, c, d) in [((-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0)),                # floor
                         ((-3, -3, CEIL), (-3, 3, CEIL), (3, 3, CEIL), (3, -3, CEIL)),    # ceiling
                         ((-3, 3, 0), (3, 3, 0), (3, 3, CEIL), (-3, 3, CEIL)),            # back wall
                         ((3, -3, 0), (3, 3, 0), (3, 3, CEIL), (3, -3, CEIL))]:           # right wall
        vs = [bm.verts.new(p) for p in (a, b, c, d)]
        bm.faces.new(vs)
    obj("room", bm, wall)
    w = bpy.data.worlds.new("dusk")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.2, 0.3, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.35
    bpy.context.scene.world = w


def canopy(material, r=0.06):
    obj("canopy", cyl(r, CEIL - 0.025, CEIL), material)


def cord(material, z0, x=0.0, y=0.0, r=0.003):
    obj("cord", cyl(r, z0, CEIL - 0.02, x, y, 8), material)


def lantern(on):
    white = mat("cord", (0.92, 0.92, 0.9), 0.5)
    paper = mat("paper", (0.95, 0.93, 0.88), 0.85, emit=(1.0, 0.72, 0.42), strength=6.0 if on else 0.0, trans=0.3)
    r = 0.225
    c = (0, 0, BOTTOM + r)
    o = obj("lantern", sphere(r, c, 48, 24, 0.92), paper)
    o.visible_shadow = False                                            # the bulb's light passes the paper
    rib = mat("rib", (0.8, 0.78, 0.72), 0.8)
    for k in range(1, 12):                                              # the paper's ribs, as thin rings
        zz = -r * 0.92 + k * (2 * r * 0.92) / 12
        rr = r * math.sqrt(max(0.0, 1 - (zz / (r * 0.92)) ** 2))
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, segments=48, radius=rr + 0.001)
        for v in bm.verts:
            v.co.z = c[2] + zz
        ring = obj(f"rib{k}", bm, rib)
        ring.visible_shadow = False
        ring.modifiers.new("t", "SKIN")
        ring.data.skin_vertices[0].data.foreach_set("radius", [0.0015, 0.0015] * len(ring.data.vertices))
    canopy(white)
    cord(white, BOTTOM + 2 * r * 0.92)
    return Vector(c), r


def opal(on):
    brass = mat("brass", (0.78, 0.6, 0.32), 0.3, 1.0)
    glass = mat("opal", (0.97, 0.96, 0.94), 0.25, emit=(1.0, 0.74, 0.46), strength=9.0 if on else 0.0, trans=0.15)
    r = 0.15
    c = (0, 0, BOTTOM + r)
    obj("globe", sphere(r, c), glass).visible_shadow = False             # the bulb's light passes the glass
    obj("collar", cyl(0.035, BOTTOM + 2 * r - 0.01, BOTTOM + 2 * r + 0.03), brass)
    obj("rod", cyl(0.007, BOTTOM + 2 * r + 0.03, CEIL - 0.02, seg=12), brass)
    canopy(brass, 0.055)
    return Vector(c), r


def halo(on):
    white = mat("white", (0.93, 0.93, 0.92), 0.4)
    glow = mat("led", (0.95, 0.94, 0.9), 0.4, emit=(1.0, 0.76, 0.5), strength=14.0 if on else 0.0)
    R = 0.30
    z = BOTTOM + 0.1
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, segments=96, radius=R)
    for v in bm.verts:
        v.co.z = z
    ring = obj("ring", bm, white)
    ring.modifiers.new("t", "SKIN")
    ring.data.skin_vertices[0].data.foreach_set("radius", [0.014, 0.014] * len(ring.data.vertices))
    sub = ring.modifiers.new("s", "SUBSURF")
    sub.levels = sub.render_levels = 1
    bm = bmesh.new()                                                    # the diffuser on the ring's underside
    bmesh.ops.create_circle(bm, segments=96, radius=R)
    for v in bm.verts:
        v.co.z = z - 0.012
    band = obj("band", bm, glow)
    band.modifiers.new("t", "SKIN")
    band.data.skin_vertices[0].data.foreach_set("radius", [0.009, 0.004] * len(band.data.vertices))
    wire = mat("wire", (0.6, 0.6, 0.6), 0.3, 1.0)
    for k in range(3):
        a = k * 2 * math.pi / 3
        bm = bmesh.new()
        p0, p1 = Vector((R * math.cos(a), R * math.sin(a), z)), Vector((0.03 * math.cos(a), 0.03 * math.sin(a), CEIL - 0.02))
        v0, v1 = bm.verts.new(p0), bm.verts.new(p1)
        bm.edges.new((v0, v1))
        w = obj(f"wire{k}", bm, wire)
        w.modifiers.new("t", "SKIN")
        w.data.skin_vertices[0].data.foreach_set("radius", [0.0012, 0.0012] * 2)
    canopy(white, 0.07)
    return Vector((0, 0, z)), R


def render(kind, on, path):
    clear()
    room()
    centre, r = {"A": lantern, "B": opal, "C": halo}[kind](on)
    if on:                                                              # the light the shade gives the room
        L = bpy.data.lights.new("bulb", "POINT")
        L.energy = 60
        L.color = (1.0, 0.74, 0.46)
        L.shadow_soft_size = r * 0.6
        lo = bpy.data.objects.new("bulb", L)
        lo.location = centre
        bpy.context.scene.collection.objects.link(lo)
    win = bpy.data.lights.new("dusk", "AREA")                           # the window's evening light
    win.energy = 120
    win.color = (1.0, 0.62, 0.5)
    win.size = 2.0
    wo = bpy.data.objects.new("dusk", win)
    wo.location = (-2.5, 2.0, 1.6)
    wo.rotation_euler = (0, math.radians(-75), math.radians(-30))
    bpy.context.scene.collection.objects.link(wo)
    cam = bpy.data.cameras.new("cam")
    cam.lens = 30
    co = bpy.data.objects.new("cam", cam)
    co.location = (-1.6, -1.9, 1.55)
    d = (centre + Vector((0, 0, 0.12))) - co.location
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(co)
    sc = bpy.context.scene
    sc.camera = co
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 720, 720
    sc.view_settings.view_transform = "AgX"
    try:
        sc.eevee.use_raytracing = True
    except AttributeError:
        pass
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


os.makedirs(OUT, exist_ok=True)
for kind in "ABC":
    for on in (False, True):
        render(kind, on, os.path.join(OUT, f"pendant-{kind}-{'on' if on else 'off'}.png"))
print("done", OUT)
