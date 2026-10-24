"""The parts library: small parametric builders for the hardware every component repeats (rounded
bodies, panels, knobs, buttons, ports, screws, grilles, drivers, poles, clamps, VESA plates, feet,
cables). Generalised from what screens.py built by hand (its ports, pole, clamp, arm plate).

Conventions (all builders):
  - metres; names checked like every other mesh (lib/names.py); mesh data `<name>_mesh`
  - a MOUNTED part (knob, button, port, screw, driver, VESA plate) is built on its mounting surface
    and sticks out of it; `facing` says which way it faces: "-Y" (default: the room's front), "+Y",
    "+X", "-X", "+Z", "-Z". On a face, "up" is world +Z (for +-Z facings: world +Y).
  - a PANEL (rounded_panel, grille) has its front face on the mounting plane and its thickness behind
    it, so parts mounted at the same `at` sit on its face.
  - `at` is the location of the part's origin (the mount point), applied as the object's location;
    the facing rotation is baked into the mesh (scale and rotation stay 1 and 0).
  - quads where it matters; caps are n-gons; smooth shading with sharp edges from 30 degrees;
    `bevel` adds a bevel modifier (angle-limited) for the edges the builder leaves sharp.
  - `mats`: a dict overriding the default palette (palette()) by key; each builder lists its keys.
  - `lite=True`: fewer segments, for the web model.

    from lib import parts
    p = parts.rounded_panel("speaker_baffle", 0.15, 0.25, 0.012, r_corner=0.006, r_front=0.002)
    k = parts.knob("speaker_knob", 0.008, 0.012, knurl=True, indicator=True, at=(0.04, 0, 0.05))
    u = parts.port("speaker_usb", "usb_c", at=(0, 0.2, 0.03), facing="+Y")
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import geo, materials as M, names

MM = 0.001

# ---------------------------------------------------------------------------
# palette and orientation
# ---------------------------------------------------------------------------
_PALETTE = {
    "body": dict(base="#c9ccd1", rough=0.32, metal=1.0),            # bead-blasted aluminium
    "alu": dict(base="#c9ccd1", rough=0.32, metal=1.0),
    "black": dict(base="#151618", rough=0.45),                       # black plastic
    "white": dict(base="#eeeeec", rough=0.4, coat=0.15),
    "rubber": dict(base="#1b1b1c", rough=0.85),
    "chrome": dict(base="#d4d7dc", rough=0.08, metal=1.0),
    "steel": dict(base="#9a9da2", rough=0.3, metal=1.0),
    "port": dict(base="#020203", rough=0.9, spec=0.15),                 # the dark inside of a socket
    "tongue": dict(base="#3d4045", rough=0.5),
    "accent": dict(base="#f2f2ee", rough=0.4),
    "cone": dict(base="#1e1f21", rough=0.7),
    "surround": dict(base="#121213", rough=0.8),
    "cap": dict(base="#2a2b2e", rough=0.4),
    "grille": dict(base="#2b2c2f", rough=0.5, metal=0.6),
    "gold": dict(base="#d9b25a", rough=0.25, metal=1.0),
    "cable": dict(base="#1a1a1b", rough=0.55),
}


def palette(prefix="mat_part_"):
    """The default materials, created once: {key: material}."""
    out = {}
    for k, v in _PALETTE.items():
        out[k] = bpy.data.materials.get(prefix + k) or M.principled(prefix + k, **v)
    return out


def _mats(mats):
    p = palette()
    if mats:
        if isinstance(mats, bpy.types.Material):
            return {k: mats for k in p}
        p.update(mats)
    return p


_FACING = {
    #       local X      local Y      local Z (out of the surface)
    "-Y": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "+Y": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "+X": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    "-X": ((0, -1, 0), (0, 0, 1), (-1, 0, 0)),
    "+Z": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "-Z": ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
}


def orient(facing):
    x, y, z = _FACING[facing]
    return Matrix((x, y, z)).transposed().to_4x4()


# ---------------------------------------------------------------------------
# the mesh accumulator
# ---------------------------------------------------------------------------
class Mesh:
    """Pieces accumulated into one bmesh, a material slot per key. Faces are wound so normals point
    out (see lathe and prism); nothing is recalculated afterwards, so open shells stay right too."""

    def __init__(self):
        self.bm = bmesh.new()
        self.keys = []

    def mi(self, key):
        if key not in self.keys:
            self.keys.append(key)
        return self.keys.index(key)

    def verts(self, pts, m=None):
        return [self.bm.verts.new((m @ Vector(p)) if m is not None else Vector(p)) for p in pts]

    def face(self, vs, key):
        try:
            f = self.bm.faces.new(vs)
        except ValueError:          # duplicate face (shared cap): skip
            return None
        f.material_index = self.mi(key)
        return f

    def strip(self, a, b, key, closed=True):
        n = len(a)
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            self.face([a[i], a[j], b[j], b[i]], key)

    def lathe(self, prof, seg, keys, m=None, phase=0.0):
        """Revolve prof [(r, z) or (r, z, f)] about local +Z (f(theta) scales r: knurls, flutes).
        Walk the profile so the solid is on the left in the (r, z) plane (out along the bottom, up the
        outside, in across the top) and every normal points out. keys: one key or one per span."""
        rings = []
        for p in prof:
            r, z = p[0], p[1]
            f = p[2] if len(p) > 2 else None
            if r < 1e-9:
                rings.append(self.verts([(0, 0, z)], m))
                continue
            pts = []
            for k in range(seg):
                a = phase + 2 * math.pi * k / seg
                rr = r * (f(a) if f else 1.0)
                pts.append((rr * math.cos(a), rr * math.sin(a), z))
            rings.append(self.verts(pts, m))
        for i in range(len(rings) - 1):
            key = keys if isinstance(keys, str) else keys[i]
            a, b = rings[i], rings[i + 1]
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                for k in range(seg):
                    self.face([a[0], b[(k + 1) % seg], b[k]], key)
            elif len(b) == 1:
                for k in range(seg):
                    self.face([a[k], a[(k + 1) % seg], b[0]], key)
            else:
                self.strip(a, b, key)
        return rings

    def prism(self, outline, z0, z1, key, cap_key=None, m=None, bottom=True, top=True):
        """Extrude a CCW outline [(x, y)] from z0 to z1 (z0 < z1)."""
        outline = ccw(outline)
        a = self.verts([(x, y, z0) for x, y in outline], m)
        b = self.verts([(x, y, z1) for x, y in outline], m)
        self.strip(a, b, key)
        if bottom:
            self.face(list(reversed(a)), cap_key or key)
        if top:
            self.face(b, cap_key or key)
        return a, b

    def ring_face(self, outer, inner, z, key, m=None, up=True):
        """A flat ring between two outlines with the same point count."""
        o = self.verts([(x, y, z) for x, y in ccw(outer)], m)
        i = self.verts([(x, y, z) for x, y in ccw(inner)], m)
        n = len(o)
        for k in range(n):
            j = (k + 1) % n
            self.face([o[k], o[j], i[j], i[k]] if up else [i[k], i[j], o[j], o[k]], key)
        return o, i

    def finish(self, name, mats, facing="-Y", at=(0, 0, 0), collection=None, parent=None, smooth=30,
               bevel=None, merge=None):
        bm = self.bm
        if merge:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
        bmesh.ops.transform(bm, matrix=orient(facing), verts=bm.verts)
        me = bpy.data.meshes.new(name + "_mesh")
        bm.to_mesh(me)
        bm.free()
        mp = _mats(mats)
        for k in self.keys:
            me.materials.append(mp.get(k) or mp["body"])
        o = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(o)
        o.parent = parent
        names.set_name(o, name)
        o.location = at
        if smooth:
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(smooth))
        if bevel:
            geo.bevel(o, bevel, segments=2, angle=40)
        return o


def ccw(pts):
    pts = [tuple(p) for p in pts]
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if a > 0 else list(reversed(pts))


def rrect(w, h, r, n=4, cx=0.0, cy=0.0):
    """Rounded rectangle, CCW, n segments per corner (r = 0: the four corners)."""
    if r <= 1e-9 or n == 0:
        return [(cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2), (cx - w / 2, cy - h / 2)]
    r = min(r, w / 2 - 1e-7, h / 2 - 1e-7)
    return geo.rounded_rect(w, h, r, n=n, cx=cx, cy=cy)


def circle(r, n, cx=0.0, cy=0.0, phase=0.0):
    return [(cx + r * math.cos(phase + 2 * math.pi * k / n), cy + r * math.sin(phase + 2 * math.pi * k / n))
            for k in range(n)]


def stadium(w, h, n=6):
    return rrect(w, h, min(w, h) / 2 - 1e-7, n)


def offset(outline, d):
    """Grow (d > 0) or shrink a CCW convex outline by d (mitred)."""
    pts = ccw(outline)
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        e0 = (p1 - p0).normalized()
        e1 = (p2 - p1).normalized()
        n0 = Vector((e0.y, -e0.x))
        n1 = Vector((e1.y, -e1.x))
        b = (n0 + n1)
        if b.length < 1e-9:
            b = n0
        b.normalize()
        c = max(0.2, b.dot(n0))
        q = p1 + b * (d / c)
        out.append((q.x, q.y))
    return out


# ---------------------------------------------------------------------------
# bodies
# ---------------------------------------------------------------------------
def _rbox(A, w, d, h, r_side, r_top, r_bottom, seg, key, z0=0.0, cap_key=None):
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
        loops.append(A.verts([(x, y, z) for x, y in rrect(w - 2 * ins, d - 2 * ins, rc, n)]))
    for a, b in zip(loops, loops[1:]):
        A.strip(a, b, key)
    A.face(list(reversed(loops[0])), cap_key or key)
    A.face(loops[-1], cap_key or key)


def rounded_box(name, w, d, h, r_side=0.0, r_top=0.0, r_bottom=0.0, seg=4, lite=False, mats=None, key="body",
                at=(0, 0, 0), collection=None, parent=None, bevel=None):
    """A w x d x h box standing on its origin (centred in x and y, z from 0 to h) with independent
    radii: r_side on the four vertical edges, r_top on the top edges, r_bottom on the bottom edges.
    r_side, when used, should be at least the edge radii (a smaller one is raised at the caps only).
    Keys: key (default "body")."""
    A = Mesh()
    _rbox(A, w, d, h, r_side, r_top, r_bottom, 1 if lite else seg, key)
    return A.finish(name, mats, "+Z", at, collection, parent, bevel=bevel)


def rounded_panel(name, w, h, t, r_corner=0.0, r_front=0.0, r_back=0.0, seg=4, lite=False, mats=None, key="body",
                  facing="-Y", at=(0, 0, 0), collection=None, parent=None, bevel=None):
    """A w (across) x h (up) slab, front face on the mounting plane, t thick behind it, corners rounded
    r_corner in the face, front and back edges rounded r_front and r_back. Keys: key."""
    A = Mesh()
    _rbox(A, w, h, t, r_corner, r_front, r_back, 1 if lite else seg, key, z0=-t)
    return A.finish(name, mats, facing, at, collection, parent, bevel=bevel)


# ---------------------------------------------------------------------------
# controls
# ---------------------------------------------------------------------------
def knob(name, r, h, knurl=False, indicator=False, skirt=None, flutes=36, depth=None, chamfer=None, seg=48,
         lite=False, mats=None, facing="-Y", at=(0, 0, 0), collection=None, parent=None):
    """A round knob standing out of its surface: plain, knurled (knurl=True: flutes ridges, depth deep),
    with a white indicator line (indicator=True) and an optional skirt (r, h) at its foot.
    Keys: "knob" (body), "accent" (indicator), "skirt"."""
    A = Mesh()
    seg = 24 if lite else (flutes * 2 if knurl else seg)
    c = chamfer if chamfer is not None else min(r, h) * 0.18
    dep = depth if depth is not None else r * 0.06
    f = (lambda a: 1.0 - (dep / r) * (0.5 + 0.5 * math.cos(a * flutes))) if (knurl and not lite) else None

    def side(z):
        return (r, z, f) if f else (r, z)
    if skirt:
        sr, sh = skirt
        prof = [(0, 0), (sr, 0), (sr, sh * 0.6), (sr * 0.94, sh), side(sh)]
        keys = ["skirt"] * 4
    else:
        prof, keys = [(0, 0), side(0.0)], ["knob"]
    prof += [side(h - c), (r - c * 0.6, h - c * 0.15), (r - c, h), (0, h)]
    keys += ["knob"] * 4
    A.lathe(prof, seg, keys)
    if indicator:
        lw = max(0.0006, r * 0.1)
        A.prism(rrect(lw, r * 0.62, lw * 0.45, 2, 0, r * 0.45), h - 0.0001, h + 0.00012, "accent")
    return A.finish(name, mats, facing, at, collection, parent)


def push_button(name, d=None, size=None, height=0.002, gap=0.0004, bezel=0.0012, r_corner=0.001, lite=False,
                mats=None, facing="-Y", at=(0, 0, 0), collection=None, parent=None):
    """A push button: round (d) or rounded square (size=(w, h)), its cap `height` proud, inside a bezel
    ring `bezel` wide with a `gap`. Keys: "cap", "bezel", "port" (the gap)."""
    A = Mesh()
    seg = 16 if lite else 40
    if d:
        rc = d / 2
        A.lathe([(0, 0), (rc, 0), (rc, height * 0.7), (rc - height * 0.25, height), (0, height)], seg, "cap")
        A.ring_face(circle(rc + gap + bezel, seg), circle(rc + gap, seg), 0.0003, "bezel")
        A.prism(circle(rc + gap, seg), 0.0, 0.0002, "port", top=True, bottom=False)
    else:
        w, h = size
        n = 2 if lite else 4
        _rbox(A, w, h, height, r_corner, min(height * 0.3, r_corner), 0.0, 1 if lite else 3, "cap")
        A.ring_face(rrect(w + 2 * (gap + bezel), h + 2 * (gap + bezel), r_corner + gap + bezel, n),
                    rrect(w + 2 * gap, h + 2 * gap, r_corner + gap, n), 0.0003, "bezel")
        A.prism(rrect(w + 2 * gap, h + 2 * gap, r_corner + gap, n), 0.0, 0.0002, "port", bottom=False)
    return A.finish(name, mats, facing, at, collection, parent)


# ---------------------------------------------------------------------------
# ports
# ---------------------------------------------------------------------------
def _hdmi(n):
    w, h, ch = 14.0, 4.55, 1.9
    return [(-w / 2, h / 2), (-w / 2, -h / 2 + ch), (-w / 2 + ch, -h / 2), (w / 2 - ch, -h / 2), (w / 2, -h / 2 + ch),
            (w / 2, h / 2)]


def _dp(n):
    w, h, ch = 16.1, 4.76, 2.2
    return [(-w / 2, h / 2), (-w / 2, -h / 2), (w / 2 - ch, -h / 2), (w / 2, -h / 2 + ch), (w / 2, h / 2)]


def _iec(n):
    w, h, ch = 24.0, 16.0, 4.0
    return [(-w / 2, h / 2), (-w / 2, -h / 2 + ch), (-w / 2 + ch, -h / 2), (w / 2 - ch, -h / 2), (w / 2, -h / 2 + ch),
            (w / 2, h / 2)]


# kind: opening outline (mm, CCW or not), rim width, rim key, tongue boxes (cx, cy, w, h) mm, round holes
PORTS = {
    "usb_a": dict(open=lambda n: rrect(12.0, 4.5, 0.3, 2), rim=0.45, rim_key="chrome",
                  tongue=[(0, 0.95, 11.0, 1.8)], tongue_key="tongue", depth=8.0),
    "usb_c": dict(open=lambda n: stadium(8.34, 2.56, n), rim=0.3, rim_key="chrome", tongue=[(0, 0, 6.7, 0.7)],
                  tongue_key="tongue", depth=6.5),
    "hdmi": dict(open=_hdmi, rim=0.4, rim_key="chrome", tongue=[(0, 0.6, 10.0, 1.2)], tongue_key="tongue", depth=8.5),
    "displayport": dict(open=_dp, rim=0.4, rim_key="chrome", tongue=[(-0.6, 0.5, 11.5, 1.1)], tongue_key="tongue",
                        depth=8.5),
    "jack_35": dict(open=lambda n: circle(1.8, n), rim=1.2, rim_key="black", round_rim=True, depth=12.0),
    "jack_635": dict(open=lambda n: circle(3.3, n), rim=2.6, rim_key="steel", round_rim=True, depth=20.0, nut=True),
    "xlr_combo": dict(open=lambda n: circle(10.0, n), rim=2.0, rim_key="steel", round_rim=True, depth=14.0,
                      insert=True),
    "iec": dict(open=_iec, rim=3.0, rim_key="black", pins=[(-7.0, -1.5, 1.5, 4.0), (7.0, -1.5, 1.5, 4.0),
                                                            (0.0, 3.5, 1.5, 4.0)], depth=12.0),
    "dc_barrel": dict(open=lambda n: circle(3.15, n), rim=1.1, rim_key="black", round_rim=True, depth=9.0,
                      pin=1.0),
}


def port(name, kind, mode="decal", rim_h=0.0003, lite=False, mats=None, facing="-Y", at=(0, 0, 0),
         collection=None, parent=None):
    """A connector socket on a surface, true size: usb_a, usb_c, hdmi, displayport, jack_35, jack_635,
    xlr_combo, iec, dc_barrel (PORTS). mode "decal": everything sits on the surface (a dark well
    inside a raised rim; no hole needed, cheapest). mode "cut": a real well `depth` deep with walls and a
    floor; pair it with port_cutter() and cut() on the panel. Keys: rim_key of the kind, "port" (the
    dark well), "black" (tongues, inserts), "chrome"/"steel"/"gold" (pins)."""
    spec = PORTS[kind]
    n = 12 if lite else 40
    op = [(x * MM, y * MM) for x, y in ccw(spec["open"](n))]
    rim = spec["rim"] * MM
    outer = offset(op, rim)
    A = Mesh()
    rk = spec["rim_key"]
    if mode == "decal":
        A.prism(outer, 0.0, rim_h, rk, bottom=False)
        A.prism(op, 0.0, rim_h + 0.00004, "port", bottom=False)
        floor = rim_h + 0.00005
        top = floor + 0.00004
    else:
        dep = spec["depth"] * MM
        o = A.verts([(x, y, 0.0) for x, y in outer])
        ot = A.verts([(x, y, rim_h) for x, y in outer])
        it = A.verts([(x, y, rim_h) for x, y in op])
        ib = A.verts([(x, y, -dep) for x, y in op])
        A.strip(o, ot, rk)
        A.strip(ot, it, rk)                       # the rim's top face, outer to inner
        A.strip(it, ib, rk if spec.get("round_rim") else "port")     # walls, facing in
        A.face(ib, "port")                                              # floor, facing out of the hole
        floor = -dep
        top = -0.0006
    for cx, cy, w, h in spec.get("tongue", []):
        A.prism(rrect(w * MM, h * MM, 0.15 * MM, 2, cx * MM, cy * MM), floor, top, spec.get("tongue_key", "black"))
    for cx, cy, w, h in spec.get("pins", []):
        A.prism(rrect(w * MM, h * MM, 0.2 * MM, 2, cx * MM, cy * MM), floor, top, "chrome")
    if spec.get("pin"):
        A.lathe([(0, floor), (spec["pin"] * MM, floor), (spec["pin"] * MM, top), (0, top)], 16, "gold")
    if spec.get("insert"):                       # the combo's black insert: the 6.35 hole, three XLR holes, latch
        r_in = 10.0 * MM
        A.lathe([(0, floor), (r_in * 0.98, floor), (r_in * 0.98, top - 0.00002), (0, top - 0.00002)], n, "black")
        A.prism(circle(3.3 * MM, n), top - 0.00002, top + 0.00002, "port", bottom=False)
        for a in (90, 210, 330):
            ax = math.radians(a)
            A.prism(circle(0.9 * MM, 12, 6.2 * MM * math.cos(ax), 6.2 * MM * math.sin(ax)), top - 0.00002,
                    top + 0.00002, "port", bottom=False)
        A.prism(rrect(4.0 * MM, 2.2 * MM, 0.3 * MM, 2, 0, 12.6 * MM), 0.0, rim_h + 0.0007, "steel")
    if spec.get("nut"):
        hexo = circle(6.4 * MM, 6, phase=math.pi / 6)
        A.prism(hexo, rim_h, rim_h + 1.6 * MM, "steel", bottom=False)
        A.prism(circle(3.3 * MM, n), rim_h + 1.6 * MM, rim_h + 1.6 * MM + 0.00004, "port", bottom=False)
    return A.finish(name, mats, facing, at, collection, parent)


def port_cutter(name, kind, depth=None, facing="-Y", at=(0, 0, 0), collection=None):
    """The opening of a port as a solid, for cut(panel, cutter) (mode "cut")."""
    spec = PORTS[kind]
    op = [(x * MM, y * MM) for x, y in spec["open"](40)]
    A = Mesh()
    A.prism(op, -(depth or spec["depth"] * MM) - 0.002, 0.002, "port")
    o = A.finish(name, None, facing, at, collection, smooth=0)
    o.hide_render = True
    o.display_type = "WIRE"
    return o


def cut(target, cutter, apply=False):
    """Boolean-difference a cutter out of a panel (exact solver). Keeps it as a modifier unless apply."""
    m = target.modifiers.new("cut_" + cutter.name, "BOOLEAN")
    m.operation, m.solver, m.object = "DIFFERENCE", "EXACT", cutter
    cutter.hide_render = True
    cutter.hide_viewport = True
    if apply:
        with bpy.context.temp_override(object=target, active_object=target):
            bpy.ops.object.modifier_apply(modifier=m.name)
    return m


# ---------------------------------------------------------------------------
# screws
# ---------------------------------------------------------------------------
def screw(name, kind="phillips", d=0.004, h=None, lite=False, mats=None, facing="-Y", at=(0, 0, 0),
          collection=None, parent=None):
    """A screw head on a surface: "phillips" (pan head, cross), "hex" (button head, hex socket),
    "hexbolt" (hexagon head), "flat" (countersunk, flush, slot). d = head diameter. Keys: "screw",
    "port" (the recess)."""
    A = Mesh()
    r = d / 2
    seg = 12 if lite else 32
    hh = h or (r * 0.7 if kind != "flat" else 0.00015)
    if kind == "phillips":
        A.lathe([(0, 0), (r, 0), (r, hh * 0.35), (r * 0.8, hh * 0.9), (r * 0.45, hh), (0, hh)], seg, "screw")
        for ang in (0, 90):
            A.prism(rrect(d * 0.62, d * 0.13, d * 0.02, 1), hh - 0.00005, hh + 0.00003, "port", bottom=False,
                    m=Matrix.Rotation(math.radians(ang), 4, "Z"))
    elif kind == "hex":
        A.lathe([(0, 0), (r, 0), (r, hh * 0.25), (r * 0.85, hh * 0.8), (r * 0.5, hh), (0, hh)], seg, "screw")
        A.prism(circle(d * 0.2, 6, phase=math.pi / 6), hh - 0.00005, hh + 0.00003, "port", bottom=False)
    elif kind == "hexbolt":
        A.lathe([(0, 0), (r * 1.08, 0), (r * 1.08, hh * 0.1), (0, hh * 0.1)], seg, "screw")
        A.prism(circle(r, 6, phase=math.pi / 6), hh * 0.1, hh, "screw")
    else:                                         # flat (countersunk)
        A.lathe([(0, 0), (r, 0), (r, hh), (0, hh)], seg, "screw")
        A.prism(rrect(d * 0.85, d * 0.14, d * 0.02, 1), hh - 0.00002, hh + 0.00003, "port", bottom=False)
    return A.finish(name, mats, facing, at, collection, parent, smooth=40)


# ---------------------------------------------------------------------------
# grille
# ---------------------------------------------------------------------------
def _cell_boundary(x0, y0, w, h, kx, ky):
    """CCW boundary of a cell, kx segments along the bottom and top, ky up the sides; bottom-left first."""
    pts = [(x0 + w * i / kx, y0) for i in range(kx)]
    pts += [(x0 + w, y0 + h * j / ky) for j in range(ky)]
    pts += [(x0 + w - w * i / kx, y0 + h) for i in range(kx)]
    pts += [(x0, y0 + h - h * j / ky) for j in range(ky)]
    return pts


def grille(name, w, h, t=0.0012, hole_d=0.002, pitch=0.003, pattern="hex", mode="holes", margin=None,
           r_corner=0.0, holes="alpha", hole_segments=8, lite=False, mats=None, facing="-Y", at=(0, 0, 0),
           collection=None, parent=None):
    """A perforated panel, w x h, t thick behind its face.

    mode "holes"   real holes through the panel (close-ups): tiled cells, each a ring of quads round an
                   8- or 16-segment hole, wall quads and a back; shared edges everywhere (hex rows are
                   offset half a pitch and closed with half cells). Rectangular outline.
    mode "texture" a plain rounded panel with a small generated tile image (holes as alpha, or dark with
                   holes="dark") repeated by its UVs: a few dozen triangles, exports to glTF as is.
    Keys: "grille"."""
    margin = pitch * 0.6 if margin is None else margin
    if mode == "texture":
        return _grille_texture(name, w, h, t, hole_d, pitch, pattern, r_corner, holes, mats, facing, at,
                               collection, parent, lite)
    k = 2 if (hole_segments <= 8 or lite) else 4
    rowh = pitch * math.sqrt(3) / 2 if pattern == "hex" else pitch
    nx = max(1, int((w - 2 * margin) // pitch))
    ny = max(1, int((h - 2 * margin) // rowh))
    fw, fh = nx * pitch, ny * rowh
    x0, y0 = -fw / 2, -fh / 2
    rr = hole_d / 2
    polys, rings = [], []                 # front polygons (2D) and hole circles (2D)
    for j in range(ny):
        yb = y0 + j * rowh
        odd = pattern == "hex" and j % 2 == 1
        cells = []
        if odd:
            cells.append((x0, pitch / 2, False))
            cells += [(x0 + pitch / 2 + i * pitch, pitch, True) for i in range(nx - 1)]
            cells.append((x0 + fw - pitch / 2, pitch / 2, False))
        else:
            cells += [(x0 + i * pitch, pitch, True) for i in range(nx)]
        for xa, cw, hole in cells:
            b = _cell_boundary(xa, yb, cw, rowh, k if hole else k // 2, k)
            if not hole:
                polys.append(b)
                continue
            cx, cy = xa + cw / 2, yb + rowh / 2
            ph = math.atan2(b[0][1] - cy, b[0][0] - cx)
            c = [(cx + rr * math.cos(ph + 2 * math.pi * i / len(b)), cy + rr * math.sin(ph + 2 * math.pi * i / len(b)))
                 for i in range(len(b))]
            for i in range(len(b)):
                q = (i + 1) % len(b)
                polys.append([b[i], b[q], c[q], c[i]])
            rings.append(c)
    # the frame between the field and the outline
    sx, sy = pitch / k, rowh / k
    bottom = [(x0 + i * sx, y0) for i in range(nx * k + 1)]
    top = [(x0 + i * sx, y0 + fh) for i in range(nx * k + 1)]
    left = [(x0, y0 + j * sy) for j in range(ny * k + 1)]
    right = [(x0 + fw, y0 + j * sy) for j in range(ny * k + 1)]
    W2, H2 = w / 2, h / 2
    polys.append([(-W2, -H2), (W2, -H2)] + list(reversed(bottom)))
    polys.append([(W2, -H2), (W2, H2)] + list(reversed(right)))
    polys.append([(W2, H2), (-W2, H2)] + top)
    polys.append([(-W2, H2), (-W2, -H2)] + left)
    A = Mesh()
    key = "grille"
    for p in polys:
        p = ccw(p)
        A.face(A.verts([(x, y, 0.0) for x, y in p]), key)
        A.face(A.verts([(x, y, -t) for x, y in reversed(p)]), key)
    for c in rings:
        a = A.verts([(x, y, -t) for x, y in c])
        b = A.verts([(x, y, 0.0) for x, y in c])
        A.strip(b, a, key)                     # the hole's wall, facing in
    out = [(-W2, -H2), (W2, -H2), (W2, H2), (-W2, H2)]
    A.prism(out, -t, 0.0, key, bottom=False, top=False)
    o = A.finish(name, mats, facing, at, collection, parent, smooth=0, merge=1e-7)
    o["holes"] = len(rings)
    return o


def grille_tile(pitch, hole_d, pattern="hex", px=64, colour=(0.17, 0.17, 0.18), hole_colour=(0.0, 0.0, 0.0),
                holes="alpha"):
    """The repeating tile as an RGBA float array (row 0 at the bottom, Blender's order) and its size in m."""
    import numpy as np
    tw = pitch
    th = pitch * math.sqrt(3) if pattern == "hex" else pitch
    W = px
    H = max(1, int(round(px * th / tw)))
    ss = 4
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    x = (xx + 0.5) / (W * ss) * tw
    y = (yy + 0.5) / (H * ss) * th
    centres = [(tw / 2, th / 2)] if pattern != "hex" else [(0, 0), (tw, 0), (0, th), (tw, th), (tw / 2, th / 2)]
    inside = np.zeros(x.shape, bool)
    for cx, cy in centres:
        inside |= (x - cx) ** 2 + (y - cy) ** 2 < (hole_d / 2) ** 2
    cov = inside.reshape(H, ss, W, ss).mean((1, 3))
    img = np.zeros((H, W, 4), np.float32)
    for i in range(3):
        img[..., i] = colour[i] * (1 - cov) + (hole_colour[i] * cov if holes == "dark" else colour[i] * cov)
    img[..., 3] = 1 - cov if holes == "alpha" else 1.0
    return img, (tw, th)


def _grille_texture(name, w, h, t, hole_d, pitch, pattern, r_corner, holes, mats, facing, at, collection, parent,
                    lite):
    mp = _mats(mats)
    base = mp["grille"]
    col = tuple(base.diffuse_color[:3])
    img, (tw, th) = grille_tile(pitch, hole_d, pattern, colour=col, holes=holes)
    H, W = img.shape[:2]
    im = bpy.data.images.new(f"img_{name}", W, H, alpha=True)
    im.pixels.foreach_set(img.ravel())
    im.pack()
    m = bpy.data.materials.new(f"mat_{name}")
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = im
    tex.interpolation = "Closest" if lite else "Linear"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    if holes == "alpha":
        nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
        try:
            m.surface_render_method = "DITHERED"
        except AttributeError:
            pass
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Metallic"].default_value = 0.5
    nt.links.new(b.outputs[0], out.inputs[0])
    o = rounded_panel(name, w, h, t, r_corner=r_corner, mats={"grille": m}, key="grille", facing="+Z", seg=2)
    me = o.data
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co.x / tw + 0.5, co.y / th + 0.5)
    me.transform(orient(facing))
    o.location = at
    o.parent = parent
    if collection is not None:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        collection.objects.link(o)
    o["tile_m"] = [tw, th]
    return o


