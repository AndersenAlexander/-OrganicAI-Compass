import { describe, expect, it } from "vitest";
import {
  displayHypothesisDimensions,
  prefilledResponseCount,
  prefillStatusCopy,
  skillPrefillIsSelfReported,
} from "./humanDiscoveryJourney";
import type { AssessmentPrefill, CareerMatch } from "../types/assessment";

describe("human discovery journey mapping", () => {
  it("presents career hypotheses as ordered dimensions instead of one opaque score", () => {
    const match = {
      dimension_scores: {
        natural_fit: 82,
        capability_fit: 54,
        evidence_strength: 24,
        transition_feasibility: 67,
        ai_augmentation_opportunity: 73,
      },
      dimension_labels: {
        natural_fit: "Strong fit",
        capability_fit: "Emerging fit",
        evidence_strength: "Limited fit",
        transition_feasibility: "Moderate fit",
        ai_augmentation_opportunity: "Strong fit",
      },
      dimension_explanations: {
        natural_fit: "Uses interests, values, and work-style preferences only.",
        capability_fit: "Uses current skills and experience.",
      },
    } as Pick<CareerMatch, "dimension_scores" | "dimension_labels" | "dimension_explanations" | "hypothesis_dimensions">;

    expect(displayHypothesisDimensions(match)).toEqual([
      expect.objectContaining({ key: "natural_fit", label: "Natural Fit", score: 82, labelText: "Strong fit" }),
      expect.objectContaining({ key: "capability_fit", label: "Capability Fit", score: 54, labelText: "Emerging fit" }),
      expect.objectContaining({ key: "evidence_strength", label: "Evidence Strength", score: 24, labelText: "Limited fit" }),
      expect.objectContaining({ key: "transition_feasibility", label: "Transition Feasibility", score: 67, labelText: "Moderate fit" }),
      expect.objectContaining({ key: "ai_augmentation_opportunity", label: "AI Opportunity", score: 73, labelText: "Strong fit" }),
    ]);
  });

  it("falls back to embedded hypothesis dimensions from the backend source metadata", () => {
    const match = {
      hypothesis_dimensions: {
        scores: { natural_fit: 71 },
        labels: { natural_fit: "Moderate fit" },
        explanations: { natural_fit: "Preference-only signal." },
      },
    } as Pick<CareerMatch, "dimension_scores" | "dimension_labels" | "dimension_explanations" | "hypothesis_dimensions">;

    const [naturalFit, capabilityFit] = displayHypothesisDimensions(match);

    expect(naturalFit).toMatchObject({ key: "natural_fit", score: 71, labelText: "Moderate fit", explanation: "Preference-only signal." });
    expect(capabilityFit).toMatchObject({ key: "capability_fit", score: undefined, labelText: "Not assessed" });
  });

  it("summarises Natural Discovery prefill without treating skills as verified evidence", () => {
    const prefill: AssessmentPrefill = {
      source: "profile.assessment_prefill",
      source_profile_id: "profile-1",
      responses: {
        interests_artistic: 5,
        skills_data_analysis: { level: "beginner", evidence_status: "self_reported", note: "Prefilled from Diagnostic." },
      },
      notes: {
        skills_data_analysis: "Confirm actual current level and add evidence if available.",
      },
      strategy: "prefill_only_user_must_confirm",
    };

    expect(prefilledResponseCount(prefill)).toBe(2);
    expect(prefillStatusCopy(prefill)).toContain("2 previously provided Natural Discovery values");
    expect(skillPrefillIsSelfReported(prefill.responses.skills_data_analysis)).toBe(true);
  });
});
