# Failure Recovery Runbook

Technical draft — requires legal and operational review before public deployment.

Database failure drill: confirm readiness, stop only `organicai-staging-postgres`, verify liveness remains available, verify readiness fails safely, restart PostgreSQL, wait for health, then verify readiness recovers.

Worker failure drill: stop only `organicai-staging-worker`, confirm core application remains available, restart worker, verify heartbeat recovery and no duplicate processing using synthetic jobs.

Backend failure drill: stop only `organicai-staging-backend`, verify proxy controlled failure behavior, keep frontend static content available, restart backend, verify readiness and auth/privacy state.

Observability outage drill: stop only `organicai-staging-otel`, verify backend readiness and request handling continue, verify telemetry export warnings are sanitized and bounded, restart the Collector, then verify new traces export again.

Graceful backend shutdown drill: run `scripts/validate-backend-sigterm.ps1`. The Task 13A.3 evidence expects SIGTERM receipt, new-work stop, active synthetic work completion, provider close hook, bounded telemetry flush, database pool disposal, successful restart and zero partial data.

Graceful worker shutdown drill: run `scripts/validate-worker-sigterm.ps1`. The Task 13A.3 evidence expects SIGTERM receipt, new-job stop, synthetic lease release or expiry, bounded telemetry flush, successful restart, single completion and zero duplicate result.
