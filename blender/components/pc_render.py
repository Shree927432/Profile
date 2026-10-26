"""pc: build, stills, the every-angle compare, close-up pairs and the GLBs (component, 2026-10-24).

Always headless:

    B=/Applications/Blender.app/Contents/MacOS/Blender
    $B -b --factory-startup --python blender/components/pc_render.py -- build,look        quick EEVEE looks
    $B -b --factory-startup --python blender/components/pc_render.py -- stills [--only=hero,dark] [--quick]
    ... -- compare [--views=gpu-front]   ... -- closeups   ... -- export
    default: build,stills,compare,closeups,export

Output: blender/out/components/pc.blend, pc-rich.glb, pc-lite.glb;
video-local/footage/2026-10-24-components/pc/ (stills, compare/, closeups/, NOTE.md).
Run `/opt/anaconda3/bin/python3 blender/components/pc.py refs` once first (the traced cut-outs).
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
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
import pc as K  # noqa: E402
from lib import compare, looks, materials as M, renderqueue, run  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
QUICK = "--quick" in ARGS
ONLY = next((a.split("=", 1)[1].split(",") for a in ARGS if a.startswith("--only=")), None)
VIEWS = next((a.split("=", 1)[1] for a in ARGS if a.startswith("--views=")), None)
OUT = os.path.join(K.BLENDER_DIR, "out", "components")
BLEND = os.path.join(OUT, "pc.blend")
FOOT = K.FOOTAGE
CMP_DIR = os.path.join(FOOT, "compare")
REPORT_PATH = os.path.join(FOOT, "pc-report.json")
EXPOSURE = -0.35
CENTRE = Vector((0, 0, K.CASE_H / 2))


def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} pc: {msg}", flush=True)


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


def eevee_glass():
    """EEVEE: ray-traced refraction, so the glass reads as glass in the compare looks too."""
    try:
        bpy.context.scene.eevee.use_raytracing = True
    except AttributeError:
        pass


def gpu():
    sc = bpy.context.scene
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "METAL"
    sc.cycles.device = "CPU" if "--cpu" in ARGS else "GPU"


def build_studio():
    """Neutral studio on a rig empty (soft key, fill, rim, top, front), light grey world and floor."""
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
        o.rotation_euler = (-Vector(loc) + Vector((0, 0, 0.25))).to_track_quat("-Z", "Y").to_euler()
        return o
    area("lt_key", (-1.6, -1.8, 1.9), 1.6, 300, "#fff8f0")
    area("lt_fill", (1.9, -1.2, 0.9), 1.4, 110, "#eef3ff")
    area("lt_rim", (0.8, 2.0, 1.7), 1.3, 170)
    area("lt_top", (0.0, -0.2, 2.6), 1.8, 140)
    area("lt_front", (-0.3, -2.6, 0.8), 2.0, 150)
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
    coll = _coll("pc")
    n = K.build(collection=coll)
    build_studio()
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    log(f"built in {time.time() - t:.1f} s: {len(n['all'])} meshes, saved {BLEND}")
    report(names=n, tris_rich=rendered_triangles(n["all"]))
    return n


def roles():
    n = {}
    objs = bpy.data.objects
    n["case"] = [x for x in ("rig_case", "rig_case_side", "rig_case_glass", "rig_case_brand") if x in objs]
    n["case_all"] = n["case"]
    n["gpu"] = [x for x in ("rig_gpu", "rig_gpu_light", "rig_gpu_fan_01", "rig_gpu_fan_02") if x in objs]
    n["gpu_all"] = n["gpu"]
    n["fans"] = ["rig_fans"] + [x for x in ("rig_glow_strips",) if x in objs] + sorted(o.name for o in objs if o.name.startswith("rig_fan_"))
    n["static"] = ["rig_static"]
    n["pc_all"] = n["case"] + n["gpu"] + n["fans"] + n["static"]
    n["all"] = n["pc_all"]
    return n


def open_blend():
    bpy.ops.wm.open_mainfile(filepath=BLEND)


def rendered_triangles(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    t = 0
    for nm in objs:
        o = bpy.data.objects.get(nm)
        if o is None or o.type != "MESH":
            continue
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        t += len(me.loop_triangles)
        o.evaluated_get(dg).to_mesh_clear()
    return t


# ---------------------------------------------------------------------------
# stills
# ---------------------------------------------------------------------------
def cameras():
    coll = _coll("still_cameras")
    cam = looks.camera
    c = {}
    zc = K.CASE_H / 2
    c["hero"] = cam("still_cam_hero", (-0.98, -1.22, 0.70), (0.0, 0.02, zc - 0.02), lens=40, coll=coll)
    c["side"] = cam("still_cam_side", (-1.75, 0.0, 0.27), (0.0, 0.0, zc), lens=50, coll=coll)
    c["front"] = cam("still_cam_front", (0.0, -1.85, 0.27), (0.0, 0.0, zc), lens=50, coll=coll)
    c["back"] = cam("still_cam_back", (1.05, 1.25, 0.66), (0.0, 0.0, zc - 0.02), lens=40, coll=coll)
    cd = bpy.data.cameras.new("still_cam_top")
    cd.type, cd.ortho_scale = "ORTHO", 0.95
    top = bpy.data.objects.new("still_cam_top", cd)
    coll.objects.link(top)
    top.location = (0, 0, 2.0)
    c["top"] = top
    c["glass"] = cam("still_cam_glass", (-0.62, -0.75, 0.62), (-0.10, -0.12, 0.40), lens=45, coll=coll)
    c["io"] = cam("still_cam_io", (-0.12, -0.62, 0.075), (0.09, -0.24, 0.03), lens=55, coll=coll)
    c["inside"] = cam("still_cam_inside", (-0.78, -0.42, 0.40), (0.0, 0.03, 0.24), lens=50, coll=coll)
    c["rear"] = cam("still_cam_rear", (1.30, 0.05, 0.25), (0.10, 0.05, 0.24), lens=50, coll=coll)
    c["dark"] = cam("still_cam_dark", (-1.10, -1.05, 0.55), (0.0, 0.03, zc - 0.03), lens=40, coll=coll)
    c["gpu"] = cam("still_cam_gpu", (0.42, -0.62, 1.95), (0.15, 0.06, 1.48), lens=50, coll=coll)
    c["gpu_fans"] = cam("still_cam_gpu_fans", (0.20, -0.62, 1.60), (0.152, 0.0, 1.562), lens=50, coll=coll)
    c["gpu_edge"] = cam("still_cam_gpu_edge", (0.36, -0.38, 1.56), (0.24, 0.0, 1.50), lens=70, coll=coll)
    c["fan"] = cam("still_cam_fan", (-0.58, -0.50, 0.24), (-0.02, 0.0, 0.15), lens=45, coll=coll)
    return c


def show(names):
    keep = set(names)
    for o in bpy.data.objects:
        if o.type == "MESH" and not o.name.startswith("still_"):
            o.hide_render = o.name not in keep


def dark_room(on):
    """The lights-on still: studio dimmed to a faint blue ambient, the fans and the card's bar lit."""
    sc = bpy.context.scene
    for n in ("lt_key", "lt_fill", "lt_rim", "lt_top", "lt_front"):
        L = bpy.data.objects[n].data
        L["e0"] = L.get("e0", L.energy)
        L.energy = L["e0"] * (0.02 if on else 1.0)
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = M.rgba("#1a2433" if on else "#d9dadd")
    bg.inputs["Strength"].default_value = 0.08 if on else 0.55
    fl = bpy.data.objects["still_floor"].data.materials[0]
    b = next(n for n in fl.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = M.rgba("#2d3138" if on else "#c9cacd")
    for mn, s in (("mat_pc_fan_light", 14.0), ("mat_gpu_light", 9.0)):
        m = bpy.data.materials[mn]
        e = next(n for n in m.node_tree.nodes if n.type == "EMISSION")
        e["s0"] = e.get("s0", e.inputs["Strength"].default_value)
        e.inputs["Strength"].default_value = s if on else e["s0"]


def render(path, cycles, samples, label, w=1920, h=1080):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGB"
    sc.render.filepath = path
    t = time.time()
    cycles = cycles and "--eevee" not in ARGS
    if cycles:
        sc.render.engine = "CYCLES"
        gpu()
        sc.cycles.samples = 24 if QUICK else samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 10
        sc.cycles.transmission_bounces = 10
        sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
        with renderqueue.slot(f"pc {label}"):
            t = time.time()
            bpy.ops.render.render(write_still=True)
    else:
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = 8 if QUICK else 48
        bpy.ops.render.render(write_still=True)
    dt = round(time.time() - t, 1)
    log(f"still {label}: {dt} s ({'Cycles' if cycles else 'EEVEE'})")
    return dt


def gpu_alone(on, pose="flat"):
    """Lift the card out of the case for its own stills (flat, backplate up, or "front": standing, fans
    toward -Y; 1.5 m up), or put it back."""
    g = bpy.data.objects["rig_gpu_root"]
    if on:
        g["m0"] = [list(r) for r in g.matrix_world]
        R = Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1))).transposed().to_4x4()
        if pose == "front":
            R = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0))).transposed().to_4x4()
        R.translation = Vector((0, 0, 1.5))
        g.matrix_world = R
    else:
        g.matrix_world = Matrix(g["m0"])
    bpy.context.view_layer.update()


