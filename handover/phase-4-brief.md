# Phase 4 brief (the room model in Blender)

Last updated: 2026-10-26. Read this first when resuming Phase 4.

## Where it stands

- **Premise (changed 2026-10-23/24):** half AI lab, half music studio. The site opens on the sky and
  the city through the window; a click pulls the camera back into the room and turns it to the AI lab,
  laid out exactly as the owner's photo `docs/moodboard/local/ai-desk-reference-1.jpg`. The music side
  (piano, guitars, rack, DJ controller) is a secret, revealed with About. Rows in `docs/05-decisions.md`
  from 2026-10-23 on explain every choice.
- **Layout:** plan v3, approved. Numbers and 82 clearance checks in `blender/lib/plan_v3.py`
  (`cd blender && python3 -m lib.plan_v3`), sheet `blender/design/room_plan_v3_sheet.py`, blockout
  `blender/design/room_plan_v3_blockout.py`, images in `video-local/footage/2026-10-24-room-plan-v3/`.
  Desk at 76.5 cm on 3 cm risers; screens and pegboard raised to match. Cameras: INTRO (out of the
  window), HERO_V3 (the photo's angle), ABOUT (the music side), phone.
- **Components (built one by one, away from the room, before placing them):**

| Component | State | Files |
|---|---|---|
| Screens: Samsung G8 34 + Apple Studio Display 27 on a pole, ScreenBar Halo 2 | approved (round 2b) | `blender/components/screens*.py` |
| Speakers: ADAM A7V pair, gloss white, desk-pole mounts (ISO-155 alternative) | approved | `blender/components/speakers*.py` |
| Desk: LAGKAPTEN L top on three ALEX units, 3 cm risers, LED strip | approved | `blender/components/desk*.py` |
| PC: Lian Li O11 Vision white, white build, RTX 5090 FE (`obj_rig`) | approved; glass and blue-white glow fixed 2026-10-26 | `blender/components/pc*.py` |
| Camera (ZV-E10 II), Flex Arm, two Key Lights, mic (MV7+ white on PSA1+ white) | approved; placement B in plan v3 (shelf at 1.95) | `blender/components/arms.py` |
| Apollo x4 (Gen 2 silver), Keychron Q1 Max, MX Master 3S, Stream Deck MK.2 white | approved; mouse rebuilt on a CC BY scan and approved "for now" (2026-10-26); keyboard legends to do | `blender/components/desktop.py`, `mouse_scan.py`, `blender/assets/mouse/` |
| Shelf and three frames, hanging plants, SKADIS pegboard + ATH-M50x, neon (words from content), Nanoleaf triangles | to do | |
| MacBook Pro 16 on Rain mStand, DJ controller (DDJ-FLX4 shape), K-pop lightstick | to do | |
| Herman Miller Aeron, Mineral (hardest) | to do | |
| Guitars: 01 Lucille, 03 Page double-neck, 05 Hetfield Explorer, 06 Henson TOD10 | to do (02 Strat and 04 Number One done) | `blender/props/guitar_0*.py` |

  Brand names: every approved component carries an invented name in place of the real logo, from
  `content/room-brands.json`, printed by `blender/lib/brands.py` in the owner's lookalike fonts
  (`blender/assets/fonts/`, OFL). Room test: `blender/design/room_v3_component_test.py` places every
  approved component at plan v3's numbers (hero.png, desk-corner.png, room-v3-test.glb in
  `video-local/footage/2026-10-26-component-test/`).
  Each component's GLBs (rich for renders, lite for the web) are in `blender/out/components/`
  (git-ignored, rebuilt from the scripts); stills, compare sheets and NOTE.md in
  `video-local/footage/2026-10-24-components/<name>/`.
- **The room itself:** `scene/assets/room.glb` on main is still the v1 room shell (with guitar_02 and
  guitar_04). A rebuild to plan v2 stalled halfway and is kept on branch
  `wip/room-rebuild-v2-stalled` for its useful parts (obj_rig.py, video/stills.py, window rebuild,
  posts screen on the 27-inch, hero camera wiring). Do not merge it; rebuild from plan v3.

## How a component is built (the pipeline)

Full commands: `blender/README.md`, section "Component pipeline". In short:

1. References: `docs/moodboard/local/ai-lab/<NN-name>/` (photos, SOURCES.md with official sizes,
   MODELS.md). Lens-correct photos with `blender/lib/refs.py`; trace on true-scale backdrops
   (`blender/lib/backdrops.py`).
2. Start from `blender/tools/component_template.py`. Parts from `blender/lib/parts.py`.
3. Outline check (`blender/tools/outline_check.py`) about 15 minutes in, gate 0.96.
4. Detail, then the every-angle compare test (`blender/lib/compare.py`, 0.98 per angle or EXPLAINED),
   the photo-vs-model sheet with a top row, close-up pair sheets of the key details.
