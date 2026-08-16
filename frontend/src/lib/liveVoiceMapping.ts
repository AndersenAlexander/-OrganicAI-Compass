import type { ChatMessage } from "../types/chat";
import type { LiveVoiceConnectionStatus, LiveVoiceStatus, LiveVoiceTurnMode } from "../types/liveVoice";
import { extractApiError } from "../api/client";

export function liveVoiceAvailability(status: LiveVoiceStatus | null): LiveVoiceConnectionStatus {
  if (!status) return "disconnected";
  if (!status.liveVoiceEnabled) return "disabled";
  if (!status.liveVoiceConfigured) return "unconfigured";
  return "disconnected";
}

export function mapLiveTurnMode(options: {
  connectionStatus: LiveVoiceConnectionStatus;
  sdkMode: "listening" | "speaking";
  isMuted: boolean;
  waitingForAgent: boolean;
}): LiveVoiceTurnMode {
  if (options.connectionStatus !== "connected") return "idle";
  if (options.isMuted) return "muted";
  if (options.sdkMode === "speaking") return "speaking";
  if (options.waitingForAgent) return "thinking";
  return "listening";
}

export function liveVoiceErrorMessage(error: unknown): string {
  const apiError = extractApiError(error);
  const hasApiResponse = Boolean((error as { response?: unknown })?.response);
  const value = String((hasApiResponse ? apiError.message : "") || (error as Error)?.message || error || "");
  const status = (error as { response?: { status?: number } })?.response?.status;
  if (status === 401) return "Authentication is required before starting live voice conversation.";
  if (status === 409) return "Live voice conversation is disabled. You can continue with text or voice message.";
  if (status === 429) return "Live voice is rate limited. Wait a moment and try again.";
  if (status === 503) return value || "ElevenLabs live voice is not configured or temporarily unavailable.";
  if (status === 502) return "ElevenLabs returned an invalid response. Continue with text chat for now.";
  if (/permission|denied/i.test(value)) return "Microphone permission was denied. You can continue with text chat.";
  if (/mediaDevices|getUserMedia|microphone/i.test(value)) return "This browser does not support live microphone access. Use text chat or voice message.";
  if (/network|disconnect/i.test(value)) return "The live voice connection was interrupted. You can retry or continue with text.";
  return value || "Live voice conversation could not be started.";
}

export function messageDedupeKey(message: Pick<ChatMessage, "role" | "content"> & { eventId?: string | number | null }) {
  return `${message.role}:${message.eventId ?? message.content.trim().toLowerCase()}`;
}

export function appendDedupedMessage(messages: ChatMessage[], message: ChatMessage & { eventId?: string | number | null }) {
  const key = messageDedupeKey(message);
  const exists = messages.some((item) => messageDedupeKey({ role: item.role, content: item.content, eventId: item.id }) === key || item.id === message.id);
  return exists ? messages : [...messages, message];
}
