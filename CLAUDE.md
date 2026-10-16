# Instructions for any agent working in this folder

This is Shrikant's personal website project. The goal is an interactive, game-like
portfolio in the spirit of felixrieseberg.com, built in our own way, on top of a
plain static site that always works.

Read these before doing anything, in this order:

1. docs/00-vision.md            what we are making and why
2. docs/02-architecture.md      how the code is laid out, the rules that must not break
3. docs/03-roadmap.md           what phase we are in and what is next
4. docs/05-decisions.md         decisions already made. Do not re-open them without asking.

Then check docs/05-decisions.md again before finishing: if you made a decision the
owner agreed to, append it there with the date.

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

## How to work with the owner

- Show, do not tell. Prefer a screenshot or a running preview over a description.
- Offer two or three options when the choice is about taste. Pick yourself when it is
  about mechanics.
- Ask before: adding a dependency, changing the premise, deleting content, changing
  the object contract.
- Keep answers short. No marketing language.

## Where things are

    content/        the words, projects, posts, links (the only source of truth)
    docs/           vision, reference, architecture, roadmap, ideas, decisions
    scene/          the 3D room (empty until Phase 3)
    scene/objects/  one file per interactive object, see CONTRACT.md
    src/            the Astro static site (created in Phase 1)
