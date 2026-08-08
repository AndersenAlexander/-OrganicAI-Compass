import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const frontendOnlySpecs = new Set([
  "navigation-layouts.spec.ts",
  "header-consistency.spec.ts",
  "workspace-header-auth.spec.ts",
  "blog.spec.ts",
  "about.spec.ts",
  "home.spec.ts",
  "rag-feedback.spec.ts",
  "project-roadmap.spec.ts",
  "research-page.spec.ts",
  "light-mode-visibility.spec.ts",
  "how-it-works.spec.ts",
  "learning-recommendations.spec.ts",
]);
const selectedSpecs = process.argv
  .slice(2)
  .filter((argument) => /\.(spec|test)\.[cm]?[jt]sx?$/.test(argument))
  .map((argument) => path.basename(argument));
const isFrontendOnlyRun =
  process.env.PLAYWRIGHT_FRONTEND_ONLY === "true" ||
  (selectedSpecs.length > 0 && selectedSpecs.every((spec) => frontendOnlySpecs.has(spec)));

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  workers: 1,
  fullyParallel: false,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
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
            command: ".venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
            cwd: "../backend",
            url: "http://127.0.0.1:8000/api/health",
            reuseExistingServer: true,
            timeout: 120_000,
          },
        ]),
    {
      command: "npm run dev -- --host 127.0.0.1",
      cwd: ".",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
