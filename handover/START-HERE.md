# Start here (new session, new account, or new agent)

Last updated: 2026-10-19 (Phase 3 paused). Everything below is also on GitHub:
https://github.com/Shree927432/Profile

## 1. Get the project

On this Mac it is already at `~/Documents/My_website`. On another machine:

    git clone https://github.com/Shree927432/Profile.git My_website
    cd My_website
    npm install
    npm run dev        # open http://localhost:4321

Needs Node 20 or newer (built with Node 25).

## 2. Prompt to paste into a new Claude Code session

Open the `My_website` folder as the session's folder, then paste:

    Read CLAUDE.md, then docs/00-vision.md, docs/02-architecture.md,
    docs/03-roadmap.md, docs/05-decisions.md and docs/08-model-guide.md.
    Then read handover/START-HERE.md, the Status section of README.md and
    handover/phase-3-brief.md. Phases 1 and 2 are done and live. Phase 3, the
    Three.js room shell, is paused on the branch phase-3-room-shell. Resume it
    from the brief with the builder agent, one step at a time. Review and test
    its work before merging into main. Show me screenshots, keep answers short,
    and ask before deleting content or adding dependencies.

The same prompt is in `handover/RESUME-PROMPT.txt`.

Shorter prompts for single steps:

- Resume Phase 3: "Read CLAUDE.md and handover/phase-3-brief.md. Switch to the
  branch phase-3-room-shell and finish the brief with the builder agent."
- Custom domain: "Read CLAUDE.md and docs/05-decisions.md. I bought <domain>.
  Walk me through adding it in Cloudflare Pages, then set `site` in astro.config.mjs."
- New project or post: "Read CLAUDE.md and content/README.md. Turn this into
  content/projects/<slug>.md (or content/posts/<slug>.md): <description>."
- Fine-tune page: "Read CLAUDE.md. Update content/projects/small-model-fine-tune.md
  with: <repo link, scorecard, what broke>."

## 3. Where things stand

| Area | State |
|---|---|
| Docs, roadmap, decisions | Done, in `docs/` |
| Static site (Phase 1) | Done and live. Lighthouse mobile 100 on all four categories (measured before the posts screen) |
| Links | Real, in `content/links.json`. Resume empty, so hidden |
| Posts | One real essay: "Nobody Starts From Zero" (date and summary are guesses, check them) |
| About, intro, tagline | Written 2026-10-19 |
| Projects | Three real: CI diagnosis MCP, GST reconciliation, small model fine-tune (in progress). Examples deleted |
| Deploy and domain | Live on Cloudflare Pages at https://shrikantpawade.pages.dev, redeploys on push to main. Custom domain later, owner's choice |
| Premise for the 3D room | Confirmed 2026-10-19: bedroom music studio, upright piano, nine objects |
| Posts screen (Phase 2) | Done and live 2026-10-19. A screen module on the home page, keyboard, click and tap. Titles only on phones |
| Room shell (Phase 3) | Paused 2026-10-19. Three.js added on the branch `phase-3-room-shell`, the rest not started. See `handover/phase-3-brief.md` |
| Agents | `.claude/agents/`: builder (Sonnet), designer (Opus), quick (Haiku) |

## 4. Next steps, in order

Done 2026-10-19: about page and home text, three real projects, example files
deleted, deploy to Cloudflare Pages, premise and objects, Phase 2 posts screen.

1. Resume Phase 3, the Three.js room shell, on the branch `phase-3-room-shell`.
   Follow `handover/phase-3-brief.md`. Builder agent, Sonnet, high effort.
2. Phase 4 after that: the real room model in Blender. Designer agent, Opus.
3. Whenever the owner buys one: add the custom domain in Cloudflare Pages, set
   `site` in `astro.config.mjs`, tick the domain box in `docs/03-roadmap.md`.
4. Keep `content/projects/small-model-fine-tune.md` current as the 30-day plan moves.

## 5. Things a new agent should know (not obvious from the code)

- Do not write `[slug]` paths in unquoted zsh shell commands. The shell treats
  them as globs and silently skips writing the file. Use the file tool or quotes.
- `npx astro check` hangs because it wants to install `@astrojs/check`.
  Use `npm run build` to verify instead, or ask the owner before adding it.
- `/content.json` is built by `src/pages/content.json.ts`, not stored in `public/`.
- `scene/` stays at the repo root. `src/integrations/scene-files.mjs` serves it
  at `/scene/` in dev and copies it into `dist/` on build.
- The site name and home text come from `content/site.json`. No text lives in pages.
- The colours are a placeholder. Change them in the `:root` variables at the top
  of `src/styles/global.css`.

## 6. Transcripts (local only, not on GitHub)

`handover/transcripts/` is ignored by git because it holds private chat logs.

- `2026-10-17-phase1-chat.md`: readable copy of the Phase 1 chat.
- `2026-10-17-phase1-static-site.zip`: full export from the Claude app.
- `side-session-notes-phase1.md`: the hand-over note left between sessions.

The earlier planning chat that wrote the docs no longer exists in the app,
so it could not be exported. Its output is the `docs/` folder itself.
