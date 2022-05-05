import adapter from '@sveltejs/adapter-auto';
import preprocess from 'svelte-preprocess';

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
      }
    }
  }
};

export default config;
