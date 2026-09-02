# OpenAI Endpoint Inventory

Technical draft — requires legal and operational review before public deployment.

Found OpenAI SDK usage:

| Source file | Feature | API endpoint | Model | Input categories | Personal data possible | store parameter | Persistent provider object | Provider object ID retained | Delete API available | ZDR compatibility status | Regional endpoint | Fallback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `backend/app/services/ai_provider.py` | Coach response generation | Chat Completions | `gpt-4o-mini` | user message, compact profile context, KB snippets | yes | `store=false` | no | no | not applicable | unknown | deterministic local answer |
| `backend/app/services/profile_generation.py` | Profile, roadmap and fear JSON generation | Chat Completions | `gpt-4o-mini` | diagnostic/profile/fear payload | yes | `store=false` | no | no | not applicable | unknown | deterministic local JSON |
| `backend/app/services/embedding_service.py` | RAG embeddings | Embeddings | `OPENAI_EMBEDDING_MODEL` | KB chunk text | user data possible if user content enters KB | not supported | no | no | not applicable | unknown | deterministic local embedding |
| `backend/app/services/speech_to_text.py` | Audio transcription | Audio transcription | `OPENAI_TRANSCRIPTION_MODEL` | uploaded audio | yes | not supported | no | no | not applicable | unknown | empty transcript fallback |
| `backend/app/scripts/validate_openai_provider.py` | Operational synthetic canary | Chat Completions | `gpt-4o-mini` | synthetic prompt only | no | `store=false` | no | no | not applicable | unknown | offline report |

Not found in application code: Responses API, speech synthesis, Files, Vector Stores, Assistants, Threads, Realtime, moderation, image generation.

`store=false` is an endpoint-level request setting and is not evidence of Zero Data Retention or organization-level data-control configuration.
