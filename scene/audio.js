// The room's sound (2026-11-15, with the piano). One Web Audio context and one master gain; objects get them through
// ctx.audio() (objects/CONTRACT.md). Owner, 2026-11-15: "On when they play": nothing makes a sound until the
// visitor plays something. The first ctx.audio() call, made inside a click or a key, starts the context (browsers
// allow it only then) and shows a Sound button in the room's bar that mutes and unmutes. Muted, ctx.audio() is null
// and the objects play silently (keys still move). Hidden tab: the context is suspended. Nothing is remembered.

const FADE = 0.06; // seconds: mute and unmute ramps

export function createAudio({ bar, labels, say }) {
  const AC = window.AudioContext || window.webkitAudioContext;
  let ac = null, out = null, muted = false, button = null;

  function showButton() {
    if (button || !bar) return;
    button = document.createElement("button");
    button.type = "button";
    button.className = "room-sound";
    const paint = () => {
      button.setAttribute("aria-pressed", String(!muted));
      button.textContent = (muted ? "\u{1F507} " : "\u{1F50A} ") + (labels.sound || "Sound");
      button.title = muted ? labels.soundOn || "Turn sound on" : labels.soundOff || "Turn sound off";
    };
    button.addEventListener("click", () => {
      muted = !muted;
      if (out) out.gain.setTargetAtTime(muted ? 0 : 1, ac.currentTime, FADE / 3);
      if (!muted && ac && ac.state === "suspended") ac.resume();
      paint();
      say(muted ? labels.soundOffSaid || "Sound off" : labels.soundOnSaid || "Sound on");
    });
    paint();
    bar.append(button);
  }

  document.addEventListener("visibilitychange", () => {
    if (!ac) return;
    if (document.hidden) ac.suspend();
    else if (!muted) ac.resume();
  });

  return {
    // ctx.audio(): { ctx, out } while sound is on, else null. The first call starts it (inside a click or a key).
    get() {
      if (muted || !AC) return null;
      if (!ac) {
        try {
          ac = new AC({ latencyHint: "interactive" });
          out = ac.createGain();
          out.connect(ac.destination);
        } catch { return null; }
      }
      if (ac.state === "suspended") ac.resume();
      showButton();
      return { ctx: ac, out };
    },
    get muted() { return muted; },
    dispose() { if (button) button.remove(); if (ac) ac.close(); },
  };
}
