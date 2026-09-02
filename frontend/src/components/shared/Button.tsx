import type { ReactNode } from "react";
import { motion, type HTMLMotionProps } from "motion/react";

type ButtonVariant = "primary" | "secondary" | "ghost";

interface ButtonProps extends HTMLMotionProps<"button"> {
  children: ReactNode;
  variant?: ButtonVariant;
}

const styles: Record<ButtonVariant, string> = {
  primary: "organic-button",
  secondary: "organic-button-secondary",
  ghost: "bg-transparent text-[color:var(--color-accent-action-muted)] hover:bg-[color:var(--color-accent-action-soft)]"
};

export function Button({ children, className = "", variant = "primary", ...props }: ButtonProps) {
  return (
    <motion.button
      whileHover={{ y: -2, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[color:var(--color-accent-action-soft)] disabled:cursor-not-allowed disabled:opacity-60 ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </motion.button>
  );
}
