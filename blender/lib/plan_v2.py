"""Room plan v2 (approved 2026-10-24): half music studio, half AI lab.

The room's layout: every place and size blender/build.py and the props build from, and the
numbers the v2 sheet (blender/design/room_plan_v2_sheet.py) and the v2 blockout
(blender/design/room_plan_v2_blockout.py) draw. It replaced the 2026-10-22 plan; from
constants.py it keeps ROOM, DOOR, SWITCH, the piano and bench, and takes the window's size,
the pendant, the rack's shape and the wall-guitar hanging rule, then moves them.

World metres, Blender axes (MESHES.md section 1): origin on the floor at the room's
centre, back wall (window) at +Y, the hero camera at -Y, left wall (AI lab, door) at -X,
right wall (piano, guitars) at +X, Z up. yaw: degrees about +Z, counter-clockwise from
above; 0 = the object's front faces -Y (towards the hero camera).

Sizes are real products' outside dimensions (w across the front, d front to back, h up),
from the makers' published specs as we remember them. UNSURE marks the ones to re-check
against the maker's page before modelling.

LAYOUT FIXES r2 (2026-10-24, PROPOSED, not approved; the owner sees a blockout before any
rebuild). The owner, after the first blockout: "DJ controller on the desk return, PC on the
floor under it. Window A, no panel, guitars lower with the lid stopping at 60 deg." So:
(1) the return is 150 and carries the DJ controller and the MacBook on its mStand; the PC
stands on the floor under the return's end, glass side to the camera; (2) window A, 150 x 140;
(3) the rack on the back wall between the window and the piano; (4) the wall guitars 24 cm
lower, the piano's top lid stopping at 60 deg; no panel.
"""
import math

from . import constants as C
from .piano_layout import lid_profile

ROOM = C.ROOM                                    # unchanged: 4.40 x 4.20 x 3.00 m
RX, RY, H = C.RX, C.RY, C.ROOM["height"]
DOOR = C.DOOR                                    # unchanged: left wall by the front corner
SWITCH = C.SWITCH                                # unchanged

# Window: centred on the back wall (decision 2026-10-23), bigger since the layout fixes (owner:
# "Window A"): 150 x 140, sill 95, head 235 (in line with the tops of the frames on the ledge).
# The stone ledge is 25 deep, 20 cm into the room (was 10) for the plant, 2 cm past each jamb.
WINDOW_V2 = dict(C.WINDOW, x0=0.55, x1=1.95, sill=0.95, head=2.35, ledge_d=0.25, ledge_horn=0.02)
LEDGE_IN = WINDOW_V2["ledge_d"] - 0.05           # how far the stone ledge stands into the room

# Pendant: on the room's centre line, in front of the window, bottom at 2.40.
LIGHT_V2 = dict(C.LIGHT, x=0.0, y=0.45)

