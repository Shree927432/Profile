// The room's camera (?room&glb): the intro (out of the window, back and round to the AI lab), the flights
// to stops and to About, and the free camera the visitor drives everywhere else. Used by desktop.js only;
// desktop.js owns the camera object, the input and the drawing, this file owns the pose.
//
// A pose is what the camera shows: { pos: Vector3, quat: Quaternion, fov (vertical degrees), shift }.
// shift is desktop.js's lens-shift factor (always 0 in the GLB room since 2026-11-12; the placeholder's orbit
// is not driven from here).
//
// Phases:
//   "still"   a fixed pose (the intro's hold on the window)
//   "move"    an eased flight along a Catmull-Rom curve to a pose; it ends in "free" at that pose
//   "free"    the visitor's camera: look (yaw, pitch) and move (position), damped; every flight ends here
//   "orbit"   nothing from here on screen (the glide into a post draws the camera directly)
//
//   still(pose, name)  hold a pose
//   go(path)           fly from what is on screen to path.to through path.via ({ to, via, ms, lookDelay,
//                      lookLead, tag, endTag, onEnd }); arrives in free at path.to, named path.endTag (or tag)
//   free(pose, name, orbit)  the free camera, at a pose (a cut, a stop under reduced motion). With orbit
//                      ({ center, min, leave } in metres, 2026-11-12) the camera is "at" a component: look()
//                      circles the centre and dolly() changes the distance (never under min); dollying out past
//                      `leave`, or move(), leaves orbit with the same pose, and look() turns in place again.
//                      A circle step that would enter blocked space (isFree) is refused, axis by axis.
//   handOver()         the visitor took over during the intro: free at once, the move's speed runs down
//                      over STOP_TAU_MS instead of stopping dead
//   look(dYaw, dPitch) radians; pitch is held between PITCH_MIN and PITCH_MAX
//   move(delta)        metres in world space, through `constrain(from, to)` (desktop.js: the room's free space)
//   dolly(metres)      forward along the look (orbit: closer to the centre); negative is back
//   forward(out, flat) the free camera's look direction (flat: level, for walking)
//   moved              true once the visitor has looked or moved since the last arrival
//   step(dt)           every loop tick; returns true when the picture changed
//
// No allocations per tick: every vector, quaternion and matrix is made once here.

export const ORBIT = "orbit";

const STOP_TAU_MS = 280; // how fast an interrupted move runs down (exponential)
const MAX_STEP_MS = 100; // a long gap between ticks (a hidden tab) never jumps a move
const FREE_TAU_MS = 70; // the free camera's damping (time constant)
const PITCH_MIN = (-60 * Math.PI) / 180;
const PITCH_MAX = (50 * Math.PI) / 180;
const ORBIT_PITCH_MIN = (-80 * Math.PI) / 180; // circling: from nearly overhead
const ORBIT_PITCH_MAX = (35 * Math.PI) / 180; // to a little below

const clamp01 = (x) => Math.min(1, Math.max(0, x));
// Zero speed and zero acceleration at both ends: the move leaves and lands like a camera on a dolly.
// Clamped: in floating point it can come out a hair over 1 just below x = 1, and the curve's arc-length lookup
// returns NaN past its end.
const smoother = (x) => Math.min(1, x * x * x * (x * (x * 6 - 15) + 10));
const clampPitch = (p) => Math.max(PITCH_MIN, Math.min(PITCH_MAX, p));

