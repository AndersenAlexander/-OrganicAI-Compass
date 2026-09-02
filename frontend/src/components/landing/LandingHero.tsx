import { ArrowRight, Play } from "lucide-react";
import { motion } from "motion/react";
import { fadeUp, staggerContainer } from "../../lib/animations";
import { HumanAISymbiosisVisual } from "./HumanAISymbiosisVisual";
import { TrustChips } from "./TrustChips";
import { Link } from "react-router-dom";

export function LandingHero() {
  return (
    <motion.section initial="hidden" animate="visible" variants={staggerContainer} className="landing-page-container landing-hero">
      <div className="landing-hero-scene">
        <HumanAISymbiosisVisual />
      </div>

      <motion.div variants={fadeUp} className="landing-hero-copy">
        <span className="landing-hero-badge"><span />HUMAN-AI GUIDANCE FOR A MEANINGFUL FUTURE</span>
        <h1 className="landing-hero-title">
          <span className="landing-hero-title-line">From fear to creativity,</span>
          <span className="landing-hero-title-line">purpose, and</span>
          <span className="landing-hero-title-line landing-hero-title-accent">human–AI collaboration</span>
        </h1>
        <p className="landing-hero-description">
          Discover your unique talents, transform fear about AI,
          and build a personalized roadmap to grow and create
          together with AI.
        </p>
        <div className="landing-hero-actions">
          <Link to="/diagnostic" className="hero-primary-cta">
            <span>Start Diagnostic</span>
            <span className="hero-primary-arrow"><ArrowRight size={18} /></span>
          </Link>
          <Link to="/how-it-works" className="hero-secondary-cta">
            <span>See How It Works</span>
            <span className="hero-secondary-play"><Play size={13} fill="currentColor" /></span>
          </Link>
        </div>
        <TrustChips />
      </motion.div>
    </motion.section>
  );
}
