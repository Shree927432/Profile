"""The MX Master 3S scan as a local base (decision 2026-10-26): clean, orient and scale the scan, then wrap our
own light quad shell onto it and save that shell (only the shell) to blender/assets/mouse/mx-master-3s-shell.json,
which desktop.py's build_mouse reads. The scan never goes into a GLB.

Scan: "Logitech MX Master 3S - Revopoint Mini 3D Scan" by Sircher, CC BY,
https://sketchfab.com/3d-models/logitech-mx-master-3s-revopoint-mini-3d-scan-9a82df69ffee4c6faa28f75e65ba192c
(local only: docs/moodboard/local/ai-lab/23-mouse/scan/mx-master-3s-scan.glb).

    B="/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python"
    $B blender/components/mouse_scan.py -- prep      import, keep the body, orient, scale -> out/components/mouse-scan-work.blend
    $B blender/components/mouse_scan.py -- shell     wrap the quad shell onto the working scan -> assets/mouse/...json

Frame (as desktop.py's mouse): origin on the desk under the top-view centre, nose +Y, thumb side -X, metres.
"""
import json
import math
import os
import sys
import time

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(BLENDER_DIR, ".."))
SCAN = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab", "23-mouse", "scan", "mx-master-3s-scan.glb")
WORK = os.path.join(BLENDER_DIR, "out", "components", "mouse-scan-work.blend")
SHELL = os.path.join(BLENDER_DIR, "assets", "mouse", "mx-master-3s-shell.json")
FOOT = os.path.join(REPO, "video-local", "footage", "2026-10-26-components", "desktop", "mouse-scan")
L, W, H = 124.9, 84.3, 51.0          # OFFICIAL (23-mouse/SOURCES.md), mm
MM = 0.001
CREDIT = ('"Logitech MX Master 3S - Revopoint Mini 3D Scan" by Sircher, CC BY, '
          "https://sketchfab.com/3d-models/logitech-mx-master-3s-revopoint-mini-3d-scan-9a82df69ffee4c6faa28f75e65ba192c")


def log(m):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} mouse_scan: {m}", flush=True)


def verts_np(o):
    v = np.empty(len(o.data.vertices) * 3, np.float64)
    o.data.vertices.foreach_get("co", v)
    return v.reshape(-1, 3)


def set_verts(o, v):
    o.data.vertices.foreach_set("co", v.astype(np.float32).ravel())
    o.data.update()


YAW = -4.0                            # degrees about Z after the principal axes (see prep)


