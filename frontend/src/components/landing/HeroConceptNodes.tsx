import { BookOpen, Cloud, Eye, Heart, Route, Sparkles, Star, UserRoundCheck } from "lucide-react";
import { motion } from "motion/react";
import type { LucideIcon } from "lucide-react";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";
import { useNavigate } from "react-router-dom";
import { useAppActions } from "../../hooks/useAppActions";

type ConceptNode = {
  label: string;
  icon: LucideIcon;
  className: string;
  delay: number;
};

const nodes: ConceptNode[] = [
  { label: "Talents", icon: Star, className: "top-[7%] left-[38%]", delay: 0.05 },
  { label: "Values", icon: Heart, className: "top-[7%] left-[59%]", delay: 0.12 },
  { label: "Fears", icon: Cloud, className: "top-[24%] right-[6%]", delay: 0.19 },
  { label: "Learning Style", icon: BookOpen, className: "top-[43%] right-[3%]", delay: 0.26 },
  { label: "Clarity", icon: Sparkles, className: "top-[39%] left-[10%]", delay: 0.33 },
  { label: "Perspective", icon: Eye, className: "bottom-[20%] left-[10%]", delay: 0.4 },
  { label: "Empowerment", icon: UserRoundCheck, className: "bottom-[10%] left-[44%]", delay: 0.47 },
  { label: "Roadmap", icon: Route, className: "bottom-[13%] right-[18%]", delay: 0.54 }
];

export function HeroConceptNodes() {
  const reducedMotion = useReducedMotionPreference();
  const navigate = useNavigate();
  const { navigateToProfile, navigateToRoadmap, navigateToFearTransformer, openCoach } = useAppActions();

  const activate = (label: string) => {
    if (["Talents", "Values", "Empowerment"].includes(label)) navigateToProfile();
    else if (label === "Fears") navigateToFearTransformer();
    else if (label === "Learning Style") navigate("/learning-paths");
    else if (label === "Clarity") openCoach("Help me gain clarity about AI and my future.");
    else if (label === "Perspective") openCoach("Help me explore a different perspective.");
    else if (label === "Roadmap") navigateToRoadmap();
  };

  return (
    <div className="hero-concept-nodes pointer-events-none absolute inset-0 z-[15]">
      {nodes.map(({ label, icon: Icon, className, delay }, index) => (
        <motion.button
          type="button"
          key={label}
          initial={reducedMotion ? false : { opacity: 0, y: 16, scale: 0.94 }}
          animate={
            reducedMotion
              ? { opacity: 1 }
              : { opacity: 1, y: [0, index % 2 ? -8 : 8, 0], scale: 1 }
          }
          transition={{
            opacity: { duration: 0.45, delay },
            scale: { duration: 0.45, delay },
            y: { duration: 5 + index * 0.2, repeat: Infinity, ease: "easeInOut", delay }
          }}
          onClick={() => activate(label)}
          aria-label={`Open ${label}`}
          className={`hero-concept-node pointer-events-auto absolute focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[color:var(--color-accent-action-soft)] ${className}`}
        >
          <span className="hero-concept-node-icon">
            <Icon size={15} />
          </span>
          <span>{label}</span>
        </motion.button>
      ))}
    </div>
  );
}
