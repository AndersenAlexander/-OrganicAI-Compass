# Application Rollback Runbook

Scope: local production rehearsal and production-preparation procedure.

## Local Rehearsal Command

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-rollback.ps1
```

The rehearsal tags the current backend image as `organicai-compass-backend:production-rehearsal-rollback-candidate`, retags it as the active rehearsal backend image, recreates the backend container without touching PostgreSQL, and requires `/health/ready` to recover.

Evidence: `evidence/task13c02/application-rollback-current.json`.

## Production Procedure

1. Pause new deployment promotion.
2. Confirm the previous image digest and migration compatibility.
3. Confirm no destructive schema migration is required for rollback.
4. Route traffic to the previous image or recreate the application service from the previous image.
5. Verify liveness, readiness, login, privacy unauthorized response and provider-disabled fallback paths.
6. Keep the database volume and backup chain intact.
7. Record the incident timeline, image digests, health evidence and follow-up action.

Rollback must not run database restore directly against the active production database. Restores are validated first into a disposable target.
