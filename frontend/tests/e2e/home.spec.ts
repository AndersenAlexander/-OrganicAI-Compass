import { expect, test, type Page } from "@playwright/test";

const viewports = [
  { width: 1448, height: 1086 },
  { width: 1366, height: 768 },
  { width: 1024, height: 768 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
];

async function theme(page: Page, value: "dark" | "light" = "dark") {
  await page.addInitScript((selected) => localStorage.setItem("organicai-theme", selected), value);
}

async function open(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: /Welcome to OrganicAI Compass/ })).toBeVisible();
}

async function noOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}

test.describe("cinematic OrganicAI homepage", () => {
  test("renders once in the unified global shell with one h1", async ({ page }) => {
    await theme(page);
    await open(page);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("header.no-print")).toHaveCount(1);
    await expect(page.getByTestId("global-header")).toHaveCount(1);
    await expect(page.locator(".organic-gradient-bg > main")).toHaveCount(1);
    await expect(page.getByRole("navigation", { name: "Global navigation" }).getByRole("link", { name: "Home", exact: true })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  test("hero has accessible muted inline video and poster", async ({ page }) => {
    await theme(page);
    await open(page);
    const hero = page.getByTestId("home-video-hero");
    const video = hero.locator("video").first();
    await expect(video).toBeVisible();
    expect(await video.evaluate((node: HTMLVideoElement) => node.muted)).toBeTruthy();
    await expect(video).toHaveAttribute("playsinline", "");
    await expect(video).toHaveAttribute("poster", "/images/organicai-hero-human-ai-bg-v2.png");
    await expect(page.getByRole("button", { name: /background video/ })).toBeVisible();
  });

  test("primary public actions resolve", async ({ page }) => {
    await theme(page);
    await open(page);
    for (const [name, path] of [
      ["Start Your Diagnostic", "/diagnostic"],
      ["See How It Works", "/how-it-works"],
    ]) {
      await expect(page.getByRole("link", { name, exact: true }).first()).toHaveAttribute("href", path);
    }
    await expect(page.getByRole("button", { name: /background video/ })).toBeVisible();
  });

  test("major conversion sections replace the old editorial story page", async ({ page }) => {
    await theme(page);
    await open(page);
    for (const testId of [
      "home-platform-intro",
      "home-overview-video",
      "home-product-journey",
      "home-services",
      "home-voice",
      "home-benefits",
      "home-testimonials",
      "home-trust",
      "home-insights",
      "home-final-conversion",
    ]) {
      await expect(page.getByTestId(testId)).toBeAttached();
    }
    await expect(page.getByRole("heading", { name: /Understand yourself/i }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: /What you can do with OrganicAI Compass/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /You do not always have to navigate/i })).toBeVisible();
    await expect(page.getByText("Technology should strengthen human capacity")).toHaveCount(0);
  });

  test("reduced motion keeps readable poster-only hero", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await theme(page);
    await open(page);
    const hero = page.getByTestId("home-video-hero");
    await expect(hero.locator("source")).toHaveCount(0);
    await expect(hero.locator("video").first()).toHaveAttribute("poster", /organicai-hero/);
    await expect(page.getByTestId("hero-copy")).toBeVisible();
  });

  test("required viewports avoid overflow and page scrolls naturally", async ({ page }) => {
    await theme(page);
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await open(page);
      await noOverflow(page);
    }
    expect(await page.evaluate(() => document.documentElement.scrollHeight / window.innerHeight)).toBeGreaterThan(5);
  });

  test("light and dark themes remain readable", async ({ page }) => {
    await theme(page);
    await open(page);
    for (const value of ["dark", "light"] as const) {
      await page.evaluate((selected) => {
        localStorage.setItem("organicai-theme", selected);
        document.documentElement.dataset.theme = selected;
      }, value);
      await expect(page.locator("html")).toHaveAttribute("data-theme", value);
      const colors = await page.getByTestId("home-platform-intro").evaluate((node) => ({
        text: getComputedStyle(node).color,
        bg: getComputedStyle(node).backgroundColor,
      }));
      expect(colors.text).not.toBe(colors.bg);
    }
  });

  test("captures requested QA screenshots", async ({ page }) => {
    await theme(page);
    await page.setViewportSize({ width: 1448, height: 1086 });
    await open(page);
    await page.screenshot({ path: "qa-home-17c-desktop-dark-top.png" });
    await page.getByTestId("home-voice").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-17c-desktop-dark-middle.png" });
    await page.getByTestId("home-final-conversion").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-17c-desktop-dark-bottom.png" });

    await page.evaluate(() => {
      localStorage.setItem("organicai-theme", "light");
      document.documentElement.dataset.theme = "light";
    });
    await page.getByTestId("home-platform-intro").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-17c-desktop-light-top.png" });
    await page.getByTestId("home-voice").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-17c-desktop-light-middle.png" });
    await page.getByTestId("home-final-conversion").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-17c-desktop-light-bottom.png" });

    await page.setViewportSize({ width: 390, height: 844 });
    await open(page);
    await page.screenshot({ path: "qa-home-17c-mobile-top.png" });
    await page.getByTestId("home-voice").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-17c-mobile-middle.png" });
    await page.getByTestId("home-final-conversion").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-17c-mobile-bottom.png" });
  });
});
