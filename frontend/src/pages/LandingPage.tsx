import {
  ArrowRight,
  AudioWaveform,
  BookOpenCheck,
  Brain,
  Compass,
  FileCheck2,
  Mic,
  Route,
  Sparkles,
  Target,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  LivingCompass,
  LivingCompassGuideLayer,
  type CompassVoiceState,
} from "../components/landing/LivingCompass";
import { ProductDemoVideo } from "../components/landing/ProductDemoVideo";
import {
  buildHomeRoute,
  homeVideoAssets,
  type HomeRouteKey,
  type HomeVideoAssetKey,
} from "../config/homeConversionContent";
import { useAppActions } from "../hooks/useAppActions";
import { useCoach } from "../hooks/useCoach";
import type { LiveVoiceContextValue } from "../context/LiveVoiceContext";

type CompassJourneyAnchor =
  | "home-platform-intro"
  | "home-overview-video"
  | "home-product-journey"
  | "home-services"
  | "home-voice";

type CompassJourneyStep = {
  anchor: CompassJourneyAnchor;
  stage: "Discover" | "Understand" | "Strategize" | "Create" | "Grow";
  eyebrow: string;
  title: string;
  description: string;
  signals: string[];
  routeKey: HomeRouteKey;
  ctaLabel: string;
  video: HomeVideoAssetKey;
  Icon: LucideIcon;
  side: "left" | "right";
};

const compassJourney: CompassJourneyStep[] = [
  {
    anchor: "home-platform-intro",
    stage: "Discover",
    eyebrow: "01 - DISCOVER",
    title: "Start with human context before recommendations appear.",
    description:
      "Natural Discovery maps interests, preferred activities, values and working style. The compass starts by listening to what feels meaningful before it asks what is marketable.",
    signals: ["interests", "values", "working style", "natural tendencies"],
    routeKey: "diagnostic",
    ctaLabel: "Start discovery",
    video: "naturalDiscovery",
    Icon: Compass,
    side: "left",
  },
  {
    anchor: "home-overview-video",
    stage: "Understand",
    eyebrow: "02 - UNDERSTAND",
    title: "Turn responses into a visible Human Potential Map.",
    description:
      "The product separates preference, capability and evidence instead of hiding them inside one opaque score. You can inspect the signals and revise the profile as your context changes.",
    signals: ["Natural Fit", "Capability Fit", "Evidence Strength", "Transition Feasibility"],
    routeKey: "profile",
    ctaLabel: "View potential map",
    video: "humanPotential",
    Icon: Brain,
    side: "right",
  },
  {
    anchor: "home-product-journey",
    stage: "Strategize",
    eyebrow: "03 - STRATEGIZE",
    title: "Explore career hypotheses as directions to test.",
    description:
      "OrganicAI Compass shows why a direction appeared, what supports it, what is missing and which assumptions should be questioned before you commit.",
    signals: ["explainable hypotheses", "provenance", "trade-offs", "robustness"],
    routeKey: "careerCompatibility",
    ctaLabel: "Explore hypotheses",
    video: "hypotheses",
    Icon: Route,
    side: "left",
  },
  {
    anchor: "home-services",
    stage: "Create",
    eyebrow: "04 - CREATE",
    title: "Build evidence through small experiments and truthful artifacts.",
    description:
      "Mini-projects, research tasks, applications and evidence records help turn a promising idea into proof you can use, question and improve.",
    signals: ["career experiments", "evidence passport", "applications", "learning roadmap"],
    routeKey: "experiments",
    ctaLabel: "Open experiments",
    video: "experiments",
    Icon: Target,
    side: "right",
  },
  {
    anchor: "home-voice",
    stage: "Grow",
    eyebrow: "05 - GROW",
    title: "Keep recalibrating with an AI coach that stays accountable.",
    description:
      "The voice core supports reflection, explanation and next-step planning. Text remains available, voice is optional and the user stays in control of the path.",
    signals: ["voice coach", "recalibration", "reflection", "user control"],
    routeKey: "coach",
    ctaLabel: "Talk to coach",
    video: "voice",
    Icon: AudioWaveform,
    side: "left",
  },
];

