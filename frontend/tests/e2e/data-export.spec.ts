import { expect, test } from "@playwright/test";
import { setupPrivacyPage } from "./utils/privacyMocks";

test("data export requires recent authentication and can remove artifacts", async ({ page }) => {
  await setupPrivacyPage(page);
  await page.goto("/privacy");

  await page.getByRole("button", { name: "Create" }).click();
  await expect(page.getByRole("heading", { name: "Confirm recent authentication" })).toBeVisible();
  await page.getByPlaceholder("Password").fill("Correct horse battery staple");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("status")).toContainText("Personal data export generated.");
  await expect(page.getByText("export-new")).toHaveCount(0);

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download" }).first().click();
  await page.getByPlaceholder("Password").fill("Correct horse battery staple");
  await page.getByRole("button", { name: "Continue" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("organicai-personal-data.zip.enc");

  await page.getByRole("button", { name: "Delete" }).first().click();
  await expect(page.getByRole("status")).toContainText("Export artifact removed.");
});
