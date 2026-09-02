import {
  BarChart3,
  BookOpenCheck,
  CheckCircle2,
  ClipboardList,
  FileClock,
  FlaskConical,
  GitCompare,
  History,
  RefreshCw,
  Save,
  Scale,
  ShieldCheck,
  SlidersHorizontal,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  acceptAdaptiveExperiment,
  addTransitionPathToDecisionJournal,
  analyseAdaptiveExperiments,
  archiveTransitionSimulation,
  compareTransitionScenarios,
  createTransitionSimulation,
  getAdaptiveEvidenceCapture,
  getAdaptiveExperiments,
  getEvidenceGaps,
  getFairnessTestSuites,
  getRecommendationProvenance,
  getFairnessAudits,
  getRecommendationRobustness,
  getRecommendationSystemCard,
  getTransitionPresets,
  getTransitionSimulations,
  proposeTransitionPathRoadmap,
  recordAdaptiveExperimentOutcome,
  reviewAdaptiveEvidenceCapture,
  rejectAdaptiveExperiment,
  runFairnessAudit,
  runRecommendationRobustness,
  runTransitionSimulation,
  saveAdaptiveExperiment,
  startAdaptiveExperiment,
  updateTransitionSimulationConstraints,
} from "../api/originalityResearchApi";
import { useAppActions } from "../hooks/useAppActions";
import { ProfileRequiredState } from "../components/shared/ProfileRequiredState";
import {
  actionAriaLabel,
  constraintSummary,
  dependencyWarnings,
  fairnessStatusTone,
  fairnessSummary,
  objectiveRows,
  paretoPathStatus,
  provenanceTimeline,
  recommendationBandTone,
  rejectionReasonLabel,
  robustnessTone,
  scoreComponentRows,
  sensitivityMatrixSummary,
  simulationSummary,
  uncertaintyCategorySummary,
} from "../lib/originalityResearchMapping";
import type {
  AdaptiveExperimentRecommendation,
  EvidenceGap,
  FairnessAudit,
  FairnessTestSuite,
  RecommendationProvenance,
  RecommendationSystemCard,
  RobustnessRun,
  TransitionPreset,
  TransitionSimulation,
} from "../types/originalityResearch";

function validProfileId(value?: string) {
  return value && !["undefined", "null"].includes(value) ? value : "";
}

function sectionFromPath(pathname: string) {
  if (pathname.includes("/transition-simulator")) return "transition";
  if (pathname.includes("/recommendation-robustness")) return "robustness";
  if (pathname.includes("/robustness-lab") || pathname.includes("/synthetic-fairness-lab")) return "fairness";
  if (pathname.includes("/recommendation-system-card")) return "card";
  return "adaptive";
}

function textArray(value: unknown) {
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
}

