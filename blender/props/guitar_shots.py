"""Build, stills and exports for the guitars built on 2026-11-12/13 (guitar_01, 03, 05, 06).

    Blender -b --factory-startup --python blender/props/guitar_shots.py -- <key> [stages] [--quick]

key: 01 | 03 | 05 | 06 (the module props/guitar_<key>.py: build_steps, export_rich, export_lite,
check, S(u, v, z) and its spec G). stages, comma-joined (default build,stills,export):
    build    the rich model upright in a small studio, saved to blender/out/guitar-<key>-quality.blend
    stills   front, side (treble), back, three-quarter, headstock, body close-up (Cycles on the CPU:
             the Metal device is never set under --factory-startup)
    ortho    straight front, orthographic, 0.5 mm a pixel, transparent: for the photo overlay
    export   blender/out/guitar_<key>-rich.glb and -lite.glb (+ atlas, ORM)
    richlite the body close-up of the rich model and of the lite one, same camera
Stills go to video-local/footage/2026-11-12-guitars/guitar-<key>-<name>.png, the report beside them.
"""
import importlib
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from lib import constants as C, geo, looks, materials as M, run  # noqa: E402

ARGS = run.args()
KEY = ARGS[0]
STAGES = set((ARGS[1] if len(ARGS) > 1 and not ARGS[1].startswith("--") else "build,stills,export").split(","))
QUICK = "--quick" in ARGS
GM = importlib.import_module(f"props.guitar_{KEY}")
G = GM.G
NAME = f"guitar_{KEY}"
FOOT = os.path.join(C.FOOTAGE, "2026-11-12-guitars")
BLEND = os.path.join(C.OUT, f"guitar-{KEY}-quality.blend")
REPORT_PATH = os.path.join(FOOT, f"guitar-{KEY}-report.json")
REPORT = {}
log = run.log


def root():
    return bpy.data.objects[NAME]


def W(u, v, z, r=None):
    return (r or root()).matrix_world @ GM.S(u, v, z)


def upright(r):
    """Standing on its tail edge, the front to -Y, the tail at the origin."""
    r.rotation_euler = (0, 0, 0)
    r.location = (0, 0, 0)
    bpy.context.view_layer.update()
    foot = W(0.0, 0.0, -G["body_t"] / 2, r)
    r.location = -foot
    bpy.context.view_layer.update()


def studio():
    sc = bpy.context.scene
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = M.rgba("#3a3d42")
    bg.inputs["Strength"].default_value = 0.3
    coll = bpy.data.collections.new("studio")
    sc.collection.children.link(coll)
    floor = geo.box("studio_floor", -3, 3, -3, 3, -0.02, 0.0, collection=coll,
                    material=M.principled("mat_studio_floor", base="#45484d", rough=0.6))
    wall = geo.box("studio_wall", -3, 3, 0.9, 0.92, 0.0, 3.0, collection=coll,
                   material=M.principled("mat_studio_wall", base="#55585e", rough=0.8))

    def light(name, loc, target, size, energy, col="#ffffff"):
        d = bpy.data.lights.new(name, "AREA")
        d.shape, d.size, d.energy, d.color = "RECTANGLE", size, energy, M.srgb(col)
        d.size_y = size * 1.4
        o = bpy.data.objects.new(name, d)
        coll.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    light("lt_key", (-1.4, -1.6, 1.9), (0, 0, 0.55), 1.2, 260, "#fff4e6")
    light("lt_fill", (1.6, -1.2, 1.0), (0, 0, 0.55), 1.6, 90, "#e6eeff")
    light("lt_rim", (0.6, 1.4, 2.0), (0, 0, 0.7), 0.8, 140)
    light("lt_top", (0.0, -0.4, 2.6), (0, 0, 0.6), 1.0, 70)
    return floor, wall


