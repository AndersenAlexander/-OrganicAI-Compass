import { expect, test, type Page } from "@playwright/test";

const profileId = "demo-profile";

const assessmentResults = {
  status: "completed",
  disclaimer: "Self-reflection and career exploration only.",
  methodology_note: "Prototype deterministic scoring.",
  assessment_version: "career-assessment-v1",
  scoring_version: "career-scoring-v1",
  session: { id: "session-1", profile_id: profileId, mode: "complete", status: "completed", consent_accepted: true, assessment_version: "career-assessment-v1", scoring_version: "career-scoring-v1", source_type: "demo", demo_marker: true, metadata: {}, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" },
  scores: [],
  grouped_scores: {},
  summary: { skills: [] },
  reflection_prompts: [],
};

const matches = [
  {
    id: "match-ai-product",
    session_id: "session-1",
    profile_id: profileId,
    role_template_id: "human_centred_ai_product_designer",
    category: "adjacent_professional_roles",
    title: "AI Product Designer",
    role_family: "Design and AI Product",
    description: "Design AI products.",
    alignment_score: 84,
    alignment_label: "Strong alignment",
    explanation: "Strong design and AI direction.",
    supporting_factors: ["Creative and investigative interests."],
    conflicting_factors: ["Needs stronger AI evaluation evidence."],
    missing_skills: ["AI evaluation"],
    transferable_skills: [{ original_skill: "Visual communication" }],
    ai_opportunities: ["Prototype alternatives"],
    next_step: "Build a two-week AI product-design prototype.",
    transition_difficulty: "moderate",
    time_horizon: "3-6 months",
    status: "suggested",
    assumptions: [],
    limitations: [],
    source_metadata: {},
    factors: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

const preferences = {
  id: "prefs-1",
  profile_id: profileId,
  preferred_language: "en",
  acceptable_secondary_languages: ["ro"],
  free_only: false,
  max_budget_per_course: 50,
  monthly_learning_budget: 50,
  available_hours_per_week: 8,
  preferred_content_formats: ["Project-based", "Text", "Video"],
  preferred_session_length_minutes: 60,
  theory_practice_preference: "practical",
  certificate_importance: "medium",
  preferred_difficulty: "adaptive",
  target_completion_date: null,
  accessibility_preferences: [],
  subtitles_required: false,
  mobile_friendly: false,
  offline_availability: false,
  provider_exclusions: [],
  strict_duration_limit_minutes: null,
  metadata: {},
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const gap = {
  id: "gap-1",
  analysis_id: "analysis-1",
  skill_id: "evaluation",
  skill_label: "AI Evaluation",
  current_level: 1,
  current_level_label: "Beginner",
  target_level: 3,
  target_level_label: "Advanced",
  gap_size: 2,
  importance: 4.5,
  evidence_level: "self_reported",
  required: true,
  ai_augmentable: true,
  prerequisite_skill_ids: ["critical_thinking"],
  missing_prerequisites: [],
  status: "Moderate gap",
  priority_label: "High priority",
  priority_score_internal: 8,
  dependency_order: 1,
  explanation: "AI evaluation is required for this role.",
};

const objective = {
  id: "objective-1",
  analysis_id: "analysis-1",
  gap_item_id: "gap-1",
  objective_key: "evaluation_1",
  skill_id: "evaluation",
  target_level: 3,
  target_level_label: "Advanced",
  description: "Define evaluation criteria before testing an AI product output.",
  prerequisite_ids: [],
  estimated_effort_minutes: 180,
  evidence_expected: "Summary plus practical evidence.",
  role_relevance: "Supports AI Product Designer.",
  priority: "High priority",
  objective_version: "learning-objective-v1",
  status: "open",
};

const skillGapAnalysis = {
  id: "analysis-1",
  profile_id: profileId,
  career_match_id: "match-ai-product",
  role_template_id: "human_centred_ai_product_designer",
  analysis_version: "skill-gap-v1",
  status: "ready",
  summary: "Skill-gap analysis for AI Product Designer.",
  hard_filters: [],
  context: {},
  items: [gap],
  objectives: [objective],
  practical_projects: [{
    id: "project-1",
    profile_id: profileId,
    career_match_id: "match-ai-product",
    skill_gap_item_id: "gap-1",
    title: "Create an explainable AI recommendation interface",
    description: "Project evidence.",
    skills_demonstrated: ["evaluation", "ux_ui"],
    estimated_effort_minutes: 480,
    suggested_deliverables: ["Prototype", "Evaluation notes"],
    completion_criteria: ["Document decisions"],
    portfolio_value: "Creates evidence beyond course completion.",
    prerequisites: [],
    status: "suggested",
  }],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function resource(id: string, title: string, provider: string, type: string, cost = "free") {
  return {
    id,
    provider_id: provider,
    external_id: null,
    title,
    canonical_url: id.startsWith("internal") ? `/learning/${id}` : "https://example.com/resource",
    description: "Stored resource metadata.",
    resource_type: type,
    resource_type_label: type.replace(/_/g, " "),
    level: "intermediate",
    language: "en",
    subtitles: ["en"],
    duration_minutes: 180,
    cost_type: cost,
    displayed_price: null,
    currency: null,
    instructor_organization: provider,
    rating: null,
    review_count: null,
    publication_date: null,
    last_updated_date: null,
    last_verified_at: "2026-07-20T00:00:00",
    prerequisites: [],
    certificate_available: false,
    practical_exercises: true,
    project_included: type.includes("project"),
    quality_status: "Verified",
    source_provenance: "manual curated MVP catalogue",
    active: true,
    affiliate: false,
    affiliate_disclosure: "No affiliate relationship is used for ranking.",
    notes_limitations: "Check provider page.",
    metadata_version: "learning-catalogue-v1",
    skills: [{ skill_id: "evaluation", coverage_level: "primary", target_level: "intermediate", weight: 1 }],
    objective_keys: ["evaluation_1"],
  };
}

const recommendations = [
  ["rec-1", resource("official-1", "NIST AI Risk Management Framework", "official_documentation", "official_documentation")],
  ["rec-2", resource("course-1", "AI For Everyone", "coursera", "online_course", "paid_or_audit")],
  ["rec-3", resource("internal-project-1", "Portfolio Project: Explainable AI Recommendation Interface", "internal", "portfolio_project")],
].map(([id, res], index) => ({
  id,
  run_id: "run-1",
  profile_id: profileId,
  career_match_id: "match-ai-product",
  skill_gap_item_id: "gap-1",
  learning_objective_id: "objective-1",
  learning_resource_id: (res as ReturnType<typeof resource>).id,
  alignment_label: index === 0 ? "Strong learning alignment" : "Good learning alignment",
  ranking_score_internal: 82 - index * 4,
  rank_position: index + 1,
  status: "suggested",
  explanation: "Recommended from stored metadata.",
  limitations: ["Metadata may become stale.", "No employment outcome is guaranteed."],
  recommendation_version: "learning-rec-v1",
  resource: res,
  skill_gap: gap,
  objective,
  factors: [{ id: `factor-${id}`, factor_type: "skill_gap_relevance", factor_value: 90, weight: 0.3, explanation: "Covers AI Evaluation." }],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
}));

const run = {
  id: "run-1",
  profile_id: profileId,
  career_match_id: "match-ai-product",
  skill_gap_analysis_id: "analysis-1",
  preferences_id: "prefs-1",
  recommendation_version: "learning-rec-v1",
  status: "ready",
  provider_status: [{ provider: "internal", status: "available" }, { provider: "external_search", status: "disabled" }],
  hard_filters: [],
  ranking_weights: {},
  recommendations,
  grouped_by_skill_gap: { "AI Evaluation": recommendations },
  created_at: "2026-01-01T00:00:00Z",
};

const runWithAuditAndNullableMetadata = {
  ...run,
  provider_status: [{ provider: "internal", status: "available", source: "curated catalogue" }, { provider: "external_search", status: "disabled", message: "Curated catalogue remains available." }],
  hard_filters: Array.from({ length: 23 }, (_, index) => ({
    resource_id: `excluded-resource-${index + 1}`,
    skill_gap_id: "gap-1",
    reasons: ["content does not cover the required skill"],
  })),
  recommendations: recommendations.map((recommendation, index) => index === 0 ? {
    ...recommendation,
    limitations: null,
    factors: null,
    resource: {
      ...recommendation.resource,
      displayed_price: null,
      currency: null,
      rating: null,
      review_count: null,
      subtitles: null,
      certificate_available: null,
      last_verified_at: null,
    },
  } : recommendation),
  grouped_by_skill_gap: { "AI Evaluation": recommendations },
};

const path = {
  id: "path-1",
  profile_id: profileId,
  career_match_id: "match-ai-product",
  recommendation_run_id: "run-1",
  title: "Personalised Learning Path: AI Product Designer",
  summary: "A staged plan.",
  status: "draft",
  weekly_effort_hours: 8,
  phases: [{
    id: "phase-1",
    phase_index: 1,
    title: "Foundations",
    description: "Essential concepts.",
    objectives: [],
    estimated_duration_minutes: 240,
    weekly_effort_hours: 4,
    completion_evidence: "Personal summary.",
    dependencies: [],
    items: [{
      id: "path-item-1",
      learning_path_id: "path-1",
      phase_id: "phase-1",
      recommendation_id: "rec-1",
      learning_resource_id: "official-1",
      learning_objective_id: "objective-1",
      title: "NIST AI Risk Management Framework",
      status: "planned",
      progress_percentage: 0,
      user_reported_progress: "",
      completion_date: null,
      evidence_url: null,
      reflection: "",
      difficulty_feedback: null,
      relevance_feedback: null,
      expected_evidence: "Summary and practical note.",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    }],
  }],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

async function mockLearning(
  page: Page,
  options: {
    recommendationRun?: unknown;
    skillGapStatus?: number;
    assessmentFailuresBeforeSuccess?: number;
  } = {}
) {
  let assessmentFailuresRemaining = options.assessmentFailuresBeforeSuccess || 0;
  const recommendationRun = options.recommendationRun || run;

  await page.addInitScript(() => {
    localStorage.setItem("organicai.auth.token", "demo-token");
    localStorage.setItem("organicai_active_profile_id", "demo-profile");
  });
  await page.route((url) => url.pathname.startsWith("/api/"), async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/auth/me") return route.fulfill({ json: { id: "demo-user", email: "demo@organicai.local", name: "OrganicAI Demo", is_demo: true } });
    if (url.pathname === "/api/demo/reset") return route.fulfill({ json: { ok: true, status: "reset", profile_id: profileId, active_profile_id: profileId, reset_sections: ["learning"], message: "Demo reset." } });
    if (url.pathname === `/api/profiles/${profileId}`) return route.fulfill({ json: { id: profileId, primary_archetype: "Curious Builder", secondary_archetype: "Systems Designer", strengths: [], values: [], fears: [], creative_tendencies: [], ai_collaboration_style: "Co-Creator", contribution_domains: [], recommended_learning_paths: [], uncertainties: [], risk_notes: [], ethical_note: "Demo.", created_at: "2026-01-01T00:00:00Z" } });
    if (url.pathname === `/api/profiles/${profileId}/feedback`) return route.fulfill({ json: { confirmed_nodes: [], hidden_recommendations: [], strength_adjustments: {}, archetype_override: null, user_notes: {} } });
    if (url.pathname === `/api/v1/profiles/${profileId}/assessment-results`) {
      if (assessmentFailuresRemaining > 0) {
        assessmentFailuresRemaining -= 1;
        return route.fulfill({ status: 500, json: { detail: "Assessment service failed." } });
      }
      return route.fulfill({ json: assessmentResults });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/career-matches`) return route.fulfill({ json: matches });
    if (url.pathname === "/api/v1/career-matches/match-ai-product/save") return route.fulfill({ json: { ...matches[0], status: "saved" } });
    if (url.pathname === `/api/v1/profiles/${profileId}/learning-preferences`) return route.fulfill({ json: preferences });
    if (url.pathname === "/api/v1/learning/providers") return route.fulfill({ json: [{ id: "internal", provider_name: "internal", display_name: "Internal", provider_type: "internal", base_url: null, active: true, supports_external_search: false, api_enabled: false, metadata: {} }] });
    if (url.pathname === `/api/v1/profiles/${profileId}/skill-gap-analysis`) {
      if (options.skillGapStatus) return route.fulfill({ status: options.skillGapStatus, json: { detail: "Skill-gap service failed." } });
      return route.fulfill({ json: skillGapAnalysis });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/learning-recommendations`) return route.fulfill({ json: recommendationRun });
    if (url.pathname.includes("/learning-recommendations/") && url.pathname.endsWith("/save")) return route.fulfill({ json: { ...recommendations[0], status: "saved" } });
    if (url.pathname.includes("/learning-recommendations/") && url.pathname.endsWith("/reject")) return route.fulfill({ json: { ...recommendations[0], status: "rejected" } });
    if (url.pathname.includes("/learning-recommendations/") && url.pathname.endsWith("/feedback")) return route.fulfill({ json: { status: "saved", feedback_id: "feedback-1", effect: {} } });
    if (url.pathname.includes("/learning-recommendations/") && url.pathname.endsWith("/alternative")) return route.fulfill({ json: { status: "alternative_requested", alternatives: recommendations.slice(1) } });
    if (url.pathname.includes("/learning-recommendations/") && url.pathname.endsWith("/add-to-roadmap")) return route.fulfill({ json: { status: "added_to_roadmap", roadmap_id: "roadmap-1", action_id: "action-1", roadmap_learning_action_id: "roadmap-learning-1" } });
    if (url.pathname === `/api/v1/profiles/${profileId}/learning-resource-comparisons`) return route.fulfill({ json: { id: "comparison-1", profile_id: profileId, recommendation_ids: ["rec-1", "rec-2"], resource_ids: ["official-1", "course-1"], criteria_weights: {}, matrix: { items: recommendations.slice(0, 2).map((rec) => ({ recommendation_id: rec.id, resource_id: rec.learning_resource_id, title: rec.resource.title, provider: rec.resource.provider_id, resource_type: rec.resource.resource_type, alignment_label: rec.alignment_label, level: rec.resource.level, duration_minutes: rec.resource.duration_minutes, price: null, cost_type: rec.resource.cost_type, language: rec.resource.language, certificate_available: rec.resource.certificate_available, project_component: rec.resource.project_included, last_verification: rec.resource.last_verified_at, prerequisites: [], strengths: ["skill_gap_relevance"], limitations: rec.limitations, criteria: {} })) }, created_at: "2026-01-01T00:00:00Z" } });
    if (url.pathname === `/api/v1/profiles/${profileId}/learning-path`) return route.fulfill({ json: path });
    if (url.pathname === `/api/v1/profiles/${profileId}/learning-path/generate`) return route.fulfill({ json: path });
    if (url.pathname === "/api/v1/learning-path-items/path-item-1/progress") return route.fulfill({ json: { ...path.phases[0].items[0], status: "completed", progress_percentage: 100, evidence_url: "/learning/evidence" } });
    return route.fulfill({ json: [] });
  });
}

test("learning page renders ready recommendations from snake_case response with audit metadata", async ({ page }) => {
  const apiRequests: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.pathname.startsWith("/api/")) apiRequests.push(url.pathname + url.search);
  });

  await mockLearning(page, { recommendationRun: runWithAuditAndNullableMetadata });
  await page.goto(`/workspace/${profileId}/learning`);

  await expect(page.getByRole("heading", { name: "Generate learning recommendations from a selected direction." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Latest Learning Recommendations" })).toBeVisible();
  await expect(page.getByText("3 recommendations available")).toBeVisible();
  await expect(page.getByText("23 filter records")).toBeVisible();
  await expect(page.getByText("external_search: disabled")).toBeVisible();
  await expect(page.getByText("NIST AI Risk Management Framework")).toBeVisible();
  await expect(page.getByText("Learning Path data could not be loaded.")).toHaveCount(0);
  await expect(page.locator('a[href*="/undefined"], a[href*="/null"]')).toHaveCount(0);
  expect(apiRequests.some((url) => url.includes("/undefined") || url.includes("/null") || url.includes("/api/v1/api/v1"))).toBe(false);

  await page.getByRole("link", { name: /Review All/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/learning/recommendations`));
  await expect(page.getByText("NIST AI Risk Management Framework")).toBeVisible();
  await expect(page.getByText("external_search: disabled")).toBeVisible();
});

test("learning page keeps recommendations visible when optional skill-gap load fails", async ({ page }) => {
  await mockLearning(page, { skillGapStatus: 500 });
  await page.goto(`/workspace/${profileId}/learning`);

  await expect(page.getByRole("heading", { name: "Generate learning recommendations from a selected direction." })).toBeVisible();
  await expect(page.getByText("NIST AI Risk Management Framework")).toBeVisible();
  await expect(page.getByText("Skill-gap snapshot could not be loaded.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry skill gap" })).toBeVisible();
  await expect(page.getByText("Learning Path data could not be loaded.")).toHaveCount(0);
});

test("learning page exposes retry when an essential loader request fails", async ({ page }) => {
  await mockLearning(page, { assessmentFailuresBeforeSuccess: 2 });
  await page.goto(`/workspace/${profileId}/learning`);

  await expect(page.getByRole("heading", { name: "Learning Path data could not be loaded." })).toBeVisible();
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByRole("heading", { name: "Generate learning recommendations from a selected direction." })).toBeVisible();
  await expect(page.getByText("NIST AI Risk Management Framework")).toBeVisible();
});

test("demo learning recommendations flow supports compare, roadmap, progress, and reset", async ({ page }) => {
  await mockLearning(page);
  await page.goto(`/workspace/${profileId}/career-compatibility`);
  await expect(page.getByRole("heading", { name: "Explore career directions before committing." })).toBeVisible();

  await page.goto(`/workspace/${profileId}/learning`);
  await expect(page.getByRole("heading", { name: "Generate learning recommendations from a selected direction." })).toBeVisible();
  await page.getByLabel(/AI Product Designer/).check();
  await page.getByRole("button", { name: "Generate Learning Recommendations" }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/learning/recommendations`));
  await expect(page.getByText("NIST AI Risk Management Framework")).toBeVisible();
  await expect(page.getByText("external_search: disabled")).toBeVisible();

  await page.getByLabel("Compare").nth(0).check();
  await page.getByLabel("Compare").nth(1).check();
  await page.getByRole("button", { name: /Compare/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/learning/compare`));
  await page.getByRole("button", { name: /Create Matrix/ }).click();
  await expect(page.getByRole("heading", { name: "Comparison Matrix" })).toBeVisible();
  await page.getByRole("button", { name: /^Add$/ }).first().click();
  await expect(page.getByRole("heading", { name: "Confirm Roadmap Learning Action" })).toBeVisible();
  await page.getByRole("button", { name: "Add to My Roadmap" }).click();
  await expect(page.getByText("Selected resource added to My Roadmap after confirmation.")).toBeVisible();

  await page.goto(`/workspace/${profileId}/learning/progress`);
  await expect(page.getByRole("heading", { name: "Personalised Learning Path: AI Product Designer" })).toBeVisible();
  await page.getByRole("button", { name: "Evidence" }).click();
  await page.getByPlaceholder("Evidence URL or internal path").fill("/learning/evidence");
  await page.getByRole("button", { name: "Save Progress" }).click();
  await expect(page.getByText("Progress and evidence saved. Skill level is not automatically upgraded.")).toBeVisible();

  await page.getByRole("button", { name: "Reset Demo" }).first().click();
  await page.getByRole("dialog").getByRole("button", { name: "Reset Demo" }).click();
  await expect(page).toHaveURL(new RegExp(`/profile/${profileId}$`));
  await expect(page.locator('a[href*="/undefined"], a[href*="/null"]')).toHaveCount(0);
});
