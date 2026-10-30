// The pick map: which meshes can be clicked, and who owns them. One raycaster for the room.
// This object is what room objects receive as ctx.interact (see objects/CONTRACT.md):
//
//   interact.set(mesh, { kind, part, owner })   register a part; owner is optional
//   interact.delete(mesh)                       unregister (object dispose)
//   interact.pick(clientX, clientY)             -> { mesh, info, hit } | null  (nearest registered mesh)
//
// Only registered meshes are tested, so unregistered geometry never blocks a pick.
// desktop.js decides what a pick means (dispatchTap): the screen gets a click with canvas
// coordinates, any other owner gets owner.click(part, hit).
// pick() also returns `part`: for a batched mesh (batch.js) the name of the part under the hit face.

export function createPickMap(THREE, camera, canvas) {
  const map = new Map(); // mesh -> { kind, part, owner? }
  const raycaster = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  let targets = []; // array copy of the map's keys, rebuilt only when the map changes

  return {
    set(mesh, info) {
      map.set(mesh, info);
      targets = [...map.keys()];
    },
    delete(mesh) {
      map.delete(mesh);
      targets = [...map.keys()];
    },
    pick(clientX, clientY) {
      if (!targets.length) return null;
      const r = canvas.getBoundingClientRect();
      ndc.set(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
      camera.updateMatrixWorld();
      raycaster.setFromCamera(ndc, camera);
      const hit = raycaster.intersectObjects(targets, false)[0];
      if (!hit) return null;
      // A batched mesh (batch.js) answers with the part under the hit face; otherwise the registered part.
      const ud = hit.object.userData;
      const part = ud.partAtFace ? ud.partAtFace(hit) : map.get(hit.object).part;
      return { mesh: hit.object, info: map.get(hit.object), hit, part };
    },
  };
}
