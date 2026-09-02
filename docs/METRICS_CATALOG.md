# Metrics Catalog

Technical draft - requires legal and operational review before public deployment.

Task 13A.2 metric labels are restricted to low-cardinality operational values: `method`, `route`, `status_class`, `service`, `job_type`, `provider`, `result` and `environment`.

| Metric | Type | Labels | Purpose | Privacy classification | Collection point | Staging status |
| --- | --- | --- | --- | --- | --- | --- |
| `organicai_http_requests_total` | counter | method, route, status_class | HTTP request volume | Operational, no personal data | FastAPI middleware | Validated internally |
| `organicai_http_request_duration_seconds_sum` | counter | method, route, status_class | HTTP latency sum | Operational, no personal data | FastAPI middleware | Validated internally |
| `organicai_http_active_requests` | gauge | none | In-flight request count | Operational, no personal data | FastAPI middleware | Validated internally |
| `organicai_database_available` | gauge | none | Database reachability | Operational, no personal data | readiness check | Validated internally |
| `organicai_database_pool_checked_out` | gauge | none | SQLAlchemy checked-out connections | Operational, no personal data | readiness check | Validated internally |
| `organicai_database_pool_available` | gauge | none | SQLAlchemy available pool slots | Operational, no personal data | readiness check | Validated internally |
| `organicai_database_pool_overflow` | gauge | none | SQLAlchemy overflow connections | Operational, no personal data | readiness check | Validated internally |
| `organicai_auth_events_total` | counter | result | Login, refresh, logout and revocation events | Security operations, no identifiers | auth service | Implemented |
| `organicai_privacy_jobs_total` | counter | job_type, result | Privacy worker job outcomes | Privacy operations, no identifiers | operational workers | Implemented |
| `organicai_provider_requests_total` | counter | provider, result | Provider request outcomes | Operational, no provider object IDs | provider adapters | Cataloged |
| `organicai_provider_request_duration_seconds_sum` | counter | provider, result | Provider latency sum | Operational, no request payloads | provider adapters | Cataloged |
| `organicai_email_send_attempts_total` | counter | result | Email attempts | Operational, no addresses | email service | Cataloged |
| `organicai_email_send_failures_total` | counter | result | Email failures | Operational, no addresses | email service | Cataloged |
| `organicai_websocket_active_connections` | gauge | none | Active WebSocket sessions | Operational, no user IDs | runtime | Cataloged |
| `organicai_live_voice_active_sessions` | gauge | none | Live voice active sessions | Operational, no transcript text | runtime | Cataloged |
| `organicai_worker_heartbeat_total` | counter | service | Worker heartbeat | Operational, no job payload | worker | Implemented |
| `organicai_worker_jobs_total` | counter | job_type, result | Worker job state changes | Operational, no job payload | worker | Implemented |
| `organicai_dead_letter_jobs_total` | counter | job_type | Dead-letter jobs | Operational, no job payload | worker | Implemented |
| `organicai_webhook_signature_failures_total` | counter | provider | Rejected webhooks | Security operations, no payload | webhook validation | Implemented |
| `organicai_webhook_duplicates_total` | counter | provider | Duplicate webhooks | Security operations, no provider object IDs | webhook validation | Implemented |
| `organicai_build_info` | gauge | service | Build presence marker | Operational, no personal data | metrics service | Validated internally |

Disallowed labels include raw user IDs, profile IDs, conversation IDs, email addresses, arbitrary URLs, provider object IDs, request IDs, trace IDs, user-input message types and exception messages.

Task 13A.3 Prometheus and Grafana validation passed locally. Prometheus target validation showed the backend and Collector targets UP. Grafana datasource and dashboard provisioning passed and survived restart.

Metrics remain internal-only in staging. The proxy blocks public access to `/internal/metrics`, `/prometheus`, `/grafana` and `/otel`.
