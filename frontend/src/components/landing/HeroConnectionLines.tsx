import { motion } from "motion/react";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

const paths = [
  "M450 268 C430 195 405 120 388 86",
  "M450 268 C505 188 565 126 602 98",
  "M450 268 C574 225 720 214 805 205",
  "M450 268 C614 290 740 330 812 382",
  "M450 268 C365 284 230 302 130 338",
  "M450 268 C355 390 220 455 120 500",
  "M450 268 C455 390 455 505 450 590",
  "M450 268 C545 395 640 490 700 560",
  "M295 385 C350 340 395 303 450 268",
  "M605 385 C560 340 512 303 450 268"
];

export function HeroConnectionLines() {
  const reducedMotion = useReducedMotionPreference();

  return (
    <svg className="hero-connection-lines" viewBox="0 0 900 700" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="heroConnectionGradient" x1="0" x2="1">
          <stop stopColor="#84cc16" stopOpacity="0.12" />
          <stop offset="0.52" stopColor="#5eead4" stopOpacity="0.78" />
          <stop offset="1" stopColor="#38bdf8" stopOpacity="0.18" />
        </linearGradient>
        <filter id="heroConnectionGlow">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {paths.map((path, index) => (
        <motion.path
          key={path}
          d={path}
          fill="none"
          stroke="url(#heroConnectionGradient)"
          strokeWidth="1"
          strokeLinecap="round"
          filter="url(#heroConnectionGlow)"
          initial={reducedMotion ? false : { pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: index > 7 ? 0.34 : 0.26 }}
          transition={{ duration: 1.25, delay: index * 0.06, ease: "easeOut" }}
        />
      ))}
      {!reducedMotion ? (
        <>
          <circle r="3" fill="#99f6e4">
            <animateMotion dur="7s" repeatCount="indefinite" path={paths[8]} />
          </circle>
          <circle r="2.5" fill="#a3e635">
            <animateMotion dur="8.5s" repeatCount="indefinite" path={paths[9]} />
          </circle>
        </>
      ) : null}
    </svg>
  );
}
