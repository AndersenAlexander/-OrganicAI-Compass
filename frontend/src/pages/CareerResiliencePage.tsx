import {
  ArrowRight,
  BadgeCheck,
  BriefcaseBusiness,
  ClipboardCheck,
  Compass,
  ExternalLink,
  FileBadge,
  FileText,
  FlaskConical,
  HeartHandshake,
  LifeBuoy,
  MapPinned,
  Play,
  RefreshCw,
  Send,
  ShieldAlert,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  createCareerExperiment,
  createImmediateActionPlan,
  createSupportBrief,
  createSupportedPaths,
  evaluateCareerExperiment,
  confirmCareerExperimentRoadmap,
  getCareerExperimentSession,
  getCareerExperimentTemplates,
  getCareerResilienceDashboard,
  getEvidencePassport,
  getImmediateActionPlan,
  getJobLossProfile,
  getProfileCareerExperiments,
  getSupportBrief,
  getSupportScreening,
  getSupportedPaths,
  recalibrateCareer,
  runSupportScreening,
  saveJobLossProfile,
  selfReviewCareerExperiment,
  startCareerExperiment,
  submitCareerExperiment,
} from "../api/careerResilienceApi";
import { extractApiError } from "../api/client";
import { getRoadmap } from "../api/roadmapApi";
import { useAppActions } from "../hooks/useAppActions";
import { careerReviewOutcome, evidenceProvenanceLabel, linkedGapExplanation } from "../lib/careerEvidenceReview";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";
import type {
  CareerExperimentSession,
  CareerExperimentTemplate,
  CareerExperimentRecommendation,
  CareerResilienceDashboard,
  EvidencePassport,
  ImmediateActionPlan,
  JobLossProfile,
  SupportBrief,
  SupportScreening,
  SupportedPathRun,
} from "../types/careerResilience";

function validProfileId(value?: string) {
  return value && !["undefined", "null"].includes(value) ? value : "";
}

function routeSection(pathname: string) {
  if (pathname.includes("/evidence-passport")) return "evidence";
  if (pathname.includes("/supported-paths")) return "paths";
  if (pathname.includes("/job-loss-support")) return "jobLoss";
  if (pathname.includes("/support-brief")) return "brief";
  if (pathname.includes("/experiments")) return "experiments";
  return "dashboard";
}

function TabLink({ to, active, icon, children }: { to: string; active: boolean; icon: ReactNode; children: ReactNode }) {
  return (
    <Link className={active ? "organic-button" : "organic-button-secondary"} to={to}>
      {icon}
      {children}
    </Link>
  );
}

function SignalCard({ title, value, icon }: { title: string; value: string; icon: React.ReactNode }) {
  return (
    <article className="glass-card p-5">
      <div className="flex items-center gap-3">
        <span className="organic-icon-orb h-10 w-10">{icon}</span>
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[color:var(--teal)]">{title}</p>
          <p className="mt-1 font-display text-xl font-semibold theme-text">{value}</p>
        </div>
      </div>
    </article>
  );
}

