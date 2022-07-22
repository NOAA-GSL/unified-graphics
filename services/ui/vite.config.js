import { fileURLToPath } from "node:url";

const scss = {
  includePaths: ["node_modules/@uswds/uswds/packages"],
};

const config = {
  root: "src/",
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
};

export default config;
