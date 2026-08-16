import { FutureScenarioSimulator } from "../components/scenarios/FutureScenarioSimulator";
import { ExperimentalConceptNotice } from "../components/shared/ExperimentalConceptNotice";

export function FutureScenarioPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Future scenarios</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-navy">The future is not a single path.</h1>
        <p className="mt-4 max-w-3xl text-slate-600">It depends on how we design our collaboration with technology.</p>
      </div>
      <ExperimentalConceptNotice module="Future Scenarios" />
      <FutureScenarioSimulator />
    </div>
  );
}
