"""pc: a one-page blueprint (front, glass side, top of the case; the card's fan face) drawn from pc.py's
constants. Plain Python:  /opt/anaconda3/bin/python3 blender/components/pc_blueprint.py"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pc as K  # noqa: E402

S = 0.95            # px per mm
INK, BLUE, BG, GREY = (29, 39, 51), (47, 109, 181), (246, 244, 238), (150, 155, 160)


def fonts():
    try:
        return (ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30),
                ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20))
    except OSError:
        f = ImageFont.load_default()
        return f, f


def dim_h(d, x0, x1, y, text, f):
    d.line([(x0, y), (x1, y)], fill=BLUE, width=2)
    for x in (x0, x1):
        d.line([(x, y - 8), (x, y + 8)], fill=BLUE, width=2)
    w = d.textlength(text, font=f)
    d.text(((x0 + x1) / 2 - w / 2, y - 28), text, fill=BLUE, font=f)


def dim_v(d, x, y0, y1, text, f):
    d.line([(x, y0), (x, y1)], fill=BLUE, width=2)
    for y in (y0, y1):
        d.line([(x - 8, y), (x + 8, y)], fill=BLUE, width=2)
    d.text((x + 10, (y0 + y1) / 2 - 12), text, fill=BLUE, font=f)


def main(out):
    big, small = fonts()
    im = Image.new("RGB", (1920, 1080), BG)
    d = ImageDraw.Draw(im)
    W, D, H, F = K.CASE_W * 1000, K.CASE_D * 1000, K.CASE_H * 1000, K.FOOT_H * 1000
    d.text((24, 16), "pc: Lian Li O11 Vision (white) and RTX 5090 Founders Edition, from blender/components/pc.py (mm)",
           fill=INK, font=big)
    # front (x right, z up), origin bottom-left at (80, 640)
    ox, oy = 90, 590

    def P(x, z):
        return (ox + (x + W / 2) * S, oy - z * S)
    d.text((ox, 70), "front", fill=INK, font=small)
    d.rectangle([P(-W / 2, H), P(W / 2, F)], outline=INK, width=3)
    xp = W / 2 - K.PILLAR_W * 1000
    d.line([P(xp, H), P(xp, F)], fill=GREY, width=2)
    for side, (tw, bw) in (("L", (K.FOOT_L_TOP, K.FOOT_L_BOT)), ("R", (K.FOOT_R_TOP, K.FOOT_R_BOT))):
        s = -1 if side == "L" else 1
        xo = s * W / 2
        poly = [P(xo, 0), P(xo - s * bw * 1000, 0), P(xo - s * tw * 1000, F), P(xo, F)]
        d.polygon(poly, outline=INK, width=3)
    for x in K.IO_X:
        d.ellipse([P(x - 3, K.IO_Z * 1000 + 3), P(x + 3, K.IO_Z * 1000 - 3)], outline=INK)
    dim_h(d, P(-W / 2, 0)[0], P(W / 2, 0)[0], oy + 40, f"{W:.0f} (official)", small)
    dim_v(d, P(W / 2, 0)[0] + 30, P(0, H)[1], P(0, 0)[1], f"{H:.1f} (official)", small)
    dim_h(d, P(xp, H)[0], P(W / 2, H)[0], P(0, H)[1] - 20, f"{K.PILLAR_W * 1000:.0f}", small)
    dim_v(d, P(-W / 2, 0)[0] - 60, P(0, F)[1], P(0, 0)[1], f"{F:.1f}", small)
    # glass side (seen from -X: y to the left is the front)
    ox2 = 560

    def Q(y, z):
        return (ox2 + (D / 2 - y) * S, oy - z * S)
    d.text((ox2, 70), "glass side (left), front on the right", fill=INK, font=small)
    d.rectangle([Q(D / 2, H), Q(-D / 2, F)], outline=INK, width=3)
    zs = F - K.RAIL_H * 1000
    for end in (-1, 1):
        yo = end * D / 2
        yt, yb = yo - end * K.FOOT_Y_TOP * 1000, yo - end * K.FOOT_Y_BOT * 1000
        d.polygon([Q(yo, 0), Q(yb, 0), Q(yt, zs), Q(yt, F), Q(yo, F)], outline=INK, width=3)
    d.rectangle([Q(D / 2 - K.FOOT_Y_TOP * 1000, F), Q(-D / 2 + K.FOOT_Y_TOP * 1000, zs)], outline=INK, width=2)
    b = K.PSU_BRACKET
    d.rectangle([Q(b["y"][1] * 1000, b["z"][1] * 1000), Q(b["y"][0] * 1000, b["z"][0] * 1000)], outline=INK, width=2)
    dim_h(d, Q(D / 2, 0)[0], Q(-D / 2, 0)[0], oy + 40, f"{D:.0f} (official) + 14 PSU bracket", small)
    # top
    oy3 = 1050

    def T(x, y):
        return (ox + (x + W / 2) * S, oy3 - (y + D / 2) * S * 0.55)
    d.text((ox, 760), "top (front at the bottom, x 0.55 in depth)", fill=INK, font=small)
    d.rectangle([T(-W / 2, D / 2), T(W / 2, -D / 2)], outline=INK, width=3)
    d.line([T(xp, D / 2), T(xp, -D / 2)], fill=GREY, width=2)
    d.text((T(-W / 2 + 20, 0)[0], T(0, 0)[1]), "3 mm top glass", fill=GREY, font=small)
    # the card
    ox4, oy4 = 1160, 400
    L, Hg = K.GPU_L * 1000, K.GPU_H * 1000

    def G(x, y):
        return (ox4 + x * S * 2.2, oy4 - y * S * 2.2)
    d.text((ox4, 70), "the card's fan face (x 2.2)", fill=INK, font=small)
    d.rounded_rectangle([G(0, Hg), G(L, 0)], radius=K.GPU_R * 1000 * S * 2.2, outline=INK, width=3)
    for fx in K.GPU_FAN_X:
        r = K.GPU_FAN_R * 1000
        d.ellipse([G(fx * 1000 - r, Hg / 2 + r), G(fx * 1000 + r, Hg / 2 - r)], outline=INK, width=2)
        r = K.GPU_HUB_R * 1000
        d.ellipse([G(fx * 1000 - r, Hg / 2 + r), G(fx * 1000 + r, Hg / 2 - r)], outline=GREY, width=2)
    f0, f1, fd = [v * 1000 for v in K.GPU_FINGERS]
    d.rectangle([G(f0, 0), G(f1, -fd)], outline=(190, 150, 40), width=2)
    by0, by1 = [v * 1000 for v in K.BRACKET_Y]
    d.rectangle([G(-3, by1), G(0, by0)], outline=INK, width=2)
    dim_h(d, G(0, 0)[0], G(L, 0)[0], G(0, -fd)[1] + 40, f"{L:.0f} (official)", small)
    dim_v(d, G(L, 0)[0] + 30, G(0, Hg)[1], G(0, 0)[1], f"{Hg:.0f}", small)
    d.text((ox4, G(0, -fd)[1] + 80), f"height {Hg:.0f} measured (135 with the PCIe fingers), thickness {K.GPU_T * 1000:.0f} (2-slot), {K.GPU_BLADES} blades per fan",
           fill=INK, font=small)
    im.save(out)
    print("SHEET", out)


if __name__ == "__main__":
    main(os.path.join(K.FOOTAGE, "pc-blueprint.png"))
