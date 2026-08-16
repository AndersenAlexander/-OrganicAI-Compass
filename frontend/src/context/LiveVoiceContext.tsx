import {
  ConversationProvider,
  useConversationClientTool,
  useConversationControls,
  useConversationInput,
  useConversationMode,
  useConversationStatus,
  type Callbacks,
} from "@elevenlabs/react";
import { createContext, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { createLiveConversationToken, getLatestLiveVoiceTurn, getLiveVoiceStatus } from "../api/voiceApi";
import { extractApiError, getLastRequestId } from "../api/client";
import { getProfileFeedback, updateProfileFeedback } from "../api/profileApi";
import { generateRoadmap } from "../api/roadmapApi";
import { useAppActions } from "../hooks/useAppActions";
import { useAuth } from "./AuthContext";
import type { ChatMessage } from "../types/chat";
import type {
  LiveVoiceConnectionStatus,
  LiveVoiceOrganicContext,
  LiveVoiceStatus,
  LiveVoiceTurnMode,
} from "../types/liveVoice";
import { appendDedupedMessage, liveVoiceAvailability, liveVoiceErrorMessage, mapLiveTurnMode } from "../lib/liveVoiceMapping";

type ElevenLabsMessagePayload = Parameters<NonNullable<Callbacks["onMessage"]>>[0];
type LiveVoiceMessageHandler = (message: ChatMessage & { appConversationId?: string | null; eventId?: string | number | null }) => void;

declare global {
  interface Window {
    __organicaiLiveVoiceTest?: {
      emitUser: (message: string) => void;
      emitAgent: (message: string) => void;
      setTurnMode: (mode: LiveVoiceTurnMode) => void;
    };
  }
}

export type LiveVoiceContextValue = {
  providerStatus: LiveVoiceStatus | null;
  connectionStatus: LiveVoiceConnectionStatus;
  turnMode: LiveVoiceTurnMode;
  isConnected: boolean;
  isListening: boolean;
  isSpeaking: boolean;
  isMuted: boolean;
  conversationId: string | null;
  interimUserTranscript: string;
  liveAgentTranscript: string;
  liveError: string;
  liveErrorCode: string;
  lastRequestId: string;
  inputLevel: number;
  outputLevel: number;
  startLiveConversation: () => Promise<void>;
  endLiveConversation: () => Promise<void>;
  setMicrophoneMuted: (muted: boolean) => void;
  sendLiveTextMessage: (text: string) => void;
  notifyUserActivity: () => void;
  sendPageContext: () => void;
  setOrganicContext: (context: LiveVoiceOrganicContext) => void;
  registerMessageHandler: (handler: LiveVoiceMessageHandler) => () => void;
  refreshStatus: () => Promise<void>;
};

const defaultOrganicContext: LiveVoiceOrganicContext = {
  activeProfileId: "",
  appConversationId: null,
  route: "/",
  selectedProfileNode: null,
  selectedRecommendationId: null,
  language: "en",
  voicePersonality: "Calm Guide",
  conversationMode: "Explain simply",
  voiceConsent: false,
};

export const LiveVoiceContext = createContext<LiveVoiceContextValue | undefined>(undefined);

function jsonResult(success: boolean, message: string) {
  return JSON.stringify({ success, message });
}

function safeString(value: unknown, maxLength = 160) {
  return typeof value === "string" && value.length <= maxLength ? value : "";
}

function makeLiveMessage(payload: ElevenLabsMessagePayload): ChatMessage & { eventId?: string | number | null } {
  const role = payload.role === "user" || payload.source === "user" ? "user" : "assistant";
  return {
    id: `live-${role}-${payload.event_id ?? `${Date.now()}-${payload.message.slice(0, 24)}`}`,
    role,
    content: payload.message,
    createdAt: new Date().toISOString(),
    inputMode: role === "user" ? "voice" : "voice",
    eventId: payload.event_id,
  };
}

function testAdapterEnabled() {
  if (typeof window === "undefined") return false;
  const localHost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  return (import.meta.env.DEV || localHost) && window.localStorage.getItem("organicai_live_voice_test_adapter") === "true";
}

function LiveVoiceBridge({ children }: { children: ReactNode }) {
  const controls = useConversationControls();
  const status = useConversationStatus();
  const mode = useConversationMode();
  const input = useConversationInput();
  const auth = useAuth();
  const actions = useAppActions();
  const navigate = useNavigate();
  const location = useLocation();

  const [providerStatus, setProviderStatus] = useState<LiveVoiceStatus | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<LiveVoiceConnectionStatus>("disconnected");
  const [waitingForAgent, setWaitingForAgent] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [interimUserTranscript, setInterimUserTranscript] = useState("");
  const [liveAgentTranscript, setLiveAgentTranscript] = useState("");
  const [liveError, setLiveError] = useState("");
  const [liveErrorCode, setLiveErrorCode] = useState("");
  const [lastRequestId, setLastRequestId] = useState("");
  const [inputLevel, setInputLevel] = useState(0);
  const [outputLevel, setOutputLevel] = useState(0);
  const [organicContext, setOrganicContextState] = useState<LiveVoiceOrganicContext>(defaultOrganicContext);
  const [testTurnMode, setTestTurnMode] = useState<LiveVoiceTurnMode | null>(null);
  const [testMuted, setTestMuted] = useState(false);

  const startGuard = useRef(false);
  const userEnded = useRef(false);
  const latestTokenConversationId = useRef<string | null>(null);
  const organicContextRef = useRef(organicContext);
  const handlers = useRef(new Set<LiveVoiceMessageHandler>());
  const emittedMessages = useRef<ChatMessage[]>([]);

  const adapterConnected = testAdapterEnabled() && testTurnMode !== null;
  const effectiveConnectionStatus: LiveVoiceConnectionStatus = adapterConnected ? "connected" : connectionStatus;
  const effectiveMuted = adapterConnected ? testMuted : input.isMuted;
  const turnMode =
    effectiveMuted && effectiveConnectionStatus === "connected"
      ? "muted"
      : testTurnMode || mapLiveTurnMode({
          connectionStatus: effectiveConnectionStatus,
          sdkMode: mode.mode,
          isMuted: effectiveMuted,
          waitingForAgent,
        });

  const emitMessage = useCallback((message: ChatMessage & { appConversationId?: string | null; eventId?: string | number | null }) => {
    const next = appendDedupedMessage(emittedMessages.current, message);
    if (next === emittedMessages.current) return;
    emittedMessages.current = next;
    handlers.current.forEach((handler) => handler(message));
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      const next = await getLiveVoiceStatus();
      setProviderStatus(next);
      setLastRequestId(getLastRequestId());
      setLiveErrorCode("");
      setConnectionStatus((current) => (current === "connected" || current === "connecting" ? current : liveVoiceAvailability(next)));
    } catch (error) {
      const apiError = extractApiError(error);
      setConnectionStatus("error");
      setLiveErrorCode(apiError.code);
      setLastRequestId(apiError.requestId);
      setLiveError("Live voice status could not be loaded. Text chat remains available.");
    }
  }, []);

  useEffect(() => {
    void refreshStatus();
  }, [refreshStatus]);

  useEffect(() => {
    organicContextRef.current = organicContext;
  }, [organicContext]);

  useEffect(() => {
    if (testAdapterEnabled() && testTurnMode) return;
    if (status.status === "connected") {
      setConnectionStatus("connected");
      setLiveError("");
      setLiveErrorCode("");
      return;
    }
    if (status.status === "connecting") {
      setConnectionStatus((current) => (current.startsWith("requesting") ? current : "connecting"));
      return;
    }
    if (status.status === "error") {
      setConnectionStatus("error");
      setLiveErrorCode("LIVE_CONNECTION_ERROR");
      setLiveError(liveVoiceErrorMessage(status.message || "Live voice connection failed."));
      return;
    }
    if (status.status === "disconnected" && connectionStatus !== "disabled" && connectionStatus !== "unconfigured") {
      setConnectionStatus(providerStatus ? liveVoiceAvailability(providerStatus) : "disconnected");
      setWaitingForAgent(false);
      if (!userEnded.current && conversationId) {
        setLiveError("The live voice session ended. You can retry or continue with text.");
      }
    }
  }, [status.status, status.message, providerStatus, connectionStatus, conversationId, testTurnMode]);

  useEffect(() => {
    if (connectionStatus !== "connected") return;
    const timer = window.setInterval(() => {
      setInputLevel(controls.getInputVolume());
      setOutputLevel(controls.getOutputVolume());
    }, 250);
    return () => window.clearInterval(timer);
  }, [connectionStatus, controls]);

  const sendPageContext = useCallback(() => {
    if (connectionStatus !== "connected") return;
    const context = organicContextRef.current;
    controls.sendContextualUpdate(
      [
        "OrganicAI application context updated:",
        `route=${location.pathname}`,
        `profile_id=${context.activeProfileId}`,
        `selected_profile_node=${context.selectedProfileNode || ""}`,
        `selected_recommendation_id=${context.selectedRecommendationId || ""}`,
        `language=${context.language}`,
        `conversation_mode=${context.conversationMode}`,
        `voice_personality=${context.voicePersonality}`,
        "Use this context for the next response. Do not acknowledge this update unless relevant.",
      ].join("\n"),
      { contextId: "organicai-page-context" },
    );
  }, [connectionStatus, controls, location.pathname]);

  useEffect(() => {
    if (connectionStatus !== "connected") return;
    const timer = window.setTimeout(sendPageContext, 450);
    return () => window.clearTimeout(timer);
  }, [connectionStatus, organicContext, location.pathname, sendPageContext]);

  const endLiveConversation = useCallback(async () => {
    userEnded.current = true;
    setConnectionStatus("disconnecting");
    setInterimUserTranscript("");
    setLiveAgentTranscript("");
    setWaitingForAgent(false);
    setTestTurnMode(null);
    setTestMuted(false);
    try {
      controls.endSession();
    } finally {
      setConversationId(null);
      latestTokenConversationId.current = null;
      setConnectionStatus(providerStatus ? liveVoiceAvailability(providerStatus) : "disconnected");
    }
  }, [controls, providerStatus]);

  useEffect(() => {
    if (!auth.isAuthenticated && conversationId) void endLiveConversation();
  }, [auth.isAuthenticated, conversationId, endLiveConversation]);

  useEffect(() => {
    const cleanup = () => {
      void endLiveConversation();
    };
    window.addEventListener("organicai:auth-cleared", cleanup);
    return () => window.removeEventListener("organicai:auth-cleared", cleanup);
  }, [endLiveConversation]);

  useEffect(() => {
    const cleanup = () => {
      if (conversationId) controls.endSession();
    };
    window.addEventListener("pagehide", cleanup);
    window.addEventListener("beforeunload", cleanup);
    return () => {
      window.removeEventListener("pagehide", cleanup);
      window.removeEventListener("beforeunload", cleanup);
      cleanup();
    };
  }, [conversationId, controls]);

  const handleFinalMessage = useCallback(
    async (payload: ElevenLabsMessagePayload) => {
      if (!payload.message?.trim()) return;
      const message = makeLiveMessage(payload);
      if (message.role === "user") {
        setInterimUserTranscript(payload.message);
        setWaitingForAgent(true);
        emitMessage(message);
        window.setTimeout(() => setInterimUserTranscript(""), 1200);
        return;
      }
      setWaitingForAgent(false);
      setLiveAgentTranscript(payload.message);
      const activeConversationId = conversationId || latestTokenConversationId.current;
      if (!activeConversationId) {
        emitMessage(message);
        return;
      }
      try {
        const latest = await getLatestLiveVoiceTurn(activeConversationId);
        emitMessage({
          ...message,
          id: latest.messageId || message.id,
          content: latest.answer || message.content,
          sourcesUsed: latest.sourcesUsed,
          confidenceNote: latest.confidenceNote,
          ethicalNote: latest.ethicalNote,
          groundingStatus: latest.groundingStatus,
          profileSignals: latest.profileSignals,
          retrievalStatus: latest.retrievalStatus,
          timing: latest.timing,
          ragRunId: latest.ragRunId || undefined,
          contextQuality: latest.contextQuality,
          appConversationId: latest.appConversationId,
        });
      } catch {
        emitMessage(message);
      }
    },
    [conversationId, emitMessage],
  );

  useEffect(() => {
    if (!testAdapterEnabled()) return;
    window.__organicaiLiveVoiceTest = {
      emitUser: (message) => void handleFinalMessage({ role: "user", source: "user", message, event_id: Date.now() }),
      emitAgent: (message) => void handleFinalMessage({ role: "agent", source: "ai", message, event_id: Date.now() }),
      setTurnMode: setTestTurnMode,
    };
    return () => {
      delete window.__organicaiLiveVoiceTest;
    };
  }, [handleFinalMessage]);

  const startLiveConversation = useCallback(async () => {
    if (startGuard.current || ["requesting-permission", "requesting-token", "connecting", "connected", "disconnecting"].includes(connectionStatus)) return;
    startGuard.current = true;
    userEnded.current = false;
    setLiveError("");
    try {
      const currentStatus = providerStatus || (await getLiveVoiceStatus());
      setProviderStatus(currentStatus);
      if (!currentStatus.liveVoiceEnabled) {
        setConnectionStatus("disabled");
        setLiveErrorCode("VOICE_DISABLED");
        setLiveError("Live voice conversation is disabled. You can continue with text or voice message.");
        return;
      }
      if (!currentStatus.liveVoiceConfigured) {
        setConnectionStatus("unconfigured");
        setLiveErrorCode("VOICE_AGENT_NOT_CONFIGURED");
        setLiveError("ElevenLabs live voice is not configured. You can continue with text or voice message.");
        return;
      }
      if (!auth.isAuthenticated || !auth.user) {
        setConnectionStatus("error");
        setLiveErrorCode("AUTH_REQUIRED");
        setLiveError("Authentication is required before starting live voice conversation.");
        return;
      }
      if (!organicContextRef.current.voiceConsent) {
        setConnectionStatus("disconnected");
        setLiveErrorCode("VOICE_CONSENT_REQUIRED");
        setLiveError("Live voice consent is required before starting the microphone.");
        return;
      }
      if (!navigator.mediaDevices?.getUserMedia) {
        setConnectionStatus("error");
        setLiveErrorCode("MICROPHONE_UNSUPPORTED");
        setLiveError("This browser does not support live microphone access. Use text chat or voice message.");
        return;
      }

      setConnectionStatus("requesting-permission");
      const permissionStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      permissionStream.getTracks().forEach((track) => track.stop());

      const context = organicContextRef.current;
      setConnectionStatus("requesting-token");
      const token = await createLiveConversationToken({
        profileId: context.activeProfileId,
        appConversationId: context.appConversationId,
        route: context.route,
        selectedProfileNode: context.selectedProfileNode,
        selectedRecommendationId: context.selectedRecommendationId,
        language: context.language,
        voicePersonality: context.voicePersonality,
        conversationMode: context.conversationMode,
        clientContext: { theme: context.theme || document.documentElement.dataset.theme || "light" },
      });
      latestTokenConversationId.current = token.conversationId;
      setLastRequestId(getLastRequestId());
      setConversationId(token.conversationId);
      if (testAdapterEnabled()) {
        setConnectionStatus("connected");
        setTestTurnMode("listening");
        setTestMuted(false);
        return;
      }
      setConnectionStatus("connecting");
      const sessionOptions: NonNullable<Parameters<typeof controls.startSession>[0]> = {
        conversationToken: token.token,
        connectionType: "webrtc",
        userId: auth.user.id,
        environment: token.environment,
        customLlmExtraBody: {
          organicai_user_id: auth.user.id,
          profile_id: context.activeProfileId,
          app_conversation_id: context.appConversationId,
          elevenlabs_conversation_id: token.conversationId,
          route: context.route,
          selected_profile_node: context.selectedProfileNode,
          selected_recommendation_id: context.selectedRecommendationId,
          language: context.language,
          voice_personality: context.voicePersonality,
          conversation_mode: context.conversationMode,
          theme: context.theme || document.documentElement.dataset.theme || "light",
        },
        dynamicVariables: {
          organicai_profile_id: context.activeProfileId,
          organicai_route: context.route,
          organicai_language: context.language,
        },
        onConnect: ({ conversationId: connectedId }) => {
          setConversationId(connectedId || token.conversationId);
          setConnectionStatus("connected");
          setLiveErrorCode("");
        },
        onDisconnect: () => {
          setConnectionStatus(currentStatus ? liveVoiceAvailability(currentStatus) : "disconnected");
          setWaitingForAgent(false);
        },
        onError: (message) => {
          setConnectionStatus("error");
          setLiveErrorCode("LIVE_CONNECTION_ERROR");
          setLiveError(liveVoiceErrorMessage(message));
        },
        onMessage: (message) => {
          void handleFinalMessage(message);
        },
        onAgentChatResponsePart: (part) => {
          setLiveAgentTranscript((current) => `${current}${part.text}`);
        },
        onInterruption: () => {
          setLiveAgentTranscript("");
          setWaitingForAgent(false);
        },
      };
      if (token.serverLocation) sessionOptions.serverLocation = token.serverLocation;
      controls.startSession(sessionOptions);
    } catch (error) {
      const apiError = extractApiError(error);
      setConnectionStatus("error");
      setLiveErrorCode(apiError.code);
      setLastRequestId(apiError.requestId);
      setLiveError(liveVoiceErrorMessage(error));
    } finally {
      startGuard.current = false;
    }
  }, [auth.isAuthenticated, auth.user, connectionStatus, controls, handleFinalMessage, providerStatus]);

  const setMicrophoneMuted = useCallback(
    (muted: boolean) => {
      if (adapterConnected) setTestMuted(muted);
      input.setMuted(muted);
    },
    [adapterConnected, input],
  );

  const sendLiveTextMessage = useCallback(
    (text: string) => {
      const connected = connectionStatus === "connected" || (testAdapterEnabled() && testTurnMode !== null);
      if (!text.trim() || !connected) return;
      if (testAdapterEnabled()) {
        void handleFinalMessage({ role: "user", source: "user", message: text.trim(), event_id: Date.now() });
        setTestTurnMode("thinking");
        return;
      }
      controls.sendUserActivity();
      controls.sendUserMessage(text.trim());
    },
    [connectionStatus, controls, handleFinalMessage, testTurnMode],
  );

  const notifyUserActivity = useCallback(() => {
    if (connectionStatus === "connected") controls.sendUserActivity();
  }, [connectionStatus, controls]);

  const setOrganicContext = useCallback((context: LiveVoiceOrganicContext) => {
    setOrganicContextState(context);
  }, []);

  const registerMessageHandler = useCallback((handler: LiveVoiceMessageHandler) => {
    handlers.current.add(handler);
    return () => {
      handlers.current.delete(handler);
    };
  }, []);

  type ToolMap = {
    navigate_to: (params: { path?: string }) => string;
    switch_theme: (params: { theme?: string }) => string;
    confirm_selected_node: (params: Record<string, unknown>) => Promise<string>;
    add_note_to_selected_node: (params: { note?: string }) => Promise<string>;
    open_selected_learning_path: (params: Record<string, unknown>) => string;
    regenerate_roadmap: (params: Record<string, unknown>) => Promise<string>;
    hide_selected_recommendation: (params: Record<string, unknown>) => Promise<string>;
    open_profile: (params: Record<string, unknown>) => string;
    open_roadmap: (params: Record<string, unknown>) => string;
    open_recommendations: (params: Record<string, unknown>) => string;
    open_diagnostic: (params: Record<string, unknown>) => string;
  };

  useConversationClientTool<ToolMap, "navigate_to">("navigate_to", ({ path }) => {
    const nextPath = safeString(path, 180);
    if (!nextPath.startsWith("/")) return jsonResult(false, "The requested route is not allowed.");
    navigate(nextPath);
    return jsonResult(true, "Route opened.");
  });
  useConversationClientTool<ToolMap, "switch_theme">("switch_theme", ({ theme }) => {
    if (theme === "dark") actions.executeVoiceCommand("dark mode");
    else if (theme === "light") actions.executeVoiceCommand("light mode");
    else return jsonResult(false, "Theme must be light or dark.");
    return jsonResult(true, `${theme} mode enabled.`);
  });
  useConversationClientTool<ToolMap, "confirm_selected_node">("confirm_selected_node", async () => {
    const node = organicContextRef.current.selectedProfileNode;
    if (!node) return jsonResult(false, "No profile node is selected.");
    const saved = await getProfileFeedback(organicContextRef.current.activeProfileId);
    await updateProfileFeedback(organicContextRef.current.activeProfileId, {
      ...saved,
      confirmed_nodes: [...new Set([...saved.confirmed_nodes, node])],
    });
    return jsonResult(true, "Selected profile node confirmed.");
  });
  useConversationClientTool<ToolMap, "add_note_to_selected_node">("add_note_to_selected_node", async ({ note }) => {
    const node = organicContextRef.current.selectedProfileNode;
    const cleanNote = safeString(note, 500);
    if (!node) return jsonResult(false, "No profile node is selected.");
    if (!cleanNote) return jsonResult(false, "A short note is required.");
    const saved = await getProfileFeedback(organicContextRef.current.activeProfileId);
    await updateProfileFeedback(organicContextRef.current.activeProfileId, {
      ...saved,
      user_notes: { ...saved.user_notes, [node]: cleanNote },
    });
    return jsonResult(true, "Note added to the selected profile node.");
  });
  useConversationClientTool<ToolMap, "open_selected_learning_path">("open_selected_learning_path", () => {
    navigate(`/workspace/${organicContextRef.current.activeProfileId}/learning`);
    return jsonResult(true, "Learning path opened.");
  });
  useConversationClientTool<ToolMap, "regenerate_roadmap">("regenerate_roadmap", async () => {
    await generateRoadmap(organicContextRef.current.activeProfileId);
    return jsonResult(true, "Roadmap regenerated.");
  });
  useConversationClientTool<ToolMap, "hide_selected_recommendation">("hide_selected_recommendation", async () => {
    const recommendationId = organicContextRef.current.selectedRecommendationId;
    if (!recommendationId) return jsonResult(false, "No recommendation is selected.");
    const saved = await getProfileFeedback(organicContextRef.current.activeProfileId);
    await updateProfileFeedback(organicContextRef.current.activeProfileId, {
      ...saved,
      hidden_recommendations: [...new Set([...saved.hidden_recommendations, recommendationId])],
    });
    return jsonResult(true, "Recommendation hidden.");
  });
  useConversationClientTool<ToolMap, "open_profile">("open_profile", () => {
    actions.navigateToProfile(organicContextRef.current.activeProfileId);
    return jsonResult(true, "Profile opened.");
  });
  useConversationClientTool<ToolMap, "open_roadmap">("open_roadmap", () => {
    actions.navigateToRoadmap(organicContextRef.current.activeProfileId);
    return jsonResult(true, "Roadmap opened.");
  });
  useConversationClientTool<ToolMap, "open_recommendations">("open_recommendations", () => {
    navigate(`/recommendations/${organicContextRef.current.activeProfileId}`);
    return jsonResult(true, "Recommendations opened.");
  });
  useConversationClientTool<ToolMap, "open_diagnostic">("open_diagnostic", () => {
    actions.navigateToDiagnostic();
    return jsonResult(true, "Diagnostic opened.");
  });

  const value = useMemo<LiveVoiceContextValue>(
    () => ({
      providerStatus,
      connectionStatus: effectiveConnectionStatus,
      turnMode,
      isConnected: effectiveConnectionStatus === "connected",
      isListening: turnMode === "listening",
      isSpeaking: turnMode === "speaking",
      isMuted: effectiveMuted,
      conversationId,
      interimUserTranscript,
      liveAgentTranscript,
      liveError,
      liveErrorCode,
      lastRequestId,
      inputLevel,
      outputLevel,
      startLiveConversation,
      endLiveConversation,
      setMicrophoneMuted,
      sendLiveTextMessage,
      notifyUserActivity,
      sendPageContext,
      setOrganicContext,
      registerMessageHandler,
      refreshStatus,
    }),
    [
      providerStatus,
      effectiveConnectionStatus,
      turnMode,
      effectiveMuted,
      conversationId,
      interimUserTranscript,
      liveAgentTranscript,
      liveError,
      liveErrorCode,
      lastRequestId,
      inputLevel,
      outputLevel,
      startLiveConversation,
      endLiveConversation,
      setMicrophoneMuted,
      sendLiveTextMessage,
      notifyUserActivity,
      sendPageContext,
      setOrganicContext,
      registerMessageHandler,
      refreshStatus,
    ],
  );

  return <LiveVoiceContext.Provider value={value}>{children}</LiveVoiceContext.Provider>;
}

export function LiveVoiceProvider({ children }: { children: ReactNode }) {
  const [muted, setMuted] = useState(false);
  return (
    <ConversationProvider isMuted={muted} onMutedChange={setMuted}>
      <LiveVoiceBridge>{children}</LiveVoiceBridge>
    </ConversationProvider>
  );
}
