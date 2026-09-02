import { expect, test } from "@playwright/test";

test.describe("Real ElevenLabs live voice validation", () => {
  test.skip(process.env.REAL_PROVIDER_TESTS_ENABLED !== "true", "REAL_PROVIDER_TESTS_ENABLED=true is required.");

  test("loads Coach and exposes live voice diagnostics", async ({ page }) => {
    await page.goto("/coach/demo-profile");
    await expect(page.getByText("Voice connection diagnostics")).toBeVisible();
  });
});
