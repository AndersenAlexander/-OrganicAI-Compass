import { AlertTriangle, BookOpenCheck, ExternalLink, GitCompare, RefreshCw, SlidersHorizontal, Target } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getAssessmentResults, getCareerMatches, saveCareerMatch } from "../api/assessmentApi";
import {
  createSkillGapAnalysis,
  generateLearningRecommendations,
  getLearningPreferences,
  getLearningRecommendations,
  getSkillGapAnalysis,
} from "../api/learningApi";
import { useAppActions } from "../hooks/useAppActions";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";
import type { AssessmentResults, CareerMatch } from "../types/assessment";
import type { LearningPreferences, LearningRecommendationRun, SkillGapAnalysis } from "../types/learning";

type SectionErrors = {
  skillGap?: string;
  recommendations?: string;
};

type EndpointDiagnostic = {
  endpoint: string;
  method: "GET" | "POST";
  essential: boolean;
  status: "fulfilled" | "rejected";
  httpStatus?: number;
  keys?: string[];
  count?: number;
  error?: string;
};

function formatHours(value?: number | null) {
  return value ? `${value} h/week` : "Not provided";
}

function asArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function errorStatus(error: unknown) {
  if (error && typeof error === "object" && "response" in error) {
    const response = (error as { response?: { status?: number } }).response;
    return response?.status;
  }
  return undefined;
}

function errorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  if (error && typeof error === "object" && "message" in error) return String((error as { message?: unknown }).message);
  return "Request failed";
}

function fulfilledDiagnostic(endpoint: string, value: unknown, essential: boolean): EndpointDiagnostic {
  const keys = value && typeof value === "object" && !Array.isArray(value) ? Object.keys(value).slice(0, 12) : undefined;
  const count = Array.isArray(value) ? value.length : undefined;
  return { endpoint, method: "GET", essential, status: "fulfilled", keys, count };
}

function rejectedDiagnostic(endpoint: string, reason: unknown, essential: boolean): EndpointDiagnostic {
  return { endpoint, method: "GET", essential, status: "rejected", httpStatus: errorStatus(reason), error: errorMessage(reason) };
}

function providerLine(item: Record<string, string>, index: number) {
  const provider = item.provider || item.provider_name || `provider_${index + 1}`;
  const status = item.status || "unknown";
  return `${provider}: ${status}`;
}

function safeStatus(value?: string | null) {
  return (value || "not_started").replace(/_/g, " ");
}

function resourceUrl(value?: string | null) {
  return value || "#";
}

