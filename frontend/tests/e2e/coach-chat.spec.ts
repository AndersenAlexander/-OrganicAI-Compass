import { expect, test } from "@playwright/test";
import { installMockAuthSession } from "./utils/authSession";

test("AI Coach sends JSON chat, keeps current profile context after refresh, and recovers with retry", async ({ page }) => {
  await installMockAuthSession(page, { state: "demo", profileId: "demo-profile" });
  await page.route("**/api/privacy/preferences", (route) => route.fulfill({
    json: {
      conversationPersistenceMode: "account-history",
      voiceTranscriptPersistenceMode: "ephemeral",
      voiceAudioStorageEnabled: false,
      productAnalyticsEnabled: false,
      researchParticipationEnabled: false,
      personalizationEnabled: true,
      serviceEmailEnabled: true,
      marketingEmailEnabled: false,
    },
  }));
  await page.route("**/api/voice/status", (route) => route.fulfill({
    json: {
      provider: "elevenlabs",
      liveVoiceEnabled: false,
      liveVoiceConfigured: false,
      customLlmEnabled: false,
      customLlmConfigured: false,
      legacyFallbackEnabled: true,
      agentIdConfigured: false,
      apiKeyConfigured: false,
      serverLocation: "",
      residencyMode: "standard",
      environment: "test",
      publicBackendReachable: false,
      blockingIssues: [],
    },
  }));

  const requests: Array<Record<string, unknown>> = [];
  let providerUnavailable = false;
  await page.route("**/api/chat", async (route) => {
    const payload = route.request().postDataJSON() as Record<string, unknown>;
    requests.push(payload);
    if (providerUnavailable) {
      await route.fulfill({ status: 503, json: { error: { code: "PROVIDER_UNAVAILABLE", message: "Provider unavailable" } } });
      return;
    }
    const message = String(payload.message || "");
    const answer = message.includes("evidence")
      ? "For Human-Centred AI Product Designer, Ideation, UX/UI, Product Thinking, Responsible AI, Risk Reasoning, and Communication are practically verified."
      : message.includes("refresh")
        ? "The refreshed Coach still uses the selected persisted profile."
        : "OrganicAI Compass helps people use AI with evidence, context, and human control.";
    await route.fulfill({
      json: {
        answer,
        conversation_id: "coach-conversation-1",
        message_id: `message-${requests.length}`,
        suggested_actions: [],
        confidence_note: "Grounded in current persisted profile context.",
        sources_used: [],
        ethical_note: "Keep final decisions human-led.",
        intent: "conversational_question",
        grounding_status: "profile_grounded",
        retrieval_status: { context_quality: "insufficient" },
        timing: {},
      },
    });
  });

  await page.goto("/coach/demo-profile");
  const input = page.getByPlaceholder("Ask anything");
  await input.fill("What is OrganicAI Compass?");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.getByText("OrganicAI Compass helps people use AI with evidence, context, and human control.")).toBeVisible();
  expect(requests[0].profile_id).toBe("demo-profile");
  expect(requests[0].mode).toBe("text");

  await page.reload();
  await page.getByPlaceholder("Ask anything").fill("What evidence has been verified for my current career direction?");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.getByText(/Human-Centred AI Product Designer, Ideation, UX\/UI/)).toBeVisible();
  expect(requests[1].profile_id).toBe("demo-profile");

  providerUnavailable = true;
  await page.getByPlaceholder("Ask anything").fill("Try provider recovery");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.getByRole("alert")).toContainText("temporarily unavailable");
  await expect(page.getByRole("button", { name: "Retry message" })).toBeVisible();
  providerUnavailable = false;
  await page.getByRole("button", { name: "Retry message" }).click();
  await expect(page.getByText("OrganicAI Compass helps people use AI with evidence, context, and human control.")).toBeVisible();
  await expect(page.getByText("Try provider recovery", { exact: true })).toHaveCount(1);
  expect(requests).toHaveLength(4);
  expect(requests[2].message).toBe("Try provider recovery");
  expect(requests[3].message).toBe("Try provider recovery");
});
