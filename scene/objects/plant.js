// Room object: the young monstera on the sill. A click waters it: a small white can floats in, tips and pours, the
// soil darkens and the leaves sway. On a return visit (one a day) the watering also unfurls a new leaf.
//
// Meshes (scene/objects/MESHES.md, obj_plant): plant_pot, plant_soil (click targets; the soil darkens when wet),
// plant_leaf_01 .. plant_leaf_NN (click targets, in growth order, origin where the leaf meets the stem: grow = scale
// from 0 there, sway = a small rotation there). The code counts the leaves.
// Content: content.site.room.plant = { tip, tipDone, hint, grew, watered, full } ({n} and {total} are filled in).
// Rules (owner, 2026-11-15): a first visit shows FIRST leaves ("14 leaves"); "A small watering can"; the new leaf
// comes "When they water it", one a day, the first visit included; visits are remembered with ctx.store (on the
// visitor's device only). With reduced motion there is no can and no sway: the soil darkens and the leaf is there.
// The can and its stream are built here from simple shapes (two draw calls, in the scene only while pouring, never
// click targets: the host may list them if a late asset arrives mid-pour, so they are taken off its map after). The
// note above the plant is HTML in ctx.overlay, styled by .room-plant-note in src/styles/global.css.

const FIRST = 14; // leaves on a first visit
const KEY = "plant"; // ctx.store: { n: leaves showing, grew: the day the last leaf came, wet: the day last watered }
const NEAR = 1.8; // metres: this close, looking at the plant and still, the hint shows (the stop is about 0.9 m away)
const FAR = 2.4; // farther than this, the note goes
const LOOK = 0.9; // cos of the angle between the view and the plant (the laptop and the window are near it too)
const WET = 0.5; // the soil's colour times this when wet
const HIDDEN = 1e-4; // a leaf that has not grown yet: this scale and not drawn
const T_IN = 450, T_TIP = 300, T_POUR = 1200, T_UNTIP = 250, T_OUT = 400; // ms: the can's visit
const T_GROW = 1400; // ms: a new leaf unfurls
const T_SWAY = 3200; // ms: the leaves settle
const SWAY = 0.045; // radians at the start of the sway
const TILT = 0.7; // radians the can tips
const NOTE_MS = 5200; // the note stays this long
// the can, in its own frame (metres): +X towards the pot, +Y up
const SPOUT_A = [0.027, -0.02, 0], SPOUT_B = [0.133, 0.055, 0]; // a long spout, 35 degrees up
const REACH = 0.2; // metres from the pot's axis to the can's while pouring (the rose then over the soil)

