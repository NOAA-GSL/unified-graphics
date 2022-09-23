import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { viteStaticCopy } from "vite-plugin-static-copy";

export default defineConfig({
  root: "src/",
  build: {
    outDir: "../build/",
  },
  plugins: [
    svelte(),
    viteStaticCopy({
      targets: [
        { src: "../node_modules/@uswds/uswds/dist/img", dest: "." },
        { src: "../node_modules/@uswds/uswds/dist/fonts", dest: "." },
      ],
    }),
  ],
  css: {
    preprocessorOptions: {
      scss: {
        includePaths: ["node_modules/@uswds/uswds/packages"],
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    include: ["../tests/unit/**/*.js"],
    coverage: {
      all: true,
      reporter: ["text"],
    },
  },
});
