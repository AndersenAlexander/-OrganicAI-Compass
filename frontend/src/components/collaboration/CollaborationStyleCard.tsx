import { motion } from "motion/react";
import { fadeUp } from "../../lib/animations";

export type CollaborationStyle = {
  title: string;
  description: string;
  usefulWhen: string;
  risks: string;
  prompts: string[];
  exercises: string[];
};

export function CollaborationStyleCard({ style, featured = false }: { style: CollaborationStyle; featured?: boolean }) {
  return (
    <motion.article
      variants={fadeUp}
      whileHover={{ y: -4 }}
      className={`rounded-2xl border p-5 shadow-sm ${featured ? "organic-action-soft shadow-[var(--shadow-action)]" : "border-white/80 bg-white/75"}`}
    >
      <h3 className="font-display text-xl font-bold text-navy">{style.title}</h3>
      <p className="mt-3 text-sm leading-6 text-slate-600">{style.description}</p>
      <p className="mt-4 text-sm text-slate-600"><span className="font-semibold text-teal">Useful when:</span> {style.usefulWhen}</p>
      <p className="mt-2 text-sm text-slate-600"><span className="font-semibold text-teal">Risks:</span> {style.risks}</p>
      <div className="mt-4">
        <p className="text-sm font-semibold text-navy">Prompt examples</p>
        <ul className="mt-2 space-y-1 text-sm text-slate-600">
          {style.prompts.map((prompt) => <li key={prompt}>- {prompt}</li>)}
        </ul>
      </div>
      <div className="mt-4">
        <p className="text-sm font-semibold text-navy">Practice</p>
        <ul className="mt-2 space-y-1 text-sm text-slate-600">
          {style.exercises.map((item) => <li key={item}>- {item}</li>)}
        </ul>
      </div>
    </motion.article>
  );
}
