import { motion } from "motion/react";
import { fadeUp, staggerContainer } from "../../lib/animations";

const beats = [
  "Fear narrows possibility.",
  "Reflection restores agency.",
  "Collaboration expands contribution."
];

export function AnimatedStorySection() {
  return (
    <motion.section
      variants={staggerContainer}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.25 }}
      className="grid gap-4 md:grid-cols-3"
    >
      {beats.map((beat) => (
        <motion.article key={beat} variants={fadeUp} className="glass-card p-5 text-center font-display text-xl font-bold text-navy">
          {beat}
        </motion.article>
      ))}
    </motion.section>
  );
}
