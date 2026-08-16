import { expect, test, type Locator, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { expectContrast, luminance, sampleContrast } from "./utils/contrast";

mkdirSync("qa", { recursive: true });

const activeProfileId = "demo-profile";

const viewports = [
  { name: "desktop-1448", width: 1448, height: 1086 },
  { name: "desktop-1366", width: 1366, height: 768 },
  { name: "desktop-1280", width: 1280, height: 800 },
  { name: "tablet-1024", width: 1024, height: 768 },
  { name: "tablet-768", width: 768, height: 1024 },
  { name: "mobile-390", width: 390, height: 844 },
] as const;

const stageTitles = [
  "Set Your Intention",
  "Complete the Human Diagnostic",
  "Generate the Human Potential Map",
  "Talk with the AI Coach",
  "Create a Personalized Roadmap",
  "Reflect, Adapt, and Grow",
];

function parseRgba(value: string): { rgb: [number, number, number]; alpha: number } {
  const normalized = value.trim();
  const channels = normalized.match(/[\d.]+/g)?.map(Number);
  if (!channels || channels.length < 3) return { rgb: [255, 255, 255], alpha: 1 };
  if (normalized.startsWith("color(srgb")) {
    return { rgb: [channels[0] * 255, channels[1] * 255, channels[2] * 255], alpha: channels[3] ?? 1 };
  }
  return { rgb: [channels[0], channels[1], channels[2]], alpha: channels[3] ?? 1 };
}

function parseRgb(value: string): [number, number, number] {
  return parseRgba(value).rgb;
}

function rgbColorsFromCss(...values: string[]) {
  return values.flatMap((value) =>
    (value.match(/rgba?\([^)]+\)|color\(srgb [^)]+\)/g) ?? [])
      .map((color) => parseRgba(color))
      .filter((color) => color.alpha > 0.5)
      .map((color) => color.rgb)
  );
}

async function gotoHowItWorks(page: Page, theme: "light" | "dark" = "light") {
  await page.addInitScript(
    ({ profileId, theme }) => {
      localStorage.setItem("organicai_active_profile_id", profileId);
      localStorage.setItem("organicai-theme", theme);
      localStorage.removeItem("organicai.auth.token");
      localStorage.removeItem("organicai_coach_temp_history");
    },
    { profileId: activeProfileId, theme }
  );

  await page.evaluate(
    ({ profileId, theme }) => {
      localStorage.setItem("organicai_active_profile_id", profileId);
      localStorage.setItem("organicai-theme", theme);
      document.documentElement.dataset.theme = theme;
      document.documentElement.style.colorScheme = theme;
    },
    { profileId: activeProfileId, theme }
  ).catch(() => undefined);

  await page.goto("/how-it-works");
  await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
  await expect(page.locator(".how-it-works-page")).toBeVisible();
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() =>
    Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - window.innerWidth
  );
  expect(overflow).toBeLessThanOrEqual(1);
}

async function expectLightSurface(locator: Locator, label: string) {
  await expect(locator.first()).toBeVisible();
  const styles = await locator.first().evaluate((element) => {
    const computed = getComputedStyle(element);
    return {
      backgroundColor: computed.backgroundColor,
      backgroundImage: computed.backgroundImage,
    };
  });
  const colors = rgbColorsFromCss(styles.backgroundColor, styles.backgroundImage);
  expect(colors.length, `${label} should expose a measurable background`).toBeGreaterThan(0);
  const darkestSurface = Math.min(...colors.map((color) => luminance(color)));
  expect(darkestSurface, `${label} background should be light`).toBeGreaterThan(0.72);
}

async function expectDarkSurface(locator: Locator, label: string) {
  await expect(locator.first()).toBeVisible();
  const styles = await locator.first().evaluate((element) => {
    const computed = getComputedStyle(element);
    return {
      backgroundColor: computed.backgroundColor,
      backgroundImage: computed.backgroundImage,
    };
  });
  const colors = rgbColorsFromCss(styles.backgroundColor, styles.backgroundImage);
  expect(colors.length, `${label} should expose a measurable background`).toBeGreaterThan(0);
  const lightestSurface = Math.max(...colors.map((color) => luminance(color)));
  expect(lightestSurface, `${label} background should stay dark`).toBeLessThan(0.18);
}

async function expectDarkText(locator: Locator, label: string) {
  await expect(locator.first()).toBeVisible();
  const color = await locator.first().evaluate((element) => getComputedStyle(element).color);
  expect(luminance(parseRgb(color)), `${label} should use dark Light Mode text: ${color}`).toBeLessThan(0.25);
}

async function expectLightText(locator: Locator, label: string) {
  await expect(locator.first()).toBeVisible();
  const color = await locator.first().evaluate((element) => getComputedStyle(element).color);
  expect(luminance(parseRgb(color)), `${label} should use light Dark Mode text: ${color}`).toBeGreaterThan(0.65);
}

