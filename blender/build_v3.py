"""Build the room the site loads from plan v3 (2026-10-31), with the lite version of every finished component.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/build_v3.py
    STAGES=build,export,stills (default build,export)   ONLY=hero,intro,...   DUMP=1 prints the object tree

blender/build.py (the v1 room) stays for history. This script reuses the room test
(blender/design/room_v3_component_test.py, its source exec'd without its final main() call, so that file
is untouched) for every placement, and the v3 blockout (through the room test) for the shell, the window,
the city and the stand-ins. Then:
  - the lite components replace the blockout's boxes: desk, screens, speakers, PC (their lite GLBs),
    arms, desk-top group, chair, wall group, return desk (built live with lite=True), the lite piano and
    guitars 02 and 04 (their lite GLBs);
  - organise(): every object goes under its root from scene/objects/MESHES.md (obj_* / set_*), `_lite`
    is dropped from names, the code-facing names stay separate meshes, everything else under a group is
    joined into `<group>_static` (one mesh per group, one primitive per material);
  - camera empties from plan v3: room_view / room_view_target (HERO_V3), camera_intro, camera_about,
    camera_phone (each with _target), under set_room;
  - saves blender/out/room_v3.blend (pack_and_save) and exports scene/assets/room.glb with Draco and WebP;
  - stills (EEVEE) into video-local/footage/2026-10-31-room-v3/.
Stand-ins still from the blockout (no component yet): guitars 01, 03, 05, 06 (flat outlines), the guitar
rack and hooks, the window frame, ledge and grill, the city, the sill plant (obj_plant), the ceiling light
(obj_light), the snake plant and the small desk plant, the felt desk mat, the rug, the door.
"""
import json
import math
import os
import re
import sys
import time
import types

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import plan_v3 as P  # noqa: E402
from lib.blendfile import pack_and_save  # noqa: E402

T0 = time.time()
STAGES = set(os.environ.get("STAGES", "build,export").split(","))
C = P.C
OUT = os.path.join(C.FOOTAGE, "2026-10-31-room-v3")
BLEND = os.path.join(HERE, "out", "room_v3.blend")
GLB = os.path.join(C.REPO, "scene", "assets", "room.glb")
GLB_RAW = os.path.join(OUT, "room-v3-raw.glb")
REPORT = os.path.join(OUT, "build-report.json")
PY = "/opt/anaconda3/bin/python3"
PHOTO = os.path.join(C.REPO, "docs", "moodboard", "local", "ai-desk-reference-1.jpg")
RES = {}


def log(msg):
    print(f"MILESTONE {time.time() - T0:6.1f}s {msg}", flush=True)


# --- the room test's placement code, without running its main()
_rt_path = os.path.join(HERE, "design", "room_v3_component_test.py")
_src = open(_rt_path).read()
_src = _src[: _src.rindex("\nmain()")]
RT = types.ModuleType("room_v3_component_test")
RT.__file__ = _rt_path
exec(compile(_src, _rt_path, "exec"), RT.__dict__)
BO = RT.BO
BO.OUT = OUT


# ---------------------------------------------------------------------------
# build: the shell and stand-ins from the blockout, the lite components in place
# ---------------------------------------------------------------------------
def build():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    BO.build_room()
    keep = P.COMPONENTS
    P.COMPONENTS = [c for c in keep if c["key"] not in RT.REPLACED]
    try:
        BO.build_parts()
    finally:
        P.COMPONENTS = keep
    BO.build_specials()
    gone = ("pole_arm", "mic_arm", "mic_hang", "mic_capsule", "flex_arm", "chair_", "neon_stroke", "nanoleaf_t",
            "peg_shelf", "vine_leaf", "dj_top", "dj_leg", "dj_rail")
    for o in list(bpy.data.objects):             # the blockout's stand-ins the components replace
        if o.name.startswith(gone):
            bpy.data.objects.remove(o, do_unlink=True)
    log("shell and stand-ins")
    RT.build_arms(lite=True)
    RT.build_desktop(lite=True)
    RT.build_chair(lite=True)
    RT.build_wall(lite=True)
    RT.build_returndesk(lite=True)
    log("live components (lite)")
    RT.import_lite()
    RES["music"] = RT.music_side()
    log(f"lite GLBs, music side {RES['music'].get('ok')}")
    BO.lights()


