// Serves the repo's scene/ folder at /scene/ in dev and copies it into dist/ on
// build, so the home page can load /scene/boot.js without moving scene/ under
// public/. scene/ stays where docs/02-architecture.md puts it.
//
// Three.js without a bundler: the browser never sees node_modules. These URLs are
// mapped (dev) and copied (build) from the installed package, and the home page's
// import map points "three" and "three/addons/" at them:
//   /scene/vendor/three/three.module.js   <- three/build/three.module.js (+ three.core.js, which it imports)
//   /scene/vendor/three/addons/<path>     <- three/examples/jsm/<path>   (only the folders in ADDON_DIRS)
import { cp, mkdir, stat } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const MIME = {
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.glb': 'model/gltf-binary',
  '.gltf': 'model/gltf+json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ktx2': 'image/ktx2',
  '.mp3': 'audio/mpeg',
  '.ogg': 'audio/ogg',
  '.wav': 'audio/wav',
  '.md': 'text/markdown; charset=utf-8',
};

const VENDOR = '/scene/vendor/three/';
const BUILD_FILES = ['three.module.js', 'three.core.js'];
// Addon folders the room needs: orbit controls, EffectComposer + passes (bloom, output), their shaders.
const ADDON_DIRS = ['controls', 'postprocessing', 'shaders'];

// Maps a /scene/vendor/three/... URL to a file inside node_modules/three, or null.
function vendorFile(threeDir, rel) {
  if (BUILD_FILES.includes(rel)) return path.join(threeDir, 'build', rel);
  if (rel.startsWith('addons/')) {
    const sub = path.normalize(rel.slice('addons/'.length));
    if (sub.startsWith('..') || !ADDON_DIRS.includes(sub.split(path.sep)[0])) return null;
    return path.join(threeDir, 'examples', 'jsm', sub);
  }
  return null;
}

export default function sceneFiles() {
  let sceneDir;
  let threeDir;
  return {
    name: 'scene-files',
    hooks: {
      'astro:config:setup': ({ config, updateConfig }) => {
        sceneDir = path.join(fileURLToPath(config.root), 'scene');
        threeDir = path.join(fileURLToPath(config.root), 'node_modules', 'three');
        updateConfig({
          vite: {
            plugins: [
              {
                name: 'scene-files-dev',
                configureServer(server) {
                  server.middlewares.use(async (req, res, next) => {
                    const url = (req.url || '').split('?')[0];
                    if (!url.startsWith('/scene/')) return next();
                    let file;
                    if (url.startsWith(VENDOR)) {
                      file = vendorFile(threeDir, decodeURIComponent(url.slice(VENDOR.length)));
                      if (!file) return next();
                    } else {
                      const rel = path.normalize(decodeURIComponent(url.slice('/scene/'.length)));
                      if (rel.startsWith('..')) return next();
                      file = path.join(sceneDir, rel);
                    }
                    try {
                      const s = await stat(file);
                      if (!s.isFile()) return next();
                    } catch {
                      return next();
                    }
                    res.setHeader('Content-Type', MIME[path.extname(file)] || 'application/octet-stream');
                    createReadStream(file).pipe(res);
                  });
                },
              },
            ],
          },
        });
      },
      'astro:build:done': async ({ dir, logger }) => {
        const out = path.join(fileURLToPath(dir), 'scene');
        await cp(sceneDir, out, {
          recursive: true,
          filter: (src) => !src.endsWith('.md'),
        });
        const vendorOut = path.join(out, 'vendor', 'three');
        await mkdir(path.join(vendorOut, 'addons'), { recursive: true });
        for (const f of BUILD_FILES) await cp(path.join(threeDir, 'build', f), path.join(vendorOut, f));
        for (const d of ADDON_DIRS) {
          await cp(path.join(threeDir, 'examples', 'jsm', d), path.join(vendorOut, 'addons', d), { recursive: true });
        }
        logger.info('copied scene/ and three.js to dist/scene/');
      },
    },
  };
}
