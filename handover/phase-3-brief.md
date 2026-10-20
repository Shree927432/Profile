# Phase 3 brief (done 2026-10-21)

Status: done. Built in four steps by the builder agent, reviewed, tested and merged
into main on 2026-10-21. The room shows only with `?room`; `/` is still Phase 2.
The rest of this file is the brief as it was written, kept for reference.

## Context to read first

Premise (from docs/00-vision.md): Shrikant's room in Pune at 5:40 a.m., a
bedroom that became a music studio, with a wall of guitars, an upright piano,
and the desk where the models get trained. Quiet, focused, lived-in.

- `docs/00-vision.md`: premise, setting, sound, the nine objects and what
  each click does. The Phase 3 box stands in for the desk monitor.
- `docs/04-ideas.md`: big bet (the instruments really play) and two surprises.
- `docs/moodboard/room-sketch.html`: the room layout and the monitor's look.
  Open it in a browser. Use it for rough colours only; looks come in Phase 4.
- `docs/moodboard/README.md`: what each reference is. The owner's photo is in
  `docs/moodboard/local/` on the owner's Mac only (not in git).
- `docs/05-decisions.md`, latest rows: Phase 2 screen, Three.js from npm, the
  `?room` gate.
- `scene/objects/CONTRACT.md` and the Phase 2 files: `scene/boot.js`,
  `scene/screen-host.js`, `scene/objects/monitor-posts.js`.

Mesh names: the placeholder uses `monitor_body` and `monitor_screen`. Keep
them; they become the first entries in the Blender naming list for Phase 4.

## Done on the branch
- `three@0.186.1` added to package.json (exact version, owner approved).
- `src/integrations/scene-files.mjs` serves `node_modules/three/build/` and the
  needed `examples/jsm/` addons at `/scene/vendor/three/` in dev, and copies
  them into `dist/scene/vendor/three/` on build. Build passes.

## Not done yet
1. Import map in the home page head: `"three"` and `"three/addons/"` to
   `/scene/vendor/three/...`.
2. `scene/boot.js`: Phase 3 checks, only when the URL has `?room`:
   reduced motion stays on the Phase 2 page with a "try anyway" link
   (`?room=force`); no WebGL2 stays with a note; otherwise hide `#static`
   visually (keep it for screen readers), show `#room`, load `desktop.js`,
   show a "plain page" link and a loading line. Any failure falls back.
3. `scene/desktop.js`: renderer, camera, resize; a placeholder group with a
   desk and a monitor (`monitor_body`, `monitor_screen` 16:10); OrbitControls
   with tight limits, no pan; bloom (subtle); `monitor-posts.js` mounted on a
   640x400 offscreen canvas as a CanvasTexture, updated only when `frame()`
   returns true; pick map + one raycaster, tap vs drag, UV to canvas click;
   wheel over the screen scrolls it; keyboard to the screen; quality ladder
   full / auto / smooth; `?debug` fps meter and level buttons; pause when hidden.
4. `content/site.json`: a `room` block for every visible word (loading, exit,
   try anyway, no WebGL, debug labels), documented in content/README.md.
5. Room and overlay styles in `src/styles/global.css`.

## Done when
`/` looks exactly like Phase 2. `/?room` shows the box room, clicking or
tapping the post row on the monitor opens the post, Enter works, orbit is
limited, the plain-page link works, no console errors. `/?room&debug` shows
fps and the level buttons work. Checked at 375px and with reduced motion.
Report the room's JavaScript size and fps.

## How to resume
    git switch phase-3-room-shell
    npm install

Then give this file to the builder agent (Sonnet, high effort per
docs/08-model-guide.md). Review, test, then merge into main.
