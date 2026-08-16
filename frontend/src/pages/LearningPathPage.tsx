import { LearningPath } from "../components/learning/LearningPath";
import { ExperimentalConceptNotice } from "../components/shared/ExperimentalConceptNotice";

export function LearningPathPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Learning paths</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-navy">AI Literacy Learning Paths</h1>
      </div>
      <ExperimentalConceptNotice module="Learning Paths prototype" />
      <LearningPath />
    </div>
  );
}
