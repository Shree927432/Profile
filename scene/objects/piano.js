// Room object: the upright piano. Its 88 keys play (a click or tap, or the computer's keys A to ' at the piano). The
// music on the rest is a small songbook: a click on its right page turns to the next piece, whose name is on the
// pages, and plays it with the keys moving; the left page turns back. Closing the key cover stops the music.
//
// Meshes (scene/objects/MESHES.md, obj_piano; its own file, scene/assets/piano.glb, so this object is made when the
// file arrives, with ctx.root that file's scene): batch_piano_keys (the 88 keys merged by scene/batch.js, one draw
// call; a click target, the key from partAtFace; each key tips about its own local +X at its back end, setAxisLocal
// and setAngle), piano_sheet (the music on the rest, two pages; a click target; its picture is drawn here, the
// turning page is a strip made here, piano_page_front/_back, in the scene only while it turns), piano_fallboard (the
// key cover; a click target; open as built, about -95 degrees about local X; closed is 0).
// Content: content.site.room.piano = { hint, playing, loading, contents, closed, closedSaid, opened, book, bookSub,
// turn, tipKeys, tipNext, tipBack, tipContents, tipClose, tipOpen }; the pieces are /piano.json (content/piano.json,
// fetched when the piano arrives: the pages show their names). Sound: the Salamander Grand Piano (Alexander Holm,
// CC BY 3.0, the credits page), 30 notes in scene/assets/sound/piano/, one every three semitones, the rest pitched
// from the nearest; loaded on the first play. ctx.audio() starts the sound on that first play (owner, 2026-11-15:
// "On when they play"); muted, the keys still move. Reduced motion: keys do not tip, the sound still plays.

const SOUND = "/scene/assets/sound/piano/";
const PIECES_URL = "/piano.json";
const DIP = (3.2 * Math.PI) / 180; // radians a pressed key tips (its front about 6 mm down)
const DOWN_MS = 40; // a key goes down this fast, and comes up over UP_MS
const UP_MS = 110;
const HOLD_MIN = 0.12, HOLD_MAX = 0.35; // seconds a key stays down for a note in a piece
const LEAD = 0.12; // seconds between a click on the music and the first note
const AHEAD = 1.5; // seconds of a piece's notes handed to the sound ahead of the playing
const BUS = 2.0; // the piano's level into the room's sound (the samples peak low; measured 2026-11-16: pieces peak about -4 dBFS, mean about -22 dB)
const TURN_MS = 750; // a page turning over
const PAPER_GLOW = 0.35; // the pages' own light (share of their colours)
const COVER_MS = 650; // the key cover folding down or up
const SEAT = (2 * Math.PI) / 180; // radians past level the closed cover rests at (its front edge onto the key slip)
const NEAR = 2.2; // metres: the hint shows this close to the keys, looking at the piano
// the computer's keys at the piano: a row of white keys from C4, the row above for the black ones (as in music apps)
const KEYMAP = { a: 60, w: 61, s: 62, e: 63, d: 64, f: 65, t: 66, g: 67, y: 68, h: 69, u: 70, j: 71, k: 72, o: 73, l: 74, p: 75, ";": 76, "'": 77 };
const PC = { c: 0, d: 2, e: 4, f: 5, g: 7, a: 9, b: 11 };
const NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];