async function expectLauncherInsideViewport(page: Page) {
  const launcher = page.locator(".floating-voice-chat__launcher").first();
  await expect(launcher).toBeVisible();
  const box = await launcher.boundingBox();
  const viewport = page.viewportSize();
  expect(box, "floating launcher should have a layout box").not.toBeNull();
  expect(viewport, "viewport should be available").not.toBeNull();
  if (!box || !viewport) return;

  expect(box.x).toBeGreaterThanOrEqual(0);
  expect(box.y).toBeGreaterThanOrEqual(0);
  expect(box.x + box.width).toBeLessThanOrEqual(viewport.width + 1);
  expect(box.y + box.height).toBeLessThanOrEqual(viewport.height + 1);
}

async function expectNoInactiveFixedBackdrop(page: Page) {
  const blockers = await page.evaluate(() => {
    const alphaOf = (value: string) => {
      const channels = value.match(/[\d.]+/g)?.map(Number);
      return channels && channels.length >= 4 ? channels[3] : channels && channels.length >= 3 ? 1 : 0;
    };

    return Array.from(document.body.querySelectorAll<HTMLElement>("*"))
      .filter((element) => {
        if (element.closest(".floating-voice-chat")) return false;
        if (element.closest("[data-application-header], [data-app-header-shell], [data-testid='global-header']")) {
          return false;
        }

        const computed = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        if (computed.position !== "fixed") return false;
        if (computed.display === "none" || computed.visibility === "hidden" || computed.pointerEvents === "none") {
          return false;
        }
        if (rect.width < window.innerWidth * 0.82 || rect.height < window.innerHeight * 0.72) return false;

        return alphaOf(computed.backgroundColor) >= 0.2;
      })
      .map((element) => ({
        tag: element.tagName,
        className: String(element.className),
        background: getComputedStyle(element).backgroundColor,
      }));
  });

  expect(blockers, "inactive fixed dark backdrops should not cover the page").toEqual([]);
}

async function expectNonOverlapping(first: Locator, second: Locator, label: string) {
  await expect(first.first()).toBeVisible();
  await expect(second.first()).toBeVisible();
  const [firstBox, secondBox] = await Promise.all([
    first.first().evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    }),
    second.first().evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    }),
  ]);
  expect(firstBox, `${label} first region should have a layout box`).not.toBeNull();
  expect(secondBox, `${label} second region should have a layout box`).not.toBeNull();

  const overlapX = Math.min(firstBox.x + firstBox.width, secondBox.x + secondBox.width) - Math.max(firstBox.x, secondBox.x);
  const overlapY =
    Math.min(firstBox.y + firstBox.height, secondBox.y + secondBox.height) - Math.max(firstBox.y, secondBox.y);
  expect(overlapX <= 1 || overlapY <= 1, `${label} regions should not visually overlap`).toBeTruthy();
}

