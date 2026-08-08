export function ConstitutionPrincipleCard({ title, items }: { title: string; items: string[] | string }) {
  return (
    <article className="rounded-2xl border border-white/80 bg-white/80 p-5">
      <h3 className="font-display text-xl font-bold text-navy">{title}</h3>
      {Array.isArray(items) ? <ul className="mt-3 space-y-2 text-sm text-slate-600">{items.map((item) => <li key={item}>- {item}</li>)}</ul> : <p className="mt-3 text-sm leading-6 text-slate-600">{items}</p>}
    </article>
  );
}
