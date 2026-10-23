"""Room plan v2 (proposed 2026-10-23, NOT approved yet): half music studio, half AI lab.

Every number the v2 room plan sheet (blender/design/room_plan_v2_sheet.py) and the v2
blockout (blender/design/room_plan_v2_blockout.py) draw. Nothing in blender/build.py or
the props reads this module: the approved 2026-10-22 plan in constants.py stays in force
until the owner approves this one, then its blocks replace LAYOUT, WINDOW, WALL_GUITARS
and HERO there.

World metres, Blender axes (MESHES.md section 1): origin on the floor at the room's
centre, back wall (window) at +Y, the hero camera at -Y, left wall (AI lab, door) at -X,
right wall (piano, guitars) at +X, Z up. yaw: degrees about +Z, counter-clockwise from
above; 0 = the object's front faces -Y (towards the hero camera).

Sizes are real products' outside dimensions (w across the front, d front to back, h up),
from the makers' published specs as we remember them. UNSURE marks the ones to re-check
against the maker's page before modelling.
"""
import math

from . import constants as C

ROOM = C.ROOM                                    # unchanged: 4.40 x 4.20 x 3.00 m
RX, RY, H = C.RX, C.RY, C.ROOM["height"]
DOOR = C.DOOR                                    # unchanged: left wall by the front corner
SWITCH = C.SWITCH                                # unchanged

# Window: same size and type, moved to the centre of the back wall (decision 2026-10-23).
WINDOW_V2 = dict(C.WINDOW, x0=-0.60, x1=0.60)    # sill 1.05, head 2.10, stone ledge 15 cm

# Pendant: on the room's centre line, in front of the window, bottom at 2.40.
LIGHT_V2 = dict(C.LIGHT, x=0.0, y=0.45)

TOP = 0.75                                       # desk top surface
# ---------------------------------------------------------------------------
# The AI-lab desk, option A (decision 2026-10-23): one continuous white L top.
# The return is measured from the back wall (180 = 80 shared with the back run + 100).
# ---------------------------------------------------------------------------
ALEX = (0.36, 0.58, 0.70)                        # IKEA ALEX-style drawer unit w, d, h
PUCK = 0.02                                      # chrome pucks between unit and top (as in the photos)
DESK_V2 = dict(
    top=TOP, t=0.03, edge_r=0.015, inner_r=0.06, colour="#f2f2ef",
    back=dict(x0=-RX, x1=WINDOW_V2["x0"] - 0.05, y0=RY - 0.80, y1=RY),     # 155 x 80
    ret=dict(x0=-RX, x1=-RX + 0.60, y0=RY - 1.80, y1=RY - 0.80),            # +100 x 60
    led_in=0.05,                                  # LED strip under the top, 5 cm in from the edge
    drawers=[                                     # (centre x, centre y, yaw)
        (-RX + 0.01 + ALEX[0] / 2, RY - 0.02 - ALEX[1] / 2, 0),             # back run, corner end
        (WINDOW_V2["x0"] - 0.05 - 0.01 - ALEX[0] / 2, RY - 0.02 - ALEX[1] / 2, 0),   # back run, window end
        (-RX + 0.01 + ALEX[1] / 2, RY - 1.80 + 0.01 + ALEX[0] / 2, 90),     # return, far end, faces the room
    ],
)
_d = DESK_V2["drawers"]
KNEE_BACK = (_d[0][0] + ALEX[0] / 2, _d[1][0] - ALEX[0] / 2)       # x range under the back run
KNEE_RET = (_d[2][1] + ALEX[0] / 2, _d[0][1] - ALEX[1] / 2)        # y range under the return
XM = (KNEE_BACK[0] + KNEE_BACK[1]) / 2           # centre line of the monitor stack and the chair
EAR = (XM, 0.95, 1.15)                           # seated listener at the back run

# speakers: ADAM A7V white, on ISO-155-style stands, tweeter about 115, back 20 cm off the wall
A7V = (0.201, 0.288, 0.337)
ISO_H = 0.135                                    # UNSURE: stand at its tall setting
TWEETER_UP = 0.265                               # UNSURE: tweeter centre above the cabinet's base
SPK_DX = 0.815 / 2 + 0.03 + A7V[0] / 2           # beside the ultrawide, 3 cm gap
SPK_Y = RY - 0.20 - A7V[1] / 2


