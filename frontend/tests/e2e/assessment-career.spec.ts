import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const profileId = "demo-profile";

const definition = {
  id: "human-potential-career-assessment",
  title: "Human Potential & Career Assessment",
  version: "career-assessment-v1",
  scoring_version: "career-scoring-v2-four-layer",
  disclaimer:
    "This assessment supports self-reflection and career exploration. It is based on self-reported information and prototype scoring methods. It is not a psychological diagnosis, employment decision, or guarantee of professional success. Final decisions remain with the user.",
  methodology_note: "Original neutral prototype items; non-clinical and not for hiring.",
  modes: [
    { id: "quick", title: "Quick Assessment", estimated_minutes: "8-10", description: "Preliminary self-understanding." },
    { id: "complete", title: "Complete Assessment", estimated_minutes: "20-30", description: "Detailed profile." },
    { id: "evidence_based", title: "Evidence-Based Assessment", estimated_minutes: "30+", description: "Structured manual evidence." },
  ],
  modules: [
    { id: "professional_background", title: "Professional Background", description: "Current context.", order: 1 },
    { id: "personality_work_style", title: "Personality, Work Style & Career Fit", description: "Current tendencies.", order: 2 },
  ],
  items: [
    { id: "background_current_profession", module_id: "professional_background", prompt: "Current profession or role", item_type: "text", dimension: "current_profession", reverse_scored: false, required: true, quick_mode: true, metadata: {} },
    { id: "personality_openness_ideas", module_id: "personality_work_style", prompt: "I enjoy exploring unfamiliar ideas.", item_type: "likert", dimension: "openness", reverse_scored: false, required: true, quick_mode: true, metadata: {} },
  ],
  likert_options: [
    { value: 1, label: "Strongly disagree" },
    { value: 2, label: "Disagree" },
    { value: 3, label: "Neither agree nor disagree" },
    { value: 4, label: "Agree" },
    { value: 5, label: "Strongly agree" },
  ],
  skill_levels: [{ value: "beginner", score: 1, label: "Beginner" }],
  evidence_statuses: [{ value: "self_reported", label: "Self-reported" }],
};

const prefill = {
  source: "profile.assessment_prefill",
  source_profile_id: profileId,
  responses: {
    background_current_profession: "Designer",
    personality_openness_ideas: 4,
  },
  notes: {
    background_current_profession: "Prefilled from Natural Discovery role context.",
    personality_openness_ideas: "Prefilled from Natural Discovery interests. Confirm or edit.",
  },
  strategy: "prefill_only_user_must_confirm",
};

