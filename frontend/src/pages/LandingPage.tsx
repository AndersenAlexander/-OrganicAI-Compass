import { Database, Route, Sparkles, UserRoundSearch, type LucideIcon } from "lucide-react";
import { HeroVideoSlider } from "../components/landing/HeroVideoSlider";
import {
  BenefitsSection,
  FinalConversionSection,
  InsightsSection,
  PlatformIntroduction,
  PlatformJourney,
  ProductOverviewVideo,
  ResearchTrustSection,
  ServicesOverview,
  TestimonialsSection,
  VoiceCoachShowcase,
} from "../components/landing/HomeConversionSections";
import { heroVideoSlides } from "../config/heroVideoSlides";
import { useAppActions } from "../hooks/useAppActions";

type HomePillar = { Icon: LucideIcon; title: string; text: string };

const homePillars: HomePillar[] = [
  { Icon: UserRoundSearch, title: "Understand Yourself", text: "Begin with your human context." },
  { Icon: Database, title: "Ground AI in Knowledge", text: "Connect guidance to visible sources." },
  { Icon: Route, title: "Turn Insight into Action", text: "Build an editable path forward." },
  { Icon: Sparkles, title: "Grow with Confidence", text: "Reflect, adapt, and retain agency." },
];

function HomeValueStrip() {
  return (
    <div className="home-value-strip" data-testid="home-value-strip">
      {homePillars.map(({ Icon, title, text }) => (
        <article key={title}>
          <Icon size={22} />
          <div>
            <b>{title}</b>
            <span>{text}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

export function LandingPage() {
  document.title = "OrganicAI Compass - Design your future with AI";
  const { activeProfileId, openCoach } = useAppActions();

  return (
    <div className="home-page">
      <HeroVideoSlider slides={heroVideoSlides} />
      <div className="home-page-container">
        <HomeValueStrip />
        <PlatformIntroduction />
        <ProductOverviewVideo />
        <PlatformJourney activeProfileId={activeProfileId} />
        <ServicesOverview activeProfileId={activeProfileId} />
        <VoiceCoachShowcase activeProfileId={activeProfileId} onOpenCoach={openCoach} />
        <BenefitsSection />
        <TestimonialsSection />
        <ResearchTrustSection />
        <InsightsSection />
        <FinalConversionSection activeProfileId={activeProfileId} onOpenCoach={openCoach} />
      </div>
    </div>
  );
}
