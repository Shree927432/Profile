"""Quick blockout: the AI lab laid out exactly as the owner's photo (ai-desk-reference-1.jpg).

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/design/photo_layout_blockout.py

Preview only (2026-10-24, owner: "i want the exact layout from the photo"). The desk's main run
stands along the LEFT wall, the return along the back wall towards the window, the PC in the
inner corner, the laptop at the return's end beside the window. The music side (right half) is
kept simple: it is the secret the site reveals later. Boxes only, sizes from the component
references; nothing here is final, plan v3 will hold the real numbers once approved.
Writes video-local/footage/2026-10-24-photo-layout/.
"""
import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "video-local", "footage", "2026-10-24-photo-layout")
RX, RY, H = 2.20, 2.10, 3.00
TOP = 0.735
WIN = dict(x0=-0.40, x1=1.00, sill=0.95, head=2.35)
MATS = {}


def mat(hexcol, rough=0.5, metal=0.0, emit=None, strength=8.0):
    key = (hexcol, rough, metal, emit, strength)
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(hexcol)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = tuple(int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5))
    b.inputs["Base Color"].default_value = (*[v ** 2.2 for v in c], 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        e = tuple(int(emit[i:i + 2], 16) / 255 for i in (1, 3, 5))
        b.inputs["Emission Color"].default_value = (*[v ** 2.2 for v in e], 1)
        b.inputs["Emission Strength"].default_value = strength
    MATS[key] = m
    return m


def box(name, x0, x1, y0, y1, z0, z1, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.object
    o.name = name
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    o.data.materials.append(m)
    return o


def cyl(name, x, y, z0, z1, r, m):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0, location=(x, y, (z0 + z1) / 2), vertices=20)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    return o


for _o in list(bpy.data.objects):          # the factory scene's cube, camera and light
    bpy.data.objects.remove(_o, do_unlink=True)
W = mat("#f2f2ef", 0.35)
WALL = mat("#dfe3ea", 0.8)
BLK = mat("#1b1b1d", 0.4)
ALU = mat("#c9ccd1", 0.25, 0.8)
SCR = mat("#3a7bd5", 0.2, emit="#5d97e6", strength=2.5)
GREEN = mat("#3f6b3a", 0.7)

# --- room shell (window on the back wall, door on the left wall near the front)
box("floor", -RX, RX, -RY, RY, -0.02, 0, mat("#8a6b52", 0.6))
box("ceiling", -RX, RX, -RY, RY, H, H + 0.02, WALL)
box("wall_l_a", -RX - 0.15, -RX, -RY, -2.00, 0, H, WALL)
box("wall_l_b", -RX - 0.15, -RX, -1.10, RY, 0, H, WALL)
box("wall_l_door_head", -RX - 0.15, -RX, -2.00, -1.10, 2.10, H, WALL)
box("door", -RX - 0.12, -RX - 0.08, -2.00, -1.10, 0, 2.10, mat("#e9e4dc", 0.5))
box("wall_r", RX, RX + 0.15, -RY, RY, 0, H, WALL)
box("wall_f", -RX, RX, -RY - 0.15, -RY, 0, H, WALL)
box("wall_b_l", -RX, WIN["x0"], RY, RY + 0.23, 0, H, WALL)
box("wall_b_r", WIN["x1"], RX, RY, RY + 0.23, 0, H, WALL)
box("wall_b_sill", WIN["x0"], WIN["x1"], RY, RY + 0.23, 0, WIN["sill"], WALL)
box("wall_b_head", WIN["x0"], WIN["x1"], RY, RY + 0.23, WIN["head"], H, WALL)
box("ledge", WIN["x0"] - 0.02, WIN["x1"] + 0.02, RY - 0.20, RY + 0.05, WIN["sill"] - 0.03, WIN["sill"], mat("#7d7d78", 0.4))
for k in range(1, 9):
    z = WIN["sill"] + k * (WIN["head"] - WIN["sill"]) / 9
    box("grill", WIN["x0"], WIN["x1"], RY + 0.10, RY + 0.115, z - 0.006, z + 0.006, BLK)
box("sky", -3, 4, RY + 1.5, RY + 1.6, -1, 5, mat("#9db8dd", emit="#a9c4ea", strength=1.6))
for i, (x, w, h) in enumerate(((-0.6, 0.5, 1.5), (0.0, 0.4, 2.4), (0.5, 0.6, 1.9), (1.1, 0.35, 2.9), (1.6, 0.5, 1.6))):
    box(f"city_{i}", x, x + w, RY + 1.2, RY + 1.4, 0.4, 0.4 + h, mat("#5b6d88", 0.8))   # stand-in skyline

# --- the L desk: main run along the left wall, return along the back wall to the window
MAIN = dict(x0=-RX, x1=-RX + 0.80, y0=0.25, y1=RY)          # 80 deep, 185 long
RET = dict(x0=-RX + 0.80, x1=WIN["x0"] - 0.08, y0=RY - 0.60, y1=RY)   # 60 deep, to 8 cm short of the window
box("desk_main", MAIN["x0"], MAIN["x1"], MAIN["y0"], MAIN["y1"], TOP - 0.035, TOP, W)
box("desk_ret", RET["x0"], RET["x1"], RET["y0"], RET["y1"], TOP - 0.035, TOP, W)
led = mat("#7fb6ff", emit="#7fb6ff", strength=10)
box("led_main", MAIN["x1"] - 0.05, MAIN["x1"] - 0.04, MAIN["y0"], RET["y0"], TOP - 0.045, TOP - 0.035, led)
box("led_ret", RET["x0"], RET["x1"], RET["y0"] + 0.04, RET["y0"] + 0.05, TOP - 0.045, TOP - 0.035, led)
# three ALEX units (36 x 58 x 70): main run's outer end, return at the corner side and its far end
box("alex_1", -RX + 0.01, -RX + 0.59, MAIN["y0"] + 0.01, MAIN["y0"] + 0.37, 0, 0.70, W)
box("alex_2", RET["x0"] + 0.02, RET["x0"] + 0.38, RY - 0.59, RY - 0.01, 0, 0.70, W)
box("alex_3", RET["x1"] - 0.38, RET["x1"] - 0.02, RY - 0.59, RY - 0.01, 0, 0.70, W)
for k, (x0, x1, y0, y1, face) in enumerate(((-RX + 0.59, -RX + 0.595, MAIN["y0"] + 0.03, MAIN["y0"] + 0.35, "x"),
                                            (RET["x0"] + 0.04, RET["x0"] + 0.36, RY - 0.595, RY - 0.59, "y"),
                                            (RET["x1"] - 0.36, RET["x1"] - 0.04, RY - 0.595, RY - 0.59, "y"))):
    for j in range(5):
        z = 0.07 + j * 0.14
        box(f"pull_{k}_{j}", x0, x1, y0, y1, z - 0.004, z + 0.004, mat("#b8b8b4"))

# --- the screens on the main run, against the left wall, facing the room (+x)
YM = 1.12                                                   # the stack's centre line
cyl("pole", -RX + 0.06, YM, TOP, 1.75, 0.02, W)
box("ultrawide", -RX + 0.18, -RX + 0.24, YM - 0.407, YM + 0.407, 0.86, 1.224, BLK)
box("ultrawide_glow", -RX + 0.241, -RX + 0.242, YM - 0.39, YM + 0.39, 0.87, 1.21, SCR)
box("studio_display", -RX + 0.16, -RX + 0.19, YM - 0.31, YM + 0.31, 1.26, 1.62, ALU)
box("studio_display_glow", -RX + 0.191, -RX + 0.192, YM - 0.29, YM + 0.29, 1.28, 1.60, mat("#0e2a4a", emit="#2c6fc4", strength=2))
box("screenbar", -RX + 0.17, -RX + 0.24, YM - 0.25, YM + 0.25, 1.226, 1.25, BLK)
# the speakers raised beside the top screen, on desk poles, as in the photo
for s in (-1, 1):
    y = YM + s * 0.46
    cyl(f"spk_pole_{s}", -RX + 0.14, y, TOP, 1.22, 0.015, W)
    box(f"a7v_{s}", -RX + 0.03, -RX + 0.31, y - 0.10, y + 0.10, 1.22, 1.557, W)
    cyl(f"a7v_woofer_{s}", -RX + 0.315, y, 1.26, 1.262, 0.06, BLK).rotation_euler = (0, math.radians(90), 0)
    box(f"a7v_tweeter_{s}", -RX + 0.31, -RX + 0.315, y - 0.03, y + 0.03, 1.44, 1.50, BLK)
# key lights on tall desk poles at the main run's two ends
for k, y in enumerate((MAIN["y0"] + 0.10, RET["y0"] + 0.05)):
    cyl(f"kl_pole_{k}", -RX + 0.70, y, TOP, 1.62, 0.0125, BLK)
    box(f"key_light_{k}", -RX + 0.66, -RX + 0.695, y - 0.175, y + 0.175, 1.55, 1.80, mat("#ffffff", emit="#ffffff", strength=6))
box("camera", -RX + 0.52, -RX + 0.64, MAIN["y0"] + 0.22, MAIN["y0"] + 0.33, 1.32, 1.39, BLK)       # on the left pole's arm
cyl("mic_arm", -RX + 0.40, MAIN["y0"] + 0.45, 1.05, 1.07, 0.01, W)
box("mic", -RX + 0.50, -RX + 0.65, MAIN["y0"] + 0.48, MAIN["y0"] + 0.55, 0.98, 1.05, W)
box("apollo", -RX + 0.30, -RX + 0.45, YM - 0.12, YM + 0.12, TOP, TOP + 0.066, ALU)
box("stream_deck", -RX + 0.32, -RX + 0.40, YM + 0.20, YM + 0.32, TOP, TOP + 0.05, W)
box("mat", -RX + 0.42, -RX + 0.72, YM - 0.40, YM + 0.40, TOP, TOP + 0.004, mat("#8d9096", 0.9))
box("keyboard", -RX + 0.47, -RX + 0.62, YM - 0.165, YM + 0.165, TOP + 0.004, TOP + 0.034, W)
box("mouse", -RX + 0.50, -RX + 0.62, YM + 0.24, YM + 0.32, TOP + 0.004, TOP + 0.05, mat("#d5d6d8"))
# shelf above, three frames, plants hanging at its ends
box("shelf", -RX, -RX + 0.25, MAIN["y0"] + 0.05, RY - 0.30, 1.86, 1.89, W)
for k, dy in enumerate((-0.38, 0.0, 0.38)):
    box(f"frame_{k}", -RX + 0.03, -RX + 0.06, YM + dy - 0.15, YM + dy + 0.15, 1.89, 2.29, BLK)
for k, y in enumerate((MAIN["y0"] + 0.12, RY - 0.40)):
    cyl(f"pot_{k}", -RX + 0.12, y, 1.89, 2.00, 0.06, W)
    cyl(f"trail_{k}", -RX + 0.12, y, 1.30, 1.89, 0.05, GREEN)
cyl("desk_plant", RET["x0"] + 0.45, RY - 0.45, TOP, TOP + 0.25, 0.05, GREEN)
# the chair at the main run, facing the screens (-x)
box("chair_seat", -1.12, -0.62, YM - 0.25, YM + 0.25, 0.44, 0.52, mat("#9a9da3", 0.6))
box("chair_back", -0.66, -0.60, YM - 0.24, YM + 0.24, 0.55, 1.08, mat("#9a9da3", 0.6))
cyl("chair_post", -0.87, YM, 0.06, 0.44, 0.025, ALU)
box("chair_base", -1.20, -0.54, YM - 0.33, YM + 0.33, 0.0, 0.06, ALU)
# --- the return: the PC in the inner corner, the laptop at the end beside the window
box("pc", RET["x0"] + 0.04, RET["x0"] + 0.52, RY - 0.36, RY - 0.06, TOP, TOP + 0.465, W)
box("pc_glass", RET["x0"] + 0.06, RET["x0"] + 0.50, RY - 0.365, RY - 0.36, TOP + 0.03, TOP + 0.44,
    mat("#cfe6ff", 0.1, emit="#9fd0ff", strength=1.5))
for k in range(3):
    cyl(f"fan_{k}", RET["x0"] + 0.50, RY - 0.21, TOP + 0.08 + k * 0.13, TOP + 0.08 + k * 0.13 + 0.002, 0.055,
        mat("#ffffff", emit="#cfe6ff", strength=4)).rotation_euler = (0, math.radians(90), 0)
box("mstand", RET["x1"] - 0.36, RET["x1"] - 0.10, RY - 0.40, RY - 0.12, TOP, TOP + 0.15, ALU)
box("laptop_base", RET["x1"] - 0.41, RET["x1"] - 0.05, RY - 0.42, RY - 0.17, TOP + 0.15, TOP + 0.166, ALU)
box("laptop_lid", RET["x1"] - 0.41, RET["x1"] - 0.05, RY - 0.17, RY - 0.155, TOP + 0.166, TOP + 0.40, ALU)
# back wall above the return: pegboard with the neon over it, triangles at the corner
box("pegboard", RET["x1"] - 0.86, RET["x1"] - 0.10, RY - 0.02, RY, 1.25, 1.81, mat("#ffffff", emit="#9fc8ff", strength=0.6))
box("headphones", RET["x1"] - 0.30, RET["x1"] - 0.12, RY - 0.08, RY - 0.02, 1.45, 1.66, W)
box("neon", RET["x1"] - 0.80, RET["x1"] - 0.16, RY - 0.015, RY, 1.95, 2.05, mat("#ffffff", emit="#f4f8ff", strength=14))
for k in range(4):
    box(f"triangle_{k}", RET["x0"] + 0.05 + (k % 2) * 0.12, RET["x0"] + 0.25 + (k % 2) * 0.12, RY - 0.01, RY,
        1.45 + k * 0.17, 1.62 + k * 0.17, mat("#ffffff", emit="#c9b8ff", strength=2))

# --- the music side (the secret): piano on the right wall, guitars over it, rack and decks
box("piano", RX - 0.62, RX - 0.02, -0.60, 0.93, 0, 1.22, BLK)
box("bench", RX - 1.15, RX - 0.80, -0.30, 0.60, 0, 0.50, BLK)
for k, (y, c) in enumerate(((0.75, "#2b2b2f"), (0.30, "#f0f0ea"), (-0.20, "#9c2b33"))):
    box(f"wall_guitar_{k}", RX - 0.12, RX - 0.07, y - 0.18, y + 0.18, 1.45, 2.50, mat(c, 0.4))
box("rack", WIN["x1"] + 0.25, WIN["x1"] + 0.75, RY - 0.55, RY - 0.05, 0, 0.95, BLK)
box("dj_table", RX - 0.70, RX - 0.10, -1.70, -1.20, 0, 0.92, BLK)
box("dj", RX - 0.66, RX - 0.14, -1.68, -1.22, 0.92, 0.98, mat("#2a2a2c", 0.5))
box("rug", -0.65, 0.95, -1.30, 0.80, 0, 0.01, mat("#6f5a4a", 0.9))
cyl("pendant", 0.15, -0.20, 2.40, 2.55, 0.20, mat("#fff4e0", emit="#fff1d6", strength=3))

# --- light and cameras
sc = bpy.context.scene
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.40, 0.50, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
sc.world = w
for nm, loc, e in (("fill", (0.2, -0.5, 2.8), 260), ("win", (0.30, RY - 0.3, 1.65), 160)):
    L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, "AREA"))
    L.data.energy, L.data.size = e, 1.6
    L.location = loc
    sc.collection.objects.link(L)
sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "AgX"


def shoot(name, pos, target, vfov, res, ortho=None):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    sc.collection.objects.link(cam)
    cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam.data.type, cam.data.ortho_scale = "ORTHO", ortho
    else:
        cam.data.sensor_fit = "VERTICAL"
        cam.data.angle = math.radians(vfov)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    bpy.data.objects["ceiling"].hide_render = bool(ortho)
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)


os.makedirs(OUT, exist_ok=True)
# the photo's angle: standing in the room, looking into the back-left corner
shoot("photo-angle", (0.85, -0.95, 1.85), (-1.50, 1.25, 1.05), 62, (900, 1100))
shoot("photo-angle-wide", (0.85, -0.95, 1.85), (-1.40, 1.30, 1.10), 55, (1600, 900))
# the intro: from the room, out of the window at the sky and the city
shoot("intro-window", (0.30, 0.60, 1.60), (0.30, 4.0, 1.85), 45, (1600, 900))
shoot("top", (0, 0, 2.6), (0, 0, 0), 0, (1100, 1050), ortho=4.9)
print("photo layout blockout done")
