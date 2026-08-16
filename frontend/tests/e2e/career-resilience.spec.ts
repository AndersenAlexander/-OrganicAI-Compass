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

function session(status = "planned", result: unknown = null) {
  return {
    id: "experiment-session-1",
    profile_id: profileId,
    career_match_id: "match-ai-product",
    experiment_template_id: template.id,
    roadmap_action_id: null,
    mode: "guided",
    status,
    user_confirmed: true,
    confidence_label: "Additional evidence required",
    created_at: "2026-07-21T09:00:00Z",
    updated_at: "2026-07-21T09:00:00Z",
    started_at: status === "planned" ? null : "2026-07-21T09:10:00Z",
    submitted_at: ["submitted", "needs_review", "evaluated"].includes(status) ? "2026-07-21T10:00:00Z" : null,
    evaluated_at: status === "evaluated" ? "2026-07-21T10:15:00Z" : null,
    template,
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
    evidence_sources: [{ id: "evidence-1", type: "career_experiment", title: "Explainable recommendation interface", description: "Practical experiment evidence.", url: "https://example.test/project", confidence: "Strong evidence", strength: "Demonstrated" }],
    recency: { status: "Current", evidence_age_days: 0, refresh_recommendation: "No refresh needed yet." },
    status: "Supported by practical evidence",
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

async function mockCareerResilience(page: Page) {
  let currentStatus = "planned";
  let currentResult: unknown = null;

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
        return route.fulfill({ json: session(currentStatus, currentResult) });
      }
      return route.fulfill({ json: [session(currentStatus, currentResult)] });
    }
    if (url.pathname === "/api/v1/career-experiment-sessions/experiment-session-1") return route.fulfill({ json: session(currentStatus, currentResult) });
    if (url.pathname.endsWith("/start")) {
      currentStatus = "in_progress";
      return route.fulfill({ json: session(currentStatus, currentResult) });
    }
    if (url.pathname.endsWith("/submit")) {
      currentStatus = "submitted";
      return route.fulfill({ json: session(currentStatus, currentResult) });
    }
    if (url.pathname.endsWith("/self-review")) {
      currentStatus = "needs_review";
      return route.fulfill({ json: session(currentStatus, currentResult) });
    }
    if (url.pathname.endsWith("/evaluate")) {
      currentStatus = "evaluated";
      currentResult = evaluatedResult;
      return route.fulfill({ json: session(currentStatus, currentResult) });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/evidence-passport`) return route.fulfill({ json: passport });
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
  await expect(page.getByRole("status")).toContainText("Evidence Passport updated and career direction recalibrated.");
});

test("evidence passport and supported paths keep confidence dimensions visible", async ({ page }) => {
  await mockCareerResilience(page);
  await page.goto(`/workspace/${profileId}/evidence-passport`);

  await expect(page.getByRole("heading", { name: "Evidence Passport" })).toBeVisible();
  await expect(page.getByText("Strong evidence")).toBeVisible();
  await expect(page.getByText("Demonstrated", { exact: true })).toBeVisible();

  await page.goto(`/workspace/${profileId}/supported-paths`);
  await expect(page.getByRole("heading", { name: "Best Supported Career Path" })).toBeVisible();
  await expect(page.getByText("Personal Fit, Capability Fit, Market Fit, and Support Fit remain separate.")).toBeVisible();
  await expect(page.getByText("Recommended experiment: Design an Explainable AI Recommendation Interface")).toBeVisible();
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
