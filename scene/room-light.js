// The dusk light for the GLB room (?room&glb), 2026-11-01. Felix's method: the light is baked in Blender's Cycles
// (blender/lib/lighting_dusk.py), the browser only draws it. desktop.js calls loadRoomLight() while the GLB loads,
// then applyRoomLight() once the room is in the scene (after batch.js), and createBloom() on desktop.
//
//   room-light.json   written by blender/tools/encode_dusk.py: the files and the numbers that decode them
//   lightmap.webp     one atlas, the Cycles DIFFUSE bake (direct + indirect, no colour) of every static mesh that
//                     never moves; meshes that carry it have a second UV set (uv1). Stored as sRGB 8-bit of
//                     light / max, so light = texel * max.
//   env.webp          an equirect of the room at dusk from above the desk (same encoding), through PMREM: the
//                     reflections on metal and glass, and the only light on the parts that move (keys, pads, knobs,
//                     faders, fans, drawers, frames, panels, chair, guitars), so no baked shadow slides with them.
//
// Baked materials keep their palette colour, roughness and metal (MeshStandardMaterial): the lightmap is their
// diffuse light, the environment their reflections only (its diffuse share is cut in the shader, else the room
// would be lit twice). No live three.js lights in the GLB room. EXPOSURE scales every light source together (the
// lightmap, the environment, emissive parts, the window's backdrop), so the posts screen, which ignores light,
// keeps its own colours. The backdrop (city_static) is drawn unlit.

const LIGHT_URL = "/scene/assets/dusk/room-light.json";

export async function loadRoomLight(THREE) {
  const res = await fetch(LIGHT_URL);
  if (!res.ok) throw new Error("no " + LIGHT_URL);
  const json = await res.json();
  const base = LIGHT_URL.slice(0, LIGHT_URL.lastIndexOf("/") + 1);
  const loader = new THREE.TextureLoader();
  const [lightMap, env] = await Promise.all([
    loader.loadAsync(base + json.lightmap.file),
    loader.loadAsync(base + json.env.file),
  ]);
  lightMap.flipY = false; // glTF UV convention, as the bake was written
  lightMap.channel = 1; // the second UV set (TEXCOORD_1)
  lightMap.colorSpace = THREE.SRGBColorSpace;
  env.mapping = THREE.EquirectangularReflectionMapping;
  env.colorSpace = THREE.SRGBColorSpace;
  return { json, lightMap, env };
}

// The environment's diffuse share is dropped for baked materials (the lightmap carries their diffuse light).
function bakedShader(shader, THREE) {
  shader.fragmentShader = shader.fragmentShader.replace(
    "#include <lights_fragment_maps>",
    THREE.ShaderChunk.lights_fragment_maps.replace("iblIrradiance += getIBLIrradiance( geometryNormal );", "")
  );
}

export function applyRoomLight(THREE, { renderer, scene, room, light, exposure }) {
  const { json, lightMap, env } = light;
  const k = exposure ?? json.exposure;
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromEquirectangular(env).texture;
  scene.environmentIntensity = json.env.max * k * (json.env.gain ?? 1);
  env.dispose();
  pmrem.dispose();

  const baked = new Map(); // source material -> baked clone (one atlas, so clones can be shared)
  const lmIntensity = Math.PI * json.lightmap.max * k;
  const emissiveGain = (json.emissiveGain ?? 1) * k;
  const seen = new Set();
  let nBaked = 0;
  room.traverse((o) => {
    if (!o.isMesh) return;
    if (o.name === "city_static" || o.parent?.name === "city_static") {
      const src = o.material;
      o.material = new THREE.MeshBasicMaterial({ map: src.emissiveMap || src.map, fog: false, side: THREE.DoubleSide });
      o.material.color.setScalar(json.backdropGain ?? 1);
      src.dispose();
      return;
    }
    if (o.geometry.attributes.uv1 && o.material.isMeshStandardMaterial) {
      let m = baked.get(o.material);
      if (!m) {
        m = o.material.clone();
        m.lightMap = lightMap;
        m.lightMapIntensity = lmIntensity;
        m.onBeforeCompile = (s) => bakedShader(s, THREE);
        m.customProgramCacheKey = () => "baked-dusk";
        baked.set(o.material, m);
      }
      o.material = m;
      nBaked++;
    }
    const m = o.material;
    if (seen.has(m)) return;
    seen.add(m);
    if (m.emissive && (m.emissive.r || m.emissive.g || m.emissive.b)) m.emissiveIntensity *= emissiveGain;
  });
  return { baked: nBaked };
}

// Bloom on desktop: RenderPass -> UnrealBloomPass -> OutputPass (tone mapping and sRGB move into OutputPass).
// The render target keeps 4x MSAA. Only parts brighter than the threshold glow: the emissives, the sun's patch.
export async function createBloom(THREE, { renderer, scene, camera, strength, radius, threshold }) {
  const [{ EffectComposer }, { RenderPass }, { UnrealBloomPass }, { OutputPass }] = await Promise.all([
    import("three/addons/postprocessing/EffectComposer.js"),
    import("three/addons/postprocessing/RenderPass.js"),
    import("three/addons/postprocessing/UnrealBloomPass.js"),
    import("three/addons/postprocessing/OutputPass.js"),
  ]);
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const rt = new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, rt);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(size.x, size.y), strength, radius, threshold);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  return {
    composer,
    bloom,
    setSize(w, h) { composer.setSize(w, h); },
    setPixelRatio(pr) { composer.setPixelRatio(pr); },
    render() { composer.render(); },
  };
}
