"""The wall group's headphones (2026-11-02): the downloaded ATH-M50x model, rich and lite. wall.py imports this.

Source (blender/assets/headphones/README.md; the original stays there untouched, git-ignored):
  "ATH-M50X Headphone" by tejay21, Sketchfab, CC BY 4.0, https://sketchfab.com/3d-models/ada0fcae10a1403c8c5bae1745a738f0
Owner: "Fix the headphones" (the round-2 model's cups read as mugs, no ear pads), and on detail: "keep the heavy models for
the Blender file. Don't cut down on that. You can do it for web version, but don't do it for the original Blender version."

Rich: the downloaded meshes and materials as they are (395k triangles, its two 1024 px images), only scaled (the file is in
centimetres), moved so the band's inside top sits on the hook, tilted so the cups rest against the board, renamed
headphones_*, and ARVELL printed on the band's top where the real audio-technica wordmark sits.
Lite (the web, about 1,550 tris with the name; the owner chose the sharper lite on 2026-11-03): each part decimated to its PARTS count (0: left out), UVs, images and hard edges
dropped, joined into one all-smooth mesh with the wall group's flat materials (hp_white, hp_pad, hp_silver, plus hp_fabric
for the cloth behind the pads), so build_v3's palettes fold it into wall_static with no extra draw call. Judged at the
hero distance; the room grows 2.3 KB against round 2's 1,602-tri headphones (lightmap islands on the decimated parts).

The logo: the brief named the mesh "3 Logo.001" as the Audio-Technica emblem. It is not: it is two plain notched blocks
(the yoke's top bracket under each pivot, 651 vertices, no lettering, no texture). The model carries no real logo
anywhere (the cup discs and the band are plain; its images are pad cloth and the slider's normal map), so the bracket stays
(headphones_yoke_bracket); without it the pivots float over the cups.

Frame: the root empty (wall.py's headphones_root) at the hook point, the band's inside top; the band in the XZ plane,
the board at +Y, the viewer at -Y, Z up, metres.
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.join(BL, "assets", "headphones", "ath-m50x_headphone.glb")
CREDIT = '"ATH-M50X Headphone" by tejay21, CC BY 4.0'
SCALE = 0.01                    # the file is in centimetres: 18.8 x 10.9 x 25.0 -> 0.188 x 0.109 x 0.250 m
CLEAR = 0.0015                  # the cups' back stops this far in front of the board's face
HOOK_LIFT = 0.0015              # the band's inside top over the root (the wire's top under the band, EST from wall.py's hook)
# the source meshes (name prefix) -> our name, lite triangles (0: left out of the lite), lite material key
PARTS = [
    ("01 MetalBar.001_HeadbarMetal.clean", "headphones_slider", 30, "hp_silver"),
    ("01 MetalBar.001_HeadbarMetal_", "headphones_slider_marks", 0, "hp_silver"),
    ("01 MetalBar.001_Headphone Default", "headphones_slider_guide", 34, "hp_white"),
    ("02 BarEnd.001", "headphones_band_ends", 210, "hp_white"),
    ("02 FabricBar.001", "headphones_band", 170, "hp_pad"),
    ("02 Screws.003", "headphones_screws_f", 0, "hp_silver"),
    ("02 Screws.004", "headphones_screws_b", 0, "hp_silver"),
    ("02 Screws.005", "headphones_pivot_screws", 0, "hp_silver"),
    ("2 X Connector Bottom.001_Headphone Default", "headphones_hinge_lower", 80, "hp_white"),
    ("2 X Connector Bottom.001_MetalRing", "headphones_hinge_ring", 0, "hp_silver"),
    ("2 X Connector Top.001", "headphones_hinge_upper", 80, "hp_white"),
    ("3 Logo.001", "headphones_yoke_bracket", 24, "hp_white"),
    ("4 EarCoverConnector.001", "headphones_yoke", 90, "hp_white"),
    ("5 EarCoverConnectorHolder.001", "headphones_yoke_holder", 0, "hp_white"),
    ("6 EarCoverHole.001", "headphones_cup_ports", 0, "hp_white"),
    ("7 EarCover.001_Headphone Default", "headphones_cups", 250, "hp_white"),
    ("7 EarCover.001_MetalRing", "headphones_cup_rings", 48, "hp_silver"),
    ("8 EarCab.001_earCab_", "headphones_pads", 250, "hp_pad"),
    ("8 EarCab.001_earCabFabric", "headphones_pad_cloth", 24, "hp_fabric"),
]
# non-manifold source parts the collapse cannot reduce (BarEnd stops at about 1,050): voxel-remeshed first (metres)
REMESH = {"headphones_band_ends": 0.0008, "headphones_hinge_upper": 0.0006}
# ARVELL where the real wordmark is printed: along the band's outer top, centred, silver-grey pad print. The real
# "audio-technica" ascenders stand about half the band's top width (Thomann detail-headband-logo-top.jpg); ARVELL is all
# capitals, so its cap height takes that: LOGO_CAP of the band's measured top width.
LOGO_CAP = 0.50
LOGO_COLOUR = "#b4b6ba"          # EST from the photo: light silver-grey print on the white band
LOGO_FINISH = "printed"
LOGO_MAX_W = 0.13                # the real wordmark with its emblem runs about 13 cm along the band
WRAP_STEP = dict(rich=0.0015, lite=0.009)   # the decal is cut this fine before it is wrapped onto the band
LITE_LIFT = 0.0006               # the lite letters' height over the decimated band
LITE_WELD = 1e-5                 # the lite parts are welded at this distance before they are decimated
LITE_SHARP = None                # all smooth: hard edges split the vertices and cost 17 KB of 31 in Draco (measured)


def _import():
    """The model's meshes, each with its world transform (incl. the file's 100x empty) and SCALE baked into its data."""
    before = set(bpy.data.objects)
    mats_before = set(bpy.data.materials)
    bpy.ops.import_scene.gltf(filepath=SRC)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    S = Matrix.Scale(SCALE, 4)
    for o in meshes:
        mw = o.matrix_world.copy()
        if o.data.users > 1:
            o.data = o.data.copy()
        o.parent = None
        o.data.transform(S @ mw)
        o.matrix_world = Matrix.Identity(4)
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    for m in bpy.data.materials:
        if m not in mats_before and not m.name.startswith("mat_hp_"):
            m.name = "mat_hp_" + m.name.lower().replace(" ", "_").replace(".", "_")
    return meshes


def _part(o):
    for prefix, name, lite_tris, mat in PARTS:
        if o.name.startswith(prefix):
            return name, lite_tris, mat
    raise RuntimeError(f"headphones: unknown mesh {o.name!r}")


def _verts(objs):
    out = []
    for o in objs:
        v = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", v)
        out.append(v.reshape(-1, 3))
    return np.concatenate(out)


def _bvh(objs):
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    b = BVHTree.FromBMesh(bm)
    bm.free()
    return b


def _place(meshes, board_y, tip_y, wire_r):
    """Move the model so the band sits in the hook's dip: its inside top on the wire, its front edge just behind the
    hook's up-turned tip (tip_y), then tilt it about X (the cups' bottom out from the board) by the least angle that keeps
    everything CLEAR in front of the board's face at y = board_y. Returns (tilt in degrees, the tilt matrix)."""
    band = [o for o in meshes if _part(o)[0] in ("headphones_band", "headphones_band_ends")]
    lo = _verts(band).min(0)
    hi = _verts(band).max(0)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    hit = _bvh(band).ray_cast(Vector((cx, cy, lo[2] - 0.05)), Vector((0, 0, 1)), 1.0)
    band_y = tip_y + wire_r + 0.0005 + (hi[1] - lo[1]) / 2      # the band's centre, its front edge behind the tip
    T = Matrix.Translation((-cx, band_y - cy, -hit[0].z + HOOK_LIFT))
    for o in meshes:
        o.data.transform(T)
    v = _verts(meshes)
    tilt = 30.0
    for k in range(0, 121):
        a = math.radians(k * 0.25)
        y = v[:, 1] * math.cos(a) + v[:, 2] * math.sin(a)       # Rotation(-a, X): the bottom (z < 0) to -Y
        if y.max() <= board_y - CLEAR:
            tilt = k * 0.25
            break
    return tilt, Matrix.Rotation(math.radians(-tilt), 4, "X")


