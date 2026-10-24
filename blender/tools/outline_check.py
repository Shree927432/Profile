"""The outline check: the gate about 15 minutes into a component, before any detail.

Build the component ROUGH (silhouettes only: the official outer sizes, the big masses), render it from
the front, the side, the top and three-quarters in quick EEVEE, score the views that have reference
photos with lib/compare.py, and write ONE review sheet for the owner or the coordinator to approve the
proportions. Seconds to a minute, no Cycles. Always headless:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/tools/outline_check.py -- blender/components/<name>.py [--out DIR] [--threshold 0.96]

The component module provides
    NAME                              "speakers"
    build(rough=True, collection=None) -> object names (a list, or a dict with "all" and roles)
    outline_views(names) -> [view, ...]  compare.py view dicts (photo, mask, objects, camera ...); optional
    FOOTAGE                           optional output folder (else video-local/footage/<today>-components/NAME)
Or call run() from another script (tools/demo_screens_toolkit.py does).

Output in <out>/: <name>-outline.png (the review sheet), <name>-outline.json and .md (scores, sizes),
the four stills and the compare data. The gate's threshold is 0.96 by default: a rough model is judged
on proportions; the full every-angle test after detailing is 0.98.

Plain Python redraws the sheet:  /opt/anaconda3/bin/python3 blender/tools/outline_check.py --sheet <json>
"""
import importlib.util
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, BLENDER_DIR)
from lib import compare  # noqa: E402

try:
    import bpy
except ImportError:
    bpy = None

GATE = 0.96


def _log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {msg}", flush=True)


def _quick_eevee(sc, w=960, h=600, samples=8):
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    try:
        sc.eevee.taa_render_samples = samples
    except AttributeError:
        pass
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.view_settings.view_transform = "AgX"


def stills(objs, out_dir, name, log=_log):
    """Front, right side, top (orthographic) and three-quarter (perspective) quick EEVEE stills of objs."""
    from lib import backdrops
    sc = bpy.context.scene
    lo, hi = compare.world_bbox(objs)
    c = (lo + hi) / 2
    size = hi - lo
    undo = compare.visible_only(objs)
    compare.ensure_studio()
    paths = {}
    aspect = 960 / 600
    cams = {
        "front": backdrops.view_camera("front", c, max(size.x, size.z * aspect) * 1.15, aspect, name="oc_front"),
        "side": backdrops.view_camera("right", c, max(size.y, size.z * aspect) * 1.15, aspect, name="oc_side"),
        "top": backdrops.view_camera("top", c, max(size.x, size.y * aspect) * 1.15, aspect, name="oc_top"),
        "three-quarter": backdrops.three_quarter_camera(c, max(size), aspect=aspect, name="oc_3q"),
    }
    cam0 = sc.camera
    _quick_eevee(sc)
    for k, cam in cams.items():
        sc.camera = cam
        p = os.path.join(out_dir, f"{name}-outline-{k}.png")
        sc.render.filepath = p
        t = time.time()
        bpy.ops.render.render(write_still=True)
        paths[k] = p
        log(f"outline still {k}: {time.time() - t:.1f} s")
    sc.camera = cam0
    undo()
    return paths, {"width_mm": round(size.x * 1000, 1), "depth_mm": round(size.y * 1000, 1),
                   "height_mm": round(size.z * 1000, 1)}


def run(name, build, views_fn=None, out_dir=None, names_fn=None, threshold=GATE, log=_log):
    """Build rough, render the four stills, score the reference views quickly, write the review sheet.
    build(rough=True) -> names (list or dict with "all"); views_fn(names) -> compare view dicts."""
    t0 = time.time()
    os.makedirs(out_dir, exist_ok=True)
    r = build(rough=True)
    names = names_fn() if names_fn else (r if isinstance(r, dict) else {"all": list(r)})
    allobjs = names.get("all") or sorted({n for v in names.values() for n in v})
    t_build = time.time() - t0
    paths, dims = stills(allobjs, out_dir, name, log)
    t_stills = time.time() - t0 - t_build
    roles = {}
    for k, v in names.items():
        if k != "all" and v:
            lo, hi = compare.world_bbox(v)
            if hi.x > lo.x:
                roles[k] = [round((hi - lo).x * 1000, 1), round((hi - lo).y * 1000, 1), round((hi - lo).z * 1000, 1)]
    entries = []
    if views_fn:
        for v in views_fn(names):
            v = dict(v)
            v["camera"] = dict(v.get("camera") or {}, quick=True)
            entries.append(compare.score_view(v, out_dir, look_engine="BLENDER_EEVEE", look_samples=8,
                                              threshold=v.get("outline_threshold", threshold), log=log))
    rep = {"component": name, "title": f"{name}: outline check", "threshold": threshold,
           "date": time.strftime("%Y-%m-%d %H:%M"), "views": entries, "stills": paths, "size_mm": dims,
           "roles_mm": roles, "seconds": {"build": round(t_build, 1), "stills": round(t_stills, 1),
                                          "total": round(time.time() - t0, 1)}}
    rep["test"] = compare.test(rep, threshold)
    jp = os.path.join(out_dir, f"{name}-outline.json")
    with open(jp, "w") as f:
        json.dump(rep, f, indent=1, default=str)
    md = compare.write_report(dict(rep), out_dir, f"{name}-outline")["md"]
    sheet = None
    py = compare.plain_python()
    if py:
        pr = subprocess.run([py, os.path.abspath(__file__), "--sheet", jp], capture_output=True, text=True)
        sheet = next((l.split(" ", 1)[1] for l in pr.stdout.splitlines() if l.startswith("SHEET ")), None)
        if sheet is None:
            print(pr.stdout, pr.stderr, flush=True)
    rep["sheet"] = sheet
    rep["paths"] = {"json": jp, "md": md}
    with open(jp, "w") as f:
        json.dump(rep, f, indent=1, default=str)
    log(f"outline check {name}: {'PASSED' if rep['test']['passed'] else 'NEEDS A LOOK'} in "
        f"{rep['seconds']['total']} s; sheet {sheet}")
    return rep


