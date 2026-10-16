// @ts-check
import { defineConfig } from 'astro/config';
import sceneFiles from './src/integrations/scene-files.mjs';

// https://astro.build/config
export default defineConfig({
  // Set the real domain here once decided (docs/05-decisions.md).
  site: 'https://example.com',
  output: 'static',
  trailingSlash: 'never',
  build: { format: 'file' },
  integrations: [sceneFiles()],
});
