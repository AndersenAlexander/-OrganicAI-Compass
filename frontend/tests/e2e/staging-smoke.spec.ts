import { expect, test } from "@playwright/test";

const baseURL = process.env.STAGING_BASE_URL ?? "http://127.0.0.1:18080";

test("staging public origin serves frontend and health endpoints", async ({ page, request }) => {
  await page.goto(baseURL);
  await expect(page.locator("#root")).toBeAttached();
  await expect((await request.get(`${baseURL}/health`)).status()).toBe(200);
  await expect((await request.get(`${baseURL}/health/live`)).status()).toBe(200);
});
