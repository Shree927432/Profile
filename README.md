# My Website

An interactive personal site that feels like a place you can explore, built in layers
so it is always online and always growing.

- Inspiration and reference: felixrieseberg.com (see docs/01-reference-felix-site.md)
- Our own premise: see docs/00-vision.md
- Current phase: see docs/03-roadmap.md

## Folder map

| Path | What it is |
|---|---|
| `CLAUDE.md` | Instructions for any AI agent or new collaborator. Read first. |
| `docs/` | Everything we know and have decided. Portable to any machine or agent. |
| `content/` | Projects, posts, about, links. The single source of truth for words. |
| `scene/objects/` | The contract every interactive object follows, and later the objects. |
| `src/` | The Astro static site. Run `npm install`, then `npm run dev`. |

## Working from another machine or agent

Clone this folder (it is a git repository). Open it with any agent. Tell it:
"Read CLAUDE.md and docs/03-roadmap.md, then continue the current phase."
Everything an agent needs to know is in the files, not in anyone's chat history.

## Status (2026-10-19)

Phase 1, almost done. The Astro static site is built and works locally. Lighthouse
mobile scored 100 on performance, accessibility, best practices and SEO.

Run it:

    npm install
    npm run dev        # http://localhost:4321
    npm run build      # output in dist/

### Where we left off

Done:
- All six pages, one layout, one stylesheet, dark and light, room hook on home.
- `/content.json` generated at build for the future room.
- Real links in `content/links.json` (resume still empty, so it is hidden).
- First real post: `content/posts/nobody-starts-from-zero.md`. Check its date
  and summary, and that you are happy with the personal details being public.
- About page, tagline and home intro written (2026-10-19).
- Three real projects: CI diagnosis MCP server, GST reconciliation, small model
  fine-tune (in progress). Example project and post deleted.
- Live on Cloudflare Pages at https://shrikantpawade.pages.dev. Every push to
  main redeploys.

Next, in this order:
1. Add the custom domain in Cloudflare Pages, then set `site` in `astro.config.mjs`.
2. Phase 2 done: posts screen live on desktop and phone.
   Phase 3 (the Three.js room shell) is paused. Unfinished work is on the branch
   `phase-3-room-shell`. Resume from `handover/phase-3-brief.md`.
3. Update the fine-tune project page as the 30-day plan moves (repo link, scorecard).

To resume with any agent, open `handover/START-HERE.md` and paste the prompt in it. 
