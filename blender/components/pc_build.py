"""pc: the detailed build (case, card, the white build inside). Numbers and their sources are in pc.py;
the few extra placements here are EST from the build photos (build-1/2/3.jpg, official-white-build.webp,
rear-chamber.jpg) and say so.

The meshes are the names proposed for obj_rig (MESHES.md conventions):
    rig_case            frame, panels, feet, front I/O, PSU bracket (white steel, perforated, grey rubber)
    rig_case_glass      the three glass panels (front, side, top), one transparent material
    rig_gpu             the card (shroud, fins, bracket, board edge), origin at the card's centre
    rig_gpu_fan_01, 02  the card's fan rotors, origin at the hub, local +Z the axis (code may spin them)
    rig_gpu_light       the light bar on the card's top edge (emissive)
    rig_fans            every case fan's light ring and edge strips, one mesh, one emissive material
    rig_fan_01 .. 08    the case fans' rotors (blades and hub), origin at the hub, local +Z the axis
    rig_static          the inside: board, cooler, memory, radiator, PSU, cables, fan frames
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import pc as K
from lib import parts as P, names as NM

MM = 0.001


def mm(*v):
    return tuple(x * MM for x in v)


# ---------------------------------------------------------------------------
# frames and small helpers
# ---------------------------------------------------------------------------
def frame(u, v, origin=(0, 0, 0)):
    """A 4x4 with local x = u, y = v, z = u x v, at origin (world, metres)."""
    u, v = Vector(u).normalized(), Vector(v).normalized()
    w = u.cross(v)
    M = Matrix((u, v, w)).transposed().to_4x4()
    M.translation = Vector(origin)
    return M


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def slab(A, u0, u1, v0, v1, w0, w1, key, M=None, edge=None):
    """A box in a local frame: faces key, the four sides `edge` (default key)."""
    A.prism(rect(u0, u1, v0, v1), w0, w1, edge or key, cap_key=key, m=M)


def fillet(poly, r, n=4):
    """Round every corner of a polygon by r (n segments), keeping it simple for convex-ish outlines."""
    out = []
    m = len(poly)
    for i in range(m):
        p0, p1, p2 = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % m])
        a, b = (p0 - p1), (p2 - p1)
        la, lb = a.length, b.length
        a.normalize()
        b.normalize()
        ang = math.acos(max(-1.0, min(1.0, a.dot(b))))
        if ang < 1e-3 or r <= 0:
            out.append(tuple(p1))
            continue
        d = min(r / math.tan(ang / 2), la * 0.45, lb * 0.45)
        rr = d * math.tan(ang / 2)
        s0, s1 = p1 + a * d, p1 + b * d
        bis = (a + b).normalized()
        c = p1 + bis * (rr / math.sin(ang / 2))
        v0, v1 = s0 - c, s1 - c
        a0 = math.atan2(v0.y, v0.x)
        a1 = math.atan2(v1.y, v1.x)
        da = a1 - a0
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for k in range(n + 1):
            t = a0 + da * k / n
            out.append((c.x + rr * math.cos(t), c.y + rr * math.sin(t)))
    return out


def plate(A, outer, holes, w0, w1, key, wall_key=None, M=None, back=True):
    """A flat plate in a local (u, v) frame from w0 to w1 with polygonal holes: front (w1) and back (w0)
    faces filled with scanfill (holes respected), walls round the outline and the holes."""
    bm = A.bm
    ki, kw = A.mi(key), A.mi(wall_key or key)
    Mx = M or Matrix.Identity(4)

    def loop(poly, w):
        return [bm.verts.new(Mx @ Vector((x, y, w))) for x, y in poly]
    outer = P.ccw(outer)
    holes = [list(reversed(P.ccw(h))) for h in holes]      # holes clockwise
    nrm = (Mx.to_3x3() @ Vector((0, 0, 1))).normalized()
    for w, up in ((w1, True), (w0, False)):
        if not up and not back:
            continue
        loops = [loop(outer, w)] + [loop(h, w) for h in holes]
        edges = []
        for lp in loops:
            for i in range(len(lp)):
                edges.append(bm.edges.new((lp[i], lp[(i + 1) % len(lp)])))
        res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
        for f in res["geom"]:
            if isinstance(f, bmesh.types.BMFace):
                f.material_index = ki
                f.normal_update()
                if (f.normal.dot(nrm) < 0) == up:
                    f.normal_flip()
        if up:
            top = loops
        else:
            bot = loops
    # walls (outer outward, holes inward): build fresh verts so faces stay simple
    for poly, inward in [(outer, False)] + [(h, True) for h in holes]:
        a = [bm.verts.new(Mx @ Vector((x, y, w0))) for x, y in poly]
        b = [bm.verts.new(Mx @ Vector((x, y, w1))) for x, y in poly]
        n = len(poly)
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new([a[i], a[j], b[j], b[i]])
            f.material_index = kw


def grid_panel(A, u0, u1, v0, v1, holes, w0, w1, key, M, edge_key=None):
    """A rectangular panel with rectangular holes (u0, u1, v0, v1) as grid cells: clean quads only."""
    us = sorted({u0, u1} | {h[0] for h in holes} | {h[1] for h in holes})
    vs = sorted({v0, v1} | {h[2] for h in holes} | {h[3] for h in holes})

    def inside(u, v):
        if not (u0 <= u <= u1 and v0 <= v <= v1):
            return False
        return not any(h[0] < u < h[1] and h[2] < v < h[3] for h in holes)
    ek = edge_key or key
    for i in range(len(us) - 1):
        for j in range(len(vs) - 1):
            cu, cv = (us[i] + us[i + 1]) / 2, (vs[j] + vs[j + 1]) / 2
            if not inside(cu, cv):
                continue
            ua, ub, va, vb = us[i], us[i + 1], vs[j], vs[j + 1]
            # front and back
            f = A.verts([(ua, va, w1), (ub, va, w1), (ub, vb, w1), (ua, vb, w1)], M)
            A.face(f, key)
            b = A.verts([(ua, va, w0), (ua, vb, w0), (ub, vb, w0), (ub, va, w0)], M)
            A.face(b, key)
            # walls where the neighbour is empty
            du, dv = (ub - ua) * 0.5 + 1e-6, (vb - va) * 0.5 + 1e-6
            for (nu, nv, e) in ((cu - du - 1e-6, cv, ((ua, vb), (ua, va))), (cu + du + 1e-6, cv, ((ub, va), (ub, vb))),
                                (cu, cv - dv - 1e-6, ((ua, va), (ub, va))), (cu, cv + dv + 1e-6, ((ub, vb), (ua, vb)))):
                if inside(nu, nv):
                    continue
                (pa, pb) = e
                q = A.verts([(pa[0], pa[1], w0), (pb[0], pb[1], w0), (pb[0], pb[1], w1), (pa[0], pa[1], w1)], M)
                A.face(q, ek)


EXTRA = {}


def new_obj(A, name, coll, parent, smooth=30, origin=None):
    mt = dict(K.mats())
    mt.update({k: bpy.data.materials[v] for k, v in EXTRA.items() if v in bpy.data.materials})
    mt["body"] = mt["white"]
    o = A.finish(name, mt, facing="+Z", at=(0, 0, 0), collection=coll, parent=None, smooth=smooth)
    if origin is not None:
        o.data.transform(Matrix.Translation(-Vector(origin)))
        o.location = Vector(origin)
    if parent is not None:
        mw = o.matrix_world.copy()
        o.parent = parent
        o.matrix_world = mw
    return o


def tile_uvs(o, tiles):
    """Planar UVs for the faces whose material is in `tiles` {material name: (tile_w, tile_h)}: projected
    on the face's dominant plane, in tiles."""
    me = o.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        mname = me.materials[poly.material_index].name if me.materials else ""
        n = poly.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        tw, th = tiles.get(mname, (0.05, 0.05))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co[a] / tw, co[b] / th)


