import { createContext, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { sendCoachMessage } from "../api/chatApi";
import { extractApiError } from "../api/client";
import { getPrivacyPreferences } from "../api/privacyApi";
import { synthesizeSpeech, transcribeAudio } from "../api/voiceApi";
import type { ChatMessage } from "../types/chat";
import { useAppActions } from "../hooks/useAppActions";
import { useLiveVoice } from "../hooks/useLiveVoice";
import { getProfileFeedback, updateProfileFeedback } from "../api/profileApi";
import { generateRoadmap } from "../api/roadmapApi";
import { appendDedupedMessage } from "../lib/liveVoiceMapping";
import {
  AUTH_CLEARED_EVENT,
  COACH_HISTORY_KEY,
  COACH_PREFERENCES_KEY,
  PRIVACY_PREFERENCES_EVENT,
  PRIVACY_PREFERENCES_SYNC_KEY,
  cleanupTranscriptStorage,
  clearAllTranscriptStorage,
  parsePrivacyPreferences,
  shouldPersistConversation,
} from "../lib/privacyTranscriptStorage";
import { useAuth } from "./AuthContext";
import type { LiveVoiceContextValue } from "./LiveVoiceContext";
import type { PrivacyPreferences } from "../types/privacy";

export type CoachState =
  | "idle"
  | "disconnected"
  | "connecting"
  | "listening"
  | "transcribing"
  | "classifying"
  | "retrieving"
  | "thinking"
  | "speaking"
  | "muted"
  | "executing"
  | "error";

export type CoachPreferences = {
  isMuted: boolean;
  autoPlay: boolean;
  autoSendTranscript: boolean;
  storeTranscripts: boolean;
  storeAudio: boolean;
  voicePersonality: string;
  conversationMode: string;
  language: "en" | "ro" | "no";
  voiceConsent: boolean;
  voiceMode: "live" | "message";
};

type CoachValue = {
  state: CoachState;
  messages: ChatMessage[];
  conversationId: string | null;
  transcript: string;
  interimTranscript: string;
  audioUrl: string;
  preferences: CoachPreferences;
  selectedProfileNode: string | null;
  selectedRecommendationId: string | null;
  currentSources: NonNullable<ChatMessage["sourcesUsed"]>;
  currentConfidenceNote: string;
  currentEthicalNote: string;
  lastRecognizedCommand: string;
  error: string;
  isSending: boolean;
  canRetryLastMessage: boolean;
  recordingSeconds: number;
  liveVoice: LiveVoiceContextValue;
  setTranscript: (value: string) => void;
  setSelectedProfileNode: (value: string | null) => void;
  setSelectedRecommendationId: (value: string | null) => void;
  setPreferences: (next: Partial<CoachPreferences>) => void;
  sendTextMessage: (text: string, mode?: "text" | "voice") => Promise<void>;
  retryLastMessage: () => Promise<void>;
  startListening: () => Promise<void>;
  stopListening: () => void;
  startVoiceMessage: () => Promise<void>;
  cancelTranscript: () => void;
  stopSpeaking: () => void;
  replayLastAnswer: () => Promise<void>;
  executeCommand: (command: string) => Promise<void>;
  clearConversation: () => void;
};

export const CoachContext = createContext<CoachValue | undefined>(undefined);

type FailedCoachMessage = {
  text: string;
  mode: "text" | "voice";
};

export function coachRequestErrorMessage(error: unknown): string {
  const status = (error as { response?: { status?: number } }).response?.status;
  const transportCode = (error as { code?: string }).code;
  const { code } = extractApiError(error);

  if (status === 401 || code === "UNAUTHENTICATED" || code === "INVALID_TOKEN") {
    return "Your session has expired. Please sign in again, then retry your message.";
  }
  if (status === 429 || code === "RATE_LIMITED") {
    return "The AI Coach is receiving too many requests. Please wait a moment, then retry your message.";
  }
  if (status === 422 || code === "VALIDATION_ERROR") {
    return "That message could not be sent as written. Shorten it or remove unsupported details, then retry.";
  }
  if (status === 503 || code === "PROVIDER_UNAVAILABLE" || code === "RETRIEVAL_UNAVAILABLE") {
    return "The AI service is temporarily unavailable. Your message is preserved—retry in a moment.";
  }
  if (transportCode === "ECONNABORTED" || code === "TIMEOUT") {
    return "The AI Coach request timed out. Your message is preserved—retry when your connection is ready.";
  }
  if (!status || transportCode === "ERR_NETWORK") {
    return "OrganicAI Compass cannot reach the AI Coach service. Check your connection and retry.";
  }
  return "The AI Coach could not complete that request. Your message is preserved—please retry.";
}

const initialPreferences: CoachPreferences = {
  isMuted: false,
  autoPlay: false,
  autoSendTranscript: false,
  storeTranscripts: false,
  storeAudio: false,
  voicePersonality: "Calm Guide",
  conversationMode: "Explain simply",
  language: "en",
  voiceConsent: false,
  voiceMode: "live",
};

const welcome: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: "Hi, I'm OrganicAI Coach. You can use text, live voice, or voice message fallback, and every answer remains available as captions.",
  createdAt: new Date().toISOString(),
  groundingStatus: "general",
};

