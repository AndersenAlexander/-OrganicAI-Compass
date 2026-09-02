import { describe, expect, it } from "vitest";

import { demoLoginFailureMessage } from "./demoApi";

function apiError(status?: number, code?: string, message?: string) {
  return status
    ? { response: { status, data: { error: { code, message, requestId: "request-demo-test" } } } }
    : new Error("Network unavailable");
}

describe("demoLoginFailureMessage", () => {
  it("identifies an unreachable configured backend", () => {
    expect(demoLoginFailureMessage(apiError())).toContain("frontend API target");
  });

  it("identifies a Demo data-store failure without exposing configuration", () => {
    const message = demoLoginFailureMessage(apiError(503, "DATABASE_UNAVAILABLE", "The database is temporarily unavailable."));
    expect(message).toContain("cannot prepare its data store");
    expect(message).toContain("request-demo-test");
  });

  it("identifies disabled or missing Demo mode", () => {
    expect(demoLoginFailureMessage(apiError(404, "NOT_FOUND", "Demo mode is disabled."))).toContain("disabled or unavailable");
  });
});
