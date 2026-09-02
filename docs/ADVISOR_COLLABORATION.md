# Advisor Collaboration

Advisor Collaboration is a temporary, scoped review layer. A share contains only the sections selected by the owner; it never grants account-wide access.

- Permission codes: `READ_ONLY`, `COMMENT`, `PROPOSE_CHANGE`.
- Share tokens are random, stored as SHA-256 hashes, shown once, bounded by expiry and access-attempt limits, and revocable server-side.
- The preview lists included and excluded sections. Sensitive fields, private transcripts, benefit inputs and unrelated applications are excluded.
- Comments and proposals are separate adviser records. The owner can accept, edit or reject them; acceptance does not silently mutate evidence, profile or roadmap data.
- Audit events record creation, access, comments, proposal decisions, revocation and expiry.

Limit: once an adviser has viewed a shared item, the platform cannot prevent copying or screenshots.
