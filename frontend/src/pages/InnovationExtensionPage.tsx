import {
  BookOpenCheck,
  Bot,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardCheck,
  ExternalLink,
  FileClock,
  History,
  Link2,
  MessageSquareText,
  PanelTop,
  RefreshCw,
  Save,
  ShieldAlert,
  UserRoundCheck,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  addPanelTurn,
  completePanelSimulation,
  confirmJobCapture,
  createAdvisorShare,
  createBrowserExtensionConnection,
  createDecisionJournalEntry,
  createJobCapture,
  createPanelSimulation,
  getAdvisorShares,
  getBrowserExtensionSettings,
  getCareerRoleComparison,
  getDecisionJournal,
  getDecisionJournalResearchExport,
  getJobCaptures,
  getPanelPersonas,
  getProfileCareerRoles,
  recordDecisionJournalOutcome,
  respondToAdvisorComment,
  revokeAdvisorShare,
  revokeBrowserExtensionConnection,
  saveCareerRoleHypothesis,
  startCareerRoleExperiment,
} from "../api/innovationExtensionApi";
import { useAppActions } from "../hooks/useAppActions";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";
import {
  advisorCommentStatus,
  advisorPermissionSummary,
  captureNeedsReview,
  careerFamilyCounts,
  extensionCapturePayload,
  journalStateSummary,
  normalisePanelFeedback,
  tokenExpiryLabel,
} from "../lib/innovationMapping";
import type {
  AdvisorComment,
  AdvisorShare,
  BrowserExtensionConnection,
  BrowserExtensionSettings,
  BrowserJobCapture,
  CareerRoleComparison,
  CareerRoleProfile,
  DecisionJournalEntry,
  PanelPersona,
  PanelSession,
} from "../types/innovationExtension";

function validProfileId(value?: string) {
  return value && !["undefined", "null"].includes(value) ? value : "";
}

function viewFromPath(pathname: string) {
  if (pathname.includes("/advisor-collaboration")) return "advisor";
  if (pathname.includes("/panel-simulation")) return "panel";
  if (pathname.includes("/career-encyclopedia") || pathname.startsWith("/careers")) return "careers";
  if (pathname.includes("/decision-journal")) return "journal";
  return "extension";
}

function arrayValue(value: unknown) {
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
}

