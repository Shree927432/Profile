# Notes saved from the planning chat (2026-10-15 to 2026-10-17)

Everything decided in that chat is already in the other docs. This file keeps
the parts that were only in the conversation.

## Where things live

- Code and docs: https://github.com/Shree927432/Profile (branch main). This is
  on your GitHub account, not your Claude account, so it survives any Claude
  account change.
- Reference site: https://felixrieseberg.com
- How he built it: https://felixrieseberg.com/made-by-mechanical-means/
- His LinkedIn post: https://www.linkedin.com/posts/felixrieseberg_i-remade-my-homepage-with-opus-55-and-pushed-activity-7510072122199801856-_fMM

## Resume on a new account or machine

    git clone https://github.com/Shree927432/Profile.git
    cd Profile && npm install && npm run dev

Then tell any agent: "Read CLAUDE.md and the Status section of README.md, then
continue from 'Next'." The agents in .claude/agents/ come with the repo.

## Deploy (not done yet)

Cloudflare Pages or Vercel, sign in with GitHub, import Profile.
Build command: npm run build. Output folder: dist. Every push to main redeploys.

## Cost

- Building: only your Claude plan's usage. No separate bill.
- Hosting: free on Cloudflare Pages, Vercel, or GitHub Pages.
- Tools: Astro, Three.js, Blender are free.
- Domain: about 10 to 15 USD a year, optional.

## Can it change later

Yes, everything. Content, styling, hosting, domain, even the framework. The
only things costly to change late are the rules in CLAUDE.md and
scene/objects/CONTRACT.md, because every room object depends on them. Review
those before Phase 3.

## LinkedIn repost text (drafted, not posted)

    Spent last night poking around Felix's new site. Opened the source because
    I wanted to know how much of it was real.

    All of it is. The calculator actually calculates. The old PC runs BASIC.
    The CD player has a volume wheel you can drag.

    Under the hood it's plain Three.js and a room that Claude built by writing
    Blender scripts, not by clicking in Blender. Each object on the desk is its
    own little file. Every screen is just a canvas drawn onto a 3D surface.

    The part I keep thinking about: he didn't read most of the code. He looked
    at screenshots on his phone and said what was off. Sixty rounds of that.

    I'm going to try building my own. Different room, my own story. Let's see
    how far I get.

## Learning model selection

1. Models overview: https://platform.claude.com/docs/en/about-claude/models/overview
2. Cost and intelligence: https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence
3. Effort: https://platform.claude.com/docs/en/build-with-claude/effort
4. Pricing: https://platform.claude.com/docs/en/about-claude/pricing
5. Claude Code subagents: https://code.claude.com/docs/en/sub-agents
6. Claude Code model config: https://code.claude.com/docs/en/model-config

Takeaways: try lower effort before a cheaper model; effort matters most for
coding and long agent runs; judge cost per finished task, not per message.

## The recommended big bet (from the chat, not yet decided)

A walkable multi-room place with real-world data on the screens, plus a phone
on the desk you can pick up to talk to an agent that knows your work.
