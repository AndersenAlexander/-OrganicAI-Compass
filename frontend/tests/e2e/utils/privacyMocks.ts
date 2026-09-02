import type { Page, Route } from "@playwright/test";

export const user = {
  id: "33333333-3333-4333-8333-333333333333",
  email: "privacy@example.test",
  name: "Privacy User",
  is_demo: false,
  email_verified_at: "2026-07-28T00:00:00Z",
  account_status: "active",
};

export const preferences = {
  conversationPersistenceMode: "account-history",
  voiceTranscriptPersistenceMode: "ephemeral",
  voiceAudioStorageEnabled: false,
  productAnalyticsEnabled: false,
  researchParticipationEnabled: false,
  personalizationEnabled: true,
  serviceEmailEnabled: true,
  marketingEmailEnabled: false,
  updatedAt: "2026-07-28T00:00:00Z",
};

export const inventory = {
  tableCount: 176,
  tableCategoryMap: { conversations: ["conversation-history"], messages: ["conversation-history"], users: ["account-profile"] },
  categories: [
    {
      key: "conversation-history",
      title: "Conversation History",
      description: "Persisted coach conversations and assistant replies.",
      tables: ["conversations", "messages"],
      purposes: ["user-requested-feature"],
      processing_classification: "user-requested-feature",
      data_origin: "provided-by-user",
      sensitivity: "potentially-sensitive",
      retention_policy_key: "account-content",
      export_behavior: "included",
      deletion_behavior: "active-delete",
      research_behavior: "excluded-when-ephemeral",
      provider_behavior: "manual-review",
    },
    {
      key: "account-profile",
      title: "Account Profile",
      description: "Account identity and service settings.",
      tables: ["users", "user_privacy_settings"],
      purposes: ["essential-service"],
      processing_classification: "essential-service",
      data_origin: "provided-by-user",
      sensitivity: "confidential",
      retention_policy_key: "account-lifecycle",
      export_behavior: "included-with-secret-exclusion",
      deletion_behavior: "tombstone",
      research_behavior: "direct-identifiers-excluded",
      provider_behavior: "not-shared",
    },
  ],
};

export async function mockAuth(page: Page) {
  await page.route("**/api/auth/refresh", async (route) => route.fulfill({ json: { access_token: "privacy-token", token_type: "bearer", expires_in: 900, user } }));
  await page.route("**/api/auth/me", async (route) => route.fulfill({ json: user }));
}