# ---------------------------------------------------------------------------
# organise: roots, names, statics joined (scene/objects/MESHES.md)
# ---------------------------------------------------------------------------
# Code-facing meshes stay separate (one mesh, the names MESHES.md lists); every other mesh under a root or a
# group joins into `<word>_static`. `*_static` names always join.
KEEP = re.compile(
    r"^(monitor_(body|screen)"
    r"|rig_(display|screen|case|case_glass|fans|fan_\d\d|gpu|gpu_fan_\d\d|gpu_light|glow_strips)"
    r"|studio_speaker_0\d(_woofer)?|apollo_(knob|leds)"
    r"|dj_(jog_[lr]|pad_[lr]_\d\d|cue_[lr]|play_[lr]|tempo_[lr]|fader_[lr]|xfader|knob_[a-z_]+)"
    r"|lightstick_(head|shell|handle)"
    r"|desk_led|desk_drawers_\d\d_drawer_\d\d|kb_key_[a-z0-9]+|kb_knob|mouse_wheel"
    r"|mic_(body|led)|keylight_\d_glow|cam_screen_lcd"
    r"|frame_\d_(border|picture)|neon|neon_glow|neon_halo|pegboard_glow|nanoleaf_panel_\d\d"
    r"|laptop_screen|light_shade"
    r"|piano_(key_[a-g]s?\d|fallboard|lid|interior|strings|hammers|sheet)"
    r"|guitar_0\d_(body|strings))$")
GROUPS = {f"frame_{i}" for i in (1, 2, 3)} | {f"guitar_0{i}" for i in range(1, 7)} | {"chair_swivel"}
STATIC_NAME = {"chair_swivel": "chair_static", "set_keylights": "keylights_static", "set_camera": "cam_static",
               "obj_guitars": "guitars_static"}
# top-level objects (after `_lite` is dropped) -> their root
TOP_ROOT = {
    "set_desk": "set_desk", "keyboard": "set_desk", "mouse": "set_desk", "deck": "set_desk", "mat": "set_desk",
    "apollo": "obj_studio", "dj_stand_root": "obj_studio", "lightstick_root": "obj_studio",
    "cam_arm": "set_camera", "cam": "set_camera", "keylight_1": "set_keylights", "keylight_2": "set_keylights",
    "chair_swivel": "set_chair", "shelf_root": "set_wall", "vine_pot_1_root": "set_wall", "vine_pot_2_root": "set_wall",
    "pegboard_root": "set_wall", "neon_root": "set_wall", "nanoleaf_root": "set_wall", "mstand_root": "set_laptop",
    "guitar_02": "obj_guitars", "guitar_04": "obj_guitars", "rug": "set_rug",
    "floor": "set_room", "ceiling": "set_room", "door": "set_room", "wall_front": "set_room", "wall_right": "set_room",
    "ledge": "obj_window", "sky": "set_city", "ground": "set_city",
    "pendant_cord": "obj_light", "pendant_shade": "obj_light", "plant_pot": "obj_plant",
    "snake_pot": "set_plants", "desk_plant_pot": "set_plants",
}
TOP_PREFIX = [("wall_l_", "set_room"), ("wb_", "set_room"), ("sk_", "set_room"), ("win_frame", "obj_window"),
              ("grill", "obj_window"), ("city_", "set_city"), ("hook", "obj_guitars"), ("rack_", "obj_guitars"),
              ("snake_leaf", "set_plants")]
RENAME = {"pendant_shade": "light_shade", "pendant_cord": "light_cord"}


def root(name):
    o = bpy.data.objects.get(name)
    if o is None:
        o = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(o)
    assert o.name == name, (o.name, name)
    return o


def reparent(o, parent):
    mw = o.matrix_world.copy()
    o.parent = parent
    o.matrix_parent_inverse = Matrix.Identity(4) if parent is None else parent.matrix_world.inverted()
    o.matrix_world = mw


