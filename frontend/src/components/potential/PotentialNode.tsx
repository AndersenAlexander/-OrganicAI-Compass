import { motion } from "motion/react";

type PotentialNodeProps = {
  label: string;
  detail: string;
  x: number;
  y: number;
  onSelect: () => void;
};

export function PotentialNode({ label, detail, x, y, onSelect }: PotentialNodeProps) {
  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, scale: 0.5, x: 0, y: 0 }}
      animate={{ opacity: 1, scale: 1, x, y }}
      transition={{ duration: 0.65, ease: "easeOut" }}
      whileHover={{ y: y - 4, scale: 1.03 }}
      whileTap={{ scale: 0.98 }}
      onClick={onSelect}
      title={detail}
      className="absolute left-1/2 top-1/2 flex w-36 -translate-x-1/2 -translate-y-1/2 flex-col items-center rounded-2xl border border-white/80 bg-white/85 p-3 text-center shadow-sm"
    >
      <span className="text-sm font-bold text-navy">{label}</span>
      <span className="mt-1 line-clamp-2 text-xs text-slate-500">{detail}</span>
    </motion.button>
  );
}
