export function JourneySidebar() {
  return (
    <aside className="space-y-4">
      <div className="glass-card p-5">
        <h2 className="font-display text-xl font-bold text-navy">Andrea Popescu</h2>
        <p className="mt-2 text-sm text-slate-600">Curious - Purpose-driven - Builder</p>
      </div>
      <div className="glass-card p-5">
        <h3 className="font-display text-lg font-bold text-navy">Recent Conversations</h3>
        <ul className="mt-4 space-y-3 text-sm text-slate-600">
          <li>Overcoming Fear with AI Collaboration</li>
          <li>Designing Ethical AI-Human Workflows</li>
          <li>Turning Ideas into Meaningful Impact</li>
        </ul>
      </div>
      <div className="glass-card p-5">
        <h3 className="font-display text-lg font-bold text-navy">Saved Milestones</h3>
        <ul className="mt-4 space-y-3 text-sm text-slate-600">
          <li>Created my Personal Why Statement</li>
          <li>Mapped my Core Talents</li>
          <li>Defined my First Contribution Idea</li>
        </ul>
      </div>
    </aside>
  );
}
