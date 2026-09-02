import { expect, test } from "@playwright/test";
import { setupPrivacyPage } from "./utils/privacyMocks";

test("privacy center presents release-readiness context as manual action, not public ready", async ({ page }) => {
  await setupPrivacyPage(page);
  await page.goto("/privacy");

  await expect(page.getByText("manual-review-required").first()).toBeVisible();
  await expect(page.getByText("Technical draft - requires legal review before public deployment.")).toBeVisible();
  await expect(page.getByText("Public release ready")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /delete provider|apply provider|configure elevenlabs/i })).toHaveCount(0);
});
