# Week 7 clean validation runbook

This runbook is the standard local procedure for feature-frozen release-candidate validation. It never points automated tests at the development or production database.

## Fresh backend-dependent E2E run

From the repository root in PowerShell:

```powershell
.\scripts\playwright-clean-run.ps1 -Spec tests/e2e/human-diagnostic-full.integration.spec.ts
```

The script:

- removes only the dedicated `backend/tmp/playwright-clean.db` fixture;
- runs `alembic upgrade head` before the test;
- uses `PLAYWRIGHT_DATABASE_URL=sqlite:///./tmp/playwright-clean.db`;
- uses dedicated ports `8036` and `5196`;
- uses the global `python.exe` override when the repository `.venv` is stale;
- cleans listeners on those dedicated ports after the run.

For several specs, pass a PowerShell array:

```powershell
.\scripts\playwright-clean-run.ps1 -Spec @(
  "tests/e2e/human-diagnostic-full.integration.spec.ts",
  "tests/e2e/assessment-career.spec.ts"
)
```

Frontend-only suites do not require a database. They can reuse the QA frontend:

```powershell
$env:PLAYWRIGHT_CHANNEL = "msedge"
$env:PLAYWRIGHT_FRONTEND_ONLY = "true"
$env:PLAYWRIGHT_REUSE_EXISTING_SERVER = "true"
npm.cmd exec -- playwright test tests/e2e/home.spec.ts tests/e2e/light-mode-visibility.spec.ts
```

## Windows teardown limitation

Playwright documents that `gracefulShutdown` is ignored on Windows. When the outer command is forcibly timed out, the managed `cmd.exe`/Node/Python descendants can remain bound to the dedicated ports even though test assertions already passed. This was reproduced on Week 7 with a fresh database.

The safe procedure is:

1. use the dedicated ports from the script;
2. wait for the command to return whenever possible;
3. if the outer runner times out, inspect only those ports;
4. stop only the listener PIDs on `8036` and `5196`;
5. rerun with a new clean database if the run was interrupted.

Example cleanup for the dedicated ports:

```powershell
foreach ($port in @(8036, 5196)) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue }
}
```

Do not apply this cleanup to the active development ports `8020` or `5190`.

## Migration checks

```powershell
Set-Location backend
python.exe -m alembic heads
python.exe -m alembic history
$env:DATABASE_URL = "sqlite:///./tmp/week7-migration-head.db"
python.exe -m alembic upgrade head
python.exe -m alembic current
```

Expected source head: `0009_collaboration_traceability_extensions`, with one head and no duplicate revision IDs.
