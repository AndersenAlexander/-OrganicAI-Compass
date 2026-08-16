import { expect, test } from "@playwright/test";
import { setupPrivacyPage } from "./utils/privacyMocks";

test("privacy center shows provider privacy status without secrets or full identifiers", async ({ page }) => {
  await setupPrivacyPage(page);
  await page.goto("/privacy");

  await expect(page.getByText("OpenAI")).toBeVisible();
  await expect(page.getByText("training: unknown")).toBeVisible();
  await expect(page.getByText("abuse: unknown")).toBeVisible();
  await expect(page.getByText("residency: unknown")).toBeVisible();
  await expect(page.getByText("data controls not verified")).toBeVisible();
  await expect(page.getByText("ElevenLabs")).toBeVisible();
  await expect(page.getByText("audio: unknown")).toBeVisible();
  await expect(page.getByText("zero retention: unknown")).toBeVisible();
  await expect(page.getByText("webhook HMAC: not-configured")).toBeVisible();
  await expect(page.getByText(/sk-/)).toHaveCount(0);
  await expect(page.getByText(/agent-[a-z0-9]/i)).toHaveCount(0);
});

test("privacy center provider status works in mobile light mode", async ({ page }) => {
  await setupPrivacyPage(page);
  await page.addInitScript(() => localStorage.setItem("organicai-theme", "light"));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/privacy");

  await expect(page.getByRole("heading", { name: "Data controls" })).toBeVisible();
  await expect(page.getByText("Provider retention settings have not yet been verified").or(page.getByText("zero retention: unknown"))).toBeVisible();
});
