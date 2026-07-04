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

test("shows error screen controls when an error occurs", async ({ page }) => {
  await page.evaluate(() => {
    const errorScreen = document.querySelector("#screen-error");
    if (errorScreen) {
      errorScreen.removeAttribute("hidden");
    }
  });
  await expect(page.locator("#btn-open-log")).toBeVisible();
  await expect(page.locator("#btn-back-from-error")).toBeVisible();
});
