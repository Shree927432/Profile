# What to know before building

You do not need to master these. You need enough to direct the work and judge
the result. One or two evenings each.

## Three.js basics
Scene, camera, renderer, mesh, material, the render loop, raycasting. Do the
first three official examples by hand. Know what a draw call is.

## GLTF
How a scene is carried: named meshes, materials, UV maps, a .glb is a zip of
all of it. Naming discipline in Blender is what lets code find things later.

## Baked lighting
Real-time browser lighting looks flat. Baking Cycles light into textures is the
single biggest reason the reference room looks real. Know the idea: a second UV
set, an atlas, a bake pass, an unlit material in the browser.

## Canvas as texture
Every "working" screen is a 2D canvas drawn each frame and used as a texture.
Once this clicks, calculators, CRTs, LCDs and notepads are the same trick.

## Web Audio
AudioContext, gain nodes, a bus per source, ducking. Autoplay rules: sound
starts only after a user gesture.

## Performance
60 fps on a mid phone means: few draw calls, small textures (KTX2 if possible),
no shadows in real time, resolution scaling when frames drag. Measure first.

## Accessibility
Static fallback, reduced motion, keyboard for everything, a live region for
screen readers, focus visible. The reference does all four.

## Blender by script
You will not click in Blender. You will ask an agent to write Python that uses
`bpy` to build geometry, render a still, and show it to you. Learn to give
feedback on stills: scale, light, color, material, clutter.

## Directing agents
See docs/07-agent-workflow.md.
