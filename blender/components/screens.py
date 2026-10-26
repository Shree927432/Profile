"""screens: the AI lab's two stacked screens on one white pole (component, 2026-10-24).

As in the owner's photo docs/moodboard/local/ai-desk-reference-1.jpg:
  bottom  Samsung Odyssey OLED G8 (G85SD) 34-inch, 1800R, silver back, hung on the pole by VESA 100
          (its own slab stand is built too, as an optional hidden part `rig_stand`)
  top     Apple Studio Display 27-inch, VESA mount adapter version, silver aluminium
  pole    a white desk-clamp pole with two tilt/swivel VESA arms
  light   BenQ ScreenBar Halo 2 (the official drawing we have is the Halo 2) on the top screen's top edge
Logos: the real makers' logos are replaced by our invented names from content/room-brands.json
(decision 2026-10-26), each where the real logo sits (add_brands below): g8_brand, sd_brand,
screenbar_brand. No other printed text.

Built from scratch, at real size, in metres, away from any room layout. Frame: Blender, front at -Y,
right at +X, Z up, the desk top at z = 0, the pole on x = 0. Every part is a child of the empty
`screens`. Part names follow scene/objects/MESHES.md (proposed in the report, not yet in MESHES.md):

  rig_display    the G8's shell, glass, hub ring and ports       (obj_rig)
  rig_screen     the G8's 21:9 picture, curved on the 1800R arc   (obj_rig, screen UV rule)
  rig_static     the G8's VESA arm and collar                     (obj_rig)
  rig_stand      the G8's own slab stand, optional, hidden        (not exported)
  monitor_body   the Studio Display: aluminium body, glass, VESA adapter (obj_monitor)
  monitor_screen the posts canvas, 16:10, 53.8 x 33.6 cm           (obj_monitor, screen UV rule)
  monitor_static the Studio Display's VESA arm and collar          (obj_monitor)
  desk_pole      the pole and its desk clamp                       (set_desk)
  desk_screenbar the light bar, its arm and rear clamp             (set_desk)
  desk_screenbar_dial  the bar's round wireless dial, on the desk  (set_desk, proposed)

Numbers: OFFICIAL = maker's page or drawing; MEASURED = from the official photos in
docs/moodboard/local/ (method in video-local/footage/2026-10-24-components/screens/NOTE.md);
EST = estimated. The profile functions below are plain Python so the blueprint can draw them.
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
# Samsung Odyssey OLED G8 G85SD (34-inch, 3440 x 1440)
# ---------------------------------------------------------------------------
G8_W = 813.6 * MM          # OFFICIAL: chord width, Samsung dimension graphic (02-main-screen)
G8_H = 363.5 * MM          # OFFICIAL (retailers citing Samsung): height without stand
G8_DEPTH = 128.1 * MM      # OFFICIAL: depth without stand, front of the curved edges to the back of the hub
G8_R = 1800 * MM           # OFFICIAL: 1800R
G8_SAG = G8_R - math.sqrt(G8_R ** 2 - (G8_W / 2) ** 2)          # 46.6 mm, centre behind the edges
G8_S = G8_R * math.asin(G8_W / 2 / G8_R)                        # half the arc length, 410.2 mm
G8_EDGE_T = 3.9 * MM       # MEASURED: the panel at its edges, top-view photo g8-05 (9 px at 0.436 mm/px)
G8_RIM = 1.6 * MM          # MEASURED g8-01 (round 2): the silver lip round the top and sides, 3.5 px at 0.465 mm/px
G8_RIM_BOTTOM = 2.5 * MM   # MEASURED g8-01 (round 2): the silver strip along the bottom is wider, about 5 px
G8_ACT_W = 797.0 * MM      # COMPUTED: 34-inch 21:9 active width (arc); MESHES.md rig_screen 79.7 cm
G8_ACT_H = 333.4 * MM      # COMPUTED: active height; MESHES.md 33.4 cm
G8_BEZEL_TOP = 10.0 * MM   # MEASURED ratio: top border : chin = 1 : 2 in g8-01; total from the official sizes
G8_ACT_Z0 = G8_H - G8_BEZEL_TOP - G8_ACT_H                       # 20.1 mm chin
G8_D0 = 50.8 * MM          # MEASURED: shell depth behind the centre of the glass (side photo ratio + official depth)
# The shell's thickness across the width, from the panel front, top-view photo g8-05 (0.436 mm/px). (x mm, T mm)
G8_T_TABLE = [(0, 50.8), (40, 50.2), (80, 47.8), (120, 43.6), (137, 40.5), (155, 37.9), (172, 36.2), (189, 34.0),
              (207, 31.8), (224, 29.6), (242, 27.0), (259, 24.0), (276, 20.9), (294, 18.3), (311, 15.3),
              (329, 12.2), (346, 8.7), (363, 6.1), (381, 4.8), (398, 4.2), (406.8, 3.9)]
# The shell's profile down the height, side photo g8-08 normalised: (fraction from the top, 0..1 of T)
# Round 2b: the same side profile eased 8 % in the upper middle and 12 % in the lower middle, from the side shot
# g8-08 matched with a free camera (distance, height, sideways offset, turn; stand included): there the round-1
# shell stood 4 to 10 mm proud of the photo's outline in those two bands while the top shoulder already matched.
G8_G_TABLE = [(0.0, 0.000), (0.0117, 0.120), (0.0313, 0.256), (0.0508, 0.379), (0.0703, 0.488), (0.0898, 0.582),
              (0.1094, 0.654), (0.1289, 0.710), (0.1484, 0.740), (0.168, 0.767), (0.1875, 0.786), (0.207, 0.808),
              (0.2266, 0.824), (0.246, 0.832), (0.285, 0.840), (0.324, 0.862), (0.363, 0.896), (0.402, 0.933),
              (0.441, 0.964), (0.48, 0.977), (0.52, 0.984), (0.559, 0.991), (0.598, 1.000), (0.637, 0.980),
              (0.68, 0.933), (0.72, 0.897), (0.773, 0.891), (0.793, 0.885), (0.8125, 0.879), (0.832, 0.873),
              (0.8516, 0.868), (0.871, 0.864), (0.8906, 0.850), (0.91, 0.799), (0.9297, 0.695), (0.949, 0.556),
              (0.969, 0.387), (0.9785, 0.297), (0.988, 0.192), (0.998, 0.075), (1.0, 0.000)]
# The hub (the round "core lighting" ring the stand or VESA arm fixes to). Round 2 (2026-10-24): rebuilt as
# the real one is, a black rim, a flat lit ring, then a smoked trumpet that narrows to a small round back
# (gallery g8-02/03 brightness profiles through the centre at 0.4355 mm/px; g8-05 top; g8-07 three-quarter).
G8_HUB_ZC = G8_H - 180 * MM    # MEASURED: centre 180 mm below the top (round 1, camera fit on g8-02)
G8_HUB_R = 133 * MM            # MEASURED g8-03: outer radius of the black rim (306 px)
G8_HUB_RIM_IN = 116.7 * MM     # MEASURED g8-03: the rim is 16.3 mm wide (36 px), then the light ring starts
G8_HUB_STEP_R = 91.0 * MM      # MEASURED g8-02/03: the light ring ends at a small step (210 px), the trumpet starts
G8_HUB_BACK_R = 58 * MM        # MEASURED g8-05 top (102 to 110 across, perspective) and g8-07 (116 across): the lip
G8_HUB_BACK_Y = G8_DEPTH - G8_SAG   # 81.5 mm behind the centre of the glass: the official 128.1 depth
G8_HUB_RIM_Y = 47.5 * MM       # MEASURED round 2b (side shot, free camera): the rim's face 7 mm nearer the glass than
                               # round 1, so the trumpet stands out longer (g8-07)
G8_HUB_LIGHT_Y = (48.0 * MM, 50.5 * MM)   # EST: the lit ring, a shallow cone from the rim to the step
G8_HUB_FUNNEL_Y0 = 52.0 * MM   # EST: where the trumpet starts, behind the step
G8_HUB_FUNNEL_P = 1.5          # EST round 2b: the trumpet's flare, a long smoky cone (g8-07, g8-08; 2.6 read as a bulb)
G8_HUB_RECESS = 3.0 * MM       # EST: the dark back inside the lip
G8_VESA = 100 * MM             # OFFICIAL: VESA 100 x 100
RING_BASE = 0.15               # the lit ring's base colour = its light x this (the lite GLB's glow undoes it)
G8_RING = "rgb"                # the ring's light: "rgb" (default, a soft colour wheel as in the photos) or "white"
# The vent slot across the top of the back (g8-02)
G8_SLOT_L, G8_SLOT_H, G8_SLOT_Z = 535 * MM, 5 * MM, G8_H - 40 * MM      # MEASURED
# The lower back panel, a trapezoid standing 0.8 mm proud (g8-02)
G8_PANEL_TOP = G8_H - 204 * MM     # MEASURED: its top edge 204 mm below the top
G8_PANEL_XT, G8_PANEL_XB = 310 * MM, 364 * MM   # MEASURED: half widths at its top and at the bottom edge
G8_PANEL_STEP = 0.8 * MM           # EST
G8_PANEL_CORNER = 15 * MM          # MEASURED: rounded top corners
# The ports: a stadium-shaped bay under the hub, ports facing back and down (g8-13 close-up, 0.34 mm/px)
G8_PORTS_W, G8_PORTS_H, G8_PORTS_Z = 150 * MM, 26 * MM, G8_H - 335 * MM   # MEASURED (height about 20% UNSURE)
# (offset along the bay from its centre as seen from behind, kind, w, h) in mm, left to right from behind:
# power (DC 24 V), DisplayPort, HDMI 1, HDMI 2, USB-B, USB-A, USB-A, the round power button. MEASURED.
G8_PORTS = [(-62.0, "dc", 9, 9), (-43.6, "dp", 7.5, 16), (-26.1, "hdmi", 5, 14), (-8.9, "hdmi", 5, 14),
            (6.9, "usbb", 8.5, 8.5), (23.4, "usba", 5.5, 12.5), (41.3, "usba", 5.5, 12.5), (60.8, "button", 13, 13)]
# Its own stand (optional part): a slab neck and a thin plate foot
G8_STAND_LOW = 522.3 * MM - G8_H   # OFFICIAL height with stand 522.3: 158.8 mm. Round 2: this is the TOP of the 120 mm
                                   # travel (g8-08/g8-09 and g8-02: neck top 74 mm above the hub at this height); the
                                   # name is kept for the callers
G8_STAND_DEPTH = 192.8 * MM        # OFFICIAL depth with stand, from the edges' front to the stand's back
G8_FOOT_AHEAD = -6 * MM            # the foot's front 6 mm behind the curved edges (round 1). Round 2b tried it 20 mm
                                   # ahead (the neck 20 mm forward), as the top view g8-05 seemed to say: g8-04 fell from
                                   # 0.970 to 0.938 and Samsung's drawing from 0.9895 to 0.9835, so it was perspective
G8_FOOT = (171 * MM, 4.5 * MM)     # MEASURED front graphic: foot width; thickness MEASURED round 2 (drawing: a 4 to 5 px
                                   # plate edge at 1.1 mm/px)
# Round 2: the neck is graphite on the front, sides and its sloped top, with a silver back plate (g8-05 top,
# g8-07, g8-08 side). Widths from g8-02 (143 / 200 px-scaled, the neck is nearer the camera than the panel).
G8_NECK = (142 * MM, 190 * MM, 22 * MM)   # MEASURED widths at the top and bottom; depth from g8-08 (bracket:neck 70:38
                                          # of the official 64.7 mm from the hub's back to the stand's back)
G8_NECK_PLATE = 2.5 * MM           # MEASURED g8-08: the silver back plate seen as a light edge from the side
G8_NECK_TOP = 74 * MM              # MEASURED g8-02: the back plate's top above the hub centre (77 px-scaled)
G8_NECK_CHAMFER = 15 * MM          # MEASURED g8-08: the top slopes down 15 mm to the front
G8_NECK_CORNER = 18 * MM           # MEASURED g8-02: rounded top corners
G8_BRACKET = (52 * MM, 30 * MM, 5 * MM)   # MEASURED g8-05 width, g8-08 height; centre 5 mm above the hub's (EST)
G8_WINDOW = (67 * MM, 22 * MM, 180 * MM)  # MEASURED g8-02: the cable window, w, h, centre above the foot

# ---------------------------------------------------------------------------
# Apple Studio Display 27-inch, VESA mount adapter version
# ---------------------------------------------------------------------------
SD_W, SD_H = 623 * MM, 362 * MM     # OFFICIAL (Apple tech specs)
SD_DEPTH = 31 * MM                  # OFFICIAL: with the VESA adapter
SD_T = 19.6 * MM                    # MEASURED round 2: Apple side diagram, adapter 16 px of the 43 px total (31 mm official)
SD_CORNER = 5.3 * MM                # MEASURED: corner radius in front-screen-off.jpg (0.254 mm/px)
SD_BACK_ROUND = 3.0 * MM            # EST: the back edge's round (hinge close-up)
SD_FRONT_ROUND = 0.5 * MM           # EST
SD_BEZEL = 13.0 * MM                # MEASURED: the black border, even on all four sides
SD_ACT_W, SD_ACT_H = 597.0 * MM, 336.0 * MM   # MEASURED; 27-inch 16:9 computes to 597.7 x 336.2
POSTS_W, POSTS_H = 538 * MM, 336 * MM          # MESHES.md: monitor_screen 16:10, 53.8 x 33.6 cm
SD_CAM_D, SD_CAM_Z = 3.0 * MM, SD_H - 5.6 * MM  # MEASURED: the camera dot
SD_GRILLE = (580 * MM, 7 * MM)      # EST from the hinge close-up: perforated band on the bottom and top faces
# The VESA mount adapter, an H plate (diagram-back-vesa-adapter.jpg, 0.706 mm/px). Below the top, in mm:
SD_H_RAIL = (18.5, 50.5, 123.5, 319.0)   # MEASURED: rail width, rail centre from the middle, rail top, rail bottom
SD_H_BAR = (261.0, 282.0)                # MEASURED: the crossbar's top and bottom
SD_H_CORNER = 6.0                        # MEASURED: inner corner radius
SD_H_T = SD_DEPTH - SD_T                 # 10.5 mm: OFFICIAL 31 less the body
SD_H_EDGE = 1.5 * MM                     # MEASURED round 2: the rounded top edge (diagram highlight bands, 3 to 4 px)
SD_H_SCREWS = (130.6, 230.6)             # MEASURED round 2: the four screws (VESA 100), mm below the top, on the rails
SD_POWER = (30.6 * MM, 11.3 * MM, SD_H - 335 * MM)  # MEASURED: the power inlet, outer, its fine inner ring (round 2b:
                                                   # 0.37 of the disc in the diagram), height
SD_PORTS_X = [172.5 * MM, 188.0 * MM, 202.9 * MM, 218.4 * MM]   # MEASURED: four USB-C slots, +X (seen from behind: left)

# ---------------------------------------------------------------------------
# BenQ ScreenBar Halo 2 (dims-diagram-inch.webp, the Halo 2 drawing, 0.252 mm/px)
# ---------------------------------------------------------------------------
HB_L = 500 * MM            # OFFICIAL: bar length
HB_DEPTH = 143.8 * MM      # OFFICIAL: bar front to clamp back
HB_HEIGHT = 109.1 * MM     # OFFICIAL: overall height
HB_TUBE = 33.4 * MM        # OFFICIAL: bar top to the pad's foot
HB_CLAMP_W = 47.4 * MM     # OFFICIAL
HB_PAD = 3.8 * MM          # OFFICIAL: the front foot pad
HB_DIAL = (74 * MM, 39.5 * MM)   # OFFICIAL: the wireless dial
HB_MAX_T = 60 * MM         # OFFICIAL: thickest monitor the clamp takes

# ---------------------------------------------------------------------------
# The pole and its arms (our design, see the report: an Ergotron/VIVO-style white pole mount)
# ---------------------------------------------------------------------------
DESK_T = 30 * MM           # decision 2026-10-23: the white L top is 3 cm
POLE_R = 17.5 * MM         # EST: 35 mm pole, the common size
POLE_H = 800 * MM          # EST: 80 cm pole, the common length
POLE_Y = 190 * MM          # EST: behind the screens, 45 mm in from the desk's back edge
DESK_BACK_Y = POLE_Y + 45 * MM
VESA_PLATE = (115 * MM, 4 * MM)  # EST: arm plate, square
G8_Z0 = 115 * MM           # EST from the owner's photo: the G8's bottom edge above the desk
STACK_GAP = 15 * MM        # EST from the owner's photo
SD_Y = 0.0                 # the top screen's glass in the G8's centre plane, as in the photo
HALO_ON = "top"            # "top" as in the owner's photo; "bottom" was asked for, rendered as option B
HALO_BOTTOM_GAP = 45 * MM  # with the bar on the G8, the top screen goes up to clear it
DIAL_AT = (300 * MM, -230 * MM)  # the dial on the desk, right of the screens (layout is the room's call)


def sd_z0(halo_on=HALO_ON):
    return G8_Z0 + G8_H + (HALO_BOTTOM_GAP if halo_on == "bottom" else STACK_GAP)


# ---------------------------------------------------------------------------
# Profile maths (no Blender)
# ---------------------------------------------------------------------------
def _pchip(table, x):
    """Monotone cubic through a (x, y) table (Fritsch-Carlson), clamped at the ends."""
    xs = [p[0] for p in table]
    ys = [p[1] for p in table]
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    k = max(i for i in range(len(xs) - 1) if xs[i] <= x)
    h = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(len(h))]

    def m(i):
        if i == 0:
            return d[0]
        if i == len(xs) - 1:
            return d[-1]
        if d[i - 1] * d[i] <= 0:
            return 0.0
        w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
        return (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    t = (x - xs[k]) / h[k]
    h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
    h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * ys[k] + h10 * h[k] * m(k) + h01 * ys[k + 1] + h11 * h[k] * m(k + 1)


def g8_T(s):
    """Shell thickness (m) from the glass at arc position s (m), at its deepest row."""
    x = abs(G8_R * math.sin(s / G8_R)) / MM
    return _pchip(G8_T_TABLE, x) * MM


def g8_G(z):
    return _pchip(G8_G_TABLE, (G8_H - z) / G8_H)


def g8_d(s, z):
    """Depth of the back from the glass, along the panel normal."""
    return G8_EDGE_T + (g8_T(s) - G8_EDGE_T) * g8_G(z)


def g8_front(s, z):
    th = s / G8_R
    return (G8_R * math.sin(th), -G8_R * (1 - math.cos(th)), z)


def g8_n(s):
    th = s / G8_R
    return (math.sin(th), math.cos(th), 0.0)


def g8_back(s, z, extra=0.0):
    f, n, d = g8_front(s, z), g8_n(s), g8_d(s, z) + extra
    return (f[0] + n[0] * d, f[1] + n[1] * d, z)


def x_to_s(x):
    return G8_R * math.asin(max(-1.0, min(1.0, x / G8_R)))


def g8_hub_profile(n=16):
    """The hub's lathe profile, from the shell outwards: [(radius m, depth behind the glass centre m)] and
    one material key per span. Black rim, the lit ring (a shallow cone), a small dark step, the smoked
    trumpet r = lip + (step - lip) * (1 - t) ** p (flat at the ring, nearly axial at the lip), the lip, then
    the dark recessed back."""
    R, Ri, Rs, Rb = G8_HUB_R, G8_HUB_RIM_IN, G8_HUB_STEP_R, G8_HUB_BACK_R
    yr, (yl0, yl1), yf, yb = G8_HUB_RIM_Y, G8_HUB_LIGHT_Y, G8_HUB_FUNNEL_Y0, G8_HUB_BACK_Y
    pts = [(R, 0.030), (R, yr - 0.002), (R - 0.0006, yr - 0.0006), (R - 0.002, yr), (Ri + 0.0008, yr),
           (Ri, yl0), (Rs + 0.0008, yl1), (Rs, yl1 + 0.0004), (Rs - 0.0005, yf)]
    keys = ["rim_black"] * 5 + ["hub_light", "black", "hub_funnel"]
    lip = yb - 0.0015
    for k in range(1, n + 1):
        t = k / n
        pts.append((Rb + (Rs - 0.0005 - Rb) * (1 - t) ** G8_HUB_FUNNEL_P, yf + (lip - yf) * t))
        keys.append("hub_funnel")
    pts += [(Rb - 0.0004, yb - 0.0002), (Rb - 0.0025, yb), (Rb - 0.0032, yb - 0.0006),
            (Rb - 0.0032, yb - G8_HUB_RECESS), (0.0, yb - G8_HUB_RECESS)]
    keys += ["hub_lip", "hub_lip", "hub_lip", "hub_back", "hub_back"]
    return pts, keys


def ring_hue(phi):
    """The ring's colour wheel as in Samsung's photos, by the angle round the hub seen from behind the
    model frame (phi from +X towards +Z, radians): +X red, top magenta, -X blue, bottom green, and between
    them yellow (lower +X) and cyan (lower -X). Returns a hue in degrees."""
    a = math.degrees(phi) % 360.0
    anchors = [(0, 360), (90, 300), (180, 232), (270, 128), (360, 0)]
    for (a0, h0), (a1, h1) in zip(anchors, anchors[1:]):
        if a <= a1:
            return (h0 + (h1 - h0) * (a - a0) / (a1 - a0)) % 360.0
    return 0.0


def halo_bar_section():
    """The bar's D section (y back, z up) in mm, origin at the monitor's top front edge."""
    c, r = (-48.0, 21.3), 12.0
    pts = [(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a)))
           for a in range(90, 216, 9)]
    pts += [(-37.2, 12.9), (-35.0, 14.4), (-34.5, 16.5), (-34.5, 31.0), (-35.3, 32.7), (-37.0, 33.3)]
    return pts


HALO_ARM = [(-36.0, 31.5), (1.3, 21.9), (60.5, 21.9), (60.5, 7.6), (1.3, 7.6), (-34.5, 14.5)]
HALO_HINGE = (75.0, -1.0)

# Brand spots (decision 2026-10-26: invented names where the real logos sit, content/room-brands.json).
# G8: Samsung's word sits on a small dark tab just under the panel's bottom edge, centred (g8-01, 0.465 mm/px:
# letters 4.5 px = 2.1 mm tall, the word 36 px = 16.6 mm wide, light grey pad print). We have no tab, so the
# name sits on the black chin straight above it, just over the silver bottom strip.
BRAND_G8 = dict(z=6.0 * MM, height=2.1 * MM, max_width=16.6 * MM, colour="#a3a5a8", finish="printed")
# Studio Display: Apple's mark, centred between the adapter rails (diagram-back-vesa-adapter, 0.705 mm/px:
# 68 x 85 mm, its body's centre 134 mm below the top), polished. Ours: a plain ring, 70 mm across.
BRAND_SD = dict(below_top=134 * MM, height=70 * MM, colour="#dcdee1", finish="polished")
# ScreenBar Halo: BenQ's word, tone on tone, on the user-facing face of the rear block above the arm
# (three-quarter-bar-with-controller: about 10 mm wide, letters about 2.5 mm). The block face is y = 60.5 mm.
BRAND_HALO = dict(y=60.5, z=34.0 * MM, height=2.5 * MM, max_width=10.8 * MM, colour="#3a3c40", finish="engraved")
HALO_WEIGHT = [(-18.8, 0.0), (5.6, 0.0), (4.0, -48.0), (1.5, -53.5), (-3.0, -55.7), (-14.0, -55.7),
               (-17.8, -53.0), (-18.8, -49.0)]


def halo_fit(t_mm):
    """How the clamp sits on a monitor t_mm thick at the top (mm). The drawing shows a toothed rail under
    the arm: the foot pad slides on it, the rear block and its hanging weight stay square, the weight's
    front face (56.2 mm behind the pad's front at full opening) rests on the monitor's back. So the bar
    stands further forward on a thin monitor. Returns, in mm, the bar frame's offset from the monitor's
    top front edge along Y, and the pad's start and end in the bar frame (where that edge sits at -offset). EST: the mechanism is read from the drawing."""
    off = t_mm - 56.2
    pad0 = -off
    return off, pad0, pad0 + min(31.5, t_mm + 4.0)


# ---------------------------------------------------------------------------
# Blender side
# ---------------------------------------------------------------------------
if bpy is not None:
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from lib import brands, geo, materials as M, names  # noqa: E402

    V = Vector
    _SFX = [""]          # name suffix while a lite copy is built next to the rich one

    def nm(n):
        return n + _SFX[0]

    class Acc:
        """Accumulates pieces into one mesh, one material slot per key."""

        def __init__(self):
            self.bm = bmesh.new()
            self.keys = []
            self.closed = []

        def mi(self, key):
            if key not in self.keys:
                self.keys.append(key)
            return self.keys.index(key)

        def verts(self, pts, mat=None):
            return [self.bm.verts.new(mat @ V(p) if mat is not None else V(p)) for p in pts]

        def face(self, vs, key, want=None, closed=False):
            f = self.bm.faces.new(vs)
            f.material_index = self.mi(key)
            if want is not None:
                f.normal_update()
                if f.normal.dot(V(want)) < 0:
                    f.normal_flip()
            if closed:
                self.closed.append(f)
            return f

        def grid(self, P, key, want=None, keyfn=None, uv=None):
            """P[j][i]: rows of points. want(i, j) -> direction the face should face."""
            vs = [self.verts(row) for row in P]
            fs = []
            for j in range(len(P) - 1):
                for i in range(len(P[0]) - 1):
                    k = keyfn(i, j) if keyfn else key
                    f = self.face([vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]], k,
                                  want(i, j) if want else None)
                    fs.append(f)
            return vs, fs

        def strip(self, a, b, key, want=None, closed_loop=False, solid=False):
            n = len(a)
            rng = range(n) if closed_loop else range(n - 1)
            for i in rng:
                j = (i + 1) % n
                self.face([a[i], a[j], b[j], b[i]], key, want(i) if want else None, closed=solid)

        def prism(self, outline, frame, w0, w1, key, cap_key=None, cap0_key=None):
            """Extrude a 2D outline (u, v) along w. frame: Matrix whose columns are u, v, w and origin."""
            a = self.verts([(u, v, w0) for u, v in outline], frame)
            b = self.verts([(u, v, w1) for u, v in outline], frame)
            self.strip(a, b, key, closed_loop=True, solid=True)
            self.face(list(reversed(a)), cap0_key or cap_key or key, closed=True)
            self.face(b, cap_key or key, closed=True)
            return a, b

        def lathe(self, prof, frame, seg, keys, cap_start=True, cap_end=True):
            """prof: [(r, a)] along the axis (local z of frame); keys: one key or one per span."""
            rings = []
            for r, a in prof:
                rings.append(self.verts([(r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), a)
                                         for k in range(seg)], frame) if r > 1e-7 else
                             self.verts([(0, 0, a)], frame))
            for i in range(len(rings) - 1):
                key = keys if isinstance(keys, str) else keys[i]
                ra, rb = rings[i], rings[i + 1]
                if len(ra) == 1 or len(rb) == 1:
                    c, ring = (ra[0], rb) if len(ra) == 1 else (rb[0], ra)
                    for k in range(seg):
                        vs = [c, ring[k], ring[(k + 1) % seg]] if len(ra) == 1 else [ring[k], ring[(k + 1) % seg], c]
                        self.face(vs, key, closed=True)
                else:
                    self.strip(ra, rb, key, closed_loop=True, solid=True)
            last = keys if isinstance(keys, str) else keys[-1]
            first = keys if isinstance(keys, str) else keys[0]
            if cap_start and len(rings[0]) > 1:
                self.face(list(reversed(rings[0])), first, closed=True)
            if cap_end and len(rings[-1]) > 1:
                self.face(rings[-1], last, closed=True)

        def cyl(self, r, p0, p1, seg, key, cap_keys=None):
            p0, p1 = V(p0), V(p1)
            d = p1 - p0
            rot = V((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
            frame = Matrix.Translation(p0) @ rot
            self.lathe([(r, 0.0), (r, d.length)], frame, seg, key)

        def box(self, x0, x1, y0, y1, z0, z1, key):
            self.prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], Matrix.Identity(4), z0, z1, key)

        def finish(self, name, mats, collection, parent, smooth=True, angle=35, bevel=None):
            bm = self.bm
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
            if self.closed:
                fs = [f for f in self.closed if f.is_valid]
                bmesh.ops.recalc_face_normals(bm, faces=fs)
            me = bpy.data.meshes.new(name + "_mesh")
            bm.to_mesh(me)
            bm.free()
            for k in self.keys:
                me.materials.append(mats[k])
            name = nm(name)
            me.name = name + "_mesh"
            obj = bpy.data.objects.new(name, me)
            collection.objects.link(obj)
            obj.parent = parent
            names.set_name(obj, name)
            if smooth:
                me.shade_smooth()
                me.set_sharp_from_angle(angle=math.radians(angle))
            if bevel:
                geo.bevel(obj, bevel, segments=2, angle=40)
            return obj

    def frame(origin, u, v, w):
        m = Matrix.Identity(4)
        for i, vec in enumerate((u, v, w)):
            for r in range(3):
                m[r][i] = vec[r]
        m.translation = V(origin)
        return m

    def stadium(w, h, n=8):
        r = h / 2
        return geo.rounded_rect(w, h, min(r, w / 2) - 1e-6, n=n)

    def rr(w, h, r, n=4):
        return geo.rounded_rect(w, h, max(1e-5, min(r, w / 2 - 1e-6, h / 2 - 1e-6)), n=n)

    # -----------------------------------------------------------------------
    # materials
    # -----------------------------------------------------------------------
    def _bead(m, scale=3000.0, strength=0.04):
        nt = m.node_tree
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        M._bump(nt, b, M._noise(nt, M._coords(nt), scale, detail=2), strength, 0.0002)
        return m

    def _perforated(name):
        """Aluminium with a fine grid of dark holes (Studio Display grilles), object coords."""
        m, nt, b = M._new(name)
        mp = M._coords(nt, scale=(1 / 0.0011, 1 / 0.0011, 1 / 0.0011))
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.feature = "F1"
        vor.inputs["Randomness"].default_value = 0.0
        nt.links.new(mp, vor.inputs["Vector"])
        mask = M._math(nt, "LESS_THAN", vor.outputs["Distance"], 0.28)
        col = M._ramp(nt, mask, [(0.0, "#c3c4c6"), (1.0, "#0b0b0c")])
        nt.links.new(col, b.inputs["Base Color"])
        rough = M._ramp(nt, mask, [(0.0, (0.35, 0.35, 0.35, 1)), (1.0, (0.9, 0.9, 0.9, 1))])
        nt.links.new(rough, b.inputs["Roughness"])
        met = M._ramp(nt, mask, [(0.0, (1, 1, 1, 1)), (1.0, (0, 0, 0, 1))])
        nt.links.new(met, b.inputs["Metallic"])
        m.diffuse_color = M.rgba("#8a8b8d")
        return m

    def ring_image(mode=None, w=256, h=32):
        """The ring's light as a small image on the hub's own UVs (UVHub): U = the angle round the hub, V =
        0..0.25 the lit ring (brighter towards its inner edge, as in g8-02), 0.3..1 the trumpet from its base
        to the lip (fading). mode "rgb": the soft colour wheel of Samsung's photos; "white": a neutral white."""
        import colorsys
        import numpy as np
        mode = mode or G8_RING
        name = f"screens_ring_{mode}"
        img = bpy.data.images.get(name) or bpy.data.images.new(name, w, h)
        px = np.ones((h, w, 4), np.float32)
        for i in range(w):
            if mode == "white":
                c = (0.92, 0.94, 1.0)
            else:
                c = colorsys.hsv_to_rgb(ring_hue(2 * math.pi * (i + 0.5) / w) / 360.0, 1.0, 1.0)
            for j in range(h):
                v = (j + 0.5) / h
                if v < 0.27:
                    k = 0.45 + 0.55 * (v / 0.27) ** 1.5           # the lit ring, outer edge to inner
                else:
                    t = min(1.0, max(0.0, (v - 0.3) / 0.7))
                    k = 0.85 - 0.5 * t ** 1.3                      # the trumpet glows nearly as the ring (g8-02)
                px[j, i, :3] = [ch * k ** (1 / 2.2) for ch in c]    # sRGB image, k a linear brightness
        img.pixels.foreach_set(px.ravel())
        img.pack()
        return img

    def _uv_image(nt, img):
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = "UVHub"
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = img
        tx.extension = "REPEAT"
        nt.links.new(uvn.outputs["UV"], tx.inputs["Vector"])
        return tx

    def _hub_light(name, mode=None):
        """The lit ring: the ring image as both colour and light (exports as a glTF emissive texture)."""
        m, nt, b = M._new(name)
        M._set(b, rough=0.6, emit_strength=1.1)
        tx = _uv_image(nt, ring_image(mode))
        # the colour itself dimmed (a light reflects little); a bright base under the studio washes it out
        dim = nt.nodes.new("ShaderNodeMix")
        dim.data_type, dim.blend_type = "RGBA", "MULTIPLY"
        dim.inputs["Factor"].default_value = 1.0
        nt.links.new(tx.outputs["Color"], dim.inputs[6])                 # the colour sockets: A 6, B 7, Result 2
        dim.inputs[7].default_value = (RING_BASE, RING_BASE, RING_BASE, 1.0)
        nt.links.new(dim.outputs[2], b.inputs["Base Color"])
        nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"])
        m.diffuse_color = M.rgba("#c070d0" if (mode or G8_RING) == "rgb" else "#e8eeff")
        return m

    def _hub_funnel(name, mode=None):
        """The smoked trumpet: dark glossy plastic carrying the ring's glow, fading to the lip."""
        m, nt, b = M._new(name)
        M._set(b, base="#07080b", rough=0.18, spec=0.4, coat=0.3, coat_rough=0.1, emit_strength=0.9)
        tx = _uv_image(nt, ring_image(mode))
        nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"])
        m.diffuse_color = M.rgba("#1a1424")
        return m

    def set_ring(mode):
        """Switch the ring between "rgb" and "white" on the built materials (the option still)."""
        img = ring_image(mode)
        for n in ("mat_screens_g8_hub_light", "mat_screens_g8_hub_funnel"):
            mat = bpy.data.materials.get(n)
            if mat:
                for nd in mat.node_tree.nodes:
                    if nd.type == "TEX_IMAGE":
                        nd.image = img

    def placeholder_image(name, w, h):
        """Neutral dark blue: a soft vertical gradient and a faint glow, no UI, no logo."""
        import numpy as np
        img = bpy.data.images.get(name) or bpy.data.images.new(name, w, h)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        v = yy / (h - 1)              # Blender row 0 is the bottom of the picture
        u = xx / (w - 1)
        top, bot = np.array([0.020, 0.045, 0.105]), np.array([0.008, 0.018, 0.048])
        col = bot[None, None, :] * (1 - v[..., None]) + top[None, None, :] * v[..., None]
        glow = np.exp(-(((u - 0.5) / 0.45) ** 2 + ((v - 0.62) / 0.55) ** 2))[..., None]
        col = col + glow * np.array([0.010, 0.022, 0.050])[None, None, :]
        px = np.ones((h, w, 4), np.float32)
        px[..., :3] = col
        img.pixels.foreach_set(px.ravel())
        img.pack()
        return img

    def make_materials():
        p = M.principled
        mats = {
            "alu": _bead(p("mat_screens_sd_alu", base="#c4c6c9", metal=0.75, rough=0.45)),
            "glass_sd": p("mat_screens_sd_glass", base="#040405", rough=0.03, spec=0.5, coat=1.0, coat_rough=0.01),
            # round 2: the inactive glass is the same black glass as the border (no band round the posts area)
            # (Apple's screen-off photo: the active area a touch lighter than the border, #1e vs #11 in the photo)
            "off_sd": p("mat_screens_sd_off", base="#151617", rough=0.03, spec=0.5, coat=1.0, coat_rough=0.01),
            "perf": _perforated("mat_screens_sd_perforated"),
            "shell": _bead(p("mat_screens_g8_shell", base="#c6c8cb", metal=0.55, rough=0.48), 2200, 0.05),
            "seam": p("mat_screens_g8_seam", base="#6e7176", rough=0.6, metal=0.3),
            "glass_g8": p("mat_screens_g8_glass", base="#060708", rough=0.24, spec=0.45),
            "black": p("mat_screens_black_plastic", base="#0d0e0f", rough=0.32, spec=0.5),
            "hub_light": _hub_light("mat_screens_g8_hub_light"),
            "hub_funnel": _hub_funnel("mat_screens_g8_hub_funnel"),
            "hub_lip": p("mat_screens_g8_hub_lip", base="#3c3f44", rough=0.4, metal=0.4),
            "rim": p("mat_screens_g8_rim", base="#d4d6d9", metal=0.3, rough=0.35),
            "rim_black": p("mat_screens_g8_hub_rim", base="#09090a", rough=0.5, spec=0.4),
            "sd_inlet": p("mat_screens_sd_inlet", base="#040404", rough=0.45, spec=0.3),
            "screw": p("mat_screens_sd_screw", base="#b9bbbe", metal=0.6, rough=0.32),
            # round 2b: the H plate reads a touch brighter than the back in Apple's diagram; the back's rounded edge in a
            # light, low-metal finish so it never reads as a dark line from behind
            "alu_h": _bead(p("mat_screens_sd_alu_adapter", base="#d3d5d8", metal=0.5, rough=0.4)),
            "alu_edge": p("mat_screens_sd_alu_edge", base="#d0d2d5", metal=0.3, rough=0.45),
            "sd_ring": p("mat_screens_sd_inlet_ring", base="#0f1011", rough=0.5),
            "hub_back": p("mat_screens_g8_hub_back", base="#16171a", rough=0.5, metal=0.1),
            "window": p("mat_screens_g8_stand_window", base="#8b8e93", rough=0.5, metal=0.3),
            "port": p("mat_screens_port", base="#030303", rough=0.7),
            "chrome": M.chrome("mat_screens_chrome"),
            "white": _bead(p("mat_screens_powder_white", base="#eceeef", rough=0.48, spec=0.5), 1800, 0.08),
            "rubber": p("mat_screens_rubber", base="#18191a", rough=0.85, spec=0.3),
            "halo": _bead(p("mat_screens_halo_anodised", base="#2e3033", metal=1.0, rough=0.4), 2600, 0.04),
            "halo_plastic": p("mat_screens_halo_plastic", base="#1c1d1f", rough=0.55, spec=0.4),
            "halo_glossy": p("mat_screens_halo_glossy", base="#08090a", rough=0.06, coat=1.0, coat_rough=0.02),
            "led": M.emission("mat_screens_halo_led", "#fff3e6", 1.2),
            "led_back": M.emission("mat_screens_halo_backlight", "#f2f6ff", 0.6),
            "stand_dark": p("mat_screens_g8_stand_dark", base="#2a2b2e", rough=0.38, metal=0.35, spec=0.5),
            "stand_silver": _bead(p("mat_screens_g8_stand_silver", base="#cfd1d4", metal=1.0, rough=0.42), 2200, 0.03),
        }
        mats["led"].diffuse_color = M.rgba("#fff3e6")
        mats["led_back"].diffuse_color = M.rgba("#f2f6ff")
        mats["posts"] = M.screen_image("mat_screens_posts", placeholder_image("screens_posts_placeholder", 512, 320), 1.0)
        mats["rig"] = M.screen_image("mat_screens_rig", placeholder_image("screens_rig_placeholder", 512, 214), 1.0)
        # round 2: each picture takes its glass's own gloss, so the screen and the glass round it reflect alike
        # (no lighter or darker band round the posts area when the picture is dark)
        for k, glass in (("posts", dict(rough=0.03, coat=1.0, coat_rough=0.01)), ("rig", dict(rough=0.24))):
            b = next(n for n in mats[k].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            M._set(b, **glass)
        return mats

    # -----------------------------------------------------------------------
    # G8
    # -----------------------------------------------------------------------
    def _uniq(xs, eps=1e-6):
        out = []
        for x in sorted(xs):
            if not out or x - out[-1] > eps:
                out.append(x)
        return out

    def g8_columns(n):
        S = G8_S
        base = [-S + 2 * S * i / n for i in range(n + 1)]
        # dense towards the edges, where the shell curls in
        base = [S * math.sin(math.pi / 2 * x / S) if abs(x) > 0 else 0.0 for x in base]
        extra = [-S + G8_RIM, S - G8_RIM, -G8_ACT_W / 2, G8_ACT_W / 2]
        return _uniq(base + extra)

    def g8_rows(n, a=0.75):
        out = []
        for i in range(n + 1):
            t = i / n
            out.append(G8_H * (t - a * math.sin(2 * math.pi * t) / (2 * math.pi)))
        return _uniq(out)

    def build_g8(mats, coll, parent, lite=False):
        """rig_display and rig_screen, in the G8 frame (glass centre at y = 0, bottom edge at z = 0)."""
        A = Acc()
        cols = g8_columns(40 if lite else 220)
        rows = g8_rows(16 if lite else 90)
        S = G8_S
        # front glass: a cylinder, rows only where the material changes
        frows = _uniq([0.0, G8_RIM_BOTTOM, G8_ACT_Z0, G8_ACT_Z0 + G8_ACT_H, G8_H - G8_RIM, G8_H])
        F = [[g8_front(s, z) for s in cols] for z in frows]

        def fkey(i, j):
            s0, s1 = cols[i], cols[i + 1]
            z0, z1 = frows[j], frows[j + 1]
            rim = (s0 < -S + G8_RIM - 1e-6 or s1 > S - G8_RIM + 1e-6 or z0 < G8_RIM_BOTTOM - 1e-6 or
                   z1 > G8_H - G8_RIM + 1e-6)
            return "rim" if rim else "glass_g8"
        A.grid(F, None, want=lambda i, j: (-math.sin(cols[i] / G8_R), -math.cos(cols[i] / G8_R), 0), keyfn=fkey)
        # back shell
        B = [[g8_back(s, z) for s in cols] for z in rows]
        bv, _ = A.grid(B, "shell", want=lambda i, j: g8_n(cols[i]))
        # edge band: top, bottom, sides (front boundary sampled like the back, so no cracks)
        top_f = A.verts([g8_front(s, G8_H) for s in cols])
        bot_f = A.verts([g8_front(s, 0.0) for s in cols])
        A.strip(top_f, bv[-1], "shell", want=lambda i: (0, 0, 1))
        A.strip(bot_f, bv[0], "shell", want=lambda i: (0, 0, -1))
        for side, idx in ((-1, 0), (1, -1)):
            fr = A.verts([g8_front(cols[idx], z) for z in rows])
            br = [bv[j][idx] for j in range(len(rows))]
            A.strip(fr, br, "shell", want=lambda i, side=side: (side, 0, 0))
        # vent slot: a dark band just proud of the shell
        xs = [x_to_s(-G8_SLOT_L / 2 + G8_SLOT_L * i / (12 if lite else 60)) for i in range((12 if lite else 60) + 1)]
        zs = [G8_SLOT_Z - G8_SLOT_H / 2, G8_SLOT_Z + G8_SLOT_H / 2]
        A.grid([[g8_back(s, z, 0.0003) for s in xs] for z in zs], "black", want=lambda i, j: g8_n(xs[i]))
        _g8_panel(A, lite)
        _g8_hub(A, lite)
        _g8_ports(A, lite)
        body = A.finish("rig_display", mats, coll, parent)
        hub_uvs(body)
        # the picture, on the arc, just in front of the glass
        n = 40 if lite else 120
        ss = [-G8_ACT_W / 2 + G8_ACT_W * i / n for i in range(n + 1)]
        zz = [G8_ACT_Z0, G8_ACT_Z0 + G8_ACT_H]
        verts, faces, uvs = [], [], []
        for z in zz:
            for s in ss:
                f, nn = g8_front(s, z), g8_n(s)
                verts.append((f[0] - nn[0] * 0.0003, f[1] - nn[1] * 0.0003, z))
        for i in range(n):
            a, b, c, d = i, i + 1, n + 1 + i + 1, n + 1 + i
            faces.append([a, b, c, d])
        scr = geo.mesh_obj(nm("rig_screen"), verts, faces, collection=coll, parent=parent, material=mats["rig"],
                           smooth=True)
        uv = scr.data.uv_layers.new(name="UVMap")
        for poly in scr.data.polygons:
            for li, vi in zip(poly.loop_indices, poly.vertices):
                i, j = vi % (n + 1), vi // (n + 1)
                # MESHES.md: U left to right, V written upside down (0 on the top edge)
                uv.data[li].uv = (i / n, 1.0 - j)
        for poly in scr.data.polygons:      # face the viewer (-Y)
            if poly.normal.y > 0:
                poly.flip()
        scr.data.update()
        geo.set_origin(scr, (0.0, -0.0003, G8_ACT_Z0 + G8_ACT_H / 2))
        return body, scr

    def _g8_panel(A, lite):
        nz, nx = (8, 24) if lite else (30, 90)
        r = G8_PANEL_CORNER

        def xb(z):
            t = z / G8_PANEL_TOP
            x = G8_PANEL_XB + (G8_PANEL_XT - G8_PANEL_XB) * t
            dz = G8_PANEL_TOP - z
            if dz < r:
                x -= r - math.sqrt(max(0.0, r * r - (r - dz) ** 2))
            return x
        zs = [G8_PANEL_TOP * (1 - (1 - i / nz) ** 1.0) for i in range(nz + 1)]
        zs = _uniq(zs + [G8_PANEL_TOP - r * (1 - math.cos(a)) for a in [k * math.pi / 12 for k in range(7)]])
        P = []
        for z in zs:
            w = xb(z)
            P.append([g8_back(x_to_s(-w + 2 * w * i / nx), z, G8_PANEL_STEP) for i in range(nx + 1)])
        A.grid(P, "shell", want=lambda i, j: (0, 1, 0))
        # the step walls round the edge (left, top, right), sunk a little into the shell
        left = [x_to_s(-xb(z)) for z in zs]
        right = [x_to_s(xb(z)) for z in zs]
        topw = [x_to_s(-xb(zs[-1]) + 2 * xb(zs[-1]) * i / nx) for i in range(nx + 1)]
        for ss, zz, want in ((left, zs, (-1, 0, 0)), (right, zs, (1, 0, 0)), (topw, [zs[-1]] * len(topw), (0, 0, 1))):
            a = A.verts([g8_back(s, z, G8_PANEL_STEP) for s, z in zip(ss, zz)])
            b = A.verts([g8_back(s, z, -0.0006) for s, z in zip(ss, zz)])
            A.strip(a, b, "shell", want=lambda i, want=want: want)
        # a fine dark seam round it on the shell (left, top, right), as in the back photo
        g = 0.0007
        for sgn in (-1, 1):
            a = A.verts([g8_back(x_to_s(sgn * xb(z)), z, 0.00012) for z in zs])
            b = A.verts([g8_back(x_to_s(sgn * (xb(z) + g)), z, 0.00012) for z in zs])
            A.strip(a, b, "seam", want=lambda i: (0, 1, 0))
        a = A.verts([g8_back(s, zs[-1], 0.00012) for s in topw])
        b = A.verts([g8_back(s, zs[-1] + g, 0.00012) for s in topw])
        A.strip(a, b, "seam", want=lambda i: (0, 1, 0))
        bot = [x_to_s(-xb(0) + 2 * xb(0) * i / nx) for i in range(nx + 1)]
        a = A.verts([g8_back(s, 0.0, G8_PANEL_STEP) for s in bot])
        b = A.verts([g8_back(s, 0.0, -G8_EDGE_T) for s in bot])
        A.strip(a, b, "shell", want=lambda i: (0, 0, -1))

    def _g8_hub(A, lite):
        seg = 40 if lite else 128
        fr = frame((0, 0, G8_HUB_ZC), (1, 0, 0), (0, 0, 1), (0, 1, 0))   # axis along +Y
        prof, keys = g8_hub_profile(6 if lite else 16)
        A.lathe(prof, fr, seg, keys, cap_start=True, cap_end=False)

    def hub_uvs(obj):
        """UVHub on the lit ring and the trumpet: U = the angle round the hub / 2 pi (continuous across each
        face, the image repeats), V = 0.12 on the ring, 0.3..1 down the trumpet (see ring_image)."""
        me = obj.data
        uv = me.uv_layers.new(name="UVHub")
        # a new layer starts as one square per face, which would stop the exporter sharing any vertex: zero it
        uv.data.foreach_set("uv", [0.0] * (2 * len(uv.data)))
        lit ={i for i, m in enumerate(me.materials) if m and m.name.startswith(("mat_screens_g8_hub_light",
                                                                                  "mat_screens_g8_hub_funnel"))}
        y0, y1 = G8_HUB_FUNNEL_Y0, G8_HUB_BACK_Y - 0.0015
        for poly in me.polygons:
            if poly.material_index not in lit:
                continue
            funnel = me.materials[poly.material_index].name.startswith("mat_screens_g8_hub_funnel")
            c = poly.center
            pc = math.atan2(c.z - G8_HUB_ZC, c.x)
            for li, vi in zip(poly.loop_indices, poly.vertices):
                co = me.vertices[vi].co
                p = math.atan2(co.z - G8_HUB_ZC, co.x)
                while p - pc > math.pi:
                    p -= 2 * math.pi
                while pc - p > math.pi:
                    p += 2 * math.pi
                v = 0.3 + 0.7 * max(0.0, min(1.0, (co.y - y0) / (y1 - y0))) if funnel else \
                    0.02 + 0.23 * (G8_HUB_RIM_IN - math.hypot(co.x, co.z - G8_HUB_ZC)) / (G8_HUB_RIM_IN - G8_HUB_STEP_R)
                uv.data[li].uv = (p / (2 * math.pi), v)

    def _surface_frame(s, z, flip_u=True):
        p = V(g8_back(s, z))
        e = 1e-4
        du = (V(g8_back(s + e, z)) - V(g8_back(s - e, z))).normalized()
        dv = (V(g8_back(s, z + e)) - V(g8_back(s, z - e))).normalized()
        w = du.cross(dv).normalized()
        if w.y < 0:
            w = -w
        u = -du if flip_u else du       # seen from behind, u runs to the viewer's right (-X)
        v = w.cross(u).normalized()
        return frame(p, u, v, w)

    def _g8_ports(A, lite):
        fr = _surface_frame(0.0, G8_PORTS_Z)
        w, h = G8_PORTS_W, G8_PORTS_H
        n = 4 if lite else 10
        A.prism(stadium(w + 0.006, h + 0.006, n), fr, -0.006, 0.0006, "shell")          # raised silver surround
        A.prism(stadium(w, h, n), fr, -0.004, 0.0009, "black", cap0_key="black")         # dark bay on it
        if lite:
            return
        fr = fr @ Matrix.Translation((0, 0, 0.0009))
        for off, kind, pw, ph in G8_PORTS:
            u = off * MM
            if kind == "button":
                f2 = fr @ Matrix.Translation((u, 0, 0.0004))
                A.lathe([(pw / 2 * MM, 0.0), (pw / 2 * MM, 0.0011), (pw / 2 * MM - 0.0006, 0.0015), (0.0, 0.0015)],
                        f2, 32, "shell")
                continue
            if kind == "dc":
                A.prism(rr(pw * MM, ph * MM, 0.0008), fr @ Matrix.Translation((u, 0, 0)), 0.0, 0.0007, "port")
                f2 = fr @ Matrix.Translation((u, 0, 0.0007))
                A.lathe([(0.0028, 0.0), (0.0028, 0.0002), (0.0, 0.0002)], f2, 20, "chrome")
                continue
            A.prism(rr(pw * MM, ph * MM, 0.0007), fr @ Matrix.Translation((u, 0, 0)), 0.0, 0.0008, "chrome")
            A.prism(rr(pw * MM - 0.0012, ph * MM - 0.0012, 0.0004), fr @ Matrix.Translation((u, 0, 0)), 0.0008,
                    0.00085, "port")
            tongue = (0.0016, ph * MM * 0.62) if kind != "usbb" else (0.0032, 0.0032)
            A.prism(rr(tongue[0], tongue[1], 0.0003), fr @ Matrix.Translation((u, 0, 0)), 0.00085, 0.0009,
                    "black" if kind == "usba" else "chrome")

    def build_g8_stand(mats, coll, parent, lite=False):
        """The G8's own stand (optional), in the G8 frame: the foot sits G8_STAND_LOW below the panel."""
        A = Acc()
        zf = -G8_STAND_LOW
        fw, ft = G8_FOOT
        y_front = -G8_SAG - G8_FOOT_AHEAD
        y_back = G8_STAND_DEPTH - G8_SAG
        neck_t = G8_NECK[2]
        A.prism(rr(fw, y_back - y_front, 0.012, 6), frame((0, (y_front + y_back) / 2, zf), (1, 0, 0), (0, 1, 0),
                                                           (0, 0, 1)), 0.0, ft, "stand_silver")
        # neck: a tapered slab, graphite front, sides and sloped top, a silver plate on its back (round 2)
        y0, y1 = y_back - neck_t, y_back
        yp = y1 - G8_NECK_PLATE
        ztop = G8_HUB_ZC + G8_NECK_TOP
        wt, wb = G8_NECK[0], G8_NECK[1]
        cr = G8_NECK_CORNER

        def outline(zt):
            o = [(-wb / 2, zf + ft), (wb / 2, zf + ft), (wt / 2, zt - cr)]
            for k in range(1, 7):
                a = math.pi / 2 * k / 6
                o.append((wt / 2 - cr + cr * math.cos(a), zt - cr + cr * math.sin(a)))
            for k in range(1, 7):
                a = math.pi / 2 + math.pi / 2 * k / 6
                o.append((-wt / 2 + cr + cr * math.cos(a), zt - cr + cr * math.sin(a)))
            return o
        fr = frame((0, 0, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0))    # outline in (x, z), extrude towards -Y
        A.prism(outline(ztop), fr, -y1, -yp, "stand_silver")          # the silver back plate
        # the graphite body: its top slopes from the plate (ztop) down to the front (ztop - chamfer)
        n = 8
        rows = []
        for i in range(n + 1):
            t = i / n
            yy = yp - (yp - y0) * t
            rows.append([(x, yy, z) for x, z in outline(ztop - G8_NECK_CHAMFER * t)])
        loops = [A.verts(r) for r in rows]
        for i in range(n):
            A.strip(loops[i], loops[i + 1], "stand_dark", closed_loop=True, solid=True)
        A.face(loops[0], "stand_dark", closed=True)
        A.face(list(reversed(loops[-1])), "stand_dark", closed=True)
        # the cable window through the neck: a grey stadium on the back plate (the inside of the opening)
        ww, wh, wz = G8_WINDOW
        hole = frame((0, y1 + 0.0002, zf + wz), (-1, 0, 0), (0, 0, 1), (0, 1, 0))
        A.prism(stadium(ww, wh), hole, -0.0005, 0.0, "window")
        # the bracket from the neck to the hub's back
        bw, bh, bz = G8_BRACKET
        A.prism(rr(bw, bh, 0.004), frame((0, 0, G8_HUB_ZC + bz), (1, 0, 0), (0, 0, 1), (0, 1, 0)),
                G8_HUB_BACK_Y - G8_HUB_RECESS, y0 + 0.001, "stand_dark")
        return A.finish("rig_stand", mats, coll, parent, bevel=None if lite else 0.0012)

    # -----------------------------------------------------------------------
    # Studio Display
    # -----------------------------------------------------------------------
    def _sd_rings(lite):
        """(y, inset) pairs from the front glass to the back face."""
        out = [(0.0, SD_FRONT_ROUND), (SD_FRONT_ROUND, 0.0)]
        rb = SD_BACK_ROUND
        n = 3 if lite else 8
        for k in range(n + 1):
            a = math.pi / 2 * k / n
            out.append((SD_T - rb + rb * math.sin(a), rb - rb * math.cos(a)))
        return out

    def build_sd(mats, coll, parent, lite=False):
        """monitor_body and monitor_screen in the SD frame: glass at y = 0, bottom edge at z = 0."""
        A = Acc()
        nc = 4 if lite else 10
        fr = frame((0, 0, SD_H / 2), (1, 0, 0), (0, 0, 1), (0, 1, 0))   # (x, z) outline, w along +Y
        rings = []
        for y, ins in _sd_rings(lite):
            pts = rr(SD_W - 2 * ins, SD_H - 2 * ins, SD_CORNER - ins, nc)
            rings.append(A.verts([(u, v, y) for u, v in pts], fr))
        for i in range(len(rings) - 1):
            A.strip(rings[i], rings[i + 1], "alu" if i < 2 else "alu_edge", closed_loop=True, solid=True)
        A.face(list(reversed(rings[0])), "glass_sd", closed=True)
        A.face(rings[-1], "alu", closed=True)
        # active area (pixels off): a touch lighter than the border
        A.prism([(-SD_ACT_W / 2, -SD_ACT_H / 2), (SD_ACT_W / 2, -SD_ACT_H / 2), (SD_ACT_W / 2, SD_ACT_H / 2),
                 (-SD_ACT_W / 2, SD_ACT_H / 2)], fr, -0.00006, -0.00001, "off_sd")
        # camera dot
        cam = frame((0, -0.00008, SD_CAM_Z), (1, 0, 0), (0, 0, 1), (0, -1, 0))
        A.lathe([(SD_CAM_D / 2, 0.0), (SD_CAM_D / 2, 0.00004), (0.0, 0.00004)], cam, 16, "black")
        if not lite:
            # perforated bands on the bottom and top faces
            gw, gd = SD_GRILLE
            for z, wz in ((-0.00005, -1), (SD_H + 0.00005, 1)):
                p = [[(-gw / 2, 0.0055, z), (gw / 2, 0.0055, z)], [(-gw / 2, 0.0055 + gd, z), (gw / 2, 0.0055 + gd, z)]]
                A.grid(p, "perf", want=lambda i, j, wz=wz: (0, 0, wz))
            # ports on the back: four USB-C slots, the round power inlet
            for x in SD_PORTS_X:
                f2 = frame((x, SD_T + 0.00005, SD_POWER[2]), (1, 0, 0), (0, 0, 1), (0, 1, 0))
                A.prism(stadium(0.0026, 0.0084, 4), f2, 0.0, 0.00005, "port")
            pw = frame((0, SD_T, SD_POWER[2]), (1, 0, 0), (0, 0, 1), (0, 1, 0))
            ro, ri = SD_POWER[0] / 2, SD_POWER[1] / 2
            # round 2: a flat matte black disc with a fine ring (Apple's diagram), not a dome
            A.lathe([(ro, -0.0005), (ro, 0.00025), (0.0, 0.00025)], pw, 64, "sd_inlet")
            A.lathe([(ri, 0.00025), (ri, 0.0003), (0.0, 0.0003)], pw, 64, "sd_ring", cap_start=False)
        # VESA mount adapter: the H plate, raised 10.5 mm, its top edge rounded (round 2: it read flat)
        fr_h = frame((0, 0, SD_H), (1, 0, 0), (0, 0, 1), (0, 1, 0))
        re_ = SD_H_EDGE
        layers = [(SD_T - 0.0005, 0.0), (SD_DEPTH - re_, 0.0)]
        for k in range(1, (3 if lite else 6) + 1):
            a = math.pi / 2 * k / (3 if lite else 6)
            layers.append((SD_DEPTH - re_ + re_ * math.sin(a), re_ * (1 - math.cos(a))))
        hl = [A.verts([(u, v, w) for u, v in sd_h_outline(3 if lite else 6, d / MM)], fr_h) for w, d in layers]
        for i in range(len(hl) - 1):
            A.strip(hl[i], hl[i + 1], "alu_h", closed_loop=True, solid=True)
        A.face(list(reversed(hl[0])), "alu_h", closed=True)
        A.face(hl[-1], "alu_h", closed=True)
        if not lite:          # the four screws (VESA 100), silver heads with a dark socket
            for sx in (-1, 1):
                for zt in SD_H_SCREWS:
                    f3 = frame((sx * SD_H_RAIL[1] * MM, SD_DEPTH, SD_H - zt * MM), (1, 0, 0), (0, 0, 1), (0, 1, 0))
                    # flush in a counterbore (Apple's side diagram shows nothing proud of the rails)
                    A.lathe([(0.0062, 0.0), (0.0062, 0.00004), (0.0, 0.00004)], f3, 32, "port", cap_start=False)
                    A.lathe([(0.0056, 0.00004), (0.0056, 0.00008), (0.0048, 0.00012), (0.0, 0.00012)], f3, 32, "screw",
                            cap_start=False)
                    A.lathe([(0.0017, 0.00013), (0.0, 0.00013)], f3, 6, "port", cap_start=False)
        body = A.finish("monitor_body", mats, coll, parent, bevel=None if lite else 0.0007)
        scr = geo.screen_plane(nm("monitor_screen"), POSTS_W, POSTS_H, (0.0, -0.0002, SD_H / 2), collection=coll,
                               parent=parent, material=mats["posts"])
        return body, scr

    def sd_h_outline(n=6, d=0.0):
        """The adapter's H in (x, z) mm -> m, z measured up from the display's top (negative); d (mm) insets it
        (the rounded top edge): the rail ends keep their centres, the inner corners grow by d."""
        rw, rc, rt, rbot = SD_H_RAIL
        bt, bb = SD_H_BAR
        c = SD_H_CORNER + d
        hw = rw / 2 - d
        pts = []

        def arc(cx, cz, r, a0, a1, k=n):
            for i in range(k + 1):
                a = math.radians(a0 + (a1 - a0) * i / k)
                pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
        hc = rw / 2                                                 # the rail ends' centres stay put
        arc(-rc, -(rt + hc), hw, 180, 0, 2 * n)                     # left rail top
        c0 = SD_H_CORNER
        arc(-(rc - rw / 2) + c0, -bt + c0, c, 180, 270)            # inner corner, top of the bar
        arc((rc - rw / 2) - c0, -bt + c0, c, 270, 360)
        arc(rc, -(rt + hc), hw, 180, 0, 2 * n)                      # right rail top
        arc(rc, -(rbot - hc), hw, 0, -180, 2 * n)                   # right rail bottom
        arc((rc - rw / 2) - c0, -bb - c0, c, 0, 90)
        arc(-(rc - rw / 2) + c0, -bb - c0, c, 90, 180)
        arc(-rc, -(rbot - hc), hw, 0, -180, 2 * n)                  # left rail bottom
        return [(x * MM, z * MM) for x, z in pts]

    # -----------------------------------------------------------------------
    # pole and arms
    # -----------------------------------------------------------------------
    def build_pole(mats, coll, parent, lite=False):
        A = Acc()
        seg = 20 if lite else 48
        y = POLE_Y
        # clamp: top plate, flange, pole, cap
        A.prism(rr(0.090, DESK_BACK_Y + 0.010 - (y - 0.055), 0.014, 4 if lite else 8),
                frame((0, (y - 0.055 + DESK_BACK_Y + 0.010) / 2, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), 0.0015, 0.010,
                "white")
        A.prism(rr(0.084, DESK_BACK_Y + 0.004 - (y - 0.052), 0.012, 4),
                frame((0, (y - 0.052 + DESK_BACK_Y + 0.004) / 2, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), 0.0, 0.0015,
                "rubber")
        A.lathe([(0.032, 0.010), (0.032, 0.020), (0.030, 0.024), (POLE_R, 0.026), (0.0, 0.026)],
                Matrix.Translation((0, y, 0)), seg, "white", cap_end=False)
        A.lathe([(POLE_R, 0.024), (POLE_R, POLE_H - 0.010), (POLE_R + 0.0008, POLE_H - 0.010),
                 (POLE_R + 0.0008, POLE_H - 0.003), (POLE_R - 0.002, POLE_H), (0.0, POLE_H)],
                Matrix.Translation((0, y, 0)), seg, "white", cap_end=False)
        # spine behind the desk edge, jaw under it, screw, pressure pad, knob
        zb = -DESK_T
        A.box(-0.03, 0.03, DESK_BACK_Y + 0.010, DESK_BACK_Y + 0.022, zb - 0.032, 0.010, "white")
        A.box(-0.026, 0.026, y - 0.025, DESK_BACK_Y + 0.016, zb - 0.031, zb - 0.020, "white")
        A.cyl(0.006, (0, y, zb - 0.060), (0, y, zb - 0.003), 12 if lite else 24, "chrome")
        A.lathe([(0.022, zb - 0.0045), (0.022, zb - 0.0015), (0.0, zb - 0.0015)], Matrix.Translation((0, y, 0)),
                seg, "white", cap_end=False)
        A.lathe([(0.022, zb - 0.0015), (0.022, zb), (0.0, zb)], Matrix.Translation((0, y, 0)), seg, "rubber",
                cap_end=False)
        A.lathe([(0.0, zb - 0.078), (0.019, zb - 0.078), (0.021, zb - 0.074), (0.021, zb - 0.064),
                 (0.012, zb - 0.060), (0.0, zb - 0.060)], Matrix.Translation((0, y, 0)), seg, "white",
                cap_start=False, cap_end=False)
        return A.finish("desk_pole", mats, coll, parent, bevel=None if lite else 0.0012)

    def build_arm(name, mats, coll, parent, mount_y, zc, lite=False):
        """A collar on the pole, a link, a swivel, a tilt head and a VESA 100 plate, its face at mount_y."""
        A = Acc()
        seg = 16 if lite else 40
        pt = VESA_PLATE[1]
        y_sw = mount_y + pt + 0.040
        # VESA plate and its screws
        A.prism(rr(VESA_PLATE[0], VESA_PLATE[0], 0.010, 3 if lite else 6),
                frame((0, 0, zc), (1, 0, 0), (0, 0, 1), (0, 1, 0)), mount_y, mount_y + pt, "white")
        if not lite:
            for sx in (-1, 1):
                for sz in (-1, 1):
                    p = (sx * G8_VESA / 2, mount_y + pt, zc + sz * G8_VESA / 2)
                    A.lathe([(0.0045, 0.0), (0.0045, 0.0012), (0.0035, 0.0022), (0.0, 0.0024)],
                            Matrix.Translation(p) @ Matrix.Rotation(-math.pi / 2, 4, "X"), 20, "chrome",
                            cap_end=False)
        # tilt head: a knuckle with an axle and two knobs
        A.prism(rr(0.046, 0.044, 0.008, 3 if lite else 6), frame((0, 0, zc), (1, 0, 0), (0, 0, 1), (0, 1, 0)),
                mount_y + pt, y_sw - 0.016, "white")
        A.cyl(0.012, (-0.031, y_sw - 0.024, zc), (0.031, y_sw - 0.024, zc), seg, "white")
        for sx in (-1, 1):
            A.cyl(0.0135, (sx * 0.031, y_sw - 0.024, zc), (sx * 0.036, y_sw - 0.024, zc), seg, "white")
        # swivel and link
        A.cyl(0.019, (0, y_sw, zc - 0.022), (0, y_sw, zc + 0.022), seg, "white")
        A.prism(rr(0.040, 0.028, 0.009, 3 if lite else 6), frame((0, 0, zc), (1, 0, 0), (0, 0, 1), (0, 1, 0)),
                y_sw, POLE_Y, "white")
        # collar on the pole, with its locking lever
        A.lathe([(0.027, zc - 0.026), (0.027, zc + 0.026)], Matrix.Translation((0, POLE_Y, 0)), seg, "white")
        A.box(0.024, 0.040, POLE_Y - 0.007, POLE_Y + 0.007, zc - 0.012, zc + 0.012, "white")
        A.cyl(0.006, (0.040, POLE_Y, zc), (0.052, POLE_Y, zc), seg, "rubber")
        return A.finish(name, mats, coll, parent, bevel=None if lite else 0.0012)

    # -----------------------------------------------------------------------
    # ScreenBar Halo 2
    # -----------------------------------------------------------------------
    def build_screenbar(mats, coll, parent, front_y, top_z, back_y_mm=None, depth_at=None, lite=False, name="desk_screenbar"):
        """In its own frame: origin at the monitor's top front edge, +Y back, +Z up (mm sections)."""
        A = Acc()
        t = back_y_mm if back_y_mm is not None else depth_at(-45.0)
        off, pad0, pad1 = halo_fit(t)
        org = Matrix.Translation((0, front_y + off * MM, top_z))
        fx = org @ frame((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))     # (y, z) outline, extrude along X

        def mm(pts):
            return [(a * MM, b * MM) for a, b in pts]
        sec = mm(halo_bar_section())
        A.prism(sec, fx, -HB_L / 2, HB_L / 2, "halo")
        # LED diffuser on the bar's underside, sensor window on top
        p0, p1 = V((0, -55.0 * MM, 13.9 * MM)), V((0, -39.0 * MM, 12.85 * MM))
        P = [[(x, p.y, p.z - 0.0002) for x in (-0.240, 0.240)] for p in (p0, p1)]
        A.grid([[org @ V(q) for q in row] for row in P], "led", want=lambda i, j: (0, 0, -1))
        A.prism(rr(0.050, 0.009, 0.003), org @ frame((0, -42 * MM, 33.3 * MM), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                -0.0001, 0.0003, "halo_glossy")
        # arm over the monitor, the front foot pad (slid to the monitor's front edge)
        A.prism(mm(HALO_ARM), fx, -HB_CLAMP_W / 2, HB_CLAMP_W / 2, "halo_plastic")
        p0, p1 = pad0, pad1
        A.prism(rr((p1 - p0) * MM, HB_PAD, 0.001), fx @ Matrix.Translation(((p0 + p1) / 2 * MM, HB_PAD / 2, 0)),
                -0.020, 0.020, "rubber")
        A.prism(rr((p1 - p0) * MM, 7.6 * MM - HB_PAD, 0.001),
                fx @ Matrix.Translation(((p0 + p1) / 2 * MM, HB_PAD + (7.6 * MM - HB_PAD) / 2, 0)), -0.021, 0.021,
                "halo_plastic")
        if not lite:       # the toothed rail the pad slides on
            for k in range(int((56.0 - 4.0) / 3.0)):
                y = 4.0 + 3.0 * k
                if not (p0 - 1 < y < p1 + 1):
                    A.box(-0.016, 0.016, y * MM, (y + 1.4) * MM, 6.4 * MM, 7.7 * MM, "halo_plastic")
        # rear block with its backlight outline
        blk = rr(21.4 * MM, 46.2 * MM, 0.005, 3 if lite else 6)
        A.prism(blk, fx @ Matrix.Translation(((60.5 + 10.7) * MM, (-0.8 + 23.1) * MM, 0)), -HB_CLAMP_W / 2,
                HB_CLAMP_W / 2, "halo_plastic")
        if not lite:
            band = org @ frame((0, 81.95 * MM, 22.0 * MM), (1, 0, 0), (0, 0, 1), (0, 1, 0))
            A.prism(rr(0.040, 0.039, 0.004, 4), band, 0.0, 0.00015, "led_back")
            A.prism(rr(0.037, 0.036, 0.003, 4), band, 0.00015, 0.0002, "halo_plastic")
        # the hinged weight, hanging square, its rubber face on the monitor's back
        hinge = org @ Matrix.Translation((0, HALO_HINGE[0] * MM, HALO_HINGE[1] * MM))
        fw = hinge @ frame((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))
        A.prism(mm(HALO_WEIGHT), fw, -0.022, 0.022, "halo_plastic")
        A.prism(rr(0.0008, 0.020, 0.0002), fw @ Matrix.Translation((-18.4 * MM, -40 * MM, 0)), -0.018, 0.018, "rubber")
        A.cyl(0.0045, hinge @ V((-0.024, 0, 0)), hinge @ V((0.024, 0, 0)), 24, "halo_plastic")
        obj = A.finish(name, mats, coll, parent, bevel=None if lite else 0.0006)
        obj["bar_offset_mm"] = round(off, 1)
        return obj

    def build_dial(mats, coll, parent, lite=False, name="desk_screenbar_dial"):
        A = Acc()
        seg = 24 if lite else 64
        d, h = HB_DIAL
        r = d / 2
        org = Matrix.Translation((DIAL_AT[0], DIAL_AT[1], 0))
        A.lathe([(r - 0.0015, 0.0), (r, 0.0015), (r, 0.024)], org, seg, "halo_plastic", cap_end=False)
        A.lathe([(r, 0.024), (r - 0.0004, 0.030), (r - 0.003, 0.0305)], org, seg, "halo", cap_start=False,
                cap_end=False)
        A.lathe([(r - 0.003, 0.0305), (r - 0.0035, h - 0.001), (r - 0.0045, h), (0.0, h)], org, seg, "halo_glossy",
                cap_start=False, cap_end=False)
        return A.finish(name, mats, coll, parent)

    def _brand(key, part, at, normal, up, name, lite, coll, **kw):
        """A brand decal on `part`, `at`/`normal`/`up` in the screens root frame (root at the origin)."""
        bpy.context.view_layer.update()
        inv = part.matrix_world.inverted()
        root_m = part.parent.matrix_world if part.parent is not None else Matrix.Identity(4)
        m = inv @ root_m
        n, u = (m.to_3x3() @ V(normal)).normalized(), (m.to_3x3() @ V(up)).normalized()
        return brands.decal(key, m @ V(at), n, u, parent=part, collection=coll, name=nm(name), lite=lite, **kw)

    def add_brands(parts, coll, lite, halo_on, z_sd):
        out = {}
        b = BRAND_G8
        f = g8_front(0.0, b["z"])
        out["g8_brand"] = _brand("screens_g8", parts["rig_display"], (f[0], f[1], f[2] + G8_Z0), (0, -1, 0),
                                 (0, 0, 1), "g8_brand", lite, coll, height=b["height"], max_width=b["max_width"],
                                 colour=b["colour"], finish=b["finish"])
        b = BRAND_SD
        out["sd_brand"] = _brand("screens_sd", parts["monitor_body"], (0.0, SD_Y + SD_T, z_sd + SD_H - b["below_top"]),
                                 (0, 1, 0), (0, 0, 1), "sd_brand", lite, coll, height=b["height"],
                                 colour=b["colour"], finish=b["finish"])
        if halo_on == "top":
            b = BRAND_HALO
            off = halo_fit(SD_T / MM)[0]
            out["screenbar_brand"] = _brand("screenbar", parts["desk_screenbar"],
                                            (0.0, SD_Y + (off + b["y"]) * MM, z_sd + SD_H + b["z"]), (0, -1, 0),
                                            (0, 0, 1), "screenbar_brand", lite, coll, height=b["height"],
                                            max_width=b["max_width"], colour=b["colour"], finish=b["finish"])
        return {k: o for k, o in out.items() if o is not None}

    # -----------------------------------------------------------------------
    # the whole component
    # -----------------------------------------------------------------------
    def g8_back_y_mm(z_from_top):
        """Depth of the G8's back at its centre, z mm below its top (negative = below)."""
        z = G8_H + z_from_top * MM
        return (g8_d(0.0, max(0.0, min(G8_H, z)))) / MM

    def build(collection=None, parent=None, lite=False, halo_on=HALO_ON, suffix=""):
        """Returns the root empty. With suffix (e.g. "_lite") every part name gets it."""
        _SFX[0] = suffix
        mats = make_materials()
        if collection is None:
            r, collection = geo.root("screens" + suffix)
        else:
            r = bpy.data.objects.new("screens" + suffix, None)
            collection.objects.link(r)
            names.set_name(r, "screens" + suffix, data=False)
        r.parent = parent
        coll = collection
        parts = {}
        g8b, g8s = build_g8(mats, coll, r, lite)
        for o in (g8b, g8s):
            o.location.z += G8_Z0
        parts["rig_display"], parts["rig_screen"] = g8b, g8s
        if not lite:
            st = build_g8_stand(mats, coll, r)
            st.location.z += G8_Z0
            st.hide_render = st.hide_viewport = True
            parts["rig_stand"] = st
        z_sd = sd_z0(halo_on)
        sdb, sds = build_sd(mats, coll, r, lite)
        for o in (sdb, sds):
            o.location.y += SD_Y
            o.location.z += z_sd
        parts["monitor_body"], parts["monitor_screen"] = sdb, sds
        parts["desk_pole"] = build_pole(mats, coll, r, lite)
        parts["rig_static"] = build_arm("rig_static", mats, coll, r, G8_HUB_BACK_Y, G8_Z0 + G8_HUB_ZC, lite)
        parts["monitor_static"] = build_arm("monitor_static", mats, coll, r, SD_Y + SD_DEPTH, z_sd + SD_H / 2, lite)
        if halo_on == "top":
            parts["desk_screenbar"] = build_screenbar(mats, coll, r, SD_Y, z_sd + SD_H, back_y_mm=SD_T / MM, lite=lite)
        else:
            parts["desk_screenbar"] = build_screenbar(mats, coll, r, 0.0, G8_Z0 + G8_H, depth_at=g8_back_y_mm,
                                                      lite=lite)
        parts["desk_screenbar_dial"] = build_dial(mats, coll, r, lite)
        parts.update(add_brands(parts, coll, lite, halo_on, z_sd))
        _SFX[0] = ""
        r["parts"] = list(parts)
        return r

    def check(root):
        probs = []
        for o in [root] + names.descendants(root):
            if not names.NAME_RE.match(o.name):
                probs.append(f"bad name {o.name}")
            if o.type == "MESH" and o.data.name == o.name:
                probs.append(f"mesh data named like {o.name}")
            if o.type == "MESH" and tuple(round(s, 6) for s in o.scale) != (1.0, 1.0, 1.0):
                probs.append(f"scale on {o.name}")
        for k in ("monitor_screen", "rig_screen"):
            o = bpy.data.objects.get(k)
            if o is None or len(o.data.materials) != 1:
                probs.append(f"{k}: needs one material")
        if probs:
            raise AssertionError("screens: " + "; ".join(probs))
        tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons)
                for o in names.descendants(root) if o.type == "MESH"}
        return {"parts": len(tris), "triangles_before_bevels": sum(tris.values()), "per_part": tris}
