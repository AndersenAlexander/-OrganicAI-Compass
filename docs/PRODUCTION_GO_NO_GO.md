# Production Go/No-Go

Status: deterministic checker implemented. It must not report production readiness while external required items are unresolved.

Commands:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.production_go_no_go --format json
.\.venv\Scripts\python.exe -m app.scripts.production_go_no_go --format text
```

The checker summarizes:

- environment configuration;
- secret placeholder and rotation status;
- local release-candidate evidence;
- local staging evidence;
- local production rehearsal evidence;
- source archive safety;
- email status;
- DNS/TLS flags;
- remote CI flag;
- real provider acceptance flags;
- backup/restore flag;
- monitoring/incident owner flag;
- legal/privacy approval flag.

Classifications:

- `local_release_candidate_ready`
- `local_staging_validated`
- `local_production_rehearsal_validated`
- `production_deployment_ready`
- `production_operationally_ready`

It exits non-zero while production deployment or operational blockers remain. The JSON report includes `secretValuesIncluded=false`.

Task 13C.0.2 adds `LOCAL-PROD-REHEARSAL` as a required deployment and operations check. The current local evidence in `evidence/task13c02/final-summary.json` passes, but production remains blocked until external/manual items are completed.
