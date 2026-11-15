// Room object: the Studio Display as a "write to me" screen. At the display (its stop, or the mic card's "Write an
// email") a form opens on the monitor: name, email, message, Send. A click elsewhere, Close, or leaving closes it.
//
// Meshes (scene/objects/MESHES.md): monitor_screen (the Studio Display's glass, 16:9; a click target). Its V may run
// either way: the frame comes from its corners' UVs.
// Content: content.site.room.compose = { idle, hint, title, name, email, message, send, sending, sent, failed, copy,
// copied, close, subject, accessKey }; content.links.email (the fallback when sending fails or is not set up).
// Sending (owner, 2026-11-15: "Form service (Web3Forms)"): a POST to Web3Forms with the public access key from
// content; a hidden "botcheck" box catches bots. With no key the form offers Copy instead of Send.
// The form is HTML in ctx.overlay laid over the screen's rectangle on screen (a sheet on narrow screens), styled by
// .room-compose in src/styles/global.css; the screen itself shows an idle picture drawn here.

const ENDPOINT = "https://api.web3forms.com/submit";
const NEAR = 1.6; // metres: the camera this close to the screen, looking at it and still, the form opens (the stop: 0.5 m)
const FAR = 2.2; // farther than this, it closes
const LOOK_OPEN = 0.97; // cos of the angle between the view and the screen's centre: about 14 degrees to open
const LOOK_KEEP = 0.9; // about 26 degrees: looking further away than this, it closes (the mic stop is near the
// screen too but looks at the mic: being near is not enough)
const NARROW = 600; // px: below this the form is a sheet
const CW = 1280;
const CH = 720; // the idle picture, 16:9 like the glass

