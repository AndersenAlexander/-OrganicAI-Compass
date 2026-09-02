# Failure Recovery Drills

Scope: Task 13C.0.2 local production rehearsal.

Status: PASSED on 2026-08-03.

Evidence: `evidence/task13c02/failure-recovery-current.json`.

## Drills Executed

- Backend restart: service restarted and `/health/ready` recovered.
- Proxy restart: proxy stopped, restarted and `/health/ready` recovered through `http://127.0.0.1:28080`.
- Worker one-shot: worker container started and reported an acceptable running/exited state with exit code `0`.

## Recovery Criteria

- PostgreSQL volume remains mounted and preserved.
- Readiness reports PostgreSQL reachable.
- Readiness reports migration state `current`.
- No real providers are called.
- No real email is sent.
- No staging, development, test or real production resource is targeted.

## Escalation Notes

If a production recovery drill fails, stop promotion and preserve logs before any restart loop or rollback. Database restore must first be tested in a disposable target. Public production recovery also requires named incident ownership, external monitoring evidence and customer-impact communications, which remain external/manual blockers.
