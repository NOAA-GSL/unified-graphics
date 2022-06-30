import adapter from "@sveltejs/adapter-node";
import preprocess from "svelte-preprocess";

import { fileURLToPath } from "node:url";

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
    vite: {
      css: {
        preprocessorOptions: { scss },
      },
      resolve: {
        alias: {
          "/fonts": fileURLToPath(
            new URL("./node_modules/@uswds/uswds/dist/fonts", import.meta.url)
          ),
          styles: fileURLToPath(new URL("./src/styles/_index.scss", import.meta.url)),
        },
      },
    },
  },
};

export default config;