export function createCompose(THREE, ctx) {
  const screen = ctx.root.getObjectByName("monitor_screen");
  const t = (ctx.content && ctx.content.site && ctx.content.site.room && ctx.content.site.room.compose) || null;
  if (!screen || !screen.isMesh || !t || !ctx.overlay) return null;
  const email = (ctx.content.links && ctx.content.links.email) || "";
  const key = (t.accessKey || "").trim();

  // ---- the screen's frame from its corners ----
  screen.updateWorldMatrix(true, false);
  const pos = screen.geometry.attributes.position, uv = screen.geometry.attributes.uv;
  if (!uv) return null;
  const corner = (score) => {
    let best = 0, bestS = -Infinity;
    for (let k = 0; k < uv.count; k++) { const s = score(uv.getX(k), uv.getY(k)); if (s > bestS) { bestS = s; best = k; } }
    return new THREE.Vector3().fromBufferAttribute(pos, best).applyMatrix4(screen.matrixWorld);
  };
  const c00 = corner((u, v) => -u - v), c10 = corner((u, v) => u - v), c01 = corner((u, v) => v - u), c11 = corner((u, v) => u + v);
  const vUp = c01.y > c00.y;
  const corners = [c00, c10, c01, c11];
  const centre = c00.clone().add(c10).add(c01).add(c11).multiplyScalar(0.25);

  // ---- the idle picture on the glass ----
  const canvas = document.createElement("canvas");
  canvas.width = CW;
  canvas.height = CH;
  const g = canvas.getContext("2d");
  if (!g) return null;
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.flipY = vUp;
  tex.anisotropy = 4;
  const oldMat = screen.material;
  screen.material = new THREE.MeshBasicMaterial({ map: tex, toneMapped: false, color: 0xbfc6d4 }); // a screen at dusk, not a lamp
  function paintIdle() {
    g.fillStyle = "#0d1626";
    g.fillRect(0, 0, CW, CH);
    g.strokeStyle = "#1f3554";
    g.lineWidth = 2;
    for (let y = 90; y < CH; y += 90) { g.beginPath(); g.moveTo(0, y); g.lineTo(CW, y); g.stroke(); }
    g.fillStyle = "#9fd0ff";
    g.font = '600 92px ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    g.textAlign = "center";
    g.fillText("✉  " + (t.idle || "Write to me"), CW / 2, CH / 2 + 10);
    g.fillStyle = "#6a97c4";
    g.font = "36px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
    g.fillText(t.hint || "click the screen", CW / 2, CH / 2 + 90);
    tex.needsUpdate = true;
  }
  paintIdle();

  // ---- the form ----
  const form = document.createElement("form");
  form.className = "room-compose";
  form.hidden = true;
  form.noValidate = false;
  form.setAttribute("aria-label", t.title || "Write to me");
  const close = document.createElement("button");
  close.type = "button";
  close.className = "room-compose-close";
  close.setAttribute("aria-label", t.close || "Close");
  close.textContent = "×";
  const h = document.createElement("p");
  h.className = "room-compose-title";
  h.textContent = t.title || "Write to me";
  const field = (label, type, name, attrs = {}) => {
    const l = document.createElement("label");
    l.className = "room-compose-field";
    const s = document.createElement("span");
    s.textContent = label;
    const i = document.createElement(type === "textarea" ? "textarea" : "input");
    if (type !== "textarea") i.type = type;
    i.name = name;
    i.required = true;
    for (const [k, v] of Object.entries(attrs)) i.setAttribute(k, v);
    l.append(s, i);
    return [l, i];
  };
  const [lName, iName] = field(t.name || "Your name", "text", "name", { autocomplete: "name", maxlength: "100" });
  const [lMail, iMail] = field(t.email || "Your email", "email", "email", { autocomplete: "email", maxlength: "200" });
  const [lMsg, iMsg] = field(t.message || "Message", "textarea", "message", { rows: "5", maxlength: "5000" });
  const trap = document.createElement("input"); // bots fill every box; people never see this one
  trap.type = "checkbox";
  trap.name = "botcheck";
  trap.tabIndex = -1;
  trap.className = "room-compose-trap";
  trap.setAttribute("aria-hidden", "true");
  const row = document.createElement("div");
  row.className = "room-compose-row";
  const send = document.createElement("button");
  send.type = "submit";
  send.className = "room-compose-send";
  send.textContent = key ? (t.send || "Send") : (t.copy || "Copy my address");
  const status = document.createElement("p");
  status.className = "room-compose-status";
  status.setAttribute("role", "status");
  row.append(send, status);
  form.append(close, h, lName, lMail, lMsg, trap, row);
  ctx.overlay.append(form);

  if (!key) { iName.required = iMail.required = iMsg.required = false; }

  async function copyAddress() {
    try { await navigator.clipboard.writeText(email); status.textContent = `${t.copied || "Copied"}: ${email}`; }
    catch { status.textContent = email; }
  }
  let busySending = false;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (busySending) return;
    if (!key) { copyAddress(); return; }
    if (trap.checked) return;
    busySending = true;
    send.disabled = true;
    status.textContent = t.sending || "Sending…";
    try {
      const res = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          access_key: key, subject: t.subject || "A message from your website", from_name: iName.value,
          name: iName.value, email: iMail.value, message: iMsg.value, botcheck: false,
        }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.success) throw new Error(j.message || res.status);
      status.textContent = t.sent || "Sent. Thank you.";
      ctx.live(status.textContent);
      iMsg.value = "";
    } catch (err) {
      status.textContent = `${t.failed || "Could not send. My address:"} ${email}`;
      ctx.live(status.textContent);
      console.warn("compose:", err);
    } finally {
      busySending = false;
      send.disabled = false;
    }
  });
  close.addEventListener("click", () => { closedHere = true; setOpen(false); });
  form.addEventListener("keydown", (e) => { if (e.key === "Escape") { e.stopPropagation(); closedHere = true; setOpen(false); } });

  // ---- open / close ----
  let open = false;
  let closedHere = false; // closed at the display: stays closed until the screen is clicked or the visitor leaves
  let lastDist = -1, still = 0;
  function setOpen(on, focus) {
    if (open === on) return;
    open = on;
    form.hidden = !on;
    if (on) {
      status.textContent = "";
      place();
      if (focus) iName.focus();
      ctx.live(t.title || "Write to me");
    } else if (form.contains(document.activeElement)) document.activeElement.blur();
  }
  const _p = new THREE.Vector3(), _dir = new THREE.Vector3(), _to = new THREE.Vector3();
  function place() {
    const cam = ctx.view();
    if (!cam) return;
    if (window.innerWidth < NARROW) { form.classList.add("is-sheet"); form.style.cssText = ""; return; }
    form.classList.remove("is-sheet");
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const c of corners) {
      _p.copy(c).project(cam);
      const x = (_p.x + 1) / 2 * window.innerWidth, y = (1 - _p.y) / 2 * window.innerHeight;
      x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    }
    // on the glass, inside the window; text scales with the screen's height on the page
    const w = Math.min(x1 - x0, window.innerWidth - 24), hh = Math.min(y1 - y0, window.innerHeight - 24);
    form.style.left = Math.round(Math.max(12, x0)) + "px";
    form.style.top = Math.round(Math.max(12, y0)) + "px";
    form.style.width = Math.round(w) + "px";
    form.style.height = Math.round(hh) + "px";
    form.style.fontSize = Math.max(11, Math.min(18, hh / 26)).toFixed(1) + "px";
  }

  const api = {
    frame() {
      const cam = ctx.view();
      if (!cam) return;
      const d = cam.position.distanceTo(centre);
      still = Math.abs(d - lastDist) < 0.0005 ? still + 1 : 0;
      lastDist = d;
      cam.getWorldDirection(_dir);
      const look = _dir.dot(_to.subVectors(centre, cam.position).normalize());
      if (d > FAR || look < LOOK_KEEP) { closedHere = false; if (open) setOpen(false); }
      else if (!open && !closedHere && d < NEAR && look > LOOK_OPEN && still >= 3) setOpen(true);
      if (open) place();
    },
    click() { closedHere = false; setOpen(true, true); },
    away() { if (open) { closedHere = true; setOpen(false); } },
    key(k) {
      const cam = ctx.view();
      if (!cam || cam.position.distanceTo(centre) > FAR) return false;
      if (k === "enter" || k === " ") { closedHere = false; setOpen(true, true); return true; }
      return false;
    },
    tip() { return open ? null : t.idle || "Write to me"; },
    get busy() { return false; },
    dispose() {
      form.remove();
      ctx.interact.delete(screen);
      screen.material.dispose();
      screen.material = oldMat;
      tex.dispose();
    },
  };
  ctx.interact.set(screen, { kind: "compose", part: "monitor_screen", owner: api });
  return api;
}
