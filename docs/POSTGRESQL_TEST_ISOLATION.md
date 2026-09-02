# PostgreSQL Test Isolation

Technical draft - local validation only.

Task 13B.0.3 uses a dedicated disposable PostgreSQL database for behavioral tests:

- Database name: `organicai_task13b03_test`
- Runtime environment variable: `TEST_POSTGRES_DATABASE_URL`
- Local source file: ignored `backend/.env.postgres-test`
- Public documentation: placeholders only, never full URLs or passwords

Protected database names are rejected before destructive operations:

- `organicai_app`
- `organicai_staging`
- `organicai_staging_restore_validation`
- `organicai_task11`
- `organicai_task11_migration`
- `organicai_task11_restore`
- `postgres`
- `template0`
- `template1`

Disposable database names must be valid PostgreSQL identifiers and contain one of:

- `_test`
- `test_`
- `_task`
- `_validation`

The guard is implemented in `backend/app/scripts/prepare_postgres_test_database.py`. It rejects malformed URLs, non-PostgreSQL URLs, missing database names, protected database names and ambiguous non-disposable names.

The preparation script may terminate sessions only for the isolated target database before drop/recreate. It must not terminate global PostgreSQL sessions and must not operate on staging, application or template databases.

Run locally:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\prepare-postgres-test-database.ps1 -DatabaseName organicai_task13b03_test
```

The current workspace could not complete this command because Docker Desktop failed to start after controlled recovery attempts. Task 13B.0.3-R1 repeated the validation after a manual Windows restart, but Docker Desktop still reported `starting` and Docker server commands failed with `Docker Desktop is unable to start`. No production-like database was modified and no Docker volume was removed.
