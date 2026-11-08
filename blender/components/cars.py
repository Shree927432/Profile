"""The car display (2026-11-08, stage 1: inspection and options only): four 1:18 scale models on a slim white shelf.

Owner: "can we use the car models that i have downloaded in our rooms some where", "Scale models on a shelf",
"Yes, load it after" (its own GLB, loaded after the room appears). Decision 2026-11-02 in docs/05-decisions.md.

Sources (blender/assets/cars/README.md; the originals stay there untouched, git-ignored), all CC BY 4.0, credited:
  w17      "2026 Mercedes W17" by Tyler_Dave
  porsche  "2024 Porsche 992 GT3 R" by Dave Love (Tyler_Dave)
  gt3      "Mercedes AMG GT3 Evo 2020" by vecarz (heynic)
  one      "Mercedes AMG One" by GT Cars (Car2022)

What the inspection found (2026-11-08, video-local/footage/2026-11-08-cars/inspect/):
  w17      268k tris, 1 object, 31 materials, 34 images (4096 paint, decal and tyre atlases), metres, nose -Y.
           Livery: Petronas teal and silver stripes and a field of Mercedes stars painted into mercedes_paint (4096);
           every sponsor (Petronas, Microsoft, IWC, TeamViewer, CrowdStrike, INEOS, Snapdragon, Solera, AMD, Signify,
           Vercel, FIA, AMG, the star) on separate decal faces (mercedes_decals); number 63 and "George" on their own
           faces; Pirelli P Zero in the tyre atlas. Repaint: easy. The decals are separate faces (delete), the paint
           and halo are their own materials (flat colour), the tyres go flat.
  porsche  489k tris, 151 objects, 91 materials, 36 images, the file is in 1/100 scale units, nose -Y.
           Livery: Manthey "Grello"-style yellow and black with BEND, E-TECK, DHL, Goodyear, Pirelli, number 91 and
           the PORSCHE wordmark (bonnet, rear wing) all in one 4096 carpaint atlas; the crest in EXT_Details (bonnet
           badge, wheel caps) and INT_DECALS; a PORSCHE windscreen banner (EXT_Banner); Pirelli on the tyres.
           Repaint: medium. One body atlas, so the body goes one flat colour (the yellow and black split is lost);
           banner faces deleted, details and interior decals flat.
  gt3      497k tris, 57 objects, 36 materials, 42 images, metres, nose +X.
           Livery: Red Bull (bulls, wordmark), Viaplay, Ravenol, DEKRA, Sparco, H&R, Michelin, number 3, AMG
           wordmarks, all in one 4096 livery atlas multiplied over the paint; the star and BENZ/MERCEDES ring on the
           grille (Grille_Logo); AMG on the side sills (the Exterior_Details atlas, shared with the carbon trim); Michelin on
           the tyres; window stickers. Repaint: medium. The livery is one material (flat colour), the grille logo and the
           exterior-details atlas go flat graphite (the sill carbon weave goes with it), stickers deleted.
  one      275k tris, 68 objects, 54 materials, 53 images, odd units (about 4.2x real), nose +Y. A game-style model.
           Body: already plain white over gloss black (flat materials). Logos on small alpha decals: the star and
           "PERFORMANCE" (Decalchassis0021, Doorrfok0111), the AMG wordmark (Hubrb1, Wheel1, Interior1, Interiora0051),
           AMG on the dash screens (Fsteer0071, Ln4, Ln1). Repaint: easy. Delete the decals, flat the screens.

Frame (every car): the root empty at the car's bottom centre, the nose to +X, Z up, metres, 1:18 of the real length.

Stage 2 (2026-11-08, the owner: "B + Dusk"): placement B (plan_v3.CARS_SHELF: back wall, two shelves left of the neon,
over the light panels) and the Dusk palette. Run:
    B="/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python"
    STAGE=rich,lite $B blender/components/cars.py   rich: out/components/cars.blend (full detail, repainted, logos out,
                                                    on the shelves, about 95 MB); lite: out/components/cars-lite.blend
    STAGE=bake $B blender/components/cars.py        opens out/room_v3_dusk.blend (never saved), bakes the lite cars'
                                                    own lightmap with the dusk rig and the wall's shadow card, writes
                                                    scene/assets/cars.glb and scene/assets/dusk/cars-light.json +
                                                    cars-lightmap.webp, Cycles stills into video-local/footage/2026-11-08-cars/
    env: CARS_LM (1024), CARS_SPP (256), CARD_SPP (512), STILLS=0, RICH_STILL=0
Lite: per car, see-through overlays and parts the room can never see go, seams welded (custom normals cleared) and
collapsed to about 10-12k tris; cars and shelves are one mesh, cars_static, with one palette material (one draw call).
The room's GLB and lightmap do not change.
"""
import os
import re

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.abspath(os.path.join(HERE, ".."))
ASSETS = os.path.join(BL, "assets", "cars")
SCALE = 1 / 18

# key: folder, real length in metres (makers' figures; the W17 from the model, 2026 rules), the nose's axis in the file
CARS = {
    "w17": dict(folder="mercedes_w17", length=None, nose="-Y",
                credit='"2026 Mercedes W17" by Tyler_Dave, CC BY 4.0'),
    "porsche": dict(folder="porsche_992_gt3_r", length=4.619, nose="-Y",
                    credit='"2024 Porsche 992 GT3 R" by Dave Love, CC BY 4.0'),
    "gt3": dict(folder="amg_gt3_evo", length=4.746, nose="+X",
                credit='"Mercedes AMG GT3 Evo 2020" by vecarz, CC BY 4.0'),
    "one": dict(folder="amg_one", length=4.756, nose="+Y",
                credit='"Mercedes AMG One" by GT Cars, CC BY 4.0'),
}

