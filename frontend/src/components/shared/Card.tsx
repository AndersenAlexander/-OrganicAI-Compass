import type { ReactNode } from "react";
import { motion, type HTMLMotionProps } from "motion/react";

interface CardProps extends HTMLMotionProps<"div"> {
  children: ReactNode;
}

export function Card({ children, className = "", ...props }: CardProps) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className={`glass-card organic-depth-hover ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
}
