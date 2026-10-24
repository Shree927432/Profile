"""pc: close-up pairs (photo crop beside render crop). The fitted compare cameras are rendered in Cycles at
the photo's size (x2 for Lian Li's small 600 px render), then cropped the same; plus four similar-angle
pairs from photos that have no fitted camera (top corner, front I/O, rear chamber, the GPU and bottom
fans in a build). The sheet is drawn by desk_blueprint.py's closeups() (plain Python)."""
import json
import os
import subprocess
import time

import bpy

import pc as K
from lib import compare, renderqueue

# (view, scale, [(name, title, None, box in the photo's pixels)])
SETS = [
    ("case-official-3q", 2, [
        ("glass-corner", "the glass corner (no pillar) and the top glass", None, (190, 25, 420, 170)),
        ("io-foot", "the right foot with the front I/O", None, (395, 470, 560, 560)),
    ]),
    ("case-front", 1, [
        ("front-io", "front I/O on the right foot, the feet and the gap", None, (620, 900, 1300, 1050)),
        ("front-top", "the front glass's top edge and the pillar", None, (900, 80, 1300, 300)),
    ]),
    ("case-glass-side", 1, [
        ("rear-slots", "the rear frame and expansion slots, through the side glass", None, (470, 480, 720, 880)),
        ("side-front", "the front glass edge and the side fan bracket", None, (1150, 100, 1440, 520)),
    ]),
    ("case-back-3q", 1, [
        ("rear-panel", "rear panel: I/O cut-out, slots, PSU bracket", None, (940, 60, 1310, 960)),
    ]),
    ("gpu-front", 1, [
        ("gpu-fan", "the card's fan and its well", None, (250, 50, 700, 500)),
        ("gpu-x", "the X and the wells' lips", None, (680, 40, 990, 515)),
        ("gpu-fingers", "the PCIe edge and the bracket", None, (225, 440, 840, 640)),
    ]),
    ("gpu-back", 1, [
        ("gpu-backplate", "the backplate's X and fin windows", None, (650, 135, 1015, 610)),
    ]),
    ("gpu-3q-end", 1, [
        ("gpu-lightbar", "the top edge's far end: where the lit lettering is, our plain light bar", None,
         (700, 860, 1000, 1110)),
        ("gpu-socket", "the top edge: slits and the power socket", None, (330, 700, 760, 960)),
    ]),
]

EXTRA = [  # (photo, box, our still, title)
    ("top-corner.jpg", (150, 60, 1500, 1078), "pc-glass-corner.png", "glass corner and top (KitGuru, empty case)"),
    ("detail-io.jpg", (550, 380, 1300, 700), "pc-io.png", "front I/O on the right foot (KitGuru)"),
    ("rear-chamber.jpg", (395, 55, 1475, 1010), "pc-rear-chamber.png", "the rear chamber, right panel off (KitGuru's build)"),
    ("build-2-gpu-fans.jpg", (230, 0, 1700, 900), "pc-fan.png", "the card over the bottom fans (KitGuru's build: a 3.5-slot Gigabyte card; ours is the 2-slot FE)"),
]


def flat(photo):
    """The cut-out on the page's light grey (for crops)."""
    from lib import refs
    import numpy as np
    out = photo.replace("-cut.png", "-flat.png")
    if os.path.exists(out):
        return out
    a = refs.load(photo)
    bg = np.array([0.91, 0.914, 0.925])
    rgb = a[..., :3] * a[..., 3:4] + bg * (1 - a[..., 3:4])
    refs.save(rgb, out)
    return out


def render_view(R, view, scale, out_png):
    sc = bpy.context.scene
    e = compare.score_view(dict(view), os.path.join(K.FOOTAGE, "closeups"), look_engine=None, log=R.log)
    undo = None
    if view["name"].startswith("gpu") and view.get("prepare"):
        undo = view["prepare"]()
    cam = bpy.data.objects.get("cmp_cam") if e["camera_mode"] in ("fit", "free") else bpy.data.objects.get("cmp_cam_ortho")
    sc.camera = cam
    from lib import refs
    H, W = refs.load(view["photo"]).shape[:2]
    sc.render.resolution_x, sc.render.resolution_y = W * scale, H * scale
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGBA"
    sc.render.engine = "CYCLES"
    R.gpu()
    sc.cycles.samples = 16 if R.QUICK else 128
    sc.cycles.use_denoising = True
    sc.render.filepath = out_png
    fl = bpy.data.objects["still_floor"]
    fl.hide_render = True
    hide = compare.visible_only(view["objects"])          # only the view's own objects (no case glass round the card)
    with renderqueue.slot(f"pc closeup {view['name']}"):
        t = time.time()
        bpy.ops.render.render(write_still=True)
    hide()
    R.log(f"close-up render {view['name']}: {time.time() - t:.1f} s")
    fl.hide_render = False
    sc.render.film_transparent = False
    if undo:
        undo()
    return e


def stage_closeups(R):
    d = os.path.join(K.FOOTAGE, "closeups")
    os.makedirs(d, exist_ok=True)
    R.show(R.roles()["pc_all"] + ["still_floor"])
    views = {v["name"]: v for v in K.outline_views(R.roles())}
    sets = []
    for name, scale, crops in SETS:
        v = views[name]
        rp = os.path.join(d, f"render-{name}.png")
        e = render_view(R, v, scale, rp)
        ph = e["photo"]
        if name.startswith("gpu"):
            ph = flat(ph)
        sets.append({"photo": ph, "transform": e["transform"], "render": rp, "render_scale": scale,
                     "left": "reference (crop)", "crops": crops})
    extra = []
    for photo, box, still, title in EXTRA:
        rp = os.path.join(K.FOOTAGE, still)
        if not os.path.exists(rp):
            continue
        extra.append(dict(title=title, left="reference photo (crop)", right="our render, a similar angle (not fitted)",
                          photo=os.path.join(K.REF_CASE, photo), box=list(box), render=rp, rbox=None))
    spec = {"sets": sets, "extra": extra, "out": os.path.join(K.FOOTAGE, "pc-closeups.jpg")}
    sp = os.path.join(d, "closeups.json")
    with open(sp, "w") as f:
        json.dump(spec, f, indent=1)
    r = subprocess.run([compare.plain_python(), os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                             "desk_blueprint.py"), "closeups", sp],
                       capture_output=True, text=True)
    print(r.stdout[-1500:], r.stderr[-1500:], flush=True)
    R.log(f"close-up sheet {spec['out']}")
