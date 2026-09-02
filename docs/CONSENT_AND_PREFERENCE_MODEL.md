# Consent And Preference Model

Technical draft - requires legal review before public deployment.

`user_privacy_settings` stores current user preferences. `privacy_consent_events` stores immutable consent and withdrawal events.

Default settings:

- Conversation history: enabled for account-history mode.
- Voice transcript history: disabled for ephemeral voice mode.
- Voice audio storage: disabled and not offered.
- Product analytics: disabled.
- Research participation: disabled.
- Personalization: enabled.
- Service email: enabled.
- Marketing email: disabled.

Preference changes create consent events with purpose key, action, legal basis label, policy version, hashed request context, source, and timestamp. Events do not store raw message content or raw network identifiers.