# Repaint rules per car: (material-name regex, role), first match wins; no match keeps the material as it is.
# Roles: paint (the body colour), accent (halo, calipers), trim (flat graphite), tyre (flat rubber),
#        glass (smoked), black (gloss black), delete (the faces go: decal overlays).
RULES = {
    "w17": [(r"^mercedes_decals|^sw_decals|^mercedes_number_63", "delete"),
            (r"^mercedes_paint2|^mercedes_colordriver", "accent"),
            (r"^mercedes_paint", "paint"),
            (r"^tread_medium|^sidewall", "tyre")],
    "porsche": [(r"^EXT_Banner|^INT_BANNER", "delete"),
                (r"^EXT_Carpaint", "paint"),
                (r"^EXT_CALIPER", "accent"),
                (r"^EXT_Details|^INT_DECALS|^INT_Steer$|^DISPLAY|^LED_RACELOGIC", "trim"),
                (r"^MI_Tyre", "tyre")],
    "gt3": [(r"Windows_Stickers", "delete"),
            (r"_Livery", "paint"),
            (r"Grille_Logo|Exterior_Details|Interior_Stickers", "trim"),   # Exterior_Details: AMG on the sills
            (r"Caliper", "accent"),
            (r"Tyre", "tyre")],
    "one": [(r"^(Decalchassis0021|Doorrfok0111|Hubrb1|Wheel1|Interior1|Interiora0051)Mtl", "delete"),
            (r"^(Fsteer0071|Fsteer0081|Ln4|Ln1|Interiore0011|Interiora1)Mtl", "trim"),
            (r"^Doorrfok0011Mtl", "paint"),
            (r"^Doorrfok0021Mtl", "black"),        # the gloss black lower body; its normal map embosses AMG on the fin
            (r"^Hubrb0021Mtl", "accent"),          # the yellow calipers
            (r"^(Doorlfok0071|Doorrfok0101)Mtl", "glass"),
            (r"^Wheel0011Mtl", "tyre")],
}

# Two palettes for the owner (stage 1). Colours sRGB hex; metal 0..1.
PALETTES = {
    "A": dict(label="Lab: white, silver, graphite, one blue accent",
              paint={"w17": ("#ecebe6", 0.0), "porsche": ("#b9bcc1", 0.7), "gt3": ("#2f3136", 0.0), "one": ("#ecebe6", 0.0)},
              accent="#5f9fff"),
    "B": dict(label="Dusk: blue, amber, graphite, pearl",
              paint={"w17": ("#25395b", 0.0), "porsche": ("#c47a35", 0.0), "gt3": ("#34363b", 0.0), "one": ("#ecebe6", 0.0)},
              accent="#d9a066"),
}
TRIM, TYRE = "#232427", "#161617"


def _lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def flat(name, hexcol, rough=0.3, metal=0.0, coat=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    pb = m.node_tree.nodes.get("Principled BSDF")
    pb.inputs["Base Color"].default_value = _lin(hexcol)
    pb.inputs["Roughness"].default_value = rough
    pb.inputs["Metallic"].default_value = metal
    pb.inputs["Coat Weight"].default_value = coat
    pb.inputs["Coat Roughness"].default_value = 0.05
    pb.inputs["Alpha"].default_value = alpha
    return m


def load(key, coll):
    """Import one car into coll; scale to 1:18, nose to +X, bottom centre at the origin, under an empty `car_<key>`."""
    spec = CARS[key]
    d = os.path.join(ASSETS, spec["folder"])
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(d, next(f for f in os.listdir(d) if f.endswith(".glb"))))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH" and len(o.data.polygons)]
    for o in meshes:                         # bake the file's transforms into the data, drop its empties
        mw = o.matrix_world.copy()
        if o.data.users > 1:
            o.data = o.data.copy()
        o.parent = None
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
    for o in new:
        if o not in meshes:
            bpy.data.objects.remove(o, do_unlink=True)
    for o in meshes:
        for c in o.users_collection:
            c.objects.unlink(o)
        coll.objects.link(o)
    v = np.concatenate([_co(o) for o in meshes])
    lo, hi = v.min(0), v.max(0)
    axis = "XYZ".index(spec["nose"][1])
    real = spec["length"] or (hi[axis] - lo[axis])
    s = real * SCALE / (hi[axis] - lo[axis])
    turn = {"+X": 0, "-X": 180, "+Y": -90, "-Y": 90}[spec["nose"]]
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    M = Matrix.Rotation(np.radians(turn), 4, "Z") @ Matrix.Scale(s, 4) @ Matrix.Translation((-cx, -cy, -lo[2]))
    for o in meshes:
        o.data.transform(M)
    root = bpy.data.objects.new(f"car_{key}", None)
    coll.objects.link(root)
    for o in meshes:
        o.parent = root
        o.name = f"car_{key}_" + o.name
    v = np.concatenate([_co(o) for o in meshes])
    return root, meshes, dict(scale=s, size=[round(float(x), 4) for x in v.max(0) - v.min(0)])


def _co(o):
    a = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)


def roles(key, meshes):
    """{material: role} for the materials this car's meshes use."""
    out = {}
    for o in meshes:
        for m in o.data.materials:
            if m is None or m.name in out:
                continue
            out[m.name] = next((r for pat, r in RULES[key] if re.search(pat, m.name)), "keep")
    return out


def _paints(key, palette):
    pal = PALETTES[palette]
    col, metal = pal["paint"][key]
    return {"paint": flat(f"car_{key}_paint", col, rough=0.28 if metal else 0.22, metal=metal, coat=0.8),
            "accent": flat("car_accent", pal["accent"], rough=0.3),
            "trim": flat("car_trim", TRIM, rough=0.55),
            "tyre": flat("car_tyre", TYRE, rough=0.8),
            "glass": flat("car_glass", "#0c0d10", rough=0.04),
            "black": flat("car_black", "#0d0e10", rough=0.25, coat=0.6)}


