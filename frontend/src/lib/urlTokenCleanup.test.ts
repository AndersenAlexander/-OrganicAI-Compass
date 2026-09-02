import { describe, expect, it } from "vitest";
import { captureTokenAndCleanSearch } from "./urlTokenCleanup";

describe("url token cleanup", () => {
  it("captures token and removes it from the remaining search string", () => {
    const result = captureTokenAndCleanSearch("?token=raw-secret&next=settings");
    expect(result.token).toBe("raw-secret");
    expect(result.cleanedSearch).toBe("?next=settings");
    expect(result.cleanedSearch).not.toContain("raw-secret");
  });

  it("keeps manual-token fallback when no token exists", () => {
    const result = captureTokenAndCleanSearch("?next=settings");
    expect(result.token).toBe("");
    expect(result.cleanedSearch).toBe("?next=settings");
  });
});
