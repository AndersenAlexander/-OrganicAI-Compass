# Production Database Operations

Status: runbook and local tooling prepared; real production backup/restore remains external/manual.

Existing safe tools:

- `python -m app.scripts.backup_database --source postgres`
- `python -m app.scripts.restore_database --backup <path> --dry-run`
- `python -m app.scripts.verify_database`
- `python -m app.scripts.prepare_postgres_test_database`
- `python -m app.scripts.db_migrate upgrade --allow-production`

Production requirements:

- PostgreSQL only;
- SSL/TLS connection with `sslmode=require`, `verify-ca` or `verify-full`;
- encrypted backup storage;
- restore into disposable database before migration;
- migration preflight with Alembic head and schema drift;
- connection pool sizing reviewed against platform limits;
- credential rotation plan;
- retention policy;
- orphan detection and integrity verification;
- downgrade limitations documented before migration.

Migration sequence:

1. Capture backup manifest.
2. Restore backup into disposable target.
3. Run integrity, migration and schema drift checks.
4. Confirm rollback criteria.
5. Execute production migration in approved window.
6. Verify readiness, schema current, connection lifecycle and application smoke.

Never restore over the active production database without explicit approval and verified backup evidence.
