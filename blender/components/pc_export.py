"""pc: the rich and lite GLBs. The right side panel joins rig_case (it is separate only for the rear-chamber
close-up). Lite: build(lite=True) under its own root, the rich tree renamed out of the way while it exports.

Glass for three.js: the lite GLB's glass is a plain alpha-blended material (no transmission extension):
baseColor #eef7f5, alpha 0.10, roughness 0.05, metallic 0, alphaMode BLEND. In the room code:
    new THREE.MeshStandardMaterial({ color: 0xeef7f5, transparent: true, opacity: 0.10, roughness: 0.05,
                                     metalness: 0, depthWrite: false })
render it after the inside (renderOrder 1) and let the scene's environment map give it its sheen. The
perforated panels and hex mesh are alpha-tested tiles (alphaMode MASK, cutoff 0.5)."""
import json
import os
import shutil
import time

import bpy

import pc as K
from lib import names as NM, run


def _tree(root):
    return [root] + list(root.children_recursive)


def _export(objs, path):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in objs)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_cameras=False, export_lights=False, export_extras=False)
    return run.glb_stats(path)


def join_side(R):
    side = bpy.data.objects.get("rig_case_side")
    case = bpy.data.objects.get("rig_case")
    if side is None or case is None:
        return
    import pc_build
    pc_build.join_into(case, [side])


def clip_tiles():
    """Perforations as alpha clip (glTF MASK): a Round node between the tile's alpha and the BSDF."""
    for mn in ("mat_pc_perf", "mat_pc_hexmesh"):
        m = bpy.data.materials.get(mn)
        if m is None:
            continue
        nt = m.node_tree
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        if any(n.type == "MATH" for n in nt.nodes):
            continue
        tex = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
        r = nt.nodes.new("ShaderNodeMath")
        r.operation = "ROUND"
        nt.links.new(tex.outputs["Alpha"], r.inputs[0])
        nt.links.new(r.outputs[0], b.inputs["Alpha"])
        try:
            m.surface_render_method = "DITHERED"
        except AttributeError:
            pass


def lite_glass():
    from lib import materials as M
    g = bpy.data.materials.get("mat_pc_glass_lite") or M.principled("mat_pc_glass_lite", base="#eef7f5", rough=0.05,
                                                                       spec=0.5)
    b = next(n for n in g.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Alpha"].default_value = 0.10   # was 0.16 (milky over the lit inside, 2026-10-26)
    try:
        g.surface_render_method = "BLENDED"
    except AttributeError:
        pass
    return g


def swap_glass(objs):
    g = lite_glass()
    from lib import materials as M
    e = bpy.data.materials.get("mat_pc_glass_edge_lite") or M.principled("mat_pc_glass_edge_lite", base="#7fbfb2",
                                                                           rough=0.1, spec=0.5)
    for o in objs:
        if o.type == "MESH":
            for i, m in enumerate(o.data.materials):
                if m and m.name == "mat_pc_glass":
                    o.data.materials[i] = g
                elif m and m.name == "mat_pc_glass_edge":
                    o.data.materials[i] = e


def web_glow():
    """The GLBs carry the glow at GLOW_WEB (the renders keep GLOW_RING / GLOW_STRIP; pc.blend is not saved)."""
    for mn in ("mat_pc_fan_light", "mat_pc_glow"):
        m = bpy.data.materials.get(mn)
        if m is not None:
            e = next(n for n in m.node_tree.nodes if n.type == "EMISSION")
            e.inputs["Strength"].default_value = K.GLOW_WEB


def stage_export(R):
    t = time.time()
    clip_tiles()
    web_glow()
    join_side(R)
    root = bpy.data.objects["pc"]
    rich_objs = [o for o in _tree(root) if not o.name.startswith("still_")]
    swap_glass(rich_objs)            # the GLBs carry the simple blended glass (see the module doc)
    rich_tris = R.rendered_triangles([o.name for o in rich_objs])
    rich = _export(rich_objs, os.path.join(R.OUT, "pc-rich.glb"))
    R.log(f"GLB rich: {rich['kb']} KB, {rich['triangles']} stored / {rich_tris} rendered triangles")
    # lite: rename the rich tree out of the way, build lite, export, remove it, restore
    for o in rich_objs:
        o.name = o.name + "_r"
    coll = R._coll("pc_lite")
    K.build(lite=True, collection=coll)
    lroot = bpy.data.objects["pc_lite"]
    lite_objs = _tree(lroot)
    import pc_build
    side = bpy.data.objects.get("rig_case_side")
    if side is not None:
        pc_build.join_into(bpy.data.objects["rig_case"], [side])
        lite_objs = _tree(lroot)
    swap_glass(lite_objs)
    per = {o.name: R.rendered_triangles([o.name]) for o in lite_objs if o.type == "MESH"}
    lite_tris = sum(per.values())
    lroot.name = "pc"
    lite = _export(lite_objs, os.path.join(R.OUT, "pc-lite.glb"))
    R.log(f"GLB lite: {lite['kb']} KB, {lite['triangles']} stored / {lite_tris} rendered triangles")
    # a lite still from the hero camera (EEVEE), before the lite tree goes
    sc = bpy.context.scene
    for o in rich_objs:
        if o.type == "MESH":
            o.hide_render = True
    sc.camera = bpy.data.objects.get("still_cam_hero") or R.cameras()["hero"]
    R.render(os.path.join(K.FOOTAGE, "pc-lite.png"), True, 128, "lite")
    for o in rich_objs:
        if o.type == "MESH":
            o.hide_render = False
    for o in lite_objs:
        bpy.data.objects.remove(o)
    for o in rich_objs:
        o.name = o.name[:-2]
    # what the GLBs say about their materials (alpha modes for the room code)
    info = {}
    for nm in ("pc-rich.glb", "pc-lite.glb"):
        info[nm] = glb_materials(os.path.join(R.OUT, nm))
    R.report(glb={"rich": rich, "rich_rendered_tris": rich_tris, "lite": lite, "lite_rendered_tris": lite_tris,
                  "lite_per_mesh": per, "materials": info, "export_s": round(time.time() - t, 1)})


def glb_materials(path):
    import struct
    with open(path, "rb") as f:
        f.read(12)
        clen, _ = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(clen))
    out = {}
    for m in doc.get("materials", []):
        out[m["name"]] = {"alphaMode": m.get("alphaMode", "OPAQUE"),
                          "ext": sorted(m.get("extensions", {}).keys())}
    return out
