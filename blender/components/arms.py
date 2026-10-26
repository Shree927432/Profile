"""The arms and lights around the screens (component, 2026-10-26), as in the owner's photo
docs/moodboard/local/ai-desk-reference-1.jpg:

  - two Elgato Key Light (Mk.2) panels on Master Mount L desk-clamp poles (keylight_1, keylight_2)
  - Sony ZV-E10 II with the E PZ 16-50 mm II (retracted), screen flipped forward (selfie), on an
    Elgato Flex Arm L (tubes 240, 170, 80, 80) clamped to key light 1's pole (cam)
  - Shure MV7+ white on a RODE PSA1+ white, posable from named joint angles (obj_mic)

Built from Sony's drawing and the makers' sizes (no base model: the Innixicated ZV-E10 was not used).
No logos, names or printed text. Always headless:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        --python blender/components/arms.py -- [outline|build,stills,compare,closeups,export] [--cycles]

The room test imports build_set() and places each assembly at plan numbers (room_v3_component_test.py).
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(BLENDER_DIR, ".."))
sys.path.insert(0, BLENDER_DIR)
sys.path.insert(0, os.path.join(BLENDER_DIR, "tools"))

try:
    import bpy
    from mathutils import Matrix, Vector
except ImportError:
    bpy = None

PART = os.environ.get("ARMS_PART", "camera")    # 2026-10-26: the owner reviews the camera first
NAME = "arms" if PART == "all" else f"arms_{PART}"
MM = 0.001
AI = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab")
R_KL, R_CAM, R_MIC, R_ARM = (os.path.join(AI, d) for d in ("17-key-lights", "18-camera", "11-mic", "12-boom-arm"))

# ---------------------------------------------------------------------------
# 1. numbers (OFFICIAL maker / MEASURED from a maker photo at official scale / EST)
# ---------------------------------------------------------------------------
# Elgato Key Light (Mk.2)
KL_W, KL_H = 350 * MM, 250 * MM        # OFFICIAL
KL_D = 35 * MM                         # OFFICIAL (30 to 35 on Elgato's pages; 35 with the back box)
KL_FRAME_T = 15 * MM                   # MEASURED side.jpg: frame 72 px of 176 px total depth -> 15 of 35
KL_BOX = (110 * MM, 150 * MM, 20 * MM)  # MEASURED side.jpg (150 tall from the bottom edge, 20 deep); width EST
KL_R = 58 * MM                         # MEASURED front-on-pole.jpg at 0.315 mm/px (corner radius)
KL_BORDER = 14.8 * MM                  # MEASURED front-on-pole.jpg: the black border, 47 px
KL_NECK = (10 * MM, 20 * MM)           # MEASURED front: neck under the panel, 10 wide, 20 tall
KL_KNOB_R, KL_KNOB_W = 11 * MM, 38 * MM  # MEASURED front: the tilt hinge and its knobs, 38 across
KL_ADAPT = (15 * MM, 65 * MM)          # MEASURED front: the pole-top adapter (r, height)
POLE_R = (14 * MM, 12.5 * MM, 11 * MM)  # EST from pole-clamp-hero.jpg (top section 24 measured on the front photo)
POLE_H = 0.775                         # plan v3: panel bottom at 1.60, minus the mount, above the 76.5 desk
DESK_T = 0.035                         # plan v3 TOP_T

# Sony ZV-E10 II (front -Y, the camera's left = +X; origin: under the lens axis on the base plate)
CB_W, CB_H, CB_D = 114.8 * MM, 67.5 * MM, 54.2 * MM  # OFFICIAL Sony drawing
CB_SHELL = 30 * MM                      # EST: 54.2 = grip 17 + shell 30 + screen 7 (top-pb.jpg: grip 18 proud)
CB_TOP = 65.0 * MM                      # MEASURED front compare: the main top line (67.5 OFFICIAL is to the shutter)
CB_GRIP = (38 * MM, 17 * MM, 62.0 * MM)
GRIP_R = dict(body=5 * MM, outer=13 * MM, inner=9 * MM, fillet=4 * MM)   # MEASURED top-pb.jpg (0.239 mm/px)  # MEASURED Henry's front (0.1226 mm/px) 35.7 to 40 (top-pb), proud 17 (top-pb), height
LENS_X = 19 * MM                        # MEASURED front: lens axis 19 right of the body centre
LENS_Z = 35.7 * MM                      # MEASURED front: lens axis above the base
LENS_R, LENS_L = 33 * MM, 31.3 * MM     # OFFICIAL Sony: 66 x 31.3 retracted
SCREEN = (72.3 * MM, 50.5 * MM, 7 * MM)  # MEASURED front (screen flipped): 72.3 x 50.5, 2.3 off the body; thickness EST
SCREEN_Z = 4.5 * MM                      # MEASURED front: the screen's bottom above the base
# Elgato Flex Arm L
FLEX = [0.240, 0.170, 0.080, 0.080]     # OFFICIAL
FLEX_R = 7.5 * MM                       # EST from kit-parts-hero.jpg (tube to length ratio)

# Shure MV7+ (local: body axis along Y, foam to -Y, origin at the yoke pivot)
MIC_L = 165 * MM                        # MEASURED side-profile (169.5 OFFICIAL overall incl. knob)
MIC_R = 33 * MM                         # MEASURED back.png at 0.0599 mm/px: 66 across
MIC_REAR_R = 28 * MM                    # MEASURED side-profile: tapers to 56 at the rear
MIC_PIVOT = 50 * MM                     # MEASURED side-profile: yoke knobs 47 to 50 from the rear plate
MIC_FOAM = 73 * MM                      # MEASURED side-profile
MIC_RING = 14 * MM                      # MEASURED side-profile: the black ring with the LED strip
YOKE_IN, YOKE_T, YOKE_W = 35.2 * MM, 3.6 * MM, 12 * MM   # MEASURED back.png (inner half-width, thickness); width EST
YOKE_TOP = 83 * MM                      # MEASURED back.png: the arc top above the body axis
STEM = (8 * MM, 48 * MM)                # MEASURED back/front.png: 16 across; length to fit 164 OFFICIAL overall
KNOB = (9.35 * MM, 4.5 * MM)            # MEASURED back.png: 18.7 across, 4.5 proud
# RODE PSA1+
ARM_L1 = ARM_L2 = 0.425                 # MEASURED RODE's drawing: hinge to hinge (500 folded overall)
ARM_W = 65 * MM                         # OFFICIAL width
ARM_COVER = (30 * MM, 40 * MM)          # EST: the padded cover, width x height
ARM_HINGE_R = 30 * MM                   # EST SOURCES (60 discs on the drawing)
ARM_POST = 0.10                         # EST: desk to the shoulder hinge
ARM_TIP = 0.06                          # EST: wrist hinge to the 3/8 stud's end

# the default poses (the room test overrides them)
POSE = dict(swivel=0.0, shoulder=40.0, elbow=-75.0, wrist=0.0, tilt=0.0)

PHOTOS = {}
CUT = os.path.join(REPO, "video-local", "footage", "2026-10-26-components", "arms", "camera", "cutouts")


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def mats():
    from lib import materials as M
    from lib import parts as P
    p = dict(P.palette())

    def get(n, **v):
        return bpy.data.materials.get(n) or M.principled(n, **v)
    p["matte"] = get("mat_arms_matte_black", base="#121314", rough=0.62)
    p["satin"] = get("mat_arms_satin_black", base="#0e0f10", rough=0.38)
    p["cam"] = get("mat_arms_camera_black", base="#0f0f10", rough=0.55, spec=0.22)
    p["lens"] = get("mat_arms_lens_black", base="#0e0e0f", rough=0.5, spec=0.24)
    p["lens_front"] = get("mat_arms_lens_print_ring", base="#0d0d0e", rough=0.62, spec=0.25)
    p["grip"] = bpy.data.materials.get("mat_arms_grip") or grip_material()
    p["mount"] = get("mat_arms_mount_silver", base="#b9bcc1", rough=0.25, metal=1.0)
    p["glass"] = get("mat_arms_lens_glass", base="#06070a", rough=0.02, coat=1.0, coat_rough=0.02)
    p["lcd"] = get("mat_arms_lcd", base="#0a0c10", rough=0.08, emit="#7d93b0", emit_strength=0.3)
    p["white"] = get("mat_arms_white", base="#eeeeec", rough=0.42, coat=0.1)
    p["mic_white"] = get("mat_arms_mic_white", base="#ececea", rough=0.45)
    p["foam"] = get("mat_arms_foam", base="#0d0d0e", rough=0.95, sheen=0.4, sheen_rough=0.6)
    p["led"] = get("mat_arms_mic_led", base="#9fe8e0", rough=0.3, emit="#7ff0e4", emit_strength=4.0)
    p["glow"] = get("mat_arms_keylight_glow", base="#ffffff", rough=0.6, emit="#fff6ea", emit_strength=6.0)
    p["red"] = get("mat_arms_red", base="#a3201c", rough=0.4)
    return p


def grip_material():
    """The grip's fine pebble texture: a noise bump (no image, so it survives the GLB as plain black)."""
    from lib import materials as M
    m, nt, b = M._new("mat_arms_grip")
    M._set(b, base="#080809", rough=0.82, spec=0.16)
    co = M._coords(nt, scale=(1, 1, 1))
    n = M._noise(nt, co, 2600.0, detail=2, rough=0.6)
    M._bump(nt, b, n, 0.25, distance=0.0002)
    m.diffuse_color = (0.02, 0.02, 0.02, 1)
    return m


