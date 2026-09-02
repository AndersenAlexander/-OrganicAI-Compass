import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const profileId = "employment-journey-profile";
const jobId = "job-human-centred-ai-product-designer";
const analysisId = "analysis-human-centred-ai-product-designer";
const applicationId = "application-human-centred-ai-product-designer";
const interviewId = "interview-technical-stage";

const profile = { id: profileId, created_at: "2026-08-31T10:00:00Z", data: {} };
const job = {
  id: jobId,
  provider: "demo-market",
  external_job_id: "human-centred-ai-product-designer-001",
  source_url: "https://jobs.example.test/human-centred-ai-product-designer-001",
  title: "Human-Centred AI Product Designer",
  employer: "Example Product Studio",
  location: "Oslo, Norway",
  municipality: "Oslo",
  country: "Norway",
  is_active: true,
  inactive_reason: "",
  work_mode: "hybrid",
  employment_type: "permanent",
  full_time_part_time: "full time",
  languages: ["English"],
  skills: ["UX/UI", "Responsible AI", "Communication"],
  career_families: ["AI Product"],
  source_metadata: {},
  recommendation: { readiness_label: "Ready for review", reason: "Uses the selected job identity.", missing_skills: [], covered_skills: ["UX/UI"] },
};

const analysis = {
  id: analysisId,
  profile_id: profileId,
  job_id: jobId,
  input_type: "saved_job",
  source_url: job.source_url,
  title: job.title,
  organisation: job.employer,
  location: job.location,
  deadline: null,
  raw_text_excerpt: "Mandatory requirements include UX/UI, responsible AI, and communication.",
  structured_output: {},
  uncertainties: ["User confirmed the extracted requirements."],
  ambiguous_statements: [],
  status: "confirmed",
  extraction_version: "job-analysis-v1",
  requirements: [{ id: "requirement-ux", requirement_text: "UX/UI and responsible AI", requirement_category: "skills", requirement_type: "mandatory", source_excerpt: "UX/UI", source_location: "job description", extraction_method: "deterministic", confidence: "high", user_confirmation_state: "confirmed", normalised_skill_id: "ux_ui", status: "active", matches: [] }],
  readiness: { id: "readiness-1", readiness_label: "Ready for review", reasons: [], blockers: [], recommended_actions: [], deterministic_version: "v1", created_at: profile.created_at },
  job,
  updated_at: profile.created_at,
};

function application() {
  return { id: applicationId, profile_id: profileId, job_id: jobId, job_analysis_id: analysisId, title: job.title, organisation: job.employer, source: "demo-market", deadline: null, status: "Preparing", contacts: [], notes: "User-entered application note.", next_action: "Review confirmed requirements.", auto_submitted: false, events: [{ id: "application-created", event_type: "created", from_status: "", to_status: "Preparing", description: "Tracker record created.", created_at: profile.created_at }], stages: [], outcome: null, recalibration: null, job, updated_at: profile.created_at };
}

function interview() {
  return { id: interviewId, profile_id: profileId, application_id: applicationId, job_analysis_id: analysisId, organisation: job.employer, role: job.title, stage_type: "technical", stage_label: "Technical interview", stage_order: 1, scheduled_at: "2026-09-15T10:00:00Z", timezone: "Europe/Bucharest", location_or_platform: "Video call", interview_format: "online", expected_duration_minutes: 45, participants: [{ role: "technical lead", user_confirmed: true }], preparation_status: "Ready for practice", mock_session_status: "Completed", confidence_before: null, confidence_after: null, interview_result: "Unknown", follow_up_status: "Not started", notes: "", source: "application", user_confirmed: true, question_count: 1, mock_session_count: 1, has_preparation: true, has_reflection: true, application_status: "Preparing", updated_at: profile.created_at };
}