def _aim(x, y, tx, ty):
    """yaw that turns an object's front (-Y) from (x, y) towards (tx, ty)."""
    return math.degrees(math.atan2(tx - x, -(ty - y)))


SPEAKERS_V2 = [dict(x=XM + s * SPK_DX, y=SPK_Y, z=TOP + ISO_H, yaw=_aim(XM + s * SPK_DX, SPK_Y, EAR[0], EAR[1]))
               for s in (-1, 1)]

# ---------------------------------------------------------------------------
# The music side
# ---------------------------------------------------------------------------
PIANO_V2 = dict(x=RX - 0.05, y=1.00, yaw=-90, bench_in=0.22)     # case back 5 cm off the right wall
RACK_V2 = dict(C.LAYOUT["rack"], x=0.95, y=1.67, yaw=-50)          # back wall, right of the window
# what the rack and its leaning guitars really cover, in the rack's own frame (x0, x1, y0, y1):
# cradle from -0.30, the top bar at +0.13, guitar bodies and the lean to about -0.32 and +0.18
RACK_EXT = (-0.32, 0.18, -0.25, 0.25)

# Wall guitars, back to front = left to right from the hero camera. Bottoms on one line
# 8.3 cm above the piano lid at 90 degrees (same rule as 2026-10-22). Real outside sizes:
# guitar_01 Lucille (ES-355 shape) 107 x 41 UNSURE; guitar_02 from guitar_specs (97.7 x 32.3);
# guitar_03 the double-neck (EDS-1275 shape) 110 x 43 UNSURE, hung on two hooks, one per head.
WG_LEN = (1.07, 0.977, 1.10)
WG_WID = (0.41, 0.323, 0.43)
WG_GAP = 0.12                                    # clear gap between bodies
WG_BACK = RY - 0.15                              # the back edge of guitar_01's body
_ys, _y = [], WG_BACK
for _w in WG_WID:
    _ys.append(_y - _w / 2)
    _y -= _w + WG_GAP
WALL_GUITARS_V2 = dict(C.WALL_GUITARS, y=tuple(round(v, 4) for v in _ys), length=WG_LEN, width=WG_WID,
                       hooks=(1, 1, 2), hook_from_top=(0.18, 0.180, 0.18))
PANEL_GUITAR_V2 = dict(y0=0.45, y1=2.02, z0=1.62, z1=2.92, t=0.05)   # dark fabric acoustic panel behind them

# ---------------------------------------------------------------------------
# Hero camera: on the centre line just inside the front wall, looking at the window.
# 54 deg vertical (about 23.5 mm on full frame... see the sheet): 84 deg across on 16:9, so
# both side walls show from y = 0.43 back, which is where every clickable object stands.
# ---------------------------------------------------------------------------
HERO_V2 = dict(pos=(0.0, -2.00, 1.55), target=(0.0, RY, 1.45), vfov=54,
               phone_vfov=70, phone_target=(XM, RY - 0.22, 1.30))

# ---------------------------------------------------------------------------
# Every component. at = (x, y, z) of the bottom centre; size = (w, d, h); yaw as above.
# role: the obj_* root it belongs to (interactive) or "set" (set dressing).
# shape: box | cyl (w = diameter) | slab (thin, on a wall) | special (the blockout knows it)
# ---------------------------------------------------------------------------
W_, B_, G_ = "#f2f2ef", "#1b1b1d", "#c9ccd1"     # white, black, aluminium

COMPONENTS = []


def cm(m):
    return f"{m * 100:.0f}"


def part(key, label, model, size, at, yaw=0, role="set", shape="box", col=W_, side="ai", note="", glow=None):
    COMPONENTS.append(dict(key=key, label=label, model=model, size=size, at=at, yaw=yaw, role=role,
                           shape=shape, col=col, side=side, note=note, glow=glow))


# --- the desk and what is on the back run
part("desk", "L desk", "one white top, 3 cm, rounded front edge (option A)", (1.55, 0.80, TOP), (0, 0, 0),
     shape="special", note="back run 155 x 80, return 180 x 60 from the back wall")
