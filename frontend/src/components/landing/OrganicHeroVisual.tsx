import { lazy, Suspense } from "react";
import { HeroConceptNodes } from "./HeroConceptNodes";
import { HeroConnectionLines } from "./HeroConnectionLines";
import { CSSOrbFallback } from "./CSSOrbFallback";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

const HumanAIOrb3D = lazy(() => import("../three/HumanAIOrb3D").then((module) => ({ default: module.HumanAIOrb3D })));

export function OrganicHeroVisual() {
  const reducedMotion = useReducedMotionPreference();

  return (
    <div className="organic-hero-visual">
      <img
        src="/images/organicai-hero-human-ai-bg-v2.png"
        alt=""
        aria-hidden="true"
        loading="eager"
        className="organic-hero-bg"
      />
      <div className="organic-hero-overlay" />
      <div className="human-ai-orb-layer">
        {reducedMotion ? (
          <CSSOrbFallback />
        ) : (
          <Suspense fallback={<CSSOrbFallback />}>
            <HumanAIOrb3D />
          </Suspense>
        )}
      </div>
      <HeroConnectionLines />
      <HeroConceptNodes />
      <div className="hero-platform-glow" aria-hidden="true" />
    </div>
  );
}
