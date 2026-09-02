export function GrowthMilestoneCard({ item }: { item: any }) {
  return (
    <article className="rounded-2xl border border-white/80 bg-white/80 p-5">
      <p className="text-sm font-semibold text-teal">{item.day}</p>
      <h3 className="mt-2 font-display text-xl font-bold text-navy">{item.title}</h3>
      <p className="mt-2 text-sm text-slate-600">{item.description}</p>
    </article>
  );
}
