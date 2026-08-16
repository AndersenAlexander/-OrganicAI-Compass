import { expect, test } from "@playwright/test";

test("service unavailable page hides infrastructure details", async ({ page }) => {
  await page.goto("/service-unavailable?requestId=task13a-safe");
  await expect(page.getByText("OrganicAI Compass is temporarily unavailable. Please try again shortly.")).toBeVisible();
  await expect(page.getByText("task13a-safe")).toBeVisible();
  await expect(page.getByText(/postgres|container|stack trace|database hostname/i)).toHaveCount(0);
});

test("proxy preserves application 401 403 and 422 responses", async ({ request }) => {
  const unauthorized = await request.get("/api/privacy/summary");
  expect(unauthorized.status()).toBe(401);
  expect(await unauthorized.text()).not.toMatch(/postgres|container|stack trace|backend:8020/i);

  const forbidden = await request.get("/api/system/validation/forbidden");
  expect(forbidden.status()).toBe(403);
  const forbiddenBody = await forbidden.json();
  expect(forbiddenBody.error.code).toBe("FORBIDDEN");
  expect(forbidden.headers()["x-request-id"]).toBeTruthy();

  const validation = await request.post("/api/auth/login", { data: {} });
  expect(validation.status()).toBe(422);
  expect(await validation.text()).not.toMatch(/postgres|container|stack trace|backend:8020/i);
});
