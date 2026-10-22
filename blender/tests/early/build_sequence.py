# Build sequence of the piano test: the parts appear in build order while the camera
# pushes in. Rendered in three looks that are cut together with crossfades later.
# Run: Blender -b piano-test.blend --python build_sequence.py -- <wire|clay|final> <first> <last>
import bpy, math, os, sys

look, first, last = sys.argv[sys.argv.index("--") + 1:][:3]
first, last = int(first), int(last)
HERE = os.path.dirname(bpy.data.filepath)
OUT = os.path.join(HERE, "..", "footage", "2026-10-21-blender-test", "build", look)
os.makedirs(OUT, exist_ok=True)
scene = bpy.context.scene
objs = bpy.data.objects

def srgb(h):
    h = h.lstrip("#"); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

# ---------- build order: (frame it starts appearing, object names) ----------
order = [(10, ["piano_static"]), (22, ["piano_keybed"]), (30, ["piano_cheek_l", "piano_cheek_r"]),
         (36, ["piano_leg_l", "piano_leg_r"]), (40, ["piano_toe_l", "piano_toe_r"]),
         (46, ["piano_pedal_01"]), (48, ["piano_pedal_02"]), (50, ["piano_pedal_03"]),
         (56, ["piano_felt"]), (60, ["piano_music_rest"]), (64, ["piano_fallboard"])]
NAMES = ["c", "cs", "d", "ds", "e", "f", "fs", "g", "gs", "a", "as", "b"]
for i, m in enumerate(range(21, 109)):                 # glissando, A0 up to C8
    order.append((70 + round(i * 1.2), [f"piano_key_{NAMES[m % 12]}{m // 12 - 1}"]))
order.append((180, [o.name for o in objs if o.name.startswith("set_bench")]))

POP = 8
for start, names in order:
    for n in names:
        o = objs[n]
        o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=start)
        o.scale = (1.08, 1.08, 1.08); o.keyframe_insert("scale", frame=start + 5)
        o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=start + POP)

# the C major chord presses near the end and releases
for n in ("piano_key_c4", "piano_key_e4", "piano_key_g4"):
    o = objs[n]
    for f, deg in ((296, 0), (300, -2.5), (318, -2.5), (324, 0)):
        o.rotation_euler.x = math.radians(deg); o.keyframe_insert("rotation_euler", frame=f)

# ---------- camera: slow push-in and swing ----------
cam, target = objs["still_cam"], objs["still_cam_target"]
pivot = bpy.data.objects.new("still_cam_pivot", None); scene.collection.objects.link(pivot)
pivot.location = target.location
cam.parent = pivot
for f, ang, dist, h in ((1, -34, 4.3, 1.1), (330, 8, 3.0, 0.62)):
    pivot.rotation_euler = (0, 0, math.radians(ang)); pivot.keyframe_insert("rotation_euler", frame=f)
    cam.location = (0, -dist, h); cam.keyframe_insert("location", frame=f)

# ---------- looks ----------
scene.render.engine = "BLENDER_EEVEE"
if look == "wire":
    for n in ("set_floor", "set_wall"):
        objs[n].hide_render = True
    for o in objs:
        if o.type == "MESH" and not o.hide_render:
            mod = o.modifiers.new("wire", "WIREFRAME"); mod.thickness = 0.006; mod.use_replace = True
    glow = bpy.data.materials.new("wire_glow"); glow.use_nodes = True
    nt = glow.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*srgb("#9fd0ff"), 1); em.inputs["Strength"].default_value = 3.0
    outn = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], outn.inputs[0])
    bpy.context.view_layer.material_override = glow
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (*srgb("#0d1626"), 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    for l in objs:
        if l.type == "LIGHT":
            l.hide_render = True
elif look == "clay":
    clay = bpy.data.materials.get("clay") or bpy.data.materials.new("clay")
    clay.use_nodes = True
    clay.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.62, 0.6, 1)
    clay.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    bpy.context.view_layer.material_override = clay
# "final" keeps the scene's own materials and lights

scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.fps = 30
scene.frame_start, scene.frame_end = first, last
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 92
scene.render.filepath = os.path.join(OUT, "f")
bpy.ops.render.render(animation=True)
print("BUILD DONE", look, first, last)
