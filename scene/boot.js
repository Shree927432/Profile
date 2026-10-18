// The room's entry point. See docs/02-architecture.md, "The hook between layers 2 and 3".
//
// Phase 2 (now): if #screen-slot exists and a 2D canvas is available, mount the posts
// screen (monitor-posts.js, run by screen-host.js) in it. The static list stays for everyone.
//
// Phase 3 will add the room, in this order:
//   1. prefers-reduced-motion?            stay static, offer a link to try anyway
//   2. no WebGL2 or a weak device?         stay static, show "try interactive"
//   3. otherwise hide #static (keep it in the DOM), show #room, import desktop.js
//      and let it paint monitor-posts.js onto the monitor texture
const slot = document.getElementById("screen-slot");
if (slot && document.createElement("canvas").getContext("2d")) {
  try {
    const [{ mountScreen }, { default: monitor }] = await Promise.all([
      import("./screen-host.js"),
      import("./objects/monitor-posts.js"),
    ]);
    await mountScreen(slot, monitor);
  } catch (err) {
    console.error("Screen not mounted:", err);
    slot.replaceChildren();
    document.documentElement.classList.remove("js");
  }
}
