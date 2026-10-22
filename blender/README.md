# blender/

The scripts that build the room. The scripts are the source; `.blend` files and test
GLBs go to `blender/out/`, which git ignores.

    build.py             THE ROOM: builds everything from scratch, checks names, saves
                         out/room.blend, exports scene/assets/room.glb (see below)
    lib/constants.py     paths, note names, colours, every piano dimension (PIANO), the room
                         (ROOM, WINDOW, DOOR, LAYOUT, WALL_GUITARS, HERO)
    lib/run.py           the windowed, timer-driven run pattern (drive, render_to, log), render setup,
                         GLB stats
    lib/looks.py         lights (lt_*), the sky plane, the dawn and night looks, clay and wireframe,
                         cameras with a look-at
    lib/piano_layout.py  key positions, cheek and console curves, fallboard, lid, sheet
                         (plain Python: the 2D sheet and the 3D builder both use it)
    lib/names.py         name checks against scene/objects/MESHES.md
    lib/geo.py           boxes, extruded profiles, lofts, cylinders, bevels, joins, tints,
                         screen planes
    lib/materials.py     procedural materials (lacquer, walnut, ivory, felt, chrome, oak, wall)
    lib/piano_ornament.py the tribal ornament: stroke engine, motifs, emblems, placements,
                         the silver-mask rasteriser and the UV mapper (sheet and model share it)
    design/              2D design sheets drawn from the same constants
    props/               one script per prop: obj_piano.py, set_room.py, set_desk.py, obj_monitor.py;
                         footprints.py holds the named stand-ins for every root not modelled yet
    video/               footage scripts and their timing files (room_shell.py,
                         timing_room_shell.json)
    tests/               test scenes with renders and exports: tests/piano_quality.py
    out/                 .blend files, GLBs, clip frames (git ignores it)

## Room plan sheet (2D, no Blender)

    python3 blender/design/room_plan_sheet.py

Writes `video-local/footage/2026-10-22-room-plan/room-plan-sheet.{html,png}` from the
ROOM, LAYOUT and HERO blocks in `lib/constants.py`, and prints a clearance check.

## Room plan v2 sheet (proposal, not approved)

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/design/room_plan_v2_blockout.py
    python3 blender/design/room_plan_v2_sheet.py

Both read `lib/plan_v2.py` only (nothing in build.py reads it). Output in
`video-local/footage/2026-10-23-room-plan-v2/`.

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

Options after `--`: a stage (`build`, `stills`, `export`, `clip`, or several joined with
commas such as `build,stills,export`; anything without `build` opens the saved .blend)
and `--quick` (half size, few samples, a handful of clip frames, no
MP4) for checking changes in about half a minute:

    .../Blender -b --factory-startup --python blender/tests/piano_quality.py -- all --quick

## Piano with the tribal ornament (2026-10-22, second run)

Same command. `props/obj_piano.py` now rasterises the approved silver strokes
(`lib/piano_ornament.py`, the geometry the 2D sheet draws) into two mask images in
`out/` (`piano_tribal_front.png` 4096x1024 for the fields, fallboard, cheeks, consoles
and bench apron; `piano_tribal_lid.png` 2048x96 for the lid's front edge), maps the
UVs of those parts onto them and mixes brushed silver into the lacquer by the mask.
Hardware is chrome; the white keys get silver fronts by vertex colour. Outputs carry
`-tribal` in their names (`piano-hero-tribal.png`, `piano-build-tribal.mp4`,
`piano-quality-report-tribal.json`), plus `piano-fallboard-tribal.png` (the emblem
straight on) and `piano-hero-ivory-fronts-tribal.png` (key fronts in ivory, for the
owner to compare).

Layout rules for every prop script: build in the prop's own frame under its `obj_*`
root, names and pivots from scene/objects/MESHES.md, dimensions from `lib/constants.py`,
the layout maths shared with the 2D sheet in `lib/piano_layout.py`. Static parts stay
separate in the .blend (the clip builds them one by one); `export_prep()` joins copies
of them into `piano_static` for the GLB and removes the join afterwards.

## The room (Phase 4 Step 1, 2026-10-22): one rebuild command

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/build.py

About 3 s. Blender opens with its window (add `-b` after `Blender` for headless; add `-- build`
or `-- export` for one stage, `--stay` to keep the window open). It builds `set_room`,
`set_desk`, `obj_monitor` (with the TOP test texture on `monitor_screen`), the approved
`obj_piano`, and named footprints for every other root on the room plan; checks the names
against `scene/objects/MESHES.md`; saves `out/room.blend`; then exports
`scene/assets/room.glb`: each root's static parts joined into `<word>_static`, bevels of 2 mm
or less and all footprint bevels off, procedural colours flattened to their mean (the bake
replaces both later), the piano as a black stand-in box (its web export is an open question),
and checks the GLB (names, `room_view`, a textured one-primitive screen). Report:
`out/room-build-report.json`.

The site loads it only behind a flag: `/?room&glb` (and `&uvtest` to keep the TOP texture).

## Room shell footage

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/video/room_shell.py

Opens `out/room.blend`, renders three Cycles stills from the hero camera, keys the build from
`video/timing_room_shell.json` (bars and beats on the placeholder Presto grid; put the MIDI
beat map's bar times in `grid.bars` and rerun), renders it from five cameras in the storm look
and one dawn drift, encodes each to MP4 and deletes its frames. About two hours at
about 2 s a frame; the owner stopped it after the hero clip (2026-10-22): per step only
light captures now, the full shoot once at the end.
`-- --test` renders a handful of half-size frames in a few seconds to check light and framing;
`-- storm --cams=hero` renders one clip. Output and a NOTE in
`video-local/footage/2026-10-22-room-shell/`.

## guitar_02, the Woodstock Strat (Phase 4, 2026-10-23)

    /Applications/Blender.app/Contents/MacOS/Blender --factory-startup --python blender/tests/guitar_02_quality.py

`props/guitar_02.py` builds the exact replica from `lib/guitar_specs.py` GUITAR_02 and the
geometry functions of the approved 2D blueprint (`design/guitar_02_blueprint.py`: outlines,
neck width, string lines, posts, pickups, the hook contact), so the sheet and the model share
every number. Parts are built in the spec's millimetres and mapped into the guitar's frame
(origin at the hook contact, MESHES.md). The headstock is r3, the small style the owner chose,
traced from the owner's photo; the body outline is r2, corrected against a perspective-rectified
frontal photo (see video-local/footage/2026-10-23-guitar-02/NOTE.md). The .blend keeps fine-grained `guitar_02_part_*`
meshes (the build preview lands them one group at a time) and one `guitar_02_strings`;
`export_rich()` joins the parts into `guitar_02_body` for renders, `export_lite()` builds the
web model (about 6.7k triangles plus 312 for the strings), packs its UVs and bakes its colours,
AO, roughness and metal from the same procedural materials into `out/guitar_02_atlas.jpg`
(1024) and `out/guitar_02_orm.jpg` (512), one material.

The test (stages `build,stills,export,preview` by default; `room` renders the guitar in the
room from `out/room.blend`) hangs it on a plain wall with the blue-hour light and one warm
lamp, renders seven Cycles stills, exports `out/guitar_02-rich.glb` and `out/guitar_02-lite.glb`,
and renders a 7 s EEVEE build preview. Outputs go to `video-local/footage/2026-10-23-guitar-02/`.
`build.py` builds the same guitar onto its hanger (`guitars_hook_02`, static) under
`obj_guitars`, in place of its footprint, and puts the lite model in `room.glb`.