const results = {
  status: "completed",
  disclaimer: definition.disclaimer,
  methodology_note: definition.methodology_note,
  assessment_version: "career-assessment-v1",
  scoring_version: "career-scoring-v2-four-layer",
  session: { id: "session-1", profile_id: profileId, mode: "quick", status: "completed", consent_accepted: true, assessment_version: "career-assessment-v1", scoring_version: "career-scoring-v2-four-layer", source_type: "user", demo_marker: false, metadata: {}, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" },
  scores: [],
  grouped_scores: {
    personality: { openness: { id: "score-1", score_type: "personality", dimension: "openness", raw_score: 4, normalized_score: 75, label: "Moderate current preference", interpretation: "Your current answers suggest moderate current preference.", source_type: "calculated", confirmation_status: "needs_review", metadata: {} } },
    career_interest: { artistic: { id: "score-2", score_type: "career_interest", dimension: "artistic", raw_score: 4, normalized_score: 75, label: "Moderate alignment", interpretation: "Artistic activities may align.", source_type: "calculated", confirmation_status: "needs_review", metadata: {} } },
  },
  summary: {
    combined_interest_profile: "Artistic-Investigative-Social",
    top_work_values: [{ value: "creativity", label: "Creativity", raw_score: 5, normalized_score: 100 }],
    ai_literacy_level: "Developing",
    ai_readiness_level: "Operational",
    change_readiness: "Ready for incremental upskilling",
    skills: [{ id: "skill-1", skill_id: "visual_communication", label: "Visual communication", category: "creative", level: 3, level_label: "Advanced", evidence_status: "supported_by_project", evidence_note: "Portfolio" }],
  },
  reflection_prompts: ["Which result felt most accurate?", "What small experiment could reduce uncertainty?"],
};

const matches = [
  {
    id: "match-current",
    session_id: "session-1",
    profile_id: profileId,
    category: "augment_current_profession",
    title: "AI Augmentation for Designer",
    role_family: "Current Profession",
    description: "Test AI inside current work.",
    alignment_score: 74,
    alignment_label: "Moderate alignment",
    explanation: "Start from the current profession before reskilling.",
    supporting_factors: ["Uses existing context."],
    conflicting_factors: ["Requires verification."],
    missing_skills: [],
    transferable_skills: [],
    ai_opportunities: ["Improve documentation"],
    next_step: "Test one AI-assisted workflow.",
    transition_difficulty: "low-to-moderate",
    time_horizon: "1-4 weeks",
    status: "suggested",
    assumptions: [],
    limitations: [],
    source_metadata: {},
    hypothesis_dimensions: {
      scores: { natural_fit: 50, capability_fit: 72, evidence_strength: 45, transition_feasibility: 80, ai_augmentation_opportunity: 70 },
      labels: { natural_fit: "Context only", capability_fit: "Moderate fit", evidence_strength: "Emerging fit", transition_feasibility: "Strong fit", ai_augmentation_opportunity: "Moderate fit" },
      explanations: {
        natural_fit: "Current profession context does not infer natural preference from history.",
        capability_fit: "Uses current work context and AI readiness.",
        evidence_strength: "Evidence remains provisional until practical validation.",
        transition_feasibility: "Small workflow experiment is feasible.",
        ai_augmentation_opportunity: "AI can support current work tasks.",
      },
    },
    dimension_scores: { natural_fit: 50, capability_fit: 72, evidence_strength: 45, transition_feasibility: 80, ai_augmentation_opportunity: 70 },
    dimension_labels: { natural_fit: "Context only", capability_fit: "Moderate fit", evidence_strength: "Emerging fit", transition_feasibility: "Strong fit", ai_augmentation_opportunity: "Moderate fit" },
    dimension_explanations: {
      natural_fit: "Current profession context does not infer natural preference from history.",
      capability_fit: "Uses current work context and AI readiness.",
      evidence_strength: "Evidence remains provisional until practical validation.",
      transition_feasibility: "Small workflow experiment is feasible.",
      ai_augmentation_opportunity: "AI can support current work tasks.",
    },
    factors: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "match-ai-product",
    session_id: "session-1",
    profile_id: profileId,
    category: "adjacent_professional_roles",
    title: "AI Product Designer",
    role_family: "Design and AI Product",
    description: "Design AI products.",
    alignment_score: 83,
    alignment_label: "Strong alignment",
    explanation: "This role appears to have strong potential alignment.",
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
    hypothesis_dimensions: {
      scores: { natural_fit: 86, capability_fit: 58, evidence_strength: 28, transition_feasibility: 64, ai_augmentation_opportunity: 82 },
      labels: { natural_fit: "Strong fit", capability_fit: "Emerging fit", evidence_strength: "Limited fit", transition_feasibility: "Moderate fit", ai_augmentation_opportunity: "Strong fit" },
      explanations: {
        natural_fit: "Uses interests, values, and work style only.",
        capability_fit: "Uses current skills, AI readiness, and relevant experience.",
        evidence_strength: "Portfolio evidence is useful but the AI evaluation gap remains unverified.",
        transition_feasibility: "Missing skills make this testable but not immediate.",
        ai_augmentation_opportunity: "The role has direct AI design support opportunities.",
      },
      rule_set: "human-discovery-career-hypothesis",
      rule_set_version: "v2",
    },
    dimension_scores: { natural_fit: 86, capability_fit: 58, evidence_strength: 28, transition_feasibility: 64, ai_augmentation_opportunity: 82 },
    dimension_labels: { natural_fit: "Strong fit", capability_fit: "Emerging fit", evidence_strength: "Limited fit", transition_feasibility: "Moderate fit", ai_augmentation_opportunity: "Strong fit" },
    dimension_explanations: {
      natural_fit: "Uses interests, values, and work style only.",
      capability_fit: "Uses current skills, AI readiness, and relevant experience.",
      evidence_strength: "Portfolio evidence is useful but the AI evaluation gap remains unverified.",
      transition_feasibility: "Missing skills make this testable but not immediate.",
      ai_augmentation_opportunity: "The role has direct AI design support opportunities.",
    },
    factors: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

async function mockAssessment(page: Page) {
  await page.addInitScript((id) => {
    localStorage.setItem("organicai_active_profile_id", id);
    localStorage.removeItem("organicai.auth.token");
  }, profileId);
  await page.route((url) => url.pathname.startsWith("/api/"), async (route) => {
    const url = new URL(route.request().url());
    if (await fulfillMockAuthRoute(route)) return;
    if (url.pathname === "/api/profiles") return route.fulfill({ json: [{ id: profileId, created_at: "2026-01-01T00:00:00Z", data: {} }] });
    if (url.pathname === `/api/v1/assessments/human-potential-career-assessment`) return route.fulfill({ json: definition });
    if (url.pathname === `/api/v1/profiles/${profileId}/assessment-sessions/current`) return route.fulfill({ json: { session: null, definition, disclaimer: definition.disclaimer, prefill } });
    if (url.pathname === `/api/v1/profiles/${profileId}/assessment-sessions`) return route.fulfill({ json: { session: { ...results.session, status: "in_progress", completed_at: null, responses: [] }, definition, disclaimer: definition.disclaimer, prefill } });
    if (url.pathname === `/api/v1/assessment-sessions/session-1/responses`) return route.fulfill({ json: { status: "saved", responses: [], session: { ...results.session, status: "in_progress" } } });
    if (url.pathname === `/api/v1/assessment-sessions/session-1/complete`) return route.fulfill({ json: { status: "completed", session: results.session, results, career_matches: matches } });
    if (url.pathname === `/api/v1/profiles/${profileId}/assessment-results`) return route.fulfill({ json: results });
    if (url.pathname === `/api/v1/profiles/${profileId}/career-matches`) return route.fulfill({ json: matches });
    if (url.pathname === `/api/v1/profiles/${profileId}/career-comparisons`) return route.fulfill({ json: { id: "comparison-1", profile_id: profileId, match_ids: ["match-current", "match-ai-product"], criteria_weights: {}, decision_priorities: {}, matrix: { items: matches.map((match) => ({ match_id: match.id, title: match.title, alignment_label: match.alignment_label, strengths: match.supporting_factors, challenges: match.conflicting_factors, uncertainties: [], next_experiment: match.next_step, evidence_required: match.missing_skills.length ? match.missing_skills : ["Interview a professional"], criteria: {} })) }, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" } });
    if (url.pathname.includes("/save") || url.pathname.includes("/reject") || url.pathname.includes("/request-alternative")) return route.fulfill({ json: matches[1] });
    if (url.pathname.includes("/create-roadmap-draft")) return route.fulfill({ json: { roadmap_id: "roadmap-1", career_match: matches[1], actions: [{ id: "action-1", title: "Validate the direction", horizon: "seven_days", status: "not_started" }] } });
    if (url.pathname === `/api/profiles/${profileId}`) return route.fulfill({ json: { id: profileId, primary_archetype: "Curious Explorer", secondary_archetype: "Responsible Builder", strengths: ["Visual communication"], values: ["Creativity"], fears: [], creative_tendencies: [], ai_collaboration_style: "Co-Creator", contribution_domains: [], recommended_learning_paths: [], uncertainties: [], risk_notes: [], ethical_note: "Exploratory profile.", created_at: "2026-01-01T00:00:00Z" } });
    if (url.pathname === `/api/profiles/${profileId}/feedback`) return route.fulfill({ json: { confirmed_nodes: [], hidden_recommendations: [], strength_adjustments: {}, archetype_override: null, user_notes: {} } });
    return route.fulfill({ json: [] });
  });
}

test("quick assessment produces career compatibility and comparison support", async ({ page }) => {
  await mockAssessment(page);
  await page.goto(`/workspace/${profileId}/assessment`);
  await expect(page.getByRole("heading", { name: "Choose an assessment path." })).toBeVisible();
  await expect(page.getByText("2 previously provided Natural Discovery values")).toBeVisible();
  const consent = page.getByLabel(/^I understand that this is self-reported decision support/);
  await consent.check();
  await expect(consent).toBeChecked();
  await page.getByRole("button", { name: /Start Quick Assessment/ }).click();
  await expect(page.getByText("Previously provided: confirm or edit.")).toBeVisible();
  await page.locator("article").filter({ hasText: "Current profession or role" }).locator("input").fill("Designer");
  await page.getByRole("button", { name: /^Continue/ }).click();
  await page.getByRole("radio", { name: "4" }).click();
  await page.getByRole("button", { name: /Complete Assessment/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/career-compatibility$`));
  await expect(page.getByRole("heading", { name: "Explore career directions before committing." })).toBeVisible();
  await expect(page.getByText("A. Augment Current Profession")).toBeVisible();
  await expect(page.getByText("AI Product Designer")).toBeVisible();
  await expect(page.getByText("Natural Fit").first()).toBeVisible();
  await expect(page.getByText("Capability Fit").first()).toBeVisible();
  await expect(page.getByText("Evidence Strength").first()).toBeVisible();
  await expect(page.getByText("Transition Feasibility").first()).toBeVisible();
  await expect(page.getByText("Strong fit").first()).toBeVisible();
  await expect(page.getByText("Limited fit").first()).toBeVisible();
  await page.getByLabel("Compare").nth(0).check();
  await page.getByLabel("Compare").nth(1).check();
  await page.getByRole("button", { name: /Compare selected/ }).click();
  await expect(page.getByRole("heading", { name: "Decision matrix" })).toBeVisible();
  await expect(page.locator('a[href*="/undefined"], a[href*="/null"]')).toHaveCount(0);
});
