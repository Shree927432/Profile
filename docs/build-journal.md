# Build journal

Raw material for the making-of blog post (docs/drafts/making-of-post.md) and the
video (docs/10-video-plan.md). Facts, numbers, what the owner said, what broke.
Newest at the bottom. Agents: add a dated entry after any work that changes the
site or the room. Keep each entry short. No polishing; the post does that.

## 2026-10-15 to 16: looking at Felix's site, then planning

- Opened felixrieseberg.com's source to see how much was real. All of it: the
  calculator calculates, the PC runs BASIC. Plain Three.js, a room Claude built by
  writing Blender scripts, one file per object. He reviewed screenshots on his
  phone, about 60 rounds.
- Decided to build my own, with my own story. No copying his desk or his VHS tapes.
- Wrote the docs before any code: vision, architecture (content, static site,
  optional room, each layer works without the one above), roadmap in seven
  phases, an append-only decisions log, an object contract, a model guide.
- Three agents: builder (Sonnet) for mechanics, designer (Opus) for taste,
  quick (Haiku) for small edits.

## 2026-10-16: Phase 1, the plain site

- Astro, zero client JavaScript, system fonts only.
- Lighthouse on mobile: 100 for performance, accessibility, best practices, SEO.
- All words live in `content/`. Pages never hard-code text.

## 2026-10-17: hand-over

- Changed Claude accounts. Wrote `handover/START-HERE.md` and a resume prompt so
  any new session can pick up from the files alone. It worked: every later
  session started from that prompt.
- First real post: "Nobody Starts From Zero", about 5,400 words.

## 2026-10-19: real content, live, the premise, Phase 2

- About page, home intro, three real projects. Example files deleted.
- Live on Cloudflare Pages. Two fixes on the live build: Node pinned to 22.22,
  and a 404 page (without it, Cloudflare served the home page for every unknown
  address).
- Premise: three sketches (a practice room at 5:40 a.m., a green room on a
  Saturday night, a studio control room at 2 a.m.). Picked none of them. Picked
  my own room instead: a bedroom that became a music studio, wall of guitars,
  upright piano, the desk where the models get trained. 5:40 a.m., first light.
  Nine objects.
- Phase 2: the posts list as a desk-monitor screen, built by the builder agent as
  the first module under the object contract. On my phone the text was too small;
  fixed the same day with a titles-only phone layout.
- Phase 3 started, then paused at my request.

## 2026-10-21: Phase 3, the room shell

- Resumed from the hand-over prompt. The builder agent did four steps, each
  reviewed and tested before the next: boot checks and fallback, the scene
  (placeholder desk and monitor), picking and input, the quality ladder.
- Review caught things the builder could not see: the in-app browser scales
  emulated sizes and breaks WebGL screenshots; a hidden preview runs about one
  frame per second.
- Size: the room's own code is about 15 KB compressed. Three.js is about 440 KB.
- 120 fps on an M2 Pro Mac. Merged and live at `/?room`. The home page stayed
  exactly the same for everyone else.

## 2026-10-21: the phone test

- What I said: "if I increase the quality the fps drops, if I increase the
  smoothness the quality drops, zoom in and out is not smooth, clicking on the
  post isn't satisfying."
- Causes: at Full the phone drew 4x the pixels into a multisampled buffer and ran
  about ten bloom passes every frame, even when nothing moved. The orbit library
  applied zoom in jumps, and the range was only 20% each way. A tap jumped
  straight to the post with no feedback.
- Fixes: no post-processing, a cheap fake glow, draw only when something changes
  (about 2 draws a second when idle), eased zoom with pinch. Then the designer
  agent (Opus) built the glide: the row lights, 120 ms later the camera glides in
  for 950 ms, the page fades over the last 300 ms, the post opens. Prefetched.
  Back returns to the normal view.
- Review found that slow frames would stretch the glide (20 s in a hidden
  preview). Fixed with a timer so the post always opens on time.
- Tested on my phone from a preview link. "It feels right." Live the same day.

## 2026-10-21: the first video, and a better plan

- A 59 s timelapse of Phases 0 to 3, rebuilt from 36 commits in a headless
  browser. My reaction: too much like a PowerPoint.
- Studied Felix's 92 s making-of: full screen, no cards, moving process footage
  (Blender turntables, clay renders), fast cuts, one small overlay in his
  premise's style.
