"""Build the room from scratch, check its names, save the .blend, export the GLB.

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/build.py
    (add -b after Blender to run headless; options after `--`: a stage list, see below)

Stages (default build,export): `build` makes the scene and saves blender/out/room.blend;
`export` (opens the .blend when run alone) joins each root's static parts, exports
scene/assets/room.glb and checks it. Progress lines start with MILESTONE; a report goes
to blender/out/room-build-report.json.

What is built (Phase 4 Step 1, the room shell):
  set_room     props/set_room.py     floor, walls, ceiling, skirting, window and door openings
  set_desk     props/set_desk.py     desk, keyboard, mouse
  obj_monitor  props/obj_monitor.py  body, screen (with the TOP test texture), stand
  obj_piano    props/obj_piano.py    the approved piano, in the .blend and the renders only;
                                     the GLB carries a stand-in box (the piano's web export
                                     is still an open question for the owner)
  guitar_02    props/guitar_02.py    the Woodstock Strat on its hanger under obj_guitars; the
                                     .blend has the rich model, the GLB its lite web model
                                     (about 6k triangles, one baked atlas)
  guitar_04    props/guitar_04.py    Number One in rack slot 1 (guitar_02's Strat builders under
                                     guitar_04's spec); rich in the .blend, lite in the GLB
  the rest     props/footprints.py   named footprint shapes for every other root on the plan
Lights, the sky plane and the review cameras (lib/looks.py) are Blender only.
"""
import json
import math
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import constants as C, geo, looks, materials as M, names, run  # noqa: E402
from props import footprints, guitar_02, guitar_04, obj_monitor, obj_piano, set_desk, set_room  # noqa: E402

ARGS = run.args()
STAGE = next((a for a in ARGS if not a.startswith("--")), "build,export")
STAGES = set(STAGE.split(","))
BLEND = os.path.join(C.OUT, "room.blend")
GLB = os.path.join(C.REPO, "scene", "assets", "room.glb")
REPORT_PATH = os.path.join(C.OUT, "room-build-report.json")
REPORT = {}
T0 = time.time()

# Roots in the GLB, in build order. obj_piano stays out (a stand-in goes in its place).
EXPORT_ROOTS = ["set_room", "set_desk", "obj_monitor"]
KEEP = {"monitor_body", "monitor_screen", "monitor_static",      # code-touched or already the static
        "guitar_02_body", "guitar_02_strings", "guitar_04_body", "guitar_04_strings"}


def skipped(o):
    """The rich guitars stay in the .blend; their lite copies go in the GLB."""
    return o.name.startswith(("guitar_02_part_", "guitar_04_part_")) or o.name.endswith("_rich")


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
    scene.world.use_nodes = True
    return scene


def place_piano(root):
    p = C.LAYOUT["piano"]
    root.location = (p["x"], p["y"], 0.0)
    root.rotation_euler = (0, 0, math.radians(p["yaw"]))
    for o in root.children:
        if o.name.startswith("piano_bench"):
            o.location.y += p["bench_in"]          # at rest, pushed in under the keys


def review_cameras():
    coll = bpy.data.collections.new("still_cameras")
    bpy.context.scene.collection.children.link(coll)
    h = C.HERO
    looks.camera("still_cam_home", h["pos"], h["target"], vfov=h["vfov"], coll=coll)
    mon = C.LAYOUT["monitor"]
    looks.camera("still_cam_phone", h["pos"], (mon["x"], mon["y"], mon["z"]), vfov=h["phone_vfov"], coll=coll)


