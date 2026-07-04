import { test, expect } from "@playwright/test";
import { fileURLToPath } from "node:url";
import path from "path";

const pagePath = fileURLToPath(
  new URL("../../../web/index.html", import.meta.url),
);
const stubPath = fileURLToPath(
  new URL("../fixtures/pywebview-stub.ts", import.meta.url),
);

test.beforeEach(async ({ page }) => {
  await page.addInitScript({ path: stubPath });
  await page.goto(`file://${pagePath}`);
});

test("shows the input screen and controls", async ({ page }) => {
  await expect(page.locator("#app-title")).toHaveText(
    "Document Sites Crawler for RAG",
  );
  await expect(page.locator("#urls_text")).toBeVisible();
  await expect(page.locator("#btn-start")).toBeVisible();
  await expect(page.locator("label", { hasText: "モード" })).toBeVisible();
});
