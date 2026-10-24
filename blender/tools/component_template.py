"""TEMPLATE for a new room component. Copy it to blender/components/<name>.py, rename NAME, replace the
EXAMPLE (an Apple Studio Display, front only, so the template runs as it is) with the component.

Always headless (-b; the window only when the owner asks to watch):

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/components/<name>.py -- [stages] [--out DIR] [--cycles]

stages, in pipeline order (see blender/README.md, "Component pipeline"):
    outline   the 15-minute gate: build(rough=True), four quick EEVEE views, scores against the photos,
              one review sheet. STOP here until the owner or the coordinator approves the proportions.
    build     the detailed model: build(rough=False); saves blender/out/components/<name>.blend
    stills    hero, front, side, top, clay: EEVEE by default; --cycles renders them in Cycles through
              the render queue (one Cycles render on this Mac at a time)
    compare   the every-angle test (lib/compare.py): pass at 0.98 or `explain` why; writes the report
              (JSON, Markdown), per-angle 50/50 and outline sheets, the stacked photo-vs-model sheet
    export    rich GLB (bevels, all materials) and lite GLB (build(lite=True)); the lite bake is
              screens_render.export_lite's job: copy it and wrap the bake in renderqueue.slot()
default: build,stills,compare,export (outline is run on its own, first).

Output: video-local/footage/<date>-components/<NAME>/ (or --out), with NOTE.md started from the skeleton
below the first time.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(BLENDER_DIR, ".."))
sys.path.insert(0, BLENDER_DIR)
sys.path.insert(0, os.path.join(BLENDER_DIR, "tools"))

try:
    import bpy
except ImportError:          # plain Python can import the numbers (for a 2D blueprint sheet)
    bpy = None

# ---------------------------------------------------------------------------
# 1. constants, each with its source: OFFICIAL (maker's page or drawing), MEASURED (from an official photo,
#    scale from an official size: refs.mm_per_px_*), EST (estimated: say from what)
# ---------------------------------------------------------------------------
NAME = "template_example"
MM = 0.001
REF = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab", "03-top-screen")

W = 623 * MM            # OFFICIAL: Apple tech specs, VESA version 623 x 362 x 31 (SOURCES.md)
H = 362 * MM            # OFFICIAL
T = 20.5 * MM           # MEASURED: Apple's side diagram, body without the adapter (screens.py SD_T)
CORNER = 5.3 * MM       # MEASURED: front-screen-off.jpg at 0.254 mm/px
BEZEL = 13.0 * MM       # MEASURED: the black border, even all round
Z0 = 0.10               # EST: where it stands in this test scene (the room layout decides later)

PHOTOS = {
    "front": dict(photo=os.path.join(REF, "front-screen-off.jpg"), mask=0.8, crop=(0, 9999, 0, 1426),
                  official_width_mm=623.0),
}


# ---------------------------------------------------------------------------
# 2. build: rough (silhouettes only, from parts.py, minutes) or detailed; lite for the web
# ---------------------------------------------------------------------------
def build(rough=False, lite=False, collection=None):
    """Returns object names by role, plus "all". Rough: only what the silhouette needs."""
    from lib import parts as P
    sfx = "_lite" if lite else ""
    coll = collection or bpy.context.scene.collection
    mats = P.palette()
    names = {}
    body = P.rounded_panel("example_body" + sfx, W, H, T, r_corner=CORNER, r_front=0.0005 if not rough else 0.0,
                           r_back=0.003 if not rough else 0.0, lite=lite or rough, collection=coll,
                           mats={"body": mats["alu"]}, at=(0, 0, Z0 + H / 2))
    names["body"] = [body.name]
    if not rough:
        glass = P.rounded_panel("example_glass" + sfx, W - 0.0006, H - 0.0006, 0.0004, r_corner=CORNER - 0.0003,
                                lite=lite, collection=coll, mats={"body": mats["black"]},
                                at=(0, -0.0001, Z0 + H / 2))
        cam = P.knob("example_camera_dot" + sfx, 0.0015, 0.0002, lite=lite, collection=coll,
                     mats={"knob": mats["port"]}, at=(0, -0.00055, Z0 + H - 0.0056))
        names["glass"] = [glass.name, cam.name]
    names["all"] = [n for v in names.values() for n in v]
    return names


def outline_views(names):
    """The photos the silhouette is scored against (outline gate and compare test). A `placed` camera
    puts the photo at true scale (refs: mm per pixel from an official size; anchor bottom-centre)."""
    from lib import refs
    out = []
    for view, p in PHOTOS.items():
        m = refs.fill_holes(refs.mask(refs.load(p["photo"]), p["mask"], p.get("crop")))
        rec = refs.ref_record(p["photo"], refs.mm_per_px_extent(m, p["official_width_mm"], "x"),
                              refs.anchor_of(m, "bottom-centre"), (0.0, Z0 * 1000), view=view)
        out.append(dict(name=f"{NAME}-{view}", title=f"{NAME}: {view} (official photo) vs our model",
                        photo=p["photo"], mask=p["mask"], crop=p.get("crop"), objects=names["all"],
                        camera={"mode": "placed", "ref": rec}))
    return out


# ---------------------------------------------------------------------------
# 3. stages
# ---------------------------------------------------------------------------
NOTE_SKELETON = """# {name}: <what it is> (component, {date})

Built on its own at real size, away from the room layout. Rebuild (headless):

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/components/{name}.py

## What it is
- <product, exact model, colour; what is ours and what is the maker's>

