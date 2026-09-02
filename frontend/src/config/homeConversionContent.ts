export type HomeVideoAssetKey =
  | "overview"
  | "naturalDiscovery"
  | "careerInterests"
  | "humanPotential"
  | "capability"
  | "hypotheses"
  | "experiments"
  | "evidence"
  | "market"
  | "application"
  | "interview"
  | "decision"
  | "voice";

export type HomeRouteKey =
  | "diagnostic"
  | "howItWorks"
  | "research"
  | "principles"
  | "systemCard"
  | "blog"
  | "knowledgeBase"
  | "careers"
  | "profile"
  | "coach"
  | "recommendations"
  | "roadmap"
  | "assessment"
  | "careerCompatibility"
  | "careerCompare"
  | "experiments"
  | "evidencePassport"
  | "marketRadar"
  | "jobAnalyzer"
  | "applications"
  | "interviews"
  | "starStories"
  | "offerReview"
  | "careerEncyclopedia"
  | "browserExtension"
  | "adaptiveExperiments"
  | "transitionSimulator"
  | "recommendationRobustness"
  | "syntheticFairness"
  | "learning"
  | "jobLoss";

export type HomeJourneyStep = {
  id: string;
  eyebrow: string;
  shortLabel: string;
  title: string;
  description: string;
  gain: string;
  signals: string[];
  video?: HomeVideoAssetKey;
  routeKey: HomeRouteKey;
  ctaLabel: string;
  layout: "media-left" | "media-right" | "wide" | "model" | "recalibration" | "decision";
};

export type HomeServiceGroup = {
  id: string;
  title: string;
  description: string;
  capabilities: string[];
  routeKey: HomeRouteKey;
  ctaLabel: string;
  tone: "teal" | "green" | "cyan" | "violet" | "gold";
  wide?: boolean;
};

export const homeVideoAssets: Record<
  HomeVideoAssetKey,
  { src: string; poster: string; title: string; caption: string }
> = {
  overview: {
    src: "/videos/home/OrganicAI_Compass_presentation.mp4",
    poster: "/images/organicai-hero-human-ai-bg-v2.png",
    title: "OrganicAI Compass product overview video",
    caption: "User-controlled platform overview. Audio starts only after pressing Play.",
  },
  naturalDiscovery: {
    src: "/videos/home/Diagnostic_wizard_dashboard.mp4",
    poster: "/images/about/about-hero-environment.png",
    title: "Natural Discovery diagnostic interface",
    caption: "Diagnostic flow and dashboard preview.",
  },
  careerInterests: {
    src: "/videos/home/OrganicAI_Compass_node_selection.mp4",
    poster: "/images/organicai-hero-human-ai-bg-v2.png",
    title: "RIASEC-inspired Career Interests interface",
    caption: "Career interest signals shown as one part of Natural Fit.",
  },
  humanPotential: {
    src: "/videos/home/Human_Potential_Map_interface.mp4",
    poster: "/images/about/about-hero-environment.png",
    title: "Human Potential Map interface",
    caption: "Profile interpretation that remains visible and revisable.",
  },
  capability: {
    src: "/videos/home/4.%20OrganicAI_Compass_diagnostic.mp4",
    poster: "/images/about/about-fear-to-agency.png",
    title: "Capability assessment interface",
    caption: "Skills, experience, goals, constraints, and readiness signals.",
  },
  hypotheses: {
    src: "/videos/home/OrganicAI_Compass_presentatio.mp4",
    poster: "/images/organicai-hero-human-ai-bg.png",
    title: "Career hypotheses interface",
    caption: "Explainable directions worth testing.",
  },
  experiments: {
    src: "/videos/home/Career_Experiment_Lab_Evidence.mp4",
    poster: "/images/about/about-final-cta.png",
    title: "Career Experiment Lab evidence video",
    caption: "Small experiments turn uncertainty into evidence.",
  },
  evidence: {
    src: "/videos/home/Documents_linking_to_platform_core.mp4",
    poster: "/images/about/about-fear-to-agency.png",
    title: "Evidence Passport and document linkage video",
    caption: "Claims are separated from demonstrated evidence.",
  },
  market: {
    src: "/videos/home/3.%20OrganicAI_Compass_academic_prese.mp4",
    poster: "/images/organicai-hero-human-ai-bg-v2.png",
    title: "Market context and job analysis video",
    caption: "Job requirements and market context are compared with the profile.",
  },
  application: {
    src: "/videos/home/5.%20OrganicAI_Compass_launch.mp4",
    poster: "/images/about/about-final-cta.png",
    title: "Application journey video",
    caption: "Evidence-grounded application preparation.",
  },
  interview: {
    src: "/videos/home/Man_in_office_looking_at.mp4",
    poster: "/images/organicai-hero-human-ai-bg.png",
    title: "Interview preparation video",
    caption: "Prepare with evidence and reflective practice.",
  },
  decision: {
    src: "/videos/home/Cursor_exploring_3D_network_nodes.mp4",
    poster: "/images/organicai-hero-human-ai-bg-v2.png",
    title: "Decision intelligence network video",
    caption: "Trade-offs, provenance, robustness, and research checks.",
  },
  voice: {
    src: "/videos/home/OrganicAI_voice_coach_interface.mp4",
    poster: "/images/organicai-hero-human-ai-bg.png",
    title: "OrganicAI Coach voice interaction video",
    caption: "Voice-enabled coaching where configuration and consent allow it.",
  },
};

