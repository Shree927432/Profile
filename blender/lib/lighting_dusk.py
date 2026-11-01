"""Dusk in Pune: the room's light (2026-11-01, the lighting pass). Used by blender/build_v3.py (stage `dusk`).

Felix's method, fitted to our pipeline: Cycles lights the room, the light is baked, the browser draws the bake.
  - lights(): a low warm sun through the window (WINDOW_V3) and its grill, the window's sky as a soft area light, a
    dim world, and the room's own lights as real sources matched to their glowing parts: the two key lights
    (dimmed, warm white), the Studio Display and the G8, the neon (white), the Nanoleaf (blue-white), the pegboard
    backlight (blue, aimed at the wall), the PC (blue-white, inside the case). The desk LED strip and the other
    emissive parts light the room through their own emission (Cycles samples emissive meshes).
  - backdrop(): the grey block city becomes one plane 22 m out with the painted Pune dusk
    (blender/tools/paint_pune_dusk.py), emissive, kept as `city_static`; it lights the room through the window
    but never shadows the sun.
  - bake(): ONE lightmap atlas for every static mesh that never moves (BAKE below): a second UV set `LM` (smart
    project over all of them at once, so texel density is even and the room shell gets the most room), a Cycles
    DIFFUSE bake without colour (direct + indirect: the sun streaks, soft shadows, bounce, the practicals' glow),
    saved as linear EXR. Albedo, roughness and metal stay in the palette textures; the browser multiplies.
    Moving parts (keys, pads, knobs, faders, fans, drawers, frames, panels, screens, chair, guitars, piano lids)
    are not baked: they are lit by the environment map, so no baked shadow slides with them.
  - env(): an equirect from above the desk in Cycles (the room lit at dusk), linear EXR, for PMREM reflections.
  - stills(): Cycles stills from HERO_V3, INTRO, ABOUT and the desk corner.
blender/tools/encode_dusk.py turns the EXRs into the small 8-bit WebPs the site loads and writes room-light.json.
Units: Cycles watts; the sun in W/m2.
"""
import math
import os
import re
import time

import bpy
from mathutils import Matrix, Vector

# must match blender/tools/paint_pune_dusk.py (X0, X1, Z0, Z1)
BACKDROP = dict(x0=-36.0, x1=36.0, z0=-14.0, z1=22.0, out=14.0)
# light travels along SUN_DIR (horizontal part), down at SUN_ELEV: in through the window, across the main desk and
# the wall behind the screens. The painted sun sits further left (in the intro's frame): a cinema cheat.
SUN_DIR = (-0.80, -0.50)
SUN_ELEV = 11.0
SUN = dict(strength=26.0, color=(1.0, 0.47, 0.20), angle=0.8)
WORLD = (0.030, 0.040, 0.075)
BAKE = re.compile(r"^(?!(chair|city|frame_\d|guitar_0\d)_static$)(.+_static|monitor_body|rig_case|rig_gpu|"
                  r"studio_speaker_0\d|mic_body)$")
EXPOSURE = -1.3                       # the stills' exposure (the site sets its own)
ENV_AT = (-1.05, 0.95, 1.20)          # above the desk's corner, in free air, near the hero target
# the music side (2026-11-01, the owner: fix the dark About view): the lightstick's watts, the hidden fill (Blender
# room frame: the piano wall is +X), and the G8's picture (blender/tools/paint_g8_dashboard.py) and its glow
MUSIC = dict(lightstick=6.0, fill=30.0, fill_at=(0.30, -0.40, 2.75), fill_aim=(2.10, -0.30, 1.30), fill_size=(1.6, 1.0))
G8_PICTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "dusk", "g8-dashboard.png")
G8_GLOW = 3.0


def log(msg, t0=[time.time()]):
    print(f"MILESTONE dusk {time.time() - t0[0]:6.1f}s {msg}", flush=True)


def wbox(o):
    ps = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector([min(p[i] for p in ps) for i in range(3)]), Vector([max(p[i] for p in ps) for i in range(3)]))


def _lamp(name, kind, at, aim=None, energy=10.0, color=(1, 1, 1), size=0.1, size_y=None, radius=None):
    d = bpy.data.lights.new(name, kind)
    d.energy, d.color = energy, color
    if kind == "AREA":
        d.shape = "RECTANGLE"
        d.size, d.size_y = size, size_y if size_y else size
    elif kind in ("POINT", "SPOT"):
        d.shadow_soft_size = radius if radius is not None else 0.05
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = at
    if aim is not None:
        o.rotation_euler = Vector(aim).normalized().to_track_quat("-Z", "Y").to_euler()
    return o


def _emit_strength(o, k):
    for m in o.data.materials:
        pb = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None) if m else None
        if pb:
            pb.inputs["Emission Strength"].default_value *= k


