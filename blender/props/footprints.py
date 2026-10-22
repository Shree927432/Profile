"""Footprints: every root on the approved room plan that is not modelled yet, as simple
named shapes to scale, so the room shell can be judged whole. Each later step replaces
one root's footprint with the real prop.

Positions and sizes come from LAYOUT, WALL_GUITARS, WINDOW, SWITCH and LIGHT in
blender/lib/constants.py, through blender/design/room_plan_sheet.py where the sheet
already derives them (speaker toe-in, rack slots, guitar outlines), so the sheet and the
model cannot disagree. The real roots are used (obj_studio, set_bed, ...); their parts
are named `<word>_footprint_*`, never a name from MESHES.md, and the export joins each
root's footprint into `<word>_static`.
"""
import math
import os
import sys

import bpy

from lib import constants as C, geo, materials as M

sys.path.insert(0, os.path.join(C.BLENDER_DIR, "design"))
import room_plan_sheet as PLAN  # noqa: E402

L, WG, WIN, H = C.LAYOUT, C.WALL_GUITARS, C.WINDOW, C.ROOM["height"]
RX, RY = C.RX, C.RY
TOP = L["desk"]["h"]
ROOTS = []                      # (root name, [part objects]) in build order


def _mat(name, colour, **v):
    return M.principled(name, base=colour, **v)


def _root(name):
    r, coll = geo.root(name)
    return r, dict(collection=coll, parent=r)


def _done(root, parts):
    ROOTS.append((root.name, parts))
    return root


def build_window():
    r, kw = _root("obj_window")
    frame_m = _mat("mat_fp_window_frame", "#2c2b29", metal=0.5, rough=0.4)
    grill_m = _mat("mat_fp_window_grill", "#3b3f4a", metal=0.4, rough=0.5)
    x0, x1, z0, z1 = WIN["x0"], WIN["x1"], WIN["sill"], WIN["head"]
    y0, y1 = RY + 0.07, RY + 0.12                    # set back in the reveal
    f = 0.04
    xm = (x0 + x1) / 2
    frame = geo.boxes("window_footprint_frame", [
        (x0, x1, y0, y1, z0, z0 + f), (x0, x1, y0, y1, z1 - f, z1),
        (x0, x0 + f, y0, y1, z0, z1), (x1 - f, x1, y0, y1, z0, z1),
        (xm - 0.02, xm + 0.02, y0 - 0.02, y1, z0, z1)], material=frame_m, **kw)
    geo.bevel(frame, 0.003, segments=2)
    bars = [(0.007, (x0, RY + 0.03, z0 + (z1 - z0) * k / 9), (x1, RY + 0.03, z0 + (z1 - z0) * k / 9))
            for k in range(1, 9)]
    grill = geo.cylinders("window_footprint_grill", bars, segments=8, material=grill_m, **kw)
    return _done(r, [frame, grill])


def build_light():
    r, kw = _root("obj_light")
    lt, sw = C.LIGHT, C.SWITCH
    white = _mat("mat_fp_light_shade", "#ecebe6", rough=0.5, sss=0.2)
    cord_m = _mat("mat_fp_light_cord", "#2a2a2a", rough=0.6)
    plate_m = _mat("mat_fp_switch", "#eeeeea", rough=0.35)
    zb = H - lt["drop"] - lt["shade_h"]
    canopy = geo.cylinder("light_footprint_canopy", lt["canopy_d"] / 2, (lt["x"], lt["y"], H - 0.03),
                          (lt["x"], lt["y"], H), segments=32, material=white, **kw)
    cord = geo.cylinder("light_footprint_cord", 0.003, (lt["x"], lt["y"], zb + lt["shade_h"]), (lt["x"], lt["y"], H),
                        segments=8, material=cord_m, **kw)
    # dome shade: a lathe of a quarter ellipse, open below
    import bmesh
    bm = bmesh.new()
    prof = [(lt["shade_d"] / 2 * math.cos(a), lt["shade_h"] * math.sin(a))
            for a in [math.pi / 2 * i / 10 for i in range(11)]]
    rings = []
    for k in range(40):
        a = 2 * math.pi * k / 40
        rings.append([bm.verts.new((lt["x"] + max(rr, 0.004) * math.cos(a), lt["y"] + max(rr, 0.004) * math.sin(a),
                                    zb + zz)) for rr, zz in prof])
    for k in range(40):
        a, b = rings[k], rings[(k + 1) % 40]
        for i in range(len(prof) - 1):
            bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    shade = geo.from_bmesh("light_footprint_shade", bm, material=white, **kw)
    sol = shade.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = 0.003
    plate = geo.box("light_footprint_switch", -RX, -RX + 0.012, sw["y"] - sw["w"] / 2, sw["y"] + sw["w"] / 2,
                    sw["z"] - sw["h"] / 2, sw["z"] + sw["h"] / 2, material=plate_m, **kw)
    geo.bevel(plate, 0.003, segments=2)
    return _done(r, [canopy, cord, shade, plate])


