"""screens: the one-page blueprint (front, side, top, with dimensions) from the same numbers the
3D build uses (blender/components/screens.py), and the photo-compare sheets from the data
screens_render.py wrote. Run with plain Python after the Blender stages:

    /opt/anaconda3/bin/python3 blender/components/screens_blueprint.py [--quick]

Writes video-local/footage/2026-10-24-components/screens/screens-blueprint.png and
screens-compare-<name>.png.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screens as S  # noqa: E402  (no Blender: numbers and profile maths only)

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FOOT = os.path.join(REPO, "video-local", "footage", "2026-10-24-components", "screens", "round2")
QUICK = "--quick" in sys.argv
MM = 1000.0
INK, DIM, HID, ACC = "#1d2733", "#2f6db5", "#8a96a3", "#c2410c"


# ---------------------------------------------------------------------------
# blueprint
# ---------------------------------------------------------------------------
def blueprint():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyBboxPatch, Polygon

    fig = plt.figure(figsize=(26, 17), dpi=100)
    fig.patch.set_facecolor("#f6f4ee")
    fig.text(0.03, 0.965, "AI lab: the two stacked screens on one pole", fontsize=26, color=INK, weight="bold")
    fig.text(0.03, 0.94, "Samsung Odyssey OLED G8 G85SD 34\" 1800R (bottom, VESA 100)  +  Apple Studio Display 27\" "
             "VESA version (top, posts)  +  white desk-clamp pole, two VESA arms  +  BenQ ScreenBar Halo 2.  "
             "Millimetres. Desk top = 0. Drawn from blender/components/screens.py.", fontsize=13, color=INK)
    zsd = S.sd_z0() * MM
    g8z = S.G8_Z0 * MM

    def dim_h(ax, x0, x1, y, text, off=0, col=DIM):
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=col, lw=1.1))
        ax.text((x0 + x1) / 2, y + off, text, ha="center", va="bottom", fontsize=10.5, color=col)

    def dim_v(ax, x, y0, y1, text, off=0, col=DIM, ha="right"):
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", color=col, lw=1.1))
        ax.text(x + off, (y0 + y1) / 2, text, ha=ha, va="center", fontsize=10.5, color=col, rotation=90)

    def rrect(ax, x, y, w, h, r, **kw):
        ax.add_patch(FancyBboxPatch((x + r, y + r), w - 2 * r, h - 2 * r, boxstyle=f"round,pad={r}", **kw))

    # ---- front -------------------------------------------------------------
    ax = fig.add_axes([0.03, 0.08, 0.45, 0.83])
    ax.set_title("FRONT", loc="left", fontsize=15, color=INK, weight="bold")
    W, H = S.G8_W * MM, S.G8_H * MM
    ax.add_patch(Polygon([(-W / 2, g8z), (W / 2, g8z), (W / 2, g8z + H), (-W / 2, g8z + H)], fill=False, ec=INK, lw=1.8))
    aw = 2 * S.G8_R * math.sin(S.G8_ACT_W / 2 / S.G8_R) * MM
    ax.add_patch(Polygon([(-aw / 2, g8z + S.G8_ACT_Z0 * MM), (aw / 2, g8z + S.G8_ACT_Z0 * MM),
                          (aw / 2, g8z + (S.G8_ACT_Z0 + S.G8_ACT_H) * MM), (-aw / 2, g8z + (S.G8_ACT_Z0 + S.G8_ACT_H) * MM)],
                         fill=True, fc="#dfe6f1", ec=INK, lw=0.8))
    ax.add_patch(Circle((0, g8z + S.G8_HUB_ZC * MM), S.G8_HUB_R * MM, fill=False, ec=HID, ls="--", lw=1))
    rrect(ax, -S.SD_W * MM / 2, zsd, S.SD_W * MM, S.SD_H * MM, S.SD_CORNER * MM, fill=False, ec=INK, lw=1.8)
    ax.add_patch(Polygon([(-S.SD_ACT_W * MM / 2, zsd + (S.SD_H - S.SD_ACT_H) * MM / 2),
                          (S.SD_ACT_W * MM / 2, zsd + (S.SD_H - S.SD_ACT_H) * MM / 2),
                          (S.SD_ACT_W * MM / 2, zsd + (S.SD_H + S.SD_ACT_H) * MM / 2),
                          (-S.SD_ACT_W * MM / 2, zsd + (S.SD_H + S.SD_ACT_H) * MM / 2)], fill=True, fc="#eef1f6",
                         ec=INK, lw=0.8))
    pw, ph = S.POSTS_W * MM, S.POSTS_H * MM
    ax.add_patch(Polygon([(-pw / 2, zsd + (S.SD_H * MM - ph) / 2), (pw / 2, zsd + (S.SD_H * MM - ph) / 2),
                          (pw / 2, zsd + (S.SD_H * MM + ph) / 2), (-pw / 2, zsd + (S.SD_H * MM + ph) / 2)],
                         fill=True, fc="#cfdcf0", ec=DIM, lw=1.2, ls="--"))
    ax.text(0, zsd + S.SD_H * MM / 2, "monitor_screen\nposts canvas 16:10\n538 x 336", ha="center", va="center",
            fontsize=12, color=DIM)
    ax.text(0, g8z + (S.G8_ACT_Z0 + S.G8_ACT_H / 2) * MM, "rig_screen  21:9  797 x 333.4 on the arc",
            ha="center", va="center", fontsize=12, color=DIM)
    ax.add_patch(Circle((0, zsd + S.SD_CAM_Z * MM), 2.5, color=INK))
    # pole (behind), clamp, bar
    ax.add_patch(Polygon([(-S.POLE_R * MM, 0), (S.POLE_R * MM, 0), (S.POLE_R * MM, S.POLE_H * MM),
                          (-S.POLE_R * MM, S.POLE_H * MM)], fill=False, ec=HID, ls="--", lw=1))
    ax.add_patch(Polygon([(-45, 0), (45, 0), (45, 10), (-45, 10)], fill=False, ec=INK, lw=1))
    bz = zsd + S.SD_H * MM
    ax.add_patch(Polygon([(-250, bz + 12.9), (250, bz + 12.9), (250, bz + 33.3), (-250, bz + 33.3)], fill=True,
                         fc="#3a3d42", ec=INK, lw=1))
    ax.plot([-700, 700], [0, 0], color=INK, lw=2)
    ax.plot([-700, 700], [-S.DESK_T * MM, -S.DESK_T * MM], color=INK, lw=1)
    ax.text(-690, -22, "desk top 0 (30 mm top)", fontsize=10, color=INK)
    dim_h(ax, -W / 2, W / 2, g8z - 45, "813.6 (official, chord)")
    dim_v(ax, -W / 2 - 25, g8z, g8z + H, "363.5", off=-6)
    dim_h(ax, -S.SD_W * MM / 2, S.SD_W * MM / 2, zsd + S.SD_H * MM + 60, "623 (official)", off=2)
    dim_v(ax, S.SD_W * MM / 2 + 30, zsd, zsd + S.SD_H * MM, "362", off=8, ha="left")
    dim_h(ax, -250, 250, bz + 75, "500 bar (official)")
    dim_v(ax, 430, 0, g8z, f"{g8z:.0f}", off=8, ha="left")
    dim_v(ax, 470, 0, zsd, f"{zsd:.1f}", off=8, ha="left")
    dim_v(ax, -460, 0, S.POLE_H * MM, "pole 800", off=-8)
    ax.text(W / 2 + 8, g8z + H - 10, "border: top 10,\nsides 11.7, chin 20.1\n(arc mm)", fontsize=10, color=INK, va="top")
    ax.text(S.SD_W * MM / 2 + 8, zsd + S.SD_H * MM - 8, "border 13 all round\ncorner R5.3", fontsize=10, color=INK,
            va="top")
    ax.set_xlim(-720, 720)
    ax.set_ylim(-110, 1020)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- side (section at x = 0, front to the left) ------------------------
    ax = fig.add_axes([0.50, 0.30, 0.24, 0.61])
    ax.set_title("SIDE  (centre section, front left)", loc="left", fontsize=15, color=INK, weight="bold")
    zs = np.linspace(0, S.G8_H, 200)
    back = [S.g8_d(0.0, z) * MM for z in zs]
    ax.fill_betweenx(g8z + zs * MM, 0, back, color="#e7e9ec", ec=INK, lw=1.5)
    edge_y = -S.G8_SAG * MM
    ax.plot([edge_y, edge_y], [g8z, g8z + H], color=HID, ls="--", lw=1)
    ax.plot([edge_y, edge_y + S.G8_EDGE_T * MM], [g8z + H, g8z + H], color=HID, lw=1)
    hc = g8z + S.G8_HUB_ZC * MM
    prof, _ = S.g8_hub_profile(16)          # round 2: the rim, the lit ring and the trumpet, as built
    hub = [(y * MM, hc + r * MM) for r, y in prof] + [(y * MM, hc - r * MM) for r, y in reversed(prof)]
    ax.add_patch(Polygon(hub, fc="#3b4250", ec=INK, lw=1))
    rrect(ax, 0, zsd, S.SD_T * MM, S.SD_H * MM, 3, fc="#e7e9ec", ec=INK, lw=1.5)
    ax.add_patch(Polygon([(S.SD_T * MM, zsd + S.SD_H * MM - 319), (S.SD_DEPTH * MM, zsd + S.SD_H * MM - 319),
                          (S.SD_DEPTH * MM, zsd + S.SD_H * MM - 123.5), (S.SD_T * MM, zsd + S.SD_H * MM - 123.5)],
                         fc="#d5d8dc", ec=INK, lw=1))
    # arms and pole
    py = S.POLE_Y * MM
    for y0, zc in ((S.G8_HUB_BACK_Y * MM, g8z + S.G8_HUB_ZC * MM), (S.SD_DEPTH * MM, zsd + S.SD_H * MM / 2)):
        ax.add_patch(Polygon([(y0, zc - 57.5), (y0 + 4, zc - 57.5), (y0 + 4, zc + 57.5), (y0, zc + 57.5)], fc="white",
                             ec=INK, lw=1))
        ax.add_patch(Polygon([(y0 + 4, zc - 14), (py, zc - 14), (py, zc + 14), (y0 + 4, zc + 14)], fc="white", ec=INK,
                             lw=1))
        ax.add_patch(Polygon([(py - 27, zc - 26), (py + 27, zc - 26), (py + 27, zc + 26), (py - 27, zc + 26)],
                             fc="white", ec=INK, lw=1))
    ax.add_patch(Polygon([(py - 17.5, 0), (py + 17.5, 0), (py + 17.5, S.POLE_H * MM), (py - 17.5, S.POLE_H * MM)],
                         fc="white", ec=INK, lw=1.2))
    dby = S.DESK_BACK_Y * MM
    ax.add_patch(Polygon([(-300, -30), (dby, -30), (dby, 0), (-300, 0)], fc="#f0efe9", ec=INK, lw=1))
    ax.add_patch(Polygon([(py - 55, 0), (dby + 10, 0), (dby + 10, 10), (py - 55, 10)], fc="white", ec=INK, lw=1))
    ax.add_patch(Polygon([(dby + 10, 10), (dby + 22, 10), (dby + 22, -62), (dby + 10, -62)], fc="white", ec=INK, lw=1))
    # screenbar section on the top screen
    bz = zsd + S.SD_H * MM
    o_ = S.halo_fit(S.SD_T * MM)[0]
    ax.add_patch(Polygon([(y + o_, bz + z) for y, z in S.halo_bar_section()], fc="#3a3d42", ec=INK, lw=1))
    ax.add_patch(Polygon([(y + o_, bz + z) for y, z in S.HALO_ARM], fc="#55585e", ec=INK, lw=1))
    ax.add_patch(Polygon([(60.5 + o_, bz - 0.8), (81.9 + o_, bz - 0.8), (81.9 + o_, bz + 45.4), (60.5 + o_, bz + 45.4)],
                         fc="#55585e", ec=INK, lw=1))
    off, p0, p1 = S.halo_fit(S.SD_T * MM)
    wpts = [(S.HALO_HINGE[0] + y + off, bz + S.HALO_HINGE[1] + z) for y, z in S.HALO_WEIGHT]
    ax.add_patch(Polygon(wpts, fc="#55585e", ec=INK, lw=1))
    ax.add_patch(Polygon([(p0 + off, bz), (p1 + off, bz), (p1 + off, bz + 7.6), (p0 + off, bz + 7.6)], fc="#222",
                         ec=INK, lw=1))
    dim_h(ax, edge_y, S.G8_HUB_BACK_Y * MM, g8z - 30, "128.1 (official)", off=-22)
    ax.annotate("", (edge_y, g8z + H + 18), (0, g8z + H + 18), arrowprops=dict(arrowstyle="<->", color=DIM, lw=1))
    ax.text(-60, g8z + H + 26, "46.6 sag\n(1800R)", fontsize=10, color=DIM, ha="center")
    dim_h(ax, 0, S.SD_DEPTH * MM, zsd - 25, "31 (official)", off=-22)
    dim_h(ax, -62 + o_, 81.9 + o_, bz + 75, "143.8 (official)")
    dim_h(ax, 0, py, -95, f"pole at {py:.0f}", off=2)
    ax.text(S.G8_D0 * MM + 3, g8z + 110, "shell 50.8\nbehind the\nglass centre", fontsize=9.5, color=INK)
    ax.set_xlim(-140, 290)
    ax.set_ylim(-110, 1020)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- top -----------------------------------------------------------------
    ax = fig.add_axes([0.50, 0.04, 0.47, 0.25])
    ax.set_title("TOP  (front at the bottom)", loc="left", fontsize=15, color=INK, weight="bold")
    ss = np.linspace(-S.G8_S, S.G8_S, 300)
    fr = np.array([S.g8_front(s, 0) for s in ss]) * MM
    bk = np.array([[S.g8_front(s, 0)[0] + S.g8_n(s)[0] * S.g8_T(s), S.g8_front(s, 0)[1] + S.g8_n(s)[1] * S.g8_T(s)]
                   for s in ss]) * MM
    ax.add_patch(Polygon(np.vstack([fr[:, :2], bk[::-1]]), fc="#e7e9ec", ec=INK, lw=1.5))
    ax.add_patch(Polygon([(r * MM, y * MM) for r, y in prof] + [(-r * MM, y * MM) for r, y in reversed(prof)],
                         fc="#3b4250", ec=INK, lw=1))
    ax.add_patch(Polygon([(-S.SD_W * MM / 2, 0), (S.SD_W * MM / 2, 0), (S.SD_W * MM / 2, S.SD_T * MM),
                          (-S.SD_W * MM / 2, S.SD_T * MM)], fill=False, ec=INK, lw=1, ls=":"))
    ax.add_patch(Circle((0, py), 17.5, fc="white", ec=INK, lw=1.2))
    ax.add_patch(Polygon([(-250, -62), (250, -62), (250, -34.5), (-250, -34.5)], fc="#3a3d42", ec=INK, lw=1, alpha=0.5))
    dim_h(ax, -S.G8_W * MM / 2, S.G8_W * MM / 2, -95, "813.6 chord, R1800 (official)", off=-28)
    ax.text(S.G8_W * MM / 2 + 10, -40, "edge 3.9\n(thinnest)", fontsize=10, color=INK)
    ax.text(-S.SD_W * MM / 2, 30, "top screen (dotted), bar shaded", fontsize=10, color=HID)
    ax.set_xlim(-520, 520)
    ax.set_ylim(-140, 230)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- notes -------------------------------------------------------------------
    notes = (
        "SOURCES\nofficial = maker's page or drawing\nmeasured = from the official photos,\n"
        "  pixel scale from an official size\nest = estimated\n(every number is tagged in screens.py)\n\n"
        "G8: 813.6 x 363.5, depth 128.1,\n1800R, VESA 100 (official).\nShell depth across the width from\n"
        "the top-view photo, down the height\nfrom the side photo; hub 264 across,\n180 below the top (measured).\n\n"
        "Studio Display: 623 x 362 x 31\nwith the VESA adapter (official);\nbody 20.5, border 13, corner R5.3,\n"
        "the H adapter (measured).\n\n"
        "ScreenBar Halo 2: bar 500, 143.8\ndeep, 109.1 tall, clamp 47.4\n(official drawing). Pad slides on\n"
        "its rail; on a 20.5 mm back the bar\nstands %.0f mm further forward (est).\n\n"
        "Pole: our design, white, 35 x 800,\nC-clamp, two collar arms with tilt\nand swivel heads (VIVO STAND-V102\n"
        "kind, in white). Screen gap 15 and\nG8 height 115: est from the photo." % -S.halo_fit(S.SD_T * MM)[0])
    fig.text(0.80, 0.90, notes, fontsize=11, color=INK, va="top", family="monospace")
    out = os.path.join(FOOT, "screens-blueprint.png")
    fig.savefig(out, dpi=100, facecolor=fig.get_facecolor())
    print("blueprint", out)


# ---------------------------------------------------------------------------
# compare sheets
# ---------------------------------------------------------------------------
def compare_sheets():
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    rp = os.path.join(FOOT, "screens-quick-report.json" if QUICK else "screens-report.json")
    rep = json.load(open(rp))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
        small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except OSError:
        font = small = ImageFont.load_default()
    notes = {
        "g8-front": "Samsung's own dimension graphic (front, with its stand). Silhouette fit: camera ~%.1f m.",
        "g8-front-gallery": "Samsung gallery front g8-01: its panel reads ~6%% taller than in Samsung's dimension "
                            "graphic and back photo; we follow the official 813.6 x 363.5.",
        "g8-back": "Samsung gallery back g8-02 (stand on). The ring light is cool white here, RGB in the photo.",
        "sd-front": "Apple front, screen off (its tilt stand cropped off). Orthographic, same scale.",
        "sd-back": "Apple's VESA-adapter back diagram. Orthographic, same scale; the arm plate hidden.",
    }
    for name, c in rep.get("compare", {}).items():
        ph = Image.open(c["photo"]).convert("RGBA")
        W, H = ph.size
        bgc = (255, 255, 255, 255) if c["photo_mask_mode"] != "alpha" else (232, 233, 236, 255)
        base = Image.new("RGBA", (W, H), bgc)
        base.alpha_composite(ph)
        ph = base
        rd = Image.open(c["render"]).convert("RGBA")
        tf = c["transform"]
        s = tf["scale"]
        rw = rd.resize((max(1, int(rd.size[0] * s)), max(1, int(rd.size[1] * s))), Image.LANCZOS)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(rw, (int(round(tf["tx"])), int(round(tf["ty"]))), rw)
        rend = Image.new("RGBA", (W, H), bgc)
        rend.alpha_composite(layer)
        over = Image.blend(ph, rend, 0.5)
        # outlines: photo red, render blue
        pa = np.array(ph.convert("RGB")).astype(float)
        pm = (np.array(Image.open(c["photo"]).convert("RGBA"))[..., 3] > 128) if c["photo_mask_mode"] == "alpha" \
            else pa.mean(-1) / 255 < c["photo_mask_mode"]
        if c.get("crop"):
            x0, x1, y0, y1 = c["crop"]
            k = np.zeros_like(pm)
            k[y0:y1, x0:x1] = True
            pm &= k
        rm = np.array(layer)[..., 3] > 128
        edge = Image.new("RGB", (W, H), (255, 255, 255))
        ea = np.array(ph.convert("L").convert("RGB")).astype(float) * 0.35 + 165
        for m, col in ((pm, (220, 40, 40)), (rm, (40, 90, 230))):
            mi = Image.fromarray((m * 255).astype(np.uint8))
            e = np.array(mi.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))) > 0
            ea[e] = col
        edge = Image.fromarray(ea.astype(np.uint8))
        ys, xs = np.nonzero(pm | rm)
        pad = int(0.04 * max(W, H))
        box = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(W, xs.max() + pad), min(H, ys.max() + pad))
        sheet = Image.new("RGB", (1920, 1080), (246, 244, 238))
        d = ImageDraw.Draw(sheet)
        d.text((24, 14), f"screens: photo compare  {name}   silhouette IoU {c['iou']:.3f}"
               + (f"  (panel only {c['iou_panel']:.3f})" if c.get("iou_panel") and c["iou_panel"] != c["iou"] else ""),
               fill=(29, 39, 51), font=font)
        note = notes.get(name, "")
        if "%.1f" in note:
            note = note % (c["distance_m"] if isinstance(c["distance_m"], float) else 0)
        d.text((24, 50), note, fill=(29, 39, 51), font=small)
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
        out = os.path.join(FOOT, f"screens-compare-{name}{'-quick' if QUICK else ''}.png")
        sheet.save(out)
        print("compare", name, c["iou"], out)


if __name__ == "__main__":
    blueprint()
    compare_sheets()
