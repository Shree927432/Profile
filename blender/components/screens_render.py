"""screens: build, stills, UV test, photo compare, rich and lite GLBs. One command:

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup \\
        --python blender/components/screens_render.py -- [stages] [--quick] [--stills=hero,front]

stages: all (default: build,stills,uvtest,compare,export) or several joined with commas. `build` saves
blender/out/components/screens.blend; the other stages open it. With the window open (no -b) the scene
shows while it is built and renders show in the render window. Then, outside Blender:

    /opt/anaconda3/bin/python3 blender/components/screens_blueprint.py   (blueprint + compare sheets)

Stills, the compare data and the report go to video-local/footage/2026-10-24-components/screens/,
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
import screens as S  # noqa: E402

ARGS = run.args()
STAGE = next((a for a in ARGS if not a.startswith("--")), "all")
STAGES = {"build", "stills", "uvtest", "compare", "export"} if STAGE == "all" else set(STAGE.split(","))
QUICK = "--quick" in ARGS
_only = next((a for a in ARGS if a.startswith("--stills=")), None)
STILLS = set(_only[len("--stills="):].split(",")) if _only else None
OUT = os.path.join(C.OUT, "components")
BLEND = os.path.join(OUT, "screens.blend")
FOOTAGE = os.path.join(C.FOOTAGE, "2026-10-24-components", "screens")
MEASURE = os.path.join(FOOTAGE, "measure")
REF = os.path.join(C.REPO, "docs", "moodboard", "local")
REPORT_PATH = os.path.join(FOOTAGE, "screens-report.json" if not QUICK else "screens-quick-report.json")
REPORT = {}
T0 = time.time()
if "--cpu" in ARGS:          # fallback when the Metal device hangs (seen 2026-10-24 with other renders running)
    _setup = run.setup_render

    def _setup_cpu(*a, **k):
        _setup(*a, **k)
        bpy.context.scene.cycles.device = "CPU"
    run.setup_render = _setup_cpu
log = run.log
PARTS = ["rig_display", "rig_screen", "rig_static", "monitor_body", "monitor_screen", "monitor_static",
         "desk_pole", "desk_screenbar", "desk_screenbar_dial"]


def out_path(name):
    return os.path.join(FOOTAGE, f"screens-{name}{'-quick' if QUICK else ''}.png")


def root():
    return bpy.data.objects["screens"]


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
    # what metals reflect: a studio with a darker floor and a light ceiling, not one flat grey
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.40, M.rgba("#3c3f44")
    el[1].position, el[1].color = 0.62, M.rgba("#d6d9de")
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    # the camera sees a lighter grey than the light the world gives
    cam_bg = nt.nodes.new("ShaderNodeBackground")
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
    area("lt_key", (-1.7, -1.9, 1.9), (0, 0.05, 0.45), 1.8, 1.4, 330, "#fff7ee")
    area("lt_fill", (2.0, -1.4, 0.9), (0, 0.05, 0.45), 1.6, 1.2, 90, "#eef3ff")
    area("lt_rim", (0.9, 1.9, 1.7), (0, 0.05, 0.5), 1.4, 1.0, 170, "#ffffff")
    area("lt_back", (-1.2, 1.6, 0.6), (0, 0.1, 0.3), 1.2, 0.8, 60, "#ffffff")
    scene.view_settings.exposure = -0.35
    sc = _coll("still_set")
    desk = geo.box("still_desk", -0.75, 0.75, -0.55, S.DESK_BACK_Y, -S.DESK_T, 0.0, collection=sc,
                   material=M.principled("mat_still_desk", base="#eeeeec", rough=0.35, coat=0.2, coat_rough=0.2))
    geo.bevel(desk, 0.003, segments=2)
    return coll


def build_cameras():
    coll = _coll("still_cameras")
    zc = 0.45
    cams = dict(
        hero=looks.camera("still_cam_hero", (-1.38, -2.15, 1.02), (0.0, 0.05, 0.47), lens=50, coll=coll),
        front=looks.camera("still_cam_front", (0.0, -2.6, zc), (0.0, 0.0, zc), lens=50, coll=coll),
        side=looks.camera("still_cam_side", (2.6, 0.05, zc), (0.0, 0.05, zc), lens=50, coll=coll),
        back=looks.camera("still_cam_back", (1.05, 1.95, 0.95), (0.0, 0.08, 0.42), lens=50, coll=coll),
        detail=looks.camera("still_cam_detail", (0.30, 0.56, 0.05), (0.0, 0.05, 0.17), lens=50, fstop=5.6, coll=coll),
        detailbar=looks.camera("still_cam_detailbar", (-0.40, -0.55, 1.12), (-0.02, 0.0, 0.86), lens=60, fstop=5.6,
                               coll=coll),
        uv=looks.camera("still_cam_uv", (0.0, -2.2, 0.50), (0.0, 0.0, 0.50), lens=55, coll=coll),
    )
    cd = bpy.data.cameras.new("still_cam_top")
    cd.type = "ORTHO"
    cd.ortho_scale = 1.05
    top = bpy.data.objects.new("still_cam_top", cd)
    coll.objects.link(top)
    top.location = (0.0, 0.0, 2.5)
    cams["top"] = top
    return cams


def stage_build():
    log("build: studio, the two screens, pole, arms, light bar")
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
    REPORT["halo_bar_offset_mm"] = bpy.data.objects["desk_screenbar"]["bar_offset_mm"]
    REPORT["layout"] = {"g8_bottom_z": S.G8_Z0, "sd_bottom_z": S.sd_z0(), "pole_y": S.POLE_Y,
                        "g8_sag_mm": round(S.G8_SAG / S.MM, 2), "g8_half_arc_mm": round(S.G8_S / S.MM, 2)}
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    log(f"built in {REPORT['build_s']} s: {REPORT['check']['triangles_before_bevels']} triangles before bevels; "
        f"saved {BLEND}")
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


# ---------------------------------------------------------------------------
# halo option B: the bar on the G8 (as asked), the top screen raised to clear it
# ---------------------------------------------------------------------------
def set_halo(option):
    r = root()
    old = bpy.data.objects["desk_screenbar"]
    me = old.data
    bpy.data.objects.remove(old)
    bpy.data.meshes.remove(me)
    mats = {k: bpy.data.materials[n] for k, n in (("halo", "mat_screens_halo_anodised"),
                                                   ("halo_plastic", "mat_screens_halo_plastic"),
                                                   ("halo_glossy", "mat_screens_halo_glossy"),
                                                   ("rubber", "mat_screens_rubber"), ("led", "mat_screens_halo_led"),
                                                   ("led_back", "mat_screens_halo_backlight"))}
    coll = r.users_collection[0]
    dz = S.sd_z0(option) - bpy.data.objects["monitor_body"].location.z
    for n in ("monitor_body", "monitor_screen"):
        bpy.data.objects[n].location.z += dz
    arm = bpy.data.objects["monitor_static"]
    arm.location.z += dz
    if option == "top":
        S.build_screenbar(mats, coll, r, S.SD_Y, S.sd_z0(option) + S.SD_H, back_y_mm=S.SD_T / S.MM)
    else:
        S.build_screenbar(mats, coll, r, 0.0, S.G8_Z0 + S.G8_H, depth_at=S.g8_back_y_mm)


# ---------------------------------------------------------------------------
# stills
# ---------------------------------------------------------------------------
def stage_stills():
    os.makedirs(FOOTAGE, exist_ok=True)
    scene = bpy.context.scene
    objs = bpy.data.objects
    run.setup_render("CYCLES", quick=QUICK)
    scene.view_settings.exposure = -0.35
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
    yield from still("detail", "still_cam_detail", 256)
    yield from still("detail-bar", "still_cam_detailbar", 256)
    looks.clay_on()
    yield from still("clay", "still_cam_hero", 128)
    looks.clay_off()
    if STILLS is None or "option-b" in STILLS:
        set_halo("bottom")
        yield from still("option-b-halo-on-g8", "still_cam_hero", 160)
        set_halo("top")
    if STILLS is None or "stand" in STILLS:
        stand_view(True)
        yield from still("g8-on-own-stand", "still_cam_hero", 160)
        stand_view(False)
    if STILLS is not None and "wire" not in STILLS:
        return
    undo = looks.wire_look(thickness=0.0004, skip={"still_desk"})
    cam_bg = [n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND" and n.name != "Background"][0]
    old_bg = tuple(cam_bg.inputs["Color"].default_value)
    cam_bg.inputs["Color"].default_value = M.rgba("#0d1626")
    old_ex = scene.view_settings.exposure
    scene.view_settings.exposure = 0.0
    run.setup_render("BLENDER_EEVEE", quick=QUICK, samples=32)
    scene.camera = objs["still_cam_hero"]
    path = out_path("wire")
    log("still wire: rendering (EEVEE)")
    dt = yield from run.render_to(path)
    times["wire"] = round(dt)
    undo()
    cam_bg.inputs["Color"].default_value = old_bg
    scene.view_settings.exposure = old_ex
    run.setup_render("CYCLES", quick=QUICK)


def stand_view(on):
    """The G8 alone on its own stand (the stand's foot on the desk), everything else hidden."""
    objs = bpy.data.objects
    dz = S.G8_STAND_LOW - S.G8_Z0
    for n in ("rig_display", "rig_screen", "rig_stand"):
        objs[n].location.z += dz if on else -dz
    objs["rig_stand"].hide_render = objs["rig_stand"].hide_viewport = not on
    for n in ("rig_static", "monitor_body", "monitor_screen", "monitor_static", "desk_pole", "desk_screenbar",
              "desk_screenbar_dial"):
        objs[n].hide_render = objs[n].hide_viewport = on


# ---------------------------------------------------------------------------
# UV test: TOP and an arrow on both screens, rendered upright; then the same check on the exported GLB
# ---------------------------------------------------------------------------
def stage_uvtest():
    scene = bpy.context.scene
    run.setup_render("CYCLES", quick=QUICK)
    scene.cycles.samples = 24 if QUICK else 96
    scene.render.image_settings.file_format = "PNG"
    img1 = geo.uvtest_image("screens_uvtest_posts", 1024, 640)
    img2 = geo.uvtest_image("screens_uvtest_rig", 1536, 640)
    swaps = []
    for n, img in (("monitor_screen", img1), ("rig_screen", img2)):
        o = bpy.data.objects[n]
        m = M.screen_image(f"mat_uvtest_{n}", img, 1.0)
        swaps.append((o, o.data.materials[0]))
        o.data.materials[0] = m
    scene.camera = bpy.data.objects["still_cam_uv"]
    path = out_path("uvtest")
    log("uvtest: rendering TOP on both screens")
    dt = yield from run.render_to(path)
    REPORT.setdefault("stills_s", {})["uvtest"] = round(dt)
    for o, m in swaps:
        o.data.materials[0] = m


# ---------------------------------------------------------------------------
# photo compare: fit the camera to the official photo's silhouette, then render it there
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
        m = px[..., 3] > 0.5
    else:
        m = px[..., :3].mean(-1) < mode
    return m


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
    """Scale and move the render's mask so its box matches the photo's (uniform scale from the widths),
    then intersection over union. With refine, also search a few pixels and half a percent of scale
    around that (the photos' outlines carry thin rims and shadows). Returns (iou, transform)."""
    px0, px1, py0, py1 = _bbox(photo)
    rx0, rx1, ry0, ry1 = _bbox(rend)
    s0 = (px1 - px0) / max(1, rx1 - rx0)
    best = None
    steps = [(ds, dx, dy) for ds in (0.99, 0.995, 1.0, 1.005, 1.01) for dx in (-4, -2, 0, 2, 4)
             for dy in (-8, -6, -4, -2, 0, 2, 4, 6, 8)] if refine else [(1.0, 0, 0)]
    for ds, dx, dy in steps:
        s = s0 * ds
        cx, cy = (px0 + px1) / 2, (py0 + py1) / 2
        rcx, rcy = (rx0 + rx1) / 2, (ry0 + ry1) / 2
        tx, ty = cx - rcx * s + dx, py0 - ry0 * s + dy
        rm = _warp(rend, photo.shape, s, tx, ty)
        iou = (rm & photo).sum() / max(1, (rm | photo).sum())
        if best is None or iou > best[0]:
            best = (iou, {"scale": float(s), "tx": float(tx), "ty": float(ty)})
    return best


COMPARES = {
    # name: photo, mask mode (alpha, or a brightness threshold on a white page), crop box, what to show,
    # camera side (-1 front, 1 back), ortho for the flat Studio Display
    "g8-front": dict(photo=os.path.join(REF, "ai-lab", "02-main-screen", "dimensions-official-samsung-au.png"),
                     mode=0.92, crop=(548, 1295, 585, 1075), show="g8_stand", side=-1),
    "g8-front-gallery": dict(photo=os.path.join(REF, "odyssey-g8-samsung", "g8-01.png"), mode="alpha",
                             crop=(0, 1705, 0, 9999), show="g8_stand", side=-1),
    "g8-back": dict(photo=os.path.join(REF, "odyssey-g8-samsung", "g8-02.png"), mode="alpha", crop=None,
                    show="g8_stand", side=1),
    "sd-front": dict(photo=os.path.join(REF, "ai-lab", "03-top-screen", "front-screen-off.jpg"), mode=0.8,
                     crop=(0, 9999, 0, 1426), show="sd", side=-1, ortho=True),
    "sd-back": dict(photo=os.path.join(REF, "ai-lab", "03-top-screen", "diagram-back-vesa-adapter.jpg"), mode=0.93,
                    crop=(0, 9999, 50, 9999), show="sd", side=1, ortho=True),
}


def _show(which):
    objs = bpy.data.objects
    keep = {"g8_stand": {"rig_display", "rig_screen", "rig_stand"}, "sd": {"monitor_body", "monitor_screen"}}[which]
    state = {}
    for o in names.descendants(root()) + [objs["still_desk"]]:
        state[o.name] = (o.hide_render, o.hide_viewport)
        o.hide_render = o.hide_viewport = o.name not in keep
    if which == "g8_stand":
        stand_view(True)
        for n in ("rig_static",):
            objs[n].hide_render = True

    def undo():
        if which == "g8_stand":
            stand_view(False)
        for n, (a, b) in state.items():
            objs[n].hide_render, objs[n].hide_viewport = a, b
    return undo


def _rowfill(m):
    """Fill holes (the photo's bright screen content): a pixel is in if it lies between the first and
    last pixel of its row and also of its column, so curved outer edges are not squared off."""
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


def _panel_only(m):
    """Rows down to the panel's bottom edge: where the silhouette narrows to the stand."""
    import numpy as np
    w = m.sum(1)
    rows = np.nonzero(w > 0.6 * w.max())[0]
    out = m.copy()
    out[rows.max() + 1:] = False
    return out


def stage_compare():
    import numpy as np
    os.makedirs(MEASURE, exist_ok=True)
    scene = bpy.context.scene
    objs = bpy.data.objects
    res = REPORT.setdefault("compare", {})
    for name, cfg in COMPARES.items():
        if STILLS is not None and name not in STILLS:
            continue
        photo = _rowfill(_load_mask(cfg["photo"], cfg["mode"]) & _crop_mask(cfg))
        H, W = photo.shape
        undo = _show(cfg["show"])
        g8 = cfg["show"] == "g8_stand"
        if g8:
            zc = objs["rig_display"].location.z + S.G8_H / 2      # stand_view(True) has moved it up
            yc = 0.0
        else:
            zc = objs["monitor_body"].location.z + S.SD_H / 2
            yc = objs["monitor_body"].location.y
        scene.render.engine = "BLENDER_WORKBENCH"
        sh = scene.display.shading
        sh.light, sh.color_type = "FLAT", "SINGLE"
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.resolution_x, scene.render.resolution_y = W // 2, H // 2
        scene.render.resolution_percentage = 100
        photo2 = photo[::2, ::2]
        cd = bpy.data.cameras.new("still_cam_cmp")
        cam = bpy.data.objects.new("still_cam_cmp", cd)
        scene.collection.objects.link(cam)
        scene.camera = cam
        side = cfg["side"]
        cam.rotation_euler = (math.radians(90), 0, math.radians(0 if side < 0 else 180))
        sil = os.path.join(MEASURE, f"sil-{name}.png")

        def place(D, dz):
            if D == "ortho":
                cd.type = "ORTHO"
                cd.ortho_scale = S.SD_W * 1.25
                cam.location = (0, yc + side * 2.0, zc)
            else:
                cd.sensor_fit = "HORIZONTAL"
                cam.location = (0, yc + side * D, zc + dz)
                cd.lens = 36 * D / 1.6
                cd.shift_y = -dz / 1.6

        def score(target):
            scene.render.filepath = sil
            bpy.ops.render.render(write_still=True)
            rm = _load_mask(sil, "alpha")
            return _iou(target, _panel_only(rm) if target is panel2 else rm)
        tries = []
        # 1. the camera, fitted on the panel alone (the stand's height is set separately)
        panel2 = _panel_only(photo2) if g8 else photo2
        if g8:
            objs["rig_stand"].hide_render = True
        if cfg.get("ortho"):
            grid = [("ortho", 0.0)]
        else:
            grid = [(D, dz) for D in (0.9, 1.3, 2.0, 3.0, 5.0, 8.0) for dz in (-0.3, -0.15, 0.0, 0.1, 0.2, 0.3)]
        best = None
        for D, dz in grid:
            place(D, dz)
            iou, tf = score(panel2)
            tries.append((round(float(iou), 4), D, dz))
            if best is None or iou > best[0]:
                best = (iou, D, dz)
            yield
        if not cfg.get("ortho"):
            D0, z0 = best[1], best[2]
            for D in (D0 * 0.75, D0 * 0.87, D0 * 1.15, D0 * 1.3):
                for dz in (z0 - 0.05, z0, z0 + 0.05):
                    place(D, dz)
                    iou, tf = score(panel2)
                    tries.append((round(float(iou), 4), round(D, 3), round(dz, 3)))
                    if iou > best[0]:
                        best = (iou, D, dz)
                    yield
        panel_iou, D, dz = best
        place(D, dz)
        # 2. the stand's height (it slides 120 mm), with the stand shown
        lift = 0.0
        if g8:
            st = objs["rig_stand"]
            st.hide_render = False
            bl = -1.0
            for lf in (0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12):
                st.location.z -= lf
                i2, _ = score(photo2)
                st.location.z += lf
                if i2 > bl:
                    bl, lift = i2, lf
                yield
            st.location.z -= lift
        # 3. full resolution silhouette and the Cycles render at that camera
        scene.render.resolution_x, scene.render.resolution_y = W, H
        scene.render.filepath = sil
        bpy.ops.render.render(write_still=True)
        rm = _load_mask(sil, "alpha")
        iou_full, tf_full = _iou(photo, rm, refine=True)
        iou_panel, _ = _iou(_panel_only(photo), _panel_only(rm), refine=True) if g8 else (iou_full, None)
        run.setup_render("CYCLES", quick=QUICK)
        scene.render.resolution_x, scene.render.resolution_y = W, H
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.image_settings.color_mode = "RGBA"
        scene.cycles.samples = 24 if QUICK else 128
        rpath = os.path.join(MEASURE, f"render-{name}.png")
        log(f"compare {name}: IoU {iou_full:.3f} (panel {iou_panel:.3f}) at D={D} dz={dz} lift={lift}; rendering")
        yield from run.render_to(rpath)
        scene.render.film_transparent = False
        scene.render.image_settings.color_mode = "RGB"
        res[name] = {"photo": cfg["photo"], "render": rpath, "silhouette": sil, "iou": round(float(iou_full), 4),
                     "iou_panel": round(float(iou_panel), 4), "distance_m": D, "height_offset_m": dz,
                     "stand_lift_m": lift, "transform": tf_full, "tries": sorted(tries)[-5:],
                     "photo_mask_mode": cfg["mode"], "crop": cfg.get("crop")}
        if lift:
            objs["rig_stand"].location.z += lift
        bpy.data.objects.remove(cam)
        undo()
        yield


def _crop_mask(cfg):
    import numpy as np
    im = bpy.data.images.load(cfg["photo"], check_existing=True)
    w, h = im.size
    m = np.zeros((h, w), bool)
    x0, x1, y0, y1 = cfg.get("crop") or (0, w, 0, h)
    m[y0:y1, x0:x1] = True
    return m


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
    coll = _coll("screens_lite")
    lroot = S.build(collection=coll, lite=True, suffix="_lite")
    bpy.context.view_layer.update()
    parts = {k: bpy.data.objects[k + "_lite"] for k in PARTS}
    baked = [o for k, o in parts.items() if k not in ("monitor_screen", "rig_screen")]
    # one shared UV atlas across the baked parts
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in baked:
        o.data.uv_layers.new(name="UVMap")
        o.select_set(True)
    bpy.context.view_layer.objects.active = baked[0]
    with _ctx(baked[0], baked):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.004, correct_aspect=True,
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
    world.light_settings.distance = 0.04
    base = _image("screens_atlas", size)
    rough = _image("screens_rough_tmp", orm_size, True)
    metal = _image("screens_metal_tmp", orm_size, True)
    ao = _image("screens_ao_tmp", orm_size, True)
    _bake(baked, base, "base", 4)
    _bake(baked, rough, "rough", 4)
    _bake(baked, metal, "metal", 4)
    _bake(baked, ao, "ao", 48)
    world.light_settings.distance = old_ao
    for o in hidden:
        o.hide_render = False
    orm = _image("screens_orm", orm_size, True)
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
    for im, fn, q in ((base, "screens_atlas.jpg", 90), (orm, "screens_orm.jpg", 92)):
        p = os.path.join(OUT, fn)
        im.filepath_raw = p
        im.file_format = "JPEG"
        scene.render.image_settings.quality = q
        try:
            im.save(filepath=p, quality=q)
        except TypeError:
            im.save()
        kb[fn] = round(os.path.getsize(p) / 1024)
    m, nt, b = M._new("mat_screens_lite")
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
    scene.render.engine = prev_engine
    # swap names for the export
    rich = [root()] + [bpy.data.objects[k] for k in PARTS]
    for o in rich:
        o.name = o.name + "_rich"
        if o.type == "MESH":
            o.data.name = o.name + "_mesh"
    names.set_name(lroot, "screens", data=False)
    for k, o in parts.items():
        names.set_name(o, k)
    info = {"images_kb": kb, "per_part": {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in parts.items()}}

    def undo():
        for o in list(parts.values()):
            me = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
        bpy.data.objects.remove(lroot)
        for o in rich:
            names.set_name(o, o.name[:-5], data=o.type == "MESH")
    return [lroot] + list(parts.values()), undo, info


def glb_screen_uv_check(path):
    """Read the GLB and check, for both screens, which UV the top-left and bottom-right corners carry
    (three.js frame: +Y up, -X left), against the rule in MESHES.md."""
    import struct
    with open(path, "rb") as f:
        f.read(12)
        clen, _ = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(clen))
        blen, _ = struct.unpack("<II", f.read(8))
        bin_ = f.read(blen)

    def acc(i):
        a = doc["accessors"][i]
        bv = doc["bufferViews"][a["bufferView"]]
        n = {"VEC2": 2, "VEC3": 3}[a["type"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", 4 * n)
        return [struct.unpack_from("<" + "f" * n, bin_, off + k * stride) for k in range(a["count"])]
    out = {}
    for mesh in doc["meshes"]:
        if mesh["name"] not in ("monitor_screen_mesh", "rig_screen_mesh"):
            continue
        prim = mesh["primitives"][0]
        pos, uv = acc(prim["attributes"]["POSITION"]), acc(prim["attributes"]["TEXCOORD_0"])
        tl = min(range(len(pos)), key=lambda k: pos[k][0] - pos[k][1])      # left and up
        br = max(range(len(pos)), key=lambda k: pos[k][0] - pos[k][1])
        # MESHES.md: as three.js loads it, U runs left to right and V bottom to top (the room's canvas
        # textures keep three.js's default flipY), so the top-left corner must read (0, 1)
        out[mesh["name"]] = {"top_left_uv": [round(x, 4) for x in uv[tl]], "bottom_right_uv": [round(x, 4) for x in uv[br]],
                             "upright": abs(uv[tl][0]) < 1e-3 and abs(uv[tl][1] - 1) < 1e-3 and
                             abs(uv[br][0] - 1) < 1e-3 and abs(uv[br][1]) < 1e-3}
    return out


def stage_export():
    t = time.time()
    r = root()
    for n in ("rig_stand",):
        bpy.data.objects[n].hide_viewport = False
    rich_objs = [r] + [bpy.data.objects[k] for k in PARTS]
    rich = _export(rich_objs, os.path.join(OUT, "screens-rich.glb"))
    bpy.data.objects["rig_stand"].hide_viewport = True
    log(f"GLB rich: {rich['kb']} KB, {rich['triangles']} triangles, {rich['materials']} materials")
    yield
    objs, undo, info = export_lite()
    lite = _export(objs, os.path.join(OUT, "screens-lite.glb"))
    yield from lite_still(objs)
    undo()
    REPORT["glb"] = {"rich": rich, "lite": lite, "lite_info": info, "export_s": round(time.time() - t, 1)}
    REPORT["glb_uv_check"] = {"rich": glb_screen_uv_check(os.path.join(OUT, "screens-rich.glb")),
                              "lite": glb_screen_uv_check(os.path.join(OUT, "screens-lite.glb"))}
    for fn in ("screens_atlas.jpg", "screens_orm.jpg"):
        shutil.copy(os.path.join(OUT, fn), os.path.join(FOOTAGE, fn.replace("_", "-")))
    log(f"GLB lite: {lite['kb']} KB, {lite['triangles']} triangles, {lite['materials']} materials, "
        f"images {lite['images']}; UV check {REPORT['glb_uv_check']}")
    yield


def lite_still(lite_objs):
    """The lite model exactly as exported (baked atlas, one material), from the hero camera, rich hidden.
    (Re-importing the GLB fails in Blender 5.2's glTF importer: "Iridescence Factor" not found.)"""
    scene = bpy.context.scene
    lite = set(o.name for o in lite_objs)
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
    print(json.dumps(REPORT, indent=2, default=str)[:4000], flush=True)


def job():
    if "build" in STAGES:
        yield from stage_build()
    else:
        open_blend()
        run.show_in_viewport()
        yield
    if "stills" in STAGES:
        yield from stage_stills()
    if "uvtest" in STAGES:
        yield from stage_uvtest()
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
