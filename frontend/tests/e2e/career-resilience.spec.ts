import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const profileId = "demo-profile";

const template = {
  id: "ai-product-explainable-recommendation-interface",
  title: "Design an Explainable AI Recommendation Interface",
  target_role_family: "AI Product Designer",
  purpose: "Test whether the user can translate AI uncertainty into understandable product interaction.",
  real_world_scenario: "A career-guidance platform generates recommendations, but users do not understand why a role was suggested.",
  user_instructions: ["Review the scenario.", "Produce a small practical artifact."],
  expected_deliverables: ["Responsive recommendation card", "State descriptions", "Design rationale"],
  estimated_duration_minutes: 180,
  difficulty: "intermediate",
  required_skills: ["ux_ui", "human_centred_ai"],
  skills_being_evaluated: ["ux_ui", "human_centred_ai", "explainability"],
  optional_prerequisites: [],
  allowed_tools: ["Whiteboard", "Text editor"],
  ai_assistance_policy: "AI assistance is allowed with disclosure.",
  reflection_questions: ["What uncertainty remains?"],
  completion_criteria: ["Submit one concrete deliverable."],
  evidence_generated: ["Career experiment submission", "Deterministic rubric result"],
  version: "career-experiment-catalogue-v1",
  source_metadata: {},
  active: true,
};

const ideationTemplate = {
  ...template,
  id: "ai-product-concept-generation-sprint",
  title: "Run an AI Feature Concept Generation Sprint",
  purpose: "Test whether the user can generate, compare, and narrow useful AI feature concepts.",
  real_world_scenario: "A product team needs to identify the most useful AI feature concept before prototyping.",
  estimated_duration_minutes: 120,
  required_skills: ["ideation", "product_thinking", "communication"],
  skills_being_evaluated: ["ideation", "product_thinking", "communication", "human_centred_ai"],
};

const ideationRecommendation = {
  version: "adaptive-career-experiment-ranking-v1",
  state: "experiment_recommended",
  rank: 1,
  score: 115,
  score_breakdown: { new_evidence_gain: 35, career_relevance: 30, unresolved_gap_coverage: 20, uncertainty_reduction: 15, feasibility: 15, redundant_evidence_penalty: 0, duplicate_experiment_penalty: 0 },
  targeted_gap_skill_ids: ["ideation"],
  unresolved_gap_skill_ids: ["ideation"],
  already_practically_verified_skill_ids: ["ux_ui", "product_thinking", "responsible_ai", "risk_reasoning"],
  rationale: [
    "Tests unresolved gap: Ideation.",
    "Relevant to Human-Centred AI Product Designer.",
    "Existing practical evidence already verifies: UX/UI, Product Thinking, Responsible AI, Risk Reasoning.",
    "Expected evidence gain: High.",
  ],
  ranked_template_ids: ["ai-product-concept-generation-sprint", "ai-product-micro-usability-test", "ai-product-human-review-flow"],
};

const evidenceSufficientRecommendation = {
  version: "adaptive-career-experiment-ranking-v1",
  state: "evidence_sufficient",
  rank: null,
  score: null,
  score_breakdown: {},
  targeted_gap_skill_ids: [],
  unresolved_gap_skill_ids: [],
  already_practically_verified_skill_ids: ["ux_ui", "product_thinking", "responsible_ai", "risk_reasoning", "ideation"],
  rationale: [
    "Current priority evidence gaps are sufficiently covered.",
    "Relevant to Human-Centred AI Product Designer.",
    "No additional skill experiment is recommended solely to keep this loop running.",
  ],
  next_options: ["Collect external evidence or feedback for this direction.", "Add a roadmap action only after explicit confirmation."],
  ranked_template_ids: ["ai-product-concept-generation-sprint", "ai-product-human-review-flow"],
};

