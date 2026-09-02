import { Code2, FileText, Mic, Route, Sparkles, Users } from "lucide-react";

const focus = [
  { label: "React and TypeScript frontend", icon: Code2 },
  { label: "FastAPI backend integration", icon: FileText },
  { label: "AI-generated talent profiles", icon: Sparkles },
  { label: "Voice-based AI Coach", icon: Mic },
  { label: "Personal roadmap generation", icon: Route },
  { label: "User-centred evaluation", icon: Users }
];

export function ThesisDirection() {
  return (
    <section id="thesis" className="grid scroll-mt-28 gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="organic-section">
        <span className="organic-badge">Thesis Direction</span>
        <h2 className="mt-4 font-display text-3xl font-black text-deepNavy sm:text-4xl">Thesis Direction</h2>
        <p className="mt-5 text-lg leading-8 text-slate-600">
          OrganicAI Compass explores how a human-centred AI platform can help users move from fear and
          uncertainty toward creativity, purpose, and positive human-machine collaboration.
        </p>
      </div>

      <div className="organic-card">
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal">Academic title</p>
        <h3 className="mt-4 font-display text-2xl font-black leading-tight text-deepNavy">
          OrganicAI Compass: Design and Implementation of a Human-Centred AI Platform for Talent Discovery,
          Purpose Alignment, and Positive Human-Machine Collaboration
        </h3>
        <div className="mt-8">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal">Engineering focus</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {focus.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.label} className="flex items-center gap-3 rounded-2xl bg-white/75 p-3 text-sm font-semibold text-slate-700 ring-1 ring-white/80">
                  <Icon size={18} className="text-teal" />
                  {item.label}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
