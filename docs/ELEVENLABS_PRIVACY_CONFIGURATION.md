# ElevenLabs Privacy Configuration

Technical draft — requires legal and operational review before public deployment.

Intended OrganicAI baseline:

- Audio saving: disabled.
- Transcript retention: minimum operational value or scheduled deletion.
- Zero Retention: preferred when available and compatible.
- Post-call audio webhook: disabled.
- Post-call transcript webhook: enabled only when required.
- Webhook authentication: HMAC required.
- Conversation deletion adapter: enabled only with explicit configuration.

`configure_elevenlabs_privacy.py` defaults to dry-run. Apply requires exact agent ID, exact confirmation text, and `ELEVENLABS_PRIVACY_CONFIGURATION_APPLY_ENABLED=true`.
