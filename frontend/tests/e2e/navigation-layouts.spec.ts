import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const activeProfileId = "demo-profile";
const desktop = { width: 1448, height: 1086 };
const mobile = { width: 390, height: 844 };
const backendApiRequest = (url: URL) => url.pathname.startsWith("/api/");

const emptyFeedback = {
  confirmed_nodes: [],
  hidden_recommendations: [],
  strength_adjustments: {},
  archetype_override: null,
  user_notes: {},
};

function mockRoadmap() {
  return {
    id: "demo-roadmap",
    profile_id: activeProfileId,
    title: "Demo Roadmap",
    summary: "A compact test roadmap.",
    status: "active",
    version: 1,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    last_recalibrated_at: null,
    progress: {
      total_actions: 0,
      completed_actions: 0,
      in_progress_actions: 0,
      skipped_actions: 0,
      blocked_actions: 0,
      completion_percentage: 0,
    },
    horizons: { seven_days: [], thirty_days: [], six_months: [] },
    milestones: [],
    recalibration_notes: [],
    ethical_cautions: [],
    contribution_direction: "Human-centred AI contribution",
    seven_days: [],
    thirty_days: [],
    six_months: [],
    recommended_skills: [],
    ai_workflows: [],
    project_idea: "",
    social_contribution_idea: "",
  };
}

function mockProfile() {
  return {
    id: activeProfileId,
    diagnostic_id: "demo-diagnostic",
    primary_archetype: "Curious Explorer",
    secondary_archetype: "Responsible Builder",
    strengths: ["Systems Thinking"],
    values: ["Agency"],
    fears: ["Losing human control"],
    creative_tendencies: ["Prototype and reflect"],
    ai_collaboration_style: "Co-Creator",
    contribution_domains: ["Human-centred AI"],
    recommended_learning_paths: ["Responsible AI Practice"],
    uncertainties: [],
    risk_notes: [],
    ethical_note: "This is an exploratory profile, not a fixed label.",
    user_feedback: emptyFeedback,
    created_at: "2026-01-01T00:00:00Z",
  };
}

async function prepareNavigationPage(page: Page, viewport = desktop) {
  await page.setViewportSize(viewport);
  await page.addInitScript((profileId) => {
    localStorage.setItem("organicai_active_profile_id", profileId);
    localStorage.setItem("organicai-theme", "dark");
    localStorage.removeItem("organicai.auth.token");
  }, activeProfileId);

  await page.route(backendApiRequest, async (route) => {
    const url = new URL(route.request().url());

    if (await fulfillMockAuthRoute(route)) return;

    if (url.pathname === "/api/diagnostics") {
      await route.fulfill({ status: 200, json: [{ id: "demo-diagnostic", created_at: "2026-01-01T00:00:00Z", payload: {} }] });
      return;
    }

    if (url.pathname === "/api/profiles") {
      await route.fulfill({
        status: 200,
        json: [{ id: activeProfileId, created_at: "2026-01-01T00:00:00Z", data: mockProfile() }],
      });
      return;
    }

    if (url.pathname === `/api/profiles/${activeProfileId}`) {
      await route.fulfill({ status: 200, json: mockProfile() });
      return;
    }

    if (url.pathname === `/api/profiles/${activeProfileId}/feedback`) {
      await route.fulfill({ status: 200, json: emptyFeedback });
      return;
    }

    if (url.pathname === "/api/roadmap") {
      await route.fulfill({ status: 200, json: [{ id: "demo-roadmap", created_at: "2026-01-01T00:00:00Z", data: mockRoadmap() }] });
      return;
    }

    if (url.pathname === `/api/roadmap/${activeProfileId}` || url.pathname === "/api/roadmap/generate") {
      await route.fulfill({ status: 200, json: mockRoadmap() });
      return;
    }

    if (url.pathname.startsWith("/api/roadmaps/demo-roadmap/")) {
      await route.fulfill({ status: 200, json: [] });
      return;
    }

    if (url.pathname === `/api/recommendations/profile/${activeProfileId}`) {
      await route.fulfill({ status: 200, json: [] });
      return;
    }

    if (url.pathname === "/api/recommendations/generate") {
      await route.fulfill({
        status: 200,
        json: { recommendations: [], context_summary: { profile_signals_used: [], feedback_applied: false }, metadata: {} },
      });
      return;
    }

    await route.fulfill({ status: 200, json: [] });
  });
}

