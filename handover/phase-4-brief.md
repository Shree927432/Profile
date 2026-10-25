# Phase 4 brief (the room model in Blender)

Last updated: 2026-10-25. Read this first when resuming Phase 4.

## Where it stands

- **Premise (changed 2026-10-23/24):** half AI lab, half music studio. The site opens on the sky and
  the city through the window; a click pulls the camera back into the room and turns it to the AI lab,
  laid out exactly as the owner's photo `docs/moodboard/local/ai-desk-reference-1.jpg`. The music side
  (piano, guitars, rack, DJ controller) is a secret, revealed with About. Rows in `docs/05-decisions.md`
  from 2026-10-23 on explain every choice.
- **Layout:** plan v3, approved. Numbers and 68 clearance checks in `blender/lib/plan_v3.py`
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
| PC: Lian Li O11 Vision white, white build, RTX 5090 FE (`obj_rig`) | built, waiting for owner approval | `blender/components/pc*.py` |
| Camera (ZV-E10 II on Flex Arm), mic (MV7+ white on PSA1+ white), key lights | next | |
| Apollo x4 (Gen 2 silver), Keychron Q1 Max, MX Master 3S, Stream Deck MK.2 white | to do | |
| Shelf and three frames, hanging plants, SKADIS pegboard + ATH-M50x, neon (words from content), Nanoleaf triangles | to do | |
| MacBook Pro 16 on Rain mStand, DJ controller (DDJ-FLX4 shape), K-pop lightstick | to do | |
| Herman Miller Aeron, Mineral (hardest) | to do | |
| Guitars: 01 Lucille, 03 Page double-neck, 05 Hetfield Explorer, 06 Henson TOD10 | to do (02 Strat and 04 Number One done) | `blender/props/guitar_0*.py` |

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

1. Owner approves the PC (view it: `preview_start` "glb-viewer", then
   `/video-local/viewer/index.html?f=blender/out/components/pc-lite.glb`).
2. Camera, mic and key lights (one builder, about 1.5 h, time-boxed).
3. The remaining components in the table, one at a time.
4. Fold the components' proposed mesh names into `scene/objects/MESHES.md` (see its section
   "Proposed names from the component builds").
5. Rebuild the room from plan v3 with the real components; owner judges the layout by eye.
6. Site: the intro (window, city) → zoom out → AI lab → About reveals the music side; posts on the
   Studio Display; `obj_rig` (PC fans pulse) as the tenth object; piano lid limited to 60 degrees.
7. The four remaining guitars, lighting bake, phone performance (under 3 s on 4G, 60 fps mid phone),
   then the new room replaces the placeholder at `/?room`.

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
