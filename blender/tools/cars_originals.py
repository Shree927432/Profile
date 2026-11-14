"""The four downloaded cars as they came (2026-11-15, owner: "Yes, originals too"): original materials, liveries and
logos, at real size, side by side on a grey studio floor, for viewing only. Nothing here goes into the room or the
site (the room's cars are repainted with every logo removed; blender/components/cars.py).

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/tools/cars_originals.py
    /Applications/Blender.app/Contents/MacOS/Blender blender/out/components/cars_originals.blend --python blender/tools/view_room.py

Uses cars.py's own loader (nose to +X, bottom centre at the origin), then undoes its 1:18 scale. Saved to
blender/out/components/cars_originals.blend (git-ignored), with a camera `still_hero` the viewer script looks through.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

BL = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, BL)
sys.path.insert(0, os.path.join(BL, "components"))
import cars as CR  # noqa: E402
from lib.blendfile import pack_and_save  # noqa: E402

OUT = os.path.join(BL, "out", "components", "cars_originals.blend")

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
coll = bpy.data.collections.new("cars_originals")
sc.collection.children.link(coll)
x = 0.0
for key in ("w17", "porsche", "gt3", "one"):
    root, meshes, info = CR.load(key, coll)
    root.scale = (1 / CR.SCALE,) * 3                          # back to real size
    ln = info["size"][0] / CR.SCALE
    root.location = (x + ln / 2, 0, 0)
    x += ln + 1.2
    print("CAR", key, round(ln, 2), "m", sum(len(o.data.polygons) for o in meshes), "faces", flush=True)
span = x - 1.2
mid = Vector((span / 2, 0, 0.6))
bpy.ops.mesh.primitive_plane_add(size=1, location=(span / 2, 0, 0))
floor = bpy.context.object
floor.name = "view_floor"
floor.scale = (span + 8, 14, 1)
fm = bpy.data.materials.new("view_floor")
fm.diffuse_color = (0.18, 0.18, 0.2, 1)
floor.data.materials.append(fm)
w = sc.world or bpy.data.worlds.new("view_world")
sc.world = w
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.35, 0.36, 0.4, 1)
bg.inputs["Strength"].default_value = 0.8
for name, off, energy, size in (("view_key", (0, -7, 5), 4000, 6), ("view_fill", (-span / 2 - 3, -5, 3), 1500, 6),
                                ("view_rim", (span / 2 + 3, 4, 5), 2000, 5)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy, ld.size = energy, size
    lo = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(lo)
    lo.location = mid + Vector(off)
    lo.rotation_euler = (mid - lo.location).to_track_quat("-Z", "Y").to_euler()
cd = bpy.data.cameras.new("still_hero")
cd.lens = 35
cam = bpy.data.objects.new("still_hero", cd)
sc.collection.objects.link(cam)
cam.location = mid + Vector((0, -span * 0.75, 2.2))
cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
pack_and_save(OUT)
print("SAVED", OUT, flush=True)
