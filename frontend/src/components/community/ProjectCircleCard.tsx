export function ProjectCircleCard({ title, roles, impact }: { title: string; roles: string[]; impact: string }) {
  return (
    <article className="rounded-2xl border border-white/80 bg-white/80 p-5">
      <h3 className="font-display text-xl font-bold text-navy">{title}</h3>
      <p className="mt-3 text-sm text-slate-600"><span className="font-semibold text-teal">Roles:</span> {roles.join(", ")}</p>
      <p className="mt-2 text-sm text-slate-600"><span className="font-semibold text-teal">Impact:</span> {impact}</p>
      <button type="button" disabled title="Community project joining is coming soon" className="mt-4 cursor-not-allowed rounded-full bg-slate-400 px-4 py-2 text-sm font-semibold text-white opacity-75">Coming Soon</button>
    </article>
  );
}
