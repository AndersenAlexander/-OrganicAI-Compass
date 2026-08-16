import { mockLearningPaths } from "../../data/mockLearningPaths";
import { LearningModuleCard } from "./LearningModuleCard";
import { QuizCard } from "./QuizCard";

export function LearningPath() {
  return (
    <section className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-3">
        {mockLearningPaths.map((path) => <LearningModuleCard key={path.id} path={path} />)}
      </div>
      <QuizCard question={mockLearningPaths[0].quiz} />
    </section>
  );
}
