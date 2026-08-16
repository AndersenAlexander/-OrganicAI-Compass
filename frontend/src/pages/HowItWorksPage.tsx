import {
  Bot,
  ClipboardCheck,
  Compass,
  Database,
  Map,
  MessageCircle,
  Network,
  Orbit,
  RefreshCw,
  Route,
} from "lucide-react";
import { lazy, Suspense, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { HowItWorksFinalCTA } from "../components/how-it-works/HowItWorksFinalCTA";
import { JourneyStageCard } from "../components/how-it-works/JourneyStageCard";
import { JourneyStageNavigator } from "../components/how-it-works/JourneyStageNavigator";
import { JourneyStagePreview } from "../components/how-it-works/JourneyStagePreview";
import { PrivacyControlSection } from "../components/how-it-works/PrivacyControlSection";
import { RagJourneyPanel } from "../components/how-it-works/RagJourneyPanel";
import { TechnicalPipeline } from "../components/how-it-works/TechnicalPipeline";
import type { JourneyStage, PipelineLayer } from "../components/how-it-works/types";
import { JourneyFlowFallback } from "../components/three/JourneyFlowFallback";
import { PublicPageShell } from "../components/public/PublicPageShell";
import { useAppActions } from "../hooks/useAppActions";

const JourneyFlowScene = lazy(() =>
  import("../components/three/JourneyFlowScene").then((module) => ({ default: module.JourneyFlowScene }))
);

const pipelineLayers: PipelineLayer[] = [
  {
    icon: MessageCircle,
    title: "Input Layer",
    labels: ["Voice", "Text", "Diagnostic responses"],
    description: "The journey starts from typed questions, voice input, and structured reflection data.",
  },
  {
    icon: Network,
    title: "Application Layer",
    labels: ["React", "TypeScript", "FastAPI"],
    description: "The interface, routes, and API boundary organize the user's active journey state.",
  },
  {
    icon: Database,
    title: "Knowledge Layer",
    labels: ["Curated Markdown", "Embeddings", "Cosine retrieval"],
    description: "Research-informed sources are retrieved before grounded AI answers are composed.",
  },
  {
    icon: Bot,
    title: "Intelligence Layer",
    labels: ["OpenAI generation", "Recommendations", "Profile context"],
    description: "The system combines retrieved context with the user's profile and current goal.",
  },
  {
    icon: Map,
    title: "Output Layer",
    labels: ["Potential Map", "Coach answer", "Roadmap", "Report"],
    description: "The output becomes a visible map, grounded answer, roadmap action, or exportable report.",
  },
];

export function HowItWorksPage() {
  document.title = "OrganicAI Compass - How It Works";
  const { activeProfileId } = useAppActions();
  const profileTo = activeProfileId ? `/profile/${activeProfileId}` : "/diagnostic";
  const coachTo = activeProfileId ? `/coach/${activeProfileId}` : "/diagnostic";
  const roadmapTo = activeProfileId ? `/roadmap/${activeProfileId}` : "/diagnostic";
  const [activeStage, setActiveStage] = useState(0);

  const stages = useMemo<JourneyStage[]>(
    () => [
      {
        id: "intention",
        number: "01",
        shortTitle: "Intention",
        title: "Set Your Intention",
        cardTitle: "Set Your Intention",
        description: "The user clarifies what they want to understand, improve, or create with AI.",
        cardDescription: "Clarify what you want to understand, improve, or create with AI.",
        exampleLabel: "Example focus areas",
        examples: ["Understand career direction", "Improve AI skills", "Build with AI creatively", "Navigate uncertainty"],
        action: "Start Diagnostic",
        to: "/diagnostic",
        icon: Compass,
        accent: "teal",
      },
      {
        id: "diagnostic",
        number: "02",
        shortTitle: "Diagnostic",
        title: "Complete the Human Diagnostic",
        cardTitle: "Complete the Diagnostic",
        description:
          "A guided five-step reflection captures interests, fears, values, skills, learning style, and AI experience.",
        cardDescription: "A guided reflection captures interests, fears, values, skills, learning style, and AI experience.",
        exampleLabel: "Example prompts",
        examples: ["What energizes you?", "What concerns you about AI?", "What do you want to contribute?"],
        action: "Start Diagnostic",
        to: "/diagnostic",
        icon: ClipboardCheck,
        accent: "cyan",
      },
      {
        id: "potential-map",
        number: "03",
        shortTitle: "Potential Map",
        title: "Generate the Human Potential Map",
        cardTitle: "Generate Potential Map",
        description:
          "OrganicAI transforms responses into an exploratory profile of talents, values, creativity, AI collaboration, contribution domains, and next steps.",
        cardDescription: "Responses become an exploratory profile of talents, values, creativity, collaboration, and next steps.",
        exampleLabel: "Mapped dimensions",
        examples: ["Talents", "Values", "Creativity", "AI Collaboration", "Contribution", "Next Steps"],
        action: "View Demo Map",
        to: profileTo,
        icon: Orbit,
        accent: "green",
      },
      {
        id: "ai-coach",
        number: "04",
        shortTitle: "AI Coach",
        title: "Talk with the AI Coach",
        cardTitle: "Talk with AI Coach",
        description:
          "The user explores questions through text or voice while the coach retrieves relevant knowledge before generating an answer.",
        cardDescription: "Ask through text or voice while the coach retrieves relevant knowledge before answering.",
        exampleLabel: "Grounded answer elements",
        examples: ["User message", "Retrieved sources", "Confidence note", "Ethical note"],
        action: "Open AI Coach",
        to: coachTo,
        icon: Bot,
        accent: "violet",
      },
      {
        id: "roadmap",
        number: "05",
        shortTitle: "Roadmap",
        title: "Create a Personalized Roadmap",
        cardTitle: "Create Roadmap",
        description: "OrganicAI generates practical actions for seven days, thirty days, and six months.",
        cardDescription: "Generate practical actions for seven days, thirty days, and six months.",
        exampleLabel: "Planning horizons",
        examples: ["7 Days", "30 Days", "6 Months"],
        action: "View Roadmap",
        to: roadmapTo,
        icon: Route,
        accent: "gold",
      },
      {
        id: "growth",
        number: "06",
        shortTitle: "Growth",
        title: "Reflect, Adapt, and Grow",
        cardTitle: "Reflect and Grow",
        description:
          "The user tracks progress, revisits recommendations, and recalibrates the roadmap as goals and circumstances change.",
        cardDescription: "Track progress, revisit recommendations, and recalibrate as goals change.",
        exampleLabel: "Growth loop",
        examples: ["Reflect", "Adapt", "Recalibrate", "Continue"],
        action: "Open My Journey",
        to: "/my-journey",
        icon: RefreshCw,
        accent: "lime",
      },
    ],
    [coachTo, profileTo, roadmapTo]
  );

  const selectedStage = stages[activeStage];

  return (
    <PublicPageShell>
      <div className="how-page how-it-works-page">
        <div className="how-page-atmosphere" aria-hidden="true">
          <span className="how-page-particles" />
          <span className="how-page-curve curve-a" />
          <span className="how-page-curve curve-b" />
          <span className="how-page-botanical botanical-a" />
          <span className="how-page-botanical botanical-b" />
        </div>
        <div className="how-page-container how-page-main">
          <motion.section
            className="how-hero"
            aria-labelledby="how-hero-title"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
          >
            <div className="how-hero-copy">
              <motion.p className="how-hero-eyebrow" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                THE ORGANICAI JOURNEY
              </motion.p>
              <motion.h1
                id="how-hero-title"
                className="how-hero-title"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.08 }}
              >
                <span>From reflection to</span>
                <span className="how-hero-title-accent">meaningful action</span>
              </motion.h1>
              <motion.p
                className="how-hero-description"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.16 }}
              >
                OrganicAI Compass combines diagnostic reflection, grounded AI, voice coaching, personalized
                recommendations, and adaptive roadmaps into one human-centred journey.
              </motion.p>
              <motion.div
                className="how-hero-actions"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.22 }}
              >
                <Link className="public-button" to="/diagnostic">
                  Begin the Journey
                </Link>
                <Link className="public-button secondary" to="/principles">
                  Explore the Principles
                </Link>
              </motion.div>
            </div>
            <motion.div
              className="how-hero-scene"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.18, duration: 0.48 }}
            >
              <div className="how-hero-scene-soft-edge" aria-hidden="true" />
              <Suspense fallback={<JourneyFlowFallback />}>
                <JourneyFlowScene />
              </Suspense>
            </motion.div>
          </motion.section>

          <section className="journey-dashboard" aria-label="Interactive journey dashboard">
            <JourneyStageNavigator stages={stages} activeIndex={activeStage} onSelect={setActiveStage} />
            <JourneyStagePreview stage={selectedStage} />
          </section>

          <section className="how-page-section journey-stage-section" aria-labelledby="journey-stages-title">
            <header className="how-section-heading">
              <p>FULL JOURNEY</p>
              <h2 id="journey-stages-title">Six connected stages, not isolated tools</h2>
              <span>Each stage turns reflection into a concrete interface, output, and next action.</span>
            </header>
            <div className="journey-stage-grid">
              {stages.map((stage) => (
                <JourneyStageCard key={stage.id} stage={stage} />
              ))}
            </div>
          </section>

          <TechnicalPipeline layers={pipelineLayers} />
          <RagJourneyPanel />
          <PrivacyControlSection />
          <HowItWorksFinalCTA coachTo={coachTo} />
        </div>
      </div>
    </PublicPageShell>
  );
}
