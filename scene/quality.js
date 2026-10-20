// Quality ladder for the room: full / auto / smooth. Pure logic, no Three.js, no DOM.
// desktop.js creates one with createQuality({ dpr, reduce, apply }) and feeds it frame times.
//
//   full    pixel ratio min(dpr, 2), bloom on.
//   smooth  pixel ratio min(dpr, 1), bloom off.
//   auto    starts at full, steps down one rung when the average fps of a ~2 s window is
//           under DOWN_BELOW_FPS, steps back up one rung after UP_AFTER_MS above
//           UP_ABOVE_FPS. Never above full. Rungs: 2 -> 1.5 -> 1 -> 0.75 (only those below
//           the device's own ratio); bloom is on at the top rung and at ratios above 1.
//   With reduce true the room draws only on change, so fps means nothing: auto stays on full.
//
// API: mode, fps (rolling, for the meter), rung ({ pixelRatio, bloom }), frame(dtMs),
//      set(mode), pause(), resume(). apply({ pixelRatio, bloom }) is called on every change,
//      and once when created.

const MAX_PIXEL_RATIO = 2;
const RUNGS = [2, 1.5, 1, 0.75]; // pixel ratios, top to bottom
const SMOOTH_PIXEL_RATIO = 1; // smooth uses min(dpr, this)
const BLOOM_ABOVE_RATIO = 1; // below the top rung, bloom only above this ratio

const SETTLE_MS = 1000; // ignored after start, after any change, after a stall or a pause
const WINDOW_MS = 2000; // one measuring window
const DOWN_BELOW_FPS = 50; // a window under this steps down
const UP_ABOVE_FPS = 58; // windows above this count toward stepping up
const UP_AFTER_MS = 10000; // how long they must add up to (uninterrupted)
const UP_AFTER_MAX_MS = 80000; // wait grows when a step up is undone straight away
const STALL_MS = 1000; // a longer gap between frames is a stall, not a measurement
const METER_MS = 500; // the fps readout averages over this

export const MODES = ["full", "auto", "smooth"];

export function createQuality({ dpr = 1, reduce = false, apply }) {
  const full = Math.min(dpr || 1, MAX_PIXEL_RATIO);
  const rungs = [full, ...RUNGS.filter((r) => r < full)].map((pixelRatio, i) => ({
    pixelRatio,
    bloom: i === 0 || pixelRatio > BLOOM_ABOVE_RATIO,
  }));
  const smooth = { pixelRatio: Math.min(full, SMOOTH_PIXEL_RATIO), bloom: false };

  let mode = "auto";
  let index = 0; // rung used by full and auto
  let rung = rungs[0];
  let paused = false;

  let settle = SETTLE_MS;
  let winTime = 0;
  let winFrames = 0;
  let goodTime = 0;
  let upAfter = UP_AFTER_MS;
  let justStepped = 0; // 1 after a step up until the next window, so a step back down is spotted
  let meterTime = 0;
  let meterFrames = 0;
  let fps = 0;

  function restartMeasuring() {
    settle = SETTLE_MS;
    winTime = 0;
    winFrames = 0;
    goodTime = 0;
  }

  function show(next) {
    rung = next;
    restartMeasuring();
    apply({ pixelRatio: rung.pixelRatio, bloom: rung.bloom });
  }

  function step(by) {
    const next = Math.min(rungs.length - 1, Math.max(0, index + by));
    if (next === index) return;
    index = next;
    show(rungs[index]);
  }

  function onWindow(avg, ms) {
    if (avg < DOWN_BELOW_FPS) {
      // Went down right after going up: the higher rung is too heavy, wait longer next time.
      if (justStepped) upAfter = Math.min(upAfter * 2, UP_AFTER_MAX_MS);
      justStepped = 0;
      goodTime = 0;
      step(1);
      return;
    }
    justStepped = 0;
    if (avg > UP_ABOVE_FPS) {
      goodTime += ms;
      if (goodTime >= upAfter && index > 0) {
        step(-1);
        justStepped = 1;
      }
    } else {
      goodTime = 0;
    }
  }

  const api = {
    get mode() { return mode; },
    get fps() { return fps; },
    get rung() { return { pixelRatio: rung.pixelRatio, bloom: rung.bloom }; },

    // dtMs: real time since the previous rendered frame.
    frame(dtMs) {
      if (!(dtMs > 0)) return;
      if (dtMs > STALL_MS) { restartMeasuring(); meterTime = 0; meterFrames = 0; return; }

      meterTime += dtMs;
      meterFrames++;
      if (meterTime >= METER_MS) {
        fps = (meterFrames * 1000) / meterTime;
        meterTime = 0;
        meterFrames = 0;
      }

      if (mode !== "auto" || reduce || paused) return;
      if (settle > 0) { settle -= dtMs; return; }
      winTime += dtMs;
      winFrames++;
      if (winTime >= WINDOW_MS) {
        const ms = winTime;
        const avg = (winFrames * 1000) / winTime;
        winTime = 0;
        winFrames = 0;
        onWindow(avg, ms);
      }
    },

    set(next) {
      if (!MODES.includes(next) || next === mode) return;
      mode = next;
      upAfter = UP_AFTER_MS;
      justStepped = 0;
      if (mode === "smooth") show(smooth);
      else { index = 0; show(rungs[0]); }
    },

    // The loop stopped (tab hidden): measure nothing until resume(), then settle again.
    pause() { paused = true; },
    resume() {
      paused = false;
      restartMeasuring();
      meterTime = 0;
      meterFrames = 0;
    },
  };

  apply({ pixelRatio: rung.pixelRatio, bloom: rung.bloom });
  return api;
}
