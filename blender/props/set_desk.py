"""set_desk: the AI-lab desk and the set dressing on it.

Numbers from blender/lib/plan_v2.py (DESK_V2, ALEX, COMPONENTS). Built in world coordinates
under the `set_desk` root. Names (MESHES.md section 4): desk_top, desk_drawers_01 ... 03,
desk_led, desk_pole, desk_keyboard, desk_mouse, desk_mat, desk_screenbar,
desk_keylight_01 ... 02, desk_camera, desk_streamdeck, desk_laptop_stand, desk_laptop,
desk_plant. The export joins them into desk_static.

The desk (option A, 2026-10-23) at shell quality: one continuous white L top, 3.5 cm thick,
its surface at 73.5 cm, the room-facing edges rounded (edge_r), the inner corner rounded in
plan (inner_r), on three ALEX-style drawer units (36 x 58 x 70, five drawers with recessed
curved pulls; IKEA's own 3D file was the reference for the shape, nothing copied from it),
and an LED strip under the front edges. Everything on the top is a stand-in: the right size,
place, colour and finish, no detail. No logos or names anywhere.
"""
import math

import bmesh
from mathutils import Matrix

from lib import geo, materials as M, plan_v2 as P

D = P.DESK_V2
TOP, T = D["top"], D["t"]
RX, RY = P.RX, P.RY
COMP = {c["key"]: c for c in P.COMPONENTS}


def _mats():
    return dict(
        white=M.principled("mat_desk_white", base=D["colour"], rough=0.32, coat=0.25, coat_rough=0.2),
        notch=M.principled("mat_desk_notch", base="#3b3c3e", rough=0.6),
        black=M.principled("mat_desk_black", base="#1b1b1d", rough=0.45),
        alu=M.principled("mat_desk_alu", base="#c9ccd1", metal=1.0, rough=0.3),
        grey=M.principled("mat_desk_grey", base="#d5d6d8", rough=0.4),
        felt=M.fabric("mat_desk_felt", "#8d9096"),
        leaf=M.principled("mat_desk_leaf", base="#3f6b3a", rough=0.45, sss=0.1),
        led=M.principled("mat_desk_led", base="#7fb6ff", emit="#7fb6ff", emit_strength=6.0),
        panel=M.principled("mat_desk_light_panel", base="#f4f4f2", emit="#fff6ea", emit_strength=1.5),
        glass=M.principled("mat_desk_screen", base="#0d0f14", rough=0.15, emit="#cfe0ff", emit_strength=0.4),
    )


def top_outline(n=8):
    """The L top in plan (x, y), counter-clockwise: return end, the rounded inner corner, the
    back run's front edge, the window end, along the back wall, down the left wall."""
    b, r = D["back"], D["ret"]
    ir = D["inner_r"]
    cx, cy = r["x1"] + ir, b["y0"] - ir                      # centre of the inner corner's arc
    arc = [(cx + ir * math.cos(a), cy + ir * math.sin(a))
           for a in [math.pi - (math.pi / 2) * i / n for i in range(n + 1)]]
    return ([(r["x0"], r["y0"]), (r["x1"], r["y0"])] + arc
            + [(b["x1"], b["y0"]), (b["x1"], b["y1"]), (b["x0"], b["y1"])])


def build_top(mat, kw):
    """One slab, the room-facing edges rounded by a weighted bevel; edges against a wall stay square."""
    o = geo.prism("desk_top", top_outline(), "Z", TOP - T, TOP, **kw)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    wl = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
    on_wall = lambda v: abs(v.co.x + RX) < 1e-4 or abs(v.co.y - RY) < 1e-4    # noqa: E731
    for e in bm.edges:
        a, b = e.verts
        wall = (on_wall(a) and on_wall(b)) and (abs(a.co.x - b.co.x) < 1e-4 or abs(a.co.y - b.co.y) < 1e-4)
        sharp = e.is_manifold and e.calc_face_angle(0.0) > math.radians(30)
        e[wl] = 1.0 if sharp and not wall else 0.0
    bm.to_mesh(o.data)
    bm.free()
    m = o.modifiers.new("bevel", "BEVEL")
    m.width, m.segments, m.limit_method = D["edge_r"], 3, "WEIGHT"
    m.use_clamp_overlap, m.harden_normals = True, True
    return o