def prep(flip=(1, 1, 1)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SCAN)
    ms = [o for o in bpy.data.objects if o.type == "MESH"]
    tris0 = sum(len(o.data.polygons) for o in ms)
    with bpy.context.temp_override(active_object=ms[0], selected_editable_objects=ms, selected_objects=ms):
        bpy.ops.object.join()
    o = ms[0]
    o.data.transform(o.matrix_world)
    o.parent = None
    o.matrix_world = Matrix()
    for e in [x for x in bpy.data.objects if x.type == "EMPTY"]:
        bpy.data.objects.remove(e)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.02)
    bm.to_mesh(o.data)
    bm.free()
    d = o.modifiers.new("dec", "DECIMATE")
    d.ratio = 400000 / max(len(o.data.polygons), 1)
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier="dec")
    log(f"joined {len(ms)} pieces, {tris0} tris -> decimated {len(o.data.polygons)}")
    # loose parts: keep the biggest (the body), report the strays
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = sorted([x for x in bpy.data.objects if x.type == "MESH"], key=lambda x: -len(x.data.polygons))
    body = parts[0]
    strays = [(x.name, len(x.data.polygons)) for x in parts[1:]]
    keep = [body] + [x for x in parts[1:] if len(x.data.polygons) > 0.05 * len(body.data.polygons)]
    for x in parts:
        if x not in keep:
            bpy.data.objects.remove(x)
    if len(keep) > 1:
        with bpy.context.temp_override(active_object=body, selected_editable_objects=keep, selected_objects=keep):
            bpy.ops.object.join()
    body.name = body.data.name = "scan_mouse"
    log(f"kept {len(keep)} parts ({len(body.data.polygons)} tris); dropped {len(strays) - len(keep) + 1} strays, "
        f"largest stray {strays[0] if strays else None}")
    # orient: principal axes (length -> Y, width -> X, the thinnest -> Z), then a fine search for the flattest Z
    v = verts_np(body)
    c = v.mean(0)
    ev, vec = np.linalg.eigh(np.cov((v - c).T))
    Rm = np.stack([vec[:, 1], vec[:, 2], vec[:, 0]])          # rows: new X, Y, Z
    if np.linalg.det(Rm) < 0:
        Rm[0] *= -1
    p = (v - c) @ Rm.T
    best = None
    for ax in np.radians(np.arange(-12, 12.1, 1.0)):
        for ay in np.radians(np.arange(-12, 12.1, 1.0)):
            r = Matrix.Rotation(ax, 3, "X") @ Matrix.Rotation(ay, 3, "Y")
            q = p @ np.array(r).T
            z = q[:, 2]
            ext = np.percentile(z, 99.9) - np.percentile(z, 0.1)
            if best is None or ext < best[0]:
                best = (ext, np.array(r))
    p = p @ best[1].T
    p *= np.array(flip, np.float64)
    # the principal axes lean with the thumb wing: a yaw fitted to Logitech's top view (silhouette IoU 0.921 -> 0.980,
    # the wheel, mode button and split then line up on one straight centre line as in top.png)
    a = math.radians(YAW)
    p = p @ np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]]).T
    lo, hi = np.percentile(p, 0.05, 0), np.percentile(p, 99.95, 0)
    raw = hi - lo
    s = L / raw[1]
    log(f"raw size (scan units) {raw.round(1)}; scale {s:.4f} to the official length")
    p = (p - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * s
    size = raw * s
    log(f"scaled size mm x {size[0]:.1f} (official {W}), y {size[1]:.1f} ({L}), z {size[2]:.1f} ({H})")
    set_verts(body, p * MM)
    rep = dict(source=CREDIT, tris_in=tris0, tris_work=len(body.data.polygons), strays=strays[:20],
               raw_size=raw.round(2).tolist(), scale=s, size_mm=size.round(2).tolist(),
               official_mm=[W, L, H], dev_pct=((size / np.array([W, L, H]) - 1) * 100).round(2).tolist())
    os.makedirs(FOOT, exist_ok=True)
    json.dump(rep, open(os.path.join(FOOT, "scan-prep.json"), "w"), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=WORK, compress=True)
    log(f"saved {WORK}: {rep['dev_pct']}")
    return body


def views(o, tag):
    """Quick Workbench views of an object: top, thumb side (-X), right side, nose (+Y), back."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = 640, 480
    sc.display.shading.light = "STUDIO"
    cd = bpy.data.cameras.new("v")
    cd.type, cd.ortho_scale = "ORTHO", 0.16
    cam = bpy.data.objects.new("v", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    for k, pos in {"top": (0, 0, 1), "thumb": (-1, 0, 0), "right": (1, 0, 0), "nose": (0, 1, 0), "back": (0, -1, 0)}.items():
        cam.location = Vector(pos) * 0.5 + Vector((0, 0, 0.025))
        up = "Y" if k != "top" else "Y"
        cam.rotation_euler = (Vector((0, 0, 0.025)) - cam.location).to_track_quat("-Z", "Y" if k == "top" else "Z").to_euler()
        if k != "top":
            cam.rotation_euler = (Vector((0, 0, 0.025)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(FOOT, f"{tag}-{k}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    st = a[0] if a else "prep"
    if st == "prep":
        f = tuple(int(x) for x in a[1].split(",")) if len(a) > 1 else (1, 1, 1)
        b = prep(f)
        views(b, "scan")
    elif st == "views":
        bpy.ops.wm.open_mainfile(filepath=WORK)
        views(bpy.data.objects["scan_mouse"], "scan")


# ---------------------------------------------------------------------------
# the shell: rays from a point inside the body, per vertical plane, onto a smoothed copy of the scan
# ---------------------------------------------------------------------------
C = (6.0, -5.0, 20.0)                 # mm: the ray centre inside the body (nose frame)
# features the shell bridges over (MEASURED on the scan's high-pass depth maps, nose frame, mm)
MASKS = [
    lambda x, y, z: abs(x - 10.8) < 5.4 and abs(y - 37.0) < 11.0 and z > 28.0,          # wheel slot and wheel
    lambda x, y, z: x < -12.0 and -7.5 < y < 13.5 and 32.5 < z < 50.0,                # thumb wheel in its pocket
    lambda x, y, z: abs(x - 10.6) < 8.5 and y > 40.0 and 2.5 < z < 12.5,                 # USB-C recess
]
RES = {"lite": (40, 3, 13), "rich": (120, 8, 34)}     # directions, band rows, body rows


def _sstep(a, b, v):
    t = min(max((v - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def band_z(x, y, lip_z):
    """The silver band's top (mm): 15.5 under the buttons at the nose, 10 round the right side and back;
    on the thumb wing it is the wing's lip (the whole underside of the wing is silver)."""
    z = 10.0 + 5.5 * _sstep(25.0, 50.0, y)
    w = _sstep(-14.0, -24.0, x) * _sstep(30.0, 18.0, y)
    return z * (1 - w) + max(z, lip_z) * w


def smoothed_bvh():
    from mathutils.bvhtree import BVHTree
    o = bpy.data.objects["scan_mouse"]
    d = o.modifiers.new("dec", "DECIMATE")
    d.ratio = 200000 / len(o.data.polygons)
    s = o.modifiers.new("smooth", "SMOOTH")
    s.factor, s.iterations = 0.5, 6
    dg = bpy.context.evaluated_depsgraph_get()
    return BVHTree.FromObject(o, dg), o


def profile(bvh, th, nphi=320):
    """One vertical plane through C at angle th: [(x, y, z) mm] from the base edge up to the top, the
    masked features bridged, the noise smoothed. Also the index of the widest sample."""
    cx, cy, cz = C
    dx, dy = math.cos(th), math.sin(th)
    hb = bvh.ray_cast(Vector((cx * MM, cy * MM, 4.0 * MM)), Vector((dx, dy, 0)))
    phis = np.linspace(math.radians(-70), math.radians(90), nphi)
    dist = np.full(nphi, np.nan)
    o = Vector((cx * MM, cy * MM, cz * MM))
    for k, ph in enumerate(phis):
        d = Vector((dx * math.cos(ph), dy * math.cos(ph), math.sin(ph)))
        h = bvh.ray_cast(o, d)
        if h[0] is None:
            continue
        p = h[0] / MM
        if p.z < 2.5 or any(m(p.x, p.y, p.z) for m in MASKS):
            continue
        dist[k] = h[3] / MM
    ok = ~np.isnan(dist)
    dist = np.interp(np.arange(nphi), np.nonzero(ok)[0], dist[ok])
    # noise: a small gaussian along the profile
    from math import exp
    g = np.array([exp(-(i / 1.5) ** 2 / 2) for i in range(-4, 5)])
    dp = np.pad(dist, 4, mode="edge")
    dist = np.convolve(dp, g / g.sum(), mode="valid")
    pts = [(cx + dx * r * math.cos(ph), cy + dy * r * math.cos(ph), cz + r * math.sin(ph)) for r, ph in zip(dist, phis)]
    pts = [p for p in pts if p[2] >= 2.5]
    if hb[0] is not None:
        b = hb[0] / MM
        pts = [(b.x, b.y, 4.0)] + [p for p in pts if p[2] > 4.0]
    pts = [(pts[0][0], pts[0][1], 1.2)] + pts
    return np.array(pts)


def resample(pts, n):
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n + 1)
    return np.stack([np.interp(t, s, pts[:, i]) for i in range(3)], 1)