// constrain(from, to): moves `to` to where the camera may be, coming from `from` (null: anywhere). reduce: the
// free camera follows input without damping.
export function createMoves({ THREE, constrain = null, isFree = null, reduce = false }) {
  const V = () => new THREE.Vector3();
  const pose = () => ({ pos: V(), quat: new THREE.Quaternion(), fov: 50, shift: 0 });
  const copyPose = (a, b) => { a.pos.copy(b.pos); a.quat.copy(b.quat); a.fov = b.fov; a.shift = b.shift; return a; };
  const UP = new THREE.Vector3(0, 1, 0);
  const ZERO = new THREE.Vector3();
  const _m = new THREE.Matrix4();
  const _dir = V();
  const _t = V();

  const shown = pose(); // what is on screen
  const from = pose(); // a move's start
  const to = pose(); // a move's end
  const _a = pose();
  const _b = pose();

  let phase = ORBIT;
  let tag = "";
  // The move
  let curve = null;
  let t = 0;
  let duration = 1;
  let lookDelay = 0; // fraction of the move before the look starts turning
  let lookLead = 0; // fraction of the move by which the look finishes early
  let yaw0 = 0, yaw1 = 0, pitch0 = 0, pitch1 = 0;
  let onEnd = null;
  let endTag = "";
  // The free camera: now and goal; a drift (an interrupted move's speed) running down.
  const fpos = V(), gpos = V(), drift = V();
  let fyaw = 0, fpitch = 0, gyaw = 0, gpitch = 0, dyaw = 0, dpitch = 0;
  let drifting = false;
  let moved = false;
  let dirty = false; // a pose was set from outside (still, free): the next step reports a change
  // Orbit at a component: the centre, the distance now and goal, and its limits.
  let orbit = null;
  let endOrbit = null;
  const ocenter = V();
  let fdist = 1, gdist = 1;
  const _o = V();
  const _d = V();

  // Look direction <-> yaw (about +Y, 0 = looking +Z) and pitch.
  function yawPitch(q, out) {
    _dir.set(0, 0, -1).applyQuaternion(q);
    out[0] = Math.atan2(_dir.x, _dir.z);
    out[1] = Math.asin(Math.max(-1, Math.min(1, _dir.y)));
  }
  function lookQuat(yaw, pitch, q) {
    const c = Math.cos(pitch);
    _dir.set(Math.sin(yaw) * c, Math.sin(pitch), Math.cos(yaw) * c);
    _m.lookAt(ZERO, _dir, UP); // a camera looks down its -Z: eye at 0, target along _dir
    return q.setFromRotationMatrix(_m);
  }
  const _yp = [0, 0];

  // The move's pose at its own clock t (ms): position along the curve, look by yaw and pitch.
  function poseAt(time, out) {
    const s = clamp01(time / duration);
    const up = smoother(s);
    const ul = smoother(clamp01((s - lookDelay) / Math.max(1e-6, 1 - lookDelay - lookLead)));
    curve.getPointAt(up, out.pos);
    lookQuat(yaw0 + (yaw1 - yaw0) * ul, pitch0 + (pitch1 - pitch0) * ul, out.quat);
    out.fov = from.fov + (to.fov - from.fov) * ul;
    out.shift = from.shift + (to.shift - from.shift) * ul;
    return out;
  }

  function still(p, name = "") {
    dirty = true;
    copyPose(shown, p);
    phase = "still";
    tag = name;
    onEnd = null;
  }

  function free(p, name = "", orb = null) {
    dirty = true;
    orbit = orb;
    if (orbit) {
      ocenter.copy(orbit.center);
      fdist = gdist = p.pos.distanceTo(ocenter);
    }
    copyPose(shown, p);
    yawPitch(p.quat, _yp);
    fyaw = gyaw = _yp[0];
    fpitch = gpitch = orbit ? Math.max(ORBIT_PITCH_MIN, Math.min(ORBIT_PITCH_MAX, _yp[1])) : clampPitch(_yp[1]);
    fpos.copy(p.pos);
    gpos.copy(p.pos);
    drifting = false;
    moved = false;
    phase = "free";
    tag = name;
    onEnd = null;
    lookQuat(fyaw, fpitch, shown.quat);
  }

  function go(path) {
    copyPose(from, shown);
    copyPose(to, path.to);
    curve = new THREE.CatmullRomCurve3([from.pos.clone(), ...(path.via || []), to.pos.clone()], false, "centripetal");
    curve.arcLengthDivisions = 400;
    curve.getLengths(); // measured now, not on the first tick
    yawPitch(from.quat, _yp); yaw0 = _yp[0]; pitch0 = _yp[1];
    yawPitch(to.quat, _yp); pitch1 = _yp[1];
    yaw1 = yaw0 + Math.atan2(Math.sin(_yp[0] - yaw0), Math.cos(_yp[0] - yaw0)); // the short way round
    duration = Math.max(1, path.ms);
    lookDelay = path.lookDelay || 0;
    lookLead = path.lookLead || 0;
    onEnd = path.onEnd || null;
    tag = path.tag || "";
    endTag = path.endTag ?? tag;
    endOrbit = path.orbit || null;
    t = 0;
    phase = "move";
  }

  function handOver() {
    if (phase === "still") { free(shown, "free"); moved = true; return; }
    if (phase !== "move") return;
    // The move's speed now, from two samples 8 ms apart, carried on and run down in free.
    poseAt(t, _a);
    poseAt(Math.min(duration, t + 8), _b);
    yawPitch(_a.quat, _yp);
    const ya = _yp[0], pa = _yp[1];
    yawPitch(_b.quat, _yp);
    free(_a, "free");
    moved = true;
    drift.subVectors(_b.pos, _a.pos).divideScalar(8);
    dyaw = Math.atan2(Math.sin(_yp[0] - ya), Math.cos(_yp[0] - ya)) / 8;
    dpitch = (_yp[1] - pa) / 8;
    drifting = true;
  }

  // Where the orbit puts the camera for a yaw, pitch and distance.
  function orbitPos(yaw, pitch, dist, out) {
    const c = Math.cos(pitch);
    return out.set(Math.sin(yaw) * c, Math.sin(pitch), Math.cos(yaw) * c).multiplyScalar(-dist).add(ocenter);
  }
  const ok = (yaw, pitch, dist) => !isFree || !isFree(fpos) || isFree(orbitPos(yaw, pitch, dist, _o));
  function look(dy, dp) {
    if (phase !== "free") return false;
    if (orbit) { // circle: the scene follows the pointer, so the camera goes the other way round
      const y = gyaw - dy;
      const p = Math.max(ORBIT_PITCH_MIN, Math.min(ORBIT_PITCH_MAX, gpitch - dp));
      if (ok(y, p, gdist)) { gyaw = y; gpitch = p; }
      else if (ok(y, gpitch, gdist)) gyaw = y; // slide along the limit
      else if (ok(gyaw, p, gdist)) gpitch = p;
      return true;
    }
    gyaw += dy;
    gpitch = clampPitch(gpitch + dp);
    moved = true;
    return true;
  }
  function leaveOrbit() {
    if (!orbit) return;
    orbit = null;
    gpos.copy(fpos); // the same picture; from here on a drag looks around in place
    gyaw = fyaw;
    gpitch = clampPitch(fpitch);
    moved = true;
  }
  function dolly(m) {
    if (phase !== "free" || !m) return false;
    if (orbit) {
      const d = Math.max(orbit.min, gdist - m);
      // Out past the leave distance, or out into something (a wall behind): leave orbit and keep pulling back
      // as the free camera, which slides along what is in the way. In: stop at the limit.
      if (d > orbit.leave || (m < 0 && !ok(gyaw, gpitch, d))) leaveOrbit();
      else { if (ok(gyaw, gpitch, d)) gdist = d; return true; }
    }
    forward(_d).multiplyScalar(m);
    return move(_d);
  }
  function move(delta) {
    if (phase !== "free") return false;
    if (orbit) leaveOrbit();
    _t.copy(gpos).add(delta);
    if (constrain) constrain(gpos, _t);
    gpos.copy(_t);
    moved = true;
    return true;
  }
  function forward(out, flat = false) {
    const c = flat ? 1 : Math.cos(gpitch);
    return out.set(Math.sin(gyaw) * c, flat ? 0 : Math.sin(gpitch), Math.cos(gyaw) * c);
  }

  function reset() { phase = ORBIT; tag = ""; onEnd = null; }

  function step(dt) {
    const was = dirty;
    dirty = false;
    if (phase === ORBIT || phase === "still") return was;
    dt = dt > 0 ? Math.min(dt, MAX_STEP_MS) : 0; // never backwards, never NaN
    if (phase === "move") {
      t = Math.min(duration, t + dt);
      poseAt(t, shown);
      if (t >= duration) {
        const done = onEnd;
        free(to, endTag, endOrbit);
        if (done) done();
      }
      return true;
    }
    // free
    if (drifting) {
      _t.copy(gpos).addScaledVector(drift, dt);
      if (constrain) constrain(gpos, _t);
      gpos.copy(_t);
      gyaw += dyaw * dt;
      gpitch = clampPitch(gpitch + dpitch * dt);
      const k = Math.exp(-dt / STOP_TAU_MS);
      drift.multiplyScalar(k);
      dyaw *= k;
      dpitch *= k;
      if (drift.lengthSq() < 1e-10 && Math.abs(dyaw) < 1e-6 && Math.abs(dpitch) < 1e-6) drifting = false;
    }
    if (orbit) {
      if (fyaw === gyaw && fpitch === gpitch && fdist === gdist) return was;
      const k = reduce ? 1 : 1 - Math.exp(-dt / FREE_TAU_MS);
      fyaw += (gyaw - fyaw) * k;
      fpitch += (gpitch - fpitch) * k;
      fdist += (gdist - fdist) * k;
      if (Math.abs(gyaw - fyaw) < 1e-5 && Math.abs(gpitch - fpitch) < 1e-5 && Math.abs(gdist - fdist) < 1e-5) {
        fyaw = gyaw; fpitch = gpitch; fdist = gdist;
      }
      orbitPos(fyaw, fpitch, fdist, fpos);
      orbitPos(gyaw, gpitch, gdist, gpos);
      shown.pos.copy(fpos);
      lookQuat(fyaw, fpitch, shown.quat);
      return true;
    }
    if (fpos.equals(gpos) && fyaw === gyaw && fpitch === gpitch) return was;
    const k = reduce ? 1 : 1 - Math.exp(-dt / FREE_TAU_MS);
    fpos.lerp(gpos, k);
    fyaw += (gyaw - fyaw) * k;
    fpitch += (gpitch - fpitch) * k;
    if (fpos.distanceToSquared(gpos) < 1e-8 && Math.abs(gyaw - fyaw) < 1e-5 && Math.abs(gpitch - fpitch) < 1e-5) {
      fpos.copy(gpos); fyaw = gyaw; fpitch = gpitch;
    }
    shown.pos.copy(fpos);
    lookQuat(fyaw, fpitch, shown.quat);
    return true;
  }

  // A fixed pose from a position, a point to look at, a fov and a shift.
  function makePose(pos, target, fov, shift = 0, out = pose()) {
    out.pos.copy(pos);
    _m.lookAt(pos, target, UP);
    out.quat.setFromRotationMatrix(_m);
    out.fov = fov;
    out.shift = shift;
    return out;
  }

  return {
    still, go, free, handOver, look, move, dolly, leaveOrbit, forward, reset, step, makePose, shown,
    get orbiting() { return phase === "free" && !!orbit; },
    get phase() { return phase; },
    get tag() { return tag; },
    get moved() { return moved; },
    get showing() { return phase !== ORBIT; },
    get moving() { return phase === "move"; },
    get progress() { return phase === "move" ? t / duration : 1; },
    get curve() { return curve; },
    // Where the free camera is heading (its goal), for picks and checks.
    get goal() { return gpos; },
  };
}
