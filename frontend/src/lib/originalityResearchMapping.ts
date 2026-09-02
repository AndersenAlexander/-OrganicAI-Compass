import type {
  AdaptiveExperimentAlternative,
  AdaptiveExperimentRecommendation,
  FairnessAudit,
  RecommendationProvenance,
  RobustnessRun,
  TransitionPath,
  TransitionSimulation,
} from "../types/originalityResearch";

export function recommendationBandTone(band = ""): "success" | "warning" | "danger" | "default" {
  if (/high evidence|useful evidence|very strong|strong/i.test(band)) return "success";
  if (/exploratory|low current feasibility|moderate/i.test(band)) return "warning";
  if (/insufficient/i.test(band)) return "danger";
  return "default";
}

export function scoreComponentRows(recommendation: Pick<AdaptiveExperimentRecommendation, "score_components">) {
  const positive = Object.entries(recommendation.score_components?.positive || {}).map(([key, item]) => ({
    key,
    direction: "positive" as const,
    value: Number(item.value ?? 0),
    weight: Number(item.weight ?? 0),
  }));
  const negative = Object.entries(recommendation.score_components?.negative || {}).map(([key, item]) => ({
    key,
    direction: "negative" as const,
    value: Number(item.value ?? 0),
    weight: Number(item.weight ?? 0),
  }));
  return [...positive, ...negative].filter((item) => Number.isFinite(item.value) && Number.isFinite(item.weight));
}

export function uncertaintyCategorySummary(recommendations: AdaptiveExperimentRecommendation[]) {
  const counts: Record<string, number> = {};
  recommendations.forEach((item) => {
    const category = String(item.uncertainty?.primary_category || "Unknown");
    counts[category] = (counts[category] || 0) + 1;
  });
  return counts;
}

export function alternativeByType(alternatives: AdaptiveExperimentAlternative[], type: string) {
  return alternatives.find((item) => item.type === type) || null;
}

export function rejectionReasonLabel(reason = "") {
  const labels: Record<string, string> = {
    too_time_consuming: "Too time-consuming",
    too_expensive: "Too expensive",
    not_accessible: "Not accessible",
    not_relevant: "Not relevant",
    already_completed_elsewhere: "Already completed elsewhere",
    personal_preference: "Personal preference",
    insufficient_explanation: "Insufficient explanation",
    other: "Other",
  };
  return labels[reason] || labels.other;
}

export function paretoPathStatus(path: TransitionPath) {
  if (path.feasibility_status === "infeasible_under_hard_constraints") {
    return { label: "Hard constraint violation", tone: "danger" as const };
  }
  return path.is_pareto_optimal
    ? { label: "Pareto-optimal", tone: "success" as const }
    : { label: "Dominated", tone: "warning" as const };
}

export function constraintSummary(path: TransitionPath | null) {
  const rows = path?.constraint_results || [];
  return {
    satisfied: rows.filter((row) => row.status === "satisfied").length,
    partial: rows.filter((row) => row.status === "partially satisfied").length,
    violated: rows.filter((row) => row.status === "violated").length,
    unknown: rows.filter((row) => row.status === "unknown").length,
  };
}

export function objectiveRows(path: TransitionPath) {
  return Object.entries(path.objectives || {}).map(([key, value]) => ({
    key,
    value: Number(value),
    direction: path.objective_directions?.[key] || "unknown",
    normalised: Number(path.normalised_objectives?.[key] ?? 0),
  }));
}

export function simulationSummary(simulation: TransitionSimulation | null) {
  const paths = simulation?.paths || [];
  return {
    pathCount: paths.length,
    paretoCount: paths.filter((path) => path.is_pareto_optimal).length,
    dominatedCount: paths.filter((path) => !path.is_pareto_optimal).length,
  };
}

export function robustnessTone(status = ""): "success" | "warning" | "danger" | "default" {
  if (/stable/i.test(status)) return "success";
  if (/moderately|data-limited/i.test(status)) return "warning";
  if (/highly|insufficient/i.test(status)) return "danger";
  return "default";
}

export function sensitivityMatrixSummary(run: RobustnessRun | null) {
  const rows = run?.sensitivity_matrix || [];
  return {
    testedVariables: rows.length,
    highImpact: rows.filter((row) => /high/i.test(String(row.magnitude_of_effect))).length,
    limitations: run?.limitations?.length || 0,
    maxRankMovement: Number(run?.metrics?.maximum_rank_movement ?? 0),
    thresholdCrossings: Number(run?.metrics?.threshold_crossing_count ?? 0),
  };
}

export function dependencyWarnings(run: RobustnessRun | null) {
  return (run?.dependency_flags || []).map((flag) => String(flag.explanation || flag.variable || "Dependency warning"));
}

export function fairnessStatusTone(status = ""): "success" | "warning" | "danger" | "default" {
  if (/passed/i.test(status)) return "success";
  if (/expected contextual|data limitation|not applicable/i.test(status)) return "warning";
  if (/review|required|possible/i.test(status)) return "danger";
  return "default";
}

export function fairnessSummary(audit: FairnessAudit | null) {
  const results = audit?.results || [];
  return {
    syntheticOnly: Boolean(audit?.synthetic_only),
    passed: results.filter((item) => item.status === "Passed").length,
    reviewRequired: results.filter((item) => /Review required|Possible unjustified/i.test(String(item.status))).length,
    contextual: results.filter((item) => item.status === "Expected contextual difference").length,
    dataLimitations: results.filter((item) => item.status === "Data limitation").length,
  };
}

export function actionAriaLabel(action: string, target: string) {
  return `${action}: ${target}`.replace(/\s+/g, " ").trim();
}

export function provenanceTimeline(provenance: RecommendationProvenance | null) {
  if (!provenance) return [];
  const snapshot = provenance.decision_support_snapshot || {};
  return [
    { label: "Input snapshot", value: String(snapshot.snapshot_id || provenance.target_id) },
    { label: "Rule set", value: provenance.rule_set_version },
    { label: "Algorithm", value: provenance.algorithm_version },
    { label: "Change policy", value: provenance.change_explanation },
  ];
}
