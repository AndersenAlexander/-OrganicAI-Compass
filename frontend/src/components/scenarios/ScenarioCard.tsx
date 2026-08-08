import { motion } from "motion/react";

export function ScenarioCard({ scenario, selected, onToggle }: { scenario: any; selected: boolean; onToggle: () => void }) {
  return (
    <motion.article layout whileHover={{ y: -3 }} className={`rounded-2xl border p-5 ${selected ? "organic-action-soft shadow-[var(--shadow-action)]" : "border-white/80 bg-white/75"}`}>
      <button type="button" onClick={onToggle} className="w-full text-left">
        <h3 className="font-display text-xl font-bold text-navy">{scenario.title}</h3>
        <p className="mt-3 text-sm leading-6 text-slate-600">{scenario.description}</p>
      </button>
    </motion.article>
  );
}
