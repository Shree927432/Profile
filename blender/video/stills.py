"""Light process capture for one build step (docs/10-video-plan.md): Cycles stills of the room
from the hero camera (blue hour, clay, wireframe) and a top view, plus a light-leak check.

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/video/stills.py -- --out=2026-10-24-room-shell-v2
    (add -b after Blender for headless; a stage list after `--`: hero,top,leak by default; --quick;
    --grazing moves the leak check's lights to 5 cm from the floor and ceiling planes)

Opens blender/out/room.blend (run blender/build.py first). Writes to video-local/footage/<out>/:
    hero-bluehour.png, hero-clay.png, hero-wire.png   1920x1080, still_cam_home (room_view)
    top.png                                           orthographic, the ceiling hidden from the camera
    leak-hero.png, leak-back.png                      the leak check (below), EEVEE, half size
    stills-report.json                                render times, the leak check's numbers
The screens show the site's posts list (the 2026-10-22 capture of the screen canvas) and a dim
dashboard colour; nothing is saved back to the .blend.

Leak check: every light inside off, the world black, the window plugged, and bright lights
outside behind each corner of the room. Any light inside then came through a seam. The check
reports the brightest pixel; the room is light-tight when it stays near black.
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from lib import constants as C, geo, looks, materials as M, plan_v2 as P, run  # noqa: E402

ARGS = run.args()
STAGE = next((a for a in ARGS if not a.startswith("--")), "hero,top,leak")
STAGES = set(STAGE.split(","))
QUICK = "--quick" in ARGS
GRAZING = "--grazing" in ARGS       # leak check with the outside lights 5 cm off the floor and the ceiling plane
_out = next((a for a in ARGS if a.startswith("--out=")), None)
if _out is None:
    raise SystemExit("stills.py: pass --out=<folder name under video-local/footage>")
FOOTAGE = os.path.join(C.FOOTAGE, _out[6:])
BLEND = os.path.join(C.OUT, "room.blend")
POSTS = os.path.join(C.FOOTAGE, "2026-10-22-room-shell", "posts-screen.png")
REPORT = {"stills": {}}
T0 = time.time()
EXPOSURE = 0.6


def screens():
    """The posts list on the posts screen (flipped: the screen's V = 0 is its top edge), a dim
    dashboard blue on the rig's screen."""
    import numpy as np
    nt = bpy.data.materials["mat_monitor_screen"].node_tree
    if os.path.exists(POSTS):
        img = bpy.data.images.load(POSTS, check_existing=True)
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        img.pixels.foreach_set(np.ascontiguousarray(px.reshape(h, w, 4)[::-1]).ravel())
        nt.nodes["screen_image"].image = img
    nt = bpy.data.materials["mat_rig_screen"].node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for sock in (b.inputs["Base Color"], b.inputs["Emission Color"]):
        for ln in list(sock.links):
            nt.links.remove(ln)
    b.inputs["Base Color"].default_value = M.rgba("#0b1424")
    b.inputs["Emission Color"].default_value = M.rgba("#2a5aa8")
    b.inputs["Emission Strength"].default_value = 0.8


def top_camera():
    cd = bpy.data.cameras.new("still_cam_top")
    cd.type, cd.ortho_scale = "ORTHO", 4.95
    cam = bpy.data.objects.new("still_cam_top", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0.0, 0.0, 2.95)
    return cam


def render(name, samples):
    scene = bpy.context.scene
    scene.cycles.samples = 32 if QUICK else samples
    path = os.path.join(FOOTAGE, name + ".png")
    run.log(f"{name}: rendering")
    dt = yield from run.render_to(path)
    REPORT["stills"][name] = {"path": path, "render_s": round(dt)}
    run.log(f"{name} done in {dt:.0f} s")


def stage_hero():
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["still_cam_home"]
    scene.view_settings.exposure = EXPOSURE
    yield from render("hero-bluehour", 256)
    looks.clay_on()
    fill = bpy.data.objects["lt_night_fill"]
    fill.hide_render = False
    yield from render("hero-clay", 128)
    fill.hide_render = True
    looks.clay_off()
    scene.view_settings.exposure = 0.0
    undo = looks.wire_look()
    yield from render("hero-wire", 48)
    undo()


def stage_top():
    scene = bpy.context.scene
    scene.camera = top_camera()
    ceil = bpy.data.objects["room_ceiling"]
    ceil.visible_camera = False
    fill = bpy.data.objects["lt_night_fill"]
    fill.hide_render = False
    old = fill.data.energy
    fill.data.energy = 220
    scene.render.resolution_x = scene.render.resolution_y = 1400
    scene.view_settings.exposure = EXPOSURE
    yield from render("top", 128)
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    fill.data.energy = old
    fill.hide_render = True
    ceil.visible_camera = True


def stage_leak():
    """Outside light only (around the corners at 0.6, 1.5 and 2.4 m, and a sun over the roof);
    the brightest pixel seen inside, per view, in EEVEE (where the 2026-10-22 leak showed) and
    in Cycles (ray-exact: a seam leaks there too, a shadow-map artifact does not)."""
    import numpy as np
    scene = bpy.context.scene
    run.setup_render("BLENDER_EEVEE", samples=32, quick=True)
    scene.view_settings.exposure = 0.0
    for o in bpy.data.objects:
        if o.type == "LIGHT":
            o.hide_render = True
    sky = bpy.data.objects.get("video_sky")
    if sky:
        sky.hide_render = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.0
    # emissive parts would light the room themselves: switch them off for the check
    emit = []
    for m in bpy.data.materials:
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.node_tree else None
        if b is not None and b.inputs["Emission Strength"].default_value > 0:
            emit.append((b, b.inputs["Emission Strength"].default_value))
            b.inputs["Emission Strength"].default_value = 0.0
    coll = bpy.data.collections.new("leak_check")
    scene.collection.children.link(coll)
    W = P.WINDOW_V2
    bt = C.ROOM["wall_back_t"]
    st = C.ROOM["wall_side_t"]
    plug = M.principled("mat_leak_plug", base="#000000", rough=1.0)
    # black blocks over the two openings, outside the walls (the openings themselves are not seams)
    geo.box("leak_plug", W["x0"] - 0.5, W["x1"] + 0.5, P.RY + bt + 0.001, P.RY + bt + 0.3, W["sill"] - 0.5, W["head"] + 0.5,
            collection=coll, material=plug)
    D = C.DOOR
    geo.box("leak_door", -P.RX - st - 0.3, -P.RX - st - 0.001, D["y0"] - 0.5, D["y1"] + 0.5, -0.3, D["head"] + 0.5,
            collection=coll, material=plug)
    for i, (sx, sy) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
        for z in ((0.05, 2.95) if GRAZING else (0.6, 1.5, 2.4)):
            d = bpy.data.lights.new(f"leak_{i}_{z}", "POINT")
            d.energy, d.shadow_soft_size = 4000, 0.05
            o = bpy.data.objects.new(d.name, d)
            coll.objects.link(o)
            o.location = (sx * (P.RX + 0.7), sy * (P.RY + 0.7), z)
    sky = bpy.data.lights.new("leak_sky", "SUN")
    sky.energy = 50
    o = bpy.data.objects.new("leak_sky", sky)
    coll.objects.link(o)
    o.rotation_euler = (math.radians(30), 0, math.radians(25))
    back = looks.camera("still_cam_leak_back", (0.0, 1.6, 1.5), (0.0, -2.1, 1.3), vfov=80)
    views = [("leak-hero-eevee", bpy.data.objects["still_cam_home"], "BLENDER_EEVEE"),
             ("leak-back-eevee", back, "BLENDER_EEVEE"),
             ("leak-hero-cycles", bpy.data.objects["still_cam_home"], "CYCLES"),
             ("leak-back-cycles", back, "CYCLES")]
    REPORT["leak"] = {}
    for name, cam, engine in views:
        scene.render.engine = engine
        scene.cycles.samples = 64
        scene.camera = cam
        path = os.path.join(FOOTAGE, name + ".png")
        yield from run.render_to(path)
        img = bpy.data.images.load(path)
        px = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        lum = px.reshape(-1, 4)[:, :3].max(axis=1)
        REPORT["leak"][name] = {"max": round(float(lum.max()), 4), "pixels_over_0.05": int((lum > 0.05).sum())}
        bpy.data.images.remove(img)
        run.log(f"{name}: brightest pixel {lum.max():.4f}, {(lum > 0.05).sum()} pixels over 0.05")
    for b, v in emit:
        b.inputs["Emission Strength"].default_value = v


def job():
    if bpy.data.filepath != BLEND:
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    yield
    os.makedirs(FOOTAGE, exist_ok=True)
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["still_cam_home"]
    run.show_in_viewport()
    screens()
    looks.use_look("dawn")
    run.setup_render("CYCLES", samples=256, quick=QUICK)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    yield
    if "hero" in STAGES:
        yield from stage_hero()
    if "top" in STAGES:
        yield from stage_top()
    if "leak" in STAGES:
        yield from stage_leak()
    REPORT["total_s"] = round(time.time() - T0)
    with open(os.path.join(FOOTAGE, "stills-report.json"), "w") as f:
        json.dump(REPORT, f, indent=2)
    run.log(f"stills done in {REPORT['total_s']} s: {FOOTAGE}")
    yield
    if "--stay" not in ARGS:
        bpy.ops.wm.quit_blender()


run.drive(job())
