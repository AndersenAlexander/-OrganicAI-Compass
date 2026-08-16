from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app.database import SessionLocal
from app.services.operational_workers import enqueue_synthetic_job, run_synthetic_continuous_worker, run_worker_once, worker_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--continuous", action="store_true")
    parser.add_argument("--enqueue-synthetic", action="store_true")
    parser.add_argument("--synthetic-mode", default="complete")
    parser.add_argument("--synthetic-delay-seconds", type=float, default=0.0)
    parser.add_argument("--worker", default="privacy")
    args = parser.parse_args()
    if args.continuous:
        report = run_synthetic_continuous_worker(SessionLocal)
    else:
        with SessionLocal() as db:
            if args.status:
                report = worker_status(db)
            elif args.enqueue_synthetic:
                run = enqueue_synthetic_job(db, mode=args.synthetic_mode, delay_seconds=args.synthetic_delay_seconds)
                report = {"status": "queued", "jobType": run.job_type, "jobId": run.id}
            else:
                report = run_worker_once(db, args.worker)
    out = Path(os.environ.get("OPERATIONAL_WORKER_REPORT_PATH", "/tmp/operational-workers-status.json"))
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError:
        pass
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