test.describe("How It Works public page QA", () => {
  test("Light Mode uses readable page surfaces without inactive overlay", async ({ page }) => {
    await page.setViewportSize({ width: 1448, height: 1086 });
    await gotoHowItWorks(page, "light");

    await expect(page.getByTestId("global-header")).toBeVisible();
    await expectNoInactiveFixedBackdrop(page);
    await expectNoHorizontalOverflow(page);

    await expectLightSurface(page.locator(".how-hero"), "hero");
    await expectLightSurface(page.locator(".journey-dashboard"), "journey dashboard");
    await expectLightSurface(page.locator(".journey-stage-preview"), "active stage preview");
    await expectLightSurface(page.locator(".journey-stage-card").first(), "stage card");
    await expectLightSurface(page.locator(".technical-architecture-section"), "technical architecture section");
    await expectLightSurface(page.locator(".rag-journey-section"), "RAG section");
    await expectLightSurface(page.locator(".privacy-control-section"), "privacy section");
    await expectLightSurface(page.locator(".how-final-cta"), "final CTA");
    await expectLightSurface(page.locator(".floating-voice-chat__launcher"), "floating launcher");

    await expectDarkText(page.locator(".how-hero-title"), "hero title");
    await expectDarkText(page.locator(".how-hero-description"), "hero description");
    await expectDarkText(page.locator(".journey-step-button").first(), "journey tab");
    await expectDarkText(page.locator(".journey-preview-copy h3"), "active stage title");
    await expectDarkText(page.locator(".journey-stage-card h3").first(), "stage card title");
    await expectDarkText(page.locator(".pipeline-layer h3").first(), "pipeline title");
    await expectDarkText(page.locator(".rag-card h3").first(), "RAG card title");
    await expectDarkText(page.locator(".privacy-panel h3").first(), "privacy panel title");
    await expectDarkText(page.locator(".floating-voice-chat__launcher"), "floating launcher label");

    await expectContrast(page.locator(".how-hero-description"), 4.5);
    await expectContrast(page.locator(".journey-preview-copy p"), 4.5);
    await expectContrast(page.locator(".journey-chip-cloud span").first(), 4.5);
    await expectContrast(page.locator(".journey-roadmap-mini strong").first(), 4.5);
    await expectContrast(page.locator(".journey-chat-bubble.answer"), 4.5);
    await expectContrast(page.locator(".public-button").first(), 4.5);
    await expectContrast(page.locator(".public-button.secondary").first(), 4.5);
    await expectContrast(page.locator(".journey-action-link").first(), 4.5);
  });

  test("stage navigation remains readable and the visual column does not overlap text", async ({ page }, testInfo) => {
    testInfo.setTimeout(120_000);
    await page.setViewportSize({ width: 1448, height: 1086 });
    await gotoHowItWorks(page, "light");

    const tabs = page.locator(".journey-step-button");
    await expect(tabs).toHaveCount(6);

    for (const [index, title] of stageTitles.entries()) {
      await tabs.nth(index).click();
      await expect(tabs.nth(index)).toHaveAttribute("aria-selected", "true");
      await expect(page.locator(".journey-preview-copy h3")).toContainText(title);
      await expectContrast(page.locator(".journey-preview-copy h3"), 4.5);
      await expectContrast(page.locator(".journey-preview-copy p"), 4.5);
      await expectNonOverlapping(
        page.locator(".journey-preview-copy"),
        page.locator(".journey-stage-preview .journey-visual"),
        `active stage ${index + 1}`
      );
    }

    const cards = page.locator(".journey-stage-card");
    await expect(cards).toHaveCount(6);
    for (let index = 0; index < 6; index += 1) {
      const card = cards.nth(index);
      await expectContrast(card.locator("h3"), 4.5);
      await expectContrast(card.locator("p"), 4.5);
      await expectNonOverlapping(card.locator(".journey-stage-copy"), card.locator(".journey-visual"), `stage card ${index + 1}`);
    }
  });

  test("responsive layouts avoid horizontal overflow and launcher clipping", async ({ page }, testInfo) => {
    testInfo.setTimeout(150_000);
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await gotoHowItWorks(page, "light");

      await expectNoHorizontalOverflow(page);
      await expectLauncherInsideViewport(page);
      await expect(page.locator(".how-hero-title")).toBeVisible();
      await expect(page.locator(".journey-dashboard")).toBeVisible();
      await expect(page.locator(".journey-stage-card").first()).toBeVisible();
      await expectContrast(page.locator(".floating-voice-chat__launcher"), 4.5);

      await expectNonOverlapping(
        page.locator(".journey-preview-copy"),
        page.locator(".journey-stage-preview .journey-visual"),
        `${viewport.name} active preview`
      );

      if (viewport.width <= 390) {
        const [firstCard, secondCard] = await Promise.all([
          page.locator(".journey-stage-card").nth(0).boundingBox(),
          page.locator(".journey-stage-card").nth(1).boundingBox(),
        ]);
        expect(firstCard, "first mobile card should have a box").not.toBeNull();
        expect(secondCard, "second mobile card should have a box").not.toBeNull();
        if (firstCard && secondCard) {
          expect(secondCard.y, "mobile cards should stack vertically").toBeGreaterThan(firstCard.y + firstCard.height - 1);
        }
      }
    }
  });

  test("Dark Mode keeps inverse surfaces and light launcher text", async ({ page }) => {
    await page.setViewportSize({ width: 1448, height: 1086 });
    await gotoHowItWorks(page, "dark");

    await expectNoHorizontalOverflow(page);
    await expectDarkSurface(page.locator(".how-hero"), "dark hero");
    await expectDarkSurface(page.locator(".floating-voice-chat__launcher"), "dark floating launcher");
    await expectLightText(page.locator(".how-hero-title"), "dark hero title");
    await expectLightText(page.locator(".floating-voice-chat__launcher"), "dark floating launcher");

    const launcherSample = await sampleContrast(page.locator(".floating-voice-chat__launcher"));
    expect(launcherSample.ratio, "dark launcher contrast").toBeGreaterThanOrEqual(4.5);
  });

  test("captures requested Light and Dark Mode QA screenshots", async ({ page }, testInfo) => {
    testInfo.setTimeout(120_000);

    for (const [theme, viewport, path] of [
      ["light", { width: 1448, height: 1086 }, "qa/how-it-works-light-1448.png"],
      ["light", { width: 768, height: 1024 }, "qa/how-it-works-light-768.png"],
      ["light", { width: 390, height: 844 }, "qa/how-it-works-light-390.png"],
      ["dark", { width: 1448, height: 1086 }, "qa/how-it-works-dark-1448.png"],
    ] as const) {
      await page.setViewportSize(viewport);
      await gotoHowItWorks(page, theme);
      await expectNoHorizontalOverflow(page);
      await expectLauncherInsideViewport(page);
      await page.screenshot({ path, fullPage: true });
    }
  });
});
