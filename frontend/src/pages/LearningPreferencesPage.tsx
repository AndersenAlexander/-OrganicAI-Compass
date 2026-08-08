import { Save, SlidersHorizontal } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getLearningPreferences, getLearningProviders, updateLearningPreferences } from "../api/learningApi";
import { useAppActions } from "../hooks/useAppActions";
import type { LearningPreferences, LearningProvider } from "../types/learning";

const formatOptions = ["Video", "Text", "Interactive", "Project-based", "Instructor-led", "Mixed"];

function toggle(values: string[], value: string) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

export function LearningPreferencesPage() {
  const { profileId } = useParams();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const id = profileId || activeProfileId || "demo-profile";
  const [preferences, setPreferences] = useState<LearningPreferences | null>(null);
  const [providers, setProviders] = useState<LearningProvider[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setActiveProfileId(id);
    Promise.all([getLearningPreferences(id), getLearningProviders()])
      .then(([prefs, providerRows]) => {
        setPreferences(prefs);
        setProviders(providerRows);
      })
      .catch(() => setError("Learning preferences could not be loaded."));
  }, [id, setActiveProfileId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!preferences) return;
    const saved = await updateLearningPreferences(id, preferences);
    setPreferences(saved);
    setMessage("Learning preferences saved. Future recommendation runs will use these constraints.");
  }

  if (error) return <div className="organic-section text-red-700">{error}</div>;
  if (!preferences) return <div className="organic-section theme-muted">Loading learning preferences...</div>;

  return (
    <div className="organic-page">
      <section className="organic-section">
        <p className="organic-badge">Learning Preferences</p>
        <h1 className="mt-4 flex items-center gap-3 font-display text-4xl font-semibold theme-text"><SlidersHorizontal size={28} /> Tune hard filters before ranking.</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">Hard constraints are applied before resource ranking. Feedback can recalibrate future runs without silently rewriting your profile.</p>
        <Link className="organic-button-secondary mt-6" to={`/workspace/${id}/learning`}>Back to Learning Path</Link>
        {message ? <p className="mt-4 text-sm font-semibold text-[color:var(--teal)]" role="status">{message}</p> : null}
      </section>

      <form className="grid gap-5 xl:grid-cols-[1fr_.8fr]" onSubmit={submit}>
        <section className="glass-card p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Language, Budget, and Time</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label className="text-sm font-bold theme-text">Preferred language
              <input className="mt-2 w-full rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" value={preferences.preferred_language} onChange={(event) => setPreferences({ ...preferences, preferred_language: event.target.value })} />
            </label>
            <label className="text-sm font-bold theme-text">Secondary languages
              <input className="mt-2 w-full rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" value={preferences.acceptable_secondary_languages.join(", ")} onChange={(event) => setPreferences({ ...preferences, acceptable_secondary_languages: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} />
            </label>
            <label className="flex items-center gap-3 rounded-2xl border border-[color:var(--border-soft)] p-4 text-sm font-bold theme-text">
              <input className="h-5 w-5 accent-[color:var(--color-accent-action)]" type="checkbox" checked={preferences.free_only} onChange={(event) => setPreferences({ ...preferences, free_only: event.target.checked })} />
              Free-only resources
            </label>
            <label className="text-sm font-bold theme-text">Maximum budget per course
              <input className="mt-2 w-full rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" type="number" min="0" value={preferences.max_budget_per_course ?? ""} onChange={(event) => setPreferences({ ...preferences, max_budget_per_course: event.target.value ? Number(event.target.value) : null })} />
            </label>
            <label className="text-sm font-bold theme-text">Monthly learning budget
              <input className="mt-2 w-full rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" type="number" min="0" value={preferences.monthly_learning_budget ?? ""} onChange={(event) => setPreferences({ ...preferences, monthly_learning_budget: event.target.value ? Number(event.target.value) : null })} />
            </label>
            <label className="text-sm font-bold theme-text">Available hours per week
              <input className="mt-2 w-full rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" type="number" min="0" max="80" value={preferences.available_hours_per_week} onChange={(event) => setPreferences({ ...preferences, available_hours_per_week: Number(event.target.value) })} />
            </label>
            <label className="text-sm font-bold theme-text">Preferred session length
              <input className="mt-2 w-full rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" type="number" min="5" value={preferences.preferred_session_length_minutes ?? ""} onChange={(event) => setPreferences({ ...preferences, preferred_session_length_minutes: event.target.value ? Number(event.target.value) : null })} />
            </label>
            <label className="text-sm font-bold theme-text">Strict duration limit
              <input className="mt-2 w-full rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" type="number" min="10" value={preferences.strict_duration_limit_minutes ?? ""} onChange={(event) => setPreferences({ ...preferences, strict_duration_limit_minutes: event.target.value ? Number(event.target.value) : null })} />
            </label>
          </div>
        </section>

        <aside className="glass-card h-fit p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Format and Access</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {formatOptions.map((option) => (
              <button key={option} type="button" className={preferences.preferred_content_formats.includes(option) ? "organic-button" : "organic-button-secondary"} onClick={() => setPreferences({ ...preferences, preferred_content_formats: toggle(preferences.preferred_content_formats, option) })}>
                {option}
              </button>
            ))}
          </div>
          <div className="mt-5 space-y-3">
            {[
              ["subtitles_required", "Subtitles required"],
              ["mobile_friendly", "Prefer mobile-friendly resources"],
              ["offline_availability", "Prefer offline availability"],
            ].map(([key, label]) => (
              <label key={key} className="flex items-center gap-3 text-sm font-bold theme-text">
                <input className="h-5 w-5 accent-[color:var(--color-accent-action)]" type="checkbox" checked={Boolean(preferences[key as keyof LearningPreferences])} onChange={(event) => setPreferences({ ...preferences, [key]: event.target.checked })} />
                {label}
              </label>
            ))}
          </div>
          <label className="mt-5 block text-sm font-bold theme-text">Accessibility preferences
            <textarea className="mt-2 min-h-24 w-full rounded-xl border border-[color:var(--border-soft)] bg-transparent p-3 theme-muted" value={preferences.accessibility_preferences.join("\n")} onChange={(event) => setPreferences({ ...preferences, accessibility_preferences: event.target.value.split("\n").map((item) => item.trim()).filter(Boolean) })} />
          </label>
        </aside>

        <section className="glass-card p-5 xl:col-span-2">
          <h2 className="font-display text-2xl font-semibold theme-text">Provider Exclusions</h2>
          <p className="mt-2 text-sm theme-muted">External API search is optional; the curated catalogue remains available when provider APIs are disabled.</p>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {providers.map((provider) => (
              <label key={provider.id} className="flex items-start gap-3 rounded-2xl border border-[color:var(--border-soft)] p-4 text-sm theme-muted">
                <input
                  className="mt-1 h-5 w-5 accent-[color:var(--color-accent-action)]"
                  type="checkbox"
                  checked={preferences.provider_exclusions.includes(provider.provider_name)}
                  onChange={() => setPreferences({ ...preferences, provider_exclusions: toggle(preferences.provider_exclusions, provider.provider_name) })}
                />
                <span><b className="theme-text">{provider.display_name}</b><span className="block text-xs">{provider.api_enabled ? "API enabled" : "Curated/disabled API"}</span></span>
              </label>
            ))}
          </div>
          <button className="organic-button mt-5" type="submit"><Save size={16} /> Save Preferences</button>
        </section>
      </form>
    </div>
  );
}
