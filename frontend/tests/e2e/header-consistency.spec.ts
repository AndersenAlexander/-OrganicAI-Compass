import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const activeProfileId = "demo-profile";
const desktop = { width: 1448, height: 1086 };
const tablet = { width: 768, height: 1024 };
const mobile = { width: 390, height: 844 };
const expectedGlobalLabels = [
  "Home",
  "About",
  "How It Works",
  "Principles",
  "Research",
  "Project Roadmap",
  "Careers",
  "System Card",
  "Journal",
  "Workspace",
];
const expectedWorkspaceLabels = [
  "Dashboard",
  "Natural Discovery",
  "Human Potential Map",
  "Capability Assessment",
  "Career Hypotheses",
  "Evidence Passport",
  "Career Experiments",
  "Supported Paths",
  "Market Radar",
  "Job Analyzer",
  "Applications",
  "Interview Journey",
  "Panel Interview",
  "STAR Stories",
  "Offer Review",
  "Career Encyclopedia",
  "Adaptive Experiments",
  "Transition Simulator",
  "Decision Journal",
  "Recommendation Robustness",
  "Synthetic Fairness Lab",
  "Advisor Collaboration",
  "Browser Extension",
  "Research Evaluation",
  "Learning Path",
  "Job Loss Support",
  "AI Coach",
  "Recommendations",
  "My Roadmap",
  "Knowledge Base",
  "Privacy Center",
  "Settings",
];
const backendApiRequest = (url: URL) => url.pathname.startsWith("/api/");

const emptyFeedback = {
  confirmed_nodes: [],
  hidden_recommendations: [],
  strength_adjustments: {},
  archetype_override: null,
  user_notes: {},
};

function mockProfile() {
  return {
    id: activeProfileId,
    diagnostic_id: "demo-diagnostic",
    primary_archetype: {
      name: "Curious Explorer",
      summary: "You connect reflection with practical experimentation.",
      confidence: 0.82,
      signals: ["curiosity", "agency"],
    },
    secondary_archetype: {
      name: "Responsible Builder",
      summary: "You prefer transparent, human-led technology.",
      confidence: 0.74,
      signals: ["responsibility"],
    },
    strengths: [{ name: "Systems Thinking", score: 86, explanation: "You notice connections.", evidence: [] }],
    values: [{ name: "Agency", score: 90, evidence: [] }],
    fears: ["Losing human control"],
    creative_tendencies: ["Prototype and reflect"],
    ai_collaboration_style: {
      name: "Co-Creator",
      summary: "Use AI for options while keeping final decisions human-led.",
      strengths: ["Ideation"],
      cautions: ["Verify important outputs"],
      recommended_uses: ["Planning"],
      human_led_decisions: ["Values", "Final decisions"],
    },
    contribution_domains: [{ name: "Human-centred AI", score: 88, explanation: "Strong fit." }],
    recommended_learning_paths: [
      { name: "Responsible AI Practice", level: "Intermediate", duration: "Self-paced", reason: "Supports the profile." },
    ],
    uncertainties: [],
    risk_notes: [],
    ethical_note: "This is an exploratory profile, not a fixed label.",
    user_feedback: emptyFeedback,
    created_at: "2026-01-01T00:00:00Z",
  };
}

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

async function preparePage(page: Page, options: { auth?: "none" | "user" | "demo"; theme?: "light" | "dark" } = {}) {
  const auth = options.auth ?? "user";
  const theme = options.theme ?? "dark";

  await page.addInitScript(
    ({ auth, profileId, theme }) => {
      localStorage.setItem("organicai_active_profile_id", profileId);
      localStorage.setItem("organicai-theme", theme);
      localStorage.removeItem("organicai.auth.token");
    },
    { auth, profileId: activeProfileId, theme }
  );

  await page.route(backendApiRequest, async (route) => {
    const url = new URL(route.request().url());

    if (await fulfillMockAuthRoute(route, auth)) return;

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

    if (url.pathname === `/api/recommendations/profile/${activeProfileId}` || url.pathname === "/api/recommendations/generate") {
      await route.fulfill({ status: 200, json: url.pathname.endsWith("/generate") ? { recommendations: [], context_summary: { profile_signals_used: [], feedback_applied: false }, metadata: {} } : [] });
      return;
    }

    await route.fulfill({ status: 200, json: [] });
  });
}

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate((nextTheme) => {
    localStorage.setItem("organicai-theme", nextTheme);
    document.documentElement.dataset.theme = nextTheme;
  }, theme);
}

function channels(value: string) {
  return value.match(/[\d.]+/g)?.slice(0, 3).map(Number) ?? [];
}

async function expectOneGlobalHeader(page: Page) {
  const header = page.getByTestId("global-header");
  await expect(header).toHaveCount(1);
  await expect(header).toBeVisible();
  await expect(page.locator("header.no-print")).toHaveCount(1);
  await expect(page.locator('[data-testid="public-header"], [data-testid="workspace-header"], [data-testid="auth-header"]')).toHaveCount(0);
  await expect(page.locator('[data-header-variant="public"], [data-header-variant="workspace"], [data-header-variant="auth"]')).toHaveCount(0);
  return header;
}

