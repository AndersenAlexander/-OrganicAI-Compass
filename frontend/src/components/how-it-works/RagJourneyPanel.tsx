import { ArrowRight, BookOpenCheck, BrainCircuit, CheckCircle2, Database, MessageCircle, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

const sources = [
  ["AI Literacy", "0.92"],
  ["Responsible AI", "0.88"],
  ["Human-AI Collaboration", "0.84"],
  ["Privacy and Voice Data", "0.79"],
];

const ragSteps = [
  "The user asks a question",
  "Relevant knowledge chunks are retrieved",
  "The AI receives retrieved context",
  "The answer displays sources and confidence information",
];

export function RagJourneyPanel() {
  return (
    <section className="how-page-section rag-journey-panel rag-journey-section" aria-labelledby="rag-title">
      <header className="how-section-heading">
        <p>GROUNDED AI COACH</p>
        <h2 id="rag-title">Grounded guidance through RAG</h2>
        <span>Questions, retrieval, and generated answers are shown as one transparent guidance workflow.</span>
      </header>
      <div className="rag-journey-grid">
        <article className="rag-card rag-question">
          <span className="rag-card-icon">
            <MessageCircle size={22} />
          </span>
          <h3>User Question</h3>
          <p className="rag-sample-question">How can I build trust when introducing AI in my team?</p>
          <div className="rag-input-labels">
            <span>Voice</span>
            <span>Text</span>
            <span>Profile Context</span>
          </div>
        </article>
        <article className="rag-card rag-retrieval">
          <span className="rag-card-icon">
            <BrainCircuit size={22} />
          </span>
          <h3>Retrieval Process</h3>
          <div className="rag-embedding-node">
            <Database size={20} />
            Embedding match
          </div>
          <div className="rag-source-stack">
            {sources.map(([source, score]) => (
              <span key={source}>
                {source}
                <b>{score}</b>
              </span>
            ))}
          </div>
        </article>
        <article className="rag-card rag-answer">
          <span className="rag-card-icon">
            <Sparkles size={22} />
          </span>
          <h3>Grounded Answer</h3>
          <p>
            Start with a shared purpose, explain where AI helps and where humans stay accountable, then run a small
            transparent pilot before scaling.
          </p>
          <div className="rag-source-chips">
            <span>AI Literacy</span>
            <span>Responsible AI</span>
            <span>Human-AI Collaboration</span>
          </div>
          <div className="rag-notes">
            <span>
              <CheckCircle2 size={14} />
              Confidence: grounded in retrieved knowledge
            </span>
            <span>
              <BookOpenCheck size={14} />
              Ethical note: keep people informed and able to challenge recommendations
            </span>
          </div>
          <Link className="journey-action-link" to="/knowledge-base">
            Explore Knowledge Base <ArrowRight size={15} />
          </Link>
        </article>
      </div>
      <div className="rag-flow-steps" aria-label="RAG explanation steps">
        {ragSteps.map((step, index) => (
          <span key={step}>
            <b>{index + 1}</b>
            {step}
          </span>
        ))}
      </div>
    </section>
  );
}
