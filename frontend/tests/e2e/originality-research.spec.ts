import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const profileId = "demo-profile";

function adaptiveRecommendation(id: string, title: string, rank: number, status = "recommended") {
  return {
    id,
    run_id: "adaptive-run-1",
    profile_id: profileId,
    experiment_template_id: `template-${rank}`,
    career_experiment_session_id: status === "started" ? "experiment-session-1" : null,
    title,
    experiment_type: "career_experiment_template",
    priority_band: rank === 1 ? "Strong recommendation" : "Moderate recommendation",
    score_band: rank === 1 ? "Strong recommendation" : "Moderate recommendation",
    score_internal: rank === 1 ? 0.68 : 0.54,
    rank_position: rank,
    related_hypotheses: [{ title: "AI Product Designer", role_family: "Design and product" }],
    uncertainty: { primary_category: "capability uncertainty", fit_distinction: "Insufficient evidence is shown as uncertainty, not as low fit or inability." },
    skills_tested: ["ux_ui", "evaluation", "responsible_ai"],
    evidence_expected: ["Portfolio artifact", "Self-review rubric"],
    expected_evidence_gain: { role_specific_or_transferable: "transferable", produces_artifact: true },
    actual_evidence_gain: status === "outcome_recorded" ? { success_not_auto_marked: true, user_reflection: "Useful but partial." } : {},
    estimated_duration: "4-6 hours",
    estimated_effort: "moderate",
    estimated_cost: "low",
    market_relevance: "Linked to active hypotheses",
    cross_path_usefulness: "High",
    accessibility_considerations: ["Can be completed asynchronously"],
    support_options: ["Adviser review"],
    limitations: ["Cannot prove production deployment experience"],
    score_components: {
      positive: { uncertainty_reduction: { value: 0.82, weight: 0.16 }, evidence_importance: { value: 0.7, weight: 0.14 } },
      negative: { complexity: { value: 0.42, weight: 0.06 }, time_cost: { value: 0.35, weight: 0.08 } },
      score_precision_note: "Scores are deterministic decision-support bands, not scientific probability estimates.",
    },
    alternatives: [
      { type: "lower_effort_alternative", title: "Short evidence review", experiment_template_id: "alt-low", reason: "Lower effort.", tradeoff: "Weaker evidence." },
      { type: "higher_evidence_alternative", title: "Portfolio prototype sprint", experiment_template_id: "alt-high", reason: "Higher evidence value.", tradeoff: "More effort." },
      { type: "no_action_reflection", title: "Decision reflection", experiment_template_id: "", reason: "Useful if action is unrealistic.", tradeoff: "No new demonstrated evidence." },
    ],
    data_quality_warnings: [],
    explanation: `Recommended next experiment: ${title}. It tests gaps without treating missing evidence as inability.`,
    status,
    user_confirmation_status: status === "recommended" ? "pending" : status,
    rejection_reason: status === "rejected" ? "too_expensive" : "",
    rejection_feedback: status === "rejected" ? { career_direction_rejected: false } : {},
    roadmap_confirmation_status: "not_requested",
    scoring_version: "adaptive-evidence-gain-score-v1",
    weight_version: "adaptive-evidence-gain-weights-v1",
    created_at: "2026-07-24T09:00:00Z",
    updated_at: "2026-07-24T09:00:00Z",
  };
}