def build_chair():
    r, kw = _root("set_chair")
    ch = L["chair"]
    m = _mat("mat_fp_chair", "#2c2d33", rough=0.7, sheen=0.3)
    seat = geo.box("chair_footprint_seat", -0.25, 0.25, -0.25, 0.25, ch["seat"] - 0.07, ch["seat"], material=m, **kw)
    back = geo.box("chair_footprint_back", -0.23, 0.23, 0.21, 0.26, ch["seat"] + 0.05, ch["h"], material=m, **kw)
    for o in (seat, back):
        geo.bevel(o, 0.02, segments=3)
    legs = [(0.025, (0, 0, 0.08), (0, 0, ch["seat"] - 0.07))]
    legs += [(0.014, (0, 0, 0.08), (0.31 * math.cos(2 * math.pi * k / 5), 0.31 * math.sin(2 * math.pi * k / 5), 0.04))
             for k in range(5)]
    base = geo.cylinders("chair_footprint_base", legs, segments=10, material=m, **kw)
    for o in (seat, back, base):
        geo.place(o, (ch["x"], ch["y"], 0), ch["yaw"])
    return _done(r, [base, seat, back])


def build_studio():
    r, kw = _root("obj_studio")
    blk = _mat("mat_fp_speaker", "#1e1f23", rough=0.6)
    cone = _mat("mat_fp_woofer", "#0c0c0d", rough=0.5)
    pad_m = _mat("mat_fp_pad", "#3a3b40", rough=0.9)
    dj_m = _mat("mat_fp_dj", "#2f3035", rough=0.55)
    jog_m = _mat("mat_fp_jog", "#5a5c63", metal=0.6, rough=0.3)
    box_m = _mat("mat_fp_interface", "#45474e", metal=0.3, rough=0.4)
    stick_w = _mat("mat_fp_stick_handle", "#f2f2f2", rough=0.3)
    stick_h = _mat("mat_fp_stick_head", "#e9c6f2", rough=0.2, sss=0.3, emit="#e9c6f2", emit_strength=0.0)
    spk = L["speakers"]
    parts = []
    for i, s in enumerate(PLAN.SPEAKERS):
        n = f"{i + 1:02d}"
        pad = geo.box(f"studio_footprint_pad_{n}", -0.10, 0.10, -0.135, 0.135, TOP, TOP + spk["pad_h"],
                      material=pad_m, **kw)
        z0 = TOP + spk["pad_h"]
        cab = geo.box(f"studio_footprint_speaker_{n}", -spk["w"] / 2, spk["w"] / 2, -spk["d"] / 2, spk["d"] / 2,
                      z0, z0 + spk["h"], material=blk, **kw)
        geo.bevel(cab, 0.012, segments=4)
        woof = geo.cylinder(f"studio_footprint_woofer_{n}", 0.062, (0, -spk["d"] / 2 + 0.004, z0 + 0.10),
                            (0, -spk["d"] / 2 - 0.004, z0 + 0.10), segments=32, material=cone, **kw)
        tw = geo.box(f"studio_footprint_tweeter_{n}", -0.03, 0.03, -spk["d"] / 2 - 0.004, -spk["d"] / 2 + 0.002,
                     z0 + 0.19, z0 + 0.24, material=cone, **kw)
        for o in (pad, cab, woof, tw):
            geo.place(o, (s["x"], s["y"], 0), s["yaw"])
        parts += [pad, cab, woof, tw]
    dj = L["dj"]
    body = geo.box("studio_footprint_dj", dj["x"] - dj["w"] / 2, dj["x"] + dj["w"] / 2, dj["y"] - dj["d"] / 2,
                   dj["y"] + dj["d"] / 2, TOP, TOP + dj["h"], material=dj_m, **kw)
    geo.bevel(body, 0.006, segments=3)
    jogs = geo.cylinders("studio_footprint_jogs", [
        (0.065, (dj["x"] + sx * 0.12, dj["y"] + 0.03, TOP + dj["h"]), (dj["x"] + sx * 0.12, dj["y"] + 0.03,
                                                                          TOP + dj["h"] + 0.012)) for sx in (-1, 1)],
        segments=40, material=jog_m, **kw)
    it = L["interface"]
    iface = geo.box("studio_footprint_interface", it["x"] - it["w"] / 2, it["x"] + it["w"] / 2, it["y"] - it["d"] / 2,
                    it["y"] + it["d"] / 2, TOP, TOP + it["h"], material=box_m, **kw)
    geo.bevel(iface, 0.004, segments=3)
    ls = L["lightstick"]
    handle = geo.cylinder("studio_footprint_stick_handle", 0.016, (ls["x"] - ls["w"] / 2, ls["y"], TOP + 0.017),
                          (ls["x"] + 0.03, ls["y"], TOP + 0.017), segments=16, material=stick_w, **kw)
    head = geo.cylinder("studio_footprint_stick_head", ls["d"] / 2, (ls["x"] + 0.03, ls["y"], TOP + ls["h"] / 2),
                        (ls["x"] + ls["w"] / 2, ls["y"], TOP + ls["h"] / 2), segments=8, material=stick_h, **kw)
    geo.bevel(head, 0.01, segments=3)
    parts += [body, jogs, iface, handle, head]
    return _done(r, parts)


