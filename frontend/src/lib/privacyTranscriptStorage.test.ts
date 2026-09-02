import { describe, expect, it } from "vitest";
import {
  COACH_HISTORY_KEY,
  cleanupTranscriptStorage,
  clearAllTranscriptStorage,
  parsePrivacyPreferences,
  removeVoiceTranscriptCaches,
  shouldPersistConversation,
} from "./privacyTranscriptStorage";
import type { PrivacyPreferences } from "../types/privacy";

class MemoryStorage {
  private data = new Map<string, string>();

  get length() {
    return this.data.size;
  }

  getItem(key: string) {
    return this.data.get(key) ?? null;
  }

  setItem(key: string, value: string) {
    this.data.set(key, value);
  }

  removeItem(key: string) {
    this.data.delete(key);
  }

  key(index: number) {
    return Array.from(this.data.keys())[index] ?? null;
  }
}

const prefs = (mode: "account-history" | "ephemeral", voiceMode: "account-history" | "ephemeral" = mode): PrivacyPreferences => ({
  conversationPersistenceMode: mode,
  voiceTranscriptPersistenceMode: voiceMode,
  voiceAudioStorageEnabled: false,
  productAnalyticsEnabled: false,
  researchParticipationEnabled: false,
  personalizationEnabled: true,
  serviceEmailEnabled: true,
  marketingEmailEnabled: false,
  updatedAt: "2026-07-29T00:00:00",
});

describe("privacy transcript storage", () => {
  it("defaults to privacy-safe persistence before server preferences load", () => {
    expect(shouldPersistConversation(null, true, false)).toBe(false);
    expect(shouldPersistConversation(prefs("account-history"), false, true)).toBe(false);
  });

  it("allows local history only for authenticated account-history mode", () => {
    expect(shouldPersistConversation(prefs("account-history"), true, true)).toBe(true);
    expect(shouldPersistConversation(prefs("ephemeral"), true, true)).toBe(false);
  });

  it("removes text history in ephemeral mode", () => {
    const storage = new MemoryStorage();
    storage.setItem(COACH_HISTORY_KEY, "[{}]");
    cleanupTranscriptStorage(prefs("ephemeral"), storage);
    expect(storage.getItem(COACH_HISTORY_KEY)).toBeNull();
  });

  it("removes known and discovered voice transcript caches", () => {
    const storage = new MemoryStorage();
    storage.setItem("organicai_live_voice_transcript_history", "a");
    storage.setItem("organicai_live_voice_custom_transcript_cache", "b");
    storage.setItem("organicai_live_voice_audio_cache", "c");
    removeVoiceTranscriptCaches(storage);
    expect(storage.getItem("organicai_live_voice_transcript_history")).toBeNull();
    expect(storage.getItem("organicai_live_voice_custom_transcript_cache")).toBeNull();
    expect(storage.getItem("organicai_live_voice_audio_cache")).toBe("c");
  });

  it("clears all transcript storage during logout cleanup", () => {
    const storage = new MemoryStorage();
    storage.setItem(COACH_HISTORY_KEY, "[{}]");
    storage.setItem("organicai_live_voice_agent_transcript", "voice");
    clearAllTranscriptStorage(storage);
    expect(storage.getItem(COACH_HISTORY_KEY)).toBeNull();
    expect(storage.getItem("organicai_live_voice_agent_transcript")).toBeNull();
  });

  it("parses cross-tab privacy preference payloads", () => {
    expect(parsePrivacyPreferences(JSON.stringify(prefs("ephemeral")))?.conversationPersistenceMode).toBe("ephemeral");
    expect(parsePrivacyPreferences("not-json")).toBeNull();
  });
});