TOP = 0.735                                      # desk top surface: ALEX 70 + top 3.5 (IKEA's own 3D file: 73.55 cm)
# ---------------------------------------------------------------------------
# The AI-lab desk, option A (decision 2026-10-23): one continuous white L top.
# The return is measured from the back wall: 150 = 80 shared with the back run + 70 (was 180).
# Under it, from the back wall: drawer unit 1 (it belongs to the back run's corner end), 57 cm
# of knee space under the DJ controller, then the PC on the floor at the end. A white round
# leg (IKEA ADILS style, 4 cm) holds the return's free corner: the PC stands where the third
# drawer unit stood, so the desk keeps two drawer units, both under the back run.
# ---------------------------------------------------------------------------
ALEX = (0.36, 0.58, 0.70)                        # IKEA ALEX-style drawer unit w, d, h
PUCK = 0.0                                       # no pucks: the top sits straight on the ALEX units (IKEA's file)
RET_LEN = 1.80                                   # return, from the back wall (r3: back to the original 180)
BACK_X1 = -0.10                                  # r3: back run 210 (owner: "increase the size of table little bit more")
WIN_EDGE = min(BACK_X1, WINDOW_V2["x0"] - 0.04)  # last desk x free of the glass, for the pole and the mic
DESK_V2 = dict(
    top=TOP, t=0.035, edge_r=0.015, inner_r=0.06, colour="#f2f2ef",
    back=dict(x0=-RX, x1=BACK_X1, y0=RY - 0.80, y1=RY),                     # 140 x 80
    ret=dict(x0=-RX, x1=-RX + 0.60, y0=RY - RET_LEN, y1=RY - 0.80),         # +70 x 60
    led_in=0.05,                                  # LED strip under the top, 5 cm in from the edge
    drawers=[                                     # (centre x, centre y, yaw)
        (-RX + 0.01 + ALEX[0] / 2, RY - 0.02 - ALEX[1] / 2, 0),             # back run, corner end
        (BACK_X1 - 0.01 - ALEX[0] / 2, RY - 0.02 - ALEX[1] / 2, 0),         # back run, window end
        (-RX + 0.01 + ALEX[1] / 2, RY - RET_LEN + 0.01 + ALEX[0] / 2, 90),  # return, far end, faces the room
    ],
    legs=[],                                                                # (x, y), round, 4 cm, white
    leg_d=0.04,
)
_d = DESK_V2["drawers"]
KNEE_BACK = (_d[0][0] + ALEX[0] / 2, _d[1][0] - ALEX[0] / 2)       # x range under the back run
# The PC (Lian Li O11 Vision, 30.4 x 48 x 46.5) on the floor under the return's end, turned
# like the old one (yaw 90): the glass side faces the camera, the front glass faces the chair.
PC_SIZE = (0.304, 0.480, 0.4645)
# r3 (owner: "we'll keep the pc in the right side of studio monitor"): on the back run's
# window end, right of the right speaker, front glass to the camera.
PC_AT = (-RX + 0.03 + PC_SIZE[1] / 2, RY - 0.08 - PC_SIZE[0] / 2, TOP)   # r4: the L's inner corner, as in the photo
KNEE_RET = (_d[2][1] + ALEX[0] / 2, _d[0][1] - ALEX[1] / 2)        # y range free under the return
# speakers: ADAM A7V white, on ISO-155-style stands, tweeter about 115, back 20 cm off the wall
A7V = (0.200, 0.280, 0.337)                      # ADAM official W x D x H
ISO_H = 0.076                                    # ISO-155 short setting (official 76 mm), tilted up towards the ear
TWEETER_UP = 0.265                               # UNSURE: tweeter centre above the cabinet's base
SPK_DX = 0.815 / 2 + 0.03 + A7V[0] / 2           # beside the ultrawide, 3 cm gap
SPK_Y = RY - 0.20 - A7V[1] / 2
_ya = math.atan2(SPK_DX, SPK_Y - 0.95)           # toe-in towards the seated ear (y 95)
SPK_HALF_X = 0.5 * (A7V[0] * math.cos(_ya) + A7V[1] * math.sin(_ya))   # a toed-in speaker's half-width in x
# The stack centres on the knee space unless the left speaker would come within 2 cm of the left
# wall: with the bigger window the two speakers and the screens fill 140 cm almost exactly.
XM = max((KNEE_BACK[0] + KNEE_BACK[1]) / 2, PC_AT[0] + PC_SIZE[1] / 2 + 0.03 + SPK_DX + SPK_HALF_X)
                                                # r4: monitor stack centre line, clear of the corner PC
EAR = (XM, 0.95, 1.15)                           # seated listener at the back run


def _aim(x, y, tx, ty):
    """yaw that turns an object's front (-Y) from (x, y) towards (tx, ty)."""
    return math.degrees(math.atan2(tx - x, -(ty - y)))


SPEAKERS_V2 = [dict(x=XM + s * SPK_DX, y=SPK_Y, z=TOP + ISO_H, yaw=_aim(XM + s * SPK_DX, SPK_Y, EAR[0], EAR[1]))
               for s in (-1, 1)]
# The DJ controller on the return, facing the chair, centred over the return's knee space;
# the MacBook on its mStand behind it, against the left wall, as the DJ laptop.
DJ_Y = 0.60                                      # r3: the original place (owner: "bring back the dj contoller to original place")
DJ_SEAT = (-RX + 0.60 + 0.38, DJ_Y - 0.12)       # the chair turned to the decks (base checked as a circle)

