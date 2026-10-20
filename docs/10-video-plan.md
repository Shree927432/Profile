# The making-of video

Written 2026-10-21. The goal is a video that goes past Felix's "redesign in 90
seconds" (see docs/01-reference-felix-site.md). His is a fast montage of process
footage. Ours is one continuous shot inside the room, cut to the owner's own
piano playing.

## The idea in one sentence

At 5:40 a.m. in the room in Pune, the camera drifts through the dark studio while
first light comes up, and every object builds itself as the camera passes, in time
with a classical piece played by the owner.

## Three parts

| Part | What it is | Length | Made when |
|---|---|---|---|
| A. One shot at dawn | One continuous camera move through the Blender room. Each object goes wireframe, then clay, then textured and lit, then it works (a guitar lifts, the monitor plays the site's history as screen recordings). No cuts, no title cards. | 90 to 120 s, 16:9 | After Phase 4 and 5 |
| B. The piano drives it | The owner plays a public-domain piece. Bars and notes become events: a bar reveals an object, a chord change brings in a phase, the room's piano keys move with the playing. | Same as A | Recording any time; edit after Phase 5 |
| C. Proof on a phone | A real phone in hand: the room loads fast, the glide into the monitor, the instruments play. Cut to the same music. | 30 s, 9:16 for Reels and LinkedIn | After Phase 5 |

Only overlay allowed: one small recording counter in a corner (date, a red REC
dot), in the room's own style. No slides, no captions.

## The music

Rules:
- The composition must be public domain (the composer died more than 70 years
  ago). All the pieces below qualify.
- The recording must be the owner's own playing. Never use a commercial recording:
  performances are copyrighted even when the piece is not.
- Best: record MIDI from a digital keyboard while playing, plus the audio. MIDI
  gives exact note times, so every cut and key press lands on the real note.
  Audio alone also works; then bar times are marked by hand or by beat detection.
- Play freely. Rubato is fine, because the edit follows the recording, not a
  fixed tempo.

Candidates (owner picks, see the open question in docs/05-decisions.md):

| Piece | Period | Why it fits | Length to use |
|---|---|---|---|
| Bach, Prelude in C major, BWV 846 (Well-Tempered Clavier I) | Baroque | One chord per bar, same pattern every bar: each bar can build one thing. The calmest fit for "quiet, focused". | Full piece, about 2 min |
| Debussy, Clair de lune | Impressionist | Starts almost silent, opens up in the middle: matches dark room to first light. Very famous. | Opening to the first big arpeggios, about 2 min |
| Beethoven, Moonlight Sonata, 1st movement | Classical to Romantic | Slow, steady triplets, instantly known. Night more than dawn. | First 1.5 to 2 min |
| Mozart, Sonata in C, K. 545, 1st movement | Classical | Bright and quick. Better for the 30 s phone cut than for the dawn shot. | Exposition, about 1 min |
| Chopin, Nocturne in E-flat, Op. 9 No. 2 | Romantic | Lyrical, intimate, a pianist's piece. | First 1.5 min |

Current recommendation: Bach's Prelude in C for the dawn shot. Its bar-by-bar
regularity makes the build-up readable. Mozart K. 545 for the phone cut, if a
second piece is wanted.

## Footage to capture during Phase 4 and 5

Every agent working on the room saves footage as it goes, so the video never
needs a reshoot of the process.

- Where: `video-local/footage/<YYYY-MM-DD>-<step>/` (git ignores `video-local/`).
- Blender: for each prop group, a still at wireframe, clay, textured and lit;
  plus a 120-frame turntable at 1920x1080 for anything new.
- One fixed "hero" camera path in the Blender file, used for every lighting
  iteration, so iterations can be cut together later.
- The site: a short headless screen recording (1920x1080 and 390x844) of each
  object once it works. The capture script from the first timelapse is in
  `video-local/scripts/capture.mjs`.
- A one-line note per folder: what changed, which commit.

## How it gets made

1. Owner records the piece (MIDI plus audio).
2. Turn the MIDI into a beat map: bar start times, chord changes, note onsets
   (JSON).
3. In Blender, key the camera path and every object's build steps to the beat
   map. Render the dawn shot with Cycles at 1920x1080, 24 or 30 fps.
4. Composite the monitor's screen recordings onto the screen in the render.
5. Mux the owner's audio with FFmpeg. Export the 16:9 master and the 9:16 cut.

Tools: Blender (needed for Phase 4 anyway; ask before installing), FFmpeg
(installed 2026-10-21), the cached headless Chromium.

## Already made

- `video-local/build-timelapse-2026-10-21.mp4`: a 59 s card-style timelapse of
  Phases 0 to 3. The owner found it too much like a slideshow. That feedback
  is the reason this plan exists.
