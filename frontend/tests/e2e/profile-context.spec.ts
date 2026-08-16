import { expect, test, type Page } from "@playwright/test";

async function mockProfileContext(page: Page, profiles: Array<{ id: string }> = [{ id: "owned-profile" }]) {
  await page.setViewportSize({ width: 1448, height: 1086 });
  await page.addInitScript(() => {
    localStorage.setItem("organicai_active_profile_id", "stale-profile");
    localStorage.removeItem("organicai.auth.token");
  });
  const user = { id: "user-1", email: "user@example.test", name: "Alex User", is_demo: false };
  await page.route("**/api/auth/refresh", (route) =>
    route.fulfill({ status: 200, json: { access_token: "profile-context-token", token_type: "bearer", expires_in: 900, user } }),
  );
  await page.route("**/api/auth/me", (route) => route.fulfill({ status: 200, json: user }));
  await page.route("**/api/auth/logout", (route) => route.fulfill({ status: 200, json: { ok: true } }));
  await page.route("**/api/profiles", (route) =>
    route.fulfill({
      status: 200,
      json: profiles.map((profile) => ({ id: profile.id, created_at: "2026-01-01T00:00:00Z", data: {} })),
    }),
  );
}

test("normal authenticated profile context uses owned profiles and never falls back to demo-profile", async ({ page }) => {
  await mockProfileContext(page, [{ id: "owned-profile" }]);
  await page.goto("/dashboard");
  await expect(page.getByRole("button", { name: /Workspace/ })).toBeVisible();
  await page.getByRole("button", { name: /Workspace/ }).click();
  await expect(page.locator('a[href*="demo-profile"]')).toHaveCount(0);
  await expect(page.locator('a[href="/profile/owned-profile"]')).toBeVisible();
  await expect.poll(() => page.evaluate(() => localStorage.getItem("organicai_active_profile_id"))).toBe("owned-profile");
});

test("authenticated no-profile state does not create demo-profile links", async ({ page }) => {
  await mockProfileContext(page, []);
  await page.goto("/dashboard");
  await page.getByRole("button", { name: /Workspace/ }).click();
  await expect(page.locator('a[href*="demo-profile"]')).toHaveCount(0);
  await expect(page.getByRole("menuitem", { name: "Natural Discovery" })).toBeVisible();
  await expect.poll(() => page.evaluate(() => localStorage.getItem("organicai_active_profile_id"))).toBeNull();
});

test("logout clears active profile context", async ({ page }) => {
  await mockProfileContext(page, [{ id: "owned-profile" }]);
  await page.goto("/dashboard");
  await expect.poll(() => page.evaluate(() => localStorage.getItem("organicai_active_profile_id"))).toBe("owned-profile");
  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect.poll(() => page.evaluate(() => localStorage.getItem("organicai_active_profile_id"))).toBeNull();
});
