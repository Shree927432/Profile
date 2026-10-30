# Mesh names: the list Blender and the room code both follow

Drafted 2026-10-21 for Phase 4, updated the same day with the owner's answers,
the widened premise (the room tells the evolution of music through its
instruments), the guitar rack and the DJ controller; see "Resolved 2026-10-21" at
the end. A row in docs/05-decisions.md points here.

The code may rely on a name only if it is in this file. Anything not listed is free
for the Blender scripts to rename, join or delete. Change a listed name only with a
decision row, because room code finds meshes by name (CONTRACT.md).

## 0. The room as built from plan v3 (2026-10-31, blender/build_v3.py)

This section is the list the GLB carries now. Where sections 2 to 6 (written for the v1
room) differ, this one wins; they stay for the rules and the pivots they describe.
Names marked (Blender) exist in the .blend and the component scripts only: the export
joins them into their root's `<word>_static`, so code must not look for them.

Roots: `set_room`, `set_city`, `obj_window`, `obj_light`, `obj_plant`, `set_rug`,
`set_desk`, `set_chair`, `set_camera`, `set_keylights`, `set_wall`, `set_laptop`,
`set_plants`, `obj_monitor`, `obj_rig`, `obj_mic`, `obj_frames`, `obj_studio`,
`obj_piano`, `obj_guitars`. Each root's other meshes are one `<word>_static`
(`room_static`, `city_static`, `window_static`, `light_static`, `plant_static`,
`rug_static`, `desk_static`, `cam_static`, `keylights_static`, `wall_static`,
`laptop_static`, `plants_static`, `monitor_static`, `rig_static`, `mic_static`,
`studio_static`, `piano_static`, `guitars_static`; the chair's is `chair_static`,
under `chair_swivel`).

