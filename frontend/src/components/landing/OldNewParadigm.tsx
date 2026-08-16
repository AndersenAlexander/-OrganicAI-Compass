import { ArrowRight, HandHeart, Lightbulb, Recycle, ShieldAlert, Users, Workflow } from "lucide-react";
import { motion } from "motion/react";
import { fadeUp } from "../../lib/animations";

const oldItems = [
  { label: "Fear", icon: ShieldAlert },
  { label: "Repetitive work", icon: Workflow },
  { label: "Competition", icon: Users },
  { label: "Scarcity", icon: Recycle }
];

const newItems = [
  { label: "Creativity", icon: Lightbulb },
  { label: "Abundance", icon: Recycle },
  { label: "Collaboration", icon: Users },
  { label: "Contribution", icon: HandHeart }
];

export function OldNewParadigm() {
  return (
    <motion.section id="paradigm" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }} variants={fadeUp} className="organic-section scroll-mt-28">
      <div className="mb-8 max-w-3xl">
        <span className="organic-badge">Paradigm shift</span>
        <h2 className="mt-4 font-display text-3xl font-black text-deepNavy sm:text-4xl">
          AI as a bridge, not a threat
        </h2>
      </div>

      <div className="grid items-stretch gap-5 lg:grid-cols-[1fr_auto_1fr]">
        <motion.div initial={{ opacity: 0, x: -24 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="rounded-[2rem] border border-white/10 bg-deepNavy p-6 text-white shadow-organic">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-softTeal">The Old Paradigm</p>
          <h3 className="mt-3 font-display text-2xl font-bold">Value under pressure</h3>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {oldItems.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.label} className="flex items-center gap-3 rounded-2xl bg-white/8 p-4 ring-1 ring-white/10">
                  <Icon size={20} className="text-softTeal" />
                  <span className="text-sm font-semibold">{item.label}</span>
                </div>
              );
            })}
          </div>
        </motion.div>

        <div className="hidden place-items-center lg:grid">
          <div className="grid h-16 w-16 place-items-center rounded-full border border-white/80 bg-white/80 text-teal shadow-glow">
            <ArrowRight size={26} />
          </div>
        </div>

        <motion.div initial={{ opacity: 0, x: 24 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="rounded-[2rem] border border-white/80 bg-gradient-to-br from-white/85 via-mist/80 to-lime-50/85 p-6 shadow-organic backdrop-blur-xl">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal">The New Paradigm</p>
          <h3 className="mt-3 font-display text-2xl font-bold text-deepNavy">Potential in collaboration</h3>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {newItems.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.label} className="flex items-center gap-3 rounded-2xl bg-white/75 p-4 ring-1 ring-white/80">
                  <Icon size={20} className="text-organic" />
                  <span className="text-sm font-semibold text-navy">{item.label}</span>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </motion.section>
  );
}
