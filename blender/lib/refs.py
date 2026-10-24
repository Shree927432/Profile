"""Reference photos: load, lens-correct, rectify, scale. numpy only, so it runs in Blender's Python and
in plain Python alike.

    numpy   required (Blender 5.2 ships 2.3; /opt/anaconda3 has 1.26)
    Pillow  used for image files when present (/opt/anaconda3, system python3); inside Blender,
            which has no Pillow, images go through bpy.data.images instead. No scipy, no OpenCV.

Image arrays are float32, H x W x 4 (RGBA, 0..1, not linearised), row 0 at the TOP, like the file.
Pixel coordinates are (x, y) with y down and the pixel centre at +0.5.

Lens model (one or two radial terms, the Number One fix generalised):

    x_u = c + (x_d - c) * (1 + k1 r^2 + k2 r^4),   r = |x_d - c| / half_diagonal

so k1 = +0.02 pushes the frame's corners out 2 %: barrel distortion corrects with k1 > 0,
pincushion with k1 < 0. Fit it from edges that are straight in the world (fit_lens(lines=...)), or from
points with known flat positions (fit_lens(points=..., plane=...), a homography and the lens terms fitted
together). Save the corrected image with undistort_image(): next to the original with a suffix (or in
out_dir), plus a .json sidecar; the original is never written to.

Typical use (plain Python or Blender):

    from lib import refs
    img = refs.load(photo)
    lines = [refs.edge_points(img, (12, 40), (20, 600)), refs.edge_points(img, (700, 30), (690, 610))]
    lens = refs.fit_lens(img.shape, lines=lines, terms=1)
    fixed = refs.undistort_image(photo, lens, out_dir=FOOTAGE)      # photo-lens.jpg + photo-lens.json
    s = refs.mm_per_px_between((x0, y0), (x1, y1), 623.0)             # official 623 mm between two points
"""
import json
import math
import os

import numpy as np

try:
    from PIL import Image as _PIL
except ImportError:                 # Blender's Python
    _PIL = None


# ---------------------------------------------------------------------------
# image I/O
# ---------------------------------------------------------------------------
def load(path):
    """RGBA float32 array, row 0 at the top."""
    if _PIL is not None:
        im = _PIL.open(path).convert("RGBA")
        return np.asarray(im, dtype=np.float32) / 255.0
    import bpy
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return np.ascontiguousarray(px.reshape(h, w, 4)[::-1])


def save(arr, path, quality=92):
    """Write an H x W x 3/4 float (0..1) or uint8 array. JPEG drops alpha."""
    a = np.asarray(arr)
    if a.dtype != np.uint8:
        a = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
    if a.ndim == 2:
        a = np.repeat(a[..., None], 3, -1)
    jpg = path.lower().endswith((".jpg", ".jpeg"))
    if _PIL is not None:
        im = _PIL.fromarray(a[..., :3] if jpg else a)
        im.save(path, quality=quality) if jpg else im.save(path)
        return path
    import bpy
    h, w = a.shape[:2]
    if a.shape[2] == 3:
        a = np.concatenate([a, np.full((h, w, 1), 255, np.uint8)], -1)
    im = bpy.data.images.new("refs_save", w, h, alpha=True)
    im.pixels.foreach_set((a[::-1].astype(np.float32) / 255.0).ravel())
    im.filepath_raw = path
    im.file_format = "JPEG" if jpg else "PNG"
    im.save()
    bpy.data.images.remove(im)
    return path


def derived_path(path, suffix, out_dir=None, ext=None, overwrite=False):
    """`<stem><suffix><ext>` next to `path` (or in out_dir). Never the original; an existing derived file
    is kept unless overwrite=True (then -2, -3 ... are not used either: it is replaced)."""
    stem, e = os.path.splitext(os.path.basename(path))
    d = out_dir or os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, stem + suffix + (ext or e))
    if os.path.abspath(out) == os.path.abspath(path):
        raise ValueError("refusing to write over the original reference")
    if os.path.exists(out) and not overwrite:
        k = 2
        while os.path.exists(os.path.join(d, f"{stem}{suffix}-{k}{ext or e}")):
            k += 1
        out = os.path.join(d, f"{stem}{suffix}-{k}{ext or e}")
    return out


def luminance(img):
    return img[..., 0] * 0.299 + img[..., 1] * 0.587 + img[..., 2] * 0.114


