import { motion } from "motion/react";

type PotentialConnectionProps = {
  x: number;
  y: number;
};

export function PotentialConnection({ x, y }: PotentialConnectionProps) {
  return (
    <motion.path
      d={`M 250 250 C ${250 + x * 0.35} ${250 + y * 0.08}, ${250 + x * 0.7} ${250 + y * 0.9}, ${250 + x} ${250 + y}`}
      fill="none"
      stroke="rgba(15,118,110,0.32)"
      strokeWidth="2"
      strokeLinecap="round"
      initial={{ pathLength: 0, opacity: 0 }}
      animate={{ pathLength: 1, opacity: 1 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    />
  );
}
