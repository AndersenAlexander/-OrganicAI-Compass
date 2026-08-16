import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const baseURL = process.env.STAGING_BASE_URL ?? process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:18080";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, "../../../evidence/task13a/screenshots/accessibility");

const viewports = [
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 820, height: 1180 },
  { name: "desktop", width: 1440, height: 1000 },
];

async function assertBasicAccessibility(page: import("@playwright/test").Page) {
  await expect(page.locator("body")).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(overflow).toBeFalsy();
  const target = page.getByRole("button").or(page.getByRole("link")).first();
  if (await target.count()) {
    await target.focus();
    const focused = await page.evaluate(() => Boolean(document.activeElement && document.activeElement !== document.body));
    expect(focused).toBeTruthy();
  }
}

test("staging visual accessibility evidence across themes and viewports", async ({ page }) => {
  test.setTimeout(180_000);
  const loginResponse = await page.context().request.post(`${baseURL}/api/auth/demo-login`);
  expect(loginResponse.ok()).toBeTruthy();
  const login = await loginResponse.json();
  const profileId = login.active_profile_id;
  expect(profileId).toBeTruthy();

  const pages = [
    { name: "login", url: "/demo" },
    { name: "dashboard", url: `/profile/${profileId}` },
    { name: "assessment", url: `/workspace/${profileId}/assessment` },
    { name: "career-compatibility", url: `/workspace/${profileId}/career-compatibility` },
    { name: "privacy-center", url: "/privacy" },
    { name: "settings", url: "/settings" },
    { name: "service-unavailable", url: "/service-unavailable" },
  ];

  for (const theme of ["light", "dark"]) {
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.addInitScript((selectedTheme) => {
        window.localStorage.setItem("organicai-theme", selectedTheme as string);
        document.documentElement.classList.toggle("dark", selectedTheme === "dark");
      }, theme);
      for (const item of pages) {
        await page.goto(`${baseURL}${item.url}`, { waitUntil: "networkidle" });
        await assertBasicAccessibility(page);
        await page.screenshot({
          path: path.join(outDir, `${item.name}-${theme}-${viewport.name}.png`),
          fullPage: true,
        });
      }
    }
  }
});
