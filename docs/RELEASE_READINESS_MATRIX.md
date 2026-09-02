# Release Readiness Matrix

**Audit date:** 2026-08-24  
**Verdict:** **Not ready for controlled UAT on this workstation until PostgreSQL is restored.** The codebase has substantial isolated technical evidence, but the configured runtime database cannot complete a PostgreSQL connection handshake.

| Gate | Status | Evidence / required action |
|---|---|---|
| Feature freeze | PASS | Only a demo-seed regression repair, stale E2E selector alignment, and release documentation were changed in this pass. |
| Migration graph | PASS (source / disposable SQLite) | One head: `0010_alembic_version_capacity`; fresh disposable SQLite upgrades from 0001 to 0010. |
| Existing PostgreSQL migration state | BLOCKED | `alembic current` cannot connect because Docker Desktop's VM endpoint is unroutable. Restore Docker Desktop/WSL networking, then run read-only `current` before any upgrade. |
| Runtime backend health | BLOCKED | Port 55432 is Docker Desktop PID 15464. Its proxy logs `no route to host` for `192.168.65.7:2376`, so port 8020 cannot complete database-backed health/readiness. |
| Live authentication and existing-user preservation | BLOCKED | No runtime account or user-data operation was performed; validate existing account, fresh QA registration, logout/login, and authenticated read after database restoration. |
| Backend regression | PASS (isolated) | 229 passed, 5 PostgreSQL-only skipped, 86 warnings. |
| Frontend quality | PASS with performance follow-up | Typecheck, 80 unit tests, and production build passed; bundle-size warnings remain. |
| Browser core selection | PARTIAL / isolated | 44 focused assertions passed; accessibility visual smoke passed; the long human journey runner was interrupted during Windows teardown after reaching deep workflow steps. Re-run after runtime repair for final UAT evidence. |
| Security/ownership | PASS (technical) | Focused authentication and authorization suites passed; live runtime confirmation remains blocked by PostgreSQL. |
| Accessibility, themes and mobile | PASS (representative visual smoke) | 42 local light/dark desktop/tablet/mobile screenshots; this is not a full accessibility conformance audit. |
| Providers | CONDITIONAL | Optional providers were not live-validated during the unavailable-runtime audit. Their status must be explicit; no silent fallback. |
| Privacy/operations | CONDITIONAL | Requires deployment secrets, transport, backups, monitoring, legal/privacy review, and penetration testing outside this local audit. |
| Dissertation demonstration | CONDITIONAL | Technically demonstrable after PostgreSQL restoration; retain the limitation wording and avoid empirical/predictive claims. |

## Release blocker exit criteria

In an authorized desktop session, start/restart Docker Desktop's stopped service and VM/WSL backend without using Docker Reset, volume removal, database recreation, or a SQLite override. Wait for the existing PostgreSQL container health check to pass; then verify a read-only connection to `organicai_app`, `alembic current`, backend readiness, existing-account login, a fresh disposable QA registration, logout/login persistence, authenticated read, and non-sensitive existing-data counts. Record those results before declaring controlled UAT ready.