# ---------------------------------------------------------------------------
# The music side
# ---------------------------------------------------------------------------
# The piano 10 cm forward (y 100 to 90), so the rack fits between the bigger window and the
# played bench.
PIANO_V2 = dict(x=RX - 0.05, y=0.60, yaw=-90, bench_in=0.22)     # case back 5 cm off the right wall
# The piano's top lid stops at 60 deg in the site's code (owner, 2026-10-24: "guitars lower with
# the lid stopping at 60"). A real upright lid has no stay: the code holds it there.
PIANO_LID_MAX_DEG = 60
# The rack against the back wall in the 78 cm between the window's ledge and the piano's toe:
# centred there it is 4 cm clear of the glass's edge and 6 cm from the piano, so it reads with
# both, the guitars on the wall above the piano continuing the line. yaw -55: slot 1 (04) is the
# left and nearest, 06 the right; faces about 35 deg off the camera, so all three bodies show.
RACK_V2 = dict(C.LAYOUT["rack"], x=0.23, y=1.80, yaw=-35)   # r3: back wall, between the desk's end and the window
# what the rack and its leaning guitars really cover, in the rack's own frame (x0, x1, y0, y1):
# cradle from -0.30, the top bar at +0.13, guitar bodies and the lean to about -0.32 and +0.18
RACK_EXT = (-0.32, 0.18, -0.25, 0.25)

# Wall guitars, back to front = left to right from the hero camera. The top lid is one piece
# across the whole case, so the guitars clear it by height, not by place. With the lid stopping
# at PIANO_LID_MAX_DEG, the bottoms sit 5 cm (rounded up to the cm) over the highest point the
# lid reaches, opening, inside the bodies' plane: 7.5 to 14.5 cm off the wall (2.5 cm behind
# the hook line to 2 cm of bridge and knobs in front of the body's face).
# Real outside sizes: guitar_01 Lucille (ES-355 shape) 107 x 41 UNSURE; guitar_02 from
# guitar_specs (97.7 x 32.3); guitar_03 the double-neck (EDS-1275 shape) 110 x 43 UNSURE,
# hung on two hooks, one per head.
WG_LEN = (1.07, 0.977, 1.10)
WG_WID = (0.41, 0.323, 0.43)
WG_GAP = 0.12                                    # clear gap between bodies
WG_BACK = RY - 0.15                              # the back edge of guitar_01's body
WG_BODY_BAND = (C.WALL_GUITARS["off_wall"] - 0.025, C.WALL_GUITARS["off_wall"] + 0.045)   # off the wall


def lid_reach(deg_max, band=WG_BODY_BAND, steps=15):
    """Highest z the piano's top lid reaches opening from 0 to deg_max, over the band (metres
    off the right wall), from lid_profile and the piano's place."""
    best = 0.0
    for i in range(steps):
        u = (RX - (band[0] + (band[1] - band[0]) * i / (steps - 1))) - PIANO_V2["x"]   # piano local y
        for k in range(int(deg_max * 4) + 1):
            pts, _ = lid_profile(k / 4)
            for (y0, z0), (y1, z1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 - u) * (y1 - u) <= 0 and y0 != y1:
                    best = max(best, z0 + (z1 - z0) * (u - y0) / (y1 - y0))
    return best


WG_BOTTOM = math.ceil((lid_reach(PIANO_LID_MAX_DEG) + 0.05) * 100) / 100     # 1.45
_ys, _y = [], WG_BACK
for _w in WG_WID:
    _ys.append(_y - _w / 2)
    _y -= _w + WG_GAP
WALL_GUITARS_V2 = dict(C.WALL_GUITARS, y=tuple(round(v, 4) for v in _ys), length=WG_LEN, width=WG_WID,
                       bottom=WG_BOTTOM, hooks=(1, 1, 2), hook_from_top=(0.18, 0.180, 0.18))
