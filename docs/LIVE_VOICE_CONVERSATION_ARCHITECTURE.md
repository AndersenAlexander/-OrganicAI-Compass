# OrganicAI Coach Live Voice Conversation Architecture

## Purpose

Task 9 replaces the old primary voice loop (`record -> stop -> transcribe -> chat -> MP3`) with a continuous ElevenLabs Agents session. The old MediaRecorder flow remains available as the separate **Voice message** fallback.

The live mode keeps the user in a single open conversation:

1. The browser requests microphone permission.
2. The backend exchanges the OrganicAI user session for an ElevenLabs conversation token.
3. `@elevenlabs/react` opens a WebRTC conversation with the configured ElevenLabs Agent.
4. ElevenLabs handles live audio transport, VAD, STT, TTS, turn taking, and barge-in.
5. In native mode, the configured ElevenLabs Agent handles each turn from its synchronized static knowledge. In optional Custom LLM mode, ElevenLabs calls OrganicAI's Custom LLM endpoint for each user turn.
6. In Custom LLM mode, OrganicAI runs the existing profile, RAG, intent, roadmap, recommendation, ethics, and persistence logic.
7. In Custom LLM mode, OrganicAI streams OpenAI-compatible SSE chunks back to ElevenLabs.
8. The browser receives final user/agent transcript events and displays them in the shared Coach state.

Task 10 adds runtime diagnostics, request IDs, standard error responses, rate limiting, and explicit ElevenLabs residency handling. Standard ElevenLabs is the default. Isolated residency modes require an explicit `ELEVENLABS_API_BASE_URL`; OrganicAI does not assume EU residency from a deprecated server-location value.

## Runtime Boundary

ElevenLabs owns:

- WebRTC media session
- microphone audio transport
- voice activity detection
- speech-to-text
- text-to-speech
- live turn orchestration
- interruption and barge-in behavior

OrganicAI owns:

- authentication and rate-limited token minting
- profile ownership and conversation ownership checks
- RAG retrieval and response metadata when Custom LLM mode is enabled
- intent classification and contextual OrganicAI commands when Custom LLM mode is enabled
- roadmap, recommendation, and profile feedback logic
- text transcript persistence
- privacy messaging and fallback voice-message mode

## Backend Endpoints

### `GET /api/voice/status`

Returns live voice availability without exposing secret values or the actual ElevenLabs Agent ID.

Response fields:

- `provider`
- `liveVoiceEnabled`
- `liveVoiceConfigured`
- `legacyFallbackEnabled`
- `agentIdConfigured`
- `serverLocation`
- `environment`

### `POST /api/voice/conversation-token`

Requires OrganicAI authentication. It validates lightweight page context, rate-limits token creation per user, and calls ElevenLabs:

`https://api.elevenlabs.io/v1/convai/conversation/token`

The request includes the configured `agent_id` and the OrganicAI user ID as the participant name. Provider errors are mapped to safe client-facing status codes.

### `POST /api/elevenlabs/v1/chat/completions`

OpenAI-compatible SSE endpoint for ElevenLabs Custom LLM. It requires:

```http
Authorization: Bearer <ELEVENLABS_CUSTOM_LLM_SECRET>
```

The endpoint validates `elevenlabs_extra_body`, including:

- `organicai_user_id`
- `profile_id`
- `app_conversation_id`
- `elevenlabs_conversation_id`
- `route`
- `selected_profile_node`
- `selected_recommendation_id`
- `roadmap_action_id`
- `language`
- `voice_personality`
- `conversation_mode`
- `theme`

It rejects missing users, invalid UUIDs, cross-user profiles, cross-user conversations, and profile-mismatched recommendations or roadmap actions.

### `GET /api/voice/conversations/{elevenlabs_conversation_id}/latest-turn`

Requires OrganicAI authentication. When Custom LLM mode is enabled, the frontend calls this after final assistant transcript events so UI messages can show OrganicAI metadata such as grounding status, sources, confidence note, ethical note, profile signals, and RAG run IDs. Native mode skips the optional request because OrganicAI does not produce per-turn Custom LLM metadata.

Current storage is an in-memory TTL cache scoped by `(user_id, elevenlabs_conversation_id)`. It is adequate for local development and single-process deployments. Production multi-worker deployments should move this metadata to Redis, the relational database, or another shared store.

## Frontend State Model

`LiveVoiceProvider` wraps `ConversationProvider` above `CoachProvider` in `App.tsx`. This makes CoachPage and FloatingVoiceChat share one live session while users navigate through the SPA.

`CoachContext` now exposes:

- `voiceMode: "live" | "message"`
- live states: `connecting`, `listening`, `thinking`, `speaking`, `muted`, `error`
- legacy voice-message methods for fallback
- shared transcript and message handling for both the full page and floating widget

Live mode does not show a "Review transcript" flow. Voice message fallback keeps transcript review before sending.

## Client Tools

The frontend registers these ElevenLabs client tool names:

- `navigate_to`
- `switch_theme`
- `confirm_selected_node`
- `add_note_to_selected_node`
- `open_selected_learning_path`
- `regenerate_roadmap`
- `hide_selected_recommendation`
- `open_profile`
- `open_roadmap`
- `open_recommendations`
- `open_diagnostic`

Each tool returns a JSON string with `success` and `message`. Tool handlers validate required state before acting, for example refusing profile-node feedback when no profile node is selected.

## Privacy Notes

Live conversation:

- ElevenLabs processes microphone audio for live turn detection, transcription, and speech output.
- OrganicAI receives text turns through Custom LLM and can store text transcripts when transcript history is enabled.
- OrganicAI does not store live audio files by default.

Voice message fallback:

- The browser records a short audio message with MediaRecorder.
- OrganicAI sends the audio to the transcription backend.
- The user can review the transcript before it becomes a chat message.
- Legacy MP3 playback remains available for fallback text-to-speech.
