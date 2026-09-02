# Legacy Data Remediation

Date: 2026-07-27

## Policy

Task 11.1 does not authorize changes to `backend/organicai.db`.

Allowed remediation actions for future review are limited to:

- `retain-and-relink`
- `delete-child-after-review`
- `restore-parent-from-backup`
- `set-null-if-semantically-valid`
- `archive-outside-active-schema`
- `ignore-with-explicit-waiver`
- `manual-review`

Do not automatically create placeholder users, profiles, conversations, or roadmaps.

## Current Plan

The generated remediation plan is:

```text
reports/database-integrity/legacy-orphan-remediation-plan.json
```

Current plan characteristics:

- Legacy database modification authorized: no
- Automatic placeholder parents: no
- Actions approved for simulation: none
- Human review required: yes

## Simulation

The repair simulation command creates a disposable SQLite copy using the SQLite backup API:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.simulate_legacy_repair --dry-run
```

Simulation result:

- Copy created: `backend/tmp/legacy-analysis/organicai-repair-simulation.db`
- Original source unchanged during simulation: yes
- Approved actions found: `0`
- Orphan violations before: `156`
- Orphan violations after: `156`

The simulation verifies the mechanism only. It does not repair production data.

## Task 11.3 Simulation Result

Task 11.3 superseded the Task 11.1 dry-run mechanism with a full non-destructive remediation simulation.

New generated artifacts:

- `reports/database-integrity/legacy-remediation-manifest.json`
- `reports/database-integrity/legacy-remediation-clone-journal.json`
- `reports/database-integrity/legacy-remediation-clone-verification.json`
- `reports/database-integrity/legacy-data-reconciliation.json`
- `reports/database-integrity/original-database-proposed-actions.json`

Simulation result:

- Complete orphan archive verified: yes
- Clone initially matched verified source backup: yes
- Empty `alembic_version` removed only from clone: yes
- Exact relinks: `0`
- Reconstructed parents: `0`
- Archived and removed from active clone: `156`
- Retained blocking rows: `0`
- Clone foreign-key violations after: `0`
- Lost rows: `0`
- Duplicate rows: `0`
- Applied to original: no

Task 11.4 must explicitly approve any original-database operation.
