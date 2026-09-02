# Database Integrity

Integrity CLI:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.verify_database
```

Status CLI:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.db_status
```

Checks include:

- connection;
- Alembic revision/head;
- required tables;
- SQLite `PRAGMA integrity_check`;
- SQLite `PRAGMA foreign_key_check`;
- application foreign key orphan scan from reflected metadata;
- sanitized result output.

Exit codes:

- `0`: healthy;
- `1`: configuration error;
- `2`: unreachable;
- `3`: migration mismatch;
- `4`: integrity failure.

The current legacy SQLite database has valid SQLite file integrity but has missing Alembic revision and foreign key orphan rows. After Task 11.4, keep it as immutable evidence only; do not stamp it, clean it, or use it as runtime persistence.
## Legacy Orphan Analysis

Task 11.1 added a read-only orphan analyzer:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.analyze_legacy_orphans `
  --database ./organicai.db `
  --output ..\reports\database-integrity\legacy-orphans.json
```

The current sanitized report identifies 156 orphan violations concentrated in `messages` -> `conversations`. Raw IDs, emails, message text, transcripts, profile content, RAG content, passwords, and tokens are not included.

The remediation plan is generated at:

```text
reports/database-integrity/legacy-orphan-remediation-plan.json
```

Do not modify the legacy SQLite database until that plan is reviewed and explicitly approved.

## Task 11.2 PostgreSQL Integrity Evidence

Disposable PostgreSQL integrity passed after Alembic upgrade, downgrade/re-upgrade, fixture migration, restore, and runtime smoke.

Evidence:

- PostgreSQL schema inventory: `reports/database-integrity/postgres-schema-inventory-task11-2.json`
- Downgrade/re-upgrade inventory: `reports/database-integrity/postgres-downgrade-reupgrade-inventory-task11-2.json`
- Table count: `165`
- Schema revision: `0001_initial_schema`
- Schema drift: `0`
- Legacy SQLite safety report: `reports/database-integrity/legacy-sqlite-task11-2-safety.json`

`backend/organicai.db` remained unchanged during Task 11.2.

## Task 11.3 Legacy Integrity Evidence

Task 11.3 captured before/after immutability evidence for `backend/organicai.db`.

Reports:

- `reports/database-integrity/original-sqlite-before-task11-3.json`
- `reports/database-integrity/original-sqlite-after-task11-3.json`
- `reports/database-integrity/original-sqlite-immutability-proof.json`

Expected proof fields:

- `changedDuringTask`: `false`
- `sha256Matches`: `true`
- `sizeMatches`: `true`
- `pageCountMatches`: `true`
- `tableCountMatches`: `true`
- `applicationRowCountsMatch`: `true`
- `foreignKeyViolationCountMatches`: `true`

The remediated clone verified with:

- SQLite integrity: `ok`
- Foreign-key violations: `0`
- Active orphan messages: `0`
- Reconciliation lost rows: `0`
- Reconciliation duplicate rows: `0`

## Task 11.4 Final Integrity Evidence

Task 11.4 finalization verified:

- Original SQLite changed during Task 11.4: no
- Clean SQLite fallback FK violations: `0`
- Clean SQLite fallback Alembic revision: `0001_initial_schema`
- Final PostgreSQL schema drift: `0`
- Final PostgreSQL migration row counts match: yes
- Archived orphan rows: `156`
- Lost active rows: `0`
- Lost archived rows: `0`
- Legacy artifact HTTP access: blocked

Primary evidence:

- `reports/database-integrity/original-sqlite-post-activation-proof.json`
- `reports/database-integrity/final-data-reconciliation.json`
- `reports/database-integrity/rollback-rehearsal-task11-4.json`
- `reports/database-integrity/legacy-artifact-accessibility-proof.json`
