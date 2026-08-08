import type { LucideIcon } from "lucide-react";
import { motion } from "motion/react";

export function HeroConceptNode({ label, icon: Icon, positionClass, delay = 0 }: { label: string; icon: LucideIcon; positionClass: string; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`absolute z-30 flex items-center gap-2 rounded-full border border-white/80 bg-white/82 px-3 py-2 text-xs font-bold text-navy shadow-sm backdrop-blur ${positionClass}`}
    >
      <span className="grid h-6 w-6 place-items-center rounded-full bg-teal/10 text-teal">
        <Icon size={14} />
      </span>
      {label}
    </motion.div>
  );
}
