"""Paint the window's backdrop: Pune at dusk (2026-11-01, the lighting pass).

    /opt/anaconda3/bin/python3 blender/tools/paint_pune_dusk.py [out.png]

A flat painting for one plane 22 m outside the window (blender/lib/lighting_dusk.py places it): a sky from amber at
the horizon to deep blue overhead, a low sun just above the Sahyadri ridge, haze, then the city in bands from far to
near (hazy mid-rises, towers with water tanks, a hill with a temple, cranes, the neighbouring rooftops, trees, a
street with sodium lamps), its first windows lit (warm bulbs and the cool white tube lights of Pune flats).
Plain numpy + Pillow, a fixed seed: the same picture every run. The image maps to the plane's x in [X0, X1] and
z in [Z0, Z1] metres (Blender, the room's frame); HORIZON is eye level.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 2560, 1280
X0, X1, Z0, Z1 = -36.0, 36.0, -14.0, 22.0       # the plane, metres
HORIZON = 1.6                                    # eye level on the plane (the room is 12 m up)
SUN = (12.0, HORIZON + 1.15, 0.42)               # x, z, radius (m): right of the intro view, just above the ridge
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "assets", "dusk",
                                                         "pune-dusk.png")
rng = np.random.default_rng(1104)


def px(x, z):
    return (x - X0) / (X1 - X0) * W, (Z1 - z) / (Z1 - Z0) * H


def mx(m):                    # metres -> px (same scale both ways)
    return m / (X1 - X0) * W


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ---- the sky: linear-ish colour stops by height above the horizon (metres on the plane)
STOPS = [(-2.0, (236, 150, 92)), (0.0, (250, 178, 104)), (1.5, (246, 160, 104)), (3.5, (222, 140, 120)),
         (6.0, (170, 122, 140)), (9.0, (104, 104, 150)), (13.0, (58, 74, 128)), (20.5, (30, 44, 92))]
zz = Z1 - (np.arange(H) + 0.5) / H * (Z1 - Z0) - HORIZON
sky = np.zeros((H, W, 3), np.float32)
for c in range(3):
    col = np.interp(zz, [s[0] for s in STOPS], [s[1][c] for s in STOPS])
    sky[:, :, c] = col[:, None]
xs = X0 + (np.arange(W) + 0.5) / W * (X1 - X0)
gx, gz = np.meshgrid(xs, zz + HORIZON)
d = np.hypot(gx - SUN[0], (gz - SUN[1]) * 1.25)
glow = np.exp(-d / 2.2) * 0.85 + np.exp(-d / 9.0) * 0.35          # the sun's glow, wide and warm
sky += glow[:, :, None] * np.array([255, 196, 120], np.float32)[None, None] * 0.55
side = np.clip((gx - X0) / (X1 - X0), 0, 1)                          # the east (left) side a little bluer
sky *= (1 - 0.10 * (1 - side))[:, :, None] * np.array([1.0, 1.0, 1.04])[None, None]
disc = np.clip((SUN[2] - np.hypot(gx - SUN[0], gz - SUN[1])) / 0.04, 0, 1)
sky = sky * (1 - disc[:, :, None]) + disc[:, :, None] * np.array([255, 244, 214], np.float32)
# a few long thin clouds lit from below
cl = np.zeros((H, W), np.float32)
for _ in range(9):
    cz = HORIZON + rng.uniform(4.0, 12.0)
    cx = rng.uniform(X0, X1)
    ln, th = rng.uniform(8, 22), rng.uniform(0.15, 0.4)
    cl += np.exp(-(((gx - cx) / ln) ** 2) - (((gz + HORIZON - HORIZON - cz) / th) ** 2)) * rng.uniform(0.3, 0.7)
cl = np.clip(cl, 0, 1)
cloud_col = np.where((gz[:, :, None] - HORIZON) < 8, np.array([255, 170, 130]), np.array([200, 130, 150]))
sky = sky * (1 - 0.45 * cl[:, :, None]) + 0.45 * cl[:, :, None] * cloud_col
img = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8), "RGB")


def haze_col(t, zc=0.0):
    """Silhouette colour at haze t (0 near, 1 at the horizon): towards the horizon's amber-lilac."""
    near, far = (34, 30, 40), (196, 132, 118)
    return tuple(int(v) for v in lerp(near, far, t))


