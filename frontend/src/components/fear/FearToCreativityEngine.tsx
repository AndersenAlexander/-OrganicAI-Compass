import { motion } from "motion/react";
import { staggerContainer } from "../../lib/animations";
import type { FearTransform } from "../../types/profile";
import { EthicalReflectionCard } from "../ethics/EthicalReflectionCard";
import { FearStepCard } from "./FearStepCard";
import { FearTransformationPath } from "./FearTransformationPath";

export function FearToCreativityEngine({ result }: { result: FearTransform }) {
  const output = result.output;
  const validation = output.validation ?? output.fear_summary;
  const controls = output.what_user_can_control ?? output.what_the_user_can_control;
  const collaboration = output.collaboration_opportunity ?? output.ai_collaboration_opportunities.join(" ");
  const ethicalNote = output.ethical_note ?? output.ethical_cautions.join(" ");

  return (
    <div className="space-y-6">
      <FearTransformationPath />
      <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="grid gap-5 lg:grid-cols-2">
        <FearStepCard title="Validation" body={validation} />
        <FearStepCard title="What is real" body={output.what_is_real} />
        <FearStepCard title="What is uncertain" body={output.what_is_uncertain} />
        <FearStepCard title="What you can control" body={controls} />
        <FearStepCard title="Creative reframe" body={output.creative_reframe} />
        <FearStepCard title="Human-AI collaboration opportunity" body={collaboration} />
        <FearStepCard title="15-minute action" body={output.fifteen_minute_action ?? "Write down one small next action you can complete today."} />
        <FearStepCard title="7-day action" body={output.seven_day_action} accent />
      </motion.div>
      <EthicalReflectionCard compact />
      {ethicalNote ? <p className="text-sm leading-6 theme-muted"><span className="font-semibold text-[color:var(--teal)]">Ethical note:</span> {ethicalNote}</p> : null}
    </div>
  );
}
