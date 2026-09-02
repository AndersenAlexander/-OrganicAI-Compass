export type HeroVideoSource = {
  src: string;
  type: string;
};

export type HeroVideoAction = {
  label: string;
  to: string;
};

export type HeroVideoSlide = {
  id: string;
  sources: HeroVideoSource[];
  posterSrc: string;
  eyebrow: string;
  title: string;
  highlightedText?: string;
  description: string;
  primaryAction: HeroVideoAction;
  secondaryAction?: HeroVideoAction;
  tertiaryAction?: HeroVideoAction;
  objectPosition?: string;
  fallbackDurationMs?: number;
  advanceAfterMs?: number;
  loop?: boolean;
};

export const heroVideoFallbackDurationMs = 9500;

const mp4 = (encodedFileName: string): HeroVideoSource => ({
  src: `/videos/home/${encodedFileName}`,
  type: "video/mp4",
});

export const heroVideoSlides: HeroVideoSlide[] = [
  {
    id: "future-with-ai",
    sources: [mp4("0.%20OrganicAI_Compass_presentation.mp4")],
    posterSrc: "/images/organicai-hero-human-ai-bg-v2.png",
    eyebrow: "HUMAN-CENTRED AI FOR MEANINGFUL ACTION",
    title: "Design your future.",
    highlightedText: "Together with AI.",
    description:
      "OrganicAI Compass helps you understand your strengths, explore your relationship with artificial intelligence, receive grounded guidance, and turn reflection into meaningful action.",
    primaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "See How It Works", to: "/how-it-works" },
    tertiaryAction: { label: "Explore the Research", to: "/research" },
    objectPosition: "center center",
    fallbackDurationMs: 11000,
  },
  {
    id: "human-potential",
    sources: [mp4("1.%20OrganicAI_Compass_presentation_.mp4")],
    posterSrc: "/images/about/about-hero-environment.png",
    eyebrow: "BEGIN WITH THE HUMAN",
    title: "Understand your potential.",
    highlightedText: "Before asking AI where to go.",
    description:
      "Start with strengths, values, interests, concerns, and preferred ways of learning before turning guidance into action.",
    primaryAction: { label: "Explore the Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "See How It Works", to: "/how-it-works" },
    tertiaryAction: { label: "Read the Principles", to: "/principles" },
    objectPosition: "56% center",
    fallbackDurationMs: 9500,
  },
  {
    id: "final-scene-title",
    sources: [mp4("2.%20OrganicAI_Compass_final_scene_title.mp4")],
    posterSrc: "/images/about/about-final-cta.png",
    eyebrow: "A HUMAN-CENTRED FUTURE",
    title: "Your future with AI should be designed.",
    highlightedText: "Not merely predicted.",
    description:
      "Keep the human story visible while OrganicAI Compass connects reflection, guidance, and action.",
    primaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "See How It Works", to: "/how-it-works" },
    tertiaryAction: { label: "Explore the Research", to: "/research" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "academic-presentation",
    sources: [mp4("3.%20OrganicAI_Compass_academic_prese.mp4")],
    posterSrc: "/images/organicai-hero-human-ai-bg.png",
    eyebrow: "DISSERTATION PROTOTYPE",
    title: "A research-informed system.",
    highlightedText: "Ready for critical review.",
    description:
      "The homepage can now present the thesis narrative through full-width cinematic video without changing product logic.",
    primaryAction: { label: "Explore the Research", to: "/research" },
    secondaryAction: { label: "View Project Roadmap", to: "/project-roadmap" },
    tertiaryAction: { label: "Read the Principles", to: "/principles" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "diagnostic",
    sources: [mp4("4.%20OrganicAI_Compass_diagnostic.mp4")],
    posterSrc: "/images/about/about-hero-environment.png",
    eyebrow: "NATURAL DISCOVERY",
    title: "Begin with reflection.",
    highlightedText: "Then move with clarity.",
    description:
      "The diagnostic frames strengths, interests, values, AI fluency, and concerns before recommendations appear.",
    primaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "See How It Works", to: "/how-it-works" },
    tertiaryAction: { label: "Read the Principles", to: "/principles" },
    objectPosition: "56% center",
    fallbackDurationMs: 9500,
  },
  {
    id: "launch",
    sources: [mp4("5.%20OrganicAI_Compass_launch.mp4")],
    posterSrc: "/images/about/about-final-cta.png",
    eyebrow: "LAUNCH THE JOURNEY",
    title: "From insight to action.",
    highlightedText: "With agency intact.",
    description:
      "OrganicAI Compass turns exploration into practical next steps while keeping every recommendation editable.",
    primaryAction: { label: "Explore How It Works", to: "/how-it-works" },
    secondaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    tertiaryAction: { label: "Open the Journal", to: "/blog" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "career-experiment-lab",
    sources: [mp4("Career_Experiment_Lab_Evidence.mp4")],
    posterSrc: "/images/about/about-fear-to-agency.png",
    eyebrow: "CAREER EXPERIMENTS",
    title: "Test career possibilities.",
    highlightedText: "Before committing.",
    description:
      "Use low-risk experiments and evidence to explore fit, feasibility, and next steps.",
    primaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "Explore How It Works", to: "/how-it-works" },
    tertiaryAction: { label: "View Project Roadmap", to: "/project-roadmap" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "network-nodes",
    sources: [mp4("Cursor_exploring_3D_network_nodes.mp4")],
    posterSrc: "/images/about/about-fear-to-agency.png",
    eyebrow: "GROUND GUIDANCE IN KNOWLEDGE",
    title: "Turn evidence into direction.",
    highlightedText: "With sources in view.",
    description:
      "Use grounded retrieval, transparent limits, and editable recommendations to move from uncertainty to informed next steps.",
    primaryAction: { label: "Open Knowledge Base", to: "/knowledge-base" },
    secondaryAction: { label: "Explore the Research", to: "/research" },
    tertiaryAction: { label: "View Project Roadmap", to: "/project-roadmap" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "diagnostic-dashboard",
    sources: [mp4("Diagnostic_wizard_dashboard.mp4")],
    posterSrc: "/images/about/about-hero-environment.png",
    eyebrow: "HUMAN DIAGNOSTIC",
    title: "Make self-discovery visible.",
    highlightedText: "Then revise it.",
    description:
      "Structured reflection becomes a transparent profile that can be reviewed, corrected, and used in context.",
    primaryAction: { label: "Explore the Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "See How It Works", to: "/how-it-works" },
    tertiaryAction: { label: "Read the Principles", to: "/principles" },
    objectPosition: "52% center",
    fallbackDurationMs: 9500,
  },
  {
    id: "documents-platform-core",
    sources: [mp4("Documents_linking_to_platform_core.mp4")],
    posterSrc: "/images/about/about-fear-to-agency.png",
    eyebrow: "SOURCE-VISIBLE CONTEXT",
    title: "Connect guidance to knowledge.",
    highlightedText: "With limits in view.",
    description:
      "Documents, retrieved context, and transparent caveats help turn AI output into something reviewable.",
    primaryAction: { label: "Open Knowledge Base", to: "/knowledge-base" },
    secondaryAction: { label: "Explore the Research", to: "/research" },
    tertiaryAction: { label: "View Project Roadmap", to: "/project-roadmap" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "human-potential-map-interface",
    sources: [mp4("Human_Potential_Map_interface.mp4")],
    posterSrc: "/images/organicai-hero-human-ai-bg-v2.png",
    eyebrow: "HUMAN POTENTIAL MAP",
    title: "See your profile as a map.",
    highlightedText: "Not a fixed label.",
    description:
      "Strengths, values, interests, and collaboration preferences stay visible as the journey evolves.",
    primaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "See How It Works", to: "/how-it-works" },
    tertiaryAction: { label: "Read the Principles", to: "/principles" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "office-reflection",
    sources: [mp4("Man_in_office_looking_at.mp4")],
    posterSrc: "/images/about/about-hero-environment.png",
    eyebrow: "CAREER TRANSFORMATION",
    title: "Reflect on change.",
    highlightedText: "Without losing agency.",
    description:
      "OrganicAI Compass supports people navigating uncertainty, learning, creativity, and collaboration with AI.",
    primaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "Explore How It Works", to: "/how-it-works" },
    tertiaryAction: { label: "Open the Journal", to: "/blog" },
    objectPosition: "58% center",
    fallbackDurationMs: 9500,
  },
  {
    id: "node-selection",
    sources: [mp4("OrganicAI_Compass_node_selection.mp4")],
    posterSrc: "/images/about/about-fear-to-agency.png",
    eyebrow: "DISCOVERY IN CONTEXT",
    title: "Choose what matters.",
    highlightedText: "See how signals connect.",
    description:
      "The interface keeps exploration grounded in visible choices rather than hidden automation.",
    primaryAction: { label: "See How It Works", to: "/how-it-works" },
    secondaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    tertiaryAction: { label: "Explore the Research", to: "/research" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "presentation-short",
    sources: [mp4("OrganicAI_Compass_presentatio.mp4")],
    posterSrc: "/images/organicai-hero-human-ai-bg-v2.png",
    eyebrow: "ORGANICAI COMPASS",
    title: "Human plus AI collaboration.",
    highlightedText: "Designed with care.",
    description:
      "The presentation layer now supports a cinematic sequence of OrganicAI Compass videos.",
    primaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "See How It Works", to: "/how-it-works" },
    tertiaryAction: { label: "Explore the Research", to: "/research" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "presentation-main",
    sources: [mp4("OrganicAI_Compass_presentation.mp4")],
    posterSrc: "/images/about/about-final-cta.png",
    eyebrow: "PRESENTATION MODE",
    title: "Tell the full story.",
    highlightedText: "From research to prototype.",
    description:
      "Use the homepage hero to present the dissertation narrative with local, static video assets.",
    primaryAction: { label: "Explore the Research", to: "/research" },
    secondaryAction: { label: "View Project Roadmap", to: "/project-roadmap" },
    tertiaryAction: { label: "Open the Journal", to: "/blog" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "voice-coach-interface",
    sources: [mp4("OrganicAI_voice_coach_interface.mp4")],
    posterSrc: "/images/organicai-hero-human-ai-bg.png",
    eyebrow: "AI COACH",
    title: "Speak, reflect, and remain in control.",
    highlightedText: "With visible states.",
    description:
      "Voice-ready interaction supports transcript review, grounded dialogue, consent, and editing.",
    primaryAction: { label: "Open AI Coach", to: "/diagnostic" },
    secondaryAction: { label: "Read the Principles", to: "/principles" },
    tertiaryAction: { label: "Explore the Research", to: "/research" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
  {
    id: "thesis-presentation",
    sources: [mp4("Thesis_presentation_OrganicAI_Co%E2%80%A6_202607241945.mp4")],
    posterSrc: "/images/about/about-final-cta.png",
    eyebrow: "FINAL THESIS PRESENTATION",
    title: "Bring the dissertation story together.",
    highlightedText: "In one cinematic sequence.",
    description:
      "The slider can carry presentation footage, platform modules, and the final academic narrative from the same local video folder.",
    primaryAction: { label: "Start Your Diagnostic", to: "/diagnostic" },
    secondaryAction: { label: "Explore the Research", to: "/research" },
    tertiaryAction: { label: "View Project Roadmap", to: "/project-roadmap" },
    objectPosition: "center center",
    fallbackDurationMs: 9500,
  },
];
