"""desk: build, stills, the every-angle compare, close-up pair sheets and the GLBs (component, 2026-10-24).

Always headless:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/components/desk_render.py
    ... -- build,stills          some stages (build, stills, compare, closeups, export); the others open the .blend
    ... -- stills --only=hero,led   some stills
    ... -- --quick              low samples (checks)

Output: blender/out/components/desk.blend, desk-rich.glb, desk-lite.glb;
video-local/footage/2026-10-24-components/desk/ (stills, compare/, closeups, NOTE.md).
The IKEA reference views (desk.py -- refviews) must exist first; the outline check is run on its own.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
import desk as D  # noqa: E402
from lib import compare, looks, materials as M, renderqueue, run  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
QUICK = "--quick" in ARGS
ONLY = next((a.split("=", 1)[1].split(",") for a in ARGS if a.startswith("--only=")), None)
OUT = os.path.join(D.BLENDER_DIR, "out", "components")
BLEND = os.path.join(OUT, "desk.blend")
FOOT = next((a.split("=", 1)[1] for a in ARGS if a.startswith("--foot=")), D.FOOTAGE)
CMP_DIR = os.path.join(FOOT, "compare")
REPORT_PATH = os.path.join(FOOT, "desk-report.json")
EXPOSURE = -0.2


def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} desk: {msg}", flush=True)


def report(**kw):
    rep = json.load(open(REPORT_PATH)) if os.path.exists(REPORT_PATH) else {}
    rep.update(kw)
    with open(REPORT_PATH, "w") as f:
        json.dump(rep, f, indent=1, default=str)


def _coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")


def gpu():
    sc = bpy.context.scene
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "METAL"
    sc.cycles.device = "CPU" if "--cpu" in ARGS else "GPU"


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def roles():
    """Object names by role, from the open file."""
    objs = bpy.data.objects
    unit = [o.name for o in objs if o.parent and o.parent.name == "alex" and o.type == "MESH"]
    desk = [o.name for o in objs if o.type == "MESH" and (o.name.startswith("desk_"))]
    cmp200 = [o.name for o in objs if o.type == "MESH" and o.name.startswith("cmp200_")]
    r = {"unit": unit, "unit_root": ["alex"], "desk": desk, "desk_root": ["set_desk"], "cmp200": cmp200,
         "cmp200_root": ["cmp200"], "all": unit + desk + cmp200}
    for w in D.LAG_SIZES:
        nm = f"lag{int(w / 10)}"
        if nm + "_top" in objs:
            r[nm] = [nm + "_top"]
    return r


def build_studio():
    """Neutral studio (soft key, fill, rim, light grey background) on a rig empty `lt_rig` that each
    still moves to its subject; a light grey floor (never exported)."""
    sc = bpy.context.scene
    w = sc.world
    try:
        w.use_nodes = True
    except AttributeError:
        pass
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = M.rgba("#d9dadd")
    bg.inputs["Strength"].default_value = 0.55
    coll = _coll("lights_studio")
    rig = bpy.data.objects.new("lt_rig", None)
    coll.objects.link(rig)

    def area(name, loc, size, energy, colour="#ffffff"):
        d = bpy.data.lights.new(name, "AREA")
        d.shape = "RECTANGLE"
        d.size, d.size_y, d.energy = size, size * 0.8, energy
        d.color = M.srgb(colour)
        o = bpy.data.objects.new(name, d)
        coll.objects.link(o)
        o.parent = rig
        o.location = loc
        o.rotation_euler = (-Vector(loc) + Vector((0, 0, 0.4))).to_track_quat("-Z", "Y").to_euler()
        return o
    area("lt_key", (2.0, -2.2, 2.4), 2.0, 520, "#fff8f0")
    area("lt_fill", (-2.4, -1.6, 1.2), 1.8, 170, "#eef3ff")
    area("lt_rim", (-1.0, 2.4, 2.2), 1.6, 260)
    area("lt_top", (0.0, -0.3, 3.2), 2.2, 220)
    area("lt_front", (0.4, -3.2, 1.0), 2.4, 260)   # the packshots' broad frontal softbox (round 2)
    fc = _coll("still_set")
    me = bpy.data.meshes.new("still_floor_mesh")
    s = 12.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new("still_floor", me)
    fc.objects.link(fl)
    me.materials.append(M.principled("mat_still_floor", base="#c9cacd", rough=0.75, spec=0.3))
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = EXPOSURE
    return rig


def stage_build():
    clear()
    t = time.time()
    n = D.build(what=("unit", "desk", "cmp200", "lag"))
    build_studio()
    for o in bpy.data.objects:                 # the compare layouts only show when asked
        if o.name.startswith(("cmp200", "lag1")):
            o.hide_render = True
            o.hide_viewport = True
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    log(f"built in {time.time() - t:.1f} s: {len(n['all'])} meshes, saved {BLEND}")


def open_blend():
    bpy.ops.wm.open_mainfile(filepath=BLEND)


def rendered_triangles(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    t = 0
    for n in objs:
        o = bpy.data.objects[n]
        if o.type != "MESH":
            continue
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        t += len(me.loop_triangles)
        o.evaluated_get(dg).to_mesh_clear()
    return t


# ---------------------------------------------------------------------------
# stills
# ---------------------------------------------------------------------------
def show(groups):
    """Render only these roots' trees (plus the floor, lights)."""
    keep = set()
    for g in groups:
        r = bpy.data.objects.get(g)
        if r is None:
            continue
        keep.add(r.name)
        keep |= {c.name for c in r.children_recursive}
    for o in bpy.data.objects:
        if o.type in ("MESH", "EMPTY") and not o.name.startswith(("still_", "lt_")):
            o.hide_render = o.name not in keep


