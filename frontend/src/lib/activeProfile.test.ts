import { describe, expect, it } from "vitest";
import { cleanProfileId, getActiveProfileId, profileContextState, profileIdFromPath, selectOwnedProfileId } from "./activeProfile";

describe("active profile resolution", () => {
  it("extracts route profile ids and rejects invalid placeholders", () => {
    expect(profileIdFromPath("/workspace/profile-1/assessment")).toBe("profile-1");
    expect(profileIdFromPath("/profile/profile-2")).toBe("profile-2");
    expect(cleanProfileId("undefined")).toBe("");
    expect(cleanProfileId("null")).toBe("");
  });

  it("does not silently fall back to demo-profile for normal flows", () => {
    expect(getActiveProfileId("/dashboard")).toBe("");
    expect(getActiveProfileId("/dashboard", { allowDemoFallback: true })).toBe("demo-profile");
  });

  it("selects only owned profile ids for normal users", () => {
    expect(selectOwnedProfileId({ routeProfileId: "owned-2", storedProfileId: "owned-1", ownedProfileIds: ["owned-1", "owned-2"], isDemo: false })).toBe("owned-2");
    expect(selectOwnedProfileId({ routeProfileId: "other-user-profile", storedProfileId: "owned-1", ownedProfileIds: ["owned-1"], isDemo: false })).toBe("owned-1");
    expect(selectOwnedProfileId({ routeProfileId: "", storedProfileId: "stale-profile", ownedProfileIds: [], isDemo: false })).toBe("");
  });

  it("allows demo-profile only for explicit demo context", () => {
    expect(selectOwnedProfileId({ routeProfileId: "", storedProfileId: "", ownedProfileIds: [], isDemo: true })).toBe("demo-profile");
    expect(profileContextState({ loading: false, authenticated: true, isDemo: true, profileId: "demo-profile" })).toBe("explicit-demo");
    expect(profileContextState({ loading: false, authenticated: true, isDemo: false, profileId: "" })).toBe("authenticated-no-profile");
  });
});