5. ONE complete review of every close-up, all fixes in one round, then the coordinator's own full
   review before the owner sees it.
6. Export rich and lite. Report: table of angles, sizes, proposed mesh names, credits, what went wrong.

Rules the owner set: Blender runs headless (`-b`) always; one heavy Cycles render at a time
(`blender/lib/renderqueue.py`); every build has a time box and re-renders only the stills a fix
touches; no logos, brand names or printed text on any model; exact replicas in shape and finish.
The builder brief that agents read is kept in this file's spirit; give each builder this section,
the component's reference folder, an approved component as a pattern, and a time box.

## Next steps, in order

0. The Aeron chair, started 2026-10-28 on Fable at the owner's request and stopped the same day before any
   file was written ("stop for now we'll start later"). Resume it first: the full brief is in
   `handover/chair-brief.md`; name "kalder" proposed in content/room-brands.json.
1. Keyboard legends on the Keychron (letters, numbers, F-keys, Mac symbols), stopped on 2026-10-26 when the
   owner put the mouse first; brief: print them as on the white Q1 Max photos, fonts from blender/assets/fonts.
2. Mouse leftovers, only if the owner asks: the thumb pocket reads dark from directly above, the wheel slot
   lacks its white frame, the shell sits 1 to 2 mm inside the official size.
3. The wall group: shelf and three frames, hanging plants, SKADIS pegboard + ATH-M50x, neon (words from
   content), Nanoleaf triangles. Then the return desk (MacBook on mStand, DJ controller, lightstick), then the
   Aeron. Each gets an invented brand name in content/room-brands.json first.
4. Fold the proposed mesh names into `scene/objects/MESHES.md` (its section "Proposed names").
5. Rebuild the room from plan v3 with the real components; owner judges the layout by eye.
6. Lighting pass: the room renders too bright (washes out the PC glow and the glass); set exposure, an
   environment map for glass and gloss, bake.
7. Site: the intro (window, city) → zoom out → AI lab → About reveals the music side; posts on the
   Studio Display; `obj_rig` (PC fans pulse) as the tenth object; piano lid limited to 60 degrees.
8. The four remaining guitars, phone performance (under 3 s on 4G, 60 fps mid phone), then the new room
   replaces the placeholder at `/?room`.

Tools added 2026-10-26: `blender/tools/live_watch.py` (one Blender window that rebuilds a component on every
save, for the owner to watch), `video-local/viewer/` pages (local): `index.html?f=<glb>&only=<part>&exp=<n>`,
`compare.html` (real photos beside the live model), `fonts.html`, `live.html?d=<footage folder>`
(newest renders), `sketchfab-ref.html` (exact views of a view-only Sketchfab model via its embed API).
The owner wants a chime when input is needed: `afplay /System/Library/Sounds/Glass.aiff` before ending such
a turn (a Notification hook in `.claude/settings.local.json` does it for permission prompts).

## Open questions for the owner

See `docs/05-decisions.md`, section "Open questions".

## Environment on this Mac

- Blender 5.2.2: `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python <script>`.
  Cycles on the Metal GPU (M2 Pro); it can stall when two Cycles jobs run at once (use the render queue).
  Blender 5.2's glTF importer fails on our GLBs ("Iridescence Factor"); check GLBs in the browser viewer.
- Python with Pillow and numpy: `/opt/anaconda3/bin/python3` (the `python3` on PATH has no Pillow).
- macOS has no `timeout` command; a wrapped command silently never runs.
- Headless Chromium: `~/Library/Caches/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-mac-arm64/chrome-headless-shell`
  with `--use-angle=metal --enable-gpu --ignore-gpu-blocklist`.
- GLB viewer: `.claude/launch.json` "glb-viewer" serves the repo on port 8765; the page is
  `video-local/viewer/index.html` (local only).
- The Mac runs on battery unless the owner plugs in; check `pmset -g batt` before long runs.

## Changing an approved component later

Every component is rebuilt from its script, so any change is an edit plus a re-run, never hand work in a .blend:
- the part's script in `blender/components/` (e.g. `desktop.py` with `DESKTOP_PART=mouse`), run headless with the
  stages its docstring lists (outline, build, stills, compare, closeups, export);
- brand names and fonts in `content/room-brands.json`; layout numbers in `blender/lib/plan_v3.py`;
- the mouse body: `blender/components/mouse_scan.py` re-wraps the shell from the local scan
  (`docs/moodboard/local/ai-lab/23-mouse/scan/`, not in git; re-download from Sircher's Sketchfab page if lost).
  The committed shell (`blender/assets/mouse/mx-master-3s-shell.json`) means ordinary rebuilds never need the scan.
Then re-run `blender/design/room_v3_component_test.py` so the room picks it up.

