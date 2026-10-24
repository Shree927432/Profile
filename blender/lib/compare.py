"""Photo compare as a test: the screens compare (screens_render.py stage_compare and
screens_blueprint.py compare_sheets) made generic.

For each view of a component: render the shown objects' silhouette from a camera that matches the
photo, score it against the photo's silhouette (intersection over union), render a look image from the
same camera, and decide pass/fail against a threshold (default 0.98). Then write a report (JSON and a
Markdown table) and the sheets: per view the 50/50 and outline sheet, and one stacked
"photo vs model" sheet (photo left, render right, a title per row).

A view is a dict:

    name      "g8-front"                         (file names, report keys)
    title     "Samsung G8: front (Samsung drawing) vs our model"
    photo     path to the reference image
    mask      "alpha" or a brightness threshold (0.92: darker than that on a white page)
    crop      (x0, x1, y0, y1) or None           only this box of the photo counts
    fill      optional: fill holes in the photo mask (bright screen content). Default (2026-10-24): True for a
              brightness-threshold mask, False for an "alpha" mask: an alpha mask already holds the true
              silhouette, and filling it closed real gaps (panel to stand) that the render keeps open
    objects   object names to show (all others are hidden for the render)
    prepare   optional callable() -> undo()      e.g. move a part into the photo's pose
    camera    one of
              {"mode": "placed", "ref": refs.ref_record(...)}
                  orthographic, from backdrops.ortho_camera(): true scale AND position; the strictest
              {"mode": "ortho", "view": "front"}
                  orthographic, framed on the objects; scored after aligning the boxes (proportions)
              {"mode": "fit", "view": "front", "tilts": [0], "distances": None, "heights": None}
                  perspective: the camera distance, height (and tilt) searched to fit the photo, as
                  screens did for Samsung's perspective renders, then (2026-10-24) a sideways lens shift
                  refined from that best (kept only where it scores higher; "shift": False turns it off);
                  scored after aligning the boxes
              {"mode": "free", "view": "front", "yaws": [-40, -30], "tilts": [0], "h_range": (-0.3, 0.3),
               "distances": None (metres; default 0.85 to 5 frame widths)}
                  the fuller search for turned shots (2026-10-24, from screens_render.free_fit): distance,
                  height, sideways lens shift, the model's turn about Z ("yaws", degrees, + = counter-
                  clockwise from above; done by orbiting the camera, the model is not moved) and tilt,
                  framed on the box's largest side. A "fit" view that gives "yaws" runs this search too.
    fit_mask  optional callable(mask) -> mask used while searching the camera (e.g. the panel only)
    threshold optional, overrides the run's
    explain   optional: why this view may stay under the threshold (shown as EXPLAINED, not FAIL)

Blender side (inside Blender):   rep = compare.run(views, out_dir, "screens")
Plain side (Pillow, no Blender): python3 blender/lib/compare.py sheets <report.json>
compare.run() calls the plain side itself through a subprocess (Blender's Python has no Pillow).

Scores: "iou" is after aligning the render's box to the photo's (uniform scale, then a small search of
a few pixels and half a percent), exactly as the screens report; in placed mode "iou_true" is the raw
overlap at true scale and position and "size_ratio" how far the best alignment had to scale (1 = the
model is the photo's size).
"""
import json
import math
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from lib import refs  # noqa: E402

THRESHOLD = 0.98


# ---------------------------------------------------------------------------
# mask maths (no Blender)
# ---------------------------------------------------------------------------
def warp(rend, shape, s, tx, ty):
    """The render mask drawn into the photo frame: photo (x, y) = render (x, y) * s + (tx, ty)."""
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W]
    sx = ((xx - tx) / s).astype(int)
    sy = ((yy - ty) / s).astype(int)
    ok = (sx >= 0) & (sy >= 0) & (sx < rend.shape[1]) & (sy < rend.shape[0]) & (xx - tx >= 0) & (yy - ty >= 0)
    out = np.zeros(shape, bool)
    out[ok] = rend[sy[ok], sx[ok]]
    return out


def iou(a, b):
    return float((a & b).sum() / max(1, (a | b).sum()))


