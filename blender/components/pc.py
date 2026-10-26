"""pc: the AI lab's training rig, a Lian Li O11 Vision (white, O11VW) with an all-white build and an
NVIDIA RTX 5090 Founders Edition, at real size, away from the room layout (component, 2026-10-24).
No real logos; our invented names (content/room-brands.json) where the makers' sit: KAIRO on the case,
NOVRA lit on the card's top edge (decision 2026-10-26).

Always headless:

    B="/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python"
    /opt/anaconda3/bin/python3 blender/components/pc.py refs          the traced photo masks (plain Python)
    $B blender/tools/outline_check.py -- blender/components/pc.py      the 15-minute gate
    $B blender/components/pc_render.py -- [stages]                     build, stills, compare, closeups, export

Frame (MESHES.md): front at -Y, right at +X, Z up; origin at the case's bottom centre on the floor.
The glass side is the LEFT side (-X) seen from the front; the rear chamber (PSU, cables, radiator) is
behind the motherboard tray on the right (+X). The card lies horizontal under the glass, fans down,
backplate up, its top edge (the light bar) toward the side glass.

Every number is tagged OFFICIAL (maker), MEASURED (from a photo, scale from an official size; the photo
is named) or EST (estimated, from what).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(BLENDER_DIR, ".."))
sys.path.insert(0, BLENDER_DIR)

try:
    import bpy
    import bmesh
    from mathutils import Matrix, Vector
except ImportError:          # plain Python: refs and the blueprint read the numbers
    bpy = None

NAME = "pc"
MM = 0.001
LAB = os.path.join(REPO, "docs", "moodboard", "local", "ai-lab")
REF_CASE = os.path.join(LAB, "15-pc-case")
REF_GPU = os.path.join(LAB, "16-gpu")
FOOTAGE = os.path.join(REPO, "video-local", "footage", "2026-10-24-components", NAME)
REFS_OUT = os.path.join(FOOTAGE, "refs")          # traced cut-outs and small copies (never the originals)

# ---------------------------------------------------------------------------
# 1. the case: Lian Li O11 Vision, white
# ---------------------------------------------------------------------------
CASE_W = 304.0 * MM      # OFFICIAL lian-li.com: 480 (D) x 304 (W) x 464.5 (H) mm
CASE_D = 480.0 * MM      # OFFICIAL
CASE_H = 464.5 * MM      # OFFICIAL (floor to top glass, feet included)
FOOT_H = 29.5 * MM       # MEASURED edge-io.jpg (58 px at 0.482 mm/px) and glass-side.jpg (58 px at 0.508)
RAIL_H = 11.0 * MM       # MEASURED glass-side.jpg: the side skirt under the body between the feet (22 px)
RAIL_T = 8.0 * MM        # EST: the skirt's thickness (it never shows in the front photo's gap)
FOOT_L_TOP = 76.0 * MM   # MEASURED edge-io.jpg: glass-side feet, front face 157 px wide at the top ...
FOOT_L_BOT = 52.0 * MM   # MEASURED ... 107 px at the floor (the inner face slants)
FOOT_R_TOP = 111.0 * MM  # MEASURED edge-io.jpg: right feet (the front one carries the I/O), 231 px ...
FOOT_R_BOT = 84.0 * MM   # MEASURED ... 175 px at the floor
FOOT_Y_TOP = 59.0 * MM   # MEASURED glass-side.jpg / solid-side.jpg: the feet along the side, 116 px ...
FOOT_Y_BOT = 38.6 * MM   # MEASURED ... 76 px at the floor (the slant is below the skirt only)
GLASS_FS = 4.0 * MM      # OFFICIAL: 4 mm tempered glass front and side
GLASS_TOP = 3.0 * MM     # OFFICIAL: 3 mm tempered glass top
PILLAR_W = 69.0 * MM     # MEASURED edge-io.jpg: the white front panel of the rear chamber (143 px)
TRAY_X = 57.0 * MM       # EST: the motherboard tray's plane (rear chamber about 90 mm inside for the
                         # 86 mm PSU on edge, as rear-chamber.jpg shows it)
BASE_T = 17.5 * MM       # MEASURED edge-io.jpg: the white bottom frame seen through the front glass
MESH_FRONT = (-204.7 * MM, -53.5 * MM)    # MEASURED solid-side.jpg: the right panel's front mesh (Y)
MESH_REAR = (89.0 * MM, 226.0 * MM)       # MEASURED solid-side.jpg: the rear mesh (Y)
MESH_Z = (53.0 * MM, 439.0 * MM)          # MEASURED solid-side.jpg (Z of both)
PSU_BRACKET = dict(x=(52.0 * MM, 148.0 * MM), y=(240.0 * MM, 254.0 * MM), z=(80.0 * MM, 231.0 * MM))
#                  MEASURED solid-side.jpg: the PSU bracket stands 14 mm out of the back, z 80..231;
#                  x EST from back.jpg (the rear chamber's width)
POWER_BTN_Z = 387.0 * MM  # MEASURED edge-io.jpg / solid-side.jpg: the power button on the front-right edge
IO_Z = 15.0 * MM          # MEASURED edge-io.jpg: the front I/O row on the right foot (centres)
IO_X = (65.9, 82.8, 102.5, 124.2)         # MEASURED edge-io.jpg: jack, USB-C, USB-A, USB-A (x, mm)

# ---------------------------------------------------------------------------
# 2. the card: RTX 5090 Founders Edition (card frame: x along the length from the bracket end, y up
#    from the PCIe edge to the top edge, z out of the fan face; mapped into the case by GPU_POSE)
# ---------------------------------------------------------------------------
GPU_L = 304.0 * MM       # OFFICIAL nvidia.com: 304 mm long
GPU_H = 123.0 * MM       # MEASURED front-fans.png and back.png: length / height 2.47 in both (304 / 2.47).
                         # NVIDIA's 137 mm is not the shroud: with the PCIe fingers it measures 135 mm
GPU_T = 40.0 * MM        # OFFICIAL-ish: 2-slot, 40 mm (Tom's Hardware, Cowcotland; SOURCES.md)
GPU_R = 11.0 * MM        # MEASURED front-fans.png: the shroud's corner radius
GPU_FAN_R = 57.5 * MM    # MEASURED front-fans.png: the fan ring, 1468 px across
GPU_HUB_R = 19.4 * MM    # MEASURED front-fans.png
GPU_FAN_X = (57.9 * MM, 243.2 * MM)       # MEASURED front-fans.png: fan centres from the bracket end
GPU_X_TOP = (91.6 * MM, 211.6 * MM)       # MEASURED front-fans.png: where the X's arms meet the long edges
GPU_FINGERS = (45.0 * MM, 128.0 * MM, 11.0 * MM)  # MEASURED front-fans.png: PCIe fingers x0, x1, depth
GPU_BLADES = 7           # MEASURED front-fans.png (seven blades per fan)
BRACKET_H = 120.0 * MM   # OFFICIAL PCIe full-height bracket
BRACKET_Y = (-28.5 * MM, 93.2 * MM)      # MEASURED front-fans.png: the bracket from below the PCIe edge to
                                         # under the shroud's top (121.7 mm: a standard bracket, 120 mm)
BRACKET_X = (-3.0 * MM, 4.5 * MM)        # MEASURED front-fans.png: the bracket and its port frame, edge-on
PCB_TAB = (44.0 * MM, 145.0 * MM)        # MEASURED front-fans.png close-up: the board's edge from the fingers on
PCB_Z = -32.0 * MM                       # EST three-quarter-io.png: the board sits near the backplate
                                         # (its fingers show over the far edge from above)
# where it sits: slot 1 under the rear fans; MEASURED build-1.jpg (fractions of the body height) and EST
GPU_TOP_Z = 212.0 * MM   # backplate top
GPU_BRACKET_Y = 233.0 * MM               # the shroud's bracket end: the bracket's face in the rear opening
GPU_SLOT_X = 36.0 * MM                   # the shroud's PCIe edge, 12 mm off the board (fingers in the slot)

# ---------------------------------------------------------------------------
# 3. the build inside (all white): EST from build-1.jpg, build-3.jpg, official-white-build.webp
# ---------------------------------------------------------------------------
FAN = 120.0 * MM         # Lian Li UNI FAN TL 120, white (KitGuru's build; SOURCES.md): 120 x 120 x 28
FAN_T = 28.0 * MM
SIDE_FANS = dict(x=TRAY_X, y=-112.0 * MM, z=(110.0 * MM, 232.0 * MM, 354.0 * MM))   # face -X, intake
REAR_FANS = dict(x=-80.0 * MM, y=236.0 * MM, z=(398.0 * MM, 277.0 * MM))           # face +Y, exhaust
BOTTOM_FANS = dict(x=-86.0 * MM, y=(150.0 * MM, 28.0 * MM, -94.0 * MM), z=47.0 * MM)  # face +Z, intake
BOARD = dict(x=50.0 * MM, y=(-34.0 * MM, 210.0 * MM), z=(52.0 * MM, 357.0 * MM))   # ATX 305 x 244
CPU = dict(y=110.0 * MM, z=280.0 * MM)    # MEASURED glass-side.jpg: the tray's CPU cut-out centre
PSU = dict(x=(62.0 * MM, 148.0 * MM), y=(90.0 * MM, 230.0 * MM), z=(83.0 * MM, 233.0 * MM))  # rear-chamber.jpg

# ---------------------------------------------------------------------------
# 4. the reference photos and their traced silhouettes (KitGuru's photos have busy backgrounds and
#    glass: the outline was traced by hand on grid zooms, pixels of the original image)
# ---------------------------------------------------------------------------
POLYS = {
    "edge-io.jpg": [(672, 110), (1258, 107), (1281, 970), (1281, 1030), (1106, 1031), (1050, 970), (808, 971),
                    (758, 1029), (652, 1029), (650, 969)],
    "glass-side.jpg": [(479, 117), (1423, 110), (1425, 1025), (1349, 1025), (1309, 988), (596, 987), (558, 1023),
                       (482, 1023)],
    "solid-side.jpg": [(497, 127), (1354, 123), (1354, 542), (1379, 542), (1379, 812), (1354, 812), (1351, 950),
                       (1286, 949), (1241, 906), (610, 915), (574, 950), (504, 950)],
    "three-quarter.jpg": [(429, 261), (949, 84), (1291, 206), (1294, 1013), (1203, 1019), (1150, 968), (1035, 982),
                          (999, 1046), (930, 1050), (869, 1041), (845, 1000), (437, 946), (421, 972), (390, 972),
                          (388, 905)],
    "back.jpg": [(468, 161), (958, 70), (1290, 178), (1288, 870), (1240, 880), (1219, 843), (1059, 882), (1029, 946),
                 (959, 950), (916, 942), (880, 886), (532, 800), (506, 837), (472, 838)],
    "official-white-3q.jpg": [(59, 131), (260, 38), (530, 76), (542, 546), (466, 546), (422, 520), (315, 521),
                              (315, 552), (248, 552), (240, 530), (130, 526), (108, 543), (72, 543), (55, 521)],
}
GPU_PHOTOS = ("front-fans.png", "back.png", "three-quarter-io.png", "three-quarter-logo.png")


def cutout_path(photo):
    pre = "gpu-" if photo in GPU_PHOTOS else "case-"
    return os.path.join(REFS_OUT, pre + os.path.splitext(photo)[0] + "-cut.png")


def make_refs():
    """Plain Python: each traced photo as an RGBA cut-out (alpha = the traced silhouette) and the
    card's big renders at 1600 px wide with their own alpha; into REFS_OUT, never over the originals."""
    from PIL import Image, ImageDraw
    os.makedirs(REFS_OUT, exist_ok=True)
    out = {}
    for f, poly in POLYS.items():
        im = Image.open(os.path.join(REF_CASE, f)).convert("RGBA")
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        im.putalpha(m)
        p = cutout_path(f)
        im.save(p)
        out[f] = p
    for f in GPU_PHOTOS:
        im = Image.open(os.path.join(REF_GPU, f)).convert("RGBA")
        k = 1600 / im.size[0]
        im = im.resize((1600, int(round(im.size[1] * k))), Image.LANCZOS)
        p = cutout_path(f)
        im.save(p)
        out[f] = p
    print(json.dumps(out, indent=1))
    return out


