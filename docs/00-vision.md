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
**Theme (added 2026-10-21):** the room tells the evolution of music through its
instruments: the piano carries Baroque, Classical and Romantic; the guitars run from
1950s jazz to today (three on the wall, three on a floor rack); the studio desk covers electronic music and K-pop.
**Time and weather:** 5:40 a.m., blue pre-dawn light, the two hours before the day
starts. No sunbeam: in Pune the sun rises between about 5:58 (June) and 7:10
(January). The window follows the real time and weather in Pune, so warm light
appears only when the real sun is up.
**Mood in three words:** Quiet, focused, lived-in.
**What you hear:** Birds outside, the computer's fan, and whichever instrument you
touch: a piano piece from its era, a guitar lick from its era, a loop from the
DJ controller, panned between the two studio monitors.

Reference: the owner's chosen photo, `docs/moodboard/local/chosen-room-guitar-wall-bedroom-studio.jpg`
(local only, not in git), with its digital piano swapped for an upright. Our
sketch is `docs/moodboard/room-sketch.html`.

Layout, from the photo: bed and bookshelf on the left wall, window with a plant
at the back, desk with monitor, speakers and a mic arm in the corner, acoustic
panels and a wall of guitars on the right, the upright piano below the guitars,
a rug on a wooden floor, one ceiling light.

## The objects (confirmed 2026-10-19, updated 2026-10-21)

List 6 to 10 objects. For each: what it is, what it does when clicked, what
content it shows. Fewer objects that fully work beat many that half work.

| Object | On click | Content it shows |
|---|---|---|
| Upright piano | All 88 keys play: notes, chords, and real Baroque, Classical and Romantic pieces with the keys moving. The key cover opens for a close-up; the top lid opens to show the strings and hammers. | About (`content/about.md`) on the music rest |
| Guitars | Six guitars, one per era: three on the wall, three on a floor rack beside the desk. A guitar lifts off its hook or out of the rack and floats up; a click plays a lick in its era's style. | Its era card. The three wall guitars also show a project each, by `order` (`content/projects`) |
| Desk monitor | Camera moves in. The screen lists posts, keyboard works. | `content/posts` (this is the Phase 2 screen) |
| Mic on its arm | Camera moves in. | Email (`content/links.json`). Later, the talk-to-me agent |
| Picture frames | A frame tilts forward. | GitHub, LinkedIn, X (`content/links.json`) |
| Studio desk | A two-deck DJ controller beside the computer: each deck plays an original EDM track, pads trigger loops and one-shots, jog wheels nudge and scratch, EQ and faders shape and blend, the crossfader mixes the decks. A small audio interface holds the pan knob (sound moves between the two studio monitors) and volume. A K-pop lightstick glows, plays a K-pop-style hook and pulses the room light. | None, it is the sound |
| Ceiling light | Toggles the room light. | None, a mood toggle. First object in Phase 5 |
| Window | Nothing. Light and sky follow real Pune time and weather. | None, live data |
| Plant on the sill | Water it. It grows a leaf on each return visit. | None, a delight |

Nine objects, under the limit of ten. The DJ controller, the audio interface, the
studio monitors and the lightstick count as one object, the studio desk.

## The instruments and their eras (decided 2026-10-21)

Guitars, as a timeline: the wall left to right (1 to 3), then the floor rack beside
the desk left to right (4 to 6). Each guitar is modelled on
one player's famous instrument, without logos, brand names or signature graphics.

| # | Era | After | Style |
|---|---|---|---|
| 1 | Blues, 1950s | B.B. King | "Lucille": black semi-hollow, gold hardware |
| 2 | Rock, 1969 | Jimi Hendrix | The Woodstock Strat, Olympic White, small headstock by the owner's choice |
| 3 | Hard rock, 1970s | Jimmy Page (Led Zeppelin) | Cherry double-neck, 12-string over 6-string |
| 4 | Blues rock, 1980s | Stevie Ray Vaughan | "Number One": sunburst Strat worn to bare wood, black pickguard |
| 5 | Metal, late 1980s | James Hetfield (Metallica) | Off-white Explorer |
| 6 | Now, 2020s | Tim Henson (Polyphia) | TOD10 modern electric in mauve |

Changed 2026-10-23 (owner): from Wes Montgomery, Hendrix, Vaughan, Slash, Hetfield,
Henson to one guitar per style, a decade apart. Since 2026-10-23 the guitars are exact
replicas in shape, hardware and finish, without logos, names or signature graphics.

Piano: Baroque, Classical and Romantic pieces (the list is chosen later; for
example Bach's Prelude in C, Mozart's K. 545, Beethoven's Für Elise and Moonlight
Sonata, Chopin's Nocturne Op. 9 No. 2).
Studio desk: electronic music on a generic two-deck DJ controller (house, techno,
trance and more) and K-pop.

What the instruments play:
- Piano: real pieces. Their compositions are public domain. Recordings or
  performances come from the owner, never from a commercial recording.
- Guitars, DJ controller and lightstick: original phrases and loops written in each
  era's style. Famous songs from these eras are copyrighted (including Polyphia's),
  so the site never plays them. Each era card names the style and the player who
  inspired it.

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
