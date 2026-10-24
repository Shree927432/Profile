"""desk: the AI lab's desk as a kit (component, 2026-10-24).

  ALEX      one IKEA ALEX drawer unit, white, 36 x 58 x 70 cm, as an exact replica: the carcass (top,
            sides, bottom, finished back), five drawers (front with the curved finger-pull cut-out, a
            drawer box behind it), the four small black feet under the recessed plinth, the runners.
            Every drawer is its own object (one material), origin on its front face at the bottom
            centre, so the room code can slide it open along the unit's local -Y.
  top       a parametric L desk top in the white of IKEA LAGKAPTEN: one continuous slab, 35 mm, edges
            rounded as the real top, small outer corner radii and a small inner-corner radius. The
            arms default to room plan v3 (blender/lib/plan_v3.py, read only).
  LED       a white-blue strip under the front edges (plan v3: 5 cm in), in the knee spaces.

Built from scratch at real size, in metres. Frame: Blender, Z up, the floor at z = 0.
  - the single unit (root `alex`): centred on the origin, front at -Y.
  - the L desk (root `desk`, set_desk): origin on the floor in the corner of the left and back walls
    (plan v3's (-RX, RY)), axes as the room (back wall +Y, left wall -X): place it in the room at
    (-RX, RY, 0) with no rotation. Its units: `desk_drawers_01` (main run, faces +X), `_02`, `_03`
    (the return, face -Y), left to right as seen from the room.
  - `cmp200`: IKEA's own 200 x 60 LAGKAPTEN/ALEX layout built from the same kit, only for the photo
    compare against IKEA's 3D file.

Numbers: OFFICIAL = IKEA's page or drawing (docs/moodboard/local/ai-lab/01-desk/SOURCES.md);
MEASURED = measured on IKEA's photos (scale from the official sizes, the front column rectified with
lib/refs.rectify) or on IKEA's own 3D file (ikea-3d/, reference only, never copied); EST = estimated.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/components/desk.py -- refviews
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/tools/outline_check.py -- blender/components/desk.py
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/components/desk_render.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(BLENDER_DIR, ".."))
sys.path.insert(0, BLENDER_DIR)
sys.path.insert(0, os.path.join(BLENDER_DIR, "tools"))

try:
    import bpy
    from mathutils import Matrix, Vector
except ImportError:          # plain Python imports the numbers (the blueprint)
    bpy = None

NAME = "desk"
MM = 0.001
REF = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab", "01-desk")
IKEA_GLB = os.path.join(REF, "ikea-3d", "lagkapten-alex-200x60.glb")
FOOTAGE = os.path.join(REPO, "video-local", "footage", "2026-10-24-components", NAME)
IKEA_VIEWS = os.path.join(FOOTAGE, "ikea-views")     # renders of IKEA's file: local reference only

# ---------------------------------------------------------------------------
# ALEX drawer unit (mm in this block)
# ---------------------------------------------------------------------------
AW, AD, AH = 360.0, 580.0, 700.0   # OFFICIAL: 36 x 58 x 70 cm (IKEA US page; IKEA's file 362.7 x 583 x 700)
FOOT_H = 12.0          # MEASURED: IKEA's file, the carcass bottom at z 12 (photo: about 12 under the plinth)
FOOT_D = 19.0          # MEASURED: IKEA's file, feet 18 to 20 across (photo: about 30 px at 1.5 px/mm)
FOOT_IN = (21.0, 20.0) # MEASURED: foot centres in from the side and from the front/back: IKEA's file (21, 20) and
                       # the packshot's two front feet solved for the fitted turn (20, 19.5); round 1 had EST (32, 34)
PANEL_T = 15.0         # OFFICIAL: 36 - 33 cm (drawing: the drawer column is 33 wide) = 2 x 15 sides
TOP_PANEL_T = 15.0     # MEASURED: IKEA's file 685 to 700; photo 14.5 (24 px at 1.65 px/mm)
BOT_PANEL_T = 16.0     # MEASURED: IKEA's file 12 to 28; photo 16 (26 px)
BACK_T = 16.0          # MEASURED: IKEA's file, the finished back 274 to 290 (IKEA: "finished on the back")
EDGE_R = 0.6           # EST: the carcass's painted edges read crisp in the close-ups (round 1 had 1.0)
OPEN_Z0 = FOOT_H + BOT_PANEL_T          # 28: the opening between bottom and top panels
OPEN_Z1 = AH - TOP_PANEL_T              # 685
FRONT_W_GAPPED = AW - 2 * PANEL_T       # 330 between the sides
FRONT_T = 17.0         # MEASURED: IKEA's file, fronts y -290 to -273
FRONT_RECESS = 0.5     # EST: fronts sit just behind the carcass edges (IKEA's file: flush within 1 mm)
FRONT_EDGE_R = 0.6     # EST: crisp painted edges; the close-ups show a sharp edge and the cut face as a grey band
                       # (round 1 had 1.5: a soft white rim hid the cut face)
# Front heights, MEASURED on alex-three-quarter.jpg rectified square-on (refs.rectify, 0.25 mm/px, the
# gap centres scaled to IKEA's 327.5 x 654.5): pitches 103.8, 103.5, 148.8, 148.9, 149.2 mm, so a small
# front plus its gap is 103.65 and a large one 149.0; IKEA's file: 101 and 147.
FRONT_SMALL, FRONT_LARGE = 101.15, 146.5
FRONT_H = [FRONT_SMALL, FRONT_SMALL, FRONT_LARGE, FRONT_LARGE, FRONT_LARGE]   # top to bottom
GAP = ((OPEN_Z1 - OPEN_Z0) - sum(FRONT_H)) / 6.0   # 2.53: six equal gaps (top, four between, bottom)
FRONT_W = FRONT_W_GAPPED - 2 * GAP                 # 324.9
# The finger-pull cut-out in each front's top edge, MEASURED on the rectified photo (the same on all
# five fronts within 0.4 mm): symmetric, a flat bottom 23.2 deep for +-30 mm, then a cosine S-curve up
# to the top edge at +-92 mm (fits the trace within 0.4 mm). IKEA's low-poly file: 168 wide, 22 deep.
CUT_DEPTH, CUT_FLAT, CUT_END = 23.2, 30.0, 92.0
CUT_EDGE_R = 1.0       # EST: the cut edge on the front face is softly rounded
# Drawer boxes: OFFICIAL drawing 30 cm wide outside, 52 cm, 8 cm (small) and 12 cm (large) high;
# depth MEASURED on IKEA's file (box back outer face at y 262, 16 thick).
BOX_W, BOX_SIDE_T, BOX_BACK_Y, BOX_BACK_T = 300.0, 12.0, 262.0, 16.0
BOX_H = {FRONT_SMALL: 80.0, FRONT_LARGE: 120.0}
BOX_UP = 5.0           # EST: the box sides start 5 mm above the front's bottom edge
BOX_BOTTOM_T, BOX_BOTTOM_UP = 6.0, 10.0   # MEASURED (IKEA's file, the double line 6 mm), EST groove height
RUNNER = (12.0, 500.0, 30.0)               # EST: runner width, length, height (open photos); set 50 back
DRAWER_TRAVEL = 0.40   # EST metres: how far a drawer slides open (alex-detail-drawer-open.jpg)
# The drawer box's surfaces carry a face attribute `inside` (1) that darkens the white to BOX_SHADE: every
# photo (IKEA's packshots, the owner's) shows the cut-outs nearly black, while a pure white box behind
# them, lit through the cut-outs, renders mid grey (round 2). One material per drawer stays.
BOX_SHADE = 0.42       # EST: linear multiplier, tuned on the close-up sheet

# ---------------------------------------------------------------------------
# LAGKAPTEN top
# ---------------------------------------------------------------------------
TOP_T = 35.0           # MEASURED: IKEA's file 700.2 to 735.5 = 35.3 (IKEA SA page 3.4 cm; plan v3 3.5)
TOP_EDGE_R = 2.0       # EST: the plastic edge band's rounding (highlight line, lagkapten-top-three-quarter.jpg)
TOP_CORNER_R = 3.0     # EST: the outer corners in plan ("tiny rounded corners", SOURCES.md)
TOP_INNER_R = 8.0      # EST: the L's inner corner, one router pass
# LED strip (plan v3: under both front edges, 5 cm in). EST size: a flat diffused strip.
LED_W, LED_T = 16.0, 5.0
LED_COLOUR = "#8fd0ff"  # EST: the owner's photo's white-blue under the front edge
LED_STRENGTH = 450.0   # EST: bright enough to wash the wall and floor below, as in the photo (round 1 had 30: no glow)

# The desk's plan from room plan v3 (read only), in the desk's frame (wall corner at the origin)
try:
    from lib import plan_v3 as P3
    _RX, _RY = P3.RX, P3.RY
    MAIN_LEN, MAIN_D, RET_D = P3.MAIN_LEN, P3.MAIN_D, P3.RET_D       # 1.85, 0.80, 0.60
    RET_REACH = P3.RET["x1"] + _RX                                     # 1.82 from the left wall
    DRAWERS_AT = [(x + _RX, y - _RY, yaw) for x, y, yaw in P3.DRAWERS]
    LED_IN = P3.LED_IN
    TOP_Z = P3.TOP
except Exception:            # plan v3 unreadable: its numbers on 2026-10-24
    MAIN_LEN, MAIN_D, RET_D, RET_REACH, LED_IN, TOP_Z = 1.85, 0.80, 0.60, 1.82, 0.05, 0.735
    DRAWERS_AT = [(0.50, -1.66, 90), (0.99, -0.30, 0), (1.63, -0.30, 0)]

DESK_AT = (1.5, 1.0, 0.0)    # where the L desk stands in the build file (the unit is at the origin)
CMP_AT = (0.0, 3.0, 0.0)     # IKEA's 200 x 60 layout for the compare
CMP_TOP = (2000.0, 600.0)    # OFFICIAL: LAGKAPTEN 200 x 60
CMP_UNIT_X = 810.0           # MEASURED: IKEA's file, the units' centres at x +-810, centred in depth
LAG_AT = (0.0, -3.0, 0.0)    # LAGKAPTEN tops alone, for the compare against IKEA's packshot of the top
LAG_SIZES = (1000.0, 1200.0, 1400.0)  # OFFICIAL 60 deep tops; the packshot's size is not given: all fitted


def front_z():
    """Bottom z (mm) of each front, top to bottom."""
    z, out = OPEN_Z1, []
    for h in FRONT_H:
        z -= GAP + h
        out.append(z)
    return out


def cut_profile(n_curve=14):
    """The front's top edge with the cut-out, from right to left: [(x, depth below the top edge)] in mm."""
    pts = []
    for i in range(n_curve + 1):
        x = CUT_END - (CUT_END - CUT_FLAT) * i / n_curve
        t = (CUT_END - x) / (CUT_END - CUT_FLAT)
        pts.append((x, CUT_DEPTH * (1 - math.cos(math.pi * t)) / 2))
    left = [(-x, d) for x, d in reversed(pts)]
    return pts + left


