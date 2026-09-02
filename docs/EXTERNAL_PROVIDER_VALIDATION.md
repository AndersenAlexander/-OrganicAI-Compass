# External Provider Validation

Technical draft — requires legal and operational review before public deployment.

Execution modes:

- offline: deterministic fixtures only.
- live-read-only: connectivity and configuration retrieval only.
- live-write-disposable: synthetic OpenAI canary, approved test email, disposable ElevenLabs deletion, and webhook test events only when all explicit flags are enabled.

Provider registry covers OpenAI, ElevenLabs, Email, PostgreSQL, and local encrypted storage. It reports configured state, connectivity, data-control status, retention status, deletion capability, verification source, and manual-review status without exposing raw identifiers or secrets.