# ---------------------------------------------------------------------------
# geometry helpers (one parts.Mesh per object; m places a piece inside the object)
# ---------------------------------------------------------------------------
def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(deg, axis):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def along(p0, p1):
    """Matrix taking local +Z (length 1 unit = metres) from p0 towards p1."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    q = d.normalized().to_track_quat("Z", "Y")
    return Matrix.Translation(p0) @ q.to_matrix().to_4x4(), d.length


def rbox(A, w, d, h, r_side, r_top, r_bottom, seg, key, m, z0=0.0):
    from lib.parts import rrect
    n = seg if r_side > 0 else 0
    rings = []
    if r_bottom > 0:
        for i in range(seg + 1):
            t = math.pi / 2 * i / seg
            rings.append((z0 + r_bottom * (1 - math.cos(t)), r_bottom * (1 - math.sin(t))))
    else:
        rings.append((z0, 0.0))
    if r_top > 0:
        for i in range(seg, -1, -1):
            t = math.pi / 2 * i / seg
            rings.append((z0 + h - r_top * (1 - math.cos(t)), r_top * (1 - math.sin(t))))
    else:
        rings.append((z0 + h, 0.0))
    loops = []
    for z, ins in rings:
        rc = max(r_side - ins, 0.12 * r_side) if r_side > 0 else 0.0
        loops.append(A.verts([(x, y, z) for x, y in rrect(w - 2 * ins, d - 2 * ins, rc, n)], m))
    for a, b in zip(loops, loops[1:]):
        A.strip(a, b, key)
    A.face(list(reversed(loops[0])), key)
    A.face(loops[-1], key)


def cyl(A, r, p0, p1, key, seg, r1=None, caps=True):
    m, L = along(p0, p1)
    r1 = r if r1 is None else r1
    prof = ([(0, 0)] if caps else []) + [(r, 0), (r1, L)] + ([(0, L)] if caps else [])
    A.lathe(prof, seg, key, m)


def empty(name, parent=None, loc=(0, 0, 0), rot=None, coll=None):
    from lib import names
    e = bpy.data.objects.new(name, None)
    (coll or bpy.context.scene.collection).objects.link(e)
    names.set_name(e, name, data=False)
    e.parent = parent
    e.location = loc
    if rot is not None:
        e.rotation_euler = rot
    e.empty_display_size = 0.03
    return e


def fin(A, name, mp, coll, parent=None, at=(0, 0, 0), bevel=None, lite=False):
    return A.finish(name, mp, "+Z", at, coll, parent, bevel=None if lite else bevel)


# ---------------------------------------------------------------------------
# 2a. key light on its pole. Origin: the pole's axis on the desk top; the panel faces -Y.
# ---------------------------------------------------------------------------
def build_keylight(n, coll, mp, rough=False, lite=False, pole_h=POLE_H, tilt=0.0, sfx=""):
    from lib import parts as P
    seg = 16 if lite else (32 if rough else 48)
    cs = 2 if lite else 6
    root = empty(f"keylight_{n}{sfx}", coll=coll)
    # the pole and its clamp: keylight_N_static
    A = P.Mesh()
    z1, z2 = 0.46 * pole_h, 0.76 * pole_h
    A.lathe([(0, 0), (POLE_R[0], 0), (POLE_R[0], z1), (0, z1)], seg, "matte")
    A.lathe([(0, z1 - 0.02), (POLE_R[1], z1 - 0.02), (POLE_R[1], z2), (0, z2)], seg, "matte")
    A.lathe([(0, z2 - 0.02), (POLE_R[2], z2 - 0.02), (POLE_R[2], pole_h), (0, pole_h)], seg, "matte")
    if not rough:
        for z, r in ((z1, POLE_R[0]), (z2, POLE_R[1])):        # the twist-lock collars
            A.lathe([(0, z - 0.004), (r + 0.0035, z - 0.004), (r + 0.0045, z), (r + 0.0045, z + 0.022),
                     (r + 0.002, z + 0.026), (0, z + 0.026)], seg, "satin")
        # the desk clamp (Master Mount L: a C-clamp under a round foot, a screw and a T-handle)
        A.lathe([(0, 0.0), (0.024, 0.0), (0.024, 0.012), (0.018, 0.020), (POLE_R[0], 0.024), (0, 0.024)], seg, "satin")
        yb = 0.040                                           # the desk's edge behind the pole (+Y)
        rbox(A, 0.050, 0.014, 0.012 + DESK_T + 0.016, 0.003, 0, 0, cs, "satin", T(0, yb + 0.007, -DESK_T - 0.016))
        rbox(A, 0.050, yb + 0.03, 0.010, 0.004, 0, 0, cs, "satin", T(0, yb / 2 - 0.008, -DESK_T - 0.016))
        A.lathe([(0, -0.072), (0.0045, -0.072), (0.0045, -DESK_T - 0.004), (0, -DESK_T - 0.004)], 12, "chrome")
        A.lathe([(0, -DESK_T - 0.004), (0.013, -DESK_T - 0.004), (0.013, -DESK_T), (0, -DESK_T)], seg, "rubber")
        cyl(A, 0.004, (-0.03, 0, -0.068), (0.03, 0, -0.068), "satin", 12)     # the T-handle
    static = fin(A, f"keylight_{n}_static{sfx}", mp, coll, root, bevel=0.0008, lite=lite)
    # the tilt joint at the pole top, the panel above it
    zp = pole_h + KL_ADAPT[1]
    tilt_e = empty(f"keylight_{n}_tilt{sfx}", root, (0, 0, zp), (math.radians(tilt), 0, 0), coll)
    A = P.Mesh()
    # adapter (in the pole frame, so it does not tilt): below the pivot
    A.lathe([(0, -KL_ADAPT[1]), (KL_ADAPT[0], -KL_ADAPT[1]), (KL_ADAPT[0], -0.012), (0.008, -0.004), (0, -0.004)],
            seg, "satin")
    hub = A.verts([(0, 0, 0)])
    static_adapter = fin(A, f"keylight_{n}_mount{sfx}", mp, coll, tilt_e, bevel=0.0008, lite=lite)
    static_adapter.parent = root
    static_adapter.location = (0, 0, zp)
    # the panel: hinge knobs, neck, frame, back box; glow face separately
    A = P.Mesh()
    cyl(A, KL_KNOB_R * 0.7, (-KL_KNOB_W / 2 + 0.006, 0, 0), (KL_KNOB_W / 2 - 0.006, 0, 0), "satin", seg)
    if not rough:
        for s in (-1, 1):
            cyl(A, KL_KNOB_R, (s * (KL_KNOB_W / 2 - 0.007), 0, 0), (s * KL_KNOB_W / 2, 0, 0), "matte", seg)
    rbox(A, KL_NECK[0], 0.016, KL_NECK[1], 0.002, 0, 0, cs, "satin", T(0, 0, 0.004))
    zb = KL_NECK[1]                                       # panel bottom above the pivot
    yf = -KL_FRAME_T / 2                                  # the frame is centred over the pole; front at yf
    Mf = T(0, yf, zb + KL_H / 2) @ R(-90, "X")            # panel frame: local z = -Y (outward... flipped below)
    # frame: rounded slab KL_W x KL_H, KL_FRAME_T deep (built along +Y)
    Mp = T(0, yf, zb + KL_H / 2) @ R(90, "X")             # local +Z -> world -Y ; rotate so z0..h runs back
    Mp = T(0, yf + KL_FRAME_T, zb + KL_H / 2) @ R(90, "X")   # local z 0..t maps to y from yf+t down to yf
    if rough:
        rbox(A, KL_W, KL_H, KL_FRAME_T, KL_R, 0, 0, 8, "matte", Mp)
    else:
        # the front lip: a frame ring proud of the glow face by 2 mm, rounded outer edge
        rbox(A, KL_W, KL_H, KL_FRAME_T, KL_R, 0.004, 0.006, 3 if lite else 4, "matte", Mp)
    if not rough:
        bw, bh, bd = KL_BOX
        Mb = T(0, yf + KL_FRAME_T + bd, zb + bh / 2 + 0.004) @ R(90, "X")
        rbox(A, bw, bh, bd, 0.016, 0.006, 0.0, 3 if lite else 4, "matte", Mb)
        # the back's raised cooling plate (a shallow rounded panel around the box)
        Mc = T(0, yf + KL_FRAME_T + 0.003, zb + KL_H / 2) @ R(90, "X")
        rbox(A, KL_W - 0.06, KL_H - 0.05, 0.003, KL_R - 0.03, 0.002, 0, 3 if lite else 4, "satin", Mc)
        # power and control buttons on the box's underside / side: two small pads
        rbox(A, 0.012, 0.006, 0.003, 0.002, 0, 0, 2, "rubber", T(0.035, yf + KL_FRAME_T + bd / 2, zb + 0.004 - 0.003))
    else:
        bw, bh, bd = KL_BOX
        rbox(A, bw, bh, bd, 0.016, 0, 0, 2, "matte", T(0, yf + KL_FRAME_T + bd, zb + bh / 2) @ R(90, "X"))
    panel = fin(A, f"keylight_{n}_panel{sfx}", mp, coll, tilt_e, bevel=0.0012, lite=lite)
    # the diffuser: the glow face, 1.5 mm behind the lip
    A = P.Mesh()
    gw, gh = KL_W - 2 * KL_BORDER, KL_H - 2 * KL_BORDER
    Mg = T(0, yf + 0.0015 + 0.0004, zb + KL_H / 2) @ R(90, "X")
    rbox(A, gw, gh, 0.0004, KL_R - KL_BORDER, 0, 0, 4 if lite else 10, "glow", Mg)
    glow = fin(A, f"keylight_{n}_glow{sfx}", mp, coll, tilt_e, lite=True)
    out = {"kl_static": [static.name, static_adapter.name], "kl_panel": [panel.name], "kl_glow": [glow.name]}
    return root, out


# ---------------------------------------------------------------------------
# 2b. the camera. Origin: under the lens axis on the base plate (the 1/4 thread); front -Y.
# ---------------------------------------------------------------------------

def body_outline(ins, d, n=6):
    """Top-view outline of body + grip at one height (mm-free, metres; x about the body centre, y from the
    front plate, + back). ins: inset (edge rounding); d: how far the grip stands proud of the front plate
    (0 = the grip has rounded away). Radii shrink with d so the grip melts into the plate. Fixed point count."""
    W, D, GW, GD = CB_W, CB_SHELL, CB_GRIP[0], CB_GRIP[1]
    t = max(0.0, min(1.0, d / GD))
    eps = 0.0003
    rb = GRIP_R["body"] - ins * 0.5
    rg1 = max(eps, rb + (GRIP_R["outer"] - rb) * t)
    rg2 = max(eps, GRIP_R["inner"] * t)
    rf = max(eps, GRIP_R["fillet"] * t)
    xl, xr, yb = -W / 2 + ins, W / 2 - ins, D - ins
    yfr = ins                       # the front plate
    yg = -d + ins if d > 0 else ins # the grip's front
    xg = -W / 2 + GW
    pts = []

    def arc(cx, cy, r, a0, a1):
        for k in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    arc(xl + rg1, yg + rg1, rg1, 180, 270)          # grip, front outer corner
    arc(xg - rg2, yg + rg2, rg2, 270, 360)          # grip, front inner corner
    arc(xg + rf, yfr - rf, rf, 180, 90)             # the concave fillet into the front plate
    arc(xr - rb, yfr + rb, rb, 270, 360)            # front plate, the lens end
    arc(xr - rb, yb - rb, rb, 0, 90)
    arc(xl + rb, yb - rb, rb, 90, 180)
    return pts


def body_shell(A, key, m, rough=False, lite=False):
    """The body and the grip as ONE closed surface: horizontal outlines lofted from the base up. The grip
    keeps its full depth to 6 mm under its top, rounds over (6 mm), steps onto its flat top 3 mm under the
    body's, and a 2 mm concave fillet runs it into the front plate above."""
    H, GT, GD = CB_TOP, CB_GRIP[2], CB_GRIP[1]
    rB, rT, RT, FIL = 0.0025, 0.0010, 0.006, 0.0015    # the front-top edge is crisp (about 1 mm)
    nb = 2 if lite else 4
    lv = []
    for i in range(nb + 1):
        a = math.pi / 2 * i / nb
        lv.append((rB * (1 - math.cos(a)), rB * (1 - math.sin(a)), GD))
    lv.append((GT - RT, 0.0, GD))
    for i in range(1, nb + 1):
        a = math.pi / 2 * i / nb
        lv.append((GT - RT + RT * math.sin(a), 0.0, GD - RT + RT * math.cos(a)))
    for i in range(nb + 1):
        a = math.pi / 2 * i / nb
        lv.append((GT + 0.0003 + FIL - FIL * math.cos(a), 0.0, FIL - FIL * math.sin(a)))   # 0.3 mm: no flat faces
    lv.append((H - rT, 0.0, 0.0))
    for i in range(1, nb + 1):
        a = math.pi / 2 * i / nb
        lv.append((H - rT + rT * math.sin(a), rT * (1 - math.cos(a)), 0.0))
    n = 2 if lite else 6
    loops = [A.verts([(x, y, z) for x, y in body_outline(ins, d, n)], m) for z, ins, d in lv]
    for a, b in zip(loops, loops[1:]):
        A.strip(a, b, key)
    A.face(list(reversed(loops[0])), key)
    A.face(loops[-1], key)


