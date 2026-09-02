# Task 14D / Week 6 Gap Audit

Date: 2026-08-05
Baseline commit: `ff09a6c01c7a3f9a7e7b5488410fd23327f1aee2`
Baseline message: `feat: complete task 14c interview and decision journey`

## Scope

This audit was completed before Task 14D code changes. It covers the recovered repository at `OrganicAI-Compass-recovered` and does not inspect or modify local secret files such as `.env.postgres-test`, `backend/.env.postgres-test`, or `backend/.venv/`.

## Findings

| Area | Classification | Evidence | Task 14D action |
| --- | --- | --- | --- |
| Existing recommendation engine | Existing and verified | `backend/app/services/recommendation_engine.py`, `recommendation_rules.py`, `recommendation_scoring.py` provide deterministic recommendation generation and feedback events. | Reuse for provenance language and avoid duplicate recommendation records. |
| Existing roadmap recommendations | Existing and verified | `RoadmapAction`, `RoadmapVersion`, roadmap recalibration and action lifecycle already exist. | Keep Week 6 outputs as proposals unless the user explicitly confirms roadmap changes. |
| Existing experiments or learning actions | Existing and verified | `CareerExperimentTemplate`, `CareerExperimentSession`, learning recommendations and roadmap learning actions exist. | Reuse career experiment sessions when adaptive experiments are started. |
| Evidence Passport gaps | Existing but incomplete | Evidence confidence and recency tables exist; adaptive analysis infers skill uncertainty, but there is no dedicated evidence-gap endpoint or structured gap IDs. | Add explicit evidence-gap discovery payloads and link generated experiments to gap identifiers. |
| Career Hypothesis uncertainty | Existing and verified | `CareerHypothesis` stores active hypotheses, alignment and uncertainty labels. | Use active hypothesis versions/snapshots in Week 6 input traces. |
| User constraints | Existing but incomplete | Adaptive and transition payloads accept time, budget and work-mode inputs; hard-constraint results are not explicit enough. | Add deterministic constraint result objects and no-feasible-path signalling. |
| Market relevance inputs | Existing and verified | Market radar, job analysis, provider status and market signal records exist from Week 4. | Use local/date-bound relevance labels only; no live provider calls. |
| Adaptive evidence-gain logic | Existing but incomplete | `originality_research_engine.py` ranks career experiment templates with visible components. | Align status vocabulary, gap IDs, no-action option, evidence-capture proposal and provenance. |
| Experiment ranking | Existing but incomplete | Weighted component scores are present and versioned. Priority bands use "recommendation" wording. | Rename bands to evidence-value language and document missing-data behavior. |
| Experiment alternatives | Existing but incomplete | Lower-effort, higher-evidence and no-action alternatives exist. | Add lower-cost alternative where applicable and make no-action visible in UI tests. |
| Evidence-value explanation | Existing but incomplete | Score components and explanation text are returned. | Add component contribution rows, methodology docs and provenance trace. |
| Experiment completion and feedback | Existing but incomplete | Outcome recording exists and avoids auto-verification, but status is `outcome_recorded` and no explicit evidence-capture proposal route exists. | Add completion workflow fields and evidence-capture review API. |
| Pareto optimisation utilities | Existing but incomplete | Non-dominated sorting exists in `create_transition_simulation`. | Add documented tie/missing/incomparable/constraint behavior and validation coverage. |
| Career transition paths | Existing and verified | `CareerTransitionSimulation` and `CareerTransitionPath` persist deterministic paths. | Extend public payload with feasibility and constraint status. |
| Path feasibility | Existing but incomplete | Controls exist but hard constraints are not surfaced as satisfied/violated/unknown. | Add feasibility status and per-constraint result objects. |
| Dominated and non-dominated path logic | Existing and verified | `_dominates`, `_normalise_paths` and `_apply_pareto` implement explicit non-dominated sorting. | Add targeted tests for ties, missing values and infeasible paths. |
| Sensitivity analysis | Existing but incomplete | Transition scenario comparison exists; robustness analysis varies selected inputs. | Add rank movement, threshold crossing and missing-data metrics. |
| Robustness analysis | Existing but incomplete | `RecommendationRobustnessRun` stores baseline, variations, sensitivity matrix and metrics. | Add top-1 stability, maximum/average rank movement, path-frontier overlap and qualitative interpretation. |
| Fairness or synthetic counterfactual testing | Existing but incomplete | Synthetic-only fairness audit exists with invariance and contextual cases. | Add missing-data, rank-stability, dominance-consistency and evidence-category separation fixtures/results. |
| Missing-data handling | Existing but incomplete | Sparse Evidence Passport warnings exist. | Add explicit missing inputs and data-quality notes to decision-support snapshots. |
| Rank-stability testing | Existing but incomplete | Robustness metrics include top-k overlap and rank stability. | Add deterministic metric tests and frontend mapping tests. |
| Recommendation provenance | Existing but incomplete | Records store input snapshots and source versions through parent runs. | Add provenance API and UI trace for experiments, simulations and robustness runs. |
| Recommendation system documentation | Existing but incomplete | `RECOMMENDATION_SYSTEM_CARD.md` and related methodology docs exist. | Update Task 14D-specific docs and system card details to match implementation. |
| System-card coverage | Existing but incomplete | API returns a system card with boundaries and limitations. | Add Week 6 methods, synthetic fairness limits and validation status. |
| Demo workflow | Existing and verified | Demo reset includes `originality_research` cleanup and seeding. | Verify Week 6 deterministic scenario after changes. |
| Thesis Chapter 4 and Chapter 5 preparation | Existing but incomplete | Chapter 4 draft exists; Chapter 5 draft does not. | Update Chapter 4 and create Chapter 5 with validation-only claims. |
| Test coverage | Existing but incomplete | Backend, frontend mapping and E2E tests cover the broad Week 6 surface. | Add targeted tests for new gap, provenance, constraint, robustness and fairness details. |
| Security and privacy implications | Existing and verified | Route authorization, personal-data inventory, repository safety and archive scripts exist. | Run audits and ensure no secrets, live providers, hidden tracking, or automatic authoritative mutation. |
| External production deployment | External/manual action required | Production deployment remains outside local scope. | Report separately; no public deployment. |
| Live provider validation | External dependency blocked | The task prohibits OpenAI, ElevenLabs, NAV, ESCO, email and external analytics calls. | Keep deterministic local fixtures and provider-disabled boundaries. |

## Initial Classification

Task 14D starts as `PARTIALLY COMPLETED` at this audit point. The recovered repository already contains real Week 6-like models, routes, services, frontend pages and tests, but acceptance gaps remain around explicit evidence-gap discovery, required experiment lifecycle vocabulary, evidence-capture review, hard-constraint feasibility, provenance APIs, expanded robustness metrics, expanded synthetic fairness fixtures, required documentation/evidence pack, archive regeneration, PostgreSQL validation and final local commit.
