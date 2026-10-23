"""Rough 3D blockout of room plan v3 (2026-10-24): the owner's photo layout, from blender/lib/plan_v3.py.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/design/room_plan_v3_blockout.py

Boxes, cylinders and flat guitar outlines, EEVEE, for judging composition only; nothing here is
exported or read by build.py. Reads plan_v3 only (the drawing helpers are copied from the v2
blockout, which runs on import). Writes video-local/footage/2026-10-24-room-plan-v3/:
v3-hero.png (16:9), v3-hero-portrait.png (4:5, the photo's shape), v3-intro.png, v3-about.png,
v3-phone.png and v3-top.png.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from lib import plan_v3 as P  # noqa: E402

C = P.C
RX, RY, H = P.RX, P.RY, P.H
W = P.WINDOW_V3
OUT = os.path.join(C.FOOTAGE, "2026-10-24-room-plan-v3")
MATS = {}


def mat(col, emit=None, strength=4.0, rough=0.6, metal=0.0):
    k = (col, emit, strength, rough, metal)
    if k in MATS:
        return MATS[k]
    m = bpy.data.materials.new(f"v3_{len(MATS)}")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    h = col.lstrip("#")
    b.inputs["Base Color"].default_value = (*[(int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)], 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        e = emit.lstrip("#")
        b.inputs["Emission Color"].default_value = (*[(int(e[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)], 1)
        b.inputs["Emission Strength"].default_value = strength
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
    o.matrix_world = Matrix.Translation(p0) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    return o


def slab_poly(name, pts, t, m, M):
    n = len(pts)
    v = [(u, -t / 2, w) for u, w in pts] + [(u, t / 2, w) for u, w in pts]
    f = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    o = obj(name, v, f, m)
    o.matrix_world = M
    return o


def guitar_outline(length, width, archtop=False, n=40):
    """Flat guitar silhouette (u across, v up): body, neck, head (as room_plan_sheet.guitar_outline)."""
    bh = length * (0.47 if archtop else 0.42)
    prof = [(0.0, 0.0), (0.04, 0.62), (0.12, 0.88), (0.28, 1.0), (0.44, 0.93), (0.58, 0.74), (0.66, 0.70),
            (0.78, 0.78), (0.88, 0.74), (0.96, 0.52), (1.0, 0.2)]

    def f(t):
        for (t0, f0), (t1, f1) in zip(prof, prof[1:]):
            if t <= t1:
                k = 0.5 - 0.5 * math.cos(math.pi * (t - t0) / (t1 - t0))
                return f0 + (f1 - f0) * k
        return prof[-1][1]
    right = [(f(i / n) * width / 2, i / n * bh) for i in range(n + 1)]
    body = right + [(-x, v) for x, v in reversed(right[1:-1])]
    nw, hw = 0.046, 0.085
    neck = [(-nw / 2, bh * 0.9), (nw / 2, bh * 0.9), (nw / 2 * 0.85, length - 0.19), (-nw / 2 * 0.85, length - 0.19)]
    head = [(-nw / 2 * 0.85, length - 0.19), (hw / 2, length - 0.15), (hw / 2 * 0.9, length), (-hw / 2 * 0.5, length)]
    return body, neck, head


def guitar(name, length, width, t, col, M, double=False, archtop=False):
    body, neck, head = guitar_outline(length * (0.92 if double else 1.0), width, archtop)
    off = M @ Matrix.Translation((0, -t * 0.3, 0))
    for k, du in enumerate((-0.085, 0.085) if double else (0.0,)):
        slab_poly(f"{name}_neck{k}", [(u + du, v) for u, v in neck], t * 0.5, mat("#3a2414"), off)
        slab_poly(f"{name}_head{k}", [(u + du, v) for u, v in head], t * 0.5, mat("#8b1e22" if double else "#2a1a12"), off)
    slab_poly(f"{name}_body", body, t, mat(col, rough=0.85), M)


# ---------------------------------------------------------------------------
def build_room():
    floor = mat("#4d5563", rough=0.95)                      # the photo's blue-grey carpet
    wall, ceil = mat("#e3e6ec", rough=0.85), mat("#f0f1f4", rough=0.9)
    box("floor", -RX - 0.2, RX + 0.2, -RY - 0.2, RY + 0.3, -0.05, 0, floor)
    box("ceiling", -RX - 0.2, RX + 0.2, -RY - 0.2, RY + 0.3, H, H + 0.05, ceil)
    D = P.DOOR
    box("wall_l_a", -RX - 0.15, -RX, -RY, D["y0"], 0, H, wall)
    box("wall_l_b", -RX - 0.15, -RX, D["y1"], RY, 0, H, wall)
    box("wall_l_head", -RX - 0.15, -RX, D["y0"], D["y1"], D["head"], H, wall)
    box("door", -RX - 0.10, -RX - 0.065, D["y0"], D["y1"], 0, D["head"], mat("#f4f2ee", rough=0.5))
    box("wall_right", RX, RX + 0.15, -RY, RY, 0, H, mat("#e0e2e8", rough=0.85))
    box("wall_front", -RX, RX, -RY - 0.15, -RY, 0, H, wall)
    bt = C.ROOM["wall_back_t"]
    for nm, x0, x1, z0, z1 in (("wb_l", -RX, W["x0"], 0, H), ("wb_r", W["x1"], RX, 0, H),
                               ("wb_low", W["x0"], W["x1"], 0, W["sill"]), ("wb_top", W["x0"], W["x1"], W["head"], H)):
        box(nm, x0, x1, RY, RY + bt, z0, z1, wall)
    box("ledge", W["x0"] - W["ledge_horn"], W["x1"] + W["ledge_horn"], RY - P.LEDGE_IN, RY + 0.05, W["sill"] - W["ledge_t"],
        W["sill"], mat("#8f8a82", rough=0.4))
    al = mat("#b9bcc0", rough=0.3, metal=0.8)
    for x in (W["x0"], (W["x0"] + W["x1"]) / 2, W["x1"]):
        box("win_frame_v", x - 0.025, x + 0.025, RY + 0.10, RY + 0.14, W["sill"], W["head"], al)
    for z in (W["sill"], W["head"]):
        box("win_frame_h", W["x0"], W["x1"], RY + 0.10, RY + 0.14, z - 0.025, z + 0.025, al)
    nb = max(6, round((W["head"] - W["sill"]) / 0.175))
    for i in range(1, nb):                                  # MS grill bars, about 17.5 cm apart
        z = W["sill"] + (W["head"] - W["sill"]) * i / nb
        box("grill", W["x0"], W["x1"], RY + 0.17, RY + 0.18, z - 0.006, z + 0.006, mat("#2b2d31"))
    for nm, a in (("sk_l", (-RX, -RX + 0.012, D["y1"], RY)), ("sk_r", (RX - 0.012, RX, -RY, RY)),
                  ("sk_b", (-RX, RX, RY - 0.012, RY)), ("sk_f", (-RX, RX, -RY, -RY + 0.012))):
        box(nm, *a, 0, 0.10, mat("#f4f2ee"))
    # outside: a sky and a stand-in city, for the intro
    # the room is on a fourth floor: the street 12 m down, the city 12 to 45 m out
    box("sky", -60, 60, RY + 60, RY + 61, -20, 50, mat("#9cc0ea", emit="#a9c8ee", strength=1.8))
    box("ground", -60, 60, RY + 1, RY + 60, -12.2, -12, mat("#6d7480", rough=0.9))
    import random
    rnd = random.Random(7)
    for i in range(70):
        dpt = RY + rnd.uniform(12.0, 45.0)
        x = rnd.uniform(-0.5, 0.5) * dpt * 1.4
        top = rnd.uniform(-10.0, -2.0) + dpt * 0.12
        wd = rnd.uniform(2.0, 5.0)
        haze = min(1.0, (dpt - 12) / 40)               # far blocks fade towards the sky
        c0, c1 = (0x5f, 0x6e, 0x88), (0x9c, 0xb0, 0xcc)
        col = "#" + "".join(f"{int(a_ + (b_ - a_) * haze):02x}" for a_, b_ in zip(c0, c1))
        box(f"city_{i}", x, x + wd, dpt, dpt + wd, -12, top, mat(col, rough=0.8))


def build_desk():
    top = mat("#f4f4f1", rough=0.35)
    z0, z1 = P.TOP - P.TOP_T, P.TOP
    m, r = P.MAIN, P.RET
    box("desk_main", m["x0"], m["x1"], m["y0"], m["y1"], z0, z1, top)
    box("desk_ret", r["x0"], r["x1"], r["y0"], r["y1"], z0, z1, top)
    led = mat("#7fb6ff", emit="#7fb6ff", strength=14)
    i = P.LED_IN
    box("led_main", m["x1"] - i - 0.005, m["x1"] - i + 0.005, m["y0"] + 0.03, r["y0"] + i, z0 - 0.008, z0, led)
    box("led_ret", m["x1"] - i, r["x1"] - 0.03, r["y0"] + i - 0.005, r["y0"] + i + 0.005, z0 - 0.008, z0, led)
    for k, (x, y, yaw) in enumerate(P.DRAWERS):
        w, d, h = P.ALEX
        M = at(x, y, 0, yaw)
        box(f"alex{k}", -w / 2, w / 2, -d / 2, d / 2, 0, h, top, M)
        for j in range(5):
            zz = h * (j + 0.5) / 5 + 0.05
            box(f"alex{k}_pull{j}", -0.06, 0.06, -d / 2 - 0.004, -d / 2, zz - 0.006, zz + 0.006, mat("#3a3c40"), M)


def neon(M):
    ne = mat("#ffffff", emit="#f4f8ff", strength=16)
    for u0, u1, v in ((-0.33, -0.05, 0.19), (0.0, 0.33, 0.19), (-0.22, 0.25, 0.07)):
        box("neon_stroke", u0, u1, -0.01, 0.0, v - 0.008, v + 0.008, ne, M)


def build_parts():
    skip = {"desk", "led", "window", "chair", "piano", "bench", "rack", "mic", "rug", "dj_stand"}
    for c in P.COMPONENTS:
        k = c["key"]
        if k in skip or k.startswith("alex") or k.startswith("guitar_0"):
            continue
        w, d, h = c["size"]
        x, y, z = c["at"]
        m = mat(c["col"], emit=c["glow"], strength=3.0) if c["glow"] and c["shape"] == "slab" else mat(c["col"])
        if c["shape"] == "cyl":
            if k == "snake_plant":
                cyl("snake_pot", w / 2, (x, y, z), (x, y, z + 0.13), mat("#f2f2ef"))
                for j in range(8):
                    a = j * 0.8
                    cyl("snake_leaf", 0.014, (x + 0.02 * math.cos(a), y + 0.02 * math.sin(a), z + 0.13),
                        (x + 0.055 * math.cos(a), y + 0.055 * math.sin(a), z + h * (0.75 + 0.25 * (j % 2))), m, 6)
                continue
            if k in ("plant", "desk_plant"):
                pot = 0.13 if k == "plant" else 0.09
                cyl(k + "_pot", w / 2, (x, y, z), (x, y, z + pot), mat("#b4553a" if k == "plant" else "#f2f2ef"))
                for j in range(6):
                    a = j * 1.05
                    s = 1.0 if k == "plant" else 0.55
                    box("leaf", -0.07 * s, 0.07 * s, -0.005, 0.005, -0.05 * s, 0.05 * s, m,
                        at(x + 0.07 * s * math.cos(a), y + 0.06 * s * math.sin(a), z + pot + 0.07 * s + 0.03 * s * j,
                           math.degrees(a)) @ Matrix.Rotation(0.5, 4, "X"))
                continue
            if k.startswith("vine_pot"):
                cyl(k, w / 2, (x, y, z), (x, y, z + h), mat("#f2f2ef"))
                continue
            if k.startswith("vine_"):
                for j in range(5):
                    a = j * 1.3
                    cyl(k, 0.012, (x + 0.03 * math.cos(a), y + 0.03 * math.sin(a), z + h),
                        (x + 0.045 * math.cos(a), y + 0.045 * math.sin(a), z + h * (0.05 + 0.25 * (j % 3))), m, 6)
                    for q in range(6):
                        zz = z + h * (0.15 + 0.14 * q)
                        box("vine_leaf", -0.025, 0.025, -0.003, 0.003, -0.02, 0.02, m,
                            at(x + 0.045 * math.cos(a), y + 0.045 * math.sin(a), zz, math.degrees(a + q)))
                continue
            if k == "pendant":
                cyl("pendant_cord", 0.004, (x, y, H), (x, y, z + h), mat("#222222"))
                cyl("pendant_shade", w / 2, (x, y, z), (x, y, z + h), mat(c["col"], emit="#ffb066", strength=1.5))
                continue
            if k == "lightstick":
                cyl("ls_cradle", 0.035, (x, y, z), (x, y, z + 0.03), mat("#d8d8de"))
                cyl("ls_handle", 0.016, (x, y, z + 0.03), (x, y, z + 0.18), mat("#e9e3f5"))
                cyl("ls_head", 0.045, (x, y, z + 0.18), (x, y, z + 0.27), mat("#e9e3f5", emit="#d9a0ff", strength=6))
                continue
            cyl(k, w / 2, (x, y, z), (x, y, z + h), m)
            continue
        M = at(x, y, z, c["yaw"])
        if k == "neon":
            neon(M)
            continue
        if k == "nanoleaf":
            nl = [mat("#dfe6ff", emit=e, strength=3) for e in ("#7a8cff", "#9fd8ff", "#c79bff")]
            s3, hh = 0.23, 0.23 * math.sqrt(3) / 2
            cells = [(0, 0, 1), (1, 0, -1), (2, 0, 1), (1, 1, 1), (2, 1, -1), (3, 1, 1), (2, 2, 1)]
            for j, (i, jj, up) in enumerate(cells):
                u, v = -w / 2 + i * s3 / 2, jj * hh
                pts = [(u, v), (u + s3, v), (u + s3 / 2, v + hh)] if up > 0 else [(u, v + hh), (u + s3 / 2, v), (u + s3, v + hh)]
                slab_poly("nanoleaf_t", [(a * 0.94 + (u + s3 / 2) * 0.06, b * 0.94 + (v + hh / 2) * 0.06) for a, b in pts],
                          0.01, nl[j % 3], M)
            continue
        if k == "pegboard":
            box(k, -w / 2, w / 2, -d / 2, d / 2, 0, h, mat("#ffffff", emit="#cfe0ff", strength=0.5), M)
            for i in range(2):     # two little shelves
                box("peg_shelf", -0.30 + i * 0.30, -0.08 + i * 0.30, -0.12, -d / 2, 0.14 + i * 0.20, 0.155 + i * 0.20, mat("#ffffff"), M)
            continue
        if k == "laptop":
            gm = mat(c["col"], rough=0.3, metal=0.6)
            box("laptop_base", -w / 2, w / 2, -d / 2, d / 2, 0, 0.017, gm, M)
            box("laptop_lid", -w / 2, w / 2, d / 2 - 0.006, d / 2, 0.017, h, gm, M)
            box("laptop_screen", -w / 2 + 0.01, w / 2 - 0.01, d / 2 - 0.008, d / 2 - 0.006, 0.027, h - 0.01,
                mat("#0d0f14", emit=c["glow"], strength=0.9), M)
            continue
        if k == "mstand":
            gm = mat(c["col"], rough=0.3, metal=0.6)
            box("mstand_top", -w / 2, w / 2, -d / 2, d / 2, h - 0.006, h, gm, M @ Matrix.Rotation(-0.10, 4, "X"))
            box("mstand_leg", -0.04, 0.04, -d / 2 + 0.03, d / 2, 0, h - 0.006, gm, M)
            continue
        if k.startswith("frame_"):
            M = M @ Matrix.Translation((0, 0.03, 0)) @ Matrix.Rotation(-0.10, 4, "X")
            box(k, -w / 2, w / 2, -d / 2, d / 2, 0, h, m, M)
            box(k + "_pic", -w / 2 + 0.04, w / 2 - 0.04, -d / 2 - 0.002, -d / 2, 0.04, h - 0.04,
                mat(["#c9d6e8", "#e8dcc9", "#d4e2d0"][int(k[-1]) - 1]), M)
            continue
        if k in ("ultrawide", "studio_display"):
            box(k, -w / 2, w / 2, -d / 2, d / 2, 0, h, mat(c["col"], rough=0.3, metal=0.6 if c["col"] != P.B_ else 0), M)
            inset = 0.008 if k == "ultrawide" else 0.013
            if k == "studio_display":     # posts canvas 16:10 inside the 16:9 glass
                box("sd_glass", -w / 2 + inset, w / 2 - inset, -d / 2 - 0.002, -d / 2, inset, h - inset, mat("#06070a", rough=0.1), M)
                box("posts_canvas", -P.POSTS["w"] / 2, P.POSTS["w"] / 2, -d / 2 - 0.004, -d / 2 - 0.002, inset, h - inset,
                    mat("#0b1730", emit="#6f9de0", strength=1.2), M)
            else:
                box("uw_glass", -w / 2 + inset, w / 2 - inset, -d / 2 - 0.002, -d / 2, inset, h - inset,
                    mat("#0b1730", emit="#3fa0d8", strength=1.8), M)
            continue
        if k == "pc":
            box("pc_frame_b", -w / 2, w / 2, -d / 2, d / 2, 0, 0.03, mat("#f2f2ef"), M)
            box("pc_frame_t", -w / 2, w / 2, -d / 2, d / 2, h - 0.02, h, mat("#e8eef5", rough=0.1), M)
            box("pc_back", -w / 2, w / 2, d / 2 - 0.02, d / 2, 0, h, mat("#f2f2ef"), M)
            box("pc_side_l", -w / 2, -w / 2 + 0.02, -d / 2, d / 2, 0, h, mat("#f2f2ef"), M)
            box("pc_inside", -w / 2 + 0.02, w / 2 - 0.03, -d / 2 + 0.03, d / 2 - 0.02, 0.03, h - 0.02,
                mat("#e9eef6", emit="#8fc2ff", strength=0.6), M)
            ring = mat("#bfe4ff", emit="#9fd0ff", strength=6)
            for j in range(3):     # three fans on the bottom-side bracket, seen through the glass
                yy = -d / 2 + 0.10 + j * 0.14
                cyl("fan", 0.055, (M @ Vector((w / 2 - 0.035, yy, 0.12)))[:], (M @ Vector((w / 2 - 0.03, yy, 0.12)))[:], ring, 18)
                cyl("fan_top", 0.055, (M @ Vector((0, yy, h - 0.06)))[:], (M @ Vector((0, yy, h - 0.055)))[:], ring, 18)
            box("gpu", -0.06, 0.08, -0.15, 0.15, 0.20, 0.24, mat("#2c2d30", metal=0.8, rough=0.3), M)
            continue
        if k.startswith("keylight_") and not k.startswith("keylight_pole"):
            box(k, -w / 2, w / 2, -d / 2, d / 2, 0, h, mat("#1b1b1d"), M)
            box(k + "_face", -w / 2 + 0.01, w / 2 - 0.01, -d / 2 - 0.002, -d / 2, 0.01, h - 0.01,
                mat("#ffffff", emit="#fff6ea", strength=7), M)
            continue
        if k.startswith("spk_plate"):
            box(k, -w / 2, w / 2, -d / 2, d / 2, 0, h, mat("#f2f2ef"), M)
            continue
        box(k, -w / 2, w / 2, -d / 2, d / 2, 0, h, m, M)
        if k.startswith("a7v"):
            cyl(k + "_woofer", 0.075, (M @ Vector((0, -d / 2, 0.12)))[:], (M @ Vector((0, -d / 2 - 0.004, 0.12)))[:], mat("#1b1b1d"), 24)
            cyl(k + "_tw", 0.035, (M @ Vector((0, -d / 2, P.TWEETER_UP)))[:], (M @ Vector((0, -d / 2 - 0.004, P.TWEETER_UP)))[:],
                mat("#2b2b2f"), 20)
        if k == "dj":
            for s in (-1, 1):
                cyl("jog", 0.068, (M @ Vector((s * 0.14, 0, h)))[:], (M @ Vector((s * 0.14, 0, h + 0.008)))[:],
                    mat("#2b2b2f", metal=0.6, rough=0.3))
            for s in (-1, 1):
                box("pads", s * 0.14 - 0.06, s * 0.14 + 0.06, -0.12, -0.08, h, h + 0.004, mat("#ff8a3d", emit="#ff8a3d", strength=2), M)


def build_specials():
    wht = mat("#f2f2ef")
    # mic arm (PSA1+ white) and the MV7+
    arm = P.mic_arm()
    for a, b in zip(arm[:-2], arm[1:-1]):
        cyl("mic_arm", 0.011, a, b, wht, 10)
    cap = Vector(P.MIC["capsule"])
    cyl("mic_hang", 0.006, arm[-2], (cap + Vector((0, 0, 0.04)))[:], wht, 8)
    to_ear = (Vector(P.EAR_SEATED) - cap).normalized()
    cyl("mic_capsule", 0.04, (cap - to_ear * 0.085)[:], (cap + to_ear * 0.085)[:], mat("#f4f4f2"), 16)
    # monitor pole arms (VESA) and the camera's flex arm
    for z in (P.UW["z"] + P.UW["h"] / 2, P.SD["z"] + P.SD["h"] / 2):
        box("pole_arm", P.POLE[0], P.SD["x"], P.YM - 0.02, P.YM + 0.02, z - 0.02, z + 0.02, wht)
    camc = P.CP["camera"]
    cyl("flex_arm", 0.008, P.CAM_ARM_FROM, (camc["at"][0], camc["at"][1], camc["at"][2] + 0.035), mat("#1b1b1d"), 8)
    # chair (Aeron-ish): star base, seat, mesh back, facing the screens
    ch = P.CP["chair"]
    x, y, _ = ch["at"]
    M = at(x, y, 0, ch["yaw"])
    g = mat("#9da1a7", rough=0.5, metal=0.5)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        cyl("chair_leg", 0.02, (x, y, 0.06), (x + 0.33 * math.cos(a), y + 0.33 * math.sin(a), 0.04), g, 8)
    cyl("chair_gas", 0.025, (x, y, 0.06), (x, y, 0.42), g, 10)
    box("chair_seat", -0.25, 0.25, -0.24, 0.22, 0.42, 0.48, mat("#5d6168"), M)
    box("chair_back", -0.23, 0.23, 0.22, 0.27, 0.55, 1.04, mat("#7b8088", rough=0.8), M @ Matrix.Rotation(-0.18, 4, "X"))
    for s in (-1, 1):
        box("chair_arm", s * 0.30 - 0.03, s * 0.30 + 0.03, -0.15, 0.15, 0.64, 0.67, mat("#3c3f45"), M)
    # piano (case from the PIANO numbers, in the piano frame) and bench
    Pn = C.PIANO
    PM = at(P.PIANO_V3["x"], P.PIANO_V3["y"], 0, P.PIANO_V3["yaw"])
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
    box("piano_sheet", -0.21, 0.21, -0.44, -0.43, C.KT + 0.25, C.KT + 0.25 + 0.297, mat("#f4f0e6"), PM)
    B = C.BENCH
    bcy = B["cy"] + P.PIANO_V3["bench_in"]
    box("bench_top", -B["w"] / 2, B["w"] / 2, bcy - B["d"] / 2, bcy + B["d"] / 2, B["h"] - B["t"], B["h"], lac, PM)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("bench_leg", sx * B["leg_x"] - 0.02, sx * B["leg_x"] + 0.02, bcy + sy * (B["d"] / 2 - 0.04) - 0.02,
                bcy + sy * (B["d"] / 2 - 0.04) + 0.02, 0, B["h"] - B["t"], lac, PM)
    # wall guitars over the lid, facing -X
    WG = P.WALL_GUITARS_V3
    cols = ["#141414", "#ece8dc", "#8b1e22"]
    for i in range(3):
        y = WG["y"][i]
        M = Matrix.Translation((RX - WG["off_wall"], y, WG["bottom"])) @ Matrix.Rotation(math.radians(-90), 4, "Z")
        guitar(f"wall_g{i}", WG["length"][i], WG["width"][i], 0.045, cols[i], M, double=(i == 2), archtop=(i == 0))
        for k in range(WG["hooks"][i]):
            dy = 0 if WG["hooks"][i] == 1 else (-0.085, 0.085)[k]
            hz = WG["bottom"] + WG["length"][i] - WG["hook_from_top"][i]
            cyl("hook", 0.006, (RX, y - dy, hz), (RX - 0.10, y - dy, hz + 0.02), mat("#cfd2d6", metal=1, rough=0.2), 8)
    # floor rack with 04 to 06
    rk = P.RACK_V3
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
    for i, ((ln, wd, col), sl) in enumerate(zip([(0.977, 0.323, "#9a5a24"), (1.00, 0.47, "#ece6d2"), (0.98, 0.32, "#a98aa9")], slots)):
        M = RM @ Matrix.Translation((-0.08, sl, rk["cradle"])) @ Matrix.Rotation(lean, 4, "Y")
        guitar(f"rack_g{i}", ln, wd, 0.045, col, M)
    # DJ stand: four slim legs, the top, a low rail
    ds = P.DJ_STAND
    DM = at(ds["x"], ds["y"], 0, ds["yaw"])
    st = mat(ds["colour"], metal=0.4, rough=0.45)
    w2, d2 = ds["w"] / 2, ds["d"] / 2
    box("dj_top", -w2, w2, -d2, d2, ds["top"] - ds["t"], ds["top"], mat("#2a2624", rough=0.5), DM)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("dj_leg", sx * (w2 - 0.03) - 0.0125, sx * (w2 - 0.03) + 0.0125, sy * (d2 - 0.03) - 0.0125,
                sy * (d2 - 0.03) + 0.0125, 0, ds["top"] - ds["t"], st, DM)
    box("dj_rail", -w2 + 0.03, w2 - 0.03, -0.01, 0.01, 0.15, 0.18, st, DM)
    # rug
    rg = P.RUG
    box("rug", rg["x"] - rg["w"] / 2, rg["x"] + rg["w"] / 2, rg["y"] - rg["d"] / 2, rg["y"] + rg["d"] / 2, 0, 0.012,
        mat("#9aa3b0", rough=0.95))


def lights():
    sc = bpy.context.scene
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.62, 0.75, 1)
    bg.inputs["Strength"].default_value = 0.5
    d = bpy.data.lights.new("day", "AREA")
    d.shape, d.size, d.size_y = "RECTANGLE", W["x1"] - W["x0"], W["head"] - W["sill"]
    d.energy, d.color = 420, (0.80, 0.88, 1.0)
    o = bpy.data.objects.new("day", d)
    sc.collection.objects.link(o)
    o.location = ((W["x0"] + W["x1"]) / 2, RY + 0.05, (W["sill"] + W["head"]) / 2)
    o.rotation_euler = (math.radians(90), 0, math.radians(180))
    f = bpy.data.lights.new("fill", "AREA")
    f.size, f.energy, f.color = 3.2, 420, (0.92, 0.95, 1.0)
    of = bpy.data.objects.new("fill", f)
    sc.collection.objects.link(of)
    of.location = (0.0, -0.3, 2.95)
    for k, (x, y) in enumerate(((P.MAIN["x1"] - 0.10, P.YM), (-1.0, P.RET["y0"] + 0.10))):
        q = bpy.data.lights.new(f"desk_glow{k}", "POINT")
        q.energy, q.color, q.shadow_soft_size = 30, (0.55, 0.75, 1.0), 0.3
        oq = bpy.data.objects.new(f"desk_glow{k}", q)
        sc.collection.objects.link(oq)
        oq.location = (x, y, 0.45)
    for k in (1, 2):           # the key lights
        c = P.CP[f"keylight_{k}"]
        L = bpy.data.lights.new(f"kl{k}", "AREA")
        L.size, L.energy, L.color = 0.3, 40, (1.0, 0.97, 0.92)
        ol = bpy.data.objects.new(f"kl{k}", L)
        sc.collection.objects.link(ol)
        x, y, z = c["at"]
        ol.location = (x, y, z + 0.125)
        ol.rotation_euler = (math.radians(90), 0, math.radians(c["yaw"]))


def camera(name, pos, target, vfov, ortho=None):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(cam)
    cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_start = 0.05
    if ortho:
        cam.data.type, cam.data.ortho_scale = "ORTHO", ortho
    else:
        cam.data.sensor_fit = "VERTICAL"
        cam.data.angle = math.radians(vfov)
    return cam


def shoot(name, cam, res):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    top = cam.data.type == "ORTHO"
    bpy.data.objects["ceiling"].hide_render = top
    bpy.data.objects["fill"].data.energy = 700 if top else 420
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)


def main():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    build_room()
    build_desk()
    build_parts()
    build_specials()
    lights()
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in
                                                                       bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 32
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    os.makedirs(OUT, exist_ok=True)
    hv = P.HERO_V3
    only = os.environ.get("ONLY", "")
    shots = [
        ("v3-hero", camera("hero_v3", hv["pos"], hv["target"], hv["vfov"]), (1600, 900)),
        ("v3-hero-portrait", camera("hero_v3_portrait", hv["pos"], hv["target"], hv["portrait_vfov"]), (880, 1100)),
        ("v3-intro", camera("intro", P.INTRO["pos"], P.INTRO["target"], P.INTRO["vfov"]), (1600, 900)),
        ("v3-about", camera("about", P.ABOUT["pos"], P.ABOUT["target"], P.ABOUT["vfov"]), (1600, 900)),
        ("v3-phone", camera("phone_v3", P.PHONE_V3["pos"], P.PHONE_V3["target"], P.PHONE_V3["vfov"]), (780, 1688)),
        ("v3-top", camera("top_v3", (0, 0, 2.9), (0, 0, 0), 0, ortho=4.8), (1100, 1050)),
    ]
    for name, cam, res in shots:
        if not only or any(s and s in name for s in only.split(",")):
            shoot(name, cam, res)
    print("room plan v3 blockout done")


main()
