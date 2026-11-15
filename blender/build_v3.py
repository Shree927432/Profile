"""Build the room the site loads from plan v3 (2026-10-31), with the lite version of every finished component.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/build_v3.py
    STAGES=build,export,stills (default build,export)   ONLY=hero,intro,...   DUMP=1 prints the object tree
    FROM_BLEND=1 STAGES=guitars   only scene/assets/guitars.glb, from the saved room_v3.blend (GUITARS_ATLAS=1024 at build
                                  time keeps the atlases at 1024; default 512, lib/guitars_room.py)

blender/build.py (the v1 room) stays for history. This script reuses the room test
(blender/design/room_v3_component_test.py, its source exec'd without its final main() call, so that file
is untouched) for every placement, and the v3 blockout (through the room test) for the shell, the window,
the city and the stand-ins. Then:
  - the lite components replace the blockout's boxes: desk, screens, speakers, PC (their lite GLBs),
    arms, desk-top group, chair, wall group, return desk (built live with lite=True), the lite piano and
    guitars 02 and 04 (their lite GLBs), the three plants (plants-lite.glb, blender/components/plants.py), the
    window with its board, architrave and net curtains (built live with lite=True, blender/components/window.py);
  - organise(): every object goes under its root from scene/objects/MESHES.md (obj_* / set_*), `_lite`
    is dropped from names, the code-facing names stay separate meshes, everything else under a group is
    joined into `<group>_static` (one mesh per group, one primitive per material);
  - camera empties from plan v3: room_view / room_view_target (HERO_V3), camera_intro, camera_about,
    camera_phone (each with _target), under set_room;
  - saves blender/out/room_v3.blend (pack_and_save) and exports scene/assets/room.glb with Draco and WebP;
  - stills (EEVEE) into video-local/footage/2026-10-31-room-v3/.
Stand-ins still from the blockout (no component yet): the guitar rack, the city, the ceiling light (obj_light), the felt
desk mat, the rug, the door.
2026-11-13: guitars 01, 03, 05 and 06 (their lite GLBs, cut for the web by lib/guitars_room.py) replace the blockout's flat
outlines, and the wall hangers are built under every head (lib/guitars_room.py hangers). The four are in the scene for
the bake (their shadows land in the room's lightmap) but not in room.glb: they ship in scene/assets/guitars.glb, loaded
after the room (export_guitars below, the deferred-asset pattern in docs/02-architecture.md).
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
from lib import guitars_room as GR  # noqa: E402

T0 = time.time()
STAGES = set(os.environ.get("STAGES", "build,export").split(","))
# RICH=1 (2026-11-15, owner: "i want to see room in full resolution in blender"): the same room from the full-detail
# components (rich builds, *-rich.glb, plants.blend, the guitars' and piano's rich GLBs at full texture size), lit by
# the dusk rig, saved as blender/out/room_v3_rich.blend for viewing. No bake, no export: the site's files are untouched.
RICH = os.environ.get("RICH") == "1"
LITE = not RICH
BLEND_RICH = os.path.join(HERE, "out", "room_v3_rich.blend")
C = P.C
OUT = os.path.join(C.FOOTAGE, "2026-10-31-room-v3")
BLEND = os.path.join(HERE, "out", "room_v3.blend")
GLB = os.path.join(C.REPO, "scene", "assets", "room.glb")
GUITARS_GLB = os.path.join(C.REPO, "scene", "assets", "guitars.glb")
PIANO_GLB = os.path.join(C.REPO, "scene", "assets", "piano.glb")       # 2026-11-14: loaded after the room (load time)
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
    RT.build_arms(lite=LITE)
    RT.build_desktop(lite=LITE)
    RT.build_chair(lite=LITE)
    RT.build_wall(lite=LITE)
    RT.build_returndesk(lite=LITE)
    RT.build_plants(lite=LITE)
    RES["window"] = RT.build_window(lite=LITE)
    log(f"live components ({'lite' if LITE else 'rich'}), plants, window")
    if RICH:                                     # desk, screens, speakers, PC, piano, guitars 02 and 04: the rich GLBs
        _imp = RT.import_glb

        def _rich(path):
            r = path.replace("-lite.glb", "-rich.glb")
            return _imp(r if os.path.exists(r) else path)
        RT.import_glb = _rich
        GR.LOD = "rich"
    RT.import_lite()
    RES["music"] = RT.music_side()
    log(f"lite GLBs, music side {RES['music'].get('ok')}")
    RES["guitars"] = guitars()
    log("guitars " + json.dumps(RES["guitars"]))
    RES["ceiling_light"] = ceiling_light()
    log("ceiling light " + json.dumps(RES["ceiling_light"]))
    BO.lights()


def ceiling_light():
    """The owner's three-square pendant and the switch by the door (2026-11-15, blender/components/ceiling_light.py) in
    place of the blockout's drum."""
    sys.path.insert(0, os.path.join(HERE, "components"))
    import ceiling_light as CL
    for o in list(bpy.data.objects):
        if o.name.startswith("pendant_"):
            bpy.data.objects.remove(o, do_unlink=True)
    CL.CEIL = C.ROOM["height"]
    root, info = CL.build(at=(P.LIGHT_V3["x"], P.LIGHT_V3["y"]))
    S = C.SWITCH
    CL.switch(wall_x=-C.RX, y=S["y"], z=S["z"], w=S["w"], h=S["h"])
    return info


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
    r"|laptop_screen|light_(led|switch|switch_plate)|plant_(pot|soil|leaf_\d\d)|window_(sash_\d|glass|curtains)"
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
    "guitar_01": "obj_guitars", "guitar_03": "obj_guitars", "guitar_05": "obj_guitars", "guitar_06": "obj_guitars",
    "floor": "set_room", "ceiling": "set_room", "door": "set_room", "wall_front": "set_room", "wall_right": "set_room",
    "sky": "set_city", "ground": "set_city",
    "light_root": "obj_light", "switch_root": "obj_light",
}
TOP_PREFIX = [("wall_l_", "set_room"), ("wb_", "set_room"), ("sk_", "set_room"),
              ("city_", "set_city"), ("guitars_hook_", "obj_guitars"), ("rack_", "obj_guitars")]
