# Database Backup and Restore

## SQLite Backup

SQLite backup uses the SQLite backup API. It does not copy the database file directly.

```powershell
.\.venv\Scripts\python.exe -m app.scripts.backup_database --source sqlite
```

Output:

```text
backend/backups/database/
  organicai-sqlite-YYYYMMDD-HHMMSS.db
  organicai-sqlite-YYYYMMDD-HHMMSS.manifest.json
```

The manifest contains SHA-256, size, schema version, table counts, and verification status. It does not contain row values.

## PostgreSQL Backup

PostgreSQL backup uses `pg_dump --format=custom` and verifies the archive with `pg_restore --list`.

```powershell
.\.venv\Scripts\python.exe -m app.scripts.backup_database --source postgres
```

`pg_dump` and `pg_restore` must be available on `PATH`.

## PostgreSQL Restore

Restore is dry-run by default:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.restore_database --backup path.dump --target-url-env RESTORE_DATABASE_URL
```

Apply requires:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.restore_database --backup path.dump --target-url-env RESTORE_DATABASE_URL --apply
```

The restore command verifies the manifest checksum, verifies the archive, refuses the active database by default, and refuses a non-empty target unless explicitly allowed.

Backup retention:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.prune_database_backups --dry-run
.\.venv\Scripts\python.exe -m app.scripts.prune_database_backups --apply
```
## PostgreSQL Tool Modes

PostgreSQL backup and restore support two administrative tool modes:

```text
PG_TOOLS_MODE=local
PG_TOOLS_MODE=docker-compose
```

`local` requires `pg_dump` and `pg_restore` on PATH.

`docker-compose` runs `pg_dump` and `pg_restore` inside the `organicai-postgres` service, copies custom-format archives to the host with `docker compose cp`, verifies archives with `pg_restore --list`, and removes temporary container files.

Required Docker Compose environment:

```text
PG_DOCKER_COMPOSE_FILE=../docker-compose.persistence.yml
PG_DOCKER_SERVICE=organicai-postgres
PG_DOCKER_ENV_FILE=../.env.postgres-test
```

Manifests must not contain credentials or full database URLs.

## Task 11.2 PostgreSQL Evidence

Disposable PostgreSQL backup and restore passed with Docker Compose tool mode.

Evidence:

- Backup file: `organicai-postgres-20260727-125250.dump`
- Manifest file: `organicai-postgres-20260727-125250.manifest.json`
- Backup format: `custom`
- Size: `634693` bytes
- SHA-256 prefix: `eaa68322b2d7`
- Restore comparison: `reports/database-restores/postgres-restore-20260727-125537.json`
- Table count: `165`
- Row counts match: `true`
- Schema drift after restore: `0`
- Row content included: `false`

See `docs/POSTGRESQL_BACKUP_RESTORE_EVIDENCE.md`.

## Task 11.4 Final Activation Backups

Task 11.4 added final activation backup evidence:

- Original SQLite final backup: `organicai-original-final-20260727-154512.db`
- Pre-activation PostgreSQL backup: `organicai-app-pre-activation-20260727-154834.dump`
- Post-activation PostgreSQL backup: `organicai-app-post-activation-20260727-163338.dump`
- PostgreSQL backup format: custom
- PostgreSQL archive verification: `pg_restore --list`
- Manifest privacy: no credentials and no full database URLs

See `docs/POSTGRESQL_OPERATIONAL_BASELINE.md` and `docs/POSTGRESQL_ACTIVATION_ROLLBACK.md`.
