import { BarChart3, CheckCircle2, Route, XCircle } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  addLearningRecommendationToRoadmap,
  createLearningComparison,
  getLearningRecommendations,
  rejectLearningRecommendation,
  saveLearningRecommendation,
} from "../api/learningApi";
import { useAppActions } from "../hooks/useAppActions";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";
import type { LearningRecommendation, LearningResourceComparison } from "../types/learning";

const criteriaLabels: Record<string, string> = {
  skill_gap_relevance: "Skill coverage",
  objective_coverage: "Objective coverage",
  level_compatibility: "Level",
  time_fit: "Duration",
  budget_fit: "Price",
  language_fit: "Language",
  format_preference: "Format",
  source_quality: "Provider quality",
  practical_evidence_value: "Project component",
  freshness: "Last verification",
};

export function LearningComparePage() {
  const { profileId } = useParams();
  const [searchParams] = useSearchParams();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const id = profileId || activeProfileId;
  const initialIds = useMemo(() => (searchParams.get("ids") || "").split(",").filter(Boolean), [searchParams]);
  const [recommendations, setRecommendations] = useState<LearningRecommendation[]>([]);
  const [selected, setSelected] = useState<string[]>(initialIds);
  const [weights, setWeights] = useState<Record<string, number>>(() => Object.fromEntries(Object.keys(criteriaLabels).map((key) => [key, 1])));
  const [comparison, setComparison] = useState<LearningResourceComparison | null>(null);
  const [roadmapCandidate, setRoadmapCandidate] = useState<{ recommendation_id: string; title: string } | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    setActiveProfileId(id);
    getLearningRecommendations(id)
      .then((run) => {
        setRecommendations(run.recommendations || []);
        const ids = initialIds.length ? initialIds : (run.recommendations || []).slice(0, 3).map((item) => item.id);
        setSelected(ids.slice(0, 3));
      })
      .catch(() => setError("Learning resources could not be loaded for comparison."));
  }, [id, initialIds, setActiveProfileId]);

  async function compare() {
    if (!id || !selected.length) return;
    const created = await createLearningComparison(id, selected, weights);
    setComparison(created);
    setMessage("Comparison matrix created. It does not alter core assessment scores or ranking history.");
  }

  async function submitRoadmap(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!roadmapCandidate) return;
    const form = new FormData(event.currentTarget);
    await addLearningRecommendationToRoadmap(roadmapCandidate.recommendation_id, {
      roadmap_title: String(form.get("roadmap_title") || ""),
      learning_objective: String(form.get("learning_objective") || ""),
      weekly_commitment: String(form.get("weekly_commitment") || ""),
      priority: Number(form.get("priority") || 2),
      expected_evidence: String(form.get("expected_evidence") || ""),
      notes: String(form.get("notes") || ""),
    });
    setRoadmapCandidate(null);
    setMessage("Selected resource added to My Roadmap after confirmation.");
  }

  const selectedRecommendations = recommendations.filter((item) => selected.includes(item.id));

  if (!id) return <ProfileRequiredState title="Create your profile before comparing learning resources." />;
  if (error) return <div className="organic-section text-red-700">{error}</div>;

  return (
    <div className="organic-page">
      <section className="organic-section">
        <p className="organic-badge">Compare Learning Resources</p>
        <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Compare up to three real stored resources.</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">The matrix compares metadata and deterministic factors. It does not invent prices, ratings, providers, or availability.</p>
        <div className="mt-6 flex flex-wrap gap-2">
          <Link className="organic-button-secondary" to={`/workspace/${id}/learning/recommendations`}>Back to Recommendations</Link>
          <button type="button" className="organic-button" disabled={!selected.length} onClick={() => void compare()}><BarChart3 size={16} /> Create Matrix</button>
        </div>
        {message ? <p className="mt-4 text-sm font-semibold text-[color:var(--teal)]" role="status">{message}</p> : null}
      </section>

      <div className="grid gap-5 xl:grid-cols-[1fr_22rem]">
        <section className="glass-card p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Resources</h2>
          <div className="mt-4 grid gap-3">
            {recommendations.map((item) => (
              <label key={item.id} className="flex cursor-pointer items-start gap-3 rounded-2xl border border-[color:var(--border-soft)] p-4">
                <input
                  className="mt-1 h-5 w-5 accent-[color:var(--color-accent-action)]"
                  type="checkbox"
                  checked={selected.includes(item.id)}
                  onChange={() => setSelected((current) => current.includes(item.id) ? current.filter((id) => id !== item.id) : current.length < 3 ? [...current, item.id] : current)}
                />
                <span>
                  <b className="theme-text">{item.resource.title}</b>
                  <span className="mt-1 block text-sm theme-muted">{item.alignment_label} - {item.resource.provider_id} - {item.resource.resource_type_label}</span>
                  <span className="mt-1 block text-xs theme-muted">{item.skill_gap?.skill_label || "General"} - {item.resource.cost_type}</span>
                </span>
              </label>
            ))}
          </div>
        </section>

        <aside className="glass-card h-fit p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Criteria Weights</h2>
          <div className="mt-4 space-y-4">
            {Object.entries(criteriaLabels).map(([key, label]) => (
              <label key={key} className="block text-xs font-bold theme-text">
                <span className="flex justify-between gap-3"><span>{label}</span><span>{weights[key].toFixed(1)}</span></span>
                <input className="organic-range-action mt-2 w-full" type="range" min="0" max="2" step="0.25" value={weights[key]} onChange={(event) => setWeights((current) => ({ ...current, [key]: Number(event.target.value) }))} />
              </label>
            ))}
          </div>
        </aside>
      </div>

      {comparison ? (
        <section className="glass-card p-5">
          <h2 className="font-display text-3xl font-semibold theme-text">Comparison Matrix</h2>
          <div className="mt-5 grid gap-4 lg:grid-cols-3">
            {comparison.matrix.items.map((item) => (
              <article key={item.recommendation_id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                <h3 className="font-display text-2xl font-semibold theme-text">{item.title}</h3>
                <p className="mt-2 text-sm font-bold text-[color:var(--color-accent-action-muted)]">{item.alignment_label}</p>
                <dl className="mt-4 space-y-2 text-sm theme-muted">
                  <div><dt className="font-bold theme-text">Provider</dt><dd>{item.provider}</dd></div>
                  <div><dt className="font-bold theme-text">Level</dt><dd>{item.level}</dd></div>
                  <div><dt className="font-bold theme-text">Duration</dt><dd>{item.duration_minutes ? `${item.duration_minutes} min` : "Not provided"}</dd></div>
                  <div><dt className="font-bold theme-text">Cost</dt><dd>{item.cost_type}</dd></div>
                  <div><dt className="font-bold theme-text">Certificate</dt><dd>{item.certificate_available ? "Available" : "Not provided"}</dd></div>
                  <div><dt className="font-bold theme-text">Project</dt><dd>{item.project_component ? "Included" : "Not included"}</dd></div>
                </dl>
                <h4 className="mt-4 text-sm font-bold theme-text">Strengths</h4>
                <p className="mt-2 text-sm theme-muted">{item.strengths.length ? item.strengths.join(", ") : "No single factor dominates."}</p>
                <h4 className="mt-4 text-sm font-bold theme-text">Limitations</h4>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">{item.limitations.map((value) => <li key={value}>{value}</li>)}</ul>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button type="button" className="organic-button-secondary" onClick={() => void saveLearningRecommendation(item.recommendation_id).then(() => setMessage("Preferred option saved."))}><CheckCircle2 size={16} /> Save</button>
                  <button type="button" className="organic-button" onClick={() => setRoadmapCandidate({ recommendation_id: item.recommendation_id, title: item.title })}><Route size={16} /> Add</button>
                  <button type="button" className="organic-button-secondary text-red-700" onClick={() => void rejectLearningRecommendation(item.recommendation_id, { reason_code: "not_relevant" }).then(() => setMessage("Resource rejected."))}><XCircle size={16} /> Reject</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : selectedRecommendations.length ? (
        <section className="glass-card p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Selected Resources</h2>
          <div className="mt-3 flex flex-wrap gap-2">{selectedRecommendations.map((item) => <span key={item.id} className="organic-chip">{item.resource.title}</span>)}</div>
        </section>
      ) : null}

      {roadmapCandidate ? (
        <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <form className="w-full max-w-xl rounded-2xl bg-[color:var(--surface)] p-6 shadow-xl" onSubmit={submitRoadmap}>
            <h2 className="font-display text-2xl font-semibold theme-text">Confirm Roadmap Learning Action</h2>
            <p className="mt-2 text-sm theme-muted">No resource is added automatically. Confirm the evidence and commitment first.</p>
            <div className="mt-5 grid gap-3">
              <input name="roadmap_title" className="rounded-xl border p-3 theme-muted" defaultValue={`Learn: ${roadmapCandidate.title}`} />
              <textarea name="learning_objective" className="min-h-20 rounded-xl border p-3 theme-muted" defaultValue={`Build evidence with ${roadmapCandidate.title}.`} />
              <input name="weekly_commitment" className="rounded-xl border p-3 theme-muted" defaultValue="3 hours/week" />
              <input name="priority" type="number" min="1" max="5" className="rounded-xl border p-3 theme-muted" defaultValue={2} />
              <textarea name="expected_evidence" className="min-h-20 rounded-xl border p-3 theme-muted" defaultValue="Summary, practical exercise, or portfolio evidence." />
              <textarea name="notes" className="min-h-20 rounded-xl border p-3 theme-muted" placeholder="Notes" />
            </div>
            <div className="mt-5 flex gap-3">
              <button className="organic-button" type="submit">Add to My Roadmap</button>
              <button className="organic-button-secondary" type="button" onClick={() => setRoadmapCandidate(null)}>Cancel</button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
}
