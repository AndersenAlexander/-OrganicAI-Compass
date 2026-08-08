import { lazy, Suspense, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  ExternalLink,
  MessageCircle,
  Mic,
  Minimize2,
  Pause,
  RotateCcw,
  Send,
  Square,
  Trash2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAppActions } from "../../hooks/useAppActions";
import { useCoach } from "../../hooks/useCoach";
import { ChatBubble } from "./ChatBubble";
import { AICoachOrbFallback } from "../three/AICoachOrbFallback";
import "../../styles/floating-voice-chat.css";

const AICoachOrb3D = lazy(() =>
  import("../three/AICoachOrb3D").then((module) => ({ default: module.AICoachOrb3D })),
);

const personalities = [
  "Calm Guide",
  "Creative Mentor",
  "Practical Coach",
  "Reflective Companion",
  "Energetic Builder",
];

const modes = [
  "Explain simply",
  "Ask reflective questions",
  "Help me structure my thoughts",
  "Help me create",
  "Challenge me ethically",
  "Build a small action plan",
];

export function FloatingVoiceChat() {
  const { activeProfileId, isCoachOpen, openCoach, closeCoach } = useAppActions();
  const coach = useCoach();
  const [input, setInput] = useState("");
  const [showConsent, setShowConsent] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  function requestVoice() {
    if (!coach.preferences.voiceConsent) setShowConsent(true);
    else void coach.startListening();
  }

  function sendInput() {
    void coach.sendTextMessage(input);
    setInput("");
  }

  return (
    <div className="floating-voice-chat" data-state={isCoachOpen ? "open" : "closed"}>
      <AnimatePresence>
        {isCoachOpen && (
          <motion.section
            initial={{ opacity: 0, y: 20, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.96 }}
            aria-label="OrganicAI Coach"
            className="floating-voice-chat__panel glass-panel flex flex-col overflow-hidden"
          >
            <header className="floating-voice-chat__header flex items-center justify-between border-b border-[color:var(--border-soft)] p-4">
              <div className="flex min-w-0 items-center gap-3">
                <Suspense fallback={<AICoachOrbFallback state={coach.state} className="floating-voice-chat__orb" />}>
                  <AICoachOrb3D
                    state={coach.state}
                    onClick={coach.state === "speaking" ? coach.stopSpeaking : undefined}
                    className="floating-voice-chat__orb overflow-hidden rounded-full bg-[#071527]"
                  />
                </Suspense>
                <div className="min-w-0">
                  <h2 className="truncate font-display text-lg font-bold theme-text">OrganicAI Coach</h2>
                  <p aria-live="polite" className="text-xs capitalize text-[color:var(--teal)]">
                    {coach.state}
                  </p>
                </div>
              </div>

              <div className="floating-voice-chat__panel-actions flex shrink-0 gap-2">
                <Link
                  to={`/coach/${activeProfileId}`}
                  aria-label="Open full AI Coach"
                  className="floating-voice-chat__icon-button grid place-items-center rounded-full border border-[color:var(--border-soft)]"
                >
                  <ExternalLink size={16} />
                </Link>
                <button
                  type="button"
                  aria-label="Minimize OrganicAI Coach"
                  onClick={closeCoach}
                  className="floating-voice-chat__icon-button floating-voice-chat__minimize grid place-items-center rounded-full border border-[color:var(--border-soft)]"
                >
                  <Minimize2 size={17} />
                </button>
              </div>
            </header>

            <div className="floating-voice-chat__messages flex-1 space-y-3 overflow-y-auto p-4">
              <button
                type="button"
                onClick={() => setShowSettings((visible) => !visible)}
                className="text-xs font-bold text-[color:var(--teal)]"
              >
                {showSettings ? "Hide" : "Show"} voice & privacy settings
              </button>

              {showSettings && (
                <div className="grid gap-3 rounded-2xl border border-[color:var(--border-soft)] p-3 text-xs">
                  <label>
                    Voice personality
                    <select
                      value={coach.preferences.voicePersonality}
                      onChange={(event) => coach.setPreferences({ voicePersonality: event.target.value })}
                      className="organic-input mt-1"
                    >
                      {personalities.map((personality) => (
                        <option key={personality}>{personality}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Conversation mode
                    <select
                      value={coach.preferences.conversationMode}
                      onChange={(event) => coach.setPreferences({ conversationMode: event.target.value })}
                      className="organic-input mt-1"
                    >
                      {modes.map((mode) => (
                        <option key={mode}>{mode}</option>
                      ))}
                    </select>
                  </label>
                  {[
                    ["Mute voice", "isMuted"],
                    ["Auto-play AI voice", "autoPlay"],
                    ["Auto-send transcript", "autoSendTranscript"],
                    ["Store transcripts", "storeTranscripts"],
                  ].map(([label, key]) => (
                    <label key={key} className="flex items-center justify-between gap-3">
                      <span>{label}</span>
                      <input
                        type="checkbox"
                        checked={Boolean(coach.preferences[key as "autoPlay"])}
                        onChange={(event) => coach.setPreferences({ [key]: event.target.checked })}
                      />
                    </label>
                  ))}
                  <label className="flex items-center justify-between">
                    <span>Store audio (off by default)</span>
                    <input
                      type="checkbox"
                      checked={coach.preferences.storeAudio}
                      onChange={(event) => coach.setPreferences({ storeAudio: event.target.checked })}
                    />
                  </label>
                </div>
              )}

              {coach.messages.map((message) => (
                <ChatBubble key={message.id} message={message} autoPlay={false} />
              ))}

              {coach.error && (
                <p role="alert" className="rounded-xl bg-amber-50 p-3 text-xs text-amber-800">
                  {coach.error}
                </p>
              )}

              {coach.transcript && (
                <div className="rounded-2xl border border-teal-200 p-3">
                  <label className="text-xs font-bold theme-text">
                    Review transcript
                    <textarea
                      className="organic-input mt-2"
                      value={coach.transcript}
                      onChange={(event) => coach.setTranscript(event.target.value)}
                      rows={3}
                    />
                  </label>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => void coach.sendTextMessage(coach.transcript, "voice")}
                      className="organic-button"
                    >
                      <Send size={15} /> Send
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        coach.cancelTranscript();
                        requestVoice();
                      }}
                      className="organic-button-secondary"
                    >
                      <RotateCcw size={15} /> Record again
                    </button>
                    <button type="button" onClick={coach.cancelTranscript} className="organic-button-secondary">
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {showConsent && (
                <div className="rounded-2xl border border-teal-200 bg-teal-50/60 p-4 text-sm text-[#102033]">
                  <p>
                    Your voice will be sent to the configured speech service for transcription. Audio is processed for
                    this interaction and is not stored unless you explicitly enable voice history.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        coach.setPreferences({ voiceConsent: true });
                        setShowConsent(false);
                        void coach.startListening();
                      }}
                      className="organic-button"
                    >
                      Continue
                    </button>
                    <button type="button" onClick={() => setShowConsent(false)} className="organic-button-secondary">
                      Use text instead
                    </button>
                    <Link to="/knowledge-base" className="organic-button-secondary">
                      Learn more
                    </Link>
                  </div>
                </div>
              )}
            </div>

            <footer className="floating-voice-chat__footer border-t border-[color:var(--border-soft)] p-3">
              {coach.state === "listening" ? (
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold text-[color:var(--teal)]">
                    Listening - {coach.recordingSeconds}s
                  </span>
                  <button type="button" onClick={coach.stopListening} className="organic-button">
                    <Square size={16} /> Stop
                  </button>
                </div>
              ) : coach.state === "speaking" ? (
                <button type="button" onClick={coach.stopSpeaking} className="organic-button-secondary w-full">
                  <Pause size={16} /> Stop Speaking
                </button>
              ) : (
                <div className="floating-voice-chat__composer flex gap-2">
                  <input
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") sendInput();
                    }}
                    className="organic-input min-w-0"
                    placeholder="Ask or use a command"
                  />
                  <button
                    type="button"
                    aria-label="Start voice"
                    onClick={requestVoice}
                    className="organic-button-secondary"
                  >
                    <Mic size={18} />
                  </button>
                  <button type="button" aria-label="Send" onClick={sendInput} className="organic-button">
                    <Send size={18} />
                  </button>
                </div>
              )}
              <div className="mt-2 flex justify-between gap-3">
                <button type="button" onClick={() => void coach.replayLastAnswer()} className="text-xs theme-muted">
                  Replay answer
                </button>
                <button
                  type="button"
                  onClick={coach.clearConversation}
                  className="flex items-center gap-1 text-xs theme-muted"
                >
                  <Trash2 size={13} /> New conversation
                </button>
              </div>
            </footer>
          </motion.section>
        )}
      </AnimatePresence>

      {!isCoachOpen && (
        <motion.button
          type="button"
          onClick={() => openCoach()}
          whileHover={{ y: -3 }}
          className="floating-voice-chat__launcher flex h-[58px] items-center gap-3 rounded-full bg-white/90 px-4 font-bold text-[#102033] shadow-[0_18px_52px_rgba(15,23,42,.18)] dark:bg-[#071527]/90 dark:text-white"
        >
          <span className="grid h-11 w-11 place-items-center rounded-full bg-[color:var(--color-accent-action)] text-[color:var(--color-accent-action-text)]">
            <MessageCircle size={21} />
          </span>
          Talk with OrganicAI Coach
        </motion.button>
      )}
    </div>
  );
}
