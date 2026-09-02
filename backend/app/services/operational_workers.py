from __future__ import annotations

import signal
import time
from datetime import datetime, timedelta
from app.core.time import utc_now_naive
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.provider_operations import OperationalJobRun
from app.privacy.service import retention_dry_run
from app.services.metrics import record_privacy_job, record_worker_heartbeat, record_worker_job
from app.services.telemetry import emit_validation_span, flush_telemetry
from app.services.token_hashing import hash_secret


WORKERS = {"privacy", "retention", "account-deletion", "provider-deletion", "email-cleanup", "expired-token-cleanup", "deletion-ledger"}
SYNTHETIC_WORKER = "synthetic_validation"
STOP_REQUESTED = False


def request_worker_stop(_signum=None, _frame=None) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True


def install_worker_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, request_worker_stop)
    signal.signal(signal.SIGINT, request_worker_stop)


def worker_status(db: Session) -> dict:
    latest = {}
    for worker in WORKERS:
        row = db.scalar(select(OperationalJobRun).where(OperationalJobRun.job_type == worker).order_by(OperationalJobRun.started_at.desc()))
        latest[worker] = {
            "status": row.status if row else "not-run",
            "heartbeatAt": row.heartbeat_at.isoformat() if row and row.heartbeat_at else None,
            "lastRunAt": row.started_at.isoformat() if row else None,
        }
    return {"workers": latest, "destructiveJobsEnabled": False}


def run_worker_once(db: Session, worker: str = "privacy", worker_id: str = "local") -> dict:
    if worker not in WORKERS:
        return {"status": "failed", "failureCode": "UNKNOWN_WORKER"}
    now = utc_now_naive()
    run = OperationalJobRun(
        job_type=worker,
        status="running",
        started_at=now,
        heartbeat_at=now,
        lease_expires_at=now + timedelta(minutes=5),
        worker_id_hash=hash_secret(worker_id),
        failure_summary_json={},
    )
    db.add(run)
    db.flush()
    record_worker_job(worker, "running")
    record_worker_heartbeat(worker)
    result = retention_dry_run(db) if worker in {"privacy", "retention"} else {"dryRun": True, "processed": 0}
    run.status = "completed"
    run.completed_at = utc_now_naive()
    run.processed_count = int(result.get("expiredExports", 0) + result.get("expiredAuthSessions", 0)) if isinstance(result, dict) else 0
    run.succeeded_count = run.processed_count
    db.commit()
    record_worker_job(worker, "completed")
    if worker in {"privacy", "retention", "account-deletion", "provider-deletion"}:
        record_privacy_job(worker if worker not in {"privacy"} else "privacy-export", "completed")
    return {"status": run.status, "jobType": worker, "processedCount": run.processed_count, "dryRun": True}


def enqueue_synthetic_job(db: Session, mode: str = "complete", delay_seconds: float = 0.0) -> OperationalJobRun:
    now = utc_now_naive()
    run = OperationalJobRun(
        job_type=SYNTHETIC_WORKER,
        status="queued",
        started_at=now,
        heartbeat_at=None,
        lease_expires_at=None,
        worker_id_hash=None,
        failure_summary_json={
            "mode": mode,
            "delaySeconds": min(max(float(delay_seconds), 0.0), 20.0),
            "validation": True,
        },
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def acquire_synthetic_job(db: Session, worker_id: str, lease_seconds: int = 30) -> OperationalJobRun | None:
    now = utc_now_naive()
    stmt = (
        select(OperationalJobRun)
        .where(
            OperationalJobRun.job_type == SYNTHETIC_WORKER,
            OperationalJobRun.status.in_(["queued", "processing"]),
        )
        .where((OperationalJobRun.lease_expires_at.is_(None)) | (OperationalJobRun.lease_expires_at < now))
        .order_by(OperationalJobRun.started_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    with db.begin():
        run = db.scalar(stmt)
        if not run:
            return None
        run.status = "processing"
        run.heartbeat_at = now
        run.lease_expires_at = now + timedelta(seconds=lease_seconds)
        run.worker_id_hash = hash_secret(worker_id)
        run.retry_count += 1
        record_worker_job(SYNTHETIC_WORKER, "processing")
        record_worker_heartbeat(SYNTHETIC_WORKER)
        return run


def complete_synthetic_job(db: Session, run: OperationalJobRun) -> None:
    run.status = "completed"
    run.completed_at = utc_now_naive()
    run.processed_count = 1
    run.succeeded_count = 1
    run.heartbeat_at = utc_now_naive()
    run.lease_expires_at = None
    db.commit()
    record_worker_job(SYNTHETIC_WORKER, "completed")


def release_synthetic_lease(db: Session, run: OperationalJobRun, reason: str = "shutdown") -> None:
    run.status = "queued"
    run.heartbeat_at = utc_now_naive()
    run.lease_expires_at = utc_now_naive() - timedelta(seconds=1)
    summary = dict(run.failure_summary_json or {})
    summary["leaseReleased"] = reason
    run.failure_summary_json = summary
    db.commit()
    record_worker_job(SYNTHETIC_WORKER, "lease_released")


def run_synthetic_continuous_worker(db_factory, worker_id: str | None = None, poll_seconds: float = 1.0) -> dict:
    install_worker_signal_handlers()
    global STOP_REQUESTED
    STOP_REQUESTED = False
    worker_id = worker_id or f"worker-{uuid4().hex[:8]}"
    processed = 0
    leased_job_id = None
    exit_reason = "completed"
    while not STOP_REQUESTED:
        with db_factory() as db:
            run = acquire_synthetic_job(db, worker_id)
            if not run:
                record_worker_heartbeat(SYNTHETIC_WORKER)
                time.sleep(poll_seconds)
                continue
            leased_job_id = run.id
            summary = dict(run.failure_summary_json or {})
            delay = float(summary.get("delaySeconds") or 0.0)
            emit_validation_span(
                "worker.synthetic_validation",
                {
                    "worker.job_type": SYNTHETIC_WORKER,
                    "worker.mode": str(summary.get("mode") or "complete"),
                },
            )
            deadline = time.monotonic() + delay
            while time.monotonic() < deadline:
                if STOP_REQUESTED:
                    release_synthetic_lease(db, run)
                    flush_telemetry(timeout_seconds=5)
                    return {
                        "status": "stopped",
                        "workerId": worker_id,
                        "leasedJobId": leased_job_id,
                        "processed": processed,
                        "leaseReleased": True,
                    }
                run.heartbeat_at = utc_now_naive()
                db.commit()
                time.sleep(min(0.5, max(0.1, deadline - time.monotonic())))
            complete_synthetic_job(db, run)
            processed += 1
            if summary.get("mode") == "single":
                break
    if STOP_REQUESTED:
        exit_reason = "stopped"
    flush_telemetry(timeout_seconds=5)
    return {"status": exit_reason, "workerId": worker_id, "processed": processed, "leaseReleased": False}

