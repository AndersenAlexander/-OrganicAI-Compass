import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, Check, RotateCcw, Save, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { submitDiagnostic } from "../../api/diagnosticApi";
import type { DiagnosticPayload } from "../../types/diagnostic";
import { useAppActions } from "../../hooks/useAppActions";
import { DiagnosticProgress, diagnosticStepNames } from "./DiagnosticProgress";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";
import { ACTION_FEEDBACK_KEY } from "../shared/ActionFeedback";

const DRAFT_KEY = "organicai_diagnostic_draft";

const initial: DiagnosticPayload = {
  interests: [],
  natural_activities: [],
  problems_noticed: [],
  preferred_orientation: [],
  career_interests: {},
  fears: [],
  fear_intensity: 5,
  ai_threat_or_opportunity: "",
  unclear_future: "",
  desired_world: "",
  values: [],
  contribution_if_supported: "",
  skills: [],
  preferred_learning_style: [],
  cognitive_style: [],
  ai_experience: "",
  ai_tools_used: [],
  ai_confidence: 5,
  ai_help_goals: [],
  preferred_interaction: "both",
  raw_answers: {},
};

type Draft = { step: number; form: DiagnosticPayload; updatedAt: string };

const optionSets = {
  interests: ["Education", "Design", "Technology", "Nature", "Storytelling", "Well-being", "Science", "Community"],
  orientation: ["People", "Ideas", "Systems", "Visual creation", "Technology", "Nature", "Learning", "Community"],
  values: ["Creativity", "Care", "Freedom", "Learning", "Responsibility", "Community", "Fairness", "Sustainability"],
  skills: ["Communication", "Analysis", "Design", "Teaching", "Facilitation", "Research", "Building", "Leadership"],
  learning: ["Hands-on practice", "Visual examples", "Reading and reflection", "Conversation and feedback"],
  cognitive: ["Structured", "Exploratory", "Visual", "Verbal", "Practical", "Social"],
  tools: ["ChatGPT", "Microsoft Copilot", "Claude", "Gemini", "Midjourney", "Canva AI", "No tools yet"],
  goals: ["Learn faster", "Create", "Research", "Make decisions", "Automate repetition", "Communicate", "Plan projects"],
};

const careerInterestDimensions = [
  {
    key: "realistic",
    label: "Realistic",
    prompt: "Practical hands-on activity with tools, physical systems, or technical operations",
  },
  {
    key: "investigative",
    label: "Investigative",
    prompt: "Research, analysis, data, science, or solving complex questions",
  },
  {
    key: "artistic",
    label: "Artistic",
    prompt: "Design, writing, visual expression, originality, or creating new concepts",
  },
  {
    key: "social",
    label: "Social",
    prompt: "Helping, teaching, mentoring, supporting, or developing people",
  },
  {
    key: "enterprising",
    label: "Enterprising",
    prompt: "Initiating projects, persuading, negotiating, leading decisions, or building opportunities",
  },
  {
    key: "conventional",
    label: "Conventional",
    prompt: "Organising information, documenting details, planning procedures, or maintaining accurate systems",
  },
] as const;

const careerInterestOptions = [
  { value: 1, label: "Not appealing" },
  { value: 2, label: "Slightly" },
  { value: 3, label: "Moderately" },
  { value: 4, label: "Very" },
  { value: 5, label: "Extremely" },
];

const generationStages = [
  "Understanding your answers",
  "Identifying patterns",
  "Mapping tendencies and values",
  "Exploring AI collaboration styles",
  "Building your Human Potential Map",
];

function readDraft(): Draft | null {
  try {
    const value = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null");
    return value?.form ? value : null;
  } catch {
    return null;
  }
}

