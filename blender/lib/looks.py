"""Lights, sky and looks for the room (Blender only, never exported; MESHES.md section 5).

    build_lights()   lt_dawn_sky, lt_monitor (collection lights_dawn); lt_night_sky,
                     lt_storm_flash, lt_night_fill, lt_monitor (lights_night); the sky plane
                     video_sky outside the window, with a dawn and a night material
    use_look(name)   "dawn" (5:40 a.m. blue hour, the default bake's light) or "night"
                     (the storm): switches lights, sky and world
    clay_on/off      one grey material over everything
    wire_look()      glowing blue wireframe on navy; returns undo()
"""
import math

import bpy

from . import constants as C, geo, materials as M, plan_v2 as P

RX, RY, H = C.RX, C.RY, C.ROOM["height"]
WIN = P.WINDOW_V2
BT = C.ROOM["wall_back_t"]
WIN_C = ((WIN["x0"] + WIN["x1"]) / 2, (WIN["sill"] + WIN["head"]) / 2)
WIN_W, WIN_H = WIN["x1"] - WIN["x0"], WIN["head"] - WIN["sill"]

LOOKS = {
    # world colour, world strength, which collection, sky material
    "dawn": dict(world=C.COL["dawn_world"], strength=0.25, coll="lights_dawn", sky="mat_video_sky_dawn"),
    "night": dict(world="#05070d", strength=0.08, coll="lights_night", sky="mat_video_sky_night"),
}


def _coll(name):
    scene = bpy.context.scene
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    return c


def _area(name, coll, loc, size, size_y, energy, colour, rot=(-90, 0, 0)):
    d = bpy.data.lights.new(name, "AREA")
    d.shape = "RECTANGLE"
    d.size, d.size_y = size, size_y
    d.energy = energy
    d.color = M.srgb(colour)
    o = bpy.data.objects.new(name, d)
    coll.objects.link(o)
    o.location = loc
    o.rotation_euler = tuple(math.radians(a) for a in rot)     # -90 about X: emits toward -Y
    return o


