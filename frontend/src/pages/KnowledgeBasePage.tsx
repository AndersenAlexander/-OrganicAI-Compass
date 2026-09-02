import { lazy, Suspense, useState, type FormEvent } from "react";
import { BookOpen, Network, RefreshCw, Search, Send, Sparkles } from "lucide-react";
import {
  askKnowledgeBase,
  reindexKnowledgeBase,
  searchKnowledgeBase,
  type RagAnswerResponse,
  type RagResult,
} from "../api/ragApi";
import { RagFeedback } from "../components/shared/RagFeedback";
import { OrganicAtmosphere } from "../components/visual/OrganicAtmosphere";
import { OrganicGlassPanel } from "../components/ui/OrganicGlassPanel";
import { OrganicIconBadge } from "../components/ui/OrganicIconBadge";
import { OrganicMetricCard } from "../components/ui/OrganicMetricCard";
import { OrganicProgressBar } from "../components/ui/OrganicProgressBar";

const Graph = lazy(() =>
  import("../components/three/RagKnowledgeGraph3D").then((module) => ({ default: module.RagKnowledgeGraph3D }))
);

const documents = [
  "OrganicAI Compass Master Knowledge",
  "OrganicAI Compass Defence Q&A",
  "AI Literacy",
  "Career Assessment and Decision Support",
  "Career Resilience Methodology",
  "Evidence-Based Skills",
  "Evidence-Locked Applications",
  "Future of Work",
  "Human-AI Collaboration",
  "Interview Journey Guidance",
  "Learning Resource Recommendations",
  "Market-Aware Application Journey",
  "NAV Stillingsfeed Market Data",
  "Norway Job Loss Support",
  "OrganicAI Methodology",
  "Privacy and Voice Data",
  "Responsible AI",
  "Robotics Awareness",
  "Talent Discovery",
];

