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

## Open questions (move to the table when answered)

- The premise sentence.
- The object list.
- Hosting: Cloudflare Pages or Vercel.
- Domain.
- Mesh naming scheme for Blender (decide before Phase 4).