def cycles(samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:              # never set the Metal device in preferences under --factory-startup
        sc.cycles.device = "CPU"
    except Exception:
        pass
    sc.cycles.samples = 24 if QUICK else samples
    sc.cycles.use_denoising = True
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.max_bounces = 8
    sc.cycles.glossy_bounces = 4
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.film_transparent = False


def render(path, cam, res, samples):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 50 if QUICK else 100
    sc.cycles.samples = 24 if QUICK else samples
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    log(f"still {os.path.basename(path)} {time.time() - t:.0f} s")
    return round(time.time() - t)


def out(name):
    return os.path.join(FOOT, f"guitar-{KEY}-{name}{'-quick' if QUICK else ''}.png")


# ---------------------------------------------------------------------------
def stage_build():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    studio()
    coll = bpy.data.collections.new("obj_guitars")
    bpy.context.scene.collection.children.link(coll)
    t = time.time()
    r = GM.build(collection=coll)
    upright(r)
    REPORT["build_s"] = round(time.time() - t, 1)
    REPORT["check"] = GM.check(r)
    REPORT["build_order"] = GM.BUILD_ORDER
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    log(f"built {NAME}: {REPORT['check']}")


def open_blend():
    if bpy.data.filepath != BLEND:
        bpy.ops.wm.open_mainfile(filepath=BLEND)


def cams():
    r = root()
    upright(r)
    L = G["v_nut"] + 180
    mid = W(0, L * 0.45, 0)
    body = W(60, 260, 0)
    head = W(0, G["v_nut"] + 90, -20)
    c = {}
    fv = 2 * math.degrees(math.atan(0.66 / 3.2))
    c["front"] = looks.camera("cam_front", tuple(mid + Vector((0, -3.2, 0.0))), tuple(mid), vfov=fv)
    c["side"] = looks.camera("cam_side", tuple(mid + Vector((3.2, 0.0, 0.0))), tuple(mid), vfov=fv)
    c["back"] = looks.camera("cam_back", tuple(mid + Vector((0, 3.2, 0.0))), tuple(mid), vfov=fv)
    c["three-quarter"] = looks.camera("cam_tq", tuple(mid + Vector((1.8, -2.55, 0.5))), tuple(mid), vfov=fv)
    c["headstock"] = looks.camera("cam_head", tuple(head + Vector((-0.22, -0.42, 0.10))), tuple(head), lens=60)
    c["body"] = looks.camera("cam_body", tuple(body + Vector((0.42, -0.62, 0.30))), tuple(body), lens=55)
    nb = W(0, 250, 0)
    c["museum"] = looks.camera("cam_museum", tuple(nb + Vector((0.08, -0.80, 0.62))), tuple(W(0, 300, 0)), lens=32)
    lo = W(-120, 115, 0)
    c["lowerleft"] = looks.camera("cam_lowerleft", tuple(lo + Vector((-0.42, -0.42, 0.30))), tuple(lo), lens=50)
    c["edge"] = looks.camera("cam_edge", tuple(W(0, 470, 0) + Vector((0.55, -0.20, 0.55))), tuple(W(0, 520, 0)), lens=50)
    return c


def stage_stills():
    os.makedirs(FOOT, exist_ok=True)
    cycles(96)
    c = cams()
    times = REPORT.setdefault("stills_s", {})
    tall = (900, 1600)
    wall = bpy.data.objects.get("studio_wall")
    for name, res in (("front", tall), ("side", tall), ("back", tall), ("three-quarter", tall),
                      ("headstock", (1200, 900)), ("body", (1400, 1000)), ("edge", (1200, 900)),
                      ("museum", (1050, 1400)), ("lowerleft", (1200, 900))):
        if wall is not None:
            wall.hide_render = name == "back"
        times[name] = render(out(name), c[name], res, 96 if name not in ("headstock", "body") else 128)
    if wall is not None:
        wall.hide_render = False


def stage_ortho():
    """Straight front, orthographic, 0.5 mm a pixel, the guitar upright, transparent film."""
    sc = bpy.context.scene
    r = root()
    upright(r)
    cycles(48)
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    for n in ("studio_floor", "studio_wall"):
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = True
    hpx = 2400
    cd = bpy.data.cameras.new("cam_ortho")
    cd.type = "ORTHO"
    cd.ortho_scale = hpx * 0.0005
    cd.sensor_fit = "VERTICAL"
    cam = bpy.data.objects.new("cam_ortho", cd)
    sc.collection.objects.link(cam)
    us = [q[0] for q in G.get("body", [(0.0, 0.0)])]
    cu, cv = round((min(us) + max(us)) / 2, 1), 560.0       # the body's middle across
    p = W(cu, cv, 0)
    cam.location = (p.x, p.y - 2.0, p.z)
    cam.rotation_euler = (math.radians(90), 0, 0)
    sc.render.resolution_percentage = 100
    path = os.path.join(FOOT, f"guitar-{KEY}-ortho-front.png")
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1100, hpx
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    # where (u, v) = (0, cv) lands, and the spec point of the nut's centre, for the overlay script
    REPORT["ortho"] = {"path": path, "mm_per_px": 0.5, "size_px": [1100, hpx], "centre_uv": [cu, cv],
                       "centre_world_z_mm": round(p.z * 1000, 2)}
    for n in ("studio_floor", "studio_wall"):
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = False
    sc.render.film_transparent = False
    log(f"ortho {path}")


def _export(objs, path):
    for o in bpy.data.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_cameras=False, export_lights=False, export_extras=False,
                              export_image_format="AUTO")
    return run.glb_stats(path)


def stage_export():
    r = root()
    t = time.time()
    objs, undo = GM.export_rich(r)
    rich = _export(objs, os.path.join(C.OUT, f"{NAME}-rich.glb"))
    undo()
    log(f"rich {rich['kb']} KB {rich['triangles']} tris {rich['materials']} materials")
    objs, undo, info = GM.export_lite(r)
    lite = _export(objs, os.path.join(C.OUT, f"{NAME}-lite.glb"))
    undo()
    log(f"lite {lite['kb']} KB {lite['triangles']} tris, {info}")
    for k, d in (("rich", rich), ("lite", lite)):
        d["path"] = os.path.join(C.OUT, f"{NAME}-{k}.glb")
        d["bytes"] = os.path.getsize(d["path"])
        d.pop("node_names", None)
    REPORT["glb"] = {"rich": rich, "lite": lite, "lite_info": info, "export_s": round(time.time() - t)}


def stage_richlite():
    """The same close camera on the rich model, then on the lite one (built, baked, swapped in)."""
    cycles(128)
    c = cams()
    REPORT.setdefault("stills_s", {})["close-rich"] = render(out("close-rich"), c["body"], (1400, 1000), 128)
    r = root()
    objs, undo, info = GM.export_lite(r)
    for o in r.children:
        o.hide_render = True
    cycles(128)
    REPORT["stills_s"]["close-lite"] = render(out("close-lite"), c["body"], (1400, 1000), 128)
    undo()
    for o in r.children:
        o.hide_render = False


def write_report():
    old = {}
    if os.path.exists(REPORT_PATH):
        try:
            old = json.load(open(REPORT_PATH))
        except ValueError:
            pass
    old.update(REPORT)
    json.dump(old, open(REPORT_PATH, "w"), indent=1, default=str)


def main():
    os.makedirs(FOOT, exist_ok=True)
    if "build" in STAGES:
        stage_build()
    else:
        open_blend()
    if "stills" in STAGES:
        stage_stills()
    if "ortho" in STAGES:
        stage_ortho()
    if "richlite" in STAGES:
        stage_richlite()
    if "export" in STAGES:
        open_blend()
        stage_export()
    write_report()
    log("done")


main()