async function headerShellBox(page: Page) {
  const shell = page.locator("[data-app-header-shell]");
  await expect(shell).toBeVisible();
  const box = await shell.boundingBox();
  expect(box).not.toBeNull();
  return box!;
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

async function expectFirstContentBelowHeader(page: Page) {
  const shell = await headerShellBox(page);
  const firstContent = page.locator(".organic-gradient-bg > main > *").first();
  await expect(firstContent).toBeVisible();
  const contentBox = await firstContent.boundingBox();
  expect(contentBox).not.toBeNull();
  expect(contentBox!.y).toBeGreaterThanOrEqual(shell.y + shell.height - 1);
}

async function desktopGlobalLabels(page: Page) {
  return page
    .locator('[aria-label="Global navigation"] > a, [aria-label="Global navigation"] > .global-header__workspace > button')
    .evaluateAll((nodes) => nodes.map((node) => (node.textContent ?? "").replace(/\s+/g, " ").trim()));
}

async function openWorkspaceDropdown(page: Page) {
  const button = page.getByRole("button", { name: "Workspace" });
  await expect(button).toBeVisible();
  await button.click();
  const menu = page.locator("#global-workspace-dropdown");
  await expect(menu).toBeVisible();
  return menu;
}

test.describe("global application header consistency", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize(desktop);
  });

  test("renders one GlobalHeader across representative public, workspace, and auth routes", async ({ page }) => {
    await preparePage(page);

    for (const path of ["/", "/about", "/blog/human-centred-ai-guidance-beyond-chatbot", "/diagnostic", "/dashboard", "/knowledge-base", "/login"]) {
      await page.goto(path);
      await expectOneGlobalHeader(page);
      await expect(page.getByRole("navigation", { name: "Global navigation" })).toBeVisible();
      await expect(page.getByRole("navigation", { name: "Public navigation" })).toHaveCount(0);
      await expect(page.getByRole("navigation", { name: "Workspace navigation" })).toHaveCount(0);
      expect(await desktopGlobalLabels(page)).toEqual(expectedGlobalLabels);
      await expectNoHorizontalOverflow(page);
    }
  });

  test("keeps the same main labels on Home, Diagnostic, and Dashboard", async ({ page }) => {
    await preparePage(page);

    for (const path of ["/", "/diagnostic", "/dashboard"]) {
      await page.goto(path);
      await expectOneGlobalHeader(page);
      expect(await desktopGlobalLabels(page)).toEqual(expectedGlobalLabels);
    }
  });

  test("Workspace dropdown exposes profile-aware workspace destinations on all route families", async ({ page }) => {
    await preparePage(page);

    for (const path of ["/", "/diagnostic", "/dashboard"]) {
      await page.goto(path);
      const menu = await openWorkspaceDropdown(page);
      await expect(menu.getByRole("menuitem")).toHaveText(expectedWorkspaceLabels);
      await expect(menu.getByRole("menuitem", { name: "Human Potential Map" })).toHaveAttribute("href", `/profile/${activeProfileId}`);
      await expect(menu.getByRole("menuitem", { name: "AI Coach" })).toHaveAttribute("href", `/coach/${activeProfileId}`);
      await expect(menu.getByRole("menuitem", { name: "Recommendations" })).toHaveAttribute("href", `/recommendations/${activeProfileId}`);
      await expect(menu.getByRole("menuitem", { name: "My Roadmap" })).toHaveAttribute("href", `/roadmap/${activeProfileId}`);
      await expect(page.locator('a[href*="/undefined"], a[href*="/null"]')).toHaveCount(0);
    }
  });

  test("active states distinguish public Project Roadmap from workspace My Roadmap", async ({ page }) => {
    await preparePage(page);

    await page.goto("/project-roadmap");
    const globalNav = page.getByRole("navigation", { name: "Global navigation" });
    await expect(globalNav.getByRole("link", { name: "Project Roadmap", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("button", { name: "Workspace" })).not.toHaveClass(/global-header__link--active/);

    await page.goto(`/roadmap/${activeProfileId}`);
    await expect(page.getByRole("button", { name: "Workspace" })).toHaveClass(/global-header__link--active/);
    await expect(globalNav.getByRole("link", { name: "Project Roadmap", exact: true })).not.toHaveAttribute("aria-current", "page");
    const menu = await openWorkspaceDropdown(page);
    await expect(menu.getByRole("menuitem", { name: "My Roadmap" })).toHaveAttribute("aria-current", "page");
  });

  test("right-side account controls are scoped to auth state", async ({ page }) => {
    await preparePage(page, { auth: "none" });
    await page.goto("/");
    let header = await expectOneGlobalHeader(page);
    await expect(header.getByRole("link", { name: "Log in", exact: true })).toBeVisible();
    await expect(header.getByRole("link", { name: "Get Started", exact: true })).toBeVisible();
    await expect(header.getByText("Demo Mode")).toHaveCount(0);
    await expect(header.getByRole("button", { name: /Logout|Exit Demo/ })).toHaveCount(0);

    await page.unroute(backendApiRequest);
    await preparePage(page, { auth: "user" });
    await page.goto("/dashboard");
    header = await expectOneGlobalHeader(page);
    await expect(header.getByRole("link", { name: "Alex", exact: true })).toBeVisible();
    await expect(header.getByRole("button", { name: "Logout" })).toBeVisible();
    await expect(header.getByRole("link", { name: "Log in", exact: true })).toHaveCount(0);
    await expect(header.getByRole("link", { name: "Get Started", exact: true })).toHaveCount(0);

    await page.unroute(backendApiRequest);
    await preparePage(page, { auth: "demo" });
    await page.goto("/dashboard");
    header = await expectOneGlobalHeader(page);
    await expect(header.getByText("Demo Mode", { exact: true })).toBeVisible();
    await expect(header.getByRole("button", { name: "Exit Demo" })).toBeVisible();
    await expect(header.getByRole("link", { name: "Log in", exact: true })).toHaveCount(0);
  });

  test("mobile uses one combined hamburger menu with Explore, Workspace, and Account groups", async ({ page }) => {
    await page.setViewportSize(mobile);
    await preparePage(page);
    await page.goto("/");

    await expectOneGlobalHeader(page);
    await expect(page.getByRole("button", { name: /navigation menu/ })).toHaveCount(1);
    await page.getByRole("button", { name: "Open navigation menu" }).click();
    const panel = page.locator("#global-mobile-navigation");
    await expect(panel).toBeVisible();
    await expect(panel.getByText("Explore", { exact: true })).toBeVisible();
    await expect(panel.getByText("Workspace", { exact: true })).toBeVisible();
    await expect(panel.getByText("Account", { exact: true })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Global mobile navigation" }).getByRole("link", { name: "Journal" })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Global mobile workspace navigation" }).getByRole("link", { name: "AI Coach" })).toHaveAttribute(
      "href",
      `/coach/${activeProfileId}`
    );
    await expect(page.getByRole("navigation", { name: "Public mobile navigation" })).toHaveCount(0);
    await expect(page.getByRole("navigation", { name: "Workspace mobile navigation" })).toHaveCount(0);
    await expectNoHorizontalOverflow(page);
    await expect(page.locator(".floating-voice-chat")).toBeHidden();
  });

  test("fixed geometry, content offset, overflow, and theme readability hold across desktop routes", async ({ page }) => {
    await preparePage(page);

    for (const path of ["/", "/diagnostic", "/dashboard"]) {
      await page.goto(path);
      const shell = await headerShellBox(page);
      expect(Math.round(shell.height)).toBe(82);
      await expectFirstContentBelowHeader(page);
      await page.evaluate(() => window.scrollTo(0, 1200));
      const scrolledShell = await headerShellBox(page);
      expect(Math.abs(scrolledShell.y - shell.y)).toBeLessThanOrEqual(1);
      await expectNoHorizontalOverflow(page);

      for (const theme of ["light", "dark"] as const) {
        await setTheme(page, theme);
        const style = await page.getByRole("navigation", { name: "Global navigation" }).getByRole("link", { name: "Home", exact: true }).evaluate((element) => {
          const computed = getComputedStyle(element);
          return { color: computed.color };
        });
        expect(Math.min(...channels(style.color))).toBeGreaterThan(185);
      }
    }
  });

  test("responsive layouts stay contained at 1448, 768, and 390 widths", async ({ page }, testInfo) => {
    testInfo.setTimeout(180_000);

    await preparePage(page, { theme: "light" });

    for (const viewport of [desktop, tablet, mobile]) {
      await page.setViewportSize(viewport);
      for (const path of ["/", "/about", "/how-it-works", "/principles", "/research", "/project-roadmap", "/blog"]) {
        await page.goto(path);
        await expectOneGlobalHeader(page);
        await expectNoHorizontalOverflow(page);
      }
    }
  });

  test("captures required global header QA screenshots", async ({ page }) => {
    await preparePage(page, { theme: "light" });
    await page.setViewportSize(desktop);

    for (const [path, fileName] of [
      ["/", "qa-global-header-home-1448.png"],
      ["/diagnostic", "qa-global-header-diagnostic-1448.png"],
      ["/dashboard", "qa-global-header-dashboard-1448.png"],
      ["/blog", "qa-global-header-blog-1448.png"],
    ] as const) {
      await page.goto(path);
      await page.screenshot({ path: fileName, fullPage: true });
    }

    await page.setViewportSize(mobile);
    for (const [path, fileName] of [
      ["/", "qa-global-header-home-390.png"],
      ["/diagnostic", "qa-global-header-diagnostic-390.png"],
      ["/dashboard", "qa-global-header-dashboard-390.png"],
    ] as const) {
      await page.goto(path);
      await page.screenshot({ path: fileName, fullPage: true });
      await expectNoHorizontalOverflow(page);
    }
  });
});
