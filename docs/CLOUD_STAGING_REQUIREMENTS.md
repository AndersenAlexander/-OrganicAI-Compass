# Cloud Staging Requirements

Technical draft - requires operational review before provisioning.

## Compute

- Linux container support.
- Backend container, frontend/reverse-proxy container, worker process and controlled migration job.
- Non-root execution, health checks, graceful shutdown, restart policy and resource limits.

## Database

- PostgreSQL with private connectivity, TLS, automatic backups and point-in-time recovery where available.
- Separate staging database, restricted database role, migration support and restore validation.

## Network

- HTTPS staging hostname, same-origin frontend/API, WebSocket support and controlled webhook endpoints.
- No public PostgreSQL, public Prometheus, public Grafana, public OTLP or public internal metrics.
- Outbound provider access only when explicitly enabled.

## Security

- Managed secrets, OIDC deployment identity, least privilege, firewall controls, encrypted storage, audit logs, rate limiting and restricted administrative endpoints.

## Observability

- Logs, metrics, traces, alerting, retention controls and telemetry privacy controls that exclude personal content.

## Operations

- Rollback, backup, restore, migrations, incident response, release evidence and cost monitoring.
