# Subprocessor Register

Technical draft - requires legal review before public deployment.

| Provider | Role | Status | Required review |
| --- | --- | --- | --- |
| OpenAI | AI generation, transcription, embeddings | Optional runtime provider | DPA, retention, transfer, regional processing |
| ElevenLabs | Live voice and speech generation | Optional runtime provider | DPA, retention, audio saving, zero-retention status |
| Local PostgreSQL | Active application database | First-party local runtime | Operational backup and access controls |
| Local file storage | Temporary exports and operational files | First-party local runtime | Retention and archive exclusions |

No public deployment should publish this register without legal and vendor review.
