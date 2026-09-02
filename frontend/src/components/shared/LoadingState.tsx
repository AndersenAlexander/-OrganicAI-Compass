export function LoadingState({ label = "Loading a grounded response..." }: { label?: string }) {
  return (
    <div className="rounded-2xl border border-teal/20 bg-white/70 p-5 text-sm text-slate-600">
      {label}
    </div>
  );
}
