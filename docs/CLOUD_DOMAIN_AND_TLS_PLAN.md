# Cloud Domain and TLS Plan

Technical draft - requires domain approval before configuration.

Suggested hostname pattern: `staging.<approved-domain>`.

Requirements:

- HTTPS certificate for the staging subdomain.
- HTTP-to-HTTPS redirect after certificate validation.
- Secure cookies with `AUTH_COOKIE_SECURE=true`.
- WebSocket Secure for live or streaming routes.
- Provider callback URLs must use the approved HTTPS staging origin.
- Email links must use the approved HTTPS staging origin.
- CORS and CSRF origins must exactly match the staging origin.
- Content Security Policy must be reviewed for the staging hostname.
- HSTS may be enabled only after HTTPS is validated.

Do not configure DNS during Task 13B.0. Do not use `localhost` in cloud callback configuration.
