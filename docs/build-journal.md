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