function transitionSimulation(id = "simulation-1", scenarioName = "Balanced transition") {
  const paths = [
    {
      id: "path-1",
      simulation_id: id,
      profile_id: profileId,
      title: "AI Product Designer",
      role_slug: "ai-product-designer",
      path_type: "adjacent_transition",
      objectives: { transition_duration: 0.45, personal_fit: 0.86, market_fit: 0.65, support_fit: 0.7 },
      normalised_objectives: { transition_duration: 1, personal_fit: 1, market_fit: 0.4, support_fit: 1 },
      objective_directions: { transition_duration: "min", personal_fit: "max", market_fit: "max", support_fit: "max" },
      is_pareto_optimal: true,
      dominated_by: [],
      dominated_explanation: "This path is non-dominated under the selected objectives. It is not a universal best path.",
      existing_assets: ["Transferable design evidence"],
      missing_assets: ["One technical artifact"],
      required_experiments: ["Adaptive evidence-gain experiment"],
      required_learning: ["Evaluation module"],
      transition_stages: ["Evidence refresh", "Portfolio artifact"],
      relevant_jobs: ["Fictional role signal only"],
      support_opportunities: ["Adviser review"],
      assumptions: ["Weekly learning capacity remains available"],
      uncertainties: ["Market coverage may change"],
      reversibility: "High",
      next_action: "Run the smallest useful experiment.",
      user_selection_status: "not_selected",
    },
    {
      id: "path-2",
      simulation_id: id,
      profile_id: profileId,
      title: "AI Integration Consultant",
      role_slug: "ai-integration-consultant",
      path_type: "market_aligned_transition",
      objectives: { transition_duration: 0.56, personal_fit: 0.74, market_fit: 0.78, support_fit: 0.66 },
      normalised_objectives: { transition_duration: 0.7, personal_fit: 0.7, market_fit: 1, support_fit: 0.8 },
      objective_directions: { transition_duration: "min", personal_fit: "max", market_fit: "max", support_fit: "max" },
      is_pareto_optimal: true,
      dominated_by: [],
      dominated_explanation: "This path is non-dominated under the selected objectives. It is not a universal best path.",
      existing_assets: ["Consulting narrative"],
      missing_assets: ["Client evidence"],
      required_experiments: ["Stakeholder simulation"],
      required_learning: ["Integration architecture"],
      transition_stages: ["Evidence refresh", "Application preparation"],
      relevant_jobs: ["Fictional role signal only"],
      support_opportunities: ["Adviser review"],
      assumptions: ["Market demand remains comparable"],
      uncertainties: ["Support eligibility is unconfirmed"],
      reversibility: "Moderate",
      next_action: "Compare assumptions.",
      user_selection_status: "not_selected",
    },
    {
      id: "path-3",
      simulation_id: id,
      profile_id: profileId,
      title: "Frontend Developer",
      role_slug: "frontend-developer",
      path_type: "fast_return_variant",
      objectives: { transition_duration: 0.55, personal_fit: 0.7, market_fit: 0.6, support_fit: 0.58 },
      normalised_objectives: { transition_duration: 0.5, personal_fit: 0.4, market_fit: 0.2, support_fit: 0.2 },
      objective_directions: { transition_duration: "min", personal_fit: "max", market_fit: "max", support_fit: "max" },
      is_pareto_optimal: false,
      dominated_by: [{ title: "AI Product Designer" }],
      dominated_explanation: "Frontend Developer is dominated by AI Product Designer because it is equal or better on the selected objectives and stronger on personal fit, support fit.",
      existing_assets: ["React evidence"],
      missing_assets: ["Recent market evidence"],
      required_experiments: ["UI project"],
      required_learning: ["Testing"],
      transition_stages: ["Evidence refresh"],
      relevant_jobs: ["Fictional role signal only"],
      support_opportunities: ["Learning support"],
      assumptions: ["Comparable budget"],
      uncertainties: ["Local opportunity availability may change"],
      reversibility: "Moderate",
      next_action: "Review dominated explanation.",
      user_selection_status: "not_selected",
    },
  ];
  return {
    id,
    profile_id: profileId,
    scenario_name: scenarioName,
    preset: "balanced_transition",
    status: "completed",
    controls: { weekly_learning_time: 8, learning_budget: 50 },
    objective_config: { selected_objectives: ["transition_duration", "personal_fit", "market_fit", "support_fit"], hidden_career_preferences: false },
    input_snapshot: { hypotheses: [] },
    pareto_front: paths.filter((path) => path.is_pareto_optimal).map((path) => ({ title: path.title, role_slug: path.role_slug })),
    paths,
    scenario_comparisons: [],
    explanation: "AI Product Designer and AI Integration Consultant are currently Pareto-optimal. This is a trade-off analysis, not a universal best-career ranking.",
    objective_version: "career-transition-objectives-v1",
    data_coverage: { candidate_paths: 3 },
    limitations: ["Market data is date-bound."],
    saved: true,
    created_at: "2026-07-24T09:00:00Z",
  };
}

