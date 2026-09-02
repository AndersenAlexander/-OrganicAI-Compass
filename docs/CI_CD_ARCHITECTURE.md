# CI/CD Architecture

Technical draft — requires legal and operational review before public deployment.

Local CI is represented by `scripts/ci-local.ps1`. GitHub workflow definitions are prepared in `.github/workflows/ci.yml` and `.github/workflows/container-build.yml`.

Remote CI execution remains pending until Git is available in PATH, the repository is safely published, and GitHub Actions are executed by GitHub. The workflows do not run live provider tests and do not deploy to production.

Task 13A.3 local CI completed with zero blocking failures. The local pipeline includes backend tests, PostgreSQL marker tests, frontend typecheck/build/tests, existing and staging E2E tests, source safety checks, observability profile validation, Prometheus target validation, Grafana provisioning validation, trace export validation, telemetry privacy audit, backend SIGTERM drill, worker SIGTERM drill and worker contention drill.

Task 13B.0.2 hardens PostgreSQL marker execution through an isolated disposable database, protected-name guard, bounded pytest diagnostics and connection-leak checks. `scripts/run-postgres-marker-tests.ps1` now fails non-zero on prepare failure, pytest failure, skips, timeout or hung output. In the current workspace, PostgreSQL behavioral validation remains blocked because Docker/PostgreSQL is not reachable as a healthy PostgreSQL server.

The only failed local stage was the nonblocking prerequisites check because Git is not available on PATH. No remote GitHub Actions result is claimed from local evidence.

Task 13B.0 adds remote execution planning in `docs/REMOTE_CI_CD_EXECUTION_PLAN.md` and validates the workflow definitions with `scripts/audit-github-action-pins.ps1`. Static GitHub Actions readiness passed with zero blocking findings, but remote execution remains pending until Git and a remote repository are configured.
