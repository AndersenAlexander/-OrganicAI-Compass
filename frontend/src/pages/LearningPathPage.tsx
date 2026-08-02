import { LearningPath } from "../components/learning/LearningPath";

export function LearningPathPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Learning paths</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-navy">AI Literacy Learning Paths</h1>
      </div>
      <LearningPath />
    </div>
  );
}
