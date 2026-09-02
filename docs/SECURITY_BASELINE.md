# Security Baseline

Task 10 adds a release-gate security baseline. This is not a final production audit.

Task 12A adds server-managed authentication sessions, HttpOnly refresh cookies, Argon2id password hashing, source-archive exclusions, and mandatory manual rotation guidance after local archive exposure. See `docs/SECRET_ROTATION_AFTER_ARCHIVE_EXPOSURE.md`.

## Request IDs

Every response includes `X-Request-ID`. A valid incoming `X-Request-ID` is accepted only when it is short and uses safe characters. Otherwise the backend generates a UUID. Standard API errors include the request ID in:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data.",
    "requestId": "...",
    "details": null
  }
}
```

## CORS and Hosts

Default development allowlist:

```env
ALLOWED_ORIGINS=http://127.0.0.1:5190,http://localhost:5190
ALLOWED_HOSTS=127.0.0.1,localhost
```

The backend does not use wildcard CORS with credentials. TrustedHostMiddleware rejects unapproved hosts. If deployed behind a proxy, configure public hosts explicitly and set `TRUST_PROXY_HEADERS=true` only after the proxy is trusted.

## Security Headers

The backend adds:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: DENY`
- `Permissions-Policy`
- `Cross-Origin-Opener-Policy`
- CSP in report-only mode

HSTS is only enabled in production when `HSTS_ENABLED=true` and HTTPS public URLs are configured.

## Rate Limiting

Protected categories:

- `auth`
- `voice_token`
- `voice_legacy`
- `chat`
- `custom_llm`
- `rag_query`
- `rag_admin`

The current implementation uses an in-memory limiter for development and tests. It is not distributed and is not sufficient for multi-worker production. Redis support is represented by configuration and readiness checks for future tasks.

## Request and Upload Limits

Configured through:

```env
MAX_REQUEST_BODY_BYTES=2000000
MAX_AUDIO_UPLOAD_BYTES=8000000
MAX_AUDIO_DURATION_SECONDS=120
MAX_CHAT_MESSAGE_CHARS=8000
MAX_CONTEXT_FIELD_CHARS=1500
```

Voice-message fallback validates Content-Length when present, MIME type, extension, and actual streamed upload size. Temporary files are deleted after transcription attempts.

## Secret Hygiene

Run:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.security_scan
```

The script reports file path and issue type only. It does not print secret values. It ignores `node_modules`, `.venv`, build output, Playwright artifacts, and `.env.example`.
# Task 12B Privacy Security Addendum

Technical draft - requires legal review before public deployment.

Technical draft — requires legal and operational review before public deployment.

Task 12C adds secret-readiness auditing and keeps prior exposed credentials in `rotation-required` status until manual attestation flags are changed after verified rotation.

Privacy exports are written outside source archives, encrypted at rest, checksum verified on download, and excluded from safe-source packaging. Export serialization omits password hashes, token hashes, request-context hashes, network hashes, provider object hashes, export key hashes, and suppression-ledger hashes.
