import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const profileId = "demo-profile";

const app = {
  id: "app-1",
  profile_id: profileId,
  job_analysis_id: "analysis-1",
  title: "AI Product Designer",
  organisation: "Fictional Fjord Labs",
  source: "manual",
  deadline: "2026-08-20",
  status: "Preparing",
  contacts: [],
  notes: "",
  next_action: "Prepare interview.",
  auto_submitted: false,
  events: [{ id: "event-1", event_type: "created", from_status: "", to_status: "Preparing", description: "Tracker created.", created_at: "2026-07-21T09:00:00Z" }],
  stages: [],
  outcome: null,
  recalibration: null,
  updated_at: "2026-07-21T09:00:00Z",
};

function interview(id = "interview-1") {
  return {
    id,
    profile_id: profileId,
    application_id: app.id,
    job_analysis_id: "analysis-1",
    organisation: app.organisation,
    role: app.title,
    stage_type: "recruiter_screening",
    stage_label: "Recruiter screening",
    stage_order: 1,
    scheduled_at: "2026-07-25T10:00:00Z",
    timezone: "Europe/Bucharest",
    location_or_platform: "Video call",
    interview_format: "online",
    expected_duration_minutes: 30,
    participants: [{ role: "recruiter" }],
    preparation_status: "Not started",
    mock_session_status: "Not started",
    confidence_before: null,
    confidence_after: null,
    interview_result: "Unknown",
    follow_up_status: "Not started",
    notes: "",
    source: "application",
    user_confirmed: true,
    question_count: 0,
    mock_session_count: 0,
    has_preparation: false,
    has_reflection: false,
    application_status: app.status,
    updated_at: "2026-07-21T09:00:00Z",
  };
}

const preparation = {
  id: "prep-1",
  interview_id: "interview-1",
  sections: {
    role_summary: { confirmed_facts: ["Role: AI Product Designer", "Organisation: Fictional Fjord Labs"], missing_information: [] },
    stage_purpose: { likely_stage_expectations: ["Verify high-level fit, logistics, motivation, and application basics."] },
    confirmed_job_requirements: {
      confirmed_facts: [{ id: "req-1", text: "UX design and responsible AI", evidence: [{ evidence_id: "evidence-1" }] }],
    },
    weak_or_missing_evidence: { missing_information: [{ id: "req-2", text: "API integration" }] },
    likely_questions: { ai_generated_suggestions: ["Could you introduce yourself?"], uncertainty_note: "Questions are plausible, not guaranteed." },
  },
  readiness_checklist: [
    { label: "stage confirmed", status: "Completed" },
    { label: "job requirements reviewed", status: "Completed" },
    { label: "mock interview completed", status: "Not started", optional: true },
  ],
  source_notes: ["Application Tracker", "Evidence Passport"],
  language: "en",
  status: "ready_for_review",
  user_confirmed: false,
};

const question = {
  id: "question-1",
  interview_id: "interview-1",
  profile_id: profileId,
  category: "introduction",
  stage: "recruiter_screening",
  question_text: "Could you introduce yourself and highlight the evidence most relevant to this role?",
  why_it_may_be_asked: "This question is plausible for this interview stage because recruiter screens verify fit and context.",
  related_job_requirement_id: null,
  related_job_requirement: "",
  related_evidence: [{ evidence_id: "evidence-1", match_category: "Strong evidence" }],
  answer_objective: "Give a concise evidence-linked introduction.",
  risk_level: "medium",
  difficulty: "moderate",
  source_type: "stage_template",
  origin: "deterministic",
  saved_by_user: false,
};

function story(id = "story-1") {
  return {
    id,
    profile_id: profileId,
    title: "Explainable recommendation story",
    situation: "A recommendation interface needed clearer explanation.",
    task: "Create an evidence-based example.",
    action: "I designed evidence, uncertainty, correction, and rejection states.",
    result: "The prototype became easier to review.",
    reflection: "More user testing evidence would strengthen it.",
    skills_demonstrated: ["ux_ui", "responsible_ai"],
    evidence_links: [{ source: "demo" }],
    confidentiality_status: "public",
    claim_statuses: [{ status: "Supported" }],
    suitable_stages: ["behavioural", "portfolio"],
    tags: ["communication"],
    quality_status: "Ready",
    quality: { labels: ["Ready"] },
    status: "active",
    updated_at: "2026-07-21T09:00:00Z",
  };
}

