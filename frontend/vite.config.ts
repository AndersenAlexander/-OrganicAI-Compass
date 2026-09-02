import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const proxyTarget = process.env.VITE_PROXY_TARGET ?? "http://127.0.0.1:8020";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5190,
    strictPort: true,
    proxy: {
      "/api": proxyTarget,
      "/media": proxyTarget
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
