import { describe, expect, it } from "vitest";
import {
  actionAriaLabel,
  alternativeByType,
  constraintSummary,
  dependencyWarnings,
  fairnessStatusTone,
  fairnessSummary,
  objectiveRows,
  paretoPathStatus,
  provenanceTimeline,
  recommendationBandTone,
  rejectionReasonLabel,
  robustnessTone,
  scoreComponentRows,
  sensitivityMatrixSummary,
  simulationSummary,
  uncertaintyCategorySummary,
} from "./originalityResearchMapping";

const recommendation: any = {
  uncertainty: { primary_category: "capability uncertainty" },
  score_components: {
    positive: { uncertainty_reduction: { value: 0.8, weight: 0.16 } },
    negative: { complexity: { value: 0.4, weight: 0.06 } },
  },
};

const path: any = {
  is_pareto_optimal: false,
  feasibility_status: "partially_feasible",
  constraint_results: [{ status: "satisfied" }, { status: "violated" }, { status: "unknown" }],
  objectives: { transition_duration: 0.5, personal_fit: 0.8 },
  normalised_objectives: { transition_duration: 1, personal_fit: 0.5 },
  objective_directions: { transition_duration: "min", personal_fit: "max" },
};

describe("originality research mapping", () => {
  it("maps recommendation bands and score components without false precision", () => {
    expect(recommendationBandTone("High evidence value")).toBe("success");
    expect(recommendationBandTone("Insufficient information")).toBe("danger");
    expect(scoreComponentRows(recommendation)).toEqual([
      { key: "uncertainty_reduction", direction: "positive", value: 0.8, weight: 0.16 },
      { key: "complexity", direction: "negative", value: 0.4, weight: 0.06 },
    ]);
  });

  it("summarises uncertainty categories and alternatives", () => {
    expect(uncertaintyCategorySummary([recommendation, { ...recommendation, uncertainty: {} }])).toEqual({
      "capability uncertainty": 1,
      Unknown: 1,
    });
    expect(alternativeByType([{ type: "lower_effort_alternative", title: "Short task" } as any], "lower_effort_alternative")?.title).toBe("Short task");
    expect(rejectionReasonLabel("too_expensive")).toBe("Too expensive");
  });

  it("maps Pareto path and objective rows", () => {
    expect(paretoPathStatus(path)).toEqual({ label: "Dominated", tone: "warning" });
    expect(paretoPathStatus({ ...path, feasibility_status: "infeasible_under_hard_constraints" })).toEqual({ label: "Hard constraint violation", tone: "danger" });
    expect(constraintSummary(path)).toEqual({ satisfied: 1, partial: 0, violated: 1, unknown: 1 });
    expect(objectiveRows(path)).toContainEqual({ key: "personal_fit", value: 0.8, direction: "max", normalised: 0.5 });
    expect(simulationSummary({ paths: [path, { ...path, is_pareto_optimal: true }] } as any)).toEqual({ pathCount: 2, paretoCount: 1, dominatedCount: 1 });
  });

  it("maps robustness sensitivity and dependency warnings", () => {
    const run: any = {
      sensitivity_matrix: [{ magnitude_of_effect: "high" }, { magnitude_of_effect: "low" }],
      dependency_flags: [{ explanation: "Market data window matters." }],
      limitations: ["Not proof of correctness."],
      metrics: { maximum_rank_movement: 2, threshold_crossing_count: 1 },
    };
    expect(robustnessTone("highly sensitive")).toBe("danger");
    expect(sensitivityMatrixSummary(run)).toEqual({ testedVariables: 2, highImpact: 1, limitations: 1, maxRankMovement: 2, thresholdCrossings: 1 });
    expect(dependencyWarnings(run)).toEqual(["Market data window matters."]);
  });

  it("maps fairness audit statuses and missing arrays", () => {
    const audit: any = {
      synthetic_only: true,
      results: [{ status: "Passed" }, { status: "Review required" }, { status: "Expected contextual difference" }, { status: "Data limitation" }],
    };
    expect(fairnessStatusTone("Review required")).toBe("danger");
    expect(fairnessSummary(audit)).toEqual({ syntheticOnly: true, passed: 1, reviewRequired: 1, contextual: 1, dataLimitations: 1 });
    expect(fairnessSummary(null)).toEqual({ syntheticOnly: false, passed: 0, reviewRequired: 0, contextual: 0, dataLimitations: 0 });
  });

  it("creates accessible action labels", () => {
    expect(actionAriaLabel("Accept", "Adaptive RAG experiment")).toBe("Accept: Adaptive RAG experiment");
    expect(provenanceTimeline({
      target_type: "adaptive_experiment",
      target_id: "rec-1",
      input_trace: {},
      decision_support_snapshot: { snapshot_id: "snap-1" },
      algorithm_version: "algorithm-v1",
      rule_set_version: "rules-v1",
      source_versions: {},
      change_explanation: "No silent recalculation.",
      available_actions: [],
      limitations: [],
    })).toContainEqual({ label: "Change policy", value: "No silent recalculation." });
  });
});
