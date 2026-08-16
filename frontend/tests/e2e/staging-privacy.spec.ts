import { expect, test } from "@playwright/test";

const baseURL = process.env.STAGING_BASE_URL ?? "http://127.0.0.1:18080";

test("staging rejects unauthenticated privacy API requests", async ({ request }) => {
  const response = await request.get(`${baseURL}/api/privacy/summary`);
  expect(response.status()).toBe(401);
});
