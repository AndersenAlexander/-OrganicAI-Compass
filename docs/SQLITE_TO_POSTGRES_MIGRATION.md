# SQLite to PostgreSQL Migration

Do not run `--apply` against the original legacy SQLite database. After Task 11.4, final PostgreSQL activation is based on the verified clean fallback at `backend/data/organicai-clean.db`.

## Phase A - Preparation

1. Stop writes to the SQLite application.
2. Verify SQLite:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.verify_database
```

3. Create a SQLite backup:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.backup_database --source sqlite
```

4. Generate inventory:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.db_inventory --output ..\reports\database-migrations\legacy-sqlite-inventory.json
```

5. Start PostgreSQL.
6. Run Alembic upgrade against PostgreSQL.
7. Verify the destination is empty except `alembic_version`.

## Phase B - Dry Run

```powershell
.\.venv\Scripts\python.exe -m app.scripts.migrate_sqlite_to_postgres --source .\organicai.db --target-url-env DATABASE_URL --dry-run
```

## Phase C - Apply

```powershell
.\.venv\Scripts\python.exe -m app.scripts.migrate_sqlite_to_postgres --source .\organicai.db --target-url-env DATABASE_URL --apply
```

## Phase D - Verify

```powershell
.\.venv\Scripts\python.exe -m app.scripts.verify_database
.\.venv\Scripts\python.exe -m app.scripts.db_status
```

## Phase E - Switch

1. Update `DATABASE_URL`.
2. Restart backend on `127.0.0.1:8020`.
3. Verify readiness.
4. Verify login.
5. Verify profile.
6. Verify chat history.
7. Verify recommendations.
8. Verify roadmap.
9. Verify RAG metadata.
10. Verify live voice metadata.

## Phase F - Rollback

1. Restore the previous `DATABASE_URL`.
2. Restart backend.
3. Retain the PostgreSQL migration report.
4. Do not delete either database.
## Task 11.1 Safety Updates

The SQLite source is opened read-only for migration planning. In strict mode, source foreign-key orphan rows block migration before the PostgreSQL target is contacted.

The CLI accepts both argument names:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.migrate_sqlite_to_postgres `
  --source ./organicai.db `
  --target-url-env TEST_MIGRATION_DATABASE_URL `
  --dry-run
```

`--target-env` remains supported for backward compatibility.

Never run `--apply` against `backend/organicai.db` until the legacy orphan remediation plan has been reviewed and approved.

## Task 11.2 Fixture Evidence

Synthetic fixture migration passed against disposable PostgreSQL.

Evidence:

- Dry-run report: `reports/database-migrations/sqlite-to-postgres-20260727-124630.json`
- Apply report: `reports/database-migrations/sqlite-to-postgres-20260727-124700.json`
- Apply status: `success`
- Source opened read-only: `true`
- Row counts match: `true`
- Foreign keys valid: `true`
- Orphan count: `0`
- Representative ID, timestamp, JSON, nullable-value, and Unicode checks: passed

Negative checks:

- Non-empty destination apply was rejected without changing existing target rows.
- Invalid JSON fixture copy failed with sanitized category `invalid_json`.
- Strict transaction rollback left `0` target application rows after failure.
- Failure report: `reports/database-migrations/sqlite-to-postgres-20260727-125115.json`

See `docs/POSTGRESQL_FIXTURE_MIGRATION_EVIDENCE.md`.

## Legacy Production Block Superseded By Task 11.4

The real legacy SQLite source must still not be applied directly to PostgreSQL. Its read-only dry-run was blocked by existing source foreign-key orphan rows. Task 11.4 superseded the block by promoting the verified clean fallback instead.

## Task 11.3 Clean Clone Evidence

Task 11.3 created a clean SQLite remediation clone and migrated that clone into a disposable PostgreSQL database.

Source:

```text
backend/tmp/legacy-remediation/organicai-remediation-clone.db
```

Target:

```text
organicai_task11_clean_legacy
```

Result:

- Clean clone FK violations: `0`
- Clean clone revision: `0001_initial_schema`
- Dry run: passed
- Apply: passed
- Inserted rows: `4607`
- Skipped rows: `0`
- Failed rows: `0`
- Row counts match: yes
- IDs, JSON, timestamps, and Unicode preserved: yes
- Schema drift: `0`

Evidence:

- `reports/database-integrity/clean-clone-inventory.json`
- `reports/database-migrations/clean-legacy-clone-to-postgres-<timestamp>.json`
- `docs/CLEAN_LEGACY_POSTGRESQL_MIGRATION_EVIDENCE.md`

The original SQLite database remains not approved for `--apply`.

## Task 11.4 Final Migration

Final migration source:

```text
backend/data/organicai-clean.db
```

Final target:

```text
organicai_app
```

Result:

- Dry run: passed
- Apply: passed
- Inserted rows before runtime smoke: `4607`
- Skipped rows: `0`
- Failed rows: `0`
- Row counts match: yes
- IDs, JSON, timestamps, Unicode, null values, and empty-string semantics preserved: yes
- Foreign keys valid: yes
- Schema drift: `0`
- Archived orphan rows inserted into active `messages`: `0`

Evidence:

- `reports/database-migrations/final-clean-sqlite-to-postgres-20260727-154723.json`
- `reports/database-migrations/final-clean-sqlite-to-postgres-20260727-154747.json`
- `docs/FINAL_DATA_RECONCILIATION.md`
