# Week 7 stabilisation and release-candidate report

Date: 2026-08-20  
Scope: feature-frozen stabilisation, defect fixing, full local verification and thesis/claim consistency.

## Executive verdict

**Stable Internal Release Candidate.** No unresolved Critical or High release-blocking defect was found in the documented local scope. Public production readiness is not claimed.

The application remains suitable for controlled internal UAT and supervisor demonstration. Empirical participant evaluation is **PENDING / NOT EXECUTED**.

## 1. Baseline validation before Week 7 fixes

The baseline available at the start of this pass was:

| Area | Baseline result |
| --- | --- |
| Backend | `215 passed, 5 skipped, 85 warnings` |
| Frontend Vitest | `15 files passed, 54 tests passed` |
| Frontend typecheck | Passed |
| Frontend production build | Passed; existing large-chunk warning |
| Browser extension | TypeScript build passed |
| Python | `compileall -q app` passed |
| Alembic | One source head, `0009_collaboration_traceability_extensions` |
| Focused core Playwright | `18/18 passed` |
| Release/privacy/persistence Playwright | `9/9 passed` |
| Light/Dark/responsive Playwright | `10/10 passed` |
| Real non-demo UAT | Assertions passed; managed-server teardown timed out |

A broader pre-fix Playwright run exposed 18 stale Home tests expecting the retired `HeroVideoSlider` and “Welcome…” headline. The current product renders the feature-frozen Living Compass homepage; the tests were corrected to that existing UI contract.

## 2. Consolidated defect register

| ID | Title / category | Severity | Reproducibility | Status and evidence | Deferred reason |
| --- | --- | --- | --- | --- | --- |
| W7-001 | Home E2E contract referenced retired hero component; regression | MEDIUM | Reproduced in 18 tests | **Fixed** by updating assertions to Living Compass; focused result `18/18`, included in final `144/144` | None |
| W7-002 | Playwright managed-server teardown can leave Windows child processes; test infrastructure | MEDIUM | Reproduced with fresh DB and isolated ports after successful assertions | **Deferred with runbook**; [WEEK7_TEST_RUNBOOK.md](WEEK7_TEST_RUNBOOK.md) and cleanup script use dedicated ports and explicit cleanup | Playwright ignores graceful shutdown on Windows; no safe assertion change available |
| W7-003 | Reused local Playwright DB can have stale schema; test hygiene | LOW | Reproduced when `DB_AUTO_CREATE_SCHEMA=true` meets an old file | **Mitigated** with fresh migration-first script and `PLAYWRIGHT_DATABASE_URL` | Existing developer-local files are not automatically deleted outside the dedicated clean path |
| W7-004 | Frontend production chunks exceed 500 kB; performance advisory | LOW | Reproduced on every production build | **Deferred**; no core regression or failed route load observed | Code splitting is cosmetic at this stage; router already lazy-loads major workspace pages |
| W7-005 | `python-jose` emits `datetime.utcnow()` deprecation warnings; dependency maintenance | LOW | Reproduced in backend tests, 85 warnings | **Deferred**; no functional failure | Requires dependency compatibility review rather than a speculative local patch |
| W7-006 | NAV/live market and voice providers unavailable without credentials; provider-dependent | MEDIUM | Reproduced in current environment | **Explicit fallback verified**; UI distinguishes unavailable/not configured from success | Requires external credentials, provider acceptance and privacy/operational review |
| W7-007 | Empirical participant evaluation not executed; research status | LOW | Confirmed by project evidence inventory | **Explicitly documented as pending** in README, system card and thesis note | Requires participant recruitment, protocol, consent and analysis outside this coding pass |

Counts: **Critical 0; High 0; Medium 3; Low 4.** The medium items are either fixed or documented external/test-harness limitations; none is an unresolved product release blocker for internal UAT.

## 3. Release-blocking criteria

No unresolved finding indicated data loss, cross-user access, hidden authoritative mutation, migration failure, broken core persistence, unsafe token handling, unsupported evidence promotion or inaccurate provenance.