const heroSignals = ["Human context", "Explainable hypotheses", "Evidence loop"];

type HomepageVoiceStatus = "ready" | "connecting" | "listening" | "speaking" | "unavailable";

const voiceStatusLabels: Record<HomepageVoiceStatus, string> = {
  ready: "READY",
  connecting: "CONNECTING",
  listening: "LISTENING",
  speaking: "SPEAKING",
  unavailable: "VOICE UNAVAILABLE",
};

function homepageVoiceStatus(voice: LiveVoiceContextValue): HomepageVoiceStatus {
  if (["requesting-permission", "requesting-token", "connecting", "reconnecting", "disconnecting"].includes(voice.connectionStatus)) {
    return "connecting";
  }
  if (voice.isSpeaking) return "speaking";
  if (voice.isListening) return "listening";
  if (voice.liveError && voice.liveErrorCode !== "VOICE_CONSENT_REQUIRED") return "unavailable";
  if (["error", "disabled", "unconfigured"].includes(voice.connectionStatus)) return "unavailable";
  return "ready";
}

function compassStateFromVoice(status: HomepageVoiceStatus): CompassVoiceState {
  if (status === "connecting") return "connecting";
  if (status === "listening") return "listening";
  if (status === "speaking") return "speaking";
  if (status === "unavailable") return "error";
  return "idle";
}

function voiceButtonLabel(status: HomepageVoiceStatus) {
  if (status === "connecting") return "Connecting...";
  if (status === "listening" || status === "speaking") return "End voice";
  if (status === "unavailable") return "Retry voice";
  return "Start voice";
}

function voiceAriaLabel(status: HomepageVoiceStatus) {
  if (status === "listening") return "OrganicAI Coach is listening. End voice conversation.";
  if (status === "speaking") return "OrganicAI Coach is speaking. End voice conversation.";
  if (status === "connecting") return "OrganicAI Coach is connecting.";
  if (status === "unavailable") return "Retry OrganicAI Coach voice conversation.";
  return "Start voice conversation with OrganicAI Coach.";
}

function CompassHero({
  voiceState,
  voiceStatus,
  voiceError,
  onToggleVoice,
  isVoiceActionPending,
  showConsent,
  onApproveConsent,
  onUseText,
}: {
  voiceState: CompassVoiceState;
  voiceStatus: HomepageVoiceStatus;
  voiceError: string;
  onToggleVoice: () => void;
  isVoiceActionPending: boolean;
  showConsent: boolean;
  onApproveConsent: () => void;
  onUseText: () => void;
}) {
  const statusLabel = voiceStatusLabels[voiceStatus];
  return (
    <section
      id="living-compass"
      className="home-compass-hero home-conversion-section"
      data-compass-anchor="center"
      data-testid="home-living-compass"
    >
      <div className="home-compass-hero__artwork" aria-hidden="true">
        <img
          src="/images/organicai-hero-guidance-v3.png"
          alt=""
          decoding="async"
          fetchPriority="high"
        />
      </div>
      <div className="home-compass-hero__copy">
        <p className="home-eyebrow">LIVING COMPASS EXPERIENCE</p>
        <h1>OrganicAI Compass</h1>
        <p>
          A career decision-support platform where the logo becomes the guide: a living compass that listens, explains
          and moves with the user from self-discovery to evidence-based action.
        </p>
        <div className="home-compass-hero__actions">
          <Link className="home-button" to="/diagnostic">
            <Sparkles size={16} /> Start diagnostic
          </Link>
          <button
            type="button"
            data-testid="home-voice-action"
            onClick={onToggleVoice}
            disabled={isVoiceActionPending}
            aria-label={voiceAriaLabel(voiceStatus)}
          >
            <Mic size={16} /> {voiceButtonLabel(voiceStatus)}
          </button>
          <Link to="/how-it-works">
            See how it works <ArrowRight size={15} />
          </Link>
        </div>
        {voiceError ? <p className="home-compass-hero__voice-error" role="status">{voiceError}</p> : null}
        {voiceStatus === "unavailable" ? (
          <button type="button" className="home-compass-hero__text-fallback" onClick={onUseText}>
            Continue in text
          </button>
        ) : null}
        {showConsent ? (
          <section className="home-compass-hero__voice-consent" role="dialog" aria-label="Voice consent">
            <p>
              Live voice uses ElevenLabs to process microphone audio, detect conversation turns, transcribe speech and
              generate the agent&apos;s voice. OrganicAI stores text transcripts only when transcript history is enabled and
              does not store live audio files by default.
            </p>
            <div>
              <button type="button" onClick={onApproveConsent}>
                Start live conversation
              </button>
              <button type="button" onClick={onUseText}>
                Use text instead
              </button>
            </div>
          </section>
        ) : null}
        <div className="home-compass-hero__signals" aria-label="OrganicAI Compass signals">
          {heroSignals.map((signal) => (
            <span key={signal}>{signal}</span>
          ))}
        </div>
      </div>

      <div className="home-compass-hero__visual">
        <div className="home-compass-hero__orbital-field" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div className="home-compass-hero__anchor" data-living-compass-anchor="hero">
          <span />
          <span />
          <span />
          <div className="home-compass-hero__preview">
            <LivingCompass
              size="guide"
              state={voiceState}
              showPath={false}
              showLabels={false}
              voiceConnectionStatus={voiceStatus}
              aria-label="Decorative Living Compass preview"
            />
          </div>
          <div className="home-compass-hero__voice-state" data-state={voiceState} data-status={voiceStatus} aria-live="polite">
            <span>OrganicAI Coach</span>
            <b>{statusLabel}</b>
          </div>
        </div>
      </div>
    </section>
  );
}

