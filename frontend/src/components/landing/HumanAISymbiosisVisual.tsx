import { motion } from "motion/react";
import { OrganicHeroVisual } from "./OrganicHeroVisual";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

export function HumanAISymbiosisVisual() {
  const reducedMotion = useReducedMotionPreference();

  return (
    <motion.div
      initial={reducedMotion ? false : { opacity: 0, scale: 0.975 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className="relative h-full"
    >
      <OrganicHeroVisual />
    </motion.div>
  );
}
