"""Write content/piano.json, the pieces the room's piano plays (2026-11-16), from the Mutopia MIDI files.

    /opt/anaconda3/bin/python3 blender/tools/piano_pieces.py

Each piece: blender/tools/midi_excerpt.py cuts the bars and plays them as a pianist would (pedal, voicing, phrasing,
a ritardando). The settings per piece are here; the MIDI files are in blender/assets/piano-midi/ (git-ignored).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MIDI = os.path.join(REPO, "blender", "assets", "piano-midi")
TOOL = os.path.join(HERE, "midi_excerpt.py")
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

PIECES = [
    dict(id="bach", file="wtk1-prelude1.mid", bars="1-11,35", speed="1.2",
         env=dict(PEDAL="half", VOICE="even", ARCH="0:0.82,0.45:1,0.8:1.04,1:0.8", RIT="3"),
         title="Prelude in C major, BWV 846", composer="J. S. Bach", era="Baroque", year=1722,
         excerpt="bars 1 to 11 and the last chord, a little quicker than the file", licence="Public domain"),
    # the exposition (bars 1 to 64) and the chord that resolves it (the downbeat of bar 65); the file has no tempo: 168
    dict(id="moonlight3", file="moonlight/moonlight3.mid", bars="1-65", speed="2.8",
         env=dict(PEDAL="none", VOICE="melody", CHORD="1.22", ARCH="0:0.6,0.3:0.7,0.6:0.74,0.9:0.78,1:0.72", RIT="1.2"),   # a dense piece: lower, to sit with the others
         until_bar=65,
         title="Moonlight Sonata, Op. 27 No. 2, III. Presto agitato", composer="Ludwig van Beethoven", era="Classical", year=1801,
         excerpt="the exposition (bars 1 to 64) and its resolving chord, at 168 to the minute", licence="CC BY-SA 2.5"),
    dict(id="elise", file="fur_Elise_WoO59.mid", bars="0-23", speed="1",
         env=dict(PICKUP="192", PEDAL="bass:1.2", VOICE="melody", ARCH="0:0.8,0.3:0.92,0.55:1,0.8:0.95,1:0.78", RIT="2"),
         until=("B4", "C5", "D5"),                     # stop before the lead-in that brings the middle phrase round again
         title="Für Elise, WoO 59", composer="Ludwig van Beethoven", era="Classical", year=1810,
         excerpt="the opening theme, its middle phrase and its return", licence="Public domain"),
    dict(id="nocturne", file="chopin_nocturne_op9_n2.mid", bars="0-4", speed="1",
         env=dict(PICKUP="192", PEDAL="bass:2.0", VOICE="melody", ARCH="0:0.84,0.5:1,0.75:1.06,1:0.82", RIT="2.5"),
         title="Nocturne in E-flat major, Op. 9 No. 2", composer="Frédéric Chopin", era="Romantic", year=1832,
         excerpt="the pickup and the opening four bars", licence="CC BY-SA 3.0"),
]


def cut(p, extra=None):
    env = {**os.environ, **p["env"], **(extra or {})}
    out = subprocess.run([sys.executable, TOOL, os.path.join(MIDI, p["file"]), "cut", p["bars"], p["speed"]],
                         env=env, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def main():
    pieces = []
    for p in PIECES:
        extra = None
        if p.get("until"):                              # find where the excerpt ends, then cut there
            raw = cut(p, dict(PEDAL="none", RIT="0"))["notes"]
            name = lambda m: NAMES[m % 12] + str(m // 12 - 1)
            seq = [name(n[1]) for n in raw]
            k = next(i for i in range(len(seq) - 2) if tuple(seq[i:i + 3]) == p["until"] and raw[i][0] > 20)
            extra = dict(UNTIL=str(raw[k][0] - 0.01))
        if p.get("until_bar"):                          # end on that bar's downbeat chord
            raw = cut(p, dict(PEDAL="none", RIT="0", CHORD="1"))
            first = int(p["bars"].split("-")[0])
            bar_s = raw["seconds_per_bar"]
            extra = dict(UNTIL=str((p["until_bar"] - first) * bar_s + 0.02))
        d = cut(p, extra)
        pieces.append(dict(id=p["id"], title=p["title"], composer=p["composer"], era=p["era"], year=p["year"],
                           excerpt=p["excerpt"], source="Mutopia Project", licence=p["licence"],
                           seconds=d["seconds"], notes=d["notes"]))
        v = [n[3] for n in d["notes"]]
        print(f"{p['id']}: {len(d['notes'])} notes, {d['seconds']} s, velocity {min(v)}..{max(v)}")
    out = dict(note="The pieces the room's piano plays (scene/objects/piano.js), cut from the Mutopia Project's MIDI files and "
                    "shaped (pedal, voicing, phrasing) by blender/tools/piano_pieces.py and midi_excerpt.py. Each note: "
                    "[start s, MIDI note, length s, velocity 0..1]. Served as /piano.json, fetched on the first play.",
               pieces=pieces)
    s = json.dumps(out, ensure_ascii=False, separators=(",", ":")).replace('"pieces":[', '"pieces":[\n').replace('},{"id"', '},\n{"id"')
    with open(os.path.join(REPO, "content", "piano.json"), "w") as f:
        f.write(s + "\n")


main()