# ---------------------------------------------------------------------------
# speaker driver
# ---------------------------------------------------------------------------
def driver(name, d, ring=None, surround=None, cone_depth=None, cap_d=None, recess=True, lite=False, mats=None,
           facing="-Y", at=(0, 0, 0), collection=None, parent=None):
    """A speaker driver as seen from the front: basket ring (flange on the baffle), rubber surround roll,
    cone, dust cap. d = the flange's outer diameter. recess=True: the cone sits below the baffle face
    in a can (cut a hole of driver_cutter() in the baffle); False: everything stands proud (no cut).
    Keys: "ring", "surround", "cone", "cap"."""
    R = d / 2
    ring = ring or R * 0.13
    sw = surround or R * 0.12
    r_in = R - ring
    r_s = r_in - sw
    cd = cone_depth or R * 0.38
    rc = (cap_d or d * 0.28) / 2
    tr = max(0.0012, R * 0.03)
    roll = sw * 0.45
    lift = 0.0 if recess else cd + 0.0004
    seg = 24 if lite else 72
    arc = 3 if lite else 8
    # the can (only seen through the baffle's hole), then the flange: from the can's lip out over the baffle, round, and back in on top
    prof = [(0, -cd * 1.25 + lift), (r_in * 0.999, -cd * 1.25 + lift), (r_in * 0.999, lift), (R, lift), (R, tr * 0.6 + lift),
            (R - tr * 0.4, tr + lift), (r_in, tr + lift), (r_in, tr * 0.5 + lift)]
    keys = ["ring", "ring", "ring", "ring", "ring", "ring", "ring"]
    for i in range(1, arc + 1):                    # the surround: a half roll from r_in to r_s
        a = math.pi * i / arc
        prof.append((r_in - sw * (1 - math.cos(a)) / 2, tr * 0.5 + lift + roll * math.sin(a)))
        keys.append("surround")
    nc = 3 if lite else 8
    z_rim = tr * 0.5 + lift
    for i in range(1, nc + 1):                     # the cone: slightly curved, down to the cap
        u = i / nc
        prof.append((r_s + (rc - r_s) * u, z_rim - cd * (u ** 0.85)))
        keys.append("cone")
    capb = z_rim - cd
    ch = rc * 0.45
    for i in range(1, arc + 1):                    # the dust cap: a dome
        a = math.pi / 2 * i / arc
        prof.append((rc * math.cos(a), capb + ch * math.sin(a)))
        keys.append("cap")
    A = Mesh()
    A.lathe(prof, seg, keys)          # out along the can's floor, up, out over the baffle, in across the top
    return A.finish(name, mats, facing, at, collection, parent, smooth=50)


