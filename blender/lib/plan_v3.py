"""Room plan v3 (2026-10-24): the owner's photo layout (docs/moodboard/local/ai-desk-reference-1.jpg).

Approved as a quick blockout (blender/design/photo_layout_blockout.py, owner: "Approved. Turn the
photo layout into plan v3 with the checks and the sheet."). The numbers here are PROPOSED: the
sheet (blender/design/room_plan_v3_sheet.py) and the blockout (blender/design/room_plan_v3_blockout.py)
draw them; nothing in build.py reads this file yet.

What it is: the AI lab copies the photo. The desk's main run (80 deep, 185 long) stands along the
LEFT wall from the back corner forward, the screens face the room (+X). The return (60 deep) runs
along the BACK wall from the corner to 8 cm short of the window. The window (140 x 140) is on the
back wall right after the return: the intro shot looks out of it. The music side (piano, guitars,
rack, decks) is the secret on the right wall, out of the AI-lab view, revealed with About.

World metres, Blender axes (MESHES.md section 1): origin on the floor at the room's centre, back
wall (window) at +Y, left wall (AI lab, door) at -X, right wall (piano) at +X, Z up. yaw: degrees
about +Z, counter-clockwise from above; 0 = the object's front faces -Y, 90 = faces +X (into the
room from the left wall), -90 = faces -X (into the room from the right wall).

Sizes are the makers' published outside sizes (docs/moodboard/local/ai-lab/*/SOURCES.md);
UNSURE marks the ones to re-check. Plain Python, no Blender: run_checks() is the clearance check.
"""
import math

from . import constants as C
from .piano_layout import lid_profile

ROOM = C.ROOM                                    # 4.40 x 4.20 x 3.00 m, unchanged
RX, RY, H = C.RX, C.RY, C.ROOM["height"]
DOOR = C.DOOR                                    # left wall by the front corner, y -2.00 to -1.10, unchanged
SWITCH = C.SWITCH

# ---------------------------------------------------------------------------
# Window: on the back wall right after the return (the intro's window). 140 x 140, sill 95,
# head 235, aluminium sliding with an MS grill, a deep stone ledge 20 cm into the room.
# 10 cm right of the quick blockout, so the return is 102 long and holds the PC, a plant and
# the laptop without crowding.
# ---------------------------------------------------------------------------
WINDOW_V3 = dict(x0=-0.30, x1=1.10, sill=0.95, head=2.35, ledge_d=0.25, ledge_horn=0.02, ledge_t=0.03)
LEDGE_IN = WINDOW_V3["ledge_d"] - 0.05           # 20 cm into the room

# ---------------------------------------------------------------------------
# The desk: one continuous white top, 3.5 cm, at 76.5: IKEA LAGKAPTEN on ALEX with 3 cm metal risers
# (owner, 2026-10-24: "Option B: short 3 cm risers, desk at about 76.5 cm").
# ---------------------------------------------------------------------------
RISER = 0.03
TOP, TOP_T = 0.70 + RISER + 0.035, 0.035      # 0.765
ALEX = (0.36, 0.58, 0.70)                        # IKEA ALEX w, d, h (official 36 x 58 x 70)
MAIN_LEN, MAIN_D, RET_D = 1.85, 0.80, 0.60
MAIN = dict(x0=-RX, x1=-RX + MAIN_D, y0=RY - MAIN_LEN, y1=RY)                       # y 25 to 210
RET = dict(x0=-RX + MAIN_D, x1=WINDOW_V3["x0"] - 0.08, y0=RY - RET_D, y1=RY)       # x -140 to -38
RET_LEN = RET["x1"] - RET["x0"]                  # beyond the main run: 102 (182 from the left wall)
DESK_L = [(MAIN["x0"], MAIN["y0"]), (MAIN["x1"], MAIN["y0"]), (MAIN["x1"], RET["y0"]), (RET["x1"], RET["y0"]),
          (RET["x1"], RET["y1"]), (MAIN["x0"], MAIN["y1"])]                         # the top, as one outline
LED_IN = 0.05                                    # LED strip under both front edges, 5 cm in
# Three ALEX units, flush (1 cm) with the front edges, as in the photo: (centre x, centre y, yaw)
DRAWERS = [
    (MAIN["x1"] - 0.01 - ALEX[1] / 2, MAIN["y0"] + 0.01 + ALEX[0] / 2, 90),   # 1: main run, outer end, faces the room
    (RET["x0"] + 0.01 + ALEX[0] / 2, RY - 0.01 - ALEX[1] / 2, 0),             # 2: return, by the corner
    (RET["x1"] - 0.01 - ALEX[0] / 2, RY - 0.01 - ALEX[1] / 2, 0),             # 3: return, far end by the window
]

# ---------------------------------------------------------------------------
# The main run, against the left wall: the screen stack, the speakers, the key lights
# ---------------------------------------------------------------------------
KL_POLE = [(MAIN["x1"] - 0.06, MAIN["y0"] + 0.07), (MAIN["x1"] - 0.06, RET["y0"] + 0.18)]   # the two ends
YM = round((KL_POLE[0][1] + KL_POLE[1][1]) / 2, 3)   # the stack's centre line, centred between the poles: 1.00
SEAT = (MAIN["x1"] + 0.45, YM)                   # the Aeron's post, parked at the main run
EAR_SEATED = (SEAT[0] - 0.06, YM, 1.18)          # seat 46 + seated ear about 72
EAR_STANDING = 1.55                              # standing ear of a 170 cm person
POLE = (-RX + 0.04, YM)                          # the dual monitor pole, clamped at the back edge
UW = dict(w=0.8136, d=0.128, h=0.364, z=0.89)    # Samsung G8 34: 813.6 wide, 128.1 deep (no stand); h UNSURE
UW["x"] = POLE[0] + 0.02 + 0.02 + UW["d"] / 2    # 2 cm behind it for the VESA arm
SD = dict(w=0.623, d=0.031, h=0.362)             # Apple Studio Display 27, VESA (Apple: 362 x 623 x 31)
SD["z"] = UW["z"] + UW["h"] + 0.04
SD["x"] = POLE[0] + 0.04 + SD["d"] / 2
SD_GLASS = (0.597, 0.336)                        # 27 in 16:9 active area
POSTS = dict(w=0.538, h=SD_GLASS[1])             # monitor_screen 16:10, 53.8 x 33.6, centred in the glass
UW_ACTIVE = (0.797, 0.334)                       # rig_screen 21:9

