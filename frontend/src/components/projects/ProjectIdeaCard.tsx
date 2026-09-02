export function ProjectIdeaCard({ project }: { project: any }) {
  return (
    <article className="rounded-2xl border border-white/80 bg-white/80 p-5">
      <p className="text-sm font-semibold text-teal">{project.domain}</p>
      <h3 className="mt-2 font-display text-xl font-bold text-navy">{project.title}</h3>
      <p className="mt-3 text-sm text-slate-600"><span className="font-semibold text-teal">Problem:</span> {project.problem}</p>
      <p className="mt-2 text-sm text-slate-600"><span className="font-semibold text-teal">Audience:</span> {project.audience}</p>
      <p className="mt-2 text-sm text-slate-600"><span className="font-semibold text-teal">MVP:</span> {project.mvp}</p>
    </article>
  );
}