## References and lens
- <photos used, which were lens-corrected (refs.fit_lens: k1, significant or not), which rectified>

## Outline check (the 15-minute gate)
- <date, scores per view, the sheet, who approved, what changed after it>

## Numbers (all in blender/components/{name}.py, each tagged OFFICIAL / MEASURED / EST)
| Part | Value | Source |
|---|---|---|

## Photo compare test (every angle, pass at 0.98 or explained)
<paste {name}-compare.md>

## Triangles and files
- rich GLB, lite GLB, render times

## What is approximate

## What went wrong
"""


def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {NAME}: {msg}", flush=True)


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")


def stage_outline(out):
    import outline_check
    clear()
    return outline_check.run(NAME, lambda rough=True: build(rough=True), outline_views, os.path.join(out, "outline"),
                             log=log)


def stage_build(out):
    clear()
    t = time.time()
    names = build()
    blend = os.path.join(BLENDER_DIR, "out", "components", f"{NAME}.blend")
    os.makedirs(os.path.dirname(blend), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    log(f"built in {time.time() - t:.1f} s, saved {blend}")
    return names


def stage_stills(out, names, cycles=False):
    from lib import backdrops, compare, renderqueue
    sc = bpy.context.scene
    compare.ensure_studio()
    lo, hi = compare.world_bbox(names["all"])
    c, size = (lo + hi) / 2, hi - lo
    cams = {"hero": backdrops.three_quarter_camera(c, max(size), name="still_hero"),
            "front": backdrops.view_camera("front", c, max(size.x, size.z * 16 / 9) * 1.15, name="still_front"),
            "side": backdrops.view_camera("right", c, max(size.y, size.z * 16 / 9) * 1.25 + 0.05, name="still_side"),
            "top": backdrops.view_camera("top", c, max(size.x, size.y * 16 / 9) * 1.15, name="still_top")}
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGB"
    sc.view_settings.view_transform = "AgX"
    if cycles:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 128
        sc.cycles.use_denoising = True
    else:
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = 32
    paths = {}
    for k, cam in list(cams.items()) + [("clay", cams["hero"])]:
        sc.camera = cam
        if k == "clay":
            from lib import looks
            looks.clay_on()
        p = os.path.join(out, f"{NAME}-{k}.png")
        sc.render.filepath = p
        if cycles:
            with renderqueue.slot(f"{NAME} {k}"):
                bpy.ops.render.render(write_still=True)
        else:
            bpy.ops.render.render(write_still=True)
        if k == "clay":
            from lib import looks
            looks.clay_off()
        paths[k] = p
    log(f"stills: {', '.join(paths)}")
    return paths


def stage_compare(out, names):
    from lib import compare
    rep = compare.run(outline_views(names), os.path.join(out, "compare"), NAME, log=log)
    log(f"compare test {'PASSED' if rep['test']['passed'] else 'FAILED'}: {rep['paths']['md']}")
    return rep["test"]


def _export(objs, path):
    from lib import run
    for o in bpy.data.objects:
        o.select_set(o.name in objs)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_cameras=False, export_lights=False, export_extras=False)
    return run.glb_stats(path)


def stage_export(out, names):
    d = os.path.join(BLENDER_DIR, "out", "components")
    os.makedirs(d, exist_ok=True)
    rich = _export(names["all"], os.path.join(d, f"{NAME}-rich.glb"))
    lite_names = build(lite=True)
    lite = _export(lite_names["all"], os.path.join(d, f"{NAME}-lite.glb"))
    log(f"GLB rich {rich['kb']} KB {rich['triangles']} tris; lite {lite['kb']} KB {lite['triangles']} tris")
    return {"rich": rich, "lite": lite}


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    st = next((x for x in a if not x.startswith("--") and not os.path.sep in x), "default")
    stages = ["build", "stills", "compare", "export"] if st == "default" else st.split(",")
    out = next((a[i + 1] for i, x in enumerate(a) if x == "--out"), None) or os.path.join(
        REPO, "video-local", "footage", time.strftime("%Y-%m-%d") + "-components", NAME)
    os.makedirs(out, exist_ok=True)
    note = os.path.join(out, "NOTE.md")
    if not os.path.exists(note):
        with open(note, "w") as f:
            f.write(NOTE_SKELETON.format(name=NAME, date=time.strftime("%Y-%m-%d")))
    rep = {"stages": stages}
    t0 = time.time()
    names = None
    if "outline" in stages:
        r = stage_outline(out)
        rep["outline"] = {"passed": r["test"]["passed"], "sheet": r.get("sheet")}
    if "build" in stages:
        names = stage_build(out)
    elif any(s in stages for s in ("stills", "compare", "export")):
        bpy.ops.wm.open_mainfile(filepath=os.path.join(BLENDER_DIR, "out", "components", f"{NAME}.blend"))
        names = {"all": [o.name for o in bpy.data.objects if o.type == "MESH" and not o.name.endswith("_lite")]}
    if "stills" in stages:
        rep["stills"] = stage_stills(out, names, "--cycles" in a)
    if "compare" in stages:
        rep["compare"] = stage_compare(out, names)
    if "export" in stages:
        rep["export"] = stage_export(out, names)
    rep["total_s"] = round(time.time() - t0, 1)
    with open(os.path.join(out, f"{NAME}-report.json"), "w") as f:
        json.dump(rep, f, indent=1, default=str)
    log(f"done in {rep['total_s']} s: {out}")


if __name__ == "__main__" and bpy is not None:
    main()
    bpy.ops.wm.quit_blender()