def tile_material(name, pitch, hole_d, pattern, colour, lite=False):
    m = bpy.data.materials.get(name)
    img, size = P.grille_tile(pitch, hole_d, pattern, colour=colour, holes="alpha", px=48 if lite else 64)
    if m is not None:
        return m, size
    H, W = img.shape[:2]
    im = bpy.data.images.new("img_" + name, W, H, alpha=True)
    im.pixels.foreach_set(img.ravel())
    im.pack()
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = im
    tex.interpolation = "Linear"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Specular IOR Level"].default_value = 0.35
    try:
        m.surface_render_method = "DITHERED"
    except AttributeError:
        pass
    nt.links.new(b.outputs[0], out.inputs[0])
    m.diffuse_color = (*colour, 1.0)
    return m, size


# ---------------------------------------------------------------------------
# the case
# ---------------------------------------------------------------------------
HW, HD = K.CASE_W / 2, K.CASE_D / 2
ZB = K.FOOT_H                       # the body's bottom
ZT = K.CASE_H                       # the top glass's top
ZG = ZT - K.GLASS_TOP               # the top glass's underside (the walls' tops)
XP = HW - K.PILLAR_W                # the pillar's inner edge, x
T_PANEL = 2.0 * MM                  # EST: steel panel thickness (4.0 mm is the official structure steel)

# local frames: u across, v up, w out of the face (outward)
F_FRONT = frame((1, 0, 0), (0, 0, 1))                 # w = -Y
F_BACK = frame((-1, 0, 0), (0, 0, 1))                 # w = +Y
F_RIGHT = frame((0, 1, 0), (0, 0, 1))                 # w = +X
F_LEFT = frame((0, -1, 0), (0, 0, 1))                 # w = -X
F_TOP = frame((1, 0, 0), (0, 1, 0))                   # w = +Z


def at_plane(F, w):
    """Frame F moved so its w = 0 plane is at distance w along its normal from the origin."""
    M = F.copy()
    M.translation = F.to_3x3() @ Vector((0, 0, w))
    return M


