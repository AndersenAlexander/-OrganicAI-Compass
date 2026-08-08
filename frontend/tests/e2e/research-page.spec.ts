import { expect, test, type Page } from "@playwright/test";

const viewports = [
  { width: 1448, height: 1086 },
  { width: 1366, height: 768 },
  { width: 1024, height: 768 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
] as const;

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.addInitScript((value) => localStorage.setItem("organicai-theme", value), theme);
}

async function expectNoOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

test.describe("Research page", () => {
  for (const viewport of viewports) {
    test(`${viewport.width}x${viewport.height} is readable without horizontal overflow`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await setTheme(page, "dark");
      await page.goto("/research");
      await expect(page.getByRole("heading", { level: 1 })).toHaveText(/Researching human-centred AI guidance/);
      if (viewport.width >= 1280) {
        const navigation = page.getByRole("navigation", { name: "Global navigation" });
        await expect(navigation).toBeVisible();
        await expect(navigation.getByRole("link", { name: "Research", exact: true })).toHaveAttribute("aria-current", "page");
      } else {
        await page.getByRole("button", { name: "Open navigation menu" }).click();
        const navigation = page.getByRole("navigation", { name: "Global mobile navigation" });
        await expect(navigation.getByRole("link", { name: "Research", exact: true })).toHaveAttribute("aria-current", "page");
      }
      await expect(page.locator("header.no-print")).toHaveCount(1);
      await expectNoOverflow(page);
    });
  }

  test("content, statuses, matrix, and CTA routes remain accurate", async ({ page }) => {
    await page.setViewportSize({ width: 1448, height: 1086 });
    await setTheme(page, "dark");
    await page.goto("/research");
    await expect(page.locator(".research-question").filter({ hasText: "RQ1" })).toBeVisible();
    await expect(page.locator(".research-question").filter({ hasText: "RQ4" })).toBeVisible();
    await expect(page.getByRole("table")).toBeVisible();
    await expect(page.getByText("NOT YET MEASURED", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /Open Knowledge Base/ }).first()).toHaveAttribute("href", "/knowledge-base");
    await expect(page.getByRole("link", { name: /View Project Roadmap/ }).last()).toHaveAttribute("href", "/project-roadmap");
    await expect(page.getByRole("link", { name: "Try the Diagnostic" })).toHaveAttribute("href", "/diagnostic");
    await expect(page.locator("canvas")).toHaveCount(1);
  });

  test("desktop and mobile screenshots in dark and light mode", async ({ page }) => {
    await page.setViewportSize({ width: 1448, height: 1086 });
    await setTheme(page, "dark");
    await page.goto("/research");
    await expect(page.locator(".research-scene-core")).toBeVisible();
    await page.screenshot({ path: "qa-research-1448x1086.png" });
    await page.screenshot({ path: "qa-research-full-1448.png", fullPage: true });
    await page.getByRole("button", { name: "Switch to light mode" }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await expectNoOverflow(page);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => localStorage.setItem("organicai-theme", "dark"));
    await page.goto("/research");
    await expect(page.locator(".research-scene-core")).toBeVisible();
    await page.getByRole("button", { name: "Switch to light mode" }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await page.getByRole("button", { name: "Switch to dark mode" }).click();
    await page.screenshot({ path: "qa-research-390x844.png" });
    await page.screenshot({ path: "qa-research-full-390.png", fullPage: true });
    await expect(page.getByRole("table")).toBeHidden();
    await expectNoOverflow(page);
  });
});
