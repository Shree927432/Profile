"""speakers: build, stills, photo compares, rich and lite GLBs. One command:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/components/speakers_render.py -- [stages] [--quick] [--stills=hero,front] [--cpu]

Always headless (-b): the owner asked on 2026-10-24 that no Blender window opens. Every stage works headless.

stages: all (default: build,stills,compare,export) or several joined with commas. `build` saves
blender/out/components/speakers.blend; the other stages open it. --compare=front,side-left limits the
compares. Then, outside Blender:

    /opt/anaconda3/bin/python3 blender/components/speakers_blueprint.py   (blueprint + compare sheets)

Stills, compare data and the report go to video-local/footage/2026-10-24-components/speakers/,
the .blend and GLBs to blender/out/components/. Progress lines start with MILESTONE.
"""
import json
import math
import os
import shutil
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from lib import constants as C, geo, looks, materials as M, names, run  # noqa: E402
import speakers as S  # noqa: E402

ARGS = run.args()
STAGE = next((a for a in ARGS if not a.startswith("--")), "all")
STAGES = {"build", "stills", "compare", "export"} if STAGE == "all" else set(STAGE.split(","))
QUICK = "--quick" in ARGS
_only = next((a for a in ARGS if a.startswith("--stills=")), None)
STILLS = set(_only[len("--stills="):].split(",")) if _only else None
_conly = next((a for a in ARGS if a.startswith("--compare=")), None)
CMP_ONLY = set(_conly[len("--compare="):].split(",")) if _conly else None
OUT = os.path.join(C.OUT, "components")
BLEND = os.path.join(OUT, "speakers.blend")
FOOTAGE = os.path.join(C.FOOTAGE, "2026-10-24-components", "speakers")
MEASURE = os.path.join(FOOTAGE, "measure")
REF = os.path.join(C.REPO, "docs", "moodboard", "local", "ai-lab", "08-studio-monitors")
REPORT_PATH = os.path.join(FOOTAGE, "speakers-report.json" if not QUICK else "speakers-quick-report.json")
REPORT = {}
T0 = time.time()
MM = S.MM
EXPOSURE = -0.6
_setup0 = run.setup_render


def _setup_look(*a, **k):
    _setup0(*a, **k)
    bpy.context.scene.view_settings.look = "AgX - High Contrast"     # deeper blacks, as the product photos
    bpy.context.scene.view_settings.exposure = EXPOSURE


run.setup_render = _setup_look
if "--cpu" in ARGS:          # fallback when the Metal device hangs (seen 2026-10-24 with other renders running)
    _setup = run.setup_render

    def _setup_cpu(*a, **k):
        _setup(*a, **k)
        bpy.context.scene.cycles.device = "CPU"
    run.setup_render = _setup_cpu
log = run.log
PARTS = [f"studio_speaker_{i:02d}{k}" for i in (1, 2) for k in ("", "_woofer", "_pole", "_iso")] + \
    ["a7v_1_brand", "a7v_2_brand"]          # the invented brand decals (2026-10-26), not in the atlas bake
from lib import renderqueue  # noqa: E402
_plain_render_to = run.render_to


def _queued_render_to(path, animation=False):
    """Every Cycles render waits for the shared GPU slot (lib/renderqueue.py); EEVEE/Workbench do not."""
    if bpy.context.scene.render.engine == "CYCLES":
        with renderqueue.slot("speakers " + os.path.basename(path)):
            return (yield from _plain_render_to(path, animation))
    return (yield from _plain_render_to(path, animation))


run.render_to = _queued_render_to
_still_dir = next((a[len("--still-dir="):] for a in ARGS if a.startswith("--still-dir=")), None)


def out_path(name):
    if _still_dir:
        return os.path.join(_still_dir, f"hero-speakers.png" if name == "hero" else f"speakers-{name}.png")
    return os.path.join(FOOTAGE, f"speakers-{name}{'-quick' if QUICK else ''}.png")


def root():
    return bpy.data.objects["speakers"]


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