def build_camera(coll, mp, rough=False, lite=False, sfx="", screen="selfie"):
    """Positions on the top plate are MEASURED from top-pb.jpg (0.239 mm/px from the 114.8 width), heights
    and the front from Henry's front image (0.227 mm/px in the compare sheet). Model x: + = the camera's
    left (the lens side), y from the shell's front face."""
    from lib import parts as P
    seg = 20 if lite else (32 if rough else 64)
    cs = 2 if lite else 5
    root = empty(f"cam{sfx}", coll=coll)
    x0 = -LENS_X                          # body centre x (the origin is under the lens)
    yf = -0.0135                          # the shell's front face
    H = CB_TOP
    A = P.Mesh()
    # body and grip: one lofted surface (the grip's pebble finish is its own material on the separate
    # cam_grip skin below, so the shell itself stays one smooth piece)
    body_shell(A, "cam", T(x0, yf, 0), rough, lite)
    if not rough:
        X = lambda mm: x0 + mm * MM       # noqa: E731  (mm from the body centre, + = the camera's left)
        Y = lambda mm: yf + mm * MM       # noqa: E731  (mm behind the front face)
        # the raised plate on the camera's left end (the shoe and the grille sit on it)
        rbox(A, 0.040, CB_SHELL - 0.002, 0.0012, 0.004, 0.0006, 0, cs, "cam", T(X(37.5), Y(15), H - 0.0002))
        hp = H + 0.001
        rbox(A, 0.0175, 0.0175, 0.0012, 0.0012, 0, 0, 2, "satin", T(X(37), Y(16), hp))           # hot shoe (black cover)
        for s in (-1, 1):
            rbox(A, 0.0175, 0.0015, 0.0014, 0.0003, 0, 0, 1, "steel", T(X(37), Y(16) + s * 0.0082, hp + 0.0008))
        rbox(A, 0.031, 0.016, 0.0006, 0.002, 0, 0, 2, "port", T(X(7), Y(14.6), H - 0.0001))       # mic grille
        if not lite:
            for i in range(20):
                for j in range(10):
                    rbox(A, 0.0009, 0.0009, 0.0004, 0, 0, 0, 0, "satin",
                         T(X(7) + (i - 9.5) * 0.0014, Y(14.6) + (j - 4.5) * 0.0014, H + 0.0004))
        # shutter button inside the zoom lever ring, on the grip top, the ON/OFF lever beside it
        sx, sy = X(-36), Y(-9)
        gt = CB_GRIP[2]
        A.lathe([(0, gt - 0.002), (0.0085, gt - 0.002), (0.0085, gt + 0.0022), (0.0080, gt + 0.0026), (0, gt + 0.0026)],
                seg, "satin", T(sx, sy, 0))
        A.lathe([(0, gt + 0.0026), (0.0050, gt + 0.0026), (0.0050, gt + 0.0050), (0.0044, gt + 0.0056), (0, gt + 0.0056)],
                seg, "satin", T(sx, sy, 0))
        rbox(A, 0.006, 0.004, 0.003, 0.0015, 0, 0, 2, "satin", T(sx - 0.0095, sy - 0.001, gt))      # zoom lever tab
        rbox(A, 0.004, 0.007, 0.0025, 0.0015, 0, 0, 2, "satin", T(sx - 0.002, sy + 0.010, gt - 0.0005))  # ON/OFF
        # record button (red ring), C1, the mode switch, the rear control dial (17 across, proud of the back)
        for (bx, by, r, key) in ((-33, 7, 0.0040, "red"), (-45.4, 7, 0.0030, "satin")):
            A.lathe([(0, H - 0.001), (r, H - 0.001), (r, H + 0.0008), (0, H + 0.0008)], 24, key, T(X(bx), Y(by), 0))
        A.lathe([(0, H + 0.0008), (0.0029, H + 0.0008), (0.0029, H + 0.0011), (0, H + 0.0011)], 24, "cam",
                T(X(-33), Y(7), 0))
        rbox(A, 0.018, 0.005, 0.0008, 0.0025, 0, 0, 2, "satin", T(X(-19.6), Y(19), H - 0.0002))
        rbox(A, 0.004, 0.0035, 0.0018, 0.001, 0, 0, 1, "steel", T(X(-20.5), Y(19), H + 0.0004))
        ribs = 0 if lite else 30
        kn = (lambda a: 1.0 + 0.03 * max(0.0, math.cos(ribs * a))) if ribs else None
        A.lathe([(0, H - 0.002), (0.0083, H - 0.002), (0.0083, H + 0.0025, kn) if kn else (0.0083, H + 0.0025),
                 (0.0078, H + 0.0031), (0, H + 0.0031)], seg, "satin", T(X(-40.6), Y(22), 0))
        # strap eyelets, both sides: thin steel loops at 60 mm
        for s in (-1, 1):
            xs = x0 + s * (CB_W / 2 + 0.0021)
            rbox(A, 0.0042, 0.006, 0.003, 0.0012, 0.001, 0.001, 2, "steel", T(xs, Y(15), 0.0585))
        # front: tally lamp (top right), the AF/self-timer lamp by the lens, the lens release button
        A.lathe([(0, 0), (0.0009, 0), (0.0009, 0.0005), (0, 0.0005)], 12, "red", T(X(51), yf, H - 0.0035) @ R(90, "X"))
        A.lathe([(0, 0), (0.003, 0), (0.003, 0.0006), (0, 0.0006)], 16, "port", T(X(-10), yf, 0.0186) @ R(90, "X"))
        A.lathe([(0, 0), (0.0032, 0), (0.0032, 0.0015), (0.0028, 0.002), (0, 0.002)], 16, "satin",
                T(X(4), yf, 0.012) @ R(90, "X"))
        # base: the tripod thread, the battery door seam
        A.lathe([(0, 0.0), (0.0032, 0.0), (0.0032, 0.0004), (0, 0.0004)], 16, "port", T(0, Y(15), 0) @ R(180, "X"))
        rbox(A, 0.032, 0.026, 0.0003, 0.002, 0, 0, 2, "satin", T(X(-36), Y(15), -0.0002))
        # rear: the empty screen bay (screen out), the thumb rest, the buttons and the control wheel
        rbox(A, 0.074, 0.0012, 0.050, 0.003, 0, 0, 2, "satin", T(X(9), Y(30), 0.007))
        rbox(A, 0.020, 0.005, 0.016, 0.005, 0.002, 0, cs, "grip", T(X(-46), Y(30), 0.046))
        for bz in (0.038, 0.030, 0.013, 0.006):
            A.lathe([(0, 0), (0.0026, 0), (0.0026, 0.0010), (0, 0.0010)], 16, "satin",
                    T(X(-48), Y(30), bz) @ R(-90, "X"))
        A.lathe([(0.0045, 0), (0.0082, 0), (0.0082, 0.0016), (0.0045, 0.0016)], 32, "satin",
                T(X(-39), Y(30), 0.022) @ R(-90, "X"))
        A.lathe([(0, 0), (0.0040, 0), (0.0040, 0.0010), (0, 0.0010)], 24, "satin", T(X(-39), Y(30), 0.022) @ R(-90, "X"))
    body = fin(A, f"cam_body{sfx}", mp, coll, root, bevel=0.0005, lite=lite)
    if not rough:
        body.data.materials.append(mp["grip"])
        gi = len(body.data.materials) - 1
        xg = x0 - CB_W / 2 + CB_GRIP[0] + 0.0005
        for poly in body.data.polygons:      # the grip's faces (left of the grip's inner edge, in front of
            c = poly.center                  # the plate or on its outer end) take the grip material
            if c.x < xg and (c.y < yf + 0.0004 or c.x < x0 - CB_W / 2 + 0.0004) and c.z < CB_GRIP[2] + 0.0005 \
                    and abs(poly.normal.z) < 0.9:
                poly.material_index = gi
    # the lens (E PZ 16-50 II, retracted), its own mesh: barrel, the ribbed control ring, the stepped front
    A = P.Mesh()
    Ml = T(0, yf, LENS_Z) @ R(90, "X")             # local +Z -> world -Y (forward)
    r, L = LENS_R, LENS_L
    seg = 24 if lite else (32 if rough else 144)   # 2 vertices per rib of the 72-rib zoom ring
    if rough:
        A.lathe([(0, 0), (r, 0), (r, L), (0, L)], seg, "lens", Ml)
    else:
        # MEASURED top-pb.jpg (proportions along the axis) and Henry's front (radial rings, 0.1226 mm/px):
        # mount ring 2.8 long, plain printed barrel 61.6 across, the ribbed zoom ring at the front (14 long,
        # 66 across), a flat front ring r 31.5 to 22, a black inner ring, the element (30 across) sunk 5.8 mm
        ribs = 0 if lite else 72
        kn = (lambda a: 1.0 + 0.0045 * max(0.0, math.cos(ribs * a))) if ribs else None

        def k(rr, z):
            return (rr, z, kn) if kn else (rr, z)
        rp = 0.0308
        prof = [(0, 0.0), (0.0300, 0.0), (0.0313, 0.0005), (0.0313, 0.0028), (rp, 0.0030), (rp, 0.0168),
                (0.0326, 0.0172), (0.0330, 0.0178), k(r, 0.0182), k(r, 0.0300), (0.0326, 0.0308), (0.0316, L),
                (0.0220, L), (0.0216, L - 0.0014), (0.0185, L - 0.0016), (0.0181, L - 0.0040),
                (0.0152, L - 0.0058), (0, L - 0.0058)]
        keys = ["lens", "lens", "lens", "lens", "lens", "lens", "lens", "lens", "lens", "lens", "lens",
                "lens_front", "lens", "lens", "lens", "lens", "lens"]
        A.lathe(prof, seg, keys, Ml)
        # the element's black retaining ring: leaves a clear centre 23 across (Henry's: dark to r 10-11)
        zg = L - 0.0059
        A.lathe([(0.0115, zg + 0.0012), (0.0151, zg + 0.0008), (0.0151, zg + 0.0019), (0.0122, zg + 0.0026),
                 (0.0115, zg + 0.0026)], seg, "lens", Ml)
        # the zoom/focus switch tab on the barrel's left (+X) side
        rbox(A, 0.004, 0.009, 0.007, 0.0015, 0, 0, 2, "lens", T(rp + 0.0018, yf - 0.009, LENS_Z) @ R(90, "Y"))
    lens = fin(A, f"cam_lens{sfx}", mp, coll, root, bevel=None, lite=lite)
    out = {"cam_body": [body.name], "cam_lens": [lens.name], "cam_screen": []}
    if not rough:   # the front element: a glass dome inside the filter ring (40.5 thread)
        A = P.Mesh()
        z0 = L - 0.0059
        A.lathe([(0, z0), (0.0152, z0), (0.0148, z0 + 0.0006), (0.0110, z0 + 0.0016), (0.0055, z0 + 0.0022),
                 (0, z0 + 0.0024)], seg, "glass", Ml)
        out["cam_lens"].append(fin(A, f"cam_lens_glass{sfx}", mp, coll, root, lite=lite).name)
    # the vari-angle screen: hinge on the camera's left (+X); "selfie" = swung out and facing front
    A = P.Mesh()
    sw, sh, st = SCREEN
    xb = x0 + CB_W / 2
    ys = yf + CB_SHELL - st
    Ms = T(xb + 0.0023 + sw / 2, ys + st, SCREEN_Z + sh / 2) @ R(90, "X")
    rbox(A, sw, sh, st, 0.004, 0.0015 if not rough else 0, 0.0015 if not rough else 0, cs, "cam", Ms)
    if not rough:
        cyl(A, 0.0022, (xb + 0.0006, ys + st / 2, 0.012), (xb + 0.0006, ys + st / 2, 0.046), "satin", 12)
        rbox(A, 0.0035, 0.004, 0.032, 0.001, 0, 0, 2, "satin", T(xb + 0.0012, ys + st / 2, 0.013))
    out["cam_screen"].append(fin(A, f"cam_screen{sfx}", mp, coll, root, bevel=0.0005, lite=lite).name)
    if not rough:
        A = P.Mesh()
        Md = T(xb + 0.0023 + sw / 2, ys - 0.00015, SCREEN_Z + sh / 2) @ R(90, "X")
        rbox(A, sw - 0.005, sh - 0.005, 0.0002, 0.002, 0, 0, 2, "lcd", Md)
        out["cam_screen"].append(fin(A, f"cam_screen_lcd{sfx}", mp, coll, root, lite=True).name)
    return root, out


