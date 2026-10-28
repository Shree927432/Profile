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
- Before the room shell, the owner asked for footage "from multiple camera angle and
  with better animation" and reminded that the "final edit will be on moonlight sonata
  as decided". The video plan now asks for five camera angles per build step, eased
  and staggered motion, and build timing read from a beat-grid file, so the footage
  can be re-rendered to the owner's own recording later.

## 2026-10-22, night: the room shell in Blender (Phase 4 Step 1)

- The owner: "start the room shell". Built on Opus (designer agent), headless first, then
  with Blender's window open for the footage.
- One command builds the whole room in about 3 s (`blender/build.py`): the floor, walls,
  ceiling, skirting, the window opening with its Kota-style stone ledge and the door
  opening at the plan's numbers; the desk with keyboard and mouse; the monitor in the
  approved style (aluminium frame, black glass front, a stand bent from one plate, leaning
  back 5 degrees); the approved piano; and a named footprint shape for every other root on
  the plan, so the shell can be judged whole. Names are checked against MESHES.md before
  the save and again in the exported GLB.
- The TOP test passed on the first export: `/?room&glb&uvtest` shows TOP upright and not
  mirrored, on desktop and phone; with `/?room&glb` the posts are upright, the glide still
  opens a post (keyboard and a mouse tap), orbit and zoom work, no console errors.
  `/?room` and `/` are unchanged. The GLB is 521 KB, 12k triangles, behind the flag only.
- The site now opens the GLB room at `room_view`, the hero camera of the approved sheet.
  Orbiting the screen's centre from there would have dropped the pendant light out of the
  top of the frame, so a lens shift keeps `room_view_target` centred at the start and fades
  out as the camera nears the screen; the close-up and the glide are framed as before.
- Went wrong on the way, all caught on rendered pictures, not in code review:
  - the first GLB was 1.1 MB because the keyboard plate's 3 mm bevel was applied to every
    keycap joined into it; keycaps became their own part, and the web copy drops bevels of
    2 mm or less and every footprint bevel (521 KB);
  - procedural colours (oak grain, walnut, stone) arrive white in a GLB; the export now
    uses each material's mean colour until the bake;
  - in the browser a black box filled the foreground: the piano stand-in lost its root's
    turn because the copies made for the static join were re-parented with a stale matrix;
  - the first storm frames speckled along the back-right corner during a lightning flash:
    walls that only touched let EEVEE leak light through the seam; the walls, floor and
    ceiling now overlap inside their thickness, and the flash is aimed into the window;
  - the top-down camera rendered black: the ceiling's visibility was keyframed by the
    build, so hiding it per camera did nothing; it is hidden from the camera ray instead;
  - the night sky material vanished from the saved file (no users); it now has a fake user.
- Footage: event times come from `blender/video/timing_room_shell.json` (bars and beats on
  the placeholder Presto grid). Three Cycles stills (blue hour, clay, wireframe) and the hero
  storm clip were rendered (24.5 s, 26.6 min at about 2 s a frame). The owner found the
  camera too static and stopped the run at 00:26, during the second of six clips; the low,
  orbit, top, detail and dawn clips were not rendered. New plan: each build step keeps only
  light process captures (a few stills, one quick low-resolution build preview); the full
  directed, multi-camera shoot to the music happens once, at the end.

## 2026-10-23, night: the first room-shell footage, and a note on the camera

- The room shell is built and runs in the site behind `?room&glb`; the TOP test passed
  first time, upright. The approved piano is placed in it.
- The owner watched the first clip: "camera movement looks very static, there's not
  camera movement, closeup where needed, no zoom out where need, like a professional
  grade camera movement". Tonight's clips stay as they are; from the next step every
  shot is directed (push-ins, reveals, cranes, focus pulls, on the beat), with a shot
  list and a low-resolution animatic approved before the full render.

## 2026-10-23: the first exact guitar, on paper

- The owner asked for "exact and very high quality copies of original guitars", without
  logos, starting with the Hendrix Woodstock Strat, and asked to see the original photos first.
- 2026-10-23: guitar_02 blueprint drawn from real specs (two measured vintage Strats, the Custom
  Shop tribute specs, the MoPOP photo). First outline was drawn from memory and read wrong (spiky horns,
  a bulging treble shoulder); found by looking at the render; fixed by measuring the silhouette of the
  real guitar in the approved museum photo. The same photo moved the bridge 18 mm towards the tail and
  made the large headstock 208 long, not 193.
