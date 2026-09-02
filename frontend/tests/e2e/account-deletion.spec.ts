import { expect, test } from "@playwright/test";
import { setupPrivacyPage } from "./utils/privacyMocks";

test("account deletion can be queued and cancelled from privacy center", async ({ page }) => {
  await setupPrivacyPage(page);
  await page.goto("/privacy");

  await page.getByRole("button", { name: "Request deletion" }).click();
  await page.getByPlaceholder("Password").fill("Correct horse battery staple");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("status")).toContainText("Account deletion queued");
  await expect(page.getByText("Queued", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Cancel deletion" }).click();
  await expect(page.getByRole("status")).toContainText("Account deletion cancelled.");
  await expect(page.getByRole("button", { name: "Request deletion" })).toBeVisible();
});
