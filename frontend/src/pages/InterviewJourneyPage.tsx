import {
  BadgeCheck,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  FileQuestion,
  Library,
  Mail,
  Mic,
  PanelTop,
  Play,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Star,
  WalletCards,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  buildInterviewAnswer,
  completeMockSession,
  createFollowUpDraft,
  createInterview,
  createMockSession,
  createOfferReview,
  createPreparationBrief,
  createReflection,
  createStarStory,
  evaluateStarStory,
  generateInterviewQuestions,
  getFollowUpDrafts,
  getInterview,
  getInterviewDashboard,
  getInterviewQuestions,
  getInterviewVoiceStatus,
  getInterviews,
  getMockSessions,
  getOfferReviews,
  getPreparationBrief,
  getReflection,
  getStarStories,
  recordInterviewApplicationEvent,
  saveInterviewQuestion,
  startMockSession,
  addMockTurn,
} from "../api/interviewJourneyApi";
import { getApplications } from "../api/marketApplicationApi";
import { useAppActions } from "../hooks/useAppActions";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";
import type { JobApplication } from "../types/marketApplication";
import type {
  AnswerBuilder,
  FollowUpDraft,
  Interview,
  InterviewDashboard,
  InterviewQuestion,
  InterviewReflection,
  MockInterviewSession,
  OfferReview,
  PreparationBrief,
  StarStory,
  VoiceStatus,
} from "../types/interviewJourney";

function validProfileId(value?: string) {
  return value && !["undefined", "null"].includes(value) ? value : "";
}

function viewFromPath(pathname: string) {
  if (pathname.includes("/star-stories")) return "stories";
  if (pathname.includes("/offer-review")) return "offer";
  if (pathname.includes("/mock")) return "mock";
  if (pathname.includes("/reflection")) return "reflection";
  if (pathname.includes("/prepare")) return "prepare";
  return "dashboard";
}

function allSettledValue<T>(result: PromiseSettledResult<T>, fallback: T): T {
  return result.status === "fulfilled" ? result.value : fallback;
}

