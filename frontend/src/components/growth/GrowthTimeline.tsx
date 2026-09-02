import { motion } from "motion/react";
import { mockGrowthTimeline } from "../../data/mockGrowthTimeline";
import { fadeUp } from "../../lib/animations";
import { GrowthInsightCard } from "./GrowthInsightCard";
import { GrowthMilestoneCard } from "./GrowthMilestoneCard";

export function GrowthTimeline() {
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_0.35fr]">
      <div className="relative space-y-5 pl-6">
        <motion.div initial={{ scaleY: 0 }} whileInView={{ scaleY: 1 }} viewport={{ once: true }} className="absolute bottom-0 left-2 top-0 w-px origin-top bg-gradient-to-b from-teal to-organic" />
        {mockGrowthTimeline.map((item) => (
          <motion.div key={item.day} variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }} className="relative">
            <span className="absolute -left-[1.1rem] top-6 h-3 w-3 rounded-full bg-teal" />
            <GrowthMilestoneCard item={item} />
          </motion.div>
        ))}
      </div>
      <GrowthInsightCard />
    </div>
  );
}
