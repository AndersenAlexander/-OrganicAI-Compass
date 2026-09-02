import { motion } from "motion/react";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

const paths = [
  "M180 220 C270 172, 356 188, 442 252 C512 304, 570 310, 640 244",
  "M180 262 C270 240, 348 246, 442 276 C522 302, 582 304, 640 284",
  "M180 302 C270 322, 350 320, 442 300 C516 286, 580 292, 640 324"
];

export function FlowingConnectionLines() {
  const reducedMotion = useReducedMotionPreference();
  return (
    <svg className="absolute inset-0 z-10 h-full w-full" viewBox="0 0 800 640" aria-hidden="true">
      {paths.map((d, index) => (
        <motion.path
          key={d}
          d={d}
          fill="none"
          stroke={index === 0 ? "rgba(20,184,166,0.58)" : index === 1 ? "rgba(132,204,22,0.46)" : "rgba(56,189,248,0.48)"}
          strokeWidth={index === 1 ? 3 : 2}
          strokeLinecap="round"
          initial={reducedMotion ? false : { pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 1.2, delay: 0.32 + index * 0.1 }}
        />
      ))}
      {[["250", "206"], ["322", "238"], ["398", "268"], ["470", "286"], ["548", "292"], ["606", "280"]].map(([cx, cy], index) => (
        <motion.circle
          key={`${cx}-${cy}`}
          cx={cx}
          cy={cy}
          r="4"
          fill={index % 2 === 0 ? "#14b8a6" : "#84cc16"}
          animate={reducedMotion ? undefined : { opacity: [0.4, 1, 0.4], scale: [1, 1.3, 1] }}
          transition={{ duration: 2.8, repeat: Infinity, delay: index * 0.18 }}
        />
      ))}
    </svg>
  );
}
