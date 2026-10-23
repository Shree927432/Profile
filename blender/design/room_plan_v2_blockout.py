"""Rough 3D blockout of room plan v2 (NOT approved), seen from the v2 hero camera.

Simple boxes, cylinders and flat guitar outlines from blender/lib/plan_v2.py, EEVEE,
for judging the composition only. Nothing here is exported or used by build.py.

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/design/room_plan_v2_blockout.py
    (fallback: add -b before --factory-startup)

Writes video-local/footage/2026-10-23-room-plan-v2/blockout-hero.png, blockout-phone.png,
blockout-top.png and saves blender/out/room_plan_v2_blockout.blend first.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from lib import constants as C, plan_v2 as P, run  # noqa: E402
from lib.piano_layout import lid_profile  # noqa: E402
import room_plan_sheet as PLAN  # noqa: E402  (guitar_outline only)

RX, RY, H = P.RX, P.RY, P.H
OUT = os.path.join(C.FOOTAGE, "2026-10-23-room-plan-v2")
MATS = {}


def mat(col, emit=None, strength=4.0, rough=0.6, metal=0.0, alpha=1.0):
    k = (col, emit, strength, rough, metal, alpha)
    if k in MATS:
        return MATS[k]
    m = bpy.data.materials.new(f"bo_{len(MATS)}")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    h = col.lstrip("#")
    rgb = [((int(h[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4)]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        e = emit.lstrip("#")
        b.inputs["Emission Color"].default_value = (*[((int(e[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4)], 1)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    MATS[k] = m
    return m


def obj(name, verts, faces, m):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(m)
    return o


def box(name, x0, x1, y0, y1, z0, z1, m, M=None):
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    o = obj(name, v, f, m)
    if M is not None:
        o.matrix_world = M
    return o


def at(x, y, z=0.0, yaw=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")


def cyl(name, r, p0, p1, m, n=20):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    q = d.to_track_quat("Z", "Y")
    v, f = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        v += [(r * math.cos(a), r * math.sin(a), 0), (r * math.cos(a), r * math.sin(a), d.length)]
    for i in range(n):
        j = (i + 1) % n
        f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    f.append(tuple(2 * i for i in reversed(range(n))))
    f.append(tuple(2 * i + 1 for i in range(n)))
    o = obj(name, v, f, m)
    o.matrix_world = Matrix.Translation(p0) @ q.to_matrix().to_4x4()
    return o


def slab_poly(name, pts, t, m, M):
    """Flat polygon in its local X-Z plane (u, v), t thick along local Y, placed by M."""
    n = len(pts)
    v = [(u, -t / 2, w) for u, w in pts] + [(u, t / 2, w) for u, w in pts]
    f = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    o = obj(name, v, f, m)
    o.matrix_world = M
    return o


def guitar(name, length, width, t, col, M, double=False):
    body, neck, head = PLAN.guitar_outline(length * (0.92 if double else 1.0), width)
    if double:
        bh = length * 0.42
        body = [(u * 1.0, v) for u, v in body]
        for k, du in enumerate((-0.085, 0.085)):
            nk = [(u + du, v) for u, v in neck]
            hd = [(u + du, v) for u, v in head]
            slab_poly(f"{name}_neck{k}", nk, t * 0.5, mat("#2a1a12"), M @ Matrix.Translation((0, -t * 0.3, 0)))
            slab_poly(f"{name}_head{k}", hd, t * 0.5, mat("#8b1e22"), M @ Matrix.Translation((0, -t * 0.3, 0)))
        slab_poly(f"{name}_body", body, t, mat(col, rough=0.25), M)
        return
    slab_poly(f"{name}_body", body, t, mat(col, rough=0.25), M)
    slab_poly(f"{name}_neck", neck, t * 0.5, mat("#3a2414"), M @ Matrix.Translation((0, -t * 0.3, 0)))
    slab_poly(f"{name}_head", head, t * 0.5, mat("#1a1a1a" if col == "#141414" else "#3a2414"),
              M @ Matrix.Translation((0, -t * 0.3, 0)))


# ---------------------------------------------------------------------------
def build_room():
    oak, wall, ceil = mat("#7a5233", rough=0.5), mat("#dcdde3", rough=0.85), mat("#e8e8ec", rough=0.9)
    box("floor", -RX - 0.2, RX + 0.2, -RY - 0.2, RY + 0.3, -0.05, 0, oak)
    box("ceiling", -RX - 0.2, RX + 0.2, -RY - 0.2, RY + 0.3, H, H + 0.05, ceil)
    box("wall_left", -RX - 0.15, -RX, -RY, RY, 0, H, mat("#d6d8df", rough=0.85))
    box("wall_right", RX, RX + 0.15, -RY, RY, 0, H, mat("#d3d4da", rough=0.85))
    box("wall_front", -RX, RX, -RY - 0.15, -RY, 0, H, wall)
    W = P.WINDOW_V2
    bt = C.ROOM["wall_back_t"]
    for nm, x0, x1, z0, z1 in (("wb_l", -RX, W["x0"], 0, H), ("wb_r", W["x1"], RX, 0, H),
                               ("wb_low", W["x0"], W["x1"], 0, W["sill"]), ("wb_top", W["x0"], W["x1"], W["head"], H)):
        box(nm, x0, x1, RY, RY + bt, z0, z1, wall)
    box("sill_ledge", W["x0"] - 0.05, W["x1"] + 0.05, RY - W["ledge_d"] + 0.05, RY + 0.05, W["sill"] - W["ledge_t"],
        W["sill"], mat("#9a9184", rough=0.4))
    al = mat("#b9bcc0", rough=0.3, metal=0.8)
    for x in (W["x0"], 0.0, W["x1"]):
        box("win_frame_v", x - 0.025, x + 0.025, RY + 0.10, RY + 0.14, W["sill"], W["head"], al)
    for z in (W["sill"], W["head"]):
        box("win_frame_h", W["x0"], W["x1"], RY + 0.10, RY + 0.14, z - 0.025, z + 0.025, al)
    for i in range(1, 6):     # MS grill bars
        z = W["sill"] + (W["head"] - W["sill"]) * i / 6
        box("grill", W["x0"], W["x1"], RY + 0.17, RY + 0.18, z - 0.006, z + 0.006, mat("#2b2d31"))
    box("sky", W["x0"] - 0.4, W["x1"] + 0.4, RY + 0.6, RY + 0.62, W["sill"] - 0.4, W["head"] + 0.4,
        mat("#8fb0ec", emit="#8fb0ec", strength=2.2))
    # door (left wall, by the front corner) and skirting
    D = C.DOOR
    box("door", -RX, -RX + 0.035, D["y0"], D["y1"], 0, D["head"], mat("#efebe4"))
    for nm, a in (("sk_l", (-RX, -RX + 0.012, -RY, RY)), ("sk_r", (RX - 0.012, RX, -RY, RY)),
                  ("sk_b", (-RX, RX, RY - 0.012, RY))):
        box(nm, *a, 0, 0.10, mat("#efebe4"))


def build_desk():
    D = P.DESK_V2
    top = mat(D["colour"], rough=0.35)
    b, r = D["back"], D["ret"]
    z0, z1 = D["top"] - D["t"], D["top"]
    box("desk_back", b["x0"], b["x1"], b["y0"], b["y1"], z0, z1, top)
    box("desk_ret", r["x0"], r["x1"], r["y0"], r["y1"], z0, z1, top)
    led = mat("#7fb6ff", emit="#7fb6ff", strength=12)
    i = D["led_in"]
    box("led_b", r["x1"] - i, b["x1"] - i, b["y0"] + i - 0.005, b["y0"] + i + 0.005, z0 - 0.008, z0, led)
    box("led_r", r["x1"] - i - 0.005, r["x1"] - i + 0.005, r["y0"] + i, b["y0"] + i, z0 - 0.008, z0, led)
    chrome = mat("#cfd2d6", rough=0.2, metal=1.0)
    for k, (x, y, yaw) in enumerate(D["drawers"]):
        w, d, h = P.ALEX
        M = at(x, y, 0, yaw)
        box(f"alex{k}", -w / 2, w / 2, -d / 2, d / 2, 0, h, top, M)
        for j in range(5):
            zz = h * (j + 0.5) / 5
            box(f"alex{k}_h{j}", -0.05, 0.05, -d / 2 - 0.006, -d / 2, zz - 0.004, zz + 0.004, mat("#c8c8c4"), M)
        for sx in (-1, 1) if P.PUCK > 0 else ():
            for sy in (-1, 1):
                cyl(f"puck{k}", 0.015, (M @ Vector((sx * (w / 2 - 0.04), sy * (d / 2 - 0.05), h)))[:],
                    (M @ Vector((sx * (w / 2 - 0.04), sy * (d / 2 - 0.05), h + P.PUCK)))[:], chrome, 10)


def neon(M):
    ne = mat("#ffffff", emit="#f4f8ff", strength=14)
    for k, (u0, u1, v) in enumerate(((-0.33, -0.05, 0.20), (0.0, 0.33, 0.20), (-0.25, 0.25, 0.07))):
        box("neon_stroke", u0, u1, -0.01, 0.0, v - 0.008, v + 0.008, ne, M)


def build_parts():
    for c in P.COMPONENTS:
        if c["shape"] == "special" and c["key"] not in ("window",):
            continue
        if c["key"] in ("window",) or c["key"].startswith("alex"):
            continue
        w, d, h = c["size"]
        x, y, z = c["at"]
        m = mat(c["col"], emit=c["glow"], strength=3.0) if c["glow"] and c["shape"] == "slab" else mat(c["col"])
        if c["shape"] == "cyl":
            if c["key"] == "snake_plant":
                cyl("snake_pot", w / 2, (x, y, z), (x, y, z + 0.12), mat("#f2f2ef"))
                for k in range(7):
                    a = k * 0.9
                    cyl("snake_leaf", 0.012, (x + 0.02 * math.cos(a), y + 0.02 * math.sin(a), z + 0.12),
                        (x + 0.06 * math.cos(a), y + 0.06 * math.sin(a), z + h * (0.75 + 0.25 * (k % 2))), m, 6)
                continue
            if c["key"] == "plant":
                cyl("plant_pot", w / 2, (x, y, z), (x, y, z + 0.13), mat("#b4553a"))
                for k in range(6):
                    a = k * 1.05
                    box("leaf", -0.07, 0.07, -0.005, 0.005, -0.05, 0.05, m,
                        at(x + 0.08 * math.cos(a), y + 0.06 * math.sin(a), z + 0.20 + 0.03 * k, math.degrees(a)) @
                        Matrix.Rotation(0.5, 4, "X"))
                continue
            if c["key"] == "pendant":
                cyl("pendant_cord", 0.004, (x, y, H), (x, y, z + h), mat("#222222"))
                cyl("pendant_shade", w / 2, (x, y, z), (x, y, z + h), mat(c["col"], emit="#ffb066", strength=1.5))
                continue
            if c["key"] == "lightstick":
                cyl("ls_base", 0.04, (x, y, z), (x, y, z + 0.03), mat("#d8d8de"))
                cyl("ls_handle", 0.016, (x, y, z + 0.03), (x, y, z + 0.18), mat("#e9e3f5"))
                cyl("ls_head", 0.045, (x, y, z + 0.18), (x, y, z + 0.27), mat("#e9e3f5", emit="#d9a0ff", strength=6))
                continue
            cyl(c["key"], w / 2, (x, y, z), (x, y, z + h), m)
            continue
        M = at(x, y, z, c["yaw"])
        if c["key"] == "neon":      # a few glowing strokes, our words come later
            neon(M)
            continue
        if c["key"] == "nanoleaf":
            nl = [mat("#dfe6ff", emit=e, strength=3) for e in ("#7a8cff", "#9fd8ff", "#c79bff")]
            s3 = 0.23
            hh = s3 * math.sqrt(3) / 2
            cells = [(0, 0, 1), (1, 0, -1), (2, 0, 1), (1, 1, 1), (2, 1, -1), (3, 1, 1), (3, 0, -1)]
            for k, (i, j, up) in enumerate(cells):
                u = -w / 2 + i * s3 / 2
                v = j * hh
                pts = [(u, v), (u + s3, v), (u + s3 / 2, v + hh)] if up > 0 else [(u, v + hh), (u + s3 / 2, v), (u + s3, v + hh)]
                slab_poly("nanoleaf_t", [(a * 0.94 + (u + s3 / 2) * 0.06, b * 0.94 + (v + hh / 2) * 0.06) for a, b in pts],
                          0.01, nl[k % 3], M)
            continue
        if c["shape"] == "slab":
            box(c["key"], -w / 2, w / 2, -d / 2, d / 2, 0, h, m, M)
            continue
        if c["key"] == "laptop":
            box("laptop_base", -w / 2, w / 2, -d / 2, d / 2, 0, 0.017, mat(c["col"], rough=0.3, metal=0.6), M)
            box("laptop_lid", -w / 2, w / 2, d / 2 - 0.006, d / 2, 0.017, h, mat(c["col"], rough=0.3, metal=0.6), M)
            box("laptop_screen", -w / 2 + 0.01, w / 2 - 0.01, d / 2 - 0.008, d / 2 - 0.006, 0.027, h - 0.01,
                mat("#0d0f14", emit=c["glow"], strength=0.8), M)
            continue
        if c["key"].startswith("frame_"):
            box(c["key"], -w / 2, w / 2, -d / 2, d / 2, 0, h, m, M)
            box(c["key"] + "_pic", -w / 2 + 0.04, w / 2 - 0.04, -d / 2 - 0.002, -d / 2, 0.04, h - 0.04,
                mat(["#c9d6e8", "#e8dcc9", "#d4e2d0"][int(c["key"][-1]) - 1]), M)
            continue
        if c["key"] in ("ultrawide", "studio_display"):
            box(c["key"], -w / 2, w / 2, -d / 2, d / 2, 0, h, mat(c["col"], rough=0.3, metal=0.6 if c["col"] != "#1b1b1d" else 0), M)
            if c["key"] == "laptop":
                box("laptop_screen", -w / 2 + 0.01, w / 2 - 0.01, -d / 2 - 0.002, -d / 2, 0.012, h - 0.012,
                    mat("#0d0f14", emit=c["glow"], strength=1.2), M)
                continue
            inset = 0.008 if c["key"] == "ultrawide" else 0.013
            sw = w - 2 * inset
            if c["key"] == "studio_display":     # posts canvas 16:10 inside the 16:9 glass
                box("sd_glass", -w / 2 + inset, w / 2 - inset, -d / 2 - 0.002, -d / 2, inset, h - inset, mat("#06070a", rough=0.1), M)
                ph = h - 2 * inset
                pw = ph * 1.6
                box("posts_canvas", -pw / 2, pw / 2, -d / 2 - 0.004, -d / 2 - 0.002, inset, h - inset,
                    mat("#0b1730", emit="#6f9de0", strength=0.9), M)
            else:
                box("uw_glass", -sw / 2, sw / 2, -d / 2 - 0.002, -d / 2, inset, h - inset,
                    mat("#0b1730", emit="#3a7bd5", strength=1.4), M)
            continue
        if c["key"] == "pc":
            box("pc_frame", -w / 2, w / 2, -d / 2, d / 2, 0, h, mat("#f2f2ef", alpha=1.0), M)
            # window side (local -X) and front glass (local -Y): glowing insides
            box("pc_inside", -w / 2 - 0.002, -w / 2, -d / 2 + 0.02, d / 2 - 0.02, 0.03, h - 0.03,
                mat("#0e1420", emit="#2d6fd0", strength=0.7), M)
            box("pc_front", -w / 2 + 0.02, w / 2 - 0.02, -d / 2 - 0.002, -d / 2, 0.03, h - 0.03,
                mat("#0e1420", emit="#2d6fd0", strength=0.5), M)
            ring = mat("#bfe4ff", emit="#9fd0ff", strength=5)
            for k in range(3):     # three front fans, glowing rings, seen through the front glass
                zc = 0.10 + k * 0.13
                cyl("fan", 0.055, (M @ Vector((0, -d / 2 - 0.003, zc)))[:], (M @ Vector((0, -d / 2 - 0.005, zc)))[:], ring, 18)
            box("gpu", -w / 2 - 0.004, -w / 2 - 0.002, -0.15, 0.15, 0.20, 0.26, mat("#2c2d30", metal=0.8, rough=0.3), M)
            continue
        if c["key"].startswith("keylight") and not c["key"].startswith("keylight_pole"):
            box(c["key"], -w / 2, w / 2, -d / 2, d / 2, 0, h, mat("#f2f2ef"), M)
            box(c["key"] + "_face", -w / 2 + 0.01, w / 2 - 0.01, -d / 2 - 0.002, -d / 2, 0.01, h - 0.01,
                mat("#ffffff", emit="#fff6ea", strength=5), M)
            continue
        if c["key"] == "screenbar":
            box(c["key"], -w / 2, w / 2, -d / 2, d / 2, 0, h, mat(c["col"]), M)
            continue
        box(c["key"], -w / 2, w / 2, -d / 2, d / 2, 0, h, m, M)
        if c["key"].startswith("a7v"):
            box(c["key"] + "_woofer", -0.07, 0.07, -d / 2 - 0.004, -d / 2, 0.05, 0.19, mat("#1b1b1d"), M)
            box(c["key"] + "_tw", -0.04, 0.04, -d / 2 - 0.004, -d / 2, 0.23, 0.30, mat("#2b2b2f"), M)
        if c["key"] == "dj":
            for s in (-1, 1):
                cyl("jog", 0.075, (M @ Vector((s * 0.13, 0, h)))[:], (M @ Vector((s * 0.13, 0, h + 0.008)))[:],
                    mat("#2b2b2f", metal=0.6, rough=0.3))


def build_specials():
    # mic arm
    mc = P.MIC
    blk = mat("#f2f2ef")
    cx, cy = mc["clamp"]
    cyl("mic_riser", 0.012, (cx, cy, P.TOP), (cx, cy, P.TOP + 0.20), blk, 10)
    cyl("mic_arm1", 0.01, (cx, cy, P.TOP + 0.20), mc["elbow"], blk, 10)
    cap = mc["capsule"]
    cyl("mic_arm2", 0.01, mc["elbow"], (cap[0] + 0.03, cap[1] + 0.10, cap[2] + 0.12), blk, 10)
    to_ear = (Vector(P.EAR) - Vector(cap)).normalized()
    cyl("mic_capsule", 0.033, (Vector(cap) - to_ear * 0.08)[:], (Vector(cap) + to_ear * 0.075)[:], mat("#f4f4f2"), 16)
    # pole arms for the two screens
    pl = mat("#f2f2ef")
    for z in (0.853 + 0.18, 1.256 + 0.18):
        box("pole_arm", P.XM - 0.02, P.XM + 0.02, 1.88, RY - 0.07, z - 0.02, z + 0.02, pl)
    # camera flex arm
    cam = [c for c in P.COMPONENTS if c["key"] == "camera"][0]
    cyl("flex_arm", 0.008, (-RX + 0.10, RY - 0.08, 1.20), (cam["at"][0], cam["at"][1] + 0.03, cam["at"][2] + 0.03),
        mat("#1b1b1d"), 8)
    # chair (Aeron-ish: star base, seat, mesh back)
    ch = [c for c in P.COMPONENTS if c["key"] == "chair"][0]
    x, y, _ = ch["at"]
    M = at(x, y, 0, ch["yaw"])
    g = mat("#9da1a7", rough=0.5, metal=0.5)
    for k in range(5):
        a = 2 * math.pi * k / 5
        cyl("chair_leg", 0.02, (x, y, 0.06), (x + 0.33 * math.cos(a), y + 0.33 * math.sin(a), 0.04), g, 8)
    cyl("chair_gas", 0.025, (x, y, 0.06), (x, y, 0.42), g, 10)
    box("chair_seat", -0.25, 0.25, -0.24, 0.22, 0.42, 0.48, mat("#5d6168"), M)
    box("chair_back", -0.23, 0.23, 0.22, 0.27, 0.55, 1.06, mat("#6b7078", rough=0.8), M @ Matrix.Rotation(-0.18, 4, "X"))
    for s in (-1, 1):
        box("chair_arm", s * 0.30 - 0.03, s * 0.30 + 0.03, -0.15, 0.15, 0.62, 0.65, mat("#3c3f45"), M)
    # piano (approximate case from PIANO numbers, in the piano frame), bench
    Pn = C.PIANO
    PM = at(P.PIANO_V2["x"], P.PIANO_V2["y"], 0, P.PIANO_V2["yaw"])
    lac = mat("#070707", rough=0.12)
    hw = Pn["width"] / 2
    box("piano_lower", -hw + 0.03, hw - 0.03, Pn["lower_face_y"], 0, Pn["floor_gap"], C.KT - 0.03, lac, PM)
    box("piano_upper", -hw, hw, Pn["panel_face_y"], 0, C.KT - 0.02, Pn["case_top"], lac, PM)
    for s in (-1, 1):
        box("piano_side", s * hw - 0.015, s * hw + 0.015, -Pn["side_depth"], 0, 0, Pn["case_top"], lac, PM)
        box("piano_cheek", s * (hw - 0.03) - 0.03, s * (hw - 0.03) + 0.03, Pn["cheek_front_y"], -0.36, C.KT - 0.08, C.KT + 0.06, lac, PM)
        box("piano_toe", s * Pn["toe_x"] - 0.036, s * Pn["toe_x"] + 0.036, Pn["toe_front_y"], -0.30, 0, 0.06, lac, PM)
    box("piano_keybed", -hw + 0.06, hw - 0.06, Pn["slip_front_y"], -0.40, C.KT - 0.08, C.KT - 0.02, lac, PM)
    box("piano_keys", -0.611, 0.611, -0.555, -0.405, C.KT - 0.02, C.KT, mat("#ebe3d0", rough=0.3), PM)
    box("piano_lid", -hw - 0.01, hw + 0.01, -Pn["side_depth"] - Pn["lid_over_front"], Pn["lid_over_back"],
        Pn["case_top"], Pn["case_top"] + Pn["lid_t"], lac, PM)
    box("piano_sheet", -0.21, 0.21, -0.44, -0.43, C.KT + 0.25, C.KT + 0.25 + 0.297, mat("#f4f0e6"), PM @ Matrix.Translation((0, 0, 0)))
    B = C.BENCH
    bcy = B["cy"] + P.PIANO_V2["bench_in"]
    box("bench_top", -B["w"] / 2, B["w"] / 2, bcy - B["d"] / 2, bcy + B["d"] / 2, B["h"] - B["t"], B["h"], lac, PM)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("bench_leg", sx * B["leg_x"] - 0.02, sx * B["leg_x"] + 0.02, bcy + sy * (B["d"] / 2 - 0.04) - 0.02,
                bcy + sy * (B["d"] / 2 - 0.04) + 0.02, 0, B["h"] - B["t"], lac, PM)
    # wall guitars: facing -X, their u (across, viewer's right) along world -Y
    WG = P.WALL_GUITARS_V2
    cols = ["#141414", "#ece8dc", "#8b1e22"]
    for i in range(3):
        y = WG["y"][i]
        M = Matrix.Translation((RX - WG["off_wall"], y, WG["bottom"])) @ Matrix.Rotation(math.radians(-90), 4, "Z")
        guitar(f"wall_g{i}", WG["length"][i], WG["width"][i], 0.045, cols[i], M, double=(i == 2))
        nh = WG["hooks"][i]
        for k in range(nh):
            dy = 0 if nh == 1 else (-0.085, 0.085)[k]
            hz = WG["bottom"] + WG["length"][i] - WG["hook_from_top"][i]
            cyl("hook", 0.006, (RX, y - dy, hz), (RX - 0.10, y - dy, hz + 0.02), mat("#cfd2d6", metal=1, rough=0.2), 8)
    # floor rack with guitar_04 to _06 (approved rack geometry, v2 place)
    rk = P.RACK_V2
    lean = math.radians(rk["lean"])
    RM = at(rk["x"], rk["y"], 0, rk["yaw"])
    metal = mat("#232326", metal=0.5, rough=0.45)
    bar_x = -0.08 + 0.70 * math.sin(lean)
    bar_z = rk["cradle"] + 0.70 * math.cos(lean)
    box("rack_cradle", -rk["w"] / 2, rk["w"] / 2 - 0.20, -rk["d"] / 2, rk["d"] / 2, rk["cradle"] - 0.03, rk["cradle"], metal, RM)
    box("rack_bar", bar_x, bar_x + 0.03, -rk["d"] / 2, rk["d"] / 2, bar_z - 0.03, bar_z, metal, RM)
    for s in (-1, 1):
        box("rack_foot", -0.12, bar_x + 0.03, s * rk["d"] / 2 - 0.012, s * rk["d"] / 2 + 0.012, 0, 0.03, metal, RM)
        box("rack_post", bar_x, bar_x + 0.025, s * rk["d"] / 2 - 0.012, s * rk["d"] / 2 + 0.012, 0, bar_z, metal, RM)
    slots = [(i - (rk["slots"] - 1) / 2) * rk["pitch"] for i in range(rk["slots"])]
    specs = [(0.977, 0.323, "#9a5a24"), (1.00, 0.47, "#ece6d2"), (0.98, 0.32, "#a98aa9")]
    for i, ((ln, wd, col), sl) in enumerate(zip(specs, slots)):
        M = RM @ Matrix.Translation((-0.08, sl, rk["cradle"])) @ Matrix.Rotation(lean, 4, "Y")
        guitar(f"rack_g{i}", ln, wd, 0.045, col, M)


def lights():
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.03, 0.05, 0.10, 1)
    bg.inputs["Strength"].default_value = 0.6
    W = P.WINDOW_V2
    d = bpy.data.lights.new("dawn", "AREA")
    d.shape, d.size, d.size_y = "RECTANGLE", 1.2, 1.05
    d.energy, d.color = 260, (0.62, 0.74, 1.0)
    o = bpy.data.objects.new("dawn", d)
    sc.collection.objects.link(o)
    o.location = (0, RY + 0.05, (W["sill"] + W["head"]) / 2)
    o.rotation_euler = (math.radians(90), 0, math.radians(180))
    f = bpy.data.lights.new("fill", "AREA")
    f.size, f.energy, f.color = 3.0, 90, (0.70, 0.78, 1.0)
    of = bpy.data.objects.new("fill", f)
    sc.collection.objects.link(of)
    of.location = (0, -1.2, 2.9)
    p = bpy.data.lights.new("pendant", "POINT")
    p.energy, p.color, p.shadow_soft_size = 25, (1.0, 0.72, 0.45), 0.15
    op = bpy.data.objects.new("pendant_l", p)
    sc.collection.objects.link(op)
    op.location = (P.LIGHT_V2["x"], P.LIGHT_V2["y"], 2.38)
    for k, (x, y) in enumerate(((P.XM, 1.55), (-1.95, 1.0))):
        q = bpy.data.lights.new(f"desk_glow{k}", "POINT")
        q.energy, q.color, q.shadow_soft_size = 18, (0.6, 0.78, 1.0), 0.3
        oq = bpy.data.objects.new(f"desk_glow{k}", q)
        sc.collection.objects.link(oq)
        oq.location = (x, y, 0.55)


def job():
    run.log("v2 blockout: building")
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    build_room()
    build_desk()
    build_parts()
    build_specials()
    lights()
    from lib import looks
    hv = P.HERO_V2
    cam = looks.camera("hero_v2", hv["pos"], hv["target"], vfov=hv["vfov"])
    camp = looks.camera("phone_v2", hv["pos"], hv["phone_target"], vfov=hv["phone_vfov"])
    top = bpy.data.cameras.new("top")
    top.type, top.ortho_scale = "ORTHO", 4.9
    ot = bpy.data.objects.new("top_v2", top)
    bpy.context.scene.collection.objects.link(ot)
    ot.location = (0, 0, 2.6)
    run.setup_render("BLENDER_EEVEE", samples=32)
    sc = bpy.context.scene
    sc.view_settings.look = "AgX - Base Contrast"
    os.makedirs(C.OUT, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, "room_plan_v2_blockout.blend"))
    yield
    for name, c, size in (("blockout-hero", cam, (1600, 900)), ("blockout-phone", camp, (780, 1688)),
                          ("blockout-top", ot, (1100, 1050))):
        sc.camera = c
        sc.render.resolution_x, sc.render.resolution_y = size
        sc.render.resolution_percentage = 100
        if name == "blockout-top":
            bpy.data.objects["ceiling"].hide_render = True
            bpy.data.objects["fill"].data.energy = 300
        run.show_in_viewport("MATERIAL")
        dt = yield from run.render_to(os.path.join(OUT, name + ".png"))
        run.log(f"{name} rendered in {dt:.1f} s")
    bpy.data.objects["ceiling"].hide_render = False
    bpy.data.objects["fill"].data.energy = 90
    # option stills for the owner's questions, at a smaller size
    sc.render.resolution_x, sc.render.resolution_y = 1200, 675
    cam50 = looks.camera("hero_50", hv["pos"], hv["target"], vfov=50)
    sc.camera = cam50
    dt = yield from run.render_to(os.path.join(OUT, "option-lens-b-50.png"))
    cut = looks.camera("hero_cut", (hv["pos"][0], hv["pos"][1] - 0.40, hv["pos"][2]), hv["target"], vfov=50)
    bpy.data.objects["wall_front"].hide_render = True
    sc.camera = cut
    dt = yield from run.render_to(os.path.join(OUT, "option-lens-c-cutaway.png"))
    bpy.data.objects["wall_front"].hide_render = False
    for o in [o for o in bpy.data.objects if o.name.startswith("neon_stroke")]:
        bpy.data.objects.remove(o, do_unlink=True)
    neon(at(P.XM, RY - 0.01, 2.40, 0))
    sc.camera = cam
    dt = yield from run.render_to(os.path.join(OUT, "option-neon-b-back-wall.png"))
    run.log("v2 blockout done")
    if run.windowed():
        bpy.ops.wm.quit_blender()


run.drive(job())
