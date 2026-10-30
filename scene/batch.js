// Draw-call batching for the GLB room (?room&glb). Called once from desktop.js after the GLB loads.
// Many small named meshes (keyboard keys, piano keys, DJ pads, knobs and faders) are merged into one mesh per
// material, so each batch costs one draw call per material instead of one per part. Names in the GLB do not
// change: the original nodes stay in the tree, hidden, as the parts' pivots and for getObjectByName.
//
// Each batch is a THREE.Mesh added to the lowest common ancestor of its parts (so offsets are in that
// ancestor's frame). batch.userData:
//   batch        the batch id (key of room.userData.batches)
//   partNames    array: part index -> name ("kb_key_a")
//   parts        { name: { index, pivot: [x,y,z] } }   pivot of the part in the batch's frame
//   parts[name].pivot / .axis / .quat   the part's origin, its local +Z and its rest rotation, in the batch's frame
//   setOffset(name, x, y, z)       move one part by (x,y,z) in the batch's frame, from its rest place
//   setOffsetLocal(name, x, y, z)  the same, with (x,y,z) in the part's own axes (a drawer slides along local -Y)
//   setAngle(name, radians)        turn one part about its own local +Z through its pivot (a fan, a knob)
//   setGlow(name, r, g, b)         add a light colour to one part's emissive (linear rgb, 0 = off)
//   partAtFace(hit)                part name for a raycast hit on this mesh (reads the per-vertex index)
//   (offset, then angle: a part turns where it stands, and the offset moves the turned part)
// The setters write a small float texture (one texel per part; rows: 0 offset, 1 glow, 2 pivot and angle, 3 axis)
// that the vertex and fragment shaders read, so moving, turning or lighting a part is a texel write and the batch
// stays one draw call per material. Nothing moves at load: all rows are zero. After a setter, the batch needs no
// other call; the room redraws when the object that moved the part asks for a frame (needsRender in desktop.js).
// The per-vertex attribute is `aPart` (the part index). pick.js reads it to turn a hit face into a part name.

import * as THREE from "three";

// id -> which nodes join (by name). Only meshes or groups whose name matches are taken.
export const BATCHES = {
  kb_keys: /^kb_key_[a-z0-9]+$/,
  piano_keys: /^piano_key_[a-g]s?\d$/,
  dj_pads: /^dj_(pad_[lr]_\d\d|cue_[lr]|play_[lr])$/,
  dj_knobs: /^dj_knob_[a-z_]+$/,
  dj_faders: /^dj_(fader_[lr]|tempo_[lr]|xfader)$/,
  desk_drawers: /^desk_drawers_\d\d_drawer_\d\d$/,
  frame_borders: /^frame_\d_border$/,
  nanoleaf_panels: /^nanoleaf_panel_\d\d$/,
  rig_fans: /^rig_(gpu_)?fan_\d\d$/,
};

const _inv = new THREE.Matrix4();
const _m = new THREE.Matrix4();
const _n = new THREE.Matrix3();
const _v = new THREE.Vector3();

function commonAncestor(nodes) {
  const chain = (o) => { const c = []; for (; o; o = o.parent) c.unshift(o); return c; };
  const chains = nodes.map(chain);
  let anc = chains[0][0];
  for (let i = 0; chains.every((c) => c[i] === chains[0][i] && c.length > i + 1); i++) anc = chains[0][i];
  return anc;
}

function patchMaterial(src, tex, size) {
  const m = src.clone();
  m.userData = { ...src.userData, partBatch: true };
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uPartTex = { value: tex };
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nattribute float aPart;\nuniform sampler2D uPartTex;\nvarying vec3 vPartGlow;")
      .replace("#include <beginnormal_vertex>",
        `#include <beginnormal_vertex>
int pi_ = int(aPart + 0.5);
vec4 pPiv = texelFetch(uPartTex, ivec2(pi_, 2), 0);
vec3 pAx = texelFetch(uPartTex, ivec2(pi_, 3), 0).xyz;
float pC = cos(pPiv.w), pS = sin(pPiv.w);
objectNormal = objectNormal * pC + cross(pAx, objectNormal) * pS + pAx * dot(pAx, objectNormal) * (1.0 - pC);`)
      .replace("#include <begin_vertex>",
        `#include <begin_vertex>
vec3 pq = transformed - pPiv.xyz;
transformed = pPiv.xyz + pq * pC + cross(pAx, pq) * pS + pAx * dot(pAx, pq) * (1.0 - pC);
transformed += texelFetch(uPartTex, ivec2(pi_, 0), 0).xyz;
vPartGlow = texelFetch(uPartTex, ivec2(pi_, 1), 0).rgb;`);
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vPartGlow;")
      .replace("#include <emissivemap_fragment>", "#include <emissivemap_fragment>\ntotalEmissiveRadiance += vPartGlow;");
  };
  m.customProgramCacheKey = () => "partbatch";
  return m;
}

