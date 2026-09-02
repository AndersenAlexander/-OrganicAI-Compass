# Local Production Rehearsal Runbook

Use this runbook only for the isolated local production rehearsal stack. Do not point it at staging, development, test or real production resources.

## Start

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-start.ps1 -WithObservability -Smoke
```

The start script generates `.tmp/production-rehearsal.env` if it does not exist. The generated file contains synthetic local-only secrets, provider flags disabled, `APP_ENV=production` and `PRODUCTION_REHEARSAL_MODE=true`.

## Status

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-status.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-status.ps1 -Json
```

Expected endpoints while running:

- App proxy: `http://127.0.0.1:28080`
- Prometheus: `http://127.0.0.1:29090`
- Grafana: `http://127.0.0.1:23000`

## Smoke

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-smoke.ps1
```

The smoke test checks frontend, `/health`, `/health/live`, `/health/ready`, expected `401` on an authenticated privacy endpoint, disabled live voice status, blocked `/internal/metrics` through the proxy and blocked observability paths.

## Backup And Restore

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-backup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-restore.ps1
```

Backups are written under `.tmp/production-rehearsal/backups/` and are ignored by source control. The restore script only targets `organicai_prod_rehearsal_restore`.

## Rollback And Recovery

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-rollback.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-recovery-drills.ps1
```

Rollback recreates the backend service from the tagged rehearsal image and requires readiness recovery. Recovery drills restart backend, restart proxy and execute the one-shot worker.

## Stop

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\production-rehearsal-stop.ps1
```

Default stop preserves containers, volume, backups and logs. Optional `-RemoveContainers` removes only rehearsal containers and still preserves the PostgreSQL volume. Do not use `docker compose down -v`, Docker prune commands, Docker Desktop factory reset or WSL unregister for this rehearsal.
