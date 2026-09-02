import { ArrowLeft, ArrowRight, CheckCircle2, Clock3, Save, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  completeAssessmentSession,
  createAssessmentSession,
  getCurrentAssessmentSession,
  saveAssessmentResponses,
} from "../api/assessmentApi";
import type { AssessmentDefinition, AssessmentItemDefinition, AssessmentMode, AssessmentPrefill, AssessmentSession } from "../types/assessment";
import { useAppActions } from "../hooks/useAppActions";
import { prefilledResponseCount, prefillStatusCopy } from "../lib/humanDiscoveryJourney";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";

type ResponseMap = Record<string, unknown>;

function routeMode(pathname: string): AssessmentMode | null {
  if (pathname.endsWith("/quick")) return "quick";
  if (pathname.endsWith("/complete")) return "complete";
  if (pathname.endsWith("/evidence")) return "evidence_based";
  return null;
}

function normaliseValue(value: unknown) {
  if (typeof value === "number") return value;
  if (typeof value === "string" && value.trim() && !Number.isNaN(Number(value))) return Number(value);
  return value;
}

function skillValue(value: unknown) {
  if (value && typeof value === "object") return value as { level?: string | number; evidence_status?: string; note?: string };
  return { level: "no_experience", evidence_status: "self_reported", note: "" };
}

function itemValueFromSession(response: { value: unknown; payload?: Record<string, unknown>; text_value?: string | null; option_value?: string | null; numeric_value?: number | null }) {
  if (response.payload && Object.keys(response.payload).length) return response.payload;
  if (response.text_value != null) return response.text_value;
  if (response.option_value != null) return response.option_value;
  if (response.numeric_value != null) return response.numeric_value;
  return response.value;
}

function responseForItem(item: AssessmentItemDefinition, value: unknown) {
  return {
    item_id: item.id,
    module_id: item.module_id,
    response_type: item.item_type,
    value,
  };
}

function itemIsAnswered(item: AssessmentItemDefinition, responses: ResponseMap) {
  const value = responses[item.id];
  if (item.item_type === "skill_level") return Boolean(skillValue(value).level);
  if (typeof value === "number") return value > 0;
  if (typeof value === "string") return value.trim().length > 0;
  if (value && typeof value === "object") return true;
  return false;
}

function LikertButtons({
  item,
  definition,
  value,
  onChange,
}: {
  item: AssessmentItemDefinition;
  definition: AssessmentDefinition;
  value: unknown;
  onChange: (value: number) => void;
}) {
  const selected = Number(value || 0);
  return (
    <div className="grid grid-cols-5 gap-2" role="radiogroup" aria-label={item.prompt}>
      {definition.likert_options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={selected === option.value}
          title={option.label}
          onClick={() => onChange(option.value)}
          className={selected === option.value ? "organic-action-selected rounded-2xl px-2 py-3 text-sm font-bold" : "organic-chip justify-center rounded-2xl px-2 py-3 text-sm"}
        >
          {option.value}
        </button>
      ))}
    </div>
  );
}

