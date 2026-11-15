// Room object: the three picture frames leaning on the shelf (GitHub, LinkedIn, X, from content).
// A click tilts a frame forward and shows "Open <name>"; a second click opens the link in a new tab; a click
// anywhere else, or walking away, stands it back up.
//
// Meshes (scene/objects/MESHES.md, obj_frames):
//   frame_1 .. frame_3          empties, the pivot on the frame's bottom edge at the wall (frame_1 the leftmost)
//   frame_N_border              frame and glass (a click target)
//   frame_N_picture             the picture: four corners, UV 0..1, painted here (its V may run either way)
// Content: content.site.room.frames = { open, hint, items: [{ link, name, handle, motif }] } in frame order;
// content.links[link] is the URL. A frame without an item or a URL keeps its baked picture and is not clickable.
// Look (owner, 2026-11-15, option B "pictures of the work"): a picture of what the link holds (motif "code": a
// contribution grid, "work": a career line, "posts": a stack of posts), the name and handle below. No logos.

const TILT = 0.38; // radians the top comes forward (about 22 degrees; the frames lean back about 6)
const TILT_MS = 320;
const PRINT_GLOW = 0.3;
const FAR = 2.6; // metres: farther than this, a tilted frame tilts back (the visitor left; the frames stop is 1.2 m away on a
// desktop, 1.9 m on a phone, the desk view 3.7 m)
const W = 480;
const H = 640; // canvas pixels, portrait 3 : 4 like the pictures
const SANS = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
const MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';