PANEL_GUITAR_V2 = None                           # no acoustic panel behind them (owner: "no panel")

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
part("desk", "L desk", "one white top, 3 cm, rounded front edge (option A)",
     (DESK_V2["back"]["x1"] - DESK_V2["back"]["x0"], 0.80, TOP), (0, 0, 0),
     shape="special", note=f"back run {cm(DESK_V2['back']['x1'] - DESK_V2['back']['x0'])} x 80, return {cm(RET_LEN)} x 60 from the back wall")
for i, (x, y, yaw) in enumerate(DESK_V2["drawers"]):
    part(f"alex_{i + 1}", f"Drawer unit {i + 1}", "IKEA ALEX style, white, 5 drawers", ALEX, (x, y, 0), yaw)
for i, (x, y) in enumerate(DESK_V2["legs"]):
    part(f"leg_{i + 1}", "Desk leg", "IKEA ADILS style, white, 4 cm round", (DESK_V2["leg_d"], DESK_V2["leg_d"], TOP - DESK_V2["t"]),
         (x, y, 0), shape="cyl", note="holds the return's free corner")
part("led", "LED strip under the desk", "Philips Hue Play gradient style", (0, 0, 0), (0, 0, TOP - 0.03),
     shape="special", glow="#7fb6ff")
UW = dict(w=0.814, h=0.364, d=0.128, z=0.853, y=RY - 0.24)
part("ultrawide", "Main screen, 34 in curved", "Samsung Odyssey OLED G8 34 (21:9, 1800R)",
     (UW["w"], UW["d"], UW["h"]), (XM, UW["y"], UW["z"]), role="obj_rig", col=B_,
     note="the live training dashboard (projects as runs); 79.7 x 33.4 active", glow="#3a7bd5")
SD = dict(w=0.623, h=0.362, d=0.03, z=UW["z"] + UW["h"] + 0.04, y=RY - 0.22)
# the posts canvas: 16:10, as tall as the 16:9 glass, centred in it (MESHES.md, obj_monitor)
SD_GLASS = (0.597, 0.336)                        # 27 in 16:9 active area, w x h
POSTS = dict(w=0.538, h=SD_GLASS[1])             # monitor_screen, 53.8 x 33.6
UW_ACTIVE = (0.797, 0.334)                       # 34 in 21:9 active area: rig_screen
part("studio_display", "Top screen, 27 in", "Apple Studio Display 27 (16:9), on the same pole",
     (SD["w"], SD["d"], SD["h"]), (XM, SD["y"], SD["z"]), role="obj_monitor", col=G_,
     note="the posts (monitor_screen 16:10 inside the 16:9 glass)", glow="#8fb8ff")
part("pole", "Monitor pole, dual stack", "clamp pole, white", (0.04, 0.04, 0.95), (XM, RY - 0.07, TOP), shape="cyl")
part("screenbar", "Monitor light bar", "BenQ ScreenBar Halo", (0.50, 0.10, 0.03),
     (XM, SD["y"] - 0.02, SD["z"] + SD["h"]), col=B_, glow="#fff4e0")
for i, s in enumerate(SPEAKERS_V2):
    part(f"iso_{i + 1}", f"Speaker stand {'LR'[i]}", "IsoAcoustics ISO-155 style", (0.155, 0.19, ISO_H),
         (s["x"], s["y"], TOP), s["yaw"], col="#2a2a2c", note="short setting, 76 mm, tilted up")
    part(f"a7v_{i + 1}", f"Studio monitor {'LR'[i]}", "ADAM A7V, Arctic White", A7V, (s["x"], s["y"], s["z"]),
         s["yaw"], role="obj_studio", note=f"tweeter at {cm(s['z'] + TWEETER_UP)}, toed in {abs(s['yaw']):.0f} deg")
