import { useState } from "react";
import { motion } from "motion/react";
import { staggerContainer } from "../../lib/animations";
import { CollaborationStyleCard, type CollaborationStyle } from "./CollaborationStyleCard";
import { CollaborationStyleQuiz } from "./CollaborationStyleQuiz";

const styles: CollaborationStyle[] = [
  { title: "AI as Mirror", description: "Reflects your thinking so patterns become visible.", usefulWhen: "you need clarity", risks: "confusing fluency with truth", prompts: ["Reflect the assumptions in this idea."], exercises: ["Journal with AI", "Compare two self-descriptions", "Name one blind spot"] },
  { title: "AI as Co-Creator", description: "Generates variations while you keep authorship.", usefulWhen: "you need options", risks: "losing your own voice", prompts: ["Give me three directions, each with a tradeoff."], exercises: ["Co-draft a concept", "Reject one option", "Refine one option"] },
  { title: "AI as Research Assistant", description: "Helps organize questions and evidence.", usefulWhen: "you need synthesis", risks: "uncited claims", prompts: ["List what I should verify first."], exercises: ["Build a source map", "Check one claim", "Summarize disagreements"] },
  { title: "AI as Mentor", description: "Structures learning and feedback loops.", usefulWhen: "you need guidance", risks: "outsourcing judgment", prompts: ["Teach this in three levels."], exercises: ["Ask for feedback", "Set a weekly drill", "Review progress"] },
  { title: "AI as Builder Assistant", description: "Turns ideas into drafts, systems, and next steps.", usefulWhen: "you need momentum", risks: "shipping before understanding", prompts: ["Turn this goal into a small prototype plan."], exercises: ["Build a checklist", "Create one artifact", "Review quality"] },
  { title: "AI as Ethical Challenger", description: "Questions impacts, blind spots, and hidden costs.", usefulWhen: "stakes are high", risks: "performative caution", prompts: ["What could harm people if this succeeds?"], exercises: ["Run a premortem", "List affected groups", "Define a red line"] }
];

export function AICollaborationStyle({ initialStyle }: { initialStyle?: string }) {
  const [selected, setSelected] = useState(initialStyle ?? "AI as Co-Creator");

  return (
    <section className="space-y-5">
      <div>
        <h2 className="font-display text-2xl font-bold text-navy">AI Collaboration Style</h2>
        <p className="mt-3 text-slate-600">Identify how AI is most useful when it supports, rather than replaces, your agency.</p>
      </div>
      <CollaborationStyleQuiz onSelect={setSelected} />
      <motion.div variants={staggerContainer} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.1 }} className="grid gap-5 lg:grid-cols-2">
        {styles.map((style) => (
          <CollaborationStyleCard key={style.title} style={style} featured={style.title === selected} />
        ))}
      </motion.div>
    </section>
  );
}