function CompassJourneySection({
  step,
  activeProfileId,
}: {
  step: CompassJourneyStep;
  activeProfileId: string;
}) {
  const video = homeVideoAssets[step.video];
  const Icon = step.Icon;

  return (
    <section
      id={step.stage.toLowerCase()}
      className={`home-compass-section home-compass-section--${step.side} home-conversion-section`}
      data-compass-anchor={step.side}
      data-testid={step.anchor}
    >
      <div className="home-compass-section__copy">
        <div className="home-compass-section__kicker">
          <Icon size={20} />
          <span>{step.eyebrow}</span>
        </div>
        <h2>{step.title}</h2>
        <p>{step.description}</p>
        <ul className="home-compass-section__signals" aria-label={`${step.stage} signals`}>
          {step.signals.map((signal) => (
            <li key={signal}>
              <span />
              {signal}
            </li>
          ))}
        </ul>
        <Link className="home-compass-section__link" to={buildHomeRoute(step.routeKey, activeProfileId)}>
          {step.ctaLabel} <ArrowRight size={15} />
        </Link>
      </div>

      <div className="home-compass-section__media">
        <div className="home-compass-section__stage-label" aria-hidden="true">
          {step.stage}
        </div>
        <ProductDemoVideo
          src={video.src}
          poster={video.poster}
          title={video.title}
          caption={video.caption}
          controls={false}
          muted
          loop
          autoPlay
          preload="metadata"
          testId={`home-compass-video-${step.stage.toLowerCase()}`}
        />
      </div>
    </section>
  );
}

