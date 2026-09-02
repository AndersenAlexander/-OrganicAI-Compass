# Final Data Reconciliation

Date: 2026-07-27

This document records how Task 11.4 accounts for the original legacy dataset, the clean SQLite fallback, the orphan archive, and final PostgreSQL runtime data.

## Reconciliation Model

The original SQLite database remains immutable evidence. It is not the active application database.

Rows are accounted for through two destinations:

- valid active rows: promoted through the clean SQLite fallback and migrated into PostgreSQL;
- legacy orphan messages: preserved in a local SQLite archive and intentionally excluded from active `messages`.

## Counts

Pre-runtime-smoke reconciliation:

- Original valid active rows: `4607`
- Clean SQLite active rows: `4607`
- PostgreSQL active rows after migration: `4607`
- Original orphan messages: `156`
- Archived orphan messages: `156`
- Lost active rows: `0`
- Lost archived rows: `0`
- Duplicate active rows: `0`
- Duplicate archived rows: `0`
- Unaccounted rows: `0`
- Reconciliation passed: yes

Post-runtime-smoke PostgreSQL count:

- Active PostgreSQL application rows after synthetic validation writes: `4724`
- Reason for increase: Task 11.4 runtime smoke created synthetic user, profile, conversation, RAG, recommendation, roadmap, and voice metadata records.
- Post-activation backup manifest row count matches this runtime state.

## Evidence

- `reports/database-integrity/final-data-reconciliation.json`
- `reports/database-integrity/pre-rollback-postgres-row-counts.json`
- `backend/backups/database/organicai-app-post-activation-20260727-163338.manifest.json`

## Privacy Boundary

Reconciliation reports contain table counts and booleans only. They do not include message bodies, transcripts, raw row identifiers, emails, tokens, credentials, or full database URLs.

