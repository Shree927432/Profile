"""Room plan v2 sheet (NOT approved yet): half music studio, half AI lab, window centred.

Plain Python (no Blender), drawn to scale from blender/lib/plan_v2.py, the same numbers
the v2 blockout (room_plan_v2_blockout.py) builds. Reuses the drawing helpers of the
approved 2026-10-22 sheet (room_plan_sheet.py) and the piano front of the piano sheet.

    python3 blender/design/room_plan_v2_sheet.py

Run the blockout first (it renders blockout-hero.png and blockout-phone.png into the same
folder; the sheet places them). Output: video-local/footage/2026-10-23-room-plan-v2/
room-plan-v2-sheet.{html,png}. Prints the clearance checks.
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import constants as C, plan_v2 as P  # noqa: E402
from lib.piano_layout import lid_profile  # noqa: E402
import room_plan_sheet as S  # noqa: E402  (helpers: text, dim, panel, View, gap, Cam, guitar_outline)
import piano_design_sheet as PDS  # noqa: E402

out = S.out
add, text, para, panel, dim, leader, cm, View = S.add, S.text, S.para, S.panel, S.dim, S.leader, S.cm, S.View
INK, ACC, MUTED, PAPER, RULE = S.INK, S.ACC, S.MUTED, S.PAPER, S.RULE
OBJ_FILL, OBJ_LINE, SET_FILL = S.OBJ_FILL, S.OBJ_LINE, S.SET_FILL
DASH, DOT = S.DASH, S.DOT
RX, RY, H = P.RX, P.RY, P.H
WIN, DOOR, R = P.WINDOW_V2, P.DOOR, P.ROOM
OUT = os.path.join(C.FOOTAGE, "2026-10-23-room-plan-v2")
W_PX, H_PX = 2400, 3560
CHROME = PDS.CHROME
CP = {c["key"]: c for c in P.COMPONENTS}
NUM = {k: i + 1 for i, (k, _, _) in enumerate(P.OBJECTS_V2)}


def rot(x, y, yaw):
    a = math.radians(yaw)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def rect_w(cx, cy, w, d, yaw):
    return [(cx + dx, cy + dy) for dx, dy in (rot(x, y, yaw) for x, y in
                                              ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)))]


def circ(cx, cy, r, n=20):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def foot(c):
    w, d, _ = c["size"]
    x, y, _ = c["at"]
    if c["shape"] == "cyl":
        return circ(x, y, w / 2)
    return rect_w(x, y, w, d, c["yaw"])


PIA = P.PIANO_V2
PN, BN = C.PIANO, C.BENCH


def piano_local(x, y):
    dx, dy = rot(x, y, PIA["yaw"])
    return PIA["x"] + dx, PIA["y"] + dy


PIANO_FOOT = [piano_local(x, y) for x, y in ((-PN["width"] / 2, PN["toe_front_y"]), (PN["width"] / 2, PN["toe_front_y"]),
                                             (PN["width"] / 2, PN["lid_over_back"]), (-PN["width"] / 2, PN["lid_over_back"]))]


def bench_foot(played=False):
    cy = BN["cy"] + (0 if played else PIA["bench_in"])
    return [piano_local(x, y) for x, y in ((-BN["w"] / 2, cy - BN["d"] / 2), (BN["w"] / 2, cy - BN["d"] / 2),
                                           (BN["w"] / 2, cy + BN["d"] / 2), (-BN["w"] / 2, cy + BN["d"] / 2))]


RK = P.RACK_V2
RACK_FOOT = [(RK["x"] + dx, RK["y"] + dy) for dx, dy in (rot(x, y, RK["yaw"]) for x, y in (
    (P.RACK_EXT[0], P.RACK_EXT[2]), (P.RACK_EXT[1], P.RACK_EXT[2]), (P.RACK_EXT[1], P.RACK_EXT[3]), (P.RACK_EXT[0], P.RACK_EXT[3])))]
DK = P.DESK_V2
BACK = DK["back"]
RET = DK["ret"]
DESK_L = [(BACK["x0"], BACK["y1"]), (BACK["x1"], BACK["y1"]), (BACK["x1"], BACK["y0"]), (RET["x1"], BACK["y0"]),
          (RET["x1"], RET["y0"]), (RET["x0"], RET["y0"])]
CHAIR_ZONE = [(P.KNEE_BACK[0], BACK["y0"] - 1.00), (P.KNEE_BACK[1] + 0.06, BACK["y0"] - 1.00),
              (P.KNEE_BACK[1] + 0.06, BACK["y0"]), (P.KNEE_BACK[0], BACK["y0"])]          # 100 behind the back run
CHAIR_ZONE_RET = [(RET["x1"], P.KNEE_RET[0]), (RET["x1"] + 1.00, P.KNEE_RET[0]),
                  (RET["x1"] + 1.00, P.KNEE_RET[1]), (RET["x1"], P.KNEE_RET[1])]          # 100 beside the return
lid90 = max(z for _, z in lid_profile(90)[0])
WG = P.WALL_GUITARS_V2

# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------
CHECKS = []


def chk(name, g, need):
    CHECKS.append((name, g, need, g >= need))


def run_checks():
    door_leaf = DOOR["y1"] - DOOR["y0"] - 0.05
    door_arc = [(-RX, DOOR["y0"]), (-RX + door_leaf, DOOR["y0"]), (-RX + door_leaf, DOOR["y0"] + door_leaf),
                (-RX, DOOR["y0"] + door_leaf)]
    window_line = [(WIN["x0"], RY - 0.01), (WIN["x1"], RY - 0.01), (WIN["x1"], RY), (WIN["x0"], RY)]
    chk("walkway to the window: desk end to rack", S.gap([(BACK["x1"], BACK["y0"]), (BACK["x1"], BACK["y1"]),
        (BACK["x1"] - 0.01, BACK["y1"]), (BACK["x1"] - 0.01, BACK["y0"])], RACK_FOOT), 0.70)
    chk("walkway: chair pulled out to the piano bench, played", S.gap(CHAIR_ZONE, bench_foot(True)), 0.70)
    chk("walkway: chair zone (return side) to the bench, played", S.gap(CHAIR_ZONE_RET, bench_foot(True)), 0.70)
    chk("walkway: chair to the rack", S.gap(foot(CP["chair"]), RACK_FOOT), 0.70)
    chk("walkway: return end to the door swing", S.gap(DESK_L[3:6] + [(RET["x0"], RET["y0"])], door_arc), 0.70)
    chk("rack to bench at rest", S.gap(RACK_FOOT, bench_foot()), 0.03)
    chk("rack to bench, played", S.gap(RACK_FOOT, bench_foot(True)), 0.02)
    chk("rack to piano", S.gap(RACK_FOOT, PIANO_FOOT), 0.05)
    chk("rack corner into the window width (on the floor, below the sill)", min(x for x, _ in RACK_FOOT) - WIN["x1"], -0.05)
    chk("desk end to the window", WIN["x0"] - BACK["x1"], 0.05)
    chk("piano case to the back wall", RY - max(y for _, y in PIANO_FOOT), 0.05)
    for k in ("alex_1", "alex_2", "alex_3"):
        chk(f"parked chair to {CP[k]['label'].lower()}", S.gap(foot(CP["chair"]), foot(CP[k])), 0.02)
    chk("rack to the back wall", RY - max(y for _, y in RACK_FOOT), 0.02)
    for a, b, need in (("a7v_1", "pc", 0.03), ("a7v_1", "interface", 0.02), ("a7v_2", "streamdeck", 0.02),
                       ("pc", "lightstick", 0.03), ("lightstick", "mstand", 0.03), ("dj", "mstand", 0.0),
                       ("a7v_2", "keylight_pole_2", 0.0), ("a7v_1", "keylight_pole_1", 0.0), ("snake_plant", "mouse", 0.03)):
        chk(f"{CP[a]['label'].lower()} to {CP[b]['label'].lower()}", S.gap(foot(CP[a]), foot(CP[b])), need)
    kl = CP["keylight_1"]
    chk("key light 1 panel to the left wall", min(x for x, _ in foot(kl)) + RX, 0.0)
    reach = math.dist(P.MIC["clamp"], P.MIC["capsule"][:2])
    chk("mic arm reach (PSA1+ about 82 cm)", 0.82 - reach, 0.0)
    for i in range(2):
        chk(f"guitar gap 0{i + 1} to 0{i + 2}", (WG["y"][i] - WG["width"][i] / 2) - (WG["y"][i + 1] + WG["width"][i + 1] / 2), 0.10)
    chk("lid at 90 deg to the lowest guitar", WG["bottom"] - lid90, 0.05)
    for i in range(3):
        chk(f"guitar_0{i + 1} top to the ceiling", H - (WG["bottom"] + WG["length"][i]), 0.10)
    chk("guitar_01 to the back wall", RY - (WG["y"][0] + WG["width"][0] / 2), 0.10)
    chk("PC top to the pegboard", CP["pegboard"]["at"][2] - (P.TOP + CP["pc"]["size"][2]), 0.05)
    chk("light bar to the ledge", P.LEDGE["z"] - (CP["screenbar"]["at"][2] + 0.03), 0.10)
    chk("ultrawide bottom over the console", CP["ultrawide"]["at"][2] - (P.TOP + CP["interface"]["size"][2]), 0.01)


# ---------------------------------------------------------------------------
# camera: what the hero frame sees (frustum only, no occlusion)
# ---------------------------------------------------------------------------
HV = P.HERO_V2
CAM = S.Cam(HV["pos"], HV["target"], HV["vfov"], 16 / 9)
CAM50 = S.Cam(HV["pos"], HV["target"], 50, 16 / 9)
PHONE = S.Cam(HV["pos"], HV["phone_target"], HV["phone_vfov"], 390 / 844)


def pts3(c):
    w, d, h = c["size"]
    x, y, z = c["at"]
    if c["key"].startswith("guitar_0"):
        u = c["size"][0] / 2
        return [(x, y + s * u, z + t * c["size"][2]) for s in (-1, 0, 1) for t in (0, 0.5, 1)]
    if c["key"] == "rack":
        return [(px, py, z) for px, py in RACK_FOOT] + [(px, py, 1.05) for px, py in RACK_FOOT]
    if c["key"] == "window":
        return [(xx, RY, zz) for xx in (WIN["x0"], 0, WIN["x1"]) for zz in (WIN["sill"], WIN["head"])]
    if c["key"] == "piano":
        return [(px, py, zz) for px, py in PIANO_FOOT for zz in (0, PN["case_top"])]
    if c["key"] == "mic":
        return [P.MIC["capsule"], P.MIC["elbow"]]
    return [(px, py, zz) for px, py in foot(c) for zz in (z, z + h)]


def visibility(cam):
    res = {}
    for k, _, _ in P.OBJECTS_V2:
        ps = [p for c in P.COMPONENTS if c["role"] == k for p in pts3(c)]
        res[k] = sum(1 for p in ps if cam.visible(p)) / len(ps)
    return res


def marker_point(k):
    main = {"obj_monitor": "studio_display", "obj_rig": "pc", "obj_mic": "mic", "obj_frames": "frame_2",
            "obj_studio": "dj", "obj_piano": "piano", "obj_guitars": "guitar_02", "obj_light": "pendant",
            "obj_window": "window", "obj_plant": "plant"}[k]
    c = CP[main]
    x, y, z = c["at"]
    h = c["size"][2]
    if main == "piano":
        return (PIA["x"] - 0.40, PIA["y"] + 0.45, 1.0)
    if main == "window":
        return (-0.30, RY, 1.75)
    if main == "mic":
        return P.MIC["capsule"]
    if main == "guitar_02":
        return (x, y, z + 0.25)
    return (x, y, z + h / 2)


def markers(cam, x0, y0, w, h):
    for k, _, _ in P.OBJECTS_V2:
        q = cam.cam(marker_point(k))
        if q[2] <= 0.05:
            continue
        a, b = cam.ndc(q)
        if abs(a) > 1 or abs(b) > 1:
            continue
        px, py = x0 + (a + 1) / 2 * w, y0 + (1 - b) / 2 * h
        add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="13" fill="{OBJ_LINE}" stroke="#fff" stroke-width="2"/>')
        text(px, py + 5, str(NUM[k]), 14, "#fff", "middle", weight=700)


# ---------------------------------------------------------------------------
# 1. floor plan
# ---------------------------------------------------------------------------
def walls_plan(v):
    tb, ts = R["wall_back_t"], R["wall_side_t"]
    v.rect(-RX - ts, RX + ts, RY, RY + tb, S.WALL_POCHE, S.WALL_POCHE, 0.5)
    v.rect(-RX - ts, -RX, -RY - ts, RY, S.WALL_POCHE, S.WALL_POCHE, 0.5)
    v.rect(RX, RX + ts, -RY - ts, RY, S.WALL_POCHE, S.WALL_POCHE, 0.5)
    v.rect(-RX - ts, RX + ts, -RY - ts, -RY, "#8d8880", "#8d8880", 0.5)
    v.rect(WIN["x0"], WIN["x1"], RY, RY + tb, PAPER, PAPER, 0)
    v.line((WIN["x0"], RY + tb * 0.45), (WIN["x1"], RY + tb * 0.45), INK, 1.0)
    v.line((WIN["x0"], RY + tb * 0.58), (WIN["x1"], RY + tb * 0.58), INK, 1.0)
    v.rect(WIN["x0"] - 0.05, WIN["x1"] + 0.05, RY - (WIN["ledge_d"] - tb * 0.45), RY, "#d2ccc0", INK, 0.8)
    dy0, dy1 = DOOR["y0"], DOOR["y1"]
    v.rect(-RX - ts, -RX, dy0, dy1, PAPER, PAPER, 0)
    leaf = dy1 - dy0 - 0.05
    v.rect(-RX, -RX + leaf, dy0, dy0 + DOOR["leaf_t"], "#fff", INK, 1.0)
    arc = [(-RX + leaf * math.sin(math.radians(a)), dy0 + leaf * math.cos(math.radians(a))) for a in range(0, 91, 3)]
    v.path(arc, MUTED, 0.9, extra=DASH)


def fill_of(c):
    return (OBJ_FILL, OBJ_LINE) if c["role"] != "set" else (SET_FILL, INK)


def plan(px, py, pw, ph):
    panel(px, py, pw, ph, "1 · Floor plan",
          "top view, back wall at the top · cm · blue: interactive objects (numbers as in the legend), grey: set dressing · dashed: above the desk or on a wall")
    s = 210
    v = View(px + 262 + RX * s, py + 250 + (RY + R["wall_back_t"]) * s, s)
    # halves
    v.rect(-RX, 0, -RY, RY, "#eef2f7", "none", 0)
    v.rect(0, RX, -RY, RY, "#f4efe6", "none", 0)
    v.line((0, -RY), (0, RY), MUTED, 0.8, extra=DOT)
    xa, ya = v.p(-RX / 2, -RY + 0.25)
    text(xa, ya, "AI LAB", 22, "#9db0c8", "middle", weight=700)
    xa, ya = v.p(RX / 2, -RY + 0.25)
    text(xa, ya, "MUSIC STUDIO", 22, "#c8b89d", "middle", weight=700)
    walls_plan(v)
    rug = CP["rug"]
    v.poly(foot(rug), "#ece4d8", MUTED, 0.9, extra=DASH)
    xr, yr = v.p(rug["at"][0], rug["at"][1] - 0.85)
    text(xr, yr, "rug 150 × 230", 12, MUTED, "middle")
    # chair clearance zone
    v.poly(CHAIR_ZONE, "#dfe8f3", "#7f9cc4", 1.0, extra=DASH + ' fill-opacity=".45"')
    v.poly(CHAIR_ZONE_RET, "#dfe8f3", "#7f9cc4", 1.0, extra=DASH + ' fill-opacity=".35"')
    xz, yz = v.p(P.XM, BACK["y0"] - 0.85)
    text(xz, yz, "chair zone: 100 cm behind both runs", 12, "#46628a", "middle")
    # desk
    v.poly(DESK_L, "#ffffff", INK, 1.6)
    for k, (x, y, yaw) in enumerate(DK["drawers"]):
        v.poly(rect_w(x, y, P.ALEX[0], P.ALEX[1], yaw), "none", MUTED, 0.9, extra=DOT)
    # components
    order = sorted(P.COMPONENTS, key=lambda c: c["at"][2])
    for c in order:
        k = c["key"]
        if k in ("desk", "led", "rug", "window", "piano", "bench", "rack", "mic", "panel_guitar") or k.startswith("alex"):
            continue
        f, st = fill_of(c)
        high = c["at"][2] > 1.2 or c["shape"] == "slab"
        if k.startswith("guitar_0"):
            continue
        if k == "chair":
            v.circle(c["at"][0], c["at"][1], 0.345, "#eceef1", INK, 1.0)
            v.poly(rect_w(c["at"][0], c["at"][1], 0.50, 0.46, c["yaw"]), "#d9dce1", INK, 0.9)
            xc, yc = v.p(c["at"][0], c["at"][1])
            text(xc, yc + 4, "chair", 12, INK, "middle")
            continue
        if k == "pendant":
            v.circle(c["at"][0], c["at"][1], 0.20, "none", OBJ_LINE, 1.1, extra=DASH)
            continue
        v.poly(foot(c), "none" if high else f, st, 1.0, extra=(DASH if high else ""))
    # mic arm
    m = P.MIC
    v.path([m["clamp"], m["elbow"][:2], m["capsule"][:2]], OBJ_LINE, 1.6)
    v.circle(*m["capsule"][:2], 0.035, OBJ_FILL, OBJ_LINE, 1.1)
    # piano, bench, rack
    v.poly(PIANO_FOOT, "#2a2a2c", INK, 1.2)
    xp, yp = v.p(PIA["x"] - 0.30, PIA["y"])
    text(xp, yp, "Piano", 15, "#fff", "middle", weight=650, rot=-90)
    for i in range(3):
        y = WG["y"][i]
        v.rect(RX - 0.125, RX - 0.075, y - WG["width"][i] / 2, y + WG["width"][i] / 2, OBJ_FILL, OBJ_LINE, 1.1, extra=DASH)
        xg, yg = v.p(RX - 0.21, y)
        text(xg, yg + 4, f"0{i + 1}", 12, "#cfe0f5", "middle", weight=700)
    v.poly(bench_foot(), "#5a5a5e", INK, 1.0)
    v.poly(bench_foot(True), "none", MUTED, 0.9, extra=DASH)
    v.poly(RACK_FOOT, OBJ_FILL, OBJ_LINE, 1.2)
    slots = [(i - (RK["slots"] - 1) / 2) * RK["pitch"] for i in range(RK["slots"])]
    for i, sl in enumerate(slots):
        a = [(RK["x"] + dx, RK["y"] + dy) for dx, dy in (rot(-0.30, sl, RK["yaw"]), rot(0.25, sl, RK["yaw"]))]
        v.line(a[0], a[1], OBJ_LINE, 2.2)
        xq, yq = v.p(*[(RK["x"] + dx, RK["y"] + dy) for dx, dy in [rot(-0.40, sl, RK["yaw"])]][0])
        text(xq, yq + 4, f"0{i + 4}", 11, OBJ_LINE, "middle", weight=700)
    # labels with leaders (page coords)
    labs = [
        ("studio_display", (-0.55, 2.80), "screens on one pole: 27 in (posts) over the 34 in curved (dashboard)"),
        ("a7v_1", (-2.45, 2.62), "A7V white on stands, toed in 34°"),
        ("ledge", (-2.45, 2.80), "floating ledge 115, three frames (wall)"),
        ("pc", (-2.45, 1.40), "training rig (PC)"),
        ("dj", (-2.45, 0.55), "DJ decks, laptop behind"),
        ("lightstick", (-2.45, 0.98), "lightstick"),
        ("pegboard", (-2.45, 0.15), "pegboard, neon above (wall)"),
        ("nanoleaf", (-2.45, 1.85), "light panels (wall)"),
        ("plant", (0.75, 2.62), "plant on the sill, window 120 centred"),
        ("rack", (0.30, 0.85), "rack: 04 05 06"),
        ("guitar_02", (1.30, 0.02), "wall guitars 01 02 03, on hooks above the piano"),
        ("snake_plant", (-0.25, 1.15), "snake plant"),
    ]
    for key, (lx, ly), s_ in labs:
        c = CP[key]
        xx, yy = c["at"][0], c["at"][1]
        x0, y0 = v.p(xx, yy)
        x1, y1 = v.p(lx, ly)
        leader(x0, y0, x1, y1, s_, "end" if lx < xx else "start", 12)
    # door, switch, pendant labels
    x0, y0 = v.p(-RX + 0.4, DOOR["y0"] + 0.4)
    text(x0 + 6, y0, "door 90 × 210", 12, MUTED)
    lx, ly = v.p(P.LIGHT_V2["x"], P.LIGHT_V2["y"])
    text(lx, ly + 34, "ceiling light", 12, OBJ_LINE, "middle")
    # hero camera and FOV
    cx, cy = HV["pos"][0], HV["pos"][1]
    for cam_, col, ext in ((CAM, ACC, DASH), (PHONE, "#7f9cc4", DOT)):
        half = math.radians(cam_.hfov / 2)
        for sgn in (-1, 1):
            ang = cam_.yaw + sgn * half
            dx, dy = math.sin(ang), math.cos(ang)
            # run to the first wall
            tx = ((RX if dx > 0 else -RX) - cx) / dx if abs(dx) > 1e-6 else 1e9
            ty = (RY - cy) / dy
            t = min(tx, ty)
            v.line((cx, cy), (cx + dx * t, cy + dy * t), col, 1.1, extra=ext)
    v.rect(cx - 0.07, cx + 0.07, cy - 0.06, cy + 0.06, ACC, INK, 1)
    xh, yh = v.p(cx, cy)
    text(xh + 14, yh - 10, f"hero camera, eye {cm(HV['pos'][2], 0)}, 10 cm off the front wall, centred", 13, ACC, weight=600)
    text(xh + 14, yh + 8, f"{HV['vfov']}° vertical, {CAM.hfov:.0f}° across on 16:9 · dotted: phone ({PHONE.hfov:.0f}° across)", 12, ACC)
    # dimensions
    top = v.p(0, -RY - 0.15)[1] + 28
    xs = [-RX, BACK["x1"], WIN["x0"], WIN["x1"], RX]
    for a, b in zip(xs, xs[1:]):
        dim(v.p(a, 0)[0], top, v.p(b, 0)[0], top, cm(b - a, 0), size=12)
    dim(v.p(-RX, 0)[0], top + 34, v.p(RX, 0)[0], top + 34, "440 inside", size=13)
    xr = v.p(RX + 0.15, 0)[0] + 34
    dim(xr, v.p(0, RY)[1], xr, v.p(0, -RY)[1], "420 inside", side=-1, size=13)
    # desk dims
    yb = v.p(0, BACK["y0"])[1] + 16
    dim(v.p(P.KNEE_BACK[0], 0)[0], yb, v.p(P.KNEE_BACK[1], 0)[0], yb, f"knee {cm(P.KNEE_BACK[1] - P.KNEE_BACK[0], 0)}", size=11)
    xd = v.p(RET["x1"], 0)[0] + 14
    dim(xd, v.p(0, P.KNEE_RET[1])[1], xd, v.p(0, P.KNEE_RET[0])[1], f"knee {cm(P.KNEE_RET[1] - P.KNEE_RET[0], 0)}", side=-1, size=11)
    xl = v.p(-RX, 0)[0] - 30
    dim(xl, v.p(0, RY)[1], xl, v.p(0, RET["y0"])[1], "return 180", size=12)
    dim(xl - 26, v.p(0, RY)[1], xl - 26, v.p(0, BACK["y0"])[1], "80", size=12)
    yd = v.p(0, RET["y0"])[1] + 20
    dim(v.p(-RX, 0)[0], yd, v.p(RET["x1"], 0)[0], yd, "60", side=-1, size=12)
    # piano position
    xpz = v.p(RX, 0)[0] + 10
    py0 = max(y for _, y in PIANO_FOOT)
    dim(xpz, v.p(0, RY)[1], xpz, v.p(0, py0)[1], cm(RY - py0, 0), side=-1, size=11)
    dim(xpz, v.p(0, py0)[1], xpz, v.p(0, min(y for _, y in PIANO_FOOT))[1], "piano 153", side=-1, size=11)
    # walkway notes
    g_win = [c for c in CHECKS if c[0].startswith("walkway to the window")][0][1]
    xw, yw = v.p((BACK["x1"] + min(x for x, _ in RACK_FOOT)) / 2, 1.42)
    text(xw, yw, f"walkway {cm(g_win, 0)} to the window", 12, ACC, "middle", weight=600)
    g_b = [c for c in CHECKS if c[0].startswith("walkway: chair pulled")][0][1]
    xw, yw = v.p(0.0, -0.35)
    text(xw, yw, f"open floor: {cm(g_b, 0)} from the chair zone to the bench (played)", 12, ACC, "middle", weight=600)
    g_d = [c for c in CHECKS if c[0].startswith("walkway: return end")][0][1]
    xw, yw = v.p(-RX + 0.55, -0.45)
    text(xw, yw, f"{cm(g_d, 0)} return end to the door swing", 12, ACC, "middle", weight=600)
    return v


# ---------------------------------------------------------------------------
# 2. elevations
# ---------------------------------------------------------------------------
def wall_frame(v, length, title, sub):
    v.rect(0, length, 0, H, "#fbfaf6", INK, 1.4)
    x, y = v.p(0, H)
    text(x, y - 34, title, 16, INK, weight=650)
    text(x, y - 16, sub, 12, MUTED)


def elev_rect(v, u0, u1, z0, z1, c, dashed=False):
    f, st = fill_of(c)
    if c.get("glow") and c["shape"] == "slab":
        f = "#eaf2ff"
    v.rect(u0, u1, z0, z1, "none" if dashed else f, st, 1.0, extra=DASH if dashed else "")


def proj_extent(c, axis):
    ps = foot(c)
    vals = [p[0] if axis == "x" else p[1] for p in ps]
    return min(vals), max(vals)


def elevations(px, py, pw, ph):
    panel(px, py, pw, ph, "2 · Wall elevations",
          "seen from inside the room · cm · solid: on or against that wall · dashed: standing out in the room")
    s = 142
    base = py + 115 + H * s
    # ---- back wall: u = x + RX
    vb = View(px + 40, base, s)
    wall_frame(vb, R["width"], "Back wall", "AI lab on the left, window centred, rack on the right")
    U = lambda x: x + RX  # noqa: E731
    vb.rect(U(WIN["x0"]), U(WIN["x1"]), WIN["sill"], WIN["head"], "#cfdcf2", INK, 1.2)
    for i in range(1, 6):
        z = WIN["sill"] + (WIN["head"] - WIN["sill"]) * i / 6
        vb.line((U(WIN["x0"]), z), (U(WIN["x1"]), z), "#7d8696", 0.7)
    vb.line((U(0), WIN["sill"]), (U(0), WIN["head"]), INK, 0.8)
    vb.rect(U(WIN["x0"] - 0.05), U(WIN["x1"] + 0.05), WIN["sill"] - 0.03, WIN["sill"], "#d2ccc0", INK, 0.8)
    # desk top and drawers
    vb.rect(U(BACK["x0"]), U(BACK["x1"]), P.TOP - DK["t"], P.TOP, "#fff", INK, 1.3)
    for x, y, yaw in DK["drawers"][:2]:
        vb.rect(U(x - P.ALEX[0] / 2), U(x + P.ALEX[0] / 2), 0, P.ALEX[2], "#fff", INK, 1.0)
        for j in range(1, 5):
            vb.line((U(x - P.ALEX[0] / 2), P.ALEX[2] * j / 5), (U(x + P.ALEX[0] / 2), P.ALEX[2] * j / 5), MUTED, 0.6)
    vb.line((U(BACK["x0"]), P.TOP - DK["t"] - 0.005), (U(BACK["x1"]), P.TOP - DK["t"] - 0.005), "#7fb6ff", 2.0)
    for key in ("pole", "keylight_pole_1", "keylight_pole_2", "iso_1", "iso_2", "a7v_1", "a7v_2", "ultrawide",
                "studio_display", "screenbar", "ledge", "frame_1", "frame_2", "frame_3", "keylight_1", "keylight_2",
                "camera", "interface", "streamdeck", "keyboard", "snake_plant", "plant"):
        c = CP[key]
        u0, u1 = proj_extent(c, "x")
        z0 = c["at"][2]
        elev_rect(vb, U(u0), U(u1), z0, z0 + c["size"][2], c, dashed=key in ("camera",))
    # rack (dashed, in the room) with guitars, piano side
    rx0, rx1 = min(x for x, _ in RACK_FOOT), max(x for x, _ in RACK_FOOT)
    vb.rect(U(rx0), U(rx1), 0, 1.06, "none", OBJ_LINE, 1.0, extra=DASH)
    xk, yk = vb.p(U((rx0 + rx1) / 2), 0.55)
    text(xk, yk, "rack, 3 guitars", 11, OBJ_LINE, "middle")
    px0 = min(x for x, _ in PIANO_FOOT)
    vb.rect(U(px0), U(RX - 0.05), 0, PN["case_top"] + PN["lid_t"], "none", MUTED, 0.9, extra=DASH)
    xk, yk = vb.p(U((px0 + RX) / 2), 0.6)
    text(xk, yk, "piano side", 11, MUTED, "middle")
    # dims back wall
    xq = vb.p(U(WIN["x1"]) + 0.08, 0)[0]
    dim(xq, vb.p(0, 0)[1], xq, vb.p(0, WIN["sill"])[1], "105", side=-1, size=11)
    dim(xq, vb.p(0, WIN["sill"])[1], xq, vb.p(0, WIN["head"])[1], "105", side=-1, size=11)
    xq = vb.p(U(BACK["x0"]) + 0.06, 0)[0]
    dim(xq, vb.p(0, 0)[1], xq, vb.p(0, P.TOP)[1], "73.5", side=-1, size=11)
    sp = P.SPEAKERS_V2[1]
    tw = sp["z"] + P.TWEETER_UP
    xq = vb.p(U(sp["x"]) + 0.16, 0)[0]
    dim(xq, vb.p(0, 0)[1], xq, vb.p(0, tw)[1], f"tweeter {cm(tw, 0)}", side=-1, size=11)
    sd = CP["studio_display"]
    xq = vb.p(U(P.XM), 0)[0]
    xs_ = vb.p(U(BACK["x0"]) + 0.30, 0)[0]
    dim(xs_, vb.p(0, sd["at"][2])[1], xs_, vb.p(0, sd["at"][2] + sd["size"][2])[1], "27 in", size=10)
    uw = CP["ultrawide"]
    dim(xs_, vb.p(0, uw["at"][2])[1], xs_, vb.p(0, uw["at"][2] + uw["size"][2])[1], "34 in", size=10)
    yq = vb.p(0, P.LEDGE["z"] + 0.52)[1]
    dim(vb.p(U(P.LEDGE["x0"]), 0)[0], yq, vb.p(U(P.LEDGE["x1"]), 0)[0], yq, "ledge 115 at 192", size=11)
    xf, yf = vb.p(U(P.XM), sd["at"][2] + sd["size"][2] / 2)
    text(xf, yf + 4, "posts", 11, OBJ_LINE, "middle", weight=700)
    xf, yf = vb.p(U(P.XM), uw["at"][2] + uw["size"][2] / 2)
    text(xf, yf + 4, "training dashboard", 11, OBJ_LINE, "middle", weight=700)
    # ---- left wall: facing -X, front corner at the left, u = y + RY
    x2 = px + 40 + R["width"] * s + 70
    vl = View(x2, base, s)
    wall_frame(vl, R["depth"], "Left wall", "door, then the desk return: rig, decks, pegboard, neon")
    U2 = lambda y: y + RY  # noqa: E731
    vl.rect(U2(DOOR["y0"]), U2(DOOR["y1"]), 0, DOOR["head"], "#f1ede5", INK, 1.1)
    vl.path([(U2(DOOR["y1"]), 0), (U2(DOOR["y0"]) + 0.02, DOOR["head"] / 2), (U2(DOOR["y1"]), DOOR["head"])], MUTED, 0.7, extra=DASH)
    sw = P.SWITCH
    vl.rect(U2(sw["y"]) - sw["w"] / 2, U2(sw["y"]) + sw["w"] / 2, sw["z"] - sw["h"] / 2, sw["z"] + sw["h"] / 2, SET_FILL, INK, 1)
    vl.rect(U2(RET["y0"]), U2(RY), P.TOP - DK["t"], P.TOP, "#fff", INK, 1.3)
    vl.line((U2(RET["y0"]), P.TOP - DK["t"] - 0.005), (U2(BACK["y0"]), P.TOP - DK["t"] - 0.005), "#7fb6ff", 2.0)
    x, y, yaw = DK["drawers"][2]
    vl.rect(U2(y - P.ALEX[0] / 2), U2(y + P.ALEX[0] / 2), 0, P.ALEX[2], "#fff", INK, 1.0)
    for j in range(1, 5):
        vl.line((U2(y - P.ALEX[0] / 2), P.ALEX[2] * j / 5), (U2(y + P.ALEX[0] / 2), P.ALEX[2] * j / 5), MUTED, 0.6)
    x, y, yaw = DK["drawers"][0]
    vl.rect(U2(y - P.ALEX[1] / 2), U2(y + P.ALEX[1] / 2), 0, P.ALEX[2], "#fff", INK, 1.0)
    for key in ("pc", "dj", "mstand", "laptop", "lightstick", "pegboard", "headphones", "neon", "nanoleaf",
                "a7v_1", "iso_1", "keylight_pole_1", "keylight_1"):
        c = CP[key]
        u0, u1 = proj_extent(c, "y")
        z0 = c["at"][2]
        elev_rect(vl, U2(u0), U2(u1), z0, z0 + c["size"][2], c, dashed=key in ("a7v_1", "iso_1", "keylight_1", "keylight_pole_1"))
    for key, lab in (("pc", "rig"), ("dj", "decks"), ("neon", "neon: our words"), ("pegboard", "pegboard"),
                     ("nanoleaf", "panels"), ("laptop", "laptop")):
        c = CP[key]
        u0, u1 = proj_extent(c, "y")
        xt, yt = vl.p(U2((u0 + u1) / 2), c["at"][2] + c["size"][2] / 2)
        text(xt, yt + 4, lab, 10, OBJ_LINE if c["role"] != "set" else INK, "middle", weight=600)
    xq = vl.p(U2(RET["y0"]) - 0.06, 0)[0]
    pg = CP["pegboard"]
    dim(xq, vl.p(0, 0)[1], xq, vl.p(0, pg["at"][2])[1], cm(pg["at"][2], 0), size=11)
    ne = CP["neon"]
    dim(xq, vl.p(0, ne["at"][2])[1], xq, vl.p(0, ne["at"][2] + ne["size"][2])[1], f"{cm(ne['at'][2], 0)} to {cm(ne['at'][2] + ne['size'][2], 0)}", size=11)
    yq = vl.p(0, 0)[1] + 18
    dim(vl.p(U2(RET["y0"]), 0)[0], yq, vl.p(U2(RY), 0)[0], yq, "return 180", side=-1, size=11)
    dim(vl.p(U2(DOOR["y1"]), 0)[0], yq, vl.p(U2(RET["y0"]), 0)[0], yq, cm(RET["y0"] - DOOR["y1"], 0), side=-1, size=11)
    # ---- right wall: facing +X, back corner at the left, u = RY - y
    x3 = x2 + R["depth"] * s + 70
    vr = View(x3, base, s)
    wall_frame(vr, R["depth"], "Right wall", "piano, three guitars on hooks, acoustic panel")
    U3 = lambda y: RY - y  # noqa: E731
    pgp = P.PANEL_GUITAR_V2
    vr.rect(U3(pgp["y1"]), U3(pgp["y0"]), pgp["z0"], pgp["z1"], "#3a3b41", "#2b2c31", 0.8)
    pv = PDS.View(vr.ox + U3(PIA["y"]) * s, base, s / 1000)
    PDS.front(pv, dict(PDS.TECH, sw=0.7), detail=False)
    hw = PN["width"] / 2 + PN["lid_over_side"]
    vr.rect(U3(PIA["y"]) - hw, U3(PIA["y"]) + hw, PN["case_top"] + PN["lid_t"], lid90, "#dfe8f3", "#7f9cc4", 1.0,
            extra=DASH + ' fill-opacity=".6"')
    xl_, yl_ = vr.p(U3(PIA["y"]), (PN["case_top"] + lid90) / 2 + 0.05)
    text(xl_, yl_ + 8, "top lid opened to 90°", 11, "#46628a", "middle")
    cols = ["#3a3a3c", "#f8f6f0", "#b8474b"]
    for i, y in enumerate(WG["y"]):
        L_, W_ = WG["length"][i], WG["width"][i]
        if i == 2:     # the double-neck: one wide body, two necks and heads
            body, neck, head = S.guitar_outline(L_ * 0.92, W_)
            for du in (-0.085, 0.085):
                vr.poly([(U3(y) + u + du, WG["bottom"] + vv) for u, vv in neck], "#c9b59c", OBJ_LINE, 0.9)
                vr.poly([(U3(y) + u + du, WG["bottom"] + vv * L_ / (L_ * 0.92)) for u, vv in head], "#8c3a3c", OBJ_LINE, 0.9)
            vr.poly([(U3(y) + u, WG["bottom"] + vv) for u, vv in body], cols[i], OBJ_LINE, 1.0)
            hz = WG["bottom"] + L_ - WG["hook_from_top"][i]
            for du in (-0.085, 0.085):
                vr.rect(U3(y) + du - 0.025, U3(y) + du + 0.025, hz - 0.05, hz, "#9a9a9a", INK, 0.8)
        else:
            body, neck, head = S.guitar_outline(L_, W_, archtop=(i == 0))
            for part_, col in ((neck, "#c9b59c"), (head, "#8c7a66"), (body, cols[i])):
                vr.poly([(U3(y) + u, WG["bottom"] + vv) for u, vv in part_], col, OBJ_LINE, 1.0)
            hz = WG["bottom"] + L_ - WG["hook_from_top"][i]
            vr.rect(U3(y) - 0.03, U3(y) + 0.03, hz - 0.05, hz, "#9a9a9a", INK, 0.8)
        xg, yg = vr.p(U3(y), WG["bottom"] + 0.20)
        text(xg, yg, f"0{i + 1}", 13, "#fff" if i != 1 else OBJ_LINE, "middle", weight=700)
        # top heights
        xt, yt = vr.p(U3(y), WG["bottom"] + L_ + 0.04)
        text(xt, yt, f"top {cm(WG['bottom'] + L_, 0)}", 10, ACC, "middle")
    bys = [p[1] for p in bench_foot()]
    vr.rect(U3(max(bys)), U3(min(bys)), 0, BN["h"], "none", MUTED, 0.9, extra=DASH)
    rfy = [p[1] for p in RACK_FOOT]
    vr.rect(U3(max(rfy)), U3(min(rfy)), 0, 1.06, "none", OBJ_LINE, 0.9, extra=DASH)
    xk, yk = vr.p(U3((max(rfy) + min(rfy)) / 2), 1.10)
    text(xk, yk, "rack", 11, OBJ_LINE, "middle")
    xq = vr.p(U3(WG["y"][2]) + WG["width"][2] / 2 + 0.10, 0)[0]
    dim(xq, vr.p(0, 0)[1], xq, vr.p(0, lid90)[1], cm(lid90, 1), side=-1, size=11)
    dim(xq, vr.p(0, lid90)[1], xq, vr.p(0, WG["bottom"])[1], cm(WG["bottom"] - lid90, 1), side=-1, size=11)
    dim(xq, vr.p(0, WG["bottom"])[1], xq, vr.p(0, WG["bottom"] + WG["length"][2])[1], cm(WG["length"][2], 0), side=-1, size=11)
    dim(xq, vr.p(0, WG["bottom"] + WG["length"][2])[1], xq, vr.p(0, H)[1], cm(H - WG["bottom"] - WG["length"][2], 0), side=-1, size=11)
    ygp = vr.p(0, WG["bottom"] - 0.12)[1]
    for i in range(2):
        a = U3(WG["y"][i]) + WG["width"][i] / 2
        b = U3(WG["y"][i + 1]) - WG["width"][i + 1] / 2
        dim(vr.p(a, 0)[0], ygp, vr.p(b, 0)[0], ygp, cm(b - a, 0), size=10)
    xa = vr.p(0, 0)[0]
    dim(xa, ygp, vr.p(U3(WG["y"][0]) - WG["width"][0] / 2, 0)[0], ygp, cm(RY - WG["y"][0] - WG["width"][0] / 2, 0), size=10)
    xq = vr.p(U3(PIA["y"] - PN["width"] / 2) + 0.06, 0)[0]
    dim(xq, vr.p(0, 0)[1], xq, vr.p(0, PN["case_top"] + PN["lid_t"])[1], cm(PN["case_top"] + PN["lid_t"], 1), side=-1, size=11)


# ---------------------------------------------------------------------------
# 3. hero blockout
# ---------------------------------------------------------------------------
def hero_panel(px, py, pw, ph):
    panel(px, py, pw, ph, "3 · From the hero camera: rough 3D blockout",
          "boxes in Blender (EEVEE, about 2 s a frame) from plan_v2.py, for composition only · numbers: the interactive objects")
    iw = pw - 36
    ih = iw * 9 / 16
    x0, y0 = px + 18, py + 76
    add(f'<image href="blockout-hero.png" x="{x0}" y="{y0}" width="{iw:.0f}" height="{ih:.0f}"/>')
    markers(CAM, x0, y0, iw, ih)
    text(x0 + 10, y0 + ih - 12, "desktop, 16:9", 13, "#fff", weight=600)
    pw2, ph2 = 300, 300 * 844 / 390
    yp = y0 + ih + 22
    add(f'<image href="blockout-phone.png" x="{x0}" y="{yp:.0f}" width="{pw2}" height="{ph2:.0f}"/>')
    add(f'<rect x="{x0}" y="{yp:.0f}" width="{pw2}" height="{ph2:.0f}" rx="16" fill="none" stroke="{INK}" stroke-width="3"/>')
    markers(PHONE, x0, yp, pw2, ph2)
    text(x0 + pw2 / 2, yp + ph2 + 20, "phone, 390 × 844, aimed at the posts screen", 12, MUTED, "middle")
    vis, vis50 = visibility(CAM), visibility(CAM50)
    tx = x0 + pw2 + 34
    lines = [("room_view (v2)", INK, 650),
             f"position x {cm(HV['pos'][0], 0)}, y {cm(HV['pos'][1], 0)}, eye {cm(HV['pos'][2], 0)} cm: on the",
             "centre line, 10 cm inside the front wall, so the window is the middle",
             f"of the frame, AI lab left, music studio right. Looks at the back wall's",
             f"centre at {cm(HV['target'][2], 0)} cm (a little under 1° down). {HV['vfov']}° vertical,",
             f"{CAM.hfov:.0f}° across on 16:9 (about a 20 mm lens on full frame).",
             "",
             ("Share of each object inside the 16:9 frame", INK, 650),
             ("(points of its box inside the frustum; at 54° and at the old 50°)", MUTED, 400)]
    yy = para(tx, yp + 16, lines, 14)
    for k, lab, _ in P.OBJECTS_V2:
        add(f'<circle cx="{tx + 9}" cy="{yy - 5:.0f}" r="9" fill="{OBJ_LINE}"/>')
        text(tx + 9, yy - 1, str(NUM[k]), 11, "#fff", "middle", weight=700)
        text(tx + 26, yy, lab, 13, INK)
        text(tx + 560, yy, f"{vis[k] * 100:.0f} %", 13, INK, "end", weight=600)
        text(tx + 640, yy, f"{vis50[k] * 100:.0f} %", 13, MUTED if vis50[k] >= 0.99 else "#a33", "end")
        yy += 21
    yy += 8
    para(tx, yy, [
        "At 50° (the approved lens) the side walls show only from y = 65 cm",
        "back, so the double-neck's near edge and the guitars' heads touch",
        "the frame; at 54° the walls show from y = 43 cm. The piano's front",
        "end is cut by the right edge either way; its keys and rest stay in.",
        "The posts screen is about 9 % of the frame's width (12 % before);",
        "a click still glides to the straight-on close-up as today.",
        "Phone: same place, 70° vertical, aimed at the screens.",
    ], 13, MUTED)
    return CAM


# ---------------------------------------------------------------------------
# 4. legend, 5. numbers and checks, 6. questions
# ---------------------------------------------------------------------------
def size_str(c):
    w, d, h = c["size"]
    if c["key"] == "desk":
        return "155×80 + 100×60"
    if c["shape"] == "cyl":
        return f"⌀{cm(w, 0)} × {cm(h, 0)}"
    if c["key"] in ("led",):
        return "along both front edges"
    f = lambda v: f"{v * 100:.1f}".rstrip("0").rstrip(".")  # noqa: E731
    return f"{f(w)} × {f(d)} × {f(h)}"


def legend(px, py, pw, ph):
    panel(px, py, pw, ph, "4 · Legend: every component",
          "w × d × h in cm, real outside sizes as published (UNSURE: re-check on the maker's page before modelling) · "
          "No logos, names or trademarked graphics on any model; the model names here are for reference only")
    rows = [c for c in P.COMPONENTS if c["key"] not in ("iso_2", "a7v_2", "keylight_2", "keylight_pole_2", "frame_2",
                                                       "frame_3", "alex_2", "alex_3", "guitar_02", "guitar_03")]
    rename = {"iso_1": "Speaker stands (2)", "a7v_1": "Studio monitors (2)", "keylight_1": "Key lights (2)",
              "keylight_pole_1": "Key light poles (2)", "frame_1": "Frames (3)", "alex_1": "Drawer units (3)",
              "guitar_01": "Wall guitars 01 to 03"}
    col_w = (pw - 36) / 2
    per = (len(rows) + 1) // 2
    for ci in range(2):
        x = px + 18 + ci * col_w
        y = py + 96
        text(x, y, "component", 12, MUTED, weight=600)
        text(x + 170, y, "real model", 12, MUTED, weight=600)
        text(x + 478, y, "size", 12, MUTED, weight=600)
        text(x + col_w - 14, y, "role", 12, MUTED, "end", weight=600)
        y += 8
        add(f'<line x1="{x}" y1="{y}" x2="{x + col_w - 14}" y2="{y}" stroke="{RULE}"/>')
        y += 18
        for c in rows[ci * per:(ci + 1) * per]:
            lab = rename.get(c["key"], c["label"])
            model = c["model"]
            if c["key"] == "guitar_01":
                model = "Lucille 107 × 41 · Strat 97.7 × 32.3 · double-neck 110 × 43"
            sz = size_str(c) if c["key"] != "guitar_01" else "see right wall"
            unsure = "UNSURE" in c["note"] or c["key"] in ("interface", "keyboard", "mstand", "guitar_01")
            text(x, y, lab[:25], 12.5, INK)
            text(x + 170, y, model if len(model) <= 50 else model[:48] + "…", 11.5, MUTED)
            text(x + 478, y, sz + (" ?" if unsure else ""), 12, INK)
            if c["role"] != "set":
                text(x + col_w - 14, y, f"{NUM[c['role']]} {c['role'][4:]}", 12, OBJ_LINE, "end", weight=650)
            else:
                text(x + col_w - 14, y, "set", 12, MUTED, "end")
            y += 19.5


def numbers_panel(px, py, pw, ph):
    panel(px, py, pw, ph, "5 · Numbers and checks", "plan_v2.py (constants.py untouched) · checked by this script")
    sp = P.SPEAKERS_V2[0]
    d_ear = math.dist((sp["x"], sp["y"]), P.EAR[:2])
    lines = [
        ("Desk (option A, refined)", INK, 650),
        f"Back run 155 × 80, x {cm(BACK['x0'], 0)} to {cm(BACK['x1'], 0)}, 5 cm short of the window.",
        f"Return 180 × 60 from the back wall (100 past the corner). Top 73.5, 3.5 cm.",
        f"Drawer units 36 × 58 × 70, top straight on them (70 + 3.5 = 73.5, as IKEA's file).",
        f"Knee space {cm(P.KNEE_BACK[1] - P.KNEE_BACK[0], 0)} under the back run, {cm(P.KNEE_RET[1] - P.KNEE_RET[0], 0)} under the return.",
        f"Screens centred on the back knee space, x {cm(P.XM, 1)}.",
        f"Speakers {cm(2 * P.SPK_DX, 0)} apart, {cm(d_ear, 0)} from the ear, toed in {abs(sp['yaw']):.0f}°,",
        f"tweeters at {cm(sp['z'] + P.TWEETER_UP, 0)}, backs 20 cm off the wall.",
        "",
        ("Window", INK, 650),
        "x −60 to +60, sill 105, head 210 (size unchanged).",
        "",
        ("Wall guitars (bottoms on one line at 172)", INK, 650),
        f"Lid at 90° reaches {cm(lid90, 1)}: {cm(WG['bottom'] - lid90, 1)} under the bodies.",
        f"Tops: 01 {cm(WG['bottom'] + WG['length'][0], 0)}, 02 {cm(WG['bottom'] + WG['length'][1], 0)}, "
        f"03 {cm(WG['bottom'] + WG['length'][2], 0)} (ceiling 300).",
        f"Centres y {', '.join(cm(y, 1) for y in WG['y'])}; 12 cm between bodies.",
        "Double-neck: two hooks, one per head, 17 cm apart.",
        "",
        ("Checks", INK, 650),
    ]
    para(px + 18, py + 92, lines[:-1], 13.5)
    y = py + 92
    text(px + 470, y, "Checks (need in brackets)", 13.5, INK, weight=650)
    y += 20
    for name, g, need, ok in CHECKS:
        val = "overlap" if g == -1.0 else cm(g, 1)
        text(px + 470, y, f"{'ok' if ok else 'CLASH'}  {name}: {val} ({cm(need, 0)})", 11.5, INK if ok else "#a33")
        y += 16.5


def objects_panel(px, py, pw, ph):
    panel(px, py, pw, ph, "6 · Interactive objects (limit 10)", "proposed; everything else is set dressing")
    y = py + 96
    for k, lab, what in P.OBJECTS_V2:
        add(f'<circle cx="{px + 30}" cy="{y - 5}" r="10" fill="{OBJ_LINE}"/>')
        text(px + 30, y - 1, str(NUM[k]), 12, "#fff", "middle", weight=700)
        text(px + 50, y, lab, 13.5, INK, weight=600)
        text(px + 50, y + 17, f"{k} · {what}", 12, MUTED)
        y += 40
    para(px + 18, y + 6, [
        "New: obj_rig (the PC and the 34 in dashboard; projects",
        "as training runs). Needs a MESHES.md change, asked below.",
        "obj_monitor moves to the 27 in screen: monitor_screen",
        "stays 16:10 (53.8 × 33.6) centred in the 16:9 glass, so",
        "the posts code and the 400 × 250 phone rule do not change.",
        "The audio interface is an Apollo x4: its big",
        "monitor knob is the volume, the preamp knob the pan.",
        "Ten is the limit: nothing else can become interactive.",
    ], 12.5, MUTED)


def questions(px, py, pw, ph):
    panel(px, py, pw, ph, "7 · For the owner", "recommendation first")
    qs = [
        ("1. Hero camera lens (stills below).", [
            "A (recommended): 54° vertical, about 20 mm, inside the room;",
            "   every object in the 16:9 frame, the orbit works as today.",
            "B: keep the approved 50° (22 mm): the guitars' heads and the",
            "   lamp touch the top edge, the double-neck the right edge.",
            "C: 50° from 40 cm behind the front wall (a cut-away set):",
            "   the calmest picture, but the front wall must be hidden",
            "   and the orbit kept from seeing past the side walls."]),
        ("2. Neon sign (still below).", [
            "A (recommended): left wall above the pegboard, as in",
            "   your photo; the back wall stays calm round the window.",
            "B: back wall above the frames: read straight on from the",
            "   hero, but the AI half's back wall gets crowded."]),
        ("3. Training rig as the tenth object.", [
            "A (recommended): its own object, obj_rig: click the PC,",
            "   fans pulse, the 34 in lists the projects as runs.",
            "   Needs a MESHES.md and contract change (new root).",
            "B: fold the PC and both screens into obj_monitor: nine",
            "   objects and one spare, but one heavy object file."]),
        ("4. Front half of the room (out of the hero view).", [
            "A (recommended): leave it open floor (door, walkway).",
            "B: a floor monstera or a beanbag, set dressing only."]),
    ]
    y = py + 92
    colx = [px + 18, px + 18 + (pw - 36) / 2]
    for i, (q, opts) in enumerate(qs):
        x = colx[i % 2]
        yy = y + (0 if i < 2 else 186)
        text(x, yy, q, 14.5, INK, weight=650)
        para(x + 10, yy + 22, opts, 12.5, MUTED, lh=17.5)
    tw = (pw - 36 - 3 * 14) / 4
    th = tw * 9 / 16
    ty = py + ph - th - 44
    for k, (f, lab) in enumerate((("blockout-hero.png", "1A · 54°, inside (recommended)"), ("option-lens-b-50.png", "1B · 50°, inside"),
                                  ("option-lens-c-cutaway.png", "1C · 50°, 40 cm behind the wall"),
                                  ("option-neon-b-back-wall.png", "2B · neon on the back wall"))):
        tx = px + 18 + k * (tw + 14)
        add(f'<image href="{f}" x="{tx:.0f}" y="{ty:.0f}" width="{tw:.0f}" height="{th:.0f}"/>')
        add(f'<rect x="{tx:.0f}" y="{ty:.0f}" width="{tw:.0f}" height="{th:.0f}" fill="none" stroke="{INK}" stroke-width="1"/>')
        text(tx, ty + th + 18, lab, 12.5, INK, weight=600)


def main():
    os.makedirs(OUT, exist_ok=True)
    out.clear()
    run_checks()
    add(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W_PX}" height="{H_PX}" '
        f'viewBox="0 0 {W_PX} {H_PX}" font-family="-apple-system, Helvetica Neue, Arial, sans-serif">')
    add(f'<rect width="{W_PX}" height="{H_PX}" fill="{PAPER}"/>')
    text(48, 58, "The room v2 · plan sheet: half music studio, half AI lab", 32, INK, weight=650)
    text(48, 88, "to scale from blender/lib/plan_v2.py · dimensions in cm · Blender axes: back wall +Y, hero camera −Y, "
         "origin on the floor at the room's centre · room 440 × 420 × 300, door unchanged", 16, MUTED)
    add(f'<rect x="{W_PX - 420}" y="30" width="372" height="40" rx="6" fill="#a33"/>')
    text(W_PX - 234, 57, "NOT YET APPROVED · proposal", 18, "#fff", "middle", weight=700)
    text(W_PX - 48, 92, "2026-10-23 · replaces the 2026-10-22 plan only once approved", 14, MUTED, "end")
    plan(40, 116, 1290, 1340)
    hero_panel(1350, 116, 1010, 1340)
    elevations(40, 1480, 2320, 640)
    legend(40, 2144, 1500, 640)
    objects_panel(1560, 2144, 800, 640)
    numbers_panel(40, 2808, 1060, 720)
    questions(1120, 2808, 1240, 720)
    add("</svg>")
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>Room plan v2</title>"
            f"<style>html,body{{margin:0;background:{PAPER}}}svg{{display:block}}</style></head><body>"
            + "\n".join(out) + "</body></html>")
    hp = os.path.join(OUT, "room-plan-v2-sheet.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    png = os.path.join(OUT, "room-plan-v2-sheet.png")
    subprocess.run([CHROME, "--headless", "--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist",
                    "--allow-file-access-from-files", "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={W_PX},{H_PX}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for name, g, need, ok in CHECKS:
        print(("ok    " if ok else "CLASH ") + f"{name}: {g * 100:.1f} cm (need {need * 100:.0f})")
    print("visibility 54:", {k: round(x, 2) for k, x in visibility(CAM).items()})
    print("visibility 50:", {k: round(x, 2) for k, x in visibility(CAM50).items()})
    print("wrote", hp, png)


if __name__ == "__main__":
    main()
