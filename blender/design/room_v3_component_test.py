"""Test assembly (2026-10-26): plan v3 room with the approved components in place of their stand-ins.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/design/room_v3_component_test.py

Not the room rebuild. Reuses the v3 blockout's build functions (its source is exec'd without its
final main() call, so that file is untouched), appends the rich components from
blender/out/components/*.blend, places them at plan v3's numbers, imports the lite piano and
guitars 02 and 04, then:
  - saves blender/out/room_v3_component_test.blend (HERO_V3 active; INTRO, ABOUT, TOP, ...);
  - renders EEVEE stills into video-local/footage/2026-10-26-component-test/;
  - writes fit-check.json there (overlaps, wall gaps, heights);
  - swaps in the lite GLBs and exports room-v3-test.glb (AI-lab corner and the room shell).
ONLY=hero,about,... limits the renders; SKIP_GLB=1 skips the export.
PC_YAW=0 renders the old PC orientation as an option, with a -pc0 suffix; it does not save the .blend,
overwrite fit-check.json or export. (2026-10-26: plan v3 now has the desk 3 cm off the walls and the
PC at yaw 90; this script reads both from plan_v3.)
"""
import json
import math
import os
import subprocess
import sys
import types

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.join(HERE, "..")
sys.path.insert(0, BL)
from lib import plan_v3 as P  # noqa: E402

# --- the blockout's helpers, without running its main()
_src_path = os.path.join(HERE, "room_plan_v3_blockout.py")
_src = open(_src_path).read()
_src = _src[: _src.rindex("\nmain()")]
BO = types.ModuleType("room_plan_v3_blockout")
BO.__file__ = _src_path
exec(compile(_src, _src_path, "exec"), BO.__dict__)

C = P.C
RX, RY, TOP = P.RX, P.RY, P.TOP
COMP = os.path.join(BL, "out", "components")
OUT = os.path.join(C.FOOTAGE, "2026-10-26-component-test")
BLEND = os.path.join(BL, "out", "room_v3_component_test.blend")
PHOTO = os.path.join(C.REPO, "docs", "moodboard", "local", "ai-desk-reference-1.jpg")
PY = "/opt/anaconda3/bin/python3"
BO.OUT = OUT
OPTION = "PC_YAW" in os.environ
PC_YAW = float(os.environ["PC_YAW"]) if OPTION else P.PC_YAW
SUFFIX = f"-pc{PC_YAW:.0f}" if OPTION else ""

REPLACED = {"pole", "ultrawide", "studio_display", "screenbar", "pc"} | {f"{p}_{i}" for p in ("spk_pole", "spk_plate", "a7v") for i in (1, 2)}
COMPONENTS = ("set_desk", "screens", "speakers", "pc")      # the .blend collections
# 2026-10-26: the arms component (key lights, the camera on its Flex Arm, the mic on its PSA1+) is built live from
# blender/components/arms.py at plan v3's numbers (ARMS=plan, the default; ARMS=0 keeps the stand-ins).
ARMS = os.environ.get("ARMS", "plan")
if ARMS != "0":
    REPLACED = REPLACED | {"keylight_pole_1", "keylight_pole_2", "keylight_1", "keylight_2", "camera", "mic"}
    SUFFIX = SUFFIX + ("" if ARMS == "plan" else f"-arms-{ARMS}")


def build_arms(lite=False):
    """The arms set at plan v3 or the proposal, in its own collection 'arms'."""
    os.environ["ARMS_PART"] = "all"
    sys.path.insert(0, os.path.join(BL, "components"))
    import arms as AR
    AR.PART = "all"
    col = bpy.data.collections.get("arms") or bpy.data.collections.new("arms")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return AR.build_set(AR.room_layout(ARMS), collection=col, lite=lite)