## 4. Final regression

| Area | Final result |
| --- | --- |
| Backend | `215 passed, 5 skipped, 85 warnings` |
| Frontend Vitest | `15 files passed, 54 tests passed` |
| Typecheck | Passed |
| Production build | Passed; 3,258 modules transformed |
| Browser extension build | Passed |
| Python compileall | Passed |
| Frontend-only Playwright | `144 passed` (`84 + 60` batch runs) |
| Accessibility visual smoke | `1 passed` across Light/Dark and 390/820/1440 viewports |
| Core module subset | `18/18 passed` |
| Privacy/auth/persistence subset | `9/9 passed` |
| Light/Dark/mobile subset | `10/10 passed` |
| Real-user integration | Journey assertions passed on a fresh non-demo UAT account; teardown limitation remains |

The 144 frontend-only tests cover authentication states, diagnostic, career resilience, market/application, interview, innovation extensions, originality, privacy, persistence, Light Mode, Dark Mode, mobile containment, RAG fallback and public navigation.

## 5. Playwright teardown and database hygiene

The teardown issue is an external Windows process-lifecycle limitation, not an assertion or product failure. Playwright’s installed type definition explicitly states that graceful shutdown is ignored on Windows. A run can pass its assertions and still leave `cmd.exe`, Node or Python descendants when the outer command is forcibly terminated.

The Week 7 clean-run smoke reproduced this precisely: the isolated Human Diagnostic spec passed its single assertion in approximately 7.5 seconds, while the outer command reached its 180-second timeout during managed teardown. A scoped post-timeout check found no listeners left on the dedicated ports after cleanup.

The supported procedure is [scripts/playwright-clean-run.ps1](../scripts/playwright-clean-run.ps1), which:

- deletes only `backend/tmp/playwright-clean.db`;
- runs `alembic upgrade head` first;
- uses dedicated ports `8036` and `5196`;
- sets `PLAYWRIGHT_DATABASE_URL` and the backend interpreter explicitly;
- cleans only listeners on those dedicated ports.

The old default developer-local database is not a production database and must not be used as automated-test state.

## 6. Migration status

- `alembic heads`: one head, `0009_collaboration_traceability_extensions`.
- `alembic history`: linear revisions `0001` through `0009`, no duplicate IDs observed.
- Fresh `<base> → head`: passed.
- Fresh `<base> → 0008 → head`: passed.
- Runtime development database: current at `0009_collaboration_traceability_extensions`.
- No schema drift or missing table/column assumptions were observed in the tested runtime.

## 7. Accessibility and responsive audit

The final local audit covered:

- semantic headings and accessible names on critical routes;
- focusability of links/buttons;
- radio groups and range inputs in Diagnostic;
- live status regions for diagnostic, resilience, interview and originality workflows;
- keyboard/ARIA feedback controls in RAG;
- visible focus and no horizontal overflow;
- 1920-class desktop, 1440/1448 desktop, tablet `820×1180` and mobile `390×844` layouts;
- Light Mode contrast/readability and Dark Mode inverse surfaces.

The focused visual accessibility smoke passed `1/1`. This is a structural/UI smoke, not a formal WCAG certification or full axe audit.

## 8. Privacy and security audit

Automated backend security/privacy suites passed within the full backend result, including auth sessions, privacy lifecycle, route authorization, profile ownership, demo separation, extension token binding and originality ownership. The frontend suites passed privacy center, export, account deletion, ephemeral conversation, provider status and URL-token cleanup.

Validated boundaries include:

- unauthorized profile access rejected with `403`;
- demo data separated from non-demo users and research export defaults;
- advisor scope excludes private transcripts and job-loss fields unless explicitly allowed;
- browser capture is user-triggered, reviewable and confirmed before analysis;
- external URL fetching is allowlisted and guarded against private/local targets;
- unsupported application/interview claims are blocked or require confirmation;
- raw voice provider keys remain backend-only and disabled voice falls back safely.