- New plan: the room builds itself in a storm to the third movement of the
  Moonlight Sonata, one second of silence, then dawn to the first movement.
  My own playing. Footage saved at every Phase 4 step.

## 2026-10-21: Phase 4 started, the mesh name list

- First Phase 4 step, before any Blender: `scene/objects/MESHES.md`, the one list of
  names the Blender scripts and the room code both follow. Nine object roots
  (`obj_piano` ...), eight scenery roots (`set_bed` ...), 153 names under the nine
  objects, 88 of them piano keys (`piano_key_a0` to `piano_key_c8`, sharps as `cs`).
  `monitor_body` and `monitor_screen` kept from the placeholder.
- Found while writing it, by reasoning, not yet tested: Blender's glTF exporter
  flips the V of every UV. The posts screen would load upside down unless the
  Blender script writes screen UVs upside down. The first export must show a "TOP"
  test pattern on the monitor before anything else is built. Also: three.js strips
  dots from names, so a Blender duplicate `guitar_01.001` would arrive as
  `guitar_01001`.
- The photo says things the sketch does not: 4 instruments on the wall (two
  acoustics, an electric and what looks like a bass) for 3 projects; black foam
  wedge panels behind the guitars and a checkered panel behind the desk, not the
  sketch's slats; two small frames and sheet music on the piano; the bed's
  headboard, bookshelf and three framed records are on the window wall (the left
  of the photo is the open door). The sketch and the vision put them on the left
  wall; we follow the vision.
- Pune's sun rises between about 5:58 (June) and 7:10 (January). At 5:40 a.m. there
  is never a sunbeam, and in late October it is still dark. The sketch's sun disc
  and floor beam are the chosen look, not the real sky.
- Four questions for the owner before the list is final: how many guitars, how many
  frames, which piano lid moves, all 88 keys or a range.

## 2026-10-21: the room becomes the evolution of music

- The owner widened the premise: "basically we are covering evolution of music
  through these combinations of instruments and their music."
