# Production Release Readiness

Technical draft — requires legal and operational review before public deployment.

Release readiness categories:

- database
- authentication
- privacy
- OpenAI
- ElevenLabs
- email
- secrets
- workers
- backup
- logging
- frontend
- legal-manual

Production is blocked by default secrets, missing export or deletion-ledger keys, unsafe database configuration, development email driver in production, unsigned webhooks, source package secret findings, unavailable Privacy Center, failed account deletion, or missing backup evidence.

Legal review remains manual-action-required.

## Task 13B.0 Readiness Gate

Repository and cloud-staging preparation is complete locally, but public release remains blocked by manual prerequisites:

- Git unavailable locally.
- Remote repository not connected.
- GitHub Actions not executed remotely.
- Critical exposed credentials not rotated and verified.
- Cloud provider, region, budget and deployment architecture not approved.
- Staging domain and TLS not configured.
- Legal/provider attestations incomplete.

No cloud deployment or public production deployment is approved by Task 13B.0.