# ADAM A7V white, raised beside the TOP screen on desk poles, as in the photo. The cabinets line
# up with the Studio Display (centre on centre), which puts the tweeters at standing ear level:
# the photo's look, and the site's camera stands. Toed in towards the seat.
A7V = (0.200, 0.280, 0.337)                      # ADAM official W x D x H
TWEETER_UP = 0.265                               # UNSURE: tweeter centre above the cabinet's base
SPK_Z = SD["z"] + SD["h"] / 2 - A7V[2] / 2       # cabinet base
SPK_X = -RX + 0.04 + A7V[1] / 2                  # back 4 cm off the wall (front ports)
SPK_PLATE = 0.02                                 # the pole's top plate under each cabinet


def _aim(x, y, tx, ty):
    """yaw that turns an object's front (-Y) from (x, y) towards (tx, ty)."""
    return math.degrees(math.atan2(tx - x, -(ty - y)))


def rot(x, y, yaw):
    a = math.radians(yaw)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def rect_w(cx, cy, w, d, yaw):
    return [(cx + dx, cy + dy) for dx, dy in (rot(x, y, yaw) for x, y in
                                              ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)))]


def circ(cx, cy, r, n=20):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


# clash test for convex outlines (separating axis) and the distance between them (from room_plan_sheet.py)
def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _overlap(A, B):
    for poly in (A, B):
        for i in range(len(poly)):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % len(poly)]
            nx, ny = y0 - y1, x1 - x0
            pa = [nx * x + ny * y for x, y in A]
            pb = [nx * x + ny * y for x, y in B]
            if max(pa) <= min(pb) or max(pb) <= min(pa):
                return False
    return True


def gap(A, B):
    """Clear distance between two convex outlines; -1 when they overlap."""
    if _overlap(A, B):
        return -1.0
    return min(_seg_dist(p, Q[i], Q[(i + 1) % len(Q)]) for P_, Q in ((A, B), (B, A)) for p in P_ for i in range(len(Q)))


def _spk_dy():
    """Smallest offset from YM that keeps a toed-in cabinet 3 cm off the Studio Display's edge and
    its pole 3 cm off the ultrawide's edge."""
    dy = SD["w"] / 2 + 0.03
    sd = rect_w(SD["x"], YM, SD["w"], SD["d"], 90)
    uw = rect_w(UW["x"], YM, UW["w"], UW["d"], 90)
    while True:
        y = YM - dy
        cab = rect_w(SPK_X, y, A7V[0], A7V[1], _aim(SPK_X, y, *EAR_SEATED[:2]))
        if gap(cab, sd) >= 0.03 and gap(circ(SPK_X, y, 0.0175), uw) >= 0.03:
            return round(dy + 0.0049, 2)
        dy += 0.005


SPK_DY = _spk_dy()
SPEAKERS = [dict(x=SPK_X, y=YM + s * SPK_DY, z=SPK_Z, yaw=_aim(SPK_X, YM + s * SPK_DY, *EAR_SEATED[:2])) for s in (-1, 1)]
TWEETER_Z = SPK_Z + TWEETER_UP

# Elgato Key Light on the Master Mount L (55 to 125 cm above the desk); the panel 4 cm in front
# of the pole, aimed at the seated face from the side (the aim point is just behind the head, so
# the panels face the hero camera as in the photo).
KL_PANEL = (0.35, 0.035, 0.25)
KL_Z = 1.60                                      # panel bottom; centre 172.5, pole height 99 above the top
KL_POLE_TOP = KL_Z + KL_PANEL[2] / 2
# Sony ZV-E10 II with the kit lens on an Elgato Flex Arm L (reach about 45) off the outer pole
CAM_AT = (MAIN["x1"] - 0.30, YM - 0.38, 1.27)    # bottom centre
CAM_ARM_FROM = (KL_POLE[0][0], KL_POLE[0][1], 1.42)
# Shure MV7+ white on a RODE PSA1+ white (reach 94 cm horizontal): clamped at the outer end's back
# edge, parked left of the keyboard, the elbow kept under the speaker's plate.
MIC = dict(clamp=(-RX + 0.05, MAIN["y0"] + 0.08), riser=0.20, elbow=(-RX + 0.30, MAIN["y0"] + 0.19, 1.16),
           capsule=(MAIN["x1"] - 0.16, YM - 0.36, 1.06))
PSA1_REACH = 0.94
# Floating shelf above the run: three frames, trailing plants at its two ends
SHELF = dict(x0=-RX, x1=-RX + 0.25, y0=0.15, y1=1.95, z=1.92, t=0.04)
VINE_LEN = 0.57                                  # the trailing plants hang to about 131

# ---------------------------------------------------------------------------
# The return, against the back wall: the PC in the inner corner (front glass to the room, side
# glass towards the window and the camera), a small plant, the MacBook on the mStand at the end
# ---------------------------------------------------------------------------
PC_SIZE = (0.304, 0.480, 0.4645)                 # Lian Li O11 Vision W x D x H (official)
PC_AT = (RET["x0"] + 0.02 + PC_SIZE[0] / 2, RY - 0.04 - PC_SIZE[1] / 2, TOP)
LAPTOP_AT = (RET["x1"] - 0.24, RY - 0.29)
LAPTOP_YAW = _aim(*LAPTOP_AT, *SEAT)             # turned to the chair, as in the photo
PEG = dict(w=0.76, h=0.56, x1=WINDOW_V3["x0"] - 0.06, z=1.28, off=0.04)   # SKADIS, 4 cm off the wall, backlit
PEG["x"] = PEG["x1"] - PEG["w"] / 2

# ---------------------------------------------------------------------------
# The music side (the secret): piano on the right wall, the three wall guitars over its lid,
# the rack (04 to 06) in the back-right corner, the decks on their own stand by the front.
# ---------------------------------------------------------------------------
PIANO_V3 = dict(x=RX - 0.05, y=0.25, yaw=-90, bench_in=0.22)   # case back 5 cm off the wall
PIANO_LID_MAX_DEG = 60                           # the site's code stops the top lid here (decision 2026-10-24)
WG_LEN = (1.07, 0.977, 1.10)                     # Lucille, Woodstock Strat, double-neck (as plan_v2)
WG_WID = (0.41, 0.323, 0.43)
WG_GAP = 0.12
WG_SPAN = sum(WG_WID) + 2 * WG_GAP
WG_BACK = PIANO_V3["y"] + WG_SPAN / 2            # the group centred over the piano
WG_BODY_BAND = (C.WALL_GUITARS["off_wall"] - 0.025, C.WALL_GUITARS["off_wall"] + 0.045)