def repaint(key, meshes, palette):
    """Swap materials by role (once). Delete-role faces are removed. Returns triangles per role.
    Later palettes: recolour(key, palette) changes the same materials' values."""
    mats = _paints(key, palette)
    rl = roles(key, meshes)
    count = {}
    for o in meshes:
        me = o.data
        dead = [i for i, m in enumerate(me.materials) if m is not None and rl.get(m.name) == "delete"]
        n = len(me.polygons)
        mi = np.zeros(n, dtype=np.int32)
        me.polygons.foreach_get("material_index", mi)
        lt = np.zeros(n, dtype=np.int32)
        me.polygons.foreach_get("loop_total", lt)
        tri = lt - 2
        for i, m in enumerate(me.materials):
            r = rl.get(m.name, "keep") if m else "keep"
            count[r] = count.get(r, 0) + int(tri[mi == i].sum())
        if dead:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in dead], context="FACES")
            bm.to_mesh(me)
            bm.free()
        for i, m in enumerate(me.materials):
            r = rl.get(m.name, "keep") if m else "keep"
            if r in mats:
                me.materials[i] = mats[r]
    return count


def recolour(key, palette):
    _paints(key, palette)


# ---------------------------------------------------------------------------
# Stage 2 (2026-11-08, owner: "B + Dusk"): the logos that are geometry, the shelves, rich, lite, the bake, the GLB.
# ---------------------------------------------------------------------------
# Loose parts that are logos, by object and a box in the car's normalised frame (fractions of L, W, H; nose +X):
# (object, (x0, x1), (y0, y1), (z0, z1), largest size in metres at 1:18). Found with ray and island probes.
DROP = {
    "gt3": [("car_gt3_Object_70", (0.44, 0.52), (-0.05, 0.05), (0.25, 0.40), 0.30 / 18),   # the grille star and its ring
            ("car_gt3_Object_79", (-0.56, -0.40), (-0.04, 0.04), (0.57, 0.66), 0.15 / 18),   # the boot lid's star
            ("car_gt3_Object_130", (0.44, 0.48), (-0.03, 0.03), (0.47, 0.53), 0.08 / 18)],  # the bonnet's star
    "one": [("car_one_Object_30", (-0.53, -0.44), (-0.03, 0.03), (0.57, 0.64), 0.05 / 18),   # the rear star
            ("car_one_Object_48", (-0.46, -0.30), (-0.6, 0.6), (0.79, 0.86), 0.30 / 18)],    # AMG on both sides of the fin
    "porsche": [("car_porsche_Object_90", (0.42, 0.48), (-0.03, 0.03), (0.40, 0.47), 0.08 / 18)],  # the bonnet crest
}
# The GT3's AMG mark is cut into both side sills (bars and letters as recesses): covered with a paint-coloured skin
# laid on the sill's outer surface (the recesses filled to the surrounding surface), both sides.
PATCH = {"gt3": dict(x=(-0.085, 0.115), z=(0.11, 0.215), n=(72, 22), dilate=4, lift=0.00004)}


def _islands(bm):
    bm.faces.ensure_lookup_table()
    seen = set()
    for f in bm.faces:
        if f.index in seen:
            continue
        seen.add(f.index)
        stack, isl = [f], []
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        yield isl


def _size(meshes):
    v = np.concatenate([_co(o) for o in meshes])
    return v.max(0) - v.min(0)


def clean(key, meshes):
    """Remove the logos that are geometry (DROP) and cover the cut-in ones (PATCH). Returns what it did."""
    L, W, H = _size(meshes)
    did = []
    byname = {o.name: o for o in meshes}
    for name, xr, yr, zr, cap in DROP.get(key, []):
        o = byname[name]
        bm = bmesh.new()
        bm.from_mesh(o.data)
        dead = []
        for isl in _islands(bm):
            vs = np.array([v.co[:] for f in isl for v in f.verts])
            c, sz = vs.mean(0), vs.max(0) - vs.min(0)
            n = (c[0] / L, c[1] / W, c[2] / H)
            if xr[0] <= n[0] <= xr[1] and yr[0] <= n[1] <= yr[1] and zr[0] <= n[2] <= zr[1] and sz.max() <= cap:
                dead += isl
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bm.to_mesh(o.data)
        bm.free()
        did.append((name, len(dead)))
    if key in PATCH:
        did += _patch(key, meshes, PATCH[key], (L, W, H))
    return did


def _patch(key, meshes, p, size):
    from mathutils.bvhtree import BVHTree
    L, W, H = size
    bm = bmesh.new()
    for o in meshes:
        bm.from_mesh(o.data)
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    paint = bpy.data.materials.get(f"car_{key}_paint")
    out = []
    nu, nv = p["n"]
    xs = np.linspace(p["x"][0] * L, p["x"][1] * L, nu)
    zs = np.linspace(p["z"][0] * H, p["z"][1] * H, nv)
    for side in (1, -1):
        depth = np.full((nv, nu), np.nan)
        for j, z in enumerate(zs):
            for i, x in enumerate(xs):
                hit = bvh.ray_cast(Vector((x, side * W, z)), Vector((0, -side, 0)), 2 * W)
                if hit[0] is not None:
                    depth[j, i] = abs(hit[0].y)
        d = np.where(np.isnan(depth), np.nanmin(depth), depth)
        r = p["dilate"]
        env = d.copy()
        for dj in range(-r, r + 1):
            for di in range(-r, r + 1):
                env = np.maximum(env, np.roll(np.roll(d, dj, 0), di, 1))
        me = bpy.data.meshes.new(f"car_{key}_sill_patch_{'l' if side > 0 else 'r'}")
        verts = [(x, side * (env[j, i] + p["lift"]), z) for j, z in enumerate(zs) for i, x in enumerate(xs)]
        faces = []
        for j in range(nv - 1):
            for i in range(nu - 1):
                a = j * nu + i
                f = (a, a + 1, a + nu + 1, a + nu)
                faces.append(f if side > 0 else f[::-1])
        me.from_pydata(verts, [], faces)
        me.materials.append(paint)
        for poly in me.polygons:
            poly.use_smooth = True
        o = bpy.data.objects.new(me.name, me)
        meshes[0].users_collection[0].objects.link(o)
        o.parent = meshes[0].parent
        meshes.append(o)
        out.append((o.name, len(faces)))
    return out


