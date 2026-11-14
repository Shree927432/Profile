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
    pickups_from_scale=(157.7, 98.2, 41.6),              # neck, middle, bridge centre from the scale line, mm. r4: the
                                                         # 1970 Strat photo (dots, screws, rows free: 295.6, 236.6, 179.1
                                                         # from v 0, +-1.3 to 2.8) and Number One's two photos (296.7 /
                                                         # 295.6, 236.0 / 237.0, 179.6 / 181.1) agree; the mean of the three.
                                                         # r1 was (162, 102, 48), from the MoPOP photo by eye
    bridge_slant_deg=10.0,                               # treble (right) end towards the bridge
    pickup_top_z=(8.0, 7.5, 7.0),

    # pickguard: 3-ply white/black/white, about 2.3 thick, 30 degree bevel, 11 screws.
    # r4 (2026-10-23 night, the owner: "you can fix the strat"): measured on the real guitar's close-up
    # (photo 2 of docs/moodboard/local/hendrix-strat-photos.jpg, a full homography on the 18 poles, 6 pickup
    # screws and 6 bridge screws, 1.33 px rms) and checked on the frontal 1970 Strat. The r1 guard was about
    # 35 mm too wide on the bass side and its screws and knob line did not match either photo. The bridge cut
    # is drawn round this guitar's bridge plate (front at v 158.0). Scripts: video-local/footage/
    # 2026-10-23-guitar-04/measure/g02_*.py; numbers in video-local/footage/2026-10-23-guitar-02/NOTE.md.
    guard_t=2.3,
    pickguard=[
        (-32.2, 354.2), (-54.8, 358.8), (-57, 347.4), (-52.9, 320.6), (-51.2, 293.4), (-50.9, 270.4),
        (-56.1, 248.4), (-64.3, 227.3), (-69.3, 205), (-69.4, 180.7), (-64.5, 158.6), (-54.6, 145.3),
        (-40.7, 140.5), (-39.5, 141.5), (-39, 160), (39, 160), (39.5, 141.5), (49.6, 141.6), (82.8, 133.2),
        (114.4, 116.3), (135.4, 95.3), (142.1, 108.7), (138, 135.7), (131.9, 168.8), (120, 208.3), (110.5,
        239.7), (111.2, 273.2), (117.5, 302.2), (123.9, 336.3), (123.2, 368), (115.1, 382.9), (103.6,
        364.8), (92, 335.3), (73.7, 320), (53.2, 319.6), (34, 326.4), (26.4, 330)],
    guard_screws=[
        (-49.7, 351.2), (32.1, 319.4), (116.7, 370.4), (109.2, 308.5), (-51.6, 247.6), (101, 212.2), (108.2,
        178.5), (122.6, 162.1), (-66.7, 198), (-50.2, 147.3), (40.9, 145.6)],

    # controls (1968): master volume, neck tone, middle tone, 3-way blade switch
    knobs=[("volume", 54.1, 165.7), ("tone, neck", 92.9, 150.4), ("tone, middle", 127.1, 122.4)],   # r4, measured (r1: 64/170, 83.5/136, 103/102)
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

    # Measured (after the owner's review: "body outline is little bit off", "even pickups of guitar are
    # little off", "bridge is different ... jack input is not right") on owner-ref-11 by fit 8: a homography
    # and one radial lens term (the photo is barrel-distorted about 3% at its edges), solved together with
    # the bridge row's and the pickups' positions along the guitar, on the dots, the fret lines and the nut
    # (centre line), the bridge screws and poles across (56.4 and 52.4 mm) and the six posts of the approved
    # r3 headstock: 1.27 px rms. Nothing on the body, the pickups or the bridge's place is assumed.
    # Checked on the real guitar (n1-4.jpg, fit 7, 0.49 px rms): see NOTE.md. Scripts and numbers:
    # video-local/footage/2026-10-23-guitar-04/measure/ (fit8_distortion.py, lens.py, trace_body.py, remap.py).

    # body: Number One's own outline, traced like the small headstock r3: the photo's silhouette in mm,
    # smoothed 2 mm, sampled every 5 mm; the neck-pocket stretch is r2's; the tail (broken by the floor
    # shadow and the strap button in the photo) is one fitted curve. Same frame as guitar_02 (v from
    # guitar_02's tail): this body's tail sits at v -6.5. 323 wide, 458.2 long.
    body=[
        (-1.9, -6.5), (3.1, -6.9), (8.1, -7.2), (12.6, -7.4), (17.6, -7.6), (22.5, -7.6), (27.4, -7.6),
        (32.3, -7.4), (37.2, -7.2), (42.2, -6.9), (47.2, -6.4), (52.2, -5.9), (56.8, -5.3), (61.7, -4.6),
        (66.7, -3.8), (71.7, -2.9), (76.1, -2.9), (79.1, 0.6), (82.4, 3.4), (87.3, 4.5), (92.1, 5.7), (96.9,
        7.1), (101.7, 8.5), (106.4, 10.2), (111.1, 12), (115.6, 14.2), (120, 16.5), (124.2, 19.1), (128.4,
        21.9), (132.3, 25), (136, 28.3), (139.6, 31.8), (142.9, 35.6), (146.1, 39.5), (148.8, 43.6), (151.4,
        47.9), (153.8, 52.3), (156, 56.8), (158, 61.3), (159.7, 66), (161.2, 70.8), (162.2, 75.7), (163.1,
        80.6), (163.6, 85.6), (163.9, 90.5), (163.9, 95.5), (163.8, 100.5), (163.7, 105.5), (163.5, 110.5),
        (163.1, 115.5), (162.5, 120.4), (161.6, 125.4), (160.7, 130.3), (159.4, 135.1), (158.1, 139.9),
        (156.7, 144.7), (155.3, 149.5), (153.8, 154.3), (152.2, 159), (150.6, 163.7), (148.9, 168.4),
        (146.8, 173), (144.9, 177.6), (142.9, 182.2), (140.6, 186.6), (138.4, 191.1), (136.2, 195.6),
        (133.9, 200), (131.6, 204.4), (129.5, 208.9), (127.3, 213.4), (125.1, 217.9), (123, 222.5), (120.8,
        227), (119.1, 231.6), (117.5, 236.4), (116.2, 241.2), (115.3, 246.1), (115, 251.1), (114.6, 256),
        (115.3, 261), (115.8, 266), (116.8, 270.9), (118.3, 275.6), (119.8, 280.4), (121.7, 285), (123.5,
        289.7), (125.4, 294.3), (127.5, 298.8), (129.2, 303.5), (131, 308.2), (132.9, 312.8), (134.4,
        317.6), (135.7, 322.4), (136.9, 327.2), (137.8, 332.1), (138.6, 337.1), (138.9, 342), (139.4, 347),
        (139.3, 352), (139, 357), (138.3, 361.9), (137.3, 366.8), (136.1, 371.7), (134.4, 376.4), (132.5,
        381), (129.2, 384.7), (125.5, 388), (121.2, 390.6), (116.4, 391.6), (111.4, 391), (107.1, 388.6),
        (104, 384.7), (101.7, 380.3), (100.1, 375.5), (98.9, 370.7), (97.8, 365.8), (97, 360.9), (95.3,
        356.2), (93.4, 351.6), (90.7, 347.4), (87.7, 343.4), (83.8, 340.3), (79.8, 337.4), (75.2, 335.4),
        (70.5, 333.8), (65.6, 332.8), (60.7, 332), (55.7, 331.9), (50.7, 332.7), (45.8, 333.5), (40.9,
        334.5), (36.3, 336.3), (31, 330.5), (29, 334), (29, 384), (26, 388), (0, 388.5), (-26, 388), (-29,
        388), (31.9, 338.6), (-32, 380.7), (-35.9, 377.7), (-40.7, 376.2), (-45.4, 374.8), (-50.4, 374.8),
        (-55.4, 375.2), (-60.2, 376.6), (-65, 378), (-69.5, 380), (-73.7, 382.7), (-77.7, 385.7), (-81.4,
        389.1), (-84.6, 392.9), (-87.4, 397), (-89.9, 401.4), (-91.7, 406), (-92.8, 410.8), (-93.8, 415.7),
        (-93.6, 420.7), (-93.7, 425.7), (-93.5, 430.7), (-94.2, 435.6), (-94.1, 440.6), (-95.6, 445.3),
        (-98.8, 449.2), (-103, 451.7), (-107.8, 451.1), (-112.7, 450), (-117.2, 447.9), (-121, 444.7),
        (-124.5, 441.1), (-127.4, 437.1), (-129.9, 432.7), (-132, 428.2), (-132.6, 423.4), (-134.8, 418.9),
        (-136.2, 414.1), (-136.6, 409.2), (-137.4, 404.4), (-137.9, 399.4), (-138.4, 394.5), (-138.2,
        389.5), (-138.1, 384.5), (-137.7, 379.5), (-137, 374.6), (-136.2, 369.6), (-135.3, 364.7), (-134.1,
        359.9), (-132.8, 355.1), (-131.5, 350.2), (-130.2, 345.4), (-128.8, 340.6), (-127.3, 335.8),
        (-125.9, 331.1), (-124.3, 326.3), (-122.8, 321.6), (-121.3, 316.8), (-119.9, 312), (-118.3, 307.3),
        (-116.9, 302.5), (-115.7, 297.6), (-114.4, 292.8), (-113.2, 288), (-112.3, 283), (-111.7, 278.1),
        (-111.5, 273.1), (-111.4, 268.1), (-111.3, 263.1), (-111.8, 258.1), (-112.3, 253.2), (-113.2,
        248.2), (-114.3, 243.4), (-115.7, 238.6), (-117.3, 233.9), (-119, 229.2), (-120.9, 224.5), (-123,
        220), (-124.9, 215.4), (-126.9, 210.8), (-128.8, 206.2), (-130.5, 201.5), (-132.5, 196.9), (-134.5,
        192.3), (-136.5, 187.8), (-138.7, 183.2), (-140.5, 178.6), (-142.6, 174), (-144.3, 169.4), (-146.1,
        164.7), (-148, 160.1), (-149.5, 155.3), (-150.9, 150.5), (-152.5, 145.8), (-153.7, 141), (-154.9,
        136.1), (-156.1, 131.2), (-157, 126.3), (-157.7, 121.4), (-158.4, 116.4), (-158.7, 111.5), (-158.7,
        106.5), (-158.6, 101.5), (-158.5, 96.5), (-157.9, 91.5), (-157.4, 86.5), (-156.6, 81.6), (-155.4,
        76.8), (-153.7, 72.1), (-151.9, 67.4), (-149.7, 63), (-147.2, 58.6), (-144.4, 54.5), (-141.4, 50.5),
        (-138.1, 46.7), (-134.5, 43.2), (-130.9, 39.8), (-127.1, 36.5), (-123.1, 33.6), (-119, 30.6),
        (-114.8, 28), (-110.5, 25.5), (-106.1, 23), (-101.7, 20.7), (-97.3, 18.4), (-92.6, 16.6), (-88,
        14.7), (-83.3, 13.1), (-78.5, 11.5), (-73.7, 10.5), (-68.9, 8.8), (-64.1, 7.1), (-59.2, 5.5),
        (-54.3, 4), (-49.4, 2.5), (-44.8, 1.3), (-41.9, 0.5), (-37.1, -0.6), (-32.4, -1.7), (-29.6, -2.3),
        (-25.1, -3.2), (-20.4, -4), (-15.6, -4.8), (-12.8, -5.2), (-11.8, -5.3), (-6.9, -5.9)],

    # pickups (measured: centres from the screws and poles, the slant from the bridge pickup's poles)
    pickup=dict(l=83.0, w=18.3, pole_d=4.9, pole_spread=52.4, screw_off=38.5),
    pickups_from_scale=(158.4, 97.7, 41.3),   # neck 296.73, middle 235.96, bridge 179.62 from v 0
    bridge_slant_deg=9.8,

    # bridge: the left-handed vintage unit, measured: the plate 73.5 wide, its front 152.7 and rear
    # 111.6 (it barely shows behind the saddles), the screw row at v 146.7; six bent-steel saddles
    # from v 119.2 to 139.1 (on average), their two height screws at 136.0
    bridge=dict(w=73.5, l=41.1, front_off=14.4, screw_off_front=6.0,
                screw_d=4.0, saddle_w=11.1, saddle_front=139.1, saddle_rear=119.2,
                height_screw_v=136.0, lip_h=9.0, saddle_top_z=12.5, float_gap=1.5, sheet=1.5),

    # pickguard: 1-ply black, beveled, 9 screws visible in the photo; traced (not the guitar_02 guard,
    # which is about 25 mm wider on the bass side). (u, v), counter-clockwise from the bass side of the
    # neck; the bridge cut opened 1.5 mm round the measured plate. Smoothed 3 mm, simplified to 0.7 mm.
    guard_t=2.3, guard_plies=1,
    pickguard=[
        (-32.1, 351.3), (-46.6, 355.4), (-50.5, 353), (-52.7, 346), (-52.2, 336.8), (-50, 328.8), (-47.6,
        310.7), (-46.5, 295.7), (-48.6, 271.1), (-71.5, 207.9), (-74.8, 188.3), (-73.7, 169.1), (-71.4,
        160.6), (-67.3, 152.7), (-61.5, 145.7), (-56.3, 141.5), (-42.5, 137.9), (-39.3, 139), (-38.4, 147.2), (-32.0, 154.3), (32.0, 154.3), (38.3, 148.6), (38.8, 141.7), (40.4, 139.9), (63.8, 138.3),
        (82.9, 133.2), (100.6, 121.7), (122.3, 101.1), (131.5, 97.3), (140.6, 98), (145.9, 102.5), (148.9,
        110.7), (149.1, 121.1), (147, 135.1), (140.4, 158.3), (137.4, 162.7), (134.4, 170.8), (127.1,
        179.2), (126.7, 184.7), (120.8, 191.6), (115.6, 202.3), (113.9, 213.4), (104.9, 229.8), (102.8,
        238.3), (103, 245.5), (101.4, 250.6), (102.3, 261.4), (105.6, 271.4), (106.3, 278), (119.9, 313),
        (125.6, 334.6), (126.8, 344.7), (126.5, 355.2), (124.6, 364.5), (121, 373.5), (118.6, 375.9),
        (116.4, 374.4), (110.8, 351.3), (105.1, 340), (97, 330.5), (89.2, 324.5), (76.3, 318.7), (60.8,
        316.3), (47.9, 318.3), (32.8, 324.1)],
    guard_screws=[
        (-45.7, 347.3), (-50.8, 246.4), (-50.5, 145.5), (43.9, 143.6), (138.6, 105.7), (84.5, 212), (97.6,
        234.1), (118.9, 366.5), (35.8, 317.3)],

    # controls (measured): master volume, two tones; 5-way switch, tip in the neck position at [109.6, 183.5]
    knobs=[("volume", 55.9, 172.5), ("tone, neck", 96.0, 151.1), ("tone, middle", 129.9, 122.0)],
    switch=dict(u=113.3, v=177.0, slot_l=22.0, slot_w=3.5, angle_deg=-60.0, tip_l=14.0, tip_w=8.0, ways=5),

    # the arm: his left-handed tremolo puts the socket at the bass end of the plate; the photo shows it as
    # a dark round socket half over the plate's end ([-40.5, 121.5]). Resting across the lower bout towards
    # the jack (as in its case photo, owner-ref-13; the owner agreed 2026-10-23), clear of the rack's cradle.
    arm=dict(u=-37.5, v=121.5, length=140.0, angle_deg=-30.0, socket_r=5.5),

    # the jack: a long oval gold plate, 83.0 x 27.5, its axis -36.1 degrees off the u axis (54 from
    # the strings), a deep gold cup towards its lower end (centre 6.7 mm down the axis, 53.6 x 19,
    # about 10 deep), the socket at the cup's upper end, a screw at each end (-34.6 and 38.6 along the axis)
    jack=dict(u=95.0, v=80.5, l=83.0, w=27.5, angle_deg=-36.1, socket_d=12.5, cup_l=53.6, cup_w=19.0,
              cup_depth=10.0, cup_off=6.7, screw_offs=(-34.6, 38.6)),

    # two strap buttons (no third on the treble horn), gold, on this body's tail and horn tip
    strap_buttons=[(0.0, -6.5, -90.0, "tail"), (-103.0, 451.7, 100.0, "long horn tip")],

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
    # colour, smoothed 1.6 mm, islands under 30 mm2 dropped, simplified to 0.9 mm (moved into fit 8's
    # frame). Under the guard, the bridge, the jack and the left-out sticker the finish is taken as
    # surviving. Small chips, scratches and the edge rash are procedural noise in the material, not traced.
    wear_front_finish=[
        [(47, 8.7), (35.3, 13.3), (36.5, 16.6), (35.4, 21.9), (28.1, 27.2), (22.2, 26.1), (26.8, 19.6), (20,
         13.1), (18.1, 13.9), (14.9, 20.6), (11.2, 21.2), (1.7, 18.3), (0.1, 10.9), (-6, 12.6), (-12.4,
         12.2), (-16.5, 15.5), (-19.3, 14.3), (-21.1, 10.3), (-22.5, 10.3), (-25.5, 14.6), (-34.6, 12.6),
         (-41.2, 12.8), (-47.6, 15), (-54.6, 13.5), (-73.5, 19), (-78.4, 23.2), (-87.3, 26.9), (-88.6,
         29.8), (-69.1, 29.9), (-63.5, 27.7), (-57.5, 27.6), (-54.1, 25.5), (-50.1, 26), (-43.6, 21.2),
         (-40.6, 21.1), (-37.1, 23.7), (-31.5, 23.6), (-26.5, 26.7), (-21.5, 27.1), (-15.5, 31.7), (-6.2,
         34.4), (-16.1, 35.9), (-23.1, 33.4), (-26.5, 28.3), (-30.1, 27.3), (-39.1, 26.9), (-41.5, 28.5),
         (-48.5, 27.5), (-62.1, 33.4), (-67.1, 32.4), (-71, 36.6), (-79, 36.2), (-83.3, 37.8), (-102, 47.2),
         (-106.9, 50.8), (-115, 60.3), (-115, 67.1), (-112, 72.2), (-112, 74.7), (-115.3, 96.1), (-111.8,
         102.8), (-103, 111), (-100, 123.6), (-93.4, 126.4), (-90.4, 130.5), (-86.5, 132), (-82.9, 136.1),
         (-79.3, 137.8), (-79.8, 142.5), (-83.9, 142.2), (-90.6, 149.5), (-90, 159), (-91.5, 167.6), (-89.5,
         176.6), (-85.1, 186.1), (-84.1, 200.7), (-76.5, 205), (-74.8, 204.8), (-74, 202), (-72.8, 202.8),
         (-48.2, 274.2), (-46.8, 302.6), (-48.8, 321.4), (-53.3, 341.4), (-50.8, 352.3), (-45.6, 355.2),
         (-33.8, 352.1), (46, 318.9), (63.6, 316.7), (75.4, 318.4), (81.9, 321), (88.6, 324.1), (98.5,
         332.1), (105.7, 340.7), (110.3, 349.9), (115.9, 372.8), (117.2, 374.6), (119.3, 374.6), (122.6,
         369.9), (125.2, 362.3), (126.8, 342.7), (120.2, 313.2), (108.5, 283.7), (105.4, 268.9), (102.4,
         261.8), (103, 237), (105.2, 229.3), (114, 213.9), (116.2, 200.6), (120.4, 192.3), (126.2, 185.7),
         (127.8, 178.5), (134.7, 170.5), (142.1, 154.4), (148.2, 129.3), (149, 110.8), (144.1, 100.7),
         (132.9, 96.1), (134.5, 92.2), (133, 81.7), (130.8, 78.4), (124.2, 76.3), (129.7, 59.2), (129.5,
         51.4), (114.8, 51.4), (103.9, 53.8), (95, 58.3), (91.7, 57.1), (96.5, 42.1), (102.1, 34.7), (103.5,
         34.2), (107.3, 36.2), (123, 35.7), (128, 29.8), (127.5, 27.7), (123.5, 25), (115.8, 25.2), (116.1,
         19.6), (106.5, 13.8), (93.3, 19.6), (89.2, 18.6), (88, 14.7), (84, 12.9), (78.4, 19.5), (75.7,
         19.6), (73.6, 18), (69.1, 18.7), (64, 13.5), (60.3, 14.7)],
        [(-102.9, 346.3), (-105.6, 347), (-108.2, 352.6), (-112.1, 352.5), (-113.3, 353.6), (-115.3, 359),
         (-114.8, 363), (-111, 369.3), (-111, 372.3), (-113.9, 373.8), (-113.9, 378.1), (-109.8, 382.4),
         (-105.2, 382.3), (-105.7, 384.2), (-109.6, 387), (-109.6, 390.6), (-112, 393.4), (-110.6, 397.4),
         (-111.1, 402.3), (-115, 407.4), (-113.6, 413.3), (-109.4, 420.1), (-106.8, 419.1), (-104.8, 411.7),
         (-106.2, 399.9), (-105.7, 390.7), (-104, 388.5), (-99.5, 388.6), (-96.4, 386.1), (-94.9, 381.6),
         (-91.5, 378.7), (-88.6, 372.6), (-88.6, 369.6), (-92, 365), (-91.7, 355.5), (-93.9, 356.7), (-93.9,
         372.4), (-97.3, 372.3), (-99.3, 364.4), (-99.3, 356.5), (-96.8, 351.7)],
        [(-121.8, 373.2), (-124.1, 374.8), (-126.5, 387.5), (-126.6, 391), (-123.5, 394.2), (-120.3, 391.6),
         (-120.2, 375.9)],
        [(6.4, 35.9), (15.5, 37.8), (14.5, 47.7), (12.1, 49.6), (8.4, 48.4), (7.4, 41.5), (3.4, 37.4)],
        [(-106.1, 363.6), (-104.6, 365.2), (-103.7, 373.1), (-101.7, 376.1), (-104.4, 379.6), (-109.5,
         374.3), (-107.6, 370.4), (-107.5, 365.1)],
        [(2.9, 24.4), (14.2, 24.9), (15.6, 27.7), (4.7, 27.7), (0.9, 25.5), (1.1, 24.1)],
    ],
    wear_front_pale=[
        [(-79.5, 202.5), (-81.6, 203.7), (-84.7, 213.4), (-88.7, 209.8), (-89.9, 210.6), (-88, 217.6),
         (-91.9, 220), (-93.1, 223.2), (-96.7, 224.9), (-96.7, 232.4), (-98.2, 236.3), (-95.3, 242.7),
         (-95.7, 248.3), (-93.3, 250.3), (-93.3, 252.3), (-102.1, 256.5), (-102.1, 276.2), (-97, 270.7),
         (-95.3, 274), (-95.7, 277.3), (-93.8, 283.9), (-92.1, 285.6), (-82.6, 288.5), (-86.7, 291.6),
         (-95.3, 294.7), (-95.3, 302.6), (-91.6, 301.4), (-88.6, 298.5), (-83.8, 303), (-73, 299.8), (-70.9,
         301.5), (-67.7, 309.8), (-66.4, 306.2), (-63.2, 305.4), (-62.5, 301.7), (-60.3, 300.6), (-56,
         307.6), (-51, 308.2), (-47.8, 304), (-47.8, 287.7), (-50.7, 267.8), (-67.9, 220.2), (-73.3, 213.8),
         (-74.8, 208.8)],
        [(-28.5, 351.2), (-43.3, 356.3), (-47.2, 356.2), (-53.5, 353.5), (-57.3, 367.5), (-55.1, 369.8),
         (-41.3, 369.6), (-29.5, 372.9), (-28.2, 371.7), (-27.2, 354.9)],
        [(-23.5, -3.4), (-26.1, -3.3), (-28.3, 1.2), (-22.1, 1.4), (-18.8, -0.1)],
        [(65.6, -2), (63.8, -0.5), (65.1, 0.7), (72.3, 2.1), (75.1, 1.2), (74.4, -0.7)],
        [(-57, 321.4), (-58.2, 336.9), (-55.4, 341.2)],
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


# ---------------------------------------------------------------------------
# guitar_01: B.B. King's "Lucille" (blues, 1950s on the wall's timeline), on the wall hook, left.
# The Gibson Lucille as built from 1980 (the 1997 guitar of the National Music Museum photo): an
# ES-355 thinline semi-hollow body WITHOUT f-holes, gloss black all over, multi-ply bound top, back,
# board and headstock, a bound ebony board with pearl blocks, two humbuckers in gold covers on black
# rings, a gold tune-o-matic and a gold fine-tuner tailpiece, a Varitone (a gold plate and a pointer
# knob), four black knurled knobs, the toggle, two output jacks on the rim, a tortoise guard.
# No logos, wordmark, crown or "Lucille" on the headstock or the truss-rod cover, no signature.
# Measured on the Commons ES-355 cut-out (docs/moodboard/local/lucille/es355-cutout.png, same body,
# neck, head and guard): the nut and frets 1-20 fitted to a pitched camera (1 px rms, 3.58 px/mm);
# Lucille's own layout (Varitone, jacks, side strap button) on lucille-front.jpg, scaled to the same
# knobs. Scripts and numbers: video-local/footage/2026-11-12-guitars/measure/g01_*.py and *.json.
# Checks: the lower bout 405.2 mm (Gibson: 16 in, 406.4), the body 485 long (19 in nominal), the nut
# 42.2 in the photo (1 11/16 in), the bridge's saddles 1-4 mm behind the fitted scale line.
# ---------------------------------------------------------------------------
_SCALE_01 = 628.65                 # 24.75 in
GUITAR_01 = dict(
    scale=_SCALE_01, frets=22, v_nut=886.6,
    v_junction=457.6,              # the body's top edge under the neck (the 20th fret)
    neck_angle_deg=3.0,            # the neck tilted back about the junction
    board_above_body=10.0,         # fretboard crown over the rim's top edge, at the junction
    v_board_end=426.0,             # the board stops just before the neck pickup's ring
    body_t=44.5,                   # rims, 1 3/4 in
    arch_top=6.0, arch_back=5.0, arch_run=90.0,   # the pressed laminated top and back: rise, mm in from the edge
    # body: traced, both halves averaged (left and right 1-6 mm apart in the photo), smoothed 2 mm,
    # sampled every 5 mm; (u, v) counter-clockwise from the tail centre. Under the neck it is the
    # straight edge at the junction.
    body=[
        (0.0, 0.0), (5.0, 0.1), (9.1, 0.3), (13.4, 0.6), (17.8, 0.8), (22.1, 1.1), (26.5, 1.4), (30.8, 1.8),
        (35.1, 2.3), (39.5, 2.8), (43.8, 3.4), (48.1, 4.0), (52.4, 4.8), (56.7, 5.5), (61.0, 6.3), (65.2, 7.3),
        (69.4, 8.3), (73.7, 9.4), (77.9, 10.6), (82.1, 11.8), (86.2, 13.1), (90.3, 14.5), (94.4, 16.1),
        (98.4, 17.7), (102.4, 19.4), (106.4, 21.2), (110.3, 23.2), (114.2, 25.2), (117.9, 27.4), (121.6, 29.7),
        (125.3, 32.0), (128.9, 34.5), (132.5, 37.0), (136.0, 39.6), (139.4, 42.3), (142.8, 45.0),
        (146.1, 47.8), (149.4, 50.7), (152.6, 53.6), (155.8, 56.6), (158.9, 59.7), (161.8, 62.9),
        (164.7, 66.2), (167.5, 69.5), (170.2, 72.9), (172.8, 76.4), (175.3, 80.0), (177.7, 83.7),
        (179.9, 87.4), (182.1, 91.2), (184.2, 95.0), (186.2, 98.9), (188.1, 102.8), (189.9, 106.8),
        (191.5, 110.8), (193.1, 114.9), (194.5, 119.0), (195.8, 123.2), (197.0, 127.3), (198.1, 131.6),
        (199.1, 135.8), (200.0, 140.1), (200.7, 144.4), (201.3, 148.7), (201.7, 153.0), (202.2, 157.4),
        (202.4, 161.7), (202.6, 166.1), (202.6, 170.4), (202.5, 174.8), (202.2, 179.1), (201.9, 183.5),
        (201.4, 187.8), (200.8, 192.1), (200.1, 196.4), (199.3, 200.7), (198.3, 205.0), (197.2, 209.2),
        (196.1, 213.4), (195.0, 217.6), (193.8, 221.8), (192.4, 225.9), (191.0, 230.1), (189.5, 234.1),
        (187.9, 238.2), (186.1, 242.1), (184.1, 246.0), (182.0, 249.8), (179.7, 253.6), (177.5, 257.3),
        (175.1, 261.0), (172.7, 264.6), (170.1, 268.1), (167.4, 271.5), (164.6, 274.9), (161.8, 278.2),
        (158.9, 281.4), (155.9, 284.6), (152.9, 287.8), (150.0, 291.0), (146.9, 294.1), (143.9, 297.2),
        (140.8, 300.3), (137.7, 303.4), (134.7, 306.6), (131.7, 309.7), (128.8, 312.9), (125.9, 316.2),
        (123.1, 319.6), (120.6, 323.1), (118.3, 326.8), (116.4, 330.7), (114.9, 334.8), (114.0, 339.1),
        (113.6, 343.4), (113.8, 347.8), (114.5, 352.1), (115.5, 356.3), (116.7, 360.5), (118.1, 364.6),
        (119.8, 368.7), (121.6, 372.6), (123.4, 376.6), (125.3, 380.5), (127.2, 384.4), (129.0, 388.4),
        (130.8, 392.4), (132.6, 396.3), (134.3, 400.4), (135.8, 404.4), (137.2, 408.6), (138.3, 412.8),
        (139.3, 417.0), (140.1, 421.3), (140.7, 425.6), (141.1, 430.0), (141.4, 434.3), (141.4, 438.7),
        (141.2, 443.0), (140.7, 447.3), (139.9, 451.6), (138.9, 455.9), (137.5, 460.0), (135.9, 464.0),
        (133.9, 467.9), (131.6, 471.6), (129.0, 475.1), (125.9, 478.2), (122.5, 480.8), (118.6, 482.9),
        (114.5, 484.4), (110.2, 485.1), (105.9, 485.1), (101.6, 484.3), (97.5, 482.8), (93.6, 480.9),
        (89.9, 478.6), (86.4, 476.1), (82.9, 473.3), (79.6, 470.6), (76.2, 467.8), (72.8, 465.1),
        (69.2, 462.6), (65.5, 460.3), (61.6, 458.5), (57.4, 457.1), (53.1, 456.8), (46.0, 457.2),
        (38.0, 457.6), (30.0, 457.6), (0.0, 457.6), (-30.0, 457.6), (-38.0, 457.6), (-46.0, 457.2),
        (-53.1, 456.8), (-57.4, 457.1), (-61.6, 458.5), (-65.5, 460.3), (-69.2, 462.6), (-72.8, 465.1),
        (-76.2, 467.8), (-79.6, 470.6), (-82.9, 473.3), (-86.4, 476.1), (-89.9, 478.6), (-93.6, 480.9),
        (-97.5, 482.8), (-101.6, 484.3), (-105.9, 485.1), (-110.2, 485.1), (-114.5, 484.4), (-118.6, 482.9),
        (-122.5, 480.8), (-125.9, 478.2), (-129.0, 475.1), (-131.6, 471.6), (-133.9, 467.9), (-135.9, 464.0),
        (-137.5, 460.0), (-138.9, 455.9), (-139.9, 451.6), (-140.7, 447.3), (-141.2, 443.0), (-141.4, 438.7),
        (-141.4, 434.3), (-141.1, 430.0), (-140.7, 425.6), (-140.1, 421.3), (-139.3, 417.0), (-138.3, 412.8),
        (-137.2, 408.6), (-135.8, 404.4), (-134.3, 400.4), (-132.6, 396.3), (-130.8, 392.4), (-129.0, 388.4),
        (-127.2, 384.4), (-125.3, 380.5), (-123.4, 376.6), (-121.6, 372.6), (-119.8, 368.7), (-118.1, 364.6),
        (-116.7, 360.5), (-115.5, 356.3), (-114.5, 352.1), (-113.8, 347.8), (-113.6, 343.4), (-114.0, 339.1),
        (-114.9, 334.8), (-116.4, 330.7), (-118.3, 326.8), (-120.6, 323.1), (-123.1, 319.6), (-125.9, 316.2),
        (-128.8, 312.9), (-131.7, 309.7), (-134.7, 306.6), (-137.7, 303.4), (-140.8, 300.3), (-143.9, 297.2),
        (-146.9, 294.1), (-150.0, 291.0), (-152.9, 287.8), (-155.9, 284.6), (-158.9, 281.4), (-161.8, 278.2),
        (-164.6, 274.9), (-167.4, 271.5), (-170.1, 268.1), (-172.7, 264.6), (-175.1, 261.0), (-177.5, 257.3),
        (-179.7, 253.6), (-182.0, 249.8), (-184.1, 246.0), (-186.1, 242.1), (-187.9, 238.2), (-189.5, 234.1),
        (-191.0, 230.1), (-192.4, 225.9), (-193.8, 221.8), (-195.0, 217.6), (-196.1, 213.4), (-197.2, 209.2),
        (-198.3, 205.0), (-199.3, 200.7), (-200.1, 196.4), (-200.8, 192.1), (-201.4, 187.8), (-201.9, 183.5),
        (-202.2, 179.1), (-202.5, 174.8), (-202.6, 170.4), (-202.6, 166.1), (-202.4, 161.7), (-202.2, 157.4),
        (-201.7, 153.0), (-201.3, 148.7), (-200.7, 144.4), (-200.0, 140.1), (-199.1, 135.8), (-198.1, 131.6),
        (-197.0, 127.3), (-195.8, 123.2), (-194.5, 119.0), (-193.1, 114.9), (-191.5, 110.8), (-189.9, 106.8),
        (-188.1, 102.8), (-186.2, 98.9), (-184.2, 95.0), (-182.1, 91.2), (-179.9, 87.4), (-177.7, 83.7),
        (-175.3, 80.0), (-172.8, 76.4), (-170.2, 72.9), (-167.5, 69.5), (-164.7, 66.2), (-161.8, 62.9),
        (-158.9, 59.7), (-155.8, 56.6), (-152.6, 53.6), (-149.4, 50.7), (-146.1, 47.8), (-142.8, 45.0),
        (-139.4, 42.3), (-136.0, 39.6), (-132.5, 37.0), (-128.9, 34.5), (-125.3, 32.0), (-121.6, 29.7),
        (-117.9, 27.4), (-114.2, 25.2), (-110.3, 23.2), (-106.4, 21.2), (-102.4, 19.4), (-98.4, 17.7),
        (-94.4, 16.1), (-90.3, 14.5), (-86.2, 13.1), (-82.1, 11.8), (-77.9, 10.6), (-73.7, 9.4), (-69.4, 8.3),
        (-65.2, 7.3), (-61.0, 6.3), (-56.7, 5.5), (-52.4, 4.8), (-48.1, 4.0), (-43.8, 3.4), (-39.5, 2.8),
        (-35.1, 2.3), (-30.8, 1.8), (-26.5, 1.4), (-22.1, 1.1), (-17.8, 0.8), (-13.4, 0.6), (-9.1, 0.3),
        (-5.0, 0.1),],

    binding_top=(("white", 1.6), ("black", 0.4), ("white", 0.4), ("black", 0.4), ("white", 0.4), ("black", 0.4)),
    binding_side_h=6.5, binding_back=(("white", 1.6), ("black", 0.4), ("white", 0.4)), binding_back_h=4.5,

    # neck: one-piece mahogany, black; 12 in radius bound ebony board; 22 medium-jumbo frets
    nut_w=42.9, w12=52.6, nut_l=4.8, radius=304.8, board_t=6.4, board_binding=1.5,
    neck_t1=21.0, neck_t12=23.5, fret_wire=(2.5, 1.15),
    blocks=(1, 3, 5, 7, 9, 12, 15, 17, 19, 21), block_len_frac=0.6, block_margin=5.5,

    # headstock: 17 degrees back, 14.5 thick, black face, bound; the outline traced (the face's
    # foreshortening undone), both sides averaged; (a, b), b from the nut. No inlay, no text.
    head_angle_deg=17.0, head_t=14.5, head_drop=8.0,   # face this far under the board's crown at the nut
    headstock=[(21.45, 0), (21.5, 10), (21.9, 16), (23.0, 21), (25.2, 26), (28.3, 30), (31.8, 33.5),
               (34.6, 37), (35.8, 42), (36.0, 60), (36.1, 85), (36.4, 110), (37.4, 128), (38.6, 142),
               (39.8, 152), (40.5, 158), (40.6, 161.5), (39.0, 163.6), (34.0, 163.3), (30.0, 163.6),
               (26.0, 164.2), (22.0, 165.2), (18.0, 167.0), (14.0, 169.1), (10.0, 170.8), (6.0, 171.4),
               (3.0, 170.8), (0.0, 169.7),
               (-3.0, 170.8), (-6.0, 171.4), (-10.0, 170.8), (-14.0, 169.1), (-18.0, 167.0),
               (-22.0, 165.2), (-26.0, 164.2), (-30.0, 163.6), (-34.0, 163.3), (-39.0, 163.6),
               (-40.6, 161.5), (-40.5, 158), (-39.8, 152), (-38.6, 142), (-37.4, 128), (-36.4, 110),
               (-36.1, 85), (-36.0, 60), (-35.8, 42), (-34.6, 37), (-31.8, 33.5), (-28.3, 30),
               (-25.2, 26), (-23.0, 21), (-21.9, 16), (-21.5, 10), (-21.45, 0)],
    tuner_posts=[(-23.9, 62.0), (-23.9, 100.0), (-23.9, 137.0), (23.9, 62.0), (23.9, 100.0), (23.9, 137.0)],
    post_d=6.0, post_h=13.0, bushing_d=10.5,
    truss_cover=dict(top_b=57.7, bottom_b=6.7, w_bottom=25.5, w_mid=16.0, t=1.6),
    hook=dict(gap=46.0),

    # strings: low E on the viewer's left; .010 to .046 (his were heavier on the wound side)
    strings=("E6", "A", "D", "G", "B", "E1"), gauges=(0.046, 0.036, 0.026, 0.017, 0.013, 0.010),
    nut_spread=35.0, bridge_spread=52.0, saddle_back=(3.8, 3.0, 2.2, 2.6, 1.6, 0.6),
    string_over_board=1.6,          # above the last fret at the body (the action), mm

    # hardware (measured centres, v from the tail edge)
    pickups=dict(neck=401.0, bridge=295.5, cover=(70.0, 38.5), ring=(88.0, 46.0), cover_h=7.0, under_string=3.2),
    tom=dict(v=252.4, l=82.0, w=10.0, h=8.0, post_span=74.0, wheel_d=10.5),
    tailpiece=dict(v=210.9, l=96.0, w=15.0, h=9.0, stud_span=82.0, gap=4.0),
    toggle=(93.7, 207.4), knobs=[(161.6, 202.0), (109.1, 161.6), (179.7, 136.6), (130.0, 97.7)],
    knob=dict(d=22.0, h=17.0), varitone=dict(u=81.7, v=122.0, plate_d=38.0),
    jacks_v=(106.0, 69.0), jack_d=19.0,   # on the treble rim
    strap_buttons_v=(0.0,),               # the tail; the other is on the back of the neck heel
    guard_bracket_v=305.0,                # the guard's gold bracket, screwed to the treble rim
    guard_z=12.0, guard_t=2.3, guard_binding=1.4,
    # pickguard: the outer edge of its white binding, traced; the inner edge straight along the strings
    pickguard=[
        (107.2, 237.3), (99.6, 237.9), (92.6, 240.3), (86.0, 243.4), (79.4, 246.6), (72.5, 249.2),
        (65.1, 250.7), (57.3, 251.0), (49.6, 250.2), (41.9, 249.6), (33.9, 249.6), (29.7, 253.5),
        (29.6, 261.4), (29.6, 269.4), (29.6, 277.4), (29.6, 285.4), (29.6, 293.4), (29.6, 301.4),
        (29.6, 309.4), (29.6, 317.4), (29.6, 325.4), (29.6, 333.4), (29.5, 341.4), (29.5, 349.4),
        (29.5, 357.4), (29.5, 365.4), (29.5, 373.4), (29.5, 381.4), (29.5, 389.4), (29.5, 397.4),
        (29.5, 405.4), (29.4, 413.4), (29.3, 421.4), (29.0, 428.9), (29.4, 436.2), (35.4, 436.1),
        (42.6, 434.2), (49.8, 432.3), (56.8, 429.9), (63.2, 426.3), (68.3, 420.9), (71.5, 414.2),
        (73.6, 407.1), (75.0, 399.6), (76.3, 392.2), (78.2, 384.9), (80.4, 377.9), (83.3, 371.0),
        (86.5, 364.4), (90.1, 357.9), (93.6, 351.3), (97.2, 344.8), (100.9, 338.3), (104.5, 331.8),
        (108.4, 325.4), (111.5, 318.9), (114.9, 312.4), (118.0, 305.7), (120.9, 298.9), (123.5, 291.9),
        (125.8, 284.9), (127.8, 277.7), (129.1, 270.2), (129.4, 262.4), (128.3, 255.1), (125.4, 248.3),
        (120.4, 242.6), (114.0, 238.8),],
)


# ---------------------------------------------------------------------------
# guitar_03: Jimmy Page's 1971 double-neck (hard rock, 1970s; on the wall, right), the EDS-1275 type:
# a solid mahogany SG-type body with bevelled edges in cherry, a 12-string neck (viewer's left as it hangs)
# and a 6-string neck, both 24.75 in scale, 20 frets, bound rosewood boards with double parallelogram
# pearl markers, four humbuckers in nickel covers on black rings, two tune-o-matics, a fixed 12-string
# tailpiece and a stop bar, a black guard with a white edge, four black knobs, the neck selector between
# the necks, the pickup selector on the treble horn, the jack on the top. No logos on the heads.
# Measured on the near-frontal Commons photo docs/moodboard/local/double-neck/page-hrc.jpg (the real
# guitar at the Hard Rock Cafe Hollywood): both necks' frets 1-21 fitted to a camera pitched about 28
# degrees (0.8 px rms each), across from the 6-string nut (1 11/16 in); checked by the four pickup covers,
# 70.4 mm each (70 mm). The 6-string headstock is the Gibson pattern measured for Lucille; the 12-string
# head's length is scaled by the same factor that brings the 6's to Lucille's (the face's extra tilt).
# Frame: u from the BODY's centre line (the necks are not centred on it: 12 at -77.0, 6 at +65.4, as
# measured), v from the tail edge. The nut position is set by the bridges (the traced tail edge was 3 mm
# off); scripts and numbers: video-local/footage/2026-11-12-guitars/measure/g03_*.py, *.json.
# ---------------------------------------------------------------------------
GUITAR_03 = dict(
    body_t=38.0,                    # 1.5 in, mahogany
    bevel=((24.0, 0.0), (18.0, -0.8), (11.0, -4.2), (4.0, -8.0), (1.0, -10.0), (0.0, -11.5)),   # (inset, z) top
    bevel_back=((0.0, -30.5), (1.0, -32.0), (4.0, -34.6), (12.0, -37.3), (20.0, -38.0)),
    necks=(-77.0, 65.4),            # u of the 12-string and the 6-string centre lines
    v_nut=792.5, v_junction=398.0,
    body=[
        (0.0, 0.0), (20.0, 2.3), (40.0, 3.4), (60.0, 4.7), (80.0, 6.9), (105.5, 12.0), (128.8, 20.0),
        (144.4, 28.0), (156.2, 36.0), (165.4, 44.0), (172.7, 52.0), (178.7, 60.0), (184.1, 68.0),
        (188.1, 76.0), (191.7, 84.0), (194.6, 92.0), (196.9, 100.0), (198.6, 108.0), (199.8, 116.0),
        (200.5, 124.0), (200.5, 132.0), (200.3, 140.0), (199.4, 148.0), (197.6, 156.0), (195.1, 164.0),
        (191.9, 172.0), (188.0, 180.0), (183.2, 188.0), (177.8, 196.0), (172.0, 204.0), (166.4, 212.0),
        (161.7, 220.0), (158.6, 228.0), (157.0, 236.0), (157.1, 244.0), (158.6, 252.0), (161.4, 260.0),
        (165.3, 268.0), (169.4, 276.0), (173.2, 284.0), (176.5, 292.0), (179.4, 300.0), (181.5, 308.0),
        (183.0, 316.0), (184.0, 324.0), (184.6, 332.0), (184.5, 340.0), (184.2, 348.0), (183.4, 356.0),
        (182.1, 364.0), (180.2, 372.0), (178.2, 380.0), (175.0, 390.0), (168.0, 400.0), (162.0, 407.5),
        (158.0, 411.0), (152.0, 406.0), (146.0, 400.0), (137.0, 391.5), (129.0, 386.5), (121.0, 385.8),
        (112.0, 389.0), (103.0, 393.5), (100.0, 397.5), (65.4, 398.0), (36.0, 397.0), (29.0, 391.0),
        (17.0, 386.5), (0.0, 385.0), (-20.0, 386.5), (-35.0, 390.0), (-44.0, 394.0), (-51.6, 397.0),
        (-77.0, 398.0), (-114.0, 397.5), (-118.0, 390.0), (-125.0, 386.0), (-134.0, 386.5), (-143.0, 392.0),
        (-150.0, 399.0), (-157.0, 405.0), (-163.0, 409.0), (-168.0, 400.0), (-175.0, 390.0), (-178.2, 380.0),
        (-180.2, 372.0), (-182.1, 364.0), (-183.4, 356.0), (-184.2, 348.0), (-184.5, 340.0), (-184.6, 332.0),
        (-184.0, 324.0), (-183.0, 316.0), (-181.5, 308.0), (-179.4, 300.0), (-176.5, 292.0), (-173.2, 284.0),
        (-169.4, 276.0), (-165.3, 268.0), (-161.4, 260.0), (-158.6, 252.0), (-157.1, 244.0), (-157.0, 236.0),
        (-158.6, 228.0), (-161.7, 220.0), (-166.4, 212.0), (-172.0, 204.0), (-177.8, 196.0), (-183.2, 188.0),
        (-188.0, 180.0), (-191.9, 172.0), (-195.1, 164.0), (-197.6, 156.0), (-199.4, 148.0), (-200.3, 140.0),
        (-200.5, 132.0), (-200.5, 124.0), (-199.8, 116.0), (-198.6, 108.0), (-196.9, 100.0), (-194.6, 92.0),
        (-191.7, 84.0), (-188.1, 76.0), (-184.1, 68.0), (-178.7, 60.0), (-172.7, 52.0), (-165.4, 44.0),
        (-156.2, 36.0), (-144.4, 28.0), (-128.8, 20.0), (-105.5, 12.0), (-80.0, 6.9), (-60.0, 4.7),
        (-40.0, 3.4), (-20.0, 2.3),],
    pickguard=[
        (-39.7, 385.1), (-28.5, 372.2), (-6.6, 365.8), (15.0, 370.1), (27.0, 381.6), (106.3, 382.5),
        (132.3, 377.3), (157.9, 365.8), (168.1, 351.0), (162.3, 313.5), (154.5, 277.1), (148.9, 237.8),
        (144.6, 210.9), (137.2, 197.7), (124.8, 191.3), (102.4, 186.0), (70.0, 183.1), (33.6, 182.3),
        (19.5, 179.0), (16.0, 167.9), (17.1, 147.8), (20.1, 129.9), (20.5, 98.2), (14.7, 88.4), (-0.8, 85.0),
        (-20.3, 87.8), (-27.6, 94.7), (-30.0, 147.8), (-27.5, 167.9), (-30.4, 184.6), (-34.0, 222.3),
        (-37.0, 301.3),],
    guard_t=2.4, guard_plies=(("black", 0.0), ("white", 0.6), ("black", 1.2)),
    # controls (measured): knobs, the neck selector between the necks, the pickup selector, the jack
    knobs=[(147.9, 177.1), (174.7, 131.7), (137.7, 128.1), (164.8, 87.8)], knob=dict(d=21.0, h=17.0),
    neck_selector=(-6.7, 121.7), pickup_toggle=(138.1, 356.4), jack=(129.3, 75.7),
    strap_buttons=[(0.0, 0.0, -90.0), (-160.0, 395.0, 100.0)],
)

# the two necks, as Lucille's builder reads a guitar (u local to each neck's centre line)
_SG_NECK = dict(GUITAR_01)
_SG_NECK.update(
    frets=20, v_nut=792.5, v_junction=398.0, neck_angle_deg=3.0, board_above_body=10.5, v_board_end=349.5,
    body_t=38.0, arch_top=0.0, arch_back=0.0, w12=53.5, radius=304.8, board_t=6.4, board_binding=1.5,
    neck_t1=21.5, neck_t12=24.0, fret_wire=(2.3, 1.1), blocks=(1, 3, 5, 7, 9, 12, 15, 17, 19),
    block_len_frac=0.62, block_margin=4.0, inlay="double_parallelogram",
    pickups=dict(neck=325.1, bridge=206.5, cover=(70.0, 38.5), ring=(88.0, 46.0), cover_h=7.0, under_string=3.0),
    tailpiece=dict(v=117.7, l=86.0, w=13.0, h=9.0, stud_span=82.0, gap=3.5),
)
GUITAR_03_N6 = dict(_SG_NECK)
GUITAR_03_N6.update(nut_w=42.9, tom=dict(v=166.1, l=82.0, w=10.0, h=8.0, post_span=74.0, wheel_d=10.5),
                    tail_kind="stopbar")
GUITAR_03_N12 = dict(_SG_NECK)
GUITAR_03_N12.update(
    nut_w=44.0, nut_spread=36.0, bridge_spread=53.0,
    tom=dict(v=167.2, l=86.0, w=10.0, h=8.0, post_span=78.0, wheel_d=10.5), tail_kind="fixed12",
    # courses low to high; each course its octave (or unison) partner on the bass side, 2.4 mm apart at the
    # nut, 3.6 at the saddles
    strings=("E3", "E4", "A2", "A3", "D3", "D4", "G3", "G4", "B3", "B3", "E4", "E4"),
    gauges=(0.046, 0.018, 0.036, 0.013, 0.026, 0.010, 0.018, 0.008, 0.013, 0.013, 0.010, 0.010),
    pair_gap=(2.4, 3.6), saddle_back=(3.8, 3.0, 2.2, 2.6, 1.6, 0.6),
    headstock=[(22.0, 0), (22.2, 8), (23.5, 15), (27.0, 21), (32.0, 26), (36.5, 31), (38.5, 38), (39.0, 60),
               (39.5, 100), (40.0, 140), (40.6, 180), (41.2, 215), (41.8, 236), (41.5, 241), (37.0, 243),
               (30.0, 243.5), (22.0, 245.0), (14.0, 247.5), (8.0, 249.5), (4.0, 249.0), (0.0, 247.5),
               (-4.0, 249.0), (-8.0, 249.5), (-14.0, 247.5), (-22.0, 245.0), (-30.0, 243.5), (-37.0, 243),
               (-41.5, 241), (-41.8, 236), (-41.2, 215), (-40.6, 180), (-40.0, 140), (-39.5, 100), (-39.0, 60),
               (-38.5, 38), (-36.5, 31), (-32.0, 26), (-27.0, 21), (-23.5, 15), (-22.2, 8), (-22.0, 0)],
    tuner_posts=[(-26.5, 49.0), (-26.5, 85.0), (-26.5, 121.0), (-26.5, 157.0), (-26.5, 193.0), (-26.5, 229.0),
                 (26.5, 52.0), (26.5, 88.0), (26.5, 124.0), (26.5, 160.0), (26.5, 196.0), (26.5, 232.0)],
)


# ---------------------------------------------------------------------------
# guitar_05: James Hetfield's "Eet Fuk" Explorer (metal, late 1980s; rack slot 2), an ESP copy of the
# Explorer: off-white, aged and grimy, no pickguard, two black active-style humbuckers in black rings (no
# logos, no pole pieces), black hardware (tune-o-matic, stop bar, six-in-line tuners), black knobs, an
# ebony board with dots, the six-in-line Explorer head in the body's colour, a strip of plain grey tape
# on the lower bass wing (the real one carries his lettering; ours carries none).
# Outline, head and hardware positions measured on the Commons Explorer cut-out
# (docs/moodboard/local/explorer/explorer-cutout.png, the Gibson the ESP copies): frets 1-22 fitted
# (0.73 px rms); across scaled by 1.067 (the shot is turned a little: the nut and the 12th measure 7 %
# narrow). The finish and parts are Hetfield's, from the reference sheet's photo (low resolution: the
# number of knobs is not certain). Scripts and numbers: video-local/footage/2026-11-12-guitars/measure/g05_*.
# ---------------------------------------------------------------------------
GUITAR_05 = dict(GUITAR_01)
GUITAR_05.update(
    frets=22, v_nut=901.0, v_junction=464.8,   # the heel starts where the treble cutaway meets the neck
    v_junction_bass=517.6, v_junction_treble=464.8,
    neck_angle_deg=3.0, board_above_body=10.0, v_board_end=444.0,
    body_t=40.0, edge_r=6.5, arch_top=0.0, arch_back=0.0,
    body=[
        (-236.1, 0.0), (-241.1, 0.3), (-245.6, 2.1), (-248.9, 5.6), (-250.1, 10.1), (-250.9, 14.8),
        (-251.6, 19.5), (-252.1, 24.4), (-252.0, 29.3), (-250.7, 33.9), (-249.0, 38.2), (-246.8, 42.4),
        (-244.3, 46.4), (-242.0, 50.6), (-239.5, 54.6), (-237.0, 58.7), (-234.7, 62.8), (-232.3, 66.9),
        (-229.8, 70.9), (-227.2, 74.9), (-225.0, 79.1), (-222.4, 83.1), (-219.9, 87.2), (-217.6, 91.2),
        (-215.0, 95.3), (-212.7, 99.4), (-210.1, 103.4), (-207.6, 107.5), (-205.3, 111.6), (-202.8, 115.6),
        (-200.3, 119.7), (-197.9, 123.8), (-195.4, 127.8), (-193.0, 131.9), (-190.6, 136.0), (-188.2, 140.1),
        (-185.7, 144.1), (-183.3, 148.2), (-180.8, 152.2), (-178.2, 156.3), (-176.0, 160.4), (-173.4, 164.4),
        (-171.1, 168.5), (-168.6, 172.5), (-166.3, 176.7), (-163.7, 180.7), (-161.2, 184.8), (-158.9, 188.8),
        (-156.3, 192.9), (-154.0, 197.0), (-151.5, 201.1), (-149.0, 205.1), (-146.6, 209.2), (-144.3, 213.3),
        (-141.7, 217.3), (-139.3, 221.4), (-136.9, 225.4), (-134.6, 229.6), (-132.0, 233.6), (-129.6, 237.6),
        (-127.2, 241.7), (-124.9, 245.9), (-122.4, 249.9), (-119.8, 253.9), (-117.5, 258.0), (-115.1, 262.1),
        (-112.7, 266.2), (-110.1, 270.2), (-107.8, 274.3), (-105.4, 278.4), (-102.9, 282.4), (-100.5, 286.5),
        (-98.1, 290.6), (-95.7, 294.7), (-93.5, 298.8), (-91.2, 303.0), (-89.4, 307.3), (-87.8, 311.7),
        (-86.5, 316.2), (-85.7, 320.9), (-85.3, 325.7), (-85.3, 330.7), (-86.0, 335.4), (-86.8, 340.1),
        (-87.2, 344.9), (-87.9, 349.6), (-88.7, 354.3), (-89.2, 359.1), (-89.9, 363.8), (-90.7, 368.5),
        (-91.5, 373.2), (-91.9, 378.0), (-92.6, 382.7), (-93.4, 387.4), (-93.9, 392.2), (-94.6, 396.9),
        (-95.3, 401.6), (-95.7, 406.5), (-96.0, 411.3), (-96.5, 416.2), (-96.0, 421.0), (-95.1, 425.7),
        (-93.4, 430.0), (-91.0, 434.1), (-87.8, 437.9), (-83.9, 441.0), (-79.6, 443.4), (-75.3, 445.7),
        (-71.0, 447.7), (-67.9, 450.2), (-70.3, 452.9), (-66.7, 455.5), (-62.0, 456.6), (-59.0, 454.6),
        (-55.7, 455.3), (-51.8, 458.3), (-47.9, 461.5), (-44.7, 465.3), (-42.2, 469.3), (-40.1, 473.5),
        (-38.7, 478.0), (-37.6, 482.6), (-36.8, 487.3), (-36.0, 492.0), (-35.1, 496.7), (-33.6, 501.1),
        (-32.1, 505.5), (-30.5, 509.9), (-29.7, 514.6), (-28.8, 519.2), (-28.0, 523.0), (-27.9, 518.4),
        (-24.5, 514.7), (-20.8, 511.1), (-17.1, 507.6), (-13.3, 504.0), (-9.6, 500.4), (-5.9, 496.9),
        (-2.1, 493.3), (1.6, 489.7), (5.3, 486.2), (9.1, 482.6), (12.9, 479.3), (16.8, 475.7), (20.5, 472.2),
        (24.2, 468.6), (27.7, 465.4), (28.2, 469.8), (28.3, 474.8), (28.5, 479.4), (30.7, 475.8),
        (34.0, 472.2), (37.6, 468.5), (41.8, 466.1), (46.6, 465.0), (51.8, 465.4), (56.7, 466.4),
        (61.3, 468.1), (65.5, 470.5), (69.6, 473.4), (73.4, 476.7), (77.2, 480.3), (80.9, 483.8),
        (84.4, 487.5), (88.1, 491.0), (91.6, 494.7), (95.1, 498.4), (98.5, 502.0), (102.2, 505.6),
        (105.8, 509.2), (109.3, 512.9), (113.0, 516.5), (116.4, 520.1), (119.9, 523.8), (123.7, 527.4),
        (127.1, 531.0), (130.8, 534.6), (134.4, 538.2), (137.8, 541.9), (141.5, 545.4), (145.3, 549.0),
        (149.6, 551.3), (154.4, 552.5), (159.5, 552.1), (164.6, 551.3), (169.1, 549.8), (173.4, 547.3),
        (176.8, 543.7), (179.2, 539.6), (179.6, 534.8), (178.9, 530.1), (177.3, 525.7), (175.8, 521.3),
        (174.4, 516.8), (172.7, 512.5), (171.1, 508.1), (169.4, 503.7), (167.8, 499.4), (166.2, 495.0),
        (164.8, 490.5), (163.1, 486.2), (161.6, 481.8), (159.9, 477.4), (158.3, 473.0), (156.6, 468.7),
        (155.2, 464.2), (153.5, 459.9), (152.0, 455.4), (150.4, 451.0), (148.7, 446.7), (147.1, 442.3),
        (145.6, 437.9), (143.9, 433.5), (142.1, 429.2), (140.5, 424.8), (138.8, 420.5), (137.5, 416.0),
        (135.7, 411.7), (134.0, 407.3), (132.3, 403.0), (130.8, 398.5), (129.2, 394.2), (127.5, 389.8),
        (125.9, 385.4), (124.2, 381.1), (122.8, 376.6), (121.1, 372.2), (119.6, 367.8), (117.9, 363.5),
        (116.3, 359.1), (114.7, 354.7), (113.3, 350.3), (111.7, 345.9), (110.0, 341.5), (108.5, 337.1),
        (107.1, 332.6), (106.3, 327.9), (105.6, 323.2), (105.4, 318.2), (105.9, 313.4), (106.3, 308.6),
        (107.5, 304.0), (108.7, 299.5), (110.3, 295.1), (111.9, 290.7), (113.2, 286.3), (114.9, 281.9),
        (116.5, 277.5), (117.9, 273.1), (119.4, 268.6), (121.1, 264.3), (122.6, 259.8), (124.0, 255.4),
        (125.6, 251.0), (127.2, 246.6), (128.6, 242.2), (130.3, 237.8), (131.8, 233.4), (133.5, 229.0),
        (134.9, 224.6), (136.6, 220.2), (138.1, 215.8), (139.7, 211.4), (141.4, 207.0), (142.9, 202.6),
        (144.3, 198.1), (145.9, 193.8), (147.6, 189.4), (148.3, 184.7), (148.8, 179.9), (147.5, 175.4),
        (144.7, 171.5), (141.3, 167.8), (137.5, 164.5), (133.3, 161.7), (129.2, 159.0), (125.1, 156.3),
        (121.0, 153.5), (116.9, 150.8), (112.8, 148.1), (108.5, 145.6), (104.4, 142.9), (100.2, 140.4),
        (95.9, 138.0), (91.8, 135.3), (87.6, 132.8), (83.3, 130.3), (79.1, 127.9), (74.8, 125.7),
        (70.5, 123.2), (66.3, 120.9), (61.9, 118.6), (57.7, 116.2), (53.4, 114.0), (49.1, 111.5),
        (44.8, 109.3), (40.6, 106.9), (36.3, 104.5), (31.9, 102.3), (27.5, 100.0), (23.3, 97.7), (19.0, 95.5),
        (14.6, 93.2), (10.2, 91.1), (5.9, 89.0), (1.5, 86.8), (-2.3, 84.2), (-5.1, 80.5), (-9.9, 79.2),
        (-14.8, 79.1), (-19.1, 76.8), (-23.6, 74.8), (-28.0, 72.6), (-32.3, 70.5), (-36.8, 68.6),
        (-41.3, 66.7), (-45.8, 64.8), (-50.3, 62.9), (-54.7, 61.0), (-59.2, 59.1), (-63.7, 57.2),
        (-68.2, 55.3), (-72.7, 53.4), (-77.2, 51.5), (-81.6, 49.7), (-86.1, 47.8), (-90.6, 45.9),
        (-95.3, 44.3), (-99.8, 42.4), (-104.4, 40.8), (-109.0, 39.0), (-113.5, 37.4), (-118.1, 35.7),
        (-122.7, 34.0), (-127.2, 32.2), (-131.8, 30.6), (-136.4, 28.9), (-140.9, 27.1), (-145.6, 25.4),
        (-150.1, 23.8), (-154.7, 22.2), (-159.5, 20.9), (-164.1, 19.3), (-168.7, 17.7), (-173.4, 16.1),
        (-178.1, 14.7), (-182.8, 13.3), (-187.4, 11.7), (-192.1, 10.2), (-196.8, 8.9), (-201.6, 7.7),
        (-206.4, 6.4), (-211.2, 5.2), (-216.0, 4.0), (-220.8, 2.8), (-225.8, 2.0), (-230.6, 1.0),
        (-235.4, 0.2),],
    headstock=[  # bass edge from b 50 to 157: a straight line fitted to the trace (the button rows had left steps)
        (21.8, -0.1), (20.7, 3.1), (20.5, 6.3), (20.8, 9.5), (21.0, 12.7), (21.0, 15.9), (21.0, 19.1),
        (21.4, 22.3), (21.4, 25.5), (21.5, 28.6), (21.8, 31.8), (22.0, 35.0), (22.4, 38.2), (22.8, 41.4),
        (23.3, 44.6), (24.4, 53.3), (25.3, 56.5), (26.0, 59.7), (28.0, 69.6), (29.3, 72.8), (30.3, 76.0),
        (31.6, 79.2), (34.3, 88.3), (35.7, 91.5), (36.9, 94.7), (39.4, 103.0), (41.5, 106.2), (43.1, 109.4),
        (45.4, 114.1), (48.5, 120.5), (50.2, 123.6), (52.0, 126.8), (55.2, 131.2), (58.3, 138.3),
        (60.2, 141.4), (62.1, 144.6), (63.9, 147.8), (65.1, 150.9), (65.3, 154.1), (64.4, 157.3),
        (62.7, 160.4), (31.7, 160.4), (24.1, 157.3), (19.1, 150.0), (12.3, 140.0), (5.5, 130.0), (-1.3, 120.0),
        (-8.1, 110.0), (-14.9, 100.0), (-21.8, 90.0), (-28.6, 80.0), (-35.4, 70.0), (-42.2, 60.0),
        (-49.0, 50.0), (-52.4, 45.0), (-55.9, 40.0), (-56.6, 35.0), (-56.0, 31.8),
        (-52.4, 28.6), (-47.3, 25.5), (-42.9, 22.3), (-39.3, 19.1), (-36.1, 15.9), (-33.4, 12.7), (-30.9, 9.5),
        (-28.6, 6.3), (-26.8, 3.1), (-25.6, -0.1),],
    tuner_posts=[
        (-31.6, 42.8), (-22.1, 60.7), (-11.8, 78.2), (0.0, 96.9), (11.1, 114.3), (22.2, 131.7),],
    nut_w=42.9, w12=52.5, radius=304.8, board_t=6.0, board_binding=0.01, neck_t1=21.0, neck_t12=23.5,
    fret_wire=(2.7, 1.3), dots=(3, 5, 7, 9, 12, 15, 17, 19, 21), dot_d=6.35, dot12_offset=11.0,
    head_angle_deg=17.0, head_t=14.0, head_drop=8.0, post_d=6.0, post_h=12.0,
    tuner_dir=(-0.856, 0.518),        # the shafts, square to the post line (31 degrees off the neck)
    strap_buttons=[(-63.0, 447.1, 170.0), (-2.7, 78.2, -90.0)],
    pickups=dict(neck=413.0, bridge=316.8, cover=(70.0, 38.5), ring=(88.0, 46.0), cover_h=7.5, under_string=3.0),
    tom=dict(v=275.6, l=82.0, w=10.0, h=8.0, post_span=74.0, wheel_d=10.5),
    tailpiece=dict(v=236.7, l=86.0, w=13.0, h=9.0, stud_span=82.0, gap=3.5), tail_kind="stopbar",
    knobs=[(88.8, 245.0), (74.2, 201.7), (56.5, 157.8)], knob=dict(d=20.0, h=16.0), toggle=(136.6, 481.2),
    jack_v=150.0,                     # on the treble rim by the knobs
    tape=dict(centre=(-135.0, 92.0), l=175.0, w=42.0),   # along the lower bass wing (its angle from the outline)
)


# ---------------------------------------------------------------------------
# guitar_06: Tim Henson's TOD10 (now, 2020s; rack slot 3), in Metallic Mauve: an AZ-type double-cut body
# with rounded edges, a bolt-on roasted maple neck with an ebony board, 24 jumbo stainless frets, a
# six-in-line head in the body's colour, two humbuckers with cream open bobbins on black rings, a two-point
# tremolo (its arm on the treble side), two chrome dome knobs and a five-way switch, all chrome. The board's
# inlay is ours, not the Tree of Death: the piano's tribal strokes in brushed silver, vertical, the tuning
# fork at the 12th fret (decision 2026-10-22). No logo on the head, no lettering anywhere.
# Measured on Ibanez's own front photo (docs/moodboard/local/tod10/, reference only): frets 1-21 fitted
# (0.69 px rms; the nut then measures 41 mm, Ibanez's spec 42); Ibanez's spec sheet for the neck (648 mm
# scale, 42 mm nut, 57 mm at the 24th, 20.5 / 22.5 mm thick at the 1st / 12th, 305 mm radius, 10.5 mm string
# spacing at the bridge). The head's angle (11 degrees) is assumed: Ibanez does not publish it.
# Scripts and numbers: video-local/footage/2026-11-12-guitars/measure/g06_*.
# ---------------------------------------------------------------------------
GUITAR_06 = dict(GUITAR_01)
GUITAR_06.update(
    scale=648.0, frets=24, v_nut=798.0, v_junction=314.9,   # where the treble cutaway meets the neck
    neck_angle_deg=0.0, board_above_body=9.5,
    v_board_end=306.0, body_t=42.0, edge_r=7.0, arch_top=0.0, arch_back=0.0,
    body=[
        (2.4, 0.0), (-2.4, 0.0), (-6.8, 1.1), (-6.7, 4.7), (-3.9, 6.2), (-8.5, 6.4), (-13.5, 6.4),
        (-18.3, 6.8), (-23.1, 7.2), (-28.0, 7.6), (-32.8, 8.1), (-37.4, 8.9), (-42.2, 9.4), (-46.9, 10.2),
        (-51.5, 11.0), (-56.2, 11.9), (-60.8, 12.8), (-65.3, 14.0), (-69.7, 15.3), (-74.2, 16.5),
        (-78.7, 17.8), (-83.0, 19.5), (-87.2, 21.2), (-91.5, 22.9), (-95.8, 24.6), (-99.9, 26.7),
        (-104.0, 28.9), (-108.0, 31.3), (-111.9, 33.9), (-115.7, 36.6), (-119.4, 39.6), (-123.2, 42.6),
        (-126.8, 45.9), (-130.3, 49.5), (-133.5, 53.2), (-136.6, 56.9), (-139.2, 60.9), (-141.8, 64.8),
        (-144.1, 68.9), (-146.1, 73.0), (-147.8, 77.4), (-149.3, 81.8), (-150.6, 86.2), (-151.8, 90.7),
        (-152.6, 95.4), (-153.1, 100.2), (-153.5, 105.0), (-153.8, 109.9), (-153.8, 114.9), (-153.4, 119.7),
        (-153.0, 124.5), (-152.5, 129.4), (-151.8, 134.1), (-150.9, 138.7), (-150.0, 143.3), (-148.7, 147.8),
        (-147.5, 152.3), (-146.0, 156.7), (-144.5, 161.1), (-142.8, 165.4), (-140.8, 169.6), (-139.0, 173.9),
        (-137.1, 178.1), (-135.2, 182.3), (-133.4, 186.6), (-131.3, 190.7), (-129.4, 195.0), (-127.6, 199.2),
        (-125.5, 203.4), (-123.4, 207.5), (-121.5, 211.7), (-119.7, 216.0), (-117.7, 220.2), (-116.0, 224.5),
        (-114.3, 228.8), (-112.7, 233.1), (-111.0, 237.5), (-109.4, 241.8), (-108.0, 246.3), (-106.6, 250.7),
        (-105.6, 255.3), (-104.8, 259.9), (-104.0, 264.6), (-103.6, 269.4), (-103.1, 274.3), (-103.1, 279.3),
        (-103.5, 283.8), (-103.9, 288.6), (-104.7, 293.3), (-105.5, 297.9), (-106.3, 302.6), (-107.5, 307.1),
        (-108.8, 311.6), (-110.0, 316.1), (-111.4, 320.5), (-112.8, 324.9), (-114.0, 329.4), (-115.6, 333.8),
        (-116.9, 338.3), (-118.3, 342.7), (-119.7, 347.1), (-120.9, 351.6), (-122.2, 356.1), (-123.6, 360.5),
        (-124.5, 365.1), (-125.7, 369.6), (-126.8, 374.2), (-127.7, 378.8), (-128.5, 383.4), (-129.0, 388.3),
        (-129.7, 392.9), (-130.1, 397.8), (-130.1, 402.8), (-130.1, 407.8), (-130.1, 412.8), (-129.7, 417.6),
        (-129.4, 422.5), (-128.8, 427.3), (-127.6, 431.8), (-126.6, 436.4), (-125.1, 440.8), (-123.4, 445.1),
        (-121.5, 449.3), (-119.3, 453.4), (-116.8, 457.4), (-113.6, 461.0), (-109.7, 463.7), (-106.5, 466.4),
        (-102.7, 468.2), (-103.8, 471.4), (-102.3, 473.9), (-97.9, 473.5), (-93.8, 471.7), (-92.2, 468.2),
        (-95.8, 467.2), (-94.5, 463.5), (-93.8, 459.5), (-92.5, 455.0), (-91.7, 450.4), (-91.6, 445.7),
        (-91.2, 440.9), (-90.5, 436.2), (-89.6, 431.6), (-88.6, 427.0), (-87.4, 422.5), (-85.9, 418.1),
        (-84.2, 413.8), (-82.1, 409.7), (-79.8, 405.6), (-77.2, 401.7), (-74.5, 397.8), (-71.6, 394.0),
        (-68.4, 390.3), (-64.7, 387.0), (-61.0, 384.1), (-57.0, 381.7), (-52.8, 379.8), (-48.4, 378.3),
        (-43.6, 377.9), (-39.1, 379.0), (-35.1, 381.4), (-32.6, 385.3), (-31.0, 389.6), (-29.2, 393.6),
        (-27.8, 391.5), (-27.7, 386.6), (-27.7, 381.6), (-26.9, 376.9), (-23.8, 373.2), (-20.6, 369.5),
        (-17.3, 365.8), (-14.1, 362.2), (-10.9, 358.5), (-7.7, 354.8), (-4.2, 351.2), (-1.0, 347.6),
        (2.3, 343.9), (5.5, 340.2), (8.7, 336.5), (11.9, 332.8), (15.2, 329.2), (18.8, 325.9), (22.0, 322.2),
        (25.2, 318.6), (28.2, 316.6), (28.3, 321.3), (28.3, 326.3), (27.9, 331.2), (27.9, 336.1),
        (27.9, 341.1), (28.0, 346.0), (29.9, 347.0), (31.1, 342.8), (32.0, 338.1), (33.2, 333.6),
        (34.4, 329.1), (35.9, 324.7), (38.3, 320.7), (41.5, 317.0), (45.2, 314.1), (49.5, 312.2),
        (53.9, 311.0), (58.8, 310.6), (63.6, 311.0), (68.1, 312.1), (72.5, 313.7), (76.5, 316.1),
        (80.3, 318.8), (83.9, 322.0), (87.2, 325.7), (90.1, 329.5), (92.7, 333.4), (94.9, 337.5),
        (97.0, 341.7), (98.8, 345.9), (100.6, 350.2), (101.8, 354.7), (103.0, 359.2), (104.2, 363.7),
        (105.1, 368.4), (106.2, 372.9), (107.1, 377.5), (108.7, 381.8), (111.4, 385.7), (115.6, 387.6),
        (120.3, 387.3), (124.5, 385.4), (127.8, 381.8), (129.9, 377.6), (131.4, 373.2), (132.8, 368.8),
        (133.7, 364.2), (134.5, 359.5), (134.9, 354.7), (135.0, 349.7), (135.0, 344.7), (134.6, 339.8),
        (134.2, 335.0), (133.4, 330.3), (132.6, 325.7), (131.4, 321.2), (129.8, 316.8), (128.5, 312.4),
        (127.0, 308.0), (125.4, 303.7), (123.7, 299.3), (122.1, 295.0), (120.1, 290.8), (118.5, 286.5),
        (116.9, 282.2), (115.2, 277.8), (113.6, 273.5), (112.3, 269.0), (111.2, 264.5), (110.0, 260.0),
        (109.2, 255.3), (108.9, 250.4), (109.2, 245.6), (109.7, 240.8), (110.9, 236.3), (112.3, 231.9),
        (113.8, 227.5), (115.8, 223.3), (117.6, 219.0), (119.6, 214.9), (121.7, 210.7), (123.7, 206.5),
        (125.7, 202.4), (127.8, 198.2), (129.8, 194.0), (131.7, 189.8), (133.7, 185.6), (135.7, 181.4),
        (137.5, 177.2), (139.5, 173.0), (141.2, 168.7), (142.9, 164.3), (144.4, 160.0), (145.8, 155.5),
        (147.1, 151.0), (148.7, 146.7), (150.0, 142.2), (151.3, 137.7), (152.3, 133.2), (153.4, 128.6),
        (153.8, 123.8), (154.7, 119.1), (155.1, 114.3), (155.2, 109.3), (155.5, 104.4), (155.2, 99.6),
        (154.8, 94.8), (154.4, 89.9), (153.6, 85.3), (152.5, 80.7), (151.4, 76.2), (150.0, 71.8),
        (148.4, 67.4), (146.7, 63.1), (144.7, 58.9), (142.6, 54.8), (140.2, 50.8), (137.4, 46.9),
        (134.5, 43.1), (131.3, 39.4), (127.7, 36.0), (124.1, 32.8), (120.4, 29.8), (116.5, 27.2),
        (112.4, 25.0), (108.4, 22.6), (104.3, 20.5), (100.1, 18.7), (95.8, 17.0), (91.5, 15.4), (87.0, 14.0),
        (82.6, 12.7), (78.0, 11.7), (73.5, 10.6), (68.8, 9.8), (64.2, 9.0), (59.4, 8.5), (54.7, 7.7),
        (49.9, 7.2), (45.1, 6.8), (40.3, 6.4), (35.3, 6.4), (30.8, 6.0), (25.8, 5.9), (20.8, 5.9), (15.8, 5.9),
        (10.8, 5.9), (5.8, 5.9), (2.0, 5.1), (5.7, 3.3), (3.3, 0.5),],
    headstock=[
        (20.7, 0.0), (20.7, 2.5), (20.7, 4.9), (20.7, 7.4), (20.7, 9.8), (20.9, 12.3), (21.3, 14.8),
        (21.8, 17.2), (22.5, 19.7), (23.5, 22.1), (24.9, 24.6), (26.6, 27.1), (28.7, 29.5), (30.8, 32.0),
        (33.6, 34.4), (36.8, 36.9), (40.1, 39.3), (42.2, 41.8), (42.5, 44.2), (42.0, 46.7), (41.5, 49.1),
        (41.1, 51.6), (40.7, 54.0), (40.2, 56.5), (39.8, 59.0), (39.4, 61.4), (39.1, 63.9), (38.7, 66.3),
        (38.3, 68.8), (38.1, 71.2), (37.8, 73.7), (37.5, 76.1), (37.3, 78.6), (37.1, 81.0), (36.8, 83.4),
        (36.7, 85.9), (36.4, 88.3), (36.3, 90.8), (36.2, 93.2), (35.8, 95.7), (35.8, 98.1), (35.8, 100.6),
        (35.8, 103.0), (35.8, 105.5), (35.8, 107.9), (35.8, 110.3), (35.8, 112.8), (35.8, 115.2),
        (35.8, 117.7), (35.8, 120.1), (36.0, 122.6), (36.2, 125.0), (36.2, 127.4), (36.6, 129.9),
        (36.6, 132.3), (36.8, 134.8), (37.0, 137.2), (37.1, 139.6), (37.4, 142.1), (37.5, 144.5),
        (37.8, 146.9), (38.1, 149.4), (38.2, 151.8), (38.5, 154.3), (38.7, 156.7), (39.0, 159.1),
        (39.3, 161.6), (39.6, 164.0), (39.9, 166.4), (40.1, 168.9), (40.5, 171.3), (40.5, 173.7),
        (40.5, 176.2), (40.2, 178.6), (39.8, 181.0), (39.2, 183.5), (38.1, 185.9), (36.4, 188.3),
        (33.2, 190.7), (27.9, 190.7), (23.9, 188.3), (21.0, 185.9), (18.9, 183.5), (16.5, 181.0),
        (13.7, 178.6), (8.0, 176.2), (4.6, 173.7), (1.9, 166.0), (-2.8, 150.0), (-8.7, 130.0), (-14.6, 110.0),
        (-20.4, 90.0), (-26.3, 70.0), (-32.2, 50.0), (-36.3, 36.0), (-37.6, 32.0), (-37.1, 29.5),
        (-34.6, 27.1), (-30.8, 24.6), (-27.4, 22.1), (-24.8, 19.7), (-23.0, 17.2), (-21.9, 14.8),
        (-21.1, 12.3), (-20.8, 9.8), (-20.8, 7.4), (-20.8, 4.9), (-20.8, 2.5), (-20.8, 0.0),],
    nut_w=42.0, w12=(42.0 + (57.0 - 42.0) * 0.5 / 0.75), radius=305.0, board_t=6.0, board_binding=0.01,
    neck_t1=20.5, neck_t12=22.5, fret_wire=(2.7, 1.4), dots_side=(3, 5, 7, 9, 12, 15, 17, 19, 21, 24),
    head_angle_deg=11.0, head_t=14.0, head_drop=7.5, post_d=6.0, post_h=11.0, tuner_dir=(-1.0, 0.0),
    tuner_posts=[(-20.3, 41.6), (-13.3, 64.6), (-6.7, 87.8), (0.1, 111.1), (7.3, 134.2), (14.0, 157.2)],
    truss_slot=dict(b0=12.0, b1=28.0, w=7.0),
    strings=("E6", "A", "D", "G", "B", "E1"), gauges=(0.046, 0.036, 0.026, 0.017, 0.013, 0.010),
    nut_spread=35.0, bridge_spread=52.5, saddle_back=(3.2, 2.6, 2.0, 2.2, 1.4, 0.6), string_over_board=1.5,
    pickups=dict(neck=282.3, bridge=194.8, bobbin=(67.5, 16.0), ring=(80.0, 42.0), cover_h=6.5, under_string=3.0),
    bridge2pt=dict(v=140.6, w=70.0, l=45.0, post_u=26.5, post_v=158.7, saddle_v=146.0),
    arm=dict(u=37.1, v=130.2, tip=(58.6, 276.0)),
    knobs=[(68.8, 179.2), (121.8, 127.1)], knob=dict(d=17.0, h=16.0),
    switch=dict(u=99.4, v=201.0, angle_deg=-62.0, slot_l=22.0),
    jack_v=90.0, strap_buttons=[(-102.3, 473.9, 95.0), (-2.7, 0.0, -90.0)],
    # the forearm contour on the top, along the lower bass edge (the owner, 2026-11-13: "there's slight curve
    # at the bottom left edge"): read on the photo's shading, v 35 to 210 from the tail, deepest at 115,
    # 55-60 mm in from the edge; the depth (12 mm at the edge) is judged from the shading, not measured
    forearm=dict(v0=35.0, v1=215.0, peak=0.46, width=60.0, depth=12.0),
)
