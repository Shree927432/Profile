# Vision

## What we are making

A personal website that is a place, not a page. You arrive somewhere, you look
around, you touch things, and the things work. Projects, posts, and contact
details are objects in that place. It should feel like the opening of a game.

Underneath it is a normal, fast, readable static site. That site is never
sacrificed for the effect.

## Why

- Personal sites are one of the last places on the web where it is fine to be
  playful. Use that.
- A site people send to each other is worth more than a resume.
- Building it teaches 3D, audio, performance, and how to direct AI agents on a
  long creative project. Those skills carry over.

## The premise (decided 2026-10-19)

Felix's room works because one sentence decides everything:
"a 1990s German journalist's desk, at night, rain on the window."

We need our own sentence. Do not copy the desk. Candidates we have talked about:

- A workshop bench: projects as tools on a pegboard, a radio for music, a label
  maker that prints contact details.
- A kitchen: posts as recipe cards in a box, fridge magnets for socials, a timer
  counting to the next talk.
- A car dashboard at night: cassette deck, glovebox for the CV, radio presets
  for sections.
- An arcade cabinet or handheld console: each project is a cartridge, the screen
  is a working mini game.
- A walkable multi-room place (apartment, shop, train car): bigger scope, more
  wow, more work.

Write the chosen premise here once decided, as one sentence, plus the time of
day, the weather, the mood, and the sound.

**Premise:** My room in Pune, a bedroom that became a music studio: a wall of
guitars, an upright piano, and the desk where the models get trained.
**Time and weather:** 5:40 a.m., first light, the two hours before the day starts.
The window follows the real time and weather in Pune.
**Mood in three words:** Quiet, focused, lived-in.
**What you hear:** Birds outside, the computer's fan, and the piano or a guitar
when you touch it.

Reference: the owner's chosen photo, `docs/moodboard/local/chosen-room-guitar-wall-bedroom-studio.jpg`
(local only, not in git), with its digital piano swapped for an upright. Our
sketch is `docs/moodboard/room-sketch.html`.

Layout, from the photo: bed and bookshelf on the left wall, window with a plant
at the back, desk with monitor, speakers and a mic arm in the corner, acoustic
panels and a wall of guitars on the right, the upright piano below the guitars,
a rug on a wooden floor, one ceiling light.

## The objects (confirmed 2026-10-19)

List 6 to 10 objects. For each: what it is, what it does when clicked, what
content it shows. Fewer objects that fully work beat many that half work.

| Object | On click | Content it shows |
|---|---|---|
| Upright piano | Keys play real notes. The lid opens to a close-up. | About (`content/about.md`) on the music rest |
| Guitar wall | A guitar lifts off its hook and floats up. A click strums it. | One project per guitar (`content/projects`) |
| Desk monitor | Camera moves in. The screen lists posts, keyboard works. | `content/posts` (this is the Phase 2 screen) |
| Mic on its arm | Camera moves in. | Email (`content/links.json`). Later, the talk-to-me agent |
| Picture frames | A frame tilts forward. | GitHub, LinkedIn, X (`content/links.json`) |
| Studio speakers | Music on or off, volume on scroll. | None, it is the sound |
| Ceiling light | Toggles the room light. | None, a mood toggle. First object in Phase 5 |
| Window | Nothing. Light and sky follow real Pune time and weather. | None, live data |
| Plant on the sill | Water it. It grows a leaf on each return visit. | None, a delight |

Nine objects, under the limit of ten.

## What "better than Felix's" means for us

- Mobile and touch are first-class, not a fallback.
- Loads in under 3 seconds on 4G. His takes longer.
- Real-world data on the screens: real time, real weather, real latest work.
- One light game layer: a few hidden things, one reward.
- The static version is genuinely good, not an apology page.

## What we will not do

- Copy his desk, his 90s journalist premise, or his VHS tapes.
- Ship more than 10 interactive objects in version 1.
- Add React or a game engine to the scene.
- Let the 3D layer break the readable site.
