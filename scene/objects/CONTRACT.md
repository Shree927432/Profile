# The object contract

Every interactive thing in the room is one file in this folder and follows this
shape. Objects never import each other. Agents work on one object at a time.

## Room objects (things in 3D)

```js
// scene/objects/lamp.js
export function createLamp(THREE, ctx) {
  // ctx.root       the loaded room (THREE.Group). Find your mesh by name.
  // ctx.scene      the scene, if you must move your mesh out of the room tree
  // ctx.interact   the pick map. Register parts: ctx.interact.set(mesh, {kind:"lamp", part:"switch"})
  // ctx.view()     the camera as drawn this frame
  // ctx.audio()    {ctx, out} while sound is on, else null
  // ctx.live(text) one line for screen readers
  // ctx.reduce     true when prefers-reduced-motion
  // ctx.content    the parsed content (projects, posts, links, about)
  const mesh = ctx.root.getObjectByName("lamp");
  if (!mesh) return null;              // the room may not have this object yet

  return {
    frame(dt, t) {},                   // once per frame, after the camera is final
    click(part) {},                    // a registered part was clicked
    key(k) { return false; },          // e.key lowercased; return true if consumed
    tip(hit) { return null; },         // hover text, or null
    get busy() { return false; },      // true while animating; the page waits
    dispose() {},
  };
}
```

## Screens (2D content painted onto a surface)

```js
// scene/objects/monitor-posts.js
export default {
  id: "monitor-posts",
  mount({ canvas, ctx, width, height, audio, content, open, reduce, say }) {
    // reduce: true when prefers-reduced-motion. say(text): one line for screen readers.
    // draw with the 2D ctx. return true from frame() only when pixels changed.
    return {
      frame(t, dt) { return false; },
      input(ev) { return false; },     // {type:"key"|"click"|"scroll"|"open", ...}; true if used
      stop() {},
    };
  },
};
```

## Rules

- Mesh names are the API between Blender and code. Document every name you
  rely on at the top of your file.
- Return `null` if your mesh is missing. The room must load without you.
- Reduced motion: every animation has an instant path.
- No global state. Everything comes in through ctx.
- Sounds under 100 KB, loaded lazily on first use.
- Write a two-line header comment: what the object is, what a click does.
