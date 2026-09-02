# Task 13C.0.2 Local Production Rehearsal

Status: completed locally on 2026-08-03.

This task adds a production-like local deployment rehearsal that is isolated from development, test and staging resources. It validates fresh PostgreSQL migration, readiness, reverse-proxy smoke, synthetic acceptance, backup, restore into a disposable database, application rollback, recovery drills, security checks, observability checks and safe teardown.

## Result

- `local_release_candidate_ready`: PASSED, using existing Task 13B.0.5 evidence.
- `local_staging_validated`: PASSED, using existing local staging evidence.
- `local_production_rehearsal_validated`: PASSED, using `evidence/task13c02/final-summary.json`.
- `production_deployment_ready`: BLOCKED.
- `production_operationally_ready`: BLOCKED.

Production remains blocked by external/manual work: remote CI execution, public DNS, public TLS, real production email acceptance, OpenAI acceptance, ElevenLabs acceptance, production backup provider/storage confirmation, monitoring ownership and legal/privacy approval.

## Implemented Artifacts

- `docker-compose.production-rehearsal.yml`
- `.env.production-rehearsal.example`
- `deploy/nginx/production-rehearsal.conf`
- `scripts/production-rehearsal-start.ps1`
- `scripts/production-rehearsal-status.ps1`
- `scripts/production-rehearsal-smoke.ps1`
- `scripts/production-rehearsal-backup.ps1`
- `scripts/production-rehearsal-restore.ps1`
- `scripts/production-rehearsal-rollback.ps1`
- `scripts/production-rehearsal-recovery-drills.ps1`
- `scripts/production-rehearsal-stop.ps1`

## Isolation

- Compose project: `organicai-prod-rehearsal`
- Network: `organicai_prod_rehearsal_network`
- PostgreSQL volume: `organicai_prod_rehearsal_postgres_data`
- Active database: `organicai_prod_rehearsal`
- Restore database: `organicai_prod_rehearsal_restore`
- Proxy: `http://127.0.0.1:28080`
- PostgreSQL host port: `127.0.0.1:55532`
- OTel HTTP: `127.0.0.1:14318`
- Prometheus: `127.0.0.1:29090`
- Grafana: `127.0.0.1:23000`

The runtime env file is generated at `.tmp/production-rehearsal.env` with synthetic secrets. It is not committed.

## Evidence

Primary evidence is in `evidence/task13c02/`:

- `final-summary.json`: overall task result.
- `production-go-no-go-current.json` and `.txt`: updated go/no-go report.
- `production-environment-validation-current.json`: production runtime validation.
- `migration-current.json` and `.txt`: migration to Alembic head.
- `schema-drift-current.json`: drift count `0`.
- `readiness-current.json`: PostgreSQL reachable and migration current.
- `smoke-current.json`: reverse-proxy smoke and synthetic acceptance.
- `backup-current.json`: sanitized backup manifest.
- `restore-current.json`: disposable restore validation.
- `application-rollback-current.json`: rollback restart validation.
- `failure-recovery-current.json`: recovery drills.
- `observability-current.json`: Prometheus and Grafana checks.
- `security-current.json` and `secret-disclosure-scan-current.json`: provider/email disabled and no secret disclosures.
- `safe-teardown-current.json`: services stopped, volume and backups retained.

No real provider calls or real email sends were performed.
