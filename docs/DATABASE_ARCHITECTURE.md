# Database Architecture

OrganicAI Compass uses synchronous SQLAlchemy.

Decision:

- SQLAlchemy mode: synchronous `create_engine`, `Session`, `sessionmaker`.
- Development driver: SQLite remains supported for focused unit tests and rollback rehearsal.
- Active runtime driver after Task 11.4: PostgreSQL.
- Production driver: PostgreSQL is required when `DATABASE_REQUIRE_POSTGRES_IN_PRODUCTION=true`.
- PostgreSQL driver: `psycopg2-binary` is retained because it is already installed and stable in the current project environment.
- Schema source of truth: Alembic migrations.
- Startup schema creation: `Base.metadata.create_all()` is no longer the normal runtime schema mechanism.

Runtime database modules:

- `backend/app/db/base.py`: shared `Base` and naming convention.
- `backend/app/db/engine.py`: SQLite/PostgreSQL engine creation.
- `backend/app/db/session.py`: session factory and request dependency.
- `backend/app/db/health.py`: connection check.
- `backend/app/db/migration_status.py`: Alembic current/head status.

`get_db()` opens one session per dependency use, rolls back on exceptions, and always closes the session. It does not commit implicitly.

`DB_AUTO_CREATE_SCHEMA=false` and `DB_AUTO_MIGRATE=false` are the defaults. Production startup must not run destructive or uncontrolled migrations.

## Task 11.4 Runtime Baseline

Task 11.4 activated PostgreSQL database `organicai_app` as the runtime persistence store.

- Original SQLite `backend/organicai.db`: immutable evidence only
- Clean SQLite fallback `backend/data/organicai-clean.db`: rollback-only fallback
- Active PostgreSQL schema revision: `0001_initial_schema`
- Active runtime flags: `DB_AUTO_CREATE_SCHEMA=false`, `DB_AUTO_MIGRATE=false`, `DB_REQUIRE_MIGRATION_HEAD=true`
- Settings diagnostics include release-gate booleans for pre-activation backup, rollback fallback, original preservation, orphan archive verification, and legacy data loss.

See `docs/POSTGRESQL_OPERATIONAL_BASELINE.md`.
