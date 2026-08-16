import { lazy, Suspense, useState } from "react";
import { ArrowRight, Bot, Mic, MicOff, Send, ShieldCheck, Sparkles, Square, Trash2, Volume2 } from "lucide-react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useCoach } from "../hooks/useCoach";
import { useAppActions } from "../hooks/useAppActions";
import { AICoachOrbFallback } from "../components/three/AICoachOrbFallback";
import { ComingSoonDialog } from "../components/shared/ComingSoonDialog";
import { RagFeedback } from "../components/shared/RagFeedback";

const AICoachOrb3D = lazy(() => import("../components/three/AICoachOrb3D").then((module) => ({ default: module.AICoachOrb3D })));

const quick: Record<string, string> = {
  "Reflect with AI": "Guide me through a short profile-aware reflection about my relationship with AI.",
  "Help Me Decide": "Help me compare options with pros, cons, profile fit, and ethical considerations.",
  "Create an Action Plan": "Build a small action plan using my confirmed profile signals.",
  "Practice a Conversation": "Start a role-play about introducing responsible AI to my team.",
  "Review My Roadmap": "Summarize my roadmap and read the seven-day plan.",
};

function liveStatusLabel(coachState: string) {
  if (coachState === "connecting") return "Connecting securely...";
  if (coachState === "listening") return "Listening";
  if (coachState === "thinking") return "OrganicAI Coach is thinking...";
  if (coachState === "speaking") return "OrganicAI Coach is speaking";
  if (coachState === "muted") return "Microphone muted";
  if (coachState === "error") return "Live voice needs attention";
  return "Live voice conversation";
}

function LevelBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="live-voice-level" aria-label={`${label} level ${Math.round(value * 100)} percent`}>
      <span>{label}</span>
      <div><i style={{ width: `${Math.min(100, Math.max(0, value * 100))}%` }} /></div>
    </div>
  );
}