def build_case(coll, parent, lite):
    A = P.Mesh()
    mt = K.mats()
    perf, perf_size = tile_material("mat_pc_perf", 2.6 * MM, 1.6 * MM, "hex", (0.86, 0.87, 0.88), lite)
    hexm, hex_size = tile_material("mat_pc_hexmesh", 10.0 * MM, 8.2 * MM, "hex", (0.86, 0.87, 0.88), lite)
    K.mats()  # ensure
    EXTRA.update({"perf": perf.name, "hex": hexm.name})
    # feet and skirts (as the outline)
    K.case_feet(A, "white")
    for s in (-1, 1):
        x0, x1 = (HW - K.RAIL_T, HW) if s > 0 else (-HW, -HW + K.RAIL_T)
        slab(A, x0, x1, -HD + K.FOOT_Y_TOP, HD - K.FOOT_Y_TOP, ZB - K.RAIL_H, ZB, "white")
    # base frame inside the glass (the white band seen through the front glass)
    slab(A, -HW + 4 * MM, HW - T_PANEL, -HD + 4 * MM, HD - T_PANEL, ZB, ZB + K.BASE_T, "white")
    # bottom of the body: a perforated tray under the main chamber, white elsewhere
    slab(A, -HW, HW, -HD, HD, ZB - 0.6 * MM, ZB, "white")
    # the pillar: the front of the rear chamber, full height, flush with the front glass
    slab(A, XP, HW, -HD, -HD + T_PANEL * 2, ZB, ZT, "white")
    # the rear chamber's top strip (flush with the top glass)
    slab(A, XP, HW, -HD, HD, ZG, ZT, "white")
    # the right side panel with its two perforated windows
    Mr = at_plane(F_RIGHT, HW)
    wins = [(K.MESH_FRONT[0], K.MESH_FRONT[1], K.MESH_Z[0], K.MESH_Z[1]),
            (K.MESH_REAR[0], K.MESH_REAR[1], K.MESH_Z[0], K.MESH_Z[1])]
    S = P.Mesh()            # the right panel is its own mesh while building (the rear-chamber close-up lifts it)
    grid_panel(S, -HD + T_PANEL * 2, HD, ZB, ZG, wins, -T_PANEL, 0.0, "white", Mr)
    for (u0, u1, v0, v1) in wins:
        slab(S, u0, u1, v0, v1, -T_PANEL * 0.75, -T_PANEL * 0.5, "perf", Mr)
    # its pressed border line near the front edge (solid-side.jpg)
    slab(S, -HD + 12 * MM, -HD + 13 * MM, ZB + 10 * MM, ZG - 10 * MM, 0.0, 0.25 * MM, "white", Mr)
    # power button on the front-right edge (MEASURED edge-io.jpg / solid-side.jpg)
    slab(S, -HD + 4 * MM, -HD + 12 * MM, K.POWER_BTN_Z - 7 * MM, K.POWER_BTN_Z + 7 * MM, 0.0, 1.2 * MM, "white", Mr,
         edge="grey")
    # the rear panel: openings (u = -X, v = Z): the PSU (behind the bracket), the board's I/O, the rear fans'
    # hex mesh, the expansion slots, the vents along the top and bottom (MEASURED back.jpg, EST in mm)
    Mb = at_plane(F_BACK, HD)
    io = (-48 * MM, -4 * MM, 197 * MM, 357 * MM)                  # u = -x
    fanw = (18 * MM, 142 * MM, 214 * MM, 456 * MM)
    psu = (-148 * MM, -52 * MM, 80 * MM, 231 * MM)
    slots = (-48 * MM, 76 * MM, 66 * MM, 214 * MM)
    vent_b = (-40 * MM, 142 * MM, 36 * MM, 60 * MM)
    vent_t = (-48 * MM, 10 * MM, 372 * MM, 452 * MM)
    vent_rc = (-146 * MM, -56 * MM, 248 * MM, 452 * MM)          # over the rear chamber, above the PSU
    rear_holes = [io, fanw, psu, slots, vent_b, vent_t, vent_rc]
    grid_panel(A, -HW, HW, ZB, ZG, rear_holes, -T_PANEL * 2, 0.0, "white", Mb)
    for h in (fanw, vent_b, vent_t, vent_rc):
        slab(A, h[0], h[1], h[2], h[3], -T_PANEL * 1.6, -T_PANEL * 1.3, "hex", Mb)
    # expansion slot covers: 7 horizontal strips (20.32 mm pitch, OFFICIAL PCIe), vented, two used by the card
    for i in range(7):
        z1 = slots[3] - i * 20.32 * MM
        z0 = z1 - 18.0 * MM
        if i < 2:
            continue                                             # the card's own bracket is there
        slab(A, slots[0] + 2 * MM, slots[1] - 2 * MM, z0, z1, -T_PANEL * 2.6, -T_PANEL * 0.5, "white", Mb)
        slab(A, slots[0] + 12 * MM, slots[1] - 14 * MM, z0 + 5 * MM, z1 - 5 * MM, -T_PANEL * 0.5, -T_PANEL * 0.45,
             "perf", Mb)
        # the thumb screw on the slot's end (u = slots[1] side, beside the opening)
        A.lathe([(0, 0), (3.2 * MM, 0), (3.2 * MM, 4 * MM), (2.6 * MM, 5 * MM), (0, 5 * MM)], 8 if lite else 16,
                "brass", m=Mb @ Matrix.Translation(Vector((slots[1] + 6 * MM, (z0 + z1) / 2, 0.0))))
    # the frame's thumb screws down the rear's glass side edge (back.jpg)
    for z in (60, 160, 260, 360, 440):
        A.lathe([(0, 0), (3.6 * MM, 0), (3.6 * MM, 5 * MM), (3.0 * MM, 6.5 * MM), (0, 6.5 * MM)], 8 if lite else 16,
                "brass", m=Mb @ Matrix.Translation(Vector((HW - 6 * MM, z * MM, 0.0))))
    # PSU bracket: a white frame standing 14 mm out of the back round the PSU's end
    b = K.PSU_BRACKET
    by0, by1 = b["y"]
    for (x0, x1, z0, z1) in ((b["x"][0], b["x"][1], b["z"][0], b["z"][0] + 2 * MM),
                             (b["x"][0], b["x"][1], b["z"][1] - 2 * MM, b["z"][1]),
                             (b["x"][0], b["x"][0] + 2 * MM, b["z"][0], b["z"][1]),
                             (b["x"][1] - 2 * MM, b["x"][1], b["z"][0], b["z"][1])):
        slab(A, x0, x1, by0 - 1 * MM, by1, z0, z1, "white", F_TOP)
    # hex side on the bracket (rear-chamber.jpg)
    slab(A, b["x"][1] - 2.2 * MM, b["x"][1] - 2.0 * MM, by0 - 30 * MM, by1, b["z"][0], b["z"][1], "hex")
    # the motherboard tray and the side fan bracket (the divider), the top frame strips
    Mt = at_plane(F_RIGHT, K.TRAY_X)           # u = y, v = z, w = +x
    cpu_cut = (K.CPU["y"] - 55 * MM, K.CPU["y"] + 55 * MM, K.CPU["z"] - 55 * MM, K.CPU["z"] + 55 * MM)
    grid_panel(A, -40 * MM, HD - 4 * MM, ZB + K.BASE_T, ZG - 4 * MM, [cpu_cut], 0.0, T_PANEL, "white", Mt)
    # the side fan bracket in front of the tray (fans mount on it): a frame round three 120 mm holes
    fy0, fy1 = K.SIDE_FANS["y"] - 63 * MM, K.SIDE_FANS["y"] + 63 * MM
    holes = [(K.SIDE_FANS["y"] - 57 * MM, K.SIDE_FANS["y"] + 57 * MM, z - 57 * MM, z + 57 * MM)
             for z in K.SIDE_FANS["z"]]
    grid_panel(A, fy0, fy1, ZB + K.BASE_T, ZG - 4 * MM, holes, T_PANEL * 0.5, T_PANEL * 1.5, "white", Mt)
    # grey rubber grommet strips at the tray's front edge and the two over the board (all photos)
    for (y0, y1, z0, z1) in ((-50, -30, 230, 445), (-50, -30, 60, 210)):
        A.prism(P.rrect((y1 - y0) * MM, (z1 - z0) * MM, 6 * MM, 2 if lite else 4, (y0 + y1) / 2 * MM, (z0 + z1) / 2 * MM),
                -8 * MM, 0.0, "grey", m=Mt)
    for (y0, y1) in ((-5, 95), (105, 205)):
        slab(A, (K.TRAY_X - 28 * MM), K.TRAY_X, y0 * MM, y1 * MM, ZG - 36 * MM, ZG - 4 * MM, "grey", None)
        for k in range(4):                                    # the slits in the grommets
            yy = (y0 + 18 + k * 20) * MM
            slab(A, K.TRAY_X - 28.4 * MM, K.TRAY_X - 27.9 * MM, yy - 0.8 * MM, yy + 0.8 * MM, ZG - 30 * MM,
                 ZG - 10 * MM, "port", None)
    # the top frame: a white rim under the top glass at the back and over the tray
    slab(A, -HW + 4 * MM, XP, HD - 22 * MM, HD - T_PANEL * 2, ZG - 10 * MM, ZG, "white")
    slab(A, K.TRAY_X - 30 * MM, XP, -HD + 4 * MM, HD - 4 * MM, ZG - 4 * MM, ZG, "white")
    # the glass's bottom channel along the front and the side (white, under the glass)
    slab(A, -HW + 4 * MM, XP, -HD, -HD + 16 * MM, ZB, ZB + K.BASE_T + 2 * MM, "white")
    # the I/O panel's pressed frame round the ports (detail-io.jpg)
    Mf = at_plane(F_FRONT, HD)
    fx0, fx1, fz0, fz1 = 52 * MM, 137 * MM, 6 * MM, 25 * MM
    for (a0, a1, b0, b1) in ((fx0, fx1, fz1, fz1 + 0.7 * MM), (fx0, fx1, fz0 - 0.7 * MM, fz0),
                             (fx1, fx1 + 0.7 * MM, fz0 - 0.7 * MM, fz1 + 0.7 * MM)):
        slab(A, a0, a1, b0, b1, -0.1 * MM, 0.05 * MM, "grey", Mf)
    # the power button where the pillar meets the right side: its front face (edge-io.jpg)
    slab(A, HW - 16 * MM, HW - 4 * MM, K.POWER_BTN_Z - 4 * MM, K.POWER_BTN_Z + 4 * MM, 0.0, 1.0 * MM, "white", Mf,
         edge="grey")
    # front I/O on the right foot (MEASURED edge-io.jpg); ports as decals
    o = new_obj(A, "rig_case", coll, parent)
    ports = []
    if not lite:
        y = -HD
        for kind, x in zip(("jack_35", "usb_c", "usb_a", "usb_a"), K.IO_X):
            ports.append(P.port(f"pc_io_{len(ports)}", kind, facing="-Y", at=(x * MM, y, K.IO_Z),
                                collection=coll))
    tile_uvs(o, {perf.name: perf_size, hexm.name: hex_size})
    if ports:
        o = join_into(o, ports)
    side = new_obj(S, "rig_case_side", coll, parent)
    tile_uvs(side, {perf.name: perf_size, hexm.name: hex_size})
    return o, side


def join_into(target, objs):
    bpy.context.view_layer.update()          # new objects' matrix_world is stale until then
    objs = [target] + list(objs)
    name = target.name
    for ob in objs[1:]:
        mw = ob.matrix_world.copy()
        ob.parent = None
        ob.matrix_world = mw
    with bpy.context.temp_override(active_object=target, object=target, selected_objects=objs,
                                   selected_editable_objects=objs):
        bpy.ops.object.join()
    NM.set_name(target, name)
    return target


def build_glass(coll, parent, lite):
    A = P.Mesh()
    g, e = "glass", "glass_edge"
    # front: x -HW..XP, outer face at y = -HD
    slab(A, -HW, XP, ZB, ZG, 0.0, K.GLASS_FS, g, at_plane(F_FRONT, HD - K.GLASS_FS), edge=e)
    # side (left): outer face at x = -HW, from behind the front glass to the back
    slab(A, -HD, HD - K.GLASS_FS, ZB, ZG, 0.0, K.GLASS_FS, g, at_plane(F_LEFT, HW - K.GLASS_FS), edge=e)
    # top over the main chamber
    slab(A, -HW, XP, -HD, HD, ZG, ZT, g, None, edge=e)
    return new_obj(A, "rig_case_glass", coll, parent, smooth=0)


