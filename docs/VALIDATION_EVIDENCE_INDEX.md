# Validation Evidence Index

Date: 2026-08-20

This index points to the current Week 7 stabilisation evidence, plus the relevant recorded evidence from earlier tasks. Historical rows retain their original dates and results; the current release authority is the Week 7 report. Evidence files avoid raw secrets and do not include personal data dumps.

| Task | Test / audit | Actual result | Date | Evidence path | Status |
| --- | --- | --- | --- | --- | --- |
| Final RC audit | Source/migration/runtime consolidation | Source graph has one head `0010_alembic_version_capacity`; fresh disposable SQLite upgrade passed; backend `229 passed, 5 PostgreSQL-only skipped`; frontend unit `80 passed`; typecheck/build passed; accessibility visual smoke `1 passed` with 42 local screenshots. Configured PostgreSQL runtime connection timed out, so existing-DB/auth runtime UAT remains blocked. | 2026-08-24 | [TEST_EVIDENCE_INDEX.md](TEST_EVIDENCE_INDEX.md), [RELEASE_READINESS_MATRIX.md](RELEASE_READINESS_MATRIX.md) | Not UAT-ready until PostgreSQL restored |
| Week 7 | Feature-frozen stabilisation and release-candidate verification | Backend `215 passed, 5 skipped, 85 warnings`; frontend unit `54 passed`; frontend-only Playwright `144 passed`; accessibility/visual smoke `1 passed`; typecheck, frontend build, browser-extension build, Python compile and Alembic upgrade-to-head passed; current head `0009_collaboration_traceability_extensions`. | 2026-08-20 | [WEEK7_STABILISATION_RELEASE_REPORT.md](WEEK7_STABILISATION_RELEASE_REPORT.md) | Stable Internal Release Candidate |
| 13B.0.5 | Local release-candidate validation summary | Backend full non-PostgreSQL `160 passed`; PostgreSQL marker `5 passed`; frontend unit `29 passed`; Playwright `140 passed, 1 skipped`; source archive regression passed. | 2026-07-30 | [final-test-summary.json](../evidence/task13b05/final-test-summary.json) | Recorded historical evidence |
| 13C.0.2 | Local production rehearsal final summary | Local release candidate, local staging and local production rehearsal passed; production deployment and operations remained blocked. | 2026-08-03 | [final-summary.json](../evidence/task13c02/final-summary.json) | Recorded historical evidence |
| 14D | Week 6 originality/research gap audit | Week 6 audit classified implemented, incomplete and external/manual areas; no provider calls or secret values recorded. | 2026-08-05 | [week6-gap-audit.json](../evidence/task14d/week6-gap-audit.json) | Recorded historical evidence |
| 15A | Security authorization evidence | Targeted security validation recorded `22 passed, 41 warnings`, market/originality engine regression `11 passed`, route blockers `0`. | 2026-08-09 | [README.md](../evidence/task15a/README.md) | Passed |
| 15B | Human discovery final summary | Backend targeted `21 passed`, frontend unit `32 passed`, typecheck/build passed, guided E2E `1 passed`, route blockers `0`; no schema migration. | 2026-08-09 | [final-summary.json](../evidence/task15b/final-summary.json) | Passed |
| 15C | Profile/demo/extension final summary | Backend extension/demo `16 passed`, Task 15B regression `21 passed`, Task 15A regression `22 passed`, frontend unit `36 passed`, browser-extension build passed, focused Playwright `3 passed`; no schema migration. | 2026-08-09 | [final-summary.json](../evidence/task15c/final-summary.json) | Passed |
| 15D | Git provenance | Same-lineage Git metadata recovered from local verified repository. | 2026-08-09 | [repository-provenance.json](../evidence/task15d/repository-provenance.json) | Passed |
| 15D | Release version inventory | Application version reconciled to `0.9.0-rc.1`; extension remains `0.1.0`. | 2026-08-09 | [version-inventory.json](../evidence/task15d/version-inventory.json) | Passed |
| 15D | Alembic head/history | Current source head is `0004_provider_operations`; Task 15D added no migration. | 2026-08-09 | [alembic-inventory.json](../evidence/task15d/alembic-inventory.json) | Passed |
| 15D | Source hygiene | No tracked real env/database/dependency/build/log/archive artifacts found by filtered Git check. | 2026-08-09 | [source-tree-hygiene.json](../evidence/task15d/source-tree-hygiene.json) | Passed |
| 15D | Repository safety scan | Repository safety audit passed with `0` blocking findings and no secret values included. | 2026-08-09 | [secret-scan-summary.json](../evidence/task15d/secret-scan-summary.json) | Passed |
| 15D | Sanitized archive scan | Archive created outside repo and verified with `0` forbidden entries and `0` blocking secret-like findings. | 2026-08-09 | [archive-scan.json](../evidence/task15d/archive-scan.json) | Passed |
| 15D | Documentation reconciliation | Stale version/Alembic/readiness claims reconciled. | 2026-08-09 | [documentation-reconciliation.json](../evidence/task15d/documentation-reconciliation.json) | Passed |
| 15D | Focused validation summary | Backend, frontend, browser-extension, security and archive validations passed; PostgreSQL not executed because no schema change. | 2026-08-09 | [validation-summary.txt](../evidence/task15d/validation-summary.txt) | Passed |
| 15D | Release manifest | Local dissertation RC manifest recorded. | 2026-08-09 | [release-manifest.json](../evidence/task15d/release-manifest.json) | Passed |
| 15D | Final summary | Task 15D classification: passed local repository/release reconciliation. | 2026-08-09 | [final-summary.json](../evidence/task15d/final-summary.json) | Passed |
| 15E | Baseline freeze | Branch `release/task13c-local-production-rehearsal`, baseline commit `e8c7a559c54a2caa848e41e7393b014f9c50ca17`, clean initial tree. | 2026-08-09 | [baseline.json](../evidence/task15e/baseline.json) | Passed |
| 15E | Historical migration check | `0001_initial_schema.py` has no diff in the Task 15D release commit; no semantic rewrite detected for final acceptance. | 2026-08-09 | [historical-migration-check.json](../evidence/task15e/historical-migration-check.json) | Passed |
| 15E | Backend safe regression | `189 passed`, `5 deselected`, `85 warnings`; PostgreSQL-marked tests excluded from this SQLite/local-safe run. | 2026-08-09 | [backend-full-regression.txt](../evidence/task15e/backend-full-regression.txt) | Passed |
| 15E | PostgreSQL final validation | Guarded target is disposable, but Docker is unavailable and local port `55432` is closed; PostgreSQL gate not executed. | 2026-08-09 | [postgres-final-validation.txt](../evidence/task15e/postgres-final-validation.txt) | Not executed |
| 15E | Route authorization | `blockingFindingCount = 0`, `advisoryFindingCount = 257`. | 2026-08-09 | [task15a-route-authorization-audit.json](../evidence/task15e/task15a-route-authorization-audit.json) | Passed |
| 15E | Task 15A regression | `5 passed`, `29 warnings`. | 2026-08-09 | [task15a-security-regression.txt](../evidence/task15e/task15a-security-regression.txt) | Passed |
| 15E | Task 15B regression | `8 passed`. | 2026-08-09 | [task15b-regression.txt](../evidence/task15e/task15b-regression.txt) | Passed |
| 15E | Task 15C regression | `2 passed`, `1 warning`. | 2026-08-09 | [task15c-regression.txt](../evidence/task15e/task15c-regression.txt) | Passed |
| 15E | Frontend unit/type/build | Unit `36 passed`; typecheck passed; production build passed with Vite large-chunk advisory only. | 2026-08-09 | [frontend-unit-validation.txt](../evidence/task15e/frontend-unit-validation.txt) | Passed |
| 15E | Browser extension validation | TypeScript build passed; manifest is MV3 with local-only host permissions. | 2026-08-09 | [browser-extension-validation.txt](../evidence/task15e/browser-extension-validation.txt) | Passed |
| 15E | Playwright local-safe regression | `137 passed`, `1 skipped`; staging-origin specs requiring port `18080` excluded from local-safe run. | 2026-08-09 | [playwright-local-safe-regression.txt](../evidence/task15e/playwright-local-safe-regression.txt) | Passed with limitation |
| 15E | Repository safety | Repository safety scan has `0` blocking findings; tracked-file check has `0` forbidden tracked paths. | 2026-08-09 | [repository-safety-final.json](../evidence/task15e/repository-safety-final.json) | Passed |
| 15E | Final acceptance matrix | Dissertation software acceptance matrix and limitation boundary recorded. | 2026-08-09 | [DISSERTATION_SOFTWARE_ACCEPTANCE.md](DISSERTATION_SOFTWARE_ACCEPTANCE.md) | Accepted with limitations |
| 16A | RIASEC-inspired Natural Discovery audit | Existing Natural Discovery inventoried; R/I/A/S/E/C coverage audited; decision `PARTIAL COVERAGE`; six direct preference items added with no schema migration. | 2026-08-09 | [question-inventory.json](../evidence/task16a/question-inventory.json), [riasec-coverage-audit.json](../evidence/task16a/riasec-coverage-audit.json) | Passed |
| 16A | RIASEC scoring and regression validation | Backend `31 passed`; route blockers `0`; frontend unit `39 passed`; typecheck/build passed; focused E2E `1 passed`. | 2026-08-09 | [final-summary.json](../evidence/task16a/final-summary.json) | Passed |
| 16B | RIASEC integration acceptance and RC2 validation | Task 16A integrated into release branch; application version reconciled to `0.9.0-rc.2`; backend/frontend/E2E/Alembic/source/archive gates recorded. | 2026-08-09 | [final-summary.json](../evidence/task16b/final-summary.json), [release-manifest-rc2.json](../evidence/task16b/release-manifest-rc2.json) | Passed |

## Commands

```powershell
python -m alembic heads
python -m alembic history
python -m app.scripts.audit_route_authorization
python -m app.scripts.audit_repository_safety --root ..
python -m pytest tests/test_task15a_security_authorization.py tests/test_task15b_human_discovery_architecture.py tests/test_task15c_profile_demo_extension.py
npm run typecheck
npm run build
npm run test -- src/lib/activeProfile.test.ts src/lib/humanDiscoveryJourney.test.ts
npm run build
python -m app.scripts.create_source_archive --output "$env:TEMP\organicai-task16b\OrganicAI-Compass-source-final-0.9.0-rc.2.zip"
```

Frontend `npm run typecheck` and focused `npm run test` initially hit the Windows sandbox `EPERM` condition on `C:\Users\achid`; approved reruns passed.
