# Operational Privacy Workers

Technical draft — requires legal and operational review before public deployment.

`run_operational_workers.py` exposes status and one-shot worker execution for privacy, retention, provider deletion, account deletion, email cleanup, expired-token cleanup, and deletion-ledger verification.

Workers record `operational_job_runs` with worker hash, heartbeat, lease expiration, processed count, retry count, and failure summaries. Destructive jobs remain disabled unless explicitly configured.
