"""Piano layout maths shared by the 2D design sheet and the 3D builder.

Plain Python, no bpy, so the sheet can run outside Blender. Everything reads
`constants.PIANO`; nothing here retypes a dimension. Piano frame: metres, back of
the case at y = 0, front toward -Y, floor at z = 0, centred on x = 0.
"""
import math

from . import constants as C

P, KT = C.PIANO, C.KT


def keyboard():
    """One tuple per key, A0 to C8: (midi, kind, x_left, x_right, back_left, back_right).

    kind is "w" or "b". For a white key x_left/x_right is its front width and
    back_left/back_right the narrowed back part beside the black keys (the notch).
    Black keys sit on the real offsets: C# and D# split C to E in five parts, F#, G#
    and A# split F to B in seven.
    """
    pitch, g = P["white_pitch"], P["white_gap"]
    whites = [m for m in range(C.MIDI_A0, C.MIDI_C8 + 1) if C.is_white(m)]
    x0 = -len(whites) * pitch / 2

    def wi(m):
        if m >= C.MIDI_A0:
            return sum(1 for n in range(C.MIDI_A0, m) if C.is_white(n))
        return -sum(1 for n in range(m, C.MIDI_A0) if C.is_white(n))

    def black_centre(m):
        pc = m % 12
        if pc in (1, 3):
            start, off = m - pc, {1: 0.9, 3: 2.1}[pc]
        else:
            start, off = m - (pc - 5), {6: 6 / 7, 8: 2.0, 10: 22 / 7}[pc]
        return x0 + (wi(start) + off) * pitch

    keys = {}
    for m in range(C.MIDI_A0, C.MIDI_C8 + 1):
        if not C.is_white(m):
            c = black_centre(m)
            keys[m] = ("b", c - P["black_w"] / 2, c + P["black_w"] / 2)
    out = []
    for m in range(C.MIDI_A0, C.MIDI_C8 + 1):
        if C.is_white(m):
            L = x0 + wi(m) * pitch
            R = L + pitch
            bl = keys[m - 1][2] + g if (m - 1) in keys else L + g / 2
            br = keys[m + 1][1] - g if (m + 1) in keys else R - g / 2
            out.append((m, "w", L + g / 2, R - g / 2, bl, br))
        else:
            out.append((m, "b", keys[m][1], keys[m][2], keys[m][1], keys[m][2]))
    return out


def fallboard_profile(angle_deg):
    """Fallboard section (y, z) in the piano frame, rotated about its hinge."""
    L, t, n = P["fall_len"], P["fall_t"], P["fall_nose"]
    local = [(0, 0), (-(L - 0.022), 0), (-(L - 0.022), -n), (-L, -n), (-L, t), (0, t)]
    a = math.radians(-angle_deg)
    py, pz = P["fall_pivot_y"], P["fall_pivot_z"]
    return [(py + y * math.cos(a) - z * math.sin(a), pz + y * math.sin(a) + z * math.cos(a))
            for y, z in local]


def lid_profile(angle_deg):
    """Lid section (y, z) rotated about its hinge, and the hinge point (y, z)."""
    t = P["lid_t"]
    y0, y1 = -(P["side_depth"] + P["lid_over_front"]), P["lid_over_back"]
    hy, hz = y1, P["case_top"] + t                     # hinge: back top edge
    local = [(y0, P["case_top"]), (y1, P["case_top"]), (y1, hz), (y0, hz)]
    a = math.radians(-angle_deg)
    return [(hy + (y - hy) * math.cos(a) - (z - hz) * math.sin(a),
             hz + (y - hy) * math.sin(a) + (z - hz) * math.cos(a)) for y, z in local], (hy, hz)


def cheek_profile(n=18):
    """Side profile (y, z) of a key cheek: a quarter ellipse from the top of the
    arm down to its rounded nose above the keys."""
    pts = [(P["cheek_back_y"], P["cheek_bottom"]), (P["cheek_front_y"], P["cheek_bottom"])]
    a = P["cheek_curve_y"] - P["cheek_front_y"]
    b = P["cheek_top"] - P["cheek_nose"]
    for i in range(n + 1):
        s = math.radians(90 * i / n)
        pts.append((P["cheek_curve_y"] - a * math.cos(s), P["cheek_nose"] + b * math.sin(s)))
    pts.append((P["cheek_back_y"], P["cheek_top"]))
    return pts


def console_profile(n=20):
    """Side profile (y, z) of a console (leg): a waisted front curve on a toe block."""
    bot, top = P["toe_rail_top"], P["cheek_bottom"]
    pts = [(P["console_back_y"], bot)]
    for i in range(n + 1):
        t = i / n
        base = P["console_front_bottom_y"] + (P["console_front_top_y"] - P["console_front_bottom_y"]) * t
        pts.append((base + P["console_waist"] * math.sin(math.pi * t), bot + (top - bot) * t))
    pts.append((P["console_back_y"], top))
    return pts


def sheet_line():
    """Bottom and top (y, z) of the music sheet leaning on the rest."""
    a = math.radians(P["sheet_lean_deg"])
    y0, z0 = P["ledge_front_y"] + 0.014, P["ledge_z"] + P["ledge_t"]
    return (y0, z0), (y0 + P["sheet_h"] * math.sin(a), z0 + P["sheet_h"] * math.cos(a))


def side_profile(n=18):
    """Side panel profile (y, z): the whole side of the case including the key
    cheek, so the outer silhouette is one piece with no seam at the arm."""
    sd = P["side_depth"]
    pts = [(0.0, P["floor_gap"]), (-sd, P["floor_gap"]), (-sd, P["cheek_bottom"]),
           (P["cheek_front_y"], P["cheek_bottom"])]
    pts += cheek_profile(n)[2:-1]                       # the quarter ellipse, nose to top
    pts += [(-sd, P["cheek_top"]), (-sd, P["case_top"]), (0.0, P["case_top"])]
    return pts


def cheek_block_profile(n=18):
    """The inner cheek block beside the keys: the arm profile, extended back to the
    upper front panel's face."""
    pts = [(P["panel_face_y"], P["cheek_bottom"]), (P["cheek_front_y"], P["cheek_bottom"])]
    pts += cheek_profile(n)[2:-1]
    pts.append((P["panel_face_y"], P["cheek_top"]))
    return pts
