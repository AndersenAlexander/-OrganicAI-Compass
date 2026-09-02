# Production Email Readiness

Status: technical implementation ready for controlled provider acceptance; real delivery is `EXTERNAL MANUAL ACTION REQUIRED`.

Implemented foundations:

- provider interface: `EmailDriver`;
- disabled/default behavior;
- local development outbox;
- SMTP production driver selected by `EMAIL_DELIVERY_DRIVER=smtp`;
- sanitized `EmailResult` with provider status, failure code and attempt count;
- bounded SMTP timeout and retry limit;
- idempotency header support;
- hashed recipient/provider-message IDs in `EmailDeliveryEvent`;
- templates for email verification, password reset, password changed/reset completed and security/session notifications;
- validation command: `python -m app.scripts.validate_email_delivery --offline`;
- opt-in live send guarded by `EMAIL_LIVE_VALIDATION_ENABLED` and `EMAIL_TEST_RECIPIENT`.

Required production configuration:

- verified sender address;
- SMTP host/port;
- TLS via STARTTLS or SSL;
- SMTP credential in secret manager when authentication is required;
- public HTTPS `EMAIL_PUBLIC_BASE_URL`;
- SPF, DKIM and DMARC DNS records;
- approved test recipient for controlled acceptance.

Acceptance test:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.provider_acceptance --provider email --execute
```

This must remain blocked until real credentials, DNS and an approved recipient are configured. Automated tests must not send real email.