def build_mic():
    r, kw = _root("obj_mic")
    m = _mat("mat_fp_mic", "#26272b", metal=0.4, rough=0.45)
    mc = L["mic"]
    cl = (*mc["clamp"], TOP)
    up = (cl[0], cl[1], TOP + 0.08)
    arm = geo.cylinders("mic_footprint_arm", [(0.008, cl, up), (0.008, up, mc["elbow"]),
                                              (0.008, mc["elbow"], mc["capsule"])], segments=10, material=m, **kw)
    cx, cy, cz = mc["capsule"]
    cap = geo.cylinder("mic_footprint_capsule", 0.028, (cx, cy, cz - 0.07), (cx, cy, cz + 0.06), segments=24,
                       material=m, **kw)
    geo.bevel(cap, 0.012, segments=3)
    return _done(r, [arm, cap])


def build_bookshelf():
    r, kw = _root("set_bookshelf")
    bs = L["bookshelf"]
    wood = _mat("mat_fp_shelf", "#3e2c20", rough=0.55)
    books_m = M.tinted("mat_fp_books", rough=0.6)
    x0, x1 = -RX, -RX + bs["d"]
    y0, y1 = bs["y"] - bs["w"] / 2, bs["y"] + bs["w"] / 2
    t = 0.018
    shelves = 5
    specs = [(x0, x1, y0, y0 + t, 0, bs["h"]), (x0, x1, y1 - t, y1, 0, bs["h"]), (x0, x0 + 0.006, y0, y1, 0, bs["h"])]
    specs += [(x0, x1, y0, y1, k * (bs["h"] - t) / shelves, k * (bs["h"] - t) / shelves + t) for k in range(shelves + 1)]
    case = geo.boxes("bookshelf_footprint_case", specs, material=wood, **kw)
    geo.bevel(case, 0.002, segments=2)
    import random
    rng = random.Random(4)
    objs = []
    cols = ["#7b2d26", "#2d4a6b", "#c9b48a", "#3f5e3a", "#d8d2c4", "#5b3b5e", "#a3622a", "#1f2a33"]
    for k in range(shelves):
        z = k * (bs["h"] - t) / shelves + t
        room = (bs["h"] - t) / shelves - t - 0.02
        y = y0 + t + 0.01
        while y < y1 - t - 0.04:
            bw = rng.uniform(0.018, 0.04)
            bh = room * rng.uniform(0.7, 0.95)
            b = geo.box(f"bookshelf_footprint_book_{len(objs):03d}", x0 + 0.03, x0 + 0.03 + rng.uniform(0.17, 0.24),
                        y, y + bw, z, z + bh, material=books_m, **kw)
            geo.tint(b, rng.choice(cols))
            objs.append(b)
            y += bw + rng.uniform(0.0, 0.004)
    books = geo.join(objs, "bookshelf_footprint_books")
    return _done(r, [case, books])


def build_frames():
    r, kw = _root("obj_frames")
    fr = L["frames"]
    border = _mat("mat_fp_frame", "#1f1d1b", rough=0.4)
    pics = [_mat(f"mat_fp_picture_{i + 1:02d}", c, rough=0.6) for i, c in enumerate(("#c98a4a", "#5d7f9e", "#9aa27a"))]
    parts = []
    for i, y in enumerate(fr["y"]):
        n = f"{i + 1:02d}"
        b = geo.box(f"frames_footprint_{n}", -RX, -RX + fr["t"], y - fr["w"] / 2, y + fr["w"] / 2,
                    fr["z"] - fr["h"] / 2, fr["z"] + fr["h"] / 2, material=border, **kw)
        geo.bevel(b, 0.003, segments=2)
        p = geo.box(f"frames_footprint_picture_{n}", -RX + fr["t"], -RX + fr["t"] + 0.002, y - fr["w"] / 2 + 0.035,
                    y + fr["w"] / 2 - 0.035, fr["z"] - fr["h"] / 2 + 0.04, fr["z"] + fr["h"] / 2 - 0.04,
                    material=pics[i], **kw)
        parts += [b, p]
    return _done(r, parts)