def _coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def build_studio():
    """Neutral studio: soft key, fill, rim, light grey world; a white desk slab (never exported)."""
    scene = bpy.context.scene
    try:
        scene.world.use_nodes = True
    except AttributeError:
        pass
    nt = scene.world.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.34
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.40, M.rgba("#3c3f44")
    el[1].position, el[1].color = 0.62, M.rgba("#d6d9de")
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    cam_bg = nt.nodes.new("ShaderNodeBackground")
    cam_bg.name = "camera_bg"
    cam_bg.inputs["Color"].default_value = M.rgba("#dcdee2")
    cam_bg.inputs["Strength"].default_value = 1.32
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(bg.outputs[0], mix.inputs[1])
    nt.links.new(cam_bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    coll = _coll("lights_studio")

    def area(name, loc, target, size, size_y, energy, colour="#ffffff"):
        d = bpy.data.lights.new(name, "AREA")
        d.shape = "RECTANGLE"
        d.size, d.size_y, d.energy = size, size_y, energy
        d.color = M.srgb(colour)
        o = bpy.data.objects.new(name, d)
        coll.objects.link(o)
        o.location = loc
        t = bpy.data.objects.new(name + "_target", None)
        coll.objects.link(t)
        t.location = target
        c = o.constraints.new("TRACK_TO")
        c.target, c.track_axis, c.up_axis = t, "TRACK_NEGATIVE_Z", "UP_Y"
        return o
    area("lt_key", (-1.7, -1.9, 1.9), (0, 0.0, 0.5), 1.8, 1.4, 330, "#fff7ee")
    area("lt_fill", (2.0, -1.4, 0.9), (0, 0.0, 0.5), 1.6, 1.2, 90, "#eef3ff")
    area("lt_rim", (0.9, 1.9, 1.7), (0, 0.0, 0.55), 1.4, 1.0, 170, "#ffffff")
    area("lt_back", (-1.2, 1.6, 0.6), (0, 0.1, 0.4), 1.2, 0.8, 60, "#ffffff")
    # a broad soft box straight in front, as in product shots: the flat centre of the baffle mirrors it,
    # the side facets (turned 16 degrees) mirror the darker room beside it, so the facets read
    area("lt_front", (0.0, -2.6, 0.75), (0, 0.0, 0.5), 1.1, 1.1, 110, "#ffffff")
    scene.view_settings.exposure = EXPOSURE
    sc = _coll("still_set")
    desk = geo.box("still_desk", -0.9, 0.9, -0.55, 0.30, -S.DESK_T * MM, 0.0, collection=sc,
                   material=M.principled("mat_still_desk", base="#eeeeec", rough=0.35, coat=0.2, coat_rough=0.2))
    geo.bevel(desk, 0.003, segments=2)
    return coll


def build_cameras():
    coll = _coll("still_cameras")
    zc = 0.50
    cab_x = S.PAIR_X * MM
    zt = S.POLE_CAB_Z * MM + S.TW_THROAT[3] * MM
    zp = S.POLE_CAB_Z * MM + S.PLATE[3] * MM
    cams = dict(
        hero=looks.camera("still_cam_hero", (-1.55, -2.45, 1.10), (0.0, 0.0, 0.42), lens=45, coll=coll),
        front=looks.camera("still_cam_front", (0.0, -2.9, zc), (0.0, 0.0, zc), lens=50, coll=coll),
        side=looks.camera("still_cam_side", (2.9, 0.0, zc), (0.0, 0.0, zc), lens=50, coll=coll),
        back=looks.camera("still_cam_back", (1.15, 2.1, 1.05), (0.0, 0.0, 0.52), lens=50, coll=coll),
        detail=looks.camera("still_cam_detail", (-cab_x - 0.12, -0.50, zt + 0.08), (-cab_x, -0.14, zt - 0.005),
                            lens=60, fstop=8.0, coll=coll),
        woofer=looks.camera("still_cam_woofer", (-cab_x + 0.14, -0.48, zt - 0.10), (-cab_x, -0.14, zt - 0.17),
                            lens=60, fstop=8.0, coll=coll),
        rear=looks.camera("still_cam_rear", (cab_x - 0.16, 0.62, zp + 0.10), (cab_x, 0.14, zp), lens=55, fstop=8.0,
                          coll=coll),
        port=looks.camera("still_cam_port", (-cab_x + 0.02, -0.55, S.POLE_CAB_Z * MM + 0.10), (-cab_x, -0.14,
                          S.POLE_CAB_Z * MM + 0.042), lens=70, fstop=8.0, coll=coll),
        iso=looks.camera("still_cam_iso", (-1.05, -1.70, 0.62), (0.0, 0.0, 0.20), lens=50, coll=coll),
        single=looks.camera("still_cam_single", (-0.88, -1.12, 0.98), (-cab_x, 0.0, 0.69), lens=50, coll=coll),
    )
    cd = bpy.data.cameras.new("still_cam_top")
    cd.type = "ORTHO"
    cd.ortho_scale = 1.0
    top = bpy.data.objects.new("still_cam_top", cd)
    coll.objects.link(top)
    top.location = (0.0, 0.0, 2.5)
    cams["top"] = top
    cd = bpy.data.cameras.new("still_cam_top_single")
    cd.type = "ORTHO"
    cd.ortho_scale = 0.62
    ts = bpy.data.objects.new("still_cam_top_single", cd)
    coll.objects.link(ts)
    ts.location = (-cab_x, 0.0, 2.5)
    cams["top_single"] = ts
    return cams


def stage_build():
    log("build: studio, the pair of A7V, two mounts")
    clear_scene()
    build_studio()
    yield
    t = time.time()
    r = S.build()
    build_cameras()
    bpy.context.scene.camera = bpy.data.objects["still_cam_hero"]
    run.show_in_viewport()
    REPORT["build_s"] = round(time.time() - t, 1)
    REPORT["check"] = S.check(r)
    os.makedirs(OUT, exist_ok=True)
    from lib.blendfile import pack_and_save
    pack_and_save(BLEND, compress=True)
    log(f"built in {REPORT['build_s']} s: {REPORT['check']['triangles_before_bevels']} triangles; "
        f"cabinet bbox {REPORT['check']['cabinet_bbox_mm_xyz']} mm; saved {BLEND}")
    yield


def open_blend():
    if bpy.data.filepath != BLEND:
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    bpy.context.scene.camera = bpy.data.objects["still_cam_hero"]


def rendered_triangles():
    dg = bpy.context.evaluated_depsgraph_get()
    tot = 0
    for o in names.descendants(root()):
        if o.type == "MESH" and not o.hide_render:
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            tot += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
    return tot


def set_finish(finish):
    """Swap the cabinet material on both cabinets: 'white' (gloss lacquer, as the photos), 'satin', 'black'."""
    mats = S.make_materials(finish)
    me = bpy.data.objects["studio_speaker_01"].data
    for i, m in enumerate(me.materials):
        if m and (m.name.startswith("mat_speakers_white") or m.name.startswith("mat_speakers_black_paint")):
            me.materials[i] = mats["cab"]
        if m and m.name.startswith("mat_speakers_seam"):
            me.materials[i] = mats["seam"]
        if m and m.name.startswith("mat_speakers_port_tube"):
            me.materials[i] = mats["port_tube"]


def set_pole_colour(key):
    me = bpy.data.objects["studio_speaker_01_pole"].data
    for i, m in enumerate(me.materials):
        if m and m.name in ("mat_speakers_pole_white", "mat_speakers_pole_black"):
            me.materials[i] = bpy.data.materials["mat_speakers_pole_white" if key == "pole" else "mat_speakers_pole_black"]


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
        scene.cycles.samples = 24 if QUICK else samples
        path = out_path(name)
        log(f"still {name}: rendering ({scene.cycles.samples} samples)")
        dt = yield from run.render_to(path)
        times[name] = round(dt)
        log(f"still {name} rendered in {round(dt)} s: {path}")

    yield from still("hero", "still_cam_hero", 320)
    yield from still("front", "still_cam_front", 160)
    yield from still("side", "still_cam_side", 160)
    yield from still("back", "still_cam_back", 192)
    yield from still("top", "still_cam_top", 128)
    yield from still("top-single", "still_cam_top_single", 128)
    yield from still("detail", "still_cam_detail", 256)
    yield from still("detail-woofer", "still_cam_woofer", 256)
    yield from still("detail-rear", "still_cam_rear", 256)
    yield from still("detail-ports", "still_cam_port", 256)
    if STILLS is None or "woofer-raking" in STILLS:
        # the cone under a grazing light from the left, the studio lights down (as tech-woofer.png)
        dims = [(o, o.data.energy) for o in objs if o.type == "LIGHT"]
        for o, e in dims:
            o.data.energy = e * 0.15
        cab_x = S.PAIR_X * MM
        zw = S.POLE_CAB_Z * MM + S.WF_Z * MM
        ld = bpy.data.lights.new("lt_raking", "AREA")
        ld.size, ld.energy = 0.08, 6.0
        lo = bpy.data.objects.new("lt_raking", ld)
        scene.collection.objects.link(lo)
        lo.location = (-cab_x - 0.40, -0.16, zw + 0.03)
        tgt = Vector((-cab_x, -0.14, zw))
        lo.rotation_euler = (tgt - lo.location).to_track_quat("-Z", "Y").to_euler()
        yield from still("woofer-raking", "still_cam_woofer", 256)
        bpy.data.objects.remove(lo)
        for o, e in dims:
            o.data.energy = e
    if STILLS is None or "iso" in STILLS:
        S.set_mount(root(), "iso")
        yield from still("iso", "still_cam_iso", 192)
        S.set_mount(root(), "pole")
    hide2 = [bpy.data.objects[f"studio_speaker_02{k}"] for k in ("", "_woofer", "_pole")]
    for o in hide2:
        o.hide_render = True
    yield from still("single", "still_cam_single", 256)
    if STILLS is None or "option-satin" in STILLS:
        set_finish("satin")
        yield from still("option-satin", "still_cam_single", 256)
        set_finish("white")
    if STILLS is None or "option-gloss" in STILLS:
        yield from still("option-gloss", "still_cam_single", 256)
    for o in hide2:
        o.hide_render = False
    if STILLS is None or "option-pole-black" in STILLS:
        set_pole_colour("pole_black")
        yield from still("option-pole-black", "still_cam_hero", 192)
        set_pole_colour("pole")
    looks.clay_on()
    yield from still("clay", "still_cam_hero", 128)
    looks.clay_off()
    if STILLS is not None and "wire" not in STILLS:
        return
    undo = looks.wire_look(thickness=0.0003, skip={"still_desk"})
    cam_bg = scene.world.node_tree.nodes["camera_bg"]
    old_bg = tuple(cam_bg.inputs["Color"].default_value)
    cam_bg.inputs["Color"].default_value = M.rgba("#0d1626")
    old_ex = scene.view_settings.exposure
    scene.view_settings.exposure = 0.0
    run.setup_render("BLENDER_EEVEE", quick=QUICK, samples=32)
    scene.camera = objs["still_cam_single"]
    path = out_path("wire")
    log("still wire: rendering (EEVEE)")
    dt = yield from run.render_to(path)
    times["wire"] = round(dt)
    undo()
    cam_bg.inputs["Color"].default_value = old_bg
    scene.view_settings.exposure = old_ex
    run.setup_render("CYCLES", quick=QUICK)


# ---------------------------------------------------------------------------
# photo compare: fit the camera (distance, height) and the cabinet's turn to the official photo's
# silhouette, then render it there
# ---------------------------------------------------------------------------
def _load_mask(path, mode):
    import numpy as np
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[::-1]
    bpy.data.images.remove(im)
    if mode == "alpha":
        return px[..., 3] > 0.5
    if isinstance(mode, (list, tuple)):          # ("bg", level, tolerance): differs from a flat background
        return abs(px[..., :3].mean(-1) * 255 - mode[1]) > mode[2]
    return px[..., :3].mean(-1) < mode


def _bbox(m):
    import numpy as np
    ys, xs = np.nonzero(m)
    return xs.min(), xs.max(), ys.min(), ys.max()


def _warp(rend, shape, s, tx, ty):
    import numpy as np
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W]
    sx = ((xx - tx) / s).astype(int)
    sy = ((yy - ty) / s).astype(int)
    ok = (sx >= 0) & (sy >= 0) & (sx < rend.shape[1]) & (sy < rend.shape[0])
    rm = np.zeros(shape, bool)
    rm[ok] = rend[sy[ok], sx[ok]]
    return rm


