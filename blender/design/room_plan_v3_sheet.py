"""Room plan v3 sheet (2026-10-24): the owner's photo layout, approved; the numbers proposed.

Plain Python (no Blender), drawn to scale from blender/lib/plan_v3.py, the same numbers the v3
blockout (room_plan_v3_blockout.py) builds. Reuses the drawing helpers of the 2026-10-22 sheet
(room_plan_sheet.py) and the piano front of the piano sheet, as the v2 sheet does.

    python3 blender/design/room_plan_v3_sheet.py

Run the blockout first (it renders the v3-*.png stills into the same folder; the sheet places
them next to the owner's photo). Output: video-local/footage/2026-10-24-room-plan-v3/
room-plan-v3.{html,png}. Prints the clearance checks.
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import plan_v3 as P  # noqa: E402
from lib.piano_layout import lid_profile  # noqa: E402
import room_plan_sheet as S  # noqa: E402  (helpers: text, para, panel, dim, leader, View, guitar_outline)
import piano_design_sheet as PDS  # noqa: E402

C = P.C
out = S.out
add, text, para, panel, dim, leader, View = S.add, S.text, S.para, S.panel, S.dim, S.leader, S.View
INK, ACC, MUTED, PAPER, RULE = S.INK, S.ACC, S.MUTED, S.PAPER, S.RULE
OBJ_FILL, OBJ_LINE, SET_FILL = S.OBJ_FILL, S.OBJ_LINE, S.SET_FILL
DASH, DOT = S.DASH, S.DOT
RX, RY, H = P.RX, P.RY, P.H
WIN, DOOR, R = P.WINDOW_V3, P.DOOR, P.ROOM
OUT = os.path.join(C.FOOTAGE, "2026-10-24-room-plan-v3")
PHOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "moodboard", "local", "ai-desk-reference-1.jpg")
W_PX, H_PX = 2400, 5060
CP = P.CP
NUM = {k: i + 1 for i, (k, _, _) in enumerate(P.OBJECTS_V3)}
CHECKS = []
PN, BN, PIA, WG = P.PN, P.BN, P.PIANO_V3, P.WALL_GUITARS_V3
foot, rot, rect_w, circ = P.foot, P.rot, P.rect_w, P.circ


def c(m, nd=0):
    t = f"{m * 100:.{nd}f}"
    return t.rstrip("0").rstrip(".") if "." in t else t


def fill_of(cmp):
    return (OBJ_FILL, OBJ_LINE) if cmp["role"] != "set" else (SET_FILL, INK)


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
    v.rect(WIN["x0"] - WIN["ledge_horn"], WIN["x1"] + WIN["ledge_horn"], RY - P.LEDGE_IN, RY, "#d2ccc0", INK, 0.8)
    v.rect(-RX - ts, -RX, DOOR["y0"], DOOR["y1"], PAPER, PAPER, 0)
    v.rect(-RX, -RX + P.DOOR_LEAF, DOOR["y0"], DOOR["y0"] + DOOR["leaf_t"], "#fff", INK, 1.0)
    v.path(P.DOOR_SWING[1:], MUTED, 0.9, extra=DASH)


def frustum(v, cam, pos, col, ext, label, lab_off=(14, -8)):
    cx, cy = pos[0], pos[1]
    half = math.radians(cam.hfov / 2)
    for sgn in (-1, 1):
        ang = cam.yaw + sgn * half
        dx, dy = math.sin(ang), math.cos(ang)
        ts = []
        if abs(dx) > 1e-6:
            ts.append(((RX if dx > 0 else -RX) - cx) / dx)
        if abs(dy) > 1e-6:
            ts.append(((RY if dy > 0 else -RY) - cy) / dy)
        t = min(t for t in ts if t > 0)
        v.line((cx, cy), (cx + dx * t, cy + dy * t), col, 1.2, extra=ext)
    v.circle(cx, cy, 0.06, col, INK, 1)
    x, y = v.p(cx, cy)
    text(x + lab_off[0], y + lab_off[1], label, 13, col, weight=650)


def plan(px, py, pw, ph):
    panel(px, py, pw, ph, "1 · Floor plan",
          "top view, back wall at the top · cm · blue: interactive objects, grey: set dressing · dashed: above the desk or on a wall")
    s = 245
    v = View(px + 120 + RX * s, py + 110 + (RY + R["wall_back_t"]) * s, s)
    v.rect(-RX, 0.25, -RY, RY, "#eef2f7", "none", 0)
    v.rect(0.25, RX, -RY, RY, "#f4efe6", "none", 0)
    xa, ya = v.p(-1.45, -0.80)
    text(xa, ya, "AI LAB", 24, "#9db0c8", "middle", weight=700)
    xa, ya = v.p(1.35, -1.85)
    text(xa, ya, "MUSIC SIDE (the secret)", 20, "#c8b89d", "middle", weight=700)
    walls_plan(v)
    rg = P.RUG
    v.rect(rg["x"] - rg["w"] / 2, rg["x"] + rg["w"] / 2, rg["y"] - rg["d"] / 2, rg["y"] + rg["d"] / 2, "#ece4d8", MUTED, 0.9, extra=DASH)
    xr, yr = v.p(rg["x"], rg["y"] - 0.95)
    text(xr, yr, "rug 160 × 230", 12, MUTED, "middle")
    # chair: parked, its swing, pulled out
    v.circle(*P.SEAT, P.SWING_R, "none", "#7f9cc4", 1.0, extra=DASH)
    v.circle(*P.CHAIR_OUT, P.CHAIR_BASE_R, "none", "#7f9cc4", 1.0, extra=DOT)
    xz, yz = v.p(P.CHAIR_OUT[0] + 0.10, P.CHAIR_OUT[1] - 0.45)
    text(xz, yz, "chair pulled out", 11, "#46628a", "middle")
    # DJ standing place
    v.poly(P.DJ_ZONE, "#f3e6d6", "#b98a55", 1.0, extra=DASH + ' fill-opacity=".5"')
    # desk
    v.poly(P.DESK_L, "#ffffff", INK, 1.6)
    for x, y, yaw in P.DRAWERS:
        v.poly(rect_w(x, y, P.ALEX[0], P.ALEX[1], yaw), "none", MUTED, 0.9, extra=DOT)
    skip = {"desk", "led", "rug", "window", "piano", "bench", "rack", "mic", "chair", "pendant"}
    for cmp in sorted(P.COMPONENTS, key=lambda q: q["at"][2]):
        k = cmp["key"]
        if k in skip or k.startswith("alex") or k.startswith("guitar_0"):
            continue
        f, st = fill_of(cmp)
        high = cmp["at"][2] > 1.2 or cmp["shape"] == "slab"
        v.poly(foot(cmp), "none" if high else f, st, 1.0, extra=(DASH if high else ""))
    ch = CP["chair"]
    v.circle(ch["at"][0], ch["at"][1], P.CHAIR_BASE_R, "#eceef1", INK, 1.0)
    v.poly(rect_w(ch["at"][0], ch["at"][1], 0.50, 0.46, ch["yaw"]), "#d9dce1", INK, 0.9)
    xc, yc = v.p(*P.SEAT)
    text(xc, yc + 4, "Aeron", 12, INK, "middle")
    v.circle(P.LIGHT_V3["x"], P.LIGHT_V3["y"], 0.20, "none", OBJ_LINE, 1.1, extra=DASH)
    arm = P.mic_arm()
    v.path([p[:2] for p in arm], OBJ_LINE, 1.6)
    v.line(P.CAM_ARM_FROM[:2], P.CAM_AT[:2], INK, 1.2)
    # music side
    v.poly(P.PIANO_FOOT, "#2a2a2c", INK, 1.2)
    xp, yp = v.p(PIA["x"] - 0.30, PIA["y"])
    text(xp, yp, "Piano", 15, "#fff", "middle", weight=650, rot=-90)
    for i in range(3):
        y = WG["y"][i]
        v.rect(RX - 0.125, RX - 0.075, y - WG["width"][i] / 2, y + WG["width"][i] / 2, OBJ_FILL, OBJ_LINE, 1.1, extra=DASH)
        xg, yg = v.p(RX - 0.21, y)
        text(xg, yg + 4, f"0{i + 1}", 12, "#cfe0f5", "middle", weight=700)
    v.poly(P.bench_foot(), "#5a5a5e", INK, 1.0)
    v.poly(P.bench_foot(True), "none", MUTED, 0.9, extra=DASH)
    rk = P.RACK_V3
    v.poly(P.RACK_FOOT, OBJ_FILL, OBJ_LINE, 1.2)
    slots = [(i - (rk["slots"] - 1) / 2) * rk["pitch"] for i in range(rk["slots"])]
    for i, sl in enumerate(slots):
        a = [(rk["x"] + dx, rk["y"] + dy) for dx, dy in (rot(-0.30, sl, rk["yaw"]), rot(0.25, sl, rk["yaw"]))]
        v.line(a[0], a[1], OBJ_LINE, 2.2)
    # cameras
    cm_ = P.cams()
    frustum(v, cm_["hero"], P.HERO_V3["pos"], ACC, DASH, "HERO_V3 (16:9)", (14, 18))
    frustum(v, cm_["portrait"], P.HERO_V3["pos"], "#d08a62", DOT, "")
    frustum(v, cm_["intro"], P.INTRO["pos"], "#2f7d5b", DASH, "INTRO", (-70, 22))
    frustum(v, cm_["about"], P.ABOUT["pos"], "#7a4fb0", DASH, "ABOUT", (-80, 26))
    # callouts: a letter by each item, the key under the plan
    labs = [
        ("studio_display", (-1.25, 1.25), "screens on one pole: 27 in (posts) over the 34 in curved (dashboard)"),
        ("a7v_2", (-1.25, 1.62), f"A7V white on desk poles beside the top screen, tweeters {c(P.TWEETER_Z)}, toed in {abs(P.SPEAKERS[0]['yaw'] - 90):.0f}°"),
        ("keylight_1", (-1.25, 0.20), "key lights on poles at both ends; the camera on a flex arm off pole 1"),
        ("mic", (-1.25, 0.55), "MV7+ on the PSA1+, parked left of the keyboard"),
        ("shelf", (-2.40, 1.60), f"floating shelf {c(P.SHELF['y1'] - P.SHELF['y0'])} × 25 at {c(P.SHELF['z'])}: three frames, trailing plants"),
        ("pc", (-1.05, 1.32), "training rig (PC) in the inner corner, front glass to the room"),
        ("laptop", (-0.20, 1.40), "MacBook on the mStand, turned to the chair"),
        ("pegboard", (-0.55, 2.55), "pegboard (backlit), neon above, light panels by the corner"),
        ("plant", (0.75, 2.55), f"window {c(WIN['x1'] - WIN['x0'])} × {c(WIN['head'] - WIN['sill'])}, sill {c(WIN['sill'])}; plant on the ledge"),
        ("rack", (1.20, 1.20), "rack 04 05 06 in the back-right corner"),
        ("guitar_02", (1.20, 0.20), "wall guitars 01 02 03 over the lid (lid stops at 60°)"),
        ("dj", (1.30, -1.35), "DJ stand 70 × 40: the decks and the lightstick"),
    ]
    for i, (key, (lx, ly), s_) in enumerate(labs):
        cc = CP[key]
        x0, y0 = v.p(cc["at"][0], cc["at"][1])
        x1, y1 = v.p(lx, ly)
        add(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{MUTED}" stroke-width=".9"/>'
            f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="2.2" fill="{MUTED}"/>'
            f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="10" fill="#fff" stroke="{ACC}" stroke-width="1.2"/>')
        text(x1, y1 + 4.5, "abcdefghijklmn"[i], 13, ACC, "middle", weight=700)
        kx = px + 24 + (i % 2) * (pw / 2)
        ky = py + ph - 100 + (i // 2) * 17
        text(kx, ky, f"{'abcdefghijklmn'[i]}  {s_}", 12.5, INK)
    x0, y0 = v.p(-RX + 0.4, DOOR["y0"] + 0.4)
    text(x0 + 6, y0, "door 90 × 210", 12, MUTED)
    # dimensions
    yt = v.p(0, -RY - 0.15)[1] + 30
    xs = sorted({-RX, P.MAIN["x1"], P.RET["x1"], WIN["x0"], WIN["x1"], RX})
    for a, b in zip(xs, xs[1:]):
        dim(v.p(a, 0)[0], yt, v.p(b, 0)[0], yt, c(b - a), size=12)
    dim(v.p(-RX, 0)[0], yt + 34, v.p(RX, 0)[0], yt + 34, "440 inside", size=13)
    xr = v.p(RX + 0.15, 0)[0] + 34
    dim(xr, v.p(0, RY)[1], xr, v.p(0, -RY)[1], "420 inside", side=-1, size=13)
    xl = v.p(-RX - 0.15, 0)[0] - 26
    dim(xl, v.p(0, RY)[1], xl, v.p(0, P.MAIN["y0"])[1], f"main run {c(P.MAIN_LEN)}", size=12)
    dim(xl, v.p(0, P.MAIN["y0"])[1], xl, v.p(0, DOOR["y1"])[1], c(P.MAIN["y0"] - DOOR["y1"]), size=12)
    yd = v.p(0, P.RET["y0"])[1] + 22
    dim(v.p(P.MAIN["x1"], 0)[0], yd, v.p(P.RET["x1"], 0)[0], yd, f"return {c(P.RET_LEN)} beyond the run, 60 deep", side=-1, size=11)
    yd = v.p(0, P.MAIN["y0"])[1] + 22
    dim(v.p(-RX, 0)[0], yd, v.p(P.MAIN["x1"], 0)[0], yd, "80", side=-1, size=12)
    xpz = v.p(RX, 0)[0] + 10
    py0, py1 = max(y for _, y in P.PIANO_FOOT), min(y for _, y in P.PIANO_FOOT)
    dim(xpz, v.p(0, RY)[1], xpz, v.p(0, py0)[1], c(RY - py0), side=-1, size=11)
    dim(xpz, v.p(0, py0)[1], xpz, v.p(0, py1)[1], "piano 153", side=-1, size=11)
    # walkways
    g = {n: val for n, val, _, _ in CHECKS}
    for (wx, wy), key in (((0.35, 0.55), "walkway: chair pulled out to the piano bench, played"),
                          ((-1.25, -1.10), "walkway: door swing to the desk's outer end"),
                          ((1.30, -0.62), "walkway: the DJ's standing place to the bench, played"),
                          ((0.55, 1.55), "walkway to the window: the return's end to the rack")):
        xw, yw = v.p(wx, wy)
        text(xw, yw, f"{c(g[key])} clear", 12, ACC, "middle", weight=650)


# ---------------------------------------------------------------------------
# 2. elevations
# ---------------------------------------------------------------------------
def wall_frame(v, length, title, sub):
    v.rect(0, length, 0, H, "#fbfaf6", INK, 1.4)
    x, y = v.p(0, H)
    text(x, y - 34, title, 16, INK, weight=650)
    text(x, y - 16, sub, 12, MUTED)


def ext(cmp, axis):
    vals = [p[0] if axis == "x" else p[1] for p in foot(cmp)]
    return min(vals), max(vals)


def erect(v, U, cmp, axis, dashed=False, label=None):
    u0, u1 = ext(cmp, axis)
    z0, z1 = P.zrange(cmp)
    f, st = fill_of(cmp)
    if cmp.get("glow") and cmp["shape"] == "slab":
        f = "#eaf2ff"
    a, b = sorted((U(u0), U(u1)))
    v.rect(a, b, z0, z1, "none" if dashed else f, st, 1.0, extra=DASH if dashed else "")
    if label:
        xt, yt = v.p((a + b) / 2, (z0 + z1) / 2)
        text(xt, yt + 4, label, 10, OBJ_LINE if cmp["role"] != "set" else INK, "middle", weight=600)


def alex_front(v, u0, u1):
    v.rect(u0, u1, 0, P.ALEX[2], "#fff", INK, 1.0)
    for j in range(1, 5):
        v.line((u0, P.ALEX[2] * j / 5), (u1, P.ALEX[2] * j / 5), MUTED, 0.6)


def elevations(px, py, pw, ph):
    panel(px, py, pw, ph, "2 · Wall elevations",
          "seen from inside the room · cm · solid: on or against that wall · dashed: further out in the room")
    s = 165
    base = py + 110 + H * s
    # ---- left wall: facing -X, front corner at the left, u = y + RY
    vl = View(px + 40, base, s)
    wall_frame(vl, R["depth"], "Left wall: the main run", "door, then the desk; screens, speakers, key lights, shelf")
    U = lambda y: y + RY  # noqa: E731
    vl.rect(U(DOOR["y0"]), U(DOOR["y1"]), 0, DOOR["head"], "#f1ede5", INK, 1.1)
    sw = P.SWITCH
    vl.rect(U(sw["y"]) - sw["w"] / 2, U(sw["y"]) + sw["w"] / 2, sw["z"] - sw["h"] / 2, sw["z"] + sw["h"] / 2, SET_FILL, INK, 1)
    vl.rect(U(P.MAIN["y0"]), U(RY), P.TOP - P.TOP_T, P.TOP, "#fff", INK, 1.3)
    vl.line((U(P.MAIN["y0"]), P.TOP - P.TOP_T - 0.006), (U(P.RET["y0"]), P.TOP - P.TOP_T - 0.006), "#7fb6ff", 2.2)
    a1 = CP["alex_1"]
    alex_front(vl, *sorted(U(q) for q in ext(a1, "y")))
    for key in ("pole", "ultrawide", "studio_display", "screenbar", "spk_pole_1", "spk_pole_2", "spk_plate_1", "spk_plate_2",
                "a7v_1", "a7v_2", "interface", "streamdeck", "keyboard", "snake_plant", "shelf", "frame_1", "frame_2", "frame_3",
                "vine_pot_1", "vine_pot_2", "vine_1", "vine_2"):
        erect(vl, U, CP[key], "y", label={"ultrawide": "dashboard 34 in", "studio_display": "posts 27 in"}.get(key))
    for key in ("keylight_pole_1", "keylight_pole_2", "keylight_1", "keylight_2", "camera", "mic", "pc"):
        erect(vl, U, CP[key], "y", dashed=True)
    xq = vl.p(U(P.MAIN["y0"]) - 0.08, 0)[0]
    dim(xq, vl.p(0, 0)[1], xq, vl.p(0, P.TOP)[1], "73.5", side=-1, size=11)
    sd = CP["studio_display"]
    xq = vl.p(U(RY) - 0.06, 0)[0]
    dim(xq, vl.p(0, P.TOP)[1], xq, vl.p(0, P.UW["z"])[1], c(P.UW["z"] - P.TOP), side=-1, size=10)
    dim(xq, vl.p(0, P.SD["z"])[1], xq, vl.p(0, P.SD["z"] + P.SD["h"])[1], "36", side=-1, size=10)
    xq = vl.p(U(RY) - 0.32, 0)[0]
    dim(xq, vl.p(0, P.TOP)[1], xq, vl.p(0, P.TWEETER_Z)[1], f"tweeter {c(P.TWEETER_Z)}", size=10)
    yq = vl.p(0, P.SHELF["z"] + 0.52)[1]
    dim(vl.p(U(P.SHELF["y0"]), 0)[0], yq, vl.p(U(P.SHELF["y1"]), 0)[0], yq, f"shelf {c(P.SHELF['y1'] - P.SHELF['y0'])} at {c(P.SHELF['z'])}", size=11)
    yq = vl.p(0, 0)[1] + 18
    dim(vl.p(U(P.MAIN["y0"]), 0)[0], yq, vl.p(U(RY), 0)[0], yq, f"main run {c(P.MAIN_LEN)}", side=-1, size=11)
    dim(vl.p(U(DOOR["y1"]), 0)[0], yq, vl.p(U(P.MAIN["y0"]), 0)[0], yq, c(P.MAIN["y0"] - DOOR["y1"]), side=-1, size=11)
    xk = vl.p(U(CP["keylight_1"]["at"][1]), P.KL_Z + 0.30)
    text(xk[0], xk[1], f"key lights {c(P.KL_Z)} to {c(P.KL_Z + P.KL_PANEL[2])}", 10, MUTED, "middle")
    # ---- back wall: u = x + RX
    x2 = px + 40 + R["depth"] * s + 60
    vb = View(x2, base, s)
    wall_frame(vb, R["width"], "Back wall: the return and the window", "PC in the corner, the laptop by the window; pegboard, neon, panels")
    U2 = lambda x: x + RX  # noqa: E731
    vb.rect(U2(WIN["x0"]), U2(WIN["x1"]), WIN["sill"], WIN["head"], "#cfdcf2", INK, 1.2)
    nb = max(6, round((WIN["head"] - WIN["sill"]) / 0.175))
    for i in range(1, nb):
        z = WIN["sill"] + (WIN["head"] - WIN["sill"]) * i / nb
        vb.line((U2(WIN["x0"]), z), (U2(WIN["x1"]), z), "#7d8696", 0.7)
    vb.line((U2((WIN["x0"] + WIN["x1"]) / 2), WIN["sill"]), (U2((WIN["x0"] + WIN["x1"]) / 2), WIN["head"]), INK, 0.8)
    vb.rect(U2(WIN["x0"] - WIN["ledge_horn"]), U2(WIN["x1"] + WIN["ledge_horn"]), WIN["sill"] - WIN["ledge_t"], WIN["sill"], "#d2ccc0", INK, 0.8)
    vb.rect(U2(-RX), U2(P.RET["x1"]), P.TOP - P.TOP_T, P.TOP, "#fff", INK, 1.3)
    vb.line((U2(P.MAIN["x1"]), P.TOP - P.TOP_T - 0.006), (U2(P.RET["x1"]), P.TOP - P.TOP_T - 0.006), "#7fb6ff", 2.2)
    for k in ("alex_2", "alex_3"):
        alex_front(vb, *sorted(U2(q) for q in ext(CP[k], "x")))
    vb.rect(U2(-RX + 0.21), U2(P.MAIN["x1"] - 0.01), 0, P.ALEX[2], "none", MUTED, 0.9, extra=DASH)    # drawer unit 1, end-on
    for key, lab in (("pc", "rig"), ("desk_plant", None), ("mstand", None), ("laptop", "laptop"), ("pegboard", "pegboard"),
                     ("headphones", None), ("neon", "neon: our words"), ("nanoleaf", "panels"), ("plant", None),
                     ("a7v_2", None), ("spk_pole_2", None), ("frame_3", None), ("vine_2", None), ("vine_pot_2", None)):
        erect(vb, U2, CP[key], "x", label=lab)
    for key in ("keylight_2", "keylight_pole_2", "rack"):
        erect(vb, U2, CP[key], "x", dashed=True, label="rack" if key == "rack" else None)
    px0 = min(x for x, _ in P.PIANO_FOOT)
    vb.rect(U2(px0), U2(RX - 0.05), 0, PN["case_top"] + PN["lid_t"], "none", MUTED, 0.9, extra=DASH)
    xq = vb.p(U2(WIN["x1"]) + 0.10, 0)[0]
    dim(xq, vb.p(0, 0)[1], xq, vb.p(0, WIN["sill"])[1], c(WIN["sill"]), side=-1, size=11)
    dim(xq, vb.p(0, WIN["sill"])[1], xq, vb.p(0, WIN["head"])[1], c(WIN["head"] - WIN["sill"]), side=-1, size=11)
    yq = vb.p(0, WIN["head"] + 0.10)[1]
    dim(vb.p(U2(WIN["x0"]), 0)[0], yq, vb.p(U2(WIN["x1"]), 0)[0], yq, c(WIN["x1"] - WIN["x0"]), size=11)
    yq = vb.p(0, 0)[1] + 18
    dim(vb.p(U2(-RX), 0)[0], yq, vb.p(U2(P.RET["x1"]), 0)[0], yq, f"desk {c(P.RET['x1'] + RX)} from the corner", side=-1, size=11)
    dim(vb.p(U2(P.RET["x1"]), 0)[0], yq, vb.p(U2(WIN["x0"]), 0)[0], yq, "8", side=-1, size=11)
    pg = CP["pegboard"]
    xq = vb.p(U2(P.PEG["x"] - P.PEG["w"] / 2) - 0.05, 0)[0]
    dim(xq, vb.p(0, P.TOP + 0.39)[1], xq, vb.p(0, pg["at"][2])[1], c(pg["at"][2] - P.TOP - 0.39), size=10)
    # ---- right wall: facing +X, back corner at the left, u = RY - y
    x3 = x2 + R["width"] * s + 60
    vr = View(x3, base, s)
    wall_frame(vr, R["depth"], "Right wall: the music side", f"piano, top lid stops at {P.PIANO_LID_MAX_DEG}°; guitars over it; rack; decks")
    U3 = lambda y: RY - y  # noqa: E731
    pv = PDS.View(vr.ox + U3(PIA["y"]) * s, base, s / 1000)
    PDS.front(pv, dict(PDS.TECH, sw=0.7), detail=False)
    hw = PN["width"] / 2 + PN["lid_over_side"]
    l60 = max(z for _, z in lid_profile(P.PIANO_LID_MAX_DEG)[0])
    vr.rect(U3(PIA["y"]) - hw, U3(PIA["y"]) + hw, PN["case_top"] + PN["lid_t"], l60, "#f3e6d6", "#b98a55", 1.0,
            extra=DASH + ' fill-opacity=".7"')
    xo, yo = vr.p(U3(PIA["y"]), l60 - 0.07)
    text(xo, yo, f"lid at {P.PIANO_LID_MAX_DEG}°: reaches {c(P.LID_REACH, 1)} in the bodies' plane", 10, "#8a5a25", "middle")
    cols = ["#3a3a3c", "#f8f6f0", "#b8474b"]
    for i, y in enumerate(WG["y"]):
        L_, W_ = WG["length"][i], WG["width"][i]
        if i == 2:
            body, neck, head = S.guitar_outline(L_ * 0.92, W_)
            for du in (-0.085, 0.085):
                vr.poly([(U3(y) + u + du, WG["bottom"] + vv) for u, vv in neck], "#c9b59c", OBJ_LINE, 0.9)
                vr.poly([(U3(y) + u + du, WG["bottom"] + vv * L_ / (L_ * 0.92)) for u, vv in head], "#8c3a3c", OBJ_LINE, 0.9)
            vr.poly([(U3(y) + u, WG["bottom"] + vv) for u, vv in body], cols[i], OBJ_LINE, 1.0)
        else:
            body, neck, head = S.guitar_outline(L_, W_, archtop=(i == 0))
            for part_, col in ((neck, "#c9b59c"), (head, "#8c7a66"), (body, cols[i])):
                vr.poly([(U3(y) + u, WG["bottom"] + vv) for u, vv in part_], col, OBJ_LINE, 1.0)
        xg, yg = vr.p(U3(y), WG["bottom"] + 0.20)
        text(xg, yg, f"0{i + 1}", 13, "#fff" if i != 1 else OBJ_LINE, "middle", weight=700)
        xt, yt = vr.p(U3(y), WG["bottom"] + L_ + 0.04)
        text(xt, yt, f"top {c(WG['bottom'] + L_)}", 10, ACC, "middle")
    bys = [p[1] for p in P.bench_foot()]
    vr.rect(U3(max(bys)), U3(min(bys)), 0, BN["h"], "none", MUTED, 0.9, extra=DASH)
    rfy = [p[1] for p in P.RACK_FOOT]
    vr.rect(U3(max(rfy)), U3(min(rfy)), 0, 1.06, "none", OBJ_LINE, 0.9, extra=DASH)
    xk, yk = vr.p(U3((max(rfy) + min(rfy)) / 2), 1.10)
    text(xk, yk, "rack 04 to 06", 11, OBJ_LINE, "middle")
    for key, lab in (("dj_stand", None), ("dj", "decks"), ("lightstick", None)):
        erect(vr, U3, CP[key], "y", label=lab)
    xq = vr.p(U3(WG["y"][2]) + WG["width"][2] / 2 + 0.10, 0)[0]
    dim(xq, vr.p(0, 0)[1], xq, vr.p(0, P.LID_REACH)[1], c(P.LID_REACH, 1), side=-1, size=11)
    dim(xq, vr.p(0, P.LID_REACH)[1], xq, vr.p(0, WG["bottom"])[1], c(WG["bottom"] - P.LID_REACH, 1), side=-1, size=11)
    dim(xq, vr.p(0, WG["bottom"])[1], xq, vr.p(0, WG["bottom"] + WG["length"][2])[1], c(WG["length"][2]), side=-1, size=11)
    ygp = vr.p(0, WG["bottom"] - 0.12)[1]
    for i in range(2):
        a = U3(WG["y"][i]) + WG["width"][i] / 2
        b = U3(WG["y"][i + 1]) - WG["width"][i + 1] / 2
        dim(vr.p(a, 0)[0], ygp, vr.p(b, 0)[0], ygp, c(b - a), size=10)
    xq = vr.p(U3(P.DJ_STAND["y"]) + 0.42, 0)[0]
    dim(xq, vr.p(0, 0)[1], xq, vr.p(0, P.DJ_STAND["top"])[1], c(P.DJ_STAND["top"]), side=-1, size=11)


# ---------------------------------------------------------------------------
# 3. the hero next to the owner's photo; 4. intro and about
# ---------------------------------------------------------------------------
def marker_point(k):
    main = {"obj_monitor": "studio_display", "obj_rig": "pc", "obj_mic": "mic", "obj_frames": "frame_2",
            "obj_studio": "a7v_2", "obj_piano": "piano", "obj_guitars": "guitar_02", "obj_light": "pendant",
            "obj_window": "window", "obj_plant": "plant"}[k]
    cc = CP[main]
    x, y, z = cc["at"]
    if main == "piano":
        return (PIA["x"] - 0.45, PIA["y"], 1.0)
    if main == "window":
        return ((WIN["x0"] + WIN["x1"]) / 2, RY, 1.95)
    if main == "mic":
        return P.MIC["capsule"]
    if main == "guitar_02":
        return (x, y, z + 0.25)
    if main == "pc":
        return (x, y, z + 0.30)
    return (x, y, z + cc["size"][2] / 2)


def markers(cam, x0, y0, w, h):
    for k, _, _ in P.OBJECTS_V3:
        q = cam.cam(marker_point(k))
        if q[2] <= 0.05:
            continue
        a, b = cam.ndc(q)
        if abs(a) > 0.97 or abs(b) > 0.97:
            continue
        px, py = x0 + (a + 1) / 2 * w, y0 + (1 - b) / 2 * h
        add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="13" fill="{OBJ_LINE}" stroke="#fff" stroke-width="2"/>')
        text(px, py + 5, str(NUM[k]), 14, "#fff", "middle", weight=700)


def img(href, x, y, w, h, label=None, frame=False):
    add(f'<image href="{href}" x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" preserveAspectRatio="xMidYMid slice"/>')
    if frame:
        add(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="16" fill="none" stroke="{INK}" stroke-width="3"/>')
    if label:
        add(f'<rect x="{x + 8:.0f}" y="{y + h - 36:.0f}" width="{len(label) * 7.6 + 16:.0f}" height="26" rx="4" fill="#000" fill-opacity=".55"/>')
        text(x + 16, y + h - 18, label, 13, "#fff", weight=600)


def hero_panel(px, py, pw, ph):
    panel(px, py, pw, ph, "3 · HERO_V3 next to the owner's photo",
          "left: the photo (docs/moodboard/local/ai-desk-reference-1.jpg) · right: the v3 blockout from HERO_V3, 4:5, EEVEE boxes")
    cm_ = P.cams()
    w = (pw - 54) / 2
    h = w * 5 / 4
    x0, y0 = px + 18, py + 76
    img(os.path.relpath(PHOTO, OUT), x0, y0, w, h, "the owner's photo")
    img("v3-hero-portrait.png", x0 + w + 18, y0, w, h, f"plan v3, HERO_V3 portrait, {P.HERO_V3['portrait_vfov']}° vertical")
    markers(cm_["portrait"], x0 + w + 18, y0, w, h)
    y1 = y0 + h + 18
    w2 = w * 1.25
    h2 = w2 * 9 / 16
    img("v3-hero.png", x0, y1, w2, h2, f"HERO_V3 desktop 16:9, {P.HERO_V3['vfov']}° vertical")
    markers(cm_["hero"], x0, y1, w2, h2)
    pw3 = h2 * 390 / 844
    img("v3-phone.png", x0 + w2 + 18, y1, pw3, h2, None, frame=True)
    markers(cm_["phone"], x0 + w2 + 18, y1, pw3, h2)
    text(x0 + w2 + 18 + pw3 / 2, y1 + h2 + 18, "phone 390 × 844", 12, MUTED, "middle")
    hv = P.HERO_V3
    para(x0 + w2 + pw3 + 50, y1 + 16, [
        ("HERO_V3", INK, 650),
        f"camera x {c(hv['pos'][0])}, y {c(hv['pos'][1])}, eye {c(hv['pos'][2])}:",
        "standing in the room, looking into",
        "the back-left corner, as the photo.",
        f"Looks {math.degrees(math.atan2(hv['pos'][2] - hv['target'][2], math.dist(hv['pos'][:2], hv['target'][:2]))):.0f}° down.",
        f"Across: desktop {cm_['hero'].hfov:.0f}°,",
        f"portrait {cm_['portrait'].hfov:.0f}°, phone {cm_['phone'].hfov:.0f}°.",
        "",
        ("The music side in frame", INK, 650),
        f"desktop {P.share(cm_['hero'], P.MUSIC_KEYS) * 100:.0f} %, portrait {P.share(cm_['portrait'], P.MUSIC_KEYS) * 100:.0f} %,",
        f"phone {P.share(cm_['phone'], P.MUSIC_KEYS) * 100:.0f} %: it stays secret.",
        "",
        ("Not the photo exactly", INK, 650),
        "Our room is wider than the",
        "photo's: the same corner shows",
        "more wall. The window is a strip",
        "at the right edge on desktop.",
    ], 13.5, MUTED)


def views_panel(px, py, pw, ph):
    panel(px, py, pw, ph, "4 · INTRO and ABOUT",
          "the site opens on INTRO; a click pulls the camera back into the room and turns it left to HERO_V3; About turns it right")
    cm_ = P.cams()
    w = (pw - 54) / 2
    h = w * 9 / 16
    x0, y0 = px + 18, py + 76
    img("v3-intro.png", x0, y0, w, h, f"INTRO: out of the window, {P.INTRO['vfov']}° vertical")
    markers(cm_["intro"], x0, y0, w, h)
    img("v3-about.png", x0 + w + 18, y0, w, h, f"ABOUT: the music side, {P.ABOUT['vfov']}° vertical")
    markers(cm_["about"], x0 + w + 18, y0, w, h)
    para(x0, y0 + h + 30, [
        f"INTRO: camera at x {c(P.INTRO['pos'][0])}, y {c(P.INTRO['pos'][1])}, eye {c(P.INTRO['pos'][2])}, a metre from the glass, a touch up. "
        "The grill and the frame edge the shot; the plant sits in the corner. The sky and the city are stand-ins (Pune's time and weather later).",
        f"ABOUT: camera at x {c(P.ABOUT['pos'][0])}, y {c(P.ABOUT['pos'][1])}, eye {c(P.ABOUT['pos'][2])}: the piano with the three guitars over it, "
        f"the rack in the corner by the window, the decks on their stand. Music side in frame: {P.share(cm_['about'], P.MUSIC_KEYS) * 100:.0f} %.",
    ], 13.5, MUTED, lh=22)


# ---------------------------------------------------------------------------
# 5. legend, 6. numbers and checks, 7. for the owner
# ---------------------------------------------------------------------------
GROUP = {"spk_pole_1": "Speaker poles (2)", "spk_plate_1": None, "spk_pole_2": None, "spk_plate_2": None,
         "a7v_1": "Studio monitors (2)", "a7v_2": None, "keylight_1": "Key lights (2)", "keylight_2": None,
         "keylight_pole_1": "Key light poles (2)", "keylight_pole_2": None, "frame_1": "Frames (3)", "frame_2": None,
         "frame_3": None, "alex_1": "Drawer units (3)", "alex_2": None, "alex_3": None, "vine_pot_1": "Trailing plants (2)",
         "vine_pot_2": None, "vine_1": None, "vine_2": None, "guitar_01": "Wall guitars 01 to 03", "guitar_02": None,
         "guitar_03": None}


def size_str(cmp):
    w, d, h = cmp["size"]
    k = cmp["key"]
    if k == "desk":
        return f"{c(P.MAIN_LEN)}×80 + {c(P.RET_LEN)}×60, top 3.5"
    if k == "led":
        return "both front edges"
    if k == "guitar_01":
        return "see right wall"
    if k == "window":
        return f"{c(w)} × {c(h)}, sill {c(WIN['sill'])}"
    if cmp["shape"] == "cyl":
        return f"⌀{c(w, 1)} × {c(h, 1)}"
    f = lambda q: c(q, 1)  # noqa: E731
    return f"{f(w)} × {f(d)} × {f(h)}"


def legend(px, py, pw, ph):
    panel(px, py, pw, ph, "5 · Legend: every component",
          "w × d × h in cm, the makers' outside sizes (SOURCES.md in docs/moodboard/local/ai-lab/); ? = re-check · "
          "no logos or names on any model; the names are for reference only")
    rows = [q for q in P.COMPONENTS if GROUP.get(q["key"], q["label"]) is not None]
    col_w = (pw - 36) / 2
    per = (len(rows) + 1) // 2
    for ci in range(2):
        x = px + 18 + ci * col_w
        y = py + 96
        for t_, dx, anc in (("component", 0, "start"), ("real model", 168, "start"), ("size", 480, "start"), ("role", col_w - 14, "end")):
            text(x + dx, y, t_, 12, MUTED, anc, weight=600)
        y += 8
        add(f'<line x1="{x}" y1="{y}" x2="{x + col_w - 14}" y2="{y}" stroke="{RULE}"/>')
        y += 18
        for q in rows[ci * per:(ci + 1) * per]:
            lab = GROUP.get(q["key"], q["label"])
            model = q["model"] if q["key"] != "guitar_01" else "Lucille 107 × 41 · Strat 97.7 × 32.3 · double-neck 110 × 43"
            unsure = "UNSURE" in q["note"] or q["key"] in ("streamdeck", "ultrawide", "guitar_01", "chair", "neon")
            text(x, y, lab[:26], 12.5, INK)
            text(x + 168, y, model if len(model) <= 52 else model[:50] + "…", 11.5, MUTED)
            text(x + 480, y, size_str(q) + (" ?" if unsure else ""), 12, INK)
            if q["role"] != "set":
                text(x + col_w - 14, y, f"{NUM[q['role']]} {q['role']}", 12, OBJ_LINE, "end", weight=650)
            else:
                text(x + col_w - 14, y, "set dressing", 12, MUTED, "end")
            y += 19.5


def objects_panel(px, py, pw, ph):
    panel(px, py, pw, ph, "6 · The ten interactive objects", "unchanged ten; new places")
    y = py + 96
    for k, lab, what in P.OBJECTS_V3:
        add(f'<circle cx="{px + 30}" cy="{y - 5}" r="10" fill="{OBJ_LINE}"/>')
        text(px + 30, y - 1, str(NUM[k]), 12, "#fff", "middle", weight=700)
        text(px + 50, y, lab, 13.5, INK, weight=600)
        text(px + 50, y + 17, f"{k} · {what}", 12, MUTED)
        y += 40
    para(px + 18, y + 6, [
        "obj_studio now has two halves: the speakers and the",
        "Apollo in the lab (volume, pan), the decks and the",
        "lightstick by the piano (the secret). One root, two",
        "close-ups; see the owner's list.",
    ], 12.5, MUTED)


def numbers_panel(px, py, pw, ph):
    panel(px, py, pw, ph, "7 · Numbers and checks", "blender/lib/plan_v3.py, run_checks() · every footprint, every pair, the walls, the door, the window")
    sp = P.SPEAKERS[0]
    lines = [
        ("Desk", INK, 650),
        f"Main run {c(P.MAIN_LEN)} × 80 on the left wall, y {c(P.MAIN['y0'])} to {c(RY)}.",
        f"Return {c(P.RET_LEN)} × 60 beyond it on the back wall, to x {c(P.RET['x1'])},",
        f"8 cm short of the window. Top at 73.5, 3.5 thick, no pucks.",
        "ALEX 1 under the run's outer end, faces the room; ALEX 2",
        "and 3 under the return, by the corner and at its end.",
        "",
        ("Main run", INK, 650),
        f"Stack centre line y {c(P.YM)}, between the key light poles.",
        f"34 in: bottom {c(P.UW['z'])}, top {c(P.UW['z'] + P.UW['h'], 1)}; 27 in: {c(P.SD['z'], 1)} to {c(P.SD['z'] + P.SD['h'], 1)}.",
        f"A7V centres {c(2 * P.SPK_DY)} apart, beside the 27 in, on desk",
        f"poles; tweeters at {c(P.TWEETER_Z)}: standing ear (155). Toed in {abs(sp['yaw'] - 90):.0f}°.",
        f"Key lights {c(P.KL_Z)} to {c(P.KL_Z + P.KL_PANEL[2])}, poles {c(P.KL_POLE_TOP - P.TOP)} above the top.",
        f"Shelf {c(P.SHELF['y1'] - P.SHELF['y0'])} × 25 at {c(P.SHELF['z'])}; vines to {c(P.SHELF['z'] - P.SHELF['t'] - P.VINE_LEN)}.",
        f"Mic parked at {c(P.MIC['capsule'][2])}, reach {c(math.dist(P.MIC['clamp'], P.MIC['capsule'][:2]))} of 94.",
        f"Aeron parked {c(P.SEAT[0] - P.MAIN['x1'])} from the edge; swing 40.",
        "",
        ("Return and window", INK, 650),
        f"PC x {c(P.PC_AT[0] - P.PC_SIZE[0] / 2)} to {c(P.PC_AT[0] + P.PC_SIZE[0] / 2)}, 48 deep, front to the room.",
        f"Laptop on the mStand at x {c(P.LAPTOP_AT[0])}, turned {abs(P.LAPTOP_YAW):.0f}° to the chair.",
        f"Pegboard {c(P.PEG['z'])} to {c(P.PEG['z'] + P.PEG['h'])}, neon above, panels by the corner.",
        f"Window x {c(WIN['x0'])} to {c(WIN['x1'])}: {c(WIN['x1'] - WIN['x0'])} × {c(WIN['head'] - WIN['sill'])}, sill {c(WIN['sill'])}, ledge 20 in.",
        "",
        ("Music side", INK, 650),
        f"Piano y {c(PIA['y'])} (centre), 5 cm off the right wall.",
        f"Lid at {P.PIANO_LID_MAX_DEG}° reaches {c(P.LID_REACH, 1)}; guitar bottoms {c(WG['bottom'])}.",
        f"Rack at x {c(P.RACK_V3['x'])}, y {c(P.RACK_V3['y'])}, yaw {P.RACK_V3['yaw']}°.",
        f"DJ stand 70 × 40, top {c(P.DJ_STAND['top'])}, y {c(P.DJ_STAND['y'])}.",
        f"Rug 160 × 230 and pendant at x {c(P.RUG['x'])}, y {c(P.RUG['y'])}.",
    ]
    para(px + 18, py + 92, lines, 13.5)
    y = py + 92
    xc = px + 540
    text(xc, y, f"Checks (need in brackets, cm): {sum(1 for q in CHECKS if q[3])} of {len(CHECKS)} pass", 13.5, INK, weight=650)
    y += 20
    for name, g, need, ok in CHECKS:
        tight = ok and need > 0 and g - need < 0.02
        text(xc, y, f"{'ok' if ok else 'CLASH'}  {name}: {c(g, 1)} ({c(need)}){'  tight' if tight else ''}", 10.5,
             "#a33" if not ok else ("#8a5a25" if tight else INK))
        y += 14.0


def owner_panel(px, py, pw, ph):
    panel(px, py, pw, ph, "8 · For the owner", "what to look at, and the choices left")
    para(px + 18, py + 96, [
        ("1. Speakers at standing ear (tweeters 154).", INK, 650),
        "   As the photo: beside the top screen. Seated, they", "   would sit beside the 34 in at 118 and crowd the camera.",
        ("2. The window moved 10 cm right of the quick blockout.", INK, 650),
        "   The return is 102 beyond the run (172 from the", "   wall): the PC, a plant and the laptop fit with air.",
        ("3. obj_studio is split across the room.", INK, 650),
        "   Speakers and Apollo in the lab; decks and lightstick", "   by the piano. Keep, or move the decks' part to", "   obj_piano's close-up?",
        ("4. The PC's front glass faces the room, its side glass", INK, 650),
        ("   the window, so the hero sees both.", INK, 650),
        ("5. Snake plant on the desk's outer end, under the", INK, 650),
        ("   camera, beside the key light.", INK, 650),
        ("6. The DJ stand stands by the front of the right wall:", INK, 650),
        "   out of the hero, in the About shot with the piano.",
        ("7. HERO_V3 is a little wider than the photo: our", INK, 650),
        "   room is bigger. The music side is 0 % in frame.",
        "",
        ("Nothing here is built yet. Next: the rebuild reads", ACC, 650),
        ("plan_v3.py (see the report for the files to change).", ACC, 650),
    ], 13.5, MUTED, lh=21)


def main():
    os.makedirs(OUT, exist_ok=True)
    out.clear()
    CHECKS[:] = P.run_checks()
    add(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W_PX}" height="{H_PX}" '
        f'viewBox="0 0 {W_PX} {H_PX}" font-family="-apple-system, Helvetica Neue, Arial, sans-serif">')
    add(f'<rect width="{W_PX}" height="{H_PX}" fill="{PAPER}"/>')
    text(48, 58, "The room v3 · the owner's photo layout: the AI lab in the back-left corner, the music side kept secret", 30, INK, weight=650)
    text(48, 88, "to scale from blender/lib/plan_v3.py · cm · Blender axes: back wall (window) +Y, left wall (AI lab, door) −X, "
         "origin on the floor at the room's centre · room 440 × 420 × 300, door unchanged", 16, MUTED)
    add(f'<rect x="{W_PX - 520}" y="24" width="472" height="44" rx="6" fill="{OBJ_LINE}"/>')
    text(W_PX - 284, 53, "plan v3, approved layout, numbers proposed", 19, "#fff", "middle", weight=700)
    allok = all(q[3] for q in CHECKS)
    text(W_PX - 48, 92, f"2026-10-24 · {len(CHECKS)} checks, {'all pass' if allok else 'SOME FAIL'}", 14,
         MUTED if allok else "#a33", "end")
    plan(40, 116, 1290, 1420)
    hero_panel(1350, 116, 1010, 1420)
    elevations(40, 1560, 2320, 700)
    views_panel(40, 2284, 2320, 820)
    legend(40, 3128, 1500, 760)
    objects_panel(1560, 3128, 800, 760)
    numbers_panel(40, 3912, 1600, 1110)
    owner_panel(1660, 3912, 700, 1110)
    add("</svg>")
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>Room plan v3</title>"
            f"<style>html,body{{margin:0;background:{PAPER}}}svg{{display:block}}</style></head><body>"
            + "\n".join(out) + "</body></html>")
    hp = os.path.join(OUT, "room-plan-v3.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    png = os.path.join(OUT, "room-plan-v3.png")
    subprocess.run([PDS.CHROME, "--headless", "--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist",
                    "--allow-file-access-from-files", "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={W_PX},{H_PX}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for name, g, need, ok in CHECKS:
        print(("ok    " if ok else "CLASH ") + f"{name}: {g * 100:.1f} cm (need {need * 100:.0f})")
    print("wrote", hp, png)


if __name__ == "__main__":
    main()
