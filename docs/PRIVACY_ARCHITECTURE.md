# Privacy Architecture

Technical draft - requires legal review before public deployment.

Technical draft — requires legal and operational review before public deployment.

Task 12B adds a first-party Privacy Center backed by PostgreSQL tables and additive Alembic revision `0003_privacy_data_lifecycle`. The design separates preference state, immutable consent events, data subject requests, lifecycle audit events, provider linkage records, encrypted export artifacts, deletion suppression ledger entries, and retention policies.

Runtime controls:

- `/api/privacy/preferences` controls account history, voice transcript history, analytics, research, personalization, service email, and marketing email.
- `/api/privacy/exports` creates encrypted-at-rest export artifacts and excludes credential hashes, token hashes, IP hashes, user-agent hashes, provider object hashes, and export encryption-key hashes.
- `/api/privacy/deletion/categories/{category}` supports category preview and controlled deletion.
- `/api/privacy/account-deletion` queues account deletion behind recent authentication and writes suppression-ledger evidence.
- `/api/privacy/research/withdraw` disables future research collection without touching active service data.

Sensitive write operations require `require_recent_authentication`, which checks the active PostgreSQL auth session `last_used_at` timestamp after `/api/privacy/reauthenticate`.
