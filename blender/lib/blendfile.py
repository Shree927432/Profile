"""Save a .blend with every external image packed inside it (owner, 2026-10-31).

Textures such as the keyboard legend atlases are written next to the .blend and linked by a relative
path. A copy of the .blend opened anywhere else lost them, and Blender showed missing-texture magenta
(the pink keycaps). Packing first makes every .blend self-contained, so copies and moves are safe.
"""
import bpy


def pack_and_save(filepath, **kwargs):
    """Pack all images that have a file on disk, then save to filepath. Missing files are reported, not fatal."""
    missing = []
    for im in bpy.data.images:
        if im.source in {"FILE", "SEQUENCE", "TILED"} and not im.packed_file and im.filepath:
            try:
                im.pack()
            except RuntimeError:
                missing.append(im.name)
    if missing:
        print(f"blendfile: could not pack {len(missing)} image(s), source not found: {', '.join(missing)}")
    bpy.ops.wm.save_as_mainfile(filepath=filepath, **kwargs)