def lights(P):
    """Remove the daylight rig, set the dusk rig. P: lib.plan_v3."""
    sc = bpy.context.scene
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    w = bpy.data.worlds.new("dusk")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*WORLD, 1)
    bg.inputs["Strength"].default_value = 1.0
    W = P.WINDOW_V3
    h = Vector((*SUN_DIR, 0)).normalized()
    d = Vector((h.x, h.y, -math.tan(math.radians(SUN_ELEV)))).normalized()
    s = bpy.data.lights.new("lt_sun", "SUN")
    s.energy, s.color, s.angle = SUN["strength"], SUN["color"], math.radians(SUN["angle"])
    so = bpy.data.objects.new("lt_sun", s)
    sc.collection.objects.link(so)
    so.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    # the sky in the window: amber low, lilac-blue high (one soft rectangle in the opening, facing in)
    wx, wz = (W["x0"] + W["x1"]) / 2, (W["sill"] + W["head"]) / 2
    _lamp("lt_dusk_sky", "AREA", (wx, P.RY + 0.06, wz), (0, -1, -0.15), 20, (0.66, 0.70, 1.0),
          W["x1"] - W["x0"], W["head"] - W["sill"])
    ob = bpy.data.objects
    # key lights: the panel's glow faces the desk; dimmed, warm white (about 3200 K)
    for k in (1, 2):
        g = ob.get(f"keylight_{k}_glow")
        if g:
            lo, hi = wbox(g)
            c = (lo + hi) / 2
            n = Vector((-1.75, 1.0, 0.95)) - c                  # towards the desk's centre
            n.z = 0
            _lamp(f"lt_keylight_{k}", "AREA", c + n.normalized() * 0.02, n, 6.0, (1.0, 0.80, 0.60), 0.30, 0.20)
    # the screens face +X (towards the room)
    for name, e, col in (("monitor_screen", 1.5, (0.80, 0.88, 1.0)), ("rig_screen", 2.5, (0.70, 0.82, 1.0)),
                         ("laptop_screen", 0.8, (0.85, 0.90, 1.0))):
        g = ob.get(name)
        if g:
            lo, hi = wbox(g)
            c = (lo + hi) / 2
            if name == "laptop_screen":
                _lamp(f"lt_{name}", "AREA", c + Vector((0, -0.03, 0)), (0, -1, -0.2), e, col, hi.x - lo.x, hi.z - lo.z)
            else:
                _lamp(f"lt_{name}", "AREA", c + Vector((0.03, 0, 0)), (1, 0, -0.1), e, col, hi.y - lo.y, hi.z - lo.z)
    # the wall's lights face -Y (into the room); the pegboard's backlight faces the wall
    for name, e, col, aim in (("neon_glow", 2.5, (1.0, 0.95, 0.90), (0, -1, 0)),
                              ("nanoleaf_panel_04", 3.0, (0.40, 0.55, 1.0), (0, -1, 0)),
                              ("pegboard_glow", 5.0, (0.10, 0.30, 1.0), (0, 1, 0))):
        g = ob.get(name)
        if not g:
            continue
        lo, hi = wbox(g)
        c = (lo + hi) / 2
        if name.startswith("nanoleaf"):
            ps = [wbox(o) for o in ob if o.name.startswith("nanoleaf_panel_")]
            lo = Vector([min(p[0][i] for p in ps) for i in range(3)])
            hi = Vector([max(p[1][i] for p in ps) for i in range(3)])
            c = (lo + hi) / 2
        off = Vector(aim) * (-0.015 if aim[1] > 0 else 0.03)
        _lamp(f"lt_{name.split('_panel')[0]}", "AREA", c + off, aim, e, col, max(0.05, hi.x - lo.x), max(0.05, hi.z - lo.z))
    # the PC: blue-white inside the case
    g = ob.get("rig_glow_strips")
    if g:
        lo, hi = wbox(g)
        _lamp("lt_pc", "POINT", (lo + hi) / 2, None, 3.0, (0.55, 0.72, 1.0), radius=0.12)
    # the lightstick on the music side: a purple glow on the wall behind the decks (1.2 W read as nothing, 2026-11-01)
    g = ob.get("lightstick_head")
    if g:
        lo, hi = wbox(g)
        _lamp("lt_lightstick", "POINT", (lo + hi) / 2, None, MUSIC["lightstick"], (0.62, 0.35, 1.0), radius=0.04)
    # the music side's fill: no source in frame, a soft warm-lilac wash from high over the room's middle onto the
    # piano wall, as the bounce of the window and the desk's lights would give (the About view read near black)
    P_ = MUSIC["fill_at"]
    _lamp("lt_music_fill", "AREA", P_, Vector(MUSIC["fill_aim"]) - Vector(P_), MUSIC["fill"], (1.0, 0.86, 0.92),
          *MUSIC["fill_size"])
    f = bpy.data.objects["lt_music_fill"]
    f.visible_camera = f.visible_glossy = False     # never a bright rectangle in the piano's black gloss
    # the G8 shows the training dashboard (a still until obj_rig draws it live), lit like a screen at dusk
    rig = bpy.data.materials.get("mat_screens_rig")
    if rig and os.path.exists(G8_PICTURE):
        t = next((n for n in rig.node_tree.nodes if n.bl_idname == "ShaderNodeTexImage"), None)
        pb = next((n for n in rig.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
        if t and pb:
            t.image = bpy.data.images.load(G8_PICTURE)
            t.image.pack()
            pb.inputs["Emission Strength"].default_value = G8_GLOW
    # the desk LED strip glows through its own emission; strength 300 is for EEVEE, too hot for a bake
    if ob.get("desk_led"):
        _emit_strength(ob["desk_led"], 0.08)
    # the key lights are dimmed; the Nanoleaf panels glow blue-white (their own emission lights the wall too)
    done = set()                                    # shared materials: scale each once
    for prefix, k in (("keylight_", 0.5), ("nanoleaf_panel_", 3.0)):
        for o in [o for o in ob if o.type == "MESH" and o.name.startswith(prefix) and
                  (prefix != "keylight_" or o.name.endswith("_glow"))]:
            for m in o.data.materials:
                if m and m.name not in done:
                    done.add(m.name)
                    pb = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
                    if pb:
                        pb.inputs["Emission Strength"].default_value *= k
    # the pendant is off at dusk until the visitor switches it on (obj_light)
    if ob.get("light_shade"):
        _emit_strength(ob["light_shade"], 0.0)
    log("lights")


def backdrop(png):
    """Replace city_static (sky, ground, blocks) with one painted plane 22 m outside the window."""
    import bmesh
    old = bpy.data.objects.get("city_static")
    parent = old.parent if old else None
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    from . import plan_v3 as P
    B = BACKDROP
    # painted for a plane 22 m out; drawn at B["out"] m, scaled about the INTRO camera so the intro's picture is the
    # same, and inside the site's 30 m far plane from every camera (at 22 m the hero saw past it, 2026-11-01)
    ix, iy, iz = P.INTRO["pos"]
    k = (P.RY + B["out"] - iy) / (P.RY + 22.0 - iy)
    y = P.RY + B["out"]
    me = bpy.data.meshes.new("city_static_mesh")
    bm = bmesh.new()
    sx = lambda x: ix + (x - ix) * k
    sz = lambda z: iz + (z - iz) * k
    vs = [bm.verts.new(v) for v in ((sx(B["x0"]), y, sz(B["z0"])), (sx(B["x1"]), y, sz(B["z0"])),
                                    (sx(B["x1"]), y, sz(B["z1"])), (sx(B["x0"]), y, sz(B["z1"])))]
    f = bm.faces.new(vs)                            # faces -Y, towards the room (reversed it faced away)
    uv = bm.loops.layers.uv.new("UVMap")
    for loop in f.loops:
        v = loop.vert.co
        loop[uv].uv = ((v.x - sx(B["x0"])) / (sx(B["x1"]) - sx(B["x0"])), (v.z - sz(B["z0"])) / (sz(B["z1"]) - sz(B["z0"])))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("city_static", me)
    bpy.context.scene.collection.objects.link(o)
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    m = bpy.data.materials.new("mat_city_dusk")
    m.use_nodes = True
    nt = m.node_tree
    pb = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(png)
    t.image.pack()
    nt.links.new(t.outputs["Color"], pb.inputs["Base Color"])
    nt.links.new(t.outputs["Color"], pb.inputs["Emission Color"])
    pb.inputs["Emission Strength"].default_value = 1.0
    pb.inputs["Roughness"].default_value = 1.0
    pb.inputs["Specular IOR Level"].default_value = 0.0
    me.materials.append(m)
    o.visible_shadow = False                        # never blocks the sun
    log("backdrop")
    return o


def _cycles(samples, denoise):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:              # never set the Metal device in preferences under --factory-startup (chair.py's fix)
        sc.cycles.device = "GPU"
    except Exception:
        pass
    sc.cycles.samples = samples
    sc.cycles.use_denoising = denoise
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 4
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.sample_clamp_indirect = 6.0
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = EXPOSURE


def bake_targets():
    return [o for o in bpy.data.objects if o.type == "MESH" and BAKE.match(o.name)]


def lightmap_uvs(objs, margin=0.0015):
    """A second UV set `LM` on every bake target, unwrapped and packed together (one atlas)."""
    for o in objs:
        if o.data.users > 1:
            o.data = o.data.copy()
        me = o.data
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        keep = next((l.name for l in me.uv_layers if l.active_render), me.uv_layers[0].name)
        lm = me.uv_layers.get("LM") or me.uv_layers.new(name="LM")
        me.uv_layers.active = lm                   # the bake writes through the active map
        me.uv_layers[keep].active_render = True    # textures (and glTF TEXCOORD_0) keep reading the first
    for o in objs:
        o.hide_set(False)
        o.hide_viewport = False
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    with bpy.context.temp_override(object=objs[0], active_object=objs[0], selected_objects=objs,
                                   selected_editable_objects=objs):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action="SELECT")
        r1 = bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=margin, area_weight=0.0,
                                      correct_aspect=False, scale_to_bounds=False)
        r2 = "smart project packs"                 # pack_islands squeezed it into a 0.2-wide column (2026-11-01)
        bpy.ops.object.mode_set(mode="OBJECT")
    log(f"lightmap UVs on {len(objs)} meshes: {r1} {r2}, in edit: {sum(1 for o in objs if o.data.uv_layers.active.name == 'LM')}")


