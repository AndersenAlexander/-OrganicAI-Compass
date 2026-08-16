import { expect, test, type Page } from "@playwright/test";

async function setTheme(page: Page, value: "dark" | "light") {
  await page.addInitScript((theme) => localStorage.setItem("organicai-theme", theme), value);
}

async function openHome(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: /Welcome to OrganicAI Compass/i })).toBeVisible();
}

async function expectNoHorizontalOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
}

async function expectFullViewportHero(page: Page) {
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  const hero = page.getByTestId("home-video-hero");
  const heroBox = await hero.boundingBox();
  expect(heroBox).not.toBeNull();
  expect(Math.abs(heroBox!.x)).toBeLessThanOrEqual(1);
  expect(Math.abs(heroBox!.width - viewportWidth)).toBeLessThanOrEqual(1);
  expect(Math.abs(heroBox!.x + heroBox!.width - viewportWidth)).toBeLessThanOrEqual(1);
  return heroBox!;
}

async function expectStrictControlPlacement(page: Page) {
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  const heroBox = await expectFullViewportHero(page);
  const prevBox = await page.getByTestId("hero-prev").boundingBox();
  const nextBox = await page.getByTestId("hero-next").boundingBox();
  const paginationBox = await page.locator(".home-video-hero__pagination").boundingBox();

  expect(prevBox).not.toBeNull();
  expect(nextBox).not.toBeNull();
  expect(paginationBox).not.toBeNull();

  const heroCenterY = heroBox.y + heroBox.height / 2;
  expect(Math.abs(prevBox!.y + prevBox!.height / 2 - heroCenterY)).toBeLessThanOrEqual(2);
  expect(Math.abs(nextBox!.y + nextBox!.height / 2 - heroCenterY)).toBeLessThanOrEqual(2);
  expect(prevBox!.x).toBeLessThanOrEqual(42);
  expect(nextBox!.x + nextBox!.width).toBeGreaterThanOrEqual(viewportWidth - 42);

  const paginationCenterX = paginationBox!.x + paginationBox!.width / 2;
  expect(Math.abs(paginationCenterX - viewportWidth / 2)).toBeLessThanOrEqual(2);
  expect(paginationBox!.y).toBeGreaterThan(heroBox.y + heroBox.height - 86);
  expect(paginationBox!.y + paginationBox!.height).toBeLessThanOrEqual(heroBox.y + heroBox.height - 12);
}

test.describe("full-width homepage video hero", () => {
  test("desktop hero spans the viewport, preserves CTAs, and advances manually", async ({ page }) => {
    await setTheme(page, "dark");
    await page.setViewportSize({ width: 1448, height: 1086 });
    await openHome(page);

    const hero = page.getByTestId("home-video-hero");
    await expect(hero).toBeVisible();

    await expectStrictControlPlacement(page);

    await expect(page.getByRole("link", { name: /Start Your Diagnostic/i }).first()).toHaveAttribute("href", "/diagnostic");
    await expect(page.getByRole("link", { name: /See How It Works/i }).first()).toHaveAttribute("href", "/how-it-works");
    await expect(page.getByRole("button", { name: /Pause background video|Play background video/i })).toBeVisible();
    await expect(page.getByTestId("hero-copy").getByText(/Design your future|Understand your potential|Begin with reflection|Turn evidence/i)).toHaveCount(0);

    await expect(page.getByTestId("hero-slide-future-with-ai")).toHaveAttribute("data-active", "true");
    await page.getByTestId("hero-next").click();
    await expect(page.getByRole("heading", { level: 1, name: /Welcome to OrganicAI Compass/i })).toBeVisible();
    await expect(page.getByTestId("hero-slide-human-potential")).toHaveAttribute("data-active", "true");
    await expect(page.getByTestId("hero-pagination-human-potential")).toHaveAttribute("aria-current", "true");
    await expect(page.getByTestId("hero-copy").getByText(/Understand your potential|Before asking AI/i)).toHaveCount(0);

    await page.getByTestId("hero-prev").click();
    await expect(page.getByRole("heading", { level: 1, name: /Welcome to OrganicAI Compass/i })).toBeVisible();

    await expect(page.getByRole("link", { name: /Start Your Diagnostic/i }).first()).toHaveAttribute("href", "/diagnostic");
    await expect(page.getByTestId("home-value-strip")).toBeVisible();
    const stripBox = await page.getByTestId("home-value-strip").boundingBox();
    expect(stripBox?.y).toBeGreaterThan((await hero.boundingBox())?.y ?? 0);
    await expectNoHorizontalOverflow(page);
  });

  test("mobile hero remains full bleed without horizontal overflow", async ({ page }) => {
    await setTheme(page, "light");
    await page.setViewportSize({ width: 390, height: 844 });
    await openHome(page);

    await expectStrictControlPlacement(page);

    await expect(page.getByRole("button", { name: "Next slide" })).toBeVisible();
    await page.getByRole("button", { name: "Next slide" }).click();
    await expect(page.getByRole("heading", { level: 1, name: /Welcome to OrganicAI Compass/i })).toBeVisible();

    await page.getByTestId("home-value-strip").scrollIntoViewIfNeeded();
    await expect(page.getByTestId("home-value-strip").getByText("Understand Yourself")).toBeVisible();
    await expect(page.getByTestId("home-value-strip").getByText("Ground AI in Knowledge")).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("reduced motion uses poster-only slides and disables autoplay sources", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await setTheme(page, "dark");
    await openHome(page);

    const hero = page.getByTestId("home-video-hero");
    await expect(hero.locator("source")).toHaveCount(0);
    await expect(hero.locator("video").first()).toHaveAttribute("poster", "/images/organicai-hero-human-ai-bg-v2.png");
    await expect(page.getByRole("button", { name: "Play background video" })).toBeVisible();
    await page.getByTestId("hero-next").click();
    await expect(page.getByRole("heading", { level: 1, name: /Welcome to OrganicAI Compass/i })).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });
});
