"""obj_piano: the upright piano and its bench, built from blender/lib/constants.py.

Names, pivots and rotation signs follow scene/objects/MESHES.md. The piano is built in
its own frame (back of the case at y = 0, front toward -Y, floor at z = 0, centred
on x = 0) under the empty `obj_piano`; the test scene places the root.

    build_steps()   generator: builds one group of parts per step and yields its label,
                    so a windowed run can redraw between steps
    build()         runs all steps, returns the root
    BUILD_ORDER     the groups in build order (names), for the build clip
    export_prep()   duplicates the static parts and joins them into `piano_static`
                    (MESHES.md export rule), returns the objects to export and an undo()

Finish A (decisions 2026-10-22): black lacquer under a clear coat, ivory keys,
ebony sharps, brass, red felt. Interior: iron plate, pin block, strings, hammers.
"""
import math
import random

import bpy
from mathutils import Vector

from lib import constants as C, geo, materials as M, names, piano_layout as L

P, KT = C.PIANO, C.KT
HW = P["width"] / 2
INNER = HW - P["side_t"]           # inside face of the side panels
ARM_IN = P["fall_half_w"] + 0.002  # inside face of the key cheeks

# Interior layout (not in the sheet; chosen here). Piano frame, metres.
INT = dict(
    soundboard_y=(-0.038, -0.022), plate_y=(-0.080, -0.045), plate_top=(1.045, 1.165),
    plate_x=0.715, strut_x=(-0.44, -0.08, 0.30, 0.62), strut_w=0.034,
    pins_y=(-0.080, -0.108), pin_r=0.0035, pins_z=(1.082, 1.102, 1.122), pins_x=(-0.665, 0.685),
    treble_y=-0.092, bass_y=-0.102, bass_notes=26, string_bottom=0.20, string_top=1.075,
    bass_top_x=(-0.655, -0.335), bass_bottom_x=(-0.06, 0.44),
    treble_top_x=(-0.305, 0.675), treble_lean=-0.05,
    hammer_z=1.000, hammer_rail=(-0.205, -0.170, 0.930, 0.952), rail_x=0.665,
    damper_z=(1.012, 1.036), damper_notes=68, damper_y=(-0.120, -0.104),
)

BUILD_ORDER = []        # [(label, [object names])], filled while building
_coll = None
_root = None
_mats = {}


def _step(label, objs):
    BUILD_ORDER.append((label, [o.name for o in objs]))


def _obj(name, builder, *args, mat=None, bev=None, seg=3, **kw):
    o = builder(name, *args, collection=_coll, parent=_root, material=_mats[mat] if mat else None, **kw)
    if bev:
        geo.bevel(o, bev, segments=seg)
    return o


def materials():
    """Create (or refresh) every material the piano uses."""
    _mats.clear()
    _mats["case"] = M.lacquer_black("mat_piano_case")
    _mats["ivory"] = M.ivory("mat_piano_ivory")
    _mats["ebony"] = M.ebony("mat_piano_ebony")
    _mats["brass"] = M.brass("mat_piano_brass")
    _mats["felt"] = M.felt("mat_piano_felt", C.COL["felt_red"])
    _mats["slot"] = M.felt("mat_piano_slot", "#17120f")
    _mats["rubber"] = M.principled("mat_piano_cup", base="#1a1816", rough=0.55, spec=0.3)
    _mats["inside"] = M.principled("mat_piano_inside", base="#0b0a09", rough=0.7, spec=0.3)
    _mats["interior"] = M.tinted("mat_piano_interior", rough=0.45)
    _mats["strings"] = M.tinted("mat_piano_strings", rough=0.30)
    _mats["hammers"] = M.tinted("mat_piano_hammers", rough=0.75)
    _mats["sheet"] = M.image_material("mat_piano_sheet", sheet_image(), rough=0.8)
    return _mats


