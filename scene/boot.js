// The room's entry point. See docs/02-architecture.md, "The hook between layers 2 and 3".
//
// Phase 3. Without ?room in the URL nothing changes from Phase 2: the posts screen
// (monitor-posts.js, run by screen-host.js) is mounted in #screen-slot, and the static
// page stays for everyone.
//
// With ?room (any value; ?room=force means "try anyway"):
//   1. prefers-reduced-motion and not room=force   plain page + note with a "try anyway" link
//   2. no WebGL2                                    plain page + note
//   3. otherwise                                    <html class="room-on"> hides #static
//      visually (it stays in the DOM for screen readers), shows #room, adds an overlay
//      (plain-page link + loading line), then imports ./desktop.js and calls start().
//      When start() resolves the loading line is hidden.
//   Any failure in step 3 logs one console.error, undoes the room state and falls back to
//   the plain page with the screen mounted. The 2D screen is NOT mounted when the room
//   starts: the scene paints monitor-posts.js onto a texture itself.
//
// desktop.js must export:  async function start(opts)  and gets one object:
//   {
//     canvas,   // the #room <canvas>, visible, no context taken yet
//     content,  // parsed /content.json (site, links, about, projects, posts)
//     overlay,  // the overlay <div class="room-overlay">; add the ?debug panel here.
//               //   Visible words come from content.site.room (see content/README.md).
//     params,   // URLSearchParams of location.search (e.g. params.has("debug"))
//     reduce,   // true when prefers-reduced-motion is set (only possible with room=force)
//   }
// start() may return anything (ignored). If it throws or rejects, boot.js falls back.

const params = new URLSearchParams(location.search);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const root = document.documentElement;

async function loadContent() {
  const res = await fetch("/content.json");
  if (!res.ok) throw new Error("content.json " + res.status);
  return res.json();
}

async function mountPlainScreen() {
  const slot = document.getElementById("screen-slot");
  if (!slot || !document.createElement("canvas").getContext("2d")) return;
  try {
    const [{ mountScreen }, { default: monitor }] = await Promise.all([
      import("./screen-host.js"),
      import("./objects/monitor-posts.js"),
    ]);
    await mountScreen(slot, monitor);
  } catch (err) {
    console.error("Screen not mounted:", err);
    slot.replaceChildren();
    root.classList.remove("js");
  }
}

// A quiet line at the top of the plain page. link: { text, href } or null.
function showNote(text, link) {
  const host = document.getElementById("static");
  if (!text || !host) return;
  const p = document.createElement("p");
  p.className = "room-note small muted";
  p.setAttribute("role", "status");
  p.append(text);
  if (link && link.text) {
    p.append(" ");
    const a = document.createElement("a");
    a.href = link.href;
    a.textContent = link.text;
    p.append(a);
  }
  host.prepend(p);
}

// Same address with room=force; other params (such as debug) are kept.
function forceHref() {
  const p = new URLSearchParams(location.search);
  p.set("room", "force");
  return location.pathname + "?" + p.toString().replace(/=(&|$)/g, "$1");
}

// Text for the notes shown before the screen's own fetch. Never throws.
async function noteText() {
  try {
    return (await loadContent()).site.room || {};
  } catch (err) {
    console.error("Room text not loaded:", err);
    return {};
  }
}

function webgl2Available() {
  try {
    return !!document.createElement("canvas").getContext("webgl2");
  } catch {
    return false;
  }
}

// While the room is on, the plain page is only visually hidden, so its links would be invisible
// tab stops. Take them out of the tab order (screen readers still reach them by reading) and put
// the old tabindex back on fallback. The skip link is included: it points at hidden content.
const TAB_HIDDEN = "#static, .site-header, .site-footer, .skip-link";
const FOCUSABLE = "a[href], button, input, select, textarea, summary, [tabindex], [contenteditable]";
let savedTabindex = null; // Map of element -> previous tabindex attribute (or null)

function leaveTabOrder() {
  savedTabindex = new Map();
  for (const host of document.querySelectorAll(TAB_HIDDEN)) {
    for (const el of [host, ...host.querySelectorAll(FOCUSABLE)]) {
      if (!el.matches(FOCUSABLE) || savedTabindex.has(el)) continue;
      savedTabindex.set(el, el.getAttribute("tabindex"));
      el.setAttribute("tabindex", "-1");
    }
  }
}

function restoreTabOrder() {
  if (!savedTabindex) return;
  for (const [el, old] of savedTabindex) {
    if (old === null) el.removeAttribute("tabindex");
    else el.setAttribute("tabindex", old);
  }
  savedTabindex = null;
}

async function startRoom() {
  const canvas = document.getElementById("room");
  let overlay = null;
  try {
    if (!canvas) throw new Error("no #room canvas");
    const content = await loadContent();
    const text = content.site && content.site.room;
    if (!text || !text.exit || !text.loading) throw new Error("site.room text missing");

    overlay = document.createElement("div");
    overlay.className = "room-overlay";
    const exit = document.createElement("a");
    exit.className = "room-exit";
    exit.href = "/";
    exit.textContent = text.exit;
    const loading = document.createElement("span");
    loading.className = "room-loading";
    loading.setAttribute("aria-live", "polite");
    overlay.append(exit, loading);

    root.classList.add("room-on");
    canvas.hidden = false;
    leaveTabOrder();
    document.body.prepend(overlay); // before the canvas, so Tab goes: plain-page link, then canvas
    loading.textContent = text.loading; // after insertion, so screen readers announce it

    const { start } = await import("./desktop.js");
    await start({ canvas, content, overlay, params, reduce });
    loading.hidden = true;
  } catch (err) {
    console.error("Room not started, showing the plain page:", err);
    root.classList.remove("room-on");
    restoreTabOrder();
    if (overlay) overlay.remove();
    if (canvas) {
      canvas.hidden = true;
      canvas.setAttribute("aria-hidden", "true");
      canvas.removeAttribute("aria-label");
      canvas.removeAttribute("tabindex");
    }
    const t = await noteText();
    showNote(t.failedNote, null);
    await mountPlainScreen();
  }
}

if (!params.has("room")) {
  await mountPlainScreen();
} else if (reduce && params.get("room") !== "force") {
  const t = await noteText();
  showNote(t.reducedMotionNote, { text: t.tryAnyway, href: forceHref() });
  await mountPlainScreen();
} else if (!webgl2Available()) {
  const t = await noteText();
  showNote(t.noWebglNote, null);
  await mountPlainScreen();
} else {
  await startRoom();
}