def align_iou(photo, rend, refine=False, identity=False):
    """Scale and move the render mask so its box matches the photo's (uniform scale from the widths,
    centred across, tops level), then IoU; with refine, also search +-4 px across, +-8 px down and
    +-1 % of scale. identity=True starts from no transform (placed cameras). Returns (iou, transform)."""
    px0, px1, py0, py1 = refs.bbox(photo)
    rx0, rx1, ry0, ry1 = refs.bbox(rend)
    if identity:
        s0, t0 = 1.0, (0.0, 0.0)
    else:
        s0 = (px1 - px0) / max(1, rx1 - rx0)
        t0 = ((px0 + px1) / 2 - (rx0 + rx1) / 2 * s0, py0 - ry0 * s0)
    # score inside the union of both boxes plus a margin wider than the search: every pixel of either
    # mask stays inside, so the result is the full-frame IoU on far fewer pixels
    m = int(0.03 * max(photo.shape)) + 10
    X0 = max(0, min(px0, int(rx0 * s0 + t0[0])) - m)
    Y0 = max(0, min(py0, int(ry0 * s0 + t0[1])) - m)
    X1 = min(photo.shape[1], max(px1, int(rx1 * s0 + t0[0])) + m)
    Y1 = min(photo.shape[0], max(py1, int(ry1 * s0 + t0[1])) + m)
    ph = photo[Y0:Y1, X0:X1]
    steps = [(ds, dx, dy) for ds in (0.99, 0.995, 1.0, 1.005, 1.01) for dx in (-4, -2, 0, 2, 4)
             for dy in (-8, -6, -4, -2, 0, 2, 4, 6, 8)] if refine else [(1.0, 0, 0)]
    best = None
    rcx, rcy = (rx0 + rx1) / 2, (ry0 + ry1) / 2
    for ds, dx, dy in steps:
        s = s0 * ds
        # scale about the render box's centre so the search does not slide the shape
        tx = t0[0] + rcx * s0 - rcx * s + dx
        ty = t0[1] + ry0 * s0 - ry0 * s + dy if not identity else t0[1] + rcy * s0 - rcy * s + dy
        rm = warp(rend, ph.shape, s, tx - X0, ty - Y0)
        v = iou(ph, rm)
        if best is None or v > best[0]:
            best = (v, {"scale": float(s), "tx": float(tx), "ty": float(ty)})
    return best


def fill_default(view):
    """Hole-fill the photo mask? The view's own "fill" if given; else only for brightness-threshold masks
    (bright content inside a dark body), never for alpha masks (their holes are real gaps)."""
    if view.get("fill") is not None:
        return bool(view["fill"])
    return view.get("mask", "alpha") != "alpha"


def photo_mask(view):
    img = refs.load(view["photo"])
    m = refs.mask(img, view.get("mask", "alpha"), view.get("crop"))
    if fill_default(view):
        m = refs.fill_holes(m)
    return m


# ---------------------------------------------------------------------------
# Blender side
# ---------------------------------------------------------------------------
def _bpy():
    import bpy
    return bpy


def visible_only(names):
    """Hide every mesh/curve/empty-with-geometry not in `names` (and not a backdrop) for rendering.
    Returns undo()."""
    bpy = _bpy()
    keep = set(names)
    state = []
    for o in bpy.data.objects:
        if o.type in ("MESH", "CURVE", "FONT", "SURFACE", "META", "EMPTY"):
            want = o.name in keep
            if o.hide_render == want:
                state.append((o, o.hide_render))
                o.hide_render = not want
    return lambda: [setattr(o, "hide_render", h) for o, h in state]


def world_bbox(names):
    bpy = _bpy()
    from mathutils import Vector
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    for n in names:
        o = bpy.data.objects[n]
        if o.type not in ("MESH", "CURVE"):
            continue
        for c in o.evaluated_get(dg).bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


class _Silhouette:
    """Workbench flat renders with a transparent film, read back as masks."""

    def __init__(self, path):
        bpy = _bpy()
        self.scene = bpy.context.scene
        self.path = path
        sc = self.scene
        self.saved = dict(engine=sc.render.engine, film=sc.render.film_transparent,
                          fmt=sc.render.image_settings.file_format, mode=sc.render.image_settings.color_mode,
                          rx=sc.render.resolution_x, ry=sc.render.resolution_y, pct=sc.render.resolution_percentage,
                          comp=sc.render.use_compositing, seq=sc.render.use_sequencer)
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading
        sh.light, sh.color_type = "FLAT", "SINGLE"
        try:
            sc.display.render_aa = "FXAA"
        except (AttributeError, TypeError):
            pass
        sc.render.film_transparent = True
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGBA"
        sc.render.resolution_percentage = 100
        sc.render.use_compositing = False
        sc.render.use_sequencer = False

    def __call__(self, w, h):
        bpy = _bpy()
        self.scene.render.resolution_x, self.scene.render.resolution_y = int(w), int(h)
        self.scene.render.filepath = self.path
        bpy.ops.render.render(write_still=True)
        return refs.load(self.path)[..., 3] > 0.5

    def restore(self):
        sc, s = self.scene, self.saved
        sc.render.engine = s["engine"]
        sc.render.film_transparent = s["film"]
        sc.render.image_settings.file_format = s["fmt"]
        sc.render.image_settings.color_mode = s["mode"]
        sc.render.resolution_x, sc.render.resolution_y = s["rx"], s["ry"]
        sc.render.resolution_percentage = s["pct"]
        sc.render.use_compositing, sc.render.use_sequencer = s["comp"], s["seq"]