function AssessmentItem({
  item,
  definition,
  value,
  onChange,
  prefillNote,
}: {
  item: AssessmentItemDefinition;
  definition: AssessmentDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
  prefillNote?: string;
}) {
  const options = Array.isArray(item.metadata.options) ? (item.metadata.options as string[]) : [];
  const skill = skillValue(value);
  return (
    <article className="rounded-2xl border border-[color:var(--border-soft)] bg-[color:var(--color-surface-secondary)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold theme-text">{item.prompt}</h3>
          {item.reverse_scored ? <p className="mt-1 text-xs theme-muted">Reverse scored internally for balance.</p> : null}
          {prefillNote ? <p className="mt-1 text-xs font-semibold text-[color:var(--color-accent-action-muted)]">Previously provided: confirm or edit. {prefillNote}</p> : null}
        </div>
        {item.required ? <span className="organic-chip px-3 py-1 text-xs">Required</span> : <span className="text-xs theme-muted">Optional</span>}
      </div>

      <div className="mt-4">
        {item.item_type === "likert" || item.item_type === "value_rating" ? (
          <div className="space-y-3">
            <LikertButtons item={item} definition={definition} value={normaliseValue(value)} onChange={onChange} />
            <div className="flex justify-between text-[11px] theme-muted">
              <span>Strongly disagree</span>
              <span>Strongly agree</span>
            </div>
          </div>
        ) : null}

        {item.item_type === "skill_level" ? (
          <div className="grid gap-3 sm:grid-cols-[1fr_1fr]">
            <label className="text-xs font-semibold theme-text">
              Skill level
              <select className="organic-input mt-2" value={String(skill.level ?? "no_experience")} onChange={(event) => onChange({ ...skill, level: event.target.value })}>
                {definition.skill_levels.map((level) => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs font-semibold theme-text">
              Evidence status
              <select className="organic-input mt-2" value={String(skill.evidence_status ?? "self_reported")} onChange={(event) => onChange({ ...skill, evidence_status: event.target.value })}>
                {definition.evidence_statuses.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        ) : null}

        {item.item_type === "single_select" ? (
          <select className="organic-input" value={String(value ?? "")} onChange={(event) => onChange(event.target.value)}>
            <option value="">Select an option</option>
            {options.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        ) : null}

        {item.item_type === "text" ? (
          <input className="organic-input" value={String(value ?? "")} onChange={(event) => onChange(event.target.value)} />
        ) : null}

        {item.item_type === "long_text" ? (
          <textarea className="organic-input min-h-28 resize-y" value={String(value ?? "")} onChange={(event) => onChange(event.target.value)} />
        ) : null}
      </div>
    </article>
  );
}

export function AssessmentPage() {
  const params = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const profileId = params.profileId || activeProfileId;
  const preferredMode = routeMode(location.pathname);
  const [definition, setDefinition] = useState<AssessmentDefinition | null>(null);
  const [session, setSession] = useState<AssessmentSession | null>(null);
  const [responses, setResponses] = useState<ResponseMap>({});
  const [prefill, setPrefill] = useState<AssessmentPrefill | null>(null);
  const [moduleIndex, setModuleIndex] = useState(0);
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!profileId || profileId === "undefined" || profileId === "null") {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setActiveProfileId(profileId);
    getCurrentAssessmentSession(profileId)
      .then((payload) => {
        if (cancelled) return;
        setDefinition(payload.definition);
        setSession(payload.session);
        setPrefill(payload.prefill ?? null);
        setConsent(Boolean(payload.session?.consent_accepted));
        const next: ResponseMap = { ...(payload.prefill?.responses ?? {}) };
        payload.session?.responses?.forEach((response) => {
          next[response.item_id] = itemValueFromSession(response);
        });
        setResponses(next);
      })
      .catch(() => {
        if (!cancelled) setError("The assessment module could not be loaded.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [profileId, setActiveProfileId]);

  const modules = useMemo(() => definition?.modules ?? [], [definition]);
  const currentModule = modules[moduleIndex];
  const currentItems = useMemo(() => (definition && currentModule ? definition.items.filter((item) => item.module_id === currentModule.id) : []), [definition, currentModule]);
  const answeredCount = useMemo(() => (definition ? definition.items.filter((item) => itemIsAnswered(item, responses)).length : 0), [definition, responses]);
  const progress = definition?.items.length ? Math.round((answeredCount / definition.items.length) * 100) : 0;
  const remaining = Math.max(0, modules.length - moduleIndex - 1);
  const prefillCount = prefilledResponseCount(prefill);

  async function start(mode: AssessmentMode) {
    if (!consent) {
      setError("Please accept the assessment purpose and limitation statement before starting.");
      return;
    }
    setError("");
    if (!profileId) return;
    const payload = await createAssessmentSession(profileId, mode, true);
    setDefinition(payload.definition);
    setSession(payload.session);
    setPrefill(payload.prefill ?? prefill);
    setResponses({ ...(payload.prefill?.responses ?? prefill?.responses ?? {}) });
    setModuleIndex(0);
    setStatus(`${payload.definition.modes.find((item) => item.id === mode)?.title ?? "Assessment"} started.`);
    navigate(`/workspace/${profileId}/assessment/${mode === "complete" ? "complete" : mode === "evidence_based" ? "evidence" : "quick"}`, { replace: true });
  }

  async function saveCurrent() {
    if (!session || !definition) return null;
    const payload = currentItems.filter((item) => itemIsAnswered(item, responses)).map((item) => responseForItem(item, responses[item.id]));
    const saved = await saveAssessmentResponses(session.id, payload);
    setSession(saved.session);
    setStatus("Saved. You can continue later.");
    return saved;
  }

  async function continueNext() {
    await saveCurrent();
    if (moduleIndex < modules.length - 1) setModuleIndex((current) => current + 1);
  }

  async function finish() {
    if (!session) return;
    await saveCurrent();
    const result = await completeAssessmentSession(session.id);
    if (result.status === "incomplete") {
      setError(`Please answer the required items before completing: ${(result.missing_required_items || []).join(", ")}`);
      return;
    }
    navigate(`/workspace/${profileId}/career-compatibility`);
  }

  if (loading) return <div className="organic-section theme-muted">Loading Human Potential & Career Assessment...</div>;
  if (!profileId) return <ProfileRequiredState title="Create your profile before assessment." message="Capability Assessment needs an owned profile. Complete Natural Discovery first, then return here to confirm capabilities and evidence." />;
  if (error && !definition) return <div className="organic-section text-red-700">{error}</div>;

  if (!definition || !session || session.status === "completed") {
    return (
      <div className="organic-page">
        <section className="organic-section">
          <p className="organic-badge">Human Potential & Career Assessment</p>
          <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Choose an assessment path.</h1>
          <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">
            Start from Natural Discovery, then confirm current capabilities, evidence, readiness, and constraints. Previously provided values can be reused without treating them as demonstrated evidence.
          </p>
          {prefillCount ? (
            <div className="mt-4 rounded-2xl border border-[color:var(--border-soft)] bg-[color:var(--color-surface-secondary)] p-4 text-sm theme-muted">
              {prefillStatusCopy(prefill)}
            </div>
          ) : null}
          <div className="mt-6 rounded-2xl border border-[color:var(--color-accent-action-border)] bg-[color:var(--color-accent-action-soft)] p-4 text-sm font-semibold text-[color:var(--color-accent-action-muted)]">
            {definition?.disclaimer ?? "This assessment supports self-reflection and career exploration. It is not a psychological diagnosis, employment decision, or guarantee of professional success."}
          </div>
          {session?.status === "completed" ? (
            <div className="mt-6 flex flex-wrap gap-3">
              <Link className="organic-button" to={`/workspace/${profileId}/career-compatibility`}>
                View Career Compatibility Map <ArrowRight size={16} />
              </Link>
              <button type="button" className="organic-button-secondary" onClick={() => void start("quick")}>
                Retake Quick Assessment
              </button>
            </div>
          ) : null}
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          {(definition?.modes ?? [
            { id: "quick", title: "Quick Assessment", estimated_minutes: "8-10", description: "Preliminary profile and broad career families." },
            { id: "complete", title: "Complete Assessment", estimated_minutes: "20-30", description: "Detailed profile, values, skills, career matches, and roadmap proposals." },
            { id: "evidence_based", title: "Evidence-Based Assessment", estimated_minutes: "30+", description: "Complete assessment plus structured manual evidence." },
          ]).map((mode) => (
            <article key={mode.id} className="glass-card flex flex-col justify-between p-6">
              <div>
                <p className="organic-chip px-3 py-1 text-xs">
                  <Clock3 size={14} /> {mode.estimated_minutes} min
                </p>
                <h2 className="mt-4 font-display text-2xl font-semibold theme-text">{mode.title}</h2>
                <p className="mt-3 text-sm leading-6 theme-muted">{mode.description}</p>
              </div>
              <button type="button" className="organic-button mt-6 w-full" onClick={() => void start(mode.id)}>
                Start {mode.title} <ArrowRight size={16} />
              </button>
            </article>
          ))}
        </section>

        <label className="glass-card flex items-start gap-3 p-5 text-sm theme-muted">
          <input className="mt-1 h-5 w-5 accent-[color:var(--color-accent-action)]" type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
          <span>
            I understand that this is self-reported decision support, not a diagnosis, hiring decision, or promise of career success. I can review, correct, export where supported, or delete the assessment data.
          </span>
        </label>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
      </div>
    );
  }

  return (
    <div className="organic-page">
      <section className="organic-section">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="organic-badge">Personality, Work Style & Career Fit</p>
            <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Human Potential & Career Assessment</h1>
            <p className="mt-3 max-w-3xl text-base leading-7 theme-muted">{definition.disclaimer}</p>
            {prefillCount ? (
              <p className="mt-2 max-w-3xl text-sm font-semibold text-[color:var(--color-accent-action-muted)]">
                Previously provided Natural Discovery values are shown for confirmation. Skill values remain self-reported until evidence is added.
              </p>
            ) : null}
          </div>
          <div className="rounded-2xl border border-[color:var(--border-soft)] p-4 text-sm theme-muted">
            <p className="font-bold theme-text">{progress}% answered</p>
            <p>{remaining} groups remaining</p>
          </div>
        </div>
        <span className="oa-progress mt-6" aria-label="Assessment progress">
          <i style={{ width: `${progress}%` }} />
        </span>
        {status ? <p className="mt-4 text-sm font-semibold text-[color:var(--teal)]" role="status">{status}</p> : null}
        {error ? <p className="mt-4 text-sm font-semibold text-red-700" role="alert">{error}</p> : null}
      </section>

      <div className="grid gap-5 lg:grid-cols-[18rem_1fr]">
        <aside className="glass-card h-fit p-4">
          <h2 className="text-sm font-bold theme-text">Assessment groups</h2>
          <div className="mt-4 grid gap-2">
            {modules.map((module, index) => {
              const moduleItems = definition.items.filter((item) => item.module_id === module.id);
              const complete = moduleItems.every((item) => !item.required || itemIsAnswered(item, responses));
              return (
                <button
                  key={module.id}
                  type="button"
                  onClick={() => setModuleIndex(index)}
                  className={index === moduleIndex ? "organic-action-selected justify-start rounded-2xl px-4 py-3 text-left text-sm font-bold" : "organic-chip justify-start rounded-2xl px-4 py-3 text-left text-sm"}
                >
                  {complete ? <CheckCircle2 size={16} /> : <span className="h-4 w-4 rounded-full border border-current" />}
                  {module.title}
                </button>
              );
            })}
          </div>
        </aside>

        <section className="glass-card p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--color-accent-action-muted)]">Group {moduleIndex + 1} of {modules.length}</p>
              <h2 className="mt-2 font-display text-3xl font-semibold theme-text">{currentModule?.title}</h2>
              <p className="mt-2 text-sm theme-muted">{currentModule?.description}</p>
            </div>
            <button type="button" className="organic-button-secondary" onClick={() => void saveCurrent()}>
              <Save size={16} /> Save and continue later
            </button>
          </div>

          <div className="mt-6 grid gap-4">
            {currentItems.map((item) => (
              <AssessmentItem
                key={item.id}
                item={item}
                definition={definition}
                value={responses[item.id]}
                prefillNote={prefill?.notes?.[item.id]}
                onChange={(value) => setResponses((current) => ({ ...current, [item.id]: value }))}
              />
            ))}
          </div>

          <div className="mt-6 flex flex-wrap justify-between gap-3">
            <button type="button" className="organic-button-secondary" disabled={moduleIndex === 0} onClick={() => setModuleIndex((current) => Math.max(0, current - 1))}>
              <ArrowLeft size={16} /> Back
            </button>
            <div className="flex flex-wrap gap-3">
              {currentItems.some((item) => !item.required) ? (
                <button type="button" className="organic-button-secondary" onClick={() => setModuleIndex((current) => Math.min(modules.length - 1, current + 1))}>
                  Skip optional group
                </button>
              ) : null}
              {moduleIndex < modules.length - 1 ? (
                <button type="button" className="organic-button" onClick={() => void continueNext()}>
                  Continue <ArrowRight size={16} />
                </button>
              ) : (
                <button type="button" className="organic-button" onClick={() => void finish()}>
                  Complete Assessment <ShieldCheck size={16} />
                </button>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
