# Rollback Requirements

- Deployment references an exact commit and immutable image digest where supported.
- Previous image remains available.
- Database downgrade or compatibility plan is documented.
- Restore target is separate from active staging.
- Rollback evidence is recorded.