for i, (x, y, yaw) in enumerate(DESK_V2["drawers"]):
    part(f"alex_{i + 1}", f"Drawer unit {i + 1}", "IKEA ALEX style, white, 5 drawers", ALEX, (x, y, 0), yaw)
part("led", "LED strip under the desk", "Philips Hue Play gradient style", (0, 0, 0), (0, 0, TOP - 0.03),
     shape="special", glow="#7fb6ff")
UW = dict(w=0.815, h=0.363, d=0.09, z=0.853, y=RY - 0.24)
part("ultrawide", "Main screen, 34 in curved", "Samsung Odyssey OLED G8 34 (21:9, 1800R)",
     (UW["w"], UW["d"], UW["h"]), (XM, UW["y"], UW["z"]), role="obj_rig", col=B_,
     note="the live training dashboard (projects as runs); 79.7 x 33.4 active", glow="#3a7bd5")
SD = dict(w=0.623, h=0.362, d=0.03, z=UW["z"] + UW["h"] + 0.04, y=RY - 0.22)
part("studio_display", "Top screen, 27 in", "Apple Studio Display 27 (16:9), on the same pole",
     (SD["w"], SD["d"], SD["h"]), (XM, SD["y"], SD["z"]), role="obj_monitor", col=G_,
     note="the posts (monitor_screen 16:10 inside the 16:9 glass)", glow="#8fb8ff")
part("pole", "Monitor pole, dual stack", "clamp pole, white", (0.04, 0.04, 0.95), (XM, RY - 0.07, TOP), shape="cyl")
part("screenbar", "Monitor light bar", "BenQ ScreenBar Halo", (0.50, 0.10, 0.03),
     (XM, SD["y"] - 0.02, SD["z"] + SD["h"]), col=B_, glow="#fff4e0")
for i, s in enumerate(SPEAKERS_V2):
    part(f"iso_{i + 1}", f"Speaker stand {'LR'[i]}", "IsoAcoustics ISO-155 style", (0.155, 0.19, ISO_H),
         (s["x"], s["y"], TOP), s["yaw"], col="#2a2a2c", note="UNSURE height: tall setting")
    part(f"a7v_{i + 1}", f"Studio monitor {'LR'[i]}", "ADAM A7V, Arctic White", A7V, (s["x"], s["y"], s["z"]),
         s["yaw"], role="obj_studio", note=f"tweeter at {cm(s['z'] + TWEETER_UP)}, toed in {abs(s['yaw']):.0f} deg")
KL = [(-RX + 0.18, RY - 0.08), (DESK_V2["back"]["x1"] - 0.04, RY - 0.06)]
for i, (x, y) in enumerate(KL):
    part(f"keylight_pole_{i + 1}", f"Key light pole {i + 1}", "desk clamp pole", (0.025, 0.025, 1.05),
         (x, y, TOP), shape="cyl", col=W_)
    part(f"keylight_{i + 1}", f"Key light {i + 1}", "Elgato Key Light Mk.2, white", (0.35, 0.06, 0.25),
         (x, y - 0.05, 1.62), _aim(x, y, EAR[0], EAR[1]), col=W_, note="UNSURE panel size",
         glow="#ffffff")
part("camera", "Camera on a flex arm", "Sony ZV-E10 II with kit lens, Elgato Flex Arm", (0.115, 0.10, 0.07),
     (XM - 0.44, RY - 0.38, 1.27), _aim(XM - 0.44, RY - 0.38, EAR[0], EAR[1]), col=B_)
MIC = dict(clamp=(DESK_V2["back"]["x1"] - 0.14, RY - 0.04), elbow=(DESK_V2["back"]["x1"] - 0.22, RY - 0.20, 1.55),
           capsule=(XM + 0.27, 1.40, 1.08))
part("mic", "Microphone on its arm", "Shure MV7+ white on a RODE PSA1+ white arm", (0.066, 0.153, 0.066),
     (MIC["capsule"][0], MIC["capsule"][1], MIC["capsule"][2] - 0.033), role="obj_mic", shape="special",
     note="email; arm reach 76 cm of 82")
part("interface", "Audio interface", "Universal Audio Apollo x4", (0.235, 0.18, 0.09), (XM - 0.145, RY - 0.38, TOP),
     role="obj_studio", col=B_, note="UNSURE size; big monitor knob = volume, preamp knob = pan (owner, 2026-10-23)")
