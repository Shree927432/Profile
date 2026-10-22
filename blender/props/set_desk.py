"""set_desk: the desk (top and steel frame), the keyboard and the mouse.

Numbers from LAYOUT in blender/lib/constants.py (desk, keyboard, mouse). Built in world
coordinates under the `set_desk` root. Names (MESHES.md section 4): desk_top, desk_legs,
desk_keyboard, desk_mouse; the export joins them into desk_static.
"""
import bmesh
import bpy

from lib import constants as C, geo, materials as M

L = C.LAYOUT


def build():
    root, coll = geo.root("set_desk")
    kw = dict(collection=coll, parent=root)
    d = L["desk"]
    x0, x1 = d["x"] - d["w"] / 2, d["x"] + d["w"] / 2
    y0, y1 = d["y"] - d["d"] / 2, d["y"] + d["d"] / 2
    top_z, t = d["h"], d["top_t"]
    wood = M.walnut("mat_desk_top", grain="X", gloss=False)
    steel = M.principled("mat_desk_steel", base="#17171a", metal=0.6, rough=0.42)
    alu = M.principled("mat_desk_alu", base="#c4c7cc", metal=1.0, rough=0.34)
    keycap = M.principled("mat_desk_keycap", base="#2a2b2f", rough=0.55, spec=0.4)
    mouse_m = M.principled("mat_desk_mouse", base="#e9e8e4", rough=0.35, coat=0.3, coat_rough=0.2)
    parts = {}

    top = geo.box("desk_top", x0, x1, y0, y1, top_z - t, top_z, material=wood, **kw)
    geo.bevel(top, 0.004, segments=3)
    parts["desk_top"] = top

    # steel frame: four square legs, side rails and a back rail under the top
    s, i = 0.05, 0.04                       # leg section, inset from the top's edges
    under = top_z - t
    rail = 0.06
    lx0, lx1, ly0, ly1 = x0 + i, x1 - i, y0 + i, y1 - i
    specs = [(lx - s / 2, lx + s / 2, ly - s / 2, ly + s / 2, 0.0, under) for lx in (lx0, lx1) for ly in (ly0, ly1)]
    specs += [(lx - 0.015, lx + 0.015, ly0, ly1, under - rail, under) for lx in (lx0, lx1)]
    specs += [(lx0, lx1, ly1 - 0.015, ly1 + 0.015, under - rail, under)]
    legs = geo.boxes("desk_legs", specs, material=steel, **kw)
    geo.bevel(legs, 0.002, segments=2)
    parts["desk_legs"] = legs

    # keyboard: an aluminium plate and a grid of low keycaps (a full-size layout, roughly)
    k = L["keyboard"]
    kx0, ky0 = k["x"] - k["w"] / 2, k["y"] - k["d"] / 2
    plate = geo.box("desk_keyboard", kx0, kx0 + k["w"], ky0, ky0 + k["d"], top_z, top_z + 0.010,
                    material=alu, **kw)
    geo.bevel(plate, 0.003, segments=3)
    pitch, cap, z0 = 0.0186, 0.0158, top_z + 0.010
    rows = 6
    caps = []
    for r in range(rows):
        ry = ky0 + k["d"] - 0.012 - (r + 0.5) * (k["d"] - 0.02) / rows     # row 0 at the back
        cx = kx0 + 0.010
        main_cols = 15
        for c in range(main_cols):
            w = cap
            if r == 5 and 3 <= c < 9:           # space bar spans six keys
                if c == 3:
                    w = pitch * 6 - (pitch - cap)
                else:
                    continue
            caps.append((cx + c * pitch, cx + c * pitch + w, ry - cap / 2, ry + cap / 2, z0, z0 + 0.006))
        nav0 = cx + main_cols * pitch + 0.008
        for c in range(3):                      # navigation block and arrows
            if r in (1, 2) or (r == 5) or (r == 4 and c == 1):
                caps.append((nav0 + c * pitch, nav0 + c * pitch + cap, ry - cap / 2, ry + cap / 2, z0, z0 + 0.006))
        num0 = nav0 + 3 * pitch + 0.008
        for c in range(4):                      # numeric pad
            if r >= 1 and num0 + c * pitch + cap <= kx0 + k["w"] - 0.006:
                caps.append((num0 + c * pitch, num0 + c * pitch + cap, ry - cap / 2, ry + cap / 2, z0, z0 + 0.006))
    keys = geo.boxes("desk_keyboard_keys", caps, material=keycap, **kw)
    geo.bevel(keys, 0.0012, segments=2)
    parts["desk_keyboard"] = plate             # the keycaps stay their own part (own bevel)
    parts["desk_keyboard_keys"] = keys

    # mouse: a flattened ellipsoid, cut flat underneath
    m = L["mouse"]
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.5)
    for v in bm.verts:
        v.co.x *= m["w"]
        v.co.y *= m["d"]
        v.co.z = max(0.0, v.co.z) * 2 * m["h"] + (0.002 if v.co.z <= 0 else 0.0)
        v.co.y += 0.012 * (v.co.z / m["h"])       # the hump sits toward the back
        v.co += __import__("mathutils").Vector((m["x"], m["y"], top_z))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    parts["desk_mouse"] = geo.from_bmesh("desk_mouse", bm, material=mouse_m, **kw)
    return root, parts