# ---------------------------------------------------------------------------
# 5. geometry helpers (Blender)
# ---------------------------------------------------------------------------
def _P():
    from lib import parts
    return parts


GPU_TONES = {
    "gunmetal": dict(base="#343233", rough=0.5, metal=0.4),
    "rim": dict(base="#7d7774", rough=0.3, metal=1.0),
    "fins": dict(base="#050506", rough=0.8, spec=0.1),
    "gpu_fan": dict(base="#151617", rough=0.55, spec=0.3),
    "gpu_hub": dict(base="#1f2022", rough=0.3, metal=0.85),
}


def mats():
    """The materials, created once. Glass is a plain principled glass (transmission 1) so the GLB
    carries KHR_materials_transmission; the site uses its own simple transparent material."""
    from lib import materials as M
    def get(name, **v):
        return bpy.data.materials.get(name) or M.principled(name, **v)
    d = {
        "white": get("mat_pc_white", base="#eceeef", rough=0.42, spec=0.45),          # white powder coat
        "white_mesh": get("mat_pc_white_mesh", base="#e3e5e6", rough=0.6, spec=0.35),  # perforated white
        "grey": get("mat_pc_grey", base="#a9adb0", rough=0.6, spec=0.3),               # grey rubber brackets
        "port": get("mat_pc_port", base="#060607", rough=0.9, spec=0.15),
        "steel": get("mat_pc_steel", base="#b9bcc0", rough=0.3, metal=1.0),
        "gold": get("mat_pc_gold", base="#d9b25a", rough=0.25, metal=1.0),
        "black": get("mat_pc_black", base="#141516", rough=0.5),
        "pcb": get("mat_pc_pcb", base="#e8e9ea", rough=0.5, spec=0.4),                # white board
        "heatsink": get("mat_pc_heatsink", base="#e6e7e8", rough=0.35, metal=0.3),
        "fan_white": get("mat_pc_fan", base="#f1f2f3", rough=0.45, spec=0.4),
        "blade": get("mat_pc_blade", base="#f4f5f6", rough=0.35, spec=0.5, sss=0.15),
        "cable": get("mat_pc_cable", base="#edeeee", rough=0.7, sheen=0.4),            # white sleeving
        # the card's tones are matched to front-fans.png / back.png region by region (pc_render tones)
        "gunmetal": get("mat_gpu_gunmetal", **GPU_TONES["gunmetal"]),   # dark warm grey, satin
        "rim": get("mat_gpu_rim", **GPU_TONES["rim"]),                   # the brighter edge frame and lips
        "fins": get("mat_gpu_fins", **GPU_TONES["fins"]),
        "gpu_fan": get("mat_gpu_fan", **GPU_TONES["gpu_fan"]),           # near-black blades
        "gpu_hub": get("mat_gpu_hub", **GPU_TONES["gpu_hub"]),
        "bracket": get("mat_gpu_bracket", base="#6d6e70", rough=0.4, metal=0.9),          # grey, as the renders
        "brass": get("mat_pc_brass", base="#b49c6c", rough=0.35, metal=1.0),               # the thumb screws
        "lcd": get("mat_pc_lcd", base="#0b0c0e", rough=0.15, spec=0.6),
    }
    if "mat_pc_glass" not in bpy.data.materials:
        from lib import materials as M
        g = M.principled("mat_pc_glass", base="#eef7f5", rough=0.02, spec=0.5)
        b = next(n for n in g.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["IOR"].default_value = 1.52
        b.inputs["Alpha"].default_value = 1.0       # true glass in Cycles; the lite GLB has a blended one
        # Cycles: the camera sees glass, while shadow and diffuse rays pass straight through (no caustics,
        # so a true glass box would leave the inside dark); EEVEE and the GLBs use the Principled alone
        nt = g.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        lp = nt.nodes.new("ShaderNodeLightPath")
        mx = nt.nodes.new("ShaderNodeMath")
        mx.operation = "MAXIMUM"
        nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
        nt.links.new(lp.outputs["Is Diffuse Ray"], mx.inputs[1])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mx.outputs[0], mix.inputs[0])
        nt.links.new(b.outputs[0], mix.inputs[1])
        nt.links.new(tr.outputs[0], mix.inputs[2])
        out.target = "CYCLES"
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        o2 = nt.nodes.new("ShaderNodeOutputMaterial")
        o2.target = "EEVEE"
        nt.links.new(b.outputs[0], o2.inputs["Surface"])
        for k, v in (("surface_render_method", "DITHERED"), ("use_raytrace_refraction", True),
                     ("thickness_mode", "SLAB")):
            try:
                setattr(g, k, v)
            except (AttributeError, TypeError):
                pass
        g.diffuse_color = (0.85, 0.95, 0.93, 0.25)
        # the glass's green-blue edge (SOURCES.md): a darker teal on the thin faces
        e = M.principled("mat_pc_glass_edge", base="#5fae9e", rough=0.1, spec=0.5)
        b2 = next(n for n in e.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b2.inputs["Transmission Weight"].default_value = 0.25
    d["glass"] = bpy.data.materials["mat_pc_glass"]
    d["glass_edge"] = bpy.data.materials["mat_pc_glass_edge"]
    from lib import materials as M
    d["fan_light"] = bpy.data.materials.get("mat_pc_fan_light") or M.emission("mat_pc_fan_light", "#eaf4ff", 6.0)
    d["gpu_light"] = bpy.data.materials.get("mat_gpu_light") or M.emission("mat_gpu_light", "#f4f7ff", 5.0)
    return d


def box(A, x0, x1, y0, y1, z0, z1, key, m=None, top=True, bottom=True):
    A.prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, key, m=m, top=top, bottom=bottom)