function robustnessRun() {
  return {
    id: "robustness-1",
    profile_id: profileId,
    status: "completed",
    input_snapshot: {},
    baseline: [{ title: "AI Product Designer", score: 0.72 }],
    variations: [],
    stability_results: [
      { career_hypothesis: "AI Product Designer", status: "stable recommendation", dependency: "No single dominant dependency" },
      { career_hypothesis: "RAG Application Developer", status: "highly sensitive", dependency: "Market data window" },
    ],
    sensitivity_matrix: [
      { tested_variable: "market_data_window", baseline_value: "30 days", tested_range: "14-90 days", magnitude_of_effect: "high" },
      { tested_variable: "evidence_recency", baseline_value: "current evidence", tested_range: "discount older evidence", magnitude_of_effect: "high" },
    ],
    dependency_flags: [{ variable: "market_data_window", explanation: "This recommendation is highly dependent on local job availability." }],
    metrics: { top_k_overlap: 0.75, rank_stability: 0.74 },
    data_coverage: { data_date: "2026-07-24" },
    limitations: ["Robustness is not proof of correctness."],
    scoring_version: "recommendation-robustness-v1",
    what_could_change: ["This recommendation is highly dependent on local job availability."],
    created_at: "2026-07-24T09:00:00Z",
  };
}

function fairnessAudit() {
  return {
    id: "audit-1",
    status: "completed",
    audit_type: "synthetic_counterfactual_rules",
    synthetic_only: true,
    fixtures: [{ case_id: "gender-marker-invariance" }],
    results: [
      { case_id: "gender-marker-invariance", status: "Passed", rule_or_service_affected: "career recommendation scoring", output_difference: "No material difference.", severity: "none" },
      { case_id: "accessibility-feasibility", status: "Review required", rule_or_service_affected: "Adaptive experiment feasibility", output_difference: "Feasibility changed; demonstrated evidence unchanged.", severity: "medium" },
      { case_id: "location-market-context", status: "Expected contextual difference", rule_or_service_affected: "Market Fit", output_difference: "Market Fit changed; Capability Fit remained unchanged.", severity: "low" },
    ],
    summary: { passed: 1, review_required: 1, real_user_data_included: false },
    system_card_version: "recommendation-system-card-v1",
    reproducibility: { deterministic_seed: "fairness-v1" },
    limitations: ["Synthetic tests do not prove real-world fairness."],
    created_at: "2026-07-24T09:00:00Z",
  };
}

function systemCard() {
  return {
    version: "recommendation-system-card-v1",
    system_purpose: "Decision support for evidence-calibrated career exploration and transition planning.",
    intended_users: ["OrganicAI Compass users"],
    excluded_uses: ["employment guarantees", "psychological diagnosis"],
    input_categories: ["career hypotheses", "Evidence Passport summaries"],
    output_categories: ["experiment recommendations", "Pareto transition paths"],
    deterministic_services: ["adaptive-evidence-gain-score-v1", "career-transition-objectives-v1"],
    ai_assisted_components: ["plain-language explanations"],
    scoring_versions: { adaptive_experiments: "adaptive-evidence-gain-score-v1" },
    known_limitations: ["Not scientifically validated without empirical evaluation."],
    data_dependencies: ["User-confirmed profile data"],
    fairness_considerations: ["Synthetic-only fairness audits"],
    human_oversight: ["No automatic roadmap mutation", "No automatic evidence change"],
    privacy: ["No raw journal export by default"],
    validation_status: "Implemented for deterministic MVP evaluation; not scientifically validated.",
    unresolved_risks: ["Proxy variables require ongoing audit"],
  };
}

