"""The ceiling light and its wall switch (2026-11-15, obj_light): the owner's photo, "use this exact light design".

    B="/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python"
    $B blender/components/ceiling_light.py -- <outdir>     close-up renders (EEVEE), off and on, beside nothing else

The photo: a long black ceiling bar; under it three square black frames of three sizes at three heights, the largest
highest and at the back, the smallest lowest and in front, overlapping in plan; each hangs on two fine steel wires from
the bar, with a short black power sleeve rising from it; a white light strip runs all round each frame's underside.
No brand, no logo. Sizes are the common ones for this design (bar 110 cm; squares 80, 60 and 40 cm; a 3.5 x 4.5 cm
profile, the light a 12 mm line along its inner bottom edge).

In the room (build_v3.py): over the free floor at plan v3's LIGHT_V3, the bar along X (parallel to the window), the
smallest square's underside at 2.40 m (plan v3's pendant bottom); the ceiling is 3.00 m. The switch is the
Pune-style modular board at constants.SWITCH (left wall, the door's latch side, 1.20 m): a white plate with four
rockers, the first of which works.

Names (scene/objects/MESHES.md, obj_light):
  light_root          empty at the bar's centre on the ceiling
    light_bar, light_frame_1..3, light_wire_*, light_sleeve_*   (joined into light_static by the room build)
    light_led         the three diffusers, one mesh, one material (light_led): white plastic, off at dusk; the code
                      lights it. Not baked.
  switch_root         empty on the wall at the plate's centre
    light_switch_plate  the plate and the three idle rockers, one mesh (a click target; baked)
    light_switch      the working rocker: origin on its pivot, local X along the wall (the flip axis), local Z out
                      of the wall. Rest = off: the top half pressed in. On: the bottom half pressed in (Indian
                      switches). Not baked (it moves).
LAMPS (below) are the light the fixture gives in Cycles: thin area lights under and over every side of every frame.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

BAR = dict(len=1.10, w=0.12, t=0.03)                    # the ceiling bar
PROF = dict(w=0.035, t=0.045, led_w=0.012, led_t=0.004)  # a frame's profile; the diffuser runs along its inner bottom edge
# the three frames, in the bar's frame (x along the bar, y across it, z down from the ceiling to the frame's top):
# side, centre x, centre y, drop. The largest highest and to the back (+y, the window side), the smallest lowest in
# front, as in the photo. Each frame's two side members cross y = 0 under the bar, where its wires hang.
FRAMES = ((0.80, 0.10, 0.12, 0.16), (0.60, -0.25, -0.02, 0.36), (0.40, 0.06, -0.18, 0.55))
SLEEVE = dict(r=0.0045, h=0.12, inset=0.05)             # the power sleeve on each frame, beside its right wire
WIRE_R = 0.0007
CEIL = 3.00
# the light in Cycles (watts in all): down through the diffusers, a little up onto the ceiling as in the photo
LAMP = dict(down=95.0, up=22.0, color=(1.0, 0.90, 0.80))
ROCKER = dict(w=0.022, h=0.046, t=0.007, tilt=7.0, gap=0.008)   # one rocker; tilt in degrees each way


def _mat(name, color, rough, metal=0.0, emit=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 0.0      # off at dusk; on: lamp_on()
    return m


def materials():
    return dict(
        black=_mat("light_black", (0.018, 0.018, 0.02), 0.45, 0.6),
        led=_mat("light_led", (0.86, 0.86, 0.85), 0.35, emit=LAMP["color"]),
        steel=_mat("light_steel", (0.55, 0.56, 0.58), 0.3, 1.0),
        white=_mat("switch_white", (0.93, 0.93, 0.91), 0.35),
    )


def _obj(name, bm, mat, parent, collection):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    collection.objects.link(o)
    me.materials.append(mat)
    o.parent = parent
    return o


def _box(bm, x0, x1, y0, y1, z0, z1):
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
                          @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))


def _bevel_all(bm, w):
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=w, segments=1, affect="EDGES", clamp_overlap=True)


def _cyl(bm, a, b, r, seg=10):
    a, b = Vector(a), Vector(b)
    d = b - a
    q = d.normalized().to_track_quat("Z", "Y")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length,
                          matrix=Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4())


def frame_square(bm, cx, cy, s, ztop, w, t):
    """A square ring of profile w x t, outer side s, its top at ztop (four mitred-looking boxes)."""
    h = s / 2
    z0, z1 = ztop - t, ztop
    _box(bm, cx - h, cx + h, cy + h - w, cy + h, z0, z1)
    _box(bm, cx - h, cx + h, cy - h, cy - h + w, z0, z1)
    _box(bm, cx - h, cx - h + w, cy - h + w, cy + h - w, z0, z1)
    _box(bm, cx + h - w, cx + h, cy - h + w, cy + h - w, z0, z1)


def build(collection=None, at=(0.0, 0.0), yaw=0.0):
    """The fixture, its top on the ceiling at `at` (world x, y). Returns (root, info)."""
    col = collection or bpy.context.scene.collection
    M = materials()
    root = bpy.data.objects.new("light_root", None)
    col.objects.link(root)
    root.matrix_world = Matrix.Translation((at[0], at[1], CEIL)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
    bm = bmesh.new()
    _box(bm, -BAR["len"] / 2, BAR["len"] / 2, -BAR["w"] / 2, BAR["w"] / 2, -BAR["t"], 0)
    _bevel_all(bm, 0.002)
    _obj("light_bar", bm, M["black"], root, col)
    led = bmesh.new()
    lows = []
    for i, (s, cx, cy, drop) in enumerate(FRAMES, 1):
        bm = bmesh.new()
        frame_square(bm, cx, cy, s, -drop, PROF["w"], PROF["t"])
        bm.normal_update()
        _obj(f"light_frame_{i}", bm, M["black"], root, col)
        zb = -drop - PROF["t"]                              # the frame's underside
        inset = PROF["w"] - PROF["led_w"] - 0.002            # 2 mm of black inside it, as the photo's thin line
        frame_square(led, cx, cy, s - 2 * inset, zb + 0.0005, PROF["led_w"], PROF["led_t"])
        lows.append(round(CEIL + zb - PROF["led_t"], 3))
        bm = bmesh.new()
        for k, x in enumerate((cx - s / 2 + PROF["w"] / 2, cx + s / 2 - PROF["w"] / 2)):
            _cyl(bm, (x, 0, -drop), (x, 0, -BAR["t"]), WIRE_R, 6)
        _obj(f"light_wire_{i}", bm, M["steel"], root, col)
        bm = bmesh.new()                                    # the power sleeve, then its cable up to the bar
        sx = cx + s / 2 - PROF["w"] / 2
        _cyl(bm, (sx, -SLEEVE["inset"], -drop), (sx, -SLEEVE["inset"], -drop + SLEEVE["h"]), SLEEVE["r"], 12)
        _cyl(bm, (sx, -SLEEVE["inset"], -drop + SLEEVE["h"]), (sx, -min(SLEEVE["inset"], BAR["w"] / 2 - 0.01), -BAR["t"]),
             0.0012, 6)
        _obj(f"light_sleeve_{i}", bm, M["black"], root, col)
    led.normal_update()
    _obj("light_led", led, M["led"], root, col)
    return root, dict(lowest=min(lows), frames=[dict(side=s, centre=(cx, cy), top=round(CEIL - d, 3)) for s, cx, cy, d in FRAMES])


def switch(collection=None, wall_x=None, y=0.0, z=1.2, w=0.20, h=0.13):
    """The modular board on the left wall (its face towards +X), plate centre at (wall_x, y, z)."""
    col = collection or bpy.context.scene.collection
    M = materials()
    root = bpy.data.objects.new("switch_root", None)
    col.objects.link(root)
    # the board's frame: local X along the wall (world -Y, so the rockers read left to right from the room),
    # local Z out of the wall (world +X)
    root.matrix_world = Matrix.Translation((wall_x, y, z)) @ Matrix(((0, 0, 1, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    plate = bmesh.new()
    _box(plate, -w / 2, w / 2, -h / 2, h / 2, 0, 0.009)
    _bevel_all(plate, 0.0025)
    R = ROCKER
    n = 4
    x0 = -(n - 1) * (R["w"] + R["gap"]) / 2
    for k in range(n):
        x = x0 + k * (R["w"] + R["gap"])
        # off: the top half pressed in (a turn about local X that sends +Y into the wall)
        at = Matrix.Translation((x, 0.0, 0.009 + R["t"] / 2)) @ Matrix.Rotation(math.radians(-R["tilt"]), 4, "X")
        bm = bmesh.new()
        _box(bm, -R["w"] / 2, R["w"] / 2, -R["h"] / 2, R["h"] / 2, -R["t"] / 2, R["t"] / 2)
        _bevel_all(bm, 0.0015)
        if k == 0:
            o = _obj("light_switch", bm, M["white"], root, col)
            o.matrix_local = at
        else:
            bm.transform(at)
            me = bpy.data.meshes.new("tmp")
            bm.to_mesh(me)
            bm.free()
            plate.from_mesh(me)
            bpy.data.meshes.remove(me)
    _obj("light_switch_plate", plate, M["white"], root, col)
    return root


def lamps(root, scale=1.0):
    """Cycles area lights for the fixture (named lt_lamp_*): a thin strip under each side of each frame, facing down,
    and a weaker one over it, facing up. Returns them. Their watts split by length."""
    import bpy as _b
    total = sum(4 * s for s, *_ in FRAMES)
    out = []
    for i, (s, cx, cy, drop) in enumerate(FRAMES, 1):
        zb = -drop - PROF["t"] - PROF["led_t"] - 0.002
        zt = -drop + 0.002
        h = s / 2 - PROF["w"] + 0.002 + PROF["led_w"] / 2     # the diffuser's centre line
        ln = 2 * h
        sides = (((cx, cy + h), (ln, PROF["led_w"])), ((cx, cy - h), (ln, PROF["led_w"])),
                 ((cx - h, cy), (PROF["led_w"], ln)), ((cx + h, cy), (PROF["led_w"], ln)))
        for k, ((x, y), (sx, sy)) in enumerate(sides):
            for tag, z, watts, rot in (("dn", zb, LAMP["down"], (0, 0, 0)), ("up", zt, LAMP["up"], (math.pi, 0, 0))):
                d = _b.data.lights.new(f"lt_lamp_{i}{k}{tag}", "AREA")
                d.shape = "RECTANGLE"
                d.size, d.size_y = sx, sy
                d.energy = watts * scale * (s / total)
                d.color = LAMP["color"]
                o = _b.data.objects.new(d.name, d)
                _b.context.scene.collection.objects.link(o)
                o.matrix_world = root.matrix_world @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot[0], 4, "X")
                out.append(o)
    return out


def lamp_on(on=True, strength=8.0):
    """The diffusers glow (the stills; the site lights them in code)."""
    m = bpy.data.materials.get("light_led")
    if m:
        m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = strength if on else 0.0


# ---------------------------------------------------------------------------
# close-ups: python ... ceiling_light.py -- outdir
# ---------------------------------------------------------------------------
def _closeups(out):
    os.makedirs(out, exist_ok=True)
    for on in (False, True):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        wall = _mat("wall", (0.82, 0.82, 0.83), 0.9)
        bm = bmesh.new()
        _box(bm, -3, 3, -3, 3, CEIL, CEIL + 0.05)                  # ceiling
        _box(bm, -3, 3, 2.2, 2.25, 0, CEIL)                        # back wall
        _box(bm, -3, 3, -3, 3, -0.05, 0)                           # floor
        _obj("room", bm, wall, None, sc.collection)
        root, info = build(sc.collection, (0, 0))
        sw = switch(sc.collection, -1.2, 1.8, 1.2)
        w = bpy.data.worlds.new("w")
        w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.21, 0.24, 1)
        w.node_tree.nodes["Background"].inputs[1].default_value = 0.6 if not on else 0.25
        sc.world = w
        if on:
            lamps(root)
            lamp_on(True)
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        sc.collection.objects.link(cam)
        cam.data.lens = 26
        cam.location = (-0.35, -1.45, 1.75)                        # as the photo: below and in front, a little left
        cam.rotation_euler = (Vector((0.0, 0.05, 2.45)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.camera = cam
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 64
        sc.cycles.use_denoising = True
        try:
            sc.cycles.device = "GPU"
        except Exception:
            pass
        sc.view_settings.view_transform = "AgX"
        sc.render.resolution_x, sc.render.resolution_y = 900, 900
        sc.render.filepath = os.path.join(out, f"ceiling-light-{'on' if on else 'off'}.png")
        bpy.ops.render.render(write_still=True)
    print("CLOSEUPS", info, flush=True)


if __name__ == "__main__" and "--" in sys.argv:
    _closeups(sys.argv[sys.argv.index("--") + 1])