def desk_pt(x, y, z):
    """A point in the desk's frame, in the build file."""
    return tuple(Vector(D.DESK_AT) + Vector((x, y, z)))


def cameras():
    coll = _coll("still_cameras")
    c = {}
    cam = looks.camera
    c["hero"] = cam("still_cam_hero", desk_pt(3.55, -3.05, 1.75), desk_pt(0.92, -0.78, 0.42), lens=35, coll=coll)
    c["front"] = cam("still_cam_front", desk_pt(0.95, -4.4, 0.62), desk_pt(0.95, -0.9, 0.40), lens=40, coll=coll)
    c["side"] = cam("still_cam_side", desk_pt(4.6, -0.95, 0.62), desk_pt(0.6, -0.95, 0.40), lens=40, coll=coll)
    c["back"] = cam("still_cam_back", desk_pt(-1.6, 1.9, 1.9), desk_pt(0.8, -0.8, 0.45), lens=35, coll=coll)
    cd = bpy.data.cameras.new("still_cam_top")
    cd.type, cd.ortho_scale = "ORTHO", 3.7
    top = bpy.data.objects.new("still_cam_top", cd)
    coll.objects.link(top)
    top.location = desk_pt(0.91, -0.93, 3.0)
    c["top"] = top
    c["alex"] = cam("still_cam_alex", (0.95, -1.75, 1.05), (0.0, 0.0, 0.36), lens=50, coll=coll)
    c["open"] = cam("still_cam_open", (0.75, -1.45, 1.55), (0.0, -0.32, 0.50), lens=45, coll=coll)
    c["detail"] = cam("still_cam_detail", (0.20, -0.62, 0.86), (0.0, -0.29, 0.645), lens=60, fstop=11.0, coll=coll)
    c["plinth"] = cam("still_cam_plinth", (0.42, -1.05, 0.34), (0.03, -0.29, 0.07), lens=60, fstop=11.0, coll=coll)
    c["corner"] = cam("still_cam_corner", desk_pt(2.15, -2.35, 1.55), desk_pt(0.85, -0.66, 0.58), lens=35, coll=coll)
    c["edge"] = cam("still_cam_edge", desk_pt(1.82 - 0.40, -0.60 - 0.95, 0.735 + 0.45), desk_pt(1.74, -0.63, 0.712),
                    lens=85, fstop=11.0, coll=coll)
    c["led"] = cam("still_cam_led", desk_pt(3.1, -3.6, 1.45), desk_pt(0.85, -0.8, 0.45), lens=32, coll=coll)
    return c


