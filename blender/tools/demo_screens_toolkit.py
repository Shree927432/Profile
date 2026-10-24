"""Proof of the component toolkit on the approved screens component (read only: nothing in
blender/components/ is changed). One command, headless, EEVEE and Workbench only (no Cycles):

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/tools/demo_screens_toolkit.py -- [stages]

stages (default all): parts, outline, compare, backdrop, lens
  parts     every parts.py builder on one sheet (EEVEE)
  outline   tools/outline_check.py on a ROUGH screens built from parts.py in a few lines (the 15-minute
            outline), against the same photos
  compare   lib/compare.py's test on the approved screens (screens.build()): G8 front, back and top
            (g8-05), Studio Display front; the stacked photo-vs-model sheet with the top row; the
            numbers next to the screens' own report
  backdrop  backdrops.py: the Studio Display front photo and the G8 top photo placed at true scale
            behind the model, rendered through their orthographic cameras (the tracing view)
  lens      refs.py: lens correction, before and after on a straight edge (runs in plain Python)

Plain Python runs the lens stage only:  /opt/anaconda3/bin/python3 blender/tools/demo_screens_toolkit.py lens
Output: video-local/footage/2026-10-24-toolkit/ (NOTE.md there).
"""
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(BLENDER_DIR, ".."))
sys.path.insert(0, BLENDER_DIR)
sys.path.insert(0, os.path.join(BLENDER_DIR, "components"))
sys.path.insert(0, HERE)
OUT = os.path.join(REPO, "video-local", "footage", "2026-10-24-toolkit")
REF = os.path.join(REPO, "docs", "moodboard", "local")
SCREENS_REPORT = os.path.join(REPO, "video-local", "footage", "2026-10-24-components", "screens", "screens-report.json")

try:
    import bpy
except ImportError:
    bpy = None


def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {msg}", flush=True)


# ---------------------------------------------------------------------------
# the four views (shared by the outline check and the full compare)
# ---------------------------------------------------------------------------
def panel_only(m):
    """Rows down to the G8 panel's bottom edge (where the silhouette narrows to the stand): the camera is
    fitted on the panel alone, as screens did."""
    import numpy as np
    w = m.sum(1)
    if w.max() == 0:
        return m
    rows = np.nonzero(w > 0.6 * w.max())[0]
    out = m.copy()
    out[rows.max() + 1:] = False
    return out


def views(names, prepare_g8=None, sd_ref=None, top_ref=None):
    """names: dict role -> object names (g8, g8_stand, sd)."""
    g8 = names["g8"] + names["g8_stand"]
    v = [
        dict(name="g8-front", title="Samsung G8: front (Samsung dimension drawing) vs our model",
             photo=os.path.join(REF, "ai-lab", "02-main-screen", "dimensions-official-samsung-au.png"), mask=0.92,
             crop=(548, 1295, 585, 1075), objects=g8, prepare=prepare_g8, fit_mask=panel_only,
             camera={"mode": "fit", "view": "front"}),
        dict(name="g8-back", title="Samsung G8: back (Samsung photo g8-02) vs our model",
             photo=os.path.join(REF, "odyssey-g8-samsung", "g8-02.png"), mask="alpha", objects=g8, prepare=prepare_g8,
             fit_mask=panel_only, camera={"mode": "fit", "view": "back"}),
        dict(name="g8-top", title="Samsung G8: top (Samsung photo g8-05) vs our model",
             photo=os.path.join(REF, "odyssey-g8-samsung", "g8-05.png"), mask="alpha", objects=g8, prepare=prepare_g8,
             camera={"mode": "placed", "ref": top_ref} if top_ref else
             {"mode": "fit", "view": "top", "tilts": [-12, -6, 0, 6, 12]}),
        dict(name="sd-front", title="Apple Studio Display: front (Apple photo, screen off) vs our model",
             photo=os.path.join(REF, "ai-lab", "03-top-screen", "front-screen-off.jpg"), mask=0.8,
             crop=(0, 9999, 0, 1426), objects=names["sd"],
             camera={"mode": "placed", "ref": sd_ref} if sd_ref else {"mode": "ortho", "view": "front"}),
    ]
    return v


def sd_front_ref(model_bottom_z_mm, width_mm=623.0):
    """The Studio Display photo at true scale: mm per pixel from Apple's official 623 mm width and the
    photo's silhouette; anchored at its bottom-centre to the model's panel bottom."""
    from lib import refs
    p = os.path.join(REF, "ai-lab", "03-top-screen", "front-screen-off.jpg")
    m = refs.fill_holes(refs.mask(refs.load(p), 0.8, (0, 9999, 0, 1426)))
    s = refs.mm_per_px_extent(m, width_mm, "x")
    return refs.ref_record(p, s, refs.anchor_of(m, "bottom-centre"), (0.0, model_bottom_z_mm), view="front",
                           note=f"scale from the official {width_mm} mm width")


