import { expect, test } from "@playwright/test";
import { setupPrivacyPage } from "./utils/privacyMocks";

test("privacy center displays policy, preferences, inventory and providers", async ({ page }) => {
  await setupPrivacyPage(page);
  await page.goto("/privacy");

  await expect(page.getByRole("heading", { level: 1, name: "Data controls" })).toBeVisible();
  await expect(page.getByText("Technical draft - requires legal review before public deployment.")).toBeVisible();
  await expect(page.getByText("2026-privacy-draft-1")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Conversation History" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Account Profile" })).toBeVisible();
  await expect(page.getByText("OpenAI")).toBeVisible();
  await expect(page.getByText("ElevenLabs")).toBeVisible();

  await page.getByRole("button", { name: "Ephemeral" }).first().click();
  await expect(page.getByRole("status")).toContainText("Privacy preferences saved.");
  await expect(page.getByText("conversation-history: withdrawn")).toBeVisible();
});
