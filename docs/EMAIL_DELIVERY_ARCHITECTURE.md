# Email Delivery Architecture

Technical draft — requires legal and operational review before public deployment.

Supported drivers:

- `disabled`
- `development-outbox`
- `smtp`

The new email package provides base message/result types, development outbox, SMTP delivery, versioned templates, and validation helpers. SMTP validation can check configuration and DNS without sending. Test send requires `EMAIL_LIVE_VALIDATION_ENABLED=true` and `EMAIL_TEST_RECIPIENT`.

SMTP acceptance is not inbox delivery verification.
