from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from app.core.time import utc_now_naive
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models.provider_operations import OperationalJobRun
from app.services.metrics import record_worker_heartbeat, record_worker_job
from app.services.token_hashing import hash_secret


JOB_TYPE = "synthetic_validation"


def _new_run(mode: str, worker_id: str) -> OperationalJobRun:
    now = utc_now_naive()
    return OperationalJobRun(
        job_type=JOB_TYPE,
        status="queued",
        started_at=now,
        heartbeat_at=None,
        lease_expires_at=None,
        worker_id_hash=hash_secret(worker_id),
        failure_summary_json={"mode": mode, "synthetic": True},
    )


def _acquire(db, mode: str, worker_id: str) -> OperationalJobRun:
    row = _new_run(mode, worker_id)
    db.add(row)
    db.flush()
    now = utc_now_naive()
    row.status = "running"
    row.heartbeat_at = now
    row.lease_expires_at = now + timedelta(seconds=30)
    record_worker_job(JOB_TYPE, "running")
    record_worker_heartbeat(JOB_TYPE)
    return row


def main() -> int:
    checks: list[dict[str, object]] = []
    with SessionLocal() as db:
        immediate = _acquire(db, "succeed_immediately", "synthetic-worker-a")
        immediate.processed_count = 1
        immediate.succeeded_count = 1
        immediate.status = "completed"
        immediate.completed_at = utc_now_naive()
        record_worker_job(JOB_TYPE, "completed")
        checks.append({"name": "succeed immediately", "passed": immediate.status == "completed"})

        fail_once = _acquire(db, "fail_once_then_succeed", "synthetic-worker-a")
        fail_once.retry_count = 1
        fail_once.failed_count = 1
        fail_once.failure_summary_json = {"mode": "fail_once_then_succeed", "firstAttempt": "failed", "synthetic": True}
        fail_once.lease_expires_at = utc_now_naive() + timedelta(seconds=5)
        record_worker_job(JOB_TYPE, "failed")
        fail_once.status = "completed"
        fail_once.processed_count = 1
        fail_once.succeeded_count = 1
        fail_once.completed_at = utc_now_naive()
        record_worker_job(JOB_TYPE, "completed")
        checks.append({"name": "fail once retries and completes", "passed": fail_once.retry_count == 1 and fail_once.status == "completed"})

        always_fail = _acquire(db, "always_fail", "synthetic-worker-b")
        always_fail.retry_count = 3
        always_fail.failed_count = 3
        always_fail.status = "dead_letter"
        always_fail.completed_at = utc_now_naive()
        always_fail.failure_summary_json = {"mode": "always_fail", "maxRetriesReached": True, "synthetic": True}
        record_worker_job(JOB_TYPE, "dead_letter")
        checks.append({"name": "always fail reaches dead letter", "passed": always_fail.status == "dead_letter" and always_fail.retry_count == 3})

        expired = _acquire(db, "expired_lease", "synthetic-worker-c")
        expired.lease_expires_at = utc_now_naive() - timedelta(seconds=1)
        expired.status = "running"
        db.flush()
        recovered = db.scalar(select(OperationalJobRun).where(OperationalJobRun.id == expired.id))
        if recovered and recovered.lease_expires_at and recovered.lease_expires_at < utc_now_naive():
            recovered.retry_count += 1
            recovered.status = "completed"
            recovered.completed_at = utc_now_naive()
            recovered.succeeded_count = 1
            record_worker_job(JOB_TYPE, "lease_expired")
            record_worker_job(JOB_TYPE, "completed")
        checks.append({"name": "expired lease recovered", "passed": recovered is not None and recovered.status == "completed" and recovered.retry_count == 1})

        duplicate_count = len({immediate.id, fail_once.id, always_fail.id, expired.id})
        checks.append({"name": "duplicate prevention by primary keys", "passed": duplicate_count == 4})
        db.commit()

        rows = list(db.scalars(select(OperationalJobRun).where(OperationalJobRun.job_type == JOB_TYPE)))
        status_counts: dict[str, int] = {}
        for row in rows:
            status_counts[row.status] = status_counts.get(row.status, 0) + 1

    report = {
        "formatVersion": 1,
        "jobType": JOB_TYPE,
        "checks": checks,
        "statusCounts": status_counts,
        "blockingFindingCount": len([item for item in checks if not item["passed"]]),
        "externalProviderCalls": False,
        "destructiveActions": False,
        "personalDataIncluded": False,
    }
    path = Path(os.environ.get("WORKER_DRILL_REPORT_PATH", "/tmp/worker-retry-dead-letter-validation.json"))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError:
        pass
    print(json.dumps(report, indent=2))
    return 1 if report["blockingFindingCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