# ---------------------------------------------------------------------------
# the card (card frame: x length from the bracket end, y up from the PCIe edge, z out of the fan face;
# the fan face at z = 0, the backplate at z = -GPU_T)
# ---------------------------------------------------------------------------
L, H, T = K.GPU_L, K.GPU_H, K.GPU_T
XC, YC = L / 2, H / 2
RIM = 4.5 * MM               # MEASURED front-fans.png: the lighter rim round the face
BACK_RIM = 3.0 * MM          # MEASURED back.png
TIP = 147.0 * MM             # MEASURED close-ups of front-fans.png / back.png: the wells' tips 10 mm apart
WELL_D = 11.0 * MM           # EST: how deep the fan wells are (three-quarter photos)
# along the top edge (EST from three-quarter-io.png and three-quarter-logo.png, perspective averaged):
SLITS = (110 * MM, 190 * MM)     # the two vent slits
SOCKET = (193 * MM, 208 * MM)    # the 12V-2x6 power socket (16 pins), recessed
LIGHT = (218 * MM, 276 * MM)     # where the maker's lettering is lit: here a plain light bar
BACK_D = 5.0 * MM            # EST: the backplate's fin windows


def well_poly(side, lite, rim=None):
    """The left (-1) or right (+1) fan well: bounded by the rim and the X's arms (MEASURED front-fans.png:
    the arms meet the inner rim at x 88.9 / 215.1 mm and the wells' inner tips at x 141 / 163 mm)."""
    xt = 88.9 * MM if side < 0 else L - 88.9 * MM
    tip = TIP if side < 0 else L - TIP
    r = RIM if rim is None else rim
    xo = r if side < 0 else L - r
    pts = [(xo, r), (xt, r), (tip, YC), (xt, H - r), (xo, H - r)]
    if side > 0:
        pts = [(xo, r), (xo, H - r), (xt, H - r), (tip, YC), (xt, r)]
    return fillet(P.ccw(pts), 13.0 * MM, 2 if lite else 6)


def outline_card(lite):
    return P.rrect(L, H, K.GPU_R, 3 if lite else 8, XC, YC)


def build_gpu(coll, parent, lite):
    A = P.Mesh()
    out = outline_card(lite)
    wl, wr = well_poly(-1, lite), well_poly(1, lite)
    # the shroud's sides (rim colour), between the face plates
    zf0, zf1 = -WELL_D, 0.0                     # front plate
    zb0, zb1 = -T, -T + BACK_D                  # back plate
    # side walls with a 2.5 mm chamfer at both faces
    ch = 2.5 * MM            # the fan face's edge
    rb = 6.0 * MM            # the backplate's edge: a full round (three-quarter photos: the "pill" ends)
    inner = P.offset(out, -ch)
    rings = []
    nb = 2 if lite else 5
    for i in range(nb + 1):                      # quarter round from the backplate face to the side wall
        t = (math.pi / 2) * i / nb
        rings.append((-T + rb * (1 - math.cos(t)), rb * (1 - math.sin(t))))
    rings += [(-ch, 0.0), (0.0, ch)]
    loops = [A.verts([(x, y, z) for x, y in P.ccw(P.offset(out, -ins) if ins > 1e-6 else out)]) for z, ins in rings]
    for k, (a_, b_) in enumerate(zip(loops, loops[1:])):
        # the rounds and the front chamfer catch the light (rim); the straight side wall is the shroud's own
        # dark satin, as the three-quarter photos show it
        A.strip(a_, b_, "gunmetal" if k == nb else "rim")
    inner_b = P.offset(out, -rb)
    # front plate (z = 0) with the two wells; the X and the triangles in gunmetal, the wells' lips in rim
    plate(A, inner, [wl, wr], zf0, zf1, "gunmetal", "rim", back=False)
    # the wells' lips: a lighter bevelled rim round each well (the X reads from these, front-fans.png)
    for poly in (wl, wr):
        A.ring_face(P.offset(poly, 1.1 * MM), poly, 0.05 * MM, "rim")
    # the X's arms: lighter bevels along the wells' diagonal edges, meeting in a small diamond (front-fans.png)
    xarm(A, wl, wr, 0.06 * MM, None)
    # back plate (z = -T) with the fin windows (same shapes, as back.png)
    Mb = Matrix(((1, 0, 0, 0), (0, -1, 0, H), (0, 0, -1, -T + BACK_D), (0, 0, 0, 1)))   # a half turn about x
    bl, br = well_poly(-1, lite, BACK_RIM), well_poly(1, lite, BACK_RIM)   # the back's rim is thinner (back.png)
    plate(A, inner_b, [bl, br], 0.0, BACK_D, "gunmetal", "rim", M=Mb, back=False)
    for poly in (bl, br):
        A.ring_face(P.offset(poly, 1.1 * MM), poly, 0.05 * MM, "rim", m=Matrix.Translation((0, H, -T)) @ Matrix.Rotation(math.pi, 4, "X"))
    xarm(A, bl, br, 0.06 * MM, Matrix.Translation((0, H, -T)) @ Matrix.Rotation(math.pi, 4, "X"))
    # the core between the plates: a dark block under the wells (fin stacks) and the board between
    if lite:
        for poly in (wl, wr):
            A.prism(poly, -T + BACK_D, -WELL_D, "fins", top=True, bottom=True)
    else:          # flow-through: fins only, with a dark plane through the middle (heat pipes, vapour chamber)
        for poly in (wl, wr):
            A.prism(poly, -T / 2 - 1.0 * MM, -T / 2 + 1.0 * MM, "black")
    # the solid middle (under the X's triangles) closes the body
    mid = [(88.9 * MM, RIM), (L - 88.9 * MM, RIM), (L - 88.9 * MM, H - RIM), (88.9 * MM, H - RIM)]
    A.prism(mid, -T + BACK_D, -WELL_D, "gunmetal")
    # the fin stacks: thin plates across the wells, 2 mm pitch (rich only), seen through the fans and the back
    if not lite:
        for poly in (wl, wr):
            xs = [p[0] for p in poly]
            for k in range(int((max(xs) - min(xs)) / (2.0 * MM))):
                x = min(xs) + (k + 0.5) * 2.0 * MM
                ys = _span(poly, x)
                if ys is None:
                    continue
                y0, y1 = ys
                slab(A, x - 0.2 * MM, x + 0.2 * MM, y0 + 0.4 * MM, y1 - 0.4 * MM, -T + BACK_D, -WELL_D - 1.5 * MM,
                     "fins")
    # top edge (y = H): the slits, the 12V-2x6 socket (EST from three-quarter-logo.png)
    Mtop = frame((1, 0, 0), (0, 0, -1), (0, H, -T / 2))
    for vv in (-6.0, 4.0):
        slab(A, SLITS[0], SLITS[1], vv * MM, vv * MM + 2.2 * MM, -0.1 * MM, 0.12 * MM, "port", Mtop)
    # the top edge's darker middle between the two rounded ends (three-quarter photos)
    slab(A, 96 * MM, 212 * MM, -T / 2 + 3 * MM, T / 2 - 3 * MM, -0.1 * MM, 0.05 * MM, "gunmetal", Mtop)
    slab(A, SOCKET[0], SOCKET[1], -5 * MM, 5 * MM, -0.1 * MM, 0.15 * MM, "port", Mtop)
    if not lite:
        for i in range(6):
            for j in range(2):
                slab(A, SOCKET[0] + (1.5 + i * 2.2) * MM, SOCKET[0] + (3.0 + i * 2.2) * MM, (-3.5 + j * 4.5) * MM, (-1.0 + j * 4.5) * MM,
                     0.1 * MM, 0.2 * MM, "black", Mtop)
    # the bracket (black) with its ports, and the PCIe board edge with gold fingers
    bx0, bx1 = K.BRACKET_X
    by0, by1 = K.BRACKET_Y
    slab(A, bx0, bx0 + 1.2 * MM, by0, by1, -T, 0.0, "bracket")
    slab(A, bx0 - 11 * MM, bx0, by1 - 1.2 * MM, by1, -T + 1 * MM, -1 * MM, "bracket")         # top tab
    slab(A, bx0 + 1.2 * MM, bx1, 2 * MM, H - 30.5 * MM, -T + 1 * MM, -1 * MM, "black")        # port frame
    for zz in (-T / 2 - 5 * MM, -T / 2 + 2 * MM):                                              # the tongue's prongs
        slab(A, bx0, bx0 + 1.2 * MM, by0 - 8 * MM, by0, zz, zz + 3 * MM, "bracket")
    slab(A, K.PCB_TAB[0], K.PCB_TAB[1], -K.GPU_FINGERS[2], 1 * MM, K.PCB_Z - 0.8 * MM, K.PCB_Z + 0.8 * MM, "black")
    if lite:
        slab(A, K.GPU_FINGERS[0], K.GPU_FINGERS[1], -K.GPU_FINGERS[2] + 0.5 * MM, -2 * MM, K.PCB_Z - 0.85 * MM,
             K.PCB_Z + 0.85 * MM, "gold")
    else:            # the contact pads at 1 mm pitch with the x16 key gap 11.65 mm from the start (PCIe CEM)
        x = K.GPU_FINGERS[0] + 0.5 * MM
        while x < K.GPU_FINGERS[1] - 0.5 * MM:
            if not (K.GPU_FINGERS[0] + 11.0 * MM < x < K.GPU_FINGERS[0] + 13.0 * MM):
                slab(A, x, x + 0.7 * MM, -K.GPU_FINGERS[2] + 0.6 * MM, -2.5 * MM, K.PCB_Z - 0.85 * MM,
                     K.PCB_Z + 0.85 * MM, "gold")
            x += 1.0 * MM
    o = new_obj(A, "rig_gpu", coll, None, origin=(XC, YC, -T / 2))
    ports = []
    if not lite:
        for i, (kind, y) in enumerate((("hdmi", 14.0), ("displayport", 36.0), ("displayport", 56.0),
                                       ("displayport", 76.0))):
            ports.append(P.port(f"gpu_port_{i}", kind, facing="-X", at=(bx0, y * MM, -T / 2), collection=coll))
        o = join_into(o, ports)
    # the lit lettering on the top edge, where the maker's name is lit: our invented name, its own emissive
    # mesh (it keeps the name rig_gpu_light, MESHES.md; it replaced the plain light bar, 2026-10-26)
    light = gpu_lettering(coll, lite)
    fans = []
    for i, fx in enumerate(K.GPU_FAN_X):
        fans.append(gpu_fan(f"rig_gpu_fan_{i + 1:02d}", coll, (fx, YC, -2.0 * MM), lite, phase=0.3 * i))
    return o, fans, light


