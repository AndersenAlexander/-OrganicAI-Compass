# Alembic Migrations

Alembic is configured in `backend/alembic.ini` and `backend/alembic/`.

The current source-code migration chain is:

```text
backend/alembic/versions/0001_initial_schema.py
backend/alembic/versions/0002_auth_sessions_and_account_security.py
backend/alembic/versions/0003_privacy_data_lifecycle.py
backend/alembic/versions/0004_provider_operations.py
backend/alembic/versions/0005_human_diagnostic_v2.py
backend/alembic/versions/0006_evidence_calibration_loop.py
backend/alembic/versions/0007_market_application_provenance.py
backend/alembic/versions/0008_interview_outcome_safety.py
backend/alembic/versions/0009_collaboration_traceability_extensions.py
backend/alembic/versions/0010_alembic_version_capacity.py
```

The current source graph has one head: `0010_alembic_version_capacity`. Revision 0010 is a PostgreSQL-only forward migration that widens `alembic_version.version_num` to 128 characters; it deliberately does not shrink the column on downgrade because historical revision identifiers exceed the earlier capacity. Historical migrations are preserved.

The 2026-08-24 audit upgraded a disposable SQLite database from 0001 to 0010 successfully. Existing PostgreSQL `current`/upgrade verification remains pending until the configured service at `127.0.0.1:55432` completes a connection handshake. Do not use this note as evidence that a disconnected runtime database is current.

Rules:

- Do not put data seeds in schema migrations.
- Do not put secrets or personal data in migration files.
- Do not run migrations automatically at application startup.
- Run upgrades explicitly from the backend directory.

Commands:

```powershell
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe heads
.\.venv\Scripts\alembic.exe history
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe upgrade head --sql
```

Safe wrapper:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.db_migrate status
.\.venv\Scripts\python.exe -m app.scripts.db_migrate upgrade
.\.venv\Scripts\python.exe -m app.scripts.db_migrate stamp --apply
```

Production upgrade requires an explicit production flag through the wrapper. Downgrade is blocked by default.
