# Roadmap

Each phase ends with something online. Never skip ahead more than one phase.
Update the status line when a phase changes.

**Current phase: 4, planned, modelling not started** (site live on Cloudflare Pages, custom domain deferred. Phases 2 and 3 done; the room shell is on main behind `?room`. Phase 4 plan and next step: handover/phase-4-brief.md.)

## Phase 0: plan and content (now)

- [x] Folder, docs, agent instructions
- [x] Decide the premise (docs/00-vision.md). One sentence. (2026-10-19: the bedroom music studio)
- [x] List 6 to 10 objects and what each does (nine, confirmed 2026-10-19)
- [x] Write content: about.md, links.json, at least 3 projects, 1 post
- [ ] Mood board folder: docs/moodboard/ with 10 to 20 reference images

Done when: a stranger can read docs/00-vision.md and picture the site.
Time: 2 to 4 evenings. Most of it is deciding, not typing.

## Phase 1: the static site

- [x] Astro project in src/, reads content/
- [x] Pages: home, projects, project detail, posts, post detail, about
- [x] One stylesheet, two fonts max, dark and light
- [x] Lighthouse 95+ on mobile for performance and accessibility
- [x] Deployed on Cloudflare Pages: https://shrikantpawade.pages.dev (2026-10-19)
- [ ] Custom domain
- [x] Home page has the empty room hook (canvas + boot.js that does nothing)

Done when: you would be fine if this were the final site.
Time: one afternoon with an agent, a weekend by hand.

## Phase 2: first screen, no 3D

- [x] One 2D canvas on the home page, styled as a CRT or LCD, listing posts (LCD monitor, 2026-10-19)
- [x] Built as a screen module per scene/objects/CONTRACT.md (`scene/objects/monitor-posts.js`)
- [x] Keyboard navigation inside it, scroll, click to open a post
- [x] Hidden behind the boot check; static list still there for everyone else

Done when: the module contract has been used once for real and feels right.
Time: 2 to 3 sessions.

## Phase 3: the room shell

- [x] Three.js scene: a box with the Phase 2 canvas as its texture (placeholder desk and monitor, 2026-10-21)
- [x] Camera with tight orbit limits, bloom pass, resize handling
- [x] Pick map + raycaster, one clickable thing (`scene/pick.js`, the monitor screen)
- [x] Quality ladder scaffold: full / auto / smooth, fps meter in debug (`scene/quality.js`, `?room&debug`)
- [ ] Replace the box with the real room GLB when it exists (Phase 4)

Done when: clicking the box screen opens a post.
Time: 2 to 4 sessions.

## Phase 4: the room model

- [ ] Blender via Python scripts, one script per group of props
- [x] Every interactive mesh named per a list (scene/objects/MESHES.md, 2026-10-21)
- [ ] Bake lighting with Cycles into atlases, export GLTF
- [ ] Load in the shell. Look at it on a phone. Iterate on stills first.
- [ ] Save footage at every step for the making-of video (docs/10-video-plan.md)

Done when: the room loads in under 3 seconds on 4G and looks like the premise.
Time: the long one. 10 to 30 iterations. 1 to 3 weeks of evenings.

## Phase 5: objects, one at a time

Order by payoff over cost. Suggested:
1. A light switch or lamp (teaches mesh lookup and click)
2. The main screen (reuses Phase 2)
3. A camera close-up on one device
4. Something that lifts and floats (a notepad, a card)
5. Music with a volume control
6. One pure delight with no content (coffee sip, clock battery)

Done when: each is fully working on desktop, touch, keyboard, reduced motion.
Time: 1 to 2 sessions per object.

## Phase 6: sound, performance, fallback

- [ ] Web Audio graph, ducking, click sounds
- [ ] Quality ladder tuned on a real mid phone
- [ ] Static fallback reviewed again with the room in mind
- [ ] Reduced motion and screen reader pass

## Phase 7: polish and cut

Two weeks of nothing new. Look, fix, remove. Cut anything that is not fully
working. Then launch.

- [ ] The making-of video: one dawn shot cut to the owner's piano, plus a 30 s phone cut (docs/10-video-plan.md)

## Later (see docs/04-ideas.md)

Real-world data on screens, hidden objects and a reward, a phone you can pick
up and talk to, a second room.

## Time, honestly

| Approach | To a solid launch |
|---|---|
| Evenings, directing an agent | 4 to 8 weeks |
| Full-time, directing an agent | 2 to 3 weeks |
| By hand, learning Three.js and Blender | 4 to 6 months |

The variable that moves this most is how fast you can look at a version and say
exactly what is wrong with it. Budget half the time for looking.
