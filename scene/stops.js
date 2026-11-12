// Stops (2026-11-11): click a component and the camera flies to a close-up of it (the owner chose "Click to fly
// there"); from there the visitor is in the free camera (camera-moves.js, 2026-11-12). Used by desktop.js only, GLB room only. This file knows the table of stops, their boxes, which stop a
// click belongs to, where the camera stands for each, and a safe waypoint for a flight. desktop.js does the
// flying (camera-moves.js), the input and the overlay. Names shown to people come from content.site.room.stops.
//
// A stop:
//   id, parent    parent "hero" (Back returns to the desk) or "about" (Back returns to the music side's overview)
//   nodes         GLB names; every mesh under them belongs to the stop (a click on it picks the stop)
//   add           extra boxes [[min], [max]] (GLB metres) for parts the export merged into a shared <root>_static
//                 mesh (the DJ stand, the guitar rack, the desk's gear); a click on a shared mesh picks the
//                 smallest stop box that holds the hit point
//   frame         optional box [[min], [max]] the close-up frames, when it should be tighter than the stop's own
//                 (the mic and camera, not their long arms; the piano, not its bench)
//   dir           from the framed centre towards the camera (any length); up a little looks down on it
//   fit           room around the box in the frame (1 = the box just fits)
// The camera's place is computed: the box is fitted to the view along dir, then pulled in so the camera stays
// MARGIN inside the room. Portrait uses the same table with its own field of view.

const MARGIN = 0.25; // metres the camera keeps from the walls, floor and ceiling (inside room-space.js's free box)
const PAD = 0.03; // metres a stop's box grows by when it classifies a hit
const MIN_DIST = 0.45; // never nearer than this to the framed centre
const PORTRAIT_WIDTH = 0.6; // share of a stop's width a portrait close-up must show

export const STOPS = [
  // The AI lab (Back: the desk)
  { id: "pc", parent: "hero", nodes: ["rig_case", "rig_case_glass", "rig_gpu_root", "rig_fans", "batch_rig_fans", "rig_glow_strips"],
    dir: [0.35, 0.45, 1], fit: 1.25 },
  { id: "dashboard", parent: "hero", nodes: ["rig_display", "rig_screen"], dir: [1, 0.18, 0.05], fit: 1.15 },
  { id: "gear", parent: "hero", nodes: ["keyboard", "mouse", "apollo", "deck", "batch_kb_keys"],
    add: [[[-2.0, 0.76, -1.32], [-1.45, 0.9, -0.74]]], dir: [0.9, 1.1, 0.12], fit: 1.15 },
  { id: "mic", parent: "hero", nodes: ["obj_mic", "set_camera"], frame: [[-1.76, 0.86, -0.68], [-1.42, 1.34, -0.3]],
    dir: [0.75, 0.85, 0.3], fit: 1.15 },
  { id: "pegboard", parent: "hero", nodes: ["pegboard_root", "neon_root", "nanoleaf_root", "headphones_root"],
    add: [[[-1.75, 1.1, -2.11], [-0.15, 2.22, -1.98]]], dir: [0.1, 0.05, 1], fit: 1.1 },
  { id: "cars", parent: "hero", nodes: ["set_cars"], late: true, dir: [0.15, -0.12, 1], fit: 1.0 },
  { id: "frames", parent: "hero", nodes: ["obj_frames", "shelf_root"], add: [[[-2.2, 1.9, -1.62], [-1.95, 2.4, -0.38]]],
    dir: [1, -0.1, 0.12], fit: 1.1 },
  { id: "laptop", parent: "hero", nodes: ["set_laptop"], dir: [-0.39, 0.16, 0.92], fit: 0.85 }, // straight at the screen (its normal; the owner: the front view, not the side)
  { id: "window", parent: "hero", nodes: ["obj_window"], view: "intro" }, // its stop is the intro's view
  { id: "plant", parent: "hero", nodes: ["obj_plant"], dir: [-0.3, 0.3, 1], fit: 1.05 },
  { id: "chair", parent: "hero", nodes: ["set_chair"], dir: [1, 0.5, 0.75], fit: 1.0 },
  // The music side (Back: its overview, the About view)
  { id: "piano", parent: "about", nodes: ["obj_piano"], frame: [[1.55, 0.0, -0.95], [2.15, 1.3, 0.45]],
    dir: [-1, 0.28, 0.05], fit: 1.0 },
  { id: "guitars", parent: "about", nodes: ["guitar_01", "guitar_02", "guitar_03"], add: [[[2.0, 1.4, -0.98], [2.2, 2.55, 0.48]]],
    dir: [-1, -0.05, 0], fit: 1.1 },
  { id: "rack", parent: "about", nodes: ["guitar_04", "guitar_05", "guitar_06"], add: [[[1.3, 0, -2.1], [2.0, 1.15, -1.4]]],
    frame: [[1.38, 0.0, -2.1], [1.95, 1.15, -1.42]], dir: [-0.3, 1.0, 1.0], fit: 1.0 }, // from over the piano's end: the curtain and the piano close the corner from the room
  { id: "decks", parent: "about", nodes: ["dj_stand_root", "lightstick_root"], add: [[[1.72, 0, 0.88], [2.2, 1.2, 1.56]]],
    frame: [[1.75, 0.85, 0.9], [2.2, 1.2, 1.56]], dir: [-1, 0.75, 0.12], fit: 1.15 },
];

