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
