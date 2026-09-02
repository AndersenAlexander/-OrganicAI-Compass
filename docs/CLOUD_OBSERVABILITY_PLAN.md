# Cloud Observability Plan

Technical draft - requires provider approval before implementation.

## Self-hosted Observability

- OpenTelemetry Collector.
- Prometheus.
- Grafana.
- Restricted administration.
- Persistent volumes.
- Backup and retention management.

## Managed Observability

- Cloud logs.
- Cloud metrics.
- Managed trace backend.
- OTLP export.
- Role-based access.
- Configured retention.

The selected model must preserve current metric names where practical, telemetry privacy controls, request/trace correlation, alerting and bounded retention. Personal data, prompts, transcripts, messages, provider payloads and secrets must not be included in telemetry.

Prometheus, Grafana and OTLP endpoints must not be public.
