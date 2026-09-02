# Legacy Remediation Simulation

Task 11.3 executed a non-destructive remediation simulation for `backend/organicai.db`.

## Boundary

The original SQLite database was accessed through read-only SQLite connections for evidence and forensic analysis. No original `INSERT`, `UPDATE`, `DELETE`, `DROP TABLE`, `ALTER TABLE`, Alembic stamp, Alembic upgrade, repair apply, or migration apply was authorized or performed.

All mutation happened only on:

```text
backend/tmp/legacy-remediation/organicai-remediation-clone.db
```

## Results

- Original table count: 165
- Original application table count: 164
- Empty original `alembic_version` table: present
- Original orphan violations: 156
- Distinct affected rows: 156
- Missing conversation groups: 26
- Exact relink candidates: 0
- Proven-parent reconstruction candidates: 0
- Archive-only candidates: 156
- Manual-review candidates: 0

## Clone Actions

The clone was created from the verified pre-remediation backup using the SQLite backup API. The clone initially matched the backup hash.

Applied to the clone:

- Dropped the empty `alembic_version` table after dependency checks.
- Verified the orphan archive.
- Removed 156 archive-verified orphan messages from active `messages`.
- Re-stamped the clean clone to exact revision `0001_initial_schema` after schema equivalence passed.

Not applied:

- Original database changes: 0
- Relinks: 0
- Reconstructed parent conversations: 0
- Placeholder conversations: 0

## Verification

- Clone SQLite integrity: ok
- Clone foreign-key violations after remediation: 0
- Non-orphan messages unchanged: yes
- Users unchanged: yes
- Profiles unchanged: yes
- Recommendations unchanged: yes
- Roadmaps unchanged: yes
- Lost rows: 0
- Duplicate archived rows: 0
- Unaccounted rows: 0

Primary reports:

```text
reports/database-integrity/legacy-remediation-manifest.json
reports/database-integrity/legacy-remediation-clone-journal.json
reports/database-integrity/legacy-remediation-clone-verification.json
reports/database-integrity/legacy-data-reconciliation.json
reports/database-integrity/clean-clone-inventory.json
```
