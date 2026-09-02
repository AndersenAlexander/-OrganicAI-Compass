import { expect, test } from "@playwright/test";
import { setupPrivacyPage } from "./utils/privacyMocks";

test("ephemeral conversation mode is exposed as an account privacy control", async ({ page }) => {
  await setupPrivacyPage(page);
  await page.goto("/privacy");

  await page.getByRole("button", { name: "Ephemeral" }).first().click();
  await expect(page.getByRole("status")).toContainText("Privacy preferences saved.");
  await expect(page.getByText("Ephemeral").first()).toBeVisible();
  await expect(page.getByText("Ephemeral conversations are excluded from research collection.")).toBeVisible();
});