function Panel({ title, icon, children, actions }: { title: string; icon: ReactNode; children: ReactNode; actions?: ReactNode }) {
  return (
    <section className="innovation-panel">
      <header className="innovation-panel__header">
        <div>
          <span className="innovation-panel__icon">{icon}</span>
          <h2>{title}</h2>
        </div>
        {actions ? <div className="innovation-actions">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}

function Pill({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "success" | "warning" | "danger" | "muted" }) {
  return <span className={`innovation-pill innovation-pill--${tone}`}>{children}</span>;
}

function Metric({ label, value, icon }: { label: string; value: string | number; icon: ReactNode }) {
  return (
    <article className="innovation-metric">
      <span>{icon}</span>
      <div>
        <b>{value}</b>
        <small>{label}</small>
      </div>
    </article>
  );
}

function tone(status: string): "default" | "success" | "warning" | "danger" | "muted" {
  if (/active|confirmed|analysed|accepted|ready|curated|recorded/i.test(status)) return "success";
  if (/need|pending|review|expires|partial/i.test(status)) return "warning";
  if (/reject|revoked|expired|blocked|duplicate/i.test(status)) return "danger";
  if (!status) return "muted";
  return "default";
}

function oneTimeToken(record: BrowserExtensionConnection | AdvisorShare | null) {
  if (!record) return "";
  if ("connection_token" in record) return record.connection_token || "";
  if ("share_token" in record) return record.share_token || "";
  return "";
}

export function InnovationExtensionPage() {
  const params = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const profileId = validProfileId(params.profileId || activeProfileId);
  const view = viewFromPath(location.pathname);
  const interviewId = params.interviewId;
  const selectedCareerSlug = params.careerSlug;

  const [settings, setSettings] = useState<BrowserExtensionSettings | null>(null);
  const [captures, setCaptures] = useState<BrowserJobCapture[]>([]);
  const [shares, setShares] = useState<AdvisorShare[]>([]);
  const [personas, setPersonas] = useState<PanelPersona[]>([]);
  const [panelSession, setPanelSession] = useState<PanelSession | null>(null);
  const [roles, setRoles] = useState<CareerRoleProfile[]>([]);
  const [comparison, setComparison] = useState<CareerRoleComparison | null>(null);
  const [journal, setJournal] = useState<DecisionJournalEntry[]>([]);
  const [researchExport, setResearchExport] = useState<Record<string, unknown> | null>(null);
  const [lastToken, setLastToken] = useState<BrowserExtensionConnection | AdvisorShare | null>(null);
  const [selectedFamily, setSelectedFamily] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const selectedRole = useMemo(() => roles.find((role) => role.slug === selectedCareerSlug) || roles[0] || null, [roles, selectedCareerSlug]);
  const latestCapture = captures[0] || null;
  const latestShare = shares[0] || null;
  const journalSummary = useMemo(() => journalStateSummary(journal), [journal]);
  const familyCounts = useMemo(() => careerFamilyCounts(roles), [roles]);
  const panelSummary = normalisePanelFeedback(panelSession);

  async function refresh() {
    if (!profileId) return;
    setLoading(true);
    setError("");
    const [settingsResult, capturesResult, sharesResult, personasResult, rolesResult, journalResult, exportResult] = await Promise.allSettled([
      getBrowserExtensionSettings(profileId),
      getJobCaptures(profileId),
      getAdvisorShares(profileId),
      getPanelPersonas(),
      getProfileCareerRoles(profileId, selectedFamily ? { family: selectedFamily } : {}),
      getDecisionJournal(profileId),
      getDecisionJournalResearchExport(profileId),
    ]);
    if (settingsResult.status === "fulfilled") setSettings(settingsResult.value);
    if (capturesResult.status === "fulfilled") setCaptures(capturesResult.value);
    if (sharesResult.status === "fulfilled") setShares(sharesResult.value);
    if (personasResult.status === "fulfilled") setPersonas(personasResult.value);
    if (rolesResult.status === "fulfilled") setRoles(rolesResult.value);
    if (journalResult.status === "fulfilled") setJournal(journalResult.value);
    if (exportResult.status === "fulfilled") setResearchExport(exportResult.value);
    const failed = [settingsResult, capturesResult, sharesResult, personasResult, rolesResult, journalResult, exportResult].filter((item) => item.status === "rejected").length;
    setError(failed ? `${failed} innovation panel(s) could not load. Available sections remain usable.` : "");
    setLoading(false);
  }

  useEffect(() => {
    if (!profileId) return;
    setActiveProfileId(profileId);
    refresh().catch(() => {
      setLoading(false);
      setError("Innovation Extension data could not be loaded.");
    });
  }, [profileId, selectedFamily, setActiveProfileId]);

  async function handleConnectExtension() {
    const connection = await createBrowserExtensionConnection(profileId, { display_name: "Save to OrganicAI Compass" });
    setLastToken(connection);
    setStatus("Extension connection token created. It is shown once and can be revoked.");
    await refresh();
  }

  async function handleRevokeConnection(connection: BrowserExtensionConnection) {
    await revokeBrowserExtensionConnection(profileId, connection.id);
    setStatus("Extension connection revoked.");
    await refresh();
  }

  async function handleSimulateCapture() {
    const payload = extensionCapturePayload({
      sourceUrl: "https://jobs.example.test/roles/ai-product-designer",
      pageTitle: "AI Product Designer - Aurora Learning Lab",
      capturedText: "Mandatory requirements include UX design, responsible AI, accessibility, evaluation, stakeholder communication and portfolio evidence.",
      selectedText: "UX design, responsible AI, accessibility and evaluation.",
    });
    const capture = await createJobCapture(profileId, payload);
    setStatus(capture.status === "Duplicate" ? "Duplicate capture detected by URL and content hash." : "Demo browser capture saved.");
    await refresh();
  }

  async function handleConfirmCapture(capture: BrowserJobCapture) {
    const confirmed = await confirmJobCapture(profileId, capture.id, { title: capture.detected_title || "Captured job", employer: capture.detected_employer, analyse: true });
    setStatus(`Capture confirmed. Job analysis ${confirmed.job_analysis_id ? "created" : "pending"}.`);
    await refresh();
    if (confirmed.job_analysis_id) navigate(`/workspace/${profileId}/job-analyzer/${confirmed.job_analysis_id}`);
  }

  async function handleCreateAdvisorShare() {
    const share = await createAdvisorShare(profileId, {
      adviser_display_name: "Dr. Ingrid Solheim",
      adviser_role: "Academic supervisor",
      purpose: "Review selected career hypothesis, Evidence Passport, Job Analysis and journal entries.",
      permission_level: "Suggest changes",
      allowed_sections: ["Career Hypotheses", "Evidence Passport", "Job Analysis", "Career Decision Journal"],
      allowed_actions: ["view", "comment", "suggest_changes", "validate_selected_evidence"],
      access_days: 14,
    });
    setLastToken(share);
    setStatus("Temporary adviser share link created.");
    await refresh();
  }

  async function handleCommentResponse(comment: AdvisorComment, next: "accepted" | "rejected") {
    await respondToAdvisorComment(profileId, comment.id, {
      status: next,
      user_response: next === "accepted" ? "Accepted as human-adviser feedback. Profile facts still require separate user confirmation." : "Rejected for this decision.",
    });
    setStatus(`Advisor suggestion ${next}. Profile and Evidence Passport were not changed automatically.`);
    await refresh();
  }

  async function handleRevokeShare(share: AdvisorShare) {
    await revokeAdvisorShare(profileId, share.id);
    setStatus("Adviser share revoked.");
    await refresh();
  }

  async function handleCreatePanel() {
    if (!interviewId) {
      setStatus("Open a specific interview before creating a panel simulation.");
      return;
    }
    const session = await createPanelSimulation(interviewId, {
      personas: ["recruiter", "hiring_manager", "technical_lead"],
      delivery_mode: "text",
      sequence_mode: "round_robin",
      duration_minutes: 30,
      difficulty: "moderate",
      follow_up_questions_enabled: true,
    });
    setPanelSession(session);
    setStatus("Panel simulation created with Recruiter, Hiring Manager and Technical Lead.");
  }

  async function handlePanelTurn() {
    if (!panelSession?.questions.length) return;
    const question = panelSession.questions[panelSession.turns.length % panelSession.questions.length];
    await addPanelTurn(panelSession.id, {
      question_id: question.id,
      persona_id: question.persona_id,
      answer_text: "I would answer with a project example, explain my specific contribution, name the evidence, and state the limitation instead of claiming unverified production experience.",
      response_duration_seconds: 72,
    });
    const next = await completePanelSimulation(panelSession.id, { user_reflection: "The panel highlighted the need for stronger technical evidence.", transcript_confirmed: true });
    setPanelSession(next);
    setStatus("Panel turn recorded and persona-specific feedback refreshed.");
  }

  async function handleCompareRole(role: CareerRoleProfile) {
    const result = await getCareerRoleComparison(profileId, role.slug);
    setComparison(result);
    setStatus(`Compared ${role.title} with profile evidence across four fit dimensions.`);
  }

  async function handleCareerAction(action: "hypothesis" | "experiment" | "journal", role: CareerRoleProfile) {
    if (action === "hypothesis") await saveCareerRoleHypothesis(profileId, role.slug);
    if (action === "experiment") await startCareerRoleExperiment(profileId, role.slug);
    if (action === "journal") {
      await createDecisionJournalEntry(profileId, {
        title: `Decision: test ${role.title}`,
        decision_summary: `Add ${role.title} to the decision journal for evidence-based review.`,
        career_slug: role.slug,
        assumptions: [{ text: "This career is worth testing through a small experiment.", status: "untested" }],
        review_date: "2026-08-15",
      });
    }
    setStatus(action === "experiment" ? "Career experiment started. Roadmap insertion still requires separate confirmation." : "Career action saved.");
    await refresh();
  }

  async function handleCreateJournal() {
    await createDecisionJournalEntry(profileId, {
      title: "Choose next evidence-building direction",
      decision_summary: "Test AI Product Designer against RAG Application Developer using evidence, market links and adviser feedback.",
      context: "Decision created from the Innovation Extension workbench.",
      selected_option: "AI Product Designer",
      options: [{ label: "AI Product Designer" }, { label: "RAG Application Developer" }],
      assumptions: [{ text: "Design evidence is stronger today.", state: "testing" }],
      evidence_links: latestCapture?.job_analysis_id ? [{ type: "job_analysis", id: latestCapture.job_analysis_id }] : [],
      review_date: "2026-08-15",
    });
    setStatus("Decision journal entry created with version 1.");
    await refresh();
  }

  async function handleRecordOutcome(entry: DecisionJournalEntry) {
    await recordDecisionJournalOutcome(profileId, entry.id, {
      outcome_status: "recorded",
      expected_outcome: "The option would clarify the next evidence gap.",
      actual_outcome: "The review exposed one technical-evidence gap and preserved the original decision version.",
      assumptions_disconfirmed: ["Existing API evidence was not strong enough."],
      next_decision_needed: true,
    });
    setStatus("Outcome recorded. My Roadmap was not changed automatically.");
    await refresh();
  }

  const tabs = [
    ["extension", "Browser Extension", `/workspace/${profileId}/integrations/browser-extension`, <Bot size={16} />],
    ["advisor", "Advisor", `/workspace/${profileId}/advisor-collaboration`, <UserRoundCheck size={16} />],
    ["careers", "Careers", `/workspace/${profileId}/career-encyclopedia`, <BookOpenCheck size={16} />],
    ["journal", "Decision Journal", `/workspace/${profileId}/decision-journal`, <FileClock size={16} />],
    ["panel", "Panel Interview", interviewId ? `/workspace/${profileId}/interviews/${interviewId}/panel-simulation` : `/workspace/${profileId}/interviews`, <PanelTop size={16} />],
  ] as const;

  if (!profileId) return <ProfileRequiredState title="Create your profile before opening browser extension integrations." />;

  return (
    <main className="innovation-page organic-page">
      <header className="innovation-header">
        <div>
          <p className="innovation-eyebrow">Innovation Extension Pack</p>
          <h1>Traceable job capture, adviser review, panel practice, career roles and decisions</h1>
          <p>Human-AI-adviser collaboration remains limited, temporary, evidence-aware and under user control.</p>
        </div>
        <aside className="innovation-metrics">
          <Metric label="Captures" value={captures.length} icon={<BriefcaseBusiness size={18} />} />
          <Metric label="Adviser shares" value={shares.length} icon={<UserRoundCheck size={18} />} />
          <Metric label="Career roles" value={roles.length} icon={<BookOpenCheck size={18} />} />
          <Metric label="Journal entries" value={journal.length} icon={<FileClock size={18} />} />
        </aside>
      </header>

      <nav className="innovation-tabs" aria-label="Innovation extension modules">
        {tabs.map(([key, label, to, icon]) => (
          <Link key={key} className={view === key ? "organic-button" : "organic-button-secondary"} to={to}>
            {icon}
            {label}
          </Link>
        ))}
      </nav>

      {(status || error || loading) ? (
        <div className="innovation-notices" aria-live="polite">
          {status ? <p><CheckCircle2 size={16} /> {status}</p> : null}
          {error ? <p className="innovation-notice-error"><ShieldAlert size={16} /> {error}</p> : null}
          {loading ? <p><RefreshCw size={16} /> Loading innovation records</p> : null}
        </div>
      ) : null}

      {lastToken && oneTimeToken(lastToken) ? (
        <Panel title="One-Time Token" icon={<Link2 size={20} />}>
          <pre className="innovation-token">{oneTimeToken(lastToken)}</pre>
          {"review_url" in lastToken && lastToken.review_url ? <Link className="organic-button-secondary" to={lastToken.review_url}><ExternalLink size={16} /> Open adviser review</Link> : null}
        </Panel>
      ) : null}

      {view === "extension" ? (
        <div className="innovation-grid innovation-grid--main">
          <Panel title="Save to OrganicAI Compass" icon={<Bot size={20} />} actions={<button className="organic-button" type="button" onClick={handleConnectExtension}><Link2 size={16} /> Connect extension</button>}>
            <div className="innovation-metric-grid">
              <Metric label="Connected" value={settings?.connected ? "yes" : "no"} icon={<CheckCircle2 size={18} />} />
              <Metric label="Last capture" value={settings?.connections.find((item) => item.last_capture)?.last_capture?.status || "none"} icon={<History size={18} />} />
              <Metric label="Permissions" value={settings?.privacy.permissions.length || 0} icon={<ShieldAlert size={18} />} />
            </div>
            <div className="innovation-source-box">
              <b>Privacy boundary</b>
              <p>{settings?.privacy_explanation || "Capture is user-triggered and excludes browser history, cookies, passwords, form contents and raw DOM snapshots."}</p>
            </div>
            <div className="innovation-list">
              {(settings?.connections || []).map((connection) => (
                <article className="innovation-row" key={connection.id}>
                  <div>
                    <b>{connection.display_name}</b>
                    <p>{connection.status} - {tokenExpiryLabel(connection.expires_at)} - last used {connection.last_used_at ? new Date(connection.last_used_at).toLocaleString() : "never"}</p>
                    <div className="innovation-chip-row">{connection.permissions.map((permission) => <span key={permission}>{permission}</span>)}</div>
                  </div>
                  <button className="organic-button-secondary" type="button" onClick={() => handleRevokeConnection(connection)}><XCircle size={16} /> Revoke</button>
                </article>
              ))}
            </div>
          </Panel>
          <Panel title="Captured Jobs" icon={<BriefcaseBusiness size={20} />} actions={<button className="organic-button" type="button" onClick={handleSimulateCapture}><Save size={16} /> Submit demo capture</button>}>
            <div className="innovation-list">
              {captures.map((capture) => (
                <article className="innovation-row" key={capture.id}>
                  <div>
                    <div className="innovation-row-title">
                      <b>{capture.detected_title || capture.page_title || "Untitled capture"}</b>
                      <Pill tone={tone(capture.status)}>{capture.status}</Pill>
                    </div>
                    <p>{capture.detected_employer || "Employer not identified"} - {capture.source_domain}</p>
                    <p>{capture.captured_text_preview}</p>
                    {captureNeedsReview(capture) ? <small>{capture.quality_warnings[0] || "Review captured content before saving."}</small> : null}
                  </div>
                  <button className="organic-button-secondary" type="button" onClick={() => handleConfirmCapture(capture)}><ClipboardCheck size={16} /> Confirm and analyse</button>
                </article>
              ))}
              {!captures.length ? <p className="innovation-empty">No browser captures yet.</p> : null}
            </div>
          </Panel>
        </div>
      ) : null}

      {view === "advisor" ? (
        <div className="innovation-grid innovation-grid--main">
          <Panel title="Advisor Collaboration" icon={<UserRoundCheck size={20} />} actions={<button className="organic-button" type="button" onClick={handleCreateAdvisorShare}><Link2 size={16} /> Create temporary share</button>}>
            <div className="innovation-list">
              {shares.map((share) => {
                const summary = advisorPermissionSummary(share);
                return (
                  <article className="innovation-row" key={share.id}>
                    <div>
                      <div className="innovation-row-title">
                        <b>{share.adviser_display_name}</b>
                        <Pill tone={tone(share.status)}>{share.status}</Pill>
                      </div>
                      <p>{share.adviser_role} - {summary.label} - {tokenExpiryLabel(share.expires_at)}</p>
                      <div className="innovation-chip-row">
                        {share.allowed_sections.map((section) => <span key={section}>{section}</span>)}
                      </div>
                    </div>
                    <button className="organic-button-secondary" type="button" onClick={() => handleRevokeShare(share)}><XCircle size={16} /> Revoke</button>
                  </article>
                );
              })}
              {!shares.length ? <p className="innovation-empty">No adviser shares have been created.</p> : null}
            </div>
          </Panel>
          <Panel title="Advisor Comments" icon={<MessageSquareText size={20} />}>
            <div className="innovation-list">
              {(latestShare?.comments || []).map((comment) => {
                const current = advisorCommentStatus(comment);
                return (
                  <article className="innovation-row" key={comment.id}>
                    <div>
                      <div className="innovation-row-title">
                        <b>{comment.suggestion_type}</b>
                        <Pill tone={current.tone}>{current.label}</Pill>
                      </div>
                      <p>{comment.comment_text}</p>
                      <small>{comment.evidence_validation} - {comment.provenance}</small>
                    </div>
                    <div className="innovation-actions">
                      <button className="organic-button-secondary" type="button" onClick={() => handleCommentResponse(comment, "accepted")}><CheckCircle2 size={16} /> Accept</button>
                      <button className="organic-button-secondary" type="button" onClick={() => handleCommentResponse(comment, "rejected")}><XCircle size={16} /> Reject</button>
                    </div>
                  </article>
                );
              })}
              {!latestShare?.comments.length ? <p className="innovation-empty">Adviser suggestions appear here after submission.</p> : null}
            </div>
          </Panel>
        </div>
      ) : null}

      {view === "panel" ? (
        <div className="innovation-grid innovation-grid--main">
          <Panel title="Multi-Persona Panel" icon={<PanelTop size={20} />} actions={<button className="organic-button" type="button" onClick={handleCreatePanel}><PanelTop size={16} /> Create panel</button>}>
            <div className="innovation-persona-grid">
              {personas.slice(0, 8).map((persona) => (
                <article className="innovation-card" key={persona.persona_id}>
                  <h3>{persona.role_label}</h3>
                  <p>{persona.purpose}</p>
                  <div className="innovation-chip-row">{persona.question_categories.slice(0, 4).map((item) => <span key={item}>{item}</span>)}</div>
                </article>
              ))}
            </div>
          </Panel>
          <Panel title="Persona Feedback" icon={<ClipboardCheck size={20} />} actions={panelSession ? <button className="organic-button" type="button" onClick={handlePanelTurn}><Save size={16} /> Answer one turn</button> : null}>
            {panelSession ? (
              <>
                <div className="innovation-metric-grid">
                  <Metric label="Personas" value={panelSummary.personaCount || (panelSession.panel_config.personas as unknown[] | undefined)?.length || 0} icon={<UserRoundCheck size={18} />} />
                  <Metric label="Unsupported claims" value={panelSummary.unsupportedClaimCount} icon={<ShieldAlert size={18} />} />
                  <Metric label="Opaque score" value={panelSummary.hasOpaqueScore ? "present" : "absent"} icon={<CheckCircle2 size={18} />} />
                </div>
                <div className="innovation-list">
                  {panelSession.questions.map((question) => (
                    <article className="innovation-row" key={question.id}>
                      <div>
                        <b>{question.persona_label}</b>
                        <p>{question.question_text}</p>
                        <small>{question.source_type} - {question.related_job_requirement || "no requirement"}</small>
                      </div>
                    </article>
                  ))}
                </div>
              </>
            ) : <p className="innovation-empty">Create a panel from an existing interview route.</p>}
          </Panel>
        </div>
      ) : null}

      {view === "careers" ? (
        <div className="innovation-grid innovation-grid--main">
          <Panel title="Career Encyclopedia" icon={<BookOpenCheck size={20} />}>
            <div className="innovation-filter-row">
              <label>
                Career family
                <select value={selectedFamily} onChange={(event) => setSelectedFamily(event.target.value)}>
                  <option value="">All families</option>
                  {Object.keys(familyCounts).map((family) => <option key={family} value={family}>{family}</option>)}
                </select>
              </label>
            </div>
            <div className="innovation-role-grid">
              {roles.map((role) => (
                <Link key={role.slug} className="innovation-card innovation-card--link" to={location.pathname.startsWith("/careers") ? `/careers/${role.slug}` : `/workspace/${profileId}/career-encyclopedia/${role.slug}`}>
                  <h3>{role.title}</h3>
                  <p>{role.summary}</p>
                  <Pill>{role.career_family}</Pill>
                </Link>
              ))}
            </div>
          </Panel>
          <Panel title={selectedRole?.title || "Role Profile"} icon={<BookOpenCheck size={20} />}>
            {selectedRole ? (
              <>
                <p className="innovation-lead">{selectedRole.summary}</p>
                <div className="innovation-chip-row">
                  {arrayValue(selectedRole.profile.technical_skills).slice(0, 8).map((skill) => <span key={skill}>{skill}</span>)}
                </div>
                <h3>Responsibilities</h3>
                <ul className="innovation-list-text">
                  {arrayValue(selectedRole.profile.typical_responsibilities).map((item) => <li key={item}>{item}</li>)}
                </ul>
                <h3>Accountability</h3>
                <ul className="innovation-list-text">
                  {arrayValue(selectedRole.profile.tasks_requiring_human_accountability).map((item) => <li key={item}>{item}</li>)}
                </ul>
                <div className="innovation-actions">
                  <button className="organic-button-secondary" type="button" onClick={() => handleCompareRole(selectedRole)}><ClipboardCheck size={16} /> Compare</button>
                  <button className="organic-button-secondary" type="button" onClick={() => handleCareerAction("experiment", selectedRole)}><Save size={16} /> Test career</button>
                  <button className="organic-button-secondary" type="button" onClick={() => handleCareerAction("hypothesis", selectedRole)}><CheckCircle2 size={16} /> Save hypothesis</button>
                  <button className="organic-button-secondary" type="button" onClick={() => handleCareerAction("journal", selectedRole)}><FileClock size={16} /> Add to journal</button>
                </div>
                {comparison ? (
                  <div className="innovation-fit-grid">
                    {Object.entries(comparison.fit_dimensions).map(([label, value]) => (
                      <span key={label}>
                        <b>{label}</b>
                        {value.label}
                      </span>
                    ))}
                  </div>
                ) : null}
              </>
            ) : <p className="innovation-empty">No role profile selected.</p>}
          </Panel>
        </div>
      ) : null}

      {view === "journal" ? (
        <div className="innovation-grid innovation-grid--main">
          <Panel title="Career Decision Journal" icon={<FileClock size={20} />} actions={<button className="organic-button" type="button" onClick={handleCreateJournal}><Save size={16} /> Create decision</button>}>
            <div className="innovation-metric-grid">
              <Metric label="Active" value={journalSummary.active} icon={<FileClock size={18} />} />
              <Metric label="Outcomes" value={journalSummary.outcomes} icon={<CheckCircle2 size={18} />} />
              <Metric label="Reconsidered" value={journalSummary.reconsidered} icon={<RefreshCw size={18} />} />
              <Metric label="Adviser-linked" value={journalSummary.adviserRelated} icon={<UserRoundCheck size={18} />} />
            </div>
            <div className="innovation-list">
              {journal.map((entry) => (
                <article className="innovation-row" key={entry.id}>
                  <div>
                    <div className="innovation-row-title">
                      <b>{entry.title}</b>
                      <Pill tone={tone(entry.status)}>{entry.status}</Pill>
                    </div>
                    <p>{entry.decision_summary}</p>
                    <small>v{entry.version_number} - review {entry.review_date || "not scheduled"} - roadmap mutation {entry.roadmap_mutation_allowed ? "allowed" : "blocked"}</small>
                  </div>
                  <button className="organic-button-secondary" type="button" onClick={() => handleRecordOutcome(entry)}><History size={16} /> Record outcome</button>
                </article>
              ))}
              {!journal.length ? <p className="innovation-empty">No decision journal entries yet.</p> : null}
            </div>
          </Panel>
          <Panel title="Research Export Filter" icon={<ShieldAlert size={20} />}>
            <pre className="innovation-token">{JSON.stringify(researchExport, null, 2)}</pre>
          </Panel>
        </div>
      ) : null}
    </main>
  );
}