def flex_points(start, end, lens=FLEX, bulge=(0, 0, 0.14), iters=60):
    """FABRIK: joint points from start to end for the Flex Arm's tubes (an arc bulging up first)."""
    S, E = Vector(start), Vector(end)
    n = len(lens)
    pts = []
    tot = sum(lens)
    acc = 0.0
    for i in range(n + 1):
        t = acc / tot
        pts.append(S.lerp(E, t) + Vector(bulge) * math.sin(math.pi * t))
        if i < n:
            acc += lens[i]
    for _ in range(iters):
        pts[-1] = E.copy()
        for i in range(n - 1, -1, -1):
            d = (pts[i] - pts[i + 1]).normalized()
            pts[i] = pts[i + 1] + d * lens[i]
        pts[0] = S.copy()
        for i in range(n):
            d = (pts[i + 1] - pts[i]).normalized()
            pts[i + 1] = pts[i] + d * lens[i]
    return pts


def build_flexarm(coll, mp, pole_xyz, pole_r, start, end, lite=False, rough=False, sfx=""):
    """The pole clamp at start (on the pole), the four tubes through FABRIK to end (the camera's base)."""
    from lib import parts as P
    seg = 10 if lite else 24
    A = P.Mesh()
    px, py, pz = pole_xyz
    # the clamp: a collar round the pole with a short arm out to the first ball
    A.lathe([(0, -0.02), (pole_r + 0.006, -0.02), (pole_r + 0.006, 0.02), (0, 0.02)], seg, "satin",
            T(px, py, start[2]))
    cyl(A, 0.008, (px, py, start[2]), start, "satin", seg)
    if not rough:
        k = (Vector(start) - Vector((px, py, start[2]))).normalized()
        side = k.cross(Vector((0, 0, 1))).normalized()
        c = Vector((px, py, start[2])) - side * (pole_r + 0.008)
        cyl(A, 0.010, c, c - side * 0.012, "matte", seg)                 # the clamp knob
    pts = flex_points(start, end)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d = (b - a).normalized()
        cyl(A, FLEX_R, a + d * 0.014, b - d * 0.012, "matte", seg)
        if not rough:
            # ball head at the tube's end, socket clamp with a lever at its start
            A.lathe([(0, -0.0095), (0.0068, -0.0068), (0.0095, 0), (0.0068, 0.0068), (0, 0.0095)], seg, "satin", T(*b))
            cyl(A, 0.0115, a, a + d * 0.024, "satin", seg)
            lever = d.cross(Vector((0, 0, 1)))
            if lever.length < 1e-4:
                lever = Vector((1, 0, 0))
            lever.normalize()
            cyl(A, 0.003, a + d * 0.012, a + d * 0.012 + lever * 0.022, "matte", 8)
    # the 1/4 screw into the camera
    cyl(A, 0.0032, end, Vector(end) + Vector((0, 0, 0.004)), "steel", 12)
    o = fin(A, f"cam_arm{sfx}", mp, coll, None, lite=lite)
    return o, pts


