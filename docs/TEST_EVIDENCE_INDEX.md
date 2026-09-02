# Test Evidence Index

Results below are the 2026-08-24 release-candidate audit results. Technical evidence shows implemented behavior under the stated test conditions; it is not empirical participant evidence.

| Capability | Test evidence | Test type | Result | Evidence class |
|---|---|---|---|---|
| Authentication, token handling, origin controls | `backend/tests/test_auth_regression.py` | Backend focused | Passed within 46 focused checks | TECHNICAL |
| Ownership/access control across owned resources | `backend/tests/test_task15a_security_authorization.py` | Backend focused | Passed within 46 focused checks | TECHNICAL |
| Diagnostic persistence and Human Potential Map | `backend/tests/test_human_diagnostic_v2.py`; isolated human-diagnostic Playwright journey | Backend + browser | Backend passed; browser journey reached post-diagnostic career flow before runner teardown | TECHNICAL |
| Evidence separation, explicit confirmation and recalibration boundary | `backend/tests/test_evidence_calibration_loop.py` | Backend focused | Passed within 46 focused checks | TECHNICAL |
| Market/application provenance, requirement confirmation and Evidence Lock | `backend/tests/test_market_application_engine.py` | Backend focused | Passed within 46 focused checks | TECHNICAL |
| Interview observable feedback and source separation | `backend/tests/test_interview_journey_engine.py` | Backend focused | Passed within 46 focused checks | TECHNICAL |
| Roadmap/recommendation provenance and controlled mutations | `backend/tests/test_human_diagnostic_v2.py`, `test_evidence_calibration_loop.py` | Backend focused | Passed within 46 focused checks | TECHNICAL |
| Adaptive Evidence-Gain and no automatic evidence promotion | `backend/tests/test_originality_research_engine.py` | Backend focused | Passed within 46 focused checks | TECHNICAL |
| Pareto dominance and robustness scenarios | `backend/tests/test_originality_research_engine.py` | Backend focused | Passed within 46 focused checks | TECHNICAL |
| Synthetic isolation | `backend/tests/test_originality_research_engine.py` | Backend focused | Passed within 46 focused checks | SYNTHETIC |
| Demo seed regression | `backend/tests/test_demo_account.py` | Backend targeted | 9 passed | TECHNICAL |
| Broad backend regression | `python -m pytest -q` | Backend full | 229 passed, 5 PostgreSQL-only skipped, 86 warnings | TECHNICAL |
| Frontend component/unit behavior | `npm.cmd run test` | Frontend unit | 19 files, 80 tests passed | TECHNICAL |
| Type correctness and production build | `npm.cmd run typecheck`; `npm.cmd run build` | Frontend quality | Passed; build has chunk-size warnings | TECHNICAL |
| Accessibility/theme/viewport visual smoke | `frontend/tests/e2e/staging-accessibility-visual.spec.ts` | Playwright isolated | 1 passed; 42 local screenshots | TECHNICAL |
| Core browser selection | Focused Playwright selection | Playwright isolated | 44 assertions passed; two stale test selectors were corrected and rerun separately | TECHNICAL |
| Live PostgreSQL runtime, real-account authentication and existing-data validation | Configured runtime only | Runtime UAT | Blocked: PID 15464 is Docker Desktop proxy; Docker logs show its VM endpoint `192.168.65.7:2376` is unroutable and SQLAlchemy `SELECT 1` times out. | PENDING |

The fresh migration upgrade passed only on a disposable SQLite audit database. Fresh/existing PostgreSQL migration checks remain pending because the Docker Desktop VM/backend is unreachable beyond the local port proxy.
