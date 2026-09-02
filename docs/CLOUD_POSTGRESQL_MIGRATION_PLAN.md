# Cloud PostgreSQL Migration Plan

Technical draft - requires provider approval before execution.

The cloud staging database must be separate from `organicai_app`, `organicai_staging` and `organicai_staging_restore_validation`.

Suggested logical name: `organicai_cloud_staging`.

Plan:

1. Provision PostgreSQL.
2. Create a restricted application role.
3. Require TLS.
4. Run a connectivity check.
5. Create a pre-migration backup if data exists.
6. Run the Alembic migrator.
7. Verify revision `0004_provider_operations`.
8. Verify one Alembic head.
9. Verify schema drift zero.
10. Seed synthetic staging data.
11. Run smoke tests.
12. Validate backup.
13. Validate restore into a separate database.

Do not migrate local personal or development data into cloud staging.
