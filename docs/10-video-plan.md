# The making-of video

Written 2026-10-21. The goal is a video that goes past Felix's "redesign in 90
seconds" (see docs/01-reference-felix-site.md). His is a fast montage of process
footage. Ours is the room building itself inside one continuous world, cut to the
owner's own piano playing.

## The idea in one sentence

The room in Pune assembles itself in a storm to the third movement of Beethoven's
Moonlight Sonata, then everything stops, and the first movement plays while first
light fills the finished room at 5:40 a.m.

## Music (decided 2026-10-21, owner's choice)

Beethoven, Piano Sonata No. 14 in C-sharp minor, Op. 27 No. 2, played by the owner.

| Section | Excerpt | Role |
|---|---|---|
| 1. Storm | 3rd movement (Presto agitato), from the start, about 60 to 75 s | The room builds. Each rising arpeggio carries the camera; each pair of accented chords snaps an object into place. |
| 2. Silence | About 1 s | The cut between the two worlds. |
| 3. Dawn | 1st movement (Adagio sostenuto), from the start, about 30 to 40 s | The finished room at first light. Slow drift, no more building. |

Both halves come from the same sonata, and the video ends on the premise: quiet,
focused, lived-in.

Recording:
- The composition is public domain. The recording must be the owner's own: never
  a commercial recording, which is copyrighted even when the piece is not.
- Best: MIDI from a digital keyboard plus the audio, in one take per movement.
  MIDI gives the exact time of every note, so cuts and the room's piano keys land
  on the real notes. Audio alone also works; then bar times are marked by hand.
- Tempo is free. The edit follows the recording, not a click track.
- The two movements are recorded separately; the silence between them is made in
  the edit.

## Shot plan

| Time (approx.) | Music | Picture |
|---|---|---|
| 0:00 | Silence | Black. A small REC counter fades in, the date of the first commit. |
| 0:02 | Presto, first phrases | Night. The empty shell of the room in wireframe: floor, walls, the window as a dark frame. The camera rides each arpeggio upward. |
| ~0:10 | Accented chords | The desk, then the monitor snap in: wireframe, clay, lit, in the length of one chord pair. The monitor plays the site's history as screen recordings (Phases 1 to 3). |
| ~0:25 | Presto continues | The studio desk (the two studio monitors, the DJ controller with its pads flashing on the accents, the K-pop lightstick), the mic on its arm, the bookshelf with the picture frames, the bed. One object per chord pair. |
| ~0:40 | Rising intensity | The guitars through the eras: on the wall the archtop, the white Strat-style and the worn sunburst, each lifting off its hook for a moment; then the floor rack fills: flame-top single-cut, Explorer-style, modern mauve, one dropping into the rack per accent. |
| ~0:55 | The phrase's peak | The upright piano last. The top lid opens, the hammers strike, the keys play the Presto notes in sync. |
| ~1:10 | Silence, about 1 s | Hard cut. The room is complete and still. The REC counter jumps to 05:40. |
| ~1:11 | Adagio, opening triplets | Slow drift from the bed toward the window. First light rises, the plant on the sill catches it, the piano keys move with the triplets. |
| ~1:45 | Adagio fades | The camera settles on the monitor. The live site is on it. End on the REC counter showing shrikantpawade.pages.dev. |

No slides, no captions. The only overlay is the small REC counter, in the room's style.

The room's theme since 2026-10-21 is the evolution of music (docs/00-vision.md). The
video keeps the Moonlight Sonata for its soundtrack; the guitars and the studio desk
appear in the build but do not play over it.

## Three outputs

| Output | What | Length |
|---|---|---|
| Master | The full storm-to-dawn shot above | 1:40 to 2:00, 16:9 |
| Phone cut | The storm only, on a real phone in hand: the room loading, the glide into the monitor, the instruments playing | 30 s, 9:16 for Reels and LinkedIn |
| Teaser | The silence and the first dawn seconds only | 10 to 15 s, for a link preview |

## Footage to capture during Phase 4 and 5