# ---------------------------------------------------------------------------
# rich: the four cars as downloaded (full detail), repainted in the owner's palette, logos removed, on the shelves
# ---------------------------------------------------------------------------
import json  # noqa: E402
import math  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

sys.path.insert(0, BL)
OUT = os.path.join(BL, "out", "components")
BLEND = os.path.join(OUT, "cars.blend")
LITE_BLEND = os.path.join(OUT, "cars-lite.blend")
REPO = os.path.abspath(os.path.join(BL, ".."))
GLB = os.path.join(REPO, "scene", "assets", "cars.glb")
LIGHT_DIR = os.path.join(REPO, "scene", "assets", "dusk")
FOOT = os.path.join(REPO, "video-local", "footage", "2026-11-08-cars")
PY = "/opt/anaconda3/bin/python3"
PALETTE = "B"                                    # the owner's choice, 2026-11-08: "B + Dusk"
GAP = 0.04                                       # between the two cars on a shelf
SHELF_WHITE = "#f2f2ef"
T0 = time.time()
REPORT = {}


def log(m):
    print(f"MILESTONE {time.time() - T0:6.1f}s {m}", flush=True)


def shelves(coll, root):
    """The two floating shelves (plan_v3.CARS_SHELF): white, 2 mm rounded edges. Returns them and each car's place."""
    from lib import plan_v3 as P
    cs = P.CARS_SHELF
    white = flat("car_shelf_white", SHELF_WHITE, rough=0.45)
    length = cs["x1"] - cs["x0"]
    out, places = [], {}
    for i, under in enumerate(cs["under"]):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(length, cs["d"], cs["t"]), verts=bm.verts)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.002, segments=2, affect="EDGES")
        bmesh.ops.translate(bm, vec=((cs["x0"] + cs["x1"]) / 2, P.RY - cs["d"] / 2, under + cs["t"] / 2), verts=bm.verts)
        me = bpy.data.meshes.new(f"cars_shelf_{i + 1}")
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(me.name, me)
        o.data.materials.append(white)
        coll.objects.link(o)
        o.parent = root
        out.append(o)
        places[i] = (under + cs["t"], cs["rows"][i])
    return out, places, cs


def rich():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sc = bpy.context.scene
    coll = bpy.data.collections.new("cars")
    sc.collection.children.link(coll)
    root = bpy.data.objects.new("set_cars", None)
    coll.objects.link(root)
    sh, places, cs = shelves(coll, root)
    cars = {}
    for k in CARS:
        r, meshes, inf = load(k, coll)
        inf["roles_tris"] = repaint(k, meshes, PALETTE)
        inf["clean"] = clean(k, meshes)
        inf["tris"] = sum(len(o.data.polygons) for o in meshes)
        cars[k] = (r, meshes, inf)
        log(f"rich {k}: {inf['tris']} faces, clean {inf['clean']}")
    from lib import plan_v3 as P
    for i, (top, row) in places.items():
        lens = [cars[k][2]["size"][0] for k in row]
        a = (cs["x0"] + cs["x1"]) / 2 - (sum(lens) + GAP) / 2
        for k, ln in zip(row, lens):
            r = cars[k][0]
            r.matrix_world = Matrix.Translation((a + ln / 2, P.RY - 0.072, top))
            r.parent = root
            r.matrix_parent_inverse = Matrix.Identity(4)
            a += ln + GAP
    REPORT["rich"] = {k: dict(size=v[2]["size"], faces=v[2]["tris"], clean=v[2]["clean"]) for k, v in cars.items()}
    return root, cars, sh


# ---------------------------------------------------------------------------
# lite: the web version. Per car: flat colours, one mesh, welded, decimated; then cars and shelves join into
# cars_static with one palette material (one draw call), as build_v3.py's palettes.
# ---------------------------------------------------------------------------
LITE_FACES = {"w17": 12000, "porsche": 12000, "gt3": 12000, "one": 10000}
WELD = 0.00025                                  # 4.5 mm real: the game-style seams close, so the collapse makes no spikes
CELL = 16


