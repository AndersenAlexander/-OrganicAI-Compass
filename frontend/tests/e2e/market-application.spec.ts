import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const profileId = "demo-profile";

function providerStatus() {
  return {
    active_provider: "demo",
    live_enabled: false,
    warning: "Live NAV feed is disabled or missing backend credentials; demo labour-market data is available.",
    providers: [
      {
        id: "demo",
        provider_name: "demo",
        display_name: "Demo labour-market provider",
        provider_type: "demo",
        enabled: true,
        configured: true,
        reachable: true,
        status: "ready",
        degraded_reason: "",
        degraded_mode_reason: "",
        documentation_url: "https://navikt.github.io/pam-stilling-feed/",
        documentation_checked_date: "2026-07-21",
        metadata: { credentials_backend_only: true, old_public_feed_used: false },
        updated_at: "2026-07-21T09:00:00Z",
      },
      {
        id: "nav_stilling_feed",
        provider_name: "nav_stilling_feed",
        display_name: "NAV Job Vacancy Feed",
        provider_type: "nav_stilling_feed",
        enabled: false,
        configured: false,
        reachable: false,
        status: "disabled",
        degraded_reason: "Live Norwegian labour-market data is not enabled.",
        degraded_mode_reason: "Live Norwegian labour-market data is not enabled.",
        documentation_url: "https://navikt.github.io/pam-stilling-feed/",
        documentation_checked_date: "2026-07-21",
        metadata: { credentials_backend_only: true, old_public_feed_used: false },
        updated_at: "2026-07-21T09:00:00Z",
      },
    ],
  };
}

const job = {
  id: "job-1",
  provider: "demo",
  external_job_id: "demo-job-1",
  source_url: "https://arbeidsplassen.nav.no/stillinger/stilling/demo-job-1",
  title: "AI Product Designer",
  employer: "Fjord Insight Labs AS",
  location: "Oslo, Oslo, Norway",
  municipality: "Oslo",
  country: "Norway",
  publication_time: "2026-07-21T09:00:00Z",
  expiry_time: "2026-08-20T09:00:00Z",
  is_active: true,
  inactive_reason: "",
  work_mode: "hybrid",
  employment_type: "permanent",
  full_time_part_time: "full_time",
  languages: ["English", "Norwegian useful"],
  skills: ["ux_ui", "responsible_ai", "accessibility", "evaluation", "apis"],
  career_families: ["AI Product Designer"],
  coverage: {
    covered_count: 3,
    missing_count: 2,
    total_count: 5,
    covered_skills: ["UX UI", "Responsible AI", "Accessibility"],
    missing_skills: ["Evaluation", "APIs"],
    label: "Partial coverage",
  },
  recommendation: {
    readiness_label: "Apply with positioning",
    reason: "Three requirements have evidence; two need positioning.",
    missing_skills: ["Evaluation", "APIs"],
    covered_skills: ["UX UI", "Responsible AI", "Accessibility"],
  },
  source_metadata: { old_public_feed_used: false },
};

function requirement(text = "UX design, responsible AI and accessibility") {
  return {
    id: "req-1",
    requirement_text: text,
    requirement_category: "skills",
    requirement_type: "mandatory",
    source_excerpt: text,
    source_location: "body",
    extraction_method: "deterministic",
    confidence: "medium",
    user_confirmation_state: text.includes("confirmed") ? "confirmed" : "needs_review",
    normalised_skill_id: "ux_ui",
    esco_uri: null,
    status: "active",
    matches: [
      {
        id: "match-1",
        requirement_id: "req-1",
        evidence_id: "evidence-1",
        evidence_type: "skill_evidence",
        evidence_strength: "Supported",
        match_category: "Strong evidence",
        recency_label: "Current",
        gap: "",
        transferable_evidence: [],
        recommended_action: "Use the project evidence in the application document.",
        deterministic_reason: "Evidence Passport contains a matching project artifact.",
      },
    ],
  };
}

function analysis(requirementText?: string) {
  return {
    id: "analysis-1",
    profile_id: profileId,
    job_id: "job-1",
    input_type: "saved_job",
    source_url: null,
    title: "AI Product Designer",
    organisation: "Fjord Insight Labs AS",
    location: "Oslo",
    deadline: "2026-08-20",
    raw_text_excerpt: "Mandatory requirements include UX design, responsible AI, accessibility and APIs.",
    structured_output: {},
    uncertainties: ["Norwegian language level is not fully specified."],
    ambiguous_statements: [],
    status: "analysed",
    extraction_version: "job-analysis-v1",
    requirements: [requirement(requirementText)],
    readiness: {
      id: "readiness-1",
      readiness_label: "Apply with positioning",
      reasons: ["Evidence covers core design requirements."],
      blockers: ["APIs need stronger proof."],
      recommended_actions: ["Add one API evidence note before submission."],
      deterministic_version: "job-readiness-v1",
      created_at: "2026-07-21T09:00:00Z",
    },
    job,
    updated_at: "2026-07-21T09:00:00Z",
  };
}

