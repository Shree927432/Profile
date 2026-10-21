# blender/

The scripts that build the room. The scripts are the source; `.blend` files and test
GLBs go to `blender/out/`, which git ignores.

    lib/constants.py     paths, note names, colours, and every piano dimension (PIANO)
    lib/piano_layout.py  key positions, cheek and console curves, fallboard, lid, sheet
                         (plain Python: the 2D sheet and the 3D builder both use it)
    lib/names.py         name checks against scene/objects/MESHES.md
    lib/geo.py           boxes, extruded profiles, lofts, cylinders, bevels, joins, tints,
                         screen planes
    lib/materials.py     procedural materials (lacquer, walnut, ivory, felt, brass, oak, wall)
    design/              2D design sheets drawn from the same constants
    props/               one script per prop: props/obj_piano.py
    tests/               test scenes with renders and exports: tests/piano_quality.py
    out/                 .blend files, GLBs, clip frames (git ignores it)

## Piano design sheet (2D, no Blender)

    python3 blender/design/piano_design_sheet.py

Writes `video-local/footage/2026-10-22-piano-quality-test/piano-design-sheet.{html,png}`.
Change a number in `lib/constants.py` and rerun; the 3D builder reads the same numbers.

## Piano in 3D: the quality test (2026-10-22)

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/tests/piano_quality.py

Blender opens with its window (the owner can watch; add `-b` after `Blender` to run
headless), builds `obj_piano` from `props/obj_piano.py` in a corner of the room with
blue-hour light and one warm lamp, saves `out/piano-quality.blend`, renders five stills
with Cycles on the Metal GPU (hero, keys close-up, lid open, clay, wireframe), exports
`out/obj_piano-rich.glb` and `out/obj_piano-lite.glb` (no bevels on keys and hammers),
renders the 13 s build clip in EEVEE (wireframe, clay, lit; FFmpeg crossfades them),
deletes the clip frames and quits. Takes about 45 minutes on the M2 Pro.

Outputs land in `video-local/footage/2026-10-22-piano-quality-test/` with a
`piano-quality-report.json` (build time, render times, GLB sizes and triangle counts).

Options after `--`: a stage (`build`, `stills`, `export`, `clip`; the last three open
the saved .blend) and `--quick` (half size, few samples, a handful of clip frames, no
MP4) for checking changes in about half a minute:

    .../Blender -b --factory-startup --python blender/tests/piano_quality.py -- all --quick

Layout rules for every prop script: build in the prop's own frame under its `obj_*`
root, names and pivots from scene/objects/MESHES.md, dimensions from `lib/constants.py`,
the layout maths shared with the 2D sheet in `lib/piano_layout.py`. Static parts stay
separate in the .blend (the clip builds them one by one); `export_prep()` joins copies
of them into `piano_static` for the GLB and removes the join afterwards.