def build_shell(bvh, res):
    nu, nb, nt = RES[res]
    cx, cy, _ = C
    # the top-view outline per direction (the widest sample) -> directions spaced evenly along it
    ths = np.linspace(0, 2 * math.pi, 360, endpoint=False)
    rim = []
    for th in ths:
        p = profile(bvh, th, 160)
        r = np.hypot(p[:, 0] - cx, p[:, 1] - cy)
        rim.append(p[int(np.argmax(r))][:2])
    rim = np.array(rim + [rim[0]])
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(rim, axis=0), axis=1))])
    want = np.linspace(0, s[-1], nu, endpoint=False)
    sel = np.interp(want, s, np.concatenate([ths, [2 * math.pi]]))
    band_rows, body_rows, pole = [], [], []
    for th in sel:
        p = profile(bvh, th)
        r = np.hypot(p[:, 0] - cx, p[:, 1] - cy)
        iw = int(np.argmax(r))
        wx, wy = p[iw, 0], p[iw, 1]
        wing = _sstep(-14.0, -24.0, wx) * _sstep(30.0, 18.0, wy)
        zb = band_z(wx, wy, 0.0) * (1 - wing) + p[iw, 2] * wing     # the wing: up to its lip, blended
        ib = next((i for i in range(1, len(p)) if p[i, 2] >= zb - 1e-6), 2)
        ib = min(ib, iw) if wing > 0.5 else ib
        band_rows.append(resample(p[:ib + 1], nb))
        body_rows.append(resample(p[ib:], nt))
        pole.append(p[-1])
    band = np.stack(band_rows)          # (nu, nb + 1, 3)
    body = np.stack(body_rows)          # (nu, nt + 1, 3)
    body[:, -1] = np.mean(pole, 0)
    G = np.concatenate([band, body[:, 1:]], 1)     # one grid: rows 0 (desk) .. nb (band edge) .. top pole
    G = relax(bvh, G, nb)
    G = calm(G, nb)
    G = pocket(G)
    return G[:, :nb + 1].copy(), G[:, nb:].copy()


