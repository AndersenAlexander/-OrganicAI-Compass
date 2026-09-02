# Task 14D Week 6 Feature Audit

Final technical classification is determined by `docs/WEEK6_TESTING_REPORT.md` after validation.

## Feature Matrix

| Feature | Status | Evidence |
| --- | --- | --- |
| Shared decision-support snapshot | Implemented | Adaptive, Pareto and robustness outputs expose `decision_support_snapshot` with input fingerprint, rule-set version, algorithm version, source versions, missing inputs, assumptions, limitations and seed. |
| Evidence-gap discovery | Implemented | `/api/v1/profiles/{profile_id}/evidence-gaps` returns deterministic gap IDs from Career Hypotheses, Evidence Passport and experiment templates. |
| Adaptive Evidence-Gain Engine | Implemented | `analyse_adaptive_experiments` ranks existing `CareerExperimentTemplate` records and stores immutable run snapshots. |
| Ranking components and weights | Implemented | Positive and negative component values, weights, normalised score and precision note are returned for every recommendation. |
| Alternatives | Implemented | Lower-effort, higher-evidence, lower-cost and no-action options are visible. |
| Experiment lifecycle | Implemented | Proposed, accepted, planned, active, paused, completed, abandoned, rejected, expired, evidence submitted and evidence reviewed statuses are validated. |
| Evidence-capture review | Implemented | Completion creates a capture proposal; no verified Evidence Passport item is created without separate user review. |
| Pareto transition simulator | Implemented | Existing transition simulations use explicit non-dominated sorting and keep dominated paths visible. |
| Constraint feasibility | Implemented | Paths expose per-constraint statuses, hard violations and recommendation eligibility. |
| Pareto visualization | Implemented | Frontend includes X/Y criterion selectors, point labels and table fallback with a visible limitation note. |
| Robustness lab | Implemented | Runs include baseline, scenarios, sensitivity matrix, rank movement, top-1/top-k stability, threshold crossings and qualitative interpretation. |
| Synthetic fairness lab | Implemented | Synthetic-only suites cover invariance, monotonicity, missing data, rank stability, dominance consistency and evidence-category separation. |
| Recommendation provenance | Implemented | `/api/v1/recommendation-provenance/{target_type}/{target_id}` exposes input trace and no-silent-recalculation policy. |
| System card | Implemented | System card includes deterministic services, prohibited claims, human oversight and fairness limitations. |
| Demo reset | Implemented | Demo seed/reset includes profile-scoped originality research cleanup and deterministic Week 6 seeding. |
| External validation | External/manual action required | Empirical evaluation, supervisor review, public deployment and live provider validation remain outside local Task 14D. |

## Safety Decision

No live OpenAI, ElevenLabs, NAV, ESCO, email provider, analytics or external research call is required for Week 6. The implementation does not estimate hiring probability, employability, psychological traits, legal fairness compliance or official labour-market forecasts.
