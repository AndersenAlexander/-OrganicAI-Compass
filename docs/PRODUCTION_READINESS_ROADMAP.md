# Production Readiness Roadmap

Task 10 establishes Release Gate 1. Task 11 adds the PostgreSQL/Alembic persistence foundation. Task 11.4 completed final local PostgreSQL activation for Release Gate 2. Task 12A adds the Release Gate 3.1 authentication foundation with rotating sessions, short-lived access tokens, account-token hashing, and source packaging safeguards. The project is still not production-ready until the remaining release gates complete.

Next release-gate tasks:

- Task 11 - PostgreSQL, Alembic, backup and restore: passed through final PostgreSQL activation; original legacy SQLite preserved as immutable evidence
- Task 12A - Secure authentication and rotating sessions: implemented locally; production email, HTTPS cookie security, and operational rotation remain required
- Task 12B - Privacy and data lifecycle
- Task 13 - Production RAG and AI evaluation
- Task 14 - Observability, audit and cost management
- Task 15 - Full QA, accessibility and performance
- Task 16 - Docker, CI/CD, staging and deployment
- Task 17 - Thesis empirical evaluation
- Task 18 - Final release audit

Important remaining work:

- replace in-memory rate limiting and latest-turn metadata with shared storage;
- add role-based admin permissions;
- configure production email verification/password recovery delivery;
- enforce HTTPS-only cookies in staging and production;
- complete retention, export, and deletion workflows;
- complete CSP hardening beyond report-only mode;
- configure real public HTTPS staging;
- run real ElevenLabs WebRTC validation;
- define retention, deletion, and export policies;
- add cost and provider observability.
## Task 11.1 Release Gate Status

Task 11.1 offline tooling is superseded by Task 11.2 execution.

PostgreSQL infrastructure validation passed on disposable Docker Desktop PostgreSQL. Real Alembic, fixture migration, backup, restore, readiness, PostgreSQL tests, and runtime smoke all passed.

Legacy remediation simulation passed in Task 11.3. Task 11.4 activated PostgreSQL through the verified clean fallback while preserving the original SQLite database unchanged.

## Task 12A Release Gate Status

Task 12A implemented Argon2id password hashing with bcrypt upgrade compatibility, server-side auth sessions, rotating refresh-token families, single-use hashed account tokens, frontend in-memory bearer tokens, auth failure cleanup, session controls, and route authorization audit reporting. Task 15D verified the current source-code Alembic head as `0004_provider_operations`; `0002_auth_sessions_security` remains a historical Task 12A revision, not the current head.
# Task 12B Privacy Readiness

Technical draft - requires legal review before public deployment.

Technical draft — requires legal and operational review before public deployment.

Task 12C introduces a software release-readiness gate, but public-production readiness remains blocked until provider settings, email DNS, secret rotation, legal review, subprocessors, transfers, staging deployment, monitoring, and incident response are complete.

Before public deployment, complete legal review for privacy notice wording, DPA/subprocessor register, provider retention claims, DPIA screening, data subject rights SLAs, deletion across backups, and research consent text. The current Privacy Center is a technical control surface, not a final legal privacy policy.

## Task 13A Local Staging Status

Task 13A is complete for local staging after Task 13A.3. Containers, PostgreSQL persistence, local CI, observability, metrics, trace export, Grafana dashboards, graceful backend shutdown, graceful worker shutdown and synthetic PostgreSQL contention validation passed locally with zero blocking failures.

This does not approve Task 13B, cloud staging or public production. Remaining production work includes Git/remote CI execution, cloud staging provider selection, OIDC/cloud identity setup, secret rotation confirmation, legal/provider attestations, public HTTPS deployment, production monitoring operations, amd64 runtime execution, automated axe scan and full production-grade SBOM inventory.

## Task 13B.0 Remote Repository and Cloud Readiness

Task 13B.0 is complete as a readiness-preparation task. It adds repository content policy, `.gitignore` hardening, repository safety audit tooling, GitHub repository policies, pull-request template, secret-rotation checklist, cloud staging requirements, provider-neutral deployment package and cloud readiness audit evidence.

