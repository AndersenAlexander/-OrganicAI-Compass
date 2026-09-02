import { expect, test, type Page } from "@playwright/test";

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

test.describe("Living Compass media journey", () => {
  test("hero preserves primary CTAs and journey media", async ({ page }) => {
    await setTheme(page, "dark");
    await page.setViewportSize({ width: 1448, height: 1086 });
    await openHome(page);
    await expect(page.getByRole("heading", { level: 1, name: "OrganicAI Compass" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Start diagnostic" }).first()).toHaveAttribute("href", "/diagnostic");
    await expect(page.getByRole("link", { name: "See how it works" }).first()).toHaveAttribute("href", "/how-it-works");
    await expect(page.locator(".home-compass-section video")).toHaveCount(5);
    await expectNoHorizontalOverflow(page);
  });

  test("mobile journey remains contained and voice control remains reachable", async ({ page }) => {
    await setTheme(page, "light");
    await page.setViewportSize({ width: 390, height: 844 });
    await openHome(page);
    await expect(page.getByTestId("home-living-compass").getByRole("button", { name: /voice conversation/i }).first()).toBeVisible();
    await page.getByTestId("home-final-conversion").scrollIntoViewIfNeeded();
    await expect(page.getByTestId("home-final-conversion").getByRole("link", { name: "Start your diagnostic" })).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("reduced motion keeps a readable compass and media posters", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await setTheme(page, "dark");
    await openHome(page);
    await expect(page.getByTestId("home-living-compass")).toBeVisible();
    for (const video of await page.locator(".home-compass-section video").all()) await expect(video).toHaveAttribute("poster", /^\/images\//);
    await expectNoHorizontalOverflow(page);
  });
});
