"""Real specs of the guitars, in millimetres, for the 2D blueprints and the Blender builds.

One block per guitar, added one guitar per session (decision of 2026-10-23). Plain Python,
no Blender import, so the 2D sheet (blender/design/guitar_NN_blueprint.py) and the 3D
build read the same numbers.

Coordinates, every guitar, front view as it hangs on the wall facing the room:
    u   across the guitar, mm. 0 on the string centre line, + to the viewer's right.
    v   along the guitar, mm. 0 at the body's tail edge (the end strap button sits below
        it), + up towards the headstock tip.
    z   out of the body, mm. 0 on the body's top (front) face, + towards the room,
        the back face at -body_t.
Headstock outlines use (a, b): a = u, b = v - v_nut (b = 0 on the nut's fretboard edge).
Outlines are spline control points: pass them through spline() for the curve.
"""
import math


def fret_positions(scale, n):
    """Distance of frets 1..n from the nut (equal temperament)."""
    return [scale * (1 - 2 ** (-k / 12)) for k in range(1, n + 1)]


def spline(points, closed=True, n=12):
    """Centripetal Catmull-Rom through the points: a list of (x, y), n samples per segment."""
    pts = list(points)
    if closed:
        ext = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        ext = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + pts + \
              [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
    out = []

    def tj(ti, a, b):
        return ti + max(1e-6, math.hypot(b[0] - a[0], b[1] - a[1])) ** 0.5

    for i in range(len(ext) - 3):
        p0, p1, p2, p3 = ext[i:i + 4]
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        for k in range(n):
            t = t1 + (t2 - t1) * k / n
            def lerp(a, b, ta, tb):
                w = (t - ta) / (tb - ta)
                return (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w)
            a1, a2, a3 = lerp(p0, p1, t0, t1), lerp(p1, p2, t1, t2), lerp(p2, p3, t2, t3)
            b1, b2 = lerp(a1, a2, t0, t2), lerp(a2, a3, t1, t3)
            out.append(lerp(b1, b2, t1, t2))
    if not closed:
        out.append(pts[-1])
    return out


# ---------------------------------------------------------------------------
# guitar_02: Jimi Hendrix's white Stratocaster, the Woodstock guitar (1968, serial not
# reproduced). A right-handed guitar flipped (turned 180 degrees in its own plane) and
# restrung for left-handed playing. Hung on the wall facing the room, a flip of that kind
# leaves the front view of the body exactly as a right-handed guitar's: long horn on the
# viewer's left, controls and jack lower right, tuners on the headstock's left edge (the
# MoPOP display photo shows the same). What changes is the stringing: thin E on the
# viewer's left, thick E on the right and on the tip tuner, reversed saddle intonation,
# and a strap button Hendrix added on the short (treble) horn. Blueprint option A.
# Sources and choices: video-local/footage/2026-10-23-guitar-02/NOTE.md
# ---------------------------------------------------------------------------
_SCALE = 647.7                     # 25.5 in
_NUT_V = 786.0                     # tail edge to nut: saddle line 138 from the tail (MoPOP photo) + scale
_HEAD_L = 190.5                     # nut to headstock tip (r3, small headstock; the large one was 208)

GUITAR_02 = dict(
    scale=_SCALE, frets=21, v_nut=_NUT_V, overall=_NUT_V + _HEAD_L, v_tip=_NUT_V + _HEAD_L,
    v_saddle=_NUT_V - _SCALE,      # 138.3: the scale line, before saddle compensation

    # body: alder, 44.5 thick, edge roundover, late-60s contours (shallower than 1950s)
    body_t=44.5, edge_r=6.4,
    body=[  # (u, v), counter-clockwise from the tail, measured from the MoPOP photo and
            # scaled to 457 long, 322 wide; the stretch under the neck heel is the pocket floor.
            # Revised 2026-10-23 (3D build, r2): the upper bout was 271.5 wide, a vintage Strat's
            # is about 0.88 of its lower bout (275.5 now); the treble horn ended at the 17th fret,
            # a frontal photo of a 1970 Strat (perspective-corrected on its fret dots) puts it at
            # the 15th to 16th (396.5 now); both horn tips narrower, as on the real body.
        (0, 0.3), (25, 1.5), (65, 8), (108, 17), (132, 30), (147, 48), (156, 66), (161, 95),
        (159, 130), (150, 156), (138, 186), (124, 212), (115, 236), (113.5, 262), (118, 281),
        (125.5, 301), (131, 322), (134, 344), (133, 364), (127.5, 381), (118.5, 392.5),
        (108, 396.5), (99, 393), (93, 383), (88.5, 368), (82.5, 351), (73, 339), (59, 332),
        (45, 329.5), (31, 330.5), (29, 334), (29, 384),
        (26, 388), (0, 388.5), (-26, 388), (-29, 388), (-38, 381), (-52, 376.5), (-68, 382),
        (-80, 393), (-87, 410), (-90, 428), (-93, 444), (-98, 452.5), (-106, 456.5),
        (-114.5, 455), (-124, 450.5), (-133.5, 442.5), (-138.5, 431.5), (-141, 418), (-141.5, 400),
        (-141, 381), (-137, 357), (-129, 337), (-118.5, 303), (-115.5, 270), (-122, 238), (-137, 205), (-152, 166),
        (-160, 135), (-161, 95), (-157, 62), (-147, 41), (-130, 22), (-96, 8), (-25, 0)],
    forearm=dict(depth=12.0, width=60.0, region=[   # front face, bass lower bout (clip to body)
        (-150, 42), (-118, 85), (-104, 130), (-103, 180), (-110, 222), (-120, 250),
        (-126, 252), (-140, 205), (-156, 166), (-165, 135), (-166, 95), (-161, 60)]),
    belly=dict(depth=14.0, width=95.0, region=[      # back face, bass upper bout and horn root (clip to body)
        (-118, 250), (-84, 280), (-64, 320), (-60, 360), (-72, 400), (-95, 444), (-112, 462),
        (-132, 448), (-142, 425), (-147, 395), (-145, 370), (-135, 337), (-123, 303),
        (-119, 270), (-124, 245)]),

    # neck: two-piece maple (a glued maple fingerboard cap, no skunk stripe on the back),
    # truss rod adjusted at the heel, so nothing on the headstock face. 4-bolt, no tilt.
    nut_w=41.3, w12=52.0, nut_l=4.7, nut_material="bone",
    neck_t1=20.8, neck_t12=23.6,          # back of neck to fretboard crown, '60s C
    v_butt=325.0, butt_side_v=330.0,      # rounded end of neck and fretboard (photo: 461 from the nut)
    pocket_depth=15.9, board_above_body=9.5, v_pocket_end=388.0,
    neck_angle_deg=0.0, radius=184.2,     # 7.25 in fretboard radius
    fret_wire=(2.1, 1.1), dot_d=6.35, dots=(3, 5, 7, 9, 12, 15, 17, 19, 21),
    dot12_offset=11.0,                    # the two 12th-fret dots, each side of centre

    # headstock (r3, owner's choice 2026-10-23): the small 1950s/early-60s Strat outline, traced from
    # the owner's square-on photo (docs/moodboard/local/strat-owner-ref-8.jpg, local only), rectified by a
    # homography on the nut ends, the ends of frets 1-3, the 3rd-fret dot and the six post bushings on one
    # line at 25.4 pitch (residual 0.45 mm rms, 1.4 max), smoothed (2 mm; 0.8 mm at most from the trace)
    # and sampled every 5 mm;
    # checked against the small headstock of the Commons comparison photo (median 1.3 mm apart).
    # Flat, face 6.4 below the fretboard; no logo, decal or text.
    head_t=14.3, head_step=6.4, head_angle_deg=0.0,
    headstock=[  # (a, b), open curve from the nut's right end, over the tip, to its left end
        (20.65, 0), (21.9, 5.9), (22.3, 10.6), (22.7, 15.4), (23.6, 20), (24.9, 24.5), (26.6, 28.8),
        (28.7, 33), (31.6, 36.9), (35, 40.4), (38.7, 43.4), (42.7, 46), (46.7, 48.3), (49.2, 51.9),
        (49.1, 56.5), (48.6, 61.3), (47.9, 66), (47.2, 70.7), (46.3, 75.2), (45.3, 79.8), (44.1, 84.3),
        (42.9, 88.8), (41.8, 93.4), (40.6, 97.9), (39.4, 102.4), (38.3, 106.9), (37.4, 111.4), (36.6, 115.9),
        (35.8, 120.7), (35.3, 125.4), (35.3, 130.1), (37, 134.4), (40.7, 137.4), (44.7, 139.9), (48.5, 142.9),
        (51.8, 146.3), (54.4, 150.3), (56.4, 154.5), (57.5, 159.1), (57.9, 163.8), (57.6, 168.5), (56.7, 173.1),
        (55, 177.5), (52.5, 181.5), (49.1, 184.9), (45.1, 187.5), (40.8, 189.3), (36.3, 190.4), (31.6, 190.5),
        (27, 189.6), (22.6, 188.1), (18.5, 185.8), (14.6, 183), (11.3, 179.5), (8.6, 175.6), (6.2, 171.6),
        (4.3, 167.3), (3.3, 162.8), (2, 158.3), (0.6, 153.9), (-0.8, 149.4), (-2.5, 145.1), (-3.6, 140.6),
        (-4.7, 136.1), (-6, 131.6), (-7.3, 127.1), (-9, 122.7), (-10.2, 118.3), (-11.2, 113.7), (-12.5, 109.2),
        (-13.8, 104.7), (-15.4, 100.4), (-17, 96), (-17.9, 91.5), (-19.1, 87), (-20.4, 82.5), (-21.8, 78.2),
        (-23.4, 73.8), (-24.5, 69.3), (-25.6, 64.8), (-27, 60.3), (-28.3, 55.8), (-29.9, 51.5), (-31.1, 47),
        (-32.2, 42.5), (-33.6, 38), (-34.9, 33.5), (-35.9, 28.9), (-36, 24.2), (-34.2, 20), (-30.8, 16.5),
        (-27, 13.8), (-23.8, 10.3), (-22.4, 5.9), (-20.65, 0)],
    tuner_posts=[(-23.92, 40.09), (-16.2, 64.28), (-8.47, 88.48), (-0.75, 112.68), (6.97, 136.88), (14.69, 161.08)],   # (a, b): one line, 17.7 deg to the neck axis
    tuner_line_deg=17.7, tuner_pitch=25.4, tuner_a=-23.92, tuner_b0=40.09,
    post_d=6.3, bushing_d=9.0, post_h=16.0,
    tuner_key=dict(gap=2.5, w=14.0, h=17.0, z=-17.0, t=5.0),   # vintage oval metal keys, shafts square to the
                                                                # neck axis, each button 2.5 past the edge
    tuner_housing=dict(w=13.0, h=21.0, depth=12.0),            # on the back, plain (no stamp)
    string_tree=dict(a=13.6, b=66.8, w=12.0, h=5.0, height=5.0, holds="A and low E"),   # r3: from the photo
    hook=dict(gap=46.0),       # inner gap of the wall hanger's two prongs

    # strings, left to right at the nut as it hangs (Hendrix's stringing)
    strings=("E1", "B", "G", "D", "A", "E6"),
    gauges=(0.010, 0.013, 0.017, 0.026, 0.032, 0.038),   # in, plain G light set of the era
    nut_spread=34.6, bridge_spread=56.4,                 # outer strings, centre to centre
    saddle_back=(1.5, 2.5, 3.5, 3.0, 3.8, 4.8),          # mm behind the scale line, per string

    # pickups: three single coils, white covers, staggered poles as built (not turned)
    pickup=dict(l=83.0, w=18.5, pole_d=4.9, pole_spread=52.4, screw_off=38.5),   # r2: screws through
                                                                                   # the cover ends, 77 apart
    pickups_from_scale=(162.0, 102.0, 48.0),             # neck, middle, bridge centre, mm (photo)
    bridge_slant_deg=10.0,                               # treble (right) end towards the bridge
    pickup_top_z=(8.0, 7.5, 7.0),

    # pickguard: 3-ply white/black/white, about 2.3 thick, 30 degree bevel, 11 screws
    guard_t=2.3,
    pickguard=[
        (-29, 362), (-40, 366), (-55, 367), (-70, 362), (-86, 350), (-96, 330), (-101, 300),
        (-101, 270), (-96, 245), (-84, 226), (-68, 210), (-57, 188), (-48, 170), (-42, 163.5),
        (-39.5, 162), (39.5, 162), (42, 158.5), (44, 140), (50, 118), (62, 98), (80, 85),
        (100, 81), (116, 86), (125, 104), (126, 130), (122, 165), (115, 200), (107, 235),
        (104, 262), (108, 290), (113, 314), (105, 328), (88, 334), (70, 330.5), (55, 326.5),
        (40, 325.5), (28, 326)],
    guard_screws=[
        (-53, 361), (-89, 333), (-95, 262), (-76, 222), (-47, 174), (50, 135),
        (92, 89), (119, 110), (114, 195), (103, 300), (48, 320)],

    # controls (1968): master volume, neck tone, middle tone, 3-way blade switch
    knobs=[("volume", 64, 170), ("tone, neck", 83.5, 136), ("tone, middle", 103, 102)],
    knob=dict(d=24.5, top_d=20.0, h=16.0, above_guard=3.0),
    switch=dict(u=68, v=208, slot_l=22.0, slot_w=3.5, angle_deg=-60.0, tip_l=14.0, tip_w=8.0),

    # vintage synchronised tremolo: 6 pivot screws, bent steel saddles, block through the body
    bridge=dict(w=74.0, l=42.0, front_off=19.7, screw_d=4.0, saddle_w=11.1, saddle_l=26.0,
                lip_h=9.0, saddle_top_z=12.5, float_gap=1.5),
    arm=dict(u=31.0, v=128.0, length=140.0, angle_deg=158.0),  # resting across, as displayed
    trem_cover=dict(w=88.0, l=145.0, v0=94.0, r=10.0, screws=6, holes=6),

    # neck plate, jack, strap buttons
    neck_plate=dict(w=51.0, l=64.0, v=356.5, r=6.0, screw_du=17.0, screw_dv=23.0),
    jack=dict(u=106.0, v=60.0, l=56.0, w=26.0, angle_deg=-40.0, socket_d=12.5),
    strap_buttons=[  # (u, v, outward angle in degrees from +u, note)
        (0.0, 0.3, -90.0, "tail, original"),
        (-106.0, 456.5, 100.0, "long horn tip, original"),
        (108.0, 396.5, 80.0, "short horn, added by Hendrix"),
    ],
    strap_button=dict(d=11.0, h=11.0),
)


# ---------------------------------------------------------------------------
# guitar_04: Stevie Ray Vaughan's "Number One" (blues rock, 1980s), in the floor rack (slot 1).
# A 1963 alder body, a 1962 neck (rosewood board, clay dots) and 1959 pickups (The Met, object
# 815934), with his changes: a left-handed vintage tremolo, gold plated, so the arm sits on the bass
# (upper) side; a black pickguard (his stick-on initials left out); jumbo bass frets; heavy strings.
# The Strat geometry is GUITAR_02's (body r2, small headstock r3, neck heel, pickups, bridge); only what
# differs is overridden here. Played and hung right-handed: low E on the viewer's left as it stands.
# Measured on the owner's square-on photo (docs/moodboard/local/number-one/owner-ref-11.jpg, a Custom
# Shop copy made from the real guitar; local only), rectified by a homography on ten fret dots, the
# nut ends, the six pickup screws, four outer poles and the two strap buttons (3.8 px rms, about 2 mm):
# the pickguard outline and its nine screws, the knobs, the switch tip, the jack plate, the arm socket,
# and the wear map (where the sunburst survives, where bare wood shows pale). Sources and choices:
# video-local/footage/2026-10-23-guitar-04/NOTE.md
# No logos, decals, initials, sticker, serials or stamps.
# ---------------------------------------------------------------------------
GUITAR_04 = dict(GUITAR_02)
GUITAR_04.update(
    # neck: 1962, maple with a round-laminated rosewood board, clay dots, refretted with jumbo bass
    # wire (Dunlop 6100, 0.110 x 0.055 in); the copy measured from it: 10 in radius, 1.650 in bone nut,
    # 0.800 in at the 1st fret and 0.930 at the 12th, a big oval C
    nut_w=41.9, w12=52.0, nut_material="bone", neck_t1=20.3, neck_t12=23.6, radius=254.0,
    fret_wire=(2.79, 1.40), dot_d=6.35, dot12_offset=11.0, board="rosewood", dot_material="clay",

    # strings: right-handed stringing, heavy (his usual set .013 to .058), tuned to E flat
    strings=("E6", "A", "D", "G", "B", "E1"),
    gauges=(0.058, 0.038, 0.028, 0.019, 0.015, 0.013),
    nut_spread=35.0, bridge_spread=56.4,
    saddle_back=(4.8, 3.9, 3.3, 3.7, 2.6, 1.6),     # low E furthest back; a plain .019 G sits back too

    # Measured (r2 of this block, after the owner's review: "body outline is little bit off", "even
    # pickups of guitar are little off", "bridge is different ... jack input is not right") on owner-ref-11
    # rectified by fit 6: a homography solved together with the bridge row's and the pickups' positions
    # along the guitar, on the dots, the fret lines and the nut (centre line) and the bridge screws and
    # poles across (56.4 and 52.4 mm): 0.52 px rms. Nothing on the body, the pickups or the bridge's place is
    # assumed. Checked on the real guitar (n1-4.jpg, the same fit, 0.49 px rms). Scripts and numbers:
    # video-local/footage/2026-10-23-guitar-04/measure/ (fit6.py, trace_body.py, check_body.py, remap.py).

    # body: Number One's own outline, traced like the small headstock r3: the photo's silhouette in mm,
    # smoothed 2 mm, sampled every 5 mm; the neck-pocket stretch is r2's; the tail (broken by the floor
    # shadow and the strap button in the photo) is one fitted curve. Same frame as guitar_02 (v from
    # guitar_02's tail): this body's tail sits at v 10.1. 313 wide, 442.5 long.
    body=[
        (-0.5, 10.1), (4.5, 9.7), (9.3, 9.4), (14.1, 9.2), (19.1, 9.1), (24, 9.1), (28.9, 9.2), (33.9, 9.3),
        (38.8, 9.6), (43.8, 10), (48.8, 10.4), (53.6, 10.9), (58.4, 11.6), (63.4, 12.3), (68.4, 13.2),
        (72.9, 14), (75.4, 17.4), (79.8, 19.2), (84.6, 20.4), (89.5, 21.5), (94.3, 22.9), (99.1, 24.4),
        (103.8, 26), (108.4, 28.1), (112.9, 30.1), (117.3, 32.5), (121.5, 35.2), (125.6, 38), (129.4, 41.3),
        (133.2, 44.6), (136.6, 48.2), (139.9, 51.9), (142.8, 56), (145.6, 60.2), (148.1, 64.5), (150.4,
        68.9), (152.5, 73.4), (154.4, 78.1), (155.8, 82.9), (156.9, 87.7), (157.6, 92.7), (158, 97.7),
        (158.5, 102.6), (158.4, 107.6), (158.4, 112.6), (158.4, 117.6), (158.1, 122.6), (157.5, 127.6),
        (156.7, 132.5), (155.7, 137.4), (154.7, 142.3), (153.2, 147), (152, 151.9), (150.6, 156.7), (149,
        161.4), (147.6, 166.2), (145.9, 170.9), (143.9, 175.5), (142, 180.1), (140.2, 184.8), (137.9,
        189.2), (135.6, 193.7), (133.5, 198.2), (131.2, 202.6), (129, 207.1), (126.8, 211.6), (124.7,
        216.1), (122.5, 220.6), (120.5, 225.2), (118.4, 229.7), (116.7, 234.4), (115.2, 239.2), (114.1,
        244), (113.5, 249), (113, 254), (113.3, 258.9), (114, 263.9), (114.7, 268.8), (116.1, 273.6),
        (117.5, 278.4), (119.4, 283), (121.2, 287.7), (123.2, 292.3), (125.2, 296.8), (127.1, 301.4), (129,
        306.1), (130.9, 310.7), (132.5, 315.4), (134, 320.2), (135.3, 325), (136.3, 329.9), (137.2, 334.8),
        (137.8, 339.8), (138.3, 344.7), (138.3, 349.7), (138.2, 354.7), (137.6, 359.7), (136.7, 364.6),
        (135.6, 369.5), (134.1, 374.2), (132.4, 378.9), (129.5, 382.9), (125.9, 386.4), (121.7, 389.2),
        (117, 390.8), (112.1, 390.5), (107.5, 388.4), (104.3, 384.7), (101.7, 380.4), (99.9, 375.8), (98.7,
        370.9), (97.5, 366.1), (96.8, 361.1), (95.1, 356.4), (93.3, 351.8), (90.7, 347.5), (87.8, 343.5),
        (83.9, 340.3), (79.9, 337.3), (75.4, 335.2), (70.7, 333.5), (65.8, 332.6), (60.9, 331.7), (55.9,
        331.6), (51, 332.3), (46.1, 333.2), (41.2, 334.2), (36.5, 335.8), (31, 330.5), (29, 334), (29, 384),
        (26, 388), (0, 388.5), (-26, 388), (-29, 388), (32, 338.1), (-32.7, 379.8), (-37, 377.2), (-41.8,
        376.1), (-46.6, 374.6), (-51.6, 375.1), (-56.5, 375.8), (-61.3, 377.3), (-66, 378.8), (-70.4,
        381.2), (-74.6, 384), (-78.5, 387.1), (-82, 390.6), (-85.1, 394.5), (-87.8, 398.8), (-90.2, 403.1),
        (-91.6, 407.9), (-92.7, 412.8), (-93.6, 417.7), (-93.2, 422.7), (-93.4, 427.7), (-93.1, 432.7),
        (-93.9, 437.6), (-93.9, 442.6), (-96, 447), (-99.3, 450.8), (-103.8, 452.6), (-108.7, 451.6),
        (-113.5, 450.3), (-117.9, 447.9), (-121.5, 444.5), (-124.9, 440.8), (-127.7, 436.6), (-130, 432.3),
        (-131.9, 427.6), (-132.8, 422.9), (-134.7, 418.3), (-135.7, 413.4), (-135.6, 408.5), (-136.9,
        403.7), (-137.4, 398.7), (-137.5, 393.8), (-137.4, 388.8), (-137.2, 383.8), (-136.6, 378.8),
        (-135.8, 373.9), (-135, 368.9), (-133.9, 364.1), (-132.7, 359.2), (-131.4, 354.4), (-130.1, 349.6),
        (-128.8, 344.8), (-127.4, 340), (-125.8, 335.3), (-124.3, 330.5), (-122.8, 325.7), (-121.2, 321),
        (-119.7, 316.2), (-118.3, 311.4), (-116.7, 306.7), (-115.4, 301.9), (-114.1, 297), (-112.9, 292.2),
        (-111.7, 287.4), (-111, 282.4), (-110.5, 277.5), (-110.3, 272.5), (-110.2, 267.5), (-110.5, 262.5),
        (-110.8, 257.5), (-111.4, 252.5), (-112.5, 247.7), (-113.9, 242.9), (-115.4, 238.1), (-117, 233.4),
        (-118.9, 228.7), (-121, 224.2), (-122.9, 219.6), (-124.8, 215), (-126.7, 210.4), (-128.5, 205.7),
        (-130.4, 201.1), (-132.4, 196.5), (-134.5, 192), (-136.6, 187.4), (-138.4, 182.8), (-140.5, 178.2),
        (-142.2, 173.5), (-144, 168.8), (-145.7, 164.2), (-147.3, 159.4), (-148.6, 154.6), (-150, 149.8),
        (-151.1, 144.9), (-152.3, 140.1), (-153.2, 135.2), (-153.9, 130.2), (-154.5, 125.3), (-154.7,
        120.3), (-154.6, 115.3), (-154.4, 110.3), (-154, 105.3), (-153.5, 100.4), (-152.7, 95.4), (-151.6,
        90.6), (-150, 85.8), (-148.1, 81.2), (-145.9, 76.7), (-143.4, 72.4), (-140.6, 68.3), (-137.5, 64.4),
        (-134.1, 60.7), (-130.5, 57.2), (-126.8, 53.8), (-122.9, 50.7), (-118.9, 47.8), (-114.8, 44.9),
        (-110.5, 42.4), (-106.1, 40), (-101.7, 37.5), (-97.3, 35.3), (-92.8, 33.1), (-88.1, 31.4), (-83.4,
        29.6), (-78.7, 28), (-73.9, 27), (-69.1, 25.3), (-64.3, 23.6), (-59.4, 22), (-54.5, 20.5), (-49.6,
        19.1), (-44.7, 17.8), (-41.7, 17), (-37, 15.9), (-32.2, 14.8), (-29, 14.2), (-24.5, 13.3), (-19.8,
        12.5), (-14.9, 11.8), (-13.7, 11.6), (-10.4, 11.2), (-5.4, 10.6)],

    # pickups (measured: centres from the screws and poles, the slant from the bridge pickup's poles)
    pickup=dict(l=82.0, w=18.0, pole_d=4.9, pole_spread=52.4, screw_off=38.65),
    pickups_from_scale=(158.8, 99.3, 44.9),   # neck 297.14, middle 237.6, bridge 183.19 from the tail
    bridge_slant_deg=9.9,

    # bridge: the left-handed vintage unit, measured: the plate 71.9 wide, its front 157.5
    # and rear 118.7 (it barely shows behind the saddles), the screw row at v 151.8; six bent-steel
    # saddles from v 125.8 to 144.6, their two height screws at 141.7
    bridge=dict(w=72.0, l=38.8, front_off=19.2, screw_off_front=5.7,
                screw_d=4.0, saddle_w=11.1, saddle_front=144.6, saddle_rear=125.8,
                height_screw_v=141.7, lip_h=9.0, saddle_top_z=12.5, float_gap=1.5, sheet=1.5),

    # pickguard: 1-ply black, beveled, 9 screws visible in the photo; traced (not the guitar_02 guard,
    # which is about 25 mm wider on the bass side). (u, v), counter-clockwise from the bass side of the
    # neck; the bridge cut clears the plate. Smoothed 3 mm, simplified to 0.7 mm.
    guard_t=2.3, guard_plies=1,
    pickguard=[
        (-31.9, 351.4), (-46.4, 355.6), (-50.3, 353.3), (-52.4, 346.3), (-51.9, 337.2), (-49.7, 329.2),
        (-47.3, 311.3), (-46.2, 296.5), (-48.3, 272.3), (-70.6, 211.1), (-73.7, 192.2), (-72.6, 173.8),
        (-70.3, 165.6), (-66.3, 158.1), (-60.6, 151.3), (-55.4, 147.3), (-41.9, 143.7), (-38.8, 144.8),
        (-36.9, 152.6), (-31.1, 157.3), (30.1, 157.4), (35.8, 153.4), (37.7, 146.9), (39.1, 145.1), (62,
        143.6), (80.6, 138.8), (97.7, 128.1), (118.4, 108.8), (127.2, 105.3), (136, 106.1), (141.2, 110.3),
        (144.2, 118), (144.7, 127.8), (142.9, 140.9), (136.9, 162.8), (134.1, 167), (131.3, 174.7), (124.2,
        182.6), (124, 187.9), (118.3, 194.5), (113.3, 204.8), (111.9, 215.5), (103.2, 231.3), (101.2,
        239.6), (101.5, 246.6), (100, 251.6), (100.9, 262.1), (104.3, 271.8), (105.1, 278.3), (118.8,
        312.8), (124.6, 334.1), (125.9, 344.1), (125.6, 354.5), (123.9, 363.7), (120.3, 372.7), (118,
        375.1), (115.8, 373.6), (110.1, 350.7), (104.4, 339.5), (96.3, 330.1), (88.6, 324.2), (75.7, 318.5),
        (60.3, 316.1), (47.6, 318.2), (32.6, 324)],
    guard_screws=[
        (-45.5, 347.6), (-50.3, 248.1), (-49.7, 151), (42.6, 148.7), (134.3, 113.3), (83, 214.1), (96.1,
        235.5), (118.2, 365.7), (35.6, 317.3)],

    # controls (measured): master volume, two tones; 5-way switch, tip in the neck position at [107.3, 186.7]
    knobs=[("volume", 54.6, 176.2), ("tone, neck", 93.5, 155.8), ("tone, middle", 126.1, 128.5)],
    switch=dict(u=111.0, v=180.2, slot_l=22.0, slot_w=3.5, angle_deg=-60.0, tip_l=14.0, tip_w=8.0, ways=5),

    # the arm: his left-handed tremolo puts the socket at the bass end of the plate; the photo shows it as
    # a dark round socket half over the plate's end ([-39.9, 128.2]). Resting across the lower bout towards
    # the jack (as in its case photo, owner-ref-13; the owner agreed 2026-10-23), clear of the rack's cradle.
    arm=dict(u=-37.0, v=128.5, length=140.0, angle_deg=-30.0, socket_r=5.5),

    # the jack: a long oval gold plate, 78.4 x 27, its axis -35.0 degrees off the u axis (55 from
    # the strings), a deep gold cup towards its lower end (centre 6.3 mm down the axis, 50.4 x 18.5,
    # about 10 deep), the socket at the cup's upper end, a screw at each end (-32.6 and 36.4 along the axis)
    jack=dict(u=91.6, v=89.8, l=78.4, w=27.0, angle_deg=-35.0, socket_d=12.5, cup_l=50.4, cup_w=18.5,
              cup_depth=10.0, cup_off=6.3, screw_offs=(-32.6, 36.4)),

    # two strap buttons (no third on the treble horn), gold, on this body's tail and horn tip
    strap_buttons=[(0.0, 10.1, -90.0, "tail"), (-103.8, 452.6, 100.0, "long horn tip")],

    # hardware finishes (keys of the materials in props/guitar_04.py): his gold bridge, saddles,
    # screws, jack, strap buttons and tuners (Gotoh, gold, plastic buttons), a chrome arm with a cream
    # tip, the steel pole pieces; the back plates are approximate (the real back is not in our photos)
    finishes=dict(bridge="gold", saddles="gold", tuners="gold", keys="pearl", string_tree="gold",
                  strap_buttons="gold", jack="gold", screws="gold", neck_plate="gold", arm="chrome",
                  trem_cover="black"),

    # sunburst, three-tone 1963 (sRGB), by distance in from the body edge, mm, as sampled on the
    # photo's surviving finish (aged: the yellow gone amber, the red faded towards brown)
    sunburst=[(0.0, "#140c08"), (14.0, "#1b100b"), (24.0, "#3b130d"), (33.0, "#6a1a0c"), (42.0, "#8f3209"),
              (55.0, "#a85208"), (70.0, "#ba6c0c"), (95.0, "#c98d1f"), (125.0, "#d29c2c")],
    wood=dict(grime="#8f5a2b", grime_dark="#603818", pale="#cfa36a", stain="#a8742f"),

    # the wear, front: where the sunburst survives (even-odd: the smaller loops are bare-wood holes),
    # and where the bare wood shows pale (rubbed clean). Traced from the rectified photo: classified by
    # colour, smoothed 1.6 mm, islands under 30 mm2 dropped, simplified to 0.9 mm (in fit 6's frame). Under
    # the guard, the bridge, the jack and the left-out sticker the finish is taken as surviving. Small chips,
    # scratches and the edge rash are procedural noise in the material, not traced.
    wear_front_finish=[
        [(44.6, 23.7), (33.4, 27.9), (34.5, 30.9), (33.6, 35.7), (26.5, 40.5), (20.8, 39.5), (25.2, 33.6),
         (18.7, 27.8), (16.9, 28.5), (13.8, 34.6), (10.2, 35.2), (1.1, 32.5), (-0.5, 25.9), (-6.3, 27.4),
         (-12.5, 27.1), (-16.4, 30.1), (-19.1, 29), (-20.9, 25.4), (-22.2, 25.5), (-25.1, 29.4), (-33.8,
         27.7), (-40.2, 27.8), (-46.4, 29.9), (-53.1, 28.7), (-71.3, 33.9), (-76.1, 37.8), (-84.7, 41.3),
         (-86, 44), (-67.2, 43.7), (-61.8, 41.7), (-56, 41.5), (-52.8, 39.6), (-48.9, 39.9), (-42.5, 35.5),
         (-39.7, 35.4), (-36.4, 37.7), (-31, 37.6), (-26.1, 40.3), (-21.3, 40.7), (-15.5, 44.9), (-6.5,
         47.2), (-16.1, 48.7), (-22.9, 46.5), (-26.1, 41.8), (-29.6, 40.9), (-38.3, 40.6), (-40.6, 42.1),
         (-47.4, 41.3), (-60.5, 46.9), (-65.3, 46), (-69.1, 49.9), (-76.8, 49.6), (-81, 51.1), (-99.1,
         60.1), (-103.9, 63.5), (-111.8, 72.3), (-111.9, 78.6), (-109, 83.3), (-109, 85.5), (-112.5, 105.5),
         (-109.2, 111.7), (-100.7, 119.2), (-97.9, 131), (-91.5, 133.6), (-88.7, 137.4), (-84.8, 138.8),
         (-81.4, 142.5), (-77.9, 144.1), (-78.4, 148.5), (-82.4, 148.3), (-88.9, 155.3), (-88.5, 164.3),
         (-90, 172.6), (-88.1, 181.2), (-83.8, 190.2), (-82.9, 204.3), (-75.6, 208.3), (-73.8, 208.1), (-73,
         205.4), (-71.9, 206.2), (-47.9, 275.4), (-46.5, 303.3), (-48.5, 321.9), (-53, 341.8), (-50.6,
         352.6), (-45.4, 355.4), (-33.6, 352.2), (45.7, 318.8), (63.1, 316.5), (74.8, 318.1), (81.3, 320.7),
         (88, 323.8), (97.8, 331.7), (105, 340.2), (109.6, 349.3), (115.3, 372), (116.7, 373.8), (118.7,
         373.8), (121.9, 369.1), (124.5, 361.5), (125.9, 342.1), (119.1, 313), (107.2, 284), (104.1, 269.4),
         (101.1, 262.5), (101.4, 238.3), (103.4, 230.8), (112, 216), (113.9, 203.1), (117.9, 195.2), (123.5,
         188.9), (124.9, 181.9), (131.5, 174.4), (138.5, 159.2), (143.9, 135.4), (144.3, 118.1), (139.5,
         108.7), (128.5, 104.2), (130, 100.7), (128.5, 90.9), (126.2, 87.8), (119.8, 85.8), (124.8, 70.1),
         (124.5, 63), (110.4, 62.8), (99.9, 64.9), (91.4, 69), (88.2, 67.9), (92.6, 54.2), (97.9, 47.5),
         (99.3, 47), (102.9, 48.9), (117.9, 48.5), (122.6, 43.3), (122.1, 41.3), (118.3, 38.8), (110.8, 39),
         (111, 33.8), (101.8, 28.5), (89.2, 33.7), (85.2, 32.8), (84, 29.3), (80.2, 27.6), (74.9, 33.6),
         (72.3, 33.6), (70.3, 32.2), (65.9, 32.8), (61, 28.1), (57.4, 29.2)],
        [(-102.3, 347.2), (-104.9, 347.8), (-107.5, 353.4), (-111.4, 353.4), (-112.6, 354.5), (-114.6,
         359.9), (-114.1, 363.8), (-110.3, 370.1), (-110.3, 373.1), (-113.2, 374.6), (-113.3, 378.9),
         (-109.3, 383.1), (-104.6, 382.9), (-105.1, 384.9), (-109, 387.7), (-109, 391.3), (-111.4, 394.1),
         (-110, 398.1), (-110.5, 403), (-114.4, 408.2), (-113, 414.1), (-108.9, 420.8), (-106.3, 419.7),
         (-104.3, 412.3), (-105.7, 400.5), (-105.2, 391.3), (-103.5, 389.1), (-99.1, 389.2), (-95.9, 386.7),
         (-94.5, 382.2), (-91.1, 379.3), (-88.1, 373.1), (-88.1, 370.2), (-91.5, 365.6), (-91.1, 356.1),
         (-93.4, 357.4), (-93.4, 373), (-96.8, 372.9), (-98.7, 365.1), (-98.7, 357.3), (-96.2, 352.4)],
        [(-121.1, 374.1), (-123.4, 375.7), (-125.8, 388.4), (-125.9, 391.9), (-122.8, 395.1), (-119.6,
         392.4), (-119.5, 376.8)],
        [(5.7, 48.5), (14.4, 50.2), (13.5, 59.2), (11.2, 61), (7.6, 59.9), (6.6, 53.6), (2.7, 49.9)],
        [(-105.5, 364.4), (-104, 366), (-103.1, 373.8), (-101.2, 376.8), (-103.8, 380.3), (-108.9, 375),
         (-107, 371.2), (-106.9, 365.9)],
        [(2.2, 38), (13.2, 38.4), (14.4, 41), (4, 41), (0.3, 39), (0.5, 37.8)],
    ],
    wear_front_pale=[
        [(-78.4, 205.9), (-80.6, 207.1), (-83.7, 216.5), (-87.5, 213.1), (-88.8, 213.9), (-86.9, 220.6),
         (-90.7, 222.9), (-92, 226.1), (-95.6, 227.8), (-95.6, 235.1), (-97.1, 238.9), (-94.2, 245.1),
         (-94.7, 250.5), (-92.3, 252.5), (-92.3, 254.4), (-101, 258.6), (-101.1, 278), (-96.1, 272.5),
         (-94.4, 275.7), (-94.9, 279), (-93, 285.4), (-91.4, 287), (-81.9, 289.7), (-86, 292.9), (-94.5,
         296), (-94.5, 303.8), (-90.9, 302.6), (-87.9, 299.7), (-83.1, 304.1), (-72.5, 300.8), (-70.3,
         302.5), (-67.3, 310.6), (-66, 307), (-62.8, 306.3), (-62.1, 302.6), (-59.9, 301.4), (-55.6, 308.3),
         (-50.7, 308.8), (-47.5, 304.7), (-47.4, 288.7), (-50.3, 269.1), (-67.1, 222.9), (-72.4, 216.8),
         (-73.8, 211.9)],
        [(-28.3, 351.3), (-43, 356.5), (-47, 356.4), (-53.2, 353.8), (-57, 367.8), (-54.8, 370), (-41.1,
         369.8), (-29.3, 373), (-28.1, 371.7), (-27, 355)],
        [(-23.2, 13.1), (-25.7, 13.2), (-27.8, 17.2), (-21.8, 17.4), (-18.6, 16)],
        [(62.3, 14.1), (60.6, 15.4), (61.9, 16.5), (68.9, 17.8), (71.5, 17), (70.8, 15.3)],
        [(-56.6, 322), (-57.8, 337.4), (-55.1, 341.6)],
    ],
    # the wear, back (designed: the real back is not in our photos): spline control points, bare wood
    # inside. The belly cut and the bass upper bout rubbed through by the body, a buckle-rash patch,
    # the lower bass edge and the treble horn.
    wear_back=[
        [(-118, 250), (-86, 274), (-62, 312), (-56, 352), (-66, 394), (-88, 436), (-108, 462), (-132, 452),
         (-145, 425), (-150, 392), (-148, 360), (-140, 325), (-128, 290), (-124, 262)],
        [(-52, 62), (-20, 50), (18, 54), (46, 66), (40, 84), (6, 90), (-30, 88), (-56, 78)],
        [(-162, 140), (-150, 150), (-140, 120), (-128, 80), (-108, 48), (-80, 26), (-52, 16), (-60, 4),
         (-110, 12), (-148, 40), (-160, 80)],
        [(84, 352), (104, 362), (118, 380), (122, 398), (106, 404), (90, 392), (82, 372)],
    ],
    edge_wear_mm=5.0,               # the roundover rubbed through all round, broken up by noise
    head_edge_wear_mm=4.0,          # the headstock edge worn to wood and dark
    neck_wear=(30.0, 330.0),        # back of the neck rubbed to bare maple between these (mm from the nut)
)
