import { expect, test, type Page, type TestInfo } from "@playwright/test";

type Box = {
  x: number;
  y: number;
  width: number;
  height: number;
};

type CompassSnapshot = {
  scrollY: number;
  header: Box | null;
  guide: Box | null;
  hero: Box | null;
  footer: Box | null;
  guideOpacity: number;
  previewOpacity: number;
  guideReleased: string | null;
};

const desktopViewport = { width: 1448, height: 1086 };
const mobileViewport = { width: 390, height: 844 };

function center(box: Box) {
  return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
}

function distance(left: { x: number; y: number }, right: { x: number; y: number }) {
  return Math.hypot(left.x - right.x, left.y - right.y);
}

function requireBox(box: Box | null, label: string): Box {
  expect(box, `${label} should have a measurable box`).not.toBeNull();
  return box!;
}

async function openHome(
  page: Page,
  theme: "light" | "dark" = "light",
  viewport = desktopViewport,
) {
  await page.addInitScript((selected) => localStorage.setItem("organicai-theme", selected), theme);
  await page.setViewportSize(viewport);
  await page.goto("/");
  await expect(page.getByTestId("home-living-compass")).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
  await page.waitForTimeout(900);
}

async function scrollTo(page: Page, top: number) {
  await page.evaluate((value) => window.scrollTo({ top: value, behavior: "instant" }), top);
  await page.waitForTimeout(900);
}

