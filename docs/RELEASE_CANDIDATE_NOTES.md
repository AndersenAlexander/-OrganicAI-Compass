# OrganicAI Compass 0.9.0-rc.2 Release Candidate Notes

Date: 2026-08-09

`0.9.0-rc.2` is the local dissertation release-candidate snapshot after Task 16B. It integrates Task 16A RIASEC-inspired Career Interests into the accepted RC1 lineage. It is not a public production release.

## Scope

- Security and authorization hardening from Task 15A is included.
- Unified human discovery and career assessment journey from Task 15B is included.
- Profile context, explicit demo isolation and browser-extension integration from Task 15C are included.
- Repository, release metadata, Alembic documentation, source hygiene and release evidence reconciliation from Task 15D are included.
- Task 15E dissertation acceptance and final regression evidence remain preserved.
- RIASEC-inspired Career Interests from Task 16A are included as a vocational-interest signal in Human Potential and Natural Fit interpretation.

## Assessment Architecture

The assessment journey separates Natural Discovery from Capability Assessment. Current scoring documentation and evidence use `career-scoring-v2-four-layer` with Natural Fit, Capability Fit, Evidence Strength and Transition Feasibility. Career hypotheses use `human-discovery-career-hypothesis v2` and preserve Market Fit and Support Fit as separate contextual dimensions instead of merging every signal into one opaque score.

Task 16A adds `riasec-career-interests-v1`, a deterministic RIASEC-inspired Career Interests layer covering Realistic, Investigative, Artistic, Social, Enterprising and Conventional preferences. It is explicitly not a validated psychometric test, personality diagnosis, career destiny model, employment predictor or guarantee.

## Security And Profile Boundaries

Task 15A keeps the route authorization blocker count at `0` and hardens previously exposed mutating, admin and provider routes. Remaining route audit findings are advisories for centralized optional-user handling and signed provider webhook handling, not blockers.

Task 15C keeps Demo Mode explicit. Normal authenticated users require an owned profile, active profile context is revalidated after session changes, logout clears stale profile context, and browser-extension capture is bound to the token owner and selected profile. Invalid, expired or wrong-profile extension capture is rejected.

## Implemented Dissertation Areas

The snapshot includes Natural Discovery, Human Potential Profile, Capability Assessment, Career Hypotheses, Evidence Passport, Career Experiments, Supported Paths, market-aware application workflows, Interview Journey, Adviser Collaboration, Career Encyclopedia, Decision Journal, adaptive evidence-gain ranking, transition Pareto simulation, recommendation robustness checks, synthetic fairness checks, recommendation provenance traces, optional RAG/voice architecture, and explicit Demo Mode.

## Versioning

- Application version: `0.9.0-rc.2`.
- Browser extension component version: `0.1.0`.
- Alembic source-code head: `0004_provider_operations`.
- Task 16B introduced no schema migration.

## Validation

- Route authorization audit: `0` blocking findings.
- Repository safety audit: `0` blocking findings.
- Backend Task 15A-C regression tests: `15 passed`.
- Frontend typecheck: passed.
- Frontend production build: passed with existing Vite chunk-size warnings.
- Focused frontend profile/discovery tests: `7 passed`.
- Browser extension TypeScript build: passed.
- Sanitized source archive verification: `0` forbidden entries and `0` blocking secret-like findings.
- Task 16B acceptance reran backend, frontend, E2E, Alembic, source-safety and archive validation gates; evidence is recorded in [../evidence/task16b](../evidence/task16b).

Detailed validation evidence is indexed in [VALIDATION_EVIDENCE_INDEX.md](VALIDATION_EVIDENCE_INDEX.md) and summarized under [../evidence/task15d](../evidence/task15d).

## Archive

Sanitized source archive:

```text
C:\Users\achid\AppData\Local\Temp\organicai-task16b\OrganicAI-Compass-source-final-0.9.0-rc.2.zip
```

SHA256:

```text
Recorded in evidence/task16b/release-manifest-rc2.json and evidence/task16b/archive-scan.json.
```

The archive was created outside the repository. It excludes real env files, local databases, dumps, logs, dependency directories, build outputs and local test/report artifacts. It includes safe `.env*.example` templates.

## Limits

- No public deployment was performed.
- No live OpenAI, ElevenLabs, NAV, ESCO, email or cloud-provider validation was performed.
- No legal/privacy approval is implied.
- No penetration test is implied.
- RC1 remains recoverable at commit `7215f9a92671e8050f99d38d39fc699634631e18`.

Future Work includes production TLS/DNS, live provider acceptance, real email delivery, empirical participant research, legal/privacy review, professional accessibility audit, penetration testing, enterprise monitoring and commercial job-board integrations.
