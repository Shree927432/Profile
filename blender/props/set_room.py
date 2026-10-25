"""set_room: floor, walls, ceiling, skirting, the window opening with its stone ledge,
the door opening, and the home view anchors. ROOM and DOOR from blender/lib/constants.py,
the window and the hero camera from blender/lib/plan_v2.py (WINDOW_V2, HERO_V2), the same
numbers the approved v2 sheet draws.

World frame (MESHES.md section 1): origin on the floor at the room's centre, back wall
(window) at +Y, viewer at -Y, left wall (AI lab, door) at -X, right wall at +X, Z up.

Light tightness: each wall is one closed mesh with its opening cut by a boolean (no blocks
that only touch at the window or the door), the walls overlap each other and the ceiling
inside their thickness, and the floor runs under all four walls. A seam where two boxes only
touch lets EEVEE leak light (the speckles in the first storm test, 2026-10-22).

Names: room_floor, room_wall_back, room_wall_left, room_wall_right, room_ceiling,
room_skirting (listed), room_window_ledge and room_threshold (free names), the anchors
room_view and room_view_target (listed, exported), and bake_wall_front, bake_door
(Blender only, never exported: they close the room for light and renders).
"""
import bpy

from lib import constants as C, geo, materials as M, plan_v2 as P

R, WIN, DOOR, HERO = C.ROOM, P.WINDOW_V2, C.DOOR, P.HERO_V2
RX, RY, H = C.RX, C.RY, C.ROOM["height"]
BT, ST = R["wall_back_t"], R["wall_side_t"]
FRONT_T = ST                    # the front wall (bake only) is an inner wall too
CEIL_T = 0.12


def _cut(obj, cutters):
    """Boolean-subtract boxes (x0, x1, y0, y1, z0, z1) from obj and apply it: one closed mesh."""
    tmp = []
    for i, c in enumerate(cutters):
        t = geo.box(f"{obj.name}_cut_{i}", *c, collection=obj.users_collection[0])
        tmp.append(t)
        m = obj.modifiers.new(f"cut_{i}", "BOOLEAN")
        m.operation, m.object, m.solver = "DIFFERENCE", t, "EXACT"
    bpy.context.view_layer.update()
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = bpy.data.meshes.new_from_object(ev)
    obj.modifiers.clear()
    old, obj.data = obj.data, me
    bpy.data.meshes.remove(old)
    me.name = obj.name + "_mesh"
    for t in tmp:
        d = t.data
        bpy.data.objects.remove(t)
        bpy.data.meshes.remove(d)
    return obj


def build():
    root, coll = geo.root("set_room")
    kw = dict(collection=coll, parent=root, smooth=False)
    oak = M.oak_floor("mat_room_floor")
    wall = M.wall_paint("mat_room_wall")
    ceil = M.wall_paint("mat_room_ceiling", "#ebe7e0")
    skirt = M.principled("mat_room_skirting", base=C.COL["skirting"], rough=0.4, coat=0.4, coat_rough=0.15)
    stone = M.stone("mat_room_stone")
    door_m = M.principled("mat_room_door", base="#d9d2c4", rough=0.5, coat=0.3, coat_rough=0.2)

    parts = {}
    # walls overlap each other and the ceiling inside their thickness, and the floor runs under them
    zb, zt = -0.02, H + CEIL_T
    parts["room_floor"] = geo.box("room_floor", -RX - ST, RX + ST, -RY - FRONT_T, RY + BT, zb, 0.0,
                                  material=oak, **kw)

    # back wall: one box with the window cut through it, down to the stone ledge's underside
    x0, x1, sill, head = WIN["x0"], WIN["x1"], WIN["sill"], WIN["head"]
    back = geo.box("room_wall_back", -RX - ST, RX + ST, RY, RY + BT, zb, zt, material=wall, **kw)
    parts["room_wall_back"] = _cut(back, [(x0, x1, RY - 0.01, RY + BT + 0.01, sill - WIN["ledge_t"], head)])
    # side walls run past the corners, so the corners are closed; the door is cut from the left one
    y0, y1, dh = DOOR["y0"], DOOR["y1"], DOOR["head"]
    left = geo.box("room_wall_left", -RX - ST, -RX, -RY - FRONT_T, RY + BT, zb, zt, material=wall, **kw)
    parts["room_wall_left"] = _cut(left, [(-RX - ST - 0.01, -RX + 0.01, y0, y1, zb - 0.01, dh)])
    parts["room_wall_right"] = geo.box("room_wall_right", RX, RX + ST, -RY - FRONT_T, RY + BT, zb, zt,
                                       material=wall, **kw)
    parts["room_ceiling"] = geo.box("room_ceiling", -RX - ST, RX + ST, -RY - FRONT_T, RY + BT, H, H + CEIL_T,
                                    material=ceil, **kw)

    # skirting on the back and side walls, broken at the door
    sh, stk = R["skirting_h"], R["skirting_t"]
    sk = geo.boxes("room_skirting", [
        (-RX, RX, RY - stk, RY, 0, sh),
        (RX - stk, RX, -RY, RY - stk, 0, sh),
        (-RX, -RX + stk, -RY, y0, 0, sh), (-RX, -RX + stk, y1, RY - stk, 0, sh)], material=skirt, **kw)
    geo.bevel(sk, 0.003, segments=2)
    parts["room_skirting"] = sk

    # stone: the window's ledge, the full depth of the wall and the bottom of the opening (the plant
    # stands on it), and the door threshold
    led = geo.box("room_window_ledge", x0 - 0.04, x1 + 0.04, RY - WIN["ledge_d"], RY + BT,
                  sill - WIN["ledge_t"], sill, material=stone, **kw)
    geo.bevel(led, 0.004, segments=3)
    parts["room_window_ledge"] = led
    parts["room_threshold"] = geo.box("room_threshold", -RX - ST, -RX, y0, y1, -0.02, 0.004, material=stone, **kw)

    # bake only: the front wall and the door leaf, open along the front wall
    parts["bake_wall_front"] = geo.box("bake_wall_front", -RX - ST, RX + ST, -RY - FRONT_T, -RY, zb, zt,
                                       material=wall, **kw)
    leaf = DOOR["leaf_t"]
    door = geo.box("bake_door", -RX, -RX + (y1 - y0) - 0.02, -RY, -RY + leaf, 0.01, dh - 0.01, material=door_m, **kw)
    geo.bevel(door, 0.004, segments=2)
    parts["bake_door"] = door

    # the home view: the hero camera on the sheet
    geo.empty("room_view", HERO["pos"], coll, parent=root)
    geo.empty("room_view_target", HERO["target"], coll, parent=root)
    return root, parts
