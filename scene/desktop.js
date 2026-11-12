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
// With ?room&glb (Phase 4, behind a flag; since 2026-11-12 the free camera below replaces the orbit, the zoom
// and the lens shift in the GLB room, so this paragraph describes the placeholder's orbit and the old GLB start):
// the camera starts at the GLB's room_view (the hero view on the approved room plan) and orbits the screen's centre. A lens shift keeps room_view_target in
// the middle of the frame at the start distance and fades out as the camera nears the screen, so the
// close-up and the glide are framed exactly as before. The start is the farthest zoom (the front
// wall is right behind it). Portrait (2026-11-11): camera_phone's framing, 60 degrees, its target centred
// by the same lens shift.
//
// Camera moves (2026-11-11, camera-moves.js, the GLB room only): the first visit in a browser session opens
// on camera_intro (the window, the city), holds, then moves back and round to the hero along a curve; a tap
// or Enter starts it sooner, any drag, wheel, pinch or other key hands the room over (the move runs down
// while the picture blends to the orbit, which already follows the input). The overlay gets the site nav's
// About as a toggle: the camera turns to camera_about and back (Escape too). The orbit is never moved by
// these: drawShown() draws the move's pose and puts the orbit's pose back. Reduced motion: no intro, About cuts.
//
// The free camera (2026-11-12, camera-moves.js + room-space.js): after the intro and every flight the visitor drives
// the camera: drag looks, wheel or pinch moves along the look, WASD and arrows walk, all kept in the room's free
// space; at a stop a drag circles the component and the wheel changes the distance. OrbitControls: placeholder only.
//
// Stops (2026-11-11, stops.js): click a component and the camera flies to its close-up (flyTo); drag looks
// around a little there, Escape, Back or a click on empty wall or floor goes back (back()): music-side stops
// to the About view, everything else to the desk. Every room mesh is in the pick map; stops.classify() says
// which stop a hit is. The overlay gets Back and a keyboard list of the stops; names from content.site.room.stops.
//
// Every word shown comes from content.site.room / content.site.screens.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { buildPlaceholderRoom } from "./placeholder-room.js";
import monitorPosts from "./objects/monitor-posts.js";
import { createPickMap } from "./pick.js";
import { batchRoom } from "./batch.js";
import { createQuality, MODES } from "./quality.js";
import { createGlide } from "./glide.js";
import { createMoves } from "./camera-moves.js";
import { createStops } from "./stops.js";
import { createRoomSpace } from "./room-space.js";
import { loadRoomLight, applyRoomLight, createBloom, loadCarsLight, applyCarsLight } from "./room-light.js";

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
// Logical height of the screen canvas (backing store is 2x); the width follows the screen mesh's
// aspect (16:10 in the placeholder room: 640x400 and 400x250, the decision of 2026-10-19; 16:9 on
// the v3 Studio Display, 2026-11-01). Under 480 CSS px wide the screen is the narrow layout.
// Chosen once at start; picking uses the same numbers.
const SCREEN_WIDE_H = 400;
const SCREEN_NARROW_H = 250;
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
// The dusk light (2026-11-01, scene/room-light.js): bloom on desktop only (not on touch or narrow screens), and only
// the top quality rung. threshold is in the scene's linear light after EXPOSURE (room-light.json).
const BLOOM = { strength: 0.3, radius: 0.45, threshold: 1.0, minWidth: 768 };
// The car display (2026-11-08): the first deferred asset. cars.glb (blender/components/cars.py) loads only after the
// room is on screen and has drawn its first frames, when the browser is idle, so it costs the first load nothing. It
// fades in over FADE_MS (reduced motion: it just appears). Not on the quality ladder's bottom rung (quality.lowest):
// never loaded there, hidden if the ladder steps down to it later. &nocars leaves it out (measuring).
const CARS = { url: "/scene/assets/cars.glb", fadeMs: 700, afterFrames: 3, idleTimeout: 1500 };
// Camera moves (2026-11-11, scene/camera-moves.js), the GLB room only. Positions and targets come from the GLB's
// empties (camera_intro, camera_about, camera_phone and their _target); field of view from plan v3 (INTRO, ABOUT,
// PHONE_V3), with portrait values of our own where plan v3 has none. Waypoints are in the GLB's metres (Y up,
// the window's wall at -Z). The intro plays once per browser session (sessionStorage); &intro forces it.
const MOVES = {
  introFov: 50, introFovPortrait: 50,
  // Portrait: camera_intro's frame is a narrow strip with the meeting stiles and both handles down its middle.
  // Moved this far right (metres, still on the window's line, still looking straight out) the phone looks
  // through the right sash at the city and the monstera. 0 = camera_intro as it is.
  introPortraitShiftX: 0.35,
  aboutFov: 50, aboutFovPortrait: 72,
  phoneFov: 60,
  holdMs: 1800, // the window, still, before the move starts by itself (a tap starts it sooner)
  introMs: 5200, // back from the window and round to the desk
  introLookDelay: 0.14, // the camera pulls straight back first, then turns
  introVia: [[0.52, 1.6, -0.45], [0.86, 1.74, 0.25]],
  aboutMs: 3000, // the turn to the music side, and back (about 120 degrees of turn: slower reads as a pan, not a whip)
  aboutLookLead: 0.1, // the look arrives a little before the camera does
  aboutVia: [[0.2, 1.74, 1.3]],
  seenKey: "room-intro-seen",
  // Stops (scene/stops.js): field of view at a close-up, the room's inside (plan v3: 4.40 x 4.20 x 3.00, GLB metres)
  // and how far a look-around drag turns (a full canvas height = this many turns).
  stopFov: 50, stopFovPortrait: 60,
  roomInside: [[-2.2, 0, -2.1], [2.2, 3.0, 2.1]],
  // The free camera (2026-11-12): a drag across the canvas's height turns this many full turns; the wheel moves
  // this many metres per pixel of delta (a 100 px notch: 25 cm); a two-finger pinch this many per pixel of
  // spread; the keys (WASD, arrows) walk at this speed.
  lookDrag: 0.45,
  wheelMove: 0.0025, pinchWheelMove: 0.012, pinchMove: 0.006,
  walk: 1.2, // m/s
  orbitMin: 0.5, orbitLeave: 1.8, // at a stop, of its framing distance
  circleKeys: 1.2, // rad/s, the arrow keys circling a stop
};