def layer(draw_fn, blur=0.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(lay), lay)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    img.paste(lay, (0, 0), lay)


def ridge(base, amp, freq, seed):
    r = np.random.default_rng(seed)
    ph = r.uniform(0, 6.28, 4)
    h = np.zeros(W)
    for k, (a, f) in enumerate(zip((1.0, 0.5, 0.25, 0.12), (1, 2.3, 5.1, 11.7))):
        h += a * np.sin(xs * freq * f + ph[k])
    return base + amp * (h - h.min()) / (h.max() - h.min())


# ---- far: the Sahyadri ridge, hazy, and a hill with a temple (Parvati) left of centre
def far(dw, lay):
    top = ridge(HORIZON + 0.15, 1.15, 0.05, 7)
    hill = np.exp(-((xs + 9.0) / 3.0) ** 2) * 1.5
    top = np.maximum(top, HORIZON + 0.2 + hill)
    pts = [px(X0, Z0)] + [px(x, t) for x, t in zip(xs, top)] + [px(X1, Z0)]
    dw.polygon(pts, fill=haze_col(0.86) + (255,))
    tx, tz = -9.0, HORIZON + 0.2 + 1.5
    for dx, h, w in ((0, 0.42, 0.16), (-0.35, 0.22, 0.24), (0.35, 0.22, 0.24)):   # the temple's shikhara and halls
        x0, y0 = px(tx + dx - w / 2, tz + h)
        x1, y1 = px(tx + dx + w / 2, tz - 0.05)
        dw.polygon([(x0, y1), ((x0 + x1) / 2, y0), (x1, y1)], fill=haze_col(0.8) + (255,))
    for k in range(5):                                                            # its first lamps
        x, y = px(tx - 0.6 + k * 0.3, tz - 0.1 - 0.12 * abs(k - 2))
        dw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 214, 150, 255))


layer(far, blur=1.2)


def building(dw, x, w, top, t, lit_p, zbase, seed, tank=True, floor=0.36):
    r = np.random.default_rng(seed)
    col = haze_col(t)
    x0, y0 = px(x, top)
    x1, y1 = px(x + w, zbase)
    dw.rectangle([x0, y0, x1, y1], fill=col + (255,))
    if tank and r.random() < 0.7:                    # the black water tanks on every Pune roof
        tw = min(w * 0.18, 0.5)
        tx = x + r.uniform(0.1, 0.7) * w
        a0, b0 = px(tx, top + tw * 0.8)
        a1, b1 = px(tx + tw, top)
        dw.rectangle([a0, b0, a1, b1], fill=haze_col(max(0, t - 0.05)) + (255,))
    if r.random() < 0.25:                            # a stair-head room
        sw = w * 0.25
        sx = x + r.uniform(0.05, 0.6) * w
        a0, b0 = px(sx, top + floor * 0.9)
        a1, b1 = px(sx + sw, top)
        dw.rectangle([a0, b0, a1, b1], fill=col + (255,))
    # windows: rows a floor apart, columns about 0.9 floors apart
    nf = int((top - zbase) / floor)
    nc = max(1, int(w / (floor * 1.1)))
    wwid, whei = floor * 0.42, floor * 0.45
    fade = 1 - t * 0.55
    for f in range(nf):
        zr = top - (f + 0.65) * floor
        if zr < Z0:
            break
        for c in range(nc):
            if r.random() > lit_p:
                continue
            cx = x + (c + 0.5) * w / nc
            warm = r.random() < 0.62
            base = (255, 196, 118) if warm else (226, 238, 255)
            k = r.uniform(0.6, 1.0) * fade
            colw = tuple(int(col[i] + (base[i] - col[i]) * k) for i in range(3))
            a0, b0 = px(cx - wwid / 2, zr + whei / 2)
            a1, b1 = px(cx + wwid / 2, zr - whei / 2)
            dw.rectangle([a0, b0, a1, b1], fill=colw + (255,))


