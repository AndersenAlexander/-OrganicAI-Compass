import { Heart, Leaf, ShieldCheck, Target, Users, UserRoundCheck } from "lucide-react";
import { Link } from "react-router-dom";

const principles = [
  { title: "Human-Centred", description: "Designed around your values and well-being.", icon: Heart },
  { title: "Trust & Transparency", description: "Clear, explainable, and ethical AI.", icon: ShieldCheck },
  { title: "Empowerment", description: "AI to amplify your strengths, not replace you.", icon: UserRoundCheck },
  { title: "Lifelong Growth", description: "Continuous learning for a changing world.", icon: Leaf },
  { title: "Collaboration", description: "Better together - human + AI synergy.", icon: Users },
  { title: "Purpose Alignment", description: "Align actions with what truly matters to you.", icon: Target }
];

export function SixPrinciples() {
  return (
    <section id="principles" className="landing-detail-card principles-card space-y-3">
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-serif text-[19px] font-semibold theme-text">6 Principles</h2>
        <Link to="/principles" className="rounded-full border border-[color:var(--border-soft)] bg-white/35 px-3 py-1 text-xs theme-muted">View all</Link>
      </div>
      <div className="principles-grid">
        {principles.map(({ title, description, icon: Icon }, index) => (
          <article key={title} className="principle-item">
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[color:var(--teal)]/10 text-[color:var(--teal)]"><Icon size={17} /></div>
            <div>
              <h3 className="text-[11px] font-bold leading-tight theme-text">{index + 1}. {title}</h3>
              <p className="mt-1 text-[10px] leading-[1.3] theme-muted">{description}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