def sample(img, x, y):
    """Bilinear sample of img (H x W x C or H x W) at float pixel coords (pixel centres at +0.5).
    Outside the frame: zeros (alpha 0)."""
    H, W = img.shape[:2]
    xf = np.asarray(x, np.float64) - 0.5
    yf = np.asarray(y, np.float64) - 0.5
    x0 = np.floor(xf).astype(np.int64)
    y0 = np.floor(yf).astype(np.int64)
    fx, fy = xf - x0, yf - y0
    out = 0.0
    inside = (xf >= -0.5) & (yf >= -0.5) & (xf <= W - 0.5) & (yf <= H - 0.5)
    for dx, dy, wgt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi = np.clip(x0 + dx, 0, W - 1)
        yi = np.clip(y0 + dy, 0, H - 1)
        v = img[yi, xi]
        out = out + (v * wgt[..., None] if img.ndim == 3 else v * wgt)
    return out * (inside[..., None] if img.ndim == 3 else inside)


# ---------------------------------------------------------------------------
# straight edges: snap points to an edge the caller roughly marks
# ---------------------------------------------------------------------------
def edge_points(img, p0, p1, n=40, search=10.0, end_trim=0.04, robust=True):
    """Points on the strongest edge near the segment p0-p1 (pixels). For each of n samples along it,
    the luminance profile across it (+-search px) is differentiated and the peak taken to sub-pixel.
    Returns an (m, 2) array; samples with a weak edge are dropped and, with robust, samples that
    jumped to a neighbouring edge (a parabola through the offsets, trimmed)."""
    lum = luminance(img) if img.ndim == 3 else img
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    t_hat = d / L
    nrm = np.array([-t_hat[1], t_hat[0]])
    ts = np.linspace(end_trim, 1 - end_trim, n)
    offs = np.arange(-search, search + 0.25, 0.5)
    base = p0[None] + ts[:, None] * d[None]
    P = base[:, None, :] + offs[None, :, None] * nrm[None, None, :]
    prof = sample(lum, P[..., 0], P[..., 1])
    gs = np.gradient(prof, axis=1)
    # one edge, one polarity (dark-to-light or light-to-dark across the line): the sign most samples'
    # strongest step has; then, per sample, the strong peak nearest to the line the caller drew
    pol = np.sign(np.median(gs[np.arange(n), np.abs(gs).argmax(1)])) or 1.0
    g = np.maximum(pol * gs, 0.0)
    rowmax = g.max(1)
    floor = 0.25 * np.median(rowmax)
    keep, o = [], []
    for i in range(n):
        gi = g[i]
        peaks = [j for j in range(1, len(offs) - 1)
                 if gi[j] >= gi[j - 1] and gi[j] > gi[j + 1] and gi[j] >= max(0.35 * rowmax[i], floor)]
        if not peaks:
            continue
        ki = min(peaks, key=lambda j: abs(offs[j]))
        a, b, c = gi[ki - 1], gi[ki], gi[ki + 1]
        den = a - 2 * b + c
        sub = 0.5 * (a - c) / den if abs(den) > 1e-9 else 0.0
        keep.append(i)
        o.append(offs[ki] + sub * 0.5)
    keep, o = np.array(keep), np.array(o)
    if robust and len(keep) >= 6:
        # the edge is a smooth curve across the segment (a line bowed by the lens): fit a parabola to the
        # offsets and drop samples that snapped to some other edge, a few times over
        t = ts[keep]
        ok = np.ones(len(t), bool)
        for _ in range(5):
            cf = np.polyfit(t[ok], o[ok], 2)
            r = np.abs(o - np.polyval(cf, t))
            tol = max(0.8, 3.0 * np.median(r[ok]))
            ok = r < tol
            if ok.sum() < 6:
                break
        keep, o = keep[ok], o[ok]
    return base[keep] + o[:, None] * nrm[None]


def line_residuals(pts):
    """Perpendicular distances of points to their own total-least-squares line."""
    c = pts.mean(0)
    _, _, vt = np.linalg.svd(pts - c)
    return (pts - c) @ vt[1]


# ---------------------------------------------------------------------------
# lens model
# ---------------------------------------------------------------------------
def lens_model(shape, k1=0.0, k2=0.0, centre=None):
    H, W = shape[:2]
    c = centre if centre is not None else (W / 2.0, H / 2.0)
    return {"k1": float(k1), "k2": float(k2), "centre": [float(c[0]), float(c[1])],
            "norm": float(math.hypot(W, H) / 2.0), "size": [int(W), int(H)]}


