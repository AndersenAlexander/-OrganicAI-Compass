import { describe, expect, it } from "vitest";

import { careerReviewOutcome, evidenceProvenanceLabel, linkedGapExplanation } from "./careerEvidenceReview";

const reviewedSession = {
  id: "session-1",
  profile_id: "profile-1",
  experiment_template_id: "human-review-flow",
  mode: "guided",
  status: "evaluated",
  user_confirmed: true,
  confidence_label: "Practical evidence persisted",
  created_at: "2026-08-31T09:00:00Z",
  updated_at: "2026-08-31T09:30:00Z",
  reviews: [],
  result: {
    id: "result-1",
    overall_score: 100,
    overall_label: "Strong evidence",
    criteria_scores: [],
    skills_evaluated: ["ux_ui"],
    strengths: [],
    improvement_areas: [],
    evidence_created: [{ skill_id: "ux_ui", skill_label: "UX/UI", evidence_id: "evidence-1", confidence_label: "Strong evidence", strength_label: "Practically verified" }],
    persistence: { status: "persisted", evidence_ids: ["evidence-1"] },
    linked_gap: {
      intended_gap: { id: "gap-1", skill_id: "ideation", skill_label: "Ideation", status: "MISSING" },
      remaining_unresolved: true,
      message: "This experiment generated evidence for UX/UI, but did not directly verify the linked Ideation gap.",
    },
  },
};

describe("career experiment review UI state", () => {
  it("shows success only after persisted evidence and completed recalibration", () => {
    expect(careerReviewOutcome(reviewedSession, { status: "completed" })).toMatchObject({ ok: true });
  });

  it("does not create optimistic success when persistence is absent", () => {
    expect(careerReviewOutcome({ ...reviewedSession, result: { ...reviewedSession.result, persistence: { status: "no_practical_evidence_generated", evidence_ids: [] } } }, { status: "completed" })).toMatchObject({ ok: false });
  });

  it("does not create optimistic success when recalibration is incomplete", () => {
    expect(careerReviewOutcome(reviewedSession, { status: "awaiting_persisted_evidence" })).toMatchObject({ ok: false });
  });

  it("keeps an unassessed linked gap visible", () => {
    expect(linkedGapExplanation(reviewedSession)).toContain("did not directly verify the linked Ideation gap");
  });

  it("labels deterministic provenance for Evidence Passport", () => {
    expect(evidenceProvenanceLabel("DETERMINISTIC_CAREER_EXPERIMENT")).toBe("Verified through career experiment");
  });
});