def _band_top(bvh, x, y, z0):
    h = bvh.ray_cast(Vector((x, y, z0 + 0.08)), Vector((0, 0, -1)), 0.2)
    return h if h[0] is not None else None


def _top_width(bvh, z0):
    """The band's top width at the crown: the y span where the top surface stays within 2 mm of the crown's height."""
    ys = np.arange(-0.03, 0.03, 0.0005)
    ok = []
    for y in ys:
        h = _band_top(bvh, 0.0, float(y), z0)
        if h is not None and h[0].z > z0 - 0.002:
            ok.append(y)
    return (max(ok) - min(ok)) if ok else 0.03


def _brand(coll, bvh, lite):
    """ARVELL on the band's outer top: built flat at the crown by lib/brands.py (size, colour and finish), then cut fine
    and wrapped onto the band along its arc (the word's x becomes arc length, its height the surface normal)."""
    from lib import brands
    top = bvh.ray_cast(Vector((0.0, 0.0, 0.5)), Vector((0, 0, -1)), 1.0)
    z0 = top[0].z
    width = _top_width(bvh, z0)
    d = brands.decal("headphones", (0.0, 0.0, z0), (0, 0, 1), (0, 1, 0), height=LOGO_CAP * width,
                     finish=LOGO_FINISH, colour=LOGO_COLOUR, collection=coll, lite=lite, name="headphones_brand",
                     max_width=LOGO_MAX_W)
    if d is None:
        return None, width
    # the band's crown profile at y = 0: arc length s(x)
    xs = np.arange(-0.09, 0.0901, 0.001)
    zs = []
    for x in xs:
        h = _band_top(bvh, float(x), 0.0, z0)
        zs.append(h[0].z if h is not None else np.nan)
    zs = np.array(zs)
    good = ~np.isnan(zs)
    xs, zs = xs[good], zs[good]
    seg = np.hypot(np.diff(xs), np.diff(zs))
    s = np.concatenate([[0.0], np.cumsum(seg)])
    s -= np.interp(0.0, xs, s)
    bm = bmesh.new()
    bm.from_mesh(d.data)
    step = WRAP_STEP["lite" if lite else "rich"]
    vx = [v.co.x for v in bm.verts]
    vy = [v.co.y for v in bm.verts]
    for axis, lo_, hi_ in ((0, min(vx), max(vx)),) + (((1, min(vy), max(vy)),) if not lite else ()):
        n = Vector((1, 0, 0)) if axis == 0 else Vector((0, 1, 0))
        c = lo_ + step
        while c < hi_:
            co = Vector((c, 0, 0)) if axis == 0 else Vector((0, c, 0))
            geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
            bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=co, plane_no=n)
            c += step
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for v in bm.verts:
        hgt = v.co.z - z0
        if lite:
            hgt = LITE_LIFT
        x = float(np.interp(v.co.x, s, xs))
        h = _band_top(bvh, x, v.co.y, z0)
        if h is None:
            h = bvh.find_nearest(Vector((x, v.co.y, z0)))
        p, nrm = h[0], h[1].normalized()
        if nrm.z < 0:
            nrm = -nrm
        v.co = p + nrm * hgt
    bm.normal_update()
    bm.to_mesh(d.data)
    bm.free()
    if lite:                       # one layer of letters on a smooth band: smooth, so its vertices are not split per face
        for p in d.data.polygons:
            p.use_smooth = True
        if d.data.attributes.get("sharp_face") is not None:
            d.data.attributes.remove(d.data.attributes["sharp_face"])
    d.data.update()
    return d, width