export function createFrames(THREE, ctx) {
  const room = ctx.root;
  const text = (ctx.content && ctx.content.site && ctx.content.site.room && ctx.content.site.room.frames) || {};
  const items = text.items || [];
  const links = (ctx.content && ctx.content.links) || {};
  const frames = [];

  for (let i = 1; i <= 3; i++) {
    const node = room.getObjectByName(`frame_${i}`);
    const pic = room.getObjectByName(`frame_${i}_picture`);
    const item = items[i - 1];
    const url = item && links[item.link];
    if (!node || !pic || !pic.isMesh || !item || !url) continue;
    node.updateWorldMatrix(true, true);
    // the picture's corners by their UVs: its size, which way is up, the way it faces
    const pos = pic.geometry.attributes.position, uv = pic.geometry.attributes.uv;
    if (!uv) continue;
    const corner = (score) => {
      let best = 0, bestS = -Infinity;
      for (let k = 0; k < uv.count; k++) { const s = score(uv.getX(k), uv.getY(k)); if (s > bestS) { bestS = s; best = k; } }
      return new THREE.Vector3().fromBufferAttribute(pos, best).applyMatrix4(pic.matrixWorld);
    };
    const p00 = corner((u, v) => -u - v), p10 = corner((u, v) => u - v), p01 = corner((u, v) => v - u);
    const vUp = p01.y > p00.y;
    const right = p10.clone().sub(p00).normalize();
    const up = p01.clone().sub(p00).multiplyScalar(vUp ? 1 : -1).normalize();
    const facing = new THREE.Vector3().crossVectors(right, up).normalize();
    const centre = p00.clone().add(p10).add(p01).add(corner((u, v) => u + v)).multiplyScalar(0.25);

    const canvas = document.createElement("canvas");
    canvas.width = W;
    canvas.height = H;
    const g = canvas.getContext("2d");
    if (!g) continue;
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.flipY = vUp;
    tex.anisotropy = 4;
    // keep the baked material (the room's light on the print), with our picture as its map
    const mat = pic.material.clone();
    mat.map = tex;
    if ("color" in mat && mat.color) mat.color.setScalar(1);
    // the shelf is dim at dusk: the print gives a little light of its own so it reads (PRINT_GLOW of its colours)
    if (mat.emissive) { mat.emissive.setScalar(1); mat.emissiveMap = tex; mat.emissiveIntensity = PRINT_GLOW; }
    mat.needsUpdate = true;
    pic.material = mat;

    const f = {
      i, node, pic, item, url, tex, g, centre, facing,
      pivot: node.getWorldPosition(new THREE.Vector3()),
      axis: new THREE.Vector3().crossVectors(up, facing).normalize(), // +angle: the top comes forward
      rest: node.matrixWorld.clone(),
      k: 0, // 0 at rest, 1 tilted
      goal: 0,
      parts: [pic],
    };
    node.traverse((o) => { if (o.isMesh && o !== pic) f.parts.push(o); });
    paint(f, false);
    frames.push(f);
  }
  if (!frames.length) return null;

  // ---- the pictures ----
  function paint(f, open) {
    const { g, item } = f;
    g.fillStyle = "#181c28";
    g.fillRect(0, 0, W, H);
    motif(g, item.motif);
    g.textAlign = "center";
    g.fillStyle = "#f0f0f5";
    g.font = `600 ${item.name.length > 2 ? 64 : 96}px ${SANS}`;
    g.fillText(item.name, W / 2, H - 150);
    g.fillStyle = "#a0b4dc";
    g.font = `24px ${MONO}`;
    g.fillText(item.handle || "", W / 2, H - 104);
    if (open) {
      const label = `${text.open || "Open"} ${item.name} ↗`;
      g.font = `600 26px ${SANS}`;
      const w = g.measureText(label).width + 48;
      g.fillStyle = "#ffb054";
      roundRect(g, (W - w) / 2, H - 76, w, 50, 25);
      g.fill();
      g.fillStyle = "#181c28";
      g.fillText(label, W / 2, H - 42);
    }
    f.tex.needsUpdate = true;
  }

  function motif(g, kind) {
    if (kind === "code") { // a contribution grid, the same every time
      const cols = ["#283042", "#1e5a6e", "#2896aa", "#6ed2e6"];
      let s = 7;
      const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
      for (let c = 0; c < 12; c++) for (let r = 0; r < 7; r++) {
        g.fillStyle = cols[Math.min(3, Math.floor(rnd() * 4))];
        roundRect(g, 48 + c * 32, 80 + r * 32, 26, 26, 5);
        g.fill();
      }
    } else if (kind === "work") { // a career line
      g.fillStyle = "#5a6e96";
      g.fillRect(104, 70, 4, 260);
      [90, 170, 250, 320].forEach((y, n) => {
        g.fillStyle = n === 0 ? "#ffb054" : "#6e96ff";
        g.beginPath(); g.arc(106, y, 11, 0, Math.PI * 2); g.fill();
        g.fillStyle = "#46557a"; roundRect(g, 140, y - 18, 250 - n * 34, 13, 6); g.fill();
        g.fillStyle = "#323e5a"; roundRect(g, 140, y + 2, 170 - n * 26, 10, 5); g.fill();
      });
    } else { // a stack of posts
      [70, 170, 270].forEach((y, n) => {
        g.fillStyle = "#242c40"; roundRect(g, 48, y, W - 96, 82, 14); g.fill();
        g.fillStyle = "#6e96ff"; g.beginPath(); g.arc(84, y + 30, 16, 0, Math.PI * 2); g.fill();
        g.fillStyle = "#5a6e96"; roundRect(g, 114, y + 20, W - 230 - n * 24, 12, 6); g.fill();
        g.fillStyle = "#3c4a68"; roundRect(g, 114, y + 44, W - 280, 10, 5); g.fill();
      });
    }
  }

  function roundRect(g, x, y, w, h, r) {
    g.beginPath();
    g.moveTo(x + r, y);
    g.arcTo(x + w, y, x + w, y + h, r);
    g.arcTo(x + w, y + h, x, y + h, r);
    g.arcTo(x, y + h, x, y, r);
    g.arcTo(x, y, x + w, y, r);
    g.closePath();
  }

  // ---- tilt ----
  const _m = new THREE.Matrix4(), _r = new THREE.Matrix4(), _t = new THREE.Matrix4(), _inv = new THREE.Matrix4();
  function place(f) {
    const a = TILT * f.k * f.k * (3 - 2 * f.k); // eased
    _t.makeTranslation(f.pivot.x, f.pivot.y, f.pivot.z);
    _r.makeRotationAxis(f.axis, a);
    _m.copy(_t).multiply(_r).multiply(_inv.makeTranslation(-f.pivot.x, -f.pivot.y, -f.pivot.z)).multiply(f.rest);
    const parent = f.node.parent;
    if (parent) { parent.updateWorldMatrix(true, false); _m.premultiply(_inv.copy(parent.matrixWorld).invert()); }
    _m.decompose(f.node.position, f.node.quaternion, f.node.scale);
  }

  let tilted = null; // the frame that is forward, or null
  function tilt(f) {
    if (tilted && tilted !== f) { tilted.goal = 0; paint(tilted, false); }
    tilted = f;
    if (f) {
      f.goal = 1;
      paint(f, true);
      ctx.live(`${f.item.name}. ${text.hint || "Click again to open."}`);
    }
  }
  function open(f) {
    window.open(f.url, "_blank", "noopener");
    ctx.live(`${text.open || "Open"} ${f.item.name}`);
  }

  const api = {
    frame(dt) {
      if (tilted) {
        const cam = ctx.view();
        if (cam && cam.position.distanceTo(tilted.centre) > FAR) { tilted.goal = 0; paint(tilted, false); tilted = null; }
      }
      for (const f of frames) {
        if (f.k === f.goal) continue;
        const step = ctx.reduce ? 1 : dt / TILT_MS;
        f.k = f.goal > f.k ? Math.min(f.goal, f.k + step) : Math.max(f.goal, f.k - step);
        place(f);
      }
    },
    click(part) {
      const f = frames.find((x) => x.i === part);
      if (!f) return;
      if (tilted === f) open(f);
      else tilt(f);
    },
    away() { // a click anywhere else (owner, 2026-11-15): the tilted frame stands back up
      if (!tilted) return;
      tilted.goal = 0;
      paint(tilted, false);
      tilted = null;
    },
    key(k) {
      const cam = ctx.view();
      if (!cam || !frames.some((f) => cam.position.distanceTo(f.centre) < FAR)) return false; // only at the shelf
      if (k === "1" || k === "2" || k === "3") { api.click(Number(k)); return true; }
      if (k === "enter" && tilted) { open(tilted); return true; }
      return false;
    },
    tip(hit) {
      const f = frames.find((x) => x.parts.includes(hit && hit.object));
      return f ? f.item.name : null;
    },
    get busy() { return frames.some((f) => f.k !== f.goal); },
    dispose() {
      for (const f of frames) {
        for (const m of f.parts) ctx.interact.delete(m);
        f.k = 0; place(f);
        f.tex.dispose();
      }
    },
  };
  for (const f of frames) for (const m of f.parts) ctx.interact.set(m, { kind: "frames", part: f.i, owner: api });
  return api;
}
