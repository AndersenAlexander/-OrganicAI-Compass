# PostgreSQL Operational Baseline

Date: 2026-07-27

Task 11.4 establishes PostgreSQL as the active local runtime baseline for Release Gate 2.

## Runtime

- Backend: `127.0.0.1:8020`
- Frontend: `127.0.0.1:5190`
- Active database engine: PostgreSQL
- Active application database: `organicai_app`
- Alembic revision: `0001_initial_schema`
- Startup schema creation: disabled
- Automatic runtime migrations: disabled
- Migration-head readiness check: enabled

Settings endpoint evidence:

- `/api/system/persistence`
- `/api/system/configuration`
- `/health/ready`

## Required Runtime Flags

```text
DATABASE_REQUIRE_POSTGRES_IN_PRODUCTION=true
DB_AUTO_CREATE_SCHEMA=false
DB_AUTO_MIGRATE=false
DB_REQUIRE_MIGRATION_HEAD=true
DB_BACKUP_DIRECTORY=./backups/database
```

Secrets and full database URLs belong only in ignored local environment files or deployment secret stores.

## Backup Baseline

Task 11.4 retained both pre-activation and post-activation PostgreSQL backups.

- Pre-activation backup: `organicai-app-pre-activation-20260727-154834.dump`
- Post-activation backup: `organicai-app-post-activation-20260727-163338.dump`
- Format: PostgreSQL custom archive
- Verification: `pg_restore --list`
- Manifest privacy: credentials and full database URLs omitted

## Data Baseline

- Canonical clean SQLite source rows: `4607`
- PostgreSQL rows after migration: `4607`
- PostgreSQL rows after synthetic runtime smoke: `4724`
- Archived orphan messages: `156`
- Unaccounted rows: `0`
- Schema drift: `0`

## Operational Rules

- Treat `backend/organicai.db` as immutable evidence only.
- Use `backend/data/organicai-clean.db` only for rollback rehearsal or emergency fallback.
- Use PostgreSQL for normal runtime after Task 11.4.
- Run Alembic explicitly before promoting new schema changes.
- Verify backups with `pg_restore --list` before accepting them.
- Do not include message content, raw identifiers, credentials, or full database URLs in reports.

## Final Validation Snapshot

- Backend pytest: `101 passed`
- PostgreSQL marker tests: `2 passed`
- Frontend typecheck, unit tests, and build: passed
- Selected E2E on `127.0.0.1:5190`: `21 passed`
- Security scan: no blocking findings