def lid_reach(deg_max, band=WG_BODY_BAND, steps=15):
    """Highest z the top lid reaches opening from 0 to deg_max over the band (metres off the right
    wall), from lid_profile and the piano's place (as plan_v2)."""
    best = 0.0
    for i in range(steps):
        u = (RX - (band[0] + (band[1] - band[0]) * i / (steps - 1))) - PIANO_V3["x"]
        for k in range(int(deg_max * 4) + 1):
            pts, _ = lid_profile(k / 4)
            for (y0, z0), (y1, z1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 - u) * (y1 - u) <= 0 and y0 != y1:
                    best = max(best, z0 + (z1 - z0) * (u - y0) / (y1 - y0))
    return best


LID_REACH = lid_reach(PIANO_LID_MAX_DEG)
WG_BOTTOM = math.ceil((LID_REACH + 0.05) * 100) / 100
_ys, _y = [], WG_BACK
for _w in WG_WID:
    _ys.append(_y - _w / 2)
    _y -= _w + WG_GAP
WALL_GUITARS_V3 = dict(C.WALL_GUITARS, y=tuple(round(v, 4) for v in _ys), length=WG_LEN, width=WG_WID,
                       bottom=WG_BOTTOM, hooks=(1, 1, 2), hook_from_top=(0.18, 0.18, 0.18))
# Floor rack (approved shape), in the back-right corner between the window's ledge and the piano.
# Its guitars face the About camera, 30 deg off, so all three bodies show.
RACK_V3 = dict(C.LAYOUT["rack"], x=1.68, y=1.72)
RACK_EXT = (-0.32, 0.18, -0.25, 0.25)            # rack plus leaning guitars, in its own frame
# DJ stand: slim, 70 x 40, top at 90 (standing DJ), against the right wall towards the front;
# the decks on it face the room, the lightstick stands in a cradle at its front end.
DJ_STAND = dict(x=RX - 0.03 - 0.20, y=-1.22, yaw=-90, w=0.70, d=0.40, top=0.90, t=0.025, colour="#1d1d1f")
DJ_ZONE_D = 0.45                                 # where the DJ stands, in front of the stand
# Rug and pendant: the open middle between the lab and the piano
RUG = dict(x=0.20, y=-0.30, w=1.60, d=2.30)
LIGHT_V3 = dict(C.LIGHT, x=0.20, y=-0.30)

# ---------------------------------------------------------------------------
# Cameras (Blender: pos, target, vertical fov in degrees)
# ---------------------------------------------------------------------------
# INTRO: inside the room, at the window, looking out at the sky and the city. A click pulls back
# into the room and turns left to HERO_V3.
INTRO = dict(pos=(0.40, 1.10, 1.55), target=(0.40, 6.0, 1.78), vfov=50)
# HERO_V3: the AI lab as in the photo: standing in the room, looking into the back-left corner.
HERO_V3 = dict(pos=(1.10, -0.80, 1.85), target=(-1.75, 1.20, 0.78), vfov=54, portrait_vfov=66)
# ABOUT: the camera turns right to the music side: piano and guitars, rack, decks.
ABOUT = dict(pos=(-0.75, -1.25, 1.55), target=(1.90, 0.20, 1.32), vfov=50)
# Phone: the hero's place, portrait 390 x 844, aimed at the screen stack.
PHONE_V3 = dict(pos=HERO_V3["pos"], target=(-1.85, YM + 0.15, 0.98), vfov=60)

# ---------------------------------------------------------------------------
# Every component. at = (x, y, z) bottom centre; size = (w, d, h); yaw as above.
# role: the obj_* root (interactive) or "set". shape: box | cyl (w = diameter) | slab (on a wall)
# | special (the blockout and the sheet draw it themselves).
# ---------------------------------------------------------------------------
W_, B_, G_ = "#f2f2ef", "#1b1b1d", "#c9ccd1"
COMPONENTS = []


def cm(m):
    return f"{m * 100:.0f}"


def part(key, label, model, size, at, yaw=0, role="set", shape="box", col=W_, side="ai", note="", glow=None):
    COMPONENTS.append(dict(key=key, label=label, model=model, size=size, at=at, yaw=yaw, role=role,
                           shape=shape, col=col, side=side, note=note, glow=glow))


# --- the desk
part("desk", "L desk", "IKEA LAGKAPTEN tops on ALEX, white, 3.5 cm, no pucks", (MAIN_D, MAIN_LEN, TOP), (0, 0, 0),
     shape="special", note=f"main run {cm(MAIN_LEN)} x 80 on the left wall, return {cm(RET_LEN)} x 60 on the back wall")
for i, (x, y, yaw) in enumerate(DRAWERS):
    part(f"alex_{i + 1}", f"Drawer unit {i + 1}", "IKEA ALEX, white, 5 drawers", ALEX, (x, y, 0), yaw)
part("led", "LED strip under the desk", "Philips Hue Play gradient strip", (0, 0, 0), (0, 0, TOP - TOP_T),
     shape="special", glow="#7fb6ff", note="under both front edges")
# --- the main run
part("pole", "Monitor pole, dual stack", "clamp pole, white", (0.04, 0.04, 1.60 - TOP), (POLE[0], POLE[1], TOP), shape="cyl",
     note="ends under the light bar's clamp")
part("ultrawide", "Main screen, 34 in curved", "Samsung Odyssey OLED G8 34 (21:9, 1800R), silver",
     (UW["w"], UW["d"], UW["h"]), (UW["x"], YM, UW["z"]), 90, role="obj_rig", col=B_,
     note="the training dashboard (rig_screen 79.7 x 33.4)", glow="#3a7bd5")
part("studio_display", "Top screen, 27 in", "Apple Studio Display 27 (16:9), VESA, on the same pole",
     (SD["w"], SD["d"], SD["h"]), (SD["x"], YM, SD["z"]), 90, role="obj_monitor", col=G_,
     note="the posts (monitor_screen 16:10, 53.8 x 33.6, inside the 16:9 glass)", glow="#8fb8ff")
part("screenbar", "Monitor light bar", "BenQ ScreenBar Halo", (0.50, 0.10, 0.03),
     (SD["x"] + 0.02, YM, SD["z"] + SD["h"]), 90, col=B_)
for i, s in enumerate(SPEAKERS):
    part(f"spk_pole_{i + 1}", f"Speaker pole {'LR'[i]}", "desk pole with a top plate, white", (0.035, 0.035, s["z"] - SPK_PLATE - TOP),
         (s["x"], s["y"], TOP), shape="cyl")
    part(f"spk_plate_{i + 1}", f"Speaker plate {'LR'[i]}", "pole plate", (0.16, 0.22, SPK_PLATE), (s["x"], s["y"], s["z"] - SPK_PLATE),
         s["yaw"])
    part(f"a7v_{i + 1}", f"Studio monitor {'LR'[i]}", "ADAM A7V, Arctic White", A7V, (s["x"], s["y"], s["z"]), s["yaw"],
         role="obj_studio", note=f"tweeter at {cm(TWEETER_Z)}, toed in {abs(s['yaw'] - 90):.0f} deg")
