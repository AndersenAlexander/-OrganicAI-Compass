# Observability Architecture

Technical draft — requires legal and operational review before public deployment.

The backend emits structured logs and exposes Prometheus-compatible internal metrics at `/internal/metrics`. The staging proxy intentionally blocks public access to `/internal/metrics`.

The optional observability profile adds OpenTelemetry Collector, Prometheus and Grafana on loopback-only ports. OpenTelemetry is disabled by default and must not include prompt, transcript, message, user identifier or secret attributes.

Task 13A.3 validated the local observability profile with Collector, Prometheus and Grafana healthy. Prometheus scraped the backend `/internal/metrics` endpoint and the Collector telemetry endpoint. Grafana provisioning created the Prometheus datasource and the `OrganicAI Local Staging` dashboard, and the dashboard remained available after a Grafana restart.

The staging proxy blocks public access to `/internal/metrics`, `/prometheus`, `/grafana` and `/otel`. Observability ports are bound only to loopback on the host.

The Collector pipeline applies a memory limiter, privacy attribute deletion and batching before debug export. The privacy processor removes authorization headers, cookies, request bodies, response bodies and SQL parameter attributes.
