import { Compass } from "lucide-react";
import { motion } from "motion/react";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

export function AnimatedHumanAIOrb() {
  const reducedMotion = useReducedMotionPreference();

  return (
    <motion.div
      className="hero-human-ai-orb"
      animate={reducedMotion ? undefined : { scale: [0.98, 1.035, 0.98] }}
      transition={{ duration: 4.8, repeat: Infinity, ease: "easeInOut" }}
      aria-hidden="true"
    >
      <motion.span
        className="hero-human-ai-orb-ring"
        animate={reducedMotion ? undefined : { rotate: 360 }}
        transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
      />
      <motion.span
        className="hero-human-ai-orb-ring hero-human-ai-orb-ring-alt"
        animate={reducedMotion ? undefined : { rotate: -360 }}
        transition={{ duration: 24, repeat: Infinity, ease: "linear" }}
      />
      <span className="hero-human-ai-orb-core">
        <Compass className="h-9 w-9 text-[#99f6e4]" />
        <span className="mt-2 text-center text-sm font-black leading-4 tracking-[0.22em]">
          HUMAN
          <br />+<br />
          AI
        </span>
      </span>
      <span className="hero-human-ai-orb-particle hero-human-ai-orb-particle-a" />
      <span className="hero-human-ai-orb-particle hero-human-ai-orb-particle-b" />
      <span className="hero-human-ai-orb-particle hero-human-ai-orb-particle-c" />
    </motion.div>
  );
}