function session(
  status = "planned",
  result: unknown = null,
  roadmapActionId: string | null = null,
  selectedTemplate = template,
  recommendation: Record<string, unknown> | null = null,
) {
  return {
    id: "experiment-session-1",
    profile_id: profileId,
    career_match_id: "match-ai-product",
    experiment_template_id: selectedTemplate.id,
    roadmap_action_id: roadmapActionId,
    mode: "guided",
    status,
    user_confirmed: true,
    confidence_label: "Additional evidence required",
    created_at: "2026-07-21T09:00:00Z",
    updated_at: "2026-07-21T09:00:00Z",
    started_at: status === "planned" ? null : "2026-07-21T09:10:00Z",
    submitted_at: ["submitted", "needs_review", "evaluated"].includes(status) ? "2026-07-21T10:00:00Z" : null,
    evaluated_at: status === "evaluated" ? "2026-07-21T10:15:00Z" : null,
    template: selectedTemplate,
    recommendation,
    submission: ["submitted", "needs_review", "evaluated"].includes(status) ? { id: "submission-1" } : null,
    result,
    reviews: [],
  };
}

const evaluatedResult = {
  id: "experiment-result-1",
  overall_score: 78,
  overall_label: "Demonstrated practical evidence",
  criteria_scores: [{ criterion_id: "human_centred", skill_id: "human_centred_ai", rating: 3, weight: 0.12, interpretation: "Competent evidence" }],
  skills_evaluated: ["human_centred_ai", "ux_ui"],
  strengths: ["Human-centred review was visible."],
  improvement_areas: ["Add stronger validation evidence."],
  evidence_created: [{ skill_id: "human_centred_ai", skill_label: "Human Centred AI", evidence_id: "evidence-1", confidence_label: "Strong evidence", strength_label: "Demonstrated" }],
  persistence: { status: "persisted", review_id: "review-1", source_type: "DETERMINISTIC_CAREER_EXPERIMENT", evidence_ids: ["evidence-1"] },
  linked_gap: {
    intended_gap: { id: "gap-ideation", skill_id: "ideation", skill_label: "Ideation", status: "MISSING" },
    assessed_skill_ids: ["human_centred_ai", "ux_ui"],
    generated_skill_ids: ["human_centred_ai"],
    directly_assessed: false,
    remaining_unresolved: true,
    message: "This experiment generated evidence for Human Centred AI and UX/UI, but did not directly verify the linked Ideation gap.",
  },
};

const evaluatedIdeationResult = {
  ...evaluatedResult,
  overall_score: 100,
  overall_label: "Strong evidence",
  criteria_scores: [
    { criterion_id: "task_understanding", skill_id: "ideation", rating: 4, weight: 0.2, interpretation: "Complete problem framing" },
    { criterion_id: "deliverable_quality", skill_id: "ideation", rating: 4, weight: 0.3, interpretation: "Three concepts submitted" },
    { criterion_id: "reasoning_clarity", skill_id: "ideation", rating: 4, weight: 0.25, interpretation: "Compared and selected" },
  ],
  skills_evaluated: ["ideation", "product_thinking", "communication", "human_centred_ai"],
  evidence_created: [{ skill_id: "ideation", skill_label: "Ideation", evidence_id: "evidence-ideation", confidence_label: "Strong evidence", strength_label: "Practically verified" }],
  persistence: { status: "persisted", review_id: "review-ideation", source_type: "DETERMINISTIC_CAREER_EXPERIMENT", evidence_ids: ["evidence-ideation"] },
  linked_gap: {
    intended_gap: { id: "gap-ideation", skill_id: "ideation", skill_label: "Ideation", status: "MISSING" },
    assessed_skill_ids: ["ideation"],
    generated_skill_ids: ["ideation"],
    directly_assessed: true,
    remaining_unresolved: false,
    message: "The linked gap was directly assessed and is now practically verified by the deterministic rubric.",
  },
  provenance: { canonical_direction_id: "role-template:human_centred_ai_product_designer", hypothesis_id: "hypothesis-1", experiment_session_id: "experiment-session-1", submission_id: "submission-1", deterministic_review_id: "review-ideation", experiment_template_id: "ai-product-concept-generation-sprint" },
};

const dashboard = {
  profile_id: profileId,
  workflow: ["Create career hypotheses", "Run a practical experiment", "Update Evidence Passport", "Compare supported paths"],
  life_event: null,
  urgent_actions: [],
  career_hypotheses: [{
    id: "hypothesis-1",
    career_match_id: "match-ai-product",
    title: "AI Product Designer",
    role_family: "Design and AI Product",
    statement: "Current evidence suggests AI Product Designer may have strong alignment. This career direction remains a hypothesis.",
    uncertainty_label: "Additional evidence required",
    status: "active",
  }],
  active_experiments: [session()],
  evidence_updates: [],
  best_supported_paths: [],
  potential_programmes: [],
  next_recommended_action: "Complete a practical career experiment",
};

