import { expect, test, type Page } from "@playwright/test";
import { fulfillMockAuthRoute } from "./utils/authSession";

const profileId = "demo-profile";

type CommentState = "pending" | "accepted" | "rejected";

function connection(includeToken = false) {
  return {
    id: "connection-1",
    profile_id: profileId,
    display_name: "Save to OrganicAI Compass",
    status: "active",
    permissions: ["capture_current_tab", "create_job_capture"],
    expires_at: "2026-08-07T09:00:00Z",
    last_used_at: null,
    revoked_at: null,
    connection_token: includeToken ? "ext_demo_token_visible_once" : undefined,
    token_visible_once: includeToken,
    last_capture: null,
    created_at: "2026-07-24T09:00:00Z",
  };
}

function capture(status = "Needs review") {
  return {
    id: "capture-1",
    profile_id: profileId,
    job_analysis_id: status === "Analysed" ? "analysis-1" : null,
    source_url: "https://jobs.example.test/roles/ai-product-designer",
    page_title: "AI Product Designer - Aurora Learning Lab",
    detected_title: "AI Product Designer",
    detected_employer: "Aurora Learning Lab",
    source_domain: "jobs.example.test",
    sanitised_text: "Mandatory requirements include UX design, responsible AI, accessibility and evaluation.",
    captured_text_preview: "Mandatory requirements include UX design, responsible AI, accessibility and evaluation.",
    selected_text: "UX design, responsible AI, accessibility and evaluation.",
    confirmed_fields: {},
    capture_method: "user_triggered_browser_extension",
    requested_action: "save_and_analyse",
    status,
    quality_warnings: status === "Needs review" ? ["Please review captured content before saving."] : [],
    extension_version: "0.1.0",
    captured_at: "2026-07-24T09:00:00Z",
    updated_at: "2026-07-24T09:00:00Z",
  };
}

function advisorComment(id: string, status: CommentState = "pending") {
  return {
    id,
    share_id: "share-1",
    profile_id: profileId,
    adviser_display_name: "Dr. Ingrid Solheim",
    adviser_role: "Academic supervisor",
    target_type: "Evidence Passport",
    target_id: "evidence-1",
    suggestion_type: id === "comment-2" ? "Learning recommendation" : "Evidence review",
    comment_text:
      id === "comment-2"
        ? "Run a short technical validation experiment before changing the roadmap."
        : "The portfolio evidence partially supports the stronger design claim.",
    evidence_validation: id === "comment-2" ? "Recommendation only" : "Partially supports",
    supporting_reference: "Portfolio review note",
    status,
    user_response: "",
    provenance: "human_adviser",
    created_at: "2026-07-24T09:00:00Z",
    updated_at: "2026-07-24T09:00:00Z",
  };
}

function advisorShare(comments: ReturnType<typeof advisorComment>[] = [], includeToken = false) {
  return {
    id: "share-1",
    profile_id: profileId,
    adviser_display_name: "Dr. Ingrid Solheim",
    adviser_role: "Academic supervisor",
    purpose: "Review selected career hypothesis, Evidence Passport, Job Analysis and journal entries.",
    permission_level: "Suggest changes",
    allowed_sections: ["Career Hypotheses", "Evidence Passport", "Job Analysis", "Career Decision Journal"],
    allowed_actions: ["view", "comment", "suggest_changes", "validate_selected_evidence"],
    export_allowed: false,
    status: "active",
    expires_at: "2026-08-07T09:00:00Z",
    access_attempts: 1,
    max_access_attempts: 25,
    last_accessed_at: null,
    comments,
    sections: [
      { name: "Career Hypotheses", items: [{ title: "AI Product Designer" }], limitations: ["Selected hypothesis only."] },
      { name: "Evidence Passport", items: [{ skill_label: "Human Centred AI" }], limitations: ["No full profile access."] },
    ],
    limitations: ["No sensitive job-loss data.", "No private transcripts."],
    share_token: includeToken ? "advisor_share_token" : undefined,
    review_url: includeToken ? "/advisor-review/advisor_share_token" : undefined,
    token_visible_once: includeToken,
    created_at: "2026-07-24T09:00:00Z",
  };
}