def build_rug():
    r, kw = _root("set_rug")
    rg = L["rug"]
    m = M.fabric("mat_fp_rug", "#6f7484")
    rug = geo.box("rug_footprint", rg["x"] - rg["w"] / 2, rg["x"] + rg["w"] / 2, rg["y"] - rg["d"] / 2,
                  rg["y"] + rg["d"] / 2, 0.0, rg["h"], material=m, **kw)
    geo.bevel(rug, 0.004, segments=2)
    return _done(r, [rug])


def build_bed():
    r, kw = _root("set_bed")
    bd = L["bed"]
    wood = _mat("mat_fp_bed_frame", "#4b3426", rough=0.5)
    sheet = M.fabric("mat_fp_bed_duvet", "#c9cdd8")
    pillow = M.fabric("mat_fp_bed_pillow", "#e4e4ea")
    bx0, bx1 = bd["x"] - bd["w"] / 2, bd["x"] + bd["w"] / 2
    by0, by1 = bd["y"] - bd["d"] / 2, bd["y"] + bd["d"] / 2
    frame = geo.boxes("bed_footprint_frame", [(bx0, bx1, by0, by1 - 0.05, 0.08, 0.32),
                                              (bx0, bx1, by1 - 0.05, by1, 0.0, bd["head_h"])]
                      + [(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.08)
                         for x in (bx0 + 0.05, bx1 - 0.05) for y in (by0 + 0.05, by1 - 0.1)], material=wood, **kw)
    geo.bevel(frame, 0.006, segments=3)
    mat = geo.box("bed_footprint_mattress", bx0 + 0.02, bx1 - 0.02, by0 + 0.02, by1 - 0.07, 0.32, bd["h"],
                  material=sheet, **kw)
    geo.bevel(mat, 0.05, segments=4)
    pil = [geo.box(f"bed_footprint_pillow_{k + 1:02d}", bx0 + 0.08 + k * 0.66, bx0 + 0.66 + k * 0.66, by1 - 0.45,
                   by1 - 0.12, bd["h"], bd["h"] + 0.12, material=pillow, **kw) for k in range(2)]
    for p in pil:
        geo.bevel(p, 0.05, segments=4)
    return _done(r, [frame, mat] + pil)


def build_panels():
    r, kw = _root("set_panels")
    pg, pdk = L["panels_guitar"], L["panels_desk"]
    g = M.fabric("mat_fp_panel_guitar", "#34353b")
    d = M.fabric("mat_fp_panel_desk", "#5b6170")
    a = geo.box("panels_footprint_guitar", RX - pg["t"], RX, pg["y0"], pg["y1"], pg["z0"], pg["z1"], material=g, **kw)
    bs = [geo.box(f"panels_footprint_desk_{i + 1:02d}", x - pdk["w"] / 2, x + pdk["w"] / 2, RY - pdk["t"], RY,
                  pdk["z0"], pdk["z1"], material=d, **kw) for i, x in enumerate(pdk["x"])]
    for o in [a] + bs:
        geo.bevel(o, 0.008, segments=3)
    return _done(r, [a] + bs)


def _guitar(name, length, width, depth, colour, kw, archtop=False):
    """A guitar silhouette (the sheet's outline), extruded: built standing in local X-Z,
    face toward -Y, bottom at z = 0, centred on x = 0."""
    body, neck, head = PLAN.guitar_outline(length, width, archtop=archtop)
    bm_ = _mat(f"mat_fp_{name}", colour, rough=0.3, coat=0.8, coat_rough=0.08)
    wood = bpy.data.materials.get("mat_fp_guitar_neck") or _mat("mat_fp_guitar_neck", "#5b3a22", rough=0.45)
    b = geo.prism(name + "_body", body, "Y", -depth / 2, depth / 2, material=bm_, **kw)
    n = geo.prism(name + "_neck", neck, "Y", -0.012, 0.012, material=wood, **kw)
    h = geo.prism(name + "_head", head, "Y", -0.009, 0.009, material=wood, **kw)
    geo.bevel(b, 0.006, segments=3, angle=60)
    return geo.join([b, n, h], name)


