# Staging Backup and Restore

Technical draft — requires legal and operational review before public deployment.

Create custom-format backups from `organicai_staging`. Restore validation must target `organicai_staging_restore_validation`, never the active staging database.

Evidence must include SHA-256, `pg_restore --list`, Alembic revision `0004_provider_operations`, table count, row count comparison, deletion suppression verification and confirmation that no legacy orphan archive was imported.
