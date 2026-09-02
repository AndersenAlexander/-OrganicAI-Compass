# PostgreSQL Connection Lifecycle

Technical draft - local validation only.

PostgreSQL marker tests use bounded test connections and diagnostics from `backend/tests/conftest.py`.

Timeout policy:

- PostgreSQL statement timeout: `30000 ms`
- PostgreSQL lock timeout: `5000 ms`
- PostgreSQL idle-in-transaction timeout: `30000 ms`
- Pytest PostgreSQL marker timeout: `60 seconds`

The timeout values are test-oriented. `DB_LOCK_TIMEOUT_MS` and `DB_IDLE_IN_TRANSACTION_SESSION_TIMEOUT_MS` default to `0` in normal runtime configuration and are enabled explicitly for PostgreSQL test validation.

Lifecycle controls:

- Engines are created after the isolated test URL is configured.
- Test engines use `pool_pre_ping`, bounded `pool_timeout`, and rollback-on-return.
- Sessions are opened with context managers or explicit `close()`.
- Failed commits roll back explicitly.
- Worker/concurrency tests clean synthetic operational-job rows before leak assertions.
- Test fixtures dispose engines after use.
- Diagnostics check test-owned PostgreSQL activity, advisory locks and unfinished synthetic jobs.

Isolation strategies:

- Repository and persistence behavior tests use database cleanup isolation, because Alembic validation and integrity checks need committed schema state.
- SKIP LOCKED and worker-style tests use database cleanup isolation, not an outer rollback transaction, because independent sessions must see committed queued jobs.
- SQLite-only tests remain isolated through temporary files or in-memory engines.

The explicit lifecycle test `test_postgres_app_lifespan_closes_database_resources` imports `app.main` in a subprocess after setting `DATABASE_URL`, runs a lifespan-aware `TestClient`, and asserts startup/shutdown/database disposal events occur once.

Task 13B.0.3 status:

- Runtime validation is still blocked by Docker Desktop startup failure.
- The dedicated test database remains `organicai_task13b03_test`.
- Docker Desktop remained in `starting` after controlled restart/start attempts, so PostgreSQL protocol connectivity could not be restored.
- Task 13B.0.3-R1 after manual Windows restart did not change this status; Docker Desktop still could not start and the test container was not launched.
- Connection, transaction, advisory-lock and worker leak assertions are implemented but not proven against PostgreSQL in this workspace.
