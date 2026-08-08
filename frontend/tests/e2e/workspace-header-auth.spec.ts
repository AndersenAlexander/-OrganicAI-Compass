import { expect, test, type Page } from "@playwright/test";

const activeProfileId = "demo-profile";

type AuthState = "unauthenticated" | "authenticated" | "demo";

async function prepareGlobalHeaderState(page: Page, state: AuthState) {
  await page.setViewportSize({ width: 1448, height: 1086 });
  await page.addInitScript(
    ({ profileId, state }) => {
      localStorage.setItem("organicai_active_profile_id", profileId);
      localStorage.setItem("organicai-theme", "dark");
      if (state === "unauthenticated") localStorage.removeItem("organicai.auth.token");
      else localStorage.setItem("organicai.auth.token", `${state}-token`);
    },
    { profileId: activeProfileId, state }
  );

  await page.route("**/api/auth/me", async (route) => {
    if (state === "unauthenticated") {
      await route.fulfill({ status: 401, json: { detail: "Not authenticated" } });
      return;
    }

    await route.fulfill({
      status: 200,
      json: {
        id: `${state}-user`,
        email: `${state}@example.test`,
        name: state === "demo" ? "Demo User" : "Alex User",
        is_demo: state === "demo",
      },
    });
  });
}

async function openGlobalHeaderPage(page: Page) {
  await page.goto("/diagnostic");
  await expect(page.getByTestId("global-header")).toHaveCount(1);
  await expect(page.getByRole("navigation", { name: "Global navigation" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Workspace navigation" })).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Public navigation" })).toHaveCount(0);
}

test.describe("GlobalHeader authentication states", () => {
  test("unauthenticated state shows login and get started only", async ({ page }) => {
    await prepareGlobalHeaderState(page, "unauthenticated");
    await openGlobalHeaderPage(page);

    const header = page.getByTestId("global-header");
    await expect(header.getByRole("link", { name: "Log in", exact: true })).toBeVisible();
    await expect(header.getByRole("link", { name: "Get Started", exact: true })).toBeVisible();
    await expect(header.getByRole("link", { name: "Create account", exact: true })).toHaveCount(0);
    await expect(header.getByRole("link", { name: "Start Journey", exact: true })).toHaveCount(0);
    await expect(header.getByRole("button", { name: /Logout|Exit Demo/i })).toHaveCount(0);
    await expect(header.getByText("Demo Mode")).toHaveCount(0);
    await expect(header.getByRole("link", { name: "Alex", exact: true })).toHaveCount(0);
  });

  test("authenticated normal user state shows user and logout without unauthenticated CTAs", async ({ page }) => {
    await prepareGlobalHeaderState(page, "authenticated");
    await openGlobalHeaderPage(page);

    const header = page.getByTestId("global-header");
    await expect(header.getByRole("link", { name: "Alex", exact: true })).toBeVisible();
    await expect(header.getByRole("button", { name: "Logout" })).toBeVisible();
    await expect(header.getByRole("link", { name: "Log in", exact: true })).toHaveCount(0);
    await expect(header.getByRole("link", { name: "Get Started", exact: true })).toHaveCount(0);
    await expect(header.getByText("Demo Mode")).toHaveCount(0);
  });

  test("authenticated demo user state shows demo indicator and exit demo", async ({ page }) => {
    await prepareGlobalHeaderState(page, "demo");
    await openGlobalHeaderPage(page);

    const header = page.getByTestId("global-header");
    await expect(header.getByText("Demo Mode", { exact: true })).toBeVisible();
    await expect(header.getByRole("button", { name: "Exit Demo" })).toBeVisible();
    await expect(header.getByRole("link", { name: "Log in", exact: true })).toHaveCount(0);
    await expect(header.getByRole("link", { name: "Get Started", exact: true })).toHaveCount(0);
  });
});