# ---- the city in bands: far (hazy, small), mid (towers, cranes), near (rooftops, trees, street)
BANDS = [  # haze, base z, height range, width range, floor height, lit share, count
    (0.74, HORIZON - 1.2, (0.6, 1.6), (0.8, 2.0), 0.13, 0.07, 120),
    (0.60, HORIZON - 2.6, (1.0, 3.2), (1.0, 2.6), 0.18, 0.09, 70),
    (0.42, HORIZON - 5.0, (2.0, 7.5), (1.6, 3.6), 0.26, 0.11, 34),
    (0.22, HORIZON - 9.0, (2.5, 6.0), (3.0, 6.5), 0.40, 0.13, 20),
    (0.08, Z0 - 0.1, (3.0, 7.0), (5.0, 10.0), 0.62, 0.16, 12),
]
for bi, (t, zb, hr, wr, fl, lit, n) in enumerate(BANDS):
    def band(dw, lay, t=t, zb=zb, hr=hr, wr=wr, fl=fl, lit=lit, n=n, bi=bi):
        r = np.random.default_rng(50 + bi)
        x = X0 - 1
        items = []
        while x < X1:
            w = r.uniform(*wr)
            items.append((x, w, zb + r.uniform(*hr) * (1.6 if r.random() < 0.12 else 1.0)))
            x += w * r.uniform(0.75, 1.15)
        for k, (x, w, top) in enumerate(items):
            building(dw, x, w, top, t, lit, zb - 4.0, 1000 * bi + k, floor=fl)
        if bi in (1, 2):                                   # cranes: Pune is always building
            for _ in range(2):
                cx = r.uniform(X0 + 6, X1 - 6)
                top = zb + hr[1] * 1.25
                col = haze_col(t - 0.04) + (255,)
                m = max(1, int(mx(0.05 + 0.03 * (2 - bi))))
                dw.line([px(cx, zb), px(cx, top)], fill=col, width=m * 2)
                dw.line([px(cx - 1.0, top - 0.1), px(cx + 3.2, top - 0.1)], fill=col, width=m)
                dw.line([px(cx, top + 0.5), px(cx + 3.2, top - 0.1)], fill=col, width=max(1, m // 2))
                a, b = px(cx, top + 0.5)
                dw.ellipse([a - 2, b - 2, a + 2, b + 2], fill=(255, 70, 50, 255))   # the red lamp on top
        if bi == 3 and False:                              # trees: cut (they read as floating blobs)
            for _ in range(26):
                tx, tz = r.uniform(X0, X1), zb + r.uniform(0.5, 2.6)
                rad = r.uniform(0.8, 2.0)
                a0, b0 = px(tx - rad, tz + rad * 0.7)
                a1, b1 = px(tx + rad, tz - rad * 0.7)
                dw.ellipse([a0, b0, a1, b1], fill=haze_col(0.1) + (255,))
    layer(band, blur=max(0.0, (t - 0.3) * 2.0))
    # haze between bands: a soft warm wash that thickens near the horizon
    hz = np.asarray(img).astype(np.float32)
    k = np.exp(-np.abs(zz)[:, None] / 2.5) * 0.10 * (1 if bi < 3 else 0.3)
    hz = hz * (1 - k[:, :, None]) + k[:, :, None] * np.array([250, 176, 120], np.float32)
    img = Image.fromarray(np.clip(hz, 0, 255).astype(np.uint8), "RGB")


# ---- the street at the bottom: sodium lamps and their pools
def street(dw, lay):
    r = np.random.default_rng(77)
    zs = Z0 + 1.2
    for k in range(14):
        x = X0 + 2 + k * 5.2 + r.uniform(-0.6, 0.6)
        a, b = px(x, zs + 1.6)
        rad = mx(0.09)
        dw.ellipse([a - rad, b - rad, a + rad, b + rad], fill=(255, 190, 100, 255))


layer(street)
lamps = Image.new("RGB", (W, H), (0, 0, 0))
dl = ImageDraw.Draw(lamps)
r = np.random.default_rng(77)
for k in range(14):
    x = X0 + 2 + k * 5.2 + r.uniform(-0.6, 0.6)
    a, b = px(x, Z0 + 1.2 + 1.6)
    rad = mx(0.6)
    dl.ellipse([a - rad, b - rad, a + rad, b + rad], fill=(150, 90, 30))
lamps = lamps.filter(ImageFilter.GaussianBlur(mx(0.4)))
out = np.asarray(img).astype(np.float32) + np.asarray(lamps).astype(np.float32) * 0.8
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").save(OUT)
print("wrote", os.path.abspath(OUT), W, H)