part("streamdeck", "Stream Deck", "Elgato Stream Deck MK.2 white", (0.118, 0.084, 0.03), (XM + 0.245, RY - 0.42, TOP))
part("mat", "Felt desk mat", "grey felt, 80 x 30", (0.80, 0.30, 0.004), (XM, 1.47, TOP), col="#8d9096")
part("keyboard", "Keyboard", "Keychron Q1 Max, white", (0.327, 0.145, 0.04), (XM - 0.045, 1.47, TOP),
     note="UNSURE height")
part("mouse", "Mouse", "Logitech MX Master 3S, pale grey", (0.084, 0.125, 0.051), (XM + 0.265, 1.46, TOP), col="#d5d6d8")
part("snake_plant", "Snake plant", "white pot", (0.12, 0.12, 0.45), (DESK_V2["back"]["x1"] - 0.13, 1.42, TOP),
     shape="cyl", col="#3f6b3a")
# --- the return
part("pc", "Training rig (PC)", "Lian Li O11 Vision white, RTX 5090 Founders Edition inside",
     (0.272, 0.446, 0.465), (-RX + 0.03 + 0.446 / 2, 1.30, TOP), 90, role="obj_rig",
     note="window side faces the camera, front glass faces the chair; GPU 30.4 x 13.7", glow="#9fd0ff")
part("dj", "DJ controller", "two-deck, Pioneer DDJ-FLX4 shape (no logos)", (0.483, 0.273, 0.059),
     (-RX + 0.60 - 0.02 - 0.273 / 2, 0.60, TOP), 90, role="obj_studio", col=B_,
     note="faces the chair at the return")
part("mstand", "Laptop stand", "Rain Design mStand, silver", (0.26, 0.235, 0.15),
     (-RX + 0.03 + 0.248 / 2, 0.60, TOP), 90, col=G_, note="UNSURE height")
part("laptop", "Laptop", "MacBook Pro 16, silver, open", (0.356, 0.248, 0.24),
     (-RX + 0.03 + 0.248 / 2, 0.60, TOP + 0.15), 90, col=G_, note="behind the decks, as a DJ laptop", glow="#cfe0ff")
part("lightstick", "K-pop lightstick", "generic, our own shape, standing in a cradle", (0.07, 0.07, 0.27),
     (-RX + 0.08, 0.98, TOP), role="obj_studio", shape="cyl", col="#e9e3f5", glow="#d9a0ff")
# --- the walls of the AI side
part("pegboard", "Pegboard, backlit", "IKEA SKADIS 76 x 56 white", (0.76, 0.02, 0.56), (-RX + 0.03, 0.90, 1.32), 90,
     shape="slab", glow="#9fc8ff")
part("headphones", "Headphones on the pegboard", "Audio-Technica ATH-M50x white", (0.19, 0.08, 0.21),
     (-RX + 0.09, 0.72, 1.48), 90, col=W_)
part("neon", "Neon sign (our words)", "custom white neon, text from content", (0.70, 0.02, 0.26),
     (-RX + 0.03, 0.90, 1.98), 90, shape="slab", col="#ffffff", glow="#ffffff",
     note="placeholder text; read from content/")
part("nanoleaf", "Light panels", "Nanoleaf Shapes Triangles, 7 panels", (0.58, 0.01, 0.52),
     (-RX + 0.01, 1.78, 1.70), 90, shape="slab", glow="#86a8ff", note="23 cm triangles, UNSURE")
LEDGE = dict(x0=XM - 0.575, x1=XM + 0.575, z=1.92, d=0.12, t=0.04)
part("ledge", "Floating ledge", "white floating shelf 115 x 12", (1.15, LEDGE["d"], LEDGE["t"]),
     (XM, RY - LEDGE["d"] / 2, LEDGE["z"]))
for i, dx in enumerate((-0.38, 0.0, 0.38)):
    part(f"frame_{i + 1}", f"Frame {i + 1}", "black frame, 30 x 40 portrait (3:4)", (0.30, 0.03, 0.40),
         (XM + dx, RY - 0.04, LEDGE["z"] + LEDGE["t"]), role="obj_frames", col="#26262a",
         note=["GitHub", "LinkedIn", "X"][i])