def front_outline(h, n_curve=14):
    """A front's face outline (x across, z up, mm, z from its bottom edge), CCW."""
    w = FRONT_W / 2
    top = [(x, h - d) for x, d in cut_profile(n_curve)]
    return [(-w, 0.0), (w, 0.0), (w, h)] + top + [(-w, h)]


def l_outline(main_len=None, main_d=None, ret_d=None, reach=None, n_corner=6, n_inner=8):
    """The L top in plan (m, desk frame: wall corner at the origin, the main run along -Y on the left
    wall, the return along +X on the back wall), CCW, corners rounded."""
    L, D, Rd, X = (main_len or MAIN_LEN), (main_d or MAIN_D), (ret_d or RET_D), (reach or RET_REACH)
    rc, ri = TOP_CORNER_R * MM, TOP_INNER_R * MM
    # corners in order (CCW seen from above): (point, convex?)
    cs = [((0.0, -L), True), ((D, -L), True), ((D, -Rd), False), ((X, -Rd), True), ((X, 0.0), True), ((0.0, 0.0), True)]
    return _round_poly(cs, rc, ri, n_corner, n_inner)


def rect_outline(w, d, n_corner=6):
    rc = TOP_CORNER_R * MM
    cs = [((-w / 2, -d / 2), True), ((w / 2, -d / 2), True), ((w / 2, d / 2), True), ((-w / 2, d / 2), True)]
    return _round_poly(cs, rc, rc, n_corner, n_corner)