POCKET = (-3.5, 41.8, 33.0, 9.0, 3.0)   # the thumb wheel's pocket: y, z, length, height, depth (mm; scan, closeup-thumb-area.jpg)


def pocket(G):
    """Press the thumb wheel's pocket into the wall: a stadium dent, deepest inside, eased out over 1.5 mm."""
    py, pz, pl, ph, dep = POCKET
    half = pl / 2 - ph / 2
    inward = np.array([0.75, 0.0, -0.66])
    for i in range(G.shape[0]):
        for j in range(1, G.shape[1] - 1):
            x, y, z = G[i, j]
            if x > -12.0:
                continue
            d = math.hypot(max(abs(y - py) - half, 0.0), z - pz) - ph / 2
            f = _sstep(1.5, -1.0, d)
            if f > 0:
                G[i, j] = G[i, j] + inward * dep * f
    return G


def calm(G, nb, iters=12, k=0.5):
    """The scan is rough between the left button and the thumb wing (button gaps, the side buttons' edges):
    plain smoothing there, no re-projection, eased in and out of the region."""
    nu, nk, _ = G.shape
    w = np.zeros((nu, nk))
    for i in range(nu):
        for j in range(1, nk - 1):
            x, y, z = G[i, j]
            if j != nb:
                w[i, j] = _sstep(-6.0, -14.0, x) * _sstep(-2.0, 6.0, y) * _sstep(52.0, 44.0, y) * _sstep(10.0, 16.0, z)
    for _ in range(iters):
        L = G.copy()
        L[:, 1:-1] = 0.25 * (np.roll(G, 1, 0)[:, 1:-1] + np.roll(G, -1, 0)[:, 1:-1] + G[:, :-2] + G[:, 2:])
        G = G + (k * w)[..., None] * (L - G)
    return G


