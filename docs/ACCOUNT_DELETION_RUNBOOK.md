# Account Deletion Runbook

Technical draft - requires legal review before public deployment.

Technical draft — requires legal and operational review before public deployment.

Account deletion is a two-step flow:

1. `/api/privacy/account-deletion` queues a `data_subject_requests` row after recent authentication and exact confirmation phrase `DELETE MY ORGANICAI ACCOUNT`.
2. The execution worker or controlled fixture revokes sessions, tombstones account identifiers, increments auth version, appends a deletion-suppression ledger entry, and records lifecycle events.

Cancellation:

- `/api/privacy/account-deletion/{request_id}/cancel` may cancel queued requests before execution.

Backup handling:

- Active rows are removed or tombstoned in the current database.
- Existing backups expire by retention schedule.
- Restores must replay `deletion_suppression_ledger` before restored data is exposed.
