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
  { label: "Journal", to: "/blog" },
];

export const publicNavigation = globalNavigation;

export function buildWorkspaceNavigation(activeProfileId: string): NavigationItem[] {
  const profileId = activeProfileId || "demo-profile";

  return [
    { label: "Dashboard", to: "/dashboard" },
    { label: "Diagnostic", to: "/diagnostic" },
    { label: "Career Assessment", to: `/workspace/${profileId}/assessment` },
    { label: "Human Potential Map", to: `/profile/${profileId}` },
    { label: "Career Compatibility", to: `/workspace/${profileId}/career-compatibility` },
    { label: "Learning Path", to: `/workspace/${profileId}/learning` },
    { label: "AI Coach", to: `/coach/${profileId}` },
    { label: "Recommendations", to: `/recommendations/${profileId}` },
    { label: "My Roadmap", to: `/roadmap/${profileId}` },
    { label: "Knowledge Base", to: "/knowledge-base" },
  ];
}

export const exploreNavigation: NavigationItem[] = [
  { label: "Future Scenarios", to: "/future-scenarios" },
  { label: "Projects", to: "/projects" },
  { label: "Growth Timeline", to: "/growth-timeline" },
  { label: "Community", to: "/community" },
  { label: "Learning Paths", to: "/learning-paths" },
  { label: "Co-Creation Studio", to: "/co-creation-studio" },
  { label: "AI Constitution", to: "/ai-constitution" },
];