def stage_stills(only=None):
    sc = bpy.context.scene
    cams = cameras()
    n = roles()
    times = {}
    pc_names = n["pc_all"]
    shots = [  # name, camera, shown, Cycles, samples
        ("hero", "hero", pc_names, True, 256),
        ("side", "side", pc_names, True, 160),
        ("front", "front", pc_names, True, 128),
        ("back", "back", pc_names, True, 128),
        ("top", "top", pc_names, True, 96),
        ("glass-corner", "glass", pc_names, True, 160),
        ("io", "io", pc_names, True, 128),
        ("inside", "inside", pc_names, True, 160),
        ("rear-chamber", "rear", [x for x in pc_names if x != "rig_case_side"], True, 128),
        ("fan", "fan", pc_names, True, 128),
        ("gpu", "gpu", n["gpu"], True, 160),
        ("gpu-fans", "gpu_fans", n["gpu"], True, 128),
        ("gpu-edge", "gpu_edge", n["gpu"], True, 128),
        ("dark", "dark", pc_names, True, 256),
        ("clay", "hero", [x for x in pc_names if x != "rig_case_glass"], False, 0),
        ("wire", "hero", pc_names, False, 0),
    ]
    for name, cam, shown, cyc, spp in shots:
        if only and name not in only:
            continue
        show(shown + ["still_floor"])
        if name.startswith("gpu"):
            gpu_alone(True, "front" if name == "gpu-fans" else "flat")
            bpy.data.objects["lt_rig"].location = (0.15, 0, 1.25)
            dim = K.product_light(True)
        sc.camera = cams[cam]
        undo = None
        if name == "clay":
            looks.clay_on()
        if name == "wire":
            undo = looks.wire_look(thickness=0.0006, skip={"still_floor"})
        if name == "dark":
            dark_room(True)
        times[name] = render(os.path.join(FOOT, f"pc-{name}.png"), cyc, spp, name)
        if name == "clay":
            looks.clay_off()
        if undo:
            undo()
        if name == "dark":
            dark_room(False)
        if name.startswith("gpu"):
            gpu_alone(False)
            K.product_light(False, dim)
            bpy.data.objects["lt_rig"].location = (0, 0, 0)
    show(pc_names + ["still_floor"])
    rep = json.load(open(REPORT_PATH)) if os.path.exists(REPORT_PATH) else {}
    st = rep.get("stills_s", {})
    st.update(times)
    report(stills_s=st)