def _srgb(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _image_mean(im):
    """Mean linear colour of an image (scaled down first)."""
    cp = im.copy()
    try:
        if max(cp.size) > 32:
            cp.scale(32, 32)
        px = np.empty(cp.size[0] * cp.size[1] * 4, np.float32)
        cp.pixels.foreach_get(px)
        px = px.reshape(-1, 4)[:, :3]
        if not cp.is_float and not cp.colorspace_settings.is_data:   # byte images hold sRGB-encoded values
            px = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
        return tuple(float(x) for x in px.mean(0))
    finally:
        bpy.data.images.remove(cp)


def flat_value(m):
    """(base linear rgb, roughness, metal) of a material, textures averaged."""
    if m is None or not m.use_nodes:
        return (0.5, 0.5, 0.5), 0.5, 0.0
    pb = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if pb is None:
        return (0.5, 0.5, 0.5), 0.5, 0.0
    bc = pb.inputs["Base Color"]
    base = tuple(bc.default_value[:3])
    if bc.is_linked:
        n = bc.links[0].from_node
        imgs = [x for x in ([n] + [l.from_node for i in n.inputs for l in i.links]) if x.bl_idname == "ShaderNodeTexImage" and x.image]
        base = _image_mean(imgs[0].image) if imgs else (0.5, 0.5, 0.5)
        if n.bl_idname == "ShaderNodeMix" and not n.inputs["B"].is_linked:
            b = n.inputs["B"].default_value
            base = tuple(base[i] * b[i] for i in range(3))
    rough = pb.inputs["Roughness"].default_value if not pb.inputs["Roughness"].is_linked else 0.5
    metal = pb.inputs["Metallic"].default_value if not pb.inputs["Metallic"].is_linked else 0.0
    if pb.inputs["Alpha"].default_value < 0.6 or (pb.inputs["Alpha"].is_linked and "glass" in m.name.lower()):
        base, rough, metal = (0.006, 0.007, 0.009), 0.05, 0.0     # see-through parts: smoked glass, opaque on the web
    return base, float(rough), float(metal)


# Directions the room can see a car from (car frame: nose +X, the wall at +Y): the room side, above, the ends, and
# from a little below (the hero camera stands under the shelves). Never from the wall side.
SEE_FROM = [(1, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (1, -1, 0), (-1, -1, 0), (1, -1, 1), (-1, -1, 1), (0, -1, 1),
            (1, 0, 1), (-1, 0, 1), (0, -1, -0.4), (1, -1, -0.4), (-1, -1, -0.4), (0.3, -1, 0.3), (-0.3, -1, 0.3)]
TINY = 0.0025                                   # loose parts smaller than this (4.5 cm real) go from the lite


def cull_hidden(o):
    """Delete the loose parts the room can never see (inside the body, behind the opaque web glass, wall side only)
    and the tiny ones. Rays from SEE_FROM to the centre and three vertices of each part; a part is seen when any ray
    reaches it first."""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    isl_of = {}
    isls = list(_islands(bm))
    for i, isl in enumerate(isls):
        for f in isl:
            isl_of[f.index] = i
    bvh = BVHTree.FromBMesh(bm)
    dirs = [Vector(d).normalized() for d in SEE_FROM]
    dead, tiny, hidden = [], 0, 0
    for i, isl in enumerate(isls):
        vs = [v.co for f in isl for v in f.verts]
        lo = Vector([min(v[a] for v in vs) for a in range(3)])
        hi = Vector([max(v[a] for v in vs) for a in range(3)])
        if (hi - lo).length < TINY:
            dead += isl
            tiny += 1
            continue
        targets = [(lo + hi) / 2] + [isl[n * len(isl) // 3].calc_center_median() for n in range(3)]
        seen = False
        for t in targets:
            for d in dirs:
                hit = bvh.ray_cast(t + d * 0.5, -d, 0.6)
                if hit[2] is not None and isl_of.get(hit[2]) == i:
                    seen = True
                    break
            if seen:
                break
        if not seen:
            dead += isl
            hidden += 1
    bmesh.ops.delete(bm, geom=list(set(dead)), context="FACES")
    bm.to_mesh(o.data)
    bm.free()
    return dict(parts=len(isls), tiny=tiny, hidden=hidden, faces_after=len(o.data.polygons))


GLASS = re.compile(r"glass|window|windshield|windscreen", re.I)


def _overlay(m):
    if m is None or not m.use_nodes or GLASS.search(m.name) or m.name.startswith("car_"):
        return False
    pb = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if pb is None:
        return False
    a = pb.inputs["Alpha"]
    return a.is_linked or a.default_value < 0.6


def lite(cars, sh):
    """cars: {key: (root, meshes, info)} from rich(). Builds cars_static (and keeps the rich objects untouched by working
    on copies). Returns the new object."""
    bpy.context.view_layer.update()              # the cars were just moved onto the shelves: fresh world matrices
    coll = bpy.data.collections.new("cars_lite")
    bpy.context.scene.collection.children.link(coll)
    parts = []
    stats = {}
    for k, (r, meshes, inf) in cars.items():
        copies = []
        for o in meshes:
            c = o.copy()
            c.data = o.data.copy()
            c.parent = None
            c.matrix_world = o.matrix_world.copy()
            coll.objects.link(c)
            copies.append(c)
        bpy.context.view_layer.update()
        for c in copies:
            c.data.transform(c.matrix_world)
            c.matrix_world = Matrix.Identity(4)
        bpy.ops.object.select_all(action="DESELECT")
        for c in copies:
            c.select_set(True)
        bpy.context.view_layer.objects.active = copies[0]
        bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active
        j.name = f"cars_lite_{k}"
        before = len(j.data.polygons)
        # see-through overlays (motion-blur rim discs, decal cards, invisible helper parts) would turn into solid
        # discs as flat colours: their faces leave the lite; glass stays (smoked, opaque on the web)
        over = [i for i, m in enumerate(j.data.materials) if _overlay(m)]
        if over:
            bm = bmesh.new()
            bm.from_mesh(j.data)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in over], context="FACES")
            bm.to_mesh(j.data)
            bm.free()
        culled = cull_hidden(j)
        # weld the seams and drop the custom normals first: on the raw game-style meshes (split vertices at every
        # seam, custom normals) the collapse tore panels and threw spikes (2026-11-08, the first lite)
        bm = bmesh.new()
        bm.from_mesh(j.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD)
        bm.to_mesh(j.data)
        bm.free()
        with bpy.context.temp_override(object=j, active_object=j, selected_objects=[j], selected_editable_objects=[j]):
            if j.data.has_custom_normals:
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
        for _ in range(2):
            tri = sum(len(p.vertices) - 2 for p in j.data.polygons)
            if tri <= LITE_FACES[k] * 1.1:
                break
            mod = j.modifiers.new("dec", "DECIMATE")
            mod.ratio = min(1.0, LITE_FACES[k] / max(1, tri))
            mod.use_collapse_triangulate = True
            with bpy.context.temp_override(object=j, active_object=j):
                bpy.ops.object.modifier_apply(modifier="dec")
        for uv in list(j.data.uv_layers)[1:]:   # the palette writes the first; the bake adds LM
            j.data.uv_layers.remove(uv)
        for p in j.data.polygons:
            p.use_smooth = True
        stats[k] = dict(before=before, culled=culled, after=sum(len(p.vertices) - 2 for p in j.data.polygons))
        parts.append(j)
        log(f"lite {k}: {before} faces -> {stats[k]['after']} tris")
    for s in sh:
        c = s.copy()
        c.data = s.data.copy()
        c.parent = None
        c.matrix_world = s.matrix_world.copy()
        coll.objects.link(c)
        bpy.context.view_layer.update()
        c.data.transform(c.matrix_world)
        c.matrix_world = Matrix.Identity(4)
        parts.append(c)
    REPORT["lite"] = stats
    # one palette material: every source material becomes a cell (colour, roughness, metal)
    cells, cell_of = [], {}
    for o in parts:
        for m in o.data.materials:
            if m is None or m.name in cell_of:
                continue
            v = flat_value(m)
            sig = (tuple(round(x, 3) for x in v[0]), round(v[1], 2), round(v[2], 2))
            if sig not in [c[0] for c in cells]:
                cells.append((sig, v))
            cell_of[m.name] = [c[0] for c in cells].index(sig)
    per_row = 16
    rows = (len(cells) + per_row - 1) // per_row
    w, h = per_row * CELL, rows * CELL

    def img(name, vals, srgb):
        im = bpy.data.images.new(name, w, h, alpha=False)
        im.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
        px = np.ones((h, w, 4), np.float32)
        for i, c in enumerate(vals):
            r_, col = divmod(i, per_row)
            px[r_ * CELL:(r_ + 1) * CELL, col * CELL:(col + 1) * CELL, :3] = [_srgb(x) for x in c] if srgb else c
        im.pixels.foreach_set(px.ravel())
        im.pack()
        return im
    pal = bpy.data.materials.new("mat_cars_palette")
    pal.use_nodes = True
    nt = pal.node_tree
    pb = nt.nodes["Principled BSDF"]
    t1 = nt.nodes.new("ShaderNodeTexImage")
    t1.image, t1.interpolation = img("cars_palette_base", [c[1][0] for c in cells], True), "Closest"
    nt.links.new(t1.outputs["Color"], pb.inputs["Base Color"])
    t2 = nt.nodes.new("ShaderNodeTexImage")
    t2.image, t2.interpolation = img("cars_palette_mr", [(0.0, c[1][1], c[1][2]) for c in cells], False), "Closest"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(t2.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], pb.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], pb.inputs["Metallic"])
    pb.inputs["Specular IOR Level"].default_value = 0.5
    for o in parts:
        me = o.data
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        n = len(me.polygons)
        mi = np.zeros(n, np.int32)
        me.polygons.foreach_get("material_index", mi)
        lt = np.zeros(n, np.int32)
        me.polygons.foreach_get("loop_total", lt)
        cell = np.array([cell_of.get(m.name, 0) if m else 0 for m in me.materials] or [0], np.int32)[mi]
        cl = np.repeat(cell, lt)
        r_, col = np.divmod(cl, per_row)
        uv = np.stack([(col + 0.5) * CELL / w, (r_ + 0.5) * CELL / h], 1).astype(np.float32)
        me.uv_layers[0].data.foreach_set("uv", uv.ravel())
        me.materials.clear()
        me.materials.append(pal)
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = j.data.name = "cars_static"
    j.data.name = "cars_static_mesh"
    REPORT["lite"]["total_tris"] = sum(len(p.vertices) - 2 for p in j.data.polygons)
    REPORT["lite"]["palette_cells"] = len(cells)
    log(f"cars_static {REPORT['lite']['total_tris']} tris, {len(cells)} palette cells")
    return j