function CompassFooterDock({
  voiceStatus,
  onToggleVoice,
  isVoiceActionPending,
}: {
  voiceStatus: HomepageVoiceStatus;
  onToggleVoice: () => void;
  isVoiceActionPending: boolean;
}) {
  return (
    <section
      className="home-compass-dock home-conversion-section"
      data-compass-anchor="center"
      data-testid="home-final-conversion"
    >
      <div className="home-compass-dock__content">
        <p className="home-eyebrow">PATH COMPLETE</p>
        <h2>The compass docks where the next decision begins.</h2>
        <p>
          Start with Natural Discovery, then let evidence, experiments and coaching keep the direction honest as your
          career context changes.
        </p>
        <div className="home-compass-dock__actions">
          <Link className="home-button" to="/diagnostic">
            Start your diagnostic <ArrowRight size={16} />
          </Link>
          <button type="button" onClick={onToggleVoice} disabled={isVoiceActionPending} aria-label={voiceAriaLabel(voiceStatus)}>
            <Mic size={16} /> {voiceButtonLabel(voiceStatus)}
          </button>
        </div>
      </div>
      <div className="home-compass-dock__compass">
        <div className="home-compass-dock__placeholder" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div className="home-compass-dock__artifacts" aria-hidden="true">
          <BookOpenCheck size={22} />
          <FileCheck2 size={22} />
          <Compass size={22} />
        </div>
      </div>
    </section>
  );
}

function LiveVoiceDebug({
  voice,
  semanticState,
}: {
  voice: LiveVoiceContextValue;
  semanticState: CompassVoiceState;
}) {
  return (
    <div className="home-live-voice-debug" aria-label="Live voice diagnostics">
      <span>Provider: {voice.providerStatus?.provider || "unknown"}</span>
      <span>Connection: {voice.connectionStatus}</span>
      <span>Compass: {semanticState}</span>
      <span>Mic: {voice.inputLevel.toFixed(2)}</span>
      <span>Output: {voice.outputLevel.toFixed(2)}</span>
      <span>Turn: {voice.turnMode}</span>
    </div>
  );
}

export function LandingPage() {
  document.title = "OrganicAI Compass - Design your future with AI";
  const { activeProfileId, openCoach } = useAppActions();
  const coach = useCoach();
  const liveVoice = coach.liveVoice;
  const [showConsent, setShowConsent] = useState(false);
  const voiceStatus = homepageVoiceStatus(liveVoice);
  const voiceState = compassStateFromVoice(voiceStatus);
  const isVoiceActionPending = voiceStatus === "connecting";
  const voiceError = voiceStatus === "unavailable"
    ? liveVoice.liveError || "Voice is temporarily unavailable. You can continue in text."
    : "";
  const showDiagnostics = import.meta.env.DEV && new URLSearchParams(window.location.search).get("voice-debug") === "1";

  const toggleVoice = () => {
    if (isVoiceActionPending) return;
    if (liveVoice.isConnected) {
      void liveVoice.endLiveConversation();
      return;
    }
    coach.setPreferences({ voiceMode: "live" });
    if (!coach.preferences.voiceConsent) {
      setShowConsent(true);
      return;
    }
    void liveVoice.startLiveConversation();
  };

  const approveConsentAndStart = () => {
    coach.setPreferences({ voiceMode: "live", voiceConsent: true });
    setShowConsent(false);
    void liveVoice.approveVoiceConsentAndStart();
  };

  const continueInText = () => {
    setShowConsent(false);
    openCoach();
  };

  return (
    <div className="home-page home-page--living-compass">
      <LivingCompassGuideLayer
        voiceState={voiceState}
        onVoiceCoreClick={toggleVoice}
        voiceConnectionStatus={voiceStatus}
        voiceAriaLabel={voiceAriaLabel(voiceStatus)}
      />
      <div className="home-compass-shell">
        <CompassHero
          voiceState={voiceState}
          voiceStatus={voiceStatus}
          voiceError={voiceError}
          onToggleVoice={toggleVoice}
          isVoiceActionPending={isVoiceActionPending}
          showConsent={showConsent}
          onApproveConsent={approveConsentAndStart}
          onUseText={continueInText}
        />
        <div className="home-compass-journey" aria-label="OrganicAI Compass guided journey">
          {compassJourney.map((step) => (
            <CompassJourneySection key={step.stage} activeProfileId={activeProfileId} step={step} />
          ))}
        </div>
        <CompassFooterDock voiceStatus={voiceStatus} onToggleVoice={toggleVoice} isVoiceActionPending={isVoiceActionPending} />
        {showDiagnostics ? <LiveVoiceDebug voice={liveVoice} semanticState={voiceState} /> : null}
      </div>
    </div>
  );
}