TOP_EXPLAIN = ("first score for this view (screens has none). Samsung's top shot is a perspective view from "
               "above the front; ours is orthographic at true scale. A thin arc makes IoU harsh. The width is right "
               "(size ratio about 0.99); the differences are in the shell's top outline: for the screens builder")


def g8_top_ref(width_mm=813.6):
    """The G8 top photo (g8-05) at true scale from the official 813.6 mm chord; anchored at its
    bottom-centre (the front of the curved edges) to the model's edge line, y = -sag."""
    from lib import refs
    import screens as S
    p = os.path.join(REF, "odyssey-g8-samsung", "g8-05.png")
    m = refs.mask(refs.load(p), "alpha")
    s = refs.mm_per_px_extent(m, width_mm, "x")
    x0, x1, y0, y1 = refs.bbox(m)
    # the edges' tips are the lowest (front-most) pixels at the far left and right of the arc
    return refs.ref_record(p, s, ((x0 + x1 + 1) / 2, y1 + 1), (0.0, -S.G8_SAG * 1000), view="top",
                           note="scale from the official 813.6 mm chord")


# ---------------------------------------------------------------------------
# scene helpers
# ---------------------------------------------------------------------------
def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves, bpy.data.cameras,
                   bpy.data.lights):
        for b in list(blocks):
            if b.users == 0:
                blocks.remove(b)
    sc = bpy.context.scene
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    return sc


def eevee(sc, w, h, samples=32):
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.eevee.taa_render_samples = samples
    sc.view_settings.view_transform = "AgX"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.film_transparent = False


