"""Name checks against scene/objects/MESHES.md.

MESHES.md is the list the room code relies on. These helpers read it, expand the
ranges it writes in shorthand (`piano_key_a0` ... `piano_key_c8`, `guitar_NN`), and
check a built object tree against it before export.
"""
import re
import bpy

from . import constants as C

NAME_RE = re.compile(r"^[a-z0-9_]{1,63}$")
TOKEN_RE = re.compile(r"`([a-z0-9_]+)`")


def set_name(obj, wanted, data=True):
    """Name an object (and its data `<name>_mesh`) and fail loudly if Blender renamed it."""
    assert NAME_RE.match(wanted), f"bad name {wanted!r}"
    obj.name = wanted
    assert obj.name == wanted, f"Blender renamed {wanted!r} to {obj.name!r} (name clash)"
    if data and obj.data is not None and obj.type == "MESH":
        obj.data.name = wanted + "_mesh"
    return obj


def _section(md, root):
    """Text of the `### `<root>`` section."""
    start = md.index(f"### `{root}`")
    nxt = md.find("\n### ", start + 4)
    return md[start: nxt if nxt != -1 else len(md)]


def _note_range(first, last):
    def midi(n):
        m = re.match(r"piano_key_([a-z]+)(\d)$", n)
        return C.NOTE_NAMES.index(m.group(1)) + 12 * (int(m.group(2)) + 1)
    return [C.key_name(m) for m in range(midi(first), midi(last) + 1)]


def expected(root, nn_count=None):
    """Names MESHES.md lists for one object root (first column of its parts tables)."""
    with open(C.MESHES_MD, encoding="utf-8") as f:
        md = f.read()
    out = []
    for line in _section(md, root).splitlines():
        if not line.startswith("| `"):
            continue
        cell = line.split("|")[1]
        toks = TOKEN_RE.findall(cell)
        if "..." in cell and len(toks) == 2 and toks[0].startswith("piano_key_"):
            out += _note_range(*toks)
            continue
        for t in toks:
            if "NN" in t:
                if nn_count is None:
                    raise ValueError(f"{t}: pass nn_count to expand it")
                out += [t.replace("NN", f"{i:02d}") for i in range(1, nn_count + 1)]
            else:
                out.append(t)
    return out


def descendants(obj):
    out = []
    for c in obj.children:
        out.append(c)
        out += descendants(c)
    return out


def check_export(root_obj, multi_material_ok=()):
    """Check the tree under `root_obj` as it will be exported. Returns a report dict.

    Fails on: a listed name missing, a name with characters three.js would change,
    a mesh data name equal to an object name, a code-touched mesh with more than one
    material (except names in `multi_material_ok`, e.g. the joined `*_static`).
    Unlisted extra names are reported, not fatal (MESHES.md allows them).
    """
    want = expected(root_obj.name)
    tree = descendants(root_obj)
    have = {o.name for o in tree}
    problems = []
    missing = [n for n in want if n not in have]
    if missing:
        problems.append(f"missing {len(missing)}: {missing[:8]}")
    for o in [root_obj] + tree:
        if not NAME_RE.match(o.name):
            problems.append(f"bad name {o.name!r}")
        if o.type == "MESH":
            if o.data.name == o.name:
                problems.append(f"mesh data named like its object: {o.name}")
            if o.name in want and o.name not in multi_material_ok and len(o.data.materials) != 1:
                problems.append(f"{o.name} has {len(o.data.materials)} materials, needs 1")
    extra = sorted(have - set(want))
    if problems:
        raise AssertionError(f"{root_obj.name}: " + "; ".join(problems))
    return {"listed": len(want), "found": len(want) - len(missing), "extra": extra}
