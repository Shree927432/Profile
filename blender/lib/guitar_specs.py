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

GUITAR_02 = dict(
    scale=_SCALE, frets=21, v_nut=_NUT_V, overall=994.0, v_tip=_NUT_V + 208.0,
    v_saddle=_NUT_V - _SCALE,      # 138.3: the scale line, before saddle compensation

    # body: alder, 44.5 thick, edge roundover, late-60s contours (shallower than 1950s)
    body_t=44.5, edge_r=6.4,
    body=[  # (u, v), counter-clockwise from the tail, measured from the MoPOP photo and
            # scaled to 457 long, 322 wide; the stretch under the neck heel is the pocket floor
        (0, 0.3), (25, 1.5), (65, 8), (108, 17), (132, 30), (147, 48), (156, 66), (161, 95),
        (159, 130), (150, 156), (138, 186), (124, 212), (115, 236), (113, 262), (117, 282),
        (125, 305), (129.5, 330), (128, 355), (121, 374), (108, 383.5), (96, 380), (88, 368),
        (84, 352), (76, 339), (62, 332), (45, 329), (31, 330.5), (29, 334), (29, 384),
        (26, 388), (0, 388.5), (-26, 388), (-29, 388), (-38, 381), (-52, 376.5), (-68, 382),
        (-80, 393), (-87, 410), (-90, 430), (-93, 448), (-106, 456), (-118, 451.5),
        (-128, 442), (-137, 425), (-142, 395), (-140, 370), (-130, 337), (-118, 303),
        (-114.5, 270), (-122, 238), (-137, 205), (-152, 166), (-160, 135), (-161, 95),
        (-157, 62), (-147, 41), (-130, 22), (-96, 8), (-25, 0)],
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

    # headstock: the large late-60s shape, flat (no tilt), face 6.4 below the fretboard
    head_t=14.3, head_step=6.4, head_angle_deg=0.0,
    headstock=[  # (a, b), open curve from the nut's right end, over the tip, to its left end
        (21, 0), (21.3, 19.4), (22.5, 43.1), (25.5, 67.9), (31, 91.6), (39, 112.1),
        (48.5, 131.5), (56, 147.6), (58.5, 162.7), (55, 177.8), (45, 188.6), (31, 195.6),
        (16, 201.5), (0, 206.4), (-16, 208), (-27, 204.2), (-33, 195.1), (-33.6, 181.1),
        (-31.8, 161.7), (-31, 129.3), (-31.2, 86.2), (-30.8, 45.3), (-28.5, 30.2), (-24, 18.3),
        (-21.6, 8.6), (-21, 0)],
    tuner_a=-20.0, tuner_b0=44.0, tuner_pitch=25.4, post_d=6.3, bushing_d=9.0, post_h=16.0,
    tuner_key=dict(a=-47.5, w=14.0, h=17.0, z=-17.0, t=5.0),   # oval metal keys, beyond the left edge
    tuner_housing=dict(w=13.0, h=21.0, depth=12.0),            # on the back, plain (no stamp)
    string_tree=dict(a=2.0, b=62.0, w=12.0, h=5.0, height=5.0, holds="A and low E"),
    hook=dict(gap=46.0),       # inner gap of the wall hanger's two prongs

    # strings, left to right at the nut as it hangs (Hendrix's stringing)
    strings=("E1", "B", "G", "D", "A", "E6"),
    gauges=(0.010, 0.013, 0.017, 0.026, 0.032, 0.038),   # in, plain G light set of the era
    nut_spread=34.6, bridge_spread=56.4,                 # outer strings, centre to centre
    saddle_back=(1.5, 2.5, 3.5, 3.0, 3.8, 4.8),          # mm behind the scale line, per string

    # pickups: three single coils, white covers, staggered poles as built (not turned)
    pickup=dict(l=83.0, w=18.5, pole_d=4.9, pole_spread=52.4, screw_off=45.5),
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
        (104, 262), (107, 290), (110, 312), (100, 326), (84, 333), (70, 330.5), (55, 326.5),
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
        (-105.0, 456.0, 100.0, "long horn tip, original"),
        (108.0, 383.5, 75.0, "short horn, added by Hendrix"),
    ],
    strap_button=dict(d=11.0, h=11.0),
)
