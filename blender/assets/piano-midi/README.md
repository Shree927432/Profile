# Piano MIDI files (downloaded 2026-11-16 from the Mutopia Project, mutopiaproject.org)

- wtk1-prelude1.mid: J. S. Bach, Prelude in C major, BWV 846. Public domain.
- fur_Elise_WoO59.mid: L. van Beethoven, Für Elise, WoO 59. Public domain.
- chopin_nocturne_op9_n2.mid: F. Chopin, Nocturne Op. 9 No. 2. CC BY-SA 3.0 (the excerpt in content/piano.json is
  under the same licence; the credits page names the Mutopia Project).

Git ignores the .mid files. blender/tools/midi_excerpt.py cuts the excerpts the room's piano plays:
  PY=/opt/anaconda3/bin/python3; T=blender/tools/midi_excerpt.py; M=blender/assets/piano-midi
  $PY $T $M/wtk1-prelude1.mid cut 1-11,35 1.2
  PICKUP=192 $PY $T $M/fur_Elise_WoO59.mid cut 0-23        (then cut before the B4 C5 D5 lead-in, about 30 s)
  PICKUP=192 $PY $T $M/chopin_nocturne_op9_n2.mid cut 0-4

Added 2026-11-16: moonlight/moonlight-mids.zip (9.5 KB, three movements): L. van Beethoven, Sonata No. 14 "Moonlight",
Op. 27 No. 2. CC BY-SA 2.5. The room plays the third movement's exposition (moonlight3.mid, bars 1 to 64 and the
downbeat of bar 65); blender/tools/piano_pieces.py holds every piece's settings and writes content/piano.json.
