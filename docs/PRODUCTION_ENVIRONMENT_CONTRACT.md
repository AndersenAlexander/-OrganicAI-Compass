# Production Environment Contract

Status: technical contract. Real production values must be supplied through a deployment secret manager and reviewed before use.

Templates:

- `.env.production.example`
- `backend/.env.production.example`

Validation commands:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.validate_production_environment --strict-production
.\.venv\Scripts\python.exe -m app.scripts.secret_rotation_status
```

Required production groups:

| Group | Required examples | Acceptance |
| --- | --- | --- |
| Runtime | `APP_ENV=production`, `APP_VERSION`, `BUILD_COMMIT` | Environment identifies the release and build. |
| Public URLs | `FRONTEND_PUBLIC_URL`, `PUBLIC_BACKEND_URL`, `EMAIL_PUBLIC_BASE_URL` | Public HTTPS only; no localhost, private IP, HTTP or `***`. |
| CORS/hosts | `ALLOWED_ORIGINS`, `ALLOWED_HOSTS` | Explicit allowlists; no wildcard or local hosts. |
| PostgreSQL | `DATABASE_URL`, `PRODUCTION_POSTGRES_SSL_REQUIRED=true` | PostgreSQL URL with `sslmode=require`, `verify-ca` or `verify-full`; no masked password. |
| Auth | `SECRET_KEY`, `AUTH_COOKIE_SECURE=true`, `AUTH_COOKIE_SAMESITE=lax` or `strict` | Strong secret, secure HttpOnly refresh cookie, origin check enabled. |
| Privacy keys | `DATA_EXPORT_ENCRYPTION_KEY`, `DELETION_LEDGER_HMAC_KEY` | Strong managed secrets, no placeholders. |
| Email | `EMAIL_DELIVERY_DRIVER=smtp`, SMTP host, sender, TLS, bounded timeout/retry | Production startup validation passes and live delivery remains separately approved. |
| Providers | OpenAI/ElevenLabs keys and flags | Disabled unless opt-in acceptance evidence exists. |
| Observability | metrics/tracing endpoints, monitoring evidence flags | Configured without exposing secrets. |

Production validator blocks:

- missing required variables;
- placeholder values;
- weak JWT/application secrets;
- masked URL/password markers containing `***`;
- localhost/private/HTTP public URLs;
- wildcard or local CORS/Trusted Hosts;
- insecure refresh cookie settings;
- production SMTP without TLS/sender/credential material;
- PostgreSQL without required SSL mode;
- insecure provider API URLs.

Real files such as `.env.production`, backend production `.env` files and secret-manager exports must remain excluded from Git and source archives.