function document(id: string, type: "cv" | "cover_letter") {
  return {
    id,
    profile_id: profileId,
    job_analysis_id: "analysis-1",
    job_application_id: null,
    document_type: type,
    title: type === "cv" ? "CV for AI Product Designer" : "Cover Letter for AI Product Designer",
    language: "en",
    variant: "concise",
    status: "draft",
    evidence_lock_status: "Blocked claims present",
    readiness_status: "Needs evidence",
    export_warning_acknowledged: false,
    sections: [
      { id: `${id}-summary`, section_type: "summary", title: "Professional Summary", content: "Evidence-based transition profile.", include_in_export: true, order_index: 1 },
      { id: `${id}-projects`, section_type: "projects", title: "Relevant Projects", content: "Selected career experiment evidence.", include_in_export: true, order_index: 2 },
    ],
    claims: [
      {
        id: `${id}-claim-1`,
        document_id: id,
        section_id: `${id}-summary`,
        claim_text: "Developed production-ready AI systems.",
        claim_type: "unsupported_seniority",
        status: "Blocked",
        safer_alternative: "Developed locally evaluated AI-enabled prototypes with documented limitations.",
        deterministic_reason: "No evidence supports the stronger claim.",
        user_confirmation_state: "needs_review",
        blocked_for_export: true,
        evidence_links: [],
      },
    ],
    versions: [{ id: `${id}-version-1`, version_number: 1, warnings: ["Developed production-ready AI systems."], created_at: "2026-07-21T09:00:00Z" }],
    source_metadata: { auto_apply: false, ats_guarantee: false },
    updated_at: "2026-07-21T09:00:00Z",
  };
}

function researchEvaluation() {
  return {
    study: {
      id: "study-1",
      title: "OrganicAI Market-Aware Journey Evaluation",
      status: "draft",
      consent_version: "research-consent-v1",
      export_schema_version: "research-export-v1",
      protocol: { no_empirical_results_claimed: true },
      questions: [
        { id: "q1", construct: "career_decision_clarity", prompt: "I understand which career direction I should test next.", instrument_type: "custom_likert", scale_min: 1, scale_max: 5, order_index: 1 },
        { id: "q2", construct: "perceived_control", prompt: "I feel in control of my career process.", instrument_type: "custom_likert", scale_min: 1, scale_max: 5, order_index: 2 },
        { id: "sus-1", construct: "sus", prompt: "I thought the system was easy to use.", instrument_type: "sus", scale_min: 1, scale_max: 5, order_index: 101 },
      ],
    },
    summary: { participants: 0, sessions: 0 },
    consent_template: {
      plain_language_summary: "Research data is consent-based, pseudonymous, and excludes raw personal text from exports.",
      consent_version: "research-consent-v1",
    },
    profile_id: profileId,
  };
}

