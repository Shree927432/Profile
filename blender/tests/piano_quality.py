"""Piano quality test: a corner of the room, the piano and bench, lights, cameras,
stills, GLB export and the build clip. One command (see blender/README.md):

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup \\
        --python blender/tests/piano_quality.py -- [stage] [--quick]

stage: all (default) | build | stills | export | clip. `build` saves
blender/out/piano-quality.blend; the other stages open it. With the window open
(no -b) the scene appears as it is built and renders show in the render window; the
script quits Blender when done. `--quick` renders small and fast for checking.

Renders and the clip go to video-local/footage/2026-10-22-piano-quality-test/, GLBs
to blender/out/. Progress lines start with MILESTONE.
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
from lib import constants as C, geo, materials as M, names  # noqa: E402
from props import obj_piano  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = next((a for a in ARGS if not a.startswith("--")), "all")
QUICK = "--quick" in ARGS
FOOTAGE = os.path.join(C.FOOTAGE, "2026-10-22-piano-quality-test")
BLEND = os.path.join(C.OUT, "piano-quality.blend")
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FPS = 30
REPORT = {}
T0 = time.time()


def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {msg}", flush=True)


# ---------------------------------------------------------------------------
# scene: a corner of the room, lights, cameras
# ---------------------------------------------------------------------------
def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    return scene


def build_room():
    coll = bpy.data.collections.new("set_test_corner")
    bpy.context.scene.collection.children.link(coll)
    floor_m = M.oak_floor("mat_test_floor")
    wall_m = M.wall_paint("mat_test_wall")
    skirt_m = M.principled("mat_test_skirting", base=C.COL["skirting"], rough=0.4, coat=0.4, coat_rough=0.15)
    parts = []
    parts.append(geo.box("test_floor", -3.6, 3.6, -3.6, 0.06, -0.02, 0.0, collection=coll, material=floor_m,
                         smooth=False))
    parts.append(geo.box("test_wall_back", -3.6, 1.64, 0.06, 0.20, 0.0, 2.9, collection=coll, material=wall_m,
                         smooth=False))
    parts.append(geo.box("test_wall_right", 1.50, 1.64, -3.6, 0.06, 0.0, 2.9, collection=coll, material=wall_m,
                         smooth=False))
    s1 = geo.box("test_skirting_back", -3.6, 1.50, 0.045, 0.06, 0.0, 0.12, collection=coll, material=skirt_m)
    s2 = geo.box("test_skirting_right", 1.485, 1.50, -3.6, 0.045, 0.0, 0.12, collection=coll, material=skirt_m)
    for s in (s1, s2):
        geo.bevel(s, 0.004, segments=3)
    parts += [s1, s2]
    return parts


def build_lights():
    scene = bpy.context.scene
    coll = bpy.data.collections.new("lights_test")
    scene.collection.children.link(coll)
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = M.rgba(C.COL["dawn_world"])
    bg.inputs["Strength"].default_value = 0.14

    def light(name, kind, loc, **props):
        d = bpy.data.lights.new(name, kind)
        o = bpy.data.objects.new(name, d)
        coll.objects.link(o)
        o.location = loc
        for k, v in props.items():
            setattr(d, k, v)
        return o

    def aim(o, target):
        t = bpy.data.objects.new(o.name + "_target", None)
        coll.objects.link(t)
        t.location = target
        c = o.constraints.new("TRACK_TO")
        c.target, c.track_axis, c.up_axis = t, "TRACK_NEGATIVE_Z", "UP_Y"

    # the window, out of frame to the left: deep blue, large and soft (5:40 a.m.)
    sky = light("lt_dawn_sky", "AREA", (-2.9, -1.5, 1.9), shape="RECTANGLE", size=1.5, size_y=2.0,
                energy=300, color=M.srgb(C.COL["dawn_sky"]))
    aim(sky, (0.1, -0.2, 0.85))
    # one small warm lamp so the lacquer shows a highlight
    light("lt_lamp", "POINT", (1.42, -1.6, 1.28), energy=24, color=M.srgb(C.COL["lamp_warm"]),
          shadow_soft_size=0.07)
    return coll


def camera(name, loc, target, lens=35, fstop=None):
    scene = bpy.context.scene
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cam = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(cam)
    cam.location = loc
    t = bpy.data.objects.new(name + "_target", None)
    scene.collection.objects.link(t)
    t.location = target
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = t, "TRACK_NEGATIVE_Z", "UP_Y"
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_object = t
    return cam


def build_cameras():
    cams = {
        "hero": camera("still_cam_hero", (-2.30, -2.75, 1.35), (0.10, -0.35, 0.68), lens=35),
        "keys": camera("still_cam_keys", (0.42, -1.00, 0.98), (0.02, -0.50, 0.745), lens=60, fstop=2.0),
        "inside": camera("still_cam_inside", (0.70, -1.40, 2.00), (0.0, -0.12, 1.08), lens=40),
    }
    return cams


def setup_render(engine="CYCLES", samples=320):
    scene = bpy.context.scene
    scene.render.engine = engine
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = 50 if QUICK else 100
    scene.render.fps = FPS
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0
    if engine == "CYCLES":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
        scene.cycles.device = "GPU"
        scene.cycles.samples = 48 if QUICK else samples
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.max_bounces = 8
        scene.cycles.glossy_bounces = 6
        scene.cycles.caustics_reflective = False
        scene.cycles.caustics_refractive = False
    else:
        ev = scene.eevee
        ev.taa_render_samples = 8 if QUICK else 32
        try:
            ev.use_raytracing = True
            ev.use_shadows = True
        except AttributeError:
            pass


# ---------------------------------------------------------------------------
# windowed driving: a generator yields between steps so the window redraws;
# renders are started with INVOKE_DEFAULT and polled until the job ends
# ---------------------------------------------------------------------------
def _window():
    wm = bpy.data.window_managers[0]
    return wm.windows[0] if wm.windows else None


def show_in_viewport():
    """Material preview through the scene camera, so the owner can watch."""
    win = _window()
    if win is None:
        return
    for area in win.screen.areas:
        if area.type == "VIEW_3D":
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type = "MATERIAL"
                    sp.overlay.show_overlays = False
                    sp.region_3d.view_perspective = "CAMERA"
            area.tag_redraw()


def render_to(path, animation=False):
    """Yield-driven render. Caller must `yield from render_to(...)`."""
    scene = bpy.context.scene
    scene.render.filepath = path
    t = time.time()
    win = _window()
    if bpy.app.background or win is None:
        bpy.ops.render.render(write_still=not animation, animation=animation)
    else:
        with bpy.context.temp_override(window=win, screen=win.screen):
            bpy.ops.render.render("INVOKE_DEFAULT", write_still=not animation, animation=animation)
        yield "wait"
        yield "wait"
        while bpy.app.is_job_running("RENDER"):
            yield "wait"
    return time.time() - t


def drive(gen):
    """Run the job generator: synchronously when headless, from a timer when windowed."""
    if bpy.app.background or _window() is None:
        for _ in gen:
            pass
        return

    def tick():
        try:
            r = next(gen)
        except StopIteration:
            return None
        except Exception:
            import traceback
            traceback.print_exc()
            log("FAILED, see the traceback above; Blender stays open")
            return None
        return 0.4 if r == "wait" else 0.02
    bpy.app.timers.register(tick, first_interval=0.5, persistent=True)


# ---------------------------------------------------------------------------
# stages
# ---------------------------------------------------------------------------
def stage_build():
    log("build: scene")
    clear_scene()
    build_room()
    build_lights()
    build_cameras()
    bpy.context.scene.camera = bpy.data.objects["still_cam_hero"]
    show_in_viewport()
    yield
    t = time.time()
    gen = obj_piano.build_steps()
    try:
        while True:
            label = next(gen)
            log(f"build: {label}")
            yield
    except StopIteration:
        pass
    REPORT["build_s"] = round(time.time() - t, 1)
    os.makedirs(C.OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    log(f"model built in {REPORT['build_s']} s and saved: {BLEND}")
    yield


def open_blend():
    if bpy.data.filepath != BLEND:
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    bpy.context.scene.camera = bpy.data.objects["still_cam_hero"]


def _piano_meshes():
    root = bpy.data.objects["obj_piano"]
    return [o for o in root.children if o.type == "MESH"]


def stage_stills():
    os.makedirs(FOOTAGE, exist_ok=True)
    scene = bpy.context.scene
    objs = bpy.data.objects
    setup_render("CYCLES")
    times = REPORT.setdefault("stills_s", {})

    def still(name, cam, samples):
        scene.camera = objs[cam]
        scene.cycles.samples = 48 if QUICK else samples
        path = os.path.join(FOOTAGE, f"piano-{name}.png")
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGB"
        log(f"still {name}: rendering ({scene.cycles.samples} samples)")
        dt = yield from render_to(path)
        times[name] = round(dt)
        log(f"still {name} rendered in {round(dt)} s: {path}")

    yield from still("hero", "still_cam_hero", 320)
    yield from still("keys", "still_cam_keys", 384)
    lid = objs["piano_lid"]
    lid.rotation_euler.x = math.radians(-C.PIANO["lid_open_deg"])
    yield from still("inside", "still_cam_inside", 320)
    lid.rotation_euler.x = 0.0
    # clay: one grey material over everything
    bpy.context.view_layer.material_override = M.clay()
    yield from still("clay", "still_cam_hero", 160)
    bpy.context.view_layer.material_override = None
    # wireframe: glowing lines on navy, EEVEE
    undo = wire_look()
    setup_render("BLENDER_EEVEE")
    scene.camera = objs["still_cam_hero"]
    path = os.path.join(FOOTAGE, "piano-wire.png")
    log("still wire: rendering")
    dt = yield from render_to(path)
    times["wire"] = round(dt)
    log(f"still wire rendered in {round(dt)} s: {path}")
    undo()
    setup_render("CYCLES")


def wire_look(thickness=0.004):
    """Glowing blue wireframe on dark navy. Returns an undo()."""
    scene = bpy.context.scene
    vl = bpy.context.view_layer
    hidden, wires, bevels = [], [], []
    for o in bpy.data.objects:
        if o.type == "LIGHT" or o.name.startswith("test_"):
            if not o.hide_render:
                o.hide_render = True
                hidden.append(o)
        elif o.type == "MESH":
            for m in o.modifiers:
                if m.type == "BEVEL" and m.width < 0.003 and m.show_render:
                    m.show_render = False
                    m.show_viewport = False
                    bevels.append(m)
            w = o.modifiers.new("wire", "WIREFRAME")
            fine = o.name.startswith("piano_key_") or o.name in ("piano_interior", "piano_strings", "piano_hammers")
            w.thickness = thickness * (0.4 if fine else 1.0)
            w.use_replace = True
            wires.append((o, w))
    glow = M.emission("mat_look_wire", "#9fd0ff", 3.0)
    vl.material_override = glow
    bg = scene.world.node_tree.nodes["Background"]
    old_col, old_str = tuple(bg.inputs["Color"].default_value), bg.inputs["Strength"].default_value
    bg.inputs["Color"].default_value = M.rgba("#0d1626")
    bg.inputs["Strength"].default_value = 1.0

    def undo():
        for o in hidden:
            o.hide_render = False
        for o, w in wires:
            o.modifiers.remove(w)
        for m in bevels:
            m.show_render = True
            m.show_viewport = True
        vl.material_override = None
        bg.inputs["Color"].default_value = old_col
        bg.inputs["Strength"].default_value = old_str
    return undo


def glb_stats(path):
    import struct
    with open(path, "rb") as f:
        magic, version, length = struct.unpack("<III", f.read(12))
        clen, ctype = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(clen))
    acc = doc["accessors"]
    per = {m["name"]: sum(acc[p["indices"]]["count"] // 3 for p in m["primitives"] if "indices" in p)
           for m in doc["meshes"]}
    tris = sum(per.values())
    keys = sum(v for k, v in per.items() if k.startswith("piano_key_"))
    top = sorted(((v, k) for k, v in per.items() if not k.startswith("piano_key_")), reverse=True)[:8]
    return {"bytes": os.path.getsize(path), "kb": round(os.path.getsize(path) / 1024),
            "meshes": len(doc["meshes"]), "nodes": len(doc["nodes"]), "triangles": tris,
            "materials": len(doc.get("materials", [])), "images": len(doc.get("images", [])),
            "keys_triangles": keys, "biggest": [f"{k} {v}" for v, k in top]}


def stage_export():
    root = bpy.data.objects["obj_piano"]
    os.makedirs(C.OUT, exist_ok=True)
    export, undo = obj_piano.export_prep(root)
    REPORT["names"] = names.check_export(root, multi_material_ok=("piano_static",))
    for o in bpy.data.objects:
        o.select_set(False)
    for o in export:
        o.select_set(True)
    out = {}
    for variant, lite in (("rich", False), ("lite", True)):
        if lite:
            toggled = []
            for o in export:
                if o.type == "MESH" and (o.name.startswith("piano_key_") or o.name in ("piano_hammers", "piano_static")):
                    for m in o.modifiers:
                        if m.type == "BEVEL" and m.width <= 0.004 and m.show_viewport:
                            m.show_viewport = False
                            toggled.append(m)
        path = os.path.join(C.OUT, f"obj_piano-{variant}.glb")
        kw = dict(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                  export_cameras=False, export_lights=False, export_extras=False, export_image_format="AUTO")
        try:
            bpy.ops.export_scene.gltf(**kw, export_vertex_color="MATERIAL")
        except TypeError:
            bpy.ops.export_scene.gltf(**kw)
        out[variant] = glb_stats(path)
        out[variant]["path"] = path
        if lite:
            for m in toggled:
                m.show_viewport = True
    undo()
    REPORT["glb"] = out
    log(f"GLB rich: {out['rich']['kb']} KB, {out['rich']['triangles']} tris, {out['rich']['meshes']} meshes; "
        f"lite: {out['lite']['kb']} KB, {out['lite']['triangles']} tris")
    yield


# ---------------------------------------------------------------------------
# the build clip: parts appear in build order, keys sweep, fallboard folds open
# ---------------------------------------------------------------------------
CLIP_END = 390
LOOKS = {"wire": (1, 165), "clay": (135, 285), "final": (255, CLIP_END)}   # 30-frame crossfades


def clip_schedule():
    """[(start frame, [object names])] from obj_piano.BUILD_ORDER."""
    order = obj_piano.BUILD_ORDER
    if not order:   # the stage was opened from the .blend: rebuild the order from names
        groups = {}
        for o in bpy.data.objects["obj_piano"].children:
            if o.type != "MESH":
                continue
            n = o.name
            if n.startswith("piano_key_"):
                g = "keys"
            elif n.startswith("piano_bench"):
                g = "bench"
            elif n in ("piano_side_l", "piano_side_r", "piano_back", "piano_bottom"):
                g = "shell"
            elif n == "piano_crown":
                g = "crown"
            elif n in ("piano_panel_upper", "piano_panel_lower", "piano_toe_rail"):
                g = "panels"
            elif n.startswith(("piano_toe_", "piano_console")):
                g = "toes"
            elif n in ("piano_keybed", "piano_cheek_l", "piano_cheek_r", "piano_slip"):
                g = "keybed"
            elif n.startswith("piano_field") or n == "piano_rest":
                g = "fields"
            elif n == "piano_lid" or n.startswith("piano_hinge"):
                g = "lid"
            elif n.startswith("piano_pedal"):
                g = "pedals"
            elif n.startswith(("piano_cup", "piano_castor")):
                g = "castors"
            elif n in ("piano_felt", "piano_key_rail"):
                g = "felt"
            else:
                g = {"piano_interior": "interior", "piano_strings": "strings", "piano_hammers": "hammers",
                     "piano_sheet": "sheet", "piano_fallboard": "fallboard"}[n]
            groups.setdefault(g, []).append(n)
        order = [(g, groups[g]) for g in ("shell", "crown", "panels", "toes", "keybed", "fields", "lid", "pedals",
                                          "castors", "felt", "interior", "strings", "hammers", "keys", "sheet",
                                          "fallboard", "bench") if g in groups]
    starts = {"shell": 6, "crown": 16, "panels": 24, "toes": 36, "keybed": 46, "fields": 56, "lid": 64,
              "pedals": 74, "castors": 82, "felt": 88, "interior": 94, "strings": 100, "hammers": 106,
              "keys": 112, "sheet": 240, "fallboard": 250, "bench": 300}
    sched = []
    for label, objs_ in order:
        f0 = starts[label]
        if label == "keys":
            keys = sorted(objs_, key=lambda n: names_midi(n))
            for i, n in enumerate(keys):
                sched.append((f0 + round(i * 118 / 87), [n]))
        elif label in ("panels", "toes", "pedals", "bench"):
            for i, n in enumerate(objs_):
                sched.append((f0 + i * 2, [n]))
        else:
            sched.append((f0, objs_))
    return sched


def names_midi(n):
    import re
    m = re.match(r"piano_key_([a-z]+)(\d)$", n)
    return C.NOTE_NAMES.index(m.group(1)) + 12 * (int(m.group(2)) + 1)


def key_clip():
    scene = bpy.context.scene
    objs = bpy.data.objects
    for start, nms in clip_schedule():
        for n in nms:
            o = objs[n]
            o.scale = (0, 0, 0)
            o.keyframe_insert("scale", frame=start)
            o.scale = (1.08, 1.08, 1.08)
            o.keyframe_insert("scale", frame=start + 5)
            o.scale = (1, 1, 1)
            o.keyframe_insert("scale", frame=start + 8)
    fb = objs["piano_fallboard"]
    for f, deg in ((1, 0), (278, 0), (306, -C.PIANO["fall_open_deg"])):
        fb.rotation_euler.x = math.radians(deg)
        fb.keyframe_insert("rotation_euler", frame=f)
    for n in ("piano_key_c4", "piano_key_e4", "piano_key_g4"):
        o = objs[n]
        for f, deg in ((330, 0), (334, 3.0), (352, 3.0), (358, 0)):
            o.rotation_euler.x = math.radians(deg)
            o.keyframe_insert("rotation_euler", frame=f)
    # camera: push in from a wide three-quarter to the hero framing
    target = bpy.data.objects.new("video_cam_build_target", None)
    scene.collection.objects.link(target)
    target.location = (0.05, -0.35, 0.80)
    pivot = bpy.data.objects.new("video_cam_build_pivot", None)
    scene.collection.objects.link(pivot)
    pivot.location = target.location
    cd = bpy.data.cameras.new("video_cam_build")
    cd.lens = 35
    cam = bpy.data.objects.new("video_cam_build", cd)
    scene.collection.objects.link(cam)
    cam.parent = pivot
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
    for f, ang, dist, h in ((1, -44, 4.7, 1.6), (CLIP_END, -22, 2.8, 0.95)):
        pivot.rotation_euler = (0, 0, math.radians(ang))
        pivot.keyframe_insert("rotation_euler", frame=f)
        cam.location = (0, -dist, h)
        cam.keyframe_insert("location", frame=f)
    scene.camera = cam
    scene.frame_start, scene.frame_end = 1, CLIP_END


def stage_clip():
    scene = bpy.context.scene
    os.makedirs(FOOTAGE, exist_ok=True)
    key_clip()
    setup_render("BLENDER_EEVEE")
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 92
    frames_dir = os.path.join(C.OUT, "clip-frames")
    times = REPORT.setdefault("clip_s", {})
    log("build clip started: three looks in EEVEE")
    for look, (f0, f1) in LOOKS.items():
        d = os.path.join(frames_dir, look)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        scene.frame_start, scene.frame_end = f0, f1
        scene.frame_step = 15 if QUICK else 1
        undo = None
        if look == "wire":
            undo = wire_look()
        elif look == "clay":
            bpy.context.view_layer.material_override = M.clay()
        dt = yield from render_to(os.path.join(d, "f"), animation=True)
        if undo:
            undo()
        bpy.context.view_layer.material_override = None
        times[look] = round(dt)
        log(f"clip look {look}: {f1 - f0 + 1} frames in {round(dt)} s")
    scene.frame_step = 1
    if QUICK:
        log("quick mode: frames left in " + frames_dir)
        return
    out = os.path.join(FOOTAGE, "piano-build.mp4")
    w0, c0, f0 = LOOKS["wire"][0], LOOKS["clay"][0], LOOKS["final"][0]
    off1 = (c0 - w0) / FPS
    off2 = (f0 - w0) / FPS
    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-framerate", str(FPS), "-start_number", str(w0), "-i", os.path.join(frames_dir, "wire", "f%04d.jpg"),
           "-framerate", str(FPS), "-start_number", str(c0), "-i", os.path.join(frames_dir, "clay", "f%04d.jpg"),
           "-framerate", str(FPS), "-start_number", str(f0), "-i", os.path.join(frames_dir, "final", "f%04d.jpg"),
           "-filter_complex",
           f"[0][1]xfade=transition=fade:duration=1:offset={off1:.4f}[a];"
           f"[a][2]xfade=transition=fade:duration=1:offset={off2:.4f},format=yuv420p[v]",
           "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log("ffmpeg failed: " + r.stderr[-600:])
    else:
        shutil.rmtree(frames_dir, ignore_errors=True)
        REPORT["clip"] = {"path": out, "kb": round(os.path.getsize(out) / 1024), "seconds": CLIP_END / FPS}
        log(f"build clip done: {out} ({REPORT['clip']['kb']} KB, {CLIP_END / FPS:.1f} s)")
    yield


def write_report():
    REPORT["total_s"] = round(time.time() - T0)
    REPORT["stage"] = STAGE
    REPORT["quick"] = QUICK
    os.makedirs(FOOTAGE, exist_ok=True)
    with open(os.path.join(FOOTAGE, "piano-quality-report.json"), "w") as f:
        json.dump(REPORT, f, indent=2)
    print(json.dumps(REPORT, indent=2), flush=True)


def job():
    if STAGE in ("all", "build"):
        yield from stage_build()
    else:
        open_blend()
        show_in_viewport()
        yield
    if STAGE in ("all", "stills"):
        yield from stage_stills()
    if STAGE in ("all", "export"):
        yield from stage_export()
    if STAGE in ("all", "clip"):
        yield from stage_clip()
    write_report()
    log(f"done: stage {STAGE} in {REPORT['total_s']} s, quitting Blender")
    yield
    bpy.ops.wm.quit_blender()


drive(job())
