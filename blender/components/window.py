"""The window and its net curtains (2026-11-02): the owner's white casement in place of the aluminium stand-in.

    B="/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python"
    $B blender/components/window.py            rich (window.blend, window-rich.glb), lite (window-lite.glb), close-ups
    STAGE=rich,lite,closeups (default all three; each runs in a fresh scene)   CLOSE_SPP=48 (Cycles close-ups)

The owner's photo: white uPVC casement, slim white glazing bars, a wide flat white architrave and a white window
board, small black lever handles and hinges. Then, through the coordinator: "the frames of each panel are too
narrower" (outer frame 5 cm, sash stiles and top rail 6.5 cm, bottom rail 8 cm, glazing bars 2.5 cm proud of the
glass, small chamfers), and "Instead of four panels, can we create two panels?" (a French-style pair, hinges on the
outer sides, the levers on the meeting stiles). And: "I want white net curtains."

The opening is plan v3's WINDOW_V3 (1.40 x 1.40, sill 0.95, head 2.35); nothing in plan v3 changes. The window board
keeps the old ledge's top (the sill) and depth (LEDGE_IN, 20 cm), so the monstera (obj_plant) stays where it is.

Frame: the root empty `window` at the opening's bottom centre on the wall's room face (plan v3: x centre, RY, sill),
Z up, metres, the room at -Y, the outside at +Y. place() puts it there.
  window > window_frame (outer frame, the frame's hinge leaves, drain caps), window_board, window_architrave,
           window_track (the ceiling track) (Blender names; the room joins them into window_static),
           window_curtains (both net panels, one mesh, baked with its own unfolded lightmap layout LM_PRE that
           lighting_dusk.lightmap_uvs places), window_sash_1, window_sash_2 (one mesh each, white and black: sash, glazing bars, handle,
           hinge knuckles; origin on the hinge line, local Z the hinge axis: sash 1 hinges at the left, opening into
           the room is a negative turn about Z, sash 2 at the right, a positive turn), window_glass (all panes).
Rich (window.blend, window-rich.glb): bevelled profiles, a double-glazed unit with its spacer, gaskets, three-knuckle
hinges, shaped levers, drain caps, the track's gliders, curtains at full fold resolution with heading and hem layers
and a 1024 px weave. Lite (window-lite.glb, and built live in the room by build_v3.py): the same parts as plain
chamfered prisms, one pane per sash, single-cylinder hinges, a 256 px weave, about 1,500 triangles per curtain.

The net: one material for both panels, a tiling weave (alpha in the texture, glTF alphaMode BLEND, double-sided).
Cycles gets its own output (Material Output target CYCLES): transparent where the weave is open, half diffuse and
half translucent where it is not, so the low sun behind a panel makes it glow in the bake. The glTF export reads the
active output (target ALL; EEVEE alone is not exported): a plain Principled with the same texture, no specular
(with it, the fold edges caught the environment and read as glass strips in the browser).
"""
import json
import math
import os
import random
import subprocess
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, BL)
from lib import constants as C  # noqa: E402
from lib import materials as M  # noqa: E402
from lib import plan_v3 as P  # noqa: E402
from lib.blendfile import pack_and_save  # noqa: E402
from lib.names import set_name  # noqa: E402

OUT = os.path.join(BL, "out", "components")
BLEND = os.path.join(OUT, "window.blend")
RICH_GLB = os.path.join(OUT, "window-rich.glb")
LITE_GLB = os.path.join(OUT, "window-lite.glb")
FOOT = os.path.join(C.FOOTAGE, "2026-11-01-window")
PY = "/opt/anaconda3/bin/python3"
BACKDROP_PNG = os.path.join(BL, "assets", "dusk", "pune-dusk.png")

# --- sizes (metres, the window's local frame)
WV = P.WINDOW_V3
CX = (WV["x0"] + WV["x1"]) / 2                    # 0.43
OW, OH = WV["x1"] - WV["x0"], WV["head"] - WV["sill"]   # 1.40 x 1.40
HW = OW / 2
FRAME = dict(face=0.05, y0=0.08, y1=0.15)          # outer frame: 5 cm face, 7 cm deep, set 8 cm into the reveal
SASH = dict(stile=0.065, top=0.065, bottom=0.08, y0=0.075, y1=0.135, gap=0.002, cols=3, rows=4)
BAR = dict(w=0.025, y0=0.083, y1=0.127, ch=0.003)  # glazing bars: 2.5 cm, proud of the glass both sides
GLASS_Y = 0.105
ARCH = dict(w=0.06, t=0.018)                       # architrave: 6 cm (the pegboard's edge is 6 cm left of the opening)
BOARD = dict(d=P.LEDGE_IN, t=0.025, horn=0.025)    # window board: 20 cm into the room, top at the sill (the plant)
APRON = 0.07
H_LOCAL = P.H - WV["sill"]                          # the ceiling, 2.05 above the sill
FLOOR = -WV["sill"]
TRACK = dict(y=-0.27, w=0.024, h=0.017, x0=-0.37 - CX, x1=1.35 - CX)   # ceiling track, clear of the board
HINGE_Z = (0.18, 1.22)
HANDLE_Z = 0.70
WHITE = "#eeede8"          # warm white, by the ALEX white (#f0f0ec), not blue-white
# curtains, world x (plan v3): outer edge, leading edge at the top, at the floor; folds; seed. The left one reaches
# further across the glass, the right one is drawn back further (lived-in, not symmetrical). The left outer edge
# stays 2 cm clear of the return desk's end (x -0.35); the right one 7 cm clear of the guitar rack.
CURTAINS = {"l": dict(outer=-0.33, lead_top=-0.03, lead_bot=0.035, folds=6, seed=3),
            "r": dict(outer=1.31, lead_top=1.05, lead_bot=1.075, folds=5, seed=11)}
NET = dict(tile=0.08, mean_alpha=0.42, translucent=0.5, rgb=(0.965, 0.96, 0.945))
LITE_TEX = 256
RICH_TEX = 1024

T0 = time.time()
REPORT = {}


