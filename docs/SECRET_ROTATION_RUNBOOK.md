# Secret Rotation Runbook

Status: provider-neutral runbook. Do not record secret values in evidence.

Validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.secret_rotation_status
```

Evidence may record configured/not configured, placeholder status, minimum-length result, redacted database URL and rotation evidence presence. It must not record actual values.

| Secret | Creation | Storage | Deployment order | Overlap | Restart | Validation | Rollback | Revocation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Application/JWT `SECRET_KEY` | Generate high-entropy value in secret manager. | Secret manager only. | Deploy new value during maintenance after session impact approval. | No dual-key support currently; expect session invalidation. | Backend restart. | `secret_rotation_status`, login/refresh/logout smoke. | Restore previous key only if still valid and not exposed. | Revoke old key after rollback window. |
| PostgreSQL password | Rotate DB user password or create replacement user. | DB secret manager and connection pool config. | Add new credential, update app secret, restart backend/worker, verify, then revoke old. | Prefer dual-user overlap. | Backend/worker/migrator restart. | Readiness, migration current, connection lifecycle. | Restore old DB credential if not revoked. | Revoke old user/password after validation. |
| OpenAI API key | Create new project-scoped key. | Secret manager. | Add key, run opt-in provider acceptance, then promote. | Dual keys supported by provider. | Backend restart if env-mounted. | `provider_acceptance --provider openai --execute`. | Restore previous key if still active. | Revoke old key in provider console. |
| ElevenLabs API key | Create new key with least required scope. | Secret manager. | Add key/agent config, run opt-in live acceptance, promote. | Dual keys/provider dependent. | Backend restart. | Provider acceptance and privacy configuration evidence. | Disable live voice or restore previous key. | Revoke old key in provider console. |
| Webhook signing secrets | Generate high-entropy signing secret. | Secret manager and provider webhook settings. | Configure app to accept new secret, update provider, verify callback. | Dual validation window should be added if provider supports it. | Backend restart. | Signed webhook validation, replay protection. | Restore previous provider secret. | Remove old provider secret. |
| Production email credentials | Create SMTP/API credential with minimal send scope. | Secret manager. | Configure DNS/sender, add credential, run controlled inbox test. | Provider dependent. | Backend restart. | Email acceptance evidence and provider event ID hash. | Disable SMTP or restore previous credential. | Revoke old credential. |
| Grafana admin password | Generate managed password. | Secret manager or platform secret. | Update Grafana env/secret and restart Grafana. | Usually no overlap. | Grafana restart. | Login/health evidence without value. | Restore previous password if still controlled. | Revoke/remove old admin password. |

External manual action remains required until every production secret has rotation evidence and old exposed values are revoked.
