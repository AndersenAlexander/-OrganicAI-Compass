# Repository Content Policy

Technical draft - requires operational review before public repository publication.

## Tracked

- Application source under `backend/`, `frontend/`, `browser-extension/`, `deploy/` and `scripts/`.
- Tests, Alembic migrations and static configuration that contains no secrets.
- Dockerfiles, Compose files, Nginx configuration and GitHub Actions workflow definitions.
- Documentation, runbooks and sanitized thesis evidence.
- Safe environment templates: `.env.staging.example`, `.env.cloud-staging.example`, `backend/.env.example` and `frontend/.env.example`.

## Excluded

- Secrets, credentials, `.env` files with real values and private keys.
- Databases, PostgreSQL dumps, backups, restore artifacts and staging volumes.
- Runtime logs, privacy exports, deletion ledgers, development outbox and provider outputs.
- OCI image exports, source archives and generated packages.
- Observability runtime state, Grafana data and Prometheus data.

## Conditional Review

- Screenshots, performance reports, SBOMs, security scan reports, generated evidence, architecture diagrams and sample data.
- Conditional files must be inspected before commit for personal data, credentials, private URLs, database connection strings and excessive binary size.