# ---------------------------------------------------------------------------
# bake + export (a second Blender run): the lite cars in the dusk room (blender/out/room_v3_dusk.blend, opened, never
# saved), their own lightmap from the same rig, a soft shadow card for the wall, the GLB and its light file.
# ---------------------------------------------------------------------------
LM_PX = int(os.environ.get("CARS_LM", "1024"))
LM_SPP = int(os.environ.get("CARS_SPP", "256"))
CARD = dict(pad=0.12, px_per_m=320, lift=0.001)   # the shadow card: margin around the shelves, texels per metre


def _bake_card(card, img, samples):
    """Cycles DIFFUSE (direct + indirect, no colour) of the card into img through its UVMap."""
    from lib import lighting_dusk as LD
    LD._cycles(samples, False)
    m = card.data.materials[0]
    t = m.node_tree.nodes.get("card_bake") or m.node_tree.nodes.new("ShaderNodeTexImage")
    t.name, t.image = "card_bake", img
    m.node_tree.nodes.active = t
    bpy.ops.object.select_all(action="DESELECT")
    card.select_set(True)
    bpy.context.view_layer.objects.active = card
    b = bpy.context.scene.render.bake
    b.use_pass_direct, b.use_pass_indirect, b.use_pass_color = True, True, False
    b.margin, b.target, b.use_clear = 2, "IMAGE_TEXTURES", True
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=2, use_clear=True)
    px = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(img.size[1], img.size[0], 4)[..., :3].mean(2)


def _blur(a, taps=((-3, 0.071), (-2, 0.131), (-1, 0.189), (0, 0.214), (1, 0.189), (2, 0.131), (3, 0.071))):
    for axis in (0, 1):
        a = sum(w * np.roll(a, o, axis) for o, w in taps)
    return a


