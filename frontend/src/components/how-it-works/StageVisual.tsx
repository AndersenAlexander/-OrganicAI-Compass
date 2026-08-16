import {
  Bot,
  Compass,
  MessageCircle,
  Orbit,
  RefreshCw,
  Sparkles,
  Target
} from "lucide-react";
import type { CSSProperties } from "react";

type StageVisualProps = {
  stageId: string;
  compact?: boolean;
};

export function StageVisual({ stageId, compact = false }: StageVisualProps) {
  return (
    <div className={`journey-visual journey-visual-${stageId} ${compact ? "compact" : ""}`} aria-hidden="true">
      {stageId === "intention" ? <IntentionVisual /> : null}
      {stageId === "diagnostic" ? <DiagnosticVisual /> : null}
      {stageId === "potential-map" ? <PotentialMapVisual /> : null}
      {stageId === "ai-coach" ? <CoachVisual /> : null}
      {stageId === "roadmap" ? <RoadmapVisual /> : null}
      {stageId === "growth" ? <GrowthVisual /> : null}
    </div>
  );
}

function IntentionVisual() {
  return (
    <>
      <div className="journey-target">
        <span />
        <Target size={28} />
        <Compass size={18} />
      </div>
      <div className="journey-chip-cloud">
        <span>Understand career direction</span>
        <span>Improve AI skills</span>
        <span>Build with AI creatively</span>
        <span>Navigate uncertainty</span>
      </div>
    </>
  );
}

function DiagnosticVisual() {
  return (
    <>
      <div className="journey-diagnostic-rail">
        {["Interests", "Fears", "Values", "Skills", "AI fit"].map((step, index) => (
          <span key={step} style={{ "--step": index } as CSSProperties}>
            {step}
          </span>
        ))}
      </div>
      <div className="journey-waveform">
        {Array.from({ length: 18 }).map((_, index) => (
          <i key={index} style={{ "--bar": index } as CSSProperties} />
        ))}
      </div>
      <div className="journey-answer-tags">
        <span>What energizes you?</span>
        <span>What concerns you about AI?</span>
        <span>What do you want to contribute?</span>
      </div>
    </>
  );
}

function PotentialMapVisual() {
  const nodes = ["Talents", "Values", "Creativity", "AI Collaboration", "Contribution", "Next Steps"];
  return (
    <div className="journey-map-mini">
      <span className="journey-map-core">
        <Orbit size={30} />
      </span>
      {nodes.map((node, index) => (
        <span className={`journey-map-node node-${index}`} key={node}>
          {node}
        </span>
      ))}
    </div>
  );
}

function CoachVisual() {
  return (
    <div className="journey-coach-mini">
      <span className="journey-coach-orb">
        <Bot size={30} />
      </span>
      <div className="journey-chat-bubble user">
        <MessageCircle size={14} />
        How do I build trust with AI?
      </div>
      <div className="journey-chat-bubble answer">
        <Sparkles size={14} />
        Start with transparency, shared goals, and small experiments.
      </div>
      <div className="journey-source-row">
        <span>AI Literacy</span>
        <span>Responsible AI</span>
      </div>
    </div>
  );
}

function RoadmapVisual() {
  return (
    <div className="journey-roadmap-mini">
      {[
        ["7 Days", "Clarify one AI use case", "74%"],
        ["30 Days", "Practice a co-creation workflow", "48%"],
        ["6 Months", "Ship a contribution project", "22%"],
      ].map(([label, text, progress]) => (
        <div key={label}>
          <strong>{label}</strong>
          <span>{text}</span>
          <i>
            <b style={{ width: progress }} />
          </i>
        </div>
      ))}
    </div>
  );
}

function GrowthVisual() {
  return (
    <div className="journey-growth-mini">
      <div className="journey-growth-ring">
        <RefreshCw size={24} />
        <span>68%</span>
      </div>
      <svg viewBox="0 0 260 110" role="img" aria-label="">
        <path d="M18 88 C 58 68, 76 74, 108 52 S 166 28, 240 24" />
        <circle cx="108" cy="52" r="5" />
        <circle cx="240" cy="24" r="5" />
      </svg>
      <span className="journey-recalibration">Recalibrate next action</span>
    </div>
  );
}