| Root | Code-facing names in the GLB |
|---|---|
| `set_room` | camera anchors (empties, position and look-at): `room_view`, `room_view_target` (HERO_V3, the AI lab as the owner's photo, vfov 54, portrait 66); `camera_intro`, `camera_intro_target` (INTRO, out of the window, vfov 50); `camera_about`, `camera_about_target` (ABOUT, the music side, vfov 50); `camera_phone`, `camera_phone_target` (PHONE_V3, vfov 60). Field of view is not in the GLB; plan v3 and the code hold it |
| `obj_monitor` | `monitor_body`, `monitor_screen` (the Studio Display 27, 16:10, 53.8 x 33.6 cm, screen rules), `monitor_static` (arm, collar, brand) |
| `obj_rig` | `rig_display` (the G8 34 body), `rig_screen` (on the 1800R arc, screen rules), `rig_case`, `rig_case_glass`, `rig_fans` (all case-fan light rings, one emissive mesh, for the pulse), `rig_fan_01`..`_08` (rotors: 01-03 side, 04-05 rear, 06-08 bottom; origin at the hub, +Z is the air's direction), `rig_glow_strips`, `rig_gpu_root` (empty) with `rig_gpu`, `rig_gpu_fan_01`..`_02`, `rig_gpu_light`; `rig_static` (G8 stand, case frame parts, brands) |
| `obj_studio` | `studio_speaker_01`, `_02` (cabinets, front local -Y in Blender, origin bottom centre), `studio_speaker_0N_woofer` (+Z out of the cone, for the pulse); `apollo` (empty) with `apollo_knob` (the one big knob: volume) and `apollo_leds`; `dj_stand_root` > `dj_root` (empties) with `dj_jog_l`/`_r` (spin about local Z), `dj_pad_l_01`..`_08`, `dj_pad_r_01`..`_08` (back row 01-04), `dj_cue_l`/`_r`, `dj_play_l`/`_r`, `dj_tempo_l`/`_r` and `dj_fader_l`/`_r` (slide along Y), `dj_xfader` (slides along X), `dj_knob_hi`/`mid`/`low`/`trim`/`cfx` `_l`/`_r`, `dj_knob_master`, `dj_knob_browse`, `dj_knob_fx_depth`, `dj_knob_hp_level`, `dj_knob_hp_mix`, `dj_knob_mic`; `lightstick_root` (empty) with `lightstick_head` (own emissive material, for recolouring), `lightstick_shell`, `lightstick_handle`. (Blender: speaker poles and `_iso`, `apollo_body`, `apollo_button_1`..`_8`, `apollo_meter_window`, `dj_body`, `dj_mixer`, `dj_brand_*`, `dj_stand`, `lightstick_cradle`, the brands) |
| `obj_mic` | joint empties `mic_j_swivel`, `_shoulder`, `_elbow`, `_wrist`, `_wrist_yaw`, `_mount`, `_stem`, `_tilt` (the pose is baked; the arm meshes are in `mic_static`), `mic_body` (click target, under `mic_j_tilt`), `mic_led`. (Blender: `mic_arm_*`, `mic_stem`, `mic_yoke`, `mic_knobs`, the brands) |
| `obj_frames` | `frame_1`..`_3` (empties; GitHub, LinkedIn, X by content), each with `frame_N_border` and `frame_N_picture` (UV 0..1, top-left at (0,1), screen rules). One digit, as the wall-group build names them |
| `set_desk` | `desk_led`, `desk_drawers_01`..`_03` (empties) with `desk_drawers_NN_drawer_01`..`_05` (top to bottom; slide 0.40 m along local -Y); `keyboard` > `kb_plate` (empties) with one mesh per key `kb_key_<id>` (81 keys; move along the plate's local Z to type) and `kb_knob`; `mouse` (empty) with `mouse_wheel`; `deck` (empty, the Stream Deck, all static). (Blender: `desk_top`, `desk_pole`, `desk_screenbar`, `desk_screenbar_dial`, `desk_drawers_NN_carcass`, `_risers`, `kb_case`, the other mouse and deck parts, the felt mat, the brands) |
| `set_chair` | `chair_swivel` (empty at the cylinder axis; the site turns it), `chair_upper` (empty, seat height), `chair_static`. (Blender: `chair_seat`, `chair_back`, `chair_arm_l`/`_r`, `chair_mech`, `chair_base`, `chair_caster_NN`, `chair_brand`) |
| `set_camera`, `set_keylights` | `cam` (empty) with `cam_screen_lcd`; `keylight_1`, `_2` > `keylight_N_tilt` (empties) with `keylight_N_glow` |
| `set_wall` | `shelf_root`, `vine_pot_1_root`, `_2_root`, `pegboard_root` > `headphones_root`, `neon_root`, `nanoleaf_root` > `nanoleaf_0N_root` (empties); `neon`, `neon_glow`, `neon_halo` (words from content/room-brands.json), `pegboard_glow`, `nanoleaf_panel_01`..`_07` |
| `set_laptop` | `mstand_root` > `laptop_root` > `laptop_hinge` (empties; the lid is baked open at -110 about local X), `laptop_screen` (UV 0..1, top-left (0,1)) |
| `obj_piano` | as section 3 (keys, `piano_fallboard`, `piano_lid`, `piano_interior`, `piano_strings`, `piano_hammers`, `piano_sheet`, `piano_static` with the bench, `piano_view`, `piano_inside_view` and their targets) |
| `obj_guitars` | `guitar_01`..`_06` (empties) with `guitar_NN_body`; `guitar_02_strings`, `guitar_04_strings` (the two built guitars); 01, 03, 05, 06 are flat stand-in outlines without strings until they are built; `guitars_static` (stand-in hooks and rack) |
| `obj_window`, `obj_light`, `obj_plant`, `set_city`, `set_plants`, `set_rug` | stand-ins: `window_static` (frame, grill, ledge), `light_shade`, `light_static`, `plant_static` (sill plant), `city_static` (sky, ground and blocks, scaled to sit inside 30 m), `plants_static` (snake plant, small desk plant), `rug_static`. `window_sky`, `window_glass`, `window_beam`, `plant_pot`, `plant_soil`, `plant_leaf_NN` do not exist yet |

Replaced by the names above (the components' own names): `frame_NN` with two digits by
`frame_N`; `studio_dj_N_*` by `dj_*` (`l`/`r` for decks 1/2, more knobs, `dj_xfader`
for `studio_dj_crossfader`); `studio_lightstick_head`/`_handle` by `lightstick_head`/`_handle`;
`studio_knob_volume` by `apollo_knob` (`studio_knob_pan` has no knob on the Apollo);
`desk_keyboard`, `desk_mouse` by `keyboard`, `mouse`; `chair` by `chair_swivel`.
Needs a decision row in docs/05-decisions.md (the rule at the top of this file).

**Batched parts (2026-10-31, `scene/batch.js`).** At load (`?room&glb`) the code merges the keyboard's `kb_key_*`,
the piano's `piano_key_*`, the DJ's pads and play/cue buttons, knobs and fader caps, the desk's 15 drawers, the
three `frame_N_border`s, the `nanoleaf_panel_NN`s and the PC's case and GPU fans (`rig_fan_NN`, `rig_gpu_fan_NN`)
into one mesh per group (one draw call per material). The names above do not change: the original nodes stay in
the tree, hidden, so `getObjectByName` still finds them and gives each part's pivot. To move or light a part, use
the batch: `ctx.root.userData.batches.<id>` (`kb_keys`, `piano_keys`, `dj_pads`, `dj_knobs`, `dj_faders`,
`desk_drawers`, `frame_borders`, `nanoleaf_panels`, `rig_fans`; a group with fewer than two parts is not made).
Its `.userData` has `setOffset(name, x, y, z)`, `setOffsetLocal(name, x, y, z)` (part axes, e.g. a drawer along
-Y), `setAngle(name, rad)` (about the part's local +Z through its pivot: fans, knobs), `setGlow(name, r, g, b)`,
`parts[name]` (index, pivot, axis) and `partAtFace(hit)`. pick.js returns `part` for a hit on a batch, so an object
registers the batch mesh once (`interact.set(batch, {kind, owner})`) and gets the part name in `click`. Nothing
moves yet. Details in the header of `scene/batch.js`. In Blender, `build_v3.py` collapses the flat materials of each
`<root>_static` (and of `rig_case`, `rig_gpu`, the fans, `mic_body`) into palette materials: a swatch texture, UVs
on the swatch, roughness and metallic in a second texture, emission in a third. Do not drive those meshes' colours.

Not one material yet (they load in three.js as a group of meshes under the name):
`apollo_leds`, `desk_led`, `mic_body`, `rig_case`, `rig_case_glass`, `rig_display`,
`rig_fan_NN`, `rig_gpu`, `rig_gpu_fan_NN`, and the DJ's jogs, cues, plays, tempos, faders,
crossfader and knobs. Fix in the component scripts before code drives them.

## 1. Conventions

**Characters.** Lower-case ASCII, digits, underscore. Nothing else. Max 63 characters
(Blender's limit). three.js strips `. : / [ ]` and turns spaces into `_`, so a
Blender auto-name like `guitar_01.001` arrives as `guitar_01001`. Blender also renames
silently on a clash, so every script checks `obj.name == wanted` after naming.

**Shape of a name.** `<object>_<part>`, e.g. `piano_lid`, `studio_speaker_01_woofer`. Parts
start with the object's word (singular). Repeats get two digits from `01`:
`guitar_01`. Numbering runs left to right as seen from the home view (`room_view`),
then top to bottom. Code counts repeats by name (`guitar_01`, `guitar_02`, ... until
one is missing); it never hard-codes how many there are. Two exceptions, stated in
their sections: the guitars number by timeline (wall, then rack), and the DJ
controller's decks are `1` and `2`, one digit, because there are always two.

**Piano keys.** `piano_key_<note><octave>`, scientific pitch, middle C is `c4`.
Sharps only, written `s`: `cs ds fs gs as`. Never flats. Full range `piano_key_a0`
to `piano_key_c8`. The code turns the name into a MIDI number, so no note table.

**Roots.** Every object has one empty at the top of its tree:
`obj_<object>` for the nine interactive objects, `set_<thing>` for static scenery.
All its parts are children. Code finds the object by its root; the video script
builds the room root by root; bake and look scripts toggle a whole root.
Each root also has a Blender collection of the same name for organising (collections
are not exported).

**Empty vs mesh.**
- A part that moves alone and is one mesh: a mesh, origin at its pivot (`piano_key_*`, `piano_fallboard`).
- A part that moves with several meshes: an empty at the pivot, meshes as children (`guitar_01`, `frame_01`).
- Camera anchors are empties (`*_view`, `*_view_target`): a position and a look-at point, no rotation to get wrong.
- A mesh the code touches has exactly one material. With two, three.js loads it as a group, and `.geometry` / `.material` do not exist.

**Rotation signs.** Right-hand rule about the part's local axis. About +X, a
positive angle moves the front (+Z) down; a negative angle lifts it. About +Y, a
positive angle turns counter-clockwise seen from above. Tables below say which.

**Static vs interactive.** Everything listed in the tables below is interactive or
an anchor. Everything else is static: baked, never touched by code. In the Blender
file static parts may be fine-grained (`piano_pedal_01`, `bed_pillow_02`) for the
video's build and four states. At export the script joins each root's static meshes
into one `<root word>_static` (`obj_guitars` gives `guitars_static`; a group if it
has several materials), to cut draw calls.
Moving parts are modelled and baked in their rest pose, except where a table says
a part is baked open because it is only ever seen open.

**Blender-only prefixes, never exported:** `lt_` lights, `video_` video cameras and
paths, `still_` review cameras, `bake_` geometry that only exists for the bake (the
front wall, the door). The GLB contains only `obj_*`, `set_*` and their children.

**Mesh data and materials.** Mesh data is named `<object name>_mesh`
(`shared_<thing>_mesh` when several objects share it), never the same as an object.
three.js de-duplicates node and mesh names together and would add `_1` to a clash.
Materials: `mat_<thing>`.

**Units and axes.**
- Metres. Scene unit scale 1.0. Scale applied (1, 1, 1) on everything exported.
  (No guitar is mirrored any more: `guitar_02` is the real right-handed guitar, restrung; see its row.) A mirrored part, if one is ever needed, is mirrored in its geometry and applied, normals
  recalculated; never a negative scale on an exported object.
- Blender is Z up. Export as GLB with the default "+Y Up". In three.js that gives y up.
- The room faces the same way as the placeholder: **back wall (window, desk,
  monitor) at Blender +Y = three.js −Z. The viewer stands at Blender −Y = three.js
  +Z**, looking at it (Blender's Front view, numpad 1). Left wall (bed, bookshelf,
  frames) at −X, right wall (guitars, panels, piano) at +X in both.
- Origin on the floor at the room's centre. Floor top at height 0.
- Each object is modelled in its own frame facing Blender −Y (three.js +Z), its
  right at +X, then placed and turned by its root. Parts keep identity rotation
  relative to the root; a fixed tilt (the monitor leaning back, a speaker toed in)
  goes on the part's rotation, never into its geometry. So for every moving part, in three.js terms local to its
  object: **+X to the object's right, +Y up, +Z out of its front.**
- The monitor must face straight out from the back wall (yaw 0, a back tilt up
  to about 10° is fine). The orbit code starts the camera at world +Z of the screen.

**Screens** (`monitor_screen`, `piano_sheet`, `frame_NN_picture`, `window_sky`):
2D canvases painted by code. Each is one mesh, one material, a flat rectangle.
- As three.js loads it: the plane spans local X (width) and Y (height), faces local
  +Z, UVs 0..1 left to right and **bottom to top**. The code reads size from the
  geometry's bounding box and the facing from local +Z. Same as the placeholder.
- In Blender that means: the plane spans local X and Z, faces local −Y (any tilt
  on the object's rotation, the geometry stays flat in X and Z), and its UVs
  are written **upside down** (V = 0 on the top edge, 1 on the bottom), because the
  glTF exporter stores V as 1 − V. One helper in the Blender scripts writes screen
  UVs; nobody edits them by hand.
- Not yet tested (no Blender here). The first GLB export must show a test pattern
  with "TOP" and an arrow on the monitor, upright, before anything else is built.

**Export settings that keep the names:** GLB, +Y Up, apply modifiers, no cameras,
no punctual lights, no custom properties. Since 2026-10-31 (blender/build_v3.py): Draco
geometry and WebP textures; the page decodes Draco with three.js's own DRACOLoader and its
glTF decoder (from the installed three package, no new dependency).

## 2. Roots and build order

The storm section of the video (docs/10-video-plan.md) builds the room root by
root, one root or group per accented chord pair.

| Root | Object | Video build order (storm) |
|---|---|---|
| `set_room` | floor, walls, ceiling, skirting | 1, wireframe shell |
| `obj_window` | window | 1, with the shell (a dark frame) |
| `obj_light` | ceiling light and switch | 1, with the shell |
| `set_desk`, `set_chair` | desk and chair | 2 |
| `obj_monitor` | desk monitor | 3 |
| `obj_studio` | studio desk: speakers, DJ controller, audio interface, lightstick | 4: the speakers left and right of the monitor, then the DJ controller and the interface; the controller's pads light on the next accents, the lightstick lands last |
| `obj_mic` | mic on its arm | 5 |
| `set_bookshelf`, `obj_frames` | bookshelf, three picture frames | 6 |
| `set_bed`, `set_nightstand`, `set_rug` | bed, nightstand, rug | 7 |
| `set_panels`, `obj_guitars` | acoustic panels, guitar wall and floor rack | 8: the hooks, then `guitar_01` to `guitar_03` onto them, one per accent, left to right; then the rack lands beside the desk and `guitar_04` to `guitar_06` drop into it, one per accent, left to right. The timeline builds from jazz to now |
| `obj_piano` | upright piano and bench | 9, last. Fallboard open, top lid closed; the keys play the Presto |
| `obj_plant` | plant on the sill | dawn section, catches the first light |

## 3. The nine objects

### `obj_piano`: upright piano

Both covers open: the key cover (fallboard) for playing, the top lid to look inside
at the strings and hammers. Both rest closed, as in the default bake. The piano
plays public-domain Baroque, Classical and Romantic pieces with the keys moving,
and free play of keys and chords; which pieces is content, not names.

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `piano_key_a0` ... `piano_key_c8` | 88 keys, 52 white, 36 black | click target, plays the note, key dips; pieces play them. Hidden while the fallboard is closed | on the hinge line at the key's back end, centred on its width. Press = positive rotation about local +X by a few degrees (front goes down) |
| `piano_fallboard` | the key cover | click target: opens or closes. Playing opens it first | on its hinge line where it folds into the case. Open = negative rotation about local +X (lifts up and back); angle set in code |
| `piano_lid` | top lid | click target: opens or closes; the camera moves to `piano_inside_view` | on the hinge along the back top edge. Open = negative rotation about local +X, front edge up; angle set in code |
| `piano_interior` | inside of the case: iron plate, pin block, tuning pins, dampers, action rail | hidden while the lid is closed | — |
| `piano_strings` | all strings as one mesh, about 220, copper-wound in the bass | hidden while the lid is closed | — |
| `piano_hammers` | all 88 hammers as one mesh, at rest | hidden while the lid is closed; static in v1 (below) | — |
| `piano_sheet` | open music on the music rest | screen: About (`content/about.md`) | screen rules. Two A4 pages open, aspect about 1.41 : 1 |
| `piano_static` | case, music rest, pedals, bench | click target: "the piano", starts the close-up | — |
| `piano_view`, `piano_view_target` | keys close-up | camera moves here; video close-up | empties, keys and sheet in frame |
| `piano_inside_view`, `piano_inside_view_target` | looking down into the open top | camera moves here when the lid opens | empties, strings and hammers in frame |

Bake: the keys, `piano_interior`, `piano_strings` and `piano_hammers` are only
seen with their cover open, so the bake script opens both covers for them. The
fallboard and lid get their outer faces baked closed and their inner faces baked
open (two passes into one texture, done by the bake script). Without this the
keys and the inside come out black.

**Hammers: one static mesh.** One per key would add 88 draw calls in the close-up
on top of the 88 keys, about 190 in all, past what a mid-range phone holds at
60 fps. One mesh costs 1 draw call and about 5k triangles. From above, an upright's
hammers move a few millimetres; at phone size that is not visible. If the owner
wants them moving after seeing the close-up, the export can carry a per-vertex key
index and a small shader swings each hammer, still 1 draw call, no name change.
Hiding the keys under the closed fallboard and the inside under the closed lid
takes 91 meshes out of the room view.

### `obj_guitars`: the guitar wall and the floor rack (the evolution of music)

Six guitars as a timeline from jazz to now: `guitar_01` to `guitar_03` hang on
hooks on the right wall, `guitar_04` to `guitar_06` stand in a floor rack beside the
desk, near a studio monitor. The timeline reads the wall left to right, then the
rack left to right, and the numbering follows it. Style only: no logos, brand names or
exact trademarked graphics (no initials on `guitar_03`'s pickguard, no text on
`guitar_05`'s tape). Headstocks get our own outline per guitar, close in
proportion but never a trace, because headstock shapes are the most-protected part
of a guitar's look. The era and player below are notes for the Blender scripts and
the sound; the era text on the site comes from content, never from the name.

| Guitar | Where | Era (note) | After (note) | Body shape (Blender script key) | Look |
|---|---|---|---|---|---|
| `guitar_01` | wall | Blues, 1950s | B.B. King | `semi_hollow_double_cut` (ES-355 style) | "Lucille": black semi-hollow, f-holes absent as on Lucille, bound body, two humbuckers, gold hardware, stop tailpiece. Exact replica from its own blueprint (to come); no name on the headstock |
| `guitar_02` | wall | Rock, 1960s | Jimi Hendrix | `offset_double_cut` (Strat), exact replica, not mirrored | The 1968 Woodstock Stratocaster, exact from `blender/lib/guitar_specs.py` GUITAR_02 (blueprint approved 2026-10-23). A right-handed guitar turned 180 degrees in its own plane and restrung: on the wall it reads right-handed; strings reversed (thin E on the left), reversed saddle intonation, re-slotted nut, the string tree on A and low E, an extra strap button on the short horn. Lifted off the hook it turns a quarter so the controls show on top, his playing view. Aged a year (Woodstock 1969). The small headstock by the owner's choice (r3, traced from their photo), not the Woodstock guitar's large one. No logos, decals or serials |
| `guitar_03` | wall | Hard rock, 1970s | Jimmy Page | `double_neck` (EDS-1275 style) | Cherry double-neck, 12-string neck above a 6-string neck, two humbuckers per neck, the selector between them. Tall and wide: the wall hooks and spacing must be re-checked on the room plan. Exact replica from its own blueprint (to come); no logos |
| `guitar_04` | rack | Blues rock, 1980s | Stevie Ray Vaughan | `offset_double_cut` (Strat): guitar_02's builders and small headstock r3, its own body outline, pickups, bridge, jack and guard, measured (GUITAR_04, 2026-10-23) | "Number One", built 2026-10-23: three-colour sunburst worn to bare wood (traced wear map), rosewood board, clay dots, 1-ply black pickguard without the initials, gold left-handed bridge and hardware, cream aged pickup covers and knobs, the tremolo arm on the bass side resting across the lower bout. In rack slot 1; pivot at the body's lowest point at the 15 degree lean. No "Custom" sticker, no logos |
| `guitar_05` | rack | Metal, late 1980s | James Hetfield | `angular` (Explorer-style) | Off-white, black hardware, one plain tape strip with no text. The widest silhouette, about 47 cm |
| `guitar_06` | rack | Now, 2020s | Tim Henson | `modern_double_cut`: slim, 24 frets (TOD10 look) | Mauve. Ebony board with a simple tree inlay of our own drawing, two humbuckers, tremolo |

Parts, per guitar (`NN` = `01` ... `06`):

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `guitar_NN`, wall (`01`–`03`) | empty, the whole guitar | lifts off the hook, floats to the camera, goes back | at the hook's contact point (where the headstock rests). Lift = move along local +Z (off the wall) then up |
| `guitar_NN`, rack (`04`–`06`) | empty, the whole guitar | lifts out of the rack, floats to the camera, goes back to its slot | at the body's lowest point where it rests in the bottom cradle, on the body's centre plane. The lean and the rack's turn are on the empty's rotation; code keeps the rest rotation and returns to it, never hard-codes an angle. Lift, all in the guitar's own plane so it never touches a neighbour: rise 0.1 m while turning upright about the pivot (the neck leaves the top bar, the body clears the cradle), move away from the top bar until clear of the rack, about 0.4 m (the direction is opposite the way the headstock leaned at rest), then float to the camera |
| `guitar_NN_body` | body, neck, headstock, strap | click target: lift; when lifted, plays its lick | child of `guitar_NN` |
| `guitar_NN_strings` | all strings as one mesh | click target: strum; strings shimmer | child; origin at the strings' midpoint between nut and bridge |
| `guitars_static` | the wall hooks and the floor rack | — | — |

A lifted guitar shows its era card. The three wall guitars also show a project
each, by `order` (3 projects today); the rack guitars show era cards only. The card
is drawn by code beside the guitar; it has no mesh. Each guitar's lick is an original phrase
in its era's style, a sound file under 100 KB, never a copyrighted song.

**The rack** is a generic floor rack of our own, like the reference photo: a low
metal frame with a padded bottom cradle, a padded top bar and three slots. The
guitars stand like books on a shelf, faces along the rack's length, each leaning
about 15° in its own plane so its neck rests on the top bar around the 3rd to 5th
fret. The rack is turned so that from `room_view` the three fan out left to right,
each body partly over the next, every headstock and most of every face in view. It
is static: at export it joins the wall hooks in `guitars_static` (one draw call; the
code never touches either). In the Blender file they stay `guitars_hook_01` ...
`03` and `guitars_rack`, so the video can build them on their own accents.

Clearance, set by the Explorer-style `guitar_05` (about 47 cm wide, angular, the
widest body):
- Slot pitch about 15 cm, so bodies and hardware (up to about 7 cm with the
  Les Paul style's carved top and bridge) keep at least 5 cm of air.
- The top bar's height and set-back are chosen so the Explorer's neck, not its long
  upper horn, touches the bar, with at least 3 cm between horn and bar. The
  narrower bodies then clear it easily.
- The cradle is at least 10 cm off the floor, so the Explorer's low wing clears
  the floor at rest and while it turns upright.
- The side away from the top bar is open: no upright or brace crosses a slot, so
  the lift path is clear. The end frames are parallel to the guitars and never
  cross it.

### `obj_monitor`: desk monitor (posts screen)

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `monitor_body` | case and bezel. **Fixed name** | camera framing uses its size | — |
| `monitor_screen` | the screen. **Fixed name.** 16:10 | screen: posts (`content/posts`), click target, glide target | screen rules |
| `monitor_static` | stand and base | — | — |
| `monitor_view`, `monitor_view_target` | close-up anchors | reserved; today the code computes its own close-up from the screen | empties |

`monitor_glow` is made by code (the halo). Blender must not use the name.

### `obj_mic`: mic on its arm (email)

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `mic_body` | microphone and shock mount | click target: camera moves in, shows email | origin at the capsule centre |
| `mic_static` | arm and desk clamp | — | — |
| `mic_view`, `mic_view_target` | close-up anchors | camera moves here; video close-up | empties |

### `obj_frames`: picture frames (GitHub, LinkedIn, X)

Three frames, `NN` = `01` ... `03`. Which link each frame shows is set in content,
not by the name.

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `frame_NN` | empty, the whole frame | tilts forward, back on second click or Esc | on the frame's bottom edge, centred, at its back face (against the wall). Tilt = rotate about local +X, top comes forward |
| `frame_NN_border` | frame and glass | click target | child |
| `frame_NN_picture` | the picture | screen: painted from `content/links.json`, click target | screen rules, portrait 3 : 4 |

### `obj_studio`: the studio desk (electronic music)

Replaces `obj_speakers`. Everything is prefixed `studio_` because `monitor_*` is
the computer screen. The root sits on the desk top, centred under the monitor.
Speakers stand left and right of the monitor, toed in toward the chair (the toe-in
is on the cabinet's rotation). The DJ controller lies flat beside the keyboard on
the side away from the mic arm, the audio interface stands next to it and the
lightstick lies beside them. Controller and interface sit square to the desk edge,
so their parts keep identity rotation.

**The DJ controller** is a generic two-deck design of our own, after the reference
photo but not a copy: about 44 × 28 cm, matte charcoal, the two decks mirrored with
their tempo faders on the outer edges, a mixer strip in the middle. No brand, logo,
model name or printed words: anything written would be visible text, which belongs
in `content/` and is drawn by code. Shapes are fine (a moulded triangle on play);
words and numbers are not. No headphone, shift, sync or mode buttons: the code
would not drive them, so they are cut.

Deck `N` is `1` (left) or `2` (right), as seen by the player and from `room_view`.
Each deck owns its jog wheel, pads, play, cue and tempo fader, and in the mixer
strip its channel's EQ, filter and fader.

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `studio_dj_N_jog` | jog wheel. Its top carries a painted tick ring with one bright mark, so a turn shows | drag: nudges the deck while it plays, scratches while held; turns slowly while its deck plays (not with reduced motion) | on the wheel's axis at the centre of its top face. Spin = rotate about local +Y; clockwise from above (forward) is a negative angle |
| `studio_dj_N_pad_01` ... `studio_dj_N_pad_08` | 8 pads, 2 rows of 4, numbered left to right, top row (away from the player) first | click, tap or key: triggers its loop, hot cue or one-shot; lit while active; dips when hit | centre of the pad's top face. Hit = small move along local −Y. Light = code sets the emissive colour |
| `studio_dj_N_play` | play / pause | starts or stops deck N; lit while it plays | as the pads |
| `studio_dj_N_cue` | cue | jumps deck N back to its cue point and stops; lit while it waits there | as the pads |
| `studio_dj_N_tempo` | tempo fader cap | drag or arrow keys: deck N's speed | at the cap's centre where it meets the panel, the cap at the centre of travel. Slides along local Z, 0.06 m in all (±0.03); toward the player (+Z) is faster. Rest = centre = the track's own tempo |
| `studio_dj_N_eq_hi`, `studio_dj_N_eq_mid`, `studio_dj_N_eq_low` | EQ knobs of channel N, top to bottom | drag, scroll or arrow keys: cut or boost that band | knob rule (`studio_knob_pan`). 12 o'clock = flat |
| `studio_dj_N_filter` | filter knob, below the EQ | same input: left of centre low-pass, right of centre high-pass | knob rule. 12 o'clock = off |
| `studio_dj_N_fader` | channel fader cap | drag or arrow keys: channel N's level | as the tempo fader. Slides along local Z, 0.05 m in all (±0.025); away from the player (−Z) is louder. Code moves it to the starting level |
| `studio_dj_crossfader` | crossfader cap, bottom of the mixer | drag or arrow keys: blends the two decks | at the cap's centre where it meets the panel, at the centre of travel. Slides along local X, 0.04 m in all (±0.02); −X = deck 1 only, +X = deck 2 only, centre = both |
| `studio_knob_pan` | pan knob on the audio interface | drag, scroll or arrow keys: moves the sound between the two speakers | **Knob rule:** on the shaft axis where the knob meets the panel. Turn = rotate about local +Y; clockwise (to the right) is a negative angle. Rest = pointer at 12 o'clock (toward local −Z). Range ±135°. Here 12 o'clock = centre |
| `studio_knob_volume` | volume knob on the audio interface | drag, scroll or arrow keys: master volume | knob rule. Modelled at 12 o'clock; code turns it to the starting volume |
| `studio_speaker_01`, `studio_speaker_02` | cabinets with tweeter, left and right | click target: music stops or resumes | — |
| `studio_speaker_01_woofer`, `studio_speaker_02_woofer` | the cones, each a child of its cabinet | pulse with that side's level after pan (not with reduced motion) | at the cone's centre on the front face. Pulse = small move along local +Z |
| `studio_lightstick_head` | the glowing head | click target: glows, deck 2 plays the K-pop hook, the room light pulses | — |
| `studio_lightstick_handle` | the handle | click target, same as the head | — |
| `studio_static` | controller body (case, jog rings, mixer panel, fader slots), audio interface body, speaker stands, cables | click target: "the studio", camera moves to `studio_view` | — |
| `studio_view`, `studio_view_target` | close-up over the desk | camera moves here; controller, interface and lightstick in frame | empties |

Knob pointers and the jog's tick ring are painted in the part's own texture, so each
stays one mesh and one material. All pads and buttons share one material in
Blender; the code gives each its own copy when it lights it.

**The audio interface** is a small desktop box of our own, about 18 × 12 cm, with
the two knobs on its top and no text. Its body is static: in the Blender file it is
`studio_interface`, and the export joins it into `studio_static` with the
controller body. A separate `studio_interface_static` would cost a draw call and
break the one-static-mesh-per-root rule, and no code needs it.

Decks and pads, a suggestion for content (names do not depend on it): each deck
plays an original EDM track in one style, house, techno, trance, drum and bass and
so on; the list lives in content. Sounds stay under 100 KB each (CONTRACT.md), so a
"track" is an arrangement the code plays from short original loops, not one long
recording. Top row pads: four loops in the deck's style (drums, bass, chords,
lead), joining on the next bar. Bottom row: two hot cues into the track and two
one-shots. A pad with nothing in content stays dark.

Light and motion: pads and buttons light steady while active. Any beat flash stays
at or under three a second (quarter notes up to 180 bpm, never 16ths), the same
limit as the room pulse. With reduced motion there are no dips, the jogs do not
turn, and lights stay steady.

**Phones.** Framed whole on a portrait phone a pad is about 15 px wide, too small
to tap. The code frames one deck at a time from the bounds of all `studio_dj_1_*`
(or `studio_dj_2_*`) meshes plus the crossfader, and widens each pad's hit area to
its grid cell. No extra anchor or name. Every control also works from the keyboard.

**Draw calls.** The controller adds 35 meshes: 17 per deck (jog, 8 pads, play,
cue, tempo, 3 EQ knobs, filter, fader) and the crossfader; its body joins
`studio_static`. Against the 16 pads it replaces, the room view at rest goes from
about 82 to about 101 draw calls. Measure at the first export. If a mid-range phone
cannot hold 60 fps, the code batches at load, names unchanged:
- the 16 pads and 4 play and cue buttons into one mesh, with a per-vertex part
  index the code writes from the names, and uniform arrays for each part's light
  colour and press depth;
- the 10 knobs (8 on the controller, 2 on the interface) into one, with a pivot
  and an angle per knob;
- the 5 fader caps into one, with an offset per fader.

The two jogs stay separate. That takes the studio's 37 moving parts to 5 draw
calls and the room view to about 69. Picking reads the part index from the hit
face. The index is not exported from Blender: a custom attribute is one more thing
for the exporter to get wrong, and the names already carry it.

The lightstick loads its K-pop hook onto deck 2 and starts it (on deck 1's next bar
if deck 1 is playing): deck 2's play lights and its jog turns, so the controller
shows where the sound comes from. A second click stops deck 2.

Lightstick: a generic design of our own, e.g. a frosted faceted capsule on a short
white handle with one button. Not a globe, heart, hammer or candy-ball head, which
read as real groups' sticks; no text, no logo. The room pulse stays under three
flashes a second; with reduced motion the stick glows steady and the room does
not pulse.

`studio_lightstick_glow` (its halo) and the room pulse are made by code. Blender
must not use the name.

### `obj_light`: ceiling light (first Phase 5 object)

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `light_shade` | the dome diffuser | click target, glows when on | at its centre |
| `light_switch` | one rocker on the wall switchboard | click target, flips | on the rocker's axis, at its centre. Flip = rotate about local X. Rest = off (matches the dawn bake) |
| `light_static` | ceiling base, switchboard plate | — | — |

Suggest the switch on the left wall near the front corner, where the door is in
the photo, as a Pune-style modular switchboard with several rockers, only one of
which works.

### `obj_window`: window (Pune time and weather)

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `window_sky` | plane just outside the glass | screen: sky painted from Pune's real time and weather | screen rules, aspect of the opening |
| `window_glass` | the panes | transparent; rain drawn on it later | — |
| `window_beam` | soft light shaft from the window to the floor | additive, not baked. Hidden while the real sun is down (so at 5:40 a.m.); code fades it in by the sun's height | — |
| `window_static` | frame, sill, blind, curtains | — | — |

### `obj_plant`: plant on the sill

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `plant_pot` | pot | click target: water it | — |
| `plant_soil` | soil surface | click target; darkens when watered | — |
| `plant_leaf_01` ... `plant_leaf_12` | leaves, in growth order | the first N show; one more per return visit | at the point where the leaf meets the stem. Grow = scale from 0 at the origin; sway = small rotation there |
| `plant_static` | stem | — | — |

Twelve leaves suggested, about five showing on a first visit. More can be added in
Blender later with no code change, because the code counts them.

## 4. Static scenery

Names inside are working names for the Blender file; the export joins each root into
`<root word>_static` (`desk_static`, `bed_static`, ...). Code relies on none of them
except the home view anchors.

| Root | Contains (enough for the bake, not every bolt) |
|---|---|
| `set_room` | `room_floor`, `room_wall_back`, `room_wall_left`, `room_wall_right`, `room_ceiling`, `room_skirting`. Anchors kept by name: `room_view`, `room_view_target` (the home view). Bake only: `bake_wall_front`, `bake_door` |
| `set_desk` | `desk_top`, `desk_legs`, `desk_keyboard`, `desk_mouse` (the audio interface moved to `obj_studio`) |
| `set_chair` | `chair` |
| `set_bed` | `bed_frame`, `bed_mattress`, `bed_duvet`, `bed_pillow_01` ... `03`, `bed_throw` |
| `set_nightstand` | `nightstand`, `nightstand_lamp` (static, not a light in v1) |
| `set_bookshelf` | `bookshelf_case`, `bookshelf_books` (books as one generated mesh) |
| `set_rug` | `rug` |
| `set_panels` | `panels_guitar_wall` (behind the guitars), `panels_desk` (behind the desk) |

## 5. Lights and cameras

Blender only, never exported. The web gets light from the bake. The default bake
is 5:40 a.m. blue hour: cool light from the window, no sun, no beam. How the
ceiling light and the "real sun is up" look appear on the site (a second bake, or
a code tint plus `window_beam`) is settled in the bake step by measuring; the
overlay is the first try, because it adds no download. These names do not change
with it.

| Name | What | Used for |
|---|---|---|
| `lt_dawn_sky` | area light filling the window opening, deep blue, no warm tones | the default bake (blue hour), the video's dawn opening |
| `lt_sun` | low warm sun lamp through the window | never in the default bake. The video's sunrise; a "sun up" bake only if the bake step picks a bake over the overlay |
| `lt_ceiling` | light at the ceiling fixture | "light on" bake |
| `lt_monitor` | weak area light on the screen | night, video |
| `lt_night_sky` | dim cool area light in the window | video storm (night) |
| `lt_storm_flash` | bright area light outside the window, keyed to the accents | video storm |
| Collection `lights_dawn` | `lt_dawn_sky`, `lt_monitor` | the default bake |
| Collection `lights_lamp` | `lt_ceiling` | the "light on" look |
| Collection `lights_night` | `lt_night_sky`, `lt_storm_flash`, `lt_monitor` | video storm only |
| Collection `lights_sunrise` | `lt_dawn_sky` keyed from blue to gold, `lt_sun` rising | video dawn only, never baked for the site |
| `video_cam_hero`, `video_path_hero`, `video_cam_hero_target` | the fixed hero camera, its path curve, its look-at | the storm build, every lighting iteration |
| `video_cam_dawn`, `video_path_dawn`, `video_cam_dawn_target` | the slow drift from the bed to the window, settling on the monitor | the dawn section |
| `still_cam_home` | matches `room_view` | review stills, desktop |
| `still_cam_phone` | same place, portrait 390 × 844 framing | review stills, phone |
| `still_cam_turntable`, `still_turntable` | camera and the empty it circles | 120-frame turntables per prop |

Close-ups in the video use the exported anchors `piano_view`, `piano_inside_view`,
`mic_view`, `monitor_view`, `studio_view` and their `_target` empties, so the site
and the video frame the same shots.

Note: in Pune the sun rises between about 5:58 (June) and 7:10 (January), so at
5:40 a.m. there is never a direct sun beam, and in October it is still dark. The
default bake is that blue hour. The live window paints Pune's real sky; warm light
comes in only when the real sun is up. The full sunrise exists only in the video.

## 6. Counts

Names the code may rely on, under the nine roots:

| Root | Names |
|---|---|
| `obj_piano` | 99: 88 keys, 7 parts, 4 anchors |
| `obj_studio` | 46: 35 DJ controller parts, 2 interface knobs, 2 cabinets, 2 woofers, 2 lightstick parts, `studio_static`, 2 anchors |
| `obj_guitars` | 19: 6 guitars × 3, plus `guitars_static` (wall hooks and floor rack) |
| `obj_plant` | 15: 12 leaves, 3 parts |
| `obj_frames` | 9: 3 frames × 3 |
| `obj_monitor` | 5 |
| `obj_mic` | 4 |
| `obj_window` | 4 |
| `obj_light` | 3 |
| Total | 204 (88 of them keys) |

The DJ controller's 35: per deck a jog, 8 pads, play, cue, tempo, 3 EQ knobs, a
filter knob and a channel fader (17), twice, plus the crossfader.

With the 9 object roots, 8 scenery roots and their 8 static meshes, and the 2 home
view anchors, the GLB has about 231 nodes, about 193 of them meshes. In the room
view at rest the 88 keys, the 3 piano interior meshes and `window_beam` are hidden,
so about 101 meshes draw, or about 69 with the studio parts batched (see
`obj_studio`). The studio close-up draws about 50, the piano close-up with both
covers open about 100. Measure draw calls on a mid-range phone at the first export;
if the keys, pads, knobs or leaves cost too much, the code batches them at load
without any name changing.

## Resolved 2026-10-21

1. Guitars: six, a timeline from jazz (after Wes Montgomery) to now (after Tim Henson), style only. Where they hang and which carry projects: item 8.
2. Frames: three, for GitHub, LinkedIn and X.
3. Piano covers: both the fallboard and the top lid open; the open top shows strings and hammers.
4. Piano keys: all 88 separate, named and playable; the piano plays public-domain Baroque, Classical and Romantic pieces and free play.
5. Speakers: replaced by the studio desk `obj_studio` (stereo monitor speakers, a generic K-pop lightstick, and a console that item 9 turned into a DJ controller).
6. Light: 5:40 a.m. blue hour with no sunbeam by default; the window follows Pune's real time and weather; warm light only when the real sun is up; a full sunrise only in the video.
7. "Which guitars do you own": superseded; the wall is the evolution of music, not an inventory.
8. Guitars split, three and three. On hooks on the right wall: `guitar_01` Wes Montgomery archtop, `guitar_02` Hendrix white left-handed Strat-style, `guitar_03` Stevie Ray Vaughan worn sunburst; they carry the projects by `order`. In a floor rack beside the desk, near a studio monitor: `guitar_04` Slash flame-top single-cut, `guitar_05` Hetfield off-white Explorer-style, `guitar_06` Tim Henson mauve modern electric; era cards and licks only. The timeline reads wall, then rack. Closes "wall space for six guitars": three on the wall need about 1.5 m.
9. Studio desk: a generic two-deck DJ controller (`studio_dj_*`, no brand, logo or printed text) replaces the 4 × 4 pad console; the `studio_pad_NN` names are gone. Pan and volume keep their names on a small audio interface beside it. The lightstick's hook plays on deck 2.

## Open questions

1. **Which side of the desk the rack stands.**
   - A. On the side toward the guitar wall, between the desk and the right wall, by
     `studio_speaker_02`. All six guitars stay in one part of the room and the eye
     runs from the wall down into the rack. **Recommended.**
   - B. On the other side, by `studio_speaker_01`. Balances the room, but puts
     guitars on both sides of the desk and splits the timeline across the room.
   Stills of A and B from the Blender file before the rack is modelled. No name
   changes either way.

## Proposed names from the component builds

Adopted on 2026-10-31 by the plan v3 room rebuild: see section 0. The component reports in
`video-local/footage/2026-10-24-components/<name>/NOTE.md` still give origins and pivots.
