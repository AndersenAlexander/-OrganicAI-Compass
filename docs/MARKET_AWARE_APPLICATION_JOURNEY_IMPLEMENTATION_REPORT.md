# Market-Aware Application Journey Implementation Report

## Created Files

- `backend/app/models/market_application.py`
- `backend/app/services/market_application_engine.py`
- `backend/app/routers/market_application.py`
- `backend/tests/test_market_application_engine.py`
- `backend/knowledge_base/market_aware_application_journey.md`
- `backend/knowledge_base/nav_stilling_feed_market_data.md`
- `backend/knowledge_base/evidence_locked_applications.md`
- `docs/MARKET_APPLICATION_RESEARCH_ARCHITECTURE.md`
- `frontend/src/types/marketApplication.ts`
- `frontend/src/api/marketApplicationApi.ts`
- `frontend/src/lib/marketApplicationMapping.ts`
- `frontend/src/lib/marketApplicationMapping.test.ts`
- `frontend/src/pages/MarketApplicationPage.tsx`
- `frontend/src/styles/market-application.css`
- `frontend/tests/e2e/market-application.spec.ts`
- `backend/alembic/versions/0007_market_application_provenance.py`
- `docs/MARKET_APPLICATION_WORKFLOW.md`

## Modified Files

- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `backend/app/models/__init__.py`
- `backend/app/routers/demo.py`
- `backend/app/services/demo_seed_service.py`
- `frontend/package.json`
- `frontend/playwright.config.ts`
- `frontend/src/config/navigation.ts`
- `frontend/src/main.tsx`
- `frontend/src/routes/router.tsx`
- `README.md`
- `frontend/src/api/journeyApi.ts`
- `frontend/src/pages/MyJourneyPage.tsx`

## Backend Endpoints

- `GET /api/v1/market/providers/status`
- `POST /api/v1/market/providers/demo/sync`
- `GET /api/v1/market/esco/status`
- `POST /api/v1/market/esco/normalise`
- `GET /api/v1/profiles/{profile_id}/market-radar`
- `PUT /api/v1/profiles/{profile_id}/market-preferences`
- `GET /api/v1/profiles/{profile_id}/jobs`
- `GET /api/v1/profiles/{profile_id}/jobs/{job_id}`
- `POST /api/v1/profiles/{profile_id}/jobs/{job_id}/save`
- `GET /api/v1/profiles/{profile_id}/job-analyses`
- `POST /api/v1/profiles/{profile_id}/job-analyses`
- `GET /api/v1/profiles/{profile_id}/job-analyses/{analysis_id}`
- `POST /api/v1/profiles/{profile_id}/job-analyses/{analysis_id}/match`
- `POST /api/v1/profiles/{profile_id}/job-analyses/{analysis_id}/confirm`
- `POST /api/v1/profiles/{profile_id}/job-analyses/{analysis_id}/readiness`
- `PATCH /api/v1/profiles/{profile_id}/job-requirements/{requirement_id}`
- `GET /api/v1/profiles/{profile_id}/master-career-profile`
- `GET /api/v1/profiles/{profile_id}/application-documents`
- `POST /api/v1/profiles/{profile_id}/application-documents`
- `GET /api/v1/profiles/{profile_id}/application-documents/{document_id}`
- `POST /api/v1/profiles/{profile_id}/application-documents/{document_id}/versions`
- `POST /api/v1/profiles/{profile_id}/application-documents/{document_id}/claims`
- `PATCH /api/v1/profiles/{profile_id}/document-claims/{claim_id}`
- `POST /api/v1/profiles/{profile_id}/document-claims/{claim_id}/confirm`
- `POST /api/v1/profiles/{profile_id}/document-claims/{claim_id}/evidence`
- `POST /api/v1/profiles/{profile_id}/application-documents/{document_id}/readiness`
- `POST /api/v1/profiles/{profile_id}/application-documents/{document_id}/export`
- `GET /api/v1/profiles/{profile_id}/applications`
- `POST /api/v1/profiles/{profile_id}/applications`
- `GET /api/v1/profiles/{profile_id}/applications/{application_id}`
- `PATCH /api/v1/profiles/{profile_id}/applications/{application_id}`
- `POST /api/v1/profiles/{profile_id}/applications/{application_id}/events`
- `POST /api/v1/profiles/{profile_id}/applications/{application_id}/stages`
- `POST /api/v1/profiles/{profile_id}/applications/{application_id}/outcome`
- `POST /api/v1/profiles/{profile_id}/applications/{application_id}/recalibrate`
- `GET /api/v1/profiles/{profile_id}/research-evaluation`
- `GET /api/v1/research/studies`
- `POST /api/v1/research/studies/ensure`
- `POST /api/v1/research/studies/{study_id}/profiles/{profile_id}/consent`
- `POST /api/v1/research/studies/{study_id}/profiles/{profile_id}/withdraw`
- `POST /api/v1/research/studies/{study_id}/profiles/{profile_id}/sessions`
- `POST /api/v1/profiles/{profile_id}/research-sessions/{session_id}/responses`
- `POST /api/v1/profiles/{profile_id}/research-sessions/{session_id}/metrics`
- `GET /api/v1/research/studies/{study_id}/summary`
- `POST /api/v1/research/studies/{study_id}/exports`
- `GET /api/v1/research/exports/{export_id}`

