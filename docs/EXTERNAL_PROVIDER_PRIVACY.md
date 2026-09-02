# External Provider Privacy

Technical draft - requires legal review before public deployment.

Technical draft — requires legal and operational review before public deployment.

Task 12C adds sanitized provider validation evidence, OpenAI data-control attestation, ElevenLabs privacy diff tooling, disposable deletion validation, webhook HMAC validation, and provider registry reporting.

Provider adapters are intentionally conservative.

OpenAI:

- Used for AI response generation, transcription, and embeddings when configured.
- The app does not claim a universal deletion API or universal retention behavior.
- DPA, transfer, and retention status require manual verification before public deployment.

ElevenLabs:

- Used for live voice and optional speech generation when configured.
- Voice transcript persistence is disabled by default.
- Voice audio storage is disabled by application policy.
- Deletion adapter remains disabled unless `ELEVENLABS_PROVIDER_DELETION_ENABLED=true`.

Local PostgreSQL and local file storage are first-party runtime stores.
