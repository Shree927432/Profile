"""guitar_06's fretboard inlay, drawn as a mask: the piano's tribal strokes (blender/lib/piano_ornament.py,
the language decided 2026-10-22: "The Henson guitar's fretboard inlay will use the same language,
vertical, emblem at the 12th fret"), our own composition, not the Tree of Death:
    the tuning fork at the 12th fret, its tines towards the nut;
    the piano's long upper arm running from above the fork towards the nut;
    the fallboard's short wing running from below the fork's stem towards the body.
Plain Python with Pillow (Blender's Python has none): props/guitar_06.py runs it through a subprocess.

    python3 -I blender/props/guitar_06_inlay.py <out.png> [px_per_mm]

The image covers the board's top: x from -30 to +30 mm across (+ to the treble side, as the guitar
hangs), y from the nut (row 0) to 500 mm towards the body; white is silver, black is ebony.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from lib import piano_ornament as PO  # noqa: E402
from lib.guitar_specs import GUITAR_06 as G, fret_positions  # noqa: E402

X0, X1, Y1 = -30.0, 30.0, 500.0


def composition():
    """[(piece, T)]: T maps the piece's local metres to board mm (x across, y from the nut)."""
    fr = fret_positions(G["scale"], G["frets"])
    yc = (fr[10] + fr[11]) / 2                     # the 12th fret's space
    sf = 0.9                                       # the fork: about 23 mm across the tines, 110 mm tall
    sa = 0.45                                      # the long arm: about 205 mm
    sw = 0.55                                      # the wing: about 95 mm

    def T(dx, dy, s, rot, my=1):
        c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        return lambda x, y: (dx + 1000 * s * (c * x - sn * y * my), dy + 1000 * s * (sn * x + c * y * my))
    fork_top = yc - 1000 * sf * 0.060
    fork_bot = yc + 1000 * sf * 0.063
    return [(PO.fork(), T(0.0, yc, sf, 0, my=-1)),                # tines towards the nut (-y)
            (PO.upper_arm(), T(1.5, fork_top - 4.0, sa, -90)),     # local +x runs to -y: towards the nut
            (PO.wing(), T(-1.0, fork_bot + 3.0, sw, 90))]          # towards the body


def main(out, ppm=8.0):
    from PIL import Image, ImageDraw
    W, H = int((X1 - X0) * ppm), int(Y1 * ppm)
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    px = lambda p: ((p[0] - X0) * ppm, p[1] * ppm)          # noqa: E731
    pieces = composition()
    for piece, T in pieces:
        for poly in piece.solid:
            d.polygon([px(T(x, y)) for x, y in poly], fill=255)
    for piece, T in pieces:
        for poly in piece.holes:
            d.polygon([px(T(x, y)) for x, y in poly], fill=0)
    im.save(out)
    print(f"inlay {W}x{H} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 8.0)
