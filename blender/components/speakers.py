"""speakers: the AI lab's studio monitors, a matched pair of ADAM Audio A7V in Arctic White
(the 25th-anniversary limited edition), and the two mounts the layout can choose between
(component, 2026-10-24).

  cabinet   ADAM A7V, 200 x 280 x 337 mm (W x D x H, official): the faceted front baffle, the X-ART
            folded-ribbon tweeter in its waveguide, the 7-inch woofer, the two front bass-reflex slots,
            the rear amplifier plate with its controls, inputs and heat sink, small rubber feet.
            White lacquer; black where the real one is black. No logo, no printed text; the small
            green status LED on the waveguide plate stays.
  mount 1   a slim white desk pole (35 mm) with a small top platform, through-desk fixing, raised to the
            heights in blender/lib/plan_v3.py (cabinet base 541.5 mm above the desk top).
  mount 2   IsoAcoustics ISO-155 isolation stand (short setting, 76 mm), black.

Built from scratch, at real size, in metres, away from any room layout. Frame: Blender, front at -Y,
right at +X, Z up, the desk top at z = 0. Every part is a child of the empty `speakers`. Part names
follow scene/objects/MESHES.md (obj_studio; the mount names are proposed in the report):

  studio_speaker_01, _02            cabinet with tweeter, woofer basket ring, ports, rear panel, feet
  studio_speaker_01_woofer, _02_    the moving part: cone, surround, dust cap (child of its cabinet,
                                    origin at the cone's centre on the front face, axes as the cabinet's)
  studio_speaker_01_pole, _02_      mount 1, origin on the desk top at the pole's axis
  studio_speaker_01_iso, _02_       mount 2, origin on the desk top at the stand's centre

Numbers: OFFICIAL = maker's page; MEASURED = from the official photos in
docs/moodboard/local/ai-lab/08-studio-monitors/ (white-front.jpg and white-back.jpg are near-orthographic
at 2.68 px/mm; black-front-1600.png at 4.0 px/mm; black-spin-side-left.jpg at 2.41 px/mm);
EST = estimated. The outline functions are plain Python so the blueprint can draw them.
Front-face coordinates are (x, z) in mm: x from the centre line, z from the bottom of the cabinet.
"""
import math

try:
    import bmesh
    import bpy
    from mathutils import Matrix, Vector
except ImportError:          # the blueprint imports the numbers without Blender
    bpy = None

MM = 0.001

# ---------------------------------------------------------------------------
# cabinet
# ---------------------------------------------------------------------------
W, D, H = 200.0, 280.0, 337.0      # OFFICIAL: adam-audio.com/en/product/a7v (mm)
RING_PROUD = 3.2                   # MEASURED: the woofer ring stands proud of the baffle (side view, 6 to 9 px)
FRONT_Y = -140.0 + RING_PROUD      # the central baffle plane; ring face to back = 280 (official D)
BACK_Y = 140.0                     # back face
FOOT_H = 1.2                       # EST: small rubber pads (not visible in any photo; kept small and inset)
FOOT_R = 6.0                       # EST
FOOT_AT = [(sx * 66.0, sy * 100.0) for sx in (-1, 1) for sy in (-1, 1)]   # EST
EDGE_R = 3.0                       # MEASURED: the edge highlight on white-front / white-back (about 8 px)
SEAM_BACK, SEAM_W = 27.0, 0.8      # MEASURED: the baffle's seam on the sides, 27 mm back (side view, 66 px)
# Photo scales: white-front.jpg 2.668 px/mm down (337 mm = rows 91 to 990), 2.705 px/mm across;
# black-spin-side-left.jpg 2.42 px/mm; black-back-1600.png 3.97 px/mm.
# The baffle's side facets: the flat centre panel narrows to the top; outside the line A-B each side
# folds back to the side wall, 16 mm deep at the top corner. MEASURED on white-front (contrast-enhanced)
# and on the side view (the facet meets the side wall at 156 mm and is 16 mm back at the top).
FACET_A = (-87.1, 191.2)          # round 2: brightness steps on 7 rows of white-front: x = -46.8 - 0.313 (320 - z)
FACET_B = (-41.5, 337.0)           # (the right side mirrors within 0.6 mm); meets the side wall at z = 150
FACET_DEPTH = 16.0
TOP_CHAMFER = (12.4, 14.5)         # MEASURED (side view, rows 124 to 154): height, depth of the top front edge

# woofer (centre z MEASURED on white-front 143.0 and black-front-1600 142.7)
WF_Z = 143.0
# radii MEASURED from radial brightness profiles on white-front.jpg (5 directions)
WF_FLANGE_R = 90.5                 # the basket ring's outer edge (white starts at 90.5 to 91)
WF_GROOVE_R = 79.5                 # the thin groove between the outer flange and the inner ring
WF_INNER_R = 72.3                  # inner ring to the surround
WF_SURR = (54.0, 71.5)             # surround roll from the cone edge to the basket (highlight at 63)
WF_CAP_R = 30.0                    # dust cap (its faint edge, 30 mm)
WF_SCREW_R = 85.5                  # MEASURED: six screws at 0, 60, ... 300 degrees
# the profile of the moving part, (r, a): a forward from the baffle plane, mm. Cone depth EST.
WF_PROFILE = ([(0.0, -16.2), (8.0, -16.5), (16.0, -17.3), (22.0, -18.2), (27.0, -19.2), (29.2, -19.7)],
              [(30.6, -20.1), (35.0, -18.2), (40.0, -15.8), (45.0, -12.9), (50.0, -9.8), (53.6, -7.4)])
CONE_LO, CONE_HI = 0.016, 0.0   # linear albedo of the charcoal (CONE_HI unused since round 4b)
CONE_VAR, CONE_CAP_LIFT, CONE_WEAVE_MM = 0.95, 0.55, 0.45   # linear albedo: charcoal, a full stroke (fitted to the photos' mean and p90)
CONE_BUMP_MM = 0.03               # stroke relief for the normal map
CONE_ROUGH, CONE_ANISO, CONE_SPEC = 0.5, 0.6, 0.22 # the brushed sheen
WF_ROLL_PEAK = -0.2                # EST: the top of the surround, just behind the baffle plane

# tweeter (X-ART folded ribbon in the HPS waveguide). Re-traced 2026-10-24 (round 2) on white-front.jpg
# (dark plate on white: outline columns and rows) and black-front-1600.png (4 px/mm, the mouth lip and ribbon).
TW_PLATE = (82.8, 83.6, 4.2, 2.5)           # outline: a superellipse |x/a|^n + |z/b|^n = 1, all four sides bulge
                                            # (top 2.2 mm, bottom 1.9 mm, sides 1.5 mm); w, h, n; 2.5 proud (EST)
TW_PLATE_Z = 282.2                          # 240.4 to 324.0 at the centre line
TW_PLATE_EDGE = 1.4                         # EST: the rounded outer edge (the photo's thin highlight)
TW_MOUTH = (73.5, 48.5, 3.2, 281.75)        # mouth (the lip): w, h, superellipse n, centre z; 307.5 to 256 (the
                                            # plain band below it is where the real plate carries the logo)
TW_LIP = 3.0                                # EST: the mouth's rounded lip
TW_THROAT = (29.0, 36.4, 2.5, 280.6)        # the ribbon's opening: w, h, corner r, centre z (ribbon 263.7 to 297.3)
TW_DEPTH = 18.0                             # EST: lip to the ribbon's frame; the photos' shading reads deep
RIBBON = (26.0, 6.25, 2.75, 4, 1.0)         # width, strip height, gap, strips, pleat pitch (1600 photo: 4 px pitch)
# invented brand (decision 2026-10-26): in the spot of the maker's logo on the waveguide plate, under the
# mouth, centred between the two lower screws. MEASURED on white-front.jpg (x 487-590, y 325-338 px against
# the screws at z 313.0 / 251.3, y 155 / 320 px; review round: 4.4 read small): cap height 4.7 mm, centre z 247.1, x 0, off-white pad print
# (photo grey 228 on the black plate), a bold, open-spaced feel. The name comes from content/room-brands.json.
BRAND = dict(z=247.1, height=4.7, colour="#e4e4e4")
TW_SCREWS = [(sx * 31.0, z) for z in (313.0, 251.3) for sx in (-1, 1)]
TW_LED = (0.0, 317.7)                       # the green status LED: in white-front.jpg (0.7, 318.5) and
                                            # black-front-1600.png (0, 314.2 on its 2.6 mm lower scale)

# bass-reflex slots, left one (the right one mirrors it). MEASURED on white-front.jpg (dark opening)
# Re-traced round 2 on a 3x crop with a mm grid: outer end -77.8, bottom 23.8, top-left corner 57.8, top edge
# falling 0.43 mm/mm to a round inner end (radius about 4.5) at -20.4.
PORT = [(-77.8, 57.8), (-20.4, 32.9), (-20.4, 23.8), (-77.8, 23.8)]     # bounding corners (blueprint)
PORT_CIRCLES = [(-73.3, 53.8, 4.5), (-25.2, 29.9, 5.0), (-73.8, 27.8, 4.0)]   # top-left, the round inner end,
                                                                             # bottom-left: x, z, r
PORT_FLARE = 8.5                            # MEASURED: the white lip's visible width (4 to 9 mm, about 6.5)
PORT_LIP, PORT_FUNNEL = 6.0, 8.0           # lip radius (white-front: the lip curves all the way in); funnel EST
PORT_DEPTH = 150.0                          # EST: the tube behind it (only its mouth shows)