def stage_build():
    run.log("build: starting from an empty scene")
    scene = clear_scene()
    yield
    t = time.time()
    set_room.build()
    run.log("build: set_room (floor, walls, ceiling, skirting, openings)")
    yield
    set_desk.build()
    run.log("build: set_desk")
    yield
    obj_monitor.build()
    run.log("build: obj_monitor")
    yield
    gen = obj_piano.build_steps()
    try:
        while True:
            next(gen)
    except StopIteration as s:
        place_piano(s.value)
    run.log("build: obj_piano (the approved model)")
    yield
    for label in footprints.build_steps():
        run.log(f"build: footprint {label[6:]}")
        yield
    og = bpy.data.objects["obj_guitars"]
    gen = guitar_02.build_steps(parent=og, collection=bpy.data.collections["obj_guitars"])
    try:
        while True:
            run.log(f"build: guitar_02 {next(gen)}")
            yield
    except StopIteration as s:
        g2 = guitar_02.place_on_wall(s.value)
    guitar_02.build_hanger(g2, bpy.data.collections["obj_guitars"], parent=og)
    run.log("build: guitar_02 on its hanger")
    yield
    gen = guitar_04.build_steps(parent=og, collection=bpy.data.collections["obj_guitars"])
    try:
        while True:
            run.log(f"build: guitar_04 {next(gen)}")
            yield
    except StopIteration as s:
        REPORT["guitar_04_rack"] = guitar_04.place_in_rack(s.value, slot=0)
    run.log(f"build: guitar_04 in rack slot 1 ({REPORT['guitar_04_rack']})")
    yield
    looks.build_lights()
    review_cameras()
    scene.camera = bpy.data.objects["still_cam_home"]
    run.show_in_viewport()
    REPORT["build_s"] = round(time.time() - t, 1)
    REPORT["names"] = check_names()
    os.makedirs(C.OUT, exist_ok=True)
    from lib.blendfile import pack_and_save
    pack_and_save(BLEND, compress=True)
    run.log(f"built in {REPORT['build_s']} s, names checked, saved {BLEND}")
    yield


def check_names():
    objs = bpy.data.objects
    out = {"set_room": names.check_set(objs["set_room"]), "set_desk": names.check_set(objs["set_desk"]),
           "obj_monitor": names.check_export(objs["obj_monitor"]),
           "guitar_02": guitar_02.check(objs["guitar_02"]), "guitar_04": guitar_04.check(objs["guitar_04"])}
    export, undo = obj_piano.export_prep(objs["obj_piano"])
    try:
        out["obj_piano"] = names.check_export(objs["obj_piano"], multi_material_ok=("piano_static",))
    finally:
        undo()
    for o in objs:
        if o.name.startswith(("monitor_glow", "studio_lightstick_glow")):
            raise AssertionError(f"{o.name} is made by code; Blender must not use it")
    return {k: ({"listed": v["listed"], "found": v["found"]} if "listed" in v else v) for k, v in out.items()}


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------
def word(root_name):
    return root_name.split("_", 1)[1]


def piano_standin():
    """A black box in the piano's place for the GLB: case, keybed, toe blocks."""
    P = C.PIANO
    r, coll = geo.root("set_piano_standin")
    m = bpy.data.materials.get("mat_standin_piano") or M.principled("mat_standin_piano", base="#0b0b0c",
                                                                      rough=0.25, coat=1.0, coat_rough=0.05)
    hw = P["width"] / 2
    specs = [(-hw, hw, P["panel_face_y"], P["lid_over_back"], P["panel_bottom"], P["case_top"] + P["lid_t"]),
             (-hw + 0.03, hw - 0.03, P["slip_front_y"], P["panel_face_y"], P["slip_top"] - 0.05, C.KT),
             (-hw, hw, P["lower_face_y"], 0.0, P["floor_gap"], P["panel_bottom"])]
    specs += [(s * P["toe_x"] - P["toe_w"] / 2, s * P["toe_x"] + P["toe_w"] / 2, P["toe_front_y"], P["toe_back_y"],
               0.0, P["cheek_top"]) for s in (-1, 1)]
    o = geo.boxes("piano_standin_box", specs, collection=coll, parent=r, material=m)
    p = C.LAYOUT["piano"]
    r.location = (p["x"], p["y"], 0.0)
    r.rotation_euler = (0, 0, math.radians(p["yaw"]))
    return r, [o]