function personas() {
  return [
    { persona_id: "recruiter", role_label: "Recruiter", purpose: "Screen motivation and clarity.", question_categories: ["motivation", "availability", "communication"], expected_depth: "concise", follow_up_style: "clarifying", terminology_level: "general", allowed_evidence_focus: ["career narrative"], maximum_question_count: 3 },
    { persona_id: "hiring_manager", role_label: "Hiring Manager", purpose: "Assess ownership and team impact.", question_categories: ["ownership", "impact", "collaboration"], expected_depth: "specific", follow_up_style: "behavioural", terminology_level: "team", allowed_evidence_focus: ["STAR stories"], maximum_question_count: 3 },
    { persona_id: "technical_lead", role_label: "Technical Lead", purpose: "Check implementation reasoning.", question_categories: ["architecture", "testing", "security"], expected_depth: "technical", follow_up_style: "probing", terminology_level: "technical", allowed_evidence_focus: ["confirmed requirements"], maximum_question_count: 3 },
    { persona_id: "design_lead", role_label: "Design Lead", purpose: "Review user-centred decisions.", question_categories: ["accessibility", "trade-offs"], expected_depth: "portfolio", follow_up_style: "evidence-led", terminology_level: "design", allowed_evidence_focus: ["portfolio evidence"], maximum_question_count: 3 },
  ];
}

function panelSession(turns: unknown[] = []) {
  return {
    id: "panel-session-1",
    interview_id: "interview-1",
    profile_id: profileId,
    mode: "panel",
    delivery_mode: "text",
    persona: "panel",
    status: turns.length ? "completed" : "active",
    panel_config: { personas: ["recruiter", "hiring_manager", "technical_lead"], sequence_mode: "round_robin" },
    questions: [
      { id: "q1", question_text: "How does your UX evidence match the confirmed accessibility requirement?", category: "motivation", source_type: "confirmed_job_requirement", related_job_requirement: "Accessibility", persona_id: "recruiter", persona_label: "Recruiter", turn_index: 1 },
      { id: "q2", question_text: "Describe ownership of a responsible AI decision and its impact.", category: "ownership", source_type: "confirmed_job_requirement", related_job_requirement: "Responsible AI", persona_id: "hiring_manager", persona_label: "Hiring Manager", turn_index: 2 },
      { id: "q3", question_text: "What testing evidence supports your AI integration work?", category: "testing", source_type: "confirmed_job_requirement", related_job_requirement: "Evaluation", persona_id: "technical_lead", persona_label: "Technical Lead", turn_index: 3 },
    ],
    turns,
    feedback: {
      shared_strengths: ["Answers cite evidence."],
      persona_feedback: {
        recruiter: { strengths: ["Clear motivation"], weaknesses: ["Tighten timeline answer"] },
        hiring_manager: { strengths: ["Ownership visible"], weaknesses: ["Quantify impact"] },
        technical_lead: { strengths: ["Testing mentioned"], weaknesses: ["Add failure-handling evidence"] },
      },
      unsupported_claims: ["production-ready"],
      prohibited_inferences: ["honesty", "personality", "emotion", "mental_state", "employability", "accent_quality"],
    },
    rubric_results: [],
    no_single_opaque_score: true,
    updated_at: "2026-07-24T09:00:00Z",
  };
}

const roleFamilies = ["AI and software", "Design and product", "Consulting and strategy", "Learning and communication"];
const roleTitles = [
  "RAG Application Developer",
  "AI Integration Developer",
  "Frontend Developer",
  "AI Product Engineer",
  "AI Product Designer",
  "UX Designer",
  "Service Designer",
  "Creative Technologist",
  "AI Integration Consultant",
  "Digital Transformation Consultant",
  "Human-Centred AI Specialist",
  "Technology Consultant",
  "Learning Experience Designer",
  "Technical Trainer",
  "AI Career Coach",
  "Digital Learning Specialist",
];

const roles = roleTitles.map((title, index) => ({
  id: `role-${index + 1}`,
  role_id: `role-${index + 1}`,
  slug: title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""),
  title,
  aliases: [title],
  career_family: roleFamilies[Math.floor(index / 4)],
  summary: `${title} connects human strengths, evidence and AI-supported work without unsupported market claims.`,
  profile: {
    technical_skills: ["UX research", "Responsible AI", "Evaluation", "APIs"],
    typical_responsibilities: ["Translate user needs into evidence-based decisions.", "Document assumptions and limitations."],
    tasks_requiring_human_accountability: ["Ethical trade-offs", "Stakeholder alignment"],
  },
  status: "Curated",
  source_metadata: { salary_figures_included: false, future_proof_claim: false },
  last_reviewed_date: "2026-07-24",
  version: "career-role-profile-v1",
  updated_at: "2026-07-24T09:00:00Z",
}));