- Research found that a flipped guitar hung on a wall is not a mirror image: the turn is in its own
  plane. The brief and MESHES.md assumed a mirror. Sheet offers A exact, B mirrored, C lifted.
- The brief said one-piece neck; the original is two-piece (no skunk stripe on the back).
- Labels first sat on top of the body; switched to numbered balloons with a legend.
- Approved: "Approved with the recommended choices" (ageing A, hangs as A, C when lifted,
  no cigarette burns). Next: the 3D replica on Opus.

## 2026-10-23, night: guitar_02 in 3D, the Woodstock Strat (01:25 to 03:05)

- Built `blender/props/guitar_02.py`: every part in the spec's millimetres from `guitar_specs.GUITAR_02`
  and the blueprint's own geometry functions, so sheet and model share every number. Body with a true
  6.4 roundover, forearm and belly contours and a routed jack dish; two-piece maple neck on the
  7.25 in radius, 21 frets, dots, bone nut; vintage tuners, butterfly tree, bent-steel saddles with
  height screws, intonation screws and springs, the arm; 3-ply guard with the black line on the
  bevel; covers with poles in the vintage stagger; knobs with 0 to 10 on the skirts; Hendrix's
  stringing with wound strings and wraps on the posts. Ageing A by a `wear` attribute (horn tips,
  forearm edge, frets 1 to 7) under procedural lacquer. The lite web model (about 7k triangles) bakes
  colour, AO, roughness and metal from the same materials into one 1024 atlas and a 512 ORM.
- `blender/build.py` now puts the guitar on its hanger in the room (rich in the .blend, lite in the
  GLB); `room.glb` 521 -> 1,097 KB. `/?room&glb` shows it on the wall; posts and glide work; no
  console errors; `npm run build` passes.
- Went wrong, found by looking at renders:
  - close-up cameras rendered the skirting and the floor: placed before the guitar's matrix updated;
  - pickup covers streaked (a bevel on a tapered n-gon); rebuilt with a real roundover;
  - saddles read as solid blocks and the arm rose through the high-E saddle; now bent steel strips,
    the arm moved 4.5 mm out, saddle ends kept clear of the lip;
  - the string tree's wings were built on the centre line, not at the tree (hidden while the tree sat
    near the centre);
  - the tuner keys rendered as dark blurry discs: flat paddles mirroring the room, 1 cm tarnish
    blotches, f/5.6 on keys 20 mm behind the face. Domed keys, finer tarnish, f/11;
  - the first lite export was 12k triangles; cut to 7k (no screws, simpler poles, keys, saddles).
- The coordinator reviewed the first hero against the museum photos: horns short, upper bout narrow,
  headstock a narrow blade, a stray chrome disc, keys too far out. An orthographic overlay showed the
  model was exactly the approved blueprint, so the error was in the blueprint data. A homography on
  a frontal 1970 Strat photo (fret dots plus the pickup screws) measured the treble horn and upper
  bout too small; two rounds brought the body within 2 to 3 mm (`guitar-02-compare.png`). The same
  check found the pickup screws drawn outside the covers (they go through the cover ends, 77 apart).
  The disc was the hanger's chrome wall plate seen in parallax; now a small black base.
- The headstock took three tries. r2 (the large CBS shape redrawn) drew the owner's "the headstock
  design is really bad, keep original one". Tracing a real one needed a download, which needed the
  owner's yes first; meanwhile the approved r1 outline went back. The owner then sent photos of a
  small-headstock Strat: "use this design for headstock", and "use only headstock design for it, rest
  you can keep it original". r3 is traced from that photo, rectified on the nut, frets 1 to 3, the
  3rd-fret dot and the six posts (0.45 mm rms), and checked against the small head in the Commons
  comparison photo (1.3 mm median). The museum photo used earlier rectified poorly beyond the frets
  (hanger foam, no known geometry up there), which is why r2 could only be matched by eye.
  New on the way: on the real guitar the tuner posts sit on a line 17.7 degrees to the neck, not
  parallel to it as the blueprint had them.
