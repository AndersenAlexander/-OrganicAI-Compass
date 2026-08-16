import { lazy, Suspense, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ExternalLink, MessageCircle, Mic, MicOff, Minimize2, RotateCcw, Send, Square, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { useAppActions } from "../../hooks/useAppActions";
import { useCoach } from "../../hooks/useCoach";
import { ChatBubble } from "./ChatBubble";
import { AICoachOrbFallback } from "../three/AICoachOrbFallback";
import "../../styles/floating-voice-chat.css";

const AICoachOrb3D = lazy(() => import("../three/AICoachOrb3D").then((module) => ({ default: module.AICoachOrb3D })));

const personalities = ["Calm Guide", "Creative Mentor", "Practical Coach", "Reflective Companion", "Energetic Builder"];
const modes = ["Explain simply", "Ask reflective questions", "Help me structure my thoughts", "Help me create", "Challenge me ethically", "Build a small action plan"];

function launcherLabel(turnMode: string) {
  if (turnMode === "listening") return "Coach listening";
  if (turnMode === "speaking") return "Coach speaking";
  if (turnMode === "muted") return "Microphone muted";
  return "Talk with OrganicAI Coach";
}

export function FloatingVoiceChat() {
  const { activeProfileId, isCoachOpen, openCoach, closeCoach } = useAppActions();
  const coach = useCoach();
  const live = coach.liveVoice;
  const [input, setInput] = useState("");
  const [showConsent, setShowConsent] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  function requestLive() {
    coach.setPreferences({ voiceMode: "live" });
    if (!coach.preferences.voiceConsent) setShowConsent(true);
    else void coach.startListening();
  }

  function requestVoiceMessage() {
    coach.setPreferences({ voiceMode: "message" });
    if (!coach.preferences.voiceConsent) setShowConsent(true);
    else void coach.startVoiceMessage();
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
                  <AICoachOrb3D state={coach.state} className="floating-voice-chat__orb overflow-hidden rounded-full bg-[#071527]" />
                </Suspense>
                <div className="min-w-0">
                  <h2 className="truncate font-display text-lg font-bold theme-text">OrganicAI Coach</h2>
                  <p aria-live="polite" className="text-xs capitalize text-[color:var(--teal)]">{coach.preferences.voiceMode === "live" ? live.turnMode : coach.state}</p>
                </div>
              </div>
              <div className="floating-voice-chat__panel-actions flex shrink-0 gap-2">
                <Link to={activeProfileId ? `/coach/${activeProfileId}` : "/diagnostic"} aria-label="Open full AI Coach" className="floating-voice-chat__icon-button grid place-items-center rounded-full border border-[color:var(--border-soft)]">
                  <ExternalLink size={16} />
                </Link>
                <button type="button" aria-label="Minimize OrganicAI Coach" onClick={closeCoach} className="floating-voice-chat__icon-button floating-voice-chat__minimize grid place-items-center rounded-full border border-[color:var(--border-soft)]">
                  <Minimize2 size={17} />
                </button>
              </div>
            </header>

            <div className="floating-voice-chat__messages flex-1 space-y-3 overflow-y-auto p-4">
              <button type="button" onClick={() => setShowSettings((visible) => !visible)} className="text-xs font-bold text-[color:var(--teal)]">
                {showSettings ? "Hide" : "Show"} voice & privacy settings
              </button>

              {showSettings ? (
                <div className="grid gap-3 rounded-2xl border border-[color:var(--border-soft)] p-3 text-xs">
                  <label>
                    Voice mode
                    <select value={coach.preferences.voiceMode} onChange={(event) => coach.setPreferences({ voiceMode: event.target.value as "live" | "message" })} className="organic-input mt-1">
                      <option value="live">Live conversation</option>
                      <option value="message">Voice message</option>
                    </select>
                  </label>
                  <label>
                    Voice personality
                    <select value={coach.preferences.voicePersonality} onChange={(event) => coach.setPreferences({ voicePersonality: event.target.value })} className="organic-input mt-1">
                      {personalities.map((personality) => <option key={personality}>{personality}</option>)}
                    </select>
                  </label>
                  <label>
                    Conversation mode
                    <select value={coach.preferences.conversationMode} onChange={(event) => coach.setPreferences({ conversationMode: event.target.value })} className="organic-input mt-1">
                      {modes.map((mode) => <option key={mode}>{mode}</option>)}
                    </select>
                  </label>
                  {[["Auto-play legacy voice", "autoPlay"], ["Auto-send voice-message transcript", "autoSendTranscript"], ["Store transcripts", "storeTranscripts"]].map(([label, key]) => (
                    <label key={key} className="flex items-center justify-between gap-3">
                      <span>{label}</span>
                      <input type="checkbox" checked={Boolean(coach.preferences[key as "autoPlay"])} onChange={(event) => coach.setPreferences({ [key]: event.target.checked })} />
                    </label>
                  ))}
                </div>
              ) : null}

              {live.isConnected ? (
                <div className="rounded-2xl border border-[color:var(--border-soft)] p-3 text-sm">
                  <p className="font-bold theme-text">Live conversation active</p>
                  <p className="mt-1 theme-muted">This is the same session used by the full Coach page.</p>
                  {live.interimUserTranscript ? <p className="mt-2 theme-text">You said: {live.interimUserTranscript}</p> : null}
                  {live.liveAgentTranscript ? <p className="mt-2 theme-text">Agent: {live.liveAgentTranscript}</p> : null}
                </div>
              ) : null}

              {coach.messages.map((message) => <ChatBubble key={message.id} message={message} autoPlay={false} />)}

              {coach.error ? <p role="alert" className="rounded-xl bg-amber-50 p-3 text-xs text-amber-800">{coach.error}</p> : null}

              {coach.preferences.voiceMode === "message" && coach.transcript ? (
                <div className="rounded-2xl border border-teal-200 p-3">
                  <label className="text-xs font-bold theme-text">
                    Review transcript
                    <textarea className="organic-input mt-2" value={coach.transcript} onChange={(event) => coach.setTranscript(event.target.value)} rows={3} />
                  </label>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <button type="button" onClick={() => void coach.sendTextMessage(coach.transcript, "voice")} className="organic-button"><Send size={15} /> Send</button>
                    <button type="button" onClick={requestVoiceMessage} className="organic-button-secondary"><RotateCcw size={15} /> Record again</button>
                    <button type="button" onClick={coach.cancelTranscript} className="organic-button-secondary">Cancel</button>
                  </div>
                </div>
              ) : null}

              {showConsent ? (
                <div className="rounded-2xl border border-teal-200 bg-teal-50/70 p-4 text-sm text-[#102033]">
                  <p>
                    Live voice uses ElevenLabs to process microphone audio, detect conversation turns, transcribe speech and generate the agent's voice. OrganicAI stores text transcripts only when transcript history is enabled and does not store live audio files by default.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        coach.setPreferences({ voiceConsent: true });
                        setShowConsent(false);
                        if (coach.preferences.voiceMode === "message") void coach.startVoiceMessage();
                        else void coach.startListening();
                      }}
                      className="organic-button"
                    >
                      {coach.preferences.voiceMode === "message" ? "Start voice message" : "Start live conversation"}
                    </button>
                    <button type="button" onClick={() => setShowConsent(false)} className="organic-button-secondary">Use text instead</button>
                    <Link to="/knowledge-base" className="organic-button-secondary">Learn more</Link>
                  </div>
                </div>
              ) : null}
            </div>

            <footer className="floating-voice-chat__footer border-t border-[color:var(--border-soft)] p-3">
              {live.isConnected ? (
                <div className="grid gap-2">
                  <div className="flex flex-wrap gap-2">
                    {live.isMuted ? (
                      <button type="button" onClick={() => live.setMicrophoneMuted(false)} className="organic-button"><Mic size={16} /> Unmute</button>
                    ) : (
                      <button type="button" onClick={() => live.setMicrophoneMuted(true)} className="organic-button-secondary"><MicOff size={16} /> Mute</button>
                    )}
                    <button type="button" onClick={() => void live.endLiveConversation()} className="organic-button-secondary"><Square size={16} /> End</button>
                  </div>
                  <div className="floating-voice-chat__composer flex gap-2">
                    <input
                      value={input}
                      onChange={(event) => {
                        setInput(event.target.value);
                        live.notifyUserActivity();
                      }}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") sendInput();
                      }}
                      className="organic-input min-w-0"
                      placeholder="Send text into live session"
                    />
                    <button type="button" aria-label="Send" onClick={sendInput} className="organic-button"><Send size={18} /></button>
                  </div>
                </div>
              ) : coach.preferences.voiceMode === "message" && coach.state === "listening" ? (
                <button type="button" onClick={coach.stopListening} className="organic-button w-full"><Square size={16} /> Stop voice message - {coach.recordingSeconds}s</button>
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
                  <button type="button" aria-label="Start live conversation" onClick={requestLive} className="organic-button-secondary"><Mic size={18} /></button>
                  <button type="button" aria-label="Send" onClick={sendInput} className="organic-button"><Send size={18} /></button>
                </div>
              )}
              <div className="mt-2 flex justify-between gap-3">
                <button type="button" onClick={requestVoiceMessage} className="text-xs theme-muted">Use voice message</button>
                <button type="button" onClick={coach.clearConversation} className="flex items-center gap-1 text-xs theme-muted"><Trash2 size={13} /> New conversation</button>
              </div>
            </footer>
          </motion.section>
        )}
      </AnimatePresence>

      {!isCoachOpen && (
        <motion.button type="button" onClick={() => openCoach()} whileHover={{ y: -3 }} className="floating-voice-chat__launcher flex h-[58px] items-center gap-3 rounded-full bg-white/90 px-4 font-bold text-[#102033] shadow-[0_18px_52px_rgba(15,23,42,.18)] dark:bg-[#071527]/90 dark:text-white">
          <span className="grid h-11 w-11 place-items-center rounded-full bg-[color:var(--color-accent-action)] text-[color:var(--color-accent-action-text)]"><MessageCircle size={21} /></span>
          {launcherLabel(live.turnMode)}
        </motion.button>
      )}
    </div>
  );
}
