import { ContributionMatchCard } from "./ContributionMatchCard";
import { ProjectCircleCard } from "./ProjectCircleCard";

export function CommunityOfContribution() {
  const matches = ["Creator + Builder", "Educator + Technologist", "Caregiver + AI Developer", "Systems Thinker + Designer", "Researcher + Communicator"];
  return (
    <section className="space-y-5">
      <div className="flex flex-wrap gap-3">{matches.map((match) => <ContributionMatchCard key={match} title={match} />)}</div>
      <div className="grid gap-5 lg:grid-cols-2">
        <ProjectCircleCard title="AI Literacy Circle" roles={["Educator", "Technologist", "Communicator"]} impact="Community understanding" />
        <ProjectCircleCard title="Care + Robotics Lab" roles={["Caregiver", "AI Developer", "Designer"]} impact="Human-centred automation" />
      </div>
    </section>
  );
}
