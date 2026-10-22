# Blender test: a small upright piano with 88 named keys, rendered clay and finished,
# exported as GLB. Run:
#   /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python piano_test.py
import bpy, math, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def mat(name, rgb, rough=0.5, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    return m

def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

M_CASE = mat("piano_case", srgb("#2a170e"), 0.22, coat=0.6)
M_WHITE = mat("key_white", srgb("#f1ece2"), 0.35)
M_BLACK = mat("key_black", srgb("#141210"), 0.3)
M_FELT = mat("felt", srgb("#7a1f1f"), 0.9)
M_BRASS = mat("brass", srgb("#c9a227"), 0.3, metal=1.0)
M_FLOOR = mat("floor", srgb("#3e281a"), 0.55)
M_WALL = mat("wall", srgb("#e9e4dc"), 0.9)

def box(name, size, loc, material, parent=None, origin=None):
    """Box of size (x,y,z) centred at loc. origin: optional world point for the object's origin."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.data.name = name + "_mesh"
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if origin is not None:
        cur = scene.cursor.location.copy()
        scene.cursor.location = origin
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        scene.cursor.location = cur
    o.data.materials.append(material)
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

# ---------- piano (Blender: Z up, the piano faces -Y) ----------
root = bpy.data.objects.new("obj_piano", None)
scene.collection.objects.link(root)

W, D, H = 1.50, 0.58, 1.24          # case width, depth, height (m)
KEY_TOP = 0.74                        # top of the white keys
WK_W, WK_GAP, WK_L = 0.0225, 0.001, 0.15
BK_W, BK_L, BK_UP = 0.0125, 0.095, 0.012

box("piano_static", (W, D, H - 0.0), (0, D / 2, H / 2), M_CASE, root)            # main case
box("piano_cheek_l", (0.06, 0.20, 0.10), (-W / 2 + 0.03, -0.10, KEY_TOP - 0.02), M_CASE, root)
box("piano_cheek_r", (0.06, 0.20, 0.10), (W / 2 - 0.03, -0.10, KEY_TOP - 0.02), M_CASE, root)
box("piano_keybed", (W, 0.20, 0.06), (0, -0.10, KEY_TOP - 0.06), M_CASE, root)
box("piano_toe_l", (0.06, 0.30, 0.06), (-W / 2 + 0.05, -0.10, 0.03), M_CASE, root)
box("piano_toe_r", (0.06, 0.30, 0.06), (W / 2 - 0.05, -0.10, 0.03), M_CASE, root)
box("piano_leg_l", (0.05, 0.05, KEY_TOP - 0.12), (-W / 2 + 0.05, -0.17, (KEY_TOP - 0.12) / 2 + 0.06), M_CASE, root)
box("piano_leg_r", (0.05, 0.05, KEY_TOP - 0.12), (W / 2 - 0.05, -0.17, (KEY_TOP - 0.12) / 2 + 0.06), M_CASE, root)
box("piano_felt", (W - 0.14, 0.01, 0.012), (0, 0.004, KEY_TOP + 0.006), M_FELT, root)
# music rest, tilted back
rest = box("piano_music_rest", (0.95, 0.02, 0.24), (0, 0.02, KEY_TOP + 0.24), M_CASE, root)
rest.rotation_euler.x = math.radians(-12)
# fallboard (key cover), open: a slim board standing behind the keys, hinge at its back edge
box("piano_fallboard", (W - 0.14, 0.05, 0.10), (0, 0.03, KEY_TOP + 0.06), M_CASE, root, origin=(0, 0.055, KEY_TOP + 0.01))
# pedals
for i, x in enumerate((-0.09, 0, 0.09)):
    box(f"piano_pedal_{i+1:02d}", (0.035, 0.09, 0.012), (x, -0.16, 0.06), M_BRASS, root)

# ---------- 88 keys, A0 (MIDI 21) to C8 (MIDI 108) ----------
NAMES = ["c", "cs", "d", "ds", "e", "f", "fs", "g", "gs", "a", "as", "b"]
WHITE = {0, 2, 4, 5, 7, 9, 11}
whites = [m for m in range(21, 109) if m % 12 in WHITE]           # 52 white keys
pitch = WK_W + WK_GAP
x0 = -(len(whites) * pitch) / 2 + pitch / 2
white_x = {m: x0 + i * pitch for i, m in enumerate(whites)}
count = 0
for m in range(21, 109):
    name = f"piano_key_{NAMES[m % 12]}{m // 12 - 1}"
    if m % 12 in WHITE:
        x = white_x[m]
        o = box(name, (WK_W, WK_L, 0.022), (x, -WK_L / 2, KEY_TOP - 0.011), M_WHITE, root,
                origin=(x, 0.0, KEY_TOP - 0.011))                     # hinge at the back
    else:
        x = (white_x[m - 1] + white_x[m + 1]) / 2
        o = box(name, (BK_W, BK_L, 0.022), (x, -BK_L / 2, KEY_TOP + BK_UP - 0.011), M_BLACK, root,
                origin=(x, 0.0, KEY_TOP + BK_UP - 0.011))
    count += 1
assert count == 88, count

# a few keys pressed, so the pivot shows (C major chord around middle C)
for n in ("piano_key_c4", "piano_key_e4", "piano_key_g4"):
    bpy.data.objects[n].rotation_euler.x = math.radians(-2.5)

# bench
box("set_bench", (0.80, 0.34, 0.06), (0, -0.62, 0.49), M_CASE)
for sx in (-0.36, 0.36):
    for sy in (-0.76, -0.48):
        box("set_bench_leg", (0.04, 0.04, 0.46), (sx, sy, 0.23), M_CASE)

# ---------- room bits ----------
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0)); f = bpy.context.active_object; f.name = "set_floor"; f.data.materials.append(M_FLOOR)
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, D + 0.05, 4), rotation=(math.radians(90), 0, 0)); w = bpy.context.active_object; w.name = "set_wall"; w.data.materials.append(M_WALL)

# ---------- light: 5:40 a.m. blue hour ----------
world = bpy.data.worlds.new("blue_hour"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (*srgb("#2b3a55"), 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
bpy.ops.object.light_add(type="AREA", location=(-2.2, -1.6, 2.4))
win = bpy.context.active_object; win.name = "lt_window"
win.data.shape = "RECTANGLE"; win.data.size = 1.4; win.data.size_y = 1.8
win.data.energy = 420; win.data.color = srgb("#b9cdf5")
win.rotation_euler = (math.radians(55), 0, math.radians(-50))
bpy.ops.object.light_add(type="POINT", location=(1.2, -1.0, 1.6))
lamp = bpy.context.active_object; lamp.name = "lt_lamp"
lamp.data.energy = 25; lamp.data.color = srgb("#ffc98a"); lamp.data.shadow_soft_size = 0.3

# ---------- camera ----------
bpy.ops.object.camera_add(location=(1.9, -2.6, 1.45))
cam = bpy.context.active_object; cam.name = "still_cam"
cam.data.lens = 40
target = bpy.data.objects.new("still_cam_target", None); scene.collection.objects.link(target)
target.location = (0.05, 0.0, 0.78)
c = cam.constraints.new("TRACK_TO"); c.target = target; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
scene.camera = cam

# ---------- render settings: Cycles on the Metal GPU ----------
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices:
    d.use = True
scene.cycles.device = "GPU"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"

def render(path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

# finished look
render(os.path.join(OUT, "piano-test-finished.png"))
# clay look: one grey material over everything
clay = mat("clay", (0.62, 0.62, 0.6), 0.8)
bpy.context.view_layer.material_override = clay
render(os.path.join(OUT, "piano-test-clay.png"))
bpy.context.view_layer.material_override = None

# ---------- save and export ----------
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "piano-test.blend"))
for o in list(scene.objects):
    o.select_set(o.name.startswith(("obj_", "piano_")))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "piano-test.glb"), export_format="GLB",
                          use_selection=True, export_yup=True, export_apply=True,
                          export_cameras=False, export_lights=False)
print("DONE keys", count, "devices", [d.name for d in prefs.devices if d.use])
