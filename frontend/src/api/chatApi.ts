import { apiClient } from "./client";
import type { ChatMessage, ChatResponse } from "../types/chat";

export type SendCoachMessagePayload = {
  message: string;
  profileId?: string | null;
  conversationId?: string | null;
  mode?: "text" | "voice";
  voicePersonality?: string;
  conversationMode?: string;
  route?: string;
  selectedProfileNode?: string | null;
  language?: string;
  clientContext?: Record<string, unknown>;
};

export async function sendChatMessage(profileId: string, message: string, mode: "text" | "voice" = "text") {
  const { data } = await apiClient.post<ChatResponse>("/chat", {
    profile_id: profileId,
    message,
    mode
  });
  return data;
}

export async function sendCoachMessage(payload: SendCoachMessagePayload): Promise<{
  answer: string;
  conversationId?: string;
  messageId?: string;
  suggestedActions: string[];
  confidenceNote: string;
  sourcesUsed: ChatResponse["sources_used"];
  ethicalNote: string;
  intent: string;
  executedCommand?: { name: string; parameters: Record<string, unknown> } | null;
  profileSignals: string[];
  groundingStatus: "grounded" | "profile_grounded" | "general";
  retrievalStatus: Record<string, unknown>;
  timing: Record<string, number>;
  ragRunId?: string;
  contextQuality?: "strong"|"partial"|"insufficient";
}> {
  const { data } = await apiClient.post<ChatResponse>("/chat", {
    message: payload.message,
    profile_id: payload.profileId ?? null,
    conversation_id: payload.conversationId ?? null,
    mode: payload.mode ?? "text",
    voice_personality: payload.voicePersonality ?? "Calm Guide",
    conversation_mode: payload.conversationMode ?? "Explain simply"
    ,route: payload.route ?? window.location.pathname
    ,selected_profile_node: payload.selectedProfileNode ?? null
    ,language: payload.language ?? "en"
    ,client_context: payload.clientContext ?? {}
  });

  return {
    answer: data.answer,
    conversationId: data.conversationId ?? data.conversation_id,
    messageId: data.messageId ?? data.message_id,
    suggestedActions: data.suggested_actions ?? [],
    confidenceNote: data.confidence_note ?? "",
    sourcesUsed: data.sources_used ?? [],
    ethicalNote: data.ethical_note ?? "",
    intent: data.intent ?? "conversational_question",
    executedCommand: data.executed_command,
    profileSignals: data.profile_signals_used ?? [],
    groundingStatus: data.grounding_status ?? (data.sources_used?.length ? "grounded" : "general"),
    retrievalStatus: data.retrieval_status ?? {},
    timing: data.timing ?? {},
    ragRunId:data.rag_run_id,
    contextQuality:data.context_quality
  };
}

export async function getChatHistory(profileId: string) {
  const { data } = await apiClient.get<ChatMessage[]>(`/chat/${profileId}/history`);
  return data;
}