def led_scene(on):
    """The LED still: two walls behind the desk, the studio dimmed, a dark carpet floor."""
    sc = bpy.context.scene
    walls = [bpy.data.objects.get(n) for n in ("still_wall_left", "still_wall_back")]
    if on and walls[0] is None:
        fc = _coll("still_set")
        mat = M.principled("mat_still_wall", base="#d6dbe2", rough=0.85, spec=0.3)
        for n, verts in (("still_wall_left", [(0, -4, 0), (0, 0.0, 0), (0, 0.0, 2.6), (0, -4, 2.6)]),
                         ("still_wall_back", [(0, 0, 0), (4, 0, 0), (4, 0, 2.6), (0, 0, 2.6)])):
            me = bpy.data.meshes.new(n + "_mesh")
            me.from_pydata([desk_pt(*v) for v in verts], [], [(0, 1, 2, 3)])
            me.materials.append(mat)
            o = bpy.data.objects.new(n, me)
            fc.objects.link(o)
        walls = [bpy.data.objects.get(n) for n in ("still_wall_left", "still_wall_back")]
    for wl in walls:
        if wl is not None:
            wl.hide_render = not on
    fl = bpy.data.objects["still_floor"].data.materials[0]
    b = next(n for n in fl.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = M.rgba("#3b4048" if on else "#c9cacd")
    for n in ("lt_key", "lt_fill", "lt_rim", "lt_top", "lt_front"):
        L = bpy.data.objects[n].data
        L["e0"] = L.get("e0", L.energy)
        L.energy = L["e0"] * (0.05 if on else 1.0)
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.03 if on else 0.55


def render(path, cycles, samples, label):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGB"
    sc.render.filepath = path
    t = time.time()
    cycles = cycles and "--eevee" not in ARGS
    if cycles:
        sc.render.engine = "CYCLES"
        gpu()
        sc.cycles.samples = 16 if QUICK else samples
        sc.cycles.use_denoising = True
        with renderqueue.slot(f"desk {label}"):
            t = time.time()
            bpy.ops.render.render(write_still=True)
    else:
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = 8 if QUICK else 64
        bpy.ops.render.render(write_still=True)
    dt = round(time.time() - t, 1)
    log(f"still {label}: {dt} s ({'Cycles' if cycles else 'EEVEE'})")
    return dt


def stage_stills():
    sc = bpy.context.scene
    cams = cameras()
    rig = bpy.data.objects["lt_rig"]
    times = {}
    drawer = bpy.data.objects["alex_drawer_01"]
    y0 = drawer.location.y
    shots = [  # name, camera, roots shown, rig at, Cycles, samples
        ("hero", "hero", ["set_desk"], desk_pt(0.9, -0.9, 0), True, 160),
        ("front", "front", ["set_desk"], desk_pt(0.9, -0.9, 0), False, 0),
        ("side", "side", ["set_desk"], desk_pt(0.9, -0.9, 0), False, 0),
        ("back", "back", ["set_desk"], desk_pt(0.9, -0.9, 0), False, 0),
        ("top", "top", ["set_desk"], desk_pt(0.9, -0.9, 0), False, 0),
        ("alex", "alex", ["alex"], (0, 0, 0), True, 160),
        ("drawer-open", "open", ["alex"], (0, 0, 0), True, 160),
        ("detail", "detail", ["alex"], (0, 0, 0), True, 128),
        ("plinth", "plinth", ["alex"], (0, 0, 0), True, 128),
        ("corner", "corner", ["set_desk"], desk_pt(0.9, -0.9, 0), True, 128),
        ("led", "led", ["set_desk"], desk_pt(0.9, -0.9, 0), True, 256),
        ("clay", "hero", ["set_desk"], desk_pt(0.9, -0.9, 0), False, 0),
        ("wire", "hero", ["set_desk"], desk_pt(0.9, -0.9, 0), False, 0),
    ]
    for name, cam, groups, at, cyc, spp in shots:
        if ONLY and name not in ONLY:
            continue
        show(groups)
        rig.location = at
        sc.camera = cams[cam]
        drawer.location.y = y0 - (D.DRAWER_TRAVEL if name == "drawer-open" else 0.0)
        undo = None
        if name == "clay":
            looks.clay_on()
        if name == "wire":
            undo = looks.wire_look(thickness=0.0012, skip={"still_floor"})
        if name == "led":
            led_scene(True)
        times[name] = render(os.path.join(FOOT, f"desk-{name}.png"), cyc, spp, name)
        if name == "clay":
            looks.clay_off()
        if undo:
            undo()
        if name == "led":
            led_scene(False)
    drawer.location.y = y0
    show(["alex", "set_desk"])
    rep = json.load(open(REPORT_PATH)) if os.path.exists(REPORT_PATH) else {}
    st = rep.get("stills_s", {})
    st.update(times)
    report(stills_s=st)


# ---------------------------------------------------------------------------
# compare (every angle) and the close-up pair sheets
# ---------------------------------------------------------------------------
ALL_VIEWS = ("photo-3q", "photo-lag", "ikea-unit-front", "ikea-unit-right", "ikea-unit-back", "ikea-unit-top", "ikea-unit-3q",
             "ikea-desk-front", "ikea-desk-right", "ikea-desk-top", "ikea-desk-3q")


def _show_cmp(on):
    for o in bpy.data.objects:
        if o.name.startswith(("cmp200", "lag1")):
            o.hide_render = not on
            o.hide_viewport = not on


def stage_compare():
    show(["alex", "set_desk"])
    _show_cmp(True)
    n = roles()
    views = D.outline_views(n, ALL_VIEWS, out_dir=CMP_DIR)
    for v in views:
        if v["name"] in EXPLAIN:
            v["explain"] = EXPLAIN[v["name"]]
    rep = compare.run(views, CMP_DIR, "desk", look_engine="BLENDER_EEVEE", look_samples=8 if QUICK else 32,
                      title="desk (ALEX and LAGKAPTEN)", log=log)
    _show_cmp(False)
    for p in rep.get("sheets", []):
        if p.endswith("photo-vs-model.jpg"):
            shutil.copy(p, os.path.join(FOOT, "desk-photo-vs-model.jpg"))
    report(compare={r["view"]: [r["iou"], r["status"]] for r in rep["test"]["rows"]}, compare_passed=rep["test"]["passed"])
    log(f"compare {'PASSED' if rep['test']['passed'] else 'FAILED'}: {rep['paths']['md']}")


EXPLAIN = {}

# close-ups: (name, title, compare view, crop box in the photo frame (x0, y0, x1, y1))
CLOSEUPS = [
    ("pull", "finger-pull cut-out (top drawer)", "alex-photo-3q", (380, 470, 790, 640)),
    ("pull-low", "finger-pull cut-out (bottom drawer)", "alex-photo-3q", (380, 1290, 790, 1450)),
    ("gaps", "drawer gaps, left edge", "alex-photo-3q", (240, 600, 520, 900)),
    ("plinth", "plinth, gap and feet", "alex-photo-3q", (240, 1450, 640, 1690)),
    ("plinth-right", "plinth, side and back foot", "alex-photo-3q", (640, 1480, 1160, 1700)),
    ("top-edge", "the unit's top panel and edge", "alex-photo-3q", (250, 300, 900, 560)),
]


def _closeup_render(view, out_png, w, h, label, scale=2, samples=96):
    """Fit the view's camera (cached turn), then render it in Cycles at scale x the photo's size."""
    sc = bpy.context.scene
    e = compare.score_view(dict(view), os.path.join(FOOT, "closeups"), look_engine=None, log=log)
    undo = view["prepare"]()
    sc.camera = bpy.data.objects["cmp_cam"]
    sc.render.resolution_x, sc.render.resolution_y = w * scale, h * scale
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGBA"
    sc.render.engine = "CYCLES"
    gpu()
    sc.cycles.samples = 16 if QUICK else samples
    sc.cycles.use_denoising = True
    sc.render.filepath = out_png
    fl = bpy.data.objects["still_floor"]
    fl.hide_render = True
    with renderqueue.slot(f"desk {label}"):
        t = time.time()
        bpy.ops.render.render(write_still=True)
    log(f"close-up render {label}: {time.time() - t:.1f} s")
    fl.hide_render = False
    undo()
    return e


def stage_closeups():
    """Photo crop beside render crop, same camera and scale (the fitted compare cameras), the renders at
    2x in Cycles: the ALEX packshot (pull, gaps, plinth, top panel) and the LAGKAPTEN packshot (edge band,
    corners); plus the L's inner corner beside the owner's photo (a similar angle, not fitted)."""
    sc = bpy.context.scene
    os.makedirs(os.path.join(FOOT, "closeups"), exist_ok=True)
    bpy.data.objects["lt_rig"].location = (0, 0, 0)
    show(["alex"])
    n = roles()
    sets = []
    v = D.outline_views(n, ("photo-3q",), out_dir=CMP_DIR)[0]
    rp = os.path.join(FOOT, "closeups", "render-alex-2x.png")
    e = _closeup_render(v, rp, 1400, 2000, "closeups alex")
    sets.append({"photo": e["photo"], "transform": e["transform"], "render": rp, "render_scale": 2,
                 "left": "IKEA packshot (crop)", "crops": CLOSEUPS})
    _show_cmp(True)
    v = D.outline_views(n, ("photo-lag",), out_dir=CMP_DIR)[0]
    show([v["lag_variant"]])
    rp = os.path.join(FOOT, "closeups", "render-lag-2x.png")
    bpy.data.objects["lt_rig"].location = D.LAG_AT
    e = _closeup_render(v, rp, 1400, 1400, "closeups lagkapten")
    sets.append({"photo": e["photo"], "transform": e["transform"], "render": rp, "render_scale": 2,
                 "left": "IKEA packshot (crop)", "crops": CLOSEUPS_LAG})
    _show_cmp(False)
    # the L's inner corner (owner's photo for the look; not fitted)
    show(["set_desk"])
    cams = cameras() if "still_cam_corner" not in bpy.data.objects else {"corner": bpy.data.objects["still_cam_corner"]}
    bpy.data.objects["lt_rig"].location = desk_pt(0.9, -0.9, 0)
    sc.render.film_transparent = False
    sc.render.image_settings.color_mode = "RGB"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1200
    sc.camera = cams["corner"]
    cp = os.path.join(FOOT, "closeups", "render-corner.png")
    sc.render.filepath = cp
    with renderqueue.slot("desk corner"):
        bpy.ops.render.render(write_still=True)
    show(["alex", "set_desk"])
    extra = [dict(title="the L's inner corner and the units under it (the owner's desk stands on metal risers; "
                        "plan v3 has none)", left="owner's photo (crop, low resolution)",
                  right="our desk, a similar angle (plan v3)",
                  photo=os.path.join(D.REPO, "docs", "moodboard", "local", "ai-desk-reference-1.jpg"),
                  box=[200, 330, 521, 520], render=cp, rbox=None)]
    spec = {"sets": sets, "extra": extra, "out": os.path.join(FOOT, "desk-closeups.jpg")}
    sp = os.path.join(FOOT, "closeups", "closeups.json")
    with open(sp, "w") as f:
        json.dump(spec, f, indent=1)
    r = subprocess.run([compare.plain_python(), os.path.join(HERE, "desk_blueprint.py"), "closeups", sp],
                       capture_output=True, text=True)
    print(r.stdout[-2000:], r.stderr[-2000:], flush=True)
    log(f"close-up sheet {spec['out']}")


CLOSEUPS_LAG = [
    ("lag-corner", "LAGKAPTEN: front right corner and the edge band", None, (1080, 690, 1380, 880)),
    ("lag-left", "LAGKAPTEN: left end, the edge band's thickness", None, (20, 600, 330, 740)),
]


# ---------------------------------------------------------------------------
# export: rich and lite
# ---------------------------------------------------------------------------
def _ctx(obj, objs=None):
    objs = objs or [obj]
    return bpy.context.temp_override(active_object=obj, object=obj, selected_objects=objs,
                                     selected_editable_objects=objs)


def _export(objs, path):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in objs)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_cameras=False, export_lights=False, export_extras=False)
    return run.glb_stats(path)


