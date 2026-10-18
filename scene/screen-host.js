// Runs one screen module (see objects/CONTRACT.md) on a plain 2D canvas on the page.
// Draws only while on screen and the tab is visible; maps keys, clicks, wheel and touch to input().

const W = 640;
const H = 400;

export async function mountScreen(container, mod) {
  const res = await fetch("/content.json");
  if (!res.ok) throw new Error("content.json " + res.status);
  const content = await res.json();

  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(W * dpr);
  canvas.height = Math.round(H * dpr);
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("no 2d context");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const live = document.createElement("div");
  live.className = "visually-hidden";
  live.setAttribute("aria-live", "polite");

  const screenText = (content.site && content.site.screens && content.site.screens.posts) || {};
  canvas.tabIndex = 0;
  if (screenText.label) canvas.setAttribute("aria-label", screenText.label);

  const open = (url) => { location.href = url; };
  const say = (s) => { live.textContent = ""; live.textContent = s; };
  const screen = mod.mount({ canvas, ctx, width: W, height: H, audio: null, content, open, reduce, say });

  container.append(canvas, live);

  const toCanvas = (cx, cy) => {
    const r = canvas.getBoundingClientRect();
    return { x: ((cx - r.left) * W) / r.width, y: ((cy - r.top) * H) / r.height };
  };
  const send = (ev, native) => {
    const used = screen.input(ev);
    if (used && native && native.cancelable) native.preventDefault();
    return used;
  };

  canvas.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    send({ type: "key", key: e.key }, e);
  });
  canvas.addEventListener("click", (e) => {
    send({ type: "click", ...toCanvas(e.clientX, e.clientY) }, e);
  });
  canvas.addEventListener("wheel", (e) => {
    const k = e.deltaMode === 1 ? 16 : 1;
    const r = canvas.getBoundingClientRect();
    send({ type: "scroll", dy: (e.deltaY * k * H) / r.height }, e);
  }, { passive: false });

  let lastY = null;
  canvas.addEventListener("touchstart", (e) => { lastY = e.touches[0].clientY; }, { passive: true });
  canvas.addEventListener("touchmove", (e) => {
    if (lastY === null) return;
    const y = e.touches[0].clientY;
    const r = canvas.getBoundingClientRect();
    const dy = ((lastY - y) * H) / r.height;
    lastY = y;
    send({ type: "scroll", dy }, e);
  }, { passive: false });
  canvas.addEventListener("touchend", () => { lastY = null; });

  let onScreen = true;
  let running = false;
  let last = 0;
  const loop = (t) => {
    if (!onScreen || document.hidden) { running = false; return; }
    screen.frame(t, t - last);
    last = t;
    requestAnimationFrame(loop);
  };
  const wake = () => {
    if (running || !onScreen || document.hidden) return;
    running = true;
    last = performance.now();
    requestAnimationFrame(loop);
  };
  new IntersectionObserver((entries) => {
    onScreen = entries[entries.length - 1].isIntersecting;
    wake();
  }).observe(canvas);
  document.addEventListener("visibilitychange", wake);
  wake();

  return { canvas, stop() { onScreen = false; screen.stop(); canvas.remove(); live.remove(); } };
}
