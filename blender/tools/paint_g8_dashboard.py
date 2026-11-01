"""Paint the G8's picture: a training dashboard with no words (2026-11-01, the lighting pass).

    /opt/anaconda3/bin/python3 blender/tools/paint_g8_dashboard.py [out.png]

The 34-inch shows "a live training dashboard" (decision 2026-10-23); until obj_rig draws the live one, this still
stands in, so the G8 glows at dusk instead of reading as a black slab. Panels on a navy ground: the loss falling
(cyan), the eval score rising (amber), eight GPU bars, a heatmap, a throughput sparkline. No text, no logo: the room's
words come from content. Plain numpy + Pillow, a fixed seed: the same picture every run. 21:9, as rig_screen.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1536, 640
BG, PANEL, EDGE, GRID = (9, 13, 26), (15, 22, 42), (34, 48, 82), (24, 34, 60)
CYAN, AMBER, BLUE, VIOLET = (90, 210, 255), (255, 176, 84), (110, 150, 255), (170, 120, 255)
rng = np.random.default_rng(7)


def panel(d, box):
    d.rounded_rectangle(box, 10, fill=PANEL, outline=EDGE, width=2)
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 + 18, y0 + 16, x0 + 18 + (x1 - x0) * 0.22, y0 + 24), 4, fill=EDGE)   # a title bar, no words


def grid(d, box, nx, ny):
    x0, y0, x1, y1 = box
    for i in range(1, nx):
        x = x0 + (x1 - x0) * i / nx
        d.line((x, y0, x, y1), fill=GRID, width=1)
    for j in range(1, ny):
        y = y0 + (y1 - y0) * j / ny
        d.line((x0, y, x1, y), fill=GRID, width=1)


def curve(d, box, ys, col, width=3):
    x0, y0, x1, y1 = box
    pts = [(x0 + (x1 - x0) * i / (len(ys) - 1), y1 - (y1 - y0) * v) for i, v in enumerate(ys)]
    d.line(pts, fill=col, width=width, joint="curve")
    return pts


def main(out):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # left: the loss, falling, with its smoothed line over the raw one
    L = (36, 36, 900, 420)
    panel(d, L)
    plot = (L[0] + 30, L[1] + 56, L[2] - 30, L[3] - 30)
    grid(d, plot, 10, 5)
    t = np.linspace(0, 1, 260)
    loss = 0.08 + 0.82 * np.exp(-4.2 * t) + 0.035 * rng.standard_normal(t.size) * (1 - 0.6 * t)
    smooth = np.convolve(loss, np.ones(15) / 15, mode="same")
    smooth[:7], smooth[-7:] = loss[:7].mean(), loss[-14:].mean()
    curve(d, plot, np.clip(loss, 0, 1), (40, 92, 120), 2)
    curve(d, plot, np.clip(smooth, 0, 1), CYAN, 4)
    # its eval score, rising, in the same plot
    ev = 0.15 + 0.7 * (1 - np.exp(-3.0 * t[::13]))
    pts = curve(d, plot, ev, AMBER, 3)
    for p in pts[::2]:
        d.ellipse((p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4), fill=AMBER)
    # right top: eight GPUs, utilisation bars
    G = (930, 36, 1500, 300)
    panel(d, G)
    bx0, by0, bx1, by1 = G[0] + 30, G[1] + 56, G[2] - 30, G[3] - 26
    util = [0.94, 0.91, 0.97, 0.89, 0.95, 0.92, 0.96, 0.90]
    bw = (bx1 - bx0) / 8
    for i, u in enumerate(util):
        x = bx0 + i * bw
        d.rounded_rectangle((x + 8, by0, x + bw - 8, by1), 5, fill=GRID)
        d.rounded_rectangle((x + 8, by1 - (by1 - by0) * u, x + bw - 8, by1), 5, fill=BLUE)
    # right bottom: a heatmap (attention-like), violet to cyan
    M = (930, 324, 1500, 604)
    panel(d, M)
    hx0, hy0, hx1, hy1 = M[0] + 30, M[1] + 52, M[2] - 30, M[3] - 22
    n, m = 22, 10
    cw, ch = (hx1 - hx0) / n, (hy1 - hy0) / m
    for i in range(n):
        for j in range(m):
            v = np.clip(np.exp(-((i / n - j / m) ** 2) / 0.02) * 0.85 + 0.25 * rng.random(), 0, 1)
            c = tuple(int(a + (b - a) * v) for a, b in zip(PANEL, (VIOLET if v < 0.6 else CYAN)))
            d.rectangle((hx0 + i * cw + 1, hy0 + j * ch + 1, hx0 + (i + 1) * cw - 1, hy0 + (j + 1) * ch - 1), fill=c)
    # bottom left: throughput sparkline and a progress bar
    S = (36, 444, 900, 604)
    panel(d, S)
    sp = (S[0] + 30, S[1] + 50, S[2] - 30, S[3] - 52)
    tp = 0.55 + 0.25 * np.sin(np.linspace(0, 18, 120)) * rng.random(120) + 0.1 * rng.random(120)
    curve(d, sp, np.clip(tp, 0, 1), VIOLET, 2)
    d.rounded_rectangle((S[0] + 30, S[3] - 34, S[2] - 30, S[3] - 22), 6, fill=GRID)
    d.rounded_rectangle((S[0] + 30, S[3] - 34, S[0] + 30 + (S[2] - S[0] - 60) * 0.68, S[3] - 22), 6, fill=CYAN)
    # a soft bloom of the bright lines, as an OLED reads in a dark room
    glow = im.filter(ImageFilter.GaussianBlur(6))
    im = Image.fromarray(np.clip(np.asarray(im, np.float32) + 0.35 * np.asarray(glow, np.float32), 0, 255).astype(np.uint8))
    im.save(out)
    print("wrote", out, im.size)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "assets", "dusk", "g8-dashboard.png"))
