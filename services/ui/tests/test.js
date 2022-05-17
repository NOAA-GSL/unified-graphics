import { expect, test } from "@playwright/test";

test("application has expected title", async ({ page }) => {
  await page.goto("/");
  expect(await page.textContent("header")).toBe("Unified Graphics");
});
