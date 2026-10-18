# Start here (new session, new account, or new agent)

Last updated: 2026-10-19. Everything below is also on GitHub:
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
    Then read handover/START-HERE.md and the Status section of README.md.
    We are at the end of Phase 1. Continue from the "Next" list in README.md,
    one step at a time. Show me screenshots, keep answers short, and ask
    before deleting content or adding dependencies.

Shorter prompts for single steps:

- About page: "Read CLAUDE.md. Draft content/about.md and the tagline and
  intro in content/site.json in my voice, using content/posts/nobody-starts-from-zero.md
  as a sample of how I write. Three short paragraphs, first person."
- Projects: "Read CLAUDE.md and content/README.md. I will describe my projects.
  Turn each into content/projects/<slug>.md with the frontmatter in content/README.md."
- Deploy: "Read CLAUDE.md and docs/05-decisions.md. Deploy this Astro site to
  <Cloudflare Pages | Vercel> from the GitHub repo, then set `site` in astro.config.mjs."
- Premise: "Read docs/00-vision.md and docs/01-reference-felix-site.md. Give me
  three premise options, each with one sentence, time, weather, mood, sound,
  and 6 to 8 objects."

## 3. Where things stand

| Area | State |
|---|---|
| Docs, roadmap, decisions | Done, in `docs/` |
| Static site (Phase 1) | Built, works locally, Lighthouse mobile 100 on all four categories |
| Links | Real, in `content/links.json`. Resume empty, so hidden |
| Posts | One real essay: "Nobody Starts From Zero" (date and summary are guesses, check them) |
| About, intro, tagline | Written 2026-10-19 |
| Projects | Three real: CI diagnosis MCP, GST reconciliation, small model fine-tune (in progress). Examples deleted |
| Deploy and domain | Live on Cloudflare Pages at https://shrikantpawade.pages.dev, redeploys on push to main. Custom domain still open |
| Premise for the 3D room | Confirmed 2026-10-19: bedroom music studio, upright piano, nine objects |
| Agents | `.claude/agents/`: builder (Sonnet), designer (Opus), quick (Haiku) |

## 4. Next steps, in order

Done 2026-10-19: about page and home text, three real projects, example files deleted.

1. Add the custom domain in Cloudflare Pages, set `site` in `astro.config.mjs`,
   tick the domain box in `docs/03-roadmap.md`. Phase 1 is then done.
2. Phase 2: the posts screen on the desk monitor, as a screen module.
3. Keep `content/projects/small-model-fine-tune.md` current as the 30-day plan moves.

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
