import type { Page, Route } from "@playwright/test";

export type MockAuthState = "none" | "user" | "demo";

export function mockAuthUser(state: Exclude<MockAuthState, "none"> = "user") {
  return {
    id: `${state}-user`,
    email: `${state}@example.test`,
    name: state === "demo" ? "Demo User" : "Alex User",
    is_demo: state === "demo",
  };
}

export async function fulfillMockAuthRoute(route: Route, state: MockAuthState = "user") {
  const { pathname } = new URL(route.request().url());
  if (!pathname.endsWith("/auth/refresh") && !pathname.endsWith("/auth/me")) return false;

  if (state === "none") {
    await route.fulfill({ status: 401, json: { detail: "Not authenticated" } });
    return true;
  }

  const user = mockAuthUser(state);
  if (pathname.endsWith("/auth/refresh")) {
    await route.fulfill({
      status: 200,
      json: {
        access_token: `playwright-${state}-memory-token`,
        token_type: "bearer",
        expires_in: 900,
        user,
      },
    });
    return true;
  }

  await route.fulfill({ status: 200, json: user });
  return true;
}

export async function installMockAuthSession(
  page: Page,
  options: { state?: MockAuthState; profileId?: string; theme?: "light" | "dark" } = {},
) {
  const state = options.state ?? "user";
  const profileId = options.profileId ?? "demo-profile";
  const theme = options.theme ?? "dark";

  await page.addInitScript(
    ({ profileId, theme }) => {
      localStorage.setItem("organicai_active_profile_id", profileId);
      localStorage.setItem("organicai-theme", theme);
      localStorage.removeItem("organicai.auth.token");
    },
    { profileId, theme },
  );

  await page.route("**/api/auth/**", async (route) => {
    if (await fulfillMockAuthRoute(route, state)) return;
    await route.fallback();
  });

  await page.route("**/api/profiles", async (route) => {
    if (state === "none") {
      await route.fulfill({ status: 401, json: { detail: "Not authenticated" } });
      return;
    }
    await route.fulfill({
      status: 200,
      json: state === "demo" ? [{ id: "demo-profile", created_at: "2026-01-01T00:00:00Z", data: {} }] : [{ id: profileId, created_at: "2026-01-01T00:00:00Z", data: {} }],
    });
  });
}