function ChoiceGroup({
  legend,
  options,
  selected,
  onToggle,
}: {
  legend: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
  single?: boolean;
}) {
  return (
    <fieldset>
      <legend className="text-sm font-semibold theme-text">{legend}</legend>
      <div className="mt-3 flex flex-wrap gap-2">
        {options.map((value) => {
          const active = selected.includes(value);

          return (
            <button
              type="button"
              key={value}
              aria-pressed={active}
              onClick={() => onToggle(value)}
              className={`inline-flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[color:var(--color-accent-action-soft)] ${
                active
                  ? "organic-action-selected"
                  : "border-[color:var(--border-soft)] bg-[color:var(--bg-glass)] theme-text hover:border-[color:var(--color-accent-action-border)]"
              }`}
            >
              {active ? <Check size={14} /> : null}
              {value}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

function CareerInterestGroup({
  values,
  onChange,
}: {
  values: Record<string, number>;
  onChange: (dimension: string, value: number) => void;
}) {
  return (
    <fieldset>
      <legend className="text-sm font-semibold theme-text">How appealing would you find work that involves these activities? *</legend>
      <p className="mt-2 text-sm theme-muted">
        This creates a RIASEC-inspired Career Interests profile. It reflects current preferences, not ability or a diagnosis.
      </p>
      <div className="mt-4 space-y-4">
        {careerInterestDimensions.map((dimension) => (
          <div key={dimension.key} className="rounded-xl border border-[color:var(--border-soft)] p-3">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="font-semibold theme-text">{dimension.label}</p>
              <p className="text-sm theme-muted">{dimension.prompt}</p>
            </div>
            <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label={`${dimension.label} career interest appeal`}>
              {careerInterestOptions.map((option) => {
                const active = values[dimension.key] === option.value;
                return (
                  <button
                    type="button"
                    key={option.value}
                    aria-pressed={active}
                    onClick={() => onChange(dimension.key, option.value)}
                    className={`rounded-full border px-3 py-2 text-xs font-semibold transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[color:var(--color-accent-action-soft)] ${
                      active
                        ? "organic-action-selected"
                        : "border-[color:var(--border-soft)] bg-[color:var(--bg-glass)] theme-text hover:border-[color:var(--color-accent-action-border)]"
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </fieldset>
  );
}

export function DiagnosticWizard() {
  const cached = useMemo(readDraft, []);
  const [showRestore, setShowRestore] = useState(!!cached);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<DiagnosticPayload>(initial);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [generationStage, setGenerationStage] = useState(0);
  const navigate = useNavigate();
  const { setActiveProfileId } = useAppActions();
  const reducedMotion = useReducedMotionPreference();

  useEffect(() => {
    if (showRestore || loading) return;
    const timer = window.setTimeout(() => {
      localStorage.setItem(DRAFT_KEY, JSON.stringify({ step, form, updatedAt: new Date().toISOString() }));
      setStatus("Progress autosaved");
    }, 450);
    return () => window.clearTimeout(timer);
  }, [form, loading, showRestore, step]);

  useEffect(() => {
    if (!loading) return;
    const timer = window.setInterval(
      () => setGenerationStage((current) => Math.min(generationStages.length - 1, current + 1)),
      900,
    );
    return () => window.clearInterval(timer);
  }, [loading]);

  const setField = <K extends keyof DiagnosticPayload>(key: K, value: DiagnosticPayload[K]) =>
    setForm((current) => ({ ...current, [key]: value }));

  const toggle = (
    key:
      | "interests"
      | "preferred_orientation"
      | "values"
      | "skills"
      | "preferred_learning_style"
      | "cognitive_style"
      | "ai_tools_used"
      | "ai_help_goals",
    value: string,
  ) => setField(key, form[key].includes(value) ? form[key].filter((item) => item !== value) : [...form[key], value]);

  const textList = (key: "natural_activities" | "problems_noticed" | "fears", label: string, optional = false) => (
    <label className="block">
      <span className="text-sm font-semibold theme-text">
        {label} {optional ? <small className="font-normal theme-muted">(optional)</small> : "*"}
      </span>
      <textarea
        rows={3}
        className="organic-input mt-2"
        value={form[key].join("\n")}
        onChange={(event) => setField(key, event.target.value.split("\n").filter(Boolean))}
        placeholder="One answer per line"
      />
    </label>
  );

  const text = (key: "unclear_future" | "desired_world" | "contribution_if_supported", label: string, optional = false) => (
    <label className="block">
      <span className="text-sm font-semibold theme-text">
        {label} {optional ? <small className="font-normal theme-muted">(optional)</small> : "*"}
      </span>
      <textarea rows={3} className="organic-input mt-2" value={form[key]} onChange={(event) => setField(key, event.target.value)} />
    </label>
  );

  const valid = [
    form.interests.length > 0 &&
      form.natural_activities.length > 0 &&
      form.preferred_orientation.length > 0 &&
      careerInterestDimensions.every((dimension) => Number.isInteger(form.career_interests[dimension.key])),
    form.fears.length > 0 && !!form.unclear_future.trim() && !!form.ai_threat_or_opportunity,
    form.values.length > 0 && !!form.desired_world.trim() && !!form.contribution_if_supported.trim(),
    form.preferred_learning_style.length > 0 && form.cognitive_style.length > 0,
    !!form.ai_experience && form.ai_help_goals.length > 0 && !!form.preferred_interaction,
  ][step];

  function resume() {
    if (cached) {
      setForm({ ...initial, ...cached.form });
      setStep(cached.step || 0);
    }
    setShowRestore(false);
    setStatus("Previous diagnostic restored.");
  }

  function startOver() {
    localStorage.removeItem(DRAFT_KEY);
    setForm(initial);
    setStep(0);
    setShowRestore(false);
    setStatus("Started a new diagnostic.");
  }

  function saveExit() {
    localStorage.setItem(DRAFT_KEY, JSON.stringify({ step, form, updatedAt: new Date().toISOString() }));
    sessionStorage.setItem(ACTION_FEEDBACK_KEY, "Diagnostic draft saved. You can resume whenever you are ready.");
    navigate("/my-journey");
  }

  async function submit() {
    if (!valid) {
      setError("Complete the required questions before continuing.");
      return;
    }

    setLoading(true);
    setGenerationStage(0);
    setError("");

    try {
      const response = await submitDiagnostic(form);
      setActiveProfileId(response.profile_id);
      localStorage.removeItem(DRAFT_KEY);
      navigate(`/profile/${response.profile_id}`);
    } catch {
      setError("We could not build your map. Your answers are safe. Retry to use the resilient profile generator.");
      setLoading(false);
    }
  }

  if (showRestore) {
    return (
      <div className="glass-card p-6">
        <p className="organic-badge">Saved diagnostic</p>
        <h2 className="mt-4 font-display text-3xl font-semibold theme-text">Continue your previous diagnostic?</h2>
        <p className="mt-3 theme-muted">
          Last saved {cached ? new Date(cached.updatedAt).toLocaleString() : "recently"}. You can resume at step{" "}
          {(cached?.step ?? 0) + 1} or begin again.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button type="button" onClick={resume} className="organic-button">
            Resume <ArrowRight size={17} />
          </button>
          <button type="button" onClick={startOver} className="organic-button-secondary">
            <RotateCcw size={17} /> Start over
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="glass-card min-h-[30rem] p-8 text-center" aria-live="polite">
        <div className="mx-auto grid h-28 w-28 place-items-center rounded-full border border-teal-200 bg-[radial-gradient(circle,rgba(94,234,212,0.35),transparent_68%)] shadow-glow">
          <Sparkles className="animate-pulse text-[color:var(--teal)]" size={38} />
        </div>
        <h2 className="mt-8 font-display text-3xl font-semibold theme-text">Building your Human Potential Map</h2>
        <div className="mx-auto mt-7 max-w-lg space-y-3">
          {generationStages.map((label, index) => (
            <p
              key={label}
              className={`rounded-xl px-4 py-2 text-sm ${
                index <= generationStage ? "bg-teal/10 font-semibold text-[color:var(--teal)]" : "theme-muted"
              }`}
            >
              {index < generationStage ? "Done" : index === generationStage ? "Active" : "Pending"} - {label}
            </p>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <DiagnosticProgress currentStep={step} />
      <div className="glass-card relative overflow-hidden p-6">
        <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-teal-200/20 blur-3xl" />
        <div className="relative flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[color:var(--teal)]">Step {step + 1}</p>
            <h2 className="mt-2 font-display text-3xl font-semibold theme-text">{diagnosticStepNames[step]}</h2>
            <p className="mt-2 text-sm theme-muted">There are no perfect answers. Choose what feels most true today.</p>
          </div>
          <button type="button" onClick={saveExit} className="organic-button-secondary">
            <Save size={17} /> Save & Exit
          </button>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={reducedMotion ? false : { opacity: 0, x: 18 }}
            animate={{ opacity: 1, x: 0 }}
            exit={reducedMotion ? undefined : { opacity: 0, x: -18 }}
            className="relative mt-7 space-y-6"
          >
            {step === 0 && (
              <>
                <ChoiceGroup legend="What topics naturally attract your attention? *" options={optionSets.interests} selected={form.interests} onToggle={(value) => toggle("interests", value)} />
                {textList("natural_activities", "Which activities make you lose track of time?")}
                {textList("problems_noticed", "What kinds of problems do you naturally notice?", true)}
                <ChoiceGroup legend="Where do you feel most energized? *" options={optionSets.orientation} selected={form.preferred_orientation} onToggle={(value) => toggle("preferred_orientation", value)} />
                <CareerInterestGroup values={form.career_interests} onChange={(dimension, value) => setField("career_interests", { ...form.career_interests, [dimension]: value })} />
              </>
            )}

            {step === 1 && (
              <>
                {textList("fears", "What concerns you most about AI?")}
                <label className="block">
                  <span className="text-sm font-semibold theme-text">How intense is this concern? {form.fear_intensity}/10</span>
                  <input type="range" min="1" max="10" value={form.fear_intensity} onChange={(event) => setField("fear_intensity", Number(event.target.value))} className="organic-range-action mt-3 w-full" />
                  <span className="mt-1 flex justify-between text-xs theme-muted">
                    <span>Low</span>
                    <span>High</span>
                  </span>
                </label>
                {text("unclear_future", "What feels unclear about your future?")}
                <ChoiceGroup legend="Do you experience AI more as a threat, opportunity, or both? *" options={["Threat", "Opportunity", "Both"]} selected={form.ai_threat_or_opportunity ? [form.ai_threat_or_opportunity] : []} onToggle={(value) => setField("ai_threat_or_opportunity", value)} />
              </>
            )}

            {step === 2 && (
              <>
                <ChoiceGroup legend="Which values matter most to you? *" options={optionSets.values} selected={form.values} onToggle={(value) => toggle("values", value)} />
                {text("desired_world", "What kind of future would you like to help create?")}
                {text("contribution_if_supported", "How would you contribute if time, money, and confidence were not barriers?")}
                <label className="block">
                  <span className="text-sm font-semibold theme-text">
                    Which human needs matter most to you? <small className="font-normal theme-muted">(optional)</small>
                  </span>
                  <textarea
                    className="organic-input mt-2"
                    rows={3}
                    value={form.raw_answers.human_needs || ""}
                    onChange={(event) => setField("raw_answers", { ...form.raw_answers, human_needs: event.target.value })}
                  />
                </label>
              </>
            )}

            {step === 3 && (
              <>
                <ChoiceGroup legend="Which capability signals would you like to prefill for later assessment? (optional)" options={optionSets.skills} selected={form.skills} onToggle={(value) => toggle("skills", value)} />
                <ChoiceGroup legend="How do you prefer to learn? *" options={optionSets.learning} selected={form.preferred_learning_style} onToggle={(value) => toggle("preferred_learning_style", value)} />
                <ChoiceGroup legend="How do you process information and approach problems? *" options={optionSets.cognitive} selected={form.cognitive_style} onToggle={(value) => toggle("cognitive_style", value)} />
              </>
            )}

            {step === 4 && (
              <>
                <ChoiceGroup legend="What is your current experience with AI? *" options={["New to AI", "Beginner", "Intermediate", "Advanced"]} selected={form.ai_experience ? [form.ai_experience] : []} onToggle={(value) => setField("ai_experience", value)} />
                <ChoiceGroup legend="Which tools have you used?" options={optionSets.tools} selected={form.ai_tools_used} onToggle={(value) => toggle("ai_tools_used", value)} />
                <label className="block">
                  <span className="text-sm font-semibold theme-text">How confident do you feel using AI? {form.ai_confidence}/10</span>
                  <input type="range" min="1" max="10" value={form.ai_confidence} onChange={(event) => setField("ai_confidence", Number(event.target.value))} className="organic-range-action mt-3 w-full" />
                </label>
                <ChoiceGroup legend="What would you like AI to help you with? *" options={optionSets.goals} selected={form.ai_help_goals} onToggle={(value) => toggle("ai_help_goals", value)} />
                <ChoiceGroup legend="Do you prefer text, voice, or both? *" options={["text", "voice", "both"]} selected={[form.preferred_interaction]} onToggle={(value) => setField("preferred_interaction", value as DiagnosticPayload["preferred_interaction"])} />
              </>
            )}
          </motion.div>
        </AnimatePresence>

        <div aria-live="polite">
          {error ? <p className="mt-5 text-sm font-semibold text-red-600">{error}</p> : null}
          {status ? <p className="mt-3 text-xs text-[color:var(--teal)]">{status}</p> : null}
        </div>

        <div className="mt-7 flex items-center justify-between gap-3">
          <button type="button" disabled={step === 0} onClick={() => { setError(""); setStep((current) => current - 1); }} className="organic-button-secondary disabled:opacity-40">
            <ArrowLeft size={17} /> Back
          </button>
          {step < 4 ? (
            <button type="button" disabled={!valid} onClick={() => { if (valid) { setError(""); setStep((current) => current + 1); } }} className="organic-button disabled:opacity-40">
              Continue <ArrowRight size={17} />
            </button>
          ) : (
            <button type="button" disabled={!valid} onClick={() => void submit()} className="organic-button disabled:opacity-40">
              Generate My Human Potential Map <Sparkles size={17} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