export const homeJourneySteps: HomeJourneyStep[] = [
  {
    id: "natural-discovery",
    eyebrow: "01 - NATURAL DISCOVERY",
    shortLabel: "Natural Discovery",
    title: "Start with what attracts you, not only with what you have done before.",
    description:
      "OrganicAI begins with interests, preferred activities, work values, working style, and natural tendencies. It is a reflective discovery flow, not a psychological diagnosis.",
    gain: "A clearer view of the kinds of professional activity that currently feel meaningful and engaging.",
    signals: ["interests", "preferred activities", "work values", "working style"],
    video: "naturalDiscovery",
    routeKey: "diagnostic",
    ctaLabel: "Start discovery",
    layout: "media-right",
  },
  {
    id: "career-interests",
    eyebrow: "02 - CAREER INTERESTS",
    shortLabel: "Career Interests",
    title: "Explore the types of work that naturally attract you.",
    description:
      "RIASEC-inspired Career Interests cover Realistic, Investigative, Artistic, Social, Enterprising, and Conventional work patterns. They are one component of Natural Fit, not a fixed identity label.",
    gain: "A language for describing attractive work patterns without confusing interest with current capability.",
    signals: ["Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"],
    video: "careerInterests",
    routeKey: "diagnostic",
    ctaLabel: "Explore interests",
    layout: "media-left",
  },
  {
    id: "human-potential",
    eyebrow: "03 - HUMAN POTENTIAL",
    shortLabel: "Human Potential",
    title: "Turn your responses into a clearer picture of your potential.",
    description:
      "Natural Tendencies, Career Interests, values, and work preferences become a visible Human Potential Map. Capabilities and evidence can enrich the profile later as the journey becomes more concrete.",
    gain: "A revisable interpretation that helps you see patterns before acting on them.",
    signals: ["Natural Tendencies", "Career Interests", "Values", "Work Preferences"],
    video: "humanPotential",
    routeKey: "profile",
    ctaLabel: "View potential map",
    layout: "media-right",
  },
  {
    id: "capability-assessment",
    eyebrow: "04 - CAPABILITY ASSESSMENT",
    shortLabel: "Capability Assessment",
    title: "Understand what you can do today.",
    description:
      "Capability Assessment looks at skills, education, professional experience, transferable strengths, AI readiness, learning exposure, goals, and constraints. Interest is not capability.",
    gain: "A clearer separation between attraction, current ability, and development needs.",
    signals: ["skills", "education", "experience", "transferable skills", "AI readiness"],
    video: "capability",
    routeKey: "assessment",
    ctaLabel: "Assess capability",
    layout: "media-left",
  },
  {
    id: "four-layer-model",
    eyebrow: "05 - FOUR-LAYER CAREER MODEL",
    shortLabel: "Four-Layer Model",
    title: "Four questions. Four different answers.",
    description:
      "OrganicAI separates Natural Fit, Capability Fit, Evidence Strength, and Transition Feasibility so a career direction can be explored without collapsing every signal into one opaque score.",
    gain: "A decision model that distinguishes attraction, ability, proof, and realistic timing.",
    signals: ["Natural Fit", "Capability Fit", "Evidence Strength", "Transition Feasibility"],
    routeKey: "careerCompatibility",
    ctaLabel: "See compatibility",
    layout: "model",
  },
  {
    id: "career-hypotheses",
    eyebrow: "06 - CAREER HYPOTHESES",
    shortLabel: "Career Hypotheses",
    title: "Explore directions worth testing, not predictions about your future.",
    description:
      "Each Career Hypothesis can show why it appeared, what supports it, what is missing, and what could be tested next. The output is explainable, revisable, testable, and user-controlled.",
    gain: "A set of candidate directions that can be questioned before being followed.",
    signals: ["why this appeared", "supporting signals", "missing evidence", "next test"],
    video: "hypotheses",
    routeKey: "careerCompatibility",
    ctaLabel: "Explore hypotheses",
    layout: "wide",
  },
  {
    id: "career-experiments",
    eyebrow: "07 - CAREER EXPERIMENTS",
    shortLabel: "Career Experiments",
    title: "Test a direction before making a major commitment.",
    description:
      "Mini-projects, research tasks, design challenges, coding challenges, and communication exercises help reduce uncertainty, generate evidence, and learn from action.",
    gain: "Evidence from doing, not only from imagining the role.",
    signals: ["mini-project", "research task", "design challenge", "coding challenge", "communication exercise"],
    video: "experiments",
    routeKey: "experiments",
    ctaLabel: "Open experiments",
    layout: "media-right",
  },
  {
    id: "evidence-passport",
    eyebrow: "08 - EVIDENCE PASSPORT",
    shortLabel: "Evidence Passport",
    title: "Separate what you believe you can do from what you can demonstrate.",
    description:
      "Evidence can come from projects, professional work, education, certifications, Career Experiments, and portfolio material. A self-reported skill is not automatically treated as demonstrated evidence.",
    gain: "A more truthful record of proof, gaps, and claims that still need support.",
    signals: ["projects", "professional work", "education", "certifications", "portfolio"],
    video: "evidence",
    routeKey: "evidencePassport",
    ctaLabel: "Open evidence passport",
    layout: "media-left",
  },
  {
    id: "recalibration",
    eyebrow: "09 - RECALIBRATION",
    shortLabel: "Recalibration",
    title: "When the evidence changes, your career hypothesis can change too.",
    description:
      "OrganicAI distinguishes changes in preferences, capabilities, evidence, constraints, and market context. The point is not to defend an old recommendation, but to update it honestly.",
    gain: "A path that can adapt when new information becomes available.",
    signals: ["preferences", "capabilities", "evidence", "constraints", "market context"],
    routeKey: "roadmap",
    ctaLabel: "Review roadmap",
    layout: "recalibration",
  },
  {
    id: "market-context",
    eyebrow: "10 - MARKET CONTEXT",
    shortLabel: "Market Context",
    title: "Compare your direction with actual job requirements.",
    description:
      "Market Radar and Job Analyzer help inspect skills, education, language, experience, tools, and evidence gaps. The homepage does not claim hiring probability.",
    gain: "A practical view of what a target role asks for and what remains to prepare.",
    signals: ["Market Radar", "Job Analyzer", "skills requirements", "education requirements", "evidence gaps"],
    video: "market",
    routeKey: "marketRadar",
    ctaLabel: "Explore market context",
    layout: "media-right",
  },
  {
    id: "application-journey",
    eyebrow: "11 - APPLICATION JOURNEY",
    shortLabel: "Application Journey",
    title: "Turn your evidence into a truthful application.",
    description:
      "The Master Career Profile, application-specific profiles, CV versions, cover letters, Evidence Lock, Application Readiness, and Application Tracker keep application facts grounded.",
    gain: "Applications that communicate evidence without silently turning unsupported claims into facts.",
    signals: ["Master Career Profile", "CV versions", "cover letters", "Evidence Lock", "Application Tracker"],
    video: "application",
    routeKey: "applications",
    ctaLabel: "Open applications",
    layout: "media-left",
  },
  {
    id: "interview-journey",
    eyebrow: "12 - INTERVIEW PREPARATION",
    shortLabel: "Interview Journey",
    title: "Prepare with evidence, not invented answers.",
    description:
      "STAR Story Library, interview preparation, practice questions, mock interviews, panel simulation, reflection, and offer review help connect answers to lived examples. Voice can support practice where enabled.",
    gain: "Interview preparation that stays grounded in evidence and reflection.",
    signals: ["STAR stories", "practice questions", "mock interviews", "panel simulation", "offer review"],
    video: "interview",
    routeKey: "interviews",
    ctaLabel: "Prepare interview",
    layout: "media-right",
  },
  {
    id: "decision-intelligence",
    eyebrow: "13 - DECISION INTELLIGENCE",
    shortLabel: "Decision Intelligence",
    title: "Understand why a direction appears and how robust it is.",
    description:
      "Adaptive Evidence-Gain, Pareto Simulator, Recommendation Robustness, Recommendation Provenance, and Synthetic Fairness research tools help inspect next tests, trade-offs, assumptions, provenance, and limitations.",
    gain: "More inspectable decisions without pretending that uncertainty has disappeared.",
    signals: ["Adaptive Evidence-Gain", "Pareto Simulator", "Robustness", "Provenance", "Synthetic Fairness"],
    video: "decision",
    routeKey: "recommendationRobustness",
    ctaLabel: "Inspect decision tools",
    layout: "decision",
  },
];

