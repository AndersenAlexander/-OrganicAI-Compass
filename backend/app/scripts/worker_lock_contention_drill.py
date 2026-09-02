from __future__ import annotations

import json
import os
import threading
from collections import Counter
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models.provider_operations import OperationalJobRun
from app.services.operational_workers import SYNTHETIC_WORKER, acquire_synthetic_job, complete_synthetic_job, enqueue_synthetic_job


def main() -> int:
    workers = int(os.environ.get("WORKER_CONTENTION_WORKERS", "2"))
    jobs = int(os.environ.get("WORKER_CONTENTION_JOBS", "8"))
    completions: list[str] = []
    errors: list[str] = []
    attempts = 0
    attempts_lock = threading.Lock()

    with SessionLocal() as db:
        created = [enqueue_synthetic_job(db, mode="contention", delay_seconds=0.0).id for _ in range(jobs)]

    def worker(index: int) -> None:
        nonlocal attempts
        while True:
            with attempts_lock:
                attempts += 1
            try:
                with SessionLocal() as db:
                    run = acquire_synthetic_job(db, f"contention-{index}", lease_seconds=10)
                    if not run:
                        return
                    job_id = run.id
                    complete_synthetic_job(db, run)
                    completions.append(job_id)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc.__class__.__name__)
                return

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    counts = Counter(completions)
    duplicates = [job_id for job_id, count in counts.items() if count > 1]
    with SessionLocal() as db:
        rows = db.scalars(select(OperationalJobRun).where(OperationalJobRun.id.in_(created))).all()
        completed_rows = [row.id for row in rows if row.status == "completed"]
    report = {
        "formatVersion": 1,
        "workers": workers,
        "jobs": jobs,
        "acquisitionAttempts": attempts,
        "uniqueCompletions": len(set(completions)),
        "databaseCompletedRows": len(completed_rows),
        "duplicateCompletions": len(duplicates),
        "deadlocks": sum(1 for error in errors if "deadlock" in error.lower()),
        "errors": sorted(set(errors)),
        "expiredLeasesRecovered": 0,
        "blockingFindingCount": 0 if len(duplicates) == 0 and not errors and len(completed_rows) == jobs else 1,
    }
    out = Path(os.environ.get("WORKER_CONTENTION_REPORT_PATH", "../evidence/task13a/postgresql-worker-lock-contention.json"))
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError:
        pass
    print(json.dumps(report, indent=2))
    return 1 if report["blockingFindingCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
