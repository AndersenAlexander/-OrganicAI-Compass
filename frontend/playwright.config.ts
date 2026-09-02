import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const frontendOnlySpecs = new Set([
  "navigation-layouts.spec.ts",
  "header-consistency.spec.ts",
  "workspace-header-auth.spec.ts",
  "blog.spec.ts",
  "about.spec.ts",
  "home.spec.ts",
  "home-conversion.spec.ts",
  "living-compass-scroll.spec.ts",
  "home-video-hero.spec.ts",
  "homepage-hero-does-not-steal-scroll.spec.ts",
  "rag-feedback.spec.ts",
  "project-roadmap.spec.ts",
  "research-page.spec.ts",
  "light-mode-visibility.spec.ts",
  "how-it-works.spec.ts",
  "learning-recommendations.spec.ts",
  "career-resilience.spec.ts",
  "career-evidence-cross-page.spec.ts",
  "career-experiment-roadmap-sync.spec.ts",
  "market-application.spec.ts",
  "interview-journey.spec.ts",
  "innovation-extension.spec.ts",
  "originality-research.spec.ts",
  "live-voice.spec.ts",
  "persistence-diagnostics.spec.ts",
  "privacy-center.spec.ts",
  "public-footer.spec.ts",
  "data-export.spec.ts",
  "account-deletion.spec.ts",
  "ephemeral-conversation.spec.ts",
  "provider-privacy-status.spec.ts",
  "email-delivery-status.spec.ts",
  "auth-url-token-cleanup.spec.ts",
  "release-readiness.spec.ts",
  "profile-context.spec.ts",
  "human-diagnostic-v2.spec.ts",
  "journey-persistence.spec.ts",
  "state-propagation.spec.ts",
  "coach-overlap.spec.ts",
  "coach-chat.spec.ts",
  "diagnostic-step2-progression.spec.ts",
]);
const selectedSpecs = process.argv
  .slice(2)
  .filter((argument) => /\.(spec|test)\.[cm]?[jt]sx?$/.test(argument))
  .map((argument) => path.basename(argument));
const isFrontendOnlyRun =
  process.env.PLAYWRIGHT_FRONTEND_ONLY === "true" ||
  (selectedSpecs.length > 0 && selectedSpecs.every((spec) => frontendOnlySpecs.has(spec)));
const frontendPort = process.env.PLAYWRIGHT_FRONTEND_PORT ?? "5191";
const frontendBaseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${frontendPort}`;
const backendPort = process.env.PLAYWRIGHT_BACKEND_PORT ?? "8021";
const backendBaseURL = `http://127.0.0.1:${backendPort}`;
const backendApiBaseURL = process.env.PLAYWRIGHT_API_BASE_URL ?? `${backendBaseURL}/api`;
const backendPython = process.env.PLAYWRIGHT_BACKEND_PYTHON ?? (process.platform === "win32" ? ".venv\\Scripts\\python.exe" : ".venv/bin/python");
const browserChannel = process.env.PLAYWRIGHT_CHANNEL;
const reuseExistingServer = process.env.PLAYWRIGHT_REUSE_EXISTING_SERVER === "true";
// A per-run file avoids a stale SQLite schema masking or blocking a browser
// regression test after a normal Alembic model change.
const defaultPlaywrightDatabaseUrl = `sqlite:///./tmp/playwright-e2e-${process.pid}.db`;

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  workers: 1,
  fullyParallel: false,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: frontendBaseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    ...(browserChannel ? { channel: browserChannel } : {}),
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    // Navigation/header specs mock auth state in-browser and do not need the FastAPI backend.
    // Backend-dependent e2e specs still start both servers unless PLAYWRIGHT_FRONTEND_ONLY=true
    // or every explicitly selected spec is listed in frontendOnlySpecs above.
    ...(isFrontendOnlyRun
      ? []
      : [
          {
            command: `${backendPython} -m uvicorn app.main:app --host 127.0.0.1 --port ${backendPort}`,
            cwd: "../backend",
            env: {
              ...process.env,
              APP_ENV: process.env.APP_ENV ?? "test",
              DATABASE_URL: process.env.PLAYWRIGHT_DATABASE_URL ?? defaultPlaywrightDatabaseUrl,
              DB_AUTO_CREATE_SCHEMA: "true",
              DATABASE_REQUIRE_POSTGRES_IN_PRODUCTION: "false",
              DEMO_ACCOUNT_ENABLED: process.env.DEMO_ACCOUNT_ENABLED ?? "true",
              DEMO_USER_PASSWORD: process.env.DEMO_USER_PASSWORD ?? "Playwright-demo-password-2026!",
              FRONTEND_URL: frontendBaseURL,
              FRONTEND_PUBLIC_URL: frontendBaseURL,
              ALLOWED_ORIGINS: `${frontendBaseURL},http://localhost:${frontendPort}`,
            },
            url: `${backendBaseURL}/api/health`,
            reuseExistingServer,
            timeout: 120_000,
          },
        ]),
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      cwd: ".",
      env: {
        ...process.env,
        VITE_API_BASE_URL: backendApiBaseURL,
        VITE_PROXY_TARGET: backendBaseURL,
      },
      url: frontendBaseURL,
      reuseExistingServer,
      timeout: 120_000,
    },
  ],
});