RENAME = {}


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


def guitars():
    """Guitars 01, 03, 05, 06 from their lite GLBs (cut for the web) in place of the blockout's flat outlines, guitar_02
    re-hung by the same rule, the blockout's hooks replaced by a hanger under every head (lib/guitars_room.py)."""
    for o in list(bpy.data.objects):
        if o.name.startswith(("wall_g0_", "wall_g2_", "rack_g1_", "rack_g2_")) or re.match(r"^hook(\.\d+)?$", o.name):
            bpy.data.objects.remove(o, do_unlink=True)
    out = {}
    for key in ("01", "03", "05", "06"):
        root, objs, info = GR.import_cut(key)
        out[key] = info
    for i, key in enumerate(GR.WALL):          # the Explorer on the wall, the Woodstock Strat in the rack (2026-11-13)
        out.setdefault(key, {})["wall"] = GR.place_wall(key, i, out.get(key, {}).get("centre_y"))
    for slot, key in GR.RACK:
        out.setdefault(key, {})["rack"] = GR.place_rack(key, slot)
    # 02 and 04 ship in guitars.glb too (2026-11-14, load time): all six come after the room, none is in the first view
    for key in ("02", "04"):
        r = bpy.data.objects[f"guitar_{key}"]
        for o in [r] + list(r.children_recursive):
            o[GR.DEFERRED] = "guitars"
    hooks, pts = GR.hangers(BO.mat("#232326", rough=0.45, metal=0.5), None)
    out["hangers"] = pts
    return out


def plants():
    """The plants component's roots (plants.py): the monstera's parts to obj_plant, the snake plant and the desk
    plant to set_plants (joined into plants_static below); the component's empties go."""
    for name, r in (("plant", "obj_plant"), ("snake_plant", "set_plants"), ("desk_plant", "set_plants")):
        e = bpy.data.objects[name]
        for o in list(e.children):
            reparent(o, root(r))
        bpy.data.objects.remove(e, do_unlink=True)