def _iou(photo, rend, refine=False):
    """Scale the render's mask so its box height matches the photo's (and centre it), then IoU. With
    refine, search a few pixels and half a percent of scale around that."""
    if not rend.any():
        return 0.0, {"scale": 1.0, "tx": 0.0, "ty": 0.0}
    px0, px1, py0, py1 = _bbox(photo)
    rx0, rx1, ry0, ry1 = _bbox(rend)
    s0 = (py1 - py0) / max(1, ry1 - ry0)
    best = None
    steps = [(ds, dx, dy) for ds in (0.99, 0.995, 1.0, 1.005, 1.01) for dx in (-4, -2, 0, 2, 4)
             for dy in (-4, -2, 0, 2, 4)] if refine else [(1.0, 0, 0)]
    for ds, dx, dy in steps:
        s = s0 * ds
        cx = (px0 + px1) / 2
        rcx = (rx0 + rx1) / 2
        tx, ty = cx - rcx * s + dx, py0 - ry0 * s + dy
        rm = _warp(rend, photo.shape, s, tx, ty)
        iou = (rm & photo).sum() / max(1, (rm | photo).sum())
        if best is None or iou > best[0]:
            best = (iou, {"scale": float(s), "tx": float(tx), "ty": float(ty)})
    return best


def _rowfill(m):
    import numpy as np
    rows = np.zeros_like(m)
    cols = np.zeros_like(m)
    for y in np.nonzero(m.any(1))[0]:
        xs = np.nonzero(m[y])[0]
        rows[y, xs[0]:xs[-1] + 1] = True
    for x in np.nonzero(m.any(0))[0]:
        ys = np.nonzero(m[:, x])[0]
        cols[ys[0]:ys[-1] + 1, x] = True
    return m | (rows & cols)


