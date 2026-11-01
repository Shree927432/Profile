# Plant models (downloaded 2026-11-01)

Free models that replace the blockout's plant stand-ins (owner: "Plants first", from
`video-local/viewer/props-candidates.html`). The full originals stay here untouched and go into the
Blender file as they are; only the web version (room.glb) is cut down and its textures shrunk (owner:
"keep the heavy models for the Blender file. Don't cut down on that"). The files are git-ignored (too big);
download them again from the links below into the folders named.

| Folder | Replaces | Source | Author | Licence | Credit needed |
|---|---|---|---|---|---|
| `potted_plant_04/` (glTF, 8K textures) | the small desk plant | [Poly Haven: Potted Plant 04](https://polyhaven.com/a/potted_plant_04) | Poly Haven | CC0 | no |
| `monstera/` | the sill plant (`obj_plant`) | [Sketchfab: Monstera Deliciosa Potted Mid-Century](https://sketchfab.com/3d-models/1ab9bf841df04c07b1819be596327629) | ChubbyPanda | CC BY 4.0 | yes, on the site's credits |
| `snake_plant/` | (no longer used, 2026-11-01) | [Sketchfab: Snake plant In Pot](https://sketchfab.com/3d-models/68b8acaeb29e402ea4dc7c981cb5b497) | FranklySketch | CC BY 4.0 | no longer needed: not in the room or the Blender file |

The Sketchfab models came as .glb (Download 3D Model, glTF): `monstera/monstera_deliciosa_potted_mid-century_plant.glb` (88 MB), `snake_plant/snake_plant_in_pot.glb` (5.8 MB).

**Snake plant, 2026-11-01:** the scan is no longer used in the room. The owner: "[snake] plant is not looking good, and
it is really looking bad in rendered down version. Also, it is not going with the theme as well." It is replaced by our
own model in `blender/components/plants.py` (`snake_plant()`: a Sansevieria 'Laurentii' with a code-painted leaf pattern in
a matte white pot). Nothing of the scan ships in the site or the .blend, so its CC BY credit is no longer needed. The
file stays here for reference.