def M_at(x, y, z=0.0, yaw=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")


def wbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def tree(o):
    out = [o]
    for c in o.children:
        out += tree(c)
    return out


# ---------------------------------------------------------------------------
# placing the components (the same code for the rich .blend parts and the lite GLBs)
# ---------------------------------------------------------------------------
SCREENS_POLE_Y = 0.190            # screens.py POLE_Y: the pole axis in the component's frame


def place(get):
    """get(name) -> object. Puts the four components at plan v3's numbers."""
    # desk: origin in the left/back corner, room axes
    get("set_desk").matrix_world = M_at(P.MAIN["x0"], P.RET["y1"], 0)   # the desk's wall corner
    # screens: front -Y in the component; yaw 90 turns it to +X. Pole axis on plan v3's POLE.
    px, py = P.POLE
    get("screens").matrix_world = M_at(px, py, TOP, 90) @ Matrix.Translation((0, -SCREENS_POLE_Y, 0))
    # speakers: split into two mounts (pole axis at x = -0.3 / +0.3), each at plan v3's spot and toe-in
    root = get("speakers")
    for i, s in enumerate(P.SPEAKERS, 1):
        mount = bpy.data.objects.new(f"spk_mount_{i}", None)        # pivot at the component origin
        bpy.context.scene.collection.objects.link(mount)
        for o in [o for o in root.children if o.name.startswith(f"studio_speaker_0{i}")]:
            o.parent = mount
            o.matrix_parent_inverse = Matrix.Identity(4)
        mount.matrix_world = M_at(s["x"], s["y"], TOP, s["yaw"]) @ Matrix.Translation((-(-0.3, 0.3)[i - 1], 0, 0))
    bpy.context.view_layer.update()
    # PC: plan v3's yaw (90: front glass to the window side, side glass to the room)
    x, y, _ = P.PC_AT
    if OPTION and PC_YAW == 0:      # the old orientation: front glass to the room, back 4 cm off the desk's edge
        x, y = P.RET["x0"] + 0.02 + 0.152, P.RET["y1"] - 0.04 - 0.24
    get("pc").matrix_world = M_at(x, y, TOP, PC_YAW)
    bpy.context.view_layer.update()


def drop_iso():
    for o in list(bpy.data.objects):
        if o.name.startswith("studio_speaker_") and "_iso" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)


def append_rich():
    for name in COMPONENTS:
        path = os.path.join(COMP, ("desk" if name == "set_desk" else name) + ".blend")
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.collections = [name]
        col = dst.collections[0]
        bpy.context.scene.collection.children.link(col)
    drop_iso()
    place(lambda n: bpy.data.objects[n])


def eevee_glass():
    """The components' glass is set up for Cycles; in EEVEE (and Material Preview) it renders as a grey
    slab. Turn on screen-space refraction for every transmissive material, in this test file only."""
    sc = bpy.context.scene
    sc.eevee.use_raytracing = True
    fixed = []
    for m in bpy.data.materials:
        if not m.use_nodes or m.get("eevee_thin"):     # has its own thin EEVEE glass (the PC, 2026-10-26)
            continue
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED" and n.inputs["Transmission Weight"].default_value > 0.5:
                m.use_raytrace_refraction = True
                m.surface_render_method = "DITHERED"
                fixed.append(m.name)
    return fixed


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def import_lite():
    for f in ("desk", "screens", "speakers", "pc"):
        import_glb(os.path.join(COMP, f + "-lite.glb"))
    drop_iso()
    place(lambda n: bpy.data.objects[n])


# ---------------------------------------------------------------------------
# piano and guitars 02, 04 from their lite GLBs (aligned by their boxes)
# ---------------------------------------------------------------------------
def align_root(new, target, front="-Y"):
    """Root at identity; then move so the box's bottom (centre x, back y=0 for 'back', else centre y)
    sits at the origin, and apply target."""
    root = [o for o in new if o.parent is None][0]
    for o in new:
        if o.type == "CAMERA" or (o.type == "EMPTY" and "view" in o.name):
            o.hide_render = o.hide_viewport = True
    root.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()
    lo, hi = wbox([o for o in new if o.type == "MESH"])
    return root, lo, hi


