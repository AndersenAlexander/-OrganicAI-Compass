# Personal Data Inventory

Technical draft - requires legal review before public deployment.

Inventory is generated from SQLAlchemy metadata by `backend/app/privacy/inventory.py` and audited by `backend/app/scripts/audit_personal_data_inventory.py`.

Current blocking inventory finding count: `0`.

Personal data categories:

- Account profile: account identity, profile settings, privacy settings, service email state.
- Diagnostic profile: questionnaire answers, generated profile, assessments and interpreted signals.
- Conversation history: persisted coach conversations, messages, RAG observability linked to persisted conversations.
- Voice interaction: voice provider sessions and optional live voice transcripts.
- Career workspace: roadmaps, recommendations, learning, interviews, market application and resilience data.
- Research participation: pseudonymous research records, study participation, fairness and robustness runs.
- Security and operations: sessions, auth events, account tokens, provider linkage hashes, lifecycle events.

Security-secret fields are excluded from exports and public reports: `hashed_password`, token hashes, request context hashes, IP hashes, user-agent hashes, provider object hashes, ledger hashes, and export key hashes.
