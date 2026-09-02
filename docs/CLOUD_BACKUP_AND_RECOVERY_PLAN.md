# Cloud Backup and Recovery Plan

Technical draft - requires provider approval before implementation.

Requirements:

- Managed PostgreSQL backup where available.
- Approved backup retention.
- Encrypted backup storage.
- Restore testing into a separate target.
- Backup before migrations.
- Evidence of latest restore drill.
- Recovery point objective: to be approved.
- Recovery time objective: to be approved.
- No unverified production assumptions.

Restore drills must not overwrite staging or production databases. Restore validation must use a separate database or isolated environment.
