# Monitoring And Incident Response

Status: checklist prepared; external alert activation remains manual.

Initial SLIs:

- API availability;
- readiness status;
- HTTP error rate;
- request latency;
- authentication failures;
- rate-limit activity;
- provider errors;
- PostgreSQL reachability;
- connection pool saturation;
- worker failures;
- webhook failures;
- RAG/provider fallback frequency;
- voice session failures;
- backup failures;
- certificate expiry.

Initial SLO draft:

- API availability: 99.5% monthly after public launch baseline.
- P95 latency: define after production traffic baseline.
- Readiness: alert within 5 minutes of sustained failure.
- Backup: every scheduled backup must produce a verified manifest.

Incident severity:

- SEV1: public outage, data exposure, auth/session compromise, destructive data issue.
- SEV2: degraded core workflow, provider outage without fallback, failed migration rollback risk.
- SEV3: non-core feature degradation, delayed worker, single failed backup with previous valid backup.
- SEV4: documentation, dashboard or advisory issue.

Required workflows:

- rollback criteria and owner;
- privacy/security incident escalation;
- provider outage degraded mode;
- database outage procedure;
- backup failure alert;
- certificate expiry alert;
- secret rotation expiry tracking.

Do not claim production alerts are active until alert routes and owner acknowledgement are verified.
