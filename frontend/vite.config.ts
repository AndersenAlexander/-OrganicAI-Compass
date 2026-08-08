import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/media": "http://localhost:8000"
    }
  },
  test: {
    // Playwright specs live under tests/e2e and are executed by npm run test:e2e, not Vitest.
    // The repository currently has no Vitest unit specs, so passWithNoTests keeps npm test useful
    // without masking e2e failures.
    exclude: ["node_modules/**", "dist/**", "tests/e2e/**"],
    passWithNoTests: true
  }
});
