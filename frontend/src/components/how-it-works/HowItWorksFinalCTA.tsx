import { ArrowRight, Bot, Compass, Sprout } from "lucide-react";
import { Link } from "react-router-dom";

type HowItWorksFinalCTAProps = {
  coachTo: string;
};

export function HowItWorksFinalCTA({ coachTo }: HowItWorksFinalCTAProps) {
  return (
    <section className="how-page-section how-final-cta" aria-labelledby="how-final-title">
      <div className="how-final-copy">
        <span>READY FOR THE NEXT STEP</span>
        <h2 id="how-final-title">
          Ready to move from uncertainty
          <br />
          to a practical direction?
        </h2>
        <div className="how-final-actions">
          <Link className="public-button" to="/diagnostic">
            Start Diagnostic <ArrowRight size={16} />
          </Link>
          <Link className="public-button secondary" to={coachTo}>
            Meet the AI Coach <Bot size={16} />
          </Link>
        </div>
      </div>
      <div className="how-final-visual" aria-hidden="true">
        <span className="how-final-compass">
          <Compass size={38} />
        </span>
        <span className="how-final-path" />
        <Sprout className="how-final-sprout sprout-a" size={34} />
        <Sprout className="how-final-sprout sprout-b" size={28} />
      </div>
    </section>
  );
}
