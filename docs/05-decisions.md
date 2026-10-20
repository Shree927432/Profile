# Decisions

Append only. Date, decision, why. Agents read this before starting and add to
it before finishing. Re-opening a decision needs the owner's say-so.

| Date | Decision | Why |
|---|---|---|
| 2026-10-16 | Layered build: content → Astro static site → optional Three.js room. | The static site must always work; the room is a layer. Same shape as the reference. |
| 2026-10-16 | Plain Three.js ES modules for the scene. No React, no game engine. | Fewer moving parts, matches the reference, easy for any agent to pick up. |
| 2026-10-16 | Astro for the static site. | Markdown in, HTML out, zero client JS by default. |
| 2026-10-16 | One file per interactive object, contract in scene/objects/CONTRACT.md. | Lets parallel sessions work without collisions. |
| 2026-10-16 | Content lives only in content/. Never hard-coded in pages or scene. | One source of truth for both layers. |
| 2026-10-16 | Do not copy the reference's premise (90s journalist desk) or its VHS tapes. | Our own place, our own objects. |
| 2026-10-16 | Version 1 ships with at most 10 interactive objects. | Fully working beats many half working. |
| 2026-10-16 | Phase 1 site uses Astro 7 with zero client JS and system font stacks (no web fonts at all, under the two-font limit). | Fastest possible load; Lighthouse mobile scored 100/100/100/100 on home and a project page. |
| 2026-10-16 | Pages use clean URLs without trailing slash (`/projects/foo`, built as `foo.html`). | Short links, works on Cloudflare Pages and Vercel without rewrites. |
| 2026-10-16 | `content.json` is emitted by an Astro endpoint (`src/pages/content.json.ts`) into `dist/content.json`, served at `/content.json`, instead of writing a file into `public/`. | Same URL for the room, works in dev and build, no generated file to keep out of git. |
| 2026-10-16 | `scene/` stays at the repo root; a small Astro integration (`src/integrations/scene-files.mjs`) serves it at `/scene/` in dev and copies it to `dist/scene/` on build. | Keeps the architecture layout. `boot.js` loads from `/scene/boot.js` as the hook specifies. |
| 2026-10-16 | Added `content/site.json` (name, tagline, intro, description) for home page text and site title. | Rule: no text hard-coded in pages. Documented in content/README.md. |
| 2026-10-16 | Colour theme: warm off-white and near-black, orange accent, from `prefers-color-scheme` only (no toggle). | Taste placeholder, easy to change in the `:root` variables of global.css. Owner may want a different palette. |
| 2026-10-16 | Model per task from docs/08-model-guide.md; agents builder (Sonnet), designer (Opus), quick (Haiku) in .claude/agents/. | Start cheap, move up on evidence; keeps usage for taste-heavy phases. |
| 2026-10-19 | Hosting: Cloudflare Pages, connected to the GitHub repo, live at https://shrikantpawade.pages.dev. Every push to main redeploys. `site` in astro.config.mjs points there until a custom domain exists. | Owner's choice. Free, no config file needed for a static Astro build. |
| 2026-10-19 | Node pinned to 22.22.0 in `.node-version`. | Astro 7 needs Node 22.22 or newer; Cloudflare's build reads the file. |
| 2026-10-19 | A 404 page (`src/pages/404.astro`), text in `content/site.json` under `notFound`. | Without it Cloudflare Pages serves the home page with status 200 for every unknown address. |
| 2026-10-19 | Premise: the owner's room in Pune, a bedroom turned music studio, with a wall of guitars, an upright piano (not digital), and a desk with monitor, speakers and mic. Chosen from the owner's own reference photo over the three sketched options. Object list and time of day are in docs/00-vision.md. | The owner picked the room. It is personal (pianist, guitars, the AI work at the desk), one room keeps Phase 4 small, and it is not a desk at night like the reference. |
| 2026-10-19 | Reference photos from the web live in `docs/moodboard/local/`, which git ignores. | The repo is public. The photos are not ours to publish. |
| 2026-10-19 | Owner confirmed the nine objects, the 5:40 a.m. setting, mood and sound, and the current pick (instruments really play; window follows Pune time and weather; the plant grows on return visits). | Owner's approval in chat. |
| 2026-10-19 | Phase 2 posts screen: `scene/objects/monitor-posts.js` (screen module), run on the home page by `scene/screen-host.js` on a 640×400 canvas, mounted by `scene/boot.js` into `#screen-slot`. The static posts list stays for everyone. Look follows the room sketch's monitor: navy screen, light blue system monospace. | Uses the contract once for real before Phase 3. Built by the builder agent, reviewed and tested here. |
| 2026-10-19 | Screen contract `mount()` gains two fields: `reduce` (prefers-reduced-motion) and `say(text)` (one line for screen readers). Screen text lives in `content/site.json` under `screens.posts`. | Screens need the same reduced-motion and screen-reader hooks room objects get through ctx. No text in scene code. |
| 2026-10-19 | `html.js` class set by an inline script in the home page head; `#screen-slot` shows and reserves 16:10 only with it. | No layout shift, and without JavaScript the home page looks exactly as before. |
| 2026-10-19 | On phones the posts screen keeps the 16:10 shape but uses a 400×250 canvas and shows titles only, in bigger text. The host picks the size when the slot is narrower than 480px; the module switches layout when its width is under 500. | Owner's choice: the full layout's text was too small to read on a 375px phone. |
| 2026-10-19 | Three.js comes from npm, pinned at exactly 0.186.1. The scene-files integration serves and copies only the files the room needs to `/scene/vendor/three/`, loaded through an import map. | Owner's choice over vendoring files in git or a CDN. Version in package.json, nothing large in git, no third-party server at runtime. |
| 2026-10-19 | Until the real room model exists (Phase 4), the room starts only when the home page URL has `?room`. Everyone else gets the Phase 2 page. | A test box is not something visitors should land on. |
| 2026-10-21 | Phase 3 room shell done, built step by step by the builder agent, reviewed and tested here. `scene/desktop.js` (renderer, camera, orbit, bloom, input), `scene/placeholder-room.js` (desk and monitor until the Phase 4 GLB), `scene/pick.js` (pick map, passed to objects as `ctx.interact`), `scene/quality.js` (ladder). Words in `content/site.json` under `room`. | Follows handover/phase-3-brief.md. Each piece is its own file so Phase 4 swaps only the placeholder. |
| 2026-10-21 | In the room, phones (under 480 px wide) get the narrow 400×250 posts screen, titles only, same rule as the Phase 2 screen. | At 640×400 the text on a 375 px phone was about 9 px. |
| 2026-10-21 | While the room is on, the hidden page's links, header, footer and skip link leave the tab order (`tabindex="-1"`, restored on fallback). Tab goes: "Plain page" link, then the room. Screen readers still read the hidden page. | Keyboard users would otherwise tab onto invisible links. |
| 2026-10-21 | Quality ladder rungs: pixel ratio 2, 1.5, 1, 0.75. Bloom only above 1. Auto steps down when a 2 s window averages under 50 fps, back up after 10 s over 58. Smooth is ratio 1 without bloom. Constants at the top of `scene/quality.js`. | A starting point. Tune on a real mid-range phone in Phase 6. |
| 2026-10-21 | Placeholder room mesh names: `monitor_body`, `monitor_screen` (16:10, UVs bottom-to-top), plus `floor`, `wall_back`, `desk_top`, `desk_leg_*`, `monitor_neck`, `monitor_base`. The first two are fixed for Blender. | Code finds meshes by name only, so the GLB can replace the placeholder. |
| 2026-10-21 | Room speed and zoom fixes (owner approved after a phone test). No post-processing: plain `renderer.render()`, bloom replaced by a cheap additive halo plane behind the screen (made in `desktop.js`). The room draws only when something changed. Ladder rungs are pixel ratio only. Zoom is our own eased distance (0.55x to 1.6x of the fit) with wheel, ctrl+wheel and two-finger pinch. | Full quality dropped fps on phones (4x MSAA half-float target plus about ten bloom passes every frame); OrbitControls dolly is instant and its range was only 0.8x to 1.2x. |

## Open questions (move to the table when answered)

- Domain.
- Mesh naming scheme for Blender (decide before Phase 4).
