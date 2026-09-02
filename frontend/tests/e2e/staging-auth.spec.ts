import { expect, test } from "@playwright/test";

const baseURL = process.env.STAGING_BASE_URL ?? "http://127.0.0.1:18080";

test("staging protects workspace routes without browser token storage", async ({ page }) => {
  await page.goto(`${baseURL}/privacy`);
  await expect(page).toHaveURL(/login/);
  const localStorageKeys = await page.evaluate(() => Object.keys(window.localStorage));
  expect(localStorageKeys.join(" ")).not.toContain("token");
});
