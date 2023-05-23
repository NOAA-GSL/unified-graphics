import { playwrightLauncher } from "@web/test-runner-playwright";

const filteredLogs = [
  "Running in dev mode",
  "lit-html is in dev mode",
  "Lit is in dev mode",
];

export default /** @type {import("@web/test-runner").TestRunnerConfig} */ ({
  /** Test files to run */
  files: "tests/js/**/*.test.js",

  /** Resolve bare module imports */
  nodeResolve: {
    exportConditions: ["browser", "development"],
  },

  /** Filter out lit dev mode logs */
  filterBrowserLogs(log) {
    for (const arg of log.args) {
      if (typeof arg === "string" && filteredLogs.some((l) => arg.includes(l))) {
        return false;
      }
    }
    return true;
  },

  /** Browsers to run tests on */
  browsers: [playwrightLauncher({ product: "chromium" })],

  /** Mocks for network tests */
  plugins: [
    {
      name: "mock-api",
      serve(context) {
        if (context.path !== "/api/data/") return;
        return JSON.stringify([1, 2, 3]);
      },
    },
  ],
});
