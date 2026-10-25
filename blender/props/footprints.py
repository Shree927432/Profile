"""Footprints: every root on room plan v2 that is not modelled yet, as simple named stand-ins
at their real size and place, so the room can be judged whole. Each later step replaces one
root's footprint with the real prop.

Positions, sizes and colours come from blender/lib/plan_v2.py (COMPONENTS, WINDOW_V2,
LIGHT_V2, RACK_V2, WALL_GUITARS_V2, PANEL_GUITAR_V2, MIC, LEDGE) and SWITCH; the guitar
outline and the rack slots from blender/design/room_plan_sheet.py, as the sheet draws them.
The real roots are used (obj_studio, set_chair, ...); their parts are named
`<word>_footprint_*`, never a name from MESHES.md, and the export joins each root's footprint
into `<word>_static`. No logos or words: the neon sign's strokes stand in for the owner's
words, which will come from content/.
"""
import math
import os
import sys

import bmesh
from mathutils import Matrix, Vector

from lib import constants as C, geo, materials as M, plan_v2 as P

sys.path.insert(0, os.path.join(C.BLENDER_DIR, "design"))
import room_plan_sheet as PLAN  # noqa: E402  (guitar_outline, rack_slots)

WG, WIN, H = P.WALL_GUITARS_V2, P.WINDOW_V2, P.H
MODELLED = {"guitar_02", "guitar_04"}   # built by their own prop scripts (props/guitar_02.py, guitar_04.py)
RX, RY, TOP = P.RX, P.RY, P.TOP
COMP = {c["key"]: c for c in P.COMPONENTS}
ROOTS = []                      # (root name, [part objects]) in build order


def _mat(name, colour, **v):
    return M.principled(name, base=colour, **v)


def _root(name):
    r, coll = geo.root(name)
    return r, dict(collection=coll, parent=r)


def _done(root, parts):
    ROOTS.append((root.name, parts))
    return root


def _at(c, local=(0, 0, 0)):
    """World point of a component's local point (its own frame: front at -Y, bottom centre at 0)."""
    m = Matrix.Translation(c["at"]) @ Matrix.Rotation(math.radians(c["yaw"]), 4, "Z")
    return tuple(m @ Vector(local))


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
    lt, sw = P.LIGHT_V2, P.SWITCH
    white = _mat("mat_fp_light_shade", "#ecebe6", rough=0.5, sss=0.2)
    cord_m = _mat("mat_fp_light_cord", "#2a2a2a", rough=0.6)
    plate_m = _mat("mat_fp_switch", "#eeeeea", rough=0.35)
    zb = H - lt["drop"] - lt["shade_h"]
    canopy = geo.cylinder("light_footprint_canopy", lt["canopy_d"] / 2, (lt["x"], lt["y"], H - 0.03),
                          (lt["x"], lt["y"], H), segments=32, material=white, **kw)
    cord = geo.cylinder("light_footprint_cord", 0.003, (lt["x"], lt["y"], zb + lt["shade_h"]), (lt["x"], lt["y"], H),
                        segments=8, material=cord_m, **kw)
    # dome shade: a lathe of a quarter ellipse, open below
    bm = bmesh.new()
    prof = [(lt["shade_d"] / 2 * math.cos(a), lt["shade_h"] * math.sin(a))
            for a in [math.pi / 2 * i / 6 for i in range(7)]]
    rings = []
    for k in range(28):
        a = 2 * math.pi * k / 28
        rings.append([bm.verts.new((lt["x"] + max(rr, 0.004) * math.cos(a), lt["y"] + max(rr, 0.004) * math.sin(a),
                                    zb + zz)) for rr, zz in prof])
    for k in range(28):
        a, b = rings[k], rings[(k + 1) % 28]
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


