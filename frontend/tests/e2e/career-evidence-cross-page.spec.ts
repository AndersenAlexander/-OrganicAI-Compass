import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const profileId = "evidence-consistency-profile";
const direction = "Human-Centred AI Product Designer";
const verifiedSkills = ["Ideation", "UX/UI", "Product Thinking", "Responsible AI", "Risk Reasoning", "Communication"];

const match = {
  id: "match-human-centred-ai-product-designer",
  session_id: "assessment-session",
  profile_id: profileId,
  role_template_id: "human_centred_ai_product_designer",
  category: "adjacent_professional_roles",
  title: direction,
  role_family: "AI Product Designer",
  description: "Design human-centred AI products.",
  alignment_score: 84,
  alignment_label: "Strong alignment",
  explanation: "The current canonical hypothesis is supported by practical evidence.",
  supporting_factors: ["Practical evidence is current."],
  conflicting_factors: [],
  missing_skills: [],
  transferable_skills: [],
  ai_opportunities: ["Use reviewable AI-assisted workflows."],
  next_step: "Choose a user-controlled next step.",
  transition_difficulty: "moderate",
  time_horizon: "3-6 months",
  status: "saved",
  assumptions: [],
  limitations: [],
  source_metadata: {},
  hypothesis_dimensions: {
    scores: { natural_fit: 80, capability_fit: 76, evidence_strength: 82, transition_feasibility: 66, ai_augmentation_opportunity: 78 },
    labels: { natural_fit: "Strong fit", capability_fit: "Strong fit", evidence_strength: "Strong fit", transition_feasibility: "Moderate fit", ai_augmentation_opportunity: "Strong fit" },
    explanations: { natural_fit: "Current snapshot.", capability_fit: "Current snapshot.", evidence_strength: "Current practical evidence.", transition_feasibility: "Current snapshot.", ai_augmentation_opportunity: "Current snapshot." },
  },
  dimension_scores: { natural_fit: 80, capability_fit: 76, evidence_strength: 82, transition_feasibility: 66, ai_augmentation_opportunity: 78 },
  dimension_labels: { natural_fit: "Strong fit", capability_fit: "Strong fit", evidence_strength: "Strong fit", transition_feasibility: "Moderate fit", ai_augmentation_opportunity: "Strong fit" },
  dimension_explanations: { natural_fit: "Current snapshot.", capability_fit: "Current snapshot.", evidence_strength: "Current practical evidence.", transition_feasibility: "Current snapshot.", ai_augmentation_opportunity: "Current snapshot." },
  factors: [],
  created_at: "2026-08-01T10:00:00Z",
  updated_at: "2026-08-31T10:00:00Z",
};