- Guitar wall, six guitars, left to right: Wes Montgomery, Jimi Hendrix, Stevie Ray
  Vaughan, Slash, James Hetfield, Tim Henson (on electric, "use electric guitar").
  First I drew five sketched silhouettes; the owner asked to see real images, so a
  reference sheet was built from Wikimedia Commons photos (plus a retailer and a press
  photo for Henson's Ibanez TOD10, which Commons does not have). Approved as shown.
- Piano: all 88 keys, "lid should be open, I should be able to play keys and chord
  and songs", and the top lid opens to show the strings inside.
- Studio desk: a console with studio monitors for EDM and electronic music, a pan
  knob for stereo ("pan music left and right that will give stereo feel"), and a K-pop
  lightstick. Counted as one object, so the room stays at 9 of the 10 allowed.
- Copyright shaped the plan: the owner first asked for famous songs on each guitar
  (Polyphia for Henson). Those need licenses, so the guitars play original licks in
  each era's style; the piano plays real public-domain pieces.
- Light: 5:40 a.m. stays, as blue pre-dawn. Pune's sun never rises before about 5:58.

## 2026-10-21: three on the wall, three on a rack, and a DJ controller

- Six guitars in one row needed about 3 m of the wall the piano is on. The owner
  answered with two photos and one line: "we can put 3 guitar on wall and 3 on rack,
  and can we also dj console to desk, so it can play edm music."
- Wall: Wes Montgomery, Hendrix, Stevie Ray Vaughan, holding the projects. Floor rack
  beside the desk: Slash, Hetfield, Tim Henson.
- The 4x4 pad console became a generic two-deck DJ controller; the pan knob moved to a
  small audio interface next to it. Still one object, still 9 in the room.

## 2026-10-21, end of day: Blender installed, paused before modelling

- Blender 5.2.2 installed with Homebrew; it runs headless and sees the M2 Pro GPU.
- The first modelling step (room shell, desk, monitor, a "TOP" test pattern to prove
  the screen loads upright in the website) was briefed to the designer agent. The
  owner said "can stop for now"; it was stopped before any file was written.
- Everything needed to start tomorrow is in handover/phase-4-brief.md.

## 2026-10-21, evening: first Blender test

- The owner: "i want to test blender, can create a small model just for testing",
  then "will it be recorded for our video". Yes: stills, a turntable and a note
  are in video-local/footage/2026-10-21-blender-test/.
- A Python script built a small upright piano with all 88 keys named by note, each
  key's pivot at its back hinge, a C major chord pressed. Rendered with Cycles on
  the M2 Pro GPU: about 75 s for the finished still, 20 s more for clay.
- Exported as a 150 KB GLB: all 88 key names came through exactly, no ".001"
  suffixes. The pipeline from Blender names to code names works.
- What went wrong: the first run returned no output at all and produced nothing;
  rerun in the background with a log file, it worked. In the render, two blocks
  overlap at the key cheeks and leave black slivers, and the music rest was placed
  inside the case. Fine for a test; the real scripts check for both.
- The owner watched the test footage: "it does not have building video". Stills and a
  turntable show a finished thing, not the making. So a build sequence was added: the
  piano assembles itself in glowing blue wireframe (case, keybed, legs, pedals, then
  all 88 keys sweeping from A0 to C8 like a glissando, then the bench), crossfades to
  clay, then to lit, and a C major chord presses. The video plan now asks for one of
  these at every step.
- Went wrong on the way: a shell loop passed all three arguments as one, so the first
  three test renders failed at once; fixed and rerun.

## 2026-10-22: quality test, 2D first, and a model change

- The owner compared the box-piano test with Felix's video ("but have seen relix
  viedeo") and asked for a quality test before Phase 4: "i want to do a quality test
  before". The designer agent started a properly modelled upright piano.
- The owner asked to watch Blender live, so the designer now runs Blender with its
  window open instead of headless, and saves the .blend before rendering.
- Then: "can i see 2d designs before it starts 3d modelling". The designer paused and
  is drawing a to-scale 2D sheet first (front, side, keyboard, details, two finishes).
- Model: asked which model gives the best results, the owner said "you can use fable
  if you want". 3D modelling moves to Claude Fable 5.1; the 2D sheet stays on Opus.

## 2026-10-22: the piano on paper before the piano in 3D

- The owner compared the first Blender test (about 100 plain boxes, flat colours) with
  Felix's making-of video and found ours far behind. The box test proved the pipeline,
  not the look. So the next step was one object, the upright piano, at the quality the
  final room needs.
- Started on the 3D side: shared Blender helpers in `blender/lib/` (name checks that
  read MESHES.md, geometry with bevels, procedural materials: black lacquer under a
  clear coat, walnut veneer, ivory, felt, brass, oak planks). None of it has run in
  Blender yet.
- Mid-task the owner asked for two things: to watch Blender build live on their screen,
  and then, before any modelling, to see 2D designs of the piano first. Modelling
  stopped there.
- All the piano's dimensions now live in one place, `blender/lib/constants.py`: 153 cm
  wide, 121.7 cm to the top of the lid, 60 cm deep, white keys at 73.5 cm, 88 keys
  spanning 122.2 cm. A plain Python script (`blender/design/piano_design_sheet.py`)
  draws the sheet from those numbers as SVG and screenshots it with headless Chromium,
  so the drawing and the later model cannot drift apart.
- The first draft of the sheet caught a real design mistake: an A4 music page leaning
  on the rest would have passed through the top moulding. Real 121 cm uprights have the
  same problem; the music sticks up past the lid and leans on its front edge. The rest
  moved forward and the sheet now leans there. The open fallboard also hit the front
  panel by 7 mm, so the panel moved back 1 cm.
- Went wrong on the way: labels ran off the panels and over each other in the first
  render, and one callout drew past its box. Fixed in a second and third render.
- Sheet: `video-local/footage/2026-10-22-piano-quality-test/piano-design-sheet.png`.
  Waiting on the owner: approve the proportions and pick the finish (polished black
  recommended, warm dark walnut the alternative).
- The owner approved the 2D sheet and chose polished black: "Approved. Go with A, polished
  black. Start the 3D piano on Fable with the Blender window open."

## 2026-10-22, night: the piano in 3D, the quality test

- The owner approved the 2D sheet and chose polished black, then went to sleep with a
  cut-off of 03:45. Fable 5.1 (designer agent) built the piano in Blender from the
  sheet's numbers: `blender/props/obj_piano.py` reads `blender/lib/constants.py`, and
  the layout maths the sheet used (key offsets, cheek and console curves, fallboard, lid,
  sheet line) moved into `blender/lib/piano_layout.py` so the drawing and the model
  share one source. The sheet rerun came out byte-for-byte identical after the move.
- What changed from the box test (about 100 boxes, flat colours): 143 parts in the
  .blend, every edge bevelled (1.2 mm on keys, 4 to 8 mm on the case), the side panel
  and key cheek are one profile so the arm has no seam, raised fields on both panels,
  a U-shaped crown moulding, three brass butt hinges with five knuckles and screws,
  brass castors in dark cups, flared pedals coming out of a felt slot, the music rest
  with lip and brackets, 88 notched white and tapered black keys on the real offsets,
  a red felt strip behind the keys, the fallboard open at 95 degrees on its hinge,
  the sheet music (a generated image of two pages of staves) leaning on the lid's
  front edge, and an interior: gold plate with struts, 230 tuning pins, pressure bar,
  bridges, 230 strings (copper bass crossing in front of the steel trichords), 88
  hammers with felt tips, 68 dampers, the hammer rail. Plus a bench. Materials are
  procedural: lacquer with a clear coat and a faint orange-peel ripple, ivory with a
  little subsurface, ebony, brass with uneven roughness, felt with sheen, oak boards.
- Builds in 1.8 s with the window open. The helpers written the day before
  (`names.py`, `geo.py`, `materials.py`) ran first time in Blender 5.2; two additions
  were needed (multi-cylinder meshes and joins for the pins, strings, hammers; a colour
  attribute so one material can tint the joined interior, since a mesh the code
  touches may have only one material).
- Watching it build: the window version drives the build and the renders from a
  Blender timer (one group of parts per tick, renders started with INVOKE so they
  show in the render window and are polled until the job ends). The viewport is set
  to material preview through the hero camera before the first part appears. Fallback
  for headless is the same generator run straight through.
- Render times, Cycles on the M2 Pro GPU at 1920x1080, denoised: hero 37 s (320
  samples), keys close-up 64 s (384, f/2 depth of field), lid open 76 s, clay 25 s,
  wireframe 1 s (EEVEE). The first quick render of the test scene was too bright and
  grey for 5:40 a.m.; the world light went from 0.35 to 0.14, exposure from +0.35 to
  0, the window light from 420 W to 300 W, and the hero camera stepped back so the
  castors and the bench legs were no longer cut off.
- GLB of `obj_piano` with the statics joined into `piano_static`: 1.86 MB, 51.5k
  triangles, 96 meshes, 101 nodes, all 99 MESHES.md names present. A "lite" export
  without the small bevels on keys and hammers: 1.75 MB, 39.5k triangles. The size is
  mostly vertex data (normals, float vertex colours, the 1024x724 sheet image); the
  triangles are mostly bevel segments on the case (20k in `piano_static`), 156 per key,
  and the pins, strings and hammers (16.6k together).
- Went wrong on the way: the first builder named each hinge's barrel, each castor's
  wheel and each hammer's shank with the same temporary name, so Blender silently
  added `.001` and the name check (which exists for exactly this) failed; unique
  temporary names fixed it, and they vanish when the parts are joined. The hammer
  heads were first placed through the strings (a sign error in front-to-back); laid
  out again with explicit y values. The generated sheet image came out upside down
  in the first quick render because the screen helper writes V = 0 on the top edge
  for the web; the image is now written top row first for Blender.
- The build clip (13 s, 390 frames at 30 fps, EEVEE at 32 samples): wireframe 42 s,
  clay 188 s, lit 199 s, then FFmpeg crossfades (1 s each) and the frames deleted.
  Whole run, build to quit, 639 s with the window open; disk peaked well under 1 GB.
  EEVEE's lit look still shows speckle on the wall by the warm lamp (soft shadows at
  32 samples); more samples or Cycles for the final video.
