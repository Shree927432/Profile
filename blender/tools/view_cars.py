"""Look at the four cars at full detail (2026-11-15, owner: "i want to see cars 3d models at full resolution").

    /Applications/Blender.app/Contents/MacOS/Blender blender/out/components/cars.blend --python blender/tools/view_cars.py

cars.blend holds the rich cars (the downloads at full geometry, repainted, logos removed; blender/components/cars.py)
on their shelves in the room's frame, with no room around them. This adds a soft studio light (a grey world and
three area lights, viewing only, not saved) and frames the cars in EEVEE's rendered view. Click a car in the
Outliner and press numpad . to fly to it.
"""
import bpy
from mathutils import Vector


def studio():
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("view_world")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.32, 0.33, 0.36, 1)
    bg.inputs["Strength"].default_value = 0.6
    root = bpy.data.objects.get("set_cars")
    pts = [o.matrix_world @ Vector(c) for o in (root.children_recursive if root else bpy.data.objects)
           if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    mid = (lo + hi) / 2
    for name, off, energy, size in (("view_key", (0.0, -0.9, 0.5), 60, 0.8), ("view_fill", (-0.8, -0.6, 0.1), 25, 1.0),
                                    ("view_rim", (0.8, -0.2, 0.6), 30, 0.6)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size = energy, size
        lo_ = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo_)
        lo_.location = mid + Vector(off)
        lo_.rotation_euler = (mid - lo_.location).to_track_quat("-Z", "Y").to_euler()
    return root


def setup():
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.view_settings.view_transform = "AgX"
    root = studio()
    bpy.ops.object.select_all(action="DESELECT")
    if root:
        for o in [root] + list(root.children_recursive):
            if o.type == "MESH":
                o.select_set(True)
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                sp = area.spaces.active
                sp.shading.type = "RENDERED"
                sp.overlay.show_overlays = False
                sp.clip_start = 0.001
                reg = next(r for r in area.regions if r.type == "WINDOW")
                with bpy.context.temp_override(window=win, area=area, region=reg):
                    bpy.ops.view3d.view_axis(type="FRONT")
                    bpy.ops.view3d.view_selected()
                sp.region_3d.view_perspective = "PERSP"
    return None


bpy.app.timers.register(setup, first_interval=1.0)