async function mockInterviewJourney(page: Page) {
  let interviews: ReturnType<typeof interview>[] = [];
  let stories = [story()];
  let prep: typeof preparation | null = null;
  let questions: typeof question[] = [];
  let sessions: any[] = [];
  let reflection: any = null;
  let followUps: any[] = [];
  let offers: any[] = [];

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
    if (pathname === `/api/v1/profiles/${profileId}/applications`) return route.fulfill({ json: [app] });
    if (pathname === "/api/v1/interview-voice/status") return route.fulfill({ json: { enabled: false, provider: "elevenlabs", configured: false, default_language: "en", session_timeout_seconds: 1800, max_session_minutes: 30, transcript_retention_enabled: false, raw_audio_retention_enabled: false, text_mode_available: true, status: "disabled", privacy_notes: ["Provider credentials remain backend-only."] } });
    if (pathname === `/api/v1/profiles/${profileId}/interviews/dashboard`) return route.fulfill({ json: { profile_id: profileId, upcoming_interviews: interviews, active_preparation: interviews, saved_star_stories: stories, readiness_checklist: ["stage confirmed"], recent_mock_sessions: sessions, unresolved_evidence_gaps: [{ label: "API integration", count: 1 }], pending_reflections: [], application_stage_links: [], next_recommended_action: "Generate a preparation brief for the next interview.", source_notes: ["Interview Journey reuses Application Tracker and Evidence Passport."] } });
    if (pathname === `/api/v1/profiles/${profileId}/interviews` && method === "POST") {
      interviews = [interview()];
      return route.fulfill({ json: interviews[0] });
    }
    if (pathname === `/api/v1/profiles/${profileId}/interviews`) return route.fulfill({ json: interviews });
    if (pathname === "/api/v1/interviews/interview-1") return route.fulfill({ json: interviews[0] || interview() });
    if (pathname === "/api/v1/interviews/interview-1/preparation" && method === "POST") {
      prep = preparation;
      return route.fulfill({ json: prep });
    }
    if (pathname === "/api/v1/interviews/interview-1/preparation") {
      return prep ? route.fulfill({ json: prep }) : route.fulfill({ status: 404, json: { detail: "Preparation brief not found" } });
    }
    if (pathname === "/api/v1/interviews/interview-1/questions/generate") {
      questions = [question];
      return route.fulfill({ json: { interview_id: "interview-1", questions, generated: true } });
    }
    if (pathname === "/api/v1/interviews/interview-1/questions") return route.fulfill({ json: questions });
    if (pathname === "/api/v1/interview-questions/question-1/save") {
      questions = questions.map((item) => ({ ...item, saved_by_user: true }));
      return route.fulfill({ json: questions[0] });
    }
    if (pathname === "/api/v1/interview-questions/question-1/answer") return route.fulfill({ json: { id: "answer-1", question_id: "question-1", answer_objective: question.answer_objective, selected_evidence: question.related_evidence, suggested_structure: ["Answer", "Evidence", "Close"], possible_opening: "A relevant example is...", possible_closing: "The relevance is...", risk_areas: [], unsupported_claims: [], claim_statuses: [{ claim_text: "draft", status: "Partially supported" }], user_draft: "draft", revised_draft: "draft", user_confirmed: false } });
    if (pathname === `/api/v1/profiles/${profileId}/star-stories` && method === "POST") {
      stories = [story("story-2"), ...stories];
      return route.fulfill({ json: stories[0] });
    }
    if (pathname === `/api/v1/profiles/${profileId}/star-stories`) return route.fulfill({ json: stories });
    if (pathname.endsWith("/evaluate")) return route.fulfill({ json: { ...stories[0], quality_status: "Ready" } });
    if (pathname === "/api/v1/interviews/interview-1/mock-sessions" && method === "POST") {
      sessions = [{ id: "mock-1", interview_id: "interview-1", mode: "guided_practice", delivery_mode: "text", persona: "recruiter", status: "created", feedback: {}, rubric_results: [], turns: [] }];
      return route.fulfill({ json: sessions[0] });
    }
    if (pathname === "/api/v1/interviews/interview-1/mock-sessions") return route.fulfill({ json: sessions });
    if (pathname === "/api/v1/mock-sessions/mock-1/start") {
      sessions = [{ ...sessions[0], status: "in_progress" }];
      return route.fulfill({ json: sessions[0] });
    }
    if (pathname === "/api/v1/mock-sessions/mock-1/turns") {
      sessions = [{ ...sessions[0], turns: [{ id: "turn-1", question_text: question.question_text, answer_text: "answer", corrected_transcript: "answer", estimated_word_count: 24, follow_up_questions: ["What evidence supports that result?"], rubric: [{ criterion: "used relevant evidence", score: 3 }], feedback: {} }] }];
      return route.fulfill({ json: sessions[0].turns[0] });
    }
    if (pathname === "/api/v1/mock-sessions/mock-1/complete") {
      sessions = [{ ...sessions[0], status: "completed", feedback: { suggested_next_practice: "Practise the lowest-scoring answer criterion next.", no_single_opaque_score: true }, rubric_results: [{ criterion: "used relevant evidence", average_score: 3, attempts: 1 }] }];
      return route.fulfill({ json: sessions[0] });
    }
    if (pathname === "/api/v1/interviews/interview-1/reflection" && method === "POST") {
      reflection = { id: "reflection-1", interview_id: "interview-1", stage_completed: "recruiter_screening", completed_date: "2026-07-21", questions_remembered: ["Tell me about yourself."], strong_answers: [], weak_answers: ["Salary priorities"], unexpected_topics: [], confirmed_interviewer_feedback: "", user_interpretation: "User reflection only.", ai_interpretation: {}, next_step: "prepare_next_stage", confidence_before: 3, confidence_after: 4, additional_evidence_needed: ["API evidence"], outcome_status: "next_stage_received", user_confirmed: true };
      return route.fulfill({ json: reflection });
    }
    if (pathname === "/api/v1/interviews/interview-1/reflection") return reflection ? route.fulfill({ json: reflection }) : route.fulfill({ status: 404, json: { detail: "not found" } });
    if (pathname === "/api/v1/interviews/interview-1/follow-up-drafts" && method === "POST") {
      followUps = [{ id: "follow-1", draft_type: "thank_you", subject: "Thank you", body: "Thank you for speaking with me.", source_facts: [], status: "draft", auto_sent: false }];
      return route.fulfill({ json: followUps[0] });
    }
    if (pathname === "/api/v1/interviews/interview-1/follow-up-drafts") return route.fulfill({ json: followUps });
    if (pathname === "/api/v1/interviews/interview-1/application-events") {
      app.status = "Recruiter screening";
      return route.fulfill({ json: { status_update_confirmed: true, event: { id: "event-2" }, application: app } });
    }
    if (pathname === `/api/v1/profiles/${profileId}/offer-reviews` && method === "POST") {
      offers = [{ id: "offer-1", profile_id: profileId, application_id: app.id, interview_id: "interview-1", organisation: app.organisation, role: app.title, offer_items: { salary: 650000, currency: "NOK" }, user_priorities: ["remote flexibility"], review: { missing_information: ["working_hours"], draft_negotiation_points: ["I would like to discuss remote flexibility as part of the full package."], legal_or_financial_advice: false }, status: "draft" }];
      return route.fulfill({ json: offers[0] });
    }
    if (pathname === `/api/v1/profiles/${profileId}/offer-reviews`) return route.fulfill({ json: offers });
    return route.fulfill({ json: [] });
  });
}

