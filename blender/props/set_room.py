"""set_room: floor, walls, ceiling, skirting, the window opening with its stone ledge,
the door opening, and the home view anchors. All numbers from blender/lib/constants.py
(ROOM, WINDOW, DOOR, HERO), the same ones the approved room plan sheet draws.

World frame (MESHES.md section 1): origin on the floor at the room's centre, back wall
(window, desk) at +Y, viewer at -Y, left wall at -X, right wall at +X, Z up.

Names: room_floor, room_wall_back, room_wall_left, room_wall_right, room_ceiling,
room_skirting (listed), room_window_ledge and room_threshold (free names), the anchors
room_view and room_view_target (listed, exported), and bake_wall_front, bake_door
(Blender only, never exported: they close the room for light and renders).
"""
import bpy

from lib import constants as C, geo, materials as M

R, WIN, DOOR, HERO = C.ROOM, C.WINDOW, C.DOOR, C.HERO
RX, RY, H = C.RX, C.RY, C.ROOM["height"]
BT, ST = R["wall_back_t"], R["wall_side_t"]
FRONT_T = ST                    # the front wall (bake only) is an inner wall too
CEIL_T = 0.12


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
    parts["room_floor"] = geo.box("room_floor", -RX, RX, -RY, RY, -0.02, 0.0, material=oak, **kw)
    # walls overlap each other, the floor and the ceiling inside their thickness: a seam where two
    # boxes only touch lets light through in EEVEE (seen as speckles in the first storm test)
    zb, zt = -0.02, H + CEIL_T

    # back wall with the window opening: four blocks around the hole
    x0, x1, sill, head = WIN["x0"], WIN["x1"], WIN["sill"], WIN["head"]
    back = geo.boxes("room_wall_back", [
        (-RX - ST, x0, RY, RY + BT, zb, zt), (x1, RX + ST, RY, RY + BT, zb, zt),
        (x0, x1, RY, RY + BT, zb, sill), (x0, x1, RY, RY + BT, head, zt)], material=wall, **kw)
    parts["room_wall_back"] = back
    # side walls run past the corners, so the corners are closed
    y0, y1, dh = DOOR["y0"], DOOR["y1"], DOOR["head"]
    parts["room_wall_left"] = geo.boxes("room_wall_left", [
        (-RX - ST, -RX, -RY - FRONT_T, y0, zb, zt), (-RX - ST, -RX, y1, RY + BT, zb, zt),
        (-RX - ST, -RX, y0, y1, dh, zt)], material=wall, **kw)
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

    # stone: the window's inside ledge (the plant stands on it) and the door threshold
    led = geo.box("room_window_ledge", x0 - 0.04, x1 + 0.04, RY - WIN["ledge_d"], RY + BT * 0.5,
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
