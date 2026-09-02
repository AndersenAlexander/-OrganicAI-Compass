import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  applyRecalibration,
  completeRoadmapAction,
  createRoadmapAction,
  deleteRoadmapAction,
  generateRoadmap,
  getRoadmap,
  getRoadmapCheckIns,
  getRoadmapEvents,
  getRoadmapVersions,
  postponeRoadmapAction,
  proposeRecalibration,
  skipRoadmapAction,
  startRoadmapAction,
  submitRoadmapCheckIn,
  updateRoadmapAction,
} from "../api/roadmapApi";
import { extractApiError } from "../api/client";
import { RoadmapActionCard } from "../components/roadmap/RoadmapActionCard";
import { useCoach } from "../hooks/useCoach";
import type { RecalibrationProposal, Roadmap, RoadmapAction, RoadmapCheckIn, RoadmapEvent } from "../types/roadmap";

const labels = { overview: "Overview", seven_days: "Next 7 Days", thirty_days: "Next 30 Days", six_months: "Next 6 Months", checkins: "Check-ins", history: "History" } as const;
type Tab = keyof typeof labels;

function requestErrorMessage(error: unknown, fallback: string) {
  const details = extractApiError(error);
  if (details.message !== "The request failed.") return details.message;
  return error instanceof Error ? error.message : fallback;
}

function eventLabel(event: RoadmapEvent) {
  const label = event.event_type.replace(/_/g, " ");
  return label.charAt(0).toUpperCase() + label.slice(1);
}

