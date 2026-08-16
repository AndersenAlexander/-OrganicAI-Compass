import { describe, expect, it } from "vitest";
import { extractRiasecCareerInterests, riasecStatusCopy } from "./riasecCareerInterests";

const dimensions = {
  realistic: { code: "R", label: "Realistic", description: "Hands-on work.", score: 50, band: "Moderate", direct_items: 1 },
  investigative: { code: "I", label: "Investigative", description: "Research.", score: 100, band: "High", direct_items: 1 },
  artistic: { code: "A", label: "Artistic", description: "Creative work.", score: 100, band: "High", direct_items: 1 },
  social: { code: "S", label: "Social", description: "Helping.", score: 75, band: "High", direct_items: 1 },
  enterprising: { code: "E", label: "Enterprising", description: "Leading.", score: 50, band: "Moderate", direct_items: 1 },
  conventional: { code: "C", label: "Conventional", description: "Structured work.", score: 25, band: "Lower", direct_items: 1 },
};

describe("RIASEC-inspired Career Interests profile parsing", () => {
  it("extracts all six dimensions in stable display order", () => {
    const profile = extractRiasecCareerInterests({
      career_interests: {
        model: "RIASEC-inspired Career Interests",
        rule_set_version: "riasec-career-interests-v1",
        status: "complete",
        dimensions,
        top_pattern: "A-I-S",
        top_dimensions: ["artistic", "investigative", "social"],
      },
    });

    expect(profile?.dimensions.map((item) => item.code)).toEqual(["R", "I", "A", "S", "E", "C"]);
    expect(profile?.topPattern).toBe("A-I-S");
    expect(profile?.dimensions[2]).toMatchObject({ key: "artistic", band: "High", score: 100 });
  });

  it("preserves close-score guidance without turning it into a personality label", () => {
    const profile = extractRiasecCareerInterests({
      career_interests: {
        status: "complete",
        dimensions,
        top_pattern: "A-I-S",
        close_score_notice: "Several interest dimensions are closely balanced.",
      },
    });

    expect(profile?.closeScoreNotice).toContain("closely balanced");
    expect(riasecStatusCopy(profile)).toContain("Natural Discovery career-interest responses");
  });

  it("returns the missing-data copy for legacy profiles without generated scores", () => {
    expect(extractRiasecCareerInterests({})).toBeNull();
    expect(riasecStatusCopy(null)).toBe("Complete Natural Discovery to generate Career Interests.");
  });
});
