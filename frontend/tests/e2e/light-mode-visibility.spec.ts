import { expect, test, type Locator, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { contrastRatio, luminance, sampleContrast } from "./utils/contrast";

mkdirSync("qa", { recursive: true });

const activeProfileId = "demo-profile";
const desktop = { width: 1448, height: 1086 };
const compactDesktop = { width: 1366, height: 768 };
const tabletLandscape = { width: 1024, height: 768 };
const tabletPortrait = { width: 768, height: 1024 };
const mobile = { width: 390, height: 844 };

const publicRoutes = [
  { path: "/", label: "Home" },
  { path: "/about", label: "About" },
  { path: "/how-it-works", label: "How It Works" },
  { path: "/principles", label: "Principles" },
  { path: "/research", label: "Research" },
  { path: "/project-roadmap", label: "Project Roadmap" },
  { path: "/blog", label: "Blog" },
];

const authRoutes = [
  { path: "/login", label: "Login" },
  { path: "/register", label: "Register" },
];

const workspaceRoutes = [
  { path: "/dashboard", label: "Dashboard" },
  { path: "/diagnostic", label: "Diagnostic" },
  { path: `/profile/${activeProfileId}`, label: "Profile" },
  { path: `/coach/${activeProfileId}`, label: "Coach" },
  { path: `/recommendations/${activeProfileId}`, label: "Recommendations" },
  { path: `/roadmap/${activeProfileId}`, label: "Roadmap" },
  { path: "/knowledge-base", label: "Knowledge Base" },
];

const additionalRoutes = [
  { path: "/blog/rag-source-visible-coaching", label: "Blog article", auth: "none" as const },
  { path: "/demo", label: "Demo", auth: "none" as const },
  { path: "/learning-paths", label: "Learning paths", auth: "user" as const },
  { path: "/future-scenarios", label: "Future scenarios", auth: "user" as const },
  { path: "/projects", label: "Projects", auth: "user" as const },
  { path: "/growth-timeline", label: "Growth timeline", auth: "user" as const },
  { path: "/community", label: "Community", auth: "user" as const },
  { path: "/co-creation-studio", label: "Co-creation studio", auth: "user" as const },
  { path: "/ai-constitution", label: "AI Constitution", auth: "user" as const },
  { path: `/report/${activeProfileId}`, label: "Report", auth: "user" as const },
  { path: `/fear-transformer/${activeProfileId}`, label: "Fear transformer", auth: "user" as const },
  { path: "/my-journey", label: "My Journey", auth: "user" as const },
];

const emptyFeedback = {
  confirmed_nodes: [],
  hidden_recommendations: [],
  strength_adjustments: {},
  archetype_override: null,
  user_notes: {},
};

const ragSource = {
  id: "source-1",
  source_id: "source-1",
  document_name: "Responsible_AI_Playbook",
  section_title: "Human agency",
  excerpt: "Responsible AI guidance should remain visible, contestable, and grounded in human judgment.",
  chunk_text: "Responsible AI guidance should remain visible, contestable, and grounded in human judgment.",
  similarity_score: 0.92,
  score: 0.92,
  rank: 1,
  relevance_status: "relevant",
};

function mockProfile() {
  return {
    id: activeProfileId,
    diagnostic_id: "demo-diagnostic",
    primary_archetype: {
      name: "Curious Explorer",
      summary: "You connect reflection with practical experimentation.",
      confidence: 0.82,
      signals: ["curiosity", "agency"],
    },
    secondary_archetype: {
      name: "Responsible Builder",
      summary: "You prefer transparent, human-led technology.",
      confidence: 0.74,
      signals: ["responsibility"],
    },
    strengths: [
      { name: "Systems Thinking", score: 86, explanation: "You notice connections.", evidence: ["Mapped trade-offs"] },
      { name: "Reflective Judgment", score: 82, explanation: "You pause before automating decisions.", evidence: ["Named boundaries"] },
    ],
    values: [
      { name: "Agency", score: 90, evidence: ["Human-led decisions"] },
      { name: "Transparency", score: 84, evidence: ["Source visibility"] },
    ],
    fears: ["Losing human control"],
    creative_tendencies: ["Prototype and reflect", "Translate abstract ideas into systems"],
    ai_collaboration_style: {
      name: "Co-Creator",
      summary: "Use AI for options while keeping final decisions human-led.",
      strengths: ["Ideation"],
      cautions: ["Verify important outputs"],
      recommended_uses: ["Planning", "Research synthesis"],
      human_led_decisions: ["Values", "Final decisions"],
    },
    contribution_domains: [
      { name: "Human-centred AI", score: 88, explanation: "Strong fit for research-informed AI workflows." },
      { name: "Education", score: 76, explanation: "Good fit for explanation and reflection." },
    ],
    recommended_learning_paths: [
      { name: "Responsible AI Practice", level: "Intermediate", duration: "Self-paced", reason: "Supports the profile." },
    ],
    uncertainties: [],
    risk_notes: ["This profile is exploratory."],
    ethical_note: "This is an exploratory profile, not a fixed label.",
    user_feedback: emptyFeedback,
    created_at: "2026-01-01T00:00:00Z",
  };
}

function mockRoadmapAction(overrides: Record<string, unknown> = {}) {
  return {
    id: "action-1",
    roadmap_id: "demo-roadmap",
    profile_id: activeProfileId,
    recommendation_id: "rec-1",
    horizon: "seven_days",
    title: "Run a transparent AI planning experiment",
    description: "Use one AI-supported planning session and record what remained human-led.",
    reason: "This matches your agency and transparency signals.",
    first_step: "Write the decision boundary before asking the AI.",
    success_criteria: "A short reflection with sources and next action.",
    estimated_minutes: 30,
    effort: "medium",
    impact: "high",
    priority: 1,
    status: "in_progress",
    progress_percentage: 40,
    due_date: null,
    scheduled_date: null,
    completed_at: null,
    skipped_at: null,
    skip_reason: null,
    user_notes: "",
    source_type: "recommendation",
    profile_signals: ["Agency", "Transparency"],
    rag_sources: [ragSource],
    ethical_cautions: ["Verify important claims before acting."],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function mockRoadmap() {
  const sevenDayAction = mockRoadmapAction();
  const thirtyDayAction = mockRoadmapAction({
    id: "action-2",
    horizon: "thirty_days",
    title: "Create a reusable AI collaboration checklist",
    status: "not_started",
    progress_percentage: 0,
  });
  return {
    id: "demo-roadmap",
    profile_id: activeProfileId,
    title: "Demo Roadmap",
    summary: "A compact test roadmap for responsible human-AI collaboration.",
    status: "active",
    version: 2,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
    last_recalibrated_at: "2026-01-02T00:00:00Z",
    progress: {
      total_actions: 2,
      completed_actions: 0,
      in_progress_actions: 1,
      skipped_actions: 0,
      blocked_actions: 0,
      completion_percentage: 40,
    },
    horizons: { seven_days: [sevenDayAction], thirty_days: [thirtyDayAction], six_months: [] },
    milestones: [],
    recalibration_notes: ["Keep experiments reversible."],
    ethical_cautions: ["Use important AI advice as a prompt for judgment, not as authority."],
    contribution_direction: "Human-centred AI contribution",
    seven_days: [sevenDayAction],
    thirty_days: [thirtyDayAction],
    six_months: [],
    recommended_skills: ["Prompt evaluation", "Source verification"],
    ai_workflows: ["Grounded planning"],
    project_idea: "Build a transparent AI reflection template.",
    social_contribution_idea: "Share a practical source-checking guide.",
  };
}

function mockRecommendation(overrides: Record<string, unknown> = {}) {
  return {
    id: "rec-1",
    profile_id: activeProfileId,
    category: "human_ai_workflows",
    title: "Use AI as a structured reflection partner",
    summary: "Ask for options, then decide with your own values and evidence.",
    reason: "Your profile emphasizes agency, transparency, and practical experimentation.",
    profile_signals: [{ signal: "Agency", source: "values", weight: 0.9 }],
    rag_sources: [
      {
        document: "Responsible_AI_Playbook",
        section: "Human agency",
        snippet: "Keep human judgment visible in consequential choices.",
        score: 0.91,
      },
    ],
    relevance_score: 0.88,
    confidence: 0.81,
    effort: "medium",
    impact: "high",
    time_horizon: "seven_days",
    estimated_duration: "30 minutes",
    prerequisites: ["Choose one real planning task"],
    first_action: "Write the boundary before using AI.",
    success_indicator: "You can explain what the AI influenced and what you decided.",
    ethical_cautions: ["Do not delegate values or sensitive decisions."],
    what_to_verify: ["Sources", "Assumptions", "Consequences"],
    status: "suggested",
    user_rating: null,
    user_feedback: null,
    score_components: { profile_fit: 0.9, evidence: 0.82 },
    retrieval_metadata: { used_chunks: 1 },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function recommendationGeneration() {
  return {
    profile_id: activeProfileId,
    generation_id: "generation-1",
    recommendations: [mockRecommendation()],
    generated_at: "2026-01-01T00:00:00Z",
    context_summary: {
      profile_signals_used: ["Agency", "Transparency"],
      feedback_applied: true,
      rag_used: true,
    },
    metadata: { strategy: "light-mode-qa" },
  };
}

async function preparePage(page: Page, options: { auth?: "none" | "user" | "demo"; theme?: "light" | "dark" } = {}) {
  const auth = options.auth ?? "user";
  const theme = options.theme ?? "light";
  const recommendation = mockRecommendation();
  const roadmap = mockRoadmap();

  await page.addInitScript(
    ({ auth, profileId, theme }) => {
      localStorage.setItem("organicai_active_profile_id", profileId);
      localStorage.setItem("organicai-theme", theme);
      localStorage.removeItem("organicai_coach_temp_history");
      if (auth === "none") localStorage.removeItem("organicai.auth.token");
      else localStorage.setItem("organicai.auth.token", `${auth}-token`);
    },
    { auth, profileId: activeProfileId, theme }
  );

  await page.route((url) => new URL(url).pathname.startsWith("/api/"), async (route) => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;

    if (pathname.endsWith("/auth/me")) {
      if (auth === "none") {
        await route.fulfill({ status: 401, json: { detail: "Not authenticated" } });
        return;
      }
      await route.fulfill({
        status: 200,
        json: {
          id: `${auth}-user`,
          email: `${auth}@example.test`,
          name: auth === "demo" ? "Demo User" : "Alex User",
          is_demo: auth === "demo",
        },
      });
      return;
    }

    if (pathname === "/api/auth/login" || pathname === "/api/auth/register") {
      await route.fulfill({
        status: 200,
        json: {
          access_token: "user-token",
          token_type: "bearer",
          user: { id: "user-1", email: "alex@example.test", name: "Alex User", is_demo: false },
        },
      });
      return;
    }

    if (pathname === "/api/demo/login") {
      await route.fulfill({
        status: 200,
        json: {
          access_token: "demo-token",
          active_profile_id: activeProfileId,
          user: { id: "demo-user", email: "demo@example.test", name: "Demo User", is_demo: true },
        },
      });
      return;
    }

    if (pathname === "/api/diagnostics") {
      await route.fulfill({ status: 200, json: [{ id: "demo-diagnostic", created_at: "2026-01-01T00:00:00Z", payload: {} }] });
      return;
    }

    if (pathname === "/api/profiles") {
      await route.fulfill({ status: 200, json: [{ id: activeProfileId, created_at: "2026-01-01T00:00:00Z", data: mockProfile() }] });
      return;
    }

    if (pathname === `/api/profiles/${activeProfileId}`) {
      await route.fulfill({ status: 200, json: mockProfile() });
      return;
    }

    if (pathname === `/api/profiles/${activeProfileId}/feedback`) {
      await route.fulfill({ status: 200, json: emptyFeedback });
      return;
    }

    if (pathname === "/api/report/demo-profile") {
      await route.fulfill({
        status: 200,
        json: { profile: mockProfile(), fear_transforms: [], roadmap },
      });
      return;
    }

    if (pathname === "/api/fear-transform") {
      await route.fulfill({
        status: 200,
        json: {
          validation: "This concern is understandable.",
          what_is_real: "AI can shift workflows.",
          what_is_uncertain: "The exact impact depends on context.",
          what_you_can_control: "You can set boundaries and verify outputs.",
          creative_reframe: "Use AI as a tool for experiments.",
          human_ai_collaboration_opportunity: "Design a small task with explicit human review.",
          fifteen_minute_action: "Write one boundary.",
          seven_day_action: "Run one reversible experiment.",
          ethical_note: "Human agency remains central.",
        },
      });
      return;
    }

    if (pathname === "/api/roadmap") {
      await route.fulfill({ status: 200, json: [{ id: "demo-roadmap", created_at: "2026-01-01T00:00:00Z", data: roadmap }] });
      return;
    }

    if (pathname === `/api/roadmap/${activeProfileId}` || pathname === "/api/roadmap/generate" || pathname === "/api/roadmaps/demo-roadmap") {
      await route.fulfill({ status: 200, json: roadmap });
      return;
    }

    if (pathname === "/api/roadmaps/demo-roadmap/actions") {
      await route.fulfill({ status: 200, json: Object.values(roadmap.horizons).flat() });
      return;
    }

    if (pathname === "/api/roadmaps/demo-roadmap/check-ins") {
      await route.fulfill({
        status: 200,
        json: [
          {
            id: "check-in-1",
            roadmap_id: "demo-roadmap",
            check_in_type: "weekly",
            energy_level: 4,
            confidence_level: 4,
            perceived_progress: 3,
            main_blocker: "",
            what_worked: "Clear boundaries helped.",
            what_changed: "More source checking.",
            user_note: "",
            created_at: "2026-01-03T00:00:00Z",
          },
        ],
      });
      return;
    }

    if (pathname === "/api/roadmaps/demo-roadmap/versions") {
      await route.fulfill({ status: 200, json: [{ version_number: 2, reason: "QA sample", created_at: "2026-01-02T00:00:00Z" }] });
      return;
    }

    if (pathname === "/api/roadmaps/demo-roadmap/recalibrate") {
      await route.fulfill({
        status: 200,
        json: {
          roadmap_id: "demo-roadmap",
          current_version: 2,
          proposed_version: 3,
          summary: "Keep one action and clarify human review.",
          changes: [{ type: "update", action_id: "action-1", patch: { priority: 1 }, reason: "Improve clarity." }],
          rules_triggered: ["stale_action"],
          ethical_note: "Keep the decision reversible.",
          confidence_note: "Moderate confidence.",
        },
      });
      return;
    }

    if (pathname === "/api/roadmaps/demo-roadmap/apply-recalibration") {
      await route.fulfill({ status: 200, json: roadmap });
      return;
    }

    if (pathname.startsWith("/api/roadmap-actions/")) {
      await route.fulfill({ status: 200, json: mockRoadmapAction() });
      return;
    }

    if (pathname === `/api/recommendations/profile/${activeProfileId}`) {
      await route.fulfill({ status: 200, json: [recommendation] });
      return;
    }

    if (pathname === "/api/recommendations/generate") {
      await route.fulfill({ status: 200, json: recommendationGeneration() });
      return;
    }

    if (pathname.startsWith("/api/recommendations/")) {
      await route.fulfill({ status: 200, json: recommendation });
      return;
    }

    if (pathname === "/api/rag/search") {
      await route.fulfill({
        status: 200,
        json: {
          query: url.searchParams.get("query") ?? "",
          results: [
            {
              id: ragSource.id,
              document_name: ragSource.document_name,
              section_title: ragSource.section_title,
              chunk_text: ragSource.chunk_text,
              score: ragSource.score,
            },
          ],
        },
      });
      return;
    }

    if (pathname === "/api/rag/ask") {
      await route.fulfill({
        status: 200,
        json: {
          query: "How should I use AI responsibly?",
          answer: "Use AI as a reflective partner, keep sources visible, and reserve consequential decisions for human judgment.",
          rag_run_id: "run-1",
          sources: [ragSource],
          sources_used: [ragSource],
          has_sources: true,
          confidence_note: "Confidence is strong because the answer uses curated Responsible AI source material.",
          ethical_note: "Do not share sensitive personal or confidential information with the system.",
          insufficient_context: false,
          context_quality: "strong",
          retrieval_summary: { retrieved_count: 1, used_count: 1, highest_score: 0.92, threshold: 0.5, retrieval_duration_ms: 12 },
          suggested_actions: ["Write a decision boundary before using AI."],
        },
      });
      return;
    }

    if (pathname === "/api/rag/reindex") {
      await route.fulfill({ status: 200, json: { documents: 8, chunks: 24 } });
      return;
    }

    if (pathname.startsWith("/api/rag/runs/")) {
      await route.fulfill({ status: 200, json: { id: "feedback-1", rag_run_id: "run-1", saved: true, rating: "helpful" } });
      return;
    }

    if (pathname === "/api/chat") {
      await route.fulfill({
        status: 200,
        json: {
          answer: "Start with a small reversible action, inspect the source material, and keep your own values as the decision filter.",
          suggested_actions: ["Create a checklist"],
          confidence_note: "Confidence is moderate-high because this response combines profile signals with a retrieved source.",
          sources_used: [{ id: "source-1", document_name: "Responsible_AI_Playbook", section_title: "Human agency", score: 0.91 }],
          ethical_note: "Do not treat this as professional advice; verify important claims and consequences.",
          conversation_id: "conversation-1",
          message_id: "message-1",
          intent: "conversational_question",
          profile_signals_used: ["Agency", "Transparency"],
          grounding_status: "grounded",
          retrieval_status: { rag_run_id: "run-1", context_quality: "strong" },
          timing: { retrieval_ms: 12, generation_ms: 34 },
          rag_run_id: "run-1",
          context_quality: "strong",
        },
      });
      return;
    }

    await route.fulfill({ status: 200, json: [] });
  });
}

function channels(value: string): [number, number, number] {
  const trimmed = value.trim();
  if (trimmed.startsWith("#")) {
    const hex = trimmed.slice(1);
    if (hex.length === 3) {
      return hex.split("").map((part) => Number.parseInt(`${part}${part}`, 16)) as [number, number, number];
    }
    return [Number.parseInt(hex.slice(0, 2), 16), Number.parseInt(hex.slice(2, 4), 16), Number.parseInt(hex.slice(4, 6), 16)];
  }
  const parsed = trimmed.match(/[\d.]+/g)?.slice(0, 3).map(Number);
  if (trimmed.startsWith("color(srgb") && parsed && parsed.length >= 3) {
    return [parsed[0] * 255, parsed[1] * 255, parsed[2] * 255];
  }
  return (parsed && parsed.length >= 3 ? parsed : [255, 255, 255]) as [number, number, number];
}

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate((nextTheme) => {
    localStorage.setItem("organicai-theme", nextTheme);
    document.documentElement.dataset.theme = nextTheme;
    document.documentElement.style.colorScheme = nextTheme;
  }, theme);
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

async function expectLightPageBackground(page: Page) {
  const color = await page.evaluate(() => getComputedStyle(document.documentElement).backgroundColor);
  expect(luminance(channels(color)), `page background ${color} should remain light`).toBeGreaterThan(0.72);
}

async function expectLightModeDarkText(locator: Locator, label: string) {
  await expect(locator.first()).toBeVisible();
  const color = await locator.first().evaluate((element) => getComputedStyle(element).color);
  expect(luminance(channels(color)), `${label} should not use white Light Mode text: ${color}`).toBeLessThan(0.25);
}

async function expectLightModeSurface(locator: Locator, label: string) {
  await expect(locator.first()).toBeVisible();
  const colors = await locator.first().evaluate((element) => {
    const isVisibleSurfaceColor = (value: string) => {
      const channels = value.match(/[\d.]+/g)?.map(Number);
      if (!channels || channels.length < 3) return false;
      return (channels[3] ?? 1) > 0.5;
    };
    const computed = getComputedStyle(element);
    return [computed.backgroundColor, computed.backgroundImage].flatMap((value) =>
      (value.match(/rgba?\([^)]+\)|color\(srgb [^)]+\)/g) ?? []).filter(isVisibleSurfaceColor)
    );
  });
  expect(colors.length, `${label} should expose a measurable Light Mode surface`).toBeGreaterThan(0);
  const darkestSurface = Math.min(...colors.map((color) => luminance(channels(color))));
  expect(darkestSurface, `${label} should use a light readable surface`).toBeGreaterThan(0.72);
}

async function expectReadable(locator: Locator, minimum = 4.5) {
  await expect(locator.first()).toBeVisible();
  const sample = await sampleContrast(locator);
  const textColor = channels(sample.color);
  const inverseSurface = await locator.first().evaluate((element) =>
    Boolean(
      element.closest(
        [
          "header.no-print",
          "[data-app-header-shell]",
          "#global-workspace-dropdown",
          "#global-mobile-navigation",
          ".surface-inverse",
          ".organic-card-dark",
          ".dark-glass-card",
          ".home-hero",
          ".home-manifesto",
          ".about-hero",
          ".about-manifesto",
          ".project-roadmap-hero",
          ".blog-hero-visual",
          ".blog-article-visual",
          ".research-hero-visual",
          ".project-roadmap-hero-visual",
        ].join(",")
      )
    )
  );

  if (inverseSurface && sample.ratio < minimum) {
    expect(Math.min(...textColor), `${sample.text || "inverse element"} should use light inverse text`).toBeGreaterThan(170);
    return sample;
  }

  expect(sample.ratio, `${sample.text || "element"} contrast ${sample.color} on ${sample.backgroundColor}`).toBeGreaterThanOrEqual(minimum);
  return sample;
}

async function firstVisibleLocator(page: Page, selector: string, options: { minText?: number; excludeInverse?: boolean } = {}) {
  const index = await page.locator(selector).evaluateAll(
    (nodes, opts) => {
      const excluded = [
        "[aria-hidden='true']",
        "header.no-print",
        "[data-app-header-shell]",
        ".surface-inverse",
        ".organic-card-dark",
        ".dark-glass-card",
        ".home-hero",
        ".home-manifesto",
        ".about-hero-scene",
        ".project-roadmap-hero-visual",
        ".blog-hero-visual",
        ".blog-article-visual",
      ].join(",");
      return nodes.findIndex((node) => {
        const element = node as HTMLElement;
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        if (rect.width < 2 || rect.height < 2 || style.display === "none" || style.visibility === "hidden") return false;
        if (opts.excludeInverse && element.closest(excluded)) return false;
        return (element.textContent ?? "").replace(/\s+/g, " ").trim().length >= (opts.minText ?? 2);
      });
    },
    { minText: options.minText ?? 2, excludeInverse: options.excludeInverse ?? true }
  );
  expect(index, `visible selector not found: ${selector}`).toBeGreaterThanOrEqual(0);
  return page.locator(selector).nth(index);
}

async function expectCardBoundaryVisible(card: Locator) {
  await expect(card.first()).toBeVisible();
  const style = await card.first().evaluate((element) => {
    const computed = getComputedStyle(element);
    return {
      backgroundColor: computed.backgroundColor,
      borderTopColor: computed.borderTopColor,
      borderTopWidth: computed.borderTopWidth,
      boxShadow: computed.boxShadow,
    };
  });
  expect(
    Number.parseFloat(style.borderTopWidth) > 0 || style.boxShadow !== "none",
    `card boundary should be visible; border=${style.borderTopWidth} ${style.borderTopColor}, shadow=${style.boxShadow}`
  ).toBeTruthy();
}

async function expectNoWhiteTextOnLightSurface(page: Page) {
  const issues = await page.evaluate(() => {
    type Rgba = [number, number, number, number];
    const parseColor = (value: string): Rgba | null => {
      const parsed = value.match(/[\d.]+/g)?.map(Number);
      if (!parsed || parsed.length < 3) return null;
      if (value.trim().startsWith("color(srgb")) return [parsed[0] * 255, parsed[1] * 255, parsed[2] * 255, parsed[3] ?? 1];
      return [parsed[0], parsed[1], parsed[2], parsed[3] ?? 1];
    };
    const blend = (top: Rgba, bottom: Rgba): Rgba => {
      const alpha = top[3] + bottom[3] * (1 - top[3]);
      if (alpha === 0) return [255, 255, 255, 1];
      return [
        (top[0] * top[3] + bottom[0] * bottom[3] * (1 - top[3])) / alpha,
        (top[1] * top[3] + bottom[1] * bottom[3] * (1 - top[3])) / alpha,
        (top[2] * top[3] + bottom[2] * bottom[3] * (1 - top[3])) / alpha,
        alpha,
      ];
    };
    const luminance = ([red, green, blue]: Rgba) => {
      const linear = [red, green, blue].map((channel) => {
        const normalized = channel / 255;
        return normalized <= 0.03928 ? normalized / 12.92 : Math.pow((normalized + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
    };
    const effectiveBackground = (element: Element) => {
      let background: Rgba = [255, 255, 255, 1];
      let current: Element | null = element;
      while (current) {
        const parsed = parseColor(getComputedStyle(current).backgroundColor);
        if (parsed && parsed[3] > 0) background = blend(parsed, background);
        if (parsed && parsed[3] >= 0.98) break;
        current = current.parentElement;
      }
      return background;
    };
    const skipSelector = [
      "[aria-hidden='true']",
      "svg",
      "header.no-print",
      "[data-app-header-shell]",
      "#global-workspace-dropdown",
      "#global-mobile-navigation",
      ".surface-inverse",
      ".organic-card-dark",
      ".dark-glass-card",
      ".home-hero",
      ".home-manifesto",
      ".home-story-media",
      ".about-hero-scene",
      ".about-manifesto",
      ".about-fear-image",
      ".project-roadmap-hero-visual",
      ".blog-hero-visual",
      ".blog-article-visual",
      ".organic-button",
      ".home-button",
      ".about-button",
      ".blog-button",
      ".project-roadmap-button",
    ].join(",");

    return Array.from(document.querySelectorAll("main *"))
      .map((element) => {
        const html = element as HTMLElement;
        const text = (html.innerText || html.textContent || "").replace(/\s+/g, " ").trim();
        if (text.length < 2 || html.closest(skipSelector)) return null;
        const rect = html.getBoundingClientRect();
        const style = getComputedStyle(html);
        if (rect.width < 2 || rect.height < 2 || style.visibility === "hidden" || style.display === "none") return null;
        if (style.backgroundImage && style.backgroundImage !== "none") return null;
        const foreground = parseColor(style.color);
        if (!foreground) return null;
        const background = effectiveBackground(html);
        const foregroundNearWhite = foreground[0] > 235 && foreground[1] > 235 && foreground[2] > 235;
        const backgroundLight = luminance(background) > 0.78;
        if (!foregroundNearWhite || !backgroundLight) return null;
        return {
          text: text.slice(0, 80),
          selector: html.className ? `.${String(html.className).split(/\s+/).slice(0, 3).join(".")}` : html.tagName.toLowerCase(),
          color: style.color,
          background: `rgba(${background.map((part) => Math.round(part)).join(", ")})`,
        };
      })
      .filter(Boolean)
      .slice(0, 5);
  });
  expect(issues, `near-white text on light surfaces: ${JSON.stringify(issues, null, 2)}`).toEqual([]);
}

async function assertRouteReadable(page: Page, path: string, options: { checkCards?: boolean } = {}) {
  await page.goto(path);
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByTestId("global-header")).toBeVisible();
  await expectLightPageBackground(page);
  await expectNoHorizontalOverflow(page);
  await expectReadable(page.getByRole("heading", { level: 1 }).first(), 3);
  await expectReadable(await firstVisibleLocator(page, "main p, main li, main span, main small, main div", { minText: 8 }), 4.5);
  const secondarySelector = "main .theme-muted, main small, main .text-slate-600, main .text-slate-500";
  if (await page.locator(secondarySelector).count()) {
    const secondary = await firstVisibleLocator(page, secondarySelector, { minText: 4 });
    await expectReadable(secondary, 4.5);
  }
  if (options.checkCards !== false) {
    const card = await firstVisibleLocator(
      page,
      [
        "main .glass-card",
        "main .organic-section",
        "main .oa-panel",
        "main .home-value-strip article",
        "main .home-audience article",
        "main .home-prototype article",
        "main .about-problem-grid article",
        "main .about-module-grid article",
        "main .about-principles article",
        "main .about-audience-grid article",
        "main .journey-stage-card",
        "main .journey-navigator",
        "main .rag-card",
        "main .milestone-card",
        "main .blog-article-card",
        "main .blog-featured",
        "main .article-callout",
        "main .article-related > div > a",
        "main article:not(.organicai-article-page):not(.project-roadmap-milestone)",
      ].join(", "),
      { minText: 4 }
    );
    await expectCardBoundaryVisible(card);
    await expectReadable(card.locator("h2, h3, p, b, span").first(), 3);
  }
  const primaryAction = page
    .locator(
      "main .organic-button:not(:disabled), main .home-button:not(.secondary):not(:disabled), main .about-button:not(.secondary):not(:disabled), main .blog-button:not(.secondary):not(:disabled), main .research-button:not(.secondary):not(:disabled), main .project-roadmap-button:not(.secondary):not(:disabled), main button[type='submit']:not(:disabled)"
      + ", main .public-button:not(.secondary):not(:disabled), main .journey-action-link"
    )
    .first();
  if (await primaryAction.count()) await expectReadable(primaryAction, 4.5);
  const secondaryAction = page
    .locator(
      "main .organic-button-secondary:not(:disabled), main .home-button.secondary:not(:disabled), main .about-button.secondary:not(:disabled), main .blog-button.secondary:not(:disabled), main .research-button.secondary:not(:disabled), main .project-roadmap-button.secondary:not(:disabled)"
      + ", main .public-button.secondary:not(:disabled)"
    )
    .first();
  if (await secondaryAction.count()) await expectReadable(secondaryAction, 4.5);
  await expectNoWhiteTextOnLightSurface(page);
}

async function expectInputFocusVisible(input: Locator) {
  await input.focus();
  const focus = await input.evaluate((element) => {
    const computed = getComputedStyle(element);
    return {
      outlineStyle: computed.outlineStyle,
      outlineWidth: computed.outlineWidth,
      outlineColor: computed.outlineColor,
      boxShadow: computed.boxShadow,
    };
  });
  expect(
    Number.parseFloat(focus.outlineWidth) >= 2 || focus.boxShadow !== "none",
    `focus should be visible: ${JSON.stringify(focus)}`
  ).toBeTruthy();
}

test.describe("complete light mode visibility and contrast audit", () => {
  test("public and auth routes keep readable Light Mode surfaces", async ({ page }, testInfo) => {
    testInfo.setTimeout(180_000);
    await preparePage(page, { auth: "none", theme: "light" });
    await page.setViewportSize(desktop);

    for (const route of [...publicRoutes, ...authRoutes]) {
      await assertRouteReadable(page, route.path);
    }
  });

  test("How It Works Light Mode keeps journey surfaces and floating launcher readable", async ({ page }) => {
    await preparePage(page, { auth: "none", theme: "light" });
    await page.setViewportSize(desktop);
    await page.goto("/how-it-works");

    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await expectNoHorizontalOverflow(page);
    await expectLightModeSurface(page.locator(".how-hero"), "How It Works hero");
    await expectLightModeSurface(page.locator(".journey-dashboard"), "How It Works journey dashboard");
    await expectLightModeSurface(page.locator(".journey-stage-preview"), "How It Works active stage preview");
    await expectLightModeSurface(page.locator(".floating-voice-chat__launcher"), "How It Works floating launcher");
    await expectLightModeDarkText(page.locator(".how-hero-title"), "How It Works hero title");
    await expectLightModeDarkText(page.locator(".journey-preview-copy h3"), "How It Works stage title");
    await expectLightModeDarkText(page.locator(".journey-stage-card h3").first(), "How It Works stage card title");
    await expectLightModeDarkText(page.locator(".floating-voice-chat__launcher"), "How It Works floating launcher label");
    await expectReadable(page.locator(".journey-chat-bubble.answer"), 4.5);
    await expectReadable(page.locator(".journey-roadmap-mini strong").first(), 4.5);

    await page.setViewportSize(mobile);
    await page.goto("/how-it-works");
    await expectNoHorizontalOverflow(page);
    const launcherBox = await page.locator(".floating-voice-chat__launcher").first().boundingBox();
    expect(launcherBox).not.toBeNull();
    if (launcherBox) {
      expect(launcherBox.x).toBeGreaterThanOrEqual(0);
      expect(launcherBox.x + launcherBox.width).toBeLessThanOrEqual(mobile.width + 1);
    }
  });

  test("workspace routes keep readable Light Mode surfaces", async ({ page }, testInfo) => {
    testInfo.setTimeout(210_000);
    await preparePage(page, { auth: "user", theme: "light" });
    await page.setViewportSize(desktop);

    for (const route of workspaceRoutes) {
      await assertRouteReadable(page, route.path);
    }
  });

  test("additional routed pages smoke-test readable headings and body copy", async ({ page }, testInfo) => {
    testInfo.setTimeout(210_000);
    await preparePage(page, { auth: "user", theme: "light" });
    await page.setViewportSize(desktop);

    for (const route of additionalRoutes.filter((item) => item.auth === "user")) {
      await assertRouteReadable(page, route.path, { checkCards: false });
    }
  });

  test("additional public pages smoke-test readable headings and body copy", async ({ page }, testInfo) => {
    testInfo.setTimeout(120_000);
    await preparePage(page, { auth: "none", theme: "light" });
    await page.setViewportSize(desktop);

    for (const route of additionalRoutes.filter((item) => item.auth === "none")) {
      await assertRouteReadable(page, route.path, { checkCards: false });
    }
  });

  test("forms, placeholders, disabled controls, dropdowns, mobile menu, floating chat, and RAG feedback remain readable", async ({ page }, testInfo) => {
    testInfo.setTimeout(210_000);
    await preparePage(page, { auth: "user", theme: "light" });

    await page.setViewportSize(desktop);
    await page.goto("/knowledge-base");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    const askBox = page.getByPlaceholder("What would you like to understand?");
    await expectReadable(askBox, 4.5);
    const placeholderColor = await askBox.evaluate((element) => getComputedStyle(element, "::placeholder").color);
    const placeholderContrast = contrastRatio(channels(placeholderColor), [255, 255, 255]);
    expect(placeholderContrast, `placeholder ${placeholderColor} on white`).toBeGreaterThanOrEqual(4.5);
    await expectInputFocusVisible(askBox);

    const disabledAsk = page.getByRole("button", { name: "Ask Knowledge Base" });
    await expect(disabledAsk).toBeDisabled();
    const disabledStyle = await disabledAsk.evaluate((element) => {
      const computed = getComputedStyle(element);
      return { opacity: Number(computed.opacity), color: computed.color };
    });
    expect(disabledStyle.opacity, "disabled control should remain understandable").toBeGreaterThanOrEqual(0.5);
    expect(channels(disabledStyle.color).every(Number.isFinite)).toBeTruthy();

    await askBox.fill("How should I use AI responsibly?");
    await disabledAsk.click();
    await expect(page.locator(".kb-answer").getByText("Grounded guidance", { exact: true })).toBeVisible();
    await expectReadable(page.locator(".kb-answer").getByText("Grounded guidance"), 4.5);
    await expectReadable(page.locator(".rag-quality").first(), 4.5);
    await expectReadable(page.locator(".kb-answer small").first(), 4.5);
    await expectReadable(page.locator(".kb-answer small").nth(1), 4.5);
    await expectReadable(page.locator(".rag-feedback").first(), 4.5);
    await expectReadable(page.locator(".kb-results article").first().getByText("Responsible AI Playbook"), 4.5);

    await page.getByRole("button", { name: "Workspace" }).click();
    const dropdown = page.locator("#global-workspace-dropdown");
    await expect(dropdown).toBeVisible();
    await expectReadable(dropdown.getByRole("menuitem", { name: "AI Coach" }), 4.5);

    await page.setViewportSize(mobile);
    await page.goto("/");
    await expectNoHorizontalOverflow(page);
    await page.getByRole("button", { name: "Open navigation menu" }).click();
    const mobilePanel = page.locator("#global-mobile-navigation");
    await expect(mobilePanel).toBeVisible();
    await expectReadable(mobilePanel.getByRole("link", { name: "Research" }), 4.5);
    await expectReadable(mobilePanel.getByRole("link", { name: "AI Coach" }), 4.5);

    await page.setViewportSize(desktop);
    await page.goto("/");
    const launcher = page.locator(".floating-voice-chat__launcher");
    await expect(launcher).toBeVisible();
    const launcherSample = await expectReadable(launcher, 4.5);
    expect(Math.min(...channels(launcherSample.color)), `launcher text must not be white: ${launcherSample.color}`).toBeLessThan(190);
    expect(luminance(channels(launcherSample.backgroundColor)), `launcher background should be light: ${launcherSample.backgroundColor}`).toBeGreaterThan(0.82);
    await launcher.focus();
    await expectInputFocusVisible(launcher);
    await launcher.hover();
    await expectReadable(launcher, 4.5);
    await launcher.click();
    const expandedChat = page.locator('section[aria-label="OrganicAI Coach"]');
    await expect(expandedChat).toBeVisible();
    await expectReadable(expandedChat.getByRole("heading", { name: "OrganicAI Coach" }), 4.5);
    await expectReadable(expandedChat.getByPlaceholder("Ask or use a command"), 4.5);
  });

  test("mobile Light Mode has no horizontal overflow across required routes", async ({ page }, testInfo) => {
    testInfo.setTimeout(210_000);
    await preparePage(page, { auth: "user", theme: "light" });
    await page.setViewportSize(mobile);

    for (const route of [...publicRoutes, ...workspaceRoutes]) {
      await page.goto(route.path);
      await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
      await expectNoHorizontalOverflow(page);
      await expectReadable(page.getByRole("heading", { level: 1 }).first(), 3);
    }
  });

  test("Light Mode captures required desktop screenshots for public and auth routes", async ({ page }, testInfo) => {
    testInfo.setTimeout(210_000);
    await preparePage(page, { auth: "none", theme: "light" });

    const captures = [
      [desktop, "/", "qa/qa-light-home-1448.png"],
      [desktop, "/about", "qa/qa-light-about-1448.png"],
      [desktop, "/how-it-works", "qa/qa-light-how-it-works-1448.png"],
      [desktop, "/principles", "qa/qa-light-principles-1448.png"],
      [desktop, "/research", "qa/qa-light-research-1448.png"],
      [desktop, "/project-roadmap", "qa/qa-light-project-roadmap-1448.png"],
      [desktop, "/blog", "qa/qa-light-blog-1448.png"],
      [desktop, "/login", "qa/qa-light-login-1448.png"],
      [mobile, "/", "qa/qa-light-home-390.png"],
      [compactDesktop, "/", "qa/qa-light-home-1366.png"],
    ] as const;

    for (const [viewport, path, file] of captures) {
      await page.setViewportSize(viewport);
      await page.goto(path);
      await page.screenshot({ path: file, fullPage: true });
      await expectNoHorizontalOverflow(page);
    }
  });

  test("Light Mode captures required desktop and mobile screenshots for workspace routes", async ({ page }, testInfo) => {
    testInfo.setTimeout(240_000);
    await preparePage(page, { auth: "user", theme: "light" });

    const captures = [
      [desktop, "/dashboard", "qa/qa-light-dashboard-1448.png"],
      [desktop, "/diagnostic", "qa/qa-light-diagnostic-1448.png"],
      [desktop, `/profile/${activeProfileId}`, "qa/qa-light-profile-1448.png"],
      [desktop, `/coach/${activeProfileId}`, "qa/qa-light-coach-1448.png"],
      [desktop, `/recommendations/${activeProfileId}`, "qa/qa-light-recommendations-1448.png"],
      [desktop, `/roadmap/${activeProfileId}`, "qa/qa-light-roadmap-1448.png"],
      [desktop, "/knowledge-base", "qa/qa-light-knowledge-base-1448.png"],
      [mobile, "/dashboard", "qa/qa-light-dashboard-390.png"],
      [mobile, "/diagnostic", "qa/qa-light-diagnostic-390.png"],
      [mobile, `/coach/${activeProfileId}`, "qa/qa-light-coach-390.png"],
      [mobile, "/knowledge-base", "qa/qa-light-knowledge-base-390.png"],
      [tabletLandscape, "/dashboard", "qa/qa-light-dashboard-1024.png"],
      [tabletPortrait, "/knowledge-base", "qa/qa-light-knowledge-base-768.png"],
    ] as const;

    for (const [viewport, path, file] of captures) {
      await page.setViewportSize(viewport);
      await page.goto(path);
      await page.screenshot({ path: file, fullPage: true });
      await expectNoHorizontalOverflow(page);
    }
  });

  test("Dark Mode critical routes keep light text on dark intentional surfaces", async ({ page }, testInfo) => {
    testInfo.setTimeout(120_000);
    await preparePage(page, { auth: "user", theme: "dark" });
    await page.setViewportSize(desktop);

    for (const [path, screenshot] of [
      ["/", "qa/qa-dark-home-regression.png"],
      ["/dashboard", "qa/qa-dark-dashboard-regression.png"],
      ["/knowledge-base", "qa/qa-dark-knowledge-base-regression.png"],
    ] as const) {
      await page.goto(path);
      await setTheme(page, "dark");
      await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
      await expect(page.getByTestId("global-header")).toBeVisible();
      await expectReadable(page.getByRole("heading", { level: 1 }).first(), 3);
      await page.screenshot({ path: screenshot, fullPage: true });
      await expectNoHorizontalOverflow(page);
    }
  });
});
