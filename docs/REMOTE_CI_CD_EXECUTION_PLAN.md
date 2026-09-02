# Remote CI/CD Execution Plan

Technical draft - requires remote repository setup before execution.

## Pull Request

- Source safety.
- Backend tests.
- PostgreSQL tests.
- Frontend tests.
- Typecheck.
- Build.
- E2E.
- Security audits.
- Container builds.
- SBOM.

## Main Branch

- Repeat quality gates.
- Build immutable images.
- Image scan.
- Publish images after registry approval.
- Generate provenance.
- Create deployment candidate.

## Staging Deployment

- Approval or protected environment.
- Acquire cloud identity through OIDC.
- Run migration job.
- Deploy backend, worker and frontend.
- Wait for readiness.
- Run smoke tests.
- Run release-candidate E2E.
- Verify observability.
- Verify backup.
- Record release evidence.

No automatic production deployment is created by Task 13B.0.
