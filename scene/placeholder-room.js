// Placeholder room: stands in for the Phase 4 GLB. Phase 4 replaces this file's use with a
// GLB loader; desktop.js only relies on the mesh names below, found with getObjectByName().
//
// Units are metres, y up, the room faces +z (the camera looks toward -z).
// Mesh names (the API between the model and the code, first entries of the Blender list):
//   monitor_body    the case/bezel of the desk monitor
//   monitor_screen  16:10 plane in front of the body, UVs 0..1 left-to-right, bottom-to-top
//   floor           wooden floor
//   wall_back       back wall
//   desk_top        desk surface
//   desk_leg_fl, desk_leg_fr, desk_leg_bl, desk_leg_br   desk legs
//   monitor_neck, monitor_base   the stand
// Colours are rough, from docs/moodboard/room-sketch.html. Looks come in Phase 4.

const WALL = 0xf2eee7;
const FLOOR = 0x3e281a;
const DESK = 0x3b2a1e;
const MONITOR = 0x15181e;

export function buildPlaceholderRoom(THREE) {
  const room = new THREE.Group();
  room.name = "placeholder_room";

  const add = (name, geometry, color, x, y, z, roughness = 0.85) => {
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color, roughness }));
    mesh.name = name;
    mesh.position.set(x, y, z);
    room.add(mesh);
    return mesh;
  };
  const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);

  // Room shell. The wall is a plane facing +z.
  const floor = add("floor", new THREE.PlaneGeometry(8, 8), FLOOR, 0, 0, 0, 0.7);
  floor.rotation.x = -Math.PI / 2;
  add("wall_back", new THREE.PlaneGeometry(8, 3), WALL, 0, 1.5, -0.9, 0.95);

  // Desk: top surface at y = 0.76, back edge 5 cm from the wall.
  const deskZ = -0.5;
  add("desk_top", box(1.6, 0.04, 0.75), DESK, 0, 0.74, deskZ, 0.6);
  const legX = 0.75;
  const legZ = 0.34;
  add("desk_leg_fl", box(0.05, 0.72, 0.05), DESK, -legX, 0.36, deskZ + legZ);
  add("desk_leg_fr", box(0.05, 0.72, 0.05), DESK, legX, 0.36, deskZ + legZ);
  add("desk_leg_bl", box(0.05, 0.72, 0.05), DESK, -legX, 0.36, deskZ - legZ);
  add("desk_leg_br", box(0.05, 0.72, 0.05), DESK, legX, 0.36, deskZ - legZ);

  // Monitor: a 0.56 x 0.35 screen (16:10) in a 0.62 x 0.41 case, on a stand.
  const mz = deskZ;
  const my = 1.065;
  add("monitor_base", box(0.22, 0.012, 0.16), MONITOR, 0, 0.766, mz + 0.02, 0.5);
  add("monitor_neck", box(0.05, 0.2, 0.03), MONITOR, 0, 0.87, mz - 0.03, 0.5);
  add("monitor_body", box(0.62, 0.41, 0.035), MONITOR, 0, my, mz, 0.4);

  // MeshBasicMaterial: desktop.js swaps in the screen texture. A plane's UVs already run
  // left-to-right, bottom-to-top, facing +z.
  const screen = new THREE.Mesh(
    new THREE.PlaneGeometry(0.56, 0.35),
    new THREE.MeshBasicMaterial({ color: 0x13253b })
  );
  screen.name = "monitor_screen";
  screen.position.set(0, my, mz + 0.0185);
  room.add(screen);

  return room;
}
