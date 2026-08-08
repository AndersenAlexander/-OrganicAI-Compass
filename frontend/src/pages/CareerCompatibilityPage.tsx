import { BarChart3, CheckCircle2, GitCompare, RefreshCw, ShieldAlert, Trash2, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  confirmAssessmentResults,
  createCareerComparison,
  createCareerRoadmapDraft,
  deleteAssessmentData,
  getAssessmentResults,
  getCareerMatches,
  rejectCareerMatch,
  requestCareerAlternative,
  saveCareerMatch,
} from "../api/assessmentApi";
import { getProfile } from "../api/profileApi";
import type { CareerComparison, CareerMatch, AssessmentResults } from "../types/assessment";
import type { HumanPotentialProfile } from "../types/profile";
import { useAppActions } from "../hooks/useAppActions";

const categoryOrder = [
  "augment_current_profession",
  "adjacent_professional_roles",
  "reskilling_opportunities",
  "entrepreneurship_independent_work",
];

const categoryLabels: Record<string, string> = {
  augment_current_profession: "A. Augment Current Profession",
  adjacent_professional_roles: "B. Adjacent Professional Roles",
  reskilling_opportunities: "C. Reskilling Opportunities",
  entrepreneurship_independent_work: "D. Entrepreneurship or Independent Work",
};

function dimensionLabel(value: string) {
  return value.replace(/_/g, " ").replace(/\bai\b/i, "AI").replace(/\bux\b/i, "UX");
}

function statusTone(status: string) {
  if (["saved", "roadmap_draft_created"].includes(status)) return "text-[color:var(--green)]";
  if (status === "rejected") return "text-red-700";
  return "text-[color:var(--color-accent-action-muted)]";
}

