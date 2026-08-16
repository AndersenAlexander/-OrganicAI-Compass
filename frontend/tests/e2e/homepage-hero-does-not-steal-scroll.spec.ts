import { expect, test, type Page } from "@playwright/test";

async function setTheme(page: Page, value: "dark" | "light") {
  await page.addInitScript((theme) => localStorage.setItem("organicai-theme", theme), value);
}

async function openHome(page: Page) {
  await page.goto("/");
  await expect(page.getByTestId("home-video-hero")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: /Welcome to OrganicAI Compass/i })).toBeVisible();
}

async function activeSlideTestId(page: Page) {
  return page
    .locator('[data-testid^="hero-slide-"][data-active="true"]')
    .evaluate((element) => element.getAttribute("data-testid") || "");
}

async function waitForNextHeroSlide(page: Page, previousSlide: string) {
  await page.waitForFunction(
    (previous) => {
      const active = Array.from(document.querySelectorAll('[data-testid^="hero-slide-"]')).find(
        (element) => element.getAttribute("data-active") === "true",
      );
      return active?.getAttribute("data-testid") !== previous;
    },
    previousSlide,
    { timeout: 30_000 },
  );
  return activeSlideTestId(page);
}

async function pageSnapshot(page: Page) {
  return page.evaluate(() => {
    const activeElement = document.activeElement;
    return {
      scrollY: window.scrollY,
      pathname: window.location.pathname,
      search: window.location.search,
      hash: window.location.hash,
      activeElementTestId: activeElement?.getAttribute("data-testid") || "",
      activeElementText: (activeElement?.textContent || "").trim().replace(/\s+/g, " "),
    };
  });
}

async function scrollToLowerSection(page: Page, testId: string) {
  const section = page.getByTestId(testId);
  await section.scrollIntoViewIfNeeded();
  await page.waitForTimeout(250);
  const focusTarget = section.locator("a, button").first();
  if (await focusTarget.count()) await focusTarget.focus();
  await expect(page.getByTestId("home-video-hero")).not.toBeInViewport();
}

function expectSameScroll(beforeY: number, afterY: number) {
  expect(Math.abs(afterY - beforeY)).toBeLessThanOrEqual(2);
}

test.describe("homepage hero autoplay scroll safety", () => {
  test("manual arrows and pagination do not move the page or change the URL", async ({ page }) => {
    await setTheme(page, "dark");
    await page.setViewportSize({ width: 1448, height: 1086 });
    await openHome(page);

    const before = await pageSnapshot(page);
    await page.getByTestId("hero-next").click();
    await expect(page.getByTestId("hero-slide-human-potential")).toHaveAttribute("data-active", "true");
    await page.getByTestId("hero-pagination-diagnostic").click();
    await expect(page.getByTestId("hero-slide-diagnostic")).toHaveAttribute("data-active", "true");
    await page.getByTestId("hero-prev").click();
    await expect(page.getByTestId("hero-slide-academic-presentation")).toHaveAttribute("data-active", "true");

    const after = await pageSnapshot(page);
    expectSameScroll(before.scrollY, after.scrollY);
    expect(after.pathname).toBe(before.pathname);
    expect(after.search).toBe(before.search);
    expect(after.hash).toBe(before.hash);
  });

  test("desktop autoplay keeps scroll, focus and URL stable through two slide transitions", async ({ page }) => {
    await setTheme(page, "dark");
    await page.setViewportSize({ width: 1448, height: 1086 });
    await openHome(page);
    await scrollToLowerSection(page, "home-services");

    const before = await pageSnapshot(page);
    const firstSlide = await activeSlideTestId(page);
    const secondSlide = await waitForNextHeroSlide(page, firstSlide);
    await page.waitForTimeout(2200);
    const afterFirst = await pageSnapshot(page);

    expect(secondSlide).not.toBe(firstSlide);
    expectSameScroll(before.scrollY, afterFirst.scrollY);
    expect(afterFirst).toMatchObject({
      pathname: before.pathname,
      search: before.search,
      hash: before.hash,
      activeElementTestId: before.activeElementTestId,
      activeElementText: before.activeElementText,
    });

    const thirdSlide = await waitForNextHeroSlide(page, secondSlide);
    await page.waitForTimeout(2200);
    const afterSecond = await pageSnapshot(page);

    expect(thirdSlide).not.toBe(secondSlide);
    expectSameScroll(before.scrollY, afterSecond.scrollY);
    expect(afterSecond).toMatchObject({
      pathname: before.pathname,
      search: before.search,
      hash: before.hash,
      activeElementTestId: before.activeElementTestId,
      activeElementText: before.activeElementText,
    });
  });

  test("mobile autoplay keeps scroll position stable below the hero", async ({ page }) => {
    await setTheme(page, "light");
    await page.setViewportSize({ width: 390, height: 844 });
    await openHome(page);
    await scrollToLowerSection(page, "home-voice");

    const before = await pageSnapshot(page);
    const firstSlide = await activeSlideTestId(page);
    const secondSlide = await waitForNextHeroSlide(page, firstSlide);
    await page.waitForTimeout(2200);
    const after = await pageSnapshot(page);

    expect(secondSlide).not.toBe(firstSlide);
    expectSameScroll(before.scrollY, after.scrollY);
    expect(after.pathname).toBe(before.pathname);
    expect(after.search).toBe(before.search);
    expect(after.hash).toBe(before.hash);
  });

  test("reduced motion remains poster-only and user-controlled", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await setTheme(page, "dark");
    await openHome(page);

    const hero = page.getByTestId("home-video-hero");
    await expect(hero.locator("source")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Play background video" })).toBeVisible();
  });
});
