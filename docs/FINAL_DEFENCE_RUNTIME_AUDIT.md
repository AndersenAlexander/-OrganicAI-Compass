# Final Defence Runtime Audit

Date: 2026-09-02  
Safety checkpoint: `93c0eadfa14476262626ff6d844a955a7cf63e45` (`stabilize final defence demo runtime`)  
Final classification: **READY WITH MINOR WARNINGS**

## Runtime baseline

| Item | Verified state |
| --- | --- |
| Frontend | `http://127.0.0.1:5192` (HTTP 200) |
| Backend | `http://127.0.0.1:8022` (`/health` and `/api/health` HTTP 200) |
| Backend worktree | `C:\Users\alexa\Desktop\31.08\1. OrganicAI Compass\backend` |
| Persistence | Isolated `backend/tmp/organicai-local-demo.db`; normal PostgreSQL was not used or changed |
| SQLite safety | WAL; `busy_timeout=10000`; locking `normal`; foreign keys enabled; passive checkpoint not busy |
| Pool | QueuePool size 5, overflow 10, timeout 30 seconds, pre-ping enabled |
| Final listeners | Frontend PID 47880; backend PID 9304 at the final audit point |

The first launch attempt was discarded because a stale 8022 process reclaimed its port between inspection and launch. The exact stale 5192/8022 listeners were stopped, both ports were verified free, and the clean cold start was repeated successfully. The final backend startup log identifies this worktree, the isolated Demo DB, and the SQLite pragmas above.

## Safety checkpoint inventory

The checkpoint captured 180 paths: functional backend/frontend changes, tests and E2E coverage, documentation/knowledge assets, the generated RAG index, presentation screenshots, migrations, and small design metadata. It also preserves the pre-existing tracked deletion of 33 legacy `scripts/` utilities. Ignored runtime databases, credentials, and logs were not committed.

Twenty-five isolated lock/stress scripts, databases, and logs from the previous SQLite incident investigation were removed. The active Demo DB, current logging configuration, and validation log were retained.

## Presentation journey

| Area | Result | Evidence |
| --- | --- | --- |
| Home / entry | PASS | Living Compass rendered, theme toggled, navigation worked, no broken images or page overflow |
| Demo login | PASS | HTTP 200 in about 1.01 s; one Demo user and one `demo-profile`; refresh persisted the session |
| Human Diagnostic | PASS | Completed self-reflection result rendered without reset |
| Human Potential Map | PASS | Archetype, answer coverage, Career Interests, AI Collaboration Style, signals and interpretation rendered |
| Career Compatibility | PASS | Nine unique returned directions; one saved priority and eight suggestions; all five score dimensions rendered; compare opened |
| Career Experiment | PASS | Two existing sessions preserved; current in-progress experiment, deterministic rubric and roadmap-link state rendered; no new experiment created |
| Evidence Passport | PASS | 34 skill records; six practically verified; self-reported/needs-verification states and provenance rendered separately |
| Career Resilience | PASS | Current hypotheses, evidence states and recalibration history rendered; focused engine/E2E tests confirm Natural Fit is not mutated by experiment evidence |
| My Roadmap | PASS | 18 actions: 3 completed, 4 active, 0 blocked; 24% progress; refresh preserved state; no automatic employment mutation |
| My Journey | PASS | Correct Demo profile selected; 3 applications, 3 interviews, 1 completed interview and 1 offer review; `roadmap_mutated=false` |
| Market Radar / Job Analyzer | PASS | Pages loaded; 10 recurring requirement signals and 6 emerging signals rendered; no duplicate job IDs; zero active jobs in the current provider sample |
| Application Tracker | PASS | Three unique applications with coherent Saved, Recruiter screening and Rejected stages |
| Interview Journey | PASS | Three unique interviews; dashboard, preparation, text simulation and reflection routes rendered; eight STAR stories persisted |
| Offer Review | PASS | One persisted offer review rendered with missing information explicitly separated |
| Decision Journal | PASS | Seven entries; User decision, Evidence, AI suggestions, and System suggestions/calculations rendered as separate categories |
| Logout / re-login | PASS | Logout 200, second Demo login 200, same user/profile reused, profile/experiment/application counts preserved |

No presentation action created an experiment, job, application, interview, story, offer, decision, or roadmap mutation.

## AI Coach rehearsal

All questions were sent through the real Demo browser to `POST /api/chat`. All returned HTTP 200, a visible concise answer, and no secret or fabricated identity data.

| # | Question | Grounding | Time | Words |
| --- | --- | --- | ---: | ---: |
| 1 | What is OrganicAI Compass? | Static KB, grounded, lexical retrieval fallback | 5.86 s | 34 |
| 2 | Why was this platform created? | Static KB, grounded, lexical retrieval fallback | 4.85 s | 38 |
| 3 | Does the LLM calculate my evidence score? | Static KB, grounded, lexical retrieval fallback | 4.46 s | 29 |
| 4 | What is my current career direction? | Persisted career hypotheses, profile-grounded | 3.55 s | 32 |
| 5 | What evidence has been practically verified for my current direction? | Persisted Evidence Passport, profile-grounded | 3.57 s | 22 |
| 6 | Which important evidence gaps are still unresolved? | Persisted Evidence Passport, profile-grounded | 4.08 s | 29 |
| 7 | How do career experiments work? | Static KB, grounded, lexical retrieval fallback | 5.37 s | 31 |
| 8 | Can you choose my career for me? | Static KB, grounded, lexical retrieval fallback | 5.87 s | 25 |
| 9 | Why did you use RAG instead of fine-tuning? | Static KB, grounded, lexical retrieval fallback | 5.58 s | 31 |
| 10 | What are the limitations of this prototype? | Static KB, grounded, lexical retrieval fallback | 4.97 s | 35 |

