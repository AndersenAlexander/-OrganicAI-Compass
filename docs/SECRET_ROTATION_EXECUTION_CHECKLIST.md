# Secret Rotation Execution Checklist

Technical draft - requires operational review before public deployment.

Do not rotate secrets automatically from local scripts. Do not print secret values in tickets, logs, screenshots or evidence.

Order:

1. Create a new provider, database or application secret.
2. Store it in the intended local, staging or cloud secret store.
3. Update only the affected environment configuration.
4. Restart only affected services.
5. Run connectivity or application smoke checks without printing the secret.
6. Revoke the old secret.
7. Verify the old secret no longer works where safe.
8. Update attestation status.
9. Inspect logs for accidental exposure.
10. Regenerate the safe source archive.

Rollback must be documented before revoking an old secret. Do not rotate encryption keys without a data re-encryption and verification plan.

| Secret | Purpose | Current status | Exposure suspected | Rotation required | Dependent services | Manual owner | Rotation date | Verification date | Rollback considerations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI API key | AI provider access | rotation-required | yes | yes | backend, worker | manual-action-required | pending | pending | keep old key active until staging smoke passes |
| ElevenLabs API key | voice provider access | rotation-required | yes | yes | backend, worker | manual-action-required | pending | pending | validate provider disabled/default-safe path first |
| ElevenLabs webhook secret | webhook signature validation | rotation-required | yes | yes | backend | manual-action-required | pending | pending | support overlap window if provider allows |
| PostgreSQL development password | local development DB | rotation-required | yes | yes | backend, tools | manual-action-required | pending | pending | local only; preserve data before changing |
| PostgreSQL staging password | local staging DB | rotation-required | yes | yes | staging backend, migrator, worker | manual-action-required | pending | pending | update `.env.staging` without committing it |
| Application `SECRET_KEY` | auth/session signing | rotation-required | yes | yes | backend | manual-action-required | pending | pending | existing sessions may be invalidated |
| Custom LLM secret | ElevenLabs custom LLM auth | rotation-required | yes | yes | backend | manual-action-required | pending | pending | keep custom LLM disabled until verified |
| Application webhook secret | generic webhook signature validation | rotation-required | yes | yes | backend | manual-action-required | pending | pending | coordinate sender and receiver |
| Data-export encryption key | privacy export encryption | rotation-required | yes | yes | backend, privacy worker | manual-action-required | pending | pending | requires data re-encryption plan if old exports exist |
| Deletion-ledger HMAC key | deletion ledger integrity | rotation-required | yes | yes | backend, privacy worker | manual-action-required | pending | pending | do not rotate without ledger continuity plan |
| SMTP password | email delivery | not-configured | unknown | yes before live email | backend, email provider | manual-action-required | pending | pending | keep email disabled until configured |
| Grafana administrator password | observability admin access | rotation-required | yes | yes | Grafana | manual-action-required | pending | pending | rotate through local/staging secret store |
| Future cloud database password | cloud PostgreSQL | not-configured | no | yes before cloud staging | backend, worker, migrator | manual-action-required | pending | pending | use managed secret store |
| Future cloud deployment credentials | cloud deployment identity | not-configured | no | not-applicable if OIDC is used | CI/CD | manual-action-required | pending | pending | prefer OIDC over static credentials |