export function RoadmapPage() {
  const { profileId } = useParams();
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [checkins, setCheckins] = useState<RoadmapCheckIn[]>([]);
  const [versions, setVersions] = useState<Array<{ version_number: number; reason: string; created_at: string }>>([]);
  const [events, setEvents] = useState<RoadmapEvent[]>([]);
  const [proposal, setProposal] = useState<RecalibrationProposal | null>(null);
  const [selectedChanges, setSelectedChanges] = useState<number[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const coach = useCoach();

  async function refetchRoadmapQueries(roadmapId: string) {
    // This frontend uses local state rather than a query-cache library. Keep all
    // roadmap-derived views consistent by explicitly refetching their queries.
    const [checkinData, versionData, eventData] = await Promise.all([
      getRoadmapCheckIns(roadmapId).catch(() => []),
      getRoadmapVersions(roadmapId).catch(() => []),
      getRoadmapEvents(roadmapId).catch(() => []),
    ]);
    setCheckins(checkinData);
    setVersions(versionData);
    setEvents(eventData);
  }

  async function load() {
    if (!profileId) return null;
    setError("");
    try {
      const next = (await getRoadmap(profileId)) || (await generateRoadmap(profileId));
      setRoadmap(next);
      await refetchRoadmapQueries(next.id);
      return next;
    } catch (requestError) {
      setError(`Your roadmap could not be loaded. ${requestErrorMessage(requestError, "Please try again.")} Please try again.`);
      throw requestError;
    }
  }

  useEffect(() => {
    void load().catch(() => undefined);
  }, [profileId]);

  async function runRoadmapMutation(operation: () => Promise<unknown>, successMessage: string) {
    setError("");
    setMessage("");
    try {
      await operation();
      await load();
      setMessage(successMessage);
    } catch (requestError) {
      setError(`Roadmap update failed. ${requestErrorMessage(requestError, "Please try again.")} Please try again.`);
    }
  }

  if (!roadmap) return <div className="organic-section theme-muted">{error || "Building your roadmap..."}</div>;

  const actionCard = (action: RoadmapAction) => <RoadmapActionCard key={action.id} action={action}
    onUpdate={patch => { void runRoadmapMutation(() => updateRoadmapAction(action.id, patch), "Roadmap action updated."); }}
    onStart={() => { void runRoadmapMutation(() => startRoadmapAction(action.id), "Roadmap action started."); }}
    onComplete={note => { void runRoadmapMutation(() => completeRoadmapAction(action.id, note), "Roadmap action completed."); }}
    onSkip={reason => { void runRoadmapMutation(() => skipRoadmapAction(action.id, reason), "Roadmap action skipped."); }}
    onPostpone={() => { void runRoadmapMutation(() => postponeRoadmapAction(action.id, undefined, "User postponed this action"), "Roadmap action postponed."); }}
    onRemove={() => { void runRoadmapMutation(() => deleteRoadmapAction(action.id), "Roadmap action removed."); }}
    onCoach={() => void coach.sendTextMessage(`Please explain and help me start roadmap action ${action.id}`)} />;

  async function add() {
    const title = prompt("Action title");
    if (!title) return;
    await runRoadmapMutation(() => createRoadmapAction(roadmap!.id, { title, horizon: "seven_days", first_step: "Choose the smallest first step.", success_criteria: "Record an outcome.", source_type: "user_created" }), "Action added to your roadmap.");
  }

  async function submitCheckIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      const item = await submitRoadmapCheckIn(roadmap!.id, {
        energy_level: Number(data.get("energy")),
        confidence_level: Number(data.get("confidence")),
        perceived_progress: Number(data.get("progress")),
        what_worked: String(data.get("worked") || ""),
        main_blocker: String(data.get("blocker") || ""),
        what_changed: String(data.get("changed") || ""),
      });
      setCheckins(current => [item, ...current]);
      await refetchRoadmapQueries(roadmap!.id);
      setMessage("Check-in saved.");
      form.reset();
    } catch (requestError) {
      setError(`Check-in could not be saved. ${requestErrorMessage(requestError, "Please try again.")} Please try again.`);
    }
  }

  async function openRecalibration() {
    setError("");
    try {
      const next = await proposeRecalibration(roadmap!.id);
      setProposal(next);
      setSelectedChanges(next.changes.map((_, index) => index));
    } catch (requestError) {
      setError(`Recalibration could not be prepared. ${requestErrorMessage(requestError, "Please try again.")} Please try again.`);
    }
  }

  async function applySelectedRecalibration() {
    if (!selectedChanges.length) return;
    setError("");
    try {
      await applyRecalibration(roadmap!.id, selectedChanges);
      await load();
      setProposal(null);
      setMessage("Selected recalibration changes applied.");
    } catch (requestError) {
      setError(`Recalibration could not be applied. ${requestErrorMessage(requestError, "Please try again.")} Please try again.`);
    }
  }

  const current = tab in roadmap.horizons ? roadmap.horizons[tab as keyof typeof roadmap.horizons] : [];

  return <div className="organic-page" data-testid="roadmap-page">
    <section className="organic-section"><p className="organic-badge">Flexible execution guide</p><div className="mt-3 flex flex-wrap items-end justify-between gap-4"><div><h1 className="font-display text-4xl font-bold theme-text">{roadmap.title}</h1><p className="mt-2 max-w-3xl theme-muted">{roadmap.summary}</p></div><div className="flex gap-2"><button className="organic-button-secondary" onClick={() => void add()}>Add Action</button><button data-testid="roadmap-recalibrate" className="organic-button" onClick={() => void openRecalibration()}>Recalibrate</button></div></div><div className="mt-5 max-w-xl"><div className="flex justify-between text-sm theme-muted"><span>Roadmap progress</span><span>{roadmap.progress.completion_percentage}%</span></div><progress className="mt-2 h-3 w-full" value={roadmap.progress.completion_percentage} max="100" /></div>{message && <p role="status" className="mt-3 text-sm text-[color:var(--teal)]">{message}</p>}{error && <p role="alert" className="mt-3 text-sm font-semibold text-red-700">{error}</p>}</section>
    <nav className="organic-section flex flex-wrap gap-2" aria-label="Roadmap sections">{Object.entries(labels).map(([id,label]) => <button key={id} onClick={() => setTab(id as Tab)} className={tab === id ? "organic-button" : "organic-button-secondary"}>{label}</button>)}<Link className="organic-button-secondary" to={`/recommendations/${profileId}`}>Recommendations</Link></nav>
    {tab === "overview" && <div className="grid gap-5 lg:grid-cols-[1.4fr_.8fr]"><section className="glass-card p-5"><h2 className="font-display text-2xl font-bold theme-text">Current focus</h2><div className="mt-4 space-y-3">{roadmap.horizons.seven_days.slice(0,3).map(actionCard)}{!roadmap.horizons.seven_days.length && <p className="theme-muted">Add your first action or bring in a recommendation.</p>}</div></section><aside className="glass-card p-5"><h2 className="font-display text-xl font-bold theme-text">At a glance</h2><p className="mt-3 theme-muted">{roadmap.progress.completed_actions} completed · {roadmap.progress.in_progress_actions} active · {roadmap.progress.blocked_actions} blocked</p></aside></div>}
    {tab in roadmap.horizons && <section className="glass-card p-5"><h2 className="font-display text-2xl font-bold theme-text">{labels[tab]}</h2><div className="mt-4 space-y-3">{current.map(actionCard)}</div></section>}
    {tab === "checkins" && <section className="glass-card max-w-3xl p-5"><h2 className="font-display text-2xl font-bold theme-text">Quick check-in</h2><form className="mt-4 grid gap-3" onSubmit={submitCheckIn}><label>Energy (1–5)<input required name="energy" type="number" min="1" max="5" className="ml-2 rounded border p-1" /></label><label>Confidence (1–5)<input required name="confidence" type="number" min="1" max="5" className="ml-2 rounded border p-1" /></label><label>Progress (1–5)<input required name="progress" type="number" min="1" max="5" className="ml-2 rounded border p-1" /></label><textarea name="worked" className="rounded border p-2" placeholder="What worked well?" /><textarea name="blocker" className="rounded border p-2" placeholder="What blocked you?" /><textarea name="changed" className="rounded border p-2" placeholder="What changed?" /><button data-testid="roadmap-checkin-submit" className="organic-button w-fit">Save check-in</button></form><div className="mt-6 space-y-3">{checkins.map(item => <p key={item.id} className="rounded-xl border p-3 text-sm theme-muted">{new Date(item.created_at).toLocaleDateString()} · energy {item.energy_level ?? "—"} · {item.main_blocker || item.what_worked || "No note"}</p>)}</div></section>}
    {tab === "history" && <section className="glass-card p-5" data-testid="roadmap-history"><h2 className="font-display text-2xl font-bold theme-text">Roadmap history</h2>{versions.map(item => <p key={item.version_number} className="mt-3 rounded-xl border p-3 theme-muted">Version {item.version_number} · {new Date(item.created_at).toLocaleDateString()} — {item.reason}</p>)}{events.map(item => <p key={item.id} data-testid="roadmap-history-event" className="mt-3 rounded-xl border p-3 theme-muted">{eventLabel(item)}{typeof item.metadata?.title === "string" ? ` — ${item.metadata.title}` : ""}</p>)}</section>}
    {proposal && <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4"><section className="max-h-[85vh] w-full max-w-2xl overflow-auto rounded-2xl bg-[color:var(--surface)] p-6 shadow-xl"><h2 className="font-display text-2xl font-bold theme-text">Recalibration proposal</h2><p className="mt-2 theme-muted">Version {proposal.current_version} → {proposal.proposed_version}. {proposal.summary}</p><div className="mt-4 space-y-2 text-sm theme-muted">{proposal.changes.map((change,index) => <label key={index} data-testid="recalibration-change" className="flex gap-2"><input type="checkbox" checked={selectedChanges.includes(index)} onChange={event => setSelectedChanges(currentChanges => event.target.checked ? [...currentChanges,index] : currentChanges.filter(value => value !== index))} /><span>{change.reason}</span></label>)}</div><p className="mt-4 text-xs theme-muted">{proposal.ethical_note}</p><div className="mt-5 flex gap-3"><button data-testid="recalibration-apply-selected" className="organic-button" disabled={!selectedChanges.length} onClick={() => void applySelectedRecalibration()}>Apply selected changes</button><button className="organic-button-secondary" onClick={() => setProposal(null)}>Keep current plan</button></div></section></div>}
  </div>;
}
