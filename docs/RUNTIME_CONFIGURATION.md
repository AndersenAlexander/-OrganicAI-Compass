# Runtime Configuration

Technical draft — requires legal and operational review before public deployment.

OrganicAI Compass now separates development, test, and production runtime configuration through `APP_ENV`.

Accepted values:

- `development`
- `test`
- `production`
- `staging`

Development can start without external provider keys. Unconfigured providers are marked disabled. Test mode must not call paid providers. Production startup can refuse unsafe configuration through the runtime configuration report.

Task 12A adds server-managed authentication sessions. Browser code stores the access token only in memory, refreshes through an HttpOnly cookie, and clears local auth state when refresh fails.

Task 12C adds `PRODUCTION_RELEASE_GATE_ENABLED`, live provider validation flags, OpenAI data-control attestation flags, ElevenLabs disposable deletion and apply flags, secret rotation attestation flags, data export/deletion-ledger keys, and SMTP email configuration.

## Core Variables

```env
APP_ENV=development
APP_NAME=OrganicAI Compass
APP_VERSION=0.9.0-rc.2
PUBLIC_BACKEND_URL=
FRONTEND_PUBLIC_URL=http://127.0.0.1:5190
ALLOWED_ORIGINS=http://127.0.0.1:5190,http://localhost:5190
ALLOWED_HOSTS=127.0.0.1,localhost
TRUST_PROXY_HEADERS=false
INTEGRATION_DIAGNOSTICS_ENABLED=true
REAL_PROVIDER_TESTS_ENABLED=false
```

## ElevenLabs Residency

Standard ElevenLabs is the default:

```env
ELEVENLABS_API_BASE_URL=https://api.elevenlabs.io
ELEVENLABS_RESIDENCY_MODE=standard
```

Accepted residency modes:

- `standard`
- `isolated-eu`
- `isolated-in`
- `isolated-sg`

For isolated modes, `ELEVENLABS_API_BASE_URL` must be configured explicitly. OrganicAI does not infer an isolated URL from `ELEVENLABS_SERVER_LOCATION`. The old `ELEVENLABS_SERVER_LOCATION` variable is deprecated and should not be used to claim data residency.

## Runtime Report

`GET /api/system/configuration` returns a sanitized report when diagnostics are enabled. It never returns API keys, JWT secrets, full Agent IDs, database credentials, Custom LLM secrets, or key fragments.

Production access must be protected with `X-Diagnostics-Token` and `DIAGNOSTIC_ACCESS_TOKEN`.

## Health

Available endpoints:

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `GET /api/health`

`/health/live` only confirms the process is alive. `/health/ready` checks required configuration, local database access, and Alembic head status when `DB_REQUIRE_MIGRATION_HEAD=true`. It does not call OpenAI or ElevenLabs.

## Database Variables

```env
DATABASE_URL=sqlite:///./organicai.db
DATABASE_REQUIRE_POSTGRES_IN_PRODUCTION=true
DB_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT_SECONDS=30
DB_POOL_RECYCLE_SECONDS=1800
DB_POOL_PRE_PING=true
DB_CONNECT_TIMEOUT_SECONDS=10
DB_STATEMENT_TIMEOUT_MS=30000
DB_APPLICATION_NAME=organicai-compass
DB_AUTO_CREATE_SCHEMA=false
DB_AUTO_MIGRATE=false
DB_REQUIRE_MIGRATION_HEAD=true
DB_BACKUP_DIRECTORY=./backups/database
DB_BACKUP_RETENTION_DAYS=30
DB_BACKUP_COMPRESSION=custom
DB_MIGRATION_BATCH_SIZE=500
DB_MIGRATION_STRICT=true
DB_MIGRATION_ALLOW_PARTIAL=false
```

Development can continue using SQLite when explicitly selected for local tests. Production can require PostgreSQL. `DATABASE_URL` is never returned by diagnostics endpoints. The current source-code Alembic head is `0010_alembic_version_capacity`; runtime migration state must be checked against the configured database before a release or UAT. Earlier revision `0002_auth_sessions_security` is a historical Task 12A revision.

On the audited workstation, `backend/.env` is the active runtime `DATABASE_URL` source because there is no shell override. It resolves to the PostgreSQL `organicai_app` target on `127.0.0.1:55432`; it must never be silently replaced by SQLite. On 2026-08-24 that port was Docker Desktop's proxy and its Linux VM route was unavailable. Recover Docker Desktop/WSL networking and the existing container before attempting a migration or runtime validation; do not reset Docker or recreate the database as a workaround.

## Authentication Variables

```env
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
AUTH_COOKIE_NAME=organicai_refresh
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
AUTH_REQUIRE_ORIGIN_CHECK=true
AUTH_REQUIRE_VERIFIED_EMAIL=false
AUTH_MAX_FAILED_LOGIN_ATTEMPTS=5
AUTH_LOCKOUT_MINUTES=15
AUTH_MAX_ACTIVE_SESSIONS=10
ACCOUNT_TOKEN_EXPIRE_MINUTES=60
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
EMAIL_DELIVERY_DRIVER=disabled
EMAIL_OUTBOX_PATH=./tmp/email-outbox.jsonl
```

Production should use HTTPS, `AUTH_COOKIE_SECURE=true`, explicit allowed origins, real email delivery, and manual rotation of any secret ever exposed in local archives or logs.

## Persistence Diagnostics

`GET /api/system/persistence` returns sanitized database state:

- driver;
- reachable;
- current schema revision;
- Alembic head revision;
- migration state;
- sanitized pool settings;
- backup availability;
- last integrity status.

It follows the same production diagnostics-token rule as `/api/system/configuration`.
# Task 12B Privacy Runtime Configuration

Technical draft - requires legal review before public deployment.

Relevant settings:

- `PRIVACY_EXPORT_DIRECTORY`
- `PRIVACY_EXPORT_EXPIRE_HOURS`
- `PRIVACY_ACCOUNT_DELETION_GRACE_DAYS`
- `PRIVACY_RECENT_AUTH_MINUTES`
- `REAL_PRIVACY_PROVIDER_TESTS_ENABLED`
- `ELEVENLABS_PROVIDER_DELETION_ENABLED`
- `ELEVENLABS_RETENTION_STATUS`
- `ELEVENLABS_AUDIO_SAVING_STATUS`
- `ELEVENLABS_ZERO_RETENTION_STATUS`

The default local frontend remains `http://127.0.0.1:5190`; the default local backend remains `http://127.0.0.1:8020`.
