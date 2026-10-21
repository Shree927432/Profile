# Phase 4 brief (the room model in Blender)

Last updated: 2026-10-22, 02:00. Planning is done. A quality test of the upright
piano is done too (2D sheet approved, 3D model, five stills, a build clip; see
`video-local/footage/2026-10-22-piano-quality-test/` and the 2026-10-22 journal
entry). The scripts in `blender/` are the start of the real build. Next: the owner
judges the quality bar and the web-export question (docs/05-decisions.md, open
questions), then Step 1 below.

## Context to read first

- `docs/00-vision.md`: the premise and the nine objects. Since 2026-10-21 the room
  tells the evolution of music: six era guitars (three on the wall, three on a floor
  rack), an 88-key upright piano with both lids opening, a studio desk with a
  two-deck DJ controller and a K-pop lightstick. 5:40 a.m., blue pre-dawn light.
- `scene/objects/MESHES.md`: the name list Blender and the code both follow
  (conventions, `obj_*` roots, pivots, the screen-UV rule and its TOP test, export
  settings, lights, cameras, counts). Final.
- `docs/05-decisions.md`: the 2026-10-21 rows explain every choice above.
- `docs/10-video-plan.md`: the making-of video (Moonlight Sonata, storm then dawn).
  Every step saves footage, as it describes.
- `docs/build-journal.md`: keep adding entries (CLAUDE.md rule).
- References, local only, never in git: `docs/moodboard/local/` (the owner's room
  photo, the approved guitar sheet, a desk-and-rack photo, a two-deck controller).
- `docs/moodboard/room-sketch.html`: layout and rough colours.

## Environment (already set up on this Mac)

- Blender 5.2.2 at `/Applications/Blender.app` (installed with Homebrew).
  Headless: `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python <script>`.
  Cycles sees the Metal GPU (Apple M2 Pro).
- FFmpeg 9 (Homebrew), for footage.
- Headless Chromium for WebGL screenshots and recordings:
  `~/Library/Caches/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-mac-arm64/chrome-headless-shell`
  with `--use-angle=metal --enable-gpu --ignore-gpu-blocklist`. The capture script
  from the first timelapse is in `video-local/scripts/capture.mjs`.
- The in-app browser pane: when hidden it runs about one frame a second, and sizes
  emulated larger than the pane scale WebGL and click coordinates wrongly. Test at
  the pane's own size, or use headless Chromium.

## Step 1: room shell, desk, monitor, and the TOP test (next)

Agent: designer (Opus, high). Goal: prove Blender to website end to end with the
smallest real slice of the room.

1. Scripts in a new `blender/` folder: one entry script (`blender/build.py`) that
   builds from scratch, checks every name against MESHES.md, saves a .blend and
   exports the GLB; shared helpers in `blender/lib/` (name checks, the screen-UV
   helper, simple materials); one script per prop group (now: `set_room`,
   `set_desk`, `obj_monitor`). One rebuild command, written in `blender/README.md`.
2. Room shell at real dimensions in metres: floor, walls, ceiling, window opening
   on the back wall. Propose the dimensions (none exist yet) as named constants.
3. Desk and monitor: `monitor_body`, `monitor_screen` (16:10, the UV rule exactly),
   `monitor_static`. The monitor faces straight out from the back wall.
4. TOP test: `monitor_screen` gets a generated "TOP" plus arrow texture. Prove it
   shows upright in three.js, then that the posts canvas does too.
5. Export `scene/assets/room.glb`. Keep the .blend out of git (the scripts are the
   source). Report the GLB size.
6. Load it behind a flag so the live site does not change: `/?room&glb` uses
   GLTFLoader and the GLB; without the flag the placeholder stays. Serve only the
   loader files needed from `src/integrations/scene-files.mjs` (GLTFLoader.js and
   the two utils it imports), not the whole 2 MB `loaders/` folder. A `uvtest`
   param keeps the GLB's own TOP texture visible.
7. Stills from the hero camera (clay, wireframe, simple blue-hour lit) at
   1920x1080, saved under `video-local/footage/<date>-room-shell/` with a note.

Done when: one command rebuilds the GLB; `/?room&glb&uvtest` shows TOP upright;
`/?room&glb` shows the posts upright and the glide still opens a post; `/?room`
and `/` are unchanged; no console errors; `npm run build` passes. Then show the
owner the stills, record the decisions (scripts layout, .blend ignored, GLB
committed, dimensions, the flag), commit.

## Later steps (one at a time, owner reviews stills after each)

2. Guitars: three on the wall, the floor rack beside the desk, six guitar models in
   each era's style (no logos or trademarked graphics). Stills decide which side of
   the desk the rack stands on.
3. Piano: upright, 88 keys, key cover and top lid opening, strings and hammers inside.
4. Studio desk: the two studio monitors, the two-deck DJ controller, the audio
   interface with pan and volume, the lightstick.
5. Mic on its arm, three picture frames, ceiling light, window, plant on the sill,
   bed, bookshelf, rug, panels.
6. Lighting: blue-hour bake with Cycles into atlases; night and sunrise setups for
   the video only.
7. The full room in the site on a phone: under 3 s on 4G, 60 fps on a mid-range
   phone (measure draw calls; merge at load if needed, as MESHES.md describes).
   Then the room replaces the placeholder at `/?room`.

## Open questions for the owner

- Which side of the desk the guitar rack stands on (decide from Step 2 stills;
  recommended: by the right studio monitor).
- Video recording: MIDI keyboard plus audio, or audio only?
- Which piano pieces per era (examples in docs/00-vision.md).
- Large assets: when the GLB and textures grow, git-lfs or a CDN bucket (see
  docs/02-architecture.md). Ask before setting either up.

## How to resume

    cd ~/Documents/My_website
    git pull
    npm install

Then paste the prompt from `handover/RESUME-PROMPT.txt` into a new session.
