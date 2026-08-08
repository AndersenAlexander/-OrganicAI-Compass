import { CheckCircle2, Play, RefreshCw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { generateLearningPath, getLearningPath, updateLearningProgress } from "../api/learningApi";
import { useAppActions } from "../hooks/useAppActions";
import type { LearningPath, LearningPathItem } from "../types/learning";

const statuses = ["planned", "not_started", "in_progress", "paused", "completed", "abandoned", "replaced"];

export function LearningProgressPage() {
  const { profileId } = useParams();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const id = profileId || activeProfileId || "demo-profile";
  const [path, setPath] = useState<LearningPath | null>(null);
  const [editing, setEditing] = useState<LearningPathItem | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setPath(await getLearningPath(id));
  }

  useEffect(() => {
    setActiveProfileId(id);
    load().catch(() => setError("Learning progress could not be loaded."));
  }, [id, setActiveProfileId]);

  async function createPath() {
    const generated = await generateLearningPath(id);
    setPath(generated);
    setMessage("Learning path generated from the latest recommendation run.");
  }

  async function quickUpdate(item: LearningPathItem, status: string) {
    const updated = await updateLearningProgress(item.id, { status, progress_percentage: status === "completed" ? 100 : status === "in_progress" ? Math.max(item.progress_percentage, 25) : item.progress_percentage });
    setPath((current) => current ? {
      ...current,
      phases: current.phases.map((phase) => ({ ...phase, items: phase.items.map((phaseItem) => phaseItem.id === item.id ? { ...phaseItem, ...(updated as LearningPathItem) } : phaseItem) })),
    } : current);
  }

  async function submitProgress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const form = new FormData(event.currentTarget);
    await updateLearningProgress(editing.id, {
      status: String(form.get("status") || editing.status),
      progress_percentage: Number(form.get("progress_percentage") || editing.progress_percentage),
      evidence_url: String(form.get("evidence_url") || ""),
      reflection: String(form.get("reflection") || ""),
      difficulty_feedback: String(form.get("difficulty_feedback") || ""),
      relevance_feedback: String(form.get("relevance_feedback") || ""),
      completion_date: String(form.get("completion_date") || ""),
      user_reported_progress: String(form.get("user_reported_progress") || ""),
    });
    setEditing(null);
    setMessage("Progress and evidence saved. Skill level is not automatically upgraded.");
    await load();
  }

  if (error) return <div className="organic-section text-red-700">{error}</div>;
  if (!path) return <div className="organic-section theme-muted">Loading learning progress...</div>;

  return (
    <div className="organic-page">
      <section className="organic-section">
        <p className="organic-badge">Learning Progress</p>
        <h1 className="mt-4 font-display text-4xl font-semibold theme-text">{path.title || "Personalised Learning Path"}</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">{path.summary || "Track learning actions, progress, evidence, and feedback."}</p>
        <div className="mt-6 flex flex-wrap gap-2">
          <Link className="organic-button-secondary" to={`/workspace/${id}/learning/recommendations`}>Learning Recommendations</Link>
          <button type="button" className="organic-button" onClick={() => void createPath()}><RefreshCw size={16} /> Generate from latest run</button>
        </div>
        {message ? <p className="mt-4 text-sm font-semibold text-[color:var(--teal)]" role="status">{message}</p> : null}
      </section>

      {path.status === "not_started" || !path.phases?.length ? (
        <section className="glass-card p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">No learning path yet.</h2>
          <p className="mt-2 text-sm theme-muted">Generate recommendations first, then create a staged learning path.</p>
          <Link className="organic-button-secondary mt-5" to={`/workspace/${id}/learning`}>Open Learning Path</Link>
        </section>
      ) : (
        <div className="space-y-5">
          {path.phases.map((phase) => (
            <section key={phase.id} className="glass-card p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--color-accent-action-muted)]">Phase {phase.phase_index}</p>
                  <h2 className="mt-1 font-display text-3xl font-semibold theme-text">{phase.title}</h2>
                  <p className="mt-2 text-sm theme-muted">{phase.description}</p>
                </div>
                <p className="organic-chip">{phase.completion_evidence}</p>
              </div>
              <div className="mt-4 grid gap-3">
                {phase.items.map((item) => (
                  <article key={item.id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <h3 className="font-display text-xl font-semibold theme-text">{item.title}</h3>
                        <p className="mt-1 text-sm theme-muted">{item.status.replace(/_/g, " ")} - {item.progress_percentage}%</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button className="organic-button-secondary" type="button" onClick={() => void quickUpdate(item, "in_progress")}><Play size={16} /> Start</button>
                        <button className="organic-button-secondary" type="button" onClick={() => void quickUpdate(item, "completed")}><CheckCircle2 size={16} /> Complete</button>
                        <button className="organic-button" type="button" onClick={() => setEditing(item)}>Evidence</button>
                      </div>
                    </div>
                    <progress className="mt-3 h-3 w-full" value={item.progress_percentage} max="100" />
                    <p className="mt-3 text-xs theme-muted">{item.expected_evidence}</p>
                    {item.evidence_url ? <a className="mt-2 inline-block text-sm font-semibold text-[color:var(--teal)] underline-offset-4 hover:underline" href={item.evidence_url}>Evidence</a> : null}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {editing ? (
        <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <form className="max-h-[90vh] w-full max-w-xl overflow-auto rounded-2xl bg-[color:var(--surface)] p-6 shadow-xl" onSubmit={submitProgress}>
            <h2 className="font-display text-2xl font-semibold theme-text">Update Learning Evidence</h2>
            <p className="mt-2 text-sm theme-muted">Evidence can support future recommendations, but course completion alone does not automatically increase a skill to Advanced.</p>
            <div className="mt-5 grid gap-3">
              <select name="status" className="rounded-xl border p-3 theme-muted" defaultValue={editing.status}>
                {statuses.map((status) => <option key={status} value={status}>{status.replace(/_/g, " ")}</option>)}
              </select>
              <label className="text-sm font-bold theme-text">Progress
                <input name="progress_percentage" type="range" min="0" max="100" defaultValue={editing.progress_percentage} className="organic-range-action mt-2 w-full" />
              </label>
              <input name="completion_date" type="date" className="rounded-xl border p-3 theme-muted" />
              <input name="evidence_url" className="rounded-xl border p-3 theme-muted" placeholder="Evidence URL or internal path" defaultValue={editing.evidence_url || ""} />
              <textarea name="user_reported_progress" className="min-h-20 rounded-xl border p-3 theme-muted" placeholder="Progress note" defaultValue={editing.user_reported_progress} />
              <textarea name="reflection" className="min-h-24 rounded-xl border p-3 theme-muted" placeholder="Reflection" defaultValue={editing.reflection} />
              <select name="difficulty_feedback" className="rounded-xl border p-3 theme-muted" defaultValue={editing.difficulty_feedback || ""}>
                <option value="">Difficulty feedback</option>
                <option value="too_basic">Too basic</option>
                <option value="too_advanced">Too advanced</option>
                <option value="useful">Useful</option>
              </select>
              <select name="relevance_feedback" className="rounded-xl border p-3 theme-muted" defaultValue={editing.relevance_feedback || ""}>
                <option value="">Relevance feedback</option>
                <option value="relevant">Relevant</option>
                <option value="not_relevant">Not relevant</option>
                <option value="too_theoretical">Too theoretical</option>
              </select>
            </div>
            <div className="mt-5 flex gap-3">
              <button className="organic-button" type="submit">Save Progress</button>
              <button className="organic-button-secondary" type="button" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
}
