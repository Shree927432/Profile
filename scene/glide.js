// The glide into the monitor when a post is opened from the room (owner's option A, 2026-10-21):
// the screen lights up, the camera glides to a straight-on close-up, the page fades to the plain
// site's background, then the browser goes to the post. Used by desktop.js only.
//
// desktop.js owns the camera, the materials and the input locks; this file only times things.
//   go(url)    start (ignored while one is running). Prefetches url at once.
//   step(dt)   every loop tick while active: light, camera, fade. Returns true when it moved.
//   reset()    back to rest: light off, fade gone (Back can restore the page from bfcache).
//   active     true from go() until reset()
// Reduced motion: no glide and no fade. The light-up shows for REDUCED_MS, then the post opens.

const HOLD_MS = 120; // the lit row shows before the camera moves, so the tap reads
const GLIDE_MS = 950; // camera travel, ease in-out
const LIGHT_MS = 220; // rise of the light-up, ease out
const FADE_MS = 300; // fade to var(--bg) over the last part of the glide
const REDUCED_MS = 120;
const MAX_STEP_MS = 100; // a long gap between ticks (tab hidden) never jumps the glide
const LATE_MS = 150; // the post opens on time even when frames are slow: a timer backs up step()

const clamp01 = (x) => Math.min(1, Math.max(0, x));
const easeInOut = (x) => (x < 0.5 ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2); // cubic
const easeOut = (x) => 1 - (1 - x) * (1 - x);
const smooth = (x) => x * x * (3 - 2 * x);

// camera, target (Vector3, the screen centre), normal (unit Vector3 the screen faces),
// closeUp() -> distance of the close-up for the current aspect, light(k) with k in 0..1.
export function createGlide({ THREE, camera, target, normal, closeUp, light, reduce }) {
  const from = new THREE.Spherical();
  const to = new THREE.Spherical();
  const now = new THREE.Spherical();
  const v = new THREE.Vector3();
  const prefetched = new Set();
  let url = null; // the post being opened; null at rest
  let t = 0;
  let left = false; // navigation started
  let fade = null;
  let timer = 0;

  function prefetch(href) {
    if (prefetched.has(href)) return;
    prefetched.add(href);
    const link = document.createElement("link");
    link.rel = "prefetch";
    link.href = href;
    document.head.append(link);
  }

  function leave() {
    if (left || !url) return;
    left = true;
    location.href = url;
  }

  function go(href) {
    if (url || !href) return;
    url = href;
    t = 0;
    left = false;
    prefetch(href);
    if (reduce) {
      light(1);
      timer = setTimeout(leave, REDUCED_MS);
      return;
    }
    from.setFromVector3(v.subVectors(camera.position, target));
    to.setFromVector3(v.copy(normal));
    // the short way round
    to.theta = from.theta + Math.atan2(Math.sin(to.theta - from.theta), Math.cos(to.theta - from.theta));
    timer = setTimeout(leave, HOLD_MS + GLIDE_MS + LATE_MS); // slow frames never delay the post
    fade = document.createElement("div");
    fade.className = "room-fade";
    fade.setAttribute("aria-hidden", "true");
    document.body.append(fade);
  }

  function step(dt) {
    if (!url || reduce || left) return false;
    t += Math.min(dt, MAX_STEP_MS);
    light(easeOut(clamp01(t / LIGHT_MS)));
    const e = easeInOut(clamp01((t - HOLD_MS) / GLIDE_MS));
    now.radius = from.radius + (closeUp() - from.radius) * e; // closeUp() follows a resize mid-glide
    now.phi = from.phi + (to.phi - from.phi) * e;
    now.theta = from.theta + (to.theta - from.theta) * e;
    camera.position.setFromSpherical(now).add(target);
    camera.lookAt(target);
    fade.style.opacity = String(smooth(clamp01((t - HOLD_MS - GLIDE_MS + FADE_MS) / FADE_MS)));
    if (t >= HOLD_MS + GLIDE_MS) leave();
    return true;
  }

  function reset() {
    clearTimeout(timer);
    url = null;
    left = false;
    if (fade) fade.remove();
    fade = null;
    light(0);
  }

  return { go, step, reset, get active() { return url !== null; } };
}
