"""The sea at sunset, Marine Drive in spirit (2026-11-12; the window's view, replacing the Pune city).

    /opt/anaconda3/bin/python3 blender/tools/paint_beach_dusk.py [A|B ...] [--flat DIR] [--final]

Writes blender/assets/dusk/candidates/beach-<look>.png (one RGBA atlas) and beach-<look>.json (where each layer goes).
--flat DIR also writes beach-<look>-flat.jpg there: the layers composited as camera_intro sees them (a quick check).
--final also writes blender/assets/dusk/beach-dusk.{png,json}, which the room builds from (build_v3.py, stage dusk).
The owner chose look A (the sun above the sea) from a flat prototype on 2026-11-12; B (just set) is kept for reference.

Layers (distance from camera_intro): sky 15 m; the far shore, the headland and the sun 14.5 m; the sea 13 m; the curved
promenade with its lamps, the road and the Art Deco row 9.5 m; our own building's parapet and railing 6 m. During the
intro's pull-back the promenade slides over the sea and the parapet over everything; the sky and the far shore barely
move. Each layer is painted in camera_intro's tangent space (u = x / forward, v = z / forward) from a small model of the
real place at real distances: a plane L metres from camera_intro shows (u, v) at x = EYE.x + u L, z = EYE.z + v L.
Drawn at 2x, downsampled with premultiplied alpha, transparent texels take their nearest covered neighbour's colour.
The bottom row of every layer is opaque, so the room can extend it down to the street with a skirt quad.
Plain numpy + Pillow, fixed seeds: the same pictures every run.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paint_pune_dusk_v2 import bleed, pack  # noqa: E402  (shared helpers: transparent-texel fill, atlas packing)

OUTDIR = os.path.join(HERE, "..", "assets", "dusk", "candidates")
EYE = (0.43, 1.10, 1.55)          # camera_intro (blender/lib/plan_v3.py INTRO), Blender frame
EYE_H = 12.0 + EYE[2]             # the eye above the promenade's road, m (the room's floor is 12 m up)
STREET_Z = EYE[2] - EYE_H
SS = 2

LOOKS = {
    "A": dict(title="Sun above the sea", seed=7, sun=(0.35, 0.050, 0.017), sun_col=(255, 240, 200),
              sky=[(-5, (250, 168, 110)), (0, (255, 196, 128)), (2, (255, 184, 118)), (6, (246, 166, 128)),
                   (13, (214, 150, 150)), (24, (150, 136, 176)), (40, (86, 98, 160)), (60, (52, 64, 124))],
              sea_far=(196, 140, 132), sea_near=(40, 46, 74), glow=0.55, glint=1.0, lights=0.35, stars=0,
              facade=(0.52, 0.40, 0.38), lamp=0.75),
    "B": dict(title="Just set, afterglow", seed=8, sun=(0.35, -0.012, 0.017), sun_col=(255, 220, 170),
              sky=[(-5, (220, 120, 92)), (0, (250, 150, 96)), (1.5, (238, 140, 104)), (5, (204, 128, 130)),
                   (11, (150, 116, 152)), (20, (96, 100, 156)), (36, (52, 66, 128)), (60, (26, 36, 86))],
              sea_far=(150, 108, 124), sea_near=(24, 28, 54), glow=0.75, glint=0.55, lights=0.75, stars=6,
              facade=(0.34, 0.28, 0.32), lamp=1.0),
}

# layer: distance from camera_intro (m; the sky at 15 m sits where the old single plane was, 16.1 m out from y = 0), tangent box (u0, u1, v0, v1), texels per tangent unit
SPEC = {
    "sky":   dict(L=15.0, box=(-2.00, 2.00, -0.30, 1.60), tpu=210, opaque=True),
    "far":   dict(L=14.5, box=(-1.40, 1.40, -0.020, 0.075), tpu=520),
    "sea":   dict(L=13.0, box=(-1.20, 1.20, -0.640, 0.065), tpu=470),
    "prom":  dict(L=9.5,  box=(-1.00, 0.00, -0.640, 0.280), tpu=900),
    "near":  dict(L=6.0,  box=(-0.92, 0.92, -0.680, -0.500), tpu=1000),
}
ORDER = ["sky", "far", "sea", "prom", "near"]


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def mul(a, b):
    return tuple(a[i] * b[i] for i in range(3))


def ci(c, a=255):
    return tuple(int(max(0, min(255, round(x)))) for x in c) + (a,)


def wall_x(Y):
    """The promenade's sea edge, X (m) at forward distance Y: from just below-left of the window, curving away left
    round the bay."""
    return -9.0 - 0.06 * Y - 0.00026 * (Y - 25.0) ** 2


class Look:
    def __init__(self, key):
        self.key, self.p = key, LOOKS[key]

    def sky(self, u, v):
        p = self.p
        u, v = np.asarray(u, np.float32), np.asarray(v, np.float32)
        e = np.degrees(np.arctan(v))
        out = np.zeros(np.broadcast(u, v).shape + (3,), np.float32)
        for c in range(3):
            out[..., c] = np.interp(e, [s[0] for s in p["sky"]], [s[1][c] for s in p["sky"]])
        us, vs, _ = p["sun"]
        d = np.hypot((u - us) * 0.7, (v - vs) * 1.6)
        g = (np.exp(-d / 0.03) * 0.22 + np.exp(-d / 0.15) * 0.42 + np.exp(-d / 0.5) * 0.2) * p["glow"]
        return out + g[..., None] * (np.array([255, 205, 140], np.float32) - out * 0.6) * 0.75

    def horizon(self, u):
        return tuple(float(x) for x in self.sky(u, 0.008))

    def haze(self, col, R, u, vis=4500.0, k=1.0):
        return lerp(col, self.horizon(u), min(1.0, (1 - math.exp(-R / vis)) * k))


class Layer:
    def __init__(self, look, name):
        s = SPEC[name]
        self.look, self.name, self.L, self.opaque = look, name, s["L"], s.get("opaque", False)
        self.u0, self.u1, self.v0, self.v1 = s["box"]
        self.tpu = s["tpu"]
        self.w = int(round((self.u1 - self.u0) * self.tpu))
        self.h = int(round((self.v1 - self.v0) * self.tpu))
        self.W, self.H, self.k = self.w * SS, self.h * SS, self.tpu * SS
        self.img = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.glow = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        self.dg = ImageDraw.Draw(self.glow)

    def grid(self):
        ys, xs = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        return self.u0 + (xs + 0.5) / self.k, self.v1 - (ys + 0.5) / self.k

    def px(self, u, v):
        return ((u - self.u0) * self.k, (self.v1 - v) * self.k)

    def p3(self, X, Y, Z):
        return self.px(X / Y, (Z - EYE_H) / Y)

    def m(self, metres, Y):
        return metres / Y * self.k

    def set_array(self, rgb, alpha=None):
        a = np.full(rgb.shape[:2] + (1,), 255, np.float32) if alpha is None else alpha[..., None] * 255
        self.img = Image.fromarray(np.concatenate([np.clip(rgb, 0, 255), a], -1).astype(np.uint8), "RGBA")
        self.d = ImageDraw.Draw(self.img)

    def halo(self, X, Y, Z, r_m, col, a, r_max=None):
        x, y = self.p3(X, Y, Z)
        r = max(1.5, self.m(r_m, Y))
        if r_max:
            r = min(r, r_max * SS)
        for k in range(4, 0, -1):
            rr = r * k / 4
            self.dg.ellipse([x - rr, y - rr, x + rr, y + rr], fill=ci(col, int(a * (1.15 - k / 4) ** 1.5)))

    def finish(self):
        img = self.img
        if self.glow.getbbox():
            img = Image.alpha_composite(img, self.glow.filter(ImageFilter.GaussianBlur(SS * 1.5)))
        a = np.asarray(img).astype(np.float32) / 255.0
        if self.opaque:
            a[..., 3] = 1.0
        pm = a.copy()
        pm[..., :3] *= pm[..., 3:4]
        ch = [Image.fromarray(pm[..., c]).resize((self.w, self.h), Image.LANCZOS) for c in range(4)]
        pm = np.stack([np.asarray(c) for c in ch], -1).clip(0, 1)
        al = pm[..., 3:4]
        rgb = np.where(al > 1e-3, pm[..., :3] / np.maximum(al, 1e-3), 0)
        rgb = bleed(rgb, al[..., 0])
        self.final = Image.fromarray((np.concatenate([rgb, al], -1) * 255 + 0.5).clip(0, 255).astype(np.uint8), "RGBA")
        return self.final


def noise(r, W, H, cells, resample=Image.BICUBIC):
    gw, gh = cells
    return np.asarray(Image.fromarray(r.random((gh, gw)).astype(np.float32)).resize((W, H), resample))


# ---------------------------------------------------------------- sky: gradient, clouds lit from below, stars
def paint_sky(lay):
    lk, p = lay.look, lay.look.p
    r = np.random.default_rng(p["seed"] + 1)
    u, v = lay.grid()
    col = lk.sky(u, v)
    n = sum(noise(r, lay.W, lay.H, c) * a for c, a in (((8, 12), 0.55), ((20, 34), 0.3), ((44, 80), 0.15)))
    n = (n - n.min()) / (n.max() - n.min())
    band = np.exp(-((v - 0.30) / 0.13) ** 2) + 0.6 * np.exp(-((v - 0.09) / 0.03) ** 2)
    c = (np.clip((n - 0.55) / 0.14, 0, 1) * band * 0.7)[..., None]
    near = np.exp(-np.abs(u - p["sun"][0]) / 0.8)[..., None]
    lit = np.array([255, 178, 136], np.float32) * near + np.array([150, 120, 158], np.float32) * (1 - near)
    lay.set_array(col * (1 - c) + c * lit)
    for _ in range(p["stars"]):
        x, y = lay.px(r.uniform(-0.9, 0.9), r.uniform(0.55, 1.1))
        lay.d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(250, 248, 236, 255))


# ---------------------------------------------------------------- far: the sun, the far shore's towers, a headland
def paint_far(lay):
    lk, p = lay.look, lay.look.p
    r = np.random.default_rng(p["seed"] + 2)
    us, vs, rs = p["sun"]
    if vs > -rs:
        x, y = lay.px(us, vs)
        rr = rs * lay.k
        lay.d.ellipse([x - rr, y - rr * 0.94, x + rr, y + rr * 0.94], fill=ci(p["sun_col"]))
        for k in range(0 if vs > 0.03 else 1):              # a thin cloud streak across a low disc
            sv = vs + r.uniform(-0.5, 0.6) * rs
            x0, y0 = lay.px(us - r.uniform(0.05, 0.12), sv)
            x1, _ = lay.px(us + r.uniform(0.05, 0.14), sv)
            th = max(1.0, r.uniform(0.0015, 0.003) * lay.k)
            lay.d.rounded_rectangle([x0, y0 - th / 2, x1, y0 + th / 2], radius=th / 2,
                                    fill=ci(lerp(lk.horizon(us), (150, 100, 110), 0.3)))
    # the sea below the horizon (hidden behind the sea layer from camera_intro, shows if the camera dips)
    sea = lerp(p["sea_far"], lk.horizon(0.0), 0.3)
    x0, y0 = lay.px(lay.u0, 0.0)
    lay.d.rectangle([0, y0, lay.W, lay.H], fill=ci(sea))
    # the far shore across the bay: towers in haze, the first lights; a headland at the far end of the curve
    Yf = 5200.0
    uu = -1.25
    while uu < -0.08:
        h = (16 + 60 * r.random() ** 2.5) if r.random() < 0.55 else 6 + 8 * r.random()
        w = r.uniform(0.0015, 0.0045)
        far = lerp((66, 70, 104), lk.horizon(uu), 0.55)
        x0, y0 = lay.p3(uu * Yf, Yf, h)
        x1, y1 = lay.p3((uu + w) * Yf, Yf, -6)
        lay.d.rectangle([x0, y0, x1, y1], fill=ci(far))
        for _ in range(int(h / 9)):
            if r.random() < p["lights"] * 0.5:
                lx, ly = lay.p3((uu + w * 0.5) * Yf, Yf, r.uniform(2, h - 1))
                lay.d.rectangle([lx, ly, lx + 1, ly + 1], fill=(255, 214, 160, 255))
        uu += w * r.uniform(0.6, 1.1)
    pts = [lay.p3(x * 3000, 3000, 30 * max(0.0, 1 - ((x + 0.66) / 0.24) ** 2) ** 0.6) for x in np.linspace(-0.90, -0.42, 80)]
    hl = lerp((48, 52, 82), lk.horizon(-0.6), 0.42)
    lay.d.polygon([lay.p3(-0.90 * 3000, 3000, -6)] + pts + [lay.p3(-0.42 * 3000, 3000, -6)], fill=ci(hl))
    for _ in range(int(40 * p["lights"])):
        x = r.uniform(-0.86, -0.46) * 3000
        lx, ly = lay.p3(x, 3000, r.uniform(1, 20))
        lay.d.rectangle([lx, ly, lx + 1, ly + 1], fill=(255, 210, 150, 255))


# ---------------------------------------------------------------- sea: colour by distance, waves, the sun's path, boats
def paint_sea(lay):
    lk, p = lay.look, lay.look.p
    r = np.random.default_rng(p["seed"] + 3)
    u, v = lay.grid()
    sea = v < 0
    R = np.where(sea, EYE_H / np.maximum(-v, 1e-4), 1e9)
    t = np.clip(np.log(R / 25.0) / np.log(20000 / 25.0), 0, 1)
    tt = t[..., None] ** 0.6
    col = np.array(p["sea_near"], np.float32) * (1 - tt) + np.array(p["sea_far"], np.float32) * tt
    col = col * 0.75 + lk.sky(u, np.abs(v) * 0.6 + 0.02) * 0.0875           # the sky, mirrored and dimmed
    # wave bands: long crests across, broken by noise; finer and fainter far off
    wn = noise(r, lay.W, lay.H, (40, 90)) * 10 + noise(r, lay.W, lay.H, (160, 300)) * 3
    ph = R * 0.8 + wn
    crest = (np.sin(ph) * 0.5 + 0.5) ** 8 * (1 - t) ** 1.2
    trough = (np.sin(ph + 1.2) * 0.5 + 0.5) ** 3 * (1 - t) * 0.12
    col = col * (1 - trough[..., None]) + crest[..., None] * (lk.sky(u, 0.25) - col) * 0.35
    # the sun's path: broken glints, narrow at the horizon, wide near the shore
    us = p["sun"][0]
    sw = 0.010 + 0.11 * (1 - t) ** 1.6
    lane = np.exp(-((u - us) / sw) ** 2) * p["glint"]
    g1 = noise(r, lay.W, lay.H, (int(lay.W / 4), int(lay.H / 1.5)), Image.BILINEAR)
    g2 = noise(r, lay.W, lay.H, (int(lay.W / 14), int(lay.H / 3)), Image.BILINEAR)
    g = np.clip((g1 * 0.6 + g2 * 0.4 - (0.80 - 0.30 * lane)) / 0.10, 0, 1) * lane * (0.45 + 0.55 * t)
    g += np.exp(-((u - us) / 0.012) ** 2) * np.exp(v / 0.006) * 0.8 * p["glint"]       # the bright core at the horizon
    gl = np.clip(g, 0, 1)[..., None]
    col = col + gl * (np.array([255, 206, 140], np.float32) - col) * 0.95
    # haze on the horizon
    hz = np.exp(-np.abs(v) / 0.010)[..., None] * 0.5
    col = col * (1 - hz) + hz * lk.sky(u, np.full_like(u, 0.008))
    lay.set_array(col, sea.astype(np.float32))
    # boats: dhows and fishing boats on the open water, a lamp or two
    for k in range(6):
        Y = r.uniform(350, 2600)
        X = r.uniform(-0.15, 0.85) * Y
        if abs(X / Y - us) < 0.05:
            X += 0.12 * Y
        L = r.uniform(8, 15)
        c = lk.haze((28, 24, 38), Y, X / Y, 3500)
        lay.d.polygon([lay.p3(X, Y, 0.0), lay.p3(X + L, Y, 0.0), lay.p3(X + L * 1.08, Y, 1.5), lay.p3(X - L * 0.1, Y, 1.5)], fill=ci(c))
        lay.d.rectangle([*lay.p3(X + L * 0.55, Y, 3.2), *lay.p3(X + L * 0.8, Y, 1.5)], fill=ci(c))      # the cabin
        if k % 3 == 0:
            lay.d.polygon([lay.p3(X + L * 0.3, Y, 1.5), lay.p3(X + L * 0.36, Y, 10.0), lay.p3(X + L * 0.7, Y, 1.7)], fill=ci(c))
        if r.random() < p["lights"] + 0.3:
            lay.halo(X + L * 0.6, Y, 3.6, 1.0, (255, 200, 130), 200, r_max=4)
            x, y = lay.p3(X + L * 0.6, Y, 3.6)
            lay.d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 220, 160, 255))


# ---------------------------------------------------------------- the promenade: Art Deco row, road, wall, lamps
def paint_prom(lay):
    lk, p = lay.look, lay.look.p
    r = np.random.default_rng(p["seed"] + 4)
    Ys = np.concatenate([np.linspace(19, 200, 160), np.linspace(200, 3200, 220)])
    hz = lambda c, Y, X: lk.haze(c, Y, X / Y, 3200)
    # the land: everything left of the sea edge, down to the bottom of the layer
    land = [lay.p3(wall_x(Y) - 2000, Y, 0) for Y in Ys[::-1]] + [lay.p3(wall_x(Y), Y, 0) for Y in Ys]
    lay.d.polygon(land, fill=(36, 34, 44, 255))
    bot = lay.p3(wall_x(19) - 2000, 19, -40)
    lay.d.polygon([lay.p3(wall_x(19), 19, 0), lay.p3(wall_x(19), 19, -40), bot, lay.p3(wall_x(19) - 2000, 19, 0)],
                  fill=(36, 34, 44, 255))
    # the road (two carriageways) and the pavement, as strips following the curve
    def strip(off0, off1, col_fn, step=1):
        pts0 = [lay.p3(wall_x(Y) - off0, Y, 0) for Y in Ys[::step]]
        pts1 = [lay.p3(wall_x(Y) - off1, Y, 0) for Y in Ys[::-step]]
        lay.d.polygon(pts0 + pts1, fill=ci(col_fn))
    strip(0.0, 7.0, lerp((70, 64, 72), lk.horizon(-0.4), 0.12))          # the pavement, catching the sky
    strip(7.0, 32.0, (40, 38, 46))                                        # the road
    strip(18.5, 20.5, (70, 74, 60))                                       # the divider, low hedges
    def details(lo, hi):
        """Everything along the promenade with forward distance in [lo, hi): the far part is drawn before the
        buildings, the near part after, so far lamps and the far wall never draw over the nearer blocks."""
        inr = lambda Y: lo <= Y < hi
        ys_ = [Y for Y in Ys if lo - 2 <= Y < hi + 2]
        # traffic: white headlights coming, red tail lights going, thinning with distance
        for _ in range(140):
            Y = 20 + 2600 * r.random() ** 2.2
            lane_off = r.uniform(8, 18) if r.random() < 0.5 else r.uniform(21, 31)
            col = (255, 246, 226) if lane_off > 20 else (255, 70, 50)
            if not inr(Y):
                continue
            x, y = lay.p3(wall_x(Y) - lane_off, Y, 0.7)
            rr = max(0.9, lay.m(0.14, Y))
            lay.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=ci(hz(col, Y, wall_x(Y)) if Y > 800 else col))
            if Y < 300:
                lay.halo(wall_x(Y) - lane_off, Y, 0.7, 0.8, col, 120, r_max=8)
        # the palms between the road and the pavement, near end
        for Y in (24, 33, 45, 62, 85, 115, 160, 220):
            if not inr(Y):
                continue
            X = wall_x(Y) - 6.5
            h = r.uniform(10, 13)
            bend = r.uniform(-0.04, 0.04)
            tr = [lay.p3(X + bend * z * z, Y, z) for z in np.linspace(0, h, 12)]
            tc = hz((30, 28, 34), Y, X)
            lay.d.line(tr, fill=ci(tc), width=max(1, int(lay.m(0.35, Y))))
            cx = X + bend * h * h
            for a in np.linspace(0, 2 * math.pi, 12)[:-1] + r.uniform(0, 0.5):
                fr = [lay.p3(cx + math.cos(a) * 4.2 * s, Y + math.sin(a) * 1.5 * s, h + 0.9 * math.sin(math.pi * s * 0.7) - 2.0 * s * s)
                      for s in np.linspace(0, 1, 9)]
                fc_ = ci(hz((26, 38, 32), Y, X))
                lay.d.line(fr, fill=fc_, width=max(1, int(lay.m(0.18, Y))))
                for q in range(2, 9):
                    x, y = fr[q]
                    ln = lay.m(1.0 * (1 - q / 11), Y)
                    lay.d.line([(x, y), (x + ln * 0.45, y + ln)], fill=fc_, width=max(1, int(lay.m(0.09, Y))))
                    lay.d.line([(x, y), (x - ln * 0.45, y + ln)], fill=fc_, width=max(1, int(lay.m(0.09, Y))))
        # the sea wall: the parapet along the pavement's edge, the tetrapods below it, the foam
        top = [lay.p3(wall_x(Y), Y, 1.0) for Y in ys_]
        lay.d.line(top, fill=ci(lerp((176, 150, 140), lk.horizon(-0.3), 0.2)), width=3)
        face = [lay.p3(wall_x(Y) + 0.3, Y, 0) for Y in ys_] + [lay.p3(wall_x(Y) + 0.3, Y, -3.0) for Y in ys_[::-1]]
        lay.d.polygon(face, fill=(44, 40, 50, 255))
        for Y in np.linspace(19, 500, 340):                  # tetrapods, a jumble of dark shapes, catching the light on top
            if not inr(Y):
                continue
            X = wall_x(Y) + r.uniform(0.5, 6.0)
            x, y = lay.p3(X, Y, -3.0 + r.uniform(0, 1.2))
            rr = lay.m(r.uniform(0.8, 1.3), Y)
            c = hz((52, 48, 58), Y, X)
            lay.d.polygon([(x - rr, y + rr * 0.5), (x, y - rr * 0.7), (x + rr, y + rr * 0.5)], fill=ci(c))
            lay.d.line([(x - rr * 0.6, y - rr * 0.2), (x, y - rr * 0.7)], fill=ci(lerp(c, (230, 170, 140), 0.35)), width=1)
        fcol = ci(lerp((150, 136, 150), lk.horizon(-0.3), 0.2))
        for Y in (np.geomspace(max(40, lo), min(3000, hi), 420) if lo < 3000 and hi > 40 else []):      # foam: broken, in short runs
            if r.random() < 0.7:
                continue
            X = wall_x(Y) + 6.0 + r.uniform(0, 2.5)
            a0, b0 = lay.p3(X, Y, -3.0)
            a1, b1 = lay.p3(X + r.uniform(1.0, 3.0), Y + r.uniform(0.5, 2.0), -3.0)
            lay.d.line([(a0, b0), (a1, b1)], fill=fcol, width=max(1, int(lay.m(0.15, Y))))
        # the Queen's Necklace: sodium lamps on tall poles along the pavement, close ones on show, far ones a string of beads
        Y = 21.0
        while Y < 3200:
            X = wall_x(Y) - 3.0
            if not inr(Y):
                Y += 28 + Y * 0.03
                continue
            x, y = lay.p3(X, Y, 10.0)
            rr = max(1.4, lay.m(0.30, Y))
            if Y < 260:
                lay.d.line([lay.p3(X, Y, 0), lay.p3(X, Y, 10.0)], fill=ci(hz((34, 32, 40), Y, X)), width=max(1, int(lay.m(0.18, Y))))
                lay.d.line([lay.p3(X, Y, 10.0), lay.p3(X + 1.2, Y, 10.0)], fill=ci(hz((34, 32, 40), Y, X)), width=max(1, int(lay.m(0.12, Y))))
                x, y = lay.p3(X + 1.2, Y, 9.8)
            if Y < 400:
                lay.halo(X + 1.2, Y, 9.8, 1.6, (255, 168, 80), int(170 * p["lamp"]), r_max=26)
            lay.d.ellipse([x - rr, y - rr * 0.7, x + rr, y + rr * 0.7], fill=(255, 216, 150, 255))
            Y += 28 + Y * 0.03
        # people walking on the pavement, near end
        for _ in range(18):
            Y = r.uniform(24, 180)
            X = wall_x(Y) - r.uniform(1, 6)
            if not inr(Y):
                continue
            a, b = lay.p3(X, Y, 1.7)
            a1, b1 = lay.p3(X + 0.45, Y, 0)
            lay.d.rectangle([a, b, a1, b1], fill=(24, 22, 30, 255))
            hx, hy = lay.p3(X + 0.22, Y, 1.85)
            hr = lay.m(0.14, Y)
            lay.d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(24, 22, 30, 255))

    details(120.0, 1e9)
    # the Art Deco row along the curve: each block's long front follows the curve and faces the sea and the sunset;
    # we see that front obliquely and the block's end wall towards us; rounded corners, horizontal bands, lit windows
    paints = [(232, 214, 186), (238, 220, 170), (226, 196, 176), (214, 210, 200), (236, 226, 212), (210, 188, 170),
              (200, 214, 214)]
    blds = []
    Y = 3200.0
    while Y > 24:
        d = r.uniform(18, 30)
        blds.append((Y, r.uniform(17, 28), d))
        Y -= d + r.uniform(3, 6) + Y * 0.01
    for Y0, h, d in blds:
        Y1 = Y0 + d
        sea_x = lambda y: wall_x(y) - 34.0
        back = 16.0
        paint = paints[int(r.integers(len(paints)))]
        fc = hz(mul(paint, p["facade"]), Y0, sea_x(Y0))
        endc = hz(mul(paint, (p["facade"][0] * 0.55, p["facade"][1] * 0.58, p["facade"][2] * 0.72)), Y0, sea_x(Y0))
        ys = np.linspace(Y0, Y1, 10)
        front = [lay.p3(sea_x(y), y, 0) for y in ys] + [lay.p3(sea_x(y), y, h) for y in ys[::-1]]
        lay.d.polygon([lay.p3(sea_x(Y0) - back, Y0, 0), lay.p3(sea_x(Y0), Y0, 0), lay.p3(sea_x(Y0), Y0, h),
                       lay.p3(sea_x(Y0) - back, Y0, h)], fill=ci(endc))
        lay.d.polygon(front, fill=ci(fc))
        # the parapet's lit top and a stair-head or two, water tanks
        lay.d.line([lay.p3(sea_x(y), y, h) for y in ys], fill=ci(lerp(fc, (255, 205, 160), 0.35)),
                   width=max(1, int(lay.m(0.5, Y0))))
        for _ in range(int(r.integers(0, 3))):
            y = r.uniform(Y0 + 2, Y1 - 4)
            lay.d.polygon([lay.p3(sea_x(y) - 3, y, h), lay.p3(sea_x(y) - 3, y + 3, h), lay.p3(sea_x(y) - 3, y + 3, h + 2.6),
                           lay.p3(sea_x(y) - 3, y, h + 2.6)], fill=ci(endc))
        if lay.m(3.0, Y0) < 3:
            # far: just a few lit dots
            for _ in range(int(h * d / 60)):
                if r.random() < p["lights"]:
                    x, y_ = lay.p3(sea_x(Y0 + r.uniform(0, d)), Y0, r.uniform(2, h - 1))
                    lay.d.point((x, y_), fill=(255, 206, 140, 255))
            continue
        band = lerp(fc, endc, 0.5)
        for f in range(1, int(h / 3.1)):
            z = f * 3.1
            lay.d.line([lay.p3(sea_x(y), y, z) for y in ys], fill=ci(band), width=max(1, int(lay.m(0.22, Y0))))
            nb = max(2, int(d / 3.0))
            for c in range(nb):
                y = Y0 + (c + 0.5) * d / nb
                on = r.random() < p["lights"] * 0.8
                if on:
                    col = lerp(fc, (255, 196, 120) if r.random() < 0.7 else (220, 236, 255), 0.88)
                else:
                    col = lerp(lerp(fc, (40, 36, 52), 0.5), lk.horizon(-0.2), 0.3 if r.random() < 0.4 else 0.0)
                q = [lay.p3(sea_x(y - 0.7), y - 0.7, z + 0.7), lay.p3(sea_x(y + 0.7), y + 0.7, z + 0.7),
                     lay.p3(sea_x(y + 0.7), y + 0.7, z + 2.1), lay.p3(sea_x(y - 0.7), y - 0.7, z + 2.1)]
                lay.d.polygon(q, fill=ci(col))
        # the rounded corner, a softer vertical edge where the end wall meets the front
        lay.d.line([lay.p3(sea_x(Y0), Y0, 0), lay.p3(sea_x(Y0), Y0, h)], fill=ci(lerp(fc, endc, 0.5)),
                   width=max(1, int(lay.m(1.2, Y0))))
    details(0.0, 120.0)


# ---------------------------------------------------------------- near: our own building's parapet, two palm crowns
def paint_near(lay):
    lk, p = lay.look, lay.look.p
    r = np.random.default_rng(p["seed"] + 5)
    Yp = 7.0            # the parapet's front edge, 7 m out from the eye (a terrace below the window), 3 m below
    top = 13.55 - 3.75     # just above the window's sill line from camera_intro
    wall = (54, 48, 58)
    x0, y0 = lay.p3(-100, Yp, top)
    lay.d.rectangle([0, y0, lay.W, lay.H], fill=ci(wall))
    lay.d.rectangle([0, y0, lay.W, y0 + lay.m(0.08, Yp)], fill=ci(lerp(wall, (255, 196, 150), 0.45)))   # its lit top
    for k in range(-60, 61):                   # a railing on the parapet
        x = k * 0.12 * Yp
        lay.d.line([lay.p3(x, Yp, top), lay.p3(x, Yp, top + 0.9)], fill=ci((40, 36, 44)), width=max(1, int(lay.m(0.025, Yp))))
    a, b = lay.p3(-100, Yp, top + 0.9)
    lay.d.rectangle([0, b - lay.m(0.03, Yp), lay.W, b + lay.m(0.03, Yp)], fill=ci((44, 40, 48)))
    lay.d.rectangle([0, b - lay.m(0.03, Yp), lay.W, b], fill=ci(lerp((44, 40, 48), (255, 190, 140), 0.4)))


PAINT = {"sky": paint_sky, "far": paint_far, "sea": paint_sea, "prom": paint_prom, "near": paint_near}


def build(key, flat=None):
    look = Look(key)
    layers = []
    for name in ORDER:
        lay = Layer(look, name)
        PAINT[name](lay)
        lay.finish()
        layers.append(lay)
        print(f"  {key} {name}: {lay.w} x {lay.h}")
    AW = 2048
    pos, used = pack([(l.name, l.w, l.h) for l in layers], AW)
    AH = (used + 2 + 15) // 16 * 16          # as many rows as the layers need (WebGL2 mipmaps any size)
    if AH > 2048:
        raise SystemExit(f"{key}: the layers need {used} rows")
    atlas = Image.new("RGBA", (AW, AH), (0, 0, 0, 0))
    meta = dict(look=key, title=look.p["title"], atlas=f"beach-{key}.png", size=[AW, AH], eye=list(EYE),
                street_z=STREET_Z, layers=[])
    for lay in layers:                       # far to near: the order to draw them in
        x, y = pos[lay.name]
        atlas.paste(lay.final, (x, y))
        meta["layers"].append(dict(
            name=lay.name, distance=lay.L, plane_y=round(EYE[1] + lay.L, 4),
            x0=round(EYE[0] + lay.u0 * lay.L, 4), x1=round(EYE[0] + lay.u1 * lay.L, 4),
            z0=round(EYE[2] + lay.v0 * lay.L, 4), z1=round(EYE[2] + lay.v1 * lay.L, 4),
            rect=[x, y, lay.w, lay.h], opaque=lay.opaque,
            uv=[(x + 0.5) / AW, 1 - (y + lay.h - 0.5) / AH, (x + lay.w - 0.5) / AW, 1 - (y + 0.5) / AH],
            skirt=not lay.opaque))
    a = np.asarray(atlas).copy()
    for L_ in meta["layers"]:                # edge texels into the padding: no bleeding between blocks
        x, y, w, h = L_["rect"]
        blk = a[y:y + h, x:x + w].copy()
        y0, y1, x0, x1 = max(0, y - 2), min(AH, y + h + 2), max(0, x - 2), min(AW, x + w + 2)
        a[y0:y, x:x + w] = blk[:1]
        a[y + h:y1, x:x + w] = blk[-1:]
        a[y0:y1, x0:x] = a[y0:y1, x:x + 1]
        a[y0:y1, x + w:x1] = a[y0:y1, x + w - 1:x + w]
    atlas = Image.fromarray(a, "RGBA")
    os.makedirs(OUTDIR, exist_ok=True)
    png = os.path.join(OUTDIR, f"beach-{key}.png")
    atlas.save(png, optimize=True)
    webp = os.path.join(OUTDIR, f"beach-{key}.webp")
    atlas.save(webp, "WEBP", quality=88, method=6)
    meta.update(bytes_png=os.path.getsize(png), bytes_webp_q88=os.path.getsize(webp),
                gpu_bytes_rgba_mips=int(AW * AH * 4 * 4 / 3), rows_used=used,
                draw_calls=len(layers), triangles=sum(4 if l["skirt"] else 2 for l in meta["layers"]))
    with open(os.path.join(OUTDIR, f"beach-{key}.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(f"wrote {png}: {meta['bytes_png'] // 1024} KB png, {meta['bytes_webp_q88'] // 1024} KB webp, rows {used}")
    if flat:
        flat_view(meta, atlas, os.path.join(flat, f"beach-{key}-flat.jpg"))
    return meta


def flat_view(meta, atlas, path, box=(-0.80, 0.80, -0.62, 0.78), S=1100):
    """The layers composited as camera_intro sees them (no room, no window)."""
    U0, U1, V0, V1 = box
    W, H = int((U1 - U0) * S), int((V1 - V0) * S)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for L in meta["layers"]:
        x, y, w, h = L["rect"]
        d = L["distance"]
        u0, u1 = (L["x0"] - EYE[0]) / d, (L["x1"] - EYE[0]) / d
        v0, v1 = (L["z0"] - EYE[2]) / d, (L["z1"] - EYE[2]) / d
        blk = atlas.crop((x, y, x + w, y + h)).resize((int((u1 - u0) * S), int((v1 - v0) * S)), Image.BILINEAR)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lay.paste(blk, (int((u0 - U0) * S), int((V1 - v1) * S)))
        out = Image.alpha_composite(out, lay)
    out.convert("RGB").save(path, quality=90)


if __name__ == "__main__":
    args = sys.argv[1:]
    flat = None
    if "--flat" in args:
        i = args.index("--flat")
        flat = args[i + 1]
        args = args[:i] + args[i + 2:]
    final = "--final" in args          # also write blender/assets/dusk/beach-dusk.{png,json}, what the room builds from
    args = [a for a in args if a != "--final"]
    for k in (args or ["A"]):
        meta = build(k, flat)
        if final:
            import shutil
            dst = os.path.join(HERE, "..", "assets", "dusk", "beach-dusk")
            shutil.copy(os.path.join(OUTDIR, meta["atlas"]), dst + ".png")
            meta = dict(meta, atlas="beach-dusk.png",
                        note=f"paint_beach_dusk.py look {k}; read by lighting_dusk.backdrop_layers()")
            with open(dst + ".json", "w") as f:
                json.dump(meta, f, indent=1)
            print("wrote", os.path.abspath(dst) + ".{png,json}")
