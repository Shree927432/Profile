"""obj_rig: the training rig, the tenth interactive object (owner, 2026-10-23): the PC on the
desk's return and the 34-inch dashboard screen under the posts screen. Stand-ins only in this
step (room shell v2): the right sizes, places, colours and finishes from blender/lib/plan_v2.py,
with the names MESHES.md lists, so the name check passes; the detailed models and the room
code come in obj_rig's own step.

Names (MESHES.md, obj_rig): rig_case (the case: a white frame, open where the glass will be,
front and the side towards the room view), rig_gpu (the card seen through the side glass),
rig_fans (the fan rings, one glowing mesh), rig_display (the 34-inch screen's body),
rig_screen (the dashboard, screen rules, 21:9, flat in this step, a plain placeholder picture), rig_static (the screen's arm
on the pole, the case's inside), rig_view and rig_view_target.

The root stands on the desk top under the 34-inch's front face, yaw 0. The case stands on the
return turned 90 degrees (its front towards the chair, its side glass towards the hero
camera); that turn is on the case's and the card's rotation (MESHES.md section 1). No logos.
"""
import math

from mathutils import Matrix, Vector

from lib import geo, materials as M, plan_v2 as P

UW = P.UW
COMP = {c["key"]: c for c in P.COMPONENTS}


def placeholder(w=256, h=108):
    """The dashboard until obj_rig's own step paints it: dark navy, a faint grid, no words. Its own
    step brings a TOP test for this screen (the UVs follow the same rule as monitor_screen)."""
    import bpy
    import numpy as np
    img = bpy.data.images.get("rig_placeholder") or bpy.data.images.new("rig_placeholder", w, h)
    px = np.zeros((h, w, 4), dtype=np.float32)
    px[...] = (0.012, 0.025, 0.055, 1.0)
    px[::18, :, :3] = px[:, ::32, :3] = (0.03, 0.06, 0.12)
    img.pixels.foreach_set(np.ascontiguousarray(px).ravel())
    img.pack()
    return img


def build():
    root, coll = geo.root("obj_rig")
    root.location = (P.XM, UW["y"] - UW["d"] / 2, P.TOP)
    kw = dict(collection=coll, parent=root)
    o = Vector(root.location)
    white = M.principled("mat_rig_white", base="#f2f2ef", rough=0.3, coat=0.2, coat_rough=0.15)
    dark = M.principled("mat_rig_dark", base="#26272b", rough=0.5)
    black = M.principled("mat_rig_display", base="#1b1b1d", rough=0.4)
    gpu_m = M.principled("mat_rig_gpu", base="#2c2d30", metal=0.7, rough=0.32)
    fan_m = M.principled("mat_rig_fans", base="#bfe4ff", emit="#9fd0ff", emit_strength=3.0)
    screen_m = M.screen_image("mat_rig_screen", placeholder())
    parts = {}

    # --- the 34-inch: a thin panel with a rear housing, flat in this step
    w, h = UW["w"], UW["h"]
    zc = UW["z"] + h / 2 - P.TOP
    panel = geo.prism("rig_display", geo.rounded_rect(w, h, 0.008, n=4, cy=zc), "Y", 0.0, 0.022,
                      material=black, smooth=False, **kw)
    housing = geo.boxes("rig_display_housing", [(-0.22, 0.22, 0.022, 0.07, zc - 0.13, zc + 0.10)], material=black, **kw)
    geo.bevel(housing, 0.01, segments=2)
    parts["rig_display"] = geo.join([panel, housing], "rig_display")
    aw, ah = P.UW_ACTIVE
    parts["rig_screen"] = geo.screen_plane("rig_screen", aw, ah, (0.0, -0.0008, zc), material=screen_m, **kw)

    # --- the case, built in its own frame (front at -Y, bottom centre at the origin), then turned
    pc = COMP["pc"]
    cw, cd, ch = pc["size"]
    t = 0.018
    case = geo.boxes("rig_case", [
        (-cw / 2, cw / 2, -cd / 2, cd / 2, 0.0, 0.035),                  # base with its feet line
        (-cw / 2, cw / 2, -cd / 2, cd / 2, ch - t, ch),                   # top
        (-cw / 2, cw / 2, cd / 2 - t, cd / 2, 0.0, ch),                   # back
        (cw / 2 - t, cw / 2, -cd / 2, cd / 2, 0.0, ch),                   # the board side (glass on the other two)
    ], material=white, **kw)
    geo.bevel(case, 0.004, segments=2)
    tray = geo.boxes("rig_tray", [(cw / 2 - t - 0.006, cw / 2 - t, -cd / 2 + 0.03, cd / 2 - 0.03, 0.06, ch - 0.03)],
                     material=dark, **kw)
    fans, hubs = [], []
    for k in range(3):                                                   # three bottom intakes, three at the back
        y = -cd / 2 + 0.09 + k * 0.13
        fans.append((0.056, (-0.02, y, 0.036), (-0.02, y, 0.040)))
        hubs.append((0.02, (-0.02, y, 0.040), (-0.02, y, 0.043)))
        z = 0.11 + k * 0.13
        fans.append((0.056, (-0.02, cd / 2 - t - 0.004, z), (-0.02, cd / 2 - t, z)))
        hubs.append((0.02, (-0.02, cd / 2 - t - 0.007, z), (-0.02, cd / 2 - t - 0.004, z)))
    fan = geo.cylinders("rig_fans", fans, segments=24, material=fan_m, **kw)
    hub = geo.cylinders("rig_fan_hubs", hubs, segments=12, material=dark, **kw)
    gl = (cw / 2 - t - 0.035 - 0.137 / 2, -0.02, 0.21)                   # the card, plugged into the board side
    gpu = geo.rounded_box("rig_gpu", 0.137, 0.304, 0.040, 0.004, material=gpu_m, **kw)
    gpu.data.transform(Matrix.Translation((0, 0, -0.020)))             # origin at the card's centre

    world = Matrix.Translation(pc["at"]) @ Matrix.Rotation(math.radians(pc["yaw"]), 4, "Z")
    to_root = Matrix.Translation(-o) @ world
    for part in (case, tray, fan, hub):
        part.matrix_basis = to_root
    gpu.matrix_basis = to_root @ Matrix.Translation(gl)
    parts.update(rig_case=case, rig_gpu=gpu, rig_fans=fan)

    # --- rig_static: the screen's arm to the pole, the case's board tray, the fan hubs
    pole = COMP["pole"]
    pole_y = pole["at"][1] - o.y
    pr = pole["size"][0] / 2
    arm = geo.boxes("rig_static", [(-0.05, 0.05, 0.07, 0.082, zc - 0.05, zc + 0.05),
                                   (-0.02, 0.02, 0.082, pole_y, zc - 0.015, zc + 0.015)], material=white, **kw)
    collar = geo.cylinder("rig_collar", pr + 0.008, (0, pole_y, zc - 0.03), (0, pole_y, zc + 0.03), segments=20,
                          material=white, **kw)
    parts["rig_static"] = geo.join([arm, collar, tray, hub], "rig_static")

    geo.empty("rig_view", (0.0, -0.85, zc + 0.03), coll, parent=root)
    geo.empty("rig_view_target", (0.0, 0.0, zc), coll, parent=root)
    return root, parts
