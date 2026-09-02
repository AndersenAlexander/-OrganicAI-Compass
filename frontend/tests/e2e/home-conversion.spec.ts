import { expect, test, type Page } from "@playwright/test";

const sectionOrder = [
  "home-living-compass",
  "home-platform-intro",
  "home-overview-video",
  "home-product-journey",
  "home-services",
  "home-voice",
  "home-final-conversion",
];

const journeyOrder = ["01 - DISCOVER", "02 - UNDERSTAND", "03 - STRATEGIZE", "04 - CREATE", "05 - GROW"];

async function setTheme(page: Page, value: "dark" | "light") {
  await page.addInitScript((theme) => localStorage.setItem("organicai-theme", theme), value);
}

async function openHome(page: Page) {
  await page.goto("/");
  await expect(page.getByTestId("home-living-compass")).toBeVisible();
}

async function expectNoHorizontalOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}

test.describe("Living Compass homepage journey", () => {
  test("renders the implemented homepage journey in order", async ({ page }) => {
    await setTheme(page, "dark");
    await page.setViewportSize({ width: 1448, height: 1086 });
    await openHome(page);
    for (const testId of sectionOrder) await expect(page.getByTestId(testId)).toBeAttached();
    const positions = await page.evaluate((ids) => ids.map((id) => {
      const element = document.querySelector(`[data-testid="${id}"]`);
      return element ? element.getBoundingClientRect().top + window.scrollY : -1;
    }), sectionOrder);
    for (let index = 1; index < positions.length; index += 1) expect(positions[index]).toBeGreaterThan(positions[index - 1]);
    await expect(page.getByText(/human context before recommendations/i)).toBeVisible();
  });

  test("explains the five compass stages with lazy user-controlled videos", async ({ page }) => {
    await setTheme(page, "dark");
    await openHome(page);
    const labels = await page.locator(".home-compass-section__kicker span").allTextContents();
    expect(labels).toEqual(journeyOrder);
    const videos = page.locator(".home-compass-section video");
    expect(await videos.count()).toBe(5);
    for (const video of await videos.all()) {
      await expect(video).toHaveAttribute("preload", "metadata");
      await expect(video).toHaveAttribute("poster", /^\/images\//);
      expect(await video.evaluate((node: HTMLVideoElement) => node.autoplay)).toBe(true);
    }
  });

  test("keeps voice optional and exposes accountable boundaries", async ({ page }) => {
    await setTheme(page, "dark");
    await openHome(page);
    const hero = page.getByTestId("home-living-compass");
    await expect(hero.getByRole("button", { name: /voice conversation/i }).first()).toBeVisible();
    await expect(page.getByTestId("home-voice").getByRole("heading", { name: /Keep recalibrating/i })).toBeVisible();
    await expect(page.getByTestId("home-final-conversion").getByRole("link", { name: "Start your diagnostic" })).toHaveAttribute("href", "/diagnostic");
  });

  test("keeps the redesigned page contained on desktop and mobile", async ({ page }) => {
    for (const theme of ["dark", "light"] as const) {
      await page.setViewportSize({ width: 1448, height: 1086 });
      await setTheme(page, theme);
      await openHome(page);
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      await expectNoHorizontalOverflow(page);
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await setTheme(page, "light");
    await openHome(page);
    await expectNoHorizontalOverflow(page);
    await expect(page.getByTestId("home-voice").getByRole("heading", { name: /Keep recalibrating/i })).toBeVisible();
  });
});