def window():
    """The window component's root (window.py): its parts to obj_window; the sashes and the glass stay separate
    meshes (KEEP), and so do the curtains (window_curtains: baked with their own lightmap layout); the frame, board,
    architrave and track join into window_static."""
    e = bpy.data.objects.get("window")
    if e is None:
        return
    for o in list(e.children):
        reparent(o, root("obj_window"))
    bpy.data.objects.remove(e, do_unlink=True)


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
    plants()
    window()
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
    RES["palettes"] = palettes()
    log("palettes " + json.dumps(RES["palettes"]))
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.data.name = o.name + "_mesh"



# ---------------------------------------------------------------------------
# palettes: fewer materials per root static (2026-10-31, draw calls)
# ---------------------------------------------------------------------------
# Every `<word>_static` draws one call per material. The flat materials (no image texture) of a static collapse
# into palette materials: a small swatch texture (one 16 px cell per colour) with the faces' UVs pointed at their
# cell. Flat materials share a palette when everything but colour, roughness, metallic and emission matches
# (specular level, coat, sheen, IOR); roughness and metallic ride in a second texture (glTF G and B channels),
# emission in a third, so the look is the same. Textured materials stay as they are. Nothing code-facing is touched.
CELL = 16
PER_ROW = 16
SNAP_SPEC = float(os.environ.get("SNAP_SPEC", "0.15"))  # specular levels within one step share a palette (the palette gets their mean); 0 = exact


def _srgb(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _principled(m):
    return next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None) if m and m.use_nodes else None


def flat_info(m):
    """None when the material needs its own draw call (an image feeds it, or no Principled); else its values.
    A procedural bump on Normal does not count: the glTF export drops it, so it is flat in the GLB too."""
    pb = _principled(m)
    if pb is None or any(n.bl_idname in ("ShaderNodeTexImage", "ShaderNodeGroup", "ShaderNodeAttribute",
                                         "ShaderNodeVertexColor") for n in m.node_tree.nodes):
        return None
    if any(i.is_linked and i.name != "Normal" for i in pb.inputs):
        return None
    g = lambda n: pb.inputs[n].default_value
    rest = []
    for i in pb.inputs:
        if i.name in ("Base Color", "Metallic", "Roughness", "Emission Color", "Emission Strength", "Normal",
                      "Tangent", "Weight") or not hasattr(i, "default_value"):
            continue
        v = i.default_value
        v = tuple(round(x, 3) for x in v) if hasattr(v, "__len__") else round(v, 3)
        if SNAP_SPEC and i.name == "Specular IOR Level":
            v = round(round(v / SNAP_SPEC) * SNAP_SPEC, 3)
        rest.append((i.name, v))
    ec = tuple(g("Emission Color")[:3])
    es = g("Emission Strength")
    return dict(spec=g("Specular IOR Level"), base=tuple(g("Base Color")[:3]), metal=g("Metallic"), rough=g("Roughness"),
                emit=tuple(c * es for c in ec) if es > 0 and max(ec) > 0 else (0.0, 0.0, 0.0), key=tuple(rest))


def _image(name, w, h, rgb, srgb):
    import numpy as np
    im = bpy.data.images.new(name, w, h, alpha=False)
    im.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
    px = np.ones((h, w, 4), dtype=np.float32)
    for i, c in enumerate(rgb):
        r, col = divmod(i, PER_ROW)
        v = [_srgb(x) if srgb else min(1.0, max(0.0, x)) for x in c]
        px[r * CELL:(r + 1) * CELL, col * CELL:(col + 1) * CELL, :3] = v
    im.pixels.foreach_set(px.ravel())
    im.pack()
    return im


