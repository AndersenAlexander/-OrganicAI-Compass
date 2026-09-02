import { describe, expect, it } from "vitest";

import { loginFailureMessage } from "./authApi";

function apiError(status?: number, code?: string) {
  return status
    ? { response: { status, data: { error: { code } } } }
    : new Error("Network unavailable");
}

describe("loginFailureMessage", () => {
  it("keeps invalid credentials non-enumerating", () => {
    expect(loginFailureMessage(apiError(401, "UNAUTHORIZED"))).toBe("Login failed. Check your email and password.");
  });

  it("identifies an unavailable database without exposing infrastructure details", () => {
    expect(loginFailureMessage(apiError(503, "DATABASE_UNAVAILABLE"))).toContain("cannot reach its data store");
  });

  it("identifies an unavailable backend", () => {
    expect(loginFailureMessage(apiError())).toContain("backend is running");
  });

  it("identifies a missing login endpoint in development", () => {
    expect(loginFailureMessage(apiError(404, "NOT_FOUND"))).toContain("login endpoint is unavailable");
  });
});
