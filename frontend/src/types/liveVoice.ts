import type { ChatMessage } from "./chat";

export type LiveVoiceConnectionStatus =
  | "disabled"
  | "unconfigured"
  | "disconnected"
  | "requesting-permission"
  | "requesting-token"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnecting"
  | "error";

export type LiveVoiceTurnMode = "idle" | "listening" | "thinking" | "speaking" | "muted";

export type LiveVoiceStatus = {
  provider: "elevenlabs";
  liveVoiceEnabled: boolean;
  liveVoiceConfigured: boolean;
  customLlmEnabled?: boolean;
  customLlmConfigured?: boolean;
  legacyFallbackEnabled: boolean;
  agentIdConfigured: boolean;
  apiKeyConfigured?: boolean;
  serverLocation: "us" | "eu-residency" | "in-residency" | "global" | string;
  residencyMode?: "standard" | "isolated-eu" | "isolated-in" | "isolated-sg" | string;
  environment: string;
  publicBackendReachable?: boolean;
  blockingIssues?: Array<{ code: string; message: string }>;
};

export type ConversationTokenRequest = {
  profileId?: string | null;
  appConversationId?: string | null;
  route: string;
  selectedProfileNode?: string | null;
  selectedRecommendationId?: string | null;
  language: "en" | "ro" | "no";
  voicePersonality: string;
  conversationMode: string;
  clientContext?: Record<string, unknown>;
};

export type ConversationTokenResponse = {
  token: string;
  conversationId: string;
  serverLocation: string;
  environment: string;
};

export type LatestLiveVoiceTurn = {
  messageId: string;
  appConversationId: string | null;
  answer: string;
  sourcesUsed: ChatMessage["sourcesUsed"];
  confidenceNote: string;
  ethicalNote: string;
  groundingStatus: ChatMessage["groundingStatus"];
  profileSignals: string[];
  retrievalStatus: Record<string, unknown>;
  timing: Record<string, number>;
  ragRunId?: string | null;
  contextQuality?: ChatMessage["contextQuality"];
  createdAt: string;
};

export type LiveVoiceOrganicContext = {
  activeProfileId: string;
  appConversationId: string | null;
  route: string;
  selectedProfileNode: string | null;
  selectedRecommendationId: string | null;
  language: "en" | "ro" | "no";
  voicePersonality: string;
  conversationMode: string;
  voiceConsent: boolean;
  theme?: string;
};
