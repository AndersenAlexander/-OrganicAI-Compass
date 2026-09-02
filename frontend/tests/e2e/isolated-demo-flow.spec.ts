import { expect, test } from "@playwright/test";

const isolatedDemoBaseUrl = process.env.ISOLATED_DEMO_E2E_BASE_URL;

function redactResponseBody(body: string) {
  try {
    const parsed = JSON.parse(body) as Record<string, unknown>;
    if ("access_token" in parsed) parsed.access_token = "[redacted]";
    if ("refresh_token" in parsed) parsed.refresh_token = "[redacted]";
    return JSON.stringify(parsed);
  } catch {
    return body;
  }
}

test.describe("isolated Demo login", () => {
  test.skip(!isolatedDemoBaseUrl, "ISOLATED_DEMO_E2E_BASE_URL is required for the isolated local Demo environment.");

  test("uses one canonical Demo account and profile across browser login, refresh, logout, and re-login", async ({ page }, testInfo) => {
    test.setTimeout(120_000);
    const requests: Array<Record<string, string | number>> = [];

    page.on("response", async (response) => {
      if (!new URL(response.url()).pathname.startsWith("/api/")) return;
      let body = "";
      try {
        body = await response.text();
      } catch {
        body = "<unreadable>";
      }
      requests.push({
        url: response.url(),
        method: response.request().method(),
        status: response.status(),
        body: redactResponseBody(body),
      });
    });

    try {
      await page.goto(`${isolatedDemoBaseUrl}/login`);
      const firstDemoResponse = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/auth/demo-login");
      await page.getByRole("button", { name: "Explore Demo", exact: true }).click();
      await firstDemoResponse;
      await expect(page).toHaveURL(/\/profile\/[^/]+$/, { timeout: 15_000 });
      await expect(page.getByText("The demo account could not be prepared.")).toHaveCount(0);

      const profileId = await page.evaluate(() => localStorage.getItem("organicai_active_profile_id"));
      expect(profileId).toBeTruthy();

      for (const path of [
        "/my-journey",
        `/career-compatibility/${profileId}`,
        `/workspace/${profileId}/career-resilience`,
        `/workspace/${profileId}/evidence-passport`,
        `/roadmap/${profileId}`,
        `/coach/${profileId}`,
      ]) {
        await page.goto(`${isolatedDemoBaseUrl}${path}`);
        await expect(page).toHaveURL(new RegExp(`${path.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`));
        await expect(page.locator("main").first()).toBeVisible();
      }

      const refreshResponse = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/auth/refresh");
      await page.reload();
      expect((await refreshResponse).status()).toBe(200);
      await expect(page).toHaveURL(new RegExp(`/coach/${profileId}$`));
      await expect(page.locator("main").first()).toBeVisible();
      expect(await page.evaluate(() => localStorage.getItem("organicai_active_profile_id"))).toBe(profileId);

      const exitDemoButton = page.getByRole("button", { name: "Exit Demo", exact: true }).first();
      await expect(exitDemoButton).toBeVisible();
      const logoutResponse = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/auth/logout");
      await exitDemoButton.click();
      expect((await logoutResponse).status()).toBeLessThan(300);
      await expect(page).toHaveURL(/\/login$/);

      const secondDemoResponse = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/auth/demo-login");
      await page.getByRole("button", { name: "Explore Demo", exact: true }).click();
      await secondDemoResponse;
      await expect(page).toHaveURL(/\/profile\/[^/]+$/);
      expect(await page.evaluate(() => localStorage.getItem("organicai_active_profile_id"))).toBe(profileId);

      const demoRequests = requests.filter((request) => request.url.includes("/auth/demo-login"));
      expect(demoRequests).toHaveLength(2);
      expect(demoRequests.every((request) => request.method === "POST" && request.status === 200)).toBe(true);
      const demoIdentities = demoRequests.map((request) => {
        const body = JSON.parse(String(request.body)) as { active_profile_id?: string; user?: { id?: string } };
        return `${body.user?.id}:${body.active_profile_id}`;
      });
      expect(new Set(demoIdentities)).toEqual(new Set([demoIdentities[0]]));
    } finally {
      await testInfo.attach("isolated-demo-network", {
        body: JSON.stringify(requests, null, 2),
        contentType: "application/json",
      });
    }
  });

  test("coalesces same-tick Explore Demo clicks into one backend request", async ({ page }) => {
    let requestCount = 0;
    page.on("request", (request) => {
      if (new URL(request.url()).pathname === "/api/auth/demo-login") requestCount += 1;
    });

    await page.goto(`${isolatedDemoBaseUrl}/login`);
    const button = page.getByRole("button", { name: "Explore Demo", exact: true });
    await button.evaluate((element) => {
      (element as HTMLButtonElement).click();
      (element as HTMLButtonElement).click();
    });

    await expect(page).toHaveURL(/\/profile\/demo-profile$/);
    await page.waitForTimeout(500);
    expect(requestCount).toBe(1);
  });
});
