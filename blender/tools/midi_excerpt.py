"""Cut a short excerpt from a MIDI file into the note data the room's piano plays (2026-11-15, objects/piano.js).

    /opt/anaconda3/bin/python3 blender/tools/midi_excerpt.py <file.mid> info
    /opt/anaconda3/bin/python3 blender/tools/midi_excerpt.py <file.mid> cut <bars> [tempo x] > notes.json
    /opt/anaconda3/bin/python3 blender/tools/midi_excerpt.py <file.mid> bars <first> <last>      one line per bar
    <bars>: ranges played one after another, "1-11,35". UNTIL=<s> ends it there. PICKUP=<ticks> when the file starts with a pickup bar
    (LilyPond's MIDI puts it at tick 0, so bar 1 starts at the pickup's length).

Standard library only (a small Standard MIDI File reader: format 0 or 1, tempo map, note on/off, sustain pedal).
Bars are counted from the time signature in the file, bar 1 the first full bar (a pickup is bar 0). "cut" writes
{"notes": [[start s, midi, length s, velocity 0..1], ...], "seconds": total}, played as a pianist would (perform():
pedal, voicing, phrasing, a ritardando; env PEDAL, VOICE, ARCH, RIT); times start at 0, `tempo x` scales the speed.
The MIDI files are in blender/assets/piano-midi/ (downloaded 2026-11-15 from the Mutopia Project; git ignores them).
"""
import json
import struct
import sys


def read_var(b, i):
    v = 0
    while True:
        c = b[i]
        i += 1
        v = (v << 7) | (c & 0x7F)
        if not c & 0x80:
            return v, i


def parse(path):
    b = open(path, "rb").read()
    assert b[:4] == b"MThd"
    fmt, ntr, div = struct.unpack(">HHH", b[8:14])
    i = 8 + struct.unpack(">I", b[4:8])[0]
    events = []                                          # (tick, kind, data)
    for track in range(ntr):
        assert b[i:i + 4] == b"MTrk"
        n = struct.unpack(">I", b[i + 4:i + 8])[0]
        j, end, t, run = i + 8, i + 8 + n, 0, None
        while j < end:
            dt, j = read_var(b, j)
            t += dt
            s = b[j]
            if s == 0xFF:
                typ, ln = b[j + 1], None
                ln, k = read_var(b, j + 2)
                data = b[k:k + ln]
                if typ == 0x51:
                    events.append((t, "tempo", int.from_bytes(data, "big")))
                elif typ == 0x58:
                    events.append((t, "sig", (data[0], 2 ** data[1])))
                j = k + ln
                continue
            if s in (0xF0, 0xF7):
                ln, k = read_var(b, j + 1)
                j = k + ln
                continue
            if s & 0x80:
                run = s
                j += 1
            st = run & 0xF0
            if st in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                d1, d2 = b[j], b[j + 1]
                j += 2
                if st == 0x90 and d2 > 0:
                    events.append((t, "on", (d1, d2, track)))
                elif st == 0x80 or (st == 0x90 and d2 == 0):
                    events.append((t, "off", (d1, track)))
                elif st == 0xB0 and d1 == 64:
                    events.append((t, "pedal", d2 >= 64))
            else:
                j += 1
        i = end
    events.sort(key=lambda e: (e[0], {"tempo": 0, "sig": 0, "pedal": 1, "off": 2, "on": 3}[e[1]]))
    return div, events


def timeline(div, events):
    """tick -> seconds, the notes as [start tick, end tick, midi, vel, track], pedal-extended, and the bar length."""
    tempos = [(0, 500000)] + [(t, v) for t, k, v in events if k == "tempo"]
    sig = next((v for t, k, v in events if k == "sig"), (4, 4))

    def sec(tick):
        s, last_t, last_v = 0.0, 0, tempos[0][1]
        for t, v in tempos[1:]:
            if t >= tick:
                break
            s += (t - last_t) * last_v / div / 1e6
            last_t, last_v = t, v
        return s + (tick - last_t) * last_v / div / 1e6
    open_, notes, pedal, held = {}, [], False, []
    for t, k, v in events:
        if k == "on":
            key = (v[0], v[2])
            if key in open_:
                st, vel = open_.pop(key)
                notes.append([st, t, v[0], vel, v[2]])
            open_[key] = (t, v[1])
        elif k == "off" and v in open_:
            st, vel = open_.pop(v)
            n = [st, t, v[0], vel, v[1]]
            notes.append(n)
            if pedal:
                held.append(n)
        elif k == "pedal":
            if not v:
                for n in held:
                    n[1] = max(n[1], t)
                held = []
            pedal = v
    bar = div * 4 * sig[0] // sig[1]
    return sec, notes, bar, sig