The exact wording of question 6 initially fell through to static knowledge. A bounded grounding-classifier fix now routes it to the persisted Evidence Passport; the corrected real-browser run and 50 focused grounding tests pass. The current priority context reports no unresolved gaps for the active hypotheses, while the wider Passport still visibly preserves skills that need verification.

## Browser, navigation and screens

- Refresh passed on Human Potential Map (1.30 s), Career Compatibility (1.24 s), Evidence Passport (1.85 s), My Roadmap (0.91 s), AI Coach (0.93 s), and Interview Journey (0.94 s).
- Browser Back/Forward navigation passed.
- Home, Human Potential Map, Career Compatibility, Evidence Passport, My Roadmap, AI Coach, Application Tracker and Interview Journey passed at both 1440x900 and 1920x1080.
- Every audited desktop page had zero document-level horizontal overflow.
- No broken images, uncaught page errors, white screens, database 503s, or application 5xx responses occurred.
- Rapid automated navigation cancelled in-flight media/API requests with `net::ERR_ABORTED`; these were navigation artefacts, not server failures.

Meaningful console/network findings:

- Expected unauthenticated bootstrap refresh calls returned 401 before a browser session existed.
- React development mode reports a cosmetic `fetchPriority` DOM-prop warning on the Home hero.
- ElevenLabs token issuance returned a safe 503 as described below.
- The corrected run emitted no Market research 403 and no panel-persona 404.

## Performance

All measured presentation interactions stayed below the 5–7 second risk threshold:

- Explore Demo: 1.01 s.
- Profile refresh: 1.30 s.
- Career Compatibility refresh: 1.24 s.
- Evidence Passport refresh: 1.85 s.
- Roadmap refresh: 0.91 s.
- First Coach answer: 5.86 s.
- Static-KB lexical fallback answers: 4.46–5.87 s.
- ElevenLabs token failure response: 2.53 s.

## Provider failure safety

### OpenAI / semantic retrieval

The real Coach used source-attributed lexical RAG fallback for static platform questions and profile-grounded deterministic answers for personal questions. Focused provider-failure tests confirm unavailable model calls degrade to deterministic/general answers without an infinite spinner or server error.

### ElevenLabs

`/api/voice/status` reports live voice enabled/configured, agent ID and API key configured, and legacy text/voice-message fallback enabled. The real token call returned HTTP 503 with the safe message `ElevenLabs is temporarily unavailable.` Backend evidence identifies a transport `ConnectError` (all connection attempts failed), so no WebRTC session, transcript, or spoken response could be completed during this audit. The application stayed usable and text chat remained available. This is an external dependency warning; no ElevenLabs architecture/configuration was changed.

### PostgreSQL

The backend remained healthy while explicitly bound to the isolated SQLite Demo database. Normal PostgreSQL settings and user data were untouched.

## Automated regression

- Backend targeted suite: **116 passed, 6 provider-gated skipped** in 49.28 s. Coverage included auth/Demo, DB observability, persistence, assessment/compatibility, resilience/evidence, employment, Coach/RAG and ElevenLabs.
- Backend grounding focus after the wording fix: **50 passed**.
- Frontend unit suite: **70 passed across 19 files**.
- Frontend type-check: **passed**.
- Instrumented real-browser audit: **passed** (complete journey, exact 10 Coach questions, refresh, resolution and console/network capture).
- Presentation E2E selection: **36/36 passed** after refreshing one obsolete Decision Journal mock fixture; it initially omitted required array fields, while real Demo data was valid.
- Additional read-only real-Demo semantic route audit: **passed**.

Expected test warnings: Python-JOSE `utcnow` deprecation, Node `NO_COLOR`/`FORCE_COLOR`, and localStorage availability in the Node unit environment.

## Issues and fixes

| Severity | Finding | Resolution |
| --- | --- | --- |
| Critical | Exact defence wording for unresolved evidence gaps used static KB instead of authenticated Evidence Passport context | Added the bounded phrase pattern and regression cases; corrected real-browser response is profile-grounded |
| Important | Decision Journal shared workbench requested panel personas at a nonexistent `/v1/interviews/panel-personas` path | Corrected frontend request to backend's `/v1/panel-personas`; real run returns 200 and panel E2E passes |
| Important | Market pages requested disabled research-only data on every section, producing misleading 403/panel warnings | Research data now loads only on the Research section; Market/Analyzer/Tracker no longer emit the 403 |
| Test-only | Decision Journal mock lacked current required arrays and caused a synthetic white screen | Updated the fixture; focused test passes; no production-data defect |

## Remaining warnings

- ElevenLabs could not be reached from the audit environment. Verify it shortly before the defence; use text chat if it remains unavailable.
- Cosmetic React `fetchPriority` development warning on Home.
- Known dependency/test deprecation warnings listed above.

No critical or important in-application blocker remains.
