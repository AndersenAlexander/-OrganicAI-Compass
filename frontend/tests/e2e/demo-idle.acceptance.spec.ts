import { expect, test } from "@playwright/test";

const baseUrl = process.env.ISOLATED_DEMO_E2E_BASE_URL;

test.describe("Demo idle-session acceptance", () => {
  test.skip(!baseUrl, "ISOLATED_DEMO_E2E_BASE_URL is required.");

  test("logs out and back in after ten minutes idle", async ({ page }) => {
    test.setTimeout(12 * 60_000);
    const databaseFailures: Array<{ status: number; url: string }> = [];
    page.on("response", (response) => {
      if (new URL(response.url()).pathname.startsWith("/api/") && response.status() >= 500) {
        databaseFailures.push({ status: response.status(), url: response.url() });
      }
    });

    await page.goto(`${baseUrl}/login`);
    const firstLogin = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/auth/demo-login");
    await page.getByRole("button", { name: "Explore Demo", exact: true }).click();
    expect((await firstLogin).status()).toBe(200);
    await expect(page).toHaveURL(/\/profile\/demo-profile$/);

    await page.waitForTimeout(10 * 60_000);

    const logout = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/auth/logout");
    await page.getByRole("button", { name: "Exit Demo", exact: true }).last().click();
    expect((await logout).status()).toBeLessThan(300);
    await expect(page).toHaveURL(/\/login$/);

    const secondLogin = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/auth/demo-login");
    await page.getByRole("button", { name: "Explore Demo", exact: true }).click();
    expect((await secondLogin).status()).toBe(200);
    await expect(page).toHaveURL(/\/profile\/demo-profile$/);
    expect(databaseFailures).toEqual([]);
  });
});
