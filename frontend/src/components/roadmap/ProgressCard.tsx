export function ProgressCard() {
  return (
    <div className="glass-card p-5">
      <h3 className="font-display text-xl font-bold text-navy">Your Progress</h3>
      <p className="mt-5 text-5xl font-black text-teal">47%</p>
      <p className="mt-2 text-sm text-slate-600">Journey Progress</p>
      <div className="mt-5 rounded-2xl bg-white/85 p-4">
        <p className="text-sm font-semibold text-teal">Next Milestone</p>
        <p className="mt-2 font-semibold text-navy">AI Idea Spark</p>
      </div>
    </div>
  );
}