async function mockOriginality(page: Page) {
  let recommendations: any[] = [];
  let simulations: any[] = [];
  let robustness: any[] = [];
  let audits: any[] = [];

  await page.addInitScript((id) => {
    localStorage.setItem("organicai_active_profile_id", id);
    localStorage.removeItem("organicai.auth.token");
  }, profileId);

  await page.route((url) => url.pathname.startsWith("/api/"), async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();
    const pathname = url.pathname;

    if (await fulfillMockAuthRoute(route, "demo")) return;
    if (pathname === `/api/profiles/${profileId}`) return route.fulfill({ json: { id: profileId, primary_archetype: "Curious Builder", strengths: [], values: [], fears: [], created_at: "2026-01-01T00:00:00Z" } });
    if (pathname === `/api/profiles/${profileId}/feedback`) return route.fulfill({ json: { confirmed_nodes: [], hidden_recommendations: [], strength_adjustments: {}, archetype_override: null, user_notes: {} } });

    if (pathname === `/api/v1/profiles/${profileId}/adaptive-experiments/analyse`) {
      recommendations = [
        adaptiveRecommendation("adaptive-1", "Evaluate a small RAG application", 1),
        adaptiveRecommendation("adaptive-2", "Create an explainable recommendation card", 2),
      ];
      return route.fulfill({ json: { id: "adaptive-run-1", profile_id: profileId, status: "completed", weight_version: "adaptive-evidence-gain-weights-v1", scoring_version: "adaptive-evidence-gain-score-v1", uncertainty_summary: { missing_evidence_note: "Missing evidence is never interpreted as proof of inability." }, recommendations } });
    }
    if (pathname === `/api/v1/profiles/${profileId}/adaptive-experiments`) return route.fulfill({ json: recommendations });
    if (pathname.startsWith("/api/v1/adaptive-experiments/") && method === "POST") {
      const id = pathname.split("/")[4];
      const action = pathname.split("/")[5];
      recommendations = recommendations.map((item) => item.id === id ? adaptiveRecommendation(id, item.title, item.rank_position, action === "outcome" ? "outcome_recorded" : action === "reject" ? "rejected" : action === "start" ? "started" : action || "accepted") : item);
      return route.fulfill({ json: recommendations.find((item) => item.id === id) });
    }

    if (pathname === "/api/v1/transition-simulations/presets") return route.fulfill({ json: [{ id: "balanced_transition", label: "Balanced transition", objective_priorities: {} }, { id: "fastest_realistic_transition", label: "Fastest realistic transition", objective_priorities: {} }] });
    if (pathname === `/api/v1/profiles/${profileId}/transition-simulations`) {
      if (method === "POST") {
        const created = transitionSimulation(`simulation-${simulations.length + 1}`, simulations.length ? "Increased weekly availability" : "Balanced transition");
        simulations = [created, ...simulations];
        return route.fulfill({ json: created });
      }
      return route.fulfill({ json: simulations });
    }
    if (pathname.includes("/transition-simulations/") && pathname.endsWith("/run")) {
      const created = transitionSimulation(`simulation-${simulations.length + 1}`, "Increased weekly availability");
      simulations = [created, ...simulations];
      return route.fulfill({ json: created });
    }
    if (pathname.includes("/transition-simulations/") && pathname.endsWith("/compare")) return route.fulfill({ json: { simulation_id: "simulation-1", comparisons: [{ front_changed: true, material_changes: ["weekly learning time changed Pareto membership"] }] } });
    if (pathname === "/api/v1/transition-paths/path-1/decision-journal") return route.fulfill({ json: { roadmap_changed: false, journal_entry: { id: "journal-1" } } });
    if (pathname === "/api/v1/transition-paths/path-1/propose-roadmap") return route.fulfill({ json: { roadmap_changed: false, confirmation_required: true } });

    if (pathname === `/api/v1/profiles/${profileId}/recommendation-robustness`) {
      if (method === "POST") {
        robustness = [robustnessRun()];
        return route.fulfill({ json: robustness[0] });
      }
      return route.fulfill({ json: robustness });
    }

    if (pathname === "/api/v1/research/fairness-audits") {
      if (method === "POST") {
        audits = [fairnessAudit()];
        return route.fulfill({ json: audits[0] });
      }
      return route.fulfill({ json: audits });
    }
    if (pathname === "/api/v1/recommendation-system-card") return route.fulfill({ json: systemCard() });

    return route.fulfill({ json: [] });
  });
}