function asLines(value: string) {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

function formatUnknown(value: unknown) {
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  if (value === null || value === undefined) return "";
  return JSON.stringify(value);
}

function Panel({ title, icon, children, actions }: { title: string; icon: ReactNode; children: ReactNode; actions?: ReactNode }) {
  return (
    <section className="interview-panel">
      <header className="interview-panel__header">
        <div>
          <span className="interview-panel__icon">{icon}</span>
          <h2>{title}</h2>
        </div>
        {actions ? <div className="interview-actions">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}

function Pill({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "success" | "warning" | "danger" | "muted" }) {
  return <span className={`interview-pill interview-pill--${tone}`}>{children}</span>;
}

function Metric({ label, value, icon }: { label: string; value: string | number; icon: ReactNode }) {
  return (
    <article className="interview-metric">
      <span>{icon}</span>
      <div>
        <b>{value}</b>
        <small>{label}</small>
      </div>
    </article>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="interview-empty">{text}</p>;
}

function statusTone(status: string): "default" | "success" | "warning" | "danger" | "muted" {
  if (/ready|completed|saved|supported|offer|next/i.test(status)) return "success";
  if (/need|missing|unknown|not started|review/i.test(status)) return "warning";
  if (/reject|blocked|danger/i.test(status)) return "danger";
  if (!status) return "muted";
  return "default";
}

function InterviewCard({ interview, profileId }: { interview: Interview; profileId: string }) {
  return (
    <article className="interview-card">
      <div className="interview-row-title">
        <div>
          <h3>{interview.role}</h3>
          <p>{interview.organisation || "Organisation not confirmed"}</p>
        </div>
        <Pill tone={statusTone(interview.preparation_status)}>{interview.stage_label}</Pill>
      </div>
      <div className="interview-meta">
        <span>{interview.scheduled_at ? new Date(interview.scheduled_at).toLocaleString() : "Date not confirmed"}</span>
        <span>{interview.interview_format || "format unknown"}</span>
        <span>{interview.application_status || "tracker not linked"}</span>
      </div>
      <div className="interview-check-strip">
        <Pill tone={statusTone(interview.preparation_status)}>Prep: {interview.preparation_status}</Pill>
        <Pill tone={statusTone(interview.mock_session_status)}>Mock: {interview.mock_session_status}</Pill>
        <Pill tone={interview.has_reflection ? "success" : "muted"}>{interview.has_reflection ? "Reflection saved" : "Reflection pending"}</Pill>
      </div>
      <div className="interview-actions">
        <Link className="organic-button-secondary" to={`/workspace/${profileId}/interviews/${interview.id}/prepare`}>
          <ClipboardList size={16} /> Prepare
        </Link>
        <Link className="organic-button-secondary" to={`/workspace/${profileId}/interviews/${interview.id}/mock`}>
          <Play size={16} /> Mock
        </Link>
        <Link className="organic-button-secondary" to={`/workspace/${profileId}/interviews/${interview.id}/reflection`}>
          <BadgeCheck size={16} /> Reflect
        </Link>
      </div>
    </article>
  );
}

function StoryCard({ story, onEvaluate }: { story: StarStory; onEvaluate: (story: StarStory) => void }) {
  return (
    <article className="interview-card">
      <div className="interview-row-title">
        <h3>{story.title}</h3>
        <Pill tone={statusTone(story.quality_status)}>{story.quality_status}</Pill>
      </div>
      <p>{story.action || story.situation}</p>
      <div className="interview-meta">
        <span>{story.confidentiality_status}</span>
        <span>{story.skills_demonstrated.slice(0, 3).join(", ") || "skills not linked"}</span>
        <span>{story.evidence_links.length ? `${story.evidence_links.length} evidence links` : "no evidence link"}</span>
      </div>
      <button className="organic-button-secondary" type="button" onClick={() => onEvaluate(story)}>
        <Star size={16} /> Evaluate
      </button>
    </article>
  );
}

function PreparationSection({ title, value }: { title: string; value: PreparationBrief["sections"][string] }) {
  const groups = [
    ["Confirmed facts", value?.confirmed_facts],
    ["Likely stage expectations", value?.likely_stage_expectations],
    ["AI-generated suggestions", value?.ai_generated_suggestions],
    ["User assumptions", value?.user_assumptions],
    ["Missing information", value?.missing_information],
  ] as const;
  return (
    <article className="interview-detail-box">
      <h3>{title.replace(/_/g, " ")}</h3>
      {groups.map(([label, items]) => items?.length ? (
        <div key={label}>
          <b>{label}</b>
          <ul>
            {items.slice(0, 5).map((item, index) => <li key={`${label}-${index}`}>{formatUnknown(item).slice(0, 260)}</li>)}
          </ul>
        </div>
      ) : null)}
      {value?.uncertainty_note ? <small>{value.uncertainty_note}</small> : null}
    </article>
  );
}

export function InterviewJourneyPage() {
  const params = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const profileId = validProfileId(params.profileId || activeProfileId);
  const interviewId = params.interviewId;
  const view = viewFromPath(location.pathname);

  const [dashboard, setDashboard] = useState<InterviewDashboard | null>(null);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [selectedApplicationId, setSelectedApplicationId] = useState("");
  const [selectedInterview, setSelectedInterview] = useState<Interview | null>(null);
  const [preparation, setPreparation] = useState<PreparationBrief | null>(null);
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [stories, setStories] = useState<StarStory[]>([]);
  const [mockSessions, setMockSessions] = useState<MockInterviewSession[]>([]);
  const [reflection, setReflection] = useState<InterviewReflection | null>(null);
  const [followUps, setFollowUps] = useState<FollowUpDraft[]>([]);
  const [offers, setOffers] = useState<OfferReview[]>([]);
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus | null>(null);
  const [answerDraft, setAnswerDraft] = useState("I work at the intersection of design, technology, and learning. A relevant example is a project where I designed an explainable recommendation interface, documented uncertainty, and tested the workflow locally with clear limitations.");
  const [reflectionText, setReflectionText] = useState("Tell me about yourself.\nWhy this role?");
  const [weakAnswers, setWeakAnswers] = useState("Salary priorities need a clearer answer.");
  const [offerSalary, setOfferSalary] = useState("650000");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [answerBuilder, setAnswerBuilder] = useState<AnswerBuilder | null>(null);

  const activeInterview = useMemo(
    () => selectedInterview || interviews.find((item) => item.id === interviewId) || null,
    [interviewId, interviews, selectedInterview]
  );
  const selectedApplication = useMemo(
    () => applications.find((item) => item.id === selectedApplicationId) || null,
    [applications, selectedApplicationId]
  );
  const latestSession = mockSessions[0] || null;

  async function refresh() {
    if (!profileId) return;
    setLoading(true);
    setError("");
    const [dashboardResult, interviewsResult, appsResult, storiesResult, voiceResult, offersResult] = await Promise.allSettled([
      getInterviewDashboard(profileId),
      getInterviews(profileId),
      getApplications(profileId),
      getStarStories(profileId),
      getInterviewVoiceStatus(),
      getOfferReviews(profileId),
    ]);
    const nextInterviews = allSettledValue(interviewsResult, []);
    setDashboard(allSettledValue(dashboardResult, null));
    setInterviews(nextInterviews);
    setApplications(allSettledValue(appsResult, []));
    setStories(allSettledValue(storiesResult, []));
    setVoiceStatus(allSettledValue(voiceResult, null));
    setOffers(allSettledValue(offersResult, []));

    const currentId = interviewId;
    if (currentId) {
      const [detailResult, prepResult, questionResult, mockResult, reflectionResult, followUpResult] = await Promise.allSettled([
        getInterview(currentId),
        getPreparationBrief(currentId),
        getInterviewQuestions(currentId),
        getMockSessions(currentId),
        getReflection(currentId),
        getFollowUpDrafts(currentId),
      ]);
      setSelectedInterview(allSettledValue(detailResult, nextInterviews.find((item) => item.id === currentId) || null));
      setPreparation(allSettledValue(prepResult, null));
      setQuestions(allSettledValue(questionResult, []));
      setMockSessions(allSettledValue(mockResult, []));
      setReflection(allSettledValue(reflectionResult, null));
      setFollowUps(allSettledValue(followUpResult, []));
    } else {
      setSelectedInterview(null);
      setPreparation(null);
      setQuestions([]);
      setMockSessions([]);
      setReflection(null);
      setFollowUps([]);
    }
    const failed = [dashboardResult, interviewsResult, appsResult, storiesResult, voiceResult, offersResult].filter((item) => item.status === "rejected").length;
    setError(failed ? `${failed} interview panel(s) could not load. Available panels remain usable.` : "");
    setLoading(false);
  }

  useEffect(() => {
    if (!profileId) return;
    setActiveProfileId(profileId);
    refresh().catch(() => {
      setLoading(false);
      setError("Interview Journey data could not be loaded.");
    });
  }, [profileId, interviewId, setActiveProfileId]);

  async function handleCreateFromApplication() {
    if (!selectedApplication) {
      setError("Select the saved application that this interview belongs to.");
      return;
    }
    const created = await createInterview(profileId, {
      application_id: selectedApplication.id,
      stage_type: "recruiter_screening",
      scheduled_at: "2026-07-25T10:00:00",
      timezone: "Europe/Bucharest",
      location_or_platform: "Video call",
      interview_format: "online",
      expected_duration_minutes: 30,
      participants: [{ role: "recruiter" }],
      source: "application",
      role: selectedApplication.title,
      organisation: selectedApplication.organisation,
      user_confirmed: true,
    });
    setStatus("Interview record created from the tracker. Application status was not changed automatically.");
    await refresh();
    navigate(`/workspace/${profileId}/interviews/${created.id}/prepare`);
  }

  async function handleCreateManualInterview() {
    const created = await createInterview(profileId, {
      stage_type: "recruiter_screening",
      scheduled_at: "2026-07-25T10:00:00",
      timezone: "Europe/Bucharest",
      location_or_platform: "Video call",
      interview_format: "online",
      expected_duration_minutes: 30,
      participants: [{ role: "recruiter" }],
      source: "manual",
      role: "Manual interview",
      organisation: "Organisation not confirmed",
      user_confirmed: true,
    });
    setStatus("Manual interview record created. It is not linked to an application.");
    await refresh();
    navigate(`/workspace/${profileId}/interviews/${created.id}/prepare`);
  }

  async function handlePrepare() {
    if (!activeInterview) return;
    const [briefResult, questionsResult] = await Promise.allSettled([
      createPreparationBrief(activeInterview.id, { language: "en", user_assumptions: ["Participant names are not required."] }),
      generateInterviewQuestions(activeInterview.id, { force: true }),
    ]);
    setPreparation(allSettledValue(briefResult, preparation));
    setQuestions(questionsResult.status === "fulfilled" ? questionsResult.value.questions : questions);
    setStatus("Preparation brief and plausible questions generated from confirmed context.");
    await refresh();
  }

  async function handleSaveQuestion(question: InterviewQuestion) {
    await saveInterviewQuestion(question.id, !question.saved_by_user);
    setStatus("Question save status updated for practice.");
    await refresh();
  }

  async function handleBuildAnswer(question: InterviewQuestion) {
    const answer = await buildInterviewAnswer(question.id, {
      user_draft: answerDraft,
      selected_evidence: question.related_evidence,
      user_confirmed: false,
    });
    setAnswerBuilder(answer);
    setStatus("Answer Builder checked draft claims using the Evidence Lock rules.");
  }

  async function handleCreateStory() {
    const story = await createStarStory(profileId, {
      title: "Interview-ready explainability story",
      situation: "A recommendation interface needed to explain why a career action was suggested.",
      task: "Create a truthful example that shows design, AI literacy, and responsible constraints.",
      action: "I designed states for evidence, uncertainty, correction, rejection, and alternative next steps.",
      result: "The prototype made the reasoning easier to review without claiming hiring success.",
      reflection: "I would add more user testing evidence before using this as a final portfolio story.",
      skills_demonstrated: ["ux_ui", "responsible_ai", "communication"],
      evidence_links: [{ source: "demo", relationship: "supports" }],
      tags: ["communication", "user_centred_design", "career_transition"],
      confidentiality_status: "public",
      user_confirmed: true,
    });
    setStatus(`STAR story saved with quality status: ${story.quality_status}.`);
    await refresh();
  }

  async function handleEvaluateStory(story: StarStory) {
    const evaluated = await evaluateStarStory(story.id);
    setStatus(`STAR story evaluated: ${evaluated.quality_status}.`);
    await refresh();
  }

  async function handleRunMock() {
    if (!activeInterview) return;
    let activeQuestions = questions;
    if (!activeQuestions.length) {
      activeQuestions = (await generateInterviewQuestions(activeInterview.id, {})).questions;
      setQuestions(activeQuestions);
    }
    const created = await createMockSession(activeInterview.id, { mode: "guided_practice", delivery_mode: "text", persona: "recruiter" });
    const started = await startMockSession(created.id);
    const question = activeQuestions[0];
    await addMockTurn(started.id, {
      question_id: question?.id,
      question_text: question?.question_text,
      answer_text: answerDraft,
      response_duration_seconds: 82,
      attempt_number: 1,
    });
    const completed = await completeMockSession(started.id, { transcript_confirmed: true, transcript_retained: true, user_reflection: "Text practice completed." });
    setStatus("Text mock interview completed with rubric feedback. Voice was not required.");
    setMockSessions([completed]);
    await refresh();
  }

  async function handleSaveReflection() {
    if (!activeInterview) return;
    const saved = await createReflection(activeInterview.id, {
      completed_date: new Date().toISOString().slice(0, 10),
      questions_remembered: asLines(reflectionText),
      strong_answers: ["Evidence-based introduction"],
      weak_answers: asLines(weakAnswers),
      unexpected_topics: ["Notice period"],
      confirmed_interviewer_feedback: "",
      user_interpretation: "User reflection only. No rejection reason is inferred.",
      next_step: "prepare_next_stage",
      confidence_before: 3,
      confidence_after: 4,
      additional_evidence_needed: ["Clearer API project evidence"],
      outcome_status: "next_stage_received",
      user_confirmed: true,
      create_recalibration: true,
    });
    setReflection(saved);
    setStatus("Reflection saved with confirmed feedback separated from user interpretation.");
    await refresh();
  }

  async function handleCreateFollowUp() {
    if (!activeInterview) return;
    await createFollowUpDraft(activeInterview.id, { draft_type: "thank_you" });
    setStatus("Follow-up draft created locally. No email was sent.");
    await refresh();
  }

  async function handleConfirmApplicationStage() {
    if (!activeInterview) return;
    await recordInterviewApplicationEvent(activeInterview.id, {
      event_type: "interview_scheduled",
      confirm_status_update: true,
      description: "User confirmed the application status update from Interview Journey.",
    });
    setStatus("Application Tracker updated after explicit confirmation; prior history was preserved.");
    await refresh();
  }

  async function handleOfferReview() {
    const offer = await createOfferReview(profileId, {
      application_id: activeInterview?.application_id || selectedApplication?.id,
      interview_id: activeInterview?.id,
      salary: Number(offerSalary) || undefined,
      currency: "NOK",
      remote_hybrid_arrangement: "Hybrid",
      working_hours: "Full time",
      start_date: "2026-09-01",
      user_priorities: ["remote flexibility", "training support", "clear title"],
      source: "manual",
    });
    setStatus(`Offer review created with ${offer.review.missing_information?.length || 0} missing fields. No legal or tax conclusion was made.`);
    await refresh();
  }

  if (!profileId) return <ProfileRequiredState title="Create your profile before opening Interview Journey." />;

  const tabs = [
    ["dashboard", "Interviews", `/workspace/${profileId}/interviews`, <CalendarClock size={16} />],
    ["stories", "STAR Stories", `/workspace/${profileId}/star-stories`, <Library size={16} />],
    ["offer", "Offer Review", `/workspace/${profileId}/offer-review`, <WalletCards size={16} />],
  ] as const;
  const workflowTabs = activeInterview ? [
    ["prepare", "Prepare", `/workspace/${profileId}/interviews/${activeInterview.id}/prepare`, <ClipboardList size={16} />],
    ["mock", "Mock", `/workspace/${profileId}/interviews/${activeInterview.id}/mock`, <Mic size={16} />],
    ["reflection", "Reflection", `/workspace/${profileId}/interviews/${activeInterview.id}/reflection`, <BadgeCheck size={16} />],
  ] as const : [];

  return (
    <main className="interview-journey-page organic-page">
      <header className="interview-hero">
        <div>
          <p className="interview-eyebrow">Interview Journey</p>
          <h1>Evidence-based interview preparation and reflection</h1>
          <p>
            Prepare from Application Tracker, Job Analysis, Evidence Passport, CV Evidence Lock, STAR stories,
            text or optional voice mock sessions, and outcome-based recalibration.
          </p>
        </div>
        <aside className="interview-metric-grid">
          <Metric label="Upcoming" value={dashboard?.upcoming_interviews.length || 0} icon={<CalendarClock size={18} />} />
          <Metric label="STAR stories" value={stories.length} icon={<Library size={18} />} />
          <Metric label="Voice status" value={voiceStatus?.status || "loading"} icon={<Mic size={18} />} />
        </aside>
      </header>

      <nav className="interview-tabs" aria-label="Interview Journey sections">
        {tabs.map(([key, label, to, icon]) => (
          <Link key={key} className={view === key || (key === "dashboard" && ["prepare", "mock", "reflection"].includes(view)) ? "organic-button" : "organic-button-secondary"} to={to}>
            {icon}
            {label}
          </Link>
        ))}
        {workflowTabs.map(([key, label, to, icon]) => (
          <Link key={key} className={view === key ? "organic-button" : "organic-button-secondary"} to={to}>
            {icon}
            {label}
          </Link>
        ))}
      </nav>

      {(status || error || voiceStatus) ? (
        <div className="interview-notices" aria-live="polite">
          {status ? <p><CheckCircle2 size={16} /> {status}</p> : null}
          {error ? <p className="interview-notice-error"><ShieldAlert size={16} /> {error}</p> : null}
          {voiceStatus ? (
            <p>
              <ShieldAlert size={16} />
              Voice mock interview is {voiceStatus.enabled ? "enabled" : "disabled"}. Text mock interview remains available; provider keys are backend-only.
            </p>
          ) : null}
        </div>
      ) : null}

      {view === "dashboard" ? (
        <div className="interview-grid interview-grid--main">
          <Panel title="Interview Dashboard" icon={<PanelTop size={20} />} actions={<button className="organic-button-secondary" type="button" onClick={() => void refresh()} disabled={loading}><RefreshCw size={16} /> Refresh</button>}>
            <div className="interview-actions interview-actions--start">
              <label className="interview-textarea-label interview-textarea-label--compact">
                Application for this interview
                <select aria-label="Application for this interview" value={selectedApplicationId} onChange={(event) => setSelectedApplicationId(event.target.value)}>
                  <option value="">Select a saved application</option>
                  {applications.map((application) => <option key={application.id} value={application.id}>{application.title} — {application.organisation}</option>)}
                </select>
              </label>
              <button className="organic-button" type="button" onClick={handleCreateFromApplication} disabled={!selectedApplication}>
                <BriefcaseBusiness size={16} /> Create from tracker
              </button>
              <button className="organic-button-secondary" type="button" onClick={handleCreateManualInterview}>
                <CalendarClock size={16} /> Add manual interview
              </button>
            </div>
            <div className="interview-card-grid">
              {interviews.map((interview) => <InterviewCard key={interview.id} interview={interview} profileId={profileId} />)}
              {!interviews.length ? <EmptyState text="No interviews yet. Create one from the Application Tracker or add a manual interview." /> : null}
            </div>
          </Panel>
          <Panel title="Next Action And Gaps" icon={<Sparkles size={20} />}>
            <div className="interview-source-box">
              <b>Next recommended action</b>
              <p>{dashboard?.next_recommended_action || "Create or select an interview to begin preparation."}</p>
            </div>
            <h3>Unresolved evidence gaps</h3>
            <div className="interview-chip-grid">
              {(dashboard?.unresolved_evidence_gaps || []).slice(0, 8).map((gap) => <span key={gap.label}>{gap.label} ({gap.count})</span>)}
              {!dashboard?.unresolved_evidence_gaps.length ? <span>No repeated evidence gaps loaded.</span> : null}
            </div>
            <h3>Source notes</h3>
            <ul className="interview-list">
              {(dashboard?.source_notes || []).map((note) => <li key={note}>{note}</li>)}
            </ul>
          </Panel>
        </div>
      ) : null}

      {view === "prepare" ? (
        <div className="interview-grid interview-grid--main">
          <Panel title="Preparation Brief" icon={<ClipboardList size={20} />} actions={<button className="organic-button" type="button" onClick={handlePrepare}><Sparkles size={16} /> Generate preparation</button>}>
            {activeInterview ? <InterviewCard interview={activeInterview} profileId={profileId} /> : <EmptyState text="Select or create an interview first." />}
            {preparation ? (
              <>
                <div className="interview-checklist">
                  {preparation.readiness_checklist.map((item) => (
                    <span key={item.label}><b>{item.status}</b>{item.label}{item.optional ? " (optional)" : ""}</span>
                  ))}
                </div>
                <div className="interview-detail-grid">
                  {Object.entries(preparation.sections).slice(0, 8).map(([key, value]) => <PreparationSection key={key} title={key} value={value} />)}
                </div>
              </>
            ) : <EmptyState text="Generate a preparation brief to separate confirmed facts, likely expectations, user assumptions, and missing information." />}
          </Panel>
          <Panel title="Plausible Questions" icon={<FileQuestion size={20} />}>
            <div className="interview-question-list">
              {questions.map((question) => (
                <article className="interview-question" key={question.id}>
                  <div className="interview-row-title">
                    <h3>{question.category}</h3>
                    <Pill tone={question.risk_level === "high" ? "warning" : "default"}>{question.source_type}</Pill>
                  </div>
                  <p>{question.question_text}</p>
                  <small>{question.why_it_may_be_asked}</small>
                  <div className="interview-actions">
                    <button className="organic-button-secondary" type="button" onClick={() => handleSaveQuestion(question)}>
                      <Star size={16} /> {question.saved_by_user ? "Unsave" : "Save"}
                    </button>
                    <button className="organic-button-secondary" type="button" onClick={() => handleBuildAnswer(question)}>
                      <ClipboardList size={16} /> Build answer
                    </button>
                  </div>
                </article>
              ))}
              {!questions.length ? <EmptyState text="Generate questions from the preparation panel." /> : null}
            </div>
          </Panel>
        </div>
      ) : null}

      {view === "mock" ? (
        <div className="interview-grid interview-grid--main">
          <Panel title="Text Mock Interview" icon={<Mic size={20} />} actions={<button className="organic-button" type="button" onClick={handleRunMock}><Play size={16} /> Run text mock</button>}>
            <label className="interview-textarea-label">
              Practice answer
              <textarea value={answerDraft} onChange={(event) => setAnswerDraft(event.target.value)} />
            </label>
            {answerBuilder ? (
              <div className="interview-source-box">
                <b>Answer Builder</b>
                <p>{answerBuilder.risk_areas.join(" ") || "Draft has no blocked claim warnings."}</p>
                {answerBuilder.claim_statuses.map((claim, index) => <Pill key={`${claim.status}-${index}`} tone={statusTone(claim.status)}>{claim.status}</Pill>)}
              </div>
            ) : null}
            {latestSession ? (
              <div className="interview-detail-grid">
                <article className="interview-detail-box">
                  <h3>Feedback</h3>
                  <p>{latestSession.feedback.suggested_next_practice || "Feedback appears after a mock turn is completed."}</p>
                  <b>No opaque total score: {latestSession.feedback.no_single_opaque_score ? "yes" : "pending"}</b>
                </article>
                <article className="interview-detail-box">
                  <h3>Rubric</h3>
                  {latestSession.rubric_results.slice(0, 6).map((item) => <p key={item.criterion}>{item.criterion}: {item.average_score}/4</p>)}
                </article>
              </div>
            ) : <EmptyState text="Run a text mock interview. Voice is optional and disabled by default." />}
          </Panel>
          <Panel title="Follow-Up Readiness" icon={<FileQuestion size={20} />}>
            {latestSession?.turns.flatMap((turn) => turn.follow_up_questions).slice(0, 6).map((question) => <p className="interview-follow-up" key={question}>{question}</p>)}
            {!latestSession ? <EmptyState text="Follow-up questions are generated from missing detail, unsupported results, ownership, trade-offs, and reflection." /> : null}
          </Panel>
        </div>
      ) : null}

      {view === "reflection" ? (
        <div className="interview-grid interview-grid--main">
          <Panel title="Post-Interview Reflection" icon={<BadgeCheck size={20} />} actions={<button className="organic-button" type="button" onClick={handleSaveReflection}><BadgeCheck size={16} /> Save reflection</button>}>
            <label className="interview-textarea-label">
              Questions remembered
              <textarea value={reflectionText} onChange={(event) => setReflectionText(event.target.value)} />
            </label>
            <label className="interview-textarea-label">
              Weak answers or evidence gaps
              <textarea value={weakAnswers} onChange={(event) => setWeakAnswers(event.target.value)} />
            </label>
            {reflection ? (
              <div className="interview-source-box">
                <b>Reflection saved</b>
                <p>Confirmed feedback: {reflection.confirmed_interviewer_feedback || "none recorded"}</p>
                <p>User interpretation: {reflection.user_interpretation}</p>
              </div>
            ) : null}
          </Panel>
          <Panel title="Tracker And Follow-Up" icon={<Mail size={20} />}>
            <div className="interview-actions interview-actions--start">
              <button className="organic-button-secondary" type="button" onClick={handleCreateFollowUp}>
                <Mail size={16} /> Draft thank-you
              </button>
              <button className="organic-button" type="button" onClick={handleConfirmApplicationStage}>
                <BriefcaseBusiness size={16} /> Confirm tracker update
              </button>
            </div>
            {followUps.map((draft) => (
              <article className="interview-detail-box" key={draft.id}>
                <h3>{draft.subject}</h3>
                <p>{draft.body}</p>
                <Pill tone="muted">{draft.auto_sent ? "sent" : "not sent automatically"}</Pill>
              </article>
            ))}
            {!followUps.length ? <EmptyState text="Create a follow-up draft locally. Emails are not sent automatically." /> : null}
          </Panel>
        </div>
      ) : null}

      {view === "stories" ? (
        <div className="interview-grid interview-grid--main">
          <Panel title="STAR Story Library" icon={<Library size={20} />} actions={<button className="organic-button" type="button" onClick={handleCreateStory}><Star size={16} /> Add demo story</button>}>
            <div className="interview-card-grid">
              {stories.map((story) => <StoryCard key={story.id} story={story} onEvaluate={handleEvaluateStory} />)}
              {!stories.length ? <EmptyState text="No STAR stories yet. Add one from confirmed facts or create one manually." /> : null}
            </div>
          </Panel>
          <Panel title="Quality Rules" icon={<ShieldAlert size={20} />}>
            <ul className="interview-list">
              <li>Stories are evaluated deterministically for situation, task ownership, action specificity, result evidence, relevance, conciseness, reflection, and confidentiality.</li>
              <li>Unsupported metrics remain blocked until evidence-linked or user-confirmed.</li>
              <li>AI may suggest structure, but complete fictional stories are not generated.</li>
            </ul>
          </Panel>
        </div>
      ) : null}

      {view === "offer" ? (
        <div className="interview-grid interview-grid--main">
          <Panel title="Offer Review" icon={<WalletCards size={20} />} actions={<button className="organic-button" type="button" onClick={handleOfferReview}><WalletCards size={16} /> Review offer</button>}>
            {!activeInterview ? <label className="interview-textarea-label interview-textarea-label--compact">
              Application to link
              <select aria-label="Application to link to offer review" value={selectedApplicationId} onChange={(event) => setSelectedApplicationId(event.target.value)}>
                <option value="">Create an unlinked comparison</option>
                {applications.map((application) => <option key={application.id} value={application.id}>{application.title} — {application.organisation}</option>)}
              </select>
            </label> : null}
            <label className="interview-textarea-label interview-textarea-label--compact">
              Salary
              <input value={offerSalary} onChange={(event) => setOfferSalary(event.target.value)} />
            </label>
            <div className="interview-card-grid">
              {offers.map((offer) => (
                <article className="interview-card" key={offer.id}>
                  <div className="interview-row-title">
                    <h3>{offer.role || "Offer review"}</h3>
                    <Pill>{offer.status}</Pill>
                  </div>
                  <p>{offer.organisation || "Organisation not set"}</p>
                  <div className="interview-chip-grid">
                    {(offer.review.missing_information || []).slice(0, 6).map((item) => <span key={item}>Missing: {item}</span>)}
                    {(offer.review.draft_negotiation_points || []).slice(0, 3).map((item) => <span key={item}>{item}</span>)}
                  </div>
                  <small>No tax calculation or legal compliance conclusion is provided.</small>
                </article>
              ))}
              {!offers.length ? <EmptyState text="Enter known offer facts and priorities to create a review." /> : null}
            </div>
          </Panel>
          <Panel title="Negotiation Limits" icon={<ShieldAlert size={20} />}>
            <ul className="interview-list">
              <li>Confirmed offer facts are separated from missing information.</li>
              <li>Negotiation points are drafts and remain user-reviewable.</li>
              <li>The system does not provide definitive legal, tax, or financial advice.</li>
            </ul>
          </Panel>
        </div>
      ) : null}
    </main>
  );
}