def music_side():
    out = {}
    try:
        for o in list(bpy.data.objects):          # the stand-ins this replaces
            if o.name.startswith(("piano_", "wall_g1_", "rack_g0_")):
                bpy.data.objects.remove(o, do_unlink=True)
        # piano: plan frame PM, case back at local y=0, front -Y, centred on x
        new = import_glb(os.path.join(BL, "out", "obj_piano-lite.glb"))
        root, lo, hi = align_root(new, None)
        out["piano_box_local"] = [list(map(lambda v: round(v, 3), lo)), list(map(lambda v: round(v, 3), hi))]
        PM = M_at(P.PIANO_V3["x"], P.PIANO_V3["y"], 0, P.PIANO_V3["yaw"])
        root.matrix_world = PM @ Matrix.Translation((-(lo.x + hi.x) / 2, -hi.y, -lo.z))
        # guitar 02 (Woodstock Strat) on the right wall, slot 1, facing -X
        WG = P.WALL_GUITARS_V3
        new = import_glb(os.path.join(BL, "out", "guitar_02-lite.glb"))
        root, lo, hi = align_root(new, None)
        out["guitar_02_box_local"] = [list(map(lambda v: round(v, 3), lo)), list(map(lambda v: round(v, 3), hi))]
        G = Matrix.Translation((RX - WG["off_wall"], WG["y"][1], WG["bottom"])) @ Matrix.Rotation(math.radians(-90), 4, "Z")
        root.matrix_world = G @ Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
        # guitar 04 (Number One) in the floor rack, slot 0
        rk = P.RACK_V3
        new = import_glb(os.path.join(BL, "out", "guitar_04-lite.glb"))
        root, lo, hi = align_root(new, None)
        out["guitar_04_box_local"] = [list(map(lambda v: round(v, 3), lo)), list(map(lambda v: round(v, 3), hi))]
        sl = (0 - (rk["slots"] - 1) / 2) * rk["pitch"]
        RM = M_at(rk["x"], rk["y"], 0, rk["yaw"])
        Mg = RM @ Matrix.Translation((-0.08, sl, rk["cradle"])) @ Matrix.Rotation(math.radians(rk["lean"]), 4, "Y")
        root.matrix_world = Mg @ Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
        bpy.context.view_layer.update()
        out["ok"] = True
    except Exception as e:  # keep the stand-ins' places empty rather than stop the test
        out["ok"] = False
        out["error"] = repr(e)
    return out


# ---------------------------------------------------------------------------
# the fit check
# ---------------------------------------------------------------------------
def groups():
    g = {"desk": [], "screens_pole": [], "g8": [], "studio_display": [], "screenbar": [], "speaker_L": [],
         "speaker_R": [], "pc": [], "keylight_1": [], "keylight_2": [], "camera_arm": [], "mic": []}
    arms_col = bpy.data.collections.get("arms")
    arms_objs = set(arms_col.all_objects) if arms_col else set()
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        n = o.name
        if o in arms_objs:
            k = "keylight_1" if n.startswith("keylight_1") else "keylight_2" if n.startswith("keylight_2") else \
                "camera_arm" if n.startswith("cam") else "mic"
            g[k].append(o)
        elif n.startswith("desk_drawers") or n in ("desk_top", "desk_led"):
            g["desk"].append(o)
        elif n.startswith("desk_pole"):
            g["screens_pole"].append(o)
        elif n.startswith("desk_screenbar"):
            g["screenbar"].append(o)
        elif n.startswith("rig_display") or n.startswith("rig_screen") or n == "rig_static" and o.parent and o.parent.name == "screens":
            g["g8"].append(o)
        elif n.startswith("monitor_"):
            g["studio_display"].append(o)
        elif n.startswith("studio_speaker_01"):
            g["speaker_L"].append(o)
        elif n.startswith("studio_speaker_02"):
            g["speaker_R"].append(o)
        elif n.startswith("rig_") and o.parent and (o.parent.name == "pc" or o.parent.name.startswith("rig_gpu")):
            g["pc"].append(o)
    return g


