// The room page: renderer, camera, orbit, zoom, the posts screen on the monitor.
// Called by boot.js (see its header for what start() receives).
//
// What lives where, top to bottom:
//   constants          camera, orbit, zoom, glow numbers in one place
//   start()            wires everything; resolves after the first frame is drawn
//     renderer               plain renderer.render(); setPixelRatio() is the one place pixel ratio changes
//     quality                quality.js decides the pixel ratio; applyQuality() applies it
//     scene                  lights + buildPlaceholderRoom(), or with ?room&glb the Blender room
//                            (/scene/assets/room.glb through GLTFLoader + DRACOLoader; &uvtest keeps its TOP texture)
//     screen + glow          monitor-posts.js on an offscreen canvas -> CanvasTexture; a soft
//                            halo plane behind it (made here so it survives the GLB)
//     camera + controls      resize() fits the monitor to the aspect; zoom is ours, not OrbitControls'
//     glide                  opening a post: light-up, glide to the close-up, fade, go (glide.js)
//     loop                   one setAnimationLoop; draws only when something changed
//
// Camera: setCameraDistance() is the one function that moves the camera along its line of sight.
// zoomTo()/zoomBy() set the goal (a fraction of the fitted distance); stepZoom() eases toward it.
// The nearest zoom is the close-up (closeUpDistance(): the screen nearly fills the view), the same
// place the glide ends. While the glide runs it alone moves the camera; orbit, zoom, picking and
// keys are locked. Back from the post (bfcache) puts everything back to the start view.
// Input (all on the canvas): pick.js holds the pick map; taps raycast it, the wheel and a
// one-finger drag that starts on the screen scroll the list, keys go to the screen. Wheel off
// the screen, ctrl+wheel (trackpad pinch) and a two-finger touch pinch zoom.
// Quality ladder (quality.js): full / auto / smooth. With ?debug a small panel in the overlay
// shows fps and the pixel ratio and switches the mode.
//
// With ?room&glb (Phase 4, behind a flag): the camera starts at the GLB's room_view (the hero view
// on the approved room plan) and orbits the screen's centre. A lens shift keeps room_view_target in
// the middle of the frame at the start distance and fades out as the camera nears the screen, so the
// close-up and the glide are framed exactly as before. The start is the farthest zoom (the front
// wall is right behind it). Portrait: 70 degrees and no shift, as the sheet's phone frame.
//
// Every word shown comes from content.site.room / content.site.screens.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { buildPlaceholderRoom } from "./placeholder-room.js";
import monitorPosts from "./objects/monitor-posts.js";
import { createPickMap } from "./pick.js";
import { createQuality, MODES } from "./quality.js";
import { createGlide } from "./glide.js";

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
// Zoom, as fractions of the fitted distance. The near end is not a constant: it is the close-up,
// where the screen fills CLOSE_UP_FILL of the view's tighter side (recomputed on resize).
const CLOSE_UP_FILL = 0.92;
const ZOOM_FAR = 1.6;
const ZOOM_SETTLE_MS = 60; // easing time constant: ~250 ms to settle
const WHEEL_ZOOM = 0.0012; // per wheel px: a 100 px notch is about 13 %
const PINCH_WHEEL_ZOOM = 0.01; // ctrl+wheel (trackpad pinch) sends small deltas
// Glow: a cheap stand-in for bloom. An additive plane just behind the screen whose alpha falls off
// as a Gaussian of the distance to the screen's edge, so it has no rim. reach and sigma in metres.
const GLOW = { color: 0x9fd0ff, opacity: 0.14, reach: 0.14, sigma: 0.04, pxPerMetre: 160 };
const GLOW_BEHIND = 0.0005; // metres behind the screen plane
// Opening a post lights the screen up: colour and glow multiplied by 1 + these at full light.
const LIGHT = { screen: 0.22, glow: 0.9 };
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
// The GLB room (?room&glb), built by blender/build_v3.py: Draco geometry, WebP textures. Field of view
// from HERO_V3 in blender/lib/plan_v3.py (vfov, portrait_vfov).
const ROOM_GLB = "/scene/assets/room.glb";
const DRACO_DECODER = "/scene/vendor/three/addons/libs/draco/gltf/";
const ROOM_FOV = 54;
const ROOM_FOV_PORTRAIT = 66;

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

  const useGlb = params.has("glb");
  const uvtest = useGlb && params.has("uvtest");
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
  // Inside the GLB room the "ground" light also reaches the ceiling: a neutral bounce, not floor brown.
  scene.add(new THREE.HemisphereLight(0xcdd5e6, useGlb ? 0x8c8a86 : 0x3e281a, 1.1));
  const sun = new THREE.DirectionalLight(0xffd7a3, 1.6); // early light from the window, left/back
  sun.position.set(-2.5, 2.2, 0.4);
  scene.add(sun);

  let room;
  if (useGlb) {
    const [{ GLTFLoader }, { DRACOLoader }] = await Promise.all([
      import("three/addons/loaders/GLTFLoader.js"),
      import("three/addons/loaders/DRACOLoader.js"),
    ]);
    const draco = new DRACOLoader().setDecoderPath(DRACO_DECODER);
    room = (await new GLTFLoader().setDRACOLoader(draco).loadAsync(ROOM_GLB)).scene;
    draco.dispose(); // frees the decoder worker; the geometry is decoded
  } else {
    room = buildPlaceholderRoom(THREE);
  }
  scene.add(room);
  scene.updateMatrixWorld(true);

  // Phase 4: the screen and body come out of the GLB by name, never by held reference.
  const screenMesh = room.getObjectByName("monitor_screen");
  const bodyMesh = room.getObjectByName("monitor_body");
  if (!screenMesh || !bodyMesh) throw new Error("room has no monitor_screen / monitor_body");
  const lookAt = screenMesh.getWorldPosition(new THREE.Vector3());
  const bodySize = new THREE.Box3().setFromObject(bodyMesh).getSize(new THREE.Vector3());
  // The screen in world space: size (metres), rotation, and the direction it faces.
  const screenQuat = new THREE.Quaternion();
  const screenSize = new THREE.Vector3();
  {
    const geo = screenMesh.geometry;
    if (!geo.boundingBox) geo.computeBoundingBox();
    const scl = new THREE.Vector3();
    screenMesh.matrixWorld.decompose(new THREE.Vector3(), screenQuat, scl);
    geo.boundingBox.getSize(screenSize).multiply(scl);
  }
  const screenNormal = new THREE.Vector3(0, 0, 1).applyQuaternion(screenQuat);

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
  const open = (url) => startGlide(url); // the screen asks for a post: glide in, then go

  // screenHandle.input({type:"key"|"click"|"scroll"|"open", ...}) returns true if it used the event.
  const screenHandle = monitorPosts.mount({
    canvas: screenCanvas, ctx: screenCtx, width: SCREEN_W, height: SCREEN_H,
    audio: null, content, open, reduce, say,
  });

  // &uvtest: the GLB's own TOP texture stays on the screen (the UV check); otherwise the posts.
  const glbMap = uvtest ? screenMesh.material.map : null;
  const screenTexture = new THREE.CanvasTexture(screenCanvas);
  screenTexture.colorSpace = THREE.SRGBColorSpace;
  screenTexture.minFilter = THREE.LinearMipmapLinearFilter;
  screenTexture.magFilter = THREE.LinearFilter;
  screenTexture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  screenMesh.material.dispose();
  // toneMapped:false: the screen shows the posts colours exactly as drawn.
  screenMesh.material = new THREE.MeshBasicMaterial({ map: glbMap || screenTexture, toneMapped: false });

  // ---- glow: soft halo behind the screen (not pickable, not in the pick map) ----
  // Placed from the screen's world transform, so it follows whatever monitor_screen is in the GLB.
  // Alpha is exp(-(d/sigma)^2), d = distance outside the screen rectangle: no disc, no rim.
  let halo = null;
  {
    const W = screenSize.x + GLOW.reach * 2;
    const H = screenSize.y + GLOW.reach * 2;
    const c = document.createElement("canvas");
    c.width = Math.round(W * GLOW.pxPerMetre);
    c.height = Math.round(H * GLOW.pxPerMetre);
    const g = c.getContext("2d");
    if (g) {
      const img = g.createImageData(c.width, c.height);
      for (let y = 0; y < c.height; y++) {
        for (let x = 0; x < c.width; x++) {
          const dx = Math.max(0, Math.abs((x + 0.5) / GLOW.pxPerMetre - W / 2) - screenSize.x / 2);
          const dy = Math.max(0, Math.abs((y + 0.5) / GLOW.pxPerMetre - H / 2) - screenSize.y / 2);
          const i = (y * c.width + x) * 4;
          img.data[i] = img.data[i + 1] = img.data[i + 2] = 255;
          img.data[i + 3] = Math.round(255 * Math.exp(-(dx * dx + dy * dy) / (GLOW.sigma * GLOW.sigma)));
        }
      }
      g.putImageData(img, 0, 0);
      const tex = new THREE.CanvasTexture(c);
      tex.colorSpace = THREE.SRGBColorSpace;
      halo = new THREE.Mesh(
        new THREE.PlaneGeometry(W, H),
        new THREE.MeshBasicMaterial({
          map: tex, color: GLOW.color, transparent: true, opacity: GLOW.opacity,
          blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false,
        })
      );
      halo.name = "monitor_glow";
      halo.quaternion.copy(screenQuat);
      halo.position.copy(lookAt).addScaledVector(screenNormal, -GLOW_BEHIND);
      halo.renderOrder = 1;
      scene.add(halo);
    }
  }

  // Opening a post: k = 0 at rest, 1 fully lit. The row itself is lit by the screen's own
  // selection highlight; this brightens the whole screen and its glow a little.
  function light(k) {
    screenMesh.material.color.setScalar(1 + LIGHT.screen * k);
    if (halo) halo.material.opacity = GLOW.opacity * (1 + LIGHT.glow * k);
    needsRender = true;
  }

  // ---- camera + orbit ----
  // With the GLB: the start position is room_view; the polar band centres on it.
  const viewNode = useGlb ? room.getObjectByName("room_view") : null;
  const viewTargetNode = useGlb ? room.getObjectByName("room_view_target") : null;
  if (useGlb && (!viewNode || !viewTargetNode)) throw new Error("room.glb has no room_view / room_view_target");
  const viewPos = viewNode ? viewNode.getWorldPosition(new THREE.Vector3()) : null;
  const viewTarget = viewTargetNode ? viewTargetNode.getWorldPosition(new THREE.Vector3()) : null;
  const startSph = viewPos ? new THREE.Spherical().setFromVector3(viewPos.clone().sub(lookAt)) : null;
  const startPolar = startSph ? startSph.phi : START_POLAR;
  // The azimuth band centres on the start view: 0 (straight on) in the placeholder room, room_view's
  // azimuth in the GLB (plan v3's screen faces +X, room_view sees it from about 57 degrees off its axis).
  const startAzimuth = startSph ? startSph.theta : 0;
  const zoomFar = useGlb ? 1 : ZOOM_FAR;

  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(lookAt);
  controls.enablePan = false;
  controls.enableZoom = false; // zoom is ours (zoomTo / stepZoom): OrbitControls would dolly instantly
  controls.enableDamping = !reduce;
  controls.dampingFactor = 0.08;
  controls.rotateSpeed = 0.6;
  controls.minAzimuthAngle = startAzimuth - AZIMUTH_LIMIT;
  controls.maxAzimuthAngle = startAzimuth + AZIMUTH_LIMIT;
  controls.minPolarAngle = startPolar - POLAR_BAND;
  controls.maxPolarAngle = startPolar + POLAR_BAND;

  let fitDistance = 0;
  let zoomNear = 1; // the close-up as a fraction of the fit; set by resize()
  // Zoom is a fraction of the fitted distance, so it survives resizes. zoomNow follows zoomGoal.
  let zoomGoal = 1;
  let zoomNow = 1;

  // Distance at which the whole monitor fits both ways, with margins. With the GLB: room_view's.
  function fittedDistance() {
    if (viewPos) return viewPos.distanceTo(lookAt);
    const tanV = Math.tan(deg(camera.fov) / 2);
    const tanH = tanV * camera.aspect;
    return Math.max((bodySize.y / 2) * FIT_MARGIN_V / tanV, (bodySize.x / 2) * FIT_MARGIN_H / tanH);
  }

  // Distance, straight on, at which the screen fills CLOSE_UP_FILL of the view's tighter side.
  // The nearest zoom, and where the glide ends.
  function closeUpDistance() {
    const tanV = Math.tan(deg(camera.fov) / 2) * CLOSE_UP_FILL;
    const tanH = Math.tan(deg(camera.fov) / 2) * camera.aspect * CLOSE_UP_FILL;
    return Math.max(screenSize.y / 2 / tanV, screenSize.x / 2 / tanH);
  }

  // THE function that moves the camera along its line of sight to the target. Everything that
  // changes the distance (wheel, pinch, easing, resize) ends here. The glide (glide.js) moves the
  // camera itself while it runs, and nothing else does then.
  const _dir = new THREE.Vector3();
  function setCameraDistance(d) {
    _dir.subVectors(camera.position, controls.target);
    camera.position.copy(controls.target).addScaledVector(_dir.setLength(d), 1);
    needsRender = true;
  }

  // The start view's direction: START_POLAR, straight on (GLB: towards room_view). resize() then sets
  // the distance.
  function placeAtStart() {
    if (viewPos) camera.position.copy(viewPos);
    else camera.position.setFromSphericalCoords(1, START_POLAR, 0).add(controls.target);
  }

  const clampZoom = (z) => THREE.MathUtils.clamp(z, zoomNear, zoomFar);

  // Lens shift (GLB, landscape): where room_view_target appears, in NDC, when the camera at room_view
  // looks at the screen's centre. Set by resize(); applyShift() moves the frame by it, scaled from 1 at
  // the fitted distance to 0 at the close-up, so the screen is centred whenever the camera is near it.
  const shiftNdc = new THREE.Vector2();
  const _probe = new THREE.PerspectiveCamera();
  function measureShift() {
    shiftNdc.set(0, 0);
    if (!viewPos || camera.aspect < 1) return;
    _probe.copy(camera);
    _probe.clearViewOffset();
    _probe.position.copy(viewPos);
    _probe.lookAt(lookAt);
    _probe.updateMatrixWorld(true);
    const p = viewTarget.clone().project(_probe);
    shiftNdc.set(p.x, p.y);
  }
  function applyShift() {
    if (!viewPos) return;
    const near = closeUpDistance();
    const k = THREE.MathUtils.clamp((camera.position.distanceTo(lookAt) - near) / Math.max(1e-6, fitDistance - near), 0, 1);
    const w = Math.max(1, canvas.clientWidth);
    const h = Math.max(1, canvas.clientHeight);
    if (k === 0 || (shiftNdc.x === 0 && shiftNdc.y === 0)) {
      if (camera.view && camera.view.enabled) camera.clearViewOffset();
      return;
    }
    camera.setViewOffset(w, h, (shiftNdc.x * k * w) / 2, (-shiftNdc.y * k * h) / 2, w, h);
  }

  // Set where the zoom should end up (a fraction of the fit). instant skips the easing; with
  // reduced motion it is always instant. Ignored during the glide.
  function zoomTo(fraction, instant = false) {
    if (glide.active) return;
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
    if (useGlb) camera.fov = camera.aspect < 1 ? ROOM_FOV_PORTRAIT : ROOM_FOV;
    camera.clearViewOffset(); // applyShift() sets it again for the new size
    camera.updateProjectionMatrix();

    fitDistance = fittedDistance();
    zoomNear = Math.min(1, closeUpDistance() / fitDistance);
    zoomGoal = clampZoom(zoomGoal);
    zoomNow = clampZoom(zoomNow);
    controls.minDistance = fitDistance * zoomNear; // safety net only; zoomNow is already inside
    controls.maxDistance = fitDistance * zoomFar;
    measureShift();
    needsRender = true;
    if (glide.active) { applyShift(); return; } // the glide owns the camera; it reads closeUpDistance() each tick
    setCameraDistance(fitDistance * zoomNow);
    camera.lookAt(controls.target);
    controls.update();
    applyShift();
  }

  // ---- glide (opening a post) ----
  const glide = createGlide({
    THREE, camera, target: controls.target, normal: screenNormal,
    closeUp: closeUpDistance, light, reduce,
  });
  function startGlide(url) {
    if (glide.active) return;
    glide.go(url);
    endGesture(); // controls off (see syncControls)
    zoomGoal = zoomNow; // a zoom still easing stops where it is
    hoverDirty = false;
    hoverPointer = false;
    canvas.style.cursor = "";
  }
  // Back from the post: the browser may restore this page as it was left, close up and faded.
  window.addEventListener("pageshow", (e) => {
    if (!e.persisted) return;
    glide.reset();
    controls.enableDamping = false;
    controls.update(); // drops any orbit momentum left from before the glide
    controls.enableDamping = !reduce;
    zoomGoal = zoomNow = 1;
    placeAtStart();
    touches.clear();
    pinchDist = 0;
    pinchLock = false;
    endGesture();
    resize();
  });

  placeAtStart();
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
  const syncControls = () => { controls.enabled = !glide.active && !pinchLock && !(down && down.scrolling); };
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
    if (e.target !== canvas || glide.active) return; // no taps, drags or pinches during the glide
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
    if (e.pointerType !== "touch" && !glide.active) { hoverX = e.clientX; hoverY = e.clientY; hoverDirty = true; }
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
    if (glide.active) { e.preventDefault(); e.stopImmediatePropagation(); return; }
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
    if (glide.active) return; // Tab still works; nothing else reaches the screen
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
    // For measuring from the console or a test script: draw calls and triangles of the last frame.
    window.roomDebug = { info: renderer.info };

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
  // Draws only when something changed: orbit or its damping (controls "change"), zoom easing, the glide,
  // the screen's frame() returning true, a resize, a quality change. Otherwise the tick is free.
  // The ladder is fed only with the gap between two consecutive drawn ticks, i.e. during motion.
  // Gaps around idle draws (the cursor blink) are not frame times and never reach it.
  let last = 0; // time of the previous loop tick
  let lastDrew = false; // did the previous tick draw?
  function renderFrame(t) {
    const dt = last ? t - last : 0;
    last = t;
    if (glide.active) {
      if (glide.step(dt)) needsRender = true;
    } else {
      stepZoom(dt);
      controls.update();
      updateHover();
    }
    if (screenHandle.frame(t, dt)) { screenTexture.needsUpdate = true; needsRender = true; }
    const drew = needsRender;
    if (drew) {
      applyShift();
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
