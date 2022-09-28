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
  },
};

export default config;
