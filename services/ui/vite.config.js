const config = {
  root: "src/",
  build: {
    outDir: "../build/",
  },
  css: {
    preprocessorOptions: {
      scss: {
        includePaths: ["node_modules/@uswds/uswds/packages"],
      },
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
};

export default config;