# rear amplifier plate. MEASURED on black-back-1600.png (3.97 px/mm; plate rows 342 to 1260), checked on
# white-back.jpg. x is the MODEL's x: seen from behind, +x is on the viewer's left.
PLATE = (141.0, 231.0, 7.5, 168.25, 1.0)    # w, h, corner r, centre z, proud
HEATSINK = (62.0, 70.6, 176.1, 241.5, 26)   # x0, x1, z0, z1, strokes: the light meander on the plate's edge
BUTTONS = [(44.7, 235.9), (16.4, 235.9), (-16.0, 235.9), (-44.3, 235.9)]   # bass, desk, presence, treble
BUTTON_D = 12.0
VOICING = (-16.0, 210.9)
INPUT_SEL = (0.25, 155.9)
LEVEL = (-44.1, 212.3, 18.3)                # knob x, z, diameter
RJ45 = (4.4, 21.0, 205.3, 222.4)
XLR = (40.7, 162.0, 24.6)
RCA = (19.3, 170.4, 10.0)
IEC = (-34.6, 30.9, 70.3, 100.5)            # the inlet module's flange (pointed ends)
IEC_SOCKET = (3.8, 20.8, 75.3, 98.0)
IEC_FUSE = (-6.9, 1.9, 75.3, 98.0)
IEC_SWITCH = (-25.8, -8.8, 76.6, 96.0)
LEDS_LIT = [(44.5, 255.7), (16.3, 248.9), (-16.0, 255.7), (-44.2, 248.9), (-7.9, 223.5), (8.2, 170.0)]
LEDS_OFF = [(44.5, 252.3), (44.5, 248.9), (44.5, 245.6), (16.3, 252.3), (16.3, 245.6), (-16.0, 252.3),
            (-16.0, 248.9), (-44.2, 255.7), (-44.2, 252.3), (-16.0, 223.5), (-23.9, 223.5), (21.0, 161.0)]
PLATE_SCREWS = [(35.3, 278.7), (-35.3, 278.7), (50.6, 269.3), (-50.4, 269.3), (53.5, 256.0), (-52.9, 256.0),
                (65.1, 250.4), (-64.9, 250.4), (53.5, 200.0), (-52.9, 199.4), (53.5, 188.7), (-52.9, 188.7),
                (50.4, 174.5), (12.6, 177.6), (65.1, 168.5), (-64.9, 168.5), (30.9, 149.2), (53.5, 110.6),
                (-52.9, 110.6), (51.0, 92.9), (-50.4, 92.9), (65.1, 87.3), (-64.9, 87.3), (26.4, 86.0),
                (-29.6, 86.0), (35.9, 58.3), (-34.6, 58.3)]

# ---------------------------------------------------------------------------
# mounts
# ---------------------------------------------------------------------------
DESK_T = 35.0                      # plan v3: TOP_T
POLE_R = 17.5                      # plan v3: 35 mm pole
POLE_CAB_Z = 541.5                 # plan v3: SPK_Z - TOP, the cabinet's base above the desk top
POLE_HEAD = 20.0                   # plan v3: SPK_PLATE, the top plate under each cabinet
POLE_PLATE = (160.0, 220.0, 14.0)  # plan v3: 0.16 x 0.22; EST corner radius
ISO_W, ISO_D = 155.0, 190.0        # OFFICIAL: isoacoustics.com/products/iso-155
ISO_H_SHORT, ISO_H_TALL = 76.0, 210.0   # OFFICIAL
ISO_POST = (61.5, 79.0)            # MEASURED: corner post centres from the official footprint drawing
ISO_CUP_R, ISO_FOOT_R = 16.0, 17.0  # MEASURED (drawing: 32 mm circles); foot EST from the photos
PAIR_X = 300.0                     # the pair in the stills: 60 cm apart, square on (the layout decides)