KL_AIM = (SEAT[0] + 0.35, YM)
for i, (x, y) in enumerate(KL_POLE):
    yaw = _aim(x, y, *KL_AIM)
    part(f"keylight_pole_{i + 1}", f"Key light pole {i + 1}", "Elgato Master Mount L", (0.025, 0.025, KL_POLE_TOP - TOP),
         (x, y, TOP), shape="cyl", col=B_)
    fx, fy = rot(0, -0.04, yaw)
    part(f"keylight_{i + 1}", f"Key light {i + 1}", "Elgato Key Light (Mk.2)", KL_PANEL, (x + fx, y + fy, KL_Z), yaw,
         col=B_, note="panel 35 x 25 x 3.5 (Elgato)", glow="#ffffff")
part("camera", "Camera on a flex arm", "Sony ZV-E10 II, 16-50 kit lens, on an Elgato Flex Arm L", (0.115, 0.10, 0.07),
     CAM_AT, _aim(CAM_AT[0], CAM_AT[1], *EAR_SEATED[:2]), col=B_, note="body 114.8 x 67.5 x 54.2 (Sony), with the lens")
part("mic", "Microphone on its arm", "Shure MV7+ white on a RODE PSA1+ white", (0.09, 0.17, 0.09),
     (MIC["capsule"][0], MIC["capsule"][1], MIC["capsule"][2] - 0.045), _aim(*MIC["capsule"][:2], *EAR_SEATED[:2]),
     role="obj_mic", shape="special", note="parked left of the keyboard; email")
part("interface", "Audio interface", "Universal Audio Apollo x4 Gen 2, silver", (0.233, 0.15, 0.066),
     (-RX + 0.185, YM - 0.10, TOP), 90, role="obj_studio", col=G_, note="233 x 149 x 66 (retailers)")
part("streamdeck", "Stream Deck", "Elgato Stream Deck MK.2 white, on its stand", (0.118, 0.084, 0.075),
     (-RX + 0.28, YM + 0.17, TOP), 90, note="118 x 84 x 25 flat (Elgato); on its stand UNSURE")
part("mat", "Felt desk mat", "grey felt, 80 x 30", (0.80, 0.30, 0.004), (MAIN["x1"] - 0.25, YM, TOP), 90, col="#8d9096")
part("keyboard", "Keyboard", "Keychron Q1 Max, white", (0.3275, 0.145, 0.032), (MAIN["x1"] - 0.22, YM - 0.05, TOP + 0.004), 90)
part("mouse", "Mouse", "Logitech MX Master 3S, pale grey", (0.0843, 0.1249, 0.051), (MAIN["x1"] - 0.22, YM + 0.25, TOP + 0.004), 90,
     col="#d5d6d8")
part("snake_plant", "Snake plant", "white ceramic pot, about 45", (0.12, 0.12, 0.45), (MAIN["x1"] - 0.24, MAIN["y0"] + 0.12, TOP),
     shape="cyl", col="#3f6b3a", note="the outer end, under the camera, beside the key light")
part("shelf", "Floating shelf", "white floating shelf 180 x 25", (SHELF["y1"] - SHELF["y0"], SHELF["x1"] - SHELF["x0"], SHELF["t"]),
     ((SHELF["x0"] + SHELF["x1"]) / 2, (SHELF["y0"] + SHELF["y1"]) / 2, SHELF["z"] - SHELF["t"]), 90)
for i, dy in enumerate((-0.38, 0.0, 0.38)):
    part(f"frame_{i + 1}", f"Frame {i + 1}", "black frame, 30 x 40 portrait", (0.30, 0.03, 0.40), (-RX + 0.035, YM + dy, SHELF["z"]), 90,
         role="obj_frames", col="#26262a", note=["GitHub", "LinkedIn", "X"][i])
for i, y in enumerate((SHELF["y0"] + 0.07, SHELF["y1"] - 0.07)):
    part(f"vine_pot_{i + 1}", f"Trailing plant {i + 1}", "pothos in a white pot", (0.12, 0.12, 0.11), (-RX + 0.11, y, SHELF["z"]),
         shape="cyl")
    part(f"vine_{i + 1}", f"Trailing vines {i + 1}", "pothos vines", (0.10, 0.10, VINE_LEN), (-RX + 0.11, y, SHELF["z"] - SHELF["t"] - VINE_LEN),
         shape="cyl", col="#3f6b3a")
part("chair", "Chair", "Herman Miller Aeron, size B, Mineral", (0.686, 0.686, 1.044), (SEAT[0], SEAT[1], 0), -90,
     shape="special", col="#c9ccd0", note="base about 69 across; swing radius 40 (UNSURE)")
# --- the return
part("pc", "Training rig (PC)", "Lian Li O11 Vision white, RTX 5090 Founders Edition inside", PC_SIZE, PC_AT, 0,
     role="obj_rig", note="front glass to the room, side glass to the window and the camera", glow="#9fd0ff")
part("desk_plant", "Small plant", "small fern in a white pot", (0.10, 0.10, 0.20), (PC_AT[0] + 0.25, RET["y0"] + 0.15, TOP),
     shape="cyl", col="#4f7a46")
part("mstand", "Laptop stand", "Rain Design mStand, silver", (0.253, 0.262, 0.15), (*LAPTOP_AT, TOP), LAPTOP_YAW, col=G_)
part("laptop", "Laptop", "MacBook Pro 16, silver, open", (0.356, 0.248, 0.24), (*LAPTOP_AT, TOP + 0.15), LAPTOP_YAW, col=G_,
     glow="#cfe0ff", note="355.7 x 248.1 (Apple)")
# --- the back wall above the return
part("pegboard", "Pegboard, backlit", "IKEA SKADIS 76 x 56, white", (PEG["w"], 0.02, PEG["h"]),
     (PEG["x"], RY - PEG["off"] + 0.01, PEG["z"]), 0, shape="slab", glow="#9fc8ff", note="LED behind it, 4 cm off the wall")
part("headphones", "Headphones on the pegboard", "Audio-Technica ATH-M50x, white", (0.19, 0.08, 0.21),
     (PEG["x"] + 0.20, RY - PEG["off"] - 0.04, PEG["z"] + 0.22), 0)