test("interview journey covers preparation, text mock, reflection, stories, and offer review", async ({ page }) => {
  await mockInterviewJourney(page);
  await page.goto(`/workspace/${profileId}/interviews`);

  await expect(page.getByRole("heading", { name: /Evidence-based interview preparation/ })).toBeVisible();
  await expect(page.getByText(/Voice mock interview is disabled/)).toBeVisible();
  await page.getByRole("button", { name: /Create from tracker/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/interviews/interview-1/prepare$`));

  await page.getByRole("button", { name: /Generate preparation/ }).click();
  await expect(page.getByText(/confirmed facts/i).first()).toBeVisible();
  await expect(page.getByText(/Questions are plausible/)).toBeVisible();
  await page.getByRole("button", { name: /Build answer/ }).first().click();
  await expect(page.getByText(/Answer Builder checked draft claims/)).toBeVisible();

  await page.locator(".interview-tabs").getByRole("link", { name: "Mock" }).click();
  await page.getByRole("button", { name: /Run text mock/ }).click();
  await expect(page.getByText(/No opaque total score: yes/)).toBeVisible();
  await expect(page.getByText(/What evidence supports that result/)).toBeVisible();

  await page.locator(".interview-tabs").getByRole("link", { name: "Reflection" }).click();
  await page.getByRole("button", { name: /Save reflection/ }).click();
  await expect(page.getByText(/Reflection saved with confirmed feedback separated/)).toBeVisible();
  await page.getByRole("button", { name: /Draft thank-you/ }).click();
  await expect(page.getByText(/No email was sent/)).toBeVisible();
  await page.getByRole("button", { name: /Confirm tracker update/ }).click();
  await expect(page.getByText(/Application Tracker updated after explicit confirmation/)).toBeVisible();

  await page.locator(".interview-tabs").getByRole("link", { name: "STAR Stories" }).click();
  await page.getByRole("button", { name: /Add demo story/ }).click();
  await expect(page.getByText(/STAR story saved/)).toBeVisible();

  await page.locator(".interview-tabs").getByRole("link", { name: "Offer Review" }).click();
  await page.getByRole("button", { name: /Review offer/ }).click();
  await expect(page.getByText(/No legal or tax conclusion was made/)).toBeVisible();
  await expect(page.getByText(/Missing: working_hours/)).toBeVisible();
});

test("interview journey mobile layout does not overflow", async ({ page }) => {
  await mockInterviewJourney(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/workspace/${profileId}/interviews`);
  await expect(page.getByRole("heading", { name: /Evidence-based interview preparation/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
});