def undistort_points(pts, lens):
    pts = np.asarray(pts, float)
    c = np.asarray(lens["centre"])
    d = pts - c
    r2 = (d ** 2).sum(-1, keepdims=True) / lens["norm"] ** 2
    return c + d * (1 + lens["k1"] * r2 + lens["k2"] * r2 ** 2)


def distort_points(pts, lens, iters=12):
    """Inverse of undistort_points (fixed-point iteration; converges for |k| well under 0.5)."""
    pts = np.asarray(pts, float)
    c = np.asarray(lens["centre"])
    du = pts - c
    dd = du.copy()
    for _ in range(iters):
        r2 = (dd ** 2).sum(-1, keepdims=True) / lens["norm"] ** 2
        dd = du / (1 + lens["k1"] * r2 + lens["k2"] * r2 ** 2)
    return c + dd


def _lm(fun, p0, iters=60, eps=1e-6):
    """Small Levenberg-Marquardt with a numeric Jacobian (no scipy in Blender)."""
    p = np.asarray(p0, float).copy()
    lam = 1e-3
    r = fun(p)
    cost = (r ** 2).sum()
    for _ in range(iters):
        J = np.empty((len(r), len(p)))
        for j in range(len(p)):
            h = eps * max(1.0, abs(p[j]))
            q = p.copy()
            q[j] += h
            J[:, j] = (fun(q) - r) / h
        A = J.T @ J
        g = J.T @ r
        improved = False
        for _ in range(10):
            step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-12), -g)
            q = p + step
            rq = fun(q)
            cq = (rq ** 2).sum()
            if cq < cost:
                p, r, cost = q, rq, cq
                lam = max(lam / 3, 1e-9)
                improved = True
                break
            lam *= 4
        if not improved or np.abs(step).max() < 1e-10:
            break
    return p, r


def fit_lens(shape, lines=None, points=None, plane=None, terms=1, centre=None):
    """Fit k1 (terms=1) or k1 and k2 (terms=2).

    lines   list of (m, 2) pixel arrays, each on an edge that is straight in the world
            (edge_points() makes them). Straightness alone fixes the radial terms.
    points, plane
            (n, 2) pixels and their (n, 2) positions on a flat object in mm (n >= 6 for one term);
            a homography and the lens terms are fitted together, as for Number One.
    Returns a lens dict with rms_before / rms_after (px), `significant` (False: the fit only chases
    the edges' noise; leave the photo alone) and, with points, the homography H (mm -> undistorted px)."""
    lens = lens_model(shape, centre=centre)
    lines = [np.asarray(l, float) for l in (lines or []) if len(l) >= 3]
    have_pts = points is not None and plane is not None
    if have_pts:
        points, plane = np.asarray(points, float), np.asarray(plane, float)

    def resid(p):
        lens["k1"] = p[0]
        lens["k2"] = p[1] if terms > 1 else 0.0
        # residuals in the photo's own pixels: divided by each line's magnification, or the fit would
        # shrink the frame (k1 -> -1) to make every distance small
        out = []
        for l in lines:
            u = undistort_points(l, lens)
            mag = np.linalg.norm(u[-1] - u[0]) / max(1e-9, np.linalg.norm(l[-1] - l[0]))
            out.append(line_residuals(u) / mag)
        if have_pts:
            Hm = np.append(p[terms:], 1.0).reshape(3, 3)
            q = apply_h(Hm, plane)
            out.append((q - undistort_points(points, lens)).ravel())
        return np.concatenate(out)

    p0 = [0.0] * terms
    if have_pts:
        p0 += list((homography(plane, points) / homography(plane, points)[2, 2]).ravel()[:8])
    r0 = resid(np.array(p0, float))
    p, r = _lm(resid, p0)
    lens["k1"] = float(p[0])
    lens["k2"] = float(p[1]) if terms > 1 else 0.0
    nl = sum(len(l) for l in lines)

    def rms(v):
        return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
    lens["rms_before_px"] = rms(r0[:nl]) if lines else rms(r0)
    lens["rms_after_px"] = rms(r[:nl]) if lines else rms(r)
    lens["max_after_px"] = float(np.abs(r).max()) if len(r) else 0.0
    lens["kind"] = "barrel" if lens["k1"] > 0 else "pincushion"
    # is the bend real? It must take a clear share of the edges' scatter away (a fifth, and 0.3 px),
    # or it is fitting the edges' own noise and the photo is better left as it is
    gain = lens["rms_before_px"] - lens["rms_after_px"]
    lens["significant"] = bool(gain > 0.3 and lens["rms_after_px"] < 0.8 * lens["rms_before_px"])
    if not lens["significant"]:
        lens["advice"] = "no lens correction: the fit does not beat the edges' noise; use the photo as it is"
    lens["corner_shift_pct"] = round(100 * (lens["k1"] + lens["k2"]), 3)
    if have_pts:
        lens["H"] = np.append(p[terms:], 1.0).reshape(3, 3).tolist()
    return lens