def masked(p):
    return any(m(*p) for m in MASKS)


def relax(bvh, G, nb, iters=20, k=0.5, reach=1.2):
    """Smooth the grid (the noise, the jagged rays) and put it back on the smoothed scan: a vertex is
    re-projected to the nearest scan point only when that point is within `reach` mm and not on a masked
    feature, so holes and the thumb wheel stay bridged. The desk row stays on the desk, the pole stays."""
    nu, nk, _ = G.shape
    for _ in range(iters):
        L = G.copy()
        L[:, 1:-1] = 0.25 * (np.roll(G, 1, 0)[:, 1:-1] + np.roll(G, -1, 0)[:, 1:-1] + G[:, :-2] + G[:, 2:])
        for r in (0, nb):           # the desk row and the band edge: smoothed along themselves only
            L[:, r] = 0.5 * (np.roll(G, 1, 0)[:, r] + np.roll(G, -1, 0)[:, r])
        L[:, 0, 2] = 1.2
        N = G + k * (L - G)
        N[:, -1] = G[:, -1]
        for i in range(nu):
            for j in range(1, nk - 1):
                q = Vector(N[i, j] * MM)
                h = bvh.find_nearest(q)
                if h[0] is None:
                    continue
                p = h[0] / MM
                if (h[0] - q).length / MM < reach and not masked((p.x, p.y, p.z)) and p.z > 2.0:
                    N[i, j] = (p.x, p.y, p.z)
        G = N
    return G


def grid_mesh(arr, cap_bottom=False, pole_top=False):
    nu, nk, _ = arr.shape
    if pole_top:
        vs = arr[:, :-1].reshape(-1, 3).tolist() + [arr[0, -1].tolist()]
        nk1 = nk - 1
    else:
        vs = arr.reshape(-1, 3).tolist()
        nk1 = nk
    idx = lambda i, k: (i % nu) * nk1 + k
    faces = []
    for i in range(nu):
        for k in range(nk1 - 1):
            faces.append([idx(i, k), idx(i + 1, k), idx(i + 1, k + 1), idx(i, k + 1)])
    if pole_top:
        P = len(vs) - 1
        for i in range(nu):
            faces.append([idx(i, nk1 - 1), idx(i + 1, nk1 - 1), P])
    if cap_bottom:
        faces.append([idx(i, 0) for i in reversed(range(nu))])
    return [[round(c, 3) for c in v] for v in vs], faces


def shell():
    bpy.ops.wm.open_mainfile(filepath=WORK)
    bvh, scan = smoothed_bvh()
    out = {"source": CREDIT, "note": "Our own quad shell, wrapped onto the scan (mm, nose +Y, thumb -X, desk z=0). "
           "mouse_scan.py writes it; desktop.py reads it.", "centre": C}
    for res in ("lite", "rich"):
        band, body = build_shell(bvh, res)
        bv, bf = grid_mesh(band, cap_bottom=True)
        tv, tf = grid_mesh(body, pole_top=True)
        out[res] = {"band": {"v": bv, "f": bf}, "body": {"v": tv, "f": tf}}
        ntri = sum(len(f) - 2 for f in bf + tf)
        log(f"{res}: band {len(bf)} faces, body {len(tf)} faces, {ntri} triangles")
    os.makedirs(os.path.dirname(SHELL), exist_ok=True)
    json.dump(out, open(SHELL, "w"), separators=(",", ":"))
    log(f"wrote {SHELL} ({os.path.getsize(SHELL) // 1024} KB)")


if __name__ == "__main__" and "shell" in sys.argv:
    shell()
