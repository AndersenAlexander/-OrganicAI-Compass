import { apiClient } from "./client";
import type {
  ConversationTokenRequest,
  ConversationTokenResponse,
  LatestLiveVoiceTurn,
  LiveVoiceStatus,
} from "../types/liveVoice";

function resolveAudioUrl(audioUrl: string) {
  const baseUrl = apiClient.defaults.baseURL;
  if (!audioUrl || !audioUrl.startsWith("/") || !baseUrl?.startsWith("http")) return audioUrl;

  const apiOrigin = new URL(baseUrl).origin;
  return `${apiOrigin}${audioUrl}`;
}

export async function transcribeAudio(audioBlob: Blob): Promise<{ transcript: string }> {
  const formData = new FormData();
  formData.append("file", audioBlob, "voice-message.webm");
  const { data } = await apiClient.post<{ transcript: string }>("/voice/transcribe", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function synthesizeSpeech(text: string): Promise<{ audioUrl: string }> {
  const { data } = await apiClient.post<{ audio_url?: string; audioUrl?: string }>("/voice/speak", { text });
  return { audioUrl: resolveAudioUrl(data.audioUrl ?? data.audio_url ?? "") };
}

export const speakText = synthesizeSpeech;

export async function getLiveVoiceStatus(): Promise<LiveVoiceStatus> {
  const { data } = await apiClient.get<LiveVoiceStatus>("/voice/status");
  return data;
}

export async function createLiveConversationToken(payload: ConversationTokenRequest): Promise<ConversationTokenResponse> {
  const { data } = await apiClient.post<{
    token: string;
    conversation_id: string;
    server_location: string;
    environment: string;
  }>("/voice/conversation-token", {
    profile_id: payload.profileId ?? null,
    app_conversation_id: payload.appConversationId ?? null,
    route: payload.route,
    selected_profile_node: payload.selectedProfileNode ?? null,
    selected_recommendation_id: payload.selectedRecommendationId ?? null,
    language: payload.language,
    voice_personality: payload.voicePersonality,
    conversation_mode: payload.conversationMode,
    client_context: payload.clientContext ?? {},
  });
  return {
    token: data.token,
    conversationId: data.conversation_id,
    serverLocation: data.server_location,
    environment: data.environment,
  };
}

export async function getLatestLiveVoiceTurn(conversationId: string): Promise<LatestLiveVoiceTurn> {
  const { data } = await apiClient.get<LatestLiveVoiceTurn>(`/voice/conversations/${conversationId}/latest-turn`);
  return data;
}