async function mockEmploymentJourney(page: Page) {
  let savedApplication = false;
  let savedInterview = false;
  let savedStory = false;
  let savedMock = false;
  let savedReflection = false;
  let savedOffer = false;
  let applicationCreateCalls = 0;
  let interviewCreateCalls = 0;
  const questions = [{ id: "question-1", interview_id: interviewId, profile_id: profileId, application_id: applicationId, job_analysis_id: analysisId, category: "technical", stage: "technical", question_text: "How would you explain a responsible AI product trade-off?", why_it_may_be_asked: "It is based on the confirmed job requirement.", related_job_requirement_id: "requirement-ux", related_job_requirement: "UX/UI and responsible AI", related_evidence: [], answer_objective: "Use a concrete, bounded example.", risk_level: "medium", difficulty: "moderate", source_type: "confirmed_job_requirement", origin: "deterministic", saved_by_user: false }];
  const journal = [{ id: "decision-1", profile_id: profileId, title: "Offer decision for Example Product Studio", decision_type: "offer_decision", decision_summary: "The user will review written conditions before deciding.", context: "Linked to the saved technical interview.", selected_option: "Review before deciding", options: [], assumptions: [{ text: "Working hours need confirmation." }], uncertainty: {}, confidence: "", reversibility: "", evidence_links: [{ type: "offer_review", id: "offer-1" }], source_attributions: [], system_suggestions: [{ calculation: "Missing working hours remain unresolved." }], ai_explanations: [{ suggestion: "Compare the full package before deciding." }], evidence_observations: [{ reflection_id: "reflection-1", confirmed_feedback: true }], adviser_inputs: [], user_reasoning: "I will wait for written conditions before deciding.", adviser_comment_ids: [], interview_id: interviewId, job_analysis_id: analysisId, application_id: applicationId, status: "active", privacy_scope: "private", outcome_status: "", outcome: {}, reconsideration_reason: "", roadmap_mutation_allowed: false, reminder_status: "not_scheduled", version_number: 1, created_at: profile.created_at, updated_at: profile.created_at }];

  await page.addInitScript((id) => {
    localStorage.setItem("organicai_active_profile_id", id);
    localStorage.removeItem("organicai.auth.token");
  }, profileId);

  await page.route((url) => url.pathname.startsWith("/api/"), async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const method = route.request().method();
    if (await fulfillMockAuthRoute(route, "demo")) return;
    if (path === `/api/profiles/${profileId}`) return route.fulfill({ json: profile });
    if (path === "/api/profiles") return route.fulfill({ json: [profile] });
    if (path === "/api/diagnostics") return route.fulfill({ json: [] });
    if (path === "/api/roadmap") return route.fulfill({ json: [{ id: "roadmap-unchanged", profile_id: profileId, data: {}, created_at: profile.created_at }] });
    if (path === `/api/roadmap/${profileId}`) return route.fulfill({ json: { id: "roadmap-unchanged", profile_id: profileId, title: "User-confirmed roadmap", status: "active", version: 1, progress: { completion_percentage: 0, completed_actions: 0, in_progress_actions: 0 }, horizons: { seven_days: [], thirty_days: [], six_months: [] }, created_at: profile.created_at, updated_at: profile.created_at } });
    if (path.startsWith("/api/v1/roadmaps/")) return route.fulfill({ json: [] });
    if (path === "/api/v1/market/providers/status") return route.fulfill({ json: { providers: [], active_provider: "demo-market", live_enabled: false, warning: "Demo only." } });
    if (path === `/api/v1/profiles/${profileId}/market-radar`) return route.fulfill({ json: { profile_id: profileId, provider_status: { providers: [], active_provider: "demo-market", live_enabled: false, warning: "Demo only." }, preferences: null, active_jobs: [job], saved_filters: {}, signal_run: { id: "signal-1", status: "completed", coverage_label: "Demo", source_metadata: {}, created_at: profile.created_at }, recurring_requirements: [], emerging_observed_requirements: [], location_language: { municipalities: [], languages: [] }, limitations: [] } });
    if (path === `/api/v1/profiles/${profileId}/job-analyses` && method === "POST") return route.fulfill({ json: analysis });
    if (path === `/api/v1/profiles/${profileId}/job-analyses`) return route.fulfill({ json: [analysis] });
    if (path.includes(`/job-analyses/${analysisId}/match`)) return route.fulfill({ json: { matches: [] } });
    if (path.includes(`/job-analyses/${analysisId}/readiness`)) return route.fulfill({ json: analysis.readiness });
    if (path === `/api/v1/profiles/${profileId}/application-documents`) return route.fulfill({ json: [] });
    if (path === `/api/v1/profiles/${profileId}/research-evaluation`) return route.fulfill({ json: {} });
    if (path === `/api/v1/profiles/${profileId}/applications` && method === "POST") {
      const payload = route.request().postDataJSON();
      expect(payload.job_id).toBe(jobId);
      expect(payload.job_analysis_id).toBe(analysisId);
      applicationCreateCalls += 1;
      savedApplication = true;
      return route.fulfill({ json: application() });
    }
    if (path === `/api/v1/profiles/${profileId}/applications`) return route.fulfill({ json: savedApplication ? [application()] : [] });
    if (path === `/api/v1/profiles/${profileId}/interviews/dashboard`) return route.fulfill({ json: { profile_id: profileId, upcoming_interviews: savedInterview ? [interview()] : [], active_preparation: savedInterview ? [interview()] : [], saved_star_stories: savedStory ? [{ id: "story-1" }] : [], readiness_checklist: [], recent_mock_sessions: savedMock ? [{ id: "mock-1" }] : [], unresolved_evidence_gaps: [], pending_reflections: [], application_stage_links: savedInterview ? [{ interview_id: interviewId, application_id: applicationId, application_status: "Preparing" }] : [], next_recommended_action: savedReflection ? "Record the interview outcome." : "Prepare for the selected interview.", source_notes: [] } });
    if (path === `/api/v1/profiles/${profileId}/interviews` && method === "POST") {
      const payload = route.request().postDataJSON();
      expect(payload.application_id).toBe(applicationId);
      interviewCreateCalls += 1;
      savedInterview = true;
      return route.fulfill({ json: interview() });
    }
    if (path === `/api/v1/profiles/${profileId}/interviews`) return route.fulfill({ json: savedInterview ? [interview()] : [] });
    if (path === `/api/v1/interviews/${interviewId}`) return route.fulfill({ json: interview() });
    if (path === `/api/v1/interviews/${interviewId}/preparation` && method === "POST") return route.fulfill({ json: { id: "preparation-1", interview_id: interviewId, application_id: applicationId, sections: { confirmed_job_requirements: { confirmed_facts: ["UX/UI and responsible AI"] } }, readiness_checklist: [], source_notes: [], language: "en", status: "ready_for_review", user_confirmed: false } });
    if (path === `/api/v1/interviews/${interviewId}/preparation`) return route.fulfill({ json: { id: "preparation-1", interview_id: interviewId, application_id: applicationId, sections: { confirmed_job_requirements: { confirmed_facts: ["UX/UI and responsible AI"] } }, readiness_checklist: [], source_notes: [], language: "en", status: "ready_for_review", user_confirmed: false } });
    if (path === `/api/v1/interviews/${interviewId}/questions/generate`) return route.fulfill({ json: { interview_id: interviewId, questions, generated: true } });
    if (path === `/api/v1/interviews/${interviewId}/questions`) return route.fulfill({ json: questions });
    if (path === `/api/v1/profiles/${profileId}/star-stories` && method === "POST") { savedStory = true; return route.fulfill({ json: { id: "story-1", profile_id: profileId, title: "Interview-ready explainability story", situation: "", task: "", action: "", result: "", reflection: "", skills_demonstrated: [], evidence_links: [], confidentiality_status: "public", claim_statuses: [], suitable_stages: [], tags: [], quality_status: "Ready", quality: {}, status: "active", user_confirmed: true, updated_at: profile.created_at } }); }
    if (path === `/api/v1/profiles/${profileId}/star-stories`) return route.fulfill({ json: savedStory ? [{ id: "story-1", profile_id: profileId, title: "Interview-ready explainability story", situation: "", task: "", action: "", result: "", reflection: "", skills_demonstrated: [], evidence_links: [], confidentiality_status: "public", claim_statuses: [], suitable_stages: [], tags: [], quality_status: "Ready", quality: {}, status: "active", user_confirmed: true, updated_at: profile.created_at }] : [] });
    if (path === `/api/v1/interviews/${interviewId}/mock-sessions` && method === "POST") return route.fulfill({ json: { id: "mock-1", interview_id: interviewId, application_id: applicationId, mode: "guided_practice", delivery_mode: "text", persona: "technical_lead", panel_personas: ["technical_lead", "product_lead"], status: "created", feedback: {}, rubric_results: [], turns: [] } });
    if (path === `/api/v1/interviews/${interviewId}/mock-sessions`) return route.fulfill({ json: savedMock ? [{ id: "mock-1", interview_id: interviewId, application_id: applicationId, mode: "guided_practice", delivery_mode: "text", persona: "technical_lead", panel_personas: ["technical_lead", "product_lead"], status: "completed", feedback: { no_single_opaque_score: true, suggested_next_practice: "Practise the lowest-scoring answer criterion next." }, rubric_results: [{ criterion: "used relevant evidence", average_score: 3, attempts: 1 }], turns: [] }] : [] });
    if (path === "/api/v1/mock-sessions/mock-1/start") return route.fulfill({ json: { id: "mock-1", interview_id: interviewId, status: "in_progress" } });
    if (path === "/api/v1/mock-sessions/mock-1/turns") return route.fulfill({ json: { id: "turn-1", question_text: questions[0].question_text, answer_text: "answer", corrected_transcript: "answer", estimated_word_count: 20, follow_up_questions: [], rubric: [], feedback: {} } });
    if (path === "/api/v1/mock-sessions/mock-1/complete") { savedMock = true; return route.fulfill({ json: { id: "mock-1", interview_id: interviewId, application_id: applicationId, mode: "guided_practice", delivery_mode: "text", persona: "technical_lead", panel_personas: ["technical_lead", "product_lead"], status: "completed", feedback: { no_single_opaque_score: true, suggested_next_practice: "Practise the lowest-scoring answer criterion next." }, rubric_results: [{ criterion: "used relevant evidence", average_score: 3, attempts: 1 }], turns: [] } }); }
    if (path === `/api/v1/interviews/${interviewId}/reflection` && method === "POST") { savedReflection = true; return route.fulfill({ json: { id: "reflection-1", interview_id: interviewId, application_id: applicationId, stage_completed: "technical", questions_remembered: [], strong_answers: [], weak_answers: ["API evidence"], unexpected_topics: [], confirmed_interviewer_feedback: "", user_interpretation: "User reflection only.", ai_interpretation: {}, system_suggestion: [], next_step: "prepare_next_stage", additional_evidence_needed: ["API evidence"], outcome_status: "UNKNOWN", user_confirmed: true } }); }
    if (path === `/api/v1/interviews/${interviewId}/reflection`) return route.fulfill({ json: savedReflection ? { id: "reflection-1", interview_id: interviewId, application_id: applicationId, stage_completed: "technical", questions_remembered: [], strong_answers: [], weak_answers: ["API evidence"], unexpected_topics: [], confirmed_interviewer_feedback: "", user_interpretation: "User reflection only.", ai_interpretation: {}, system_suggestion: [], next_step: "prepare_next_stage", additional_evidence_needed: ["API evidence"], outcome_status: "UNKNOWN", user_confirmed: true } : null });
    if (path === `/api/v1/profiles/${profileId}/offer-reviews` && method === "POST") { const payload = route.request().postDataJSON(); expect(payload.application_id).toBe(applicationId); savedOffer = true; return route.fulfill({ json: { id: "offer-1", profile_id: profileId, application_id: applicationId, interview_id: null, organisation: job.employer, role: job.title, offer_items: { salary: 900000, currency: "NOK" }, user_priorities: ["remote flexibility"], review: { missing_information: ["working_hours"], legal_or_financial_advice: false }, status: "draft" } }); }
    if (path === `/api/v1/profiles/${profileId}/offer-reviews`) return route.fulfill({ json: savedOffer ? [{ id: "offer-1", profile_id: profileId, application_id: applicationId, interview_id: null, organisation: job.employer, role: job.title, offer_items: { salary: 900000, currency: "NOK" }, user_priorities: ["remote flexibility"], review: { missing_information: ["working_hours"], legal_or_financial_advice: false }, status: "draft" }] : [] });
    if (path === "/api/v1/interview-voice/status") return route.fulfill({ json: { enabled: false, status: "disabled", provider: "none", configured: false, default_language: "en", session_timeout_seconds: 0, max_session_minutes: 0, transcript_retention_enabled: false, raw_audio_retention_enabled: false, text_mode_available: true, privacy_notes: [] } });
    if (path === `/api/v1/profiles/${profileId}/decision-journal`) return route.fulfill({ json: journal });
    if (path === `/api/v1/profiles/${profileId}/decision-journal/research-export`) return route.fulfill({ json: {} });
    if (path === `/api/v1/profiles/${profileId}/career-resilience`) return route.fulfill({ json: { career_hypotheses: [{ id: "hypothesis-human-centred-ai", career_match_id: "match-human-centred-ai", canonical_direction_id: "human-centred-ai-product-designer", title: job.title, role_family: "AI product", statement: "Current canonical direction.", uncertainty_label: "moderate", status: "active" }], evidence_states: [{ hypothesis_id: "hypothesis-human-centred-ai", career_match_id: "match-human-centred-ai", canonical_direction_id: "human-centred-ai-product-designer", state: "evidence_sufficient", recommendation: { version: "adaptive-evidence-v1", state: "evidence_sufficient", rank: null, score: null, score_breakdown: {}, targeted_gap_skill_ids: [], unresolved_gap_skill_ids: [], already_practically_verified_skill_ids: ["ideation", "ux-ui", "product-thinking", "responsible-ai", "risk-reasoning", "communication"], rationale: [], ranked_template_ids: [] } }], active_experiments: [], evidence_gaps: [], next_recommended_action: "Record the interview outcome." } });
    if (path === `/api/profiles/${profileId}/journey-state`) return route.fulfill({ json: { profile_id: profileId, has_market_activity: savedApplication, has_application_activity: savedApplication, has_interview_activity: savedInterview, employment_summary: { application_count: savedApplication ? 1 : 0, interview_count: savedInterview ? 1 : 0, completed_interview_count: savedReflection ? 1 : 0, offer_review_count: savedOffer ? 1 : 0, roadmap_mutated: false }, interview_summary: savedInterview ? { id: interviewId, lifecycle_status: savedReflection ? "COMPLETED" : "PLANNED", stage_type: "technical", has_reflection: savedReflection, outcome: "Unknown", next_action: savedReflection ? "Record the interview outcome." : "Prepare for the selected interview." } : null } });
    if (path === `/api/recommendations/profile/${profileId}`) return route.fulfill({ json: [] });
    return route.fulfill({ json: [] });
  });

  return { counts: () => ({ applicationCreateCalls, interviewCreateCalls }) };
}

