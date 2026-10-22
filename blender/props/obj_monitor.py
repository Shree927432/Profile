"""obj_monitor: the desk monitor that shows the posts. Thin aluminium frame with a black
glass front on a slim stand bent from one aluminium plate (the owner's pick, option A
of docs/moodboard/local/desk-references.png), at our 16:10 screen.

Names (MESHES.md, obj_monitor): monitor_body (case and bezel, one material: aluminium
with the black glass front by vertex colour), monitor_screen (screen rules: a flat
16:10 rectangle spanning local X and Z, facing local -Y, UVs written upside down by
geo.screen_plane), monitor_static (the stand), monitor_view and monitor_view_target.

The root stands on the desk top under the display's front face. The display leans back
LAYOUT["monitor"]["tilt"] degrees about the hinge where the stand meets its back; the
tilt is on the parts' rotation, never in their geometry (MESHES.md section 1). Yaw 0:
the screen faces straight out from the back wall.

The screen carries a generated TOP test texture (top_image()): the word TOP and an arrow
pointing at the screen's top edge. The browser test (/?room&glb&uvtest) shows it upright.
"""
import math

import bpy
from mathutils import Matrix, Vector

from lib import constants as C, geo, materials as M

MON = C.LAYOUT["monitor"]
DESK = C.LAYOUT["desk"]


def top_image(w=1024, h=640):
    """TOP and an up arrow on dark slate, with a red corner mark at the top left.
    Row 0 of the array is the top of the picture. Blender's row 0 is V = 0, and the
    screen helper puts V = 0 on the plane's top edge, so it goes in unflipped (as the
    piano's sheet music does). Opened in an image viewer the PNG looks upside down; on
    the screen it is upright, in Blender and, through the exporter's V flip, in three.js."""
    import numpy as np
    img = bpy.data.images.get("monitor_uvtest") or bpy.data.images.new("monitor_uvtest", w, h)
    px = np.zeros((h, w, 4), dtype=np.float32)
    px[...] = (0.10, 0.14, 0.20, 1.0)
    ink = (0.95, 0.95, 0.92)
    px[:10, :, :3] = px[-10:, :, :3] = px[:, :10, :3] = px[:, -10:, :3] = ink   # border
    px[16:96, 16:96, :3] = (0.85, 0.18, 0.14)                                     # top-left mark
    glyphs = {
        "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
        "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
        "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    }
    cell, gap = 34, 2
    text_w = 3 * 5 * cell + 2 * cell
    x = (w - text_w) // 2
    y0 = 70
    for ch in "TOP":
        for r, row in enumerate(glyphs[ch]):
            for c, on in enumerate(row):
                if on == "#":
                    px[y0 + r * cell + gap: y0 + (r + 1) * cell - gap,
                       x + c * cell + gap: x + (c + 1) * cell - gap, :3] = ink
        x += 6 * cell
    # arrow under the word, pointing up at the top edge
    cx, tip, base, bottom = w // 2, y0 + 7 * cell + 40, y0 + 7 * cell + 150, h - 50
    for yy in range(tip, base):
        half = int((yy - tip) * 0.9)
        px[yy, cx - half: cx + half + 1, :3] = (0.45, 0.80, 1.0)
    px[base:bottom, cx - 30: cx + 30, :3] = (0.45, 0.80, 1.0)
    img.pixels.foreach_set(np.ascontiguousarray(px).ravel())
    img.pack()
    return img


def stand_profile(zc, t):
    """Side view (y, z) of the stand: the foot plate, a bend, the arm leaning forward to the
    hinge at the display's back. One plate of thickness plate_t, as a closed polygon."""
    pt = MON["plate_t"]
    fy0, fy1 = -0.03, -0.03 + MON["foot_d"]
    hinge = Vector((t + pt / 2 + 0.001, zc))
    bend_r = 0.03
    # centreline: foot (front to back), quarter-ish bend, arm to the hinge
    arm_dir = (hinge - Vector((fy1, bend_r))).normalized()
    pts = [Vector((fy0, pt / 2)), Vector((fy1 - bend_r, pt / 2))]
    c = Vector((fy1 - bend_r, bend_r + pt / 2))
    a_end = math.atan2(arm_dir.y, arm_dir.x) - math.pi / 2       # normal angle at the arm
    for i in range(1, 9):
        a = -math.pi / 2 + (a_end + math.pi / 2) * i / 8
        pts.append(c + Vector((math.cos(a), math.sin(a))) * bend_r)
    pts.append(hinge)
    # offset the centreline both ways by half the plate
    left, right = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        d = (b - a).normalized()
        n = Vector((-d.y, d.x))
        left.append(p + n * pt / 2)
        right.append(p - n * pt / 2)
    return [tuple(v) for v in left + list(reversed(right))]


def build():
    root, coll = geo.root("obj_monitor")
    root.location = (MON["x"], MON["y"], DESK["h"])
    kw = dict(collection=coll, parent=root)
    w, h, t = MON["w"], MON["h"], MON["t"]
    zc = MON["z"] - DESK["h"]                       # body centre above the desk top
    sw = MON["screen_w"]
    sh = sw / 1.6                                   # 16:10

    body_m = M.tinted("mat_monitor_body", rough=0.28)
    alu = M.principled("mat_monitor_alu", base="#c9ccd1", metal=1.0, rough=0.3)
    screen_m = M.screen_image("mat_monitor_screen", top_image())

    # body: rounded rectangle front, extruded back; front face is black glass
    body = geo.prism("monitor_body", geo.rounded_rect(w, h, 0.012, n=5, cy=zc), "Y", 0.0, t,
                     material=body_m, smooth=False, **kw)
    geo.tint_faces(body, "#08090b", 0.0, lambda p: p.normal.y < -0.9, rest=(*M.srgb("#c9ccd1"), 1.0))
    geo.bevel(body, 0.0025, segments=3)

    screen = geo.screen_plane("monitor_screen", sw, sh, (0.0, -0.0008, zc), material=screen_m, **kw)

    stand = geo.prism("monitor_static", stand_profile(zc, t), "X", -MON["arm_w"] / 2, MON["arm_w"] / 2,
                      material=alu, **kw)
    geo.bevel(stand, 0.0015, segments=2)

    # lean back about the hinge: rotation on the parts, geometry stays flat
    hinge = Vector((0.0, t, zc))
    tilt = math.radians(-MON["tilt"])               # negative about +X: the top goes back (MESHES.md)
    rot = Matrix.Rotation(tilt, 4, "X")
    for o in (body, screen):
        if o is body:
            geo.set_origin(o, (0.0, t / 2, zc))
        mw = Matrix.Translation(hinge) @ rot @ Matrix.Translation(-hinge) @ Matrix.Translation(o.location)
        o.location = mw.to_translation()
        o.rotation_euler = (tilt, 0.0, 0.0)

    geo.empty("monitor_view", (0.0, -0.80, zc + 0.04), coll, parent=root)
    geo.empty("monitor_view_target", (0.0, 0.0, zc), coll, parent=root)
    return root, {"monitor_body": body, "monitor_screen": screen, "monitor_static": stand}