export function LearningPage() {
  const { profileId } = useParams();
  const navigate = useNavigate();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const id = profileId || activeProfileId;
  const [results, setResults] = useState<AssessmentResults | null>(null);
  const [matches, setMatches] = useState<CareerMatch[]>([]);
  const [preferences, setPreferences] = useState<LearningPreferences | null>(null);
  const [gapAnalysis, setGapAnalysis] = useState<SkillGapAnalysis | null>(null);
  const [recommendationRun, setRecommendationRun] = useState<LearningRecommendationRun | null>(null);
  const [selectedMatchId, setSelectedMatchId] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    setSectionErrors({});

    const endpoints = {
      assessment: `/api/v1/profiles/${id}/assessment-results`,
      careerMatches: `/api/v1/profiles/${id}/career-matches`,
      preferences: `/api/v1/profiles/${id}/learning-preferences`,
      skillGap: `/api/v1/profiles/${id}/skill-gap-analysis`,
      recommendations: `/api/v1/profiles/${id}/learning-recommendations`,
    };

    const [assessmentResult, careerMatchesResult, preferencesResult, skillGapResult, recommendationsResult] = await Promise.allSettled([
      getAssessmentResults(id),
      getCareerMatches(id),
      getLearningPreferences(id),
      getSkillGapAnalysis(id),
      getLearningRecommendations(id),
    ]);

    const diagnostics: EndpointDiagnostic[] = [
      assessmentResult.status === "fulfilled"
        ? fulfilledDiagnostic(endpoints.assessment, assessmentResult.value, true)
        : rejectedDiagnostic(endpoints.assessment, assessmentResult.reason, true),
      careerMatchesResult.status === "fulfilled"
        ? fulfilledDiagnostic(endpoints.careerMatches, careerMatchesResult.value, true)
        : rejectedDiagnostic(endpoints.careerMatches, careerMatchesResult.reason, true),
      preferencesResult.status === "fulfilled"
        ? fulfilledDiagnostic(endpoints.preferences, preferencesResult.value, true)
        : rejectedDiagnostic(endpoints.preferences, preferencesResult.reason, true),
      skillGapResult.status === "fulfilled"
        ? fulfilledDiagnostic(endpoints.skillGap, skillGapResult.value, false)
        : rejectedDiagnostic(endpoints.skillGap, skillGapResult.reason, false),
      recommendationsResult.status === "fulfilled"
        ? fulfilledDiagnostic(endpoints.recommendations, recommendationsResult.value, false)
        : rejectedDiagnostic(endpoints.recommendations, recommendationsResult.reason, false),
    ];

    if (import.meta.env.DEV) {
      console.debug("LearningPage initial load", {
        profile_id: id,
        endpoints: diagnostics,
        recommendation_status: recommendationsResult.status === "fulfilled" ? recommendationsResult.value.status : "unavailable",
        recommendation_count: recommendationsResult.status === "fulfilled" ? recommendationsResult.value.recommendations.length : 0,
        skill_gap_count: skillGapResult.status === "fulfilled" ? asArray(skillGapResult.value.items).length : 0,
        objective_count: skillGapResult.status === "fulfilled" ? asArray(skillGapResult.value.objectives).length : 0,
        provider_status: recommendationsResult.status === "fulfilled" ? asArray(recommendationsResult.value.provider_status).map(providerLine) : [],
      });
    }

    if (assessmentResult.status === "rejected" || careerMatchesResult.status === "rejected" || preferencesResult.status === "rejected") {
      setError("Learning Path data could not be loaded.");
      setLoading(false);
      return;
    }

    const careerMatches = careerMatchesResult.value;
    setResults(assessmentResult.value);
    setMatches(careerMatches);
    setPreferences(preferencesResult.value);

    if (skillGapResult.status === "fulfilled") {
      setGapAnalysis(skillGapResult.value);
    } else {
      setGapAnalysis({ status: "not_started", items: [], objectives: [], practical_projects: [] });
      setSectionErrors((current) => ({ ...current, skillGap: "Skill-gap snapshot could not be loaded." }));
    }

    if (recommendationsResult.status === "fulfilled") {
      setRecommendationRun(recommendationsResult.value);
    } else {
      setRecommendationRun(null);
      setSectionErrors((current) => ({ ...current, recommendations: "Learning recommendations could not be loaded." }));
    }

    const saved = careerMatches.find((match) => ["saved", "roadmap_draft_created", "learning_selected"].includes(match.status));
    setSelectedMatchId((current) => current || saved?.id || careerMatches.find((match) => match.category !== "augment_current_profession")?.id || careerMatches[0]?.id || "");
    setLoading(false);
  }, [id]);

  async function retrySkillGap() {
    setSectionErrors((current) => ({ ...current, skillGap: undefined }));
    try {
      setGapAnalysis(await getSkillGapAnalysis(id));
    } catch {
      setSectionErrors((current) => ({ ...current, skillGap: "Skill-gap snapshot could not be loaded." }));
    }
  }

  async function retryRecommendations() {
    if (!id) return;
    setSectionErrors((current) => ({ ...current, recommendations: undefined }));
    try {
      setRecommendationRun(await getLearningRecommendations(id));
    } catch {
      setSectionErrors((current) => ({ ...current, recommendations: "Learning recommendations could not be loaded." }));
    }
  }

  useEffect(() => {
    if (!id) {
      setLoading(false);
      return;
    }
    setActiveProfileId(id);
    void load();
  }, [id, load, setActiveProfileId]);

  const selectedMatch = useMemo(() => matches.find((match) => match.id === selectedMatchId), [matches, selectedMatchId]);
  const savedMatch = useMemo(() => matches.find((match) => ["saved", "roadmap_draft_created", "learning_selected"].includes(match.status)), [matches]);
  const recommendations = recommendationRun?.recommendations ?? [];
  const providerStatus = recommendationRun?.provider_status ?? [];
  const hardFilters = recommendationRun?.hard_filters ?? [];
  const uniqueRecommendedResources = useMemo(() => new Set(recommendations.map((item) => item.learning_resource_id || item.resource.id)), [recommendations]);
  const uniqueExcludedResources = useMemo(() => new Set(hardFilters.map((item) => item.resource_id).filter(Boolean)), [hardFilters]);
  const evaluatedResources = useMemo(() => new Set([...uniqueRecommendedResources, ...uniqueExcludedResources]).size, [uniqueRecommendedResources, uniqueExcludedResources]);
  const topRecommendations = recommendations.slice(0, 3);
  const skillGaps = asArray(gapAnalysis?.items);
  const objectives = asArray(gapAnalysis?.objectives);

  async function generate() {
    if (!id) return;
    if (!selectedMatchId) {
      setStatus("Select or save a career direction before generating a personalised learning path.");
      return;
    }
    setStatus("Generating personalised learning recommendations...");
    await saveCareerMatch(selectedMatchId, { feedback_text: "Selected for learning recommendation generation.", user_priority: 5 });
    await createSkillGapAnalysis(id, selectedMatchId);
    await generateLearningRecommendations(id, selectedMatchId);
    navigate(`/workspace/${id}/learning/recommendations?match=${encodeURIComponent(selectedMatchId)}`);
  }

  if (!id) return <ProfileRequiredState title="Create your profile before opening Learning Path." />;
  if (error) {
    return (
      <section className="organic-section">
        <p className="organic-badge">Personalised Learning Path</p>
        <h1 className="mt-4 font-display text-4xl font-semibold theme-text">{error}</h1>
        <p className="mt-3 max-w-2xl theme-muted">A required profile, assessment, career direction, or learning preference request failed. Recommendation provider status and hard-filter audit records are not treated as page failures.</p>
        <button type="button" className="organic-button mt-6" disabled={loading} onClick={() => void load()}>
          <RefreshCw size={16} /> Retry
        </button>
      </section>
    );
  }
  if (loading || !results || !preferences) return <div className="organic-section theme-muted">Loading Learning Path...</div>;
  if (results.status !== "completed") {
    return (
      <section className="organic-section">
        <p className="organic-badge">Personalised Learning Path</p>
        <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Complete the assessment first.</h1>
        <p className="mt-3 max-w-2xl theme-muted">Learning recommendations need completed or usable assessment results, a selected career direction, skills, and preferences.</p>
        <Link className="organic-button mt-6" to={`/workspace/${id}/assessment`}>Open Career Assessment</Link>
      </section>
    );
  }

  const secondaryLanguages = asArray(preferences.acceptable_secondary_languages);
  const contentFormats = asArray(preferences.preferred_content_formats);

  return (
    <div className="organic-page">
      <section className="organic-section">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="organic-badge">Personalised Learning Path</p>
            <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Generate learning recommendations from a selected direction.</h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">
              Recommendations are based on stored resources, skill gaps, and deterministic ranking. Course names, prices, URLs, and providers are not invented by an LLM.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link className="organic-button-secondary" to={`/workspace/${id}/learning/preferences`}><SlidersHorizontal size={16} /> Preferences</Link>
            <Link className="organic-button-secondary" to={`/workspace/${id}/learning/progress`}><BookOpenCheck size={16} /> Progress</Link>
          </div>
        </div>
        {status ? <p className="mt-4 text-sm font-semibold text-[color:var(--color-accent-action-muted)]" role="status">{status}</p> : null}
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]">
        <section className="glass-card p-5">
          <h2 className="flex items-center gap-2 font-display text-2xl font-semibold theme-text"><Target size={20} /> Selected Career Direction</h2>
          {!matches.length ? (
            <div className="mt-4 rounded-2xl border border-[color:var(--border-soft)] p-4">
              <p className="font-semibold theme-text">Select or save a career direction before generating a personalised learning path.</p>
              <Link className="organic-button-secondary mt-4" to={`/workspace/${id}/career-compatibility`}>Open Career Compatibility</Link>
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              {matches.map((match) => (
                <label key={match.id} className="flex cursor-pointer items-start gap-3 rounded-2xl border border-[color:var(--border-soft)] p-4">
                  <input
                    className="mt-1 h-5 w-5 accent-[color:var(--color-accent-action)]"
                    type="radio"
                    checked={selectedMatchId === match.id}
                    onChange={() => setSelectedMatchId(match.id)}
                  />
                  <span>
                    <b className="theme-text">{match.title}</b>
                    <span className="mt-1 block text-sm theme-muted">{match.alignment_label} - {match.transition_difficulty} - {match.time_horizon}</span>
                    <span className="mt-1 block text-xs theme-muted">Status: {safeStatus(match.status)}</span>
                  </span>
                </label>
              ))}
            </div>
          )}
        </section>

        <aside className="glass-card h-fit p-5">
          <h2 className="font-display text-2xl font-semibold theme-text">Learning Context</h2>
          <dl className="mt-4 space-y-3 text-sm theme-muted">
            <div><dt className="font-bold theme-text">Preferred language</dt><dd>{(preferences.preferred_language || "en").toUpperCase()} {secondaryLanguages.length ? `+ ${secondaryLanguages.join(", ")}` : ""}</dd></div>
            <div><dt className="font-bold theme-text">Budget</dt><dd>{preferences.free_only ? "Free only" : preferences.max_budget_per_course != null ? `Up to ${preferences.max_budget_per_course}` : "Flexible or not provided"}</dd></div>
            <div><dt className="font-bold theme-text">Time</dt><dd>{formatHours(preferences.available_hours_per_week)}</dd></div>
            <div><dt className="font-bold theme-text">Formats</dt><dd>{contentFormats.length ? contentFormats.join(", ") : "Mixed"}</dd></div>
          </dl>
          <button type="button" className="organic-button mt-5 w-full" disabled={!selectedMatchId} onClick={() => void generate()}>
            Generate Learning Recommendations
          </button>
          <Link className="organic-button-secondary mt-3 w-full justify-center" to={`/workspace/${id}/learning/compare`}>
            <GitCompare size={16} /> Compare Learning Resources
          </Link>
        </aside>
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="glass-card p-5">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--color-accent-action-muted)]">Catalogue Summary</p>
          <h2 className="mt-2 font-display text-2xl font-semibold theme-text">{recommendations.length} recommendations available</h2>
          <p className="mt-2 text-sm theme-muted">{evaluatedResources || recommendations.length} resources evaluated, {uniqueExcludedResources.size} resources have hard-filter audit records.</p>
        </article>
        <article className="glass-card p-5">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--color-accent-action-muted)]">Provider Status</p>
          <h2 className="mt-2 font-display text-2xl font-semibold theme-text">{recommendationRun?.status === "ready" ? "Ready" : safeStatus(recommendationRun?.status)}</h2>
          <p className="mt-2 text-sm theme-muted">{providerStatus.length ? providerStatus.map(providerLine).join("; ") : "Curated catalogue status is not available yet."}</p>
        </article>
        <article className="glass-card p-5">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--color-accent-action-muted)]">Audit Detail</p>
          <h2 className="mt-2 font-display text-2xl font-semibold theme-text">{hardFilters.length} filter records</h2>
          <p className="mt-2 text-sm theme-muted">Detailed exclusions stay in traceability views and do not block the main page.</p>
        </article>
      </section>

      <section className="glass-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-2xl font-semibold theme-text">Latest Learning Recommendations</h2>
            <p className="mt-2 text-sm theme-muted">Ready recommendations are shown from the stored run. Disabled external providers and populated hard filters are audit state, not failures.</p>
          </div>
          <Link className="organic-button-secondary" to={`/workspace/${id}/learning/recommendations`}>Review All <ExternalLink size={16} /></Link>
        </div>
        {sectionErrors.recommendations ? (
          <div className="mt-5 rounded-2xl border border-[color:var(--border-soft)] p-5">
            <p className="flex items-center gap-2 font-semibold theme-text"><AlertTriangle size={18} /> {sectionErrors.recommendations}</p>
            <button type="button" className="organic-button-secondary mt-4" onClick={() => void retryRecommendations()}><RefreshCw size={16} /> Retry recommendations</button>
          </div>
        ) : topRecommendations.length ? (
          <div className="mt-5 grid gap-4 lg:grid-cols-3">
            {topRecommendations.map((item) => (
              <article key={item.id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--color-accent-action-muted)]">{item.alignment_label}</p>
                <h3 className="mt-2 font-display text-xl font-semibold theme-text">{item.resource.title}</h3>
                <p className="mt-2 text-sm theme-muted">{item.resource.provider_id} - {item.resource.resource_type_label} - {item.resource.level}</p>
                <p className="mt-3 text-sm theme-muted">{item.skill_gap?.skill_label || "General learning objective"}</p>
                <a className="mt-4 inline-flex items-center gap-2 text-sm font-bold text-[color:var(--teal)]" href={resourceUrl(item.resource.canonical_url)} target="_blank" rel="noreferrer">
                  Open provider <ExternalLink size={14} />
                </a>
              </article>
            ))}
          </div>
        ) : (
          <div className="mt-5 rounded-2xl border border-[color:var(--border-soft)] p-5">
            <h3 className="font-display text-xl font-semibold theme-text">No generated recommendations yet.</h3>
            <p className="mt-2 text-sm theme-muted">{recommendationRun?.message || "Select a career direction and generate recommendations from the curated catalogue."}</p>
          </div>
        )}
      </section>

      <section className="glass-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-2xl font-semibold theme-text">Current Skill-Gap Snapshot</h2>
            <p className="mt-2 text-sm theme-muted">{objectives.length} learning objectives available for the selected direction.</p>
          </div>
          {sectionErrors.skillGap ? <button type="button" className="organic-button-secondary" onClick={() => void retrySkillGap()}><RefreshCw size={16} /> Retry skill gap</button> : null}
        </div>
        {sectionErrors.skillGap ? (
          <p className="mt-3 flex items-center gap-2 text-sm theme-muted"><AlertTriangle size={18} /> {sectionErrors.skillGap}</p>
        ) : gapAnalysis?.status === "ready" && skillGaps.length ? (
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {skillGaps.slice(0, 6).map((gap) => (
              <article key={gap.id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--color-accent-action-muted)]">{gap.priority_label || "Priority"}</p>
                <h3 className="mt-1 font-display text-xl font-semibold theme-text">{gap.skill_label}</h3>
                <p className="mt-2 text-sm theme-muted">{gap.current_level_label} to {gap.target_level_label} - {gap.status}</p>
                <p className="mt-2 text-xs theme-muted">{safeStatus(gap.evidence_level)} evidence</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm theme-muted">{savedMatch || selectedMatch ? "Generate recommendations to calculate the latest skill gaps." : "Select or save a career direction before generating a personalised learning path."}</p>
        )}
      </section>
    </div>
  );
}
