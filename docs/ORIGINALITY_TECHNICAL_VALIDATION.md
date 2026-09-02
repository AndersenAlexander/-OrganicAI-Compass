# Originality Technical Validation

Status: technical validation is available for deterministic implementation behavior. Synthetic engineering validation is available for the Synthetic Fairness Lab. Empirical participant evaluation is pending.

## Adaptive Evidence-Gain Experiment Engine

- **Purpose:** prioritise a bounded practical experiment that may reduce evidence uncertainty around an active Career Hypothesis.
- **Inputs:** persisted current-profile active `CareerHypothesis` records, non-provisional Evidence Passport confidence and recency, active experiment-template metadata, prior completed/rejected experiment sessions, and the supplied weekly-time/budget/accessibility/preference constraint snapshot. It does not use another user’s records or a fallback career hypothesis.
- **Algorithm type:** deterministic weighted score. Positive factors are uncertainty reduction, evidence importance, market relevance, cross-path transferability, portfolio value, feasibility, support availability, and preference alignment. Negative factors are time cost, monetary cost, complexity, accessibility barrier, repetition, redundancy, and implementation risk.
- **Outputs:** ranked experiments with human-readable related hypothesis, evidence gap, expected evidence gain, effort/cost, alternatives, score-band explanation, limitation, and versioned provenance snapshot.
- **User-control boundary:** completion produces an evidence-capture proposal only. Accepting or rejecting that proposal does not create verified Evidence Passport evidence; a separate Evidence Passport action is required. Roadmap insertion is also opt-in.
- **Uncertainty / limitations:** missing evidence is uncertainty, not inability. With no active Career Hypothesis the persisted run is `insufficient_data` and produces no fallback recommendation.
- **Tests executed:** focused `backend/tests/test_originality_research_engine.py`, including ranking, constraints, ties, no-hypothesis, run-snapshot, and no-auto-promotion coverage.
- **Result:** deterministic technical behavior covered; empirical effectiveness is pending.

## Career Transition Pareto Simulator

- **Purpose:** compare transition-path trade-offs without declaring one “best career.”
- **Inputs:** current active Career Hypotheses, user-controlled scenario constraints, configured objectives, local role metadata, and local/date-bound market fixture metadata.
- **Algorithm type:** deterministic normalisation followed by Pareto dominance. A path dominates another only when it is equal or better on every selected objective and strictly better on at least one.
- **Objectives:** transition duration, direct monetary cost, weekly effort, financial risk, evidence gap, capability gap, language barrier, dependence on uncertain assumptions, personal/capability/market/support fit, local opportunity availability, accessibility, reversibility, portfolio reuse, transferable-skill reuse, and AI-change stability; only selected configured objectives determine a front.
- **Outputs:** visible non-dominated and dominated paths, objective directions, constraints, feasibility, trade-off labels, assumptions, limitations, provenance, and scenario timestamps.
- **User-control boundary:** changing or rerunning a scenario creates a new simulation record. It does not mutate the Human Potential Map, hypotheses, Evidence Passport, Roadmap, or application state. A Decision Journal entry is created only when the user explicitly chooses the action.
- **Uncertainty / limitations:** no active hypothesis yields an `insufficient_data` record with no fallback path. Objective values are prototype decision-support fixtures, not labour-market or income forecasts.
- **Tests executed:** focused engine tests for clear dominance, ties, identical vectors, multiple non-dominated paths, one candidate, empty candidates, constraints, and scenario persistence.
- **Result:** Pareto mechanics are technically covered; participant usefulness and outcome validity are pending.

## Recommendation Robustness Lab

- **Purpose:** make sensitivity to selected non-sensitive scenario assumptions inspectable.
- **Inputs:** current active Career Hypotheses supply the baseline. The implemented scenario labels are weekly learning time (8 hours; 5–12), learning budget (50 EUR; 0–100), market-data window (30 days; 14–90), evidence recency (current; discount older evidence), and support availability (unconfirmed; available/unavailable).
- **Algorithm type:** deterministic scenario-offset sensitivity check. It records rank movement, top-1 stability, top-k overlap, fit-band threshold crossings, label stability, rank stability, fixed score-variance/scenario-agreement descriptors, and dependency flags.
- **Outputs:** sensitivity matrix, affected paths, scenario results, limitations, provenance snapshot, and a cautious qualitative status.
- **User-control boundary:** a run is an immutable scenario record and changes no profile, hypothesis, evidence, roadmap, application, or journal data.
- **Uncertainty / limitations:** confirmed qualifications and professional history are not perturbed. The module does not rerun the upstream Human Diagnostic, hypothesis, market, or recommendation algorithms; it is not statistical confidence, causal validation, or correctness proof. Without an active hypothesis it returns `insufficient_data` and does not fabricate a baseline.
- **Tests executed:** focused engine coverage for baseline, sensitivity/dependency output, sparse/no-hypothesis input, provenance, and no user-state mutation.
- **Result:** deterministic scenario-sensitivity behavior is technically covered; empirical robustness and predictive validity are pending.

## Synthetic Fairness Lab

- **Purpose:** engineering validation using synthetic fixtures only.
- **Inputs:** deterministic synthetic case definitions, fixed seed `fairness-v1`, and the listed engine versions. No identifiable real-user profile or protected attribute is written to normal profile state.
- **Algorithm type:** deterministic fixture audit.
- **Metrics / output checks:** case status and output difference for gender-marker and age-band invariance, budget/accessibility monotonicity, location contextual difference, missing-evidence behavior, employment-gap wording, non-sensitive rank stability, Pareto dominance consistency, and evidence-category separation. Summary counts include Passed, Review required, Data limitation, and Expected contextual difference.
- **User-control boundary:** audit records are synthetic research records; they do not mutate production profile, evidence, roadmap, application, or Decision Journal state. Reset is limited to explicitly marked demo synthetic runs.
- **Uncertainty / limitations:** **SYNTHETIC ONLY — ENGINEERING VALIDATION.** Synthetic data may not represent real users; test dimensions are limited; untested bias sources may remain; no legal compliance, fairness certification, or real-world fairness conclusion is claimed. Empirical participant evaluation and review remain required.
- **Reproducibility:** the audit persists timestamp, fixture/engine versions, deterministic seed, synthetic-only marker, output summary, and limitations.
- **Tests executed:** focused originality engine tests assert synthetic isolation, reproducibility metadata, visible limitation state, result metrics, and no normal-user mutation.
- **Result:** synthetic engineering checks are available; empirical fairness evidence is pending.

## Provenance, run history, and AI boundary

- Adaptive, Pareto, and Robustness outputs persist an input snapshot/fingerprint, source versions, algorithm/rule-set version, timestamp, data coverage, assumptions, limitations, and user-confirmation state. New adaptive analyses and Pareto reruns append records rather than overwrite a historical snapshot.
- The System Card separates user input, Evidence Passport, deterministic services, synthetic data, user decisions, and optional AI-assisted explanations. AI-assisted components may explain results or draft reflection prompts; they do not calculate or alter adaptive ranking, Pareto dominance/front membership, robustness metrics, or fairness statuses.
- My Journey does not infer lifecycle completion from an originality run. Decision Journal creation requires the explicit “Decision Journal” user action; a simulation result alone is not a decision.
