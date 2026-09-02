import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const profileId = "diagnostic-profile";
const sessionId = "human-review-experiment";
const actionId = "career-experiment-roadmap-action";
const title = "Prototype a Human Review Flow for an AI Feature";

const template = {
  id: "human-review-flow",
  title,
  target_role_family: "Human-Centred AI Product Designer",
  purpose: "Test a human-review intervention for an AI feature.",
  real_world_scenario: "An AI feature needs a clear human review and correction flow.",
  user_instructions: ["Prototype the review flow."],
  expected_deliverables: ["Human review flow prototype"],
  estimated_duration_minutes: 120,
  difficulty: "intermediate",
  required_skills: ["human_centred_ai"],
  skills_being_evaluated: ["human_centred_ai"],
  optional_prerequisites: [],
  allowed_tools: ["Design tool"],
  ai_assistance_policy: "AI assistance is allowed with disclosure.",
  reflection_questions: ["What review evidence is still missing?"],
  completion_criteria: ["A reviewable prototype exists."],
  evidence_generated: ["Experiment session"],
  version: "test-v1",
  source_metadata: {},
  active: true,
};

function experiment(roadmapActionId: string | null, status = "in_progress") {
  return {
    id: sessionId,
    profile_id: profileId,
    career_match_id: "career-match-human-ai",
    experiment_template_id: template.id,
    roadmap_action_id: roadmapActionId,
    mode: "guided",
    status,
    user_confirmed: true,
    confidence_label: "Additional evidence required",
    created_at: "2026-08-30T09:00:00Z",
    updated_at: "2026-08-30T09:10:00Z",
    started_at: "2026-08-30T09:05:00Z",
    submitted_at: null,
    evaluated_at: null,
    template,
    submission: null,
    result: null,
    reviews: [],
  };
}

function roadmap(added: boolean) {
  const action = {
    id: actionId,
    roadmap_id: "roadmap-1",
    user_id: "demo-user",
    profile_id: profileId,
    recommendation_id: sessionId,
    career_experiment_session_id: sessionId,
    career_hypothesis_id: "hypothesis-human-ai",
    evidence_gap_id: "gap-human-review",
    horizon: "seven_days",
    title,
    description: "Build a reviewable human correction flow for the AI feature.",
    reason: "Create practical evidence for the career hypothesis.",
    first_step: "Define the reviewer decision points.",
    success_criteria: "A testable review flow is available.",
    estimated_minutes: 120,
    effort: "medium",
    impact: "high",
    priority: 1,
    status: "in_progress",
    progress_percentage: 35,
    due_date: null,
    scheduled_date: null,
    completed_at: null,
    skipped_at: null,
    skip_reason: null,
    user_notes: "",
    source_type: "career_experiment",
    profile_signals: [],
    rag_sources: [],
    ethical_cautions: [],
    created_at: "2026-08-30T09:10:00Z",
    updated_at: "2026-08-30T09:10:00Z",
  };
  const actions = added ? [action] : [];
  return {
    id: "roadmap-1",
    profile_id: profileId,
    title: "Your Human-AI Growth Roadmap",
    summary: "A flexible guide.",
    status: "active",
    version: 1,
    created_at: "2026-08-30T08:00:00Z",
    updated_at: "2026-08-30T09:10:00Z",
    progress: {
      total_actions: actions.length,
      completed_actions: 0,
      in_progress_actions: added ? 1 : 0,
      skipped_actions: 0,
      blocked_actions: 0,
      completion_percentage: 0,
    },
    horizons: { seven_days: actions, thirty_days: [], six_months: [] },
    milestones: [],
    recalibration_notes: [],
    ethical_cautions: [],
    contribution_direction: "Human-centred AI product work",
    seven_days: actions,
    thirty_days: [],
    six_months: [],
    recommended_skills: [],
    ai_workflows: [],
    project_idea: "",
    social_contribution_idea: "",
  };
}

