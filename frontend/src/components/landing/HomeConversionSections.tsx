import {
  ArrowRight,
  AudioWaveform,
  BadgeCheck,
  BookOpenCheck,
  Brain,
  BriefcaseBusiness,
  CirclePlay,
  ClipboardCheck,
  Compass,
  Database,
  FileCheck2,
  FileSearch,
  GraduationCap,
  Layers3,
  Lightbulb,
  Map,
  MessageCircle,
  Mic,
  Network,
  Newspaper,
  Quote,
  Radar,
  RefreshCw,
  Route,
  Scale,
  SearchCheck,
  ShieldCheck,
  Sparkles,
  Target,
  UserRoundSearch,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { blogArticles } from "../../data/blogArticles";
import {
  buildHomeRoute,
  homeBenefits,
  homeJourneySteps,
  homeServiceGroups,
  homeTrustModules,
  homeVideoAssets,
  homeVoiceBoundaries,
  homeVoiceExamples,
  type HomeJourneyStep,
  type HomeServiceGroup,
} from "../../config/homeConversionContent";
import { homeTestimonials } from "../../config/homeTestimonials";
import { ProductDemoVideo } from "./ProductDemoVideo";

type HomeConversionSectionsProps = {
  activeProfileId: string;
  onOpenCoach: (prompt?: string) => void;
};

type HeadingProps = {
  eyebrow: string;
  title: string;
  description?: string;
};

const stepIcons: Record<string, LucideIcon> = {
  "natural-discovery": UserRoundSearch,
  "career-interests": SearchCheck,
  "human-potential": Compass,
  "capability-assessment": ClipboardCheck,
  "four-layer-model": Layers3,
  "career-hypotheses": Lightbulb,
  "career-experiments": Target,
  "evidence-passport": FileCheck2,
  recalibration: RefreshCw,
  "market-context": Radar,
  "application-journey": FileSearch,
  "interview-journey": MessageCircle,
  "decision-intelligence": Brain,
};

const serviceIcons: Record<HomeServiceGroup["id"], LucideIcon> = {
  "career-discovery": UserRoundSearch,
  "career-direction": Route,
  "evidence-development": FileCheck2,
  "market-jobs": Radar,
  "application-support": BriefcaseBusiness,
  "interview-support": MessageCircle,
  "decision-intelligence": Scale,
  "ai-support": AudioWaveform,
};

const modelLayers = [
  ["NATURAL FIT", "What attracts you?"],
  ["CAPABILITY FIT", "What can you currently do?"],
  ["EVIDENCE STRENGTH", "What can you demonstrate?"],
  ["TRANSITION FEASIBILITY", "How realistic is the transition now?"],
];

const decisionModules = [
  ["Adaptive Evidence-Gain", "What should I test next?"],
  ["Pareto Simulator", "What trade-offs exist between alternatives?"],
  ["Recommendation Robustness", "Would this recommendation change if assumptions changed?"],
  ["Recommendation Provenance", "Why did this recommendation appear?"],
  ["Synthetic Fairness", "Research-oriented synthetic checks, not certification."],
];

const introductionSignals = [
  ["Explainable", "Career Hypotheses"],
  ["Testable", "Career Experiments"],
  ["Evidence-aware", "Evidence Passport"],
  ["Revisable", "Recalibration"],
];

function SectionHeading({ eyebrow, title, description }: HeadingProps) {
  return (
    <header className="home-conversion-heading">
      <p className="home-eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {description ? <span>{description}</span> : null}
    </header>
  );
}

function RouteLink({
  routeKey,
  activeProfileId,
  children,
  className,
}: {
  routeKey: Parameters<typeof buildHomeRoute>[0];
  activeProfileId: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Link className={className} to={buildHomeRoute(routeKey, activeProfileId)}>
      {children}
    </Link>
  );
}

export function PlatformIntroduction() {
  return (
    <section id="what-is-organicai" className="home-platform-intro home-conversion-section" data-testid="home-platform-intro">
      <div>
        <p className="home-eyebrow">WHAT IS ORGANICAI COMPASS?</p>
        <h2>
          Understand yourself.
          <br />
          Explore possibilities.
          <br />
          Build evidence.
          <br />
          Make better career decisions.
        </h2>
      </div>
      <div className="home-platform-intro__body">
        <p>
          OrganicAI Compass is a human-centred career decision-support platform designed to help people understand their
          professional preferences, capabilities and evidence, explore possible career directions, test those directions
          and make more informed decisions.
        </p>
        <p>
          Instead of telling the user what their perfect career is, the platform creates explainable Career Hypotheses
          that can be tested and recalibrated as new evidence becomes available.
        </p>
        <div className="home-platform-intro__signals" aria-label="OrganicAI Compass product signals">
          {introductionSignals.map(([label, value]) => (
            <span key={label}>
              <b>{label}</b>
              {value}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

export function ProductOverviewVideo() {
  const video = homeVideoAssets.overview;

  return (
    <section id="overview-video" className="home-overview-video home-conversion-section" data-testid="home-overview-video">
      <SectionHeading
        eyebrow="PLATFORM OVERVIEW"
        title="See OrganicAI Compass in action."
        description="From Natural Discovery to Career Experiments, market analysis and interview preparation."
      />
      <ProductDemoVideo
        src={video.src}
        poster={video.poster}
        title={video.title}
        caption={video.caption}
        testId="home-overview-product-video"
      />
    </section>
  );
}

function FourLayerModel() {
  return (
    <div className="home-four-layer" aria-label="Four-layer career model">
      {modelLayers.map(([title, text]) => (
        <article key={title}>
          <span>{title}</span>
          <p>{text}</p>
        </article>
      ))}
      <div className="home-four-layer__context">
        <b>Additional context</b>
        <span>Market Fit and Support Fit can be considered when reliable context becomes available.</span>
      </div>
    </div>
  );
}

function RecalibrationVisual() {
  return (
    <div className="home-recalibration-visual" aria-label="Recalibration flow">
      {["BEFORE EXPERIMENT", "NEW EVIDENCE", "UPDATED HYPOTHESIS"].map((item, index) => (
        <span key={item}>
          <b>{String(index + 1).padStart(2, "0")}</b>
          {item}
        </span>
      ))}
    </div>
  );
}

function DecisionVisual() {
  return (
    <div className="home-decision-modules" aria-label="Decision intelligence modules">
      {decisionModules.map(([title, text]) => (
        <article key={title}>
          <Network size={18} />
          <b>{title}</b>
          <span>{text}</span>
        </article>
      ))}
    </div>
  );
}

function JourneyMedia({ step }: { step: HomeJourneyStep }) {
  if (step.layout === "model") return <FourLayerModel />;
  if (step.layout === "recalibration") return <RecalibrationVisual />;
  if (step.layout === "decision") return <DecisionVisual />;
  if (!step.video) return null;

  const video = homeVideoAssets[step.video];
  return (
    <ProductDemoVideo
      src={video.src}
      poster={video.poster}
      title={video.title}
      caption={video.caption}
      testId={`home-journey-video-${step.id}`}
    />
  );
}

function PlatformJourneySection({ step, activeProfileId }: { step: HomeJourneyStep; activeProfileId: string }) {
  const Icon = stepIcons[step.id] || Sparkles;

  return (
    <article
      className={`home-journey-card home-journey-card--${step.layout}`}
      data-step-id={step.id}
      data-testid="home-journey-step"
    >
      <div className="home-journey-card__copy">
        <div className="home-journey-card__label">
          <Icon size={20} />
          <span>{step.eyebrow}</span>
        </div>
        <h3>{step.title}</h3>
        <p>{step.description}</p>
        <div className="home-journey-card__gain">
          <b>What you gain</b>
          <span>{step.gain}</span>
        </div>
        <div className="home-journey-card__signals" aria-label={`${step.shortLabel} signals`}>
          {step.signals.map((signal) => (
            <span key={signal}>{signal}</span>
          ))}
        </div>
        <RouteLink activeProfileId={activeProfileId} routeKey={step.routeKey}>
          {step.ctaLabel} <ArrowRight size={14} />
        </RouteLink>
      </div>
      <div className="home-journey-card__media">
        <JourneyMedia step={step} />
      </div>
    </article>
  );
}

export function PlatformJourney({ activeProfileId }: { activeProfileId: string }) {
  return (
    <section id="how-it-works" className="home-product-journey home-conversion-section" data-testid="home-product-journey">
      <SectionHeading
        eyebrow="HOW ORGANICAI COMPASS WORKS"
        title="A real product journey from discovery to decision."
        description="The homepage journey follows the implemented OrganicAI order, from Natural Discovery through evidence, applications, interviews and decision intelligence."
      />
      <div className="home-product-journey__steps">
        {homeJourneySteps.map((step) => (
          <PlatformJourneySection key={step.id} activeProfileId={activeProfileId} step={step} />
        ))}
      </div>
    </section>
  );
}

export function ServicesOverview({ activeProfileId }: { activeProfileId: string }) {
  return (
    <section id="services" className="home-services home-conversion-section" data-testid="home-services">
      <SectionHeading
        eyebrow="SERVICES"
        title="What you can do with OrganicAI Compass."
        description="The platform groups discovery, direction, evidence, market context, applications, interviews, decision intelligence and AI support into one coherent career workflow."
      />
      <div className="home-services__grid">
        {homeServiceGroups.map((service) => {
          const Icon = serviceIcons[service.id];
          return (
            <article
              className={`home-service-card home-service-card--${service.tone} ${service.wide ? "home-service-card--wide" : ""}`}
              key={service.id}
            >
              <Icon size={26} />
              <p>{service.title}</p>
              <h3>{service.description}</h3>
              <ul>
                {service.capabilities.map((capability) => (
                  <li key={capability}>
                    <BadgeCheck size={15} />
                    {capability}
                  </li>
                ))}
              </ul>
              <RouteLink activeProfileId={activeProfileId} routeKey={service.routeKey}>
                {service.ctaLabel} <ArrowRight size={14} />
              </RouteLink>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export function VoiceCoachShowcase({ activeProfileId, onOpenCoach }: HomeConversionSectionsProps) {
  const video = homeVideoAssets.voice;

  return (
    <section id="voice" className="home-voice home-conversion-section" data-testid="home-voice">
      <div className="home-voice__copy">
        <p className="home-eyebrow">TALK TO ORGANICAI</p>
        <h2>
          You do not always have to navigate.
          <br />
          You can talk to your AI Coach.
        </h2>
        <p>
          OrganicAI Coach provides a conversational layer over the platform. Users can ask questions, request
          explanations, explore recommendations and move through parts of the experience using natural conversation.
          Depending on the active configuration, interaction can include voice as well as text.
        </p>
        <div className="home-voice__actions">
          <button
            type="button"
            className="home-button"
            data-testid="home-voice-open-coach"
            onClick={() => onOpenCoach("What career directions are currently worth testing?")}
          >
            <Mic size={16} /> Talk to OrganicAI Coach
          </button>
          <RouteLink activeProfileId={activeProfileId} className="home-voice__full-link" routeKey="coach">
            Open full Coach <ArrowRight size={14} />
          </RouteLink>
        </div>
        <div className="home-voice__examples" aria-label="Example OrganicAI Coach questions">
          {homeVoiceExamples.map((example) => (
            <span key={example}>{example}</span>
          ))}
        </div>
        <ul className="home-voice__boundaries">
          {homeVoiceBoundaries.map((boundary) => (
            <li key={boundary}>
              <ShieldCheck size={15} />
              {boundary}
            </li>
          ))}
        </ul>
      </div>
      <div className="home-voice__media">
        <div className="home-voice__visual" aria-label="Voice coach states">
          <span>
            <Mic size={16} /> microphone
          </span>
          <i />
          <span>
            <AudioWaveform size={16} /> transcript
          </span>
          <i />
          <span>
            <MessageCircle size={16} /> response
          </span>
        </div>
        <ProductDemoVideo
          src={video.src}
          poster={video.poster}
          title={video.title}
          caption={video.caption}
          testId="home-voice-video"
        />
      </div>
    </section>
  );
}

export function BenefitsSection() {
  return (
    <section id="benefits" className="home-benefits home-conversion-section" data-testid="home-benefits">
      <div className="home-benefits__statement">
        <p className="home-eyebrow">WHY IT MATTERS</p>
        <h2>What OrganicAI Compass can help you do.</h2>
        <p>
          The goal is not a guaranteed outcome. The goal is a clearer, more evidence-aware way to understand options,
          test directions and make decisions with less hidden assumption.
        </p>
      </div>
      <div className="home-benefits__outcomes">
        {homeBenefits.map((benefit, index) => (
          <span key={benefit}>
            <b>{String(index + 1).padStart(2, "0")}</b>
            {benefit}
          </span>
        ))}
      </div>
    </section>
  );
}

export function TestimonialsSection() {
  return (
    <section id="testimonials" className="home-testimonials home-conversion-section" data-testid="home-testimonials">
      <SectionHeading
        eyebrow="SOCIAL PROOF"
        title="Built around real human decisions."
        description="The homepage includes a testimonial architecture, but it does not display fictional users as real evidence."
      />
      {homeTestimonials.length > 0 ? (
        <div className="home-testimonials__grid">
          {homeTestimonials.slice(0, 3).map((testimonial) => (
            <blockquote key={`${testimonial.name}-${testimonial.context}`}>
              <Quote size={24} />
              <p>{testimonial.quote}</p>
              <footer>
                <b>{testimonial.name}</b>
                <span>{testimonial.role}</span>
                <small>{testimonial.context}</small>
              </footer>
            </blockquote>
          ))}
        </div>
      ) : (
        <div className="home-testimonials__empty" data-testid="home-testimonials-empty">
          <Quote size={30} />
          <h3>Real testimonial content has not been supplied yet.</h3>
          <p>
            Add verified testimonials in <code>frontend/src/config/homeTestimonials.ts</code>. Until then, the production
            homepage avoids fabricated names, quotes, outcomes, companies and success metrics.
          </p>
        </div>
      )}
    </section>
  );
}

export function ResearchTrustSection() {
  return (
    <section id="research" className="home-trust home-conversion-section" data-testid="home-trust">
      <div>
        <p className="home-eyebrow">BUILT FOR EXPLAINABILITY</p>
        <h2>
          AI guidance should be understandable,
          <br />
          not mysterious.
        </h2>
        <p>
          OrganicAI Compass is designed around visible reasoning, evidence-based recommendations, user control,
          limitations and privacy-aware interaction patterns.
        </p>
        <div className="home-trust__links">
          <Link className="home-button" to="/research">
            Research <ArrowRight size={15} />
          </Link>
          <Link to="/about/recommendation-system-card">System Card</Link>
          <Link to="/principles">Principles</Link>
        </div>
      </div>
      <div className="home-trust__grid">
        {homeTrustModules.map((module) => (
          <article key={module.title}>
            <ShieldCheck size={20} />
            <h3>{module.title}</h3>
            <p>{module.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function InsightsSection() {
  const articles = [...blogArticles].sort((a, b) => Number(b.featured) - Number(a.featured)).slice(0, 3);

  return (
    <section id="insights" className="home-insights home-conversion-section" data-testid="home-insights">
      <SectionHeading
        eyebrow="BLOG / INSIGHTS / RESOURCES"
        title="Learn before you decide."
        description="Research notes and explainers help visitors understand the product, the responsible AI boundaries and the future-of-work context behind the prototype."
      />
      <div className="home-insights__grid">
        {articles.map((article) => (
          <article key={article.slug} data-testid="home-insight-card">
            <div className={`home-insight-visual home-insight-visual--${article.heroVariant}`} aria-hidden="true">
              <Newspaper size={28} />
              <span>{article.category}</span>
            </div>
            <p>{article.contentType}</p>
            <h3>{article.title}</h3>
            <span>{article.excerpt}</span>
            <Link to={`/blog/${article.slug}`}>
              Read Article <ArrowRight size={14} />
            </Link>
            <small>{article.readingTime}</small>
          </article>
        ))}
      </div>
      <Link className="home-insights__cta" to="/blog">
        Explore Insights <ArrowRight size={15} />
      </Link>
    </section>
  );
}

export function FinalConversionSection({ onOpenCoach }: HomeConversionSectionsProps) {
  return (
    <section className="home-final-conversion home-conversion-section" data-testid="home-final-conversion">
      <div>
        <p className="home-eyebrow">START WITH YOURSELF</p>
        <h2>Your next direction does not have to begin with a guess.</h2>
        <p>Begin with Natural Discovery and build a career hypothesis you can understand, test and refine.</p>
        <div className="home-final-conversion__actions">
          <Link className="home-button" to="/diagnostic">
            Start Your Diagnostic <ArrowRight size={16} />
          </Link>
          <button type="button" onClick={() => onOpenCoach()} data-testid="home-final-open-coach">
            <Mic size={16} /> Talk to OrganicAI Coach
          </button>
          <Link to="/how-it-works">See How It Works</Link>
        </div>
      </div>
      <div className="home-final-conversion__orb" aria-hidden="true">
        <Compass size={58} />
        <Workflow size={34} />
        <CirclePlay size={30} />
        <GraduationCap size={30} />
        <Database size={30} />
        <BookOpenCheck size={30} />
        <Map size={30} />
      </div>
    </section>
  );
}
