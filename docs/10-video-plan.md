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
