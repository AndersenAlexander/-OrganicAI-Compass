import { expect, test } from "@playwright/test";

const baseUrl = process.env.ISOLATED_DEMO_E2E_BASE_URL;

test.describe("Demo browser-cycle acceptance", () => {
  test.skip(!baseUrl, "ISOLATED_DEMO_E2E_BASE_URL is required.");

  test("completes 50 Explore Demo -> profile -> logout -> Explore Demo cycles", async ({ page }) => {
    test.setTimeout(15 * 60_000);
    const demoStatuses: number[] = [];
    const logoutStatuses: number[] = [];
    const identities = new Set<string>();
    const databaseFailureResponses: Array<{ status: number; url: string }> = [];

    page.setDefaultTimeout(15_000);
    page.on("response", (response) => {
      const pathname = new URL(response.url()).pathname;
      if (!pathname.startsWith("/api/")) return;
      if (response.status() >= 500) {
        databaseFailureResponses.push({ status: response.status(), url: response.url() });
      }
      if (pathname === "/api/auth/demo-login") {
        demoStatuses.push(response.status());
      }
      if (pathname === "/api/auth/logout") logoutStatuses.push(response.status());
    });

    const enterDemo = async () => {
      const responsePromise = page.waitForResponse(
        (response) => new URL(response.url()).pathname === "/api/auth/demo-login",
      );
      await page.getByRole("button", { name: "Explore Demo", exact: true }).click();
      const response = await responsePromise;
      expect(response.status()).toBe(200);
      const body = (await response.json()) as { active_profile_id?: string; user?: { id?: string } };
      identities.add(`${body.user?.id}:${body.active_profile_id}`);
      await expect(page).toHaveURL(/\/profile\/demo-profile$/, { timeout: 15_000 });
      await expect(page.getByText("The demo account could not be prepared.")).toHaveCount(0);
    };

    const exitDemo = async () => {
      const responsePromise = page.waitForResponse(
        (response) => new URL(response.url()).pathname === "/api/auth/logout",
      );
      await page.getByRole("button", { name: "Exit Demo", exact: true }).last().click();
      expect((await responsePromise).status()).toBeLessThan(300);
      await expect(page).toHaveURL(/\/login$/);
    };

    await page.goto(`${baseUrl}/login`);
    await enterDemo();
    for (let cycle = 1; cycle <= 50; cycle += 1) {
      await exitDemo();
      await enterDemo();
    }

    expect(demoStatuses).toHaveLength(51);
    expect(logoutStatuses).toHaveLength(50);
    expect(demoStatuses.every((status) => status === 200)).toBe(true);
    expect(logoutStatuses.every((status) => status < 300)).toBe(true);
    expect(identities.size).toBe(1);
    expect(databaseFailureResponses).toEqual([]);
  });
});
