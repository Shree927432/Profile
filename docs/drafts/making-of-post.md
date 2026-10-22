---
title: A room that builds itself
date: 2026-12-01
summary: How I directed Claude agents to turn my bedroom studio in Pune into a website you can walk around in, without writing the code myself.
tags: [making-of, ai, three-js]
---

<!--
DRAFT. Not published. Lives in docs/drafts/ because posts in content/posts go live
on the next push. To publish: set the real date, move this file to
content/posts/<slug>.md, delete these comments.

Facts for every section are in docs/build-journal.md. Write in the first person,
like "Nobody Starts From Zero": honest, specific, numbers where they help, the
parts that went wrong included.

Title options (pick one):
- A room that builds itself
- Directing, not coding: how my website got built
- Nobody starts from zero, including websites
-->

<!-- VIDEO: the master cut (storm, silence, dawn), embedded at the very top. -->

<!-- 1. HOOK (100 to 150 words)
Felix Rieseberg's site, and opening its source to see how much was real. All of it
was. The question it left me with: could a pianist who left music a year ago
direct something like that? -->

## Why a room

<!-- 2. (200 words) A personal site is one of the last places on the web where it is
fine to play. The rule I set: a place, not a page, but the plain site must always
work. The three layers: words, a plain site, a room on top. -->

## Plans before code

<!-- 3. (250 words) Docs first: vision, architecture, roadmap, a decisions log, an
object contract. Why: long runs with agents drift, and written decisions are what
hold the line. The account change on 17 October, and how the hand-over files let a
new session carry on. -->

## The plain site first

<!-- 4. (150 words) Astro, no JavaScript, Lighthouse 100 on mobile. The site that
crawlers, slow phones and screen readers get. Not an apology page. -->

## Choosing the room

<!-- 5. (300 words) Three sketched premises, and why I picked none of them. My own
room: the guitars, the upright piano that replaced the digital one, the desk where
the models get trained, 5:40 a.m. The nine objects and what each one does.
IMAGES: premise sketches, room sketch. -->
<!-- NOTE 2026-10-21: the premise grew in Phase 4: the room became the evolution of
music. Six guitars from Wes Montgomery to Tim Henson, the piano from Bach to Chopin,
a studio desk for electronic music and K-pop. Copyright decided what each one plays. -->

## The first object: a screen

<!-- 6. (200 words) The posts list as a monitor screen. Too small on my phone; fixed
the same day. What the "object contract" is, in plain words. IMAGE: screen,
desktop and phone. -->

## The first 3D room

<!-- 7. (300 words) Phase 3 in four reviewed steps. What one agent builds and
another checks. Numbers: 15 KB of room code, 120 fps on a Mac. Still hidden at
/?room. IMAGE or CLIP: the placeholder room. -->

## The phone test

<!-- 8. (400 words, the heart of the post) What I said, word for word. What was
actually wrong underneath (bloom passes, instant zoom, no feedback). What changed.
The glide, in milliseconds. "It feels right." This is where "creative direction"
stops being a slogan. CLIP: before and after on the phone. -->

## The video

<!-- 9. (250 words) The first video looked like a slideshow. What Felix's does
differently. Why the Moonlight Sonata: the storm builds the room, the first
movement brings the morning. Why it had to be my own playing. -->

## What I would tell someone starting

<!-- 10. (200 words) Three to five lessons, each one sentence plus an example.
Candidates: write decisions down; look at it on your phone, not your laptop;
describe the feeling, not the fix; keep a plain version that always works; one
object at a time. -->

## What's next

<!-- 11. (100 words) The room in Blender, the instruments that play, the window that
follows Pune's real time and weather. Link to the room. -->
<!-- NOTE 2026-10-21: Phase 4 began with a list of names, not a model: 88 piano keys
named by note so the code can play them, because names are the only thing the
Blender file and the website share. -->
<!-- NOTE 2026-10-21: the first Blender test was a small piano, 88 keys named by note,
rendered clay and finished on the laptop's GPU; the names survived the export. -->
<!-- NOTE 2026-10-22: after comparing the box-piano test with Felix's making-of, I asked
for the design on paper first: a to-scale 2D sheet of the upright (front, side
section, keyboard, details, two finishes) drawn from the same numbers the 3D model
will use, before any modelling. -->
<!-- NOTE 2026-10-22: the quality test. One object, the upright piano, built properly
from the approved sheet: bevels, curved cheeks, brass hinges, 88 real keys, strings and
hammers inside, black lacquer that reflects the blue window. The first box test was
100 boxes; this one is 143 parts and 50k triangles. Renders took about a minute each.
Blender ran with its window open so the build could be watched, and the clip of it
assembling itself is in the footage folder. -->
<!-- NOTE 2026-10-22: I chose the black piano "with some polyphia style". Before any
modelling, a sheet showed the same piano three times with more and more gold ornament
(light, medium, full), our own branching scroll-vine instead of copying the band's art. -->
<!-- NOTE 2026-10-22: before I picked a level I sent two tribal tattoo designs and asked for
"this kind of art work on my piano in silver". The tall tattoo had to be turned on its
side to fit a wide piano: the centre emblem went to the key cover, the two arms behind
the music. -->
<!-- NOTE 2026-10-22: the rebuild with the silver. The same stroke geometry that drew the
sheet was rasterised into the texture, so what I approved on paper is what sits on the
lacquer; the first lit render came out right. The silver key fronts I had asked for
looked like a dark metal bar from across the room, so the agent rendered the ivory
alternative beside it for me to choose. -->
<!-- NOTE 2026-10-22: the room on paper. Before any wall was built, a plan of the whole
room to scale, with a rough 3D sketch from the camera the site opens on. The sketch
showed what a plan hides: from the door you only see the back half of the room, so
everything clickable had to move there, and the ceiling had to be 3 m for the guitars
to hang clear of the piano's open lid. -->
<!-- NOTE 2026-10-22: the room shell. One command builds the room in 3 seconds and the
first export passed the upside-down test: the word TOP on the monitor read upright in
the browser. The misses were the good part: a black box swallowing the view (a piano
stand-in that forgot which way it faced), light leaking through wall corners in the
lightning, a top-down camera that saw only the ceiling. All found by looking at frames.
Then I watched the first 25-second clip, found the camera too static, and stopped the other
five: half an hour a clip was too much for footage of stand-in boxes. The big shoot moved
to the end. -->
