export const mockLearningPaths = [
  "AI for Beginners",
  "AI for Creatives",
  "AI for Teachers",
  "AI for Entrepreneurs",
  "AI for Designers",
  "AI for People Afraid of Technology",
  "AI and Ethics",
  "AI and the Future of Work",
  "AI and Robotics"
].map((title, index) => ({
  id: `path-${index}`,
  title,
  progress: (index % 4) * 20,
  modules: ["Foundations", "Practice", "Reflection"],
  exercise: "Use AI on one real task, then verify the result.",
  quiz: "What should remain human-led?",
  miniProject: "Create a one-page guide for your context."
}));
