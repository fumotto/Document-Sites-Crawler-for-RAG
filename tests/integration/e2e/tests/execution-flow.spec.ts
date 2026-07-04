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

test("starts execution and enters running state", async ({ page }) => {
  await page.fill("#urls_text", "https://example.com/docs");
  await page.click("#btn-start");
  await expect(page.locator("#screen-running")).toBeVisible();
  await expect(page.locator("#progress-text")).toContainText("サイト処理中");
});
