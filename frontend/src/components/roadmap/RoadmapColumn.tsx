export function RoadmapColumn({ title, subtitle, actions }: { title: string; subtitle: string; actions: string[][] }) {
  return (
    <section className="glass-card p-5">
      <div className="mb-5">
        <h2 className="font-display text-2xl font-bold text-navy">{title}</h2>
        <p className="text-sm font-semibold text-teal">{subtitle}</p>
      </div>
      <div className="space-y-4">
        {actions.map(([label, action]) => <article key={action} className="rounded-xl border border-[color:var(--border-soft)] p-3"><p className="text-xs font-semibold text-teal">{label}</p><p className="mt-1 font-semibold text-navy">{action}</p></article>)}
      </div>
    </section>
  );
}
