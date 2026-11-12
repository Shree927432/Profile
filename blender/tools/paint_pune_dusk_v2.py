"""Pune at dusk, in layers (2026-11-12, candidates for the window's view; the old flat painting is paint_pune_dusk.py).

    /opt/anaconda3/bin/python3 blender/tools/paint_pune_dusk_v2.py [A|B|C ...]

Writes blender/assets/dusk/candidates/city-<opt>.png (one RGBA atlas) and city-<opt>.json (where each layer goes).

Why layers: the site opens on this view and then pulls the camera back 1.9 m and turns it; one flat plane does not
shift against itself, so the city read as a poster. Here the view is split into planes at different distances from
the intro camera (sky 18 m, ridge 16 m, far city 13.5 m, mid city 10 m, near rooftops 7 m), so the near rooftops
slide over the mid city, the mid city over the far city, and the ridge barely moves.

How it is painted: every layer is drawn in the intro camera's tangent space (u = x / forward, v = z / forward, from
camera_intro, Blender frame), from a little 3D model of real Pune at real distances (buildings 40 m to 3 km away,
the Sahyadri 6 to 15 km). A plane L metres in front of camera_intro shows tangent (u, v) at x = EYE.x + u L,
z = EYE.z + v L: from camera_intro the layers line up exactly as the 3D model would. The model is a box city: fronts,
the side facing the view axis, roofs when they are below the eye (the room is 12 m up, so most roofs show), then
parapets, black water tanks, stair heads, balconies, grilles, lit windows (warm bulbs, cool tube lights), cranes,
towers with red lamps, rain trees and palms, a road with sodium lamps. Aerial haze by real distance. Drawn at 2x and
downsampled with premultiplied alpha; transparent texels take the colour of the nearest opaque ones (no dark fringes
under bilinear filtering and mipmaps). Plain numpy + Pillow, fixed seeds: the same pictures every run.

Each layer's bottom row is opaque: the room extends it down to the street with a skirt quad sampling that row.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "assets", "dusk", "candidates")
EYE = (0.43, 1.10, 1.55)          # camera_intro (blender/lib/plan_v3.py INTRO), Blender frame
EYE_H = 12.0 + EYE[2]             # the eye above the street, m (the room's floor is 12 m up)
STREET_Z = EYE[2] - EYE_H         # the street in the room's frame: -12 m
SS = 2                            # supersampling

# ---------------------------------------------------------------- the three looks
LOOKS = {
    # A: golden hour, an open view to the hills; the cheapest atlas
    "A": dict(
        title="Golden hour", seed=11,
        sky=[(-30, (226, 150, 96)), (0, (255, 190, 112)), (2, (252, 178, 108)), (6, (238, 168, 124)),
             (14, (196, 162, 156)), (26, (132, 146, 186)), (45, (82, 108, 164)), (70, (52, 76, 132))],
        sun=(0.30, 0.040, 0.0105), sun_col=(255, 250, 230), glow=0.9, band=0.6,
        amb=(0.30, 0.27, 0.32), roof=(0.56, 0.48, 0.47), rim=1.0, vis=3400.0,
        lit=0.14, warm=0.70, sodium=0.5, clouds=0.55, cloud_hi=(255, 196, 150), cloud_lo=(176, 150, 170),
        near="open", dens=0.80,
        layers=["sky", "ridge", "far", "mid", "near"], atlas=(2048, 2048)),
    # B: the sun touching the ridge, afterglow, the first lights
    "B": dict(
        title="Sun on the ridge", seed=22,
        sky=[(-30, (214, 128, 84)), (0, (255, 172, 92)), (1.5, (250, 160, 96)), (5, (226, 150, 120)),
             (11, (174, 140, 158)), (20, (120, 128, 176)), (38, (72, 94, 156)), (70, (38, 56, 112))],
        sun=(0.30, 0.004, 0.0115), sun_col=(255, 246, 214), glow=1.0, band=1.0,
        amb=(0.25, 0.24, 0.32), roof=(0.44, 0.39, 0.46), rim=0.8, vis=3000.0,
        lit=0.30, warm=0.64, sodium=0.8, clouds=0.75, cloud_hi=(255, 170, 128), cloud_lo=(150, 124, 160),
        near="open", dens=1.0,
        layers=["sky", "ridge", "far", "mid", "near"], atlas=(2048, 2048)),
    # C: blue hour on a lane: the sun gone, a lit block of flats across the road, sodium lamps
    "C": dict(
        title="Lamps on, across the lane", seed=33,
        sky=[(-30, (170, 104, 86)), (0, (238, 140, 82)), (1.2, (226, 136, 96)), (4, (176, 124, 132)),
             (9, (118, 116, 164)), (18, (78, 96, 156)), (36, (46, 66, 126)), (70, (24, 36, 84))],
        sun=(0.30, -0.030, 0.0115), sun_col=(255, 190, 120), glow=0.75, band=1.2,
        amb=(0.17, 0.18, 0.27), roof=(0.30, 0.30, 0.42), rim=0.35, vis=2600.0,
        lit=0.46, warm=0.62, sodium=1.0, clouds=0.6, cloud_hi=(236, 140, 120), cloud_lo=(96, 96, 140),
        near="lane", dens=1.0,
        layers=["sky", "ridge", "far", "mid", "near"], atlas=(2048, 2048)),
}

# layer name: distance from camera_intro (m), tangent box (u0, u1, v0, v1), texels per tangent unit at dens 1
LAYER_SPEC = {
    "sky":   dict(L=18.0, box=(-1.60, 1.60, -0.30, 1.30), tpu=230, opaque=True),
    "ridge": dict(L=16.0, box=(-1.30, 1.30, -0.035, 0.125), tpu=470),
    "far":   dict(L=13.5, box=(-1.10, 1.10, -0.050, 0.110), tpu=640),
    "mid":   dict(L=10.0, box=(-0.95, 0.95, -0.110, 0.300), tpu=960),
    "near":  dict(L=7.0,  box=(-0.88, 0.88, -0.560, 0.360), tpu=1130),
}

PAINTS = [(232, 218, 186), (236, 212, 150), (226, 168, 136), (186, 204, 166), (228, 228, 222), (176, 174, 170),
          (176, 194, 212), (156, 150, 144), (214, 196, 170), (200, 150, 150)]


def clamp8(a):
    return np.clip(a, 0, 255)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def mul(a, b):
    return tuple(a[i] * b[i] for i in range(3))


def ci(c, a=255):
    return tuple(int(max(0, min(255, round(x)))) for x in c) + (a,)


class Look:
    def __init__(self, key):
        self.key = key
        self.p = dict(LOOKS[key])
        self.rng = np.random.default_rng(self.p["seed"])
        us, dv, rs = self.p["sun"]                       # the sun's height is given above the near ridge's line
        self.ridge_u = np.linspace(-1.3, 1.3, 2048)
        self.ridges = [ridges_top(self.ridge_u, self.p["seed"], i) for i in range(2)]
        self.p["sun"] = (us, float(np.interp(us, self.ridge_u, self.ridges[1])) + dv, rs)

    def sky(self, u, v):
        """Sky colour (float arrays) at tangent u, v: stops by elevation, the sun's glow, an afterglow band."""
        p = self.p
        e = np.degrees(np.arctan(v))
        st = p["sky"]
        out = np.zeros(np.broadcast(u, v).shape + (3,), np.float32)
        for c in range(3):
            out[..., c] = np.interp(e, [s[0] for s in st], [s[1][c] for s in st])
        us, vs, _ = p["sun"]
        d = np.hypot((u - us) * 0.75, (v - vs) * 1.6)
        g = (np.exp(-d / 0.035) * 0.55 + np.exp(-d / 0.16) * 0.40 + np.exp(-d / 0.55) * 0.22) * p["glow"]
        band = p["band"] * np.exp(-np.clip(v, 0, None) / 0.05) * np.exp(-np.abs(u - us) / 0.9) * 0.35
        warm = np.array([255, 196, 128], np.float32)
        out = out + (g + band)[..., None] * (warm - out * 0.6) * 0.75
        east = np.clip(-(u - us) / 2.4, 0, 1)[..., None]           # away from the sun: a little bluer, darker
        out = out * (1 - 0.14 * east) + 0.14 * east * out * np.array([0.82, 0.88, 1.10], np.float32)
        return out

    def horizon(self, u):
        return tuple(float(x) for x in self.sky(np.float32(u), np.float32(0.012)))

    def haze(self, col, R, u, k=1.0):
        t = (1 - math.exp(-R / self.p["vis"])) * k
        hz = lerp(self.horizon(u), tuple(float(x) for x in self.sky(np.float32(u), np.float32(0.14))), 0.45)
        return lerp(col, hz, min(1.0, t))


