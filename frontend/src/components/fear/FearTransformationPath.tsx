import { motion } from "motion/react";

const steps = ["Fear", "Clarity", "Agency", "Creative Action"];

export function FearTransformationPath() {
  return (
    <div className="relative grid gap-3 md:grid-cols-4">
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="absolute left-0 right-0 top-6 hidden h-px origin-left bg-gradient-to-r from-deepNavy via-teal to-organic md:block"
      />
      {steps.map((step, index) => (
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.12 }}
          className="organic-chip relative z-10 justify-center px-4 py-3 text-center text-sm font-bold"
        >
          {step}
        </motion.div>
      ))}
    </div>
  );
}