def web_prep(objs, footprint=()):
    """Two changes for the web copy only, undone after the export:
    - bevels of 2 mm or less are switched off (invisible at web size; they were most of the
      triangles: the keycaps alone had 20k), and every bevel on a footprint,
    - a procedural base colour (wood grain, stone) cannot travel in a GLB and arrives white,
      so it is unplugged and the material's mean colour (its viewport colour) is used.
      Image textures and vertex colours stay. The bake (Phase 4 Step 6) replaces both."""
    mods, links = [], []
    for o in objs:
        if o.type != "MESH":
            continue
        for m in o.modifiers:
            if m.type == "BEVEL" and (m.width <= 0.002 or o.name in footprint) and m.show_viewport:
                m.show_viewport = False
                mods.append(m)
    seen = set()
    for o in objs:
        if o.type != "MESH":
            continue
        for mat in o.data.materials:
            if mat is None or mat.name in seen or not mat.node_tree:
                continue
            seen.add(mat.name)
            b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            sock = b.inputs["Base Color"] if b else None
            if sock is None or not sock.is_linked:
                continue
            ln = sock.links[0]
            if ln.from_node.type in ("TEX_IMAGE", "VERTEX_COLOR"):
                continue
            links.append((mat, ln.from_socket, sock, tuple(sock.default_value)))
            mat.node_tree.links.remove(ln)
            sock.default_value = tuple(mat.diffuse_color)

    def undo():
        for m in mods:
            m.show_viewport = True
        for mat, src, dst, old in links:
            dst.default_value = old
            mat.node_tree.links.new(src, dst)
    return undo


def prep_root(root_name, temp):
    """Copies of a root's static meshes joined into `<word>_static`. Returns objects to export."""
    bpy.context.view_layer.update()             # matrix_world of roots placed this session
    root = bpy.data.objects[root_name]
    tree = [o for o in names.descendants(root) if not skipped(o)]
    keep = [o for o in tree if o.type == "EMPTY" or o.name in KEEP]
    static = [o for o in tree if o.type == "MESH" and o.name not in KEEP and not o.name.startswith("bake_")]
    out = [root] + keep
    if static:
        copies = []
        for o in static:
            c = o.copy()
            c.data = o.data.copy()
            c.name = o.name + "_tmp"
            root.users_collection[0].objects.link(c)      # same parent, basis and parent inverse
            copies.append(c)
        # bake modifiers into the copies before joining (join drops them otherwise)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        for c in copies:
            if c.modifiers:
                ev = c.evaluated_get(dg)
                me = bpy.data.meshes.new_from_object(ev)
                c.modifiers.clear()
                old = c.data
                c.data = me
                bpy.data.meshes.remove(old)
        j = geo.join(copies, word(root_name) + "_static")
        temp.append(j)
        out.append(j)
    return out


def stage_export():
    if "build" not in STAGES:
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    run.log("export: guitar_02 web model (lite parts, baked atlas)")
    lite_objs, undo_lite, lite_info = guitar_02.export_lite(bpy.data.objects["guitar_02"])
    REPORT["guitar_02_lite"] = lite_info
    yield
    run.log("export: guitar_04 web model (lite parts, baked atlas)")
    lite4, undo_lite4, lite_info4 = guitar_04.export_lite(bpy.data.objects["guitar_04"])
    REPORT["guitar_04_lite"] = lite_info4
    yield
    run.log("export: joining static parts")
    temp = []
    roots = EXPORT_ROOTS + [n for n, _ in footprints.ROOTS] if footprints.ROOTS else None
    if roots is None:                                   # opened from the .blend
        roots = EXPORT_ROOTS + [o.name for o in bpy.data.objects if o.parent is None and o.type == "EMPTY"
                                and o.name.startswith(("obj_", "set_")) and o.name not in EXPORT_ROOTS
                                and o.name != "obj_piano"]
    sr, _ = piano_standin()
    temp.append(sr)
    sources = [d for rn in roots + ["set_piano_standin"] for d in names.descendants(bpy.data.objects[rn])]
    fp = {d.name for rn in roots if rn not in EXPORT_ROOTS for d in names.descendants(bpy.data.objects[rn])}
    undo_web = web_prep(sources, fp)
    export = []
    for rn in roots + ["set_piano_standin"]:
        export += prep_root(rn, temp)
    for o in bpy.data.objects:
        o.select_set(False)
    for o in export:
        o.select_set(True)
    os.makedirs(os.path.dirname(GLB), exist_ok=True)
    kw = dict(filepath=GLB, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
              export_cameras=False, export_lights=False, export_extras=False, export_image_format="AUTO")
    try:
        bpy.ops.export_scene.gltf(**kw, export_vertex_color="MATERIAL")
    except TypeError:
        bpy.ops.export_scene.gltf(**kw)
    undo_web()
    undo_lite4()
    undo_lite()
    gone = {c.name for o in temp for c in [o] + names.descendants(o)}
    for n in gone:
        c = bpy.data.objects[n]
        data = c.data if c.type == "MESH" else None
        bpy.data.objects.remove(c)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)
    for cn in ("set_piano_standin",):
        if cn in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections[cn])
    st = run.glb_stats(GLB)
    REPORT["glb"] = {k: v for k, v in st.items() if k != "node_names"}
    REPORT["glb"]["path"] = GLB
    REPORT["glb"]["check"] = check_glb(GLB, st)
    run.log(f"GLB exported: {st['kb']} KB, {st['triangles']} triangles, {st['meshes']} meshes, "
            f"{st['nodes']} nodes: {GLB}")
    yield


