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
// The window's layers, far to near (blender/lib/lighting_dusk.py backdrop_layers): drawn in this order.
const BACKDROP_ORDER = { city_sky: -5, city_far: -4, city_sea: -3, city_prom: -2, city_near: -1 };

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
  const backdropMat = new Map(); // the backdrop's source material -> its unlit, blended stand-in (shared by the layers)
  const lmIntensity = Math.PI * json.lightmap.max * k;
  const emissiveGain = (json.emissiveGain ?? 1) * k;
  const seen = new Set();
  let nBaked = 0;
  room.traverse((o) => {
    if (!o.isMesh) return;
    if (o.name === "city_static" || o.parent?.name === "city_static") {
      // The window's view (2026-11-12): the sea at sunset in planes at different distances (city_sky, city_far,
      // city_sea, city_prom, city_near) under the city_static empty, one atlas with alpha. Drawn unlit, blended, far
      // to near by renderOrder, all before the window's glass and curtains (renderOrder 0).
      const src = o.material;
      if (!backdropMat.has(src)) {
        const m = new THREE.MeshBasicMaterial({
          map: src.map || src.emissiveMap, fog: false, side: THREE.DoubleSide,
          transparent: true, depthWrite: false, alphaTest: 0.004,
        });
        m.color.setScalar(json.backdropGain ?? 1);
        backdropMat.set(src, m);
        src.dispose(); // its texture lives on in m
      }
      o.material = backdropMat.get(src);
      o.renderOrder = BACKDROP_ORDER[o.name] ?? -6;
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

// Deferred assets (docs/02-architecture.md): GLBs loaded after the room appears, in the room's own frame. The car display
// (2026-11-08, scene/assets/cars.glb) carries its own lightmap from the same dusk rig (blender/components/cars.py),
// written next to the room's as cars-light.json + cars-lightmap.webp, decoded the same way (light = texel * max, times the
// room's exposure). cars_static is one mesh with one palette material (one draw call) and a second UV set for the
// lightmap; a `*_shadow` mesh is a card 1 mm off the wall whose alpha is how much the asset darkens the wall (baked as a
// ratio, so the room's own lightmap stays as it is): drawn black, unlit. The guitars (2026-11-13, scene/assets/guitars.glb)
// have no light file: like guitars 02 and 04 in the room they are lit by the environment only (they lift off later).

export async function loadDeferredLight(THREE, url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error("no " + url);
  const json = await res.json();
  const base = url.slice(0, url.lastIndexOf("/") + 1);
  const lightMap = await new THREE.TextureLoader().loadAsync(base + json.lightmap.file);
  lightMap.flipY = false;
  lightMap.channel = 1;
  lightMap.colorSpace = THREE.SRGBColorSpace;
  return { json, lightMap };
}

// root: the loaded GLB's scene. light: loadDeferredLight's result, or null (environment light only). exposure: the room's
// (room-light.json, or the &exp override). Returns the materials to fade in.
export function applyDeferredLight(THREE, { root, light, exposure }) {
  const mats = [];
  root.traverse((o) => {
    if (!o.isMesh) return;
    const src = o.material;
    if (/_shadow$/.test(o.name)) {
      o.material = new THREE.MeshBasicMaterial({
        color: 0x000000, map: src.map, transparent: true, depthWrite: false,
        polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
      });
      o.renderOrder = 1;
    } else if (light && o.geometry.attributes.uv1 && src.isMeshStandardMaterial) {
      const m = src.clone();
      m.lightMap = light.lightMap;
      m.lightMapIntensity = Math.PI * light.json.lightmap.max * exposure;
      m.onBeforeCompile = (s) => bakedShader(s, THREE);
      m.customProgramCacheKey = () => "baked-dusk";
      o.material = m;
    }
    if (o.material !== src) src.dispose();
    if (!mats.includes(o.material)) mats.push(o.material);
  });
  return mats;
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