def build_drawers(i, x, y, yaw, mats, kw):
    """An ALEX-style unit in its own frame (front at -Y), five drawer fronts with a curved finger
    notch at the top of each, placed and turned."""
    w, d, h = P.ALEX
    ft = 0.018                                                   # drawer front thickness
    car = geo.box(f"desk_drawers_{i:02d}_carcass", -w / 2, w / 2, -d / 2 + ft, d / 2, 0.0, h,
                  material=mats["white"], **kw)
    fronts, notches = [], []
    z0, z1, gap = 0.02, h - 0.006, 0.003
    pitch = (z1 - z0) / 5
    for k in range(5):
        a, b = z0 + k * pitch + gap / 2, z0 + (k + 1) * pitch - gap / 2
        fronts.append((-w / 2 + 0.0015, w / 2 - 0.0015, -d / 2, -d / 2 + ft, a, b))
        # the pull: a shallow crescent cut into the top edge, 11 cm across, 1.4 cm deep at the middle
        top, half, deep = b - 0.006, 0.055, 0.014
        pts = [(half * math.cos(t), top - 0.003 * math.sin(t)) for t in [math.pi * j / 6 for j in range(7)]]
        pts += [(half * math.cos(t), top - deep * math.sin(t)) for t in [math.pi - math.pi * j / 6 for j in range(7)]][1:-1]
        notches.append(geo.prism(f"desk_drawers_{i:02d}_pull_{k}", pts, "Y", -d / 2 - 0.0006, -d / 2 + 0.008,
                                 material=mats["notch"], smooth=False, **kw))
    fr = geo.boxes(f"desk_drawers_{i:02d}_fronts", fronts, material=mats["white"], **kw)
    geo.bevel(fr, 0.0015, segments=2)
    geo.bevel(car, 0.002, segments=2)
    o = geo.join([car, fr] + notches, f"desk_drawers_{i:02d}")
    return geo.place(o, (x, y, 0.0), yaw)


def build_led(mat, kw):
    """The strip under the top, led_in in from the room-facing edges (back run, then return)."""
    b, r, i = D["back"], D["ret"], D["led_in"]
    z0, z1 = TOP - T - 0.004, TOP - T
    return geo.boxes("desk_led", [(r["x1"] + i, b["x1"] - i, b["y0"] + i - 0.005, b["y0"] + i + 0.005, z0, z1),
                                  (r["x1"] - i - 0.005, r["x1"] - i + 0.005, r["y0"] + i, b["y0"] + i, z0, z1)],
                     material=mat, **kw)


def standin(name, key, mat, kw, r=0.008, h=None):
    """A rounded box at a component's place and size from plan_v2."""
    c = COMP[key]
    w, d, hh = c["size"]
    return geo.rounded_box(name, w, d, h or hh, r, at=c["at"], yaw=c["yaw"], material=mat, **kw)


def build_mouse(mat, kw):
    c = COMP["mouse"]
    w, d, h = c["size"]
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.5)
    for v in bm.verts:
        v.co.x *= w
        v.co.y *= d
        v.co.z = max(0.0, v.co.z) * 2 * h
        v.co.y += 0.012 * (v.co.z / h)                       # the hump toward the back
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return geo.place(geo.from_bmesh("desk_mouse", bm, material=mat, **kw), c["at"], c["yaw"])


def build_keylight(i, mats, kw):
    """Pole clamped at the back edge, the panel 5 cm in front of it, turned to the chair."""
    pole, panel = COMP[f"keylight_pole_{i}"], COMP[f"keylight_{i}"]
    x, y, z = pole["at"]
    pw, _, ph = pole["size"]
    parts = [geo.cylinder(f"desk_keylight_{i:02d}_pole", pw / 2, (x, y, z), (x, y, z + ph), segments=12,
                          material=mats["white"], **kw)]
    w, d, h = panel["size"]
    body = geo.rounded_box(f"desk_keylight_{i:02d}_panel", w, d, h, 0.012, at=panel["at"], yaw=panel["yaw"],
                           material=mats["white"], **kw)
    face = geo.box(f"desk_keylight_{i:02d}_face", -w / 2 + 0.012, w / 2 - 0.012, -d / 2 - 0.001, -d / 2 + 0.001,
                   0.012, h - 0.012, material=mats["panel"], **kw)
    geo.place(face, panel["at"], panel["yaw"])
    px, py, pz = panel["at"]
    parts += [body, face, geo.cylinder(f"desk_keylight_{i:02d}_mount", 0.008, (x, y, pz + h / 2), (px, py, pz + h / 2),
                                       segments=8, material=mats["black"], **kw)]
    return geo.join(parts, f"desk_keylight_{i:02d}")


def build_camera(mats, kw):
    """Camera body with its zoom lens, on a flex arm clamped at the back corner."""
    c = COMP["camera"]
    w, d, h = c["size"]
    body = geo.rounded_box("desk_camera_body", w, d * 0.45, h, 0.006, material=mats["black"], **kw)
    lens = geo.cylinder("desk_camera_lens", 0.031, (0.012, -d * 0.225, h * 0.45), (0.012, -d * 0.225 - 0.05, h * 0.45),
                        segments=20, material=mats["black"], **kw)
    o = geo.join([body, lens], "desk_camera")
    geo.place(o, c["at"], c["yaw"])
    cx, cy, cz = c["at"]
    clamp = (-RX + 0.10, RY - 0.08)
    pts = [(*clamp, TOP), (*clamp, 1.10), (cx - 0.10, cy + 0.12, cz + 0.12), (cx, cy + 0.02, cz)]
    arm = geo.cylinders("desk_camera_arm", [(0.007, a, b) for a, b in zip(pts, pts[1:])], segments=8,
                        material=mats["black"], **kw)
    return geo.join([o, arm], "desk_camera")


