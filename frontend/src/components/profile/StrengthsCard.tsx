export function StrengthsCard({ strengths }: { strengths: { label: string; value: number }[] }) {
  return (
    <article className="glass-card p-5">
      <h3 className="font-display text-xl font-bold text-navy">Top Strengths</h3>
      <div className="mt-5 space-y-4">
        {strengths.map((item) => (
          <div key={item.label}>
            <div className="mb-2 flex justify-between text-sm">
              <span className="font-semibold text-navy">{item.label}</span>
              <span className="text-slate-500">{item.value}%</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-gradient-to-r from-teal to-sky" style={{ width: `${item.value}%` }} />
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}
