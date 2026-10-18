// @ts-check
import { defineConfig } from 'astro/config';
import sceneFiles from './src/integrations/scene-files.mjs';

// https://astro.build/config
export default defineConfig({
  // Live on Cloudflare Pages. Replace with the custom domain once it is set up.
  site: 'https://shrikantpawade.pages.dev',
  output: 'static',
  trailingSlash: 'never',
  build: { format: 'file' },
  integrations: [sceneFiles()],
});
