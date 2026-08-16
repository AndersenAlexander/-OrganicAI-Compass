import { expect, test, type Page } from "@playwright/test";

const activeProfileId = "demo-profile";
const appConversationId = "app-conversation-live";
const elevenLabsConversationId = "conv_playwright";
function corsHeaders(origin: string | undefined, requestId: string) {
  return {
    "Access-Control-Allow-Origin": origin || "http://127.0.0.1:5191",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Expose-Headers": "X-Request-ID",
    "X-Request-ID": requestId,
  };
}

const emptyFeedback = {
  confirmed_nodes: [],
  hidden_recommendations: [],
  strength_adjustments: {},
  archetype_override: null,
  user_notes: {},
};

function profile() {
  return {
    id: activeProfileId,
    diagnostic_id: "diagnostic-live",
    primary_archetype: "Curious Explorer",
    secondary_archetype: "Responsible Builder",
    strengths: ["Systems Thinking"],
    values: ["Agency"],
    fears: ["Losing human control"],
    creative_tendencies: ["Prototype and reflect"],
    ai_collaboration_style: "Co-Creator",
    contribution_domains: ["Human-centred AI"],
    recommended_learning_paths: ["Responsible AI Practice"],
    uncertainties: [],
    risk_notes: [],
    ethical_note: "This is an exploratory profile, not a fixed label.",
    user_feedback: emptyFeedback,
    created_at: "2026-01-01T00:00:00Z",
  };
}

async function prepareLiveVoicePage(page: Page, options: { tokenError?: boolean } = {}) {
  await page.setViewportSize({ width: 1448, height: 1086 });
  await page.addInitScript(
    ({ profileId }) => {
      localStorage.setItem("organicai_active_profile_id", profileId);
      localStorage.setItem("organicai-theme", "dark");
      localStorage.setItem("organicai_live_voice_test_adapter", "true");
      localStorage.setItem(
        "organicai_coach_preferences",
        JSON.stringify({
          voiceMode: "live",
          voiceConsent: true,
          storeTranscripts: false,
          autoPlay: false,
          language: "en",
          voicePersonality: "Calm Guide",
          conversationMode: "Explain simply",
        }),
      );
      Object.defineProperty(navigator, "mediaDevices", {
        configurable: true,
        value: {
          getUserMedia: async () => {
            const track = {
              kind: "audio",
              enabled: true,
              readyState: "live",
              stop: () => undefined,
              addEventListener: () => undefined,
              removeEventListener: () => undefined,
            };
            return {
              active: true,
              id: "mock-live-audio-stream",
              getTracks: () => [track],
              getAudioTracks: () => [track],
              getVideoTracks: () => [],
              addEventListener: () => undefined,
              removeEventListener: () => undefined,
            };
          },
        },
      });
    },
    { profileId: activeProfileId },
  );

  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (!url.pathname.startsWith("/api/")) {
      await route.continue();
      return;
    }
    const origin = route.request().headers().origin;

    if (url.pathname.endsWith("/auth/me")) {
      await route.fulfill({
        status: 200,
        json: {
          id: "11111111-1111-4111-8111-111111111111",
          email: "alex@example.test",
          name: "Alex User",
          is_demo: false,
        },
      });
      return;
    }

    if (url.pathname.endsWith("/auth/refresh")) {
      await route.fulfill({
        status: 200,
        json: {
          access_token: "playwright-memory-access-token",
          token_type: "bearer",
          expires_in: 900,
          user: {
            id: "11111111-1111-4111-8111-111111111111",
            email: "alex@example.test",
            name: "Alex User",
            is_demo: false,
          },
        },
      });
      return;
    }

    if (url.pathname === "/api/profiles") {
      await route.fulfill({
        status: 200,
        json: [{ id: activeProfileId, created_at: "2026-01-01T00:00:00Z", data: {} }],
      });
      return;
    }

    if (url.pathname === "/api/voice/status") {
      await route.fulfill({
        status: 200,
        headers: corsHeaders(origin, "req-live-status-1"),
        json: {
          provider: "elevenlabs",
          liveVoiceEnabled: true,
          liveVoiceConfigured: true,
          customLlmEnabled: true,
          customLlmConfigured: true,
          legacyFallbackEnabled: true,
          agentIdConfigured: true,
          apiKeyConfigured: true,
          serverLocation: "",
          residencyMode: "standard",
          environment: "production",
          publicBackendReachable: true,
          blockingIssues: [],
        },
      });
      return;
    }

    if (url.pathname === "/api/voice/conversation-token") {
      if (options.tokenError) {
        await route.fulfill({
          status: 503,
          headers: corsHeaders(origin, "req-live-token-error"),
          json: {
            error: {
              code: "VOICE_PROVIDER_UNAVAILABLE",
              message: "Live voice is temporarily unavailable.",
              requestId: "req-live-token-error",
              details: null,
            },
          },
        });
        return;
      }
      await route.fulfill({
        status: 200,
        headers: corsHeaders(origin, "req-live-token-1"),
        json: {
          token: "temporary-elevenlabs-token",
          conversation_id: elevenLabsConversationId,
          server_location: "",
          environment: "production",
        },
      });
      return;
    }

    if (url.pathname === `/api/voice/conversations/${elevenLabsConversationId}/latest-turn`) {
      await route.fulfill({
        status: 200,
        json: {
          messageId: "assistant-live-1",
          appConversationId,
          answer: "Start with one small reversible experiment.",
          sourcesUsed: [],
          confidenceNote: "Profile-aware guidance generated through OrganicAI.",
          ethicalNote: "Keep final decisions human-led.",
          groundingStatus: "profile_grounded",
          profileSignals: ["Systems Thinking"],
          retrievalStatus: { rag_run_id: "rag-live-1", context_quality: "partial" },
          timing: { total_ms: 12 },
          ragRunId: "rag-live-1",
          contextQuality: "partial",
          createdAt: "2026-01-01T00:00:00Z",
        },
      });
      return;
    }

    if (url.pathname === `/api/profiles/${activeProfileId}`) {
      await route.fulfill({ status: 200, json: profile() });
      return;
    }

    if (url.pathname === `/api/profiles/${activeProfileId}/feedback`) {
      await route.fulfill({ status: 200, json: emptyFeedback });
      return;
    }

    await route.fulfill({ status: 200, json: [] });
  });
}

