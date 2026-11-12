// Where the free camera may be (2026-11-12): the room's inside less a margin, a height band, and out of the
// furniture. Used by desktop.js only, GLB room only.
//
// The room is cut into CELL-sized cells. Every triangle of every room mesh marks the cells its bounding box
// touches (conservative: a slanted triangle marks a little air too), then the marks grow by MARGIN, so a free
// cell is at least about MARGIN from any surface and the near plane (5 cm) never reaches geometry. Built once
// when the browser is idle (a few tens of ms), again for a late asset (the car shelf). Until it is built the
// camera is only kept inside the room and the height band.
//
//   build(meshes)         mark these meshes (world space) and grow the marks; call again to add more
//   constrain(from, to)   moves `to` to where the camera may go from `from`: clamped to the room and the band,
//                         and sliding along furniture (axis by axis) instead of entering it. Long steps are
//                         walked in short ones, so nothing thin is jumped. No allocation.
//   isFree(p)             true when p is in free space

const CELL = 0.08; // metres
const MARGIN = 0.22; // metres kept from any surface
const BAND = [0.6, 2.4]; // camera height, metres
const SUBSTEP = 0.08; // metres per check on a long step

export function createRoomSpace({ THREE, inside }) {
  const lo = inside.min.clone();
  const nx = Math.ceil((inside.max.x - lo.x) / CELL);
  const ny = Math.ceil((inside.max.y - lo.y) / CELL);
  const nz = Math.ceil((inside.max.z - lo.z) / CELL);
  const marks = new Uint8Array(nx * ny * nz); // a surface touches the cell
  const solid = new Uint8Array(nx * ny * nz); // marks grown by MARGIN
  const tmp = new Uint8Array(nx * ny * nz);
  const R = Math.ceil(MARGIN / CELL);
  const box = new THREE.Box3(
    new THREE.Vector3(inside.min.x + MARGIN, BAND[0], inside.min.z + MARGIN),
    new THREE.Vector3(inside.max.x - MARGIN, BAND[1], inside.max.z - MARGIN),
  );
  let ready = false;

  const idx = (i, j, k) => (k * ny + j) * nx + i;
  const ci = (v, o, n) => Math.min(n - 1, Math.max(0, Math.floor((v - o) / CELL)));

  const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _c = new THREE.Vector3();
  function mark(meshes) {
    for (const m of meshes) {
      const pos = m.geometry.attributes.position;
      if (!pos) continue;
      const index = m.geometry.index;
      const n = index ? index.count : pos.count;
      const mw = m.matrixWorld;
      for (let t = 0; t + 2 < n; t += 3) {
        const i0 = index ? index.getX(t) : t, i1 = index ? index.getX(t + 1) : t + 1, i2 = index ? index.getX(t + 2) : t + 2;
        _a.fromBufferAttribute(pos, i0).applyMatrix4(mw);
        _b.fromBufferAttribute(pos, i1).applyMatrix4(mw);
        _c.fromBufferAttribute(pos, i2).applyMatrix4(mw);
        const x0 = ci(Math.min(_a.x, _b.x, _c.x), lo.x, nx), x1 = ci(Math.max(_a.x, _b.x, _c.x), lo.x, nx);
        const y0 = ci(Math.min(_a.y, _b.y, _c.y), lo.y, ny), y1 = ci(Math.max(_a.y, _b.y, _c.y), lo.y, ny);
        const z0 = ci(Math.min(_a.z, _b.z, _c.z), lo.z, nz), z1 = ci(Math.max(_a.z, _b.z, _c.z), lo.z, nz);
        for (let k = z0; k <= z1; k++) for (let j = y0; j <= y1; j++) for (let i = x0; i <= x1; i++) marks[idx(i, j, k)] = 1;
      }
    }
  }
  // Grow the marks by R cells along each axis in turn (a box-shaped grow).
  function grow() {
    const pass = (srcArr, dstArr, axis) => {
      for (let k = 0; k < nz; k++) for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
        let hit = 0;
        for (let d = -R; d <= R && !hit; d++) {
          const ii = axis === 0 ? i + d : i, jj = axis === 1 ? j + d : j, kk = axis === 2 ? k + d : k;
          if (ii < 0 || jj < 0 || kk < 0 || ii >= nx || jj >= ny || kk >= nz) continue;
          hit = srcArr[idx(ii, jj, kk)];
        }
        dstArr[idx(i, j, k)] = hit;
      }
    };
    pass(marks, solid, 0);
    pass(solid, tmp, 1);
    pass(tmp, solid, 2);
  }

  function build(meshes) {
    for (const m of meshes) m.updateWorldMatrix(true, false);
    mark(meshes);
    grow();
    ready = true;
  }

  function isFree(p) {
    if (!box.containsPoint(p)) return false;
    if (!ready) return true;
    return !solid[idx(ci(p.x, lo.x, nx), ci(p.y, lo.y, ny), ci(p.z, lo.z, nz))];
  }

  const _p = new THREE.Vector3(), _q = new THREE.Vector3(), _step = new THREE.Vector3();
  // One short step with sliding: whole, else axis by axis.
  function slide(p, target) {
    if (isFree(target)) { p.copy(target); return; }
    _q.copy(p); _q.x = target.x; if (isFree(_q)) p.x = target.x;
    _q.copy(p); _q.z = target.z; if (isFree(_q)) p.z = target.z;
    _q.copy(p); _q.y = target.y; if (isFree(_q)) p.y = target.y;
  }
  function constrain(from, to) {
    box.clampPoint(to, to);
    if (!from || !ready) return;
    // Starting in blocked space (a flight can end near something): let the camera move, so it is never stuck.
    if (!isFree(from)) return;
    _p.copy(from);
    const n = Math.max(1, Math.ceil(from.distanceTo(to) / SUBSTEP));
    _step.subVectors(to, from).divideScalar(n);
    for (let s = 0; s < n; s++) {
      _w.copy(_p).add(_step); // where this sub-step wants to go; slide() may move only part of the way
      slide(_p, _w);
    }
    to.copy(_p);
  }
  const _w = new THREE.Vector3();

  return { build, constrain, isFree, get ready() { return ready; }, box };
}
