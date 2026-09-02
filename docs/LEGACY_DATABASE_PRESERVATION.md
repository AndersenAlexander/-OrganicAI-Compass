# Legacy Database Preservation

Date: 2026-07-27

Task 11.4 preserves the original legacy SQLite database as immutable evidence.

## Original Role

- File: `backend/organicai.db`
- Role: immutable evidence
- Runtime use: disabled
- Cleanup/stamping: not performed
- Direct migration: not performed
- Foreign-key orphan count retained in original: `156`

The original still contains the historical orphan rows identified in Task 11.1 and Task 11.3. Those rows are preserved in place and are not served through the application.

## Immutability Proof

Task 11.4 captured before/after evidence and a post-activation proof.

Stable fields:

- SHA-256 prefix: `9e609cc07e74`
- File size: `8392704` bytes
- Table count: `165`
- Application row counts unchanged: yes
- Foreign-key violation count unchanged: yes
- Modified during Task 11.4: no

Evidence:

- `reports/database-integrity/original-sqlite-before-task11-4.json`
- `reports/database-integrity/original-sqlite-after-task11-4.json`
- `reports/database-integrity/original-sqlite-post-activation-proof.json`

## Backup Chain

The final original backup was created through the SQLite backup API and verified logically against the source.

- Backup: `backend/backups/database/organicai-original-final-20260727-154512.db`
- Backup manifest: `backend/backups/database/organicai-original-final-20260727-154512.manifest.json`
- Chain report: `reports/database-integrity/original-sqlite-chain-of-custody.json`
- SQLite integrity: ok
- Logical row counts match: yes
- Chain verification passed: yes

SQLite backup API output may not be byte-for-byte identical to the source file because SQLite can rewrite pages while preserving logical content. Task 11.4 therefore records physical hashes and requires logical equivalence for the chain proof.

## Orphan Archive

Task 11.3 archived the orphan messages locally. Task 11.4 reverified that archive before promotion.

- Archived orphan messages: `156`
- Source orphan count: `156`
- Archive verification passed: yes
- Archived rows inserted into active PostgreSQL `messages`: `0`
- Data loss: `0`

Evidence:

- `reports/database-integrity/final-orphan-archive-verification.json`
- `backend/backups/legacy-orphans/organicai-orphan-messages-20260727-144408.db`

## Access Boundary

Legacy artifacts are CLI/file-system evidence only. The backend does not serve the original SQLite file, clean fallback, backups, orphan archive, or integrity reports through HTTP.

Evidence:

- `reports/database-integrity/legacy-artifact-accessibility-proof.json`

