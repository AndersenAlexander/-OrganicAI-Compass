export type NavigationItem = {
  label: string;
  to: string;
  end?: boolean;
};

export const globalNavigation: NavigationItem[] = [
  { label: "Home", to: "/", end: true },
  { label: "About", to: "/about" },
  { label: "How It Works", to: "/how-it-works" },
  { label: "Principles", to: "/principles" },
  { label: "Research", to: "/research" },
  { label: "Project Roadmap", to: "/project-roadmap" },
  { label: "Careers", to: "/careers" },
  { label: "System Card", to: "/about/recommendation-system-card" },
  { label: "Journal", to: "/blog" },
];

export const publicNavigation = globalNavigation;

export function buildWorkspaceNavigation(activeProfileId: string): NavigationItem[] {
  const profileId = activeProfileId || "";

  if (!profileId) {
    return [
      { label: "Dashboard", to: "/dashboard" },
      { label: "Natural Discovery", to: "/diagnostic" },
      { label: "Knowledge Base", to: "/knowledge-base" },
      { label: "Privacy Center", to: "/privacy" },
      { label: "Settings", to: "/settings" },
    ];
  }

  return [
    { label: "Dashboard", to: "/dashboard" },
    { label: "Natural Discovery", to: "/diagnostic" },
    { label: "Human Potential Map", to: `/profile/${profileId}` },
    { label: "Capability Assessment", to: `/workspace/${profileId}/assessment` },
    { label: "Career Hypotheses", to: `/workspace/${profileId}/career-compatibility` },
    { label: "Evidence Passport", to: `/workspace/${profileId}/evidence-passport` },
    { label: "Career Experiments", to: `/workspace/${profileId}/experiments` },
    { label: "Supported Paths", to: `/workspace/${profileId}/supported-paths` },
    { label: "Market Radar", to: `/workspace/${profileId}/market-radar` },
    { label: "Job Analyzer", to: `/workspace/${profileId}/job-analyzer` },
    { label: "Applications", to: `/workspace/${profileId}/applications` },
    { label: "Interview Journey", to: `/workspace/${profileId}/interviews` },
    { label: "Panel Interview", to: `/workspace/${profileId}/interviews` },
    { label: "STAR Stories", to: `/workspace/${profileId}/star-stories` },
    { label: "Offer Review", to: `/workspace/${profileId}/offer-review` },
    { label: "Career Encyclopedia", to: `/workspace/${profileId}/career-encyclopedia` },
    { label: "Adaptive Experiments", to: `/workspace/${profileId}/adaptive-experiments` },
    { label: "Transition Simulator", to: `/workspace/${profileId}/transition-simulator` },
    { label: "Decision Journal", to: `/workspace/${profileId}/decision-journal` },
    { label: "Recommendation Robustness", to: `/workspace/${profileId}/recommendation-robustness` },
    { label: "Synthetic Fairness Lab", to: `/workspace/${profileId}/synthetic-fairness-lab` },
    { label: "Advisor Collaboration", to: `/workspace/${profileId}/advisor-collaboration` },
    { label: "Browser Extension", to: `/workspace/${profileId}/integrations/browser-extension` },
    { label: "Research Evaluation", to: `/workspace/${profileId}/research-evaluation` },
    { label: "Learning Path", to: `/workspace/${profileId}/learning` },
    { label: "Job Loss Support", to: `/workspace/${profileId}/job-loss-support` },
    { label: "AI Coach", to: `/coach/${profileId}` },
    { label: "Recommendations", to: `/recommendations/${profileId}` },
    { label: "My Roadmap", to: `/roadmap/${profileId}` },
    { label: "Knowledge Base", to: "/knowledge-base" },
    { label: "Privacy Center", to: "/privacy" },
    { label: "Settings", to: "/settings" },
  ];
}

export const exploreNavigation: NavigationItem[] = [
  { label: "Community", to: "/community" },
  { label: "Co-Creation Studio", to: "/co-creation-studio" },
];
