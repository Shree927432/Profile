# blender/

The scripts that build the room. The scripts are the source; `.blend` files and test
GLBs go to `blender/out/`, which git ignores.

    lib/constants.py   paths, note names, colours, and every piano dimension (PIANO)
    lib/names.py       name checks against scene/objects/MESHES.md
    lib/geo.py         boxes, extruded profiles, lofts, cylinders, bevels, screen planes
    lib/materials.py   procedural materials (lacquer, walnut, ivory, felt, brass, oak, wall)
    design/            2D design sheets drawn from the same constants

## Piano design sheet (2D, no Blender)

    python3 blender/design/piano_design_sheet.py

Writes `video-local/footage/2026-10-22-piano-quality-test/piano-design-sheet.{html,png}`.
Change a number in `lib/constants.py` and rerun; the 3D builder reads the same numbers.

## Piano in 3D

Not built yet: waiting for the owner to approve the design sheet. Next:
`props/obj_piano.py` (the object) and `tests/piano_quality.py` (test scene, renders,
GLB), run with Blender's window open so the owner can watch:

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/tests/piano_quality.py