function Panel({ title, icon, actions, children }: { title: string; icon: ReactNode; actions?: ReactNode; children: ReactNode }) {
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

function Pill({ children, tone = "default" }: { children: ReactNode; tone?: "success" | "warning" | "danger" | "default" | "muted" }) {
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

export function OriginalityResearchPage() {
  const params = useParams();
  const location = useLocation();
  const { activeProfileId, setActiveProfileId } = useAppActions();
  const profileId = validProfileId(params.profileId || activeProfileId);
  const section = sectionFromPath(location.pathname);

  const [recommendations, setRecommendations] = useState<AdaptiveExperimentRecommendation[]>([]);
  const [evidenceGaps, setEvidenceGaps] = useState<EvidenceGap[]>([]);
  const [simulations, setSimulations] = useState<TransitionSimulation[]>([]);
  const [presets, setPresets] = useState<TransitionPreset[]>([]);
  const [robustnessRuns, setRobustnessRuns] = useState<RobustnessRun[]>([]);
  const [audits, setAudits] = useState<FairnessAudit[]>([]);
  const [fairnessSuites, setFairnessSuites] = useState<FairnessTestSuite[]>([]);
  const [card, setCard] = useState<RecommendationSystemCard | null>(null);
  const [provenance, setProvenance] = useState<RecommendationProvenance | null>(null);
  const [captureProposal, setCaptureProposal] = useState<Record<string, unknown> | null>(null);
  const [weeklyHours, setWeeklyHours] = useState(8);
  const [budget, setBudget] = useState(50);
  const [preset, setPreset] = useState("balanced_transition");
  const [xCriterion, setXCriterion] = useState("transition_duration");
  const [yCriterion, setYCriterion] = useState("market_fit");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const selectedRecommendation = recommendations[0] || null;
  const selectedSimulation = simulations[0] || null;
  const selectedRobustness = robustnessRuns[0] || null;
  const latestAudit = audits[0] || null;
  const uncertaintyCounts = useMemo(() => uncertaintyCategorySummary(recommendations), [recommendations]);
  const simulationStats = useMemo(() => simulationSummary(selectedSimulation), [selectedSimulation]);
  const sensitivityStats = useMemo(() => sensitivityMatrixSummary(selectedRobustness), [selectedRobustness]);
  const auditStats = useMemo(() => fairnessSummary(latestAudit), [latestAudit]);
  const selectedConstraintStats = useMemo(() => constraintSummary(selectedSimulation?.paths?.[0] || null), [selectedSimulation]);
  const provenanceRows = useMemo(() => provenanceTimeline(provenance), [provenance]);
  const objectiveOptions = useMemo(() => {
    const first = selectedSimulation?.paths?.[0];
    return Object.keys(first?.normalised_objectives || first?.objectives || {});
  }, [selectedSimulation]);

  async function refresh() {
    if (!profileId) return;
    setLoading(true);
    setError("");
    const [recommendationResult, gapResult, simulationResult, presetResult, robustnessResult, auditResult, suiteResult, cardResult] = await Promise.allSettled([
      getAdaptiveExperiments(profileId),
      getEvidenceGaps(profileId),
      getTransitionSimulations(profileId),
      getTransitionPresets(),
      getRecommendationRobustness(profileId),
      getFairnessAudits(),
      getFairnessTestSuites(),
      getRecommendationSystemCard(),
    ]);
    if (recommendationResult.status === "fulfilled") setRecommendations(recommendationResult.value);
    if (gapResult.status === "fulfilled") setEvidenceGaps(gapResult.value.gaps || []);
    if (simulationResult.status === "fulfilled") setSimulations(simulationResult.value);
    if (presetResult.status === "fulfilled") setPresets(presetResult.value);
    if (robustnessResult.status === "fulfilled") setRobustnessRuns(robustnessResult.value);
    if (auditResult.status === "fulfilled") setAudits(auditResult.value);
    if (suiteResult.status === "fulfilled") setFairnessSuites(suiteResult.value);
    if (cardResult.status === "fulfilled") setCard(cardResult.value);
    const failed = [recommendationResult, gapResult, simulationResult, presetResult, robustnessResult, auditResult, suiteResult, cardResult].filter((item) => item.status === "rejected").length;
    setError(failed ? `${failed} originality research panel(s) could not load. Available sections remain usable.` : "");
    setLoading(false);
  }

  useEffect(() => {
    if (!profileId) return;
    setActiveProfileId(profileId);
    refresh().catch(() => {
      setLoading(false);
      setError("Originality research data could not be loaded.");
    });
  }, [profileId, setActiveProfileId]);

  async function handleAnalyseAdaptive() {
    const run = await analyseAdaptiveExperiments(profileId, { weekly_learning_time: weeklyHours, learning_budget: budget });
    setRecommendations(run.recommendations);
    setEvidenceGaps(run.evidence_gaps || evidenceGaps);
    setStatus("Adaptive experiment analysis completed. My Roadmap and Evidence Passport were not changed.");
    await refresh();
  }

  async function handleRecommendation(action: "accept" | "save" | "reject" | "start" | "outcome", recommendation: AdaptiveExperimentRecommendation) {
    if (action === "accept") await acceptAdaptiveExperiment(recommendation.id, { add_to_roadmap: false });
    if (action === "save") await saveAdaptiveExperiment(recommendation.id);
    if (action === "reject") await rejectAdaptiveExperiment(recommendation.id, { reason: "too_expensive", note: "Need a lower-cost alternative this week." });
    if (action === "start") await startAdaptiveExperiment(recommendation.id, { add_to_roadmap: false });
    if (action === "outcome") {
      await recordAdaptiveExperimentOutcome(recommendation.id, {
        actual_evidence_gained: [{ skill_id: recommendation.skills_tested[0] || "unknown", actual_gain: "partial demonstrated evidence" }],
        completion_notes: "Completed for demonstration with partial output.",
        actual_time: recommendation.estimated_duration,
        actual_cost: 0,
        produced_artefact: "Demo artifact reference",
        user_reflection: "The experiment produced useful but partial evidence.",
        experiment_outcome: "completed_with_partial_evidence_gain",
      });
      setCaptureProposal(await getAdaptiveEvidenceCapture(recommendation.id));
    }
    const label = action === "reject" ? `Recommendation rejected: ${rejectionReasonLabel("too_expensive")}. Career direction was not rejected.` : `Recommendation ${action} recorded.`;
    setStatus(`${label} No automatic roadmap or evidence mutation was performed.`);
    await refresh();
  }

  async function handleProvenance(targetType: string, targetId: string) {
    const result = await getRecommendationProvenance(targetType, targetId);
    setProvenance(result);
    setStatus("Recommendation provenance loaded. Historical result was not recalculated.");
  }

  async function handleCaptureReview(recommendation: AdaptiveExperimentRecommendation, decision: "accept" | "reject") {
    const updated = await reviewAdaptiveEvidenceCapture(recommendation.id, { decision, note: "User-reviewed demo evidence capture." });
    setRecommendations((current) => current.map((item) => item.id === updated.id ? updated : item));
    setCaptureProposal(((updated.actual_evidence_gain || {}) as Record<string, unknown>).evidence_capture_proposal as Record<string, unknown> | null);
    setStatus("Evidence-capture review recorded. Verified Evidence Passport evidence was not created automatically.");
    await refresh();
  }

  async function handleRunSimulation() {
    const simulation = await createTransitionSimulation(profileId, {
      preset,
      scenario_name: presets.find((item) => item.id === preset)?.label || "Balanced transition",
      controls: { weekly_learning_time: weeklyHours, learning_budget: budget },
      save_scenario: true,
    });
    setSimulations([simulation, ...simulations.filter((item) => item.id !== simulation.id)]);
    setStatus("Transition simulation completed. Multiple Pareto-optimal paths can remain visible.");
    await refresh();
  }

  async function handleRerunSimulation() {
    if (!selectedSimulation) return;
    const simulation = await runTransitionSimulation(selectedSimulation.id, {
      scenario_name: "Increased weekly availability",
      controls: { weekly_learning_time: weeklyHours + 4, learning_budget: budget },
    });
    setStatus("Scenario rerun completed with changed weekly learning time.");
    setSimulations([simulation, ...simulations]);
    await refresh();
  }

  async function handleCompareSimulation() {
    if (!selectedSimulation) return;
    await compareTransitionScenarios(selectedSimulation.id, { comparison_ids: simulations.slice(1, 3).map((item) => item.id) });
    setStatus("Scenario comparison stored. The permanent profile was not changed.");
    await refresh();
  }

  async function handleUpdateConstraints() {
    if (!selectedSimulation) return;
    await updateTransitionSimulationConstraints(selectedSimulation.id, {
      controls: { weekly_learning_time: weeklyHours, learning_budget: budget, maximum_transition_duration: Math.max(3, weeklyHours) },
    });
    setStatus("Constraint update created a new simulation and preserved the historical result.");
    await refresh();
  }

  async function handleArchiveSimulation() {
    if (!selectedSimulation) return;
    await archiveTransitionSimulation(selectedSimulation.id, { reason: "User archived after comparison." });
    setStatus("Simulation archived. Historical input trace remains inspectable.");
    await refresh();
  }

  async function handlePathAction(action: "journal" | "roadmap", pathId: string) {
    if (action === "journal") await addTransitionPathToDecisionJournal(pathId);
    if (action === "roadmap") await proposeTransitionPathRoadmap(pathId);
    setStatus(action === "journal" ? "Selected path added to the Decision Journal. Roadmap unchanged." : "Roadmap proposal created. User confirmation is still required.");
    await refresh();
  }

  async function handleRunRobustness() {
    const run = await runRecommendationRobustness(profileId);
    setRobustnessRuns([run, ...robustnessRuns.filter((item) => item.id !== run.id)]);
    setStatus("Robustness analysis completed using non-sensitive input variations.");
    await refresh();
  }

  async function handleRunFairness() {
    const audit = await runFairnessAudit();
    setAudits([audit, ...audits.filter((item) => item.id !== audit.id)]);
    setStatus("Synthetic fairness audit completed. No real-user profile data was included.");
    await refresh();
  }

  if (!profileId) return <ProfileRequiredState title="Create your profile before opening research and robustness tools." />;

  const base = `/workspace/${profileId}`;
  const tabs = [
    ["adaptive", "Adaptive Experiments", `${base}/adaptive-experiments`, <FlaskConical size={16} />],
    ["transition", "Transition Simulator", `${base}/transition-simulator`, <Scale size={16} />],
    ["robustness", "Recommendation Robustness", `${base}/recommendation-robustness`, <ShieldCheck size={16} />],
    ["fairness", "Synthetic Fairness", `${base}/synthetic-fairness-lab`, <ClipboardList size={16} />],
    ["card", "System Card", "/about/recommendation-system-card", <BookOpenCheck size={16} />],
  ] as const;

  return (
    <main className="innovation-page organic-page originality-page">
      <header className="innovation-header">
        <div>
          <p className="innovation-eyebrow">Originality and Research Innovation Pack</p>
          <h1>Evidence-gain experiments, Pareto transition trade-offs, and recommendation robustness</h1>
          <p>Decision-support outputs remain deterministic, versioned, explainable and user-controlled. The system does not automatically change career direction, evidence, roadmap, applications, or journal history.</p>
        </div>
        <aside className="innovation-metrics">
          <Metric label="Adaptive recommendations" value={recommendations.length} icon={<FlaskConical size={18} />} />
          <Metric label="Transition simulations" value={simulations.length} icon={<Scale size={18} />} />
          <Metric label="Robustness runs" value={robustnessRuns.length} icon={<ShieldCheck size={18} />} />
          <Metric label="Synthetic audits" value={audits.length} icon={<ClipboardList size={18} />} />
        </aside>
      </header>

      <nav className="innovation-tabs" aria-label="Originality research modules">
        {tabs.map(([key, label, to, icon]) => (
          <Link key={key} className={section === key ? "organic-button" : "organic-button-secondary"} to={to}>
            {icon}
            {label}
          </Link>
        ))}
      </nav>

      {(status || error || loading) ? (
        <div className="innovation-notices" aria-live="polite">
          {status ? <p><CheckCircle2 size={16} /> {status}</p> : null}
          {error ? <p className="innovation-notice-error"><XCircle size={16} /> {error}</p> : null}
          {loading ? <p><RefreshCw size={16} /> Loading originality research records</p> : null}
        </div>
      ) : null}

      {provenanceRows.length ? (
        <section className="innovation-panel originality-provenance" aria-label="Recommendation provenance">
          <header className="innovation-panel__header">
            <div>
              <span className="innovation-panel__icon"><History size={18} /></span>
              <h2>Recommendation Provenance</h2>
            </div>
          </header>
          <div className="originality-timeline">
            {provenanceRows.map((row) => (
              <span key={row.label}>
                <b>{row.label}</b>
                {row.value}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {section === "adaptive" ? (
        <div className="innovation-grid innovation-grid--main">
          <Panel title="Adaptive Evidence-Gain Experiment Engine" icon={<FlaskConical size={20} />} actions={<button className="organic-button" type="button" onClick={handleAnalyseAdaptive}><RefreshCw size={16} /> Analyse next experiment</button>}>
            <div className="originality-controls">
              <label>
                Weekly learning time
                <input type="number" min={0} max={80} value={weeklyHours} onChange={(event) => setWeeklyHours(Number(event.target.value))} />
              </label>
              <label>
                Learning budget
                <input type="number" min={0} value={budget} onChange={(event) => setBudget(Number(event.target.value))} />
              </label>
            </div>
            <div className="innovation-metric-grid">
              {Object.entries(uncertaintyCounts).map(([category, count]) => <Metric key={category} label={category} value={count} icon={<BarChart3 size={18} />} />)}
              {!Object.keys(uncertaintyCounts).length ? <Metric label="Uncertainty model" value="not run" icon={<BarChart3 size={18} />} /> : null}
              <Metric label="Evidence gaps" value={evidenceGaps.length} icon={<ClipboardList size={18} />} />
            </div>
            <div className="originality-gap-list" aria-label="Evidence-gap summary">
              {evidenceGaps.slice(0, 4).map((gap) => (
                <span key={gap.id}>
                  <b>{gap.skill_id.replace(/_/g, " ")}</b>
                  {gap.gap_type} - severity {gap.severity.toFixed(2)}
                </span>
              ))}
              {!evidenceGaps.length ? <span><b>Missing evidence</b>No gap analysis has been loaded yet.</span> : null}
            </div>
            <div className="innovation-list">
              {recommendations.map((recommendation) => (
                <article className="innovation-row" key={recommendation.id}>
                  <div>
                    <div className="innovation-row-title">
                      <b>{recommendation.title}</b>
                      <Pill tone={recommendationBandTone(recommendation.priority_band)}>{recommendation.priority_band}</Pill>
                    </div>
                    <p>{recommendation.explanation}</p>
                    <div className="innovation-chip-row">
                      {recommendation.skills_tested.slice(0, 5).map((skill) => <span key={skill}>{skill}</span>)}
                      {(recommendation.linked_evidence_gap_ids || []).slice(0, 2).map((gapId) => <span key={gapId}>{gapId}</span>)}
                    </div>
                    <small>{recommendation.estimated_duration} - effort {recommendation.estimated_effort} - cost {recommendation.estimated_cost}</small>
                  </div>
                  <div className="innovation-actions">
                    <button aria-label={actionAriaLabel("Accept", recommendation.title)} className="organic-button-secondary" type="button" onClick={() => handleRecommendation("accept", recommendation)}><CheckCircle2 size={16} /> Accept</button>
                    <button aria-label={actionAriaLabel("Save", recommendation.title)} className="organic-button-secondary" type="button" onClick={() => handleRecommendation("save", recommendation)}><Save size={16} /> Save</button>
                    <button aria-label={actionAriaLabel("Reject", recommendation.title)} className="organic-button-secondary" type="button" onClick={() => handleRecommendation("reject", recommendation)}><XCircle size={16} /> Reject</button>
                  </div>
                </article>
              ))}
              {!recommendations.length ? <p className="innovation-empty">Run the analysis to generate adaptive recommendations from current hypotheses and evidence.</p> : null}
            </div>
          </Panel>

          <Panel title={selectedRecommendation?.title || "Recommendation Detail"} icon={<SlidersHorizontal size={20} />} actions={selectedRecommendation ? <button className="organic-button" type="button" onClick={() => handleRecommendation("start", selectedRecommendation)}><FlaskConical size={16} /> Start experiment</button> : null}>
            {selectedRecommendation ? (
              <>
                <p className="innovation-lead">{selectedRecommendation.expected_evidence_gain?.role_specific_or_transferable ? `Evidence gain: ${selectedRecommendation.expected_evidence_gain.role_specific_or_transferable}` : selectedRecommendation.explanation}</p>
                <div className="innovation-source-box">
                  <b>Score explanation</b>
                  <p>{selectedRecommendation.score_components.score_precision_note || "Scores are bands, not scientific probabilities."}</p>
                </div>
                <button className="organic-button-secondary" type="button" onClick={() => handleProvenance("adaptive-experiment", selectedRecommendation.id)}><History size={16} /> Provenance</button>
                <div className="originality-component-list">
                  {scoreComponentRows(selectedRecommendation).slice(0, 10).map((component) => (
                    <span key={`${component.direction}-${component.key}`}>
                      <b>{component.key.replace(/_/g, " ")}</b>
                      {component.direction}: {component.value.toFixed(2)} x {component.weight.toFixed(2)}
                    </span>
                  ))}
                </div>
                {captureProposal ? (
                  <div className="innovation-source-box" aria-label="Evidence capture review">
                    <b>Evidence Capture Review</b>
                    <p>{String(captureProposal.evidence_status || captureProposal.status || "pending_user_review")}. Completion is not verified Evidence Passport evidence.</p>
                    <div className="innovation-actions">
                      <button className="organic-button-secondary" type="button" onClick={() => handleCaptureReview(selectedRecommendation, "accept")}><CheckCircle2 size={16} /> Accept capture</button>
                      <button className="organic-button-secondary" type="button" onClick={() => handleCaptureReview(selectedRecommendation, "reject")}><XCircle size={16} /> Reject capture</button>
                    </div>
                  </div>
                ) : null}
                <h3>Alternatives</h3>
                <div className="innovation-list">
                  {selectedRecommendation.alternatives.map((alternative) => (
                    <article className="innovation-card" key={alternative.type}>
                      <h3>{alternative.title}</h3>
                      <p>{alternative.reason}</p>
                      <small>{alternative.tradeoff}</small>
                    </article>
                  ))}
                </div>
                <button className="organic-button-secondary" type="button" onClick={() => handleRecommendation("outcome", selectedRecommendation)}><History size={16} /> Record outcome</button>
              </>
            ) : <p className="innovation-empty">Select or generate a recommendation.</p>}
          </Panel>
        </div>
      ) : null}

      {section === "transition" ? (
        <div className="innovation-grid innovation-grid--main">
          <Panel title="Career Transition Pareto Simulator" icon={<Scale size={20} />} actions={<button className="organic-button" type="button" onClick={handleRunSimulation}><Scale size={16} /> Run simulation</button>}>
            <div className="originality-controls">
              <label>
                Scenario preset
                <select value={preset} onChange={(event) => setPreset(event.target.value)}>
                  {presets.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
                  {!presets.length ? <option value="balanced_transition">Balanced transition</option> : null}
                </select>
              </label>
              <label>
                Weekly learning time
                <input type="number" min={0} max={80} value={weeklyHours} onChange={(event) => setWeeklyHours(Number(event.target.value))} />
              </label>
              <label>
                Learning budget
                <input type="number" min={0} value={budget} onChange={(event) => setBudget(Number(event.target.value))} />
              </label>
            </div>
            <div className="innovation-metric-grid">
              <Metric label="Candidate paths" value={simulationStats.pathCount} icon={<GitCompare size={18} />} />
              <Metric label="Pareto-optimal" value={simulationStats.paretoCount} icon={<CheckCircle2 size={18} />} />
              <Metric label="Dominated visible" value={simulationStats.dominatedCount} icon={<Scale size={18} />} />
              <Metric label="Objective version" value={selectedSimulation?.objective_version || "not run"} icon={<ClipboardList size={18} />} />
              <Metric label="Constraint violations" value={selectedConstraintStats.violated} icon={<XCircle size={18} />} />
            </div>
            <div className="innovation-list">
              {(selectedSimulation?.paths || []).map((path) => {
                const status = paretoPathStatus(path);
                const hardConstraintViolations = path.hard_constraint_violations || [];
                return (
                  <article className="innovation-row" key={path.id}>
                    <div>
                      <div className="innovation-row-title">
                        <b>{path.title}</b>
                        <Pill tone={status.tone}>{status.label}</Pill>
                      </div>
                      <p>{path.dominated_explanation}</p>
                      <div className="innovation-chip-row">
                        <span>{path.reversibility} reversibility</span>
                        <span>{path.path_type}</span>
                        <span>{path.feasibility_status || "feasibility unknown"}</span>
                      </div>
                      {hardConstraintViolations.length ? <small>Hard constraint: {String(hardConstraintViolations[0].constraint)}</small> : null}
                    </div>
                    <div className="innovation-actions">
                      <button className="organic-button-secondary" type="button" onClick={() => handlePathAction("journal", path.id)}><FileClock size={16} /> Decision Journal</button>
                      <button className="organic-button-secondary" type="button" onClick={() => handlePathAction("roadmap", path.id)}><Save size={16} /> Propose roadmap</button>
                    </div>
                  </article>
                );
              })}
              {!selectedSimulation ? <p className="innovation-empty">Run a scenario to calculate non-dominated transition paths.</p> : null}
            </div>
          </Panel>
          <Panel title="Trade-Off Detail" icon={<GitCompare size={20} />} actions={selectedSimulation ? <><button className="organic-button-secondary" type="button" onClick={handleRerunSimulation}><RefreshCw size={16} /> Change time</button><button className="organic-button-secondary" type="button" onClick={handleUpdateConstraints}><SlidersHorizontal size={16} /> Update constraints</button><button className="organic-button-secondary" type="button" onClick={handleCompareSimulation}><GitCompare size={16} /> Compare</button><button className="organic-button-secondary" type="button" onClick={() => handleProvenance("transition-simulation", selectedSimulation.id)}><History size={16} /> Provenance</button><button className="organic-button-secondary" type="button" onClick={handleArchiveSimulation}><XCircle size={16} /> Archive</button></> : null}>
            <p className="innovation-lead">{selectedSimulation?.explanation || "No simulation has been run yet."}</p>
            <div className="originality-controls">
              <label>
                X-axis criterion
                <select value={xCriterion} onChange={(event) => setXCriterion(event.target.value)}>
                  {(objectiveOptions.length ? objectiveOptions : ["transition_duration", "market_fit"]).map((item) => <option key={item} value={item}>{item.replace(/_/g, " ")}</option>)}
                </select>
              </label>
              <label>
                Y-axis criterion
                <select value={yCriterion} onChange={(event) => setYCriterion(event.target.value)}>
                  {(objectiveOptions.length ? objectiveOptions : ["market_fit", "personal_fit"]).map((item) => <option key={item} value={item}>{item.replace(/_/g, " ")}</option>)}
                </select>
              </label>
            </div>
            <div className="originality-scatter" role="img" aria-label={`Pareto chart comparing ${xCriterion.replace(/_/g, " ")} and ${yCriterion.replace(/_/g, " ")}`}>
              {(selectedSimulation?.paths || []).map((path) => {
                const x = Math.max(6, Math.min(94, Number(path.normalised_objectives?.[xCriterion] ?? 0.5) * 88 + 6));
                const y = Math.max(6, Math.min(94, 94 - Number(path.normalised_objectives?.[yCriterion] ?? 0.5) * 88));
                return <button key={path.id} type="button" className={path.is_pareto_optimal ? "originality-point originality-point--front" : "originality-point"} style={{ left: `${x}%`, top: `${y}%` }} aria-label={`${path.title}: ${path.is_pareto_optimal ? "non-dominated" : "dominated"}, ${path.feasibility_status || "feasibility unknown"}`}>{path.is_pareto_optimal ? "P" : "D"}</button>;
              })}
            </div>
            <p className="innovation-source-box">The chart shows two selected criteria. Pareto classification uses the complete configured criterion set.</p>
            <div className="originality-table" role="table" aria-label="Transition objective comparison">
              <div role="row">
                <b role="columnheader">Path</b>
                <b role="columnheader">Objective</b>
                <b role="columnheader">Direction</b>
                <b role="columnheader">Normalised</b>
              </div>
              {(selectedSimulation?.paths || []).flatMap((path) => objectiveRows(path).slice(0, 4).map((objective) => (
                <div role="row" key={`${path.id}-${objective.key}`}>
                  <span role="cell">{path.title}</span>
                  <span role="cell">{objective.key.replace(/_/g, " ")}</span>
                  <span role="cell">{objective.direction}</span>
                  <span role="cell">{objective.normalised.toFixed(2)}</span>
                </div>
              )))}
            </div>
          </Panel>
        </div>
      ) : null}

      {section === "robustness" ? (
        <div className="innovation-grid innovation-grid--main">
          <Panel title="Recommendation Robustness" icon={<ShieldCheck size={20} />} actions={<><button className="organic-button" type="button" onClick={handleRunRobustness}><ShieldCheck size={16} /> Run robustness analysis</button>{selectedRobustness ? <button className="organic-button-secondary" type="button" onClick={() => handleProvenance("recommendation-robustness", selectedRobustness.id)}><History size={16} /> Provenance</button> : null}</>}>
            <div className="innovation-metric-grid">
              <Metric label="Tested variables" value={sensitivityStats.testedVariables} icon={<SlidersHorizontal size={18} />} />
              <Metric label="High-impact rows" value={sensitivityStats.highImpact} icon={<BarChart3 size={18} />} />
              <Metric label="Limitations" value={sensitivityStats.limitations} icon={<ClipboardList size={18} />} />
              <Metric label="Top-k overlap" value={String(selectedRobustness?.metrics?.top_k_overlap ?? "not run")} icon={<GitCompare size={18} />} />
              <Metric label="Max rank movement" value={sensitivityStats.maxRankMovement} icon={<RefreshCw size={18} />} />
              <Metric label="Threshold crossings" value={sensitivityStats.thresholdCrossings} icon={<XCircle size={18} />} />
            </div>
            <div className="innovation-list">
              {(selectedRobustness?.stability_results || []).map((item) => (
                <article className="innovation-row" key={String(item.career_hypothesis)}>
                  <div>
                    <div className="innovation-row-title">
                      <b>{String(item.career_hypothesis)}</b>
                      <Pill tone={robustnessTone(String(item.status))}>{String(item.status)}</Pill>
                    </div>
                    <p>{String(item.dependency)}</p>
                  </div>
                </article>
              ))}
              {!selectedRobustness ? <p className="innovation-empty">Run robustness analysis to test non-sensitive input variation.</p> : null}
            </div>
          </Panel>
          <Panel title="What Could Change This Recommendation?" icon={<BarChart3 size={20} />}>
            <div className="innovation-list">
              {dependencyWarnings(selectedRobustness).map((warning) => <p className="innovation-source-box" key={warning}>{warning}</p>)}
            </div>
            <div className="originality-table" role="table" aria-label="Sensitivity matrix">
              <div role="row">
                <b role="columnheader">Variable</b>
                <b role="columnheader">Range</b>
                <b role="columnheader">Effect</b>
              </div>
              {(selectedRobustness?.sensitivity_matrix || []).map((row) => (
                <div role="row" key={String(row.tested_variable)}>
                  <span role="cell">{String(row.tested_variable).replace(/_/g, " ")}</span>
                  <span role="cell">{String(row.tested_range)}</span>
                  <span role="cell">{String(row.magnitude_of_effect)}</span>
                </div>
              ))}
            </div>
            <div className="innovation-list">
              {(selectedRobustness?.scenario_results || []).slice(0, 3).map((scenario) => (
                <article className="innovation-card" key={String(scenario.scenario_id)}>
                  <h3>{String(scenario.tested_variable).replace(/_/g, " ")}</h3>
                  <p>{String(scenario.interpretation)}</p>
                  <small>Top-k overlap {String(scenario.top_k_overlap)} - label changes {Array.isArray(scenario.label_changes) ? scenario.label_changes.length : 0}</small>
                </article>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {section === "fairness" ? (
        <div className="innovation-grid innovation-grid--main">
          <Panel title="Synthetic Fairness Lab" icon={<ShieldCheck size={20} />} actions={<button className="organic-button" type="button" onClick={handleRunFairness}><ShieldCheck size={16} /> Run synthetic audit</button>}>
            <div className="innovation-metric-grid">
              <Metric label="Synthetic only" value={auditStats.syntheticOnly ? "yes" : "no"} icon={<ShieldCheck size={18} />} />
              <Metric label="Passed" value={auditStats.passed} icon={<CheckCircle2 size={18} />} />
              <Metric label="Review required" value={auditStats.reviewRequired} icon={<XCircle size={18} />} />
              <Metric label="Contextual" value={auditStats.contextual} icon={<Scale size={18} />} />
              <Metric label="Data limitations" value={auditStats.dataLimitations} icon={<ClipboardList size={18} />} />
              <Metric label="Test suites" value={fairnessSuites.length} icon={<BookOpenCheck size={18} />} />
            </div>
            <div className="innovation-list">
              {(latestAudit?.results || []).map((result) => (
                <article className="innovation-row" key={String(result.case_id)}>
                  <div>
                    <div className="innovation-row-title">
                      <b>{String(result.case_id)}</b>
                      <Pill tone={fairnessStatusTone(String(result.status))}>{String(result.status)}</Pill>
                    </div>
                    <p>{String(result.output_difference)}</p>
                    <small>{String(result.rule_or_service_affected)} - severity {String(result.severity)}</small>
                  </div>
                </article>
              ))}
              {!latestAudit ? <p className="innovation-empty">Run a synthetic audit. No identifiable real-user profiles are used.</p> : null}
            </div>
          </Panel>
          <Panel title="Technical Report Export Preview" icon={<ClipboardList size={20} />}>
            <div className="innovation-list">
              {fairnessSuites.map((suite) => (
                <article className="innovation-card" key={suite.suite_id}>
                  <h3>{suite.label}</h3>
                  <p>{suite.cases.length} deterministic synthetic cases. Synthetic only: {suite.synthetic_only ? "yes" : "no"}.</p>
                  <small>{suite.limitations.join(" ")}</small>
                </article>
              ))}
            </div>
            <pre className="innovation-token">{JSON.stringify(latestAudit || { synthetic_only: true, real_user_data_included: false }, null, 2)}</pre>
          </Panel>
        </div>
      ) : null}

      {section === "card" ? (
        <div className="innovation-grid innovation-grid--main originality-printable">
          <Panel title="Recommendation System Card" icon={<BookOpenCheck size={20} />}>
            <p className="innovation-lead">{card?.system_purpose || "Loading the machine-readable recommendation system card."}</p>
            <div className="innovation-fit-grid">
              <span><b>Version</b>{card?.version || "not loaded"}</span>
              <span><b>Validation status</b>{card?.validation_status || "not loaded"}</span>
            </div>
            {card ? ["intended_users", "excluded_uses", "input_categories", "output_categories", "deterministic_services", "ai_assisted_components"].map((key) => (
              <section className="originality-card-section" key={key}>
                <h3>{key.replace(/_/g, " ")}</h3>
                <ul className="innovation-list-text">
                  {textArray((card as unknown as Record<string, unknown>)[key]).map((item) => <li key={item}>{item}</li>)}
                </ul>
              </section>
            )) : null}
          </Panel>
          <Panel title="Human Oversight, Privacy and Risks" icon={<ShieldCheck size={20} />}>
            {card ? ["human_oversight", "privacy", "fairness_considerations", "known_limitations", "unresolved_risks"].map((key) => (
              <section className="originality-card-section" key={key}>
                <h3>{key.replace(/_/g, " ")}</h3>
                <ul className="innovation-list-text">
                  {textArray((card as unknown as Record<string, unknown>)[key]).map((item) => <li key={item}>{item}</li>)}
                </ul>
              </section>
            )) : <p className="innovation-empty">System card unavailable.</p>}
          </Panel>
        </div>
      ) : null}
    </main>
  );
}