const passport = {
  profile_id: profileId,
  version: "evidence-confidence-v1",
  methodology: "Evidence Passport separates self-report from stronger practical evidence and tracks recency.",
  skills: [{
    skill_id: "human_centred_ai",
    skill_label: "Human Centred AI",
    category: "career_experiment",
    declared_level: 3,
    target_level: 4,
    evidence_confidence: "Strong evidence",
    strongest_evidence_label: "Demonstrated",
    evidence_sources: [{ id: "evidence-1", type: "career_experiment", title: "Explainable recommendation interface", description: "Practical experiment evidence.", url: "https://example.test/project", confidence: "Strong evidence", strength: "Demonstrated", sources: [{ id: "source-1", source_type: "DETERMINISTIC_CAREER_EXPERIMENT", provenance_label: "Verified through career experiment", deterministic_score: 78 }] }],
    recency: { status: "Current", evidence_age_days: 0, refresh_recommendation: "No refresh needed yet." },
    status: "Supported by practical evidence",
    related_roles: ["AI Product Designer"],
    outstanding_verification_needs: [],
  }],
};

const ideationPassport = {
  ...passport,
  skills: [{
    skill_id: "ideation",
    skill_label: "Ideation",
    category: "career_experiment",
    declared_level: 3,
    target_level: 4,
    evidence_confidence: "Strong evidence",
    strongest_evidence_label: "Practically verified",
    evidence_sources: [{ id: "evidence-ideation", type: "career_experiment", title: "Verified through career experiment: Run an AI Feature Concept Generation Sprint - Ideation", description: "Direct deterministic review of the concept-generation sprint.", url: "https://example.test/ideation-sprint", confidence: "Strong evidence", strength: "Practically verified", sources: [{ id: "source-ideation", source_type: "DETERMINISTIC_CAREER_EXPERIMENT", provenance_label: "Verified through career experiment: Run an AI Feature Concept Generation Sprint", deterministic_score: 100, experiment_session_id: "experiment-session-1", submission_id: "submission-1", deterministic_review_id: "review-ideation" }] }],
    recency: { status: "Current", evidence_age_days: 0, refresh_recommendation: "No refresh needed yet." },
    status: "Practically verified evidence",
    related_roles: ["AI Product Designer"],
    outstanding_verification_needs: [],
  }],
};

const paths = {
  id: "supported-path-run-1",
  status: "ready",
  results: [{
    id: "supported-path-1",
    career_match_id: "match-ai-product",
    role_family: "Design and AI Product",
    title: "AI Product Designer",
    personal_fit: "Strong",
    capability_fit: "Developing",
    market_fit: "Moderate",
    support_fit: "Potentially supported",
    transition_difficulty: "moderate",
    estimated_preparation_range: "3-6 months",
    main_strengths: ["Interest alignment", "Practical design evidence"],
    main_gaps: ["AI evaluation depth"],
    main_uncertainties: ["Norway market evidence is curated, not live."],
    required_experiment_id: template.id,
    required_experiment_title: template.title,
    possible_public_support: [],
    next_best_action: "Complete a second experiment.",
    official_assessment_required: true,
  }],
};

const plan = {
  id: "action-plan-1",
  status: "ready",
  items: [{
    id: "action-1",
    title: "Register as a jobseeker",
    reason: "NAV describes registration as a first step for occupational follow-up.",
    urgency: "high",
    official_source: { title: "NAV - Register as a jobseeker", url: "https://www.nav.no/registrer-arbeidssoker/en", last_checked_date: "2026-07-21" },
    status: "open",
    due_date: null,
    user_confirmation: false,
  }],
};

