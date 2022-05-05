import adapter from '@sveltejs/adapter-auto';
import preprocess from 'svelte-preprocess';

import { fileURLToPath } from "node:url";

const scss = {
  includePaths: [
    'node_modules/@uswds/uswds/packages'
  ]
};

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: preprocess({ scss }),
  kit: {
    adapter: adapter(),
    vite: {
      css: {
        preprocessorOptions: { scss }
      },
      resolve: {
        alias: {
          "styles": fileURLToPath(new URL('./src/styles/_index.scss', import.meta.url))
        }
      }
    }
  }
};

export default config;
