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
