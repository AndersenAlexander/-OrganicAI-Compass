import { CheckCircle2, ExternalLink, GitCompare, RefreshCw, Route, XCircle } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  addLearningRecommendationToRoadmap,
  generateLearningPath,
  generateLearningRecommendations,
  getLearningRecommendations,
  rejectLearningRecommendation,
  requestLearningAlternative,
  saveLearningRecommendation,
  sendLearningFeedback,
} from "../api/learningApi";
import { useAppActions } from "../hooks/useAppActions";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";
import type { LearningRecommendation, LearningRecommendationRun } from "../types/learning";

function minutesLabel(value?: number | null) {
  if (!value) return "Not provided";
  if (value < 90) return `${value} min`;
  return `${Math.round(value / 60)} h`;
}

function moneyLabel(resource: LearningRecommendation["resource"]) {
  if (resource.cost_type === "free" || resource.cost_type === "open") return "Free";
  if (resource.displayed_price != null) return `${resource.displayed_price} ${resource.currency || ""}`.trim();
  return "Check provider page";
}

function safeDateLabel(value?: string | null) {
  if (!value) return "Not verified";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not verified" : date.toLocaleDateString();
}

function groupRecommendations(items: LearningRecommendation[]) {
  return items.reduce<Record<string, LearningRecommendation[]>>((groups, item) => {
    const key = item.skill_gap?.skill_label || "General";
    groups[key] = [...(groups[key] || []), item];
    return groups;
  }, {});
}

function RecommendationCard({
  recommendation,
  selected,
  onCompare,
  onSave,
  onReject,
  onAlternative,
  onFeedback,
  onRoadmap,
}: {
  recommendation: LearningRecommendation;
  selected: boolean;
  onCompare: () => void;
  onSave: () => void;
  onReject: (reason: string) => void;
  onAlternative: (reason?: string) => void;
  onFeedback: (reason: string) => void;
  onRoadmap: () => void;
}) {
  const resource = recommendation.resource;
  return (
    <article className="rounded-2xl border border-[color:var(--border-soft)] bg-[color:var(--color-surface-secondary)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--color-accent-action-muted)]">{recommendation.alignment_label}</p>
          <h3 className="mt-1 font-display text-2xl font-semibold theme-text">{resource.title}</h3>
          <p className="mt-1 text-sm theme-muted">{resource.provider_id} - {resource.resource_type_label} - {resource.level}</p>
        </div>
        <label className="organic-chip cursor-pointer">
          <input className="h-4 w-4 accent-[color:var(--color-accent-action)]" type="checkbox" checked={selected} onChange={onCompare} />
          Compare
        </label>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs theme-muted">
        <span className="organic-chip">{minutesLabel(resource.duration_minutes)}</span>
        <span className="organic-chip">{(resource.language || "en").toUpperCase()}</span>
        <span className="organic-chip">{moneyLabel(resource)}</span>
        <span className="organic-chip">{resource.quality_status}</span>
        {resource.project_included ? <span className="organic-chip">Project included</span> : null}
        {resource.certificate_available ? <span className="organic-chip">Certificate available</span> : null}
      </div>

      <p className="mt-4 text-sm leading-6 theme-muted">{recommendation.explanation}</p>
      {recommendation.objective ? <p className="mt-3 rounded-2xl border border-[color:var(--color-accent-action-border)] bg-[color:var(--color-accent-action-soft)] p-3 text-sm theme-muted">{recommendation.objective.description}</p> : null}

      <details className="mt-3 rounded-2xl border border-[color:var(--border-soft)] p-4">
        <summary className="cursor-pointer font-bold theme-text">Details and traceability</summary>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-bold theme-text">Skills covered</h4>
            <p className="mt-2 text-sm theme-muted">{(resource.skills || []).map((skill) => (skill.skill_id || "skill").replace(/_/g, " ")).join(", ") || recommendation.skill_gap?.skill_label || "Not provided"}</p>
          </div>
          <div>
            <h4 className="text-sm font-bold theme-text">Verification</h4>
            <p className="mt-2 text-sm theme-muted">{safeDateLabel(resource.last_verified_at)} - {resource.source_provenance || "Not provided"}</p>
          </div>
          <div>
            <h4 className="text-sm font-bold theme-text">Limitations</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">{(recommendation.limitations || []).map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
          <div>
            <h4 className="text-sm font-bold theme-text">Ranking factors</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">{(recommendation.factors || []).slice(0, 4).map((factor, index) => <li key={factor.id || index}>{(factor.factor_type || "factor").replace(/_/g, " ")}: {Math.round(Number(factor.factor_value) || 0)}</li>)}</ul>
          </div>
        </div>
        <p className="mt-4 text-xs theme-muted">{resource.affiliate_disclosure || "No affiliate relationship is used for ranking."}</p>
      </details>

      <div className="mt-4 flex flex-wrap gap-2">
        <a className="organic-button-secondary" href={resource.canonical_url} target="_blank" rel="noreferrer"><ExternalLink size={16} /> Open provider</a>
        <button type="button" className="organic-button-secondary" onClick={onSave}><CheckCircle2 size={16} /> Save</button>
        <button type="button" className="organic-button" onClick={onRoadmap}><Route size={16} /> Add to roadmap</button>
        <button type="button" className="organic-button-secondary" onClick={() => onAlternative("alternative_requested")}><RefreshCw size={16} /> Replace</button>
        <button type="button" className="organic-button-secondary text-red-700" onClick={() => onReject("not_relevant")}><XCircle size={16} /> Not relevant</button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {[
          ["too_basic", "Too basic"],
          ["too_advanced", "Too advanced"],
          ["too_expensive", "Request free alternative"],
          ["too_long", "Too long"],
          ["wrong_language", "Wrong language"],
          ["already_completed", "Already completed"],
          ["too_theoretical", "Request practical alternative"],
        ].map(([reason, label]) => (
          <button key={reason} type="button" className="text-xs font-semibold text-[color:var(--teal)] underline-offset-4 hover:underline" onClick={() => reason.includes("alternative") || reason === "too_expensive" || reason === "too_theoretical" ? onAlternative(reason) : onFeedback(reason)}>
            {label}
          </button>
        ))}
      </div>
      <p className="mt-3 text-xs font-bold text-[color:var(--color-accent-action-muted)]">Status: {(recommendation.status || "suggested").replace(/_/g, " ")}</p>
    </article>
  );
}