- Mistake: running `room_plan_sheet.py` to check it after the WALL_GUITARS change rewrote the local
  room-plan PNG (only guitar_02's length and hook moved, by millimetres). The script is the source.
- Light process record only, as planned: seven Cycles stills, two in the room, a 7 s EEVEE preview.

## 2026-10-23, 03:00: the room changes what it says

- Looking at the room, the owner: "the room looks more like a musicians room, where as
  i'm a musican but i'm some one who is going to lead frontier and currently i'm a ai
  engineer". Then two photos of a white L-shaped tech desk: "we can remove the bed and
  table and turn the other half into this". The room becomes half music studio, half AI
  lab. A new room plan sheet comes first.

## 2026-10-23, 03:20 to 04:50: Number One overnight, then guitar_02's guard

- `guitar_04`, Stevie Ray Vaughan's "Number One", built overnight without a prior blueprint approval
  (decision of the evening). Blueprint and 3D together: `guitar_04.py` runs guitar_02's Strat builders
  under guitar_04's names and spec (`lib/variant.py`), so guitar_02.py was not touched; its own pieces
  are the worn sunburst (traced wear map plus noise, shared with the blueprint by `lib/guitar_wear.py`),
  rosewood and clay dots, gold hardware, pearl tuner buttons, the jack, the bridge and the arm. Stands in
  rack slot 1, pivot at the body's lowest point at the 15 degree lean, neck on the top bar at the 3rd fret.
  First stills 03:38, room 03:51; rich 3.7 MB / 126k, lite 644 KB / 7.1k triangles.
- Owner's review of the first compare, in three messages: "head stock is correct but body outline is
  little bit off", "even pickups of guitar are little off", "bridge is different of this guitar plus jack
  input is not right". The first photo fit had used guitar_02's pickup places and strap buttons as fit
  points, so it could not have found them wrong. Refit with the bridge row and pickups free (0.52 px rms):
  pickups 3 to 7 mm and the bridge 5 to 7 mm towards the tail of guitar_02's places, and a traced body of
  its own. Rebuilt; the coordinator committed it (76a6b45).
- Then the check on a second photo (the real guitar, n1-4) put the trace 6.6 mm inside it, 4.6% apart.
  Photo or guitar? One radial lens term on owner-ref-11 dropped the residual from 3.65 to 1.27 px, made the
  body 322.6 mm wide (a Strat's) and made the approved headstock fit too (25 -> 4 mm): the retail photo is
  barrel-distorted about 3% at its edges. n1-4 shows no distortion. Everything re-measured in the lens-
  corrected frame, rebuilt (997c140): body median 0.0 mm, 95% within 0.6 against owner-ref-11; 4 mm inside
  n1-4 (1.9%, within that photo's dark-edge segmentation). Rich 3.9 MB / 132k, lite 650 KB / 7.3k triangles.
- Owner: "you can change position of tremolo arm": the arm rests across the lower bout (it would hang
  into the rack's cradle as displayed). "you can fix the strat if you want": guitar_02 r4. On the real 1968
  guitar's close-up its r1 guard was about 50 mm too wide on the bass side at the waist and the knob line
  10 to 32 mm off; the frontal 1970 Strat put its pickups 4 to 7 mm too far up, agreeing with Number One's
  places. Guard, screws, knobs and pickups fixed; body, headstock, bridge, switch left (the bridge is about
  7 mm off and the switch about 17 mm by the same photos: for the owner). Rich 3.6 MB, lite 579 KB.
  `room.glb` 1,745 KB with both; `/?room&glb` loads with no console errors on desktop and phone, posts and
  glide work, `npm run build` passes.
- Went wrong: a misread grid put the bridge screws 3 to 7 px off (found when the bridge row came out of the
  fit 2 mm off); a re-aimed hero cut off the headstock; the rack close-up first rendered black (camera
  inside the piano) and then mostly piano bench; one windowed Blender run printed 6,833 "Python context
  internal state bug" lines without harming the renders. The first wood read grey-violet under the dawn
  light: warmer colours, rougher, lower specular.

## 2026-10-23, 03:30 to 04:50: the AI lab on paper, piece by piece

- Asked for "the exact ai lab and same models for each components of it", I drew a rough
  front-facing layout of the two walls from the owner's photos, with each component
  numbered. The brands in the photos could not all be read for sure; the drawing said so.
- The owner chose white studio monitors ("can use white version of adam aduio studio
  montiors") and asked whether to place them as in the photo or as in the old layout. The
  photo was right: on short stands, tweeters at ear height, turned in. My first drawing had
  them on flat pads, too low. Checking the photos showed the white A7V is a real limited
  edition, so nothing had to be invented.
- "i want to know model of each component": a list of 22, then "can show the images as
  well": a local photo sheet of Bing thumbnails, 112 images, nothing downloaded. One swap
  came from checking: the white Stream Deck I could confirm is the MK.2, not the +.
- The L desk: three options drawn to scale (one-piece top, two butted IKEA tops, an L
  standing desk). Owner: "okay go with option A". Then: "okay then list has been aproved".
- Miss: the first front layout put the speakers on pads at desk height, and the window
  still sits at its old place in `constants.py`; both are fixed on the new room plan sheet.

## 2026-10-23, 05:00 to 05:30: the room plan v2, half studio, half AI lab

- Owner: "Draw the room plan sheet tonight after Number One and the Strat fix, then shut down.
  I'll review it all in the morning." The designer (Opus) drew it from a new
  `blender/lib/plan_v2.py`; nothing the current build reads was changed. Sheet, blockout from
  the hero camera and a phone view in `video-local/footage/2026-10-23-room-plan-v2/`. Not yet
  approved.
- Numbers: window centred (x -60 to +60); L desk 155 x 80 plus a 180 x 60 return; screens on
  one pole, the 27-inch on top carries the posts (16:10 inside the glass, so the posts code does
  not change), the 34-inch the training dashboard; the wall guitars' bottoms 8 cm above the open
  lid, the double-neck 18 cm under the ceiling; walkways 120 cm or more; ten interactive
  objects, exactly the limit, with a new `obj_rig` (needs the owner's OK to change MESHES.md).
- Went wrong, all found in the first blockout render: the wall guitars' heads cut off at the top,
  the DJ decks hidden behind the chair, every left-wall item facing the wall, the rack's
  footprint through the back wall and the bench, the rack's guitars in reverse order, a key
  light through the wall. Not fixed: the chair zone overlaps the rug by about 10 cm.
- Morning: the owner asked whether the PC setup would look better on the left wall. From the
  hero camera the screens would turn almost edge-on, so the back wall stays. Owner: "keep the
  current version don't change it".
- The owner found "better rendered models of guitar online": two Sketchfab Strats and an ADAM
  A4V on RenderHub. Checked, none usable as is: the Hendrix one is view-only and is not the
  Woodstock guitar (rosewood board, cream guard); the free CC-BY Strat is a modern sunburst
  with the logo, 373k triangles; the A4V is editorial use only. Their edge is lighting and
  lacquer, not shape. A look pass on ours was offered; owner: "Not now, leave the guitars as
  they are."
- Reference photos saved, local only: the 14 ADAM A4V preview renders from RenderHub (the paid,
  editorial-only model itself not bought) and the 14 Samsung Odyssey OLED G8 gallery images.
  The Samsung server was slow; the download took over two minutes.
- Owner: "can you use apollo twin or suitable apollo audio interface instead of RØDECaster Pro
  II". Now an Apollo Twin X: big knob = volume, preamp knob = pan. Plan and sheet updated; the
  blockout still shows the old, larger console box until the next blockout render.
- Owner: "go for bigger option": the Apollo x4 instead of the Twin X. It fits under the 34-inch
  screen with only 1.3 cm to spare; the next plan revision raises the screen or moves the
  interface forward.

## 2026-10-23, afternoon: references for every AI-lab component

- Owner: "do deep research and download the best reference image of each component for AI
  lab and save it", then "you also find the best free 3d models of component that can be used
  for our work if needed". Four research agents (Sonnet), one per group. 27 folders in
  `docs/moodboard/local/ai-lab/` (local only, 152 MB), each with images, a SOURCES.md
  (official dimensions with sources, UNSURE marks) and a MODELS.md (free models, licence,
  triangles, verdict). No 3D file downloaded; a shortlist waits for the owner.
- Owner sent IKEA's desk page: IKEA's own 3D file measured 2000.7 x 600.6 x 735.5 mm, so the
  desk is 73.5 cm high, not the 75 the plan assumed (no pucks under the top).
- Went wrong: the first research run died when the app restarted. Its images survived (all
  valid) but every notes file was lost, because the agents wrote notes last. The rerun wrote
  each component in full before the next. Many sites blocked scripted downloads (Sony, B&H,
  Audio-Technica, Unsplash, Pexels; Nanoleaf rate-limited), worked around through makers' CDNs
  and the browser pane. One "white" Stream Deck image was the wrong product.
- Findings that change the plan: the Hue Play strip is made for the back of a monitor, not under
  a desk; the current Apollo x4 (Gen 2) is silver with white buttons; the ISO-155's short
  setting (76 mm) tilted up puts the tweeters near ear height; the PC case is 30.4 x 48 x 46.5.
  Plan v2 now uses the confirmed sizes; sheet and blockout redrawn, 36 checks pass.
- The free-model shortlist went nowhere, for two reasons. Sketchfab now signs in through Epic
  Games, whose security check never rendered in the in-app browser (the owner saw a blank "One
  more step" box). And looking at the models, the owner: "these models are very novice models".
  Decision: we build every AI-lab object ourselves from the references, like the guitars. The
  three Poly Haven CC0 downloads stay as local reference.
- The owner downloaded six of the free models in Safari after all ("you can check if it works
  then its fine or make some adjustments"). Checked in Blender: scales were off by 33x to 90x,
  the GPU came out light silver with "GEFORCE RTX" on its edge, the camera was the original
  ZV-E10 with a big prime lens. The plants and the ledge are good as they are, once scaled; the
  GPU, camera body and keyboard are bases to adjust. Verdicts and four-view renders are local.
- Owner answered the four room-plan questions, option A on all: 54 degree lens inside, neon on the left wall, obj_rig as the tenth object, open floor in front.

## 2026-10-24: the room shell rebuild, and a layout that did not feel right

- The designer rebuilt the room to plan v2; the app restarted mid-run, so 15 files sit
  half-finished and uncommitted. The owner moved the PC first ("desk is looking too clutered, can
  we shift cpu little bitt towards left"), then: "something is not looking right about the layout
  of the room, what do you think it is". Diagnosis: the desk return put the PC, decks and laptop
  nearest the lens; the centre was an empty wall round a small window; the rack stood alone; the
  wall guitars were jammed under the ceiling.
- Four fixes in the blockout. Two did not work as written: the one-piece piano lid meant the
  guitars gained only 3 cm unless the lid stops at 60 degrees, and the DJ stand only fitted in
  front of the new window, which spoiled it. Owner: "DJ controller on the desk return, PC on the
  floor under it. Window A, no panel, guitars lower with the lid stopping at 60°."
- Seven layout versions later, the owner pointed at the reference photo: "no i want the exact
  layout from the photo". The reason was a new story for the site: open on the sky or the city
  through the window, click, the camera pulls back into the room and turns to the AI lab; the
  music side stays hidden until About. A quick hand-built blockout copied the photo into the
  back-left corner in about ten minutes (the first render had Blender's default cube sitting
  in the middle of the room).

## 2026-10-24, night: plan v3 from the photo layout

- Owner: "Approved. Turn the photo layout into plan v3 with the checks and the sheet." The
  designer drew `blender/lib/plan_v3.py` with four named cameras (intro out of the window, the
  hero matching the photo, about for the music side, phone) and 68 clearance checks, all passing
  after five first-run clashes (the monitor pole through the light bar, speaker poles 0.6 cm off
  the 34-inch screen, the mic arm through the snake plant). The window moved 10 cm right to give
  the return room. The hero cannot match the photo's perspective exactly: our room is wider, and
  an exact match would put the camera where the piano stands.
- Owner: "render the components first and then decide the layout", then "do one component for
  now" (the Mac was on battery at 33%). The screens on their pole went first; the desk and speaker
  builds were stopped before they wrote anything.

## 2026-10-24, overnight to morning: the first AI-lab component, the screens

- One builder (designer, Opus) built the screens on their pole: the Samsung G8 34-inch on its
  1800R curve, the Apple Studio Display 27-inch (VESA version, the posts screen), a white desk pole
  of our own design, the ScreenBar Halo 2 on the top screen as in the owner's photo. Silhouette
  matches against the makers' photos: 0.99 for the G8, 0.999 for the Studio Display. TOP upright on
  both screens. Rich 1.7 MB / 81k triangles, lite 468 KB / 7.6k.
- Went wrong: the Metal GPU stopped returning Cycles renders while three builders and the plan
  designer rendered at once; the builder fell back to the CPU. The Mac was on battery all night and
  reached 2% at 7 am; the coordinator stopped the last slow re-render and committed the scripts
  early. In the morning a re-export "did nothing": macOS has no `timeout` command, so the wrapped
  Blender never started.

## 2026-10-24: a toolkit for faster, more precise modelling

- Owner: "make things faster and more precise". A designer built `blender/lib/{refs,backdrops,
  compare,parts,renderqueue}.py` and `blender/tools/` (outline check, component template, a
  demo). Proved on the approved screens: the generic compare reproduces their scores (G8 front
  0.9894 vs 0.9893, Studio Display 0.9993 vs 0.9985); the lens fit recovers a known 6% barrel
  bend; 30 parts build in 0.1 s; the outline gate takes 37 s and catches a wrong top view.
- It also found something new: Samsung's top photo scores only 0.81 against the G8, the hub ring
  and the stand top too big and too far back. That is the hub the owner already asked to fix.
- Owner mid-task: "Blender is reopening its window again and again, and it's interrupting my
  flow". Everything now runs headless.

## 2026-10-24: the speakers, four rounds to "near identical"

- The white A7V pair passed the outline test from 14 angles on the first run (0.98 to 0.996),
  but close-ups told a different story. Round 2 rebuilt the tweeter plate from a 29 x 28 point
  trace, pleated the ribbon, re-traced the ports, re-measured the facets. Two of the coordinator's
  notes were wrong and the photos said so: the green dot is ADAM's real status LED, and the "chin"
  under the plate is just the logo band. Round 3 fixed the woofer centre and the port insides.
  Round 4, after the owner's "it should look like the photo's fine swirl": the first new cone
  matched the photo's numbers and looked like snow; moving the strokes from colour into normal
  and sheen made it read like brushed fibre. Owner: "Speakers approved, gloss white."
- The coordinator gave feedback in three pieces instead of one full review; the owner asked
  "why these tasks are taking so long". Rule since then: one complete review per round.

## 2026-10-24: the screens, approved, then reopened, then approved

- After round 2 the coordinator called the screens ready; the owner: "still there are lot of
  problems in screen". A full review found ten (the G8's side, ring, foot, rim; the Studio
  Display's banded glass, flat bracket, domed inlet, dark edge, side). Fixing them showed that
  part of the trouble was the comparison itself: hole-filled masks and a side camera 0.7 m away on
  a 25 mm lens had drawn our shell as a wedge and the foot as a block. Owner: "Screens approved
  now."
- Lesson: review the close-ups before calling anything ready, and distrust a comparison that
  disagrees with your eyes.

## 2026-10-25: copy for friends to review, and a push

- The owner asked to drop music from the bio ("remove music part for now"), then to sound confident ("i don't want to look a fresher"), then for copy that is "real, shows my capabilites and work and what i'm persuaing". Home now says what was built, what is in progress and where it is headed. One About rewrite was tried and reverted. Pushed main (59 commits) so friends can review; Cloudflare had it live in about 45 seconds.

## 2026-10-25: checkpoint before the owner closes the session

- Owner: "can you update everything, all checkpoints and remaining tasks and whatever is needed, i
  might quit this session". Updated handover/START-HERE.md, handover/phase-4-brief.md (rewritten:
  state, component pipeline, next steps, this Mac's quirks), handover/RESUME-PROMPT.txt,
  docs/00-vision.md (the current premise), docs/03-roadmap.md, scene/objects/MESHES.md (proposed
  component names), docs/10-video-plan.md, the open questions. The stalled plan-v2 rebuild was moved
  to branch `wip/room-rebuild-v2-stalled` so main is clean.

## 2026-10-26: the components meet the room

- Owner: "can we test the all the component that we have created in the room", then "i want see
  it in blender". The approved desk, screens, speakers and the PC went into the plan v3 room at
  its numbers, with the piano and two guitars on the music side (`blender/design/room_v3_component_test.py`,
  `blender/out/room_v3_component_test.blend`). The test found what a plan cannot: the screen pole's
  clamp 2.7 cm inside the wall, the real arms holding the screens 7 to 13 cm further forward than
  planned, the speakers 1.5 cm from the top screen, and the PC's glass facing the wrong way.
  Owner: "PC option B ... Also apply the plan v3 fit fixes it found", then "Keep the window 3 cm
  to the right." 80 checks pass.
- Went wrong: a reparenting bug put a speaker into the wall in the first test render; the PC glass
  read as a grey slab in EEVEE until screen-space refraction was turned on.

## 2026-10-26: arms, key lights and mic, first pass; invented brand names

- The builder finished the Flex Arm, both key lights and the MV7+ on the PSA1+ in 37 of its 75 minutes
  and placed them in the room test. Its placement proposal B moves key light 1 to the far-left
  corner as in the owner's photo, but needs the shelf 3 cm higher (the real speaker is taller than
  plan v3's box).
- My review of the 15 close-ups found ten misses, the biggest being the Flex Arm (plain tubes, no ball
  joints, one tube floating), the MV7+ yoke (a round fork instead of a flat band) and the PSA1+ (round
  tubes instead of padded covers). All went back in one fix round.
- The owner wanted to watch the modelling live. First a page that refreshes with each new render, then
  one Blender window that rebuilds on every save of the builder's script
  (`blender/tools/live_watch.py`); the owner closed both after a look.
- The owner offered to measure parts and to trace outlines by hand. Not needed yet: the red outlines are
  cut from the makers' photos; hand tracing is kept for photos the automatic cut can't handle.
- Owner: "i want all the names on component with same design, your can different branding names so
  that we don't get copyright". Picked set A, coined tech names; they live in
  `content/room-brands.json`.
- Owner: "Yes, raise the shelf 3 cm to 1.95 m and use placement B." Applied to plan v3, with a new check
  that the key-light panels clear the real speaker's top (the plan's speaker box was 3.6 cm short of the
  built component, which is why plan v3's key light hid the speaker). 82 checks pass.

- Fix round on the arms, lights and mic: all ten fixes in, in 15 of 45 minutes (black finned key-light rim,
  landscape back box, Flex Arm ball joints, flat-band MV7+ yoke, rainbow LED arc, rear ports, padded PSA1+
  covers, T-handle clamp). Left as is: the Flex Arm's balls sit mostly inside their sockets in the room pose;
  the fins and foam texture are rich-only. The room test now reads plan v3's numbers (B). Rich GLB 3.7 MB,
  lite 537 KB.
- Brand names printed (17:25 to 17:42): one helper, blender/lib/brands.py, reads content/room-brands.json; four
  parallel forks did the screens, speakers, PC and arms. 15 decals; lite grew by about 1,230 triangles and 57 KB.
  Went wrong: two forks overwrote lite stills and report JSON in the approved 2026-10-24 footage folders
  (git-ignored, so not recoverable from git; they can be re-rendered); the helper's letter spacing moves
  overlapping letters as one group; the MV7+ knob covers the first letter of HALDEN on one side; the PC
  case shows no logo in any photo, so KAIRO's spot is a guess. Owner: "there are some render issues with
  pc, and why every reflective thing is reflecting the shadow of tree" (the trees were Blender's Material
  Preview forest light, not the room); the PC glass and glow fix started right after.
- PC glass and glow: the milky, grainy EEVEE glass came from the room test forcing raytraced refraction on
  every glass material; the PC now has a thin blended glass for EEVEE and the web, a blue-white glow
  (#5f9fff) on the fan rings and four strips inside the case, and a hidden light inside for renders.
- Fonts. Owner: "fonts are really bad", then "i want the original fonts". The real logos are custom-drawn
  and protected, so a comparison page put each real logo beside three free lookalikes; owner: "use c for
  all". Seven OFL fonts downloaded with permission, cut to static weights. Re-printed every name; spacing now
  comes from Blender's own text engine (the old helper moved overlapping letters as one block). HALDEN moved
  clear of the knob; KAIRO removed (no logo on the real case). Miss: lowering the clamp print's roughness
  made it greyer (it mirrored the white studio at a grazing angle); turning its specular down fixed it.
- The fan rings went from 2.2 to about 5 mm; in the bright room they read as pale circles, still soft.

- Desk-top group: the first builder was lost when the Claude session restarted, about 35 minutes in, with
  no files written. Owner: "You also said 60 minutes half an hour ago". Restarted with a 75-minute box and a
  PROGRESS.md the owner can check at each stage.
- Desk-top group built in about 50 of 75 minutes: Apollo x4 silver, Keychron Q1 Max (81 separate keys for
  typing later), MX Master 3S, Stream Deck MK.2 on its stand, with SOLANT, TAVEN, MIRREX and BRILA printed.
  Went wrong: importing speakers_render.py for its bake helpers ran that whole job and overwrote four approved
  speaker stills (video-local is not in git; the new renders are of the same model). The mouse was first built
  backwards; the outline check caught it. My review: the mouse's thumb wheel read as a jagged fin and the
  Apollo's meter window and knob ring should be one black shape; one 25-minute fix round. Apollo moved 2.5 cm
  off the monitor pole for its rear cables.
- Mouse rebuilt on Sircher's CC BY scan (owner downloaded it in Safari): the scan agrees with Logitech's size
  within 1.3 %. Our own quad shell is wrapped onto it (blender/assets/mouse/), the scan stays local. Scan
  silhouettes pass at 0.983 (thumb, right side). The first pass still had the USB-C missing, the thumb wheel
  sticking out and a white nose; one more round fixed them. The owner watched it live and asked to be chimed.

## 2026-10-28

- Owner asked for the mesh chair next, then to use Fable as the designer agent. The Aeron build was
  started twice (Opus, then Fable) and stopped by the owner before any file was written: "stop for now
  we'll start later". The brief is saved as handover/chair-brief.md so it resumes without re-planning.
- 23:06: the Claude session restarted and the chair builder was lost with it, 10 minutes in, before any file
  was written (only PROGRESS.md's first line). Restarted on Fable at 23:07 with the same brief.
- 23:48: the Aeron's first pass landed in 41 minutes (Fable). Reads as an Aeron in silhouette, but my review
  sent six things back in one round: the seat was a flat square tray, the back nearly straight, the arms
  straight bars, the mechanism a white plastic box, the weave coarse, the kalder mark too faint. Went wrong
  in the build: a Cycles crash from setting the Metal device under --factory-startup (removed); the compare
  masks swallowed the see-through mesh, so the IoU numbers are low even where the overlay fits.

## 2026-10-29 (night, unattended; the owner pre-approved the plan)

- The Aeron: fix round 1 (8 min) fixed the back curve, the mechanism, the weave and the mark; round 2
  (4 min) gave the seat a slim rail and uniform see-through mesh over a dark pan, and thicker arm supports.
  Both rounds used, so the chair stops here for the owner's judgement: the seat still reads tray-like in
  close-up and the arms slimmer than the real castings. Committed and placed in the room.

- Keyboard legends (Fable, 25 min, one review round): every cap printed from a legend atlas, Montserrat
  SemiBold, symbols drawn as shapes; all 81 keys still separate. My check: layout and glyphs all right; the
  ink reads a shade light in EEVEE, fine in Cycles. Accepted without a fix round. Went wrong: the export
  overwrote the desk-top group's atlas copies in the 2026-10-26 footage folder (same pipeline, no harm).
- 00:20: the session restarted a second time tonight and the wall-group builder was lost with it, 7 minutes
  in, nothing written. Restarted at 00:22 with the same brief, told to save its script within 10 minutes.
- 00:44: a third session restart killed the wall builder mid-review. This time its script survived
  (blender/components/wall.py, all five parts built, stills and 7 close-up pairs rendered); export, the
  compare and the room placement did not run. Weekly usage reached 93%, over the 92% line the plan set,
  so it is not restarted tonight; the script is committed as work in progress. Resume: run wall.py's
  review, export and room stages (see handover/phase-4-brief.md next steps).
- The owner asked why AI can't model an exact replica of a complex object and what the bottlenecks are,
  then for a researched essay on language models versus world models. Draft written to
  docs/drafts/world-models-essay.md for the owner to edit; not in content/posts until they approve.
