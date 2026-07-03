import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  reporter: [["list"]],
  webServer: {
    command: "node ../../testserver/server.js",
    url: "http://127.0.0.1:8080",
    reuseExistingServer: true,
    timeout: 30_000,
  },
  use: {
    baseURL: "http://127.0.0.1:8080",
    headless: true,
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
  },
});
