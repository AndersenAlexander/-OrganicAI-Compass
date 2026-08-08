import { motion } from "framer-motion";
import type { KeyboardEvent } from "react";
import type { JourneyStage } from "./types";

type JourneyStageNavigatorProps = {
  stages: JourneyStage[];
  activeIndex: number;
  onSelect: (index: number) => void;
};

export function JourneyStageNavigator({ stages, activeIndex, onSelect }: JourneyStageNavigatorProps) {
  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    if (event.key === "ArrowRight") {
      event.preventDefault();
      onSelect((index + 1) % stages.length);
      return;
    }

    if (event.key === "ArrowLeft") {
      event.preventDefault();
      onSelect((index - 1 + stages.length) % stages.length);
    }
  }

  return (
    <section className="how-page-section journey-navigator" aria-labelledby="journey-navigator-title">
      <header className="how-section-heading">
        <p>JOURNEY DASHBOARD</p>
        <h2 id="journey-navigator-title">A six-stage journey</h2>
        <span>Select a stage to understand how OrganicAI moves from reflection to practical action.</span>
      </header>
      <div className="journey-step-track" role="tablist" aria-label="Journey stages">
        <span className="journey-track-line" aria-hidden="true" />
        <motion.span
          className="journey-active-path"
          aria-hidden="true"
          animate={{ width: `${((activeIndex + 0.5) / stages.length) * 100}%` }}
          transition={{ duration: 0.35, ease: "easeOut" }}
        />
        {stages.map(({ icon: Icon, number, shortTitle, accent }, index) => {
          const isActive = activeIndex === index;
          return (
            <button
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-current={isActive ? "step" : undefined}
              className={`journey-step-button accent-${accent}`}
              key={shortTitle}
              onClick={() => onSelect(index)}
              onKeyDown={(event) => handleKeyDown(event, index)}
            >
              <span className="journey-step-number">{number}</span>
              <span className="journey-step-icon">
                <Icon size={20} />
              </span>
              <b>{shortTitle}</b>
              {isActive ? <motion.i layoutId="journey-active-dot" aria-hidden="true" /> : null}
            </button>
          );
        })}
      </div>
    </section>
  );
}