const screening = {
  id: "screening-1",
  status: "preliminary",
  country: "Norway",
  unknown_fields: ["income history"],
  preliminary_result: {
    programmes: [{
      programme_id: "nav_unemployment_benefit",
      programme_name: "Unemployment benefit",
      preliminary_label: "Additional information required",
      explanation: "NAV must assess income, working-hours reduction, residence, and jobseeker status.",
      unknown_fields: ["income history"],
      official_source: { title: "NAV - Unemployment benefit", url: "https://www.nav.no/dagpenger/en", last_checked_date: "2026-07-21" },
      human_assessment_required: true,
    }],
    limitations: ["No eligibility decision is made."],
  },
  rule_version: "support-rule-no-v1",
};

const brief = {
  id: "brief-1",
  content: {
    purpose: "Prepare for a NAV discussion.",
    situation_summary: "Job loss profile for Norway with training interest.",
  },
  disclaimer: "This brief supports preparation only. It is not an eligibility decision or legal advice.",
  official_source_references: [{ programme_id: "nav_unemployment_benefit", title: "NAV - Unemployment benefit", url: "https://www.nav.no/dagpenger/en", last_checked_date: "2026-07-21" }],
  unresolved_questions: ["Confirm income history with NAV."],
};

async function mockCareerResilience(page: Page, options: { reviewed?: boolean; failEvidencePersistence?: boolean } = {}) {
  let currentStatus = "planned";
  let currentResult: unknown = null;
  let roadmapConfirmed = false;
  let evidencePersisted = Boolean(options.reviewed);
  let currentTemplate = template;
  let currentRecommendation: Record<string, unknown> | null = null;

  await page.addInitScript((id) => {
    localStorage.setItem("organicai_active_profile_id", id);
    localStorage.removeItem("organicai.auth.token");
  }, profileId);

  await page.route((url) => url.pathname.startsWith("/api/"), async (route) => {
    const url = new URL(route.request().url());
    if (await fulfillMockAuthRoute(route, "demo")) return;
    if (url.pathname === `/api/profiles/${profileId}`) return route.fulfill({ json: { id: profileId, primary_archetype: "Curious Builder", secondary_archetype: "Systems Designer", strengths: [], values: [], fears: [], creative_tendencies: [], ai_collaboration_style: "Co-Creator", contribution_domains: [], recommended_learning_paths: [], uncertainties: [], risk_notes: [], ethical_note: "Demo.", created_at: "2026-01-01T00:00:00Z" } });
    if (url.pathname === `/api/profiles/${profileId}/feedback`) return route.fulfill({ json: { confirmed_nodes: [], hidden_recommendations: [], strength_adjustments: {}, archetype_override: null, user_notes: {} } });
    if (url.pathname === `/api/v1/profiles/${profileId}/career-resilience`) return route.fulfill({ json: dashboard });
    if (url.pathname === "/api/v1/career-experiments") return route.fulfill({ json: [template] });
    if (url.pathname === `/api/v1/profiles/${profileId}/career-experiments`) {
      if (route.request().method() === "POST") {
        currentStatus = "planned";
        currentResult = null;
        const payload = route.request().postDataJSON() as { career_match_id?: string } | null;
        if (payload?.career_match_id) {
          if (evidencePersisted) {
            return route.fulfill({ json: { status: "evidence_sufficient", profile_id: profileId, career_match_id: "match-ai-product", hypothesis_id: "hypothesis-1", user_confirmed: true, expected_evidence_gain: "None", recommendation: evidenceSufficientRecommendation } });
          }
          currentTemplate = ideationTemplate;
          currentRecommendation = ideationRecommendation;
        } else {
          currentTemplate = template;
          currentRecommendation = null;
        }
        return route.fulfill({ json: session(currentStatus, currentResult, null, currentTemplate, currentRecommendation) });
      }
      return route.fulfill({ json: [session(currentStatus, currentResult, roadmapConfirmed ? "roadmap-action-1" : null, currentTemplate, currentRecommendation)] });
    }
    if (url.pathname === "/api/v1/career-experiment-sessions/experiment-session-1") return route.fulfill({ json: session(currentStatus, currentResult, roadmapConfirmed ? "roadmap-action-1" : null, currentTemplate, currentRecommendation) });
    if (url.pathname.endsWith("/start")) {
      currentStatus = "in_progress";
      return route.fulfill({ json: session(currentStatus, currentResult, roadmapConfirmed ? "roadmap-action-1" : null, currentTemplate, currentRecommendation) });
    }
    if (url.pathname.endsWith("/submit")) {
      currentStatus = "submitted";
      return route.fulfill({ json: session(currentStatus, currentResult, roadmapConfirmed ? "roadmap-action-1" : null, currentTemplate, currentRecommendation) });
    }
    if (url.pathname.endsWith("/self-review")) {
      currentStatus = "needs_review";
      return route.fulfill({ json: session(currentStatus, currentResult, roadmapConfirmed ? "roadmap-action-1" : null, currentTemplate, currentRecommendation) });
    }
    if (url.pathname.endsWith("/evaluate")) {
      if (options.failEvidencePersistence) return route.fulfill({ status: 503, json: { detail: "Evidence storage is temporarily unavailable." } });
      currentStatus = "evaluated";
      currentResult = currentTemplate.id === ideationTemplate.id ? evaluatedIdeationResult : evaluatedResult;
      evidencePersisted = true;
      return route.fulfill({ json: session(currentStatus, currentResult, roadmapConfirmed ? "roadmap-action-1" : null, currentTemplate, currentRecommendation) });
    }
    if (url.pathname.endsWith("/roadmap")) {
      roadmapConfirmed = true;
      return route.fulfill({ json: session(currentStatus, currentResult, "roadmap-action-1", currentTemplate, currentRecommendation) });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/evidence-passport`) {
      return route.fulfill({
        json: evidencePersisted
          ? (currentTemplate.id === ideationTemplate.id ? ideationPassport : passport)
          : {
              ...passport,
              skills: passport.skills.map((skill) => ({
                ...skill,
                evidence_confidence: "Limited evidence",
                strongest_evidence_label: "Self-reported",
                evidence_sources: [],
                status: "Needs verification",
                outstanding_verification_needs: ["Add practical or externally confirmed evidence."],
              })),
            },
      });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/supported-paths`) {
      if (route.request().method() === "POST") return route.fulfill({ json: paths });
      return route.fulfill({ json: paths });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/job-loss-profile`) {
      if (route.request().method() === "POST") return route.fulfill({ json: { id: "job-loss-1", profile_id: profileId, consent_accepted: true, country_of_residence: "Norway", country_of_employment: "Norway", municipality_or_region: "Oslo", last_working_date: null, contract_termination_type: "terminated", employment_status: "unemployed", reduction_in_working_hours: 100, jobseeker_registration_status: "not_registered", current_benefits: [], training_interest: "yes", availability_for_work: "yes", sensitive_explanations: {} } });
      return route.fulfill({ json: null });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/immediate-action-plan`) {
      if (route.request().method() === "POST") return route.fulfill({ json: plan });
      return route.fulfill({ json: plan });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/support-screening`) {
      if (route.request().method() === "POST") return route.fulfill({ json: screening });
      return route.fulfill({ json: screening });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/support-brief`) {
      if (route.request().method() === "POST") return route.fulfill({ json: brief });
      return route.fulfill({ json: brief });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/career-recalibration`) return route.fulfill({ json: { id: "recalibration-1", status: "completed" } });
    if (url.pathname === `/api/roadmap/${profileId}`) return route.fulfill({ json: { id: "roadmap-1", profile_id: profileId, seven_days: [], thirty_days: [], six_months: [] } });
    return route.fulfill({ json: [] });
  });
}

test("career resilience dashboard and experiment flow expose evidence hypothesis states", async ({ page }) => {
  await mockCareerResilience(page);
  await page.goto(`/workspace/${profileId}/career-resilience`);

  await expect(page.getByRole("heading", { name: "Evidence-based career hypotheses." })).toBeVisible();
  await expect(page.getByText("Current evidence suggests directions to test.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "AI Product Designer" })).toBeVisible();

  await page.getByRole("link", { name: /Experiments/ }).click();
  await expect(page.getByRole("heading", { name: "Experiment catalogue" })).toBeVisible();
  await page.getByRole("button", { name: /Plan/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/experiments/experiment-session-1$`));
  await page.getByRole("button", { name: /Start/ }).click();
  await expect(page.getByRole("status")).toContainText("Experiment is in progress.");
  await page.getByPlaceholder("Submission text or deliverable summary").fill("Prototype with user correction, validation review, accessibility and explainability notes.");
  await page.getByPlaceholder("Completion notes").fill("Manual submission for deterministic review.");
  await page.getByRole("button", { name: /Submit/ }).click();
  await page.getByRole("button", { name: /Review evidence/ }).click();
  await expect(page.getByRole("status")).toContainText("Practical evidence was persisted in Evidence Passport");
  await expect(page.getByTestId("unresolved-linked-gap")).toContainText("did not directly verify the linked Ideation gap");
});

