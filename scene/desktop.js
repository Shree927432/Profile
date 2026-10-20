// The room page: renderer, camera, orbit, bloom, the posts screen on the monitor.
// Called by boot.js (see its header for what start() receives).
//
// What lives where, top to bottom:
//   constants          camera, orbit, bloom numbers in one place
//   start()            wires everything; resolves after the first frame is drawn
//     renderer / composer    setPixelRatio() is the one place pixel ratio changes
//     scene                  lights + buildPlaceholderRoom() (Phase 4: GLB loader instead)
//     camera + controls      frame() fits the monitor to the aspect on every resize
//     screen                 monitor-posts.js on an offscreen canvas -> CanvasTexture
//     loop                   one setAnimationLoop; stops while the tab is hidden
//
// Next steps plug in at the TODO markers: pick map + raycaster, wheel/keys to the screen,
// quality ladder + ?debug.
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
const SCREEN_W = 640; // logical size of the screen canvas; backing store is 2x
const SCREEN_H = 400;

export async function start({ canvas, content, overlay, params, reduce }) {
  const text = content.site.room;

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

  let pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  // The one place that changes resolution. TODO(quality ladder): call this with other ratios.
  function setPixelRatio(pr) {
    pixelRatio = pr;
    renderer.setPixelRatio(pr);
    composer.setPixelRatio(pr);
  }

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

  // The handle for the next step: screenHandle.input({type:"key"|"click"|"scroll"|"open", ...}).
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
  let needsRender = true;

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

  setPixelRatio(pixelRatio);
  resize();
  window.addEventListener("resize", resize);
  window.addEventListener("orientationchange", resize);
  controls.addEventListener("change", () => { needsRender = true; });

  // ---- canvas accessibility ----
  canvas.removeAttribute("aria-hidden");
  canvas.setAttribute("aria-label", text.canvasLabel);

  // TODO(pick map): one raycaster, a Map of mesh -> owner, tap vs drag, UV -> screen canvas click.
  // TODO(wheel/keys): wheel over the screen -> screenHandle.input scroll; keys -> screenHandle.input.
  // TODO(quality ladder + ?debug): fps meter in overlay, full / auto / smooth via setPixelRatio.

  // ---- loop ----
  let last = 0;
  function renderFrame(t) {
    const dt = last ? t - last : 0;
    last = t;
    controls.update();
    if (screenHandle.frame(t, dt)) { screenTexture.needsUpdate = true; needsRender = true; }
    // Reduced motion: draw only when something changed (orbit, resize, screen).
    if (!reduce || needsRender) {
      composer.render();
      needsRender = false;
    }
  }
  function run() { last = 0; renderer.setAnimationLoop(renderFrame); }
  function stop() { renderer.setAnimationLoop(null); }
  document.addEventListener("visibilitychange", () => (document.hidden ? stop() : run()));

  renderFrame(performance.now()); // first frame, drawn before start() resolves
  if (!document.hidden) run();
}