def _cam(name="cmp_cam"):
    bpy = _bpy()
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if cam.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(cam)
    return cam, cd


def _place_persp(cam, cd, view, centre, F, D, dz, tilt, side=0.0, yaw=0.0):
    """A perspective camera D from centre along the view's normal, raised dz and moved sideways `side`
    with the lens shifted back so the centre stays framed (as product renders do), tilted `tilt` degrees
    about its right axis; yaw (degrees) orbits it about world Z through the centre by -yaw, which shows
    the model as if turned +yaw."""
    from mathutils import Matrix, Vector
    from . import backdrops
    R, U, N = backdrops.axes(view)
    if tilt:
        rot = Matrix.Rotation(math.radians(tilt), 3, R)
        U, N = rot @ U, rot @ N
    if yaw:
        rz = Matrix.Rotation(math.radians(-yaw), 3, "Z")
        R, U, N = rz @ R, rz @ U, rz @ N
    cd.type = "PERSP"
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36
    cd.lens = 36 * D / F
    cd.shift_x, cd.shift_y = -side / F, -dz / F
    cd.clip_start = 0.01
    cd.clip_end = D * 4 + 10
    cam.matrix_world = (Matrix.Translation(Vector(centre) + N * D + U * dz + R * side)
                        @ Matrix((R, U, N)).transposed().to_4x4())


def _free_search(score, F, yaws, tilts, h_range=(-0.3, 0.3), tries=None, distances=None):
    """The fuller camera search (screens_render.free_fit, made generic): a grid over distance, height,
    sideways shift, turn and tilt (lengths in units of the frame width F), then a pattern search that halves
    its steps. score(D, dz, side, yaw, tilt) -> IoU. Returns (iou, (D, dz, side, yaw, tilt))."""
    hr = (h_range[0] * F, h_range[1] * F)
    hs = sorted(set([h * F for h in (-0.15, -0.05, 0.05, 0.15) if h_range[0] <= h <= h_range[1]] + list(hr)))
    best = None
    for D in (distances or (0.85 * F, 1.35 * F, 2.1 * F, 3.4 * F, 5.0 * F)):
        for h in hs:
            for side in (-0.17 * F, 0.0, 0.08 * F, 0.17 * F):
                for yaw in yaws:
                    for tl in tilts:
                        p = (D, h, side, yaw, tl)
                        v = score(*p)
                        if tries is not None:
                            tries.append((round(v, 4),) + tuple(round(x, 3) for x in p))
                        if best is None or v > best[0]:
                            best = (v, p)
    ystep = abs(yaws[1] - yaws[0]) / 2 if len(yaws) > 1 else 0.0
    tstep = abs(tilts[1] - tilts[0]) / 2 if len(tilts) > 1 else 0.0
    steps = [0.25, 0.04 * F, 0.05 * F, ystep, tstep]
    for _ in range(7):
        for i in range(5):
            if not steps[i]:
                continue
            for sgn in (1, -1):
                p = list(best[1])
                p[i] = p[i] * (1 + sgn * steps[0]) if i == 0 else p[i] + sgn * steps[i]
                p[1] = min(hr[1], max(hr[0], p[1]))
                v = score(*p)
                if tries is not None:
                    tries.append((round(v, 4),) + tuple(round(x, 3) for x in p))
                if v > best[0]:
                    best = (v, tuple(p))
                    break
        steps = [x / 2 for x in steps]
    return best