Task 13B.0.2 added PostgreSQL behavioral-test isolation and connection-lifecycle tooling. Task 13B.0.3 initially found Docker Desktop and PostgreSQL runtime recovery blockers without deleting volumes. Task 13B.0.3-R1 and follow-up remediation closed the local PostgreSQL validation gap: SQLAlchemy URL password masking was fixed, PowerShell native stderr handling was fixed, PostgreSQL preparation passed at Alembic head `0004_provider_operations`, the PostgreSQL marker suite passed with `5 passed`, and the backend regression passed with PostgreSQL tests executed separately. Task 13B.0.4 reduced backend UTC deprecation warnings from `34869` to `55`, with the remaining warnings isolated to `python-jose`.

Cloud deployment remains blocked. Task 13B.1 may start only after Git is available, a private remote repository is connected, a reviewed safe initial commit is created, GitHub Actions pass remotely, critical exposed credentials are rotated and verified, and the user approves cloud provider, region, budget and deployment architecture.

## Task 13B.0.5 Release Candidate Status

Task 13B.0.5 produced a validated local release candidate. Backend compile, targeted backend tests, the full non-PostgreSQL backend suite, PostgreSQL preparation, PostgreSQL marker tests, frontend typecheck, frontend unit tests, frontend build, full Playwright E2E, local staging smoke, observability smoke, security/privacy audits, and source archive safety checks passed with no local release-candidate blocking findings.

Final local validation totals: backend `160 passed, 5 deselected, 55 warnings`; PostgreSQL marker suite `5 passed, 0 failed, 0 skipped`; frontend unit tests `29 passed`; Playwright E2E `140 passed, 1 skipped, 0 failed`. The skipped E2E is real external provider validation and must not be treated as executed.

Current classification: demonstration ready, local release-candidate ready, and local staging validated. Production deployment ready and production operationally ready remain blocked by external manual actions: credential rotation, production secret management, production email delivery, public DNS/TLS, private remote repository and remote CI, cloud deployment approval, real provider acceptance testing, and legal/privacy operational review.

## Task 13C.0.1 Production Readiness Gap Closure

Task 13C.0.1 closes the production-readiness gaps that can be addressed safely without a public deployment. It adds production environment templates, strict production environment validation, secret rotation status reporting, bounded SMTP delivery behavior, provider-neutral real-provider acceptance harnesses disabled by default, hardened remote CI definitions, DNS/TLS, database operations, monitoring/incident and legal/privacy runbooks, and a deterministic production go/no-go checker.

This task does not rotate real credentials, configure public DNS/TLS, send production email, run live provider tests, deploy to a public environment or grant legal/privacy approval. Production deployment ready and production operationally ready remain blocked until those external/manual evidence items are completed and the go/no-go checker returns a passing production classification.

## Task 13C.0.2 Local Production Rehearsal

Task 13C.0.2 is complete locally. It adds an isolated Docker Compose rehearsal stack with `APP_ENV=production`, PostgreSQL on a separate volume/database/port, production build images, reverse proxy, one-shot worker, OTel, Prometheus and Grafana. The rehearsal validated fresh Alembic migration to `0004_provider_operations`, readiness with PostgreSQL reachable and migration current, schema drift `0`, reverse-proxy smoke, synthetic acceptance with real providers disabled, PostgreSQL backup, restore into `organicai_prod_rehearsal_restore`, backend rollback, recovery drills, observability and safe teardown preserving volume/backups/logs.

Current classification after Task 13C.0.2: local release candidate ready, local staging validated and local production rehearsal validated. Production deployment ready and production operationally ready remain blocked by external/manual actions: remote CI, public DNS/TLS, production email/provider acceptance, production backup/storage confirmation, monitoring ownership and legal/privacy approval.

## Task 15D Repository and Release Reconciliation

Task 15D selects local dissertation release-candidate version `0.9.0-rc.1` for the reconciled snapshot after Tasks 15A, 15B and 15C. It does not approve public production deployment and does not replace Task 15E final regression.

Verified Task 15D source facts:

- Git metadata was recovered from a nearby same-lineage local repository at head `ff09a6c01c7a3f9a7e7b5488410fd23327f1aee2`.
- Current source-code Alembic head is `0004_provider_operations`.
- Task 15A route authorization blocking findings remain `0` when freshly audited.
- Task 15B architecture remains `career-scoring-v2-four-layer` and `human-discovery-career-hypothesis v2`.
- Task 15C profile/demo/extension documentation confirms normal users require owned profiles and browser-extension capture is token/profile/owner scoped.