def _lite_mesh(o, tris, voxel=None):
    """o's geometry welded (UVs and custom normals dropped), voxel-remeshed if `voxel`, decimated to about `tris`."""
    me = o.data
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    if getattr(me, "has_custom_normals", False):
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], selected_editable_objects=[o]):
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for a in ("sharp_edge", "sharp_face"):                 # the import's hard edges split vertices in the GLB
        if me.attributes.get(a) is not None:
            me.attributes.remove(me.attributes[a])
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=LITE_WELD)
    bm.to_mesh(me)
    bm.free()
    if voxel:
        m = o.modifiers.new("remesh", "REMESH")
        m.mode, m.voxel_size = "VOXEL", voxel
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.object.modifier_apply(modifier=m.name)
    have = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if tris < have:
        m = o.modifiers.new("dec", "DECIMATE")
        m.ratio = tris / have
        m.use_collapse_triangulate = True
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.object.modifier_apply(modifier=m.name)
    me = o.data                    # all smooth (the remesh comes out flat): hard edges split vertices in the GLB
    for p in me.polygons:
        p.use_smooth = True
    for a in ("sharp_edge", "sharp_face"):
        if me.attributes.get(a) is not None:
            me.attributes.remove(me.attributes[a])



def _lite_material(mp, key):
    if key in mp:
        return mp[key]
    from lib import materials as M
    n = "mat_wall_hp_fabric_lite"
    return bpy.data.materials.get(n) or M.principled(n, base="#717171", rough=0.9)   # the cloth behind the pads: its texture's mean