def main():
    path, cmd = sys.argv[1], sys.argv[2]
    div, ev = parse(path)
    sec, notes, bar, sig = timeline(div, ev)
    import os
    first = min(n[0] for n in notes)
    pickup = int(os.environ.get("PICKUP", "0"))
    origin = first + pickup                                   # bar 1 starts here
    if cmd == "info":
        last = max(n[1] for n in notes)
        print(json.dumps(dict(division=div, sig=sig, bar_ticks=bar, notes=len(notes), first_tick=first,
                              pickup_ticks=pickup, bars=round((last - origin) / bar, 2),
                              seconds=round(sec(last) - sec(first), 1),
                              tempos=[(t, round(6e7 / v, 1)) for t, k, v in ev if k == "tempo"][:6])))
        return
    NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    name = lambda m: NAMES[m % 12] + str(m // 12 - 1)
    start = lambda b: origin + (b - 1) * bar if b >= 1 else first
    if cmd == "bars":
        for b in range(int(sys.argv[3]), int(sys.argv[4]) + 1):
            ns = sorted((n for n in notes if start(b) <= n[0] < start(b + 1)), key=lambda n: n[0])
            print(b, " ".join(name(n[2]) for n in ns)[:150])
        return
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    # the right hand: the track with the higher notes on average
    tracks = {}
    for n in notes:
        tracks.setdefault(n[4], []).append(n[2])
    rh = max(tracks, key=lambda k: sum(tracks[k]) / len(tracks[k]))
    data, bars, at = [], [], 0.0
    for rng in sys.argv[3].split(","):
        b0, b1 = (int(x) for x in rng.split("-")) if "-" in rng else (int(rng), int(rng))
        t0, t1 = start(b0), start(b1 + 1)
        s0 = sec(t0)
        last = rng == sys.argv[3].split(",")[-1]
        for b in range(max(1, b0), b1 + 1):
            bars.append(at + (sec(start(b)) - s0) / speed)
        for a, e, m, v, tr in sorted(n for n in notes if t0 <= n[0] < t1):
            end = e if last else min(e, t1)
            data.append([at + (sec(a) - s0) / speed, m, max(0.08, sec(end) - sec(a)) / speed, v / 127, "r" if tr == rh else "l"])
        at += (sec(t1) - s0) / speed
    bar_s = sec(bar) / speed
    until = float(os.environ.get("UNTIL", "0"))              # end the excerpt here (seconds), before the shaping
    if until:
        data = [n for n in data if n[0] < until]
        bars = [b for b in bars if b < until]
        at = until
    data = perform(data, bars, bar_s, at)
    tail = max(n[0] + n[2] for n in data)
    print(json.dumps(dict(notes=data, seconds=round(max(at, tail), 2), seconds_per_bar=bar_s)))


def perform(data, bars, bar_s, total):
    """The score as a pianist plays it (2026-11-16, the owner on the first renders: "Dynamics / balance", "Pedal / note
    lengths"; the files carry neither). Env:
      PEDAL   half: change at every bar and half bar (Bach); bass:<s>: down at each bass note of the left hand
              (below E3, the lowest at its moment), up at the next one or after <s> seconds (Beethoven, Chopin);
              none. Notes struck while the pedal is down ring until it lifts; the last chord rings on.
      VOICE   melody: the right hand sings over the left (Beethoven, Chopin); even: both hands even, the bass of each
              half bar and the top note of each beat a little stronger (Bach).
      ARCH    the piece's overall shape, fraction:level pairs (default 0:0.86,0.55:1,0.85:1.02,1:0.84).
      RIT     seconds of ritardando at the end (default 2.5), slowing to about 18 % at the last note.
      CHORD   a hand's chords of three notes or more are struck this much harder (default 1: the sforzando chords
              of the Moonlight's finale, 1.3).
    Velocities are 0..1; the piano code turns them into loudness and tone (softer is darker)."""
    import os
    import random
    rnd = random.Random(846)
    pedal = os.environ.get("PEDAL", "none")
    voice = os.environ.get("VOICE", "melody")
    arch = [tuple(float(x) for x in p.split(":")) for p in os.environ.get("ARCH", "0:0.86,0.55:1,0.85:1.02,1:0.84").split(",")]
    rit = float(os.environ.get("RIT", "2.5"))
    chord = float(os.environ.get("CHORD", "1"))
    data.sort(key=lambda n: (n[0], n[1]))
    # pedal: change points, then each note held to its window's lift
    lifts = []                                                 # (down, up)
    if pedal == "half":
        pts = sorted(set([round(b, 4) for b in bars] + [round(b + bar_s / 2, 4) for b in bars]))
        lifts = [(a, b - 0.04) for a, b in zip(pts, pts[1:])]
    elif pedal.startswith("bass"):
        mx = float(pedal.split(":")[1]) if ":" in pedal else 2.0
        downs = []
        for n in data:
            if n[4] == "l" and n[1] < 52 and not any(o[4] == "l" and o[1] < n[1] and abs(o[0] - n[0]) < 0.03 for o in data):
                if not downs or n[0] - downs[-1] > 0.05:
                    downs.append(n[0])
        lifts = [(a, min(b - 0.04, a + mx)) for a, b in zip(downs, downs[1:] + [total + 9])]
    for n in data:
        w = next(((a, b) for a, b in lifts if a - 0.002 <= n[0] < b), None)
        if w:
            n[2] = max(n[2], w[1] - n[0])
    last = max(n[0] for n in data)
    for n in data:
        if n[0] >= last - 0.05:
            n[2] = max(n[2], 3.0)                               # the last chord rings
    # dynamics
    def level(t):
        f = t / total if total else 0
        for (f0, v0), (f1, v1) in zip(arch, arch[1:]):
            if f0 <= f <= f1:
                return v0 + (v1 - v0) * (f - f0) / (f1 - f0 or 1)
        return arch[-1][1]
    beat = bar_s / 2 if voice == "even" else bar_s / 4
    for n in data:
        s, m, ln, v, hand = n
        near = [o[1] for o in data if o[4] == hand and abs(o[0] - s) < 1.6]
        lo, hi = min(near), max(near)
        if voice == "melody":
            base = 0.72 if hand == "r" else 0.46
            if hand == "r":
                base *= 0.86 + 0.26 * ((m - lo) / (hi - lo) if hi > lo else 0.5)  # the line rises and falls
            elif not any(o[4] == "l" and o[1] < m and abs(o[0] - s) < 0.03 for o in data) and m < 52:
                base *= 1.12                                    # the bass note of the left hand
        else:
            base = 0.5
            if hand == "l":
                base = 0.6 if m == min(o[1] for o in data if o[4] == "l" and abs(o[0] - s) < bar_s / 2) else 0.53
            win = [o for o in data if o[4] == "r" and int(o[0] / beat) == int(s / beat)]
            if hand == "r" and win and m == max(o[1] for o in win):
                base += 0.06                                    # the line on top of the broken chord
        accent = 1.07 if any(abs(s - b) < 0.02 for b in bars) else 1.03 if any(abs(s - b - bar_s / 2) < 0.02 for b in bars) else 1.0
        if chord != 1.0 and sum(1 for o in data if o[4] == hand and abs(o[0] - s) < 0.012) >= 3:
            accent *= chord
        n[3] = max(0.15, min(1.0, base * accent * level(s) * (1 + rnd.uniform(-0.03, 0.03))))
    # the ending slows: time stretched by up to 18 % over the last RIT seconds
    t_r = last - rit
    warp = lambda t: t + (0.18 * (t - t_r) ** 2 / (2 * rit) if t > t_r and rit > 0 else 0)
    out = []
    for s, m, ln, v, hand in data:
        s2 = warp(s)
        out.append([round(s2, 3), m, round(warp(s + ln) - s2, 3), round(v, 2)])
    return out


main()