# ---------------------------------------------------------------------------
# 2c. the mic and its arm. obj_mic's origin: the clamp's pole axis on the desk top; the arm's rest
#     direction is +X (swivel turns it).
# ---------------------------------------------------------------------------
def build_mic_head(coll, mp, parent, rough=False, lite=False, sfx=""):
    """The MV7+ hanging from its stem. Returns (yoke empty at the stem top, body tilt empty, names).
    In the yoke frame: the stem top at z=0, the body axis along Y (foam to -Y) at z = -(stem+arc)."""
    from lib import parts as P
    seg = 20 if lite else (32 if rough else 64)
    zc = -(STEM[1] + YOKE_TOP)            # the body axis (pivot) under the stem top
    hang = empty(f"mic_j_stem{sfx}", parent, coll=coll)
    A = P.Mesh()
    # stem, lock ring, the yoke's top block and the U strap down to the knobs
    A.lathe([(0, -STEM[1]), (STEM[0], -STEM[1]), (STEM[0], 0), (0, 0)], seg, "mic_white")
    if not rough:
        A.lathe([(0, -0.012), (0.0125, -0.012), (0.0125, -0.004), (0, -0.004)], seg, "mic_white")
        A.lathe([(0.0035, -0.0001), (0.0062, -0.0001), (0.0062, 0.0004), (0.0035, 0.0004)], 24, "steel")  # thread insert
    rbox(A, 0.024, YOKE_W + 0.004, 0.012, 0.004, 0.002, 0.002, 3, "mic_white", T(0, 0, -STEM[1] - 0.010))
    # strap: an arc from the knob axis up and over (semi-circle top, straight sides)
    ro = YOKE_IN + YOKE_T                # outer half-width
    straight = YOKE_TOP - ro            # the straight part's length above the axis
    nA = 6 if lite else 18
    path = [(-ro + YOKE_T / 2, zc + 0.0), (-ro + YOKE_T / 2, zc + straight)]
    for k in range(1, nA):
        a = math.pi - math.pi * k / nA
        path.append(((ro - YOKE_T / 2) * math.cos(a), zc + straight + (ro - YOKE_T / 2) * math.sin(a)))
    path += [(ro - YOKE_T / 2, zc + straight), (ro - YOKE_T / 2, zc)]
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        d = Vector((x1 - x0, 0, z1 - z0))
        L = d.length
        ang = math.degrees(math.atan2(d.x, d.z))
        rbox(A, YOKE_T, YOKE_W, L + 0.0012, 0.0008, 0, 0, 1, "mic_white", T(x0, 0, z0) @ R(ang, "Y") @ T(0, 0, -0.0006))
    yoke = fin(A, f"mic_yoke{sfx}", mp, coll, hang, lite=lite)
    # the tilt empty at the knob axis, the body inside it
    tilt = empty(f"mic_j_tilt{sfx}", hang, (0, 0, zc), coll=coll)
    A = P.Mesh()
    Mb = R(90, "X")                      # local +Z -> world -Y: the lathe's z runs from the rear (z<0) forward
    zr = -MIC_PIVOT                      # rear plate
    zl = MIC_L - MIC_PIVOT - MIC_FOAM - MIC_RING   # the LED ring starts
    zf = MIC_L - MIC_PIVOT                # the foam's front
    if rough:
        A.lathe([(0, zr), (MIC_REAR_R, zr), (MIC_R, zl), (MIC_R, zf - 0.015), (MIC_R - 0.012, zf), (0, zf)], seg,
                "mic_white", Mb)
    else:
        A.lathe([(0, zr), (MIC_REAR_R - 0.004, zr), (MIC_REAR_R - 0.0005, zr + 0.0015), (MIC_REAR_R, zr + 0.004),
                 (MIC_R - 0.0004, zl - 0.002), (MIC_R, zl)], seg, "mic_white", Mb)
        A.lathe([(MIC_R, zl), (MIC_R + 0.0002, zl + 0.003)], seg, "satin", Mb) if False else None
        # the black ring: front of the body, with a groove for the LED strip (the strip is mic_led)
        A.lathe([(MIC_R - 0.0003, zl), (MIC_R + 0.0003, zl), (MIC_R + 0.0003, zl + 0.003), (MIC_R - 0.0008, zl + 0.0035),
                 (MIC_R - 0.0008, zl + 0.0065), (MIC_R + 0.0003, zl + 0.007), (MIC_R + 0.0003, zl + MIC_RING),
                 (MIC_R - 0.001, zl + MIC_RING)], seg, "satin", Mb)
        # knobs (black, knurled) on both sides at the pivot, and the rear panel's ports
        for s in (-1, 1):
            k = P.Mesh  # noqa
        foam_z0 = zl + MIC_RING
        rf = MIC_R - 0.001
        prof = [(rf, foam_z0)]
        prof += [(rf, zf - 0.020)]
        for k in range(1, 7):
            a = math.pi / 2 * k / 7
            prof.append((0.012 + (rf - 0.012) * math.cos(a), zf - 0.020 + 0.020 * math.sin(a)))
        prof += [(0, zf)]
        A.lathe(prof, seg, "foam", Mb)
    body = fin(A, f"mic_body{sfx}", mp, coll, tilt, lite=lite)
    out = {"mic_body": [body.name], "mic_yoke": [yoke.name]}
    if not rough:
        A = P.Mesh()
        for s in (-1, 1):
            x = s * (YOKE_IN + YOKE_T)
            ribs = 0 if lite else 24
            kn = (lambda a: 1.0 + 0.04 * max(0.0, math.cos(ribs * a))) if ribs else None
            prof = [(0, 0), (KNOB[0] * 0.8, 0), (KNOB[0], 0.001, kn) if kn else (KNOB[0], 0.001),
                    (KNOB[0], KNOB[1] - 0.001, kn) if kn else (KNOB[0], KNOB[1] - 0.001), (KNOB[0] * 0.85, KNOB[1]), (0, KNOB[1])]
            A.lathe(prof, seg, "satin", T(x, 0, 0) @ R(90 * s, "Y"))
        # the rear plate: XLR (3 pins), USB-C, 3.5 mm jack, as dark sockets (no text)
        Mr = T(0, MIC_PIVOT, 0) @ R(-90, "X")       # local +Z -> world +Y (out of the rear)
        A.lathe([(0, 0.0), (0.0105, 0.0), (0.0105, 0.0004), (0, 0.0004)], 32, "port", Mr @ T(0, -0.002, 0))
        for k in range(3):
            a = math.radians(90 + 120 * k)
            A.lathe([(0, 0.0), (0.0011, 0.0), (0.0011, 0.004), (0, 0.004)], 8, "steel",
                    Mr @ T(0.0055 * math.cos(a), -0.002 + 0.0055 * math.sin(a), -0.003))
        rbox(A, 0.009, 0.0032, 0.0006, 0.0015, 0, 0, 2, "port", Mr @ T(0.0, -0.0165, 0))
        A.lathe([(0, 0.0), (0.0021, 0.0), (0.0021, 0.0006), (0, 0.0006)], 16, "port", Mr @ T(-0.0145, 0.008, 0))
        knobs = fin(A, f"mic_knobs{sfx}", mp, coll, tilt, lite=lite)
        out["mic_body"].append(knobs.name)
        # the LED strip: a thin emissive band in the black ring's groove
        A = P.Mesh()
        A.lathe([(MIC_R - 0.0007, zl + 0.0035), (MIC_R - 0.0002, zl + 0.0035), (MIC_R - 0.0002, zl + 0.0065),
                 (MIC_R - 0.0007, zl + 0.0065)], seg, "led", Mb)
        led = fin(A, f"mic_led{sfx}", mp, coll, tilt, lite=True)
        out["mic_led"] = [led.name]
    return hang, tilt, out


def build_mic(coll, mp, rough=False, lite=False, pose=None, sfx=""):
    """obj_mic: clamp and post (mic_static), lower and upper arms (mic_arm_lower/upper), the wrist head
    (mic_arm_tip), the MV7+ under it. Joints are empties: mic_j_swivel (Z), mic_j_shoulder, mic_j_elbow
    (pitch), mic_j_wrist (levels the head, then yaw), mic_j_tilt (the mic in its yoke)."""
    from lib import parts as P
    pose = dict(POSE, **(pose or {}))
    seg = 16 if lite else (24 if rough else 48)
    cs = 2 if lite else 5
    root = empty(f"obj_mic{sfx}", coll=coll)
    A = P.Mesh()
    # base: C-clamp (white), the cone cover, the post
    A.lathe([(0, 0), (0.048, 0), (0.048, 0.004), (0.020, 0.032), (0.0145, 0.036), (0, 0.036)], seg, "white")
    A.lathe([(0, 0.03), (0.0125, 0.03), (0.0125, ARM_POST - 0.03), (0, ARM_POST - 0.03)], seg, "white")
    if not rough:
        yb = 0.045
        rbox(A, 0.055, 0.016, DESK_T + 0.020, 0.004, 0, 0, cs, "white", T(0, yb + 0.008, -DESK_T - 0.020))
        rbox(A, 0.055, yb + 0.03, 0.012, 0.005, 0.002, 0, cs, "white", T(0, yb / 2 - 0.008, -DESK_T - 0.020))
        A.lathe([(0, -0.085), (0.0055, -0.085), (0.0055, -DESK_T - 0.005), (0, -DESK_T - 0.005)], 16, "chrome")
        A.lathe([(0, -DESK_T - 0.005), (0.016, -DESK_T - 0.005), (0.016, -DESK_T), (0, -DESK_T)], seg, "rubber")
        A.lathe([(0, -0.095), (0.020, -0.095), (0.022, -0.090), (0.020, -0.082), (0, -0.082)], seg, "white")  # knob
        # the swivel collar at the post top
        A.lathe([(0, ARM_POST - 0.032), (0.016, ARM_POST - 0.032), (0.016, ARM_POST - 0.020), (0, ARM_POST - 0.020)],
                seg, "steel")
    static = fin(A, f"mic_static{sfx}", mp, coll, root, bevel=0.001, lite=lite)
    sw = empty(f"mic_j_swivel{sfx}", root, (0, 0, ARM_POST - 0.02), (0, 0, math.radians(pose["swivel"])), coll)
    A = P.Mesh()
    # the shoulder knuckle: a fork round the hinge
    for s in (-1, 1):
        cyl(A, ARM_HINGE_R * 0.85, (0, s * (ARM_W / 2 - 0.009), 0.02), (0, s * ARM_W / 2, 0.02), "white", seg)
    rbox(A, 0.036, ARM_W - 0.004, 0.022, 0.006, 0.004, 0, cs, "white", T(0, 0, 0))
    knuckle = fin(A, f"mic_arm_knuckle{sfx}", mp, coll, sw, bevel=0.001, lite=lite)
    sh = empty(f"mic_j_shoulder{sfx}", sw, (0, 0, 0.02), (0, -math.radians(pose["shoulder"]), 0), coll)

    def segment(name, L, parent):
        A = P.Mesh()
        cw, ch = ARM_COVER
        Mx = R(90, "Y")                          # local +Z -> +X (along the arm)
        rbox(A, ch, cw, L - 0.030, 0.012 if not rough else 0.0, 0.0, 0.0, cs, "white", Mx @ T(0, 0, 0.015))
        if not rough:
            for e in (0.0, L):                   # the hinge discs at both ends (outside the cover), screw heads
                for s in (-1, 1):
                    cyl(A, ARM_HINGE_R * (0.9 if e else 0.8), (e, s * 0.019, 0), (e, s * (ARM_W / 2 - 0.006), 0), "white", seg)
                    cyl(A, 0.006, (e, s * (ARM_W / 2 - 0.006), 0), (e, s * (ARM_W / 2 - 0.0045), 0), "chrome", 16)
            # the cable channel under the cover
            rbox(A, 0.010, 0.006, L - 0.06, 0.002, 0, 0, 2, "white", Mx @ T(-ch / 2 + 0.002, 0, 0.03))
        return fin(A, name, mp, coll, parent, bevel=0.0012, lite=lite)

    lower = segment(f"mic_arm_lower{sfx}", ARM_L1, sh)
    el = empty(f"mic_j_elbow{sfx}", sh, (ARM_L1, 0, 0), (0, -math.radians(pose["elbow"]), 0), coll)
    upper = segment(f"mic_arm_upper{sfx}", ARM_L2, el)
    level = math.radians(pose["shoulder"] + pose["elbow"])
    wr = empty(f"mic_j_wrist{sfx}", el, (ARM_L2, 0, 0), (0, level, 0), coll)
    wy = empty(f"mic_j_wrist_yaw{sfx}", wr, (0, 0, 0), (0, 0, math.radians(pose["wrist"])), coll)
    A = P.Mesh()
    # the head: a block hanging from the wrist hinge, a swivel, the 3/8 stud pointing down
    rbox(A, 0.030, 0.034, 0.040, 0.008, 0.006, 0.004, cs, "white", T(0, 0, -0.040))
    if not rough:
        A.lathe([(0, -0.050), (0.012, -0.050), (0.012, -0.040), (0, -0.040)], seg, "steel")
        A.lathe([(0, -ARM_TIP), (0.0045, -ARM_TIP), (0.0045, -0.050), (0, -0.050)], 16, "steel")
    tip = fin(A, f"mic_arm_tip{sfx}", mp, coll, wy, bevel=0.001, lite=lite)
    stem_top = empty(f"mic_j_mount{sfx}", wy, (0, 0, -ARM_TIP + 0.010), coll=coll)
    hang, tilt, head = build_mic_head(coll, mp, stem_top, rough, lite, sfx)
    tilt.rotation_euler = (math.radians(pose["tilt"]), 0, 0)
    out = {"mic_static": [static.name, knuckle.name], "mic_arm": [lower.name, upper.name, tip.name]}
    out.update(head)
    return root, out