const profile = { id: profileId, primary_archetype: "Curious Builder", secondary_archetype: "Responsible Builder", strengths: [], values: [], fears: [], creative_tendencies: [], ai_collaboration_style: "Co-Creator", contribution_domains: [], recommended_learning_paths: [], uncertainties: [], risk_notes: [], ethical_note: "Decision support only.", created_at: "2026-08-01T10:00:00Z" };
const evidenceSufficient = { status: "evidence_sufficient", profile_id: profileId, career_match_id: match.id, hypothesis_id: "hypothesis-current", user_confirmed: true, expected_evidence_gain: "None", recommendation: { version: "adaptive-career-experiment-ranking-v1", state: "evidence_sufficient", rank: null, score: null, score_breakdown: {}, targeted_gap_skill_ids: [], unresolved_gap_skill_ids: [], already_practically_verified_skill_ids: verifiedSkills.map((skill) => skill.toLowerCase().replace("/", "_u" ).replace(/ /g, "_")), rationale: ["Current priority evidence gaps are sufficiently covered.", "No additional skill experiment is recommended solely to keep this loop running."], next_options: ["Collect external feedback.", "Add a roadmap action only after explicit confirmation."], ranked_template_ids: [] } };
const roadmap = { id: "roadmap-unchanged", profile_id: profileId, title: "User-confirmed roadmap", summary: "This roadmap is unchanged by evidence evaluation.", status: "active", version: 3, horizons: { seven_days: [], thirty_days: [], six_months: [] }, progress: { completion_percentage: 0, completed_actions: 0, in_progress_actions: 0, blocked_actions: 0 }, last_recalibrated_at: null, created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z" };
const assessment = { status: "completed", disclaimer: "Decision support only.", methodology_note: "Deterministic assessment.", assessment_version: "career-assessment-v1", scoring_version: "career-scoring-v1", session: { id: "assessment-session", profile_id: profileId, mode: "complete", status: "completed", consent_accepted: true, assessment_version: "career-assessment-v1", scoring_version: "career-scoring-v1", source_type: "test", demo_marker: false, metadata: {}, created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z" }, scores: [], grouped_scores: { personality: {}, career_interest: {} }, summary: { skills: [], top_work_values: [], combined_interest_profile: "Human-centred product work", ai_literacy_level: "Developing", ai_readiness_level: "Ready", change_readiness: "Exploring" }, reflection_prompts: [] };
const preferences = { id: "preferences", profile_id: profileId, preferred_language: "en", acceptable_secondary_languages: [], free_only: false, max_budget_per_course: null, monthly_learning_budget: null, available_hours_per_week: 6, preferred_content_formats: ["Project-based"], preferred_session_length_minutes: 60, theory_practice_preference: "practical", certificate_importance: "medium", preferred_difficulty: "adaptive", target_completion_date: null, accessibility_preferences: [], subtitles_required: false, mobile_friendly: false, offline_availability: false, provider_exclusions: [], strict_duration_limit_minutes: null, metadata: {}, created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z" };

async function mockPersistedPostEvidenceState(page: Page) {
  await page.addInitScript((id) => {
    localStorage.setItem("organicai_active_profile_id", id);
    localStorage.removeItem("organicai.auth.token");
  }, profileId);

  await page.route((url) => url.pathname.startsWith("/api/"), async (route) => {
    const url = new URL(route.request().url());
    if (await fulfillMockAuthRoute(route, "demo")) return;
    if (url.pathname === `/api/profiles/${profileId}`) return route.fulfill({ json: profile });
    if (url.pathname === "/api/profiles") return route.fulfill({ json: [{ id: profileId, created_at: profile.created_at, data: {} }] });
    if (url.pathname === "/api/diagnostics") return route.fulfill({ json: [{ id: "diagnostic", created_at: profile.created_at, payload: {} }] });
    if (url.pathname === "/api/roadmap") return route.fulfill({ json: [roadmap] });
    if (url.pathname === `/api/roadmap/${profileId}`) return route.fulfill({ json: roadmap });
    if (url.pathname.startsWith("/api/roadmaps/")) return route.fulfill({ json: [] });
    if (url.pathname === `/api/v1/profiles/${profileId}/career-resilience`) return route.fulfill({ json: { profile_id: profileId, workflow: [], life_event: null, urgent_actions: [], career_hypotheses: [{ id: "hypothesis-current", career_match_id: match.id, canonical_direction_id: "role-template:human_centred_ai_product_designer", title: direction, role_family: match.role_family, statement: "Current hypothesis.", uncertainty_label: "Bounded evidence support", status: "active", version: 2, fit_band: "Strong", user_decision_state: "exploring", source_breakdown: {}, missing_evidence: [] }], active_experiments: [{ id: "experiment-completed", career_match_id: match.id, experiment_template_id: "ai-product-concept-generation-sprint", roadmap_action_id: null, mode: "guided", status: "evaluated", user_confirmed: true, confidence_label: "Strong evidence", created_at: profile.created_at, updated_at: profile.created_at, started_at: profile.created_at, submitted_at: profile.created_at, evaluated_at: profile.created_at, template: { id: "ai-product-concept-generation-sprint", title: "Run an AI Feature Concept Generation Sprint", target_role_family: "AI Product Designer", purpose: "Direct Ideation evidence.", real_world_scenario: "", user_instructions: [], expected_deliverables: [], estimated_duration_minutes: 120, difficulty: "intermediate", required_skills: ["ideation"], skills_being_evaluated: ["ideation"], optional_prerequisites: [], allowed_tools: [], ai_assistance_policy: "", reflection_questions: [], completion_criteria: [], evidence_generated: [], version: "v1", source_metadata: {}, active: true }, recommendation: evidenceSufficient.recommendation, submission: { id: "submission" }, result: null, reviews: [] }], evidence_updates: [], evidence_gaps: [], evidence_states: [{ hypothesis_id: "hypothesis-current", career_match_id: match.id, canonical_direction_id: "role-template:human_centred_ai_product_designer", state: "evidence_sufficient", recommendation: evidenceSufficient.recommendation }], evidence_proposals: [], recalibration_history: [], best_supported_paths: [], market_snapshot: {}, potential_programmes: [], support_opportunity_graph: [], next_recommended_action: "Choose a user-controlled next step.", required_language: {} } });
    if (url.pathname === `/api/v1/profiles/${profileId}/career-experiments`) {
      return route.request().method() === "POST" ? route.fulfill({ json: evidenceSufficient }) : route.fulfill({ json: [] });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/evidence-passport`) return route.fulfill({ json: { profile_id: profileId, version: "evidence-passport-v1", methodology: "Persisted practical evidence.", skills: verifiedSkills.map((skill) => ({ skill_id: skill.toLowerCase().replace("/", "_u").replace(/ /g, "_"), skill_label: skill, category: "career_experiment", declared_level: 3, target_level: 3, evidence_confidence: "Strong evidence", strongest_evidence_label: "Practically verified", evidence_sources: [{ id: `evidence-${skill}`, type: "career_experiment", title: `Verified through career experiment: ${skill}`, description: "", url: null, verification_status: "practically_verified", confidence: "Strong evidence", strength: "Practically verified", created_at: profile.created_at, sources: [{ id: `source-${skill}`, source_type: "DETERMINISTIC_CAREER_EXPERIMENT", provenance_label: "Verified through career experiment", title: "", url: null, independent_confirmation: false }] }], recency: { status: "Current", evidence_age_days: 0, refresh_recommendation: "No refresh needed." }, status: "Practically verified evidence", related_roles: [direction], outstanding_verification_needs: [] })) } });
    if (url.pathname === `/api/v1/profiles/${profileId}/assessment-results`) return route.fulfill({ json: assessment });
    if (url.pathname === `/api/v1/profiles/${profileId}/career-matches`) return route.fulfill({ json: [match] });
    if (url.pathname === `/api/v1/profiles/${profileId}/learning-preferences`) return route.fulfill({ json: preferences });
    if (url.pathname === `/api/v1/profiles/${profileId}/skill-gap-analysis`) return route.fulfill({ json: { id: "analysis-current", profile_id: profileId, career_match_id: match.id, role_template_id: match.role_template_id, analysis_version: "skill-gap-v1", status: "ready", summary: "Only unresolved development skills remain.", hard_filters: [], context: {}, items: [{ id: "gap-evaluation", analysis_id: "analysis-current", skill_id: "evaluation", skill_label: "AI Evaluation", current_level: 1, current_level_label: "Beginner", target_level: 3, target_level_label: "Advanced", gap_size: 2, importance: 5, evidence_level: "self_reported", required: true, ai_augmentable: true, prerequisite_skill_ids: [], missing_prerequisites: [], status: "Moderate gap", priority_label: "High priority", priority_score_internal: 8, dependency_order: 1, explanation: "Further development, not evidence verification." }], objectives: [], practical_projects: [] } });
    if (url.pathname === `/api/v1/profiles/${profileId}/learning-recommendations`) return route.fulfill({ json: { id: "learning-run", profile_id: profileId, career_match_id: match.id, skill_gap_analysis_id: "analysis-current", preferences_id: preferences.id, recommendation_version: "learning-rec-v1", status: "ready", provider_status: [], hard_filters: [], ranking_weights: {}, recommendations: [], grouped_by_skill_gap: {}, created_at: profile.created_at } });
    if (url.pathname === `/api/recommendations/profile/${profileId}`) return route.fulfill({ json: [] });
    if (url.pathname === "/api/recommendations/generate") return route.fulfill({ json: { recommendations: [], context_summary: { profile_signals_used: [], feedback_applied: false }, metadata: {} } });
    if (url.pathname === `/api/v1/profiles/${profileId}/browser-extension/settings`) return route.fulfill({ json: {} });
    if (url.pathname === `/api/v1/profiles/${profileId}/job-captures` || url.pathname === `/api/v1/profiles/${profileId}/advisor-shares` || url.pathname === "/api/v1/panel-personas" || url.pathname === `/api/v1/profiles/${profileId}/career-encyclopedia`) return route.fulfill({ json: [] });
    if (url.pathname === `/api/v1/profiles/${profileId}/decision-journal`) return route.fulfill({ json: [{ id: "journal-1", profile_id: profileId, title: "User decision", decision_type: "career_direction", decision_summary: "User decision kept separate from evidence.", context: "", selected_option: direction, options: [], assumptions: [], uncertainty: {}, confidence: "", reversibility: "", evidence_links: [{ type: "career_experiment", id: "experiment-completed" }], source_attributions: [], system_suggestions: [{ calculation: "evidence_sufficient" }], ai_explanations: [{ suggestion: "Consider market feedback." }], evidence_observations: [{ skill: "Ideation", status: "Practically verified" }], adviser_inputs: [], user_reasoning: "The user retains the decision.", adviser_comment_ids: [], status: "active", privacy_scope: "private", outcome_status: "not_recorded", outcome: {}, reconsideration_reason: "", roadmap_mutation_allowed: false, reminder_status: "not_scheduled", version_number: 1, created_at: profile.created_at, updated_at: profile.created_at }] });
    if (url.pathname === `/api/v1/profiles/${profileId}/decision-journal/research-export`) return route.fulfill({ json: {} });
    return route.fulfill({ json: [] });
  });
}

test("persisted post-experiment state stays aligned across core pages after refresh", async ({ page }) => {
  await mockPersistedPostEvidenceState(page);

  await page.goto(`/workspace/${profileId}/career-resilience`);
  await expect(page.getByRole("heading", { name: "Evidence-based career hypotheses." })).toBeVisible();
  await expect(page.getByText(direction, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /Test this career/ }).click();
  await expect(page.getByTestId("evidence-sufficient-state")).toContainText("Current priority evidence is sufficient");
  await page.reload();
  await expect(page.getByTestId("evidence-sufficient-state")).toContainText("Current priority evidence is sufficient");
  await expect(page.getByText(direction, { exact: true })).toBeVisible();

  await page.goto(`/workspace/${profileId}/evidence-passport`);
  await expect(page.getByRole("heading", { name: "Evidence Passport" })).toBeVisible();
  for (const skill of verifiedSkills) await expect(page.getByText(skill, { exact: true })).toBeVisible();
  await expect(page.getByText("Practically verified", { exact: true })).toHaveCount(6);
  await page.reload();
  await expect(page.getByText("Practically verified", { exact: true })).toHaveCount(6);

  await page.goto(`/workspace/${profileId}/career-compatibility`);
  await expect(page.getByText(direction, { exact: true })).toBeVisible();
  await expect(page.getByText("82/100")).toBeVisible();
  await page.reload();
  await expect(page.getByText(direction, { exact: true })).toBeVisible();

  await page.goto(`/workspace/${profileId}/learning`);
  await expect(page.getByText("AI Evaluation", { exact: true })).toBeVisible();
  await expect(page.getByText("Ideation", { exact: true })).toHaveCount(0);
  await page.reload();
  await expect(page.getByText("Ideation", { exact: true })).toHaveCount(0);

  await page.goto(`/recommendations/${profileId}`);
  await expect(page.getByText("No recommendations match these filters.")).toBeVisible();
  await page.reload();
  await expect(page.getByText("No recommendations match these filters.")).toBeVisible();

  await page.goto(`/roadmap/${profileId}`);
  await expect(page.getByRole("heading", { name: "User-confirmed roadmap" })).toBeVisible();
  await expect(page.getByText("This roadmap is unchanged by evidence evaluation.")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "User-confirmed roadmap" })).toBeVisible();

  await page.goto("/dashboard");
  await expect(page.getByTestId("my-journey-page")).toBeVisible();
  await expect(page.getByTestId("journey-career-evidence")).toBeVisible();
  await expect(page.getByTestId("journey-current-direction")).toHaveText(direction);
  await expect(page.getByTestId("journey-evidence-state")).toContainText("evidence sufficient");
  await expect(page.getByText("Experiment status: evaluated")).toBeVisible();
  await expect(page.getByText("0%", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByTestId("journey-current-direction")).toHaveText(direction);
  await expect(page.getByTestId("journey-evidence-state")).toContainText("evidence sufficient");
  await expect(page.getByText("0%", { exact: true })).toBeVisible();

  await page.goto(`/workspace/${profileId}/decision-journal`);
  await expect(page.getByText("Career Decision Journal", { exact: true })).toBeVisible();
  await expect(page.locator(".innovation-row-title").getByText("User decision", { exact: true })).toBeVisible();
  await page.getByText("Separate decision record", { exact: true }).click();
  await expect(page.getByText("AI suggestions", { exact: true })).toBeVisible();
  await expect(page.getByText("System suggestions and calculations", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.locator(".innovation-row-title").getByText("User decision", { exact: true })).toBeVisible();
});