// root: the room's scene graph; bounds: the room's inside (Box3). Returns the live stop list and helpers.
export function createStops({ THREE, root, bounds }) {
  const inner = bounds.clone().expandByScalar(-MARGIN);
  const stops = [];
  const byId = new Map();
  const owner = new Map(); // mesh -> stop
  const _v = new THREE.Vector3();
  const _b = new THREE.Box3();

  function meshBox(o, into) {
    o.updateWorldMatrix(true, true);
    o.traverseVisible((m) => {
      if (!m.isMesh) return;
      if (!m.geometry.boundingBox) m.geometry.computeBoundingBox();
      into.union(_b.copy(m.geometry.boundingBox).applyMatrix4(m.matrixWorld));
    });
    return into;
  }

  // Builds (or rebuilds, for a late root) every stop whose nodes are in the scene now.
  function build(scope) {
    const made = [];
    for (const def of STOPS) {
      if (byId.has(def.id)) continue;
      const nodes = def.nodes.map((n) => scope.getObjectByName(n)).filter(Boolean);
      if (!nodes.length) continue;
      const box = new THREE.Box3();
      for (const n of nodes) meshBox(n, box);
      for (const [a, b] of def.add || []) box.union(new THREE.Box3(new THREE.Vector3(...a), new THREE.Vector3(...b)));
      if (box.isEmpty()) continue;
      const view = def.frame ? new THREE.Box3(new THREE.Vector3(...def.frame[0]), new THREE.Vector3(...def.frame[1])) : box;
      const stop = { ...def, box: view, hitBox: box.clone().expandByScalar(PAD), center: view.getCenter(new THREE.Vector3()), meshes: [] };
      for (const n of nodes) n.traverseVisible((m) => { if (m.isMesh) { owner.set(m, stop); stop.meshes.push(m); } });
      box.getSize(_v);
      stop.volume = _v.x * _v.y * _v.z;
      stops.push(stop);
      byId.set(stop.id, stop);
      made.push(stop);
    }
    stops.sort((a, b) => STOPS.findIndex((s) => s.id === a.id) - STOPS.findIndex((s) => s.id === b.id));
    return made;
  }

  // Which stop a raycast hit belongs to: the mesh's own stop, else the smallest stop box holding the point.
  function classify(mesh, point) {
    const own = owner.get(mesh);
    if (own) return own;
    let best = null;
    for (const s of stops) {
      if (s.hitBox.containsPoint(point) && (!best || s.volume < best.volume)) best = s;
    }
    return best;
  }

  // The camera's place for a stop: fit the box along dir for this aspect and vertical fov, then keep inside.
  const _dir = new THREE.Vector3();
  const _right = new THREE.Vector3();
  const _up = new THREE.Vector3();
  const _c = new THREE.Vector3();
  const UP = new THREE.Vector3(0, 1, 0);
  function place(stop, aspect, fov, outPos) {
    _dir.set(...stop.dir).normalize();
    _right.crossVectors(UP, _dir).normalize(); // camera's right (it looks along -_dir)
    _up.crossVectors(_dir, _right).normalize();
    let w = 0, h = 0, front = 0;
    const { min, max } = stop.box;
    for (let i = 0; i < 8; i++) {
      _c.set(i & 1 ? max.x : min.x, i & 2 ? max.y : min.y, i & 4 ? max.z : min.z).sub(stop.center);
      w = Math.max(w, Math.abs(_c.dot(_right)));
      h = Math.max(h, Math.abs(_c.dot(_up)));
      front = Math.max(front, _c.dot(_dir));
    }
    const tanV = Math.tan((fov * Math.PI) / 360);
    const tanH = tanV * aspect;
    // Portrait: fitting a wide stop's whole width would push the camera to the far wall; fit its height and most
    // of its width, and let the look-around show the sides.
    const wFit = aspect < 1 ? PORTRAIT_WIDTH : 1;
    let d = Math.max(MIN_DIST, Math.max((w * wFit) / tanH, h / tanV) * (stop.fit || 1.2) + front);
    // Keep the camera inside the room: the farthest it can stand along dir.
    let tmax = Infinity;
    for (const ax of ["x", "y", "z"]) {
      const v = _dir[ax];
      if (Math.abs(v) < 1e-6) continue;
      const lim = v > 0 ? inner.max[ax] : inner.min[ax];
      tmax = Math.min(tmax, (lim - stop.center[ax]) / v);
    }
    d = Math.max(Math.min(d, tmax), Math.min(MIN_DIST, tmax));
    outPos.copy(stop.center).addScaledVector(_dir, d);
    return { dist: d, front };
  }

  // A waypoint when the straight line from a to b passes through something: lifted over the middle, or through
  // the room's open middle. Five rays (centre and four 12 cm off it) per segment, once per flight.
  const rc = new THREE.Raycaster();
  const _a = new THREE.Vector3();
  const _o = new THREE.Vector3();
  const OFF = [[0, 0], [0.12, 0], [-0.12, 0], [0, 0.12], [0, -0.12]];
  function blocked(a, b, obstacles) {
    _a.subVectors(b, a);
    const len = _a.length();
    if (len < 1e-3) return false;
    _a.divideScalar(len);
    _right.crossVectors(UP, _a);
    if (_right.lengthSq() < 1e-6) _right.set(1, 0, 0);
    _right.normalize();
    _up.crossVectors(_a, _right).normalize();
    rc.far = len;
    for (const [x, y] of OFF) {
      _o.copy(a).addScaledVector(_right, x).addScaledVector(_up, y);
      rc.set(_o, _a);
      if (rc.intersectObjects(obstacles, false).length) return true;
    }
    return false;
  }
  const OPEN_MIDDLE = new THREE.Vector3(0.25, 1.85, 0.35); // over the rug, under the pendant's height, clear of all
  function via(a, b, obstacles) {
    if (!blocked(a, b, obstacles)) return [];
    const top = inner.max.y - 0.25;
    const tries = [];
    for (const lift of [0.5, 1.0]) {
      const p = new THREE.Vector3().addVectors(a, b).multiplyScalar(0.5);
      p.y = Math.min(top, Math.max(a.y, b.y) + lift);
      tries.push(p);
    }
    tries.push(OPEN_MIDDLE.clone());
    for (const p of tries) if (!blocked(a, p, obstacles) && !blocked(p, b, obstacles)) return [p];
    return [tries[1]]; // nothing is clear: go high
  }

  build(root);
  return { stops, byId, build, classify, place, via, blocked };
}