def finish(A, name, coll, parent, smooth=30):
    o = A.finish(name, mats(), facing="+Z", at=(0, 0, 0), collection=coll, parent=parent, smooth=smooth)
    return o


def empty(name, coll, parent=None, at=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    coll.objects.link(o)
    o.parent = parent
    o.location = at
    o.empty_display_size = 0.05
    from lib import names
    names.set_name(o, name, data=False)
    return o


# ---------------------------------------------------------------------------
# 6. the case
# ---------------------------------------------------------------------------
def foot_profile_x(side, top_w, bot_w):
    """The front face of a foot (x across), as an outline in (x, z): outer edge vertical, inner edge
    slanting from top_w at FOOT_H to bot_w at the floor."""
    s = -1 if side == "L" else 1
    xo = s * CASE_W / 2
    return [(xo, 0.0), (xo - s * bot_w, 0.0), (xo - s * top_w, FOOT_H), (xo, FOOT_H)]


def case_feet(A, key, rough=False):
    """Four corner feet: the front-view trapezoid (full height) cut by the side-view trapezoid (slant
    below the skirt). Built as a solid with 8 + 2 vertices per foot."""
    zs = FOOT_H - RAIL_H                   # the side slant runs from the floor to the skirt
    for side, (tw, bw) in (("L", (FOOT_L_TOP, FOOT_L_BOT)), ("R", (FOOT_R_TOP, FOOT_R_BOT))):
        s = -1 if side == "L" else 1
        xo = s * CASE_W / 2
        for end in (-1, 1):                # front (-Y) and back (+Y)
            yo = end * CASE_D / 2
            yi_top, yi_bot = yo - end * FOOT_Y_TOP, yo - end * FOOT_Y_BOT
            # outline in (x, z) of the front face, extruded along y, with the inner y face slanted below zs
            def P(x, y, z):
                return (x, y, z)
            xi_t, xi_b = xo - s * tw, xo - s * bw
            # vertices: outer face at y = yo, inner face profile in y depends on z
            def inner_y(z):
                return yi_bot + (yi_top - yi_bot) * min(1.0, z / zs) if zs > 0 else yi_top
            def xin(z):
                return xi_b + (xi_t - xi_b) * (z / FOOT_H)
            zlev = [0.0, zs, FOOT_H]
            rings = []
            for z in zlev:
                xi = xin(z)
                yi = inner_y(z)
                rings.append([(xo, yo, z), (xi, yo, z), (xi, yi, z), (xo, yi, z)])
            vs = [A.verts(r) for r in rings]
            # orient each ring CCW seen from +Z
            def area(r):
                return sum(r[i][0] * r[(i + 1) % 4][1] - r[(i + 1) % 4][0] * r[i][1] for i in range(4))
            if area(rings[0]) < 0:
                vs = [list(reversed(v)) for v in vs]
            for a, b in zip(vs, vs[1:]):
                A.strip(a, b, key)
            A.face(list(reversed(vs[0])), key)
            A.face(vs[-1], key)


def build_case_rough(coll, parent):
    from lib import parts as P
    A = P.Mesh()
    hw, hd = CASE_W / 2, CASE_D / 2
    box(A, -hw, hw, -hd, hd, FOOT_H, CASE_H, "white")
    case_feet(A, "white")
    for s in (-1, 1):                       # the side skirts
        x0, x1 = (s * hw - s * RAIL_T, s * hw) if s > 0 else (-hw, -hw + RAIL_T)
        box(A, min(x0, x1), max(x0, x1), -hd + FOOT_Y_TOP, hd - FOOT_Y_TOP, FOOT_H - RAIL_H, FOOT_H, "white")
    b = PSU_BRACKET
    box(A, b["x"][0], b["x"][1], b["y"][0] - 0.001, b["y"][1], b["z"][0], b["z"][1], "white")
    return finish(A, "rig_case", coll, parent)


def build_gpu_rough(coll, parent):
    from lib import parts as P
    A = P.Mesh()
    out = P.rrect(GPU_L, GPU_H, GPU_R, 4, GPU_L / 2, GPU_H / 2)
    A.prism(out, -GPU_T, 0.0, "gunmetal")                 # rough: the fan face at z = 0, backplate at -T
    box(A, PCB_TAB[0], PCB_TAB[1], -GPU_FINGERS[2], 0.0005, PCB_Z - 0.0008, PCB_Z + 0.0008, "gold")
    box(A, BRACKET_X[0], BRACKET_X[1], BRACKET_Y[0], BRACKET_Y[1], -GPU_T, 0.0, "bracket")
    return finish(A, "rig_gpu", coll, parent)


def gpu_root_matrix():
    """The card root's place in the case: its origin at the card frame's origin (bracket end, PCIe
    edge, fan face) with the card frame turned as gpu_matrix() says. In the card frame the fan face is
    z = 0 and the backplate z = -GPU_T (the fans look along +z)."""
    R = Matrix(((0, -1, 0), (-1, 0, 0), (0, 0, -1))).transposed()
    M = R.to_4x4()
    # fans look along card +z -> case -Z: the fan face (z = 0) is the card's bottom at GPU_TOP_Z - GPU_T
    M.translation = Vector((GPU_SLOT_X, GPU_BRACKET_Y, GPU_TOP_Z - GPU_T))
    return M


def build(rough=False, lite=False, collection=None):
    """Returns object names by role plus "all". rough=True: the outline masses only."""
    coll = collection or bpy.context.scene.collection
    sfx = "_lite" if lite else ""
    root = bpy.data.objects.get("pc" + sfx) or empty("pc" + sfx, coll)
    names = {}
    if rough:
        c = build_case_rough(coll, root)
        groot = empty("rig_gpu_root", coll, root)
        groot.matrix_world = gpu_root_matrix()
        g = build_gpu_rough(coll, groot)
        names = {"case": [c.name], "gpu": [g.name], "all": [c.name, g.name]}
        return names
    import pc_build
    return pc_build.build(root, coll, lite=lite)


# ---------------------------------------------------------------------------
# 7. the compare views
# ---------------------------------------------------------------------------
def product_light(on, saved=None):
    """The maker's packshots are lit in a dark studio: the world dimmed (and the floor hidden) while the card
    is shown alone; returns what to restore."""
    w = bpy.context.scene.world
    bg = w.node_tree.nodes.get("Background") if w and w.node_tree else None
    if bg is None:
        return None
    lights = [bpy.data.objects[n].data for n in ("lt_front", "lt_fill", "lt_top") if n in bpy.data.objects]
    if on:
        old = (bg.inputs["Strength"].default_value, [L.energy for L in lights])
        bg.inputs["Strength"].default_value = GPU_WORLD
        for L in lights:
            L.energy *= 0.35
        return old
    if saved is not None:
        bg.inputs["Strength"].default_value = saved[0]
        for L, e in zip(lights, saved[1]):
            L.energy = e
    return None


GPU_WORLD = 0.12


def gpu_pose(kind):
    """prepare() for the card's own views: lift the card out to the world origin in a pose, undo after."""
    def prep():
        g = bpy.data.objects["rig_gpu_root"]
        m0 = g.matrix_world.copy()
        par = g.parent
        g.parent = None
        # card frame: x length, y up, z out of the fans
        if kind == "front":            # fans toward the camera at -Y, top edge up, bracket left
            R = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0))).transposed()     # columns: card x, y, z
        elif kind == "back":           # backplate toward the camera at -Y, fingers up, bracket left
            R = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0))).transposed()
        else:                          # lying flat, backplate up (fans down): x along +X, y along +Y
            R = Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1))).transposed()
        M = R.to_4x4()
        M.translation = Vector((0, 0, 1.5))
        g.matrix_world = M
        rig = bpy.data.objects.get("lt_rig")
        r0 = rig.location.copy() if rig else None
        if rig:
            rig.location = (0.15, 0.0, 1.25)          # the studio lights aim at the card, not the case
        dim = product_light(True)
        bpy.context.view_layer.update()

        def undo():
            g.parent = par
            g.matrix_world = m0
            if rig:
                rig.location = r0
            product_light(False, dim)
            bpy.context.view_layer.update()
        return undo
    return prep