def build_laptop(mats, kw):
    """The stand (an open aluminium wedge) and the laptop open on it, facing the DJ decks."""
    s, l = COMP["mstand"], COMP["laptop"]
    sw, sd, sh = s["size"]
    side = [(-sd / 2, 0.0), (sd / 2, 0.0), (sd / 2, sh), (-sd / 2, 0.02)]          # (y, z): high at the back
    stand = geo.prism("desk_laptop_stand", [(y, z) for y, z in side], "X", -sw / 2, sw / 2, material=mats["alu"], **kw)
    geo.place(stand, s["at"], s["yaw"])
    w, d, h = l["size"]
    tilt = math.atan2(sh - 0.02, sd)                                          # the stand's slope
    base = geo.rounded_box("desk_laptop_base", w, d, 0.017, 0.01, material=mats["alu"], **kw)
    lid = geo.rounded_box("desk_laptop_lid", w, 0.007, h - 0.017, 0.01, at=(0, d / 2 - 0.0035, 0.012),
                          material=mats["alu"], **kw)
    lid.rotation_euler = (math.radians(-18), 0, 0)
    scr = geo.box("desk_laptop_glass", -w / 2 + 0.012, w / 2 - 0.012, -0.0006, 0.0, 0.012, h - 0.03,
                  material=mats["glass"], **kw)
    scr.location = (0, d / 2 - 0.007, 0.012)
    scr.rotation_euler = lid.rotation_euler
    lap = geo.join([base, lid, scr], "desk_laptop")
    # onto the stand's slope (back up), then turned with it
    sx, sy, _ = s["at"]
    lap.matrix_basis = (Matrix.Translation((sx, sy, TOP + (sh + 0.02) / 2 + 0.004))
                        @ Matrix.Rotation(math.radians(s["yaw"]), 4, "Z") @ Matrix.Rotation(tilt, 4, "X"))
    return stand, lap


def build_plant(mats, kw):
    c = COMP["snake_plant"]
    x, y, z = c["at"]
    w, _, h = c["size"]
    pot = geo.cylinder("desk_plant_pot", w / 2, (x, y, z), (x, y, z + 0.12), segments=24, material=mats["white"], **kw)
    blades = []
    for k in range(7):
        a = k * 2.4
        rr = 0.012 + 0.02 * (k % 3) / 2
        bx, by = x + rr * math.cos(a), y + rr * math.sin(a)
        top = z + h * (0.72 + 0.28 * ((k * 3) % 5) / 4)
        lean = 0.025 + 0.01 * (k % 2)
        blades.append((0.011, (bx, by, z + 0.10), (bx + lean * math.cos(a), by + lean * math.sin(a), top)))
    leaves = geo.cylinders("desk_plant_leaves", blades, segments=5, material=mats["leaf"], **kw)
    return geo.join([pot, leaves], "desk_plant")


def build():
    root, coll = geo.root("set_desk")
    kw = dict(collection=coll, parent=root)
    mats = _mats()
    parts = {"desk_top": build_top(mats["white"], kw)}
    for i, (x, y, yaw) in enumerate(D["drawers"], 1):
        parts[f"desk_drawers_{i:02d}"] = build_drawers(i, x, y, yaw, mats, kw)
    parts["desk_led"] = build_led(mats["led"], kw)
    c = COMP["pole"]
    x, y, z = c["at"]
    parts["desk_pole"] = geo.cylinder("desk_pole", c["size"][0] / 2, (x, y, z), (x, y, z + c["size"][2]), segments=20,
                                      material=mats["white"], **kw)
    parts["desk_screenbar"] = standin("desk_screenbar", "screenbar", mats["black"], kw, r=0.012)
    parts["desk_mat"] = standin("desk_mat", "mat", mats["felt"], kw, r=0.02)
    kb = standin("desk_keyboard", "keyboard", mats["white"], kw, r=0.008)
    parts["desk_keyboard"] = kb
    for o in (parts["desk_mat"], kb):           # both lie on the mat's top / the desk top
        o.location.z = TOP + (0.004 if o is kb else 0.0)
    parts["desk_mouse"] = build_mouse(mats["grey"], kw)
    parts["desk_mouse"].location.z = TOP + 0.004
    parts["desk_streamdeck"] = standin("desk_streamdeck", "streamdeck", mats["white"], kw, r=0.008)
    for i in (1, 2):
        parts[f"desk_keylight_{i:02d}"] = build_keylight(i, mats, kw)
    parts["desk_camera"] = build_camera(mats, kw)
    parts["desk_laptop_stand"], parts["desk_laptop"] = build_laptop(mats, kw)
    parts["desk_plant"] = build_plant(mats, kw)
    return root, parts
