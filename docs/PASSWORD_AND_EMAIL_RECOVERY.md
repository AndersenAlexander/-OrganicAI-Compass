# Password And Email Recovery

Date: 2026-07-27

Task 12A adds foundations for password reset and email verification.

`account_tokens` stores only hashed tokens. Tokens are single-use and expire. Purposes are `email_verification` and `password_reset`.

The `development-outbox` email driver writes local JSON messages outside source directories by default:

```text
backend/tmp/email-outbox
```

The outbox may contain sensitive one-time links and must not be committed, archived, exposed through an API, or included in source ZIP files. SMTP is documented as a future deployment driver but is not validated in Task 12A.

