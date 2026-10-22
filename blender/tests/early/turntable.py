# Turntable footage of the piano test: the camera swings in an arc in front of the piano.
# Run: Blender -b piano-test.blend --python turntable.py
import bpy, math, os

OUT = os.path.join(os.path.dirname(bpy.data.filepath), "..", "footage", "2026-10-21-blender-test", "turntable")
os.makedirs(OUT, exist_ok=True)
scene = bpy.context.scene
cam = bpy.data.objects["still_cam"]
target = bpy.data.objects["still_cam_target"]

# pivot the camera around the piano: an empty at the target, camera parented to it
pivot = bpy.data.objects.new("still_cam_pivot", None)
scene.collection.objects.link(pivot)
pivot.location = target.location
cam.parent = pivot
cam.location = (0, -3.2, 0.75)

FRAMES = 120
scene.frame_start, scene.frame_end = 1, FRAMES
for f, angle in ((1, -38), (FRAMES // 2, 38), (FRAMES, -38)):
    pivot.rotation_euler = (0, 0, math.radians(angle))
    pivot.keyframe_insert("rotation_euler", frame=f)
for fc in pivot.animation_data.action.fcurves if pivot.animation_data.action and hasattr(pivot.animation_data.action, "fcurves") else []:
    for k in fc.keyframe_points:
        k.interpolation = "SINE"

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.fps = 30
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 92
scene.render.filepath = os.path.join(OUT, "f")
bpy.ops.render.render(animation=True)
print("TURNTABLE DONE", OUT)
