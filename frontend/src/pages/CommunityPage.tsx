import { CommunityOfContribution } from "../components/community/CommunityOfContribution";

export function CommunityPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Community</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-navy">Community of Contribution</h1>
      </div>
      <CommunityOfContribution />
    </div>
  );
}