def shadow_card(cars_static):
    """A plane 1 mm off the back wall behind the shelves. Its alpha is how much the shelves and cars darken the wall:
    1 - (light with them) / (light without them), both baked here; drawn black, so the room's own baked wall shows
    through scaled by that ratio. No room rebake."""
    from lib import plan_v3 as P
    cs = P.CARS_SHELF
    x0, x1 = cs["x0"] - CARD["pad"], cs["x1"] + CARD["pad"]
    z0, z1 = cs["under"][0] - CARD["pad"] - 0.06, cs["under"][1] + cs["t"] + cs["car_h"] + CARD["pad"]
    y = P.RY - CARD["lift"]
    me = bpy.data.meshes.new("cars_shadow_mesh")
    me.from_pydata([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [], [(0, 1, 2, 3)])   # faces the room (-Y)
    uv = me.uv_layers.new(name="UVMap")
    for loop, (u, v) in zip(me.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[loop.index].uv = (u, v)
    card = bpy.data.objects.new("cars_shadow", me)
    bpy.context.scene.collection.objects.link(card)
    m = flat("mat_cars_shadow_bake", "#eeeeea", rough=0.9)
    me.materials.append(m)
    w, h = int((x1 - x0) * CARD["px_per_m"]), int((z1 - z0) * CARD["px_per_m"])
    img = bpy.data.images.new("cars_shadow_bake", w, h, alpha=True, float_buffer=True)
    spp = int(os.environ.get("CARD_SPP", "512"))
    lit_with = _bake_card(card, img, spp)
    cars_static.hide_render = True
    lit_without = _bake_card(card, img, spp)
    cars_static.hide_render = False
    ratio = np.clip(_blur(_blur(lit_with)) / np.maximum(_blur(_blur(lit_without)), 1e-5), 0, 1)   # two passes: soft, no grain
    alpha = 1 - ratio
    # fade to zero at the card's edges so it never shows as a rectangle
    fy = np.clip(np.minimum(np.arange(h), h - 1 - np.arange(h)) / (0.25 * CARD["px_per_m"] * CARD["pad"] * 4), 0, 1)
    fx = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / (0.25 * CARD["px_per_m"] * CARD["pad"] * 4), 0, 1)
    alpha = alpha * fy[:, None] * fx[None, :]
    out = bpy.data.images.new("cars_shadow", w, h, alpha=True)
    px = np.zeros((h, w, 4), np.float32)
    px[..., 3] = alpha
    out.pixels.foreach_set(px.ravel())
    out.pack()
    # the material the GLB carries: black, its alpha from the image (BLEND); the site draws it unlit
    mm = bpy.data.materials.new("mat_cars_shadow")
    mm.use_nodes = True
    nt = mm.node_tree
    pb = nt.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (0, 0, 0, 1)
    pb.inputs["Roughness"].default_value = 1.0
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = out
    nt.links.new(t.outputs["Alpha"], pb.inputs["Alpha"])
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        if hasattr(mm, attr):
            try:
                setattr(mm, attr, val)
            except Exception:
                pass
    me.materials.clear()
    me.materials.append(mm)
    REPORT["shadow_card"] = dict(px=[w, h], max_alpha=round(float(alpha.max()), 3), mean_alpha=round(float(alpha.mean()), 4))
    log(f"shadow card {w}x{h}, alpha max {alpha.max():.2f}")
    return card


def encode_lightmap(exr_img, name):
    """As blender/tools/encode_dusk.py: masked blur, gaps filled outwards, light / max (99.8th percentile) as sRGB
    8-bit WebP. Returns max."""
    w, h = exr_img.size
    px = np.empty(w * h * 4, np.float32)
    exr_img.pixels.foreach_get(px)
    lm = px.reshape(h, w, 4)[::-1].copy()
    mask = lm[..., 3] > 0.5
    rgb = lm[..., :3]
    num, den = rgb * mask[..., None], mask.astype(np.float32)
    taps = ((-2, 0.12), (-1, 0.23), (0, 0.30), (1, 0.23), (2, 0.12))
    for axis in (0, 1):
        num = sum(wt * np.roll(num, o, axis) for o, wt in taps)
        den = sum(wt * np.roll(den, o, axis) for o, wt in taps)
    ok = mask & (den > 1e-4)
    rgb = rgb.copy()
    rgb[ok] = num[ok] / den[ok][:, None]
    m2 = mask.copy()
    for _ in range(16):
        acc, cnt = np.zeros_like(rgb), np.zeros(m2.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            mm = np.roll(np.roll(m2, dy, 0), dx, 1)
            acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * mm[..., None]
            cnt += mm
        new = (~m2) & (cnt > 0)
        if not new.any():
            break
        rgb[new] = acc[new] / cnt[new][:, None]
        m2 |= new
    lmax = float(np.percentile(rgb[mask].max(axis=1), 99.8))
    x = np.clip(rgb / lmax, 0, 1)
    x = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    tmp = os.path.join(BL, "out", "dusk", "enc")
    os.makedirs(tmp, exist_ok=True)
    png = os.path.join(tmp, name + ".png")
    im = bpy.data.images.new(name + "_png", w, h, alpha=False)
    im.colorspace_settings.name = "Non-Color"
    o = np.ones((h, w, 4), np.float32)
    o[..., :3] = x
    im.pixels.foreach_set(o[::-1].ravel())
    im.filepath_raw, im.file_format = png, "PNG"
    im.save()
    code = ("import sys\nfrom PIL import Image\nImage.open(sys.argv[1]).convert('RGB').save(sys.argv[2],'WEBP',"
            "quality=int(sys.argv[3]),method=6)\n")
    subprocess.run([PY, "-c", code, png, os.path.join(LIGHT_DIR, name + ".webp"), os.environ.get("CARS_LM_Q", "86")], check=True)
    os.remove(png)
    REPORT["lightmap"] = dict(px=[w, h], coverage=round(float(mask.mean()), 3), max=round(lmax, 4))
    return lmax


def bake_export():
    from lib import lighting_dusk as LD
    from lib import plan_v3 as P
    bpy.ops.wm.open_mainfile(filepath=os.path.join(BL, "out", "room_v3_dusk.blend"))
    log("opened room_v3_dusk.blend (never saved)")
    with bpy.data.libraries.load(LITE_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in ("cars_static", "set_cars_lite")]
    sc = bpy.context.scene
    for o in dst.objects:
        if o is not None:
            sc.collection.objects.link(o)
    cs = bpy.data.objects["cars_static"]
    root = bpy.data.objects.get("set_cars_lite")
    if root is not None:
        root.name = "set_cars"
    else:
        root = bpy.data.objects.new("set_cars", None)
        sc.collection.objects.link(root)
    if pmset_low():
        raise SystemExit("battery under 30 % and discharging: no bake")
    LD.lightmap_uvs([cs], margin=0.004)
    os.makedirs(os.path.join(BL, "out", "dusk"), exist_ok=True)
    t = time.time()
    LD.bake([cs], os.path.join(BL, "out", "dusk", "cars-lightmap.exr"), LM_PX, LM_SPP)
    log(f"cars bake {LM_PX}px {LM_SPP} spp {time.time() - t:.0f} s")
    exr = bpy.data.images.load(os.path.join(BL, "out", "dusk", "cars-lightmap.exr"), check_existing=False)
    lmax = encode_lightmap(exr, "cars-lightmap")
    card = shadow_card(cs)
    for o in (cs, card):
        o.parent = root
    # the light file next to the room's (scene/assets/dusk/room-light.json): the same exposure applies
    with open(os.path.join(LIGHT_DIR, "cars-light.json"), "w") as f:
        json.dump(dict(note="Written by blender/components/cars.py from its own Cycles bake in the dusk room. light = texel * max; "
                            "the room's exposure (room-light.json) applies.",
                       glb="/scene/assets/cars.glb", lightmap=dict(file="cars-lightmap.webp", max=round(lmax, 4)),
                       shadow="cars_shadow"), f, indent=1)
    # export only the cars
    bpy.ops.object.select_all(action="DESELECT")
    for o in (root, cs, card):
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                              export_cameras=False, export_lights=False, export_extras=False, export_image_format="WEBP",
                              export_image_quality=80, export_draco_mesh_compression_enable=True,
                              export_draco_mesh_compression_level=7, export_draco_position_quantization=14,
                              export_draco_normal_quantization=10, export_draco_texcoord_quantization=12)
    REPORT["glb_bytes"] = os.path.getsize(GLB)
    REPORT["lightmap_bytes"] = os.path.getsize(os.path.join(LIGHT_DIR, "cars-lightmap.webp"))
    log(f"cars.glb {REPORT['glb_bytes'] / 1e3:.0f} KB, lightmap {REPORT['lightmap_bytes'] / 1e3:.0f} KB")
    if os.environ.get("STILLS", "1") == "1":
        stills(cs, card)


def pmset_low():
    try:
        out = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True).stdout
        pct = int(out.split("%")[0].split()[-1])
        return pct < 30 and "discharging" in out
    except Exception:
        return False


