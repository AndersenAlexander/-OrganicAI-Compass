import { expect, test, type Page } from "@playwright/test";

const sectionOrder = [
  "home-video-hero",
  "home-value-strip",
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
  "public-footer",
];

const journeyOrder = [
  "01 - NATURAL DISCOVERY",
  "02 - CAREER INTERESTS",
  "03 - HUMAN POTENTIAL",
  "04 - CAPABILITY ASSESSMENT",
  "05 - FOUR-LAYER CAREER MODEL",
  "06 - CAREER HYPOTHESES",
  "07 - CAREER EXPERIMENTS",
  "08 - EVIDENCE PASSPORT",
  "09 - RECALIBRATION",
  "10 - MARKET CONTEXT",
  "11 - APPLICATION JOURNEY",
  "12 - INTERVIEW PREPARATION",
  "13 - DECISION INTELLIGENCE",
];

async function setTheme(page: Page, value: "dark" | "light") {
  await page.addInitScript((theme) => localStorage.setItem("organicai-theme", theme), value);
}

async function openHome(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: /Welcome to OrganicAI Compass/i })).toBeVisible();
}

async function expectNoHorizontalOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}

test.describe("conversion-oriented OrganicAI homepage", () => {
  test("renders the required homepage funnel in order", async ({ page }) => {
    await setTheme(page, "dark");
    await page.setViewportSize({ width: 1448, height: 1086 });
    await openHome(page);

    for (const testId of sectionOrder) {
      await expect(page.getByTestId(testId)).toBeAttached();
    }

    const positions = await page.evaluate((ids) => {
      return ids.map((id) => {
        const element = document.querySelector(`[data-testid="${id}"]`);
        if (!element) return -1;
        return element.getBoundingClientRect().top + window.scrollY;
      });
    }, sectionOrder);

    for (let index = 1; index < positions.length; index += 1) {
      expect(positions[index]).toBeGreaterThan(positions[index - 1]);
    }

    await expect(page.getByText("Technology should strengthen human capacity")).toHaveCount(0);
    await expect(page.getByText(/Artificial intelligence should not define who you are/i)).toHaveCount(0);
  });

  test("explains the real product journey with lazy, user-controlled videos", async ({ page }) => {
    await setTheme(page, "dark");
    await openHome(page);

    const labels = await page
      .getByTestId("home-product-journey")
      .locator(".home-journey-card__label span")
      .allTextContents();
    expect(labels).toEqual(journeyOrder);

    await expect(page.locator('[data-step-id="career-interests"]').getByText("RIASEC-inspired Career Interests")).toBeVisible();
    await expect(page.locator('[data-step-id="capability-assessment"]').getByText("Interest is not capability.")).toBeVisible();
    await expect(page.getByText("Four questions. Four different answers.")).toBeVisible();

    const productVideos = page.locator(".product-demo-video video");
    expect(await productVideos.count()).toBeGreaterThanOrEqual(12);
    for (const video of await productVideos.all()) {
      await expect(video).toHaveAttribute("preload", "none");
      await expect(video).toHaveAttribute("poster", /^\/images\//);
      expect(await video.evaluate((node: HTMLVideoElement) => node.autoplay)).toBe(false);
    }
  });

  test("presents voice as optional coach interaction and opens the real coach panel", async ({ page }) => {
    await setTheme(page, "dark");
    await openHome(page);

    const voice = page.getByTestId("home-voice");
    await voice.scrollIntoViewIfNeeded();
    await expect(voice.getByRole("heading", { name: /You do not always have to navigate/i })).toBeVisible();
    await expect(voice.getByText("Voice is an interaction channel, not a behavioural hiring assessment.")).toBeVisible();
    await expect(voice.getByText("Text remains available, and voice is optional.")).toBeVisible();
    await expect(voice).not.toContainText(/control everything by voice/i);
    await expect(voice).not.toContainText(/analyses personality/i);
    await expect(voice.getByRole("link", { name: /Open full Coach/i })).toHaveAttribute("href", "/diagnostic");

    await page.getByTestId("home-voice-open-coach").click();
    await expect(page.locator('section[aria-label="OrganicAI Coach"]')).toBeVisible();
  });

  test("handles testimonials honestly and connects insights to real blog routes", async ({ page }) => {
    await setTheme(page, "light");
    await openHome(page);

    await expect(page.getByTestId("home-testimonials-empty")).toBeVisible();
    await expect(page.getByTestId("home-testimonials").locator("blockquote")).toHaveCount(0);
    await expect(page.getByText(/fictional users/i)).toBeVisible();

    await expect(page.getByTestId("home-insight-card")).toHaveCount(3);
    const hrefs = await page.getByTestId("home-insight-card").locator("a").evaluateAll((links) =>
      links.map((link) => link.getAttribute("href")),
    );
    expect(hrefs.every((href) => href?.startsWith("/blog/"))).toBe(true);
  });

  test("desktop light, desktop dark and mobile layouts avoid horizontal overflow", async ({ page }) => {
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
    await expect(page.getByTestId("home-voice").getByText("microphone", { exact: true })).toBeVisible();
  });
});