def apply_mods():
    dg = bpy.context.evaluated_depsgraph_get()
    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        if o.data.users > 1:
            o.data = o.data.copy()
        if o.modifiers:
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            o.modifiers.clear()
            old, o.data = o.data, me
            if old.users == 0:
                bpy.data.meshes.remove(old)


def outside_city():
    """Sky, ground and city: four shared haze materials (was one per block), then scaled about the INTRO camera
    by 0.44 so the sky sits 27 m out, inside the site's 30 m far plane. From INTRO the picture is unchanged."""
    blocks = [o for o in bpy.data.objects if o.name.startswith("city_")]
    c0, c1 = (0x5f, 0x6e, 0x88), (0x9c, 0xb0, 0xcc)
    mats = []
    for k in range(4):
        h = (k + 0.5) / 4
        mats.append(BO.mat("#" + "".join(f"{int(a + (b - a) * h):02x}" for a, b in zip(c0, c1)), rough=0.8))
    for o in blocks:
        y = (o.matrix_world @ Vector(o.bound_box[0])).y
        o.data.materials[0] = mats[min(3, int(max(0.0, (y - P.RY - 12) / 40) * 4))]
    pivot = Vector(P.INTRO["pos"])
    S = Matrix.Translation(pivot) @ Matrix.Scale(0.44, 4) @ Matrix.Translation(-pivot)
    for o in blocks + [bpy.data.objects["sky"], bpy.data.objects["ground"]]:
        o.data.transform(S @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)


def guitar_standins():
    """Guitars 01, 03, 05, 06: the blockout's flat outlines, one material each, as guitar_NN / guitar_NN_body."""
    g = root("obj_guitars")
    for src, nn in (("wall_g0", "01"), ("wall_g2", "03"), ("rack_g1", "05"), ("rack_g2", "06")):
        parts = [o for o in bpy.data.objects if o.name.startswith(src + "_")]
        body = next(o for o in parts if o.name == src + "_body")
        m = body.data.materials[0]
        for o in parts:
            o.data = o.data.copy()
            o.data.materials.clear()
            o.data.materials.append(m)
        lo = min((o.matrix_world @ Vector(c)).z for o in parts for c in o.bound_box)
        cx = sum((o.matrix_world @ Vector(c)).x for c in body.bound_box) / 8
        cy = sum((o.matrix_world @ Vector(c)).y for c in body.bound_box) / 8
        e = root(f"guitar_{nn}")
        e.matrix_world = Matrix.Translation((cx, cy, lo))
        reparent(e, g)
        for o in [body] + [o for o in parts if o is not body]:
            reparent(o, e)
        from lib import geo
        geo.join([body] + [o for o in parts if o is not body], f"guitar_{nn}_body")


def plants():
    """The blockout names every leaf `leaf`: the sill plant's go to obj_plant, the desk plant's to set_plants."""
    sill = bpy.data.objects["plant_pot"].matrix_world.translation
    for o in [o for o in bpy.data.objects if o.name.startswith("leaf")]:
        near = (o.matrix_world.translation - sill).length < 0.25
        reparent(o, root("obj_plant" if near else "set_plants"))