def build_studio():
    """A7V speakers on ISO stands, the audio interface, the DJ decks on the return, the lightstick in its
    cradle on a small shelf on the pegboard."""
    r, kw = _root("obj_studio")
    white = _mat("mat_fp_speaker", "#f2f2ef", rough=0.35)
    cone = _mat("mat_fp_woofer", "#1b1b1d", rough=0.5)
    stand_m = _mat("mat_fp_iso", "#2a2a2c", rough=0.6)
    dj_m = _mat("mat_fp_dj", "#1b1b1d", rough=0.5)
    jog_m = _mat("mat_fp_jog", "#4a4c52", metal=0.6, rough=0.3)
    silver = _mat("mat_fp_interface", "#b9bcc0", metal=0.7, rough=0.35)
    stick_w = _mat("mat_fp_stick_handle", "#f2f2f2", rough=0.3)
    stick_h = _mat("mat_fp_stick_head", "#e9e3f5", rough=0.2, emit="#d9a0ff", emit_strength=2.0)
    parts = []
    for i in (1, 2):
        n = f"{i:02d}"
        iso, spk = COMP[f"iso_{i}"], COMP[f"a7v_{i}"]
        parts.append(geo.rounded_box(f"studio_footprint_stand_{n}", *iso["size"], 0.01, at=iso["at"], yaw=iso["yaw"],
                                     material=stand_m, **kw))
        w, d, h = spk["size"]
        cab = geo.rounded_box(f"studio_footprint_speaker_{n}", w, d, h, 0.012, at=spk["at"], yaw=spk["yaw"],
                              material=white, **kw)
        geo.bevel(cab, 0.008, segments=3)
        faces = [(0.075, _at(spk, (0, -d / 2 + 0.002, 0.11)), _at(spk, (0, -d / 2 - 0.004, 0.11))),
                 (0.03, _at(spk, (0, -d / 2 + 0.002, 0.265)), _at(spk, (0, -d / 2 - 0.004, 0.265)))]
        parts += [cab, geo.cylinders(f"studio_footprint_drivers_{n}", faces, segments=28, material=cone, **kw)]
    it = COMP["interface"]
    w, d, h = it["size"]
    parts.append(geo.rounded_box("studio_footprint_interface", w, d, h, 0.008, at=it["at"], yaw=it["yaw"],
                                 material=silver, **kw))
    parts.append(geo.cylinder("studio_footprint_interface_knob", 0.024, _at(it, (0.05, 0, h)), _at(it, (0.05, 0, h + 0.022)),
                              segments=24, material=silver, **kw))
    dj = COMP["dj"]
    w, d, h = dj["size"]
    body = geo.rounded_box("studio_footprint_dj", w, d, h, 0.012, at=dj["at"], yaw=dj["yaw"], material=dj_m, **kw)
    geo.bevel(body, 0.005, segments=2)
    jogs = geo.cylinders("studio_footprint_jogs", [(0.07, _at(dj, (sx * 0.15, 0.01, h)), _at(dj, (sx * 0.15, 0.01, h + 0.01)))
                                                   for sx in (-1, 1)], segments=40, material=jog_m, **kw)
    ls = COMP["lightstick"]
    x, y, z = ls["at"]
    cradle = geo.cylinder("studio_footprint_stick_cradle", 0.035, (x, y, z), (x, y, z + 0.025), segments=20,
                          material=stick_w, **kw)
    handle = geo.cylinder("studio_footprint_stick_handle", 0.015, (x, y, z + 0.025), (x, y, z + 0.17), segments=16,
                          material=stick_w, **kw)
    head = geo.cylinder("studio_footprint_stick_head", 0.04, (x, y, z + 0.17), (x, y, z + ls["size"][2]), segments=8,
                        material=stick_h, **kw)
    geo.bevel(head, 0.012, segments=3)
    sh = P.LIGHTSTICK_SHELF                         # a small shelf hooked into the pegboard
    shelf = geo.box("studio_footprint_stick_shelf", -RX + 0.035, -RX + 0.035 + sh["d"], y - sh["w"] / 2, y + sh["w"] / 2,
                    z - sh["t"], z, material=stick_w, **kw)
    parts += [body, jogs, shelf, cradle, handle, head]
    return _done(r, parts)


def build_mic():
    """Shure MV7+ style capsule, white, on a white broadcast arm clamped at the back edge."""
    r, kw = _root("obj_mic")
    m = _mat("mat_fp_mic", "#f2f2ef", rough=0.35)
    mc = P.MIC
    cx, cy = mc["clamp"]
    cap = Vector(mc["capsule"])
    elbow = Vector(mc["elbow"])
    riser = Vector((cx, cy, TOP + 0.20))
    hang = cap + Vector((0.03, 0.10, 0.12))
    arm = geo.cylinders("mic_footprint_arm", [(0.012, (cx, cy, TOP), riser[:]), (0.009, riser[:], elbow[:]),
                                              (0.009, elbow[:], hang[:]), (0.006, hang[:], cap[:])],
                        segments=10, material=m, **kw)
    to_ear = (Vector(P.EAR) - cap).normalized()
    body = geo.cylinder("mic_footprint_capsule", 0.033, (cap - to_ear * 0.08)[:], (cap + to_ear * 0.073)[:],
                        segments=20, material=m, **kw)
    geo.bevel(body, 0.012, segments=3)
    return _done(r, [arm, body])


