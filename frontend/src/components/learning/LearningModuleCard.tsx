export function LearningModuleCard({ path }: { path: any }) {
  return (
    <article className="rounded-2xl border border-white/80 bg-white/80 p-5">
      <h3 className="font-display text-xl font-bold text-navy">{path.title}</h3>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full bg-teal" style={{ width: `${path.progress}%` }} />
      </div>
      <p className="mt-2 text-xs font-semibold text-teal">{path.progress}% complete</p>
      <ul className="mt-4 space-y-1 text-sm text-slate-600">{path.modules.map((module: string) => <li key={module}>- {module}</li>)}</ul>
    </article>
  );
}