part("neon", "Neon sign (our words)", "custom white LED neon on clear acrylic", (0.70, 0.02, 0.26),
     (PEG["x"], RY - 0.01, PEG["z"] + PEG["h"] + 0.11), 0, shape="slab", col="#ffffff", glow="#ffffff",
     note="text read from content/")
part("nanoleaf", "Light panels", "Nanoleaf Shapes Triangles, 7 panels", (0.58, 0.01, 0.52),
     (PEG["x"] - PEG["w"] / 2 - 0.05 - 0.29, RY - 0.005, 1.30), 0, shape="slab", glow="#86a8ff",
     note="23 x 20 triangles (Nanoleaf), near the corner")
# --- the window and the sill
_ww, _wh = WINDOW_V3["x1"] - WINDOW_V3["x0"], WINDOW_V3["head"] - WINDOW_V3["sill"]
part("window", "Window", f"aluminium sliding, {cm(_ww)} x {cm(_wh)}, MS grill, stone ledge",
     (_ww, 0.23, _wh), ((WINDOW_V3["x0"] + WINDOW_V3["x1"]) / 2, RY, WINDOW_V3["sill"]),
     role="obj_window", shape="special", side="window", note="the intro: sky and city; Pune's time and weather")
part("plant", "Plant on the sill", "young monstera, terracotta pot", (0.14, 0.14, 0.40),
     (WINDOW_V3["x1"] - 0.28, RY - 0.11, WINDOW_V3["sill"]), role="obj_plant", shape="cyl", col="#4f7a46", side="window",
     note="in the intro's frame; a leaf per visit")
# --- the music side
part("piano", "Upright piano", "our approved black upright (constants.PIANO)", (1.53, 0.608, 1.217),
     (PIANO_V3["x"] - 0.30, PIANO_V3["y"], 0), -90, role="obj_piano", shape="special", col="#0a0a0a", side="music")
part("bench", "Piano bench", "constants.BENCH", (C.BENCH["w"], C.BENCH["d"], C.BENCH["h"]),
     (PIANO_V3["x"] + C.BENCH["cy"] + PIANO_V3["bench_in"], PIANO_V3["y"], 0), -90, col="#0a0a0a", side="music")
for i in range(3):
    part(f"guitar_0{i + 1}", ["Lucille", "Woodstock Strat", "Double-neck"][i],
         ["B.B. King's ES-355 shape, black", "Hendrix's white Strat (built)", "Jimmy Page's cherry double-neck"][i],
         (WG_WID[i], 0.07, WG_LEN[i]), (RX - C.WALL_GUITARS["off_wall"] + 0.01, WALL_GUITARS_V3["y"][i], WG_BOTTOM), -90,
         role="obj_guitars", shape="special", col=["#141414", "#ece8dc", "#8b1e22"][i], side="music")
part("rack", "Guitar rack (3)", "floor rack, approved shape", (0.50, 0.50, 1.06), (RACK_V3["x"], RACK_V3["y"], 0), 0,
     role="obj_guitars", shape="special", col="#232326", side="music", note="04 Number One (built), 05 Explorer, 06 TOD10")
part("dj_stand", "DJ stand", "slim steel stand, black, 70 x 40, top at 90", (DJ_STAND["w"], DJ_STAND["d"], DJ_STAND["top"]),
     (DJ_STAND["x"], DJ_STAND["y"], 0), DJ_STAND["yaw"], col=DJ_STAND["colour"], side="music")
_dx, _dy = rot(-0.05, 0.0, DJ_STAND["yaw"])
part("dj", "DJ controller", "two-deck, Pioneer DDJ-FLX4 shape (no logos)", (0.482, 0.273, 0.059),
     (DJ_STAND["x"] + _dx, DJ_STAND["y"] + _dy, DJ_STAND["top"]), DJ_STAND["yaw"], role="obj_studio", col=B_, side="music",
     note="482 x 273 x 59 (Pioneer)")
_dx, _dy = rot(0.27, 0.0, DJ_STAND["yaw"])
part("lightstick", "K-pop lightstick", "generic, our own shape, in a cradle", (0.07, 0.07, 0.27),
     (DJ_STAND["x"] + _dx, DJ_STAND["y"] + _dy, DJ_STAND["top"]), role="obj_studio", shape="cyl", col="#e9e3f5",
     glow="#d9a0ff", side="music", note="at the decks' front end")
part("rug", "Rug", "wool, 160 x 230", (RUG["w"], RUG["d"], 0.01), (RUG["x"], RUG["y"], 0), col="#6f5a4a", side="room")
part("pendant", "Ceiling light", "pendant, 40 cm shade, bottom at 240", (0.40, 0.40, 0.15), (LIGHT_V3["x"], LIGHT_V3["y"], 2.40),
     role="obj_light", shape="cyl", col="#d9d4c8", glow="#ffb066", side="room")

CP = {c["key"]: c for c in COMPONENTS}

# Interactive objects (version 1 limit is 10): unchanged ten, new places
OBJECTS_V3 = [
    ("obj_monitor", "Posts screen (top, 27 in)", "glide in, posts list, keyboard works"),
    ("obj_rig", "Training rig: PC on the return, 34 in screen", "fans pulse, the dashboard lists projects as runs"),
    ("obj_mic", "Mic on its arm", "email; later the talk-to-me agent"),
    ("obj_frames", "Three frames on the shelf", "GitHub, LinkedIn, X"),
    ("obj_studio", "Studio: speakers, Apollo; decks, lightstick", "volume and pan in the lab; tracks, loops, K-pop by the piano"),
    ("obj_piano", "Upright piano", "88 keys, both lids, About on the music rest"),
    ("obj_guitars", "Guitars: wall 01 to 03, rack 04 to 06", "lift, era card, lick"),
    ("obj_light", "Ceiling light", "room light on and off"),
    ("obj_window", "Window (the intro)", "sky and city; live Pune sky"),
    ("obj_plant", "Plant on the sill", "water it, a leaf per visit"),
]


# ---------------------------------------------------------------------------
# Footprints (plan outlines) and height ranges for the checks and the sheet
# ---------------------------------------------------------------------------
PN, BN = C.PIANO, C.BENCH


def piano_local(x, y):
    dx, dy = rot(x, y, PIANO_V3["yaw"])
    return PIANO_V3["x"] + dx, PIANO_V3["y"] + dy


PIANO_FOOT = [piano_local(x, y) for x, y in ((-PN["width"] / 2, PN["toe_front_y"]), (PN["width"] / 2, PN["toe_front_y"]),
                                             (PN["width"] / 2, PN["lid_over_back"]), (-PN["width"] / 2, PN["lid_over_back"]))]


