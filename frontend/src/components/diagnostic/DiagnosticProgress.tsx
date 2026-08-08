import { Check } from "lucide-react";
import { motion } from "motion/react";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

export const diagnosticStepNames = [
  "Interests & Curiosity",
  "Fears & Uncertainty",
  "Values & Contribution",
  "Skills & Learning Style",
  "AI Experience",
];

export function DiagnosticProgress({ currentStep }: { currentStep: number }) {
  const reducedMotion = useReducedMotionPreference();
  const percentage = Math.round(((currentStep + 1) / diagnosticStepNames.length) * 100);

  return (
    <section className="glass-card overflow-hidden p-5" aria-label="Diagnostic progress">
      <div className="flex items-center justify-between gap-4 md:hidden">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-[color:var(--color-accent-action-muted)]">
            Step {currentStep + 1} of 5
          </p>
          <p className="mt-1 font-semibold theme-text">{diagnosticStepNames[currentStep]}</p>
        </div>
        <strong className="text-[color:var(--color-accent-action-muted)]">{percentage}%</strong>
      </div>

      <div className="relative hidden md:grid md:grid-cols-5">
        <div className="absolute left-[10%] right-[10%] top-5 h-px bg-[color:var(--border-soft)]" />
        <motion.div
          initial={false}
          animate={{ width: `${(currentStep / 4) * 80}%` }}
          transition={reducedMotion ? { duration: 0 } : { duration: 0.35 }}
          className="organic-progress-action absolute left-[10%] top-5 h-px"
        />
        {diagnosticStepNames.map((name, index) => (
          <div key={name} className="relative z-10 text-center">
            <span
              aria-current={index === currentStep ? "step" : undefined}
              className={`mx-auto grid h-10 w-10 place-items-center rounded-full border text-sm font-bold ${
                index < currentStep
                  ? "border-transparent bg-[color:var(--color-accent-success)] text-white"
                  : index === currentStep
                    ? "organic-action-selected"
                    : "border-[color:var(--border-soft)] bg-[color:var(--bg-glass)] theme-muted"
              }`}
            >
              {index < currentStep ? <Check size={16} /> : index + 1}
            </span>
            <p className={`mt-2 text-xs ${index === currentStep ? "font-bold organic-action-link" : "theme-muted"}`}>
              {name}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-200/60 dark:bg-white/10">
        <motion.div
          initial={false}
          animate={{ width: `${percentage}%` }}
          transition={reducedMotion ? { duration: 0 } : { duration: 0.35 }}
          className="organic-progress-action h-full rounded-full"
        />
      </div>
      <p className="mt-2 text-right text-xs theme-muted">
        {percentage}% - {4 - currentStep} step{4 - currentStep === 1 ? "" : "s"} remaining
      </p>
    </section>
  );
}
