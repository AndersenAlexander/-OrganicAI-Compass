import { ArrowRight, BookOpen, BrainCircuit, CheckCircle2, CircleDot, Database, Eye, FileSearch, GitBranch, Layers3, LockKeyhole, MessageSquareText, Network, Orbit, Route, Scale, ShieldCheck, Sparkles, Target, UserRoundCheck, Waves } from "lucide-react";
import { lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import { OrganicPageBackdrop } from "../components/public/OrganicPageBackdrop";
import { PublicPageShell } from "../components/public/PublicPageShell";
import "../styles/research.css";

const ResearchSystemScene = lazy(() => import("../components/three/ResearchSystemScene").then((module) => ({ default: module.ResearchSystemScene })));

function ResearchSceneLoadingFallback() {
  return <div className="research-scene-fallback" role="img" aria-label="Human context connected to AI guidance and evaluation"><div className="research-fallback-ring ring-one" /><div className="research-fallback-ring ring-two" /><div className="research-fallback-core"><b>HUMAN</b><span>context + agency</span></div></div>;
}

const questions = [
  ["RQ1", "Human-centred guidance", "How can a human-centred AI platform help users understand their strengths, values, concerns, and goals while preserving their decision authority?", "Diagnostic · Human Potential Map", "Perceived agency · profile confirmation"],
  ["RQ2", "Grounded AI", "To what extent can retrieval-augmented generation improve the transparency, relevance, and source grounding of AI coaching responses?", "Knowledge Base · AI Coach", "Retrieval relevance · grounding · source visibility"],
  ["RQ3", "Personalized action", "How relevant and actionable are recommendations and adaptive roadmap steps generated from the user's diagnostic and profile context?", "Recommendations · Roadmap", "Relevance · actionability · acceptance"],
  ["RQ4", "Interaction and trust", "How do interface transparency, voice interaction, and visible system feedback affect usability, perceived trust, and user agency?", "Voice · source chips · UI feedback", "Usability · trust · interaction clarity"],
];
const methods = [
  ["01", "Problem identification", "Define the guidance, transparency, and agency problem.", "Research problem", "Completed"],
  ["02", "Requirements and principles", "Translate human-centred values into system requirements.", "Requirements + principles", "Completed"],
  ["03", "Interaction design", "Prototype inspectable, editable, responsive journeys.", "Interface system", "Implemented and iterated"],
  ["04", "Prototype implementation", "Integrate frontend, backend, knowledge, voice, and data.", "Working artifact", "Implemented"],
  ["05", "Functional evaluation", "Verify routes, workflows, responsive behavior, and integration.", "Engineering evidence", "In progress"],
  ["06", "Empirical evaluation", "Study usability, trust, relevance, and perceived agency.", "Participant evidence", "Planned"],
];
const architecture = [
  ["01 · EXPERIENCE", "Public research website", "Diagnostic", "Human Potential Map", "AI Coach", "Roadmap", "Recommendations", "Knowledge Base"],
  ["02 · FRONTEND", "React", "TypeScript", "Vite", "React Router", "React Three Fiber", "Responsive light/dark UI"],
  ["03 · APPLICATION SERVICES", "Profile context", "Diagnostic processing", "Recommendation generation", "Roadmap state", "Conversation state", "Demo environment"],
  ["04 · AI + KNOWLEDGE", "RAG", "Embeddings", "Semantic retrieval", "Grounded generation", "Source metadata", "Voice transcription + TTS"],
  ["05 · BACKEND + DATA", "FastAPI", "SQLite", "JWT authentication", "Persistent profiles", "Knowledge index", "Environment-based secrets"],
];
const architectureDescriptions: Record<string, string> = {
  "01 · EXPERIENCE": "User-facing journeys for reflection, grounded guidance, and action.",
  "02 · FRONTEND": "A responsive, typed interface coordinates navigation and visual feedback.",
  "03 · APPLICATION SERVICES": "Shared context connects profiles, conversations, plans, and demo state.",
  "04 · AI + KNOWLEDGE": "Retrieval and voice services construct evidence-aware AI interactions.",
  "05 · BACKEND + DATA": "Server-side APIs persist state and protect credentials and access boundaries.",
};
const ragSteps = ["Curated documents", "Chunking", "Embeddings", "Semantic retrieval", "Context construction", "AI generation", "Source-visible response", "Evaluation"];
const ragIndicators = [
  ["Retrieval relevance", "Are the recovered chunks relevant to the query?", "Human relevance rating or top-k relevance"],
  ["Source grounding", "Does the response remain supported by retrieved context?", "Groundedness or citation-support assessment"],
  ["Answer usefulness", "Does the response help the user understand or act?", "User usefulness rating"],
  ["Transparency", "Can the user identify sources and uncertainty?", "Source visibility and confidence comprehension"],
  ["Latency", "Does the system respond within an acceptable interaction time?", "End-to-end response time"],
];
const evaluation = [
  ["Functional correctness", "Routes and workflows · authentication · persistence · demo reset · API integration · responsive behavior", "implemented"],
  ["RAG quality", "Retrieval relevance · context coverage · source grounding · faithfulness · source visibility", "ready"],
  ["Recommendation quality", "Relevance · actionability · personalization · clarity · diversity of options", "planned"],
  ["User experience", "Task completion · usability · clarity · engagement · interaction efficiency", "planned"],
  ["Responsible AI", "Agency · transparency · uncertainty · privacy awareness · reject/edit controls", "unmeasured"],
];
const traceRows = [
  ["RQ1", "Diagnostic + Human Potential Map", "Profile interaction and user feedback", "Perceived agency / profile confirmation", "Ready for evaluation"],
  ["RQ2", "Knowledge Base + RAG Coach", "Retrieved chunks and generated responses", "Relevance / grounding / source visibility", "Ready for evaluation"],
  ["RQ3", "Recommendations + Roadmap", "Generated recommendations and task actions", "Relevance / actionability / acceptance", "Planned"],
  ["RQ4", "Voice + interaction feedback", "Task sessions and user feedback", "Usability / trust / interaction clarity", "Planned"],
];
const evidence = [
  ["IMPLEMENTED", "implemented", ["React + TypeScript interface", "FastAPI + SQLite backend", "JWT authentication", "Public and workspace layouts", "Human diagnostic + Potential Map", "AI Coach + recommendations", "Adaptive Roadmap", "Curated Knowledge Base", "RAG indexing and search", "Voice integration architecture", "Light/dark responsive UI", "Automated navigation tests"]],
  ["READY FOR EVALUATION", "ready", ["Retrieval relevance", "Grounded answer quality", "Recommendation relevance", "Task completion", "Source comprehension", "Perceived user control", "Voice interaction usability"]],
  ["PLANNED", "planned", ["Structured participant study", "Formal usability questionnaire", "Trust and agency evaluation", "Comparative RAG analysis", "Longitudinal progression study", "Production security hardening", "Deployment monitoring"]],
] as const;

function Heading({ eyebrow, title, copy }: { eyebrow: string; title: string; copy?: string }) {
  return <header className="research-heading"><p>{eyebrow}</p><h2>{title}</h2>{copy && <span>{copy}</span>}</header>;
}
function Status({ children, kind = "planned" }: { children: React.ReactNode; kind?: string }) { return <span className={`research-status ${kind}`}>{children}</span>; }

export function ResearchPage() {
  document.title = "OrganicAI Compass - Research";
  return (
    <PublicPageShell>
      <div className="research-page">
        <OrganicPageBackdrop />
        <div className="research-page-container">
          <section className="research-hero" aria-labelledby="research-title">
            <div className="research-hero-copy">
              <p className="research-eyebrow">MASTER'S DISSERTATION RESEARCH</p>
              <h1 id="research-title">Researching human-centred AI guidance through an implemented prototype</h1>
              <p className="research-lead">OrganicAI Compass investigates how personal reflection, grounded AI, voice interaction, and adaptive recommendations can support meaningful human action while preserving user agency, transparency, and control.</p>
              <div className="research-badges"><Status kind="implemented">IMPLEMENTED PROTOTYPE</Status><Status kind="ready">RAG + VOICE + PERSONALIZATION</Status><Status>EVALUATION FRAMEWORK IN PROGRESS</Status></div>
              <div className="research-actions"><a className="research-button" href="#research-methodology">Explore the Methodology <ArrowRight size={16} /></a><Link className="research-button secondary" to="/knowledge-base">Open Knowledge Base</Link><Link className="research-text-link" to="/principles">View the Principles</Link></div>
            </div>
            <div className="research-hero-visual"><Suspense fallback={<ResearchSceneLoadingFallback />}><ResearchSystemScene /></Suspense><div className="research-evaluation-loop">GROUNDING · USABILITY · TRUST · AGENCY</div></div>
          </section>

          <section className="research-status-strip" aria-label="Current prototype facts">
            {["Implemented web prototype", "Human-centred AI workflow", "Curated RAG knowledge base", "Functional evaluation environment"].map((item) => <span key={item}><CheckCircle2 size={16} />{item}</span>)}
            <small>Current local prototype index · 8 documents · 24 chunks</small>
          </section>

          <section className="research-status-strip" aria-label="Research readiness boundary">
            <span><LockKeyhole size={16} />Research configuration incomplete</span>
            <small>Live recruitment and empirical data collection are disabled until researcher identity, contact, storage duration, study version, and consent document version are completed. Synthetic evaluation may remain available.</small>
          </section>

          <section className="research-section"><Heading eyebrow="RESEARCH CONTEXT" title="Why human-centred AI guidance requires more than a chatbot" copy="Rapid AI adoption can create uncertainty about future skills while generic advice, limited source transparency, and fragmented tools make sustained action difficult. A guidance system must support reflection without reducing user autonomy." />
            <div className="research-three-grid">{[
              [GitBranch, "01", "Fragmented Guidance", "Users receive disconnected answers, resources, assessments, and plans.", "Research implication: connect reflection, evidence, recommendations, and action."],
              [Eye, "02", "Limited Transparency", "Generative systems may recommend actions without showing their knowledge context.", "Research implication: expose sources, confidence, and boundaries."],
              [UserRoundCheck, "03", "Human Agency", "Personalization can become prescriptive when users cannot modify or reject outputs.", "Research implication: keep the user in control of calibration."],
            ].map(([Icon, no, title, text, implication]) => <article className="research-card" key={title as string}><span className="research-icon"><Icon size={23} /></span><small>{no as string}</small><h3>{title as string}</h3><p>{text as string}</p><b>{implication as string}</b></article>)}</div>
          </section>

          <section className="research-objective"><Heading eyebrow="RESEARCH OBJECTIVE" title="Design, implement, and evaluate a human-centred AI information system" /><p>To investigate how a web-based AI system combining personal reflection, retrieval-augmented generation, voice interaction, and adaptive recommendations can provide useful guidance while maintaining transparency, user agency, and responsible interaction boundaries.</p><ul>{["Implemented multi-component software prototype", "Human-centred interaction framework", "Grounded AI coaching through RAG", "Personalized recommendations and adaptive roadmap", "Evaluation framework connecting principles to measurable indicators"].map((x) => <li key={x}><CircleDot size={15} />{x}</li>)}</ul></section>

          <section className="research-section"><Heading eyebrow="RESEARCH QUESTIONS" title="Questions guiding the development and evaluation" copy="These questions guide planned evaluation; they are not presented as answered." /><div className="research-question-grid">{questions.map(([rq, title, question, modules, dimensions]) => <article className="research-question" key={rq}><span>{rq}</span><h3>{title}</h3><p>{question}</p><dl><div><dt>Implemented modules</dt><dd>{modules}</dd></div><div><dt>Proposed dimensions</dt><dd>{dimensions}</dd></div></dl></article>)}</div></section>

          <section id="research-methodology" className="research-section"><Heading eyebrow="METHODOLOGY" title="From research problem to evaluated artifact" copy="A Design Science Research-oriented iterative development process for a software engineering dissertation." /><div className="research-method-flow">{methods.map(([no, title, objective, artifact, status]) => <article key={no}><span>{no}</span><h3>{title}</h3><p>{objective}</p><small>Principal artifact</small><b>{artifact}</b><Status kind={status.includes("Completed") || status === "Implemented" ? "implemented" : status === "Planned" ? "planned" : "ready"}>{status}</Status></article>)}</div></section>

          <section className="research-section research-architecture" aria-labelledby="architecture-title"><Heading eyebrow="IMPLEMENTED ARTIFACT" title="A multi-layer architecture for personalized and grounded guidance" /><div className="research-architecture-diagram" role="img" aria-label="Five layer system architecture with OpenAI and ElevenLabs external services">{architecture.map(([title, ...items]) => <article key={title}><h3>{title}</h3><p>{architectureDescriptions[title]}</p><div>{items.map((x) => <span key={x}>{x}</span>)}</div></article>)}<aside><b>EXTERNAL SERVICES</b><small>Hosted capabilities connected through server-side credentials.</small><span>OpenAI</span><span>ElevenLabs</span></aside></div><p className="research-architecture-flow">USER INTERACTION → FRONTEND → APPLICATION CONTEXT → RAG / AI SERVICES → BACKEND PERSISTENCE → RESPONSE WITH EVIDENCE</p>
            <div className="research-four-grid">{[[UserRoundCheck,"Personal Context","Diagnostic results, profile data, values, goals, and progress provide the basis for personalization."],[Database,"Grounded Knowledge","Curated documents are segmented and retrieved according to semantic similarity."],[BrainCircuit,"AI Interaction","The model combines user context and retrieved knowledge to generate coaching responses."],[Eye,"Visible Evidence","Source chips, confidence notes, ethical notes, and editable recommendations expose system context."]].map(([Icon,title,text])=><article className="research-mini-card" key={title as string}><Icon size={22}/><h3>{title as string}</h3><p>{text as string}</p></article>)}</div>
          </section>

          <section className="research-section research-rag"><Heading eyebrow="RAG RESEARCH PIPELINE" title="From curated knowledge to source-visible guidance" /><div className="research-rag-flow">{ragSteps.map((step, index)=><div key={step}><span>{String(index+1).padStart(2,"0")}</span><b>{step}</b></div>)}</div><div className="research-domain-row">{["AI Literacy","Future of Work","Human–AI Collaboration","OrganicAI Methodology","Privacy and Voice Data","Responsible AI","Robotics Awareness","Talent Discovery"].map(x=><span key={x}>{x}</span>)}</div><Link className="research-button" to="/knowledge-base">Open the Knowledge Base <ArrowRight size={16}/></Link>
            <div className="research-indicator-grid">{ragIndicators.map(([title,q,indicator])=><article className="research-card" key={title}><Status>PROPOSED INDICATOR</Status><h3>{title}</h3><p>{q}</p><b>{indicator}</b></article>)}</div>
          </section>

          <section className="research-section research-evaluation"><Heading eyebrow="EVALUATION FRAMEWORK" title="Evaluating the prototype across technical and human dimensions" /><div className="research-evaluation-visual">{evaluation.map(([title,items,status],index)=><article key={title}><span>{index+1}</span><div><h3>{title}</h3><p>{items}</p></div><Status kind={status}>{status === "ready" ? "READY FOR EVALUATION" : status === "unmeasured" ? "NOT YET MEASURED" : status.toUpperCase()}</Status></article>)}</div><div className="research-legend"><Status kind="implemented">IMPLEMENTED</Status><Status kind="ready">READY FOR EVALUATION</Status><Status>PLANNED</Status><Status kind="unmeasured">NOT YET MEASURED</Status></div></section>

          <section className="research-section"><Heading eyebrow="TRACEABILITY" title="From research question to observable evidence" /><div className="research-table-wrap"><table><thead><tr>{["Research Question","System Feature","Evidence Source","Evaluation Indicator","Current Status"].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{traceRows.map(row=><tr key={row[0]}>{row.map((cell,i)=><td key={cell}>{i===4?<Status kind={cell.startsWith("Ready")?"ready":"planned"}>{cell}</Status>:cell}</td>)}</tr>)}</tbody></table></div><div className="research-trace-cards">{traceRows.map(row=><dl key={row[0]}>{["Research Question","System Feature","Evidence Source","Evaluation Indicator","Current Status"].map((label,i)=><div key={label}><dt>{label}</dt><dd>{row[i]}</dd></div>)}</dl>)}</div></section>

          <section className="research-section"><Heading eyebrow="CURRENT PROTOTYPE STATUS" title="What has been implemented, what can be evaluated, and what remains" /><div className="research-evidence-grid">{evidence.map(([title,kind,items])=><article key={title}><Status kind={kind}>{title}</Status><ul>{items.map(x=><li key={x}><CheckCircle2 size={15}/>{x}</li>)}</ul></article>)}</div><aside className="research-validation"><div><p>SOFTWARE VERIFICATION</p><h3>Automated engineering checks are not empirical user validation</h3><span><b className="research-verification-label">Latest local verification.</b> TypeScript build, separated navigation contexts, authentication states, theme behavior, and responsive overflow checks are verified. Participant-based research evaluation remains planned.</span></div><div><b>16/16</b><small>navigation checks</small></div><div><b>3/3</b><small>authentication-state checks</small></div></aside></section>

          <section className="research-section"><Heading eyebrow="RESPONSIBLE RESEARCH" title="Agency, transparency, privacy, and bounded claims" /><div className="research-four-grid">{[[UserRoundCheck,"User Agency","Users can inspect, edit, reject, and recalibrate system recommendations."],[Eye,"Transparency","The system distinguishes sources, generated content, uncertainty, and implemented versus planned evaluation."],[LockKeyhole,"Privacy","Voice and profile data remain under explicit user control; API secrets remain server-side."],[Scale,"Bounded Claims","OrganicAI Compass is an exploratory guidance prototype, not a medical, psychological, or deterministic prediction system."]].map(([Icon,title,text])=><article className="research-card" key={title as string}><span className="research-icon"><Icon size={23}/></span><h3>{title as string}</h3><p>{text as string}</p></article>)}</div><div className="research-actions"><Link className="research-button" to="/principles">Read the Principles</Link><Link className="research-button secondary" to="/ai-constitution">Open AI Constitution</Link></div></section>

          <section className="research-section research-limitations"><Heading eyebrow="RESEARCH LIMITATIONS" title="Current limitations of the research prototype" /><ul>{["Limited curated knowledge corpus","Dependency on external AI services","Exploratory personalization model","No completed large-scale participant study","No longitudinal validation","Evaluation indicators are still being operationalized","Possible model variability","Local prototype database","Production security and monitoring are not yet complete"].map(x=><li key={x}><CircleDot size={15}/>{x}</li>)}</ul></section>

          <section className="research-section"><Heading eyebrow="FUTURE WORK" title="A research roadmap from prototype to evaluated system" /><div className="research-future-flow">{["Expand the knowledge corpus","Introduce structured RAG benchmarks","Conduct usability and trust studies","Evaluate recommendation relevance","Compare grounded and non-grounded answers","Study voice interaction","Improve accessibility","Deploy a controlled research environment","Investigate longitudinal adaptation"].map((x,i)=><article key={x}><span>{String(i+1).padStart(2,"0")}</span><p>{x}</p></article>)}</div><Link className="research-button" to="/project-roadmap">View Project Roadmap <ArrowRight size={16}/></Link></section>

          <section className="research-final-cta"><div><p>IMPLEMENTED RESEARCH ARTIFACT</p><h2>Explore the implemented research artifact</h2><span>Use the OrganicAI Compass prototype, inspect its grounded knowledge workflow, and follow the development from research concept to evaluated system.</span><div className="research-actions"><Link className="research-button" to="/diagnostic">Try the Diagnostic</Link><Link className="research-button secondary" to="/knowledge-base">Open Knowledge Base</Link><Link className="research-text-link" to="/project-roadmap">View Project Roadmap</Link></div></div><div className="research-cta-orbit" aria-hidden="true"><Orbit/><span>HUMAN</span><i/><i/><i/></div></section>
        </div>
      </div>
    </PublicPageShell>
  );
}