async function mockMarketApplication(page: Page) {
  let analyses: ReturnType<typeof analysis>[] = [];
  let docs: ReturnType<typeof document>[] = [];
  let apps: any[] = [];
  let requirementText = "UX design, responsible AI and accessibility";

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
    if (pathname === "/api/v1/market/providers/status") return route.fulfill({ json: providerStatus() });
    if (pathname === "/api/v1/market/providers/demo/sync") return route.fulfill({ json: { status: "completed", fetched_count: 1 } });
    if (pathname === `/api/v1/profiles/${profileId}/market-radar`) {
      return route.fulfill({
        json: {
          profile_id: profileId,
          provider_status: providerStatus(),
          preferences: null,
          active_jobs: [job],
          saved_filters: {},
          signal_run: { id: "signal-1", status: "ready", coverage_label: "Curated demonstration dataset", source_metadata: {}, created_at: "2026-07-21T09:00:00Z" },
          recurring_requirements: [{ id: "signal-skill-1", signal_type: "skill_frequency", label: "Responsible AI", trend_label: "Stable in the observed dataset", observation_count: 4, comparison_count: 3, confidence_label: "Moderate", limitations: [], factor: {} }],
          emerging_observed_requirements: [{ id: "signal-skill-2", signal_type: "skill_frequency", label: "Accessibility", trend_label: "Increasing in the observed dataset", observation_count: 3, comparison_count: 1, confidence_label: "Limited", limitations: [], factor: {} }],
          location_language: { municipalities: [{ label: "Oslo", count: 1 }], languages: [{ label: "English", count: 1 }] },
          limitations: ["Trend labels describe observed records in the local dataset only."],
        },
      });
    }
    if (pathname === `/api/v1/profiles/${profileId}/market-preferences` && method === "PUT") return route.fulfill({ json: { id: "prefs-1", profile_id: profileId, country: "Norway", municipality: "Oslo", user_confirmed_storage: true, work_modes: [], preferred_languages: [], employment_types: [], full_time_part_time: [], career_families: [], excluded_employers: [], excluded_keywords: [], updated_at: "2026-07-21T09:00:00Z" } });
    if (pathname === `/api/v1/profiles/${profileId}/job-analyses` && method === "POST") {
      analyses = [analysis(requirementText)];
      return route.fulfill({ json: analyses[0] });
    }
    if (pathname === `/api/v1/profiles/${profileId}/job-analyses`) return route.fulfill({ json: analyses });
    if (pathname === `/api/v1/profiles/${profileId}/job-analyses/analysis-1`) return route.fulfill({ json: analyses[0] || analysis(requirementText) });
    if (pathname.endsWith("/job-analyses/analysis-1/match")) return route.fulfill({ json: { matches: (analyses[0] || analysis(requirementText)).requirements[0].matches } });
    if (pathname.endsWith("/job-analyses/analysis-1/readiness")) return route.fulfill({ json: (analyses[0] || analysis(requirementText)).readiness });
    if (pathname === `/api/v1/profiles/${profileId}/job-requirements/req-1` && method === "PATCH") {
      requirementText = "UX design with accessibility evidence (user-confirmed interpretation)";
      analyses = [analysis(requirementText)];
      return route.fulfill({ json: analyses[0].requirements[0] });
    }
    if (pathname === `/api/v1/profiles/${profileId}/application-documents` && method === "POST") {
      const body = JSON.parse(route.request().postData() || "{}");
      const doc = document(body.document_type === "cover_letter" ? "cover-1" : "cv-1", body.document_type === "cover_letter" ? "cover_letter" : "cv");
      docs = [...docs.filter((item) => item.id !== doc.id), doc];
      return route.fulfill({ json: doc });
    }
    if (pathname === `/api/v1/profiles/${profileId}/application-documents`) return route.fulfill({ json: docs });
    if (pathname.includes("/document-claims/") && method === "PATCH") {
      docs = docs.map((doc) => ({ ...doc, evidence_lock_status: "Evidence locked", readiness_status: "Ready for user submission", claims: doc.claims.map((claim) => ({ ...claim, claim_text: claim.safer_alternative, status: "User-confirmed", blocked_for_export: false, user_confirmation_state: "confirmed" })) }));
      return route.fulfill({ json: docs[0]?.claims[0] });
    }
    if (pathname.includes("/application-documents/") && pathname.endsWith("/export")) return route.fulfill({ json: { document_id: "cv-1", export_format: "html_json", auto_apply: false, ats_guarantee: false, structured_json: { claims: docs[0]?.claims || [] } } });
    if (pathname === `/api/v1/profiles/${profileId}/applications` && method === "POST") {
      apps = [{
        id: "app-1",
        profile_id: profileId,
        job_id: "job-1",
        job_analysis_id: "analysis-1",
        cv_document_id: "cv-1",
        cover_letter_document_id: "cover-1",
        title: "AI Product Designer",
        organisation: "Fjord Insight Labs AS",
        source: "saved_job",
        deadline: "2026-08-20",
        status: "Preparing",
        contacts: [],
        notes: "",
        next_action: "Review documents before user submission.",
        auto_submitted: false,
        events: [{ id: "event-1", event_type: "created", from_status: "", to_status: "Preparing", description: "Tracker created.", created_at: "2026-07-21T09:00:00Z" }],
        stages: [],
        outcome: null,
        recalibration: null,
        job,
        updated_at: "2026-07-21T09:00:00Z",
      }];
      return route.fulfill({ json: apps[0] });
    }
    if (pathname === `/api/v1/profiles/${profileId}/applications`) return route.fulfill({ json: apps });
    if (pathname.endsWith("/applications/app-1/stages")) {
      apps = apps.map((app) => ({ ...app, status: "Recruiter screening", stages: [{ id: "stage-1", stage_type: "recruiter", result: "screening_completed", feedback: "Observed data.", probable_questions: [], created_at: "2026-07-21T09:00:00Z" }] }));
      return route.fulfill({ json: apps[0].stages[0] });
    }
    if (pathname.endsWith("/applications/app-1/outcome")) {
      apps = apps.map((app) => ({ ...app, status: "Recruiter screening", outcome: { id: "outcome-1", outcome: "Recruiter screening", outcome_date: "2026-07-21", employer_feedback: "", feedback_confirmed: false, user_interpretation: "Reached recruiter screening.", ai_interpretation: "", observed_data: {} }, events: [...app.events, { id: "event-2", event_type: "outcome_recorded", from_status: "Preparing", to_status: "Recruiter screening", description: "Outcome recorded.", created_at: "2026-07-21T09:30:00Z" }] }));
      return route.fulfill({ json: apps[0].outcome });
    }
    if (pathname.endsWith("/applications/app-1/recalibrate")) {
      apps = apps.map((app) => ({ ...app, recalibration: { id: "recalibration-1", status: "suggested", observed_data: {}, roadmap_changes_require_confirmation: true, suggestions: [{ suggestion_type: "strengthen_evidence", label: "Strengthen missing evidence before the next application.", requires_user_confirmation: true }] } }));
      return route.fulfill({ json: apps[0].recalibration });
    }
    if (pathname === `/api/v1/profiles/${profileId}/research-evaluation`) return route.fulfill({ json: researchEvaluation() });
    if (pathname.endsWith("/consent")) return route.fulfill({ json: { consent_given: true, participant: { pseudonymous_id: "p-abc123" } } });
    if (pathname.endsWith("/withdraw")) return route.fulfill({ json: { withdrawn: true } });
    if (pathname.endsWith("/sessions")) return route.fulfill({ json: { id: "session-1", status: "started" } });
    if (pathname.endsWith("/responses")) return route.fulfill({ json: { id: "session-1", status: "completed" } });
    if (pathname.endsWith("/metrics")) return route.fulfill({ json: { metrics: [{ id: "metric-1" }] } });
    if (pathname.endsWith("/exports")) return route.fulfill({ json: { id: "export-1", preview: { participant_summary: [{ pseudonymous_id: "p-abc123" }], excluded_fields: ["names", "email_addresses", "raw_cv_text", "raw_cover_letter_text"], survey_responses: [] }, demo_records_excluded: true } });
    return route.fulfill({ json: [] });
  });
}

