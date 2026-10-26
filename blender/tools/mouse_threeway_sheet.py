"""Plain Python (Pillow): compose the three-way sheet from mouse_threeway.py renders.
    /opt/anaconda3/bin/python3 blender/tools/mouse_threeway_sheet.py <out_dir>"""
import os
import sys
from PIL import Image, ImageDraw

D = sys.argv[1]
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab", "23-mouse")
REAL = {"top": os.path.join(R, "top.png"), "nose": os.path.join(R, "front.png"),
        "thumb": os.path.join(R, "sketchfab-ref", "side-thumb.jpg"),
        "right": os.path.join(R, "sketchfab-ref", "side-right-profile.jpg"), "threeq": os.path.join(R, "three-quarter.png")}
NOTE = {"thumb": "sketchfab-ref (another author's model, graphite)", "right": "sketchfab-ref (another author's model, graphite)"}
W, H = 600, 430
rows = []
for k, real in REAL.items():
    row = Image.new("RGB", (W * 3, H + 34), (24, 24, 26))
    dr = ImageDraw.Draw(row)
    dr.text((10, 10), f"{k}: scan (local base, Sircher CC BY) | ours | real ({NOTE.get(k, 'Logitech image')})", fill=(235, 235, 235))
    for i, f in enumerate((os.path.join(D, f"tw-{k}-scan.png"), os.path.join(D, f"tw-{k}-ours.png"), real)):
        im = Image.open(f)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (150, 152, 156))
            bg.paste(im, mask=im.split()[3])
            im = bg
            bb = Image.open(f).convert("RGBA").split()[3].getbbox()
            if bb:
                pad = 60
                im = im.crop((max(bb[0] - pad, 0), max(bb[1] - pad, 0), bb[2] + pad, bb[3] + pad))
        im = im.convert("RGB")
        if f.endswith(".jpg") and "sketchfab-ref" in f:
            im = im.crop((150, 140, 650, 420))
        im.thumbnail((W - 10, H))
        row.paste(im, (i * W + (W - im.width) // 2, 34 + (H - im.height) // 2))
    row.save(os.path.join(D, f"threeway-{k}.jpg"), quality=88)
    rows.append(row)
s = Image.new("RGB", (W * 3, sum(r.height for r in rows)))
y = 0
for r in rows:
    s.paste(r, (0, y))
    y += r.height
s.save(os.path.join(D, "threeway-sheet.jpg"), quality=85)
print("SHEET", os.path.join(D, "threeway-sheet.jpg"))