async function snapshot(page: Page): Promise<CompassSnapshot> {
  return page.evaluate(() => {
    const readBox = (selector: string) => {
      const rect = document.querySelector<HTMLElement>(selector)?.getBoundingClientRect();
      return rect
        ? { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
        : null;
    };
    const guideLayer = document.querySelector<HTMLElement>(".living-compass-traveler");
    const preview = document.querySelector<HTMLElement>(".home-compass-hero__preview");

    return {
      scrollY: window.scrollY,
      header: readBox(".brand-compass-anchor .living-compass-logo-mark"),
      guide: readBox(".living-compass-traveler .living-compass-component"),
      hero: readBox('[data-living-compass-anchor="hero"]'),
      footer: readBox('[data-living-compass-anchor="footer"]'),
      guideOpacity: guideLayer ? Number.parseFloat(getComputedStyle(guideLayer).opacity) : Number.NaN,
      previewOpacity: preview ? Number.parseFloat(getComputedStyle(preview).opacity) : Number.NaN,
      guideReleased: guideLayer?.dataset.released ?? null,
    };
  });
}

async function capture(page: Page, testInfo: TestInfo, name: string) {
  await page.screenshot({ path: testInfo.outputPath(`living-compass-${name}.png`) });
}

test.describe("Living Compass scroll geometry", () => {
  test("keeps the header logo static while one guide detaches downward, locks into the hero, and docks at the footer", async ({
    page,
  }, testInfo) => {
    await openHome(page);
    await expect(page.locator(".living-compass-guide-layer")).toHaveCount(1);
    await expect(page.locator('[data-living-compass-traveler="true"]')).toHaveCount(1);
    await expect(page.locator(".home-compass-hero__preview button")).toHaveCount(0);

    const rest = await snapshot(page);
    const restHeader = requireBox(rest.header, "static header logo");
    const restGuide = requireBox(rest.guide, "resting guide");
    expect(rest.guideOpacity).toBeLessThanOrEqual(0.01);
    expect(rest.guideReleased).toBe("false");
    expect(distance(center(restGuide), center(restHeader))).toBeLessThanOrEqual(1);
    await expect(page.locator('[data-living-compass-traveler="true"] .living-compass-component__surface--button')).toHaveCount(0);
    await capture(page, testInfo, "scroll-000-rest");

    await scrollTo(page, 8);
    const earlyDetach = await snapshot(page);
    const earlyGuide = requireBox(earlyDetach.guide, "early detached guide");
    expect(earlyDetach.guideReleased).toBe("true");
    expect(earlyDetach.guideOpacity).toBeGreaterThan(0.9);
    expect(center(earlyGuide).y).toBeGreaterThanOrEqual(center(restGuide).y);
    await expect(page.locator('[data-living-compass-traveler="true"] .living-compass-component__surface--button')).toHaveCount(1);
    await capture(page, testInfo, "scroll-008-early-detach");

    const downwardSamples: CompassSnapshot[] = [earlyDetach];
    for (const scrollY of [32, 96, 240, 480]) {
      await scrollTo(page, scrollY);
      downwardSamples.push(await snapshot(page));
    }
    for (let index = 1; index < downwardSamples.length; index += 1) {
      const previousGuide = requireBox(downwardSamples[index - 1].guide, "previous traveling guide");
      const currentGuide = requireBox(downwardSamples[index].guide, "traveling guide");
      expect(center(currentGuide).y).toBeGreaterThanOrEqual(center(previousGuide).y - 1);
      expect(currentGuide.width).toBeGreaterThanOrEqual(previousGuide.width - 1);
    }
    await capture(page, testInfo, "scroll-480-mid-travel");

    await scrollTo(page, 900);
    await page.waitForTimeout(500);
    const heroLock = await snapshot(page);
    const heroGuide = requireBox(heroLock.guide, "hero guide");
    const heroAnchor = requireBox(heroLock.hero, "hero anchor");
    expect(distance(center(heroGuide), center(heroAnchor))).toBeLessThan(10);
    expect(Math.abs(heroGuide.width - heroAnchor.width)).toBeLessThan(12);
    expect(heroLock.previewOpacity).toBeLessThanOrEqual(0.05);
    await capture(page, testInfo, "scroll-900-hero-lock");

    await scrollTo(page, 1700);
    const heroDetach = await snapshot(page);
    const detachedGuide = requireBox(heroDetach.guide, "hero-detached guide");
    expect(detachedGuide.width).toBeLessThan(heroGuide.width);
    await capture(page, testInfo, "scroll-1700-hero-detach");

    await scrollTo(page, 2500);
    const centralGuideSnapshot = await snapshot(page);
    const centralGuide = requireBox(centralGuideSnapshot.guide, "central journey guide");
    expect(centralGuide.width).toBeGreaterThan(200);
    expect(centralGuide.width).toBeLessThan(270);
    expect(Math.abs(center(centralGuide).x - desktopViewport.width / 2)).toBeLessThan(40);
    await capture(page, testInfo, "scroll-2500-central-guide");

    await page.evaluate(() => window.scrollTo({ top: document.documentElement.scrollHeight, behavior: "instant" }));
    await page.waitForTimeout(1200);
    const footerDock = await snapshot(page);
    const dockedGuide = requireBox(footerDock.guide, "footer-docked guide");
    const footerAnchor = requireBox(footerDock.footer, "footer anchor");
    expect(distance(center(dockedGuide), center(footerAnchor))).toBeLessThan(12);
    expect(Math.abs(dockedGuide.width - footerAnchor.width)).toBeLessThan(8);
    await capture(page, testInfo, "scroll-footer-dock");

    const finalHeader = requireBox(footerDock.header, "static header logo after scrolling");
    expect(distance(center(restHeader), center(finalHeader))).toBeLessThanOrEqual(1);
  });

  test("preserves both themes and a readable reduced-motion guide", async ({ page }) => {
    for (const theme of ["light", "dark"] as const) {
      await openHome(page, theme);
      await expect(page.locator(".brand-compass-anchor .living-compass-logo-mark")).toBeVisible();
      await expect(page.locator(".home-compass-hero__preview")).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
    }

    await page.emulateMedia({ reducedMotion: "reduce" });
    await openHome(page, "light");
    await expect(page.locator(".living-compass-guide-layer")).toHaveAttribute("data-reduced-motion", "true");
    await scrollTo(page, 900);
    const reducedMotionHero = await snapshot(page);
    const guide = requireBox(reducedMotionHero.guide, "reduced-motion hero guide");
    const hero = requireBox(reducedMotionHero.hero, "reduced-motion hero anchor");
    expect(distance(center(guide), center(hero))).toBeLessThan(10);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);

    await openHome(page, "light", mobileViewport);
    await page.getByTestId("home-services").scrollIntoViewIfNeeded();
    await page.waitForTimeout(900);
    const mobileGuideSnapshot = await snapshot(page);
    const mobileGuide = requireBox(mobileGuideSnapshot.guide, "mobile journey guide");
    expect(mobileGuide.width).toBeGreaterThan(96);
    expect(mobileGuide.width).toBeLessThan(132);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  });
});