def undistort_image(path_or_img, lens, out_path=None, out_dir=None, suffix="-lens", overwrite=False, src=None):
    """Resample the photo through the lens model, same size and centre. Writes the image and a .json
    sidecar (the lens, the source) and returns the new path; with an array in and no out_path,
    returns the array. The original file is never touched."""
    if isinstance(path_or_img, str):
        src = path_or_img
        img = load(src)
    else:
        img = path_or_img
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    pu = np.stack([xx + 0.5, yy + 0.5], -1).reshape(-1, 2)
    pd = distort_points(pu, lens)
    out = sample(img, pd[:, 0], pd[:, 1]).reshape(H, W, img.shape[2]).astype(np.float32)
    if out_path is None and src is None:
        return out
    if out_path is None:
        out_path = derived_path(src, suffix, out_dir, overwrite=overwrite)
    save(out, out_path)
    with open(os.path.splitext(out_path)[0] + ".json", "w") as f:
        json.dump({"source": src, "kind": "lens-corrected", "lens": lens}, f, indent=1)
    return out_path


# ---------------------------------------------------------------------------
# homography and rectification
# ---------------------------------------------------------------------------
def homography(src, dst):
    """3 x 3 H with dst ~ H @ src, from four or more point pairs (normalised DLT)."""
    src, dst = np.asarray(src, float), np.asarray(dst, float)
    assert len(src) >= 4 and len(src) == len(dst), "four or more point pairs"

    def norm(p):
        c = p.mean(0)
        s = math.sqrt(2) / max(1e-12, np.sqrt(((p - c) ** 2).sum(1)).mean())
        return np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1]])
    Ts, Td = norm(src), norm(dst)
    s = apply_h(Ts, src)
    d = apply_h(Td, dst)
    A = []
    for (x, y), (u, v) in zip(s, d):
        A.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        A.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, vt = np.linalg.svd(np.array(A))
    Hn = vt[-1].reshape(3, 3)
    Hm = np.linalg.inv(Td) @ Hn @ Ts
    return Hm / Hm[2, 2]


def apply_h(Hm, pts):
    pts = np.asarray(pts, float)
    q = np.c_[pts, np.ones(len(pts))] @ np.asarray(Hm).T
    return q[:, :2] / q[:, 2:3]


def rectify(path_or_img, src_px, dst_mm, mm_per_px=0.5, bounds_mm=None, lens=None, out_path=None,
            out_dir=None, suffix="-rect", overwrite=False):
    """Map a photographed flat face onto a true-scale, square-on image.

    src_px    four or more pixel points in the photo (as photographed, distorted if lens is given)
    dst_mm    the same points on the face in mm, x right and y UP (a front view: x and z)
    bounds_mm (x0, y0, x1, y1) of the output; default: the dst points plus 10 %
    lens      a fit_lens() model: undistorted on the fly, one resample in all
    The output image has row 0 at the top (y = y1). Writes `<stem>-rect.png` and a sidecar with
    mm_per_px and origin_mm (the mm point of the top-left pixel corner), which backdrops.add() reads.
    Returns (path or array, info)."""
    src = path_or_img if isinstance(path_or_img, str) else None
    img = load(src) if src else path_or_img
    sp = np.asarray(src_px, float)
    if lens is not None:
        sp = undistort_points(sp, lens)
    dm = np.asarray(dst_mm, float)
    Hm = homography(dm, sp)                    # mm -> (undistorted) photo px
    if bounds_mm is None:
        lo, hi = dm.min(0), dm.max(0)
        pad = 0.1 * (hi - lo)
        bounds_mm = (lo[0] - pad[0], lo[1] - pad[1], hi[0] + pad[0], hi[1] + pad[1])
    x0, y0, x1, y1 = bounds_mm
    W = int(round((x1 - x0) / mm_per_px))
    Hh = int(round((y1 - y0) / mm_per_px))
    yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float64)
    mm = np.stack([x0 + (xx + 0.5) * mm_per_px, y1 - (yy + 0.5) * mm_per_px], -1).reshape(-1, 2)
    p = apply_h(Hm, mm)
    if lens is not None:
        p = distort_points(p, lens)
    out = sample(img, p[:, 0], p[:, 1]).reshape(Hh, W, img.shape[2]).astype(np.float32)
    resid = apply_h(Hm, dm) - sp
    info = {"source": src, "kind": "rectified", "mm_per_px": float(mm_per_px), "origin_mm": [float(x0), float(y1)],
            "size": [W, Hh], "H_mm_to_px": Hm.tolist(), "rms_px": float(np.sqrt((resid ** 2).sum(1).mean())),
            "lens": lens}
    if src is None and out_path is None:
        return out, info
    if out_path is None:
        out_path = derived_path(src, suffix, out_dir, ext=".png", overwrite=overwrite)
    save(out, out_path)
    with open(os.path.splitext(out_path)[0] + ".json", "w") as f:
        json.dump(info, f, indent=1)
    return out_path, info


