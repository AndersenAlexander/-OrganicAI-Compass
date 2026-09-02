# Clean Legacy PostgreSQL Migration Evidence

Task 11.3 migrated the verified clean SQLite clone into a disposable PostgreSQL database.

## Source

```text
backend/tmp/legacy-remediation/organicai-remediation-clone.db
```

Source state:

- SQLite integrity: ok
- Foreign-key violations: 0
- Alembic revision: `0001_initial_schema`
- Archived orphan messages remain external to the active application schema.

## Target

```text
organicai_task11_clean_legacy
```

Target handling:

- Disposable PostgreSQL database was recreated.
- Alembic upgrade targeted exact revision `0001_initial_schema`.
- Strict SQLite-to-PostgreSQL dry run passed.
- Strict apply passed.

## Result

- Inserted rows: 4607
- Skipped rows: 0
- Failed rows: 0
- Source and target row counts: matched
- IDs preserved: yes
- Foreign-key integrity: passed
- JSON preserved: yes
- Timestamps preserved: yes
- Unicode preserved: yes
- Schema drift: 0
- Archived orphan messages inserted into active PostgreSQL tables: 0

Primary report:

```text
reports/database-migrations/clean-legacy-clone-to-postgres-<timestamp>.json
```

Runtime smoke report:

```text
reports/database-integrity/clean-postgres-runtime-smoke.json
```
