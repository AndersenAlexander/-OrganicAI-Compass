export type PrivacyPreferences = {
  conversationPersistenceMode: "account-history" | "ephemeral";
  voiceTranscriptPersistenceMode: "account-history" | "ephemeral";
  voiceAudioStorageEnabled: boolean;
  productAnalyticsEnabled: boolean;
  researchParticipationEnabled: boolean;
  personalizationEnabled: boolean;
  serviceEmailEnabled: boolean;
  marketingEmailEnabled: boolean;
  updatedAt: string;
};

export type PrivacySummary = {
  policy: { version: string; title: string; technicalDraft: boolean; legalReviewRequired: boolean };
  preferences: PrivacyPreferences;
  categoryCount: number;
  providerCount: number;
  backupDisclosure: string;
  legacyOrphanArchive: string;
};

export type PersonalDataCategory = {
  key: string;
  title: string;
  description: string;
  tables: string[];
  purposes: string[];
  processing_classification: string;
  data_origin: string;
  sensitivity: string;
  retention_policy_key: string;
  export_behavior: string;
  deletion_behavior: string;
  research_behavior: string;
  provider_behavior: string;
};

export type PrivacyInventory = {
  categories: PersonalDataCategory[];
  tableCount: number;
  tableCategoryMap: Record<string, string[]>;
};

export type PrivacyConsentEvent = {
  id: string;
  purposeKey: string;
  action: string;
  legalBasisLabel: string;
  source: string;
  occurredAt: string;
};

export type PrivacyRequestRecord = {
  id: string;
  type: string;
  status: string;
  scope: Record<string, unknown>;
  submittedAt: string;
  completedAt: string | null;
  resultSummary: Record<string, unknown>;
};

export type PrivacyProvider = {
  provider: string;
  purpose: string;
  dataCategories?: string[];
  connectivity?: string;
  featuresUsed?: string[];
  trainingOptInStatus?: string;
  abuseMonitoringMode?: string;
  dataResidencyStatus?: string;
  dataControlsVerified?: boolean;
  agentConfigured?: boolean;
  webhookSignatureStatus?: string;
  deliveryDriver?: string;
  senderVerifiedStatus?: string;
  deliveryTrackingStatus?: string;
  retentionStatus: string;
  audioSavingStatus?: string;
  zeroRetentionStatus?: string;
  deletionCapability: string;
  linkedRecordCount?: number;
  transferReviewStatus: string;
  dpaReviewStatus: string;
  lastVerifiedDate: string | null;
};

export type PrivacyResearchSummary = {
  participationEnabled: boolean;
  pseudonymousSubjectId: string | null;
  directIdentifiersIncluded: boolean;
  ephemeralDataExcluded: boolean;
  withdrawalAvailable: boolean;
  configurationComplete: boolean;
  missingFields: string[];
  liveRecruitmentEnabled: boolean;
  empiricalDataCollectionEnabled: boolean;
  syntheticEvaluationEnabled: boolean;
};

export type PrivacyExportArtifact = {
  id: string;
  status: string;
  format: string;
  createdAt: string;
  expiresAt: string;
  sizeBytes: number;
  checksumSha256: string;
  downloadedAt: string | null;
};

export type CategoryDeletionPreview = {
  category: PersonalDataCategory;
  rowCounts: Record<string, number>;
  providerImpact: string;
  requiresConfirmation: boolean;
};
