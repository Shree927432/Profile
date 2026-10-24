"""speakers: the one-page blueprint (front, side, top, the two mounts, with dimensions) from the same
numbers the 3D build uses (blender/components/speakers.py), the per-angle compare sheets and the
photo-vs-model sheet from the data speakers_render.py wrote. Plain Python after the Blender stages:

    /opt/anaconda3/bin/python3 blender/components/speakers_blueprint.py [--quick]

Writes video-local/footage/2026-10-24-components/speakers/speakers-blueprint.png,
speakers-compare-<angle>.png and speakers-photo-vs-model.jpg.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import speakers as S  # noqa: E402  (no Blender: numbers and outline maths only)

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FOOT = os.path.join(REPO, "video-local", "footage", "2026-10-24-components", "speakers")
QUICK = "--quick" in sys.argv
INK, DIM, HID, ACC = "#1d2733", "#2f6db5", "#8a96a3", "#c2410c"
ORDER = ["front", "white-front", "side-left", "side-right", "back", "white-back", "3q-front-left", "3q-front-right",
         "3q-studio-right", "white-hero", "white-3q-right", "3q-back-left", "3q-back-right", "front-above"]
TITLES = {
    "front": "Front (ADAM spin photo, black A7V, same shape) vs our model in black",
    "white-front": "Front, white edition (ADAM press photo) vs our model",
    "side-left": "Left side (ADAM spin photo) vs our model",
    "side-right": "Right side (ADAM spin photo) vs our model",
    "back": "Back (ADAM spin photo) vs our model",
    "white-back": "Back, white edition (ADAM press photo) vs our model",
    "3q-front-left": "Three-quarter front, left side showing (ADAM spin photo) vs our model",
    "3q-front-right": "Three-quarter front, right side showing (ADAM spin photo) vs our model",
    "3q-studio-right": "Three-quarter front, studio shot (ADAM product page) vs our model",
    "white-hero": "White edition hero (white-limited-transparent.png) vs our model",
    "white-3q-right": "White edition three-quarter (ADAM press photo) vs our model",
    "3q-back-left": "Three-quarter back (ADAM spin photo) vs our model",
    "3q-back-right": "Three-quarter back, other side (ADAM spin photo) vs our model",
    "front-above": "Front from slightly above: the top and the baffle's facets (ADAM product page) vs our model",
    "top": "Top view: no official top photo exists; our model, orthographic",
}


# ---------------------------------------------------------------------------
# blueprint
# ---------------------------------------------------------------------------
def blueprint():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle

    fig = plt.figure(figsize=(26, 17), dpi=100)
    fig.patch.set_facecolor("#f6f4ee")
    fig.text(0.03, 0.965, "AI lab: studio monitors, ADAM A7V Arctic White (pair), and their two mounts",
             fontsize=26, color=INK, weight="bold")
    fig.text(0.03, 0.94, "Official 200 x 280 x 337 mm (W x D x H). Millimetres. Cabinet bottom = 0, centre line = 0. "
             "Drawn from blender/components/speakers.py. No logos or printed text on the model.", fontsize=13,
             color=INK)

    def dim_h(ax, x0, x1, y, text, col=DIM):
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=col, lw=1.1))
        ax.text((x0 + x1) / 2, y + 3, text, ha="center", va="bottom", fontsize=10.5, color=col)

    def dim_v(ax, x, y0, y1, text, col=DIM, off=-4, ha="right"):
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", color=col, lw=1.1))
        ax.text(x + off, (y0 + y1) / 2, text, ha=ha, va="center", fontsize=10.5, color=col, rotation=90)

    def poly(ax, pts, **kw):
        ax.add_patch(Polygon(pts, closed=True, fill=False, **kw))

    hw = S.W / 2
    # ---- front -------------------------------------------------------------
    ax = fig.add_axes([0.02, 0.06, 0.30, 0.84])
    ax.set_title("FRONT", loc="left", fontsize=15, color=INK, weight="bold")
    ax.add_patch(Rectangle((-hw, S.FOOT_H), S.W, S.H - S.FOOT_H, fill=False, ec=INK, lw=1.8))
    zs = S.facet_meets_side_z()
    for s in (-1, 1):
        ax.plot([s * hw, s * abs(S.FACET_B[0])], [zs, S.H], color=INK, lw=1.0)
    ax.plot([-abs(S.FACET_B[0]) - 3, abs(S.FACET_B[0]) + 3], [S.H - S.TOP_CHAMFER[0]] * 2, color=HID, lw=0.9, ls="--")
    pw, ph, pr, pp = S.TW_PLATE
    ax.add_patch(FancyBboxPatch((-pw / 2 + pr, S.TW_PLATE_Z - ph / 2 + pr), pw - 2 * pr, ph - 2 * pr,
                                boxstyle=f"round,pad={pr}", fill=False, ec=INK, lw=1.3))
    mw, mh, mn, mz = S.TW_MOUTH
    poly(ax, S.superellipse(mw, mh, mn, mz, 96), ec=INK, lw=1.0)
    rw, sh, gap, ns, pitch = S.RIBBON
    tz = S.TW_THROAT[3]
    total = ns * sh + (ns - 1) * gap
    for k in range(ns):
        zt = tz + total / 2 - k * (sh + gap)
        ax.add_patch(Rectangle((-rw / 2, zt - sh), rw, sh, fill=True, fc="#e8b33a", ec=INK, lw=0.6))
    for x, z in S.TW_SCREWS:
        ax.add_patch(Circle((x, z), 2.4, fill=False, ec=INK, lw=0.8))
    ax.add_patch(Circle(S.TW_LED, 1.0, fc="#38c060", ec="none"))
    for r, lw in ((S.WF_FLANGE_R, 1.4), (S.WF_GROOVE_R, 0.7), (S.WF_INNER_R, 0.9), (S.WF_SURR[1], 0.9),
                  (S.WF_SURR[0], 0.9), (S.WF_CAP_R, 0.9)):
        ax.add_patch(Circle((0, S.WF_Z), r, fill=False, ec=INK, lw=lw))
    for k in range(6):
        t = math.radians(60 * k)
        ax.add_patch(Circle((S.WF_SCREW_R * math.cos(t), S.WF_Z + S.WF_SCREW_R * math.sin(t)), 2.4, fill=False,
                            ec=INK, lw=0.8))
    for side in (-1, 1):
        P = S.port_outline(side, 8)
        poly(ax, P, ec=INK, lw=1.2)
        poly(ax, S.offset_poly(P, S.PORT_FLARE), ec=HID, lw=0.8, ls="--")
    dim_h(ax, -hw, hw, S.H + 14, f"{S.W:.0f} (official)")
    dim_v(ax, -hw - 18, 0, S.H, f"{S.H:.0f} (official)")
    dim_v(ax, hw + 16, 0, S.WF_Z, f"woofer centre {S.WF_Z:.1f}", off=4, ha="left")
    dim_v(ax, hw + 34, 0, tz, f"ribbon centre {tz:.1f}", off=4, ha="left")
    dim_h(ax, -S.WF_FLANGE_R, S.WF_FLANGE_R, S.WF_Z - S.WF_FLANGE_R - 8, f"basket ring {2 * S.WF_FLANGE_R:.0f}")
    dim_h(ax, -pw / 2, pw / 2, S.TW_PLATE_Z + ph / 2 + 4, f"{pw:.0f} x {ph:.1f}")
    ax.text(-hw + 4, zs + 6, f"facet meets the side at {zs:.0f}", fontsize=9.5, color=ACC)
    ax.text(-38, 4, "ports: round inner end, 6.5 mm lip", fontsize=9.5, color=HID)
    ax.set_xlim(-hw - 40, hw + 60)
    ax.set_ylim(-14, S.H + 30)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- side (left) ---------------------------------------------------------
    ax = fig.add_axes([0.33, 0.40, 0.36, 0.50])
    ax.set_title("SIDE (front to the left)", loc="left", fontsize=15, color=INK, weight="bold")
    y0, y1 = S.FRONT_Y, S.BACK_Y
    ch, cd = S.TOP_CHAMFER
    side = [(y0, S.FOOT_H), (y0, S.H - ch), (y0 + cd, S.H), (y1, S.H), (y1, S.FOOT_H)]
    poly(ax, side, ec=INK, lw=1.8)
    ax.plot([y0 + S.SEAM_BACK] * 2, [S.FOOT_H, S.H], color=HID, lw=0.9)
    ax.plot([y0, y0 + S.FACET_DEPTH], [zs, S.H], color=INK, lw=1.0)
    ax.add_patch(Rectangle((y0 - 2.4, S.WF_Z - S.WF_FLANGE_R), 2.4, 2 * S.WF_FLANGE_R, fill=True, fc="#333", ec=INK))
    ax.add_patch(Rectangle((y0 - pp, S.TW_PLATE_Z - ph / 2), pp, ph, fill=True, fc="#333", ec=INK))
    ax.add_patch(Rectangle((y1, S.PLATE[3] - S.PLATE[1] / 2), S.PLATE[4], S.PLATE[1], fill=True, fc="#333", ec=INK))
    for y, _ in ((-S.FOOT_AT[0][1], 0), (S.FOOT_AT[0][1], 0)):
        yc = (y0 + y1) / 2 + y
        ax.add_patch(Rectangle((yc - S.FOOT_R, 0), 2 * S.FOOT_R, S.FOOT_H, fc="#555", ec="none"))
    dim_h(ax, y0 - 2.4, y1, S.H + 14, f"{S.D:.0f} (official, ring face to back)")
    dim_h(ax, y0, y0 + S.SEAM_BACK, -14, f"seam {S.SEAM_BACK:.0f}")
    dim_v(ax, y1 + 30, 0, S.H, f"{S.H:.0f}", off=4, ha="left")
    ax.text(y0 + 4, S.H - 30, f"top chamfer {ch:.0f} x {cd:.0f}\nfacet {S.FACET_DEPTH:.0f} back at the top corner",
            fontsize=9.5, color=ACC)
    ax.set_xlim(y0 - 30, y1 + 70)
    ax.set_ylim(-30, S.H + 30)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- top with the two mount footprints ----------------------------------
    ax = fig.add_axes([0.70, 0.40, 0.28, 0.50])
    ax.set_title("TOP (front at the top) + mount footprints", loc="left", fontsize=15, color=INK, weight="bold")
    top = [(-hw, -y1), (hw, -y1), (hw, -(y0 + S.FACET_DEPTH)), (abs(S.FACET_B[0]), -(y0 + cd)),
           (-abs(S.FACET_B[0]), -(y0 + cd)), (-hw, -(y0 + S.FACET_DEPTH))]
    poly(ax, top, ec=INK, lw=1.8)
    ax.add_patch(Rectangle((-hw, -y1), S.W, y1 - y0, fill=False, ec=HID, lw=0.8, ls="--"))
    yc = -(y0 + y1) / 2
    pw_, pd_, pr_ = S.POLE_PLATE
    ax.add_patch(FancyBboxPatch((-pw_ / 2 + pr_, yc - pd_ / 2 + pr_), pw_ - 2 * pr_, pd_ - 2 * pr_,
                                boxstyle=f"round,pad={pr_}", fill=False, ec=ACC, lw=1.2))
    ax.add_patch(Rectangle((-S.ISO_W / 2, yc - S.ISO_D / 2), S.ISO_W, S.ISO_D, fill=False, ec=DIM, lw=1.2, ls=":"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            ax.add_patch(Circle((sx * S.ISO_POST[0], yc + sy * S.ISO_POST[1]), S.ISO_CUP_R, fill=False, ec=DIM, lw=0.9))
    ax.add_patch(Circle((0, yc), S.POLE_R, fill=False, ec=ACC, lw=1.0))
    ax.text(-hw, -y1 - 18, f"pole platform {pw_:.0f} x {pd_:.0f} (orange)   ISO-155 {S.ISO_W:.0f} x {S.ISO_D:.0f} "
            f"(blue, official)", fontsize=10, color=INK)
    ax.set_xlim(-hw - 20, hw + 20)
    ax.set_ylim(-y1 - 30, -y0 + 20)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- the mounts in elevation ---------------------------------------------
    ax = fig.add_axes([0.33, 0.04, 0.65, 0.33])
    ax.set_title("MOUNTS (front view, desk top = 0)", loc="left", fontsize=15, color=INK, weight="bold")
    ax.axhline(0, color=INK, lw=1.2)
    ax.add_patch(Rectangle((-420, -S.DESK_T), 840, S.DESK_T, fc="#e6e4de", ec=INK, lw=0.8))
    # pole
    cx = -200
    top_ = S.POLE_CAB_Z - S.POLE_HEAD
    ax.add_patch(Rectangle((cx - S.POLE_R, 7.5), 2 * S.POLE_R, top_ - 7.5, fc="#f2f2f0", ec=INK))
    ax.add_patch(Rectangle((cx - 32, 0), 64, 7.5, fc="#f2f2f0", ec=INK))
    ax.add_patch(Rectangle((cx - 25, top_ - 46), 50, 46, fc="#f2f2f0", ec=INK))
    ax.add_patch(Rectangle((cx - pw_ / 2, top_ + 12), pw_, 8, fc="#f2f2f0", ec=INK))
    ax.add_patch(Rectangle((cx - S.W / 2, S.POLE_CAB_Z), S.W, 120, fc="none", ec=HID, ls="--"))
    dim_v(ax, cx - 110, 0, S.POLE_CAB_Z, f"cabinet base {S.POLE_CAB_Z:.1f} (plan v3)")
    ax.text(cx + 30, top_ / 2, f"35 mm pole, {top_:.1f} tall\nthrough-desk fixing\nplatform {pw_:.0f} x {pd_:.0f}, "
            f"{S.POLE_HEAD:.0f} with pad", fontsize=10, color=INK, va="center")
    # ISO
    cx = 200
    hh = S.ISO_H_SHORT
    for sx in (-1, 1):
        x = cx + sx * S.ISO_POST[0]
        ax.add_patch(Rectangle((x - S.ISO_FOOT_R, 0), 2 * S.ISO_FOOT_R, 24, fc="#333", ec=INK))
        ax.add_patch(Rectangle((x - 7, 24), 14, hh - 26 - 24, fc="#555", ec=INK))
        ax.add_patch(Rectangle((x - S.ISO_CUP_R, hh - 26), 2 * S.ISO_CUP_R, 26, fc="#333", ec=INK))
    ax.add_patch(Rectangle((cx - S.W / 2, hh), S.W, 120, fc="none", ec=HID, ls="--"))
    dim_v(ax, cx + 120, 0, hh, f"{hh:.0f} short (official); tall {S.ISO_H_TALL:.0f}", off=4, ha="left")
    dim_h(ax, cx - S.ISO_W / 2, cx + S.ISO_W / 2, -S.DESK_T - 22, f"{S.ISO_W:.0f} (official)")
    ax.set_xlim(-430, 430)
    ax.set_ylim(-80, S.POLE_CAB_Z + 140)
    ax.set_aspect("equal")
    ax.axis("off")
    out = os.path.join(FOOT, f"speakers-blueprint{'-quick' if QUICK else ''}.png")
    fig.savefig(out, facecolor=fig.get_facecolor())
    print("blueprint", out)


# ---------------------------------------------------------------------------
# compare sheets
# ---------------------------------------------------------------------------
def _fonts():
    from PIL import ImageFont
    try:
        return (ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26),
                ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20))
    except OSError:
        f = ImageFont.load_default()
        return f, f


def _pair(c):
    """(photo on its background, our render placed at the same scale and position, photo mask, render mask)."""
    from PIL import Image
    src = Image.open(c["photo"]).convert("RGBA")
    W, H = src.size
    alpha_photo = c["photo"].endswith(".png") and np.array(src)[..., 3].min() < 250
    bgc = (236, 237, 240, 255) if alpha_photo else tuple(int(v) for v in np.array(src)[4, 4][:3]) + (255,)
    ph = Image.new("RGBA", (W, H), bgc)
    ph.alpha_composite(src)
    rd = Image.open(c["render"]).convert("RGBA")
    tf = c["transform"]
    s = tf["scale"] * W / rd.size[0]      # the render may be at 2x the photo's size (close-up compares)
    rw = rd.resize((max(1, int(round(rd.size[0] * s))), max(1, int(round(rd.size[1] * s)))), Image.LANCZOS)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(rw, (int(round(tf["tx"])), int(round(tf["ty"]))), rw)
    rend = Image.new("RGBA", (W, H), bgc)
    rend.alpha_composite(layer)
    pm = np.array(Image.open(c["photo_mask"]).convert("L")) > 128
    rm = np.array(layer)[..., 3] > 128
    return ph, rend, pm, rm


def _box(pm, rm, W, H, pad=0.05):
    ys, xs = np.nonzero(pm | rm)
    p = int(pad * max(xs.max() - xs.min(), ys.max() - ys.min()))
    return (max(0, xs.min() - p), max(0, ys.min() - p), min(W, xs.max() + p), min(H, ys.max() + p))


def compare_sheets():
    from PIL import Image, ImageDraw, ImageFilter
    rp = os.path.join(FOOT, "speakers-quick-report.json" if QUICK else "speakers-report.json")
    rep = json.load(open(rp))
    font, small = _fonts()
    for name, c in rep.get("compare", {}).items():
        ph, rend, pm, rm = _pair(c)
        W, H = ph.size
        over = Image.blend(ph, rend, 0.5)
        ea = np.array(ph.convert("L").convert("RGB")).astype(float) * 0.35 + 165
        for m, col in ((pm, (220, 40, 40)), (rm, (40, 90, 230))):
            mi = Image.fromarray((m * 255).astype(np.uint8))
            e = np.array(mi.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))) > 0
            ea[e] = col
        edge = Image.fromarray(ea.astype(np.uint8))
        box = _box(pm, rm, W, H)
        sheet = Image.new("RGB", (1920, 1080), (246, 244, 238))
        d = ImageDraw.Draw(sheet)
        d.text((24, 14), f"speakers: photo compare  {name}   silhouette IoU {c['iou']:.3f}", fill=(29, 39, 51), font=font)
        d.text((24, 50), TITLES.get(name, "") + f"   (fitted: turn {c['yaw_deg']:.1f} deg, camera {c['distance_m']:.2f} m, "
               f"{c['height_offset_m'] * 1000:.0f} mm above the centre; our model in the photo's finish: {c['finish']})",
               fill=(29, 39, 51), font=small)
        tiles = [("official photo", ph), ("our render, same camera and scale", rend), ("50 / 50", over),
                 ("outlines: photo red, render blue", edge)]
        tw, th = 940, 488
        for i, (lab, im) in enumerate(tiles):
            crop = im.convert("RGB").crop(box)
            crop.thumbnail((tw, th - 30), Image.LANCZOS)
            x = 13 + (i % 2) * (tw + 14)
            y = 84 + (i // 2) * (th + 6)
            sheet.paste(crop, (x + (tw - crop.size[0]) // 2, y + 30))
            d.text((x, y + 2), lab, fill=(47, 109, 181), font=small)
        out = os.path.join(FOOT, f"speakers-compare-{name}{'-quick' if QUICK else ''}.png")
        sheet.save(out)
        print("compare", name, c["iou"], out)
    photo_vs_model(rep)
    closeup_sheet(rep)


def photo_vs_model(rep):
    """Every compare pair stacked: official photo left, our render right, same camera and scale; the
    top view last (no photo exists)."""
    from PIL import Image, ImageDraw
    font, small = _fonts()
    rows = []
    for name in ORDER:
        c = rep.get("compare", {}).get(name)
        if not c:
            continue
        ph, rend, pm, rm = _pair(c)
        box = _box(pm, rm, *ph.size)
        rows.append((name, c, ph.convert("RGB").crop(box), rend.convert("RGB").crop(box)))
    top = os.path.join(FOOT, f"speakers-top-single{'-quick' if QUICK else ''}.png")
    if not os.path.exists(top):
        top = os.path.join(FOOT, f"speakers-top{'-quick' if QUICK else ''}.png")
    colw, rowh, head = 940, 560, 76
    Wd = 2 * colw + 40
    Ht = len(rows) * (rowh + head) + (rowh + head if os.path.exists(top) else 0) + 20
    sheet = Image.new("RGB", (Wd, Ht), (246, 244, 238))
    d = ImageDraw.Draw(sheet)
    y = 10
    for name, c, a, b in rows:
        d.text((14, y), TITLES.get(name, name) + f"   (silhouette IoU {c['iou']:.3f})", fill=(29, 39, 51), font=font)
        d.text((14, y + 40), "official photo", fill=(47, 109, 181), font=small)
        d.text((colw + 34, y + 40), "our render, same camera and scale", fill=(47, 109, 181), font=small)
        for k, im in enumerate((a, b)):
            im = im.copy()
            im.thumbnail((colw, rowh), Image.LANCZOS)
            sheet.paste(im, (14 + k * (colw + 20) + (colw - im.size[0]) // 2, y + head))
        y += rowh + head
    if os.path.exists(top):
        d.text((14, y), TITLES["top"], fill=(29, 39, 51), font=font)
        d.text((14, y + 40), "no official top photo (the nearest is 'front from slightly above', above)",
               fill=(47, 109, 181), font=small)
        d.text((colw + 34, y + 40), "our model, orthographic, from above", fill=(47, 109, 181), font=small)
        im = Image.open(top).convert("RGB")
        a = np.array(im).astype(int)
        diff = np.abs(a - a[5, 5]).sum(-1) > 12
        ys, xs = np.nonzero(diff)
        if len(xs):
            p = 30
            im = im.crop((max(0, xs.min() - p), max(0, ys.min() - p), min(im.size[0], xs.max() + p),
                          min(im.size[1], ys.max() + p)))
        im.thumbnail((colw, rowh), Image.LANCZOS)
        sheet.paste(im, (14 + colw + 20 + (colw - im.size[0]) // 2, y + head))
    out = os.path.join(FOOT, f"speakers-photo-vs-model{'-quick' if QUICK else ''}.jpg")
    sheet.save(out, quality=90)
    print("photo-vs-model", out, sheet.size)


def closeup_sheet(rep):
    """Detail, not outline: the tweeter plate, the woofer and the ports, photo crop beside the render crop
    at the same camera and scale, from the white front press photo and the 1600 px black front."""
    from PIL import Image, ImageDraw
    font, small = _fonts()
    boxes = {"white-front": [("Waveguide plate and ribbon", (420, 110, 665, 380)), ("Woofer", (285, 350, 800, 870)),
                             ("Bass-reflex ports", (300, 800, 790, 960))],
             "front-above": [("Waveguide plate and ribbon", (615, 170, 985, 545)), ("Woofer", (430, 530, 1170, 1270)),
                             ("Bass-reflex ports", (455, 1180, 1145, 1440))]}
    rows = []
    for name, items in boxes.items():
        c = rep.get("compare", {}).get(name)
        if not c:
            continue
        ph, rend, _, _ = _pair(c)
        for title, box in items:
            rows.append((f"{title}: {TITLES[name].split(' vs ')[0]}", ph.convert("RGB").crop(box),
                         rend.convert("RGB").crop(box)))
    colw, head = 940, 70
    hs = []
    for _, a, _ in rows:
        hs.append(int(min(colw / a.size[0], 640 / a.size[1]) * a.size[1]))
    sheet = Image.new("RGB", (2 * colw + 40, sum(h + head for h in hs) + 20), (246, 244, 238))
    d = ImageDraw.Draw(sheet)
    y = 10
    for (title, a, b), h in zip(rows, hs):
        d.text((14, y), title, fill=(29, 39, 51), font=font)
        d.text((14, y + 38), "official photo", fill=(47, 109, 181), font=small)
        d.text((colw + 34, y + 38), "our render, same camera and scale (black finish for the black photo)",
               fill=(47, 109, 181), font=small)
        sc = h / a.size[1]
        for k, im in enumerate((a, b)):
            im = im.resize((int(im.size[0] * sc), h), Image.LANCZOS)
            sheet.paste(im, (14 + k * (colw + 20) + (colw - im.size[0]) // 2, y + head))
        y += h + head
    out = os.path.join(FOOT, f"speakers-closeups{'-quick' if QUICK else ''}.jpg")
    sheet.save(out, quality=92)
    print("closeups", out, sheet.size)


if __name__ == "__main__":
    if "--sheets" not in sys.argv:
        blueprint()
    compare_sheets()
