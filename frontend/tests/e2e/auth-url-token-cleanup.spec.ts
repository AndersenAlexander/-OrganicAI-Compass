import { expect, test, type Page } from "@playwright/test";

async function mockUnauthenticatedBoot(page: Page) {
  await page.route("**/api/auth/refresh", async (route) => route.fulfill({ status: 401, json: { detail: "Not authenticated" } }));
  await page.route("**/api/auth/me", async (route) => route.fulfill({ status: 401, json: { detail: "Not authenticated" } }));
}

test("reset password captures URL token and removes it from the address bar", async ({ page }) => {
  await mockUnauthenticatedBoot(page);
  await page.goto("/reset-password?token=reset-secret&next=settings");
  await expect.poll(() => page.url()).not.toContain("reset-secret");
  await expect(page).toHaveURL(/\/reset-password\?next=settings$/);
  await expect(page.getByLabel("Reset token")).toHaveCount(0);
});

test("email verification captures URL token and removes it from the address bar", async ({ page }) => {
  await mockUnauthenticatedBoot(page);
  await page.goto("/verify-email?token=verify-secret&next=settings");
  await expect.poll(() => page.url()).not.toContain("verify-secret");
  await expect(page).toHaveURL(/\/verify-email\?next=settings$/);
  await expect(page.getByLabel("Verification token")).toHaveCount(0);
});
