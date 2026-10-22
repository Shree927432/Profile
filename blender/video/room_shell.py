"""Footage for Phase 4 Step 1, the room shell: the build sequence from several cameras, a dawn
shot of the finished shell, and Cycles stills from the hero camera.

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/video/room_shell.py
    (add -b after Blender for headless; options after `--`, see below)

Opens blender/out/room.blend (run blender/build.py first). Event times come from
blender/video/timing_room_shell.json (bars and beats on the placeholder Presto grid; later
the owner's MIDI beat map), never from this file. Parts land with eased, staggered motion
and a small overshoot; nothing appears in one frame. All cameras watch the same animation.

Options: a stage list (default stills,storm,dawn), `--cams=hero,low` to limit cameras,
`--quick` (half size, few samples, every 10th frame, no MP4), `--test` (a few EEVEE frames
of each camera as PNGs, to check light and framing).

Output: video-local/footage/2026-10-22-room-shell/
    room-shell-<camera>-storm.mp4   hero, low, orbit, top, detail (30 fps, 1920x1080, EEVEE 64)
    room-shell-drift-dawn.mp4       the finished shell at blue hour, a slow drift, no building
    room-shell-<look>.png           Cycles stills from the hero camera: clay, wire, bluehour
    timing_room_shell.json          the timing file these were rendered from
    room-shell-report.json          render times
Frames go to blender/out/frames/ and are deleted after each clip is encoded.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import time

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from lib import constants as C, looks, materials as M, names, run  # noqa: E402

ARGS = run.args()
STAGE = next((a for a in ARGS if not a.startswith("--")), "stills,storm,dawn")
STAGES = set(STAGE.split(","))
QUICK = "--quick" in ARGS
TEST = "--test" in ARGS
_cams = next((a for a in ARGS if a.startswith("--cams=")), None)
ONLY = set(_cams[7:].split(",")) if _cams else None
TIMING_PATH = os.path.join(HERE, "timing_room_shell.json")
T = json.load(open(TIMING_PATH))
FPS = T["fps"]
FOOTAGE = os.path.join(C.FOOTAGE, "2026-10-22-room-shell")
FRAMES = os.path.join(C.OUT, "frames")
BLEND = os.path.join(C.OUT, "room.blend")
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
REPORT = {"clips": {}, "stills": {}}
T0 = time.time()


# ---------------------------------------------------------------------------
# time: bars and beats -> seconds -> frames
# ---------------------------------------------------------------------------
G = T["grid"]
BEAT_S = G["bar_s"] / G["beats_per_bar"]
H_S = T["handles_s"]


def bar_start(bar):
    if G.get("bars"):                      # a real beat map: bar start times in seconds
        return G["bars"][bar - 1]
    return (bar - 1) * G["bar_s"]


def t_of(bar, beat=1.0):
    return H_S + bar_start(bar) + (beat - 1) * BEAT_S


def frame(t):
    return int(round(t * FPS)) + 1        # frame 1 is t = 0


LAST_BAR = max(e["bar"] for e in T["events"]) + T["tail_bars"]
END_T = t_of(LAST_BAR + 1) + H_S
FRAME_END = frame(END_T) - 1


# ---------------------------------------------------------------------------
# keyframes with per-key interpolation
# ---------------------------------------------------------------------------
_interp = {}            # (id_data name, data_path, index or -1, frame) -> (interpolation, easing, back)


def key(owner, path, frame_, value, interp="BEZIER", easing="AUTO", back=None, index=-1):
    if index >= 0:
        getattr(owner, path)[index] = value
    else:
        setattr(owner, path, value)
    owner.keyframe_insert(path, frame=frame_, index=index)
    _interp[(owner.as_pointer(), path, frame_)] = (interp, easing, back)


def _fcurves(idb):
    ad = idb.animation_data
    if ad is None or ad.action is None:
        return []
    act = ad.action
    try:
        return list(act.fcurves)
    except AttributeError:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(cb.fcurves) if cb else []


def apply_interp(owners):
    for owner in owners:
        idb = owner.id_data
        for fc in _fcurves(idb):
            path = fc.data_path.split(".")[-1]
            for kp in fc.keyframe_points:
                f = int(round(kp.co.x))
                spec = _interp.get((owner.as_pointer(), path, f))
                if spec is None:
                    continue
                kp.interpolation = spec[0]
                if spec[1] and spec[0] not in ("BEZIER", "CONSTANT", "LINEAR"):
                    kp.easing = spec[1]
                if spec[2] is not None and spec[0] == "BACK":
                    kp.back = spec[2]


# ---------------------------------------------------------------------------
# motions
# ---------------------------------------------------------------------------
def meshes_of(o):
    return [x for x in [o] + names.descendants(o) if x.type == "MESH"]


def world_bbox(objs):
    pts = [m.matrix_world @ Vector(c) for o in objs for m in meshes_of(o) for c in m.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def hide_until(objs, f0):
    for o in objs:
        for m in [o] + names.descendants(o):
            for prop in ("hide_render", "hide_viewport"):
                key(m, prop, 0, True, "CONSTANT")
                key(m, prop, f0, False, "CONSTANT")
            ANIMATED.add(m)


def scale_about(objs, f0, f1, s0, pivot_w, back):
    """Scale each object from s0 (a 3-vector) to 1 about a fixed world point, eased with
    an overshoot. Location is keyed with the same curve so the pivot stays put."""
    for o in objs:
        bpy.context.view_layer.update()
        p = o.matrix_world.inverted() @ pivot_w          # pivot in the object's own frame
        L0 = o.location.copy()
        S0 = Vector(o.scale)
        R = o.matrix_basis.to_3x3().normalized()
        s = Vector((S0.x * s0[0], S0.y * s0[1], S0.z * s0[2]))
        d = Vector(((S0.x - s.x) * p.x, (S0.y - s.y) * p.y, (S0.z - s.z) * p.z))
        key(o, "scale", f0, s, "BACK", "EASE_OUT", back)
        key(o, "location", f0, L0 + R @ d, "BACK", "EASE_OUT", back)
        key(o, "scale", f1, S0)
        key(o, "location", f1, L0)
        ANIMATED.add(o)


def parent_rot(o):
    if o.parent is None:
        return Matrix.Identity(3)
    return (o.parent.matrix_world @ o.matrix_parent_inverse).to_3x3().normalized()


def move_from(objs, f0, f1, offset_w, back):
    for o in objs:
        L0 = o.location.copy()
        off = parent_rot(o).inverted() @ Vector(offset_w)
        key(o, "location", f0, L0 + off, "BACK", "EASE_OUT", back)
        key(o, "location", f1, L0)
        ANIMATED.add(o)


def drop(objs, f0, f1, h):
    """Fall with gravity, land, a small rebound, settle."""
    land = f0 + max(2, round((f1 - f0) * 0.55))
    up = land + max(2, round((f1 - f0) * 0.18))
    for o in objs:
        L0 = o.location.copy()
        r = parent_rot(o).inverted()
        key(o, "location", f0, L0 + r @ Vector((0, 0, h)), "QUAD", "EASE_IN")
        key(o, "location", land, L0, "SINE", "EASE_OUT")
        key(o, "location", up, L0 + r @ Vector((0, 0, min(0.02, h * 0.05))), "SINE", "EASE_IN_OUT")
        key(o, "location", max(f1, up + 2), L0)
        ANIMATED.add(o)


ANIMATED = set()
SCREEN = {}


def screen_setup():
    """The screen shows the posts list (a capture of the site's own screen canvas) as
    emission only, dark until it lights up. The image is flipped on load: the screen's
    UVs put V = 0 on its top edge (MESHES.md), Blender's row 0 is the image's bottom."""
    import numpy as np
    m = bpy.data.materials["mat_monitor_screen"]
    nt = m.node_tree
    tex = nt.nodes["screen_image"]
    path = os.path.join(FOOTAGE, "posts-screen.png")
    if os.path.exists(path):
        img = bpy.data.images.load(path, check_existing=True)
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        img.pixels.foreach_set(np.ascontiguousarray(px.reshape(h, w, 4)[::-1]).ravel())
        tex.image = img
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for ln in list(b.inputs["Base Color"].links):
        nt.links.remove(ln)
    b.inputs["Base Color"].default_value = (0.005, 0.006, 0.008, 1)
    SCREEN["socket"] = b.inputs["Emission Strength"]
    SCREEN["socket"].default_value = 1.0
    SCREEN["energy"] = bpy.data.objects["lt_monitor"].data.energy


def glow(f0, f1, on=True):
    s = SCREEN["socket"]
    key(s, "default_value", 0, 0.0, "CONSTANT")
    key(s, "default_value", f0, 0.0, "SINE", "EASE_IN_OUT")
    key(s, "default_value", f1, 1.0)
    lt = bpy.data.objects["lt_monitor"].data
    key(lt, "energy", 0, 0.0, "CONSTANT")
    key(lt, "energy", f0, 0.0, "SINE", "EASE_IN_OUT")
    key(lt, "energy", f1, SCREEN["energy"])
    ANIMATED.add(s)
    ANIMATED.add(lt)


def flashes():
    """Lightning outside the window on each accented bar: one flash, quick decay. At most
    one flash in 3 s, far under the three-a-second limit."""
    lt = bpy.data.objects["lt_storm_flash"].data
    key(lt, "energy", 0, 0.0, "LINEAR")
    bar = G["first_accent_bar"]
    while bar <= max(e["bar"] for e in T["events"]):
        f = frame(t_of(bar))
        key(lt, "energy", f - 1, 0.0, "LINEAR")
        key(lt, "energy", f + 1, 2600.0, "QUAD", "EASE_OUT")
        key(lt, "energy", f + 9, 0.0, "LINEAR")
        bar += G["accent_every"]
    ANIMATED.add(lt)


def key_build():
    objs = bpy.data.objects
    D = T["defaults"]
    for ev in T["events"]:
        t0 = t_of(ev["bar"], ev.get("beat", 1))
        dur = ev.get("duration_beats", D["duration_beats"]) * BEAT_S
        stag = ev.get("stagger_beats", D["stagger_beats"]) * BEAT_S
        back = ev.get("overshoot", D["overshoot"])
        for i, unit in enumerate(ev["objects"]):
            unit = [objs[n] for n in (unit if isinstance(unit, list) else [unit])]
            f0, f1 = frame(t0 + i * stag), frame(t0 + i * stag + dur)
            mo = ev["motion"]
            if mo == "glow":
                glow(f0, f1)
                continue
            hide_until(unit, f0)
            lo, hi = world_bbox(unit)
            if mo == "rise":
                scale_about(unit, f0, f1, (1, 1, 0.001), Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)), back)
            elif mo == "grow":
                scale_about(unit, f0, f1, (0.001, 0.001, 0.001), (lo + hi) / 2, back)
            elif mo == "unfold":
                ax = "xyz".index(ev["axis"])
                piv = (lo + hi) / 2
                piv[ax] = hi[ax] if ev.get("from", "min") == "max" else lo[ax]
                s0 = [1, 1, 1]
                s0[ax] = 0.001
                # unfold along a world axis: the parts here have no rotation about Z
                scale_about(unit, f0, f1, s0, piv, back)
            elif mo == "slide":
                move_from(unit, f0, f1, ev["offset"], back)
            elif mo == "drop":
                drop(unit, f0, f1, ev.get("drop_m", D["drop_m"]))
            else:
                raise ValueError(f"unknown motion {mo}")
    flashes()
    apply_interp(ANIMATED)
    # anything built but never scheduled would sit there from frame 1: say so
    roots = [o for o in objs if o.parent is None and o.name.startswith(("obj_", "set_"))]
    loose = [m.name for r in roots for m in meshes_of(r) if m not in ANIMATED and not any(
        a in ANIMATED for a in _ancestors(m))]
    hidden = set(T.get("storm_hidden", []))
    loose = [n for n in loose if not any(n in {x.name for x in meshes_of(objs[h])} for h in hidden)]
    if loose:
        run.log(f"note: not in the timing file, visible from the start: {loose[:12]}")
    REPORT["frames"] = FRAME_END
    REPORT["seconds"] = round(FRAME_END / FPS, 2)


def _ancestors(o):
    out = []
    while o.parent is not None:
        o = o.parent
        out.append(o)
    return out


def storm_hidden(on):
    for n in T.get("storm_hidden", []):
        for m in [bpy.data.objects[n]] + names.descendants(bpy.data.objects[n]):
            m.hide_render = on
            m.hide_viewport = on


# ---------------------------------------------------------------------------
# cameras (Blender only, video_ prefix)
# ---------------------------------------------------------------------------
def build_cameras():
    coll = bpy.data.collections.new("video_cameras")
    bpy.context.scene.collection.children.link(coll)
    h = C.HERO
    mon = C.LAYOUT["monitor"]
    cams = {}
    # hero: room_view, a slow push-in toward its target over the whole sequence
    c = looks.camera("video_cam_hero", h["pos"], h["target"], vfov=h["vfov"], coll=coll)
    p0, tg = Vector(h["pos"]), Vector(h["target"])
    key(c, "location", 1, p0)
    key(c, "location", FRAME_END, p0 + (tg - p0).normalized() * 0.7)
    cams["hero"] = (c, 1, FRAME_END)
    # low wide: near the floor, front right, looking up at the back wall as it rises
    c = looks.camera("video_cam_low", (1.35, -1.55, 0.22), (-0.15, 1.2, 1.05), lens=16, coll=coll)
    key(c, "location", 1, Vector((1.35, -1.55, 0.22)))
    key(c, "location", FRAME_END, Vector((0.90, -1.70, 0.26)))
    cams["low"] = (c, 1, FRAME_END)
    # orbit: a 75 degree arc around the desk end of the room
    piv = bpy.data.objects.new("video_orbit_pivot", None)
    coll.objects.link(piv)
    piv.location = (0.1, 0.9, 0.0)
    c = looks.camera("video_cam_orbit", (0, -2.6, 1.95), (0.1, 1.1, 0.85), lens=20, coll=coll)
    c.parent = piv
    key(piv, "rotation_euler", 1, (0, 0, math.radians(-40)))
    key(piv, "rotation_euler", FRAME_END, (0, 0, math.radians(35)))
    cams["orbit"] = (c, 1, FRAME_END)
    # top-down: the plan becoming the room (the ceiling is hidden for this camera only)
    cd = bpy.data.cameras.new("video_cam_top")
    cd.sensor_fit, cd.sensor_height, cd.lens = "VERTICAL", 24, 36
    c = bpy.data.objects.new("video_cam_top", cd)
    coll.objects.link(c)
    key(c, "location", 1, Vector((0.0, 0.05, 12.5)))
    key(c, "location", FRAME_END, Vector((0.0, 0.05, 11.2)))
    key(c, "rotation_euler", 1, (0, 0, 0))
    key(c, "rotation_euler", FRAME_END, (0, 0, math.radians(6)))
    cams["top"] = (c, 1, FRAME_END)
    # detail: the monitor landing and lighting up, 85 mm at f/2
    d = T["detail"]
    t5 = t_of(d["bar"], d.get("beat", 1))
    f0, f1 = frame(t5 - d["before_s"] - H_S), frame(t5 + d["after_s"] + H_S)
    focus = (mon["x"] - mon["w"] / 2 + 0.03, mon["y"] - 0.01, mon["z"] - mon["h"] / 2 + 0.04)   # lower left corner
    c = looks.camera("video_cam_detail", (-0.78, 0.98, 0.97), focus, lens=50, coll=coll, fstop=2.0)
    key(c, "location", f0, Vector((-0.78, 0.98, 0.97)))
    key(c, "location", f1, Vector((-0.66, 1.06, 0.99)))
    cams["detail"] = (c, max(1, f0), f1)
    # dawn drift: from by the bed, looking at the window, settling on the monitor
    c = looks.camera("video_cam_dawn", (-1.0, -0.2, 1.25), (-1.35, 2.1, 1.55), lens=24, coll=coll)
    tgt = bpy.data.objects["video_cam_dawn_target"]
    n = int(round((T["dawn"]["seconds"] + 2 * H_S) * FPS))
    D0 = 2001
    key(c, "location", D0, Vector((-1.0, -0.2, 1.25)))
    key(c, "location", D0 + n - 1, Vector((-0.55, -1.25, 1.42)))
    key(tgt, "location", D0, Vector((-1.35, 2.1, 1.55)))
    key(tgt, "location", D0 + n - 1, Vector((mon["x"], mon["y"], mon["z"] - 0.02)))
    cams["drift"] = (c, D0, D0 + n - 1)
    apply_interp([o for o in coll.objects])
    return cams


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------
def encode(src_dir, f0, out):
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-framerate", str(FPS), "-start_number", str(f0),
           "-i", os.path.join(src_dir, "f%04d.jpg"), "-c:v", "libx264", "-crf", "18", "-preset", "slow",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-600:])


def render_clip(name, cam, f0, f1, look):
    scene = bpy.context.scene
    scene.camera = cam
    scene.frame_start, scene.frame_end = f0, f1
    scene.frame_step = 10 if QUICK else 1
    ceiling = bpy.data.objects["room_ceiling"]
    ceiling.visible_camera = name != "top"          # hide_render is keyed by the build
    d = os.path.join(FRAMES, f"{name}-{look}")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 92
    n = (f1 - f0) // scene.frame_step + 1
    run.log(f"clip {name}-{look}: rendering {n} frames ({(f1 - f0 + 1) / FPS:.1f} s)")
    dt = yield from run.render_to(os.path.join(d, "f"), animation=True)
    ceiling.visible_camera = True
    scene.frame_step = 1
    out = os.path.join(FOOTAGE, f"room-shell-{name}-{look}.mp4")
    if QUICK:
        run.log(f"clip {name}-{look}: {n} frames in {dt:.0f} s ({dt / n:.2f} s a frame), frames kept in {d}")
        return
    encode(d, f0, out)
    shutil.rmtree(d, ignore_errors=True)
    kb = round(os.path.getsize(out) / 1024)
    REPORT["clips"][f"{name}-{look}"] = {"path": out, "frames": n, "seconds": round(n / FPS, 2),
                                          "render_s": round(dt), "s_per_frame": round(dt / n, 2), "kb": kb}
    run.log(f"clip done: {out} ({n / FPS:.1f} s, {kb} KB, rendered in {dt / 60:.1f} min)")
    write_report()


def setup_eevee():
    run.setup_render("BLENDER_EEVEE", samples=64, quick=QUICK, fps=FPS)
    scene = bpy.context.scene
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5


def stage_storm(cams):
    looks.use_look("night")
    storm_hidden(True)
    setup_eevee()
    bpy.context.scene.view_settings.exposure = STORM_EXPOSURE
    for name in ("hero", "low", "orbit", "top", "detail"):
        if ONLY and name not in ONLY:
            continue
        c, f0, f1 = cams[name]
        yield from render_clip(name, c, f0, f1, "storm")
    bpy.context.scene.view_settings.exposure = 0.0


def stage_dawn(cams):
    if ONLY and "drift" not in ONLY:
        return
    looks.use_look("dawn")
    storm_hidden(False)
    setup_eevee()
    bpy.context.scene.view_settings.exposure = DAWN_EXPOSURE
    c, f0, f1 = cams["drift"]
    yield from render_clip("drift", c, f0, f1, "dawn")
    bpy.context.scene.view_settings.exposure = 0.0


STORM_EXPOSURE = 1.0
DAWN_EXPOSURE = 1.4
STILL_EXPOSURE = 0.6


def stage_stills():
    """Cycles, hero camera, the finished shell (before any animation is keyed)."""
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["still_cam_home"]
    looks.use_look("dawn")
    run.setup_render("CYCLES", samples=320, quick=QUICK)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    def still(label, samples):
        scene.cycles.samples = 32 if QUICK else samples
        path = os.path.join(FOOTAGE, f"room-shell-{label}.png")
        run.log(f"still {label}: rendering ({scene.cycles.samples} samples)")
        dt = yield from run.render_to(path)
        REPORT["stills"][label] = {"path": path, "render_s": round(dt)}
        run.log(f"still {label} done in {dt:.0f} s: {path}")

    scene.view_settings.exposure = STILL_EXPOSURE
    yield from still("bluehour", 320)
    looks.clay_on()
    fill = bpy.data.objects["lt_night_fill"]
    fill.hide_render = False
    yield from still("clay", 160)
    fill.hide_render = True
    looks.clay_off()
    scene.view_settings.exposure = 0.0
    undo = looks.wire_look()
    yield from still("wire", 64)
    undo()


def stage_test(cams):
    """A few EEVEE frames per camera, storm and dawn, to judge light and framing."""
    scene = bpy.context.scene
    setup_eevee()
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_percentage = 50
    scene.render.image_settings.file_format = "PNG"
    d = os.path.join(C.OUT, "test-frames")
    os.makedirs(d, exist_ok=True)
    looks.use_look("night")
    storm_hidden(True)
    scene.view_settings.exposure = STORM_EXPOSURE
    picks = {"hero": [frame(t_of(3, 2)), frame(t_of(9)), FRAME_END - 20], "low": [frame(t_of(5, 3))],
             "orbit": [frame(t_of(8))], "top": [frame(t_of(4)), frame(t_of(12))], "detail": [frame(t_of(5, 3.5))]}
    for name, fs in picks.items():
        c = cams[name][0]
        scene.camera = c
        bpy.data.objects["room_ceiling"].visible_camera = name != "top"
        for f in fs:
            scene.frame_set(f)
            dt = yield from run.render_to(os.path.join(d, f"{name}-storm-{f:04d}.png"))
            run.log(f"test {name} frame {f}: {dt:.1f} s")
    bpy.data.objects["room_ceiling"].visible_camera = True
    looks.use_look("dawn")
    storm_hidden(False)
    scene.view_settings.exposure = DAWN_EXPOSURE
    c, f0, f1 = cams["drift"]
    scene.camera = c
    for f in (f0, (f0 + f1) // 2, f1):
        scene.frame_set(f)
        dt = yield from run.render_to(os.path.join(d, f"drift-dawn-{f:04d}.png"))
        run.log(f"test drift frame {f}: {dt:.1f} s")


def write_report():
    REPORT["total_s"] = round(time.time() - T0)
    os.makedirs(FOOTAGE, exist_ok=True)
    with open(os.path.join(FOOTAGE, "room-shell-report.json"), "w") as f:
        json.dump(REPORT, f, indent=2)


def job():
    if bpy.data.filepath != BLEND:
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    yield
    os.makedirs(FOOTAGE, exist_ok=True)
    shutil.copy(TIMING_PATH, os.path.join(FOOTAGE, os.path.basename(TIMING_PATH)))
    bpy.context.scene.camera = bpy.data.objects["still_cam_home"]
    run.show_in_viewport()
    run.log(f"footage run: stages {sorted(STAGES)}; build sequence {FRAME_END} frames ({FRAME_END / FPS:.1f} s)")
    yield
    screen_setup()
    if "stills" in STAGES and not TEST:
        yield from stage_stills()
    key_build()
    cams = build_cameras()
    bpy.context.scene.frame_set(1)
    run.show_in_viewport()
    yield
    if TEST:
        yield from stage_test(cams)
    else:
        if "storm" in STAGES:
            yield from stage_storm(cams)
        if "dawn" in STAGES:
            yield from stage_dawn(cams)
    write_report()
    run.log(f"footage done in {(time.time() - T0) / 60:.1f} min")
    yield
    if "--stay" not in ARGS:
        bpy.ops.wm.quit_blender()


run.drive(job())