def solid_mesh():
    """prepare(): the perforated panels opaque while scoring (the photo's traced silhouette is solid)."""
    def prep():
        undo = []
        for mn in ("mat_pc_perf", "mat_pc_hexmesh"):
            m = bpy.data.materials.get(mn)
            if m is None:
                continue
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            for l in list(b.inputs["Alpha"].links):
                undo.append((m, l.from_socket))
                m.node_tree.links.remove(l)
        def u():
            for m, sock in undo:
                b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                m.node_tree.links.new(sock, b.inputs["Alpha"])
        return u
    return prep


def outline_views(names):
    case = names.get("case_all") or names["case"]
    allc = names.get("pc_all") or (names["case"] + names["gpu"])
    gpu = names.get("gpu_all") or names["gpu"]
    v = []
    cut = cutout_path
    v.append(dict(name="case-front", title="O11 Vision: front (KitGuru edge-io, traced)", photo=cut("edge-io.jpg"),
                  mask="alpha", objects=allc, camera={"mode": "fit", "view": "front", "tilts": [-6.0, -3.0, 0.0, 3.0, 6.0]}))
    v.append(dict(name="case-glass-side", title="O11 Vision: glass side (KitGuru, traced)", photo=cut("glass-side.jpg"),
                  mask="alpha", objects=allc, camera={"mode": "fit", "view": "left", "tilts": [-4.0, -2.0, 0.0, 2.0]}))
    v.append(dict(name="case-solid-side", title="O11 Vision: right side (KitGuru, traced)", photo=cut("solid-side.jpg"),
                  mask="alpha", objects=allc, camera={"mode": "fit", "view": "right", "tilts": [-4.0, -2.0, 0.0, 2.0]}))
    v.append(dict(name="case-3q", title="O11 Vision: three-quarter front (KitGuru, traced)",
                  photo=cut("three-quarter.jpg"), mask="alpha", objects=allc,
                  camera={"mode": "free", "view": "front", "yaws": [42.0, 48.0, 54.0], "tilts": [8.0, 13.0, 18.0],
                          "h_range": (-0.5, 0.05), "distances": [0.7, 0.9, 1.1, 1.3]}))
    v.append(dict(name="case-back-3q", title="O11 Vision: three-quarter back (KitGuru, traced)", photo=cut("back.jpg"),
                  mask="alpha", objects=allc,
                  camera={"mode": "free", "view": "back", "yaws": [35.0, 43.0, 51.0], "tilts": [-6.0, 0.0, 6.0]}))
    v.append(dict(name="case-official-3q", title="O11 Vision white: Lian Li's three-quarter (traced)",
                  photo=cut("official-white-3q.jpg"), mask="alpha", objects=allc,
                  camera={"mode": "free", "view": "front", "yaws": [17.0, 25.0, 33.0], "tilts": [-6.0, 0.0, 6.0]}))
    v.append(dict(name="gpu-front", title="RTX 5090 FE: fan side (NVIDIA render)", photo=cut("front-fans.png"),
                  mask="alpha", objects=gpu, prepare=gpu_pose("front"),
                  camera={"mode": "fit", "view": "front"}))
    v.append(dict(name="gpu-back", title="RTX 5090 FE: backplate side (NVIDIA render)", photo=cut("back.png"),
                  mask="alpha", objects=gpu, prepare=gpu_pose("back"),
                  camera={"mode": "fit", "view": "front", }))
    v.append(dict(name="gpu-3q-io", title="RTX 5090 FE: three-quarter, bracket end (NVIDIA render)",
                  photo=cut("three-quarter-io.png"), mask="alpha", objects=gpu, prepare=gpu_pose("flat"),
                  camera={"mode": "free", "view": "top", "yaws": [15.0, 30.0, 45.0],
                          "tilts": [35.0, 50.0, 65.0], "h_range": (-0.4, 0.4),
                          "distances": [0.9, 1.4, 2.2]}))
    v.append(dict(name="gpu-3q-end", title="RTX 5090 FE: three-quarter, far end (NVIDIA render)",
                  photo=cut("three-quarter-logo.png"), mask="alpha", objects=gpu, prepare=gpu_pose("flat"),
                  camera={"mode": "free", "view": "top", "yaws": [-55.0, -40.0, -25.0],
                          "tilts": [35.0, 50.0, 65.0], "h_range": (-0.4, 0.4),
                          "distances": [0.9, 1.4, 2.2]}))
    for x in v:
        if x["name"].startswith("case-"):
            x["prepare"] = solid_mesh()
    only = os.environ.get("PC_VIEWS")          # a comma list, to iterate on some views
    if only:
        v = [x for x in v if x["name"] in only.split(",")]
    return v


if __name__ == "__main__" and bpy is None:
    if "refs" in sys.argv[1:]:
        make_refs()
    else:
        print(__doc__)
