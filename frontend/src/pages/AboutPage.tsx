import {
  ArrowRight,
  AudioWaveform,
  BookOpenCheck,
  BriefcaseBusiness,
  Compass,
  Database,
  GraduationCap,
  Leaf,
  Network,
  Palette,
  PlayCircle,
  Route,
  ShieldCheck,
  UserRound,
  UserRoundSearch,
  Users,
  Waves
} from "lucide-react";
import { Suspense, type SyntheticEvent } from "react";
import { Link } from "react-router-dom";
import { AboutCompassScene } from "../components/three/AboutCompassScene";
import { AboutCompassFallback } from "../components/three/AboutCompassFallback";
import { OrganicPageBackdrop } from "../components/public/OrganicPageBackdrop";
import { PublicPageShell } from "../components/public/PublicPageShell";
import { ABOUT_ASSETS } from "../config/aboutAssets";
import { getActiveProfileId } from "../lib/activeProfile";

const issueCards = [
  {
    icon: Waves,
    title: "Fear and uncertainty",
    text: "Too much change, too fast. People feel anxious about AI's impact on work and future."
  },
  {
    icon: Network,
    title: "Fragmented information",
    text: "Scattered, technical, and often conflicting content makes it hard to know what to trust."
  },
  {
    icon: Compass,
    title: "Loss of direction",
    text: "Without a clear starting point, it is difficult to take action or build a path that feels right."
  }
];

const researchDomains = [
  {
    icon: Users,
    title: "Human-centred AI",
    text: "Designing with empathy, context, and human flourishing at the core.",
    focus: "People & Context"
  },
  {
    icon: ShieldCheck,
    title: "Explainable & Responsible AI",
    text: "Building trust through transparency, fairness, and accountability.",
    focus: "Trust & Ethics"
  },
  {
    icon: Network,
    title: "Recommender Systems & Personalization",
    text: "Delivering the right knowledge and guidance at the right time.",
    focus: "Relevance & Fit"
  },
  {
    icon: AudioWaveform,
    title: "Voice Interaction & Conversational Interfaces",
    text: "Making AI accessible through natural, inclusive conversations.",
    focus: "Accessibility"
  }
];

const handleImageError = (event: SyntheticEvent<HTMLImageElement>) => {
  if (import.meta.env.DEV) {
    console.error("OrganicAI About image failed:", event.currentTarget.src);
  }
};

