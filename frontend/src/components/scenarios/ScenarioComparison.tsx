import { AnimatePresence, motion } from "motion/react";

export function ScenarioComparison({ scenarios }: { scenarios: any[] }) {
  return (
    <AnimatePresence>
      {scenarios.length === 2 ? (
        <motion.section layout initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="grid gap-5 lg:grid-cols-2">
          {scenarios.map((scenario) => (
            <article key={scenario.id} className="rounded-2xl border border-white/80 bg-white/80 p-5">
              <h3 className="font-display text-xl font-bold text-navy">{scenario.title}</h3>
              <p className="mt-4 text-sm text-slate-600"><span className="font-semibold text-teal">Opportunities:</span> {scenario.opportunities.join(", ")}</p>
              <p className="mt-3 text-sm text-slate-600"><span className="font-semibold text-teal">Risks:</span> {scenario.risks.join(", ")}</p>
              <p className="mt-3 text-sm text-slate-600"><span className="font-semibold text-teal">Human role:</span> {scenario.humanRole}</p>
              <p className="mt-3 text-sm text-slate-600"><span className="font-semibold text-teal">AI role:</span> {scenario.aiRole}</p>
            </article>
          ))}
        </motion.section>
      ) : null}
    </AnimatePresence>
  );
}
