import adapter from '@sveltejs/adapter-auto';
import preprocess from 'svelte-preprocess';
import { sass } from 'sass';

const USWDS_PACKAGES = new URL('./node_modules/@uswds/uswds/packages', import.meta.url).toString();

console.log(USWDS_PACKAGES);

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: preprocess({
    implementation: sass({
      includePaths: [USWDS_PACKAGES]
    })
  }),
  kit: {
    adapter: adapter()
  }
};

export default config;