# ---------------------------------------------------------------------------
# parts sheet
# ---------------------------------------------------------------------------
def stage_parts():
    from lib import parts as P, compare
    from mathutils import Vector
    sc = clear()
    t0 = time.time()
    cell = 0.16
    made = []
    timings = {}

    def at(c, r, dx=0.0, dz=0.0):
        return (c * cell + dx, 0.0, -r * cell + dz)

    def label(text, c, r):
        cu = bpy.data.curves.new("lbl_" + text, "FONT")
        cu.body = text
        cu.size = 0.011
        cu.align_x = "CENTER"
        o = bpy.data.objects.new("lbl_" + text[:20].replace(" ", "_"), cu)
        sc.collection.objects.link(o)
        o.location = (c * cell, -0.03, -r * cell - 0.068)
        o.rotation_euler = (math.radians(90), 0, 0)
        o.data.materials.append(bpy.data.materials.get("mat_part_black") or P.palette()["black"])

    def backing(c, r, w=0.13, h=0.12, name=None):
        return P.rounded_panel(name or f"sheet_back_{c}_{r}", w, h, 0.006, r_corner=0.006, r_front=0.001,
                               mats={"body": P.palette()["white"]}, at=(c * cell, 0.006, -r * cell))

    def timed(key, fn):
        t = time.time()
        o = fn()
        timings[key] = round((time.time() - t) * 1000)
        made.append(key)
        return o
    # row 0: bodies and knobs
    timed("rounded_box", lambda: P.rounded_box("p_rounded_box", 0.09, 0.05, 0.045, r_side=0.012, r_top=0.006,
                                                r_bottom=0.0015, at=at(0, 0, dz=-0.03)))
    label("rounded_box", 0, 0)
    timed("rounded_panel", lambda: P.rounded_panel("p_rounded_panel", 0.10, 0.075, 0.01, r_corner=0.012,
                                                    r_front=0.003, r_back=0.001, at=at(1, 0)))
    label("rounded_panel", 1, 0)
    backing(2, 0)
    timed("knob plain", lambda: P.knob("p_knob_plain", 0.014, 0.016, at=at(2, 0, dx=-0.035, dz=0.0)))
    timed("knob knurled", lambda: P.knob("p_knob_knurl", 0.012, 0.018, knurl=True, indicator=True,
                                          at=at(2, 0, dx=0.0)))
    timed("knob skirt", lambda: P.knob("p_knob_skirt", 0.009, 0.014, indicator=True, skirt=(0.015, 0.003),
                                        mats={"knob": P.palette()["black"], "skirt": P.palette()["alu"]},
                                        at=at(2, 0, dx=0.038)))
    label("knob: plain, knurled, skirt", 2, 0)
    backing(3, 0)
    timed("push_button", lambda: P.push_button("p_button_round", d=0.014, at=at(3, 0, dx=-0.03),
                                                mats={"cap": P.palette()["alu"], "bezel": P.palette()["black"]}))
    P.push_button("p_button_square", size=(0.022, 0.012), r_corner=0.002, at=at(3, 0, dx=0.025),
                  mats={"cap": P.palette()["black"], "bezel": P.palette()["alu"]})
    label("push_button: round, square", 3, 0)
    backing(4, 0)
    for i, k in enumerate(("phillips", "hex", "hexbolt", "flat")):
        timed("screw " + k, lambda k=k, i=i: P.screw(f"p_screw_{k}", k, d=0.012,
                                                     mats={"screw": P.palette()["steel"]},
                                                     at=at(4, 0, dx=-0.045 + i * 0.03)))
    label("screw: phillips, hex, bolt, flat", 4, 0)
    # row 1: ports
    kinds = list(P.PORTS)
    for i, k in enumerate(kinds):
        c = 0 if i < 5 else 1
        j = i if i < 5 else i - 5
        if j == 0:
            P.rounded_panel(f"sheet_ports_{c}", 0.14, 0.12, 0.006, r_corner=0.004, at=at(c, 1, dx=0.0))
        cols = 2
        dx = -0.035 + (j % cols) * 0.07
        dz = 0.035 - (j // cols) * 0.035
        timed("port " + k, lambda k=k, dx=dx, dz=dz, c=c: P.port(f"p_port_{k}", k, at=at(c, 1, dx=dx, dz=dz)))
    label("port, decal: usb_a usb_c hdmi dp 3.5", 0, 1)
    label("port, decal: 6.35 xlr iec dc", 1, 1)
    # cut mode: a real hole in an aluminium panel
    pan = P.rounded_panel("sheet_cut_panel", 0.13, 0.12, 0.008, r_corner=0.006, r_front=0.0008, at=at(2, 1))
    for k, dx in (("usb_c", -0.035), ("hdmi", 0.025)):
        ctr = P.port_cutter(f"p_cut_{k}", k, at=at(2, 1, dx=dx))
        P.cut(pan, ctr)
        timed("port cut " + k, lambda k=k, dx=dx: P.port(f"p_portcut_{k}", k, mode="cut", at=at(2, 1, dx=dx)))
    ctr = P.port_cutter("p_cut_xlr", "xlr_combo", at=at(2, 1, dz=-0.03))
    P.cut(pan, ctr)
    P.port("p_portcut_xlr", "xlr_combo", mode="cut", at=at(2, 1, dz=-0.03))
    label("port, cut: usb_c hdmi xlr", 2, 1)
    timed("grille holes", lambda: P.grille("p_grille_holes", 0.12, 0.10, hole_d=0.0035, pitch=0.005,
                                            pattern="hex", hole_segments=8, at=at(3, 1)))
    label("grille, real holes", 3, 1)
    timed("grille texture", lambda: P.grille("p_grille_tex", 0.12, 0.10, hole_d=0.0035, pitch=0.005, mode="texture",
                                              r_corner=0.008, holes="alpha", at=at(4, 1)))
    backing(4, 1, w=0.10, h=0.08, name="sheet_behind_tex")
    bpy.data.objects["sheet_behind_tex"].location.y = 0.03
    bpy.data.objects["sheet_behind_tex"].data.materials[0] = P.palette()["accent"]
    label("grille, texture tile", 4, 1)
    # row 2: driver, VESA, tube/pole/clamp
    baf = P.rounded_panel("sheet_baffle", 0.14, 0.13, 0.012, r_corner=0.008, r_front=0.002,
                          mats={"body": P.palette()["black"]}, at=at(0, 2))
    ctr = P.driver_cutter("p_driver_cut", 0.11, at=at(0, 2))
    P.cut(baf, ctr)
    timed("driver", lambda: P.driver("p_driver", 0.11, at=at(0, 2), mats={"ring": P.palette()["alu"]}))
    label("driver, in a cut baffle", 0, 2)
    timed("vesa_plate", lambda: P.vesa_plate("p_vesa", 100, facing="-Y", at=at(1, 2)))
    backing(1, 2, w=0.14, h=0.135, name="sheet_behind_vesa")
    bpy.data.objects["sheet_behind_vesa"].data.materials[0] = P.palette()["alu"]
    label("vesa_plate 100 (+75 holes)", 1, 2)
    timed("tube", lambda: P.tube("p_tube", 0.01, 0.11, wall=0.0015, facing="+X", at=at(2, 2, dx=-0.055, dz=0.03)))
    P.tube("p_rod", 0.006, 0.11, facing="+X", key="chrome", at=at(2, 2, dx=-0.055, dz=-0.0))
    label("tube, rod, cable", 2, 2)
    cx, cz = 3 * cell, -2 * cell + 0.0
    P.rounded_box("sheet_desk", 0.14, 0.10, 0.03, r_top=0.001, at=(cx, -0.005, cz - 0.03),
                  mats={"body": P.palette()["oak"] if "oak" in P.palette() else P.palette()["alu"]})
    timed("desk_clamp", lambda: P.desk_clamp("p_clamp", at=(cx, 0.0, cz), mats={"white": P.palette()["white"]}))
    timed("pole", lambda: P.pole("p_pole", h=0.10, at=(cx, 0.0, cz + 0.024)))
    label("pole, desk_clamp", 3, 2)
    slab = P.rounded_box("sheet_slab", 0.10, 0.07, 0.015, r_side=0.004, r_top=0.002, r_bottom=0.002,
                         mats={"body": P.palette()["alu"]})
    timed("rubber_feet", lambda: P.rubber_feet("p_feet", [(-0.04, -0.025), (0.04, -0.025), (-0.04, 0.025),
                                                           (0.04, 0.025)], d=0.012, h=0.004, z=0.0, parent=slab))
    slab.location = at(4, 2, dz=0.01)
    slab.rotation_euler = (math.radians(-110), 0, 0)
    label("rubber_feet (slab tipped up)", 4, 2)
    # topology check: open edges and non-manifold edges per part (decals are open on purpose)
    import bmesh
    topo = {}
    for o in bpy.data.objects:
        if o.name.startswith("p_") and o.type == "MESH" and o.data.polygons:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            topo[o.name] = {"faces": len(bm.faces), "quads_pct": round(100 * sum(len(f.verts) == 4 for f in bm.faces) / len(bm.faces)),
                            "open_edges": sum(e.is_boundary for e in bm.edges),
                            "non_manifold": sum((not e.is_manifold) and not e.is_boundary for e in bm.edges)}
            bm.free()
    pts = P.sag_points((-0.06, -0.02, 0.02), (0.06, -0.02, 0.0), 0.03, n=5)
    timed("cable", lambda: P.cable("p_cable", [(x + 2 * cell, y, z - 2 * cell) for x, y, z in pts], r=0.003))
    build_s = round(time.time() - t0, 2)
    # count triangles per builder object
    tris = {}
    for o in bpy.data.objects:
        if o.name.startswith("p_") and o.type == "MESH":
            me = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
            me.calc_loop_triangles()
            tris[o.name] = len(me.loop_triangles)
    # look
    compare.ensure_studio(1.1)
    w = bpy.context.scene.world
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.78, 0.78, 0.8, 1)
    from lib import backdrops
    cam = backdrops.view_camera("front", (2 * cell, 0, -1.05 * cell), 5 * cell + 0.02, aspect=16 / 10,
                                ortho=False, lens=85, name="sheet_cam")
    # a little from above and the left so the depth reads
    from mathutils import Matrix
    piv = Vector((2 * cell, 0, -1.05 * cell))
    cam.matrix_world = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(-14), 4, "Z") @ \
        Matrix.Rotation(math.radians(12), 4, "X") @ Matrix.Translation(-piv) @ cam.matrix_world
    sc.camera = cam
    eevee(sc, 2400, 1500, 48)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "parts-sheet.png")
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    rs = round(time.time() - t, 1)
    closeups = []
    for k, (c0, r0, wdt) in {"ports": (0.5, 1, 0.33), "cut-grille": (2.5, 1, 0.33), "knobs": (2.5, 0, 0.33)}.items():
        piv = Vector((c0 * cell, 0, -r0 * cell))
        cam2 = backdrops.view_camera("front", piv, wdt, aspect=16 / 9, ortho=False, lens=85, name="sheet_cam_" + k)
        cam2.matrix_world = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(-16), 4, "Z") @ \
            Matrix.Rotation(math.radians(12), 4, "X") @ Matrix.Translation(-piv) @ cam2.matrix_world
        sc.camera = cam2
        eevee(sc, 1920, 1080, 48)
        p2 = os.path.join(OUT, f"parts-closeup-{k}.png")
        sc.render.filepath = p2
        bpy.ops.render.render(write_still=True)
        closeups.append(p2)
    path2 = closeups
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, "out", "toolkit-parts.blend"), compress=True)
    info = {"builders": made, "build_s": build_s, "build_ms": timings, "triangles": tris, "topology": topo, "render_s": rs,
            "sheet": path, "closeup": path2}
    log(f"parts: {len(made)} parts built in {build_s} s, sheet rendered in {rs} s: {path}")
    return info


