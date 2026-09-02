import { ArrowRight, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAssessmentResults } from "../api/assessmentApi";
import type { AssessmentResults } from "../types/assessment";
import { useAppActions } from "../hooks/useAppActions";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";

export function AssessmentResultsPage() {
  const { profileId } = useParams();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const id = profileId || activeProfileId;
  const [results, setResults] = useState<AssessmentResults | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    setActiveProfileId(id);
    getAssessmentResults(id).then(setResults).catch(() => setError("Assessment results could not be loaded."));
  }, [id, setActiveProfileId]);

  if (!id) return <ProfileRequiredState title="Create your profile before viewing assessment results." />;
  if (error) return <div className="organic-section text-red-700">{error}</div>;
  if (!results) return <div className="organic-section theme-muted">Loading assessment results...</div>;
  if (results.status !== "completed") {
    return (
      <div className="organic-section">
        <p className="organic-badge">Assessment Results</p>
        <h1 className="mt-4 font-display text-4xl font-semibold theme-text">No completed assessment yet.</h1>
        <Link className="organic-button mt-6" to={`/workspace/${id}/assessment`}>
          Start Assessment <ArrowRight size={16} />
        </Link>
      </div>
    );
  }

  const personality = Object.values(results.grouped_scores.personality || {});
  const interests = Object.values(results.grouped_scores.career_interest || {}).sort((a, b) => b.normalized_score - a.normalized_score).slice(0, 3);
  const topValues = results.summary.top_work_values || [];

  return (
    <div className="organic-page">
      <section className="organic-section">
        <p className="organic-badge">Assessment Results</p>
        <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Your self-reflection profile is ready.</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">{results.disclaimer}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link className="organic-button" to={`/workspace/${id}/career-compatibility`}>
            Open Career Compatibility Map <ArrowRight size={16} />
          </Link>
          <Link className="organic-button-secondary" to={`/workspace/${id}/assessment`}>
            <RefreshCw size={16} /> Review or retake
          </Link>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <article className="glass-card p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Personality & Work Style</h2>
          <div className="mt-4 space-y-3">
            {personality.map((score) => (
              <p key={score.id} className="text-sm theme-muted">
                <b className="theme-text">{score.dimension.replace(/_/g, " ")}</b>: {score.label}
              </p>
            ))}
          </div>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Career Interests</h2>
          <p className="mt-3 text-sm theme-muted">{results.summary.combined_interest_profile}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {interests.map((score) => (
              <span key={score.id} className="organic-chip">{score.dimension.replace(/_/g, " ")} - {score.label}</span>
            ))}
          </div>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Values & Readiness</h2>
          <p className="mt-3 text-sm theme-muted">AI readiness: {results.summary.ai_readiness_level}</p>
          <p className="mt-2 text-sm theme-muted">Change readiness: {results.summary.change_readiness}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {topValues.map((value) => (
              <span key={value.value} className="organic-chip">{value.label}</span>
            ))}
          </div>
        </article>
      </section>

      <section className="grid gap-4 lg:grid-cols-4">
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Natural Fit</h2>
          <p className="mt-3 text-sm theme-muted">Uses interests, preferred activities, values, and work-style tendencies. It does not use years of experience or evidence.</p>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Capability Fit</h2>
          <p className="mt-3 text-sm theme-muted">Uses current skills, AI readiness, and professional exposure. Self-report is not treated as demonstrated evidence.</p>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Evidence Strength</h2>
          <p className="mt-3 text-sm theme-muted">Uses evidence status and Evidence Passport records. Course exposure alone is not practical verification.</p>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Transition Feasibility</h2>
          <p className="mt-3 text-sm theme-muted">Uses time, budget, readiness, and constraints. It can change without changing Natural Fit.</p>
        </article>
      </section>
    </div>
  );
}
