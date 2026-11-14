"""The guitars in the room (2026-11-13): guitars 01, 03, 05 and 06 (built 2026-11-12/13, blender/props/guitar_0N.py) placed
from their lite GLBs, cut for the web, and the wall hangers for 01 to 03. Used by blender/build_v3.py.

    import_cut(key)        blender/out/guitar_<key>-lite.glb imported (guitar_<key> empty at the guitar's pivot, with
                           guitar_<key>_body and guitar_<key>_strings), its atlas and ORM scaled down for the web
                           (ATLAS_PX, ORM_PX). The rich and lite files are never changed.
    place_wall(objs, i, key)   wall slot i (plan v3 WALL_GUITARS_V3): the body's centre plane WG_OFF off the wall, the
                           lowest point at WG_BOTTOM, the body centred on the slot's y. WALL: 01, 05 (the Explorer, since
                           2026-11-13) and 03, all three by the same rule.
    place_rack(objs, slot) rack slot (0..2): the pivot (the body's lowest point at the rack's lean, on the centre plane)
                           on the cradle, the string line through the rack's notch line (as guitar_04).
    hangers(...)           a wall hanger under each head contact (the pivot; the double-neck has one per neck): a round
                           wall plate, an arm, a yoke with two padded prongs the head rests on, the gap the builders use.
    DEFERRED               the custom property that keeps a guitar out of room.glb (it ships in guitars.glb).

Frames (MESHES.md, obj_guitars): every guitar_<key> empty is at its pivot, +X the viewer's right, -Y out of the front,
+Z up the neck. In the lite GLBs exported upright by props/guitar_shots.py, the body's centre plane is at the empty's
local y = -(the empty's y), the tail on it at the origin. guitar_02's GLB is older: its empty sits at its hook contact,
the centre plane 18.2 mm behind it (props/guitar_02.py PIV z -4.05, body 44.5 thick).
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

from lib import constants as C, plan_v3 as P

OUT = os.path.join(C.BLENDER_DIR, "out")
ATLAS_PX = int(os.environ.get("GUITARS_ATLAS", "512"))
ORM_PX = int(os.environ.get("GUITARS_ORM", "256"))
DEFERRED = "deferred"                                   # custom property: the file the object ships in ("guitars")
CENTRE_LOCAL_Y = {"02": 0.0182}                          # see the docstring; the others: -(empty's y at import)
# the double-neck's two head contacts, from its pivot (props/guitar_03.py: 12-string at u -77.0, v 801.9, z -28.1;
# 6-string at u 65.4, v 809.1, z -30.7; the pivot midway), in the empty's frame (x = u, y = -z, z = v), metres
CONTACTS = {"03": [(-0.0712, -0.0013, -0.0036), (0.0712, 0.0013, 0.0036)],
            # the Explorer hangs since 2026-11-13 (owner: "white stratt guitar should go on rack and other white should be
            # hanged on the wall"): its pivot is the rack contact, so the head contact is measured on the lite GLB (cut
            # through the neck: the nut at z 0.885, 43 mm wide on the string line x 0.1952; 48 mm, past the gap, at 0.8875)
            "05": [(0.1952, 0.003, 0.8875)]}
WALL = ("01", "05", "03")                                # left to right, as seen from the room
RACK = ((1, "02"), (2, "06"))                            # slot 0 is guitar_04's, placed with the music side
HOOK_GAP = 0.046                                         # the hanger's inner gap (guitar_specs: hook gap 46 mm)
_PIVOT_U = {}
HANGER = dict(plate_r=0.022, plate_t=0.008, arm_r=0.0055, prong_r=0.0045, back=0.022, front=0.030, drop=0.035)


def _objs(key):
    root = bpy.data.objects[f"guitar_{key}"]
    return root, [root] + list(root.children)


def import_cut(key):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, f"guitar_{key}-lite.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    root = next(o for o in new if o.parent is None)
    assert root.name == f"guitar_{key}", root.name
    info = dict(centre_y=-root.location.y, pivot=[round(v, 4) for v in root.location])
    _PIVOT_U[key] = root.location.x                         # the pivot's u: the tail's string line is at x 0 upright
    for o in new:
        if o.type != "MESH":
            continue
        for m in o.data.materials:
            for n in m.node_tree.nodes:
                if n.bl_idname == "ShaderNodeTexImage" and n.image and n.image.size[0] > 0:
                    im = n.image
                    px = ORM_PX if "orm" in im.name else ATLAS_PX
                    if im.size[0] > px:
                        im.scale(px, px)
                        im.pack()                       # the scaled pixels, so a saved .blend keeps them
    for o in new:
        o[DEFERRED] = "guitars"
    info["images"] = {im.name: list(im.size) for im in bpy.data.images if im.name.startswith(f"guitar_{key}_")}
    info["tris"] = {o.name: _tris(o) for o in new if o.type == "MESH"}
    return root, new, info


def _tris(o):
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)


def _local_box(root, objs):
    """The meshes' box in the empty's own frame (the empty set to identity for the measure)."""
    keep = root.matrix_world.copy()
    root.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    root.matrix_world = keep
    bpy.context.view_layer.update()
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def place_wall(key, i, centre_y=None):
    """Wall slot i: facing the room (-X), the centre plane WG_OFF off the right wall, the lowest point on WG_BOTTOM."""
    WG = P.WALL_GUITARS_V3
    root, objs = _objs(key)
    lo, hi = _local_box(root, objs)
    cy = CENTRE_LOCAL_Y.get(key, centre_y)
    # the empty's local axes after the turn: +X -> world -Y, +Y -> world +X (the wall), +Z up
    x = P.RX - WG["off_wall"] - cy
    y = WG["y"][i] + (lo.x + hi.x) / 2
    z = WG["bottom"] - lo.z
    root.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(-90), 4, "Z")
    bpy.context.view_layer.update()
    head_back = hi.y - cy                                   # the head tip behind the centre plane
    return dict(slot=i, pivot=[round(v, 4) for v in (x, y, z)], head_clear=round(WG["off_wall"] - head_back, 4),
                length=round(hi.z - lo.z, 4), width=round(hi.x - lo.x, 4))


def place_rack(key, slot):
    """Rack slot: the pivot on the cradle at the rack's lean, the string line through x -0.08 at the cradle (guitar_04's)."""
    rk = P.RACK_V3
    root, objs = _objs(key)
    th = math.radians(rk["lean"])
    u_p = _PIVOT_U.get(key, 0.0)                            # guitar_02's pivot is its hook contact, on the string line
    # the centre plane on the slot line (guitar_02's is 18.2 mm behind its empty: local +Y, the rack's -Y once turned)
    sl = (slot - (rk["slots"] - 1) / 2) * rk["pitch"] + CENTRE_LOCAL_Y.get(key, 0.0)
    # turned half round (2026-11-13, owner: "turn the face of guitar toward main side"): the front out of the rack's +Y,
    # the side _rack_yaw turns 30 deg off the About camera; the lean flipped too, so the neck still tips onto the bar
    x_p = -0.08 - u_p / math.cos(th)
    RM = Matrix.Translation((rk["x"], rk["y"], 0)) @ Matrix.Rotation(math.radians(rk["yaw"]), 4, "Z")
    root.matrix_world = (RM @ Matrix.Translation((x_p, sl, rk["cradle"])) @ Matrix.Rotation(math.pi, 4, "Z")
                         @ Matrix.Rotation(-th, 4, "Y"))
    bpy.context.view_layer.update()
    # the pivot is the lowest point for the other lean: slide up the lean line (the string line stays in the notch)
    # until the body's lowest point is on the cradle
    pts = [o.matrix_world @ v.co for o in objs if o.type == "MESH" for v in o.data.vertices]
    s = (rk["cradle"] - min(p.z for p in pts)) / math.cos(th)
    root.matrix_world = RM @ Matrix.Translation((s * math.sin(th), 0, s * math.cos(th))) @ RM.inverted() @ root.matrix_world
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ v.co for o in objs if o.type == "MESH" for v in o.data.vertices]
    return dict(slot=slot, lowest=round(min(p.z for p in pts), 4), cradle=rk["cradle"],
                box=[[round(min(p[k] for p in pts), 3) for k in range(3)], [round(max(p[k] for p in pts), 3) for k in range(3)]])


def _cyl(bm, a, b, r, seg=12):
    import bmesh
    a, b = Vector(a), Vector(b)
    d = b - a
    ln = d.length
    q = d.normalized().to_track_quat("Z", "Y")
    M = Matrix.Translation(a) @ q.to_matrix().to_4x4() @ Matrix.Translation((0, 0, ln / 2))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=ln, matrix=M)


def _ball(bm, c, r):
    import bmesh
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r, matrix=Matrix.Translation(Vector(c)))


def hangers(material, parent):
    """One hanger under each wall guitar's head contact. Returns the mesh objects (named guitars_hook_NN, joined into
    guitars_static by the build) and their contact points."""
    import bmesh
    H = HANGER
    out, pts = [], []
    n = 0
    for key in WALL:
        root = bpy.data.objects[f"guitar_{key}"]
        for c in CONTACTS.get(key, [(0.0, 0.0, 0.0)]):
            p = root.matrix_world @ Vector(c)               # the head rests here (mid-thickness, gap-wide)
            n += 1
            bm = bmesh.new()
            ztop = p.z                                      # the prongs' top
            zp = ztop - H["prong_r"]
            xb, xf = p.x + H["back"], p.x - H["front"]      # behind and in front of the head
            wall = P.RX
            zw = zp - H["drop"]                             # the arm leaves the wall a little lower and rises
            _cyl(bm, (wall, p.y, zw), (wall - H["plate_t"], p.y, zw), H["plate_r"], 20)
            _cyl(bm, (wall - H["plate_t"], p.y, zw), (xb, p.y, zp), H["arm_r"])
            half = HOOK_GAP / 2 + H["prong_r"]
            _cyl(bm, (xb, p.y - half, zp), (xb, p.y + half, zp), H["prong_r"])
            for s in (-1, 1):
                y = p.y + s * half
                _ball(bm, (xb, y, zp), H["prong_r"])
                _cyl(bm, (xb, y, zp), (xf, y, zp), H["prong_r"])
                _cyl(bm, (xf, y, zp), (xf - 0.004, y, zp + 0.014), H["prong_r"])
                _ball(bm, (xf - 0.004, y, zp + 0.014), H["prong_r"] * 1.15)
            me = bpy.data.meshes.new(f"guitars_hook_{n:02d}")
            bm.to_mesh(me)
            bm.free()
            for poly in me.polygons:
                poly.use_smooth = True
            o = bpy.data.objects.new(f"guitars_hook_{n:02d}", me)
            bpy.context.scene.collection.objects.link(o)
            me.materials.append(material)
            if parent is not None:
                o.parent = parent
                o.matrix_parent_inverse = parent.matrix_world.inverted()
            out.append(o)
            pts.append([round(v, 4) for v in p])
    return out, pts