def _tree(root):
    return [root] + list(root.children_recursive)


def _image(name, size, data=False):
    im = bpy.data.images.get(name)
    if im is not None:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    if data:
        im.colorspace_settings.name = "Non-Color"
    return im


def _bake(objs, target, kind, samples):
    """Bake into target: 'base' (the base colour through an emission rewire) or 'ao'."""
    sc = bpy.context.scene
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
            rw = None
            if kind == "base":
                out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
                b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
                e = nt.nodes.new("ShaderNodeEmission")
                sock = b.inputs["Base Color"]
                if sock.is_linked:
                    nt.links.new(sock.links[0].from_socket, e.inputs["Color"])
                else:
                    e.inputs["Color"].default_value = tuple(sock.default_value)
                old = out.inputs["Surface"].links[0].from_socket
                nt.links.new(e.outputs[0], out.inputs["Surface"])
                rw = (e, old, out)
            restore.append((mat, tn, rw))
    sc.cycles.samples = samples
    sc.render.bake.margin = 4
    sc.render.bake.use_clear = True
    sc.render.bake.target = "IMAGE_TEXTURES"
    for o in bpy.context.view_layer.objects:
        o.select_set(o in objs)
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


def export_lite(size=1024, ao_size=512):
    """The web model: build(lite=True), one shared ALEX mesh set, square edges except a 1-segment round on
    the top; one 1024 base-colour atlas and a 512 occlusion map (ORM's R; roughness and metal are
    constant on a matte white desk, so they stay material values). The LED keeps its own emissive
    material."""
    import numpy as np
    sc = bpy.context.scene
    prev = sc.render.engine
    coll = _coll("set_desk_lite")
    D.build(lite=True, collection=coll, what=("desk",), suffix="_lite")
    lroot = bpy.data.objects["set_desk_lite"]
    lroot.location = (0, 0, 0)
    dg = bpy.context.evaluated_depsgraph_get()
    top = bpy.data.objects["desk_top_lite"]
    me = bpy.data.meshes.new_from_object(top.evaluated_get(dg))
    top.modifiers.clear()
    old = top.data
    top.data = me
    bpy.data.meshes.remove(old)
    me.name = "desk_top_mesh_lite"
    baked = [top, bpy.data.objects["desk_drawers_01_carcass_lite"]] + \
        [bpy.data.objects[f"desk_drawers_01_drawer_{i:02d}_lite"] for i in range(1, 6)]
    for o in baked:
        lay = o.data.uv_layers.new(name="UVMap")
        o.data.uv_layers.active = lay
    for o in bpy.context.view_layer.objects:
        o.select_set(o in baked)
    bpy.context.view_layer.objects.active = baked[0]
    with _ctx(baked[0], baked):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.004, correct_aspect=True,
                                 scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    # hide everything else (the rich desk sits at DESK_AT; the lite one at the origin)
    hidden = []
    keep = set(o.name for o in _tree(lroot))
    for o in sc.objects:
        if o.type == "MESH" and o.name not in keep and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    sc.render.engine = "CYCLES"
    gpu()
    sc.cycles.use_denoising = False
    world = sc.world
    old_d = world.light_settings.distance
    world.light_settings.distance = 0.06
    base = _image("desk_atlas", size)
    ao = _image("desk_ao_tmp", ao_size, True)
    with renderqueue.slot("desk lite bake"):
        t = time.time()
        _bake(baked, base, "base", 1)
        _bake(baked, ao, "ao", 8 if QUICK else 64)
        log(f"lite bake {time.time() - t:.1f} s")
    world.light_settings.distance = old_d
    for o in hidden:
        o.hide_render = False
    orm = _image("desk_orm", ao_size, True)
    px = np.empty(ao_size * ao_size * 4, np.float32)
    ao.pixels.foreach_get(px)
    a = px.reshape(-1, 4)[:, 0].copy()
    o4 = np.ones((ao_size * ao_size, 4), np.float32)
    o4[:, 0] = 0.35 + 0.65 * a
    o4[:, 1] = 0.5
    o4[:, 2] = 0.0
    orm.pixels.foreach_set(o4.ravel())
    bpy.data.images.remove(ao)
    kb = {}
    for im, fn, q in ((base, "desk_atlas.jpg", 88), (orm, "desk_orm.jpg", 90)):
        p = os.path.join(OUT, fn)
        im.filepath_raw = p
        im.file_format = "JPEG"
        sc.render.image_settings.quality = q
        im.save()
        kb[fn] = round(os.path.getsize(p) / 1024)
    m, nt, b = M._new("mat_desk_lite")
    tb = nt.nodes.new("ShaderNodeTexImage")
    tb.image = base
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = orm
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sep.inputs[0])
    nt.links.new(tb.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.5
    gg = nt.nodes.new("ShaderNodeGroup")
    gg.node_tree = _gltf_group()
    nt.links.new(sep.outputs[0], gg.inputs["Occlusion"])
    M._set(b, spec=0.5)
    for o in baked:
        o.data.materials.clear()
        o.data.materials.append(m)
    sc.render.engine = prev
    # the lite tree takes the real names while it is exported
    rich = _tree(bpy.data.objects["set_desk"])
    for o in rich:
        o.name = o.name + "_rich"
    lite = _tree(lroot)
    for o in lite:
        o.name = o.name[:-5]
    info = {"images_kb": kb}

    def undo():
        for o in lite:
            o.name = o.name + "_lite"
        for o in rich:
            o.name = o.name[:-5]
    return lite, undo, info


def stage_export():
    t = time.time()
    root = bpy.data.objects["set_desk"]
    at = root.location.copy()
    root.location = (0, 0, 0)
    rich_objs = _tree(root)
    rich_tris = rendered_triangles([o.name for o in rich_objs])
    rich = _export(rich_objs, os.path.join(OUT, "desk-rich.glb"))
    log(f"GLB rich: {rich['kb']} KB, {rich['triangles']} stored / {rich_tris} rendered triangles")
    lite_objs, undo, info = export_lite()
    lite_tris = rendered_triangles([o.name for o in lite_objs])
    per = {}
    for o in lite_objs:
        if o.type == "MESH" and o.data.name not in per:
            per[o.data.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)
    lite = _export(lite_objs, os.path.join(OUT, "desk-lite.glb"))
    log(f"GLB lite: {lite['kb']} KB, {lite['triangles']} stored / {lite_tris} rendered triangles")
    # a still of the lite model (EEVEE), same hero camera, at the rich desk's place
    lroot = next(o for o in lite_objs if o.parent is None)
    lroot.location = at
    show([lroot.name])
    cams = {"hero": bpy.data.objects.get("still_cam_hero")} if "still_cam_hero" in bpy.data.objects else cameras()
    bpy.context.scene.camera = cams["hero"]
    bpy.data.objects["lt_rig"].location = desk_pt(0.9, -0.9, 0)
    render(os.path.join(FOOT, "desk-lite.png"), False, 0, "lite")
    undo()
    root.location = at
    for fn in ("desk_atlas.jpg", "desk_orm.jpg"):
        shutil.copy(os.path.join(OUT, fn), os.path.join(FOOT, fn.replace("_", "-")))
    report(glb={"rich": rich, "rich_rendered_tris": rich_tris, "lite": lite, "lite_rendered_tris": lite_tris,
                "lite_per_mesh": per, "lite_info": info, "export_s": round(time.time() - t, 1)})


def main():
    stages = next((a for a in ARGS if not a.startswith("--")), "build,stills,compare,closeups,export").split(",")
    os.makedirs(FOOT, exist_ok=True)
    t0 = time.time()
    if "build" in stages:
        stage_build()
    else:
        open_blend()
    if "stills" in stages:
        stage_stills()
    if "compare" in stages:
        stage_compare()
    if "closeups" in stages:
        stage_closeups()
    if "export" in stages:
        stage_export()
    log(f"done {stages} in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
    bpy.ops.wm.quit_blender()
