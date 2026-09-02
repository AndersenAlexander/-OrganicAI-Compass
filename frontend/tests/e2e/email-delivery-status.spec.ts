import { expect, test } from "@playwright/test";
import { setupPrivacyPage } from "./utils/privacyMocks";

test("privacy center shows email delivery status without false inbox-delivery claim", async ({ page }) => {
  await setupPrivacyPage(page);
  await page.goto("/privacy");

  await expect(page.getByText("Email")).toBeVisible();
  await expect(page.getByText("driver: development-outbox")).toBeVisible();
  await expect(page.getByText("smtp-acceptance-only")).toBeVisible();
  await expect(page.getByText("Inbox delivery verified")).toHaveCount(0);
  await expect(page.getByText(/smtp.*password/i)).toHaveCount(0);
});
