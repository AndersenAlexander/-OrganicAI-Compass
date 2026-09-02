import {
  BadgeCheck,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardCheck,
  Database,
  Download,
  FileLock2,
  FileText,
  FlaskConical,
  Gauge,
  MapPinned,
  RefreshCw,
  Save,
  Search,
  Send,
  ShieldAlert,
  WandSparkles,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  addApplicationStage,
  calculateJobAnalysisReadiness,
  consentToResearch,
  createApplication,
  createApplicationDocument,
  createJobAnalysis,
  createResearchExport,
  createResearchSession,
  exportApplicationDocument,
  getApplicationDocuments,
  getApplications,
  getJobAnalyses,
  getMarketProviderStatus,
  getMarketRadar,
  getResearchEvaluation,
  matchJobAnalysis,
  recordApplicationOutcome,
  recalibrateApplication,
  saveMarketJob,
  submitResearchMetrics,
  submitResearchResponses,
  syncDemoMarketProvider,
  updateDocumentClaim,
  updateJobRequirement,
  updateMarketPreferences,
  withdrawResearchConsent,
} from "../api/marketApplicationApi";
import { useAppActions } from "../hooks/useAppActions";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";
import { analysisCanCreateDocuments, buildLikertResponses, readinessTone } from "../lib/marketApplicationMapping";
import type {
  ApplicationDocument,
  DocumentClaim,
  JobAnalysis,
  JobApplication,
  JobRequirement,
  MarketJob,
  MarketRadar,
  ProviderStatusResponse,
  ResearchEvaluation,
} from "../types/marketApplication";

function validProfileId(value?: string) {
  return value && !["undefined", "null"].includes(value) ? value : "";
}

function routeSection(pathname: string) {
  if (pathname.includes("/job-analyzer")) return "analyzer";
  if (pathname.includes("/application-studio")) return "studio";
  if (pathname.includes("/applications")) return "applications";
  if (pathname.includes("/research-evaluation")) return "research";
  return "radar";
}

