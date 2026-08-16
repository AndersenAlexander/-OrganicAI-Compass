export function ArchetypeSummaryCard({ label, title, description }: { label: string; title: string; description: string }) {
  return (
    <article className="glass-card p-5">
      <p className="text-sm font-semibold text-teal">{label}</p>
      <h3 className="mt-3 font-display text-xl font-bold text-navy">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
    </article>
  );
}
