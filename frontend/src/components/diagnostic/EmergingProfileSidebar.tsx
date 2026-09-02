const traits = ["Curiosity", "Courage", "Purpose", "Potential", "AI Synergy"];

export function EmergingProfileSidebar() {
  return (
    <aside className="space-y-4">
      <div className="glass-card p-5">
        <h2 className="font-display text-xl font-bold theme-text">Why this matters</h2>
        <p className="mt-3 text-sm leading-6 theme-muted">
          Understanding your interests and curiosities helps shape a path that feels meaningful and sustainable-together with AI.
        </p>
      </div>
      <div className="glass-card p-5">
        <h2 className="font-display text-xl font-bold theme-text">Your emerging profile</h2>
        <p className="mt-2 text-sm theme-muted">This updates as you go.</p>
        <div className="mt-5 space-y-4">
          {traits.map((trait) => (
            <div key={trait}>
              <div className="mb-2 flex justify-between text-sm">
                <span className="font-semibold theme-text">{trait}</span>
                <span className="theme-muted">Not set</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/20">
                <div className="h-full w-1/3 rounded-full organic-progress-action" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