# the brand names (decision 2026-10-26): names from content/room-brands.json via lib/brands.py
GPU_LETTER_H = 6.0 * MM      # EST detail-logo-edge.jpg: GEFORCE RTX cap height about 1/6 of the 40 mm edge
CASE_LETTER_H = 4.0 * MM     # EST: small print, as the O11 family's front pillar carries it


def _brand_name(o, wanted, lite):
    """brands.decal adds _lite in lite builds; the PC's lite tree uses the plain names (the rich tree is
    renamed out of the way while it exports)."""
    if lite:
        NM.set_name(o, wanted)
    return o


def gpu_lettering(coll, lite):
    from lib import brands
    c = Vector(((LIGHT[0] + LIGHT[1]) / 2, H, -T / 2))
    o = brands.decal("pc_gpu", at=c, normal=(0, 1, 0), up=(0, 0, -1), height=GPU_LETTER_H, finish="lit",
                     colour="#f4f7ff", lite=lite, name="rig_gpu_light", spacing=1.25, weight=0.025,
                     collection=coll)
    o.data.materials[0] = K.mats()["gpu_light"]          # the same light as before (the room pulses it)
    o.data.transform(Matrix.Translation(-c))
    o.location = c
    return _brand_name(o, "rig_gpu_light", lite)


def case_lettering(coll, root, lite):
    """KAIRO at the foot of the front pillar (the rear chamber's white front panel), light grey print."""
    from lib import brands
    o = brands.decal("pc_case", parent=root, at=((XP + HW) / 2, -HD, ZB + 24.0 * MM), normal=(0, -1, 0),
                     up=(0, 0, 1), height=CASE_LETTER_H, finish="printed", colour="#a4a8ad", lite=lite,
                     name="rig_case_brand", spacing=1.4, collection=coll)
    return _brand_name(o, "rig_case_brand", lite)


def xarm(A, wl, wr, z, M):
    """Bands 1.0 to 3.6 mm outside each well's two diagonal edges, full length (rim colour)."""
    tipl = (TIP, YC)
    tipr = (L - TIP, YC)
    for tip, sgn in ((tipl, -1), (tipr, 1)):
        xt = 88.9 * MM if sgn < 0 else L - 88.9 * MM
        for yend in (RIM, H - RIM):
            p0, p1 = Vector((xt, yend)), Vector(tip)
            d = (p1 - p0).normalized()
            n = Vector((-d.y, d.x))
            if n.x * (-sgn) < 0:          # outward from the well, toward the card's middle
                n = -n
            q = [p0 + n * 1.0 * MM, p1 + n * 1.0 * MM + d * 2.5 * MM, p1 + n * 3.6 * MM + d * 2.5 * MM, p0 + n * 3.6 * MM]
            A.prism([tuple(v) for v in q], z - 0.05 * MM, z, "rim", bottom=False, m=M)


def _span(poly, x):
    """The y range of a convex polygon at x."""
    ys = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (x0 - x) * (x1 - x) <= 0 and x0 != x1:
            t = (x - x0) / (x1 - x0)
            ys.append(y0 + t * (y1 - y0))
    return (min(ys), max(ys)) if len(ys) >= 2 else None


def blade_surface(A, r0, r1, a_root, a_tip, sweep, chord0, chord1, z0, z1, key, nr=6, na=4, thick=0.8 * MM,
                  m=None):
    """One swept fan blade between radii r0 and r1: its leading edge from a_root (at r0) sweeping to a_tip,
    angular chord from chord0 to chord1 (radians), pitched from z1 (leading) to z0 (trailing)."""
    grid_t, grid_b = [], []
    for i in range(nr + 1):
        s = i / nr
        r = r0 + (r1 - r0) * s
        lead = a_root + (a_tip - a_root) * s + sweep * s * s
        chord = chord0 + (chord1 - chord0) * s
        rt, rb = [], []
        for j in range(na + 1):
            t = j / na
            a = lead - chord * t
            z = z1 + (z0 - z1) * t
            camber = 0.6 * MM * math.sin(math.pi * t)
            p = (r * math.cos(a), r * math.sin(a))
            rt.append((p[0], p[1], z + camber + thick / 2))
            rb.append((p[0], p[1], z + camber - thick / 2))
        grid_t.append(A.verts(rt, m))
        grid_b.append(A.verts(rb, m))
    for i in range(nr):
        for j in range(na):
            A.face([grid_t[i][j], grid_t[i + 1][j], grid_t[i + 1][j + 1], grid_t[i][j + 1]], key)
            A.face([grid_b[i][j], grid_b[i][j + 1], grid_b[i + 1][j + 1], grid_b[i + 1][j]], key)
    for j in range(na):        # tip and root
        A.face([grid_t[nr][j], grid_b[nr][j], grid_b[nr][j + 1], grid_t[nr][j + 1]], key)
        A.face([grid_t[0][j], grid_t[0][j + 1], grid_b[0][j + 1], grid_b[0][j]], key)
    for i in range(nr):        # leading and trailing edges
        A.face([grid_t[i][0], grid_b[i][0], grid_b[i + 1][0], grid_t[i + 1][0]], key)
        A.face([grid_t[i][na], grid_t[i + 1][na], grid_b[i + 1][na], grid_b[i][na]], key)


