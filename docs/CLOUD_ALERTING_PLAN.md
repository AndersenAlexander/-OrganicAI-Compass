# Cloud Alerting Plan

Technical draft - requires operations approval before implementation.

| Alert | Severity |
| --- | --- |
| Backend readiness unavailable | critical |
| HTTP 5xx rate elevated | high |
| High p95 latency | warning |
| PostgreSQL unavailable | critical |
| Database connection saturation | high |
| Worker heartbeat stale | high |
| Dead-letter jobs present | high |
| Privacy export failures | high |
| Account-deletion job failures | critical |
| Webhook signature failures | warning |
| Provider failure spike | warning |
| Backup overdue | high |
| Migration mismatch | critical |
| Certificate expiration | high |
| Disk usage high | warning |
| Memory pressure | warning |

Alerts must not include raw user identifiers, email addresses, request bodies, prompts, transcripts, provider payloads or secret values.
