// Room object: the mic on its arm (the email). A click lights its LED ring and opens an "On air" card beside it with
// the email and two real buttons, Copy and Write an email. A click anywhere else, or walking away, closes it.
//
// Meshes (scene/objects/MESHES.md, obj_mic): mic_body (the microphone and its mount; a click target),
// mic_led (the LED ring; a click target, lit while the card is open).
// Content: content.links.email; the words in content.site.room.mic = { onAir, title, copy, copied, write, close }.
// The card is HTML in ctx.overlay (owner, 2026-11-15: option A, "a card by the mic", with real buttons), styled by
// .room-mic-card in src/styles/global.css. Desktop: beside the mic, following it on screen. Narrow screens: a
// sheet at the bottom.

const FAR = 2.4; // metres: farther than this from the mic, the card closes (the mic stop is about 1 m away)
const LED_ON = 4; // the LED's light times this while the card is open
const FADE_MS = 220;
const NARROW = 600; // px: below this the card is a bottom sheet
const GAP = 28; // px between the mic on screen and the card

export function createMic(THREE, ctx) {
  const body = ctx.root.getObjectByName("mic_body");
  const led = ctx.root.getObjectByName("mic_led");
  const email = ctx.content && ctx.content.links && ctx.content.links.email;
  if (!body || !email || !ctx.overlay) return null;
  const t = (ctx.content.site && ctx.content.site.room && ctx.content.site.room.mic) || {};

  // the LED: its own material, so lighting it touches nothing else
  let ledMat = null, ledBase = 0;
  const ledMesh = led && (led.isMesh ? led : led.children.find((c) => c.isMesh));
  if (ledMesh && ledMesh.material && !Array.isArray(ledMesh.material)) {
    ledMat = ledMesh.material.clone();
    if (ledMat.emissive && !ledMat.emissiveMap && ledMat.map) { ledMat.emissiveMap = ledMat.map; ledMat.emissive.setScalar(1); }
    ledBase = ledMat.emissiveIntensity || 1;
    ledMesh.material = ledMat;
  }

  // ---- the card ----
  const card = document.createElement("div");
  card.className = "room-mic-card";
  card.setAttribute("role", "dialog");
  card.setAttribute("aria-label", t.title || "Email");
  card.hidden = true;
  const onAir = document.createElement("p");
  onAir.className = "room-mic-onair";
  onAir.textContent = t.onAir || "On air";
  const title = document.createElement("p");
  title.className = "room-mic-title";
  title.textContent = t.title || "Let's talk";
  const addr = document.createElement("p");
  addr.className = "room-mic-email";
  addr.textContent = email;
  const row = document.createElement("div");
  row.className = "room-mic-buttons";
  const copy = document.createElement("button");
  copy.type = "button";
  copy.className = "room-mic-copy";
  copy.textContent = t.copy || "Copy";
  const write = document.createElement("a");
  write.className = "room-mic-write";
  write.href = "mailto:" + email;
  write.textContent = (t.write || "Write an email") + " ↗";
  const close = document.createElement("button");
  close.type = "button";
  close.className = "room-mic-close";
  close.setAttribute("aria-label", t.close || "Close");
  close.textContent = "×";
  row.append(copy, write);
  card.append(close, onAir, title, addr, row);
  ctx.overlay.append(card);

  let copiedTimer = 0;
  copy.addEventListener("click", async () => {
    let ok = false;
    try { await navigator.clipboard.writeText(email); ok = true; } catch { /* no clipboard: select the address */ }
    if (!ok) {
      const r = document.createRange();
      r.selectNodeContents(addr);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(r);
    }
    copy.textContent = ok ? (t.copied || "Copied") : (t.copy || "Copy");
    if (ok) ctx.live((t.copied || "Copied") + ": " + email);
    clearTimeout(copiedTimer);
    copiedTimer = setTimeout(() => { copy.textContent = t.copy || "Copy"; }, 1600);
  });
  close.addEventListener("click", () => setOpen(false));
  card.addEventListener("keydown", (e) => { if (e.key === "Escape") { e.stopPropagation(); setOpen(false); } });

  // ---- open / close ----
  let open = false;
  let k = 0; // the LED and the card's fade, 0..1
  const box = new THREE.Box3().setFromObject(body); // the mic as a whole: the card goes past its edge on screen
  if (led) box.expandByObject(led);
  const centre = box.getCenter(new THREE.Vector3());
  const corners = [];
  for (let n = 0; n < 8; n++) corners.push(new THREE.Vector3(n & 1 ? box.max.x : box.min.x, n & 2 ? box.max.y : box.min.y, n & 4 ? box.max.z : box.min.z));
  function setOpen(on, focus) {
    if (open === on) return;
    open = on;
    card.hidden = false;
    card.classList.toggle("is-open", on);
    if (on) {
      ctx.live(`${t.title || "Let's talk"}: ${email}`);
      place();
      if (focus) write.focus();
    }
    if (!on && card.contains(document.activeElement)) document.activeElement.blur();
  }
  const _p = new THREE.Vector3();
  function place() {
    const cam = ctx.view();
    if (!cam) return;
    if (window.innerWidth < NARROW) { card.classList.add("is-sheet"); card.style.left = card.style.top = ""; return; }
    card.classList.remove("is-sheet");
    let x0 = Infinity, x1 = -Infinity, ys = 0;
    for (const c of corners) {
      _p.copy(c).project(cam);
      const x = (_p.x + 1) / 2 * window.innerWidth;
      x0 = Math.min(x0, x); x1 = Math.max(x1, x); ys += (1 - _p.y) / 2 * window.innerHeight;
    }
    const y = ys / corners.length;
    const w = card.offsetWidth || 320, h = card.offsetHeight || 180;
    let left = x1 + GAP;
    if (left + w > window.innerWidth - 12) left = x0 - GAP - w; // no room on the right: the left side
    const top = Math.min(Math.max(12, y - h / 2), window.innerHeight - h - 12);
    card.style.left = Math.round(Math.max(12, left)) + "px";
    card.style.top = Math.round(top) + "px";
  }

  const api = {
    frame(dt) {
      const cam = ctx.view();
      if (open && cam && cam.position.distanceTo(centre) > FAR) setOpen(false);
      const goal = open ? 1 : 0;
      if (k !== goal) {
        const step = ctx.reduce ? 1 : dt / FADE_MS;
        k = goal > k ? Math.min(1, k + step) : Math.max(0, k - step);
        if (ledMat) ledMat.emissiveIntensity = ledBase * (1 + (LED_ON - 1) * k);
        if (k === 0) card.hidden = true;
      }
      if (open) place();
    },
    click() { setOpen(true); },
    away() { setOpen(false); },
    key(key) {
      const cam = ctx.view();
      if (!cam || cam.position.distanceTo(centre) > FAR) return false;
      if (key === "enter" || key === " ") { setOpen(true, true); return true; }
      return false;
    },
    tip() { return open ? null : t.title || "Let's talk"; },
    get busy() { return k !== (open ? 1 : 0); },
    dispose() {
      clearTimeout(copiedTimer);
      card.remove();
      for (const m of parts) ctx.interact.delete(m);
    },
  };
  // mic_body has two materials, so it loads as a group of two meshes: every mesh under it (and the LED) is a target
  const parts = [];
  for (const node of [body, led]) if (node) node.traverse((o) => { if (o.isMesh && !parts.includes(o)) parts.push(o); });
  for (const m of parts) ctx.interact.set(m, { kind: "mic", part: m.name, owner: api });
  return api;
}