def build_guitars():
    r, kw = _root("obj_guitars")
    metal = _mat("mat_fp_rack", "#232326", metal=0.5, rough=0.45)
    chrome = M.chrome("mat_fp_hook")
    parts = []
    # wall: three on hooks, faces into the room (-X), timeline back to front
    gx = RX - WG["off_wall"]
    cols = ["#b5651d", "#f1efe8", "#8a4b1f"]
    hooks = []
    for i, y in enumerate(WG["y"]):
        g = _guitar(f"guitars_footprint_{i + 1:02d}", WG["length"][i], WG["width"][i], 0.08 if i == 0 else 0.045,
                    cols[i], kw, archtop=(i == 0))
        g.rotation_euler = (0, 0, math.radians(-90))      # face -X
        g.location = (gx, y, WG["bottom"])
        parts.append(g)
        hz = WG["bottom"] + WG["length"][i] - WG["hook_from_top"]
        hooks.append((0.006, (RX, y, hz), (gx + 0.01, y, hz + 0.02)))
    parts.append(geo.cylinders("guitars_footprint_hooks", hooks, segments=10, material=chrome, **kw))
    # floor rack (option A), from the sheet's rack geometry
    rk, gs, slots = PLAN.rack_slots()
    lean = math.radians(rk["lean"])
    bar_x = -0.08 + 0.70 * math.sin(lean)
    bar_z = rk["cradle"] + 0.70 * math.cos(lean)
    specs = [(-rk["w"] / 2, rk["w"] / 2 - 0.20, -rk["d"] / 2, rk["d"] / 2, rk["cradle"] - 0.03, rk["cradle"]),
             (bar_x, bar_x + 0.03, -rk["d"] / 2, rk["d"] / 2, bar_z - 0.03, bar_z)]
    for s in (-1, 1):
        specs.append((-0.12, bar_x + 0.03, s * rk["d"] / 2 - 0.012, s * rk["d"] / 2 + 0.012, 0, 0.03))
        specs.append((bar_x, bar_x + 0.025, s * rk["d"] / 2 - 0.012, s * rk["d"] / 2 + 0.012, 0, bar_z))
    rack = geo.boxes("guitars_footprint_rack", specs, material=metal, **kw)
    geo.bevel(rack, 0.004, segments=2)
    geo.place(rack, (rk["x"], rk["y"], 0), rk["yaw"])
    parts.append(rack)
    rcols = ["#c0762a", "#ece8dc", "#a98aa9"]
    for i, (g, sl) in enumerate(zip(gs, slots)):
        o = _guitar(f"guitars_footprint_{i + 4:02d}", g["length"], g["width"], 0.05, rcols[i], kw)
        # in the rack's X-Z plane at its slot (face along the rack's length), bottom on the
        # cradle, leaning toward +X about the rack's Y, then the rack's yaw (as the sheet draws it)
        from mathutils import Matrix
        m = (Matrix.Translation((rk["x"], rk["y"], 0)) @ Matrix.Rotation(math.radians(rk["yaw"]), 4, "Z")
             @ Matrix.Translation((-0.08, sl, rk["cradle"])) @ Matrix.Rotation(lean, 4, "Y"))
        o.matrix_world = m
        parts.append(o)
    return _done(r, parts)


def build_plant():
    r, kw = _root("obj_plant")
    pl = L["plant"]
    pot_m = _mat("mat_fp_pot", "#b4553a", rough=0.7)
    leaf_m = _mat("mat_fp_leaf", "#4f7a46", rough=0.5, sss=0.15)
    z0 = WIN["sill"]
    import bmesh
    pot = geo.cylinder("plant_footprint_pot", pl["pot_d"] / 2, (pl["x"], pl["y"], z0), (pl["x"], pl["y"], z0 + 0.13),
                       segments=24, material=pot_m, **kw)
    geo.bevel(pot, 0.004, segments=2)
    bm = bmesh.new()
    for dx, dz, rr in ((0.0, 0.25, 0.09), (-0.07, 0.20, 0.06), (0.07, 0.22, 0.065)):
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rr)
        bmesh.ops.translate(bm, vec=(pl["x"] + dx, pl["y"] - 0.01, z0 + dz), verts=res["verts"])
    leaves = geo.from_bmesh("plant_footprint_leaves", bm, material=leaf_m, **kw)
    return _done(r, [pot, leaves])


BUILDERS = [build_window, build_light, build_chair, build_studio, build_mic, build_bookshelf, build_frames,
            build_rug, build_bed, build_panels, build_guitars, build_plant]


def build_steps():
    ROOTS.clear()
    for fn in BUILDERS:
        fn()
        yield fn.__name__
