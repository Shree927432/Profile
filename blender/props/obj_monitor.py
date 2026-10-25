"""obj_monitor: the posts screen, the 27-inch top screen of the AI-lab stack (the Apple Studio
Display stand-in of room plan v2: a thin aluminium body, an all-black glass front, no logo),
on a VESA arm clamped to the shared monitor pole (the pole itself is set_desk's desk_pole).

Numbers from blender/lib/plan_v2.py (SD, POSTS, XM, TOP, the pole's place). Names
(MESHES.md, obj_monitor): monitor_body (case and glass, one material: aluminium with the
black glass front by vertex colour), monitor_screen (screen rules: a flat 16:10 rectangle,
53.8 x 33.6, centred in the 16:9 glass, spanning local X and Z, facing local -Y, UVs written
upside down by geo.screen_plane), monitor_static (the arm), monitor_view and
monitor_view_target.

The root stands on the desk top under the display's front face, yaw 0 (the screen faces
straight out from the back wall), no tilt. The screen carries a generated TOP test texture
(geo.uvtest_image): the word TOP and an arrow pointing at the screen's top edge. The browser
test (/?room&glb&uvtest) shows it upright.
"""
from lib import geo, materials as M, plan_v2 as P

SD, POSTS = P.SD, P.POSTS
POLE = next(c for c in P.COMPONENTS if c["key"] == "pole")


def build():
    root, coll = geo.root("obj_monitor")
    w, h, t = SD["w"], SD["h"], SD["d"]
    root.location = (P.XM, SD["y"] - t / 2, P.TOP)
    kw = dict(collection=coll, parent=root)
    zc = SD["z"] + h / 2 - P.TOP                    # display centre above the desk top

    body_m = M.tinted("mat_monitor_body", rough=0.28)
    arm_m = M.principled("mat_monitor_arm", base="#f2f2ef", rough=0.35)
    screen_m = M.screen_image("mat_monitor_screen", geo.uvtest_image("monitor_uvtest", 1024, 640))

    # body: a rounded rectangle extruded back; the whole front is black glass
    body = geo.prism("monitor_body", geo.rounded_rect(w, h, 0.012, n=5, cy=zc), "Y", 0.0, t,
                     material=body_m, smooth=False, **kw)
    geo.tint_faces(body, "#08090b", 0.0, lambda p: p.normal.y < -0.9, rest=(*M.srgb("#c9ccd1"), 1.0))
    geo.bevel(body, 0.0025, segments=3)

    screen = geo.screen_plane("monitor_screen", POSTS["w"], POSTS["h"], (0.0, -0.0008, zc), material=screen_m, **kw)

    # VESA arm from the display's back to a collar on the pole
    pole_y = POLE["at"][1] - root.location.y
    pr = POLE["size"][0] / 2
    arm = geo.boxes("monitor_static", [(-0.05, 0.05, t, t + 0.012, zc - 0.05, zc + 0.05),     # VESA plate
                                       (-0.02, 0.02, t + 0.012, pole_y, zc - 0.015, zc + 0.015)],
                    material=arm_m, **kw)
    collar = geo.cylinder("monitor_collar", pr + 0.008, (0, pole_y, zc - 0.03), (0, pole_y, zc + 0.03), segments=20,
                          material=arm_m, **kw)
    arm = geo.join([arm, collar], "monitor_static")

    geo.empty("monitor_view", (0.0, -0.80, zc + 0.04), coll, parent=root)
    geo.empty("monitor_view_target", (0.0, 0.0, zc), coll, parent=root)
    return root, {"monitor_body": body, "monitor_screen": screen, "monitor_static": arm}
