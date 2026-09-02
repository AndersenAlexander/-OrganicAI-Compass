import { Leaf, ShieldCheck } from "lucide-react";
import { motion } from "motion/react";
import { fadeUp } from "../../lib/animations";

type EthicalReflectionCardProps = {
  compact?: boolean;
};

export function EthicalReflectionCard({ compact = false }: EthicalReflectionCardProps) {
  return (
    <motion.aside
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
      className="rounded-2xl border border-teal/15 bg-white/75 p-5 shadow-sm"
    >
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-teal/10 text-teal">
          {compact ? <Leaf size={18} /> : <ShieldCheck size={19} />}
        </span>
        <div>
          <h3 className="font-display text-lg font-bold text-navy">Ethical reflection</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Use AI to explore possibilities, not to define your identity. Your roadmap is a guide, not a fixed label.
          </p>
        </div>
      </div>
      {!compact ? (
        <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-2">
          <p><span className="font-semibold text-teal">Be careful about:</span> over-trust, privacy, and automation bias.</p>
          <p><span className="font-semibold text-teal">Keep human-led:</span> values, identity, consent, and final judgment.</p>
          <p><span className="font-semibold text-teal">Verify:</span> important facts, sources, and consequences.</p>
          <p><span className="font-semibold text-teal">Do not share:</span> sensitive personal or confidential data.</p>
        </div>
      ) : null}
    </motion.aside>
  );
}