def score_view(view, out_dir, look_engine="BLENDER_EEVEE", look_samples=16, threshold=THRESHOLD, log=print):
    """Score one view; returns its report entry (see the module doc)."""
    bpy = _bpy()
    from . import backdrops
    t0 = time.time()
    scene = bpy.context.scene
    name = view["name"]
    os.makedirs(os.path.join(out_dir, "measure"), exist_ok=True)
    sil = os.path.join(out_dir, "measure", f"sil-{name}.png")
    photo = photo_mask(view)
    H, W = photo.shape
    cam0 = scene.camera
    undo_prep = view["prepare"]() if view.get("prepare") else None
    undo_vis = visible_only(view["objects"])
    S = _Silhouette(sil)
    camcfg = dict(view.get("camera") or {"mode": "ortho", "view": "front"})
    mode = camcfg["mode"]
    fitm = view.get("fit_mask")
    entry = {"name": name, "title": view.get("title", name), "photo": view["photo"], "mask": view.get("mask", "alpha"),
             "crop": view.get("crop"), "fill": fill_default(view), "camera_mode": mode,
             "objects": list(view["objects"])}
    tries = []
    try:
        if mode == "placed":
            cam = backdrops.ortho_camera(camcfg["ref"], name="cmp_cam_placed")
            scene.camera = cam
            entry["camera"] = {"view": camcfg["ref"]["view"], "mm_per_px": camcfg["ref"]["mm_per_px"],
                               "anchor_px": camcfg["ref"]["anchor_px"], "anchor_mm": camcfg["ref"]["anchor_mm"]}
            rm = S(W, H)
            entry["iou_true"] = round(iou(photo, rm), 4)
            v, tf = align_iou(photo, rm, refine=True, identity=True)
            entry["size_ratio"] = round(tf["scale"], 4)
        elif mode == "ortho":
            lo, hi = world_bbox(view["objects"])
            c = (lo + hi) / 2
            R, U, N = backdrops.axes(camcfg["view"])
            ext = max(abs((hi - lo).dot(R)), abs((hi - lo).dot(U)) * W / H)
            cam = backdrops.view_camera(camcfg["view"], c, ext * 1.15, aspect=W / H, name="cmp_cam_ortho")
            scene.camera = cam
            rm = S(W, H)
            v, tf = align_iou(photo, rm, refine=True)
            entry["camera"] = {"view": camcfg["view"], "ortho_scale": cam.data.ortho_scale}
        elif mode == "free" or camcfg.get("yaws"):              # the fuller search (turned shots)
            lo, hi = world_bbox(view["objects"])
            centre = (lo + hi) / 2
            F = 1.2 * max(max(hi - lo), 0.05) * max(1.0, W / H)     # the largest side fits both ways
            cam, cd = _cam()
            scene.camera = cam
            p4 = photo[::4, ::4]

            def score4(D, dz, side, yaw, tl):
                _place_persp(cam, cd, camcfg["view"], centre, F, D, dz, tl, side, yaw)
                return align_iou(p4, S(p4.shape[1], p4.shape[0]))[0]
            _, (D, dz, side, yaw, tl) = _free_search(score4, F, list(camcfg.get("yaws") or [0.0]),
                                                     list(camcfg.get("tilts") or [0.0]),
                                                     camcfg.get("h_range", (-0.3, 0.3)), tries,
                                                     camcfg.get("distances"))
            _place_persp(cam, cd, camcfg["view"], centre, F, D, dz, tl, side, yaw)
            rm = S(W, H)
            v, tf = align_iou(photo, rm, refine=True)
            entry["camera"] = {"view": camcfg["view"], "distance_m": round(D, 4), "height_offset_m": round(dz, 4),
                               "sideways_m": round(side, 4), "turn_deg": round(yaw, 1), "tilt_deg": round(tl, 1),
                               "frame_width_m": round(F, 4), "lens_mm": round(36 * D / F, 2)}
            entry["yaw_deg"] = round(yaw, 1)
            entry["tries_best"] = sorted(tries)[-5:]
        else:                                                   # perspective fit
            lo, hi = world_bbox(view["objects"])
            centre = (lo + hi) / 2
            R, U, N = backdrops.axes(camcfg["view"])
            # the frame's width; 2026-10-24: wide enough that the height fits a landscape photo too (a tall
            # object in a 16:9 photo was cut off at the top and bottom before; unchanged when it fits)
            F = 1.3 * max(abs((hi - lo).dot(R)), abs((hi - lo).dot(U)) * W / H, 0.05)
            cam, cd = _cam()
            scene.camera = cam
            quick = camcfg.get("quick")
            q = 4 if quick else 2                  # the search runs at half (quick: quarter) size
            p2 = photo[::q, ::q]
            target = fitm(p2) if fitm else p2
            dists = camcfg.get("distances") or [k * F for k in ((0.8, 1.25, 1.9, 3.1) if quick else
                                                                (0.56, 0.8, 1.25, 1.9, 3.1, 5.0))]
            heights = camcfg.get("heights") or [k * F for k in ((-0.09, 0.0, 0.09) if quick else
                                                                (-0.28, -0.19, -0.09, 0.0, 0.09, 0.19, 0.28))]
            tilts = camcfg.get("tilts") or [0.0]

            def score2(D, dz, tl):
                _place_persp(cam, cd, camcfg["view"], centre, F, D, dz, tl)
                r = S(p2.shape[1], p2.shape[0])
                r = fitm(r) if fitm else r
                return align_iou(target, r)[0]
            best = None
            for tl in tilts:
                for D in dists:
                    for dz in heights:
                        v = score2(D, dz, tl)
                        tries.append((round(v, 4), round(D, 3), round(dz, 3), tl))
                        if best is None or v > best[0]:
                            best = (v, D, dz, tl)
            _, D0, z0, t0_ = best
            step = (heights[1] - heights[0]) if len(heights) > 1 else 0.05 * F
            for D in ((D0 * 0.87, D0 * 1.15) if quick else (D0 * 0.75, D0 * 0.87, D0 * 1.15, D0 * 1.3)):
                for dz in (z0 - step / 2, z0, z0 + step / 2):
                    for tl in ([t0_ - 2.5, t0_, t0_ + 2.5] if len(tilts) > 1 else [t0_]):
                        v = score2(D, dz, tl)
                        tries.append((round(v, 4), round(D, 3), round(dz, 3), tl))
                        if v > best[0]:
                            best = (v, D, dz, tl)
            # then a small pattern search: each of distance, height (and tilt) a step either way, keep
            # what helps, halve the steps (the grid alone can stop in a shallow local best)
            if not quick:
                st = {"D": best[1] * 0.12, "dz": step / 2, "tl": 2.0 if len(tilts) > 1 else 0.0}
                for _ in range(4):
                    for k in ("D", "dz", "tl"):
                        if not st[k]:
                            continue
                        for sgn in (1, -1):
                            cand = list(best[1:])
                            cand[("D", "dz", "tl").index(k)] += sgn * st[k]
                            v = score2(*cand)
                            tries.append((round(v, 4), round(cand[0], 3), round(cand[1], 3), cand[2]))
                            if v > best[0]:
                                best = (v, *cand)
                                break
                    st = {k: x / 2 for k, x in st.items()}
            _, D0, dz0, tl = best

            def height_pass(dz, side):
                """the fit part (say the panel) barely fixes the camera's height at long range; the rest
                (the stand) does: one more pass on the whole silhouette, height only"""
                full2 = photo[::q, ::q]
                bh = None

                def hscore(h):
                    _place_persp(cam, cd, camcfg["view"], centre, F, D0, h, tl, side)
                    return align_iou(full2, S(full2.shape[1], full2.shape[0]))[0]
                for h in sorted(set([dz] + list(heights))):
                    v = hscore(h)
                    if bh is None or v > bh[0]:
                        bh = (v, h)
                for h in (bh[1] - step / 2, bh[1] - step / 4, bh[1] + step / 4, bh[1] + step / 2):
                    v = hscore(h)
                    if v > bh[0]:
                        bh = (v, h)
                return bh[1]

            def final(dz, side):
                _place_persp(cam, cd, camcfg["view"], centre, F, D0, dz, tl, side)
                rm = S(W, H)
                return align_iou(photo, rm, refine=True) + (rm, dz, side)
            # the search as before (no sideways shift)
            res = final(height_pass(dz0, 0.0) if fitm else dz0, 0.0)
            if camcfg.get("shift", True) and not quick:
                # 2026-10-24: a sideways lens shift refined from that best (product renders are often shot
                # off-centre; the grid cannot see it). The final full-size score decides, so the result is
                # never worse than the search without it.
                bs = (best[0], 0.0)
                st = 0.08 * F
                for _ in range(5):
                    for sgn in (1, -1):
                        _place_persp(cam, cd, camcfg["view"], centre, F, D0, dz0, tl, bs[1] + sgn * st)
                        r = S(p2.shape[1], p2.shape[0])
                        v = align_iou(target, fitm(r) if fitm else r)[0]
                        tries.append((round(v, 4), round(D0, 3), round(dz0, 3), tl, round(bs[1] + sgn * st, 3)))
                        if v > bs[0]:
                            bs = (v, bs[1] + sgn * st)
                            break
                    st /= 2
                if bs[1]:
                    res2 = final(height_pass(dz0, bs[1]) if fitm else dz0, bs[1])
                    if res2[0] > res[0]:
                        res = res2
            v, tf, rm, dz, side = res
            D = D0
            _place_persp(cam, cd, camcfg["view"], centre, F, D, dz, tl, side)    # the look render's camera
            entry["camera"] = {"view": camcfg["view"], "distance_m": round(D, 4), "height_offset_m": round(dz, 4),
                               "tilt_deg": tl, "sideways_m": round(side, 4), "frame_width_m": round(F, 4),
                               "lens_mm": round(36 * D / F, 2)}
            if fitm:
                entry["iou_fit_part"] = round(align_iou(fitm(photo), fitm(rm), refine=True)[0], 4)
            entry["tries_best"] = sorted(tries)[-5:]
        entry["iou"] = round(v, 4)
        entry["transform"] = tf
        entry["silhouette"] = sil
        # the look render, same camera and frame
        if look_engine:
            S.restore()
            rpath = os.path.join(out_dir, "measure", f"render-{name}.png")
            ensure_studio()
            look(rpath, W, H, look_engine, look_samples)
            entry["render"] = rpath
        else:
            S.restore()
    finally:
        undo_vis()
        if undo_prep:
            undo_prep()
        scene.camera = cam0
    thr = view.get("threshold", threshold)
    entry["threshold"] = thr
    entry["pass"] = bool(entry["iou"] >= thr)
    entry["explain"] = view.get("explain", "")
    entry["seconds"] = round(time.time() - t0, 1)
    log(f"compare {name}: IoU {entry['iou']:.4f} ({'pass' if entry['pass'] else 'FAIL'} at {thr}) "
        f"in {entry['seconds']} s, camera {entry.get('camera')}")
    return entry