export function createPiano(THREE, ctx) {
  const batch = ctx.root.getObjectByName("batch_piano_keys");
  const sheet = ctx.root.getObjectByName("piano_sheet");
  if (!batch || !batch.userData.parts || !batch.userData.setAxisLocal) return null;
  const t = (ctx.content && ctx.content.site && ctx.content.site.room && ctx.content.site.room.piano) || {};
  const B = batch.userData;

  // keys: name <-> MIDI note; each key's turn is about its own +X through its pivot (the back end)
  const keyOf = new Map(), midiOf = new Map();
  for (const name of B.partNames) {
    const m = /^piano_key_([a-g])(s?)(\d)$/.exec(name);
    if (!m) continue;
    const midi = 12 * (Number(m[3]) + 1) + PC[m[1]] + (m[2] ? 1 : 0);
    keyOf.set(midi, name);
    midiOf.set(name, midi);
    B.setAxisLocal(name, 1, 0, 0);
  }
  const noteName = (m) => NAMES[m % 12] + (Math.floor(m / 12) - 1);

  // ---- sound: 30 samples, A0 to C8 every three semitones ----
  const SAMPLES = [];
  for (let m = 21; m <= 108; m += 3) SAMPLES.push(m);
  const fileOf = (m) => ["C", "", "", "Ds", "", "", "Fs", "", "", "A", "", ""][m % 12] + (Math.floor(m / 12) - 1);
  const buffers = new Map(); // sample MIDI -> AudioBuffer
  let loadingSamples = null, bus = null;
  function loadSamples(ac) {
    if (!loadingSamples) {
      loadingSamples = Promise.all(SAMPLES.map(async (m) => {
        try {
          const res = await fetch(SOUND + fileOf(m) + ".mp3");
          buffers.set(m, await ac.decodeAudioData(await res.arrayBuffer()));
        } catch (err) { console.warn("piano sample", m, err); }
      }));
    }
    return loadingSamples;
  }
  function chain(a) {
    if (!bus) { // the piano's own bus: a little headroom and a gentle limiter for full chords
      const g = a.ctx.createGain();
      g.gain.value = BUS;
      const comp = a.ctx.createDynamicsCompressor();
      comp.threshold.value = -10;
      comp.ratio.value = 4;
      comp.attack.value = 0.003;
      comp.release.value = 0.25;
      const limit = a.ctx.createDynamicsCompressor(); // and a limiter: the Moonlight's full chords never clip
      limit.threshold.value = -4; limit.knee.value = 2; limit.ratio.value = 20; limit.attack.value = 0.001; limit.release.value = 0.1;
      g.connect(comp).connect(limit).connect(a.out);
      bus = g;
    }
    return bus;
  }
  const voices = new Set();
  const sounding = new Map(); // MIDI note -> its latest voice
  function sound(midi, vel, when, len) {
    const a = ctx.audio();
    if (!a) return;
    const base = SAMPLES[Math.max(0, Math.min(SAMPLES.length - 1, Math.round((midi - 21) / 3)))];
    const buf = buffers.get(base);
    if (!buf) { loadSamples(a.ctx); return; }
    const at = Math.max(a.ctx.currentTime, when ?? a.ctx.currentTime);
    const src = a.ctx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = Math.pow(2, (midi - base) / 12);
    const g = a.ctx.createGain();
    const peak = 0.05 + 0.8 * vel * vel;
    g.gain.setValueAtTime(peak, at);
    // softer is darker, as a hammer that strikes gently: the one recorded layer is filtered by the velocity
    const tone = a.ctx.createBiquadFilter();
    tone.type = "lowpass";
    tone.frequency.value = 1400 + 15000 * vel * vel;
    tone.Q.value = 0.5;
    // the same key struck again: the string's last sound is damped
    const prev = sounding.get(midi);
    if (prev) { prev.g.gain.cancelScheduledValues(at); prev.g.gain.setTargetAtTime(0, at, 0.03); }
    src.connect(tone).connect(g).connect(chain(a));
    src.start(at);
    if (len) { // a piece: the damper falls at the note's end
      const rel = midi < 48 ? 0.4 : midi < 72 ? 0.26 : 0.17;
      const end = at + len;
      g.gain.setValueAtTime(peak, end);
      g.gain.setTargetAtTime(0, end, rel);
      src.stop(end + rel * 6);
    }
    const v = { src, g };
    voices.add(v);
    sounding.set(midi, v);
    src.onended = () => { voices.delete(v); if (sounding.get(midi) === v) sounding.delete(midi); g.disconnect(); };
  }
  function silence() {
    const a = ctx.audio();
    for (const v of voices) {
      try {
        if (a) { v.g.gain.cancelScheduledValues(a.ctx.currentTime); v.g.gain.setTargetAtTime(0, a.ctx.currentTime, 0.05); }
        v.src.stop(a ? a.ctx.currentTime + 0.3 : 0);
      } catch { /* already stopped */ }
    }
  }

  // ---- keys moving ----
  const down = new Map(); // key name -> until (ms, performance clock)
  const amount = new Map(); // key name -> 0..1 (how far down)
  function press(name, ms) {
    if (!name) return;
    down.set(name, Math.max(down.get(name) || 0, performance.now() + ms));
    if (!amount.has(name)) amount.set(name, 0);
  }
  function stepKeys(dt) {
    const now = performance.now();
    for (const [name, k] of amount) {
      const goal = (down.get(name) || 0) > now ? 1 : 0;
      let v = k;
      if (ctx.reduce) v = 0;
      else if (goal > v) v = Math.min(1, v + dt / DOWN_MS);
      else if (goal < v) v = Math.max(0, v - dt / UP_MS);
      if (v !== k) B.setAngle(name, DIP * v);
      if (v === 0 && goal === 0) { amount.delete(name); down.delete(name); } else amount.set(name, v);
    }
  }

  // ---- the pieces (/piano.json, fetched when the piano arrives: the pages need their names) ----
  let pieces = null, playing = null; // playing: { piece, i, t0 (ms), a, startAt }
  const ready = fetch(PIECES_URL).then((r) => r.json()).then((j) => {
    pieces = (j.pieces || []).map((p) => ({ ...p, ns: p.notes.map(([s, m, len, v]) => ({ s, m, len, vel: v ?? 0.6 })) }));
    paintSpread(spread);
    return pieces;
  }).catch((err) => { console.warn("piano pieces:", err); return null; });
  const label = (p) => `${p.composer}, ${p.title} (${p.era}, ${p.year})`;
  const playingLine = (p) => (t.playing || "Playing: {piece}").replace("{piece}", label(p));
  async function play(piece) {
    stop(false);
    const a = ctx.audio(); // inside the click: starts the sound
    if (a && !buffers.size) showNote(t.loading || "Tuning the piano…");
    if (a) await loadSamples(a.ctx);
    if (piece !== current()) return; // the page was turned again meanwhile
    const a2 = ctx.audio();
    const startAt = a2 ? a2.ctx.currentTime + LEAD : 0;
    playing = { piece, i: 0, sched: 0, t0: performance.now() + LEAD * 1000, a: a2, startAt };
    schedule(0);
    const line = playingLine(piece);
    showNote(line);
    ctx.live(line);
  }
  function stop(said) {
    if (!playing) return;
    playing = null;
    silence();
    for (const name of down.keys()) down.set(name, 0);
    if (said) { showNote(said, 2600); ctx.live(said); } else hideNote();
  }
  // the notes are handed to the sound a little ahead of time, not all at once (the Moonlight's finale is 1,600 notes)
  function schedule(el) {
    const p = playing;
    if (!p || !p.a) return;
    while (p.sched < p.piece.ns.length && p.piece.ns[p.sched].s < el + AHEAD) {
      const n = p.piece.ns[p.sched++];
      sound(n.m, n.vel, p.startAt + n.s, n.len);
    }
  }
  function stepPiece() {
    if (!playing) return;
    const p = playing;
    const el = p.a ? p.a.ctx.currentTime - p.startAt : (performance.now() - p.t0) / 1000;
    schedule(el);
    while (p.i < p.piece.ns.length && p.piece.ns[p.i].s <= el) {
      const n = p.piece.ns[p.i++];
      press(keyOf.get(n.m), 1000 * Math.min(HOLD_MAX, Math.max(HOLD_MIN, n.len * 0.8)));
    }
    if (el > p.piece.seconds + 0.3) { playing = null; if (noteShown) hideNote(); }
  }

  // ---- the songbook on the music rest (2026-11-16, owner: "a page turning feature to change the piece, and names of
  // pieces on the pages"): spread 0 is the contents, spread i the i-th piece (its name, era and its opening drawn as
  // music from its notes). A click on the right page turns forward and plays the new piece ("Turn and play"); on the
  // left page, back. The page turns over the spine with a curl; reduced motion: it changes at once.
  let spread = 0;
  const current = () => (pieces && spread > 0 ? pieces[spread - 1] : null);
  const PW = 640, PH = 904; // one page, canvas pixels (the sheet: two A4 pages side by side)
  const SERIF = 'Georgia, "Times New Roman", serif';
  const book = document.createElement("canvas");
  book.width = 2 * PW;
  book.height = PH;
  const bg = book.getContext("2d");
  const sheetTex = new THREE.CanvasTexture(book);
  sheetTex.colorSpace = THREE.SRGBColorSpace;
  sheetTex.anisotropy = 4;
  let frame3 = null; // the sheet's frame: spine bottom, along (to the right page), up, out (to the reader), sizes
  let oldSheetMat = null;
  if (sheet && sheet.isMesh && sheet.geometry.attributes.uv) {
    sheet.updateWorldMatrix(true, false);
    const pos = sheet.geometry.attributes.position, uv = sheet.geometry.attributes.uv;
    const corner = (f) => {
      let b = 0, bs = -Infinity;
      for (let k = 0; k < uv.count; k++) { const sc = f(uv.getX(k), uv.getY(k)); if (sc > bs) { bs = sc; b = k; } }
      return new THREE.Vector3().fromBufferAttribute(pos, b).applyMatrix4(sheet.matrixWorld);
    };
    const c00 = corner((u, v) => -u - v), c10 = corner((u, v) => u - v), c01 = corner((u, v) => v - u);
    const vUp = c01.y > c00.y;
    const bottomL = vUp ? c00 : c01, bottomR = vUp ? c10 : corner((u, v) => u + v), topL = vUp ? c01 : c00;
    const along = bottomR.clone().sub(bottomL), up = topL.clone().sub(bottomL);
    const W = along.length(), H = up.length();
    along.normalize(); up.normalize();
    frame3 = { spine: bottomL.clone().addScaledVector(along, W / 2), along, up, out: new THREE.Vector3().crossVectors(along, up).normalize(), half: W / 2, H };
    sheetTex.flipY = vUp;
    oldSheetMat = sheet.material;
    const m = sheet.material.clone();
    m.map = sheetTex;
    m.transparent = false; // paper: opaque, whatever the asset's fade-in is doing to the material it was copied from
    m.opacity = 1;
    if (m.color) m.color.setScalar(1);
    // the stand is dim at dusk: the paper gives a little light of its own so the names read (as the frames' prints)
    if (m.emissive) { m.emissive.setScalar(1); m.emissiveMap = sheetTex; m.emissiveIntensity = PAPER_GLOW; }
    sheet.material = m;
  }

  // drawing: a page of the book at x0 of a 2D context
  function paper(g, x0, left) {
    g.fillStyle = "#f3eee1";
    g.fillRect(x0, 0, PW, PH);
    const sh = g.createLinearGradient(left ? x0 + PW - 46 : x0, 0, left ? x0 + PW : x0 + 46, 0); // the fold at the spine
    sh.addColorStop(left ? 0 : 1, "rgba(80,60,30,0)");
    sh.addColorStop(left ? 1 : 0, "rgba(80,60,30,0.16)");
    g.fillStyle = sh;
    g.fillRect(left ? x0 + PW - 46 : x0, 0, 46, PH);
  }
  const STEP = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6], SHARP = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0];
  function staves(g, x0, y0, n, piece, t0, t1) { // n grand staves from y0, the notes from t0 to t1 seconds
    const gap = 9, sysH = 13 * gap + 54, xa = x0 + 64, xb = x0 + PW - 52;
    const per = (t1 - t0) / n;
    g.lineWidth = 1.2;
    for (let k = 0; k < n; k++) {
      const top = y0 + k * sysH, trebleBottom = top + 4 * gap, bassBottom = trebleBottom + 9 * gap;
      g.strokeStyle = "#6c655b";
      for (let l = 0; l < 5; l++) {
        g.beginPath(); g.moveTo(xa, top + l * gap); g.lineTo(xb, top + l * gap); g.stroke();
        g.beginPath(); g.moveTo(xa, trebleBottom + 5 * gap + l * gap); g.lineTo(xb, trebleBottom + 5 * gap + l * gap); g.stroke();
      }
      g.lineWidth = 2;
      g.beginPath(); g.moveTo(xa, top); g.lineTo(xa, bassBottom); g.stroke();
      g.beginPath(); g.moveTo(xb, top); g.lineTo(xb, bassBottom); g.stroke();
      g.lineWidth = 1.2;
      if (!piece) continue;
      const a = t0 + k * per, b = a + per;
      g.fillStyle = g.strokeStyle = "#26221d";
      for (const nt of piece.ns) {
        if (nt.s < a || nt.s >= b) continue;
        const oct = Math.floor(nt.m / 12) - 1, step = oct * 7 + STEP[nt.m % 12];
        const treble = nt.m >= 60;
        const y = treble ? trebleBottom - (step - 30) * gap / 2 : bassBottom - (step - 18) * gap / 2;
        const x = xa + 26 + (nt.s - a) / per * (xb - xa - 44);
        const lineTop = treble ? top : trebleBottom + 5 * gap, lineBottom = treble ? trebleBottom : bassBottom;
        for (let ly = lineBottom + gap; ly <= y + 0.1; ly += gap) { g.beginPath(); g.moveTo(x - 9, ly); g.lineTo(x + 9, ly); g.stroke(); }
        for (let ly = lineTop - gap; ly >= y - 0.1; ly -= gap) { g.beginPath(); g.moveTo(x - 9, ly); g.lineTo(x + 9, ly); g.stroke(); }
        g.beginPath(); g.ellipse(x, y, 5.6, 4, -0.35, 0, Math.PI * 2); g.fill();
        const upStem = y > (lineTop + lineBottom) / 2;
        g.beginPath(); g.moveTo(upStem ? x + 5 : x - 5, y); g.lineTo(upStem ? x + 5 : x - 5, upStem ? y - 30 : y + 30); g.stroke();
        if (SHARP[nt.m % 12]) { g.font = `15px ${SERIF}`; g.fillText("♯", x - 19, y + 5); }
      }
    }
    return sysH;
  }
  function centred(g, x0, y, text, font, color) { g.font = font; g.fillStyle = color; g.textAlign = "center"; g.fillText(text, x0 + PW / 2, y); g.textAlign = "left"; }
  function drawPage(g, x0, n, side) { // spread n, side "l" or "r"
    paper(g, x0, side === "l");
    const ink = "#26221d", soft = "#6c655b";
    if (n === 0) {
      if (side === "l") {
        const count = ["", "One piece", "Two pieces", "Three pieces", "Four pieces", "Five pieces", "Six pieces"][(pieces || []).length] || t.book || "Pieces";
        centred(g, x0, 140, t.book || count, `italic 58px ${SERIF}`, ink);
        centred(g, x0, 190, t.bookSub || "for the piano in this room", `24px ${SERIF}`, soft);
        (pieces || []).forEach((p, i) => {
          const y = 275 + i * Math.min(175, 590 / pieces.length);
          g.fillStyle = ink; g.font = `600 36px ${SERIF}`; g.fillText(`${i + 1}.`, x0 + 52, y);
          g.font = `600 34px ${SERIF}`; g.fillText(p.composer, x0 + 100, y);
          g.font = `30px ${SERIF}`; g.fillText(p.title.split(", ")[0], x0 + 100, y + 42); // the name; its number is on its own page
          g.fillStyle = soft; g.font = `italic 25px ${SERIF}`; g.fillText(`${p.era}, ${p.year}`, x0 + 100, y + 78);
        });
      } else {
        staves(g, x0, 210, 3, null, 0, 1);
        centred(g, x0, 760, t.turn || "Turn the page to play →", `italic 38px ${SERIF}`, ink);
      }
      return;
    }
    const p = pieces[n - 1];
    const T = Math.min(p.seconds, 30);
    if (side === "l") {
      g.fillStyle = soft; g.font = `italic 26px ${SERIF}`; g.textAlign = "right"; g.fillText(`${p.era}, ${p.year}`, x0 + PW - 52, 66); g.textAlign = "left";
      const words = p.title.split(", "); // a catalogue number on its own line: "Nocturne in E-flat major" / "Op. 9 No. 2"
      centred(g, x0, 150, words[0], `600 ${words[0].length > 24 ? 38 : 46}px ${SERIF}`, ink);
      if (words.length > 1) centred(g, x0, 198, words.slice(1).join(", "), `34px ${SERIF}`, ink);
      centred(g, x0, 252, p.composer, `italic 32px ${SERIF}`, ink);
      staves(g, x0, 300, 3, p, 0, T * 3 / 7);
      g.fillStyle = soft; g.font = `18px ${SERIF}`; g.fillText(String(2 * n), x0 + 60, PH - 40);
    } else {
      staves(g, x0, 90, 4, p, T * 3 / 7, T);
      g.fillStyle = soft; g.font = `18px ${SERIF}`; g.textAlign = "right"; g.fillText(String(2 * n + 1), x0 + PW - 60, PH - 40); g.textAlign = "left";
    }
  }
  function paintSpread(n, leftOf = n, rightOf = n) {
    if (!frame3) return;
    drawPage(bg, 0, leftOf, "l");
    drawPage(bg, PW, rightOf, "r");
    sheetTex.needsUpdate = true;
  }

  // the turning page: one strip of N segments bent over the spine, its front the right-hand page, its back the left
  const N = 24;
  let turn = null; // { from, to, fwd, k 0..1 }
  let leaf = null;
  function makeLeaf() {
    const posA = new THREE.BufferAttribute(new Float32Array((N + 1) * 2 * 3), 3);
    const idx = [];
    for (let k = 0; k < N; k++) { const a = 2 * k; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
    const mk = (back) => {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", posA);
      const uv = new Float32Array((N + 1) * 4);
      for (let k = 0; k <= N; k++) { const u = back ? 1 - k / N : k / N; uv.set([u, 0, u, 1], k * 4); }
      geo.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
      geo.setIndex(idx);
      const c = document.createElement("canvas");
      c.width = PW; c.height = PH;
      const tex = new THREE.CanvasTexture(c);
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.anisotropy = 4;
      const mat = sheet.material.clone();
      mat.map = tex;
      if (mat.emissiveMap) mat.emissiveMap = tex;
      mat.side = back ? THREE.BackSide : THREE.FrontSide;
      const mesh = new THREE.Mesh(geo, mat);
      mesh.frustumCulled = false;
      mesh.name = back ? "piano_page_back" : "piano_page_front";
      return { mesh, c, g: c.getContext("2d"), tex };
    };
    leaf = { pos: posA, front: mk(false), back: mk(true) };
  }
  const _a = new THREE.Vector3();
  function bend(k, fwd) {
    const f = frame3, seg = f.half / N, ease = (x) => x * x * (3 - 2 * x), L = 0.35;
    const p = leaf.pos.array;
    _a.copy(f.spine).addScaledVector(f.out, 0.0018);
    let x = 0, z = 0;
    for (let i = 0; i <= N; i++) {
      for (let j = 0; j < 2; j++) {
        const o = (i * 2 + j) * 3;
        p[o] = _a.x + f.along.x * x + f.out.x * z + f.up.x * f.H * j;
        p[o + 1] = _a.y + f.along.y * x + f.out.y * z + f.up.y * f.H * j;
        p[o + 2] = _a.z + f.along.z * x + f.out.z * z + f.up.z * f.H * j;
      }
      if (i === N) break;
      const sOut = (i + 0.5) / N; // 0 at the spine, 1 at the edge: the edge leads, as when a hand lifts it
      const e = ease(Math.min(1, Math.max(0, k * (1 + L) - L * (1 - sOut))));
      const th = Math.PI * (fwd ? e : 1 - e);
      x += seg * Math.cos(th);
      z += seg * Math.sin(th);
    }
    leaf.pos.needsUpdate = true;
    leaf.front.mesh.geometry.computeVertexNormals();
    leaf.back.mesh.geometry.computeVertexNormals();
  }
  function turnTo(to, fwd) {
    if (!frame3 || !pieces) return;
    if (turn) return;
    const from = spread;
    stop(false);
    spread = to;
    if (ctx.reduce) { paintSpread(to); arrive(); return; }
    if (!leaf) makeLeaf();
    // under the leaf: forward, the old left page and the new right; back, the new left and the old right
    if (fwd) { paintSpread(to, from, to); drawPage(leaf.front.g, 0, from, "r"); drawPage(leaf.back.g, 0, to, "l"); }
    else { paintSpread(to, to, from); drawPage(leaf.front.g, 0, to, "r"); drawPage(leaf.back.g, 0, from, "l"); }
    leaf.front.tex.needsUpdate = leaf.back.tex.needsUpdate = true;
    turn = { k: 0, fwd };
    bend(0, fwd);
    ctx.scene.add(leaf.front.mesh, leaf.back.mesh);
  }
  function stepTurn(dt) {
    if (!turn) return;
    turn.k = Math.min(1, turn.k + dt / TURN_MS);
    bend(turn.k, turn.fwd);
    if (turn.k === 1) {
      ctx.scene.remove(leaf.front.mesh, leaf.back.mesh);
      turn = null;
      paintSpread(spread);
      arrive();
    }
  }
  function arrive() { // the page is down: the new piece plays ("Turn and play")
    const p = current();
    if (p) play(p);
    else { const s = t.contents || "The contents. Turn the page for a piece."; showNote(s, 2600); ctx.live(s); }
  }
  function nextPage() {
    if (!pieces) return;
    openCover();
    ctx.audio(); // inside the click: the sound starts now, so the piece can play when the page is down
    turnTo((spread + 1) % (pieces.length + 1), true);
  }
  function prevPage() {
    if (!pieces || spread === 0) return;
    openCover();
    ctx.audio();
    turnTo(spread - 1, false);
  }

  // ---- the key cover (owner, 2026-11-16: "Close the key cover" stops the music) ----
  const cover = ctx.root.getObjectByName("piano_fallboard");
  const coverOpen = cover ? 2 * Math.atan2(cover.quaternion.x, cover.quaternion.w) : 0; // open as built: about -95 deg about local X
  let coverK = 1, coverGoal = 1; // 1 open, 0 closed
  const _xa = new THREE.Vector3(1, 0, 0);
  function openCover() { if (cover && coverGoal === 0) { coverGoal = 1; ctx.live(t.opened || "The key cover is open."); } }
  function closeCover() {
    if (!cover || coverGoal === 0) return;
    coverGoal = 0;
    if (playing) stop(t.closed || "The cover is closed. Turn the page or open it to play.");
    else ctx.live(t.closedSaid || "The key cover is closed.");
  }
  // closed, the keys are hidden (MESHES.md: "Hidden while the fallboard is closed"): the cover is shallower than the
  // keys and sits above them, so their white fronts showed under it (owner, 2026-11-16: "cover is not closing
  // properly"). It also seats a little past level onto the cheeks.
  function stepCover(dt) {
    if (!cover || coverK === coverGoal) return;
    coverK = ctx.reduce ? coverGoal : coverGoal > coverK ? Math.min(1, coverK + dt / COVER_MS) : Math.max(0, coverK - dt / COVER_MS);
    const e = coverK * coverK * (3 - 2 * coverK);
    cover.quaternion.setFromAxisAngle(_xa, SEAT + (coverOpen - SEAT) * e);
    batch.visible = coverK > 0;
  }

  // ---- free play ----
  async function playKey(midi) {
    const name = keyOf.get(midi);
    if (!name) return;
    if (coverGoal === 0) { openCover(); return; } // the first touch opens the cover
    press(name, 160);
    const a = ctx.audio();
    if (!a) return;
    if (!buffers.size) {
      showNote(t.loading || "Tuning the piano…", 1500);
      await loadSamples(a.ctx);
    }
    sound(midi, 0.75);
    if (hintShown && !playing) hideNote();
  }

  // ---- the note above the piano (the hint, what is playing) ----
  const note = document.createElement("p");
  note.className = "room-plant-note room-piano-note";
  note.setAttribute("aria-hidden", "true");
  note.hidden = true;
  ctx.overlay.append(note);
  let noteTimer = 0, noteShown = false, hintShown = false;
  function showNote(s, ms) {
    clearTimeout(noteTimer);
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
  const top = new THREE.Vector3(), _p = new THREE.Vector3();
  if (sheet) { const bx = new THREE.Box3().setFromObject(sheet); top.set((bx.min.x + bx.max.x) / 2, bx.max.y + 0.08, (bx.min.z + bx.max.z) / 2); }
  else new THREE.Box3().setFromObject(batch).getCenter(top);
  const keysCentre = new THREE.Box3().setFromObject(batch).getCenter(new THREE.Vector3());
  function placeNote() {
    const cam = ctx.view();
    if (!cam || !noteShown) return;
    _p.copy(top).project(cam);
    const w = note.offsetWidth || 280, h = note.offsetHeight || 40;
    const x = (_p.x + 1) / 2 * window.innerWidth, y = (1 - _p.y) / 2 * window.innerHeight;
    note.style.left = Math.round(Math.min(Math.max(12, x - w / 2), window.innerWidth - w - 12)) + "px";
    note.style.top = Math.round(Math.min(Math.max(64, y - h - 10), window.innerHeight - h - 12)) + "px";
  }
  const _dir = new THREE.Vector3(), _to = new THREE.Vector3();
  let lastDist = -1, still = 0, near = false;
  const pageOf = (hit) => (hit && hit.uv ? (hit.uv.x < 0.5 ? "l" : "r") : "r");

  const api = {
    frame(dt) {
      stepTurn(dt);
      stepCover(dt);
      stepPiece();
      stepKeys(dt);
      const cam = ctx.view();
      if (cam) {
        const d = cam.position.distanceTo(keysCentre);
        still = Math.abs(d - lastDist) < 0.0005 ? still + 1 : 0;
        lastDist = d;
        cam.getWorldDirection(_dir);
        const look = _dir.dot(_to.subVectors(keysCentre, cam.position).normalize());
        const nowNear = d < NEAR && look > 0.85;
        // away from the piano the note goes; a piece plays on to its end (at most 40 s; the Sound button mutes it)
        if (!nowNear && near) { hintShown = false; hideNote(); }
        if (nowNear && !near && playing) showNote(playingLine(playing.piece));
        if (nowNear && !hintShown && still >= 3 && !playing && !noteShown && !turn) {
          hintShown = true;
          showNote(t.hint || "Play the keys, turn the page for a piece, close the key cover to stop.");
        }
        near = nowNear;
      }
      if (noteShown) placeNote();
    },
    click(part, hit) {
      if (part === "keys" && hit && hit.object && hit.object.userData.partAtFace) {
        playKey(midiOf.get(hit.object.userData.partAtFace(hit)));
      } else if (part === "piano_sheet") {
        if (pageOf(hit) === "l" && spread > 0) prevPage(); else nextPage();
      } else if (part === "piano_fallboard") {
        if (coverGoal === 1) closeCover(); else openCover();
      }
    },
    away() {},
    key(k) {
      if (k in KEYMAP) { playKey(KEYMAP[k]); return true; }
      if (k === "enter" || k === " ") { nextPage(); return true; }
      if (k === "backspace") { prevPage(); return true; }
      return false;
    },
    tip(hit) {
      if (hit && hit.object === batch && B.partAtFace) {
        const m = midiOf.get(B.partAtFace(hit));
        return m ? `${t.tipKeys || "Play"} ${noteName(m)}` : null;
      }
      if (hit && hit.object === sheet) {
        if (pageOf(hit) === "l" && spread > 0) return t.tipBack || "Previous piece";
        return spread === (pieces ? pieces.length : 0) ? t.tipContents || "Back to the contents" : t.tipNext || "Turn the page";
      }
      if (hit && cover && hit.object === cover) return coverGoal === 1 ? t.tipClose || "Close the key cover" : t.tipOpen || "Open the key cover";
      return null;
    },
    get busy() { return !!playing || amount.size > 0 || !!turn || coverK !== coverGoal; },
    dispose() {
      stop(false);
      clearTimeout(noteTimer);
      note.remove();
      for (const name of B.partNames) B.setAngle(name, 0);
      ctx.interact.delete(batch);
      if (sheet) { ctx.interact.delete(sheet); if (oldSheetMat) { sheet.material.dispose(); sheet.material = oldSheetMat; } }
      if (cover) { ctx.interact.delete(cover); cover.quaternion.setFromAxisAngle(_xa, coverOpen); }
      if (leaf) { ctx.scene.remove(leaf.front.mesh, leaf.back.mesh); for (const s of [leaf.front, leaf.back]) { s.mesh.geometry.dispose(); s.mesh.material.dispose(); s.tex.dispose(); } }
      sheetTex.dispose();
      void ready;
    },
  };
  ctx.interact.set(batch, { kind: "piano", part: "keys", owner: api });
  if (sheet && sheet.isMesh) ctx.interact.set(sheet, { kind: "piano", part: "piano_sheet", owner: api });
  if (cover && cover.isMesh) ctx.interact.set(cover, { kind: "piano", part: "piano_fallboard", owner: api });
  return api;
}