async function expectSingleLayoutChrome(page: Page) {
  await expect(page.getByTestId("global-header")).toHaveCount(1);
  await expect(page.locator("header.no-print")).toHaveCount(1);
  expect(await page.locator("footer").count()).toBeLessThanOrEqual(1);
  await expect(page.locator(".organic-gradient-bg")).toHaveCount(1);
  await expect(page.locator(".organic-gradient-bg > main")).toHaveCount(1);
  expect(await page.locator(".fixed.bottom-4.right-4").count()).toBeLessThanOrEqual(1);
  await expect(page.locator('[data-testid="public-header"], [data-testid="workspace-header"], [data-testid="auth-header"]')).toHaveCount(0);
  await expect(page.locator('a[href*="/undefined"], a[href*="/null"]')).toHaveCount(0);
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

async function openWorkspaceDropdown(page: Page) {
  const button = page.getByRole("button", { name: "Workspace" });
  await expect(button).toBeVisible();
  await button.click();
  const menu = page.locator("#global-workspace-dropdown");
  await expect(menu).toBeVisible();
  return menu;
}

test.describe("navigation route layouts", () => {
  test.beforeEach(async ({ page }) => {
    await prepareNavigationPage(page);
  });

  for (const path of ["/", "/about", "/how-it-works", "/principles"] as const) {
    test(`${path} shows the unified global navigation`, async ({ page }) => {
      await page.goto(path);

      const globalNav = page.getByRole("navigation", { name: "Global navigation" });
      await expect(globalNav).toBeVisible();
      await expect(globalNav.getByRole("link", { name: "About", exact: true })).toHaveAttribute("href", "/about");
      await expect(globalNav.getByRole("link", { name: "Research", exact: true })).toHaveAttribute("href", "/research");
      await expect(globalNav.getByRole("link", { name: "Project Roadmap", exact: true })).toHaveAttribute("href", "/project-roadmap");
      await expect(globalNav.getByRole("link", { name: "Journal", exact: true })).toHaveAttribute("href", "/blog");
      await expect(page.getByRole("button", { name: "Workspace" })).toBeVisible();
      await expect(page.getByRole("navigation", { name: "Public navigation" })).toHaveCount(0);
      await expect(page.getByRole("navigation", { name: "Workspace navigation" })).toHaveCount(0);
      await expectSingleLayoutChrome(page);
    });
  }

  test("/research shows global navigation and Research is active", async ({ page }) => {
    await page.goto("/research");

    const globalNav = page.getByRole("navigation", { name: "Global navigation" });
    await expect(globalNav).toBeVisible();
    await expect(globalNav.getByRole("link", { name: "Research", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("heading", { level: 1, name: /Researching human-centred AI guidance/ })).toBeVisible();
    await expectSingleLayoutChrome(page);
  });

  test("/project-roadmap shows global navigation and Project Roadmap is active", async ({ page }) => {
    await page.goto("/project-roadmap");

    const globalNav = page.getByRole("navigation", { name: "Global navigation" });
    await expect(globalNav).toBeVisible();
    await expect(globalNav.getByRole("link", { name: "Project Roadmap", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("button", { name: "Workspace" })).not.toHaveClass(/global-header__link--active/);
    await expect(page.getByRole("heading", { level: 1, name: /From research concept\s+to evaluated prototype/ })).toBeVisible();
    await expectSingleLayoutChrome(page);
  });

  test("/blog shows global navigation and Journal is active", async ({ page }) => {
    await page.goto("/blog");

    const globalNav = page.getByRole("navigation", { name: "Global navigation" });
    await expect(globalNav).toBeVisible();
    await expect(globalNav.getByRole("link", { name: "Journal", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("navigation", { name: "Public navigation" })).toHaveCount(0);
    await expectSingleLayoutChrome(page);
  });

  test("/knowledge-base shows global navigation and active Workspace dropdown item", async ({ page }) => {
    await page.goto("/knowledge-base");

    const globalNav = page.getByRole("navigation", { name: "Global navigation" });
    await expect(globalNav).toBeVisible();
    await expect(globalNav.getByRole("link", { name: "About", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Workspace" })).toHaveClass(/global-header__link--active/);
    const workspaceMenu = await openWorkspaceDropdown(page);
    await expect(workspaceMenu.getByRole("menuitem", { name: "Knowledge Base", exact: true })).toHaveAttribute("aria-current", "page");
    await expectSingleLayoutChrome(page);
  });

  test("/diagnostic shows global navigation and active Workspace dropdown item", async ({ page }) => {
    await page.goto("/diagnostic");

    await expect(page.getByRole("navigation", { name: "Global navigation" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Workspace" })).toHaveClass(/global-header__link--active/);
    const workspaceMenu = await openWorkspaceDropdown(page);
    await expect(workspaceMenu.getByRole("menuitem", { name: "Natural Discovery", exact: true })).toHaveAttribute("aria-current", "page");
    await expectSingleLayoutChrome(page);
  });

  test("/login uses the same GlobalHeader with full global navigation", async ({ page }) => {
    await page.goto("/login");

    await expect(page.getByRole("link", { name: /OrganicAI/i })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Global navigation" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Workspace" })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Public navigation" })).toHaveCount(0);
    await expect(page.getByRole("navigation", { name: "Workspace navigation" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Open navigation menu" })).toHaveCount(0);
    await expectSingleLayoutChrome(page);
  });

  test("mobile /research shows one combined global menu", async ({ page }) => {
    await page.setViewportSize(mobile);
    await page.goto("/research");

    await page.getByRole("button", { name: "Open navigation menu" }).click();
    const panel = page.locator("#global-mobile-navigation");
    await expect(panel).toBeVisible();
    const exploreNav = page.getByRole("navigation", { name: "Global mobile navigation" });
    const workspaceNav = page.getByRole("navigation", { name: "Global mobile workspace navigation" });
    await expect(exploreNav.getByRole("link", { name: "Research", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(exploreNav.getByRole("link", { name: "About", exact: true })).toBeVisible();
    await expect(workspaceNav.getByRole("link", { name: "Knowledge Base", exact: true })).toBeVisible();
    await expect(workspaceNav.getByRole("link", { name: "AI Coach", exact: true })).toHaveAttribute("href", `/coach/${activeProfileId}`);
    await expect(page.getByRole("navigation", { name: "Public mobile navigation" })).toHaveCount(0);
    await expect(page.getByRole("navigation", { name: "Workspace mobile navigation" })).toHaveCount(0);
    await page.keyboard.press("Escape");
    await expect(panel).toHaveCount(0);
    await expectNoHorizontalOverflow(page);
    await expectSingleLayoutChrome(page);
  });

  test("mobile /knowledge-base shows the same combined menu with workspace active state", async ({ page }) => {
    await page.setViewportSize(mobile);
    await page.goto("/knowledge-base");

    await page.getByRole("button", { name: "Open navigation menu" }).click();
    const workspaceNav = page.getByRole("navigation", { name: "Global mobile workspace navigation" });
    await expect(workspaceNav).toBeVisible();
    await expect(workspaceNav.getByRole("link", { name: "Knowledge Base", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(workspaceNav.getByRole("link", { name: "AI Coach", exact: true })).toHaveAttribute("href", `/coach/${activeProfileId}`);
    await expect(page.getByRole("navigation", { name: "Global mobile navigation" }).getByRole("link", { name: "Research", exact: true })).toBeVisible();
    await expectNoHorizontalOverflow(page);
    await expectSingleLayoutChrome(page);
  });

  test("workspace profile-aware links use the current activeProfileId and never undefined", async ({ page }) => {
    await page.goto("/knowledge-base");

    const workspaceMenu = await openWorkspaceDropdown(page);
    await expect(workspaceMenu.getByRole("menuitem", { name: "AI Coach", exact: true })).toHaveAttribute("href", `/coach/${activeProfileId}`);
    await expect(workspaceMenu.getByRole("menuitem", { name: "Human Potential Map", exact: true })).toHaveAttribute(
      "href",
      `/profile/${activeProfileId}`
    );
    await expect(workspaceMenu.getByRole("menuitem", { name: "My Roadmap", exact: true })).toHaveAttribute("href", `/roadmap/${activeProfileId}`);
    await expect(workspaceMenu.getByRole("menuitem", { name: "Recommendations", exact: true })).toHaveAttribute(
      "href",
      `/recommendations/${activeProfileId}`
    );
    await expectSingleLayoutChrome(page);
  });

  test("1448px smoke routes keep a single shell without horizontal overflow", async ({ page }, testInfo) => {
    testInfo.setTimeout(120_000);

    for (const path of [
      "/",
      "/about",
      "/how-it-works",
      "/principles",
      "/research",
      "/project-roadmap",
      "/blog",
      "/knowledge-base",
      "/diagnostic",
      "/login",
      "/register",
    ]) {
      await page.goto(path);
      await expectNoHorizontalOverflow(page);
      await expectSingleLayoutChrome(page);
    }
  });

  test("theme toggle works in public, workspace, and auth routes", async ({ page }) => {
    for (const path of ["/research", "/knowledge-base", "/login"]) {
      await page.goto(path);
      await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
      await page.getByRole("button", { name: "Switch to light mode" }).click();
      await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
      await page.getByRole("button", { name: "Switch to dark mode" }).click();
      await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    }
  });

  test("floating OrganicAI launcher keeps theme contrast and mobile containment", async ({ page }, testInfo) => {
    testInfo.setTimeout(120_000);
    const launcher = page.locator(".floating-voice-chat__launcher");
    const publicPaths = ["/", "/about", "/how-it-works", "/principles", "/research", "/project-roadmap", "/blog"];

    for (const path of publicPaths) {
      await page.goto(path);
      await page.getByRole("button", { name: "Switch to light mode" }).click();
      await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
      await expect(launcher).toBeVisible();
      const lightColors = await launcher.evaluate((element) => {
        const style = getComputedStyle(element);
        const channels = (value: string) => value.match(/[\d.]+/g)?.slice(0, 3).map(Number) ?? [];
        return {
          text: channels(style.color),
          background: channels(style.backgroundColor),
          backgroundImage: style.backgroundImage,
        };
      });
      expect(Math.max(...lightColors.text)).toBeLessThan(150);
      expect(Math.min(...lightColors.background)).toBeGreaterThan(235);
      expect(lightColors.backgroundImage).toContain("linear-gradient");
      await expectNoHorizontalOverflow(page);
    }

    await page.getByRole("button", { name: "Switch to dark mode" }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    const darkText = await launcher.evaluate((element) =>
      getComputedStyle(element).color.match(/[\d.]+/g)?.slice(0, 3).map(Number) ?? []
    );
    expect(Math.min(...darkText)).toBeGreaterThan(200);

    for (const viewport of [
      { width: 1448, height: 1086 },
      { width: 768, height: 1024 },
      { width: 390, height: 844 },
    ]) {
      await page.setViewportSize(viewport);
      await page.getByRole("button", { name: "Switch to light mode" }).click();
      await expect(launcher).toBeVisible();
      await expectNoHorizontalOverflow(page);
      await page.getByRole("button", { name: "Switch to dark mode" }).click();
    }
  });

  test("390px routes do not create horizontal overflow", async ({ page }) => {
    await page.setViewportSize(mobile);

    for (const path of [
      "/",
      "/about",
      "/how-it-works",
      "/principles",
      "/research",
      "/project-roadmap",
      "/blog",
      "/knowledge-base",
      "/diagnostic",
      "/login",
      "/register",
    ]) {
      await page.goto(path);
      await expectNoHorizontalOverflow(page);
      await expectSingleLayoutChrome(page);
    }
  });
});
