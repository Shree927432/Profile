// The room page: renderer, camera, orbit, zoom, the posts screen on the monitor.
// Called by boot.js (see its header for what start() receives).
//
// What lives where, top to bottom:
//   constants          camera, orbit, zoom, glow numbers in one place
//   start()            wires everything; resolves after the first frame is drawn
//     renderer               plain renderer.render(); setPixelRatio() is the one place pixel ratio changes
//     quality                quality.js decides the pixel ratio; applyQuality() applies it
//     scene                  lights + buildPlaceholderRoom() (Phase 4: GLB loader instead)
//     screen + glow          monitor-posts.js on an offscreen canvas -> CanvasTexture; a soft
//                            halo plane behind it (made here so it survives the GLB)
//     camera + controls      resize() fits the monitor to the aspect; zoom is ours, not OrbitControls'
//     loop                   one setAnimationLoop; draws only when something changed
//
// Camera: setCameraDistance() is the one function that moves the camera along its line of sight.
// zoomTo()/zoomBy() set the goal (a fraction of the fitted distance); stepZoom() eases toward it.
// Input (all on the canvas): pick.js holds the pick map; taps raycast it, the wheel and a
// one-finger drag that starts on the screen scroll the list, keys go to the screen. Wheel off
// the screen, ctrl+wheel (trackpad pinch) and a two-finger touch pinch zoom.
// Quality ladder (quality.js): full / auto / smooth. With ?debug a small panel in the overlay
// shows fps and the pixel ratio and switches the mode.
//
// Every word shown comes from content.site.room / content.site.screens.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { buildPlaceholderRoom } from "./placeholder-room.js";
import monitorPosts from "./objects/monitor-posts.js";
import { createPickMap } from "./pick.js";
import { createQuality, MODES } from "./quality.js";

const deg = THREE.MathUtils.degToRad;

const BACKGROUND = 0x14110f;
const FOV = 40;
// Framing: how much room around the monitor, as a multiple of its half size.
const FIT_MARGIN_V = 1.5;
const FIT_MARGIN_H = 1.1;
// Orbit: camera starts 8 degrees above the screen's centre line, looking straight on.
const START_POLAR = deg(82);
const POLAR_BAND = deg(8);
const AZIMUTH_LIMIT = deg(25);
// Zoom, as fractions of the fitted distance. Near brings the screen to fill a phone.
const ZOOM_NEAR = 0.55;
const ZOOM_FAR = 1.6;
const ZOOM_SETTLE_MS = 60; // easing time constant: ~250 ms to settle
const WHEEL_ZOOM = 0.0012; // per wheel px: a 100 px notch is about 13 %
const PINCH_WHEEL_ZOOM = 0.01; // ctrl+wheel (trackpad pinch) sends small deltas
// Glow: a cheap stand-in for bloom. A soft additive halo plane just behind the screen.
const GLOW = { color: 0x9fd0ff, opacity: 0.3, size: 1.45, texture: 128 }; // size: multiple of the screen
const GLOW_BEHIND = 0.0005; // metres behind the screen plane
// Logical size of the screen canvas (backing store is 2x). Same rule as screen-host.js and the
// decision of 2026-10-19: under 480 CSS px wide the screen is the narrow 400x250 layout.
// Chosen once at start; picking uses the same numbers.
const SCREEN_WIDE = { w: 640, h: 400 };
const SCREEN_NARROW = { w: 400, h: 250 };
const NARROW_BELOW = 480;
// Tap vs drag: a pointer that moved less than this many CSS px and was down less than this
// many ms counts as a tap.
const TAP_MAX_MOVE = 6;
const TAP_MAX_MS = 500;
const WHEEL_LINE_PX = 16; // deltaMode "lines" -> px, as in screen-host.js