def driver_cutter(name, d, ring=None, depth=None, facing="-Y", at=(0, 0, 0), collection=None):
    R = d / 2
    r_in = R - (ring or R * 0.13)
    A = Mesh()
    A.lathe([(0, -(depth or R) - 0.002), (r_in * 0.999, -(depth or R) - 0.002), (r_in * 0.999, 0.002), (0, 0.002)],
            48, "port")
    o = A.finish(name, None, facing, at, collection, smooth=0)
    o.hide_render = True
    o.display_type = "WIRE"
    return o


# ---------------------------------------------------------------------------
# tubes, poles, clamps
# ---------------------------------------------------------------------------
def tube(name, r, length, wall=None, seg=32, lite=False, mats=None, key="steel", facing="+Z", at=(0, 0, 0),
         collection=None, parent=None):
    """A rod (wall None) or a tube (wall thickness) from its origin along `facing`, length long. Keys: key."""
    A = Mesh()
    seg = max(8, seg // 2) if lite else seg
    if wall:
        ri = r - wall
        A.lathe([(ri, 0), (r, 0), (r, length), (ri, length), (ri, 0)], seg, key)
    else:
        A.lathe([(0, 0), (r, 0), (r, length), (0, length)], seg, key)
    return A.finish(name, mats, facing, at, collection, parent)


def pole(name, r=0.0175, h=0.8, cap=True, lite=False, mats=None, key="white", at=(0, 0, 0), collection=None,
         parent=None):
    """A vertical pole standing on its origin, with a slightly proud end cap (screens' desk pole)."""
    A = Mesh()
    seg = 20 if lite else 48
    prof = [(0, 0), (r, 0), (r, h - 0.010)]
    if cap:
        prof += [(r + 0.0008, h - 0.010), (r + 0.0008, h - 0.003), (r - 0.002, h)]
    else:
        prof += [(r, h)]
    prof += [(0, h)]
    A.lathe(prof, seg, key)
    return A.finish(name, mats, "+Z", at, collection, parent, bevel=None if lite else 0.0008)


def desk_clamp(name, pole_r=0.0175, desk_t=0.030, edge=0.045, plate_w=0.090, knob_r=0.021, lite=False, mats=None,
               at=(0, 0, 0), collection=None, parent=None):
    """A desk C-clamp for a pole (screens' clamp, generalised). Origin: the pole axis on the desk top;
    the desk's back edge is `edge` behind it (+Y), the desk desk_t thick. Top plate and collar, a spine
    down the back edge, a jaw under the desk, the screw, its pad and a knob.
    Keys: "white" (body), "rubber", "chrome"."""
    A = Mesh()
    seg = 20 if lite else 48
    n = 4 if lite else 8
    y0, y1 = -0.055, edge + 0.010
    A.prism(rrect(plate_w, y1 - y0, 0.014, n, 0, (y0 + y1) / 2), 0.0015, 0.010, "white")
    A.prism(rrect(plate_w - 0.006, y1 - y0 - 0.006, 0.012, n, 0, (y0 + y1) / 2), 0.0, 0.0015, "rubber")
    A.lathe([(0, 0.010), (pole_r + 0.0145, 0.010), (pole_r + 0.0145, 0.020), (pole_r + 0.0125, 0.024),
             (pole_r, 0.026), (0, 0.026)], seg, "white")
    zb = -desk_t
    A.prism(rrect(0.060, 0.012, 0.002, 2, 0, edge + 0.016), zb - 0.032, 0.010, "white")
    A.prism(rrect(0.052, edge + 0.041, 0.003, 2, 0, (edge + 0.016 - 0.025) / 2), zb - 0.031, zb - 0.020, "white")
    A.lathe([(0, zb - 0.060), (0.006, zb - 0.060), (0.006, zb - 0.003), (0, zb - 0.003)], 12 if lite else 24, "chrome")
    A.lathe([(0, zb - 0.0045), (knob_r, zb - 0.0045), (knob_r, zb - 0.0015), (0, zb - 0.0015)], seg, "white")
    A.lathe([(0, zb - 0.0015), (knob_r, zb - 0.0015), (knob_r, zb), (0, zb)], seg, "rubber")
    A.lathe([(0, zb - 0.078), (knob_r * 0.9, zb - 0.078), (knob_r, zb - 0.074), (knob_r, zb - 0.064),
             (0.012, zb - 0.060), (0, zb - 0.060)], seg, "white")
    return A.finish(name, mats, "+Z", at, collection, parent, bevel=None if lite else 0.0010)


def vesa_plate(name, pattern=100, size=None, t=0.004, r_corner=0.008, screws=True, other=True, lite=False,
               mats=None, key="white", facing="+Y", at=(0, 0, 0), collection=None, parent=None):
    """A VESA plate (75 or 100), size square (default pattern + 15 mm), t thick, front on the mounting
    plane; four pan-head screws on the pattern and the other pattern's holes as dark discs (other=True).
    Facing "+Y": on a screen's back. Keys: key, "chrome", "port"."""
    A = Mesh()
    p = pattern * MM
    s = size or p + 0.015
    _rbox(A, s, s, t, r_corner, 0.0006, 0.0, 1 if lite else 3, key, cap_key=key)
    seg = 12 if lite else 24
    if screws:
        for sx in (-1, 1):
            for sy in (-1, 1):
                m = Matrix.Translation((sx * p / 2, sy * p / 2, t))
                A.lathe([(0, 0), (0.0045, 0), (0.0045, 0.0012), (0.0035, 0.0022), (0, 0.0024)], seg, "chrome", m=m)
                for ang in (0, 90):
                    A.prism(rrect(0.0055, 0.0011, 0.0002, 1), 0.0023, 0.00243, "port", bottom=False,
                            m=m @ Matrix.Rotation(math.radians(ang), 4, "Z"))
    if other:
        q = (75 if pattern == 100 else 100) * MM
        if q / 2 + 0.003 < s / 2:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    A.prism(circle(0.0025, seg, sx * q / 2, sy * q / 2), t, t + 0.00005, "port", bottom=False)
    return A.finish(name, mats, facing, at, collection, parent)


def rubber_feet(name, positions, d=0.012, h=0.003, square=False, z=0.0, lite=False, mats=None, collection=None,
                parent=None):
    """Rubber feet under a body: one mesh, a foot at each (x, y) (world, in the parent's frame) hanging
    down from the plane z. Round (d across) or square. Keys: "rubber"."""
    A = Mesh()
    seg = 12 if lite else 32
    r = d / 2
    for x, y in positions:
        m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.pi, 4, "X")
        if square:
            o = rrect(d, d, d * 0.2, 2 if lite else 4)
            a = A.verts([(px, py, 0.0) for px, py in o], m)
            b = A.verts([(px * 0.88, py * 0.88, h) for px, py in o], m)
            A.strip(a, b, "rubber")
            A.face(list(reversed(a)), "rubber")
            A.face(b, "rubber")
        else:
            A.lathe([(0, 0), (r, 0), (r, h * 0.55), (r * 0.8, h), (0, h)], seg, "rubber", m=m)
    return A.finish(name, mats, "+Z", (0, 0, 0), collection, parent)