def ensure_studio(strength=1.0):
    """A neutral light studio for look renders, only if the scene has no lights of its own."""
    bpy = _bpy()
    if any(o.type == "LIGHT" and not o.hide_render for o in bpy.data.objects):
        return None
    scene = bpy.context.scene
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    w = scene.world
    try:
        w.use_nodes = True
    except AttributeError:
        pass
    bg = w.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs["Color"].default_value = (0.62, 0.63, 0.66, 1)
        bg.inputs["Strength"].default_value = 0.55 * strength
    coll = bpy.data.collections.get("cmp_studio") or bpy.data.collections.new("cmp_studio")
    if coll.name not in scene.collection.children:
        scene.collection.children.link(coll)
    from mathutils import Vector
    for nm, loc, e in (("cmp_key", (-2.0, -2.5, 2.4), 900), ("cmp_fill", (2.4, -1.8, 1.2), 300),
                       ("cmp_rim", (1.0, 2.6, 2.2), 500), ("cmp_top", (0.0, 0.0, 3.5), 250)):
        d = bpy.data.lights.new(nm, "AREA")
        d.size, d.energy = 2.0, e * strength
        o = bpy.data.objects.new(nm, d)
        coll.objects.link(o)
        o.location = loc
        o.rotation_euler = (-Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return coll


def look(path, w, h, engine="BLENDER_EEVEE", samples=16, label=None):
    """A lit render from the scene camera at w x h, transparent background. Cycles goes through the
    render queue."""
    bpy = _bpy()
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = int(w), int(h)
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.render.filepath = path
    if engine == "CYCLES":
        from . import renderqueue
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        with renderqueue.slot(label or os.path.basename(path)):
            bpy.ops.render.render(write_still=True)
    else:
        try:
            sc.eevee.taa_render_samples = samples
        except AttributeError:
            pass
        bpy.ops.render.render(write_still=True)
    sc.render.film_transparent = False
    return path


def run(views, out_dir, name, threshold=THRESHOLD, look_engine="BLENDER_EEVEE", look_samples=16, sheets=True,
        title=None, log=print):
    """Score every view, write <name>-compare.json and <name>-compare.md (the test table) in out_dir,
    then the sheets (through plain Python). Returns the report dict."""
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    entries = [score_view(v, out_dir, look_engine, look_samples, threshold, log) for v in views]
    rep = {"component": name, "title": title or name, "threshold": threshold, "date": time.strftime("%Y-%m-%d %H:%M"),
           "views": entries, "seconds": round(time.time() - t0, 1)}
    rep["test"] = test(rep, threshold)
    paths = write_report(rep, out_dir, name)
    rep["paths"] = paths
    if sheets:
        rep["sheets"] = make_sheets(paths["json"])
    return rep


# ---------------------------------------------------------------------------
# the test
# ---------------------------------------------------------------------------
def test(rep, threshold=THRESHOLD):
    """Pass/fail per view. A view under its threshold with an 'explain' counts as EXPLAINED (the
    pipeline allows that, with the reason written down); the component passes when every view is
    PASS or EXPLAINED."""
    rows = []
    for e in rep["views"]:
        thr = e.get("threshold", threshold)
        ok = e["iou"] >= thr
        status = "PASS" if ok else ("EXPLAINED" if e.get("explain") else "FAIL")
        rows.append({"view": e["name"], "iou": e["iou"], "threshold": thr, "status": status, "pass": ok,
                     "iou_true": e.get("iou_true"), "size_ratio": e.get("size_ratio"),
                     "camera": e.get("camera_mode"), "explain": e.get("explain", "")})
    return {"passed": all(r["status"] != "FAIL" for r in rows), "rows": rows}


def write_report(rep, out_dir, name):
    jp = os.path.join(out_dir, f"{name}-compare.json")
    mp = os.path.join(out_dir, f"{name}-compare.md")
    with open(jp, "w") as f:
        json.dump(rep, f, indent=1, default=str)
    t = rep["test"]
    lines = [f"# {rep.get('title', name)}: photo compare test", "",
             f"{rep['date']}, threshold {rep['threshold']}: **{'PASSED' if t['passed'] else 'FAILED'}**", "",
             "| Angle | IoU | Threshold | Result | Camera | True-scale IoU | Size ratio | Note |",
             "|---|---|---|---|---|---|---|---|"]
    for r in t["rows"]:
        lines.append(f"| {r['view']} | {r['iou']:.4f} | {r['threshold']} | {r['status']} | {r['camera']} | "
                     f"{'' if r['iou_true'] is None else format(r['iou_true'], '.4f')} | "
                     f"{'' if r['size_ratio'] is None else r['size_ratio']} | {r['explain']} |")
    lines += ["", "IoU: silhouette intersection over union after aligning the boxes (scale from the widths, then a",
              "search of a few pixels and 1 % of scale). True-scale IoU (placed cameras): no alignment at all.", ""]
    with open(mp, "w") as f:
        f.write("\n".join(lines))
    return {"json": jp, "md": mp}


# ---------------------------------------------------------------------------
# plain side: sheets (Pillow)
# ---------------------------------------------------------------------------
def plain_python():
    """A python3 with numpy and Pillow (Blender's has no Pillow)."""
    for p in ("/opt/anaconda3/bin/python3", "/usr/local/bin/python3", "/opt/homebrew/bin/python3", "/usr/bin/python3"):
        if os.path.exists(p):
            r = subprocess.run([p, "-c", "import numpy, PIL"], capture_output=True)
            if r.returncode == 0:
                return p
    return None


def make_sheets(report_json):
    """From inside Blender: run this file with plain Python to draw the sheets. Returns their paths."""
    py = plain_python()
    if py is None:
        print("compare: no python3 with Pillow found; sheets skipped", flush=True)
        return []
    r = subprocess.run([py, os.path.abspath(__file__), "sheets", report_json], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr, flush=True)
        return []
    return [l.split(" ", 1)[1] for l in r.stdout.splitlines() if l.startswith("SHEET ")]


def _fonts():
    from PIL import ImageFont
    try:
        return (ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30),
                ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 21))
    except OSError:
        f = ImageFont.load_default()
        return f, f