def build_frames():
    """Three black frames standing on the ledge above the screens."""
    r, kw = _root("obj_frames")
    border = _mat("mat_fp_frame", "#26262a", rough=0.4)
    pics = [_mat(f"mat_fp_picture_{i + 1:02d}", c, rough=0.6) for i, c in enumerate(("#c9d6e8", "#e8dcc9", "#d4e2d0"))]
    parts = []
    for i in range(3):
        c = COMP[f"frame_{i + 1}"]
        w, d, h = c["size"]
        n = f"{i + 1:02d}"
        b = geo.rounded_box(f"frames_footprint_{n}", w, d, h, 0.003, at=c["at"], yaw=c["yaw"], material=border, **kw)
        p = geo.box(f"frames_footprint_picture_{n}", -w / 2 + 0.04, w / 2 - 0.04, -d / 2 - 0.002, -d / 2, 0.04, h - 0.04,
                    material=pics[i], **kw)
        geo.place(p, c["at"], c["yaw"])
        parts += [b, p]
    return _done(r, parts)


def build_chair():
    """Aeron-style stand-in in Mineral: five-star base, gas lift, seat, mesh back, arms."""
    r, kw = _root("set_chair")
    ch = COMP["chair"]
    frame = _mat("mat_fp_chair_frame", "#9da1a7", metal=0.5, rough=0.45)
    mesh = M.fabric("mat_fp_chair_mesh", ch["col"])
    x, y, _ = ch["at"]
    legs = [(0.025, (0, 0, 0.06), (0, 0, 0.42))]
    legs += [(0.018, (0, 0, 0.07), (0.33 * math.cos(2 * math.pi * k / 5), 0.33 * math.sin(2 * math.pi * k / 5), 0.04))
             for k in range(5)]
    base = geo.cylinders("chair_footprint_base", legs, segments=10, material=frame, **kw)
    seat = geo.rounded_box("chair_footprint_seat", 0.50, 0.46, 0.06, 0.08, at=(0, -0.01, 0.42), material=mesh, **kw)
    back = geo.rounded_box("chair_footprint_back", 0.46, 0.05, 0.50, 0.08, material=mesh, **kw)
    back.data.transform(Matrix.Translation((0, 0.245, 0.56)) @ Matrix.Rotation(-0.18, 4, "X"))
    back.location = (0, 0, 0)
    arms = geo.boxes("chair_footprint_arms", [(s * 0.30 - 0.03, s * 0.30 + 0.03, -0.15, 0.15, 0.62, 0.65) for s in (-1, 1)]
                     + [(s * 0.30 - 0.012, s * 0.30 + 0.012, 0.0, 0.03, 0.45, 0.62) for s in (-1, 1)],
                     material=frame, **kw)
    for o in (seat, back, arms):
        geo.bevel(o, 0.01, segments=2)
    o = geo.join([base, seat, back, arms], "chair_footprint")
    geo.place(o, (x, y, 0), ch["yaw"])
    return _done(r, [o])


def build_rug():
    r, kw = _root("set_rug")
    c = COMP["rug"]
    w, d, h = c["size"]
    rug = geo.rounded_box("rug_footprint", w, d, h, 0.01, at=c["at"], yaw=c["yaw"], material=M.fabric("mat_fp_rug", c["col"]),
                          **kw)
    return _done(r, [rug])


def build_panels():
    r, kw = _root("set_panels")
    pg = P.PANEL_GUITAR_V2
    a = geo.box("panels_footprint_guitar", RX - pg["t"], RX, pg["y0"], pg["y1"], pg["z0"], pg["z1"],
                material=M.fabric("mat_fp_panel_guitar", "#34363c"), **kw)
    geo.bevel(a, 0.008, segments=3)
    return _done(r, [a])