test.describe("ElevenLabs live voice conversation", () => {
  test.beforeEach(async ({ page }) => {
    await prepareLiveVoicePage(page);
  });

  test("keeps one shared live session across Coach page and floating widget", async ({ page }) => {
    await page.goto(`/coach/${activeProfileId}`);
    await expect(page.getByRole("heading", { name: "Live voice conversation" })).toBeVisible();
    await page.getByText("Voice connection diagnostics").click();
    await expect(page.getByText("Live voice enabled: true")).toBeVisible();
    await expect(page.getByText("Custom LLM configured: true")).toBeVisible();
    await expect(page.getByText("Residency mode: standard")).toBeVisible();
    await expect(page.getByText("Request ID: req-live-status-1")).toBeVisible();

    await page.getByRole("button", { name: "Start live conversation" }).click();
    await expect(page.getByRole("heading", { name: "Listening" })).toBeVisible();
    await expect(page.getByText("Request ID: req-live-token-1")).toBeVisible();

    await page.evaluate(() => window.__organicaiLiveVoiceTest?.emitUser("I want to use AI well."));
    await expect(page.getByText("I want to use AI well.", { exact: true })).toBeVisible();

    await page.evaluate(() => {
      window.__organicaiLiveVoiceTest?.setTurnMode("speaking");
      window.__organicaiLiveVoiceTest?.emitAgent("Start with one small reversible experiment.");
    });
    await expect(page.getByRole("heading", { name: "OrganicAI Coach is speaking" })).toBeVisible();
    await expect(page.getByText("Start with one small reversible experiment.", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Profile-aware guidance generated through OrganicAI.", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Keep final decisions human-led.", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Review transcript")).toHaveCount(0);

    await page.getByRole("button", { name: "Mute microphone" }).click();
    await expect(page.getByRole("heading", { name: "Microphone muted" })).toBeVisible();
    await page.getByRole("button", { name: "Unmute microphone" }).click();
    await page.evaluate(() => window.__organicaiLiveVoiceTest?.setTurnMode("listening"));
    await expect(page.getByRole("heading", { name: "Listening" })).toBeVisible();

    await page.getByRole("link", { name: "Human Potential Map" }).click();
    await expect(page).toHaveURL(new RegExp(`/profile/${activeProfileId}$`));
    await expect(page.getByRole("button", { name: "Coach listening" })).toBeVisible();
    await page.getByRole("button", { name: "Coach listening" }).click();
    const coachPanel = page.getByRole("region", { name: "OrganicAI Coach" });
    await expect(coachPanel).toContainText("Live conversation active");
    await expect(coachPanel).toContainText("Start with one small reversible experiment.");

    await coachPanel.getByRole("button", { name: "End", exact: true }).click();
    await expect(coachPanel.getByRole("button", { name: "Start live conversation" })).toBeVisible();
    await expect(page.locator("body")).not.toContainText("temporary-elevenlabs-token");
    await expect(page.locator("body")).not.toContainText("agent_");
  });

  test("shows safe diagnostics and fallback when provider token fails", async ({ page }) => {
    await page.unroute("**/*");
    await prepareLiveVoicePage(page, { tokenError: true });
    await page.goto(`/coach/${activeProfileId}`);

    await page.getByRole("button", { name: "Start live conversation" }).click();
    await expect(page.getByRole("alert")).toContainText("Live voice is temporarily unavailable.");
    await page.getByText("Voice connection diagnostics").click();
    await expect(page.getByText("Last safe error code: VOICE_PROVIDER_UNAVAILABLE")).toBeVisible();
    await expect(page.getByText("Request ID: req-live-token-error")).toBeVisible();
    await expect(page.getByRole("button", { name: "Use voice message instead" })).toBeVisible();
    await expect(page.locator("body")).not.toContainText("temporary-elevenlabs-token");
  });
});
