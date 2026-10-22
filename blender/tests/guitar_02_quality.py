"""guitar_02 quality test: the Woodstock Strat on a plain wall at the room's blue-hour light
plus one warm lamp. Stills, rich and lite GLBs, one quick build preview. One command:

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup \\
        --python blender/tests/guitar_02_quality.py -- [stage] [--quick] [--stills=hero,front]

stage: all (default: build,stills,export,preview) | build | stills | export | preview | room,
or several joined with commas. `build` saves blender/out/guitar-02-quality.blend; the other
stages open it. `room` opens blender/out/room.blend (run blender/build.py first) and renders
the guitar on its wall from the hero camera (room_view). With the window open (no -b) the
scene shows as it is built and the renders show in the render window. `--quick` renders
small and fast for checking.

Renders, the preview and the report go to video-local/footage/2026-10-23-guitar-02/, the
GLBs to blender/out/. Progress lines start with MILESTONE.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from lib import constants as C, geo, looks, materials as M, run  # noqa: E402
from props import guitar_02 as G2  # noqa: E402

ARGS = run.args()
STAGE = next((a for a in ARGS if not a.startswith("--")), "all")
STAGES = {"build", "stills", "export", "preview"} if STAGE == "all" else set(STAGE.split(","))
QUICK = "--quick" in ARGS
_only = next((a for a in ARGS if a.startswith("--stills=")), None)
STILLS = set(_only[len("--stills="):].split(",")) if _only else None
FOOTAGE = os.path.join(C.FOOTAGE, "2026-10-23-guitar-02")
BLEND = os.path.join(C.OUT, "guitar-02-quality.blend")
REPORT_PATH = os.path.join(FOOTAGE, "guitar-02-quality-report.json" if not QUICK else "guitar-02-quick-report.json")
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FPS = 30
TAIL_Z = 0.95                       # the body's tail above the floor in the test
REPORT = {}
T0 = time.time()
log = run.log


def out_path(name):
    return os.path.join(FOOTAGE, f"guitar-02-{name}{'-quick' if QUICK else ''}.png")


# ---------------------------------------------------------------------------
# scene
# ---------------------------------------------------------------------------
def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    return scene


def wall_y():
    """The wall's face: as far behind the guitar as the room's hanger puts it."""
    return (G2.PIV[2] + G2.G["body_t"] / 2) * C.MM + C.WALL_GUITARS["off_wall"]


def build_room():
    coll = bpy.data.collections.new("set_test_wall")
    bpy.context.scene.collection.children.link(coll)
    wy = wall_y()
    floor_m = M.oak_floor("mat_test_floor")
    wall_m = M.wall_paint("mat_test_wall")
    skirt_m = M.principled("mat_test_skirting", base=C.COL["skirting"], rough=0.4, coat=0.4, coat_rough=0.15)
    geo.box("test_floor", -3.0, 3.0, -4.0, wy + 0.2, -0.02, 0.0, collection=coll, material=floor_m, smooth=False)
    geo.box("test_wall", -3.0, 3.0, wy, wy + 0.2, 0.0, 3.0, collection=coll, material=wall_m, smooth=False)
    s = geo.box("test_skirting", -3.0, 3.0, wy - 0.012, wy, 0.0, C.ROOM["skirting_h"], collection=coll,
                material=skirt_m)
    geo.bevel(s, 0.003, segments=2)
    return coll


def build_lights():
    scene = bpy.context.scene
    coll = bpy.data.collections.new("lights_test")
    scene.collection.children.link(coll)
    try:
        scene.world.use_nodes = True
    except AttributeError:
        pass
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = M.rgba(C.COL["dawn_world"])
    bg.inputs["Strength"].default_value = 0.16

    def light(name, kind, loc, target=None, **props):
        d = bpy.data.lights.new(name, kind)
        o = bpy.data.objects.new(name, d)
        coll.objects.link(o)
        o.location = loc
        for k, v in props.items():
            setattr(d, k, v)
        if target:
            t = bpy.data.objects.new(name + "_target", None)
            coll.objects.link(t)
            t.location = target
            c = o.constraints.new("TRACK_TO")
            c.target, c.track_axis, c.up_axis = t, "TRACK_NEGATIVE_Z", "UP_Y"
        return o

    # the window, out of frame to the left: blue hour, large and soft
    light("lt_dawn_sky", "AREA", (-2.4, -1.3, 1.9), (0.0, 0.0, 1.35), shape="RECTANGLE", size=1.4, size_y=1.9,
          energy=320, color=M.srgb(C.COL["dawn_sky"]))
    # one warm lamp, front right, low: the highlight on the lacquer and the metal
    light("lt_lamp", "POINT", (1.05, -1.05, 1.22), energy=22, color=M.srgb(C.COL["lamp_warm"]),
          shadow_soft_size=0.06)
    # room bounce from the ceiling (the room has walls on every side; the test has one)
    light("lt_bounce", "AREA", (0.2, -1.6, 2.9), (0.0, 0.0, 1.3), shape="RECTANGLE", size=2.2, size_y=1.6,
          energy=45, color=M.srgb("#a9b8dc"))
    return coll


def W(u, v, z):
    return bpy.data.objects["guitar_02"].matrix_world @ G2.S(u, v, z)


def build_cameras():
    coll = bpy.data.collections.new("still_cameras")
    bpy.context.scene.collection.children.link(coll)
    VN, VS = G2.VN, G2.VS
    head = W(-6, VN + 100, 0)
    bridge = W(2, VS + 40, 6)
    cams = dict(
        hero=looks.camera("still_cam_hero", (-1.05, -2.05, 1.22), (0.02, 0.0, 1.44), lens=42, coll=coll),
        front=looks.camera("still_cam_front", (0.0, -2.85, 1.45), (0.0, 0.0, 1.45), lens=40, coll=coll),
        head=looks.camera("still_cam_head", tuple(head + __import__("mathutils").Vector((-0.21, -0.48, 0.05))),
                          tuple(head), lens=50, fstop=11, coll=coll),
        bridge=looks.camera("still_cam_bridge", tuple(bridge + __import__("mathutils").Vector((0.20, -0.30, 0.21))),
                            tuple(bridge), lens=55, fstop=2.8, coll=coll),
        back=looks.camera("still_cam_back", (1.05, -2.05, 1.22), (-0.02, 0.0, 1.44), lens=42, coll=coll),
    )
    return cams


def stage_build():
    log("build: test wall, lights, guitar_02")
    clear_scene()
    build_room()
    build_lights()
    yield
    t = time.time()
    coll = bpy.data.collections.new("obj_guitars")
    bpy.context.scene.collection.children.link(coll)
    gen = G2.build_steps(collection=coll)
    root = None
    try:
        while True:
            label = next(gen)
            if root is None and "guitar_02" in bpy.data.objects:
                root = bpy.data.objects["guitar_02"]
                root.location = (0.0, 0.0, TAIL_Z + G2.PIV[1] * C.MM)
                bpy.context.view_layer.update()
                if not bpy.data.objects.get("still_cam_hero"):
                    build_cameras()
                    bpy.context.scene.camera = bpy.data.objects["still_cam_hero"]
                    run.show_in_viewport()
            log(f"build: {label}")
            yield
    except StopIteration as s:
        root = s.value
    G2.build_hanger(root, coll, None, name="test_hanger")
    REPORT["build_s"] = round(time.time() - t, 1)
    REPORT["check"] = G2.check(root)
    REPORT["build_order"] = G2.BUILD_ORDER
    os.makedirs(C.OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    log(f"model built in {REPORT['build_s']} s, {REPORT['check']['parts']} parts, "
        f"{REPORT['check']['triangles_before_bevels']} triangles before bevels; saved {BLEND}")
    yield


def open_blend():
    if bpy.data.filepath != BLEND:
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    bpy.context.scene.camera = bpy.data.objects["still_cam_hero"]


def rendered_triangles():
    dg = bpy.context.evaluated_depsgraph_get()
    tot = 0
    for o in [bpy.data.objects["guitar_02"]] + list(bpy.data.objects["guitar_02"].children):
        if o.type == "MESH":
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            tot += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
    return tot


# ---------------------------------------------------------------------------
# stills
# ---------------------------------------------------------------------------
def stage_stills():
    os.makedirs(FOOTAGE, exist_ok=True)
    scene = bpy.context.scene
    objs = bpy.data.objects
    run.setup_render("CYCLES", quick=QUICK)
    scene.cycles.glossy_bounces = 6
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    times = REPORT.setdefault("stills_s", {})
    REPORT["rendered_triangles"] = rendered_triangles()

    def still(name, cam, samples):
        if STILLS is not None and name not in STILLS:
            return
        scene.camera = objs[cam]
        scene.cycles.samples = 32 if QUICK else samples
        path = out_path(name)
        log(f"still {name}: rendering ({scene.cycles.samples} samples)")
        dt = yield from run.render_to(path)
        times[name] = round(dt)
        log(f"still {name} rendered in {round(dt)} s: {path}")

    yield from still("hero", "still_cam_hero", 320)
    yield from still("front", "still_cam_front", 256)
    yield from still("headstock", "still_cam_head", 320)
    yield from still("bridge", "still_cam_bridge", 384)
    # the back: turned half round on its pivot, as if lifted off the hook
    root = objs["guitar_02"]
    hanger = objs.get("test_hanger")
    root.rotation_euler.z = math.pi
    if hanger:
        hanger.hide_render = True
    yield from still("back", "still_cam_back", 256)
    root.rotation_euler.z = 0.0
    if hanger:
        hanger.hide_render = False
    looks.clay_on()
    yield from still("clay", "still_cam_hero", 160)
    looks.clay_off()
    if STILLS is not None and "wire" not in STILLS:
        return
    undo = looks.wire_look(thickness=0.0003, skip={o.name for o in objs if o.name.startswith("test_")})
    run.setup_render("BLENDER_EEVEE", quick=QUICK, samples=64)
    scene.camera = objs["still_cam_hero"]
    path = out_path("wire")
    log("still wire: rendering (EEVEE)")
    dt = yield from run.render_to(path)
    times["wire"] = round(dt)
    log(f"still wire rendered in {round(dt)} s: {path}")
    undo()
    run.setup_render("CYCLES", quick=QUICK)


# ---------------------------------------------------------------------------
# exports: rich (renders) and lite (the site)
# ---------------------------------------------------------------------------
def _export(objs, path):
    for o in bpy.data.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    kw = dict(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
              export_cameras=False, export_lights=False, export_extras=False, export_image_format="AUTO")
    bpy.ops.export_scene.gltf(**kw)
    return run.glb_stats(path)


def stage_export():
    root = bpy.data.objects["guitar_02"]
    t = time.time()
    objs, undo = G2.export_rich(root)
    rich = _export(objs, os.path.join(C.OUT, "guitar_02-rich.glb"))
    undo()
    log(f"GLB rich: {rich['kb']} KB, {rich['triangles']} triangles, {rich['materials']} materials")
    yield
    objs, undo, info = G2.export_lite(root)
    lite = _export(objs, os.path.join(C.OUT, "guitar_02-lite.glb"))
    undo()
    REPORT["glb"] = {"rich": rich, "lite": lite, "lite_info": info, "export_s": round(time.time() - t, 1)}
    for k in ("rich", "lite"):
        REPORT["glb"][k]["path"] = os.path.join(C.OUT, f"guitar_02-{k}.glb")
    shutil.copy(os.path.join(C.OUT, "guitar_02_atlas.jpg"), os.path.join(FOOTAGE, "guitar-02-lite-atlas.jpg"))
    shutil.copy(os.path.join(C.OUT, "guitar_02_orm.jpg"), os.path.join(FOOTAGE, "guitar-02-lite-orm.jpg"))
    log(f"GLB lite: {lite['kb']} KB, {lite['triangles']} triangles ({info['body_triangles']} body, "
        f"{info['strings_triangles']} strings), {lite['materials']} materials, images {lite['images']}")
    yield


# ---------------------------------------------------------------------------
# the quick build preview: body, neck, hardware, pickguard, strings land in order
# ---------------------------------------------------------------------------
PREVIEW_END = 210
STARTS = {"body": 8, "neck": 34, "hardware": 62, "pickguard": 106, "strings": 152}
ORDER = {"hardware": ["tuners", "tuner_slots", "string_tree", "bridge", "saddles", "saddle_screws",
                      "saddle_springs", "arm", "arm_tip"],
         "pickguard": ["pickguard", "guard_screws", "guard_slots", "pickups", "poles", "knobs", "knob_numbers",
                       "switch_slot", "switch_lever", "switch_tip"]}


def preview_schedule():
    root = bpy.data.objects["guitar_02"]
    groups = {}
    for o in root.children:
        if o.type == "MESH":
            groups.setdefault(o.get("group", "body"), []).append(o)
    sched = []
    for g, f0 in STARTS.items():
        objs = groups.get(g, [])
        if g in ORDER:
            key = lambda o: ORDER[g].index(o.name.replace("guitar_02_part_", "")) \
                if o.name.replace("guitar_02_part_", "") in ORDER[g] else 99   # noqa: E731
            objs = sorted(objs, key=key)
            for i, o in enumerate(objs):
                sched.append((f0 + i * 4, o))
        else:
            for o in objs:
                sched.append((f0, o))
    return sched


def key_preview():
    from mathutils import Vector
    scene = bpy.context.scene
    for f0, o in preview_schedule():
        rest = o.location.copy()
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=1)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f0)
        drop = Vector((0.0, -0.22, 0.07)) if o.get("group") != "strings" else Vector((0.0, -0.10, 0.0))
        o.location = rest + drop
        o.keyframe_insert("location", frame=f0)
        o.location = rest
        o.keyframe_insert("location", frame=f0 + 12)
    cam = looks.camera("video_cam_preview", (-1.45, -2.45, 1.58), (0.0, 0.0, 1.42), lens=40)
    cam.keyframe_insert("location", frame=1)
    cam.location = (-0.92, -1.98, 1.36)
    cam.keyframe_insert("location", frame=PREVIEW_END)
    scene.camera = cam
    scene.frame_start, scene.frame_end = 1, PREVIEW_END


def stage_preview():
    scene = bpy.context.scene
    os.makedirs(FOOTAGE, exist_ok=True)
    key_preview()
    run.setup_render("BLENDER_EEVEE", quick=True, samples=16)
    scene.eevee.taa_render_samples = 16
    scene.render.resolution_percentage = 50
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    frames = os.path.join(C.OUT, "guitar02-preview-frames")
    shutil.rmtree(frames, ignore_errors=True)
    os.makedirs(frames)
    scene.frame_step = 10 if QUICK else 1
    log(f"preview: rendering {PREVIEW_END} frames, EEVEE, 960x540, 16 samples")
    dt = yield from run.render_to(os.path.join(frames, "f"), animation=True)
    scene.frame_step = 1
    REPORT["preview_s"] = round(dt)
    if QUICK:
        log(f"preview (quick) frames in {frames}")
        return
    out = os.path.join(FOOTAGE, "guitar-02-build-preview.mp4")
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(frames, "f%04d.jpg"),
           "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "20", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log("ffmpeg failed: " + r.stderr[-400:])
    else:
        shutil.rmtree(frames, ignore_errors=True)
        REPORT["preview"] = {"path": out, "kb": round(os.path.getsize(out) / 1024), "seconds": PREVIEW_END / FPS}
        log(f"preview done in {round(dt)} s: {out} ({REPORT['preview']['kb']} KB, {PREVIEW_END / FPS:.0f} s)")
    yield


# ---------------------------------------------------------------------------
# in the room, from room_view
# ---------------------------------------------------------------------------
def stage_room():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(C.OUT, "room.blend"))
    scene = bpy.context.scene
    yield
    run.setup_render("CYCLES", quick=QUICK)
    scene.cycles.glossy_bounces = 6
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    times = REPORT.setdefault("stills_s", {})
    for name, cam, samples in (("room", "still_cam_home", 256), ("room-wall", "still_cam_guitars", 256)):
        if cam not in bpy.data.objects:
            if cam == "still_cam_guitars":
                wg = C.WALL_GUITARS
                looks.camera(cam, (C.RX - 2.1, wg["y"][1] - 1.75, 1.55), (C.RX - 0.1, wg["y"][1], 2.12), lens=30)
            else:
                continue
        scene.camera = bpy.data.objects[cam]
        scene.cycles.samples = 32 if QUICK else samples
        path = out_path(name)
        log(f"still {name}: rendering ({scene.cycles.samples} samples)")
        dt = yield from run.render_to(path)
        times[name] = round(dt)
        log(f"still {name} rendered in {round(dt)} s: {path}")


def write_report():
    REPORT["total_s"] = round(time.time() - T0)
    REPORT["stage"] = STAGE
    REPORT["quick"] = QUICK
    os.makedirs(FOOTAGE, exist_ok=True)
    old = {}
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH) as f:
                old = json.load(f)
        except ValueError:
            old = {}
    for k, v in REPORT.items():
        if isinstance(v, dict) and isinstance(old.get(k), dict):
            old[k].update(v)
        else:
            old[k] = v
    with open(REPORT_PATH, "w") as f:
        json.dump(old, f, indent=2, default=str)
    print(json.dumps(REPORT, indent=2, default=str), flush=True)


def job():
    if "room" in STAGES:
        yield from stage_room()
    else:
        if "build" in STAGES:
            yield from stage_build()
        else:
            open_blend()
            run.show_in_viewport()
            yield
        if "stills" in STAGES:
            yield from stage_stills()
        if "export" in STAGES:
            yield from stage_export()
        if "preview" in STAGES:
            yield from stage_preview()
    write_report()
    log(f"done: stage {STAGE} in {REPORT['total_s']} s, quitting Blender")
    yield
    if "--stay" not in ARGS:
        bpy.ops.wm.quit_blender()


run.drive(job())