def build_walls():
    """The AI side's walls: the backlit pegboard with the headphones, the neon sign (strokes, not
    words), the light panels, the floating ledge under the frames."""
    r, kw = _root("set_walls")
    white = _mat("mat_fp_walls_white", "#f2f2ef", rough=0.35)
    glow = _mat("mat_fp_walls_backlight", "#9fc8ff", emit="#9fc8ff", emit_strength=4.0)
    neon_m = _mat("mat_fp_walls_neon", "#ffffff", emit="#f4f8ff", emit_strength=8.0)
    cup = _mat("mat_fp_walls_headphones", "#e9e9e6", rough=0.4)
    parts = []
    pb = COMP["pegboard"]
    w, d, h = pb["size"]
    board = geo.box("walls_footprint_pegboard", -w / 2, w / 2, -0.035, -0.035 + d, 0.0, h, material=white, **kw)
    light = geo.box("walls_footprint_backlight", -w / 2 + 0.02, w / 2 - 0.02, -0.010, -0.006, 0.02, h - 0.02,
                    material=glow, **kw)
    for o in (board, light):
        geo.place(o, (-RX, pb["at"][1], pb["at"][2]), pb["yaw"])
    hp = COMP["headphones"]
    hx, hy, hz = hp["at"]
    cups = [(0.045, (hx, hy + s * 0.06, hz + 0.05), (hx, hy + s * 0.095, hz + 0.05)) for s in (-1, 1)]
    band = [(0.011, (hx, hy + 0.075 * math.cos(a0), hz + 0.10 + 0.10 * math.sin(a0)),
             (hx, hy + 0.075 * math.cos(a1), hz + 0.10 + 0.10 * math.sin(a1)))
            for a0, a1 in [(math.pi * k / 6, math.pi * (k + 1) / 6) for k in range(6)]]
    phones = geo.cylinders("walls_footprint_headphones", cups + band, segments=16, material=cup, **kw)
    ne = COMP["neon"]
    strokes = [(-0.30, -0.04, 0.19), (0.02, 0.30, 0.19), (-0.22, 0.22, 0.07)]
    neon = geo.boxes("walls_footprint_neon", [(u0, u1, -0.02, -0.008, v - 0.007, v + 0.007) for u0, u1, v in strokes],
                     material=neon_m, **kw)
    geo.place(neon, (-RX, ne["at"][1], ne["at"][2]), ne["yaw"])
    parts += [board, light, phones, neon]
    # light panels: seven triangles, three colours, our own arrangement
    nl = COMP["nanoleaf"]
    tri_m = [_mat(f"mat_fp_walls_panel_{k + 1}", "#dfe6ff", emit=e, emit_strength=2.5)
             for k, e in enumerate(("#7a8cff", "#9fd8ff", "#c79bff"))]
    s3 = 0.23
    hh = s3 * math.sqrt(3) / 2
    cells = [(0, 0, 1), (1, 0, -1), (2, 0, 1), (1, 1, 1), (2, 1, -1), (3, 1, 1), (3, 0, -1)]
    tris = []
    for k, (i, j, up) in enumerate(cells):
        u, v = -nl["size"][0] / 2 + i * s3 / 2, j * hh
        pts = [(u, v), (u + s3, v), (u + s3 / 2, v + hh)] if up > 0 else [(u, v + hh), (u + s3 / 2, v), (u + s3, v + hh)]
        c = (u + s3 / 2, v + hh / 2)
        pts = [(a * 0.94 + c[0] * 0.06, b * 0.94 + c[1] * 0.06) for a, b in pts]
        t = geo.prism(f"walls_footprint_panel_{k}", pts, "Y", -0.012, 0.0, material=tri_m[k % 3], **kw)
        geo.place(t, (-RX, nl["at"][1], nl["at"][2]), nl["yaw"])
        tris.append(t)
    parts.append(geo.join(tris, "walls_footprint_panels"))
    lg = COMP["ledge"]
    w, d, h = lg["size"]
    ledge = geo.box("walls_footprint_ledge", -w / 2, w / 2, -d / 2, d / 2, 0.0, h, material=white, **kw)
    geo.place(ledge, lg["at"], lg["yaw"])
    geo.bevel(ledge, 0.004, segments=2)
    parts.append(ledge)
    return _done(r, parts)


def _guitar(name, length, width, depth, colour, kw, archtop=False, double=False):
    """A guitar silhouette (the sheet's outline), extruded: built standing in local X-Z,
    face toward -Y, bottom at z = 0, centred on x = 0. double: two necks and heads."""
    body, neck, head = PLAN.guitar_outline(length * (0.92 if double else 1.0), width, archtop=archtop)
    bm_ = _mat(f"mat_fp_{name}", colour, rough=0.3, coat=0.8, coat_rough=0.08)
    wood = _mat("mat_fp_guitar_neck", "#3a2414", rough=0.45)
    out = [geo.prism(name + "_body", body, "Y", -depth / 2, depth / 2, material=bm_, **kw)]
    geo.bevel(out[0], 0.006, segments=3, angle=60)
    for k, du in enumerate((-0.085, 0.085) if double else (0.0,)):
        out.append(geo.prism(f"{name}_neck_{k}", [(u + du, v) for u, v in neck], "Y", -0.012, 0.012, material=wood, **kw))
        out.append(geo.prism(f"{name}_head_{k}", [(u + du, v) for u, v in head], "Y", -0.009, 0.009,
                             material=bm_ if double else wood, **kw))
    return geo.join(out, name)


