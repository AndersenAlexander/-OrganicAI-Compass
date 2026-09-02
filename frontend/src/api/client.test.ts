import { afterEach, describe, expect, it, vi } from "vitest";

import { extractApiError } from "./client";

afterEach(() => vi.unstubAllGlobals());

describe("extractApiError", () => {
  it("does not attach a stale stored request ID to a current error", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => "stale-request-id",
      setItem: () => undefined,
    });

    const result = extractApiError({
      response: {
        status: 503,
        headers: {},
        data: { error: { code: "DATABASE_UNAVAILABLE", message: "The database is temporarily unavailable." } },
      },
    });

    expect(result.requestId).toBe("");
  });

  it("uses the request ID returned by the current response", () => {
    const result = extractApiError({
      response: {
        status: 503,
        headers: { "x-request-id": "current-request-id" },
        data: { error: { code: "DATABASE_UNAVAILABLE", message: "The database is temporarily unavailable." } },
      },
    });

    expect(result.requestId).toBe("current-request-id");
  });
});
