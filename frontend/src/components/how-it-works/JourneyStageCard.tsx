import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { StageVisual } from "./StageVisual";
import type { JourneyStage } from "./types";

type JourneyStageCardProps = {
  stage: JourneyStage;
};

export function JourneyStageCard({ stage }: JourneyStageCardProps) {
  const Icon = stage.icon;

  return (
    <motion.article
      id={`stage-${stage.id}`}
      className={`journey-stage-card accent-${stage.accent}`}
      initial={false}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.38 }}
    >
      <span className="journey-stage-watermark">{stage.number}</span>
      <div className="journey-stage-copy">
        <span className="journey-stage-icon">
          <Icon size={24} />
        </span>
        <h3>{stage.cardTitle ?? stage.title}</h3>
        <p>{stage.cardDescription ?? stage.description}</p>
        <Link className="journey-action-link" to={stage.to}>
          {stage.action} <ArrowRight size={15} />
        </Link>
      </div>
      <StageVisual stageId={stage.id} compact />
    </motion.article>
  );
}
