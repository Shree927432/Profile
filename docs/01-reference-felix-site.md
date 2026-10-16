# Reference: how felixrieseberg.com is built

Everything here was read from the live site's source and from Felix's post
"Made by mechanical means" (felixrieseberg.com/made-by-mechanical-means/) on
2026-10-15. Use it as a map, not a template.

## Stack

| Layer | What he uses |
|---|---|
| Blog and hosting | Ghost CMS 6.x with a custom theme. The 3D room is a theme asset. |
| Static fallback | Plain HTML in `<main>`: bio, social links, full post list. Weak devices are routed here. Crawlers see it. |
| 3D | Plain Three.js 0.169 as ES modules. No React, no bundler framework. |
| Three.js addons | GLTFLoader, OrbitControls, EffectComposer, RenderPass, UnrealBloomPass, ShaderPass, OutputPass, RectAreaLight libs. |
| Room model | Built in Blender by Python scripts Claude wrote (~3,000 lines), exported as GLTF. |
| Lighting | Baked with Cycles (Blender's path tracer) into texture atlases. Up to four maps per atlas. This is why it looks photoreal in a browser. |
| Textures | Procedural noise written as code, not photos. Some furniture from Poly Haven (CC0). |
| Fonts on screens | Caveat (handwriting), VT323 (terminal), Archivo (labels), IBM PC 8x16 bitmap font for the old PC. |
| Audio | Web Audio API. A gain bus per source. Music ducks when the TV film plays. |
| Analytics | Ghost's built-in stats. |

## Scene file layout (as served)

    assets/scene/<hash>/
      boot.js               device check, decides static vs interactive
      desktop.js            the page: loads room, camera, bloom, pick map, pages
      touch/touch.js        phone and touch handling
      city/                 the window view: a living city shader with depth, rain, night life
      winframe/             window frame texture, charts
      pc/basic.js           the old PC: a tiny BASIC interpreter, About and Online live here
      pckeys/pckeys.js      PC keyboard: keys you type press the caps
      calc/calc.js          pocket calculator: floats up, 20 keys, 8-digit engine
      cdplayer/cdplayer.js  music, close-up, 4 buttons, volume thumbwheel
      vcrdoor/vcrdoor.js    VCR flap that a tape pushes open
      notepad/notepad.js    Work notepad that floats up
      credits/credits.js    credits on an index card in a Rolodex, floats up
      coffee/coffee.js      a click is a sip
      clock/clock.js        wall clock, a click removes the battery
      pccase/case.js        PC plastic material up close

## The five tricks that make "everything works"

1. **Pick map plus raycasting.** On load each module finds its mesh by name in
   the GLTF (e.g. `gear_calc`, `gear_rolodex`) and registers its parts in a
   shared map like `{kind:"calc", part:"key", i:7}`. On click, a raycaster hits
   a mesh, the page looks up the owner, and calls that module's `click(part)`.

2. **Screens are 2D canvases used as textures.** The CRT, the PC, the calculator
   LCD, the CD display, the notepad: each is an offscreen canvas drawn with the
   2D context and used as a Three.js texture. The texture is uploaded only when
   `frame()` returns true (the canvas changed).

3. **One module contract for every object.** Each exports a `create…(THREE, ctx)`
   that returns a controller with `frame(dt,t)`, `at(x,y)`, `click(part)`,
   `key(k)`, `tip(hit)`, `lift()/lower()`, `busy`. Screens use
   `mount({canvas, ctx, width, height, audio}) -> {frame, input, stop}`.

4. **Close-ups are camera moves, not new scenes.** Clicking the CD player tweens
   the camera down and swaps control limits. The calculator and credits card
   lift off the desk and float in front of the camera. Esc returns.

5. **A quality ladder.** Full, Auto, Smooth. Auto lowers render resolution when
   frames drag. Phones start at Auto. Songs are decoded in ~3 MB pieces to avoid
   running out of memory on small phones.

## Accessibility and fallback

- `prefers-reduced-motion`: no flight, no bob.
- A live region for screen readers (`ctx.live(text)`).
- Keyboard works on everything: calculator keys, PC typing, credits links.
- A static version with all content, chosen by device check, with a link to try
  the interactive one anyway.

## How he built it (from his post)

- One Claude Project. Around 60 cloud sessions, often in parallel, each with its
  own machine (Blender, FFmpeg, Playwright installed), one shared folder, one
  shared memory where decisions are written down.
- Started with a mood board (90s rave posters, films, ads, photos). Ten sessions
  explored directions in parallel. Twenty-five brainstorm sites. He picked the
  VHS one and pushed it.
- Second draft arrived 39 minutes after the first brief and was already
  recognizably the room. Shipped version took about 60 iterations.
- Claude wrote Blender as Python: tape_model.py (332 lines), gear90s.py (659),
  retro_pc.py (431), room_back.py (290). Rendered stills, Felix gave feedback.
- Modular from the start so sessions could work on separate objects without
  collisions.
- He reviewed on his phone from preview pages. He rarely read code.
- He cut features late: all but one VHS tape were removed.

## What people said in the LinkedIn comments

- "Software engineering is becoming creative direction."
- Long runs die on drift, not context limits. How do you hold the line?
  (Answer we believe: a decisions file and a modular contract.)
- Laggy on mobile, long first load. Both are places to beat him.
- The unplugging-the-clock detail got a comment. Small, fully-working
  surprises land.
