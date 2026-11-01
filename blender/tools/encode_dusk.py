"""Encode the dusk bake for the site (2026-11-01): blender/out/dusk/{lightmap,env}.exr -> scene/assets/dusk/.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/tools/encode_dusk.py
    env: LM_PX (atlas size on the site, default 2048), LM_Q / ENV_Q (WebP quality), EXPOSURE, BACKDROP_GAIN,
         EMISSIVE_GAIN, ENV_GAIN (written into room-light.json for scene/room-light.js)

Blender reads the EXRs (numpy does the rest), Pillow (/opt/anaconda3/bin/python3) writes the WebPs.
The lightmap: a light denoise (a Gaussian of 1.6 px inside the baked texels only, so islands never bleed into each
other), the gaps filled outwards from each island (so mipmaps do not pull in black), then light / max as sRGB 8-bit.
max is the 99.8th percentile of the baked texels: only the hottest sun texels clip. The env map the same, no blur.
Re-run this alone to change the encoding; no re-bake.
"""
import json
import os
import subprocess
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "blender", "out", "dusk")
DST = os.path.join(REPO, "scene", "assets", "dusk")
PY = "/opt/anaconda3/bin/python3"
E = os.environ


def load(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(px)
    return px.reshape(h, w, 4)[::-1].copy()      # top row first, as an image file


def shift(a, dy, dx):
    return np.roll(np.roll(a, dy, 0), dx, 1)


# a Gaussian of sigma 1.6 px (7 taps)
TAPS = tuple((o, w) for o, w in zip(range(-3, 4), (0.071, 0.131, 0.189, 0.214, 0.189, 0.131, 0.071)))


def blur_masked(rgb, mask, taps=TAPS):
    num, den = rgb * mask[..., None], mask.astype(np.float32)
    for axis in (0, 1):
        n2, d2 = np.zeros_like(num), np.zeros_like(den)
        for o, w in taps:
            n2 += w * np.roll(num, o, axis)
            d2 += w * np.roll(den, o, axis)
        num, den = n2, d2
    out = rgb.copy()
    ok = mask & (den > 1e-4)
    out[ok] = num[ok] / den[ok][:, None]
    return out


def fill(rgb, mask, passes=24):
    rgb, mask = rgb.copy(), mask.copy()
    for _ in range(passes):
        acc, cnt = np.zeros_like(rgb), np.zeros(mask.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            m = shift(mask, dy, dx)
            acc += shift(rgb, dy, dx) * m[..., None]
            cnt += m
        new = (~mask) & (cnt > 0)
        if not new.any():
            break
        rgb[new] = acc[new] / cnt[new][:, None]
        mask = mask | new
    return rgb


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def png(path, rgb):
    im = bpy.data.images.new(os.path.basename(path), rgb.shape[1], rgb.shape[0], alpha=False)
    im.colorspace_settings.name = "Non-Color"
    px = np.ones((rgb.shape[0], rgb.shape[1], 4), np.float32)
    px[..., :3] = rgb
    im.pixels.foreach_set(px[::-1].ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()


def main():
    os.makedirs(DST, exist_ok=True)
    tmp = os.path.join(SRC, "enc")
    os.makedirs(tmp, exist_ok=True)
    lm = load(os.path.join(SRC, "lightmap.exr"))
    mask = lm[..., 3] > 0.5
    rgb = blur_masked(lm[..., :3], mask)
    rgb = fill(rgb, mask)
    lmax = float(np.percentile(rgb[mask].max(axis=1), 99.8))
    png(os.path.join(tmp, "lightmap.png"), srgb(rgb / lmax))
    ev = load(os.path.join(SRC, "env.exr"))[..., :3]
    emax = float(np.percentile(ev.max(axis=2), 99.0))
    png(os.path.join(tmp, "env.png"), srgb(ev / emax))
    print(f"ENCODE coverage {mask.mean():.3f} lmax {lmax:.3f} (mean {rgb[mask].mean():.3f}) emax {emax:.3f}", flush=True)
    lm_px, lq, eq = int(E.get("LM_PX", "2048")), int(E.get("LM_Q", "86")), int(E.get("ENV_Q", "90"))
    code = ("import sys\nfrom PIL import Image\n"
            "a=Image.open(sys.argv[1]).convert('RGB'); n=int(sys.argv[3])\n"
            "a=a.resize((n,n),Image.LANCZOS) if a.width!=n else a\n"
            "a.save(sys.argv[2],'WEBP',quality=int(sys.argv[4]),method=6)\n"
            "b=Image.open(sys.argv[5]).convert('RGB'); b.save(sys.argv[6],'WEBP',quality=int(sys.argv[7]),method=6)\n")
    subprocess.run([PY, "-c", code, os.path.join(tmp, "lightmap.png"), os.path.join(DST, "lightmap.webp"), str(lm_px),
                    str(lq), os.path.join(tmp, "env.png"), os.path.join(DST, "env.webp"), str(eq)], check=True)
    out = dict(
        note="Written by blender/tools/encode_dusk.py from the Cycles bake (blender/lib/lighting_dusk.py). light = texel * max.",
        exposure=float(E.get("EXPOSURE", "0.28")),
        backdropGain=float(E.get("BACKDROP_GAIN", "1.0")),
        emissiveGain=float(E.get("EMISSIVE_GAIN", "1.0")),
        lightmap=dict(file="lightmap.webp", max=round(lmax, 4)),
        env=dict(file="env.webp", max=round(emax, 4), gain=float(E.get("ENV_GAIN", "0.6"))),
    )
    with open(os.path.join(DST, "room-light.json"), "w") as f:
        json.dump(out, f, indent=1)
    for n in ("lightmap.webp", "env.webp", "room-light.json"):
        print(f"ENCODE {n} {os.path.getsize(os.path.join(DST, n)) / 1e3:.0f} KB", flush=True)


main()
sys.exit(0)