def gpu_fan(name, coll, centre, lite, phase=0.0):
    """The card's fan rotor: seven swept blades, a hub with a turned cap, a thin ring round the tips
    (MEASURED front-fans.png). Local +Z is the axis (out of the fan face)."""
    A = P.Mesh()
    R = K.GPU_FAN_R - 1.2 * MM
    hub = K.GPU_HUB_R
    n = K.GPU_BLADES
    seg = 24 if lite else 64
    for k in range(n):
        a0 = phase + 2 * math.pi * k / n
        blade_surface(A, hub - 1 * MM, R - 0.5 * MM, a0, a0 - 0.35, -0.25, 0.95, 0.75, -7.5 * MM, -1.5 * MM, "gpu_fan",
                      nr=3 if lite else 7, na=2 if lite else 5)
    A.lathe([(0, -9 * MM), (hub, -9 * MM), (hub, -1.2 * MM), (hub - 1.0 * MM, -0.2 * MM), (0, -0.2 * MM)], seg,
            ["gpu_hub", "gpu_hub", "rim", "gpu_hub"])          # the cap's bevel catches the light
    if not lite:      # the turned rings on the cap
        for rr in (5, 9, 13, 17):        # the cap's turned grooves, barely lighter
            A.ring_face(P.circle(rr * MM + 0.2 * MM, seg), P.circle(rr * MM - 0.2 * MM, seg), -0.15 * MM, "gpu_fan")
    A.lathe([(R, -8 * MM), (R + 1.2 * MM, -8 * MM), (R + 1.2 * MM, -1.5 * MM), (R, -1.5 * MM)], seg, "gpu_fan")
    o = new_obj(A, name, coll, None, smooth=40)
    o.location = Vector(centre)
    return o


# ---------------------------------------------------------------------------
# case fans: Lian Li UNI FAN TL 120, white (KitGuru's build; SOURCES.md)
# ---------------------------------------------------------------------------
def fan_frame(A, Ar, M, lite):
    """The square frame (white), 120 x 120 x 28 with chamfered corners; its light ring (front) and edge
    strips (four sides) go into Ar (rig_fans)."""
    s = K.FAN / 2
    d = K.FAN_T / 2
    c = 9 * MM
    sq = [(-s + c, -s), (s - c, -s), (s, -s + c), (s, s - c), (s - c, s), (-s + c, s), (-s, s - c), (-s, -s + c)]
    ro = 58.5 * MM
    seg = 32 if lite else 72
    hole = P.circle(ro, seg)
    plate(A, sq, [hole], -d, d, "fan_white", "fan_white", M=M)
    # the light ring on the intake face and the strips along the four sides
    Ar.ring_face(P.circle(ro + 2.6 * MM, seg), P.circle(ro + 0.4 * MM, seg), d + 0.15 * MM, "fan_light", m=M)
    Ar.ring_face(P.circle(ro + 2.6 * MM, seg), P.circle(ro + 0.4 * MM, seg), d + 0.15 * MM, "fan_light",
                 m=M @ Matrix.Rotation(math.pi, 4, "X"))
    for k in range(4):
        R4 = M @ Matrix.Rotation(k * math.pi / 2, 4, "Z")
        # strip on the side face x = s: a thin raised bar, 76 mm long, 3 mm tall, mid-depth
        slab(Ar, s - 0.1 * MM, s + 0.3 * MM, -45 * MM, 45 * MM, -4.0 * MM, 4.0 * MM, "fan_light", R4)
    # the motor strut cross on the outlet face (4 struts) and the hub housing
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        R4 = M @ Matrix.Rotation(a, 4, "Z")
        slab(A, 20 * MM, ro + 0.5 * MM, -1.6 * MM, 1.6 * MM, -d, -d + 3 * MM, "fan_white", R4)
    A.lathe([(0, -d), (22 * MM, -d), (22 * MM, -d + 6 * MM), (0, -d + 6 * MM)], 16 if lite else 40, "fan_white", m=M)


def fan_rotor(name, coll, M, lite, phase=0.0):
    """Nine white blades and the hub; origin at the hub, local +Z the air's way."""
    A = P.Mesh()
    d = K.FAN_T / 2
    for k in range(9):
        a0 = phase + 2 * math.pi * k / 9
        blade_surface(A, 20 * MM, 57.0 * MM, a0, a0 - 0.25, -0.2, 0.62, 0.58, -8 * MM, 6 * MM, "blade",
                      nr=2 if lite else 5, na=2 if lite else 4)
    A.lathe([(0, -d + 6 * MM), (21 * MM, -d + 6 * MM), (21 * MM, d - 1.5 * MM), (19.5 * MM, d - 0.2 * MM),
             (0, d - 0.2 * MM)], 16 if lite else 48, "fan_white")
    o = new_obj(A, name, coll, None, smooth=40)
    o.matrix_world = M
    return o


def fan_matrix(centre, facing):
    """A fan's local frame at its centre: local +Z = the air's way (facing)."""
    f = {"-X": ((0, 1, 0), (0, 0, 1)), "+Y": ((-1, 0, 0), (0, 0, 1)), "+Z": ((1, 0, 0), (0, 1, 0))}[facing]
    return frame(f[0], f[1], centre)


def all_fans():
    """(centre, facing) for every case fan, numbered: side 01-03 top to bottom, rear 04-05 top to bottom,
    bottom 06-08 front to back."""
    out = []
    sf = K.SIDE_FANS
    for z in sf["z"]:
        out.append(((sf["x"] + K.FAN_T / 2 + 1 * MM, sf["y"], z), "-X"))
    rf = K.REAR_FANS
    for z in rf["z"]:
        out.append(((rf["x"], rf["y"] - 4 * MM - K.FAN_T / 2, z), "+Y"))
    bf = K.BOTTOM_FANS
    for y in sorted(bf["y"]):
        out.append(((bf["x"], y, bf["z"] + K.FAN_T / 2), "+Z"))
    return out


