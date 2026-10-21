"""Constants every Blender script shares: paths, units, note names, colours."""
import os

BLENDER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = os.path.abspath(os.path.join(BLENDER_DIR, ".."))
MESHES_MD = os.path.join(REPO, "scene", "objects", "MESHES.md")
OUT = os.path.join(BLENDER_DIR, "out")            # .blend files and GLBs, git ignores it
FOOTAGE = os.path.join(REPO, "video-local", "footage")

# Units: metres, Blender Z up, objects face -Y (MESHES.md section 1).
MM = 0.001

# Piano keys: scientific pitch, sharps only, written "s" (MESHES.md section 1).
NOTE_NAMES = ["c", "cs", "d", "ds", "e", "f", "fs", "g", "gs", "a", "as", "b"]
WHITE_PCS = {0, 2, 4, 5, 7, 9, 11}
MIDI_A0, MIDI_C8 = 21, 108


def key_name(midi):
    return f"piano_key_{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def is_white(midi):
    return midi % 12 in WHITE_PCS


# Palette for the room (sRGB hex). The room sketch and the owner's photo set these.
COL = {
    "lacquer_black": "#060606",
    "walnut_dark": "#2a170d",
    "walnut_mid": "#4a2c1a",
    "walnut_light": "#6b4329",
    "ivory": "#ebe3d0",
    "ebony": "#0d0c0b",
    "felt_red": "#6a1a20",
    "felt_cream": "#e4dac4",
    "brass": "#c8994c",
    "oak_dark": "#5a3a22",
    "oak_light": "#8a5d3a",
    "wall": "#e4ddd2",
    "skirting": "#efebe4",
    "dawn_sky": "#8fb0ec",
    "dawn_world": "#24365c",
    "lamp_warm": "#ffb066",
}


# ---------------------------------------------------------------------------
# Upright piano (obj_piano). Metres, in the piano's own frame: back of the case at
# y = 0, front toward -Y, floor at z = 0, centred on x = 0. A studio upright in the
# size class of the common 121 cm models: 1.53 m wide, 1.217 m high, 0.605 m deep.
# The 2D design sheet (blender/design/piano_design_sheet.py) and the 3D builder
# (blender/props/obj_piano.py) both read these, so the drawing and the model agree.
# ---------------------------------------------------------------------------
KT = 0.735                      # top of the white keys above the floor
PIANO = dict(
    # case
    width=1.530, side_t=0.030, side_depth=0.400, case_top=1.195, floor_gap=0.035,
    back_t=0.020,
    lid_t=0.022, lid_over_side=0.010, lid_over_front=0.012, lid_over_back=0.008,
    lid_open_deg=55,            # for stills only; the site sets the angle in code
    crown_h=0.035, crown_proud=0.006,
    # upper front panel, music rest, sheet
    panel_face_y=-0.360, panel_back_y=-0.335, panel_bottom=KT - 0.020,
    inset_bottom=KT + 0.270, inset_top=1.135, inset_half_w=0.640, inset_proud=0.006,
    ledge_z=KT + 0.215, ledge_t=0.018, ledge_lip_top=KT + 0.252, ledge_front_y=-0.448,
    ledge_half_w=0.440,
    sheet_w=0.420, sheet_h=0.297, sheet_lean_deg=5.0,
    # keys (88: A0 to C8, 52 white, 36 black)
    white_pitch=0.0235, white_gap=0.0009, white_len=0.150, white_h=0.022,
    black_len=0.095, black_w=0.0128, black_top_w=0.0098, black_up=0.0127, black_taper=0.010,
    key_back_y=-0.405,
    # key cheeks (arms): a quarter ellipse from the top of the arm down to its nose
    cheek_back_y=-0.395, cheek_front_y=-0.585, cheek_curve_y=-0.425,
    cheek_top=KT + 0.080, cheek_nose=KT + 0.012, cheek_bottom=KT - 0.075,
    # key slip (the rail in front of the keys) and the keybed
    slip_front_y=-0.583, slip_back_y=-0.562, slip_top=KT - 0.016,
    # fallboard (key cover): hinge at its back lower edge, opens up and back
    fall_pivot_y=-0.402, fall_pivot_z=KT + 0.022, fall_len=0.177, fall_t=0.022,
    fall_nose=0.010, fall_half_w=0.6105, fall_open_deg=95,
    # lower case
    lower_face_y=-0.345, lower_back_y=-0.320, lower_inset_half_w=0.580,
    lower_inset_bottom=0.155, lower_inset_top=KT - 0.140,
    toe_rail_front_y=-0.370, toe_rail_top=0.095,
    # consoles (legs) and toe blocks
    toe_x=0.690, toe_w=0.072, toe_front_y=-0.600, toe_back_y=-0.300,
    console_w=0.048, console_back_y=-0.330, console_front_bottom_y=-0.565,
    console_front_top_y=-0.575, console_waist=0.085,
    # pedals: soft, sostenuto (practice on many uprights), sustain
    pedal_x=(-0.085, 0.0, 0.085), pedal_back_y=-0.360, pedal_front_y=-0.475,
    pedal_z=0.060, pedal_t=0.012, pedal_w_back=0.018, pedal_w_front=0.034,
    # castors in floor cups, lid hinges
    cup_r=0.038, cup_h=0.016, castor_r=0.013,
    cups=((-0.690, -0.555), (0.690, -0.555), (-0.700, -0.060), (0.700, -0.060)),
    hinge_x=(-0.550, 0.0, 0.550), hinge_r=0.0045, hinge_len=0.060,
)

# The two finish options for the owner (sRGB). Room context colours are in COL.
FINISHES = {
    "black": dict(label="Polished black", material="mat_piano_case",
                  base="#060606", note="black lacquer under a mirror clear coat"),
    "walnut": dict(label="Warm dark walnut", material="mat_piano_case",
                   base="#4a2c1a", dark="#2a170d", light="#6b4329",
                   note="walnut veneer under a satin-gloss clear coat"),
}
