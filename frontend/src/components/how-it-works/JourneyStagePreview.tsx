import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { StageVisual } from "./StageVisual";
import type { JourneyStage } from "./types";

type JourneyStagePreviewProps = {
  stage: JourneyStage;
};

export function JourneyStagePreview({ stage }: JourneyStagePreviewProps) {
  const Icon = stage.icon;

  return (
    <div className={`journey-stage-preview accent-${stage.accent}`} role="tabpanel" aria-live="polite">
      <AnimatePresence mode="wait">
        <motion.div
          key={stage.id}
          className="journey-preview-content"
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.24 }}
        >
          <div className="journey-preview-copy">
            <span className="journey-preview-kicker">
              <Icon size={18} />
              Stage {stage.number}
            </span>
            <h3>{stage.title}</h3>
            <p>{stage.description}</p>
            <div className="journey-preview-example">
              <small>{stage.exampleLabel}</small>
              {stage.examples.map((example) => (
                <span key={example}>{example}</span>
              ))}
            </div>
            <Link className="journey-action-link" to={stage.to}>
              {stage.action} <ArrowRight size={15} />
            </Link>
          </div>
          <StageVisual stageId={stage.id} />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