export function CoachPage() {
  const coach = useCoach();
  const actions = useAppActions();
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [concept, setConcept] = useState(false);
  const [comingSoon, setComingSoon] = useState(false);
  const [pipeline, setPipeline] = useState(false);
  const [voiceConsent, setVoiceConsent] = useState(false);
  const latest = [...coach.messages].reverse().find((message) => message.role === "assistant");
  const live = coach.liveVoice;
  const startDisabled = ["requesting-permission", "requesting-token", "connecting", "disconnecting"].includes(live.connectionStatus);

  function send(text: string) {
    void coach.sendTextMessage(text);
    setInput("");
  }

  function requestLive() {
    coach.setPreferences({ voiceMode: "live" });
    if (!coach.preferences.voiceConsent) setVoiceConsent(true);
    else void coach.startListening();
  }

  function requestVoiceMessage() {
    coach.setPreferences({ voiceMode: "message" });
    if (!coach.preferences.voiceConsent) setVoiceConsent(true);
    else void coach.startVoiceMessage();
  }

  return (
    <div className="organic-page">
      <div className="grid gap-6 xl:grid-cols-[16rem_1fr_24rem]">
        <aside className="surface-inverse rounded-[2rem] bg-[#071527]/92 p-5 text-white">
          <div className="mb-6 flex items-center gap-3"><Bot /> <b>OrganicAI Compass</b></div>
          {[
            ["Home", "/"],
            ["AI Coach", `/coach/${actions.activeProfileId}`],
            ["Diagnostic", "/diagnostic"],
            ["Human Potential Map", `/profile/${actions.activeProfileId}`],
            ["Roadmap", `/roadmap/${actions.activeProfileId}`],
            ["Knowledge Base", "/knowledge-base"],
          ].map(([label, to]) => (
            <NavLink key={label} to={to} className={({ isActive }) => `mt-1 block rounded-xl px-3 py-2 text-sm ${isActive ? "bg-white/12 text-[#99f6e4]" : "text-white/75 hover:bg-white/8"}`}>
              {label}
            </NavLink>
          ))}
          <div className="mt-6 rounded-2xl border border-white/10 p-3 text-xs text-white/70">
            <p className="font-bold text-white">Current profile</p>
            <p className="mt-1">{actions.activeProfileId}</p>
            <p className="mt-3">Voice: {coach.preferences.voicePersonality}</p>
            <p>Mode: {coach.preferences.voiceMode === "live" ? "Live conversation" : "Voice message"}</p>
          </div>
          <button type="button" onClick={coach.clearConversation} className="mt-5 flex items-center gap-2 text-sm text-white/70">
            <Trash2 size={15} /> New conversation
          </button>
        </aside>

        <main className="space-y-5">
          <section className="relative min-h-[420px] overflow-hidden rounded-[2.5rem] bg-[#06101d] p-7 text-white">
            <div className="relative z-10 max-w-md">
              <p className="text-xs font-bold uppercase tracking-wider text-[#99f6e4]">Voice-first profile-aware agent</p>
              <h1 className="mt-3 font-display text-4xl font-semibold">How can we move forward?</h1>
              <p aria-live="polite" className="mt-3 capitalize text-white/70">Agent state: {coach.state}</p>
              {coach.lastRecognizedCommand ? <p className="mt-3 text-sm text-[#a3e635]">Last command: {coach.lastRecognizedCommand}</p> : null}
            </div>
            <Suspense fallback={<AICoachOrbFallback state={coach.state} className="absolute right-12 top-12 h-72 w-72" />}>
              <AICoachOrb3D state={coach.state} onClick={coach.state === "speaking" ? coach.stopSpeaking : undefined} className="absolute inset-y-0 right-0 w-1/2" />
            </Suspense>
          </section>

          <section className="glass-card live-voice-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--teal)]">Live conversation</p>
                <h2 className="font-display text-2xl font-bold theme-text">{liveStatusLabel(coach.state)}</h2>
                <p className="mt-2 max-w-2xl text-sm theme-muted">
                  Speak naturally with OrganicAI Coach. The microphone stays active until you end the session.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {!live.isConnected ? (
                  <button type="button" onClick={requestLive} disabled={startDisabled} className="organic-button">
                    <Mic size={17} /> {coach.state === "error" ? "Retry live conversation" : "Start live conversation"}
                  </button>
                ) : (
                  <>
                    {live.isMuted ? (
                      <button type="button" onClick={() => live.setMicrophoneMuted(false)} className="organic-button">
                        <Mic size={17} /> Unmute microphone
                      </button>
                    ) : (
                      <button type="button" onClick={() => live.setMicrophoneMuted(true)} className="organic-button-secondary">
                        <MicOff size={17} /> Mute microphone
                      </button>
                    )}
                    <button type="button" onClick={() => void live.endLiveConversation()} className="organic-button-secondary">
                      <Square size={16} /> End conversation
                    </button>
                  </>
                )}
                <button type="button" onClick={requestVoiceMessage} className="organic-button-secondary">
                  Use voice message instead
                </button>
              </div>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <LevelBar label="Input" value={live.inputLevel} />
              <LevelBar label="Output" value={live.outputLevel} />
            </div>

            {live.isSpeaking ? <p className="mt-3 text-sm theme-muted">You can interrupt the agent naturally by speaking over the response when barge-in is enabled in ElevenLabs.</p> : null}
            {live.interimUserTranscript ? <p className="mt-3 rounded-2xl border border-[color:var(--border-soft)] p-3 text-sm theme-text">You said: {live.interimUserTranscript}</p> : null}
            {live.liveAgentTranscript ? <p className="mt-3 rounded-2xl border border-[color:var(--border-soft)] p-3 text-sm theme-text">Agent transcript: {live.liveAgentTranscript}</p> : null}
            {coach.error ? (
              <div role="alert" className="mt-4 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
                <p>{coach.error}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button type="button" onClick={requestLive} className="organic-button-secondary">Retry live conversation</button>
                  <button type="button" onClick={() => coach.setPreferences({ voiceMode: "live" })} className="organic-button-secondary">Continue with text</button>
                </div>
              </div>
            ) : null}

            {voiceConsent ? (
              <div className="mt-4 rounded-2xl border border-teal-200 bg-teal-50/70 p-4 text-sm text-[#102033]">
                <p>
                  Live voice uses ElevenLabs to process microphone audio, detect conversation turns, transcribe speech and generate the agent's voice. The live session remains active until you end it. OrganicAI stores text transcripts only when transcript history is enabled. OrganicAI does not store live audio files by default.
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      coach.setPreferences({ voiceConsent: true });
                      setVoiceConsent(false);
                      if (coach.preferences.voiceMode === "message") void coach.startVoiceMessage();
                      else void coach.startListening();
                    }}
                    className="organic-button"
                  >
                    {coach.preferences.voiceMode === "message" ? "Start voice message" : "Start live conversation"}
                  </button>
                  <button type="button" onClick={() => setVoiceConsent(false)} className="organic-button-secondary">Use text instead</button>
                  <Link to="/knowledge-base" className="organic-button-secondary">Learn more</Link>
                </div>
              </div>
            ) : null}

            <details className="mt-4 rounded-2xl border border-[color:var(--border-soft)] p-4 text-sm">
              <summary className="cursor-pointer font-bold theme-text">Voice connection diagnostics</summary>
              <div className="mt-3 grid gap-2 text-xs theme-muted sm:grid-cols-2">
                <p>Live voice enabled: {String(Boolean(live.providerStatus?.liveVoiceEnabled))}</p>
                <p>Agent configured: {String(Boolean(live.providerStatus?.agentIdConfigured))}</p>
                <p>Custom LLM configured: {String(Boolean(live.providerStatus?.customLlmConfigured))}</p>
                <p>Residency mode: {live.providerStatus?.residencyMode || "standard"}</p>
                <p>Public backend required: {String(Boolean(live.providerStatus?.customLlmEnabled))}</p>
                <p>Public backend reachable: {String(Boolean(live.providerStatus?.publicBackendReachable))}</p>
                <p>Microphone support: {typeof navigator !== "undefined" && Boolean(navigator.mediaDevices) ? "available" : "unsupported"}</p>
                <p>Browser permission: {coach.preferences.voiceConsent ? "consent accepted" : "not granted yet"}</p>
                <p>Current connection: {live.connectionStatus}</p>
                <p>Last safe error code: {live.liveErrorCode || "none"}</p>
                <p>Request ID: {live.lastRequestId || "none"}</p>
                <p>Fallback availability: {String(Boolean(live.providerStatus?.legacyFallbackEnabled))}</p>
              </div>
              {live.providerStatus?.blockingIssues?.length ? (
                <ul className="mt-3 space-y-1 text-xs text-amber-700">
                  {live.providerStatus.blockingIssues.map((issue) => <li key={issue.code}>Code: {issue.code}</li>)}
                </ul>
              ) : null}
            </details>
          </section>

          {coach.preferences.voiceMode === "message" ? (
            <section className="glass-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-display text-xl font-bold theme-text">Voice message fallback</h2>
                  <p className="mt-1 text-sm theme-muted">Record a short message, review the transcript, then send it to the text coach.</p>
                </div>
                {coach.state === "listening" ? (
                  <button type="button" onClick={coach.stopListening} className="organic-button"><Square size={16} /> Stop recording - {coach.recordingSeconds}s</button>
                ) : (
                  <button type="button" onClick={requestVoiceMessage} className="organic-button-secondary"><Mic size={17} /> Start voice message</button>
                )}
              </div>
              {coach.transcript ? (
                <label className="mt-4 block">
                  <span className="text-sm font-bold theme-text">Review transcript before sending</span>
                  <textarea value={coach.transcript} onChange={(event) => coach.setTranscript(event.target.value)} className="organic-input mt-2" rows={3} />
                  <div className="mt-2 flex flex-wrap gap-2">
                    <button type="button" onClick={() => void coach.sendTextMessage(coach.transcript, "voice")} className="organic-button">Send transcript</button>
                    <button type="button" onClick={requestVoiceMessage} className="organic-button-secondary">Record again</button>
                    <button type="button" onClick={coach.cancelTranscript} className="organic-button-secondary">Cancel</button>
                  </div>
                </label>
              ) : null}
            </section>
          ) : null}

          <section className="glass-card p-5">
            <div className="flex justify-between">
              <h2 className="font-display text-xl font-bold theme-text">Knowledge & profile context</h2>
              <Link to="/knowledge-base" className="text-sm text-[color:var(--teal)]">View all <ArrowRight className="inline" size={14} /></Link>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {latest?.groundingStatus ? (
                <span className="organic-chip"><ShieldCheck size={15} />{latest.groundingStatus === "grounded" ? "Grounded answer" : latest.groundingStatus === "profile_grounded" ? "Profile-grounded guidance" : "General AI answer"}</span>
              ) : null}
              {latest?.sourcesUsed?.map((source) => <Link to="/knowledge-base" key={source.id} className="organic-chip text-xs">{source.document_name} - {source.section_title}</Link>)}
              {latest?.profileSignals?.map((signal) => <span key={signal} className="organic-chip text-xs">Profile: {signal}</span>)}
            </div>
            {latest && typeof latest.retrievalStatus?.rag_run_id === "string" ? (
              <>
                <span className={`rag-quality ${String(latest.retrievalStatus.context_quality || "partial")}`}>Context quality: {String(latest.retrievalStatus.context_quality || "partial")}</span>
                <RagFeedback runId={latest.retrievalStatus.rag_run_id} />
              </>
            ) : null}
          </section>

          {import.meta.env.DEV ? (
            <section className="glass-card p-5">
              <button type="button" onClick={() => setPipeline((visible) => !visible)} className="font-bold text-[color:var(--teal)]">Explain AI Pipeline</button>
              {pipeline ? (
                <div className="mt-4 text-xs theme-muted">
                  <p>Live microphone - ElevenLabs WebRTC - OrganicAI Custom LLM - RAG - streamed voice. Voice message fallback still uses MediaRecorder - transcription - text chat - legacy MP3.</p>
                  <pre className="mt-3 overflow-auto rounded-xl bg-slate-950 p-3 text-white">{JSON.stringify({ intent: latest?.intent, grounding: latest?.groundingStatus, retrieval: latest?.retrievalStatus, profile_signals: latest?.profileSignals, sources: latest?.sourcesUsed, timing: latest?.timing }, null, 2)}</pre>
                </div>
              ) : null}
            </section>
          ) : null}
        </main>

        <aside className="space-y-4">
          <section className="organic-card-dark flex max-h-[650px] flex-col p-5 text-white">
            <h2 className="font-display text-xl font-bold">Conversation</h2>
            <div className="mt-4 flex-1 space-y-3 overflow-y-auto">
              {coach.messages.map((message) => (
                <article key={message.id} className={`rounded-2xl p-3 text-sm leading-6 ${message.role === "user" ? "ml-8 bg-teal/70" : "mr-8 bg-white/10"}`}>
                  <p>{message.content}</p>
                  {message.confidenceNote ? <p className="mt-2 text-xs text-white/60">{message.confidenceNote}</p> : null}
                  {message.ethicalNote ? <p className="mt-2 text-xs text-[#99f6e4]">{message.ethicalNote}</p> : null}
                </article>
              ))}
            </div>
            <div className="mt-4 flex gap-2">
              <input
                value={input}
                onChange={(event) => {
                  setInput(event.target.value);
                  live.notifyUserActivity();
                }}
                onKeyDown={(event) => event.key === "Enter" && send(input)}
                className="min-w-0 flex-1 rounded-xl bg-white/10 px-3 text-sm outline-none"
                placeholder={live.isConnected ? "Send text into the live session" : "Ask anything"}
              />
              <button type="button" aria-label="Send message" onClick={() => send(input)} className="organic-icon-orb h-11 w-11"><Send size={17} /></button>
            </div>
          </section>
          <section className="glass-card p-5">
            <h2 className="font-display text-lg font-bold theme-text">Quick Actions</h2>
            <div className="mt-3 space-y-2">
              {Object.entries(quick).map(([label, prompt]) => <button type="button" key={label} onClick={() => send(prompt)} className="organic-chip w-full justify-between text-left">{label}<ArrowRight size={14} /></button>)}
              <button type="button" onClick={() => setConcept(true)} className="organic-chip w-full justify-between">Explain a Concept<ArrowRight size={14} /></button>
              <button type="button" onClick={() => navigate(`/fear-transformer/${actions.activeProfileId}`)} className="organic-chip w-full justify-between">Transform a Fear<ArrowRight size={14} /></button>
              <button type="button" onClick={() => setComingSoon(true)} className="organic-chip w-full justify-between">Summarize a Document<ArrowRight size={14} /></button>
            </div>
            {concept ? (
              <div className="mt-3">
                <input value={input} onChange={(event) => setInput(`Explain ${event.target.value} simply and ethically.`)} className="organic-input" placeholder="Which concept?" autoFocus />
                <button type="button" onClick={() => { send(input); setConcept(false); }} className="organic-button mt-2"><Sparkles size={15} /> Explain</button>
              </div>
            ) : null}
          </section>
          <section className="glass-card p-5">
            <h2 className="font-display text-lg font-bold theme-text">Live audio</h2>
            <p className="mt-2 text-sm theme-muted"><Volume2 className="inline" size={15} /> Status: {live.turnMode}</p>
            <p className="mt-1 text-xs theme-muted">Session duration: {coach.recordingSeconds}s</p>
          </section>
        </aside>
      </div>
      <ComingSoonDialog open={comingSoon} feature="Document summarization" description="Secure upload and grounded document summarization are planned for a future release." onClose={() => setComingSoon(false)} />
    </div>
  );
}