# ---------------------------------------------------------------------------
# lens (plain Python or Blender)
# ---------------------------------------------------------------------------
LENS_LINES = {
    # edges that are straight in the room, marked roughly (pixels) on the owner's desk photo; search 6 px
    "shelf": ((80, 250), (455, 295)),
    "drawer_left": ((100, 660), (118, 840)),
    "desk_right": ((640, 590), (730, 622)),
    "window": ((668, 160), (656, 520)),
    "carpet_drawer": ((235, 845), (122, 857)),
}


def stage_lens():
    """refs.py on two photos. (1) A known answer: Apple's front photo of the Studio Display (a perfectly
    straight black rectangle across most of the frame) given a phone-like barrel distortion with
    k1 = +0.06, then refs recovers k1 from the four screen edges alone and undistorts it.
    (2) The owner's desk photo (ai-desk-reference-2.jpg, a wide shot): k1 fitted from five room edges."""
    import numpy as np
    from lib import refs
    os.makedirs(os.path.join(OUT, "lens"), exist_ok=True)
    res = {}
    # (1) known answer
    src = os.path.join(REF, "ai-lab", "03-top-screen", "front-screen-off.jpg")
    img = refs.load(src)
    H, W = img.shape[:2]
    small = img[::2, ::2]
    pad = 110                               # a white page round it: the photo is cropped at the screen's top
    page = np.ones((small.shape[0] + 2 * pad, small.shape[1] + 2 * pad, 4), np.float32)
    page[pad:-pad, pad:-pad] = small
    small = page
    truth = refs.lens_model(small.shape, k1=0.06)
    # distorting = sampling the straight photo at the undistorted positions of the distorted pixels
    yy, xx = np.mgrid[0:small.shape[0], 0:small.shape[1]].astype(float)
    pd = np.stack([xx + 0.5, yy + 0.5], -1).reshape(-1, 2)
    pu = refs.undistort_points(pd, truth)
    bent = refs.sample(small, pu[:, 0], pu[:, 1]).reshape(small.shape).astype(np.float32)
    a = bent[..., 3:4]
    bent[..., :3] = bent[..., :3] + (1 - a)            # outside the photo: white page, as the photo's own
    bent[..., 3] = 1.0
    bent_path = os.path.join(OUT, "lens", "sd-front-barrel-k1-0.06.png")
    refs.save(bent, bent_path)
    m = refs.mask(bent, 0.5)
    x0, x1, y0, y1 = refs.bbox(m)
    # the screen's four edges, marked at their middles' ends only (a builder would click these)
    ins = 40
    wide = np.nonzero(m.sum(1) > 0.5 * m.sum(1).max())[0]
    y0, y1 = int(wide.min()), int(wide.max())  # the screen's rows (not the stand's foot)
    edges = {"top": ((x0 + ins, y0 + 8), (x1 - ins, y0 + 8)), "bottom": ((x0 + ins, y1 - 8), (x1 - ins, y1 - 8)),
             "left": ((x0 + 8, y0 + ins), (x0 + 8, y1 - ins)), "right": ((x1 - 8, y0 + ins), (x1 - 8, y1 - ins))}
    lines = {}
    for k, (a, b) in edges.items():
        # snap to the true bowed edge: search wide enough for the bow
        lines[k] = refs.edge_points(bent, a, b, n=60, search=22)
    fit = refs.fit_lens(bent.shape, lines=list(lines.values()), terms=1)
    fixed_path = refs.undistort_image(bent_path, fit, out_dir=os.path.join(OUT, "lens"), overwrite=True)
    fixed = refs.load(fixed_path)
    lines_after = {k: refs.undistort_points(v, fit) for k, v in lines.items()}
    res["known"] = {"source": src, "k1_true": 0.06, "k1_fitted": round(fit["k1"], 5),
                    "rms_before_px": round(fit["rms_before_px"], 3), "rms_after_px": round(fit["rms_after_px"], 3),
                    "bent": bent_path, "fixed": fixed_path,
                    "bow_top_before_px": round(float(np.ptp(refs.line_residuals(lines["top"]))), 2),
                    "bow_top_after_px": round(float(np.ptp(refs.line_residuals(lines_after["top"]))), 2)}
    # (2) the owner's desk photo
    desk = os.path.join(REF, "ai-desk-reference-2.jpg")
    dimg = refs.load(desk)
    dl = {k: refs.edge_points(dimg, a, b, n=60, search=6) for k, (a, b) in LENS_LINES.items()}
    dfit = refs.fit_lens(dimg.shape, lines=list(dl.values()), terms=1)
    dfixed = refs.undistort_image(desk, dfit, out_dir=os.path.join(OUT, "lens"), overwrite=True) \
        if dfit["significant"] else None
    res["desk"] = {"source": desk, "k1_fitted": round(dfit["k1"], 5), "corner_shift_pct": dfit["corner_shift_pct"],
                   "rms_before_px": round(dfit["rms_before_px"], 3), "rms_after_px": round(dfit["rms_after_px"], 3),
                   "per_line_rms_before": {k: round(float(np.sqrt(np.mean(refs.line_residuals(v) ** 2))), 2)
                                           for k, v in dl.items()},
                   "significant": dfit["significant"], "advice": dfit.get("advice", ""), "fixed": dfixed}
    res["known"]["significant"] = fit["significant"]
    # before / after sheet (Pillow)
    try:
        lens_sheet(bent, fixed, lines, lines_after, fit, res, os.path.join(OUT, "lens-before-after.png"))
        res["sheet"] = os.path.join(OUT, "lens-before-after.png")
    except ImportError:
        res["sheet"] = None
    with open(os.path.join(OUT, "lens", "lens-report.json"), "w") as f:
        json.dump(res, f, indent=1)
    log(f"lens: known k1 0.06 -> fitted {res['known']['k1_fitted']}; top edge bow {res['known']['bow_top_before_px']}"
        f" -> {res['known']['bow_top_after_px']} px; desk photo k1 {res['desk']['k1_fitted']}")
    return res