def pose_mic(sfx, **angles):
    """Set the named joints of an existing obj_mic: swivel, shoulder, elbow, wrist, tilt (degrees)."""
    o = bpy.data.objects
    p = dict(POSE, **angles)
    o[f"mic_j_swivel{sfx}"].rotation_euler = (0, 0, math.radians(p["swivel"]))
    o[f"mic_j_shoulder{sfx}"].rotation_euler = (0, -math.radians(p["shoulder"]), 0)
    o[f"mic_j_elbow{sfx}"].rotation_euler = (0, -math.radians(p["elbow"]), 0)
    o[f"mic_j_wrist{sfx}"].rotation_euler = (0, math.radians(p["shoulder"] + p["elbow"]), 0)
    o[f"mic_j_wrist_yaw{sfx}"].rotation_euler = (0, 0, math.radians(p["wrist"]))
    o[f"mic_j_tilt{sfx}"].rotation_euler = (math.radians(p["tilt"]), 0, 0)
    bpy.context.view_layer.update()


def solve_mic(clamp, capsule, aim, yaw_root=0.0):
    """Joint angles that put the mic's pivot at `capsule` (world) with the foam pointed at `aim`,
    for an obj_mic at clamp=(x, y, desk z) whose root is turned yaw_root degrees. Elbow-up solution."""
    cx, cy, cz = clamp
    sh = Vector((cx, cy, cz + ARM_POST))
    hang = STEM[1] + YOKE_TOP + ARM_TIP - 0.010           # wrist hinge above the pivot
    W = Vector(capsule) + Vector((0, 0, hang))
    d = W - sh
    swivel = math.degrees(math.atan2(d.y, d.x)) - yaw_root
    h = math.hypot(d.x, d.y)
    v = d.z
    D = min(math.hypot(h, v), ARM_L1 + ARM_L2 - 1e-4)
    a = math.acos(max(-1, min(1, (ARM_L1 ** 2 + D ** 2 - ARM_L2 ** 2) / (2 * ARM_L1 * D))))
    base = math.atan2(v, h)
    shoulder = math.degrees(base + a)                       # elbow up
    ex, ez = ARM_L1 * math.cos(math.radians(shoulder)), ARM_L1 * math.sin(math.radians(shoulder))
    up = math.degrees(math.atan2(v - ez, h - ex))
    elbow = up - shoulder
    to = Vector(aim) - Vector(capsule)
    head_yaw = math.degrees(math.atan2(to.y, to.x))         # world direction the foam should face
    # the foam is local -Y in the wrist frame; the wrist frame's yaw is swivel + yaw_root + wrist
    wrist = head_yaw - (swivel + yaw_root) + 90.0
    tilt = -math.degrees(math.atan2(to.z, math.hypot(to.x, to.y)))   # + tips the foam down
    wrist = (wrist + 180) % 360 - 180
    return dict(swivel=swivel, shoulder=shoulder, elbow=elbow, wrist=wrist, tilt=tilt)


# ---------------------------------------------------------------------------
# 3. the whole set, laid out for the component stills (and, with a layout, for the room)
# ---------------------------------------------------------------------------
DEMO = dict(kl=[(0.0, 0.0, 0.0, 0.0), (0.95, 0.0, 0.0, 0.0)],          # (x, y, z desk, yaw)
            cam_clamp_z=0.42, cam_at=(0.12, -0.30, 0.42), cam_yaw=0.0,
            mic_clamp=(-0.55, 0.05, 0.0), mic_yaw=0.0, mic_pose=None,
            mic_capsule=(-0.20, -0.35, 0.33), mic_aim=(-0.20, -1.0, 0.45))


def build(rough=False, lite=False, collection=None, layout=None):
    lay = dict(DEMO, **(layout or {}))
    sfx = "_lite" if lite else ""
    coll = collection or bpy.context.scene.collection
    mp = mats()
    names = {}

    def add(d):
        for k, v in d.items():
            names.setdefault(k, []).extend(v)
    if PART == "camera":
        cam, d = build_camera(coll, mp, rough, lite, sfx)
        add(d)
        bpy.context.view_layer.update()
        names["all"] = sorted({n for v in d.values() for n in v})
        return names
    kls = []
    for i, (x, y, z, yaw) in enumerate(lay["kl"], 1):
        root, d = build_keylight(i, coll, mp, rough, lite, pole_h=lay.get("pole_h", POLE_H),
                                 tilt=lay.get("kl_tilt", 0.0), sfx=sfx)
        root.location = (x, y, z)
        root.rotation_euler = (0, 0, math.radians(yaw))
        kls.append(root)
        add({f"keylight_{i}": [n for v in d.values() for n in v]})
        add(d)
    # camera on the flex arm from key light 1's pole
    x, y, z, _ = lay["kl"][0]
    cam, d = build_camera(coll, mp, rough, lite, sfx)
    cx, cy, cz = lay["cam_at"]
    cam.location = (cx, cy, cz)
    cam.rotation_euler = (math.radians(lay.get("cam_pitch", 0.0)), 0, math.radians(lay["cam_yaw"]))
    bpy.context.view_layer.update()
    add(d)
    zc = z + lay["cam_clamp_z"]
    out_dir = Vector((cx - x, cy - y, 0))
    out_dir = out_dir.normalized() if out_dir.length > 1e-6 else Vector((0, -1, 0))
    start = Vector((x, y, zc)) + out_dir * (POLE_R[0] + 0.030)
    arm, pts = build_flexarm(coll, mp, (x, y, z), POLE_R[0], start, (cx, cy, cz - 0.004), lite, rough, sfx)
    add({"cam_arm": [arm.name]})
    # the mic
    mx, my, mz = lay["mic_clamp"]
    pose = lay["mic_pose"] or solve_mic(lay["mic_clamp"], lay["mic_capsule"], lay["mic_aim"], lay["mic_yaw"])
    mic, d = build_mic(coll, mp, rough, lite, pose, sfx)
    mic.location = (mx, my, mz)
    mic.rotation_euler = (0, 0, math.radians(lay["mic_yaw"]))
    add(d)
    bpy.context.view_layer.update()
    names["mic_pose"] = [json.dumps({k: round(v, 1) for k, v in pose.items()})]
    names["flex_reach"] = [f"{(Vector(pts[-1]) - Vector(pts[0])).length:.3f}"]
    names["all"] = sorted({n for k, v in names.items() if k not in ("mic_pose", "flex_reach", "all") for n in v
                           if n in bpy.data.objects and bpy.data.objects[n].type == "MESH"})
    return names


def build_set(layout, collection=None, lite=False):
    """For the room test: the whole set at room coordinates (layout keys as DEMO)."""
    return build(False, lite, collection, layout)


# ---------------------------------------------------------------------------
# 4. the photo views
# ---------------------------------------------------------------------------
def outline_views(names):
    v = []
    if PART == "camera":
        return [x for x in _all_views(names) if x["name"].startswith("camera-")]
    return _all_views(names)


