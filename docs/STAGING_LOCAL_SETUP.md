# Staging Local Setup

Technical draft — requires legal and operational review before public deployment.

1. Copy `.env.staging.example` to `.env.staging`.
2. Fill only staging-safe values. Do not reuse production credentials.
3. Run `scripts/check-development-prerequisites.ps1`.
4. Run `scripts/staging-up.ps1 -Smoke`.
5. Open `http://127.0.0.1:18080`.

Use `scripts/staging-down.ps1` to stop services while retaining volumes. Do not use `down -v` for normal stops.

To start the local observability profile, run `scripts/observability-up.ps1`. The validated loopback endpoints are:

- Staging origin: `http://127.0.0.1:18080`
- Prometheus: `http://127.0.0.1:19090`
- Grafana: `http://127.0.0.1:13000`
- OTLP HTTP receiver: `http://127.0.0.1:4318`

Prometheus, Grafana and Collector routes must not be exposed through the staging origin.
