import { useState } from "react";
import { motion } from "motion/react";
import { mockScenarios } from "../../data/mockScenarios";
import { staggerContainer } from "../../lib/animations";
import { ScenarioCard } from "./ScenarioCard";
import { ScenarioComparison } from "./ScenarioComparison";

export function FutureScenarioSimulator() {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const selected = mockScenarios.filter((item) => selectedIds.includes(item.id));
  const toggle = (id: string) =>
    setSelectedIds((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < 2 ? [...current, id] : [current[1], id]);

  return (
    <div className="space-y-6">
      <motion.div variants={staggerContainer} initial="hidden" whileInView="visible" viewport={{ once: true }} className="grid gap-5 lg:grid-cols-2">
        {mockScenarios.map((scenario) => <ScenarioCard key={scenario.id} scenario={scenario} selected={selectedIds.includes(scenario.id)} onToggle={() => toggle(scenario.id)} />)}
      </motion.div>
      <ScenarioComparison scenarios={selected} />
    </div>
  );
}