function Panel({ title, icon, children, actions }: { title: string; icon: ReactNode; children: ReactNode; actions?: ReactNode }) {
  return (
    <section className="market-panel">
      <header className="market-panel__header">
        <div>
          <span className="market-panel__icon">{icon}</span>
          <h2>{title}</h2>
        </div>
        {actions ? <div className="market-panel__actions">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}

function Pill({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "success" | "warning" | "danger" | "muted" }) {
  return <span className={`market-pill market-pill--${tone}`}>{children}</span>;
}

function Metric({ label, value, icon }: { label: string; value: string | number; icon: ReactNode }) {
  return (
    <article className="market-metric">
      <span>{icon}</span>
      <div>
        <b>{value}</b>
        <small>{label}</small>
      </div>
    </article>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="market-empty">{text}</p>;
}

function allSettledValue<T>(result: PromiseSettledResult<T>, fallback: T): T {
  return result.status === "fulfilled" ? result.value : fallback;
}

function JobCard({ job, onAnalyze, onSave }: { job: MarketJob; onAnalyze: (job: MarketJob) => void; onSave: (job: MarketJob) => void }) {
  return (
    <article className="market-job">
      <div className="market-job__top">
        <div>
          <h3>{job.title}</h3>
          <p>{job.employer || "Employer not shown"} - {job.location || job.municipality || job.country}</p>
        </div>
        <Pill tone={job.is_active ? "success" : "muted"}>{job.is_active ? "Active" : job.inactive_reason || "Inactive"}</Pill>
      </div>
      <div className="market-job__meta">
        <Pill>{job.provider}</Pill>
        <Pill>{job.work_mode || "work mode not stated"}</Pill>
        <Pill>{job.employment_type || "employment type not stated"}</Pill>
        <Pill tone="warning">{job.recommendation?.readiness_label || "Needs analysis"}</Pill>
      </div>
      <p className="market-job__reason">{job.recommendation?.reason || "Run Job Analyzer to compare requirements against Evidence Passport records."}</p>
      <div className="market-skill-row">
        {job.skills.slice(0, 6).map((skill) => <span key={skill}>{skill}</span>)}
      </div>
      <div className="market-button-row">
        <button className="organic-button-secondary" type="button" onClick={() => onSave(job)}>
          <Save size={16} /> Save
        </button>
        <button className="organic-button" type="button" onClick={() => onAnalyze(job)} disabled={!job.is_active}>
          <Search size={16} /> Analyze
        </button>
      </div>
    </article>
  );
}

function RequirementList({ requirements, onCorrect }: { requirements: JobRequirement[]; onCorrect: (requirement: JobRequirement) => void }) {
  if (!requirements.length) return <EmptyState text="No requirements have been extracted yet." />;
  return (
    <div className="market-list">
      {requirements.map((requirement) => (
        <article className="market-row" key={requirement.id}>
          <div>
            <div className="market-row__title">
              <b>{requirement.requirement_text}</b>
              <Pill tone={requirement.requirement_type === "mandatory" ? "warning" : "muted"}>{requirement.requirement_type}</Pill>
            </div>
            <p>{requirement.requirement_category} - {requirement.confidence} extraction - {requirement.user_confirmation_state}</p>
            {requirement.matches.length ? (
              <div className="market-match-grid">
                {requirement.matches.slice(0, 2).map((match) => (
                  <span key={match.id}>
                    <b>{match.match_category}</b>
                    {match.deterministic_reason || match.recommended_action}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
          <button className="organic-button-secondary" type="button" onClick={() => onCorrect(requirement)}>
            <ClipboardCheck size={16} /> Correct
          </button>
        </article>
      ))}
    </div>
  );
}

function DocumentCard({ document, onUseSaferClaim, onExport }: { document: ApplicationDocument; onUseSaferClaim: (claim: DocumentClaim) => void; onExport: (document: ApplicationDocument) => void }) {
  const blocked = document.claims.filter((claim) => claim.blocked_for_export || claim.status === "Blocked");
  const unresolved = document.claims.filter((claim) => claim.status === "Unverified");
  return (
    <article className="market-document">
      <div className="market-row__title">
        <h3>{document.title}</h3>
        <Pill tone={document.evidence_lock_status.includes("Evidence locked") ? "success" : "warning"}>{document.evidence_lock_status}</Pill>
      </div>
      <p>{document.document_type.replace("_", " ")} - {document.readiness_status} - {document.versions.length} versions</p>
      <div className="market-document__sections">
        {document.sections.slice(0, 4).map((section) => (
          <span key={section.id}>
            <b>{section.title}</b>
            {section.content}
          </span>
        ))}
      </div>
      <div className="market-list market-list--compact">
        {document.claims.slice(0, 5).map((claim) => (
          <div className="market-claim" key={claim.id}>
            <div>
              <Pill tone={claim.status === "Blocked" ? "danger" : claim.status === "Supported" ? "success" : "warning"}>{claim.status}</Pill>
              <p>{claim.claim_text}</p>
              {claim.safer_alternative ? <small>Safer alternative: {claim.safer_alternative}</small> : null}
            </div>
            {claim.safer_alternative ? (
              <button className="organic-button-secondary" type="button" onClick={() => onUseSaferClaim(claim)}>
                <ShieldAlert size={16} /> Use safer
              </button>
            ) : null}
          </div>
        ))}
      </div>
      <div className="market-button-row">
        <Pill tone={blocked.length ? "danger" : unresolved.length ? "warning" : "success"}>
          {blocked.length ? `${blocked.length} blocked` : unresolved.length ? `${unresolved.length} unverified` : "claims reviewed"}
        </Pill>
        <button className="organic-button" type="button" onClick={() => onExport(document)}>
          <Download size={16} /> Export with review
        </button>
      </div>
    </article>
  );
}

function ApplicationCard({ application }: { application: JobApplication }) {
  return (
    <article className="market-application-card">
      <div className="market-row__title">
        <h3>{application.title}</h3>
        <Pill tone={["Offer", "Recruiter screening", "Interview 1", "Interview 2"].includes(application.status) ? "success" : application.status === "Rejected" ? "danger" : "default"}>{application.status}</Pill>
      </div>
      <p>{application.organisation || "Organisation not set"} - {application.source} - deadline {application.deadline || "not stated"}</p>
      <div className="market-timeline">
        {application.events.slice(-4).map((event) => (
          <span key={event.id}>
            <b>{event.event_type}</b>
            {event.description || event.to_status}
          </span>
        ))}
      </div>
      {application.recalibration ? (
        <div className="market-recalibration">
          <b>Recalibration suggestions require confirmation</b>
          {application.recalibration.suggestions.slice(0, 2).map((suggestion) => <p key={suggestion.suggestion_type}>{suggestion.label}</p>)}
        </div>
      ) : null}
    </article>
  );
}

export function MarketApplicationPage() {
  const params = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const profileId = validProfileId(params.profileId || activeProfileId);
  const section = routeSection(location.pathname);
  const analysisId = params.analysisId;
  const applicationId = params.applicationId;

  const [providerStatus, setProviderStatus] = useState<ProviderStatusResponse | null>(null);
  const [radar, setRadar] = useState<MarketRadar | null>(null);
  const [analyses, setAnalyses] = useState<JobAnalysis[]>([]);
  const [documents, setDocuments] = useState<ApplicationDocument[]>([]);
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [research, setResearch] = useState<ResearchEvaluation | null>(null);
  const [municipality, setMunicipality] = useState("Oslo");
  const [query, setQuery] = useState("");
  const [pastedAd, setPastedAd] = useState(
    "Human-centred AI Product Designer. Mandatory requirements include UX design, responsible AI, accessibility, evaluation, and clear communication. Preferred requirements include RAG, APIs, Norwegian, English, and portfolio evidence."
  );
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [exportPreview, setExportPreview] = useState<Record<string, unknown> | null>(null);

  // An action that writes data must stay tied to an explicit route identity.
  // A sole record is unambiguous; with several records the user must choose a
  // card or a route instead of silently acting on whichever record was listed first.
  const selectedAnalysis = useMemo(
    () => (analysisId ? analyses.find((item) => item.id === analysisId) || null : analyses.length === 1 ? analyses[0] : null),
    [analyses, analysisId]
  );
  const selectedApplication = useMemo(
    () => (applicationId ? applications.find((item) => item.id === applicationId) || null : applications.length === 1 ? applications[0] : null),
    [applications, applicationId]
  );
  const analysisDocuments = useMemo(
    () => selectedAnalysis ? documents.filter((document) => document.job_analysis_id === selectedAnalysis.id || !document.job_analysis_id) : [],
    [documents, selectedAnalysis]
  );
  const cvDocument = analysisDocuments.find((document) => document.document_type === "cv");
  const coverLetter = analysisDocuments.find((document) => document.document_type === "cover_letter");

  async function refresh(nextQuery = query, nextMunicipality = municipality) {
    if (!profileId) return;
    setLoading(true);
    setError("");
    const [providerResult, radarResult, analysesResult, docsResult, appsResult, researchResult] = await Promise.allSettled([
      getMarketProviderStatus(),
      getMarketRadar(profileId, { query: nextQuery || undefined, municipality: nextMunicipality || undefined, active_only: true, limit: 24 }),
      getJobAnalyses(profileId),
      getApplicationDocuments(profileId),
      getApplications(profileId),
      section === "research" ? getResearchEvaluation(profileId) : Promise.resolve(null),
    ]);
    setProviderStatus(allSettledValue(providerResult, null));
    setRadar(allSettledValue(radarResult, null));
    setAnalyses(allSettledValue(analysesResult, []));
    setDocuments(allSettledValue(docsResult, []));
    setApplications(allSettledValue(appsResult, []));
    setResearch(allSettledValue(researchResult, null));
    const failed = [providerResult, radarResult, analysesResult, docsResult, appsResult, ...(section === "research" ? [researchResult] : [])]
      .filter((item) => item.status === "rejected").length;
    setError(failed ? `${failed} market workflow panel(s) could not load. Available panels are still shown.` : "");
    setLoading(false);
  }

  useEffect(() => {
    if (!profileId) return;
    setActiveProfileId(profileId);
    refresh().catch(() => {
      setLoading(false);
      setError("Market-aware application data could not be loaded.");
    });
  }, [profileId, section, setActiveProfileId]);

  async function handleRefreshDemoFeed() {
    await syncDemoMarketProvider();
    setStatus("Demo market feed refreshed with idempotent provider records.");
    await refresh();
  }

  async function handleSavePreferences() {
    await updateMarketPreferences(profileId, {
      country: "Norway",
      municipality,
      commuting_area: municipality,
      radius_km: 50,
      work_modes: ["hybrid", "remote"],
      preferred_languages: ["English", "Norwegian"],
      career_families: ["human_centred_ai", "ai_product", "ux_research"],
      user_confirmed_storage: true,
    });
    setStatus("Market preferences stored after explicit confirmation. No precise address was saved.");
    await refresh(query, municipality);
  }

  async function handleAnalyzeJob(job?: MarketJob) {
    const created = await createJobAnalysis(profileId, job ? { job_id: job.id, input_type: "saved_job" } : {
      input_type: "pasted_text",
      pasted_text: pastedAd,
      title: "Pasted AI product role",
      organisation: "Manual import",
      location: municipality || "Norway",
    });
    await matchJobAnalysis(profileId, created.id);
    await calculateJobAnalysisReadiness(profileId, created.id);
    setStatus("Job analysis created with deterministic evidence matching and readiness.");
    await refresh(query, municipality);
    navigate(`/workspace/${profileId}/job-analyzer/${created.id}`);
  }

  async function handleCorrectRequirement(requirement: JobRequirement) {
    await updateJobRequirement(profileId, requirement.id, {
      requirement_text: `${requirement.requirement_text} (user-confirmed interpretation)`,
      requirement_type: requirement.requirement_type,
      user_confirmation_state: "confirmed",
      change_reason: "User corrected the deterministic extraction.",
    });
    if (selectedAnalysis) {
      await matchJobAnalysis(profileId, selectedAnalysis.id);
      await calculateJobAnalysisReadiness(profileId, selectedAnalysis.id);
    }
    setStatus("Requirement correction saved and analysis readiness recalculated.");
    await refresh(query, municipality);
  }

  async function handleCreateDocuments() {
    if (!selectedAnalysis) return;
    const cv = await createApplicationDocument(profileId, { job_analysis_id: selectedAnalysis.id, document_type: "cv", language: "en" });
    await createApplicationDocument(profileId, { job_analysis_id: selectedAnalysis.id, document_type: "cover_letter", language: "en" });
    setStatus("Evidence-locked CV and cover letter drafts created.");
    await refresh(query, municipality);
    navigate(`/workspace/${profileId}/application-studio/${selectedAnalysis.id}`, { state: { documentId: cv.id } });
  }

  async function handleUseSaferClaim(claim: DocumentClaim) {
    await updateDocumentClaim(profileId, claim.id, {
      claim_text: claim.safer_alternative || claim.claim_text,
      status: "User-confirmed",
      user_confirmation_state: "confirmed",
    });
    setStatus("Safer claim wording applied. Export readiness was recalculated.");
    await refresh(query, municipality);
  }

  async function handleExportDocument(document: ApplicationDocument) {
    const result = await exportApplicationDocument(profileId, document.id, true);
    setExportPreview(result as Record<string, unknown>);
    setStatus("Document export generated as HTML plus structured JSON. The platform did not submit the application.");
    await refresh(query, municipality);
  }

  async function handleCreateApplication() {
    if (!selectedAnalysis) return;
    const app = await createApplication(profileId, {
      job_id: selectedAnalysis.job_id,
      job_analysis_id: selectedAnalysis.id,
      cv_document_id: cvDocument?.id,
      cover_letter_document_id: coverLetter?.id,
      status: "Preparing",
      title: selectedAnalysis.title,
      organisation: selectedAnalysis.organisation,
      source: selectedAnalysis.input_type,
    });
    setStatus("Application tracker record created. No external application was submitted.");
    await refresh(query, municipality);
    navigate(`/workspace/${profileId}/applications/${app.id}`);
  }

  async function handleOutcomeLoop() {
    if (!selectedApplication) return;
    await addApplicationStage(profileId, selectedApplication.id, {
      stage_type: "recruiter",
      result: "screening_completed",
      feedback: "User-recorded outcome. Treat as observed data, not causal proof.",
    });
    await recordApplicationOutcome(profileId, selectedApplication.id, {
      outcome: "Recruiter screening",
      outcome_date: new Date().toISOString().slice(0, 10),
      feedback_confirmed: false,
      user_interpretation: "Reached recruiter screening in the recorded tracker sample.",
    });
    await recalibrateApplication(profileId, selectedApplication.id);
    setStatus("Outcome recorded and recalibration suggestions prepared. My Roadmap was not changed automatically.");
    await refresh(query, municipality);
  }

  async function handleSaveJob(job: MarketJob) {
    await saveMarketJob(profileId, job.id);
    setStatus("Job saved to Application Tracker. It remains a local tracker record.");
    await refresh(query, municipality);
  }

  async function handleResearchRun() {
    if (!research) return;
    await consentToResearch(research.study.id, profileId);
    const session = await createResearchSession(research.study.id, profileId, "post_test", "experimental") as { id: string };
    const responses = buildLikertResponses(research, "post_test");
    await submitResearchResponses(profileId, session.id, responses);
    await submitResearchMetrics(profileId, session.id, [
      { metric_name: "job_analysed", metric_value: analyses.length ? 1 : 0, workflow_stage: "post_test" },
      { metric_name: "application_document_created", metric_value: documents.length ? 1 : 0, workflow_stage: "post_test" },
      { metric_name: "application_outcome_recorded", metric_value: applications.some((item) => item.outcome) ? 1 : 0, workflow_stage: "post_test" },
    ]);
    const exportRun = await createResearchExport(research.study.id, false);
    setExportPreview(exportRun as Record<string, unknown>);
    setStatus("Research session and pseudonymous export preview created. Demo records are excluded by default.");
    await refresh(query, municipality);
  }

  async function handleWithdrawConsent() {
    if (!research) return;
    await withdrawResearchConsent(research.study.id, profileId);
    setStatus("Research consent withdrawn. Future exports exclude the participant unless consent is restored.");
    await refresh(query, municipality);
  }

  if (!profileId) return <ProfileRequiredState title="Create your profile before opening Market and Applications." />;

  const activeProvider = providerStatus?.providers.find((provider) => provider.provider_name === providerStatus.active_provider) || providerStatus?.providers[0];
  const tabs = [
    ["radar", "Market Radar", `/workspace/${profileId}/market-radar`, <BarChart3 size={16} />],
    ["analyzer", "Job Analyzer", `/workspace/${profileId}/job-analyzer`, <Search size={16} />],
    ["studio", "Application Studio", `/workspace/${profileId}/application-studio/${selectedAnalysis?.id || analysisId || "latest"}`, <FileLock2 size={16} />],
    ["applications", "Tracker", `/workspace/${profileId}/applications`, <BriefcaseBusiness size={16} />],
    ["research", "Research", `/workspace/${profileId}/research-evaluation`, <FlaskConical size={16} />],
  ] as const;

  return (
    <main className="market-application-page organic-page">
      <header className="market-workbench-header">
        <div>
          <p className="market-eyebrow">Market-aware application journey</p>
          <h1>Applications grounded in evidence and observed market data</h1>
          <p>
            This workspace connects the OrganicAI profile, Evidence Passport, market observations, job-ad analysis,
            evidence-locked documents, outcome tracking, and academic evaluation exports.
          </p>
        </div>
        <aside>
          <Metric label="Provider" value={activeProvider?.display_name || "Demo market"} icon={<Database size={18} />} />
          <Metric label="Provider state" value={activeProvider?.status || "loading"} icon={<Gauge size={18} />} />
          <Metric label="Live mode" value={providerStatus?.live_enabled ? "enabled" : "demo/fallback"} icon={<ShieldAlert size={18} />} />
        </aside>
      </header>

      <nav className="market-tabs" aria-label="Market application workflow">
        {tabs.map(([key, label, to, icon]) => (
          <Link key={key} className={section === key ? "organic-button" : "organic-button-secondary"} to={to}>
            {icon}
            {label}
          </Link>
        ))}
      </nav>

      {(status || error || providerStatus?.warning) ? (
        <div className="market-notices" aria-live="polite">
          {status ? <p><CheckCircle2 size={16} /> {status}</p> : null}
          {error ? <p className="market-notice-error"><ShieldAlert size={16} /> {error}</p> : null}
          {providerStatus?.warning ? <p><ShieldAlert size={16} /> {providerStatus.warning}</p> : null}
        </div>
      ) : null}

      {section === "radar" ? (
        <div className="market-grid market-grid--main">
          <Panel
            title="Market Radar"
            icon={<MapPinned size={20} />}
            actions={<button className="organic-button-secondary" type="button" onClick={handleRefreshDemoFeed}><RefreshCw size={16} /> Refresh demo feed</button>}
          >
            <div className="market-filter-row">
              <label>
                Region or municipality
                <input value={municipality} onChange={(event) => setMunicipality(event.target.value)} placeholder="Oslo" />
              </label>
              <label>
                Search terms
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="AI, UX, RAG" />
              </label>
              <button className="organic-button" type="button" onClick={() => refresh(query, municipality)} disabled={loading}>
                <Search size={16} /> Apply filters
              </button>
              <button className="organic-button-secondary" type="button" onClick={handleSavePreferences}>
                <BadgeCheck size={16} /> Confirm preferences
              </button>
            </div>
            <div className="market-metric-grid">
              <Metric label="Current active opportunities" value={radar?.active_jobs.length || 0} icon={<BriefcaseBusiness size={18} />} />
              <Metric label="Recurring requirement signals" value={radar?.recurring_requirements.length || 0} icon={<BarChart3 size={18} />} />
              <Metric label="Emerging observed signals" value={radar?.emerging_observed_requirements.length || 0} icon={<WandSparkles size={18} />} />
            </div>
            <div className="market-source-box">
              <b>Data source and coverage</b>
              <p>{radar?.signal_run.coverage_label || "Waiting for provider data."}</p>
              <small>Trend labels are based only on the observed local dataset and are not predictions.</small>
            </div>
            <div className="market-job-grid">
              {(radar?.active_jobs || []).map((job) => <JobCard key={job.id} job={job} onAnalyze={handleAnalyzeJob} onSave={handleSaveJob} />)}
              {!radar?.active_jobs.length ? <EmptyState text="No active jobs match the current filters." /> : null}
            </div>
          </Panel>
          <Panel title="Requirements And Locations" icon={<BarChart3 size={20} />}>
            <h3>Recurring requirements</h3>
            <div className="market-signal-list">
              {(radar?.recurring_requirements || []).slice(0, 8).map((signal) => (
                <span key={signal.id}>
                  <b>{signal.label}</b>
                  {signal.trend_label} - {signal.observation_count} observed
                </span>
              ))}
            </div>
            <h3>Emerging observed requirements</h3>
            <div className="market-signal-list">
              {(radar?.emerging_observed_requirements || []).slice(0, 6).map((signal) => (
                <span key={signal.id}>
                  <b>{signal.label}</b>
                  {signal.confidence_label} - not a forecast
                </span>
              ))}
            </div>
            <h3>Location and language</h3>
            <div className="market-skill-row">
              {(radar?.location_language.municipalities || []).slice(0, 5).map((item) => <span key={item.label}>{item.label}: {item.count}</span>)}
              {(radar?.location_language.languages || []).slice(0, 5).map((item) => <span key={item.label}>{item.label}: {item.count}</span>)}
            </div>
            <h3>Market limitations</h3>
            <ul className="market-limit-list">
              {(radar?.limitations || []).map((item) => <li key={item}>{item}</li>)}
            </ul>
          </Panel>
        </div>
      ) : null}

      {section === "analyzer" ? (
        <div className="market-grid market-grid--main">
          <Panel title="Job Analyzer" icon={<Search size={20} />} actions={<button className="organic-button" type="button" onClick={() => handleAnalyzeJob()}><WandSparkles size={16} /> Analyze pasted ad</button>}>
            <label className="market-textarea-label">
              Paste job ad text
              <textarea value={pastedAd} onChange={(event) => setPastedAd(event.target.value)} />
            </label>
            <div className="market-job-grid">
              {(radar?.active_jobs || []).slice(0, 4).map((job) => <JobCard key={job.id} job={job} onAnalyze={handleAnalyzeJob} onSave={handleSaveJob} />)}
            </div>
          </Panel>
          <Panel
            title={selectedAnalysis ? selectedAnalysis.title : "Analysis Results"}
            icon={<ClipboardCheck size={20} />}
            actions={analysisCanCreateDocuments(selectedAnalysis) ? <button className="organic-button" type="button" onClick={handleCreateDocuments}><FileText size={16} /> Create documents</button> : null}
          >
            {selectedAnalysis ? (
              <>
                <div className="market-readiness-band">
                  <Pill tone={readinessTone(selectedAnalysis.readiness?.readiness_label)}>{selectedAnalysis.readiness?.readiness_label || "Readiness pending"}</Pill>
                  <span>{selectedAnalysis.extraction_version}</span>
                </div>
                <RequirementList requirements={selectedAnalysis.requirements} onCorrect={handleCorrectRequirement} />
              </>
            ) : <EmptyState text="Analyze a saved or pasted job ad to extract requirements." />}
          </Panel>
        </div>
      ) : null}

      {section === "studio" ? (
        <div className="market-grid market-grid--main">
          <Panel title="Application Studio" icon={<FileLock2 size={20} />} actions={<button className="organic-button" type="button" onClick={handleCreateApplication} disabled={!selectedAnalysis}><Send size={16} /> Create tracker record</button>}>
            <div className="market-readiness-band">
              <Pill>{selectedAnalysis?.title || "No selected job analysis"}</Pill>
              <span>CV Evidence Lock blocks unsupported factual claims until they are corrected or explicitly acknowledged.</span>
            </div>
            <div className="market-document-grid">
              {analysisDocuments.map((document) => <DocumentCard key={document.id} document={document} onUseSaferClaim={handleUseSaferClaim} onExport={handleExportDocument} />)}
              {!analysisDocuments.length ? (
                <button className="organic-button" type="button" onClick={handleCreateDocuments} disabled={!selectedAnalysis}>
                  <FileText size={16} /> Create evidence-locked CV and cover letter
                </button>
              ) : null}
            </div>
          </Panel>
          <Panel title="Export Preview" icon={<Download size={20} />}>
            {exportPreview ? (
              <pre className="market-export-preview">{JSON.stringify(exportPreview, null, 2).slice(0, 2200)}</pre>
            ) : (
              <EmptyState text="Export creates local HTML and structured JSON only. Auto-apply and ATS guarantees are disabled." />
            )}
          </Panel>
        </div>
      ) : null}

      {section === "applications" ? (
        <div className="market-grid market-grid--main">
          <Panel title="Application Tracker" icon={<BriefcaseBusiness size={20} />} actions={<button className="organic-button" type="button" onClick={handleOutcomeLoop} disabled={!selectedApplication}><RefreshCw size={16} /> Record outcome loop</button>}>
            <div className="market-application-grid">
              {applications.map((application) => (
                <Link key={application.id} to={`/workspace/${profileId}/applications/${application.id}`}>
                  <ApplicationCard application={application} />
                </Link>
              ))}
              {!applications.length ? <EmptyState text="Create an application record from Application Studio or save a market job." /> : null}
            </div>
          </Panel>
          <Panel title="Outcome Recalibration" icon={<Gauge size={20} />}>
            {selectedApplication?.recalibration ? (
              <div className="market-recalibration market-recalibration--large">
                <b>Suggestions only</b>
                <p>Roadmap changes require explicit confirmation and are not applied automatically.</p>
                {selectedApplication.recalibration.suggestions.map((suggestion) => <span key={suggestion.suggestion_type}>{suggestion.label}</span>)}
              </div>
            ) : (
              <EmptyState text="Record stages and outcomes to generate recalibration suggestions." />
            )}
          </Panel>
        </div>
      ) : null}

      {section === "research" ? (
        <div className="market-grid market-grid--main">
          <Panel title="Research Evaluation" icon={<FlaskConical size={20} />} actions={<button className="organic-button" type="button" onClick={handleResearchRun} disabled={!research}><FlaskConical size={16} /> Run demo evaluation</button>}>
            <div className="market-research-summary">
              <Metric label="Study status" value={research?.study.status || "loading"} icon={<FlaskConical size={18} />} />
              <Metric label="Questions" value={research?.study.questions.length || 0} icon={<ClipboardCheck size={18} />} />
              <Metric label="Export schema" value={research?.study.export_schema_version || "v1"} icon={<Database size={18} />} />
            </div>
            <div className="market-source-box">
              <b>Consent and withdrawal</b>
              <p>{String(research?.consent_template.plain_language_summary || "Research data is consent-based, pseudonymous, and excludes raw personal text from exports.")}</p>
              <button className="organic-button-secondary" type="button" onClick={handleWithdrawConsent} disabled={!research}>
                <ShieldAlert size={16} /> Withdraw consent
              </button>
            </div>
            <div className="market-question-grid">
              {(research?.study.questions || []).slice(0, 8).map((question) => (
                <span key={question.id}>
                  <b>{question.construct}</b>
                  {question.prompt}
                </span>
              ))}
            </div>
          </Panel>
          <Panel title="Pseudonymous Export Preview" icon={<Database size={20} />}>
            {exportPreview ? (
              <pre className="market-export-preview">{JSON.stringify(exportPreview, null, 2).slice(0, 2200)}</pre>
            ) : (
              <EmptyState text="Exports include versioned surveys, interaction metrics, and outcomes; names, emails, raw CV text, and cover-letter text are excluded." />
            )}
          </Panel>
        </div>
      ) : null}
    </main>
  );
}