def log(m):
    print(f"MILESTONE {time.time() - T0:6.1f}s window: {m}", flush=True)


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------
class Mesh:
    """Collects closed pieces (verts, quads/tris, a material slot each) and makes one object."""

    def __init__(self):
        self.v, self.f, self.m = [], [], []

    def add(self, verts, faces, mi=0):
        o = len(self.v)
        self.v += [tuple(p) for p in verts]
        self.f += [tuple(i + o for i in f) for f in faces]
        self.m += [mi] * len(faces)

    def loft(self, loops, mi=0, close_first=False, close_last=False, closed_loop=True):
        """Quads between consecutive loops (equal length); optional caps."""
        n = len(loops[0])
        o = len(self.v)
        for lp in loops:
            self.v += [tuple(p) for p in lp]
        rng = n if closed_loop else n - 1
        for a in range(len(loops) - 1):
            for i in range(rng):
                j = (i + 1) % n
                self.f.append((o + a * n + i, o + a * n + j, o + (a + 1) * n + j, o + (a + 1) * n + i))
                self.m.append(mi)
        if close_first:
            self.f.append(tuple(o + i for i in range(n))[::-1])
            self.m.append(mi)
        if close_last:
            k = len(loops) - 1
            self.f.append(tuple(o + k * n + i for i in range(n)))
            self.m.append(mi)

    def obj(self, name, mats, coll, parent=None, origin=None, flat=True, recalc=True):
        me = bpy.data.meshes.new(name + "_mesh")
        me.from_pydata(self.v, [], self.f)
        me.update()
        for m in mats:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", self.m)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        if recalc:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = not flat
        o = bpy.data.objects.new(name, me)
        coll.objects.link(o)
        set_name(o, name)
        if origin is not None:
            me.transform(Matrix.Translation(-Vector(origin)))
            o.location = origin
        if parent is not None:
            o.parent = parent
        return o


def rect(x0, x1, z0, z1, y):
    return [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]


def box(ms, x0, x1, y0, y1, z0, z1, mi=0):
    ms.loft([rect(x0, x1, z0, z1, y0), rect(x0, x1, z0, z1, y1)], mi, True, True)


def ring(ms, o, i, y0, y1, ch_in=0.0, ch_out=0.0, mi=0):
    """A closed picture-frame ring between the outer rect o and inner rect i (x0, x1, z0, z1), from y0 (room face)
    to y1, with a chamfer ch_in on the room face's inner edge and ch_out on its outer edge."""
    ox0, ox1, oz0, oz1 = o
    ix0, ix1, iz0, iz1 = i
    loops = [rect(ox0, ox1, oz0, oz1, y1), rect(ox0, ox1, oz0, oz1, y0 + ch_out)]
    if ch_out:
        loops.append(rect(ox0 + ch_out, ox1 - ch_out, oz0 + ch_out, oz1 - ch_out, y0))
    loops.append(rect(ix0 - ch_in, ix1 + ch_in, iz0 - ch_in, iz1 + ch_in, y0))
    if ch_in:
        loops.append(rect(ix0, ix1, iz0, iz1, y0 + ch_in))
    loops.append(rect(ix0, ix1, iz0, iz1, y1))
    loops.append(loops[0])
    ms.loft(loops, mi)


def prism(ms, prof, axis, a0, a1, at=(0.0, 0.0), mi=0):
    """Extrude a closed profile [(s, y)] along X (axis 'x', s is z, at=(_, z0)) or Z (axis 'z', s is x)."""
    if axis == "z":
        mk = lambda s, y, t: (at[0] + s, y, t)
    else:
        mk = lambda s, y, t: (t, y, at[1] + s)
    ms.loft([[mk(s, y, a0) for s, y in prof], [mk(s, y, a1) for s, y in prof]], mi, True, True)


