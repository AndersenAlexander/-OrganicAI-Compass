# Originality Research Pack Implementation Report

1. Repository audit findings: the implementation reuses the existing FastAPI, SQLAlchemy, React, Vite, Vitest, and Playwright structure. Career resilience, market application, innovation extension, demo reset, and research-export boundaries were already present and were extended rather than replaced.

2. Reused modules/entities: Career Hypotheses, Evidence Passport, Career Experiment Templates, Career Experiment Sessions, Career Encyclopedia-style transition labels, Supported Paths, Market Radar inputs, Decision Journal entries, Research Evaluation separation, Demo Mode, and Reset Demo hooks.

3. Architecture decisions: the pack is deterministic, versioned, inspectable, and user-controlled. It does not introduce opaque AI ranking and does not automatically mutate career direction, evidence, roadmap, applications, or journal history.

4. Files created: `backend/app/models/originality_research.py`, `backend/app/services/originality_research_engine.py`, `backend/app/routers/originality_research.py`, `backend/tests/test_originality_research_engine.py`, `frontend/src/api/originalityResearchApi.ts`, `frontend/src/types/originalityResearch.ts`, `frontend/src/lib/originalityResearchMapping.ts`, `frontend/src/lib/originalityResearchMapping.test.ts`, `frontend/src/pages/OriginalityResearchPage.tsx`, `frontend/src/styles/originality-research.css`, `frontend/tests/e2e/originality-research.spec.ts`, and the Originality Research Pack documentation files.

5. Files modified: `README.md`, `backend/app/database.py`, `backend/app/main.py`, `backend/app/models/__init__.py`, `backend/app/services/demo_seed_service.py`, `backend/app/routers/demo.py`, `frontend/src/main.tsx`, `frontend/src/routes/router.tsx`, `frontend/src/config/navigation.ts`, and `frontend/playwright.config.ts`.

6. Adaptive design: the Adaptive Evidence-Gain Experiment Engine converts reusable career experiment templates into explainable recommendations based on evidence gap, hypothesis uncertainty, feasibility, diversity, reversibility, user cost, market signal, and recency.

7. Scoring formula/default weights: the default scoring version is `adaptive-evidence-gain-score-v1` with `adaptive-evidence-gain-weights-v1`. Positive weights are assigned to evidence gap, uncertainty, feasibility, diversity, reversibility, market signal, and recency gap; negative weights are assigned to time and budget burden. The output stores normalized components and the final score.

8. Uncertainty model: uncertainty distinguishes missing evidence from inability. The UI and API expose uncertainty categories, evidence-gap notes, and confidence bands instead of presenting a single unexplained recommendation.

9. Evidence-gain calculation: expected gain is computed from the current hypothesis/evidence gaps and experiment properties; actual gain can be recorded later as user-reported outcome data without overwriting the Evidence Passport automatically.

10. Alternatives: alternatives are exposed through explicit endpoints and UI affordances for lower-cost, faster, more reversible, and different-signal experiments. Rejection reasons are stored as human-readable decision context.

11. Pareto design: the Career Transition Pareto Simulator generates transition paths and sorts them using deterministic non-dominated sorting across multiple objectives. Dominated paths remain visible for comparison.

12. Objectives: transition objectives include fit, time, cost, risk, learning load, market window, reversibility, evidence confidence, and support availability.

13. Non-dominated sorting: a path dominates another path only when it is at least as good on all objectives and better on at least one objective. No universal "best career path" is emitted.

14. Presets: transition presets provide balanced, low-cost, fast-prototype, low-risk, and support-heavy simulation defaults while keeping user inputs editable.

15. Robustness methodology: the Recommendation Robustness Lab reruns recommendation logic over controlled non-sensitive perturbations and reports how stable the recommendation surface remains.

16. Sensitivity metrics: robustness metrics include top-k overlap, rank stability, score movement, sensitivity matrix entries, dependency warnings, and feature-level perturbation summaries for weekly time, budget, market window, evidence recency, and support access.

17. Fairness audit methodology: fairness audits are synthetic-only MVP checks over counterfactual fixture sets. They report pass, review-required, and expected-contextual-difference statuses.

18. Synthetic fixtures: fixture groups cover gender-marker invariance, age-band invariance, caregiving-context differences, budget-access pressure, and support-access effects. No real protected-attribute user audit is performed.

19. Recommendation System Card: the system card is available as UI and machine-readable JSON. It documents purpose, users, excluded uses, data dependencies, user controls, human oversight, privacy, risks, limitations, validation status, and version.