def organise():
    for o in bpy.data.objects:                # the room test hides the piano's camera anchors for its renders
        if o.type == "EMPTY":
            o.hide_viewport = o.hide_render = False
            o.hide_set(False)
    apply_mods()
    for o in list(bpy.data.objects):          # lights: Blender only, lt_ prefix
        if o.type == "LIGHT" and not o.name.startswith("lt_"):
            o.name = "lt_" + o.name
    for o in list(bpy.data.objects):          # the stand-in bench: the lite piano brings its own (piano_static)
        if o.name.startswith("bench_"):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects:
        if o.name.endswith("_lite"):
            o.name = o.name[:-5]
    for o in list(bpy.data.objects):
        if o.name.endswith("_lite"):          # a second pass: names freed by the first
            o.name = o.name[:-5]
    outside_city()
    guitar_standins()
    plants()
    # flatten the component roots that MESHES.md does not have
    for o in list(bpy.data.objects["screens"].children):
        n = o.name
        reparent(o, root("obj_monitor" if n.startswith("monitor_") else "obj_rig" if n.startswith("rig_") else "set_desk"))
    for o in list(bpy.data.objects["pc"].children):
        reparent(o, root("obj_rig"))
    for i in (1, 2):
        for o in list(bpy.data.objects[f"spk_mount_{i}"].children):
            reparent(o, root("obj_studio"))
    for n in ("screens", "pc", "spk_mount_1", "spk_mount_2", "speakers"):
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    # the frames: frame_N_root -> frame_N (the empty), the border mesh frame_N -> frame_N_border, under obj_frames
    for i in (1, 2, 3):
        bpy.data.objects[f"frame_{i}"].name = f"frame_{i}_border"
        e = bpy.data.objects[f"frame_{i}_root"]
        e.name = f"frame_{i}"
        reparent(e, root("obj_frames"))
    # every other top-level object to its root
    for o in list(bpy.data.objects):
        if o.parent is not None or o.type in ("LIGHT", "CAMERA") or o.name.startswith(("obj_", "set_")):
            continue
        r = TOP_ROOT.get(o.name) or next((rt for p, rt in TOP_PREFIX if o.name.startswith(p)), None)
        if r is None:
            raise RuntimeError(f"no root for {o.name}")
        reparent(o, root(r))
    for a, b in RENAME.items():
        if a in bpy.data.objects:
            bpy.data.objects[a].name = b
    # join the statics: per root (or GROUPS empty), all non-KEEP meshes
    pools = {}
    for o in bpy.data.objects:
        if o.type != "MESH" or KEEP.match(o.name):
            continue
        g = o.parent
        while g.parent is not None and not (g.type == "EMPTY" and g.name in GROUPS):
            g = g.parent
        pools.setdefault(g.name, []).append(o)
    made = {}
    from lib import geo
    for gname, objs in pools.items():
        g = bpy.data.objects[gname]
        word = gname[4:] if gname.startswith(("obj_", "set_")) else gname
        target = STATIC_NAME.get(gname, word + "_static")
        for o in objs:                        # children of joined meshes stay where they are
            for c in list(o.children):
                if c not in objs:
                    reparent(c, c.parent.parent)
            o.name = "tmp_" + o.name
        first = objs[0]
        reparent(first, g)
        j = geo.join(objs, target)
        made[target] = len(j.data.materials)
    RES["statics"] = made
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.data.name = o.name + "_mesh"


def cameras():
    """Camera empties under set_room: the site's moves read them by name."""
    sr = root("set_room")
    out = {}
    for name, cam in (("room_view", P.HERO_V3), ("camera_intro", P.INTRO), ("camera_about", P.ABOUT),
                      ("camera_phone", P.PHONE_V3)):
        for suffix, pt in (("", cam["pos"]), ("_target", cam["target"])):
            e = root(name + suffix)
            e.empty_display_type, e.empty_display_size = "PLAIN_AXES", 0.1
            e.matrix_world = Matrix.Translation(pt)
            reparent(e, sr)
        out[name] = dict(pos=cam["pos"], target=cam["target"], vfov=cam["vfov"])
    RES["cameras"] = out


def check_names():
    exported = [o for o in bpy.data.objects if o.type in ("MESH", "EMPTY")]
    bad = [o.name for o in exported if not re.match(r"^[a-z0-9_]{1,63}$", o.name) or o.name.startswith("tmp_")]
    roots = sorted(o.name for o in exported if o.parent is None)
    need = ["monitor_screen", "monitor_body", "room_view", "room_view_target", "camera_intro", "camera_intro_target",
            "camera_about", "camera_about_target", "camera_phone", "camera_phone_target", "rig_screen", "mic_body",
            "kb_key_a", "dj_jog_l", "chair_swivel", "frame_1_picture", "laptop_screen", "guitar_02_body",
            "piano_view", "piano_view_target", "piano_inside_view", "piano_inside_view_target"]
    missing = [n for n in need if n not in bpy.data.objects]
    multi = [o.name for o in exported if o.type == "MESH" and KEEP.match(o.name) and len(o.data.materials) > 1]
    RES["names"] = dict(bad=bad, roots=roots, missing=missing, keep_multi_material=multi)
    log(f"names: {len(bad)} bad, missing {missing}, roots {roots}")
    if bad or missing or any(r for r in roots if not r.startswith(("obj_", "set_"))):
        raise RuntimeError(f"name check failed: {RES['names']}")


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------
def export(path, draco, image_format):
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        if o.type in ("MESH", "EMPTY"):
            o.select_set(True)
    kw = dict(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
              export_cameras=False, export_lights=False, export_extras=False, export_image_format=image_format,
              export_image_quality=80)
    if draco:
        kw.update(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
                  export_draco_position_quantization=14, export_draco_normal_quantization=10,
                  export_draco_texcoord_quantization=12)
    bpy.ops.export_scene.gltf(**kw)
    log(f"exported {path}: {os.path.getsize(path) / 1e6:.2f} MB")
    return os.path.getsize(path)