# ---------------------------------------------------------------------------
# the inside: board, cooler, memory, radiator, PSU, cables
# ---------------------------------------------------------------------------
def build_static(coll, parent, lite, Afans):
    A = P.Mesh()
    Ar = Afans
    for i, (c, f) in enumerate(all_fans()):
        fan_frame(A, Ar, fan_matrix(c, f), lite)
    bx = K.BOARD["x"]
    y0, y1 = K.BOARD["y"]
    z0, z1 = K.BOARD["z"]
    # board (white PCB) and its standoffs; parts on the -X side (toward the glass)
    slab(A, bx - 1.6 * MM, bx, y0, y1, z0, z1, "pcb", None)
    xf = bx - 1.6 * MM                                 # the component side
    # the rear I/O cover ("shroud") and the VRM heatsinks, white (EST from build-1/2.jpg)
    slab(A, xf - 30 * MM, xf, y1 - 32 * MM, y1, 205 * MM, z1, "heatsink")
    slab(A, xf - 24 * MM, xf, 62 * MM, 168 * MM, 322 * MM, 350 * MM, "heatsink")
    slab(A, xf - 24 * MM, xf, 150 * MM, 172 * MM, 236 * MM, 322 * MM, "heatsink")
    if not lite:      # fins on the VRM heatsink
        for k in range(12):
            yy = (66 + k * 8.5) * MM
            slab(A, xf - 27 * MM, xf - 24 * MM, yy, yy + 4 * MM, 324 * MM, 348 * MM, "heatsink")
    # M.2 covers and the chipset cover (flat white plates on the lower board)
    slab(A, xf - 5 * MM, xf, -24 * MM, 150 * MM, 150 * MM, 168 * MM, "heatsink")
    slab(A, xf - 7 * MM, xf, -24 * MM, 100 * MM, 64 * MM, 140 * MM, "heatsink")
    slab(A, xf - 3 * MM, xf, 105 * MM, 200 * MM, 64 * MM, 140 * MM, "heatsink")
    # PCIe slots (grey) under and below the card
    for zz in (195, 154, 113):
        slab(A, xf - 9 * MM, xf, 60 * MM, 150 * MM, zz * MM, (zz + 7) * MM, "grey")
    # memory: four slots, two white sticks (A2, B2)
    for k in range(4):
        yy = (28 + k * 9) * MM
        slab(A, xf - 7 * MM, xf, yy, yy + 6 * MM, 222 * MM, 352 * MM, "black")
    for k in (1, 3):
        yy = (28 + k * 9) * MM
        slab(A, xf - 42 * MM, xf - 7 * MM, yy + 0.4 * MM, yy + 5.6 * MM, 224 * MM, 350 * MM, "heatsink", edge="white")
        slab(A, xf - 43 * MM, xf - 42 * MM, yy + 1.4 * MM, yy + 4.6 * MM, 226 * MM, 348 * MM, "fan_light" if False else "white")
    # 24-pin and EPS headers
    slab(A, xf - 14 * MM, xf, y0 + 2 * MM, y0 + 10 * MM, 255 * MM, 305 * MM, "black")
    slab(A, xf - 12 * MM, xf, 20 * MM, 60 * MM, z1 - 14 * MM, z1 - 4 * MM, "black")
    # the AIO pump head: a white block with a square dark screen (blank; KitGuru's shows numbers)
    cy, cz = K.CPU["y"], K.CPU["z"]
    A.prism(P.rrect(64 * MM, 64 * MM, 9 * MM, 2 if lite else 6, cy, cz), -38 * MM, 0.0, "white",
            m=frame((0, 1, 0), (0, 0, 1), (xf, 0, 0)))
    slab(A, xf - 38.6 * MM, xf - 38 * MM, cy - 25 * MM, cy + 25 * MM, cz - 25 * MM, cz + 25 * MM, "lcd")
    # the radiator (360) behind the side fans in the rear chamber's front, white
    sf = K.SIDE_FANS
    rx0 = sf["x"] + K.FAN_T + 2 * MM
    slab(A, rx0, rx0 + 27 * MM, sf["y"] - 62 * MM, sf["y"] + 62 * MM, 45 * MM, 438 * MM, "heatsink", edge="white")
    slab(A, rx0 + 3 * MM, rx0 + 24 * MM, sf["y"] - 64 * MM, sf["y"] + 64 * MM, 45 * MM, 62 * MM, "white")
    slab(A, rx0 + 3 * MM, rx0 + 24 * MM, sf["y"] - 64 * MM, sf["y"] + 64 * MM, 421 * MM, 438 * MM, "white")
    if not lite:              # the radiator's fins, seen through the right panel and with it off
        for k in range(178):
            zz = 63 * MM + k * 2.0 * MM
            slab(A, rx0 + 27 * MM, rx0 + 27.4 * MM, sf["y"] - 58 * MM, sf["y"] + 58 * MM, zz, zz + 0.8 * MM, "grey")
    # the cable cover plate in the rear chamber (rear-chamber.jpg), with its keyholes
    slab(A, 133 * MM, 135 * MM, -128 * MM, -26 * MM, 75 * MM, 455 * MM, "white")
    for zz in (120, 200, 300, 380):
        for yy in (-110, -44):
            A.prism(P.circle(5 * MM, 12, yy * MM, zz * MM), 2.0 * MM, 2.05 * MM, "port",
                    m=frame((0, 1, 0), (0, 0, 1), (133 * MM, 0, 0)), bottom=False)
    # the perforated cage over the PSU (rear-chamber.jpg)
    slab(A, 70 * MM, 146 * MM, 92 * MM, 228 * MM, 262 * MM, 375 * MM, "white")
    slab(A, 146 * MM, 146.3 * MM, 98 * MM, 222 * MM, 268 * MM, 369 * MM, "hex")
    # the PSU in the rear chamber on its side, its fan toward the right panel's mesh; its end in the bracket
    p = K.PSU
    slab(A, p["x"][0], p["x"][1], p["y"][0], K.PSU_BRACKET["y"][1] - 4 * MM, p["z"][0], p["z"][1], "white")
    Mp = at_plane(F_RIGHT, p["x"][1])
    pc_y = (p["y"][0] + p["y"][1]) / 2
    pc_z = (p["z"][0] + p["z"][1]) / 2
    A.ring_face(P.circle(62 * MM, 48, pc_y, pc_z), P.circle(58 * MM, 48, pc_y, pc_z), 0.2 * MM, "grey", m=Mp)
    A.prism(P.circle(57 * MM, 32 if lite else 64, pc_y, pc_z), 0.0, 0.1 * MM, "hex", m=Mp, bottom=False)
    # the PSU's end (seen at the back): the IEC socket and switch
    Mpe = at_plane(F_BACK, K.PSU_BRACKET["y"][1] - 4 * MM)
    slab(A, -128 * MM, -96 * MM, 120 * MM, 146 * MM, 0.0, 0.3 * MM, "black", Mpe)
    slab(A, -128 * MM, -112 * MM, 160 * MM, 175 * MM, 0.0, 1.5 * MM, "black", Mpe)
    slab(A, -140 * MM, -60 * MM, 185 * MM, 225 * MM, 0.0, 0.2 * MM, "hex", Mpe)
    # the I/O shield (black plate with the board's ports, generic) in the rear opening
    Mio = at_plane(F_BACK, K.CASE_D / 2 - 6 * MM)
    slab(A, -48 * MM, -4 * MM, 197 * MM, 357 * MM, 0.0, 1 * MM, "black", Mio)
    if not lite:
        for k, (u, v, w, h) in enumerate(((-40, 215, 14, 6), (-24, 215, 14, 6), (-40, 232, 12, 5), (-24, 232, 12, 5),
                                          (-40, 250, 12, 5), (-24, 250, 12, 5), (-34, 272, 15, 13), (-34, 300, 14, 6),
                                          (-34, 320, 8, 3), (-34, 335, 12, 8))):
            slab(A, (u - w / 2) * MM, (u + w / 2) * MM, (v - h / 2) * MM, (v + h / 2) * MM, 1 * MM, 1.6 * MM,
                 "steel" if k % 3 else "port", Mio)
    # standoff screws (board corners)
    if not lite:
        for (yy, zz) in ((y0 + 6 * MM, z1 - 6 * MM), (y1 - 6 * MM, z1 - 6 * MM), (y0 + 6 * MM, z0 + 6 * MM),
                         (y1 - 6 * MM, z0 + 6 * MM), (y0 + 6 * MM, (z0 + z1) / 2), (y1 - 40 * MM, (z0 + z1) / 2)):
            A.lathe([(0, 0), (3 * MM, 0), (3 * MM, 1.5 * MM), (0, 1.5 * MM)], 12,
                    "steel", m=frame((0, 1, 0), (0, 0, -1), (xf, yy, zz)))
    o = new_obj(A, "rig_static", coll, parent)
    perf = bpy.data.materials.get("mat_pc_perf")
    hexm = bpy.data.materials.get("mat_pc_hexmesh")
    tile_uvs(o, {hexm.name: (10.0 * MM, 10.0 * MM * math.sqrt(3))} if hexm else {})
    cables = build_cables(coll, lite)
    return join_into(o, cables) if cables else o