def bench_foot(played=False):
    cy = BN["cy"] + (0 if played else PIANO_V3["bench_in"])
    return [piano_local(x, y) for x, y in ((-BN["w"] / 2, cy - BN["d"] / 2), (BN["w"] / 2, cy - BN["d"] / 2),
                                           (BN["w"] / 2, cy + BN["d"] / 2), (-BN["w"] / 2, cy + BN["d"] / 2))]


def _rack_yaw():
    """The rack's guitars face along its local Y (side by side, like books); turn local +Y 30 deg
    off the About camera, so all three bodies show."""
    tx, ty = ABOUT["pos"][0] - RACK_V3["x"], ABOUT["pos"][1] - RACK_V3["y"]
    face = math.degrees(math.atan2(-tx, ty))      # yaw whose local -Y points at the camera: (sin a, -cos a)
    return round(face - 30)


RACK_V3["yaw"] = _rack_yaw()
CP["rack"]["yaw"] = RACK_V3["yaw"]
RACK_FOOT = [(RACK_V3["x"] + dx, RACK_V3["y"] + dy) for dx, dy in (rot(x, y, RACK_V3["yaw"]) for x, y in (
    (RACK_EXT[0], RACK_EXT[2]), (RACK_EXT[1], RACK_EXT[2]), (RACK_EXT[1], RACK_EXT[3]), (RACK_EXT[0], RACK_EXT[3])))]
DJ_ZONE = rect_w(DJ_STAND["x"] - DJ_STAND["d"] / 2 - DJ_ZONE_D / 2, DJ_STAND["y"], DJ_ZONE_D, DJ_STAND["w"], 0)
SWING_R = 0.40                                   # an Aeron B turning on its post: back and arms (UNSURE)
CHAIR_BASE_R = 0.343
CHAIR_OUT = (SEAT[0] + 0.35, SEAT[1])            # pulled out to stand up
DOOR_LEAF = DOOR["y1"] - DOOR["y0"] - 0.05
DOOR_SWING = [(-RX, DOOR["y0"])] + [(-RX + DOOR_LEAF * math.sin(math.radians(a)), DOOR["y0"] + DOOR_LEAF * math.cos(math.radians(a)))
                                    for a in range(0, 91, 10)]
WIN_ZONE = [(WINDOW_V3["x0"] - WINDOW_V3["ledge_horn"], RY - LEDGE_IN), (WINDOW_V3["x1"] + WINDOW_V3["ledge_horn"], RY - LEDGE_IN),
            (WINDOW_V3["x1"] + WINDOW_V3["ledge_horn"], RY), (WINDOW_V3["x0"] - WINDOW_V3["ledge_horn"], RY)]
WIN_Z = (WINDOW_V3["sill"] - WINDOW_V3["ledge_t"], WINDOW_V3["head"])


def foot(c):
    k = c["key"]
    w, d, h = c["size"]
    x, y, _ = c["at"]
    if k == "piano":
        return PIANO_FOOT
    if k == "bench":
        return bench_foot()
    if k == "rack":
        return RACK_FOOT
    if k == "chair":
        return circ(x, y, CHAIR_BASE_R)
    if k == "desk":
        return DESK_L
    if k == "window":
        return WIN_ZONE
    if c["shape"] == "cyl":
        return circ(x, y, w / 2, 16)
    return rect_w(x, y, w, d, c["yaw"])


def zrange(c):
    k = c["key"]
    if k == "desk":
        return (TOP - TOP_T, TOP)
    if k == "window":
        return WIN_Z
    if k == "mic":
        return (MIC["capsule"][2] - 0.045, MIC["capsule"][2] + 0.045)
    return (c["at"][2], c["at"][2] + c["size"][2])


# pairs that touch by design (mounted on each other), checked elsewhere or not at all
ALLOWED = {frozenset(p) for p in (("keylight_pole_1", "keylight_1"), ("keylight_pole_2", "keylight_2"),
                                  ("window", "plant"), ("pole", "studio_display"), ("pole", "ultrawide"),
                                  ("pegboard", "headphones"))}
SKIP = {"rug", "led", "desk"}                    # the desk is checked as the top's outline, below


# ---------------------------------------------------------------------------
# Checks: (name, value, need, ok). Value and need in metres; a CLASH fails the plan.
# ---------------------------------------------------------------------------
def pairs():
    """Every pair of components whose heights overlap: their clear distance in plan."""
    out = []
    cs = [c for c in COMPONENTS if c["key"] not in SKIP]
    for i, a in enumerate(cs):
        za = zrange(a)
        for b in cs[i + 1:]:
            if frozenset((a["key"], b["key"])) in ALLOWED:
                continue
            zb = zrange(b)
            if za[0] >= zb[1] - 1e-6 or zb[0] >= za[1] - 1e-6:
                continue
            out.append((gap(foot(a), foot(b)), a["key"], b["key"]))
    # the desk top (70 to 73.5) against everything that crosses that height and is not under it
    for c in cs:
        z = zrange(c)
        if z[0] < TOP - 1e-6 and z[1] > TOP - TOP_T + 1e-6 and not c["key"].startswith("alex"):
            out.append((gap(foot(c), MAIN_POLY), "desk (main run)", c["key"]))
            out.append((gap(foot(c), RET_POLY), "desk (return)", c["key"]))
    return sorted(out)


MAIN_POLY = [(MAIN["x0"], MAIN["y0"]), (MAIN["x1"], MAIN["y0"]), (MAIN["x1"], MAIN["y1"]), (MAIN["x0"], MAIN["y1"])]
RET_POLY = [(RET["x0"], RET["y0"]), (RET["x1"], RET["y0"]), (RET["x1"], RET["y1"]), (RET["x0"], RET["y1"])]


def wall_gap(c):
    ps = foot(c)
    return min(min(x + RX, RX - x, y + RY, RY - y) for x, y in ps)