def bake(objs, path, size=2048, samples=96):
    sc = bpy.context.scene
    _cycles(samples, False)
    img = bpy.data.images.new("lm_dusk", size, size, alpha=True, float_buffer=True)
    img.generated_color = (0, 0, 0, 0)
    nodes = []
    for o in objs:
        for m in o.data.materials:
            if m is None or any(n.name == "lm_bake" for n in m.node_tree.nodes):
                continue
            t = m.node_tree.nodes.new("ShaderNodeTexImage")
            t.name, t.image = "lm_bake", img
            m.node_tree.nodes.active = t
            nodes.append((m, t))
    # Cycles bakes through the render UV map, so LM becomes the render map for the bake. The materials' own
    # textures are pinned to their first map with UV Map nodes meanwhile (the bounce light keeps its colours), and
    # everything is put back after.
    keep = {}
    for o in objs:
        first = next(l.name for l in o.data.uv_layers if l.name != "LM")
        for m in o.data.materials:
            if m is not None:
                keep.setdefault(m, first)
    pins = []
    for m, first in keep.items():
        for n in list(m.node_tree.nodes):
            if n.bl_idname == "ShaderNodeTexImage" and n.name != "lm_bake" and not n.inputs["Vector"].is_linked:
                u = m.node_tree.nodes.new("ShaderNodeUVMap")
                u.uv_map = first
                m.node_tree.links.new(u.outputs["UV"], n.inputs["Vector"])
                pins.append((m, u))
    for o in objs:
        o.data.uv_layers["LM"].active_render = True
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    b = sc.render.bake
    b.use_pass_direct, b.use_pass_indirect, b.use_pass_color = True, True, False
    b.margin, b.margin_type = 4, "EXTEND"
    b.use_clear = True
    b.target = "IMAGE_TEXTURES"
    t0 = time.time()
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=4, use_clear=True)
    log(f"baked {size}px {samples} spp in {time.time() - t0:.0f} s")
    img.filepath_raw = path
    img.file_format = "OPEN_EXR"
    img.save()
    for m, t in nodes:
        m.node_tree.nodes.remove(t)
    for m, u in pins:
        m.node_tree.nodes.remove(u)
    for o in objs:
        next(l for l in o.data.uv_layers if l.name != "LM").active_render = True
    return path


