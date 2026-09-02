# Backup Restore Validation Report

Scope: Task 13C.0.2 local production rehearsal.

Status: PASSED on 2026-08-03.

## Backup

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-backup.ps1
```

Result:

- Backup file: `organicai-prod-rehearsal-20260803-190618.dump`
- Manifest file: `organicai-prod-rehearsal-20260803-190618.manifest.json`
- Format: PostgreSQL custom dump
- Schema version: `0004_provider_operations`
- PostgreSQL version: `16.6`
- Backup location: `.tmp/production-rehearsal/backups/`
- Source control: backup content not committed
- Evidence: `evidence/task13c02/backup-current.json`

The manifest is sanitized and includes only database identity flags, table counts, file name, checksum and size. It does not include connection URLs, passwords or provider secrets.

## Restore

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-restore.ps1
```

Result:

- Restore target: `organicai_prod_rehearsal_restore`
- Active database used as target: false
- Restore status: success
- Schema drift after restore: passed
- Drift count: `0`
- Evidence: `evidence/task13c02/restore-current.json`

The restore target guard blocks staging, test, development, production-like protected names and the active rehearsal database.