test("market-aware application journey connects radar, analysis, documents, tracker, and research export", async ({ page }) => {
  await mockMarketApplication(page);
  await page.goto(`/workspace/${profileId}/market-radar`);

  await expect(page.getByRole("heading", { name: /Applications grounded in evidence/ })).toBeVisible();
  await expect(page.getByText(/Live NAV feed is disabled/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "AI Product Designer" }).first()).toBeVisible();

  await page.getByRole("button", { name: /Confirm preferences/ }).click();
  await expect(page.getByText(/Market preferences stored/)).toBeVisible();

  await page.locator(".market-job").first().getByRole("button", { name: /Analyze/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/job-analyzer/analysis-1$`));
  await expect(page.locator(".market-row b", { hasText: /UX design, responsible AI/ }).first()).toBeVisible();

  await page.getByRole("button", { name: /Correct/ }).first().click();
  await expect(page.getByText(/Requirement correction saved/)).toBeVisible();

  await page.getByRole("button", { name: /Create documents/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/application-studio/analysis-1$`));
  await expect(page.getByRole("heading", { name: "Application Studio" })).toBeVisible();
  await page.getByRole("button", { name: /Use safer/ }).first().click();
  await expect(page.getByText(/Safer claim wording applied/)).toBeVisible();
  await page.getByRole("button", { name: /Export with review/ }).first().click();
  await expect(page.getByText(/Document export generated/)).toBeVisible();

  await page.getByRole("button", { name: /Create tracker record/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/applications/app-1$`));
  await page.getByRole("button", { name: /Record outcome loop/ }).click();
  await expect(page.getByText(/My Roadmap was not changed automatically/)).toBeVisible();

  await page.goto(`/workspace/${profileId}/research-evaluation`);
  await page.getByRole("button", { name: /Run demo evaluation/ }).click();
  await expect(page.getByText(/pseudonymous export preview created/)).toBeVisible();
  await expect(page.getByText(/raw_cv_text/)).toBeVisible();
});

test("market application routes stay contained on mobile", async ({ page }) => {
  await mockMarketApplication(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/workspace/${profileId}/market-radar`);
  await expect(page.getByRole("heading", { name: /Applications grounded in evidence/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
});
