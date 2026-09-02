# Local PostgreSQL Setup

Task 11 adds an optional compose file. It does not start PostgreSQL automatically.

Set local credentials outside Git:

```powershell
$env:ORGANICAI_POSTGRES_USER="organicai"
$env:ORGANICAI_POSTGRES_PASSWORD="<local-password>"
$env:ORGANICAI_POSTGRES_DB="organicai"
$env:ORGANICAI_POSTGRES_PORT="5432"
```

Start PostgreSQL:

```powershell
docker compose -f docker-compose.persistence.yml up -d
```

Set `DATABASE_URL` in the backend environment from the local credentials. Do not print or commit the full database URL.

Run migrations:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

Run optional PostgreSQL tests:

```powershell
# Set TEST_POSTGRES_DATABASE_URL from local credentials without printing it.
.\.venv\Scripts\python.exe -m pytest -m postgres
```
## Task 11.2 Disposable Validation

Use `.env.postgres-test` at the repository root for local disposable validation. This file is ignored by Git and must not be committed or printed.

Expected database names:

- `organicai_task11`
- `organicai_task11_restore`
- `organicai_task11_migration`
- `organicai_task11_pytest`
- `organicai_task11_downgrade`
- `organicai_task11_failure`

The compose service is `organicai-postgres` and binds to localhost only:

```powershell
docker compose --env-file .env.postgres-test -f docker-compose.persistence.yml up -d organicai-postgres
```

Task 11.2 validated this path with Docker Desktop. The PostgreSQL container reached `healthy`, Alembic reached `0001_initial_schema`, schema drift was `0`, PostgreSQL marker tests passed, fixture migration passed, backup/restore passed, and runtime smoke passed.

For backend commands that run from `backend/`, construct database URLs from `.env.postgres-test` without printing the password. Use `OPENAI_API_KEY=disabled` for local smoke when provider calls must be avoided.

If Docker is unavailable, do not use an unknown PostgreSQL server. Start a known disposable PostgreSQL instance outside Codex, then rerun the validation commands.
