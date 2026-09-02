# PostgreSQL Activation Rollback

Date: 2026-07-27

This runbook describes the Task 11.4 rollback posture after final PostgreSQL activation.

## Active State

- Active database: PostgreSQL database `organicai_app`
- Backend validation port: `127.0.0.1:8020`
- Frontend validation port: `127.0.0.1:5190`
- Clean fallback: `backend/data/organicai-clean.db`
- Original legacy database: evidence only, never rollback target

## Rollback Target

Use only the clean fallback database:

```text
backend/data/organicai-clean.db
```

Do not point runtime traffic back to `backend/organicai.db`. The original legacy database intentionally remains unchanged and still contains historical orphan rows.

## Controlled Rollback Command

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.task11_4_finalize runtime-config --mode sqlite
```

Then restart the backend on `127.0.0.1:8020` and verify:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.task11_4_runtime_smoke --base-url http://127.0.0.1:8020 --wait --rollback-readonly
```

Expected:

- `/health/ready`: `200`
- persistence driver: SQLite
- migration state: current
- schema version: `0001_initial_schema`
- fallback manifest match: yes
- fallback hash unchanged during rehearsal: yes

## Return To PostgreSQL

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.task11_4_finalize runtime-config --mode postgresql
```

Restart the backend and verify:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.task11_4_runtime_smoke --base-url http://127.0.0.1:8020 --wait --verify-restart
```

Expected:

- `/health/ready`: `200`
- persistence driver: PostgreSQL
- migration state: current
- synthetic Task 11.4 data persisted after restart

## Evidence

- Rollback report: `reports/database-integrity/rollback-rehearsal-task11-4.json`
- Runtime configuration report: `reports/database-integrity/runtime-configuration-change-task11-4.json`
- Restart proof: `reports/database-integrity/final-postgres-restart-persistence.json`
- Clean fallback manifest: `backend/data/organicai-clean.manifest.json`

## Operator Notes

- Do not delete either PostgreSQL backups or SQLite evidence during rollback.
- Keep `DB_AUTO_CREATE_SCHEMA=false`, `DB_AUTO_MIGRATE=false`, and `DB_REQUIRE_MIGRATION_HEAD=true`.
- Disable demo seeding during rollback proof when checking fallback immutability.