def _largest(m):
    """Keep the largest connected blob (drops stray specks and text)."""
    import numpy as np
    from collections import deque
    H, W = m.shape
    lab = np.zeros((H, W), np.int32)
    best, best_n, cur = 0, 0, 0
    ys, xs = np.nonzero(m)
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0]:
            continue
        cur += 1
        q = deque([(y0, x0)])
        lab[y0, x0] = cur
        n = 0
        while q:
            y, x = q.popleft()
            n += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = cur
                    q.append((yy, xx))
        if n > best_n:
            best, best_n = cur, n
    return lab == best


def _p(name):
    return os.path.join(REF, name)


FEATURE_DARK = 0.30      # luminance below this, inside the silhouette: the woofer, the waveguide plate, the ports
# yaw: the cabinet's turn about Z (degrees; 0 = front to the camera, 90 = front to the image's right)
COMPARES = {
    "front": dict(photo=_p("black-spin-front.jpg"), mode=0.6, yaw=[0], finish="black"),
    "side-left": dict(photo=_p("black-spin-side-left.jpg"), mode=0.6, yaw=[-90], finish="black"),
    "side-right": dict(photo=_p("black-spin-side-right.jpg"), mode=0.6, yaw=[90], finish="black"),
    "back": dict(photo=_p("black-spin-back.jpg"), mode=0.6, yaw=[180], finish="black"),
    "3q-front-left": dict(photo=_p("black-spin-three-quarter-left.jpg"), mode=0.6, yaw=[20, 30, 40, 50, 60],
                          finish="black"),
    "3q-front-right": dict(photo=_p("black-spin-three-quarter-right.jpg"), mode=0.6, yaw=[-20, -30, -40, -50, -60],
                           finish="black"),
    "3q-back-left": dict(photo=_p("black-spin-back-three-quarter.jpg"), mode=0.6, yaw=[-110, -125, -140, -155],
                         finish="black"),
    "3q-back-right": dict(photo=_p("black-spin-back-three-quarter-2.jpg"), mode=0.6, yaw=[110, 125, 140, 155],
                          finish="black"),
    "front-above": dict(photo=_p("black-front-1600.png"), mode="alpha", yaw=[0], finish="black", hires=2,
                        dz=[0.05, 0.10, 0.15, 0.25, 0.35]),
    "3q-studio-right": dict(photo=_p("black-3q-right-1600.png"), mode="alpha", yaw=[-15, -22, -30, -38],
                            finish="black", dz=[0.0, 0.08, 0.16, 0.26]),
    "white-hero": dict(photo=_p("white-limited-transparent.png"), mode="alpha", yaw=[10, 16, 22, 28], finish="white", feature=True,
                       dz=[-0.30, -0.22, -0.15, -0.08], tilt=[0, 3, 6, 9]),
    "white-front": dict(photo=_p("white-front.jpg"), mode=("bg", 255, 3), hires=2, feature_w=0.25, D=(0.8, 1.0, 1.3, 2.0, 3.5), yaw=[0], finish="white", feature=True, crop=(0, 9999, 0, 991)),
    "white-back": dict(photo=_p("white-back.jpg"), mode=("bg", 255, 3), yaw=[180], finish="white", feature=True, crop=(0, 9999, 0, 991)),
    "white-3q-right": dict(photo=_p("white-three-quarter-right.jpg"), mode=("bg", 246, 3), crop=(0, 9999, 0, 984),
                           yaw=[16, 22, 28], finish="white", feature=True, feature_w=0.3, D=(0.45, 0.6, 0.8, 1.1, 1.6),
                           dz=[-0.25, -0.15, -0.05, 0.05], tilt=[-6, -2, 2, 6, 10]),
}


