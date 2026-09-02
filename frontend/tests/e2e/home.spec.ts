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
  await expect(page.getByTestId("home-living-compass")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: "OrganicAI Compass" })).toBeVisible();
}

async function noOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}

test.describe("Living Compass homepage", () => {
  test("renders once in the unified global shell with one h1", async ({ page }) => {
    await theme(page);
    await open(page);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("header.no-print")).toHaveCount(1);
    await expect(page.getByTestId("global-header")).toHaveCount(1);
    await expect(page.getByRole("navigation", { name: "Global navigation" }).getByRole("link", { name: "Home", exact: true })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  test("hero exposes the Living Compass and optional voice control", async ({ page }) => {
    await theme(page);
    await open(page);
    const hero = page.getByTestId("home-living-compass");
    await expect(hero.getByRole("link", { name: "Start diagnostic" })).toHaveAttribute("href", "/diagnostic");
    await expect(hero.getByRole("link", { name: "See how it works" })).toHaveAttribute("href", "/how-it-works");
    await expect(hero.getByRole("button", { name: /voice conversation/i }).first()).toBeVisible();
    await expect(hero.getByText("OrganicAI Coach")).toBeVisible();
    await expect(hero.getByText("READY", { exact: true })).toBeVisible();
  });

  test("hero scenic artwork remains decorative and keeps the copy area usable", async ({ page }) => {
    await theme(page, "light");
    await open(page);
    const artwork = page.locator(".home-compass-hero__artwork");
    await expect(artwork).toHaveCount(1);
    await expect(artwork).toHaveAttribute("aria-hidden", "true");
    const image = artwork.locator("img");
    await expect(image).toHaveAttribute("src", "/images/organicai-hero-guidance-v3.png");
    await expect(image).toHaveAttribute("alt", "");
    await expect.poll(() => image.evaluate((node: HTMLImageElement) => node.naturalWidth)).toBeGreaterThan(1000);
    await expect(page.getByRole("heading", { level: 1, name: "OrganicAI Compass" })).toBeVisible();
    await noOverflow(page);
  });

  test("primary public actions resolve", async ({ page }) => {
    await theme(page);
    await open(page);
    await expect(page.getByRole("link", { name: "Start diagnostic" }).first()).toHaveAttribute("href", "/diagnostic");
    await expect(page.getByRole("link", { name: "See how it works" }).first()).toHaveAttribute("href", "/how-it-works");
  });

  test("implemented compass journey sections remain visible and ordered", async ({ page }) => {
    await theme(page);
    await open(page);
    const sectionIds = ["home-platform-intro", "home-overview-video", "home-product-journey", "home-services", "home-voice", "home-final-conversion"];
    for (const testId of sectionIds) await expect(page.getByTestId(testId)).toBeAttached();
    const positions = await page.evaluate((ids) => ids.map((id) => {
      const element = document.querySelector(`[data-testid="${id}"]`);
      return element ? element.getBoundingClientRect().top + window.scrollY : -1;
    }), sectionIds);
    for (let index = 1; index < positions.length; index += 1) expect(positions[index]).toBeGreaterThan(positions[index - 1]);
    await expect(page.getByRole("heading", { name: /Start with human context/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Keep recalibrating/i })).toBeAttached();
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

  test("captures required Living Compass QA screenshots", async ({ page }) => {
    await theme(page);
    await page.setViewportSize({ width: 1448, height: 1086 });
    await open(page);
    await page.screenshot({ path: "qa-home-week7-desktop-dark-top.png" });
    await page.getByTestId("home-services").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-week7-desktop-dark-middle.png" });
    await page.getByTestId("home-final-conversion").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-week7-desktop-dark-bottom.png" });
    await page.evaluate(() => {
      localStorage.setItem("organicai-theme", "light");
      document.documentElement.dataset.theme = "light";
    });
    await page.getByTestId("home-platform-intro").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "qa-home-week7-desktop-light-top.png" });
    await page.setViewportSize({ width: 390, height: 844 });
    await open(page);
    await page.screenshot({ path: "qa-home-week7-mobile-top.png" });
  });
});