# ---------------------------------------------------------------------------
# stills (EEVEE), from the built scene before organise() (shoot() finds `ceiling` and `fill` by name)
# ---------------------------------------------------------------------------
def stills():
    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 32
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    RT.eevee_glass()
    cams = RT.cameras()
    cams["PHONE"] = BO.camera("PHONE", P.PHONE_V3["pos"], P.PHONE_V3["target"], P.PHONE_V3["vfov"])
    only = os.environ.get("ONLY", "")
    shots = [("hero", "HERO_V3", (1600, 900)), ("hero-portrait", "HERO_V3_PORTRAIT", (880, 1100)),
             ("intro", "INTRO", (1600, 900)), ("about", "ABOUT", (1600, 900)), ("top", "TOP", (1100, 1050)),
             ("desk-corner", "DESK_CORNER", (1600, 1000)), ("phone", "PHONE", (780, 1688))]
    for name, cam, res in shots:
        if not only or name in only.split(","):
            BO.shoot(name, cams[cam], res)
            log(f"still {name}")
    for c in cams.values():                   # review cameras are Blender only
        c.name = "still_" + c.name.lower()
    portrait = os.path.join(OUT, "hero-portrait.png")
    if os.path.exists(portrait) and os.path.exists(PHOTO):
        import subprocess
        code = ("import sys\nfrom PIL import Image, ImageDraw\n"
                "a=Image.open(sys.argv[1]).convert('RGB');b=Image.open(sys.argv[2]).convert('RGB')\n"
                "h=1100;a=a.resize((round(a.width*h/a.height),h));b=b.resize((round(b.width*h/b.height),h))\n"
                "s=Image.new('RGB',(a.width+b.width+60,h+80),(24,24,26));s.paste(a,(20,60));s.paste(b,(a.width+40,60))\n"
                "d=ImageDraw.Draw(s);d.text((20,20),'owner photo',fill=(230,230,230));"
                "d.text((a.width+40,20),'room v3 (lite components, the GLB), HERO_V3 portrait',fill=(230,230,230))\n"
                "s.save(sys.argv[3],quality=90)\n")
        subprocess.run([PY, "-c", code, PHOTO, portrait, os.path.join(OUT, "hero-portrait-vs-photo.jpg")], check=False)


def main():
    build()
    pb = bpy.data.objects.get("piano_static")
    if pb:
        lo, hi = RT.wbox([pb])
        RES["piano_static_box"] = [[round(v, 3) for v in lo], [round(v, 3) for v in hi]]
    if "stills" in STAGES:
        stills()
    organise()
    cameras()
    check_names()
    bpy.context.scene.camera = bpy.data.objects.get("still_hero_v3")
    pack_and_save(BLEND)
    log(f"saved {BLEND}")
    if "export" in STAGES:
        RES["raw_bytes"] = export(GLB_RAW, False, "AUTO")
        RES["glb_bytes"] = export(GLB, True, "WEBP")
    RES["total_s"] = round(time.time() - T0, 1)
    os.makedirs(OUT, exist_ok=True)
    with open(REPORT, "w") as f:
        json.dump(RES, f, indent=1)
    log("done " + json.dumps({k: RES[k] for k in ("raw_bytes", "glb_bytes", "statics") if k in RES}))


main()