def build_guitars():
    r, kw = _root("obj_guitars")
    metal = _mat("mat_fp_rack", "#232326", metal=0.5, rough=0.45)
    chrome = M.chrome("mat_fp_hook")
    parts = []
    # wall: on hooks, faces into the room (-X), timeline back to front
    gx = RX - WG["off_wall"]
    hooks = []
    for i, y in enumerate(WG["y"]):
        if f"guitar_{i + 1:02d}" in MODELLED:
            continue
        c = COMP[f"guitar_{i + 1:02d}"]
        g = _guitar(f"guitars_footprint_{i + 1:02d}", WG["length"][i], WG["width"][i], 0.045, c["col"], kw,
                    archtop=(i == 0), double=(i == 2))
        g.rotation_euler = (0, 0, math.radians(-90))      # face -X
        g.location = (gx, y, WG["bottom"])
        parts.append(g)
        hz = WG["bottom"] + WG["length"][i] - WG["hook_from_top"][i]
        for k in range(WG["hooks"][i]):
            dy = 0.0 if WG["hooks"][i] == 1 else (-0.085, 0.085)[k]
            hooks.append((0.006, (RX, y - dy, hz), (gx + 0.01, y - dy, hz + 0.02)))
    parts.append(geo.cylinders("guitars_footprint_hooks", hooks, segments=10, material=chrome, **kw))
    # floor rack (the approved shape), at its v2 place
    rk, gs, slots = PLAN.rack_slots(P.RACK_V2)
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
    rcols = {"guitar_05": "#ece6d2", "guitar_06": "#a98aa9"}
    for i, (g, sl) in enumerate(zip(gs, slots)):
        if g["name"] in MODELLED:
            continue
        o = _guitar(f"guitars_footprint_{i + 4:02d}", g["length"], g["width"], 0.045, rcols[g["name"]], kw)
        # in the rack's X-Z plane at its slot (face along the rack's length), bottom on the
        # cradle, leaning toward +X about the rack's Y, then the rack's yaw (as the sheet draws it)
        o.matrix_world = (Matrix.Translation((rk["x"], rk["y"], 0)) @ Matrix.Rotation(math.radians(rk["yaw"]), 4, "Z")
                          @ Matrix.Translation((-0.08, sl, rk["cradle"])) @ Matrix.Rotation(lean, 4, "Y"))
        parts.append(o)
    return _done(r, parts)


def build_plant():
    """Young monstera in a terracotta pot on the centred sill."""
    r, kw = _root("obj_plant")
    c = COMP["plant"]
    pot_m = _mat("mat_fp_pot", "#b4553a", rough=0.7)
    leaf_m = _mat("mat_fp_leaf", c["col"], rough=0.5, sss=0.15)
    x, y, z0 = c["at"]
    pot = geo.cylinder("plant_footprint_pot", c["size"][0] / 2, (x, y, z0), (x, y, z0 + 0.13), segments=24,
                       material=pot_m, **kw)
    geo.bevel(pot, 0.004, segments=2)
    bm = bmesh.new()
    for dx, dz, rr in ((0.0, 0.25, 0.09), (-0.07, 0.20, 0.06), (0.07, 0.22, 0.065)):
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rr)
        bmesh.ops.scale(bm, vec=(1.0, 0.45, 0.8), verts=res["verts"])
        bmesh.ops.translate(bm, vec=(x + dx, y - 0.01, z0 + dz), verts=res["verts"])
    leaves = geo.from_bmesh("plant_footprint_leaves", bm, material=leaf_m, **kw)
    return _done(r, [pot, leaves])


BUILDERS = [build_window, build_light, build_studio, build_mic, build_frames, build_chair, build_rug,
            build_panels, build_walls, build_guitars, build_plant]


def build_steps():
    ROOTS.clear()
    for fn in BUILDERS:
        fn()
        yield fn.__name__
