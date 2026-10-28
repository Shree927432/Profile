# Chair brief (Herman Miller Aeron, Size B, Mineral, polished base)

Started 2026-10-28 on Fable 5.1 (designer agent), stopped the same day before any file was written. Give this
whole brief to the designer agent (Fable, per the owner's choice) with a 90-minute box.

Build the mesh chair as an exact replica in shape and finish. References: `docs/moodboard/local/ai-lab/25-chair/`
(SOURCES.md has the official Size B numbers: 686 W x 1044 H overall, seat depth 432, mid seat height about 460,
arms about 215 above the seat, seat width about 514, back about 530; MODELS.md: no usable free Aeron, build from
scratch; photos: front, back, side, both three-quarters, size guides, arm diagrams, details sheet; the owner wants
the POLISHED base). The owner's room photo `docs/moodboard/local/ai-desk-reference-1.jpg` shows it in context.

What makes it read as an Aeron: the wedge back frame (wider at the top) with the mesh across it and its curve in
side view; the Y-shaped PostureFit SL on the back; the mesh seat with the waterfall front edge; polished arm
stems with pale pads and knobs; the tilt mechanism and levers under the seat; the slim tapered polished five-star
base, cylinder and black casters; the 8Z Pellicle mesh, pale grey, see-through (rich: alpha or procedural weave
with a sheen; lite: an alpha-tested weave texture, alphaMode MASK, checked in three.js).

Pipeline as the approved components (`blender/components/desktop.py` and `arms.py` are the patterns): new script
`blender/components/chair.py` with the stages outline, build, stills, compare, closeups, export; outline check
about 15 minutes in (gate 0.96: front, side, back, three-quarter); detail; every-angle compare (0.98 or
EXPLAINED); photo-vs-model sheet; close-up pairs (back frame and weave, the Y, an arm and knob, the seat front
edge, the mechanism, the base and a caster, the logo spot); ONE full review round; export chair-rich.glb and
chair-lite.glb (lite about 8,000 triangles, atlas plus ORM, the weave as a small tiling alpha texture). Mesh
names chair_seat, chair_back, chair_back_mesh, chair_arm_l/_r, chair_base, chair_cylinder, chair_caster_01..05,
chair_mech, chair_brand, and an empty chair_swivel at the cylinder so the site can turn it.

Brand name: content/room-brands.json key "chair": "kalder" (lowercase like the real mark, Montserrat SemiBold),
printed with blender/lib/brands.py at the real logo's spot; if no photo shows a logo, place none and say so.

Room: place it in `blender/design/room_v3_component_test.py` at plan v3's SEAT facing the desk, replacing the
stand-in; run the room test default once; propose position changes in the report, don't edit plan_v3.py.

Rules: Blender headless always; EEVEE to iterate, Cycles once at the end via renderqueue; check `pmset -g batt`
(stop under 20 % on battery); footage to `video-local/footage/2026-10-28-components/chair/` with a PROGRESS.md
line per stage; never overwrite other dated footage folders; never import another component's *_render.py; no
downloads; don't commit or edit docs, content or plan_v3.py. Report: angles and IoU, review fixes, sizes and
triangles, mesh names, logo spot, placement, sheet paths, what went wrong.