export function createPlant(THREE, ctx) {
  const pot = ctx.root.getObjectByName("plant_pot");
  const soil = ctx.root.getObjectByName("plant_soil");
  const leaves = [];
  for (let i = 1; ; i++) {
    const o = ctx.root.getObjectByName("plant_leaf_" + String(i).padStart(2, "0"));
    if (!o) break;
    leaves.push(o);
  }
  if (!pot || !soil || !soil.isMesh || !leaves.length) return null;
  const text = (ctx.content && ctx.content.site && ctx.content.site.room && ctx.content.site.room.plant) || {};
  const total = leaves.length;

  // ---- what the visitor's device remembers ----
  const today = (() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; })();
  const saved = (ctx.store && ctx.store.get(KEY)) || {};
  const state = {
    n: Math.min(total, Math.max(1, Number.isInteger(saved.n) ? saved.n : Math.min(FIRST, total))),
    grew: typeof saved.grew === "string" ? saved.grew : "",
    wet: typeof saved.wet === "string" ? saved.wet : "",
  };
  const save = () => { if (ctx.store) ctx.store.set(KEY, state); };

  // ---- the plant as it stands ----
  ctx.root.updateWorldMatrix(true, true);
  const up = new THREE.Vector3(0, 1, 0);
  const box = new THREE.Box3().setFromObject(pot);
  const potCentre = box.getCenter(new THREE.Vector3());
  const soilY = new THREE.Box3().setFromObject(soil).max.y;
  const plantBox = box.clone();
  const parts = [pot, soil];
  const L = leaves.map((mesh, i) => {
    const b = new THREE.Box3().setFromObject(mesh);
    plantBox.union(b);
    // the sway turns the leaf at its origin, about the level line across the way it reaches out
    const out = b.getCenter(new THREE.Vector3()).sub(mesh.getWorldPosition(new THREE.Vector3())).setY(0);
    const axis = out.lengthSq() > 1e-8 ? new THREE.Vector3().crossVectors(up, out.normalize()) : new THREE.Vector3(1, 0, 0);
    if (mesh.parent) axis.transformDirection(new THREE.Matrix4().copy(mesh.parent.matrixWorld).invert());
    const leaf = { mesh, axis, q: mesh.quaternion.clone(), s: mesh.scale.clone(), phase: i * 2.4, grow: 1 };
    if (i >= state.n) { mesh.visible = false; mesh.scale.setScalar(HIDDEN); leaf.grow = 0; }
    if (mesh.isMesh) parts.push(mesh);
    return leaf;
  });
  const centre = plantBox.getCenter(new THREE.Vector3());
  const top = new THREE.Vector3(centre.x, plantBox.max.y, centre.z);

  // the soil: its own colour, darker when wet (the material is the soil's alone in the room)
  const soilMat = soil.material;
  const soilDry = soilMat.color ? soilMat.color.clone() : null;
  let wet = state.wet === today ? 1 : 0;
  const paintSoil = () => { if (soilDry) soilMat.color.copy(soilDry).multiplyScalar(1 - (1 - WET) * wet); };
  paintSoil();

  // ---- the can and its stream ----
  const _q = new THREE.Quaternion(), _m = new THREE.Matrix4(), _v = new THREE.Vector3();
  function merged(list) { // [geometry, matrix] pairs as one geometry (position and normal)
    const pos = [], nor = [];
    for (const [g0, m] of list) {
      const g = g0.toNonIndexed().applyMatrix4(m);
      pos.push(...g.attributes.position.array);
      nor.push(...g.attributes.normal.array);
      g0.dispose();
      g.dispose();
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("normal", new THREE.Float32BufferAttribute(nor, 3));
    return g;
  }
  const a = new THREE.Vector3(...SPOUT_A), b = new THREE.Vector3(...SPOUT_B);
  const along = b.clone().sub(a);
  const spoutLen = along.length();
  along.normalize();
  const aim = new THREE.Matrix4().makeRotationFromQuaternion(_q.setFromUnitVectors(up, along));
  const at = (p) => new THREE.Matrix4().makeTranslation(p.x, p.y, p.z).multiply(aim);
  const canGeo = merged([
    [new THREE.CylinderGeometry(0.028, 0.032, 0.072, 20), new THREE.Matrix4()],
    [new THREE.CylinderGeometry(0.004, 0.0065, spoutLen, 10), at(a.clone().add(b).multiplyScalar(0.5))],
    [new THREE.CylinderGeometry(0.012, 0.005, 0.012, 12), at(b.clone().addScaledVector(along, 0.006))],
    [new THREE.TorusGeometry(0.024, 0.0038, 8, 14, Math.PI), new THREE.Matrix4().makeTranslation(-0.027, 0, 0).multiply(_m.makeRotationZ(Math.PI / 2))],
  ]);
  const roseTip = b.clone().addScaledVector(along, 0.012);
  // white, with a little light of its own so it reads as white at dusk
  const canMat = new THREE.MeshStandardMaterial({ color: 0xf3f1ec, emissive: 0xf3f1ec, emissiveIntensity: 0.18, roughness: 0.5, metalness: 0, transparent: true, opacity: 0 });
  const can = new THREE.Mesh(canGeo, canMat);
  can.name = "plant_can";
  const streamGeo = new THREE.CylinderGeometry(0.004, 0.011, 1, 10, 1, true).translate(0, -0.5, 0); // hangs from its top
  const streamMat = new THREE.MeshBasicMaterial({ color: 0xcfe6ff, transparent: true, opacity: 0.5, depthWrite: false, side: THREE.DoubleSide });
  const stream = new THREE.Mesh(streamGeo, streamMat);
  stream.name = "plant_stream";
  stream.visible = false;
  // where the can pours from (set at each watering from the camera): in front of the pot and to the right as seen, below
  // the leaves, its spout across the view so it reads as a can; it comes and goes up and away
  const toPot = new THREE.Vector3(), pourAt = new THREE.Vector3(), restAt = new THREE.Vector3();
  const rimY = box.max.y;
  let yaw = 0;
  function aimCan() {
    const cam = ctx.view();
    const dc = cam ? _v.copy(cam.position).sub(potCentre).setY(0) : _v.set(0, 0, 1);
    if (dc.lengthSq() < 1e-6) dc.set(0, 0, 1);
    dc.normalize();
    toPot.set(-dc.z, 0, dc.x).multiplyScalar(-0.6).addScaledVector(dc, 0.8).normalize().negate(); // (right 0.6, front 0.8 as seen) to the pot
    pourAt.copy(potCentre).addScaledVector(toPot, -REACH).setY(rimY + 0.072);
    restAt.copy(pourAt).addScaledVector(toPot, -0.1).add(_v.set(0, 0.1, 0));
    yaw = Math.atan2(-toPot.z, toPot.x);
  }
  const _tip = new THREE.Vector3();
  function poseCan(k, tilt) { // k: 0 away .. 1 at the pot
    const e = k * k * (3 - 2 * k);
    can.position.lerpVectors(restAt, pourAt, e);
    can.rotation.set(0, yaw, -tilt, "YXZ");
    canMat.opacity = Math.min(1, k * 1.6);
    can.updateMatrixWorld();
  }

  // ---- the note above the plant ----
  const note = document.createElement("p");
  note.className = "room-plant-note";
  note.setAttribute("aria-hidden", "true"); // ctx.live says the same line
  note.hidden = true;
  ctx.overlay.append(note);
  let noteTimer = 0, noteShown = false;
  const fill = (s) => String(s || "").replace("{n}", state.n).replace("{total}", total);
  function showNote(s, ms) {
    clearTimeout(noteTimer);
    if (!s) return;
    note.textContent = s;
    note.hidden = false;
    noteShown = true;
    placeNote();
    requestAnimationFrame(() => note.classList.add("is-open"));
    if (ms) noteTimer = setTimeout(hideNote, ms);
  }
  function hideNote() {
    clearTimeout(noteTimer);
    if (!noteShown) return;
    noteShown = false;
    note.classList.remove("is-open");
    noteTimer = setTimeout(() => { if (!noteShown) note.hidden = true; }, 250);
  }
  const _p = new THREE.Vector3();
  function placeNote() {
    const cam = ctx.view();
    if (!cam || !noteShown) return;
    _p.copy(top).project(cam);
    const w = note.offsetWidth || 260, h = note.offsetHeight || 40;
    const x = (_p.x + 1) / 2 * window.innerWidth, y = (1 - _p.y) / 2 * window.innerHeight;
    note.style.left = Math.round(Math.min(Math.max(12, x - w / 2), window.innerWidth - w - 12)) + "px";
    note.style.top = Math.round(Math.min(Math.max(12, y - h - 14), window.innerHeight - h - 12)) + "px";
  }

  // ---- watering ----
  let seq = -1; // ms into the can's visit, or -1
  let sway = -1; // ms into the sway, or -1
  let growing = null; // the leaf unfurling: { leaf, t }
  let result = ""; // the line to show once the water is in
  let hinted = false; // the hint was shown on this stay at the plant
  let lastDist = -1, still = 0;

  function water() {
    if (seq >= 0) return;
    hideNote();
    const grows = state.n < total && state.grew !== today;
    const leaf = grows ? L[state.n] : null;
    if (grows) { state.n += 1; state.grew = today; }
    state.wet = today;
    save();
    result = fill(grows ? (state.n === total ? text.full : text.grew) : (state.n === total ? text.full : text.watered));
    if (ctx.reduce) { // no can, no sway: the soil is wet and the leaf is there
      wet = 1;
      paintSoil();
      if (leaf) { leaf.grow = 1; leaf.mesh.visible = true; leaf.mesh.scale.copy(leaf.s); }
      done();
      return;
    }
    growing = leaf ? { leaf, t: -1 } : null;
    seq = 0;
    aimCan();
    poseCan(0, 0);
    ctx.scene.add(can, stream);
  }
  function done() {
    if (!result) return;
    showNote(result, NOTE_MS);
    ctx.live(result);
  }
  function stepCan(dt) {
    const before = seq;
    seq += dt;
    const t1 = T_IN, t2 = t1 + T_TIP, t3 = t2 + T_POUR, t4 = t3 + T_UNTIP, t5 = t4 + T_OUT;
    const k = seq < t1 ? seq / t1 : seq < t4 ? 1 : Math.max(0, 1 - (seq - t4) / T_OUT);
    const tilt = seq < t1 ? 0 : seq < t2 ? (seq - t1) / T_TIP : seq < t3 ? 1 : seq < t4 ? 1 - (seq - t3) / T_UNTIP : 0;
    poseCan(k, TILT * tilt * tilt * (3 - 2 * tilt));
    // the stream: out of the rose, down to the soil; its head falls first, its tail last
    const pouring = seq >= t2 - 80 && seq < t3 + 120;
    stream.visible = pouring;
    if (pouring) {
      _tip.copy(roseTip).applyMatrix4(can.matrixWorld);
      const full = Math.max(0.01, _tip.y - soilY);
      const head = Math.min(1, (seq - (t2 - 80)) / 120), tail = Math.max(0, (seq - t3) / 120);
      stream.position.set(_tip.x, _tip.y - full * tail, _tip.z);
      stream.scale.set(1, Math.max(0.001, full * (head - tail)), 1);
      wet = Math.max(wet, Math.min(1, (seq - t2) / (T_POUR * 0.7)));
      paintSoil();
    }
    if (before < t2 && seq >= t2) sway = 0; // the water lands
    if (before < t3 && seq >= t3) { // the water is in
      wet = 1;
      paintSoil();
      if (growing) { growing.t = 0; growing.leaf.mesh.visible = true; }
      done();
    }
    if (seq >= t5) { seq = -1; ctx.scene.remove(can, stream); stream.visible = false; ctx.interact.delete(can); ctx.interact.delete(stream); }
  }
  function stepLeaves(dt) {
    if (growing && growing.t >= 0) {
      growing.t += dt;
      const k = Math.min(1, growing.t / T_GROW);
      const leaf = growing.leaf;
      leaf.grow = 1 - (1 - k) * (1 - k) * (1 - k); // fast out of the stem, slow to full size
      leaf.mesh.scale.copy(leaf.s).multiplyScalar(Math.max(HIDDEN, leaf.grow));
      if (k === 1) growing = null;
    }
    if (sway >= 0) {
      sway += dt;
      const over = sway >= T_SWAY;
      const amp = over ? 0 : SWAY * Math.exp(-sway / 900);
      for (const leaf of L) {
        if (!leaf.mesh.visible) continue;
        if (over) leaf.mesh.quaternion.copy(leaf.q);
        else leaf.mesh.quaternion.copy(leaf.q).premultiply(_q.setFromAxisAngle(leaf.axis, amp * Math.sin(sway * 0.0088 + leaf.phase)));
      }
      if (over) sway = -1;
    }
  }

  const _dir = new THREE.Vector3(), _to = new THREE.Vector3();
  function looking() { // near, and the plant in view: 0 no, 1 within FAR, 2 within NEAR
    const cam = ctx.view();
    if (!cam) return 0;
    const d = cam.position.distanceTo(centre);
    cam.getWorldDirection(_dir);
    if (d > FAR || _dir.dot(_to.subVectors(centre, cam.position).normalize()) < LOOK) return 0;
    return d < NEAR ? 2 : 1;
  }

  const api = {
    frame(dt) {
      if (seq >= 0) stepCan(dt);
      stepLeaves(dt);
      // the hint: once per stay at the plant, when it has not been watered today
      const cam = ctx.view();
      if (cam) {
        const d = cam.position.distanceTo(centre);
        still = Math.abs(d - lastDist) < 0.0005 ? still + 1 : 0;
        lastDist = d;
        const at = looking();
        if (!at) { hinted = false; if (noteShown && seq < 0) hideNote(); }
        else if (at === 2 && !hinted && still >= 3 && seq < 0 && state.wet !== today) {
          hinted = true;
          showNote(fill(text.hint));
          if (text.hint) ctx.live(fill(text.hint));
        }
      }
      if (noteShown) placeNote();
    },
    click() { water(); },
    key(k) {
      if (!looking()) return false;
      if (k === "enter" || k === " ") { water(); return true; }
      return false;
    },
    tip() { return seq >= 0 ? null : fill(state.wet === today ? text.tipDone : text.tip) || null; },
    get busy() { return seq >= 0 || sway >= 0 || !!growing; },
    dispose() {
      clearTimeout(noteTimer);
      note.remove();
      ctx.scene.remove(can, stream);
      for (const m of parts) ctx.interact.delete(m);
      ctx.interact.delete(can);
      ctx.interact.delete(stream);
      for (const leaf of L) { leaf.mesh.visible = true; leaf.mesh.scale.copy(leaf.s); leaf.mesh.quaternion.copy(leaf.q); }
      if (soilDry) soilMat.color.copy(soilDry);
      canGeo.dispose(); canMat.dispose(); streamGeo.dispose(); streamMat.dispose();
    },
  };
  for (const m of parts) ctx.interact.set(m, { kind: "plant", part: m.name, owner: api });
  return api;
}
