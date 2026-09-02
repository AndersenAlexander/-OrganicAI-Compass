# Legacy Orphan Analysis

Date: 2026-07-27

## Source

Legacy database:

```text
backend/organicai.db
```

The analysis command opens the database read-only:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.analyze_legacy_orphans `
  --database ./organicai.db `
  --output ..\reports\database-integrity\legacy-orphans.json
```

## Result

The generated report confirms:

- Orphan violations: `156`
- Distinct affected rows: `156`
- SQLite integrity check: `ok`
- Raw identifiers included: no
- Row content included: no

Highest-risk concentration:

- `messages` -> `conversations`
- Orphan violations: `156`
- Category: conversation/history orphans
- Risk: high
- Recommended action: manual review

## Root Cause Assessment

The probable root cause is historical SQLite referential-integrity drift. The legacy database had no valid Alembic revision when the baseline was captured, and SQLite foreign-key enforcement was not sufficient to prevent orphaned `messages` rows.

No user, conversation, message, profile, RAG, token, password, or transcript content is included in the report. Affected row identifiers are represented by SHA-256 hashes truncated to 16 hex characters with process-local salt.

## Reports

Sanitized local reports:

- `reports/database-integrity/legacy-orphans.json`
- `reports/database-integrity/legacy-orphan-remediation-plan.json`
- `reports/database-integrity/legacy-repair-simulation.json`

The original database must not be repaired until the remediation plan is reviewed and explicitly approved.

## Task 11.2 Safety Verification

Task 11.2 did not modify `backend/organicai.db`.

Safety evidence:

- Report: `reports/database-integrity/legacy-sqlite-task11-2-safety.json`
- Changed during Task 11.2: `false`
- SHA-256 prefix unchanged: `9e609cc07e74`
- File size unchanged: `true`
- Modified time unchanged: `true`
- Row counts unchanged: `true`
- Empty `alembic_version` still empty: `true`

The legacy dry-run remains blocked with `SOURCE_FOREIGN_KEY_ORPHANS`. Do not remove the empty `alembic_version` table or mutate legacy data without an explicit operator decision.

## Task 11.3 Forensic Update

Task 11.3 added message-level forensic analysis without exposing message content or raw identifiers.

Generated report:

```text
reports/database-integrity/legacy-orphan-forensic-analysis.json
```

Results:

- Orphan message rows: `156`
- Missing conversation groups: `26`
- Owner resolved rows: `0`
- Owner unknown rows: `156`
- Demo/test messages: `26`
- System-generated messages: `52`
- Ordinary user content: `78`
- Potentially sensitive personal content: `0`
- Exact relink candidates: `0`
- Proven-parent reconstruction candidates: `0`
- Archive-only candidates: `156`

The Task 11.3 archive and clone simulation passed, but the original database remains unchanged and still requires explicit approval before cleanup.