# ---------------------------------------------------------------------------
# the review sheet (plain Python)
# ---------------------------------------------------------------------------
def sheet(jp):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    rep = json.load(open(jp))
    font, small = compare._fonts()
    W = 1920
    tiles = []
    for e in rep["views"]:
        ph, rend, pm, rm = compare._layers(e)
        ea = np.asarray(ph.convert("L").convert("RGB")).astype(float) * 0.35 + 165
        for m, col in ((pm, (220, 40, 40)), (rm, (40, 90, 230))):
            mi = Image.fromarray((m * 255).astype(np.uint8))
            edge = np.asarray(mi.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))) > 0
            ea[edge] = col
        box = compare._box(pm, rm, *ph.size)
        tiles.append((e, Image.fromarray(ea.astype(np.uint8)).crop(box)))
    rows_v = (len(tiles) + 1) // 2
    H = 120 + 380 + 40 + rows_v * 450 + 60
    s = Image.new("RGB", (W, H), (246, 244, 238))
    d = ImageDraw.Draw(s)
    t = rep["test"]
    d.text((24, 14), f"{rep['title']}: {'PASSED' if t['passed'] else 'NEEDS A LOOK'} (gate {rep['threshold']})",
           fill=(29, 39, 51), font=font)
    sz = rep["size_mm"]
    roles = "   ".join(f"{k} {v[0]:.0f} x {v[1]:.0f} x {v[2]:.0f}" for k, v in rep.get("roles_mm", {}).items())
    d.text((24, 52), f"rough model {sz['width_mm']:.0f} wide x {sz['depth_mm']:.0f} deep x {sz['height_mm']:.0f} high "
           f"(mm)   {roles}", fill=(29, 39, 51), font=small)
    d.text((24, 80), f"built in {rep['seconds']['build']} s, four stills in {rep['seconds']['stills']} s, total "
           f"{rep['seconds']['total']} s. Approve the proportions before any detail.", fill=(29, 39, 51), font=small)
    x = 14
    for k in ("front", "side", "top", "three-quarter"):
        p = rep["stills"].get(k)
        if not p or not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        im.thumbnail((465, 330))
        d.text((x, 120), k, fill=(47, 109, 181), font=small)
        s.paste(im, (x, 150))
        x += 474
    y = 120 + 380 + 20
    for i, (e, im) in enumerate(tiles):
        im.thumbnail((930, 390))
        xx = 14 + (i % 2) * 950
        yy = y + (i // 2) * 450
        st = "PASS" if e["pass"] else ("EXPLAINED" if e.get("explain") else "FAIL")
        d.text((xx, yy), f"{e['name']}: IoU {e['iou']:.3f} {st}   (photo red, rough model blue)",
               fill=(29, 39, 51) if e["pass"] else (190, 40, 30), font=small)
        s.paste(im, (xx, yy + 32))
    out = os.path.splitext(jp)[0] + ".png"
    s.save(out)
    return out


def _load_component(path):
    spec = importlib.util.spec_from_file_location("component_under_check", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    if "--sheet" in sys.argv:
        print("SHEET", sheet(sys.argv[sys.argv.index("--sheet") + 1]))
    elif bpy is not None and "--" in sys.argv:
        a = sys.argv[sys.argv.index("--") + 1:]
        comp = _load_component(next(x for x in a if x.endswith(".py")))
        out = next((a[i + 1] for i, x in enumerate(a) if x == "--out"), None)
        thr = float(next((a[i + 1] for i, x in enumerate(a) if x == "--threshold"), GATE))
        name = getattr(comp, "NAME", "component")
        out = out or getattr(comp, "FOOTAGE", None) or os.path.join(
            BLENDER_DIR, "..", "video-local", "footage", time.strftime("%Y-%m-%d") + "-components", name)
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o)
        run(name, comp.build, getattr(comp, "outline_views", None), os.path.join(out, "outline"), threshold=thr)
        bpy.ops.wm.quit_blender()
    else:
        print(__doc__)
