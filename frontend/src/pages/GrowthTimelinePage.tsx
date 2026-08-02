import { GrowthTimeline } from "../components/growth/GrowthTimeline";

export function GrowthTimelinePage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Memory of growth</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-navy">My Growth Timeline</h1>
      </div>
      <GrowthTimeline />
    </div>
  );
}
