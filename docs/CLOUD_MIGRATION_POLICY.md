# Cloud Migration Policy

Technical draft - requires operational review before cloud deployment.

- Migrations run as a dedicated deployment job.
- Backend containers do not all run migrations.
- Migration must complete before a new application revision becomes ready.
- Migration failure blocks deployment.
- Destructive migration requires explicit approval.
- Backup verification precedes destructive migration.
- Downgrade procedure must be documented before release.
- Application revision and database revision must be compatible.
- No automatic SQLite fallback is allowed in staging or production.