def bvh(objs):
    verts, faces = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in me.vertices]
        faces += [[base + i for i in p.vertices] for p in me.polygons]
        e.to_mesh_clear()
    return BVHTree.FromPolygons(verts, faces, all_triangles=False), verts


def min_dist(va, tb):
    best = 1e9
    for v in va[::max(1, len(va) // 4000)]:
        hit = tb.find_nearest(v)
        if hit[0] is not None:
            best = min(best, hit[3])
    return best


def fit_check():
    g = groups()
    others = {}
    comp_names = {o.name for objs in g.values() for o in objs}
    skip = {"floor", "ceiling", "sky", "ground"}
    for o in bpy.data.objects:
        if o.type == "MESH" and not o.hide_render and o.name not in comp_names and not o.name.startswith(("city_", "piano", "guitar", "obj_")) \
                and o.name not in skip:
            others[o.name] = o
    trees = {k: bvh(v) for k, v in g.items() if v}
    res = {"boxes": {}, "pairs": [], "standins": [], "walls": {}}
    for k, objs in g.items():
        if objs:
            lo, hi = wbox(objs)
            res["boxes"][k] = dict(lo=[round(v, 4) for v in lo], hi=[round(v, 4) for v in hi])
            res["walls"][k] = dict(left_wall_gap=round(lo.x - (-RX), 4), back_wall_gap=round(RY - hi.y, 4))
    keys = list(trees)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            ta, va = trees[a]
            tb, vb = trees[b]
            ov = len(ta.overlap(tb))
            d = 0.0 if ov else min(min_dist(va, tb), min_dist(vb, ta))
            if ov or d < 0.05:
                res["pairs"].append(dict(a=a, b=b, overlap_tris=ov, gap=round(d, 4)))
    for k in keys:
        ta, va = trees[k]
        for n, o in others.items():
            tb, vb = bvh([o])
            ov = len(ta.overlap(tb))
            if ov:
                res["standins"].append(dict(component=k, standin=n, overlap_tris=ov))
            else:
                d = min_dist(vb, ta)
                if d < 0.03:
                    res["standins"].append(dict(component=k, standin=n, overlap_tris=0, gap=round(d, 4)))
    top = bpy.data.objects.get("desk_top")
    if top:
        lo, hi = wbox([top])
        res["desk_top_z"] = [round(lo.z, 4), round(hi.z, 4)]
    res["plan"] = dict(TOP=TOP, POLE=P.POLE, UW=P.UW, SD=P.SD, SPEAKERS=P.SPEAKERS, PC_AT=P.PC_AT, SPK_Z=P.SPK_Z)
    return res


# ---------------------------------------------------------------------------
def cameras():
    cams = {}
    hv = P.HERO_V3
    cams["HERO_V3"] = BO.camera("HERO_V3", hv["pos"], hv["target"], hv["vfov"])
    cams["HERO_V3_PORTRAIT"] = BO.camera("HERO_V3_PORTRAIT", hv["pos"], hv["target"], hv["portrait_vfov"])
    cams["INTRO"] = BO.camera("INTRO", P.INTRO["pos"], P.INTRO["target"], P.INTRO["vfov"])
    cams["ABOUT"] = BO.camera("ABOUT", P.ABOUT["pos"], P.ABOUT["target"], P.ABOUT["vfov"])
    cams["TOP"] = BO.camera("TOP", (0, 0, 2.9), (0, 0, 0), 0, ortho=4.8)
    cams["DESK_CORNER"] = BO.camera("DESK_CORNER", (-0.55, -0.15, 1.62), (-1.85, 1.30, 1.10), 58)
    return cams


def main():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    os.makedirs(OUT, exist_ok=True)
    BO.build_room()
    keep = P.COMPONENTS
    P.COMPONENTS = [c for c in keep if c["key"] not in REPLACED]
    try:
        BO.build_parts()
    finally:
        P.COMPONENTS = keep
    BO.build_specials()
    for o in list(bpy.data.objects):
        if o.name.startswith("pole_arm"):            # the stand-in VESA arms; the screens bring their own
            bpy.data.objects.remove(o, do_unlink=True)
        elif ARMS != "0" and o.name.startswith(("mic_arm", "mic_hang", "mic_capsule", "flex_arm")):
            bpy.data.objects.remove(o, do_unlink=True)   # the stand-in mic arm and flex arm
    if ARMS != "0":
        arms_names = build_arms()
        print("ARMS", ARMS, arms_names.get("mic_pose"), arms_names.get("flex_reach"))
    BO.lights()
    append_rich()
    music = music_side()
    cams = cameras()
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 32
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.camera = cams["HERO_V3"]
    glass = eevee_glass()
    print("eevee glass", glass)
    report = fit_check()
    report["music"] = music
    report["eevee_glass"] = glass
    with open(os.path.join(OUT, f"fit-check{SUFFIX}.json"), "w") as f:
        json.dump(report, f, indent=1)
    print("FIT", json.dumps(report))
    if not OPTION and ARMS in ("plan", "0"):
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
        print("saved", BLEND)

    only = os.environ.get("ONLY", "")
    shots = [("hero", "HERO_V3", (1600, 900)), ("hero-portrait", "HERO_V3_PORTRAIT", (880, 1100)),
             ("about", "ABOUT", (1600, 900)), ("top", "TOP", (1100, 1050)), ("desk-corner", "DESK_CORNER", (1600, 1000))]
    for name, cam, res in shots:
        if not only or name in only.split(","):
            BO.shoot(name + SUFFIX, cams[cam], res)
    sc.camera = cams["HERO_V3"]
    portrait = os.path.join(OUT, f"hero-portrait{SUFFIX}.png")
    if os.path.exists(portrait) and os.path.exists(PHOTO):
        code = ("import sys\nfrom PIL import Image, ImageDraw\n"
                "a=Image.open(sys.argv[1]).convert('RGB');b=Image.open(sys.argv[2]).convert('RGB')\n"
                "h=1100;a=a.resize((round(a.width*h/a.height),h));b=b.resize((round(b.width*h/b.height),h))\n"
                "s=Image.new('RGB',(a.width+b.width+60,h+80),(24,24,26));s.paste(a,(20,60));s.paste(b,(a.width+40,60))\n"
                "d=ImageDraw.Draw(s);d.text((20,20),'owner photo',fill=(230,230,230));d.text((a.width+40,20),'HERO_V3 portrait, real components (test)',fill=(230,230,230))\n"
                "s.save(sys.argv[3],quality=90)\n")
        subprocess.run([PY, "-c", code, PHOTO, portrait, os.path.join(OUT, f"hero-portrait{SUFFIX}-vs-photo.jpg")], check=False)

    if os.environ.get("SKIP_GLB") or OPTION or ARMS not in ("plan", "0"):
        return
    # --- the GLB: lite components plus the room shell and the AI-lab stand-ins
    for name in COMPONENTS:
        col = bpy.data.collections.get(name)
        for o in list(col.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(col)
    for o in list(bpy.data.objects):
        if o.name.startswith("spk_mount_") or o.name.startswith(("piano", "guitar", "obj_piano", "bench", "wall_g", "rack", "dj", "lightstick")):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in list(bpy.data.objects):     # the GLB importer's leftovers from the music side
        if o.type == "MESH" and o.parent is None and o.name.startswith(("piano_", "guitar_")):
            bpy.data.objects.remove(o, do_unlink=True)
    import_lite()
    if ARMS != "0":                                  # the arms: rich out, lite in
        col = bpy.data.collections.get("arms")
        for o in list(col.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
        build_arms(lite=True)
    drop = {"sky", "ground", "ceiling"}
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        if o.type in ("MESH", "EMPTY") and o.name not in drop and not o.name.startswith("city_"):
            o.select_set(True)
    glb = os.path.join(OUT, "room-v3-test.glb")
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_cameras=False,
                              export_lights=False, export_apply=False)
    print("glb", glb, os.path.getsize(glb))


main()