def bundle(name, coll, pts, n, r, spread, lite, axis=(0, 0, 1)):
    """n white sleeved cables side by side along a path (offset along `axis`, the bundle's width)."""
    out = []
    ax = Vector(axis).normalized()
    for k in range(n):
        off = ax * ((k - (n - 1) / 2) * spread)
        p = [tuple(Vector(q) + off) for q in pts]
        out.append(P.cable(f"{name}_{k:02d}", p, r=r, seg=6 if lite else 10, mats={"cable": K.mats()["cable"]},
                           to_mesh=True, lite=lite, collection=coll))
    return out


def build_cables(coll, lite):
    c = []
    xf = K.BOARD["x"] - 1.6 * MM
    y0 = K.BOARD["y"][0]
    n24 = 6 if lite else 12
    # 24-pin: from the header out toward the glass, round and into the tray's front grommet (two rows)
    for row, dx in enumerate((0.0, -4.6 * MM)):
        c += bundle(f"pc_cab_24p_{row}", coll,
                    [(xf - 14 * MM + dx, y0 + 6 * MM, 280 * MM), (xf - 26 * MM + dx, y0 - 10 * MM, 280 * MM),
                     (K.TRAY_X - 12 * MM + dx, -46 * MM, 280 * MM), (K.TRAY_X + 16 * MM, -46 * MM, 280 * MM)],
                    n24, 2.0 * MM, 4.2 * MM, lite)
    # the card's 12V-2x6 cable: from the socket on its top edge, out, forward and into the grommet
    gm = pc_gpu_point((SOCKET[0] + SOCKET[1]) / 2, K.GPU_H + 2 * MM, -K.GPU_T / 2)
    for row, dz in enumerate((-2.2 * MM, 2.2 * MM)):        # 12V-2x6: a round bundle of two rows
        o = Vector((0, 0, dz))
        c += bundle(f"pc_cab_gpu_{row}", coll, [gm + o, gm + o + Vector((-16 * MM, 0, 0)),
                                                gm + o + Vector((-26 * MM, -12 * MM, 26 * MM)),
                                                Vector((-60 * MM, -40 * MM, 246 * MM)) + o,
                                                Vector((0.0, -46 * MM, 250 * MM)) + o,
                                                Vector((K.TRAY_X - 4 * MM, -44 * MM, 250 * MM)) + o,
                                                Vector((K.TRAY_X + 22 * MM, -44 * MM, 250 * MM)) + o],
                    2 if lite else 4, 1.9 * MM, 4.0 * MM, lite, axis=(0, 1, 0))
    # EPS 8-pin x 2 up into the top grommet
    c += bundle("pc_cab_eps", coll, [(xf - 12 * MM, 40 * MM, K.BOARD["z"][1] - 10 * MM),
                                     (xf - 22 * MM, 40 * MM, K.BOARD["z"][1] + 20 * MM),
                                     (K.TRAY_X - 18 * MM, 40 * MM, K.CASE_H - 40 * MM),
                                     (K.TRAY_X + 20 * MM, 40 * MM, K.CASE_H - 45 * MM)],
                3 if lite else 8, 1.8 * MM, 3.8 * MM, lite, axis=(0, 1, 0))
    # the AIO's two tubes: from the pump's top over to the radiator's top (white sleeved, 11 mm)
    cy, cz = K.CPU["y"], K.CPU["z"]
    sf = K.SIDE_FANS
    rx = sf["x"] + K.FAN_T + 15 * MM
    for k, dy in enumerate((-10 * MM, 10 * MM)):
        c.append(P.cable(f"pc_tube_{k}", [(xf - 20 * MM, cy + dy, cz + 32 * MM), (xf - 30 * MM, cy + dy, cz + 80 * MM),
                                          (xf - 40 * MM, cy - 60 * MM + dy, 420 * MM), (20 * MM, sf["y"] + 10 * MM + dy, 440 * MM),
                                          (rx, sf["y"] + 30 * MM + dy, 445 * MM), (rx, sf["y"] + 40 * MM + dy, 432 * MM)],
                         r=5.5 * MM, seg=8 if lite else 16, mats={"cable": K.mats()["cable"]}, to_mesh=True, lite=lite,
                         collection=coll))
    # the PSU's cables in the rear chamber: three bundles from its front up to the grommets (rear-chamber.jpg)
    p = K.PSU
    for k, (zz, top) in enumerate(((p["z"][1] - 30 * MM, 300 * MM), (p["z"][1] - 70 * MM, 250 * MM),
                                    (p["z"][0] + 30 * MM, 160 * MM))):
        c += bundle(f"pc_cab_psu_{k}", coll, [(105 * MM, p["y"][0] + 2 * MM, zz), (105 * MM, p["y"][0] - 30 * MM, zz),
                                             (100 * MM, -10 * MM - k * 12 * MM, top), (75 * MM, -40 * MM, top + 20 * MM)],
                    4 if lite else 8, 1.9 * MM, 4.0 * MM, lite, axis=(1, 0, 0))
    return c


def pc_gpu_point(x, y, z):
    """A point in the card frame -> the case frame."""
    return K.gpu_root_matrix() @ Vector((x, y, z))


# ---------------------------------------------------------------------------
# the whole
# ---------------------------------------------------------------------------
def build(root, coll, lite=False):
    sfx = "_lite" if lite else ""
    names = {}
    case, side = build_case(coll, root, lite)
    glass = build_glass(coll, root, lite)
    Afans = P.Mesh()
    static = build_static(coll, root, lite, Afans)
    rings = new_obj(Afans, "rig_fans", coll, root)
    rotors = []
    for i, (c, f) in enumerate(all_fans()):
        r = fan_rotor(f"rig_fan_{i + 1:02d}", coll, fan_matrix(c, f), lite, phase=0.17 * i)
        mw = r.matrix_world.copy()
        r.parent = root
        r.matrix_world = mw
        rotors.append(r)
    # the card, built in its own frame, under a root placed in the case (rig_gpu_root stays Blender-only)
    groot = bpy.data.objects.new("rig_gpu_root", None)
    coll.objects.link(groot)
    groot.parent = root
    groot.matrix_world = K.gpu_root_matrix()
    gpu, gfans, glight = build_gpu(coll, groot, lite)
    for o in [gpu] + gfans + [glight]:
        o.parent = groot
    gfans_names = [o.name for o in gfans]
    cbrand = case_lettering(coll, root, lite)
    names["case"] = [case.name, side.name, glass.name, cbrand.name]
    names["case_all"] = names["case"]
    names["gpu"] = [gpu.name, glight.name] + gfans_names
    names["gpu_all"] = names["gpu"]
    names["fans"] = [rings.name] + [r.name for r in rotors]
    names["static"] = [static.name]
    names["pc_all"] = names["case"] + names["gpu"] + names["fans"] + names["static"]
    names["all"] = names["pc_all"]
    return names
