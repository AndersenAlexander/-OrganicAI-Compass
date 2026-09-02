import { describe, expect, it } from "vitest";
import { coachRequestErrorMessage } from "./CoachContext";

describe("coach request error messages", () => {
  it.each([
    [{ response: { status: 401, data: { detail: "expired" } } }, "session has expired"],
    [{ response: { status: 429, data: { detail: "limited" } } }, "too many requests"],
    [{ response: { status: 422, data: { detail: "invalid" } } }, "could not be sent"],
    [{ response: { status: 503, data: { detail: "offline" } } }, "temporarily unavailable"],
    [{ code: "ECONNABORTED" }, "timed out"],
    [{ code: "ERR_NETWORK" }, "cannot reach"],
  ])("maps %o to an actionable, safe message", (error, expected) => {
    expect(coachRequestErrorMessage(error)).toContain(expected);
  });
});
