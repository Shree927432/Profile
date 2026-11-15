# Architecture

Three layers. Each one works without the ones above it.

    ┌─────────────────────────────────────────┐
    │  3. The room (Three.js, scene/)         │  optional, loads only on capable devices
    ├─────────────────────────────────────────┤
    │  2. The static site (Astro, src/)       │  always works, what crawlers and phones get
    ├─────────────────────────────────────────┤
    │  1. Content (content/)                  │  markdown + JSON, the only source of truth
    └─────────────────────────────────────────┘

## Layer 1: content

    content/
      about.md              who you are, one page
      links.json            socials, email, resume link
      projects/*.md         one file per project, frontmatter + body
      posts/*.md            one file per post, frontmatter + body

Frontmatter fields are defined in content/README.md. Both the static pages and
the room objects read these files. Nobody types a project title twice.

Later, the build step also emits `public/content.json` so the room can fetch
everything in one request.

## Layer 2: the static site

Astro. Markdown in, HTML out, zero client JavaScript by default.

    src/
      pages/index.astro       home: short intro, latest projects, latest posts
      pages/projects/         list + one page per project
      pages/posts/            list + one page per post
      pages/about.astro
      layouts/Base.astro      one layout, one stylesheet
      styles/global.css

Rules:
- It must look good on its own. This is not a placeholder.
- Fast: no web fonts beyond two, no large images without `loading="lazy"`.
- Semantic HTML, headings in order, skip link, focus styles.

## The hook between layers 2 and 3

On the home page only:

    <main id="static"> ...normal homepage... </main>
    <canvas id="room" hidden></canvas>
    <script type="module" src="/scene/boot.js"></script>

`boot.js` decides, in this order:
1. `prefers-reduced-motion`? Stay static (offer a link to try anyway).
2. No WebGL2, or a weak device heuristic? Stay static, show "try interactive".
3. Otherwise: hide `#static` (keep it in the DOM for screen readers), show the
   canvas, import `desktop.js`, start the room.

Until Phase 3, `boot.js` does nothing. The hook exists so nothing is rewired later.

## Layer 3: the room

    scene/
      boot.js               device check (above)
      desktop.js            the page: load GLTF, camera, bloom, pick map, pages
      objects/CONTRACT.md   the interface every object follows
      objects/<name>.js     one interactive object per file
      assets/               room.glb, baked textures, sounds (git-lfs or hosted)

Mechanics, copied on purpose from the reference:
- Named meshes in the GLTF. Objects find their mesh by name.
- A pick map: each object registers its parts; one raycaster; dispatch to owner.
- Screens: offscreen 2D canvas as texture, re-upload only when changed.
- Close-ups: camera tween plus control limits, not new scenes.
- Quality ladder: full / auto / smooth, auto drops resolution when fps drags.
- Audio: Web Audio graph with one gain bus per source.

## The room's first load (2026-11-13)

Everything the first picture needs starts downloading at once, from the page's head, not one step at a time:

1. `src/pages/index.astro`: with `?room&glb` (and not when `boot.js` will refuse the room) an inline script adds
   `modulepreload` for `boot.js`, `desktop.js`, three.js and the rest of `desktop.js`'s import graph (plus the bloom's
   modules where bloom is on), and `preload` for `/content.json`, the light JSON, `lightmap.webp`, `env.webp`, the Draco
   decoder and `room.glb.gz`. A file missing from the list only loads later. The plain site and plain `?room` get none.
2. `boot.js` imports `desktop.js` while it fetches `content.json`.
3. `desktop.js` `start()` begins the room (`loadRoomGlb()`), the light (`loadRoomLight()`) and the bloom's composer
   before anything else, then builds the renderer while they download. The Draco decoder is set up during the download.
4. `room.glb.gz` is the GLB gzipped at build (`scene-files.mjs`): Cloudflare Pages sends `.glb` uncompressed. It is
   unpacked with DecompressionStream; if that fails the plain `.glb` is fetched. Add any other big GLB to `GZIPPED`.
5. The first frame draws at the end of `start()`; the warm-up (draw the whole room once, out of sight) comes after it.
   The cars load after that (below).

Measured 2026-11-13 at 9 Mbps, 60 ms RTT, CPU 4x, cold: first room frame 4.65 s before, 3.64 s after (2.88 MB on the
wire). The floor is the bytes: the room's file is done at about 2.8 s and 0.8 s of main-thread work follows. Anything
new in the first picture adds its bytes to that. `public/_headers` sets long caching on `/_astro/*` and a day on the
vendored three.js; the room's own files keep Cloudflare's default (they must change together).

## Room objects (Phase 5, from 2026-11-15)

`desktop.js` hosts the room objects of `scene/objects/` (`objects/CONTRACT.md`): it makes each with the ctx (the room,
the scene, `interact`, `view`, `live`, `reduce`, `content`, `overlay`; `audio` is null until sound), calls `frame(dt, t)` every
tick and draws while one is `busy`. The meshes an object registers with an owner stay out of the stops' "room"
registration. A click on an object's part acts only at the object's stop; from anywhere else it flies there first
(the laptop's posts screen works the same way). Keys at a stop reach only the objects with a registered part in that
stop (stops.classify); each decides if a key is its own.
Today: `frames.js` (the picture frames), `mic.js` (the email card, HTML in `ctx.overlay`), `compose.js` (the Studio Display's "write to me" form, sending
through Web3Forms; the only outside service the room calls), `plant.js` (the monstera: water it, a leaf a day).
`ctx.go(stopId)` lets an object fly the camera; `ctx.store` lets it remember things between visits, in the visitor's
browser only (localStorage `room:<key>`; nothing leaves the device).

## Deferred assets (2026-11-08, the car display first; the guitars 2026-11-13; the piano 2026-11-14)

The room's first load has a budget (about 3 MB, about 3 s on 4G). Anything that is not
needed for the first picture ships as its own file and loads after the room is on screen:

- Its own GLB in `scene/assets/` (Draco, WebP), in the room's own frame, listed in `DEFERRED`
  in `scene/desktop.js` (one loader for all: `loadDeferred`, `scene/room-light.js`
  `loadDeferredLight` / `applyDeferredLight`). Today: `cars.glb` (the car display,
  `blender/components/cars.py`), `piano.glb` (`obj_piano`, `export_piano`) and `guitars.glb`
  (all six guitars under `obj_guitars_late`, written by `blender/build_v3.py` `export_guitars`;
  02 and 04 joined 2026-11-14).
- Its light, one of two kinds. Baked: its own lightmap next to the room's
  (`scene/assets/dusk/<name>-light.json` + `<name>-lightmap.webp`, the same dusk rig and the
  same decoding, the room's exposure applies); it never changes `room.glb` or its lightmap, and
  a contact shadow it casts on the room is a `*_shadow` card in its own file (black, alpha =
  1 - baked ratio of the light with and without it), not a room rebake (the cars). Or the
  room's own lightmap (`light: "room"`): a part baked with the room keeps its TEXCOORD_1 into
  the room's atlas and takes the room's loaded lightmap (the piano). Or the
  environment only, like every part that moves (the guitars lift off their hooks): no light
  file. The guitars are in the room's Blender scene when the room is baked, so their shadows
  on the wall and the rack are in the room's lightmap; on the bottom quality rung, where the
  guitars are skipped, those soft shadows stay without them.
- `desktop.js` asks for them only after the first frames have drawn (a few animation frames,
  then `requestIdleCallback`), one after another (the cars, then the guitars, each on its own
  idle callback), so the first load pays nothing. `&nocars` / `&nopiano` / `&noguitars` leave one
  out. `always: true` loads it on the bottom quality rung too (the piano, a stop you can visit);
  its key meshes are merged with `batchRoom` as the room's are.
- A deferred asset can bring a new stop (`late: true` in `scene/stops.js`, the car shelf) or
  more meshes for a stop that exists (the guitars came in two parts until 2026-11-14; now the
  Guitar wall, Guitar rack and Piano stops are made when their files arrive). Either way the room's picking and the free camera's
  room space take its meshes when it arrives.
- It fades in (opacity, under a second); under `prefers-reduced-motion` it just appears.
- It is skipped on the quality ladder's bottom rung (`quality.lowest`) and hidden if the
  ladder steps down to it later; never loaded for the placeholder room or the static site.
- Draw calls: one mesh, one palette material where possible, as the room's statics.
- The static site never depends on it; the room never waits for it.

## The camera, moves and stops (2026-11-11, free camera 2026-11-12, the GLB room)

The GLB room has one camera the visitor drives; OrbitControls are left to the placeholder `?room`.

- `scene/camera-moves.js` owns the pose. Phases: `still` (the intro's hold on the window), `move` (an eased
  flight along a Catmull-Rom curve, smootherstep, yaw and pitch eased apart from the position), `free` (the
  visitor's camera; every flight ends in it) and `orbit` (nothing from here on screen: the glide into a post).
  In free, a drag looks around in place (full yaw, pitch -60 to +50 degrees), the wheel, trackpad pinch and
  two-finger pinch move along the look, WASD and the arrows walk (1.2 m/s). All damped (70 ms), reduce: none.
  At a stop the free camera is in orbit: a drag circles the stop's centre (pitch -80 to +35), wheel, pinch and
  the up/down arrows change the distance (never under half the framing distance), left/right arrows circle.
  Dollying out past 1.8 times the framing distance, or into a wall behind, or walking, leaves orbit with the
  same picture; flying to a stop turns it on again. An intro interrupted by any input becomes free at once and
  the move's speed runs down over 280 ms.
- `scene/room-space.js` is where the camera may be: the room's inside less 22 cm, heights 0.6 to 2.4 m, and
  out of the furniture. Built once on a quiet tick (about 50 to 110 ms): every triangle's box marks 8 cm cells,
  grown by 22 cm. Walking and dollying go through `constrain` (short sub-steps, sliding axis by axis); a circle
  step into a blocked cell is refused (sliding on the other axis). No raycasts, no allocation per frame. The
  car shelf adds its cells when it arrives.
- `scene/stops.js` is the table of stops: per stop, the GLB nodes it owns, extra boxes for parts the export
  merged into a shared `<root>_static` mesh, an optional tighter framing box, a direction to look from and a
  fit. The camera's place is computed from the box, the aspect and the field of view, 25 cm inside the room
  (portrait fits the height and 60 % of the width).
- Picking: every visible room mesh is in the pick map, so nearer things hide farther ones; picks use the
  picture's pose. A hit belongs to its mesh's stop, or else to the smallest stop box holding the hit point.
  A click on a stop flies there; on the posts screen it opens the post (the glide starts from any pose and
  turns the look smoothly); on a wall or the floor it does nothing. Drags never click (6 px, 500 ms).
- Flights: 1.1 to 2.6 s by distance and turn, through a lifted or open-middle waypoint if the straight line
  hits something (five rays, once per flight).
- Back: Escape or the Back button (shown away from the desk pose): a music-side stop goes back to the About
  view, everything else to the desk. Words from `content.site.room.stops` and `room.back`; the hover label is
  a DOM element. Keyboard: a stop list in the bar, hidden until focused. Reduced motion: flights are cuts;
  looking and moving stay (the visitor drives them).
- The posts screen: the wheel over it is the list's, keys reach it when the canvas has focus at the desk pose.

## Build order dependency

    content  →  static site  →  hook  →  2D screen object (no 3D)
             →  Three.js shell with one box  →  real room model
             →  objects one at a time  →  sound  →  quality ladder  →  polish

Each arrow is a shippable commit. Never be more than one arrow from something
that works.

## Hosting

Static output. Cloudflare Pages or Vercel, from the GitHub repo. Large scene
assets (GLB, textures, audio) go in `scene/assets/` under git-lfs, or on a CDN
bucket if they pass ~50 MB total.
