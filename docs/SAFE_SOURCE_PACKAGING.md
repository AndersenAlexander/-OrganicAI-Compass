# Safe Source Packaging

Date: 2026-07-27

Use the Task 12A source archive tool to create sanitized source ZIP files.

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.create_source_archive --output ..\OrganicAI-Compass-source.zip
```

The tool excludes `.env` files, virtual environments, dependencies, build output, local databases, dumps, logs, `backend/data`, `backend/backups`, `backend/tmp`, reports, Playwright artifacts, test results, and root-level local screenshot/image artifacts.

The archive includes a sanitized `SOURCE_ARCHIVE_MANIFEST.json` and does not include secret values.
# Task 12B Packaging Exclusions

Technical draft - requires legal review before public deployment.

Safe source archives must exclude `backend/tmp/privacy-exports`, `backend/tmp/email-outbox`, `backend/tmp/privacy-worker`, `backend/tmp/provider-deletion`, and all local database, backup, report artifact, environment, and generated build directories. Privacy exports are user data artifacts and must never be included in source packages.

