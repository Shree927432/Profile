# Phase 3 brief (paused 2026-10-19)

Status: paused at the owner's request. Work so far is on the branch
`phase-3-room-shell` (not merged, not reviewed). The live site is Phase 2.

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