def _layers(e):
    """(photo on its page, our render placed in the photo frame on the same page, photo mask, render mask)."""
    from PIL import Image
    src = Image.open(e["photo"]).convert("RGBA")
    W, H = src.size
    bgc = (255, 255, 255, 255) if e["mask"] != "alpha" else (232, 233, 236, 255)
    ph = Image.new("RGBA", (W, H), bgc)
    ph.alpha_composite(src)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if e.get("render") and os.path.exists(e["render"]):
        rd = Image.open(e["render"]).convert("RGBA")
        tf = e["transform"]
        s = tf["scale"]
        rw = rd.resize((max(1, int(round(rd.size[0] * s))), max(1, int(round(rd.size[1] * s)))), Image.LANCZOS)
        layer.paste(rw, (int(round(tf["tx"])), int(round(tf["ty"]))), rw)
    rend = Image.new("RGBA", (W, H), bgc)
    rend.alpha_composite(layer)
    pm = refs.mask(np.asarray(src, np.float32) / 255.0, e["mask"], e.get("crop"))
    if fill_default(e):
        pm = refs.fill_holes(pm)
    rm = np.asarray(layer)[..., 3] > 128
    return ph, rend, pm, rm


def _box(pm, rm, W, H, pad=0.04):
    ys, xs = np.nonzero(pm | rm)
    p = int(pad * max(W, H))
    return (max(0, xs.min() - p), max(0, ys.min() - p), min(W, xs.max() + p), min(H, ys.max() + p))