def _round_poly(cs, rc, ri, n_c, n_i):
    out = []
    k = len(cs)
    for i, (p, convex) in enumerate(cs):
        a, b = cs[i - 1][0], cs[(i + 1) % k][0]
        r, n = (rc, n_c) if convex else (ri, n_i)
        if r <= 0 or n == 0:
            out.append(p)
            continue
        u = [(a[0] - p[0]), (a[1] - p[1])]
        v = [(b[0] - p[0]), (b[1] - p[1])]
        lu, lv = math.hypot(*u), math.hypot(*v)
        u = [u[0] / lu, u[1] / lu]
        v = [v[0] / lv, v[1] / lv]
        # right-angle corners: the arc centre is r along both edges
        c = (p[0] + (u[0] + v[0]) * r, p[1] + (u[1] + v[1]) * r)
        s = (p[0] + u[0] * r, p[1] + u[1] * r)
        e = (p[0] + v[0] * r, p[1] + v[1] * r)
        a0 = math.atan2(s[1] - c[1], s[0] - c[0])
        a1 = math.atan2(e[1] - c[1], e[0] - c[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for j in range(n + 1):
            t = a0 + da * j / n
            out.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return out


def led_segments():
    """The strip's runs in the desk frame (m): ((x0, y0), (x1, y1)), in the knee spaces only: plan v3
    puts it 5 cm in, where the units (1 cm in) stand under the top, so it stops 1 cm short of them."""
    hw, hd = AW * MM / 2, AD * MM / 2
    foot = []
    for x, y, yaw in DRAWERS_AT:
        if yaw == 90:
            foot.append((x - hd, x + hd, y - hw, y + hw))
        else:
            foot.append((x - hw, x + hw, y - hd, y + hd))
    xm = MAIN_D - LED_IN                       # main run: along y at x = 0.75
    yr = -RET_D + LED_IN                       # return: along x at y = -0.55
    u1 = foot[0]
    segs = [((xm, u1[3] + 0.01), (xm, yr))]   # from unit 1 to the corner
    u2, u3 = foot[1], foot[2]
    if u2[0] - 0.01 > xm:
        segs.append(((xm, yr), (u2[0] - 0.01, yr)))
    segs.append(((u2[1] + 0.01, yr), (u3[0] - 0.01, yr)))
    return segs


# ---------------------------------------------------------------------------
# Blender side
# ---------------------------------------------------------------------------
def _alex_white():
    """The ALEX white, darkened on faces whose `inside` attribute is 1 (the drawer boxes)."""
    from lib import materials as M
    m = bpy.data.materials.get("mat_desk_alex_white")
    if m is not None:
        return m
    m = M.principled("mat_desk_alex_white", base="#f0f0ec", rough=0.5, spec=0.45)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_type, at.attribute_name = "GEOMETRY", "inside"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    c = tuple(b.inputs["Base Color"].default_value)
    mix.inputs["A"].default_value = c
    mix.inputs["B"].default_value = (BOX_SHADE, BOX_SHADE, BOX_SHADE, 1.0)
    nt.links.new(at.outputs["Fac"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


def materials():
    from lib import materials as M
    get = bpy.data.materials.get
    return {
        "white": _alex_white(),
        "top": get("mat_desk_top_white") or M.principled("mat_desk_top_white", base="#f2f2ee", rough=0.42, spec=0.5),
        "black": get("mat_desk_feet") or M.principled("mat_desk_feet", base="#141414", rough=0.6),
        "steel": get("mat_desk_runner") or M.principled("mat_desk_runner", base="#a3a6aa", rough=0.35, metal=1.0),
        "led": get("mat_desk_led") or M.principled("mat_desk_led", base="#e9f2ff", rough=0.4, emit=LED_COLOUR,
                                                    emit_strength=LED_STRENGTH),
        "led_body": get("mat_desk_led_body") or M.principled("mat_desk_led_body", base="#e6e6e6", rough=0.4),
    }


def _box(A, x0, x1, y0, y1, z0, z1, key):
    A.prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, key)


def _cyl(A, cx, cy, r, z0, z1, n, key):
    A.prism([(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)],
            z0, z1, key)


def _bevel(o, width, segments, angle=30):
    from lib import geo
    if segments > 0 and width > 0:
        geo.bevel(o, width, segments=segments, angle=angle)
    return o


def _finish(A, name, mats, coll, parent, at=(0, 0, 0), bevel=None, segs=2, data_name=True):
    from lib import names
    o = A.finish(name, mats, "+Z", at, coll, parent, smooth=30)
    if bevel:
        _bevel(o, bevel, segs)
    return o


def _empty(name, coll, parent=None, at=(0, 0, 0), yaw=0.0, size=0.2):
    from lib import names
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = size
    coll.objects.link(e)
    e.parent = parent
    names.set_name(e, name, data=False)
    e.location = at
    e.rotation_euler = (0, 0, math.radians(yaw))
    return e


def alex_unit(prefix, coll, parent=None, at=(0, 0, 0), yaw=0.0, rough=False, lite=False, share=None, sfx=""):
    """One ALEX unit under an empty `prefix`. share: a dict from an earlier unit (its meshes are reused,
    linked, as the three units of the desk are identical). Returns (root, {role: [objects]}, share)."""
    from lib import parts as P, names
    mats = materials()
    root = _empty(prefix + sfx, coll, parent, at, yaw)
    out = {"carcass": [], "drawers": []}
    s = MM
    hw, hd = AW / 2 * s, AD / 2 * s
    if rough:                                  # the silhouette: carcass box on four feet
        A = P.Mesh()
        _box(A, -hw, hw, -hd, hd, FOOT_H * s, AH * s, "white")
        for fx in (-1, 1):
            for fy in (-1, 1):
                _cyl(A, fx * (hw - FOOT_IN[0] * s), fy * (hd - FOOT_IN[1] * s), FOOT_D / 2 * s, 0, FOOT_H * s, 12, "black")
        out["carcass"].append(_finish(A, prefix + "_carcass" + sfx, mats, coll, root))
        return root, out, None
    if share:
        o = bpy.data.objects.new(prefix + "_carcass" + sfx, share["carcass"].data)
        coll.objects.link(o)
        o.parent = root
        names.set_name(o, prefix + "_carcass" + sfx, data=False)
        for m in share["carcass"].modifiers:
            _bevel(o, m.width, m.segments)
        out["carcass"].append(o)
        for i, d in enumerate(share["drawers"]):
            n = f"{prefix}_drawer_{i + 1:02d}{sfx}"
            o = bpy.data.objects.new(n, d.data)
            coll.objects.link(o)
            o.parent = root
            names.set_name(o, n, data=False)
            o.location = d.location
            for m in d.modifiers:
                _bevel(o, m.width, m.segments)
            out["drawers"].append(o)
        return root, out, share
    # carcass: top, bottom (both full width and depth), sides between them, the finished back inset
    A = P.Mesh()
    _box(A, -hw, hw, -hd, hd, OPEN_Z1 * s, AH * s, "white")                        # top panel
    _box(A, -hw, hw, -hd, hd, FOOT_H * s, OPEN_Z0 * s, "white")                    # bottom panel (the plinth)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * hw, sx * (hw - PANEL_T * s)))
        _box(A, x0, x1, -hd, hd, OPEN_Z0 * s, OPEN_Z1 * s, "white")              # sides
    _box(A, -hw + PANEL_T * s, hw - PANEL_T * s, hd - BACK_T * s, hd, OPEN_Z0 * s, OPEN_Z1 * s, "white")  # back
    nfoot = 8 if lite else 24
    for fx in (-1, 1):
        for fy in (-1, 1):
            _cyl(A, fx * (hw - FOOT_IN[0] * s), fy * (hd - FOOT_IN[1] * s), FOOT_D / 2 * s, 0.0, FOOT_H * s + 0.0005,
                 nfoot, "black")
    if not lite:                               # the carcass half of each runner pair, on the side walls
        for z0, h in zip(front_z(), FRONT_H):
            zr = (z0 + BOX_UP + 4.0) * s
            for sx in (-1, 1):
                x0, x1 = sorted((sx * (hw - PANEL_T * s), sx * (hw - PANEL_T * s - RUNNER[0] * s * 0.5)))
                _box(A, x0, x1, -hd + 50 * s, -hd + 50 * s + RUNNER[1] * s, zr, zr + RUNNER[2] * s, "steel")
    carcass = _finish(A, prefix + "_carcass" + sfx, mats, coll, root, bevel=None if lite else EDGE_R * s, segs=2)
    _mark_inside(carcass, hw - PANEL_T * s, hd, OPEN_Z0 * s, OPEN_Z1 * s)
    out["carcass"].append(carcass)
    # drawers
    yf = -hd + FRONT_RECESS * s                # front face
    ncut = 6 if lite else 18
    for i, (z0, h) in enumerate(zip(front_z(), FRONT_H)):
        n = f"{prefix}_drawer_{i + 1:02d}{sfx}"
        A = P.Mesh()
        # the front: its face outline extruded back FRONT_T (built at origin = front face bottom centre)
        A.prism([(x * s, z * s) for x, z in front_outline(h, ncut)], -FRONT_T * s, 0.0, "white",
                m=P.orient("-Y"))
        nf_front = len(A.bm.faces)
        # the box behind it: sides, back, bottom
        bh, by0, by1 = BOX_H[h] * s, FRONT_T * s, (BOX_BACK_Y * s - yf)
        zb = BOX_UP * s
        bw = BOX_W / 2 * s
        for sx in (-1, 1):
            x0, x1 = sorted((sx * bw, sx * (bw - BOX_SIDE_T * s)))
            _box(A, x0, x1, by0, by1, zb, zb + bh, "white")
        _box(A, -bw + BOX_SIDE_T * s, bw - BOX_SIDE_T * s, by1 - BOX_BACK_T * s, by1, zb, zb + bh, "white")
        _box(A, -bw + BOX_SIDE_T * s, bw - BOX_SIDE_T * s, by0, by1 - BOX_BACK_T * s,
             zb + BOX_BOTTOM_UP * s, zb + (BOX_BOTTOM_UP + BOX_BOTTOM_T) * s, "white")
        if not lite:                           # the drawer half of the runners
            zr = (BOX_UP + 4.0) * s
            for sx in (-1, 1):
                x0, x1 = sorted((sx * bw, sx * (bw + RUNNER[0] * s * 0.45)))
                _box(A, x0, x1, by0 + 30 * s, by0 + 30 * s + (RUNNER[1] - 40) * s, zr, zr + RUNNER[2] * s, "white")
        d = _finish(A, n, mats, coll, root, at=(0.0, yf, z0 * s), bevel=None if lite else FRONT_EDGE_R * s, segs=2)
        ins = d.data.attributes.new("inside", "FLOAT", "FACE")
        ins.data.foreach_set("value", [0.0 if i < nf_front else 1.0 for i in range(len(d.data.polygons))])
        out["drawers"].append(d)
    share = {"carcass": carcass, "drawers": out["drawers"]}
    return root, out, share


def _mark_inside(o, xi, hd, z0, z1, eps=1e-4):
    """`inside` = 1 on the carcass's faces that look into the drawer cavity (side panels' inner faces,
    the back's front face, the bottom's top face, the top's underside): seen only through the gaps and
    the cut-outs, dark in every photo."""
    vals = []
    for p in o.data.polygons:
        c, n = p.center, p.normal
        inner = (-xi - eps <= c.x <= xi + eps and -hd + 0.02 < c.y < hd + eps and z0 - eps <= c.z <= z1 + eps and
                 ((abs(abs(c.x) - xi) < eps and n.x * c.x < 0) or (abs(c.z - z0) < eps and n.z > 0.5) or
                  (abs(c.z - z1) < eps and n.z < -0.5) or (n.y < -0.5 and c.y > hd - BACK_T * MM - eps)))
        vals.append(1.0 if inner else 0.0)
    a = o.data.attributes.new("inside", "FLOAT", "FACE")
    a.data.foreach_set("value", vals)


def top_slab(name, outline, coll, parent, z0, lite=False, mat_key="top"):
    from lib import parts as P
    A = P.Mesh()
    A.prism(outline, z0, z0 + TOP_T * MM, mat_key)
    o = A.finish(name, materials(), "+Z", (0, 0, 0), coll, parent, smooth=30)
    return _bevel(o, TOP_EDGE_R * MM, 1 if lite else 3, angle=40)


def led_strip(name, coll, parent, lite=False):
    """The strip under the top: a white body with a white-blue glowing face pointing down. One mesh,
    two materials (static, never touched by code)."""
    from lib import parts as P
    A = P.Mesh()
    w, t = LED_W * MM / 2, LED_T * MM
    z1 = TOP_Z - TOP_T * MM
    for (x0, y0), (x1, y1) in led_segments():
        if abs(x1 - x0) > abs(y1 - y0):        # along x
            xa, xb = sorted((x0, x1))
            _box(A, xa, xb, y0 - w, y0 + w, z1 - t, z1, "led_body")
            _box(A, xa + 0.002, xb - 0.002, y0 - w + 0.002, y0 + w - 0.002, z1 - t - 0.0008, z1 - t + 0.0002, "led")
        else:
            ya, yb = sorted((y0, y1))
            _box(A, x0 - w, x0 + w, ya, yb, z1 - t, z1, "led_body")
            _box(A, x0 - w + 0.002, x0 + w - 0.002, ya + 0.002, yb - 0.002, z1 - t - 0.0008, z1 - t + 0.0002, "led")
    return A.finish(name, materials(), "+Z", (0, 0, 0), coll, parent, smooth=30)


def _coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def build(rough=False, lite=False, collection=None, what=("unit",), suffix=""):
    """rough: the unit's silhouette only (outline check). what: any of "unit" (the single ALEX at the
    origin), "desk" (the L desk, plan v3), "cmp200" (IKEA's 200 x 60 layout). Returns {role: [names]}."""
    names = {}
    if "unit" in what:
        coll = collection or _coll("alex" + suffix)
        root, parts, _ = alex_unit("alex", coll, rough=rough, lite=lite, sfx=suffix)
        names["unit_root"] = [root.name]
        names["unit"] = [o.name for v in parts.values() for o in v]
        names["unit_drawers"] = [o.name for o in parts["drawers"]]
    if "desk" in what and not rough:
        coll = collection or _coll("set_desk" + suffix)
        root = _empty("set_desk" + suffix, coll, None, DESK_AT, size=0.4)
        top = top_slab("desk_top" + suffix, l_outline(), coll, root, TOP_Z - TOP_T * MM, lite)
        objs = [top]
        share = None
        for i, (x, y, yaw) in enumerate(DRAWERS_AT):
            r, p, share = alex_unit(f"desk_drawers_{i + 1:02d}", coll, root, (x, y, 0.0), yaw, lite=lite,
                                    share=share, sfx=suffix)
            objs += [o for v in p.values() for o in v]
        led = led_strip("desk_led" + suffix, coll, root, lite)
        objs.append(led)
        names["desk_root"] = [root.name]
        names["desk"] = [o.name for o in objs]
    if "cmp200" in what and not rough:
        coll = collection or _coll("cmp200")
        root = _empty("cmp200", coll, None, CMP_AT)
        top = top_slab("cmp200_top", rect_outline(CMP_TOP[0] * MM, CMP_TOP[1] * MM), coll, root, AH * MM, lite)
        objs = [top]
        share = None
        for i, sx in enumerate((-1, 1)):
            r, p, share = alex_unit(f"cmp200_unit_{i + 1:02d}", coll, root, (sx * CMP_UNIT_X * MM, 0.0, 0.0), 0.0,
                                    share=share)
            objs += [o for v in p.values() for o in v]
        names["cmp200_root"] = [root.name]
        names["cmp200"] = [o.name for o in objs]
    if "lag" in what and not rough:
        coll = collection or _coll("cmp_lag")
        for w in LAG_SIZES:
            nm = f"lag{int(w / 10)}"
            root = _empty(nm, coll, None, LAG_AT)
            top_slab(nm + "_top", rect_outline(w * MM, 600 * MM), coll, root, 0.0, lite)
            names[nm + "_root"] = [nm]
            names[nm] = [nm + "_top"]
    names["all"] = names.get("unit", []) + names.get("desk", []) + names.get("cmp200", [])
    return names


# ---------------------------------------------------------------------------
# reference views: IKEA's own 3D file rendered square-on (local reference only, never shipped)
# ---------------------------------------------------------------------------
def _views_spec():
    """IKEA file reference renders: (file, view, centre (m), ortho width (m), res (w, h), which part)."""
    return {
        "ikea-unit-front": dict(view="front", part="unit", centre=(0, 0, 0.35), width=0.50, res=(1000, 1600)),
        "ikea-unit-right": dict(view="right", part="unit", centre=(0, 0, 0.35), width=0.72, res=(1440, 1600)),
        "ikea-unit-back": dict(view="back", part="unit", centre=(0, 0, 0.35), width=0.50, res=(1000, 1600)),
        "ikea-unit-top": dict(view="top", part="unit", centre=(0, 0, 0.35), width=0.50, res=(1000, 1300)),
        "ikea-unit-3q": dict(view="3q", part="unit", centre=(0, 0, 0.35), az=35.0, el=20.0, res=(1100, 1300)),
        "ikea-desk-front": dict(view="front", part="desk", centre=(0, 0, 0.37), width=2.10, res=(2100, 800)),
        "ikea-desk-right": dict(view="right", part="desk", centre=(0, 0, 0.37), width=0.70, res=(1400, 1600)),
        "ikea-desk-top": dict(view="top", part="desk", centre=(0, 0, 0.37), width=2.10, res=(2100, 700)),
        "ikea-desk-3q": dict(view="3q", part="desk", centre=(0, 0, 0.37), az=-30.0, el=22.0, res=(1600, 1000)),
    }


def stage_refviews(out=IKEA_VIEWS):
    """Import IKEA's file, cut out one ALEX unit (and the desk without its middle leg), render each view
    square-on with a transparent background and write a ref record (true scale) per view."""
    import bmesh
    import json
    from lib import backdrops
    os.makedirs(out, exist_ok=True)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    bpy.ops.import_scene.gltf(filepath=IKEA_GLB)
    src = next(o for o in bpy.data.objects if o.type == "MESH")
    src.data.transform(src.matrix_world)
    src.matrix_world = Matrix.Identity(4)

    def cut(name, keep):
        me = src.data.copy()
        bm = bmesh.new()
        bm.from_mesh(me)
        for co, no in keep.get("bisect", []):
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
        kill = [v for v in bm.verts if not keep["fn"](v.co)]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        return o
    unit = cut("ikea_unit", {"bisect": [((0.62, 0, 0), (1, 0, 0)), ((0, 0, 0.6999), (0, 0, 1))],
                             "fn": lambda c: c.x > 0.6199 and c.z < 0.69992})
    lo = [min(v.co[i] for v in unit.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in unit.data.vertices) for i in range(3)]
    unit.data.transform(Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, 0)))
    desk = cut("ikea_desk", {"fn": lambda c: not (abs(c.x) < 0.2 and c.z < 0.6999)})   # the ADILS leg out
    src.hide_render = True
    sizes = {"unit_mm": [round((h - l) * 1000, 1) for l, h in zip(lo, hi)]}
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type = "STUDIO", "SINGLE"
    sh.single_color = (0.85, 0.85, 0.84)
    sh.show_cavity = True
    sh.cavity_type = "WORLD"
    sc.render.film_transparent = True
    sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGBA"
    sc.render.resolution_percentage = 100
    recs = {}
    for fn, v in _views_spec().items():
        unit.hide_render = v["part"] != "unit"
        desk.hide_render = v["part"] != "desk"
        w, h = v["res"]
        sc.render.resolution_x, sc.render.resolution_y = w, h
        c = Vector(v["centre"])
        if v["view"] == "3q":
            cam = backdrops.three_quarter_camera(c, 0.42 if v["part"] == "unit" else 1.25, az=v["az"], el=v["el"],
                                                 lens=70, aspect=w / h, name="ref_cam_" + fn)
        else:
            cam = backdrops.view_camera(v["view"], c, v["width"], aspect=w / h, name="ref_cam_" + fn)
        sc.camera = cam
        p = os.path.join(out, fn + ".png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        if v["view"] != "3q":
            R, U, N = backdrops.axes(v["view"])
            mpp = v["width"] * 1000 / w
            # the world origin's pixel: the image centre is the camera centre c
            ax = w / 2 - c.dot(R) * 1000 / mpp
            ay = h / 2 + c.dot(U) * 1000 / mpp
            recs[fn] = {"image": p, "mm_per_px": mpp, "anchor_px": [ax, ay], "anchor_mm": [0.0, 0.0],
                        "view": v["view"], "note": "IKEA's 3D file, rendered square-on (reference only)"}
        else:
            recs[fn] = {"image": p, "view": "3q", "az": v["az"], "el": v["el"]}
    with open(os.path.join(out, "ikea-views.json"), "w") as f:
        json.dump({"records": recs, "sizes": sizes}, f, indent=1)
    print("MILESTONE refviews", sizes, flush=True)
    return recs


# ---------------------------------------------------------------------------
# the compare views (outline check and the every-angle test)
# ---------------------------------------------------------------------------
PHOTO_3Q_SRC = os.path.join(REF, "alex-three-quarter.jpg")
# compare.py's perspective fit frames 1.3 x the model's width, so a tall unit in a square photo is cut off
# at the top and bottom: the fit uses a copy padded with white to 1400 x 2000 (the original untouched)
PHOTO_3Q = os.path.join(FOOTAGE, "refs", "alex-three-quarter-pad.png")
PHOTO_LAG = os.path.join(REF, "lagkapten-top-three-quarter.jpg")


def padded_photo():
    if not os.path.exists(PHOTO_3Q):
        import subprocess
        from lib import compare
        os.makedirs(os.path.dirname(PHOTO_3Q), exist_ok=True)
        code = ("import sys; from PIL import Image; a = Image.open(sys.argv[1]).convert('RGB'); "
                "b = Image.new('RGB', (a.size[0], 2000), (255, 255, 255)); b.paste(a, (0, (2000 - a.size[1]) // 2)); "
                "b.save(sys.argv[2])")
        subprocess.run([compare.plain_python(), "-c", code, PHOTO_3Q_SRC, PHOTO_3Q], check=True)
    return PHOTO_3Q


def _records():
    import json
    p = os.path.join(IKEA_VIEWS, "ikea-views.json")
    return json.load(open(p))["records"] if os.path.exists(p) else {}


def _rotator(root_name, yaw):
    def prep():
        r = bpy.data.objects[root_name]
        old = r.rotation_euler.copy()
        r.rotation_euler = (0, 0, math.radians(yaw))
        bpy.context.view_layer.update()

        def undo():
            r.rotation_euler = old
            bpy.context.view_layer.update()
        return undo
    return prep


def fit_yaw(view, root_name, yaws, out_dir, cache_key, quick=True):
    """The model's turn for a three-quarter photo: camera fits at each yaw, the best kept with its
    camera (cached in out_dir/yaw-cache.json). Returns {"yaw", "D", "dz", "tilt", "iou"}."""
    import json
    from lib import compare
    cp = os.path.join(out_dir, "yaw-cache.json")
    cache = json.load(open(cp)) if os.path.exists(cp) else {}
    if isinstance(cache.get(cache_key), dict):
        return cache[cache_key]
    best = None
    tried = []

    def one(y):
        v = dict(view, prepare=_rotator(root_name, y), camera=dict(view["camera"], quick=quick),
                 name=view["name"] + "-yaw")
        e = compare.score_view(v, os.path.join(out_dir, "yawfit"), look_engine=None, threshold=0.0, log=lambda *a: None)
        c = e["camera"]
        r = {"yaw": y, "D": c["distance_m"], "dz": c["height_offset_m"], "tilt": c["tilt_deg"], "iou": e["iou"]}
        tried.append((round(e["iou"], 4), y))
        return r
    for y in yaws:
        r = one(y)
        if best is None or r["iou"] > best["iou"]:
            best = r
    step = abs(yaws[1] - yaws[0]) / 2 if len(yaws) > 1 else 2.0
    for y in (best["yaw"] - step, best["yaw"] + step, best["yaw"] - step / 2, best["yaw"] + step / 2):
        r = one(y)
        if r["iou"] > best["iou"]:
            best = r
    cache[cache_key] = best
    os.makedirs(out_dir, exist_ok=True)
    json.dump(cache, open(cp, "w"), indent=1)
    print(f"MILESTONE fit_yaw {cache_key}: {best} (tried {sorted(tried)[-4:]})", flush=True)
    return best


def _fitted_camera(f, level=False):
    """A fit camera searched closely around a cached fit (level: no tilt, the shifted-lens packshot)."""
    D, dz, t = f["D"], f["dz"], f["tilt"]
    k = 0.03 * D if level else 0.01
    return {"mode": "fit", "view": "front", "distances": [D * 0.96, D, D * 1.04], "heights": [dz - k, dz, dz + k],
            "tilts": [t] if level else [t - 1.0, t, t + 1.0]}


def outline_views(names, which=("photo-3q", "ikea-unit-front", "ikea-unit-right", "ikea-unit-top", "ikea-unit-3q"),
                  out_dir=None):
    """compare.py views. The unit is scored against IKEA's packshot (three-quarter, camera and turn
    fitted) and against IKEA's own 3D file rendered square-on (true scale, `placed`); the IKEA 200 x 60
    layout (cmp200) against the file's desk views."""
    recs = _records()
    out_dir = out_dir or os.path.join(FOOTAGE, "outline")
    unit = names.get("unit") or names["all"]
    uroot = (names.get("unit_root") or ["alex"])[0]
    views = []
    for k in which:
        if k == "photo-3q":
            v = dict(name="alex-photo-3q", title="ALEX: IKEA packshot, three-quarter, vs our model", photo=padded_photo(),
                     mask=0.985, crop=None, objects=unit,
                     camera={"mode": "fit", "view": "front", "tilts": [0.0],
                             "heights": [0.3, 0.6, 0.9, 1.2, 1.5, 1.8], "distances": [3.0, 4.5, 6.5, 9.0, 12.0]})
            # IKEA's packshots are shot level with a shifted lens (verticals parallel, the five fronts'
            # pitches constant down the unit): a raised camera looking level, not a tilted one
            f = fit_yaw(v, uroot, [-30.0, -26.0, -22.0, -18.0], out_dir, "photo-3q", quick=False)
            v["prepare"] = _rotator(uroot, f["yaw"])
            v["camera"] = _fitted_camera(f, level=True)
            v["title"] += f" (turned {f['yaw']:.1f} deg)"
            views.append(v)
            continue
        if k == "photo-lag":
            best = None
            for w in LAG_SIZES:
                nm = f"lag{int(w / 10)}"
                if nm not in names:
                    continue
                for mode, cam in (("level", {"mode": "fit", "view": "front", "tilts": [0.0],
                                             "heights": [0.3, 0.7, 1.1, 1.5, 2.0, 2.6], "distances": [2.5, 4.0, 6.0, 9.0]}),
                                  ("tilt", {"mode": "fit", "view": "front", "tilts": [-36.0, -29.0, -22.0, -15.0]}),
                                  ("tilt-fine", {"mode": "fit", "view": "front", "tilts": [-27.0, -24.5, -22.0, -19.5]})):
                    if mode == "tilt-fine" and w != 1400.0:
                        continue
                    v = dict(name="lagkapten-photo-3q", photo=PHOTO_LAG, mask=0.985, objects=names[nm], camera=cam)
                    f = fit_yaw(v, nm, [-32.0, -26.0, -20.0, -14.0], out_dir, f"photo-lag-{nm}-{mode}", quick=False)
                    if best is None or f["iou"] > best[1]["iou"]:
                        best = (nm, f, v, mode)
            if best:
                nm, f, v, mode = best
                v["prepare"] = _rotator(nm, f["yaw"])
                v["camera"] = _fitted_camera(f, level=mode == "level")
                if mode != "level":
                    v["camera"]["tilts"] = [f["tilt"] - 0.75, f["tilt"], f["tilt"] + 0.75]
                v["title"] = (f"LAGKAPTEN top: IKEA packshot vs our top at {nm[3:]} x 60 (the best of "
                              f"{', '.join(str(int(x / 10)) for x in LAG_SIZES)}; turned {f['yaw']:.1f} deg)")
                v["lag_variant"] = nm
                views.append(v)
            continue
        r = recs.get(k)
        if r is None:
            continue
        part = "unit" if "-unit-" in k else "desk"
        objs = unit if part == "unit" else names.get("cmp200", [])
        root = uroot if part == "unit" else "cmp200"
        if not objs:
            continue
        label = {"front": "front", "right": "right side", "back": "back", "top": "top", "3q": "three-quarter"}[r["view"]]
        title = f"{'ALEX' if part == 'unit' else 'LAGKAPTEN/ALEX 200 x 60'}: IKEA's 3D file, {label}, vs our model"
        if r["view"] == "3q":
            v = dict(name=k, title=title, photo=r["image"], mask="alpha", objects=objs,
                     camera={"mode": "fit", "view": "front", "tilts": [-26.0, -22.0, -18.0, -14.0]})
            sgn = -1 if r["az"] > 0 else 1
            f = fit_yaw(v, root, [sgn * a for a in (40.0, 35.0, 30.0, 25.0)], out_dir, k, quick=False)
            v["prepare"] = _rotator(root, f["yaw"])
            v["camera"] = _fitted_camera(f)
            v["title"] += f" (turned {f['yaw']:.1f} deg)"
        else:
            rr = dict(r)
            loc = bpy.data.objects[root].location
            from lib import backdrops
            R, U, N = backdrops.axes(r["view"])
            rr["anchor_mm"] = [loc.dot(R) * 1000, loc.dot(U) * 1000]
            v = dict(name=k, title=title, photo=r["image"], mask="alpha", objects=objs,
                     camera={"mode": "placed", "ref": rr})
        views.append(v)
    return views


if __name__ == "__main__" and bpy is not None:
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "refviews" in a:
        stage_refviews()
    bpy.ops.wm.quit_blender()
