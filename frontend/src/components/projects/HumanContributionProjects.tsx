import { mockProjects } from "../../data/mockProjects";
import { EthicalReflectionCard } from "../ethics/EthicalReflectionCard";
import { ProjectBuilder } from "./ProjectBuilder";
import { ProjectIdeaCard } from "./ProjectIdeaCard";

export function HumanContributionProjects() {
  return (
    <section className="space-y-5">
      <div>
        <h2 className="font-display text-2xl font-bold text-navy">Human Contribution Projects</h2>
        <p className="mt-3 text-slate-600">Turn profile signals into practical ideas for social good.</p>
      </div>
      <ProjectBuilder />
      <div className="grid gap-5 lg:grid-cols-2">
        {mockProjects.map((project) => <ProjectIdeaCard key={project.title} project={project} />)}
      </div>
      <EthicalReflectionCard compact />
    </section>
  );
}
