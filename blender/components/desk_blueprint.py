"""desk: the one-page blueprint (front, side and top of the ALEX unit; the L plan from plan v3) drawn from
the same constants as the model, and the close-up pair sheet composer. Plain Python (Pillow):

    /opt/anaconda3/bin/python3 blender/components/desk_blueprint.py
    /opt/anaconda3/bin/python3 blender/components/desk_blueprint.py closeups <closeups.json>
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
import desk as D  # noqa: E402

INK = (29, 39, 51)
BLUE = (47, 109, 181)
GREY = (150, 155, 160)
LED = (70, 160, 230)
BG = (246, 244, 238)


def fonts():
    try:
        f = "/System/Library/Fonts/Helvetica.ttc"
        return ImageFont.truetype(f, 30), ImageFont.truetype(f, 19), ImageFont.truetype(f, 15)
    except OSError:
        d = ImageFont.load_default()
        return d, d, d


def dim(d, p0, p1, text, off, font, horizontal=True):
    """A dimension line offset `off` px from the edge p0-p1, with ticks and the text."""
    (x0, y0), (x1, y1) = p0, p1
    if horizontal:
        y = y0 + off
        d.line([(x0, y0), (x0, y)], fill=GREY)
        d.line([(x1, y1), (x1, y)], fill=GREY)
        d.line([(x0, y), (x1, y)], fill=BLUE, width=1)
        for x in (x0, x1):
            d.line([(x - 4, y + 4), (x + 4, y - 4)], fill=BLUE, width=2)
        w = d.textlength(text, font=font)
        d.text(((x0 + x1) / 2 - w / 2, y + (4 if off > 0 else -22)), text, fill=BLUE, font=font)
    else:
        x = x0 + off
        d.line([(x0, y0), (x, y0)], fill=GREY)
        d.line([(x1, y1), (x, y1)], fill=GREY)
        d.line([(x, y0), (x, y1)], fill=BLUE, width=1)
        for y in (y0, y1):
            d.line([(x - 4, y + 4), (x + 4, y - 4)], fill=BLUE, width=2)
        w = d.textlength(text, font=font)
        d.text((x + (6 if off > 0 else -w - 6), (y0 + y1) / 2 - 9), text, fill=BLUE, font=font)


def blueprint(out):
    big, mid, small = fonts()
    W, H = 1920, 1080
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((24, 14), "desk: IKEA ALEX drawer unit and the LAGKAPTEN L top (plan v3), drawn from desk.py", fill=INK, font=big)
    d.text((24, 52), "mm. OFFICIAL 360 x 580 x 700; fronts, gaps and the cut-out MEASURED on IKEA's photo (rectified) "
           "and IKEA's 3D file; feet EST.", fill=INK, font=small)
    k = 0.62                                  # px per mm for the unit views
    # ---- front
    ox, oy = 90, 150 + D.AH * k               # floor line, left edge of the unit
    def P(x, z):
        return (ox + (x + D.AW / 2) * k, oy - z * k)
    d.text((ox, 74), "ALEX front", fill=BLUE, font=mid)
    d.rectangle([P(-D.AW / 2, D.AH), P(D.AW / 2, D.FOOT_H)], outline=INK, width=2)
    d.line([P(-D.AW / 2, D.OPEN_Z1), P(D.AW / 2, D.OPEN_Z1)], fill=INK)
    d.line([P(-D.AW / 2, D.OPEN_Z0), P(D.AW / 2, D.OPEN_Z0)], fill=INK)
    for sx in (-1, 1):
        d.line([P(sx * (D.AW / 2 - D.PANEL_T), D.OPEN_Z0), P(sx * (D.AW / 2 - D.PANEL_T), D.OPEN_Z1)], fill=INK)
        x = sx * (D.AW / 2 - D.FOOT_IN[0])
        d.rectangle([P(x - D.FOOT_D / 2, D.FOOT_H), P(x + D.FOOT_D / 2, 0)], fill=INK)
    for z0, h in zip(D.front_z(), D.FRONT_H):
        pts = [P(x, z0 + z) for x, z in D.front_outline(h)]
        d.polygon(pts, outline=INK, fill=(255, 255, 255))
    z0, h = D.front_z()[0], D.FRONT_H[0]
    dim(d, P(-D.AW / 2, D.AH), P(D.AW / 2, D.AH), "360", -18, small)
    dim(d, P(-D.AW / 2, 0), P(-D.AW / 2, D.AH), "700", -40, small, horizontal=False)
    dim(d, P(D.AW / 2, D.front_z()[1]), P(D.AW / 2, D.front_z()[1] + D.FRONT_H[1]), f"{D.FRONT_SMALL:.1f}", 14, small,
        horizontal=False)
    dim(d, P(D.AW / 2, D.front_z()[4]), P(D.AW / 2, D.front_z()[4] + D.FRONT_H[4]), f"{D.FRONT_LARGE:.1f}", 14, small,
        horizontal=False)
    dim(d, P(D.AW / 2, 0), P(D.AW / 2, D.FOOT_H + D.BOT_PANEL_T), "28", 60, small, horizontal=False)
    d.text((ox, oy + 30), f"gaps {D.GAP:.2f}, fronts {D.FRONT_W:.1f} wide, 17 thick; plinth: bottom panel 16 on feet 12",
           fill=INK, font=small)
    # the cut-out, 3x
    cx, cy, kk = ox + 30, oy + 110, 2.0
    d.text((cx, cy - 50), "finger-pull cut-out, 2:1 (MEASURED: flat 23.2 deep for +-30, cosine to +-92)",
           fill=BLUE, font=small)
    prof = [(cx + (x + 100) * kk, cy + dd * kk) for x, dd in D.cut_profile(24)]
    d.line([(cx, cy), prof[0]], fill=INK, width=2)
    d.line(prof, fill=INK, width=2)
    d.line([prof[-1], (cx + 200 * kk, cy)], fill=INK, width=2)
    dim(d, (cx + 8 * kk, cy), (cx + 192 * kk, cy), "184", -14, small)
    dim(d, (cx + 200 * kk, cy), (cx + 200 * kk, cy + D.CUT_DEPTH * kk), "23.2", 10, small, horizontal=False)
    # ---- side
    sx0 = ox + D.AW * k + 110
    def S(y, z):
        return (sx0 + (y + D.AD / 2) * k, oy - z * k)
    d.text((sx0, 74), "ALEX side (front at left)", fill=BLUE, font=mid)
    d.rectangle([S(-D.AD / 2, D.AH), S(D.AD / 2, D.FOOT_H)], outline=INK, width=2)
    d.line([S(-D.AD / 2, D.OPEN_Z1), S(D.AD / 2, D.OPEN_Z1)], fill=GREY)
    d.line([S(-D.AD / 2, D.OPEN_Z0), S(D.AD / 2, D.OPEN_Z0)], fill=GREY)
    for fy in (-1, 1):
        y = fy * (D.AD / 2 - D.FOOT_IN[1])
        d.rectangle([S(y - D.FOOT_D / 2, D.FOOT_H), S(y + D.FOOT_D / 2, 0)], fill=INK)
    dim(d, S(-D.AD / 2, D.AH), S(D.AD / 2, D.AH), "580", -18, small)
    d.line([S(D.AD / 2 - D.BACK_T, D.OPEN_Z0), S(D.AD / 2 - D.BACK_T, D.OPEN_Z1)], fill=GREY)
    d.text((sx0 + 190, oy + 30), "finished back 16, inset; top 15, sides 15", fill=INK, font=small)
    # ---- top of the unit
    tx0 = sx0 + D.AD * k + 90
    d.text((tx0, 74), "ALEX top", fill=BLUE, font=mid)
    d.rectangle([(tx0, 170), (tx0 + D.AW * k, 170 + D.AD * k)], outline=INK, width=2)
    d.line([(tx0, 170 + D.AD * k - 2), (tx0 + D.AW * k, 170 + D.AD * k - 2)], fill=INK, width=3)
    d.text((tx0, 170 + D.AD * k + 8), "front", fill=INK, font=small)
    # ---- the L plan (plan v3), x right, y up, wall corner top-left
    kp = 0.30
    px0, py0 = 1250, 190
    def L(x, y):
        return (px0 + x * 1000 * kp, py0 - y * 1000 * kp)
    d.text((px0 - 60, 74), "L top, plan v3 (from above; left wall at left, back wall at top)", fill=BLUE, font=mid)
    lo = D.l_outline()
    d.polygon([L(x, y) for x, y in lo], outline=INK, fill=(255, 255, 255))
    d.line([L(0, 0.02), L(D.RET_REACH + 0.05, 0.02)], fill=GREY, width=3)
    d.line([L(-0.02, 0), L(-0.02, -D.MAIN_LEN - 0.05)], fill=GREY, width=3)
    for i, (x, y, yaw) in enumerate(D.DRAWERS_AT):
        w, dd = (D.AD, D.AW) if yaw == 90 else (D.AW, D.AD)
        d.rectangle([L(x - w / 2000, y + dd / 2000), L(x + w / 2000, y - dd / 2000)], outline=GREY, width=2)
        d.text(L(x - 0.05, y + 0.03), f"0{i + 1}", fill=GREY, font=small)
        fx, fy = (x + w / 2000, y) if yaw == 90 else (x, y - dd / 2000)
        d.ellipse([L(fx, fy)[0] - 4, L(fx, fy)[1] - 4, L(fx, fy)[0] + 4, L(fx, fy)[1] + 4], fill=GREY)
    for (x0, y0), (x1, y1) in D.led_segments():
        d.line([L(x0, y0), L(x1, y1)], fill=LED, width=4)
    dim(d, L(0, -D.MAIN_LEN), L(D.MAIN_D, -D.MAIN_LEN), "800", 22, small)
    dim(d, L(0, 0), L(D.RET_REACH, 0), f"{D.RET_REACH * 1000:.0f}", -30, small)
    dim(d, L(0, 0), L(0, -D.MAIN_LEN), f"{D.MAIN_LEN * 1000:.0f}", -46, small, horizontal=False)
    dim(d, L(D.RET_REACH, 0), L(D.RET_REACH, -D.RET_D), "600", 14, small, horizontal=False)
    d.text(L(0.05, -D.MAIN_LEN - 0.25), f"top {D.TOP_T:.0f} thick at {D.TOP_Z * 1000:.0f}; corners R{D.TOP_CORNER_R:.0f}, "
           f"inner corner R{D.TOP_INNER_R:.0f}; edge R{D.TOP_EDGE_R:.0f}", fill=INK, font=small)
    d.text(L(0.05, -D.MAIN_LEN - 0.33), f"LED (blue) {D.LED_IN * 100:.0f} cm in, in the knee spaces; units grey, "
           "dot = front", fill=INK, font=small)
    # the top's edge section, 4:1
    ex, ey, ke = 1500, 860, 4.0
    d.text((ex - 40, ey - 60), "top edge, 4:1", fill=BLUE, font=small)
    r = D.TOP_EDGE_R
    pts = [(ex + 60 * ke, ey)]
    for i in range(7):
        a = math.pi / 2 * i / 6
        pts.append((ex + (r - r * math.sin(a)) * ke, ey + (r - r * math.cos(a)) * ke))
    for i in range(7):
        a = math.pi / 2 * i / 6
        pts.append((ex + (r - r * math.cos(a)) * ke, ey + (D.TOP_T - r + r * math.sin(a)) * ke))
    pts.append((ex + 60 * ke, ey + D.TOP_T * ke))
    d.line(pts, fill=INK, width=2)
    dim(d, (ex + 60 * ke, ey), (ex + 60 * ke, ey + D.TOP_T * ke), f"{D.TOP_T:.0f}", 12, small, horizontal=False)
    im.save(out)
    return out


def closeups(spec_path):
    sp = json.load(open(spec_path))
    big, mid, small = fonts()
    rows = []
    for st in sp["sets"]:
        photo = Image.open(st["photo"]).convert("RGB")
        W, H = photo.size
        tf = st["transform"]
        s = tf["scale"] / st["render_scale"]
        rd = Image.open(st["render"]).convert("RGBA")
        rw = rd.resize((max(1, int(round(rd.size[0] * s))), max(1, int(round(rd.size[1] * s)))), Image.LANCZOS)
        layer = Image.new("RGBA", (W, H), (255, 255, 255, 255))
        layer.alpha_composite(rw, (int(round(tf["tx"])), int(round(tf["ty"]))))
        rend = layer.convert("RGB")
        for name, title, _view, box in st["crops"]:
            a, b = photo.crop(box), rend.crop(box)
            k = min(900 / a.size[0], 420 / a.size[1])
            sz = (int(a.size[0] * k), int(a.size[1] * k))
            rows.append((title, st["left"], a.resize(sz, Image.LANCZOS), "our render, same camera and scale",
                         b.resize(sz, Image.LANCZOS)))
    for extra in sp.get("extra", []):
        a = Image.open(extra["photo"]).convert("RGB").crop(extra["box"])
        b = Image.open(extra["render"]).convert("RGB")
        if extra.get("rbox"):
            b = b.crop(extra["rbox"])
        k = min(900 / a.size[0], 420 / a.size[1])
        a = a.resize((int(a.size[0] * k), int(a.size[1] * k)), Image.LANCZOS)
        k2 = min(900 / b.size[0], 420 / b.size[1])
        b = b.resize((int(b.size[0] * k2), int(b.size[1] * k2)), Image.LANCZOS)
        rows.append((extra["title"], extra["left"], a, extra["right"], b))
    Ht = 20 + sum(70 + max(r[2].size[1], r[4].size[1]) + 20 for r in rows)
    sheet = Image.new("RGB", (1920, Ht), BG)
    d = ImageDraw.Draw(sheet)
    y = 14
    for title, la, a, lb, b in rows:
        d.text((14, y), title, fill=INK, font=big)
        d.text((14, y + 40), la, fill=BLUE, font=mid)
        d.text((974, y + 40), lb, fill=BLUE, font=mid)
        y += 70
        sheet.paste(a, (14 + (930 - a.size[0]) // 2, y))
        sheet.paste(b, (974 + (930 - b.size[0]) // 2, y))
        y += max(a.size[1], b.size[1]) + 20
    sheet.save(sp["out"], quality=90)
    print("SHEET", sp["out"])
    return sp["out"]


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "closeups":
        closeups(sys.argv[2])
    else:
        print("SHEET", blueprint(os.path.join(D.FOOTAGE, "desk-blueprint.png")))