def env(path, res=(512, 256), samples=128):
    sc = bpy.context.scene
    _cycles(samples, True)
    cam = bpy.data.objects.new("still_env", bpy.data.cameras.new("still_env"))
    sc.collection.objects.link(cam)
    cam.data.type = "PANO"
    try:
        cam.data.panorama_type = "EQUIRECTANGULAR"
    except AttributeError:
        cam.data.cycles.panorama_type = "EQUIRECTANGULAR"
    cam.location = ENV_AT
    # three.js equirect: u = 0.5 is +X (three and Blender), u = 0.75 is +Z three = -Y Blender: the camera looks +X
    cam.rotation_euler = (math.radians(90), 0, math.radians(-90))
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "16"
    sc.render.filepath = path
    vt = sc.view_settings.view_transform
    sc.view_settings.view_transform = "Standard"
    bpy.ops.render.render(write_still=True)
    sc.view_settings.view_transform = vt
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    log(f"env {res}")
    return path


def stills(cams, out, samples=64, only=""):
    """cams: [(file, camera object, (w, h))]. Cycles, denoised, AgX."""
    sc = bpy.context.scene
    _cycles(samples, True)
    sc.render.image_settings.file_format = "PNG"
    for name, cam, res in cams:
        if only and name not in only.split(","):
            continue
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.resolution_percentage = 100
        sc.render.filepath = os.path.join(out, name + ".png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        log(f"still {name} {time.time() - t0:.0f} s")
