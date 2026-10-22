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

# Piano bench (obj_piano build_bench and the ornament sheet share these). Metres.
BENCH = dict(w=0.80, d=0.34, h=0.49, t=0.045, apron=0.075, leg_x=0.35, cy=-1.03)

# The two finish options for the owner (sRGB). Room context colours are in COL.
FINISHES = {
    "black": dict(label="Polished black", material="mat_piano_case",
                  base="#060606", note="black lacquer under a mirror clear coat"),
    "walnut": dict(label="Warm dark walnut", material="mat_piano_case",
                   base="#4a2c1a", dark="#2a170d", light="#6b4329",
                   note="walnut veneer under a satin-gloss clear coat"),
}


# ---------------------------------------------------------------------------
# The room (set_room and where every root stands). Proposed 2026-10-22 on the room
# plan sheet (blender/design/room_plan_sheet.py); the owner approves the sheet before
# any of it is modelled. World metres, Blender axes (MESHES.md section 1): origin on the
# floor at the room's centre, back wall (window, desk) at +Y, viewer at -Y, left wall
# (bed, frames) at -X, right wall (piano, guitars) at +X, Z up.
#
# A large master bedroom in an older Pune flat: 4.40 x 4.20 m (14 ft 5 in x 13 ft 9 in),
# 3.00 m clear ceiling. Smaller than this and the bed, the desk chair and the piano
# bench start to collide; the 3 m ceiling is what lets the wall guitars hang clear of
# the piano's open lid.
# ---------------------------------------------------------------------------
ROOM = dict(
    width=4.40,                 # X, left wall to right wall (inner faces)
    depth=4.20,                 # Y, front wall to back wall
    height=3.00,                # floor to ceiling, clear
    wall_back_t=0.23,           # outer wall with the window (230 mm brick)
    wall_side_t=0.15,           # inner walls (150 mm block)
    skirting_h=0.10, skirting_t=0.012,
)
RX, RY = ROOM["width"] / 2, ROOM["depth"] / 2   # inner faces at x = +-RX, y = +-RY

# Openings and fittings in the walls.
WINDOW = dict(              # back wall, over the bed's head; aluminium sliding window, MS grill
    x0=-1.95, x1=-0.75, sill=1.05, head=2.10,
    ledge_d=0.15, ledge_t=0.03,     # stone sill ledge inside, the plant stands on it
)
DOOR = dict(                # left wall near the front corner, as in the owner's photo
    wall="left", y0=-2.00, y1=-1.10, head=2.10, leaf_t=0.035,
    hinge="front",                  # hinged at y0, swings in and lies along the front wall
)
SWITCH = dict(wall="left", y=-0.92, z=1.20, w=0.20, h=0.13)   # modular board, latch side
LIGHT = dict(x=0.10, y=0.50, canopy_d=0.12, drop=0.45, shade_d=0.40, shade_h=0.15)  # pendant over the free floor, bottom at 2.40

# Where each root stands. x, y: the root's origin in the world; yaw: degrees about +Z
# (counter-clockwise from above), 0 = the object's front faces -Y. Sizes are footprints
# (w along the object's own X, d along its own Y, h up); the prop sheets refine them.
LAYOUT = dict(
    bed=dict(x=-1.475, y=1.10, yaw=0, w=1.45, d=2.00, h=0.55, head_h=1.00),   # head on the back wall
    bookshelf=dict(x=-2.05, y=-0.35, yaw=90,  w=0.80, d=0.30, h=1.95),
    rug=dict(x=0.10, y=-0.20, yaw=0, w=1.50, d=2.30, h=0.01),
    desk=dict(x=0.025, y=1.695, yaw=0, w=1.45, d=0.75, h=0.75, top_t=0.03),   # back edge 3 cm off the wall
    chair=dict(x=0.05, y=0.92, yaw=165, w=0.66, d=0.66, h=1.02, seat=0.47),
    monitor=dict(x=0.10, y=1.79, w=0.62, h=0.41, t=0.035, z=1.055),           # body centre; screen 0.56 x 0.35
    speakers=dict(dx=0.52, y=1.87, w=0.17, d=0.25, h=0.28, pad_h=0.10),       # centres at monitor x -+ dx
    dj=dict(x=-0.43, y=1.50, w=0.44, d=0.28, h=0.05),
    interface=dict(x=-0.22, y=1.73, w=0.18, d=0.12, h=0.05),
    lightstick=dict(x=-0.49, y=1.69, w=0.26, d=0.06, h=0.06),                 # lying along X
    keyboard=dict(x=0.10, y=1.44, w=0.44, d=0.13),
    mic=dict(clamp=(0.47, 2.05), elbow=(0.52, 1.93, 1.45), capsule=(0.56, 1.52, 1.16)),
    plant=dict(x=-0.92, y=RY - 0.08, pot_d=0.14, h=0.38),                     # on the sill ledge
    rack=dict(x=1.15, y=1.745, yaw=22, w=0.60, d=0.50, h=0.95, slots=3, pitch=0.15, cradle=0.10, lean=15),
    piano=dict(x=RX - 0.05, y=0.95, yaw=-90, bench_in=0.22),                  # case back 5 cm off the wall; bench rests 22 cm in from BENCH.cy
    frames=dict(y=(1.21, 1.53, 1.85), z=1.55, w=0.30, h=0.40, t=0.03),       # left wall, front to back
    panels_guitar=dict(y0=0.10, y1=1.80, z0=1.62, z1=2.86, t=0.05),           # right wall, behind the guitars
    panels_desk=dict(x=(-0.42, 0.62), w=0.50, z0=1.15, z1=2.15, t=0.05),      # back wall, behind each speaker
)

# Wall guitars (guitar_01 to _03, right wall, back to front = left to right from the
# hero view). Bottoms in one line 8 cm above the piano lid opened fully to 90 degrees.
WALL_GUITARS = dict(
    y=(1.45, 0.95, 0.45), bottom=1.72, off_wall=0.10,
    length=(1.07, 0.99, 0.99), width=(0.43, 0.32, 0.32), hook_from_top=0.18,
)

# The hero camera: the room view the website opens on (room_view, room_view_target,
# still_cam_home). Standing just inside the front wall, left of centre, as in the
# owner's photo, looking 30 cm above the screen's centre so the monitor sits in the
# middle of the frame, a little low; vertical field of view in degrees (about a 22 mm
# lens on full frame).
HERO = dict(pos=(-0.70, -2.00, 1.60), target=(0.10, 1.77, 1.35), vfov=50,
            phone_vfov=70)   # still_cam_phone: same place, aimed at the monitor
