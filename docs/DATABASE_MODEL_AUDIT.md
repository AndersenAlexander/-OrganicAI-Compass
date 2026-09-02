# Database Model Audit

The Task 11 audit inspected the SQLAlchemy metadata used by all files in `backend/app/models/`.

Findings:

- Public IDs are string identifiers and are preserved. No UUID type conversion was applied.
- JSON columns use SQLAlchemy `JSON` for SQLite/PostgreSQL portability. JSONB was not introduced.
- Boolean columns are represented with SQLAlchemy `Boolean`; migration tooling converts legacy SQLite `0/1` values.
- Date/time columns remain SQLAlchemy `DateTime` with the current application convention of naive UTC-like values.
- Foreign keys are represented in metadata and are used for migration ordering.
- Naming convention was added for primary keys, foreign keys, indexes, unique constraints, and check constraints.
- Existing SQLite schema is compatible with the `0001_initial_schema` metadata shape.

Legacy data inventory:

- Database: `backend/organicai.db`
- Size: 8,384,512 bytes
- Tables: 164
- SQLite integrity: `ok`
- Alembic version table: missing
- Foreign key orphan rows: 156

Corrections applied:

- `Base.metadata` now has a stable naming convention.
- Runtime schema creation was moved behind `DB_AUTO_CREATE_SCHEMA`.
- Readiness now detects missing Alembic revision.
- Administrative reports do not include row values, passwords, transcripts, tokens, full conversations, or RAG content.

Remaining model risk:

- Many application services still call `datetime.utcnow()`. This is a known application-owned warning source and should be normalized in a narrower follow-up because it touches broad business logic.