def stage_look():
    """Quick EEVEE looks at 960 x 540 for review while modelling."""
    global QUICK
    sc = bpy.context.scene
    cams = cameras()
    n = roles()
    d = os.path.join(FOOT, "look")
    os.makedirs(d, exist_ok=True)
    for name, cam, shown in (("hero", "hero", n["pc_all"]), ("side", "side", n["pc_all"]),
                             ("back", "back", n["pc_all"]), ("inside", "inside", n["pc_all"]),
                             ("rear", "rear", [x for x in n["pc_all"] if x != "rig_case_side"]),
                             ("gpu", "gpu", n["gpu"]), ("gpu_fans", "gpu_fans", n["gpu"]), ("io", "io", n["pc_all"])):
        if ONLY and name not in ONLY:
            continue
        show(shown + ["still_floor"])
        if name.startswith("gpu"):
            gpu_alone(True, "front" if name == "gpu_fans" else "flat")
            bpy.data.objects["lt_rig"].location = (0.15, 0, 1.2)
        sc.camera = cams[cam]
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = 16
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
        sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGB"
        sc.render.filepath = os.path.join(d, f"look-{name}.png")
        bpy.ops.render.render(write_still=True)
        if name.startswith("gpu"):
            gpu_alone(False)
            bpy.data.objects["lt_rig"].location = (0, 0, 0)
    show(n["pc_all"] + ["still_floor"])
    log(f"looks in {d}")