export function AboutPage() {
  document.title = "OrganicAI Compass - About";
  const activeProfileId = getActiveProfileId();

  const platformCards = [
    {
      icon: UserRoundSearch,
      title: "Human Diagnostic",
      text: "Discover your strengths, values, and AI fluency through a science-backed assessment.",
      to: "/diagnostic",
      accent: "teal"
    },
    {
      icon: Database,
      title: "RAG Knowledge Base",
      text: "Curated, research-informed content tailored to your context and evolving needs.",
      to: "/knowledge-base",
      accent: "cyan"
    },
    {
      icon: AudioWaveform,
      title: "Voice AI Coach",
      text: "Have natural conversations that clarify, challenge, and guide your thinking.",
      to: `/coach/${activeProfileId}`,
      accent: "violet"
    },
    {
      icon: Route,
      title: "Personalized Roadmap",
      text: "Receive actionable recommendations and next steps aligned with your goals.",
      to: `/roadmap/${activeProfileId}`,
      accent: "green"
    }
  ];

  const personas = [
    {
      icon: BriefcaseBusiness,
      title: "Professionals navigating AI change",
      text: "Build confidence, stay relevant, and lead with clarity in an evolving landscape.",
      to: `/profile/${activeProfileId}`,
      outcome: "Clarity and adaptation"
    },
    {
      icon: GraduationCap,
      title: "Students and lifelong learners",
      text: "Develop future-ready skills and make smarter learning and career decisions.",
      to: "/learning-paths",
      outcome: "Future-ready learning"
    },
    {
      icon: Palette,
      title: "Designers, creators, and interdisciplinary innovators",
      text: "Explore new possibilities and co-create meaningful solutions with AI.",
      to: "/co-creation-studio",
      outcome: "Meaningful co-creation"
    }
  ];

  return (
    <PublicPageShell>
      <OrganicPageBackdrop />
      <section className="about-hero" aria-labelledby="about-title">
        <div className="about-hero-copy">
          <p className="about-eyebrow">ABOUT ORGANICAI COMPASS</p>
          <h1 id="about-title" className="about-hero-title">
            <span className="about-hero-title-line">
              A <span className="about-hero-title-accent">human-centred</span>
            </span>
            <span className="about-hero-title-line">compass for the age of AI</span>
          </h1>
          <p className="about-lead about-hero-description">
            We help people understand their strengths, transform uncertainty about AI, and create a meaningful path
            for human-AI collaboration - rooted in purpose, guided by insight, and designed for real impact.
          </p>
          <div className="about-actions about-hero-actions">
            <Link className="public-button" to="/diagnostic">
              Start Your Diagnostic <ArrowRight size={17} />
            </Link>
            <Link className="public-button secondary" to="/how-it-works">
              <PlayCircle size={17} /> See How It Works
            </Link>
          </div>
          <div className="about-trust about-trust-row" aria-label="Platform qualities">
            {[
              [UserRound, "Human-centred"],
              [BookOpenCheck, "Research-informed"],
              [ShieldCheck, "Privacy-aware"],
              [AudioWaveform, "Voice-enabled"]
            ].map(([Icon, label]) => (
              <span key={label as string}>
                <Icon size={15} /> {label as string}
              </span>
            ))}
          </div>
        </div>
        <div className="about-hero-scene" aria-hidden="true">
          <img
            className="about-hero-environment-image"
            src={ABOUT_ASSETS.hero}
            alt=""
            aria-hidden="true"
            loading="eager"
            fetchPriority="high"
            decoding="async"
            onError={handleImageError}
          />
          <div className="about-hero-environment-overlay" aria-hidden="true" />
          <div className="about-hero-atmospheric-glow" aria-hidden="true" />
          <div className="about-hero-r3f-layer">
            <Suspense fallback={<AboutCompassFallback />}>
              <AboutCompassScene />
            </Suspense>
          </div>
        </div>
      </section>

      <div className="about-content-mosaic">
        <section className="about-mosaic-panel about-why-panel" aria-labelledby="about-why-title">
          <h2 id="about-why-title" className="about-panel-title">
            1. Why OrganicAI Compass exists
          </h2>
          <div className="about-why-grid about-why-content">
            <article className="about-statement-card">
              <span className="about-plant-orb">
                <Leaf size={30} />
              </span>
              <p>
                <strong>AI is transforming everything.</strong>
                <span>But people are left with more questions than answers.</span>
              </p>
              <small>
                OrganicAI Compass exists to bring clarity, confidence, and direction to your human-AI journey.
              </small>
            </article>
            {issueCards.map(({ icon: Icon, title, text }, index) => (
              <article className={`about-issue-card issue-${index}`} key={title}>
                <span>
                  <Icon size={22} />
                </span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="about-mosaic-panel about-agency-panel" aria-labelledby="about-agency-title">
          <h2 id="about-agency-title" className="about-panel-title">
            2. From fear to agency
          </h2>
          <div className="about-agency-visual about-agency-content">
            <img
              className="about-agency-image"
              src={ABOUT_ASSETS.transformation}
              alt=""
              aria-hidden="true"
              loading="lazy"
              decoding="async"
              onError={handleImageError}
            />
            <div className="about-agency-image-overlay" aria-hidden="true" />
            <div className="agency-side old">
              <small>OLD PARADIGM</small>
              <h3>Technology-led</h3>
              <span>Automation replaces</span>
              <span>One-size-fits-all tools</span>
              <span>Passive adoption</span>
              <span>Unclear outcomes</span>
            </div>
            <div className="agency-path">
              <small>TRANSFORMATION PATH</small>
              {["Understand", "Reflect", "Align", "Act", "Evolve"].map((step) => (
                <span key={step}>{step}</span>
              ))}
            </div>
            <div className="agency-side new">
              <small>NEW PARADIGM</small>
              <h3>Human-led collaboration</h3>
              <span>Augmentation empowers</span>
              <span>Personalized guidance</span>
              <span>Active co-creation</span>
              <span>Meaningful impact</span>
            </div>
          </div>
        </section>

        <section className="about-mosaic-panel about-platform-panel" aria-labelledby="about-platform-title">
          <h2 id="about-platform-title" className="about-panel-title">
            3. What the platform combines
          </h2>
          <div className="about-platform-grid platform-card-grid">
            {platformCards.map(({ icon: Icon, title, text, to, accent }) => (
              <Link className={`about-platform-card accent-${accent}`} to={to} key={title}>
                <span className="about-card-icon">
                  <Icon size={25} />
                </span>
                <h3>{title}</h3>
                <p>{text}</p>
                <strong>
                  Explore <ArrowRight size={14} />
                </strong>
              </Link>
            ))}
          </div>
        </section>

        <section className="about-mosaic-panel about-research-panel" aria-labelledby="about-research-title">
          <h2 id="about-research-title" className="about-panel-title">
            4. Research-informed, not technology-led
          </h2>
          <div className="research-map research-node-grid">
            <span className="research-flow" aria-hidden="true" />
            {researchDomains.map(({ icon: Icon, title, text, focus }, index) => (
              <article key={title}>
                <small>{index + 1}</small>
                <span className="research-node">
                  <Icon size={24} />
                </span>
                {index < researchDomains.length - 1 ? <i className="connector" /> : null}
                <h3>{title}</h3>
                <p>{text}</p>
                <strong>Focus: {focus}</strong>
              </article>
            ))}
          </div>
        </section>

        <section className="about-mosaic-panel about-audience-panel" aria-labelledby="about-audience-title">
          <h2 id="about-audience-title" className="about-panel-title">
            5. Who it is for
          </h2>
          <div className="about-personas audience-grid">
            {personas.map(({ icon: Icon, title, text, to, outcome }) => (
              <Link className="about-persona-card audience-card" to={to} key={title}>
                <span className="persona-avatar">
                  <Icon size={25} />
                </span>
                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                  <b>{outcome}</b>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section className="about-mosaic-panel about-final-cta" aria-labelledby="about-final-title">
          <img
            className="about-final-cta-image"
            src={ABOUT_ASSETS.finalCta}
            alt=""
            aria-hidden="true"
            loading="lazy"
            decoding="async"
            onError={handleImageError}
          />
          <div className="about-final-cta-overlay" aria-hidden="true" />
          <div className="about-final-inner about-final-cta-content">
            <span id="about-final-title" className="about-final-cta-eyebrow">
              Designed for a meaningful human-AI future
            </span>
            <h2 className="about-final-cta-title">
              <span>Your future with AI should be designed,</span>
              <span>not merely predicted.</span>
            </h2>
            <div className="about-actions about-final-cta-actions">
              <Link className="public-button" to="/diagnostic">
                Start Diagnostic <ArrowRight size={17} />
              </Link>
              <Link className="public-button secondary" to="/principles">
                <Compass size={16} /> Explore the Principles
              </Link>
            </div>
          </div>
        </section>
      </div>
    </PublicPageShell>
  );
}
