import { expect, test, type Page } from "@playwright/test";

async function setTheme(page: Page, value: "dark" | "light") {
  await page.addInitScript((theme) => localStorage.setItem("organicai-theme", theme), value);
}

async function openHome(page: Page) {
  await page.goto("/");
  await expect(page.getByTestId("home-living-compass")).toBeVisible();
}

function expectSameScroll(beforeY: number, afterY: number) {
  expect(Math.abs(afterY - beforeY)).toBeLessThanOrEqual(2);
}

async function snapshot(page: Page) {
  return page.evaluate(() => ({
    scrollY: window.scrollY,
    pathname: window.location.pathname,
    search: window.location.search,
    hash: window.location.hash,
  }));
}

test.describe("homepage scroll safety", () => {
  test("navigation and section focus do not change the URL unexpectedly", async ({ page }) => {
    await setTheme(page, "dark");
    await page.setViewportSize({ width: 1448, height: 1086 });
    await openHome(page);
    const before = await snapshot(page);
    await page.getByTestId("home-services").scrollIntoViewIfNeeded();
    await page.getByTestId("home-services").locator("a, button").first().focus();
    const after = await snapshot(page);
    expect(after.pathname).toBe(before.pathname);
    expect(after.search).toBe(before.search);
    expect(after.hash).toBe(before.hash);
    expect(after.scrollY).toBeGreaterThan(before.scrollY);
  });

  test("lower-page interaction keeps focus and scroll stable", async ({ page }) => {
    await setTheme(page, "dark");
    await page.setViewportSize({ width: 1448, height: 1086 });
    await openHome(page);
    await page.getByTestId("home-voice").scrollIntoViewIfNeeded();
    const target = page.getByTestId("home-voice").locator("a, button").first();
    await target.focus();
    const before = await snapshot(page);
    await page.waitForTimeout(500);
    const after = await snapshot(page);
    expectSameScroll(before.scrollY, after.scrollY);
    expect(after.pathname).toBe(before.pathname);
    await expect(target).toBeFocused();
  });

  test("mobile lower sections remain usable without horizontal overflow", async ({ page }) => {
    await setTheme(page, "light");
    await page.setViewportSize({ width: 390, height: 844 });
    await openHome(page);
    await page.getByTestId("home-final-conversion").scrollIntoViewIfNeeded();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
    await expect(page.getByTestId("home-final-conversion").getByRole("link", { name: "Start your diagnostic" })).toBeVisible();
  });

  test("reduced motion remains readable and user-controlled", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await setTheme(page, "dark");
    await openHome(page);
    await expect(page.getByTestId("home-living-compass")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  });
});
