# Instructions for any agent working in this folder

This is Shrikant's personal website project. The goal is an interactive, game-like
portfolio in the spirit of felixrieseberg.com, built in our own way, on top of a
plain static site that always works.

Read these before doing anything, in this order:

1. docs/00-vision.md            what we are making and why
2. docs/02-architecture.md      how the code is laid out, the rules that must not break
3. docs/03-roadmap.md           what phase we are in and what is next
4. docs/05-decisions.md         decisions already made. Do not re-open them without asking.
5. docs/08-model-guide.md       which model, effort and agent (.claude/agents/) fits each task
6. docs/09-chat-notes.md        links, deploy steps, costs, drafts saved from the planning chat

Then check docs/05-decisions.md again before finishing: if you made a decision the
owner agreed to, append it there with the date.

Also before finishing, keep the story files current. They feed the making-of blog
post and video, so record the misses, not only the wins:
- docs/build-journal.md: a short dated entry for any work that changed the site or
  the room, any decision, any iteration the owner asked for, and anything that went
  wrong (what broke, why, how it was found, what fixed it). Quote the owner's own
  words when they gave feedback.
- docs/10-video-plan.md: update it when a decision changes the video (music, shots,
  footage needs). In Phase 4 and 5, save footage as it describes.
- docs/drafts/making-of-post.md: when something happens that the post should tell,
  add a one-line note under the matching section's comment. Do not write the prose;
  the owner writes it at launch.

## Hard rules

- Content lives in `content/` as markdown and JSON. Never hard-code text, links or
  project details inside page or scene code. Read it from content.
- The static HTML site is the real site. The 3D room is a layer on top. Every feature
  must still be reachable without the room (crawlers, weak phones, screen readers).
- Every interactive object in the room is its own module under `scene/objects/` and
  follows the contract in `scene/objects/CONTRACT.md`. One object per file. Objects
  never import each other.
- One agent edits one object at a time. If you are asked to work on the calculator,
  do not touch the CD player.
- Respect `prefers-reduced-motion`. Every animation has a no-motion path.
- Target 60 fps on a mid-range phone. Measure before adding anything heavy.
- Plain Three.js as ES modules. No React, no bundler-only tricks for the scene. Astro
  for the static site. Nothing else unless a decision in docs/05-decisions.md allows it.

## Choosing a model

When starting a session or handing off work, pick the agent, model and effort from
the table in docs/08-model-guide.md. Say which you picked in one line.

## How to work with the owner

- Show, do not tell. Prefer a screenshot or a running preview over a description.
- Offer two or three options when the choice is about taste. Pick yourself when it is
  about mechanics.
- Ask before: adding a dependency, changing the premise, deleting content, changing
  the object contract.
- Keep answers short. No marketing language.

## Where things are

    content/        the words, projects, posts, links (the only source of truth)
    docs/           vision, reference, architecture, roadmap, ideas, decisions, model guide,
                    video plan, build journal, drafts/ (the making-of blog post)
    handover/       start here when resuming: START-HERE.md and the current phase brief
    .claude/agents/ builder (Sonnet), designer (Opus), quick (Haiku)
    scene/          the 3D room (Phase 3 shell; the Blender model arrives in Phase 4)
    scene/objects/  one file per interactive object, see CONTRACT.md; MESHES.md lists
                    every mesh name Blender and the code share
    blender/        Phase 4: Python scripts that build and export the room (to come)
    src/            the Astro static site (created in Phase 1)
    video-local/    videos and their scripts, local only (git ignores it)