def _sky_material(name, stops, strength):
    m, nt, b = M._new(name)
    nt.nodes.remove(b)
    out = nt.nodes["Material Output"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    col = M._ramp(nt, sep.outputs["Z"], stops)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Strength"].default_value = strength
    nt.links.new(col, e.inputs["Color"])
    nt.links.new(e.outputs[0], out.inputs[0])
    m.use_fake_user = True              # kept in the .blend while the other look is on
    return m


def build_lights():
    dawn, night = _coll("lights_dawn"), _coll("lights_night")
    wx, wz = WIN_C
    _area("lt_dawn_sky", dawn, (wx, RY + 0.11, wz), WIN_W, WIN_H, 260, C.COL["dawn_sky"])
    _area("lt_night_sky", night, (wx, RY + 0.11, wz), WIN_W, WIN_H, 160, "#6f86b8")
    fl = _area("lt_storm_flash", night, (wx + 0.3, RY + 1.6, wz + 0.6), 2.0, 1.2, 0.0, "#dfe8ff", rot=(-105, 0, 8))
    fl.data.spread = math.radians(40)          # into the window, not over the outside of the walls
    _area("lt_night_fill", night, (0.2, -0.6, H - 0.25), 2.4, 2.0, 90, "#7d8db5", rot=(0, 0, 0))
    sd = P.SD
    lm = _area("lt_monitor", dawn, (P.XM, sd["y"] - sd["d"] / 2 - 0.02, sd["z"] + sd["h"] / 2), P.POSTS["w"],
               P.POSTS["h"], 4.0, "#cfe0ff")
    night.objects.link(lm)
    # the sky beyond the window: a big emissive plane (never exported)
    sky = geo.mesh_obj("video_sky", [(-2.2, 0, -1.6), (2.2, 0, -1.6), (2.2, 0, 1.6), (-2.2, 0, 1.6)],
                       [[0, 1, 2, 3]], collection=_coll("video_sky"), smooth=False)
    sky.location = (wx, RY + BT + 0.9, wz)
    _sky_material("mat_video_sky_dawn", [(0.0, "#a9bde6"), (0.45, "#6f8fcf"), (1.0, "#27406f")], 1.6)
    _sky_material("mat_video_sky_night", [(0.0, "#1b2236"), (0.5, "#0d1220"), (1.0, "#05070d")], 1.0)
    sky.data.materials.append(bpy.data.materials["mat_video_sky_dawn"])
    use_look("dawn")


def use_look(name):
    lk = LOOKS[name]
    scene = bpy.context.scene
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = M.rgba(lk["world"])
    bg.inputs["Strength"].default_value = lk["strength"]
    on = set(o.name for o in bpy.data.collections[lk["coll"]].objects)
    for cn in ("lights_dawn", "lights_night"):
        for o in bpy.data.collections[cn].objects:
            o.hide_render = o.hide_viewport = o.name not in on
    sky = bpy.data.objects.get("video_sky")
    if sky is not None:
        sky.data.materials[0] = bpy.data.materials[lk["sky"]]


def clay_on():
    bpy.context.view_layer.material_override = M.clay()


def clay_off():
    bpy.context.view_layer.material_override = None


def wire_look(thickness=0.004, skip=()):
    """Glowing blue wireframe on dark navy. Returns an undo()."""
    scene = bpy.context.scene
    vl = bpy.context.view_layer
    hidden, wires, bevels = [], [], []
    for o in bpy.data.objects:
        if o.type == "LIGHT" or o.name == "video_sky" or o.name in skip:
            if not o.hide_render:
                o.hide_render = True
                hidden.append(o)
        elif o.type == "MESH":
            for m in o.modifiers:
                if m.type == "BEVEL" and m.width < 0.003 and m.show_render:
                    m.show_render = False
                    bevels.append(m)
            w = o.modifiers.new("wire", "WIREFRAME")
            fine = o.name.startswith("piano_key_") or o.name in ("piano_interior", "piano_strings", "piano_hammers")
            w.thickness = thickness * (0.4 if fine else 1.0)
            w.use_replace = True
            wires.append((o, w))
    vl.material_override = M.emission("mat_look_wire", "#9fd0ff", 3.0)
    bg = scene.world.node_tree.nodes["Background"]
    old = tuple(bg.inputs["Color"].default_value), bg.inputs["Strength"].default_value
    bg.inputs["Color"].default_value = M.rgba("#0d1626")
    bg.inputs["Strength"].default_value = 1.0

    def undo():
        for o in hidden:
            o.hide_render = False
        for o, w in wires:
            o.modifiers.remove(w)
        for m in bevels:
            m.show_render = True
        vl.material_override = None
        bg.inputs["Color"].default_value = old[0]
        bg.inputs["Strength"].default_value = old[1]
    return undo


def camera(name, loc, target, vfov=None, lens=None, coll=None, fstop=None, size=(1920, 1080)):
    """A camera with a TRACK_TO look-at empty `<name>_target`. vfov in degrees (vertical)."""
    scene = bpy.context.scene
    coll = coll or scene.collection
    cd = bpy.data.cameras.new(name)
    if vfov is not None:
        cd.sensor_fit = "VERTICAL"
        cd.sensor_height = 24
        cd.lens = 12 / math.tan(math.radians(vfov) / 2)
    else:
        cd.sensor_fit = "HORIZONTAL"
        cd.sensor_width = 36
        cd.lens = lens or 35
    cd.clip_start = 0.02
    cam = bpy.data.objects.new(name, cd)
    coll.objects.link(cam)
    cam.location = loc
    t = bpy.data.objects.new(name + "_target", None)
    coll.objects.link(t)
    t.location = target
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = t, "TRACK_NEGATIVE_Z", "UP_Y"
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_object = t
    return cam