class Layer:
    def __init__(self, look, name):
        self.look, self.name = look, name
        s = LAYER_SPEC[name]
        self.L, (self.u0, self.u1, self.v0, self.v1) = s["L"], s["box"]
        self.tpu = s["tpu"] * look.p["dens"]
        self.w = int(round((self.u1 - self.u0) * self.tpu))
        self.h = int(round((self.v1 - self.v0) * self.tpu))
        self.W, self.H = self.w * SS, self.h * SS
        self.opaque = s.get("opaque", False)
        self.img = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.glow = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))   # soft halos, alpha-blended on top
        self.dg = ImageDraw.Draw(self.glow)
        self.k = self.tpu * SS                                          # px per tangent unit (supersampled)

    def px(self, u, v):
        return ((u - self.u0) * self.k, (self.v1 - v) * self.k)

    def p3(self, X, Y, Z):
        """Real metres: X right, Y forward from the eye, Z above the street."""
        return self.px(X / Y, (Z - EYE_H) / Y)

    def m(self, metres, Y):
        return metres / Y * self.k

    def poly(self, pts3, col, a=255):
        self.d.polygon([self.p3(*q) for q in pts3], fill=ci(col, a))

    def rect(self, X0, X1, Z0, Z1, Y, col, a=255, d=None):
        x0, y0 = self.p3(X0, Y, Z1)
        x1, y1 = self.p3(X1, Y, Z0)
        (d or self.d).rectangle([x0, y0, max(x0, x1 - 1), max(y0, y1 - 1)], fill=ci(col, a))

    def halo(self, X, Y, Z, r_m, col, a):
        x, y = self.p3(X, Y, Z)
        r = max(1.5, self.m(r_m, Y))
        for k in range(4, 0, -1):
            rr = r * k / 4
            self.dg.ellipse([x - rr, y - rr, x + rr, y + rr], fill=ci(col, int(a * (1.15 - k / 4) ** 1.5)))

    def mist(self, v_top, k):
        """Haze lying low: covered texels below v_top pulled towards the horizon's colour, up to k at the bottom."""
        a = np.asarray(self.img).astype(np.float32)
        ys = np.arange(self.H, dtype=np.float32)
        v = self.v1 - (ys + 0.5) / self.k
        t = (np.clip((v_top - v) / (v_top - self.v0), 0, 1) ** 0.7 * k)[:, None, None]
        u = self.u0 + (np.arange(self.W, dtype=np.float32) + 0.5) / self.k
        hz = self.look.sky(u, np.full_like(u, 0.012))[None]
        a[..., :3] = a[..., :3] * (1 - t) + hz * t
        self.img = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
        self.d = ImageDraw.Draw(self.img)

    def finish(self):
        img = self.img
        if self.glow.getbbox():
            g = self.glow.filter(ImageFilter.GaussianBlur(SS * 1.5))
            img = Image.alpha_composite(img, g)
        a = np.asarray(img).astype(np.float32) / 255.0
        if self.opaque:
            a[..., 3] = 1.0
        pm = a.copy()
        pm[..., :3] *= pm[..., 3:4]
        chans = [Image.fromarray(pm[..., c]).resize((self.w, self.h), Image.LANCZOS) for c in range(4)]
        pm = np.stack([np.asarray(c) for c in chans], -1).clip(0, 1)
        al = pm[..., 3:4]
        rgb = np.where(al > 1e-3, pm[..., :3] / np.maximum(al, 1e-3), 0)
        rgb = bleed(rgb, al[..., 0])
        out = np.concatenate([rgb, al], -1)
        self.final = Image.fromarray((out * 255 + 0.5).clip(0, 255).astype(np.uint8), "RGBA")
        return self.final