# ---------------------------------------------------------------------------
# scale
# ---------------------------------------------------------------------------
def mm_per_px_between(p0, p1, mm):
    """Scale from two pixel points a known official distance apart (on a square-on view)."""
    return float(mm) / float(np.linalg.norm(np.asarray(p1, float) - np.asarray(p0, float)))


def mm_per_px_extent(mask, mm, axis="x"):
    """Scale from a silhouette's full width (axis x) or height (axis y) and its official size."""
    x0, x1, y0, y1 = bbox(mask)
    return float(mm) / float((x1 - x0 + 1) if axis == "x" else (y1 - y0 + 1))


def ref_record(path, mm_per_px, anchor_px, anchor_mm, view="front", note=""):
    """Everything backdrops.add() and compare need to place a photo at true scale: the image, its scale,
    and one pixel point whose model position (mm, in the view's own right/up axes) is known."""
    return {"image": path, "mm_per_px": float(mm_per_px), "anchor_px": [float(a) for a in anchor_px],
            "anchor_mm": [float(a) for a in anchor_mm], "view": view, "note": note}


# ---------------------------------------------------------------------------
# silhouettes (the compare's photo side; shared with compare.py)
# ---------------------------------------------------------------------------
def mask(img, mode="alpha", crop=None):
    """Silhouette: mode 'alpha' (alpha > 0.5) or a float threshold (darker than it on a light page).
    crop (x0, x1, y0, y1) keeps only that box."""
    if mode == "alpha":
        m = img[..., 3] > 0.5
    else:
        m = img[..., :3].mean(-1) < float(mode)
    if crop:
        x0, x1, y0, y1 = crop
        k = np.zeros_like(m)
        k[y0:y1, x0:x1] = True
        m &= k
    return m


def bbox(m):
    ys, xs = np.nonzero(m)
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def fill_holes(m):
    """In if between the first and last pixel of its row AND of its column (fills bright screen content
    without squaring off curved outer edges); the screens compare's row-and-column fill."""
    rows = np.zeros_like(m)
    cols = np.zeros_like(m)
    for y in np.nonzero(m.any(1))[0]:
        xs = np.nonzero(m[y])[0]
        rows[y, xs[0]:xs[-1] + 1] = True
    for x in np.nonzero(m.any(0))[0]:
        ys = np.nonzero(m[:, x])[0]
        cols[ys[0]:ys[-1] + 1, x] = True
    return m | (rows & cols)


def anchor_of(m, where="bottom-centre"):
    """A pixel anchor on a silhouette's box: 'bottom-centre', 'top-centre', 'centre', 'left-bottom' ..."""
    x0, x1, y0, y1 = bbox(m)
    xs = {"left": x0, "centre": (x0 + x1 + 1) / 2, "right": x1 + 1}
    ys = {"top": y0, "centre": (y0 + y1 + 1) / 2, "bottom": y1 + 1}
    a, b = (where.split("-") + ["centre"])[:2]
    if a in ys and b in xs:
        return (xs[b], ys[a])
    return (xs.get(a, xs["centre"]), ys.get(b, ys["centre"]))