function MatchCard({
  match,
  selected,
  onToggleCompare,
  onSave,
  onReject,
  onAlternative,
  onRoadmap,
}: {
  match: CareerMatch;
  selected: boolean;
  onToggleCompare: () => void;
  onSave: () => void;
  onReject: () => void;
  onAlternative: () => void;
  onRoadmap: () => void;
}) {
  return (
    <article className="rounded-2xl border border-[color:var(--border-soft)] bg-[color:var(--color-surface-secondary)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--color-accent-action-muted)]">{match.alignment_label}</p>
          <h3 className="mt-1 font-display text-2xl font-semibold theme-text">{match.title}</h3>
          <p className="mt-1 text-sm theme-muted">{match.role_family} - {match.transition_difficulty} transition - {match.time_horizon}</p>
        </div>
        <label className="organic-chip cursor-pointer">
          <input className="h-4 w-4 accent-[color:var(--color-accent-action)]" type="checkbox" checked={selected} onChange={onToggleCompare} />
          Compare
        </label>
      </div>
      <p className="mt-4 text-sm leading-6 theme-muted">{match.explanation}</p>

      <details className="mt-4 rounded-2xl border border-[color:var(--border-soft)] p-4">
        <summary className="cursor-pointer font-bold theme-text">Why it may fit, and what conflicts</summary>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-bold theme-text">Supporting factors</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">
              {match.supporting_factors.length ? match.supporting_factors.map((item) => <li key={item}>{item}</li>) : <li>More evidence is needed before treating this as a strong signal.</li>}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-bold theme-text">Conflicts or gaps</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">
              {match.conflicting_factors.length ? match.conflicting_factors.map((item) => <li key={item}>{item}</li>) : <li>No major conflict was detected by the prototype scoring rules.</li>}
            </ul>
          </div>
        </div>
      </details>

      <details className="mt-3 rounded-2xl border border-[color:var(--border-soft)] p-4">
        <summary className="cursor-pointer font-bold theme-text">Skills, AI use, and next experiment</summary>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div>
            <h4 className="text-sm font-bold theme-text">Transferable skills</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">
              {match.transferable_skills.length ? match.transferable_skills.slice(0, 4).map((item, index) => <li key={index}>{String(item.original_skill || item.skill || "Transferable skill")}</li>) : <li>Additional evidence would clarify transferability.</li>}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-bold theme-text">Missing skills</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">
              {match.missing_skills.length ? match.missing_skills.map((item) => <li key={item}>{item}</li>) : <li>No major required skill gap was detected.</li>}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-bold theme-text">AI opportunities</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">
              {match.ai_opportunities.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
        </div>
        <p className="mt-4 rounded-2xl border border-[color:var(--color-accent-action-border)] bg-[color:var(--color-accent-action-soft)] p-3 text-sm font-semibold text-[color:var(--color-accent-action-muted)]">
          Recommended decision experiment: {match.next_step}
        </p>
      </details>

      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" className="organic-button-secondary" onClick={onSave}><CheckCircle2 size={16} /> Save</button>
        <button type="button" className="organic-button-secondary" onClick={onAlternative}><RefreshCw size={16} /> Request alternative</button>
        <button type="button" className="organic-button" onClick={onRoadmap}>Add exploratory action to My Roadmap</button>
        <button type="button" className="organic-button-secondary text-red-700" onClick={onReject}><XCircle size={16} /> Not for me</button>
      </div>
      <p className={`mt-3 text-xs font-bold ${statusTone(match.status)}`}>Status: {match.status.replace(/_/g, " ")}</p>
    </article>
  );
}

export function CareerCompatibilityPage() {
  const { profileId } = useParams();
  const navigate = useNavigate();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const id = profileId || activeProfileId || "demo-profile";
  const [profile, setProfile] = useState<HumanPotentialProfile | null>(null);
  const [results, setResults] = useState<AssessmentResults | null>(null);
  const [matches, setMatches] = useState<CareerMatch[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<CareerComparison | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    const [profileData, resultData, matchData] = await Promise.all([getProfile(id), getAssessmentResults(id), getCareerMatches(id)]);
    setProfile(profileData);
    setResults(resultData);
    setMatches(matchData);
  }

  useEffect(() => {
    setActiveProfileId(id);
    refresh().catch(() => setError("Career compatibility data could not be loaded."));
  }, [id, setActiveProfileId]);

  const grouped = useMemo(() => {
    const out: Record<string, CareerMatch[]> = {};
    categoryOrder.forEach((category) => {
      out[category] = matches.filter((match) => match.category === category);
    });
    return out;
  }, [matches]);

  async function updateMatch(action: Promise<CareerMatch> | Promise<unknown>, message: string) {
    await action;
    setStatus(message);
    await refresh();
  }

  async function compare() {
    if (!selected.length) return;
    const created = await createCareerComparison(id, selected);
    setComparison(created);
    setStatus("Decision matrix created. Core assessment scores were not changed.");
  }

  async function deleteData() {
    if (!window.confirm("Delete assessment answers, scores, career matches, comparisons, and interpretations for this profile?")) return;
    await deleteAssessmentData(id);
    navigate(`/workspace/${id}/assessment`);
  }

  if (error) return <div className="organic-section text-red-700">{error}</div>;
  if (!results || !profile) return <div className="organic-section theme-muted">Loading Career Compatibility Map...</div>;
  if (results.status !== "completed") {
    return (
      <div className="organic-section">
        <p className="organic-badge">Career Compatibility Map</p>
        <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Complete the assessment to unlock career compatibility.</h1>
        <p className="mt-3 max-w-2xl theme-muted">{results.disclaimer}</p>
        <Link className="organic-button mt-6" to={`/workspace/${id}/assessment`}>Start Assessment</Link>
      </div>
    );
  }

  const personality = Object.values(results.grouped_scores.personality || {});
  const interests = Object.values(results.grouped_scores.career_interest || {}).sort((a, b) => b.normalized_score - a.normalized_score).slice(0, 3);
  const topValues = results.summary.top_work_values || [];
  const skills = (results.summary.skills || []).filter((skill) => skill.level >= 2).slice(0, 8);

  return (
    <div className="organic-page">
      <section className="organic-section">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="organic-badge">Career Compatibility Map</p>
            <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Explore career directions before committing.</h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">{results.disclaimer}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link className="organic-button-secondary" to={`/workspace/${id}/assessment/results`}>Assessment Results</Link>
            <Link className="organic-button-secondary" to={`/workspace/${id}/career-compare`}>Compare Options</Link>
          </div>
        </div>
        {status ? <p className="mt-4 text-sm font-semibold text-[color:var(--teal)]" role="status">{status}</p> : null}
      </section>

      <section className="grid gap-4 lg:grid-cols-4">
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Profile Summary</h2>
          <p className="mt-2 text-sm theme-muted">{profile.primary_archetype.name}</p>
          <p className="mt-2 text-xs theme-muted">Self-reported and calculated data are shown separately below.</p>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Career Interests</h2>
          <p className="mt-2 text-sm theme-muted">{results.summary.combined_interest_profile}</p>
          <div className="mt-3 flex flex-wrap gap-2">{interests.map((score) => <span key={score.id} className="organic-chip">{dimensionLabel(score.dimension)}</span>)}</div>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">AI Readiness</h2>
          <p className="mt-2 text-sm theme-muted">{results.summary.ai_literacy_level} literacy</p>
          <p className="text-sm theme-muted">{results.summary.ai_readiness_level} readiness</p>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Change Readiness</h2>
          <p className="mt-2 text-sm theme-muted">{results.summary.change_readiness}</p>
        </article>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <details className="glass-card p-5" open>
          <summary className="cursor-pointer font-display text-xl font-semibold theme-text">Personality tendencies</summary>
          <div className="mt-4 space-y-2">
            {personality.map((score) => (
              <p key={score.id} className="text-sm theme-muted"><b className="theme-text">{dimensionLabel(score.dimension)}</b>: {score.label}</p>
            ))}
          </div>
        </details>
        <details className="glass-card p-5" open>
          <summary className="cursor-pointer font-display text-xl font-semibold theme-text">Top work values</summary>
          <div className="mt-4 flex flex-wrap gap-2">
            {topValues.map((value) => <span key={value.value} className="organic-chip">{value.label}</span>)}
          </div>
        </details>
        <details className="glass-card p-5" open>
          <summary className="cursor-pointer font-display text-xl font-semibold theme-text">Skills and evidence</summary>
          <div className="mt-4 space-y-2">
            {skills.map((skill) => (
              <p key={skill.id} className="text-sm theme-muted"><b className="theme-text">{skill.label}</b>: {skill.level_label}, {skill.evidence_status.replace(/_/g, " ")}</p>
            ))}
          </div>
        </details>
      </section>

      <section className="glass-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-display text-3xl font-semibold theme-text">Compatible career families</h2>
            <p className="mt-2 text-sm theme-muted">The system returns several role families and starts with current-profession augmentation before reskilling.</p>
          </div>
          <button type="button" className="organic-button" disabled={selected.length === 0} onClick={() => void compare()}>
            <GitCompare size={16} /> Compare selected ({selected.length}/3)
          </button>
        </div>

        {comparison ? (
          <div className="mt-5 rounded-2xl border border-[color:var(--color-accent-action-border)] p-4">
            <h3 className="font-display text-2xl font-semibold theme-text">Decision matrix</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-3">
              {comparison.matrix.items.map((item) => (
                <article key={item.match_id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                  <h4 className="font-bold theme-text">{item.title}</h4>
                  <p className="mt-2 text-sm text-[color:var(--color-accent-action-muted)]">{item.alignment_label}</p>
                  <p className="mt-3 text-sm theme-muted">Next experiment: {item.next_experiment}</p>
                  <p className="mt-2 text-sm theme-muted">Evidence required: {item.evidence_required.join(", ")}</p>
                </article>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mt-6 space-y-8">
          {categoryOrder.map((category) => (
            <section key={category}>
              <h3 className="font-display text-2xl font-semibold theme-text">{categoryLabels[category]}</h3>
              <div className="mt-4 grid gap-4">
                {(grouped[category] || []).map((match) => (
                  <MatchCard
                    key={match.id}
                    match={match}
                    selected={selected.includes(match.id)}
                    onToggleCompare={() => setSelected((current) => current.includes(match.id) ? current.filter((item) => item !== match.id) : current.length < 3 ? [...current, match.id] : current)}
                    onSave={() => void updateMatch(saveCareerMatch(match.id), "Career direction saved.")}
                    onReject={() => void updateMatch(rejectCareerMatch(match.id, { reason_code: "not_for_me" }), "Career direction rejected.")}
                    onAlternative={() => void updateMatch(requestCareerAlternative(match.id), "Alternative directions requested.")}
                    onRoadmap={() => void updateMatch(createCareerRoadmapDraft(match.id), "Exploratory roadmap draft created after explicit confirmation.")}
                  />
                ))}
                {!grouped[category]?.length ? <p className="rounded-2xl border border-[color:var(--border-soft)] p-4 text-sm theme-muted">No active suggestions in this category.</p> : null}
              </div>
            </section>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_auto]">
        <details className="glass-card p-5">
          <summary className="cursor-pointer font-display text-2xl font-semibold theme-text">Methodology and limitations</summary>
          <div className="mt-4 space-y-3 text-sm leading-6 theme-muted">
            <p>{results.methodology_note}</p>
            <p>Raw answers and deterministic scores are stored separately from explanations. LLM-generated explanation is not used to calculate raw scores.</p>
            <p>Alignment labels are visual presentation categories. They are not employment suitability ratings, psychological diagnoses, or guarantees.</p>
          </div>
        </details>
        <div className="glass-card flex flex-col gap-3 p-5">
          <button type="button" className="organic-button-secondary" onClick={() => void confirmAssessmentResults(id, { confirmation_status: "confirmed", summary: "User reviewed the assessment results." }).then(() => setStatus("Results confirmed."))}>
            <CheckCircle2 size={16} /> Confirm results
          </button>
          <button type="button" className="organic-button-secondary" onClick={() => navigate(`/workspace/${id}/assessment`)}>
            <RefreshCw size={16} /> Review answers
          </button>
          <button type="button" className="organic-button-secondary text-red-700" onClick={() => void deleteData()}>
            <Trash2 size={16} /> Delete assessment data
          </button>
        </div>
      </section>

      <section className="glass-card p-5">
        <h2 className="font-display text-2xl font-semibold theme-text">Reflection prompts</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {results.reflection_prompts.map((prompt) => (
            <div key={prompt} className="rounded-2xl border border-[color:var(--border-soft)] p-4 text-sm theme-muted">
              <ShieldAlert className="mb-2 text-[color:var(--color-accent-action-muted)]" size={18} />
              {prompt}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