export async function start({ canvas, content, overlay, params, reduce }) {
  const text = content.site.room;
  const SCREEN_H = window.innerWidth < NARROW_BELOW ? SCREEN_NARROW_H : SCREEN_WIDE_H;

  // ---- renderer ----
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping; // the screen material opts out (toneMapped: false)
  renderer.setClearColor(BACKGROUND);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(BACKGROUND);

  const useGlb = params.has("glb");
  const uvtest = useGlb && params.has("uvtest");
  // The dusk light files load while the GLB does (the GLB room only).
  const lightLoad = useGlb ? loadRoomLight(THREE) : null;
  const bloomAllowed = useGlb && !params.has("nobloom") && window.innerWidth >= BLOOM.minWidth &&
    !window.matchMedia("(pointer: coarse)").matches;
  let post = null; // the bloom composer, once made (createBloom)
  let bloomOn = false;
  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.05, 30);

  // The loop draws only when this is true (see renderFrame). Anything that changes the picture sets it.
  let needsRender = true;
  // The one place that changes resolution.
  function setPixelRatio(pr) {
    renderer.setPixelRatio(pr);
    if (post) post.setPixelRatio(pr);
    needsRender = true;
  }
  // Called by the quality ladder at start and on every change.
  let carsRoot = null; // the car display once loaded (see loadCars)
  function applyQuality({ pixelRatio, bloom }) {
    bloomOn = !!bloom;
    setPixelRatio(pixelRatio);
    if (carsRoot) carsRoot.visible = !quality.lowest; // quality exists by the time the cars do
  }
  const quality = createQuality({ dpr: window.devicePixelRatio || 1, reduce, apply: applyQuality, bloom: bloomAllowed });

  // ---- scene ----
  // The placeholder room is lit live; the GLB room by its bake (scene/room-light.js), no live lights.
  if (!useGlb) {
    scene.add(new THREE.HemisphereLight(0xcdd5e6, 0x3e281a, 1.1));
    const sun = new THREE.DirectionalLight(0xffd7a3, 1.6); // early light from the window, left/back
    sun.position.set(-2.5, 2.2, 0.4);
    scene.add(sun);
  }

  let room;
  let roomExposure = null; // the dusk light's exposure, for the deferred cars
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
  if (useGlb) batchRoom(room); // keys, pads, knobs, faders: one draw call per material (batch.js)
  if (useGlb) {
    renderer.toneMapping = THREE.AgXToneMapping;
    const exp = parseFloat(params.get("exp") || ""); // &exp=0.5: tuning only
    const light = await lightLoad.catch((e) => { console.warn("room light:", e); return null; });
    if (light) applyRoomLight(THREE, { renderer, scene, room, light, exposure: Number.isFinite(exp) ? exp : undefined });
    if (light) roomExposure = Number.isFinite(exp) ? exp : light.json.exposure;
    else scene.add(new THREE.HemisphereLight(0xcdd5e6, 0x8c8a86, 1.1)); // the bake files missing: plain light, still usable
    if (light && bloomAllowed) {
      post = await createBloom(THREE, { renderer, scene, camera, ...BLOOM });
      post.setPixelRatio(renderer.getPixelRatio());
    }
  }

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
  const SCREEN_W = Math.round((SCREEN_H * screenSize.x) / screenSize.y);

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
  // The other camera empties (camera_intro, camera_about, camera_phone and their _target), or null.
  const empty = (name) => {
    const n = useGlb ? room.getObjectByName(name) : null;
    return n ? n.getWorldPosition(new THREE.Vector3()) : null;
  };
  const cams = {
    intro: empty("camera_intro"), introTarget: empty("camera_intro_target"),
    about: empty("camera_about"), aboutTarget: empty("camera_about_target"),
    phone: empty("camera_phone"), phoneTarget: empty("camera_phone_target"),
  };
  const hasPhone = !!(cams.phone && cams.phoneTarget);
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
  // Portrait (2026-11-11): camera_phone's framing, its target centred the same way (camera_phone stands where
  // room_view does). Without the phone empties: no shift, as before.
  const portrait = () => camera.aspect < 1;
  // The GLB room is driven by the free camera (camera-moves.js); OrbitControls stays for the placeholder room.
  const freeCam = useGlb;
  function measureShift() {
    shiftNdc.set(0, 0);
    if (!viewPos) return;
    if (portrait() && !hasPhone) return;
    _probe.copy(camera);
    _probe.clearViewOffset();
    _probe.position.copy(portrait() ? cams.phone : viewPos);
    _probe.lookAt(lookAt);
    _probe.updateMatrixWorld(true);
    const p = (portrait() ? cams.phoneTarget : viewTarget).clone().project(_probe);
    shiftNdc.set(p.x, p.y);
  }
  // The shift's strength for where the orbit camera is now: 1 at the start distance, 0 at the close-up.
  function shiftFactor() {
    if (!viewPos || freeCam) return 0; // the free camera has no lens shift
    const near = closeUpDistance();
    return THREE.MathUtils.clamp((camera.position.distanceTo(lookAt) - near) / Math.max(1e-6, fitDistance - near), 0, 1);
  }
  function setShift(k) {
    if (!viewPos) return;
    const w = Math.max(1, canvas.clientWidth);
    const h = Math.max(1, canvas.clientHeight);
    if (k === 0 || (shiftNdc.x === 0 && shiftNdc.y === 0)) {
      if (camera.view && camera.view.enabled) camera.clearViewOffset();
      return;
    }
    camera.setViewOffset(w, h, (shiftNdc.x * k * w) / 2, (-shiftNdc.y * k * h) / 2, w, h);
  }
  const applyShift = () => setShift(shiftFactor());

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
    if (post) post.setSize(w, h);
    camera.aspect = w / h;
    if (useGlb) camera.fov = camera.aspect >= 1 ? ROOM_FOV : hasPhone ? MOVES.phoneFov : ROOM_FOV_PORTRAIT;
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
    // The intro's hold, and a place the visitor has not moved from, take the new aspect's framing; a free
    // pose keeps where it is and takes the aspect's field of view.
    if (moves.phase === "still" && moves.tag === "intro") moves.still(introPose(), "intro");
    else if (moves.phase === "free") {
      const id = moves.moved ? "" : moves.tag;
      if (id === "desk") moves.free(heroPose(), "desk");
      else if (isPlace(id)) { const p = poseFor(id); moves.free(p.pose, id, p.orbit); }
      else moves.shown.fov = freeFov();
    }
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
    if (glide.active || moves.moving) return;
    if (freeCam) { // the glide starts from what is on screen and owns the camera until the post opens
      const sh = moves.shown;
      camera.position.copy(sh.pos);
      camera.quaternion.copy(sh.quat);
      camera.fov = sh.fov;
      camera.clearViewOffset();
      camera.updateProjectionMatrix();
      moves.reset();
    }
    glide.go(url);
    endGesture(); // controls off (see syncControls)
    zoomGoal = zoomNow; // a zoom still easing stops where it is
    hoverDirty = false;
    hoverPointer = false;
    canvas.style.cursor = "";
  }
  // ---- camera moves: the intro, About and back (camera-moves.js) ----
  const V3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
  // The orbit stays the home view; moves draw over it (see renderFrame). Reduced motion: no intro, About cuts.
  const roomInside = new THREE.Box3(V3(MOVES.roomInside[0]), V3(MOVES.roomInside[1]));
  const space = useGlb ? createRoomSpace({ THREE, inside: roomInside }) : null;
  const moves = createMoves({ THREE, reduce, constrain: space ? space.constrain : null, isFree: space ? space.isFree : null });
  const introVia = MOVES.introVia.map(V3);
  const aboutVia = MOVES.aboutVia.map(V3);
  const canIntro = !!(cams.intro && cams.introTarget);
  const canAbout = !!(cams.about && cams.aboutTarget);
  const _introPos = new THREE.Vector3();
  const _introTarget = new THREE.Vector3();
  function introPose() {
    const dx = portrait() ? MOVES.introPortraitShiftX : 0;
    _introPos.copy(cams.intro).x += dx;
    _introTarget.copy(cams.introTarget).x += dx;
    return moves.makePose(_introPos, _introTarget, portrait() ? MOVES.introFovPortrait : MOVES.introFov);
  }
  const aboutPose = () => moves.makePose(cams.about, cams.aboutTarget, portrait() ? MOVES.aboutFovPortrait : MOVES.aboutFov);
  // The desk: room_view looking at room_view_target (portrait: camera_phone at its target), no lens shift.
  const freeFov = () => (camera.aspect >= 1 ? ROOM_FOV : hasPhone ? MOVES.phoneFov : ROOM_FOV_PORTRAIT);
  function heroPose() {
    const ph = portrait() && hasPhone;
    return moves.makePose(ph ? cams.phone : viewPos, ph ? cams.phoneTarget : viewTarget, freeFov());
  }
  let aboutOn = false;
  let aboutButton = null; // made with the overlay below, when the site's nav has an About link
  const introRunning = () => moves.tag === "intro" && (moves.phase === "still" || moves.phase === "move");
  const holding = () => moves.tag === "intro" && moves.phase === "still";
  let holdLeft = 0; // ms of the intro's hold still to go
  let carsWaiting = null; // the cars, loaded during a move, are added when it ends (no hitch mid-move)

  function playIntro() {
    if (!holding()) return;
    moves.go({ to: heroPose(), via: introVia, ms: MOVES.introMs, lookDelay: MOVES.introLookDelay, tag: "intro", endTag: "desk" });
    needsRender = true;
  }
  // Any drag, wheel, pinch or key during the intro: the visitor has the room now (the free camera, where the
  // picture is; the move's speed runs down instead of stopping dead).
  function handOver() {
    if (!introRunning()) return;
    moves.handOver();
    needsRender = true;
  }
  // ---- stops: click a component and fly to it (stops.js), the GLB room only ----
  // Where the visitor is: "desk" (the orbit), "about" (the music side's overview), a stop's id, or the intro.
  // About is the music side's overview stop; its four stops go Back to it, every other stop Backs to the desk.
  const stops = useGlb ? createStops({ THREE, root: room, bounds: roomInside }) : null;
  const keys = new Set(); // walking keys held down (KeyW, ArrowUp, ...)
  const stopNames = text.stops || {};
  const nameOf = (id) => stopNames[id] || "";
  let obstacles = []; // every mesh a flight must not pass through (the city and the halo are not in it)
  function collectObstacles() {
    obstacles = [];
    scene.traverseVisible((o) => { if (o.isMesh && o !== halo && !/^city/.test(o.name)) obstacles.push(o); });
  }
  const _stopPos = new THREE.Vector3();
  function poseFor(id) {
    if (id === "about") return { pose: aboutPose() };
    const st = stops.byId.get(id);
    if (st.view === "intro") return { pose: introPose() };
    const fov = portrait() ? MOVES.stopFovPortrait : MOVES.stopFov;
    const { dist } = stops.place(st, camera.aspect, fov, _stopPos);
    // At a component a drag circles it (owner, 2026-11-12: "Circle the component"): never nearer than
    // orbitMin of the framing distance, and dollying out past orbitLeave of it turns the drag back to looking.
    const orbit = { center: st.center, min: Math.max(0.35, dist * MOVES.orbitMin), leave: dist * MOVES.orbitLeave };
    return { pose: moves.makePose(_stopPos, st.center, fov), orbit };
  }
  const isPlace = (id) => id === "about" || (!!stops && stops.byId.has(id));
  // "intro" (hold or move), a place's id while flying there or standing where it put the camera ("desk",
  // "about", a stop), or "free" once the visitor has looked or moved away from it.
  function currentId() {
    if (!freeCam) return "desk";
    if (moves.phase === "still") return "intro";
    if (moves.phase === "move") return moves.tag;
    if (moves.phase === "free") return moves.moved ? "free" : moves.tag || "free";
    return "desk";
  }
  const parentOf = (id) => (stops && stops.byId.has(id) && stops.byId.get(id).parent === "about" ? "about" : "desk");
  let backButton = null; // made with the overlay below
  // The bar follows where the visitor is: About pressed on the music side, Back away from the desk.
  let navId = "";
  function updateNav() {
    const id = currentId();
    if (id === navId) return;
    navId = id;
    aboutOn = id === "about" || (isPlace(id) && parentOf(id) === "about");
    if (aboutButton) aboutButton.setAttribute("aria-pressed", String(aboutOn));
    if (backButton) backButton.hidden = id === "desk" || id === "intro";
  }
  const _q0 = new THREE.Quaternion();
  // Fly to a stop, the About view, or the desk ("desk"). Arrives in the free camera. Reduced motion: a cut.
  function flyTo(id) {
    if (!useGlb || glide.active || (id !== "desk" && !isPlace(id))) return;
    if (id === "about" && !canAbout) return;
    const cur = currentId();
    if (id === cur && !moves.moving) return;
    endGesture();
    keys.clear();
    hoverDirty = false;
    setHover(false, "");
    const target = id === "desk" ? { pose: heroPose() } : poseFor(id);
    const fromPos = moves.shown.pos;
    _q0.copy(moves.shown.quat);
    const aboutTurn = (id === "about" && cur === "desk") || (id === "desk" && cur === "about");
    const via = aboutTurn ? aboutVia : stops ? stops.via(fromPos, target.pose.pos, obstacles) : [];
    const ms = aboutTurn ? MOVES.aboutMs
      : THREE.MathUtils.clamp(950 + 330 * fromPos.distanceTo(target.pose.pos) + 500 * _q0.angleTo(target.pose.quat), 1100, 2600);
    const name = nameOf(id === "about" ? "music" : id);
    if (reduce) {
      moves.free(target.pose, id, target.orbit);
      if (name) say(name);
    } else {
      moves.go({
        to: target.pose, via, ms, lookLead: aboutTurn ? MOVES.aboutLookLead : 0.06,
        tag: id, orbit: target.orbit, onEnd: () => { if (name) say(name); },
      });
    }
    updateNav();
    needsRender = true;
  }
  // Back: from a music-side stop to the About view, from anywhere else (a stop, About, a free pose) to the desk.
  function back() {
    const cur = currentId();
    if (cur === "desk" || cur === "intro") return false;
    flyTo(isPlace(cur) && cur !== "about" ? parentOf(cur) : "desk");
    return true;
  }
  const setAbout = (on) => flyTo(on ? "about" : "desk");

  // The intro: once per browser session, never with reduced motion; &intro forces it (footage, testing).
  function introWanted() {
    if (!useGlb || reduce || !canIntro) return false;
    if (params.has("intro")) return true;
    try {
      if (sessionStorage.getItem(MOVES.seenKey)) return false;
      sessionStorage.setItem(MOVES.seenKey, "1");
    } catch { /* storage blocked: play it */ }
    return true;
  }

  // Back from the post: the browser may restore this page as it was left, close up and faded.
  window.addEventListener("pageshow", (e) => {
    if (!e.persisted) return;
    glide.reset();
    if (freeCam) moves.free(heroPose(), "desk");
    keys.clear();
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
  if (introWanted()) { moves.still(introPose(), "intro"); holdLeft = MOVES.holdMs; }
  else if (freeCam) moves.free(heroPose(), "desk");
  window.addEventListener("resize", resize);
  window.addEventListener("orientationchange", resize);
  controls.addEventListener("change", () => { needsRender = true; });

  // ---- canvas accessibility ----
  canvas.removeAttribute("aria-hidden");
  canvas.setAttribute("aria-label", text.canvasLabel);

  // ---- About in the room ----
  // The site's own About entry (the header nav's link, its words as the site shows them) goes into the
  // overlay as a toggle: pressed, the camera turns to the music side; again (or Escape), back to the desk.
  // No nav link, no button: no words are made up here.
  const navAbout = document.querySelector('.site-nav a[href="/about"]');
  if (canAbout && navAbout && navAbout.textContent.trim()) {
    aboutButton = document.createElement("button");
    aboutButton.type = "button";
    aboutButton.className = "room-about";
    aboutButton.textContent = navAbout.textContent.trim();
    aboutButton.setAttribute("aria-pressed", "false");
    aboutButton.addEventListener("click", () => setAbout(!aboutOn));
    const exit = overlay.querySelector(".room-exit");
    if (exit) exit.after(aboutButton);
    else overlay.prepend(aboutButton);
  }

  // ---- stops in the overlay ----
  // Back (content.site.room.back): shown away from the desk. The stops as buttons, one per stop, for the keyboard
  // and screen readers: the list stays visually hidden until focus is in it (Tab), then shows in the bar.
  let stopList = null;
  const stopButtons = new Map(); // id -> button
  if (stops) {
    if (text.back) {
      backButton = document.createElement("button");
      backButton.type = "button";
      backButton.className = "room-back";
      backButton.textContent = text.back;
      backButton.hidden = true;
      backButton.addEventListener("click", () => back());
      (aboutButton || overlay.querySelector(".room-exit") || overlay.firstChild).after(backButton);
    }
    stopList = document.createElement("div");
    stopList.className = "room-stops";
    (backButton || aboutButton || overlay.querySelector(".room-exit")).after(stopList);
  }
  function addStopButtons() {
    if (!stopList) return;
    for (const st of stops.stops) {
      if (stopButtons.has(st.id) || !nameOf(st.id)) continue;
      const b = document.createElement("button");
      b.type = "button";
      b.className = "room-stop";
      b.textContent = nameOf(st.id);
      b.addEventListener("click", () => flyTo(st.id));
      stopButtons.set(st.id, b);
    }
    stopList.replaceChildren(...stops.stops.map((st) => stopButtons.get(st.id)).filter(Boolean));
  }

  // ---- picking and input ----
  // ctx.interact for Phase 5 room objects: they call interact.set(mesh, {kind, part, owner}).
  const interact = createPickMap(THREE, camera, canvas);
  interact.set(screenMesh, { kind: "screen", part: "monitor_screen" });
  // Stops: every mesh in the room can be picked (so nearer things hide farther ones); stops.classify() says
  // which stop a hit belongs to, or none (a wall, the floor). The cars register when they arrive.
  function registerRoom() {
    collectObstacles();
    for (const m of obstacles) if (m !== screenMesh) interact.set(m, { kind: "room" });
    addStopButtons();
  }
  if (stops) registerRoom();
  // A pick with the picture's pose: the camera is put where the picture is first (the free camera may have
  // moved since the last draw).
  function placeCamera(p) {
    camera.position.copy(p.pos);
    camera.quaternion.copy(p.quat);
    if (camera.fov !== p.fov) { camera.fov = p.fov; camera.updateProjectionMatrix(); }
    if (camera.view && camera.view.enabled) camera.clearViewOffset();
    camera.updateMatrixWorld();
  }
  function pickShown(x, y) {
    if (freeCam && moves.showing) placeCamera(moves.shown);
    return interact.pick(x, y);
  }
  // What a pick means here: "screen", a stop, or null.
  function stopOf(picked) {
    if (!picked || !stops) return null;
    if (picked.info.kind === "screen") return "screen";
    const st = stops.classify(picked.mesh, picked.hit.point);
    if (!st || (st.late && carsRoot && !carsRoot.visible)) return null;
    return st;
  }

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
  // The orbit is locked while a still view or a move is on screen; a hand-over gives it back at once.
  // OrbitControls only drive the placeholder room; the GLB room's camera is the free camera.
  const syncControls = () => { controls.enabled = !freeCam && !glide.active && !pinchLock && !(down && down.scrolling); };
  syncControls();
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
    // During the intro's move a press hands the room over, before OrbitControls sees it (this is the
    // capture phase), so the same drag already turns the orbit. During the hold a tap starts the move
    // (onPointerEnd) and a drag hands over (pointermove below).
    if (introRunning() && !holding()) handOver();
    if (e.pointerType === "touch") {
      touches.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (touches.size === 2) { // second finger: pinch, whatever the first one was doing
        handOver();
        pinchLock = true;
        pinchDist = touchGap();
        endGesture();
        return;
      }
      if (pinchLock) return;
    }
    if (!e.isPrimary || (e.pointerType === "mouse" && e.button !== 0)) return;
    down = { id: e.pointerId, x: e.clientX, y: e.clientY, t: performance.now(), scrolling: false, lastY: e.clientY, lx: e.clientX, ly: e.clientY };
    if (e.pointerType === "touch" && !moves.moving && isScreen(pickShown(e.clientX, e.clientY))) {
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
      if (gap > 0) {
        if (freeCam) walkBy((gap - pinchDist) * MOVES.pinchMove); // fingers apart -> forward
        else zoomBy(pinchDist / gap, true); // fingers apart -> closer
      }
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
    if (holding() && down && e.pointerId === down.id && Math.hypot(e.clientX - down.x, e.clientY - down.y) >= TAP_MAX_MOVE) {
      handOver();
      return;
    }
    // The free camera: a drag looks around from where the camera is, the scene following the pointer (it
    // starts after a few pixels, so a tap stays a tap).
    if (freeCam && down && e.pointerId === down.id && !down.scrolling && !pinchLock && moves.phase === "free") {
      if (down.looking || Math.hypot(e.clientX - down.x, e.clientY - down.y) >= 3) {
        down.looking = true;
        const k = (2 * Math.PI * MOVES.lookDrag) / Math.max(1, canvas.clientHeight);
        if (moves.look((e.clientX - down.lx) * k, (e.clientY - down.ly) * k)) needsRender = true;
      }
      down.lx = e.clientX;
      down.ly = e.clientY;
    }
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
    if (holding()) { playIntro(); return; } // the decided opening: a click pulls back into the room
    if (moves.moving) return; // nothing is picked while the camera travels
    if (!stops) { // the placeholder room: as before
      if (moves.showing) return;
      const picked = interact.pick(e.clientX, e.clientY);
      if (picked) dispatchTap(picked);
      return;
    }
    // The posts screen keeps its own behaviour from anywhere (a row opens its post with the glide); a stop
    // flies there; a wall or the floor does nothing (Back and Escape go back).
    const picked = pickShown(e.clientX, e.clientY);
    const what = stopOf(picked);
    if (what === "screen") { dispatchTap(picked); return; }
    if (what && what.id !== currentId()) flyTo(what.id);
  }
  canvas.addEventListener("pointerup", onPointerEnd);
  canvas.addEventListener("pointercancel", onPointerEnd);
  canvas.addEventListener("lostpointercapture", (e) => { if (down && e.pointerId === down.id && down.scrolling) endGesture(); });

  // Hover: raycast at most once per frame, from the last pointermove, never for touch.
  let hoverX = 0;
  let hoverY = 0;
  let hoverDirty = false;
  let hoverPointer = false;
  // Over a stop the cursor is a pointer and a small label with the stop's name follows it (a DOM element: no
  // draw call, and no material is touched, since the export merges each root's parts into shared meshes).
  const tip = document.createElement("div");
  tip.className = "room-tip";
  tip.setAttribute("aria-hidden", "true");
  tip.hidden = true;
  if (stops) document.body.append(tip);
  let tipText = "";
  function setHover(on, label) {
    if (on !== hoverPointer) { hoverPointer = on; canvas.style.cursor = on ? "pointer" : ""; }
    const show = on && !!label;
    if (show && label !== tipText) { tip.textContent = label; tipText = label; }
    if (tip.hidden === show) tip.hidden = !show;
    if (show) tip.style.transform = `translate(${hoverX + 14}px, ${hoverY + 18}px)`;
  }
  function updateHover() {
    if (!hoverDirty) return;
    hoverDirty = false;
    if (!stops) { setHover(!!interact.pick(hoverX, hoverY), ""); return; }
    if (down && down.looking) { setHover(false, ""); return; } // no label while dragging
    const what = stopOf(pickShown(hoverX, hoverY));
    if (what === "screen") setHover(true, "");
    else if (what && what.id !== currentId()) setHover(true, nameOf(what.id));
    else setHover(false, "");
  }
  canvas.addEventListener("pointerleave", () => {
    hoverDirty = false;
    setHover(false, "");
  });

  // Wheel: over the screen it scrolls the list; anywhere else it zooms. ctrl+wheel (trackpad
  // pinch) always zooms and never reaches the browser's page zoom.
  window.addEventListener("wheel", (e) => {
    if (e.target !== canvas) return;
    handOver(); // during the intro: the wheel takes the room, and moves at once
    const k = e.deltaMode === 1 ? WHEEL_LINE_PX : 1;
    if (glide.active || moves.moving) { e.preventDefault(); e.stopImmediatePropagation(); return; }
    if (!e.ctrlKey && isScreen(pickShown(e.clientX, e.clientY))) {
      const px = screenPixelHeight();
      const used = px > 0 && scrollScreen((e.deltaY * k * SCREEN_H) / px);
      // The free camera: over the posts screen the wheel is the list's, even when the list is too short to scroll.
      if (used || freeCam) {
        e.preventDefault();
        e.stopImmediatePropagation();
        return;
      }
    }
    e.preventDefault();
    e.stopImmediatePropagation();
    if (freeCam) walkBy(-e.deltaY * k * (e.ctrlKey ? MOVES.pinchWheelMove : MOVES.wheelMove)); // down/pinch in = back
    else zoomBy(Math.exp(e.deltaY * k * (e.ctrlKey ? PINCH_WHEEL_ZOOM : WHEEL_ZOOM))); // down/pinch in = farther
  }, { capture: true, passive: false });
  // Forward (negative: back) along the look, through the room's free space.
  const _walk = new THREE.Vector3();
  const _side = new THREE.Vector3();
  function walkBy(metres) {
    if (moves.phase !== "free" || !metres) return;
    if (moves.dolly(metres)) needsRender = true; // at a stop: closer to or further from it
  }

  // Keyboard: the canvas is focusable (tab stop); keys go to the screen.
  canvas.tabIndex = 0;
  canvas.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (glide.active || moves.moving || (freeCam && currentId() !== "desk")) return; // keys reach the screen at the desk
    if (screenHandle.input({ type: "key", key: e.key })) e.preventDefault();
  });
  // Keys anywhere on the page: during the intro's hold Enter or Space starts the move (the keyboard's
  // click); any other key during the intro hands the room over. Escape goes Back (a stop, the About view).
  const MODIFIER_KEYS = new Set(["Shift", "Control", "Alt", "Meta", "CapsLock"]);
  window.addEventListener("keydown", (e) => {
    if (MODIFIER_KEYS.has(e.key)) return;
    if (holding() && (e.key === "Enter" || e.key === " ") && (e.target === canvas || e.target === document.body)) {
      e.preventDefault();
      playIntro();
      return;
    }
    if (introRunning()) handOver();
    if (e.key === "Escape" && back()) { e.preventDefault(); return; }
    // Walking (free camera): WASD always, the arrows unless the posts screen has them (the canvas focused at
    // the desk). Never while a button or link has focus.
    if (!freeCam || e.ctrlKey || e.metaKey || e.altKey || !WALK_KEYS[e.code]) return;
    const el = document.activeElement;
    if (el && el !== canvas && el !== document.body) return;
    if (e.code.startsWith("Arrow") && el === canvas && currentId() === "desk") return;
    keys.add(e.code);
    e.preventDefault();
  }, { capture: true });
  window.addEventListener("keyup", (e) => { keys.delete(e.code); });
  window.addEventListener("blur", () => keys.clear());
  // code -> [forward, right]
  const WALK_KEYS = {
    KeyW: [1, 0], ArrowUp: [1, 0], KeyS: [-1, 0], ArrowDown: [-1, 0],
    KeyA: [0, -1], ArrowLeft: [0, -1], KeyD: [0, 1], ArrowRight: [0, 1],
  };
  // Every tick while walking keys are held: a step along the level forward and right.
  function stepWalk(dt) {
    if (!keys.size || moves.phase !== "free") return;
    if (moves.orbiting) { // at a stop the arrows circle (left, right) and move closer or further (up, down)
      const s = Math.min(dt, 100) / 1000;
      let turn = 0, dol = 0;
      if (keys.has("ArrowLeft")) turn -= 1;
      if (keys.has("ArrowRight")) turn += 1;
      if (keys.has("ArrowUp")) dol += 1;
      if (keys.has("ArrowDown")) dol -= 1;
      if (turn && moves.look(turn * MOVES.circleKeys * s, 0)) needsRender = true;
      if (dol && moves.dolly(dol * MOVES.walk * 0.7 * s)) needsRender = true;
      if (!(keys.has("KeyW") || keys.has("KeyA") || keys.has("KeyS") || keys.has("KeyD"))) return;
    }
    let f = 0, r = 0;
    const circling = moves.orbiting;
    for (const c of keys) { const w = WALK_KEYS[c]; if (w && !(circling && c.startsWith("Arrow"))) { f += w[0]; r += w[1]; } }
    if (!f && !r) return;
    const step = (MOVES.walk * Math.min(dt, 100)) / 1000 / Math.hypot(f, r);
    moves.forward(_walk, true);
    _side.set(-_walk.z, 0, _walk.x); // right of the level forward
    _walk.multiplyScalar(f * step).addScaledVector(_side, r * step);
    if (moves.move(_walk)) needsRender = true;
  }

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
    window.roomDebug = { info: renderer.info, THREE, scene, camera, renderer, get post() { return post; }, get bloomOn() { return bloomOn; } };

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
  let carsFade = null; // { mats, t0 } while the cars fade in
  let last = 0; // time of the previous loop tick
  let lastDrew = false; // did the previous tick draw?
  function renderFrame(t) {
    const dt = last ? t - last : 0;
    last = t;
    if (glide.active) {
      if (glide.step(dt)) needsRender = true;
    } else {
      if (!freeCam) { stepZoom(dt); controls.update(); }
      if (!moves.moving) updateHover();
      if (!warm && dt > 0) warmUp();
      else if (space && !space.ready && dt > 0 && !moves.moving && performance.now() > spaceAt) buildSpace();
      if (holding() && (holdLeft -= Math.min(dt, 100)) <= 0) playIntro(); // the hold ends by itself
      stepWalk(dt);
      if (moves.step(dt)) needsRender = true;
      if (freeCam) updateNav();
      if (carsWaiting && !moves.moving) { const add = carsWaiting; carsWaiting = null; add(); }
    }
    if (screenHandle.frame(t, dt)) { screenTexture.needsUpdate = true; needsRender = true; }
    if (carsFade) stepCarsFade(t);
    const drew = needsRender;
    if (drew) {
      if (moves.showing && !glide.active) drawShown();
      else {
        applyShift();
        if (post && bloomOn) post.render();
        else renderer.render(scene, camera);
      }
      needsRender = false;
      if (lastDrew && dt > 0) quality.frame(dt);
    }
    lastDrew = drew;
    if (updateDebug) updateDebug(t);
  }
  // The GLB room: the camera takes the pose camera-moves.js shows (the free camera, a flight, the intro).
  function drawShown() { drawPose(moves.shown); }
  // The same path as a real frame (the bloom composer when it is on): shaders differ by render target.
  function drawPose(p) {
    placeCamera(p);
    if (post && bloomOn) post.render();
    else renderer.render(scene, camera);
  }
  // Warm-up, once, on the first tick after the first frame. Three.js makes a part's shader, buffers and
  // textures the first time the part is drawn; the intro's first frame shows only the window, so without
  // this the rest of the room was made mid-move (a 65 ms frame on an M2 when the pegboard came in). Here the
  // whole room is drawn once with view culling off, and overdrawn in the same tick by the real frame, so
  // nobody sees it. About's first turn gains from it too.
  let warm = !useGlb;
  // The free camera's room space (room-space.js), built on a quiet tick after the warm-up: during the intro's
  // hold or at rest, never mid-flight. The car shelf adds itself when it arrives.
  const spaceAt = performance.now() + 300;
  function buildSpace() {
    const t0 = performance.now();
    space.build(obstacles);
    spaceTiming.ms = Math.round(performance.now() - t0);
  }
  const spaceTiming = { ms: 0 };
  const _culled = [];
  function warmUp() {
    warm = true;
    renderer.compile(scene, camera);
    scene.traverse((o) => { if (o.isMesh && o.frustumCulled) { o.frustumCulled = false; _culled.push(o); } });
    drawPose(heroPose());
    for (const o of _culled) o.frustumCulled = true;
    _culled.length = 0;
    needsRender = true;
  }
  function run() { last = 0; lastDrew = false; quality.resume(); renderer.setAnimationLoop(renderFrame); }
  function stop() { renderer.setAnimationLoop(null); quality.pause(); }
  document.addEventListener("visibilitychange", () => (document.hidden ? stop() : run()));

  // ---- the car display (deferred) ----
  // Fade: opacity 0 -> 1 with the materials briefly transparent; then opaque again (the shadow card stays blended).
  function stepCarsFade(t) {
    const k = Math.min(1, (t - carsFade.t0) / CARS.fadeMs);
    const e = k * k * (3 - 2 * k);
    for (const m of carsFade.mats) m.opacity = e;
    if (k >= 1) {
      for (const m of carsFade.mats) {
        if (m.isMeshStandardMaterial) { m.transparent = false; m.needsUpdate = true; }
      }
      carsFade = null;
    }
    needsRender = true;
  }
  const carsTiming = { roomShown: 0, requested: 0, shown: 0, skipped: "" };
  async function loadCars() {
    if (quality.lowest) { carsTiming.skipped = "lowest rung"; return; }
    carsTiming.requested = performance.now();
    const [{ GLTFLoader }, { DRACOLoader }] = await Promise.all([
      import("three/addons/loaders/GLTFLoader.js"),
      import("three/addons/loaders/DRACOLoader.js"),
    ]);
    const draco = new DRACOLoader().setDecoderPath(DRACO_DECODER);
    const [gltf, carLight] = await Promise.all([
      new GLTFLoader().setDRACOLoader(draco).loadAsync(CARS.url),
      loadCarsLight(THREE).catch((e) => { console.warn("cars light:", e); return null; }),
    ]);
    draco.dispose();
    const root = gltf.scene;
    const mats = applyCarsLight(THREE, { root, light: carLight, exposure: roomExposure ?? 1 });
    // Not while the camera travels: a shader compile or a buffer or texture upload mid-move is a visible hitch.
    // During the intro's hold the window fills the view and the shelf is out of frame: the cars go in at
    // once, without the fade, and are made ready (drawn once out of sight) while nothing moves.
    const add = () => {
      const quiet = holding();
      if (!reduce && !quiet) {
        for (const m of mats) { m.transparent = true; m.opacity = 0; }
        carsFade = { mats, t0: performance.now() };
      }
      scene.add(root);
      carsRoot = root;
      root.visible = !quality.lowest;
      if (quiet) warm = false; // the next tick draws the hero once more, out of sight (warmUp), with the cars in
      if (stops && stops.build(root).length) registerRoom(); // the car shelf's stop appears now
      if (space && space.ready) { const ms = []; root.traverseVisible((o) => { if (o.isMesh) ms.push(o); }); space.build(ms); }
      needsRender = true;
      carsTiming.shown = performance.now() + (reduce || quiet ? 0 : CARS.fadeMs);
      carsTiming.during = moves.tag || "orbit";
    };
    if (moves.moving) carsWaiting = add;
    else add();
  }
  function scheduleCars() {
    let frames = 0;
    const idle = window.requestIdleCallback || ((f) => setTimeout(f, 200));
    const wait = () => {
      if (++frames < CARS.afterFrames) { requestAnimationFrame(wait); return; }
      idle(() => loadCars().catch((e) => console.warn("cars:", e)), { timeout: CARS.idleTimeout });
    };
    requestAnimationFrame(wait);
  }
  if (window.roomDebug) {
    window.roomDebug.cars = carsTiming;
    // Moves, for measuring and frame capture: stop() the loop, then tick(t) with fixed steps.
    Object.assign(window.roomDebug, { moves, controls, setAbout, playIntro, tick: renderFrame, stop, run, stops, flyTo, back, currentId, pickShown, stopOf, poseFor, space, spaceTiming, heroPose, walkBy, keys });
  }

  renderFrame(performance.now()); // first frame, drawn before start() resolves
  carsTiming.roomShown = performance.now();
  if (!document.hidden) run();
  if (useGlb && roomExposure !== null && !params.has("nocars")) scheduleCars();
}