def _show_single():
    """Only speaker 01 (cabinet and woofer), at the origin; returns undo."""
    objs = bpy.data.objects
    keep = {"studio_speaker_01", "studio_speaker_01_woofer"}
    state = {}
    for o in names.descendants(root()) + [objs["still_desk"]]:
        state[o.name] = (o.hide_render, o.hide_viewport)
        o.hide_render = o.hide_viewport = o.name not in keep
    cab = objs["studio_speaker_01"]
    old = (cab.location.copy(), cab.rotation_euler.copy())
    cab.location = (0.0, -(S.FRONT_Y + S.BACK_Y) / 2 * MM, 0.0)

    def undo():
        for n, (a, b) in state.items():
            objs[n].hide_render, objs[n].hide_viewport = a, b
        cab.location, cab.rotation_euler = old
    return undo


def _yaw(deg):
    """Turn the cabinet about the vertical through its body's centre."""
    cab = bpy.data.objects["studio_speaker_01"]
    yc = (S.FRONT_Y + S.BACK_Y) / 2 * MM
    a = math.radians(deg)
    cab.rotation_euler = (0, 0, a)
    # the local point (0, yc) must land on the world origin
    cab.location = (-(-math.sin(a) * yc), -(math.cos(a) * yc), 0.0)


def stage_compare():
    import numpy as np
    os.makedirs(MEASURE, exist_ok=True)
    scene = bpy.context.scene
    objs = bpy.data.objects
    res = REPORT.setdefault("compare", {})
    undo = _show_single()
    zc = S.H / 2 * MM
    size = 0.8
    for name, cfg in COMPARES.items():
        if CMP_ONLY is not None and name not in CMP_ONLY:
            continue
        t0 = time.time()
        set_finish(cfg["finish"])
        raw = _load_mask(cfg["photo"], cfg["mode"])
        if cfg.get("crop"):
            x0_, x1_, y0_, y1_ = cfg["crop"]
            keep = raw.copy()
            keep[:] = False
            keep[y0_:y1_, x0_:x1_] = True
            raw &= keep
        photo = _rowfill(_largest(raw))
        H, W = photo.shape
        k = max(1, int(round(W / 640)))
        photo_s = photo[::k, ::k]
        feat = cfg.get("feature")          # also match the dark parts (woofer, waveguide plate) inside
        pdark = (_load_mask(cfg["photo"], FEATURE_DARK) & photo) if feat else None
        pdark_s = pdark[::k, ::k] if feat else None
        scene.render.engine = "BLENDER_WORKBENCH"
        sh = scene.display.shading
        sh.light, sh.color_type = "FLAT", ("MATERIAL" if feat else "SINGLE")
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.resolution_percentage = 100
        cd = bpy.data.cameras.new("still_cam_cmp")
        cam = bpy.data.objects.new("still_cam_cmp", cd)
        scene.collection.objects.link(cam)
        scene.camera = cam
        cam.rotation_euler = (math.radians(90), 0, 0)
        cd.sensor_fit = "HORIZONTAL"
        cd.clip_start = 0.01
        sil = os.path.join(MEASURE, f"sil-{name}.png")

        def place(D, dz, tilt=0.0):
            # a camera on the -Y axis, dz above the cabinet's centre, pitched up by `tilt` degrees, shifted
            # so the cabinet stays in frame
            cam.rotation_euler = (math.radians(90 + tilt), 0, 0)
            dz_eff = dz + D * math.tan(math.radians(tilt))
            cam.location = (0, -D, zc + dz)
            cd.lens = 36 * D / size
            cd.shift_y = -dz_eff / size if W >= H else -dz_eff / size * W / H
            return
            cam.location = (0, -D, zc + dz)
            cd.lens = 36 * D / size
            cd.shift_y = -dz / size if W >= H else -dz / size * W / H

        def score(target, res_k, dark=None):
            scene.render.resolution_x, scene.render.resolution_y = W // res_k, H // res_k
            scene.render.filepath = sil
            bpy.ops.render.render(write_still=True)
            rm = _load_mask(sil, "alpha")
            iou, tf = _iou(target, rm)
            if dark is None:
                return iou, tf
            rd = _load_mask(sil, FEATURE_DARK) & rm
            wd = _warp(rd, dark.shape, tf["scale"], tf["tx"], tf["ty"])
            fi = (wd & dark).sum() / max(1, (wd | dark).sum())
            fw = cfg.get("feature_w", 0.3)
            return (1 - fw) * iou + fw * fi, tf
        tries = []
        best = None
        dzs = cfg.get("dz", [0.0, 0.03, 0.06, 0.10, 0.15])
        tilts = cfg.get("tilt", [0.0])
        for yaw in cfg["yaw"]:
            _yaw(yaw)
            for D in cfg.get("D", (0.55, 0.8, 1.2, 2.0, 3.5, 6.0, 12.0)):
                for dz in dzs:
                    for tl in tilts:
                        place(D, dz, tl)
                        iou, _ = score(photo_s, k, pdark_s)
                        tries.append((round(float(iou), 4), yaw, D, dz, tl))
                        if best is None or iou > best[0]:
                            best = (iou, yaw, D, dz, tl)
                        yield
        # refine around the best
        for it in range(3):
            _, y0, D0, z0, t0_ = best
            fy = 8.0 / (2 ** it)
            for yaw in ({y0} if len(cfg["yaw"]) == 1 else {y0 - fy, y0, y0 + fy}):
                for D in (D0 * 0.8, D0, D0 * 1.25):
                    for dz in (z0 - 0.04 / (it + 1), z0, z0 + 0.04 / (it + 1)):
                        for tl in ({t0_} if len(tilts) == 1 else {t0_ - 2.0 / (it + 1), t0_, t0_ + 2.0 / (it + 1)}):
                            _yaw(yaw)
                            place(D, dz, tl)
                            iou, _ = score(photo_s, k, pdark_s)
                            tries.append((round(float(iou), 4), yaw, round(D, 3), round(dz, 3), tl))
                            if iou > best[0]:
                                best = (iou, yaw, D, dz, tl)
                            yield
        _, yaw, D, dz, tl = best
        _yaw(yaw)
        place(D, dz, tl)
        scene.render.resolution_x, scene.render.resolution_y = W, H
        scene.render.filepath = sil
        bpy.ops.render.render(write_still=True)
        rm = _load_mask(sil, "alpha")
        iou_full, tf_full = _iou(photo, rm, refine=True)
        feat_iou = None
        if feat:
            rd = _load_mask(sil, FEATURE_DARK) & rm
            wd = _warp(rd, pdark.shape, tf_full["scale"], tf_full["tx"], tf_full["ty"])
            feat_iou = round(float((wd & pdark).sum() / max(1, (wd | pdark).sum())), 4)
            _save_mask(pdark, os.path.join(MEASURE, f"dark-photo-{name}.png"))
            _save_mask(wd, os.path.join(MEASURE, f"dark-render-{name}.png"))
        run.setup_render("CYCLES", quick=QUICK)
        scene.render.resolution_x, scene.render.resolution_y = W, H
        hires = cfg.get("hires", 1)        # close-up sheets: render at 2x, the sheet scales it down (crisper)
        scene.render.resolution_percentage = 100 * (1 if QUICK else hires)
        scene.render.film_transparent = True
        scene.render.image_settings.color_mode = "RGBA"
        scene.cycles.samples = 24 if QUICK else (96 if hires == 1 else 512)
        if hires > 1 and not QUICK:
            scene.cycles.use_denoising = False   # the denoiser smears the cone's 0.2 mm fibres into blotches
        rpath = os.path.join(MEASURE, f"render-{name}.png")
        log(f"compare {name}: IoU {iou_full:.4f} (dark parts {feat_iou}) at yaw={yaw} D={D:.2f} dz={dz:.3f} tilt={tl}; "
            f"rendering")
        yield from run.render_to(rpath)
        scene.render.film_transparent = False
        scene.render.image_settings.color_mode = "RGB"
        # the photo mask actually used, for the sheet's outlines
        mpath = os.path.join(MEASURE, f"mask-{name}.png")
        _save_mask(photo, mpath)
        res[name] = {"photo": cfg["photo"], "render": rpath, "silhouette": sil, "photo_mask": mpath,
                     "iou": round(float(iou_full), 4), "iou_dark_parts": feat_iou, "yaw_deg": yaw, "distance_m": round(D, 3),
                     "height_offset_m": round(dz, 3), "tilt_deg": tl, "transform": tf_full, "tries": sorted(tries)[-4:],
                     "finish": cfg["finish"], "fit_s": round(time.time() - t0)}
        bpy.data.objects.remove(cam)
        yield
    set_finish("white")
    _yaw(0)
    undo()


