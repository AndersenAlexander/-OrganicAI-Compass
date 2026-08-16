import { expect, test, type Page } from "@playwright/test";

const profileId = "riasec-profile";
const user = { id: "user-riasec", email: "riasec@example.test", name: "Ria Sec", is_demo: false };

const careerInterests = {
  model: "RIASEC-inspired Career Interests",
  rule_set_version: "riasec-career-interests-v1",
  status: "complete",
  top_pattern: "A-I-S",
  top_dimensions: ["artistic", "investigative", "social"],
  close_score_notice: "Several interest dimensions are closely balanced.",
  limitations: ["Interest is not capability or evidence."],
  dimensions: {
    realistic: { code: "R", label: "Realistic", description: "Interest in practical hands-on activity.", score: 50, band: "Moderate", direct_items: 1 },
    investigative: { code: "I", label: "Investigative", description: "Interest in analysis and research.", score: 100, band: "High", direct_items: 1 },
    artistic: { code: "A", label: "Artistic", description: "Interest in design and original concepts.", score: 100, band: "High", direct_items: 1 },
    social: { code: "S", label: "Social", description: "Interest in helping and teaching.", score: 75, band: "High", direct_items: 1 },
    enterprising: { code: "E", label: "Enterprising", description: "Interest in initiating projects.", score: 50, band: "Moderate", direct_items: 1 },
    conventional: { code: "C", label: "Conventional", description: "Interest in structured processes.", score: 25, band: "Lower", direct_items: 1 },
  },
};

async function mockApp(page: Page) {
  let submittedDiagnostic: Record<string, unknown> | null = null;
  await page.addInitScript(() => {
    localStorage.removeItem("organicai_diagnostic_draft");
    localStorage.removeItem("organicai_active_profile_id");
  });
  await page.route("**/api/auth/refresh", (route) => route.fulfill({ json: { access_token: "riasec-token" } }));
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: user }));
  await page.route("**/api/privacy/preferences", (route) =>
    route.fulfill({
      json: {
        conversationPersistenceMode: "ephemeral",
        voiceTranscriptPersistenceMode: "ephemeral",
        productAnalyticsEnabled: false,
        researchParticipationEnabled: false,
        personalizationEnabled: true,
        serviceEmailEnabled: true,
        marketingEmailEnabled: false,
      },
    }),
  );
  await page.route("**/api/profiles", (route) => route.fulfill({ json: [{ id: profileId, created_at: "2026-01-01T00:00:00Z", data: {} }] }));
  await page.route("**/api/diagnostics", async (route) => {
    if (route.request().method() === "POST") {
      submittedDiagnostic = route.request().postDataJSON();
      return route.fulfill({ json: { diagnostic_id: "diagnostic-riasec", profile_id: profileId } });
    }
    return route.fulfill({ json: [] });
  });
  await page.route(`**/api/profiles/${profileId}`, (route) =>
    route.fulfill({
      json: {
        id: profileId,
        diagnostic_id: "diagnostic-riasec",
        natural_discovery_snapshot: { career_interests: careerInterests },
        primary_archetype: { name: "Curious Designer", summary: "Your answers suggest exploratory design interests.", confidence: 0.82, signals: ["Design", "Research"] },
        secondary_archetype: { name: "Reflective Explorer", summary: "You test ideas carefully.", confidence: 0.7, signals: ["Learning"] },
        strengths: [{ name: "Creative Problem Solving", score: 84, explanation: "Generated alternatives.", evidence: ["Design"] }],
        values: [{ name: "Creativity", score: 88, evidence: ["Selected value"] }],
        fears: [],
        creative_tendencies: ["Design experiments"],
        ai_collaboration_style: { name: "Co-Creator", summary: "Use AI to compare alternatives.", strengths: ["Ideation"], cautions: ["Verify"], recommended_uses: ["Prototype"], human_led_decisions: ["Final decisions"] },
        contribution_domains: [{ name: "Responsible Design", score: 82, explanation: "Potential contribution area." }],
        recommended_learning_paths: [],
        uncertainties: [],
        risk_notes: [],
        ethical_note: "This is exploratory and user-confirmable.",
        created_at: "2026-01-01T00:00:00Z",
      },
    }),
  );
  await page.route(`**/api/profiles/${profileId}/feedback`, (route) =>
    route.fulfill({ json: { confirmed_nodes: [], hidden_recommendations: [], strength_adjustments: {}, archetype_override: null, user_notes: {} } }),
  );
  await page.route(`**/api/v1/profiles/${profileId}/assessment-results`, (route) =>
    route.fulfill({
      json: {
        status: "completed",
        disclaimer: "Decision support, not a diagnosis.",
        assessment_version: "career-assessment-v1",
        scoring_version: "career-scoring-v2-four-layer",
        session: { id: "session-riasec", profile_id: profileId, status: "completed" },
        scores: [],
        grouped_scores: {},
        summary: {},
        reflection_prompts: ["Which interest should you test with evidence?"],
      },
    }),
  );
  await page.route(`**/api/v1/profiles/${profileId}/career-matches**`, (route) =>
    route.fulfill({
      json: [
        {
          id: "match-ai-design",
          title: "Human-Centred AI Product Designer",
          category: "reskilling_opportunities",
          role_family: "Design and AI Product",
          description: "Prototype role.",
          alignment_score: 72,
          alignment_label: "Moderate alignment",
          explanation: "Your current interests show strong Artistic and Investigative signals, which contribute to Natural Fit for this hypothesis.",
          supporting_factors: ["Strong Artistic and Investigative interest signals."],
          conflicting_factors: ["Evidence remains limited."],
          missing_skills: ["AI evaluation"],
          transferable_skills: [],
          ai_opportunities: [],
          next_step: "Run a small product-design experiment.",
          transition_difficulty: "moderate",
          time_horizon: "3-6 months",
          assumptions: [],
          limitations: ["This remains a hypothesis."],
          factors: [],
          dimension_scores: { natural_fit: 78, capability_fit: 42, evidence_strength: 30, transition_feasibility: 62 },
          dimension_labels: { natural_fit: "Strong", capability_fit: "Developing", evidence_strength: "Limited", transition_feasibility: "Moderate" },
          dimension_explanations: { natural_fit: "Uses interests, values, and work style only.", evidence_strength: "Evidence remains separate from interest." },
          status: "suggested",
          user_priority: null,
        },
      ],
    }),
  );
  await page.route(`**/api/v1/profiles/${profileId}/assessment-sessions/current`, (route) =>
    route.fulfill({
      json: {
        session: null,
        disclaimer: "Decision support, not a diagnosis.",
        prefill: { responses: { interest_artistic_design: 5 }, notes: { interest_artistic_design: "Confirm or edit." }, source: "natural_discovery_profile" },
        definition: {
          id: "human-potential-career-assessment",
          title: "Human Potential & Career Assessment",
          version: "career-assessment-v1",
          scoring_version: "career-scoring-v2-four-layer",
          disclaimer: "Decision support, not a diagnosis.",
          methodology_note: "",
          modes: [{ id: "quick", title: "Quick Assessment", estimated_minutes: "8-10", description: "Focused assessment." }],
          modules: [],
          items: [],
        },
      },
    }),
  );
  return () => submittedDiagnostic;
}