def sheet_view(e, out):
    """One view: photo, render (same camera and scale), 50/50, outlines (photo red, render blue)."""
    from PIL import Image, ImageDraw, ImageFilter
    font, small = _fonts()
    ph, rend, pm, rm = _layers(e)
    W, H = ph.size
    over = Image.blend(ph, rend, 0.5)
    ea = np.asarray(ph.convert("L").convert("RGB")).astype(float) * 0.35 + 165
    for m, col in ((pm, (220, 40, 40)), (rm, (40, 90, 230))):
        mi = Image.fromarray((m * 255).astype(np.uint8))
        edge = np.asarray(mi.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))) > 0
        ea[edge] = col
    edge = Image.fromarray(ea.astype(np.uint8))
    box = _box(pm, rm, W, H)
    sheet = Image.new("RGB", (1920, 1080), (246, 244, 238))
    d = ImageDraw.Draw(sheet)
    status = "PASS" if e["pass"] else ("EXPLAINED" if e.get("explain") else "FAIL")
    extra = f"   true scale {e['iou_true']:.3f}, size x{e['size_ratio']}" if e.get("iou_true") is not None else ""
    d.text((24, 14), f"{e['title']}   IoU {e['iou']:.4f}  {status} at {e['threshold']}{extra}", fill=(29, 39, 51),
           font=font)
    cam = e.get("camera", {})
    d.text((24, 52), f"camera: {e['camera_mode']} {json.dumps(cam)[:150]}" + (f"   note: {e['explain']}" if e.get("explain") else ""),
           fill=(29, 39, 51), font=small)
    tiles = [("official photo", ph), ("our render, same camera and scale", rend), ("50 / 50", over),
             ("outlines: photo red, render blue", edge)]
    tw, th = 940, 488
    for i, (lab, im) in enumerate(tiles):
        crop = im.convert("RGB").crop(box)
        crop.thumbnail((tw, th - 30), Image.LANCZOS)
        x = 13 + (i % 2) * (tw + 14)
        y = 84 + (i // 2) * (th + 6)
        sheet.paste(crop, (x + (tw - crop.size[0]) // 2, y + 30))
        d.text((x, y + 2), lab, fill=(47, 109, 181), font=small)
    sheet.save(out)
    return out


def sheet_stack(rep, out, width=1920):
    """Every view stacked: a title per row, the photo left, our render right, same crop."""
    from PIL import Image, ImageDraw
    font, small = _fonts()
    rows = []
    col_w = width // 2 - 30
    for e in rep["views"]:
        ph, rend, pm, rm = _layers(e)
        box = _box(pm, rm, *ph.size)
        a = ph.convert("RGB").crop(box)
        b = rend.convert("RGB").crop(box)
        s = min(col_w / a.size[0], 520 / a.size[1])
        sz = (max(1, int(a.size[0] * s)), max(1, int(a.size[1] * s)))
        rows.append((e, a.resize(sz, Image.LANCZOS), b.resize(sz, Image.LANCZOS)))
    H = 20 + sum(84 + r[1].size[1] + 16 for r in rows)
    sheet = Image.new("RGB", (width, H), (246, 244, 238))
    d = ImageDraw.Draw(sheet)
    y = 14
    for e, a, b in rows:
        status = "PASS" if e["pass"] else ("EXPLAINED" if e.get("explain") else "FAIL")
        d.text((14, y), f"{e['title']}", fill=(29, 39, 51), font=font)
        d.text((width - 420, y + 6), f"IoU {e['iou']:.3f}  {status}", fill=(29, 39, 51) if e["pass"] else (190, 40, 30),
               font=small)
        d.text((14, y + 44), "official photo", fill=(47, 109, 181), font=small)
        d.text((width // 2 + 14, y + 44), "our render, same camera and scale", fill=(47, 109, 181), font=small)
        y += 76
        sheet.paste(a, (14 + (col_w - a.size[0]) // 2, y))
        sheet.paste(b, (width // 2 + 14 + (col_w - b.size[0]) // 2, y))
        y += a.size[1] + 24
    if out.lower().endswith((".jpg", ".jpeg")):
        sheet.save(out, quality=90)
    else:
        sheet.save(out)
    return out


def sheets(report_json):
    rep = json.load(open(report_json))
    d = os.path.dirname(report_json)
    name = rep["component"]
    outs = []
    for e in rep["views"]:
        outs.append(sheet_view(e, os.path.join(d, f"{name}-compare-{e['name']}.png")))
    outs.append(sheet_stack(rep, os.path.join(d, f"{name}-photo-vs-model.jpg")))
    return outs


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "sheets":
        for p in sheets(sys.argv[2]):
            print("SHEET", p)
    else:
        print(__doc__)