test("employment journey keeps the selected job/application/interview chain after refresh", async ({ page }) => {
  const flow = await mockEmploymentJourney(page);

  await page.goto(`/workspace/${profileId}/market-radar`);
  await expect(page.getByRole("heading", { name: job.title, level: 3, exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Analyze" }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/job-analyzer/${analysisId}$`));
  await page.reload();
  await expect(page.getByRole("heading", { name: job.title, level: 2, exact: true })).toBeVisible();

  await page.goto(`/workspace/${profileId}/application-studio/${analysisId}`);
  await page.getByRole("button", { name: /Create tracker record/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/applications/${applicationId}$`));
  await page.reload();
  await expect(page.getByRole("heading", { name: job.title, level: 3, exact: true })).toBeVisible();
  await expect(page.getByText(/Tracker record created/)).toBeVisible();

  await page.goto(`/workspace/${profileId}/interviews`);
  await page.getByLabel("Application for this interview").selectOption(applicationId);
  await page.getByRole("button", { name: /Create from tracker/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/interviews/${interviewId}/prepare$`));
  await page.getByRole("button", { name: /Generate preparation/ }).click();
  await expect(page.getByText("UX/UI and responsible AI")).toBeVisible();
  await page.reload();
  await expect(page.getByText("UX/UI and responsible AI")).toBeVisible();

  await page.goto(`/workspace/${profileId}/star-stories`);
  await page.getByRole("button", { name: /Add demo story/ }).click();
  await expect(page.getByText(/STAR story saved/)).toBeVisible();
  await page.reload();
  await expect(page.getByText("Interview-ready explainability story")).toBeVisible();

  await page.goto(`/workspace/${profileId}/interviews/${interviewId}/mock`);
  await page.getByRole("button", { name: /Run text mock/ }).click();
  await expect(page.getByText(/No opaque total score: yes/)).toBeVisible();
  await page.reload();
  await expect(page.getByText(/No opaque total score: yes/)).toBeVisible();

  await page.goto(`/workspace/${profileId}/interviews/${interviewId}/reflection`);
  await page.getByRole("button", { name: /Save reflection/ }).click();
  await expect(page.getByText(/Reflection saved with confirmed feedback separated/)).toBeVisible();
  await page.reload();
  await expect(page.getByText(/User interpretation: User reflection only/)).toBeVisible();

  await page.goto(`/workspace/${profileId}/offer-review`);
  await page.getByLabel("Application to link to offer review").selectOption(applicationId);
  await page.getByRole("button", { name: /Review offer/ }).click();
  await expect(page.getByText("Missing: working_hours")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Missing: working_hours")).toBeVisible();

  await page.goto(`/workspace/${profileId}/decision-journal`);
  await expect(page.getByText("Offer decision for Example Product Studio")).toBeVisible();
  await page.getByText("Separate decision record", { exact: true }).click();
  await expect(page.getByText("AI suggestions", { exact: true })).toBeVisible();
  await expect(page.getByText("System suggestions and calculations", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("Offer decision for Example Product Studio")).toBeVisible();

  await page.goto("/dashboard");
  await expect(page.getByTestId("journey-current-direction")).toHaveText(job.title);
  await expect(page.getByTestId("journey-evidence-state")).toContainText("evidence sufficient");
  await expect(page.getByTestId("journey-employment-summary")).toContainText("Applications: 1 · Interviews: 1 · Completed interviews: 1 · Offer reviews: 1");
  await expect(page.getByText("Interview and offer events do not mutate the roadmap automatically.")).toBeVisible();
  await page.reload();
  await expect(page.getByTestId("journey-employment-summary")).toContainText("Applications: 1 · Interviews: 1 · Completed interviews: 1 · Offer reviews: 1");
  expect(flow.counts()).toEqual({ applicationCreateCalls: 1, interviewCreateCalls: 1 });
});
