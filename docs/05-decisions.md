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

## Open questions (move to the table when answered)

- Domain.
- Mesh naming scheme for Blender (decide before Phase 4).