export const homeServiceGroups: HomeServiceGroup[] = [
  {
    id: "career-discovery",
    title: "Career Discovery",
    description: "Start with personal context before jumping to recommendations.",
    capabilities: ["Natural Discovery", "RIASEC-inspired Career Interests", "Human Potential", "Career Compatibility"],
    routeKey: "diagnostic",
    ctaLabel: "Start discovery",
    tone: "teal",
    wide: true,
  },
  {
    id: "career-direction",
    title: "Career Direction",
    description: "Compare possible paths as hypotheses to inspect and test.",
    capabilities: ["Career Hypotheses", "Career Comparison", "Supported Paths", "Job-Loss Recovery"],
    routeKey: "careerCompatibility",
    ctaLabel: "Explore directions",
    tone: "green",
  },
  {
    id: "evidence-development",
    title: "Evidence & Development",
    description: "Build proof and learning momentum through focused action.",
    capabilities: ["Career Experiments", "Evidence Passport", "Learning Recommendations", "Roadmap / My Journey"],
    routeKey: "experiments",
    ctaLabel: "Build evidence",
    tone: "cyan",
  },
  {
    id: "market-jobs",
    title: "Market & Jobs",
    description: "Connect a direction with visible role requirements and gaps.",
    capabilities: ["Market Radar", "Job Analyzer", "Career Encyclopedia", "Browser Job Capture"],
    routeKey: "marketRadar",
    ctaLabel: "Check market fit",
    tone: "violet",
  },
  {
    id: "application-support",
    title: "Application Support",
    description: "Prepare truthful materials from your evidence base.",
    capabilities: ["Master Career Profile", "CV / Cover Letter", "Evidence Lock", "Application Tracker"],
    routeKey: "applications",
    ctaLabel: "Prepare applications",
    tone: "gold",
  },
  {
    id: "interview-support",
    title: "Interview Support",
    description: "Practice answers using real evidence and reflective preparation.",
    capabilities: ["STAR Story Library", "Interview Preparation", "Mock Interview", "Panel Simulation", "Offer Reflection"],
    routeKey: "interviews",
    ctaLabel: "Prepare interviews",
    tone: "teal",
  },
  {
    id: "decision-intelligence",
    title: "Decision Intelligence",
    description: "Inspect trade-offs, provenance, robustness, and next tests.",
    capabilities: [
      "Adaptive Evidence-Gain",
      "Pareto Simulator",
      "Recommendation Robustness",
      "Recommendation Provenance",
      "Synthetic Fairness research tools",
    ],
    routeKey: "systemCard",
    ctaLabel: "View system card",
    tone: "cyan",
  },
  {
    id: "ai-support",
    title: "AI Support",
    description: "Use conversational, source-visible support across the platform.",
    capabilities: ["OrganicAI Coach", "RAG-backed guidance", "Voice interaction", "Contextual navigation/help"],
    routeKey: "coach",
    ctaLabel: "Talk to coach",
    tone: "green",
    wide: true,
  },
];