function comparison() {
  return {
    profile_id: profileId,
    career_slug: "ai-product-designer",
    career_title: "AI Product Designer",
    fit_dimensions: {
      "Personal Fit": { label: "Strong", reason: "Values and work-style evidence align." },
      "Capability Fit": { label: "Developing", reason: "Evidence exists with one technical gap." },
      "Market Fit": { label: "Observed", reason: "Linked to saved opportunities only." },
      "Support Fit": { label: "Potentially supported", reason: "Learning and experiment routes exist." },
    },
    evidence_passport_links: [{ id: "evidence-1", label: "Human Centred AI" }],
    recommended_experiments: ["Run a portfolio validation experiment."],
    learning_objectives: ["Strengthen evaluation evidence."],
    status: "ready",
  };
}

function journalEntry(status = "active") {
  return {
    id: "journal-1",
    profile_id: profileId,
    title: "Choose next evidence-building direction",
    decision_type: "career_direction",
    status,
    decision_summary: "Test AI Product Designer against RAG Application Developer using evidence and adviser feedback.",
    context: "Decision created from the Innovation Extension workbench.",
    selected_option: "AI Product Designer",
    options: [{ label: "AI Product Designer" }, { label: "RAG Application Developer" }],
    assumptions: [{ text: "Design evidence is stronger today.", state: "testing" }],
    uncertainty: { note: "Technical evidence still needs validation." },
    confidence: "medium",
    reversibility: "high",
    evidence_links: [{ type: "job_analysis", id: "analysis-1" }],
    source_attributions: [{ type: "job_analysis", id: "analysis-1" }],
    system_suggestions: [{ calculation: "Evidence strength remains deterministic." }],
    ai_explanations: [{ explanation: "Compare reversible evidence-building options." }],
    evidence_observations: [{ observation: "The practical evidence gap remains visible." }],
    adviser_inputs: [],
    user_reasoning: "Build evidence before choosing a direction.",
    adviser_comment_ids: [],
    career_slug: "ai-product-designer",
    job_analysis_id: null,
    application_id: null,
    privacy_scope: "private",
    review_date: "2026-08-15",
    outcome_status: status === "outcome_recorded" ? "recorded" : "",
    outcome: status === "outcome_recorded" ? { expected_outcome: "Clarify next gap.", actual_outcome: "Technical evidence gap remained." } : {},
    reconsideration_reason: "",
    roadmap_mutation_allowed: false,
    version_number: 1,
    reminder_status: "scheduled",
    versions: [{ id: "journal-version-1", version_number: 1, snapshot: { title: "Choose next evidence-building direction" }, change_reason: "initial", created_at: "2026-07-24T09:00:00Z" }],
    created_at: "2026-07-24T09:00:00Z",
    updated_at: "2026-07-24T09:00:00Z",
  };
}