async function mockFlow(page: Page, options: { failConfirmation?: boolean } = {}) {
  let roadmapAdded = false;
  let started = false;
  let confirmationRequests = 0;

  await page.addInitScript((id) => {
    localStorage.setItem("organicai_active_profile_id", id);
    localStorage.removeItem("organicai.auth.token");
  }, profileId);

  await page.route((url) => url.pathname.startsWith("/api/"), async route => {
    const url = new URL(route.request().url());
    if (await fulfillMockAuthRoute(route, "demo")) return;
    if (url.pathname === `/api/profiles/${profileId}`) return route.fulfill({ json: { id: profileId, primary_archetype: "Curious Builder", secondary_archetype: "Systems Designer", strengths: [], values: [], fears: [], creative_tendencies: [], ai_collaboration_style: "Co-Creator", contribution_domains: [], recommended_learning_paths: [], uncertainties: [], risk_notes: [], ethical_note: "Demo.", created_at: "2026-01-01T00:00:00Z" } });
    if (url.pathname === `/api/profiles/${profileId}/feedback`) return route.fulfill({ json: { confirmed_nodes: [], hidden_recommendations: [], strength_adjustments: {}, archetype_override: null, user_notes: {} } });
    if (url.pathname === `/api/v1/profiles/${profileId}/career-resilience`) return route.fulfill({ json: {
      profile_id: profileId,
      workflow: ["Create career hypotheses", "Run a practical experiment"],
      life_event: null,
      urgent_actions: [],
      career_hypotheses: [{ id: "hypothesis-human-ai", career_match_id: "career-match-human-ai", title: "Human-Centred AI Product Designer", role_family: "AI Product", statement: "This is a hypothesis to test.", uncertainty_label: "Additional evidence required", status: "active" }],
      active_experiments: [experiment(roadmapAdded ? actionId : null, started ? "in_progress" : "planned")],
      evidence_updates: [], best_supported_paths: [], potential_programmes: [], next_recommended_action: "Test this direction",
    } });
    if (url.pathname === "/api/v1/career-experiments") return route.fulfill({ json: [template] });
    if (url.pathname === `/api/v1/profiles/${profileId}/career-experiments`) {
      if (route.request().method() === "POST") return route.fulfill({ json: experiment(null, "planned") });
      return route.fulfill({ json: [experiment(roadmapAdded ? actionId : null, started ? "in_progress" : "planned")] });
    }
    if (url.pathname === `/api/v1/career-experiment-sessions/${sessionId}/roadmap`) {
      confirmationRequests += 1;
      expect(route.request().postDataJSON()).toEqual({ confirmed: true });
      if (options.failConfirmation) return route.fulfill({ status: 503, json: { detail: "Roadmap persistence is temporarily unavailable." } });
      roadmapAdded = true;
      return route.fulfill({ json: experiment(actionId, "in_progress") });
    }
    if (url.pathname === `/api/v1/career-experiment-sessions/${sessionId}`) return route.fulfill({ json: experiment(roadmapAdded ? actionId : null, started ? "in_progress" : "planned") });
    if (url.pathname === `/api/v1/career-experiment-sessions/${sessionId}/start`) {
      started = true;
      return route.fulfill({ json: experiment(roadmapAdded ? actionId : null, "in_progress") });
    }
    if (url.pathname === `/api/v1/profiles/${profileId}/evidence-passport`) return route.fulfill({ json: null });
    if (url.pathname === `/api/v1/profiles/${profileId}/supported-paths`) return route.fulfill({ json: null });
    if (url.pathname === `/api/v1/profiles/${profileId}/job-loss-profile`) return route.fulfill({ json: null });
    if (url.pathname === `/api/v1/profiles/${profileId}/immediate-action-plan`) return route.fulfill({ json: null });
    if (url.pathname === `/api/v1/profiles/${profileId}/support-screening`) return route.fulfill({ json: null });
    if (url.pathname === `/api/v1/profiles/${profileId}/support-brief`) return route.fulfill({ json: null });
    if (url.pathname === `/api/roadmap/${profileId}`) return route.fulfill({ json: roadmap(roadmapAdded) });
    if (url.pathname === "/api/roadmaps/roadmap-1/check-ins") return route.fulfill({ json: [] });
    if (url.pathname === "/api/roadmaps/roadmap-1/versions") return route.fulfill({ json: roadmapAdded ? [{ version_number: 2, reason: `Career experiment added to roadmap: ${title}`, created_at: "2026-08-30T09:10:00Z" }] : [{ version_number: 1, reason: "Initial roadmap generated", created_at: "2026-08-30T08:00:00Z" }] });
    if (url.pathname === "/api/roadmaps/roadmap-1/events") return route.fulfill({ json: roadmapAdded ? [{ id: "event-1", roadmap_id: "roadmap-1", action_id: actionId, user_id: "demo-user", event_type: "career_experiment_added_to_roadmap", metadata: { title, experiment_id: sessionId }, created_at: "2026-08-30T09:10:00Z" }] : [] });
    return route.fulfill({ json: [] });
  });

  return { confirmationRequests: () => confirmationRequests };
}

test("persists a confirmed in-progress career experiment in My Roadmap across refresh", async ({ page }) => {
  const api = await mockFlow(page);
  await page.goto(`/workspace/${profileId}/career-resilience`);

  await page.getByRole("button", { name: /Test this career/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/experiments/${sessionId}$`));
  await page.getByRole("button", { name: "Start", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Experiment is in progress.");

  await page.getByTestId("add-experiment-to-roadmap").click();
  await expect(page.getByRole("status")).toContainText("Experiment added to My Roadmap after explicit confirmation.");
  await expect(page.getByText("Roadmap confirmed", { exact: true })).toBeVisible();
  await expect(page.getByTestId("add-experiment-to-roadmap")).toBeDisabled();
  expect(api.confirmationRequests()).toBe(1);

  await page.goto(`/roadmap/${profileId}`);
  await expect(page.getByRole("heading", { name: title })).toBeVisible();
  await expect(page.getByText("1 active", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "History", exact: true }).click();
  await expect(page.getByTestId("roadmap-history-event")).toContainText("Career experiment added to roadmap");

  await page.reload();
  await expect(page.getByRole("heading", { name: title })).toBeVisible();
  await expect(page.getByText("1 active", { exact: false })).toBeVisible();

  await page.goto(`/workspace/${profileId}/experiments/${sessionId}`);
  await expect(page.getByText("in progress", { exact: true })).toBeVisible();
  await expect(page.getByText("Roadmap confirmed", { exact: true })).toBeVisible();
});

test("does not falsely confirm when roadmap persistence fails and leaves retry available", async ({ page }) => {
  await mockFlow(page, { failConfirmation: true });
  await page.goto(`/workspace/${profileId}/experiments/${sessionId}`);

  await page.getByTestId("add-experiment-to-roadmap").click();
  await expect(page.getByRole("alert")).toContainText("Could not add this experiment to My Roadmap.");
  await expect(page.getByRole("alert")).toContainText("Please try again.");
  await expect(page.getByText("Roadmap confirmed", { exact: true })).toHaveCount(0);
  await expect(page.getByTestId("add-experiment-to-roadmap")).toBeEnabled();
});