export const homeBenefits = [
  "Understand yourself more clearly",
  "Discover career directions you may not have considered",
  "Separate interest from current ability",
  "See what evidence you actually have",
  "Identify what evidence is missing",
  "Test a career before making a major commitment",
  "Understand career transition trade-offs",
  "Prepare stronger, evidence-grounded applications",
  "Prepare for interviews",
  "Reassess your direction when circumstances change",
];

export const homeVoiceExamples = [
  "What career directions are currently worth testing?",
  "Why did you recommend this path?",
  "What evidence am I missing?",
  "Help me prepare for this interview.",
];

export const homeVoiceBoundaries = [
  "Voice is an interaction channel, not a behavioural hiring assessment.",
  "Text remains available, and voice is optional.",
  "Microphone access requires user action and consent.",
  "Voice is not used to infer personality, honesty, emotion, or protected attributes.",
];

export const homeTrustModules = [
  { title: "Career Hypotheses", text: "Directions are framed as explainable hypotheses, not final answers." },
  { title: "Evidence-based reasoning", text: "Recommendations can refer to visible profile signals and demonstrated evidence." },
  { title: "Recommendation Provenance", text: "Users can inspect why a direction appeared and which assumptions matter." },
  { title: "Robustness", text: "Decision-support tools can test whether recommendations change when assumptions change." },
  { title: "User control", text: "Profiles, plans, and recommendations remain editable, rejectable, and revisable." },
  { title: "Limits and privacy", text: "The interface communicates boundaries instead of hiding uncertainty." },
];

