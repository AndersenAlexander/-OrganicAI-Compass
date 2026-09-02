import type { CareerExperimentSession } from "../types/careerResilience";

type Recalibration = { status?: string } | null | undefined;

export function careerReviewOutcome(session: CareerExperimentSession, recalibration: Recalibration) {
  const persistence = session.result?.persistence;
  if (persistence?.status !== "persisted" || !persistence.evidence_ids?.length) {
    return {
      ok: false,
      message: "The deterministic review finished, but practical evidence was not persisted. Please try again.",
    };
  }
  if (recalibration?.status !== "completed") {
    return {
      ok: false,
      message: "Practical evidence was persisted, but career recalibration did not complete. Please try again.",
    };
  }
  return {
    ok: true,
    message: "Practical evidence was persisted in Evidence Passport and career hypotheses were recalibrated.",
  };
}

export function linkedGapExplanation(session: CareerExperimentSession) {
  const linkedGap = session.result?.linked_gap;
  if (!linkedGap?.intended_gap || !linkedGap.remaining_unresolved) return "";
  return linkedGap.message || `This experiment did not directly verify the linked ${linkedGap.intended_gap.skill_label} gap.`;
}

export function evidenceProvenanceLabel(sourceType: string, label?: string) {
  if (label) return label;
  if (sourceType === "DETERMINISTIC_CAREER_EXPERIMENT") return "Verified through career experiment";
  return sourceType.replace(/_/g, " ").toLowerCase();
}
