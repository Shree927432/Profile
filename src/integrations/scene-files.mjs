// Serves the repo's scene/ folder at /scene/ in dev and copies it into dist/ on
// build, so the home page can load /scene/boot.js without moving scene/ under
// public/. scene/ stays where docs/02-architecture.md puts it.
import { cp, stat } from 'node:fs/promises';
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

export default function sceneFiles() {
  let sceneDir;
  return {
    name: 'scene-files',
    hooks: {
      'astro:config:setup': ({ config, updateConfig }) => {
        sceneDir = path.join(fileURLToPath(config.root), 'scene');
        updateConfig({
          vite: {
            plugins: [
              {
                name: 'scene-files-dev',
                configureServer(server) {
                  server.middlewares.use(async (req, res, next) => {
                    const url = (req.url || '').split('?')[0];
                    if (!url.startsWith('/scene/')) return next();
                    const rel = path.normalize(decodeURIComponent(url.slice('/scene/'.length)));
                    if (rel.startsWith('..')) return next();
                    const file = path.join(sceneDir, rel);
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
        logger.info('copied scene/ to dist/scene/');
      },
    },
  };
}
