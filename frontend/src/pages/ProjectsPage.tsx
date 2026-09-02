import { HumanContributionProjects } from "../components/projects/HumanContributionProjects";
import { ExperimentalConceptNotice } from "../components/shared/ExperimentalConceptNotice";

export function ProjectsPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Projects</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-navy">Turn profile into contribution</h1>
      </div>
      <ExperimentalConceptNotice module="Human Contribution Projects" />
      <HumanContributionProjects />
    </div>
  );
}
