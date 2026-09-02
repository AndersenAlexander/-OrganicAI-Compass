# Staging Architecture

Technical draft — requires legal and operational review before public deployment.

Local staging uses one public loopback origin: `http://127.0.0.1:18080`.

Traffic enters `organicai-staging-proxy`, which serves frontend routes through the frontend container and proxies `/api` and `/health` to the backend container. The backend reaches only the isolated PostgreSQL service on the Docker network. PostgreSQL data is stored in the `organicai_staging_postgres_data` volume.

External OpenAI, ElevenLabs and email delivery are disabled by default in staging.