def build(coll, mp, root, lite, sfx, board_y, tip_y, wire_r):
    """The headphones under `root` (wall.py's headphones_root). `mp` is wall.py's materials; `board_y` the board's face,
    `tip_y` the hook's up-turned tip and `wire_r` its wire radius, in the root's frame (metres).
    Returns ({"headphones": [...], "headphones_brand": [...]}, {"tilt": deg, "band_top_w": m, "tris": n})."""
    meshes = _import()
    for o in meshes:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
    tilt, R = _place(meshes, board_y, tip_y, wire_r)
    names = {"headphones": [], "headphones_brand": []}
    if lite:
        keep = []
        for o in meshes:
            name, tris, mk = _part(o)
            if tris == 0:
                bpy.data.objects.remove(o, do_unlink=True)
                continue
            _lite_mesh(o, tris, REMESH.get(name))
            o.data.materials.clear()
            o.data.materials.append(_lite_material(mp, mk))
            keep.append(o)
        for o in keep:
            o.select_set(False)
        with bpy.context.temp_override(active_object=keep[0], selected_editable_objects=keep):
            bpy.ops.object.join()
        body = keep[0]
        body.name = "headphones" + sfx
        body.data.name = body.name + "_mesh"
        for p in body.data.polygons:
            p.use_smooth = True
        if LITE_SHARP:
            body.data.set_sharp_from_angle(angle=math.radians(LITE_SHARP))
        bands = [body]
        parts = [body]
    else:
        parts = []
        for o in meshes:
            name, _, _ = _part(o)
            o.name = name + sfx
            o.data.name = o.name + "_mesh"
            parts.append(o)
        bands = [o for o in parts if o.name in ("headphones_band" + sfx, "headphones_band_ends" + sfx)]
    bvh = _bvh(bands)
    d, width = _brand(coll, bvh, lite)
    out = parts + ([d] if d is not None else [])
    for o in out:
        o.data.transform(R)
        o.parent = root
        o.matrix_parent_inverse = Matrix.Identity(4)
        o.matrix_basis = Matrix.Identity(4)
    if lite and not LITE_SHARP:           # the join leaves hard edges (sharp_edge); they split vertices in the GLB
        for o in out:
            a = o.data.attributes.get("sharp_edge")
            if a is not None:
                o.data.attributes.remove(a)
    names["headphones"] = [o.name for o in parts]
    names["headphones_brand"] = [d.name] if d is not None else []
    tris = sum(len(p.vertices) - 2 for o in out for p in o.data.polygons)
    btris = sum(len(p.vertices) - 2 for p in d.data.polygons) if d is not None else 0
    return names, {"tilt": tilt, "band_top_w": round(float(width), 4), "tris": tris, "brand_tris": btris}