## 9. Real-user, ownership and mutation audit

The fresh non-demo UAT flow persisted diagnostic, map, hypothesis, evidence gap, experiment, evidence proposal, recalibration, capture, job analysis, application, interview, mock session, outcome, advisor review, journal and originality records. Logout/login persistence passed in the full integration journey.

The second-user isolation flow attempted access to the first user’s profile context and received safe rejection. Backend ownership tests also cover hypotheses, evidence, experiments, job analyses, applications, interviews, advisor shares, journal entries and originality runs.

Authoritative boundaries verified:

- interpretation remains editable and does not silently become confirmed assessment data;
- experiment output creates a provisional evidence proposal;
- Evidence Passport promotion requires explicit user review;
- actual experiment gain does not auto-create verified evidence;
- roadmap actions require explicit confirmation;
- outcome recalibration stores suggestions and before/after context without automatic profile mutation;
- advisor comments are human feedback and do not silently rewrite the profile;
- transcript retention requires explicit confirmation;
- application and interview status changes require explicit confirmation where configured.

## 10. Missing-data and uncertainty audit

The tested modules preserve `MISSING`, `INSUFFICIENT INFORMATION`, `UNKNOWN`, `PENDING REVIEW`, provider coverage limits and synthetic-only labels. Missing evidence is not converted into zero capability, low capability or automatic rejection. This was checked in diagnostic, Evidence Passport, readiness, market coverage, robustness and fairness fixtures.

## 11. Originality layer regression

Deterministic backend and E2E fixtures passed for:

- Adaptive Evidence-Gain alternatives, rejection, start and outcome boundaries;
- lower-effort, higher-evidence and no-action/reflection options;
- Pareto non-dominated and dominated paths, dominated-by explanations and saved scenarios;
- robustness perturbations, rank stability, top-k overlap, fit-band stability and dependency warnings;
- Synthetic Fairness results with contextual differences separated from capability;
- Recommendation Provenance with input trace, rule/algorithm versions, source versions and limitations;
- Recommendation System Card purpose, inputs, outputs, oversight, privacy and validation status.

The real UAT continuation produced 8 recommendations, 4 transition paths and 5 robustness scenarios. Fairness remained `synthetic_only=true`; no fairness certification claim was made.

## 12. Provider and Demo Mode status

NAV/live market and voice providers are unavailable in this environment. The UI and backend expose this as unavailable/not configured or fallback state; deterministic demo data is not presented as live market success.

The deterministic Demo Mode seed/reset path covers diagnostic, profile, recommendations, roadmap, resilience, market/application, interview, innovation extension and originality records. Backend demo-account tests verify idempotence, reset isolation and research separation; frontend demo journeys passed. Demo content is fictional and not participant evidence.

## 13. Error-state matrix

Covered by backend and frontend fixtures:

| Failure | Expected behavior | Result |
| --- | --- | --- |
| Backend/API unavailable | clear fallback/retry and no fabricated success | Passed |
| Expired auth / URL token | safe redirect or token removal | Passed |
| Provider unavailable / voice disabled | explicit fallback | Passed |
| Invalid advisor token | access failure without private data | Passed |
| Browser capture rejected/unconfirmed | review boundary blocks analysis | Passed |
| No confirmed evidence | readiness/proposal remains uncertain | Passed |
| Incomplete diagnostic / partial autosave | progress and missing state remain visible | Passed |
| Partial interview | text fallback and incomplete state remain explicit | Passed |

The synthetic staging forbidden-route check must run with `APP_ENV=test` or `staging`; in development it intentionally returns 404 and was not counted as a product defect.

## 14. Performance and route loading

The production build transformed 3,258 modules. Existing advisory chunks include approximately:

- `index`: 1,639.49 kB;
- `react-three-fiber.esm`: 866.39 kB;
- `index` CSS: 517.55 kB.

Major workspace pages are already lazy-loaded in the router. Further splitting is deferred because it is performance polish and the current build is stable.

## 15. Claim-to-evidence review