def _cam(name, pos, target, vfov):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(c)
    c.location = pos
    c.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    c.data.sensor_fit = "VERTICAL"
    c.data.angle_y = math.radians(vfov)
    c.data.clip_start = 0.02
    return c


def stills(cs, card):
    """Cycles stills of the lite cars in the room (what the site shows, lit by Cycles): hero, the site's phone frame,
    a close-up; then the rich cars (cars.blend) in the same close-up."""
    from lib import lighting_dusk as LD
    from lib import plan_v3 as P
    os.makedirs(FOOT, exist_ok=True)
    sc = bpy.context.scene
    card.hide_render = True                        # Cycles draws the real shadow; the card is for the site
    LD._cycles(int(os.environ.get("STILL_SPP", "48")), True)
    sc.cycles.time_limit = 150.0
    sc.render.image_settings.file_format = "PNG"
    H = P.HERO_V3
    shots = [("hero", _cam("cars_still_hero", H["pos"], H["target"], H["vfov"]), (1600, 900)),
             ("phone", _cam("cars_still_phone", H["pos"], (-1.90, P.YM, 1.44), H["portrait_vfov"]), (750, 1624)),
             ("close", _cam("cars_still_close", (-1.05, 0.95, 1.95), (-1.61, P.RY, 2.17), 34), (1600, 900))]
    for name, cam, res in shots:
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.resolution_percentage = 100
        sc.render.filepath = os.path.join(FOOT, f"after-{name}.png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        log(f"still {name} {time.time() - t:.0f} s")
    if os.environ.get("RICH_STILL", "1") == "1" and os.path.exists(BLEND):
        cs.hide_render = True
        with bpy.data.libraries.load(BLEND, link=False) as (src, dst):
            dst.objects = list(src.objects)
        for o in dst.objects:
            if o is not None and o.name != "set_cars":
                sc.collection.objects.link(o)
        sc.camera = bpy.data.objects["cars_still_close"]
        sc.render.resolution_x, sc.render.resolution_y = 1600, 900
        sc.render.filepath = os.path.join(FOOT, "after-close-rich.png")
        bpy.ops.render.render(write_still=True)
        log("still close-rich")


def main():
    stage = os.environ.get("STAGE", "rich,lite")
    os.makedirs(OUT, exist_ok=True)
    if "rich" in stage:
        root, cars, sh = rich()
        bpy.data.orphans_purge(do_recursive=True)
        from lib.blendfile import pack_and_save
        pack_and_save(BLEND, compress=True)
        log(f"saved {BLEND} {os.path.getsize(BLEND) / 1e6:.0f} MB")
        if "lite" in stage:
            j = lite(cars, sh)
            keep = {j}
            for o in list(bpy.data.objects):
                if o not in keep:
                    bpy.data.objects.remove(o, do_unlink=True)
            r = bpy.data.objects.new("set_cars_lite", None)
            bpy.context.scene.collection.objects.link(r)
            bpy.data.orphans_purge(do_recursive=True)
            bpy.ops.wm.save_as_mainfile(filepath=LITE_BLEND, compress=True)
            log(f"saved {LITE_BLEND} {os.path.getsize(LITE_BLEND) / 1e6:.1f} MB")
    if "bake" in stage:
        bake_export()
    rep = os.path.join(FOOT, f"cars-report-{stage.replace(',', '-')}.json")
    os.makedirs(FOOT, exist_ok=True)
    with open(rep, "w") as f:
        json.dump(REPORT, f, indent=1, default=str)
    log("done")


if __name__ == "__main__":
    main()