test("Test this career shows the latest adaptive evidence rationale and keeps it after refresh", async ({ page }) => {
  await mockCareerResilience(page);
  await page.goto(`/workspace/${profileId}/career-resilience`);

  await page.getByRole("button", { name: /Test this career/ }).click();
  await expect(page.getByRole("heading", { name: "Run an AI Feature Concept Generation Sprint" })).toBeVisible();
  await expect(page.getByTestId("experiment-recommendation-rationale")).toContainText("Tests unresolved gap: Ideation.");
  await expect(page.getByTestId("experiment-recommendation-rationale")).toContainText("Existing practical evidence already verifies: UX/UI, Product Thinking, Responsible AI, Risk Reasoning.");
  await expect(page.getByTestId("experiment-recommendation-rationale")).not.toContainText("Tests unresolved gap: UX/UI");

  await page.reload();
  await expect(page.getByRole("heading", { name: "Run an AI Feature Concept Generation Sprint" })).toBeVisible();
  await expect(page.getByTestId("experiment-recommendation-rationale")).toContainText("Tests unresolved gap: Ideation.");
});

test("reviewed direct Ideation evidence makes the next recommendation evidence-sufficient without changing My Roadmap", async ({ page }) => {
  await mockCareerResilience(page);
  await page.goto(`/workspace/${profileId}/career-resilience`);

  await page.getByRole("button", { name: /Test this career/ }).click();
  await expect(page.getByTestId("experiment-recommendation-rationale")).toContainText("Tests unresolved gap: Ideation.");
  await page.getByRole("button", { name: /Start/ }).click();
  await page.getByPlaceholder("Submission text or deliverable summary").fill("Generated and compared several AI feature concepts with user needs and trade-offs.");
  await page.getByPlaceholder("Completion notes").fill("Concept sprint evidence for deterministic review.");
  await page.getByRole("button", { name: /Submit/ }).click();
  await page.getByRole("button", { name: /Review evidence/ }).click();
  await expect(page.getByRole("status")).toContainText("Practical evidence was persisted in Evidence Passport");

  await page.getByRole("link", { name: "Evidence" }).click();
  await expect(page.getByRole("heading", { name: "Evidence Passport" })).toBeVisible();
  await expect(page.getByText("Ideation", { exact: true })).toBeVisible();
  await expect(page.getByText("Practically verified", { exact: true })).toBeVisible();
  await expect(page.getByText("Verified through career experiment: Run an AI Feature Concept Generation Sprint")).toBeVisible();
  await expect(page.getByText("Verified through career experiment")).toBeVisible();
  await page.goto(`/workspace/${profileId}/career-resilience`);
  await page.getByRole("button", { name: /Test this career/ }).click();
  await expect(page.getByTestId("evidence-sufficient-state")).toContainText("Current priority evidence is sufficient");
  await expect(page.getByTestId("evidence-sufficient-state")).toContainText("No additional skill experiment is recommended solely to keep this loop running.");
  await expect(page.getByTestId("evidence-sufficient-state")).toContainText("No roadmap action was created");

  await page.reload();
  await page.getByRole("button", { name: /Test this career/ }).click();
  await expect(page.getByTestId("evidence-sufficient-state")).toContainText("Current priority evidence is sufficient");
});

