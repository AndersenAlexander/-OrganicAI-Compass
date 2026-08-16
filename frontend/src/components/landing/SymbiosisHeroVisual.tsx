import { Bot, Brain, Leaf, Lightbulb, Network, Sparkles, UserRound } from "lucide-react";
import { motion } from "motion/react";

const nodes = [
  { label: "Talent", className: "left-8 top-10", icon: Brain },
  { label: "Clarity", className: "right-8 top-14", icon: Sparkles },
  { label: "Creativity", className: "bottom-14 left-5", icon: Leaf },
  { label: "Contribution", className: "bottom-10 right-5", icon: Network }
];

export function SymbiosisHeroVisual() {
  return (
    <div className="soft-glow relative mx-auto aspect-[1.05] w-full max-w-[36rem] overflow-hidden rounded-[2.75rem] border border-white/70 bg-white/50 p-6 backdrop-blur-2xl">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_25%,rgba(94,234,212,0.34),transparent_28%),radial-gradient(circle_at_76%_24%,rgba(132,204,22,0.28),transparent_30%),radial-gradient(circle_at_50%_72%,rgba(250,204,21,0.16),transparent_30%)]" />
      <div className="concept-arc-left absolute -left-24 top-0 h-full w-44 rounded-r-[5rem] opacity-95 ring-1 ring-white/10" />
      <div className="concept-arc-right absolute -right-24 top-0 h-full w-44 rounded-l-[5rem] opacity-95 ring-1 ring-white/80" />
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 520 520" aria-hidden="true">
        <motion.path
          d="M95 260 C150 110, 370 110, 425 260 C370 410, 150 410, 95 260Z"
          fill="none"
          stroke="rgba(15,118,110,0.26)"
          strokeWidth="2"
          animate={{ pathLength: [0.8, 1, 0.8] }}
          transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.path
          d="M92 252 C180 150, 338 150, 428 252"
          fill="none"
          stroke="rgba(132,204,22,0.45)"
          strokeLinecap="round"
          strokeWidth="5"
          animate={{ pathLength: [0.5, 1, 0.5] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.path
          d="M92 282 C180 382, 338 382, 428 282"
          fill="none"
          stroke="rgba(94,234,212,0.55)"
          strokeLinecap="round"
          strokeWidth="5"
          animate={{ pathLength: [0.5, 1, 0.5] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
        />
        <path
          d="M260 105 C238 170, 238 350, 260 415"
          fill="none"
          stroke="rgba(7,21,39,0.16)"
          strokeDasharray="7 12"
          strokeLinecap="round"
          strokeWidth="3"
        />
      </svg>

      <div className="relative grid h-full place-items-center">
        <div className="absolute left-1 top-1/2 hidden -translate-y-1/2 -rotate-90 rounded-full bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-white sm:block">
          Old paradigm
        </div>
        <div className="absolute right-1 top-1/2 hidden -translate-y-1/2 rotate-90 rounded-full bg-white/70 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-organic sm:block">
          New paradigm
        </div>

        <div className="absolute left-10 top-1/2 flex -translate-y-1/2 flex-col items-center gap-3 sm:left-14">
          <div className="grid h-24 w-24 place-items-center rounded-[2rem] border border-white/80 bg-cream/85 text-teal shadow-organic">
            <UserRound size={38} />
          </div>
          <span className="rounded-full bg-white/75 px-4 py-2 text-sm font-bold text-navy">Human</span>
        </div>

        <div className="absolute right-10 top-1/2 flex -translate-y-1/2 flex-col items-center gap-3 sm:right-14">
          <div className="grid h-24 w-24 place-items-center rounded-[2rem] border border-white/80 bg-deepNavy text-softTeal shadow-glow">
            <Bot size={38} />
          </div>
          <span className="rounded-full bg-white/75 px-4 py-2 text-sm font-bold text-navy">AI</span>
        </div>

        <div className="z-10 grid h-36 w-36 place-items-center rounded-full border border-white/90 bg-white/85 text-center shadow-glow backdrop-blur-xl">
          <div>
            <div className="mx-auto mb-2 grid h-10 w-10 place-items-center rounded-full bg-teal text-white">
              <Leaf size={20} />
            </div>
            <p className="text-sm font-black uppercase tracking-[0.14em] text-teal">Human + AI</p>
          </div>
        </div>

        {nodes.map((node) => {
          const Icon = node.icon;
          return (
            <div
              key={node.label}
              className={`absolute ${node.className} flex items-center gap-2 rounded-full border border-white/80 bg-white/80 px-3 py-2 text-xs font-bold text-navy shadow-sm backdrop-blur`}
            >
              <Icon size={15} className="text-teal" />
              {node.label}
            </div>
          );
        })}

        <div className="absolute left-[10%] top-[22%] grid h-12 w-12 place-items-center rounded-full border border-white/20 bg-deepNavy/90 text-softTeal">
          <Brain size={20} />
        </div>
        <div className="absolute right-[10%] top-[22%] grid h-12 w-12 place-items-center rounded-full border border-white/80 bg-white/80 text-gold">
          <Lightbulb size={21} />
        </div>

        <div className="absolute left-[28%] top-[28%] h-3 w-3 rounded-full bg-gold shadow-glow" />
        <div className="absolute right-[30%] top-[32%] h-2 w-2 rounded-full bg-softTeal shadow-glow" />
        <div className="absolute bottom-[29%] left-[35%] h-2.5 w-2.5 rounded-full bg-leaf shadow-glow" />
        <div className="absolute bottom-[32%] right-[35%] h-2 w-2 rounded-full bg-teal shadow-glow" />
      </div>
    </div>
  );
}
