# Start here (new session, new account, or new agent)

Last updated: 2026-10-26 (Phase 4: components approved through the desk-top group; mouse rebuilt on a scan). Everything below is also on GitHub:
https://github.com/Shree927432/Profile

## 1. Get the project

On this Mac it is already at `~/Documents/My_website`. On another machine:

    git clone https://github.com/Shree927432/Profile.git My_website
    cd My_website
    npm install
    npm run dev        # open http://localhost:4321

Needs Node 20 or newer (built with Node 25).

## 2. Prompt to paste into a new Claude Code session

Open the `My_website` folder as the session's folder, then paste the prompt in
`handover/RESUME-PROMPT.txt`.



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
| About, intro, tagline | Rewritten 2026-10-25: confident, no music for now. Home: "AI engineer in Pune, building agents, developer tools and small language models." Pushed and live |
| Projects | Three real: CI diagnosis MCP, GST reconciliation, small model fine-tune (in progress). Examples deleted |
| Deploy and domain | Live on Cloudflare Pages at https://shrikantpawade.pages.dev, redeploys on push to main. Custom domain later, owner's choice |
| Premise for the 3D room | Since 2026-10-24: half AI lab (exactly the owner's desk photo), half music studio kept secret for About. The site opens on the sky and city through the window, then pulls back to the AI lab. Ten objects incl. `obj_rig` (the PC). History in docs/05-decisions.md |
| Posts screen (Phase 2) | Done and live 2026-10-19. A screen module on the home page, keyboard, click and tap. Titles only on phones |
| Room shell (Phase 3) | Done 2026-10-21, on main. Shows only with `?room` (`?room&debug` for fps and quality). Placeholder desk and monitor; clicking or Enter on the post glides into the screen, then opens it. Tuned after the owner's phone test: no glow pass, draws only on change, eased zoom. See `handover/phase-3-brief.md` |
| Room model (Phase 4) | Piano, guitar_02 Strat and guitar_04 Number One done. Plan v3 approved (82 checks). Components approved: screens, speakers, desk, PC (glass and glow fixed), camera, Flex Arm, key lights, mic and boom arm, the desk-top group (Apollo, keyboard, mouse rebuilt on a CC BY scan, Stream Deck). Every one carries an invented brand name (content/room-brands.json). The room GLB on main is still the v1 shell. See `handover/phase-4-brief.md` |
| Making-of video and blog | Planned: `docs/10-video-plan.md` (Moonlight Sonata, storm then dawn, the owner plays), `docs/drafts/making-of-post.md` (outline), `docs/build-journal.md` (facts as we go). A first card-style timelapse is in `video-local/` (local only) |
| Agents | `.claude/agents/`: builder (Sonnet), designer (Opus), quick (Haiku) |

## 4. Next steps, in order

The current list is in `handover/phase-4-brief.md`, section "Next steps". In short: keyboard
legends; the wall group, the return desk and the Aeron, one at a time; rebuild the room from plan v3
with the real models; the lighting pass; the intro, hero and About camera moves in the site; the four
remaining guitars; phone performance; then the new room goes live.
Whenever the owner buys a domain: add it in Cloudflare Pages and set `site` in `astro.config.mjs`.

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
- Blender runs headless, always (owner, 2026-10-24): `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python <script>`.
- macOS has no `timeout` command. Builders get a time box and re-render only what a fix touches.
- Component references and official sizes: `docs/moodboard/local/ai-lab/` (local only).
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
