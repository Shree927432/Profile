# Start here (new session, new account, or new agent)

Last updated: 2026-10-21, end of day (Phase 4 planned, modelling starts next). Everything below is also on GitHub:
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
    handover/phase-4-brief.md (it lists the files to read and the setup on
    this Mac). Phases 1 to 3 are done and live; the room shows at ?room.
    Phase 4 planning is done: the room tells the evolution of music, and the
    mesh names are final in scene/objects/MESHES.md. Start Phase 4 Step 1
    (room shell, desk, monitor, TOP test) with the designer agent, one step
    at a time. Review and test its work before committing. Keep the build
    journal, video plan and blog draft current. Show me screenshots, keep
    answers short, and ask before deleting content or adding dependencies.

The same prompt is in `handover/RESUME-PROMPT.txt`.

Shorter prompts for single steps:

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
| Premise for the 3D room | Bedroom music studio in Pune (2026-10-19), widened 2026-10-21 to the evolution of music: six era guitars (three on the wall, three on a rack), 88-key piano with both lids, studio desk with a two-deck DJ controller and a K-pop lightstick. Nine objects. 5:40 a.m. blue pre-dawn |
| Posts screen (Phase 2) | Done and live 2026-10-19. A screen module on the home page, keyboard, click and tap. Titles only on phones |
| Room shell (Phase 3) | Done 2026-10-21, on main. Shows only with `?room` (`?room&debug` for fps and quality). Placeholder desk and monitor; clicking or Enter on the post glides into the screen, then opens it. Tuned after the owner's phone test: no glow pass, draws only on change, eased zoom. See `handover/phase-3-brief.md` |
| Room model (Phase 4) | Planned 2026-10-21. Mesh names final in `scene/objects/MESHES.md`. Blender 5.2.2 installed. No modelling yet. See `handover/phase-4-brief.md` |
| Making-of video and blog | Planned: `docs/10-video-plan.md` (Moonlight Sonata, storm then dawn, the owner plays), `docs/drafts/making-of-post.md` (outline), `docs/build-journal.md` (facts as we go). A first card-style timelapse is in `video-local/` (local only) |
| Agents | `.claude/agents/`: builder (Sonnet), designer (Opus), quick (Haiku) |

## 4. Next steps, in order

Done 2026-10-19: about page and home text, three real projects, example files
deleted, deploy to Cloudflare Pages, premise and objects, Phase 2 posts screen.
Done 2026-10-21: Phase 3 room shell, tuned after the owner's phone test. Phase 4
planning: the evolution-of-music premise, the guitar lineup, the mesh name list,
Blender installed, the video plan and the blog outline.

1. Phase 4 Step 1: room shell, desk, monitor and the TOP test export, behind a
   `?room&glb` flag. Designer agent, Opus. Full spec in `handover/phase-4-brief.md`.
2. Phase 4 Steps 2 to 7 from the same brief, one at a time, owner reviews stills.
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
- Blender runs headless: `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python <script>`.
  Headless Chromium with the Mac's GPU, FFmpeg and the capture script are described
  in `handover/phase-4-brief.md`.
- The in-app browser pane runs about one frame a second while hidden, and emulated
  sizes larger than the pane break WebGL screenshots and click positions.
- `video-local/` (videos and their scripts) and `docs/moodboard/local/` (photos from
  the web and the owner's room) are local only; git ignores them.
- After any work: update `docs/build-journal.md`, and the video plan and blog draft
  when relevant (CLAUDE.md rule).

## 6. Transcripts (local only, not on GitHub)

`handover/transcripts/` is ignored by git because it holds private chat logs.

- `2026-10-17-phase1-chat.md`: readable copy of the Phase 1 chat.
- `2026-10-17-phase1-static-site.zip`: full export from the Claude app.
- `side-session-notes-phase1.md`: the hand-over note left between sessions.

The earlier planning chat that wrote the docs no longer exists in the app,
so it could not be exported. Its output is the `docs/` folder itself.