def _all_views(names):
    v = []
    if PART == "camera":
        names = dict(names, kl_panel=[], kl_glow=[], kl_static=[], mic_body=[], mic_yoke=[], mic_arm=[], mic_static=[])
    kl = names["kl_panel"][:1] + names["kl_glow"][:1] + [n for n in names["kl_static"] if "_mount" in n][:1]
    kl = [n for n in kl if n.startswith("keylight_1")]
    v.append(dict(name="keylight-front", title="Key Light: front (Elgato render) vs our model",
                  photo=os.path.join(R_KL, "front-on-pole.jpg"), mask=0.5, crop=(800, 2020, 360, 1560),
                  objects=kl, camera={"mode": "fit", "view": "front"}))
    v.append(dict(name="keylight-side", title="Key Light: side (Elgato render) vs our model",
                  photo=os.path.join(R_KL, "side.jpg"), mask=0.5, crop=(1200, 1700, 290, 1560),
                  objects=kl, camera={"mode": "fit", "view": "right", "tilts": [-3.0, 0.0, 3.0]}))
    cam = names["cam_body"] + names["cam_lens"] + names["cam_screen"]
    v.append(dict(name="camera-front", title="ZV-E10 II: front, screen flipped (Sony image) vs our model",
                  photo=os.path.join(R_CAM, "front-windscreen-official-henrys.png"), mask=0.85,
                  crop=(150, 1900, 812, 1420), objects=cam, camera={"mode": "fit", "view": "front"},
                  explain="the supplied fur windscreen on the hot shoe is cropped out of the photo (not modelled)"))
    v.append(dict(name="camera-top", title="ZV-E10 II: top (review photo) vs our model",
                  photo=os.path.join(CUT, "top-pb-traced.png"), mask="alpha", objects=names["cam_body"] + names["cam_lens"],
                  prepare=hide_screen(), camera={"mode": "free", "view": "top", "yaws": [170, 180, 190],
                                                 "tilts": [-35.0, -28.0, -21.0, -14.0], "h_range": (-0.3, 0.3)},
                  explain="perspective review photo, the silhouette hand-traced (polygon) from top-pb.jpg"))
    v.append(dict(name="camera-side", title="ZV-E10 II: screen side, screen closed (review photo) vs our model",
                  photo=os.path.join(CUT, "side-screen-card-slot-pb-cut.png"), mask="alpha",
                  objects=names["cam_body"] + names["cam_lens"], prepare=hide_screen(),
                  camera={"mode": "free", "view": "back", "yaws": [-40, -30, -20], "tilts": [10.0, 20.0, 30.0]},
                  explain="perspective review photo on a lace table (colour-keyed cutout, ragged at the grip and the card door); the photo's screen is closed, ours is hidden"))
    mic = [n for n in names["mic_body"] + names["mic_yoke"] + names.get("mic_led", [])]
    v.append(dict(name="mic-back", title="MV7+ white: back (Shure image) vs our model",
                  photo=os.path.join(R_MIC, "back.png"), mask="alpha", crop=(0, 3000, 240, 3000),
                  objects=mic, prepare=mic_view("back"), camera={"mode": "fit", "view": "back"},
                  explain="the photo's stem runs off the top edge; the crop starts under the stem block"))
    v.append(dict(name="mic-front", title="MV7+ white: front, hanging (Shure image) vs our model",
                  photo=os.path.join(R_MIC, "front.png"), mask="alpha", crop=(0, 3000, 120, 3000),
                  objects=mic, prepare=mic_view("front"),
                  camera={"mode": "free", "view": "front", "yaws": [-6.0, 0.0, 6.0], "tilts": [-10.0, 0.0, 10.0],
                          "h_range": (-0.2, 0.2)}))
    v.append(dict(name="mic-side", title="MV7+ white: side, upright (retail photo) vs our model",
                  photo=os.path.join(R_MIC, "side-profile-yoke-open.jpg"), mask=0.93, objects=names["mic_body"],
                  prepare=mic_view("side"), camera={"mode": "fit", "view": "right"},
                  explain="white body on a white page: the threshold mask loses the lit edge; the yoke is swung open in the photo, ours is hidden"))
    v.append(dict(name="arm-side", title="PSA1+ white: folded, side (RODE image) vs our model",
                  photo=os.path.join(R_ARM, "white-folded-side-2000.png"), mask="alpha",
                  objects=names["mic_arm"] + [n for n in names["mic_static"] if "knuckle" in n],
                  prepare=arm_folded(), camera={"mode": "fit", "view": "front", "tilts": [-4.0, 0.0, 4.0]},
                  explain="RODE's folded shot lies the arm on its side without the clamp; the head's swivel differs"))
    only = os.environ.get("ARMS_VIEWS")
    if only:
        v = [x for x in v if x["name"] in only.split(",")]
    return v


def _sfx_of(name):
    return "_lite" if name.endswith("_lite") else ""


def hide_screen():
    def prep():
        o = [x for x in bpy.data.objects if x.name.startswith("cam_screen")]
        st = [(x, x.hide_render) for x in o]
        for x in o:
            x.hide_render = True
        return lambda: [setattr(x, "hide_render", h) for x, h in st]
    return prep


def mic_view(which):
    """Turn the mic head into the photo's pose: back (axis toward the camera), front (hanging, the foam
    toward the camera and a little down), side (upright: foam up, seen from the side)."""
    def prep():
        o = bpy.data.objects
        root, tilt, hang = o["obj_mic"], o["mic_j_tilt"], o["mic_j_stem"]
        saved = (root.matrix_world.copy(), tilt.rotation_euler.copy(), hang.matrix_world.copy())
        hang.parent = None
        if which == "back":
            hang.matrix_world = Matrix.Rotation(math.radians(180), 4, "Z")
            tilt.rotation_euler = (0, 0, 0)
        elif which == "front":
            hang.matrix_world = Matrix.Identity(4)
            tilt.rotation_euler = (math.radians(35), 0, 0)
        else:
            hang.matrix_world = Matrix.Identity(4)
            tilt.rotation_euler = (math.radians(-90), 0, 0)
        bpy.context.view_layer.update()

        def undo():
            hang.parent = o["mic_j_mount"]
            hang.matrix_parent_inverse = Matrix.Identity(4)
            hang.matrix_basis = Matrix.Identity(4)
            tilt.rotation_euler = saved[1]
            bpy.context.view_layer.update()
        return undo
    return prep


def arm_folded():
    def prep():
        o = bpy.data.objects
        old = {k: o[k].rotation_euler.copy() for k in ("mic_j_swivel", "mic_j_shoulder", "mic_j_elbow", "mic_j_wrist")}
        pose_mic("", swivel=0, shoulder=8, elbow=-172, wrist=0, tilt=0)

        def undo():
            for k, r in old.items():
                o[k].rotation_euler = r
            bpy.context.view_layer.update()
        return undo
    return prep


# ---------------------------------------------------------------------------
# 5. stages
# ---------------------------------------------------------------------------
def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {NAME}: {msg}", flush=True)


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")


def stage_outline(out):
    import outline_check
    clear()
    holder = {}

    def b(rough=True):
        holder["n"] = build(rough=True)
        return {k: v for k, v in holder["n"].items() if k not in ("mic_pose", "flex_reach")}
    return outline_check.run(NAME, b, outline_views, os.path.join(out, "outline"), log=log)