function EvidenceLabel({ value }: { value: string }) {
  const tone = value.toLowerCase().includes("strong") || value.toLowerCase().includes("multiple")
    ? "border-[color:var(--color-accent-success)] text-[color:var(--green)]"
    : value.toLowerCase().includes("limited")
      ? "border-amber-400 text-amber-700"
      : "border-[color:var(--teal)] text-[color:var(--teal)]";
  return <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-bold ${tone}`}>{value}</span>;
}

export function CareerResiliencePage() {
  const params = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const profileId = validProfileId(params.profileId || activeProfileId);
  const experimentId = params.experimentId;
  const section = routeSection(location.pathname);

  const [dashboard, setDashboard] = useState<CareerResilienceDashboard | null>(null);
  const [templates, setTemplates] = useState<CareerExperimentTemplate[]>([]);
  const [sessions, setSessions] = useState<CareerExperimentSession[]>([]);
  const [sessionDetail, setSessionDetail] = useState<CareerExperimentSession | null>(null);
  const [passport, setPassport] = useState<EvidencePassport | null>(null);
  const [paths, setPaths] = useState<SupportedPathRun | null>(null);
  const [jobLoss, setJobLoss] = useState<JobLossProfile | null>(null);
  const [plan, setPlan] = useState<ImmediateActionPlan | null>(null);
  const [screening, setScreening] = useState<SupportScreening | null>(null);
  const [brief, setBrief] = useState<SupportBrief | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [roadmapMutationError, setRoadmapMutationError] = useState("");
  const [reviewMutationError, setReviewMutationError] = useState("");
  const [addingToRoadmap, setAddingToRoadmap] = useState(false);
  const [reviewingEvidence, setReviewingEvidence] = useState(false);
  const [submissionText, setSubmissionText] = useState("");
  const [projectUrl, setProjectUrl] = useState("");
  const [completionNotes, setCompletionNotes] = useState("");
  const [reflection, setReflection] = useState("");
  const [jobConsent, setJobConsent] = useState(false);
  const [jobRegion, setJobRegion] = useState("Oslo");
  const [lastWorkingDate, setLastWorkingDate] = useState("");
  const [evidenceSufficientRecommendation, setEvidenceSufficientRecommendation] = useState<CareerExperimentRecommendation | null>(null);

  async function refresh() {
    if (!profileId) return;
    setError("");
    const [dashboardData, templateData, sessionData, passportData, pathsData, jobData, planData, screeningData, briefData] = await Promise.all([
      getCareerResilienceDashboard(profileId).catch(() => null),
      getCareerExperimentTemplates().catch(() => []),
      getProfileCareerExperiments(profileId).catch(() => []),
      getEvidencePassport(profileId).catch(() => null),
      getSupportedPaths(profileId).catch(() => null),
      getJobLossProfile(profileId).catch(() => null),
      getImmediateActionPlan(profileId).catch(() => null),
      getSupportScreening(profileId).catch(() => null),
      getSupportBrief(profileId).catch(() => null),
    ]);
    setDashboard(dashboardData);
    setTemplates(templateData);
    setSessions(sessionData);
    setPassport(passportData);
    setPaths(pathsData);
    setJobLoss(jobData);
    setPlan(planData);
    setScreening(screeningData);
    setBrief(briefData);
    if (experimentId) {
      const detail = await getCareerExperimentSession(experimentId).catch(() => null);
      setSessionDetail(detail);
    } else {
      setSessionDetail(null);
    }
  }

  useEffect(() => {
    if (!profileId) return;
    setActiveProfileId(profileId);
    refresh().catch(() => setError("Career Resilience data could not be loaded."));
  }, [profileId, experimentId, setActiveProfileId]);

  const selectedSession = useMemo(() => {
    if (sessionDetail) return sessionDetail;
    if (!experimentId) return sessions[0] ?? null;
    return sessions.find((item) => item.id === experimentId) ?? null;
  }, [experimentId, sessionDetail, sessions]);

  async function createSession(templateId: string) {
    const created = await createCareerExperiment(profileId, {
      experiment_template_id: templateId,
      mode: "guided",
      user_confirmed: true,
    });
    if (!("id" in created)) {
      setEvidenceSufficientRecommendation(created.recommendation);
      setStatus("Current priority evidence is sufficient. My Roadmap was not changed.");
      return;
    }
    setStatus("Experiment planned. My Roadmap was not changed.");
    navigate(`/workspace/${profileId}/experiments/${created.id}`);
  }

  async function handleTestCareer(careerMatchId?: string | null) {
    if (!careerMatchId) return;
    const created = await createCareerExperiment(profileId, {
      career_match_id: careerMatchId,
      mode: "guided",
      user_confirmed: true,
    });
    if (!("id" in created)) {
      setEvidenceSufficientRecommendation(created.recommendation);
      setStatus("Current priority evidence is sufficient. My Roadmap was not changed.");
      await refresh();
      return;
    }
    setEvidenceSufficientRecommendation(null);
    setStatus("Career experiment planned. My Roadmap was not changed.");
    navigate(`${base}/experiments/${created.id}`);
  }

  async function handleAddToRoadmap(session: CareerExperimentSession) {
    if (session.roadmap_action_id || addingToRoadmap) return;
    setAddingToRoadmap(true);
    setRoadmapMutationError("");
    setStatus("");
    try {
      let updated: CareerExperimentSession;
      try {
        updated = await confirmCareerExperimentRoadmap(session.id, true);
        if (!updated.roadmap_action_id) {
          throw new Error("The server did not return a confirmed roadmap link.");
        }
      } catch (requestError) {
        const details = extractApiError(requestError);
        const detail = details.message !== "The request failed."
          ? details.message
          : requestError instanceof Error
            ? requestError.message
            : details.message;
        const requestId = details.requestId ? ` Request ID: ${details.requestId}.` : "";
        setRoadmapMutationError(`Could not add this experiment to My Roadmap. ${detail}${requestId} Please try again.`);
        return;
      }

      setSessionDetail(updated);
      // This app uses local page state rather than a query-cache library. Refetch
      // both aggregates explicitly so counters, badges, and My Roadmap agree.
      try {
        await Promise.all([refresh(), getRoadmap(profileId)]);
        setStatus("Experiment added to My Roadmap after explicit confirmation.");
      } catch (requestError) {
        setRoadmapMutationError(`Experiment was added to My Roadmap, but the latest state could not be refreshed. ${requestError instanceof Error ? requestError.message : "Refresh this page to verify it."}`);
      }
    } finally {
      setAddingToRoadmap(false);
    }
  }

  async function handleStart(session: CareerExperimentSession) {
    const updated = await startCareerExperiment(session.id);
    setSessionDetail(updated);
    setStatus("Experiment is in progress.");
    await refresh();
  }

  async function handleSubmit(session: CareerExperimentSession) {
    const updated = await submitCareerExperiment(session.id, {
      text_response: submissionText,
      project_url: projectUrl || undefined,
      completion_notes: completionNotes || "Submitted manual evidence for deterministic review.",
      time_spent_minutes: 120,
      ai_tools_used: ["Optional AI assistant"],
      assistance_level: "brainstorming_and_critique",
      self_rated_difficulty: 3,
      self_rated_enjoyment: 4,
      confidence_before: 3,
      confidence_after: 4,
      reflection: { note: reflection || "The task clarified interest, gaps, and next evidence needs." },
    });
    setSessionDetail(updated);
    setStatus("Submission saved. Deterministic review is ready.");
    await refresh();
  }

  async function handleReviewAndEvaluate(session: CareerExperimentSession) {
    if (reviewingEvidence) return;
    setReviewingEvidence(true);
    setReviewMutationError("");
    setStatus("");
    try {
      const alreadySelfReviewed = session.reviews.some((review) => review.source_type === "self_review");
      if (!alreadySelfReviewed) {
        await selfReviewCareerExperiment(session.id, {
          reflection: reflection || "The experiment created useful evidence and left some uncertainty.",
          self_rated_difficulty: 3,
          self_rated_enjoyment: 4,
          confidence_before: 3,
          confidence_after: 4,
        });
      }
      const evaluated = await evaluateCareerExperiment(session.id);
      const recalibration = await recalibrateCareer(profileId, evaluated.result?.id);
      const outcome = careerReviewOutcome(evaluated, recalibration);
      if (!outcome.ok) throw new Error(outcome.message);

      // Refetch the persisted sources and derived career state before reporting
      // success. This page has local state instead of a query-cache library.
      const [passportData, dashboardData, sessionsData, detail] = await Promise.all([
        getEvidencePassport(profileId),
        getCareerResilienceDashboard(profileId),
        getProfileCareerExperiments(profileId),
        getCareerExperimentSession(session.id),
      ]);
      setPassport(passportData);
      setDashboard(dashboardData);
      setSessions(sessionsData);
      setSessionDetail(detail);
      setStatus(outcome.message);
    } catch (requestError) {
      const details = extractApiError(requestError);
      const detail = details.message !== "The request failed."
        ? details.message
        : requestError instanceof Error
          ? requestError.message
          : details.message;
      const requestId = details.requestId ? ` Request ID: ${details.requestId}.` : "";
      setReviewMutationError(`Could not persist reviewed evidence. ${detail}${requestId} Please try again.`);
    } finally {
      setReviewingEvidence(false);
    }
  }

  async function handleSupportedPaths() {
    const created = await createSupportedPaths(profileId);
    setPaths(created);
    setStatus("Supported paths recalculated with separate personal, capability, market, and support factors.");
    await refresh();
  }

  async function activateJobLossMode() {
    await saveJobLossProfile(profileId, {
      consent_accepted: jobConsent,
      country_of_residence: "Norway",
      country_of_employment: "Norway",
      municipality_or_region: jobRegion,
      last_working_date: lastWorkingDate || undefined,
      contract_termination_type: "terminated",
      employment_status: "unemployed",
      reduction_in_working_hours: 100,
      jobseeker_registration_status: "not_registered",
      current_benefits: [],
      education: "User-provided education summary",
      training_interest: "yes",
      availability_for_work: "yes",
      relocation_preferences: "Hybrid or remote preferred",
    });
    const [createdPlan, createdScreening] = await Promise.all([createImmediateActionPlan(profileId), runSupportScreening(profileId)]);
    const createdPaths = await createSupportedPaths(profileId);
    const createdBrief = await createSupportBrief(profileId);
    setPlan(createdPlan);
    setScreening(createdScreening);
    setPaths(createdPaths);
    setBrief(createdBrief);
    setStatus("Job Loss Mode activated with preliminary support screening and official-source actions.");
    await refresh();
  }

  const base = `/workspace/${profileId}`;
  const persistedEvidenceSufficientRecommendation = useMemo(
    () => dashboard?.evidence_states?.find((item) => item.state === "evidence_sufficient")?.recommendation ?? null,
    [dashboard],
  );
  const currentEvidenceSufficientRecommendation = evidenceSufficientRecommendation || persistedEvidenceSufficientRecommendation;
  const groupedTemplates = useMemo(() => {
    const groups: Record<string, CareerExperimentTemplate[]> = {};
    templates.forEach((template) => {
      groups[template.target_role_family] = [...(groups[template.target_role_family] || []), template];
    });
    return groups;
  }, [templates]);

  if (!profileId) return <ProfileRequiredState title="Create your profile before opening Career Experiments." />;
  if (error) return <div className="organic-section text-red-700">{error}</div>;

  return (
    <div className="organic-page">
      <section className="organic-section">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="organic-badge">Career Resilience</p>
            <h1 className="mt-4 font-display text-4xl font-semibold theme-text">Evidence-based career hypotheses.</h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">
              Current evidence suggests directions to test. This career direction remains a hypothesis until practical evidence, market signals, and support feasibility are reviewed.
            </p>
          </div>
          <div className="grid gap-2 sm:flex sm:flex-wrap">
            <TabLink to={`${base}/career-resilience`} active={section === "dashboard"} icon={<Compass size={16} />}>Dashboard</TabLink>
            <TabLink to={`${base}/experiments`} active={section === "experiments"} icon={<FlaskConical size={16} />}>Experiments</TabLink>
            <TabLink to={`${base}/evidence-passport`} active={section === "evidence"} icon={<FileBadge size={16} />}>Evidence</TabLink>
            <TabLink to={`${base}/supported-paths`} active={section === "paths"} icon={<MapPinned size={16} />}>Supported Paths</TabLink>
            <TabLink to={`${base}/job-loss-support`} active={section === "jobLoss"} icon={<LifeBuoy size={16} />}>Job Loss Support</TabLink>
          </div>
        </div>
        {status ? <p className="mt-4 text-sm font-bold text-[color:var(--teal)]" role="status">{status}</p> : null}
        {roadmapMutationError ? <p className="mt-3 text-sm font-semibold text-red-700" role="alert">{roadmapMutationError}</p> : null}
        {reviewMutationError ? <p className="mt-3 text-sm font-semibold text-red-700" role="alert">{reviewMutationError}</p> : null}
      </section>

      {section === "dashboard" ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <SignalCard title="Next action" value={dashboard?.next_recommended_action || "Select a role experiment"} icon={<ArrowRight size={18} />} />
            <SignalCard title="Active hypotheses" value={String(dashboard?.career_hypotheses.length ?? 0)} icon={<Compass size={18} />} />
            <SignalCard title="Experiment records" value={String(dashboard?.active_experiments.length ?? 0)} icon={<FlaskConical size={18} />} />
            <SignalCard title="Urgent actions" value={String(dashboard?.urgent_actions.length ?? 0)} icon={<ShieldAlert size={18} />} />
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <article className="glass-card p-5">
              <h2 className="font-display text-2xl font-semibold theme-text">Career hypotheses</h2>
              <div className="mt-4 grid gap-3">
                {(dashboard?.career_hypotheses || []).map((hypothesis) => (
                  <div key={hypothesis.id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-bold theme-text">{hypothesis.title}</h3>
                        <p className="mt-2 text-sm theme-muted">{hypothesis.statement}</p>
                      </div>
                      <EvidenceLabel value={hypothesis.uncertainty_label} />
                    </div>
                    {hypothesis.missing_evidence?.length ? <p className="mt-3 text-sm theme-muted" data-testid="career-hypothesis-unresolved-gaps">Unresolved evidence: {hypothesis.missing_evidence.map((gap) => gap.capability).join(", ")}</p> : <p className="mt-3 text-sm theme-muted">No unresolved priority evidence gap is currently recorded.</p>}
                    <button
                      type="button"
                      className="organic-button-secondary mt-4"
                      onClick={() => void handleTestCareer(hypothesis.career_match_id)}
                    >
                      <FlaskConical size={16} /> Test this career
                    </button>
                  </div>
                ))}
                {currentEvidenceSufficientRecommendation?.state === "evidence_sufficient" ? (
                  <section className="rounded-2xl border border-[color:var(--color-accent-success)] bg-[color:var(--color-accent-success-soft)] p-4" data-testid="evidence-sufficient-state">
                    <h3 className="font-bold theme-text">Current priority evidence is sufficient</h3>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">
                      {currentEvidenceSufficientRecommendation.rationale.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                    <p className="mt-3 text-sm font-semibold theme-text">Choose a next step when you are ready</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">
                      {(currentEvidenceSufficientRecommendation.next_options || []).map((item) => <li key={item}>{item}</li>)}
                    </ul>
                    <p className="mt-3 text-xs theme-muted">No roadmap action was created. Adding one always requires explicit confirmation.</p>
                  </section>
                ) : null}
                {!dashboard?.career_hypotheses.length ? <p className="text-sm theme-muted">Complete Career Compatibility to create hypotheses.</p> : null}
              </div>
            </article>

            <article className="glass-card p-5">
              <h2 className="font-display text-2xl font-semibold theme-text">Workflow</h2>
              <div className="mt-4 grid gap-2">
                {(dashboard?.workflow || []).map((step, index) => (
                  <div key={step} className="flex items-center gap-3 rounded-2xl border border-[color:var(--border-soft)] px-4 py-3 text-sm theme-muted">
                    <span className="grid h-7 w-7 place-items-center rounded-full bg-[color:var(--color-accent-action-soft)] text-xs font-bold text-[color:var(--color-accent-action-muted)]">{index + 1}</span>
                    {step}
                  </div>
                ))}
              </div>
            </article>
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            {(dashboard?.best_supported_paths || []).slice(0, 3).map((path) => (
              <article key={path.id} className="glass-card p-5">
                <p className="organic-badge">Supported Path</p>
                <h3 className="mt-3 font-display text-2xl font-semibold theme-text">{path.title}</h3>
                <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                  <EvidenceLabel value={`Personal: ${path.personal_fit}`} />
                  <EvidenceLabel value={`Capability: ${path.capability_fit}`} />
                  <EvidenceLabel value={`Market: ${path.market_fit}`} />
                  <EvidenceLabel value={`Support: ${path.support_fit}`} />
                </div>
              </article>
            ))}
          </section>
        </>
      ) : null}

      {section === "experiments" ? (
        <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
          <article className="glass-card p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-display text-2xl font-semibold theme-text">Experiment catalogue</h2>
              <span className="organic-chip">{templates.length} templates</span>
            </div>
            <div className="mt-5 space-y-5">
              {Object.entries(groupedTemplates).map(([family, items]) => (
                <div key={family}>
                  <h3 className="font-bold theme-text">{family}</h3>
                  <div className="mt-3 grid gap-3">
                    {items.map((template) => (
                      <article key={template.id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <h4 className="font-bold theme-text">{template.title}</h4>
                            <p className="mt-2 text-sm theme-muted">{template.purpose}</p>
                            <p className="mt-2 text-xs font-semibold text-[color:var(--color-accent-action-muted)]">{template.estimated_duration_minutes} minutes - {template.difficulty}</p>
                          </div>
                          <button type="button" className="organic-button-secondary" onClick={() => void createSession(template.id)}>
                            <ClipboardCheck size={16} /> Plan
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="glass-card p-5">
            <h2 className="font-display text-2xl font-semibold theme-text">{selectedSession?.template?.title || "Active experiment"}</h2>
            {selectedSession ? (
              <div className="mt-4 space-y-4">
                <div className="flex flex-wrap gap-2">
                  <EvidenceLabel value={selectedSession.status.replace(/_/g, " ")} />
                  <EvidenceLabel value={selectedSession.mode.replace(/_/g, " ")} />
                  {selectedSession.roadmap_action_id ? <EvidenceLabel value="Roadmap confirmed" /> : <EvidenceLabel value="Not in roadmap" />}
                </div>
                {selectedSession.recommendation ? (
                  <section className="rounded-2xl border border-[color:var(--color-accent-action-border)] bg-[color:var(--color-accent-action-soft)] p-4" data-testid="experiment-recommendation-rationale">
                    <h3 className="font-bold theme-text">Recommended because</h3>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">
                      {selectedSession.recommendation.rationale.map((reason) => <li key={reason}>{reason}</li>)}
                    </ul>
                  </section>
                ) : null}
                <p className="text-sm leading-6 theme-muted">{selectedSession.template?.real_world_scenario}</p>
                {selectedSession.template?.evaluation_rubric ? (
                  <details className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                    <summary className="cursor-pointer font-bold theme-text">Deterministic review rubric</summary>
                    <ul className="mt-3 list-disc space-y-1 pl-5 text-sm theme-muted">
                      {selectedSession.template.evaluation_rubric.criteria.map((criterion) => <li key={criterion.id}><span className="font-semibold">{criterion.description}</span> ({Math.round(criterion.weight * 100)}%): {criterion.evidence_requirement}</li>)}
                    </ul>
                  </details>
                ) : null}
                <details className="rounded-2xl border border-[color:var(--border-soft)] p-4" open>
                  <summary className="cursor-pointer font-bold theme-text">Expected deliverables</summary>
                  <ul className="mt-3 list-disc space-y-1 pl-5 text-sm theme-muted">
                    {(selectedSession.template?.expected_deliverables || []).map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </details>
                <div className="flex flex-wrap gap-2">
                  <button type="button" className="organic-button" disabled={selectedSession.status === "in_progress" || selectedSession.status === "evaluated"} onClick={() => void handleStart(selectedSession)}>
                    <Play size={16} /> Start
                  </button>
                  <button
                    type="button"
                    data-testid="add-experiment-to-roadmap"
                    className="organic-button-secondary"
                    disabled={addingToRoadmap || Boolean(selectedSession.roadmap_action_id)}
                    onClick={() => void handleAddToRoadmap(selectedSession)}
                  >
                    <BriefcaseBusiness size={16} /> {selectedSession.roadmap_action_id ? "Added to Roadmap" : addingToRoadmap ? "Adding to Roadmap..." : "Add to Roadmap"}
                  </button>
                </div>
                <div className="grid gap-3">
                  <textarea className="organic-input min-h-32" placeholder="Submission text or deliverable summary" value={submissionText} onChange={(event) => setSubmissionText(event.target.value)} />
                  <input className="organic-input" placeholder="Project or portfolio URL" value={projectUrl} onChange={(event) => setProjectUrl(event.target.value)} />
                  <textarea className="organic-input min-h-24" placeholder="Completion notes" value={completionNotes} onChange={(event) => setCompletionNotes(event.target.value)} />
                  <textarea className="organic-input min-h-24" placeholder="Reflection" value={reflection} onChange={(event) => setReflection(event.target.value)} />
                  <div className="flex flex-wrap gap-2">
                    <button type="button" className="organic-button-secondary" onClick={() => void handleSubmit(selectedSession)}>
                      <Send size={16} /> Submit
                    </button>
                    <button type="button" className="organic-button" disabled={reviewingEvidence || (!selectedSession.submission && selectedSession.status !== "submitted" && selectedSession.status !== "needs_review")} onClick={() => void handleReviewAndEvaluate(selectedSession)}>
                      <BadgeCheck size={16} /> {reviewingEvidence ? "Persisting evidence..." : "Review evidence"}
                    </button>
                  </div>
                </div>
                {selectedSession.result ? (
                  <div className="rounded-2xl border border-[color:var(--color-accent-success)] p-4">
                    <h3 className="font-bold theme-text">Deterministic result: {selectedSession.result.overall_label}</h3>
                    <p className="mt-2 text-sm theme-muted">Score {selectedSession.result.overall_score}. The LLM did not calculate or alter this score.</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {selectedSession.result.evidence_created.map((item) => <EvidenceLabel key={item.evidence_id} value={`${item.skill_label}: ${item.strength_label}`} />)}
                    </div>
                    {linkedGapExplanation(selectedSession) ? <p className="mt-3 text-sm theme-muted" data-testid="unresolved-linked-gap">{linkedGapExplanation(selectedSession)}</p> : null}
                    {selectedSession.result.evidence_not_created?.length ? <ul className="mt-3 list-disc space-y-1 pl-5 text-sm theme-muted">{selectedSession.result.evidence_not_created.map((item) => <li key={item.skill_id}>{item.skill_label}: {item.reason}</li>)}</ul> : null}
                    {selectedSession.result.provenance?.deterministic_review_id ? <p className="mt-3 text-xs theme-muted">Provenance: deterministic review {selectedSession.result.provenance.deterministic_review_id}; session {selectedSession.result.provenance.experiment_session_id}.</p> : null}
                    <p className="mt-3 text-sm theme-muted">This evidence did not change My Roadmap. Use Add to Roadmap only if you explicitly choose to create an action.</p>
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="mt-4 text-sm theme-muted">Plan an experiment to generate practical evidence.</p>
            )}
          </article>
        </section>
      ) : null}

      {section === "evidence" ? (
        <section className="glass-card p-5">
          <h2 className="font-display text-3xl font-semibold theme-text">Evidence Passport</h2>
          <p className="mt-2 text-sm theme-muted">{passport?.methodology}</p>
          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            {(passport?.skills || []).map((skill) => (
              <article key={skill.skill_id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="font-bold theme-text">{skill.skill_label}</h3>
                    <p className="mt-1 text-sm theme-muted">Declared {skill.declared_level} / Target {skill.target_level} - {skill.recency.status}</p>
                  </div>
                  <EvidenceLabel value={skill.evidence_confidence} />
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <EvidenceLabel value={skill.strongest_evidence_label} />
                  <EvidenceLabel value={skill.status} />
                </div>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm theme-muted">
                  {skill.evidence_sources.slice(0, 3).map((source) => (
                    <li key={source.id}>
                      {source.title} - {source.strength}
                      {source.sources?.map((provenance) => (
                        <span key={provenance.id}> · {evidenceProvenanceLabel(provenance.source_type, provenance.provenance_label)}{provenance.deterministic_score !== undefined ? ` (${provenance.deterministic_score}%)` : ""}</span>
                      ))}
                    </li>
                  ))}
                  {!skill.evidence_sources.length ? <li>{skill.outstanding_verification_needs[0] || "Additional evidence is required."}</li> : null}
                </ul>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {section === "paths" ? (
        <section className="glass-card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-3xl font-semibold theme-text">Best Supported Career Path</h2>
              <p className="mt-2 text-sm theme-muted">Personal Fit, Capability Fit, Market Fit, and Support Fit remain separate.</p>
            </div>
            <button type="button" className="organic-button" onClick={() => void handleSupportedPaths()}>
              <RefreshCw size={16} /> Recalculate
            </button>
          </div>
          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            {(paths?.results || []).map((path) => (
              <article key={path.id} className="rounded-2xl border border-[color:var(--border-soft)] p-5">
                <h3 className="font-display text-2xl font-semibold theme-text">{path.title}</h3>
                <div className="mt-4 grid gap-2 sm:grid-cols-4">
                  <EvidenceLabel value={path.personal_fit} />
                  <EvidenceLabel value={path.capability_fit} />
                  <EvidenceLabel value={path.market_fit} />
                  <EvidenceLabel value={path.support_fit} />
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-3">
                  <div>
                    <h4 className="text-sm font-bold theme-text">Strengths</h4>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">{path.main_strengths.map((item) => <li key={item}>{item}</li>)}</ul>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold theme-text">Gaps</h4>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">{path.main_gaps.map((item) => <li key={item}>{item}</li>)}</ul>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold theme-text">Uncertainties</h4>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm theme-muted">{path.main_uncertainties.map((item) => <li key={item}>{item}</li>)}</ul>
                  </div>
                </div>
                <p className="mt-4 rounded-2xl border border-[color:var(--color-accent-action-border)] bg-[color:var(--color-accent-action-soft)] p-3 text-sm font-semibold text-[color:var(--color-accent-action-muted)]">
                  Recommended experiment: {path.required_experiment_title}
                </p>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {section === "jobLoss" ? (
        <section className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
          <article className="glass-card p-5">
            <h2 className="font-display text-3xl font-semibold theme-text">I have lost my job.</h2>
            <p className="mt-3 text-sm leading-6 theme-muted">Sensitive fields are optional unless needed for preliminary source matching. No application is submitted to any authority.</p>
            <label className="mt-5 flex items-start gap-3 text-sm font-semibold theme-text">
              <input className="mt-1 h-4 w-4 accent-[color:var(--color-accent-action)]" type="checkbox" checked={jobConsent} onChange={(event) => setJobConsent(event.target.checked)} />
              Store job-loss information for this profile
            </label>
            <div className="mt-4 grid gap-3">
              <input className="organic-input" value={jobRegion} onChange={(event) => setJobRegion(event.target.value)} placeholder="Municipality or region" />
              <input className="organic-input" value={lastWorkingDate} onChange={(event) => setLastWorkingDate(event.target.value)} placeholder="Last working date" type="date" />
              <button type="button" className="organic-button" disabled={!jobConsent} onClick={() => void activateJobLossMode()}>
                <LifeBuoy size={16} /> Activate Job Loss Mode
              </button>
            </div>
            {jobLoss ? (
              <div className="mt-5 rounded-2xl border border-[color:var(--border-soft)] p-4 text-sm theme-muted">
                <p><b className="theme-text">Residence:</b> {jobLoss.country_of_residence}</p>
                <p><b className="theme-text">Employment:</b> {jobLoss.employment_status}</p>
                <p><b className="theme-text">Training interest:</b> {jobLoss.training_interest}</p>
              </div>
            ) : null}
          </article>
          <article className="glass-card p-5">
            <h2 className="font-display text-2xl font-semibold theme-text">Immediate actions and screening</h2>
            <div className="mt-4 grid gap-3">
              {(plan?.items || []).map((item) => (
                <div key={item.id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-bold theme-text">{item.title}</h3>
                      <p className="mt-2 text-sm theme-muted">{item.reason}</p>
                    </div>
                    <EvidenceLabel value={item.urgency} />
                  </div>
                  <a className="mt-3 inline-flex items-center gap-2 text-sm font-bold text-[color:var(--teal)]" href={item.official_source.url} target="_blank" rel="noreferrer">
                    Official source <ExternalLink size={14} />
                  </a>
                </div>
              ))}
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {(screening?.preliminary_result.programmes || []).slice(0, 6).map((programme) => (
                <div key={programme.programme_id} className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                  <h3 className="font-bold theme-text">{programme.programme_name}</h3>
                  <EvidenceLabel value={programme.preliminary_label} />
                  <p className="mt-2 text-sm theme-muted">{programme.explanation}</p>
                </div>
              ))}
            </div>
          </article>
        </section>
      ) : null}

      {section === "brief" ? (
        <section className="glass-card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-3xl font-semibold theme-text">Support Application Brief</h2>
              <p className="mt-2 text-sm theme-muted">{brief?.disclaimer || "This document supports preparation for a discussion with the relevant authority. It is not an eligibility decision or legal advice."}</p>
            </div>
            <button type="button" className="organic-button" onClick={() => void createSupportBrief(profileId).then((created) => setBrief(created))}>
              <FileText size={16} /> Generate Brief
            </button>
          </div>
          {brief ? (
            <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_0.8fr]">
              <article className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                <h3 className="font-bold theme-text">Brief content</h3>
                <div className="mt-4 grid gap-3 text-sm theme-muted">
                  {Object.entries(brief.content).map(([key, value]) => (
                    <div key={key} className="rounded-xl border border-[color:var(--border-soft)] p-3">
                      <b className="theme-text">{key.replace(/_/g, " ")}</b>
                      <p className="mt-1 break-words">{typeof value === "string" ? value : JSON.stringify(value)}</p>
                    </div>
                  ))}
                </div>
              </article>
              <article className="rounded-2xl border border-[color:var(--border-soft)] p-4">
                <h3 className="font-bold theme-text">Official-source references</h3>
                <div className="mt-3 grid gap-2">
                  {brief.official_source_references.map((source) => (
                    <a key={`${source.title}-${source.url}`} className="inline-flex items-center justify-between gap-2 rounded-xl border border-[color:var(--border-soft)] p-3 text-sm font-bold text-[color:var(--teal)]" href={source.url} target="_blank" rel="noreferrer">
                      {source.title}
                      <ExternalLink size={14} />
                    </a>
                  ))}
                </div>
                <h3 className="mt-5 font-bold theme-text">Unresolved questions</h3>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm theme-muted">
                  {brief.unresolved_questions.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </article>
            </div>
          ) : (
            <p className="mt-4 text-sm theme-muted">Generate a brief after support screening.</p>
          )}
        </section>
      ) : null}

      <section className="organic-section">
        <div className="flex flex-wrap items-center gap-3 text-sm theme-muted">
          <HeartHandshake className="text-[color:var(--teal)]" size={18} />
          <span>Current evidence suggests possible directions. Final eligibility is determined by the responsible authority.</span>
          <Link className="organic-button-secondary ml-auto" to={`${base}/support-brief`}>
            <FileText size={16} /> Support Brief
          </Link>
        </div>
      </section>
    </div>
  );
}
