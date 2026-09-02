# Research Data Separation

Technical draft - requires legal review before public deployment.

Research participation is disabled by default. When enabled, research uses pseudonymous subject identifiers derived from account identity through secret hashing. Direct identifiers are not included in the research summary response.

Separation rules:

- Ephemeral conversation and voice data are excluded from future research collection.
- Research withdrawal disables future collection immediately.
- Historical identifiable cleanup is marked manual-review-required where linkage may already exist.
- Active product functionality must not depend on research participation.