# ---------------------------------------------------------------------------
# cable
# ---------------------------------------------------------------------------
def sag_points(p0, p1, sag, n=6):
    """Points along a hanging cable from p0 to p1 that sags `sag` metres at its middle (a parabola)."""
    p0, p1 = Vector(p0), Vector(p1)
    return [tuple(p0.lerp(p1, i / (n - 1)) - Vector((0, 0, 4 * sag * (i / (n - 1)) * (1 - i / (n - 1)))))
            for i in range(n)]


def cable(name, points, r=0.0025, seg=8, mats=None, key="cable", to_mesh=False, lite=False, collection=None,
          parent=None):
    """A round cable along a smooth Bezier path through `points` (auto handles). to_mesh=True converts
    it to a mesh (for export and joins). Keys: key."""
    cu = bpy.data.curves.new(name + "_curve", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 1 if lite else max(1, seg // 4)
    cu.resolution_u = 4 if lite else 12
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.materials.append(_mats(mats)[key])
    o = bpy.data.objects.new(name, cu)
    (collection or bpy.context.scene.collection).objects.link(o)
    o.parent = parent
    names.set_name(o, name, data=False)
    if to_mesh:
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        bpy.data.objects.remove(o)
        bpy.data.curves.remove(cu)
        o = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(o)
        o.parent = parent
        names.set_name(o, name)
        me.shade_smooth()
    return o


ALL = ["rounded_box", "rounded_panel", "knob", "push_button", "port", "screw", "grille", "driver", "tube", "pole",
       "desk_clamp", "vesa_plate", "rubber_feet", "cable"]
