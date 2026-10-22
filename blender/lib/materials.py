"""Material helpers. Procedural only (no image files), so scripts stay the source.

Every material is a Principled BSDF with a few nodes in front. Names follow
MESHES.md: `mat_<thing>`. The bake step later turns these into texture atlases for
the web; the GLB here carries only base values.
"""
import math
import bpy

from . import constants as C


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def rgba(h):
    return (*srgb(h), 1.0)


def _new(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    return m, nt, b


def _set(b, **v):
    keys = {"base": "Base Color", "rough": "Roughness", "metal": "Metallic",
            "coat": "Coat Weight", "coat_rough": "Coat Roughness", "coat_ior": "Coat IOR",
            "sheen": "Sheen Weight", "sheen_rough": "Sheen Roughness", "sheen_tint": "Sheen Tint",
            "sss": "Subsurface Weight", "sss_scale": "Subsurface Scale", "spec": "Specular IOR Level",
            "emit": "Emission Color", "emit_strength": "Emission Strength"}
    for k, val in v.items():
        sock = b.inputs[keys[k]]
        if isinstance(val, str):
            val = rgba(val)
        sock.default_value = val


def principled(name, **v):
    m, nt, b = _new(name)
    _set(b, **v)
    m.diffuse_color = b.inputs["Base Color"].default_value[:]  # solid view colour
    return m


def _coords(nt, scale=(1, 1, 1), rot=(0, 0, 0), space="Object"):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    mp.inputs["Rotation"].default_value = rot
    nt.links.new(tc.outputs[space], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def _noise(nt, vec, scale, detail=4, rough=0.5, distortion=0.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    n.inputs["Distortion"].default_value = distortion
    nt.links.new(vec, n.inputs["Vector"])
    return n.outputs["Fac"]


def _ramp(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    for i, (pos, col) in enumerate(stops):
        e = el[i] if i < len(el) else el.new(pos)
        e.position = pos
        e.color = rgba(col) if isinstance(col, str) else col
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def _bump(nt, b, height, strength, distance=0.001, socket="Normal"):
    bm = nt.nodes.new("ShaderNodeBump")
    bm.inputs["Strength"].default_value = strength
    bm.inputs["Distance"].default_value = distance
    nt.links.new(height, bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], b.inputs[socket])
    return bm


def _math(nt, op, a, bval, cval=None):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    nt.links.new(a, m.inputs[0])
    m.inputs[1].default_value = bval
    if cval is not None:
        m.inputs[2].default_value = cval
    return m.outputs[0]


def lacquer_black(name, image=None, silver_rough=0.35):
    """Polished ebony lacquer: near-black base under a mirror clear coat, a faint
    orange-peel ripple in the coat so reflections are not CG-perfect. With `image`
    (RGB lacquer or silver, alpha the silver mask) the mask drives the base colour,
    metallic and roughness: a brushed silver inlay flat under the same coat. Wired
    so the glTF exporter carries it (base colour texture, alpha into Metallic)."""
    m, nt, b = _new(name)
    _set(b, base=C.COL["lacquer_black"], rough=0.32, coat=1.0, coat_rough=0.03,
         coat_ior=1.52, spec=0.5)
    if image is not None:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = image
        t.interpolation = "Cubic"
        t.location = (-500, 0)
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(t.outputs["Alpha"], b.inputs["Metallic"])
        nt.links.new(_math(nt, "MULTIPLY_ADD", t.outputs["Alpha"], silver_rough - 0.32, 0.32), b.inputs["Roughness"])
    peel = _noise(nt, _coords(nt), 900, detail=2)
    _bump(nt, b, peel, 0.02, 0.0002, socket="Coat Normal")
    m.diffuse_color = (0.02, 0.02, 0.02, 1)
    return m


def walnut(name, grain="Z", gloss=True):
    """Dark walnut veneer under a clear coat. `grain` is the local axis the grain runs
    along. Rings from a distorted wave give the figure, stretched noise the pores."""
    m, nt, b = _new(name)
    rot = {"Z": (0, 0, 0), "X": (0, math.radians(90), 0), "Y": (math.radians(90), 0, 0)}[grain]
    v = _coords(nt, rot=rot)
    # stretch along the grain (Z after the rotation)
    sep = nt.nodes.new("ShaderNodeMapping")
    sep.inputs["Scale"].default_value = (1, 1, 0.06)
    nt.links.new(v, sep.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.inputs["Scale"].default_value = 2.2
    wave.inputs["Distortion"].default_value = 9.0
    wave.inputs["Detail"].default_value = 3.0
    wave.inputs["Detail Scale"].default_value = 1.5
    nt.links.new(sep.outputs[0], wave.inputs["Vector"])
    pores_v = nt.nodes.new("ShaderNodeMapping")
    pores_v.inputs["Scale"].default_value = (260, 260, 3)
    nt.links.new(v, pores_v.inputs["Vector"])
    pores = _noise(nt, pores_v.outputs[0], 1.0, detail=6, rough=0.6)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.35
    nt.links.new(wave.outputs["Fac"], mix.inputs["A"])
    nt.links.new(pores, mix.inputs["B"])
    col = _ramp(nt, mix.outputs["Result"], [(0.25, C.COL["walnut_dark"]), (0.55, C.COL["walnut_mid"]),
                                            (0.85, C.COL["walnut_light"])])
    nt.links.new(col, b.inputs["Base Color"])
    _bump(nt, b, pores, 0.08, 0.0003)
    _set(b, rough=0.38, spec=0.5)
    if gloss:
        _set(b, coat=1.0, coat_rough=0.06, coat_ior=1.5)
    m.diffuse_color = rgba(C.COL["walnut_mid"])
    return m


def ivory(name, fronts=False):
    """Ivory-white key tops (acrylic, as on modern pianos): warm, slightly translucent.
    With `fronts`, the colour attribute `tint` (rgb silver, alpha 1 on the key's
    front face, geo.tint_faces) turns that face into brushed silver; the Value node
    `key_silver` (1 or 0) switches the silver off for a comparison render."""
    m, nt, b = _new(name)
    _set(b, base=C.COL["ivory"], rough=0.3, sss=0.12, sss_scale=0.004, coat=0.35, coat_rough=0.12)
    tint = _noise(nt, _coords(nt), 40, detail=3)
    col = _ramp(nt, tint, [(0.35, "#e6dcc6"), (0.65, "#efe8d8")])
    if fronts:
        a = nt.nodes.new("ShaderNodeVertexColor")
        a.layer_name = "tint"
        sw = nt.nodes.new("ShaderNodeValue")
        sw.name = sw.label = "key_silver"
        sw.outputs[0].default_value = 1.0
        fac = nt.nodes.new("ShaderNodeMath")
        fac.operation = "MULTIPLY"
        nt.links.new(a.outputs["Alpha"], fac.inputs[0])
        nt.links.new(sw.outputs[0], fac.inputs[1])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        nt.links.new(fac.outputs[0], mix.inputs["Factor"])
        nt.links.new(col, mix.inputs[6])
        nt.links.new(a.outputs["Color"], mix.inputs[7])
        col = mix.outputs[2]
        nt.links.new(fac.outputs[0], b.inputs["Metallic"])
        nt.links.new(_math(nt, "MULTIPLY_ADD", fac.outputs[0], 0.05, 0.3), b.inputs["Roughness"])
    nt.links.new(col, b.inputs["Base Color"])
    m.diffuse_color = rgba(C.COL["ivory"])
    return m


def ebony(name):
    m = principled(name, base=C.COL["ebony"], rough=0.36, coat=0.3, coat_rough=0.18)
    return m


def felt(name, colour):
    m, nt, b = _new(name)
    _set(b, base=colour, rough=1.0, sheen=0.8, sheen_rough=0.35, spec=0.2)
    fuzz = _noise(nt, _coords(nt), 2500, detail=2)
    _bump(nt, b, fuzz, 0.25, 0.0002)
    m.diffuse_color = rgba(colour)
    return m


def brass(name):
    m, nt, b = _new(name)
    _set(b, base=C.COL["brass"], metal=1.0, rough=0.24)
    r = _noise(nt, _coords(nt), 180, detail=3)
    rr = _ramp(nt, r, [(0.3, (0.16, 0.16, 0.16, 1)), (0.7, (0.32, 0.32, 0.32, 1))])
    nt.links.new(rr, b.inputs["Roughness"])
    m.diffuse_color = rgba(C.COL["brass"])
    return m


def chrome(name, colour="#d4d7dc", rough=0.06):
    """Polished chrome hardware: the sheet's #d4d7dc, metallic, near-mirror."""
    m = principled(name, base=colour, metal=1.0, rough=rough)
    return m


def tinted(name, rough=0.35, coat=0.0):
    """One material for a mesh made of several kinds of parts (MESHES.md: a mesh the
    code touches has exactly one material). Colour comes from the colour attribute
    `tint` (geo.tint writes it); its alpha is the metallic value."""
    m, nt, b = _new(name)
    a = nt.nodes.new("ShaderNodeVertexColor")   # the glTF exporter carries this one as COLOR_0
    a.layer_name = "tint"
    nt.links.new(a.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(a.outputs["Alpha"], b.inputs["Metallic"])
    _set(b, rough=rough, coat=coat, coat_rough=0.1)
    m.diffuse_color = (0.5, 0.4, 0.2, 1)
    return m


def oak_floor(name, plank_w=0.14, plank_l=1.25):
    """Warm oak planks running along Y, satin finish."""
    m, nt, b = _new(name)
    v = _coords(nt, rot=(0, 0, math.radians(90)), space="Object")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5
    brick.offset_frequency = 1
    brick.squash = 1.0
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.0012
    brick.inputs["Mortar Smooth"].default_value = 0.2
    brick.inputs["Bias"].default_value = 0.0
    brick.inputs["Brick Width"].default_value = plank_l
    brick.inputs["Row Height"].default_value = plank_w
    nt.links.new(v, brick.inputs["Vector"])
    gv = nt.nodes.new("ShaderNodeMapping")
    gv.inputs["Scale"].default_value = (1.2, 70, 70)
    nt.links.new(v, gv.inputs["Vector"])
    grain = _noise(nt, gv.outputs[0], 1.0, detail=8, rough=0.62, distortion=0.4)
    c1 = _ramp(nt, grain, [(0.3, C.COL["oak_dark"]), (0.7, C.COL["oak_light"])])
    c2 = _ramp(nt, grain, [(0.3, "#4c301b"), (0.7, "#7a5030")])
    nt.links.new(c1, brick.inputs["Color1"])
    nt.links.new(c2, brick.inputs["Color2"])
    brick.inputs["Mortar"].default_value = rgba("#1c120a")
    nt.links.new(brick.outputs["Color"], b.inputs["Base Color"])
    seam = _math(nt, "SUBTRACT", brick.outputs["Fac"], 0.0)
    h = nt.nodes.new("ShaderNodeMath")
    h.operation = "ADD"
    nt.links.new(_math(nt, "MULTIPLY", grain, 0.15), h.inputs[0])
    nt.links.new(_math(nt, "MULTIPLY", seam, -1.0), h.inputs[1])
    _bump(nt, b, h.outputs[0], 0.35, 0.0008)
    rr = _ramp(nt, grain, [(0.3, (0.32, 0.32, 0.32, 1)), (0.7, (0.48, 0.48, 0.48, 1))])
    nt.links.new(rr, b.inputs["Roughness"])
    _set(b, coat=0.35, coat_rough=0.22, spec=0.5)
    m.diffuse_color = rgba(C.COL["oak_light"])
    return m


def wall_paint(name, colour=None):
    m, nt, b = _new(name)
    _set(b, base=colour or C.COL["wall"], rough=0.85, spec=0.35)
    roller = _noise(nt, _coords(nt), 120, detail=4)
    _bump(nt, b, roller, 0.06, 0.0005)
    m.diffuse_color = rgba(colour or C.COL["wall"])
    return m


def image_material(name, image, rough=0.85):
    m, nt, b = _new(name)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = image
    t.interpolation = "Cubic"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    _set(b, rough=rough, spec=0.3, sheen=0.3)
    m.diffuse_color = (0.9, 0.88, 0.82, 1)
    return m


def emission(name, colour, strength):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = rgba(colour)
    e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def clay(name="mat_look_clay"):
    return principled(name, base="#b7b2a9", rough=0.62, spec=0.4)


def stone(name, colour="#8a8478"):
    """Kota-style limestone (the grey-blue stone of Pune sills and thresholds): honed,
    fine speckle, faint cloud."""
    m, nt, b = _new(name)
    cloud = _noise(nt, _coords(nt), 6, detail=3)
    speck = _noise(nt, _coords(nt), 300, detail=2)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.3
    nt.links.new(cloud, mix.inputs["A"])
    nt.links.new(speck, mix.inputs["B"])
    col = _ramp(nt, mix.outputs["Result"], [(0.35, "#6f6d66"), (0.65, "#9b968b")])
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Base Color"].default_value = rgba(colour)
    _set(b, rough=0.45, spec=0.5)
    m.diffuse_color = rgba(colour)
    return m


def fabric(name, colour, rough=0.9):
    """Woven fabric: matte with sheen and a fine weave bump."""
    m, nt, b = _new(name)
    _set(b, base=colour, rough=rough, sheen=0.5, sheen_rough=0.4, spec=0.25)
    weave = _noise(nt, _coords(nt), 1400, detail=2)
    _bump(nt, b, weave, 0.15, 0.0003)
    m.diffuse_color = rgba(colour)
    return m


def screen_image(name, image, strength=1.0):
    """A screen: the image as base colour and as emission, so it reads in the dark.
    The glTF exporter carries both (baseColorTexture, emissiveTexture)."""
    m, nt, b = _new(name)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.name = "screen_image"
    t.image = image
    t.interpolation = "Linear"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    _set(b, rough=0.18, spec=0.5, emit_strength=strength)
    m.diffuse_color = (0.1, 0.15, 0.25, 1)
    return m