function buildBatch(id, parts, room) {
  const ancestor = commonAncestor(parts);
  ancestor.updateWorldMatrix(true, false);
  _inv.copy(ancestor.matrixWorld).invert();
  const partNames = parts.map((p) => p.name);
  const info = {};
  const byMaterial = new Map(); // material -> [{ geo, matrix, part }]
  parts.forEach((part, index) => {
    part.updateWorldMatrix(true, true);
    _m.multiplyMatrices(_inv, part.matrixWorld);
    const pq = new THREE.Quaternion().setFromRotationMatrix(_m.clone().scale(_v.set(1, 1, 1).divide(new THREE.Vector3().setFromMatrixScale(_m))));
    info[part.name] = {
      index,
      pivot: _v.setFromMatrixPosition(_m).toArray(),
      axis: new THREE.Vector3(0, 0, 1).applyQuaternion(pq).toArray(),
      quat: pq,
    };
    part.traverse((o) => {
      if (!o.isMesh || Array.isArray(o.material)) return;
      if (!byMaterial.has(o.material)) byMaterial.set(o.material, []);
      byMaterial.get(o.material).push({ geo: o.geometry, matrix: new THREE.Matrix4().multiplyMatrices(_inv, o.matrixWorld), index });
    });
  });

  // merged geometry: position, normal, uv, aPart; one index range per material (a geometry group each)
  let nv = 0, ni = 0;
  for (const list of byMaterial.values()) for (const e of list) { nv += e.geo.attributes.position.count; ni += e.geo.index ? e.geo.index.count : e.geo.attributes.position.count; }
  const pos = new Float32Array(nv * 3), nor = new Float32Array(nv * 3), uv = new Float32Array(nv * 2), pid = new Float32Array(nv);
  const idx = new Uint32Array(ni);
  const geometry = new THREE.BufferGeometry();
  const mats = [];
  let vo = 0, io = 0;
  for (const [material, list] of byMaterial) {
    const start = io;
    for (const { geo, matrix, part: _p, index } of list) {
      const count = geo.attributes.position.count;
      _n.getNormalMatrix(matrix);
      for (let i = 0; i < count; i++) {
        _v.fromBufferAttribute(geo.attributes.position, i).applyMatrix4(matrix).toArray(pos, (vo + i) * 3);
        if (geo.attributes.normal) _v.fromBufferAttribute(geo.attributes.normal, i).applyMatrix3(_n).normalize().toArray(nor, (vo + i) * 3);
        if (geo.attributes.uv) { uv[(vo + i) * 2] = geo.attributes.uv.getX(i); uv[(vo + i) * 2 + 1] = geo.attributes.uv.getY(i); }
        pid[vo + i] = index;
      }
      if (geo.index) for (let i = 0; i < geo.index.count; i++) idx[io++] = vo + geo.index.getX(i);
      else for (let i = 0; i < count; i++) idx[io++] = vo + i;
      vo += count;
    }
    geometry.addGroup(start, io - start, mats.length);
    mats.push(material);
  }
  geometry.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geometry.setAttribute("normal", new THREE.BufferAttribute(nor, 3));
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
  geometry.setAttribute("aPart", new THREE.BufferAttribute(pid, 1));
  geometry.setIndex(new THREE.BufferAttribute(idx, 1));
  geometry.computeBoundingSphere();
  geometry.computeBoundingBox();

  // per-part state: row 0 offset (xyz), row 1 glow (rgb), row 2 pivot (xyz) and angle (w), row 3 axis (xyz)
  const n = parts.length;
  const data = new Float32Array(n * 4 * 4);
  for (const p of Object.values(info)) {
    data.set(p.pivot, (2 * n + p.index) * 4);
    data.set(p.axis, (3 * n + p.index) * 4);
  }
  const tex = new THREE.DataTexture(data, n, 4, THREE.RGBAFormat, THREE.FloatType);
  tex.minFilter = tex.magFilter = THREE.NearestFilter;
  tex.generateMipmaps = false;
  tex.needsUpdate = true;
  const mesh = new THREE.Mesh(geometry, mats.map((m) => patchMaterial(m, tex)));
  mesh.name = `batch_${id}`;
  // Parts can move a little, so a bounding sphere from the rest pose is padded; the batch is small anyway.
  mesh.frustumCulled = true;
  const write = (row, name, a, b, c) => {
    const p = info[name];
    if (!p) return false;
    const o = (row * n + p.index) * 4;
    data[o] = a; data[o + 1] = b; data[o + 2] = c;
    tex.needsUpdate = true;
    return true;
  };
  mesh.userData = {
    batch: id,
    partNames,
    parts: info,
    setOffset: (name, x, y, z) => write(0, name, x, y, z),
    setOffsetLocal: (name, x, y, z) => {
      const p = info[name];
      if (!p) return false;
      _v.set(x, y, z).applyQuaternion(p.quat);
      return write(0, name, _v.x, _v.y, _v.z);
    },
    setAngle: (name, a) => {
      const p = info[name];
      if (!p) return false;
      data[(2 * n + p.index) * 4 + 3] = a;
      tex.needsUpdate = true;
      return true;
    },
    setGlow: (name, r, g, b) => write(1, name, r, g, b),
    partAtFace: (hit) => partNames[Math.round(geometry.attributes.aPart.getX(hit.face.a))],
  };
  ancestor.add(mesh);
  parts.forEach((p) => { p.visible = false; });
  return mesh;
}

// Merge every batch that has parts in the room. Returns { id: mesh }, also stored on room.userData.batches.
export function batchRoom(room, spec = BATCHES) {
  const out = {};
  for (const [id, re] of Object.entries(spec)) {
    const parts = [];
    room.traverse((o) => { if (re.test(o.name) && !parts.some((p) => p === o)) parts.push(o); });
    if (parts.length < 2) continue;
    parts.sort((a, b) => (a.name < b.name ? -1 : 1));
    out[id] = buildBatch(id, parts, room);
  }
  room.userData.batches = out;
  return out;
}