20. DB entities: new SQLAlchemy entities persist adaptive runs/recommendations, transition simulations/paths, robustness runs, fairness audits, system card versions, originality research sessions, and originality audit events.

21. API endpoints: endpoints were added under `/api/v1` for adaptive experiment analysis/actions/outcomes/alternatives, transition simulation presets/runs/comparisons/journal/roadmap proposals, robustness runs/dependencies, fairness audits, system card, and consent-gated originality research sessions.

22. Routes: frontend routes include `/workspace/:profileId/adaptive-experiments`, `/workspace/:profileId/transition-simulator`, `/workspace/:profileId/recommendation-robustness`, `/research/robustness-lab`, and `/about/recommendation-system-card`.

23. Demo mode: demo seeding now creates representative adaptive recommendations, transition simulations, robustness analysis, fairness audit data, and a system card. Reset Demo includes the `originality_research` section and deletes pack records for demo profiles.

24. Research integration: originality research sessions require explicit consent, support baseline and experimental metrics, collect structured feedback, and expose filtered results.

25. Privacy/ethics: the pack avoids raw journal and transcript export by default, avoids automatic sensitive-attribute inference, avoids claims of scientific validation, and preserves user approval before roadmap or journal side effects.

26. Accessibility: the frontend uses semantic sections, buttons with icons and accessible labels, responsive tables, visible status/error messaging, keyboard-friendly controls, and print-aware system card styling.

27. Tests added: backend tests cover adaptive scoring, alternatives, rejection, start behavior, outcome recording, Pareto sorting, dominated-path visibility, scenario comparison, journal/roadmap proposal boundaries, robustness matrices, synthetic fairness, system card, consent gating, export filtering, and demo reset deletion. Frontend unit tests cover display mapping. Playwright tests cover the main workflows with mocked network responses.

28. Exact commands: backend targeted test, backend full test, backend compile check, frontend typecheck, frontend unit test, frontend build, frontend lint attempt, and frontend Playwright E2E were run. Screenshot commands were run against the live local app.

29. Backend targeted results: `.\.venv\Scripts\python.exe -m pytest tests\test_originality_research_engine.py -q` returned `4 passed, 399 warnings in 2.84s`.

30. Backend full results: `.\.venv\Scripts\python.exe -m pytest -q` returned `63 passed, 34555 warnings in 37.54s`.

31. Warning counts: backend targeted tests produced 399 warnings; backend full tests produced 34555 warnings. These were pre-existing warning categories surfaced by the wider suite and were not converted into failures.

32. Frontend unit results: `npm.cmd run test` returned `3 passed` test files and `16 passed` tests. Current rerun duration was `760ms`.

33. Typecheck: `npm.cmd run typecheck` returned exit code 0 and ran `tsc -b`.

34. Production build: `npm.cmd run build` returned exit code 0. Vite built successfully in `7.25s` and emitted the existing large-chunk warning for chunks over 500 kB.

35. Lint: `npm.cmd run lint` returned exit code 1 because the frontend package has no `lint` script. `npm.cmd run` confirms available scripts are `dev`, `typecheck`, `build`, `preview`, `test`, `test:e2e`, `test:e2e:roadmap`, `test:e2e:ui`, and `test:e2e:headed`.

36. Playwright: `$env:PLAYWRIGHT_FRONTEND_ONLY='true'; npm.cmd run test:e2e -- tests/e2e/originality-research.spec.ts` returned `4 passed (12.2s)` after selector fixes.

37. Browser/manual QA: the updated backend was verified with `GET http://127.0.0.1:8911/api/health` returning `{"status":"ok"}` and `GET http://127.0.0.1:8911/api/v1/recommendation-system-card.json` returning the system card JSON. The frontend was verified at `http://127.0.0.1:5176/`.

38. Screenshot paths: visual QA screenshots were saved to `docs/artifacts/originality-system-card.png` and `docs/artifacts/originality-robustness-lab.png`.

39. Limitations: the pack is deterministic MVP decision support, not a scientifically validated career prediction system. Fairness checks are synthetic only, robustness checks are local perturbation diagnostics, and production migrations should be added if the project adopts Alembic for this module.

40. Deferred work: future work should add migration files, expand expert-reviewed fairness fixtures, add longitudinal participant analysis, add richer scenario history pagination, and consider a formal frontend lint script for CI parity.
