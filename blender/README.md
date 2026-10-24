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

## Component pipeline (the toolkit, 2026-10-24)

Every Blender run is headless: always `-b`. The window opens only when the owner asks to watch.

    B="/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python"

Start a component by copying `tools/component_template.py` to `components/<name>.py` (it runs as it is,
on an example). The steps, in order:

1. **References.** Official photos and drawings in `docs/moodboard/local/...` with a SOURCES.md that gives
   the official sizes. Each number in the component is tagged OFFICIAL, MEASURED or EST.
2. **Lens correction** (`lib/refs.py`, plain Python or Blender): for a real camera photo, mark a few
   edges that are straight in the world, `refs.edge_points()` snaps them, and `refs.fit_lens()` fits one
   or two radial terms (or a homography and the lens terms from points with known positions, as for
   Number One). Use the fit only when it is `significant`. `refs.undistort_image()` writes
   `<photo>-lens.<ext>` plus a .json next to the original (or in `out_dir`) and never touches the original.
   Maker renders and drawings need none. `refs.rectify()` maps a photographed flat face to a square-on,
   true-scale image from four or more points. `refs.mm_per_px_extent()` and `mm_per_px_between()` give
   the scale from an official size.
3. **Backdrops** (`lib/backdrops.py`): `backdrops.add(refs.ref_record(...))` puts the photo behind the model
   at true scale for front, back, right, left or top (a textured plane, or `kind="empty"` for a viewport-only
   image empty). `backdrops.ortho_camera()` frames it pixel for pixel. Model straight onto it.
4. **Outline check, about 15 minutes in** (`tools/outline_check.py`): build `rough=True` (the silhouettes
   from `lib/parts.py`, official outer sizes only). It renders front, side, top and three-quarter in quick
   EEVEE and scores the photo views. One review sheet comes out of it. The gate is 0.96. **The owner or the
   coordinator approves the proportions before any detail.**

       $B blender/tools/outline_check.py -- blender/components/<name>.py
       $B blender/components/<name>.py -- outline

5. **Detail** with `lib/parts.py`: rounded_box (separate radii), rounded_panel, knob (plain, knurled, with
   an indicator, with a skirt), push_button, port (usb_a, usb_c, hdmi, displayport, jack_35, jack_635,
   xlr_combo, iec, dc_barrel; "decal" or a real "cut" with port_cutter + cut), screw (phillips, hex,
   hexbolt, flat), grille (real holes with clean shared topology, or a texture tile with alpha for lite),
   driver (+ driver_cutter), tube, pole, desk_clamp, vesa_plate (75/100), rubber_feet, cable (Bezier).
   They are all in metres, named, wound outward, `lite=True` for the web, and `facing` / `at` to place
   them. The sheet is `video-local/footage/2026-10-24-toolkit/parts-sheet.png`.
6. **The every-angle compare test** (`lib/compare.py`): a view per reference photo, with a `placed` camera
   (true scale and position from the photo's ref record; the strictest), `ortho` (box-aligned) or `fit`
   (a perspective camera searched to the photo, for the makers' perspective renders). It passes at 0.98
   IoU, or the view carries an `explain` and shows as EXPLAINED. It writes `<name>-compare.json` and
   `.md` (angle, IoU, pass) and `<name>-compare-<view>.png` (photo, render, 50/50, outlines).
   Changed 2026-10-24 (from the screens builder's workarounds, now in the toolkit): an `alpha` photo mask
   is no longer hole-filled unless the view says `fill=True` (filling closed real gaps such as panel to
   stand); threshold masks still fill by default. `fit` also tries a sideways lens shift and keeps it only
   when the full-size score is higher. A new `free` camera (or `fit` with `yaws`) searches distance,
   height, sideways shift, the model's turn and tilt, framed on the largest side, for turned shots. On the
   demo: g8-front 0.9894 (same), g8-back 0.9893 (+0.0001), g8-top 0.8268 (+0.017, the unfilled mask),
   sd-front 0.9993 (same); Samsung's turned g8-04 went from 0.42 (`fit`) to 0.947 (`free`).
7. **The photo-vs-model sheet:** `<name>-photo-vs-model.jpg`, every view stacked with the photo on the left,
   the render on the right and a title per row, top view included. It comes out of the same run.
8. **Export:** rich and lite GLBs (template stage `export`; the baked lite atlas is
   `components/screens_render.py export_lite`).

       $B blender/components/<name>.py                    build, stills, compare, export
       $B blender/components/<name>.py -- compare         one stage (opens the saved .blend)

**Render queue** (`lib/renderqueue.py`): only one Cycles render runs on this Mac at a time, across
processes. It is a file lock in `out/render-queue.lock`, and the OS frees it if Blender dies. Wrap every
Cycles render or bake in `with renderqueue.slot("label"):`, or `dt = yield from
renderqueue.render_to(path, "label")` in run.drive() jobs. While waiting it logs who holds the GPU,
once a minute. `python3 blender/lib/renderqueue.py` says who holds it now. EEVEE and Workbench do
not need it. The toolkit renders in EEVEE and Workbench by default; `--cycles` in the template opts in.

Proof on the approved screens (nothing in `components/` changed):

    $B blender/tools/demo_screens_toolkit.py              parts, outline, compare, backdrop, lens: about 2 min

Output and numbers are in `video-local/footage/2026-10-24-toolkit/NOTE.md`.
