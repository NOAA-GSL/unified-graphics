import adapter from "@sveltejs/adapter-node";
import preprocess from "svelte-preprocess";

// FIXME: Duplicated from vite.config.js
const scss = {
  includePaths: ["node_modules/@uswds/uswds/packages"],
};

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: preprocess({ scss }),
  kit: {
    adapter: adapter(),
    prerender: {
      default: true,
    },
  },
};

export default config;
