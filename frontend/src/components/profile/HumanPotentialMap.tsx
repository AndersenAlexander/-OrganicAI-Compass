import { Leaf, Sparkles, Heart, Brain, Users, Route } from "lucide-react";
import { motion } from "motion/react";

const nodes = [
  { label: "Natural Tendencies", icon: Brain, className: "top-4 left-1/2 -translate-x-1/2" },
  { label: "Values", icon: Heart, className: "left-8 top-28" },
  { label: "Creativity", icon: Sparkles, className: "right-8 top-28" },
  { label: "Next Steps", icon: Leaf, className: "left-10 bottom-24" },
  { label: "Contribution Domains", icon: Users, className: "left-1/2 bottom-4 -translate-x-1/2" },
  { label: "AI Collaboration", icon: Route, className: "right-10 bottom-24" }
];

export function HumanPotentialMap() {
  return (
    <div className="organic-hero-surface relative min-h-[38rem] overflow-hidden rounded-[2.5rem] p-6">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_46%,rgba(94,234,212,0.2),transparent_22%),radial-gradient(circle_at_50%_50%,rgba(132,204,22,0.13),transparent_36%)]" />
      <div className="absolute left-1/2 top-1/2 h-[28rem] w-[28rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#99f6e4]/20 shadow-[inset_0_0_60px_rgba(94,234,212,0.14)]" />
      <div className="absolute left-1/2 top-1/2 h-[21rem] w-[21rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/16" />
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 620 520" aria-hidden="true">
        {nodes.map((_, index) => {
          const angles = [-90, -145, -35, 145, 90, 35];
          const angle = angles[index] * (Math.PI / 180);
          const x = 310 + Math.cos(angle) * 180;
          const y = 260 + Math.sin(angle) * 170;
          return (
            <motion.path key={index} d={`M310 260 C310 220, ${x} ${y}, ${x} ${y}`} fill="none" stroke="url(#mapGlow)" strokeWidth="2.5" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} />
          );
        })}
        <defs>
          <linearGradient id="mapGlow" x1="0" x2="1" y1="0" y2="1">
            <stop stopColor="#99f6e4" stopOpacity="0.18" />
            <stop offset="0.55" stopColor="#5eead4" stopOpacity="0.76" />
            <stop offset="1" stopColor="#a3e635" stopOpacity="0.45" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute left-1/2 top-1/2 grid h-44 w-44 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-[#99f6e4]/35 bg-[color:var(--bg-glass)] text-center shadow-glow backdrop-blur-2xl">
        <div>
          <p className="font-display text-3xl font-bold theme-text">You</p>
          <p className="mt-1 text-sm text-[color:var(--teal)]">Visionary</p>
          <p className="text-sm text-[color:var(--teal)]">Integrator</p>
        </div>
      </div>
      {nodes.map(({ label, icon: Icon, className }) => (
        <motion.div key={label} initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className={`absolute ${className} grid h-32 w-32 place-items-center rounded-full border border-[#99f6e4]/25 bg-[color:var(--bg-glass)] p-3 text-center shadow-[0_18px_55px_rgba(15,118,110,0.16)] backdrop-blur-xl`}>
          <div>
            <Icon size={22} className="mx-auto text-[color:var(--teal)]" />
            <p className="mt-2 text-sm font-semibold theme-text">{label}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