const makeMessage = (role: "user" | "assistant", content: string, mode: "text" | "voice" = "text"): ChatMessage => ({
  id: `${role}-${Date.now()}-${Math.random()}`,
  role,
  content,
  createdAt: new Date().toISOString(),
  inputMode: mode,
});

function normalizeCommand(text: string) {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z\s]/g, "")
    .trim();
}

function liveState(liveVoice: LiveVoiceContextValue): CoachState {
  if (liveVoice.connectionStatus === "requesting-permission" || liveVoice.connectionStatus === "requesting-token" || liveVoice.connectionStatus === "connecting") return "connecting";
  if (liveVoice.connectionStatus === "error") return "error";
  if (liveVoice.turnMode === "muted") return "muted";
  if (liveVoice.turnMode === "speaking") return "speaking";
  if (liveVoice.turnMode === "thinking") return "thinking";
  if (liveVoice.turnMode === "listening") return "listening";
  return "idle";
}

export function CoachProvider({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const actions = useAppActions();
  const liveVoice = useLiveVoice();
  const location = useLocation();
  const [legacyState, setLegacyState] = useState<CoachState>("idle");
  const [messages, setMessages] = useState<ChatMessage[]>([welcome]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [selectedProfileNode, setSelectedProfileNode] = useState<string | null>(null);
  const [selectedRecommendationId, setSelectedRecommendationId] = useState<string | null>(null);
  const [preferences, setPreferencesState] = useState<CoachPreferences>(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(COACH_PREFERENCES_KEY) || "{}");
      return { ...initialPreferences, ...stored, storeTranscripts: false, storeAudio: false };
    } catch {
      return initialPreferences;
    }
  });
  const [privacyLoaded, setPrivacyLoaded] = useState(false);
  const [lastRecognizedCommand, setLastRecognizedCommand] = useState("");
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [lastFailedMessage, setLastFailedMessage] = useState<FailedCoachMessage | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [liveSessionSeconds, setLiveSessionSeconds] = useState(0);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<BlobPart[]>([]);
  const stream = useRef<MediaStream | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const sendingRef = useRef(false);

  const state = preferences.voiceMode === "live" ? liveState(liveVoice) : legacyState;
  const exposedError = preferences.voiceMode === "live" ? liveVoice.liveError || error : error;

  useEffect(() => {
    localStorage.setItem(COACH_PREFERENCES_KEY, JSON.stringify({ ...preferences, storeTranscripts: false, storeAudio: false }));
  }, [preferences]);

  useEffect(() => {
    const allowed = shouldPersistConversation(
      {
        conversationPersistenceMode: preferences.storeTranscripts ? "account-history" : "ephemeral",
        voiceTranscriptPersistenceMode: preferences.storeAudio ? "account-history" : "ephemeral",
      } as PrivacyPreferences,
      auth.isAuthenticated,
      privacyLoaded,
    );
    if (allowed) localStorage.setItem(COACH_HISTORY_KEY, JSON.stringify(messages));
    else localStorage.removeItem(COACH_HISTORY_KEY);
  }, [auth.isAuthenticated, messages, preferences.storeAudio, preferences.storeTranscripts, privacyLoaded]);

  const applyPrivacyPreferences = useCallback(
    (next: PrivacyPreferences, loadHistory: boolean) => {
      const storeTranscripts = shouldPersistConversation(next, auth.isAuthenticated, true);
      cleanupTranscriptStorage(next);
      setPrivacyLoaded(true);
      setPreferencesState((current) => ({ ...current, storeTranscripts, storeAudio: false }));
      if (!storeTranscripts) {
        setMessages([welcome]);
        setConversationId(null);
        setTranscript("");
        setLastFailedMessage(null);
        return;
      }
      if (loadHistory) {
        try {
          setMessages(JSON.parse(localStorage.getItem(COACH_HISTORY_KEY) || "null") || [welcome]);
        } catch {
          setMessages([welcome]);
        }
      }
    },
    [auth.isAuthenticated],
  );

  useEffect(() => {
    let cancelled = false;
    if (!auth.isAuthenticated) {
      setPrivacyLoaded(false);
      clearAllTranscriptStorage();
      setPreferencesState((current) => ({ ...current, storeTranscripts: false, storeAudio: false }));
      setMessages([welcome]);
      setConversationId(null);
      setTranscript("");
      setLastFailedMessage(null);
      return;
    }
    setPrivacyLoaded(false);
    setPreferencesState((current) => ({ ...current, storeTranscripts: false, storeAudio: false }));
    void getPrivacyPreferences()
      .then((next) => {
        if (!cancelled) applyPrivacyPreferences(next, true);
      })
      .catch(() => {
        if (!cancelled) {
          clearAllTranscriptStorage();
          setPrivacyLoaded(false);
          setPreferencesState((current) => ({ ...current, storeTranscripts: false, storeAudio: false }));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [applyPrivacyPreferences, auth.isAuthenticated, auth.user?.id]);

  useEffect(() => {
    const onAuthCleared = () => {
      setPrivacyLoaded(false);
      clearAllTranscriptStorage();
      setPreferencesState((current) => ({ ...current, storeTranscripts: false, storeAudio: false }));
      setMessages([welcome]);
      setConversationId(null);
      setTranscript("");
      setLastFailedMessage(null);
    };
    const onPrivacyUpdate = (event: Event) => {
      const next = (event as CustomEvent<PrivacyPreferences>).detail;
      if (next) applyPrivacyPreferences(next, false);
    };
    const onStorage = (event: StorageEvent) => {
      if (event.key !== PRIVACY_PREFERENCES_SYNC_KEY) return;
      const next = parsePrivacyPreferences(event.newValue);
      if (next) applyPrivacyPreferences(next, false);
    };
    window.addEventListener(AUTH_CLEARED_EVENT, onAuthCleared);
    window.addEventListener(PRIVACY_PREFERENCES_EVENT, onPrivacyUpdate);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(AUTH_CLEARED_EVENT, onAuthCleared);
      window.removeEventListener(PRIVACY_PREFERENCES_EVENT, onPrivacyUpdate);
      window.removeEventListener("storage", onStorage);
    };
  }, [applyPrivacyPreferences]);

  useEffect(() => {
    if (legacyState !== "listening") return;
    const timer = window.setInterval(() => setRecordingSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [legacyState]);

  useEffect(() => {
    if (!liveVoice.isConnected) {
      setLiveSessionSeconds(0);
      return;
    }
    const timer = window.setInterval(() => setLiveSessionSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [liveVoice.isConnected]);

  useEffect(() => {
    return liveVoice.registerMessageHandler((message) => {
      if (message.appConversationId) setConversationId(message.appConversationId);
      setMessages((current) => appendDedupedMessage(current, message));
    });
  }, [liveVoice.registerMessageHandler]);

  useEffect(() => {
    liveVoice.setOrganicContext({
      activeProfileId: actions.activeProfileId,
      appConversationId: conversationId,
      route: location.pathname,
      selectedProfileNode,
      selectedRecommendationId,
      language: preferences.language,
      voicePersonality: preferences.voicePersonality,
      conversationMode: preferences.conversationMode,
      voiceConsent: preferences.voiceConsent,
      theme: document.documentElement.dataset.theme || "light",
    });
  }, [
    actions.activeProfileId,
    conversationId,
    location.pathname,
    preferences.conversationMode,
    preferences.language,
    preferences.voiceConsent,
    preferences.voicePersonality,
    selectedProfileNode,
    selectedRecommendationId,
    liveVoice.setOrganicContext,
  ]);

  const stopSpeaking = useCallback(() => {
    audio.current?.pause();
    if (audio.current) audio.current.currentTime = 0;
    if (!liveVoice.isConnected) setLegacyState("idle");
  }, [liveVoice.isConnected]);

  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if (event.key === "Escape") stopSpeaking();
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, [stopSpeaking]);

  useEffect(() => {
    return () => {
      stream.current?.getTracks().forEach((track) => track.stop());
      audio.current?.pause();
    };
  }, []);

  const setPreferences = (next: Partial<CoachPreferences>) => {
    const { storeAudio: _storeAudio, storeTranscripts: _storeTranscripts, ...safeNext } = next;
    setPreferencesState((current) => ({ ...current, ...safeNext, storeAudio: false }));
  };

  async function play(text: string) {
    if (preferences.isMuted) return;
    try {
      const result = await synthesizeSpeech(text);
      if (!result.audioUrl) throw new Error("No audio URL returned.");
      setAudioUrl(result.audioUrl);
      const player = new Audio(result.audioUrl);
      audio.current = player;
      player.onended = () => setLegacyState("idle");
      setLegacyState("speaking");
      await player.play();
    } catch {
      setError("Voice playback is unavailable. Your text answer is still ready.");
      setLegacyState("idle");
    }
  }

  async function executeCommand(raw: string) {
    setLegacyState("executing");
    const result = actions.executeVoiceCommand(raw);
    if (result.recognized) {
      const confirmation = `Voice command recognized: ${result.label}. ${result.message || ""}`;
      setLastRecognizedCommand(result.label || raw);
      setMessages((current) => [...current, makeMessage("assistant", confirmation)]);
      if (preferences.autoPlay && !preferences.isMuted) await play(result.message || confirmation);
      else setLegacyState("idle");
    } else {
      setLegacyState("idle");
    }
  }

  async function sendTextMessage(text: string, mode: "text" | "voice" = "text", retry = false) {
    if (!text.trim() || sendingRef.current) return;
    if (preferences.voiceMode === "live" && liveVoice.isConnected) {
      liveVoice.sendLiveTextMessage(text);
      setTranscript("");
      return;
    }

    const normalized = normalizeCommand(text);
    if (["stop speaking", "stop voice", "opreste vocea", "taci"].includes(normalized)) {
      setMessages((current) => [...current, makeMessage("user", text, mode), makeMessage("assistant", "Voice command recognized: Stop Speaking.")]);
      setLastRecognizedCommand("Stop Speaking");
      stopSpeaking();
      return;
    }
    if (["repeat answer", "repeat that", "repeta raspunsul"].includes(normalized)) {
      setLastRecognizedCommand("Repeat Answer");
      await replayLastAnswer();
      return;
    }
    setError("");
    const localCommand = actions.executeVoiceCommand(text);
    if (localCommand.recognized) {
      setMessages((current) => [...current, makeMessage("user", text, mode)]);
      await executeCommand(text);
      setTranscript("");
      return;
    }

    if (!retry) setMessages((current) => [...current, makeMessage("user", text, mode)]);
    setTranscript("");
    setLegacyState("classifying");
    sendingRef.current = true;
    setIsSending(true);
    const retrievalTimer = window.setTimeout(() => setLegacyState("retrieving"), 180);
    try {
      const response = await sendCoachMessage({
        message: text,
        profileId: actions.activeProfileId,
        conversationId,
        mode,
        voicePersonality: preferences.voicePersonality,
        conversationMode: preferences.conversationMode,
        route: location.pathname,
        selectedProfileNode,
        language: preferences.language,
        clientContext: {
          theme: document.documentElement.dataset.theme,
          selected_recommendation_id: selectedRecommendationId,
        },
      });
      window.clearTimeout(retrievalTimer);
      let answer = response.answer;
      if (response.executedCommand) {
        setLastRecognizedCommand(response.executedCommand.name);
        setLegacyState("executing");
        const name = response.executedCommand.name;
        if (name === "confirm_selected_node" && selectedProfileNode) {
          const saved = await getProfileFeedback(actions.activeProfileId);
          await updateProfileFeedback(actions.activeProfileId, { ...saved, confirmed_nodes: [...new Set([...saved.confirmed_nodes, selectedProfileNode])] });
          answer = `Confirmed the ${selectedProfileNode} interpretation. You remain in control of this profile.`;
        } else if (name === "add_note_to_selected_node" && selectedProfileNode) {
          const saved = await getProfileFeedback(actions.activeProfileId);
          const note = String(response.executedCommand.parameters.note || "");
          await updateProfileFeedback(actions.activeProfileId, { ...saved, user_notes: { ...saved.user_notes, [selectedProfileNode]: note } });
          answer = `I added that note to ${selectedProfileNode}.`;
        } else if (name === "open_selected_learning_path") actions.executeVoiceCommand("open learning paths");
        else if (name === "regenerate_roadmap") {
          await generateRoadmap(actions.activeProfileId);
          answer = "Your roadmap was regenerated using your current profile.";
        }
      } else setLegacyState("thinking");

      const assistant: ChatMessage = {
        ...makeMessage("assistant", answer),
        sourcesUsed: response.sourcesUsed,
        confidenceNote: response.confidenceNote,
        ethicalNote: response.ethicalNote,
        intent: response.intent,
        profileSignals: response.profileSignals,
        groundingStatus: response.groundingStatus,
        retrievalStatus: response.retrievalStatus,
        timing: response.timing,
        ragRunId: response.ragRunId,
        contextQuality: response.contextQuality,
      };
      setConversationId(response.conversationId || conversationId);
      setMessages((current) => [...current, assistant]);
      setLastFailedMessage(null);
      if (preferences.autoPlay && !preferences.isMuted) await play(answer);
      else setLegacyState("idle");
    } catch (requestError) {
      window.clearTimeout(retrievalTimer);
      setLastFailedMessage({ text, mode });
      setError(coachRequestErrorMessage(requestError));
      setLegacyState("error");
    } finally {
      window.clearTimeout(retrievalTimer);
      sendingRef.current = false;
      setIsSending(false);
    }
  }

  async function retryLastMessage() {
    if (!lastFailedMessage || sendingRef.current) return;
    setError("");
    await sendTextMessage(lastFailedMessage.text, lastFailedMessage.mode, true);
  }

  async function startVoiceMessage() {
    if (!preferences.voiceConsent) {
      setError("Voice consent is required before recording.");
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("No microphone is available. You can still use text chat.");
      return;
    }
    try {
      const media = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.current = media;
      chunks.current = [];
      const instance = new MediaRecorder(media, MediaRecorder.isTypeSupported("audio/webm") ? { mimeType: "audio/webm" } : undefined);
      recorder.current = instance;
      instance.ondataavailable = (event) => {
        if (event.data.size) chunks.current.push(event.data);
      };
      instance.onstop = async () => {
        media.getTracks().forEach((track) => track.stop());
        setLegacyState("transcribing");
        try {
          const result = await transcribeAudio(new Blob(chunks.current, { type: instance.mimeType || "audio/webm" }));
          setTranscript(result.transcript);
          setLegacyState("idle");
          if (preferences.autoSendTranscript && result.transcript.trim()) await sendTextMessage(result.transcript, "voice");
        } catch {
          setError("We could not transcribe that voice message. You can try again or type your message.");
          setLegacyState("error");
        }
      };
      setRecordingSeconds(0);
      instance.start();
      setLegacyState("listening");
    } catch {
      setError("Microphone permission was denied. You can continue with text.");
      setLegacyState("error");
    }
  }

  async function startListening() {
    if (preferences.voiceMode === "live") await liveVoice.startLiveConversation();
    else await startVoiceMessage();
  }

  function stopListening() {
    if (preferences.voiceMode === "live") {
      liveVoice.setMicrophoneMuted(true);
      return;
    }
    if (recorder.current?.state === "recording") recorder.current.stop();
  }

  async function replayLastAnswer() {
    const latest = [...messages].reverse().find((item) => item.role === "assistant");
    if (latest) await play(latest.content);
  }

  function clearConversation() {
    stopSpeaking();
    setMessages([welcome]);
    setConversationId(null);
    setTranscript("");
    setError("");
    setLastFailedMessage(null);
    localStorage.removeItem(COACH_HISTORY_KEY);
  }

  const latest = [...messages].reverse().find((item) => item.role === "assistant");
  const value = useMemo<CoachValue>(
    () => ({
      state,
      messages,
      conversationId,
      transcript,
      interimTranscript: preferences.voiceMode === "live" ? liveVoice.interimUserTranscript : "",
      audioUrl,
      preferences,
      selectedProfileNode,
      selectedRecommendationId,
      currentSources: latest?.sourcesUsed || [],
      currentConfidenceNote: latest?.confidenceNote || "",
      currentEthicalNote: latest?.ethicalNote || "",
      lastRecognizedCommand,
      error: exposedError,
      isSending,
      canRetryLastMessage: Boolean(lastFailedMessage),
      recordingSeconds: preferences.voiceMode === "live" ? liveSessionSeconds : recordingSeconds,
      liveVoice,
      setTranscript,
      setSelectedProfileNode,
      setSelectedRecommendationId,
      setPreferences,
      sendTextMessage,
      retryLastMessage,
      startListening,
      stopListening,
      startVoiceMessage,
      cancelTranscript: () => setTranscript(""),
      stopSpeaking,
      replayLastAnswer,
      executeCommand,
      clearConversation,
    }),
    [
      state,
      messages,
      conversationId,
      transcript,
      preferences,
      liveVoice,
      audioUrl,
      selectedProfileNode,
      selectedRecommendationId,
      latest,
      lastRecognizedCommand,
      exposedError,
      liveSessionSeconds,
      recordingSeconds,
      isSending,
      lastFailedMessage,
      stopSpeaking,
      actions.activeProfileId,
      location.pathname,
    ],
  );

  return <CoachContext.Provider value={value}>{children}</CoachContext.Provider>;
}