async function mockInnovationExtension(page: Page) {
  let connected = false;
  let captures: ReturnType<typeof capture>[] = [];
  let shares: ReturnType<typeof advisorShare>[] = [];
  let comments: ReturnType<typeof advisorComment>[] = [];
  let panelTurns: unknown[] = [];
  let journal: ReturnType<typeof journalEntry>[] = [];

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

    if (pathname === `/api/v1/profiles/${profileId}/browser-extension/settings`) {
      return route.fulfill({
        json: {
          profile_id: profileId,
          feature_name: "Save to OrganicAI Compass",
          connections: connected ? [connection()] : [],
          connected,
          installation_instructions: ["Load browser-extension/dist in Chrome or Edge developer mode."],
          privacy_explanation: "Capture is user-triggered and excludes browser history, cookies, passwords, form contents and raw DOM snapshots.",
          privacy: { user_triggered_only: true, automatic_background_scraping: false, raw_html_storage: false, permissions: ["activeTab", "storage", "scripting"] },
        },
      });
    }
    if (pathname === `/api/v1/profiles/${profileId}/browser-extension/connection` && method === "POST") {
      connected = true;
      return route.fulfill({ json: connection(true) });
    }
    if (pathname === `/api/v1/profiles/${profileId}/job-captures`) {
      if (method === "POST") {
        captures = [capture("Needs review")];
        return route.fulfill({ json: captures[0] });
      }
      return route.fulfill({ json: captures });
    }
    if (pathname === `/api/v1/profiles/${profileId}/job-captures/capture-1/confirm`) {
      captures = [capture("Analysed")];
      return route.fulfill({ json: captures[0] });
    }

    if (pathname === `/api/v1/profiles/${profileId}/advisor-shares`) {
      if (method === "POST") {
        shares = [advisorShare(comments, true)];
        return route.fulfill({ json: shares[0] });
      }
      return route.fulfill({ json: shares.map((share) => advisorShare(comments, false)) });
    }
    if (pathname === `/api/v1/profiles/${profileId}/advisor-comments/comment-1` || pathname === `/api/v1/profiles/${profileId}/advisor-comments/comment-2`) {
      const id = pathname.endsWith("comment-1") ? "comment-1" : "comment-2";
      const body = JSON.parse(route.request().postData() || "{}");
      comments = comments.map((comment) => comment.id === id ? { ...comment, status: body.status || comment.status, user_response: body.user_response || "" } : comment);
      return route.fulfill({ json: comments.find((comment) => comment.id === id) });
    }
    if (pathname === "/api/v1/advisor-review/bad-token") return route.fulfill({ status: 410, json: { detail: "Invalid or expired share token." } });
    if (pathname === "/api/v1/advisor-review/advisor_share_token") return route.fulfill({ json: advisorShare(comments, false) });
    if (pathname === "/api/v1/advisor-review/advisor_share_token/comments") {
      comments = [advisorComment("comment-1"), advisorComment("comment-2")];
      return route.fulfill({ json: comments[0] });
    }

    if (pathname === "/api/v1/panel-personas") return route.fulfill({ json: personas() });
    if (pathname === "/api/v1/interviews/interview-1/panel-simulation") {
      panelTurns = [];
      return route.fulfill({ json: panelSession(panelTurns) });
    }
    if (pathname === "/api/v1/mock-sessions/panel-session-1/panel-turns") {
      panelTurns = [{ id: "turn-1", persona_id: "recruiter", persona_label: "Recruiter" }];
      return route.fulfill({ json: panelTurns[0] });
    }
    if (pathname === "/api/v1/mock-sessions/panel-session-1/panel-complete") return route.fulfill({ json: panelSession(panelTurns) });

    if (pathname === `/api/v1/profiles/${profileId}/career-encyclopedia` || pathname === "/api/v1/careers") {
      const family = url.searchParams.get("family");
      return route.fulfill({ json: family ? roles.filter((role) => role.career_family === family) : roles });
    }
    if (pathname === `/api/v1/profiles/${profileId}/career-encyclopedia/ai-product-designer/compare`) return route.fulfill({ json: comparison() });
    if (pathname.endsWith("/hypothesis")) return route.fulfill({ json: { id: "hypothesis-1", status: "active" } });
    if (pathname.endsWith("/experiment")) return route.fulfill({ json: { id: "experiment-1", status: "planned", roadmap_confirmation_required: true } });

    if (pathname === `/api/v1/profiles/${profileId}/decision-journal`) {
      if (method === "POST") {
        journal = [journalEntry()];
        return route.fulfill({ json: journal[0] });
      }
      return route.fulfill({ json: journal });
    }
    if (pathname === `/api/v1/profiles/${profileId}/decision-journal/journal-1/outcome`) {
      journal = [journalEntry("outcome_recorded")];
      return route.fulfill({ json: journal[0] });
    }
    if (pathname === `/api/v1/profiles/${profileId}/decision-journal/research-export`) {
      return route.fulfill({ json: { profile_id: profileId, included_fields: ["status", "outcome_status", "assumption_count"], excluded_fields: ["raw_journal_text", "private_notes", "adviser_free_text"], entries: journal.map((entry) => ({ id: entry.id, version_number: entry.version_number })) } });
    }

    if (pathname === `/api/v1/profiles/${profileId}/job-analyses/analysis-1`) {
      return route.fulfill({ json: { id: "analysis-1", profile_id: profileId, title: "AI Product Designer", organisation: "Aurora Learning Lab", requirements: [], readiness: null, updated_at: "2026-07-24T09:00:00Z" } });
    }

    return route.fulfill({ json: [] });
  });
}

