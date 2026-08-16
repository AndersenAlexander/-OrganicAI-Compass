import { motion } from "framer-motion";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";
import type { PipelineLayer } from "./types";

type TechnicalPipelineProps = {
  layers: PipelineLayer[];
};

const techChips = ["React", "TypeScript", "FastAPI", "SQLite", "RAG", "OpenAI", "ElevenLabs", "React Three Fiber"];

export function TechnicalPipeline({ layers }: TechnicalPipelineProps) {
  const reduced = useReducedMotionPreference();

  return (
    <section className="how-page-section pipeline-architecture technical-architecture-section" aria-labelledby="pipeline-title">
      <header className="how-section-heading">
        <p>TECHNICAL ARCHITECTURE</p>
        <h2 id="pipeline-title">What happens behind the interface</h2>
        <span>A transparent view of the OrganicAI processing pipeline.</span>
      </header>
      <div className="pipeline-panel">
        <div className="pipeline-track" aria-label="OrganicAI processing pipeline">
          <span className="pipeline-line" aria-hidden="true" />
          <motion.span
            className="pipeline-energy"
            aria-hidden="true"
            animate={reduced ? undefined : { left: ["2%", "98%"] }}
            transition={reduced ? undefined : { duration: 7, repeat: Infinity, ease: "easeInOut" }}
          />
          {layers.map(({ title, labels, description, icon: Icon }, index) => (
            <article key={title} className="pipeline-layer">
              <span className="pipeline-layer-node">
                <b>{index + 1}</b>
                <Icon size={21} />
              </span>
              <h3>{title}</h3>
              <p>{description}</p>
              <div className="pipeline-labels">
                {labels.map((label) => (
                  <span key={label}>{label}</span>
                ))}
              </div>
              {index < layers.length - 1 ? <i className="pipeline-arrow" aria-hidden="true" /> : null}
            </article>
          ))}
        </div>
        <div className="pipeline-tech-chips" aria-label="Technologies used">
          {techChips.map((chip) => (
            <span key={chip}>{chip}</span>
          ))}
        </div>
      </div>
    </section>
  );
}
