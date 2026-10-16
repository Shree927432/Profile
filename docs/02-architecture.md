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
