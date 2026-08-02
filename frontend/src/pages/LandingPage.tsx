import { MVPFlow } from "../components/landing/MVPFlow";
import { LandingHero } from "../components/landing/LandingHero";
import { ParadigmComparison } from "../components/landing/ParadigmComparison";
import { SixPrinciples } from "../components/landing/SixPrinciples";
import { FeatureStrip } from "../components/landing/FeatureStrip";
import { QuoteStatsStrip } from "../components/landing/QuoteStatsStrip";
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

export function LandingPage() {
  const [searchParams] = useSearchParams();
  useEffect(() => {
    const section = searchParams.get("section");
    if (section) window.setTimeout(() => document.getElementById(section)?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
  }, [searchParams]);
  return (
    <div className="landing-page relative min-h-screen pb-7">
      <LandingHero />
      <FeatureStrip />
      <div className="landing-page-container landing-detail-grid">
        <ParadigmComparison />
        <SixPrinciples />
        <MVPFlow />
      </div>
      <QuoteStatsStrip />
    </div>
  );
}