- Open for the owner: the inside still is dark and the sheet music hides the middle
  of the action; a brighter interior fill or a camera from further right would help.
  The hinge barrels sit on the lid's back corner with the lid overhanging 8 mm, which
  is right from the front and odd from behind (never seen in the room).

## 2026-10-22, 02:00: the owner checks the piano and changes the design

- The owner woke to the quality test, opened the .blend in Blender ("can first check
  this piano") and then asked "can we use different design". A sheet of five styles
  from reference photos (modern black, satin mahogany, Victorian walnut, carved cabinet
  grand, a design grand) was made in about ten minutes; its first render had the wrong
  photos on one card (a nameplate and a loose moulding instead of the piano), fixed.
- Choice: "i'll choose option A with some polyphia style". So the black studio upright
  stays, dressed in Polyphia's black-and-gold ornament language. Next: a 2D sheet with
  three ornament levels, then the 3D rebuild.

## 2026-10-22: the ornament sheet, three levels of Polyphia style

- Follows the owner's "i'll choose option A with some polyphia style". A 2D sheet,
  before any 3D: the same front elevation three times at one scale (reused from
  `piano_design_sheet.py`, so proportions match the approved sheet), a 2.4x close-up
  of the fallboard and music rest for each, a strip of the motif language, and a
  recommendation. Script `blender/design/piano_ornament_sheet.py`; output
  `video-local/footage/2026-10-22-piano-quality-test/piano-ornament-sheet.png`.
- The motif is our own: a Baroque scroll-vine that branches like a family tree (the
  room's evolution of music), black and gold with pearl accents. No copied artwork, no
  text, no logos. Every ornament is drawn in the piano's metres and tagged geometry,
  texture or material.
- Light: gold hardware, a 2.5 mm pinstripe, the seed motif on the fallboard. Medium:
  plus corner filigree, a pierced music rest backed with dark mauve silk, gold cheek
  caps, a running scroll on the lid edge. Full: plus a big branch across the upper
  panel, relief on the cheeks and consoles, engraved pedals, pearl key fronts, the
  bench. Recommended: Medium. Owner to choose.
- Went wrong on the way: the first render had the Full column's text running into the
  bottom panels, the motif cells' gold lines spilling outside their boxes, the cheek
  caps drawn as heavy gold bars, and the running scroll reading as a zigzag with
  tiny hooks. Fixed by a taller page, clipped cells, thinner caps and bigger curls.
- Noticed: the bench's dimensions live only in `blender/props/obj_piano.py`, not in
  `constants.py`; the sheet copies them with a comment.
- Before picking a level, the owner sent two tribal tattoo designs (one with a
  skull-spider centre, one with a heart): "i want this kind of art work on my piano in
  silver". The scroll-vine in gold is dropped; a new sheet in tribal silver follows.

## 2026-10-22: the tribal sheet, silver instead of gold

- Follows the owner's "i want this kind of art work on my piano in silver", with two
  tribal tattoo designs (local only). A new 2D sheet, same front elevation and scale as
  before: `blender/design/piano_tribal_sheet.py` (the scroll-vine script is untouched),
  output `video-local/footage/2026-10-22-piano-quality-test/piano-tribal-sheet.png`.
- Our own strokes from four parts: a tapering blade, a hook, a flame point, a teardrop
  cut-out, mirrored about the piano's centreline, every needle pointing away from the
  emblem. Nothing traced from the references.
- The main question was placement: the references stand tall, the piano is wide. The
  axis turns 90°: the emblem drops to the fallboard's face, two arms open sideways
  from behind the music across the upper panel. The centre cannot sit above the music
  line: the sheet's top (126 cm) is higher than the case (119.5 cm).
- Three emblems for the owner: a clean skull (no spider), a heart, and a tuning fork
  (ours; a treble clef was ruled out because it cannot be mirrored). Two levels:
  Medium (sweep, emblem, lower corners, chrome hardware; about +0.4k triangles,
  +0.5 MB) and Full (plus consoles, cheeks, lid edge, bench, silver key fronts;
  about +1.1 MB). Recommended: Medium with the tuning fork. Owner to choose.
- Silver spec: brushed sterling silver inlay #b7bbc2 under the clear coat, flat in
  the bake; hardware polished chrome #d4d7dc, nickel #cbc4b6 shown as the warmer
  option. Texture, not relief.
- Went wrong on the way: the first render's strokes were too thin, closer to barbed
  wire than tattoo work, and the teardrop cut-outs were too small to see. Widths about
  1.6x fixed it. Then each stroke had its own gradient, so wherever two strokes
  overlapped (flame roots, the skull's cheekbones) a seam showed. One page-wide
  silver sheen fixed that. Also cut: brow points on the skull that read as ears,
  and a cheek motif first drawn across the cheek cap; it moved to the flat front
  below the nose.
- The owner picked from the tribal sheet: "fork ,full". Tuning-fork emblem, Full level,
  against the designer's Medium recommendation. Next: the 3D rebuild on Fable.

## 2026-10-22, 03:00: the 3D rebuild with the tribal ornament (Fable 5.1, designer)

- Follows the owner's "fork ,full". The quality-test piano rebuilt with the approved
  ornament: tuning-fork emblem, Full level, brushed silver #b7bbc2 under the clear
  coat, polished chrome #d4d7dc hardware. Dimensions unchanged. Owner's deadline:
  stop by 04:00, so the run went hero first, fallboard close-up and the ivory-fronts
  alternate next, the other stills, the GLBs, the clip last.
- One source for the strokes: the engine, motifs, emblems and placements moved from
  `blender/design/piano_tribal_sheet.py` into `blender/lib/piano_ornament.py`; the
  sheet now imports them and its HTML output is byte-identical to before (checked by
  diff). The same module rasterises the strokes into the silver masks (numpy, a
  non-zero-winding scanline fill on a 4x4 sub-grid, box-filtered: no new dependency)
  and writes the UVs: each ornamented face is a rectangle of the front elevation
  packed into a 4096x1024 atlas (upper field and fallboard at 1.6 px/mm, lower field
  1.4, cheeks 2.4, consoles 2.0 turned on their side, bench apron 2.0) plus a
  2048x96 strip for the lid's front edge. The mask is the image's alpha; its RGB is
  lacquer or silver, so one image per material drives base colour, metallic and
  roughness, and the glTF exporter carries it (checked first with a three-plane
  test: alpha into Metallic becomes a metallicRoughness texture in the GLB).
- The UV rule that kept the bevels clean: front faces project onto their region;
  side, top, bottom and back faces snap to a blank 8 px margin ring just outside it.
  A bevel strip between a front face and a neighbour then only ever crosses blank
  texels. Without this the fallboard's outer face (the top when closed) would have
  carried a mirror of the emblem, and the 4 mm bevels would have smeared whole
  regions along the edges. Worked out on paper before the first render; the quick
  headless check (42 s) came out right first time, emblem upright, nothing on the
  back faces.
- Also built: chrome caps over the cheek noses, a pointed lock plate with its keyhole
  on the key slip (about +0.4k triangles, as the sheet said), pedals, castors and
  hinges swapped to chrome, silver fronts on the 52 white keys by a colour attribute
  in the ivory material (a Value node `key_silver` switches them off for the
  comparison render). The bench's dimensions moved to `constants.BENCH`. Materials
  13 (was 12: `mat_piano_lid` has the lid strip; `mat_piano_chrome` replaces brass).
- The lid-open still: a 90 W fill over the open lid, on only for that still, and the
  camera moved to the right of the sheet. Strings, hammers and dampers now read.
- Times, Cycles GPU 1920x1080 denoised, window open: build 3.9 s (the masks take
  about 2 s of it); hero 45 s, fallboard 45 s, ivory-fronts hero 46 s, keys 109 s,
  inside 90 s, clay 27 s, wire 1 s. GLB rich 2462 KB and 53.1k triangles (was 1862
  KB, 51.5k), lite 2294 KB and 41.1k; of the growth, 300 KB is the five PNGs the
  exporter embeds (the atlas twice: base colour 161 KB and the derived
  metallic-roughness 120 KB; the lid strip 11 + 9 KB; the sheet 29 KB), the rest UVs
  on `piano_static` and the key colours. Atlas on disk 165 KB as PNG; as KTX2 about
  512 KB (ETC1S) or 4 MB (UASTC), so ETC1S for the mask.
- The silver key fronts, seen lit: from the hero distance they turn the keyboard's
  front into a dark grey-blue bar (brushed metal reflecting a dim room) and the
  ivory loses its warmth; straight on they read as cool grey bars under the keys,
  not as silver. The ivory alternate keeps the keyboard reading as a keyboard.
  Designer's view: ivory fronts; the owner decides from the two heroes.
- Went wrong on the way: nothing in the model; the run itself was clean. Two
  things to watch: the cheek hook crosses the 6 mm bevel groove between the cheek
  block and the side panel (as drawn on the sheet, both parts share the region, so
  the stroke is continuous but bends over the groove); and the console flames reach
  the console's edges, so their tips are clipped by the face.
- The build clip (13 s, 390 frames, EEVEE at 64 samples instead of 32): wireframe 78
  s, clay 357 s, lit 383 s, FFmpeg crossfades, frames deleted (44 MB at peak). The
  silver appears in the lit phase. Whole run, build to quit, 1195 s (20 min) with
  the window open; done 03:28, inside the owner's 04:00 deadline.
- The owner chose ivory key fronts and asked to shorten the two clipped strokes: "Ivory
  key fronts, and shorten the two clipped strokes. Then this piano is approved". The
  designer agent (Fable) switched the fronts and shortened the cheek hook, re-rendered
  the hero and the sheet, then stopped when the owner's usage limit ran out at about
  03:35, before the console flames, the other stills and the exports. Finished the
  next day on Opus: the console flames were 5.5 cm at 40 degrees on a 4.8 cm face, now
  2.6 cm at 28 degrees; the hero, key cover and keys stills and both GLBs re-made
  headless in 204 s (rich 2.36 MB, lite 2.25 MB). The piano is approved as the
  quality bar for the room.
- The owner moved off Fable: "now don't use fable", then "you can use other model with
  right effort". Back to the model guide: designer on Opus, builder on Sonnet, quick
  on Haiku.

## 2026-10-22, afternoon: the room on paper (Phase 4 Step 1, designer on Opus)

- Before the room shell is built, a to-scale 2D room plan, as the 2026-10-22 rule
  asks: `blender/design/room_plan_sheet.py` draws
  `video-local/footage/2026-10-22-room-plan/room-plan-sheet.png` from new blocks in
  `blender/lib/constants.py` (ROOM, WINDOW, DOOR, SWITCH, LIGHT, LAYOUT,
  WALL_GUITARS, HERO). The piano front on the right wall is drawn by the approved
  piano sheet's own function, so its numbers are not retyped.
- Proposed room: 440 x 420 cm, 300 cm ceiling. Window over the bed's head on the
  back wall (east), desk in the middle of the back wall, rack between the desk and
  the piano, piano on the right wall in the back half, wall guitars above it, door
  on the left wall by the front corner as in the owner's photo.
- What drove the numbers, found by trying it, not by guessing: the hero camera stands
  at the front wall, so only the back wall and the back halves of the side walls are
  in frame. Everything clickable moved there. The first layouts put the piano and
  the frames too far forward and they fell out of frame; the wall guitars hang high
  (the lid opened fully reaches 163.7 cm), so with a 2.85 m ceiling their headstocks
  were cut. 300 cm ceiling, guitar bottoms in one line at 172 cm.
- The script checks clearances (desk, rack, piano, bench, bed, door, lid vs guitars)
  and computes how much of each of the nine objects is in the hero frame; it also
  renders a flat-shaded perspective sketch from the same numbers, so the composition
  is judged from a picture, not a description.
- Went wrong on the way: the centimetre formatter stripped zeros from whole numbers
  ("44 cm" for 440); the guitar panel was depth-sorted over the guitars on it; the
  sketch's back-face culling was inverted (the camera frame is left-handed), which hid
  the monitor's screen and the frame pictures; the ceiling-light check measured the
  light at the room's centre after it had moved. All seen on the rendered PNG and fixed.
- Rack question: the hero sketch shows A and B side by side. B has no wall to stand
  on (the bed's head is left of the desk), so the rack ends up on the rug. Recommended A.
- Small changes proposed for the owner: cut the nightstand, the ceiling light becomes a
  pendant 50 cm behind the centre so it is in the hero frame, the bench rests pushed in
  22 cm so the rack guitars show, the switch on the left wall by the door.

## 2026-10-22, afternoon: the room plan and the desk designs

- The room plan sheet (440 x 420 x 300 cm, the walls, the hero camera) was drawn on
  Opus; the internet dropped halfway and the agent was resumed from its last step.
- The owner approved rack A and asked "before that what models you are going to use
  for studio monitors, monitor screen and dj console". A reference sheet showed three
  options each. The owner: "use adam audio studio monitors, which model you are
  choosing let me know, for rest you can use recommended options". Chosen: the A7V
  style, the thin aluminium monitor, the compact two-deck controller.
