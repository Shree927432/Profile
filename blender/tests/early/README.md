# The first Blender tests (2026-10-21)

Kept for the build history. Not part of the room build.

- `piano_test.py`: a box piano with 88 keys named by note. It proved the names survive
  the GLB export. Run with Blender headless; writes next to the script.
- `turntable.py`: a 4 s turntable of that piano (opens `piano-test.blend`).
- `build_sequence.py`: the first build clip, wireframe to clay to lit
  (`-- <wire|clay|final> <first> <last>`).

They write into `video-local/` paths relative to the old test folder. The renders they
made are in `video-local/footage/2026-10-21-blender-test/` (local only). The owner
compared them with Felix's making-of and asked for the quality test that followed.