# ---------------------------------------------------------------------------
# the music sheet image: two open pages of staves, drawn with numpy (no files)
# ---------------------------------------------------------------------------
def sheet_image(w=1024, h=724):
    import numpy as np
    img = bpy.data.images.get("piano_sheet_pages") or bpy.data.images.new("piano_sheet_pages", w, h)
    px = np.full((h, w, 4), 1.0, dtype=np.float32)
    px[..., :3] = (0.93, 0.90, 0.84)
    rng = random.Random(7)
    ink = (0.12, 0.11, 0.10)
    # centre fold: a soft shadow
    for i in range(18):
        a = 0.18 * (1 - i / 18)
        for x in (w // 2 - i, w // 2 + i):
            px[:, x, :3] *= (1 - a)
    # row 0 of the array is the TOP of the picture once written upside down below
    def staff(x0, x1, y):
        for k in range(5):
            px[y + k * 9: y + k * 9 + 2, x0:x1, :3] = ink
        # bar lines
        for bx in range(x0, x1 + 1, (x1 - x0) // 4):
            px[y: y + 38, max(x0, bx - 1): bx + 1, :3] = ink
        # notes with stems
        for n in range(14):
            nx = x0 + 18 + int((x1 - x0 - 36) * (n + rng.random() * 0.6) / 14)
            ny = y + rng.choice((-4, 0, 4, 9, 13, 18, 22, 27, 31, 36, 40))
            yy, xx = np.ogrid[-5:6, -7:8]
            mask = (xx / 7.0) ** 2 + (yy / 4.5) ** 2 <= 1
            sub = px[ny - 5: ny + 6, nx - 7: nx + 8, :3]
            if sub.shape[:2] == mask.shape:
                sub[mask] = ink
            px[ny - 30: ny, nx + 6: nx + 8, :3] = ink
    for page in (0, 1):
        x0 = 48 + page * (w // 2)
        x1 = x0 + w // 2 - 96
        top = 110 if page == 0 else 60
        if page == 0:  # title block and a composer line on the first page
            px[34:50, x0 + 120: x1 - 120, :3] = ink
            px[62:68, x1 - 200: x1, :3] = (0.35, 0.33, 0.30)
        for s in range(8 if page == 0 else 9):
            staff(x0, x1, top + s * 72)
    # Blender's row 0 is V = 0; the screen helper puts V = 0 on the plane's top edge,
    # so row 0 of the picture (its top) goes in first, unflipped.
    img.pixels.foreach_set(np.ascontiguousarray(px).ravel())
    img.pack()
    return img


# ---------------------------------------------------------------------------
# the case
# ---------------------------------------------------------------------------
def build_case():
    sd, ft, ct = P["side_depth"], P["floor_gap"], P["case_top"]
    side = L.side_profile()
    l = _obj("piano_side_l", geo.prism, side, "X", -HW, -INNER, mat="case", bev=0.006)
    r = _obj("piano_side_r", geo.prism, side, "X", INNER, HW, mat="case", bev=0.006)
    back = _obj("piano_back", geo.box, -INNER, INNER, -P["back_t"], 0.0, ft, ct, mat="case", bev=0.004)
    bottom = _obj("piano_bottom", geo.box, -INNER, INNER, -sd, 0.0, ft, ft + 0.020, mat="inside")
    _step("shell", [l, r, back, bottom])

    # crown moulding under the lid: a U band, proud of the case, rounded below
    p = P["crown_proud"]
    u = [(-HW - p, 0.0), (-HW - p, -sd - p), (HW + p, -sd - p), (HW + p, 0.0),
         (INNER, 0.0), (INNER, P["panel_back_y"]), (-INNER, P["panel_back_y"]), (-INNER, 0.0)]
    crown = _obj("piano_crown", geo.prism, u, "Z", ct - P["crown_h"], ct, mat="case", bev=0.007, seg=4)
    _step("crown", [crown])

    up = _obj("piano_panel_upper", geo.box, -INNER, INNER, P["panel_face_y"], P["panel_back_y"],
              P["panel_bottom"], ct - P["crown_h"] + 0.002, mat="case", bev=0.004)
    low = _obj("piano_panel_lower", geo.box, -INNER, INNER, P["lower_face_y"], P["lower_back_y"],
               P["toe_rail_top"], P["cheek_bottom"] + 0.002, mat="case", bev=0.004)
    rail = _obj("piano_toe_rail", geo.box, -INNER, INNER, P["toe_rail_front_y"], -0.300,
                ft, P["toe_rail_top"], mat="case", bev=0.006)
    _step("panels", [up, low, rail])

    toes, cons = [], []
    for s, x in ((-1, "l"), (1, "r")):
        tx = s * P["toe_x"]
        toes.append(_obj(f"piano_toe_{x}", geo.box, tx - P["toe_w"] / 2, tx + P["toe_w"] / 2,
                         P["toe_front_y"], P["toe_back_y"], ft, P["toe_rail_top"] + 0.002,
                         mat="case", bev=0.008, seg=4))
        cons.append(_obj(f"piano_console_{x}", geo.prism, L.console_profile(), "X",
                         tx - P["console_w"] / 2, tx + P["console_w"] / 2, mat="case", bev=0.006))
    _step("toes", toes + cons)

    bed = _obj("piano_keybed", geo.box, -ARM_IN, ARM_IN, -0.560, -0.360, P["cheek_bottom"] - 0.002,
               KT - 0.035, mat="inside")
    cheeks = [_obj(f"piano_cheek_{x}", geo.prism, L.cheek_block_profile(), "X", *xr, mat="case", bev=0.006)
              for x, xr in (("l", (-INNER - 0.001, -ARM_IN)), ("r", (ARM_IN, INNER + 0.001)))]
    slip = _obj("piano_slip", geo.box, -ARM_IN, ARM_IN, P["slip_front_y"], P["slip_back_y"],
                P["cheek_bottom"], P["slip_top"], mat="case", bev=0.004)
    _step("keybed", [bed] + cheeks + [slip])

    pr = P["inset_proud"]
    f1 = _obj("piano_field_upper", geo.box, -P["inset_half_w"], P["inset_half_w"],
              P["panel_face_y"] - pr, P["panel_face_y"] + 0.002, P["inset_bottom"], P["inset_top"],
              mat="case", bev=0.004, seg=4)
    f2 = _obj("piano_field_lower", geo.box, -P["lower_inset_half_w"], P["lower_inset_half_w"],
              P["lower_face_y"] - pr, P["lower_face_y"] + 0.002, P["lower_inset_bottom"],
              P["lower_inset_top"], mat="case", bev=0.004, seg=4)
    # music rest: a ledge with a front lip, two small brackets under it
    hw = P["ledge_half_w"]
    ledge = _obj("piano_rest", geo.box, -hw, hw, P["ledge_front_y"], P["panel_face_y"] + 0.002,
                 P["ledge_z"], P["ledge_z"] + P["ledge_t"], mat="case")
    lip = _obj("piano_rest_lip", geo.box, -hw, hw, P["ledge_front_y"], P["ledge_front_y"] + 0.012,
               P["ledge_z"], P["ledge_lip_top"], mat="case")
    br = [_obj(f"piano_rest_bracket_{i}", geo.box, x - 0.015, x + 0.015, P["ledge_front_y"] + 0.03,
               P["panel_face_y"] + 0.002, P["ledge_z"] - 0.045, P["ledge_z"], mat="case")
          for i, x in enumerate((-hw + 0.06, hw - 0.06))]
    rest = geo.join([ledge, lip] + br, "piano_rest")
    geo.bevel(rest, 0.003)
    _step("fields", [f1, f2, rest])


def build_lid():
    ct, t = P["case_top"], P["lid_t"]
    lid = _obj("piano_lid", geo.box, -HW - P["lid_over_side"], HW + P["lid_over_side"],
               -(P["side_depth"] + P["lid_over_front"]), P["lid_over_back"], ct, ct + t,
               mat="case", bev=0.008, seg=5)
    geo.set_origin(lid, (0, P["lid_over_back"], ct + t))
    hinges = []
    for i, hx in enumerate(P["hinge_x"]):
        n = 5
        seg = P["hinge_len"] / n
        zc, yc = ct + t - 0.001, P["lid_over_back"] + 0.001
        specs = []
        for k in range(n):
            x0 = hx - P["hinge_len"] / 2 + k * seg + 0.0004
            r = P["hinge_r"] if k % 2 == 0 else P["hinge_r"] - 0.0004
            specs.append((r, (x0, yc, zc), (x0 + seg - 0.0008, yc, zc)))
        barrel = _obj(f"piano_hinge_barrel_{i}", geo.cylinders, specs, segments=20, mat="brass")
        leaf = _obj(f"piano_hinge_leaf_{i}", geo.box, hx - P["hinge_len"] / 2, hx + P["hinge_len"] / 2,
                    0.0, 0.0018, ct - 0.040, ct - 0.001, mat="brass")
        screws = _obj(f"piano_hinge_screws_{i}", geo.cylinders,
                      [(0.0022, (sx, 0.0018, ct - 0.020), (sx, 0.0028, ct - 0.020))
                       for sx in (hx - 0.02, hx, hx + 0.02)], segments=12, mat="brass")
        hinges.append(geo.join([barrel, leaf, screws], f"piano_hinge_{i + 1:02d}"))
    _step("lid", [lid] + hinges)


def build_hardware():
    pedals = []
    yb, yf = P["pedal_back_y"], P["pedal_front_y"]
    for i, px in enumerate(P["pedal_x"]):
        wb, wf = P["pedal_w_back"], P["pedal_w_front"]
        r = wf / 2
        yc = yf + r
        pts = [(px + wb / 2, yb), (px + wf / 2, yc)]
        pts += [(px + r * math.cos(a), yc - r * math.sin(a)) for a in
                [math.pi * k / 10 for k in range(1, 10)]]
        pts += [(px - wf / 2, yc), (px - wb / 2, yb)]
        pd = _obj(f"piano_pedal_{i + 1:02d}", geo.prism, pts, "Z", P["pedal_z"], P["pedal_z"] + P["pedal_t"],
                  mat="brass", bev=0.004, seg=4)
        geo.set_origin(pd, (px, yb, P["pedal_z"]))
        pd.rotation_euler.x = math.radians(-4)      # pedals rise a little toward the front
        pedals.append(pd)
    slot = _obj("piano_pedal_slot", geo.box, -0.13, 0.13, P["toe_rail_front_y"] - 0.0015, -0.355,
                0.046, 0.072, mat="slot", bev=0.003)
    _step("pedals", pedals + [slot])

    cups, castors = [], []
    for i, (cx, cy) in enumerate(P["cups"]):
        cups.append(_obj(f"piano_cup_{i + 1:02d}", geo.cylinder, P["cup_r"], (cx, cy, 0.0),
                         (cx, cy, P["cup_h"]), segments=32, mat="rubber", bev=0.004))
        zc = P["floor_gap"] - P["castor_r"] + 0.004
        wheel = _obj(f"piano_castor_wheel_{i}", geo.cylinder, P["castor_r"], (cx - 0.006, cy, zc),
                     (cx + 0.006, cy, zc), segments=20, mat="brass", bev=0.002, seg=2)
        fork = _obj(f"piano_castor_fork_{i}", geo.box, cx - 0.009, cx + 0.009, cy - 0.016, cy + 0.016,
                    zc, P["floor_gap"] + 0.004, mat="brass")
        castors.append(geo.join([wheel, fork], f"piano_castor_{i + 1:02d}"))
    _step("castors", cups + castors)

    felt = _obj("piano_felt", geo.box, -ARM_IN, ARM_IN, P["key_back_y"] + 0.0005, P["key_back_y"] + 0.012,
                KT - 0.006, KT + 0.010, mat="felt")
    rail = _obj("piano_key_rail", geo.box, -ARM_IN, ARM_IN, P["key_back_y"] + 0.010, P["panel_face_y"] + 0.002,
                KT - 0.036, KT + 0.012, mat="inside")
    _step("felt", [felt, rail])


# ---------------------------------------------------------------------------
# the keys: 88 separate meshes, origin on the hinge line at the back
# ---------------------------------------------------------------------------
def build_keys():
    keys = []
    yb = P["key_back_y"]
    yn = yb - P["black_len"] - P["white_gap"]          # where the white key notch starts
    yf = yb - P["white_len"]
    z0 = KT - P["white_h"]
    for midi, kind, xl, xr, bl, br in L.keyboard():
        name = C.key_name(midi)
        if kind == "w":
            pts = [(xl, yf), (xr, yf), (xr, yn)]
            if br < xr - 1e-6:
                pts += [(br, yn), (br, yb)]
            else:
                pts += [(xr, yb)]
            if bl > xl + 1e-6:
                pts += [(bl, yb), (bl, yn), (xl, yn)]
            else:
                pts += [(xl, yb)]
            k = _obj(name, geo.prism, pts, "Z", z0, KT, mat="ivory", bev=0.0012, seg=2)
            geo.set_origin(k, ((xl + xr) / 2, yb, z0))
        else:
            cx = (xl + xr) / 2
            tw = P["black_top_w"] / 2
            zb, zt = KT - 0.010, KT + P["black_up"]
            bottom = [(xl, yb - P["black_len"], zb), (xr, yb - P["black_len"], zb), (xr, yb, zb), (xl, yb, zb)]
            top = [(cx - tw, yb - P["black_len"] + P["black_taper"], zt),
                   (cx + tw, yb - P["black_len"] + P["black_taper"], zt), (cx + tw, yb, zt), (cx - tw, yb, zt)]
            k = _obj(name, geo.loft, bottom, top, mat="ebony", bev=0.0012, seg=2)
            geo.set_origin(k, (cx, yb, z0))
        keys.append(k)
    assert len(keys) == 88
    _step("keys", keys)


def build_sheet_and_fallboard():
    (y0, z0), _ = L.sheet_line()
    a = math.radians(P["sheet_lean_deg"])
    h = P["sheet_h"]
    centre = (0.0, y0 + h / 2 * math.sin(a), z0 + h / 2 * math.cos(a))
    sheet = geo.screen_plane("piano_sheet", P["sheet_w"], h, centre, collection=_coll, parent=_root,
                             material=_mats["sheet"])
    sheet.rotation_euler.x = -a            # top leans back (+Y) onto the lid's front edge
    _step("sheet", [sheet])

    fb = _obj("piano_fallboard", geo.prism, L.fallboard_profile(0), "X", -P["fall_half_w"], P["fall_half_w"],
              mat="case", bev=0.004, seg=4)
    geo.set_origin(fb, (0.0, P["fall_pivot_y"], P["fall_pivot_z"]))
    fb.rotation_euler.x = math.radians(-P["fall_open_deg"])   # open: negative about +X
    _step("fallboard", [fb])


# ---------------------------------------------------------------------------
# the interior: plate, pin block, strings, hammers (seen with the lid open)
# ---------------------------------------------------------------------------
def _hammer_x():
    """x of each note's hammer, from where its strings cross the hammer line."""
    I = INT
    xs = []
    for i in range(88):
        if i < I["bass_notes"]:
            t = i / (I["bass_notes"] - 1)
            top = I["bass_top_x"][0] + t * (I["bass_top_x"][1] - I["bass_top_x"][0])
            bot = I["bass_bottom_x"][0] + t * (I["bass_bottom_x"][1] - I["bass_bottom_x"][0])
        else:
            t = (i - I["bass_notes"]) / (87 - I["bass_notes"])
            top = I["treble_top_x"][0] + t * (I["treble_top_x"][1] - I["treble_top_x"][0])
            bot = top + I["treble_lean"]
        s = (I["string_top"] - I["hammer_z"]) / (I["string_top"] - I["string_bottom"])
        xs.append((top, bot, top + s * (bot - top)))
    return xs


def build_interior():
    I = INT
    parts = []
    sb = _obj("piano_soundboard", geo.box, -INNER, INNER, I["soundboard_y"][0], I["soundboard_y"][1],
              0.06, P["case_top"] - 0.01, mat="interior")
    geo.tint(sb, "#9c7a48")
    parts.append(sb)
    gold = "#9a7634"
    py0, py1 = I["plate_y"]
    pb = _obj("piano_plate_top", geo.box, -I["plate_x"], I["plate_x"], py0, py1, *I["plate_top"],
              mat="interior", bev=0.006, seg=3)
    parts.append(geo.tint(pb, gold, 0.35))
    pbot = _obj("piano_plate_bottom", geo.box, -I["plate_x"], I["plate_x"], py0 + 0.012, py1, 0.09, 0.16,
                mat="interior", bev=0.005)
    parts.append(geo.tint(pbot, gold, 0.35))
    for i, sx in enumerate(I["strut_x"]):
        st = _obj(f"piano_plate_strut_{i}", geo.box, sx - I["strut_w"] / 2, sx + I["strut_w"] / 2,
                  py0 + 0.012, py1, 0.15, I["plate_top"][0] + 0.01, mat="interior", bev=0.005)
        parts.append(geo.tint(st, gold, 0.35))
    # a diagonal bass strut, following the overstrung bass
    bx0, bx1 = I["bass_top_x"][0] - 0.03, I["bass_bottom_x"][1] + 0.02
    dx, dz = bx1 - bx0, 0.17 - I["string_top"]
    d = _obj("piano_plate_bass_strut", geo.box, -0.02, 0.02, py0 + 0.012, py1, 0.0,
             math.hypot(dx, dz), mat="interior", bev=0.005)
    d.location = (bx0, 0.0, I["string_top"])
    d.rotation_euler.y = math.atan2(dx, dz)      # a +Z box turned to run from top-left down to the right
    parts.append(geo.tint(d, gold, 0.35))
    # tuning pins: three staggered rows across the pin block
    specs = []
    x0, x1 = I["pins_x"]
    n = 230
    for k in range(n):
        x = x0 + (x1 - x0) * k / (n - 1)
        z = I["pins_z"][k % 3]
        specs.append((I["pin_r"], (x, I["pins_y"][0], z), (x, I["pins_y"][1], z)))
    pins = _obj("piano_pins", geo.cylinders, specs, segments=8, mat="interior")
    parts.append(geo.tint(pins, "#9a9a96", 1.0))
    # pressure bar under the pins, bridges on the soundboard
    bar = _obj("piano_pressure_bar", geo.box, x0, x1, py0 - 0.006, py0 + 0.004, 1.055, 1.068, mat="interior",
               bev=0.003)
    parts.append(geo.tint(bar, "#8a8a86", 1.0))
    tb = _obj("piano_bridge_treble", geo.box, -0.016, 0.016, I["soundboard_y"][0] - 0.022, I["soundboard_y"][0],
              0.0, 1.05, mat="interior", bev=0.004)
    tb.location = (0.69, 0.0, 0.24)
    tb.rotation_euler.y = math.radians(-66)
    parts.append(geo.tint(tb, "#6b4a2c"))
    bb = _obj("piano_bridge_bass", geo.box, -0.016, 0.016, I["soundboard_y"][0] - 0.022, I["soundboard_y"][0],
              0.0, 0.42, mat="interior", bev=0.004)
    bb.location = (0.07, 0.0, 0.24)
    bb.rotation_euler.y = math.radians(-50)
    parts.append(geo.tint(bb, "#6b4a2c"))
    # hammer rail and its brackets, dampers (felt blocks on the strings)
    ry0, ry1, rz0, rz1 = I["hammer_rail"]
    rail = _obj("piano_hammer_rail", geo.box, -I["rail_x"], I["rail_x"], ry0, ry1, rz0, rz1, mat="interior",
                bev=0.003)
    parts.append(geo.tint(rail, "#5a3b22"))
    for i, bxp in enumerate((-0.62, -0.21, 0.21, 0.62)):
        b = _obj(f"piano_action_bracket_{i}", geo.box, bxp - 0.012, bxp + 0.012, ry0 - 0.02, ry1,
                 rz0 - 0.08, I["damper_z"][1] + 0.03, mat="interior", bev=0.003)
        parts.append(geo.tint(b, "#2a2a2a", 0.6))
    hx = _hammer_x()
    dz0, dz1 = I["damper_z"]
    dy0, dy1 = I["damper_y"]
    dampers = []
    for i in range(I["damper_notes"]):
        x = hx[i][2]
        w = 0.0115 if i < I["bass_notes"] else 0.0135
        dampers.append(_obj(f"piano_damper_{i}", geo.box, x - w / 2, x + w / 2, dy0, dy1, dz0, dz1,
                            mat="interior"))
    dmp = geo.join(dampers, "piano_dampers")
    parts.append(geo.tint(dmp, "#ece4d2"))
    interior = geo.join(parts, "piano_interior")
    _step("interior", [interior])

    # strings: wound copper bass crossing in front, steel trichords behind
    specs = []
    tints = []
    for i, (top, bot, _) in enumerate(hx):
        if i < I["bass_notes"]:
            n_str = 1 if i < 8 else 2
            r = 0.0024 - 0.0012 * i / I["bass_notes"]
            y = I["bass_y"]
            spread = 0.0045
        else:
            n_str = 3
            r = 0.00055
            y = I["treble_y"]
            spread = 0.0032
        for s in range(n_str):
            off = (s - (n_str - 1) / 2) * spread
            specs.append((r, (top + off, y, I["string_top"]), (bot + off, y, I["string_bottom"])))
    strings = _obj("piano_strings", geo.cylinders, specs, segments=6, mat="strings")
    # bass strings copper, treble steel: tint per loop by the string's x at the top
    me = strings.data
    ca = me.color_attributes.new(name="tint", type="FLOAT_COLOR", domain="CORNER")
    copper, steel = M.srgb("#b4642c"), M.srgb("#c8c8c4")
    for poly in me.polygons:
        v = me.vertices[poly.vertices[0]].co
        col = copper if v.y < (I["bass_y"] + I["treble_y"]) / 2 else steel
        for li in poly.loop_indices:
            ca.data[li].color = (*col, 1.0)
    _step("strings", [strings])

    # hammers: shank from the rail to a wooden head with a felt tip toward the strings
    hs = []
    hz = I["hammer_z"]
    for i, (_, _, x) in enumerate(hx):
        shank = _obj(f"piano_hammer_shank_{i}", geo.cylinder, 0.0028, (x, ry1 - 0.017, rz1 - 0.002),
                     (x, -0.154, hz - 0.010), segments=8, mat="hammers")
        geo.tint(shank, "#a07a4a")
        head = _obj(f"piano_hammer_head_{i}", geo.box, x - 0.0055, x + 0.0055, -0.170, -0.142,
                    hz - 0.014, hz + 0.004, mat="hammers")
        geo.tint(head, "#5a3b22")
        felt = _obj(f"piano_hammer_felt_{i}", geo.box, x - 0.006, x + 0.006, -0.144, -0.124,
                    hz - 0.016, hz + 0.006, mat="hammers", bev=0.003, seg=2)
        geo.tint(felt, "#ece4d2")
        hs += [shank, head, felt]
    hammers = geo.join(hs, "piano_hammers")
    _step("hammers", [hammers])


def build_bench():
    w, d, h, t = 0.80, 0.34, 0.49, 0.045
    cy = -1.03
    top = _obj("piano_bench_top", geo.box, -w / 2, w / 2, cy - d / 2, cy + d / 2, h - t, h,
               mat="case", bev=0.008, seg=4)
    legs, aprons = [], []
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        lx, ly = sx * (w / 2 - 0.05), cy + sy * (d / 2 - 0.045)
        bottom = [(lx - 0.016, ly - 0.016, 0.0), (lx + 0.016, ly - 0.016, 0.0),
                  (lx + 0.016, ly + 0.016, 0.0), (lx - 0.016, ly + 0.016, 0.0)]
        upper = [(lx - 0.024, ly - 0.024, h - t), (lx + 0.024, ly - 0.024, h - t),
                 (lx + 0.024, ly + 0.024, h - t), (lx - 0.024, ly + 0.024, h - t)]
        legs.append(_obj(f"piano_bench_leg_{i + 1:02d}", geo.loft, bottom, upper, mat="case", bev=0.003))
    ax = w / 2 - 0.05
    ay = d / 2 - 0.045
    aprons.append(_obj("piano_bench_apron_01", geo.box, -ax, ax, cy - ay - 0.012, cy - ay + 0.012,
                       h - t - 0.075, h - t, mat="case", bev=0.003))
    aprons.append(_obj("piano_bench_apron_02", geo.box, -ax, ax, cy + ay - 0.012, cy + ay + 0.012,
                       h - t - 0.075, h - t, mat="case", bev=0.003))
    for i, sx in enumerate((-1, 1)):
        aprons.append(_obj(f"piano_bench_apron_{i + 3:02d}", geo.box, sx * ax - 0.012, sx * ax + 0.012,
                           cy - ay, cy + ay, h - t - 0.075, h - t, mat="case", bev=0.003))
    _step("bench", [top] + legs + aprons)


def build_anchors():
    out = []
    for name, loc in (("piano_view", (0.25, -1.30, 1.05)), ("piano_view_target", (0.0, -0.46, 0.80)),
                      ("piano_inside_view", (0.35, -1.25, 1.95)), ("piano_inside_view_target", (0.0, -0.10, 1.05))):
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "SPHERE"
        e.empty_display_size = 0.05
        e.location = loc
        _coll.objects.link(e)
        e.parent = _root
        names.set_name(e, name, data=False)
        out.append(e)
    return out


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
def build_steps(collection=None):
    """Yield after each group of parts. Returns the root through StopIteration.value."""
    global _coll, _root
    BUILD_ORDER.clear()
    scene = bpy.context.scene
    _coll = bpy.data.collections.get("obj_piano") or bpy.data.collections.new("obj_piano")
    if _coll.name not in scene.collection.children:
        scene.collection.children.link(_coll)
    _root = bpy.data.objects.new("obj_piano", None)
    _coll.objects.link(_root)
    names.set_name(_root, "obj_piano", data=False)
    materials()
    yield "materials"
    for fn in (build_case, build_lid, build_hardware, build_interior, build_keys,
               build_sheet_and_fallboard, build_bench):
        fn()
        yield fn.__name__
    build_anchors()
    yield "anchors"
    return _root


def build(collection=None):
    gen = build_steps(collection)
    try:
        while True:
            next(gen)
    except StopIteration as stop:
        return stop.value


MOVING = {"piano_fallboard", "piano_lid", "piano_sheet", "piano_interior", "piano_strings", "piano_hammers"}


def static_parts(root):
    return [o for o in root.children if o.type == "MESH" and o.name not in MOVING
            and not o.name.startswith("piano_key_")]


def export_prep(root):
    """Duplicate the static meshes and join the copies into `piano_static` (MESHES.md:
    the export joins each root's static parts). Returns (objects to export, undo)."""
    copies = []
    for o in static_parts(root):
        c = o.copy()
        c.data = o.data.copy()
        c.name = o.name + "_tmp"
        _coll.objects.link(c)
        c.parent = root
        copies.append(c)
    static = geo.join(copies, "piano_static")
    export = [root] + [o for o in root.children if o is not static and o not in static_parts(root)] + [static]

    def undo():
        me = static.data
        bpy.data.objects.remove(static)
        bpy.data.meshes.remove(me)
    return export, undo