part("chair", "Chair", "Herman Miller Aeron size B, Mineral", (0.686, 0.69, 1.06), (XM + 0.125, 1.00, 0), 200,
     shape="special", col="#c9ccd0")
# --- the music side
part("piano", "Upright piano", "our approved black upright (constants.PIANO)", (1.53, 0.60, 1.217),
     (PIANO_V2["x"] - 0.30, PIANO_V2["y"], 0), -90, role="obj_piano", shape="special", col="#0a0a0a", side="music")
part("bench", "Piano bench", "constants.BENCH", (C.BENCH["w"], C.BENCH["d"], C.BENCH["h"]),
     (PIANO_V2["x"] + C.BENCH["cy"] + PIANO_V2["bench_in"], PIANO_V2["y"], 0), -90, col="#0a0a0a", side="music")
for i in range(3):
    part(f"guitar_0{i + 1}", ["Lucille", "Woodstock Strat", "Double-neck"][i],
         ["B.B. King's ES-355 shape, black", "Hendrix's white Strat (built)", "Jimmy Page's cherry double-neck"][i],
         (WG_WID[i], 0.05 if i else 0.045, WG_LEN[i]),
         (RX - C.WALL_GUITARS["off_wall"], WALL_GUITARS_V2["y"][i], C.WALL_GUITARS["bottom"]), -90,
         role="obj_guitars", shape="special", col=["#141414", "#ece8dc", "#8b1e22"][i], side="music")
part("panel_guitar", "Acoustic panel", "dark fabric panel behind the guitars", (1.57, 0.05, 1.30),
     (RX - 0.025, (PANEL_GUITAR_V2["y0"] + PANEL_GUITAR_V2["y1"]) / 2, PANEL_GUITAR_V2["z0"]), -90,
     shape="slab", col="#34363c", side="music")
part("rack", "Guitar rack (3)", "floor rack, approved shape", (0.50, 0.50, 0.95), (RACK_V2["x"], RACK_V2["y"], 0),
     RACK_V2["yaw"], role="obj_guitars", shape="special", col="#232326", side="music",
     note="04 Number One (built), 05 Explorer, 06 TOD10")
part("rug", "Rug", "wool, 150 x 230", (1.50, 2.30, 0.01), (0.05, 0.15, 0), col="#6f5a4a", side="music")
part("pendant", "Ceiling light", "pendant, 40 cm shade", (0.40, 0.40, 0.15), (LIGHT_V2["x"], LIGHT_V2["y"], 2.40),
     role="obj_light", shape="cyl", col="#d9d4c8", glow="#ffb066", side="music")
part("plant", "Plant on the sill", "young monstera, terracotta pot", (0.14, 0.14, 0.38), (0.28, RY - 0.08, 1.05),
     role="obj_plant", shape="cyl", col="#4f7a46", side="music", note="grows a leaf each visit")
part("window", "Window", "aluminium sliding, 120 x 105, MS grill", (1.20, 0.23, 1.05), (0, RY, 1.05),
     role="obj_window", shape="special", side="music", note="sky follows Pune's time and weather")


# Interactive objects (version 1 limit is 10): obj root -> (number, label, what a click does)
OBJECTS_V2 = [
    ("obj_monitor", "Posts screen (top, 27 in)", "glide in, posts list, keyboard works"),
    ("obj_rig", "Training rig: PC and main screen", "fans pulse, the dashboard lists projects as training runs"),
    ("obj_mic", "Mic on its arm", "email; later the talk-to-me agent"),
    ("obj_frames", "Three frames on the ledge", "GitHub, LinkedIn, X"),
    ("obj_studio", "Studio desk: DJ decks, console, speakers, lightstick", "tracks, loops, pan, volume, K-pop hook"),
    ("obj_piano", "Upright piano", "88 keys, both lids, About on the music rest"),
    ("obj_guitars", "Guitars: wall 01 to 03, rack 04 to 06", "lift, era card, lick"),
    ("obj_light", "Ceiling light", "room light on and off"),
    ("obj_window", "Window", "live Pune sky (no click)"),
    ("obj_plant", "Plant on the sill", "water it, a leaf per visit"),
]
