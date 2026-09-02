# Data Retention Schedule

Technical draft - requires legal review before public deployment.

Technical draft — requires legal and operational review before public deployment.

Configured retention controls:

- Privacy exports expire after `PRIVACY_EXPORT_EXPIRE_HOURS`.
- Account deletion grace period is `PRIVACY_ACCOUNT_DELETION_GRACE_DAYS`.
- Auth sessions expire by auth session settings and are removed by retention worker.
- Backups are retained according to `DB_BACKUP_RETENTION_DAYS`.
- Legacy orphan archive remains immutable local evidence and outside active product flows.

Worker scripts:

- `backend/app/scripts/run_retention_worker.py --dry-run`
- `backend/app/scripts/run_retention_worker.py --apply`
- `backend/app/scripts/run_privacy_worker.py --once`
- `backend/app/scripts/run_operational_workers.py --status`
- `backend/app/scripts/run_operational_workers.py --once --worker retention`

Retention dry-run must report planned deletions before apply mode is used.