test("browser capture creates a token, saves a reviewed job, and enters Job Analyzer", async ({ page }) => {
  await mockInnovationExtension(page);
  await page.goto(`/workspace/${profileId}/integrations/browser-extension`);

  await expect(page.getByRole("heading", { name: "Save to OrganicAI Compass" })).toBeVisible();
  await expect(page.getByText(/Capture is user-triggered/)).toBeVisible();
  await page.keyboard.press("Tab");
  await page.getByRole("button", { name: /Connect extension/ }).click();
  await expect(page.getByText("ext_demo_token_visible_once")).toBeVisible();

  await page.getByRole("button", { name: /Submit demo capture/ }).click();
  await expect(page.getByText("Needs review")).toBeVisible();
  await expect(page.getByText(/review captured content/i)).toBeVisible();

  await page.getByRole("button", { name: /Confirm and analyse/ }).click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${profileId}/job-analyzer/analysis-1$`));
});

test("adviser share is limited, temporary, and user-controlled", async ({ page }) => {
  await mockInnovationExtension(page);
  await page.goto(`/workspace/${profileId}/advisor-collaboration`);

  await page.getByRole("button", { name: /Create temporary share/ }).click();
  await expect(page.getByText("advisor_share_token")).toBeVisible();

  await page.getByRole("link", { name: /Open adviser review/ }).click();
  await expect(page.getByText(/does not grant access to your full OrganicAI Compass account/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Selected Sections" })).toBeVisible();
  await page.getByRole("button", { name: /Submit review/ }).click();
  await expect(page.getByText(/user must accept it/i)).toBeVisible();

  await page.goto(`/workspace/${profileId}/advisor-collaboration`);
  await page.getByRole("button", { name: /Accept/ }).first().click();
  await expect(page.getByText(/Profile and Evidence Passport were not changed automatically/)).toBeVisible();
  await page.getByRole("button", { name: /Reject/ }).first().click();
  await expect(page.getByText(/Advisor suggestion rejected/)).toBeVisible();
});

test("invalid adviser token explains the access failure", async ({ page }) => {
  await mockInnovationExtension(page);
  await page.goto("/advisor-review/bad-token");
  await expect(page.getByText(/invalid, expired, revoked, or has reached its access limit/i)).toBeVisible();
});

test("panel simulation uses personas, confirmed requirements, and no opaque score", async ({ page }) => {
  await mockInnovationExtension(page);
  await page.goto(`/workspace/${profileId}/interviews/interview-1/panel-simulation`);

  await expect(page.getByText("Recruiter")).toBeVisible();
  await expect(page.getByText("Hiring Manager")).toBeVisible();
  await expect(page.getByText("Technical Lead")).toBeVisible();
  await page.getByRole("button", { name: /Create panel/ }).click();
  await expect(page.getByText(/confirmed accessibility requirement/i)).toBeVisible();
  await page.getByRole("button", { name: /Answer one turn/ }).click();
  await expect(page.getByText(/Opaque score/i)).toBeVisible();
  await expect(page.getByText("absent")).toBeVisible();
  await expect(page.getByText(/personality|emotion|honesty|employability/i)).toHaveCount(0);
});

test("career encyclopedia exposes curated roles and evidence-aware actions", async ({ page }) => {
  await mockInnovationExtension(page);
  await page.goto(`/workspace/${profileId}/career-encyclopedia`);

  await expect(page.getByText("AI Product Designer").first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Learning Experience Designer/ })).toBeVisible();
  await page.getByLabel("Career family").selectOption("Design and product");
  await expect(page.getByRole("link", { name: /Service Designer/ })).toBeVisible();
  await page.getByRole("link", { name: /AI Product Designer/ }).click();
  await page.getByRole("button", { name: /Compare/ }).click();
  await expect(page.getByText("Personal Fit")).toBeVisible();
  await expect(page.getByText("Capability Fit")).toBeVisible();
  await expect(page.getByText("Market Fit")).toBeVisible();
  await expect(page.getByText("Support Fit")).toBeVisible();
  await page.getByRole("button", { name: /Test career/ }).click();
  await expect(page.getByText(/Roadmap insertion still requires separate confirmation/)).toBeVisible();
});

test("decision journal records outcomes without mutating the roadmap", async ({ page }) => {
  await mockInnovationExtension(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/workspace/${profileId}/decision-journal`);

  await page.getByRole("button", { name: /Create decision/ }).click();
  await expect(page.getByText("Choose next evidence-building direction")).toBeVisible();
  await expect(page.getByText(/v1 - review 2026-08-15 - roadmap mutation blocked/)).toBeVisible();
  await page.getByRole("button", { name: /Record outcome/ }).click();
  await expect(page.getByText(/My Roadmap was not changed automatically/)).toBeVisible();
  await expect(page.getByText(/raw_journal_text/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
});
