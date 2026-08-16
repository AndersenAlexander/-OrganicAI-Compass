export function ExperimentalConceptNotice({ module }: { module: string }) {
  return (
    <div className="rounded-lg border border-amber-300/45 bg-amber-500/12 p-4 text-sm text-amber-950">
      <span className="mr-2 inline-flex rounded-full border border-amber-500/50 bg-amber-200 px-2 py-0.5 text-xs font-black uppercase tracking-wide text-amber-950">
        Experimental
      </span>
      {module} uses synthetic, non-persistent demo data and is excluded from evaluated MVP claims.
    </div>
  );
}
