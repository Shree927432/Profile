"""Three-way sheet for the MX Master 3S: the scan, our model, the real photo, per main view (EEVEE).
    $B blender/tools/mouse_threeway.py -- <out_dir>
Opens out/components/desktop_mouse.blend, links in the scan working copy (decimated; local only, never exported)."""
import os
import sys
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, BL)
OUT = sys.argv[sys.argv.index("--") + 1]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(BL, "out", "components", "desktop_mouse.blend"))
with bpy.data.libraries.load(os.path.join(BL, "out", "components", "mouse-scan-work.blend")) as (src, dst):
    dst.objects = ["scan_mouse"]
scan = dst.objects[0]
bpy.context.scene.collection.objects.link(scan)
d = scan.modifiers.new("dec", "DECIMATE")
d.ratio = 200000 / len(scan.data.polygons)
from lib import materials as M
from lib import compare
scan.data.materials.clear()
scan.data.materials.append(M.principled("mat_scan_grey", base="#c9cacc", rough=0.6))
ours = [o for o in bpy.data.objects if o.type == "MESH" and o is not scan]
sc = bpy.context.scene
compare.ensure_studio(0.45)
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 24
sc.render.film_transparent = False
sc.render.resolution_x, sc.render.resolution_y = 900, 640
sc.view_settings.view_transform = "AgX"
cd = bpy.data.cameras.new("tw")
cam = bpy.data.objects.new("tw", cd)
sc.collection.objects.link(cam)
sc.camera = cam
c = Vector((0, 0, 0.024))
VIEWS = {"top": ((0, 0, 0.5), "ORTHO"), "nose": ((0, 0.5, 0.024), "ORTHO"), "thumb": ((-0.5, 0, 0.024), "ORTHO"),
         "right": ((0.5, 0, 0.024), "ORTHO"), "threeq": ((-0.16, 0.13, 0.17), "PERSP")}
for k, (pos, typ) in VIEWS.items():
    cd.type = typ
    cd.ortho_scale = 0.17 if k == "top" else 0.15
    cd.lens = 60
    cam.location = pos
    cam.rotation_euler = (0, 0, 0) if k == "top" else (c - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    for tag, show in (("scan", [scan]), ("ours", ours)):
        for o in [scan] + ours:
            o.hide_render = o not in show
        sc.render.filepath = os.path.join(OUT, f"tw-{k}-{tag}.png")
        bpy.ops.render.render(write_still=True)
# the scan's own silhouettes (alpha) for the compare test's ortho views: the real object where no photo exists
sc.render.film_transparent = True
sc.render.image_settings.color_mode = "RGBA"
for o in [scan] + ours:
    o.hide_render = o is not scan
for k in ("nose", "thumb", "right"):
    pos, _ = VIEWS[k]
    cd.type = "ORTHO"
    cd.ortho_scale = 0.15
    cam.location = pos
    cam.rotation_euler = (c - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(os.path.dirname(OUT.rstrip("/")), "..", "cutouts", f"scan-{k}-alpha.png")
    bpy.ops.render.render(write_still=True)
print("THREEWAY", OUT)
