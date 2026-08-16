import { BarChart3, SlidersHorizontal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { createCareerComparison, getCareerMatches } from "../api/assessmentApi";
import type { CareerComparison, CareerMatch } from "../types/assessment";
import { useAppActions } from "../hooks/useAppActions";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";

const criteriaLabels: Record<string, string> = {
  skills_match: "Skills match",
  interest_alignment: "Interest alignment",
  work_values_alignment: "Work-values alignment",
  work_style_fit: "Work-style fit",
  ai_opportunity: "AI opportunity",
  training_required: "Training required",
  transition_difficulty: "Transition difficulty",
  time_horizon: "Time horizon",
  resource_requirements: "Cost or resources",
  employment_entrepreneurship: "Employment vs entrepreneurship",
  identified_risks: "Identified risks",
  user_priority: "User priority",
};

export function CareerComparePage() {
  const { profileId } = useParams();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const id = profileId || activeProfileId;
  const [matches, setMatches] = useState<CareerMatch[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [weights, setWeights] = useState<Record<string, number>>(() => Object.fromEntries(Object.keys(criteriaLabels).map((key) => [key, 1])));
  const [comparison, setComparison] = useState<CareerComparison | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    setActiveProfileId(id);
    getCareerMatches(id).then(setMatches).catch(() => setError("Career options could not be loaded."));
  }, [id, setActiveProfileId]);

  const selectedMatches = useMemo(() => matches.filter((match) => selected.includes(match.id)), [matches, selected]);

  async function compare() {
    if (!selected.length) return;
    if (!id) return;
    const created = await createCareerComparison(id, selected, weights, { note: "User adjusted comparison weights only." });
    setComparison(created);
  }

  if (error) return <div className="organic-section text-red-700">{error}</div>;
  if (!id) return <ProfileRequiredState title="Create your profile before comparing career directions." />;

  return (
    <div className="organic-page">
      <section className="organic-section">
        <p className="organic-badge">Career Comparison</p>
        <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Compare up to three career directions.</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">
          Adjusting criteria changes only this decision matrix. It does not silently rewrite your core assessment scores.
        </p>
        <Link className="organic-button-secondary mt-6" to={`/workspace/${id}/career-compatibility`}>Back to Career Compatibility Map</Link>
      </section>

      <div className="grid gap-5 xl:grid-cols-[1fr_22rem]">
        <section className="glass-card p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Career directions</h2>
          <div className="mt-4 grid gap-3">
            {matches.map((match) => (
              <label key={match.id} className="flex cursor-pointer items-start gap-3 rounded-2xl border border-[color:var(--border-soft)] p-4">
                <input
                  className="mt-1 h-5 w-5 accent-[color:var(--color-accent-action)]"
                  type="checkbox"
                  checked={selected.includes(match.id)}
                  onChange={() => setSelected((current) => current.includes(match.id) ? current.filter((item) => item !== match.id) : current.length < 3 ? [...current, match.id] : current)}
                />
                <span>
                  <b className="theme-text">{match.title}</b>
                  <span className="mt-1 block text-sm theme-muted">{match.alignment_label} - {match.transition_difficulty} - {match.time_horizon}</span>
                </span>
              </label>
            ))}
          </div>
        </section>

        <aside className="glass-card h-fit p-5">
          <h2 className="flex items-center gap-2 font-display text-2xl font-semibold theme-text"><SlidersHorizontal size={20} /> Criteria weights</h2>
          <div className="mt-4 space-y-4">
            {Object.entries(criteriaLabels).map(([key, label]) => (
              <label key={key} className="block text-xs font-bold theme-text">
                <span className="flex justify-between gap-3"><span>{label}</span><span>{weights[key].toFixed(1)}</span></span>
                <input className="organic-range-action mt-2 w-full" type="range" min="0" max="2" step="0.25" value={weights[key]} onChange={(event) => setWeights((current) => ({ ...current, [key]: Number(event.target.value) }))} />
              </label>
            ))}
          </div>
          <button type="button" className="organic-button mt-5 w-full" disabled={!selected.length} onClick={() => void compare()}>
            <BarChart3 size={16} /> Create Matrix
          </button>
        </aside>
      </div>

      {comparison ? (
        <section className="glass-card p-5">
          <h2 className="font-display text-3xl font-semibold theme-text">Decision matrix</h2>
          <div className="mt-5 grid gap-4 lg:grid-cols-3">
            {comparison.matrix.items.map((item) => (
              <article key={item.match_id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                <h3 className="font-display text-2xl font-semibold theme-text">{item.title}</h3>
                <p className="mt-2 text-sm font-bold text-[color:var(--color-accent-action-muted)]">{item.alignment_label}</p>
                <h4 className="mt-4 text-sm font-bold theme-text">Strengths</h4>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">{item.strengths.map((value) => <li key={value}>{value}</li>)}</ul>
                <h4 className="mt-4 text-sm font-bold theme-text">Challenges</h4>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">{item.challenges.map((value) => <li key={value}>{value}</li>)}</ul>
                <h4 className="mt-4 text-sm font-bold theme-text">Next experiment</h4>
                <p className="mt-2 text-sm theme-muted">{item.next_experiment}</p>
                <h4 className="mt-4 text-sm font-bold theme-text">Evidence before deciding</h4>
                <p className="mt-2 text-sm theme-muted">{item.evidence_required.join(", ")}</p>
              </article>
            ))}
          </div>
        </section>
      ) : selectedMatches.length ? (
        <section className="glass-card p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Selected directions</h2>
          <div className="mt-3 flex flex-wrap gap-2">{selectedMatches.map((match) => <span key={match.id} className="organic-chip">{match.title}</span>)}</div>
        </section>
      ) : null}
    </div>
  );
}
