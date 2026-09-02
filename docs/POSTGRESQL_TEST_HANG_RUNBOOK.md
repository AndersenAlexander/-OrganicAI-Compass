# PostgreSQL Test Hang Runbook

Technical draft - local validation only.

Use this runbook when `pytest -m postgres` hangs, times out or fails before migration.

1. Collect marker inventory:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest -m postgres --collect-only -q
```

2. Prepare the isolated database:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\prepare-postgres-test-database.ps1 -DatabaseName organicai_task13b03_test
```

3. Run one node with bounded diagnostics:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-postgres-test-hang.ps1 -NodeId "tests/test_release_gate_persistence.py::test_postgres_release_gate_core_persistence_behaviors"
```

4. Run the marker suite:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\run-postgres-marker-tests.ps1 -DatabaseName organicai_task13b03_test
```

Diagnostics are sanitized and must not include passwords, complete database URLs, raw personal data or SQL bind values.

Current local failure mode:

- Docker Desktop API returned HTTP 500 for container inspection and compose startup.
- `127.0.0.1:55432` initially accepted TCP connections through `com.docker.backend`.
- psycopg2 initially failed during PostgreSQL handshake with `timeout expired`.
- A controlled Docker Desktop restart was attempted for Task 13B.0.3, but Docker Desktop remained in `starting` and Docker WSL distributions stopped.
- Final PostgreSQL handshake failed with connection refused because the Docker port proxy no longer listened on `55432`.
- Task 13B.0.3-R1 was run after a manual Windows restart. Docker Desktop still reported `starting`, Docker server commands failed with `Docker Desktop is unable to start`, and port `55432` was not listening.

Required remediation before rerun:

- Recover Docker Desktop manually through the UI or host-level troubleshooting, or provide a reachable local PostgreSQL server bound only to the approved local test port.
- Keep `organicai_staging_postgres_data` intact.
- Do not use `docker compose down -v`.
- Use only `organicai_task13b03_test` or another guard-approved disposable database.