def cyl(ms, r, c0, c1, n=12, mi=0, dome=0):
    """A cylinder from c0 to c1 (vertical or along Y), with flat or domed ends."""
    c0, c1 = Vector(c0), Vector(c1)
    ax = (c1 - c0).normalized()
    u = ax.orthogonal().normalized()
    w = ax.cross(u)
    circ = lambda c, rr: [c + (u * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * rr for k in range(n)]
    loops = []
    if dome:
        for k in range(dome, 0, -1):
            a = math.pi / 2 * k / (dome + 1)
            loops.append(circ(c0 - ax * r * 0.5 * math.sin(a), r * math.cos(a)))
    loops += [circ(c0, r), circ(c1, r)]
    if dome:
        for k in range(1, dome + 1):
            a = math.pi / 2 * k / (dome + 1)
            loops.append(circ(c1 + ax * r * 0.5 * math.sin(a), r * math.cos(a)))
    ms.loft(loops, mi, True, True)


def chamfer_box_prof(w, y0, y1, ch):
    """A bar's cross-section (s across, y), chamfered on both faces."""
    h = w / 2
    return [(-h, y0 + ch), (-h + ch, y0), (h - ch, y0), (h, y0 + ch), (h, y1 - ch), (h - ch, y1), (-h + ch, y1), (-h, y1 - ch)]


def rounded_prof(w, y0, y1, r, n):
    """A rectangle (s across w, y0..y1) with its two room-side corners (y0) rounded by r, n steps."""
    h = w / 2
    pts = [(-h, y1)]
    for k in range(n + 1):
        a = math.pi / 2 * k / n
        pts.append((-h + r - r * math.cos(a), y0 + r - r * math.sin(a)))
    for k in range(n + 1):
        a = math.pi / 2 * k / n
        pts.append((h - r + r * math.sin(a), y0 + r - r * math.cos(a)))
    pts.append((h, y1))
    return pts


def bevel(o, width, segments=2, angle=30):
    md = o.modifiers.new("bevel", "BEVEL")
    md.width, md.segments, md.limit_method, md.angle_limit = width, segments, "ANGLE", math.radians(angle)
    md.harden_normals = False
    return md


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def mats(lite):
    d = {
        "white": M.principled("mat_window_white", base=WHITE, rough=0.35, spec=0.5),
        "black": M.principled("mat_window_black", base="#161618", rough=0.4, spec=0.5),
        "gasket": M.principled("mat_window_gasket", base="#2b2c2f", rough=0.75, spec=0.5),
    }
    d["glass"] = glass_lite() if lite else glass_rich()
    d["net"] = net_material(lite)
    return d


def glass_lite():
    # black base: the pane only darkens what is behind it a little and reflects; a white base picked up the
    # environment's light and laid a pale veil over the city in the browser's intro (2026-11-02)
    g = M.principled("mat_window_glass_lite", base="#000000", rough=0.04, spec=0.5)
    b = next(n for n in g.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Alpha"].default_value = 0.08       # the dusk backdrop must read through it (the intro)
    g.surface_render_method = "BLENDED"
    g.use_backface_culling = True                # seen from the room only: one draw call, not two
    return g


def glass_rich():
    """True glass for Cycles that never blocks the sun or the bounce (as the PC's), a thin blended glass in EEVEE."""
    g = M.principled("mat_window_glass", base="#f2f7f6", rough=0.0, spec=0.5)
    nt = g.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.52
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
    e = nt.nodes.new("ShaderNodeBsdfPrincipled")
    e.inputs["Base Color"].default_value = M.rgba("#f2f7f6")
    e.inputs["Roughness"].default_value = 0.02
    e.inputs["Alpha"].default_value = 0.07
    o2 = nt.nodes.new("ShaderNodeOutputMaterial")
    o2.target = "EEVEE"
    nt.links.new(e.outputs[0], o2.inputs["Surface"])
    g.surface_render_method = "BLENDED"
    g["eevee_thin"] = 1                         # the room test's EEVEE glass switch leaves it alone
    return g


def weave(px):
    """A tiling net: square weave, NET['tile'] metres per tile, threads about 1.2 mm apart, a little slub."""
    rnd = np.random.default_rng(7)
    threads = 64
    pitch = px / threads
    x = (np.arange(px) + 0.5) / pitch                      # thread units
    frac = np.abs(x - np.round(x))                         # 0 on a thread's centre
    width = 0.13 if px >= 1024 else 0.16                   # half-width in thread units
    prof = np.clip((width + 0.5 / pitch - frac) / (1.0 / pitch), 0, 1)   # anti-aliased thread profile
    jit_u = 0.85 + 0.15 * rnd.random(threads)
    jit_v = 0.85 + 0.15 * rnd.random(threads)
    idx = np.round(x).astype(int) % threads
    a_u = prof * jit_u[idx]
    a_v = prof * jit_v[idx]
    cover = 1 - (1 - a_u[None, :]) * (1 - a_v[:, None])
    # slubs: a soft, tiling low-frequency variation
    k = np.arange(px) / px * 2 * np.pi
    slub = 0.06 * (np.sin(3 * k + 1.3)[None, :] * np.cos(2 * k + 0.4)[:, None] + 0.5 * np.sin(5 * k[:, None] + k[None, :]))
    base = 0.06
    alpha = base + (1 - base) * cover
    alpha *= NET["mean_alpha"] / alpha.mean()
    alpha = np.clip(alpha + slub * alpha, 0, 1)
    img = np.ones((px, px, 4), np.float32)
    img[..., :3] = NET["rgb"]
    img[..., 3] = alpha
    return img, float(alpha.mean())


def net_material(lite):
    name = "mat_window_net"
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    px = LITE_TEX if lite else RICH_TEX
    imname = f"window_net_{px}"
    im = bpy.data.images.get(imname)
    if im is None:
        arr, mean = weave(px)
        im = bpy.data.images.new(imname, px, px, alpha=True)
        im.colorspace_settings.name = "sRGB"
        im.pixels.foreach_set(arr[::-1].ravel())       # a byte image: sRGB values as they are; bottom row first
        im.alpha_mode = "STRAIGHT"
        im.pack()
        REPORT.setdefault("net", {})["mean_alpha"] = round(mean, 3)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image, t.location = im, (-700, 100)
    t.interpolation = "Linear"
    # the export (and EEVEE): a plain Principled, alpha from the texture -> glTF BLEND
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.location = (-200, 300)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.0   # no Fresnel edges: they read as glass strips on the web
    if not lite:
        b.inputs["Sheen Weight"].default_value = 0.3
    o_e = nt.nodes.new("ShaderNodeOutputMaterial")
    o_e.target, o_e.location = "ALL", (200, 300)      # target EEVEE alone is skipped by the glTF exporter
    nt.links.new(b.outputs[0], o_e.inputs["Surface"])
    # Cycles (the bake and the stills): transparent | (diffuse + translucent), so a backlit panel glows
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    m1 = nt.nodes.new("ShaderNodeMixShader")
    m2 = nt.nodes.new("ShaderNodeMixShader")
    for n_, xy in ((dif, (-200, -100)), (tl, (-200, -250)), (tp, (-200, -400)), (m1, (0, -150)), (m2, (150, -250))):
        n_.location = xy
    nt.links.new(t.outputs["Color"], dif.inputs["Color"])
    nt.links.new(t.outputs["Color"], tl.inputs["Color"])
    m1.inputs[0].default_value = NET["translucent"]
    nt.links.new(dif.outputs[0], m1.inputs[1])
    nt.links.new(tl.outputs[0], m1.inputs[2])
    nt.links.new(t.outputs["Alpha"], m2.inputs[0])
    nt.links.new(tp.outputs[0], m2.inputs[1])
    nt.links.new(m1.outputs[0], m2.inputs[2])
    o_c = nt.nodes.new("ShaderNodeOutputMaterial")
    o_c.target, o_c.location = "CYCLES", (350, -250)
    nt.links.new(m2.outputs[0], o_c.inputs["Surface"])
    o_e.is_active_output = True                  # the glTF exporter follows the active output
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False               # glTF doubleSided: three.js draws back faces, then front faces
    try:
        m.use_transparency_overlap = True
    except AttributeError:
        pass
    m.diffuse_color = (*NET["rgb"], 0.45)
    return m


# ---------------------------------------------------------------------------
# the parts
# ---------------------------------------------------------------------------
def frame(coll, root, d, lite):
    F, f = FRAME, FRAME["face"]
    ms = Mesh()
    ring(ms, (-HW, HW, 0, OH), (-HW + f, HW - f, f, OH - f), F["y0"], F["y1"], 0.0 if lite else 0.004, 0.0, 0)
    # the hinges' frame leaves (black), beside each sash's outer stile
    for sx in (-1, 1):
        xe = sx * (HW - f)
        for z in HINGE_Z:
            box(ms, min(xe, xe + sx * 0.026), max(xe, xe + sx * 0.026), F["y0"] - 0.002, F["y0"], z - 0.045, z + 0.045, 1)
    if not lite:
        # drain caps on the bottom member, two per sash: white hoods with a dark slot
        for xc in (-0.47, -0.18, 0.18, 0.47):
            box(ms, xc - 0.02, xc + 0.02, F["y0"] - 0.006, F["y0"], 0.012, 0.022, 0)
            box(ms, xc - 0.016, xc + 0.016, F["y0"] - 0.0065, F["y0"] - 0.005, 0.013, 0.0155, 2)
        # the gasket line in the 2 mm shadow gap round the sashes
        ring(ms, (-HW + f, HW - f, f, OH - f), (-HW + f + 0.003, HW - f - 0.003, f + 0.003, OH - f - 0.003),
             F["y0"] + 0.004, F["y0"] + 0.012, 0, 0, 2)
        box(ms, -0.0012, 0.0012, SASH["y0"] + 0.012, SASH["y1"] - 0.01, f + 0.003, OH - f - 0.003, 2)
    o = ms.obj("window_frame", [d["white"], d["black"], d["gasket"]], coll, root)
    if not lite:
        bevel(o, 0.0015)
    return o


def board(coll, root, d, lite):
    B = BOARD
    xe = HW + ARCH["w"] + B["horn"]
    ms = Mesh()
    # the slab in front of the wall, with a rounded front edge (rich) or a small chamfer (lite)
    r = 0.008 if not lite else 0.004
    n = 5 if not lite else 1
    prof = []                                    # (s = z, y): profile across the board, extruded along x
    t = B["t"]
    y0 = -B["d"]
    prof.append((0.0, 0.0))
    for k in range(n + 1):                       # top front corner
        a = math.pi / 2 * k / n
        prof.append((-r + r * math.cos(a), y0 + r - r * math.sin(a)))
    for k in range(n + 1):                       # bottom front corner
        a = math.pi / 2 * k / n
        prof.append((-t + r - r * math.sin(a), y0 + r - r * math.cos(a)))
    prof.append((-t, 0.0))
    prism(ms, prof, "x", -xe, xe, (0.0, 0.0), 0)
    box(ms, -HW, HW, -0.001, FRAME["y0"] + 0.01, -t, 0.0, 0)          # into the reveal, under the frame
    # the apron under it: the trim returning round the board
    box(ms, -HW - ARCH["w"], HW + ARCH["w"], -0.016, 0.0, -t - APRON, -t, 0)
    o = ms.obj("window_board", [d["white"]], coll, root)
    if not lite:
        bevel(o, 0.0015)
    return o


def architrave(coll, root, d, lite):
    A = ARCH
    ms = Mesh()
    ch = 0.0 if lite else 0.0
    for sx in (-1, 1):
        x0, x1 = sorted((sx * HW, sx * (HW + A["w"])))
        box(ms, x0, x1, -A["t"], 0.0, 0.0, OH + A["w"], 0)
    box(ms, -HW, HW, -A["t"], 0.0, OH, OH + A["w"], 0)
    o = ms.obj("window_architrave", [d["white"]], coll, root)
    if not lite:
        bevel(o, 0.003, 3)
    return o


def track(coll, root, d, lite):
    T = TRACK
    ms = Mesh()
    z1 = H_LOCAL - 0.001
    z0 = z1 - T["h"]
    if lite:
        box(ms, T["x0"], T["x1"], T["y"] - T["w"] / 2, T["y"] + T["w"] / 2, z0, z1, 0)
    else:
        # a C profile: rounded underside with the glider slot
        h, w = T["h"], T["w"]
        prof = [(-w / 2, z1), (-w / 2, z0 + 0.004), (-w / 2 + 0.004, z0), (-0.003, z0), (-0.003, z0 + 0.006),
                (0.003, z0 + 0.006), (0.003, z0), (w / 2 - 0.004, z0), (w / 2, z0 + 0.004), (w / 2, z1)]
        loops = [[(T["x0"], T["y"] + s, z) for s, z in prof], [(T["x1"], T["y"] + s, z) for s, z in prof]]
        ms.loft(loops, 0, True, True)
        for x in (T["x0"], T["x1"]):             # end caps
            box(ms, x - 0.004, x + 0.004, T["y"] - w / 2 - 0.001, T["y"] + w / 2 + 0.001, z0 - 0.001, z1, 0)
        # gliders with their hooks, one per fold top, both panels
        for side, c in CURTAINS.items():
            xo, xl = c["outer"] - CX, c["lead_top"] - CX
            for k in range(c["folds"] * 2 + 1):
                x = xo + (xl - xo) * k / (c["folds"] * 2)
                box(ms, x - 0.005, x + 0.005, T["y"] - 0.0025, T["y"] + 0.0025, z0 - 0.012, z0 + 0.004, 0)
    o = ms.obj("window_track", [d["white"]], coll, root)
    if not lite:
        bevel(o, 0.001)
    return o


def _sash_rects(k):
    """Outer and inner (glass) rects of sash k (1 left, 2 right)."""
    S, f, g = SASH, FRAME["face"], SASH["gap"]
    if k == 1:
        x0, x1 = -HW + f + g, -g / 2
        ix0, ix1 = x0 + S["stile"], x1 - S["stile"]
    else:
        x0, x1 = g / 2, HW - f - g
        ix0, ix1 = x0 + S["stile"], x1 - S["stile"]
    z0, z1 = f + g, OH - f - g
    return (x0, x1, z0, z1), (ix0, ix1, z0 + S["bottom"], z1 - S["top"])


def bar_positions(i):
    ix0, ix1, iz0, iz1 = i
    w = BAR["w"]
    pw = (ix1 - ix0 - (SASH["cols"] - 1) * w) / SASH["cols"]
    ph = (iz1 - iz0 - (SASH["rows"] - 1) * w) / SASH["rows"]
    xs = [ix0 + j * pw + (j - 0.5) * w for j in range(1, SASH["cols"])]
    zs = [iz0 + j * ph + (j - 0.5) * w for j in range(1, SASH["rows"])]
    return xs, zs, pw, ph


def handle(ms, xc, lite, mi=1):
    """A black casement lever, closed (pointing down), on the room face of a meeting stile."""
    y0 = SASH["y0"]
    zc = HANDLE_Z
    # lite (2026-11-02): the same shapes at lower resolution; plain boxes read as black bars in the intro
    nc, N, ns, nn = (2, 6, 8, 8) if lite else (4, 16, 12, 16)
    # rose: a rounded slab with a chamfered face
    rr = []
    w, h, r = 0.030, 0.080, 0.010
    for (cx, cz, a0) in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                         (w / 2 - r, -h / 2 + r, 270)):
        for k in range(nc + 1):
            a = math.radians(a0 + 90 * k / nc)
            rr.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    sh = lambda pts, s: [(x * s, z * s) for x, z in pts]
    loops = [[(xc + x, y0, zc + z) for x, z in rr], [(xc + x, y0 - 0.009, zc + z) for x, z in rr],
             [(xc + x, y0 - 0.012, zc + z) for x, z in sh(rr, 0.86)]]
    ms.loft(loops, mi, True, True)
    # the neck, then the lever: a curved, tapering bar with rounded sections, ending in a soft tip
    zn = zc + 0.024
    cyl(ms, 0.0085, (xc, y0 - 0.011, zn), (xc, y0 - 0.036, zn), nn, mi)
    secs = []
    for k in range(N + 1):
        t = k / N
        z = zn + 0.012 - t * 0.135
        y = y0 - 0.043 - 0.010 * math.sin(math.pi * t * 0.9)       # a slight belly away from the sash
        hw = 0.0085 - 0.0018 * t
        hd = 0.0058 - 0.0012 * t
        if k == N:
            hw, hd = hw * 0.8, hd * 0.8
        sec = []
        for j in range(ns):
            a = 2 * math.pi * j / ns
            c, s = math.cos(a), math.sin(a)
            sec.append((xc + hw * math.copysign(abs(c) ** 0.6, c), y + hd * math.copysign(abs(s) ** 0.6, s), z))
        secs.append(sec)
    ms.loft(secs, mi, True, True)


def hinge_knuckles(ms, x, lite, mi=1):
    """Hinge barrel on the room face at the sash's outer edge, plus the sash's leaf."""
    yk = SASH["y0"] - 0.0075
    sx = 1 if x < 0 else -1
    for z in HINGE_Z:
        box(ms, min(x, x + sx * 0.028), max(x, x + sx * 0.028), SASH["y0"] - 0.002, SASH["y0"], z - 0.045, z + 0.045, mi)
        if lite:
            cyl(ms, 0.0065, (x, yk, z - 0.048), (x, yk, z + 0.048), 8, mi)
        else:
            segs = ((-0.048, -0.017), (-0.0155, 0.0155), (0.017, 0.048))
            for k, (a, b) in enumerate(segs):
                cyl(ms, 0.0065, (x, yk, z + a), (x, yk, z + b), 20, mi, dome=2 if k != 1 else 0)
            box(ms, x - 0.0035, x + 0.0035, yk + 0.002, SASH["y0"], z - 0.045, z + 0.045, mi)   # knuckle web


def sash(coll, root, d, k, lite):
    o, i = _sash_rects(k)
    ms = Mesh()
    ring(ms, o, i, SASH["y0"], SASH["y1"], 0.006 if lite else 0.008, 0.0 if lite else 0.0015, 0)
    xs, zs, pw, ph = bar_positions(i)
    prof = chamfer_box_prof(BAR["w"], BAR["y0"], BAR["y1"], BAR["ch"])
    for x in xs:
        prism(ms, prof, "z", i[2], i[3], (x, 0), 0)
    # horizontal bars run between the verticals and end just inside them (crossing bars with coplanar faces
    # rendered black squares in Cycles, 2026-11-02)
    e = BAR["w"] / 2 - BAR["ch"]
    stops = [i[0]] + [v for x in xs for v in (x - e, x + e)] + [i[1]]
    for z in zs:
        for a, b in zip(stops[0::2], stops[1::2]):
            prism(ms, prof, "x", a, b, (0, z), 0)
    if not lite:
        # gasket: a dark line where the glass meets the bead, room side
        g = 0.003
        ring(ms, (i[0] - 0.0005, i[1] + 0.0005, i[2] - 0.0005, i[3] + 0.0005), (i[0] + g, i[1] - g, i[2] + g, i[3] - g),
             0.0885, 0.092, 0, 0, 2)
    # the meeting stile's lever (sash 1: right stile; sash 2: left stile); the hinge barrel on the outer stile
    meet = (o[1] - SASH["stile"] / 2) if k == 1 else (o[0] + SASH["stile"] / 2)
    handle(ms, meet, lite)
    xh = o[0] - SASH["gap"] if k == 1 else o[1] + SASH["gap"]
    hinge_knuckles(ms, xh, lite)
    pivot = (xh, SASH["y0"] - 0.0075, o[2])
    ob = ms.obj(f"window_sash_{k}", [d["white"], d["black"], d["gasket"]] if not lite else [d["white"], d["black"]],
                coll, root, origin=pivot)
    if not lite:
        bevel(ob, 0.0012)
    REPORT.setdefault("panes", dict(w=round(pw, 4), h=round(ph, 4), per_sash=SASH["cols"] * SASH["rows"]))
    return ob


def glass(coll, root, d, lite):
    ms = Mesh()
    for k in (1, 2):
        _, i = _sash_rects(k)
        e = 0.004                                     # into the bead
        x0, x1, z0, z1 = i[0] - e, i[1] + e, i[2] - e, i[3] + e
        if lite:
            ms.add(rect(x0, x1, z0, z1, GLASS_Y), [(0, 1, 2, 3)], 0)
        else:                                         # a double-glazed unit: two 4 mm panes and a grey spacer
            for y in (0.093, 0.113):
                box(ms, x0, x1, y, y + 0.004, z0, z1, 0)
    o = ms.obj("window_glass", [d["glass"]], coll, root, recalc=not lite)   # lite: one quad per sash, facing -Y
    if not lite:
        sp = Mesh()
        for k in (1, 2):
            _, i = _sash_rects(k)
            ring(sp, (i[0] - 0.004, i[1] + 0.004, i[2] - 0.004, i[3] + 0.004), (i[0] + 0.004, i[1] - 0.004, i[2] + 0.004,
                                                                                  i[3] - 0.004), 0.097, 0.113, 0, 0, 0)
        spacer = sp.obj("window_glass_spacer", [d["gasket"]], coll, root)
        REPORT["spacer"] = spacer.name
    # Cycles: the glass never shades the sun, the sky light or the bounce (no caustics)
    o.visible_shadow = False
    o.visible_diffuse = False
    return o


def _smooth_noise(n, seed):
    rnd = random.Random(seed)
    vals = [rnd.random() for _ in range(n + 2)]
    def f(x):
        x = max(0.0, min(n + 0.999, x))
        i = int(x)
        t = x - i
        t = t * t * (3 - 2 * t)
        return vals[i] * (1 - t) + vals[i + 1] * t
    return f


def _panel(bm, uv, lm, side, lite, oy):
    """One net panel, drawn back to its side: vertical folds, pinned pleats at the top, a heavier hem below. Writes
    UVMap (the weave, by arc length) and LM_PRE (the panel unfolded, in metres, from y = oy: the main sheet, then the
    heading and the hem above it), and returns the height it used."""
    c = CURTAINS[side]
    xo = c["outer"] - CX
    x_top, x_bot = c["lead_top"] - CX, c["lead_bot"] - CX
    n = c["folds"]
    rnd = random.Random(c["seed"])
    amp = _smooth_noise(n * 2, c["seed"])
    ph0 = rnd.uniform(0, 2 * math.pi)
    zt, zb = H_LOCAL - TRACK["h"] - 0.012, FLOOR + 0.012
    nu = n * (28 if not lite else 8)
    nz = 150 if not lite else 16
    tile = NET["tile"]
    sgn = 1 if xo < x_top else -1
    gap = 0.05

    def point(u, z, off=0.0):
        t = (zt - z) / (zt - zb)                     # 0 at the top, 1 at the floor
        xl = x_top + (x_bot - x_top) * t ** 1.4 + sgn * 0.012 * math.sin(math.pi * min(1.0, t * 1.2))
        x = xo + (xl - xo) * u
        a = (0.018 + 0.026 * t ** 0.8) * (0.7 + 0.6 * amp(u * n * 2))
        ph = ph0 + 0.55 * t * math.sin(1.7 * t + c["seed"])
        dy = a * (math.sin(2 * math.pi * n * u + ph) + 0.22 * math.sin(2 * math.pi * (2 * n + 1) * u + 2.1 * ph))
        if not lite:                                 # pencil pleats in the heading tape, fading out below it
            w = max(0.0, 1.0 - (zt - z) / 0.09)
            dy = dy * (1 - 0.6 * w) + w * 0.006 * math.sin(2 * math.pi * 4 * n * u)
        x += 0.25 * a * math.cos(2 * math.pi * n * u + ph)       # folds also move a little sideways
        return (x, TRACK["y"] + dy - off, z)

    def sheet(zs, off, oy):
        rows, width = [], 0.0
        for z in zs:
            pts = [point(j / nu, z, off) for j in range(nu + 1)]
            s, acc = [0.0], 0.0
            for a_, b_ in zip(pts, pts[1:]):
                acc += math.hypot(b_[0] - a_[0], b_[1] - a_[1])
                s.append(acc)
            width = max(width, acc)
            rows.append([(bm.verts.new(p), s[j]) for j, p in enumerate(pts)])
        z0 = min(zs)
        for r in range(len(rows) - 1):
            for j in range(nu):
                q = [rows[r][j], rows[r][j + 1], rows[r + 1][j + 1], rows[r + 1][j]]
                f = bm.faces.new([v for v, _ in q])
                zr = (zs[r], zs[r], zs[r + 1], zs[r + 1])
                for loop, (v, s_), z in zip(f.loops, q, zr):
                    loop[uv].uv = (s_ / tile, (z - zb) / tile)
                    loop[lm].uv = (s_, oy + z - z0)
        return width, max(zs) - z0

    k = 6 if not lite else 1
    w, h = sheet([zt - (zt - zb) * i / nz for i in range(nz + 1)], 0.0, oy)
    # heading tape (7 cm) and hem (6 cm): a second layer just in front, so the edges read denser
    w2, h2 = sheet([zt - 0.07 * i / k for i in range(k + 1)], 0.0025, oy + h + gap)
    k = 5 if not lite else 1
    w3, h3 = sheet([zb + 0.06 * (1 - i / k) for i in range(k + 1)], 0.0025, oy + h + gap + h2 + gap)
    return h + h2 + h3 + 3 * gap


def curtains(coll, root, d, lite):
    """Both net panels as one mesh, window_curtains: baked as its own mesh, with a lightmap layout made here (LM_PRE,
    the panels unfolded) because smart project cut every fold into strips one or two texels wide (2026-11-02)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    lm = bm.loops.layers.uv.new("LM_PRE")
    oy = 0.0                                         # the two panels stacked: a narrow strip in the atlas
    for side in ("l", "r"):
        oy += _panel(bm, uv, lm, side, lite, oy)
    me = bpy.data.meshes.new("window_curtains_mesh")
    bm.normal_update()
    ny = sum(f.normal.y * f.calc_area() for f in bm.faces)
    if ny > 0:                                       # front faces to the room (-Y)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.uv_layers["UVMap"].active_render = True
    me.uv_layers.active = me.uv_layers["UVMap"]
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(d["net"])
    o = bpy.data.objects.new("window_curtains", me)
    coll.objects.link(o)
    set_name(o, "window_curtains")
    o.parent = root
    return o


# ---------------------------------------------------------------------------
# build, place
# ---------------------------------------------------------------------------
def _coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def build(lite=False, collection=None):
    coll = collection or _coll("window")
    root = bpy.data.objects.new("window", None)
    coll.objects.link(root)
    set_name(root, "window", data=False)
    root.empty_display_type, root.empty_display_size = "PLAIN_AXES", 0.2
    d = mats(lite)
    parts = [frame(coll, root, d, lite), board(coll, root, d, lite), architrave(coll, root, d, lite),
             track(coll, root, d, lite), sash(coll, root, d, 1, lite), sash(coll, root, d, 2, lite),
             glass(coll, root, d, lite), curtains(coll, root, d, lite)]
    bpy.context.view_layer.update()
    rep = {"tris": {}, "lite": lite}
    dg = bpy.context.evaluated_depsgraph_get()
    for o in coll.all_objects:
        if o.type == "MESH":
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            rep["tris"][o.name] = len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
    rep["tris_total"] = sum(rep["tris"].values())
    rep["images"] = {im.name: list(im.size) for im in bpy.data.images if im.name.startswith("window_")}
    rep.update({k: v for k, v in REPORT.items() if k in ("panes", "net")})
    log(f"built {'lite' if lite else 'rich'}: {rep['tris_total']} tris")
    return root, rep


def place(get, P_=P):
    """The root at the opening's bottom centre on the wall's room face (plan v3's WINDOW_V3)."""
    W = P_.WINDOW_V3
    get("window").matrix_world = Matrix.Translation(((W["x0"] + W["x1"]) / 2, P_.RY, W["sill"]))
    bpy.context.view_layer.update()


def replace_standin():
    """In the room (blockout shell): drop the aluminium window, the grill and the stone ledge; lower the wall under the
    opening to the board's underside (its top met the board's top in one plane: z-fighting in the browser)."""
    for o in list(bpy.data.objects):
        if o.name == "ledge" or o.name.startswith(("win_frame", "grill")):
            bpy.data.objects.remove(o, do_unlink=True)
    wl = bpy.data.objects.get("wb_low")
    if wl is not None:                               # its mesh is in world units (the blockout's box); idempotent
        under = (wl.matrix_world.inverted() @ Vector((0, 0, WV["sill"] - BOARD["t"]))).z
        top = max(v.co.z for v in wl.data.vertices)
        for v in wl.data.vertices:
            if abs(v.co.z - top) < 1e-6:
                v.co.z = min(v.co.z, under)
        wl.data.update()


def clearances(names=("plant_leaf", "plant_pot", "rack", "guitar_0", "desk", "laptop", "mstand", "peg", "neon",
                      "headphones", "pegboard", "returndesk", "ret_")):
    """Smallest distance from each curtain to the meshes around it (world space), for the log."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    curtains = [bpy.data.objects["window_curtains"]]
    others = []
    lo_c = Vector((min(c.matrix_world.translation.x for c in curtains) - 1.5, 0, 0))
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name.startswith("window") or o.name in ("floor", "ceiling") or \
                o.name.startswith(("wb_", "wall_", "sk_", "city", "sky", "ground")):
            continue
        ps = [o.matrix_world @ Vector(cn) for cn in o.bound_box]
        if max(p.y for p in ps) < P.RY - 0.6 or min(p.x for p in ps) > 1.6 or max(p.x for p in ps) < -0.6:
            continue
        others.append(o)
    for c in curtains:
        me = c.evaluated_get(dg).to_mesh()
        pts = [c.matrix_world @ v.co for v in me.vertices][::3]
        c.evaluated_get(dg).to_mesh_clear()
        best = []
        for o in others:
            ps = [o.matrix_world @ Vector(cn) for cn in o.bound_box]
            lo = Vector([min(p[i] for p in ps) for i in range(3)])
            hi = Vector([max(p[i] for p in ps) for i in range(3)])
            near = [p for p in pts if all(lo[i] - 0.2 < p[i] < hi[i] + 0.2 for i in range(3))]
            if not near:
                continue
            em = o.evaluated_get(dg).to_mesh()
            bvh = BVHTree.FromPolygons([o.matrix_world @ v.co for v in em.vertices], [tuple(p.vertices) for p in em.polygons])
            o.evaluated_get(dg).to_mesh_clear()
            dmin = min((bvh.find_nearest(p)[3] for p in near if bvh.find_nearest(p)[0] is not None), default=None)
            if dmin is not None:
                best.append((round(dmin, 3), o.name))
        out[c.name] = sorted(best)[:5]
    log(f"clearances {out}")
    return out


# ---------------------------------------------------------------------------
# export, close-ups
# ---------------------------------------------------------------------------
def export(path, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    kw = dict(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
              export_cameras=False, export_lights=False, export_extras=False)
    if path == LITE_GLB:
        kw.update(export_image_format="WEBP", export_image_quality=80)
    bpy.ops.export_scene.gltf(**kw)
    log(f"exported {path}: {os.path.getsize(path) / 1e6:.3f} MB")
    return os.path.getsize(path)


def _closeup_set():
    """A slice of the room round the window: the back wall with the opening, floor, ceiling, side walls, the painted
    dusk outside, the low sun from the left and behind (as lighting_dusk), a dim world."""
    sc = bpy.context.scene
    W = P.WINDOW_V3
    m_wall = M.principled("still_wall", base="#e3e6ec", rough=0.85)
    m_floor = M.principled("still_floor", base="#4d5563", rough=0.95)
    coll = sc.collection
    ms = Mesh()
    bt = 0.23
    for x0, x1, z0, z1 in ((-1.6, -HW, FLOOR, H_LOCAL), (HW, 1.6, FLOOR, H_LOCAL), (-HW, HW, FLOOR, -BOARD["t"] - 0.002),
                           (-HW, HW, OH, H_LOCAL)):
        box(ms, x0, x1, 0, bt, z0, z1, 0)
    box(ms, -1.6, -1.55, -2.5, 0, FLOOR, H_LOCAL, 0)
    box(ms, 1.55, 1.6, -2.5, 0, FLOOR, H_LOCAL, 0)
    box(ms, -1.6, 1.6, -2.5, 0.3, H_LOCAL, H_LOCAL + 0.05, 0)
    ms.obj("still_walls", [m_wall], coll)
    fl = Mesh()
    box(fl, -1.6, 1.6, -3.0, 0.3, FLOOR - 0.05, FLOOR, 0)
    fl.obj("still_floor", [m_floor], coll)
    # the painted dusk, 14 m out (as lighting_dusk.backdrop, scaled from this camera's view)
    bd = bpy.data.objects.new("still_backdrop", bpy.data.meshes.new("still_backdrop"))
    yb = 14.0
    k = 0.42
    bd.data.from_pydata([(-36 * k, yb, -14 * k), (36 * k, yb, -14 * k), (36 * k, yb, 22 * k), (-36 * k, yb, 22 * k)], [],
                        [(0, 1, 2, 3)])
    bd.data.uv_layers.new(name="UVMap")
    for li, uv in zip(bd.data.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        bd.data.uv_layers[0].data[li.index].uv = uv
    coll.objects.link(bd)
    mb = bpy.data.materials.new("still_backdrop")
    mb.use_nodes = True
    nt = mb.node_tree
    pb = nt.nodes["Principled BSDF"]
    if os.path.exists(BACKDROP_PNG):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(BACKDROP_PNG)
        nt.links.new(t.outputs["Color"], pb.inputs["Base Color"])
        nt.links.new(t.outputs["Color"], pb.inputs["Emission Color"])
    pb.inputs["Emission Strength"].default_value = 1.0
    bd.data.materials.append(mb)
    bd.visible_shadow = False
    from lib import lighting_dusk as LD
    h = Vector((*LD.SUN_DIR, 0)).normalized()
    dv = Vector((h.x, h.y, -math.tan(math.radians(LD.SUN_ELEV)))).normalized()
    s = bpy.data.lights.new("still_sun", "SUN")
    s.energy, s.color, s.angle = LD.SUN["strength"], LD.SUN["color"], math.radians(LD.SUN["angle"])
    so = bpy.data.objects.new("still_sun", s)
    coll.objects.link(so)
    so.rotation_euler = dv.to_track_quat("-Z", "Y").to_euler()
    a = bpy.data.lights.new("still_sky", "AREA")
    a.shape, a.size, a.size_y, a.energy, a.color = "RECTANGLE", OW, OH, 20, (0.66, 0.70, 1.0)
    ao = bpy.data.objects.new("still_sky", a)
    coll.objects.link(ao)
    ao.location = (0, 0.20, OH / 2)
    ao.visible_transmission = ao.visible_glossy = False     # never a white sheet seen through the true glass
    ao.rotation_euler = Vector((0, -1, -0.15)).to_track_quat("-Z", "Y").to_euler()
    room = bpy.data.lights.new("still_room", "AREA")
    room.size, room.energy, room.color = 1.0, 25, (1.0, 0.85, 0.7)
    ro = bpy.data.objects.new("still_room", room)
    coll.objects.link(ro)
    ro.location = (-0.8, -2.2, 1.4)
    ro.rotation_euler = Vector((0.5, 1, -0.2)).to_track_quat("-Z", "Y").to_euler()
    w = bpy.data.worlds.new("still_world")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.04, 0.075, 1)


def closeups(tag):
    sc = bpy.context.scene
    _closeup_set()
    sc.render.engine = "CYCLES"
    try:
        sc.cycles.device = "GPU"
    except Exception:
        pass
    sc.cycles.samples = int(os.environ.get("CLOSE_SPP", "48"))
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = -1.0
    cd = bpy.data.cameras.new("still_cam")
    cam = bpy.data.objects.new("still_cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    os.makedirs(os.path.join(FOOT, "closeup-parts"), exist_ok=True)
    shots = (("whole", (0.25, -2.75, 0.55), (0.05, 0.0, 0.55), 62, (900, 1100)),
             ("handles", (0.12, -0.42, 0.78), (0.0, 0.08, 0.66), 50, (900, 900)),
             ("hinge", (-0.40, -0.36, 0.40), (-0.65, 0.07, 0.20), 45, (900, 900)))
    curtains = [o for o in bpy.data.objects if o.name.startswith("window_curtains")]
    for name, pos, tgt, fov, res in shots:
        for o in curtains:                           # the hinges sit behind the curtains
            o.hide_render = name == "hinge"
        cam.location = pos
        cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
        cd.sensor_fit, cd.angle = "VERTICAL", math.radians(fov)
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = os.path.join(FOOT, "closeup-parts", f"{name}-{tag}.png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        log(f"close-up {name} {tag} {time.time() - t0:.0f} s")


def sheets():
    rep = json.load(open(os.path.join(FOOT, "window-report.json")))
    code = ("import sys,os\nfrom PIL import Image, ImageDraw\nd0=sys.argv[1]\n"
            "for k in ('whole','handles','hinge'):\n"
            " p=[os.path.join(d0,'closeup-parts',k+'-'+t+'.png') for t in ('rich','lite')]\n"
            " if not all(os.path.exists(x) for x in p): continue\n"
            " a,b=[Image.open(x).convert('RGB') for x in p]\n"
            " s=Image.new('RGB',(a.width+b.width+60,a.height+80),(24,24,26));s.paste(a,(20,60));s.paste(b,(a.width+40,60))\n"
            " d=ImageDraw.Draw(s);d.text((20,20),'rich (Blender) '+sys.argv[2],fill=(230,230,230))\n"
            " d.text((a.width+40,20),'lite (web) '+sys.argv[3],fill=(230,230,230))\n"
            " s.save(os.path.join(d0,'closeup-'+k+'.jpg'),quality=90)\n")
    lab = [f"{rep.get(t, {}).get('tris_total', '?')} tris" for t in ("rich", "lite")]
    subprocess.run([PY, "-c", code, FOOT] + lab, check=False)


def _save_report(part, data):
    os.makedirs(FOOT, exist_ok=True)
    p = os.path.join(FOOT, "window-report.json")
    rep = json.load(open(p)) if os.path.exists(p) else {}
    rep[part] = data
    json.dump(rep, open(p, "w"), indent=1, default=str)


def main():
    stages = os.environ.get("STAGE", "rich,lite,closeups").split(",")
    os.makedirs(OUT, exist_ok=True)
    for lite in (False, True):
        tag = "lite" if lite else "rich"
        if tag not in stages:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        REPORT.clear()
        root, rep = build(lite=lite)
        objs = list(bpy.data.collections["window"].all_objects)
        if not lite:
            pack_and_save(BLEND)
            log(f"saved {BLEND}")
        rep["glb_bytes"] = export(LITE_GLB if lite else RICH_GLB, objs)
        _save_report(tag, rep)
        if "closeups" in stages:
            closeups(tag)
    if "closeups" in stages:
        sheets()
    log("done")


if __name__ == "__main__":
    main()