export async function start({ canvas, content, overlay, params, reduce }) {
  const text = content.site.room;
  const { w: SCREEN_W, h: SCREEN_H } = window.innerWidth < NARROW_BELOW ? SCREEN_NARROW : SCREEN_WIDE;

  // ---- renderer ----
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping; // the screen material opts out (toneMapped: false)
  renderer.setClearColor(BACKGROUND);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(BACKGROUND);

  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.05, 30);

  // The loop draws only when this is true (see renderFrame). Anything that changes the picture sets it.
  let needsRender = true;
  // The one place that changes resolution.
  function setPixelRatio(pr) {
    renderer.setPixelRatio(pr);
    needsRender = true;
  }
  // Called by the quality ladder at start and on every change.
  function applyQuality({ pixelRatio }) {
    setPixelRatio(pixelRatio);
  }
  const quality = createQuality({ dpr: window.devicePixelRatio || 1, reduce, apply: applyQuality });

  // ---- scene ----
  scene.add(new THREE.HemisphereLight(0xcdd5e6, 0x3e281a, 1.1));
  const sun = new THREE.DirectionalLight(0xffd7a3, 1.6); // early light from the window, left/back
  sun.position.set(-2.5, 2.2, 0.4);
  scene.add(sun);

  const room = buildPlaceholderRoom(THREE);
  scene.add(room);
  scene.updateMatrixWorld(true);

  // Phase 4: the screen and body come out of the GLB by name, never by held reference.
  const screenMesh = room.getObjectByName("monitor_screen");
  const bodyMesh = room.getObjectByName("monitor_body");
  if (!screenMesh || !bodyMesh) throw new Error("room has no monitor_screen / monitor_body");
  const lookAt = screenMesh.getWorldPosition(new THREE.Vector3());
  const bodySize = new THREE.Box3().setFromObject(bodyMesh).getSize(new THREE.Vector3());

  // ---- posts screen on the monitor ----
  const screenCanvas = document.createElement("canvas");
  screenCanvas.width = SCREEN_W * 2;
  screenCanvas.height = SCREEN_H * 2;
  const screenCtx = screenCanvas.getContext("2d");
  if (!screenCtx) throw new Error("no 2d context for the screen");
  screenCtx.setTransform(2, 0, 0, 2, 0, 0); // after the size is set, which resets it

  const live = document.createElement("div");
  live.className = "visually-hidden";
  live.setAttribute("aria-live", "polite");
  overlay.append(live);
  const say = (s) => { live.textContent = ""; live.textContent = s; };
  const open = (url) => { location.href = url; };

  // screenHandle.input({type:"key"|"click"|"scroll"|"open", ...}) returns true if it used the event.
  const screenHandle = monitorPosts.mount({
    canvas: screenCanvas, ctx: screenCtx, width: SCREEN_W, height: SCREEN_H,
    audio: null, content, open, reduce, say,
  });

  const screenTexture = new THREE.CanvasTexture(screenCanvas);
  screenTexture.colorSpace = THREE.SRGBColorSpace;
  screenTexture.minFilter = THREE.LinearMipmapLinearFilter;
  screenTexture.magFilter = THREE.LinearFilter;
  screenTexture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  screenMesh.material.dispose();
  // toneMapped:false: the screen shows the posts colours exactly as drawn.
  screenMesh.material = new THREE.MeshBasicMaterial({ map: screenTexture, toneMapped: false });

  // ---- glow: soft halo behind the screen (not pickable, not in the pick map) ----
  // Placed from the screen's world transform, so it follows whatever monitor_screen is in the GLB.
  {
    const c = document.createElement("canvas");
    c.width = c.height = GLOW.texture;
    const g = c.getContext("2d");
    if (g) {
      const r = GLOW.texture / 2;
      const grad = g.createRadialGradient(r, r, 0, r, r, r);
      grad.addColorStop(0, "rgba(255,255,255,1)");
      grad.addColorStop(0.6, "rgba(255,255,255,0.45)");
      grad.addColorStop(0.82, "rgba(255,255,255,0.12)");
      grad.addColorStop(1, "rgba(255,255,255,0)");
      g.fillStyle = grad;
      g.fillRect(0, 0, GLOW.texture, GLOW.texture);
      const tex = new THREE.CanvasTexture(c);
      tex.colorSpace = THREE.SRGBColorSpace;
      const geo = screenMesh.geometry;
      if (!geo.boundingBox) geo.computeBoundingBox();
      const pos = new THREE.Vector3();
      const quat = new THREE.Quaternion();
      const scl = new THREE.Vector3();
      screenMesh.matrixWorld.decompose(pos, quat, scl);
      const size = geo.boundingBox.getSize(new THREE.Vector3()).multiply(scl);
      const halo = new THREE.Mesh(
        new THREE.PlaneGeometry(size.x * GLOW.size, size.y * GLOW.size),
        new THREE.MeshBasicMaterial({
          map: tex, color: GLOW.color, transparent: true, opacity: GLOW.opacity,
          blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false,
        })
      );
      halo.name = "monitor_glow";
      halo.quaternion.copy(quat);
      halo.position.copy(pos).addScaledVector(new THREE.Vector3(0, 0, 1).applyQuaternion(quat), -GLOW_BEHIND);
      halo.renderOrder = 1;
      scene.add(halo);
    }
  }

  // ---- camera + orbit ----
  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(lookAt);
  controls.enablePan = false;
  controls.enableZoom = false; // zoom is ours (zoomTo / stepZoom): OrbitControls would dolly instantly
  controls.enableDamping = !reduce;
  controls.dampingFactor = 0.08;
  controls.rotateSpeed = 0.6;
  controls.minAzimuthAngle = -AZIMUTH_LIMIT;
  controls.maxAzimuthAngle = AZIMUTH_LIMIT;
  controls.minPolarAngle = START_POLAR - POLAR_BAND;
  controls.maxPolarAngle = START_POLAR + POLAR_BAND;

  let fitDistance = 0;
  // Zoom is a fraction of the fitted distance, so it survives resizes. zoomNow follows zoomGoal.
  let zoomGoal = 1;
  let zoomNow = 1;

  // Distance at which the whole monitor fits both ways, with margins.
  function fittedDistance() {
    const tanV = Math.tan(deg(FOV) / 2);
    const tanH = tanV * camera.aspect;
    return Math.max((bodySize.y / 2) * FIT_MARGIN_V / tanV, (bodySize.x / 2) * FIT_MARGIN_H / tanH);
  }

  // THE function that moves the camera along its line of sight to the target. Everything that
  // changes the distance (wheel, pinch, easing, resize, a later glide to a post) ends here.
  const _dir = new THREE.Vector3();
  function setCameraDistance(d) {
    _dir.subVectors(camera.position, controls.target);
    if (_dir.lengthSq() === 0) _dir.setFromSphericalCoords(1, START_POLAR, 0); // first call
    camera.position.copy(controls.target).addScaledVector(_dir.setLength(d), 1);
    needsRender = true;
  }

  const clampZoom = (z) => THREE.MathUtils.clamp(z, ZOOM_NEAR, ZOOM_FAR);

  // Set where the zoom should end up (a fraction of the fit). instant skips the easing; with
  // reduced motion it is always instant.
  function zoomTo(fraction, instant = false) {
    zoomGoal = clampZoom(fraction);
    if (instant || reduce) { zoomNow = zoomGoal; setCameraDistance(fitDistance * zoomNow); }
    else needsRender = true;
  }
  const zoomBy = (ratio, instant = false) => zoomTo(zoomGoal * ratio, instant);

  // Every tick, before controls.update(): ease toward the goal, frame-rate independent.
  function stepZoom(dt) {
    if (zoomNow === zoomGoal) return;
    const k = 1 - Math.exp(-Math.min(dt, 100) / ZOOM_SETTLE_MS);
    zoomNow += (zoomGoal - zoomNow) * k;
    if (Math.abs(zoomGoal - zoomNow) < 0.0005) zoomNow = zoomGoal;
    setCameraDistance(fitDistance * zoomNow);
  }

  // Sets size, projection and framing. Keeps the user's zoom (as a fraction of the fit).
  function resize() {
    const w = Math.max(1, canvas.clientWidth);
    const h = Math.max(1, canvas.clientHeight);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();

    fitDistance = fittedDistance();
    controls.minDistance = fitDistance * ZOOM_NEAR; // safety net only; zoomNow is already inside
    controls.maxDistance = fitDistance * ZOOM_FAR;
    setCameraDistance(fitDistance * zoomNow);
    camera.lookAt(controls.target);
    controls.update();
    needsRender = true;
  }

  resize();
  window.addEventListener("resize", resize);
  window.addEventListener("orientationchange", resize);
  controls.addEventListener("change", () => { needsRender = true; });

  // ---- canvas accessibility ----
  canvas.removeAttribute("aria-hidden");
  canvas.setAttribute("aria-label", text.canvasLabel);

  // ---- picking and input ----
  // ctx.interact for Phase 5 room objects: they call interact.set(mesh, {kind, part, owner}).
  const interact = createPickMap(THREE, camera, canvas);
  interact.set(screenMesh, { kind: "screen", part: "monitor_screen" });

  // screen UV (0..1, origin bottom-left) -> screen canvas coordinates (origin top-left).
  // The plane's UVs run left-to-right, bottom-to-top (see placeholder-room.js), hence 1 - v.
  function tapScreen(hit) {
    if (!hit.uv) return false;
    return screenHandle.input({ type: "click", x: hit.uv.x * SCREEN_W, y: (1 - hit.uv.y) * SCREEN_H });
  }

  // The one place a pick turns into an action. Phase 5 objects get click(part, hit).
  function dispatchTap(picked) {
    const { info, hit } = picked;
    if (info.kind === "screen") return tapScreen(hit);
    if (info.owner && info.owner.click) { info.owner.click(info.part, hit); return true; }
    return false;
  }
  const isScreen = (picked) => !!picked && picked.info.kind === "screen";

  // Height of the screen on the display in CSS px, to turn finger movement into screen units.
  const _corner = new THREE.Vector3();
  function screenPixelHeight() {
    const geo = screenMesh.geometry;
    if (!geo.boundingBox) geo.computeBoundingBox();
    const { min, max } = geo.boundingBox;
    const yAt = (y) => {
      _corner.set((min.x + max.x) / 2, y, (min.z + max.z) / 2).applyMatrix4(screenMesh.matrixWorld).project(camera);
      return _corner.y;
    };
    return Math.abs(yAt(max.y) - yAt(min.y)) * 0.5 * canvas.clientHeight;
  }
  const scrollScreen = (dy) => screenHandle.input({ type: "scroll", dy });

  // Pointer state. A gesture is one primary pointer: tap, orbit (OrbitControls), or a touch
  // drag that started on the screen (scrolls the list, controls disabled until it ends).
  // Two touches down is a pinch: it zooms, never taps, and rotation stays off until every
  // finger is up (OrbitControls would otherwise jump when one finger lifts).
  let down = null; // { id, x, y, t, scrolling, lastY }
  const touches = new Map(); // pointerId -> { x, y } for touches on the canvas
  let pinchDist = 0; // distance between the two fingers at the last move, 0 when not pinching
  let pinchLock = false; // true from the second finger down until all fingers are up
  const syncControls = () => { controls.enabled = !pinchLock && !(down && down.scrolling); };
  function endGesture() {
    down = null;
    syncControls();
  }
  const touchGap = () => {
    const [a, b] = [...touches.values()];
    return Math.hypot(a.x - b.x, a.y - b.y);
  };

  // Window capture so these run before OrbitControls' own listeners on the canvas.
  window.addEventListener("pointerdown", (e) => {
    if (e.target !== canvas) return;
    if (e.pointerType === "touch") {
      touches.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (touches.size === 2) { // second finger: pinch, whatever the first one was doing
        pinchLock = true;
        pinchDist = touchGap();
        endGesture();
        return;
      }
      if (pinchLock) return;
    }
    if (!e.isPrimary || (e.pointerType === "mouse" && e.button !== 0)) return;
    down = { id: e.pointerId, x: e.clientX, y: e.clientY, t: performance.now(), scrolling: false, lastY: e.clientY };
    if (e.pointerType === "touch" && isScreen(interact.pick(e.clientX, e.clientY))) {
      down.scrolling = true;
      controls.enabled = false; // OrbitControls ignores this pointer entirely
      try { canvas.setPointerCapture(e.pointerId); } catch { /* pointerup still arrives on the canvas */ }
    }
  }, { capture: true });

  window.addEventListener("pointermove", (e) => {
    const t = touches.get(e.pointerId);
    if (!t) return;
    t.x = e.clientX;
    t.y = e.clientY;
    if (touches.size === 2 && pinchDist > 0) {
      const gap = touchGap();
      if (gap > 0) zoomBy(pinchDist / gap, true); // fingers apart -> closer
      pinchDist = gap;
    }
  });
  function touchEnd(e) {
    if (!touches.delete(e.pointerId)) return;
    pinchDist = 0;
    if (touches.size === 0) { pinchLock = false; syncControls(); }
  }
  window.addEventListener("pointerup", touchEnd);
  window.addEventListener("pointercancel", touchEnd);

  canvas.addEventListener("pointermove", (e) => {
    if (down && down.scrolling && e.pointerId === down.id) {
      const px = screenPixelHeight();
      if (px > 0) scrollScreen(((down.lastY - e.clientY) * SCREEN_H) / px);
      down.lastY = e.clientY;
      return;
    }
    if (e.pointerType !== "touch") { hoverX = e.clientX; hoverY = e.clientY; hoverDirty = true; }
  });

  function onPointerEnd(e) {
    if (!down || e.pointerId !== down.id) return;
    const d = down;
    endGesture();
    if (e.type !== "pointerup") return;
    const moved = Math.hypot(e.clientX - d.x, e.clientY - d.y);
    if (moved >= TAP_MAX_MOVE || performance.now() - d.t >= TAP_MAX_MS) return;
    const picked = interact.pick(e.clientX, e.clientY);
    if (picked) dispatchTap(picked);
  }
  canvas.addEventListener("pointerup", onPointerEnd);
  canvas.addEventListener("pointercancel", onPointerEnd);
  canvas.addEventListener("lostpointercapture", (e) => { if (down && e.pointerId === down.id && down.scrolling) endGesture(); });

  // Hover: raycast at most once per frame, from the last pointermove, never for touch.
  let hoverX = 0;
  let hoverY = 0;
  let hoverDirty = false;
  let hoverPointer = false;
  function updateHover() {
    if (!hoverDirty) return;
    hoverDirty = false;
    const on = !!interact.pick(hoverX, hoverY);
    if (on !== hoverPointer) { hoverPointer = on; canvas.style.cursor = on ? "pointer" : ""; }
  }
  canvas.addEventListener("pointerleave", () => {
    hoverDirty = false;
    hoverPointer = false;
    canvas.style.cursor = "";
  });

  // Wheel: over the screen it scrolls the list; anywhere else it zooms. ctrl+wheel (trackpad
  // pinch) always zooms and never reaches the browser's page zoom.
  window.addEventListener("wheel", (e) => {
    if (e.target !== canvas) return;
    const k = e.deltaMode === 1 ? WHEEL_LINE_PX : 1;
    if (!e.ctrlKey && isScreen(interact.pick(e.clientX, e.clientY))) {
      const px = screenPixelHeight();
      if (px > 0 && scrollScreen((e.deltaY * k * SCREEN_H) / px)) {
        e.preventDefault();
        e.stopImmediatePropagation();
        return;
      }
    }
    e.preventDefault();
    e.stopImmediatePropagation();
    zoomBy(Math.exp(e.deltaY * k * (e.ctrlKey ? PINCH_WHEEL_ZOOM : WHEEL_ZOOM))); // down/pinch in = farther
  }, { capture: true, passive: false });

  // Keyboard: the canvas is focusable (tab stop); keys go to the screen.
  canvas.tabIndex = 0;
  canvas.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (screenHandle.input({ type: "key", key: e.key })) e.preventDefault();
  });

  // ---- ?debug panel ----
  // Numbers refresh about twice a second. Not a live region, so screen readers stay quiet.
  let updateDebug = null;
  if (params.has("debug")) {
    const labels = text.debug;
    const panel = document.createElement("div");
    panel.className = "room-debug";
    const fpsEl = document.createElement("span");
    fpsEl.className = "room-debug-fps";
    const ratioEl = document.createElement("span");
    ratioEl.className = "room-debug-ratio";
    const buttons = MODES.map((mode) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "room-debug-mode";
      b.textContent = labels[mode];
      b.addEventListener("click", () => { quality.set(mode); refreshDebug(); });
      return [mode, b];
    });
    panel.append(fpsEl, ratioEl, ...buttons.map(([, b]) => b));
    overlay.append(panel);

    function refreshDebug() {
      // quality.fps keeps the last value measured during motion; 0 until there has been motion.
      fpsEl.textContent = labels.fps + " " + (quality.fps ? Math.round(quality.fps) : "\u2013");
      ratioEl.textContent = quality.rung.pixelRatio + "\u00d7";
      for (const [mode, b] of buttons) b.setAttribute("aria-pressed", String(mode === quality.mode));
    }
    let nextDebug = 0;
    updateDebug = (t) => {
      if (t < nextDebug) return;
      nextDebug = t + 500;
      refreshDebug();
    };
    refreshDebug();
  }

  // ---- loop ----
  // Draws only when something changed: orbit or its damping (controls "change"), zoom easing,
  // the screen's frame() returning true, a resize, a quality change. Otherwise the tick is free.
  // The ladder is fed only with the gap between two consecutive drawn ticks, i.e. during motion.
  // Gaps around idle draws (the cursor blink) are not frame times and never reach it.
  let last = 0; // time of the previous loop tick
  let lastDrew = false; // did the previous tick draw?
  function renderFrame(t) {
    const dt = last ? t - last : 0;
    last = t;
    stepZoom(dt);
    controls.update();
    updateHover();
    if (screenHandle.frame(t, dt)) { screenTexture.needsUpdate = true; needsRender = true; }
    const drew = needsRender;
    if (drew) {
      renderer.render(scene, camera);
      needsRender = false;
      if (lastDrew && dt > 0) quality.frame(dt);
    }
    lastDrew = drew;
    if (updateDebug) updateDebug(t);
  }
  function run() { last = 0; lastDrew = false; quality.resume(); renderer.setAnimationLoop(renderFrame); }
  function stop() { renderer.setAnimationLoop(null); quality.pause(); }
  document.addEventListener("visibilitychange", () => (document.hidden ? stop() : run()));

  renderFrame(performance.now()); // first frame, drawn before start() resolves
  if (!document.hidden) run();
}
