# Cloud Secret Management Plan

Technical draft - requires provider approval before implementation.

Requirements:

- Use provider-managed secret storage.
- No secrets in Docker images.
- No secrets in GitHub Actions YAML.
- No secrets in repository variables visible to pull requests.
- No secrets in logs.
- Avoid secrets in command-line arguments.
- Use OIDC for deployment identity.
- Restrict secret access per service.
- Rotate staging and production secrets separately.
- Audit access and document recovery.

Secret classes:

- Backend: `DATABASE_URL`, `SECRET_KEY`, privacy keys, provider keys and webhook secrets.
- Worker: database and privacy-worker secrets.
- Migrator: database migration credential.
- Proxy: TLS material only when not provider-managed.
- Database: application role password or managed identity.
- Observability: Grafana administrator password and telemetry backend credentials.
- CI/CD: OIDC configuration and registry credentials if required.
- External provider: OpenAI, ElevenLabs and webhook credentials.
- Email: SMTP or provider API credentials.