def check_glb(path, st):
    """The names the room code relies on are in the GLB, clean, and the screen is a textured quad."""
    import struct
    with open(path, "rb") as f:
        f.read(12)
        clen, _ = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(clen))
    nodes = {n.get("name"): n for n in doc["nodes"]}
    need = ["set_room", "room_view", "room_view_target", "obj_monitor", "monitor_body", "monitor_screen",
            "monitor_static", "monitor_view", "monitor_view_target", "set_desk", "desk_static", "room_static",
            "obj_guitars", "guitar_02", "guitar_02_body", "guitar_02_strings", "guitar_04", "guitar_04_body",
            "guitar_04_strings", "guitars_static"]
    missing = [n for n in need if n not in nodes]
    bad = [n for n in nodes if not names.NAME_RE.match(n or "")]
    leaked = [n for n in nodes if n.startswith(("lt_", "video_", "still_", "bake_"))]
    scr = doc["meshes"][nodes["monitor_screen"]["mesh"]]["primitives"]
    mat = doc["materials"][scr[0]["material"]]
    res = {"missing": missing, "bad_names": bad, "leaked": leaked, "screen_primitives": len(scr),
           "screen_has_uv": "TEXCOORD_0" in scr[0]["attributes"],
           "screen_textured": "baseColorTexture" in mat.get("pbrMetallicRoughness", {}),
           "room_view": nodes["room_view"].get("translation"),
           "room_view_target": nodes["room_view_target"].get("translation")}
    if not missing:
        gb = doc["meshes"][nodes["guitar_02_body"]["mesh"]]["primitives"]
        gs = doc["meshes"][nodes["guitar_02_strings"]["mesh"]]["primitives"]
        gm = doc["materials"][gb[0]["material"]]
        res.update(guitar_02_body_primitives=len(gb), guitar_02_strings_primitives=len(gs),
                   guitar_02_textured="baseColorTexture" in gm.get("pbrMetallicRoughness", {}),
                   guitar_02=nodes["guitar_02"].get("translation"),
                   guitar_02_strings_origin=nodes["guitar_02_strings"].get("translation"))
        gb4 = doc["meshes"][nodes["guitar_04_body"]["mesh"]]["primitives"]
        gs4 = doc["meshes"][nodes["guitar_04_strings"]["mesh"]]["primitives"]
        gm4 = doc["materials"][gb4[0]["material"]]
        res.update(guitar_04_body_primitives=len(gb4), guitar_04_strings_primitives=len(gs4),
                   guitar_04_textured="baseColorTexture" in gm4.get("pbrMetallicRoughness", {}),
                   guitar_04=nodes["guitar_04"].get("translation"), guitar_04_rotation=nodes["guitar_04"].get("rotation"))
    ok = not missing and not bad and not leaked and len(scr) == 1 and res["screen_has_uv"] and res["screen_textured"]
    ok = ok and res.get("guitar_02_body_primitives") == 1 and res.get("guitar_02_strings_primitives") == 1 \
        and res.get("guitar_02_textured")
    ok = ok and res.get("guitar_04_body_primitives") == 1 and res.get("guitar_04_strings_primitives") == 1 \
        and res.get("guitar_04_textured")
    res["ok"] = ok
    if not ok:
        raise AssertionError(f"GLB check failed: {res}")
    return res


def job():
    if "build" in STAGES:
        yield from stage_build()
    if "export" in STAGES:
        yield from stage_export()
    REPORT["total_s"] = round(time.time() - T0, 1)
    with open(REPORT_PATH, "w") as f:
        json.dump(REPORT, f, indent=2)
    print(json.dumps(REPORT, indent=2), flush=True)
    run.log(f"done in {REPORT['total_s']} s")
    yield
    if "--stay" not in ARGS:
        bpy.ops.wm.quit_blender()


run.drive(job())