def lens_sheet(bent, fixed, lines, lines_after, fit, res, out):
    """Before and after on the top edge of the screen: a ruler line from the edge's two ends drawn on
    both; before, the edge bows away from it; after, it lies on it."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from lib import refs
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 21)
    except OSError:
        font = small = ImageFont.load_default()
    sheet = Image.new("RGB", (1920, 1330), (246, 244, 238))
    d = ImageDraw.Draw(sheet)
    d.text((24, 14), "refs.py lens correction: a straight edge, before and after", fill=(29, 39, 51), font=font)
    k = res["known"]
    d.text((24, 54), f"Apple's front photo of the Studio Display bent with a known barrel distortion (k1 = +0.06, "
           f"corners pushed in 6 %). refs fitted k1 = {k['k1_fitted']:+.4f}", fill=(29, 39, 51), font=small)
    d.text((24, 80), f"from the four screen edges alone (marked roughly, snapped by edge_points). Edge points off a "
           f"straight line: rms {k['rms_before_px']:.2f} px before, {k['rms_after_px']:.2f} px after.",
           fill=(29, 39, 51), font=small)
    tw = 930
    for i, (im, ln, lab) in enumerate(((bent, lines["top"], "before: the top edge bows off the ruler "
                                        f"({k['bow_top_before_px']:.1f} px)"),
                                       (fixed, lines_after["top"], "after: on the ruler "
                                        f"({k['bow_top_after_px']:.1f} px)"))):
        im = im.copy()
        im[..., :3] = im[..., :3] * im[..., 3:4] + (1 - im[..., 3:4])     # transparent border: white
        a = Image.fromarray((np.clip(im[..., :3], 0, 1) * 255).astype(np.uint8))
        s = tw / a.size[0]
        a = a.resize((tw, int(a.size[1] * s)), Image.LANCZOS)
        dd = ImageDraw.Draw(a)
        p0, p1 = ln[0] * s, ln[-1] * s
        dd.line([tuple(p0), tuple(p1)], fill=(230, 40, 40), width=2)
        x = 20 + i * (tw + 20)
        sheet.paste(a, (x, 150))
        d.text((x, 118), lab, fill=(47, 109, 181), font=small)
        # zoom on the middle of the top edge, 6x
        mid = (ln[len(ln) // 2]).astype(int)
        z = Image.fromarray((np.clip(im[..., :3], 0, 1) * 255).astype(np.uint8)).crop(
            (mid[0] - 75, mid[1] - 25, mid[0] + 75, mid[1] + 25)).resize((900, 300), Image.NEAREST)
        dz = ImageDraw.Draw(z)
        # the ruler in the zoom: the chord at this x
        t = (mid[0] - ln[0][0]) / max(1e-6, ln[-1][0] - ln[0][0])
        yc = ln[0][1] + t * (ln[-1][1] - ln[0][1])
        yz = (yc - (mid[1] - 25)) * 6
        dz.line([(0, yz), (900, yz)], fill=(230, 40, 40), width=2)
        sheet.paste(z, (x + 15, 150 + a.size[1] + 50))
        d.text((x + 15, 150 + a.size[1] + 20), "the middle of the top edge, 6x; red: the straight line between its ends",
               fill=(47, 109, 181), font=small)
    dk = res["desk"]
    d.text((24, 1250), f"Owner's desk photo (ai-desk-reference-2.jpg), five room edges: k1 = {dk['k1_fitted']:+.4f} "
           f"(rms {dk['rms_before_px']:.2f} -> {dk['rms_after_px']:.2f} px).", fill=(29, 39, 51), font=small)
    d.text((24, 1280), "A real bend, corrected." if dk["significant"] else
           "No better than the edges' own noise, so refs says to leave that photo as it is (it was lens-corrected "
           "before it was posted).", fill=(29, 39, 51), font=small)
    sheet.save(out)
    return out


# ---------------------------------------------------------------------------
# Blender stages: screens
# ---------------------------------------------------------------------------
G8_NAMES = ["rig_display", "rig_screen"]


def stand_view(on):
    """screens_render.stand_view, read only: the G8 alone on its own stand at its lowest (the official
    522.3 mm with stand), everything else hidden."""
    import screens as S
    objs = bpy.data.objects
    dz = S.G8_STAND_LOW - S.G8_Z0
    for n in ("rig_display", "rig_screen", "rig_stand"):
        objs[n].location.z += dz if on else -dz
    objs["rig_stand"].hide_render = objs["rig_stand"].hide_viewport = not on


def prepare_g8():
    stand_view(True)
    return lambda: stand_view(False)


def build_rich():
    import screens as S
    sc = clear()
    t = time.time()
    r = S.build()
    log(f"screens rebuilt from blender/components/screens.py in {time.time() - t:.1f} s")
    return sc, r


def stage_compare():
    from lib import compare
    import screens as S
    sc, r = build_rich()
    ref = sd_front_ref(S.sd_z0() * 1000)
    names = {"g8": G8_NAMES, "g8_stand": ["rig_stand"], "sd": ["monitor_body", "monitor_screen"]}
    vs = views(names, prepare_g8, ref, g8_top_ref())
    vs[2]["explain"] = TOP_EXPLAIN
    rep = compare.run(vs, os.path.join(OUT, "compare"), "screens", title="screens (approved), toolkit compare",
                      log=log)
    old = json.load(open(SCREENS_REPORT)).get("compare", {})
    rows = []
    for e in rep["views"]:
        o = old.get(e["name"], {})
        rows.append({"view": e["name"], "toolkit_iou": e["iou"], "screens_iou": o.get("iou"),
                     "diff": None if o.get("iou") is None else round(e["iou"] - o["iou"], 4),
                     "toolkit_camera": e.get("camera"), "screens_camera": {k: o.get(k) for k in
                                                                         ("distance_m", "height_offset_m")} if o else None,
                     "iou_true": e.get("iou_true"), "size_ratio": e.get("size_ratio"), "seconds": e["seconds"]})
    with open(os.path.join(OUT, "compare", "vs-screens-report.json"), "w") as f:
        json.dump(rows, f, indent=1, default=str)
    return {"report": rep["paths"], "sheets": rep.get("sheets"), "vs_screens": rows, "passed": rep["test"]["passed"]}


def rough_screens(collection=None):
    """The 15-minute outline of the screens, from parts.py: the G8 as a rounded panel bent to 1800R with
    a hub disc behind, its slab stand from two rounded boxes; the Studio Display as a rounded panel; the
    pole. Only official sizes; about 20 lines. Returns the names by role."""
    from lib import parts as P
    import screens as S
    coll = collection or bpy.context.scene.collection
    g8 = P.rounded_panel("rough_g8", 2 * S.G8_S, S.G8_H, 0.004, r_corner=0.004, lite=True, collection=coll,
                         at=(0, 0, S.G8_Z0 + S.G8_H / 2))
    # bend it onto the 1800R arc: cut it into 32 strips across, then move every vertex onto the arc
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(g8.data)
    for i in range(1, 32):
        x = -S.G8_S + 2 * S.G8_S * i / 32
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(x, 0, 0),
                               plane_no=(1, 0, 0))
    for v in bm.verts:
        a = v.co.x / S.G8_R
        rr = S.G8_R + v.co.y                    # the glass on the arc, the thickness behind it
        v.co.x, v.co.y = rr * math.sin(a), -S.G8_R + rr * math.cos(a)
    bm.to_mesh(g8.data)
    bm.free()
    hub = P.tube("rough_g8_hub", S.G8_HUB_R, S.G8_HUB_BACK_Y - S.G8_D0 * 0.4, facing="+Y", lite=True, collection=coll,
                 at=(0, S.G8_D0 * 0.4, S.G8_Z0 + S.G8_HUB_ZC))
    shell = P.rounded_box("rough_g8_shell", S.G8_W * 0.80, S.G8_D0, S.G8_H * 0.92, r_side=0.02, lite=True,
                          collection=coll, at=(0, S.G8_D0 / 2 - 0.004, S.G8_Z0 + S.G8_H * 0.04))
    fw, ft = S.G8_FOOT
    neck_w0, neck_w1, neck_t = S.G8_NECK
    foot = P.rounded_box("rough_g8_foot", fw, S.G8_STAND_DEPTH * 0.82, ft, r_side=0.01, lite=True, collection=coll,
                         at=(0, S.G8_STAND_DEPTH * 0.41 - S.G8_SAG + 0.01, S.G8_Z0 - S.G8_STAND_LOW))
    neck = P.rounded_box("rough_g8_neck", (neck_w0 + neck_w1) / 2, neck_t, S.G8_STAND_LOW + S.G8_HUB_ZC, lite=True,
                         collection=coll, at=(0, S.G8_HUB_BACK_Y + neck_t / 2, S.G8_Z0 - S.G8_STAND_LOW))
    for o in (foot, neck):
        o.hide_render = True
    sd = P.rounded_panel("rough_sd", S.SD_W, S.SD_H, S.SD_T, r_corner=S.SD_CORNER, lite=True, collection=coll,
                         at=(0, S.SD_Y, S.sd_z0() + S.SD_H / 2))
    P.pole("rough_pole", S.POLE_R, S.POLE_H, lite=True, collection=coll, at=(0, S.POLE_Y, 0))
    return {"g8": ["rough_g8", "rough_g8_hub", "rough_g8_shell"], "g8_stand": ["rough_g8_foot", "rough_g8_neck"],
            "sd": ["rough_sd"], "all": ["rough_g8", "rough_g8_hub", "rough_g8_shell", "rough_sd", "rough_pole"]}


def stage_outline():
    import outline_check
    import screens as S
    clear()
    ref = sd_front_ref(S.sd_z0() * 1000)
    holder = {}

    def build(rough=True):
        holder["names"] = rough_screens()
        return holder["names"]["all"]

    def rough_prepare():
        objs = bpy.data.objects
        dz = S.G8_STAND_LOW - S.G8_Z0
        for n in ("rough_g8", "rough_g8_hub", "rough_g8_shell", "rough_g8_foot", "rough_g8_neck"):
            objs[n].location.z += dz
        for n in ("rough_g8_foot", "rough_g8_neck"):
            objs[n].hide_render = False

        def undo():
            for n in ("rough_g8", "rough_g8_hub", "rough_g8_shell", "rough_g8_foot", "rough_g8_neck"):
                objs[n].location.z -= dz
            for n in ("rough_g8_foot", "rough_g8_neck"):
                objs[n].hide_render = True
        return undo

    def view_fn(names):
        return views(names, rough_prepare, ref, g8_top_ref())
    rep = outline_check.run("screens-rough", build, view_fn, os.path.join(OUT, "outline"), names_fn=lambda: holder["names"],
                            log=log)
    return rep


def stage_backdrop():
    from lib import backdrops, compare, refs
    import screens as S
    sc, r = build_rich()
    out = os.path.join(OUT, "backdrop")
    os.makedirs(out, exist_ok=True)
    res = {}
    for key, rec, show in (("sd-front", sd_front_ref(S.sd_z0() * 1000), ["monitor_body", "monitor_screen"]),
                           ("g8-top", g8_top_ref(), G8_NAMES + ["rig_stand"])):
        undo_p = prepare_g8() if key.startswith("g8") else None
        bd = backdrops.add(rec, depth=1.5, opacity=1.0, name=f"ref_{key.replace('-', '_')}")
        cam = backdrops.ortho_camera(rec, distance=3.0, scale_res=0.5)
        # two Workbench passes through the backdrop's camera: the photo alone at its own colours, then the
        # model alone; laid over each other here (Workbench's X-ray would fade the photo as well)
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading
        sh.light, sh.color_type = "FLAT", "TEXTURE"
        sc.render.image_settings.color_mode = "RGBA"
        sc.render.film_transparent = True
        passes = {}
        for k, objs in (("photo", [bd.name]), ("model", show)):
            undo = compare.visible_only(objs)
            sh.light = "FLAT" if k == "photo" else "STUDIO"
            sh.show_object_outline = k == "model"
            p = os.path.join(out, f"tmp-{key}-{k}.png")
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            passes[k] = refs.load(p)
            os.remove(p)
            undo()
        ph, md = passes["photo"], passes["model"]
        a = md[..., 3:4] * 0.55
        rgb = ph[..., :3] * ph[..., 3:4] + 0.86 * (1 - ph[..., 3:4])        # the photo on a light page
        rgb = rgb * (1 - a) + md[..., :3] * a
        import numpy as np
        edge = (md[..., 3] > 0.5)
        e2 = edge ^ np.roll(edge, 1, 0) | edge ^ np.roll(edge, 1, 1)
        rgb[e2] = (0.1, 0.35, 0.95)
        path = os.path.join(out, f"tracing-{key}.png")
        refs.save(rgb, path)
        if undo_p:
            undo_p()
        bd.hide_render = True
        res[key] = {"image": path, "mm_per_px": round(rec["mm_per_px"], 4), "anchor_px": rec["anchor_px"],
                    "anchor_mm": rec["anchor_mm"], "note": rec["note"]}
        log(f"backdrop {key}: {rec['mm_per_px']:.4f} mm/px; tracing view {path}")
    # also an image empty (viewport only) saved in the .blend for a builder to open
    backdrops.add(sd_front_ref(S.sd_z0() * 1000), kind="empty", opacity=0.6, depth=1.5, name="ref_sd_front_empty")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, "out", "toolkit-backdrops.blend"), compress=True)
    return res


def main_blender(stages):
    res = {}
    t0 = time.time()
    for st, fn in (("parts", stage_parts), ("outline", stage_outline), ("compare", stage_compare),
                   ("backdrop", stage_backdrop)):
        if st in stages:
            t = time.time()
            res[st] = fn()
            res[st + "_s"] = round(time.time() - t, 1)
    if "lens" in stages:
        from lib import compare
        py = compare.plain_python()
        r = subprocess.run([py, os.path.abspath(__file__), "lens"], capture_output=True, text=True)
        print(r.stdout[-2000:], r.stderr[-2000:], flush=True)
        try:
            res["lens"] = json.load(open(os.path.join(OUT, "lens", "lens-report.json")))
        except OSError:
            res["lens"] = {"error": r.stderr[-500:]}
    res["total_s"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "toolkit-demo-report.json")
    old = {}
    if os.path.exists(p):
        try:
            old = json.load(open(p))
        except ValueError:
            old = {}
    old.update(res)
    with open(p, "w") as f:
        json.dump(old, f, indent=1, default=str)
    log(f"demo done in {res['total_s']} s: {p}")


if __name__ == "__main__":
    if bpy is None:
        if "lens" in sys.argv[1:]:
            stage_lens()
        else:
            print(__doc__)
    else:
        a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        st = next((x for x in a if not x.startswith("--")), "all")
        stages = {"parts", "outline", "compare", "backdrop", "lens"} if st == "all" else set(st.split(","))
        main_blender(stages)
        bpy.ops.wm.quit_blender()