KL = [(PC_AT[0] + PC_SIZE[1] / 2 + 0.06, RY - 0.06), (WIN_EDGE - 0.16, RY - 0.06)]   # 2: its panel ends clear of the glass
for i, (x, y) in enumerate(KL):
    part(f"keylight_pole_{i + 1}", f"Key light pole {i + 1}", "desk clamp pole", (0.025, 0.025, 1.05),
         (x, y, TOP), shape="cyl", col=W_)
    part(f"keylight_{i + 1}", f"Key light {i + 1}", "Elgato Key Light Mk.2, white", (0.35, 0.035, 0.25),
         (x, y - 0.05, 1.62), _aim(x, y, EAR[0], EAR[1]), col=W_, note="panel 35 x 25 (Elgato)",
         glow="#ffffff")
part("camera", "Camera on a flex arm", "Sony ZV-E10 II with kit lens, Elgato Flex Arm", (0.115, 0.10, 0.07),
     (XM - 0.44, RY - 0.38, 1.27), _aim(XM - 0.44, RY - 0.38, EAR[0], EAR[1]), col=B_)
MIC = dict(clamp=(WIN_EDGE - 0.06, RY - 0.04), elbow=(WIN_EDGE - 0.14, RY - 0.20, 1.55),
           capsule=(XM + 0.27, 1.40, 1.08))
part("mic", "Microphone on its arm", "Shure MV7+ white on a RODE PSA1+ white arm", (0.066, 0.153, 0.066),
     (MIC["capsule"][0], MIC["capsule"][1], MIC["capsule"][2] - 0.033), role="obj_mic", shape="special",
     note="email; arm reach 76 cm of 82")
part("interface", "Audio interface", "Universal Audio Apollo x4 (Gen 2, silver)", (0.233, 0.15, 0.066), (XM - 0.145, RY - 0.38, TOP),
     role="obj_studio", col=B_, note="size from retailers; big monitor knob = volume, preamp knob = pan (owner, 2026-10-23)")
part("streamdeck", "Stream Deck", "Elgato Stream Deck MK.2 white", (0.118, 0.084, 0.03), (XM + 0.245, RY - 0.42, TOP))
part("mat", "Felt desk mat", "grey felt, 80 x 30", (0.80, 0.30, 0.004), (XM, 1.47, TOP), col="#8d9096")
part("keyboard", "Keyboard", "Keychron Q1 Max, white", (0.3275, 0.145, 0.032), (XM - 0.045, 1.47, TOP),
     note="UNSURE height")
part("mouse", "Mouse", "Logitech MX Master 3S, pale grey", (0.084, 0.125, 0.051), (XM + 0.265, 1.46, TOP), col="#d5d6d8")
part("snake_plant", "Snake plant", "white pot", (0.12, 0.12, 0.45), (BACK_X1 - 0.10, RY - 0.60, TOP),   # r4: the desk's outer end
     shape="cyl", col="#3f6b3a")
# --- the return (r2, owner: "DJ controller on the desk return, PC on the floor under it")
part("dj", "DJ controller", "two-deck, Pioneer DDJ-FLX4 shape (no logos)", (0.483, 0.273, 0.059),
     (-RX + 0.60 - 0.02 - 0.273 / 2, DJ_Y, TOP), 90, role="obj_studio", col=B_,
     note="on the return, faces the chair, over the return's knee space")
part("mstand", "Laptop stand", "Rain Design mStand, silver", (0.253, 0.262, 0.15),
     (-RX + 0.03 + 0.262 / 2, DJ_Y, TOP), 90, col=G_, note="25.3 x 26.2 x 15 (Rain Design)")
part("laptop", "Laptop", "MacBook Pro 16, silver, open", (0.356, 0.248, 0.24),
     (-RX + 0.03 + 0.262 / 2, DJ_Y, TOP + 0.15), 90, col=G_, note="the DJ laptop, behind the decks", glow="#cfe0ff")
part("pc", "Training rig (PC)", "Lian Li O11 Vision white, RTX 5090 Founders Edition inside",
     PC_SIZE, PC_AT, 90, role="obj_rig",
     note="on the desk, right of the right speaker; front glass to the camera", glow="#9fd0ff")