test("adaptive experiment workflow shows uncertainty, alternatives, rejection, start, and outcome boundaries", async ({ page }) => {
  await mockOriginality(page);
  await page.goto(`/workspace/${profileId}/adaptive-experiments`);

  await expect(page.getByRole("heading", { name: /Evidence-gain experiments/ })).toBeVisible();
  await page.getByRole("button", { name: /Analyse next experiment/ }).click();
  await expect(page.getByText("Evaluate a small RAG application").first()).toBeVisible();
  await expect(page.getByText(/Scores are deterministic decision-support bands/)).toBeVisible();
  await expect(page.getByText("Short evidence review")).toBeVisible();

  await page.getByRole("button", { name: /Accept: Evaluate a small RAG application/ }).click();
  await expect(page.getByText(/No automatic roadmap or evidence mutation/)).toBeVisible();
  await page.getByRole("button", { name: /Reject: Create an explainable recommendation card/ }).click();
  await expect(page.getByText(/Career direction was not rejected/)).toBeVisible();
  await page.getByRole("button", { name: /Start experiment/ }).click();
  await expect(page.getByText(/Recommendation start recorded/)).toBeVisible();
  await page.getByRole("button", { name: /Record outcome/ }).click();
  await expect(page.getByText(/Recommendation outcome recorded/)).toBeVisible();
});

test("transition simulator keeps Pareto-optimal and dominated paths visible", async ({ page }) => {
  await mockOriginality(page);
  await page.goto(`/workspace/${profileId}/transition-simulator`);

  await page.getByRole("button", { name: /Run simulation/ }).click();
  await expect(page.getByText("AI Product Designer").first()).toBeVisible();
  await expect(page.getByText("Pareto-optimal").first()).toBeVisible();
  await expect(page.getByText("Dominated").first()).toBeVisible();
  await expect(page.getByText(/not a universal best-career ranking/)).toBeVisible();
  await page.getByRole("button", { name: /Change time/ }).click();
  await expect(page.getByText(/Scenario rerun completed/)).toBeVisible();
  await page.getByRole("button", { name: /Compare/ }).click();
  await expect(page.getByText(/permanent profile was not changed/)).toBeVisible();
  await page.getByRole("button", { name: /Decision Journal/ }).first().click();
  await expect(page.getByText(/Roadmap unchanged/)).toBeVisible();
  await page.getByRole("button", { name: /Propose roadmap/ }).first().click();
  await expect(page.getByText(/User confirmation is still required/)).toBeVisible();
});

test("recommendation robustness displays sensitivity matrix and dependency warnings on mobile", async ({ page }) => {
  await mockOriginality(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/workspace/${profileId}/recommendation-robustness`);

  await page.getByRole("button", { name: /Run robustness analysis/ }).click();
  await expect(page.getByText("AI Product Designer").first()).toBeVisible();
  await expect(page.getByText(/highly dependent on local job availability/)).toBeVisible();
  await expect(page.getByRole("cell", { name: "market data window" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(180);
});

test("fairness lab and system card use synthetic-only audit data and visible limitations", async ({ page }) => {
  await mockOriginality(page);
  await page.goto("/research/robustness-lab");

  await page.getByRole("button", { name: /Run synthetic audit/ }).click();
  await expect(page.getByText("Synthetic Fairness Lab")).toBeVisible();
  await expect(page.getByText("Passed").first()).toBeVisible();
  await expect(page.getByText("Review required").first()).toBeVisible();
  await expect(page.getByText("Expected contextual difference").first()).toBeVisible();
  await expect(page.locator(".innovation-row p", { hasText: /Capability Fit remained unchanged/ })).toBeVisible();
  await expect(page.getByText(/\"synthetic_only\": true/)).toBeVisible();

  await page.goto("/about/recommendation-system-card");
  await expect(page.getByRole("heading", { name: "Recommendation System Card" })).toBeVisible();
  await expect(page.getByText(/not scientifically validated/)).toBeVisible();
  await expect(page.getByText("No automatic roadmap mutation")).toBeVisible();
});
