import { describe, expect, it } from "vitest";
import {
  appendDedupedMessage,
  liveVoiceAvailability,
  liveVoiceErrorMessage,
  liveVoiceMetadataAvailable,
  mapLiveTurnMode,
} from "./liveVoiceMapping";
import type { ChatMessage } from "../types/chat";

const status = {
  provider: "elevenlabs" as const,
  liveVoiceEnabled: true,
  liveVoiceConfigured: true,
  legacyFallbackEnabled: true,
  agentIdConfigured: true,
  serverLocation: "eu-residency",
  environment: "production",
};

function message(id: string, content: string): ChatMessage {
  return { id, role: "user", content, createdAt: "2026-07-27T00:00:00Z", inputMode: "voice" };
}

describe("live voice mapping", () => {
  it("maps disabled, unconfigured and available status", () => {
    expect(liveVoiceAvailability(null)).toBe("disconnected");
    expect(liveVoiceAvailability({ ...status, liveVoiceEnabled: false })).toBe("disabled");
    expect(liveVoiceAvailability({ ...status, liveVoiceConfigured: false })).toBe("unconfigured");
    expect(liveVoiceAvailability(status)).toBe("disconnected");
  });

  it("requests OrganicAI turn metadata only when Custom LLM is enabled and configured", () => {
    expect(liveVoiceMetadataAvailable(null)).toBe(false);
    expect(liveVoiceMetadataAvailable(status)).toBe(false);
    expect(liveVoiceMetadataAvailable({ ...status, customLlmEnabled: false, customLlmConfigured: true })).toBe(false);
    expect(liveVoiceMetadataAvailable({ ...status, customLlmEnabled: true, customLlmConfigured: false })).toBe(false);
    expect(liveVoiceMetadataAvailable({ ...status, customLlmEnabled: true, customLlmConfigured: true })).toBe(true);
  });

  it("maps connected turn modes without a conflicting state machine", () => {
    expect(mapLiveTurnMode({ connectionStatus: "connected", sdkMode: "listening", isMuted: false, waitingForAgent: false })).toBe("listening");
    expect(mapLiveTurnMode({ connectionStatus: "connected", sdkMode: "speaking", isMuted: false, waitingForAgent: false })).toBe("speaking");
    expect(mapLiveTurnMode({ connectionStatus: "connected", sdkMode: "listening", isMuted: true, waitingForAgent: false })).toBe("muted");
    expect(mapLiveTurnMode({ connectionStatus: "connected", sdkMode: "listening", isMuted: false, waitingForAgent: true })).toBe("thinking");
  });

  it("returns explicit recoverable error messages", () => {
    expect(liveVoiceErrorMessage({ response: { status: 401, data: { detail: "No" } } })).toContain("Authentication");
    expect(liveVoiceErrorMessage({ response: { status: 409, data: { detail: "Disabled" } } })).toContain("disabled");
    expect(liveVoiceErrorMessage({ response: { status: 429, data: { detail: "Limit" } } })).toContain("rate limited");
    expect(liveVoiceErrorMessage(new Error("Microphone permission denied"))).toContain("permission");
  });

  it("appends final transcripts once", () => {
    const first = appendDedupedMessage([], { ...message("live-user-1", "Hello"), eventId: 1 });
    const second = appendDedupedMessage(first, { ...message("live-user-1", "Hello"), eventId: 1 });
    expect(first).toHaveLength(1);
    expect(second).toHaveLength(1);
  });
});
