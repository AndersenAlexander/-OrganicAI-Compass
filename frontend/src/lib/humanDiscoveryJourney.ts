import type { AssessmentPrefill, CareerMatch } from "../types/assessment";

export const hypothesisDimensionOrder = [
  { key: "natural_fit", label: "Natural Fit" },
  { key: "capability_fit", label: "Capability Fit" },
  { key: "evidence_strength", label: "Evidence Strength" },
  { key: "transition_feasibility", label: "Transition Feasibility" },
  { key: "ai_augmentation_opportunity", label: "AI Opportunity" },
] as const;

export type HypothesisDimensionKey = (typeof hypothesisDimensionOrder)[number]["key"];

export function displayHypothesisDimensions(match: Pick<CareerMatch, "dimension_scores" | "dimension_labels" | "dimension_explanations" | "hypothesis_dimensions">) {
  const labels = match.dimension_labels || match.hypothesis_dimensions?.labels || {};
  const scores = match.dimension_scores || match.hypothesis_dimensions?.scores || {};
  const explanations = match.dimension_explanations || match.hypothesis_dimensions?.explanations || {};

  return hypothesisDimensionOrder.map((dimension) => ({
    ...dimension,
    score: scores[dimension.key],
    labelText: labels[dimension.key] || "Not assessed",
    explanation: explanations[dimension.key] || "",
  }));
}

export function prefilledResponseCount(prefill: AssessmentPrefill | null | undefined) {
  return Object.keys(prefill?.responses ?? {}).length;
}

export function prefillStatusCopy(prefill: AssessmentPrefill | null | undefined) {
  const count = prefilledResponseCount(prefill);
  if (!count) return "";
  return `${count} previously provided Natural Discovery values are available for confirmation or editing in this assessment.`;
}

export function skillPrefillIsSelfReported(value: unknown) {
  return Boolean(
    value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      "evidence_status" in value &&
      (value as { evidence_status?: unknown }).evidence_status === "self_reported",
  );
}