test("evidence passport and supported paths keep confidence dimensions visible", async ({ page }) => {
  await mockCareerResilience(page, { reviewed: true });
  await page.goto(`/workspace/${profileId}/evidence-passport`);

  await expect(page.getByRole("heading", { name: "Evidence Passport" })).toBeVisible();
  await expect(page.getByText("Strong evidence")).toBeVisible();
  await expect(page.getByText("Demonstrated", { exact: true })).toBeVisible();

  await page.goto(`/workspace/${profileId}/supported-paths`);
  await expect(page.getByRole("heading", { name: "Best Supported Career Path" })).toBeVisible();
  await expect(page.getByText("Personal Fit, Capability Fit, Market Fit, and Support Fit remain separate.")).toBeVisible();
  await expect(page.getByText("Recommended experiment: Design an Explainable AI Recommendation Interface")).toBeVisible();
});

test("persists reviewed evidence, keeps the linked ideation gap unresolved, and survives refresh", async ({ page }) => {
  await mockCareerResilience(page);
  await page.goto(`/workspace/${profileId}/experiments/experiment-session-1`);

  await page.getByRole("button", { name: /Start/ }).click();
  await page.getByTestId("add-experiment-to-roadmap").click();
  await expect(page.getByText("Roadmap confirmed", { exact: true })).toBeVisible();
  await page.getByPlaceholder("Submission text or deliverable summary").fill("Prototype with user correction, validation review, accessibility and explainability notes.");
  await page.getByPlaceholder("Completion notes").fill("Manual submission for deterministic review.");
  await page.getByRole("button", { name: /Submit/ }).click();
  await page.getByRole("button", { name: /Review evidence/ }).click();

  await expect(page.getByRole("status")).toContainText("Practical evidence was persisted");
  await expect(page.getByTestId("unresolved-linked-gap")).toContainText("did not directly verify the linked Ideation gap");
  await page.getByRole("link", { name: "Evidence" }).click();
  await expect(page.getByText("Demonstrated", { exact: true })).toBeVisible();
  await expect(page.getByText("Verified through career experiment")).toBeVisible();

  await page.reload();
  await expect(page.getByText("Demonstrated", { exact: true })).toBeVisible();
  await expect(page.getByText("Verified through career experiment")).toBeVisible();
  await page.getByRole("link", { name: "Experiments" }).click();
  await expect(page.getByText("Roadmap confirmed", { exact: true })).toBeVisible();
  await expect(page.getByTestId("unresolved-linked-gap")).toContainText("did not directly verify the linked Ideation gap");
});

