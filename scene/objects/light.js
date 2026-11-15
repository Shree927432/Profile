// Room object: the ceiling light and its switch by the door. A click on the switch flips the rocker and turns the
// three-square light on: its strips glow and the room fades from dusk to lit; a second click turns it off.
//
// Meshes (scene/objects/MESHES.md, obj_light): light_switch (the working rocker; a click target; origin on its pivot,
// local X along the wall: off = the top half pressed in, on = the bottom half, a turn of 2 x TILT about local X),
// light_switch_plate (the plate and the idle rockers; a click target), light_led (the three frames' diffusers: they
// glow while on).
// Content: content.site.room.light = { tipOn, tipOff, on, off }.
// The room's light comes through ctx.light (objects/CONTRACT.md, 2026-11-15): load() fetches the lights-on bake on
// the first switch-on, set(t) fades it. Owner, 2026-11-15: "use this exact light design", "A wall switch" "By the
// door", "Real lights-on bake", and every visit opens at dusk (nothing remembered). Reduced motion: no fade.

const TILT = (7 * Math.PI) / 180; // the rocker's turn each way from flat (blender/components/ceiling_light.py ROCKER)
const FADE_MS = 700; // the room from dusk to lit
const FLIP_MS = 90; // the rocker
const GLOW = 3.2; // the strips' emissive intensity when on (bloom picks them up)
const GLOW_COLOR = 0xfff0e0; // about 4000 K, the bake's colour

export function createLight(THREE, ctx) {
  const rocker = ctx.root.getObjectByName("light_switch");
  const plate = ctx.root.getObjectByName("light_switch_plate");
  const led = ctx.root.getObjectByName("light_led");
  if (!rocker || !plate) return null;
  const t = (ctx.content && ctx.content.site && ctx.content.site.room && ctx.content.site.room.light) || {};
  const light = ctx.light || null;

  // the strips: their own material, dark until on
  let ledMat = null;
  const ledMesh = led && (led.isMesh ? led : led.children.find((c) => c.isMesh));
  if (ledMesh && ledMesh.material && !Array.isArray(ledMesh.material)) {
    ledMat = ledMesh.material.clone();
    ledMat.emissive = new THREE.Color(GLOW_COLOR);
    ledMat.emissiveIntensity = 0;
    ledMesh.material = ledMat;
  }

  const rest = rocker.quaternion.clone(); // off, as built
  const _q = new THREE.Quaternion(), _x = new THREE.Vector3(1, 0, 0);
  let on = false;
  let k = 0, flip = 0; // the room's fade and the rocker, 0 (off) .. 1 (on)
  let waiting = false; // loading the lights-on bake

  function pose() {
    rocker.quaternion.copy(rest).multiply(_q.setFromAxisAngle(_x, 2 * TILT * flip));
    if (ledMat) ledMat.emissiveIntensity = GLOW * k;
    if (light) light.set(k);
  }
  async function toggle() {
    if (waiting) return;
    on = !on;
    ctx.live(on ? t.on || "The light is on." : t.off || "The light is off.");
    if (on && light && !light.ready) {
      waiting = true;
      await light.load();
      waiting = false;
    }
  }

  const api = {
    frame(dt) {
      const goal = on ? 1 : 0;
      if (flip === goal && (waiting || k === goal)) return;
      if (flip !== goal) flip = ctx.reduce ? goal : goal > flip ? Math.min(1, flip + dt / FLIP_MS) : Math.max(0, flip - dt / FLIP_MS);
      if (!waiting && k !== goal) k = ctx.reduce ? goal : goal > k ? Math.min(1, k + dt / FADE_MS) : Math.max(0, k - dt / FADE_MS);
      pose();
    },
    click() { toggle(); },
    key(key) {
      if (key === "enter" || key === " ") { toggle(); return true; }
      return false;
    },
    tip() { return on ? t.tipOff || "Turn the light off" : t.tipOn || "Turn the light on"; },
    get busy() { const goal = on ? 1 : 0; return waiting || flip !== goal || k !== goal; },
    dispose() {
      on = false; k = flip = 0; pose();
      for (const m of [rocker, plate]) ctx.interact.delete(m);
    },
  };
  for (const m of [rocker, plate]) ctx.interact.set(m, { kind: "light", part: m.name, owner: api });
  return api;
}