export function KnowledgeBasePage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<RagResult[]>([]);
  const [answer, setAnswer] = useState<RagAnswerResponse | null>(null);
  const [status, setStatus] = useState("RAG index ready");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState("OrganicAI Compass Master Knowledge");

  async function run(action: () => Promise<void>) {
    setLoading(true);
    try {
      await action();
    } catch {
      setStatus("The Knowledge Base action failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function search(event: FormEvent) {
    event.preventDefault();
    if (query.trim().length < 2) return;

    void run(async () => {
      const data = await searchKnowledgeBase(query.trim());
      setResults(data.results);
      setAnswer(null);
      setStatus(`${data.results.length} grounded results found.`);
    });
  }

  async function ask() {
    if (query.trim().length < 2) return;

    await run(async () => {
      const data = await askKnowledgeBase(query.trim());
      setAnswer(data);
      setStatus(data.insufficient_context ? "The current Knowledge Base has insufficient context." : "Grounded response ready.");
    });
  }

  const shown =
    answer?.sources.map((source) => ({
      id: source.id,
      document_name: source.document_name,
      section_title: source.section_title,
      chunk_text: source.excerpt,
      score: source.score,
    })) ?? results;

  return (
    <div className="kb-page">
      <OrganicAtmosphere />
      <header className="kb-hero">
        <div>
          <p>CURATED RAG</p>
          <h1>OrganicAI Knowledge Base</h1>
          <span>
            Search and ask questions grounded in 19 curated documents. Sources, sections, snippets, and retrieval
            relevance scores stay visible; local lexical matching remains available when embeddings are unavailable.
          </span>
        </div>
        <div className="kb-metrics">
          <OrganicMetricCard value={documents.length.toString()} label="Curated documents" />
          <OrganicMetricCard value="196" label="Indexed chunks" />
          <OrganicMetricCard value="41" label="Canonical sections" />
          <OrganicMetricCard value={loading ? "..." : "Ready"} label="RAG index status" />
        </div>
      </header>

      <p role="status" className="kb-status">
        {status}
      </p>

      <main className={`kb-dashboard ${answer ? "kb-dashboard--answered" : ""}`}>
        <OrganicGlassPanel className="kb-library">
          <div className="kb-title">
            <OrganicIconBadge icon={BookOpen} />
            <h2>Document library</h2>
          </div>
          {documents.map((name, index) => (
            <button
              key={name}
              onClick={() => {
                setSelected(name);
                setQuery(name);
              }}
              className={selected === name ? "active" : ""}
            >
              <span>{index + 1}</span>
              <b>{name}</b>
              <small>Ready - curated chunks</small>
            </button>
          ))}
        </OrganicGlassPanel>

        <div className="kb-centre">
          <OrganicGlassPanel className="kb-graph">
            <div>
              <p>KNOWLEDGE CONSTELLATION</p>
              <h2>{selected}</h2>
              <span>Choose a document to focus your search.</span>
            </div>
            <Suspense fallback={<div className="kb-graph-fallback" />}>
              <Graph />
            </Suspense>
          </OrganicGlassPanel>

          <OrganicGlassPanel>
            <form onSubmit={search} className="kb-search">
              <Search />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search responsible AI, privacy, collaboration..."
              />
              <button disabled={loading || query.trim().length < 2}>Search</button>
            </form>

            <div className="kb-results">
              {shown.length ? (
                shown.map((item) => (
                  <article key={item.id}>
                    <div>
                      <b>{item.document_name.replace(/_/g, " ")}</b>
                      <span>{item.section_title}</span>
                    </div>
                    <OrganicProgressBar value={Math.round(item.score * 100)} />
                    <small title="This score reflects semantic similarity between the question and retrieved text. It is not a correctness probability.">
                      Retrieval similarity: {item.score.toFixed(3)}
                    </small>
                    <p>{item.chunk_text}</p>
                    {answer ? <RagFeedback runId={answer.rag_run_id} sourceId={item.id} /> : null}
                  </article>
                ))
              ) : (
                <div className="kb-empty">
                  <Network size={30} />
                  <p>Search the curated knowledge base or choose a constellation node.</p>
                </div>
              )}
            </div>
          </OrganicGlassPanel>
        </div>

        <OrganicGlassPanel className={`kb-ask ${answer ? "kb-ask--answered" : ""}`}>
          <div className="kb-title">
            <OrganicIconBadge icon={Sparkles} />
            <h2>Ask OrganicAI</h2>
          </div>
          <p>Receive grounded context with visible source details.</p>
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="What would you like to understand?"
          />
          <div className="kb-suggestions">
            {["How can I build trust with AI?", "What does responsible AI mean?", "How should I protect voice data?"].map(
              (suggestion) => (
                <button key={suggestion} onClick={() => setQuery(suggestion)}>
                  {suggestion}
                </button>
              )
            )}
          </div>
          <button className="kb-ask-button" disabled={loading || query.trim().length < 2} onClick={() => void ask()}>
            <Send size={17} />
            {loading ? "Thinking..." : "Ask Knowledge Base"}
          </button>

          {answer ? (
            <div className={`kb-answer ${answer.insufficient_context ? "insufficient" : ""}`}>
              <b>{answer.insufficient_context ? "Insufficient Knowledge Base context" : "Grounded guidance"}</b>
              <span className={`rag-quality ${answer.context_quality}`}>Context quality: {answer.context_quality}</span>
              <p>{answer.answer}</p>
              <small>{answer.confidence_note}</small>
              <small>{answer.ethical_note}</small>
              {answer.insufficient_context ? (
                <div className="rag-fallback-actions">
                  <button onClick={() => setQuery("")}>Try another question</button>
                  <a href="#knowledge-library">Browse Knowledge Base</a>
                </div>
              ) : null}
              <RagFeedback runId={answer.rag_run_id} />
            </div>
          ) : null}
        </OrganicGlassPanel>
      </main>

      <OrganicGlassPanel className="kb-pipeline">
        <div>
          <h2>How grounded guidance works</h2>
          <p>Question - Embedding - Retrieval - Safe context - Grounded answer</p>
        </div>
        <button
          disabled={loading}
          onClick={() =>
            void run(async () => {
              const data = await reindexKnowledgeBase();
              setStatus(`Reindex complete: ${data.documents} documents and ${data.chunks} chunks.`);
            })
          }
        >
          <RefreshCw size={18} /> {loading ? "Indexing knowledge..." : "Reindex Knowledge Base"}
        </button>
      </OrganicGlassPanel>
    </div>
  );
}
