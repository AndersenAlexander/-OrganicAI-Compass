import {
  Ban,
  BrainCircuit,
  BriefcaseMedical,
  Compass,
  EyeOff,
  FileWarning,
  Heart,
  MicOff,
  RouteOff,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Sprout,
  Target,
  UserRoundCheck,
  UsersRound,
  type LucideIcon,
} from "lucide-react";
import { lazy, Suspense, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { PublicPageShell } from "../components/public/PublicPageShell";
import "../styles/principles.css";

const PrinciplesCompassScene = lazy(() =>
  import("../components/three/PrinciplesCompassScene").then((module) => ({ default: module.PrinciplesCompassScene }))
);

type PrincipleAccent = "teal" | "cyan" | "violet" | "green" | "bluegreen" | "gold";

type Principle = {
  icon: LucideIcon;
  title: string;
  shortTitle: string;
  summary: string;
  meaning: string;
  application: string;
  protection: string;
  example: string;
  accent: PrincipleAccent;
};

type MatrixRow = {
  principle: string;
  feature: string;
  mechanism: string;
  indicator: string;
};

type Boundary = {
  icon: LucideIcon;
  title: string;
  description: string;
};

const principles: Principle[] = [
  {
    icon: Heart,
    title: "Human-Centred",
    shortTitle: "Human-Centred",
    summary: "Technology begins with human values, needs, agency, and well-being.",
    meaning: "The system adapts to the person instead of forcing the person to adapt to the system.",
    application:
      "Diagnostic starts with interests and values; recommendations use personal context; profiles can be confirmed or rejected.",
    protection: "No clinical, psychological, or deterministic claims.",
    example: "Editable profile interpretation.",
    accent: "teal",
  },
  {
    icon: ShieldCheck,
    title: "Trust & Transparency",
    shortTitle: "Trust",
    summary: "Users should understand where information comes from and where uncertainty remains.",
    meaning: "Guidance should identify its sources and limitations.",
    application: "RAG source chips, confidence notes, ethical notes, and visible limitations.",
    protection: "Exploratory guidance, never unquestionable truth.",
    example: "Source-grounded coach answer.",
    accent: "cyan",
  },
  {
    icon: UserRoundCheck,
    title: "Empowerment, Not Replacement",
    shortTitle: "Empowerment",
    summary: "AI should increase human capability rather than reduce human agency.",
    meaning: "The user keeps meaningful choices and final decisions.",
    application: "Options instead of commands, reflection prompts, and skill-building roadmaps.",
    protection: "No pressure to delegate meaningful decisions entirely to AI.",
    example: "Recommendation alternatives.",
    accent: "violet",
  },
  {
    icon: Sprout,
    title: "Lifelong Growth",
    shortTitle: "Growth",
    summary: "Learning is an adaptive process, not a one-time assessment.",
    meaning: "Progress changes with circumstances and reflection.",
    application: "Seven-day actions, longer directions, recalibration, and learning paths.",
    protection: "No permanent score or fixed personality.",
    example: "Adaptive roadmap check-in.",
    accent: "green",
  },
  {
    icon: UsersRound,
    title: "Collaboration",
    shortTitle: "Collaboration",
    summary: "The strongest outcomes emerge from human judgment and machine capability working together.",
    meaning: "AI should make its machine nature visible and invite feedback.",
    application: "Co-creation prompts, voice interaction, conversational coaching, and iterative refinement.",
    protection: "No imitation of human authority.",
    example: "Text and voice Coach.",
    accent: "bluegreen",
  },
  {
    icon: Target,
    title: "Purpose Alignment",
    shortTitle: "Purpose",
    summary: "Technology should connect actions with values and meaningful contribution.",
    meaning: "Success belongs to the user, not to a system metric.",
    application: "Values analysis, contribution domains, ethical cautions, and impact-oriented roadmap.",
    protection: "No single definition of productivity or purpose.",
    example: "Contribution-aware recommendations.",
    accent: "gold",
  },
];

const matrix: MatrixRow[] = [
  {
    principle: "Human-Centred",
    feature: "Diagnostic and editable profile",
    mechanism: "Personalization context",
    indicator: "User-confirmation rate",
  },
  {
    principle: "Transparency",
    feature: "Source chips and confidence notes",
    mechanism: "RAG retrieval metadata",
    indicator: "Source-grounding score",
  },
  {
    principle: "Empowerment",
    feature: "Multiple options and actions",
    mechanism: "Recommendation generation",
    indicator: "Perceived agency rating",
  },
  {
    principle: "Lifelong Growth",
    feature: "Adaptive roadmap",
    mechanism: "Stored progress and recalibration",
    indicator: "Task progression",
  },
  {
    principle: "Collaboration",
    feature: "Voice and text coach",
    mechanism: "Conversational interaction",
    indicator: "Usability and engagement",
  },
  {
    principle: "Purpose Alignment",
    feature: "Values and contribution mapping",
    mechanism: "Profile-roadmap alignment",
    indicator: "Recommendation relevance",
  },
];

const boundaries: Boundary[] = [
  {
    icon: Ban,
    title: "Diagnose mental-health or personality conditions",
    description: "OrganicAI presents reflective guidance only; it does not act as a clinical or psychometric system.",
  },
  {
    icon: ShieldAlert,
    title: "Hide the fact that content is AI-generated",
    description: "The interface keeps AI involvement visible through coach labels, sources, and confidence notes.",
  },
  {
    icon: EyeOff,
    title: "Manipulate the user through fear or urgency",
    description: "Recommendations should support reflection and choice, not pressure or exploit emotional uncertainty.",
  },
  {
    icon: BriefcaseMedical,
    title: "Replace qualified professional advice",
    description: "The prototype cannot substitute medical, legal, financial, therapeutic, or safety-critical expertise.",
  },
  {
    icon: BrainCircuit,
    title: "Predict a person's future with certainty",
    description: "Profiles and roadmaps are exploratory interpretations, not fixed predictions or destiny claims.",
  },
  {
    icon: RouteOff,
    title: "Present recommendations as the only valid choice",
    description: "The user remains able to compare, reject, adapt, and reinterpret suggested actions.",
  },
  {
    icon: MicOff,
    title: "Reuse voice or personal data without explicit permission",
    description: "Voice and personal context must remain visible, consent-based, and user-controlled.",
  },
  {
    icon: FileWarning,
    title: "Claim research validation that has not been completed",
    description: "Academic indicators are evaluation directions for the prototype, not completed validation claims.",
  },
];

export function PrinciplesPage() {
  document.title = "OrganicAI Compass - Principles";

  return (
    <PublicPageShell>
      <div className="principles-page">
        <div className="principles-atmosphere" aria-hidden="true">
          <span className="principles-particles" />
          <span className="principles-curve curve-a" />
          <span className="principles-curve curve-b" />
          <span className="principles-geometry" />
          <span className="principles-botanical botanical-a" />
          <span className="principles-botanical botanical-b" />
        </div>

        <div className="principles-page-container principles-page-main">
          <section className="principles-hero" aria-labelledby="principles-hero-title">
            <div className="principles-hero-copy">
              <p className="principles-eyebrow">THE ORGANICAI CONSTITUTION</p>
              <h1 id="principles-hero-title" className="principles-hero-title">
                <span>Six principles for</span>
                <span>meaningful</span>
                <span className="principles-hero-title-accent">human-AI collaboration</span>
              </h1>
              <p className="principles-hero-description">
                OrganicAI Compass is designed to support human agency, understanding, creativity, learning, and
                purpose-not dependency, manipulation, or replacement.
              </p>
              <div className="principles-hero-actions">
                <a className="public-button" href="#principles-grid">
                  Read the Principles
                </a>
                <Link className="public-button secondary" to="/ai-constitution">
                  View AI Constitution
                </Link>
              </div>
            </div>

            <div className="principles-hero-visual" aria-label="OrganicAI constitutional compass visualization">
              <Suspense fallback={<PrinciplesCompassFallback />}>
                <PrinciplesCompassScene />
              </Suspense>
            </div>
          </section>

          <section id="principles-grid" className="principles-section principles-principles-section scroll-mt-28">
            <PrinciplesSectionHeader
              eyebrow="THE SIX PRINCIPLES"
              title={
                <>
                  Principles that shape
                  <br />
                  system behaviour
                </>
              }
              description="Each principle defines how OrganicAI should interpret information, generate recommendations, protect user agency, and evaluate system quality."
            />
            <div className="principles-grid">
              {principles.map((principle, index) => (
                <PrincipleCard key={principle.title} principle={principle} index={index} />
              ))}
            </div>
          </section>

          <section className="principles-section implementation-matrix-section" aria-labelledby="implementation-matrix-title">
            <PrinciplesSectionHeader
              eyebrow="RESEARCH IMPLEMENTATION"
              title="Implementation matrix"
              description="Academic indicators describe evaluation directions for this research prototype, not completed validation claims."
            />

            <div className="implementation-matrix-table" role="region" aria-label="Principles implementation matrix">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Principle</th>
                    <th scope="col">Visible UI Feature</th>
                    <th scope="col">System Mechanism</th>
                    <th scope="col">Evaluation Indicator</th>
                  </tr>
                </thead>
                <tbody>
                  {matrix.map((row) => (
                    <tr key={row.principle}>
                      <th scope="row">{row.principle}</th>
                      <td>{row.feature}</td>
                      <td>{row.mechanism}</td>
                      <td>{row.indicator}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="implementation-matrix-cards" aria-label="Principles implementation matrix cards">
              {matrix.map((row) => (
                <article className="implementation-matrix-mobile-card" key={row.principle}>
                  <h3>{row.principle}</h3>
                  <dl>
                    <div>
                      <dt>Visible UI Feature</dt>
                      <dd>{row.feature}</dd>
                    </div>
                    <div>
                      <dt>System Mechanism</dt>
                      <dd>{row.mechanism}</dd>
                    </div>
                    <div>
                      <dt>Evaluation Indicator</dt>
                      <dd>{row.indicator}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          </section>

          <section className="principles-section responsible-boundaries-section" aria-labelledby="boundaries-title">
            <div className="boundaries-heading">
              <p className="principles-eyebrow">RESPONSIBLE BOUNDARIES</p>
              <h2 id="boundaries-title">Responsible boundaries</h2>
              <h3>What OrganicAI Compass will not do</h3>
              <p>
                Ethical clarity requires limits. These boundaries make clear where the research prototype must stay
                transparent, provisional, and human-led.
              </p>
            </div>

            <div className="boundary-grid">
              {boundaries.map(({ icon: Icon, title, description }) => (
                <article className="boundary-item" key={title}>
                  <span className="boundary-icon" aria-hidden="true">
                    <Icon size={20} />
                  </span>
                  <div>
                    <h4>{title}</h4>
                    <p>{description}</p>
                  </div>
                </article>
              ))}
            </div>

            <Link className="principles-constitution-link" to="/ai-constitution">
              Open the AI Constitution
            </Link>
          </section>

          <section className="principles-final-cta" aria-labelledby="principles-final-title">
            <div className="principles-final-copy">
              <p className="principles-eyebrow">FROM PRINCIPLE TO SYSTEM BEHAVIOUR</p>
              <h2 id="principles-final-title">
                Principles become meaningful
                <br />
                when they shape system behaviour.
              </h2>
              <p>
                Explore the complete OrganicAI Constitution, including responsibility boundaries, data principles,
                interaction rules, and evaluation commitments.
              </p>
              <div className="principles-final-actions">
                <Link className="public-button" to="/ai-constitution">
                  Open AI Constitution
                </Link>
                <Link className="public-button secondary" to="/diagnostic">
                  Start Diagnostic
                </Link>
              </div>
            </div>

            <div className="principles-final-visual" aria-hidden="true">
              <span className="cta-orb">
                <Compass size={42} />
              </span>
              <span className="cta-shield">
                <ShieldCheck size={22} />
              </span>
              {principles.map((principle, index) => (
                <i key={principle.shortTitle} className={`cta-dot dot-${index}`} />
              ))}
              <span className="cta-botanical" />
            </div>
          </section>
        </div>
      </div>
    </PublicPageShell>
  );
}

function PrinciplesSectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: ReactNode;
  description?: string;
}) {
  return (
    <header className="principles-section-heading">
      <p>{eyebrow}</p>
      <h2>{title}</h2>
      {description ? <span>{description}</span> : null}
    </header>
  );
}

function PrincipleCard({ principle, index }: { principle: Principle; index: number }) {
  const Icon = principle.icon;

  return (
    <article className={`principle-card principle-card-${principle.accent}`}>
      <span className={`principle-card-motif motif-${principle.accent}`} aria-hidden="true" />
      <div className="principle-card-header">
        <span className="principle-card-number">{String(index + 1).padStart(2, "0")}</span>
        <span className="principle-card-icon" aria-hidden="true">
          <Icon size={22} />
        </span>
        <div>
          <h3>{principle.title}</h3>
          <p>{principle.summary}</p>
        </div>
      </div>

      <div className="principle-card-blocks">
        <PrincipleContentBlock label="WHAT IT MEANS" body={principle.meaning} />
        <PrincipleContentBlock label="HOW ORGANICAI APPLIES IT" body={principle.application} />
        <PrincipleContentBlock label="USER PROTECTION" body={principle.protection} />
      </div>

      <p className="principle-example">
        <Sparkles size={13} aria-hidden="true" />
        <span>Implementation example: {principle.example}</span>
      </p>
    </article>
  );
}

function PrincipleContentBlock({ label, body }: { label: string; body: string }) {
  return (
    <div className="principle-content-block">
      <h4>{label}</h4>
      <p>{body}</p>
    </div>
  );
}

function PrinciplesCompassFallback() {
  return (
    <div className="principles-compass-fallback" role="img" aria-label="Six OrganicAI principles orbiting a HUMAN plus AI sphere">
      <div className="principles-fallback-core">
        <b>HUMAN</b>
        <span>+</span>
        <b>AI</b>
      </div>
      {principles.map((principle, index) => {
        const Icon = principle.icon;
        return (
          <span key={principle.shortTitle} className={`principles-fallback-node node-${index}`}>
            <Icon size={16} aria-hidden="true" />
            <b>{principle.shortTitle}</b>
          </span>
        );
      })}
    </div>
  );
}
