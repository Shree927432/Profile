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

## Open questions (move to the table when answered)

- The premise sentence.
- The object list.
- Hosting: Cloudflare Pages or Vercel.
- Domain.
- Mesh naming scheme for Blender (decide before Phase 4).