def _save_mask(m, path):
    import numpy as np
    H, W = m.shape
    im = bpy.data.images.new("tmp_mask", W, H, alpha=True)
    px = np.zeros((H, W, 4), np.float32)
    px[..., 0] = px[..., 1] = px[..., 2] = px[..., 3] = m[::-1].astype(np.float32)
    im.pixels.foreach_set(px.ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


# ---------------------------------------------------------------------------
# exports
# ---------------------------------------------------------------------------
def _export(objs, path):
    for o in bpy.data.objects:
        o.select_set(False)
    for o in objs:
        o.hide_viewport = False
        o.select_set(True)
    kw = dict(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
              export_cameras=False, export_lights=False, export_extras=False, export_image_format="AUTO")
    bpy.ops.export_scene.gltf(**kw)
    return run.glb_stats(path)


def _ctx(obj, objs=None):
    wm = bpy.data.window_managers[0]
    objs = objs or [obj]
    kw = dict(active_object=obj, object=obj, selected_objects=objs, selected_editable_objects=objs)
    if wm.windows and not bpy.app.background:
        kw.update(window=wm.windows[0], screen=wm.windows[0].screen)
    return bpy.context.temp_override(**kw)


def _image(name, size, data=False):
    im = bpy.data.images.get(name)
    if im is not None:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    if data:
        im.colorspace_settings.name = "Non-Color"
    return im


def _bake(objs, target, kind, samples=4):
    """Bake one channel of all `objs` into `target`: 'base', 'rough', 'metal' (an emission rewire) or 'ao'."""
    scene = bpy.context.scene
    restore = []
    seen = set()
    for o in objs:
        for mat in o.data.materials:
            if mat.name in seen:
                continue
            seen.add(mat.name)
            nt = mat.node_tree
            tn = nt.nodes.new("ShaderNodeTexImage")
            tn.image = target
            nt.nodes.active = tn
            restore.append((mat, tn, None))
            if kind == "ao":
                continue
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
            em = next((n for n in nt.nodes if n.type == "EMISSION"), None)
            e = nt.nodes.new("ShaderNodeEmission")
            if b is not None:
                sock = b.inputs[{"base": "Base Color", "rough": "Roughness", "metal": "Metallic"}[kind]]
                if sock.is_linked:
                    nt.links.new(sock.links[0].from_socket, e.inputs["Color"])
                else:
                    dv = sock.default_value
                    e.inputs["Color"].default_value = tuple(dv) if kind == "base" else (dv, dv, dv, 1.0)
            else:
                c = tuple(em.inputs["Color"].default_value) if em else (1, 1, 1, 1)
                e.inputs["Color"].default_value = c if kind == "base" else ((0.5,) * 3 + (1,) if kind == "rough" else (0, 0, 0, 1))
            old = out.inputs["Surface"].links[0].from_socket
            nt.links.new(e.outputs[0], out.inputs["Surface"])
            restore[-1] = (mat, tn, (e, old, out))
    scene.cycles.samples = samples
    scene.render.bake.margin = 4
    scene.render.bake.use_clear = True
    scene.render.bake.target = "IMAGE_TEXTURES"
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    with _ctx(objs[0], objs):
        bpy.ops.object.bake(type="AO" if kind == "ao" else "EMIT")
    for mat, tn, rw in restore:
        nt = mat.node_tree
        if rw:
            e, old, out = rw
            nt.links.new(old, out.inputs["Surface"])
            nt.nodes.remove(e)
        nt.nodes.remove(tn)


def _gltf_group():
    g = bpy.data.node_groups.get("glTF Material Output")
    if g is None:
        g = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
        g.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    return g


def export_lite(size=1024, orm_size=512):
    import numpy as np
    scene = bpy.context.scene
    prev_engine = scene.render.engine
    coll = _coll("speakers_lite")
    lroot = S.build(collection=coll, lite=True, suffix="_lite")
    S.set_mount(lroot, "pole", "_lite")
    for k in ("_pole", "_iso"):          # both mounts go in the GLB; the room shows one
        for i in (1, 2):
            o = bpy.data.objects[f"studio_speaker_{i:02d}{k}_lite"]
            o.hide_render = o.hide_viewport = False
    bpy.context.view_layer.update()
    parts = {k: bpy.data.objects[k + "_lite"] for k in PARTS}
    baked = [parts[k] for k in ("studio_speaker_01", "studio_speaker_01_woofer", "studio_speaker_01_pole",
                                "studio_speaker_01_iso")]          # 02 shares these meshes
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in baked:
        lay = o.data.uv_layers.new(name="UVMap")
        o.data.uv_layers.active = lay            # the atlas UV; the woofer keeps ConeUV for the bake source
        o.select_set(True)
    bpy.context.view_layer.objects.active = baked[0]
    with _ctx(baked[0], baked):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.003, correct_aspect=True,
                                 scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "METAL"
    scene.cycles.device = "CPU" if "--cpu" in ARGS else "GPU"
    scene.cycles.use_denoising = False
    hidden = []
    for o in scene.objects:
        if o not in baked and o.type == "MESH" and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    world = scene.world
    old_ao = world.light_settings.distance
    world.light_settings.distance = 0.03
    base = _image("speakers_atlas", size)
    rough = _image("speakers_rough_tmp", orm_size, True)
    metal = _image("speakers_metal_tmp", orm_size, True)
    ao = _image("speakers_ao_tmp", orm_size, True)
    with renderqueue.slot("speakers lite bake"):
        _bake(baked, base, "base", 4)
        _bake(baked, rough, "rough", 4)
        _bake(baked, metal, "metal", 4)
        _bake(baked, ao, "ao", 48)
    world.light_settings.distance = old_ao
    for o in hidden:
        o.hide_render = False
    orm = _image("speakers_orm", orm_size, True)
    px = np.empty(orm_size * orm_size * 4, np.float32)
    ch = []
    for im in (ao, rough, metal):
        im.pixels.foreach_get(px)
        ch.append(px.reshape(-1, 4)[:, 0].copy())
    out = np.ones((orm_size * orm_size, 4), np.float32)
    out[:, 0] = 0.4 + 0.6 * ch[0]
    out[:, 1], out[:, 2] = ch[1], ch[2]
    orm.pixels.foreach_set(out.ravel())
    for im in (rough, metal, ao):
        bpy.data.images.remove(im)
    kb = {}
    for im, fn, q in ((base, "speakers_atlas.jpg", 90), (orm, "speakers_orm.jpg", 92)):
        p = os.path.join(OUT, fn)
        im.filepath_raw = p
        im.file_format = "JPEG"
        scene.render.image_settings.quality = q
        try:
            im.save(filepath=p, quality=q)
        except TypeError:
            im.save()
        kb[fn] = round(os.path.getsize(p) / 1024)
    m, nt, b = M._new("mat_speakers_lite")
    tb = nt.nodes.new("ShaderNodeTexImage")
    tb.image = base
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = orm
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sep.inputs[0])
    nt.links.new(tb.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(sep.outputs[1], b.inputs["Roughness"])
    nt.links.new(sep.outputs[2], b.inputs["Metallic"])
    gg = nt.nodes.new("ShaderNodeGroup")
    gg.node_tree = _gltf_group()
    nt.links.new(sep.outputs[0], gg.inputs["Occlusion"])
    M._set(b, spec=0.5)
    for o in baked:
        o.data.materials.clear()
        o.data.materials.append(m)
        cu = o.data.uv_layers.get("ConeUV")
        if cu is not None:
            o.data.uv_layers.remove(cu)          # the lite model has one UV: the atlas
        o.data.uv_layers["UVMap"].active_render = True
    scene.render.engine = prev_engine
    rich = [root()] + [bpy.data.objects[k] for k in PARTS]
    for o in rich:
        o.name = o.name + "_rich"
    names.set_name(lroot, "speakers", data=False)
    for k, o in parts.items():
        o.name = k
    info = {"images_kb": kb, "per_part": {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in parts.items()}}

    def undo():
        mes = set(o.data for o in parts.values())
        for o in list(parts.values()):
            bpy.data.objects.remove(o)
        for me in mes:
            bpy.data.meshes.remove(me)
        bpy.data.objects.remove(lroot)
        for o in rich:
            o.name = o.name[:-5]
    return [lroot] + list(parts.values()), undo, info


def stage_export():
    t = time.time()
    r = root()
    S.set_mount(r, "pole")
    rich_objs = [r] + [bpy.data.objects[k] for k in PARTS]
    hidden = [o for o in rich_objs if o.hide_render]
    for o in hidden:
        o.hide_render = o.hide_viewport = False
    rich = _export(rich_objs, os.path.join(OUT, "speakers-rich.glb"))
    S.set_mount(r, "pole")
    log(f"GLB rich: {rich['kb']} KB, {rich['triangles']} triangles, {rich['materials']} materials")
    yield
    objs, undo, info = export_lite()
    lite = _export(objs, os.path.join(OUT, "speakers-lite.glb"))
    yield from lite_still(objs)
    undo()
    S.set_mount(r, "pole")
    REPORT["glb"] = {"rich": rich, "lite": lite, "lite_info": info, "export_s": round(time.time() - t, 1)}
    for fn in ("speakers_atlas.jpg", "speakers_orm.jpg"):
        shutil.copy(os.path.join(OUT, fn), os.path.join(FOOTAGE, fn.replace("_", "-")))
    log(f"GLB lite: {lite['kb']} KB, {lite['triangles']} triangles, {lite['materials']} materials, "
        f"images {lite['images']}")
    yield


def lite_still(lite_objs):
    """The lite model exactly as exported (baked atlas, one material), from the hero camera, rich hidden;
    the ISO stands hidden as in the room."""
    scene = bpy.context.scene
    lite = set(o.name for o in lite_objs if not o.name.endswith("_iso"))
    hidden = []
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name not in lite and not o.name.startswith("still_") and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    run.setup_render("CYCLES", quick=QUICK)
    scene.cycles.samples = 24 if QUICK else 128
    scene.camera = bpy.data.objects["still_cam_hero"]
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    dt = yield from run.render_to(out_path("lite"))
    REPORT.setdefault("stills_s", {})["lite"] = round(dt)
    for o in hidden:
        o.hide_render = False


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
    print(json.dumps({k: v for k, v in REPORT.items() if k != "compare"}, indent=2, default=str)[:3000], flush=True)


def job():
    if "build" in STAGES:
        yield from stage_build()
    else:
        open_blend()
        run.show_in_viewport()
        yield
    if "stills" in STAGES:
        yield from stage_stills()
    if "compare" in STAGES:
        yield from stage_compare()
    if "export" in STAGES:
        yield from stage_export()
    write_report()
    log(f"done: stage {STAGE} in {REPORT['total_s']} s")
    yield
    if "--stay" not in ARGS:
        bpy.ops.wm.quit_blender()


run.drive(job())