# On a small shelf on the backlit pegboard, above the laptop
LIGHTSTICK_SHELF = dict(z=1.40, d=0.10, w=0.12, t=0.012)
part("lightstick", "K-pop lightstick", "generic, our own shape, standing in a cradle on a pegboard shelf",
     (0.07, 0.07, 0.27), (-RX + 0.08, 1.25, LIGHTSTICK_SHELF["z"]), role="obj_studio", shape="cyl", col="#e9e3f5",
     glow="#d9a0ff", note="on the pegboard, above the DJ laptop")
# --- the walls of the AI side
PEG_Y = 1.05                                    # over the DJ end of the return (was 90)
part("pegboard", "Pegboard, backlit", "IKEA SKADIS 76 x 56 white", (0.76, 0.02, 0.56), (-RX + 0.03, PEG_Y, 1.32), 90,
     shape="slab", glow="#9fc8ff")
part("headphones", "Headphones on the pegboard", "Audio-Technica ATH-M50x white", (0.19, 0.08, 0.21),
     (-RX + 0.09, PEG_Y - 0.20, 1.48), 90, col=W_)
part("neon", "Neon sign (our words)", "custom white neon, text from content", (0.70, 0.02, 0.26),
     (-RX + 0.03, PEG_Y, 1.98), 90, shape="slab", col="#ffffff", glow="#ffffff",
     note="placeholder text; read from content/")
part("nanoleaf", "Light panels", "Nanoleaf Shapes Triangles, 7 panels", (0.58, 0.01, 0.52),
     (-RX + 0.01, 1.78, 1.70), 90, shape="slab", glow="#86a8ff", note="23 x 20 cm triangles (Nanoleaf)")
LEDGE = dict(x0=XM - 0.575, x1=XM + 0.575, z=1.92, d=0.12, t=0.04)
part("ledge", "Floating ledge", "white floating shelf 115 x 12", (1.15, LEDGE["d"], LEDGE["t"]),
     (XM, RY - LEDGE["d"] / 2, LEDGE["z"]))
for i, dx in enumerate((-0.38, 0.0, 0.38)):
    part(f"frame_{i + 1}", f"Frame {i + 1}", "black frame, 30 x 40 portrait (3:4)", (0.30, 0.03, 0.40),
         (XM + dx, RY - 0.04, LEDGE["z"] + LEDGE["t"]), role="obj_frames", col="#26262a",
         note=["GitHub", "LinkedIn", "X"][i])
part("chair", "Chair", "Herman Miller Aeron size B, Mineral", (0.686, 0.686, 1.044), (XM + 0.20, 1.00, 0), 200,
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
         (RX - C.WALL_GUITARS["off_wall"], WALL_GUITARS_V2["y"][i], WG_BOTTOM), -90,
         role="obj_guitars", shape="special", col=["#141414", "#ece8dc", "#8b1e22"][i], side="music")
part("rack", "Guitar rack (3)", "floor rack, approved shape", (0.50, 0.50, 0.95), (RACK_V2["x"], RACK_V2["y"], 0),
     RACK_V2["yaw"], role="obj_guitars", shape="special", col="#232326", side="music",
     note="04 Number One (built), 05 Explorer, 06 TOD10")
part("rug", "Rug", "wool, 150 x 230", (1.50, 2.30, 0.01), (0.05, 0.15, 0), col="#6f5a4a", side="music")
part("pendant", "Ceiling light", "pendant, 40 cm shade", (0.40, 0.40, 0.15), (LIGHT_V2["x"], LIGHT_V2["y"], 2.40),
     role="obj_light", shape="cyl", col="#d9d4c8", glow="#ffb066", side="music")
part("plant", "Plant on the sill", "young monstera, terracotta pot", (0.14, 0.14, 0.38), (WINDOW_V2["x0"] + 0.30, RY - 0.12, WINDOW_V2["sill"]),
     role="obj_plant", shape="cyl", col="#4f7a46", side="music", note="grows a leaf each visit")
_ww, _wh = WINDOW_V2["x1"] - WINDOW_V2["x0"], WINDOW_V2["head"] - WINDOW_V2["sill"]
part("window", "Window", f"aluminium sliding, {cm(_ww)} x {cm(_wh)}, MS grill", (_ww, 0.23, _wh), (0, RY, WINDOW_V2["sill"]),
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