def bleed(rgb, al, steps=24):
    """Transparent texels take the colour of the nearest covered ones."""
    have = al > 0.02
    col = rgb * have[..., None]
    w = have.astype(np.float32)
    for _ in range(steps):
        if have.all():
            break
        cs = sum(np.roll(np.roll(col, dy, 0), dx, 1) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        ws = sum(np.roll(np.roll(w, dy, 0), dx, 1) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        new = (~have) & (ws > 0)
        col[new] = cs[new] / ws[new][:, None]
        w[new] = 1.0
        have = have | new
    mean = col[have].mean(0) if have.any() else np.zeros(3)
    col[~have] = mean
    return np.where(al[..., None] > 0.02, rgb, col)


# ---------------------------------------------------------------- the sky
def paint_sky(lay):
    lk = lay.look
    ys, xs = np.mgrid[0:lay.H, 0:lay.W].astype(np.float32)
    u = lay.u0 + (xs + 0.5) / lay.k
    v = lay.v1 - (ys + 0.5) / lay.k
    col = lk.sky(u, v)
    # clouds: stretched value noise, thin long banks lit from below (warm towards the sun), a few streaks low down
    r = np.random.default_rng(lk.p["seed"] + 1)
    n = np.zeros((lay.H, lay.W), np.float32)
    for (gw, gh), amp in (((10, 14), 0.55), ((22, 36), 0.28), ((46, 90), 0.17)):
        g = Image.fromarray(r.random((gh, gw)).astype(np.float32))
        n += np.asarray(g.resize((lay.W, lay.H), Image.BICUBIC)) * amp
    n = (n - n.min()) / (n.max() - n.min())
    bandv = np.exp(-((v - 0.32) / 0.16) ** 2) + 0.55 * np.exp(-((v - 0.075) / 0.03) ** 2)
    c = np.clip((n - 0.52) / 0.16, 0, 1) * bandv * lk.p["clouds"]
    us = lk.p["sun"][0]
    near_sun = np.exp(-np.abs(u - us) / 0.9)[..., None]
    lit = np.array(lk.p["cloud_hi"], np.float32) * near_sun + np.array(lk.p["cloud_lo"], np.float32) * (1 - near_sun)
    c = c[..., None]
    col = col * (1 - 0.7 * c) + 0.7 * c * lit
    lay.img = Image.fromarray(clamp8(col).astype(np.uint8), "RGB").convert("RGBA")
    lay.d = ImageDraw.Draw(lay.img)


# ---------------------------------------------------------------- the ridge, the sun
RIDGES = ((15000, 5, 0.010, 0.050), (7000, 6, 0.002, 0.052))   # real distance, seed, base, height (tangent)


def ridges_top(xs, seed, i):
    R, sd, base, amp = RIDGES[i]
    top = ridge_profile(xs, sd + seed, base, amp)
    if i == 1:      # Sinhagad-like: one big flat-topped massif left of centre
        top = np.maximum(top, base + 0.072 * np.clip(1 - np.abs((xs + 0.66) / 0.17) ** 5, 0, 1) ** 0.35)
    return top


def ridge_profile(xs, seed, base, amp, n=7):
    """Deccan trap hills: separate flat-topped massifs with steep scarps, a terrace or two, a low rolling base."""
    r = np.random.default_rng(seed)
    h = np.zeros_like(xs)
    for a, f in ((0.10, 2.0), (0.05, 5.0), (0.02, 13.0)):
        h += a * (1 + np.sin(xs * f * 3.0 + r.uniform(0, 6.3)))
    for _ in range(n):
        c, w = r.uniform(xs[0], xs[-1]), r.uniform(0.08, 0.26)
        top, pw = r.uniform(0.35, 1.0), r.uniform(2.5, 6.0)
        m = np.clip(1 - np.abs((xs - c) / w) ** pw, 0, 1)
        step = np.where(np.abs(xs - c) < w * r.uniform(0.3, 0.6), 1.0, r.uniform(0.75, 0.9))   # a terrace
        h = np.maximum(h, top * m ** 0.35 * step)
    return base + amp * h


def paint_ridge(lay):
    lk = lay.look
    us, vs, rs = lk.p["sun"]
    # the sun's disc (behind the ridge in B), with a few thin cloud streaks across it
    x, y = lay.px(us, vs)
    r = rs * lay.k
    lay.d.ellipse([x - r, y - r, x + r, y + r], fill=ci(lk.p["sun_col"]))
    rr = np.random.default_rng(lk.p["seed"] + 2)
    for k in range(3):
        sv = vs + rr.uniform(-0.4, 0.9) * rs * 1.4
        su = us + rr.uniform(-0.15, 0.1)
        ln = rr.uniform(0.18, 0.4)
        th = max(1.0, rr.uniform(0.0012, 0.0028) * lay.k)
        c = lerp(lk.horizon(su), (120, 90, 110), 0.35)
        x0, y0 = lay.px(su - ln / 2, sv)
        x1, _ = lay.px(su + ln / 2, sv)
        lay.d.rounded_rectangle([x0, y0 - th / 2, x1, y0 + th / 2], radius=th / 2, fill=ci(lerp(c, lk.horizon(su), 0.3)))
    xs = np.linspace(lay.u0, lay.u1, lay.W)
    for i, (R, _, base, _) in enumerate(RIDGES):
        top = np.interp(xs, lk.ridge_u, lk.ridges[i])
        col = lerp((52, 48, 76), lk.horizon(0.0), 0.50 if R > 10000 else 0.28)
        pts = [lay.px(lay.u0, lay.v0 - 0.01)] + [lay.px(u, t) for u, t in zip(xs[::2], top[::2])] + \
              [lay.px(lay.u1, lay.v0 - 0.01)]
        lay.d.polygon(pts, fill=ci(col))
        # the lit rim on the sun side
        if lk.p["rim"] > 0.5 and R < 10000:
            for u, t in zip(xs[::3], top[::3]):
                w = math.exp(-abs(u - us) / 0.25) * lk.p["rim"]
                if w > 0.15:
                    a, b = lay.px(u, t)
                    lay.d.point((a, b + 1), fill=ci(lerp(col, (255, 190, 120), 0.5 * w)))
    # the haze lying in the valley in front of the hills
    lay.mist(0.006, 0.55)


# ---------------------------------------------------------------- buildings
class City:
    def __init__(self, lay):
        self.lay, self.lk = lay, lay.look
        self.p = self.lk.p

    def facade(self, paint, R, u, k=1.0):
        return self.lk.haze(mul(paint, self.p["amb"]), R, u, k)

    def roofc(self, paint, R, u):
        base = lerp(mul(paint, self.p["roof"]), (150, 140, 150), 0.35)
        return self.lk.haze(base, R, u)

    def rim(self, u):
        us = self.p["sun"][0]
        return self.p["rim"] * math.exp(-abs(u - us) / 0.5)

    def lit_colour(self, r):
        p = self.p
        x = r.random()
        if x < p["warm"] * 0.8:
            return (255, 186, 104)                    # a warm bulb
        if x < p["warm"]:
            return (255, 222, 170)                    # a warm LED
        if x < p["warm"] + 0.05:
            return (255, 150, 112)                    # an orange curtain
        if x < p["warm"] + 0.08:
            return (130, 168, 255)                    # a television
        return (214, 236, 255)                        # a tube light

    def box(self, X, Y, w, d, h, paint, r, kind="flat", lit=None, detail=2):
        """One building. X: left edge, Y: front's distance, w, d, h metres. detail 0 far, 1 mid, 2 near."""
        lay, lk = self.lay, self.lk
        u = (X + w / 2) / Y
        lit = self.p["lit"] if lit is None else lit
        fc = self.facade(paint, Y, u)
        sc = lerp(fc, (0, 0, 0), 0.25)
        rc = self.roofc(paint, Y, u)
        para = 1.0 if kind != "tower" else 1.5
        top = h + para
        # the side facing the view axis
        if X + w < 0:
            lay.poly([(X + w, Y, 0), (X + w, Y + d, 0), (X + w, Y + d, top), (X + w, Y, top)], sc)
        elif X > 0:
            lay.poly([(X, Y, 0), (X, Y + d, 0), (X, Y + d, top), (X, Y, top)], sc)
        # the roof, seen from above when it is below the eye, with its clutter
        if h < EYE_H - 0.5:
            lay.poly([(X, Y, h), (X + w, Y, h), (X + w, Y + d, h), (X, Y + d, h)], rc)
            lay.poly([(X, Y + d, h), (X + w, Y + d, h), (X + w, Y + d, top), (X, Y + d, top)], lerp(fc, rc, 0.4))
            for sx in (X, X + w):
                lay.poly([(sx, Y, h), (sx, Y + d, h), (sx, Y + d, top), (sx, Y, top)], lerp(fc, rc, 0.5))
        if detail >= 1 and kind != "tower":
            self.roof_clutter(X, Y, w, d, h, paint, r, detail)
        # the front
        if kind == "setback" and detail >= 1:
            sb = min(2, int(h / 3) - 1) * 3.0
            lay.rect(X, X + w, 0, h - sb + para, Y, fc)
            lay.rect(X + w * 0.15, X + w * 0.85, h - sb, top, Y + 0.5, fc)
        else:
            lay.rect(X, X + w, 0, top, Y, fc)
        if kind == "tower":
            self.crown(X, Y, w, h, fc, r)
        # the warm rim of the setting sun along the parapet's top
        rm = self.rim(u)
        if rm > 0.08:
            th = max(SS * 0.8, lay.m(0.15, Y))
            x0, y0 = lay.p3(X, Y, top)
            x1, _ = lay.p3(X + w, Y, top)
            lay.d.rectangle([x0, y0, x1, y0 + th], fill=ci(lerp(fc, (255, 200, 140), min(0.8, 0.6 * rm))))
        self.windows(X, Y, w, h, fc, paint, r, lit, detail, kind)
        if detail >= 1 and kind not in ("tower",):
            # the monsoon stains under the parapet
            for _ in range(int(w / 3)):
                sx = X + r.uniform(0, w)
                ln = r.uniform(1.5, 6.0)
                x0, y0 = lay.p3(sx, Y, top - 0.3)
                x1, y1 = lay.p3(sx + r.uniform(0.3, 0.9), Y, max(0.0, top - ln))
                lay.d.rectangle([x0, y0, x1, y1], fill=ci(lerp(fc, (10, 10, 18), 0.12)))

    def crown(self, X, Y, w, h, fc, r):
        lay = self.lay
        lay.rect(X + w * 0.25, X + w * 0.75, h, h + 4.0, Y + 1, lerp(fc, (0, 0, 0), 0.1))
        lay.rect(X + w * 0.45, X + w * 0.55, h + 4, h + 9.0, Y + 1, lerp(fc, (0, 0, 0), 0.2))
        lay.halo(X + w * 0.5, Y + 1, h + 9.0, 0.9, (255, 60, 40), 230)
        x, y = lay.p3(X + w * 0.5, Y + 1, h + 9.0)
        rr = max(1.0, lay.m(0.25, Y))
        lay.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 90, 70, 255))

    def roof_clutter(self, X, Y, w, d, h, paint, r, detail):
        lay, lk = self.lay, self.lk
        u = (X + w / 2) / Y
        items = []
        # black Sintex water tanks on steel stands, one to four
        for _ in range(int(r.integers(1, 5))):
            items.append(("tank", X + r.uniform(0.1, 0.8) * w, Y + r.uniform(0.2, 0.8) * d))
        if r.random() < 0.6:
            items.append(("stair", X + r.uniform(0.05, 0.6) * w, Y + r.uniform(0.3, 0.7) * d))
        if detail >= 2:
            if r.random() < 0.5:
                items.append(("dish", X + r.uniform(0.1, 0.9) * w, Y + r.uniform(0.1, 0.4) * d))
            if r.random() < 0.5:
                items.append(("line", X + r.uniform(0.1, 0.5) * w, Y + r.uniform(0.3, 0.6) * d))
            if r.random() < 0.3:
                items.append(("rebar", X + r.uniform(0.1, 0.8) * w, Y + r.uniform(0.1, 0.9) * d))
        items.sort(key=lambda t: -t[2])
        dark = lk.haze((18, 18, 24), Y, u)
        for kind, x, y in items:
            if kind == "tank":
                tr, th = 0.65, 1.3
                lay.rect(x - tr * 0.8, x + tr * 0.8, h, h + 0.9, y, lerp(dark, (90, 90, 96), 0.3))   # the stand
                lay.rect(x - tr, x + tr, h + 0.9, h + 0.9 + th, y, dark)
                x0, y0 = lay.p3(x - tr, y, h + 0.9 + th + 0.25)
                x1, y1 = lay.p3(x + tr, y, h + 0.9 + th - 0.25)
                lay.d.ellipse([x0, y0, x1, y1], fill=ci(lerp(dark, (120, 110, 120), 0.25)))
                rm = self.rim(u)
                if rm > 0.1:
                    lay.d.arc([x0, y0, x1, y1], 200, 340, fill=ci(lerp(dark, (255, 190, 130), 0.5 * rm)))
            elif kind == "stair":
                sw, sd, sh = r.uniform(2.5, 3.5), 3.0, 2.6
                c = self.facade(paint, y, u)
                if h + sh < EYE_H:
                    lay.poly([(x, y, h + sh), (x + sw, y, h + sh), (x + sw, y + sd, h + sh), (x, y + sd, h + sh)],
                             self.roofc(paint, y, u))
                lay.rect(x, x + sw, h, h + sh, y, c)
                lay.rect(x + sw * 0.3, x + sw * 0.6, h, h + 2.0, y - 0.01, lerp(c, (0, 0, 0), 0.5))  # its door
            elif kind == "dish":
                x0, y0 = lay.p3(x - 0.4, y, h + 1.6)
                x1, y1 = lay.p3(x + 0.4, y, h + 0.8)
                lay.d.ellipse([x0, y0, x1, y1], fill=ci(lk.haze((170, 170, 176), y, u)))
                lay.d.line([lay.p3(x, y, h), lay.p3(x, y, h + 1.0)], fill=ci(dark), width=max(1, int(lay.m(0.06, y))))
            elif kind == "line":                     # a clothesline with the day's washing
                ln = r.uniform(3, 6)
                a, b = lay.p3(x, y, h + 1.6), lay.p3(x + ln, y, h + 1.6)
                lay.d.line([a, b], fill=ci(dark), width=max(1, int(lay.m(0.03, y))))
                for k in range(int(ln / 0.6)):
                    if r.random() < 0.6:
                        cc = PAINTS[int(r.integers(len(PAINTS)))]
                        cc = lerp(mul(cc, self.p["roof"]), (80, 60, 90), r.uniform(0, 0.4))
                        lay.rect(x + k * 0.6, x + k * 0.6 + 0.45, h + 0.9, h + 1.6, y, lk.haze(cc, y, u))
            elif kind == "rebar":                    # columns left for the next floor: Pune is always building
                for k in range(int(r.integers(2, 5))):
                    cx = x + k * r.uniform(1.5, 3.0)
                    if cx > X + w:
                        break
                    lay.d.line([lay.p3(cx, y, h), lay.p3(cx, y, h + 1.4)], fill=ci(dark),
                               width=max(1, int(lay.m(0.05, y))))

    def windows(self, X, Y, w, h, fc, paint, r, lit, detail, kind):
        lay, lk = self.lay, self.lk
        u = (X + w / 2) / Y
        fl = 3.0
        nf = max(1, int(h / fl))
        bay = 3.2 if kind != "tower" else 2.2
        nb = max(1, int(w / bay))
        balconies = kind in ("balcony", "setback") and detail >= 1
        lit_b = lit * r.uniform(0.5, 1.6)
        glass = lerp(lerp(fc, (0, 0, 0), 0.35), lk.sky(np.float32(u), np.float32(0.25)).tolist(), 0.18)
        for f in range(nf):
            z0 = f * fl
            if kind == "setback" and z0 > h - 2 * fl - 0.1:
                continue
            if f == 0 and detail >= 2:                # the ground floor: shops with shutters, a lit sign or two
                if r.random() < 0.5:
                    for b in range(nb):
                        cx = X + (b + 0.5) * w / nb
                        on = r.random() < 0.35
                        col = (255, 214, 150) if on else lerp(fc, (0, 0, 0), 0.4)
                        lay.rect(cx - 1.2, cx + 1.2, 0.0, 2.6, Y - 0.01, col)
                        if on and r.random() < 0.5:
                            lay.rect(cx - 1.3, cx + 1.3, 2.8, 3.4, Y - 0.02,
                                     [(240, 90, 70), (90, 200, 160), (250, 220, 120)][int(r.integers(3))])
                continue
            if balconies:
                # the slab, the railing, the recessed wall, a door and a window per flat
                sl = lerp(fc, (210, 200, 210), 0.25)
                lay.rect(X + 0.2, X + w - 0.2, z0 + 0.0, z0 + 0.22, Y - 0.6, sl)
                lay.rect(X + 0.3, X + w - 0.3, z0 + 0.22, z0 + fl, Y - 0.02, lerp(fc, (0, 0, 0), 0.25))
            for b in range(nb):
                cx = X + (b + 0.5) * w / nb
                on = r.random() < lit_b
                if balconies:
                    ww, wh, wz = 1.0, 2.1, z0 + 0.25
                else:
                    ww, wh, wz = (1.3, 1.35, z0 + 0.95) if kind != "tower" else (1.6, 2.2, z0 + 0.4)
                if on:
                    col = self.lit_colour(r)
                    k = r.uniform(0.75, 1.0)
                    col = lerp(fc, col, k)
                    col = lk.haze(col, Y, u, 0.6)
                else:
                    col = glass
                lay.rect(cx - ww / 2, cx + ww / 2, wz, wz + wh, Y - 0.01, col)
                pxw = lay.m(ww, Y)
                if detail >= 1 and pxw > 9:
                    frame = lerp(fc, (0, 0, 0), 0.45)
                    lw = max(1, int(lay.m(0.06, Y)))
                    a, b0 = lay.p3(cx, Y, wz + wh)
                    _, b1 = lay.p3(cx, Y, wz)
                    lay.d.line([(a, b0), (a, b1)], fill=ci(frame), width=lw)
                    if not balconies:
                        a0, bm = lay.p3(cx - ww / 2, Y, wz + wh * 0.62)
                        a1, _ = lay.p3(cx + ww / 2, Y, wz + wh * 0.62)
                        lay.d.line([(a0, bm), (a1, bm)], fill=ci(frame), width=lw)
                    if pxw > 22 and not balconies:          # the grille box over the window
                        gc = lerp(fc, (0, 0, 0), 0.6)
                        for g in range(1, 6):
                            gx = cx - ww / 2 + ww * g / 6
                            lay.d.line([lay.p3(gx, Y - 0.25, wz - 0.05), lay.p3(gx, Y - 0.25, wz + wh + 0.05)],
                                       fill=ci(gc), width=max(1, lw // 2))
                    if r.random() < 0.25 and not balconies:  # a window AC
                        lay.rect(cx + ww / 2 + 0.1, cx + ww / 2 + 0.9, wz, wz + 0.55, Y - 0.3,
                                 lk.haze((150, 150, 156), Y, u))
                if balconies:
                    side = 1.4 if r.random() < 0.5 else -1.4
                    wc = col if (on and r.random() < 0.7) else glass
                    lay.rect(cx + side - 0.6, cx + side + 0.6, z0 + 1.0, z0 + 2.2, Y - 0.01, wc)
            if balconies:
                rc = lerp(fc, (0, 0, 0), 0.5)
                lw = max(1, int(lay.m(0.05, Y)))
                a0, b0 = lay.p3(X + 0.2, Y - 0.6, z0 + 1.05)
                a1, _ = lay.p3(X + w - 0.2, Y - 0.6, z0 + 1.05)
                lay.d.line([(a0, b0), (a1, b0)], fill=ci(rc), width=lw)
                if lay.m(0.12, Y) > 1.2:
                    n = int(w / 0.12 / 3)
                    for k in range(n):
                        gx = X + 0.2 + (w - 0.4) * k / max(1, n - 1)
                        lay.d.line([lay.p3(gx, Y - 0.6, z0 + 0.22), lay.p3(gx, Y - 0.6, z0 + 1.05)],
                                   fill=ci(lerp(rc, fc, 0.3)), width=max(1, lw // 2))
                if r.random() < 0.3 and detail >= 2:           # potted plants on the rail
                    for k in range(int(r.integers(1, 4))):
                        gx = X + r.uniform(0.5, w - 0.5)
                        a, b = lay.p3(gx, Y - 0.7, z0 + 1.3)
                        rr = lay.m(0.3, Y)
                        lay.d.ellipse([a - rr, b - rr, a + rr, b + rr], fill=ci(lk.haze((24, 40, 30), Y, u)))
        # a drain pipe
        if detail >= 1 and r.random() < 0.6:
            px_ = X + r.uniform(0.1, 0.9) * w
            lay.d.line([lay.p3(px_, Y - 0.05, 0), lay.p3(px_, Y - 0.05, h)], fill=ci(lerp(fc, (0, 0, 0), 0.4)),
                       width=max(1, int(lay.m(0.1, Y))))

    def tree(self, X, Y, h, rad, r, palm=False):
        lay, lk = self.lay, self.lk
        u = X / Y
        dark = lk.haze((26, 40, 34), Y, u)
        trunk = lk.haze((34, 30, 32), Y, u)
        if palm:
            pts, x = [], X
            bend = r.uniform(-0.12, 0.12)
            for k in range(12):
                z = h * k / 11
                pts.append(lay.p3(X + bend * z * z / h, Y, z))
            lay.d.line(pts, fill=ci(trunk), width=max(1, int(lay.m(0.35, Y))))
            cx, cz = X + bend * h, h
            for k in range(10):
                a = k / 10 * 2 * math.pi + r.uniform(-0.2, 0.2)
                ln = r.uniform(3.0, 4.5)
                fr = []
                for s in range(8):
                    t = s / 7
                    fr.append(lay.p3(cx + math.cos(a) * ln * t, Y + math.sin(a) * 0.5,
                                     cz + 0.8 * math.sin(math.pi * t * 0.7) - (1.6 * t * t) * (0.6 + 0.4 * abs(math.cos(a)))))
                lay.d.line(fr, fill=ci(dark), width=max(1, int(lay.m(0.4, Y))))
            return
        # a rain tree: a trunk, a broad crown of many small clumps, darker below, a warm edge towards the sun
        lay.d.line([lay.p3(X, Y, 0), lay.p3(X + r.uniform(-0.5, 0.5), Y, h * 0.6)], fill=ci(trunk),
                   width=max(1, int(lay.m(0.6, Y))))
        rm = self.rim(u)
        clumps = []
        for _ in range(int(40 + rad * 8)):
            a = r.uniform(0, 2 * math.pi)
            q = r.random() ** 0.6
            cx = X + math.cos(a) * rad * q
            cz = h - rad * 0.45 + math.sin(a) * rad * 0.45 * q + r.uniform(-0.3, 0.3)
            clumps.append((cz, cx, r.uniform(0.5, 1.2) * rad / 3.5))
        clumps.sort()
        for cz, cx, cr in clumps:
            t = (cz - (h - rad)) / rad
            c = lerp(dark, lk.haze((52, 70, 56), Y, u), max(0.0, min(1.0, t)))
            x, y = lay.p3(cx, Y, cz)
            rr = lay.m(cr, Y)
            lay.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=ci(c))
        if rm > 0.15:
            for cz, cx, cr in clumps[-8:]:
                x, y = lay.p3(cx, Y, cz + cr * 0.6)
                rr = lay.m(cr * 0.5, Y)
                lay.d.ellipse([x - rr, y - rr * 0.4, x + rr, y + rr * 0.4], fill=ci(lerp(dark, (240, 170, 110), 0.5 * rm)))

    def tiled(self, X, Y, w, d, h, paint, r):
        """An old one- or two-storey house with a Mangalore-tiled roof, a lit doorway or window."""
        lay, lk = self.lay, self.lk
        u = (X + w / 2) / Y
        fc = self.facade(paint, Y, u)
        tile = lk.haze(mul((150, 84, 66), self.p["roof"]), Y, u)
        ridge = h + 2.2
        lay.poly([(X - 0.4, Y - 0.6, h), (X + w + 0.4, Y - 0.6, h), (X + w + 0.4, Y + d / 2, ridge),
                  (X - 0.4, Y + d / 2, ridge)], tile)
        tile = lerp(tile, (40, 34, 44), 0.25)
        for k in range(1, 9):                      # tile courses
            t = k / 9
            a0, b0 = lay.p3(X - 0.4, Y - 0.6 + (d / 2 + 0.6) * t, h + 2.2 * t)
            a1, _ = lay.p3(X + w + 0.4, Y - 0.6 + (d / 2 + 0.6) * t, h + 2.2 * t)
            lay.d.line([(a0, b0), (a1, b0)], fill=ci(lerp(tile, (20, 16, 24), 0.3)), width=max(1, int(lay.m(0.05, Y))))
        rm = self.rim(u)
        a0, b0 = lay.p3(X - 0.4, Y + d / 2, ridge)
        a1, _ = lay.p3(X + w + 0.4, Y + d / 2, ridge)
        lay.d.line([(a0, b0), (a1, b0)], fill=ci(lerp(tile, (255, 190, 130), 0.4 * rm + 0.1)),
                   width=max(1, int(lay.m(0.12, Y))))
        lay.rect(X, X + w, 0, h, Y, fc)
        for k in range(max(1, int(w / 3.5))):
            cx = X + (k + 0.5) * w / max(1, int(w / 3.5))
            on = r.random() < self.p["lit"] * 1.6
            col = lerp(fc, self.lit_colour(r), 0.85) if on else lerp(fc, (0, 0, 0), 0.4)
            lay.rect(cx - 0.5, cx + 0.5, 1.0, 2.2, Y - 0.01, col)
            if h > 5:
                lay.rect(cx - 0.5, cx + 0.5, 4.0, 5.2, Y - 0.01, lerp(fc, (0, 0, 0), 0.4) if r.random() > self.p["lit"] else col)

    def crane(self, X, Y, h, r):
        lay, lk = self.lay, self.lk
        u = X / Y
        c = lk.haze((40, 40, 50), Y, u, 0.9)
        lw = max(1, int(lay.m(0.25, Y)))
        mw = 1.6
        for s in (0, mw):
            lay.d.line([lay.p3(X + s, Y, 0), lay.p3(X + s, Y, h)], fill=ci(c), width=lw)
        n = int(h / 2.5)
        for k in range(n):
            z0, z1 = h * k / n, h * (k + 1) / n
            lay.d.line([lay.p3(X, Y, z0), lay.p3(X + mw, Y, z1)], fill=ci(c), width=max(1, lw // 2))
        jl, cl = r.uniform(30, 45), 12.0
        jz = h
        lay.d.line([lay.p3(X - cl, Y, jz), lay.p3(X + mw + jl, Y, jz)], fill=ci(c), width=lw * 2)
        lay.d.line([lay.p3(X - cl, Y, jz + 1.6), lay.p3(X + jl * 0.9, Y, jz + 1.6)], fill=ci(c), width=lw)
        lay.d.line([lay.p3(X + mw / 2, Y, jz + 6), lay.p3(X + jl, Y, jz + 1.6)], fill=ci(c), width=max(1, lw // 2))
        lay.d.line([lay.p3(X + mw / 2, Y, jz + 6), lay.p3(X - cl, Y, jz + 1.6)], fill=ci(c), width=max(1, lw // 2))
        lay.rect(X - cl, X - cl + 4, jz - 2.0, jz + 0.5, Y, c)                      # the counterweight
        hx = X + jl * r.uniform(0.4, 0.8)
        lay.d.line([lay.p3(hx, Y, jz), lay.p3(hx, Y, jz - r.uniform(6, 20))], fill=ci(c), width=max(1, lw // 2))
        lay.halo(X + mw / 2, Y, jz + 6, 1.2, (255, 50, 40), 255)
        x, y = lay.p3(X + mw / 2, Y, jz + 6)
        rr = max(1.2, lay.m(0.35, Y))
        lay.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 80, 60, 255))

    def ground(self, R0, R1, col, lights=0, r=None):
        """The ground from R0 to R1 (and everything below the layer), with sodium lamps scattered on it."""
        lay = self.lay
        Xw = 4 * R1
        lay.poly([(-Xw, R1, 0), (Xw, R1, 0), (Xw, R0, -60), (-Xw, R0, -60)], col)
        for _ in range(lights):
            Y = R0 + (R1 - R0) * r.random() ** 0.7
            u = r.uniform(lay.u0, lay.u1)
            lay.halo(u * Y, Y, 6.0, 4.0 + Y * 0.004, (255, 160, 70), int(120 * self.p["sodium"]))
            x, y = lay.p3(u * Y, Y, 6.0)
            rr = max(0.8, lay.m(0.25, Y))
            lay.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=ci((255, 190, 110)))


# ---------------------------------------------------------------- the layers' contents
def scatter(r, lay, n, R0, R1, margin=0.05):
    out = []
    for _ in range(n):
        Y = R0 + (R1 - R0) * r.random() ** 0.8
        u = r.uniform(lay.u0 - margin, lay.u1 + margin)
        out.append((Y, u))
    return out


def paint_far(lay):
    lk = lay.look
    c = City(lay)
    r = np.random.default_rng(lk.p["seed"] + 30)
    c.ground(600, 3200, lk.haze((60, 56, 66), 2400, 0.0), lights=0)
    items = scatter(r, lay, 260, 800, 3000)
    for k in range(4):
        u = r.uniform(-0.9, 0.9)
        if abs(u - lk.p["sun"][0]) > 0.15 and abs(u + 0.42) > 0.12:
            items.append((r.uniform(1400, 2600), u, "tower"))
    for k in range(3):
        items.append((r.uniform(1100, 2200), r.uniform(-0.8, 0.8), "crane"))
    items.sort(key=lambda t: -t[0])
    for it in items:
        Y, u = it[0], it[1]
        kind = it[2] if len(it) > 2 else "flat"
        if kind == "crane":
            c.crane(u * Y, Y, r.uniform(50, 75), r)
            continue
        w = r.uniform(18, 50)
        h = r.uniform(10, 26) if kind == "flat" else r.uniform(45, 80)
        dd = r.uniform(12, 25)
        c.box(u * Y - w / 2, Y, w, dd, h, PAINTS[int(r.integers(len(PAINTS)))], r,
              kind="tower" if kind == "tower" else "flat", lit=lk.p["lit"] * 0.7, detail=0)
    # the city's own haze over its far edge
    lay.mist(0.02, 0.45)
    for _ in range(int(260 * lk.p["sodium"])):                       # the street lights already on
        Y = r.uniform(700, 2600)
        u = r.uniform(lay.u0, lay.u1)
        x, y = lay.p3(u * Y, Y, r.uniform(2, 8))
        lay.d.rectangle([x, y, x + 1, y + 1], fill=ci(lk.haze((255, 180, 100), Y, u, 0.3)))


def paint_parvati(lay, c, r):
    """Parvati hill and its temple, left of centre, about 1.2 km away."""
    lk = lay.look
    Y, cx, hh, hw = 820.0, -0.42 * 820.0, 92.0, 260.0
    xs = np.linspace(cx - hw, cx + hw, 120)
    prof = hh * np.clip(1 - ((xs - cx) / hw) ** 2, 0, 1) ** 0.8
    prof = np.minimum(prof, hh * 0.92) + np.where(np.abs(xs - cx) < 28, hh * 0.08, 0)
    col = lk.haze((44, 54, 50), Y, cx / Y)
    lay.d.polygon([lay.p3(cx - hw, Y, 0)] + [lay.p3(x, Y, z) for x, z in zip(xs, prof)] + [lay.p3(cx + hw, Y, 0)],
                  fill=ci(col))
    # trees on the slope
    tc = lk.haze((30, 44, 36), Y, cx / Y)
    for _ in range(160):
        x = r.uniform(cx - hw * 0.9, cx + hw * 0.9)
        z = hh * max(0.0, 1 - ((x - cx) / hw) ** 2) ** 0.8 * r.uniform(0.2, 0.97)
        a, b = lay.p3(x, Y - 5, z)
        rr = lay.m(r.uniform(4, 8), Y)
        lay.d.ellipse([a - rr, b - rr * 0.8, a + rr, b + rr * 0.8], fill=ci(tc))
    # the steps up the face, lit
    for k in range(18):
        t = k / 17
        x = cx - 120 + 120 * t
        z = hh * max(0.0, 1 - ((x - cx) / hw) ** 2) ** 0.8 * (0.25 + 0.7 * t)
        a, b = lay.p3(x, Y - 8, z)
        lay.d.point((a, b), fill=(255, 206, 140, 255))
    # the temple: a walled court, the shikhara, two domes
    top = hh
    tcol = lk.haze((70, 62, 70), Y, cx / Y)
    lay.rect(cx - 30, cx + 30, top - 2, top + 6, Y - 10, tcol)
    pts = []
    for k in range(25):                       # the spire: a curved cone with a kalash
        t = k / 24
        pts.append((cx - 6.5 * (1 - t) ** 0.7, top + 6 + 26 * t))
    pts += [(cx + 6.5 * (1 - (p[1] - top - 6) / 26) ** 0.7, p[1]) for p in reversed(pts)]
    lay.d.polygon([lay.p3(x, Y - 10, z) for x, z in pts], fill=ci(tcol))
    lay.d.line([lay.p3(cx, Y - 10, top + 32), lay.p3(cx, Y - 10, top + 35)], fill=ci(tcol), width=max(1, int(lay.m(1.0, Y))))
    for dx, rr in ((-20, 5.5), (19, 4.5)):
        a0, b0 = lay.p3(cx + dx - rr, Y - 10, top + 6 + rr * 1.8)
        a1, b1 = lay.p3(cx + dx + rr, Y - 10, top + 6 - rr * 0.2)
        lay.d.ellipse([a0, b0, a1, b1], fill=ci(tcol))
        lay.rect(cx + dx - rr, cx + dx + rr, top + 2, top + 6.8, Y - 10, tcol)
    rm = c.rim(cx / Y)
    if rm > 0.1:
        lay.d.line([lay.p3(x, Y - 10, z + 0.3) for x, z in pts[len(pts) // 2:]], fill=ci(lerp(tcol, (255, 200, 140), 0.6 * rm)),
                   width=max(1, int(lay.m(0.8, Y))))
    for k in range(9):                        # its first lamps
        lay.halo(cx - 28 + k * 7, Y - 12, top + 3, 3.0, (255, 200, 130), 160)
        a, b = lay.p3(cx - 28 + k * 7, Y - 12, top + 3)
        lay.d.point((a, b), fill=(255, 220, 160, 255))


def paint_mid(lay):
    lk = lay.look
    c = City(lay)
    r = np.random.default_rng(lk.p["seed"] + 40)
    c.ground(160, 1400, lk.haze((46, 44, 54), 600, 0.0))
    paint_parvati(lay, c, r)
    items = []
    for Y, u in scatter(r, lay, 80, 180, 720):
        if abs(u + 0.42) < 0.12 and Y > 380:                 # keep Parvati in view
            continue
        x = r.random()
        kind = "tower" if x < 0.05 else ("balcony" if x < 0.5 else ("setback" if x < 0.65 else "flat"))
        if kind == "tower" and abs(u - lk.p["sun"][0]) < 0.2:
            kind = "balcony"
        items.append((Y, u, kind))
    for Y, u in scatter(r, lay, 26, 170, 600):
        items.append((Y, u, "tree" if r.random() < 0.8 else "palm"))
    for k in range(2):
        items.append((r.uniform(330, 520), r.uniform(-0.6, 0.7), "crane"))
    items.sort(key=lambda t: -t[0])
    for Y, u, kind in items:
        if kind == "crane":
            c.crane(u * Y, Y, r.uniform(55, 70), r)
        elif kind in ("tree", "palm"):
            c.tree(u * Y, Y, r.uniform(10, 16), r.uniform(4, 8), r, palm=kind == "palm")
        else:
            w = r.uniform(14, 34)
            h = r.uniform(36, 58) if kind == "tower" else 3.0 * int(r.integers(2, 7)) + 0.5
            c.box(u * Y - w / 2, Y, w, r.uniform(12, 22), h, PAINTS[int(r.integers(len(PAINTS)))], r, kind=kind,
                  detail=1)
    c.ground(160, 175, lk.haze((40, 38, 46), 170, 0.0))         # the near edge, so the bottom row is solid
    lay.rect(-1e4, 1e4, -1e4, 0, 170, lk.haze((40, 38, 46), 170, 0.0))
    for _ in range(int(60 * lk.p["sodium"])):
        Y = r.uniform(180, 650)
        u = r.uniform(lay.u0, lay.u1)
        lay.halo(u * Y, Y, 6.5, 5.0, (255, 160, 70), int(150 * lk.p["sodium"]))


def row(c, r, R0, R1, u0, u1, hmax, lit, corridor, gap=0.35):
    """A row of low neighbours between R0 and R1 across u0..u1, with trees in the gaps; lower in the sun's corridor."""
    items = []
    u = u0
    while u < u1:
        Y = r.uniform(R0, R1)
        w = r.uniform(9, 20)
        cu, cw = corridor
        hm = min(hmax, 9.5) if abs(u + w / Y / 2 - cu) < cw else hmax
        h = 3.0 * int(r.integers(1, max(2, int(hm / 3.0)) + 1)) + 0.4
        x = r.random()
        kind = "balcony" if x < 0.4 else ("flat" if x < 0.85 else "setback")
        items.append((Y, u * Y, w, h, kind))
        u += w / Y
        if r.random() < gap:
            tu = u + r.uniform(0.0, 0.04)
            items.append((Y + r.uniform(-4, 6), tu * Y, r.uniform(8, 13), r.uniform(4, 7), "palm" if r.random() < 0.2 else "tree"))
            u += r.uniform(0.04, 0.10)
    return items


def paint_near(lay):
    lk = lay.look
    c = City(lay)
    r = np.random.default_rng(lk.p["seed"] + 50)
    road0, road1 = 24.0, 31.0
    gcol = lk.haze((34, 32, 38), 60, 0.0)
    c.ground(road1, 160, gcol)
    corridor = (lk.p["sun"][0], 0.14)
    items = row(c, r, 120, 155, lay.u0 - 0.02, lay.u1, 14.0, 1.0, corridor, gap=0.25)
    items += row(c, r, 70, 110, lay.u0 - 0.02, lay.u1, 12.0, 1.0, corridor, gap=0.3)
    items += row(c, r, 40, 62, lay.u0 - 0.02, lay.u1, 9.5, 1.0, corridor, gap=0.4)
    u = lay.u0 - 0.02
    while u < lay.u1:                          # old houses with tiled roofs, right behind the wall
        Y = r.uniform(32.5, 36.0)
        w = r.uniform(6, 11)
        items.append((Y, u * Y, w, r.choice([3.4, 3.4, 6.4]), "tiled"))
        u += w / Y + (r.uniform(0.03, 0.08) if r.random() < 0.5 else 0.005)
    if lk.p["near"] == "open":      # two taller neighbours frame the view, clear of the sun
        items += [(48, -0.84 * 48, 20, 15.4, "balcony"), (56, 0.62 * 56, 19, 15.4, "balcony")]
    else:                           # across the lane: a G+5 block of flats, its balconies lit
        items += [(33, -0.90 * 33, 24, 18.4, "balcony"), (60, 0.60 * 60, 18, 15.4, "balcony")]
    items.sort(key=lambda t: -t[0])
    for Y, X, a, b, kind in items:
        if kind in ("tree", "palm"):
            c.tree(X, Y, a, b, r, palm=kind == "palm")
        elif kind == "tiled":
            c.tiled(X, Y, a, 8.0, b, PAINTS[int(r.integers(len(PAINTS)))], r)
        else:
            c.box(X, Y, a, r.uniform(12, 18), b, PAINTS[int(r.integers(len(PAINTS)))], r, kind=kind, detail=2,
                  lit=lk.p["lit"] * 1.3)
    # a compound wall and the road, with sodium lamps and their pools
    wall = lk.haze((70, 64, 66), 30, 0.0)
    lay.rect(-200, 200, 0, 1.8, road1 + 0.5, mul(wall, (0.8, 0.8, 0.9)))
    lay.poly([(-200, road1, 0), (200, road1, 0), (200, road0, 0), (-200, road0, 0)], (30, 30, 36))
    lay.rect(-200, 200, -60, 0.0, road0, (26, 26, 32))
    for k in range(5):
        x = -26 + k * 13 + r.uniform(-1.5, 1.5)
        Y = road1 - 0.6
        pole = (40, 40, 46)
        lay.d.line([lay.p3(x, Y, 0), lay.p3(x, Y, 8.0)], fill=ci(pole), width=max(1, int(lay.m(0.15, Y))))
        lay.d.line([lay.p3(x, Y, 8.0), lay.p3(x + 1.6, Y - 1.2, 8.0)], fill=ci(pole), width=max(1, int(lay.m(0.12, Y))))
        s = lk.p["sodium"]
        a, b = lay.p3(x + 1.6, Y - 1.2, 7.8)
        rr = lay.m(0.28, Y)
        lay.d.ellipse([a - rr, b - rr * 0.6, a + rr, b + rr * 0.6], fill=ci((255, 186, 96)))
        lay.halo(x + 1.6, Y - 1.2, 7.8, 1.6, (255, 170, 80), int(200 * s))
        for q in range(6):                       # the pool on the road
            t = q / 6
            a0, b0 = lay.p3(x + 1.6 - 5 * (1 - t), Y - 1.2 - 3 * (1 - t), 0.0)
            a1, b1 = lay.p3(x + 1.6 + 5 * (1 - t), Y - 1.2 + 3 * (1 - t), 0.0)
            lay.dg.ellipse([a0, min(b0, b1) - 2, a1, max(b0, b1) + 2], fill=ci((255, 150, 60), int(30 * s)))
    # gulmohar trees on this side of the road, parked two-wheelers along the wall
    for k in range(4):
        x = -22 + k * 15 + r.uniform(-3, 3)
        c.tree(x, road0 + 0.8, r.uniform(7.5, 9.5), r.uniform(3.5, 4.5), r)
    for k in range(5):
        x = -28 + k * 12 + r.uniform(-3, 3)
        Y = road1 - 1.2
        col = [(200, 200, 204), (150, 30, 30), (60, 60, 70), (230, 230, 226), (40, 70, 120)][k]
        body = mul(col, lk.p["amb"])
        lay.rect(x, x + 4.2, 0.3, 1.0, Y, body)
        lay.poly([(x + 0.8, Y, 1.0), (x + 3.4, Y, 1.0), (x + 3.0, Y + 0.6, 1.5), (x + 1.2, Y + 0.6, 1.5)],
                 lerp(body, lk.horizon(x / Y), 0.35))          # the roof catching the sky
        for wx in (0.8, 3.4):
            a, b = lay.p3(x + wx, Y, 0.3)
            rr = lay.m(0.32, Y)
            lay.d.ellipse([a - rr, b - rr, a + rr, b + rr], fill=(18, 18, 22, 255))
    # a few vehicles: head and tail lights
    for k in range(4):
        x = r.uniform(-25, 25)
        Y = r.uniform(road0 + 1, road1 - 1)
        for dx in (0, 1.4):
            a, b = lay.p3(x + dx, Y, 0.7)
            rr = max(1.0, lay.m(0.12, Y))
            col = (255, 70, 50) if k % 2 else (255, 244, 220)
            lay.d.ellipse([a - rr, b - rr, a + rr, b + rr], fill=ci(col))
            lay.halo(x + dx, Y, 0.7, 0.5, col, 120)


PAINT = {"sky": paint_sky, "ridge": paint_ridge, "far": paint_far, "mid": paint_mid, "near": paint_near}


# ---------------------------------------------------------------- the atlas
def pack(rects, W):
    """Shelf packing, tallest first. rects: [(name, w, h)]. Returns {name: (x, y)}, height used."""
    pad = 4
    order = sorted(rects, key=lambda t: -t[2])
    pos, x, y, row = {}, 0, 0, 0
    for name, w, h in order:
        if x + w > W:
            x, y, row = 0, y + row + pad, 0
        pos[name] = (x, y)
        x += w + pad
        row = max(row, h)
    return pos, y + row


def build(key):
    look = Look(key)
    p = look.p
    layers = []
    for name in p["layers"]:
        lay = Layer(look, name)
        PAINT[name](lay)
        lay.finish()
        layers.append(lay)
        print(f"  {key} {name}: {lay.w} x {lay.h}")
    AW, AH = p["atlas"]
    pos, used = pack([(l.name, l.w, l.h) for l in layers], AW)
    if used > AH:
        raise SystemExit(f"{key}: the layers need {used} rows, the atlas has {AH}")
    atlas = Image.new("RGBA", (AW, AH), (0, 0, 0, 0))
    meta = dict(look=key, title=p["title"], atlas=f"city-{key}.png", size=[AW, AH], eye=list(EYE),
                street_z=STREET_Z, layers=[])
    for lay in sorted(layers, key=lambda l: -l.L):
        x, y = pos[lay.name]
        atlas.paste(lay.final, (x, y))
        # fill the pad round each block with its edge texels (no bleeding between blocks under filtering)
        meta["layers"].append(dict(
            name=lay.name, distance=lay.L, plane_y=round(EYE[1] + lay.L, 4),
            x0=round(EYE[0] + lay.u0 * lay.L, 4), x1=round(EYE[0] + lay.u1 * lay.L, 4),
            z0=round(EYE[2] + lay.v0 * lay.L, 4), z1=round(EYE[2] + lay.v1 * lay.L, 4),
            rect=[x, y, lay.w, lay.h], opaque=lay.opaque,
            uv=[(x + 0.5) / AW, 1 - (y + lay.h - 0.5) / AH, (x + lay.w - 0.5) / AW, 1 - (y + 0.5) / AH],
            skirt=not lay.opaque))
    a = np.asarray(atlas).copy()
    for L_ in meta["layers"]:
        x, y, w, h = L_["rect"]
        blk = a[y:y + h, x:x + w]
        y0, y1, x0, x1 = max(0, y - 2), min(AH, y + h + 2), max(0, x - 2), min(AW, x + w + 2)
        a[y0:y, x:x + w] = blk[:1]
        a[y + h:y1, x:x + w] = blk[-1:]
        a[y0:y1, x0:x] = a[y0:y1, x:x + 1]
        a[y0:y1, x + w:x1] = a[y0:y1, x + w - 1:x + w]
    atlas = Image.fromarray(a, "RGBA")
    os.makedirs(OUTDIR, exist_ok=True)
    png = os.path.join(OUTDIR, f"city-{key}.png")
    atlas.save(png, optimize=True)
    webp = os.path.join(OUTDIR, f"city-{key}.webp")
    atlas.save(webp, "WEBP", quality=88, method=6)
    meta["bytes_png"] = os.path.getsize(png)
    meta["bytes_webp_q88"] = os.path.getsize(webp)
    meta["gpu_bytes_rgba_mips"] = int(AW * AH * 4 * 4 / 3)
    with open(os.path.join(OUTDIR, f"city-{key}.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(f"wrote {png} ({meta['bytes_png'] // 1024} KB png, {meta['bytes_webp_q88'] // 1024} KB webp), rows used {used}")
    return meta


if __name__ == "__main__":
    for k in (sys.argv[1:] or list(LOOKS)):
        build(k)