export function LearningRecommendationsPage() {
  const { profileId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const id = profileId || activeProfileId;
  const careerMatchId = searchParams.get("match") || undefined;
  const [run, setRun] = useState<LearningRecommendationRun | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [resourceType, setResourceType] = useState("all");
  const [cost, setCost] = useState("all");
  const [roadmapItem, setRoadmapItem] = useState<LearningRecommendation | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    if (!id) return;
    const data = await getLearningRecommendations(id, careerMatchId);
    setRun(data);
  }

  useEffect(() => {
    if (!id) return;
    setActiveProfileId(id);
    load().catch((err) => {
      if (err?.response?.status === 409) setError("Select or save a career direction before generating a personalised learning path.");
      else setError("Learning recommendations could not be loaded.");
    });
  }, [id, careerMatchId, setActiveProfileId]);

  const filtered = useMemo(() => {
    const items = run?.recommendations || [];
    return items.filter((item) => {
      if (resourceType !== "all" && item.resource.resource_type !== resourceType) return false;
      if (cost === "free" && !["free", "open"].includes(item.resource.cost_type)) return false;
      if (cost === "paid" && ["free", "open"].includes(item.resource.cost_type)) return false;
      return true;
    });
  }, [run, resourceType, cost]);
  const grouped = useMemo(() => groupRecommendations(filtered), [filtered]);
  const recommendations = run?.recommendations || [];
  const providerStatus = run?.provider_status || [];
  const hardFilters = run?.hard_filters || [];
  const resourceTypes = useMemo(() => Array.from(new Set(recommendations.map((item) => item.resource.resource_type))), [recommendations]);

  async function refreshWith(action: Promise<unknown>, nextMessage: string) {
    await action;
    setMessage(nextMessage);
    await load();
  }

  async function generate() {
    if (!id) return;
    const data = await generateLearningRecommendations(id, careerMatchId);
    setRun(data);
    setMessage("Recommendations regenerated from stored resource records.");
  }

  async function createPath() {
    if (!id || !run?.id) return;
    await generateLearningPath(id, run.id);
    navigate(`/workspace/${id}/learning/progress`);
  }

  async function submitRoadmap(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!id || !roadmapItem) return;
    const form = new FormData(event.currentTarget);
    await addLearningRecommendationToRoadmap(roadmapItem.id, {
      roadmap_title: String(form.get("roadmap_title") || ""),
      learning_objective: String(form.get("learning_objective") || ""),
      start_date: String(form.get("start_date") || ""),
      target_completion_date: String(form.get("target_completion_date") || ""),
      weekly_commitment: String(form.get("weekly_commitment") || ""),
      priority: Number(form.get("priority") || 2),
      expected_evidence: String(form.get("expected_evidence") || ""),
      associated_practical_project: String(form.get("associated_practical_project") || ""),
      notes: String(form.get("notes") || ""),
    });
    setRoadmapItem(null);
    setMessage("Learning action added to My Roadmap after confirmation.");
    await load();
  }

  if (!id) return <ProfileRequiredState title="Create your profile before viewing learning recommendations." />;
  if (error) {
    return (
      <section className="organic-section">
        <p className="organic-badge">Learning Recommendations</p>
        <h1 className="mt-4 font-display text-4xl font-semibold theme-text">{error}</h1>
        <Link className="organic-button mt-6" to={`/workspace/${id}/learning`}>Select Career Direction</Link>
      </section>
    );
  }
  if (!run) return <div className="organic-section theme-muted">Loading Learning Recommendations...</div>;

  return (
    <div className="organic-page">
      <section className="organic-section">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="organic-badge">Learning Recommendations</p>
            <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Review alternatives before adding anything to My Roadmap.</h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">Resources are grouped by skill gap. Hard filters and ranking factors are stored for traceability.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="organic-button-secondary" onClick={() => void generate()}><RefreshCw size={16} /> Regenerate</button>
            <button type="button" className="organic-button" disabled={!selected.length} onClick={() => navigate(`/workspace/${id}/learning/compare?ids=${selected.join(",")}`)}><GitCompare size={16} /> Compare ({selected.length}/3)</button>
          </div>
        </div>
        {message ? <p className="mt-4 text-sm font-semibold text-[color:var(--teal)]" role="status">{message}</p> : null}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Provider Status</h2>
          <div className="mt-3 space-y-2 text-sm theme-muted">{providerStatus.map((item, index) => <p key={index}>{item.provider || `provider_${index + 1}`}: {item.status || "unknown"}</p>)}</div>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Hard Filters</h2>
          <p className="mt-3 text-sm theme-muted">{hardFilters.length} exclusions recorded for inactive, language, budget, provider, duration, prerequisite, or feedback reasons.</p>
        </article>
        <article className="glass-card p-5">
          <h2 className="font-display text-xl font-semibold theme-text">Learning Path Draft</h2>
          <button type="button" className="organic-button mt-3" disabled={!recommendations.length} onClick={() => void createPath()}>Generate staged path</button>
        </article>
      </section>

      <section className="glass-card p-5">
        <div className="flex flex-wrap gap-3">
          <select className="rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" value={resourceType} onChange={(event) => setResourceType(event.target.value)} aria-label="Resource type filter">
            <option value="all">All resource types</option>
            {resourceTypes.map((type) => <option key={type} value={type}>{type.replace(/_/g, " ")}</option>)}
          </select>
          <select className="rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" value={cost} onChange={(event) => setCost(event.target.value)} aria-label="Cost filter">
            <option value="all">All costs</option>
            <option value="free">Free only</option>
            <option value="paid">Paid or audit-priced</option>
          </select>
          <Link className="organic-button-secondary" to={`/workspace/${id}/learning/preferences`}>Edit Preferences</Link>
        </div>

        {!filtered.length ? (
          <div className="mt-5 rounded-2xl border border-[color:var(--border-soft)] p-5">
            <h2 className="font-display text-2xl font-semibold theme-text">No matching resources for the current filters.</h2>
            <p className="mt-2 text-sm theme-muted">Try alternative language, budget, duration, or format preferences. External provider failures do not block the curated catalogue.</p>
          </div>
        ) : (
          <div className="mt-6 space-y-8">
            {Object.entries(grouped).map(([gap, items]) => (
              <section key={gap}>
                <h2 className="font-display text-3xl font-semibold theme-text">{gap}</h2>
                <div className="mt-4 grid gap-4">
                  {items.map((item) => (
                    <RecommendationCard
                      key={item.id}
                      recommendation={item}
                      selected={selected.includes(item.id)}
                      onCompare={() => setSelected((current) => current.includes(item.id) ? current.filter((id) => id !== item.id) : current.length < 3 ? [...current, item.id] : current)}
                      onSave={() => void refreshWith(saveLearningRecommendation(item.id), "Resource saved.")}
                      onReject={(reason) => void refreshWith(rejectLearningRecommendation(item.id, { reason_code: reason }), "Resource rejected and excluded from future runs.")}
                      onAlternative={(reason) => void refreshWith(requestLearningAlternative(item.id, reason), "Alternative requested. Future ranking accounts for this feedback.")}
                      onFeedback={(reason) => void refreshWith(sendLearningFeedback(item.id, { reason_code: reason }), "Feedback saved for future recommendation runs.")}
                      onRoadmap={() => setRoadmapItem(item)}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </section>

      {roadmapItem ? (
        <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <form className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-2xl bg-[color:var(--surface)] p-6 shadow-xl" onSubmit={submitRoadmap}>
            <h2 className="font-display text-3xl font-semibold theme-text">Confirm Roadmap Learning Action</h2>
            <p className="mt-2 text-sm theme-muted">Nothing is added automatically. Confirm the action, evidence, and commitment first.</p>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <label className="text-sm font-bold theme-text">Roadmap title<input name="roadmap_title" className="mt-2 w-full rounded-xl border p-3 theme-muted" defaultValue={`Learn: ${roadmapItem.resource.title}`} /></label>
              <label className="text-sm font-bold theme-text">Weekly commitment<input name="weekly_commitment" className="mt-2 w-full rounded-xl border p-3 theme-muted" defaultValue="3 hours/week" /></label>
              <label className="text-sm font-bold theme-text">Start date<input name="start_date" type="date" className="mt-2 w-full rounded-xl border p-3 theme-muted" /></label>
              <label className="text-sm font-bold theme-text">Target completion<input name="target_completion_date" type="date" className="mt-2 w-full rounded-xl border p-3 theme-muted" /></label>
              <label className="text-sm font-bold theme-text md:col-span-2">Learning objective<textarea name="learning_objective" className="mt-2 min-h-20 w-full rounded-xl border p-3 theme-muted" defaultValue={roadmapItem.objective?.description || `Build evidence with ${roadmapItem.resource.title}`} /></label>
              <label className="text-sm font-bold theme-text">Priority<input name="priority" type="number" min="1" max="5" className="mt-2 w-full rounded-xl border p-3 theme-muted" defaultValue={2} /></label>
              <label className="text-sm font-bold theme-text">Associated practical project<input name="associated_practical_project" className="mt-2 w-full rounded-xl border p-3 theme-muted" /></label>
              <label className="text-sm font-bold theme-text md:col-span-2">Expected evidence<textarea name="expected_evidence" className="mt-2 min-h-20 w-full rounded-xl border p-3 theme-muted" defaultValue="Personal summary, practical exercise, project note, or portfolio artifact." /></label>
              <label className="text-sm font-bold theme-text md:col-span-2">Notes<textarea name="notes" className="mt-2 min-h-20 w-full rounded-xl border p-3 theme-muted" /></label>
            </div>
            <div className="mt-5 flex flex-wrap gap-3">
              <button className="organic-button" type="submit">Add to My Roadmap</button>
              <button className="organic-button-secondary" type="button" onClick={() => setRoadmapItem(null)}>Cancel</button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
}
