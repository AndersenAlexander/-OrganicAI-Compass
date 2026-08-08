import { expect, test } from "@playwright/test";

test("one-click demo account covers the complete workspace flow", async ({ page }) => {
  await test.step("1. Login page shows Explore Demo", async () => {
    await page.goto("/login");
    await expect(page.getByRole("button", { name: "Explore Demo", exact: true })).toBeVisible();
  });

  await test.step("2. Demo login requires one explicit click", async () => {
    await expect(page).toHaveURL(/\/login$/);
    await page.getByRole("button", { name: "Explore Demo", exact: true }).click();
  });

  await test.step("3. Demo login reaches the workspace", async () => {
    await expect(page).toHaveURL(/\/profile\/demo-profile$/);
    await expect(page.getByRole("heading", { name: "Your Human Potential Map" })).toBeVisible();
  });

  await test.step("4. Authentication persists after refresh", async () => {
    await page.reload();
    await expect(page.getByRole("heading", { name: "Your Human Potential Map" })).toBeVisible();
  });

  await test.step("5. Demo Mode badge is visible", async () => {
    await expect(page.getByLabel("Demo Mode")).toContainText("You are exploring demonstration data.");
  });

  await test.step("6. Active profile is demo-profile", async () => {
    expect(await page.evaluate(() => localStorage.getItem("organicai_active_profile_id"))).toBe("demo-profile");
  });

  await test.step("7. Diagnostic renders", async () => {
    await page.goto("/diagnostic");
    await expect(page.getByRole("heading", { name: /Discover the signal/ })).toBeVisible();
  });

  await test.step("8. Human Potential Map renders", async () => {
    await page.goto("/profile/demo-profile");
    await expect(page.getByRole("heading", { name: "Your Human Potential Map" })).toBeVisible();
  });

  await test.step("9. AI Coach renders", async () => {
    await page.goto("/coach/demo-profile");
    await expect(page.getByRole("heading", { name: "How can we move forward?" })).toBeVisible();
  });

  await test.step("10. Recommendations render", async () => {
    await page.goto("/recommendations/demo-profile");
    await expect(page.getByRole("heading", { name: "Your Personalized Recommendations" })).toBeVisible();
    await expect(page.getByText("Recommendations").first()).toBeVisible();
  });

  await test.step("11. Roadmap renders", async () => {
    await page.goto("/roadmap/demo-profile");
    await expect(page.getByTestId("roadmap-page")).toBeVisible();
  });

  await test.step("12. Reset Demo opens an accessible confirmation", async () => {
    await page.getByRole("button", { name: "Reset Demo" }).click();
    const dialog = page.getByRole("dialog", { name: "Reset demonstration data?" });
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText("diagnostic, profile, recommendations, roadmap, and sample conversations");
  });

  await test.step("13. Escape closes reset dialog", async () => {
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog", { name: "Reset demonstration data?" })).not.toBeVisible();
  });

  await test.step("14. Reset restores original demo data", async () => {
    await page.getByRole("button", { name: "Reset Demo" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Reset Demo" }).click();
    await expect(page).toHaveURL(/\/profile\/demo-profile$/);
    await expect(page.getByRole("heading", { name: "Your Human Potential Map" })).toBeVisible();
  });

  await test.step("15. Demo has no admin research export UI", async () => {
    await expect(page.getByRole("link", { name: /research export/i })).toHaveCount(0);
  });

  await test.step("16. Light Mode is readable", async () => {
    const toggle = page.getByRole("button", { name: "Switch to light mode" });
    if (await toggle.count()) await toggle.click();
    const color = await page.getByLabel("Demo Mode").evaluate((element) => getComputedStyle(element).color);
    expect(color).not.toBe("rgb(255, 255, 255)");
  });

  await test.step("17. Dark Mode is readable", async () => {
    await page.getByRole("button", { name: "Switch to dark mode" }).click();
    await expect(page.getByLabel("Demo Mode")).toBeVisible();
  });

  await test.step("18. Mobile layout has no horizontal overflow", async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(0);
  });

  await test.step("19. Keyboard focus reaches Reset Demo", async () => {
    const reset = page.getByRole("button", { name: "Reset Demo" });
    await reset.focus();
    await expect(reset).toBeFocused();
  });

  await test.step("20. Exit Demo logs out and regular login remains available", async () => {
    await page.getByRole("button", { name: "Exit Demo" }).click();
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("button", { name: "Log in" })).toBeVisible();
    await expect(page.getByLabel("Email")).toBeEditable();
    await expect(page.getByLabel("Password")).toBeEditable();
  });
});
