import { motion } from "motion/react";
import { fadeUp } from "../../lib/animations";

export function FearStepCard({ title, body, accent = false }: { title: string; body: string | string[]; accent?: boolean }) {
  return (
    <motion.article variants={fadeUp} className={`glass-card organic-depth-hover p-5 ${accent ? "ring-1 ring-lime-300/30" : ""}`}>
      <h3 className="font-display text-lg font-bold theme-text">{title}</h3>
      {Array.isArray(body) ? (
        <ul className="mt-3 space-y-2 text-sm leading-6 theme-muted">
          {body.map((item) => <li key={item}>- {item}</li>)}
        </ul>
      ) : (
        <p className="mt-3 text-sm leading-6 theme-muted">{body}</p>
      )}
    </motion.article>
  );
}
