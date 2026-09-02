# ElevenLabs Webhook Security

Technical draft — requires legal and operational review before public deployment.

`POST /api/webhooks/elevenlabs` validates raw request body before parsing. The signature format is timestamp plus HMAC SHA-256. The endpoint rejects missing signature, invalid signature, expired timestamp, oversized body, unsupported event types, and audio webhook events.

Supported initial events:

- `post_call_transcription`
- `call_initiation_failure`

Webhook events are deduplicated by provider and event fingerprint. Transcript and audio content are not logged or persisted by the webhook handler.
