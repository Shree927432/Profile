# Mesh names: the list Blender and the room code both follow

Drafted 2026-10-21 for Phase 4, updated the same day with the owner's answers and
the widened premise (the room tells the evolution of music through its
instruments; see "Resolved 2026-10-21" at the end). Once approved, a row in
docs/05-decisions.md points here.

The code may rely on a name only if it is in this file. Anything not listed is free
for the Blender scripts to rename, join or delete. Change a listed name only with a
decision row, because room code finds meshes by name (CONTRACT.md).

## 1. Conventions

**Characters.** Lower-case ASCII, digits, underscore. Nothing else. Max 63 characters
(Blender's limit). three.js strips `. : / [ ]` and turns spaces into `_`, so a
Blender auto-name like `guitar_01.001` arrives as `guitar_01001`. Blender also renames
silently on a clash, so every script checks `obj.name == wanted` after naming.

**Shape of a name.** `<object>_<part>`, e.g. `piano_lid`, `studio_speaker_01_woofer`. Parts
start with the object's word (singular). Repeats get two digits from `01`:
`guitar_01`. Numbering runs left to right as seen from the home view (`room_view`),
then top to bottom. Code counts repeats by name (`guitar_01`, `guitar_02`, ... until
one is missing); it never hard-codes how many there are.

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
  A mirrored part (`guitar_02`) is mirrored in its geometry and applied, normals
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
no punctual lights, no custom properties. Draco or meshopt compression need a
decoder in the page, so that is a dependency question for the owner later.

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
| `obj_studio` | studio desk: speakers, console, lightstick | 4: the speakers left and right of the monitor, then the console; its pads flash on the next accents, the lightstick lands last |
| `obj_mic` | mic on its arm | 5 |
| `set_bookshelf`, `obj_frames` | bookshelf, three picture frames | 6 |
| `set_bed`, `set_nightstand`, `set_rug` | bed, nightstand, rug | 7 |
| `set_panels`, `obj_guitars` | acoustic panels, guitar wall | 8: six guitars, one per accent, left to right, so the timeline builds from jazz to now |
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

### `obj_guitars`: the guitar wall (the evolution of music, left to right)

Six guitars as a timeline from jazz to now. Style only: no logos, brand names or
exact trademarked graphics (no initials on `guitar_03`'s pickguard, no text on
`guitar_05`'s tape). Headstocks get our own outline per guitar, close in
proportion but never a trace, because headstock shapes are the most-protected part
of a guitar's look. The era and player below are notes for the Blender scripts and
the sound; the era text on the site comes from content, never from the name.

| Guitar | Era (note) | After (note) | Body shape (Blender script key) | Look |
|---|---|---|---|---|
| `guitar_01` | Jazz, 1950s–60s | Wes Montgomery | `archtop`: hollow, single cutaway, about 8 cm deep | L-5 CES style. Carved top in sunburst, f-holes, bound body, one neck pickup, floating bridge, gold tailpiece |
| `guitar_02` | Rock, 1960s | Jimi Hendrix | `offset_double_cut` (Strat-style), mirrored | White, maple neck and board, white pickguard. A right-handed guitar flipped and strung left-handed: build it right-handed, mirror the whole guitar on its width axis and apply, then reverse the string order across the neck. Tuners and controls end up on the other side, the bridge pickup slants the other way |
| `guitar_03` | Blues rock, 1980s | Stevie Ray Vaughan | `offset_double_cut` (Strat-style) | "Number One" look. Three-colour sunburst worn to bare wood on the forearm, belly and edges; black pickguard, no initials; rosewood board. The wear is in the texture, not the geometry |
| `guitar_04` | Hard rock, late 1980s | Slash | `single_cut_carved` (Les Paul style) | Flame-maple top in amber sunburst, cream binding, two humbuckers, amber knobs |
| `guitar_05` | Metal, late 1980s | James Hetfield | `angular` (Explorer-style) | Off-white, black hardware, one plain tape strip with no text. The widest silhouette, about 47 cm |
| `guitar_06` | Now, 2020s | Tim Henson | `modern_double_cut`: slim, 24 frets (TOD10 look) | Mauve. Ebony board with a simple tree inlay of our own drawing, two humbuckers, tremolo |

Parts, per guitar (`NN` = `01` ... `06`):

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `guitar_NN` | empty, the whole guitar | lifts off the hook, floats to the camera, goes back | at the hook's contact point (where the headstock rests). Lift = move along local +Z (off the wall) then up |
| `guitar_NN_body` | body, neck, headstock, strap | click target: lift; when lifted, plays its lick | child of `guitar_NN` |
| `guitar_NN_strings` | all strings as one mesh | click target: strum; strings shimmer | child; origin at the strings' midpoint between nut and bridge |
| `guitars_static` | the hooks, which stay on the wall | — | — |

A lifted guitar shows its era card and, by `order`, a project if there is one
(3 today, so `guitar_04` to `guitar_06` show era cards only). The card is drawn by
code beside the guitar; it has no mesh. Each guitar's lick is an original phrase
in its era's style, a sound file under 100 KB, never a copyrighted song.

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
is on the cabinet's rotation). The console sits beside the keyboard on the side
away from the mic arm, the lightstick lies on the desk next to it.

| Name | What | Code does | Pivot / origin |
|---|---|---|---|
| `studio_pad_01` ... `studio_pad_16` | 4 × 4 pads, numbered left to right, back row (nearest the wall) first | click or key: starts or stops its loop; lit while playing; dips when hit | centre of the pad's top face. Hit = small move along local −Y. Light = code sets the emissive colour |
| `studio_knob_pan` | pan knob | drag, scroll or arrow keys: moves the sound between the two speakers | on the shaft axis at the console surface. Turn = rotate about local +Y; clockwise (to the right) is a negative angle. Rest = pointer at 12 o'clock (toward local −Z) = centre. Range ±135° |
| `studio_knob_volume` | volume knob | drag, scroll or arrow keys: volume | same rule. Modelled at 12 o'clock; code turns it to the starting volume |
| `studio_speaker_01`, `studio_speaker_02` | cabinets with tweeter, left and right | click target: music stops or resumes | — |
| `studio_speaker_01_woofer`, `studio_speaker_02_woofer` | the cones, each a child of its cabinet | pulse with that side's level after pan (not with reduced motion) | at the cone's centre on the front face. Pulse = small move along local +Z |
| `studio_lightstick_head` | the glowing head | click target: glows, the console plays the K-pop hook, the room light pulses | — |
| `studio_lightstick_handle` | the handle | click target, same as the head | — |
| `studio_static` | console body, speaker stands, cables | click target: "the studio", camera moves to `studio_view` | — |
| `studio_view`, `studio_view_target` | close-up over the console | camera moves here; pads, knobs and lightstick in frame | empties |

Knob pointers are painted in the knob's own texture, so each knob stays one mesh
and one material.

Pads, a suggestion for content (names do not depend on it): columns are house,
techno, trance and K-pop; rows are drums, bass, chords, lead. Pads in one column
layer in sync; a pad in another column switches genre at the next bar. The
lightstick fires the whole K-pop column. All loops original, each under 100 KB.
A pad with no loop in content stays dark.

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
| `set_desk` | `desk_top`, `desk_legs`, `desk_keyboard`, `desk_mouse`, `desk_interface` (the audio interface) |
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
| `obj_guitars` | 19: 6 guitars × 3, plus `guitars_static` |
| `obj_studio` | 27: 16 pads, 2 knobs, 2 cabinets, 2 woofers, 2 lightstick parts, `studio_static`, 2 anchors |
| `obj_plant` | 15: 12 leaves, 3 parts |
| `obj_frames` | 9: 3 frames × 3 |
| `obj_monitor` | 5 |
| `obj_mic` | 4 |
| `obj_window` | 4 |
| `obj_light` | 3 |
| Total | 185 (88 of them keys) |

With the 9 object roots, 8 scenery roots and their 8 static meshes, and the 2 home
view anchors, the GLB has about 212 nodes, about 174 of them meshes. In the room
view at rest the 88 keys, the 3 piano interior meshes and `window_beam` are hidden,
so about 82 meshes draw. The piano close-up with both covers open draws about 100.
Measure draw calls on a mid-range phone at the first export; if the keys, pads or
leaves cost too much, the code can batch them at load without any name changing.

## Resolved 2026-10-21

1. Guitars: six, a timeline left to right from jazz (after Wes Montgomery) to now (after Tim Henson), style only; projects by `order`, so `guitar_04` to `guitar_06` show era cards only for now.
2. Frames: three, for GitHub, LinkedIn and X.
3. Piano covers: both the fallboard and the top lid open; the open top shows strings and hammers.
4. Piano keys: all 88 separate, named and playable; the piano plays public-domain Baroque, Classical and Romantic pieces and free play.
5. Speakers: replaced by the studio desk `obj_studio` (console with pads and two knobs, stereo monitor speakers, a generic K-pop lightstick).
6. Light: 5:40 a.m. blue hour with no sunbeam by default; the window follows Pune's real time and weather; warm light only when the real sun is up; a full sunrise only in the video.
7. "Which guitars do you own": superseded; the wall is the evolution of music, not an inventory.

## Open questions

1. **Wall space for six guitars.** In one straight row at about 50 cm centres they
   need about 3 m of the right wall, which also holds the piano, and the piano's top
   lid needs clear space above it to open.
   - A. A staggered row: hooks alternate high and low so each body sits beside a
     neighbour's neck, about 32 cm centres, about 2 m in all. Still reads left to
     right as a timeline; the piano keeps its place clear of the guitars.
     **Recommended.**
   - B. One straight row on the right wall; the piano moves to the back wall
     beside the window.
   - C. Two rows of three. Compact, but the timeline reads as two lines.
   Stills of A and B from the Blender file before the wall is modelled.