def make_palette(word, k, cells, rep):
    """cells: list of flat_info dicts. rep: a material of the group (its Principled values are copied)."""
    rows = (len(cells) + PER_ROW - 1) // PER_ROW
    w, h = PER_ROW * CELL, rows * CELL
    m = rep.copy()
    m.name = f"mat_{word}_palette_{k}"
    nt = m.node_tree
    pb = _principled(m)
    pb.inputs["Specular IOR Level"].default_value = sum(c["spec"] for c in cells) / len(cells)
    for n in list(nt.nodes):
        if n.bl_idname not in ("ShaderNodeBsdfPrincipled", "ShaderNodeOutputMaterial"):
            nt.nodes.remove(n)
    for i in pb.inputs:
        for l in list(i.links):
            nt.links.remove(l)

    def tex(imname, rgb, srgb, y):
        im = _image(f"{m.name}_{imname}", w, h, rgb, srgb)
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image, t.interpolation, t.extension = im, "Closest", "EXTEND"
        t.location = (-600, y)
        return t
    t = tex("base", [c["base"] for c in cells], True, 300)
    nt.links.new(t.outputs["Color"], pb.inputs["Base Color"])
    if len({(round(c["metal"], 3), round(c["rough"], 3)) for c in cells}) > 1:
        t = tex("mr", [(0.0, c["rough"], c["metal"]) for c in cells], False, 0)
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        sep.location = (-300, 0)
        nt.links.new(t.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Green"], pb.inputs["Roughness"])
        nt.links.new(sep.outputs["Blue"], pb.inputs["Metallic"])
    else:
        pb.inputs["Roughness"].default_value, pb.inputs["Metallic"].default_value = cells[0]["rough"], cells[0]["metal"]
    emit = [c["emit"] for c in cells]
    top = max((max(e) for e in emit), default=0.0)
    if top > 0:
        strength = max(1.0, top)           # <= 1: baked into the texture; above 1: the glTF strength extension
        t = tex("emit", [tuple(x / strength for x in e) for e in emit], True, -300)
        nt.links.new(t.outputs["Color"], pb.inputs["Emission Color"])
        pb.inputs["Emission Strength"].default_value = strength
    else:
        pb.inputs["Emission Strength"].default_value = 0.0
    return m


# code-facing meshes whose materials nothing drives by colour: their flat materials collapse too, and meshes with
# the same cells share one palette (the fans), so the load-time batching (scene/batch.js) can draw them together
PALETTE_EXTRA = re.compile(r"^(rig_(case|gpu|fan_\d\d|gpu_fan_\d\d)|mic_body|window_sash_\d)$")   # the sashes share one


def palettes():
    """Collapse the flat materials of every `_static` mesh (and the PALETTE_EXTRA ones) into palette materials."""
    import numpy as np
    report = {}
    cache = {}
    for o in [o for o in bpy.data.objects if o.type == "MESH" and (o.name.endswith("_static") or PALETTE_EXTRA.match(o.name))]:
        me = o.data
        mats = list(me.materials)
        infos = [flat_info(m) for m in mats]
        flat = [i for i, f in enumerate(infos) if f]
        if len(flat) < 2:
            continue
        word = o.name[:-7] if o.name.endswith("_static") else o.name
        groups = {}
        for i in flat:
            groups.setdefault(infos[i]["key"], []).append(i)
        n = len(me.polygons)
        mi = np.zeros(n, dtype=np.int32)
        me.polygons.foreach_get("material_index", mi)
        ls = np.zeros(n, dtype=np.int32)
        lt = np.zeros(n, dtype=np.int32)
        me.polygons.foreach_get("loop_start", ls)
        me.polygons.foreach_get("loop_total", lt)
        poly_of_loop = np.repeat(np.arange(n), lt)
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        out = np.zeros(n, dtype=np.int32)
        keep = [i for i, m in enumerate(mats) if i not in flat]
        new_mats = [mats[i] for i in keep]
        new_index = {i: j for j, i in enumerate(keep)}
        uvs = [np.zeros(len(me.loops) * 2, dtype=np.float32) for _ in me.uv_layers]
        for u, layer in zip(uvs, me.uv_layers):
            layer.data.foreach_get("uv", u)
        uvs = [u.reshape(-1, 2) for u in uvs]
        for k, (key, idx) in enumerate(sorted(groups.items(), key=lambda kv: kv[1][0]), 1):
            cells, cell_of = [], {}
            for i in idx:                       # deduplicate identical colour and surface values
                f = infos[i]
                sig = (tuple(round(x, 4) for x in f["base"]), round(f["metal"], 3), round(f["rough"], 3), round(f["spec"], 3),
                       tuple(round(x, 4) for x in f["emit"]))
                if sig not in cell_of:
                    cell_of[sig] = len(cells)
                    cells.append(f)
                cell_of[i] = cell_of[sig]
            ckey = (key, tuple(
                (tuple(round(x, 4) for x in c["base"]), round(c["metal"], 3), round(c["rough"], 3), round(c["spec"], 3),
                 tuple(round(x, 4) for x in c["emit"])) for c in cells))
            if o.name.endswith("_static") or ckey not in cache:
                pal = make_palette(word, k, cells, mats[idx[0]])
                cache[ckey] = pal
            pal = cache[ckey]
            w, h = PER_ROW * CELL, ((len(cells) + PER_ROW - 1) // PER_ROW) * CELL
            slot = len(new_mats)
            new_mats.append(pal)
            for i in idx:
                c = cell_of[i]
                r, col = divmod(c, PER_ROW)
                uv = ((col + 0.5) * CELL / w, (r + 0.5) * CELL / h)
                polys = mi == i
                out[polys] = slot
                sel = polys[poly_of_loop]
                for u in uvs:
                    u[sel] = uv
        for i, j in new_index.items():
            out[mi == i] = j
        for u, layer in zip(uvs, me.uv_layers):
            layer.data.foreach_set("uv", u.ravel())
        me.materials.clear()
        for m in new_mats:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", out)      # after the slots exist: clearing them resets indices
        me.update()
        report[o.name] = (len(mats), len(new_mats))
    return report


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
            "piano_view", "piano_view_target", "piano_inside_view", "piano_inside_view_target",
            "plant_pot", "plant_soil", "plant_leaf_01", "plant_static", "plants_static",
            "window_static", "window_sash_1", "window_sash_2", "window_glass", "window_curtains",
            "light_static", "light_led", "light_switch", "light_switch_plate"]
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
        if o.type in ("MESH", "EMPTY") and not o.get(GR.DEFERRED):
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


DRACO = dict(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
             export_draco_position_quantization=14, export_draco_normal_quantization=10,
             export_draco_texcoord_quantization=12)


def _export_sel(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                              export_cameras=False, export_lights=False, export_extras=False, export_image_format="WEBP",
                              export_image_quality=80, **DRACO)
    return os.path.getsize(path)


def export_guitars():
    """scene/assets/guitars.glb (2026-11-13): all six guitars (01, 03, 05, 06 from 2026-11-13; 02 and 04 joined them
    2026-11-14 to shorten the first load) under one root, obj_guitars_late, at their places in the room (the room's
    frame, so the site adds it as it is). Env-lit (no lightmap: they lift off their hooks later, MESHES.md). Each
    guitar's share is measured by exporting it alone."""
    keys = ("01", "02", "03", "04", "05", "06")
    roots = [bpy.data.objects[f"guitar_{k}"] for k in keys]
    late = bpy.data.objects.new("obj_guitars_late", None)
    bpy.context.scene.collection.objects.link(late)
    parents = [(r, r.parent) for r in roots]
    for r in roots:
        reparent(r, late)
    each = {}
    tmp = os.path.join(HERE, "out", "dusk", "enc")
    os.makedirs(tmp, exist_ok=True)
    for k, r in zip(keys, roots):
        objs = [r] + list(r.children)
        tris = 0
        for o in objs:
            if o.type == "MESH":
                o.data.calc_loop_triangles()
                tris += len(o.data.loop_triangles)
        f = os.path.join(tmp, f"guitar_{k}-web.glb")
        each[k] = dict(kb=round(_export_sel(objs, f) / 1000), tris=tris)
        os.remove(f)
    size = _export_sel([late] + [o for r in roots for o in [r] + list(r.children)], GUITARS_GLB)
    for r, p in parents:
        reparent(r, p)
    bpy.data.objects.remove(late, do_unlink=True)
    log(f"exported {GUITARS_GLB}: {size / 1e3:.0f} KB {json.dumps(each)}")
    return dict(bytes=size, each=each)


def mark_piano_deferred():
    """2026-11-14 (load time): the piano leaves room.glb for scene/assets/piano.glb, loaded after the room appears. It is
    out of the first view (the desk), and at 0.41 MB it is the largest part of the room the first picture does not
    need. It keeps its place in the bake and its lightmap UVs (TEXCOORD_1 into the room's own atlas): the site lights it
    with the room's lightmap (desktop.js DEFERRED, light "room"). Marked only after the bake and the raw review export."""
    root = bpy.data.objects["obj_piano"]
    for o in [root] + list(root.children_recursive):
        o[GR.DEFERRED] = "piano"


def export_piano():
    """scene/assets/piano.glb: obj_piano and everything under it, in the room's frame (the site adds it as it is)."""
    root = bpy.data.objects["obj_piano"]
    size = _export_sel([root] + list(root.children_recursive), PIANO_GLB)
    log(f"exported {PIANO_GLB}: {size / 1e3:.0f} KB")
    return dict(bytes=size)


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


# ---------------------------------------------------------------------------
# dusk (2026-11-01): the lighting pass, blender/lib/lighting_dusk.py. STAGES=dusk,export FROM_BLEND=1 relights the
# saved room_v3.blend without rebuilding it. DUSK_LM (atlas px), DUSK_SPP (bake samples), DUSK_STILLS=hero,intro,...
# The EXRs land in blender/out/dusk/; blender/tools/encode_dusk.py makes the site's WebPs from them.
# ---------------------------------------------------------------------------
DUSK_OUT = os.path.join(C.FOOTAGE, "2026-11-01-dusk")
DUSK_DIR = os.path.join(HERE, "out", "dusk")
BLEND_DUSK = os.path.join(HERE, "out", "room_v3_dusk.blend")


def dusk():
    from lib import lighting_dusk as LD
    os.makedirs(DUSK_DIR, exist_ok=True)
    os.makedirs(DUSK_OUT, exist_ok=True)
    LD.lights(P)
    # the window's view (2026-11-12): the sea at sunset in layers; LD.backdrop(".../pune-dusk.png") was the city
    LD.backdrop_layers(os.path.join(HERE, "assets", "dusk", "beach-dusk.json"))
    objs = LD.bake_targets()
    RES["dusk_baked"] = sorted(o.name for o in objs)
    LD.lightmap_uvs(objs)
    if os.environ.get("DUSK_SPP", "96") != "0":
        LD.bake(objs, os.path.join(DUSK_DIR, "lightmap.exr"), int(os.environ.get("DUSK_LM", "2048")),
                int(os.environ.get("DUSK_SPP", "96")))
    if os.environ.get("DUSK_ENV", "1") == "1":
        LD.env(os.path.join(DUSK_DIR, "env.exr"))
    want = os.environ.get("DUSK_STILLS", "hero,intro,about,desk-corner")
    if want:
        cams = [("hero", BO.camera("still_hero", P.HERO_V3["pos"], P.HERO_V3["target"], P.HERO_V3["vfov"]), (1600, 900)),
                ("intro", BO.camera("still_intro", P.INTRO["pos"], P.INTRO["target"], P.INTRO["vfov"]), (1600, 900)),
                ("about", BO.camera("still_about", P.ABOUT["pos"], P.ABOUT["target"], P.ABOUT["vfov"]), (1600, 900)),
                ("desk-corner", BO.camera("still_desk", (-0.55, -0.15, 1.62), (-1.85, 1.30, 1.10), 58), (1600, 1000)),
                ("door", *door_view())]
        LD.stills(cams, DUSK_OUT, int(os.environ.get("DUSK_STILL_SPP", "64")), want)


def door_view():
    """A still of the switch by the door and the ceiling light (2026-11-15): from the piano side of the room."""
    return BO.camera("still_door", (1.10, 0.35, 1.70), (-C.RX, C.SWITCH["y"] + 0.25, 1.75), 62), (1600, 900)


def lamp():
    """STAGES=...,lamp (after dusk, same run: the LM layout must be the dusk bake's): the ceiling light's layer."""
    from lib import lighting_dusk as LD
    sys.path.insert(0, os.path.join(HERE, "components"))
    want = os.environ.get("LAMP_STILLS", "hero,about,door")
    allc = {"hero": (BO.camera("still_hero_l", P.HERO_V3["pos"], P.HERO_V3["target"], P.HERO_V3["vfov"]), (1600, 900)),
            "about": (BO.camera("still_about_l", P.ABOUT["pos"], P.ABOUT["target"], P.ABOUT["vfov"]), (1600, 900)),
            "door": door_view()}
    cams = [(k + "-lamp", *allc[k]) for k in want.split(",") if k in allc]
    LD.lamp_layer(LD.bake_targets(), os.path.join(DUSK_DIR, "lightmap-lamp.exr"), os.path.join(DUSK_DIR, "env-lamp.exr"),
                  int(os.environ.get("DUSK_LM", "2048")), int(os.environ.get("LAMP_SPP", os.environ.get("DUSK_SPP", "96"))),
                  cams, DUSK_OUT, int(os.environ.get("DUSK_STILL_SPP", "64")))


def main_rich():
    """RICH=1: build the room from the full-detail components, light it with the dusk rig, save it. Nothing exported."""
    from lib import lighting_dusk as LD
    build()
    cars = os.path.join(HERE, "out", "components", "cars.blend")      # the car shelf, rich, in the room's frame
    if os.path.exists(cars):
        with bpy.data.libraries.load(cars, link=False) as (src, dst):
            dst.collections = [c for c in src.collections if c == "cars"]
        for c in dst.collections:
            bpy.context.scene.collection.children.link(c)
        log("car shelf appended from cars.blend")
    LD.lights(P)
    LD.backdrop_layers(os.path.join(HERE, "assets", "dusk", "beach-dusk.json"))
    cams = RT.cameras()
    for name, c in cams.items():
        c.name = "still_" + name.lower()
    bpy.context.scene.camera = bpy.data.objects.get("still_hero_v3")
    pack_and_save(BLEND_RICH)
    log(f"saved {BLEND_RICH}")


def main():
    if RICH:
        main_rich()
        return
    if os.environ.get("FROM_BLEND"):
        bpy.ops.wm.open_mainfile(filepath=BLEND)
        log(f"opened {BLEND}")
        relight_and_export()
        return
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
    relight_and_export()


def relight_and_export():
    if "guitars" in STAGES and "export" not in STAGES:      # guitars.glb alone (FROM_BLEND=1 STAGES=guitars)
        RES["guitars_glb"] = export_guitars()
        log("done " + json.dumps(RES["guitars_glb"]))
        return
    if "dusk" in STAGES:
        dusk()
        pack_and_save(BLEND_DUSK)
        log(f"saved {BLEND_DUSK}")
    if "export" in STAGES:
        RES["raw_bytes"] = export(os.path.join(DUSK_OUT, "room-dusk-raw.glb") if "dusk" in STAGES else GLB_RAW, False, "AUTO")
        mark_piano_deferred()
        RES["glb_bytes"] = export(GLB, True, "WEBP")
        RES["guitars_glb"] = export_guitars()
        RES["piano_glb"] = export_piano()
    if "lamp" in STAGES:
        lamp()
    RES["total_s"] = round(time.time() - T0, 1)
    rep = os.path.join(DUSK_OUT, "build-report.json") if "dusk" in STAGES else REPORT
    os.makedirs(os.path.dirname(rep), exist_ok=True)
    with open(rep, "w") as f:
        json.dump(RES, f, indent=1)
    log("done " + json.dumps({k: RES[k] for k in ("raw_bytes", "glb_bytes", "statics") if k in RES}))


main()
