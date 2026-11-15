// Room object: the upright piano. Its 88 keys play (a click or tap, or the computer's keys A to ; at the piano), and
// a click on the music on the rest plays a short piece with the keys moving: Bach, then Beethoven, then Chopin; a
// click while one plays stops it.
//
// Meshes (scene/objects/MESHES.md, obj_piano; its own file, scene/assets/piano.glb, so this object is made when the
// file arrives, with ctx.root that file's scene): batch_piano_keys (the 88 keys merged by scene/batch.js, one draw
// call; a click target, the key from partAtFace; each key tips about its own local +X at its back end, setAxisLocal
// and setAngle), piano_sheet (the music on the rest; a click target).
// Content: content.site.room.piano = { hint, playing, stopped, tipKeys, tipSheet, tipStop, loading }; the pieces are
// /piano.json (content/piano.json, fetched on the first play). Sound: the Salamander Grand Piano (Alexander Holm,
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
const BUS = 2.4; // the piano's level into the room's sound (the samples peak low; measured 2026-11-16: pieces peak about -4 dBFS, mean about -22 dB)
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
      g.connect(comp).connect(a.out);
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

  // ---- the pieces ----
  let pieces = null, loadingPieces = null, next = 0, playing = null; // playing: { piece, i, t0 (ms), ac, a0 }
  async function getPieces() {
    if (pieces) return pieces;
    if (!loadingPieces) {
      loadingPieces = fetch(PIECES_URL).then((r) => r.json()).then((j) => {
        pieces = (j.pieces || []).map((p) => {
                    const ns = p.notes.map(([s, m, len, v]) => ({ s, m, len, v }));
          for (const n of ns) n.vel = n.v ?? 0.6; // shaped like a pianist's playing by blender/tools/midi_excerpt.py
          return { ...p, ns };
        });
        return pieces;
      }).catch((err) => { console.warn("piano pieces:", err); loadingPieces = null; return null; });
    }
    return loadingPieces;
  }
  const label = (p) => `${p.composer}, ${p.title} (${p.era}, ${p.year})`;
  const playingLine = (p) => (t.playing || "Playing: {piece}").replace("{piece}", label(p));
  async function playNext() {
    if (playing) { stop(true); return; }
    const a = ctx.audio(); // inside the click: starts the sound
    showNote(t.loading || "Loading the piano…");
    const ps = await getPieces();
    if (a) await loadSamples(a.ctx);
    if (!ps || !ps.length) { hideNote(); return; }
    const piece = ps[next % ps.length];
    next++;
    const a2 = ctx.audio();
    const startAt = a2 ? a2.ctx.currentTime + LEAD : 0;
    if (a2) for (const n of piece.ns) sound(n.m, n.vel, startAt + n.s, n.len);
    playing = { piece, i: 0, t0: performance.now() + LEAD * 1000, a: a2, startAt };
    const line = playingLine(piece);
    showNote(line);
    ctx.live(line);
  }
  function stop(said) {
    if (!playing) return;
    playing = null;
    silence();
    for (const name of down.keys()) down.set(name, 0);
    if (said) { const s = t.stopped || "Stopped."; showNote(s, 2500); ctx.live(s); } else hideNote();
  }
  function stepPiece() {
    if (!playing) return;
    const p = playing;
    const el = p.a ? p.a.ctx.currentTime - p.startAt : (performance.now() - p.t0) / 1000;
    while (p.i < p.piece.ns.length && p.piece.ns[p.i].s <= el) {
      const n = p.piece.ns[p.i++];
      press(keyOf.get(n.m), 1000 * Math.min(HOLD_MAX, Math.max(HOLD_MIN, n.len * 0.8)));
    }
    if (el > p.piece.seconds + 0.3) { playing = null; if (noteShown) hideNote(); }
  }

  // ---- free play ----
  async function playKey(midi) {
    const name = keyOf.get(midi);
    if (!name) return;
    press(name, 160);
    const a = ctx.audio();
    if (!a) return;
    if (!buffers.size) {
      showNote(t.loading || "Loading the piano…", 1500);
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

  const api = {
    frame(dt) {
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
        if (nowNear && !hintShown && still >= 3 && !playing && !noteShown) {
          hintShown = true;
          showNote(t.hint || "Play the keys, or click the music for a piece.");
        }
        near = nowNear;
      }
      if (noteShown) placeNote();
    },
    click(part, hit) {
      if (part === "keys" && hit && hit.object && hit.object.userData.partAtFace) {
        playKey(midiOf.get(hit.object.userData.partAtFace(hit)));
      } else if (part === "piano_sheet") playNext();
    },
    away() {},
    key(k) {
      if (k in KEYMAP) { playKey(KEYMAP[k]); return true; }
      if (k === "enter" || k === " ") { playNext(); return true; }
      return false;
    },
    tip(hit) {
      if (hit && hit.object === batch && B.partAtFace) {
        const m = midiOf.get(B.partAtFace(hit));
        return m ? `${t.tipKeys || "Play"} ${noteName(m)}` : null;
      }
      if (hit && hit.object === sheet) return playing ? t.tipStop || "Stop" : t.tipSheet || "Play a piece";
      return null;
    },
    get busy() { return !!playing || amount.size > 0; },
    dispose() {
      stop(false);
      clearTimeout(noteTimer);
      note.remove();
      for (const name of B.partNames) B.setAngle(name, 0);
      ctx.interact.delete(batch);
      if (sheet) ctx.interact.delete(sheet);
    },
  };
  ctx.interact.set(batch, { kind: "piano", part: "keys", owner: api });
  if (sheet && sheet.isMesh) ctx.interact.set(sheet, { kind: "piano", part: "piano_sheet", owner: api });
  return api;
}