**Changed 2026-10-23 (owner's decision): light captures now, one directed shoot at the
end.** Everything in the room is built by scripts, so any shot can be re-rendered at
any time. Polished footage is therefore made once, in Phase 7, when the room is
finished, the camera direction is settled and the owner's Moonlight Sonata recording
sets the timing. During Phase 4 and 5 each build step keeps only a process record:
- a few Cycles stills of the new part (clay, wireframe, lit), and
- one quick, low-resolution build preview (EEVEE, low samples, a single camera,
  minutes not hours), plus
- the commit the scripts were at, written in the folder's NOTE.md, so any step can be
  re-rendered later from its own version.
The multi-camera, camera-direction and Moonlight sections below describe the final
shoot, not each step. The room-shell hero clip of 2026-10-22 is kept as the first
example of that look.

Every agent working on the room saves footage as it goes, so the video never
needs a reshoot of the process.

- Where: `video-local/footage/<YYYY-MM-DD>-<step>/` (git ignores `video-local/`).
- Blender: for each prop group, a still at wireframe, clay, textured and lit;
  plus a 120-frame turntable at 1920x1080 for anything new.
- A build sequence for each prop group (added 2026-10-21, owner's request): the
  parts appear in build order while the camera pushes in, rendered as glowing
  wireframe, then crossfading to clay, then to lit, MP4 at 1920x1080 30 fps. The
  first one is the piano test in `video-local/footage/2026-10-21-blender-test/`,
  made by `video-local/blender-test/build_sequence.py`; reuse its approach (parts
  scale in with a slight overshoot, keys sweep low to high). These clips are the raw
  material for the storm section.
- Build every prop so it can be shown in all four states (wireframe, clay,
  textured, lit) from the same file. The storm section needs them.
- One fixed "hero" camera path in the Blender file, used for every lighting
  iteration, so iterations can be cut together later.
- Three lighting setups: night (storm), 5:40 a.m. blue hour (the default room bake),
  and a full sunrise (`lights_sunrise` in scene/objects/MESHES.md) used only for the
  video's dawn section.
- The site: a short headless screen recording (1920x1080 and 390x844) of each
  object once it works. The capture script from the first timelapse is in
  `video-local/scripts/capture.mjs`.
- A one-line note per folder: what changed, which commit.

### Multiple cameras and better animation (added 2026-10-22, owner's request)

Changed 2026-10-22 night, after the room shell's first clip: each build step keeps only
light process captures (a few stills, one quick low-resolution build preview); the
directed, multi-camera, music-timed shoot below happens once, at the end.

Every build step from the room shell on renders its build sequence from several
cameras, so the final edit can cut between angles instead of holding one shot:
- **Hero:** the room_view the site opens on, a slow push-in.
- **Low wide:** near the floor, wide lens, looking up at the part as it lands.
- **Orbit:** a slow arc of 60 to 90 degrees around the part being built.
- **Detail:** a close macro with shallow depth of field on one moment (a key, a
  hinge, the emblem, a pad lighting up).
- **Top-down:** for the room shell and the floor plan becoming the room.
All cameras watch the same animation, so the angles match and can be cut together.

Animation quality:
- Parts land with eased motion: a drop or slide-in with a small overshoot and settle,
  staggered so groups ripple rather than pop together. Nothing appears in one frame.
- Cameras move on eased paths with no sudden starts or stops.
- Clean frames: no text, no counters, no UI. Titles happen in the edit only.

### Camera direction (added 2026-10-23, owner's feedback)

The first room-shell clips were too static: each camera held one slow move. From the
next build step on, every shot is directed like a professional camera, not parked:
- **Motivated moves.** The camera does what the moment needs: a push-in to a close-up
  as a part lands (a hinge, a key, the emblem), a pull-out to reveal the room around
  it, a crane up or down, a dolly or tracking move alongside, an orbit only where it
  shows shape. Each shot has a start frame, an end frame and a reason.
- **Close and wide on purpose.** Alternate scales the way an editor needs them: wide
  establishing, medium, close, macro detail, then back out. Zoom by moving the camera
  (dolly) or changing the lens, not by a cheap digital zoom.
- **Real camera behaviour.** Eased acceleration and deceleration, a slight overshoot
  and settle at the end of fast moves, lens choices from 18 mm wide to 85 mm and a
  100 mm macro, depth of field with focus pulls (rack focus) from one part to the next,
  and a very subtle hand-held drift only where it adds life, off with reduced effort
  shots.
- **Moves land on the music.** Moves start and peak on the beat grid of the timing
  file: a push-in that arrives on an accented chord, a reveal that opens on a bar line.
- **A shot list first.** Before rendering, each step writes a short shot list (camera,
  lens, move, what it frames, which beat) and renders a fast, low-quality preview of
  all the moves cut together (an animatic, a few minutes in EEVEE at low resolution).
  The owner approves the camera work on that preview; only then the full renders run.
  Same rule as "2D before 3D": cheap to fix on the preview, expensive after.

### Built for the Moonlight Sonata edit (added 2026-10-22, owner's reminder)

The final edit is on the Moonlight Sonata, as decided: the storm (3rd movement,
Presto agitato) builds the room, then dawn (1st movement) shows it finished. So the
footage is made to be cut to music:
- **Timing from a table, not baked in.** Each build script reads its event times
  (when each part lands) from a small timing file. Until the owner's recording
  exists, the times follow a placeholder beat grid at the Presto's usual tempo (a
  bar about 1.5 s, the accented chords every second bar); later the real MIDI beat
  map replaces the file and the same scripts re-render in time with the playing.
- **Every landing on a beat.** The main parts land on the accented chords; small parts
  ripple on the eighth notes in between. The keys sweep like the arpeggios.
- **Handles.** Each shot starts 1 s early and ends 1 s late, so the editor can trim to
  the music.
- **Two looks per shot.** Storm footage in the night lighting (the building); dawn
  footage in blue hour turning to sunrise (the finished room, slow camera moves, no
  building), for the 1st movement.
- **30 fps, 1920x1080, one file per camera per step,** named
  `<step>-<camera>-<look>.mp4`, plus the timing file used.

## How it gets made

1. Owner records both excerpts (MIDI plus audio).
2. Turn the MIDI into a beat map: bar start times, accented chords, note onsets
   (JSON). The accents in the Presto are the build cues.
3. In Blender, key the camera path, the build steps and the piano keys to the
   beat map. Render with Cycles at 1920x1080, 24 or 30 fps.
4. Composite the monitor's screen recordings onto the screen in the render.
5. Mux the owner's audio with FFmpeg. Export the master, the phone cut and the teaser.

Tools: Blender (needed for Phase 4 anyway; ask before installing), FFmpeg
(installed 2026-10-21), the cached headless Chromium.

## Already made

- `video-local/build-timelapse-2026-10-21.mp4`: a 59 s card-style timelapse of
  Phases 0 to 3. The owner found it too much like a slideshow. That feedback
  is the reason this plan exists.
- `video-local/footage/2026-10-22-piano-quality-test/`: the first prop at the real
  quality bar: five Cycles stills of the upright piano (hero, keys close-up, lid open,
  clay, wireframe) and `piano-build.mp4`, a 13 s build sequence from
  `blender/tests/piano_quality.py` (wireframe, clay, lit; keys sweep, fallboard folds
  open, C major chord). Raw material for the piano's accent in the storm section.
- `video-local/footage/2026-10-22-room-shell/`: the room shell (Phase 4 Step 1):
  `room-shell-hero-storm.mp4` (the build from room_view, 24.5 s with handles; the owner
  found the camera too static), three Cycles stills (blue hour, clay, wireframe) and the
  timing file. The other four cameras and the dawn drift were stopped by the owner; their
  setups stay in `blender/video/room_shell.py` for the final shoot.

### The timing file (decided by use, 2026-10-22)

`blender/video/timing_room_shell.json`, one per build step. `grid` holds the beat grid:
`bar_s`, `beats_per_bar`, `accent_every`, and `bars`, which is null for the placeholder
and becomes the list of bar start times from the owner's MIDI beat map. Each event says
`bar` and `beat` (1-based, fractional for eighths), a `motion` (`rise`, `drop`, `slide`,
`unfold`, `grow`, `glow`), its `objects` (a name, or a list of names that move as one),
and optional `duration_beats`, `stagger_beats` (0.5 = an eighth note), `overshoot`,
`drop_m`, `offset`. `handles_s` and `tail_bars` frame the shot; `detail` places the close
camera's moment; `storm_hidden` lists roots kept for the dawn. The script copies the file
next to the clips it renders.

## Update 2026-10-25: the new opening and the component footage

- The site and the final cut can share the opening: plan v3's INTRO camera (the sky and the city
  through the window), the pull-back to HERO_V3 (the AI lab, the owner's photo angle), and ABOUT
  (the music side revealed). Use these named cameras for the directed shoot.
- Every component now has a light process record in `video-local/footage/2026-10-24-components/<name>/`:
  hero, close-ups, clay, wire, the outline check and the photo-vs-model sheets. The "photo vs our
  model" pairs are strong material for the making-of: the real product beside ours, then the overlay.

## Update 2026-10-26: live building, names and the scan

- The owner watched the modelling live: one Blender window that rebuilt the arms on every save
  (`blender/tools/live_watch.py`) and a page of the newest renders (`video-local/viewer/live.html`). A
  screen recording of that window during a build is a good shot for the "how it was made" part.
- New sheet types worth showing: the logo pairs (real logo, Blender's default font, the owner's pick) in
  `video-local/footage/2026-10-26-components/brand-fonts/`, and the mouse's three-way sheet (scan, ours, real)
  in `.../desktop/mouse-scan/r4/threeway/`. The scan-to-model step reads well as a wipe.
- No change to the music or the shot plan.

