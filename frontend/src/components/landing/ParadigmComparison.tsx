import { CheckCircle2, CircleX, Leaf } from "lucide-react";
import { Link } from "react-router-dom";

const oldItems = ["AI as a threat", "Automation mindset", "One-size-fits-all learning", "Information overload", "Disconnected growth"];
const newItems = ["AI as a collaborator", "Augmentation mindset", "Personalized growth", "Curated, meaningful insights", "Purpose-driven roadmap"];

export function ParadigmComparison() {
  return (
    <section id="paradigm" className="landing-detail-card paradigm-card space-y-4">
      <h2 className="font-serif text-[19px] font-semibold theme-text">Old Paradigm vs New Paradigm</h2>
      <div className="grid gap-2.5 sm:grid-cols-[1fr_auto_1fr]">
        <div className="rounded-2xl border border-slate-200/70 bg-slate-50/80 p-3 text-[#071527] dark:border-white/10 dark:bg-white/5 dark:text-white">
          <p className="text-xs font-semibold theme-text">Old Paradigm</p>
          <ul className="mt-3 space-y-1.5">
            {oldItems.map((item) => (
              <li key={item} className="flex items-center gap-1.5 text-[11px] leading-[1.3] theme-muted"><CircleX size={12} /> {item}</li>
            ))}
          </ul>
        </div>
        <div className="hidden items-center justify-center sm:flex">
          <span className="text-xl font-light text-[#38bdf8]">»</span>
        </div>
        <div className="rounded-2xl border border-emerald-200/70 bg-emerald-50/60 p-3 dark:border-teal-300/15 dark:bg-teal-300/8">
          <p className="text-xs font-semibold text-[color:var(--teal)]">New Paradigm</p>
          <ul className="mt-3 space-y-1.5">
            {newItems.map((item) => (
              <li key={item} className="flex items-center gap-1.5 text-[11px] leading-[1.3] theme-muted"><CheckCircle2 size={12} className="text-[color:var(--teal)]" /> {item}</li>
            ))}
          </ul>
        </div>
      </div>
      <p className="flex items-center justify-center gap-2 text-center text-[11px] theme-muted">Shift your mindset. Shape your future. <Leaf size={13} className="text-[color:var(--teal)]" /></p><Link to="/about" className="block text-center text-[11px] font-bold text-[color:var(--teal)]">Learn why OrganicAI exists →</Link>
    </section>
  );
}