## Frontend Routes

- `/workspace/:profileId/market-radar`
- `/workspace/:profileId/job-analyzer`
- `/workspace/:profileId/job-analyzer/:analysisId`
- `/workspace/:profileId/application-studio/:analysisId`
- `/workspace/:profileId/applications`
- `/workspace/:profileId/applications/:applicationId`
- `/workspace/:profileId/research-evaluation`

## Compliance And Safety

- The deprecated NAV public feed is not used.
- NAV credentials are backend-only.
- The frontend calls only OrganicAI backend endpoints.
- Inactive or deleted records are not shown as active opportunities.
- URL-import analysis uses a backend allowlist and private-IP guard.
- Provider freshness, availability, fallback, source-window, and coverage metadata are exposed with the market result.
- Extracted requirements remain non-authoritative until the user confirms each active item; unconfirmed items are not evidence-assessed.
- Document claims carry deterministic Evidence Lock support states and version snapshots.
- Market signals are labelled as observed dataset signals, not predictions.
- Application Studio does not auto-apply and does not guarantee ATS outcomes.
- Outcome recalibration produces suggestions only and requires explicit confirmation before any roadmap change.
- Research export is pseudonymous and excludes raw personal text fields.

## Verification Commands

- `backend/.venv/Scripts/python.exe -m compileall app`
- `backend/.venv/Scripts/python.exe -m pytest tests/test_market_application_engine.py -q`
- `backend/.venv/Scripts/python.exe -m pytest tests -q`
- `frontend/npm.cmd run test -- marketApplicationMapping`
- `frontend/npm.cmd run test`
- `frontend/npm.cmd run typecheck`
- `frontend/npm.cmd run build`
- `frontend/npm.cmd run test:e2e -- market-application.spec.ts`
- `frontend/npm.cmd run test:e2e -- career-resilience.spec.ts`

Lint note: the frontend did not have an ESLint configuration or `lint` script before this work. An attempted ESLint dev-dependency install hit npm peer-resolution friction and then stalled on retry, so lint was not added. TypeScript, Vitest, production build, and Playwright checks were run instead.

## Current Limitations

- Live NAV sync is disabled until backend credentials and operational review are supplied.
- ESCO web lookup is not active by default; raw/local fallback terms remain visible.
- Demo vacancies are fictional and must not be interpreted as current Norwegian market coverage.
- Migration `0007_market_application_provenance` adds the provenance, confirmation, readiness, Evidence Lock, and tracker snapshot fields. It is additive and preserves existing records.
