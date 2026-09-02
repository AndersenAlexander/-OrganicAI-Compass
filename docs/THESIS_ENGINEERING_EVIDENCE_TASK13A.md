# Thesis Engineering Evidence Task 13A

Technical draft — requires legal and operational review before public deployment.

The evidence package in `evidence/task13a/` supports reproducibility through Dockerfiles, Compose, scripts and runbooks; reliability through health/readiness checks and failure drills; maintainability through CI definitions and documentation; security through secret exclusion, non-root containers and staging fail-closed validation; observability through JSON logs, metrics and optional OpenTelemetry; privacy by design through provider-off defaults and sanitized telemetry; and operational resilience through backup/restore and recovery procedures.

This evidence does not claim cloud staging or public production deployment.

Task 13A.3 adds final local evidence for observability and graceful shutdown: real local Collector/Prometheus/Grafana runtime, provisioned dashboards, sanitized trace export, collector outage recovery, public observability isolation, backend SIGTERM cleanup, worker SIGTERM lease handling, PostgreSQL multi-worker contention and a corrected local CI run with zero blocking failures.
