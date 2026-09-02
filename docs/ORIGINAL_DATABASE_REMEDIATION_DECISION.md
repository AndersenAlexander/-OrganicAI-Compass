# Original Database Remediation Decision

Task 11.3 does not approve changes to `backend/organicai.db`.

## Current Original State

- Empty `alembic_version` table exists.
- 156 orphan `messages` rows reference missing `conversations` rows.
- 156 distinct affected rows were detected.
- Other application data remained intact in the Task 11.3 evidence comparison.
- Strict production migration remains blocked until original cleanup is explicitly approved.

## Proposed Safe Operation

The proposed Task 11.4 operation is:

1. Create a new verified backup of the original database.
2. Create and verify the orphan archive.
3. Apply exact relinks only if exact evidence is proven.
4. Reconstruct parent conversations only if exact evidence is proven.
5. Archive unresolved messages.
6. Remove archived unresolved rows from active `messages`.
7. Remove the empty `alembic_version` table.
8. Verify zero data loss through reconciliation.

## Task 11.3 Evidence

- Exact relink rows: 0
- Reconstructed parent rows: 0
- Archive-and-remove rows proposed: 156
- Retain-blocking rows: 0
- Approved for original: false
- Applied to original: false

Machine-readable proposed actions:

```text
reports/database-integrity/original-database-proposed-actions.json
```

Manual approval is required before any original-database modification.
