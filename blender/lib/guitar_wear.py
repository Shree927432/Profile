"""Wear and finish fields for a worn guitar, from its spec (numpy only, no Blender), so the 2D
blueprint and the 3D material read the same maps. Used by guitar_04 (Number One).

    fields(G, head)        dict of float32 arrays on a 1 mm grid over the whole front view:
        dist     signed distance in from the body edge, mm (+ inside, - outside)
        finish   front: 1 where the sunburst survives (traced polygons, even-odd), soft edged
        pale     front: 1 where the bare wood is rubbed pale
        back     back: 1 where the wood shows (designed polygons), soft edged
        head     signed distance in from the headstock edge, mm (+ inside)
    GRID                   (u0, v0, step, width, height): pixel (i, j) is at u0 + (j + 0.5) * step,
                           v0 + (i + 0.5) * step (row 0 at the tail end)
    pack(f)                two RGB float images (rows from the tail up) for the material:
                           A = (dist, finish, pale), B = (back, head, 0), each scaled to 0..1 by ENC
    preview(G, f)          an sRGB uint8 picture of the finish (sunburst, wood, wear) for the sheet
"""
import math

import numpy as np

from .guitar_specs import spline

U0, U1, V0, V1, STEP = -172.0, 172.0, -16.0, 1000.0, 1.0
W, H = int((U1 - U0) / STEP), int((V1 - V0) / STEP)
GRID = (U0, V0, STEP, W, H)
ENC = dict(dist=(-20.0, 150.0), head=(-10.0, 30.0))     # value range stored in 0..1


def _grid(v_lo=V0, v_hi=V1):
    i0, i1 = int((v_lo - V0) / STEP), int(math.ceil((v_hi - V0) / STEP))
    i0, i1 = max(0, i0), min(H, i1)
    u = U0 + (np.arange(W) + 0.5) * STEP
    v = V0 + (np.arange(i0, i1) + 0.5) * STEP
    return np.meshgrid(u, v), (i0, i1)


def inside(polys, U, V):
    """Even-odd fill of several closed polygons."""
    res = np.zeros(U.shape, bool)
    for P in polys:
        P = np.asarray(P, float)
        A, B = P, np.roll(P, -1, axis=0)
        for (ax, ay), (bx, by) in zip(A, B):
            if ay == by:
                continue
            c = (ay > V) != (by > V)
            xi = ax + (V - ay) * (bx - ax) / (by - ay)
            res ^= c & (U < xi)
    return res


def distance(polys, U, V):
    """Unsigned distance to the edges of the polygons, mm."""
    d = np.full(U.shape, 1e9, np.float64)
    for P in polys:
        P = np.asarray(P, float)
        A, B = P, np.roll(P, -1, axis=0)
        for (ax, ay), (bx, by) in zip(A, B):
            ex, ey = bx - ax, by - ay
            L2 = ex * ex + ey * ey + 1e-12
            t = np.clip(((U - ax) * ex + (V - ay) * ey) / L2, 0.0, 1.0)
            dx, dy = U - (ax + t * ex), V - (ay + t * ey)
            np.minimum(d, dx * dx + dy * dy, out=d)
    return np.sqrt(d)


def blur(a, r):
    """Two box passes of radius r px each way (close to a gaussian of sigma about r * 0.8)."""
    r = int(round(r))
    if r < 1:
        return a
    out = a.astype(np.float64)
    for _ in range(2):
        for ax in (0, 1):
            p = np.pad(out, [(r + 1, r) if k == ax else (0, 0) for k in (0, 1)], mode="edge")
            c = np.cumsum(p, axis=ax)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[ax]), axis=ax)
            lo = np.take(c, np.arange(0, c.shape[ax] - 2 * r - 1), axis=ax)
            out = (hi - lo) / (2 * r + 1)
    return out


def fields(G, head):
    """head: the headstock outline in (u, v), open from one nut end to the other."""
    body = spline(G["body"])
    out = {}
    (U, V), (i0, i1) = _grid(V0, 480.0)
    inb = inside([body], U, V)
    d = distance([body], U, V)
    dist = np.full((H, W), ENC["dist"][0], np.float32)
    dist[i0:i1] = np.where(inb, d, -d).clip(*ENC["dist"])
    out["dist"] = dist
    fin = np.zeros((H, W), np.float32)
    fin[i0:i1] = inside(G["wear_front_finish"], U, V)
    out["finish"] = blur(fin, 1).astype(np.float32)
    pale = np.zeros((H, W), np.float32)
    pale[i0:i1] = inside(G["wear_front_pale"], U, V)
    out["pale"] = blur(pale, 1).astype(np.float32)
    back = np.zeros((H, W), np.float32)
    back[i0:i1] = inside([spline(p) for p in G["wear_back"]], U, V)
    out["back"] = blur(back, 3).astype(np.float32)
    (U, V), (j0, j1) = _grid(G["v_nut"] - 12.0, V1)
    hp = list(head) + [head[0]]
    inh = inside([hp], U, V)
    dh = distance([hp[:-1]], U, V)
    hd = np.full((H, W), ENC["head"][0], np.float32)
    hd[j0:j1] = np.where(inh, dh, -dh).clip(*ENC["head"])
    out["head"] = hd
    return out


def _enc(a, key):
    lo, hi = ENC[key]
    return ((a - lo) / (hi - lo)).clip(0, 1)


def pack(f):
    A = np.stack([_enc(f["dist"], "dist"), f["finish"], f["pale"]], -1).astype(np.float32)
    B = np.stack([f["back"], _enc(f["head"], "head"), np.zeros_like(f["back"])], -1).astype(np.float32)
    return A, B


def _hex(h):
    h = h.lstrip("#")
    return np.array([int(h[k:k + 2], 16) for k in (0, 2, 4)], np.float64)


def sunburst(G, d):
    st = G["sunburst"]
    xs = np.array([s[0] for s in st])
    cs = np.array([_hex(s[1]) for s in st])
    return np.stack([np.interp(d, xs, cs[:, k]) for k in range(3)], -1)


def preview(G, f, side="front", seed=4):
    """The finish as the material draws it, without lighting: rows top (headstock) first."""
    rng = np.random.default_rng(seed)
    d = f["dist"]
    burst = sunburst(G, np.clip(d, 0, None))
    wd = G["wood"]
    nz = blur(rng.random(d.shape), 2)
    nz = (nz - nz.mean()) / (nz.std() + 1e-9)
    grain = blur(rng.random(d.shape), 1)
    grime = _hex(wd["grime"]) * (0.9 + 0.2 * grain[..., None])
    wood = grime * (1 - f["pale"][..., None]) + _hex(wd["pale"]) * f["pale"][..., None] if side == "front" else grime
    keep = f["finish"] if side == "front" else 1.0 - f["back"]
    edge = np.clip((d + nz * 1.2 - G["edge_wear_mm"] * 0.5) / (G["edge_wear_mm"] * 0.6), 0, 1)
    s = np.clip((keep * edge - 0.5 + nz * 0.06) * 8 + 0.5, 0, 1)[..., None]
    rgb = burst * s + wood * (1 - s)
    out = np.where((d > 0)[..., None], rgb, 255.0)
    return out[::-1].clip(0, 255).astype(np.uint8)
