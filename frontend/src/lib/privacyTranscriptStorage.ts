import type { PrivacyPreferences } from "../types/privacy";

export const COACH_PREFERENCES_KEY = "organicai_coach_preferences";
export const COACH_HISTORY_KEY = "organicai_coach_temp_history";
export const PRIVACY_PREFERENCES_SYNC_KEY = "organicai_privacy_preferences";
export const PRIVACY_PREFERENCES_EVENT = "organicai:privacy-preferences-updated";
export const AUTH_CLEARED_EVENT = "organicai:auth-cleared";

const KNOWN_VOICE_TRANSCRIPT_KEYS = [
  "organicai_live_voice_transcript_history",
  "organicai_live_voice_agent_transcript",
  "organicai_live_voice_user_transcript",
];

type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem" | "key" | "length">;

export function shouldPersistConversation(preferences: PrivacyPreferences | null, authenticated: boolean, loaded: boolean) {
  return Boolean(authenticated && loaded && preferences?.conversationPersistenceMode === "account-history");
}

export function removeVoiceTranscriptCaches(storage: StorageLike = window.localStorage) {
  const keys = new Set(KNOWN_VOICE_TRANSCRIPT_KEYS);
  for (let index = storage.length - 1; index >= 0; index -= 1) {
    const key = storage.key(index);
    if (key && key.includes("organicai_live_voice") && key.includes("transcript")) keys.add(key);
  }
  keys.forEach((key) => storage.removeItem(key));
}

export function clearAllTranscriptStorage(storage: StorageLike = window.localStorage) {
  storage.removeItem(COACH_HISTORY_KEY);
  removeVoiceTranscriptCaches(storage);
}

export function cleanupTranscriptStorage(preferences: Pick<PrivacyPreferences, "conversationPersistenceMode" | "voiceTranscriptPersistenceMode">, storage: StorageLike = window.localStorage) {
  if (preferences.conversationPersistenceMode === "ephemeral") {
    storage.removeItem(COACH_HISTORY_KEY);
  }
  if (preferences.voiceTranscriptPersistenceMode === "ephemeral") {
    removeVoiceTranscriptCaches(storage);
  }
}

export function publishPrivacyPreferences(preferences: PrivacyPreferences, storage: StorageLike = window.localStorage, target: Window = window) {
  storage.setItem(PRIVACY_PREFERENCES_SYNC_KEY, JSON.stringify(preferences));
  target.dispatchEvent(new CustomEvent(PRIVACY_PREFERENCES_EVENT, { detail: preferences }));
}

export function parsePrivacyPreferences(value: string | null): PrivacyPreferences | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value) as PrivacyPreferences;
    if (parsed.conversationPersistenceMode && parsed.voiceTranscriptPersistenceMode) return parsed;
  } catch {
    return null;
  }
  return null;
}
