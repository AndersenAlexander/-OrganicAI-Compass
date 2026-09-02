import { expect, test } from "@playwright/test";

test("an existing demo account can login, refresh, logout, and re-login", async ({ page }) => {
  await page.goto("/login");

  await page.getByRole("button", { name: "Explore Demo", exact: true }).click();
  await expect(page).toHaveURL(/\/profile\//);
  await expect(page.getByRole("heading", { name: "Your Human Potential Map" })).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Your Human Potential Map" })).toBeVisible();

  await page.getByTestId("global-header").getByRole("button", { name: "Exit Demo", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);

  await page.getByRole("button", { name: "Explore Demo", exact: true }).click();
  await expect(page).toHaveURL(/\/profile\//);
  await expect(page.getByRole("heading", { name: "Your Human Potential Map" })).toBeVisible();
});
