import { describe, expect, test } from "vitest";
import {
  buildHomeRoute,
  homeJourneySteps,
  homeServiceGroups,
  homeVideoAssets,
  homeVoiceBoundaries,
  homeVoiceExamples,
} from "./homeConversionContent";

describe("homepage conversion content", () => {
  test("keeps the 13-step OrganicAI product journey in order", () => {
    expect(homeJourneySteps.map((step) => step.shortLabel)).toEqual([
      "Natural Discovery",
      "Career Interests",
      "Human Potential",
      "Capability Assessment",
      "Four-Layer Model",
      "Career Hypotheses",
      "Career Experiments",
      "Evidence Passport",
      "Recalibration",
      "Market Context",
      "Application Journey",
      "Interview Journey",
      "Decision Intelligence",
    ]);
  });

  test("keeps services grouped instead of creating tiny capability cards", () => {
    expect(homeServiceGroups).toHaveLength(8);
    expect(homeServiceGroups.map((group) => group.title)).toContain("AI Support");
    expect(homeServiceGroups.flatMap((group) => group.capabilities)).toContain("Voice interaction");
  });

  test("uses public video paths and lazy-compatible video metadata", () => {
    for (const video of Object.values(homeVideoAssets)) {
      expect(video.src).toMatch(/^\/videos\/home\//);
      expect(video.poster).toMatch(/^\/images\//);
      expect(video.title).toBeTruthy();
    }
  });

  test("voice copy presents voice as optional interaction, not assessment", () => {
    expect(homeVoiceExamples).toHaveLength(4);
    expect(homeVoiceExamples.join(" ")).not.toMatch(/control everything/i);
    expect(homeVoiceBoundaries.join(" ")).toMatch(/interaction channel/i);
    expect(homeVoiceBoundaries.join(" ")).toMatch(/optional/i);
    expect(homeVoiceBoundaries.join(" ")).toMatch(/protected attributes/i);
  });

  test("profile-aware routes never produce undefined or null", () => {
    for (const routeKey of homeJourneySteps.map((step) => step.routeKey)) {
      expect(buildHomeRoute(routeKey, "")).not.toMatch(/undefined|null/);
      expect(buildHomeRoute(routeKey, "demo-profile")).not.toMatch(/undefined|null/);
    }
  });
});
