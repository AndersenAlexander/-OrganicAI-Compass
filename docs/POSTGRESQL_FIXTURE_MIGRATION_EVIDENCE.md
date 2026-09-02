# PostgreSQL Fixture Migration Evidence

Date: 2026-07-27

## Scope

This evidence covers synthetic SQLite-to-PostgreSQL migration validation for Task 11.2.

The synthetic source fixture was disposable and intentionally small. It was generated through Alembic and did not use `backend/organicai.db`.

## Source Fixture

- Fixture: `backend/tmp/task11-fixtures/organicai-fixture.db`
- Source dialect: SQLite
- SQLite integrity: passed
- Foreign-key issue count: `0`
- Source opened read-only during migration: `true`

Representative application coverage included users, diagnostics, profiles, conversations, messages, recommendations, recommendation events, recommendation feedback, roadmaps, RAG runs, RAG sources, and RAG feedback.

No row content is included in this document.

## Dry Run

Report:

```text
reports/database-migrations/sqlite-to-postgres-20260727-124630.json
```

Result:

- Status: `dry_run`
- Target dialect: PostgreSQL
- Row counts match: `true`
- Foreign keys valid: `true`
- Orphan count: `0`
- Inserted rows: `0`

## Apply

Report:

```text
reports/database-migrations/sqlite-to-postgres-20260727-124700.json
```

Result:

- Status: `success`
- Target dialect: PostgreSQL
- Row counts match: `true`
- Foreign keys valid: `true`
- Orphan count: `0`
- Failed rows: `0`
- Skipped rows: `0`

Post-apply targeted checks passed for:

- primary-key preservation;
- relationship preservation for conversations, messages, recommendations, roadmaps, and RAG records;
- JSON boolean and JSON null semantics;
- SQL nullable columns;
- timestamp equivalence;
- representative Unicode values.

## Negative Checks

Non-empty destination rejection:

- Apply to a non-empty target was rejected
- Existing target application row count stayed unchanged
- No row content or credentials were printed

Strict rollback check:

- Invalid fixture copy: `backend/tmp/task11-fixtures/organicai-fixture-invalid-json.db`
- Failure category: `invalid_json`
- Failed table: `diagnostics`
- Transaction rolled back: `true`
- Target application rows after failure: `0`
- Failure report: `reports/database-migrations/sqlite-to-postgres-20260727-125115.json`

## Gate Decision

Synthetic SQLite-to-PostgreSQL migration passed for Task 11.2. Production migration from `backend/organicai.db` remained blocked at that time. Task 11.4 superseded the blocker by migrating the verified clean fallback instead of the original legacy file.