test("Natural Discovery creates a RIASEC-inspired interest profile before capability and evidence", async ({ page }) => {
  const submitted = await mockApp(page);
  await page.goto("/diagnostic");

  await page.getByRole("button", { name: "Design" }).click();
  await page.getByRole("button", { name: "Science" }).click();
  await page.getByLabel("Which activities make you lose track of time? *").fill("Designing explainable interfaces");
  await page.getByRole("button", { name: "Visual creation" }).click();
  await page.getByRole("group", { name: "Realistic career interest appeal" }).getByRole("button", { name: "Moderately" }).click();
  await page.getByRole("group", { name: "Investigative career interest appeal" }).getByRole("button", { name: "Extremely" }).click();
  await page.getByRole("group", { name: "Artistic career interest appeal" }).getByRole("button", { name: "Extremely" }).click();
  await page.getByRole("group", { name: "Social career interest appeal" }).getByRole("button", { name: "Very" }).click();
  await page.getByRole("group", { name: "Enterprising career interest appeal" }).getByRole("button", { name: "Moderately" }).click();
  await page.getByRole("group", { name: "Conventional career interest appeal" }).getByRole("button", { name: "Slightly" }).click();
  await page.getByRole("button", { name: "Continue" }).click();

  await page.getByLabel("What concerns you most about AI? *").fill("Losing human judgement");
  await page.getByLabel("What feels unclear about your future? *").fill("How to combine design and AI responsibly");
  await page.getByRole("button", { name: "Both" }).click();
  await page.getByRole("button", { name: "Continue" }).click();

  await page.getByRole("button", { name: "Creativity" }).click();
  await page.getByRole("button", { name: "Learning" }).click();
  await page.getByLabel("What kind of future would you like to help create? *").fill("A future where AI tools explain limits clearly.");
  await page.getByLabel("How would you contribute if time, money, and confidence were not barriers? *").fill("Design transparent AI learning products.");
  await page.getByRole("button", { name: "Continue" }).click();

  await page.getByRole("button", { name: "Research" }).click();
  await page.getByRole("button", { name: "Hands-on practice" }).click();
  await page.getByRole("button", { name: "Visual", exact: true }).click();
  await page.getByRole("button", { name: "Continue" }).click();

  await page.getByRole("button", { name: "Intermediate" }).click();
  await page.getByRole("button", { name: "Research" }).click();
  await page.getByRole("button", { name: "Create" }).click();
  await page.getByRole("button", { name: "Generate My Human Potential Map" }).click();

  await expect(page).toHaveURL(/\/profile\/riasec-profile$/);
  await expect(page.getByRole("heading", { name: "RIASEC-inspired Career Interests" })).toBeVisible();
  await expect(page.getByText("Current interest pattern:")).toBeVisible();
  await expect(page.getByText("A-I-S")).toBeVisible();
  await expect(page.getByText("Interest is kept separate from capability")).toBeVisible();
  expect(submitted()?.career_interests).toMatchObject({ artistic: 5, investigative: 5, conventional: 2 });

  await page.getByRole("button", { name: "Career Interests" }).click();
  await expect(page.getByText("Artistic (A)")).toBeVisible();

  await page.goto(`/workspace/${profileId}/assessment`);
  await expect(page.getByRole("heading", { name: "Choose an assessment path." })).toBeVisible();

  await page.goto(`/workspace/${profileId}/career-compatibility`);
  await expect(page.getByRole("heading", { name: "Explore career directions before committing." })).toBeVisible();
  await expect(page.getByText("Natural Fit").first()).toBeVisible();
  await expect(page.getByText("Evidence Strength").first()).toBeVisible();
  await page.getByText("Why it may fit, and what conflicts").click();
  await expect(page.getByText("Strong Artistic and Investigative interest signals.")).toBeVisible();
});
