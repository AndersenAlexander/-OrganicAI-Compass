import { expect, test, type Page } from "@playwright/test";

const persistenceStatus = {
  driver: "postgresql",
  reachable: true,
  schemaVersion: "0002_auth_sessions_security",
  headVersion: "0002_auth_sessions_security",
  migrationState: "current",
  productionPostgresRequired: true,
  pool: { enabled: true, sizeConfigured: 5, prePing: true },
  backup: { directoryConfigured: true, latestBackupAvailable: true, retentionDays: 30 },
  integrity: { lastCheckStatus: "not_run" },
  releaseGate: {
    preActivationBackupVerified: true,
    rollbackFallbackAvailable: true,
    legacyOriginalPreserved: true,
    legacyOrphanArchiveVerified: true,
    legacyDataLoss: 0,
    originalDatabaseRole: "immutable evidence",
  },
  requestId: "persistence-request-1",
};

async function mockClipboard(page: Page) {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async (value: string) => localStorage.setItem("copied-persistence-summary", value),
      },
    });
  });
}

async function mockAuth(page: Page) {
  await page.route("**/api/auth/refresh", async (route) =>
    route.fulfill({
      json: {
        access_token: "playwright-memory-access-token",
        token_type: "bearer",
        expires_in: 900,
        user: {
          id: "22222222-2222-4222-8222-222222222222",
          email: "alex@example.test",
          name: "Alex User",
          is_demo: false,
          email_verified_at: "2026-07-27T00:00:00Z",
          account_status: "active",
        },
      },
    }),
  );
  await page.route("**/api/auth/me", async (route) =>
    route.fulfill({
      json: {
        id: "22222222-2222-4222-8222-222222222222",
        email: "alex@example.test",
        name: "Alex User",
        is_demo: false,
        email_verified_at: "2026-07-27T00:00:00Z",
        account_status: "active",
      },
    }),
  );
  await page.route("**/api/auth/sessions", async (route) =>
    route.fulfill({
      json: [
        {
          id: "session-1",
          created_at: "2026-07-27T00:00:00Z",
          last_used_at: "2026-07-27T00:01:00Z",
          expires_at: "2026-08-26T00:00:00Z",
          current_session: true,
          device: "Playwright",
          revoked: false,
        },
      ],
    }),
  );
}

test("settings displays persistence diagnostics and copies sanitized summary", async ({ page }) => {
  await mockAuth(page);
  await mockClipboard(page);
  await page.route("**/api/system/persistence", async (route) => route.fulfill({ json: persistenceStatus }));
  await page.goto("/settings");

  await expect(page.getByRole("heading", { level: 1, name: "Persistence" })).toBeVisible();
  await expect(page.getByText("Database driver", { exact: true })).toBeVisible();
  await expect(page.getByText("postgresql").first()).toBeVisible();
  await expect(page.getByText("Connected").first()).toBeVisible();
  await expect(page.getByText("Schema current").first()).toBeVisible();
  await expect(page.getByText("Backup available").first()).toBeVisible();
  await expect(page.getByText("Integrity not checked").first()).toBeVisible();
  await expect(page.getByText("Legacy remediation simulation", { exact: true })).toBeVisible();
  await expect(page.getByText("Legacy orphan archive", { exact: true })).toBeVisible();
  await expect(page.getByText("Archived orphan messages", { exact: true })).toBeVisible();
  await expect(page.getByText("Pre-activation backup", { exact: true })).toBeVisible();
  await expect(page.getByText("Rollback fallback", { exact: true })).toBeVisible();
  await expect(page.getByText("Active persistence", { exact: true })).toBeVisible();
  await expect(page.getByText("DATABASE_URL")).toHaveCount(0);
  await expect(page.getByText("postgresql://")).toHaveCount(0);
  await expect(page.getByText("organicai-orphan-messages")).toHaveCount(0);

  await page.getByRole("button", { name: "Copy diagnostic summary" }).click();
  await expect(page.getByRole("status")).toContainText("Diagnostic summary copied.");
  const copied = await page.evaluate(() => localStorage.getItem("copied-persistence-summary") || "");
  expect(copied).toContain("Database driver: postgresql");
  expect(copied).toContain("Legacy remediation simulation: passed");
  expect(copied).toContain("Legacy data loss: 0");
  expect(copied).toContain("Active persistence: PostgreSQL");
  expect(copied).not.toContain("DATABASE_URL");
  expect(copied).not.toContain("postgresql://");
  expect(copied).not.toContain("organicai-orphan-messages");
});

test("settings handles backend error, light mode, and mobile layout", async ({ page }) => {
  await mockAuth(page);
  await page.addInitScript(() => localStorage.setItem("organicai-theme", "light"));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/system/persistence", async (route) =>
    route.fulfill({
      status: 503,
      json: { error: { code: "DATABASE_UNAVAILABLE", message: "The database is temporarily unavailable.", requestId: "request-error" } },
    }),
  );
  await page.goto("/settings");
  await expect(page.getByRole("alert")).toContainText("The database is temporarily unavailable.");
  await expect(page.getByRole("button", { name: "Copy diagnostic summary" })).toBeDisabled();
  await expect(page.locator("main")).toBeVisible();
});