| Claim family | Classification |
| --- | --- |
| Implemented modules and boundaries | `IMPLEMENTED` |
| Backend/frontend/unit/E2E behavior in this report | `AUTOMATED-TESTED` |
| Real non-demo persistence and ownership smoke | `MANUALLY-VALIDATED` + automated integration assertions |
| Deterministic Demo Mode journey | `DEMO-ONLY` |
| NAV, voice, OpenAI, ElevenLabs, email, cloud and production operations | `PROVIDER-DEPENDENT` / `NOT YET VALIDATED` |
| Synthetic fairness | `AUTOMATED-TESTED` synthetic engineering validation, not empirical fairness |
| Participant usefulness, trust, agency, statistical improvement and career outcomes | `NOT YET VALIDATED` |

No documentation or UI claim was accepted as empirical effectiveness. The thesis boundary is recorded in [WEEK7_THESIS_CLAIM_CONSISTENCY.md](WEEK7_THESIS_CLAIM_CONSISTENCY.md).

## 16. Demo and presentation package

- Stable deterministic profile: existing `demo-profile` seeded by Demo Mode; cross-module seed includes market, interview, innovation and originality state.
- 8–12 minute supervisor script: [WEEK7_DEMO_SCRIPT.md](WEEK7_DEMO_SCRIPT.md).
- Thesis/presentation screenshot checklist: [WEEK7_SCREENSHOT_CHECKLIST.md](WEEK7_SCREENSHOT_CHECKLIST.md).
- Clean test and demo fallback procedure: [WEEK7_TEST_RUNBOOK.md](WEEK7_TEST_RUNBOOK.md).

## 17. Known limitations and deferred issues

- Empirical participant evaluation: `PENDING / NOT EXECUTED`.
- Public production deployment, operational monitoring and penetration testing: not validated.
- Legal/privacy approval: pending external review.
- NAV/live market credentials and validation: unavailable locally.
- Voice provider credentials and live acceptance: unavailable locally.
- PostgreSQL/cloud/email provider operations: external/manual gates.
- Windows Playwright managed-server teardown: runbook workaround required when forcibly interrupted.
- Dedicated clean Playwright DB required; stale developer-local DBs are unsupported.
- Large frontend chunks and `python-jose` deprecation warnings remain non-blocking advisories.

## 18. Files changed in Week 7

Feature-frozen Week 7 changes:

- `README.md` — current internal RC status and evidence links;
- `docs/RELEASE_CANDIDATE_0_9_0_RC2.md` — current head/count/status reconciliation;
- `docs/WEEK7_STABILISATION_RELEASE_REPORT.md` — this report;
- `docs/WEEK7_TEST_RUNBOOK.md` — clean DB and Windows teardown procedure;
- `docs/WEEK7_THESIS_CLAIM_CONSISTENCY.md` — thesis claim boundary;
- `docs/WEEK7_DEMO_SCRIPT.md` — supervisor demo script;
- `docs/WEEK7_SCREENSHOT_CHECKLIST.md` — screenshot checklist;
- `scripts/playwright-clean-run.ps1` — dedicated fresh DB/migration/cleanup path;
- Home E2E suites — assertions aligned with the existing Living Compass contract.

Other dirty-worktree changes predate this Week 7 pass and were preserved.

## 19. Week 7 exit criteria

| Criterion | Verdict |
| --- | --- |
| No unresolved Critical defect | Pass |
| No unresolved High defect affecting core journey | Pass |
| Full regression scope documented | Pass |
| Accessibility/privacy/security audit completed for local scope | Pass with formal axe/penetration/legal limits documented |
| Migrations healthy | Pass |
| Provider fallbacks explicit | Pass |
| Demo workflow stable | Pass |
| Documentation matches current head/status | Pass for current release documents |
| Known limitations documented | Pass |
| Thesis claims evidence-aligned | Pass |
| Ready for Week 8 presentation preparation | Pass |

**Final classification: STABLE INTERNAL RELEASE CANDIDATE.**