# ---------------------------------------------------------------------------
# compare and close-ups
# ---------------------------------------------------------------------------
EXPLAIN = {
    "case-back-3q": ("KitGuru's close hand-held shot from behind (wide lens): the same camera limit as the front "
                     "three-quarter; the edges agree within a few pixels; the outline differs most at the feet, which "
                     "the photo shows from very low"),
    "gpu-back": ("NVIDIA's backplate render: the shroud fits; the bracket and the board's edge above it do not "
                 "both fit one camera with the fan side (0.982); the photo's board edge is longer, with a second "
                 "tab, ours is the fingers' length only"),
    "gpu-3q-io": ("NVIDIA's three-quarter product render: the card's ends are fuller rounded 'pill' caps in the "
                  "photo and its long edges dip in the middle; our ends are a 6 mm round on a straight wall"),
    "gpu-3q-end": ("as gpu-3q-io, seen from the far end, where the photo's rounded end cap is largest"),
    "case-3q": ("KitGuru's close, low, hand-held shot: no single pinhole camera fits it better than about 0.96 "
                "(its lens fit is not significant, roll did not help); the edges agree within a few pixels, the "
                "five other case views pass"),
}


def stage_compare():
    eevee_glass()
    show(roles()["pc_all"] + ["still_floor"])
    bpy.data.objects["still_floor"].hide_render = True
    views = K.outline_views(roles())
    if VIEWS:
        views = [v for v in views if v["name"] in VIEWS.split(",")]
    for v in views:
        if v["name"] in EXPLAIN:
            v["explain"] = EXPLAIN[v["name"]]
    out = CMP_DIR
    rep = compare.run(views, out, "pc", look_engine="BLENDER_EEVEE", look_samples=8 if QUICK else 32,
                      title="pc (O11 Vision and RTX 5090 FE)", log=log)
    bpy.data.objects["still_floor"].hide_render = False
    for p in rep.get("sheets", []):
        if p.endswith("photo-vs-model.jpg"):
            shutil.copy(p, os.path.join(FOOT, "pc-photo-vs-model.jpg"))
    report(compare={r["view"]: [r["iou"], r["status"]] for r in rep["test"]["rows"]}, compare_passed=rep["test"]["passed"])
    log(f"compare {'PASSED' if rep['test']['passed'] else 'FAILED'}: {rep['paths']['md']}")


def stage_export():
    pass


def main():
    stages = next((a for a in ARGS if not a.startswith("--")), "build,stills,compare,closeups,export").split(",")
    os.makedirs(FOOT, exist_ok=True)
    t0 = time.time()
    if "build" in stages:
        stage_build()
    else:
        open_blend()
    if "look" in stages:
        stage_look()
    if "stills" in stages:
        stage_stills(ONLY)
    if "compare" in stages:
        stage_compare()
    if "closeups" in stages:
        import pc_closeups
        pc_closeups.stage_closeups(sys.modules[__name__])
    if "export" in stages:
        import pc_export
        pc_export.stage_export(sys.modules[__name__])
    log(f"done {stages} in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
    bpy.ops.wm.quit_blender()