def stage_build(out):
    clear()
    t = time.time()
    names = build()
    blend = os.path.join(BLENDER_DIR, "out", "components", f"{NAME}.blend")
    os.makedirs(os.path.dirname(blend), exist_ok=True)
    with open(os.path.join(out, f"{NAME}-names.json"), "w") as f:
        json.dump(names, f, indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    log(f"built in {time.time() - t:.1f} s, saved {blend}; pose {names.get('mic_pose')} flex {names.get('flex_reach')}")
    return names


def _studio(sc, cycles, strength=1.0):
    from lib import compare
    compare.ensure_studio(strength)
    sc.render.film_transparent = False
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGB"
    sc.view_settings.view_transform = "AgX"
    if cycles:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 96
        sc.cycles.use_denoising = True
        try:
            sc.cycles.device = "GPU"
        except Exception:
            pass
    else:
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = 32


def _shoot(sc, cam, path, cycles, label):
    from lib import renderqueue
    sc.camera = cam
    sc.render.filepath = path
    if cycles:
        with renderqueue.slot(f"{NAME} {label}"):
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(write_still=True)


def look_cam(name, pos, target, lens=50, ortho=None):
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.005
    cd.clip_end = 50
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    cam = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if cam.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(cam)
    d = Vector(target) - Vector(pos)
    cam.location = pos
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return cam


def stage_stills(out, names, cycles=False):
    sc = bpy.context.scene
    _studio(sc, cycles, 0.45)        # the toolkit studio at full strength greys a small black object
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    from lib import compare
    lo, hi = compare.world_bbox(names["all"])
    c = (lo + hi) / 2
    k = max(hi - lo) * 3.2
    shots = {"hero": look_cam("still_hero", (c.x - 0.35 * k, c.y - 0.9 * k, c.z + 0.4 * k), c, 50),
             "front": look_cam("still_front", (c.x, c.y - 6, c.z), c, ortho=max((hi - lo).x, (hi - lo).z * 16 / 9) * 1.1),
             "side": look_cam("still_side", (c.x + 6, c.y, c.z), c, ortho=max((hi - lo).y, (hi - lo).z * 16 / 9) * 1.4),
             "top": look_cam("still_top", (c.x, c.y, c.z + 6), c, ortho=max((hi - lo).x, (hi - lo).y * 16 / 9) * 1.1)}
    paths = {}
    only = os.environ.get("ARMS_STILLS")
    for k, cam in shots.items():
        if only and k not in only.split(","):
            continue
        p = os.path.join(out, f"{NAME}-{k}{'-cycles' if cycles else ''}.png")
        _shoot(sc, cam, p, cycles, k)
        paths[k] = p
    log(f"stills: {paths}")
    return paths


# close-up pairs: (name, title, photo, camera pos, target, lens), positions relative to object origins
def closeup_specs():
    o = bpy.data.objects
    if PART == "camera":
        cam = o["cam"].matrix_world
        return [
            ("cam-lens", "ZV-E10 II: the lens front", os.path.join(R_CAM, "front-lens-pb.jpg"),
             cam @ Vector((0.05, -0.30, 0.10)), cam @ Vector((0.0, -0.03, LENS_Z)), 50),
            ("cam-top", "ZV-E10 II: the top dials", os.path.join(R_CAM, "top-pb.jpg"),
             cam @ Vector((-0.02, 0.10, 0.32)), cam @ Vector((-0.015, 0.0, CB_H)), 50),
            ("cam-screen", "ZV-E10 II: the flipped screen", os.path.join(R_CAM, "front-screen-selfie-pb.jpg"),
             cam @ Vector((0.16, -0.30, 0.13)), cam @ Vector((0.03, 0.0, 0.03)), 50),
            ("cam-grip", "ZV-E10 II: the grip side", os.path.join(R_CAM, "three-quarter-grip-side-pb.jpg"),
             cam @ Vector((-0.26, -0.22, 0.10)), cam @ Vector((-0.035, 0.0, 0.032)), 50),
            ("cam-mount", "ZV-E10 II: the lens mount and the body front", os.path.join(R_CAM, "front-body-hires-commons.jpg"),
             cam @ Vector((-0.10, -0.30, 0.12)), cam @ Vector((-0.01, -0.02, 0.035)), 50),
            ("cam-back", "ZV-E10 II: the back (screen out, bay empty)", os.path.join(R_CAM, "back-screen-swung-out-pb.jpg"),
             cam @ Vector((0.10, 0.32, 0.10)), cam @ Vector((0.0, 0.0, 0.032)), 50),
        ]
    kl = o["keylight_1"].matrix_world
    cam = o["cam"].matrix_world
    mic = o["mic_j_tilt"].matrix_world
    arm = o["obj_mic"].matrix_world
    zp = POLE_H + KL_ADAPT[1] + KL_NECK[1]
    sh = o["mic_j_shoulder"].matrix_world.translation
    el = o["mic_j_elbow"].matrix_world.translation
    return [
        ("kl-edge", "Key Light: the panel's edge and lip", os.path.join(R_KL, "three-quarter.jpg"),
         kl @ Vector((-0.45, -0.55, zp + 0.30)), kl @ Vector((0.0, 0, zp + KL_H / 2)), 50),
        ("kl-back", "Key Light: the back and its box", os.path.join(R_KL, "back-in-use.jpg"),
         kl @ Vector((0.35, 0.65, zp + 0.45)), kl @ Vector((0, 0, zp + KL_H / 2)), 50),
        ("kl-clamp", "Key Light: the desk clamp and the lower pole", os.path.join(R_KL, "pole-clamp-hero.jpg"),
         kl @ Vector((0.25, -0.30, 0.10)), kl @ Vector((0, 0.01, -0.01)), 50),
        ("cam-lens", "ZV-E10 II: the lens front", os.path.join(R_CAM, "front-lens-pb.jpg"),
         cam @ Vector((0.05, -0.30, 0.10)), cam @ Vector((0.0, -0.03, LENS_Z)), 50),
        ("cam-top", "ZV-E10 II: the top dials", os.path.join(R_CAM, "top-pb.jpg"),
         cam @ Vector((-0.02, 0.13, 0.30)), cam @ Vector((-0.02, 0.0, CB_H)), 50),
        ("cam-screen", "ZV-E10 II: the flipped screen", os.path.join(R_CAM, "front-screen-selfie-pb.jpg"),
         cam @ Vector((0.18, -0.30, 0.12)), cam @ Vector((0.04, 0.0, 0.03)), 50),
        ("mic-led", "MV7+: the LED ring and the foam", os.path.join(R_MIC, "detail-led-ring-windscreen.jpg"),
         mic @ Vector((0.12, -0.22, 0.05)), mic @ Vector((0, -0.03, 0)), 50),
        ("mic-grille", "MV7+: the foam's front", os.path.join(R_MIC, "front-bottom-view-white-1500.png"),
         mic @ Vector((0.0, -0.45, -0.05)), mic @ Vector((0, -0.05, 0.0)), 50),
        ("mic-yoke", "MV7+: the yoke, knobs and stem", os.path.join(R_MIC, "side-tilted-back-ports.jpg"),
         mic @ Vector((0.30, 0.10, 0.12)), mic @ Vector((0, 0.0, 0.05)), 50),
        ("mic-rear", "MV7+: the rear ports", os.path.join(R_MIC, "back-straight-white-1500.png"),
         mic @ Vector((0.0, 0.40, 0.04)), mic @ Vector((0, 0.05, 0.0)), 50),
        ("arm-joints", "PSA1+: the elbow hinge", os.path.join(R_ARM, "white-three-quarter-extended-2000.png"),
         el + Vector((0.20, -0.35, 0.10)), el, 50),
        ("arm-springs", "PSA1+: the shoulder knuckle (springs are inside the covers)",
         os.path.join(R_ARM, "white-folded-side-2000.png"), sh + Vector((0.25, -0.40, 0.12)), sh, 50),
        ("arm-clamp", "PSA1+: the clamp and the cone", os.path.join(R_ARM, "detail-white-clamp-mount.jpg"),
         arm @ Vector((0.25, -0.35, 0.10)), arm @ Vector((0, 0.01, 0.0)), 50),
    ]


def stage_closeups(out, names, cycles=False, only=None):
    sc = bpy.context.scene
    _studio(sc, cycles, 0.45)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 720, 100
    d = os.path.join(out, "closeups")
    os.makedirs(d, exist_ok=True)
    pairs = []
    for key, title, photo, pos, tgt, lens in closeup_specs():
        if only and key not in only:
            continue
        cam = look_cam(f"still_cu_{key.replace('-', '_')}", pos, tgt, lens)
        p = os.path.join(d, f"{key}.png")
        _shoot(sc, cam, p, cycles, key)
        pairs.append(dict(key=key, title=title, photo=photo, render=p))
    jp = os.path.join(d, "pairs.json")
    with open(jp, "w") as f:
        json.dump(pairs, f, indent=1)
    import subprocess
    subprocess.run(["/opt/anaconda3/bin/python3", os.path.abspath(__file__), "--pairs", jp, d], check=False)
    log(f"close-ups: {len(pairs)} in {d}")
    return pairs


def pairs_sheet(jp, d):
    from PIL import Image, ImageDraw
    pairs = json.load(open(jp))
    W, H = 1600, 600
    rows = []
    for p in pairs:
        row = Image.new("RGB", (W, H + 40), (24, 24, 26))
        dr = ImageDraw.Draw(row)
        dr.text((12, 10), p["title"] + "   (left: reference photo, right: our model)", fill=(235, 235, 235))
        for i, f in enumerate((p["photo"], p["render"])):
            im = Image.open(f)
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[3])
                im = bg
            im = im.convert("RGB")
            im.thumbnail((W // 2 - 20, H))
            row.paste(im, (i * W // 2 + 10, 40))
        row.save(os.path.join(d, f"{p['key']}-pair.jpg"), quality=88)
        rows.append(row)
    for k in range(0, len(rows), 4):
        part = rows[k:k + 4]
        s = Image.new("RGB", (W, sum(r.height for r in part)))
        y = 0
        for r in part:
            s.paste(r, (0, y))
            y += r.height
        s.save(os.path.join(d, f"closeups-sheet-{k // 4 + 1}.jpg"), quality=85)
    print("SHEETS", d)


def stage_compare(out, names):
    from lib import compare
    rep = compare.run(outline_views(names), os.path.join(out, "compare"), NAME, log=log)
    log(f"compare test {'PASSED' if rep['test']['passed'] else 'FAILED'}: {rep['paths']['md']}")
    return rep["test"]


def _export(objs, path):
    from lib import run
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select_set(o.name in objs)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_cameras=False, export_lights=False, export_extras=False)
    return run.glb_stats(path)


def _with_empties(names):
    keep = set(names)
    for o in bpy.data.objects:
        if o.name in keep:
            p = o.parent
            while p is not None:
                keep.add(p.name)
                p = p.parent
    return keep


def stage_export(out, names):
    d = os.path.join(BLENDER_DIR, "out", "components")
    os.makedirs(d, exist_ok=True)
    rich = _export(_with_empties(names["all"]), os.path.join(d, f"{NAME}-rich.glb"))
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    lite_names = build(lite=True)
    lite = _export(_with_empties(lite_names["all"]), os.path.join(d, f"{NAME}-lite.glb"))
    log(f"GLB rich {rich['kb']} KB {rich['triangles']} tris; lite {lite['kb']} KB {lite['triangles']} tris")
    return {"rich": rich, "lite": lite}


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    st = next((x for x in a if not x.startswith("--") and os.path.sep not in x), "default")
    stages = ["build", "stills", "compare", "closeups", "export"] if st == "default" else st.split(",")
    out = next((a[i + 1] for i, x in enumerate(a) if x == "--out"), None) or os.path.join(
        REPO, "video-local", "footage", "2026-10-26-components", "arms")
    os.makedirs(out, exist_ok=True)
    rep = {"stages": stages}
    t0 = time.time()
    names = None
    out = out if PART == "all" else os.path.join(out, PART)
    os.makedirs(out, exist_ok=True)
    cycles = "--cycles" in a or os.environ.get("ARMS_CYCLES") == "1"
    if "outline" in stages:
        r = stage_outline(out)
        rep["outline"] = {"passed": r["test"]["passed"], "sheet": r.get("sheet")}
    if "build" in stages:
        names = stage_build(out)
    elif any(s in stages for s in ("stills", "compare", "export", "closeups")):
        bpy.ops.wm.open_mainfile(filepath=os.path.join(BLENDER_DIR, "out", "components", f"{NAME}.blend"))
        names = json.load(open(os.path.join(out, f"{NAME}-names.json")))
    if "stills" in stages:
        rep["stills"] = stage_stills(out, names, cycles)
    if "compare" in stages:
        rep["compare"] = stage_compare(out, names)
    if "closeups" in stages:
        only = os.environ.get("ARMS_CU")
        rep["closeups"] = stage_closeups(out, names, cycles, only.split(",") if only else None)
    if "export" in stages:
        rep["export"] = stage_export(out, names)
    rep["total_s"] = round(time.time() - t0, 1)
    with open(os.path.join(out, f"{NAME}-report{'-' + st if st != 'default' else ''}.json"), "w") as f:
        json.dump(rep, f, indent=1, default=str)
    log(f"done in {rep['total_s']} s: {out}")


def make_cutouts():
    """Plain Python (Pillow, numpy, scipy): the camera compare's silhouettes, written to CUT (never touches
    the photos): top-pb-traced.png (a hand-traced polygon) and side-screen-card-slot-pb-cut.png (colour key,
    largest dark part, closed and filled).  /opt/anaconda3/bin/python3 blender/components/arms.py --cutouts"""
    import numpy as np
    from PIL import Image, ImageDraw
    from scipy import ndimage as nd
    os.makedirs(CUT, exist_ok=True)
    im = Image.open(os.path.join(R_CAM, "top-pb.jpg")).convert("RGB")
    poly = [(72, 82), (100, 57), (150, 45), (200, 42), (250, 45), (300, 56), (326, 80), (332, 198), (352, 198),
            (360, 160), (376, 128), (405, 115), (450, 112), (485, 119), (505, 140), (518, 175), (522, 250),
            (526, 350), (512, 376), (60, 378), (42, 360), (42, 200), (72, 190)]
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    im.putalpha(m)
    im.save(os.path.join(CUT, "top-pb-traced.png"))
    a = np.asarray(Image.open(os.path.join(R_CAM, "side-screen-card-slot-pb.jpg")).convert("RGB")) / 255.0
    k = (a.mean(-1) < 0.20) & ((a.max(-1) - a.min(-1)) < 0.12)
    k = nd.binary_closing(k, iterations=6)
    lab, n = nd.label(k)
    k = lab == (np.argmax(nd.sum(k, lab, range(1, n + 1))) + 1)
    k = nd.binary_opening(nd.binary_fill_holes(k), iterations=3)
    Image.fromarray(np.dstack([a * 255, k * 255]).astype(np.uint8), "RGBA").save(
        os.path.join(CUT, "side-screen-card-slot-pb-cut.png"))
    print("CUTOUTS", CUT)


if __name__ == "__main__":
    if bpy is not None:
        main()
        bpy.ops.wm.quit_blender()
    elif "--cutouts" in sys.argv:
        make_cutouts()
    elif "--pairs" in sys.argv:
        i = sys.argv.index("--pairs")
        pairs_sheet(sys.argv[i + 1], sys.argv[i + 2])
