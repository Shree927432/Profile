// The room page: renderer, camera, orbit, bloom, the posts screen on the monitor.
// Called by boot.js (see its header for what start() receives).
//
// What lives where, top to bottom:
//   constants          camera, orbit, bloom numbers in one place
//   start()            wires everything; resolves after the first frame is drawn
//     renderer / composer    setPixelRatio() is the one place pixel ratio changes
//     quality                quality.js decides pixel ratio and bloom; applyQuality() applies it
//     scene                  lights + buildPlaceholderRoom() (Phase 4: GLB loader instead)
//     camera + controls      frame() fits the monitor to the aspect on every resize
//     screen                 monitor-posts.js on an offscreen canvas -> CanvasTexture
//     loop                   one setAnimationLoop; stops while the tab is hidden
//
// Input (all on the canvas): pick.js holds the pick map; taps raycast it, the wheel and a
// one-finger drag that starts on the screen scroll the list, keys go to the screen.
// Quality ladder (quality.js): full / auto / smooth. With ?debug a small panel in the overlay
// shows fps and the pixel ratio and switches the mode.
//
// Every word shown comes from content.site.room / content.site.screens.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
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
const ZOOM_NEAR = 0.8; // of the fitted distance
const ZOOM_FAR = 1.2;
// Bloom: threshold sits above the lit room, so only the screen glows.
const BLOOM = { strength: 0.18, radius: 0.4, threshold: 0.9 };
const SCREEN_GLOW = 1.3; // screen colour multiplier (above 1 so it clears the bloom threshold)
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

  // ---- renderer + composer ----
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping; // applied by OutputPass; keeps the screen's colours
  renderer.setClearColor(BACKGROUND);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(BACKGROUND);

  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.05, 30);

  // MSAA target: the composer would otherwise lose antialiasing.
  const target = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, target);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), BLOOM.strength, BLOOM.radius, BLOOM.threshold);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  let needsRender = true;
  // The one place that changes resolution. Both resize their buffers at the current size.
  function setPixelRatio(pr) {
    renderer.setPixelRatio(pr);
    composer.setPixelRatio(pr);
    needsRender = true;
  }
  // Called by the quality ladder at start and on every change. With bloom off the pass is
  // skipped; the screen keeps its colour (OutputPass tone-maps either way), it only loses the glow.
  function applyQuality({ pixelRatio, bloom: bloomOn }) {
    bloom.enabled = bloomOn;
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
  // toneMapped:false only matters when drawing straight to the screen; with the composer the
  // OutputPass tone-maps everything, which is why the neutral curve is used.
  screenMesh.material = new THREE.MeshBasicMaterial({ map: screenTexture, toneMapped: false });
  screenMesh.material.color.setScalar(SCREEN_GLOW);

  // ---- camera + orbit ----
  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(lookAt);
  controls.enablePan = false;
  controls.enableDamping = !reduce;
  controls.dampingFactor = 0.08;
  controls.rotateSpeed = 0.6;
  controls.minAzimuthAngle = -AZIMUTH_LIMIT;
  controls.maxAzimuthAngle = AZIMUTH_LIMIT;
  controls.minPolarAngle = START_POLAR - POLAR_BAND;
  controls.maxPolarAngle = START_POLAR + POLAR_BAND;

  let fitDistance = 0;

  // Distance at which the whole monitor fits both ways, with margins.
  function fittedDistance() {
    const tanV = Math.tan(deg(FOV) / 2);
    const tanH = tanV * camera.aspect;
    return Math.max((bodySize.y / 2) * FIT_MARGIN_V / tanV, (bodySize.x / 2) * FIT_MARGIN_H / tanH);
  }

  // Sets size, projection and framing. Keeps the user's zoom (as a fraction of the fit).
  function resize() {
    const w = Math.max(1, canvas.clientWidth);
    const h = Math.max(1, canvas.clientHeight);
    renderer.setSize(w, h, false);
    composer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();

    const zoom = fitDistance ? camera.position.distanceTo(controls.target) / fitDistance : 1;
    fitDistance = fittedDistance();
    controls.minDistance = fitDistance * ZOOM_NEAR;
    controls.maxDistance = fitDistance * ZOOM_FAR;
    const dist = THREE.MathUtils.clamp(fitDistance * zoom, controls.minDistance, controls.maxDistance);
    const dir = camera.position.clone().sub(controls.target);
    if (dir.lengthSq() === 0) dir.setFromSphericalCoords(1, START_POLAR, 0); // first call
    dir.setLength(dist);
    camera.position.copy(controls.target).add(dir);
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
  let down = null; // { id, x, y, t, scrolling, lastY }
  function endGesture() {
    down = null;
    controls.enabled = true;
  }

  // Window capture so these run before OrbitControls' own listeners on the canvas.
  window.addEventListener("pointerdown", (e) => {
    if (e.target !== canvas) return;
    if (down && e.pointerType === "touch") { endGesture(); return; } // second finger: pinch/zoom goes to the controls
    if (!e.isPrimary || (e.pointerType === "mouse" && e.button !== 0)) return;
    down = { id: e.pointerId, x: e.clientX, y: e.clientY, t: performance.now(), scrolling: false, lastY: e.clientY };
    if (e.pointerType === "touch" && isScreen(interact.pick(e.clientX, e.clientY))) {
      down.scrolling = true;
      controls.enabled = false; // OrbitControls ignores this pointer entirely
      try { canvas.setPointerCapture(e.pointerId); } catch { /* pointerup still arrives on the canvas */ }
    }
  }, { capture: true });

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

  // Wheel over the screen scrolls the list instead of zooming; elsewhere OrbitControls zooms.
  window.addEventListener("wheel", (e) => {
    if (e.target !== canvas || e.ctrlKey) return;
    if (!isScreen(interact.pick(e.clientX, e.clientY))) return;
    const px = screenPixelHeight();
    if (px <= 0) return;
    const k = e.deltaMode === 1 ? WHEEL_LINE_PX : 1;
    if (scrollScreen((e.deltaY * k * SCREEN_H) / px)) {
      e.preventDefault();
      e.stopImmediatePropagation();
    }
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
      fpsEl.textContent = labels.fps + " " + Math.round(quality.fps);
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
  let last = 0; // time of the previous loop tick
  let lastDrawn = 0; // time of the previous drawn frame, for the quality ladder
  function renderFrame(t) {
    const dt = last ? t - last : 0;
    last = t;
    controls.update();
    updateHover();
    if (screenHandle.frame(t, dt)) { screenTexture.needsUpdate = true; needsRender = true; }
    // Reduced motion: draw only when something changed (orbit, resize, screen).
    if (!reduce || needsRender) {
      composer.render();
      needsRender = false;
      if (lastDrawn) quality.frame(t - lastDrawn);
      lastDrawn = t;
    }
    if (updateDebug) updateDebug(t);
  }
  function run() { last = 0; lastDrawn = 0; quality.resume(); renderer.setAnimationLoop(renderFrame); }
  function stop() { renderer.setAnimationLoop(null); quality.pause(); }
  document.addEventListener("visibilitychange", () => (document.hidden ? stop() : run()));

  renderFrame(performance.now()); // first frame, drawn before start() resolves
  if (!document.hidden) run();
}