test("does not report review success when evidence persistence fails and leaves retry available", async ({ page }) => {
  await mockCareerResilience(page, { failEvidencePersistence: true });
  await page.goto(`/workspace/${profileId}/experiments/experiment-session-1`);
  await page.getByRole("button", { name: /Start/ }).click();
  await page.getByPlaceholder("Submission text or deliverable summary").fill("Prototype with a review and correction flow.");
  await page.getByPlaceholder("Completion notes").fill("Submission for deterministic review.");
  await page.getByRole("button", { name: /Submit/ }).click();
  await page.getByRole("button", { name: /Review evidence/ }).click();

  await expect(page.getByRole("alert")).toContainText("Could not persist reviewed evidence.");
  await expect(page.getByText("Practical evidence was persisted in Evidence Passport and career hypotheses were recalibrated.")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Review evidence/ })).toBeEnabled();
});

test("job loss mode requires consent and renders official-source preliminary support", async ({ page }) => {
  await mockCareerResilience(page);
  await page.goto(`/workspace/${profileId}/job-loss-support`);

  await expect(page.getByRole("heading", { name: "I have lost my job." })).toBeVisible();
  await expect(page.getByRole("button", { name: /Activate Job Loss Mode/ })).toBeDisabled();
  await page.getByLabel("Store job-loss information for this profile").check();
  await page.getByRole("button", { name: /Activate Job Loss Mode/ }).click();

  await expect(page.getByRole("status")).toContainText("Job Loss Mode activated");
  await expect(page.getByText("Register as a jobseeker")).toBeVisible();
  await expect(page.getByText("Additional information required")).toBeVisible();

  await page.getByRole("link", { name: /Support Brief/ }).click();
  await expect(page.getByRole("heading", { name: "Support Application Brief" })).toBeVisible();
  await expect(page.getByText("not an eligibility decision or legal advice")).toBeVisible();
  await expect(page.locator('a[href*="/undefined"], a[href*="/null"]')).toHaveCount(0);
});