def _pt_box_dist(p, c):
    """3D distance from a point to a component's box (yawed)."""
    x, y, z = c["at"]
    w, d, h = c["size"]
    lx, ly = rot(p[0] - x, p[1] - y, -c["yaw"])
    dx = max(abs(lx) - w / 2, 0)
    dy = max(abs(ly) - d / 2, 0)
    dz = max(z - p[2], p[2] - (z + h), 0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _seg_pts(a, b, n=24):
    return [tuple(a[k] + (b[k] - a[k]) * i / n for k in range(3)) for i in range(n + 1)]


def mic_arm():
    m = MIC
    c0 = (*m["clamp"], TOP)
    c1 = (*m["clamp"], TOP + m["riser"])
    cap = m["capsule"]
    hang = (cap[0], cap[1], cap[2] + 0.12)
    return [c0, c1, m["elbow"], hang, cap]


class Cam:
    """Pinhole camera (frustum only, no occlusion), as room_plan_sheet.Cam."""
    def __init__(self, pos, target, vfov, aspect):
        self.c = pos
        dx, dy, dz = (target[i] - pos[i] for i in range(3))
        self.yaw = math.atan2(dx, dy)
        self.pitch = math.atan2(dz, math.hypot(dx, dy))
        cy, sy, cp, sp = math.cos(self.yaw), math.sin(self.yaw), math.cos(self.pitch), math.sin(self.pitch)
        self.f = (sy * cp, cy * cp, sp)
        self.r = (cy, -sy, 0.0)
        f, r = self.f, self.r
        self.u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
        self.tv = math.tan(math.radians(vfov) / 2)
        self.th = self.tv * aspect
        self.vfov, self.aspect = vfov, aspect
        self.hfov = 2 * math.degrees(math.atan(self.th))

    def cam(self, p):
        d = [p[i] - self.c[i] for i in range(3)]
        return (sum(d[i] * self.r[i] for i in range(3)), sum(d[i] * self.u[i] for i in range(3)),
                sum(d[i] * self.f[i] for i in range(3)))

    def ndc(self, q):
        return q[0] / q[2] / self.th, q[1] / q[2] / self.tv

    def visible(self, p):
        q = self.cam(p)
        if q[2] <= 0.05:
            return False
        a, b = self.ndc(q)
        return abs(a) <= 1 and abs(b) <= 1


def cams():
    h = HERO_V3
    return dict(hero=Cam(h["pos"], h["target"], h["vfov"], 16 / 9),
                portrait=Cam(h["pos"], h["target"], h["portrait_vfov"], 4 / 5),
                phone=Cam(PHONE_V3["pos"], PHONE_V3["target"], PHONE_V3["vfov"], 390 / 844),
                intro=Cam(INTRO["pos"], INTRO["target"], INTRO["vfov"], 16 / 9),
                about=Cam(ABOUT["pos"], ABOUT["target"], ABOUT["vfov"], 16 / 9))


def pts3(c):
    """Sample points on a component (its box corners and mid-height), for the frustum share."""
    z0, z1 = zrange(c)
    if c["key"].startswith("guitar_0"):
        x, y, _ = c["at"]
        return [(x, y + s * c["size"][0] / 2, z0 + t * (z1 - z0)) for s in (-1, 0, 1) for t in (0, 0.5, 1)]
    if c["key"] == "window":
        return [(x, RY, z) for x in (WINDOW_V3["x0"], (WINDOW_V3["x0"] + WINDOW_V3["x1"]) / 2, WINDOW_V3["x1"])
                for z in (WINDOW_V3["sill"], WINDOW_V3["head"])]
    return [(px, py, z) for px, py in foot(c) for z in (z0, (z0 + z1) / 2, z1)]


def share(cam, keys):
    ps = [p for k in keys for p in pts3(CP[k])]
    return sum(1 for p in ps if cam.visible(p)) / len(ps)


MUSIC_KEYS = ["piano", "bench", "guitar_01", "guitar_02", "guitar_03", "rack", "dj_stand", "dj", "lightstick"]
LAB_KEYS = ["ultrawide", "studio_display", "a7v_1", "a7v_2", "keylight_1", "keylight_2", "pc", "laptop", "pegboard",
            "neon", "nanoleaf", "frame_1", "frame_2", "frame_3", "mic", "chair"]


def run_checks():
    ch = []

    def chk(name, g, need):
        ch.append((name, g, need, g >= need - 1e-9))

    cs = [c for c in COMPONENTS if c["key"] not in SKIP]
    # 1. walls
    worst = min(((wall_gap(c), c["key"]) for c in cs if c["key"] != "window"))
    chk(f"every footprint inside the walls (closest: {worst[1]})", worst[0], 0.0)
    for c in cs:
        if c["shape"] not in ("slab",) and c["key"] not in ("window", "shelf", "frame_1", "frame_2", "frame_3") \
                and not c["key"].startswith("vine") and wall_gap(c) < 0.005 and c["at"][2] < 2.0:
            chk(f"{c['label'].lower()} off the wall", wall_gap(c), 0.005)
    # 2. each other: every pair whose heights overlap, and the desk top
    ps = pairs()
    clash = [p for p in ps if p[0] < 0.01]
    chk(f"every pair of components clear (closest: {ps[0][1]} / {ps[0][2]})", ps[0][0], 0.01)
    for g, a, b in clash:
        chk(f"{a} to {b}", g, 0.01)
    for g, a, b in ps[:6]:
        if g >= 0.01 and g < 0.04:
            chk(f"tight pair: {a} to {b}", g, 0.01)
    # 3. the door swing and the walkway from the door
    low = [c for c in cs if zrange(c)[0] < DOOR["head"] and c["shape"] != "slab"]
    g = min((gap(DOOR_SWING, foot(c)), c["key"]) for c in low)
    chk(f"walkway: door swing to the nearest thing ({g[1]})", g[0], 0.70)
    chk("walkway: door swing to the desk's outer end", gap(DOOR_SWING, MAIN_POLY), 0.70)
    # 4. the window
    chk("the return ends 8 cm short of the window", WINDOW_V3["x0"] - RET["x1"], 0.08)
    chk("pegboard clear of the window's edge", WINDOW_V3["x0"] - (PEG["x"] + PEG["w"] / 2), 0.05)
    chk("neon clear of the window's edge", WINDOW_V3["x0"] - (CP["neon"]["at"][0] + CP["neon"]["size"][0] / 2), 0.05)
    chk("window head to the ceiling", H - WINDOW_V3["head"], 0.50)
    chk("plant pot on the stone ledge", LEDGE_IN - (RY - CP["plant"]["at"][1] + CP["plant"]["size"][0] / 2 - 0.05), 0.0)
    chk("rack clear of the stone ledge", gap(RACK_FOOT, WIN_ZONE), 0.03)
    # 5. walkways (70)
    out_zone = circ(*CHAIR_OUT, CHAIR_BASE_R)
    chk("walkway: chair pulled out to the piano bench, played", gap(out_zone, bench_foot(True)), 0.70)
    chk("walkway: chair pulled out to the DJ's standing place", gap(out_zone, DJ_ZONE), 0.70)
    chk("walkway to the window: the return's end to the rack", gap(RET_POLY, RACK_FOOT), 0.70)
    chk("walkway to the window: chair swing to the rack", gap(circ(*SEAT, SWING_R), RACK_FOOT), 0.70)
    chk("walkway: the DJ's standing place to the bench, played", gap(DJ_ZONE, bench_foot(True)), 0.70)
    chk("walkway: the bench, played, to the AI desk's outer end", gap(bench_foot(True), MAIN_POLY), 0.70)
    # 6. the chair's swing (radius 40 at the parked place)
    sw = circ(*SEAT, SWING_R)
    chk("chair swing to the main run's front edge", gap(sw, MAIN_POLY), 0.03)
    chk("chair swing to the return's front edge", gap(sw, RET_POLY), 0.03)
    for k in ("alex_1", "alex_2"):
        chk(f"chair swing to {CP[k]['label'].lower()}", gap(sw, foot(CP[k])), 0.03)
    chk("chair base, parked, to the main run (knees under the top)", gap(circ(*SEAT, CHAIR_BASE_R), MAIN_POLY), 0.0)
    # 7. the main run's stack
    chk("ultrawide bottom over the Apollo and the Stream Deck", UW["z"] - (TOP + max(CP["interface"]["size"][2], CP["streamdeck"]["size"][2])), 0.03)
    chk("posts canvas (16:10) inside the 27 in glass", SD_GLASS[0] - POSTS["w"], 0.0)
    chk("light bar to the shelf", SHELF["z"] - SHELF["t"] - (SD["z"] + SD["h"] + 0.03), 0.10)
    chk("key light panels under the shelf", SHELF["z"] - SHELF["t"] - (KL_Z + KL_PANEL[2]), 0.0)
    for i in range(2):
        hgt = KL_POLE_TOP - TOP
        chk(f"key light pole {i + 1}: working height inside 55 to 125", min(hgt - 0.55, 1.25 - hgt), 0.0)
    reach = math.dist(CAM_ARM_FROM, (CAM_AT[0], CAM_AT[1], CAM_AT[2] + 0.035))
    chk("camera flex arm reach (Flex Arm L about 45)", 0.45 - reach, 0.0)
    reach = math.dist(MIC["clamp"], MIC["capsule"][:2])
    chk("mic arm reach (PSA1+ 94 horizontal)", PSA1_REACH - reach, 0.0)
    arm = mic_arm()
    pts = [p for a, b in zip(arm, arm[1:]) for p in _seg_pts(a, b)]
    for k in ("a7v_1", "spk_plate_1", "spk_pole_1", "camera", "keyboard", "streamdeck", "snake_plant", "vine_1", "keylight_pole_1"):
        chk(f"mic arm to {CP[k]['label'].lower()}", min(_pt_box_dist(p, CP[k]) for p in pts) - 0.012, 0.02)
    flex = _seg_pts(CAM_ARM_FROM, (CAM_AT[0], CAM_AT[1], CAM_AT[2] + 0.035))[:-2]
    for k in ("a7v_1", "vine_1"):
        chk(f"camera arm to {CP[k]['label'].lower()}", min(_pt_box_dist(p, CP[k]) for p in flex) - 0.01, 0.02)
    chk("tweeters at standing ear level (within 5 cm)", 0.05 - abs(TWEETER_Z - EAR_STANDING), 0.0)
    # 8. the return
    chk("PC inside the return's front edge", PC_AT[1] - PC_SIZE[1] / 2 - RET["y0"], 0.05)
    chk("laptop top to the pegboard", PEG["z"] - (TOP + 0.15 + 0.24), 0.10)
    lap = foot(CP["laptop"])
    chk("laptop inside the return's end", RET["x1"] - max(x for x, _ in lap), 0.02)
    chk("laptop inside the return's front edge", min(y for _, y in lap) - RET["y0"], 0.0)
    chk("PC top to the light panels", CP["nanoleaf"]["at"][2] - (TOP + PC_SIZE[2]), 0.05)
    chk("pegboard to the light panels", (PEG["x"] - PEG["w"] / 2) - (CP["nanoleaf"]["at"][0] + CP["nanoleaf"]["size"][0] / 2), 0.03)
    chk("neon top to the ceiling", H - (CP["neon"]["at"][2] + CP["neon"]["size"][2]), 0.50)
    # 9. the music side
    WG = WALL_GUITARS_V3
    for i in range(2):
        chk(f"guitar gap 0{i + 1} to 0{i + 2}", (WG["y"][i] - WG["width"][i] / 2) - (WG["y"][i + 1] + WG["width"][i + 1] / 2), 0.10)
    chk(f"lid's swing to {PIANO_LID_MAX_DEG} deg to the guitar bottoms", WG_BOTTOM - LID_REACH, 0.05)
    for i in range(3):
        chk(f"guitar_0{i + 1} top to the ceiling", H - (WG_BOTTOM + WG_LEN[i]), 0.10)
    py = [y for _, y in PIANO_FOOT]
    chk("wall guitars inside the piano's width", min(max(py) - (WG["y"][0] + WG_WID[0] / 2),
                                                     (WG["y"][2] - WG_WID[2] / 2) - min(py)), 0.0)
    chk("rack to the piano", gap(RACK_FOOT, PIANO_FOOT), 0.05)
    chk("rack to the bench, played", gap(RACK_FOOT, bench_foot(True)), 0.05)
    chk("DJ stand to the piano", gap(foot(CP["dj_stand"]), PIANO_FOOT), 0.20)
    chk("lightstick top under the right-wall guitars' line", WG_BOTTOM - (CP["lightstick"]["at"][2] + 0.27), 0.10)
    # 10. the cameras: the music side hidden from the lab views, revealed by About
    cm_ = cams()
    for nm in ("hero", "portrait", "phone"):
        chk(f"music side hidden from {nm} (share of its points in frame)", 0.05 - share(cm_[nm], MUSIC_KEYS), 0.0)
    chk("hero sees the AI lab (share of its points in frame)", share(cm_["hero"], LAB_KEYS) - 0.90, 0.0)
    chk("about shows the piano, guitars, rack and decks", share(cm_["about"], MUSIC_KEYS) - 0.85, 0.0)
    chk("intro: the window fills the frame (corners outside it)", 0.0 if not any(
        cm_["intro"].visible(p) for p in ((WINDOW_V3["x0"], RY, WINDOW_V3["sill"]), (WINDOW_V3["x1"], RY, WINDOW_V3["head"]))) else -1, 0.0)
    return ch


if __name__ == "__main__":
    for name, g, need, ok in run_checks():
        print(("ok    " if ok else "CLASH ") + f"{name}: {g * 100:.1f} (need {need * 100:.0f})")
