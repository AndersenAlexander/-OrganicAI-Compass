# Staging Configuration

Technical draft — requires legal and operational review before public deployment.

Staging fails closed for SQLite, placeholder secrets, missing privacy cryptographic keys, missing explicit staging origin, automatic schema creation, automatic backend migrations, non-JSON logs and development email outbox.

Required staging database: `organicai_staging`.

Required origin: `http://127.0.0.1:18080`.

Task 13A.3 validated local observability with loopback-only host bindings for Prometheus, Grafana and OTLP. The staging proxy returns blocked responses for public observability paths and does not expose metric payloads, Grafana UI or Collector endpoints through `http://127.0.0.1:18080`.

The backend container starts Uvicorn through `exec` so SIGTERM reaches the application process. Graceful shutdown performs provider close hooks, bounded telemetry flush and database pool disposal.
