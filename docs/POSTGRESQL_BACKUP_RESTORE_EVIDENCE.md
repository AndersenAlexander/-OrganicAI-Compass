# PostgreSQL Backup And Restore Evidence

Date: 2026-07-27

## Scope

This evidence covers disposable PostgreSQL backup and restore validation for Task 11.2.

The validation used Docker Compose mode and did not expose passwords, full database URLs, or row contents.

## Source Database

- Source database name: `organicai_task11_migration`
- Schema revision: `0001_initial_schema`
- Integrity before backup: passed
- Schema drift before backup: `0`

## Backup

Command mode:

```text
PG_TOOLS_MODE=docker-compose
PG_DOCKER_COMPOSE_FILE=../docker-compose.persistence.yml
PG_DOCKER_SERVICE=organicai-postgres
PG_DOCKER_ENV_FILE=../.env.postgres-test
```

Result:

- Status: `success`
- Backup file: `organicai-postgres-20260727-125250.dump`
- Manifest file: `organicai-postgres-20260727-125250.manifest.json`
- Backup format: `custom`
- Size: `634693` bytes
- SHA-256 prefix: `eaa68322b2d7`
- Tools mode: `docker-compose`
- Schema version: `0001_initial_schema`

Independent verification:

- Manifest hash matched the archive hash
- `pg_restore --list` passed inside the container
- Archive included table data entries for application tables and `alembic_version`
- Manifest included `165` table-count entries

## Restore

Restore target:

- Target database name: `organicai_task11_restore`
- Target verified empty before apply: yes

Restore validation:

- Dry-run: passed
- Apply: passed
- Post-restore `db_status`: passed
- Post-restore `verify_database`: passed
- Post-restore schema drift: `0`

Comparison report:

```text
reports/database-restores/postgres-restore-20260727-125537.json
```

Report result:

- Match: `true`
- Table count: `165`
- Row counts match: `true`
- Primary-key counts match: `true`
- Schema revision match: `true`
- Foreign-key integrity: passed
- Row content included: `false`

## Gate Decision

PostgreSQL backup and restore passed for the disposable Task 11.2 environment.
