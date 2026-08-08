export function LearningPathsCard({ items }: { items: string[] }) {
  return (
    <article className="glass-card p-5">
      <h3 className="font-display text-xl font-bold text-navy">Learning Paths</h3>
      <div className="mt-4 space-y-3">{items.map((item) => <div key={item} className="rounded-2xl bg-white/80 px-4 py-3 text-sm font-semibold text-navy">{item}</div>)}</div>
    </article>
  );
}