export async function mockPrivacyApi(page: Page) {
  let currentPreferences = { ...preferences };
  let exports = [
    {
      id: "export-1",
      status: "ready",
      format: "zip-json",
      createdAt: "2026-07-28T00:05:00Z",
      expiresAt: "2026-07-29T00:05:00Z",
      sizeBytes: 2048,
      checksumSha256: "abc123",
      downloadedAt: null,
    },
  ];
  let requests: Array<Record<string, unknown>> = [];
  const consents = [
    { id: "consent-1", purposeKey: "essential-service", action: "not-required", legalBasisLabel: "essential-service", source: "migration", occurredAt: "2026-07-28T00:00:00Z" },
  ];

  await page.route("**/api/privacy/summary", async (route) =>
    route.fulfill({
      json: {
        policy: { version: "2026-privacy-draft-1", title: "OrganicAI Compass Privacy Technical Draft", technicalDraft: true, legalReviewRequired: true },
        preferences: currentPreferences,
        categoryCount: inventory.categories.length,
        providerCount: 4,
        backupDisclosure: "Deletion removes active rows and backups expire by retention policy.",
        legacyOrphanArchive: "Legacy orphan archive is excluded from export, deletion, research and RAG flows.",
      },
    }),
  );
  await page.route("**/api/privacy/preferences", async (route) => {
    if (route.request().method() === "PUT") {
      currentPreferences = { ...currentPreferences, ...(route.request().postDataJSON() as Record<string, unknown>), updatedAt: "2026-07-28T00:10:00Z" };
      consents.unshift({ id: `consent-${consents.length + 1}`, purposeKey: "conversation-history", action: currentPreferences.conversationPersistenceMode === "ephemeral" ? "withdrawn" : "granted", legalBasisLabel: "optional-consent", source: "privacy-center", occurredAt: "2026-07-28T00:10:00Z" });
    }
    await route.fulfill({ json: currentPreferences });
  });
  await page.route("**/api/privacy/inventory", async (route) => route.fulfill({ json: inventory }));
  await page.route("**/api/privacy/providers", async (route) =>
    route.fulfill({
      json: [
        { provider: "OpenAI", purpose: "AI response generation and embeddings.", dataCategories: ["conversation-history"], connectivity: "configured-unverified", featuresUsed: ["chat-completions"], trainingOptInStatus: "unknown", abuseMonitoringMode: "unknown", dataResidencyStatus: "unknown", dataControlsVerified: false, retentionStatus: "provider-policy-review-required", deletionCapability: "no-universal-delete-api", transferReviewStatus: "manual-review-required", dpaReviewStatus: "manual-review-required", lastVerifiedDate: null },
        { provider: "ElevenLabs", purpose: "Live voice sessions when configured.", dataCategories: ["conversation-history"], connectivity: "configured-unverified", agentConfigured: true, retentionStatus: "unknown", audioSavingStatus: "unknown", zeroRetentionStatus: "unknown", webhookSignatureStatus: "not-configured", deletionCapability: "adapter-disabled", transferReviewStatus: "manual-review-required", dpaReviewStatus: "manual-review-required", lastVerifiedDate: null },
        { provider: "Email", purpose: "Transactional notifications.", dataCategories: ["account-profile"], connectivity: "not-configured", deliveryDriver: "development-outbox", senderVerifiedStatus: "manual-review-required", deliveryTrackingStatus: "smtp-acceptance-only", retentionStatus: "operational-events-only", deletionCapability: "not-applicable", transferReviewStatus: "manual-review-required", dpaReviewStatus: "manual-review-required", lastVerifiedDate: null },
      ],
    }),
  );
  await page.route("**/api/privacy/research", async (route) => route.fulfill({ json: { participationEnabled: currentPreferences.researchParticipationEnabled, pseudonymousSubjectId: null, directIdentifiersIncluded: false, ephemeralDataExcluded: true, withdrawalAvailable: true } }));
  await page.route("**/api/privacy/consents", async (route) => route.fulfill({ json: consents }));
  await page.route("**/api/privacy/requests", async (route) => route.fulfill({ json: requests }));
  await page.route("**/api/privacy/reauthenticate", async (route) => route.fulfill({ json: { recentAuthentication: true } }));
  await page.route("**/api/privacy/exports", async (route) => {
    if (route.request().method() === "POST") {
      const artifact = { id: "export-new", status: "ready", format: "zip-json", createdAt: "2026-07-28T00:12:00Z", expiresAt: "2026-07-29T00:12:00Z", sizeBytes: 4096, checksumSha256: "def456", downloadedAt: null };
      exports = [artifact, ...exports];
      return route.fulfill({ json: artifact });
    }
    return route.fulfill({ json: exports });
  });
  await page.route("**/api/privacy/exports/*/download", async (route) => route.fulfill({ body: "encrypted-export", contentType: "application/octet-stream" }));
  await page.route("**/api/privacy/exports/*", async (route) => {
    if (route.request().method() === "DELETE") {
      const artifactId = route.request().url().split("/").pop();
      exports = exports.filter((artifact) => artifact.id !== artifactId);
      return route.fulfill({ status: 204, body: "" });
    }
    return route.fallback();
  });
  await page.route("**/api/privacy/deletion/categories/*/preview", async (route) => route.fulfill({ json: { category: inventory.categories[0], rowCounts: { conversations: 1, messages: 2 }, providerImpact: "provider records may be marked pending", requiresConfirmation: true } }));
  await page.route("**/api/privacy/deletion/categories/*", async (route) => route.fulfill({ json: { categoryKey: "conversation-history", deletedRows: { conversations: 1, messages: 2 }, providerStatus: "not-requested" } }));
  await page.route("**/api/privacy/account-deletion", async (route) => {
    requests = [{ id: "deletion-request-1", type: "account-deletion", status: "queued", scope: {}, submittedAt: "2026-07-28T00:15:00Z", completedAt: null, resultSummary: { graceUntil: "2026-08-04T00:15:00Z" } }];
    return route.fulfill({ json: { requestId: "deletion-request-1", status: "queued", graceUntil: "2026-08-04T00:15:00Z" } });
  });
  await page.route("**/api/privacy/account-deletion/*/cancel", async (route) => {
    requests = [];
    return route.fulfill({ json: { requestId: "deletion-request-1", status: "cancelled" } });
  });
  await page.route("**/api/privacy/research/withdraw", async (route) => {
    currentPreferences = { ...currentPreferences, researchParticipationEnabled: false };
    return route.fulfill({ json: { researchParticipationEnabled: false, futureResearchCollection: "disabled", identifiableCleanup: "manual-review-required" } });
  });
}

export async function setupPrivacyPage(page: Page) {
  await mockAuth(page);
  await mockPrivacyApi(page);
}

export async function fulfillNotFound(route: Route) {
  await route.fulfill({ status: 404, json: { error: { message: "Not mocked" } } });
}
