import { AudioWaveform, Bot, Compass, Database, LockKeyhole, Sparkles } from "lucide-react";

const features = [
  { title: "Voice Interaction", description: "Speak naturally. Get clarity instantly.", icon: AudioWaveform },
  { title: "OpenAI + ElevenLabs", description: "Powerful AI models. Human-like voice.", icon: Bot },
  { title: "RAG Knowledge Base", description: "Trusted insights from curated sources.", icon: Database },
  { title: "Personalized Recommendations", description: "Tailored to you. Adaptive over time.", icon: Sparkles },
  { title: "Guided Roadmap", description: "Step-by-step paths to transformation.", icon: Compass },
  { title: "Privacy First", description: "Your data is yours. Always.", icon: LockKeyhole }
];

export function FeatureStrip() {
  return (
    <section className="landing-page-container landing-feature-strip">
      {features.map(({ title, description, icon: Icon }, index) => (
        <article key={title} className={`landing-feature-item ${index > 0 ? "landing-feature-divider" : ""}`}>
          <span className="landing-feature-icon"><Icon size={16} /></span>
          <span>
            <span className="landing-feature-title">{title}</span>
            <span className="landing-feature-description">{description}</span>
          </span>
        </article>
      ))}
    </section>
  );
}
