"""The arms and lights around the screens (component, 2026-10-26), as in the owner's photo
docs/moodboard/local/ai-desk-reference-1.jpg:

  - two Elgato Key Light (Mk.2) panels on Master Mount L desk-clamp poles (keylight_1, keylight_2)
  - Sony ZV-E10 II with the E PZ 16-50 mm II (retracted), screen flipped forward (selfie), on an
    Elgato Flex Arm L (tubes 240, 170, 80, 80) clamped to key light 1's pole (cam)
  - Shure MV7+ white on a RODE PSA1+ white, posable from named joint angles (obj_mic)

Built from Sony's drawing and the makers' sizes (no base model: the Innixicated ZV-E10 was not used).
Invented brand names (content/room-brands.json, lib/brands.py) at the real logos' spots; no other printed
text. Always headless:

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
KL_BOX = (110 * MM, 75 * MM, 20 * MM)   # EST back-in-use.jpg: landscape, 110 x 75; 20 deep (side.jpg)
KL_BOX_Z = 0.150                       # EST back-in-use.jpg: the box's centre above the panel's bottom edge (high)
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
MIC_R = 31 * MM                         # MEASURED back.png: 0.79 of the yoke's outer half-width (38.8)
MIC_REAR_R = 26.5 * MM                    # MEASURED side-profile: tapers to 56 at the rear
MIC_PIVOT = 50 * MM                     # MEASURED side-profile: yoke knobs 47 to 50 from the rear plate
MIC_FOAM = 73 * MM                      # MEASURED side-profile
MIC_RING = 14 * MM                      # MEASURED side-profile: the black ring with the LED strip
YOKE_IN, YOKE_T, YOKE_W = 35.2 * MM, 3.0 * MM, 14 * MM   # MEASURED back.png (inner half-width); band 14 x 3 (side photos)
YOKE_TOP = 83 * MM                      # MEASURED back.png: the arc top above the body axis
STEM = (8 * MM, 48 * MM)                # MEASURED back/front.png: 16 across; length to fit 164 OFFICIAL overall
KNOB = (9.35 * MM, 4.5 * MM)            # MEASURED back.png: 18.7 across, 4.5 proud
# RODE PSA1+
ARM_L1 = ARM_L2 = 0.425                 # MEASURED RODE's drawing: hinge to hinge (500 folded overall)
ARM_W = 65 * MM                         # OFFICIAL width
ARM_COVER = (26 * MM, 32 * MM)          # EST white-folded-side-2000.png: padded rounded-square cover, width x height
ARM_HINGE_R = 30 * MM                   # EST SOURCES (60 discs on the drawing)
ARM_POST = 0.10                         # EST: desk to the shoulder hinge
ARM_TIP = 0.06                          # EST: wrist hinge to the 3/8 stud's end
ARM_JOG = 0.0                           # one elbow pivot (RODE's folded shot: a single disc at the elbow)

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
    p["kl_black"] = get("mat_arms_keylight_black", base="#151517", rough=0.6, spec=0.18)
    p["kl_back"] = bpy.data.materials.get("mat_arms_keylight_back") or bumpy_material(
        "mat_arms_keylight_back", "#141416", 0.62, 0.18, 900.0, 0.35)
    p["led_rainbow"] = bpy.data.materials.get("mat_arms_mic_led_rainbow") or rainbow_material()
    p["brass"] = get("mat_arms_brass", base="#c9a55a", rough=0.28, metal=1.0)
    p["satin"] = get("mat_arms_satin_black", base="#0e0f10", rough=0.38)
    p["cam"] = get("mat_arms_camera_black", base="#0f0f10", rough=0.55, spec=0.22)
    p["lens"] = get("mat_arms_lens_black", base="#0e0e0f", rough=0.5, spec=0.24)
    p["lens_front"] = get("mat_arms_lens_print_ring", base="#0d0d0e", rough=0.62, spec=0.25)
    p["grip"] = bpy.data.materials.get("mat_arms_grip") or grip_material()
    p["mount"] = get("mat_arms_mount_silver", base="#b9bcc1", rough=0.25, metal=1.0)
    p["glass"] = bpy.data.materials.get("mat_arms_lens_glass") or glass_material()
    p["glass_lite"] = get("mat_arms_lens_glass_lite", base="#05070a", rough=0.04, spec=1.0, coat=1.0,
                          coat_rough=0.02)
    p["glass_hint"] = get("mat_arms_lens_glass_hint", base="#5a6a78", rough=0.15, spec=1.0)
    p["lens_rib"] = get("mat_arms_lens_rib", base="#111113", rough=0.38, spec=0.35)
    p["lcd"] = get("mat_arms_lcd", base="#0a0c10", rough=0.08, emit="#7d93b0", emit_strength=0.3)
    p["white"] = get("mat_arms_white", base="#eeeeec", rough=0.42, coat=0.1)
    p["pad"] = bpy.data.materials.get("mat_arms_pad") or bumpy_material("mat_arms_pad", "#ececea", 0.85, 0.2, 700.0, 0.25)
    p["mic_white"] = get("mat_arms_mic_white", base="#ececea", rough=0.45)
    p["foam"] = bpy.data.materials.get("mat_arms_foam") or bumpy_material("mat_arms_foam", "#080809", 1.0, 0.1, 2200.0, 0.6)
    p["led"] = get("mat_arms_mic_led", base="#9fe8e0", rough=0.3, emit="#6ff2c8", emit_strength=6.0)
    p["glow"] = get("mat_arms_keylight_glow", base="#ffffff", rough=0.6, emit="#fff6ea", emit_strength=6.0)
    p["red"] = get("mat_arms_red", base="#a3201c", rough=0.4)
    return p


def glass_material():
    """Coated lens glass for renders: clear dielectric (IOR 1.5), a thin-film coat for the green and magenta
    reflections. Rich only: the glTF importer in Blender 5.2 fails on iridescence, so lite uses glass_lite."""
    from lib import materials as M
    m, nt, b = M._new("mat_arms_lens_glass")
    for k, v in (("Base Color", (0.95, 0.95, 0.95, 1)), ("Roughness", 0.01), ("IOR", 1.5),
                 ("Transmission Weight", 1.0), ("Thin Film Thickness", 560.0), ("Thin Film IOR", 1.38),
                 ("Coat Weight", 0.5), ("Coat Roughness", 0.0), ("Coat IOR", 1.6)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    m.use_raytrace_refraction = True
    m.surface_render_method = "DITHERED"
    m.diffuse_color = (0.02, 0.03, 0.04, 1)
    return m


def bumpy_material(name, base, rough, spec, scale, strength):
    """A plain material with a fine noise bump (foam cells, the Key Light's textured back). Rich renders
    only: the bump does not reach the GLB, the base colour and roughness do."""
    from lib import materials as M
    m, nt, b = M._new(name)
    M._set(b, base=base, rough=rough, spec=spec)
    n = M._noise(nt, M._coords(nt), scale, detail=3, rough=0.7)
    M._bump(nt, b, n, strength, distance=0.0003)
    m.diffuse_color = M.rgba(base)
    return m


def rainbow_image():
    """The MV7+ LED arc's colours along the arc (green, yellow, orange, pink): a 64 x 1 image, packed in the GLB."""
    im = bpy.data.images.get("arms_mic_led_rainbow")
    if im is None:
        stops = [(0.0, (0.25, 1.0, 0.45)), (0.35, (0.95, 0.95, 0.25)), (0.65, (1.0, 0.55, 0.15)), (1.0, (1.0, 0.35, 0.6))]
        px = []
        for i in range(64):
            t = i / 63
            for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
                if t0 <= t <= t1:
                    f = (t - t0) / (t1 - t0)
                    px += [c0[k] + (c1[k] - c0[k]) * f for k in range(3)] + [1.0]
                    break
        im = bpy.data.images.new("arms_mic_led_rainbow", 64, 1)
        im.pixels = px
        im.pack()
    return im


def rainbow_material():
    """Emissive arc: base and emission from the gradient image along the arc's U (exports as an emissive texture)."""
    from lib import materials as M
    m, nt, b = M._new("mat_arms_mic_led_rainbow")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = rainbow_image()
    tex.interpolation = "Linear"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 3.0
    b.inputs["Roughness"].default_value = 0.35
    m.diffuse_color = (0.9, 0.7, 0.4, 1)
    return m


def uv_strip(name, rings, key_mat, coll, parent, m=None):
    """A quad strip mesh from a list of rings (each a list of points), with U running along the ring (0..1)
    and V across the rings; one material. For the LED arc (a gradient texture needs UVs)."""
    verts, faces, uvs = [], [], []
    n = len(rings[0])
    for r in rings:
        verts += [tuple((m @ Vector(p)) if m is not None else p) for p in r]
    for j in range(len(rings) - 1):
        for i in range(n - 1):
            a, b2 = j * n + i, (j + 1) * n + i
            faces.append((a, a + 1, b2 + 1, b2))
            uvs.append([(i / (n - 1), j), ((i + 1) / (n - 1), j), ((i + 1) / (n - 1), j + 1), (i / (n - 1), j + 1)])
    me = bpy.data.meshes.new(name + "_mesh")
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for f, uv in zip(me.polygons, uvs):
        for li, u in zip(f.loop_indices, uv):
            uvl.data[li].uv = u
    me.materials.append(key_mat)
    me.shade_smooth()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    from lib import names
    names.set_name(o, name)
    o.parent = parent
    return o


def resample(outline, step):
    """Points every `step` metres along a closed outline (for the Key Light's rim fins)."""
    pts = outline + [outline[0]]
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total = sum(seg)
    n = int(total / step)
    out, i, acc = [], 0, 0.0
    for k in range(n):
        t = k * total / n
        while acc + seg[i] < t:
            acc += seg[i]
            i += 1
        f = (t - acc) / seg[i] if seg[i] else 0.0
        a, b = pts[i], pts[i + 1]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


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


# invented brand names (decision 2026-10-26): the name comes from content/room-brands.json via lib/brands.py;
# each sits at the real logo's spot, size, colour and finish. Positions: the parent part's local frame.
# Photos: 18-camera/front-body-hires-commons.jpg, 17-key-lights/back-in-use.jpg, 11-mic/three-quarter.png,
# side-profile-yoke-open.jpg, back-straight-white-1500.png, 12-boom-arm/white-three-quarter-extended-2000.png,
# detail-white-clamp-mount.jpg.
def brand(key, parent, name, sfx, lite, at, normal, up, **kw):
    from lib import brands
    bpy.context.view_layer.update()
    return brands.decal(key, at=at, normal=normal, up=up, parent=parent, lite=lite, name=f"{name}{sfx}", **kw)


def join_into(a, b):
    """Merge decal b into decal a (same parent, both identity transforms)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(a.data)
    bm.from_mesh(b.data)
    bm.to_mesh(a.data)
    bm.free()
    me = b.data
    bpy.data.objects.remove(b)
    bpy.data.meshes.remove(me)
    return a


# ---------------------------------------------------------------------------
# 2a. key light on its pole. Origin: the pole's axis on the desk top; the panel faces -Y.
# ---------------------------------------------------------------------------
def build_keylight(n, coll, mp, rough=False, lite=False, pole_h=POLE_H, tilt=0.0, sfx="", pan=0.0):
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
    tilt_e = empty(f"keylight_{n}_tilt{sfx}", root, (0, 0, zp), (math.radians(tilt), 0, math.radians(pan)), coll)
    A = P.Mesh()
    # adapter (in the pole frame, so it does not tilt): below the pivot
    A.lathe([(0, -KL_ADAPT[1]), (KL_ADAPT[0], -KL_ADAPT[1]), (KL_ADAPT[0], -0.012), (0.008, -0.004), (0, -0.004)],
            seg, "satin")
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
    Mp = T(0, yf + KL_FRAME_T, zb + KL_H / 2) @ R(90, "X")   # local z 0..t maps to y from yf+t down to yf
    from lib.parts import rrect
    if rough:
        rbox(A, KL_W, KL_H, KL_FRAME_T, KL_R, 0, 0, 8, "kl_black", Mp)
    else:
        nq = 4 if lite else 10
        gw, gh = KL_W - 2 * KL_BORDER, KL_H - 2 * KL_BORDER
        Mq = T(0, yf, zb + KL_H / 2) @ R(90, "X")          # local z 0 = the front, -t = towards the back
        ou, inn = rrect(KL_W, KL_H, KL_R, nq), rrect(gw, gh, KL_R - KL_BORDER, nq)
        # the front lip: a near-black ring round the glow face, 2.5 mm deep, softened outer edge
        o0 = A.verts([(x, y, -0.0025) for x, y in ou], Mq)
        o1 = A.verts([(x, y, -0.0004) for x, y in ou], Mq)
        A.strip(o0, o1, "kl_black")
        A.ring_face([(x * 0.9985, y * 0.9975) for x, y in ou], inn, 0.0, "kl_black", Mq)
        A.strip(o1, A.verts([(x * 0.9985, y * 0.9975, 0.0) for x, y in ou], Mq), "kl_black")
        i1_ = A.verts([(x, y, 0.0) for x, y in inn], Mq)
        i0_ = A.verts([(x, y, -0.0025) for x, y in inn], Mq)
        A.strip(i1_, i0_, "kl_black")
        zf0, zf1 = -0.0025, -(KL_FRAME_T - 0.002)        # the rim between the lip and the back plate
        if lite:
            rbox(A, KL_W - 0.001, KL_H - 0.001, KL_FRAME_T - 0.0025, KL_R, 0.0, 0.004, 3, "kl_black", Mp)
        else:
            # the heat-sink rim: fine fins all round (side.jpg, three-quarter.jpg): 1.2 mm grooves every 3 mm,
            # one prism from an outline whose points alternate between the rim and 1.2 mm in
            dense = rrect(KL_W, KL_H, KL_R, 48)
            base = resample(dense, 0.00075)
            fin_pts = []
            for k, (x, y) in enumerate(base):
                a, b2 = base[k - 1], base[(k + 1) % len(base)]
                tx, ty = b2[0] - a[0], b2[1] - a[1]
                tl = math.hypot(tx, ty) or 1.0
                nx, ny = ty / tl, -tx / tl                   # outward for a CCW outline
                d = 0.0 if (k // 2) % 2 == 0 else -0.0012
                fin_pts.append((x + nx * d, y + ny * d))
            f0 = A.verts([(x, y, zf1) for x, y in fin_pts], Mq)
            f1 = A.verts([(x, y, zf0) for x, y in fin_pts], Mq)
            A.strip(f0, f1, "kl_black")
            A.face(list(reversed(f0)), "kl_black")
            A.face(f1, "kl_black")
        # the back plate: a shallow rounded panel with a fine bumpy finish, inset 2 mm
        Mc = T(0, yf + KL_FRAME_T, zb + KL_H / 2) @ R(90, "X")
        rbox(A, KL_W - 0.004, KL_H - 0.004, 0.0025, KL_R - 0.002, 0.0, 0.0015, 3 if lite else 6, "kl_back", Mc)
    # the control box: landscape, centred high on the back, ports on its lower edge
    bw, bh, bd = KL_BOX
    bz = zb + KL_BOX_Z
    Mb = T(0, yf + KL_FRAME_T + bd, bz) @ R(90, "X")
    rbox(A, bw, bh, bd, 0.012, 0.004 if not rough else 0, 0.0, 2 if lite else 4, "kl_black", Mb)
    if not rough:
        yb_ = yf + KL_FRAME_T + bd / 2
        for k, (w_, x_) in enumerate(((0.010, -0.022), (0.009, 0.0), (0.006, 0.020))):   # DC in, USB-C, the button
            rbox(A, w_, 0.004, 0.002, 0.0012, 0, 0, 2, "port" if k < 2 else "rubber",
                 T(x_, yb_, bz - bh / 2 - 0.0015))
    panel = fin(A, f"keylight_{n}_panel{sfx}", mp, coll, tilt_e, bevel=0.0012, lite=lite)
    # the diffuser: the glow face, 1.5 mm behind the lip
    A = P.Mesh()
    gw, gh = KL_W - 2 * KL_BORDER, KL_H - 2 * KL_BORDER
    Mg = T(0, yf + 0.0021, zb + KL_H / 2) @ R(90, "X")       # 2 mm behind the lip's front
    rbox(A, gw, gh, 0.0004, KL_R - KL_BORDER, 0, 0, 4 if lite else 10, "glow", Mg)
    glow = fin(A, f"keylight_{n}_glow{sfx}", mp, coll, tilt_e, lite=True)
    out = {"kl_static": [static.name, static_adapter.name], "kl_panel": [panel.name], "kl_glow": [glow.name]}
    if not rough:
        # the logo plate's spot on the back box: centred, 25 mm under the box top, about 6 mm, light grey
        b = brand("keylights", panel, f"keylight_{n}_brand", sfx, lite,
                  at=(0, yf + KL_FRAME_T + bd, bz + bh / 2 - 0.025), normal=(0, 1, 0), up=(0, 0, 1),
                  height=6 * MM, finish="printed", colour="#c9cacc")
        out["kl_brand"] = [b.name]
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

        rp = 0.0308
        zr0, zr1 = 0.0182, L - 0.0006          # the ribbed zoom ring (top-pb.jpg: the front 45 % of the barrel)
        # barrel up to the ribbed ring, then (after the ring) a crisp 0.4 mm edge, the FLAT front annulus
        # (r 32.6 to 22.5, the plain print ring), and stepped black rings going in (Henry's radial profile)
        A.lathe([(0, 0.0), (0.0300, 0.0), (0.0313, 0.0005), (0.0313, 0.0028), (rp, 0.0030), (rp, 0.0168),
                 (0.0326, 0.0172), (0.0329, zr0), (0, zr0)], seg, "lens", Ml)
        front = [(r, zr1), (r - 0.0004, L), (0.0225, L), (0.0225, L - 0.0008), (0.0205, L - 0.0008),
                 (0.0205, L - 0.0022), (0.0186, L - 0.0022), (0.0183, L - 0.0040), (0.0156, L - 0.0052),
                 (0.0151, L - 0.0128), (0, L - 0.0128)]
        A.lathe(front, seg, ["lens", "lens_front", "lens", "lens", "lens", "lens", "lens", "lens", "lens",
                             "port"], Ml)
        # the ribs: their own lathe, 4 vertices per rib, a square wave 0.25 mm proud, so they catch the light
        ribs = 0 if lite else 140
        if ribs:
            rs = ribs * 4
            sq = lambda a: 1.0 + (0.00025 / r) * (1.0 if math.cos(ribs * a - math.pi / 4) > 0 else 0.0)  # noqa: E731
            A.lathe([(r, zr0, sq), (r, zr1, sq)], rs, "lens_rib", Ml, phase=math.pi / rs)     # open tube
        else:
            A.lathe([(r, zr0), (r, zr1)], seg, "lens_rib", Ml)
        # the element's black retaining ring at the front element's edge, the aperture plate deeper inside
        zg = L - 0.0062
        A.lathe([(0.0128, zg + 0.0016), (0.0156, zg + 0.0010), (0.0156, zg + 0.0021), (0.0134, zg + 0.0026),
                 (0.0128, zg + 0.0026)], seg, "lens", Ml)
        A.lathe([(0.0042, L - 0.0118), (0.0151, L - 0.0118), (0.0151, L - 0.0114), (0.0042, L - 0.0114)], seg, "satin", Ml)
        # the zoom/focus switch tab on the barrel's left (+X) side
        rbox(A, 0.004, 0.009, 0.007, 0.0015, 0, 0, 2, "lens", T(rp + 0.0018, yf - 0.009, LENS_Z) @ R(90, "Y"))
    lens = fin(A, f"cam_lens{sfx}", mp, coll, root, bevel=None, lite=lite)
    out = {"cam_body": [body.name], "cam_lens": [lens.name], "cam_screen": []}
    if not rough:
        # the glass: a front element (a solid meniscus, 30 across) and a second, smaller element 4 mm deeper;
        # rich: transmissive coated glass; lite: a glossy dark dielectric plus a faint highlight crescent
        g = "glass_lite" if lite else "glass"
        A = P.Mesh()
        z0 = L - 0.0062
        A.lathe([(0, z0), (0.0150, z0), (0.0150, z0 + 0.0007), (0.0112, z0 + 0.0016), (0.0060, z0 + 0.0022),
                 (0, z0 + 0.0024)], seg, g, Ml)
        if not lite:
            z1 = L - 0.0108
            A.lathe([(0, z1), (0.0100, z1), (0.0100, z1 + 0.0006), (0.0060, z1 + 0.0016), (0, z1 + 0.0019)], seg, g, Ml)
        else:
            n = 10
            arc = [(math.radians(115 + 45 * k / n)) for k in range(n + 1)]
            ri, ro = 0.0080, 0.0104
            hz = lambda rr: z0 + 0.0024 - 0.0024 * (rr / 0.0150) ** 2 + 0.00012   # noqa: E731  (on the dome)
            a = A.verts([(ro * math.cos(t), ro * math.sin(t), hz(ro)) for t in arc], Ml)
            b = A.verts([(ri * math.cos(t), ri * math.sin(t), hz(ri)) for t in arc], Ml)
            for k in range(n):
                A.face([b[k], b[k + 1], a[k + 1], a[k]], "glass_hint")
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
        # the wordmark's spot: 47 mm from the grip-side edge (centre), 2.2 to 4.9 mm under the top, silver print
        b = brand("camera", body, "cam_brand", sfx, lite, at=(x0 - CB_W / 2 + 0.049, yf, H - 0.0036),
                  normal=(0, -1, 0), up=(0, 0, 1), height=3.2 * MM, finish="printed", colour="#c4c6c9",
                  max_width=15 * MM)
        out["cam_brand"] = [b.name]
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
    # the camera mount: a socket clamp 30 mm under the camera, a plate and the 1/4 screw; the chain ends at its ball
    mount_h = 0.030
    E = Vector(end)
    pts = flex_points(start, E - Vector((0, 0, mount_h)))
    BALL, SOCK, SOCK_L = 0.010, 0.0125, 0.028

    def ball(c):
        A.lathe([(0, -BALL), (BALL * 0.7, -BALL * 0.7), (BALL, 0), (BALL * 0.7, BALL * 0.7), (0, BALL)],
                12 if lite else 32, "satin", T(*c))

    def socket(c, d):
        """A two-part socket clamp gripping the ball at c, along d: body, chrome bands, the split, a lever."""
        cyl(A, SOCK, c - d * 0.004, c + d * SOCK_L, "matte", seg)
        if not rough:
            for t in (0.002, SOCK_L - 0.004):
                cyl(A, SOCK + 0.0004, c + d * t, c + d * (t + 0.0018), "chrome", seg)
            cyl(A, SOCK + 0.0002, c + d * (SOCK_L * 0.45), c + d * (SOCK_L * 0.45 + 0.001), "port", seg)
            side = d.cross(Vector((0, 0, 1)))
            side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))
            up = side.cross(d).normalized()
            hub = c + d * (SOCK_L * 0.55) + side * SOCK
            cyl(A, 0.004, hub, hub + side * 0.004, "satin", 12)
            tipp = hub + side * 0.006 + up * 0.026 - d * 0.006
            cyl(A, 0.0026, hub + side * 0.005, tipp, "matte", 8)              # the lever handle
            cyl(A, 0.0036, tipp, tipp + (tipp - hub).normalized() * 0.006, "matte", 8)
    ball(pts[0])                                         # the pole clamp's own ball
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d = (b - a).normalized()
        socket(a, d)
        cyl(A, FLEX_R, a + d * (SOCK_L - 0.006), b - d * (BALL * 0.5), "matte", seg)   # overlaps: no gaps
        ball(b)
    # the camera mount's socket on the last ball, its plate under the camera
    socket(pts[-1], Vector((0, 0, 1)))
    cyl(A, 0.016, E - Vector((0, 0, mount_h - SOCK_L - 0.002)), E - Vector((0, 0, 0.0005)), "matte", seg)
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
    # the stem (its own mesh: the photos cut it at their top edge), its lock ring and thread insert
    A.lathe([(0, -STEM[1]), (STEM[0], -STEM[1]), (STEM[0], 0), (0, 0)], seg, "mic_white")
    if not rough:
        A.lathe([(0, -0.012), (0.0125, -0.012), (0.0125, -0.004), (0, -0.004)], seg, "mic_white")
        A.lathe([(0.0035, -0.0001), (0.0062, -0.0001), (0.0062, 0.0004), (0.0035, 0.0004)], 24, "steel")  # thread insert
    stem = fin(A, f"mic_stem{sfx}", mp, coll, hang, lite=lite)
    A = P.Mesh()
    # the yoke: a round threaded socket on top (the stem goes in), and the flat band bent in a U
    A.lathe([(0, -STEM[1] - 0.016), (0.011, -STEM[1] - 0.016), (0.0115, -STEM[1] - 0.003), (0.010, -STEM[1]),
             (0, -STEM[1])], seg, "mic_white")
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
        rbox(A, YOKE_T, YOKE_W, L + 0.0012, 0.0012, 0, 0, 2, "mic_white", T(x0, 0, z0) @ R(ang, "Y") @ T(0, 0, -0.0006))
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
        # the black ring: fine vertical grip ribs at its rear (the white body side), then the LED band, then plain
        if lite:
            A.lathe([(MIC_R - 0.0003, zl), (MIC_R + 0.0003, zl), (MIC_R + 0.0003, zl + MIC_RING),
                     (MIC_R - 0.001, zl + MIC_RING)], seg, "satin", Mb)
        else:
            ribs = 120
            sq = lambda a: 1.0 + (0.0005 / MIC_R) * (1.0 if math.cos(ribs * a - math.pi / 4) > 0 else 0.0)  # noqa: E731
            A.lathe([(MIC_R - 0.0003, zl), (MIC_R, zl, sq), (MIC_R, zl + 0.0045, sq), (MIC_R - 0.0003, zl + 0.0045)],
                    ribs * 4, "satin", Mb, phase=math.pi / (ribs * 4))
            A.lathe([(MIC_R - 0.0003, zl + 0.0045), (MIC_R + 0.0003, zl + 0.0045), (MIC_R + 0.0003, zl + MIC_RING),
                     (MIC_R - 0.001, zl + MIC_RING)], seg, "satin", Mb)
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
    out = {"mic_body": [body.name], "mic_yoke": [yoke.name], "mic_stem": [stem.name]}
    if not rough:
        A = P.Mesh()
        for s in (-1, 1):
            x = s * (YOKE_IN + YOKE_T)
            ribs = 0 if lite else 24
            kn = (lambda a: 1.0 + 0.04 * max(0.0, math.cos(ribs * a))) if ribs else None
            prof = [(0, 0), (KNOB[0] * 0.8, 0), (KNOB[0], 0.001, kn) if kn else (KNOB[0], 0.001),
                    (KNOB[0], KNOB[1] - 0.001, kn) if kn else (KNOB[0], KNOB[1] - 0.001), (KNOB[0] * 0.85, KNOB[1]), (0, KNOB[1])]
            A.lathe(prof, seg, "satin", T(x, 0, 0) @ R(90 * s, "Y"))
        # the rear plate (back.png at 0.0599 mm/px, seen from behind: xv to the viewer's right, zv up):
        # XLR at (-4.4, 8.0) in a black housing, the 3.5 mm jack at (-18.6, 2.0), screws at (-11.4, 18.8) and
        # (9.3, -2.8), USB-C at (18.0, -9.3). No text.
        Mr = T(0, MIC_PIVOT, 0) @ R(-90, "X")       # local +Z -> world +Y (out of the rear); local y -> world -z

        def rp(xv, zv):
            return Mr @ T(-xv * MM, -zv * MM, 0)
        A.lathe([(0, 0.0), (0.0085, 0.0), (0.0085, 0.0008), (0, 0.0008)], 32, "satin", rp(-4.4, 8.0))
        A.lathe([(0, 0.0), (0.0062, 0.0), (0.0062, 0.0009), (0, 0.0009)], 32, "port", rp(-4.4, 8.0))
        for k in range(3):
            a = math.radians(90 + 120 * k)
            A.lathe([(0, 0.0), (0.0008, 0.0), (0.0008, 0.0035), (0, 0.0035)], 8, "gold",
                    rp(-4.4 + 3.3 * math.cos(a), 8.0 + 3.3 * math.sin(a)) @ T(0, 0, -0.002))
        A.lathe([(0.0019, 0.0), (0.0042, 0.0), (0.0042, 0.0007), (0.0019, 0.0007)], 24, "chrome", rp(-18.6, 2.0))
        A.lathe([(0, -0.0005), (0.0019, -0.0005), (0.0019, 0.0002), (0, 0.0002)], 16, "port", rp(-18.6, 2.0))
        for xv, zv in ((-11.4, 18.8), (9.3, -2.8)):
            A.lathe([(0, 0.0), (0.0016, 0.0), (0.0016, 0.0005), (0, 0.0005)], 16, "satin", rp(xv, zv))
        rbox(A, 0.0092, 0.0034, 0.0006, 0.0016, 0, 0, 2, "satin", rp(18.0, -9.3))
        rbox(A, 0.0084, 0.0026, 0.0008, 0.0012, 0, 0, 2, "port", rp(18.0, -9.3))
        knobs = fin(A, f"mic_knobs{sfx}", mp, coll, tilt, lite=lite)
        out["mic_body"].append(knobs.name)
        # the LED: an arc (about 130 degrees) on the top of the ring, 4 mm wide, a rainbow along it
        # (green, yellow, orange, pink, detail-led-ring-windscreen.jpg); its own UV-mapped mesh
        na = 12 if lite else 40
        r_led = MIC_R + 0.00035
        rings = []
        for zz in (zl + 0.0055, zl + 0.0095):
            rings.append([(r_led * math.cos(math.radians(25 + 130 * k / na)), r_led * math.sin(math.radians(25 + 130 * k / na)), zz)
                          for k in range(na + 1)])
        led = uv_strip(f"mic_led{sfx}", rings, mp["led_rainbow"], coll, tilt, Mb)
        out["mic_led"] = [led.name]
        # the side wordmark, along the axis, black pad print, conformed to the tapered body; on both sides,
        # letter tops toward the stem (Shure's three-quarter shot). Real spot (side-profile-yoke-open.jpg,
        # 0.175 mm/px from the 50 mm rear plate to knob axis): SHURE runs 6 to 36 mm from the rear plate, about
        # 30 x 5 mm. Ours: 15.5 to 43.5 mm behind the knob axis, 6 mm clear of the knob (9.35 mm radius, 4.5 mm
        # proud), so no letter goes under it from any angle the photos show.
        yc = 0.0295
        sides = [brand("mic", body, "mic_body_brand", sfx, lite, at=(s * MIC_R, yc, 0), normal=(s, 0, 0),
                       up=(0, 0, 1), height=6.3 * MM, max_width=28 * MM, finish="printed", colour="#1c1c1d",
                       conform=body) for s in (1, -1)]
        mb = join_into(*sides)
        # the rear plate: centred, 8.3 mm under the plate's centre, about 3 mm, dark grey
        rb = brand("mic", body, "mic_rear_brand", sfx, lite, at=(0, MIC_PIVOT, -0.0083), normal=(0, 1, 0),
                   up=(0, 0, 1), height=2.8 * MM, finish="printed", colour="#3c3c3e")
        out["mic_brand"] = [mb.name, rb.name]
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
        # the screw's slim T-handle with ball tips, under the round pad
        cyl(A, 0.0028, (-0.032, 0, -0.088), (0.032, 0, -0.088), "chrome", 12)
        for sx in (-1, 1):
            A.lathe([(0, -0.0045), (0.0032, -0.0032), (0.0045, 0), (0.0032, 0.0032), (0, 0.0045)], 16, "chrome",
                    T(sx * 0.034, 0, -0.088))
        A.lathe([(0, -0.091), (0.007, -0.091), (0.007, -0.082), (0, -0.082)], 16, "chrome")
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
        # the padded cover: a soft rounded-square sleeve (6 mm corners, 5 mm rounded ends), velcro tabs at the ends
        rbox(A, ch, cw, L - 0.050, 0.006 if not rough else 0.0, 0.005 if not rough else 0.0,
             0.005 if not rough else 0.0, cs, "pad", Mx @ T(0, 0, 0.025))
        if not rough:
            for e in (0.034, L - 0.040):
                rbox(A, ch + 0.0016, cw + 0.0016, 0.008, 0.0065, 0.001, 0.001, cs, "pad", Mx @ T(0, 0, e))
                rbox(A, 0.004, 0.006, 0.007, 0.001, 0.001, 0.001, 1, "pad", Mx @ T(ch / 2 + 0.002, 0, e + 0.0005))
            for e in (0.0, L):                   # the hinge discs at both ends (outside the cover), screw heads
                for s in (-1, 1):
                    cyl(A, ARM_HINGE_R * (0.9 if e else 0.8), (e, s * 0.019, 0), (e, s * (ARM_W / 2 - 0.006), 0), "white", seg)
                    cyl(A, 0.006, (e, s * (ARM_W / 2 - 0.006), 0), (e, s * (ARM_W / 2 - 0.0045), 0), "chrome", 16)
            # the cable channel under the cover
            rbox(A, 0.010, 0.006, L - 0.06, 0.002, 0, 0, 2, "white", Mx @ T(-ch / 2 + 0.002, 0, 0.03))
        return fin(A, name, mp, coll, parent, bevel=0.0012, lite=lite)

    lower = segment(f"mic_arm_lower{sfx}", ARM_L1, sh)
    brands_ = []

    def cover_brand(seg_obj, L, nm):
        # white-on-white, 15 mm, on the cover's +Y side near the far end, letter tops to the arm's top, reading
        # from the far end towards the base (the photo: R at the wrist end of the upper arm, at the elbow end
        # of the lower, upright)
        if rough:
            return
        brands_.append(brand("boom_arm", seg_obj, nm, sfx, lite, at=(L - 0.095, ARM_COVER[0] / 2, 0),
                             normal=(0, 1, 0), up=(0, 0, 1), height=15 * MM, finish="printed",
                             colour="#f7f7f5", max_width=73 * MM).name)
    cover_brand(lower, ARM_L1, "boom_lower_brand")
    A = P.Mesh()      # the elbow: the outer hinge discs (a jog plate between two pivots when ARM_JOG > 0)
    for sy in (-1, 1):
        for zz in sorted({0.0, -ARM_JOG}):
            cyl(A, ARM_HINGE_R, (ARM_L1, sy * (ARM_W / 2 - 0.007), zz), (ARM_L1, sy * ARM_W / 2, zz), "white", seg)
            cyl(A, 0.006, (ARM_L1, sy * ARM_W / 2, zz), (ARM_L1, sy * (ARM_W / 2 + 0.0015), zz), "chrome", 16)
        if ARM_JOG > 0:
            rbox(A, 2 * ARM_HINGE_R, 0.007, ARM_JOG, 0.0, 0, 0, 0, "white",
                 T(ARM_L1, sy * (ARM_W / 2 - 0.0035), -ARM_JOG))
    fin(A, f"mic_arm_elbow{sfx}", mp, coll, sh, bevel=0.001, lite=lite)
    el = empty(f"mic_j_elbow{sfx}", sh, (ARM_L1, 0, -ARM_JOG), (0, -math.radians(pose["elbow"]), 0), coll)
    upper = segment(f"mic_arm_upper{sfx}", ARM_L2, el)
    cover_brand(upper, ARM_L2, "boom_upper_brand")
    if not rough:
        # the small mark on the clamp's cone, over the C-clamp's back (+Y), a glossy true-black pad print
        # (detail-white-clamp-mount.jpg)
        zc_, rc_ = 0.0095, 0.048 - 0.028 * (0.0095 - 0.004) / 0.028
        brands_.append(brand("boom_arm", static, "boom_clamp_brand", sfx, lite, at=(0, rc_, zc_),
                             normal=(0, 1, 1), up=(0, -1, 1), height=3.6 * MM, finish="ink",
                             colour="#050506", max_width=18 * MM, conform=static).name)
    level = math.radians(pose["shoulder"] + pose["elbow"])
    wr = empty(f"mic_j_wrist{sfx}", el, (ARM_L2, 0, 0), (0, level, 0), coll)
    wy = empty(f"mic_j_wrist_yaw{sfx}", wr, (0, 0, 0), (0, 0, math.radians(pose["wrist"])), coll)
    A = P.Mesh()
    # the head: a block hanging from the wrist hinge, a swivel, the 3/8 stud pointing down
    rbox(A, 0.030, 0.034, 0.040, 0.008, 0.006, 0.004, cs, "white", T(0, 0, -0.040))
    if not rough:
        A.lathe([(0, -0.050), (0.012, -0.050), (0.012, -0.040), (0, -0.040)], seg, "steel")
        A.lathe([(0, -ARM_TIP), (0.0045, -ARM_TIP), (0.0045, -0.050), (0, -0.050)], 16, "brass")   # the 3/8 thread
    tip = fin(A, f"mic_arm_tip{sfx}", mp, coll, wy, bevel=0.001, lite=lite)
    stem_top = empty(f"mic_j_mount{sfx}", wy, (0, 0, -ARM_TIP + 0.010), coll=coll)
    hang, tilt, head = build_mic_head(coll, mp, stem_top, rough, lite, sfx)
    tilt.rotation_euler = (math.radians(pose["tilt"]), 0, 0)
    out = {"mic_static": [static.name, knuckle.name], "boom_brand": brands_,
           "mic_arm": [lower.name, f"mic_arm_elbow{sfx}", upper.name, tip.name]}
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
    L1 = math.hypot(ARM_L1, ARM_JOG)                        # shoulder to the upper arm's pivot
    off = math.atan2(ARM_JOG, ARM_L1)
    D = min(math.hypot(h, v), L1 + ARM_L2 - 1e-4)
    a = math.acos(max(-1, min(1, (L1 ** 2 + D ** 2 - ARM_L2 ** 2) / (2 * L1 * D))))
    base = math.atan2(v, h)
    se = base + a                                            # elbow up
    shoulder = math.degrees(se + off)
    ex, ez = L1 * math.cos(se), L1 * math.sin(se)
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
            cam_clamp_z=0.64, cam_at=(0.14, -0.26, 0.47), cam_yaw=0.0,
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
    for i, e in enumerate(lay["kl"], 1):        # (x, y, desk z, clamp yaw[, panel pan relative to the clamp])
        x, y, z, yaw = e[:4]
        root, d = build_keylight(i, coll, mp, rough, lite, pole_h=lay.get("pole_h", POLE_H),
                                 tilt=lay.get("kl_tilt", 0.0), sfx=sfx, pan=e[4] if len(e) > 4 else 0.0)
        root.location = (x, y, z)
        root.rotation_euler = (0, 0, math.radians(yaw))
        kls.append(root)
        add({f"keylight_{i}": [n for v in d.values() for n in v]})
        add(d)
    # camera on the flex arm from key light 1's pole
    x, y, z = lay["kl"][0][:3]
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


def facing_yaw(frm, to):
    """The yaw (degrees) that turns a part's front (-Y) from frm towards to (x, y)."""
    return math.degrees(math.atan2(to[0] - frm[0], -(to[1] - frm[1])))


def room_layout(mode="plan"):
    """Room placement, read from plan v3 (approved 2026-10-26: the arms build's proposal B, the shelf at 1.95).
    Key-light clamps turn by plan's KL_CLAMP_YAW (the jaw towards the desk edge); the panels aim at KL_AIM.
    The mic's clamp jaw faces the main run's outer short edge (plan v3 MIC["clamp_yaw"])."""
    from lib import plan_v3 as PL
    top, aim, ear = PL.TOP, PL.KL_AIM, PL.EAR_SEATED
    kl = []
    for (x, y), cyaw in zip(PL.KL_POLE, PL.KL_CLAMP_YAW):
        kl.append((x, y, top, cyaw, facing_yaw((x, y), aim) - cyaw))
    return dict(kl=kl, pole_h=PL.KL_Z - top - KL_ADAPT[1] - KL_NECK[1], cam_at=PL.CAM_AT,
                cam_clamp_z=PL.CAM_ARM_FROM[2] - top, cam_yaw=facing_yaw(PL.CAM_AT[:2], ear[:2]), cam_pitch=-3.0,
                mic_clamp=(*PL.MIC["clamp"], top), mic_yaw=PL.MIC["clamp_yaw"], mic_pose=None, mic_capsule=PL.MIC["capsule"],
                mic_aim=ear)


def build_set(layout, collection=None, lite=False):
    """For the room test: the whole set at room coordinates (layout keys as DEMO)."""
    return build(False, lite, collection, layout)


# ---------------------------------------------------------------------------
# 4. the photo views
# ---------------------------------------------------------------------------
def outline_views(names):
    if PART == "camera":
        return [x for x in _all_views(names) if x["name"].startswith("camera-")]
    return [x for x in _all_views(names) if not x["name"].startswith("camera-")]   # the camera is approved


def _all_views(names):
    v = []
    if PART == "camera":
        names = dict(names, kl_panel=[], kl_glow=[], kl_static=[], mic_body=[], mic_yoke=[], mic_arm=[], mic_static=[])
    kl = names["kl_panel"][:1] + names["kl_glow"][:1] + [n for n in names["kl_static"] if "_mount" in n][:1]
    kl = [n for n in kl if n.startswith("keylight_1")]
    v.append(dict(name="keylight-front", title="Key Light: front (Elgato render) vs our model",
                  photo=os.path.join(R_KL, "front-on-pole.jpg"), mask=0.5, crop=(800, 2020, 360, 1560),
                  objects=kl, camera={"mode": "fit", "view": "front"},
                  explain="the corner radius (58 mm, measured) runs a little tight at the top corners; the mount under the panel is cropped at the photo's stand"))
    v.append(dict(name="keylight-side", title="Key Light: side (Elgato render) vs our model",
                  photo=os.path.join(R_KL, "side.jpg"), mask=0.5, crop=(1200, 1700, 290, 1300),
                  objects=[n for n in kl if "_mount" not in n], camera={"mode": "fit", "view": "right", "tilts": [-3.0, 0.0, 3.0]},
                  explain="the panel only. The references disagree on the back box: side.jpg shows a bump 150 mm up from the bottom edge, back-in-use.jpg a landscape box (110 x 75) high on the back; ours follows back-in-use (coordinator, 2026-10-26)"))
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
                  photo=os.path.join(R_MIC, "back.png"), mask="alpha", crop=(0, 3000, 232, 3000),
                  objects=mic, prepare=mic_view("back"), camera={"mode": "ortho", "view": "back"},
                  explain="the photo's stem runs off the top edge: the crop starts at the stem block, our stem is not drawn"))
    v.append(dict(name="mic-front", title="MV7+ white: front, hanging (Shure image) vs our model",
                  photo=os.path.join(R_MIC, "front.png"), mask="alpha", crop=(0, 3000, 578, 3000),
                  objects=mic, prepare=mic_view("front"),
                  camera={"mode": "free", "view": "front", "yaws": [-6.0, 0.0, 6.0], "tilts": [-10.0, 0.0, 10.0],
                          "h_range": (-0.2, 0.2), "distances": [1.0, 1.6, 2.4]},
                  explain="Shure's hanging render tips the mic toward the viewer at an unknown angle; ours is posed at 35 degrees"))
    v.append(dict(name="mic-3q", title="MV7+ white: three-quarter, hanging (Shure image) vs our model",
                  photo=os.path.join(R_MIC, "three-quarter.png"), mask="alpha", crop=(0, 3000, 598, 3000),
                  objects=mic, prepare=mic_view("3q"),
                  camera={"mode": "free", "view": "front", "yaws": [-40.0, -30.0, -20.0, 20.0, 30.0, 40.0],
                          "tilts": [-10.0, 0.0, 10.0], "h_range": (-0.2, 0.2), "distances": [1.0, 1.6, 2.4]},
                  explain="the photo's stem runs off the top edge"))
    v.append(dict(name="arm-side", title="PSA1+ white: folded, side (RODE image) vs our model",
                  photo=os.path.join(R_ARM, "white-folded-side-2000.png"), mask="alpha",
                  objects=names["mic_arm"] + [n for n in names["mic_static"] if "knuckle" in n],
                  prepare=arm_folded(), camera={"mode": "free", "view": "front", "yaws": [176.0, 180.0, 184.0],
                                                "tilts": [-4.0, 0.0, 4.0], "distances": [2.0, 3.0, 4.0]},
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
        if which == "back":                  # the rear plate is +Y in the hanger's frame: the "back" camera sees it
            hang.matrix_world = Matrix.Identity(4)
            tilt.rotation_euler = (0, 0, 0)
        elif which in ("front", "3q"):
            hang.matrix_world = Matrix.Identity(4)
            tilt.rotation_euler = (math.radians(35 if which == "front" else 25), 0, 0)
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
        pose_mic("", swivel=0, shoulder=0, elbow=-170.5, wrist=0, tilt=0)

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
        sc.eevee.use_raytracing = True          # the lens glass refracts in EEVEE too


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
    from lib import compare as _cmp
    _lo, _hi = _cmp.world_bbox(["cam_arm"])
    fa_c = (_lo + _hi) / 2
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
        ("flex-clamp", "Flex Arm L: the clamp on the key light's pole", os.path.join(AI, "19-camera-arm", "master-mount-l-pole-clamp.jpg"),
         kl @ Vector((0.20, -0.24, DEMO["cam_clamp_z"] + 0.06)), kl @ Vector((0.01, -0.03, DEMO["cam_clamp_z"])), 50),
        ("flex-joints", "Flex Arm L: the ball joints and socket clamps", os.path.join(AI, "19-camera-arm", "detail-joints-crop-from-hero.jpg"),
         fa_c + Vector((0.30, -0.42, 0.12)), fa_c, 50),
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