const profileRoute = (activeProfileId: string, path: string) => (activeProfileId ? path.replace(":profileId", activeProfileId) : "/diagnostic");

export function buildHomeRoute(routeKey: HomeRouteKey, activeProfileId: string) {
  switch (routeKey) {
    case "diagnostic":
      return "/diagnostic";
    case "howItWorks":
      return "/how-it-works";
    case "research":
      return "/research";
    case "principles":
      return "/principles";
    case "systemCard":
      return "/about/recommendation-system-card";
    case "blog":
      return "/blog";
    case "knowledgeBase":
      return "/knowledge-base";
    case "careers":
      return "/careers";
    case "profile":
      return profileRoute(activeProfileId, "/profile/:profileId");
    case "coach":
      return profileRoute(activeProfileId, "/coach/:profileId");
    case "recommendations":
      return profileRoute(activeProfileId, "/recommendations/:profileId");
    case "roadmap":
      return profileRoute(activeProfileId, "/roadmap/:profileId");
    case "assessment":
      return profileRoute(activeProfileId, "/workspace/:profileId/assessment");
    case "careerCompatibility":
      return profileRoute(activeProfileId, "/workspace/:profileId/career-compatibility");
    case "careerCompare":
      return profileRoute(activeProfileId, "/workspace/:profileId/career-compare");
    case "experiments":
      return profileRoute(activeProfileId, "/workspace/:profileId/experiments");
    case "evidencePassport":
      return profileRoute(activeProfileId, "/workspace/:profileId/evidence-passport");
    case "marketRadar":
      return profileRoute(activeProfileId, "/workspace/:profileId/market-radar");
    case "jobAnalyzer":
      return profileRoute(activeProfileId, "/workspace/:profileId/job-analyzer");
    case "applications":
      return profileRoute(activeProfileId, "/workspace/:profileId/applications");
    case "interviews":
      return profileRoute(activeProfileId, "/workspace/:profileId/interviews");
    case "starStories":
      return profileRoute(activeProfileId, "/workspace/:profileId/star-stories");
    case "offerReview":
      return profileRoute(activeProfileId, "/workspace/:profileId/offer-review");
    case "careerEncyclopedia":
      return profileRoute(activeProfileId, "/workspace/:profileId/career-encyclopedia");
    case "browserExtension":
      return profileRoute(activeProfileId, "/workspace/:profileId/integrations/browser-extension");
    case "adaptiveExperiments":
      return profileRoute(activeProfileId, "/workspace/:profileId/adaptive-experiments");
    case "transitionSimulator":
      return profileRoute(activeProfileId, "/workspace/:profileId/transition-simulator");
    case "recommendationRobustness":
      return profileRoute(activeProfileId, "/workspace/:profileId/recommendation-robustness");
    case "syntheticFairness":
      return profileRoute(activeProfileId, "/workspace/:profileId/synthetic-fairness-lab");
    case "learning":
      return profileRoute(activeProfileId, "/workspace/:profileId/learning");
    case "jobLoss":
      return profileRoute(activeProfileId, "/workspace/:profileId/job-loss-support");
    default: {
      const exhaustive: never = routeKey;
      return exhaustive;
    }
  }
}