# ---------------------------------------------------------------------------
# outlines (plain Python)
# ---------------------------------------------------------------------------
def round_poly(pts, radii, n=8):
    """Round each corner of a convex CCW-or-CW polygon by its radius. Returns the point list."""
    out = []
    k = len(pts)
    for i in range(k):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % k]
        a = (p0[0] - p1[0], p0[1] - p1[1])
        b = (p2[0] - p1[0], p2[1] - p1[1])
        la, lb = math.hypot(*a), math.hypot(*b)
        a, b = (a[0] / la, a[1] / la), (b[0] / lb, b[1] / lb)
        ang = math.acos(max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1])))
        r = radii[i]
        t = r / math.tan(ang / 2)
        s, e = (p1[0] + a[0] * t, p1[1] + a[1] * t), (p1[0] + b[0] * t, p1[1] + b[1] * t)
        bis = (a[0] + b[0], a[1] + b[1])
        lbis = math.hypot(*bis)
        c = (p1[0] + bis[0] / lbis * r / math.sin(ang / 2), p1[1] + bis[1] / lbis * r / math.sin(ang / 2))
        a0 = math.atan2(s[1] - c[1], s[0] - c[0])
        a1 = math.atan2(e[1] - c[1], e[0] - c[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for j in range(n + 1):
            u = a0 + da * j / n
            out.append((c[0] + r * math.cos(u), c[1] + r * math.sin(u)))
    return out


def signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def offset_poly(pts, d):
    """Offset a convex polygon outwards by d (vertex normals, mitred)."""
    ccw = signed_area(pts) > 0
    k = len(pts)
    out = []
    for i in range(k):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % k]
        ns = []
        for a, b in ((p0, p1), (p1, p2)):
            ex, ey = b[0] - a[0], b[1] - a[1]
            le = math.hypot(ex, ey) or 1.0
            ns.append((ey / le, -ex / le) if ccw else (-ey / le, ex / le))
        nx, ny = ns[0][0] + ns[1][0], ns[0][1] + ns[1][1]
        ln = math.hypot(nx, ny) or 1.0
        nx, ny = nx / ln, ny / ln
        cos_h = max(0.3, nx * ns[1][0] + ny * ns[1][1])
        out.append((p1[0] + nx * d / cos_h, p1[1] + ny * d / cos_h))
    return out


def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def _resample(poly, count):
    """`count` points evenly spaced along a closed polygon."""
    seg = [math.dist(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]
    tot = sum(seg)
    out, i, acc = [], 0, 0.0
    for k in range(count):
        t = tot * k / count
        while acc + seg[i] < t:
            acc += seg[i]
            i += 1
        u = (t - acc) / seg[i] if seg[i] else 0.0
        a, b = poly[i], poly[(i + 1) % len(poly)]
        out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


def port_lip_width(nx, nz):
    """The lip's visible width (mm) for an outward edge normal (nx, nz) of the LEFT port, re-traced on a 5x
    crop of white-front.jpg: about 8 at the outer end, 6 along the sloped top, 9 round the inner end, 5 along
    the bottom. Cosine-weighted between those four directions."""
    w = {(-1, 0): 8.0, (0, 1): 6.0, (1, 0): 9.0, (0, -1): 5.0}
    tot = acc = 0.0
    for (dx, dz), v in w.items():
        c = max(0.0, nx * dx + nz * dz)
        tot += c
        acc += c * v
    return acc / tot if tot else 7.0


def offset_var(pts, fn, scale=1.0, mirror=False):
    """Offset a convex CCW polygon outwards by fn(normal) * scale per vertex."""
    k = len(pts)
    out = []
    for i in range(k):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % k]
        tx, tz = p2[0] - p0[0], p2[1] - p0[1]
        ln = math.hypot(tx, tz) or 1.0
        nx, nz = tz / ln, -tx / ln                 # outward for a CCW polygon
        d = fn(-nx if mirror else nx, nz) * scale
        out.append((p1[0] + nx * d, p1[1] + nz * d))
    return out


def port_outline(side=-1, n=8):
    """The bass-reflex slot's opening (x, z) mm, CCW: the convex hull of its three corner circles
    (PORT_CIRCLES), so the inner end is a true half round and the edges run tangent. side +1 mirrors."""
    pts = []
    for cx, cz, r in PORT_CIRCLES:
        for k in range(72):
            a = 2 * math.pi * k / 72
            pts.append(((cx + r * math.cos(a)) * (-1 if side > 0 else 1), cz + r * math.sin(a)))
    poly = _resample(_hull(pts), 24 * n)
    return poly if signed_area(poly) > 0 else poly[::-1]


def superellipse(w, h, n, cz, count=64, cx=0.0):
    """CCW outline starting at the right, angle-sampled from the centre (x, z) mm."""
    out = []
    for i in range(count):
        t = 2 * math.pi * i / count
        c, s = math.cos(t), math.sin(t)
        r = (abs(c / (w / 2)) ** n + abs(s / (h / 2)) ** n) ** (-1 / n)
        out.append((cx + r * c, cz + r * s))
    return out


def rrect_by_angle(w, h, r, cz, count=64, about=None):
    """A rounded rectangle sampled by angle from `about` (x, z), so it pairs point for point with a
    superellipse sampled the same way."""
    ax, az = about if about else (0.0, cz)
    hw, hh = w / 2, h / 2

    def inside(x, z):
        dx, dz = abs(x) - (hw - r), abs(z - cz) - (hh - r)
        if dx <= 0 or dz <= 0:
            return abs(x) <= hw and abs(z - cz) <= hh
        return dx * dx + dz * dz <= r * r
    out = []
    for i in range(count):
        t = 2 * math.pi * i / count
        c, s = math.cos(t), math.sin(t)
        lo, hi = 0.0, max(w, h)
        for _ in range(40):
            mid = (lo + hi) / 2
            if inside(ax + mid * c, az + mid * s):
                lo = mid
            else:
                hi = mid
        out.append((ax + lo * c, az + lo * s))
    return out


def facet_x(z):
    """x of the left facet line at height z (mm)."""
    (x0, z0), (x1, z1) = FACET_A, FACET_B
    return x0 + (z - z0) * (x1 - x0) / (z1 - z0)


def facet_meets_side_z():
    (x0, z0), (x1, z1) = FACET_A, FACET_B
    return z0 + (-W / 2 - x0) * (z1 - z0) / (x1 - x0)



# ---------------------------------------------------------------------------
# the woofer cone's fibre texture (round 4): an image of many short brushed strokes
# ---------------------------------------------------------------------------
# Measured on black-front-1600.png and white-front.jpg (structure tensor, cone ring r 34 to 52 mm): the
# strokes run about 10 degrees off tangential (a slight spiral), spread about 22 degrees; 1 to 4 mm long,
# about 0.2 mm wide, dense; grey mean 46 to 50 with a 90th percentile of 105 to 115. The cap (r < 30) is a
# fine fabric with no main direction.
CONE_TEX = dict(size=2048, span=144.0, n_cone=600000, n_cap=9000, dev_mean=12.0, dev_sd=38.0, seed=7)
# dev_mean is +12 here because the woofer's local frame mirrors the front view; it renders about 10 degrees
# the photos' way (checked with the same structure-tensor histogram on the renders)


def cone_stroke_maps(size=None, seed=None):
    """(albedo, height, cone_mask) as float32 arrays size x size, row 0 = v 0 (Blender's bottom); the image
    spans CONE_TEX['span'] mm centred on the woofer's axis: u = x / span + 0.5, v = y / span + 0.5.
    Round 4b (coordinator: "subtle, fine, dense; the contrast comes from the sheen"):
      cone  hundreds of thousands of fine short strokes packed along arcs (about 10 degrees off tangential);
            the albedo keeps only a little of them (0..1, low contrast); the height carries them for the
            normal map, so the brushed sweep shows with the light, helped by a tangential anisotropic sheen
      cap   a tight plain weave (0.45 mm), its own albedo and height"""
    import numpy as np
    size = size or CONE_TEX["size"]
    rng = np.random.default_rng(CONE_TEX["seed"] if seed is None else seed)
    span = CONE_TEX["span"]
    px = size / span
    acc = np.zeros((size, size), np.float32)

    def splat(xs, ys, w):
        u = xs * px + size / 2
        v = ys * px + size / 2
        i0 = np.floor(u).astype(int)
        j0 = np.floor(v).astype(int)
        fu, fv = u - i0, v - j0
        for di, dj, ww in ((0, 0, (1 - fu) * (1 - fv)), (1, 0, fu * (1 - fv)), (0, 1, (1 - fu) * fv), (1, 1, fu * fv)):
            ii, jj = i0 + di, j0 + dj
            ok = (ii >= 0) & (jj >= 0) & (ii < size) & (jj < size)
            np.add.at(acc, (jj[ok], ii[ok]), (w * ww)[ok])

    S = 12
    t = np.linspace(-0.5, 0.5, S, dtype=np.float32)
    n_total = CONE_TEX["n_cone"]
    for chunk in range(0, n_total, 100000):
        n = min(100000, n_total - chunk)
        r = np.sqrt(rng.uniform(28.0 ** 2, 57.0 ** 2, n)).astype(np.float32)
        th = rng.uniform(0, 2 * np.pi, n).astype(np.float32)
        L = rng.gamma(4.0, 0.35, n).astype(np.float32) + 0.6
        dev = np.radians(rng.normal(CONE_TEX["dev_mean"], CONE_TEX["dev_sd"], n)).astype(np.float32)
        amp = rng.gamma(6.0, 1 / 6.0, n).astype(np.float32)          # even: no isolated bright hairs
        s = t[None, :] * L[:, None]
        rr = r[:, None] + s * np.sin(dev)[:, None]
        tt = th[:, None] + s * np.cos(dev)[:, None] / r[:, None]
        splat((rr * np.cos(tt)).ravel(), (rr * np.sin(tt)).ravel(), np.repeat(amp, S))

    def blur(img, sigma):
        k = np.fft.fftfreq(size)
        g = np.exp(-2 * (np.pi * sigma) ** 2 * (k[:, None] ** 2 + k[None, :] ** 2))
        return np.real(np.fft.ifft2(np.fft.fft2(img) * g)).astype(np.float32)
    strokes = blur(acc, 0.035 * px)
    strokes -= blur(strokes, 1.2 * px)                     # keep the fine structure only (no blotches)
    strokes /= np.percentile(np.abs(strokes), 99) + 1e-6
    yy, xx = (np.mgrid[0:size, 0:size].astype(np.float32) - size / 2 + 0.5) / px
    rad = np.hypot(xx, yy)
    cone_mask = np.clip((rad - 30.0) / 0.8, 0, 1).astype(np.float32)
    # the cap's weave: two sets of threads at right angles, over-under
    p = CONE_WEAVE_MM
    wx = 0.5 + 0.5 * np.cos(2 * np.pi * xx / p)
    wy = 0.5 + 0.5 * np.cos(2 * np.pi * yy / p)
    over = (np.floor(xx / p) + np.floor(yy / p)) % 2
    weave = np.where(over > 0, wx * (0.6 + 0.4 * wy), wy * (0.6 + 0.4 * wx)).astype(np.float32)
    albedo = cone_mask * (0.45 + 0.55 * np.clip(strokes * 1.8, -1, 1)) + (1 - cone_mask) * (0.55 + 0.45 * weave)
    height = cone_mask * strokes + (1 - cone_mask) * 0.6 * weave
    return albedo.astype(np.float32), height.astype(np.float32), cone_mask


if bpy is not None:
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from lib import brands, geo, materials as M, names  # noqa: E402
    from screens import Acc, frame, rr  # noqa: E402  (the approved component's mesh accumulator)

    V = Vector
    m_ = MM
    SWEEP_SEG = [0]          # set while building the web copy: fewer section points

    def F(x, z, w=0.0):
        """Front-face point (mm): x, z, and w forward of the baffle plane -> metres, Blender."""
        return V((x * m_, (FRONT_Y - w) * m_, z * m_))

    FRONT = frame((0, FRONT_Y * m_, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0))     # (x, z, forward)
    BACK = frame((0, BACK_Y * m_, 0), (-1, 0, 0), (0, 0, 1), (0, 1, 0))       # (-x, z, backward)

    def front_at(x, z):
        return frame((x * m_, FRONT_Y * m_, z * m_), (1, 0, 0), (0, 0, 1), (0, -1, 0))

    def back_at(x, z, w=0.0):
        return frame((x * m_, (BACK_Y + w) * m_, z * m_), (-1, 0, 0), (0, 0, 1), (0, 1, 0))

    def mmv(pts):
        return [(x * m_, z * m_) for x, z in pts]

    # -----------------------------------------------------------------------
    # materials
    # -----------------------------------------------------------------------
    def _bump(m, scale, strength, dist=0.0002):
        nt = m.node_tree
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        M._bump(nt, b, M._noise(nt, M._coords(nt), scale, detail=2), strength, dist)
        return m

    def _m(nt, op, *args):
        """A math node; each arg is a socket (linked) or a number."""
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, a in enumerate(args):
            if isinstance(a, (int, float)):
                n.inputs[i].default_value = a
            else:
                nt.links.new(a, n.inputs[i])
        return n.outputs[0]

    def _streaks(nt, vec, angle, along, across, thresh):
        """Short fibre strokes in one direction (object coords turned by `angle` about local Z)."""
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0.0, 0.0, angle)
        nt.links.new(vec, mp.inputs["Vector"])
        mp2 = nt.nodes.new("ShaderNodeMapping")
        mp2.inputs["Scale"].default_value = (along, across, across)
        nt.links.new(mp.outputs["Vector"], mp2.inputs["Vector"])
        n = M._noise(nt, mp2.outputs["Vector"], 1.0, detail=3, rough=0.55)
        return _m(nt, "MAXIMUM", _m(nt, "SUBTRACT", n, thresh), 0.0)

    def _cone(name):
        """The MLM cone: charcoal with short pale fibre strokes in every direction (tech-woofer.png,
        white-front.jpg, black-front-1600.png). Object coordinates of the woofer (local XY = the cone's face)."""
        m, nt, b = M._new(name)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        vec = tc.outputs["Object"]
        acc = None
        for k, ang in enumerate((0.0, 1.05, 2.1, 0.52, 1.57, 2.62)):
            st = _streaks(nt, vec, ang, 22.0 + 5 * k, 4200.0, 0.60)
            acc = st if acc is None else _m(nt, "MAXIMUM", acc, st)
        fac = _m(nt, "MULTIPLY", acc, 4.5)
        col = M._ramp(nt, fac, [(0.0, "#0f0f11"), (1.0, "#68686e")])
        nt.links.new(col, b.inputs["Base Color"])
        M._set(b, rough=0.72, spec=0.25, sheen=0.1, sheen_rough=0.35)
        M._bump(nt, b, fac, 0.25, 0.0001)
        m.diffuse_color = M.rgba("#252527")
        return m

    def _cap(name):
        """The dust cap: a fine woven fabric, the cone's charcoal (a 0.55 mm basket weave)."""
        m, nt, b = M._new(name)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        k = 2 * math.pi / 0.00055
        sx = _m(nt, "SINE", _m(nt, "MULTIPLY", sep.outputs[0], k), 0.0)
        sy = _m(nt, "SINE", _m(nt, "MULTIPLY", sep.outputs[1], k), 0.0)
        weave = _m(nt, "MULTIPLY", sx, sy)
        h = _m(nt, "MULTIPLY_ADD", weave, 0.5, 0.5)
        col = M._ramp(nt, h, [(0.0, "#040406"), (1.0, "#2c2c30")])
        nt.links.new(col, b.inputs["Base Color"])
        M._set(b, rough=0.75, spec=0.22, sheen=0.15, sheen_rough=0.4)
        M._bump(nt, b, h, 0.3, 0.0001)
        m.diffuse_color = M.rgba("#1c1c1e")
        return m

    def _ribbon(name):
        """The folded ribbon: gold with a dark line at every fold (1 mm pitch across x). The rich model also
        has the folds as geometry; the lite one keeps only this (baked into the atlas)."""
        m, nt, b = M._new(name)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        w = _m(nt, "SINE", _m(nt, "MULTIPLY", sep.outputs[0], 2 * math.pi / (RIBBON[4] * MM)), 0.0)
        line = _m(nt, "POWER", _m(nt, "MULTIPLY_ADD", w, 0.5, 0.5), 1.6)
        col = M._ramp(nt, line, [(0.0, "#f2cc2a"), (0.5, "#cf9f08"), (1.0, "#5a3e00")])
        nt.links.new(col, b.inputs["Base Color"])
        M._set(b, metal=0.35, rough=0.34)
        M._bump(nt, b, line, 0.4, 0.0002)
        m.diffuse_color = M.rgba("#c49200")
        return m

    def _port_tube(name, finish):
        """The port's tube: the cabinet's colour at the funnel, black 60 mm in (cabinet object coords)."""
        m, nt, b = M._new(name)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = (FRONT_Y + 12.0) * MM
        mr.inputs["From Max"].default_value = (FRONT_Y + 95.0) * MM
        nt.links.new(sep.outputs[1], mr.inputs["Value"])
        light = {"white": "#d8d8d6", "satin": "#d8d8d6", "black": "#1a1a1b"}[finish]
        col = M._ramp(nt, mr.outputs["Result"], [(0.0, light), (0.3, light), (0.6, "#5a5a5a"), (1.0, "#050505")])
        nt.links.new(col, b.inputs["Base Color"])
        M._set(b, rough=0.55, spec=0.4)
        m.diffuse_color = M.rgba("#202020")
        return m

    def _cone_images():
        """The cone's albedo (RGBA: grey strokes, A = 1 on the cone and 0 on the cap) and normal map, built
        once and packed into the .blend."""
        import numpy as np
        al, nm = bpy.data.images.get("speakers_cone_albedo"), bpy.data.images.get("speakers_cone_normal")
        if al is not None and nm is not None:
            return al, nm
        size = CONE_TEX["size"]
        strokes, height, mask = cone_stroke_maps(size)
        lo, hi = CONE_LO, CONE_HI                          # linear albedo of the charcoal and of a full stroke
        # low contrast in the base colour: the strokes vary it by +-CONE_VAR; the cap a touch lighter
        base = mask * lo + (1 - mask) * lo * CONE_CAP_LIFT
        grey = base * (1 + CONE_VAR * (2 * strokes - 1))
        px = np.ones((size, size, 4), np.float32)
        px[..., 0] = px[..., 1] = px[..., 2] = grey
        px[..., 3] = mask
        al = bpy.data.images.new("speakers_cone_albedo", size, size, alpha=True)
        al.colorspace_settings.name = "Non-Color"         # values are linear already
        al.pixels.foreach_set(px.ravel())
        al.pack()
        mmpp = CONE_TEX["span"] / size
        gy, gx = np.gradient(height * CONE_BUMP_MM, mmpp)
        n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        px = np.ones((size, size, 4), np.float32)
        px[..., :3] = n * 0.5 + 0.5
        nm = bpy.data.images.new("speakers_cone_normal", size, size, alpha=False)
        nm.colorspace_settings.name = "Non-Color"
        nm.pixels.foreach_set(px.ravel())
        nm.pack()
        return al, nm

    def _cone_mat(name):
        """The MLM cone and cap: the stroke image on the planar UV `ConeUV`, its normal map, and an
        anisotropic sheen brushed round the axis (the woofer's local Z), off on the cap."""
        al, nmi = _cone_images()
        m, nt, b = M._new(name)
        uv = nt.nodes.new("ShaderNodeUVMap")
        uv.uv_map = "ConeUV"
        ta = nt.nodes.new("ShaderNodeTexImage")
        ta.image = al
        ta.interpolation = "Cubic"
        nt.links.new(uv.outputs["UV"], ta.inputs["Vector"])
        nt.links.new(ta.outputs["Color"], b.inputs["Base Color"])
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = nmi
        nt.links.new(uv.outputs["UV"], tn.inputs["Vector"])
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.uv_map = "ConeUV"
        nmap.inputs["Strength"].default_value = 1.0
        nt.links.new(tn.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], b.inputs["Normal"])
        tg = nt.nodes.new("ShaderNodeTangent")
        tg.direction_type = "RADIAL"
        tg.axis = "Z"
        nt.links.new(tg.outputs["Tangent"], b.inputs["Tangent"])
        an = _m(nt, "MULTIPLY", ta.outputs["Alpha"], CONE_ANISO)
        nt.links.new(an, b.inputs["Anisotropic"])
        M._set(b, rough=CONE_ROUGH, spec=CONE_SPEC)
        # the cap is matte fabric: rougher where the alpha (the cone mask) is 0
        rmix = _m(nt, "MULTIPLY_ADD", ta.outputs["Alpha"], CONE_ROUGH - 0.62, 0.62)
        nt.links.new(rmix, b.inputs["Roughness"])
        m.diffuse_color = M.rgba("#262628")
        return m

    def make_materials(finish="white"):
        p = M.principled
        cab = {
            "white": lambda: p("mat_speakers_white_lacquer", base="#e6e6e4", rough=0.24, spec=0.5, coat=1.0,
                               coat_rough=0.05),
            "satin": lambda: p("mat_speakers_white_satin", base="#e6e6e4", rough=0.48, spec=0.45),
            "black": lambda: _bump(p("mat_speakers_black_paint", base="#1c1c1d", rough=0.7, spec=0.4),
                                   1400, 0.5, 0.0003),        # the black A7V's coarse speckle paint (compares only)
        }[finish]()
        seam = {"white": "#5e5e5e", "satin": "#5e5e5e", "black": "#090909"}[finish]
        mats = {
            "cab": cab,
            "seam": p(f"mat_speakers_seam_{finish}", base=seam, rough=0.6),
            "port": p("mat_speakers_port", base="#151515", rough=0.8, spec=0.3),
            "plastic": _bump(p("mat_speakers_plastic", base="#141415", rough=0.78, spec=0.25), 5200, 0.55,
                             0.00012),                      # the woofer ring's stippled matte
            "tw_plate": _bump(p("mat_speakers_waveguide_plate", base="#1a1a1b", rough=0.7, spec=0.32), 5200, 0.55,
                              0.00012),                     # the stippled matte face of the real plate
            "horn": _bump(p("mat_speakers_horn", base="#141415", rough=0.62, spec=0.35), 5200, 0.5, 0.00012),
            "screw": p("mat_speakers_screw", base="#1e1f21", metal=0.7, rough=0.45),
            "rubber": p("mat_speakers_surround", base="#060607", rough=0.66, spec=0.28),
            "cone": _cone_mat("mat_speakers_cone"),
            "cap": _cone_mat("mat_speakers_cone"),       # the photos: the cap in the cone's tone and texture
            "ribbon": _ribbon("mat_speakers_ribbon"),
            "bar": p("mat_speakers_ribbon_bar", base="#2e3033", metal=0.5, rough=0.45),
            "port_tube": _port_tube(f"mat_speakers_port_tube_{finish}", finish),
            "throat": p("mat_speakers_throat", base="#050505", rough=0.7),
            "plate": _bump(p("mat_speakers_rear_plate", base="#070708", metal=0.15, rough=0.62), 2600, 0.12),
            "alu": p("mat_speakers_heatsink", base="#cfd1d3", metal=1.0, rough=0.35),
            "knob": p("mat_speakers_knob", base="#0f0f10", rough=0.6, spec=0.3),
            "chrome": p("mat_speakers_jack_metal", base="#8c8e91", metal=1.0, rough=0.38),
            "gold": p("mat_speakers_gold", base="#d9b46a", metal=1.0, rough=0.25),
            "socket": p("mat_speakers_socket_white", base="#e8e6e0", rough=0.5),
            "switch": p("mat_speakers_switch", base="#0b0b0c", rough=0.15, coat=1.0, coat_rough=0.05),
            "led": M.emission("mat_speakers_led_green", "#38ff6c", 1.5),
            "led_off": p("mat_speakers_led_off", base="#2a2d2b", rough=0.25),
            "feet": p("mat_speakers_feet", base="#1a1a1b", rough=0.85),
            "pole": _bump(p("mat_speakers_pole_white", base="#eceeef", rough=0.48, spec=0.5), 1800, 0.08),
            "pole_black": _bump(p("mat_speakers_pole_black", base="#1b1c1d", rough=0.5, spec=0.5), 1800, 0.08),
            "pad": p("mat_speakers_pad", base="#202122", rough=0.9, spec=0.3),
            "iso": _bump(p("mat_speakers_iso_abs", base="#151516", rough=0.58, spec=0.45), 2600, 0.15),
            "iso_rod": p("mat_speakers_iso_rod", base="#121314", metal=0.6, rough=0.32),
            "iso_rubber": p("mat_speakers_iso_isolator", base="#1d1e1f", rough=0.8, spec=0.3),
        }
        mats["led"].diffuse_color = M.rgba("#38ff6c")
        return mats

    # -----------------------------------------------------------------------
    # helpers
    # -----------------------------------------------------------------------
    def merge(parts, name, mats, collection, parent, angle=14.0):
        """parts: [(mesh, [key per slot])]. One object, one slot per key, sharp edges by angle."""
        bm = bmesh.new()
        keys = []
        for me, slot_keys in parts:
            n0 = len(bm.faces)
            bm.from_mesh(me)
            bm.faces.ensure_lookup_table()
            for f in bm.faces[n0:]:
                k = slot_keys[f.material_index] if f.material_index < len(slot_keys) else slot_keys[0]
                if k not in keys:
                    keys.append(k)
                f.material_index = keys.index(k)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
        me = bpy.data.meshes.new(name + "_mesh")
        bm.to_mesh(me)
        bm.free()
        for k in keys:
            me.materials.append(mats[k])
        obj = bpy.data.objects.new(name, me)
        collection.objects.link(obj)
        obj.parent = parent
        names.set_name(obj, name)
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(angle))
        return obj

    def evaluated(obj):
        """The object's mesh with its modifiers applied (a new datablock), and its slot keys."""
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
        return me

    def acc_mesh(A, mats, bevel=None, coll=None):
        """Finish an Acc into a temporary object, apply an optional bevel, return (mesh, keys)."""
        keys = list(A.keys)
        coll = coll or bpy.context.scene.collection
        tmp = A.finish("tmp_speakers_part", mats, coll, None, smooth=False, bevel=bevel)
        me = evaluated(tmp)
        old = tmp.data
        bpy.data.objects.remove(tmp)
        bpy.data.meshes.remove(old)
        return me, keys

    def ring_strip(A, a, b, key, want=None):
        A.strip(a, b, key, closed_loop=True, solid=True)

    def lathe_at(A, prof_mm, frm, seg, keys, cap_start=True, cap_end=True):
        A.lathe([(r * m_, a * m_) for r, a in prof_mm], frm, seg, keys, cap_start=cap_start, cap_end=cap_end)

    def button_head(A, frm, r, h, seg, key):
        """A round button head / domed knob of radius r, height h (mm), on the frame's plane. Screws get a
        hex socket (a dark six-sided recess)."""
        if key == "screw":
            prof = [(r, 0.0), (r, h * 0.55), (r * 0.9, h * 0.85), (r * 0.55, h), (r * 0.42, h)]
            lathe_at(A, prof, frm, seg, key, cap_start=True, cap_end=False)
            lathe_at(A, [(r * 0.42, h), (r * 0.42, h - 0.35), (0.0, h - 0.35)], frm, 6, "port", cap_start=False,
                     cap_end=False)
            return
        prof = [(r, 0.0), (r, h * 0.6), (r * 0.92, h * 0.88), (r * 0.6, h), (0.0, h)]
        lathe_at(A, prof, frm, seg, key, cap_start=True, cap_end=False)

    def sweep(A, path, w, h, key, seg=4):
        seg = SWEEP_SEG[0] or seg
        """A rounded-rect section (w across, h tall, mm) swept along a 3D path (mm, Blender axes)."""
        sec = rr(w, h, min(w, h) * 0.35, seg)
        rings = []
        for i, p in enumerate(path):
            p = V(p)
            t = (V(path[min(i + 1, len(path) - 1)]) - V(path[max(i - 1, 0)])).normalized()
            side = t.cross(V((0, 0, 1)))
            if side.length < 1e-6:
                side = V((1, 0, 0))
            side.normalize()
            up = side.cross(t).normalized()
            rings.append(A.verts([(p + side * u + up * v) * m_ for u, v in sec]))
        for i in range(len(rings) - 1):
            A.strip(rings[i], rings[i + 1], key, closed_loop=True, solid=True)
        A.face(list(reversed(rings[0])), key, closed=True)
        A.face(rings[-1], key, closed=True)

    # -----------------------------------------------------------------------
    # cabinet body: box, facets and top chamfer cut off, edges rounded, seams, holes cut
    # -----------------------------------------------------------------------
    def _cut(bm, co, no):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=co, plane_no=no, clear_outer=True)
        bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)

    def body_bmesh():
        bm = bmesh.new()
        x0, x1 = -W / 2 * m_, W / 2 * m_
        y0, y1 = FRONT_Y * m_, BACK_Y * m_
        z0, z1 = FOOT_H * m_, H * m_
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = V((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
        # side facets
        for s in (-1, 1):
            A = V((s * abs(FACET_A[0]), FRONT_Y, FACET_A[1])) * m_
            B = V((s * abs(FACET_B[0]), FRONT_Y, FACET_B[1])) * m_
            C = V((s * W / 2, FRONT_Y + FACET_DEPTH, H)) * m_
            n = (B - A).cross(C - A).normalized()
            test = V((s * (W / 2 - 1), FRONT_Y - 1, H - 1)) * m_
            if n.dot(test - A) < 0:
                n = -n
            _cut(bm, A, n)
        # top chamfer
        ch, cd = TOP_CHAMFER
        P = V((0, FRONT_Y, H - ch)) * m_
        Q = V((0, FRONT_Y + cd, H)) * m_
        n = V((1, 0, 0)).cross(Q - P).normalized()
        if n.dot(V((0, -1, 1))) < 0:
            n = -n
        _cut(bm, P, n)
        # the seam: two parallel cuts, the strip between them gets the seam colour
        for yy in (FRONT_Y + SEAM_BACK, FRONT_Y + SEAM_BACK + SEAM_W):
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-7,
                                   plane_co=V((0, yy * m_, 0)), plane_no=V((0, 1, 0)))
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            c = f.calc_center_median()
            f.material_index = 1 if (FRONT_Y + SEAM_BACK) * m_ < c.y < (FRONT_Y + SEAM_BACK + SEAM_W) * m_ else 0
        return bm

    def cutters_bmesh(lite):
        """Closed cutters: the two ports (flared mouth, white; tube, dark), the woofer hole, the horn hole."""
        A = Acc()
        nr = 3 if lite else 7
        npts = 1 if lite else 8
        for side in (-1, 1):
            P = port_outline(side, npts)
            rings = []
            front = A.verts([(x * m_, z * m_, 3 * m_) for x, z in offset_poly(P, PORT_FLARE)], FRONT)  # 3 mm in front of the face
            rings.append((front, None))
            # the mouth: a crisp rounded lip (3 mm) off the face, then a straight funnel down to the tube
            # (black-front-1600 and tech-bass-reflex.png show the lip and the flat funnel walls)
            # the lip: a crisp crease at its outer edge (0.9 mm step), then a round over into the slot
            # (white-front: the bright rounded rim with a visible outer edge)
            r_ = PORT_FLARE - 0.6
            prof = [(PORT_FLARE, 0.0), (r_, 0.5)]
            nk = 2 if lite else 6
            for k in range(1, nk + 1):
                th = math.pi / 2 * k / nk
                prof.append((r_ * (1 - math.sin(th)), 0.5 + r_ * (1 - math.cos(th))))
            prof += [(0.0, max(PORT_FUNNEL, prof[-1][1] + 1.0))]
            for off, dep in prof:
                ring_pts = offset_var(P, port_lip_width, off / PORT_FLARE, mirror=side > 0)
                rings.append((A.verts([(x * m_, z * m_, -dep * m_) for x, z in ring_pts], FRONT), "cab"))
            depth = 40.0 if lite else PORT_DEPTH
            # the tube: white lacquer that darkens with depth (as the photos: lit lip, black inside)
            # the slot narrows into the cabinet (its walls face the front and catch the light, as in the
            # photos): 4 mm in all round by 45 mm deep, straight after that
            for dd, inset in (((PORT_FUNNEL + 8.0, 1.0), (25.0, 2.5), (45.0, 4.0)) if not lite else ((45.0, 4.0),)):
                rings.append((A.verts([(x * m_, z * m_, -dd * m_) for x, z in offset_poly(P, -inset)], FRONT),
                              "port_tube"))
            rings.append((A.verts([(x * m_, z * m_, -depth * m_) for x, z in offset_poly(P, -4.0)], FRONT),
                          "port_tube"))
            for i in range(len(rings) - 1):
                A.strip(rings[i][0], rings[i + 1][0], rings[i + 1][1] or "cab", closed_loop=True, solid=True)
            A.face(list(reversed(rings[0][0])), "cab", closed=True)
            A.face(rings[-1][0], "port", closed=True)
        # woofer hole (behind the basket ring) and the waveguide's hole
        A.cyl((WF_INNER_R + 0.3) * m_, F(0, WF_Z, 3), F(0, WF_Z, -45), 32 if lite else 96, "port")
        # the hole under the waveguide: the plate's outline less 4 mm, so no edge of it can cross the horn
        pw, ph, pn, _ = TW_PLATE
        hole = superellipse(pw - 4.0, ph - 4.0, pn, TW_PLATE_Z, 32 if lite else 96)
        A.prism(mmv(hole), FRONT, -30 * m_, 3 * m_, "port")
        return A

    def build_body(mats, lite):
        coll = bpy.context.scene.collection
        bm = body_bmesh()
        me = bpy.data.meshes.new("tmp_speakers_body_mesh")
        bm.to_mesh(me)
        bm.free()
        body = bpy.data.objects.new("tmp_speakers_body", me)
        coll.objects.link(body)
        for k in ("cab", "seam", "port"):
            me.materials.append(mats[k])
        bv = body.modifiers.new("bevel", "BEVEL")
        bv.width = EDGE_R * m_
        bv.segments = 2 if lite else 7
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(30)
        bv.use_clamp_overlap = True
        A = cutters_bmesh(lite)
        ckeys = list(A.keys)
        cut = A.finish("tmp_speakers_cutter", mats, coll, None, smooth=False)
        bo = body.modifiers.new("ports", "BOOLEAN")
        bo.operation = "DIFFERENCE"
        bo.solver = "EXACT"
        bo.object = cut
        bo.material_mode = "TRANSFER"
        out = evaluated(body)
        keys = []
        for mat in out.materials:
            keys.append(next(k for k, v in mats.items() if v == mat))
        for o in (body, cut):
            d = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(d)
        return out, keys, ckeys

    # -----------------------------------------------------------------------
    # front details: woofer ring, tweeter plate and waveguide, ribbon, screws, LED
    # -----------------------------------------------------------------------
    def build_front(A, lite):
        seg = 48 if lite else 160
        # woofer basket ring (the flange with its groove and inner ring)
        gr, ir = WF_GROOVE_R, WF_INNER_R
        rp = RING_PROUD
        bw = WF_SURR[1] + 0.3            # the basket's inner wall, just outside the surround
        prof = [(bw, -7.0), (bw, rp - 2.0), (bw + 0.6, rp - 1.2), (gr - 0.6, rp - 0.9), (gr - 0.4, rp - 1.5),
                (gr + 0.4, rp - 1.5), (gr + 0.6, rp - 0.4), (WF_FLANGE_R - 2.6, rp), (WF_FLANGE_R - 0.9, rp - 0.4),
                (WF_FLANGE_R, rp - 1.4), (WF_FLANGE_R, -0.8), (bw, -7.0)]
        if lite:
            prof = [(bw, -7.0), (bw, rp - 2.0), (bw + 0.9, rp - 0.9), (WF_FLANGE_R - 1.5, rp), (WF_FLANGE_R, rp - 1.4),
                    (WF_FLANGE_R, -0.8), (bw, -7.0)]
        lathe_at(A, prof, front_at(0, WF_Z), seg, "plastic", cap_start=False, cap_end=False)
        sseg = 6 if lite else 24
        for k in range(6):
            t = math.radians(60 * k)
            x, z = WF_SCREW_R * math.cos(t), WF_Z + WF_SCREW_R * math.sin(t)
            fr = frame(F(x, z, RING_PROUD - 0.15), (1, 0, 0), (0, 0, 1), (0, -1, 0))
            if not lite:
                lathe_at(A, [(3.8, -0.3), (3.8, 0.05), (3.2, 0.05), (0.0, 0.05)], fr, sseg, "port", cap_start=False,
                         cap_end=False)
            button_head(A, fr, 3.4, 1.2, sseg, "screw")
        build_tweeter(A, lite, sseg)

    def build_tweeter(A, lite, sseg):
        """The waveguide plate (a bulging superellipse with a rounded edge), the rounded mouth lip, the
        flared horn down to the ribbon's frame, the folded ribbon, four screws and the status LED."""
        pw, ph, pn, pp = TW_PLATE
        mw, mh, mn, mz = TW_MOUTH
        tw, th, tr, tz = TW_THROAT
        n = 40 if lite else 128
        about = (0.0, (TW_PLATE_Z + mz) / 2)
        outer = [_ray_superellipse(pw, ph, pn, TW_PLATE_Z, about, i, n) for i in range(n)]
        mouth = [_ray_superellipse(mw, mh, mn, mz, about, i, n) for i in range(n)]
        throat = rrect_by_angle(tw, th, tr, tz, n, about)

        def ring(pts, w):
            return A.verts([(x * m_, z * m_, w * m_) for x, z in pts], FRONT)
        # plate: back, the side wall, the rounded outer edge, the flat face
        er = TW_PLATE_EDGE
        prev = ring(outer, -0.5)
        for k in ((0, 4) if lite else range(5)):
            a = math.pi / 2 * k / 4
            cur = ring(offset_poly(outer, -er * (1 - math.cos(a))), pp - er + er * math.sin(a))
            ring_strip(A, prev, cur, "tw_plate")
            prev = cur
        # face to the lip: the lip rounds the face over into the horn
        lip = TW_LIP
        steps = 2 if lite else 6
        lip_rings = []
        for k in range(steps + 1):
            a = math.pi / 2 * 0.6 * k / steps            # the lip turns the face by 54 degrees
            off = lip * math.sin(a)
            dep = lip * (1 - math.cos(a))
            lip_rings.append(ring(offset_poly(mouth, lip - off), pp - dep))
        ring_strip(A, prev, lip_rings[0], "tw_plate")
        for k in range(steps):
            ring_strip(A, lip_rings[k], lip_rings[k + 1], "tw_plate")
        prev = lip_rings[-1]
        lip_end = offset_poly(mouth, lip - lip * math.sin(math.pi / 2 * 0.6))
        w0 = pp - lip * (1 - math.cos(math.pi / 2 * 0.6))
        # the horn: a quadratic curve in (inward fraction, depth fraction) from a 40-degree wall at the lip
        # to a steep wall at the ribbon's frame (P0 = (0, 0), P1 = (0.62, 0.30), P2 = (1, 1))
        hs = 4 if lite else 18
        for k in range(1, hs + 1):
            u = k / hs
            f = 2 * (1 - u) * u * 0.62 + u * u
            g = 2 * (1 - u) * u * 0.30 + u * u
            pts = [(lx + (tx - lx) * f, lz + (tz_ - lz) * f) for (lx, lz), (tx, tz_) in zip(lip_end, throat)]
            cur = ring(pts, w0 - TW_DEPTH * g)
            ring_strip(A, prev, cur, "horn" if k <= hs - (1 if lite else 3) else "throat")   # the neck: matte black
            prev = cur
        A.face(prev, "throat", want=(0, -1, 0))
        wt = w0 - TW_DEPTH
        # the folded ribbon: four strips, each a row of fine vertical folds, between light metal bars
        rw, sh, gap, ns, pitch = RIBBON
        total = ns * sh + (ns - 1) * gap
        z_top = tz + total / 2
        A.box(-(rw / 2 + 0.3) * m_, (rw / 2 + 0.3) * m_, (FRONT_Y - (wt + 0.25)) * m_, (FRONT_Y - wt) * m_,
              (z_top - total - 0.3) * m_, (z_top + 0.3) * m_, "bar")              # the frame behind
        for k in range(ns):
            zt = z_top - k * (sh + gap)
            zb = zt - sh
            if lite:
                A.face(A.verts([F(-rw / 2, zb, wt + 0.5), F(rw / 2, zb, wt + 0.5), F(rw / 2, zt, wt + 0.5),
                                F(-rw / 2, zt, wt + 0.5)]), "ribbon", want=(0, -1, 0))
            else:
                nf = int(round(rw / pitch * 2))
                xs = [-rw / 2 + rw * i / nf for i in range(nf + 1)]
                ws = [wt + 0.35 + (0.7 if i % 2 else 0.0) for i in range(nf + 1)]
                bot = [A.bm.verts.new(F(x, zb, w)) for x, w in zip(xs, ws)]
                top = [A.bm.verts.new(F(x, zt, w)) for x, w in zip(xs, ws)]
                for i in range(nf):
                    A.face([bot[i], bot[i + 1], top[i + 1], top[i]], "ribbon", want=(0, -1, 0))
            if k < ns - 1:                       # the bar below this strip, rounded ends
                zc = zb - gap / 2
                A.prism(mmv(rr(rw + 0.6, gap - 0.4, (gap - 0.4) / 2, 2 if lite else 4)),
                        frame((0, (FRONT_Y - wt) * m_, zc * m_), (1, 0, 0), (0, 0, 1), (0, -1, 0)),
                        0.0, 1.6 * m_, "bar")
        # plate screws and the LED
        for x, z in TW_SCREWS:
            fr = frame(F(x, z, pp), (1, 0, 0), (0, 0, 1), (0, -1, 0))
            if not lite:
                lathe_at(A, [(3.9, -0.3), (3.9, 0.05), (3.3, 0.05), (0.0, 0.05)], fr, sseg, "port",
                         cap_start=False, cap_end=False)
            button_head(A, fr, 3.0, 0.5, sseg, "screw")
        fr = frame(F(TW_LED[0], TW_LED[1], pp), (1, 0, 0), (0, 0, 1), (0, -1, 0))
        button_head(A, fr, 0.5, 0.25, 8 if lite else 16, "led")

    def _ray_superellipse(w, h, n, cz, about, i, count):
        """Point i of `count` on the superellipse (centre (0, cz)), on the ray from `about` at angle i."""
        t = 2 * math.pi * i / count
        c, s = math.cos(t), math.sin(t)
        ax, az = about
        lo, hi = 0.0, max(w, h)
        for _ in range(40):
            mid = (lo + hi) / 2
            x, z = ax + mid * c, az + mid * s
            if abs(x / (w / 2)) ** n + abs((z - cz) / (h / 2)) ** n <= 1:
                lo = mid
            else:
                hi = mid
        return (ax + lo * c, az + lo * s)

    # -----------------------------------------------------------------------
    # rear panel: amplifier plate, heat sink comb, controls, inputs, power inlet
    # -----------------------------------------------------------------------
    def build_back(A, lite):
        pw, ph, pr, pz, pp = PLATE
        A.prism(rr(pw * m_, ph * m_, pr * m_, 3 if lite else 8), back_at(0, pz), -0.5 * m_, pp * m_, "plate")
        sseg = 8 if lite else 24
        w0 = pp

        def on(x, z, w=w0):
            return back_at(x, z, w)
        # heat sink: the light meander along the plate's edge (strokes across, joined at alternate ends)
        x0, x1, z0, z1, nst = HEATSINK
        pitch = (z1 - z0) / nst
        tk = pitch * 0.42
        for i in range(nst):
            zc = z0 + pitch * (i + 0.5)
            _rear_box(A, x0, x1, zc - tk / 2, zc + tk / 2, w0, w0 + 0.35, "alu")
            if i < nst - 1 and not lite:
                xe = (x1 - tk, x1) if i % 2 == 0 else (x0, x0 + tk)
                _rear_box(A, xe[0], xe[1], zc, zc + pitch, w0, w0 + 0.35, "alu")
        # room-adaptation buttons, voicing button, input select, level knob with its pointer
        bseg = 10 if lite else 40
        for x, z in BUTTONS + [VOICING, INPUT_SEL]:
            button_head(A, on(x, z), BUTTON_D / 2, 3.5, bseg, "knob")
        lx, lz, ld = LEVEL
        lathe_at(A, [(ld / 2, 0.0), (ld / 2, 9.0), (ld / 2 - 0.8, 11.5), (0.0, 11.8)], on(lx, lz), 20 if lite else 56,
                 "knob", cap_start=False, cap_end=True)
        if not lite:
            _rear_box(A, lx - 0.45, lx + 0.45, lz + 3.0, lz + ld / 2 - 1.2, w0 + 11.75, w0 + 11.95, "socket")
        # LEDs
        for x, z in LEDS_LIT:
            button_head(A, on(x, z), 0.75, 0.4, 4 if lite else 12, "led")
        if not lite:
            for x, z in LEDS_OFF:
                button_head(A, on(x, z), 0.75, 0.3, 12, "led_off")
        # network jack (remote control): metal shield, dark opening, the latch slot
        rx0, rx1, rz0, rz1 = RJ45
        _rear_box(A, rx0, rx1, rz0, rz1, w0, w0 + 2.0, "chrome")
        _rear_box(A, rx0 + 1.4, rx1 - 1.4, rz0 + 3.0, rz1 - 1.6, w0 + 2.0, w0 + 2.05, "port")
        if not lite:
            _rear_box(A, (rx0 + rx1) / 2 - 2.0, (rx0 + rx1) / 2 + 2.0, rz0 + 1.2, rz0 + 3.2, w0 + 2.0, w0 + 2.05, "port")
            for xx_ in (rx0 + 2.4, rx1 - 2.4):
                _rear_box(A, xx_ - 0.9, xx_ + 0.9, rz0 + 1.0, rz0 + 2.2, w0 + 2.05, w0 + 2.15, "led")
        # XLR input: round black housing, recessed face, three gold contacts, latch
        xx, xz, xd = XLR
        lathe_at(A, [(xd / 2, 0.0), (xd / 2, 2.6), (xd / 2 - 1.2, 3.2), (9.0, 3.2), (9.0, 1.2), (7.5, 1.2),
                     (7.5, 1.8), (0.0, 1.8)], on(xx, xz), 20 if lite else 56, "knob", cap_start=False, cap_end=True)
        if not lite:
            for a in (40, 140, 270):
                t = math.radians(a)
                button_head(A, on(xx + 3.6 * math.cos(t), xz + 3.6 * math.sin(t), w0 + 1.8), 1.1, 0.35, 12, "gold")
        # RCA input: chrome collar, gold ring, white insulator
        cx, cz, cdia = RCA
        lathe_at(A, [(cdia / 2, 0.0), (cdia / 2, 1.0), (cdia / 2 - 1.2, 1.0), (cdia / 2 - 1.2, 7.0),
                     (cdia / 2 - 1.8, 7.0), (cdia / 2 - 1.8, 6.0), (1.4, 6.0), (1.4, 6.2), (0.0, 6.2)],
                 on(cx, cz), 12 if lite else 40, "gold", cap_start=False, cap_end=True)
        if not lite:
            lathe_at(A, [(cdia / 2 - 1.85, 6.0), (cdia / 2 - 1.85, 6.6), (1.4, 6.6), (1.4, 6.0)], on(cx, cz), 32,
                     "socket", cap_start=False, cap_end=False)
        # power: the inlet module (pointed-end flange), its socket with three pins, fuse drawer, rocker switch
        ix0, ix1, iz0, iz1 = IEC
        izc, ch = (iz0 + iz1) / 2, 9.0
        fl = [(ix0, izc - 5), (ix0 + ch, iz0), (ix1 - ch, iz0), (ix1, izc - 5), (ix1, izc + 5), (ix1 - ch, iz1),
              (ix0 + ch, iz1), (ix0, izc + 5)]
        A.prism([(-x * m_, (z - izc) * m_) for x, z in fl], back_at(0, izc), -0.2 * m_, 1.6 * m_, "knob")
        sx0, sx1, sz0, sz1 = IEC_SOCKET
        A.prism([(-x * m_, (z - izc) * m_) for x, z in
                 [(sx0, sz0), (sx1, sz0), (sx1, sz1 - 4), (sx1 - 4, sz1), (sx0, sz1)]],
                back_at(0, izc), 1.6 * m_, 2.4 * m_, "knob")
        A.prism([(-x * m_, (z - izc) * m_) for x, z in
                 [(sx0 + 1.2, sz0 + 1.2), (sx1 - 1.2, sz0 + 1.2), (sx1 - 1.2, sz1 - 4.5), (sx1 - 4.5, sz1 - 1.2),
                  (sx0 + 1.2, sz1 - 1.2)]], back_at(0, izc), 2.4 * m_, 2.45 * m_, "port")
        if not lite:
            scx = (sx0 + sx1) / 2
            # seen from behind: the earth pin on the left (model +x), the two others on the right
            for px, pz_ in ((scx - 3.0, sz1 - 6.5), (scx + 2.5, (sz0 + sz1) / 2), (scx - 3.0, sz0 + 6.5)):
                _rear_box(A, px - 2.6, px + 2.6, pz_ - 0.8, pz_ + 0.8, w0 + 1.0, w0 + 2.45, "chrome")
            fx0, fx1, fz0, fz1 = IEC_FUSE
            _rear_box(A, fx0, fx1, fz0, fz1, w0 + 1.6, w0 + 2.5, "knob")
            fxc = (fx0 + fx1) / 2
            A.cyl(1.7 * m_, V((fxc, BACK_Y + w0 + 2.6, fz0 + 4.0)) * m_, V((fxc, BACK_Y + w0 + 2.6, fz1 - 4.0)) * m_, 16,
                  "knob")
            for zz in (fz0 + 4.0, fz1 - 4.0):
                A.cyl(2.3 * m_, V((fxc, BACK_Y + w0 + 2.6, zz - 1.2)) * m_, V((fxc, BACK_Y + w0 + 2.6, zz + 1.2)) * m_,
                      16, "knob")
        wx0, wx1, wz0, wz1 = IEC_SWITCH
        _rear_box(A, wx0, wx1, wz0, wz1, w0 + 1.6, w0 + 3.0, "knob")
        fr = back_at((wx0 + wx1) / 2, (wz0 + wz1) / 2, w0 + 3.0)
        hw_, hh_ = (wx1 - wx0) / 2 - 2.2, (wz1 - wz0) / 2 - 2.2
        # the rocker, pressed to "on": its top half stands out, the lower half sits in
        A.prism([(-hw_ * m_, 0.0), (hw_ * m_, 0.0), (hw_ * m_, hh_ * m_), (-hw_ * m_, hh_ * m_)], fr, 0.0, 2.2 * m_,
                "switch")
        A.prism([(-hw_ * m_, -hh_ * m_), (hw_ * m_, -hh_ * m_), (hw_ * m_, 0.0), (-hw_ * m_, 0.0)], fr, 0.0, 1.0 * m_,
                "switch")
        # plate screws (pan heads) and the inlet's two flange screws (the web copy leaves them to the bake)
        for x, z in ([] if lite else PLATE_SCREWS):
            button_head(A, on(x, z), 2.8, 1.1, sseg, "screw")

    def _rear_box(A, xa, xb, za, zb, wa, wb, key):
        """A box on the back: model x range, z range (mm), w = mm behind the back face."""
        A.box(min(xa, xb) * m_, max(xa, xb) * m_, (BACK_Y + wa) * m_, (BACK_Y + wb) * m_, za * m_, zb * m_, key)

    def build_feet(A, lite):
        for x, y in FOOT_AT:
            yc = (FRONT_Y + BACK_Y) / 2 + y
            lathe_at(A, [(0.0, 0.0), (FOOT_R - 0.8, 0.0), (FOOT_R, 0.6), (FOOT_R, FOOT_H + 0.3), (0.0, FOOT_H + 0.3)],
                     Matrix.Translation(V((x, yc, 0)) * m_), 12 if lite else 32, "feet", cap_start=False,
                     cap_end=False)

    # -----------------------------------------------------------------------
    # the woofer's moving part
    # -----------------------------------------------------------------------
    def build_woofer(mats, coll, parent, name, lite):
        A = Acc()
        cap, cone = WF_PROFILE
        r0, r1 = WF_SURR
        roll = []
        nroll = 6 if lite else 18
        for i in range(nroll + 1):
            t = math.pi * i / nroll
            roll.append((r0 + (r1 - r0) * (1 - math.cos(t)) / 2, -6.4 + (WF_ROLL_PEAK + 6.4) * math.sin(t)))
        # the cap's glued joint: a small raised bead where the cap meets the cone (the ring in the photos)
        bead = [(29.8, -19.6), (30.2, -19.5), (30.6, -19.62), (30.9, -19.85)]
        pts = ([(p_, "cap") for p_ in (cap if not lite else [cap[0], cap[3], cap[-1]])] +
               [(p_, "cap") for p_ in (bead if not lite else [bead[2]])] +
               [(p_, "cone") for p_ in (cone[1:] if not lite else cone[1::2])] +
               [(p_, "rubber") for p_ in roll] +
               [((r1 + 0.1, -6.6), "port"), ((r1 + 0.1, -40.0 if not lite else -20.0), "port"),
                ((0.0, -40.0 if not lite else -20.0), "port")])
        prof = [p_ for p_, _ in pts]
        keys = [k for _, k in pts][:-1]
        lathe_at(A, prof, front_at(0, WF_Z), 48 if lite else 144, keys, cap_start=False, cap_end=False)
        obj = A.finish(name, mats, coll, parent, smooth=True, angle=30)
        geo.set_origin(obj, F(0, WF_Z, 0))
        # MESHES.md: the pulse is a move along local +Z, so local +Z points out of the cone (cabinet -Y)
        obj.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))
        obj.rotation_euler = (math.pi / 2, 0.0, 0.0)
        # planar UV over the cone (local XY, mm / span + 0.5) for the stroke image
        me = obj.data
        uvl = me.uv_layers.new(name="ConeUV")
        span = CONE_TEX["span"] * m_
        for poly in me.polygons:
            for li in poly.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                uvl.data[li].uv = (co.x / span + 0.5, co.y / span + 0.5)
        return obj

    # -----------------------------------------------------------------------
    # the cabinet
    # -----------------------------------------------------------------------
    def build_cabinet(mats, coll, parent, name, lite):
        body_me, body_keys, _ = build_body(mats, lite)
        A = Acc()
        build_front(A, lite)
        build_back(A, lite)
        build_feet(A, lite)
        det_me, det_keys = acc_mesh(A, mats, bevel=None if lite else 0.0003)
        obj = merge([(body_me, body_keys), (det_me, det_keys)], name, mats, coll, parent)
        for me in (body_me, det_me):
            bpy.data.meshes.remove(me)
        return obj

    # -----------------------------------------------------------------------
    # mount 1: the desk pole with its platform (our design after the owner's photo; plan v3 heights)
    # -----------------------------------------------------------------------
    def build_pole(mats, coll, parent, name, lite, colour="pole"):
        A = Acc()
        seg = 20 if lite else 48
        top = POLE_CAB_Z - POLE_HEAD              # the pole's top
        O = Matrix.Identity(4)
        # through-desk fixing: flange and washer on the desk, rod, plate and wing knob under it
        lathe_at(A, [(0.0, 7.5), (30.0, 7.5), (32.0, 6.0), (32.0, 1.5), (0.0, 1.5)], O, seg, colour,
                 cap_start=False, cap_end=False)
        lathe_at(A, [(0.0, 1.5), (32.0, 1.5), (32.0, 0.0), (0.0, 0.0)], O, seg, "pad", cap_start=False, cap_end=False)
        if not lite:
            lathe_at(A, [(0.0, -DESK_T), (6.0, -DESK_T), (6.0, -DESK_T - 38.0), (0.0, -DESK_T - 38.0)], O, 16,
                     "chrome", cap_start=False, cap_end=False)
            A.prism(rr(0.07, 0.07, 0.008, 6), frame((0, 0, (-DESK_T - 5.0) * m_), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                    0.0, 5.0 * m_, colour)
            lathe_at(A, [(0.0, -DESK_T - 22.0), (14.0, -DESK_T - 22.0), (15.0, -DESK_T - 26.0), (9.0, -DESK_T - 32.0),
                         (0.0, -DESK_T - 32.0)], O, 24, colour, cap_start=False, cap_end=False)
            A.box(-26 * m_, 26 * m_, -3 * m_, 3 * m_, (-DESK_T - 30.0) * m_, (-DESK_T - 23.0) * m_, colour)
        # pole
        lathe_at(A, [(0.0, 7.0), (POLE_R, 7.0), (POLE_R, top - 1.0), (POLE_R - 1.0, top), (0.0, top)], O, seg,
                 colour, cap_start=False, cap_end=False)
        # head: collar with its lock knob, a boss, the platform, the rubber pad
        lathe_at(A, [(0.0, top - 46.0), (24.0, top - 46.0), (25.0, top - 44.0), (25.0, top - 2.0), (23.0, top),
                     (0.0, top)], O, seg, colour, cap_start=False, cap_end=False)
        A.cyl(5.0 * m_, V((25.0, 0, top - 24.0)) * m_, V((40.0, 0, top - 24.0)) * m_, 16, colour)
        A.cyl(9.0 * m_, V((40.0, 0, top - 24.0)) * m_, V((48.0, 0, top - 24.0)) * m_, 24, "pad")
        lathe_at(A, [(0.0, top), (21.0, top), (21.0, top + 12.0), (0.0, top + 12.0)], O, seg, colour,
                 cap_start=False, cap_end=False)
        pw, pd, pr = POLE_PLATE
        fz = frame((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
        A.prism(rr(pw * m_, pd * m_, pr * m_, 4 if lite else 10), fz, (top + 12.0) * m_, (top + 18.0) * m_, colour)
        A.prism(rr((pw - 8) * m_, (pd - 8) * m_, (pr - 4) * m_, 4 if lite else 10), fz, (top + 18.0) * m_,
                POLE_CAB_Z * m_, "pad")
        return A.finish(name, mats, coll, parent, bevel=None if lite else 0.0008)

    # -----------------------------------------------------------------------
    # mount 2: IsoAcoustics ISO-155 (short), black
    # -----------------------------------------------------------------------
    def build_iso(mats, coll, parent, name, lite, tall=False):
        A = Acc()
        seg = 10 if lite else 40
        SWEEP_SEG[0] = 1 if lite else 0
        Hh = ISO_H_TALL if tall else ISO_H_SHORT
        foot_h, cup_h = 24.0, 26.0
        cup_z0 = Hh - cup_h
        px, py = ISO_POST
        posts = [(sx * px, sy * py) for sx in (-1, 1) for sy in (-1, 1)]
        for x, y in posts:
            O = Matrix.Translation(V((x, y, 0)) * m_)
            # foot, isolator, rod, isolator, cup with its rubber top
            lathe_at(A, [(0.0, 0.0), (ISO_FOOT_R - 1.0, 0.0), (ISO_FOOT_R, 1.5), (ISO_FOOT_R, foot_h - 1.5),
                         (ISO_FOOT_R - 1.5, foot_h), (0.0, foot_h)], O, seg, "iso", cap_start=False, cap_end=False)
            lathe_at(A, [(0.0, foot_h), (11.5, foot_h), (11.5, foot_h + 5.0), (0.0, foot_h + 5.0)], O, seg,
                     "iso_rubber", cap_start=False, cap_end=False)
            lathe_at(A, [(0.0, foot_h + 5.0), (7.0, foot_h + 5.0), (7.0, cup_z0 - 5.0), (0.0, cup_z0 - 5.0)], O, seg,
                     "iso_rod", cap_start=False, cap_end=False)
            lathe_at(A, [(0.0, cup_z0 - 5.0), (11.5, cup_z0 - 5.0), (11.5, cup_z0), (0.0, cup_z0)], O, seg,
                     "iso_rubber", cap_start=False, cap_end=False)
            lathe_at(A, [(0.0, cup_z0), (ISO_CUP_R - 1.5, cup_z0), (ISO_CUP_R, cup_z0 + 1.5),
                         (ISO_CUP_R, Hh - 2.0), (ISO_CUP_R - 1.0, Hh - 1.0), (ISO_CUP_R - 2.5, Hh - 1.0),
                         (ISO_CUP_R - 2.5, Hh - 1.6), (0.0, Hh - 1.6)], O, seg, "iso", cap_start=False, cap_end=False)
            lathe_at(A, [(0.0, Hh - 1.6), (ISO_CUP_R - 2.6, Hh - 1.6), (ISO_CUP_R - 2.6, Hh), (0.0, Hh)], O,
                     seg, "iso_rubber", cap_start=False, cap_end=False)
        n = 5 if lite else 24
        # top frame: side rails cup to cup (slightly bowed out), short rails arched out, the oval ring, braces
        zt = cup_z0 + 13.0
        for sx in (-1, 1):
            path = [(sx * (px + 1.5 * math.sin(math.pi * i / n)), -py + 2 * py * i / n, zt) for i in range(n + 1)]
            sweep(A, path, 8.0, 12.0, "iso")
        for sy in (-1, 1):
            path = [(-px + 2 * px * i / n, sy * (py + 6.0 * math.sin(math.pi * i / n)), zt) for i in range(n + 1)]
            sweep(A, path, 8.0, 12.0, "iso")
        ring = [(57.0 * math.cos(2 * math.pi * i / (2 * n)), 79.0 * math.sin(2 * math.pi * i / (2 * n)), zt - 1.0)
                for i in range(2 * n + 1)]
        sweep(A, ring, 6.0, 10.0, "iso")
        for x, y in posts:
            sweep(A, [(x * 0.92, y * 0.92, zt), (x * 0.78, y * 0.84, zt - 0.5)], 7.0, 10.0, "iso")
        # bottom frame: rails between the feet, bowed in and arched up
        zb = 9.0
        for sx in (-1, 1):
            path = [(sx * (px - 10.0 * math.sin(math.pi * i / n)), -py + 2 * py * i / n,
                     zb + 7.0 * math.sin(math.pi * i / n)) for i in range(n + 1)]
            sweep(A, path, 10.0, 9.0, "iso")
        for sy in (-1, 1):
            path = [(-px + 2 * px * i / n, sy * (py - 14.0 * math.sin(math.pi * i / n)),
                     zb + 9.0 * math.sin(math.pi * i / n)) for i in range(n + 1)]
            sweep(A, path, 10.0, 9.0, "iso")
        SWEEP_SEG[0] = 0
        return A.finish(name, mats, coll, parent, bevel=None if lite else 0.0008)

    # -----------------------------------------------------------------------
    # the component
    # -----------------------------------------------------------------------
    def build(collection=None, parent=None, lite=False, finish="white", mount="pole", suffix="", pole_colour="pole"):
        """Returns the root empty `speakers` (+suffix). mount: 'pole' (plan v3) or 'iso' sets where the
        cabinets stand; both mounts are always built (the other one is hidden)."""
        mats = make_materials(finish)
        if collection is None:
            r, collection = geo.root("speakers" + suffix)
        else:
            r = bpy.data.objects.new("speakers" + suffix, None)
            collection.objects.link(r)
            names.set_name(r, "speakers" + suffix, data=False)
        r.parent = parent
        parts = {}
        # speaker 01 is built; speaker 02 shares its meshes (a matched pair; the GLB stores them once)
        n1 = "studio_speaker_01"
        first = {"": build_cabinet(mats, collection, r, n1 + suffix, lite)}
        first["_woofer"] = build_woofer(mats, collection, first[""], n1 + "_woofer" + suffix, lite)
        first["_pole"] = build_pole(mats, collection, r, n1 + "_pole" + suffix, lite, pole_colour)
        first["_iso"] = build_iso(mats, collection, r, n1 + "_iso" + suffix, lite)
        for i, sx in enumerate((-1, 1)):
            nn = f"studio_speaker_{i + 1:02d}"
            objs = {}
            for k, o in first.items():
                if i == 0:
                    objs[k] = o
                    continue
                c = bpy.data.objects.new(nn + k + suffix, o.data)
                collection.objects.link(c)
                names.set_name(c, nn + k + suffix, data=False)
                c.parent = objs[""] if k == "_woofer" else r
                c.location = o.location.copy()
                c.rotation_euler = o.rotation_euler.copy()
                objs[k] = c
            for k in ("_pole", "_iso"):
                objs[k].location = (sx * PAIR_X * m_, 0, 0)
            objs[""].location = (sx * PAIR_X * m_, -(FRONT_Y + BACK_Y) / 2 * m_, cab_z(mount))
            parts.update({nn + k: o for k, o in objs.items()})
        # the brand on each tweeter plate (speaker 02 shares speaker 01's decal mesh, like the cabinet)
        b1 = brands.decal("speakers", parent=parts["studio_speaker_01"],
                          at=(0.0, (FRONT_Y - TW_PLATE[3]) * m_, BRAND["z"] * m_), normal=(0, -1, 0), up=(0, 0, 1),
                          height=BRAND["height"] * m_, finish="printed", colour=BRAND["colour"],
                          collection=collection, lite=lite,
                          name="a7v_1_brand" + suffix)
        names.set_name(b1, "a7v_1_brand" + suffix, data=False)
        b2 = bpy.data.objects.new("a7v_2_brand" + suffix, b1.data)
        collection.objects.link(b2)
        names.set_name(b2, "a7v_2_brand" + suffix, data=False)
        b2.parent = parts["studio_speaker_02"]
        parts["a7v_1_brand"], parts["a7v_2_brand"] = b1, b2
        set_mount(r, mount, suffix)
        r["parts"] = list(parts)
        return r

    def cab_z(mount):
        return (POLE_CAB_Z if mount == "pole" else ISO_H_SHORT) * m_

    def set_mount(root, mount, suffix=""):
        for i in (1, 2):
            nn = f"studio_speaker_{i:02d}"
            bpy.data.objects[nn + suffix].location.z = cab_z(mount)
            for k, on in (("_pole", mount == "pole"), ("_iso", mount == "iso")):
                o = bpy.data.objects[nn + k + suffix]
                o.hide_render = o.hide_viewport = not on

    def check(root):
        probs = []
        for o in [root] + names.descendants(root):
            if not names.NAME_RE.match(o.name):
                probs.append(f"bad name {o.name}")
            if o.type == "MESH" and o.data.name == o.name and o.data.users == 1:
                probs.append(f"mesh data named like {o.name}")
            if o.type == "MESH" and tuple(round(s, 6) for s in o.scale) != (1.0, 1.0, 1.0):
                probs.append(f"scale on {o.name}")
        cab = bpy.data.objects.get("studio_speaker_01")
        if cab is not None:
            vs = [v.co for v in cab.data.vertices]
            dims = [round((max(c[k] for c in vs) - min(c[k] for c in vs)) / m_, 1) for k in range(3)]
            body = [v for v in vs if v.y > (FRONT_Y + 0.5) * m_ and v.y < BACK_Y * m_ + 1e-6]
            bd = [round((max(c[k] for c in body) - min(c[k] for c in body)) / m_, 1) for k in range(3)]
        else:
            dims = bd = None
        if probs:
            raise AssertionError("speakers: " + "; ".join(probs))
        tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons)
                for o in names.descendants(root) if o.type == "MESH"}
        return {"parts": len(tris), "triangles_before_bevels": sum(tris.values()), "per_part": tris,
                "cabinet_bbox_mm_xyz": dims, "body_bbox_mm_xyz": bd}
